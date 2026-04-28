up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose run --rm web python manage.py migrate

makemigrations:
	docker compose run --rm web python manage.py makemigrations

seed:
	docker compose run --rm web python manage.py seed_demo_data

# Create/update Site + NASDevice from RADIUS_NAS_DEVICE_* / RADIUS_NAS_CLIENT_IP in .env
ensure-nas:
	docker compose run --rm web python manage.py ensure_nas_device

test:
	# No Postgres in this compose file: use SQLite in the test run (see DJANGO_USE_SQLITE in ananseWifi/settings.py).
	# CELERY_TASK_ALWAYS_EAGER=1 is set in conftest.py.
	docker compose run --rm -e CELERY_TASK_ALWAYS_EAGER=1 -e DJANGO_USE_SQLITE=1 web pytest -q

# Verifies the app can connect using DATABASE_URL from .env (migrations not run; safe for read-only check).
verify-database-url:
	docker compose run --rm -e RUN_MIGRATIONS=0 -e RUN_COLLECTSTATIC=0 web sh -c '\
		python -c "import os, django; os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"ananseWifi.settings\"); django.setup(); \
from django.db import connection; connection.ensure_connection(); print(\"DATABASE_URL: connection OK\");" && \
		python manage.py check'

check-deploy:
	docker compose run --rm -e DJANGO_DEBUG=0 web python manage.py check --deploy

lint:
	docker compose run --rm web ruff check .

# Show public DNS for the portal host. Cloudflare-proxied A records (104.x / 172.67.x) do not pass RADIUS UDP — use VPS IP or a grey-cloud A record for the router RADIUS address field.
check-radius-host:
	@dig +short anansewifi.shrt.fit A || true

# Explain DNS vs origin; suggest RADIUS target from DATABASE_URL; show outbound IP for RADIUS_NAS_CLIENT_IP. Optional: RADIUS test against DATABASE_URL host (needs deployment to accept your IP as a client).
radius-info:
	@python3 scripts/radius_endpoint_info.py

radius-test-vps:
	@python3 scripts/radius_endpoint_info.py --radtest

# Portal HTTPS + DNS/radius-info (no local FreeRADIUS required).
radius-sanity:
	@curl -sS -o /dev/null -w "HTTPS anansewifi.shrt.fit/portal/login/ -> %{http_code}\n" --max-time 15 https://anansewifi.shrt.fit/portal/login/ || true
	@python3 scripts/radius_endpoint_info.py

# Requires `make up` with the radius service running. Seeds user must exist (make seed) for demo-customer / DEMO01.
radius-test-local:
	docker compose exec -T radius radtest demo-customer DEMO01 127.0.0.1 0 ananse-radius-secret
