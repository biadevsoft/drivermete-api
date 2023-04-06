#!/usr/bin/env sh
set -e

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate

gunicorn app.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --master \
  --enable-threads \
  --module app.wsgi &
daphne -b 0.0.0.0 -p 8001 app.asgi:application