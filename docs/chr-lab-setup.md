# CHR Lab Setup

## Interface assumptions

- `ether1`: WAN/uplink
- `ether2`: hotspot/client LAN to AP
- `ether3`: backend LAN to Docker host services

## Suggested IP plan

- Hotspot subnet (`ether2`): `172.20.20.0/24`
  - CHR gateway: `172.20.20.1`
- Backend/management subnet (`ether3`): `172.20.30.0/24`
  - CHR mgmt IP: `172.20.30.1`
  - Linux host IP: `172.20.30.2`
  - FreeRADIUS reachable via Linux host on UDP `1812/1813`

## Service expectations

- RADIUS auth/accounting: UDP 1812/1813
- Django/nginx operator access: TCP host port from `NGINX_HTTP_PORT` (default **18080** in `docker-compose`; use 8080 only if you set `NGINX_HTTP_PORT=8080` and nothing else binds it)
- PostgreSQL and Redis remain internal to Docker network

## FreeRADIUS client example

Use `radius/raddb/clients.conf` as a baseline:

```
client chr_hotspot {
    ipaddr = 172.20.20.1
    secret = ananse-radius-secret
    shortname = chr-hotspot
}
```

## Validation checklist

1. Confirm CHR can reach Linux host backend subnet.
2. Register CHR as a RADIUS client with shared secret.
3. Redeem voucher in portal.
4. Trigger login from AP client.
5. Confirm accounting records and session updates in admin/dashboard.

## One-host two-NIC approach

- NIC1 can bridge to AP/hotspot side for real client testing.
- NIC2 can be reserved for management/uplink/internet connectivity.
- Use host routes or bridge configuration to keep hotspot and backend traffic separated.
