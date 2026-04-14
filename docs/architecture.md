# Architecture

## High-level design

Ananse WiFi follows a local-first architecture for CHR lab development:

1. CHR hotspot authenticates users against FreeRADIUS.
2. FreeRADIUS uses synchronized records generated from Django entities.
3. Django remains source of truth for plans, vouchers, customers, entitlements, sessions, and operations.
4. Accounting events are ingested into Django to power billing logic and dashboards.

## Components

- `web`: Django app + admin + portal + DRF API
- `db`: PostgreSQL for business and RADIUS-facing data
- `redis`: queue/result backend
- `worker`, `beat`: Celery task processing
- `radius`: FreeRADIUS runtime
- `nginx`: reverse proxy and static serving

## App boundaries

- `core`: shared base models, API router, command tooling
- `accounts`: staff profile and role metadata
- `customers`: customer identity and devices
- `plans`: speed profiles and commercial packages
- `vouchers`: voucher inventory and redemption workflow
- `payments`: manual-first payment ledger and gateway-ready abstraction
- `sessions`: entitlement lifecycle, usage sessions, accounting records
- `radius_integration`: synchronized auth/reply data and RADIUS ingestion endpoints
- `network`: sites, NAS devices, and RADIUS clients
- `audit`: business-state action logs
- `dashboard`: operator metrics and summaries
- `portal`: captive portal pages and simple user flows

## Why this works for CHR + Docker lab

- decouples network protocol concerns (RADIUS) from product concerns (billing/UI)
- allows iterative, local, reproducible testing with Compose
- keeps CHR integration realistic while preserving future production scaling options
