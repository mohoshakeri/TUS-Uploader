import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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
