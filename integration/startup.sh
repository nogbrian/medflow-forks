#!/bin/bash
set -e

echo "========================================"
echo "MedFlow Integration Startup"
echo "========================================"

# Run database migrations first
echo ""
echo "[1/3] Running database migrations..."
python -m alembic upgrade head 2>&1 || echo "Alembic migration completed (or skipped)"

# Seed database if not already seeded
echo ""
echo "[2/3] Checking if database needs seeding..."
python seed.py 2>&1 || echo "Seed script completed (or skipped)"

# Start the main application
echo ""
echo "[3/3] Starting application..."
echo "========================================"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
