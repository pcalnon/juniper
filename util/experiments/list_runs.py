#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   experiments
# File Name:     list_runs.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Safety-gated lister / pruner for experiment RUN_DIRs (CLI experimentation plan §13.3, Wave 7.2).
#   v1 scans ${JUNIPER_EXP_RUN_ROOT} directly (the §13.3 index.jsonl registry arrives with Wave 7.1's
#   run_suite.py; when it lands, this tool remains the directory-truth fallback). Safety discipline
#   mirrors util/generated_prompt_index.py: destructive actions require explicit --yes, never act
#   under --dry-run, only touch torn-down convention-named runs, and never touch a run whose recorded
#   listener pid is still alive with its recorded cmdline.
#####################################################################################################################################################################################################
"""List / filter / prune experiment run directories.

Usage:
    python util/experiments/list_runs.py [--run-root P] [--json]
    python util/experiments/list_runs.py --older-than 7 [--state down]
    python util/experiments/list_runs.py --prune --older-than 7 --yes   # destructive, gated

A run directory is recognised by the launcher's ``<UTC yyyymmddThhmmssZ>-<4 hex>`` name
convention. State classification:

- ``down``  — ``teardown.json`` present (the launcher's teardown record).
- ``up?``   — no teardown record and at least one recorded pidfile whose pid is alive
  and still running the recorded cmdline (the F-6 discipline, read-only here).
- ``stale`` — no teardown record and no live recorded pid (crashed or reaped mid-run).

``--prune`` removes only ``down``/``stale`` runs matching ``--older-than`` — a run
classified ``up?`` is never pruned, even with ``--yes``. Exit 0 always except
misuse (2).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RUN_ID_RE = re.compile(r"^(\d{8}T\d{6}Z)-[0-9a-f]{4}$")

DEFAULT_RUN_ROOT = Path.home() / ".local" / "state" / "juniper-experiments"


def _parse_run_ts(run_id: str) -> "datetime | None":
    m = RUN_ID_RE.match(run_id)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _pid_alive_with_cmdline(pid: int, recorded_cmdline: str) -> bool:
    proc = Path(f"/proc/{pid}")
    if not proc.exists():
        return False
    try:
        current = (proc / "cmdline").read_bytes().decode().replace("\0", " ").strip()
    except OSError:
        return False
    return bool(recorded_cmdline) and current == recorded_cmdline.strip()


def classify(run_dir: Path) -> str:
    """``down`` / ``up?`` / ``stale`` per the module docstring."""
    if (run_dir / "teardown.json").exists():
        return "down"
    for pidfile in run_dir.glob("*.pid"):
        try:
            pid = int(pidfile.read_text().strip())
        except (OSError, ValueError):
            continue
        cmdline_file = pidfile.with_suffix(".cmdline")
        recorded = ""
        try:
            recorded = cmdline_file.read_text()
        except OSError:
            continue
        if _pid_alive_with_cmdline(pid, recorded):
            return "up?"
    return "stale"


def scan(run_root: Path) -> "list[dict]":
    rows: list[dict] = []
    if not run_root.is_dir():
        return rows
    for entry in sorted(run_root.iterdir()):
        if not entry.is_dir() or not RUN_ID_RE.match(entry.name):
            continue
        ts = _parse_run_ts(entry.name)
        experiment = None
        ports: dict = {}
        ports_file = entry / "ports.json"
        if ports_file.exists():
            try:
                pj = json.loads(ports_file.read_text())
                experiment = pj.get("experiment")
                ports = {k: pj[k] for k in ("data", "cascor", "recurrence") if pj.get(k) is not None}
            except (OSError, ValueError):
                pass
        cells = sorted(str(m.parent.relative_to(entry)) for m in entry.glob("*/manifest.json")) + sorted(str(m.parent.relative_to(entry)) for m in entry.glob("*/*/manifest.json"))
        rows.append(
            {
                "run_id": entry.name,
                "created_utc": ts.isoformat() if ts else None,
                "state": classify(entry),
                "experiment": experiment,
                "ports": ports,
                "cells": cells,
                "has_root_manifest": (entry / "manifest.json").exists(),
                "path": str(entry),
            }
        )
    return rows


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT, help=f"Experiment run root (default: {DEFAULT_RUN_ROOT})")
    parser.add_argument("--json", action="store_true", help="Emit the row list as JSON")
    parser.add_argument("--older-than", type=float, metavar="DAYS", default=None, help="Only rows whose run_id timestamp is older than DAYS days")
    parser.add_argument("--state", choices=("up", "down", "stale", "all"), default="all", help="Filter by state ('up' matches the tentative 'up?')")
    parser.add_argument("--prune", action="store_true", help="Remove matching run dirs (requires --yes; never under --dry-run; never 'up?' runs)")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive action")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — even with --yes, nothing is removed")
    args = parser.parse_args(argv)

    rows = scan(args.run_root)

    if args.older_than is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.older_than)
        rows = [r for r in rows if r["created_utc"] and datetime.fromisoformat(r["created_utc"]) < cutoff]
    if args.state != "all":
        want = "up?" if args.state == "up" else args.state
        rows = [r for r in rows if r["state"] == want]

    pruned: list[str] = []
    if args.prune:
        candidates = [r for r in rows if r["state"] in ("down", "stale")]
        skipped_live = [r for r in rows if r["state"] == "up?"]
        if args.dry_run or not args.yes:
            note = "--dry-run" if args.dry_run else "missing --yes"
            for r in candidates:
                print(f"WOULD PRUNE ({note}): {r['run_id']} [{r['state']}]")
        else:
            for r in candidates:
                shutil.rmtree(r["path"], ignore_errors=False)
                pruned.append(r["run_id"])
                print(f"PRUNED: {r['run_id']} [{r['state']}]")
        for r in skipped_live:
            print(f"SKIP (live recorded pid): {r['run_id']}")

    if args.json:
        print(json.dumps({"run_root": str(args.run_root), "runs": rows, "pruned": pruned}, indent=2))
    elif not args.prune:
        if not rows:
            print(f"No experiment runs under {args.run_root}")
        for r in rows:
            cells = f" cells={len(r['cells'])}" if r["cells"] else ""
            ports = ",".join(f"{k}:{v}" for k, v in r["ports"].items())
            print(f"{r['run_id']}  [{r['state']:5s}]  exp={r['experiment'] or '-':<16s} {ports}{cells}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
