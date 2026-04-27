# RADIUS Flow

## Integration strategy

Django business models are the source of truth. A projection layer syncs RADIUS-facing rows (`radcheck`, `radreply`) from entitlement state. FreeRADIUS reads only those RADIUS tables and writes accounting rows to `radacct`.

## Authentication flow

1. Customer credentials/voucher redemption create or update entitlement.
2. Django projection sync writes RADIUS check/reply attributes:
   - `Cleartext-Password`
   - `Mikrotik-Rate-Limit`
   - `Session-Timeout`
   - `Idle-Timeout`
3. CHR sends Access-Request to FreeRADIUS.
4. FreeRADIUS evaluates `radcheck`/`radreply` and returns Access-Accept/Reject.

## Accounting flow

1. CHR sends accounting Start/Interim/Stop to FreeRADIUS.
2. FreeRADIUS writes accounting updates into `radacct`.
3. Django periodically consumes new `radacct` rows, writes `AccountingRecord`, updates `Session` usage totals, and closes session on stop events.
4. In development, accounting payloads can still be posted directly to `/api/radius/accounting/` for simulation.

## Expected MikroTik attributes

- `Mikrotik-Rate-Limit` for bandwidth profile
- `Session-Timeout` for max session duration
- `Idle-Timeout` for inactivity cutoff

## Local test strategy

- redeem a voucher through portal or API
- sync entitlement to `radcheck`/`radreply`
- submit accounting events through FreeRADIUS (or HTTP simulation endpoint for dev)
- verify session usage and dashboard metrics update

## Simulating CHR requests in development

- auth simulation:
  - `docker compose exec radius radtest demo-customer ANW-DEMO-001 127.0.0.1 0 ananse-radius-secret`
- accounting simulation:
  - `docker compose exec radius radclient -x 127.0.0.1:1813 acct ananse-radius-secret <<'EOF'\nUser-Name = \"demo-customer\"\nAcct-Status-Type = Interim-Update\nAcct-Session-Id = \"sim-1\"\nAcct-Unique-Session-Id = \"sim-1-unique\"\nNAS-IP-Address = 172.20.20.1\nCalling-Station-Id = \"AA-BB-CC-DD-EE-FF\"\nFramed-IP-Address = 10.10.10.10\nAcct-Input-Octets = 1024\nAcct-Output-Octets = 2048\nAcct-Session-Time = 120\nEOF`
  - then trigger sync window (or wait for beat schedule interval)
- optional direct HTTP simulation:
  - `curl -X POST http://localhost:18080/api/radius/accounting/ -H 'Content-Type: application/json' -d '{\"event_type\":\"interim\",\"username\":\"demo-customer\",\"session_id\":\"sim-1\",\"input_octets\":1024,\"output_octets\":2048,\"duration_seconds\":120}'` (or your `NGINX_HTTP_PORT` if not 18080)
- inspect results:
  - `radacct` entries in Postgres
  - Django admin (`/admin/`) for `Session` and `AccountingRecord`
  - API dashboard summary (`/api/dashboard/summary/`)

## Production router (MikroTik) and the public site

- **Postgres for FreeRADIUS** comes from the same `DATABASE_URL` as Django; no duplicate `RADIUS_DB_*` env block is required unless you set `RADIUS_USE_DATABASE_URL=0` (see [radius/entrypoint.sh](../radius/entrypoint.sh)). Coolify: give the `radius` service the same `DATABASE_URL` as `web` / `worker` / `beat`.
- The HTTPS portal (e.g. [anansewifi.shrt.fit](https://anansewifi.shrt.fit/)) is not the RADIUS transport. Point the router at **UDP 1812/1813** on the host running FreeRADIUS (VPS public IP, or a **DNS-only** A record; Cloudflare **proxied** hostnames do not carry RADIUS). Run `make check-radius-host` to see whether the name resolves to Cloudflare anycast.
- In server `.env`, set `RADIUS_NAS_CLIENT_IP` to the **source IP of RADIUS packets** (usually the router WAN). The optional `clients-optional-nas` block is rendered when that variable is set.
- Run `python manage.py ensure_nas_device <hotspot-gateway-ip>` so `NAS-IP-Address` in accounting matches a `NASDevice` row (often the LAN gateway, e.g. `192.168.10.1`).
- Import [mikrotik_radius_anansewifi.rsc](../mikrotik_radius_anansewifi.rsc) on the router after editing `radAddr` and `radSec`, then `make radius-test-local` (with `make up` and seeded demo user) to run `radtest` against the local FreeRADIUS container.
