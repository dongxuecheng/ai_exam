#!/bin/bash

# Load common configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# Service specific configuration
SERVICE_NAME="welding3_k2"
HOST="${WELDING3_K2_SERVER_IP}"
PORT="${WELDING3_K2_SERVER_PORT}"

# Change to project directory
cd "${PROJECT_DIR}"

# Activate conda environment
activate_conda "${CONDA_ENV_NAME}"

# Kill existing processes on port
kill_port_processes "${PORT}"

# Start FastAPI application
start_fastapi "${SERVICE_NAME}" "${HOST}" "${PORT}"