"""
Survey which cascor snapshot `meta` fields are live vs inert, by writer-path cohort.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/snapshot_classify.py SS ITERATIONS, NOT EPOCHS; tests/test_snapshot_classify.py
         IterationsNotEpochsTest; docs/REFERENCE.md snapshot_classify.py entry

WHY THIS EXISTS
    ``util/snapshot_classify.py`` carried a claim -- repeated verbatim in the test suite
    and in ``docs/REFERENCE.md`` -- that three ``meta`` fields are uniformly dead across
    the archive: ``current_epoch`` is 0, ``snapshot_counter`` is 0, ``best_value_loss``
    is inf. Two of those hold. ``snapshot_counter`` does not: it is nonzero in roughly
    45% of the archive. This script is the measurement that settled it, kept so the
    numbers in those three files can be re-derived rather than trusted.

WHAT IT MEASURES
    Files are cohorted by WRITER SIGNATURE, not by ``serializer_version`` -- because the
    serializer version does not separate the populations (every archive file sampled is
    ``2.0.0``, the same as today's). The tell is ``current_epoch``: where it is present
    ``best_value_loss`` is inf, where it is absent ``best_value_loss`` is finite. The
    cohort key is therefore
    ``(serializer_version, format_version, current_epoch present?, history present?)``.

MODES
    --sample N   uniform random sample, seeded (default seed 20260826) -- seconds.
                 Bounds any cohort above ~1% and is what the docstring numbers cite.
    (default)    full census of every ``*.h5`` under the roots -- ~35 min for 28k files,
                 because archive files carry full parameter tensors.

READ-ONLY. Opens every file ``r`` and never writes into a snapshot root. The only write
is the optional ``--json`` report.

USAGE
    python util/ad-hoc/2026-08-26_snapshot_meta_field_survey.py --sample 400 \
        ~/Development/python/Juniper/juniper-cascor/cascor-snapshots

    python util/ad-hoc/2026-08-26_snapshot_meta_field_survey.py \
        ~/.local/state/juniper-experiments --json /tmp/current.json
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import h5py

#: Seeded so a re-run reproduces the exact same sample, and therefore the exact same
#: numbers quoted in snapshot_classify.py. Changing this invalidates those citations.
DEFAULT_SEED = 20260826

FIELD_ABSENT = "<absent>"


def _decode(value: Any, default: str = FIELD_ABSENT) -> str:
    """HDF5 string attrs come back as bytes; normalise for use as a dict key."""
    if value is None:
        return default
    return value.decode() if isinstance(value, bytes) else str(value)


def _new_record() -> Dict[str, Any]:
    return {
        "n": 0,
        "counter_nonzero": 0,
        "counter_zero": 0,
        "counter_absent": 0,
        "bvl_finite": 0,
        "bvl_inf": 0,
        "bvl_absent": 0,
        "epoch_nonzero": 0,
        "history_populated": 0,
        "created_min": None,
        "created_max": None,
        "examples": [],
    }


def _history_is_populated(handle: h5py.File) -> bool:
    """A ``history`` group counts only if at least one series actually has samples."""
    node = handle["history"]
    for key in node.keys():
        child = node[key]
        shape = getattr(child, "shape", None)
        if shape and shape[0] > 0:
            return True
    return False


def _tally(path: str, stats: Dict[Tuple[str, ...], Dict[str, Any]]) -> None:
    with h5py.File(path, "r") as handle:
        root_attrs = dict(handle.attrs)
        meta = dict(handle["meta"].attrs) if "meta" in handle else {}
        has_epoch = "current_epoch" in meta
        has_history = "history" in handle

        key = (
            _decode(root_attrs.get("serializer_version")),
            _decode(root_attrs.get("format_version")),
            f"current_epoch={'yes' if has_epoch else 'no'}",
            f"history={'yes' if has_history else 'no'}",
        )
        record = stats[key]
        record["n"] += 1

        if "snapshot_counter" not in meta:
            record["counter_absent"] += 1
        elif int(meta["snapshot_counter"]) == 0:
            record["counter_zero"] += 1
        else:
            record["counter_nonzero"] += 1

        if "best_value_loss" not in meta:
            record["bvl_absent"] += 1
        elif math.isfinite(float(meta["best_value_loss"])):
            record["bvl_finite"] += 1
        else:
            record["bvl_inf"] += 1

        if has_epoch and int(meta["current_epoch"]) != 0:
            record["epoch_nonzero"] += 1

        if has_history and _history_is_populated(handle):
            record["history_populated"] += 1

        created = _decode(root_attrs.get("created"), "")
        if created:
            if record["created_min"] is None or created < record["created_min"]:
                record["created_min"] = created
            if record["created_max"] is None or created > record["created_max"]:
                record["created_max"] = created

        if len(record["examples"]) < 2:
            record["examples"].append(os.path.basename(path))


def collect(paths: List[str]) -> Dict[Tuple[str, ...], Dict[str, Any]]:
    stats: Dict[Tuple[str, ...], Dict[str, Any]] = defaultdict(_new_record)
    for index, path in enumerate(paths):
        if index and index % 5000 == 0:
            print(f"  ...{index}", flush=True)
        try:
            _tally(path, stats)
        except (OSError, KeyError, ValueError) as exc:
            # One corrupt or half-written file must not abort a 28k-file census; the
            # unreadable cohort is itself a reportable result.
            record = stats[("<unreadable>", "-", "-", "-")]
            record["n"] += 1
            if len(record["examples"]) < 2:
                record["examples"].append(f"{os.path.basename(path)}: {exc}")
    return stats


def report(stats: Dict[Tuple[str, ...], Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key in sorted(stats, key=lambda item: -stats[item]["n"]):
        record = stats[key]
        rows.append({"cohort": " | ".join(key), **record})
        print("=" * 76)
        print(f"COHORT  {' | '.join(key)}")
        print(f"  n = {record['n']}      created {record['created_min']}  ..  {record['created_max']}")
        print(
            f"  snapshot_counter : nonzero={record['counter_nonzero']}"
            f"  zero={record['counter_zero']}  absent={record['counter_absent']}"
        )
        print(
            f"  best_value_loss  : finite={record['bvl_finite']}"
            f"  inf={record['bvl_inf']}  absent={record['bvl_absent']}"
        )
        print(f"  current_epoch    : nonzero={record['epoch_nonzero']}")
        print(f"  history populated: {record['history_populated']}")
        print(f"  examples: {record['examples']}")
    return rows


def gather_paths(roots: List[str]) -> List[str]:
    paths: List[str] = []
    for root in roots:
        paths.extend(sorted(glob.glob(os.path.join(os.path.expanduser(root), "**", "*.h5"), recursive=True)))
    return paths


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", nargs="+", help="Snapshot root(s) to scan, recursively")
    parser.add_argument("--sample", type=int, default=None, help="Sample N files instead of a full census")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Sample seed (default {DEFAULT_SEED})")
    parser.add_argument("--json", dest="json_path", default=None, help="Write the cohort table here as JSON")
    args = parser.parse_args(argv)

    paths = gather_paths(args.roots)
    print(f"population: {len(paths)} file(s)")
    if args.sample is not None and args.sample < len(paths):
        paths = random.Random(args.seed).sample(paths, args.sample)
        print(f"sampling {len(paths)} with seed {args.seed}")

    rows = report(collect(paths))

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(rows, handle, indent=2)
        print(f"\nwrote {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
