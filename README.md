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
4. Open:
   - Portal login: `http://localhost:8080/portal/login/`
   - Plans: `http://localhost:8080/portal/plans/`
   - Dashboard: `http://localhost:8080/dashboard/`
   - Admin: `http://localhost:8080/admin/`

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
