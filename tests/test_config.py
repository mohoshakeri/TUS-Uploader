import unittest

from utils.config import parse_upload_directories


class ConfigTests(unittest.TestCase):
    def test_parse_upload_directories_normalizes_relative_directories(self) -> None:
        self.assertEqual(
            parse_upload_directories("documents, images/ ,clients/acme,documents"),
            ["documents", "images", "clients/acme"],
        )

    def test_parse_upload_directories_rejects_unsafe_paths(self) -> None:
        with self.assertRaises(ValueError):
            parse_upload_directories("/tmp")

        with self.assertRaises(ValueError):
            parse_upload_directories("../outside")


if __name__ == "__main__":
    unittest.main()
