"""YAML-based configuration utilities for AI exam services."""

import yaml
from pathlib import Path
from typing import List, Set, Dict, Any
from shared.schemas import StreamConfig, ServerConfig


class ConfigManager:
    """Centralized configuration manager for YAML-based configs."""
    
    def __init__(self, config_path: str = None):
        """Initialize config manager with YAML file path."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        services = self._config.get('services', {})
        if service_name not in services:
            raise ValueError(f"Service '{service_name}' not found in configuration")
        return services[service_name]
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration."""
        return self._config.get('global', {})
    
    def create_server_config(self, service_name: str) -> ServerConfig:
        """Create ServerConfig for a service from YAML configuration."""
        service_config = self.get_service_config(service_name)
        global_config = self.get_global_config()
        
        # Get base directory
        base_dir = Path(global_config.get('project_dir', Path.cwd()))
        weights_base_dir = base_dir / 'weights' / service_name
        images_dir = base_dir / 'images' / service_name
        
        # Ensure directories exist
        weights_base_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Get server configuration
        server_config = service_config['server']
        # Use global IP instead of service-specific IP
        server_ip = global_config.get('ip', '127.0.0.1')
        server_port = server_config['port']
        static_mount_path = server_config['static_mount_path']
        # Generate img_url_path dynamically from global IP, port and static path
        img_url_path = f"http://{server_ip}:{server_port}{static_mount_path}"
        
        # Get GPU device configuration
        defaults = global_config.get('defaults', {})
        gpu_device = service_config.get('gpu_device', defaults.get('gpu_device', 0))
        
        # Build weights paths from simplified models list
        weights_paths = []
        models = service_config.get('models', [])
        for weight_file in models:
            # weight_file is now directly the filename string
            weight_path = str(weights_base_dir / weight_file)
            weights_paths.append(weight_path)
        
        # Create stream configurations from streams list
        stream_configs = self._create_stream_configs(service_config, global_config)
        
        return ServerConfig(
            server_ip=server_ip,
            server_port=server_port,
            weights_paths=weights_paths,
            images_dir=images_dir,
            static_mount_path=static_mount_path,
            img_url_path=img_url_path,
            stream_configs=stream_configs,
            gpu_device=gpu_device
        )
    
    def _create_stream_configs(self, service_config: Dict[str, Any], global_config: Dict[str, Any]) -> List[StreamConfig]:
        """Create stream configurations from service config."""
        configs = []
        defaults = global_config.get('defaults', {})
        queue_size = defaults.get('queue_size', 100)
        frame_skip = defaults.get('frame_skip', 10)
        
        # Get models list to create model to index mapping
        models = service_config.get('models', [])
        model_to_index = {model: idx for idx, model in enumerate(models)}
        
        streams = service_config.get('streams', [])
        for stream in streams:
            rtsp_url = stream['url']
            
            # Convert model names to indices
            model_names = stream.get('models', [])
            target_models = set()
            for model_name in model_names:
                if model_name in model_to_index:
                    target_models.add(model_to_index[model_name])
                else:
                    raise ValueError(f"Model '{model_name}' not found in models list for service")
            
            config = StreamConfig(
                rtsp_url=rtsp_url,
                queue_size=queue_size,
                frame_skip=frame_skip,
                target_models=target_models
            )
            configs.append(config)
        
        return configs
    
    def get_service_names(self) -> List[str]:
        """Get list of all configured service names."""
        return list(self._config.get('services', {}).keys())
    
    def get_service_models(self, service_name: str) -> List[str]:
        """Get model configurations for a service."""
        service_config = self.get_service_config(service_name)
        return service_config.get('models', [])
    
    def get_service_streams(self, service_name: str) -> List[Dict[str, Any]]:
        """Get stream configurations for a service."""
        service_config = self.get_service_config(service_name)
        return service_config.get('streams', [])


# Global config manager instance
config_manager = ConfigManager()


def get_service_config(service_name: str) -> ServerConfig:
    """Convenience function to get server configuration for a service."""
    return config_manager.create_server_config(service_name)


def get_service_names() -> List[str]:
    """Get list of all configured service names."""
    return config_manager.get_service_names()


def get_service_models(service_name: str) -> List[str]:
    """Get model configurations for a service."""
    return config_manager.get_service_models(service_name)


def get_service_streams(service_name: str) -> List[Dict[str, Any]]:
    """Get stream configurations for a service."""
    return config_manager.get_service_streams(service_name)
