"""Aggregate the E-A re-surface grid, keeping only GPU-clean cells.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-10
Status: ad-hoc -- one-off
Retire when: the F-P4-1 re-surface evidence note is written; delete with the campaign scripts.
Related: F-P4-1 re-surface; the cascor GPU-leak trap.

The re-surfaced grid was collected across several suite runs (the leak forced per-cell
reaping, which produces one suite dir per cell). A cell is only usable if its cascor log
recorded ZERO ``out of memory`` lines -- a contaminated cell either collapses to the
1-unit / no_candidate signature or, more insidiously, just reports depressed accuracy
(c010: val 0.585 with 202 OOM vs 0.645 clean). So this walks every E-A suite dir, keeps
the newest oom==0 succeeded row per cell_id, and reports anything still missing.
"""

import json
import re
import sys
from pathlib import Path

SUITES = Path("/home/pcalnon/.local/state/juniper-experiments/suites")


def field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else "?"


def main() -> int:
    best: dict[str, dict] = {}
    for suite_dir in sorted(SUITES.glob("e-a-cascor-budget-sweep-*")):
        registry = suite_dir / "registry.jsonl"
        if not registry.is_file():
            continue
        for line in registry.read_text().splitlines():
            row = json.loads(line)
            run_dir = Path(row["run_dir"])
            log = run_dir / "logs/juniper-cascor.log"
            oom = log.read_text(errors="ignore").count("out of memory") if log.is_file() else -1
            if row["outcome"] != "succeeded" or oom != 0:
                continue
            summary = run_dir / "artifacts/results/summary.md"
            text = summary.read_text() if summary.is_file() else ""
            over = row["overrides"]
            # Later suite dirs sort last, so a plain overwrite keeps the newest clean run.
            best[row["cell_id"][:4]] = {
                "pool": over.get("training.params.candidate_pool_size"),
                "cap": over.get("training.params.max_hidden_units"),
                "epochs": over.get("training.params.max_epochs"),
                "units": field(text, r"hidden_units: (\S+)"),
                "train": field(text, r"train_accuracy: (\S+)"),
                "val": field(text, r"val_accuracy: (\S+)"),
                "reason": field(text, r"completion reason: (\S+)"),
                "wall": row["wall_seconds"],
                "corr": max(re.findall(r"hidden_units=\d+: best (\S+)", text) or ["-"]),
            }

    print(f"{'cell':<5}{'pool':>5}{'cap':>5}{'units':>7}{'train':>8}{'val':>8}{'wall_s':>8}  {'completion':<15}best_corr")
    for cell in sorted(best):
        r = best[cell]
        cap = r["cap"] if r["cap"] is not None else f"({r['epochs']}ep)"
        print(f"{cell:<5}{str(r['pool']):>5}{str(cap):>5}{r['units']:>7}{r['train'][:6]:>8}{r['val'][:6]:>8}{r['wall']:>8.0f}  {r['reason']:<15}{r['corr']}")

    expected = {f"c{i:03d}" for i in range(12)}
    missing = sorted(expected - set(best))
    print(f"\nclean cells: {len(best)}/12")
    if missing:
        print(f"MISSING (no oom-free succeeded run): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
