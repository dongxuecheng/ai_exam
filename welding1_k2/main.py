from fastapi import FastAPI
from .api import router 
from fastapi.staticfiles import StaticFiles
from .core import WELDING1_K2_CONFIG

def create_app() -> FastAPI:
    """应用程序工厂"""
    #settings = Settings()
    app = FastAPI(
        title="Welding1 K2 API",
        description="API for welding examination system",
        version="1.0.0"
    )
    app.mount(WELDING1_K2_CONFIG.static_mount_path, StaticFiles(directory=WELDING1_K2_CONFIG.images_dir))
    app.include_router(router)
    return app

app = create_app()