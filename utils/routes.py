import uuid
from pathlib import Path
from typing import Any, BinaryIO

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse

from CONSTANTS import (
    ALLOWED_TYPES,
    API_CONFIG_ROUTE,
    API_FILE_LINK_ROUTE,
    CACHE_CONTROL_NO_STORE,
    CONFIG_ALLOWED_EXTENSIONS_KEY,
    CONFIG_BASE_URL_KEY,
    CONFIG_CHUNK_SIZE_KEY,
    CONFIG_MAX_UPLOAD_SIZE_KEY,
    CONFIG_PASSWORD_REQUIRED_KEY,
    CONFIG_UPLOAD_ENDPOINT_KEY,
    CONTENT_TYPE_KEY,
    DOWNLOAD_URL_KEY,
    ERROR_CHUNK_EXCEEDS_LENGTH,
    ERROR_OFFSET_MISMATCH,
    FILE_NAME_KEY,
    FILE_ROUTE,
    FILES_ROUTE,
    HEADER_CACHE_CONTROL,
    HEADER_LOCATION,
    HEADER_TUS_EXTENSION,
    HEADER_TUS_MAX_SIZE,
    HEADER_TUS_RESUMABLE,
    HEADER_TUS_VERSION,
    HEADER_UPLOAD_LENGTH,
    HEADER_UPLOAD_METADATA,
    HEADER_UPLOAD_OFFSET,
    HEALTH_ROUTE,
    HEALTH_STATUS,
    STATUS_KEY,
    INDEX_FILE_NAME,
    LENGTH_KEY,
    OFFSET_KEY,
    READ_WRITE_BINARY_MODE,
    ROOT_ROUTE,
    STATUS_UPLOAD_NOT_COMPLETE,
    STORED_NAME_KEY,
    TUS_EXTENSION,
    TUS_VERSION,
    UPLOADS_URL_ROUTE,
    UPLOAD_ENDPOINT,
    UPLOAD_ID_KEY,
    ZERO_OFFSET,
)
from utils.config import (
    BASE_URL,
    CHUNK_SIZE,
    MAX_UPLOAD_SIZE,
    PROJECT_ROOT,
    UPLOADS_DIR,
    UPLOAD_PASSWORD,
)
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

router: APIRouter = APIRouter()


@router.get(ROOT_ROUTE)
async def index() -> FileResponse:
    return FileResponse(PROJECT_ROOT / INDEX_FILE_NAME)


@router.get(API_CONFIG_ROUTE)
async def get_config() -> JSONResponse:
    config_payload: dict[str, Any] = {
        CONFIG_BASE_URL_KEY: BASE_URL,
        CONFIG_UPLOAD_ENDPOINT_KEY: UPLOAD_ENDPOINT,
        CONFIG_MAX_UPLOAD_SIZE_KEY: MAX_UPLOAD_SIZE,
        CONFIG_CHUNK_SIZE_KEY: CHUNK_SIZE,
        CONFIG_ALLOWED_EXTENSIONS_KEY: sorted(ALLOWED_TYPES.keys()),
        CONFIG_PASSWORD_REQUIRED_KEY: bool(UPLOAD_PASSWORD),
    }
    return JSONResponse(config_payload)


@router.get(HEALTH_ROUTE)
async def health() -> JSONResponse:
    return JSONResponse({STATUS_KEY: HEALTH_STATUS})


@router.options(FILES_ROUTE)
@router.options(FILE_ROUTE)
async def tus_options(upload_id: str | None = None) -> Response:
    del upload_id
    response: Response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.headers[HEADER_TUS_RESUMABLE] = TUS_VERSION
    response.headers[HEADER_TUS_VERSION] = TUS_VERSION
    response.headers[HEADER_TUS_EXTENSION] = TUS_EXTENSION
    response.headers[HEADER_TUS_MAX_SIZE] = str(MAX_UPLOAD_SIZE)
    return response


@router.post(FILES_ROUTE, status_code=status.HTTP_201_CREATED)
async def create_upload(request: Request) -> Response:
    validate_upload_password(request)
    validate_tus_resumable(request)

    upload_length: int = parse_upload_length(request)
    metadata: dict[str, str] = parse_upload_metadata(
        request.headers.get(HEADER_UPLOAD_METADATA)
    )
    suffix: str
    content_type: str
    suffix, content_type = validate_file_metadata(metadata, upload_length)

    upload_id: str = str(uuid.uuid4())
    stored_name: str = "{}{}".format(upload_id, suffix)
    file_path: Path = UPLOADS_DIR / stored_name
    file_path.touch(exist_ok=False)

    write_tus_metadata(
        upload_id,
        {
            UPLOAD_ID_KEY: upload_id,
            STORED_NAME_KEY: stored_name,
            OFFSET_KEY: ZERO_OFFSET,
            LENGTH_KEY: upload_length,
            CONTENT_TYPE_KEY: content_type,
        },
    )

    response: Response = Response(status_code=status.HTTP_201_CREATED)
    response.headers[HEADER_LOCATION] = "{}/files/{}".format(BASE_URL, upload_id)
    response.headers[HEADER_TUS_RESUMABLE] = TUS_VERSION
    response.headers[HEADER_UPLOAD_OFFSET] = str(ZERO_OFFSET)
    return response


@router.head(FILE_ROUTE)
async def head_upload(upload_id: str, request: Request) -> Response:
    validate_upload_password(request)
    validate_tus_resumable(request)

    metadata: dict[str, Any] = read_tus_metadata(upload_id)
    response: Response = Response(status_code=status.HTTP_200_OK)
    response.headers[HEADER_TUS_RESUMABLE] = TUS_VERSION
    response.headers[HEADER_UPLOAD_OFFSET] = str(metadata[OFFSET_KEY])
    response.headers[HEADER_UPLOAD_LENGTH] = str(metadata[LENGTH_KEY])
    response.headers[HEADER_CACHE_CONTROL] = CACHE_CONTROL_NO_STORE
    return response


@router.patch(FILE_ROUTE)
async def patch_upload(upload_id: str, request: Request) -> Response:
    validate_upload_password(request)
    validate_tus_resumable(request)
    validate_patch_content_type(request)

    metadata: dict[str, Any] = read_tus_metadata(upload_id)
    expected_offset: int = metadata[OFFSET_KEY]
    provided_offset: int = parse_upload_offset(request)

    if provided_offset != expected_offset:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=ERROR_OFFSET_MISMATCH
        )

    chunk: bytes = await request.body()
    next_offset: int = expected_offset + len(chunk)
    if next_offset > metadata[LENGTH_KEY]:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=ERROR_CHUNK_EXCEEDS_LENGTH,
        )

    file_path: Path = upload_path_from_meta(metadata)
    buffer: BinaryIO
    with file_path.open(READ_WRITE_BINARY_MODE) as buffer:
        buffer.seek(expected_offset)
        buffer.write(chunk)

    metadata[OFFSET_KEY] = next_offset
    if next_offset == metadata[LENGTH_KEY]:
        delete_tus_metadata(upload_id)
    else:
        write_tus_metadata(upload_id, metadata)

    response: Response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.headers[HEADER_TUS_RESUMABLE] = TUS_VERSION
    response.headers[HEADER_UPLOAD_OFFSET] = str(next_offset)
    return response


@router.get(API_FILE_LINK_ROUTE)
async def get_uploaded_file_link(upload_id: str) -> JSONResponse:
    if tus_metadata_path(upload_id).exists():
        current_metadata: dict[str, Any] = read_tus_metadata(upload_id)
        if current_metadata[OFFSET_KEY] < current_metadata[LENGTH_KEY]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=STATUS_UPLOAD_NOT_COMPLETE,
            )

    file_path: Path = resolve_completed_file(upload_id)
    return JSONResponse(
        {
            FILE_NAME_KEY: file_path.name,
            DOWNLOAD_URL_KEY: "{}{}/{}".format(
                BASE_URL, UPLOADS_URL_ROUTE, file_path.name
            ),
        }
    )
