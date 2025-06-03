from .api import router 
from .core import config, service_name
from shared.app_factory import create_app as create_fastapi_app

def create_app():
    """应用程序工厂"""
    return create_fastapi_app(service_name, config, router)

app = create_app()