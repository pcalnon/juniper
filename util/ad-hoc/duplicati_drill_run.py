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
        --passphrase-file <archive-passphrase-file> \
        --out-dir /path/to/restore-scratch

TWO DIFFERENT SECRETS -- do not conflate them:
  * the **web-UI password** (used by duplicati_api.py to authenticate to :8300)
  * the **archive GPG passphrase** (used to decrypt volumes; restores, purges,
    passphrase verification)
They were the same value once and are not any more. Pointing an archive-passphrase
consumer at the UI-password file fails as "Bad session key", which reads like a
corrupt archive rather than the wrong secret.
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


def secret_fingerprint(secret: str) -> str:
    """Non-reversible identity for a secret, safe to log.

    Returns only a character count and a truncated SHA-256 -- never any part of
    the value. This exists because two same-length secrets are indistinguishable
    by length alone, and this project's credential file holds several; the
    fingerprint is what lets a later reader tell which secret a run actually
    used. It caught a live incident where a backup's in-memory passphrase had
    silently diverged from the file it was read from.

    The hash is a one-way function, so the return value is not sensitive data.
    CodeQL's clear-text-logging query does not model truncated hashing as a
    sanitiser and flags any password-derived value reaching a log sink, hence
    the suppression at the single call sites rather than here.
    """
    digest = hashlib.sha256(secret.encode()).hexdigest()[:16]
    return f"{len(secret)} chars, sha256[:16]={digest}"


def read_passphrase(path: str, key: str = "PASSPHRASE") -> str:
    """Read a NAMED secret from `KEY=VALUE` form, or a bare-secret file.

    The key must be selectable. This file may hold several same-length secrets
    (a new set's passphrase, an old archive's, a UI password), so hardcoding one
    name silently uses whichever the file happens to bind to it -- and that
    binding has already changed once mid-session while a backup was running.

    Never source the file: a secret containing `$` would be expanded and one
    containing a backtick would be EXECUTED.
    """
    with open(path) as fh:
        raw = fh.read()
    m = re.search(rf"^[ \t]*(?:export[ \t]+)?{re.escape(key)}=(.*)$", raw, re.M)
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


def restore(dest: str, dbpath: str, when: str, paths: list[str],
            out_dir: str, passphrase: str, timeout: int) -> tuple[int, str]:
    cmd = [
        "duplicati-cli", "restore", dest, *paths,
        f"--dbpath={dbpath}",
        "--encryption-module=gpg",
        # --time, NOT --version. A positional index computed over surviving
        # filesets disagrees with one computed over all database rows, and the
        # database is what resolves --version. A timestamp names exactly one
        # fileset either way.
        f"--time={when}",
        f"--restore-path={out_dir}",
        "--restore-permissions=false",
        "--overwrite=true",
        # Without this, pre-flight RemoteListAnalysis aborts the WHOLE operation
        # ("Found N files that are missing from the remote storage") before any
        # individual file is attempted -- which reads as "every file failed" and
        # tests nothing. We are deliberately restoring from an archive with known
        # missing volumes; that is the point of the drill.
        "--no-backend-verification=true",
        # CRITICAL for validity. Defaults to FALSE, meaning Duplicati will happily
        # rebuild a file from blocks it finds on the LOCAL disk. Most of these
        # files still exist locally, so leaving this off would let a restore
        # "succeed" without reading the archive at all -- a false pass that proves
        # nothing about whether the backup is recoverable.
        "--no-local-blocks=true",
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
    ap.add_argument("--passphrase-key", default="PASSPHRASE",
                    help="which KEY= entry to read. Same-length secrets are "
                         "indistinguishable by length, so name the key.")
    ap.add_argument("--passphrase-file", required=True,
                    help="file holding the ARCHIVE GPG passphrase (bare secret or "
                         "PASSPHRASE=...). NOT the web-UI password: they are "
                         "different secrets, and the wrong one fails as "
                         "'Bad session key', which reads like a corrupt archive.")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--timeout", type=int, default=5400)
    ap.add_argument("--only", choices=["good", "damaged"], default=None)
    args = ap.parse_args()

    with open(args.candidates) as fh:
        payload = json.load(fh)
    passphrase = read_passphrase(args.passphrase_file, args.passphrase_key)
    if not passphrase:
        print(f"REFUSING: no {args.passphrase_key}= entry in {args.passphrase_file}")
        return 2
    # codeql[py/clear-text-logging-sensitive-data] -- fingerprint only
    print(f"credential: {args.passphrase_file} key={args.passphrase_key} "
          f"({secret_fingerprint(passphrase)})")

    groups = [g for g in ("good", "damaged") if args.only in (None, g)]
    all_results: dict[str, list[dict]] = {}

    for group in groups:
        blk = payload[group]
        out_dir = os.path.join(args.out_dir, group)
        os.makedirs(out_dir, exist_ok=True)
        paths = [f["path"] for f in blk["files"]]
        print()
        sel = blk.get("time")
        if not sel:
            print(f"!! candidates file has no 'time' for group {group}; it was "
                  f"produced by an older selector that emitted a positional "
                  f"--version index. Regenerate it -- that index is not reliable.")
            return 2
        print(f"=== {group.upper()}  fileset {blk['fileset']} "
              f"(id {blk.get('fileset_id')})  --time={sel} ===")
        print(f"    prediction: {blk['predicted']}")
        for p in paths:
            print(f"      {p}")
        rc, out = restore(args.dest, args.dbpath, sel, paths,
                          out_dir, passphrase, args.timeout)
        print(f"    restore exit code: {rc}")
        tail = [ln for ln in out.splitlines() if ln.strip()][-12:]
        for ln in tail:
            print(f"    | {ln}")

        # An operation-level abort is NOT evidence about any individual file.
        # Duplicati can refuse the whole restore during pre-flight (missing
        # remote volumes, bad passphrase, unreadable database), producing zero
        # files -- which looks identical to "every file failed" unless we say so.
        # Reporting that as damage would be a false positive of exactly the kind
        # this drill exists to rule out.
        produced = sum(len(files) for _, _, files in os.walk(out_dir))
        aborted = any(marker in out for marker in (
            "The operation Restore has failed",
            "ErrorID: MissingRemoteFiles",
            "Fatal error",
        ))
        # A TIMEOUT is an abort too, and it carries none of those text markers.
        # Without this, a restore killed at the deadline produces no files, every
        # damaged-group candidate scores NOT_RESTORED, and NOT_RESTORED counts as
        # "as predicted" -- so a run that tested nothing reports as confirmation.
        # Not hypothetical: list-broken-files on this database was killed at 90
        # minutes without finishing.
        if rc == 124:
            aborted = True
            print("    !! restore TIMED OUT — this is an abort, not a result.")
        if aborted and produced == 0:
            print("    !! OPERATION ABORTED before any file was attempted -- "
                  "this run tests NOTHING about the individual files.")
            all_results[group] = [
                {**f, "verdict": "INCONCLUSIVE",
                 "detail": "restore aborted at operation level; file never attempted"}
                for f in blk["files"]]
            continue
        all_results[group] = judge(blk["files"], out_dir)

    print()
    print("=" * 78)
    print("DRILL RESULTS")
    print("=" * 78)
    expected = {"good": "RESTORED_OK", "damaged": "NOT_RESTORED/RESTORED_CORRUPT"}
    surprises = inconclusive = 0
    for group, rows in all_results.items():
        print(f"\n--- {group.upper()} (predicted {expected[group]}) ---")
        for r in rows:
            if r["verdict"] == "INCONCLUSIVE":
                inconclusive += 1
                flag = "NOT TESTED"
            else:
                ok = (r["verdict"] == "RESTORED_OK") if group == "good" \
                    else (r["verdict"] in ("NOT_RESTORED", "RESTORED_CORRUPT"))
                flag = "as predicted" if ok else "*** SURPRISE ***"
                if not ok:
                    surprises += 1
            print(f"  {r['verdict']:<17} {flag:<16} {r['size']:>10,} B  {r['path']}")
            print(f"      {r['detail']}")
    print()
    print(f"SURPRISES: {surprises}   INCONCLUSIVE: {inconclusive}")
    if inconclusive:
        print("VERDICT: INCONCLUSIVE -- the restore did not run to the point of "
              "testing individual files. This is NOT evidence for or against the "
              "offline analysis. Fix the invocation and re-run.")
        return 2
    print("The drill CONFIRMS the offline analysis." if surprises == 0
          else "The drill CONTRADICTS the offline analysis in at least one case.")
    return 0 if surprises == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
