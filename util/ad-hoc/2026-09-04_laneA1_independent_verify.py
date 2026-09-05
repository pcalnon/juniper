#!/usr/bin/env python3
"""
Project: Juniper
Sub-Project: juniper-ml
Application: Lane A1 independent-consensus re-measurement (2026-09-04)
Author: Paul Calnon
Version: 1.0.0
License: MIT

Independent re-creation of the PF-1 numeric claims straight from raw artifacts.
Deliberately shares NO code with util/experiments/read_run_metrics.py or
util/ad-hoc/2026-09-02_pf1_drive_extract.py -- everything below parses
manifest.json / metrics_series.csv / registry.jsonl / train_response.json /
experiment.yaml by hand.

Invoke through 2026-09-04_laneA1_run.py (module name starts with a digit).
"""
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

import yaml

ROOT = Path.home() / ".local/state/juniper-experiments"


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------
def load_json(p):
    try:
        with open(p) as fh:
            return json.load(fh)
    except Exception:
        return None


def run_dirs():
    """Every directory directly under ROOT that owns a manifest.json."""
    return [d for d in sorted(ROOT.iterdir()) if d.is_dir() and (d / "manifest.json").is_file()]


def last_metrics_row(run):
    """(step_count, step_sum, nrows) from the LAST row of metrics_series.csv."""
    p = Path(run) / "artifacts/results/metrics_series.csv"
    if not p.is_file():
        return None
    with open(p, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return None
    last = rows[-1]

    def num(k):
        v = last.get(k, "")
        if v in (None, ""):
            return None
        try:
            return float(v)
        except ValueError:
            return None

    return (
        num("juniper_cascor_training_step_duration_seconds_count"),
        num("juniper_cascor_training_step_duration_seconds_sum"),
        len(rows),
    )


def sd(xs):
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def pct(x, mean):
    return 100.0 * x / mean if mean else float("nan")


# --------------------------------------------------------------------------
# claim 1 -- drive quantization
# --------------------------------------------------------------------------
def claim1():
    rows = []
    for run in run_dirs():
        m = load_json(run / "manifest.json")
        if not m:
            continue
        polls = (m.get("drive_loop") or {}).get("polls")
        drive = (m.get("timings") or {}).get("drive")
        iv = (m.get("driver") or {}).get("poll_interval")
        if polls is None or drive is None:
            continue
        rows.append((run.name, polls, drive, iv, drive - (polls - 1) * 5.0))
    n = len(rows)
    print(f"runs with both drive_loop.polls and timings.drive: {n}")
    ivs = {}
    for r in rows:
        ivs[r[3]] = ivs.get(r[3], 0) + 1
    print(f"driver.poll_interval values: {ivs}")
    res = sorted(r[4] for r in rows)

    def q(p):
        i = p * (n - 1)
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        return res[lo] + (res[hi] - res[lo]) * (i - lo)

    print(f"residual drive-(polls-1)*5.0: min={res[0]:.3f} p25={q(.25):.3f} "
          f"median={q(.5):.3f} p75={q(.75):.3f} p95={q(.95):.3f} max={res[-1]:.3f}")
    for lim in (0.25, 0.5, 1.0, 2.0, 5.0):
        c = sum(1 for x in res if abs(x) <= lim)
        print(f"  |residual| <= {lim:>4}: {c}/{n} ({100 * c / n:.1f}%)")
    print("largest |residual|:")
    for name, polls, drive, iv, r in sorted(rows, key=lambda r: -abs(r[4]))[:10]:
        print(f"  {name}  polls={polls:<5} drive={drive:<10.3f} iv={iv} resid={r:+.3f}")

    gen = [(r[0], r[1], r[2], r[3], r[2] - (r[1] - 1) * r[3]) for r in rows if r[3]]
    g = sorted(x[4] for x in gen)
    print(f"\nGENERALISED law drive-(polls-1)*poll_interval over {len(g)} runs: "
          f"min={g[0]:.3f} median={statistics.median(g):.3f} max={g[-1]:.3f}")
    print(f"  negative residuals: {sum(1 for x in g if x < 0)}")
    print("\nresidual (5 s law) by poll count, poll_interval==5.0:")
    for lo, hi in [(2, 20), (21, 50), (51, 100), (101, 300), (301, 700), (701, 10 ** 9)]:
        sel = [r for r in rows if lo <= r[1] <= hi and r[3] == 5.0]
        if not sel:
            continue
        rs = [r[4] for r in sel]
        per = [r[4] / max(r[1] - 1, 1) for r in sel]
        lab = "inf" if hi > 10 ** 8 else str(hi)
        print(f"  polls {lo:>4}-{lab:>4}: n={len(sel):<4} resid median={statistics.median(rs):7.3f} "
              f"max={max(rs):8.3f} | per-poll median={statistics.median(per) * 1000:7.3f} ms")


# --------------------------------------------------------------------------
# suite helpers
# --------------------------------------------------------------------------
def suite_cells(suite_id):
    out = []
    with open(ROOT / "suites" / suite_id / "registry.jsonl") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    out.sort(key=lambda r: r["cell_id"])
    return out


def cell_row(rec):
    run = Path(rec["run_dir"])
    m = load_json(run / "manifest.json") or {}
    lm = last_metrics_row(run)
    return {
        "cell": rec["cell_id"],
        "run": run.name,
        "exists": run.is_dir(),
        "cfg": rec.get("config_sha256"),
        "wall": rec.get("wall_seconds"),
        "drive": (m.get("timings") or {}).get("drive"),
        "total": (m.get("timings") or {}).get("total"),
        "polls": (m.get("drive_loop") or {}).get("polls"),
        "final_epoch": (m.get("drive_loop") or {}).get("final_epoch"),
        "step_count": lm[0] if lm else None,
        "step_sum": lm[1] if lm else None,
        "csv_rows": lm[2] if lm else None,
        "completion": m.get("completion_reason"),
        "overrides": rec.get("overrides") or {},
    }


def cell_table(suite_id):
    return [cell_row(r) for r in suite_cells(suite_id)]


def show_suite(suite_id, note=""):
    rows = cell_table(suite_id)
    print(f"== {suite_id} == {note}")
    print(f"{'cell':<14}{'run':<24}{'drive':>9}{'polls':>7}{'rows':>6}"
          f"{'step_count':>11}{'step_sum':>10}{'ms/step':>9}  completion")
    for r in rows:
        if not r["exists"]:
            print(f"{r['cell']:<14}{r['run']:<24}   *** RUN DIR MISSING ***")
            continue
        mps = (r["step_sum"] / r["step_count"] * 1000) if (r["step_sum"] and r["step_count"]) else float("nan")
        d = "     None" if r["drive"] is None else format(r["drive"], "9.3f")
        sc = "       None" if r["step_count"] is None else format(r["step_count"], "11.0f")
        ss = "      None" if r["step_sum"] is None else format(r["step_sum"], "10.3f")
        print(f"{r['cell']:<14}{r['run']:<24}{d}{str(r['polls']):>7}{str(r['csv_rows']):>6}"
              f"{sc}{ss}{mps:>9.3f}  {r['completion']}")
    drives = [r["drive"] for r in rows if r["drive"] is not None]
    sums = [r["step_sum"] for r in rows if r["step_sum"] is not None]
    counts = [r["step_count"] for r in rows if r["step_count"] is not None]
    if drives:
        mu = statistics.fmean(drives)
        print(f"  drive     : n={len(drives)} min={min(drives):.3f} median={statistics.median(drives):.3f} "
              f"max={max(drives):.3f} mean={mu:.3f} sd={sd(drives):.4f} cv={pct(sd(drives), mu):.4f}%")
    if sums:
        mu = statistics.fmean(sums)
        print(f"  step_sum  : n={len(sums)} min={min(sums):.3f} median={statistics.median(sums):.3f} "
              f"max={max(sums):.3f} mean={mu:.3f} sd={sd(sums):.4f} cv={pct(sd(sums), mu):.4f}%")
    if counts:
        print(f"  step_count: distinct={sorted(set(int(c) for c in counts))}")
    if drives and sums and sd(drives) > 0:
        rr = sd(sums) / sd(drives)
        cr = (sd(sums) / statistics.fmean(sums)) / (sd(drives) / statistics.fmean(drives))
        print(f"  sd ratio step_sum/drive = {rr:.2f}x     CV ratio = {cr:.2f}x")
    cfgs = [r["cfg"] for r in rows]
    print(f"  config_sha256 distinct = {len(set(cfgs))} of {len(cfgs)}  -> {[c[:8] for c in cfgs]}")
    return rows


def claim2():
    show_suite("pf1-cascor-spiral-repeats-20260903T040803Z", "(claims 2 + 5)")


# --------------------------------------------------------------------------
# claim 3 -- 20 s cells: drive sd vs step_sum sd
# --------------------------------------------------------------------------
TWENTY = [
    "pf1-cascor-spiral-repeats-20260831T233254Z",
    "pf1-cascor-spiral-repeats-20260901T071754Z",
    "pf1-cascor-spiral-repeats-20260901T072151Z",
]
ALL_PF1 = TWENTY + [
    "pf1-cascor-spiral-repeats-20260901T101126Z",
    "pf1-cascor-spiral-repeats-20260901T101940Z",
    "pf1-cascor-spiral-repeats-20260901T103324Z",
    "pf1-cascor-spiral-repeats-20260903T040803Z",
]


def claim3():
    per_suite = []
    for s in TWENTY:
        rows = show_suite(s)
        print()
        per_suite.append(rows)
    print("=== pooled across the three 20 s suites ===")
    drives, sums = [], []
    for rows in per_suite:
        drives += [r["drive"] for r in rows if r["drive"] is not None]
        sums += [r["step_sum"] for r in rows if r["step_sum"] is not None]
    if drives and sums:
        dm, sm = statistics.fmean(drives), statistics.fmean(sums)
        print(f"drive   n={len(drives)} mean={dm:.4f} sd={sd(drives):.5f} cv={pct(sd(drives), dm):.4f}%")
        print(f"step_sum n={len(sums)} mean={sm:.4f} sd={sd(sums):.5f} cv={pct(sd(sums), sm):.4f}%")
        print(f"pooled RAW sd ratio = {sd(sums) / sd(drives):.2f}x  "
              f"CV ratio = {(sd(sums) / sm) / (sd(drives) / dm):.2f}x")


def claim3_all():
    for s in ALL_PF1:
        show_suite(s)
        print()


# --------------------------------------------------------------------------
# claim 4 -- quiet-run drift floor
# --------------------------------------------------------------------------
def ms_per_step(rows):
    return [r["step_sum"] / r["step_count"] * 1000
            for r in rows if r["step_sum"] and r["step_count"]]


def claim4():
    print("--- part A: the three 20 s PF-1 suites, mean ms/step per suite ---")
    means = []
    for s in TWENTY:
        rows = cell_table(s)
        v = ms_per_step(rows)
        if not v:
            print(f"{s}: NO DATA")
            continue
        mu = statistics.fmean(v)
        means.append(mu)
        print(f"{s}: n={len(v)} mean={mu:.3f} ms  per-cell={[round(x, 3) for x in v]}")
    if len(means) > 1:
        lo, hi = min(means), max(means)
        print(f"suite means: {[round(m, 3) for m in means]}")
        print(f"spread max/min-1 = {100 * (hi / lo - 1):.2f}%   "
              f"sd/mean = {pct(sd(means), statistics.fmean(means)):.2f}%")

    print("\n--- part B: headroom-sweep quiet blocks ---")
    for sweep in sorted(ROOT.glob("headroom-sweep-*")):
        tsv = sweep / "blocks.tsv"
        if not tsv.is_file():
            continue
        print(f"[{sweep.name}]")
        qmeans = []
        with open(tsv) as fh:
            rdr = csv.DictReader(fh, delimiter="\t")
            for rec in rdr:
                sdir = Path(rec["suite_dir"])
                sid = sdir.name
                try:
                    rows = cell_table(sid)
                except FileNotFoundError:
                    print(f"  {rec['block']:<12} {rec['profile']:<8} registry MISSING ({sid})")
                    continue
                v = ms_per_step(rows)
                if not v:
                    print(f"  {rec['block']:<12} {rec['profile']:<8} no metrics rows")
                    continue
                mu = statistics.fmean(v)
                if rec["profile"] == "quiet":
                    qmeans.append((rec["block"], mu))
                print(f"  {rec['block']:<12} {rec['profile']:<8} workers={rec['workers']:<3} "
                      f"load={rec['loadavg_at_start']:<6} n={len(v)} mean={mu:8.3f} ms  "
                      f"cells={[round(x, 3) for x in v]}")
        if len(qmeans) > 1:
            vals = [m for _, m in qmeans]
            lo, hi = min(vals), max(vals)
            print(f"  QUIET blocks {[b for b, _ in qmeans]} -> {[round(v, 3) for v in vals]}")
            print(f"  quiet spread max/min-1 = {100 * (hi / lo - 1):.2f}%   "
                  f"sd/mean = {pct(sd(vals), statistics.fmean(vals)):.2f}%")


# --------------------------------------------------------------------------
# claim 6 -- cosmetic-stripped config hash
# --------------------------------------------------------------------------
def strip_hash(path):
    with open(path) as fh:
        doc = yaml.safe_load(fh)
    exp = doc.get("experiment")
    if isinstance(exp, dict):
        exp.pop("description", None)
        exp.pop("name", None)
    return hashlib.sha256(
        json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def raw_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def claim6(*suite_ids):
    ids = list(suite_ids) or [
        "pf1-cascor-spiral-repeats-20260903T040803Z",
        "pf1-cascor-spiral-repeats-20260901T101126Z",
    ]
    per_suite = {}
    for sid in ids:
        cells = sorted((ROOT / "suites" / sid / "cells").iterdir())
        print(f"== {sid} ==")
        hs = []
        for c in cells:
            y = c / "experiment.yaml"
            if not y.is_file():
                print(f"  {c.name}: experiment.yaml MISSING")
                continue
            sh, rh = strip_hash(y), raw_hash(y)
            hs.append(sh)
            print(f"  {c.name:<16} raw={rh[:16]}  stripped={sh[:16]}")
        print(f"  stripped distinct = {len(set(hs))} of {len(hs)}")
        per_suite[sid] = set(hs)
    if len(ids) > 1:
        keys = list(per_suite)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = per_suite[keys[i]], per_suite[keys[j]]
                print(f"\n{keys[i]} vs {keys[j]}: "
                      f"{'IDENTICAL' if a == b else 'DIFFERENT'}  "
                      f"({sorted(x[:12] for x in a)} vs {sorted(x[:12] for x in b)})")


def claim6_all():
    claim6(*ALL_PF1)


# --------------------------------------------------------------------------
# claim 7 -- recurrence runs
# --------------------------------------------------------------------------
def claim7():
    rec_runs = []
    for run in run_dirs():
        m = load_json(run / "manifest.json")
        if not m:
            continue
        if "train" in (m.get("timings") or {}):
            rec_runs.append((run, m))
    print(f"runs whose manifest.timings contains 'train': {len(rec_runs)}")
    ne, nw, missing_file, missing_key = {}, {}, [], []
    for run, _m in rec_runs:
        tr = load_json(run / "artifacts/results/train_response.json")
        if tr is None:
            missing_file.append(run.name)
            continue
        v = tr.get("n_epochs")
        if v is None:
            missing_key.append(run.name)
        else:
            ne[v] = ne.get(v, 0) + 1
        w = (tr.get("dataset") or {}).get("n_windows")
        nw[w] = nw.get(w, 0) + 1
    print(f"n_epochs distribution: {dict(sorted(ne.items(), key=lambda kv: (kv[0] is None, kv[0])))}")
    print(f"  total with a value = {sum(ne.values())}")
    print(f"  train_response.json MISSING: {len(missing_file)} -> {missing_file}")
    print(f"  present but n_epochs absent/null: {len(missing_key)} -> {missing_key}")
    print(f"dataset.n_windows distribution: {dict(sorted(nw.items(), key=lambda kv: (kv[0] is None, kv[0])))}")
    print(f"  distinct n_windows = {len(nw)}")


# --------------------------------------------------------------------------
# claim 8 -- epoch calibration
# --------------------------------------------------------------------------
def resolved_training(run):
    """The run's own copy of the config it actually acted on."""
    p = Path(run) / "config/experiment.yaml"
    if not p.is_file():
        return {}
    try:
        with open(p) as fh:
            doc = yaml.safe_load(fh) or {}
        return ((doc.get("training") or {}).get("params") or {})
    except Exception:
        return {}


def claim8():
    at1010 = {}
    for sid in ["pf1-epoch-calibration-20260903T040341Z", "output-epochs-impact-20260903T002924Z"]:
        print(f"== {sid} ==")
        for rec in suite_cells(sid):
            r = cell_row(rec)
            tp = resolved_training(rec["run_dir"])
            if tp.get("max_hidden_units") == 10 and tp.get("max_iterations") == 10 and r["step_sum"]:
                at1010.setdefault(tp.get("max_epochs"), []).append(r["step_sum"])
            mps = (r["step_sum"] / r["step_count"] * 1000) if (r["step_sum"] and r["step_count"]) else float("nan")
            print(f"  {r['cell']:<16} max_epochs={str(tp.get('max_epochs')):<6} "
                  f"output_epochs={str(tp.get('output_epochs')):<6} "
                  f"hu={str(tp.get('max_hidden_units')):<4} it={str(tp.get('max_iterations')):<4} | "
                  f"drive={r['drive'] if r['drive'] is None else format(r['drive'], '.3f'):>8} "
                  f"step_count={str(int(r['step_count']) if r['step_count'] else None):>7} "
                  f"step_sum={r['step_sum'] if r['step_sum'] is None else format(r['step_sum'], '.3f'):>8} "
                  f"ms/step={mps:7.3f}  {r['completion']}")
        print()
    print("=== step_sum at max_hidden_units=10, max_iterations=10, keyed by max_epochs ===")
    for k in sorted(at1010):
        v = at1010[k]
        print(f"  max_epochs={k:<6} n={len(v)} values={[round(x, 3) for x in v]} "
              f"mean={statistics.fmean(v):.4f}")
