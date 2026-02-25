#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
echo "==> Running collectstatic..."
python manage.py collectstatic --noinput
echo "==> Static files collected. Contents of staticfiles/:"
ls -la staticfiles/ || echo "staticfiles directory not found!"
ls staticfiles/css/ || echo "css directory not found in staticfiles!"

# Apply database migrations
python manage.py migrate

# Seed valid student/staff registration numbers
echo "==> Seeding valid registration IDs..."
python manage.py seed_valid_ids

# Create superuser if DJANGO_SUPERUSER_USERNAME is set (only creates if not exists)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "==> Creating superuser..."
    python manage.py createsuperuser --noinput || echo "Superuser already exists or creation failed"
    echo "==> Setting superuser role to admin..."
    python manage.py setup_admin
fi
