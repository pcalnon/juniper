"""
Survey every shipped suite for the per_run_timeout / wall-budget ORDERING defect.

`per_run_timeout_seconds` is run_suite's SUBPROCESS timeout. When it sits at or below
the driver's effective wall budget, run_suite kills the driver from outside, records
`timed_out` with `exit_code: null` (run_suite.py:350-354, returning BEFORE the manifest
read at :355) and the driver never writes its manifest -- the honest `timed_out` record
of the plan's Section 13.4 is lost.

The rule is stated in-repo by a suite author at
`util/experiments/suites/p4/e-j-h2h-wide-cap64.yaml:73-75`: per_run_timeout_seconds must
sit ABOVE the effective wall budget so the DRIVER is what stops a run.

Effective-budget precedence, per `run_experiment.py:1384` / `:1883`
(`CLI > YAML outputs.max_wall_seconds > 3600`):

  1. suite `execution.max_wall_seconds`  -> forwarded as --max-wall-seconds, WINS outright
  2. else the resolved cell config's `outputs.max_wall_seconds`
     (base_config, with matrix / include dotted overrides applied -- E-I uses this)
  3. else DEFAULT_MAX_WALL_SECONDS = 3600

The budget is therefore PER-CELL, not per-suite, so this resolves after expand_cells
rather than at load time. Base configs that do not resolve locally (uncloned sibling
repos) are reported UNRESOLVED and declined rather than guessed -- mirroring
`tests/test_experiment_suite_yamls.py::_inherited_wall_budgets`.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-20
Status: ad-hoc -- investigation
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the ordering gate lands in tests/test_experiment_suite_yamls.py and this
             survey is reproducible from that gate's own helper.
Related: HANDOFF_2026-08-18_cli-experimentation-unowned-tasks.md T1; ml#1142; ml#1152
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "util" / "experiments"))

import run_suite  # noqa: E402

SUITES_DIR = REPO_ROOT / "util" / "experiments" / "suites"
# An `app: cascor` suite may legitimately live outside the shipped tree. One did --
# `util/ad-hoc/2026-08-10_spiral_correlation_threshold_diagnostic.yaml`, INVERTED at
# 1800/3600 and invisible to this survey AND to the T1 gate, both of which scanned
# SUITES_DIR alone. Scanned separately (2026-08-24) so the shipped-suite counts stay
# comparable with the gate's, which is still SUITES_DIR-only by design.
ADHOC_DIR = REPO_ROOT / "util" / "ad-hoc"
DEFAULT_TIMEOUT = 3600.0
DEFAULT_WALL = 3600.0
WALL_KEY = "outputs.max_wall_seconds"


def _num(value):
    """Coerce to float, rejecting bools (which are ints in Python)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def cell_budgets(doc: dict, suite_path: Path):
    """Effective wall budget for every cell, plus any base configs that did not resolve.

    Returns (budgets, unresolved). A suite-level ``execution.max_wall_seconds`` short-
    circuits: the forwarded CLI flag wins over whatever the cell config says.
    """
    declared = _num((doc.get("execution") or {}).get("max_wall_seconds"))
    if declared is not None:
        return [declared], []

    budgets: list[float] = []
    unresolved: list[str] = []
    try:
        cells = run_suite.expand_cells(doc, suite_path)
    except Exception as exc:  # noqa: BLE001 - survey must not die on one bad suite
        return [], [f"expand_cells failed: {exc}"]

    for cell in cells:
        override = _num(cell["overrides"].get(WALL_KEY))
        if override is not None:
            budgets.append(override)
            continue
        path = Path(cell["config_path"])
        try:
            base = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
        except (OSError, yaml.YAMLError):
            base = None
        if not isinstance(base, dict):
            unresolved.append(str(path))
            continue
        inherited = _num((base.get("outputs") or {}).get("max_wall_seconds"))
        budgets.append(inherited if inherited is not None else DEFAULT_WALL)
    return budgets, unresolved


def verdict(timeout: float, budgets: list[float]) -> str:
    """INVERTED when the subprocess kill can pre-empt the driver on any cell."""
    if not budgets:
        return "UNRESOLVED"
    worst = max(budgets)
    if timeout < worst:
        return "INVERTED"
    if timeout == worst:
        return "EQUAL"
    return "OK"


def survey(base_dir: Path, skip_non_suites: bool = False) -> list[tuple]:
    """Rows for every suite YAML under ``base_dir``.

    ``skip_non_suites`` drops files that fail ``load_suite`` instead of reporting them
    UNRESOLVED. Off for SUITES_DIR, where every YAML is meant to be a suite and a load
    failure is a finding; on for ADHOC_DIR, which is mostly base configs and unrelated
    workflow YAML that would otherwise bury the one real row in noise.
    """
    rows: list[tuple] = []
    for path in sorted(base_dir.rglob("*.yaml")):
        rel = path.relative_to(base_dir)
        try:
            doc = run_suite.load_suite(path)
        except Exception as exc:  # noqa: BLE001
            if skip_non_suites:
                continue
            rows.append((str(rel), "?", "?", "?", "UNRESOLVED", f"load_suite failed: {exc}"))
            continue
        app = (doc.get("suite") or {}).get("app", "?")
        execution = doc.get("execution") or {}
        timeout = _num(execution.get("per_run_timeout_seconds"))
        timeout = DEFAULT_TIMEOUT if timeout is None else timeout
        declared = _num(execution.get("max_wall_seconds"))
        budgets, unresolved = cell_budgets(doc, path)
        note = ""
        if declared is not None:
            note = "declares execution.max_wall_seconds"
        elif unresolved:
            note = f"unresolved base: {unresolved[0]}"
        span = "-" if not budgets else (
            f"{max(budgets):g}" if len(set(budgets)) == 1 else f"{min(budgets):g}..{max(budgets):g}"
        )
        rows.append((str(rel), app, f"{timeout:g}", span, verdict(timeout, budgets), note))
    return rows


def _print_table(rows: list[tuple]) -> None:
    width = max(len(r[0]) for r in rows)
    print(f"{'suite':<{width}}  {'app':<10} {'timeout':>8} {'budget':>12}  verdict     note")
    print("-" * (width + 56))
    for rel, app, timeout, span, verd, note in sorted(rows, key=lambda r: (r[4], r[0])):
        print(f"{rel:<{width}}  {app:<10} {timeout:>8} {span:>12}  {verd:<11} {note}")

    print()
    for name in ("INVERTED", "EQUAL", "OK", "UNRESOLVED"):
        count = sum(1 for r in rows if r[4] == name)
        print(f"{name:<11} {count}")
    print(f"{'TOTAL':<11} {len(rows)}")


def main() -> int:
    shipped = survey(SUITES_DIR)
    _print_table(shipped)
    at_risk = sum(1 for r in shipped if r[4] in ("INVERTED", "EQUAL"))
    print(f"\na gate with predicate `per_run_timeout_seconds <= effective_budget` fires on {at_risk}")

    adhoc = survey(ADHOC_DIR, skip_non_suites=True)
    print(f"\n=== AD-HOC SUITES under {ADHOC_DIR.relative_to(REPO_ROOT)} (UNGATED) ===")
    if not adhoc:
        print("(none -- no suite-shaped YAML outside the shipped tree)")
        return 0
    _print_table(adhoc)
    adhoc_at_risk = [r for r in adhoc if r[4] in ("INVERTED", "EQUAL")]
    print(
        "\nThese are NOT judged by tests/test_experiment_suite_yamls.py -- it scans the shipped\n"
        "tree only, deliberately, so that util/ad-hoc/ stays scratch. Ordering defects here are\n"
        f"reported, not enforced: {len(adhoc_at_risk)} at risk."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
