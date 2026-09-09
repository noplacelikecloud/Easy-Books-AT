#!/bin/sh
set -e

# Ensure the data directory exists (local_config.py also does this, but belt-and-suspenders)
mkdir -p "${EB_DATA_DIR:-/data}"

echo "[startup] Running Alembic migrations..."
uv run --no-dev --frozen alembic upgrade head

echo "[startup] Seeding demo data (skips if any user already exists)..."
uv run --no-dev --frozen python -m scripts.autoseed_demo || echo "[startup] Demo seed skipped or non-fatal error"

if [ "$#" -gt 0 ]; then
    echo "[startup] Starting configured process: $1"
    exec uv run --no-dev --frozen "$@"
fi

echo "[startup] Starting API server..."
exec uv run --no-dev --frozen python -m uvicorn main:app --host 0.0.0.0 --port 8000
