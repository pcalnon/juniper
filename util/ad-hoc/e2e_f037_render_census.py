#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-3 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Multi-session render census for F-CANOPY-037 (topology graph starved
#          ABSENT). The finding measured the graph rendering in **2 of 11** live
#          sessions, so a fix for it CANNOT be validated by one session -- a
#          single green run was always ~18% likely even while broken. This driver
#          runs the seg17 ``topodiag`` step N times in N SEPARATE processes (each
#          gets its own browser, its own Dash session and its own renderer slot
#          pool) and tallies how many painted.
#
#          Each session's structured verdict is read from its own results file
#          via JUNIPER_E2E_SEG17_RESULTS -- not scraped from the log -- so the
#          census cannot silently mis-parse its way to a clean answer.
#
# Usage:
#   python3 util/ad-hoc/e2e_f037_render_census.py                    # 11 sessions
#   python3 util/ad-hoc/e2e_f037_render_census.py --sessions 5
#   python3 util/ad-hoc/e2e_f037_render_census.py --out reports/e2e/<run>/f037_census.json
#
# Exit codes: 0 census completed (read the tally -- it does NOT judge pass/fail),
#             2 a session crashed or produced no verdict.

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(_HERE, "e2e_seg17_topology_driver.py")

# The finding's own sample size. Matching it is what makes the before/after
# comparable at all: 2/11 vs 11/11 is a claim, 2/11 vs 1/1 is not.
DEFAULT_SESSIONS = 11


def run_session(index: int, python_exe: str, workdir: str, tmpdir: str, timeout_s: float) -> dict:
    """One fresh process -> one fresh browser -> one topodiag verdict."""
    results_path = os.path.join(tmpdir, f"session_{index:02d}.json")
    env = dict(os.environ)
    env["JUNIPER_E2E_SEG17_RESULTS"] = results_path
    # The JuniperCanopy1 activate hooks do not run for a direct binary
    # invocation, so strip the rust_mudgeon libtorch the same way they would.
    env["LIBTORCH"] = ""
    env["LD_LIBRARY_PATH"] = ""

    t0 = time.time()
    try:
        proc = subprocess.run(
            [python_exe, DRIVER, "--step", "topodiag"],
            cwd=workdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        rc, timed_out = proc.returncode, False
        tail = (proc.stdout or "")[-600:]
    except subprocess.TimeoutExpired:
        rc, timed_out, tail = None, True, "(timed out)"
    wall = round(time.time() - t0, 1)

    entry = {"session": index, "wall_s": wall, "returncode": rc, "timed_out": timed_out}
    try:
        with open(results_path, encoding="utf-8") as fh:
            entry.update(json.load(fh).get("topodiag") or {})
    except (OSError, ValueError):
        entry["verdict"] = None
        entry["tail"] = tail
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", type=int, default=DEFAULT_SESSIONS, help=f"independent sessions to run (default {DEFAULT_SESSIONS}, the finding's sample size)")
    ap.add_argument("--python", default=sys.executable, help="interpreter for the driver subprocess")
    ap.add_argument("--workdir", default=os.path.dirname(os.path.dirname(_HERE)), help="cwd for the driver (repo root)")
    ap.add_argument("--timeout", type=float, default=420.0, help="per-session wall timeout; topodiag's own paint budget is 240 s")
    ap.add_argument("--out", default=None, help="write the combined census JSON here")
    args = ap.parse_args()

    print(f"F-CANOPY-037 render census: {args.sessions} independent sessions", flush=True)
    print(f"  driver : {DRIVER}", flush=True)
    print("  baseline to beat: 2 of 11 painted (the finding)\n", flush=True)

    entries = []
    with tempfile.TemporaryDirectory(prefix="f037-census-") as tmpdir:
        for i in range(1, args.sessions + 1):
            e = run_session(i, args.python, args.workdir, tmpdir, args.timeout)
            entries.append(e)
            verdict = e.get("verdict") or "NO-VERDICT"
            counts = e.get("counts") or {}
            print(
                f"  session {i:2d}/{args.sessions}: {verdict:10s} "
                f"elapsed={e.get('elapsed_s')}s wall={e['wall_s']}s "
                f"counts={counts.get('input')}/{counts.get('hidden')}/{counts.get('output')}/{counts.get('conn')} "
                f"traces={e.get('traces')} sig={e.get('sig')}",
                flush=True,
            )

    painted = [e for e in entries if e.get("verdict") == "PASS"]
    absent = [e for e in entries if e.get("verdict") == "FAIL"]
    broken = [e for e in entries if e.get("verdict") not in ("PASS", "FAIL")]

    print(f"\n=== census: {len(painted)}/{len(entries)} painted ===", flush=True)
    if absent:
        print(f"  absent : {len(absent)} session(s) -> {[e['session'] for e in absent]}", flush=True)
    if broken:
        print(f"  BROKEN : {len(broken)} session(s) produced no verdict -> {[e['session'] for e in broken]}", flush=True)
    if painted:
        el = [e["elapsed_s"] for e in painted if isinstance(e.get("elapsed_s"), (int, float))]
        if el:
            print(f"  paint time: min={min(el)}s median={statistics.median(el)}s max={max(el)}s", flush=True)
        servers = {json.dumps(e.get("server"), sort_keys=True) for e in painted}
        print(f"  server truth seen: {len(servers)} distinct -> {list(servers)[:2]}", flush=True)

    summary = {
        "sessions": len(entries),
        "painted": len(painted),
        "absent": len(absent),
        "no_verdict": len(broken),
        "baseline": "2 of 11 (F-CANOPY-037 as found)",
        "entries": entries,
    }
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, default=str)
        print(f"  -> {args.out}", flush=True)

    # Deliberately does NOT return a pass/fail judgement on the render rate --
    # that is the operator's call against the row's own contract. A non-zero exit
    # means the CENSUS itself failed to measure, which is a different thing.
    return 2 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
