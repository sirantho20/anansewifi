#!/usr/bin/env python3
"""Upload router_bootstrap_lab.rsc + hotspot/login.html to MikroTik and run /import."""

from __future__ import annotations

import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(REPO / ".env")
    import os

    host = os.environ.get("ROUTER_IP", "").strip() or os.environ.get("ROUTER_IP_2", "").strip()
    user = os.environ.get("ROUTER_USERNAME", "").strip()
    password = os.environ.get("ROUTER_PASSWORD", "")
    if not host or not user:
        sys.exit("Set ROUTER_IP and ROUTER_USERNAME in .env")

    rsc = REPO / "router_bootstrap_lab.rsc"
    login_html = REPO / "hotspot" / "login.html"
    if not rsc.is_file():
        sys.exit(f"Missing {rsc}")

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
            sftp.put(str(rsc), "router_bootstrap_lab.rsc")
            if login_html.is_file():
                try:
                    sftp.mkdir("flash/hotspot")
                except OSError:
                    pass
                sftp.put(str(login_html), "flash/hotspot/login.html")
        finally:
            sftp.close()

        # /import can run minutes on a busy router; wait for exit before read to avoid
        # paramiko's default pipe read timeout (seen at ~120s) mid-import.
        stdin, stdout, stderr = client.exec_command(
            "/import file-name=router_bootstrap_lab.rsc", timeout=600.0
        )
        ch = stdout.channel
        ch.settimeout(600.0)
        code = ch.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        sys.stdout.write(out)
        if err.strip():
            sys.stdout.write(err)
        if code != 0:
            sys.exit(code)
    finally:
        client.close()


if __name__ == "__main__":
    main()
