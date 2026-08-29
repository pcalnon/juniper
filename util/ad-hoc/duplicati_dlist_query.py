#!/usr/bin/env python3
"""
Query the NEWEST dlist of a Duplicati destination, destination-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — investigation (Yamaguchi scope-widening re-baseline)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8)

Answers "what does the newest restore point actually contain?" without the
job database and without the server: decrypts the newest dlist (the names
embed the UTC start stamp, so the lexically last one is the newest), reads
filelist.json, and reports

  * fileset metadata (IsFullBackup), entry counts by type, total File bytes
  * the N largest files (the drill's large-stratum planning input)
  * every entry matching each --match regex (type, size, mtime) -- e.g. "are
    the VM images in?" / "is the release-train private key in?"

Read-only on the destination; the passphrase key is named explicitly and only
its sha256[:16] is logged; plaintext lands in a temp dir on the scratch fs and
is removed. Exit 0 = report written; 2 = operational failure.

    python3 util/ad-hoc/duplicati_dlist_query.py --encryption aes \\
        --dest /mnt/Backups/Ubuntu/Yamaguchi \\
        --match '\\.vdi$' --match 'juniper-release-train' --largest 12
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(2)


def mount_point_of(path):
    """Containing mountpoint of *path*, found by walking up. Returns "/" when nothing else matches."""
    p = os.path.realpath(path)
    while p != "/" and not os.path.ismount(p):
        p = os.path.dirname(p)
    return p


def load_passphrase(cred_file, key):
    pp = None
    with open(cred_file) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(f"{key}=") or line.startswith(f"export {key}="):
                pp = line.split("=", 1)[1].strip().strip('"')
    if not pp:
        fail(f"no {key}= entry in {cred_file}")
    print(f"credential  : {cred_file} key={key} (sha256[:16]={hashlib.sha256(pp.encode()).hexdigest()[:16]})")
    return pp


def decrypt(src, dst, passphrase, encryption):
    if encryption == "aes":
        # SharpAESCrypt: password on argv (accepted single-user-host deviation);
        # rc 3 = HMAC mismatch, rc 4 = wrong password.
        proc = subprocess.run(["duplicati-aescrypt", "d", passphrase, src, dst], capture_output=True, check=False)
        if proc.returncode != 0:
            fail(f"aescrypt rc={proc.returncode} on {os.path.basename(src)}: {proc.stderr.decode(errors='replace')[:200]}")
        return
    with open(dst, "wb") as out:
        proc = subprocess.run(
            ["gpg", "--batch", "--quiet", "--pinentry-mode", "loopback", "--passphrase-fd", "0", "--decrypt", src],
            input=(passphrase + "\n").encode(), stdout=out, stderr=subprocess.PIPE, check=False,
        )
    if proc.returncode != 0:
        fail(f"gpg failed on {os.path.basename(src)}: {proc.stderr.decode(errors='replace')[:300]}")


def main():
    ap = argparse.ArgumentParser(description="query the newest dlist of a Duplicati destination")
    # REQUIRED, for the same reason as duplicati_drill_fresh.py: the old default
    # (/media/pcalnon/temp_backups/Yamaguchi) survived the 2026-08-26 migration to
    # /mnt/Backups/Ubuntu/Yamaguchi as a frozen copy, so a bare run would answer questions
    # about a stale fileset while looking entirely healthy.  Like the drill, this tool reads
    # the destination directly and must keep working when the Duplicati server does not, so
    # it names the destination rather than asking the server (contrast yamaguchi_census.py,
    # which needs the server anyway to reconcile against it).
    ap.add_argument("--dest", required=True,
                    help="destination directory to query (REQUIRED -- no default, deliberately). "
                         "Live Yamaguchi set: /mnt/Backups/Ubuntu/Yamaguchi (--encryption aes).")
    ap.add_argument("--scratch", default="/media/pcalnon/temp_backups/_yamaguchi_check",
                    help="parent for the temporary plaintext dir (scratch fs, never the destination)")
    ap.add_argument("--cred-file", default=os.path.expanduser("~/.config/duplicati-backup/env"))
    ap.add_argument("--cred-key", default="PASSPHRASE")
    ap.add_argument("--encryption", choices=["gpg", "aes"], default="aes")
    ap.add_argument("--match", action="append", default=[], help="regex against entry paths (repeatable)")
    ap.add_argument("--largest", type=int, default=10, help="list the N largest files")
    ap.add_argument("--json", help="also write the matches + summary to this JSON file")
    args = ap.parse_args()

    dest = os.path.realpath(args.dest)
    if not os.path.isdir(dest):
        fail(f"destination is not a directory: {dest}")
    # Derived, not named: the previous guard asserted a filesystem this tool no longer
    # necessarily reads, so it would have passed while pointed anywhere (note 8.14).
    dest_mp = mount_point_of(dest)
    if dest_mp == "/":
        fail(f"destination {dest} is not on a mounted filesystem (walked up to /)")
    scratch_mp = mount_point_of(args.scratch if os.path.isdir(args.scratch) else os.path.dirname(args.scratch))
    if scratch_mp == "/":
        fail(f"scratch {args.scratch} is not on a mounted filesystem (walked up to /)")
    if scratch_mp == dest_mp:
        fail(f"scratch {args.scratch} is on the destination filesystem ({dest_mp}) -- plaintext must "
             "never be written to the disk holding the encrypted set")
    names = sorted(os.listdir(dest))
    dlists = [n for n in names if ".dlist." in n]
    if not dlists:
        fail(f"no dlist in {dest}")
    dlist_name = dlists[-1]
    print(f"destination : {dest} -> {len(dlists)} dlist / {sum('.dindex.' in n for n in names)} dindex / {sum('.dblock.' in n for n in names)} dblock")
    print(f"dlist       : {dlist_name} (newest of {len(dlists)}); all dlists: {dlists}")

    passphrase = load_passphrase(args.cred_file, args.cred_key)
    workdir = tempfile.mkdtemp(prefix="dlist-query-", dir=args.scratch)
    try:
        plain = os.path.join(workdir, "dlist.zip")
        decrypt(os.path.join(dest, dlist_name), plain, passphrase, args.encryption)
        with zipfile.ZipFile(plain) as zf:
            filelist = json.loads(zf.read("filelist.json"))
            fileset_meta = json.loads(zf.read("fileset")) if "fileset" in zf.namelist() else {}
            manifest = json.loads(zf.read("manifest")) if "manifest" in zf.namelist() else {}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    by_type = {}
    total_bytes = 0
    for e in filelist:
        t = e.get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1
        if t == "File":
            total_bytes += int(e.get("size", 0) or 0)
    print(f"fileset     : IsFullBackup={fileset_meta.get('IsFullBackup')} manifest.Blocksize={manifest.get('Blocksize')} entries={len(filelist)}")
    print(f"by type     : {json.dumps(by_type, sort_keys=True)}")
    print(f"File bytes  : {total_bytes} ({total_bytes / 2**30:.1f} GiB)")

    files = [e for e in filelist if e.get("type") == "File"]
    largest = sorted(files, key=lambda e: -int(e.get("size", 0) or 0))[: args.largest]
    print(f"largest {args.largest}:")
    for e in largest:
        print(f"  {int(e.get('size', 0)):>14} B  {e.get('time', '')}  {e['path']}")

    matches = {}
    for pat in args.match:
        rx = re.compile(pat)
        hits = [e for e in filelist if rx.search(e.get("path", ""))]
        matches[pat] = [{"path": e["path"], "type": e.get("type"), "size": e.get("size", 0), "time": e.get("time")} for e in hits]
        print(f"match {pat!r}: {len(hits)} entr{'y' if len(hits) == 1 else 'ies'}")
        for h in hits[:50]:
            print(f"  [{h.get('type', '?'):>7}] {int(h.get('size', 0) or 0):>14} B  {h.get('time', '')}  {h['path']}")
        if len(hits) > 50:
            print(f"  ... {len(hits) - 50} more")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"dest": dest, "dlist": dlist_name, "dlists": dlists, "fileset": fileset_meta,
                       "by_type": by_type, "file_bytes": total_bytes,
                       "largest": [{"path": e["path"], "size": e.get("size", 0), "time": e.get("time")} for e in largest],
                       "matches": matches}, fh, indent=1)
        print(f"json        : {args.json}")


if __name__ == "__main__":
    main()
