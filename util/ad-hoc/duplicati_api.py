#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Minimal authenticated client for the local Duplicati web-service API.

Duplicati 2.3.x issues short-lived access tokens, so a long operational session
loses its token repeatedly; this re-authenticates on demand rather than making
the caller handle 401s.  The password is read from a file and is never passed on
a command line (it would be visible in ``ps``).

Deliberately has no write helpers beyond ``call()`` -- the destructive verbs on
this API (Repair, purge-broken-files, destination operations) must stay explicit
at the call site, not be wrapped in convenience functions.

Usage
-----
    python3 util/ad-hoc/duplicati_api.py GET  serverstate
    python3 util/ad-hoc/duplicati_api.py POST task/7/abort

Environment
-----------
    DUPLICATI_URL        default http://127.0.0.1:8300
    DUPLICATI_PW_FILE    default .env  (the WEB-UI password, not the archive passphrase)

TWO DIFFERENT SECRETS -- do not conflate them:
  * the **web-UI password** (used by duplicati_api.py to authenticate to :8300)
  * the **archive GPG passphrase** (used to decrypt volumes; restores, purges,
    passphrase verification)
They were the same value once and are not any more. Pointing an archive-passphrase
consumer at the UI-password file fails as "Bad session key", which reads like a
corrupt archive rather than the wrong secret.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("DUPLICATI_URL", "http://127.0.0.1:8300").rstrip("/")
# The WEB-UI password. Distinct from the archive GPG passphrase -- see the
# module docstring. resources/duplicati.env was removed when the UI password
# was rotated 2026-08-23; the current value lives in the repo-root .env.
PW_FILE = os.environ.get("DUPLICATI_PW_FILE", ".env")


def _password() -> str:
    """Read the WEB-UI password from PW_FILE.

    Selects by NAME, not position. The file may hold several secrets -- it
    currently carries both a new archive passphrase and the UI password -- and
    matching the first KEY=VALUE line silently returns whichever happens to be
    first, producing a 401 that looks like a wrong password rather than a wrong
    key. DUPLICATI_PW_KEY overrides; the candidates below are tried in order.
    """
    with open(PW_FILE) as fh:
        raw = fh.read()

    explicit = os.environ.get("DUPLICATI_PW_KEY")
    candidates = [explicit] if explicit else [
        "DUPLICATI_UI_PASSWORD", "UI_PASSWORD", "PASSPHRASE_OLD", "PASSPHRASE",
    ]
    for key in candidates:
        m = re.search(rf"^[ \t]*(?:export[ \t]+)?{re.escape(key)}=(.*)$", raw, re.M)
        if not m:
            continue
        val = m.group(1).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        if val:
            return val
    if explicit:
        raise SystemExit(f"no {explicit}= entry in {PW_FILE}")
    # bare-secret file
    return raw.strip()


def login() -> str:
    body = json.dumps({"Password": _password()}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/auth/login", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["AccessToken"]


def call(endpoint: str, method: str = "GET", payload=None, token: str | None = None):
    """Call the API, re-authenticating once on 401. Returns (status, parsed_or_text)."""
    tok = token or login()
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Authorization": "Bearer " + tok}
    if data is not None:
        headers["Content-Type"] = "application/json"

    def _do(t):
        h = dict(headers)
        h["Authorization"] = "Bearer " + t
        req = urllib.request.Request(
            f"{BASE}/api/v1/{endpoint.lstrip('/')}", data=data, method=method, headers=h)
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return resp.status, raw.decode(errors="replace")

    try:
        return _do(tok)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return _do(login())
        detail = ""
        try:
            detail = exc.read().decode(errors="replace")[:400]
        except Exception:  # nosec B110
            # Best-effort enrichment only. The HTTP status in exc.code is the
            # actual result and is returned either way; a body that is absent,
            # already consumed, or undecodable must not mask it by raising a
            # second exception from the error path.
            detail = "<error body unavailable>"
        return exc.code, detail


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    method, endpoint = argv[1].upper(), argv[2]
    payload = json.loads(argv[3]) if len(argv) > 3 else None
    status, body = call(endpoint, method, payload)
    print(f"[{status}]")
    print(json.dumps(body, indent=1) if not isinstance(body, str) else body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
