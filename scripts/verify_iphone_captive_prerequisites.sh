#!/usr/bin/env sh
# Run checks from config.txt section 13–14: Hotspot + iOS captive sheet prerequisites.
# Read-only. Requires: Docker, docker compose, and .env (ROUTER_*) for SSH.
# Optional: curl on the host to hit http://login.hotspot and http://neverssl.com on en0.
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

MHD='docker compose run --rm --no-deps --entrypoint "" web python3 mikrotik_helper.py'

echo "=== 1) Hotspot hosts (H=DHCP; A=authorized). Phone should appear when connected. ==="
$MHD -c "/ip hotspot host print detail" || true

echo ""
echo "=== 2) Device mode (expect proxy: yes for walled-garden to apply) ==="
$MHD -c "/system device-mode print" || true

echo ""
echo "=== 3) Walled garden (captive.apple.com). If using HTTPS to anansewifi.shrt.fit, import hotspot_external_portal.rsc. ==="
$MHD -c "/ip hotspot walled-garden print; /ip hotspot walled-garden ip print" || true

echo ""
echo "=== 4) Bridge: use-ip-firewall (expect yes for Hotspot HTTP on bridge) ==="
$MHD -c "/interface bridge settings print" || true

WIFI_IF="${HOTSPOT_WIFI_IF:-en0}"
echo ""
echo "=== 5) HTTP from this machine on ${WIFI_IF} (non-fatal) ==="
if command -v curl >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  curl -sS -o /dev/null -w "  http://login.hotspot/  final=%{url_effective} code=%{http_code}\n" -L --connect-timeout 5 --max-time 10 --interface "$WIFI_IF" "http://login.hotspot/" || echo "  login.hotspot: (failed — connect this Mac to Hotspot WiFi?)"
  # shellcheck disable=SC2086
  curl -sS -o /dev/null -w "  http://neverssl.com/   final=%{url_effective} code=%{http_code}\n" -L --connect-timeout 5 --max-time 10 --interface "$WIFI_IF" "http://neverssl.com/" || echo "  neverssl: (failed)"
else
  echo "  (curl not installed)"
fi

echo ""
echo "=== iPhone: do manually ==="
echo "  - Airplane on + WiFi only, or turn cellular off; forget SSID; rejoin."
echo "  - No VPN, iCloud Private Relay, or per-network Private DNS for that SSID."
echo "  - Safari: http://login.hotspot or http://neverssl.com (system sheet is optional; see config.txt 13)."
