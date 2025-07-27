#!/bin/bash
set -e
python manage.py migrate
python manage.py collectstatic --noinput
cp -r /app/collected_static/. /backend_static/static/
exec "$@"