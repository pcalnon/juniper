#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Destination-only integrity cross-check for a Duplicati backup set: does the
dlist reference any block hash that no dindex declares present in any dblock?

Why this exists
---------------
The fresh set's single dlist was written by run 2 at 22:51:50 -- 24 seconds
after that run started, hours after the last real data volume landed -- i.e. a
*synthetic* manifest produced by a reconciliation pass, describing a fileset
whose author never certified it complete. Duplicati normally writes the dlist
LAST precisely so its presence implies completeness. Before any restore drill
treats this fileset as "a restore point", every block the dlist needs must be
shown present in the destination's own index:

  NEEDED   = single-block file hashes + metadata hashes + blocklist hashes
             + every data-block hash inside each blocklist's content
  AVAILABLE = union over dindex vol/* entries of declared block hashes

Both sides come exclusively from destination artifacts (dlist + dindex files);
the job database is deliberately not consulted -- a drill restores from the
destination, so the destination must be self-sufficient. Blocklist contents
are expanded from dindex list/* entries (each holds the raw concatenated
32-byte SHA-256 hashes of the data blocks); a blocklist hash with no list/*
entry anywhere is reported separately as UNEXPANDABLE (a dindex gap: coverage
of its data blocks cannot be proven from the destination alone).

Safety
------
Read-only on the archive: every archive file is decrypted to a scratch
workdir; nothing under the destination is ever written, and the script refuses
a workdir inside it. The passphrase key is named explicitly (PASSPHRASE, the
FRESH-set key -- never PASSPHRASE_OLD) and only its sha256[:16] is logged.

Exit codes: 0 = complete coverage; 1 = missing hashes or unexpandable
blocklists; 2 = operational failure.
"""

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import zipfile

HASH_BYTES = 32  # SHA-256


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(2)


def load_passphrase(cred_file, key):
    pp = None
    with open(cred_file) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(f"{key}=") or line.startswith(f"export {key}="):
                pp = line.split("=", 1)[1].strip().strip('"')
    if not pp:
        fail(f"no {key}= entry in {cred_file}")
    print(f"credential : {cred_file} key={key} ({len(pp)} chars, sha256[:16]={hashlib.sha256(pp.encode()).hexdigest()[:16]})")
    return pp


def gpg_decrypt(src, dst, passphrase):
    with open(dst, "wb") as out:
        proc = subprocess.run(
            ["gpg", "--batch", "--quiet", "--pinentry-mode", "loopback",
             "--passphrase-fd", "0", "--decrypt", src],
            input=(passphrase + "\n").encode(), stdout=out,
            stderr=subprocess.PIPE, check=False,
        )
    if proc.returncode != 0:
        fail(f"gpg failed on {os.path.basename(src)}: {proc.stderr.decode(errors='replace')[:300]}")


def main():
    ap = argparse.ArgumentParser(description="dlist vs dindex block-coverage cross-check")
    ap.add_argument("--dest", default="/media/pcalnon/temp_backups/Ubuntu")
    ap.add_argument("--workdir", default="/media/pcalnon/temp_backups/_fresh_dlist_check")
    ap.add_argument("--cred-file", default=os.path.expanduser("~/.config/duplicati-backup/env"))
    ap.add_argument("--cred-key", default="PASSPHRASE", help="FRESH-set key; never PASSPHRASE_OLD here")
    ap.add_argument("--blocksize", type=int, default=1024 * 1024, help="job --blocksize (1MB)")
    args = ap.parse_args()

    dest = os.path.realpath(args.dest)
    workdir = os.path.realpath(args.workdir)
    if not os.path.ismount("/media/pcalnon/temp_backups"):
        fail("/media/pcalnon/temp_backups is not a mountpoint")
    if workdir == dest or workdir.startswith(dest + os.sep):
        fail("workdir must not be inside the destination")
    os.makedirs(workdir, exist_ok=True)

    names = sorted(os.listdir(dest))
    dlists = [n for n in names if ".dlist." in n]
    dindexes = [n for n in names if ".dindex." in n]
    dblocks = [n for n in names if ".dblock." in n]
    print(f"destination: {dest} -> {len(dlists)} dlist / {len(dindexes)} dindex / {len(dblocks)} dblock")
    if len(dlists) != 1:
        fail(f"expected exactly 1 dlist, found {len(dlists)}")

    passphrase = load_passphrase(args.cred_file, args.cred_key)

    # ---- AVAILABLE: union of blocks declared by dindex vol/* entries --------
    available = set()
    blocklist_content = {}   # blocklist hash (b64) -> [data-block hashes (b64)]
    indexed_dblocks = set()
    poisoned = 0
    list_entries = 0
    for i, name in enumerate(dindexes, 1):
        plain = os.path.join(workdir, "dindex.zip")
        gpg_decrypt(os.path.join(dest, name), plain, passphrase)
        with zipfile.ZipFile(plain) as zf:
            for entry in zf.namelist():
                if entry.startswith("vol/"):
                    indexed_dblocks.add(entry[4:])
                    data = json.loads(zf.read(entry))
                    for blk in data.get("blocks", []):
                        available.add(blk["hash"])
                elif entry.startswith("list/"):
                    list_entries += 1
                    raw = zf.read(entry)
                    if len(raw) % HASH_BYTES:
                        fail(f"list entry {entry} in {name} has length {len(raw)} not divisible by {HASH_BYTES} -- refusing to under-build NEEDED")
                    # filename is Base64UrlEncode(blocklist hash), padding kept;
                    # normalize back to standard base64 for matching
                    fn = entry[5:]
                    fn_plain = fn.replace("-", "+").replace("_", "/")
                    # Duplicati itself distrusts blocklist entries in index files
                    # (compact can leave invalid ones) -- verify content hashes
                    # to its filename before using it to build NEEDED.
                    if base64.b64encode(hashlib.sha256(raw).digest()).decode() != fn_plain:
                        print(f"POISONED: list entry {entry} in {name} does not hash to its filename")
                        poisoned += 1
                        continue
                    hashes = [base64.b64encode(raw[o:o + HASH_BYTES]).decode()
                              for o in range(0, len(raw), HASH_BYTES)]
                    blocklist_content[fn_plain] = hashes
                    blocklist_content[fn] = hashes
        os.unlink(plain)
        if i % 25 == 0:
            print(f"  parsed {i}/{len(dindexes)} dindex files ...")
    if poisoned:
        fail(f"{poisoned} poisoned list/ entries -- index is untrustworthy, coverage verdict would be vacuous")
    print(f"list entries: {list_entries} blocklist entries across all dindexes, all content-hash-verified against their filenames")
    print(f"available  : {len(available)} distinct blocks declared across {len(indexed_dblocks)} indexed dblocks")

    missing_dblock_index = sorted(set(dblocks) - indexed_dblocks)
    if missing_dblock_index:
        print(f"WARN: {len(missing_dblock_index)} dblock file(s) have no dindex vol/ entry: {missing_dblock_index[:3]} ...")

    # ---- NEEDED: every hash the dlist references ----------------------------
    plain = os.path.join(workdir, "dlist.zip")
    gpg_decrypt(os.path.join(dest, dlists[0]), plain, passphrase)
    with zipfile.ZipFile(plain) as zf:
        filelist = json.loads(zf.read("filelist.json"))
        manifest = json.loads(zf.read("manifest"))
        fileset_meta = json.loads(zf.read("fileset")) if "fileset" in zf.namelist() else {}
    os.unlink(plain)
    # trust the manifest, not assumptions: a non-default job would mis-expand
    if manifest.get("BlockHash", "SHA256") != "SHA256" or manifest.get("FileHash", "SHA256") != "SHA256":
        fail(f"manifest hash algorithms not SHA256: {manifest} -- single-block rule invalid, aborting")
    if int(manifest.get("Blocksize", args.blocksize)) != args.blocksize:
        print(f"NOTE: manifest Blocksize={manifest.get('Blocksize')} overrides --blocksize {args.blocksize}")
        args.blocksize = int(manifest["Blocksize"])
    if fileset_meta:
        print(f"fileset    : IsFullBackup={fileset_meta.get('IsFullBackup')}")

    needed = {}          # hash -> reason (first occurrence)
    unexpandable = []    # blocklist hashes with no list/* content anywhere
    files = dirs = 0
    for entry in filelist:
        etype = entry.get("type")
        path = entry.get("path", "?")
        metahash = entry.get("metahash")
        metasize = entry.get("metasize", 0)
        if metahash and 0 < metasize <= args.blocksize:
            needed.setdefault(metahash, f"metadata of {path}")
        if etype != "File":
            dirs += 1
            continue
        files += 1
        size = entry.get("size", 0)
        blocklists = entry.get("blocklists")
        if blocklists:
            for blh in blocklists:
                needed.setdefault(blh, f"blocklist of {path}")
                content = blocklist_content.get(blh) or blocklist_content.get(
                    blh.replace("+", "-").replace("/", "_"))
                if content is None:
                    unexpandable.append((blh, path))
                else:
                    for h in content:
                        needed.setdefault(h, f"data block of {path}")
        elif size > 0:
            needed.setdefault(entry["hash"], f"single-block content of {path}")
    print(f"dlist      : {files} files, {dirs} non-file entries -> {len(needed)} distinct needed hashes, {len(unexpandable)} unexpandable blocklists")

    missing = {h: why for h, why in needed.items() if h not in available}

    print()
    if not missing and not unexpandable:
        print(f"RESULT: COMPLETE COVERAGE -- all {len(needed)} hashes the dlist references are declared present by the dindex set.")
        sys.exit(0)
    if missing:
        print(f"RESULT: {len(missing)} MISSING hash(es) -- referenced by the dlist, declared by NO dindex:")
        for h, why in list(missing.items())[:20]:
            print(f"  {h}  ({why})")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
    if unexpandable:
        print(f"RESULT: {len(unexpandable)} UNEXPANDABLE blocklist(s) (no list/* entry in any dindex; data-block coverage unprovable from destination):")
        for blh, path in unexpandable[:10]:
            print(f"  {blh}  ({path})")
    sys.exit(1)


if __name__ == "__main__":
    main()
