"""
How many archive snapshots persist a ``history`` group at all?

Calibration for the instability question. The dataset-swap probe found ZERO swap events in
the unstable networks -- but it also found no ``history`` group in those files, and
``dataset_swaps`` lives *inside* ``history``. Absence of the container is not evidence about
its contents: if no snapshot in the archive carries ``history``, then "no swap events" says
nothing about whether the network was retrained, and the instability question cannot be
settled from the files.

This census establishes which of those two worlds we are in, and dates the transition if
there is one.

STRICTLY READ-ONLY: h5py in "r" mode; no cascor import, so no snapshot can be created.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-24
Status: ad-hoc -- investigation
Retire when: section 3 item 4 of the 2026-08-23 handoff is closed.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import random
import re

import h5py

ARCHIVE = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots")
STAMP = re.compile(r"cascor_snapshot_(\d{8})_")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--archive", type=pathlib.Path, default=ARCHIVE)
    parser.add_argument("--sample", type=int, default=400)
    parser.add_argument("--seed", type=int, default=20260824)
    args = parser.parse_args(argv)

    files = sorted(args.archive.glob("*.h5"))
    print(f"total .h5 in archive: {len(files)}")
    if not files:
        return 1

    chosen = files if args.sample >= len(files) else random.Random(args.seed).sample(files, args.sample)
    groups: collections.Counter = collections.Counter()
    has_history: collections.Counter = collections.Counter()
    has_swaps: collections.Counter = collections.Counter()
    by_month: dict = collections.defaultdict(collections.Counter)
    unreadable = 0

    for path in chosen:
        try:
            with h5py.File(path, "r") as handle:
                keys = set(handle.keys())
                groups[",".join(sorted(keys))] += 1
                present = "history" in keys
                has_history[present] += 1
                if present:
                    has_swaps["dataset_swaps" in handle["history"]] += 1
                match = STAMP.search(path.name)
                month = match.group(1)[:6] if match else "unknown"
                by_month[month][present] += 1
        except Exception:  # noqa: BLE001 - unreadable files are cohort B and expected
            unreadable += 1

    print(f"sampled: {len(chosen)}   unreadable: {unreadable}")
    print(f"has a `history` group: {dict(has_history)}")
    if has_swaps:
        print(f"  of those, has `history/dataset_swaps`: {dict(has_swaps)}")
    print("\ntop-level group sets:")
    for combo, n in groups.most_common(8):
        print(f"  x{n:<5} {combo}")
    print("\nby month (True = carries history):")
    for month in sorted(by_month):
        print(f"  {month}: {dict(by_month[month])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
