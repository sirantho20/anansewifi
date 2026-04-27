#!/usr/bin/env python3
"""
Resolve the portal hostname, explain when Cloudflare hides the origin, and suggest a
RADIUS UDP target from DATABASE_URL in .env (same host as Postgres is often the app VPS).

Does not print database credentials.
"""

from __future__ import annotations

import argparse
import ipaddress
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path


# https://www.cloudflare.com/ips-v4 (subset; extend if needed)
_CLOUDFLARE_IPV4 = [
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22",
]


def _in_cloudflare_v4(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
        if ip.version != 4:
            return False
        for cidr in _CLOUDFLARE_IPV4:
            if ip in ipaddress.ip_network(cidr):
                return True
    except ValueError:
        return False
    return False


def _load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _db_host_from_database_url(url: str) -> str | None:
    try:
        u = urllib.parse.urlparse(url)
        if u.scheme not in ("postgres", "postgresql"):
            return None
        return u.hostname
    except Exception:
        return None


def _dig_a(name: str) -> list[str]:
    try:
        p = subprocess.run(
            ["dig", "+short", name, "A"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    addrs: list[str] = []
    for line in p.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith(";"):
            addrs.append(line)
    return addrs


def _outbound_v4() -> str | None:
    for url in (
        "https://ifconfig.io/ip",
        "https://ifconfig.me/ip",
    ):
        try:
            with urllib.request.urlopen(url, timeout=6) as r:  # noqa: S310
                text = r.read().decode().strip()
                ipaddress.ip_address(text)
                return text
        except Exception:
            continue
    return None


def _p(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="RADIUS / DNS / VPS hint helper")
    parser.add_argument(
        "--host",
        default="anansewifi.shrt.fit",
        help="Portal hostname to resolve (default: anansewifi.shrt.fit)",
    )
    parser.add_argument(
        "--radtest",
        action="store_true",
        help="Run radtest against DATABASE_URL host (needs Docker image anansewifi-radius)",
    )
    parser.add_argument(
        "--user",
        default="demo-customer",
        help="radtest User-Name",
    )
    parser.add_argument(
        "--pass",
        dest="pass_",
        default="ANW-DEMO-001",
        help="radtest password",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    envp = root / ".env"
    env = _load_dotenv(envp)
    db_url = env.get("DATABASE_URL", "")
    vps = _db_host_from_database_url(db_url) if db_url else None

    _p("=== Portal DNS (public A records) ===")
    a_records = _dig_a(args.host)
    if not a_records:
        _p("  (no A records or dig not available)")
    for a in a_records:
        cf = "Cloudflare (proxied) — RADIUS UDP does not use this" if _in_cloudflare_v4(a) else "not a known Cloudflare v4 (may be origin or other CDN)"
        _p(f"  {a}  ({cf})")

    _p("")
    _p("=== Origin / RADIUS target (not available from proxied DNS alone) ===")
    if vps and vps not in a_records:
        _p(
            f"  Suggested RADIUS/UDP target from DATABASE_URL hostname: {vps} "
            f"(set router / MikroTik radAddr to this IP, or a grey-cloud A record).\n"
            f"  On the FreeRADIUS host, set RADIUS_NAS_CLIENT_IP to the router's WAN, "
            f"or your test machine's public IP (see below), so Access-Request is accepted."
        )
    elif vps:
        _p(
            f"  DATABASE_URL host: {vps} (same as A record above — if this is the VPS, you can use it for RADIUS when UDP 1812/1813 is open.)"
        )
    else:
        _p("  Set DATABASE_URL in .env to derive a host, or set RADIUS_NAS_CLIENT_IP on the server manually.")

    my_ip = _outbound_v4()
    _p("")
    _p("=== This machine's public IPv4 (for RADIUS_NAS_CLIENT_IP on the server when testing with radtest) ===")
    if my_ip:
        _p(f"  {my_ip}")
    else:
        _p("  (could not detect)")

    if args.radtest:
        if not vps:
            print("--radtest skipped: no DATABASE_URL host with postgres scheme", file=sys.stderr)
            return 1
        secret = env.get("RADIUS_CLIENT_SECRET", "ananse-radius-secret")
        _p("")
        _p(f"=== radtest to {vps} (0 = PAP) ===")
        try:
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "anansewifi-radius",
                    "radtest",
                    args.user,
                    args.pass_,
                    vps,
                    "0",
                    secret,
                ],
                check=False,
            )
        except FileNotFoundError:
            print("docker not found", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
