#!/usr/bin/env python3
"""Upload a RouterOS .rsc to the MikroTik (ROUTER_IP from .env) and /import it."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.rsc>", file=sys.stderr)
        sys.exit(2)
    rsc = Path(sys.argv[1]).resolve()
    if not rsc.is_file() or rsc.suffix.lower() != ".rsc":
        sys.exit(f"Not a .rsc file: {rsc}")

    load_dotenv(REPO / ".env")
    host = os.environ.get("ROUTER_IP", "").strip() or os.environ.get("ROUTER_IP_2", "").strip()
    user = os.environ.get("ROUTER_USERNAME", "").strip()
    password = os.environ.get("ROUTER_PASSWORD", "")
    if not host or not user:
        sys.exit("Set ROUTER_IP and ROUTER_USERNAME in .env")

    remote = rsc.name
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
            sftp.put(str(rsc), remote)
        finally:
            sftp.close()

        cmd = f"/import file-name={remote}"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=120.0)
        ch = stdout.channel
        ch.settimeout(120.0)
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
