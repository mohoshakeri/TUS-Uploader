import base64
import binascii
import mimetypes
import re
from pathlib import Path

from fastapi import HTTPException, Request, status

from CONSTANTS import (
    ALLOWED_TYPES,
    CONTENT_TYPE_OCTET_STREAM,
    EMPTY_STRING,
    ERROR_FILE_MIME_MISMATCH,
    ERROR_FILE_TOO_LARGE,
    ERROR_FILE_TYPE_NOT_ALLOWED,
    ERROR_FILENAME_UNSUPPORTED,
    ERROR_INVALID_METADATA,
    ERROR_INVALID_PASSWORD,
    ERROR_TUS_RESUMABLE_REQUIRED,
    ERROR_UNSUPPORTED_PATCH_CONTENT_TYPE,
    ERROR_UPLOAD_LENGTH_REQUIRED,
    ERROR_UPLOAD_LENGTH_ZERO,
    ERROR_UPLOAD_OFFSET_REQUIRED,
    FILENAME_METADATA_KEY,
    FILENAME_PATTERN,
    FILETYPE_METADATA_KEY,
    HEADER_CONTENT_TYPE,
    HEADER_TUS_RESUMABLE,
    HEADER_UPLOAD_LENGTH,
    HEADER_UPLOAD_OFFSET,
    HEADER_UPLOAD_PASSWORD,
    METADATA_KEY_SEPARATOR,
    METADATA_SEPARATOR,
    TUS_VERSION,
    UTF_8,
)
from utils.config import MAX_UPLOAD_SIZE, UPLOAD_PASSWORD


def parse_upload_metadata(raw_metadata: str | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not raw_metadata:
        return parsed

    for metadata_item in raw_metadata.split(METADATA_SEPARATOR):
        item: str = metadata_item.strip()
        if not item:
            continue

        key: str
        ignored_separator: str
        encoded_value: str
        key, ignored_separator, encoded_value = item.partition(METADATA_KEY_SEPARATOR)
        del ignored_separator
        if not key:
            continue

        if not encoded_value:
            parsed[key] = EMPTY_STRING
            continue

        try:
            decoded_value: str = base64.b64decode(encoded_value).decode(UTF_8)
        except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_INVALID_METADATA,
            ) from exc

        parsed[key] = decoded_value

    return parsed


def validate_file_metadata(metadata: dict[str, str], upload_length: int) -> tuple[str, str]:
    if upload_length <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_UPLOAD_LENGTH_ZERO,
        )

    if upload_length > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=ERROR_FILE_TOO_LARGE,
        )

    original_name: str = metadata.get(FILENAME_METADATA_KEY, EMPTY_STRING).strip()
    content_type: str = metadata.get(FILETYPE_METADATA_KEY, EMPTY_STRING).strip().lower()
    suffix: str = Path(original_name).suffix.lower()

    if not original_name or not suffix or suffix not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_FILE_TYPE_NOT_ALLOWED,
        )

    allowed_mimes: set[str] = ALLOWED_TYPES[suffix]
    if content_type not in allowed_mimes:
        guessed_content_type: str | None
        guessed_content_type, _ = mimetypes.guess_type(original_name)
        if guessed_content_type not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_FILE_MIME_MISMATCH,
            )
        content_type = guessed_content_type

    if not re.fullmatch(FILENAME_PATTERN, original_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_FILENAME_UNSUPPORTED,
        )

    return suffix, content_type


def validate_upload_password(request: Request) -> None:
    if not UPLOAD_PASSWORD:
        return

    provided_password: str = request.headers.get(HEADER_UPLOAD_PASSWORD, EMPTY_STRING).strip()
    if provided_password != UPLOAD_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_PASSWORD,
        )


def validate_tus_resumable(request: Request) -> None:
    tus_resumable: str | None = request.headers.get(HEADER_TUS_RESUMABLE)
    if tus_resumable != TUS_VERSION:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=ERROR_TUS_RESUMABLE_REQUIRED,
        )


def parse_upload_length(request: Request) -> int:
    upload_length_header: str | None = request.headers.get(HEADER_UPLOAD_LENGTH)
    if not upload_length_header or not upload_length_header.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_UPLOAD_LENGTH_REQUIRED,
        )

    return int(upload_length_header)


def parse_upload_offset(request: Request) -> int:
    provided_offset: str | None = request.headers.get(HEADER_UPLOAD_OFFSET)
    if provided_offset is None or not provided_offset.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_UPLOAD_OFFSET_REQUIRED,
        )

    return int(provided_offset)


def validate_patch_content_type(request: Request) -> None:
    if request.headers.get(HEADER_CONTENT_TYPE) == CONTENT_TYPE_OCTET_STREAM:
        return

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail=ERROR_UNSUPPORTED_PATCH_CONTENT_TYPE,
    )
