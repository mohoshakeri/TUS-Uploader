import unittest

from fastapi.middleware.cors import CORSMiddleware

from main import app


class MainAppTests(unittest.TestCase):
    def test_app_registers_cors_middleware(self) -> None:
        middleware_classes: list[type] = [
            middleware.cls for middleware in app.user_middleware
        ]

        self.assertIn(CORSMiddleware, middleware_classes)


if __name__ == "__main__":
    unittest.main()
