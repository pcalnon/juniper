#!/usr/bin/env python3
"""Mutation check for the APD-CASCOR-003 + operation_id route-metadata pins.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation (mutation evidence for the APD-CASCOR-003 close)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-CASCOR-003 and its §4.3 note), the juniper-cascor fix PR named in its §5.1 row

Applies each mutation to a COPY-BACKED source file, runs the pin module in a subprocess with
bytecode writing disabled (a same-second restore otherwise leaves a VALIDATING stale ``.pyc``
-- see memory ``reference_mutation_check_stale_pyc_and_piped_exit``), restores the file in
``finally``, and prints which tests failed. Never uses ``git checkout`` to restore, because that
would also wipe uncommitted real edits on the file.

**M5 is the row that matters most, and it must SURVIVE.** The whole purpose of an explicit
``operation_id`` is to DECOUPLE the published SDK method name from the handler's Python name, so
renaming a handler has to change nothing. A pin asserting ``operation_id == endpoint.__name__``
would pass every other arm here while quietly reinstating the defect in a new form, and only an
expected-survival row exposes that. The sibling ``APD-DATA-023`` close carries the identical row.

    /opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/apd_cascor_003_mutation_check.py <cascor-worktree>
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

TEST = "src/tests/unit/api/test_route_metadata.py"
ADMIN = "src/api/routes/admin.py"
HEALTH = "src/api/routes/health.py"


@dataclass(frozen=True)
class Mutation:
    """One source edit plus the outcome it is expected to produce."""

    label: str
    path: str
    apply: Callable[[str], str]
    expect_fail: bool


MUTATIONS = (
    Mutation(
        label="M1 drop operation_id from one decorator (the original gap)",
        path=ADMIN,
        apply=lambda s: s.replace('operation_id="get_experimental_functions", ', "", 1),
        expect_fail=True,
    ),
    Mutation(
        label="M2 change one published operation_id (a breaking SDK rename)",
        path=ADMIN,
        apply=lambda s: s.replace('operation_id="get_experimental_functions"', 'operation_id="fetch_experimental_functions"', 1),
        expect_fail=True,
    ),
    Mutation(
        label="M3 drop response_model from one envelope route (the original APD-CASCOR-003)",
        path=ADMIN,
        apply=lambda s: s.replace(", response_model=ResponseEnvelope", "", 1),
        expect_fail=True,
    ),
    Mutation(
        label="M4 declare the envelope on a bare-dict health route (changes the cross-service wire)",
        path=HEALTH,
        # health.py does not import ResponseEnvelope (it declares none), so the mutation adds the
        # import too -- otherwise it would fail on NameError at import and prove nothing about the pin.
        apply=lambda s: s.replace("from api.models.health import ", "from api.models.common import ResponseEnvelope\nfrom api.models.health import ", 1).replace('@router.get("/health", operation_id="health_check")', '@router.get("/health", operation_id="health_check", response_model=ResponseEnvelope)', 1),
        expect_fail=True,
    ),
    Mutation(
        label="M5 rename a handler, leaving its operation_id alone (EXPECTED SURVIVAL)",
        path=ADMIN,
        apply=lambda s: s.replace("async def get_experimental_functions(", "async def read_experimental_functions(", 1),
        expect_fail=False,
    ),
)


def run_test(worktree: Path) -> list[str]:
    """Run the pin module and return the names of the tests that failed."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", TEST, "-p", "no:cacheprovider", "-o", "addopts=--tb=line", "-q"],
        cwd=worktree,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    names = re.findall(r"^(?:FAILED|ERROR) .*::(\w+)", proc.stdout, flags=re.MULTILINE)
    if names:
        return names
    # A mutation that breaks IMPORT of the module under test produces a collection error with no
    # per-test line at all. Matching only ``FAILED`` would report that as a clean survival -- the
    # vacuous-pass class. Fall back to the process exit status so a broken run can never read green.
    if proc.returncode != 0:
        return ["<non-zero exit, no per-test line: collection or import error>"]
    return []


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    worktree = Path(argv[0]).resolve()
    baseline = run_test(worktree)
    print(f"baseline failures: {baseline or 'none'}")
    ok = not baseline

    for mut in MUTATIONS:
        target = worktree / mut.path
        original = target.read_text(encoding="utf-8")
        mutated = mut.apply(original)
        if mutated == original:
            print(f"{mut.label}: mutation did not apply -- ABORT")
            return 2
        try:
            target.write_text(mutated, encoding="utf-8")
            failed = run_test(worktree)
        finally:
            target.write_text(original, encoding="utf-8")

        good = bool(failed) == mut.expect_fail
        expected = "fail" if mut.expect_fail else "survive"
        print(f"{mut.label}\n    expected={expected:8s} failed={failed or 'none'}  [{'OK' if good else 'UNEXPECTED'}]")
        ok = ok and good

    after = run_test(worktree)
    print(f"post-restore failures: {after or 'none'}")
    return 0 if ok and not after else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
