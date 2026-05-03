import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from utils.config import TMP_DIR, UPLOADS_DIR


def ensure_directories() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def tus_metadata_path(upload_id: str) -> Path:
    return TMP_DIR / f"{upload_id}.tus"


def upload_path_from_meta(meta: dict[str, Any]) -> Path:
    return UPLOADS_DIR / meta["stored_name"]


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
