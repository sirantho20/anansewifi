#!/bin/sh
set -eu

# Align FreeRADIUS SQL with Django when DATABASE_URL is PostgreSQL.
# Overrides RADIUS_DB_* / POSTGRES_* from .env. Set RADIUS_USE_DATABASE_URL=0 to disable.
if [ "${RADIUS_USE_DATABASE_URL:-1}" != "0" ] && [ -n "${DATABASE_URL:-}" ]; then
  case "$DATABASE_URL" in
    postgres:*|postgresql:*)
      _radius_db_env="$(python3 -c "
import os
import shlex
from urllib.parse import urlparse, unquote

u = urlparse(os.environ.get('DATABASE_URL', ''))
if u.scheme not in ('postgres', 'postgresql'):
    raise SystemExit(0)
host = u.hostname or ''
port = u.port if u.port is not None else 5432
path = (u.path or '/').strip('/')
name = path.split('/')[0] if path else ''
user = unquote(u.username or '')
password = unquote(u.password or '')
if not host or not name:
    raise SystemExit(0)
for key, val in (
    ('RADIUS_DB_HOST', host),
    ('RADIUS_DB_PORT', str(port)),
    ('RADIUS_DB_NAME', name),
    ('RADIUS_DB_USER', user),
    ('RADIUS_DB_PASSWORD', password),
):
    print(f'export {key}={shlex.quote(val)}')
" 2>/dev/null)" || _radius_db_env=""
      if [ -n "$_radius_db_env" ]; then
        eval "$_radius_db_env"
      fi
      ;;
  esac
fi

: "${RADIUS_DB_HOST:=${POSTGRES_HOST:-db}}"
: "${RADIUS_DB_PORT:=${POSTGRES_PORT:-5432}}"
: "${RADIUS_DB_NAME:=${POSTGRES_DB:-ananse_wifi}}"
: "${RADIUS_DB_USER:=${POSTGRES_USER:-ananse}}"
: "${RADIUS_DB_PASSWORD:=${POSTGRES_PASSWORD:-ananse}}"
: "${RADIUS_SQL_DIALECT:=postgresql}"
: "${RADIUS_CLIENT_SECRET:=ananse-radius-secret}"

render_template() {
  template_path="$1"
  target_path="$2"
  sed \
    -e "s|__RADIUS_DB_HOST__|${RADIUS_DB_HOST}|g" \
    -e "s|__RADIUS_DB_PORT__|${RADIUS_DB_PORT}|g" \
    -e "s|__RADIUS_DB_NAME__|${RADIUS_DB_NAME}|g" \
    -e "s|__RADIUS_DB_USER__|${RADIUS_DB_USER}|g" \
    -e "s|__RADIUS_DB_PASSWORD__|${RADIUS_DB_PASSWORD}|g" \
    -e "s|__RADIUS_SQL_DIALECT__|${RADIUS_SQL_DIALECT}|g" \
    -e "s|__RADIUS_CLIENT_SECRET__|${RADIUS_CLIENT_SECRET}|g" \
    "$template_path" > "$target_path"
}

render_template /opt/ananse-radius/clients.conf.template /etc/freeradius/clients.conf
render_template /opt/ananse-radius/sql.template /etc/freeradius/mods-enabled/sql
cp /opt/ananse-radius/default.site /etc/freeradius/sites-enabled/default

NS="${LOG_NAMESPACE:-base.radius}"
freeradius -X 2>&1 | awk -v ns="$NS" '{print ns " | " $0}'
