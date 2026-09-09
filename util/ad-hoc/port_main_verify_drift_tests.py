#!/usr/bin/env python3
"""Emit a per-repo port of juniper-ml's main-verify catch-up-base test UNION.

Project     : Juniper
Sub-Project : juniper-ml
Application : cross-repo test fan-out (ad-hoc)
Author      : Paul Calnon
License     : MIT License
Created     : 2026-09-08

Why this exists
---------------
`tests/test_main_verify_catchup_base.py` (juniper-ml, 16 tests) and
`src/tests/regression/test_main_verify_catchup_base.py` (juniper-canopy, 6 tests)
guard the SAME defect from two angles, and seven repos have NEITHER:
cascor, cascor-client, cascor-worker, data, data-client, deploy, recurrence.

The guarded defect is silent. `main-verify.yml` resolves its catch-up BASE from
the newest run that reached a sequence-safety VERDICT, and the signal is an EXACT
step name -- `Assert screens reached a verdict`. Rename it and nothing fails: the
resolver matches nothing, silently drops to the legacy `status=success` tier, and
restores the recurring-red defect while every check stays green.

Transcribing 486 lines into seven repos by hand is how fan-outs drift (cf.
`reference_cascor_model_verbatim_extraction_drift`). This script TRANSFORMS the
reference instead, and every replacement below asserts it matched exactly the
expected number of times -- a seam that stops matching is a hard error here rather
than a quietly half-ported file downstream.

Verified 2026-09-08: all seven target repos are an identical fan-out on the three
constants the tests pin -- job id `symbol-screen`, display name `Symbol & Docs
Screen`, and step name `Assert screens reached a verdict`. One canonical port is
therefore correct for all of them.

Three deliberate divergences from BOTH references
-------------------------------------------------
1. `SkipTest` becomes a hard failure. Both references skip when the workflow or
   the resolver step cannot be found. In these seven repos `main-verify.yml` is
   known to exist, so a skip there means the port is MISPLACED -- and a misplaced
   port is silently green, which is the exact vacuous-pass shape the tests exist
   to catch. Skipping on "the step is missing" is worse still: that IS the drift.
2. `RedactedEnv` is dropped rather than copied. The reference masks a copy of the
   real environment because a subprocess-driving test puts its env mapping into
   every failure traceback. This port does not copy the environment at all, which
   removes the exposure instead of masking it -- the fixture needs only PATH, HOME
   and a git identity. It also drops a juniper-ml-only import.
3. canopy's unique static test is folded in, giving the 17-test union.

Usage
-----
    python3 util/ad-hoc/port_main_verify_drift_tests.py \
        --repo-slug pcalnon/juniper-cascor-worker \
        --project juniper-cascor-worker \
        --out /tmp/scratch/test_main_verify_catchup_base.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ML_REFERENCE = Path("tests/test_main_verify_catchup_base.py")
CANOPY_REFERENCE = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src/tests/regression/test_main_verify_catchup_base.py")
UNIQUE_TEST = "test_resolver_prefers_the_screened_tier_over_legacy_success"

PORTED_HEADER = """Ported from juniper-ml (ml#1291 fan-out) by
``util/ad-hoc/port_main_verify_drift_tests.py``. The design of record stays there:
``notes/JUNIPER_2026-08-23_JUNIPER-ML_MAIN-VERIFY-CATCHUP-BASE-SCREENED-NOT-GREEN-DESIGN.md``.

This port differs from BOTH references in one way that matters: where they raise
``SkipTest`` when the workflow or the resolver step cannot be found, this FAILS.
This repo has a ``main-verify.yml``, so a skip would mean the file is misplaced --
and a misplaced guard is silently green, which is the very shape it exists to catch.

"""

CHILD_ENV_HELPER = '''

def _child_env(**overrides: str) -> dict[str, str]:
    """Build a MINIMAL child environment rather than copying ``os.environ``.

    juniper-ml's original passes ``RedactedEnv(os.environ, ...)`` -- a masked copy of
    the real environment -- because a subprocess-driving test leaves its env mapping
    as a frame-local in every failure traceback, and ``--showlocals`` renders it. This
    port does not copy the environment at all, so there is nothing to mask: the
    fixture needs only ``PATH`` (the stub ``gh`` is prepended to it), ``HOME`` for
    git, and an explicit identity. That also removes the juniper-ml-only
    ``tests.redacted_env`` import, which does not exist in this repo.
    """
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),  # nosec B108 - fallback only; git needs a HOME
        "LANG": "C",
    }
    env.update(overrides)
    return env
'''


def _replace_once(text: str, old: str, new: str, *, label: str, expect: int = 1) -> str:
    """Replace ``old`` and assert it matched exactly ``expect`` times."""
    found = text.count(old)
    if found != expect:
        raise SystemExit(f"SEAM DRIFT: {label!r} matched {found} time(s), expected {expect}.\nThe reference changed; re-read it before trusting this port.\nPattern: {old[:120]!r}")
    return text.replace(old, new)


def _extract_unique_test(canopy_src: str) -> str:
    """Pull canopy's one unique test method out verbatim (no transcription)."""
    lines = canopy_src.splitlines(keepends=True)
    start = next((i for i, ln in enumerate(lines) if ln.startswith(f"    def {UNIQUE_TEST}(")), None)
    if start is None:
        raise SystemExit(f"canopy reference no longer defines {UNIQUE_TEST}; re-read {CANOPY_REFERENCE}")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if ln.startswith("    def ") or (ln.strip() and not ln.startswith(" ")):
            end = i
            break
    block = "".join(lines[start:end]).rstrip("\n")
    if UNIQUE_TEST not in block or "status=completed" not in block:
        raise SystemExit("extracted canopy block does not look like the unique test; aborting")
    return block


def build(repo_slug: str, project: str, marker: str | None) -> str:
    src = ML_REFERENCE.read_text(encoding="utf-8")
    canopy = CANOPY_REFERENCE.read_text(encoding="utf-8")
    unique = _extract_unique_test(canopy)

    # --- seam 1: the juniper-ml-only RedactedEnv import ------------------------
    src = _replace_once(src, "\nimport yaml\n\nfrom tests.redacted_env import RedactedEnv\n", "\nimport yaml\n", label="RedactedEnv import")

    # --- seam 2: define the replacement helper the next two seams will call ----
    src = _replace_once(src, '\nSTEP_NAME = "Resolve catch-up base"\n', '\nSTEP_NAME = "Resolve catch-up base"\n' + CHILD_ENV_HELPER, label="child-env helper insertion")

    # --- seam 3 + 4: both RedactedEnv construction sites -----------------------
    src = _replace_once(
        src,
        'env=RedactedEnv(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"),',
        'env=_child_env(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"),',
        label="git env",
    )
    src = _replace_once(src, "            env = RedactedEnv(os.environ)\n", "            env = _child_env()\n", label="resolver env")

    # --- seam 4: the repo slug the stubbed gh is asked about -------------------
    src = _replace_once(src, 'repo_name: str = "pcalnon/juniper-ml",', f'repo_name: str = "{repo_slug}",', label="repo slug")

    # --- seam 5: the three SkipTest sites become hard failures -----------------
    src = _replace_once(src, 'raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")', 'raise AssertionError(f"{WORKFLOW_NAME} not present at {wf} -- this repo HAS one, so this test is misplaced (a skip here would be silently green)")', label="missing-workflow skip", expect=2)
    src = _replace_once(src, 'raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")', 'raise AssertionError(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME} -- that IS the drift this test guards, so it must fail, not skip")', label="missing-step skip")

    # --- seam 6: header ---------------------------------------------------------
    src = _replace_once(
        src,
        "Run: python3 -m unittest -v tests/test_main_verify_catchup_base.py\n\nProject: juniper-ml\n",
        PORTED_HEADER + f"Project: {project}\n",
        label="header",
    )

    # --- seam 7: fold in canopy's unique static test ----------------------------
    anchor = "    def test_screen_job_name_matches_the_workflow_job(self) -> None:"
    src = _replace_once(src, anchor, unique + "\n\n" + anchor, label="unique-test anchor")

    # --- seam 8: optional pytest marker for marker-filtered repos ---------------
    if marker:
        src = _replace_once(
            src,
            "import yaml\n",
            f'import pytest\nimport yaml\n\n# This repo\'s CI runs ``pytest -m "unit and not slow"`` with ``--strict-markers``\n# and has no auto-marking conftest, so an UNMARKED file is silently DESELECTED --\n# present, collected by nothing, and green.\npytestmark = pytest.mark.{marker}\n',
            label="pytest marker",
        )

    return src


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-slug", required=True, help="owner/name used by the stubbed gh, e.g. pcalnon/juniper-data")
    ap.add_argument("--project", required=True, help="value for the header's Project: field")
    ap.add_argument("--marker", default=None, help="pytest marker to apply module-wide (use 'unit' for cascor / data)")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    if not ML_REFERENCE.is_file():
        raise SystemExit(f"run this from the juniper-ml repo root; {ML_REFERENCE} not found")

    out = build(args.repo_slug, args.project, args.marker)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out, encoding="utf-8")
    print(f"wrote {args.out} ({len(out.splitlines())} lines, marker={args.marker or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
