#!/bin/bash

# Default to port 8000 if PORT is not set
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."
exec uvicorn src.backend.main:app --host 0.0.0.0 --port "$PORT"


