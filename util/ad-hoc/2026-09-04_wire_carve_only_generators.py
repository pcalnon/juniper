#!/usr/bin/env python3
"""Wire the three real-data generators onto carve-only three-way partitioning.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3)

``mnist``, ``csv_import`` and ``arc_agi`` read a fixed corpus, so design section
6.3's "not amenable to synthetic generation" clause applies: additive sizing is
unimplementable there, not merely undesirable. Their params models move onto
``CarveOnlyPartitionParams`` (which rejects additive rather than silently
carving), their default ``test_ratio`` drops to 0.1 so the shipped
0.8 / 0.1 / 0.1 carve is valid against the new cross-field validator, and their
VERSION bumps to invalidate cached artifacts (risk R-1).

The generate() bodies are edited by hand, not here -- csv_import's normaliser
and arc_agi's task_ids make them genuinely different.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d")

PARAMS_CLASS = {
    "mnist": "MnistParams",
    "csv_import": "CsvImportParams",
    "arc_agi": "ArcAgiParams",
}


def rewire(name: str, cls: str, dry: bool) -> bool:
    base = ROOT / "juniper_data" / "generators" / name

    params_path = base / "params.py"
    src = params_path.read_text()
    if f"class {cls}(BaseModel):" not in src:
        print(f"  {name}: params base class not found -- REFUSING", file=sys.stderr)
        return False
    new = src.replace(f"class {cls}(BaseModel):", f"class {cls}(CarveOnlyPartitionParams):")
    new = re.sub(
        r"^from pydantic import (?P<n>[^\n]+)$",
        lambda m: "from pydantic import " + ", ".join(x for x in m.group("n").split(", ") if x != "BaseModel") + "\n\nfrom juniper_data.core.partition_params import CarveOnlyPartitionParams",
        new,
        count=1,
        flags=re.M,
    )
    if "CarveOnlyPartitionParams" not in new.split("class ")[0]:
        print(f"  {name}: import rewrite failed -- REFUSING", file=sys.stderr)
        return False
    if not dry:
        params_path.write_text(new)

    gen_path = base / "generator.py"
    gen = gen_path.read_text()
    if "from juniper_data.core.split import shuffle_and_split\n" not in gen:
        print(f"  {name}: split import not found -- REFUSING", file=sys.stderr)
        return False
    gen = gen.replace(
        "from juniper_data.core.split import shuffle_and_split\n",
        "from juniper_data.core.split import partition_and_assemble, resolve_counts_for_params\n",
    )
    gen, n = re.subn(r'^VERSION = "1\.0\.\d+"$', 'VERSION = "2.0.0"', gen, flags=re.M)
    if n != 1:
        print(f"  {name}: VERSION bump matched {n} times -- REFUSING", file=sys.stderr)
        return False
    if not dry:
        gen_path.write_text(gen)

    defaults_path = base / "defaults.py"
    if defaults_path.exists():
        d = defaults_path.read_text()
        d2 = re.sub(r"^([A-Z_]+_DEFAULT_TEST_RATIO: float = )0\.2$", r"\g<1>0.1", d, flags=re.M)
        if d2 != d and not dry:
            defaults_path.write_text(d2)
        if d2 != d:
            print(f"  {name}: test_ratio default 0.2 -> 0.1")

    print(f"  {name}: rewired")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    ok = True
    for name, cls in PARAMS_CLASS.items():
        print(f"{name}:")
        ok &= rewire(name, cls, args.dry_run)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
