#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Canopy E2E arc -- M-TOPOLOGY-16 (cascade-add glow) (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Decide whether M-TOPOLOGY-16 is FIXABLE or BLOCKED, by measuring the
#          only two things that determine it, from inside the callback:
#
#            1. does ``metrics_data`` actually REACH update_network_graph?
#            2. given what it receives, does the detector ARM the highlight?
#
#          The distinction matters because the named fix (replace the last-pair
#          check at network_visualizer.py:512-517 with a whole-window scan) is
#          UNOBSERVABLE if (1) is empty -- ``newly_added_unit`` is None either
#          way, the glow never fires, and a census of the row would show no
#          improvement, inviting the wrong conclusion that the scan failed.
#
#          Reading the source cannot settle (1): ``metrics-panel-metrics-store``
#          has TWO writers (dashboard_manager.py:3878 guarded poll, :3910
#          unguarded allow_duplicate WS append), so whether the CLIENT copy is
#          populated depends on which path ran. It is a measurement question.
#
#          Measures the callback's OWN ARGUMENT rather than the store, which is
#          what broke F-CANOPY-039 open: every browser-side probe in this arc has
#          been unreliable or ambiguous, and a store reading led to a retracted
#          root cause. The argument is the value the detector actually sees.
#
#          Verdicts:
#            metrics_len=0 on every sample      -> BLOCKED on the metrics store;
#                                                  the whole-window fix cannot fire.
#            metrics_len>0 and armed=0 across a
#            cascade-add                        -> the last-pair check is the defect;
#                                                  the whole-window fix is warranted.
#            metrics_len>0 and armed>0          -> the glow already arms; M-TOPOLOGY-16
#                                                  needs a DOM-level check, not this fix.
#
# Usage:
#   python3 util/ad-hoc/e2e_m16_glow_instrument.py apply  --checkout <canopy>
#   # restart ONLY the canopy leg, drive a cascade-add with the topology tab open
#   python3 util/ad-hoc/e2e_m16_glow_instrument.py report --log <canopy log>
#   python3 util/ad-hoc/e2e_m16_glow_instrument.py revert --checkout <canopy>
#
# Exit codes: 0 ok, 1 nothing to do, 2 the instrument itself failed (NOT a result).

import argparse
import os
import re
import shutil
import subprocess  # nosec B404 - git plumbing only, fixed argv, no shell
import sys

REL = os.path.join("src", "frontend", "components", "network_visualizer.py")
BAK = "e2e_m16_glow_instrument.bak"

# Anchored on the line AFTER the detector runs, so the probe sees the result.
ANCHOR = "            # P2-1: Manage new node highlight state"
INDENT = " " * 12

PROBE = "\n".join(
    [
        "{i}# --- M16 GLOWPROBE (temporary; revert before committing) ---",
        "{i}try:",
        "{i}    _m16_n = len(metrics_data) if metrics_data else 0",
        "{i}    _m16_prev = None",
        "{i}    _m16_curr = None",
        "{i}    if metrics_data and len(metrics_data) >= 2:",
        "{i}        _m16_prev = (metrics_data[-2] or {{}}).get('network_topology', {{}}).get('hidden_units')",
        "{i}        _m16_curr = (metrics_data[-1] or {{}}).get('network_topology', {{}}).get('hidden_units')",
        "{i}    _m16_span = None",
        "{i}    if metrics_data:",
        "{i}        _m16_hs = [(_m or {{}}).get('network_topology', {{}}).get('hidden_units') for _m in metrics_data]",
        "{i}        _m16_hs = [_h for _h in _m16_hs if _h is not None]",
        "{i}        _m16_span = (min(_m16_hs), max(_m16_hs)) if _m16_hs else None",
        "{i}    self.logger.warning(",
        "{i}        f\"GLOWPROBE metrics_len={{_m16_n}} last_pair={{_m16_prev}}->{{_m16_curr}} \"",
        "{i}        f\"window_span={{_m16_span}} armed={{1 if newly_added_unit is not None else 0}} \"",
        "{i}        f\"newly_added_unit={{newly_added_unit}} topo_hidden={{(topology_data or {{}}).get('hidden_units')}}\"",
        "{i}    )",
        "{i}except Exception as _m16_e:  # pragma: no cover - never break the app for a probe",
        "{i}    self.logger.warning(f\"GLOWPROBE failed: {{_m16_e}}\")",
        "{i}# --- end M16 GLOWPROBE ---",
        "",
    ]
)


def _git_dir(checkout):
    try:
        return subprocess.run(  # nosec B603 B607 - fixed argv, no shell
            ["git", "-C", checkout, "rev-parse", "--absolute-git-dir"],
            capture_output=True, text=True, check=True, timeout=15,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def _paths(checkout):
    path = os.path.join(checkout, REL)
    if not os.path.isfile(path):
        print(f"not found: {path}", file=sys.stderr)
        sys.exit(2)
    gd = _git_dir(checkout)
    bak = os.path.join(gd, BAK) if gd and os.path.isdir(gd) else path + "." + BAK
    return path, bak


def do_apply(checkout):
    path, bak = _paths(checkout)
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if "GLOWPROBE" in src:
        print("already instrumented -- revert first")
        return 1
    if "newly_added_unit" not in src:
        print("newly_added_unit not found -- the detector has moved or been renamed", file=sys.stderr)
        return 2
    if src.count(ANCHOR) != 1:
        print(f"anchor found {src.count(ANCHOR)} times, expected 1 -- re-derive it", file=sys.stderr)
        return 2
    idx = src.find(ANCHOR)
    shutil.copyfile(path, bak)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src[:idx] + PROBE.format(i=INDENT) + src[idx:])
    print(f"instrumented {path}\n  backup: {bak}")
    print("  RESTART only the canopy leg, open Network Topology, drive a cascade-add, then `report`.")
    return 0


def do_revert(checkout):
    path, bak = _paths(checkout)
    if os.path.isfile(bak):
        shutil.move(bak, path)
        print(f"reverted from backup: {path}")
        return 0
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if "GLOWPROBE" not in src:
        print("not instrumented; nothing to revert")
        return 1
    cleaned = re.sub(r"[ \t]*# --- M16 GLOWPROBE.*?# --- end M16 GLOWPROBE ---\n", "", src, flags=re.S)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(cleaned)
    print(f"reverted by pattern: {path}")
    return 0


def _detector_kind(checkout):
    """Which new-unit detector is installed: 'whole-window', 'last-pair', or None.

    The verdict depends on this. ``armed=1`` is a FAILURE-mode observation under a
    last-pair detector (it got lucky) and a SUCCESS observation under a whole-window
    one, so a report that does not know which it measured is not interpretable.
    """
    if not checkout:
        return None
    try:
        with open(os.path.join(checkout, REL), encoding="utf-8") as fh:
            src = fh.read()
    except OSError:
        return None
    if "newly_added_unit" not in src:
        return None
    # The whole-window scan walks the window backwards; the last-pair check indexes
    # [-2] and [-1] directly. Look for the loop rather than a comment, so a stale
    # comment cannot misreport the build.
    if re.search(r"for\s+_i\s+in\s+range\(len\(metrics_data\)\s*-\s*1,\s*0,\s*-1\)", src):
        return "whole-window"
    if "metrics_data[-2]" in src:
        return "last-pair"
    return None


def do_report(log_path, checkout):
    if not os.path.isfile(log_path):
        print(f"log not found: {log_path}", file=sys.stderr)
        return 2
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n") for ln in fh if "GLOWPROBE" in ln]

    if not lines:
        # Absence is only a RESULT if the probe is provably installed; otherwise it
        # is an instrument failure, and reporting it as a result is how a vacuous
        # pass gets published.
        installed = False
        if checkout:
            try:
                with open(os.path.join(checkout, REL), encoding="utf-8") as fh:
                    installed = "GLOWPROBE" in fh.read()
            except OSError:
                installed = False
        if not checkout:
            print("no GLOWPROBE lines. Pass --checkout so I can confirm the probe is installed;")
            print("without that, absence is ambiguous between 'never ran' and 'not instrumented'.")
            return 2
        if not installed:
            print("no GLOWPROBE lines AND the probe is NOT installed -- instrument failure, not a result.")
            return 2
        print("no GLOWPROBE lines, and the probe IS installed in the running source.")
        print("  => the rebuild never ran while the log covered. Drive the topology tab and retry.")
        return 0

    n = len(lines)
    with_metrics = [ln for ln in lines if re.search(r"metrics_len=(?!0\b)\d+", ln)]
    armed = [ln for ln in lines if "armed=1" in ln]
    spans = re.findall(r"window_span=\((\d+), (\d+)\)", "\n".join(lines))
    growth_windows = [s for s in spans if s[0] != s[1]]

    print(f"GLOWPROBE invocations       : {n}")
    print(f"  with metrics_data (len>0) : {len(with_metrics)}")
    print(f"  windows spanning a change : {len(growth_windows)}  (min!=max hidden_units in the window)")
    print(f"  highlight ARMED           : {len(armed)}")
    print()
    for ln in lines[:6]:
        print("  " + ln[ln.find("GLOWPROBE"):][:190])
    if n > 6:
        print(f"  ... {n - 6} more")
    print()

    if not with_metrics:
        print("VERDICT: BLOCKED on the metrics store.")
        print("  metrics_data was EMPTY in every invocation, so newly_added_unit is None regardless of")
        print("  whether the detector is a last-pair check or a whole-window scan. Replacing the scan")
        print("  would be correct but UNOBSERVABLE -- fix the store first, and do not census this row.")
    elif not armed and growth_windows:
        print("VERDICT: the LAST-PAIR CHECK is the defect, and the whole-window fix is warranted.")
        print("  The callback received metrics windows that SPAN a hidden-unit change, yet armed the")
        print("  highlight zero times -- exactly what a last-pair check does when the rebuild does not")
        print("  happen to run on the one tick where the final two samples straddle the addition.")
    elif armed:
        # The verdict MUST know which detector it measured. "armed" means opposite
        # things before and after the fix, and an earlier version of this branch
        # asserted "a whole-window scan is NOT the fix" while reporting a run of the
        # whole-window scan working -- which would have told the next reader to undo it.
        scan = _detector_kind(checkout)
        if scan == "whole-window":
            print("VERDICT: the WHOLE-WINDOW scan is present and ARMING -- this is the fix working.")
            print("  Compare against a last-pair run on the same window shape; the discriminating pair is")
            print("  identical inputs with armed=0 (last-pair) vs armed=1 (whole-window).")
        elif scan == "last-pair":
            print("VERDICT: the LAST-PAIR check armed the highlight -- it caught an addition in the one")
            print("  tick where the final two samples straddled it. That is the lucky case, not the norm;")
            print("  the same detector armed 0 times across windows spanning up to 17 additions.")
        else:
            print("VERDICT: the highlight armed, but I could not determine WHICH detector is installed")
            print("  (pass --checkout). 'armed' means opposite things before and after the fix, so this")
            print("  result is not interpretable on its own.")
    else:
        print("VERDICT: INCONCLUSIVE -- metrics arrived but no window spanned a change.")
        print("  The cascade did not grow while the probe was live. Drive a real cascade-add and retry;")
        print("  do NOT read this as 'the detector works'.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["apply", "revert", "report"])
    ap.add_argument("--checkout", default="/home/pcalnon/Development/python/Juniper/juniper-canopy")
    ap.add_argument("--log", default="/tmp/juniper-e2e/logs/juniper-canopy.log")
    args = ap.parse_args()

    if args.action == "apply":
        return do_apply(args.checkout)
    if args.action == "revert":
        return do_revert(args.checkout)
    return do_report(args.log, args.checkout)


if __name__ == "__main__":
    sys.exit(main())
