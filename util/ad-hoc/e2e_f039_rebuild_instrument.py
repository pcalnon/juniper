#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Instrument the topology REBUILD (`update_network_graph`) to log, on every
#          invocation, (a) that it ran at all, (b) what `topology_data` it actually
#          received, and (c) which exit it took.
#
# WHY THIS IS THE DECISIVE PROBE, and what it distinguishes.
#
#   Measured 2026-08-30 on the live trio, same instant, three samples:
#       STORE  len=6434  input_units=2  hidden=10  conns=89   (single instance,
#                                                              paths-resolved)
#       GRAPH  traces=0  counts=['0','0','0','0']
#
#   The `0/0/0/0` counts can only be written by the rebuild's own
#   `input_units == 0` fast path (`network_visualizer.py:490`). The duplicate-store
#   probe found ONE instance of the store id on every tab, so "the reader reads a
#   different instance" is refuted. That leaves two possibilities that look
#   IDENTICAL from the browser and have completely different fixes:
#
#     A. the rebuild RUNS and receives an empty `topology_data` despite the store
#        holding 6,434 B -- a delivery problem between store and callback;
#     B. the rebuild does NOT RUN, and the `0/0/0/0` on screen is the stale result
#        of the mount-time invocation, when the store legitimately was empty.
#
#   (B) is live-hypothesis-shaped since canopy#537 merged: that fix made the tick
#   short-circuit actually fire (it had named a lane F-CANOPY-027 replaced, so it
#   was dead code), and both legs have since been restarted onto it. A completed
#   network's topology store also stops changing, so there may be no Input change
#   left to trigger a rebuild at all.
#
#   One log line separates them. Absence of REBUILDPROBE lines IS the (B) result --
#   but only if the probe is known to be installed, which `report` checks.
#
# Usage:
#   python3 util/ad-hoc/e2e_f039_rebuild_instrument.py apply  --checkout <canopy>
#   #   restart ONLY the canopy leg, open Network Topology ~90 s, then:
#   python3 util/ad-hoc/e2e_f039_rebuild_instrument.py report --log <canopy log>
#   python3 util/ad-hoc/e2e_f039_rebuild_instrument.py revert --checkout <canopy>
#
# The backup goes in the git dir, never the work tree -- see the sibling
# topoprobe instrument's header for why that matters.
#
# Exit: 0 ok, 1 nothing to do / no lines found, 2 invocation error.

import argparse
import os
import re
import shutil
import subprocess  # noqa: S404 - resolves the git dir so backups stay out of the work tree
import sys

REL = "src/frontend/components/network_visualizer.py"
BAK = "f039-rebuildprobe.bak"
ANCHOR = 'if not topology_data or topology_data.get("input_units", 0) == 0:'
INDENT = " " * 12

PROBE = "\n".join(
    [
        "{i}# --- F039 REBUILDPROBE (temporary; revert before committing) ---",
        "{i}try:",
        "{i}    import json as _f039_json",
        "",
        "{i}    _f039_ctx = dash.callback_context",
        "{i}    _f039_trig = [t.get('prop_id') for t in (_f039_ctx.triggered or [])] if _f039_ctx else []",
        "{i}    _f039_td = _f039_json.dumps(topology_data, sort_keys=True, default=str) if topology_data is not None else ''",
        "{i}    _f039_iu = topology_data.get('input_units') if isinstance(topology_data, dict) else None",
        "{i}    _f039_empty = (not topology_data) or (isinstance(topology_data, dict) and topology_data.get('input_units', 0) == 0)",
        "{i}    self.logger.warning(f\"REBUILDPROBE ran=1 td_type={{type(topology_data).__name__}} td_len={{len(_f039_td)}} input_units={{_f039_iu}} takes_empty_path={{_f039_empty}} triggered={{_f039_trig}}\")",
        "{i}except Exception as _f039_e:  # pragma: no cover - never break the app for a probe",
        "{i}    self.logger.warning(f\"REBUILDPROBE failed: {{_f039_e}}\")",
        "{i}# --- end F039 REBUILDPROBE ---",
        "",
    ]
)


def _git_dir(checkout):
    try:
        return subprocess.run(
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
    if "REBUILDPROBE" in src:
        print("already instrumented — revert first")
        return 1
    if "def update_network_graph" not in src:
        print("update_network_graph not found — has it been renamed?", file=sys.stderr)
        return 2
    if src.count(ANCHOR) != 1:
        print(f"anchor found {src.count(ANCHOR)} times, expected 1 — re-derive it", file=sys.stderr)
        return 2
    idx = src.find(ANCHOR)
    line_start = src.rfind("\n", 0, idx) + 1
    shutil.copyfile(path, bak)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src[:line_start] + PROBE.format(i=INDENT) + src[line_start:])
    print(f"instrumented {path}\n  backup: {bak}")
    print("  RESTART only the canopy leg, open Network Topology, then `report`.")
    return 0


def do_revert(checkout):
    path, bak = _paths(checkout)
    if os.path.isfile(bak):
        shutil.move(bak, path)
        print(f"reverted from backup: {path}")
        return 0
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if "REBUILDPROBE" not in src:
        print("not instrumented — nothing to revert")
        return 1
    cleaned = re.sub(r"[ \t]*# --- F039 REBUILDPROBE.*?# --- end F039 REBUILDPROBE ---\n", "", src, flags=re.S)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(cleaned)
    print(f"probe block removed from {path} (no backup present)")
    return 0


def do_report(log, checkout):
    if not os.path.isfile(log):
        print(f"not found: {log}", file=sys.stderr)
        return 2
    with open(log, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n") for ln in fh if "REBUILDPROBE" in ln]

    if not lines:
        # Absence is a RESULT here -- but only if the probe is actually installed.
        installed = None
        if checkout:
            path, _ = _paths(checkout)
            with open(path, encoding="utf-8") as fh:
                installed = "REBUILDPROBE" in fh.read()
        if installed is False:
            print("no REBUILDPROBE lines AND the probe is NOT installed — instrument failure, not a result.")
            return 1
        if installed is None:
            print("no REBUILDPROBE lines. Pass --checkout so I can confirm the probe is installed;")
            print("without that, absence is ambiguous and is NOT a result.")
            return 1
        print("no REBUILDPROBE lines, and the probe IS installed in the running source.")
        print("=> VERDICT (B): update_network_graph NEVER RAN during this window.")
        print("   The 0/0/0/0 on screen is the stale mount-time render, not a live empty read.")
        print("   Look at what should trigger it: a completed network's topology store stops")
        print("   changing, and canopy#537 made the bare-tick short-circuit live.")
        return 0

    heads = [ln for ln in lines if "ran=1" in ln]
    print(f"REBUILDPROBE invocations: {len(heads)}")
    for ln in heads[:15]:
        print("  " + ln[ln.find("REBUILDPROBE"):][:190])

    empt = [h for h in heads if "takes_empty_path=True" in h]
    lens = sorted({int(m.group(1)) for m in (re.search(r"td_len=(\d+)", h) for h in heads) if m})
    print()
    print(f"  invocations taking the EMPTY fast path: {len(empt)} / {len(heads)}")
    print(f"  distinct td_len values: {lens}")
    if empt and max(lens or [0]) < 100:
        print("  => VERDICT (A): the rebuild RUNS and receives an EMPTY topology_data,")
        print("     even though the client store holds a populated one. The defect is in")
        print("     DELIVERY of the store value to this callback.")
    elif not empt:
        print("  => the rebuild runs and receives a POPULATED topology_data — so it is not")
        print("     taking the empty path, and the 0/0/0/0 on screen came from somewhere else.")
        print("     Check whether its RESPONSE is being applied (that was the F-039 starting point).")
    else:
        print("  => mixed: some invocations empty, some populated. Read the triggered= field to")
        print("     see which lane produced the empty ones before concluding.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["apply", "revert", "report"])
    ap.add_argument("--checkout")
    ap.add_argument("--log", default="/home/pcalnon/Development/python/Juniper/juniper-canopy/logs/system.log")
    args = ap.parse_args()
    if args.action == "report":
        return do_report(args.log, args.checkout)
    if not args.checkout:
        print("--checkout is required for apply/revert", file=sys.stderr)
        return 2
    return do_apply(args.checkout) if args.action == "apply" else do_revert(args.checkout)


if __name__ == "__main__":
    sys.exit(main())
