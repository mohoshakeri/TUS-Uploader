from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from CONSTANTS import (
    HEADER_ALLOW_ALL,
    HEADER_ALLOW_METHODS,
    HEADER_EXPOSE_HEADERS,
    SECURITY_HEADER_CONTENT_TYPE_OPTIONS,
    SECURITY_HEADER_FRAME_OPTIONS,
    SECURITY_HEADER_PERMISSIONS_POLICY,
    SECURITY_HEADER_REFERRER_POLICY,
    SECURITY_VALUE_CONTENT_TYPE_OPTIONS,
    SECURITY_VALUE_FRAME_OPTIONS,
    SECURITY_VALUE_PERMISSIONS_POLICY,
    SECURITY_VALUE_REFERRER_POLICY,
)
from utils.config import CORS_ALLOWEDS


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWEDS,
        allow_credentials=False,
        allow_methods=HEADER_ALLOW_METHODS,
        allow_headers=HEADER_ALLOW_ALL,
        expose_headers=HEADER_EXPOSE_HEADERS,
    )

    @app.middleware("http")
    async def apply_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response: Response = await call_next(request)
        response.headers[SECURITY_HEADER_CONTENT_TYPE_OPTIONS] = SECURITY_VALUE_CONTENT_TYPE_OPTIONS
        response.headers[SECURITY_HEADER_FRAME_OPTIONS] = SECURITY_VALUE_FRAME_OPTIONS
        response.headers[SECURITY_HEADER_REFERRER_POLICY] = SECURITY_VALUE_REFERRER_POLICY
        response.headers[SECURITY_HEADER_PERMISSIONS_POLICY] = SECURITY_VALUE_PERMISSIONS_POLICY
        return response
