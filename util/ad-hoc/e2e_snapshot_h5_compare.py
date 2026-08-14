#!/usr/bin/env python3
"""Compare cascor snapshot .h5 artifacts, structure by structure.

Project:     Juniper
Sub-Project: juniper-ml
Application: Canopy E2E validation arc -- Phase 1 evidence tooling
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Why this exists
---------------
Phase-1 segment 6 established **F-CASCOR-002** (snapshot load always drops
optimizer state) from a reproduced ``TypeError`` plus the swallowed WARNING.
Segment 7 found a second, *physical* corroboration: re-snapshotting a network
that was itself restored from a snapshot yields a measurably SMALLER artifact,
because the optimizer state that failed to load is simply not there to write
back out.

This script makes that claim checkable rather than asserted: it prints the
node inventory, the optimizer-related nodes, and the dtype actually used for
``learning_rate`` (the ``np.bytes_`` that trips torch's range check at
``:1037``) for every ``.h5`` in a directory.

Usage
-----
    python util/ad-hoc/e2e_snapshot_h5_compare.py <snapshot-dir>

Read-only: opens every file with mode ``r`` and writes nothing.
"""

from __future__ import annotations

import os
import sys


def describe(path: str) -> None:
    """Print a one-file structural summary."""
    import h5py  # imported lazily so --help-ish misuse fails fast without h5py

    size = os.path.getsize(path)
    print(f"\n--- {os.path.basename(path)} ({size:,} bytes) ---")
    with h5py.File(path, "r") as handle:
        nodes: list[str] = []
        handle.visit(nodes.append)

        tops = sorted({n.split("/")[0] for n in nodes})
        print(f"  nodes: {len(nodes)}   top-level groups: {tops}")

        opt = [n for n in nodes if "optim" in n.lower()]
        print(f"  optimizer nodes: {len(opt)}" + (f" -> {opt[:8]}" if opt else "  <-- ABSENT"))

        for key in ("learning_rate", "lr"):
            if key in handle.attrs:
                value = handle.attrs[key]
                print(f"  attrs[{key!r}] = {value!r}  (python type {type(value).__name__})")

        for name in nodes:
            node = handle.get(name)
            if hasattr(node, "attrs") and "learning_rate" in getattr(node, "attrs", {}):
                value = node.attrs["learning_rate"]
                print(f"  {name}.attrs['learning_rate'] = {value!r}  (python type {type(value).__name__})")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    directory = argv[1]
    if not os.path.isdir(directory):
        print(f"not a directory: {directory}", file=sys.stderr)
        return 2

    try:
        import h5py  # noqa: F401
    except ImportError:
        print("h5py is not importable in this interpreter; run under an env that has it (e.g. JuniperCascor1)")
        return 3

    files = sorted(f for f in os.listdir(directory) if f.endswith(".h5"))
    if not files:
        print(f"no .h5 files under {directory}")
        return 1
    for name in files:
        describe(os.path.join(directory, name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
