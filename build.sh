#!/usr/bin/env bash
# SENTRA -- Render Build Script
# Runs automatically by Render before starting the web service.
# Do not put secrets directly in this file.

set -o errexit

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate

echo "==> Build complete."
