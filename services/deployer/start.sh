#!/bin/bash
set -e

# Start TorchServe in the background
echo "Starting TorchServe..."
torchserve --start --ncs --model-store /app/model_store --ts-config /app/config.properties &

# Wait for TorchServe to be ready
echo "Waiting for TorchServe to start..."
until curl -s http://localhost:8081/ping; do
    sleep 1
done
echo "TorchServe is running."

# Start the Flask application
echo "Starting Flask API..."
exec python main.py
