#!/bin/bash

# YAML-based Configuration Loader for AI Exam Services
# =====================================================
# This script provides common functions for loading YAML-based configurations
# and managing service startup with the new configuration system.

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# YAML Configuration Functions
# =============================

check_yaml_config() {
    local config_file="${PROJECT_DIR}/config.yaml"
    if [ ! -f "$config_file" ]; then
        echo "Error: YAML configuration file not found: $config_file"
        exit 1
    fi
    echo "Using YAML configuration: $config_file"
}

get_service_config() {
    local service_name="$1"
    local config_key="$2"
    
    python3 -c "
import yaml
import sys
from pathlib import Path

config_path = Path('${PROJECT_DIR}/config.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    service_config = config['services']['${service_name}']
    global_config = config.get('global', {})
    
    if '${config_key}' == 'port':
        print(service_config['server']['port'])
    elif '${config_key}' == 'ip':
        # Use global IP instead of service-specific IP
        print(global_config.get('ip', '127.0.0.1'))
    else:
        print(service_config.get('${config_key}', ''))
except Exception as e:
    print(f'Error loading config: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# Service Management Functions
# ============================

start_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "Usage: start_service <service_name>"
        return 1
    fi
    
    echo "Starting service: $service_name"
    
    # Check YAML configuration
    check_yaml_config
    
    # Get service configuration
    local port=$(get_service_config "$service_name" "port")
    local host=$(get_service_config "$service_name" "ip")
    
    if [ -z "$port" ] || [ -z "$host" ]; then
        echo "Error: Could not retrieve configuration for service: $service_name"
        return 1
    fi
    
    echo "Service: $service_name"
    echo "Host: $host, Port: $port"
    
    # Check if port is already in use
    check_and_kill_port "$port"
    
    # Activate conda environment
    activate_conda_env
    
    # Change to project directory
    cd "$PROJECT_DIR" || exit 1
    
    # Start the service
    echo "Starting $service_name on $host:$port..."
    uvicorn "${service_name}.main:app" --host "$host" --port "$port"
}

check_and_kill_port() {
    local port="$1"
    
    if [ -z "$port" ]; then
        echo "Error: Port not specified"
        return 1
    fi
    
    echo "Checking port $port..."
    
    # Find process using the port
    local pid=$(lsof -ti:$port)
    
    if [ -n "$pid" ]; then
        echo "Port $port is in use by process $pid. Killing it..."
        kill -9 $pid
        sleep 2
        
        # Verify the process is killed
        if lsof -ti:$port > /dev/null; then
            echo "Warning: Port $port is still in use"
        else
            echo "Port $port is now free"
        fi
    else
        echo "Port $port is free"
    fi
}

activate_conda_env() {
    # Get conda environment name from YAML
    local conda_env=$(python3 -c "
import yaml
from pathlib import Path

config_path = Path('${PROJECT_DIR}/config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print(config['global'].get('conda_env', 'fastapi'))
")
    
    if [ -z "$conda_env" ]; then
        conda_env="fastapi"
    fi
    
    echo "Activating conda environment: $conda_env"
    
    # Initialize conda for bash
    eval "$(conda shell.bash hook)"
    
    # Activate environment
    conda activate "$conda_env"
    
    if [ $? -eq 0 ]; then
        echo "Successfully activated conda environment: $conda_env"
    else
        echo "Warning: Failed to activate conda environment: $conda_env"
        echo "Using current environment"
    fi
}

# Utility Functions
# =================

list_services() {
    echo "Available services:"
    python3 -c "
import yaml
from pathlib import Path

config_path = Path('${PROJECT_DIR}/config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

for service_name in config['services'].keys():
    service_config = config['services'][service_name]
    port = service_config['server']['port']
    print(f'  - {service_name} (port: {port})')
"
}

show_service_info() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "Usage: show_service_info <service_name>"
        return 1
    fi
    
    python3 -c "
import yaml
from pathlib import Path

config_path = Path('${PROJECT_DIR}/config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

service_config = config['services']['${service_name}']
server_config = service_config['server']
global_config = config.get('global', {})
global_ip = global_config.get('ip', '127.0.0.1')

print(f'Service: ${service_name}')
print(f'  Server: {global_ip}:{server_config[\"port\"]}')
print(f'  Static Path: {server_config[\"static_mount_path\"]}')
print(f'  Image URL: http://{global_ip}:{server_config[\"port\"]}{server_config[\"static_mount_path\"]}')
print(f'  Models: {len(service_config[\"models\"])}')
print(f'  Streams: {len(service_config[\"streams\"])}')
"
}

# Auto-load configuration when script is sourced
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    # Script is being executed directly
    echo "YAML Configuration Manager for AI Exam Services"
    echo "==============================================="
    
    case "${1:-}" in
        "list")
            list_services
            ;;
        "info")
            show_service_info "$2"
            ;;
        "start")
            start_service "$2"
            ;;
        *)
            echo "Usage: $0 {list|info|start} [service_name]"
            echo ""
            echo "Commands:"
            echo "  list              - List all available services"
            echo "  info <service>    - Show service information"
            echo "  start <service>   - Start a service"
            echo ""
            echo "Examples:"
            echo "  $0 list"
            echo "  $0 info basket_k2"
            echo "  $0 start basket_k2"
            ;;
    esac
else
    # Script is being sourced
    echo "YAML configuration functions loaded"
fi