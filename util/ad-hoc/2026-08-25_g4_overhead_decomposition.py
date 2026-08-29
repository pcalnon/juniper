#!/usr/bin/env python3
"""
G4 instrument: decompose a training run's wall-clock into named overhead segments.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc — investigation (cascor#571 / perf-lane G4)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: cascor#571; util/ad-hoc/2026-08-16_h2h_phase_split.py (candidate/output split only);
         util/ad-hoc/2026-08-21_h2h_paired_campaign.bash (produces the runs this reads)

WHY. After cascor#563 the candidate phase fell from ~98% to ~66% of a service cap-16 span —
startup, dataset acquisition, output passes, snapshot saves and teardown now set the wall,
and no instrument names them (G4: "no instrument exists — build the decomposition first,
measure second"). This reads a run's trainer log and carves the span into:

    pre_dataset   first log record → dataset acquisition start
    dataset       dataset acquisition start → tensors reported
    pre_fit       tensors reported → fit start (network construction, seeding)
    training (train_start = min(first output record, fit_start) → fit end):
      pool_setup    first cand_start → "Persistent pool created" (⊂ candidate)
      candidate     per-round train_candidates spans (existing phase_split semantics)
      output        output-layer training spans
      snapshots     Σ (Saving network → Successfully saved) inside fit
      train_other   training span minus the buckets above
    teardown      fit end → last log record
    unlogged      (optional) process wall seconds minus first→last record span, when a
                  thread_probe.json sits beside the logs — python boot + exit cost the
                  log cannot see

ANCHORING: message TEXT only, never file.py:func:LINE (methodology rule 5). Timestamps
carry 1-second resolution, so every figure is an integer-second count and short segments
quantise — treat ±1 s per boundary as the instrument's floor (methodology rule 9).

Usage:
  2026-08-25_g4_overhead_decomposition.py --dir-arm NAME PARENT_DIR   # run-*/ or cli-*/ with logs/
  2026-08-25_g4_overhead_decomposition.py --run-arm NAME RUN_DIR ...  # explicit run dirs
  (repeatable; add --json OUT.json for the full result)
"""

import argparse
import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

# Service-tier records interleave a comma-millisecond variant ((… 19:38:02,083)) with the
# trainer's second-resolution stamps; tolerate both, keep second resolution.
TS = re.compile(r"\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:,\d+)?\)")
MARKS = [
    ("dataset_start", re.compile(r"generate_n_spiral_dataset: Using JuniperData service at|_reload_dataset: Reloading dataset|_reload_dataset: Fetching")),
    ("dataset_ready", re.compile(r"solve_n_spiral_problem: Dataset x_full: Shape:|Reloaded dataset '")),
    ("fit_start", re.compile(r"fit: Starting main training loop with max_epochs:")),
    # "Creating persistent pool" logs at DEBUG (invisible at INFO); the pool is created
    # INSIDE the first train_candidates call, so pool_setup is measured as
    # first cand_start -> "Persistent pool created" and is a SUB-SEGMENT of candidate.
    ("pool_create_end", re.compile(r"_ensure_worker_pool: Persistent pool created with")),
    ("cand_start", re.compile(r"train_candidates: Executing candidate training with \d+ processes")),
    ("out_progress", re.compile(r"train_output_layer: Output Layer Training - Epoch \d+, Loss:")),
    ("out_final", re.compile(r"train_output_layer: Final output layer training loss:")),
    ("snap_start", re.compile(r"CascadeHDF5Serializer: Saving network to")),
    ("snap_end", re.compile(r"CascadeHDF5Serializer: Successfully saved network to")),
    ("fit_end", re.compile(r"fit: Training completed\.")),
]


def segments(run_dir: Path) -> "list[Path]":
    logs = run_dir / "logs"
    base = logs / "juniper_cascor.log"
    rotated = []
    if logs.is_dir():
        for p in logs.glob("juniper_cascor.log.*"):
            sfx = p.name.rsplit(".", 1)[-1]
            if sfx.isdigit():
                rotated.append((int(sfx), p))
    return [p for _n, p in sorted(rotated, reverse=True)] + ([base] if base.exists() else [])


def parse_run(run_dir: Path) -> "dict | None":
    events = []
    first_ts = last_ts = None
    for seg in segments(run_dir):
        with open(seg, errors="replace") as fh:
            for line in fh:
                m = TS.search(line)
                if not m:
                    continue
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                first_ts = first_ts or ts
                last_ts = ts
                for name, rx in MARKS:
                    if rx.search(line):
                        events.append((name, ts))
                        break
    if first_ts is None:
        return None
    ev = {}
    for name, ts in events:
        ev.setdefault(name, []).append(ts)

    def one(name, which=0):
        return ev.get(name, [None])[which] if ev.get(name) else None

    fit_start, fit_end = one("fit_start"), (ev.get("fit_end", [None])[-1] if ev.get("fit_end") else None)
    if not (fit_start and fit_end):
        return {"run": run_dir.name, "usable": False, "reason": "missing fit boundary"}

    s = lambda a, b: (b - a).total_seconds() if a and b else None  # noqa: E731

    # Phase split via a STREAM-ORDER state machine (nrun semantics). Two hard-won facts
    # from the service smoke run (d5a8): (1) a round's output tail lands in the SAME SECOND
    # as the next cand_start, so timestamp-partitioning zeroes rounds -- only log stream
    # order disambiguates 1-second-resolution events; (2) the INITIAL output pass runs
    # BEFORE the "fit: Starting main training loop" record (L-2 semantics: max_epochs is
    # the initial-pass budget), so that marker is NOT the training-start boundary --
    # train_start is min(first output record, fit_start).
    cand_total = 0.0
    out_total = 0.0
    cand_open = None
    out_open = None
    first_out = None
    for name, ts in events:
        if name == "cand_start":
            cand_open, out_open = ts, None
        elif name == "out_progress":
            if first_out is None:
                first_out = ts
            if cand_open is not None:
                cand_total += (ts - cand_open).total_seconds()
                cand_open, out_open = None, ts
            elif out_open is None:
                out_open = ts
        elif name == "out_final":
            if out_open is not None:
                out_total += (ts - out_open).total_seconds()
                out_open = None
    if cand_open is not None:  # final round with no output pass after it
        cand_total += (fit_end - cand_open).total_seconds()

    snap_total = 0.0
    snap_ends = ev.get("snap_end", [])
    for ss in ev.get("snap_start", []):
        se = next((x for x in snap_ends if x >= ss), None)
        if se:
            snap_total += (se - ss).total_seconds()
    first_cand = ev.get("cand_start", [None])[0]
    pool = s(first_cand, one("pool_create_end"))
    train_start = min([x for x in (first_out, fit_start) if x is not None])
    train_span = s(train_start, fit_end)
    train_other = train_span - cand_total - out_total - snap_total

    row = {
        "run": run_dir.name,
        "usable": True,
        "total_logged": s(first_ts, last_ts),
        "pre_dataset": s(first_ts, one("dataset_start")),
        "dataset": s(one("dataset_start"), one("dataset_ready")),
        "pre_fit": s(one("dataset_ready"), train_start),
        "train_span": train_span,
        "pool_setup": pool,
        "candidate": cand_total,
        "output": out_total,
        "snapshots": snap_total,
        "n_snapshots": len(ev.get("snap_start", [])),
        "train_other": train_other,
        "teardown": s(fit_end, last_ts),
        "rounds": len(ev.get("cand_start", [])),
    }
    probe = run_dir / "thread_probe.json"
    if probe.exists():
        try:
            wall = json.loads(probe.read_text()).get("process_wall_seconds")
            row["process_wall"] = wall
            row["unlogged"] = wall - row["total_logged"] if wall is not None else None
        except Exception:  # nosec B110
            pass
    return row


COLS = ["pre_dataset", "dataset", "pre_fit", "pool_setup", "candidate", "output", "snapshots", "train_other", "teardown", "unlogged", "total_logged", "process_wall"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir-arm", action="append", nargs=2, default=[], metavar=("NAME", "PARENT"))
    ap.add_argument("--run-arm", action="append", nargs="+", default=[], metavar="NAME RUN_DIR")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    arms = {}
    for name, parent in args.dir_arm:
        arms[name] = sorted(d for d in Path(parent).iterdir() if d.is_dir() and (d / "logs").is_dir())
    for spec in args.run_arm:
        arms[spec[0]] = [Path(p) for p in spec[1:]]
    if not arms:
        ap.error("no arms given")

    result = {}
    for name, dirs in arms.items():
        rows = [r for r in (parse_run(d) for d in dirs) if r]
        unusable = [r["run"] for r in rows if not r.get("usable")]
        rows = [r for r in rows if r.get("usable")]
        result[name] = {"rows": rows, "unusable": unusable}
        print(f"\n=== arm {name}: {len(rows)} usable, unusable={unusable or '[]'} ===")
        hdr = f"{'run':16}" + "".join(f"{c:>12}" for c in COLS)
        print(hdr)
        for r in rows:
            print(f"{r['run']:16}" + "".join(f"{(r.get(c) if r.get(c) is not None else float('nan')):>12.0f}" for c in COLS))
        if rows:
            print(f"{'mean±sd':16}" + "".join(_ms(rows, c) for c in COLS))
            fs = [r["train_span"] for r in rows]
            print(f"train_span mean {statistics.mean(fs):.0f} s; candidate share of training {100 * statistics.mean([r['candidate'] / r['train_span'] for r in rows if r['train_span']]):.0f}%")

    if args.json:
        args.json.write_text(json.dumps(result, indent=2, default=str))
        print(f"\njson -> {args.json}")
    return 0


def _ms(rows, col):
    vals = [r.get(col) for r in rows if r.get(col) is not None]
    if not vals:
        return f"{'—':>12}"
    if len(vals) == 1:
        return f"{vals[0]:>12.0f}"
    return f"{statistics.mean(vals):>7.0f}±{statistics.stdev(vals):<4.0f}"


if __name__ == "__main__":
    sys.exit(main())
