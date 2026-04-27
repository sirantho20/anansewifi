# Ananse WiFi Billing Platform

Local-first community WiFi billing and captive portal platform for CHR lab testing.

## Why this architecture

The project uses **Django as the source of truth** for business entities (plans, customers, vouchers, entitlements, sessions).  
FreeRADIUS consumes Django-projected `radcheck`/`radreply` policy rows while MikroTik CHR speaks only to FreeRADIUS.  
FreeRADIUS writes `radacct`, and Django consumes those records so billing workflows, dashboards, and operator tools stay in one place.

## Stack

- Python 3.12, Django, Django REST Framework
- PostgreSQL, Redis, Celery worker + beat
- FreeRADIUS container
- Nginx reverse proxy
- Docker Compose local orchestration

## Quick start

1. Copy environment file:
   - `cp .env.example .env`
2. Start stack:
   - `make up`
3. Seed demo data:
   - `make seed`
4. Open (nginx publishes host port **18080** by default; set `NGINX_HTTP_PORT=8080` in `.env` if you prefer 8080 and it is free):
   - Portal login: `http://localhost:18080/portal/login/`
   - Plans: `http://localhost:18080/portal/plans/`
   - Dashboard: `http://localhost:18080/dashboard/`
   - Admin: `http://localhost:18080/admin/`

## Demo workflow

- Use seeded user `demo-customer`
- Redeem a seeded voucher `ANW-DEMO-001`
- Confirm entitlement/session behavior in admin and API endpoints

## Key commands

- `make up` / `make down`
- `make makemigrations` / `make migrate`
- `make seed`
- `make test`
- `make lint`

## Docs

- `docs/architecture.md`
- `docs/data-model.md`
- `docs/radius-flow.md`
- `docs/docker-dev.md`
- `docs/chr-lab-setup.md`
- `docs/future-roadmap.md`

## MikroTik physical lab (hEX / Hotspot)

The repo also includes **stand-alone** router-side helpers in the same tree (not part of the Docker stack by default):

- `mikrotik_helper.py` — SSH to the gateway using `.env` (`ROUTER_IP`, etc.)
- `mikrotik_radius_anansewifi.rsc` — import on the router to point Hotspot RADIUS at the project’s FreeRADIUS (`radAddr` defaults to **77.237.238.58**; HTTPS may stay on Cloudflare — UDP does not use that name)
- `verify_hotspot_page.py` — `curl` the Hotspot login page over a chosen Wi-Fi interface (default: external redirect to `anansewifi.shrt.fit`; `--local-form` for the full on-router form)
- `scripts/verify_iphone_captive_prerequisites.sh` — read-only check of Hotspot hosts, `device-mode` proxy, walled-garden, bridge `use-ip-firewall`, and optional `http://login.hotspot` on `HOTSPOT_WIFI_IF` (default `en0`); iPhone steps are printed at the end (see `config.txt` §13–14)
- `hotspot/*.html` — files intended for `flash/hotspot` on the router (`login-local-form.html` is the RADIUS form backup; default `login.html` redirects to the public portal)
- `hotspot_external_portal.rsc` — walled-garden entry for HTTPS to the public portal before login
- `config.txt` — network narrative and troubleshooting notes

VPS RADIUS: set `RADIUS_NAS_CLIENT_IP` (router WAN), run `python manage.py ensure_nas_device` for the hotspot gateway IP (NAS-IP-Address), `make check-radius-host` for DNS sanity, `make radius-info` / `python3 scripts/radius_endpoint_info.py` when HTTPS is behind Cloudflare. See `.env.example`.

Use a small venv and `pip install -r requirements.txt` (includes `paramiko` and `python-dotenv` for these tools plus all Django stack deps for the app).
