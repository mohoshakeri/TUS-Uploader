APP_TITLE: str = "TUS Uploader"
APP_VERSION: str = "1.0.0"
APP_HOST: str = "0.0.0.0"
APP_IMPORT_PATH: str = "main:app"

STATIC_ROUTE: str = "/static"
UPLOADS_ROUTE: str = "/f"
UPLOADS_URL_ROUTE: str = "/uploads"
INDEX_FILE_NAME: str = "index.html"
ROOT_ROUTE: str = "/"

CONFIG_BASE_URL_KEY: str = "base_url"
CONFIG_UPLOAD_ENDPOINT_KEY: str = "upload_endpoint"
CONFIG_MAX_UPLOAD_SIZE_KEY: str = "max_upload_size"
CONFIG_CHUNK_SIZE_KEY: str = "chunk_size"
CONFIG_ALLOWED_EXTENSIONS_KEY: str = "allowed_extensions"
CONFIG_PASSWORD_REQUIRED_KEY: str = "password_required"
CONFIG_LOGO_URL_KEY: str = "logo_url"
CONFIG_FAVICON_URL_KEY: str = "favicon_url"
FILE_NAME_KEY: str = "file_name"
DOWNLOAD_URL_KEY: str = "download_url"
STATUS_KEY: str = "status"

API_CONFIG_ROUTE: str = "/api/config"
API_FILE_LINK_ROUTE: str = "/api/files/{upload_id}/link"
FILES_ROUTE: str = "/files"
FILE_ROUTE: str = "/files/{upload_id}"
HEALTH_ROUTE: str = "/health"

UPLOAD_ENDPOINT: str = "/files"
HEALTH_STATUS: str = "ok"

TUS_VERSION: str = "1.0.0"
TUS_EXTENSION: str = "creation,expiration"
CONTENT_TYPE_OCTET_STREAM: str = "application/offset+octet-stream"
CACHE_CONTROL_NO_STORE: str = "no-store"

HEADER_CACHE_CONTROL: str = "Cache-Control"
HEADER_CONTENT_TYPE: str = "Content-Type"
HEADER_LOCATION: str = "Location"
HEADER_TUS_EXTENSION: str = "Tus-Extension"
HEADER_TUS_MAX_SIZE: str = "Tus-Max-Size"
HEADER_TUS_RESUMABLE: str = "Tus-Resumable"
HEADER_TUS_VERSION: str = "Tus-Version"
HEADER_UPLOAD_LENGTH: str = "Upload-Length"
HEADER_UPLOAD_METADATA: str = "Upload-Metadata"
HEADER_UPLOAD_OFFSET: str = "Upload-Offset"
HEADER_UPLOAD_PASSWORD: str = "X-Upload-Password"

HEADER_ALLOW_METHODS: list[str] = ["GET", "POST", "HEAD", "PATCH", "OPTIONS"]
HEADER_ALLOW_ALL: list[str] = ["*"]
HEADER_EXPOSE_HEADERS: list[str] = [
    HEADER_LOCATION,
    HEADER_UPLOAD_OFFSET,
    HEADER_UPLOAD_LENGTH,
    HEADER_TUS_RESUMABLE,
]

SECURITY_HEADER_CONTENT_TYPE_OPTIONS: str = "X-Content-Type-Options"
SECURITY_HEADER_FRAME_OPTIONS: str = "X-Frame-Options"
SECURITY_HEADER_REFERRER_POLICY: str = "Referrer-Policy"
SECURITY_HEADER_PERMISSIONS_POLICY: str = "Permissions-Policy"
SECURITY_VALUE_CONTENT_TYPE_OPTIONS: str = "nosniff"
SECURITY_VALUE_FRAME_OPTIONS: str = "DENY"
SECURITY_VALUE_REFERRER_POLICY: str = "same-origin"
SECURITY_VALUE_PERMISSIONS_POLICY: str = "camera=(), microphone=(), geolocation=()"

ENV_DEBUG: str = "DEBUG"
ENV_PORT: str = "PORT"
ENV_BASE_URL: str = "BASE_URL"
ENV_CORS_ALLOWEDS: str = "CORS_ALLOWEDS"
ENV_MAX_UPLOAD_SIZE: str = "MAX_UPLOAD_SIZE"
ENV_CHUNK_SIZE: str = "CHUNK_SIZE"
ENV_UPLOAD_PASSWORD: str = "UPLOAD_PASSWORD"
ENV_LOGO_URL: str = "LOGO_URL"
ENV_FAVICON_URL: str = "FAVICON_URL"

DEFAULT_DEBUG: str = "NO"
DEFAULT_PORT: str = "8989"
DEFAULT_UPLOAD_PASSWORD: str = "1234"
DEFAULT_LOGO_URL: str = "/static/logo.png"
DEFAULT_FAVICON_URL: str = "/static/favicon.ico"
DEBUG_ENABLED_VALUE: str = "YES"
LOCALHOST: str = "localhost"
LOCALHOST_IP: str = "127.0.0.1"

BYTES_IN_MEGABYTE: int = 1024 * 1024
DEFAULT_MAX_UPLOAD_SIZE_BYTES: int = 1024 * BYTES_IN_MEGABYTE
DEFAULT_CHUNK_SIZE_BYTES: int = BYTES_IN_MEGABYTE

UPLOAD_ID_KEY: str = "upload_id"
STORED_NAME_KEY: str = "stored_name"
OFFSET_KEY: str = "offset"
LENGTH_KEY: str = "length"
CONTENT_TYPE_KEY: str = "content_type"
FILENAME_METADATA_KEY: str = "filename"
FILETYPE_METADATA_KEY: str = "filetype"

TUS_METADATA_SUFFIX: str = ".tus"
METADATA_SEPARATOR: str = ","
METADATA_KEY_SEPARATOR: str = " "
FILENAME_PATTERN: str = r"[A-Za-z0-9._ -]+"

EMPTY_STRING: str = ""
UTF_8: str = "utf-8"
TEXT_HTML_UTF_8: str = "text/html; charset=utf-8"
READ_WRITE_BINARY_MODE: str = "r+b"

STATUS_UPLOAD_NOT_COMPLETE: str = "Upload is not complete yet."
ERROR_CHUNK_EXCEEDS_LENGTH: str = "Chunk exceeds declared upload length."
ERROR_FILE_MIME_MISMATCH: str = "The file MIME type does not match the allowed extension."
ERROR_FILE_TOO_LARGE: str = "File is larger than the allowed upload size."
ERROR_FILE_TYPE_NOT_ALLOWED: str = "This file type is not allowed."
ERROR_FILENAME_UNSUPPORTED: str = "Filename contains unsupported characters."
ERROR_INVALID_METADATA: str = "Invalid Upload-Metadata header."
ERROR_INVALID_PASSWORD: str = "Invalid upload password."
ERROR_OFFSET_MISMATCH: str = "Upload-Offset does not match the current server offset."
ERROR_UPLOAD_LENGTH_REQUIRED: str = "Upload-Length header is required."
ERROR_UPLOAD_LENGTH_ZERO: str = "Upload-Length must be greater than zero."
ERROR_UPLOAD_OFFSET_REQUIRED: str = "Upload-Offset header is required."
ERROR_UPLOAD_SESSION_NOT_FOUND: str = "Upload session not found."
ERROR_UPLOADED_FILE_NOT_FOUND: str = "Uploaded file not found."
ERROR_TUS_RESUMABLE_REQUIRED: str = "Tus-Resumable header must be 1.0.0."
ERROR_UNSUPPORTED_PATCH_CONTENT_TYPE: str = "Content-Type must be application/offset+octet-stream."

ZERO_OFFSET: int = 0

STATIC_DIR_NAME: str = "static"
UPLOADS_DIR_NAME: str = "uploads"
TMP_DIR_NAME: str = "tmp"

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
