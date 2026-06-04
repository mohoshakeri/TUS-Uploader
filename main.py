import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from CONSTANTS import (
    APP_HOST,
    APP_IMPORT_PATH,
    APP_TITLE,
    APP_VERSION,
    STATIC_ROUTE,
    UPLOADS_ROUTE,
)
from utils.config import DEBUG, PORT, STATIC_DIR, UPLOADS_DIR
from utils.middlewares import register_middlewares
from utils.routes import router
from utils.storage import ensure_directories


def create_app() -> FastAPI:
    ensure_directories()
    app_instance: FastAPI = FastAPI(title=APP_TITLE, version=APP_VERSION, debug=DEBUG)
    register_middlewares(app_instance)
    app_instance.mount(STATIC_ROUTE, StaticFiles(directory=STATIC_DIR), name=STATIC_DIR.name)
    app_instance.mount(UPLOADS_ROUTE, StaticFiles(directory=UPLOADS_DIR), name=UPLOADS_DIR.name)
    app_instance.include_router(router)
    return app_instance


app: FastAPI = create_app()


if __name__ == "__main__":
    uvicorn.run(APP_IMPORT_PATH, host=APP_HOST, port=PORT, reload=DEBUG)
