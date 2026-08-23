#!/usr/bin/env python3
"""Are the arch-mismatch snapshots DAMAGED, or merely mis-rebuilt?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-22
Status: ad-hoc — investigation (root cause for handoff §3.4, "fails to load" subset)
Retire when: the config_json/live-network divergence is fixed in juniper-cascor, or the
             finding is folded into a cascor regression test.
Related: notes/JUNIPER_2026-08-21_JUNIPER-CASCOR_SNAPSHOT-FORENSICS-TOOLING-DESIGN.md §4.2,
         juniper-cascor `cascade_correlation.py:897` (_resize_network_for_dataset),
         `snapshots/snapshot_serializer.py:324` (_save_configuration), cascor#252

WHAT IT ANSWERS
    The dominant "fails to load" signature is D-E's arch-mismatch gate:

        output_size disagrees: the snapshot's arch group says 3,
        the network built from its config is 2

    Read naively that says the file is inconsistent with itself. It is not. A snapshot
    stores the same fields TWICE, from two different sources:

        arch.attrs / config.attrs  <- the LIVE network (network.output_size)
        config/config_json         <- the CONFIG OBJECT (network.config.output_size)

    `_resize_network_for_dataset` (the live dataset swap, cascor#252) assigns
    `self.output_size = output_size_new` and never touches `self.config`. Nothing in the
    tree ever assigns `config.output_size`. So after a resize the config object is
    permanently stale, and every later snapshot records the contradiction.

    The loader rebuilds from `config_json` — the one stale source — so the rebuilt
    network is narrower than the tensors it is about to load.

    That makes the mismatch a REBUILD fault, not damage. This probe tests that claim the
    only way that settles it: load with `allow_invalid=True` and ask whether the
    recovered network is self-consistent and can actually infer.

USAGE
    python util/ad-hoc/2026-08-22_arch_mismatch_recoverability_probe.py [--limit N]

READ-ONLY. Opens snapshots through cascor's own loader and never writes one.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

ARCHIVE = Path.home() / "Development" / "python" / "Juniper" / "juniper-cascor" / "cascor-snapshots"
CASCOR_SRC = Path.home() / "Development" / "python" / "Juniper" / "juniper-cascor" / "src"


@contextlib.contextmanager
def muffled():
    """cascor logs every load to stdout; keep the report readable."""
    sys.stdout.flush()
    saved, devnull = os.dup(1), os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved, 1)
        os.close(devnull)
        os.close(saved)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=6, help="How many mismatch specimens to probe")
    args = parser.parse_args()

    sys.path.insert(0, str(CASCOR_SRC))
    import h5py
    import torch

    from snapshots.snapshot_serializer import CascadeHDF5Serializer

    index = ARCHIVE / "snapshots_index.jsonl"
    rows = [json.loads(line) for line in index.open() if line.strip()]

    # The population: arch says one output width, config_json says another. Read both
    # straight from the file rather than trusting the index, which only carries `arch`.
    specimens = []
    for row in rows:
        declared = (row.get("arch") or {}).get("output_size")
        if declared is None:
            continue
        try:
            with h5py.File(row["path"], "r") as handle:
                if "config" not in handle or "config_json" not in handle["config"]:
                    continue
                raw = handle["config"]["config_json"][()]
                config = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
        except Exception:  # noqa: BLE001 - unreadable is a different finding
            continue
        if config.get("output_size") != declared:
            specimens.append((row, config.get("output_size"), declared))
        if len(specimens) >= args.limit:
            break

    print(f"probing {len(specimens)} arch/config_json mismatch specimen(s)\n")
    serializer = CascadeHDF5Serializer()
    recovered = 0
    for row, config_says, arch_says in specimens:
        print(f"{row['name'][:58]}")
        print(f"   config_json.output_size={config_says}   arch.output_size={arch_says}")
        with muffled():
            strict = serializer.load_network_result(row["path"], restore_multiprocessing=False)
            network = serializer.load_network(row["path"], restore_multiprocessing=False, allow_invalid=True)
        print(f"   strict load        : {strict.status}")
        if network is None:
            print("   permissive load    : FAILED — genuinely unrecoverable\n")
            continue
        weights = getattr(network, "output_weights", None)
        bias = getattr(network, "output_bias", None)
        hidden = len(getattr(network, "hidden_units", []) or [])
        expected_rows = network.input_size + hidden
        shapes_ok = weights is not None and bias is not None and tuple(weights.shape) == (expected_rows, arch_says) and tuple(bias.shape) == (arch_says,)
        print(f"   permissive load    : OK   weights={tuple(weights.shape)} bias={tuple(bias.shape)} hidden={hidden}")
        print(f"   tensors self-consistent at width {arch_says}: {shapes_ok}")
        try:
            with muffled():
                out = network.forward(torch.zeros(4, network.input_size))
            finite = bool(torch.isfinite(out).all())
            print(f"   inference          : OK  out={tuple(out.shape)} all-finite={finite}")
            if shapes_ok and finite:
                recovered += 1
        except Exception as exc:  # noqa: BLE001 - the point of the probe
            print(f"   inference          : RAISED {type(exc).__name__}: {exc}")
        print()

    print(f"RESULT: {recovered}/{len(specimens)} recovered a self-consistent, inferring network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
