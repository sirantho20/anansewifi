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
  - `curl -X POST http://localhost:8080/api/radius/accounting/ -H 'Content-Type: application/json' -d '{\"event_type\":\"interim\",\"username\":\"demo-customer\",\"session_id\":\"sim-1\",\"input_octets\":1024,\"output_octets\":2048,\"duration_seconds\":120}'`
- inspect results:
  - `radacct` entries in Postgres
  - Django admin (`/admin/`) for `Session` and `AccountingRecord`
  - API dashboard summary (`/api/dashboard/summary/`)
