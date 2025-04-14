from fastapi import FastAPI
from .api import router 
from fastapi.staticfiles import StaticFiles
from .core import WELDING_K1_CONFIG

def create_app() -> FastAPI:
    """应用程序工厂"""
    #settings = Settings()
    app = FastAPI(
        title="Welding K1 API",
        description="API for sling examination system",
        version="1.0.0"
    )
    app.mount(WELDING_K1_CONFIG.static_mount_path, StaticFiles(directory=WELDING_K1_CONFIG.images_dir))
    app.include_router(router)
    return app

app = create_app()