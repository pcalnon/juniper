"""
Read GROUND TRUTH for the attribution-instability question straight out of the snapshots.

The instability could be explained by the network genuinely having been trained on more than
one dataset. That is not something to infer from scores, because cascor RECORDS it: P2-2
persists every live dataset swap under ``history/dataset_swaps/event_{i}`` with ``before_cfg``,
``after_cfg`` and ``arch_changes``. If those events are present, the network really was
retrained and attribution tracking the newest dataset is CORRECT behaviour. If they are absent
across the whole trajectory, the multi-dataset attribution has no training-side explanation and
is a scoring artifact.

Also dumps the ``data`` group and the D-C ``provenance`` group, which are the other two places
a dataset identity could be recorded.

STRICTLY READ-ONLY: opens each file with ``h5py.File(..., "r")`` and never writes. It does not
import cascor at all, so it cannot trigger the unconditional ``create_snapshot()`` in
``train_output_layer``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-24
Status: ad-hoc -- investigation
Retire when: section 3 item 4 of the 2026-08-23 handoff is closed.
Related: notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

import h5py

ARCHIVE = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots")
UNSTABLE = ("2537e0f0", "846587fb", "17de4973", "1e9e15a8", "5af596ef")


def decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def probe(path: pathlib.Path) -> dict:
    out = {"swaps": 0, "events": [], "groups": [], "provenance": {}, "data": {}}
    with h5py.File(path, "r") as handle:
        out["groups"] = sorted(handle.keys())
        history = handle.get("history")
        if history is not None and "dataset_swaps" in history:
            swaps = history["dataset_swaps"]
            out["swaps"] = len(swaps.keys())
            for key in sorted(swaps.keys()):
                event = swaps[key]
                out["events"].append(
                    {
                        "timestamp": decode(event.attrs.get("timestamp")),
                        "before_cfg": decode(event.attrs.get("before_cfg")),
                        "after_cfg": decode(event.attrs.get("after_cfg")),
                    }
                )
        prov = handle.get("provenance")
        if prov is not None:
            out["provenance"] = {k: decode(v) for k, v in prov.attrs.items()}
        data = handle.get("data")
        if data is not None:
            out["data"] = {"attrs": {k: decode(v) for k, v in data.attrs.items()}, "keys": sorted(data.keys())}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--archive", type=pathlib.Path, default=ARCHIVE)
    parser.add_argument("--uuid", action="append", default=[], help="repeatable; default: the five unstable networks")
    parser.add_argument("--limit", type=int, default=None, help="cap files per network")
    args = parser.parse_args(argv)

    if not args.archive.is_dir():
        print(f"archive not found: {args.archive}", file=sys.stderr)
        return 1

    for uuid in args.uuid or UNSTABLE:
        files = sorted(p for p in args.archive.glob(f"*{uuid}*.h5"))
        if args.limit:
            files = files[: args.limit]
        print("=" * 92)
        print(f"NETWORK {uuid}   files={len(files)}")
        print("=" * 92)
        if not files:
            print("  (no files)\n")
            continue

        swap_counts: collections.Counter = collections.Counter()
        group_sets: collections.Counter = collections.Counter()
        unreadable = 0
        all_events = []
        prov_seen = collections.Counter()
        data_seen = collections.Counter()

        for path in files:
            try:
                info = probe(path)
            except Exception as exc:  # noqa: BLE001 - an unreadable file is a finding
                unreadable += 1
                print(f"  UNREADABLE {path.name}: {type(exc).__name__}: {exc}")
                continue
            swap_counts[info["swaps"]] += 1
            group_sets[",".join(info["groups"])] += 1
            all_events.extend(info["events"])
            prov_seen[json.dumps(info["provenance"], sort_keys=True)] += 1
            data_seen[json.dumps(info["data"], sort_keys=True)] += 1

        print(f"  dataset_swap event counts across files: {dict(swap_counts)}")
        if unreadable:
            print(f"  unreadable: {unreadable}")
        print(f"  top-level group sets: {dict(group_sets)}")
        for blob, n in prov_seen.most_common(3):
            print(f"  provenance x{n}: {blob[:200]}")
        for blob, n in data_seen.most_common(3):
            print(f"  data x{n}: {blob[:200]}")
        if all_events:
            print(f"  --- {len(all_events)} swap event(s) ---")
            for event in all_events[:10]:
                print(f"    {event['timestamp']}  before={str(event['before_cfg'])[:90]}  after={str(event['after_cfg'])[:90]}")
        else:
            print("  ** NO dataset-swap events recorded anywhere in this network's trajectory")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
