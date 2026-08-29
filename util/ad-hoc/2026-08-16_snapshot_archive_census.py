"""
Read-only census + stratified validation of a cascor HDF5 snapshot archive.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-16
Status: ad-hoc — investigation (produced the F-P1-4 lifecycle design's evidence)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the Phase 6.2 snapshot index ships in util/ proper and supersedes this scan.
Related: notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md (§2),
         F-P1-4, juniper-ml#1137

WHAT IT ANSWERS
    How many snapshots exist, how many are actually LOADABLE, what wrote them, and how
    they are distributed over time -- measured rather than assumed. The design it backs
    turns on exactly this: the archive was recorded as "debris" and is in fact ~27.8k
    valid, replayable models, so no sweep is justified.

WHY IT IS NOT A SWEEP
    It opens every file read-only and writes nothing. It has no delete path, by design.
    Retention cannot be decided until snapshots carry run provenance (design §6.1/§6.2);
    until then any deletion rule would be guessing. See the design's §6.5 non-goals.

METHOD NOTE (the mistake this script exists to prevent)
    An earlier probe generalised from the single OLDEST file -- an Oct-2025 husk holding
    only `config`+`meta` that fails verification -- and would have declared 97% of the
    archive dead, making an aggressive sweep look justified. One file is not a cohort.
    Hence --sample: a seed-fixed, stratified draw across filename year-months, validated
    with cascor's OWN verifier rather than a hand-rolled structural guess.

    Note also that mtime is NOT creation time in this archive (a copy reset them all);
    bucket on the filename / the internal `created` attribute instead.

USAGE
    # needs an env with h5py + the cascor tree importable for --sample
    cd <juniper-cascor>/src
    python <juniper-ml>/util/ad-hoc/2026-08-16_snapshot_archive_census.py --census
    python <juniper-ml>/util/ad-hoc/2026-08-16_snapshot_archive_census.py --sample --per-bucket 12

    --dir DIR       snapshot root (default: juniper-cascor/cascor-snapshots -- the ONE root
                    shared by the CLI, service and container tiers since the 2026-08-20
                    storage-convention ruling; was juniper-cascor/src/cascor_snapshots)
    --census        structural census: count, bytes, loadable vs stub, writer versions
    --sample        stratified verify_saved_network sample (needs the cascor tree on sys.path)
    --per-bucket N  sample size per filename year-month (default 12)
    --seed N        sample seed (default 20260816, the figures in the design doc)
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import random
import sys

DEFAULT_DIR = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots"
)


def _decode(value) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def _bucket(path: pathlib.Path) -> str:
    """Year-month from the FILENAME, not mtime (mtimes were reset by a copy)."""
    parts = path.stem.split("_")
    return parts[2][:6] if len(parts) > 2 and len(parts[2]) >= 6 else "unknown"


def census(root: pathlib.Path) -> int:
    import h5py

    files = sorted(root.glob("*.h5"))
    print(f"root       : {root}")
    print(f"total files: {len(files)}")
    if not files:
        return 1

    kinds: collections.Counter = collections.Counter()
    versions: collections.Counter = collections.Counter()
    formats: collections.Counter = collections.Counter()
    buckets: collections.Counter = collections.Counter()
    bucket_bytes: collections.Counter = collections.Counter()
    loadable_bytes = 0
    other_bytes = 0

    for f in files:
        size = f.stat().st_size
        buckets[_bucket(f)] += 1
        bucket_bytes[_bucket(f)] += size
        try:
            with h5py.File(f, "r") as h:
                keys = list(h.keys())
                attrs = dict(h.attrs)
                if not keys and not attrs:
                    kinds["EMPTY (no attrs, no groups)"] += 1
                    other_bytes += size
                elif not keys:
                    kinds["HEADER-ONLY (attrs, no groups)"] += 1
                    other_bytes += size
                else:
                    kinds["LOADABLE (has model groups)"] += 1
                    loadable_bytes += size
                    if "format" in attrs:
                        formats[f"{_decode(attrs['format'])} v{_decode(attrs.get('format_version'))}"] += 1
                    if "juniper_version" in attrs:
                        versions[_decode(attrs["juniper_version"])] += 1
        except Exception as exc:  # noqa: BLE001 - census of possibly-corrupt files
            kinds[f"UNREADABLE ({type(exc).__name__})"] += 1
            other_bytes += size

    print("\n=== classification ===")
    for k, v in kinds.most_common():
        print(f"  {v:6d}  {k}")
    print("\n=== bytes ===")
    print(f"  loadable     : {loadable_bytes / 1024 ** 3:.2f} GiB")
    print(f"  non-loadable : {other_bytes / 1024 ** 3:.2f} GiB")
    print("\n=== format (loadable) ===")
    for k, v in formats.most_common():
        print(f"  {v:6d}  {k}")
    print("\n=== writer juniper_version (loadable) ===")
    for k, v in versions.most_common():
        print(f"  {v:6d}  {k}")
    print("\n=== by FILENAME year-month (count / MiB) ===")
    for b in sorted(buckets):
        print(f"  {b}  {buckets[b]:6d}  {bucket_bytes[b] / 1024 ** 2:9.1f} MiB")
    return 0


def sample(root: pathlib.Path, per_bucket: int, seed: int) -> int:
    """Stratified validation using cascor's own verifier (import required)."""
    import h5py

    try:
        from snapshots.snapshot_serializer import CascadeHDF5Serializer
    except ImportError as exc:
        print(f"cannot import cascor serializer ({exc}).", file=sys.stderr)
        print("Run from <juniper-cascor>/src, or add it to PYTHONPATH.", file=sys.stderr)
        return 2

    files = sorted(root.glob("*.h5"))
    if not files:
        print("no snapshots found", file=sys.stderr)
        return 1

    # nosec B311 - a deterministic statistical sample, not a security draw. The fixed seed
    # is the point: it is what makes the design doc's 88/89 figure reproducible.
    random.seed(seed)
    buckets: collections.defaultdict = collections.defaultdict(list)
    for f in files:
        buckets[_bucket(f)].append(f)

    serializer = CascadeHDF5Serializer()
    overall: collections.Counter = collections.Counter()
    print(f"=== verify_saved_network, <= {per_bucket} per filename year-month (seed {seed}) ===")
    for b in sorted(buckets):
        pool = buckets[b]
        drawn = random.sample(pool, min(per_bucket, len(pool)))
        verdicts: collections.Counter = collections.Counter()
        versions: collections.Counter = collections.Counter()
        for f in drawn:
            try:
                info = serializer.verify_saved_network(f)
                ok = bool(info.get("valid"))
                verdicts["valid" if ok else f"INVALID:{info.get('error')}"] += 1
                overall["valid" if ok else "invalid"] += 1
            except Exception as exc:  # noqa: BLE001
                verdicts[f"EXC:{type(exc).__name__}"] += 1
                overall["exception"] += 1
            try:
                with h5py.File(f, "r") as h:
                    versions[_decode(h.attrs.get("juniper_version"))] += 1
            except Exception as exc:  # noqa: BLE001 - a stub/corrupt file still gets counted
                # Never swallow silently: an unreadable file is a fact about the archive,
                # and hiding it is the exact class of defect this investigation found.
                versions[f"UNREADABLE:{type(exc).__name__}"] += 1
        print(f"  {b} (n={len(drawn)} of {len(pool)}): {dict(verdicts)}")
        print(f"       versions={dict(versions)}")

    print(f"\n=== overall === {dict(overall)}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1], add_help=True)
    ap.add_argument("--dir", type=pathlib.Path, default=DEFAULT_DIR)
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--per-bucket", type=int, default=12)
    ap.add_argument("--seed", type=int, default=20260816)
    args = ap.parse_args(argv)

    if not args.census and not args.sample:
        ap.error("choose --census and/or --sample")
    if not args.dir.is_dir():
        print(f"not a directory: {args.dir}", file=sys.stderr)
        return 2

    rc = 0
    if args.census:
        rc |= census(args.dir)
    if args.sample:
        if args.census:
            print()
        rc |= sample(args.dir, args.per_bucket, args.seed)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
