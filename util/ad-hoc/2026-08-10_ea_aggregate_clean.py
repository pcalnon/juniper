"""Aggregate a cascor experiment grid, keeping only GPU-clean cells.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-10
Status: ad-hoc -- one-off
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the F-P4-1 re-surface evidence note is written; delete with the campaign scripts.
Related: F-P4-1 re-surface; the cascor GPU-leak trap (cascor#509).

A grid collected under the GPU leak spans several suite runs -- per-cell reaping produces
one suite dir per cell -- so the usable result for a cell is scattered across them. A cell
is only usable if its cascor log recorded ZERO ``out of memory`` lines: a contaminated cell
either collapses to the 1-unit / no_candidate signature or, more insidiously, just reports
depressed accuracy (c010: val 0.585 with 202 OOM vs 0.645 clean). So this walks every
matching suite dir, keeps the newest oom==0 succeeded row per cell_id, and reports anything
still missing.

Originally E-A-only (hence the filename); now takes the suite prefix, run root, and expected
cell count as arguments so the same aggregation serves any cascor campaign -- the E-B / E-C
re-runs and the E-H cascor leg. This mirrors how the sibling
``2026-08-10_ea_finish_cells.bash`` grew its ``JUNIPER_SUITE_YAML`` knob.

    python util/ad-hoc/2026-08-10_ea_aggregate_clean.py
    python util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite e-h-real-data --expect 6
    python util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite e-c-cascor-noise-robustness --json

Exit codes: 0 = every expected cell has a clean run; 1 = at least one is missing (so a
campaign script can gate on it); 2 = the run root or suite prefix matched nothing.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_RUN_ROOT = Path(os.environ.get("JUNIPER_EXP_RUN_ROOT", Path.home() / ".local/state/juniper-experiments"))
DEFAULT_SUITE_PREFIX = os.environ.get("JUNIPER_SUITE_PREFIX", "e-a-cascor-budget-sweep")

# The driver writes one log per app; a suite dir for the other app would otherwise score
# every cell -1 (missing log) and silently drop the whole grid.
LOG_CANDIDATES = ("logs/juniper-cascor.log", "logs/juniper-recurrence.log")


def field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else "?"


def find_log(run_dir: Path) -> Path | None:
    """Resolve the app log for a run dir, whichever app produced it."""
    for relative in LOG_CANDIDATES:
        candidate = run_dir / relative
        if candidate.is_file():
            return candidate
    return None


def count_oom(run_dir: Path) -> int:
    """OOM lines in the run's app log, or -1 when no log could be found.

    -1 is deliberately distinct from 0: "we could not verify this cell was clean" must
    never be mistaken for "this cell was clean".
    """
    log = find_log(run_dir)
    if log is None:
        return -1
    return log.read_text(errors="ignore").count("out of memory")


def collect(suites_root: Path, prefix: str) -> tuple[dict[str, dict], set[str], int]:
    """Return (clean rows by cell, every cell_id seen, number of suite dirs scanned)."""
    best: dict[str, dict] = {}
    seen: set[str] = set()
    suite_dirs = 0
    for suite_dir in sorted(suites_root.glob(f"{prefix}-*")):
        registry = suite_dir / "registry.jsonl"
        if not registry.is_file():
            continue
        suite_dirs += 1
        for line in registry.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cell = row["cell_id"][:4]
            seen.add(cell)
            run_dir = Path(row["run_dir"])
            if row["outcome"] != "succeeded" or count_oom(run_dir) != 0:
                continue
            summary = run_dir / "artifacts/results/summary.md"
            text = summary.read_text() if summary.is_file() else ""
            over = row["overrides"]
            # Later suite dirs sort last, so a plain overwrite keeps the newest clean run.
            best[cell] = {
                "pool": over.get("training.params.candidate_pool_size"),
                "cap": over.get("training.params.max_hidden_units"),
                "epochs": over.get("training.params.max_epochs"),
                "overrides": over,
                "units": field(text, r"hidden_units: (\S+)"),
                "train": field(text, r"train_accuracy: (\S+)"),
                "val": field(text, r"val_accuracy: (\S+)"),
                "reason": field(text, r"completion reason: (\S+)"),
                "wall": row["wall_seconds"],
                "corr": max(re.findall(r"hidden_units=\d+: best (\S+)", text) or ["-"]),
            }
    return best, seen, suite_dirs


def print_table(best: dict[str, dict]) -> None:
    print(f"{'cell':<5}{'pool':>5}{'cap':>5}{'units':>7}{'train':>8}{'val':>8}{'wall_s':>8}  {'completion':<15}best_corr")
    for cell in sorted(best):
        r = best[cell]
        # A suite that overrides neither knob (E-H inherits both from its base config) has no
        # cap AND no epochs — print a dash rather than the "None(Noneep)" the E-A-shaped
        # fallback produced.
        if r["cap"] is not None:
            cap = str(r["cap"])
        elif r["epochs"] is not None:
            cap = f"({r['epochs']}ep)"
        else:
            cap = "-"
        pool = str(r["pool"]) if r["pool"] is not None else "-"
        print(f"{cell:<5}{pool:>5}{cap:>5}{r['units']:>7}{r['train'][:6]:>8}{r['val'][:6]:>8}{r['wall']:>8.0f}  {r['reason']:<15}{r['corr']}")
        # A non-cascor suite has none of the three budget knobs; show what it did vary
        # rather than a row of Nones.
        if r["pool"] is None and r["cap"] is None and r["epochs"] is None and r["overrides"]:
            print(f"{'':<5}overrides: {json.dumps(r['overrides'], sort_keys=True)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--suite", default=DEFAULT_SUITE_PREFIX, help=f"suite-dir name prefix (default: {DEFAULT_SUITE_PREFIX})")
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT, help=f"experiment run root (default: {DEFAULT_RUN_ROOT})")
    parser.add_argument("--expect", type=int, default=None, help="expected cell count; default is however many distinct cells the registries mention")
    parser.add_argument("--json", action="store_true", help="emit the clean rows as JSON instead of a table")
    args = parser.parse_args()

    suites_root = args.run_root / "suites"
    if not suites_root.is_dir():
        print(f"ERROR: no suites dir at {suites_root} (set --run-root or JUNIPER_EXP_RUN_ROOT)", file=sys.stderr)
        return 2

    best, seen, suite_dirs = collect(suites_root, args.suite)
    if not suite_dirs:
        print(f"ERROR: no suite dirs matching {args.suite!r}-* under {suites_root}", file=sys.stderr)
        return 2

    # Expected cells: an explicit count when the caller knows the grid size, otherwise the
    # cells the registries actually mention. The latter cannot see a cell that never ran at
    # all, which is exactly why --expect stays available.
    expected = {f"c{i:03d}" for i in range(args.expect)} if args.expect is not None else set(seen)
    missing = sorted(expected - set(best))

    if args.json:
        print(json.dumps({"suite": args.suite, "suite_dirs": suite_dirs, "clean": best, "missing": missing, "expected": sorted(expected)}, indent=2, sort_keys=True))
    else:
        print_table(best)
        print(f"\nclean cells: {len(best)}/{len(expected)}  (from {suite_dirs} suite dir(s) matching {args.suite!r}-*)")
        if missing:
            print(f"MISSING (no oom-free succeeded run): {', '.join(missing)}")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
