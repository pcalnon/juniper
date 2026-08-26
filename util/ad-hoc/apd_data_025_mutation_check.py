#!/usr/bin/env python3
"""Mutation check for the APD-DATA-025 binary-media-type pins in a juniper-data worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation (mutation evidence for the APD-DATA-025 close)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-DATA-025), the juniper-data fix PR named in its §5.1 row

Applies each mutation to a COPY-BACKED source file, runs the pin module in a subprocess with
bytecode writing disabled (a same-second restore otherwise leaves a validating stale ``.pyc``
-- see memory ``reference_mutation_check_stale_pyc_and_piped_exit``), restores the file in
``finally``, and prints which tests failed. Never uses ``git checkout`` to restore, because
that would also wipe uncommitted real edits on the file.

    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/apd_data_025_mutation_check.py <juniper-data-worktree>
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

TEST = "juniper_data/tests/unit/test_binary_media_types.py"
ROUTES = "juniper_data/api/routes/datasets.py"
CONSTANTS = "juniper_data/api/constants.py"
DERIVED = "media_type=BINARY_MEDIA_TYPE,"


def _last_site_inline(source: str, literal: str) -> str:
    """Replace the LAST derived site (the artifact route) with an inline literal."""
    head, sep, tail = source.rpartition(DERIVED)
    return head + f'media_type="{literal}",' + tail if sep else source


MUTATIONS = (
    # (label, relative path, mutation)
    (
        "M1 inline application/zip literal on the export route",
        ROUTES,
        lambda s: s.replace(DERIVED, 'media_type="application/zip",', 1),
    ),
    (
        "M2 artifact route restored to an inline application/octet-stream",
        ROUTES,
        lambda s: _last_site_inline(s, "application/octet-stream"),
    ),
    (
        "M3 BINARY_MEDIA_TYPE changed to application/octet-stream",
        CONSTANTS,
        lambda s: s.replace('BINARY_MEDIA_TYPE: str = "application/zip"', 'BINARY_MEDIA_TYPE: str = "application/octet-stream"', 1),
    ),
)


def run_test(worktree: Path) -> list[str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", TEST, "-p", "no:cacheprovider", "-o", "addopts=--tb=line", "-q"],
        cwd=worktree,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return re.findall(r"^FAILED .*::(\w+)", proc.stdout, flags=re.MULTILINE)


def main() -> int:
    worktree = Path(sys.argv[1]).resolve()
    baseline = run_test(worktree)
    print(f"baseline failures: {baseline or 'none'}")
    ok = not baseline
    for label, rel, mutate in MUTATIONS:
        target = worktree / rel
        original = target.read_text(encoding="utf-8")
        mutated = mutate(original)
        if mutated == original:
            print(f"{label}: mutation did not apply -- ABORT")
            return 2
        try:
            target.write_text(mutated, encoding="utf-8")
            failed = run_test(worktree)
        finally:
            target.write_text(original, encoding="utf-8")
        print(f"{label}: failed={failed or 'none'}")
        ok = ok and bool(failed)
    after = run_test(worktree)
    print(f"post-restore failures: {after or 'none'}")
    return 0 if ok and not after else 1


if __name__ == "__main__":
    raise SystemExit(main())
