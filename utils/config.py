import os
from pathlib import Path

from dotenv import load_dotenv

from CONSTANTS import (
    ALLOWED_TYPES,
    DEBUG_ENABLED_VALUE,
    DEFAULT_CHUNK_SIZE_BYTES,
    DEFAULT_DEBUG,
    DEFAULT_FAVICON_URL,
    DEFAULT_LOGO_URL,
    DEFAULT_MAX_UPLOAD_SIZE_BYTES,
    DEFAULT_PORT,
    DEFAULT_UPLOAD_PASSWORD,
    EMPTY_STRING,
    ENV_BASE_URL,
    ENV_CHUNK_SIZE,
    ENV_CORS_ALLOWEDS,
    ENV_DEBUG,
    ENV_FAVICON_URL,
    ENV_LOGO_URL,
    ENV_MAX_UPLOAD_SIZE,
    ENV_PORT,
    ENV_UPLOAD_PASSWORD,
    LOCALHOST,
    LOCALHOST_IP,
    STATIC_DIR_NAME,
    TMP_DIR_NAME,
    UPLOADS_DIR_NAME,
)

load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
STATIC_DIR: Path = PROJECT_ROOT / STATIC_DIR_NAME
UPLOADS_DIR: Path = PROJECT_ROOT / UPLOADS_DIR_NAME
TMP_DIR: Path = PROJECT_ROOT / TMP_DIR_NAME

DEBUG: bool = os.getenv(ENV_DEBUG, DEFAULT_DEBUG).upper() == DEBUG_ENABLED_VALUE
PORT: int = int(os.getenv(ENV_PORT, DEFAULT_PORT))
BASE_URL: str = os.getenv(ENV_BASE_URL, "http://localhost:{}".format(PORT)).rstrip("/")
CORS_ALLOWEDS: list[str] = [
    item.strip()
    for item in os.getenv(ENV_CORS_ALLOWEDS, EMPTY_STRING).split(",")
    if item.strip()
]
MAX_UPLOAD_SIZE: int = int(os.getenv(ENV_MAX_UPLOAD_SIZE, str(DEFAULT_MAX_UPLOAD_SIZE_BYTES)))
CHUNK_SIZE: int = int(os.getenv(ENV_CHUNK_SIZE, str(DEFAULT_CHUNK_SIZE_BYTES)))
UPLOAD_PASSWORD: str = os.getenv(ENV_UPLOAD_PASSWORD, DEFAULT_UPLOAD_PASSWORD).strip()
LOGO_URL: str = os.getenv(ENV_LOGO_URL, DEFAULT_LOGO_URL).strip() or DEFAULT_LOGO_URL
FAVICON_URL: str = os.getenv(ENV_FAVICON_URL, DEFAULT_FAVICON_URL).strip() or DEFAULT_FAVICON_URL

if not CORS_ALLOWEDS:
    cors_defaults: set[str] = {
        BASE_URL,
        BASE_URL.replace(LOCALHOST, LOCALHOST_IP),
        BASE_URL.replace(LOCALHOST_IP, LOCALHOST),
    }
    CORS_ALLOWEDS = sorted(cors_defaults)
