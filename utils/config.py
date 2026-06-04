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
    ENV_UPLOAD_DIRECTORIES,
    ENV_UPLOAD_PASSWORD,
    LOCALHOST,
    LOCALHOST_IP,
    STATIC_DIR_NAME,
    TMP_DIR_NAME,
    UPLOADS_DIR_NAME,
)

load_dotenv()


def parse_upload_directories(raw_directories: str) -> list[str]:
    upload_directories: list[str] = []
    seen_directories: set[str] = set()

    for raw_item in raw_directories.split(","):
        normalized_item: str = raw_item.strip().replace("\\", "/")
        if not normalized_item:
            continue

        directory_path: Path = Path(normalized_item)
        if directory_path.is_absolute() or ".." in directory_path.parts:
            raise ValueError(
                "{} entries must be relative directory names inside uploads/.".format(
                    ENV_UPLOAD_DIRECTORIES
                )
            )

        directory: str = directory_path.as_posix().strip("/")
        if not directory:
            continue

        if directory not in seen_directories:
            seen_directories.add(directory)
            upload_directories.append(directory)

    return upload_directories


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
UPLOAD_DIRECTORIES: list[str] = parse_upload_directories(
    os.getenv(ENV_UPLOAD_DIRECTORIES, EMPTY_STRING)
)

if not CORS_ALLOWEDS:
    cors_defaults: set[str] = {
        BASE_URL,
        BASE_URL.replace(LOCALHOST, LOCALHOST_IP),
        BASE_URL.replace(LOCALHOST_IP, LOCALHOST),
    }
    CORS_ALLOWEDS = sorted(cors_defaults)
