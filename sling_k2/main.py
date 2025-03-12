from fastapi import FastAPI
from .api import router 
from fastapi.staticfiles import StaticFiles
from .core import SLING_K2_CONFIG

def create_app() -> FastAPI:
    """应用程序工厂"""
    #settings = Settings()
    app = FastAPI(
        title="Sling K2 API",
        description="API for sling examination system",
        version="1.0.0"
    )
    app.mount(SLING_K2_CONFIG.static_mount_path, StaticFiles(directory=SLING_K2_CONFIG.images_dir))
    app.include_router(router)
    return app

app = create_app()