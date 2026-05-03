from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from utils.config import CORS_ALLOWEDS


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWEDS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "HEAD", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Location", "Upload-Offset", "Upload-Length", "Tus-Resumable"],
    )

    @app.middleware("http")
    async def apply_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
