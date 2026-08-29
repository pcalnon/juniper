#!/usr/bin/env python3
"""Tier 3 retirement: the scratch the old-archive purge finally made dead.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tier 3 was named in note §8.8 and has been **blocked on the old-archive purge
decision** ever since.  §8.16 executed that purge, so the block is gone -- and
gone in a way that matters: ``_drill_scratch/`` is 35 GB of temporary SQLite
databases built by the 2026-08-23 drill **to index the very volumes that purge
deleted**.  While the archive existed those DBs were a possible shortcut for
re-drilling it.  With the volumes gone they index nothing.  That is the whole
reason the dependency ran in this direction, and gate 3 enforces it rather than
assuming it.

What is deleted (~99 GB, all on sdc4):

* ``_drill_scratch/*.sqlite*`` -- ~35 GB of drill temp DBs (13.2 GB + 17.3 GB +
  6.9 GB WAL + shm) for the now-purged archive.
* ``_yamaguchi_drill/drill-20260826-175815/restored/`` -- 64 GB of restored
  copies from the migration drill.  The **verdict** of that drill (17/17
  VERIFIED) lives in ``results.json``, not in the restored bytes; the tree is
  scaffolding that has already done its job.
* ``_duplicati_tmp/`` -- the pre-§8.14 tempdir, empty and provably unused since
  ``--tempdir`` moved to ``~/.cache/duplicati-tmp``.

What is **preserved first**, because deleting it would be the real loss:

* ``_drill_scratch/restored/`` -- nine restored sample files (``good/`` and
  ``damaged/``) from the old-archive drill.  264 KB, and now the only surviving
  artifact of a drill whose archive no longer exists.  The standing records sync
  (``yamaguchi_records_sync.bash``) does **not** cover ``_drill_scratch``, so
  these would have gone silently.  Gate 5 copies them to the sda1 mirror.
* Every drill evidence file (``results.json``, ``drill-meta.json``,
  ``provenance.txt``, ``candidates.json``, ``restore-all.log``).  Gate 4 requires
  each to exist on **both** spindles and be byte-identical before ``restored/``
  is touched -- ``yamaguchi_retire_tier2.bash`` reads that ``results.json`` as
  its own gate 4, so destroying it would silently disarm a different tool.

Dry run by default; ``--execute`` required.

Exit: 0 done (or dry run clean), 3 a gate refused, 4 deletion incomplete.
"""

import argparse
import filecmp
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

SDC4 = "/media/pcalnon/temp_backups"
ARCHIVE = "/mnt/Backups/Ubuntu"
LIVE = os.path.join(ARCHIVE, "Yamaguchi")
RECORDS = os.path.join(ARCHIVE, "_yamaguchi_records")
DRILL_RUN = "drill-20260826-175815"
EVIDENCE = ("results.json", "drill-meta.json", "provenance.txt", "candidates.json", "restore-all.log")


def refuse(msg):
    print(f"\nREFUSED: {msg}", file=sys.stderr)
    sys.exit(3)


def human(n):
    v = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(v) < 1024 or unit == "TiB":
            return f"{v:.1f} {unit}" if unit != "B" else f"{int(v)} B"
        v /= 1024.0
    return f"{v:.1f} TiB"


def tree_size(path):
    """Bytes under `path`. Unreadable entries are REPORTED, not swallowed: this number is what
    the operator is shown before authorising a deletion, so a silent skip understates it."""
    total, skipped = 0, []
    # onerror is REQUIRED: os.walk's default silently drops an entire unreadable directory, which
    # is a far larger under-count than the per-file OSError below and would make the docstring false.
    for root, _dirs, files in os.walk(path, onerror=lambda e: skipped.append(f"{e.filename}: {e}")):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.lstat(fp).st_size
            except OSError as exc:
                skipped.append(f"{fp}: {exc}")
    if skipped:
        print(f"   WARNING: {len(skipped)} entr{'y' if len(skipped) == 1 else 'ies'} under {path} "
              f"could not be sized; the total below is a LOWER BOUND", file=sys.stderr)
        for s in skipped[:5]:
            print(f"     {s}", file=sys.stderr)
    return total


def is_mountpoint(path):
    return os.path.ismount(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--execute", action="store_true", help="actually delete (default: dry run)")
    args = ap.parse_args()

    print("== Yamaguchi Tier 3 retirement")
    print(f"   mode: {'EXECUTE' if args.execute else 'DRY RUN'}")

    # ---- gate 0
    for p in (SDC4, ARCHIVE):
        if not is_mountpoint(p):
            refuse(f"{p} is not a mountpoint")
    print("gate 0 PASS: both filesystems mounted")

    # ---- gate 1
    tok = api.login()
    st, state = api.req("GET", "/api/v1/serverstate", tok)
    if st != 200:
        refuse(f"serverstate -> {st}")
    if state.get("ActiveTask") or state.get("SchedulerQueueIds"):
        refuse(f"a task is active or queued: {state.get('ActiveTask')} {state.get('SchedulerQueueIds')}")
    print("gate 1 PASS: ActiveTask=null, scheduler queue empty")

    # ---- gate 2
    st, body = api.req("GET", "/api/v1/backup/2", tok)
    if st != 200 or "Backup" not in body:
        refuse(f"GET backup 2 -> {st}")
    b = body["Backup"]
    meta = {m["Name"]: m["Value"] for m in b.get("Metadata", [])} \
        if isinstance(b.get("Metadata"), list) else dict(b.get("Metadata") or {})
    n, sz = 0, 0
    with os.scandir(LIVE) as it:
        for e in it:
            if e.is_file():
                n += 1
                sz += e.stat().st_size
    if (n, sz) != (int(meta.get("TargetFilesCount", -1)), int(meta.get("TargetFilesSize", -1))):
        refuse(f"live set does not reconcile: {n}/{sz} vs server "
               f"{meta.get('TargetFilesCount')}/{meta.get('TargetFilesSize')}")
    print(f"gate 2 PASS: live set reconciles -- {n} files / {sz} B AGREE")

    # ---- gate 3: Tier 3's actual precondition -- the purge really happened
    root_files = [f for f in os.listdir(ARCHIVE) if os.path.isfile(os.path.join(ARCHIVE, f))]
    vols = [f for f in root_files if f.endswith((".dblock.zip.gpg", ".dindex.zip.gpg"))]
    dlists = [f for f in root_files if f.endswith(".dlist.zip.gpg")]
    if vols:
        refuse(f"the old archive still holds {len(vols)} volumes -- Tier 3 is gated on the purge "
               "(those drill DBs index these volumes and are NOT dead while they exist)")
    if len(dlists) != 10:
        refuse(f"expected the 10 retained dlists at the archive root, found {len(dlists)}")
    print(f"gate 3 PASS: purge complete -- 0 volumes at the archive root, {len(dlists)} dlists retained")

    # ---- gate 4: drill evidence exists on BOTH spindles, byte-identical
    src_run = os.path.join(SDC4, "_yamaguchi_drill", DRILL_RUN)
    dst_run = os.path.join(RECORDS, "_yamaguchi_drill", DRILL_RUN)
    for name in EVIDENCE:
        a, c = os.path.join(src_run, name), os.path.join(dst_run, name)
        if not os.path.isfile(a):
            refuse(f"drill evidence missing on sdc4: {a}")
        if not os.path.isfile(c):
            refuse(f"drill evidence not mirrored to sda1: {c} -- run yamaguchi_records_sync.bash")
        if not filecmp.cmp(a, c, shallow=False):
            refuse(f"drill evidence differs between spindles: {name}")
    print(f"gate 4 PASS: {len(EVIDENCE)} drill evidence files present on both spindles, byte-identical")

    # ---- gate 5: preserve the old-archive drill samples (NOT covered by records_sync)
    samples_src = os.path.join(SDC4, "_drill_scratch", "restored")
    samples_dst = os.path.join(RECORDS, "_drill_scratch", "restored")
    n_samples = sum(len(f) for _r, _d, f in os.walk(samples_src)) if os.path.isdir(samples_src) else 0
    if n_samples:
        if args.execute:
            # Copy to a staging path and swap, never rmtree-then-copy: the destination is the
            # only surviving artifact of a drill whose archive no longer exists, and a failure
            # between the delete and the copy would destroy it outright.
            os.makedirs(os.path.dirname(samples_dst), exist_ok=True)
            staging = samples_dst + ".incoming"
            if os.path.isdir(staging):
                # NOT ignore_errors: a stale .incoming that cannot be removed must stop the run.
                # Inferring "I copied into staging" from isdir(staging) afterwards would promote
                # that leftover over the fresh copy -- and a leftover of the same 9 samples passes
                # a count check, so the wrong bytes land silently.
                shutil.rmtree(staging)
            used_staging = os.path.isdir(samples_dst)
            shutil.copytree(samples_src, staging if used_staging else samples_dst, symlinks=True)
            if used_staging:
                shutil.rmtree(samples_dst)
                os.rename(staging, samples_dst)
            got = sum(len(f) for _r, _d, f in os.walk(samples_dst))
            if got != n_samples:
                refuse(f"sample preservation incomplete: {got}/{n_samples}")
            print(f"gate 5 PASS: {n_samples} old-archive drill sample(s) preserved to {samples_dst}")
        else:
            print(f"gate 5 (dry run): would preserve {n_samples} sample(s) -> {samples_dst}")
    else:
        print("gate 5 PASS: no drill samples to preserve")

    # ---- gate 6: the old tempdir is empty and no longer the job's tempdir
    tmpdir = os.path.join(SDC4, "_duplicati_tmp")
    live_tmp = next((s.get("Value") for s in b.get("Settings", []) if s.get("Name") == "--tempdir"), None)
    if live_tmp and os.path.realpath(live_tmp) == os.path.realpath(tmpdir):
        refuse(f"--tempdir is still {live_tmp} -- not retirable")
    leftover = os.listdir(tmpdir) if os.path.isdir(tmpdir) else []
    if leftover:
        refuse(f"{tmpdir} is not empty: {leftover[:5]}")
    print(f"gate 6 PASS: {tmpdir} empty; live --tempdir is {live_tmp}")

    # ---- the deletion set
    scratch = os.path.join(SDC4, "_drill_scratch")
    dbs = [os.path.join(scratch, f) for f in os.listdir(scratch)
           if f.endswith((".sqlite", ".sqlite-wal", ".sqlite-shm")) or ".sqlite" in f] \
        if os.path.isdir(scratch) else []
    restored = os.path.join(src_run, "restored")
    db_bytes = sum(os.path.getsize(p) for p in dbs)
    restored_bytes = tree_size(restored) if os.path.isdir(restored) else 0

    print("\n== deletion set")
    for p in dbs:
        print(f"   {human(os.path.getsize(p)):>10}  {p}")
    print(f"   {human(restored_bytes):>10}  {restored}/")
    print(f"   {'(empty dir)':>10}  {tmpdir}/")
    print(f"   total: {human(db_bytes + restored_bytes)}")
    st_before = os.statvfs(SDC4)
    print(f"   sdc4 free before: {human(st_before.f_bavail * st_before.f_frsize)}")

    if not args.execute:
        print("\nDRY RUN -- nothing deleted. All gates passed; re-run with --execute.")
        return 0

    freed = 0
    for p in dbs:
        sz = os.path.getsize(p)
        os.remove(p)
        freed += sz
    if os.path.isdir(restored):
        shutil.rmtree(restored)
        freed += restored_bytes
    if os.path.isdir(tmpdir):
        os.rmdir(tmpdir)

    # post-conditions: the evidence we promised to keep is still there
    for name in EVIDENCE:
        if not os.path.isfile(os.path.join(src_run, name)):
            print(f"FATAL: evidence {name} vanished from {src_run}", file=sys.stderr)
            return 4
    if n_samples and sum(len(f) for _r, _d, f in os.walk(samples_dst)) != n_samples:
        print("FATAL: preserved samples are incomplete", file=sys.stderr)
        return 4
    st_after = os.statvfs(SDC4)
    print(f"\nfreed {human(freed)}; sdc4 free now {human(st_after.f_bavail * st_after.f_frsize)}")
    print(f"kept: {len(EVIDENCE)} drill evidence files, {n_samples} preserved sample(s), "
          "and the 196 GB frozen Yamaguchi copy (Paul: KEEP)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
