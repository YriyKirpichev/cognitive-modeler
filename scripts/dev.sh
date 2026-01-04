#!/bin/bash

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found, using defaults"
fi

export FRONTEND_PORT=${FRONTEND_PORT:-5175}
export BACKEND_PORT=${BACKEND_PORT:-8001}
export BACKEND_HOST=${BACKEND_HOST:-localhost}

echo "Starting development environment..."
echo "Frontend port: $FRONTEND_PORT"
echo "Backend port: $BACKEND_PORT"
echo "Backend host: $BACKEND_HOST"

npx concurrently -k \
  "cd frontend && npm run dev -- --port $FRONTEND_PORT" \
  "cd backend && BACKEND_PORT=$BACKEND_PORT uv run fastapi dev app/main.py --port $BACKEND_PORT" \
  "npx wait-on http://localhost:$FRONTEND_PORT && electron ."