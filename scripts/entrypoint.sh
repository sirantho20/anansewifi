#!/usr/bin/env sh
set -e

if [ "$POSTGRES_HOST" = "db" ]; then
  echo "Waiting for PostgreSQL..."
  until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 1
  done
fi

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

if [ "$1" = "" ]; then
  exec gunicorn ananseWifi.wsgi:application --bind 0.0.0.0:8000
fi

exec "$@"
