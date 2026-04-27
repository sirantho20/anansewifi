#!/usr/bin/env sh
set -e

# Wait for PostgreSQL when not using SQLite (any host, including external / Coolify)
if [ "${DJANGO_USE_SQLITE:-0}" != "1" ]; then
  PG_HOST="${POSTGRES_HOST:-db}"
  PG_PORT="${POSTGRES_PORT:-5432}"
  if [ -n "${DATABASE_URL:-}" ]; then
    _res=$(python -c "
import os
from urllib.parse import urlparse
u = os.environ.get('DATABASE_URL', '')
if not u:
    raise SystemExit(0)
p = urlparse(u)
h = p.hostname
port = p.port if p.port is not None else 5432
if h:
    print(h)
    print(port)
" 2>/dev/null) || _res=""
    if [ -n "$_res" ]; then
      PG_HOST=$(printf '%s\n' "$_res" | head -1)
      PG_PORT=$(printf '%s\n' "$_res" | tail -1)
    fi
  fi
  if [ -n "$PG_HOST" ] && [ -n "$PG_PORT" ]; then
    echo "Waiting for PostgreSQL at ${PG_HOST}:${PG_PORT}..."
    until nc -z "$PG_HOST" "$PG_PORT"; do
      sleep 1
    done
  fi
fi

# Default 0: static is baked in the image. Set to 1 when using a bind mount or after changing static assets.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
  # Idempotent: ensures default unlimited plans exist in DATABASE_URL / Postgres (and any DB)
  python manage.py ensure_default_plans
fi

if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

if [ "$1" = "" ]; then
  if [ "${DJANGO_DEBUG:-0}" = "1" ]; then
    exec gunicorn --reload -c gunicorn.conf.py ananseWifi.wsgi:application
  else
    exec gunicorn -c gunicorn.conf.py ananseWifi.wsgi:application
  fi
fi

exec "$@"
