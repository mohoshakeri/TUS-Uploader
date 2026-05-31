import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from CONSTANTS import (
    ERROR_UPLOADED_FILE_NOT_FOUND,
    ERROR_UPLOAD_SESSION_NOT_FOUND,
    STORED_NAME_KEY,
    TUS_METADATA_SUFFIX,
    UTF_8,
)
from utils.config import TMP_DIR, UPLOADS_DIR


def ensure_directories() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def tus_metadata_path(upload_id: str) -> Path:
    return TMP_DIR / "{}{}".format(upload_id, TUS_METADATA_SUFFIX)


def upload_path_from_meta(meta: dict[str, Any]) -> Path:
    return UPLOADS_DIR / meta[STORED_NAME_KEY]


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
    matches: list[Path] = list(UPLOADS_DIR.glob("{}.*".format(upload_id)))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_UPLOADED_FILE_NOT_FOUND,
        )

    return matches[0]
