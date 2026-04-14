# Data Model

## Core entities

- `Customer`: hotspot end user profile
- `Device`: customer MAC association
- `Plan`: package definition (price, quota model, limits)
- `SpeedProfile`: rate profile mapped to MikroTik-compatible attributes
- `VoucherBatch`: bulk voucher generation grouping
- `Voucher`: redeemable access token with state transitions
- `Entitlement`: active usage rights from voucher/payment
- `Session`: active/closed user access session
- `AccountingRecord`: normalized accounting payload snapshots
- `Payment`: manual-first payment records
- `Site`: physical/logical deployment location
- `NASDevice`: CHR/router endpoint metadata
- `RadiusClient`: RADIUS client identity metadata
- `AuditLog`: operator and system state changes

## Key relationships

- `Plan` -> `SpeedProfile` (many-to-one)
- `Voucher` -> `Plan`, `VoucherBatch`, optional `Customer`
- `Entitlement` -> `Plan`, optional `Customer`, optional `Voucher`
- `Session` -> optional `Customer`, optional `Entitlement`, optional `NASDevice`
- `AccountingRecord` -> optional `Session`
- `Payment` -> `Customer`, optional `Plan`
- `NASDevice` -> `Site`
- `RadiusClient` -> `NASDevice`

## Lifecycle highlights

- voucher redemption creates and activates an entitlement
- accounting updates feed usage counters on sessions
- stop accounting closes the session and records disconnect reason
