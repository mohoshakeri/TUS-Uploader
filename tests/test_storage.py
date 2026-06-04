import tempfile
import unittest
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from CONSTANTS import STORED_NAME_KEY
from utils import storage


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        self.project_root: Path = Path(self.temp_directory.name)
        self.original_uploads_dir: Path = storage.UPLOADS_DIR
        self.original_tmp_dir: Path = storage.TMP_DIR
        self.original_upload_directories: list[str] = storage.UPLOAD_DIRECTORIES
        storage.UPLOADS_DIR = self.project_root / "uploads"
        storage.TMP_DIR = self.project_root / "tmp"
        storage.UPLOAD_DIRECTORIES = []
        storage.ensure_directories()

    def tearDown(self) -> None:
        storage.UPLOADS_DIR = self.original_uploads_dir
        storage.TMP_DIR = self.original_tmp_dir
        storage.UPLOAD_DIRECTORIES = self.original_upload_directories
        self.temp_directory.cleanup()

    def test_write_read_and_delete_tus_metadata(self) -> None:
        payload: dict[str, Any] = {"offset": 3, STORED_NAME_KEY: "upload.txt"}

        storage.write_tus_metadata("abc", payload)

        self.assertEqual(storage.read_tus_metadata("abc"), payload)
        self.assertTrue(storage.tus_metadata_path("abc").exists())

        storage.delete_tus_metadata("abc")

        self.assertFalse(storage.tus_metadata_path("abc").exists())

    def test_read_tus_metadata_returns_404_for_missing_session(self) -> None:
        with self.assertRaises(HTTPException) as context:
            storage.read_tus_metadata("missing")

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_upload_path_from_meta_uses_stored_name(self) -> None:
        file_path: Path = storage.upload_path_from_meta({STORED_NAME_KEY: "file.pdf"})

        self.assertEqual(file_path, storage.UPLOADS_DIR / "file.pdf")

    def test_upload_path_from_meta_uses_stored_directory(self) -> None:
        file_path: Path = storage.upload_path_from_meta(
            {STORED_NAME_KEY: "file.pdf", "stored_directory": "reports"}
        )

        self.assertEqual(file_path, storage.UPLOADS_DIR / "reports" / "file.pdf")

    def test_ensure_directories_creates_configured_upload_directories(self) -> None:
        storage.UPLOAD_DIRECTORIES = ["reports", "media/images"]

        storage.ensure_directories()

        self.assertTrue((storage.UPLOADS_DIR / "reports").is_dir())
        self.assertTrue((storage.UPLOADS_DIR / "media" / "images").is_dir())

    def test_resolve_completed_file_finds_uploaded_file_by_upload_id(self) -> None:
        completed_file: Path = storage.UPLOADS_DIR / "abc.txt"
        completed_file.write_text("content", encoding="utf-8")

        self.assertEqual(storage.resolve_completed_file("abc"), completed_file)

    def test_resolve_completed_file_finds_uploaded_file_in_subdirectory(self) -> None:
        completed_dir: Path = storage.UPLOADS_DIR / "reports"
        completed_dir.mkdir()
        completed_file: Path = completed_dir / "abc.txt"
        completed_file.write_text("content", encoding="utf-8")

        self.assertEqual(storage.resolve_completed_file("abc"), completed_file)

    def test_resolve_completed_file_returns_404_when_file_is_missing(self) -> None:
        with self.assertRaises(HTTPException) as context:
            storage.resolve_completed_file("missing")

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
