import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles



# Get ENV
DEBUG = os.getenv("DEBUG", "NO") == "YES"
PORT = int(os.getenv("PORT", 8989))
BASE_URL = os.getenv("BASE_URL", "http://localhost:8989")
CORS_ALLOWEDS = os.getenv(
    "CORS_ALLOWEDS",
    "http://localhost:8989",
).split(",")

# PATH
PROJECT_ROOT = os.path.dirname(__file__)


app = FastAPI(
    title="TUS Uploader",
    version="1.0.0",
    debug=DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWEDS,
    allow_methods=["GET"],
)


# Include Routers
def get_routes():
    import routes

    # Routes
    app.include_router(routes.router, prefix="/", tags=["routes"])
    
    # Static
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Uploads
    app.mount("/f", StaticFiles(directory="uploads"), name="uploads")


if __name__ == "__main__":
    logger.info("Start App ...")
    get_routes()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
