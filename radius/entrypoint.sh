#!/bin/sh
set -eu

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
