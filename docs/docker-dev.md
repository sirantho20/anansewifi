# Docker Development

## Services

- `web`: Django + Gunicorn
- `db`: PostgreSQL
- `redis`: Redis broker/backend
- `worker`: Celery worker
- `beat`: Celery beat scheduler
- `radius`: FreeRADIUS daemon
- `nginx`: reverse proxy

`radius` is built from `radius/Dockerfile` and configured to:
- read auth policy from `radcheck` and `radreply`
- write accounting rows to `radacct`
- use DB credentials from `.env` (`RADIUS_DB_*`)

## Local workflow

1. `cp .env.example .env`
2. `make migrate`
3. `make up`
4. `make seed`
5. Browse `http://localhost:8080`

## Common operations

- create migrations: `make makemigrations`
- apply migrations: `make migrate`
- run tests: `make test`
- stream logs: `make logs`
- stop stack: `make down`
- radius logs: `docker compose logs -f radius`
- radius auth simulation: `docker compose exec radius radtest demo-customer ANW-DEMO-001 127.0.0.1 0 ananse-radius-secret`

## Rebuild loop

When code or Docker dependencies change:

1. `make down`
2. `make up`
3. validate with portal/API/admin smoke checks
