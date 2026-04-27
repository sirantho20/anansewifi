#!/usr/bin/env python3
"""Upload hotspot/login.html to MikroTik flash/hotspot/ for the captive portal (no /import)."""

from __future__ import annotations

import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    load_dotenv(REPO / ".env")
    import os

    host = os.environ.get("ROUTER_IP", "").strip() or os.environ.get("ROUTER_IP_2", "").strip()
    user = os.environ.get("ROUTER_USERNAME", "").strip()
    password = os.environ.get("ROUTER_PASSWORD", "")
    if not host or not user:
        print("Set ROUTER_IP and ROUTER_USERNAME in .env", file=sys.stderr)
        return 1

    login_html = REPO / "hotspot" / "login.html"
    if not login_html.is_file():
        print(f"Missing {login_html}", file=sys.stderr)
        return 1

    remote_path = "flash/hotspot/login.html"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        port=22,
        username=user,
        password=password or None,
        allow_agent=False,
        look_for_keys=False,
        timeout=30.0,
    )
    try:
        sftp = client.open_sftp()
        try:
            try:
                sftp.mkdir("flash/hotspot")
            except OSError:
                pass
            sftp.put(str(login_html), remote_path)
        finally:
            sftp.close()
        print(f"Uploaded {login_html.name} -> {host}:{remote_path}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
