#!/bin/bash

# Default to port 8000 if PORT is not set
PORT=${PORT:-8000}

echo "=========================================="
echo "Starting Franchise Matcher Backend"
echo "=========================================="
echo "Port: $PORT"
echo "Host: 0.0.0.0"
echo "=========================================="

# Use exec to replace shell process with uvicorn
# This ensures proper signal handling for Railway
exec uvicorn src.backend.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --no-access-log


