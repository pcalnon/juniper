#!/usr/bin/env python3
"""Prove whether the OLD gpg archive at /mnt/Backups/Ubuntu is still decryptable.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Written 2026-08-28 for the old-archive purge decision (note 8.15).  The purge is
the decision that gates consolidating backups onto sda1, and it turns on one
question that had never been tested: **can these 5,366 volumes still be read?**

Two facts make the answer non-obvious, and both are recorded here because each
one, taken alone, points the wrong way:

* ``gpg --list-secret-keys`` shows the RSA-4096 key whose UID literally says
  ``yamaguchi_gpg2-yubikey`` as validity ``e`` -- **expired 2021-01-09** -- with
  its subkeys resident on YubiKey serial ``D2760001240102010006092583970000``,
  a different card from the current 3a/3c.  That invites the conclusion that the
  archive needs a card that may be gone.
* It does not.  ``gpg --list-packets`` on any volume reports
  ``:symkey enc packet`` / "encrypted with 1 passphrase" -- Duplicati's GPG module
  used **symmetric** encryption.  No key, no card, no expiry is involved.
  Decryptability depends only on whether the passphrase is still held.

So the probe is a passphrase test, not a key test.  It decrypts real volumes and
checks the plaintext is a real Zip (Duplicati volumes are Zip inside the GPG
envelope) -- a passphrase that "succeeds" while emitting garbage is the failure
mode a bare exit-code check would miss.

Reads ``~/.config/duplicati-backup/env`` for ``PASSPHRASE_OLD`` (and, with
``--try-current``, ``PASSPHRASE``).  The value is never printed or logged; only
which named variable worked.

Read-only: decrypts to memory, writes nothing, touches no volume.

Exit: 0 decryptable, 1 not decryptable with any tried passphrase, 2 setup error.
"""

import argparse
import os
import re
import subprocess  # nosec B404 -- fixed argv, no shell
import sys

ENV_FILE = os.path.expanduser("~/.config/duplicati-backup/env")
ARCHIVE = "/mnt/Backups/Ubuntu"
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


def read_var(key):
    """Return the value of ``key`` from the env file, or None. Never printed by callers."""
    try:
        with open(ENV_FILE) as fh:
            for line in fh:
                m = re.match(rf"^\s*(?:export\s+)?{re.escape(key)}=(.*)$", line)
                if m and m.group(1).strip():
                    return m.group(1).strip().strip("'\"")
    except OSError as exc:
        sys.exit(f"FATAL: cannot read {ENV_FILE}: {exc}")
    return None


def try_decrypt(path, passphrase):
    """Decrypt ``path`` to memory. Return (ok, detail). ok only if plaintext is a Zip."""
    proc = subprocess.run(  # nosec B603 -- fixed argv, no shell
        [
            "gpg", "--batch", "--quiet", "--no-tty",
            "--pinentry-mode", "loopback",
            "--passphrase-fd", "0",
            "--decrypt", path,
        ],
        input=passphrase.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode(errors="replace").strip().splitlines()
        return False, (err[-1] if err else f"rc={proc.returncode}")
    if not proc.stdout.startswith(ZIP_MAGIC):
        return False, f"decrypted but not a Zip (first 4 bytes {proc.stdout[:4]!r})"
    return True, f"{len(proc.stdout)} bytes of Zip"


def pick_volumes(count):
    """Smallest dindex volumes first, then the newest dlist -- cheap, and spans both kinds."""
    entries = []
    with os.scandir(ARCHIVE) as it:
        for e in it:
            if e.is_file() and e.name.endswith(".dindex.zip.gpg"):
                entries.append((e.stat().st_size, e.path))
    entries.sort()
    picked = [p for _, p in entries[:count]]
    dlists = sorted(
        e.path for e in os.scandir(ARCHIVE) if e.is_file() and e.name.endswith(".dlist.zip.gpg")
    )
    if dlists:
        picked.append(dlists[-1])
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--count", type=int, default=3, help="dindex volumes to probe (default 3)")
    ap.add_argument("--try-current", action="store_true", help="also try PASSPHRASE if PASSPHRASE_OLD fails")
    args = ap.parse_args()

    if not os.path.isdir(ARCHIVE):
        sys.exit(f"FATAL: {ARCHIVE} is not mounted")

    names = ["PASSPHRASE_OLD"] + (["PASSPHRASE"] if args.try_current else [])
    volumes = pick_volumes(args.count)
    if not volumes:
        sys.exit(f"FATAL: no .gpg volumes found at {ARCHIVE}")

    print(f"== old-archive decrypt probe: {len(volumes)} volume(s) under {ARCHIVE}")
    for name in names:
        secret = read_var(name)
        if not secret:
            print(f"  {name}: absent from {ENV_FILE} -- skipped")
            continue
        results = [(os.path.basename(v),) + try_decrypt(v, secret) for v in volumes]
        for base, ok, detail in results:
            print(f"  {name}: {'OK  ' if ok else 'FAIL'} {base} -- {detail}")
        if all(ok for _, ok, _ in results):
            print(f"\nVERDICT: DECRYPTABLE with {name} ({len(results)}/{len(results)} volumes, Zip-verified)")
            return 0
    print("\nVERDICT: NOT decryptable with any passphrase tried")
    return 1


if __name__ == "__main__":
    sys.exit(main())
