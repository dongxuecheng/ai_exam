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
    # 格式化服务名称为友好的标题
    formatted_name = service_name.replace('_', ' ').title()
    
    app = FastAPI(
        title=f"{formatted_name} {title_suffix}",
        description=f"API for {formatted_name.lower()} examination system",
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


# 便捷函数，使用YAML配置直接创建应用
def create_app_from_yaml(service_name: str, router: Any) -> FastAPI:
    """
    使用YAML配置创建应用的便捷函数
    
    Args:
        service_name: 服务名称，需要与config.yaml中的服务名一致
        router: API路由器
    
    Returns:
        配置好的FastAPI应用实例
    """
    from shared.utils.config import get_service_config
    config = get_service_config(service_name)
    return create_app(service_name, config, router)
