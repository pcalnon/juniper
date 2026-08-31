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


def _find_juniper_root(start: str = None) -> str:
    """Walk UP from this script until we find the dir holding the sibling repos.

    Must not be computed as a fixed number of ``dirname`` hops. This tool is
    routinely run from a git worktree nested INSIDE the repo
    (``juniper-ml/.claude/worktrees/<name>/util/ad-hoc``), where the old
    three-hop form landed on ``worktrees/`` and every sibling-repo lookup missed.
    Measured 2026-08-31: the first census to carry provenance recorded
    ``sha=None`` for canopy -- the single field the block exists to capture.

    Identified by containing BOTH juniper-canopy and juniper-cascor, so a
    partial match cannot satisfy it. Falls back to the three-hop guess only if
    the walk finds nothing, so behaviour never gets worse than before.
    """
    here = start or _HERE
    cur = here
    for _ in range(12):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
        if os.path.isdir(os.path.join(cur, "juniper-canopy")) and os.path.isdir(os.path.join(cur, "juniper-cascor")):
            return cur
    return os.path.dirname(os.path.dirname(os.path.dirname(here)))


def _repo_provenance(path: str) -> dict:
    """HEAD sha + dirty flag for one repo, or an explicit reason it is unknown.

    No census in this arc ever recorded which build it measured, so the
    provenance of the two results that shaped it (0-of-6 and 0-of-2) had to be
    reconstructed from leg logs a sweep had nearly destroyed, and one of them
    could not be tied to a build at all. Recording four cheap fields here is the
    whole fix.
    """
    if not os.path.isdir(path):
        return {"path": path, "sha": None, "unknown_because": "path does not exist"}
    try:
        sha = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=15)
        if sha.returncode != 0:
            return {"path": path, "sha": None, "unknown_because": (sha.stderr or "").strip()[:200]}
        porcelain = subprocess.run(["git", "-C", path, "status", "--porcelain"], capture_output=True, text=True, timeout=30)
        branch = subprocess.run(["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=15)
        return {
            "path": path,
            "sha": sha.stdout.strip(),
            "branch": branch.stdout.strip() or None,
            # NB `git status --porcelain` is blind to ignored files; it answers
            # "are there uncommitted TRACKED changes", which is what identifies
            # the build under test.
            "dirty": bool(porcelain.stdout.strip()),
        }
    except (subprocess.SubprocessError, OSError) as exc:
        return {"path": path, "sha": None, "unknown_because": f"{type(exc).__name__}: {exc}"}


def _topology_conditions(entries: list) -> dict:
    """What did this census actually put the panel through?

    Two INDEPENDENT questions, and conflating them produced a wrong claim once
    already (recorded here so it is not repeated):

    ``populated`` -- did the server ever offer a non-trivial topology? If every
    session saw ``hidden_units == 0`` there was nothing to draw, so a FAIL means
    "nothing to paint", not "failed to paint". **This is the real vacuity: the
    census tested nothing.** A census that is not populated cannot be read at
    all, in either direction.

    ``varied`` -- did the cascade GROW mid-census? This does NOT decide whether
    the census is valid. An idle (populated, non-varying) census is a perfectly
    good test of F-CANOPY-039's core question, because after the identity
    suppression there is exactly ONE populated rebuild -- the mount-time fetch,
    where the 7,059 B payload differs from the 75 B store default -- and whether
    the graph paints is precisely whether that one response was applied. It
    discriminates supersession from a contention-independent apply failure.

    What an idle census does NOT cover is the growth-dependent rows
    (M-TOPOLOGY-16's cascade-add glow and friends) and the residual per-change
    race: a server-side ``no_update`` does not save a renderer slot, so the 5 s
    bare tick is still a real invocation against the same 8 outputs and can
    retire an in-flight rebuild. At idle that races one rebuild; during growth
    it races every one of them.

    So: ``populated`` false invalidates the run. ``varied`` false merely bounds
    what may be concluded from it.
    """
    seen = []
    for e in entries:
        server = e.get("server")
        if isinstance(server, dict):
            hidden = server.get("hidden_units", server.get("hidden"))
            if hidden is not None:
                seen.append(str(hidden))

    distinct = sorted(set(seen))
    nonzero = [h for h in distinct if h not in ("0", "None", "")]
    populated = bool(nonzero)

    if not populated:
        note = (
            "INVALID: the server never offered a non-trivial topology (hidden_units was 0 or absent in "
            "every session). There was nothing to draw, so neither PASS nor FAIL can be read from this "
            "run. Train a network before censusing."
        )
    elif len(distinct) <= 1:
        note = (
            "VALID, IDLE SCOPE. The topology was populated but never changed, so this run does test "
            "F-CANOPY-039's core question (was the single populated rebuild's response applied?) but "
            "does NOT cover the growth-dependent rows or the per-change bare-tick race. Do not "
            "generalise a PASS here to 'the panel tracks a live cascade'."
        )
    else:
        note = (
            "VALID, GROWTH SCOPE -- distinct topologies were observed ACROSS sessions, so the rebuild "
            "was exercised against more than the one it saw at mount. NOTE the limit of this check: it "
            "compares the value each session OBSERVED, so it cannot distinguish 'the cascade grew while "
            "a session watched' from 'consecutive sessions saw different static topologies'. For the "
            "stronger claim -- painting while units are actively being added -- read the per-session "
            "elapsed_s and trace counts, where a mid-growth paint shows up as a longer elapsed and a "
            "trace count above the static signature for that unit count."
        )

    return {
        "hidden_units_observed": distinct,
        "populated": populated,
        "varied": len(distinct) > 1,
        "scope": "invalid" if not populated else ("idle" if len(distinct) <= 1 else "growth"),
        "note": note,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", type=int, default=DEFAULT_SESSIONS, help=f"independent sessions to run (default {DEFAULT_SESSIONS}, the finding's sample size)")
    ap.add_argument("--python", default=sys.executable, help="interpreter for the driver subprocess")
    ap.add_argument("--workdir", default=os.path.dirname(os.path.dirname(_HERE)), help="cwd for the driver (repo root)")
    ap.add_argument("--timeout", type=float, default=420.0, help="per-session wall timeout; topodiag's own paint budget is 240 s")
    ap.add_argument("--out", default=None, help="write the combined census JSON here")
    ap.add_argument("--canopy-src", default=None, help="canopy checkout the stack under test runs from (default: $CANOPY_SRC_DIR, else the primary)")
    ap.add_argument("--cascor-src", default=None, help="cascor checkout the stack under test runs from (default: $CASCOR_SRC_DIR, else the primary)")
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

    juniper_root = _find_juniper_root()
    # Record the source the STACK ran from, not a hardcoded primary. The stack
    # takes CANOPY_SRC_DIR / CASCOR_SRC_DIR, so a fix under test usually lives in
    # a worktree while the primary sits on main -- recording the primary's sha
    # would be an authoritative-looking wrong answer, which is worse than none.
    canopy_src = args.canopy_src or os.environ.get("CANOPY_SRC_DIR") or os.path.join(juniper_root, "juniper-canopy")
    cascor_src = args.cascor_src or os.environ.get("CASCOR_SRC_DIR") or os.path.join(juniper_root, "juniper-cascor")
    provenance = {
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "canopy_src_resolved_from": (
            "--canopy-src" if args.canopy_src else ("CANOPY_SRC_DIR" if os.environ.get("CANOPY_SRC_DIR") else "default primary checkout")
        ),
        "juniper_canopy": _repo_provenance(canopy_src),
        "juniper_cascor": _repo_provenance(cascor_src),
        "juniper_ml": _repo_provenance(os.path.dirname(os.path.dirname(_HERE))),
    }
    conditions = _topology_conditions(entries)

    print(f"\n  build under test: canopy {provenance['juniper_canopy'].get('sha')} "
          f"(dirty={provenance['juniper_canopy'].get('dirty')})", flush=True)
    print(f"  conditions: scope={conditions['scope']} populated={conditions['populated']} "
          f"varied={conditions['varied']} hidden_units_seen={conditions['hidden_units_observed']}", flush=True)
    if conditions["scope"] != "growth":
        print(f"  !! {conditions['note']}", flush=True)

    summary = {
        "sessions": len(entries),
        "painted": len(painted),
        "absent": len(absent),
        "no_verdict": len(broken),
        "baseline": "2 of 11 (F-CANOPY-037 as found)",
        "provenance": provenance,
        "topology_conditions": conditions,
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
