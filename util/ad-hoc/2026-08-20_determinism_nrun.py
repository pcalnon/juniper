#!/usr/bin/env python3
"""N-RUN determinism instrument: a divergence RATE and a timing noise floor, per arm.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-20
Status:      ad-hoc -- one-off (juniper-cascor#532 seeded-run reproducibility)
Retire when: #532 is root-caused or accepted and the evidence note is merged; delete then.
Related:     2026-08-18_h2h_pair_compare.py (the PAIR-shaped predecessor this replaces for
             N-run work; kept for its existing callers);
             2026-08-16_h2h_phase_split.py (where the phase-split idea comes from -- but see
             ANCHORING below, that script's line-number markers are now stale).

WHY THIS EXISTS RATHER THAN ANOTHER PAIR COMPARISON
---------------------------------------------------
Three claims in this investigation were made and then withdrawn, all by the same error:
generalising a mechanism from too few samples ("19.5 pp is monotonic in thread count", "the
service is deterministic and the CLI is not", "every divergence lands on one of two values at
iteration 2"). The effect being measured fires in roughly HALF of run-pairs. On a coin that
lands heads half the time, two tosses tell you nothing, and the predecessor tool's shape --
group runs into an (a, b) pair, print DETERMINISTIC or NONDETERMINISTIC -- structurally invites
exactly the withdrawn claim. It also silently DROPPED members 3..N of any group and could not
group service runs at all, because their directory names are unique run ids.

So this reports a RATE over N runs with an interval, never a verdict over a pair, and it names
every run it could not use instead of dropping it.

WHAT "OUTCOME" MEANS
--------------------
The fingerprint is the FULL per-iteration ``grow_network`` trace -- the tuple of
``(iteration, train_loss, train_accuracy, early_stop)`` strings exactly as logged, in order.
Final accuracy alone is too coarse: a cap-4 run has only a handful of iterations and two
genuinely different trajectories can land on the same rounded endpoint. Log strings are compared
rather than parsed floats so the fingerprint is exactly what the run recorded.

THE HEADLINE STATISTIC
----------------------
``pair_divergence_rate`` = the fraction of the C(N,2) unordered run-pairs whose fingerprints
differ. This is deliberately in the SAME units as the observation that opened #532 ("3 of 5
run-pairs diverged"), so the two are directly comparable.

It is also a legitimate estimator, not just a descriptive count: if runs are i.i.d. draws from
some distribution over outcomes, the pairwise agreement rate is an unbiased U-statistic for
``P(two independent runs agree)`` = the collision probability ``sum_k p_k^2``. Its sampling
variance is NOT binomial -- the pairs share runs and are therefore not independent -- so the
interval here is a RUN-level bootstrap (resample the N runs with replacement, recompute), which
is valid for a U-statistic where a naive binomial interval would be too narrow. ``--boot-seed``
keeps it reproducible.

``distinct_outcomes`` and the outcome histogram are reported alongside, because a rate near 1.0
means something very different when it comes from 2 near-equal clusters than from 20 singletons.

ANCHORING (this bit has already bitten once)
--------------------------------------------
Every marker below is matched on MESSAGE TEXT, never on a ``file.py: func:LINE`` token. Line
numbers shift with any edit to the trainer, and a stale token does not raise -- it silently
matches nothing and the tool reports a confident zero. This is not hypothetical:
``2026-08-16_h2h_phase_split.py`` anchors on ``train_candidates:2166`` /
``train_output_layer:2100`` / ``train_output_layer:2120``, and after juniper-cascor#539 shifted
``cascade_correlation.py`` by ~90 lines all three now point at non-logging statements. Counts
derived from the anchors are asserted non-zero here so the failure is loud.

TIMING, AND WHY IT IS PART OF A DETERMINISM TOOL
------------------------------------------------
The wall-clock residual this investigation returns to next (a ~1.17x candidate-phase ratio at
cap 16) rests on ONE run per arm. Sizing it needs a noise floor, and the N runs collected here
are exactly the sample that provides one -- so span, candidate-phase span, candidate epoch count
and seconds-per-candidate-epoch are captured per run and reported as mean +/- sd per arm. Not
collecting them here would mean paying for a second N-run campaign to get them.

CROSS-ARM ACCURACY CAVEAT
-------------------------
``train_acc`` / ``val_acc`` are the last two ``calculate_accuracy`` records. On the direct-CLI
arm those come from ``SpiralProblem.evaluate``'s post-fit pair; on the service arm they come
from ``fit``'s own call sites. Same function, different provenance -- fine WITHIN an arm (which
is all the divergence rate uses), but do not publish a cross-arm accuracy delta from this field
without confirming the two are measuring the same thing.

Usage:
    python util/ad-hoc/2026-08-20_determinism_nrun.py \
        --arm cli     /path/to/cli-1  /path/to/cli-2  ... \
        --arm service /path/to/run-a  /path/to/run-b  ... \
        [--json out.json] [--boot 10000] [--boot-seed 20260820]

    A RUN_DIR is any directory containing ``logs/juniper_cascor.log`` (plus rotated ``.N``
    segments). That single shape covers both arms: the direct-CLI runner points
    ``JUNIPER_CASCOR_LOG_DIR`` at ``<OUT_DIR>/logs``, and a service run dir carries the
    trainer's log at the same relative path.

Exit: 0 on a report; 2 if no arm had a usable run, or if a marker matched nothing anywhere
      (a stale-anchor failure, which must be loud rather than reported as a clean zero).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# --- markers: message TEXT only, never a file:line token (see ANCHORING above) --------------
TS = re.compile(r"\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)")
RE_ITER = re.compile(
    r"grow_network: Iteration (\d+) - Train Loss: ([0-9.eE+-]+), "
    r"Train Accuracy: ([0-9.eE+-]+), Early stop: (\w+)"
)
# Only the ``calculate_accuracy`` frame; the sibling ``_accuracy`` frame logs the same phrase.
RE_ACC = re.compile(r"calculate_accuracy: Calculated accuracy: ([0-9.]+)")
RE_DONE = re.compile(r"fit: Training completed\.")
RE_FIT_START = re.compile(r"fit: Starting main training loop with max_epochs:")
RE_CAND_START = re.compile(r"train_candidates: Executing candidate training with (\d+) processes")
RE_OUT_PROGRESS = re.compile(r"train_output_layer: Output Layer Training - Epoch (\d+), Loss:")
RE_OUT_FINAL = re.compile(r"train_output_layer: Final output layer training loss:")
RE_CAND_EPOCH = re.compile(r"CandidateUnit: train: Epoch (\d+) - Norm Output:")
RE_CORR = re.compile(r"CandidateUnit: train: Final Correlation: UUID: [0-9a-f-]+, Final correlation value: ([0-9.eE+-]+)")
RE_UNITS = re.compile(r"grow_network: .*?(\d+) hidden units")

#: ``CandidateUnit._display_training_progress`` emits one INFO record every
#: ``display_frequency`` epochs; both arms leave it at the module default of 10. Record counts
#: are therefore multiplied by this to get epochs. Reported BOTH ways so the raw count stays
#: auditable -- juniper-cascor#531's published 44,910 / 46,080 are the x10 forms of 4,491 /
#: 4,608, and conflating the two silently changes a rate by an order of magnitude.
CAND_DISPLAY_FREQUENCY = 10


def segments(run_dir: Path) -> "list[Path]":
    """The run's trainer log plus any rotated siblings, OLDEST FIRST.

    A single cap-64 cell has written ~950 MB and rotated mid-run, leaving the ``fit:`` start
    marker stranded in ``juniper_cascor.log.1``. Reading only the base file loses the span.
    """
    logs = run_dir / "logs"
    base = logs / "juniper_cascor.log"
    rotated: "list[tuple[int, Path]]" = []
    if logs.is_dir():
        for p in logs.glob("juniper_cascor.log.*"):
            suffix = p.name.rsplit(".", 1)[-1]
            if suffix.isdigit():
                rotated.append((int(suffix), p))
    # Higher .N is older, so descending .N then the live file yields chronological order.
    return [p for _n, p in sorted(rotated, reverse=True)] + ([base] if base.exists() else [])


def parse_run(run_dir: Path) -> dict:
    """Extract one run's fingerprint and timing. Never raises on a malformed log."""
    iters: "list[tuple[str, str, str, str]]" = []
    accs: "list[str]" = []
    complete = False
    fit_start = fit_end = None
    cand_start = out_start = None
    cand_spans: "list[float]" = []
    out_spans: "list[float]" = []
    cand_epoch_records = 0
    cand_epoch_max = 0
    processes = None
    corr_rounds: "list[list[str]]" = []

    for seg in segments(run_dir):
        try:
            fh = seg.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if (m := RE_CAND_EPOCH.search(line)):
                    cand_epoch_records += 1
                    cand_epoch_max = max(cand_epoch_max, int(m.group(1)))
                    continue
                if (m := RE_CORR.search(line)):
                    if corr_rounds:
                        corr_rounds[-1].append(m.group(1))
                    continue
                if (m := RE_ITER.search(line)):
                    iters.append((m.group(1), m.group(2), m.group(3), m.group(4)))
                    continue
                if (m := RE_ACC.search(line)):
                    accs.append(m.group(1))
                    continue
                # The remaining markers are the timing skeleton and all carry a timestamp.
                ts_m = TS.search(line)
                ts = datetime.strptime(ts_m.group(1), "%Y-%m-%d %H:%M:%S") if ts_m else None
                if RE_DONE.search(line):
                    complete = True
                    if ts:
                        fit_end = ts
                elif RE_FIT_START.search(line):
                    if ts and fit_start is None:
                        fit_start = ts
                elif (m := RE_CAND_START.search(line)):
                    processes = int(m.group(1))
                    cand_start, out_start = ts, None
                    corr_rounds.append([])
                elif RE_OUT_PROGRESS.search(line):
                    # The first output-progress record after a candidate phase closes it.
                    if cand_start is not None and out_start is None and ts is not None:
                        cand_spans.append((ts - cand_start).total_seconds())
                        out_start = ts
                elif RE_OUT_FINAL.search(line):
                    if out_start is not None and ts is not None:
                        out_spans.append((ts - out_start).total_seconds())
                    cand_start = out_start = None

    trace_key = "|".join(",".join(t) for t in iters)
    # SECOND, FINER FINGERPRINT. A cap-4 run logs only 3 `grow_network` iterations but trains 32
    # candidates, so two runs can share a trace fingerprint while their arithmetic differed -- most
    # obviously in the final candidate round, whose iteration line is never logged. Sorted per
    # round, because log order is worker arrival order and varies by construction.
    corr_key = "|".join(",".join(sorted(r)) for r in corr_rounds)
    span = (fit_end - fit_start).total_seconds() if fit_start and fit_end else None
    cand_total = sum(cand_spans) if cand_spans else None
    cand_epochs = cand_epoch_records * CAND_DISPLAY_FREQUENCY
    return {
        "dir": str(run_dir),
        "name": run_dir.name,
        "complete": complete,
        "n_iterations": len(iters),
        "iters": iters,
        # Content fingerprints for grouping identical runs, not security primitives.
        "fingerprint": hashlib.sha1(trace_key.encode(), usedforsecurity=False).hexdigest()[:12] if iters else None,
        "corr_fingerprint": hashlib.sha1(corr_key.encode(), usedforsecurity=False).hexdigest()[:12] if corr_rounds else None,
        "corr_rounds": len(corr_rounds),
        "corr_values": sum(len(r) for r in corr_rounds),
        # SpiralProblem.evaluate logs train then test last; see CROSS-ARM ACCURACY CAVEAT.
        "train_acc": accs[-2] if len(accs) >= 2 else None,
        "val_acc": accs[-1] if len(accs) >= 2 else None,
        "span_s": span,
        "cand_total_s": cand_total,
        "out_total_s": sum(out_spans) if out_spans else None,
        "cand_phases": len(cand_spans),
        "out_passes": len(out_spans),
        "cand_epoch_records": cand_epoch_records,
        "cand_epochs": cand_epochs,
        "s_per_cand_epoch": (cand_total / cand_epochs) if cand_total and cand_epochs else None,
        "processes": processes,
    }


def _mean_sd(values: "list[float]") -> "tuple[float | None, float | None, int]":
    vals = [v for v in values if v is not None]
    if not vals:
        return None, None, 0
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else None
    return mean, sd, len(vals)


def _fmt(mean, sd, n, unit: str = "", places: int = 1) -> str:
    if mean is None:
        return "n/a"
    sd_txt = f" +/- {sd:.{places}f}" if sd is not None else " +/- n/a"
    cv = f"  (cv {100 * sd / mean:.1f}%)" if sd is not None and mean else ""
    return f"{mean:.{places}f}{sd_txt}{unit}  [n={n}]{cv}"


def pair_stats(runs: "list[dict]", key: str = "fingerprint") -> dict:
    """Pairwise divergence rate + the first-divergent-iteration histogram."""
    fps = [r[key] for r in runs]
    n = len(fps)
    n_pairs = n * (n - 1) // 2
    divergent = 0
    first_div: Counter = Counter()
    length_mismatch = 0
    for i in range(n):
        for j in range(i + 1, n):
            if fps[i] == fps[j]:
                continue
            divergent += 1
            a, b = runs[i]["iters"], runs[j]["iters"]
            point = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), None)
            if point is None:
                # Traces agree on the overlap but differ in length: growth stopped elsewhere.
                length_mismatch += 1
                first_div[f"len({len(a)}vs{len(b)})"] += 1
            else:
                # Report the trace's own iteration label, not the list index.
                first_div[a[point][0]] += 1
    return {
        "n_runs": n,
        "n_pairs": n_pairs,
        "n_divergent_pairs": divergent,
        "pair_divergence_rate": (divergent / n_pairs) if n_pairs else None,
        "distinct_outcomes": len(set(fps)),
        "outcome_histogram": dict(Counter(fps).most_common()),
        "first_divergence_histogram": dict(sorted(first_div.items(), key=lambda kv: (-kv[1], str(kv[0])))),
        "length_mismatch_pairs": length_mismatch,
    }


def bootstrap_ci(runs: "list[dict]", draws: int, seed: int, key: str = "fingerprint") -> "tuple[float, float] | None":
    """Run-level bootstrap interval for the pairwise divergence rate.

    Resamples RUNS (not pairs). The pairs share runs, so they are not independent and a binomial
    interval on ``n_divergent_pairs / n_pairs`` would be far too narrow; resampling the
    underlying i.i.d. units is the correct move for a U-statistic.
    """
    fps = [r[key] for r in runs]
    n = len(fps)
    if n < 3 or draws <= 0:
        return None
    rng = random.Random(seed)
    rates: "list[float]" = []
    for _ in range(draws):
        sample = [fps[rng.randrange(n)] for _ in range(n)]
        div = sum(1 for i in range(n) for j in range(i + 1, n) if sample[i] != sample[j])
        rates.append(div / (n * (n - 1) // 2))
    rates.sort()
    lo = rates[int(0.025 * (len(rates) - 1))]
    hi = rates[int(0.975 * (len(rates) - 1))]
    return lo, hi


def report_arm(name: str, run_dirs: "list[Path]", draws: int, seed: int) -> dict:
    parsed = [parse_run(d) for d in run_dirs]

    # Name every excluded run rather than dropping it silently -- the predecessor tool's
    # silent drop of group members 3..N is precisely what this replaces.
    no_trace = [r for r in parsed if not r["iters"]]
    in_flight = [r for r in parsed if r["iters"] and not r["complete"]]
    usable = [r for r in parsed if r["iters"] and r["complete"]]

    print(f"\n{'=' * 100}")
    print(f"ARM: {name}    dirs given={len(parsed)}  usable={len(usable)}  "
          f"in-flight={len(in_flight)}  no-trace={len(no_trace)}")
    print("=" * 100)
    for r in no_trace:
        print(f"  EXCLUDED (no grow_network trace) : {r['name']}")
    for r in in_flight:
        print(f"  EXCLUDED (no 'Training completed.'): {r['name']}  iterations={r['n_iterations']}")
    if not usable:
        print("  no usable runs in this arm")
        return {"arm": name, "usable": 0}

    print(f"\n  {'run':<34} {'fp':<13} {'iters':>5} {'train':>7} {'val':>7} "
          f"{'span_s':>7} {'cand_s':>7} {'out_s':>6} {'cand_ep':>8} {'s/ep':>7}")
    print("  " + "-" * 106)
    for r in sorted(usable, key=lambda x: x["name"]):
        print(f"  {r['name'][:34]:<34} {r['fingerprint']:<13} {r['n_iterations']:>5} "
              f"{r['train_acc'] or '-':>7} {r['val_acc'] or '-':>7} "
              f"{r['span_s'] or 0:>7.0f} {r['cand_total_s'] or 0:>7.0f} {r['out_total_s'] or 0:>6.0f} "
              f"{r['cand_epochs']:>8} {r['s_per_cand_epoch'] or 0:>7.4f}")

    stats = pair_stats(usable)
    ci = bootstrap_ci(usable, draws, seed)
    rate = stats["pair_divergence_rate"]

    print(f"\n  --- reproducibility ({stats['n_runs']} runs, {stats['n_pairs']} pairs) ---")
    if rate is not None:
        ci_txt = f"   95% CI [{ci[0]:.3f}, {ci[1]:.3f}] (run-level bootstrap, {draws} draws)" if ci else ""
        print(f"  pair divergence rate : {stats['n_divergent_pairs']}/{stats['n_pairs']} "
              f"= {rate:.3f}{ci_txt}")
    print(f"  distinct outcomes    : {stats['distinct_outcomes']} of {stats['n_runs']} runs")
    print(f"  outcome histogram    : {stats['outcome_histogram']}")
    if stats["first_divergence_histogram"]:
        print(f"  first divergent iter : {stats['first_divergence_histogram']}")
    if stats["length_mismatch_pairs"]:
        print(f"  length-mismatch pairs: {stats['length_mismatch_pairs']} "
              f"(traces agree on the overlap but growth stopped at different iterations)")

    # The finer fingerprint. A run that matches on the logged trace can still have done different
    # arithmetic -- the final candidate round never gets a `grow_network` line -- so a rate of 0
    # on the trace alone is not a determinism result. Report both; the correlation rate is the
    # strictly stronger statement and is the one to quote when claiming a fix worked.
    corr_stats = None
    if all(r.get("corr_fingerprint") for r in usable):
        corr_stats = pair_stats(usable, key="corr_fingerprint")
        corr_ci = bootstrap_ci(usable, draws, seed, key="corr_fingerprint")
        c_rate = corr_stats["pair_divergence_rate"]
        rounds = {r["corr_rounds"] for r in usable}
        values = {r["corr_values"] for r in usable}
        print(f"\n  --- finer fingerprint: per-round candidate correlations "
              f"(rounds={sorted(rounds)}, values/run={sorted(values)}) ---")
        if c_rate is not None:
            c_txt = f"   95% CI [{corr_ci[0]:.3f}, {corr_ci[1]:.3f}]" if corr_ci else ""
            print(f"  pair divergence rate : {corr_stats['n_divergent_pairs']}/{corr_stats['n_pairs']} "
                  f"= {c_rate:.3f}{c_txt}")
        print(f"  distinct outcomes    : {corr_stats['distinct_outcomes']} of {corr_stats['n_runs']} runs")
        if rate is not None and c_rate is not None and c_rate > rate:
            print(f"  NOTE: the correlations diverge more often than the trace does "
                  f"({c_rate:.3f} vs {rate:.3f}) -- runs that look identical in the iteration\n"
                  f"        trace did measurably different candidate arithmetic.")

    timing = {}
    print("\n  --- timing noise floor ---")
    for key, label, unit, places in (
        ("span_s", "training span", " s", 1),
        ("cand_total_s", "candidate phase", " s", 1),
        ("out_total_s", "output phase", " s", 1),
        ("cand_epochs", "candidate epochs", "", 0),
        ("s_per_cand_epoch", "s / candidate epoch", " s", 5),
    ):
        mean, sd, n = _mean_sd([r[key] for r in usable])
        timing[key] = {"mean": mean, "sd": sd, "n": n}
        print(f"  {label:<20}: {_fmt(mean, sd, n, unit, places)}")

    return {
        "arm": name,
        "usable": len(usable),
        "excluded_no_trace": [r["name"] for r in no_trace],
        "excluded_in_flight": [r["name"] for r in in_flight],
        "bootstrap_ci": list(ci) if ci else None,
        "bootstrap_draws": draws,
        "bootstrap_seed": seed,
        "runs": [{k: v for k, v in r.items() if k != "iters"} for r in usable],
        "timing": timing,
        "correlation_fingerprint": corr_stats,
        **stats,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", action="append", nargs="+", default=[],
                    metavar="NAME RUN_DIR", help="arm label followed by its run directories; repeatable")
    ap.add_argument("--dir-arm", action="append", nargs=2, default=[],
                    metavar=("NAME", "PARENT_DIR"),
                    help="arm label plus a parent directory; uses every immediate subdirectory "
                         "that contains a logs/ folder. Avoids expanding 20 paths on a command line.")
    ap.add_argument("--suite-arm", action="append", nargs=2, default=[],
                    metavar=("NAME", "REGISTRY_JSONL"),
                    help="arm label plus a suite registry.jsonl; expands to that suite's run_dirs. "
                         "A service arm's run dirs carry unique run ids, so listing them by hand is "
                         "both tedious and a place to silently drop one.")
    ap.add_argument("--json", type=Path, default=None, help="also write the full result as JSON")
    ap.add_argument("--boot", type=int, default=10000, help="bootstrap draws (0 disables)")
    ap.add_argument("--boot-seed", type=int, default=20260820, help="bootstrap RNG seed")
    args = ap.parse_args()

    if not args.arm and not args.suite_arm and not args.dir_arm:
        print("need at least one --arm, --dir-arm or --suite-arm", file=sys.stderr)
        return 2

    results = []
    for spec in args.arm:
        if len(spec) < 2:
            print(f"--arm needs a label and at least one directory, got {spec!r}", file=sys.stderr)
            return 2
        results.append(report_arm(spec[0], [Path(p) for p in spec[1:]], args.boot, args.boot_seed))
    for label, parent in args.dir_arm:
        kids = sorted((p for p in Path(parent).iterdir() if (p / "logs").is_dir()),
                      key=lambda p: p.name)
        if not kids:
            print(f"--dir-arm: no run directories with a logs/ folder under {parent}", file=sys.stderr)
            return 2
        results.append(report_arm(label, kids, args.boot, args.boot_seed))
    for label, registry in args.suite_arm:
        try:
            rows = [json.loads(line) for line in Path(registry).read_text().splitlines() if line.strip()]
        except (OSError, ValueError) as exc:
            print(f"--suite-arm: could not read {registry}: {exc}", file=sys.stderr)
            return 2
        # Report cells the suite itself did not complete, rather than quietly analysing a subset:
        # a rate over 17 surviving cells reported as "N=20" is a real way to overstate a result.
        bad = [r.get("cell_id") for r in rows if r.get("outcome") != "succeeded"]
        if bad:
            print(f"\n  NOTE [{label}]: {len(bad)} cell(s) did not succeed and carry no usable run: {bad}")
        results.append(report_arm(label, [Path(r["run_dir"]) for r in rows if r.get("run_dir")],
                                  args.boot, args.boot_seed))

    usable_total = sum(r.get("usable", 0) for r in results)
    if not usable_total:
        print("\nno usable runs in any arm", file=sys.stderr)
        return 2

    # A stale anchor does not raise -- it matches nothing and reports a clean zero. Fail loudly
    # instead, because a silent zero here would read as a real measurement.
    dead = [
        f"{r['arm']}.{key}"
        for r in results if r.get("usable")
        for key in ("span_s", "cand_total_s", "cand_epochs")
        if not (r["timing"].get(key) or {}).get("mean")
    ]
    if dead:
        print(f"\nSTALE-ANCHOR FAILURE: these markers matched nothing: {', '.join(dead)}", file=sys.stderr)
        print("Re-derive the marker text from the current trainer source before trusting any number above.",
              file=sys.stderr)
        return 2

    if args.json:
        args.json.write_text(json.dumps({"arms": results}, indent=2, default=str))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
