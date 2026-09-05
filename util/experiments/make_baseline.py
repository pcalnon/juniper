#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   experiments
# File Name:     make_baseline.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Writes the Q-8 run-level baseline directory (perf-lane P2 item 1.1), implementing §4 of
#   notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md.
#
#   OPERATOR-INVOKED ONLY. Blessing a measurement is a deliberate act; a run that promotes itself
#   to baseline can launder a bad number into the reference. Nothing here is ever called from
#   run_suite.py or run_experiment.py, and there is no "auto" mode.
#
#   LAYOUT (§4):
#       baselines/<tag>/
#           baseline.json           per-scenario summary statistics
#           manifests/<run_id>.json the constituent run manifests, copied VERBATIM
#           HOST.json               hardware + thread budget + package versions at capture time
#
#   HOST.json IS LOAD-BEARING, NOT METADATA. The run tier's regression definition is "same YAML,
#   same hardware, same thread budget". Without a recorded fingerprint the FIRST condition a
#   comparison must check cannot be checked, and the comparison silently becomes cross-hardware.
#
#   RETENTION: baselines are NEVER auto-deleted, and a superseded tag is superseded BY NAME. There
#   is deliberately no --force: overwriting a tag in place is the one operation the retention policy
#   forbids, so it is absent rather than merely discouraged. Want a different baseline? New tag.
#####################################################################################################################################################################################################
"""Bless a set of suite runs as a named run-level baseline.

Usage:
    python util/experiments/make_baseline.py --tag pf1-2026-09-03 --suite SUITE_DIR
    python util/experiments/make_baseline.py --tag t --suite A --suite B --dry-run
"""

from __future__ import annotations

import argparse
import importlib.metadata as importlib_metadata
import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments import read_run_metrics as rrm  # noqa: E402  (path-invoked util import)

DEFAULT_RUN_ROOT = Path.home() / ".local/state/juniper-experiments"
BASELINES_DIRNAME = "baselines"


class BaselineError(Exception):
    """Refusal to write a baseline -> exit 2."""


def _cpu_model() -> Optional[str]:
    """CPU model from procfs, or ``None`` where procfs is absent (macOS, a container, Windows).

    Swallowing OSError is deliberate and is NOT an error path: ``None`` is a truthful answer that
    HOST.json records as such. Raising would make a baseline un-writable on a host whose CPU model
    simply cannot be read, and the fingerprint's other fields still carry real information.
    """
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        return None  # no procfs -> "unknown", recorded honestly rather than raised
    return None


def _total_ram_kb() -> Optional[int]:
    """Total RAM in kB from procfs, or ``None``.

    Same contract as ``_cpu_model``: a missing or malformed ``MemTotal`` is recorded as unknown.
    ValueError/IndexError cover a procfs whose format is not the expected ``MemTotal: <n> kB``.
    """
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None  # unreadable or unexpected format -> "unknown", not a failure
    return None


def _gpu_present() -> bool:
    """Cheap presence probe. Deliberately does NOT import torch -- that costs seconds."""
    return Path("/proc/driver/nvidia/version").exists() or shutil.which("nvidia-smi") is not None


def _dist_version(name: str) -> Optional[str]:
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def collect_host(manifests: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Build HOST.json from the runs plus this host, flagging any fidelity gap.

    torch/numpy versions come from THIS interpreter, because the run manifests record only
    ``juniper-*`` packages. That is only trustworthy when the tool runs under the same interpreter
    as the runs did, so the check is performed and recorded rather than assumed -- a HOST.json
    carrying a plausible but wrong torch version is worse than one that says it could not tell.
    """
    run_pythons = sorted({(m.get("environment") or {}).get("python") for m in manifests if (m.get("environment") or {}).get("python")})
    tool_python = platform.python_version()
    thread_envs = [(m.get("environment") or {}).get("thread_env") for m in manifests]
    nprocs = sorted({(m.get("environment") or {}).get("nproc") for m in manifests if (m.get("environment") or {}).get("nproc")})

    host: Dict[str, Any] = {
        "cpu_model": _cpu_model(),
        "cpu_count": nprocs[0] if len(nprocs) == 1 else nprocs,
        "total_ram_kb": _total_ram_kb(),
        "gpu_present": _gpu_present(),
        "platform": sorted({(m.get("environment") or {}).get("platform") for m in manifests if (m.get("environment") or {}).get("platform")}),
        "thread_budget": thread_envs[0] if thread_envs and all(t == thread_envs[0] for t in thread_envs) else thread_envs,
        "versions": {
            "python_tool": tool_python,
            "python_runs": run_pythons,
            "torch": _dist_version("torch"),
            "numpy": _dist_version("numpy"),
        },
    }
    if run_pythons and run_pythons != [tool_python]:
        host["versions"]["caveat"] = (
            f"torch/numpy were read from THIS interpreter ({tool_python}), but the runs used "
            f"{run_pythons}. Treat those two versions as unverified for these runs."
        )
    if len(nprocs) > 1:
        host["caveat_cpu_count"] = f"runs report differing nproc {nprocs} -- these are not the same hardware condition"
    return host


def _load_manifest(run_dir: Path) -> Dict[str, Any]:
    path = run_dir / "manifest.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"cannot read manifest {path}: {exc}") from exc


def build_baseline(tag: str, suite_dirs: Sequence[Path], *, accept_warnings: bool = False) -> Dict[str, Any]:
    """Assemble the baseline payload, refusing anything that would bless a bad measurement."""
    scenarios: List[Dict[str, Any]] = []
    manifests: Dict[str, Dict[str, Any]] = {}
    refusals: List[str] = []

    for suite_dir in suite_dirs:
        rows = rrm.read_suite(suite_dir)
        if not rows:
            refusals.append(f"{suite_dir}: no registry.jsonl or no cells")
            continue
        summary = rrm.summarise(rows)

        failed = [r["run_id"] for r in rows if r.get("outcome") != "succeeded"]
        if failed:
            refusals.append(f"{suite_dir.name}: cells did not succeed: {failed}")
        # A baseline exists to support the WORK gate. Recurrence exposes no work-done counter
        # (surveyed 2026-09-04: n_epochs is 1-or-200 by readout type and invariant to d/n_steps;
        # n_windows is input size), so a "baseline" cut from one could only ever back a SPEED
        # comparison -- and this host's 13-20.5% drift floor is precisely why speed is not gated.
        # Blessing one would invite exactly the comparison the lane has ruled out.
        if summary.get("truncated_terminations"):
            refusals.append(
                f"{suite_dir.name}: cells ended on {summary['truncated_terminations']} -- the driver stopped before "
                f"the workload did, so step_count is a fact about the budget. A baseline must not enshrine one."
            )
        if not summary.get("single_completion_reason"):
            refusals.append(
                f"{suite_dir.name}: completion_reason is not a single known branch "
                f"(seen {summary.get('completion_reasons')}, cells={summary.get('cells')}) -- step_count is "
                f"deterministic only within a branch, so these are not repeats and their agreement would be luck."
            )
        if not summary.get("work_countable", True):
            reason = next((r.get("work_uncountable_reason") for r in rows if r.get("work_uncountable_reason")), "no work counter")
            refusals.append(
                f"{suite_dir.name}: runs of kind {summary.get('kinds')} expose no countable work -- {reason}. "
                f"A baseline supports the WORK gate; a speed-only reference would invite the comparison the "
                f"13-20.5% drift floor rules out. Report these runs instead of baselining them."
            )
        # A suite of repeats whose work amount MOVED is not a set of repeats, and a baseline cut
        # from it fixes a work count that was never stable. This is the split gate's own premise.
        if not summary["work_invariant"]:
            refusals.append(f"{suite_dir.name}: step_count is NOT invariant across cells ({[int(c) for c in summary['step_counts']]}) -- these are not repeats")
        # Distinct from the work invariant: cells that ran DIFFERENT workloads would give a
        # step_count spread that is a fact about the configs, not about the host or the code.
        if not summary["single_workload"]:
            refusals.append(
                f"{suite_dir.name}: cells ran {len(summary['workload_fingerprints'])} different workloads "
                f"(fingerprints {[f[:12] for f in summary['workload_fingerprints']]}) -- a baseline scenario must be ONE workload"
            )
        missing = [r["run_id"] for r in rows if r.get("step_count") is None]
        if missing:
            refusals.append(f"{suite_dir.name}: no step-duration data for {missing} -- cannot baseline an unmeasured run")

        warned = {}
        for row in rows:
            manifest = _load_manifest(Path(row["run_dir"]))
            manifests[str(row["run_id"])] = manifest
            notes = manifest.get("validation_warnings") or []
            if notes:
                warned[str(row["run_id"])] = notes
        if warned and not accept_warnings:
            refusals.append(
                f"{suite_dir.name}: {len(warned)} run(s) carry validation_warnings -- re-run clean, or "
                f"pass --accept-warnings to record the acceptance in baseline.json. First: {next(iter(warned.values()))[0][:120]}"
            )

        scenarios.append(
            {
                "suite_dir": str(suite_dir),
                "suite": Path(suite_dir).name,
                "cells": summary["cells"],
                "run_ids": [r["run_id"] for r in rows],
                "overrides": rows[0].get("overrides"),
                # The comparator's FIRST check (P2 item 1.5): a differing fingerprint means the
                # comparison is INVALID, not that the code regressed. Recorded here so a later
                # comparison can tell those apart instead of blaming the code for a config edit.
                "workload_fingerprint": summary["workload_fingerprints"][0] if summary["single_workload"] else None,
                # `completion_reason` is recorded WITH the count because the count is only
                # meaningful given it (see compare_baseline's precondition).
                "work": {
                    "step_count": summary["step_counts"][0] if summary["work_invariant"] else None,
                    "invariant": summary["work_invariant"],
                    "completion_reason": summary["completion_reasons"][0] if summary["single_completion_reason"] else None,
                },
                "speed": summary.get("mean_step"),
                "drive": summary.get("drive"),
                "step_sum": summary.get("step_sum"),
                "validation_warnings": warned,
            }
        )

    if refusals:
        raise BaselineError("refusing to write a baseline:\n  - " + "\n  - ".join(refusals))
    if not scenarios:
        raise BaselineError("no scenarios collected -- nothing to bless")

    return {
        "schema": 1,
        "tag": tag,
        "created_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "accepted_warnings": accept_warnings,
        "scenarios": scenarios,
        "metric_contract": {
            "work": "step_count -- gated EXACTLY; deterministic for a seed-fixed config and contention-immune",
            "speed": "mean_step_seconds -- REPORTED, never gated; carries a 13-20.5% host drift floor",
            "de_ratified": "timings.drive and wall_seconds; drive is quantized to the 5 s poll interval",
        },
    }


def write_baseline(root: Path, tag: str, payload: Dict[str, Any], manifests: Dict[str, Dict[str, Any]], host: Dict[str, Any]) -> Path:
    """Create ``<root>/baselines/<tag>/``. Refuses to overwrite -- supersede by NAME."""
    target = root / BASELINES_DIRNAME / tag
    if target.exists():
        raise BaselineError(
            f"{target} already exists. Baselines are never overwritten or auto-deleted -- a superseded "
            f"baseline is superseded BY NAME (§4 of the P1 design). Choose a new tag."
        )
    (target / "manifests").mkdir(parents=True)
    (target / "baseline.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (target / "HOST.json").write_text(json.dumps(host, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for run_id, manifest in manifests.items():
        (target / "manifests" / f"{run_id}.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Bless suite runs as a named Q-8 run-level baseline.")
    parser.add_argument("--tag", required=True, help="operator-chosen baseline name, e.g. pf1-2026-09-03")
    parser.add_argument("--suite", action="append", required=True, type=Path, help="suite directory (repeatable)")
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT, help=f"experiment state root (default {DEFAULT_RUN_ROOT})")
    parser.add_argument("--accept-warnings", action="store_true", help="bless runs carrying validation_warnings; the acceptance is recorded in baseline.json")
    parser.add_argument("--dry-run", action="store_true", help="validate and print, write nothing")
    args = parser.parse_args(argv)

    if "/" in args.tag or args.tag.startswith("."):
        print(f"make_baseline: invalid tag {args.tag!r} -- must be a single path segment", file=sys.stderr)
        return 2

    try:
        payload = build_baseline(args.tag, args.suite, accept_warnings=args.accept_warnings)
        manifests = {}
        for scenario in payload["scenarios"]:
            for row in rrm.read_suite(Path(scenario["suite_dir"])):
                manifests[str(row["run_id"])] = _load_manifest(Path(row["run_dir"]))
        host = collect_host(list(manifests.values()))
        if args.dry_run:
            print(json.dumps({"baseline": payload, "HOST": host}, indent=2, sort_keys=True))
            print(f"\n[dry-run] would write {args.run_root / BASELINES_DIRNAME / args.tag} ({len(manifests)} manifests)", file=sys.stderr)
            return 0
        target = write_baseline(args.run_root, args.tag, payload, manifests, host)
    except BaselineError as exc:
        print(f"make_baseline: {exc}", file=sys.stderr)
        return 2

    print(f"wrote {target}")
    print(f"  baseline.json  {len(payload['scenarios'])} scenario(s)")
    print(f"  manifests/     {len(manifests)} run manifest(s)")
    print(f"  HOST.json      cpu={host.get('cpu_count')} torch={host['versions'].get('torch')} numpy={host['versions'].get('numpy')}")
    if host["versions"].get("caveat"):
        print(f"  CAVEAT: {host['versions']['caveat']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
