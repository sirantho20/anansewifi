#!/usr/bin/env python3
"""
Fetch the MikroTik Hotspot login page over a specific interface (Wi‑Fi to 192.168.10.x)
and verify the rendered HTML.

Default: minimal on-router `login.html` (code field, Log in, Buy package link).
Optional --local-form: two-field RADIUS form (see hotspot/login-local-form.html).
Optional --user-login: hotspot/user_login.html (same checks + Account sign in title).
Optional --redirect: legacy meta-refresh page to the portal root (older login.html style).

Uses curl(1) so traffic is bound to the interface (macOS: --interface en0).

Example:
  HOTSPOT_WIFI_IF=en0 python3 verify_hotspot_page.py
  python3 verify_hotspot_page.py --url http://login.hotspot/login
  python3 verify_hotspot_page.py --local-form
  python3 verify_hotspot_page.py --redirect
  python3 verify_hotspot_page.py --insecure  # if profile uses HTTPS/self-signed again
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXTERNAL_PORTAL_URL = "https://anansewifi.shrt.fit/"
PORTAL_PACKAGES_URL = "https://anansewifi.shrt.fit/packages/"


def _run_curl(
    url: str, interface: str, max_time: float, *, insecure: bool, location: bool
) -> tuple[int, str, str, str]:
    """
    Return (returncode, body, writeout, stderr).
    On success, writeout is two lines: http_code and final_url (from curl -w).
    """
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        cmd = [
            "curl",
            "-sS",
            "--connect-timeout",
            "8",
            "--max-time",
            str(max_time),
            "--interface",
            interface,
            "-o",
            path,
            "-w",
            "%{http_code}\n%{url_effective}",
        ]
        if location:
            cmd.insert(1, "-L")
        if insecure:
            cmd.insert(3, "-k")
        cmd.append(url)
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=int(max_time) + 15
        )
        err = (proc.stderr or "").strip()
        if proc.returncode != 0:
            return proc.returncode, "", "", err or f"exit {proc.returncode}"
        body = Path(path).read_text(encoding="utf-8", errors="replace")
        wo = (proc.stdout or "").strip()
        return 0, body, wo, err
    finally:
        try:
            Path(path).unlink()
        except OSError:
            pass


def verify_minimal_router_login_body(body: str) -> list[str]:
    """Verify default repo hotspot/login.html: code field, form, packages link."""
    failures: list[str] = []
    if not body.strip():
        failures.append("empty response body")
        return failures
    if "<!DOCTYPE html>" not in body and "<!doctype html>" not in body.lower():
        failures.append("missing HTML5 doctype")
    if PORTAL_PACKAGES_URL not in body:
        failures.append(f"missing packages link ({PORTAL_PACKAGES_URL})")
    if "<form" not in body.lower():
        failures.append("missing <form> (login form)")
    if "hs_code" not in body:
        failures.append("expected id=hs_code (code field)")
    if not re.search(r'name\s*=\s*["\']username["\']', body, re.I):
        failures.append("missing name=username (Hotspot login)")
    if not re.search(r'name\s*=\s*["\']password["\']', body, re.I):
        failures.append("missing name=password (PAP/CHAP)")
    if "Buy package" not in body:
        failures.append('expected "Buy package" link text')
    return failures


def verify_external_redirect_body(body: str) -> list[str]:
    """Verify meta-redirect Hotspot page (optional legacy `login.html` style)."""
    failures: list[str] = []
    if not body.strip():
        failures.append("empty response body")
        return failures
    if "<!DOCTYPE html>" not in body and "<!doctype html>" not in body.lower():
        failures.append("missing HTML5 doctype")
    if EXTERNAL_PORTAL_URL not in body and "anansewifi.shrt.fit" not in body:
        failures.append(f"missing redirect target ({EXTERNAL_PORTAL_URL})")
    if not re.search(
        r'http-equiv\s*=\s*["\']refresh["\']', body, re.I
    ) and EXTERNAL_PORTAL_URL not in body:
        failures.append("expected meta refresh or portal URL in body")
    return failures


def verify_local_form_body(body: str) -> list[str]:
    """Verify full Hotspot login form (repo hotspot/login-local-form.html)."""
    failures: list[str] = []
    if not body.strip():
        failures.append("empty response body")
        return failures
    if "<!DOCTYPE html>" not in body and "<!doctype html>" not in body.lower():
        failures.append("missing HTML5 doctype")
    if not re.search(r"<title>\s*Ananse WiFi\s*—\s*Sign in\s*</title>", body, re.I):
        if "Ananse WiFi" not in body or "Sign in" not in body:
            failures.append("expected <title>Ananse WiFi — Sign in</title> (or title text)")
    if "<form" not in body.lower():
        failures.append("missing <form> (login form)")
    if not re.search(r'name\s*=\s*["\']password["\']', body, re.I):
        failures.append("missing name=password input (Hotspot login)")
    if "name=username" not in body.replace("'", '"') and 'name="username"' not in body:
        if not re.search(r'name\s*=\s*["\']username["\']', body, re.I):
            failures.append("missing username field")
    return failures


def verify_user_login_body(body: str) -> list[str]:
    """Verify repo hotspot/user_login.html (username/password form + CHAP script)."""
    failures = verify_local_form_body(body)
    if not failures and "Account sign in" not in body:
        failures.append('expected user_login marker "Account sign in" (title)')
    return failures


def main() -> int:
    p = argparse.ArgumentParser(description="Verify Hotspot login HTML over Wi‑Fi interface.")
    p.add_argument(
        "--interface",
        "-i",
        default=os.environ.get("HOTSPOT_WIFI_IF", "en0"),
        help="Interface bound to Hotspot LAN (default: en0 or HOTSPOT_WIFI_IF).",
    )
    p.add_argument(
        "--url",
        default="http://login.hotspot/",
        help="Initial URL (redirects to /login).",
    )
    p.add_argument(
        "--max-time",
        type=float,
        default=15.0,
        help="curl --max-time (seconds).",
    )
    p.add_argument(
        "--insecure",
        "-k",
        action="store_true",
        help="Pass curl -k (accept self-signed HTTPS) if Hotspot uses TLS again.",
    )
    p.add_argument(
        "--local-form",
        action="store_true",
        help="Expect the two-field on-router RADIUS form (login-local-form.html).",
    )
    p.add_argument(
        "--redirect",
        action="store_true",
        help="Expect a meta-redirect to the portal root (legacy login.html).",
    )
    p.add_argument(
        "--user-login",
        action="store_true",
        help="Expect user_login.html (default URL …/user_login.html); same RADIUS fields as --local-form.",
    )
    args = p.parse_args()
    mode_flags = [args.redirect, args.local_form, args.user_login]
    if sum(bool(x) for x in mode_flags) > 1:
        print("Use only one of --local-form, --user-login, or --redirect.", file=sys.stderr)
        return 2

    insecure = args.insecure or os.environ.get("HOTSPOT_CURL_INSECURE", "").lower() in (
        "1",
        "true",
        "yes",
    )
    curl_url = args.url
    if args.user_login:
        base = curl_url.split("?", 1)[0].rstrip("/")
        if base == "http://login.hotspot":
            curl_url = "http://login.hotspot/user_login.html"

    code, body, writeout, cerr = _run_curl(
        curl_url, args.interface, args.max_time, insecure=insecure, location=True
    )
    if code != 0:
        print(f"curl failed (exit {code}): {cerr}", file=sys.stderr)
        return 1

    lines = writeout.split("\n", 1)
    http_code = int(lines[0].strip()) if lines and lines[0].strip().isdigit() else 0
    final_url = lines[1].strip() if len(lines) > 1 else ""
    if cerr:
        print(f"curl_note: {cerr}", file=sys.stderr)

    print(f"http_code={http_code}")
    print(f"final_url={final_url}")
    print(f"body_bytes={len(body.encode('utf-8'))}")

    if http_code != 200:
        print(f"FAIL: expected HTTP 200, got {http_code}", file=sys.stderr)
        return 1
    if "/login" not in final_url.lower() and "hotspot" not in final_url.lower():
        print(
            f"WARN: final URL may not be Hotspot login path: {final_url}",
            file=sys.stderr,
        )

    if args.local_form:
        failures = verify_local_form_body(body)
        ok_msg = "OK: Hotspot login page HTML looks like the full Ananse RADIUS form (title, form, fields)."
    elif args.user_login:
        failures = verify_user_login_body(body)
        ok_msg = "OK: Hotspot page matches user_login.html (username/password → RADIUS form + CHAP)."
    elif args.redirect:
        failures = verify_external_redirect_body(body)
        ok_msg = "OK: Hotspot login page redirects to the external portal (anansewifi.shrt.fit)."
    else:
        failures = verify_minimal_router_login_body(body)
        ok_msg = (
            "OK: Hotspot login page looks like minimal on-router Ananse (code, Log in, packages link)."
        )

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        preview = body[:1200].replace("\n", " ")[:800]
        print(f"body_preview: {preview!r}...", file=sys.stderr)
        return 1

    print(ok_msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
