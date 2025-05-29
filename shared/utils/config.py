"""Shared configuration utilities for loading from environment variables."""

import os
from pathlib import Path
from typing import List, Set
from dotenv import load_dotenv
from shared.schemas import StreamConfig, ServerConfig

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

def get_env_var(key: str, default: str = None) -> str:
    """Get environment variable with optional default."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is required but not set")
    return value

def get_env_int(key: str, default: int = None) -> int:
    """Get environment variable as integer."""
    value = os.getenv(key)
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"Environment variable {key} is required but not set")
    return int(value)

def parse_target_models(models_str: str) -> Set[int]:
    """Parse comma-separated model IDs into a set of integers."""
    if not models_str:
        return set()
    return {int(x.strip()) for x in models_str.split(',')}

def get_base_dir() -> Path:
    """Get the base directory from environment or use default."""
    base_dir_str = get_env_var('BASE_DIR', str(Path(__file__).parent.parent))
    return Path(base_dir_str)

def create_stream_configs(service_prefix: str, stream_count: int) -> List[StreamConfig]:
    """Create stream configurations for a service from environment variables.
    
    Args:
        service_prefix: The service prefix (e.g., 'BASKET_K2', 'WELDING_K1')
        stream_count: Number of streams to create
    """
    configs = []
    queue_size = get_env_int('DEFAULT_QUEUE_SIZE', 100)
    frame_skip = get_env_int('DEFAULT_FRAME_SKIP', 10)
    
    for i in range(1, stream_count + 1):
        url_key = f"{service_prefix}_STREAM{i}_URL"
        models_key = f"{service_prefix}_STREAM{i}_TARGET_MODELS"
        
        rtsp_url = get_env_var(url_key)
        target_models_str = get_env_var(models_key)
        target_models = parse_target_models(target_models_str)
        
        config = StreamConfig(
            rtsp_url=rtsp_url,
            queue_size=queue_size,
            frame_skip=frame_skip,
            target_models=target_models
        )
        configs.append(config)
    
    return configs

def create_server_config(service_prefix: str, weights_keys: List[str], stream_count: int) -> ServerConfig:
    """Create server configuration for a service from environment variables.
    
    Args:
        service_prefix: The service prefix (e.g., 'BASKET_K2', 'WELDING_K1')
        weights_keys: List of weight file keys to load
        stream_count: Number of streams for this service
    """
    base_dir = get_base_dir()
    weights_base_dir = base_dir / 'weights' / service_prefix.lower()
    images_dir = base_dir / 'images' / service_prefix.lower()
    
    # Ensure directories exist
    weights_base_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Get server configuration
    server_ip = get_env_var(f"{service_prefix}_SERVER_IP")
    server_port = get_env_int(f"{service_prefix}_SERVER_PORT")
    static_mount_path = get_env_var(f"{service_prefix}_STATIC_MOUNT_PATH")
    img_url_path = get_env_var(f"{service_prefix}_IMG_URL_PATH")
    
    # Build weights paths
    weights_paths = []
    for weight_key in weights_keys:
        weight_filename = get_env_var(f"{service_prefix}_WEIGHT_{weight_key}")
        weight_path = str(weights_base_dir / weight_filename)
        weights_paths.append(weight_path)
    
    # Create stream configurations
    stream_configs = create_stream_configs(service_prefix, stream_count)
    
    return ServerConfig(
        server_ip=server_ip,
        server_port=server_port,
        weights_paths=weights_paths,
        images_dir=images_dir,
        static_mount_path=static_mount_path,
        img_url_path=img_url_path,
        stream_configs=stream_configs
    )
