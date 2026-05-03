import uuid

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse

from utils.config import ALLOWED_TYPES, BASE_URL, CHUNK_SIZE, MAX_UPLOAD_SIZE, PROJECT_ROOT, UPLOADS_DIR, UPLOAD_PASSWORD
from utils.storage import (
    delete_tus_metadata,
    read_tus_metadata,
    resolve_completed_file,
    tus_metadata_path,
    upload_path_from_meta,
    write_tus_metadata,
)
from utils.validators import (
    parse_upload_length,
    parse_upload_metadata,
    parse_upload_offset,
    validate_file_metadata,
    validate_patch_content_type,
    validate_tus_resumable,
    validate_upload_password,
)

router = APIRouter()


@router.get("/")
async def index() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "index.html")


@router.get("/api/config")
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


@router.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.options("/files")
@router.options("/files/{upload_id}")
async def tus_options(upload_id: str | None = None) -> Response:
    del upload_id
    response = Response(status_code=204)
    response.headers["Tus-Resumable"] = "1.0.0"
    response.headers["Tus-Version"] = "1.0.0"
    response.headers["Tus-Extension"] = "creation,expiration"
    response.headers["Tus-Max-Size"] = str(MAX_UPLOAD_SIZE)
    return response


@router.post("/files", status_code=status.HTTP_201_CREATED)
async def create_upload(request: Request) -> Response:
    validate_upload_password(request)
    validate_tus_resumable(request)

    upload_length = parse_upload_length(request)
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


@router.head("/files/{upload_id}")
async def head_upload(upload_id: str, request: Request) -> Response:
    validate_upload_password(request)
    validate_tus_resumable(request)

    metadata = read_tus_metadata(upload_id)
    response = Response(status_code=200)
    response.headers["Tus-Resumable"] = "1.0.0"
    response.headers["Upload-Offset"] = str(metadata["offset"])
    response.headers["Upload-Length"] = str(metadata["length"])
    response.headers["Cache-Control"] = "no-store"
    return response


@router.patch("/files/{upload_id}")
async def patch_upload(upload_id: str, request: Request) -> Response:
    validate_upload_password(request)
    validate_tus_resumable(request)
    validate_patch_content_type(request)

    metadata = read_tus_metadata(upload_id)
    expected_offset = metadata["offset"]
    provided_offset = parse_upload_offset(request)

    if provided_offset != expected_offset:
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


@router.get("/api/files/{upload_id}/link")
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
