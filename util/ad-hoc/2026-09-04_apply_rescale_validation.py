#!/usr/bin/env python3
"""Route the six synthetic generators' size-knob override through re-validation.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3 follow-up)

``model_copy(update=...)`` does not re-validate in pydantic v2, so the computed
size knob bypassed each generator's own bound (spiral's ``le=MAX_POINTS`` among
them). ``rescale_generator_params`` re-validates, turning the bypass into a 422.

Found by review on juniper-data#361 and confirmed empirically before fixing:
``n_points_per_spiral=10000`` scaled to 17 000, a value the same model rejects
when constructed directly.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d")

GENERATORS = ["spiral", "xor", "gaussian", "moon", "circles", "checkerboard"]


def rewrite(name: str, dry: bool) -> bool:
    path = ROOT / "juniper_data" / "generators" / name / "generator.py"
    src = path.read_text()

    if "params.model_copy(update=" not in src:
        print(f"  {name}: no model_copy call found -- REFUSING", file=sys.stderr)
        return False

    new = src.replace("gen_params = params.model_copy(update=", "gen_params = rescale_generator_params(params, **")
    # `model_copy(update={...})` takes a dict; `rescale_generator_params` takes
    # kwargs, so the braces become nothing and the dict keys become kwargs.
    new = new.replace('rescale_generator_params(params, **{"', 'rescale_generator_params(params, ')
    new = new.replace('": per_unit_count(', "=per_unit_count(")
    new = new.replace('": counts["n_raw_required"]})', "=counts[\"n_raw_required\"])")
    new = new.replace('params.n_spirals)})', "params.n_spirals))")
    new = new.replace("_N_QUADRANTS)})", "_N_QUADRANTS))")
    new = new.replace("params.n_classes)})", "params.n_classes))")

    if "model_copy" in new:
        print(f"  {name}: model_copy survived the rewrite -- REFUSING", file=sys.stderr)
        return False

    # The split import line differs per generator -- the total-knob ones (moon,
    # circles, checkerboard) do not pull `per_unit_count` -- so insert before
    # whatever that line actually says rather than matching one spelling.
    new, n_import = re.subn(
        r"^(from juniper_data\.core\.split import .*)$",
        r"from juniper_data.core.partition_params import rescale_generator_params\n\1",
        new,
        count=1,
        flags=re.M,
    )
    if n_import != 1:
        print(f"  {name}: split import line not found -- REFUSING", file=sys.stderr)
        return False
    # Check the import block itself, not "everything before the first 'class '":
    # these module docstrings contain the word "class", which truncated the
    # slice to a few lines of prose and made this refuse every file.
    if "from juniper_data.core.partition_params import rescale_generator_params" not in new:
        print(f"  {name}: import not added -- REFUSING", file=sys.stderr)
        return False

    if not dry:
        path.write_text(new)
    print(f"  {name}: rewritten")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    ok = True
    for name in GENERATORS:
        print(f"{name}:")
        ok &= rewrite(name, args.dry_run)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
