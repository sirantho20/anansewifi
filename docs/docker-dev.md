# Docker Development

## Services

- `web`: Django + Gunicorn (the only app service with `build: .`); `worker` and `beat` use the same `ananse-wifi:local` image
- external PostgreSQL via `DATABASE_URL` (no `db` service in the default compose file)
- `redis`: Redis broker/backend
- `worker`: Celery worker
- `beat`: Celery beat scheduler
- `radius`: FreeRADIUS daemon
- `nginx`: reverse proxy (proxies `/static/` to the app so Gunicorn+WhiteNoise serve files baked in the `ananse-wifi:local` image; no static volume)

`radius` is built from `radius/Dockerfile` and configured to:
- read auth policy from `radcheck` and `radreply`
- write accounting rows to `radacct`
- use the same `DATABASE_URL` as the app: `radius/entrypoint.sh` maps it to `rlm_sql` (set `RADIUS_USE_DATABASE_URL=0` and discrete `RADIUS_DB_*` only if you must bypass the URL)

## Local workflow

1. `cp .env.example .env`
2. `make migrate`
3. `make up`
4. `make seed`
5. Browse `http://localhost:18080` (or set `NGINX_HTTP_PORT=8080` in `.env` if port 8080 is available on your host)

## Live reload (optional)

The default `docker-compose.yml` does not bind-mount the project into the `web` container (so production and Coolify use the app copied into the image). To pick up local code changes without rebuilding `web` each time, copy the example override and bring the stack up again:

1. `cp docker-compose.override.example.yml docker-compose.override.yml`
2. `make up`

Compose automatically merges `docker-compose.override.yml` with `docker-compose.yml`. Remove `docker-compose.override.yml` when you need to test the same layout as a remote deploy.

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

## Redeploy timing (build vs. container start)

If a redeploy feels slow even when the Git tree is unchanged, check **where the time goes**:

- **Build / registry** — `pip install`, `apt-get`, or “pushing” layers. Often cache-related: use BuildKit, avoid `--no-cache` unless needed, and on hosts like **Coolify** turn on build cache so image layers from unchanged `Dockerfile` / `requirements.txt` reuse. A large Docker build context also slows the upload; this repo’s `.dockerignore` trims it.
- **Web container start** — Postgres wait, `migrate` / `ensure_default_plans`, and (when enabled) `collectstatic` in `scripts/entrypoint.sh` before Gunicorn. The default image runs migrations at boot; `collectstatic` is off by default because static assets are built into the app image.
