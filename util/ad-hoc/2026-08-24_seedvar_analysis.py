#!/usr/bin/env python3
# Compare DIAG candidate-seed lists across N instrumented direct-CLI runs.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-24
# Status:      ad-hoc -- one-off (juniper-cascor#532 attribution: did candidate seeds vary
#              run-to-run on the pre-#566 direct-CLI path?)
# Retire when: #532's attribution is written up in the evidence note and merged; delete then.
# Related:     util/ad-hoc/2026-08-21_cascor_seeds_and_balance_diag.patch (emits the lines);
#              util/ad-hoc/2026-08-20_determinism_arm.bash (produces the run layout);
#              util/ad-hoc/2026-08-20_determinism_nrun.py (fingerprint-level comparison).
#
# WHAT THIS ANSWERS
# cascor#566 replaced `random.randint` off the process-global stream with a network-owned
# `random.Random(random_seed)` for candidate seeds. The post-#566 N=20 campaign reads 0/190
# diverging pairs where the pre-arc build read 0.768 -- but that closure is unattributed
# across 24 commits. If, at the DIRECT PARENT of #566 (e4e5b990, #565), the per-round
# candidate-seed lists VARY across identically-configured runs, then the global-stream
# coupling was live immediately before #566 and the attribution is settled. If they are
# constant AND the runs' outcomes are identical, the closure predates #565 and the window
# reopens (bisect earlier).
#
# ANCHORING: message TEXT only, never file.py:func:LINE (methodology rule 5).
# VACUITY GUARDS (methodology rule 8): a run with no DIAG seed line, an unexpected pool
# size, or an unexpected round count is COUNTED AND NAMED, never silently skipped.
#
# Usage: 2026-08-24_seedvar_analysis.py <ARM_DIR> [--json OUT.json]
#   ARM_DIR  parent directory whose immediate run-* subdirectories each hold logs/.

import argparse
import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

RE_SEEDS = re.compile(r"DIAG: candidate_seeds=\[([0-9, ]*)\] random_max_value=(\d+) network_seed=(\S+)")
RE_INSTALL = re.compile(r"_add_best_candidate: DIAG: iteration=(\d+) installed_index=(\S+) correlation_exact=(\S+)")


def segments(run_dir: Path) -> "list[Path]":
    """Trainer log plus rotated siblings, OLDEST FIRST (same contract as _nrun.py)."""
    logs = run_dir / "logs"
    base = logs / "juniper_cascor.log"
    rotated = []
    if logs.is_dir():
        for p in logs.glob("juniper_cascor.log.*"):
            suffix = p.name.rsplit(".", 1)[-1]
            if suffix.isdigit():
                rotated.append((int(suffix), p))
    return [p for _n, p in sorted(rotated, reverse=True)] + ([base] if base.exists() else [])


def parse_run(run_dir: Path) -> dict:
    rounds = []
    max_vals = set()
    net_seeds = set()
    installs = []
    for seg in segments(run_dir):
        with open(seg, errors="replace") as fh:
            for line in fh:
                m = RE_SEEDS.search(line)
                if m:
                    seeds = tuple(int(t) for t in m.group(1).replace(",", " ").split())
                    rounds.append(seeds)
                    max_vals.add(m.group(2))
                    net_seeds.add(m.group(3))
                    continue
                m = RE_INSTALL.search(line)
                if m:
                    installs.append((int(m.group(1)), m.group(2), m.group(3)))
    return {
        "run": run_dir.name,
        "rounds": rounds,
        "n_rounds": len(rounds),
        "pool_sizes": sorted({len(r) for r in rounds}),
        "random_max_values": sorted(max_vals),
        "network_seeds": sorted(net_seeds),
        "installs": installs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arm_dir", type=Path)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    run_dirs = sorted(d for d in args.arm_dir.iterdir() if d.is_dir() and (d / "logs").is_dir())
    if not run_dirs:
        print(f"FATAL: no run directories with logs/ under {args.arm_dir}", file=sys.stderr)
        return 2

    runs = [parse_run(d) for d in run_dirs]

    # --- vacuity guards, each named ---------------------------------------------------------
    no_seed_lines = [r["run"] for r in runs if r["n_rounds"] == 0]
    usable = [r for r in runs if r["n_rounds"] > 0]
    print(f"runs discovered: {len(runs)}   with seed lines: {len(usable)}   WITHOUT: {no_seed_lines or '[]'}")
    if not usable:
        print("FATAL: instrument dead in every run -- nothing to compare", file=sys.stderr)
        return 2
    round_counts = Counter(r["n_rounds"] for r in usable)
    pool_sizes = sorted({s for r in usable for s in r["pool_sizes"]})
    print(f"rounds/run: {dict(sorted(round_counts.items()))}   pool sizes seen: {pool_sizes}")
    print(f"network_seed values seen: {sorted({s for r in usable for s in r['network_seeds']})}")

    # --- the question: do seed lists vary run to run? ---------------------------------------
    common_rounds = min(r["n_rounds"] for r in usable)
    print(f"\nper-round distinct seed lists (over {len(usable)} runs, first {common_rounds} rounds):")
    any_variation = False
    for k in range(common_rounds):
        vals = Counter(r["rounds"][k] for r in usable)
        distinct = len(vals)
        any_variation = any_variation or distinct > 1
        top = "; ".join(f"{c}x {list(v)[:4]}..." if len(v) > 4 else f"{c}x {list(v)}" for v, c in vals.most_common(3))
        print(f"  round {k}: {distinct} distinct   [{top}]")

    fps = [tuple(r["rounds"][:common_rounds]) for r in usable]
    pairs = list(itertools.combinations(range(len(fps)), 2))
    diverging = sum(1 for i, j in pairs if fps[i] != fps[j])
    rate = diverging / len(pairs) if pairs else 0.0
    print(f"\nseed-fingerprint pair divergence: {diverging}/{len(pairs)} = {rate:.3f}")
    print(f"distinct whole-run seed fingerprints: {len(set(fps))} of {len(fps)}")

    # --- corroboration: installed-candidate + exact-correlation fingerprints ----------------
    inst_fps = [tuple(r["installs"]) for r in usable]
    inst_div = sum(1 for i, j in pairs if inst_fps[i] != inst_fps[j])
    n_inst = sorted({len(f) for f in inst_fps})
    print(f"installed-candidate fingerprints: {len(set(inst_fps))} distinct of {len(inst_fps)} (records/run {n_inst}); pair divergence {inst_div}/{len(pairs)}")

    verdict = "SEEDS VARY RUN-TO-RUN (global-stream coupling live on this build)" if any_variation else "seeds CONSTANT across runs on this build"
    print(f"\nVERDICT: {verdict}")

    if args.json:
        args.json.write_text(json.dumps({
            "arm_dir": str(args.arm_dir),
            "runs": [{k: (v if k != "rounds" else [list(t) for t in v]) for k, v in r.items()} for r in runs],
            "no_seed_lines": no_seed_lines,
            "common_rounds": common_rounds,
            "seed_pair_divergence": {"diverging": diverging, "pairs": len(pairs), "rate": rate},
            "distinct_seed_fingerprints": len(set(fps)),
            "installed_pair_divergence": inst_div,
            "verdict": verdict,
        }, indent=2))
        print(f"json -> {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
