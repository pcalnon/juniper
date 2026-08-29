#!/usr/bin/env python3
"""
Project     : Juniper
Sub-Project : juniper-ml
Application : Yamaguchi backup -- passphrase escrow
Author      : Paul Calnon
Version     : 1.0.0
License     : MIT License

Escrow the Yamaguchi passphrases OFF the source spindle.

The problem (note section 8.18): the AES passphrase for the whole 210 GB
destination lives in /home/pcalnon/.config/duplicati-backup/env, which is on
sdc3 -- the same physical disk as the backup sources, the 196 GB second copy
(sdc4) and the dlist mirror. Filter 43 excludes that directory from the job, so
the key is not in the backup either. Losing physical disk `sdc` -- the event
this backup exists for -- takes the sources, both copies and the key together,
leaving 210 GB of ciphertext nobody can open.

PASSPHRASE_OLD is worse: it is the only key to the ten retained dlists, the sole
surviving record of the purged 2.3 TiB archive.

This tool writes a copy to a destination on a DIFFERENT PHYSICAL DEVICE, and
refuses to run if the destination is not on one -- an escrow copy on the same
disk is not an escrow, and the check has to be mechanical because "different
directory" looks identical to "different disk" in an ls.

It also emits a printable sheet for the offline half of the escrow. That sheet
contains PLAINTEXT SECRETS: it defaults into ~/.cache/, which filter 36 excludes
from the job, precisely so the printable copy never lands inside the archive it
unlocks. Print it, then delete it.

Secret VALUES are never printed to stdout -- only key names, byte counts and
digests.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import sys
from datetime import datetime, timezone

SRC = "/home/pcalnon/.config/duplicati-backup/env"
DEST_DIR = "/mnt/Backups/Ubuntu/_yamaguchi_keys"
SHEET_DEFAULT = os.path.expanduser("~/.cache/yamaguchi-key-escrow-sheet.txt")
REQUIRED_KEYS = ("PASSPHRASE", "PASSPHRASE_OLD")

DEST_README = """\
# Yamaguchi passphrase escrow

This directory exists because of note section 8.18: the passphrase that unlocks
the ciphertext in ../Yamaguchi/ lived ONLY on disk sdc, together with the backup
sources and both secondary copies. Losing sdc would have left the destination
unopenable.

`env` here is a byte-identical copy of /home/pcalnon/.config/duplicati-backup/env.

  PASSPHRASE      -- AES key for the live Yamaguchi destination (../Yamaguchi/)
  PASSPHRASE_OLD  -- key for the ten retained gpg dlists in ../ (the only record
                     of the purged 2.3 TiB archive)

To load it:

    export $(grep -E '^(export )?PASSPHRASE=' env | sed 's/^export //')

KNOWN AND ACCEPTED LIMITATION (owner decision, {date}): this copy sits on the
same filesystem as the ciphertext it unlocks, so a single stolen or seized sda1
yields both. It is the fast machine-local recovery path. The authoritative
escrow is the OFFLINE copy -- printed and stored away from this machine. If the
offline copy does not exist, this escrow is only half done.

Regenerate with:  python3 util/ad-hoc/yamaguchi_key_escrow.py --execute
"""

SHEET = """\
================================================================================
  YAMAGUCHI BACKUP -- OFFLINE KEY ESCROW SHEET
  generated {date}
  PLAINTEXT SECRETS BELOW.  PRINT THIS, THEN DELETE THE FILE.
================================================================================

Machine      : {host}
Destination  : file:///mnt/Backups/Ubuntu/Yamaguchi   (disk sda1)
Encryption   : AES  (Duplicati built-in, encryption-module=aes)
Old archive  : /mnt/Backups/Ubuntu/*.dlist.zip.gpg    (10 dlists, gpg)

--------------------------------------------------------------------------------
PASSPHRASE       (unlocks the live 210 GB Yamaguchi destination)

    {p_live}

--------------------------------------------------------------------------------
PASSPHRASE_OLD   (unlocks the ten retained gpg dlists -- the ONLY record of the
                  2.3 TiB archive purged 2026-08-28; no other copy exists)

    {p_old}

--------------------------------------------------------------------------------

WHY THIS SHEET EXISTS
  Both keys otherwise live only on disk sdc, which also holds every backup
  source and both secondary copies. Losing sdc is the exact event the backup
  exists to survive -- and without this sheet it would also destroy the ability
  to read the backup.

WHERE TO KEEP IT
  Away from this machine. A copy stored beside the machine defeats the point.

RESTORING WITHOUT THIS REPOSITORY
  Install Duplicati, add a backup pointing at file:///mnt/Backups/Ubuntu/Yamaguchi
  with encryption AES and PASSPHRASE above, then "Restore from configuration".
  The job definition (2 sources, 44 filters, 10 settings) is reproducible from
  util/ad-hoc/yamaguchi_config_record.py in the juniper-ml repo, and a copy of
  the Duplicati server DB is captured daily to
  ~/.local/state/duplicati-server-db/ (note section 8.19).

================================================================================
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_keys(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            m = re.match(r"^\s*(?:export\s+)?([A-Z_]+)=(.*)$", line)
            if m:
                out[m.group(1)] = m.group(2).strip().strip("'\"")
    return out


def fail(msg):
    sys.exit(f"REFUSE: {msg}")


def enclosing_mount(path):
    p = os.path.abspath(path)
    while p != "/" and not os.path.ismount(p):
        p = os.path.dirname(p)
    return p


def backing_disk(mountpoint):
    """Resolve a mountpoint to its parent block device (sdc4 -> sdc)."""
    src_dev = None
    with open("/proc/self/mountinfo") as fh:
        for line in fh:
            parts = line.split(" - ")
            if len(parts) < 2:
                continue
            fields = parts[0].split()
            if len(fields) > 4 and fields[4] == mountpoint:
                src_dev = parts[1].split()[1]
    if not src_dev or not src_dev.startswith("/dev/"):
        return None
    name = os.path.basename(src_dev)
    sysdev = f"/sys/class/block/{name}"
    if not os.path.exists(sysdev):
        return None
    parent = os.path.basename(os.path.dirname(os.path.realpath(sysdev)))
    return parent if parent.startswith(("sd", "nvme", "vd", "hd")) else name


def main():
    ap = argparse.ArgumentParser(description="Escrow the Yamaguchi passphrases off the source spindle.")
    ap.add_argument("--execute", action="store_true", help="actually write (default is a dry run)")
    ap.add_argument("--dest-dir", default=DEST_DIR, help=f"escrow directory (default {DEST_DIR})")
    ap.add_argument("--sheet", default=SHEET_DEFAULT, help=f"printable offline sheet (default {SHEET_DEFAULT})")
    ap.add_argument("--no-sheet", action="store_true", help="skip the printable sheet")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    print(f"== Yamaguchi key escrow at {stamp}")
    print(f"mode        : {'EXECUTE' if args.execute else 'DRY RUN'}")

    # ---- gate 1: source -------------------------------------------------
    if not os.path.isfile(SRC):
        fail(f"source key file missing: {SRC}")
    st_src = os.stat(SRC)
    keys = parse_keys(SRC)
    missing = [k for k in REQUIRED_KEYS if not keys.get(k)]
    if missing:
        fail(f"source {SRC} has no value for: {', '.join(missing)}")
    print(f"source      : {SRC} ({st_src.st_size} B, mode {stat.S_IMODE(st_src.st_mode):04o})")
    print(f"keys found  : {', '.join(sorted(k for k in keys if keys[k]))}")
    print(f"source sha  : {sha256(SRC)}")

    # ---- gate 2: destination must not be inside a backup Source ---------
    # Escrowing into a Source would put the key inside the archive it unlocks.
    # Ordered FIRST because it is a pure string test with no mount dependency:
    # run after gate 4, the same-filesystem check would swallow every
    # /home/pcalnon/... destination and report the vaguer error instead.
    dest_dir = os.path.abspath(args.dest_dir)
    if dest_dir.startswith("/home/pcalnon/"):
        fail(f"{dest_dir} is inside backup Source /home/pcalnon/ -- "
             "that would put the key inside the archive it unlocks")

    # ---- gate 3: destination must sit under a real mountpoint -----------
    dest_mount = enclosing_mount(dest_dir)
    if dest_mount == "/":
        fail(f"{dest_dir} does not sit under a mountpoint -- writing there would fill the root filesystem")
    print(f"dest mount  : {dest_mount}")

    # ---- gate 4: THE point of the exercise ------------------------------
    # A copy on the same physical device is not an escrow. st_dev separates
    # sdc3 from sda1; it does NOT separate sdc3 from sdc4, so the backing-disk
    # check below is the one that actually encodes the failure being defended.
    if os.stat(dest_mount).st_dev == st_src.st_dev:
        fail(f"{dest_mount} is on the same filesystem as {SRC} -- that is not an escrow")

    src_mount = enclosing_mount(SRC)
    d_src, d_dst = backing_disk(src_mount), backing_disk(dest_mount)
    print(f"source disk : {d_src or '?'}   ({src_mount})")
    print(f"dest disk   : {d_dst or '?'}   ({dest_mount})")
    if d_src and d_dst and d_src == d_dst:
        fail(f"{dest_mount} and {src_mount} are both on physical disk {d_src} -- "
             "losing that disk would take the key and the sources together")
    if not (d_src and d_dst):
        print("WARN        : could not resolve both backing disks; relying on the st_dev check alone")

    dest_env = os.path.join(dest_dir, "env")
    print(f"dest        : {dest_env}")

    if not args.execute:
        print("\nwould write :")
        print(f"  {dest_env}   (mode 0600)")
        print(f"  {os.path.join(dest_dir, 'README.md')}")
        if not args.no_sheet:
            print(f"  {args.sheet}   (mode 0600, PLAINTEXT -- print then delete)")
        print("\ndry run -- nothing written. re-run with --execute")
        return 0

    # ---- write -----------------------------------------------------------
    os.makedirs(dest_dir, mode=0o700, exist_ok=True)
    os.chmod(dest_dir, 0o700)

    tmp = dest_env + ".tmp"
    shutil.copyfile(SRC, tmp)
    os.chmod(tmp, 0o600)
    os.replace(tmp, dest_env)

    got, want = sha256(dest_env), sha256(SRC)
    if got != want:
        fail(f"verification failed: copy sha {got} != source sha {want}")
    print(f"wrote       : {dest_env}  (sha256 verified identical)")

    readme_path = os.path.join(dest_dir, "README.md")
    with open(readme_path, "w") as fh:
        fh.write(DEST_README.format(date=stamp))
    print(f"wrote       : {readme_path}")

    if not args.no_sheet:
        sheet_dir = os.path.dirname(args.sheet)
        if sheet_dir:
            os.makedirs(sheet_dir, exist_ok=True)
        fd = os.open(args.sheet, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(SHEET.format(
                date=stamp,
                host=os.uname().nodename,
                p_live=keys["PASSPHRASE"],
                p_old=keys["PASSPHRASE_OLD"],
            ))
        print(f"wrote       : {args.sheet}  (mode 0600, PLAINTEXT)")
        print("\nNEXT -- the escrow is NOT complete until you do this:")
        print(f"  1. print or transcribe {args.sheet}")
        print("  2. store the paper copy away from this machine")
        print(f"  3. shred -u {args.sheet}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
