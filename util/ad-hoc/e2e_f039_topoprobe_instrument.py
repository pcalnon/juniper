#!/usr/bin/env python3
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  E2E Phase-5 support (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Re-runnable form of the ONE instrument that root-caused F-CANOPY-039,
#          generalised to any of the canopy store writers that show its shape.
#
#          Every browser-side probe in that investigation was unreliable or
#          ambiguous (the driver's ``_store()`` read returned ``None`` while that
#          store's writer provably fired 12x/60 s). What settled it was logging the
#          comparison's OPERANDS SERVER-side, inside the handler, where the value
#          Dash actually delivered as ``State`` is visible:
#
#            TOPOPROBE[topology] eq=False cur_type=dict cur_len=75   new_len=7059   (x4)
#            TOPOPROBE[topology] eq=True  cur_type=dict cur_len=7059 new_len=7059   (x11)
#
#          Read the WHOLE log, not its head: the client's copy is empty for ~22 s and
#          then CONVERGES, holding the correct 7,059 B topology for 11 consecutive
#          ticks. (The original reading of this same log said "permanently empty" --
#          it had generalised from the first four lines. ``report`` now prints the
#          distinct ``cur_len`` values precisely so that mistake cannot recur.)
#
#          The finding is the CONTRADICTION: over that same window the rebuild's
#          ``input_units == 0`` fast path proves the value its READER gets is empty.
#          Two different values for one store id at the same instant -- the
#          duplicate-store-instance signature.
#
#          That instrumentation was a temporary source edit and was reverted, so the
#          finding became unreproducible. This script makes it a first-class,
#          revertible tool instead.
#
#          **Why two targets.** F-CANOPY-035 records a related shape on
#          ``metrics-panel-metrics-store`` ("globally empty, len 0, on both tabs"), and
#          F-CANOPY-038's census -- 32 writes, 31 byte-identical, ZERO ``no_update`` --
#          is only possible if that store's client copy never equals any of them.
#          ``--target metrics`` decides it, and topology now supplies the BASELINE to
#          read it against: eq=False x4, then eq=True x11. If metrics is eq=False on
#          EVERY sample at one constant ``cur_len``, its client copy really never
#          advances -- a different behaviour from topology's, and the explanation
#          F-CANOPY-035 was missing. If it converges the way topology's does, the
#          round-trip-asymmetry hypothesis lives and the two are separate defects.
#
# Usage:
#   # 1. instrument a canopy checkout (idempotent; writes a .f039bak beside the file)
#   python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py apply  --checkout <canopy-dir> --target metrics
#   # 2. restart that canopy leg, drive the relevant tab, then:
#   python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py report --log <canopy .log> [--target metrics]
#   # 3. ALWAYS revert before committing anything from that checkout
#   python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py revert --checkout <canopy-dir>
#
# NOTE on ``--target topology``: as of 2026-08-29 ``_update_topology_store_handler``
#   takes only ``(n, active_tab)`` -- it does NOT receive the client's store copy. The
#   original probe worked because the investigation had temporarily added that State.
#   ``apply`` therefore REFUSES this target with instructions rather than emitting a
#   probe that reads a name not in scope. ``--target metrics`` needs no such edit:
#   ``current_metrics`` is already a parameter.
#
# Exit codes: 0 ok, 1 nothing to do / no probe lines found, 2 invocation error.

import argparse
import os
import re
import shutil
import sys

REL = "src/frontend/dashboard_manager.py"
BAK_SUFFIX = ".f039bak"

# handler -- the method that must exist (a rename is itself the hazard class this arc
#            keeps hitting, so refuse loudly rather than probe blind)
# current -- the parameter carrying the CLIENT's copy, delivered as State
# fresh   -- the local holding the value just fetched from the server
# anchor  -- source text the probe is inserted immediately BEFORE
# indent  -- leading whitespace at the insertion point
TARGETS = {
    "topology": {
        "handler": "_update_topology_store_handler",
        "current": "current",
        "fresh": "topology",
        "anchor": "return topology",
        "indent": " " * 16,
        "store": "network-visualizer-topology-store",
    },
    "metrics": {
        "handler": "_update_metrics_store_handler",
        "current": "current_metrics",
        "fresh": "metrics",
        # Anchored on the Stage 2 suppression itself, so EVERY comparison is logged --
        # including any that would have returned no_update.
        "anchor": "if isinstance(current_metrics, list) and metrics == current_metrics:",
        "indent": " " * 12,
        "store": "metrics-panel-metrics-store",
    },
}

PROBE_TMPL = "\n".join(
    [
        "{i}# --- F039 TOPOPROBE ({t}; temporary instrumentation; revert before committing) ---",
        "{i}try:",
        "{i}    import json as _f039_json",
        "",
        "{i}    _f039_same = {cur} == {new}",
        '{i}    _f039_cur = _f039_json.dumps({cur}, sort_keys=True, default=str) if {cur} is not None else ""',
        "{i}    _f039_new = _f039_json.dumps({new}, sort_keys=True, default=str)",
        '{i}    self.logger.warning(f"TOPOPROBE[{t}] eq={{_f039_same}} cur_type={{type({cur}).__name__}} cur_len={{len(_f039_cur)}} new_len={{len(_f039_new)}} canon_eq={{_f039_cur == _f039_new}}")',
        "{i}    if not _f039_same and isinstance({cur}, dict) and isinstance({new}, dict):",
        "{i}        for _f039_k in sorted(set(list({new}) + list({cur}))):",
        "{i}            if {cur}.get(_f039_k) != {new}.get(_f039_k):",
        '{i}                self.logger.warning(f"TOPOPROBE[{t}]   differs key={{_f039_k!r}} cur={{str({cur}.get(_f039_k))[:80]}} new={{str({new}.get(_f039_k))[:80]}}")',
        "{i}except Exception as _f039_e:  # pragma: no cover - never break the app for a probe",
        '{i}    self.logger.warning(f"TOPOPROBE[{t}] failed: {{_f039_e}}")',
        "{i}# --- end F039 TOPOPROBE ---",
        "",
    ]
)


def build_probe(target):
    spec = TARGETS[target]
    return PROBE_TMPL.format(i=spec["indent"], t=target, cur=spec["current"], new=spec["fresh"])


def _target_path(checkout):
    path = os.path.join(checkout, REL)
    if not os.path.isfile(path):
        print(f"not found: {path}", file=sys.stderr)
        sys.exit(2)
    return path


def do_apply(checkout, target):
    spec = TARGETS[target]
    path = _target_path(checkout)
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if "TOPOPROBE" in src:
        print("already instrumented - revert first (only one target at a time)")
        return 1

    if f"def {spec['handler']}" not in src:
        print(f"{spec['handler']} not found - has it been renamed?", file=sys.stderr)
        return 2

    # The probe compares the CLIENT's store copy against the fresh fetch, so the handler
    # must actually RECEIVE it. Emitting a probe that reads a name not in scope is the
    # stale-identifier class this arc has already hit three times.
    sig = re.search(rf"def {spec['handler']}\(([^)]*)\)", src)
    if sig is None or spec["current"] not in sig.group(1):
        print(
            f"REFUSING: {spec['handler']} has no `{spec['current']}` parameter\n"
            f"  signature: {sig.group(1).strip() if sig else '<unparsed>'}\n\n"
            f"The probe compares the CLIENT's copy of `{spec['store']}` against the fresh\n"
            f"fetch, so the handler must receive it. Add\n"
            f'    State("{spec["store"]}", "data")\n'
            f"to that callback, thread it through as `{spec['current']}=`, and re-run.\n"
            f"(As of 2026-08-29 this is the expected outcome for --target topology and NOT\n"
            f"for --target metrics; see this file's header note.)",
            file=sys.stderr,
        )
        return 2

    idx = src.find(spec["anchor"])
    if idx == -1:
        print(f"anchor {spec['anchor']!r} not found - re-derive it against the current source", file=sys.stderr)
        return 2
    line_start = src.rfind("\n", 0, idx) + 1
    shutil.copyfile(path, path + BAK_SUFFIX)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src[:line_start] + build_probe(target) + src[line_start:])
    print(f"instrumented {path} (target: {target} -> {spec['store']})")
    print(f"  backup: {path + BAK_SUFFIX}")
    print("  RESTART that canopy leg, drive the relevant tab, then `report`.")
    print("  REMEMBER to `revert` before committing anything from this checkout.")
    return 0


def do_revert(checkout):
    path = _target_path(checkout)
    bak = path + BAK_SUFFIX
    if os.path.isfile(bak):
        shutil.move(bak, path)
        print(f"reverted from backup: {path}")
        return 0
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if "TOPOPROBE" not in src:
        print("not instrumented - nothing to revert")
        return 1
    cleaned = re.sub(r"[ \t]*# --- F039 TOPOPROBE.*?# --- end F039 TOPOPROBE ---\n", "", src, flags=re.S)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(cleaned)
    print(f"probe block removed from {path} (no backup was present)")
    return 0


def do_report(log, target):
    if not os.path.isfile(log):
        print(f"not found: {log}", file=sys.stderr)
        return 2
    # Accept the pre-2026-08-29 unlabelled form too, so the original evidence file reports.
    want = ("TOPOPROBE[%s]" % target) if target else "TOPOPROBE"
    with open(log, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n") for ln in fh if want in ln or (target and "TOPOPROBE " in ln and target == "topology")]
    if not lines:
        print(f"no {want} lines - is the leg running the instrumented checkout, and was the tab driven?")
        return 1
    heads = [ln for ln in lines if " eq=" in ln]
    print(f"TOPOPROBE lines: {len(lines)}  (comparisons: {len(heads)})")
    for ln in lines[:20]:
        print("  " + ln[ln.find("TOPOPROBE") :][:170])

    if not heads:
        return 0
    never_equal = all("eq=False" in h for h in heads)
    cur_lens = sorted({int(m.group(1)) for m in (re.search(r"cur_len=(\d+)", h) for h in heads) if m})
    cur_types = sorted({m.group(1) for m in (re.search(r"cur_type=(\w+)", h) for h in heads) if m})
    canon_eqs = sorted({m.group(1) for m in (re.search(r"canon_eq=(\w+)", h) for h in heads) if m})
    print()
    print(f"  every comparison unequal: {never_equal}")
    print(f"  distinct cur_len values : {cur_lens if cur_lens else 'none parsed'}")
    print(f"  distinct cur_type values: {', '.join(cur_types) if cur_types else 'none parsed'}")
    print(f"  distinct canon_eq values: {', '.join(canon_eqs) if canon_eqs else 'none parsed'}")

    # cur_len alone does NOT discriminate: the metrics store ships data=[] (empty
    # default -> cur_len=2) and an unresolved State gives cur_len=0 via the probe's
    # own `"" if current is None` branch. Different defects, different fixes, both
    # "small and constant". And a DETERMINISTIC round-trip asymmetry is large AND
    # constant -- the bucket an earlier version of this rule did not have at all.
    print()
    if not never_equal:
        print("  => VERDICT: some comparisons MATCHED - the client copy does advance.")
        print("     Refutes 'never advances' for this store. (This is topology's shape:")
        print("     eq=False x4 then eq=True x11.)")
        return 0
    if len(cur_lens) != 1:
        print("  => VERDICT: never equal, and cur_len VARIES. Neither the never-advances")
        print("     signature nor a deterministic asymmetry. Investigate before concluding.")
        return 0
    only = cur_lens[0]
    if only == 0 or "NoneType" in cur_types:
        print("  => VERDICT: cur_len=0 / cur_type=NoneType - the State is not being")
        print("     DELIVERED at all. That is a different defect from a store that is")
        print("     written-but-empty, and it is NOT a confirmation of the unification.")
    elif only <= 8:
        print(f"  => VERDICT: constant small cur_len={only} matching the store's empty")
        print("     default - the client's copy never advances. For --target metrics this")
        print("     supports F-035/-038/-039 being one defect.")
    else:
        print(f"  => VERDICT: constant LARGE cur_len={only} with never-equal. The client copy")
        print("     is populated and stable yet never compares equal: that is hypothesis (i),")
        print("     a DETERMINISTIC round-trip asymmetry, and it REFUTES the unification.")
        print("     A constant is what a deterministic transform predicts, not evidence against it.")
    print()
    print("  BEFORE concluding: discriminate by WRITER. metrics-panel-metrics-store has a")
    print("  second, UNGUARDED writer (append_ws_metrics_store, allow_duplicate=True,")
    print("  dashboard_manager.py:3910) whose every write is no_update-free by construction,")
    print("  and the guarded handler writes [] rather than no_update when the copy is falsy.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["apply", "revert", "report"])
    ap.add_argument("--checkout", help="canopy checkout to instrument (apply/revert)")
    ap.add_argument("--target", choices=sorted(TARGETS), default="topology", help="which store writer to probe (default: topology)")
    ap.add_argument("--log", default="/tmp/juniper-e2e/juniper-canopy-ab.log", help="canopy stdout log to scan (report)")
    args = ap.parse_args()

    if args.action == "report":
        return do_report(args.log, args.target)
    if not args.checkout:
        print("--checkout is required for apply/revert", file=sys.stderr)
        return 2
    return do_apply(args.checkout, args.target) if args.action == "apply" else do_revert(args.checkout)


if __name__ == "__main__":
    sys.exit(main())
