#!/bin/bash

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate fastapi

# Configuration
PORT=5002
HOST="172.16.20.163"

# Check if port is in use and kill processes
echo "Checking port ${PORT}..."
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null ; then
    echo "Port ${PORT} is in use. Killing existing processes..."
    lsof -ti :${PORT} | xargs kill -9
    echo "Processes on port ${PORT} have been terminated."
    # Wait a moment for processes to fully terminate
    sleep 2
fi

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate fastapi

# Run FastAPI application
echo "Starting FastAPI application..."
uvicorn app_welding_k2:app --host ${HOST} --port ${PORT}