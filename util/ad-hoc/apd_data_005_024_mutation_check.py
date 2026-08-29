#!/usr/bin/env python3
"""Mutation check for the APD-DATA-005 / APD-DATA-024 OpenAPI-behind-the-key pins.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- investigation (mutation evidence for the APD-DATA-005 / -024 close)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-DATA-005, APD-DATA-024), the juniper-data fix PR named in its §5.1 row

Applies each mutation to a COPY-BACKED source file, runs the pin module in a subprocess with
bytecode writing disabled (a same-second restore otherwise leaves a VALIDATING stale ``.pyc``
-- see memory ``reference_mutation_check_stale_pyc_and_piped_exit``), restores the file in
``finally``, and prints which tests failed. Never uses ``git checkout`` to restore, because
that would also wipe uncommitted real edits on the file.

M1 is the mutation that matters most. It restores ``/openapi.json`` to ``EXEMPT_PATHS`` while
leaving everything else fixed -- i.e. it recreates the trap of "serve the document" being
mistaken for "serve the document behind the key". If the suite still passed under M1, the
pins would be certifying an OPEN documentation endpoint as secured.

M5 is an EXPECTED-SURVIVAL row: renaming the generated security scheme must change nothing,
because the pins look the scheme up by its ``type``/``in``/``name`` shape rather than by
FastAPI's default class-derived key. A runner that only counts failures cannot show that.

    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/apd_data_005_024_mutation_check.py <juniper-data-worktree>
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

TEST = "juniper_data/tests/unit/test_openapi_security.py"
APP = "juniper_data/api/app.py"
CONSTANTS = "juniper_data/api/constants.py"
SECURITY = "juniper_data/api/security.py"

ROUTERS = """    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(generators.router, prefix=API_PREFIX, dependencies=protected)
    app.include_router(datasets.router, prefix=API_PREFIX, dependencies=protected)
"""


@dataclass(frozen=True)
class Mutation:
    """One source edit plus the outcome it is expected to produce."""

    label: str
    path: str
    apply: Callable[[str], str]
    expect_fail: bool


MUTATIONS = (
    Mutation(
        label="M1 restore /openapi.json to EXEMPT_PATHS (the 'looks fixed, is open' trap)",
        path=CONSTANTS,
        apply=lambda s: s.replace('        f"{API_PREFIX}/health/ready",\n', '        f"{API_PREFIX}/health/ready",\n        "/openapi.json",\n', 1),
        expect_fail=True,
    ),
    Mutation(
        label="M2 gate openapi_url on explorers_enabled again (the original -024 defect)",
        path=APP,
        apply=lambda s: s.replace('        openapi_url="/openapi.json",\n', '        openapi_url="/openapi.json" if explorers_enabled else None,\n', 1),
        expect_fail=True,
    ),
    Mutation(
        label="M3 drop the security dependency from both protected routers (the original -005 defect)",
        path=APP,
        apply=lambda s: s.replace(ROUTERS, ROUTERS.replace(", dependencies=protected", ""), 1),
        expect_fail=True,
    ),
    Mutation(
        label="M4 also declare the exempt health router as requiring a key (document overstates policy)",
        path=APP,
        apply=lambda s: s.replace("    app.include_router(health.router, prefix=API_PREFIX)\n", "    app.include_router(health.router, prefix=API_PREFIX, dependencies=protected)\n", 1),
        expect_fail=True,
    ),
    Mutation(
        label="M5 rename the generated security scheme (EXPECTED SURVIVAL)",
        path=SECURITY,
        apply=lambda s: s.replace("api_key_header = APIKeyHeader(name=HEADER_X_API_KEY, auto_error=False)", 'api_key_header = APIKeyHeader(name=HEADER_X_API_KEY, auto_error=False, scheme_name="JuniperDataApiKey")', 1),
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
    return re.findall(r"^FAILED .*::(\w+)", proc.stdout, flags=re.MULTILINE)


def main() -> int:
    worktree = Path(sys.argv[1]).resolve()
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
    raise SystemExit(main())
