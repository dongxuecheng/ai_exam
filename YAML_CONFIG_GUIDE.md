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
  ip: 127.0.0.1
  defaults:
    queue_size: 100
    frame_skip: 10

services:
  service_name:
    server:
      port: 5001
      static_mount_path: /service_name
    
    models:
      - model_file1.pt
      - model_file2.pt
    
    streams:
      - url: rtsp://camera_url
        models: [model_file1.pt, model_file2.pt]
```

## Benefits of YAML Configuration

1. **Centralized Management**: All configurations in one place
2. **Clean Structure**: Clear hierarchy and organization
3. **Easy Maintenance**: Simple to add/modify services
4. **Direct Model Reference**: Models referenced by filename, not abstract names
5. **Intuitive Stream Configuration**: Streams directly specify which models to use
6. **Type Safety**: Automatic validation and error handling
7. **No Index Management**: No need to remember model indices

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

# Get models for a specific service (returns list of model filenames)
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
      - model1.pt
      - model2.pt
    
    streams:
      - url: rtsp://camera1
        models: [model1.pt]
      - url: rtsp://camera2
        models: [model2.pt]
```

2. Create service config file:
```python
# new_service/core/config.py
from shared.utils.config import get_service_config

# Automatically loads models and streams from YAML
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
