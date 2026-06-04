import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from CONSTANTS import (
    ERROR_UPLOADED_FILE_NOT_FOUND,
    ERROR_UPLOAD_SESSION_NOT_FOUND,
    STORED_DIRECTORY_KEY,
    STORED_NAME_KEY,
    TUS_METADATA_SUFFIX,
    UTF_8,
)
from utils.config import TMP_DIR, UPLOADS_DIR, UPLOAD_DIRECTORIES


def ensure_directories() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    for upload_directory in UPLOAD_DIRECTORIES:
        (UPLOADS_DIR / upload_directory).mkdir(parents=True, exist_ok=True)


def tus_metadata_path(upload_id: str) -> Path:
    return TMP_DIR / "{}{}".format(upload_id, TUS_METADATA_SUFFIX)


def upload_path_from_meta(meta: dict[str, Any]) -> Path:
    stored_directory: str = str(meta.get(STORED_DIRECTORY_KEY, "")).strip()
    if not stored_directory:
        return UPLOADS_DIR / meta[STORED_NAME_KEY]

    return UPLOADS_DIR / stored_directory / meta[STORED_NAME_KEY]


def write_tus_metadata(upload_id: str, payload: dict[str, Any]) -> None:
    serialized_payload: str = json.dumps(payload, ensure_ascii=True)
    tus_metadata_path(upload_id).write_text(serialized_payload, encoding=UTF_8)


def read_tus_metadata(upload_id: str) -> dict[str, Any]:
    metadata_file: Path = tus_metadata_path(upload_id)
    if not metadata_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_UPLOAD_SESSION_NOT_FOUND,
        )

    metadata: dict[str, Any] = json.loads(metadata_file.read_text(encoding=UTF_8))
    return metadata


def delete_tus_metadata(upload_id: str) -> None:
    metadata_file: Path = tus_metadata_path(upload_id)
    if not metadata_file.exists():
        return

    metadata_file.unlink()


def resolve_completed_file(upload_id: str) -> Path:
    matches: list[Path] = sorted(UPLOADS_DIR.rglob("{}.*".format(upload_id)))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_UPLOADED_FILE_NOT_FOUND,
        )

    return matches[0]
