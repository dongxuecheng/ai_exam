# AI Exam YAML Configuration Guide

## Overview

The AI Exam project now uses a centralized YAML configuration system for managing all services, models, and video streams. This provides better organization, easier maintenance, and cleaner configuration management.

## Configuration Files

### Main Configuration
- `config.yaml` - Central YAML configuration file containing all service configurations

### Service Configuration Files
Each service now has a simplified configuration file that automatically loads from YAML:
- `basket_k2/core/config.py`
- `sling_k2/core/config.py`
- `welding1_k1/core/config.py`
- `welding1_k2/core/config.py`
- `welding2_k2/core/config.py`
- `welding3_k2/core/config.py`

## YAML Configuration Structure

```yaml
global:
  project_dir: /home/dxc/ai_exam
  conda_env: fastapi
  defaults:
    queue_size: 100
    frame_skip: 10

services:
  service_name:
    server:
      ip: 127.0.0.1
      port: 5001
      static_mount_path: /service_name
      img_url_path: http://127.0.0.1:5001/service_name
    
    models:
      - name: MODEL_NAME
        weight_file: model_file.pt
    
    streams:
      - url: rtsp://camera_url
        target_models: [0, 1]
```

## Benefits of YAML Configuration

1. **Centralized Management**: All configurations in one place
2. **Clean Structure**: Clear hierarchy and organization
3. **Easy Maintenance**: Simple to add/modify services
4. **No Hardcoding**: Models and streams defined in config, not code
5. **Type Safety**: Automatic validation and error handling

## Usage

### Loading Service Configuration
```python
from shared.utils.yaml_config import get_service_config

# Automatically loads models and streams from YAML
config = get_service_config('service_name')
```

### Getting Service Information
```python
from shared.utils.yaml_config import get_service_names, get_service_models, get_service_streams

# Get all configured services
services = get_service_names()

# Get models for a specific service
models = get_service_models('service_name')

# Get streams for a specific service
streams = get_service_streams('service_name')
```

## Adding a New Service

1. Add service configuration to `config.yaml`:
```yaml
services:
  new_service:
    server:
      ip: 127.0.0.1
      port: 5008
      static_mount_path: /new_service
      img_url_path: http://127.0.0.1:5008/new_service
    
    models:
      - name: MODEL1
        weight_file: model1.pt
      - name: MODEL2
        weight_file: model2.pt
    
    streams:
      - url: rtsp://camera1
        target_models: [0]
      - url: rtsp://camera2
        target_models: [1]
```

2. Create service config file:
```python
# new_service/core/config.py
from shared.utils.yaml_config import get_service_config
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights' / "new_service"
IMAGES_DIR = BASE_DIR / 'images' / "new_service"

WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

NEW_SERVICE_CONFIG = get_service_config('new_service')
```

## Migration from .env

The project has been migrated from environment variable-based configuration (`.env` files) to YAML-based configuration. The old system required:
- Hardcoded model names and stream counts in each service
- Complex environment variable management
- Difficult maintenance and updates

The new YAML system eliminates these issues by:
- Auto-discovering models and streams from configuration
- Centralized management
- Cleaner, more maintainable code structure
