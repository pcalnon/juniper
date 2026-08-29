#!/usr/bin/env python3
"""Prove the registry ``depends_on`` coverage guard actually fires (juniper-ml, 2026-08-29).

Project:     Juniper
Sub-Project: juniper-ml
Application: release-train registry drift probe
Author:      Paul Calnon
License:     MIT License
Status:      ad-hoc (single-use verification for the fix/release-train-registry-missing-depends-on PR)

WHY THIS EXISTS
---------------
``tests/test_release_train_registry.py``'s cross-repo tier auto-skips when the ecosystem siblings
are not on disk, and neither ``ci.yml`` nor ``main-verify.yml`` clones them -- so the new guard
``test_declared_depends_on_covers_every_real_juniper_dependency`` cannot be demonstrated by
running the suite from a ``.claude/worktrees/`` checkout (``_find_ecosystem_root`` walks two levels
up and finds ``worktrees/``, not the Juniper root).

This probe pins the guard down the way a mutation check would: it evaluates the SAME comparison the
test makes, against the REAL sibling pyprojects, for both the pre-fix and post-fix registry. A guard
that cannot be shown to fail against the broken input is not evidence of anything.

Run:
    python3 util/ad-hoc/2026-08-29_registry_depends_on_probe.py
Exit 0 when the guard behaves correctly (fails pre-fix, passes post-fix); 1 otherwise.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ECOSYSTEM_ROOT = Path("/home/pcalnon/Development/python/Juniper")

sys.path.insert(0, str(REPO_ROOT / "tests"))
import test_release_train_registry as mod  # noqa: E402


def _resolve(pkg: dict) -> Path:
    base = REPO_ROOT if pkg["repo"] == "juniper-ml" else ECOSYSTEM_ROOT / pkg["repo"]
    return (base / pkg["path"] / "pyproject.toml") if pkg["path"] != "." else (base / "pyproject.toml")


def missing_edges(packages: list) -> dict:
    """The exact comparison the guard makes, as {pypi_name: [omitted deps]}."""
    known = {p["pypi_name"] for p in packages}
    out: dict[str, list] = {}
    for pkg in packages:
        if pkg["pypi_name"] == "juniper-ml":
            continue
        pyproject = _resolve(pkg)
        if not pyproject.is_file():
            continue
        real = mod._juniper_pinned_deps(pyproject)
        if real is None:
            continue
        gap = sorted((real & known) - set(pkg["depends_on"]))
        if gap:
            out[pkg["pypi_name"]] = gap
    return out


def main() -> int:
    packages = mod._load_raw()

    post = missing_edges(packages)

    # Reconstruct the pre-fix registry: drop the two edges this PR adds.
    pre_packages = copy.deepcopy(packages)
    for pkg in pre_packages:
        if pkg["pypi_name"] in {"juniper-data", "juniper-cascor"}:
            pkg["depends_on"] = [d for d in pkg["depends_on"] if d != "juniper-service-core"]
    pre = missing_edges(pre_packages)

    print(f"ecosystem root : {ECOSYSTEM_ROOT}")
    print(f"packages read  : {len(packages)}")
    print()
    print("PRE-FIX registry (the state on main before this PR):")
    for name, gap in sorted(pre.items()):
        print(f"  FAIL  {name}: depends_on omits {gap}")
    if not pre:
        print("  (none) -- the guard would NOT have caught the defect")
    print()
    print("POST-FIX registry (this PR):")
    for name, gap in sorted(post.items()):
        print(f"  FAIL  {name}: depends_on omits {gap}")
    if not post:
        print("  (none) -- clean")
    print()

    expected_pre = {"juniper-cascor": ["juniper-service-core"]}
    ok = pre == expected_pre and post == {}
    print("VERDICT:", "guard fires on the defect and is clean after the fix" if ok else "UNEXPECTED -- inspect above")
    if pre != expected_pre:
        print(f"  expected pre-fix failures {expected_pre}, got {pre}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
