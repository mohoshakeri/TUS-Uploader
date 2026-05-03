import base64
import binascii
import json
import mimetypes
import os
import re
import uuid
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


# Config Case
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_ROOT / "static"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
TMP_DIR = PROJECT_ROOT / "tmp"

DEBUG = os.getenv("DEBUG", "NO").upper() == "YES"
PORT = int(os.getenv("PORT", "8989"))
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}").rstrip("/")
CORS_ALLOWEDS = [item.strip() for item in os.getenv("CORS_ALLOWEDS", "").split(",") if item.strip()]
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(1 * 1024 * 1024 * 1024)))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", str(1 * 1024 * 1024)))
UPLOAD_PASSWORD = os.getenv("UPLOAD_PASSWORD", "1234").strip()

if not CORS_ALLOWEDS:
    cors_defaults = {
        BASE_URL,
        BASE_URL.replace("localhost", "127.0.0.1"),
        BASE_URL.replace("127.0.0.1", "localhost"),
    }
    CORS_ALLOWEDS = sorted(cors_defaults)

ALLOWED_TYPES: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".txt": {"text/plain"},
    ".csv": {"text/csv", "application/csv"},
    ".json": {"application/json", "text/json"},
    ".zip": {"application/zip", "application/x-zip-compressed"},
    ".rar": {"application/vnd.rar", "application/x-rar-compressed"},
    ".7z": {"application/x-7z-compressed"},
    ".mp4": {"video/mp4"},
    ".mp3": {"audio/mpeg"},
    ".wav": {"audio/wav", "audio/x-wav"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".xls": {"application/vnd.ms-excel"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".ppt": {"application/vnd.ms-powerpoint"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
}

# App Case
app = FastAPI(title="TUS Uploader", version="1.0.0", debug=DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWEDS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "HEAD", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Location", "Upload-Offset", "Upload-Length", "Tus-Resumable"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/f", StaticFiles(directory=UPLOADS_DIR), name="uploads")


# Helpers Case
def ensure_directories() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def tus_metadata_path(upload_id: str) -> Path:
    return TMP_DIR / f"{upload_id}.tus"


def upload_path_from_meta(meta: dict[str, Any]) -> Path:
    return UPLOADS_DIR / meta["stored_name"]


def parse_upload_metadata(raw_metadata: str | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not raw_metadata:
        return parsed

    for item in raw_metadata.split(","):
        item = item.strip()
        if not item:
            continue

        key, _, encoded_value = item.partition(" ")
        if not key:
            continue

        if not encoded_value:
            parsed[key] = ""
            continue

        try:
            decoded_value = base64.b64decode(encoded_value).decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
            raise HTTPException(status_code=400, detail="Invalid Upload-Metadata header.") from exc

        parsed[key] = decoded_value

    return parsed


def validate_file_metadata(metadata: dict[str, str], upload_length: int) -> tuple[str, str]:
    if upload_length <= 0:
        raise HTTPException(status_code=400, detail="Upload-Length must be greater than zero.")

    if upload_length > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File is larger than the allowed upload size.")

    original_name = metadata.get("filename", "").strip()
    content_type = metadata.get("filetype", "").strip().lower()
    suffix = Path(original_name).suffix.lower()

    if not original_name or not suffix or suffix not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="This file type is not allowed.")

    allowed_mimes = ALLOWED_TYPES[suffix]
    if content_type not in allowed_mimes:
        guessed_content_type, _ = mimetypes.guess_type(original_name)
        if guessed_content_type not in allowed_mimes:
            raise HTTPException(status_code=400, detail="The file MIME type does not match the allowed extension.")
        content_type = guessed_content_type

    if not re.fullmatch(r"[A-Za-z0-9._ -]+", original_name):
        raise HTTPException(status_code=400, detail="Filename contains unsupported characters.")

    return suffix, content_type


def validate_upload_password(request: Request) -> None:
    if not UPLOAD_PASSWORD:
        return

    provided_password = request.headers.get("X-Upload-Password", "").strip()
    if provided_password != UPLOAD_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid upload password.")


def write_tus_metadata(upload_id: str, payload: dict[str, Any]) -> None:
    tus_metadata_path(upload_id).write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


def read_tus_metadata(upload_id: str) -> dict[str, Any]:
    metadata_file = tus_metadata_path(upload_id)
    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Upload session not found.")
    return json.loads(metadata_file.read_text(encoding="utf-8"))


def delete_tus_metadata(upload_id: str) -> None:
    metadata_file = tus_metadata_path(upload_id)
    if metadata_file.exists():
        metadata_file.unlink()


def resolve_completed_file(upload_id: str) -> Path:
    matches = list(UPLOADS_DIR.glob(f"{upload_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Uploaded file not found.")
    return matches[0]


@app.middleware("http")
async def apply_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# Page Case
@app.get("/")
async def index() -> FileResponse:
    return FileResponse("index.html")


@app.get("/api/config")
async def get_config() -> JSONResponse:
    return JSONResponse(
        {
            "base_url": BASE_URL,
            "upload_endpoint": "/files",
            "max_upload_size": MAX_UPLOAD_SIZE,
            "chunk_size": CHUNK_SIZE,
            "allowed_extensions": sorted(ALLOWED_TYPES.keys()),
            "password_required": bool(UPLOAD_PASSWORD),
        }
    )


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


# Tus Case
@app.options("/files")
@app.options("/files/{upload_id}")
async def tus_options(upload_id: str | None = None) -> Response:
    response = Response(status_code=204)
    response.headers["Tus-Resumable"] = "1.0.0"
    response.headers["Tus-Version"] = "1.0.0"
    response.headers["Tus-Extension"] = "creation,expiration"
    response.headers["Tus-Max-Size"] = str(MAX_UPLOAD_SIZE)
    return response


@app.post("/files", status_code=status.HTTP_201_CREATED)
async def create_upload(request: Request) -> Response:
    validate_upload_password(request)

    tus_resumable = request.headers.get("Tus-Resumable")
    if tus_resumable != "1.0.0":
        raise HTTPException(status_code=412, detail="Tus-Resumable header must be 1.0.0.")

    upload_length_header = request.headers.get("Upload-Length")
    if not upload_length_header or not upload_length_header.isdigit():
        raise HTTPException(status_code=400, detail="Upload-Length header is required.")

    upload_length = int(upload_length_header)
    metadata = parse_upload_metadata(request.headers.get("Upload-Metadata"))
    suffix, content_type = validate_file_metadata(metadata, upload_length)

    upload_id = str(uuid.uuid4())
    stored_name = f"{upload_id}{suffix}"
    file_path = UPLOADS_DIR / stored_name
    file_path.touch(exist_ok=False)

    write_tus_metadata(
        upload_id,
        {
            "upload_id": upload_id,
            "stored_name": stored_name,
            "offset": 0,
            "length": upload_length,
            "content_type": content_type,
        },
    )

    response = Response(status_code=status.HTTP_201_CREATED)
    response.headers["Location"] = f"{BASE_URL}/files/{upload_id}"
    response.headers["Tus-Resumable"] = "1.0.0"
    response.headers["Upload-Offset"] = "0"
    return response


@app.head("/files/{upload_id}")
async def head_upload(upload_id: str, request: Request) -> Response:
    validate_upload_password(request)

    tus_resumable = request.headers.get("Tus-Resumable")
    if tus_resumable != "1.0.0":
        raise HTTPException(status_code=412, detail="Tus-Resumable header must be 1.0.0.")

    metadata = read_tus_metadata(upload_id)
    response = Response(status_code=200)
    response.headers["Tus-Resumable"] = "1.0.0"
    response.headers["Upload-Offset"] = str(metadata["offset"])
    response.headers["Upload-Length"] = str(metadata["length"])
    response.headers["Cache-Control"] = "no-store"
    return response


@app.patch("/files/{upload_id}")
async def patch_upload(upload_id: str, request: Request) -> Response:
    validate_upload_password(request)

    tus_resumable = request.headers.get("Tus-Resumable")
    if tus_resumable != "1.0.0":
        raise HTTPException(status_code=412, detail="Tus-Resumable header must be 1.0.0.")

    if request.headers.get("Content-Type") != "application/offset+octet-stream":
        raise HTTPException(status_code=415, detail="Content-Type must be application/offset+octet-stream.")

    metadata = read_tus_metadata(upload_id)
    expected_offset = metadata["offset"]
    provided_offset = request.headers.get("Upload-Offset")

    if provided_offset is None or not provided_offset.isdigit():
        raise HTTPException(status_code=400, detail="Upload-Offset header is required.")

    if int(provided_offset) != expected_offset:
        raise HTTPException(status_code=409, detail="Upload-Offset does not match the current server offset.")

    chunk = await request.body()
    next_offset = expected_offset + len(chunk)
    if next_offset > metadata["length"]:
        raise HTTPException(status_code=413, detail="Chunk exceeds declared upload length.")

    file_path = upload_path_from_meta(metadata)
    with file_path.open("r+b") as buffer:
        buffer.seek(expected_offset)
        buffer.write(chunk)

    metadata["offset"] = next_offset
    if next_offset == metadata["length"]:
        delete_tus_metadata(upload_id)
    else:
        write_tus_metadata(upload_id, metadata)

    response = Response(status_code=204)
    response.headers["Tus-Resumable"] = "1.0.0"
    response.headers["Upload-Offset"] = str(next_offset)
    return response


# Download Case
@app.get("/api/files/{upload_id}/link")
async def get_uploaded_file_link(upload_id: str) -> JSONResponse:
    if tus_metadata_path(upload_id).exists():
        current = read_tus_metadata(upload_id)
        if current["offset"] < current["length"]:
            raise HTTPException(status_code=409, detail="Upload is not complete yet.")

    file_path = resolve_completed_file(upload_id)
    return JSONResponse(
        {
            "file_name": file_path.name,
            "download_url": f"{BASE_URL}/uploads/{file_path.name}",
        }
    )


if __name__ == "__main__":
    ensure_directories()
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=DEBUG)
