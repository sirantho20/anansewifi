# Future Roadmap

## Near-term hardening

- add background jobs for periodic RADIUS sync and stale session cleanup
- add richer operator pages for active sessions, auth failures, and voucher operations
- improve audit trail coverage for sensitive actions

## Payments and integrations

- plug in external payment providers behind gateway abstraction
- webhook ingestion for payment confirmation and entitlement activation
- settlement and reseller commission foundations

## Network automation

- add MikroTik API/SSH integration module for provisioning and disconnect actions
- add CoA/Disconnect support when CHR policy requirements are finalized
- add site inventory and AP policy templates

## Scaling

- multi-site separation and tenancy strategy
- asynchronous event pipeline for accounting-heavy deployments
- observability stack (metrics/traces/log aggregation)
