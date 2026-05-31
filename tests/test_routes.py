import base64
import tempfile
import unittest
from pathlib import Path
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, JSONResponse

from CONSTANTS import (
    CONTENT_TYPE_OCTET_STREAM,
    HEADER_CONTENT_TYPE,
    HEADER_LOCATION,
    HEADER_TUS_RESUMABLE,
    HEADER_UPLOAD_LENGTH,
    HEADER_UPLOAD_METADATA,
    HEADER_UPLOAD_OFFSET,
    LENGTH_KEY,
    OFFSET_KEY,
    STORED_NAME_KEY,
    TUS_VERSION,
)
from utils import routes, storage, validators


class RequestStub:
    def __init__(self, headers: dict[str, str], body: bytes = b"") -> None:
        self.headers: dict[str, str] = headers
        self._body: bytes = body

    async def body(self) -> bytes:
        return self._body


class RouteTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_directory: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        self.project_root: Path = Path(self.temp_directory.name)
        self.original_route_uploads_dir: Path = routes.UPLOADS_DIR
        self.original_storage_uploads_dir: Path = storage.UPLOADS_DIR
        self.original_storage_tmp_dir: Path = storage.TMP_DIR
        self.original_password: str = validators.UPLOAD_PASSWORD
        routes.UPLOADS_DIR = self.project_root / "uploads"
        storage.UPLOADS_DIR = self.project_root / "uploads"
        storage.TMP_DIR = self.project_root / "tmp"
        validators.UPLOAD_PASSWORD = ""
        storage.ensure_directories()

    def tearDown(self) -> None:
        routes.UPLOADS_DIR = self.original_route_uploads_dir
        storage.UPLOADS_DIR = self.original_storage_uploads_dir
        storage.TMP_DIR = self.original_storage_tmp_dir
        validators.UPLOAD_PASSWORD = self.original_password
        self.temp_directory.cleanup()

    async def test_index_health_and_config_handlers_return_responses(self) -> None:
        index_response: FileResponse = await routes.index()
        health_response: JSONResponse = await routes.health()
        config_response: JSONResponse = await routes.get_config()

        self.assertIsInstance(index_response, FileResponse)
        self.assertEqual(health_response.body.decode("utf-8"), '{"status":"ok"}')
        self.assertEqual(config_response.status_code, status.HTTP_200_OK)

    async def test_tus_options_returns_required_headers(self) -> None:
        response = await routes.tus_options()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.headers[HEADER_TUS_RESUMABLE], TUS_VERSION)

    async def test_create_head_patch_and_link_upload_flow(self) -> None:
        metadata: str = self._metadata_header("sample.txt", "text/plain")
        create_request: RequestStub = RequestStub(
            {
                HEADER_TUS_RESUMABLE: TUS_VERSION,
                HEADER_UPLOAD_LENGTH: "5",
                HEADER_UPLOAD_METADATA: metadata,
            }
        )

        create_response = await routes.create_upload(create_request)
        upload_id: str = create_response.headers[HEADER_LOCATION].rsplit("/", 1)[-1]

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.headers[HEADER_UPLOAD_OFFSET], "0")

        head_response = await routes.head_upload(
            upload_id, RequestStub({HEADER_TUS_RESUMABLE: TUS_VERSION})
        )

        self.assertEqual(head_response.headers[HEADER_UPLOAD_OFFSET], "0")
        self.assertEqual(head_response.headers[HEADER_UPLOAD_LENGTH], "5")

        patch_request: RequestStub = RequestStub(
            {
                HEADER_TUS_RESUMABLE: TUS_VERSION,
                HEADER_CONTENT_TYPE: CONTENT_TYPE_OCTET_STREAM,
                HEADER_UPLOAD_OFFSET: "0",
            },
            body=b"hello",
        )
        patch_response = await routes.patch_upload(upload_id, patch_request)

        self.assertEqual(patch_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(patch_response.headers[HEADER_UPLOAD_OFFSET], "5")
        self.assertFalse(storage.tus_metadata_path(upload_id).exists())

        link_response: JSONResponse = await routes.get_uploaded_file_link(upload_id)
        self.assertIn(upload_id, link_response.body.decode("utf-8"))

    async def test_patch_upload_rejects_wrong_offset(self) -> None:
        upload_id: str = "abc"
        stored_name: str = "abc.txt"
        (storage.UPLOADS_DIR / stored_name).touch()
        storage.write_tus_metadata(
            upload_id,
            {
                STORED_NAME_KEY: stored_name,
                OFFSET_KEY: 2,
                LENGTH_KEY: 5,
            },
        )
        request: RequestStub = RequestStub(
            {
                HEADER_TUS_RESUMABLE: TUS_VERSION,
                HEADER_CONTENT_TYPE: CONTENT_TYPE_OCTET_STREAM,
                HEADER_UPLOAD_OFFSET: "0",
            },
            body=b"hello",
        )

        with self.assertRaises(HTTPException) as context:
            await routes.patch_upload(upload_id, request)

        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)

    def _metadata_header(self, filename: str, filetype: str) -> str:
        encoded_filename: str = base64.b64encode(filename.encode("utf-8")).decode("ascii")
        encoded_filetype: str = base64.b64encode(filetype.encode("utf-8")).decode("ascii")
        return "filename {},filetype {}".format(encoded_filename, encoded_filetype)


if __name__ == "__main__":
    unittest.main()
