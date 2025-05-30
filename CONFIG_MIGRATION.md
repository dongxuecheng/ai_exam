# AI Exam Environment Configuration

This document describes the new environment-based configuration system for the AI Exam project.

## Overview

The configuration system has been migrated from hardcoded Python configurations to environment variable-based configurations using `.env` files. This provides better flexibility, security, and environment-specific customization.

**All startup scripts and service configurations now use environment variables loaded from the `.env` file.**

## Features

- **Environment-based**: All configurations are now loaded from environment variables
- **Centralized**: Single `.env` file for all services
- **Flexible**: Easy to customize for different environments (development, production, etc.)
- **Secure**: Sensitive information can be kept in environment variables
- **Type-safe**: Automatic type conversion and validation
- **Script Integration**: Startup scripts use shared configuration loading

## Configuration Files

### Main Configuration Files

- **`.env`**: Main environment configuration file (active configuration)
- **`.env.example`**: Example configuration template with documentation
- **`shared/utils/config.py`**: Configuration loading utilities
- **`scripts/common.sh`**: Common script configuration loader

### Service Configuration Files

Each service now has a simplified configuration file that uses the utility functions:

- `basket_k2/core/config.py`
- `welding_k1/core/config.py`
- `welding_k2/core/config.py`
- `welding2_k2/core/config.py`
- `welding3_k2/core/config.py`
- `sling_k2/core/config.py`

### Startup Scripts

All startup scripts now use environment configuration:

- `scripts/start_basket_k2.sh`
- `scripts/start_welding_k1.sh`
- `scripts/start_welding_k2.sh`
- `scripts/start_welding2_k2.sh`
- `scripts/start_welding3_k2.sh`
- `scripts/start_sling_k2.sh`

## Environment Variables Structure

### Global Script Settings

```bash
CONDA_ENV_NAME=fastapi
PROJECT_DIR=/home/dxc/ai_exam
BASE_DIR=/home/dxc/ai_exam
DEFAULT_QUEUE_SIZE=100
DEFAULT_FRAME_SKIP=10
```

### Service-Specific Settings

For each service (e.g., `BASKET_K2`), the following variables are configured:

#### Server Configuration
```bash
BASKET_K2_SERVER_IP=127.0.0.1
BASKET_K2_SERVER_PORT=5005
BASKET_K2_STATIC_MOUNT_PATH=/basket_k2
BASKET_K2_IMG_URL_PATH=http://127.0.0.1:5005/basket_k2
```

#### Model Weights
```bash
BASKET_K2_WEIGHT_POSE1=yolo11l-pose1.pt
BASKET_K2_WEIGHT_OIL_TANK=yz_oil_tank.pt
BASKET_K2_WEIGHT_POSE2=yolo11l-pose2.pt
BASKET_K2_WEIGHT_GROUNDING_WIRE=yz_grounding_wire.pt
```

#### RTSP Streams
```bash
BASKET_K2_STREAM1_URL=rtsp://admin:yaoan1234@172.16.22.237/cam/realmonitor?channel=1&subtype=0
BASKET_K2_STREAM1_TARGET_MODELS=0
BASKET_K2_STREAM2_URL=rtsp://admin:yaoan1234@172.16.22.230/cam/realmonitor?channel=1&subtype=0
BASKET_K2_STREAM2_TARGET_MODELS=1
BASKET_K2_STREAM3_URL=rtsp://admin:yaoan1234@172.16.22.242/cam/realmonitor?channel=1&subtype=0
BASKET_K2_STREAM3_TARGET_MODELS=2,3
```

## Port Configuration

Each service uses a unique port:

- **BASKET_K2**: 5005
- **WELDING1_K1**: 5001
- **WELDING1_K2**: 5002
- **WELDING2_K2**: 5003
- **WELDING3_K2**: 5004
- **SLING_K2**: 5006

## Services Configuration

### Supported Services

1. **BASKET_K2**: Basket inspection service (3 streams, 4 weights)
2. **WELDING1_K1**: Basic welding service (1 stream, 2 weights)
3. **WELDING1_K2**: Advanced welding service (5 streams, 6 weights)
4. **WELDING2_K2**: Enhanced welding service (5 streams, 7 weights)
5. **WELDING3_K2**: Extended welding service (5 streams, 8 weights)
6. **SLING_K2**: Sling inspection service (2 streams, 4 weights)

### Configuration Pattern

Each service follows this pattern:

```python
from shared.utils.config import create_server_config

SERVICE_CONFIG = create_server_config(
    service_prefix='SERVICE_NAME',
    weights_keys=['WEIGHT1', 'WEIGHT2', ...],
    stream_count=N
)
```

## Startup Scripts

### Common Configuration Loading

All startup scripts use the common configuration loader:

```bash
#!/bin/bash

# Get script directory and load common configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Load environment variables
load_env_config

# Get configuration for service
PORT=${SERVICE_NAME_SERVER_PORT}
HOST=${SERVICE_NAME_SERVER_IP}

# Run FastAPI application
uvicorn service_name.main:app --host ${HOST} --port ${PORT}
```

### Script Features

- **Automatic port detection and cleanup**
- **Conda environment activation**
- **Configuration validation**
- **Error handling**
- **Consistent logging**

## Usage

### Setting up a new environment

1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your specific values:
   ```bash
   nano .env
   ```

3. The configuration will be automatically loaded when importing any service config.

### Adding a new service

1. Add environment variables to `.env` following the naming pattern
2. Create a config file using the utility functions
3. Update the documentation

### Customizing for different environments

You can use different `.env` files for different environments:

```bash
# Development
cp .env.example .env.development

# Production  
cp .env.example .env.production

# Load specific environment
export ENV_FILE=.env.production
```

## Utility Functions

### Core Functions

- `get_env_var(key, default=None)`: Get string environment variable
- `get_env_int(key, default=None)`: Get integer environment variable
- `parse_target_models(models_str)`: Parse comma-separated model IDs
- `create_stream_configs(service_prefix, stream_count)`: Create stream configurations
- `create_server_config(service_prefix, weights_keys, stream_count)`: Create complete server config

### Example Usage

```python
from shared.utils.config import get_env_var, create_server_config

# Get individual variables
server_ip = get_env_var('BASKET_K2_SERVER_IP')
server_port = get_env_int('BASKET_K2_SERVER_PORT')

# Create complete configuration
config = create_server_config(
    service_prefix='BASKET_K2',
    weights_keys=['POSE1', 'OIL_TANK', 'POSE2', 'GROUNDING_WIRE'],
    stream_count=3
)
```

## Migration Notes

### Changes Made

1. **Dependencies**: Added `python-dotenv` for environment variable loading
2. **Structure**: Simplified config files using utility functions
3. **Flexibility**: All hardcoded values moved to environment variables
4. **Validation**: Added type checking and required variable validation

### Backward Compatibility

- All existing service interfaces remain the same
- Configuration objects maintain the same structure
- No changes required in service code that uses the configurations

### Benefits

- **Security**: Credentials and URLs not stored in code
- **Flexibility**: Easy to change configurations without code changes  
- **Environment-specific**: Different configs for dev/staging/production
- **Maintainability**: Centralized configuration management
- **Documentation**: Clear separation of configurable values

## Troubleshooting

### Common Issues

1. **Missing environment variables**: Check that all required variables are set in `.env`
2. **File path issues**: Ensure `.env` file is in the project root
3. **Type conversion errors**: Verify integer values are valid numbers
4. **Stream configuration**: Check comma-separated target model lists

### Validation

Test configuration loading:

```bash
cd /home/dxc/ai_exam
python -c "from basket_k2.core.config import BASKET_K2_CONFIG; print('Config loaded successfully')"
```

### Debug Environment Loading

```bash
python -c "from shared.utils.config import get_env_var; print('Base dir:', get_env_var('BASE_DIR'))"
```
