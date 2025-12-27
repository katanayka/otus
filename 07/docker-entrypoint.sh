#!/usr/bin/env sh
set -e

mkdir -p /app/data

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
