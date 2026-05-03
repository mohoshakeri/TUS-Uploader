import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from utils.config import DEBUG, PORT, STATIC_DIR, UPLOADS_DIR
from utils.middlewares import register_middlewares
from utils.routes import router
from utils.storage import ensure_directories


def create_app() -> FastAPI:
    ensure_directories()
    app = FastAPI(title="TUS Uploader", version="1.0.0", debug=DEBUG)
    register_middlewares(app)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/f", StaticFiles(directory=UPLOADS_DIR), name="uploads")
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=DEBUG)
