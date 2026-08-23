#!/usr/bin/env python3
"""Paired CLI-vs-service wall-clock ratio, with the interval that decides how many pairs are enough.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-21
Status:      ad-hoc -- one-off (residual CLI-vs-service wall gap, post-#533)
Retire when: the residual wall-gap evidence note is merged; delete then.
Related:     2026-08-21_h2h_paired_campaign.bash (produces what this reads);
             2026-08-20_determinism_nrun.py (whose parser this REUSES -- see below).

THE STATISTIC: RATIO-OF-PAIRS, NOT RATIO-OF-MEANS
Each pair's two legs run adjacent in time, so they see nearly the same host. Forming the ratio
INSIDE a pair and then averaging those ratios cancels that shared condition; averaging each arm
first and dividing at the end does not, and it lets a single slow leg move the headline. This is
the same reason the wide-budget campaign reported a paired delta rather than two independent
means.

Both are printed, deliberately. When they disagree, the disagreement IS the finding: it means the
pairs were not experiencing comparable conditions and the campaign needs re-running rather than
re-interpreting.

WHY IT ALSO PRINTS A REQUIRED-K
The predecessor arc's whole failure mode was quoting a ratio from one run per arm. So this reports
the pairwise sd and, from it, the number of pairs needed for a 95% half-width narrower than the
effect being claimed -- i.e. enough to distinguish the measured ratio from 1.0, and enough to
resolve a stated target precision. If the campaign already has that many pairs it says so; if not
it says how many more.

PARSER REUSE
The per-run parse (span, candidate phase, output phase, candidate epochs) is imported from
2026-08-20_determinism_nrun.py rather than re-implemented. Those marker regexes are anchored on
message TEXT precisely because line-number anchors went stale once already
(2026-08-16_h2h_phase_split.py, silently, after juniper-cascor#539); keeping ONE copy means a
future re-anchor cannot fix one reader and leave this one quietly wrong.

Usage: python util/ad-hoc/2026-08-21_h2h_paired_ratio.py <CAMPAIGN_OUT_ROOT> [--target-precision 0.05]
Exit:  0 on a report; 2 if fewer than one complete pair was found.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_det_nrun", _HERE / "2026-08-20_determinism_nrun.py")
_det = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_det)
parse_run = _det.parse_run


def service_dirs(out_root: Path) -> "list[Path]":
    """Service run dirs, in pair order, from the campaign's own leg record."""
    legs = out_root / "legs.jsonl"
    dirs: "list[Path]" = []
    if not legs.exists():
        return dirs
    for line in legs.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("arm") != "service":
            continue
        reg = Path(row["suite_dir"]) / "registry.jsonl"
        if not reg.exists():
            continue
        for entry in reg.read_text().splitlines():
            if entry.strip():
                cell = json.loads(entry)
                if cell.get("run_dir"):
                    dirs.append(Path(cell["run_dir"]))
    return dirs


def _ratio_stats(values: "list[float]") -> dict:
    vals = [v for v in values if v is not None and math.isfinite(v)]
    if not vals:
        return {"n": 0}
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else None
    # 95% interval on the MEAN ratio, t-ish via 1.96 (the pair counts here are small enough that
    # this is optimistic; it is reported as an indication, and required-k below is what matters).
    half = 1.96 * sd / math.sqrt(len(vals)) if sd is not None and len(vals) > 1 else None
    return {"n": len(vals), "mean": mean, "sd": sd, "half_width": half,
            "lo": mean - half if half is not None else None,
            "hi": mean + half if half is not None else None,
            "cv": (sd / mean) if sd is not None and mean else None}


def required_k(sd: "float | None", mean: "float | None", target_abs: float) -> "int | None":
    """Pairs needed for a 95% half-width <= target_abs on the mean ratio."""
    if sd is None or not sd or mean is None:
        return None
    return max(2, math.ceil((1.96 * sd / target_abs) ** 2))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_root", type=Path)
    ap.add_argument("--target-precision", type=float, default=0.05,
                    help="desired 95%% half-width on the mean ratio, in ratio units (default 0.05)")
    args = ap.parse_args()

    svc = service_dirs(args.out_root)
    cli = sorted(p for p in args.out_root.glob("cli-*") if (p / "logs").is_dir())
    n = min(len(svc), len(cli))
    if n < 1:
        print(f"paired-ratio: no complete pair under {args.out_root} "
              f"(service={len(svc)}, cli={len(cli)})", file=sys.stderr)
        return 2
    if len(svc) != len(cli):
        # Name the imbalance rather than silently truncating -- a campaign that died mid-pair
        # should not read as a clean k-pair result.
        print(f"NOTE: unequal arms (service={len(svc)}, cli={len(cli)}); using the first {n} pairs")

    rows = []
    for i in range(n):
        s, c = parse_run(svc[i]), parse_run(cli[i])
        row = {"pair": i + 1, "svc": s, "cli": c}
        for key in ("span_s", "cand_total_s", "out_total_s", "cand_epochs", "s_per_cand_epoch"):
            sv, cv = s.get(key), c.get(key)
            row[key] = (cv / sv) if (sv and cv) else None
        rows.append(row)

    print(f"{'pair':>4}  {'svc_span':>9} {'cli_span':>9} {'span×':>7}  "
          f"{'svc_cand':>9} {'cli_cand':>9} {'cand×':>7}  "
          f"{'svc_ep':>8} {'cli_ep':>8} {'work×':>7}  {'rate×':>7}")
    print("-" * 108)
    for r in rows:
        s, c = r["svc"], r["cli"]
        print(f"{r['pair']:>4}  {s['span_s'] or 0:>9.0f} {c['span_s'] or 0:>9.0f} "
              f"{r['span_s'] or 0:>7.3f}  {s['cand_total_s'] or 0:>9.0f} {c['cand_total_s'] or 0:>9.0f} "
              f"{r['cand_total_s'] or 0:>7.3f}  {s['cand_epochs']:>8} {c['cand_epochs']:>8} "
              f"{r['cand_epochs'] or 0:>7.3f}  {r['s_per_cand_epoch'] or 0:>7.3f}")

    print(f"\n=== paired ratios (CLI / service), {n} pairs ===")
    summary = {}
    for key, label in (("span_s", "training span"), ("cand_total_s", "candidate phase"),
                       ("out_total_s", "output phase"), ("cand_epochs", "candidate work (epochs)"),
                       ("s_per_cand_epoch", "per-candidate-epoch rate")):
        st = _ratio_stats([r[key] for r in rows])
        summary[key] = st
        if not st["n"]:
            print(f"  {label:<26}: n/a")
            continue
        sd_txt = f" ± {st['sd']:.3f}" if st["sd"] is not None else ""
        ci_txt = f"   95% CI [{st['lo']:.3f}, {st['hi']:.3f}]" if st["lo"] is not None else ""
        print(f"  {label:<26}: {st['mean']:.3f}{sd_txt}{ci_txt}  [n={st['n']}]")

    # Ratio-of-means, as the cross-check described in the docstring.
    print("\n=== cross-check: ratio of means (should agree with the paired figure) ===")
    for key, label in (("span_s", "training span"), ("cand_total_s", "candidate phase")):
        sv = [r["svc"][key] for r in rows if r["svc"][key]]
        cv = [r["cli"][key] for r in rows if r["cli"][key]]
        if sv and cv:
            rom = statistics.mean(cv) / statistics.mean(sv)
            paired = summary[key].get("mean")
            flag = ""
            if paired and abs(rom - paired) / paired > 0.02:
                flag = "   <-- DISAGREES with the paired figure by >2%: the pairs did not see comparable hosts"
            print(f"  {label:<26}: {rom:.3f}{flag}")

    print(f"\n=== how many pairs are enough? (target 95% half-width ≤ {args.target_precision:g}) ===")
    for key, label in (("span_s", "training span"), ("cand_total_s", "candidate phase"),
                       ("s_per_cand_epoch", "per-candidate-epoch rate")):
        st = summary[key]
        need = required_k(st.get("sd"), st.get("mean"), args.target_precision)
        if need is None:
            print(f"  {label:<26}: sd unavailable (need ≥2 pairs)")
            continue
        have = st["n"]
        verdict = "SUFFICIENT" if have >= need else f"need {need - have} more"
        print(f"  {label:<26}: k={need:<4} (have {have}) — {verdict}")
    print("\n  Effect size matters as much as precision: a ratio whose interval excludes 1.000 is\n"
          "  established as a real gap even when the half-width is wide.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
