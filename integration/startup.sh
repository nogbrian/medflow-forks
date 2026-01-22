#!/bin/bash

echo "========================================"
echo "MedFlow Integration Startup v3.1"
echo "========================================"
echo "Starting uvicorn directly..."

# Start uvicorn - no migrations or seeding at startup
# Use single worker to avoid issues
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
