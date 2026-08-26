"""
Probe what a SHAPE-BROKEN cascor snapshot actually does after it is loaded.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-20
Status: ad-hoc — investigation (evidence for the `_validate_shapes` warn-and-continue defect)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the warn-and-continue behaviour is decided and fixed in juniper-cascor.
Related: notes/JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md §9,
         juniper-cascor `snapshots/snapshot_serializer.py:913` (the warn), `:1592`
         (`_validate_shapes`), juniper-cascor#539

WHAT IT ANSWERS
    `load_network` calls `_validate_shapes` and, on failure, only logs a WARNING —
    then returns the network anyway, which `_load_snapshot_to_network` installs on the
    live lifecycle. The operator is told the restore succeeded.

    The open question is what that network then DOES. Two very different answers are
    possible and they imply different fixes:

      (a) it raises somewhere downstream  -> loud, late, but not silently wrong;
      (b) the bad shape BROADCASTS        -> the network computes garbage and reports
                                             nothing, which is far worse.

    This script answers it by measurement rather than by reading, for each of the four
    violation classes `_validate_shapes` detects.

WHY IT CORRUPTS THE FILE RATHER THAN THE OBJECT
    Mutating tensors on an in-memory network would skip the load path entirely — and the
    load path is the thing under test. Each case here does a real save -> corrupt the
    HDF5 dataset -> real `load_network` -> use the result.

    It writes only into a temp dir it creates, and never touches the snapshot archive.

    A second mode, --archive-sample N, sizes the BLAST RADIUS of rejecting at load: it
    loads a random sample of real archive snapshots and reports how many would newly
    fail. `verify_saved_network` does NOT call `_validate_shapes` (it gates on
    `_validate_format`), so the 2026-08-16 census says nothing about this. Read-only.

USAGE
    # needs the cascor tree importable (run from <juniper-cascor>/src)
    cd <juniper-cascor>/src
    python <juniper-ml>/util/ad-hoc/2026-08-20_shape_broken_network_probe.py
    python <juniper-ml>/util/ad-hoc/2026-08-20_shape_broken_network_probe.py --archive-sample 200
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
import tempfile
from pathlib import Path

import h5py
import numpy as np
import torch

from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig
from snapshots.snapshot_serializer import CascadeHDF5Serializer

INPUT_SIZE = 3
OUTPUT_SIZE = 2
N_HIDDEN = 2
BATCH = 8


def build_reference_network():
    """A small, VALID network with hidden units installed the way growth installs them."""
    torch.manual_seed(42)
    config = CascadeCorrelationConfig(input_size=INPUT_SIZE, output_size=OUTPUT_SIZE, random_seed=42)
    network = CascadeCorrelationNetwork(config=config)
    for _ in range(N_HIDDEN):
        prev_in = network.output_weights.shape[0]
        network._install_hidden_unit(
            weights=torch.randn(prev_in, dtype=torch.float32),
            bias=torch.tensor([0.0], dtype=torch.float32),
            activation_fn=network.activation_fn,
            correlation=0.5,
        )
        network._resize_output_layer_for_new_units(num_added=1, prev_input_size=prev_in)
    network.train_output_layer(torch.randn(BATCH, INPUT_SIZE), torch.randn(BATCH, OUTPUT_SIZE), epochs=3)
    return network


def replace_dataset(path: Path, dataset: str, array: np.ndarray) -> None:
    """Overwrite one dataset in place, changing its shape."""
    with h5py.File(path, "a") as hf:
        del hf[dataset]
        hf.create_dataset(dataset, data=array)


# Each case: (label, dataset path, replacement array builder, what _validate_shapes should say)
CASES = [
    (
        "A: output_weights loses a row",
        "params/output_layer/weights",
        lambda: np.zeros((INPUT_SIZE + N_HIDDEN - 1, OUTPUT_SIZE), dtype=np.float32),
    ),
    (
        "B: output_bias wrong length",
        "params/output_layer/bias",
        lambda: np.zeros((OUTPUT_SIZE + 1,), dtype=np.float32),
    ),
    (
        "C: hidden unit 1 weights too short",
        "hidden_units/unit_1/weights",
        lambda: np.zeros((INPUT_SIZE - 1,), dtype=np.float32),
    ),
    (
        "D: hidden unit 1 weights length 1 (broadcast hazard)",
        "hidden_units/unit_1/weights",
        lambda: np.ones((1,), dtype=np.float32),
    ),
]


def describe(fn) -> str:
    """Run `fn`, reporting either the exception type or a short description of the result."""
    try:
        out = fn()
    except Exception as exc:  # noqa: BLE001 - reporting, not handling
        return f"RAISED {type(exc).__name__}: {str(exc).splitlines()[0][:90]}"
    if isinstance(out, torch.Tensor):
        finite = "finite" if bool(torch.isfinite(out).all()) else "NON-FINITE"
        return f"returned tensor shape={tuple(out.shape)} ({finite})"
    return f"returned {out!r}"


def default_archive() -> Path:
    """Snapshot root, resolved the way the ecosystem resolves it.

    Deliberately NOT derived from this file's location: the script is often run from a
    git worktree nested inside juniper-ml, where walking up parent directories lands
    somewhere that does not exist.  Honour the shared override first, then fall back to
    the documented usage (run from ``<juniper-cascor>/src``).

    The leaf name is ``cascor-snapshots`` since the 2026-08-20 storage-convention ruling --
    one root at the cascor repo root, shared by the CLI, service and container tiers.
    From ``<juniper-cascor>/src`` the cwd-relative fallback no longer lands on it, so pass
    ``--archive`` or export ``JUNIPER_CASCOR_SNAPSHOTS_DIR`` when sampling the real archive.
    """
    override = os.environ.get("JUNIPER_CASCOR_SNAPSHOTS_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.cwd() / "cascor-snapshots"


def archive_sample(archive: Path, sample_size: int, seed: int) -> int:
    """How many REAL archive snapshots does the load-time integrity gate refuse?

    Read-only: opens each file through the production loader and re-runs
    ``_validate_shapes`` on the result. Writes nothing, deletes nothing.

    ``allow_invalid=True`` is REQUIRED here, and is the whole reason this function still
    works. D-E (juniper-cascor#551) made ``load_network`` fail closed, so without the
    flag every shape-invalid file comes back ``None`` and lands in
    ``load_returned_none`` -- collapsing the two categories this sample exists to tell
    apart, and reporting ``SHAPE_INVALID: 0`` as though the archive were clean. The
    measurement tool has to opt out of the gate it is measuring.
    """
    serializer = CascadeHDF5Serializer()
    files = sorted(p for p in archive.glob("*.h5"))
    if not files:
        print(f"no .h5 files under {archive}")
        return 2
    rng = random.Random(seed)
    chosen = files if len(files) <= sample_size else rng.sample(files, sample_size)

    counts = {"shape_ok": 0, "SHAPE_INVALID": 0, "load_returned_none": 0, "load_raised": 0}
    offenders = []
    for path in chosen:
        try:
            network = serializer.load_network(path, restore_multiprocessing=False, allow_invalid=True)
        except Exception:  # noqa: BLE001 - counted, not handled
            counts["load_raised"] += 1
            continue
        if network is None:
            counts["load_returned_none"] += 1
            continue
        if serializer._validate_shapes(network):
            counts["shape_ok"] += 1
        else:
            counts["SHAPE_INVALID"] += 1
            if len(offenders) < 10:
                offenders.append(path.name)

    print(f"\n=== archive shape-validity sample (n={len(chosen)} of {len(files)}, seed {seed}) ===")
    for key, value in counts.items():
        print(f"  {key:>20}: {value}")
    loaded = counts["shape_ok"] + counts["SHAPE_INVALID"]
    if loaded:
        pct = 100.0 * counts["SHAPE_INVALID"] / loaded
        print(f"\n  Of snapshots that deserialize, {pct:.2f}% are refused by the D-E integrity gate")
        print("  (reachable for inspection only via load_network(..., allow_invalid=True)).")
    if offenders:
        print("  first offenders: " + ", ".join(offenders))
    return 0


def inspect_one(path: Path) -> int:
    """Classify a single real snapshot's shape violation and show what it computes.

    Answers the question the sample raises: is a real shape-invalid archive file one of
    the loud classes (A/B/C, which raise) or the SILENT class (D, which broadcasts and
    trains on garbage)?
    """
    serializer = CascadeHDF5Serializer()
    # allow_invalid: the whole point is to inspect a file the D-E gate refuses.
    network = serializer.load_network(path, restore_multiprocessing=False, allow_invalid=True)
    if network is None:
        print(f"{path.name}: load_network returned None even with allow_invalid — not deserializable at all")
        return 1
    print(f"  strict load (production path): {'ACCEPTED' if serializer.load_network(path, restore_multiprocessing=False) is not None else 'REFUSED by the integrity gate'}")

    print(f"\n=== {path.name} ===")
    print(f"  input_size={network.input_size} output_size={network.output_size} hidden={len(network.hidden_units)}")
    expected = network.input_size + len(network.hidden_units)
    print(f"  output_weights {tuple(network.output_weights.shape)}  expected ({expected}, {network.output_size})")
    print(f"  output_bias    {tuple(network.output_bias.shape)}  expected ({network.output_size},)")
    for i, unit in enumerate(network.hidden_units):
        want = network.input_size + i
        got = tuple(unit["weights"].shape) if "weights" in unit else None
        flag = "" if got and got[0] == want else "   <-- MISMATCH"
        print(f"  hidden[{i}] weights {got} expected ({want},){flag}")
    print(f"  _validate_shapes: {serializer._validate_shapes(network)}")

    x = torch.randn(4, network.input_size)
    print(f"  forward(x)      : {describe(lambda: network.forward(x))}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1], add_help=True)
    ap.add_argument("--archive-sample", type=int, default=0, help="instead of the corruption cases, sample N real archive snapshots for shape validity")
    ap.add_argument("--archive", type=Path, default=None, help="snapshot root (default: $JUNIPER_CASCOR_SNAPSHOTS_DIR, else ./cascor-snapshots)")
    ap.add_argument("--inspect", type=Path, default=None, help="classify one real snapshot's shape violation")
    ap.add_argument("--seed", type=int, default=20260820)
    args = ap.parse_args()

    if args.inspect:
        return inspect_one(args.inspect)
    if args.archive_sample:
        return archive_sample(args.archive or default_archive(), args.archive_sample, args.seed)

    serializer = CascadeHDF5Serializer()
    reference = build_reference_network()
    x = torch.randn(BATCH, INPUT_SIZE)
    y = torch.randn(BATCH, OUTPUT_SIZE)

    with torch.no_grad():
        reference_out = reference.forward(x)
    print(f"reference network: hidden={len(reference.hidden_units)} output_weights={tuple(reference.output_weights.shape)}")
    print(f"reference forward: shape={tuple(reference_out.shape)}\n")

    tmpdir = Path(tempfile.mkdtemp(prefix="shape_probe_"))
    try:
        good = tmpdir / "good.h5"
        assert serializer.save_network(reference, str(good)), "reference save failed"

        for label, dataset, make_array in CASES:
            broken = tmpdir / f"broken_{label[0]}.h5"
            shutil.copy(good, broken)
            replace_dataset(broken, dataset, make_array())

            print(f"--- {label}")
            # The production path now refuses these (D-E). Report that, then re-load
            # with the forensic flag so the rest of the probe can still show WHAT the
            # broken network would have done -- which is the evidence this script
            # exists to produce, and which is no longer reachable any other way.
            strict = serializer.load_network(broken, restore_multiprocessing=False)
            print(f"    strict load           : {'ACCEPTED' if strict is not None else 'REFUSED by the integrity gate'}")
            loaded = serializer.load_network(broken, restore_multiprocessing=False, allow_invalid=True)
            if loaded is None:
                print("    (not deserializable even with allow_invalid — nothing further to probe)\n")
                continue

            print(f"    _validate_shapes      : {serializer._validate_shapes(loaded)}  (False = detected)")
            print(f"    forward(x)            : {describe(lambda: loaded.forward(x))}")

            # Did it silently produce a DIFFERENT answer than the intact network?
            try:
                with torch.no_grad():
                    out = loaded.forward(x)
                if out.shape == reference_out.shape:
                    drift = float((out - reference_out).abs().max())
                    verdict = "SILENTLY WRONG" if drift > 1e-6 else "matches reference"
                    print(f"    vs reference output   : {verdict} (max abs delta {drift:.4g})")
            except Exception:  # noqa: BLE001 - already reported above
                pass

            print(f"    train_output_layer    : {describe(lambda: loaded.train_output_layer(x, y, epochs=2))}\n")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
