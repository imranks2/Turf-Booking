#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/turf
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "==> Pulling latest code"
cd "$APP_DIR"
git pull --ff-only

echo "==> Backend dependencies"
cd "$BACKEND_DIR"
python3.12 -m venv .venv 2>/dev/null || true
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo "==> Database migrations"
./.venv/bin/alembic upgrade head

echo "==> Frontend build"
cd "$FRONTEND_DIR"
npm ci
npm run build

echo "==> Restarting services"
sudo systemctl restart turf-backend.service
sudo systemctl restart turf-celery.service
sudo systemctl reload nginx

echo "==> Done"
