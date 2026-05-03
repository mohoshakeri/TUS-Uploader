import base64
import binascii
import mimetypes
import re
from pathlib import Path

from fastapi import HTTPException, Request

from utils.config import ALLOWED_TYPES, MAX_UPLOAD_SIZE, UPLOAD_PASSWORD


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


def validate_tus_resumable(request: Request) -> None:
    tus_resumable = request.headers.get("Tus-Resumable")
    if tus_resumable != "1.0.0":
        raise HTTPException(status_code=412, detail="Tus-Resumable header must be 1.0.0.")


def parse_upload_length(request: Request) -> int:
    upload_length_header = request.headers.get("Upload-Length")
    if not upload_length_header or not upload_length_header.isdigit():
        raise HTTPException(status_code=400, detail="Upload-Length header is required.")
    return int(upload_length_header)


def parse_upload_offset(request: Request) -> int:
    provided_offset = request.headers.get("Upload-Offset")
    if provided_offset is None or not provided_offset.isdigit():
        raise HTTPException(status_code=400, detail="Upload-Offset header is required.")
    return int(provided_offset)


def validate_patch_content_type(request: Request) -> None:
    if request.headers.get("Content-Type") != "application/offset+octet-stream":
        raise HTTPException(status_code=415, detail="Content-Type must be application/offset+octet-stream.")
