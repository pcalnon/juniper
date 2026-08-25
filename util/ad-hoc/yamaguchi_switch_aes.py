#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

One-shot: switch the Yamaguchi job (backup id 2) to the built-in AES
encryption module, per the 2026-08-25 decision -- the GPGFlushError class
(GPGStreamWrapper's hardcoded 5 s Join) is structurally impossible under AES.
Removes the now-moot --gpg-encryption-switches; every other setting is kept
(asynchronous-upload-limit=1 stays: still bounds temp/queue usage). The
passphrase is re-set explicitly from the credentials file rather than
round-tripping the server's (potentially masked) value.
"""

import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yamaguchi_server_api import login, req  # noqa: E402


def read_passphrase():
    with open(os.path.expanduser("~/.config/duplicati-backup/env")) as fh:
        for line in fh:
            m = re.match(r"^\s*(?:export\s+)?PASSPHRASE=(.*)$", line)
            if m and m.group(1).strip():
                return m.group(1).strip().strip('"')
    sys.exit("FATAL: no PASSPHRASE in credentials file")


def main():
    tok = login()
    st, body = req("GET", "/api/v1/backup/2", tok)
    if st != 200:
        sys.exit(f"GET failed {st}: {body}")
    data = body.get("data", body)
    b = data.get("Backup", data)
    drop = ("--gpg-encryption-switches", "encryption-module", "passphrase")
    settings = [s for s in b["Settings"] if s.get("Name") not in drop]
    settings.insert(0, {"Name": "encryption-module", "Value": "aes"})
    settings.insert(1, {"Name": "passphrase", "Value": read_passphrase()})
    b["Settings"] = settings
    st, resp = req("PUT", "/api/v1/backup/2", tok, body={"Backup": b, "Schedule": data.get("Schedule")})
    print("update:", st, json.dumps(resp)[:200])
    if st != 200:
        sys.exit(1)
    st, body = req("GET", "/api/v1/backup/2", tok)
    data = body.get("data", body)
    for s in data.get("Backup", data).get("Settings") or []:
        n = s.get("Name") or ""
        print("  ", n, "=", ("<redacted>" if "passphrase" in n.lower() else s.get("Value")))


if __name__ == "__main__":
    main()
