#!/bin/bash
# Common configuration loader for all startup scripts
# Source this file to load environment variables

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

# Function to load environment variables from .env file
load_env() {
    if [ -f "$ENV_FILE" ]; then
        echo "Loading environment variables from $ENV_FILE..."
        # Export variables from .env file, ignoring comments and empty lines
        set -a
        source <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/^/export /')
        set +a
        echo "Environment variables loaded successfully."
    else
        echo "Warning: .env file not found at $ENV_FILE"
        echo "Using default values..."
        # Set default values if .env file doesn't exist
        export CONDA_ENV_NAME="fastapi"
        export PROJECT_DIR="/home/dxc/ai_exam"
    fi
}

# Function to activate conda environment
activate_conda() {
    local env_name="${1:-$CONDA_ENV_NAME}"
    echo "Activating conda environment: $env_name"
    eval "$(conda shell.bash hook)"
    conda activate "$env_name"
}

# Function to check and kill processes on a port
kill_port_processes() {
    local port="$1"
    echo "Checking port ${port}..."
    if lsof -Pi ":${port}" -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Port ${port} is in use. Killing existing processes..."
        lsof -ti ":${port}" | xargs kill -9 2>/dev/null
        echo "Processes on port ${port} have been terminated."
        # Wait a moment for processes to fully terminate
        sleep 2
    else
        echo "Port ${port} is available."
    fi
}

# Function to start FastAPI application
start_fastapi() {
    local service_name="$1"
    local host="$2"
    local port="$3"
    
    echo "Starting FastAPI application for $service_name..."
    echo "Host: $host, Port: $port"
    uvicorn "${service_name}.main:app" --host "$host" --port "$port"
}

# Load environment variables when this script is sourced
load_env
