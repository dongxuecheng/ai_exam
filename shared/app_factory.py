"""
通用应用工厂 - 为所有服务创建标准化的FastAPI应用
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from shared.schemas import ServerConfig
from typing import Any


def create_app(
    service_name: str,
    config: ServerConfig,
    router: Any,
    title_suffix: str = "API"
) -> FastAPI:
    """
    创建标准化的FastAPI应用实例
    
    Args:
        service_name: 服务名称
        config: 服务器配置
        router: API路由器
        title_suffix: 标题后缀
    
    Returns:
        配置好的FastAPI应用实例
    """
    app = FastAPI(
        title=f"{service_name.title().replace('_', ' ')} {title_suffix}",
        description=f"API for {service_name.replace('_', ' ')} examination system",
        version="1.0.0"
    )
    
    # 挂载静态文件目录
    app.mount(
        config.static_mount_path, 
        StaticFiles(directory=config.images_dir)
    )
    
    # 包含API路由
    app.include_router(router)
    
    return app
