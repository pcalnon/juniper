#!/usr/bin/env python3
"""Mutation check for the APD-DATA-021 filter-contract pin in a juniper-data worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc -- investigation (mutation evidence for the APD-DATA-021 close)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-DATA-021), the juniper-data fix PR named in its §5.1 row

Applies each mutation to a COPY-BACKED source file, runs the contract test in a subprocess
with bytecode writing disabled (a same-second restore otherwise leaves a validating stale
``.pyc`` -- see memory ``reference_mutation_check_stale_pyc_and_piped_exit``), restores the
file in ``finally``, and prints which tests failed. Never uses ``git checkout`` to restore,
because that would also wipe uncommitted real edits on the file.

    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/apd_data_021_mutation_check.py <juniper-data-worktree>
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

TEST = "juniper_data/tests/unit/test_filter_contract.py"

MUTATIONS = (
    (
        "M1 inline pattern literal in the route",
        "juniper_data/api/routes/datasets.py",
        lambda s: s.replace("pattern=TAGS_MATCH_PATTERN,", 'pattern="^(any|all)$",', 1),
    ),
    (
        "M2 bare DatasetListFilter class resurrected",
        "juniper_data/core/models.py",
        lambda s: s + '\n\nclass DatasetListFilter(BaseModel):\n    """resurrected"""\n',
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
