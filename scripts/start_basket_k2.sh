#!/bin/bash

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate fastapi

# Configuration
PORT=5005
HOST="127.0.0.1"

# Check if port is in use and kill processes
echo "Checking port ${PORT}..."
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null ; then
    echo "Port ${PORT} is in use. Killing existing processes..."
    lsof -ti :${PORT} | xargs kill -9
    echo "Processes on port ${PORT} have been terminated."
    # Wait a moment for processes to fully terminate
    sleep 2
fi
# Change to the welding_k2 directory
cd /home/xcd/ai_exam
# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate fastapi

# Run FastAPI application
echo "Starting FastAPI application..."
uvicorn basket_k2.main:app --host ${HOST} --port ${PORT}