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
