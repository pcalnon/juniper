#!/usr/bin/env python3
"""Wire the tabular generators onto the three-way train/val/test partition.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3)

Rewrites each tabular generator's ``generate()`` from the two-partition
``shuffle_and_split`` call to the sizing-mode-aware
``resolve_counts_for_params`` / ``partition_and_assemble`` pair, swaps the
params model onto the shared ``PartitionParams`` mixin, and bumps the generator
VERSION (R-1's cache-invalidation mitigation).

Mechanical only. Every generator is verified individually afterwards; this
exists so the nine edits are provably identical rather than nine hand
transcriptions -- the failure juniper-data#320 was.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d")

# generator -> (native-rows expression, model_copy update expression or None)
SYNTHETIC: dict[str, tuple[str, str]] = {
    "xor": ("_N_QUADRANTS * params.n_points_per_quadrant", '{"n_points_per_quadrant": per_unit_count(counts["n_raw_required"], _N_QUADRANTS)}'),
    "gaussian": ("params.n_classes * params.n_samples_per_class", '{"n_samples_per_class": per_unit_count(counts["n_raw_required"], params.n_classes)}'),
    "moon": ("params.n_samples", '{"n_samples": counts["n_raw_required"]}'),
    "circles": ("params.n_samples", '{"n_samples": counts["n_raw_required"]}'),
    "checkerboard": ("params.n_samples", '{"n_samples": counts["n_raw_required"]}'),
}

CLASS_NAME = {
    "xor": ("XorGenerator", "XorParams"),
    "gaussian": ("GaussianGenerator", "GaussianParams"),
    "moon": ("MoonGenerator", "MoonParams"),
    "circles": ("CirclesGenerator", "CirclesParams"),
    "checkerboard": ("CheckerboardGenerator", "CheckerboardParams"),
}

SPLIT_CALL = re.compile(
    r"        X, y = (?P<cls>\w+)\._generate_raw\(params, rng\)\n"
    r"\n"
    r"        split_result = shuffle_and_split\(\n"
    r"            X=X,\n"
    r"            y=y,\n"
    r"            train_ratio=params\.train_ratio,\n"
    r"            test_ratio=params\.test_ratio,\n"
    r"            seed=params\.seed,\n"
    r"            shuffle=params\.shuffle,\n"
    r"        \)\n"
    r"\n"
    r"        return \{\n"
    r'            "X_train": split_result\["X_train"\],\n'
    r'            "y_train": split_result\["y_train"\],\n'
    r'            "X_test": split_result\["X_test"\],\n'
    r'            "y_test": split_result\["y_test"\],\n'
    r'            "X_full": X,\n'
    r'            "y_full": y,\n'
    r"        \}\n"
)


def rewrite_generator(name: str, native: str, update: str, dry: bool) -> bool:
    cls, _ = CLASS_NAME[name]
    path = ROOT / "juniper_data" / "generators" / name / "generator.py"
    src = path.read_text()

    replacement = (
        f"        counts = resolve_counts_for_params(params, {native})\n"
        f"        # Additive sizing needs more raw rows than the size knob names,\n"
        f"        # because that knob now denotes the TRAIN count alone.\n"
        f"        gen_params = params.model_copy(update={update})\n"
        f"\n"
        f"        X, y = {cls}._generate_raw(gen_params, rng)\n"
        f"\n"
        f"        return partition_and_assemble(X, y, counts, params.seed, params.shuffle)\n"
    )

    new, n = SPLIT_CALL.subn(replacement, src)
    if n != 1:
        print(f"  {name}: split-call pattern matched {n} times -- REFUSING", file=sys.stderr)
        return False

    new = new.replace(
        "from juniper_data.core.split import shuffle_and_split\n",
        "from juniper_data.core.split import partition_and_assemble, per_unit_count, resolve_counts_for_params\n",
    )
    new = re.sub(r'^VERSION = "1\.0\.0"$', 'VERSION = "2.0.0"', new, flags=re.M)

    if name == "xor":
        new = new.replace(
            'VERSION = "2.0.0"\n',
            'VERSION = "2.0.0"\n\n#: XOR is four quadrants by construction; the size knob is per-quadrant.\n_N_QUADRANTS = 4\n',
        )

    # Docstring: the returned dict now carries the val pair.
    new = new.replace(
        "                - X_test: Test features",
        "                - X_val: Validation features (n_val, 2)\n                - y_val: Validation labels (n_val, 2)\n                - X_test: Test features",
    )

    if not dry:
        path.write_text(new)
    print(f"  {name}: generator rewritten")
    return True


def rewrite_params(name: str, dry: bool) -> bool:
    _, params_cls = CLASS_NAME[name]
    path = ROOT / "juniper_data" / "generators" / name / "params.py"
    src = path.read_text()

    if f"class {params_cls}(BaseModel):" not in src:
        print(f"  {name}: params base class not found -- REFUSING", file=sys.stderr)
        return False

    new = src.replace(f"class {params_cls}(BaseModel):", f"class {params_cls}(PartitionParams):")
    # The pydantic import line differs per generator (some also pull
    # field_validator), so drop BaseModel from whatever the line actually is
    # rather than matching one spelling of it.
    new = re.sub(
        r"^from pydantic import (?P<names>[^\n]+)$",
        lambda m: "from pydantic import " + ", ".join(n for n in m.group("names").split(", ") if n != "BaseModel") + "\n\nfrom juniper_data.core.partition_params import PartitionParams",
        new,
        count=1,
        flags=re.M,
    )
    if "from juniper_data.core.partition_params import PartitionParams" not in new:
        print(f"  {name}: could not rewrite the pydantic import -- REFUSING", file=sys.stderr)
        return False

    if not dry:
        path.write_text(new)
    print(f"  {name}: params rewritten")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ok = True
    for name, (native, update) in SYNTHETIC.items():
        print(f"{name}:")
        ok &= rewrite_params(name, args.dry_run)
        ok &= rewrite_generator(name, native, update, args.dry_run)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
