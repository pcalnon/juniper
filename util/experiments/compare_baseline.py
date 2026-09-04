#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   experiments
# File Name:     compare_baseline.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   The SPLIT comparator (perf-lane P2 item 1.2), implementing the rule decided in item 1.5 and
#   written up in §2.2 of notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md.
#
#   THE GATE HAS TWO HALVES WITH DIFFERENT CONTRACTS:
#     * WORK  -- step_count, compared EXACTLY. Deterministic for a seed-fixed config and
#                contention-immune (measured identical across 21 cells spanning a 3x range of step
#                duration), so a change in it is a statement about the CODE, never about the host.
#     * SPEED -- mean step duration, REPORTED and never gated. The host's own drift floor is
#                13-20.5%, larger than the effect of six competing CPU-bound processes, so a speed
#                threshold here would fire on an idle machine.
#
#   IDENTITY IS CHECKED FIRST, and a mismatch is a REFUSAL rather than a failure. A step_count
#   difference only means "the code regressed" when both sides ran the same workload; reporting an
#   ordinary config edit as a code regression is how a gate earns a reputation for lying and gets
#   switched off while still green.
#
#   EXIT CODES -- deliberately three, so a caller can tell the cases apart:
#       0  PASS or WAIVED
#       1  FAIL          -- same workload, work moved. The gate firing correctly.
#       2  REFUSED       -- cannot compare (identity, host, or an incoherent candidate), or usage.
#####################################################################################################################################################################################################
"""Compare a suite run against a named Q-8 baseline.

Usage:
    python util/experiments/compare_baseline.py --baseline pf1-2026-09-03 --suite SUITE_DIR
    python util/experiments/compare_baseline.py --baseline t --suite S --json
    python util/experiments/compare_baseline.py --baseline t --suite S --accept-work-change "cascor#618 raised the epoch budget"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments import make_baseline as mb  # noqa: E402  (path-invoked util import)
from experiments import read_run_metrics as rrm  # noqa: E402

PASS, FAIL, WAIVED, REFUSED = "PASS", "FAIL", "WAIVED", "REFUSED"
EXIT = {PASS: 0, WAIVED: 0, FAIL: 1, REFUSED: 2}

# The P1 design §2 condition for a valid run-tier comparison: "same YAML, same hardware, same
# thread budget". These are the HOST.json fields that encode the last two.
HOST_IDENTITY_FIELDS = ("cpu_model", "cpu_count", "thread_budget")

# Differences that change the SPEED number but not the WORK count. Reported, never a refusal --
# the gated half is unaffected, and refusing here would make a routine dependency bump un-comparable.
HOST_ADVISORY_VERSION_FIELDS = ("torch", "numpy", "python_runs")


class CompareError(Exception):
    """Usage or load failure -> exit 2."""


def _load_baseline(root: Path, tag: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    target = root / mb.BASELINES_DIRNAME / tag
    if not target.is_dir():
        raise CompareError(f"no baseline {tag!r} under {root / mb.BASELINES_DIRNAME}")
    payload = rrm._load_json(target / "baseline.json")
    host = rrm._load_json(target / "HOST.json")
    if not payload:
        raise CompareError(f"{target / 'baseline.json'} is missing or unreadable")
    return payload, host


def compare_host(baseline_host: Mapping[str, Any], candidate_host: Mapping[str, Any]) -> Dict[str, Any]:
    """Split host differences into blocking (identity) and advisory (versions)."""
    blocking = {
        field: {"baseline": baseline_host.get(field), "candidate": candidate_host.get(field)}
        for field in HOST_IDENTITY_FIELDS
        if baseline_host.get(field) != candidate_host.get(field)
    }
    base_versions = baseline_host.get("versions") or {}
    cand_versions = candidate_host.get("versions") or {}
    advisory = {
        field: {"baseline": base_versions.get(field), "candidate": cand_versions.get(field)}
        for field in HOST_ADVISORY_VERSION_FIELDS
        if base_versions.get(field) != cand_versions.get(field)
    }
    return {"match": not blocking, "blocking_differences": blocking, "advisory_differences": advisory}


def compare(
    baseline_payload: Mapping[str, Any],
    baseline_host: Mapping[str, Any],
    suite_dirs: Sequence[Path],
    *,
    accept_work_change: Optional[str] = None,
) -> Dict[str, Any]:
    """Produce the typed verdict. Never raises on a comparison outcome -- only on load failure."""
    reasons: List[str] = []
    scenario_results: List[Dict[str, Any]] = []
    by_fingerprint = {s.get("workload_fingerprint"): s for s in baseline_payload.get("scenarios", []) if s.get("workload_fingerprint")}

    candidate_manifests: List[Dict[str, Any]] = []
    for suite_dir in suite_dirs:
        rows = rrm.read_suite(suite_dir)
        if not rows:
            reasons.append(f"{Path(suite_dir).name}: no registry.jsonl or no cells")
            continue
        summary = rrm.summarise(rows)
        candidate_manifests.extend(rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rows)

        # An incoherent CANDIDATE cannot be compared to anything -- its own spread would not be a
        # property of the code. Refuse rather than pick a cell arbitrarily. Unknown identity and
        # unmeasured cells are checked on the ROWS, not on the summary's uniqueness flags: those
        # flags used to drop None before testing uniqueness, which would PASS a suite that mixed
        # one known/measured cell with one unknown/unmeasured cell.
        unknown = [str(r.get("cell_id") or r.get("run_id") or "?") for r in rows if not r.get("workload_fingerprint")]
        if unknown:
            reasons.append(
                f"{Path(suite_dir).name}: candidate identity unknown for cells {unknown} -- "
                f"cannot compare what cannot be identified"
            )
            continue
        unmeasured = [str(r.get("cell_id") or r.get("run_id") or "?") for r in rows if not isinstance(r.get("step_count"), (int, float))]
        if unmeasured:
            reasons.append(
                f"{Path(suite_dir).name}: no step-duration data for {unmeasured} -- "
                f"cannot compare an unmeasured run"
            )
            continue
        if not summary["single_workload"]:
            reasons.append(
                f"{Path(suite_dir).name}: candidate cells ran {len(summary['workload_fingerprints'])} different workloads "
                f"-- cannot compare"
            )
            continue
        if not summary["work_invariant"]:
            reasons.append(f"{Path(suite_dir).name}: candidate step_count is not invariant across cells ({[int(c) for c in summary['step_counts']]}) -- not a set of repeats")
            continue

        fingerprint = summary["workload_fingerprints"][0]
        matched = by_fingerprint.get(fingerprint)
        if matched is None:
            reasons.append(
                f"{Path(suite_dir).name}: workload {fingerprint[:12]}... is not in baseline "
                f"{baseline_payload.get('tag')!r} (which holds {[str(f)[:12] + '...' for f in by_fingerprint]}) -- "
                f"different workload, so this is an INVALID comparison rather than a regression"
            )
            continue

        base_count = (matched.get("work") or {}).get("step_count")
        cand_count = summary["step_counts"][0]
        base_speed = (matched.get("speed") or {}).get("mean")
        cand_speed = (summary.get("mean_step") or {}).get("mean")
        speed_delta = (100 * (cand_speed - base_speed) / base_speed) if base_speed and cand_speed else None

        scenario_results.append(
            {
                "suite": Path(suite_dir).name,
                "baseline_scenario": matched.get("suite"),
                "workload_fingerprint": fingerprint,
                "work": {"baseline": base_count, "candidate": cand_count, "match": base_count == cand_count},
                # Reported only. There is no threshold field here BY DESIGN -- adding one would
                # re-open the question item 1.5 closed.
                "speed": {
                    "baseline_mean_step_seconds": base_speed,
                    "candidate_mean_step_seconds": cand_speed,
                    "delta_pct": speed_delta,
                    "gated": False,
                },
            }
        )

    host = compare_host(baseline_host, mb.collect_host(candidate_manifests) if candidate_manifests else {})
    if not host["match"]:
        reasons.append(
            "host identity differs from the baseline (" + ", ".join(sorted(host["blocking_differences"])) + ") -- "
            "the run tier's regression definition requires the same hardware and thread budget, so this comparison "
            "would silently be cross-hardware"
        )

    # FAIL must not be swallowed by a sibling suite's REFUSED. `--suite` is repeatable and a
    # baseline holds one scenario per suite: work that moved on a comparable suite is still a
    # FAIL even if another suite could not be identified. Host mismatch stays a REFUSAL -- the
    # work delta cannot be attributed to the code. A clean PASS still requires every given
    # suite to have been compared (leftover reasons -> REFUSED, not a green overall).
    work_moved = bool(scenario_results) and not all(s["work"]["match"] for s in scenario_results)
    host_blocked = not host["match"]
    if work_moved and not host_blocked:
        verdict = WAIVED if accept_work_change else FAIL
    elif reasons or not scenario_results:
        verdict = REFUSED
        if not scenario_results and not reasons:
            reasons.append("no scenarios compared -- nothing to judge")
    else:
        verdict = PASS

    return {
        "verdict": verdict,
        "baseline_tag": baseline_payload.get("tag"),
        "reasons": reasons,
        "waiver": {"accepted": bool(accept_work_change), "reason": accept_work_change} if accept_work_change else None,
        "host": host,
        "scenarios": scenario_results,
    }


def render(result: Mapping[str, Any]) -> str:
    lines = [f"verdict: {result['verdict']}  (baseline {result['baseline_tag']!r})"]
    for scenario in result["scenarios"]:
        work = scenario["work"]
        mark = "OK  " if work["match"] else "MOVED"
        lines.append(f"  {scenario['suite']}")
        lines.append(f"    work  {mark} step_count baseline={work['baseline']} candidate={work['candidate']}")
        speed = scenario["speed"]
        delta = f"{speed['delta_pct']:+.2f}%" if speed["delta_pct"] is not None else "n/a"
        lines.append(f"    speed  (reported, NOT gated) mean step {delta}")
    advisory = result["host"].get("advisory_differences")
    if advisory:
        lines.append(f"  note: package/interpreter differences affect the reported SPEED only: {sorted(advisory)}")
    for reason in result["reasons"]:
        lines.append(f"  REFUSED: {reason}")
    if result.get("waiver"):
        # Only report the waiver as having DONE something when it actually did. Printing
        # "WAIVED by operator" under a REFUSED verdict reads as though the override took effect,
        # which is the opposite of what happened -- a waiver blesses a work change, never an
        # invalid comparison.
        if result["verdict"] == WAIVED:
            lines.append(f"  WAIVED by operator: {result['waiver']['reason']}")
        else:
            lines.append(f"  note: --accept-work-change was given but had NO effect (verdict {result['verdict']}); a waiver cannot override a refusal")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compare a suite run against a named Q-8 baseline.")
    parser.add_argument("--baseline", required=True, help="baseline tag")
    parser.add_argument("--suite", action="append", required=True, type=Path, help="candidate suite directory (repeatable)")
    parser.add_argument("--run-root", type=Path, default=mb.DEFAULT_RUN_ROOT, help=f"experiment state root (default {mb.DEFAULT_RUN_ROOT})")
    parser.add_argument(
        "--accept-work-change",
        metavar="REASON",
        help="bless a deliberate workload change; requires a REASON, yields WAIVED (never PASS), and records the reason. Prefer cutting a NEW BASELINE -- they supersede by name and are cheap.",
    )
    parser.add_argument("--json", action="store_true", help="emit the verdict as JSON")
    args = parser.parse_args(argv)

    if args.accept_work_change is not None and not args.accept_work_change.strip():
        print("compare_baseline: --accept-work-change requires a non-empty reason", file=sys.stderr)
        return EXIT[REFUSED]

    try:
        payload, host = _load_baseline(args.run_root, args.baseline)
    except CompareError as exc:
        print(f"compare_baseline: {exc}", file=sys.stderr)
        return EXIT[REFUSED]

    result = compare(payload, host, args.suite, accept_work_change=args.accept_work_change)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else render(result))
    return EXIT[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
