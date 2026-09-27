#!/usr/bin/env bash
# SENTRA -- Render Build Script

set -o errexit

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate

echo "==> Creating production admin if configured..."

python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

email = os.environ.get("SENTRA_ADMIN_EMAIL")
password = os.environ.get("SENTRA_ADMIN_PASSWORD")

if email and password:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(password)
    user.save()

    if created:
        print(f"==> Production admin created: {email}")
    else:
        print(f"==> Production admin updated: {email}")
else:
    print("==> SENTRA_ADMIN_EMAIL/PASSWORD not configured; skipping admin creation.")

print("==> Build complete.")
PY