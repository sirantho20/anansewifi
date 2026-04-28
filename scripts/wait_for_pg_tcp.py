#!/usr/bin/env python3
"""
TCP wait for PostgreSQL before entrypoint runs migrations (docker/Coolify).
Use PG_WAIT_SKIP=1 to bypass if the DB is up but the wait is wrong (debug only).
"""
from __future__ import annotations

import os
import socket
import sys
import time

SKIP = "PG_WAIT_SKIP"
FORCE4 = "PG_WAIT_FORCE_IPV4"
TIMEOUT = "PG_WAIT_TIMEOUT_SECONDS"
INTERVAL = "PG_WAIT_PROGRESS_INTERVAL"


def can_connect(
    host: str, port: int, *, force_ipv4: bool, per_try_s: float = 2.0
) -> bool:
    if force_ipv4:
        try:
            infos = socket.getaddrinfo(
                host, port, socket.AF_INET, socket.SOCK_STREAM
            )
        except OSError:
            return False
        for _fam, st, _proto, _canon, sa in infos:
            s: socket.socket | None = None
            try:
                s = socket.socket(st, socket.SOCK_STREAM)
                s.settimeout(per_try_s)
                s.connect(sa)
                return True
            except OSError:
                pass
            finally:
                if s is not None:
                    s.close()
        return False
    s: socket.socket | None = None
    try:
        s = socket.create_connection((host, port), timeout=per_try_s)
        return True
    except OSError:
        return False
    finally:
        if s is not None:
            s.close()


def main() -> int:
    if os.environ.get(SKIP, "0") == "1":
        print(
            f"{SKIP}=1: skipping TCP wait (migrations will fail if DB is unreachable).",
            file=sys.stderr,
        )
        return 0

    host = os.environ.get("PG_HOST", "")
    port_s = os.environ.get("PG_PORT", "")
    if not host or not port_s:
        return 0

    try:
        port = int(port_s)
    except ValueError:
        print("Error: PG_PORT is not a valid integer.", file=sys.stderr)
        return 1

    try:
        max_s = int(os.environ.get(TIMEOUT, "120"))
    except ValueError:
        max_s = 120
    try:
        interval = int(os.environ.get(INTERVAL, "10"))
    except ValueError:
        interval = 10

    force4 = os.environ.get(FORCE4, "0") == "1"
    v = " (IPv4 only)" if force4 else ""
    print(f"Waiting for PostgreSQL at {host}:{port} (max {max_s}s){v}...")

    n = 0
    while n < max_s:
        if can_connect(host, port, force_ipv4=force4, per_try_s=2.0):
            return 0
        n += 1
        if interval > 0 and n % interval == 0 and n < max_s:
            print(
                f"Still waiting for PostgreSQL at {host}:{port}... ({n}s of {max_s}s max)"
            )
        if n < max_s:
            time.sleep(1)

    _failed(host, port, max_s)
    return 1


def _failed(host: str, port: int, max_s: int) -> None:
    print(
        f"Error: could not open TCP to PostgreSQL at {host}:{port} after {max_s}s.",
        file=sys.stderr,
    )
    print(
        "\nCommon fixes:\n"
        "  • Open firewall / security group: allow the app host egress IP to this port.\n"
        "  • Same Docker stack: use the Postgres service name and internal port (5432) in "
        "DATABASE_URL, not the VPS public IP and mapped port (e.g. 5434) — hairpin often fails.\n"
        f"  • Try IPv4-only: set {FORCE4}=1 if IPv6/AAAA resolution breaks in the container.\n"
        f"  • Debug only: {SKIP}=1 skips this wait; fix DATABASE_URL / network before production.\n"
        f"  • Increase {TIMEOUT} if the DB is slow to start.\n",
        file=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
