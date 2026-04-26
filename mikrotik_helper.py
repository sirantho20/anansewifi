#!/usr/bin/env python3
"""
SSH helper for MikroTik RouterOS. Loads ROUTER_USERNAME, ROUTER_PASSWORD, and host
from .env next to this script (or current working directory).

Host: ROUTER_IP when set, else ROUTER_IP_2. Use `--host ADDR` to override for one-off SSH.

Hotspot runs on 192.168.10.0/24—use that LAN to test captive portal and login flows.
That segment may have no general internet. Cursor model calls, package installs,
and other public-internet traffic should use the host's Wi‑Fi (or another path
with a default route), not only the Hotspot lab segment.
On mode=home, if walled-garden shows "inactivated, not allowed by device-mode",
see enable_proxy_device_mode.rsc and config.txt section 14.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Missing dependency: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependency: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


def find_dotenv() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here / ".env", Path.cwd() / ".env"):
        if candidate.is_file():
            return candidate
    return here / ".env"


def load_router_env() -> tuple[str, str, str]:
    load_dotenv(find_dotenv())
    host = os.environ.get("ROUTER_IP", "").strip() or os.environ.get(
        "ROUTER_IP_2", ""
    ).strip()
    user = os.environ.get("ROUTER_USERNAME", "").strip()
    password = os.environ.get("ROUTER_PASSWORD", "")
    if not host or not user:
        sys.exit(
            "Set ROUTER_IP (or ROUTER_IP_2 as fallback) and ROUTER_USERNAME in .env "
            "(and ROUTER_PASSWORD if used)."
        )
    return host, user, password


def router_ssh(
    host: str,
    user: str,
    password: str,
    command: str,
    *,
    port: int = 22,
    timeout: float = 30.0,
) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        port=port,
        username=user,
        password=password or None,
        allow_agent=False,
        look_for_keys=False,
        timeout=timeout,
        banner_timeout=timeout,
    )
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        exit_status = stdout.channel.recv_exit_status()
        if err.strip():
            out = (out + "\n" + err).strip() + "\n"
        if exit_status != 0 and not out.strip():
            sys.exit(f"Remote command failed (exit {exit_status}).")
        return out
    finally:
        client.close()


PRESETS: dict[str, str] = {
    "status": (
        "/system resource print; "
        "/interface print; "
        "/ip address print; "
        "/ip route print detail; "
        "/ip dhcp-server lease print"
    ),
    "export": "/export compact",
    "firewall": "/ip firewall filter print stats; /ip firewall nat print stats",
    # Captive portal: Hotspot on bridge-main (only ether4+ether5). ether3 is not on this bridge.
    "hotspot": (
        "/system device-mode print; "
        "/ip hotspot print detail; "
        "/ip hotspot profile print where name=cp-main; "
        "/ip hotspot user print; "
        "/interface bridge port print where bridge=bridge-main; "
        "/ip dhcp-server network print detail"
    ),
    # Captive portal troubleshooting: hosts, cookies, bindings, DNS for guest LAN.
    "hotspot-diagnose": (
        "/system device-mode print; "
        "/ip proxy print; "
        "/ip route print where dst-address=0.0.0.0/0; "
        "/ping 8.8.8.8 count=1; "
        "/ip hotspot print detail; "
        "/ip hotspot profile print detail where name=cp-main; "
        "/ip hotspot host print detail; "
        "/ip hotspot active print detail; "
        "/ip hotspot cookie print; "
        "/ip hotspot ip-binding print detail; "
        "/ip hotspot walled-garden print; "
        "/ip hotspot walled-garden ip print; "
        "/ip dhcp-server network print detail where address~192.168.10; "
        "/ip dns static print where name~hotspot; "
        "/interface bridge port print where bridge=bridge-main"
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run RouterOS commands on MikroTik via SSH (.env credentials)."
    )
    parser.add_argument(
        "preset",
        nargs="?",
        choices=sorted(PRESETS.keys()),
        help="Predefined command bundle (default: status).",
    )
    parser.add_argument(
        "-c",
        "--command",
        metavar="CMD",
        help="Raw RouterOS command (overrides preset). Use RouterOS syntax.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=22,
        help="SSH port (default: 22).",
    )
    parser.add_argument(
        "--host",
        metavar="ADDR",
        help="Override SSH host (still uses ROUTER_USERNAME / ROUTER_PASSWORD from .env).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        metavar="SEC",
        help="TCP/SSH connect and remote-exec timeout in seconds (default: 30).",
    )
    args = parser.parse_args()

    host, user, password = load_router_env()
    if args.host:
        host = args.host.strip()
    if args.command:
        cmd = args.command.strip()
    else:
        cmd = PRESETS[args.preset or "status"]

    sys.stdout.write(
        router_ssh(
            host, user, password, cmd, port=args.port, timeout=args.timeout
        )
    )


if __name__ == "__main__":
    main()
