#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Run the restore drill and judge each prediction against a content oracle.

Method
------
Candidates and their predictions come from ``duplicati_drill_select.py`` and were
recorded **before** any restore was attempted, so the drill can falsify them.

Each restored file is judged by **SHA-256 + byte length** against the values
recorded in the archived job database (``Blockset.FullHash`` / ``Blockset.Length``;
``Configuration.filehash`` is SHA256). A restore that exits 0 is *not* evidence:
Duplicati can emit a short or zero-length file and still return success, which is
exactly the "vacuous pass" shape this drill exists to rule out.

Verdicts
--------
    RESTORED_OK       file present, length and SHA-256 both match
    RESTORED_CORRUPT  file present but content does not match  <- worst case
    NOT_RESTORED      no file produced
Predictions are GOOD -> expect RESTORED_OK, DAMAGED -> expect NOT_RESTORED
(or RESTORED_CORRUPT). Anything else is a surprise and is reported as such.

Why ``--dbpath`` and not ``--no-local-db``
-----------------------------------------
``--no-local-db`` rebuilds a temporary index from every dindex volume in the
destination on **each** invocation -- measured at >30 minutes for a single small
file here, without completing. Pointing at a *copy* of the archived job database
pays that cost once. The copy is disposable; the original is never opened.

Usage
-----
    python3 util/ad-hoc/duplicati_drill_run.py \
        --candidates drill_candidates.json \
        --dbpath /path/to/disposable-copy.sqlite \
        --dest file:///mnt/Backups/Ubuntu \
        --passphrase-file resources/duplicati.env \
        --out-dir /path/to/restore-scratch
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys


def read_passphrase(path: str) -> str:
    """Accept either `KEY=VALUE` (optionally `export`-prefixed) or a bare secret.

    Never source the file: a bare password containing `$` or a backtick would be
    expanded or executed by the shell.
    """
    with open(path) as fh:
        raw = fh.read()
    m = re.search(r"^[ \t]*(?:export[ \t]+)?PASSPHRASE=(.*)$", raw, re.M)
    if m:
        val = m.group(1).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        return val
    return raw.strip()


def sha256_b64(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(4 << 20), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


def restore(dest: str, dbpath: str, version: int, paths: list[str],
            out_dir: str, passphrase: str, timeout: int) -> tuple[int, str]:
    cmd = [
        "duplicati-cli", "restore", dest, *paths,
        f"--dbpath={dbpath}",
        "--encryption-module=gpg",
        f"--version={version}",
        f"--restore-path={out_dir}",
        "--restore-permissions=false",
        "--overwrite=true",
    ]
    env = dict(os.environ, PASSPHRASE=passphrase)   # never on the command line
    try:
        p = subprocess.run(cmd, env=env, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {timeout}s"


def locate(out_dir: str, original: str) -> str | None:
    """Find the restored copy of `original` under out_dir.

    Duplicati strips leading path components when it can, so search by basename
    rather than assuming the full original path is reproduced.
    """
    base = os.path.basename(original)
    for root, _, files in os.walk(out_dir):
        if base in files:
            return os.path.join(root, base)
    return None


def judge(cands: list[dict], out_dir: str) -> list[dict]:
    results = []
    for c in cands:
        got = locate(out_dir, c["path"])
        if got is None:
            verdict, detail = "NOT_RESTORED", "no file produced"
        else:
            size = os.path.getsize(got)
            if size != c["size"]:
                verdict = "RESTORED_CORRUPT"
                detail = f"length {size} != expected {c['size']}"
            else:
                digest = sha256_b64(got)
                if digest == c["sha256_b64"]:
                    verdict, detail = "RESTORED_OK", "length + SHA-256 match"
                else:
                    verdict = "RESTORED_CORRUPT"
                    detail = f"SHA-256 {digest} != expected {c['sha256_b64']}"
        results.append({**c, "verdict": verdict, "detail": detail})
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--dbpath", required=True, help="DISPOSABLE copy; it gets migrated")
    ap.add_argument("--dest", default="file:///mnt/Backups/Ubuntu")
    ap.add_argument("--passphrase-file", default="resources/duplicati.env")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--timeout", type=int, default=5400)
    ap.add_argument("--only", choices=["good", "damaged"], default=None)
    args = ap.parse_args()

    with open(args.candidates) as fh:
        payload = json.load(fh)
    passphrase = read_passphrase(args.passphrase_file)
    print(f"passphrase: {len(passphrase)} chars from {args.passphrase_file}")

    groups = [g for g in ("good", "damaged") if args.only in (None, g)]
    all_results: dict[str, list[dict]] = {}

    for group in groups:
        blk = payload[group]
        out_dir = os.path.join(args.out_dir, group)
        os.makedirs(out_dir, exist_ok=True)
        paths = [f["path"] for f in blk["files"]]
        print()
        print(f"=== {group.upper()}  fileset {blk['fileset']}  --version={blk['version']} ===")
        print(f"    prediction: {blk['predicted']}")
        for p in paths:
            print(f"      {p}")
        rc, out = restore(args.dest, args.dbpath, blk["version"], paths,
                          out_dir, passphrase, args.timeout)
        print(f"    restore exit code: {rc}")
        tail = [ln for ln in out.splitlines() if ln.strip()][-12:]
        for ln in tail:
            print(f"    | {ln}")
        all_results[group] = judge(blk["files"], out_dir)

    print()
    print("=" * 78)
    print("DRILL RESULTS")
    print("=" * 78)
    expected = {"good": "RESTORED_OK", "damaged": "NOT_RESTORED/RESTORED_CORRUPT"}
    surprises = 0
    for group, rows in all_results.items():
        print(f"\n--- {group.upper()} (predicted {expected[group]}) ---")
        for r in rows:
            ok = (r["verdict"] == "RESTORED_OK") if group == "good" \
                else (r["verdict"] in ("NOT_RESTORED", "RESTORED_CORRUPT"))
            flag = "as predicted" if ok else "*** SURPRISE ***"
            if not ok:
                surprises += 1
            print(f"  {r['verdict']:<17} {flag:<16} {r['size']:>10,} B  {r['path']}")
            print(f"      {r['detail']}")
    print()
    print(f"SURPRISES: {surprises}")
    print("The drill CONFIRMS the offline analysis." if surprises == 0
          else "The drill CONTRADICTS the offline analysis in at least one case.")
    return 0 if surprises == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
