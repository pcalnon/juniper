#!/usr/bin/env python3
"""Diff the 2026-02-27 project archive's legacy trees against the current juniper-legacy/ tree.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc/2026-08-28_legacy_archive_diff.py
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Answers one question: does the 2026-02-27 archive hold legacy content the CURRENT tree does not
reproduce? If not, the 2026-02-27 backup run can skip it. If so, it must carry it.

LAYOUT CHANGE, and why a naive prefix diff is wrong. On 2026-02-27 the legacy content sat at the
Juniper parent's TOP LEVEL as `JuniperBackup/`, `JuniperCascor/`, `JuniperData/`, `JuniperLegacy/`.
It was later consolidated INTO `juniper-legacy/<same four>`. A diff keyed on a `juniper-legacy/`
prefix therefore finds nothing in the archive and concludes -- wrongly -- that it is absent. This
script maps each archived top-level legacy directory onto its current home before comparing.

Comparison is on (relative path, size). Size is a strong signal for a legacy tree of binaries,
checkpoints and datasets; it will not catch a same-size content edit, so --hash-sample spot-checks
a random sample of same-size files with SHA-256 on both sides.

Usage:
    python3 util/ad-hoc/2026-08-28_legacy_archive_diff.py \\
        --archive-root ~/juniper-restore-2026-02-27 \\
        --current-root ~/Development/python/Juniper
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import sys
from collections import defaultdict

# Archived top-level directory  ->  its path under the current tree.
LEGACY_MAP = {
    "JuniperBackup": "juniper-legacy/JuniperBackup",
    "JuniperCascor": "juniper-legacy/JuniperCascor",
    "JuniperData": "juniper-legacy/JuniperData",
    "JuniperLegacy": "juniper-legacy/JuniperLegacy",
}


def human(num_bytes: float) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024.0:
            return f"{value:,.1f} {unit}"
        value /= 1024.0
    return f"{value:,.1f} PB"


def walk_sizes(root: str) -> dict[str, int]:
    """Map every regular file under root to its size, keyed by path relative to root."""
    sizes: dict[str, int] = {}
    if not os.path.isdir(root):
        return sizes
    for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                continue
            try:
                sizes[os.path.relpath(full, root)] = os.path.getsize(full)
            except OSError:
                continue
    return sizes


def sha256(path: str) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def top_groups(paths: set[str], sizes: dict[str, int], limit: int = 10) -> list[tuple[str, int, int]]:
    buckets: dict[str, list[int]] = defaultdict(list)
    for member in paths:
        segments = member.split(os.sep)
        key = os.sep.join(segments[:2]) if len(segments) > 1 else member
        buckets[key].append(sizes.get(member, 0))
    rows = [(key, len(vals), sum(vals)) for key, vals in buckets.items()]
    rows.sort(key=lambda row: row[2], reverse=True)
    return rows[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", required=True, help="extracted 2026-02-27 tree")
    parser.add_argument("--current-root", required=True, help="live Juniper parent directory")
    parser.add_argument("--minor-threshold", type=float, default=2.0,
                        help="percent of archived bytes that may be unreproduced and still count as MINOR")
    parser.add_argument("--hash-sample", type=int, default=25,
                        help="same-size files to SHA-256 on both sides (0 disables)")
    args = parser.parse_args()

    archive_root = os.path.expanduser(args.archive_root)
    current_root = os.path.expanduser(args.current_root)

    total_archived: dict[str, int] = {}
    total_current: dict[str, int] = {}
    present_dirs: list[str] = []

    print("=" * 78)
    print("Per legacy tree: 2026-02-27 archive vs. current")
    print("=" * 78)
    print(f"  {'tree':<18}{'archived':>22}{'current':>22}")
    print("  " + "-" * 62)

    for archived_name, current_rel in sorted(LEGACY_MAP.items()):
        archived_dir = os.path.join(archive_root, archived_name)
        current_dir = os.path.join(current_root, current_rel)
        archived_sizes = walk_sizes(archived_dir)
        current_sizes = walk_sizes(current_dir)
        if not archived_sizes and not current_sizes:
            continue
        present_dirs.append(archived_name)
        print(f"  {archived_name:<18}"
              f"{len(archived_sizes):>8,} f {human(sum(archived_sizes.values())):>11}"
              f"{len(current_sizes):>8,} f {human(sum(current_sizes.values())):>11}")
        # Namespace each tree's paths so identical relative names in different trees never collide.
        for rel, size in archived_sizes.items():
            total_archived[f"{archived_name}/{rel}"] = size
        for rel, size in current_sizes.items():
            total_current[f"{archived_name}/{rel}"] = size

    if not total_archived:
        print("\nVERDICT: no legacy trees found in the archive at any known name.")
        print("  Re-check the extracted top level before concluding.")
        return 1

    archived_paths = set(total_archived)
    current_paths = set(total_current)
    only_archived = archived_paths - current_paths
    only_current = current_paths - archived_paths
    shared = archived_paths & current_paths
    changed = {m for m in shared if total_archived[m] != total_current[m]}

    archived_bytes = sum(total_archived.values())
    only_archived_bytes = sum(total_archived[m] for m in only_archived)
    changed_bytes = sum(abs(total_archived[m] - total_current[m]) for m in changed)
    at_risk = only_archived_bytes + changed_bytes
    at_risk_pct = (at_risk / archived_bytes * 100.0) if archived_bytes else 0.0

    print("\n" + "=" * 78)
    print("Aggregate")
    print("=" * 78)
    print(f"  archived total  : {len(total_archived):>8,} files  {human(archived_bytes):>12}")
    print(f"  current total   : {len(total_current):>8,} files  {human(sum(total_current.values())):>12}")
    print("  " + "-" * 62)
    print(f"  only in archive : {len(only_archived):>8,} files  {human(only_archived_bytes):>12}  <-- lost if skipped")
    print(f"  only in current : {len(only_current):>8,} files")
    print(f"  size-changed    : {len(changed):>8,} files  {human(changed_bytes):>12}  <-- lost if skipped")
    print(f"  identical size  : {len(shared) - len(changed):>8,} files")
    print("  " + "-" * 62)
    print(f"  UNREPRODUCED BY THE CURRENT TREE: {human(at_risk)} ({at_risk_pct:.2f}% of archived bytes)")

    if only_archived:
        print("\n  Largest groups present ONLY in the archive:")
        for key, count, total in top_groups(only_archived, total_archived):
            print(f"    {human(total):>12}  {count:>7,} files  {key}")

    if changed:
        deltas = {m: abs(total_archived[m] - total_current[m]) for m in changed}
        print("\n  Largest size-changed files:")
        for member in sorted(deltas, key=lambda m: deltas[m], reverse=True)[:8]:
            print(f"    {human(deltas[member]):>12}  {member}")

    # Size equality is necessary, not sufficient. Spot-check content so an "identical" verdict is not vacuous.
    if args.hash_sample and shared - changed:
        same_size = sorted(shared - changed)
        random.seed(20260828)
        sample = random.sample(same_size, min(args.hash_sample, len(same_size)))
        mismatches = 0
        checked = 0
        for member in sample:
            tree, _, rel = member.partition("/")
            a_path = os.path.join(archive_root, tree, rel)
            c_path = os.path.join(current_root, LEGACY_MAP[tree], rel)
            a_hash, c_hash = sha256(a_path), sha256(c_path)
            if a_hash is None or c_hash is None:
                continue
            checked += 1
            if a_hash != c_hash:
                mismatches += 1
                if mismatches <= 5:
                    print(f"    CONTENT DIFFERS at equal size: {member}")
        print(f"\n  Content spot-check: {checked} same-size files hashed, {mismatches} differ.")
        if mismatches:
            print("  Equal size is NOT proving equal content here -- treat the size verdict as a floor.")

    print("\n" + "=" * 78)
    if at_risk_pct <= args.minor_threshold:
        print(f"VERDICT: MINOR ({at_risk_pct:.2f}% <= {args.minor_threshold}%)")
        print("  The current tree reproduces essentially all archived legacy content.")
        print("  -> The 2026-02-27 run may SKIP the legacy trees.")
        print("  NOTE: that leaves juniper-legacy with NO backup coverage at all, since it is")
        print("        absent from APPLICATION_REPOS. Covering it is a separate decision.")
    else:
        print(f"VERDICT: SUBSTANTIAL ({at_risk_pct:.2f}% > {args.minor_threshold}%)")
        print("  The archive holds legacy content the current tree does not reproduce.")
        print("  -> The 2026-02-27 run MUST carry the legacy trees.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
