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
