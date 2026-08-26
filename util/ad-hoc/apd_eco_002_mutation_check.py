#!/usr/bin/env python3
"""Mutation check for the APD-ECO-002 retry-jitter pins in a Juniper client worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation (mutation evidence for the APD-ECO-002 close)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-ECO-002), the three client fix PRs named in its §5.1 row

Applies each mutation to a COPY-BACKED source file, runs the pin module in a subprocess with
bytecode writing disabled (a same-second restore otherwise leaves a VALIDATING stale ``.pyc`` --
see memory ``reference_mutation_check_stale_pyc_and_piped_exit``), restores the file in
``finally``, and prints which tests failed. Never uses ``git checkout`` to restore, because that
would also wipe uncommitted real edits on the file.

Carries an **expected-survival** row (M3). The property APD-ECO-002 exists for is "the schedule is
decorrelated", NOT "the jitter is 0.5" -- so retuning the constant to another positive value must
change nothing. A runner that only counts failures cannot show that, so each mutation declares the
outcome it expects and the run fails if any mutation deviates.

    python3 util/ad-hoc/apd_eco_002_mutation_check.py <client-worktree> [...]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

TEST = "tests/test_retry_policy.py"

JITTER_KWARG = """            # APD-ECO-002: decorrelate retry schedules across client instances.
            backoff_jitter=DEFAULT_BACKOFF_JITTER,
"""


@dataclass(frozen=True)
class Mutation:
    """One source edit plus the outcome it is expected to produce."""

    label: str
    which: str  # "client" or "constants"
    apply: Callable[[str], str]
    expect_fail: bool


MUTATIONS = (
    Mutation(
        label="M1 drop the backoff_jitter kwarg from the Retry(...) call",
        which="client",
        apply=lambda s: s.replace(JITTER_KWARG, "", 1),
        expect_fail=True,
    ),
    Mutation(
        label="M2 set DEFAULT_BACKOFF_JITTER to 0.0 (kwarg still present)",
        which="constants",
        apply=lambda s: s.replace("DEFAULT_BACKOFF_JITTER: float = 0.5", "DEFAULT_BACKOFF_JITTER: float = 0.0", 1),
        expect_fail=True,
    ),
    Mutation(
        label="M3 retune DEFAULT_BACKOFF_JITTER to 0.25 (EXPECTED SURVIVAL)",
        which="constants",
        apply=lambda s: s.replace("DEFAULT_BACKOFF_JITTER: float = 0.5", "DEFAULT_BACKOFF_JITTER: float = 0.25", 1),
        expect_fail=False,
    ),
)


def discover(worktree: Path) -> tuple[Path, Path, Path]:
    """Return (pytest_cwd, client.py, constants.py) for the one client package under ``worktree``."""
    matches = [m for m in sorted(worktree.glob("**/juniper_*_client/constants.py")) if "test" not in m.parts]
    if len(matches) != 1:
        raise SystemExit(f"{worktree}: expected exactly one client package, found {len(matches)}")
    constants = matches[0]
    return constants.parent.parent, constants.parent / "client.py", constants


def run_test(cwd: Path) -> list[str]:
    """Run the pin module and return the names of the tests that failed."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", TEST, "-p", "no:cacheprovider", "-o", "addopts=--tb=line", "-q"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return re.findall(r"^FAILED .*::(\w+)", proc.stdout, flags=re.MULTILINE)


def check(worktree: Path) -> bool:
    cwd, client, constants = discover(worktree)
    print(f"\n=== {cwd.name} ===")

    baseline = run_test(cwd)
    print(f"baseline failures: {baseline or 'none'}")
    ok = not baseline

    for mut in MUTATIONS:
        target = client if mut.which == "client" else constants
        original = target.read_text(encoding="utf-8")
        mutated = mut.apply(original)
        if mutated == original:
            print(f"{mut.label}: mutation did not apply -- ABORT")
            return False
        try:
            target.write_text(mutated, encoding="utf-8")
            failed = run_test(cwd)
        finally:
            target.write_text(original, encoding="utf-8")

        good = bool(failed) == mut.expect_fail
        verdict = "OK" if good else "UNEXPECTED"
        expected = "fail" if mut.expect_fail else "survive"
        print(f"{mut.label}\n    expected={expected:8s} failed={failed or 'none'}  [{verdict}]")
        ok = ok and good

    after = run_test(cwd)
    print(f"post-restore failures: {after or 'none'}")
    return ok and not after


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    results = {Path(a).resolve().name: check(Path(a).resolve()) for a in argv}
    print("\n=== summary ===")
    for name, good in results.items():
        print(f"{'PASS' if good else 'FAIL'}  {name}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
