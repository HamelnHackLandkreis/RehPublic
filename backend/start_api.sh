#!/bin/bash

# Start the Wildlife Camera API
# Run this script from the backend directory

echo "Starting Wildlife Camera API..."
echo "API will be available at: http://127.0.0.1:8000"
echo "API docs at: http://127.0.0.1:8000/docs"
echo ""

uvicorn api.main:app --reload --port 8000
