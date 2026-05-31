import base64
import unittest

from fastapi import HTTPException, status

from CONSTANTS import (
    CONTENT_TYPE_OCTET_STREAM,
    HEADER_CONTENT_TYPE,
    HEADER_TUS_RESUMABLE,
    HEADER_UPLOAD_LENGTH,
    HEADER_UPLOAD_OFFSET,
    HEADER_UPLOAD_PASSWORD,
    TUS_VERSION,
)
from utils import validators


class RequestStub:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers: dict[str, str] = headers


class ValidatorTests(unittest.TestCase):
    def test_parse_upload_metadata_decodes_base64_values(self) -> None:
        filename: str = base64.b64encode("photo.png".encode("utf-8")).decode("ascii")
        filetype: str = base64.b64encode("image/png".encode("utf-8")).decode("ascii")
        raw_metadata: str = "filename {},filetype {}".format(filename, filetype)

        parsed: dict[str, str] = validators.parse_upload_metadata(raw_metadata)

        self.assertEqual(parsed["filename"], "photo.png")
        self.assertEqual(parsed["filetype"], "image/png")

    def test_parse_upload_metadata_rejects_invalid_base64(self) -> None:
        with self.assertRaises(HTTPException) as context:
            validators.parse_upload_metadata("filename abc")

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_file_metadata_accepts_allowed_file(self) -> None:
        metadata: dict[str, str] = {"filename": "report.pdf", "filetype": "application/pdf"}

        suffix: str
        content_type: str
        suffix, content_type = validators.validate_file_metadata(metadata, 128)

        self.assertEqual(suffix, ".pdf")
        self.assertEqual(content_type, "application/pdf")

    def test_validate_file_metadata_uses_mimetype_guess_when_filetype_is_empty(self) -> None:
        metadata: dict[str, str] = {"filename": "photo.png", "filetype": ""}

        suffix: str
        content_type: str
        suffix, content_type = validators.validate_file_metadata(metadata, 128)

        self.assertEqual(suffix, ".png")
        self.assertEqual(content_type, "image/png")

    def test_validate_file_metadata_rejects_unsupported_filename_characters(self) -> None:
        metadata: dict[str, str] = {"filename": "bad/name.png", "filetype": "image/png"}

        with self.assertRaises(HTTPException) as context:
            validators.validate_file_metadata(metadata, 128)

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)

    def test_parse_upload_length_requires_positive_integer_header(self) -> None:
        request: RequestStub = RequestStub({HEADER_UPLOAD_LENGTH: "42"})

        self.assertEqual(validators.parse_upload_length(request), 42)

        with self.assertRaises(HTTPException):
            validators.parse_upload_length(RequestStub({HEADER_UPLOAD_LENGTH: "abc"}))

    def test_parse_upload_offset_requires_integer_header(self) -> None:
        request: RequestStub = RequestStub({HEADER_UPLOAD_OFFSET: "12"})

        self.assertEqual(validators.parse_upload_offset(request), 12)

        with self.assertRaises(HTTPException):
            validators.parse_upload_offset(RequestStub({}))

    def test_validate_tus_resumable_requires_version_header(self) -> None:
        validators.validate_tus_resumable(RequestStub({HEADER_TUS_RESUMABLE: TUS_VERSION}))

        with self.assertRaises(HTTPException) as context:
            validators.validate_tus_resumable(RequestStub({HEADER_TUS_RESUMABLE: "0.9.0"}))

        self.assertEqual(context.exception.status_code, status.HTTP_412_PRECONDITION_FAILED)

    def test_validate_upload_password_rejects_wrong_password(self) -> None:
        original_password: str = validators.UPLOAD_PASSWORD
        validators.UPLOAD_PASSWORD = "secret"
        try:
            with self.assertRaises(HTTPException) as context:
                validators.validate_upload_password(RequestStub({HEADER_UPLOAD_PASSWORD: "wrong"}))
        finally:
            validators.UPLOAD_PASSWORD = original_password

        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_validate_patch_content_type_requires_tus_content_type(self) -> None:
        validators.validate_patch_content_type(
            RequestStub({HEADER_CONTENT_TYPE: CONTENT_TYPE_OCTET_STREAM})
        )

        with self.assertRaises(HTTPException) as context:
            validators.validate_patch_content_type(RequestStub({HEADER_CONTENT_TYPE: "text/plain"}))

        self.assertEqual(context.exception.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


if __name__ == "__main__":
    unittest.main()
