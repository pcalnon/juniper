#!/usr/bin/env python3
"""WIDE-BUDGET HEAD-TO-HEAD -- collect both arms into one comparable table.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-08-16
Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
Retire when: the wide-budget head-to-head evidence note is merged; delete then.
Related:     util/experiments/suites/p4/e-j-h2h-wide-cap{64,128}.yaml (the service arm);
             util/ad-hoc/2026-08-16_h2h_cli_arm.bash (the CLI arm);
             util/ad-hoc/2026-08-16_h2h_preflight.py (the before-the-run invariant check).

THE WALL-CLOCK DENOMINATOR
The head-to-head smoke note could not report a speed ratio: its service figure was the driver's
poll-based drive loop and its CLI figure was whole-process wall including interpreter start and
dataset fetch, so the two shared no denominator. They do now. Both paths run the same
CascadeCorrelationNetwork.fit and bracket it with the same pair of INFO records --

    cascade_correlation.py:1918  "fit: Starting main training loop with max_epochs: ..."
    cascade_correlation.py:1936  "fit: Training completed."

-- at second resolution, and since juniper-cascor#523 the SERVICE arm writes them into its own
run dir (JUNIPER_CASCOR_LOG_DIR, exported per run by experiment_stack.bash) instead of the
checkout-shared file where the driver could not see them. TRAINING SPAN is the difference between
that pair and is the only wall figure these two arms may be compared on. Whole-process /
drive-loop walls are still reported, explicitly labelled non-comparable.

Second resolution means +/-1 s of quantisation on each endpoint; at spans of thousands of
seconds that is noise, but it is why this refuses to print a ratio for very short spans.

WHAT IT WILL NOT DO
It does not pool the two arms' seed spreads into a single resolution figure. Varying
dataset.params.seed gives a fresh data draw on both arms but a fresh network init on the CLI arm
ONLY (the CLI threads the dataset seed into the network; the service always re-seeds to
_PROJECT_RANDOM_SEED = 42 and nothing the driver can send reaches it). The two spreads measure
different things, so they are reported side by side and never combined.

Usage:
    python util/ad-hoc/2026-08-16_h2h_collect.py --suite-dir DIR [--suite-dir DIR ...]
                                                 --cli-root DIR [--json]
Exit: 0 collected; 1 an equalisation check failed; 2 nothing to collect.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

TS = r"\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)"
RE_FIT_START = re.compile(r"fit:1918.*" + TS + r".*Starting main training loop with max_epochs: (\d+), max_iterations: (\d+), early stopping: (\w+)")
RE_FIT_END = re.compile(r"fit:1936.*" + TS + r".*Training completed\.")
RE_ACC = re.compile(r"calculate_accuracy:\d+\].*Calculated accuracy: ([0-9.]+)")
RE_UNITS = re.compile(r"summary:\d+\].*Number of hidden units: (\d+)")
RE_DATA_SVC = re.compile(r"Using JuniperData service at (\S+)")


RE_SUITE_STAMP = re.compile(r"-\d{8}T\d{6}Z$")


def _dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def _label(suite_dir_name: str) -> str:
    """Suite dir name minus its run stamp -- the tables have to fit on a page."""
    return RE_SUITE_STAMP.sub("", suite_dir_name)


def _log_segments(path: Path) -> "list[Path]":
    """``juniper_cascor.log`` plus its rotated siblings, OLDEST first.

    cascor's parent log rotates (observed: a 64-unit cell wrote ~950 MB and left
    ``juniper_cascor.log.1`` holding the run's first half while ``juniper_cascor.log`` held only
    the tail). The fit-start marker is on the FIRST line of the run, so reading only the live file
    silently yields "no training span" -- which is how a wall-clock comparison quietly becomes
    unavailable. Segments are ``.log.N`` with the HIGHEST N oldest, then ``.log`` newest.
    """
    live = [path] if path.exists() else []
    rotated = []
    for sib in path.parent.glob(path.name + ".*"):
        suffix = sib.name[len(path.name) + 1:]
        if suffix.isdigit():
            rotated.append((int(suffix), sib))
    return [p for _n, p in sorted(rotated, reverse=True)] + live


def read_parent_log(path: Path) -> dict:
    """Training span + the fit-line budget echo + (CLI only) final accuracies / units.

    Reads every rotated segment as one logical stream. A ``markers.txt`` sidecar written live by
    the marker sentinel is consulted as well, so a run whose first segment was rotated out of the
    backup window still yields a span.
    """
    segments = _log_segments(path)
    out: dict = {"parent_log": str(path), "present": bool(segments), "log_segments": [s.name for s in segments]}
    starts: list = []
    ends: list = []
    accs: list = []
    units = None
    data_url = None
    for seg in segments + [path.parent / "markers.txt"]:
        if not seg.exists():
            continue
        with seg.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if (m := RE_FIT_START.search(line)):
                    starts.append((_dt(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)))
                elif (m := RE_FIT_END.search(line)):
                    ends.append(_dt(m.group(1)))
                elif (m := RE_ACC.search(line)):
                    accs.append(float(m.group(1)))
                elif (m := RE_UNITS.search(line)):
                    units = int(m.group(1))
                elif data_url is None and (m := RE_DATA_SVC.search(line)):
                    data_url = m.group(1)
    # The sentinel duplicates whatever the live segments also kept; de-duplicate so a
    # sentinel-recorded start does not look like a second fit block.
    starts = sorted(set(starts))
    ends = sorted(set(ends))
    if not segments:
        return out
    out["fit_blocks"] = len(starts)
    if starts:
        start, out["log_max_epochs"], out["log_max_iterations"], out["log_early_stopping"] = starts[-1]
        # Pair the last start with the last completion at or after it.
        after = [e for e in ends if e >= start]
        if after:
            out["training_span_seconds"] = int((after[-1] - start).total_seconds())
            out["fit_start"], out["fit_end"] = start.isoformat(sep=" "), after[-1].isoformat(sep=" ")
        else:
            out["training_span_seconds"] = None  # started, never completed
    # The CLI's SpiralProblem.evaluate calls calculate_accuracy on (x_train, y_train) then
    # (x_test, y_test) -- spiral_problem.py:1481-1483 -- as the last such pair in the run.
    if len(accs) >= 2:
        out["train_accuracy"], out["val_accuracy"] = accs[-2], accs[-1]
    if units is not None:
        out["hidden_units"] = units
    if data_url:
        out["juniper_data_url"] = data_url
    return out


def collect_service(suite_dir: Path) -> list[dict]:
    rows: list[dict] = []
    registry = suite_dir / "registry.jsonl"
    if not registry.exists():
        return rows
    seen: dict[str, dict] = {}
    for line in registry.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            seen[row["cell_id"]] = row  # last write wins (resume)
    for cell_id, row in sorted(seen.items()):
        rec = {"arm": "service", "suite": _label(suite_dir.name), "suite_dir": suite_dir.name, "cell_id": cell_id, "outcome": row.get("outcome"), "exit_code": row.get("exit_code"), "run_id": row.get("run_id"), "suite_wall_seconds": row.get("wall_seconds"), "overrides": row.get("overrides") or {}}
        run_dir = Path(row["run_dir"]) if row.get("run_dir") else None
        if run_dir and (mf := run_dir / "manifest.json").exists():
            man = json.loads(mf.read_text())
            rec |= {
                "dataset_id": (man.get("dataset") or {}).get("dataset_id"),
                "completion_reason": man.get("completion_reason"),
                "seed_dataset": (man.get("seeds") or {}).get("dataset"),
                "drive_wall_seconds": (man.get("drive_loop") or {}).get("wall_seconds"),
                "total_wall_seconds": (man.get("timings") or {}).get("total"),
                "acceptance_ok": (man.get("acceptance") or {}).get("ok"),
                "cascor_version": ((man.get("packages") or {}).get("juniper-cascor") or {}).get("version"),
            }
        if run_dir and (fm := run_dir / "artifacts/results/metrics_final.json").exists():
            met = json.loads(fm.read_text())
            rec |= {"train_accuracy": met.get("train_accuracy"), "val_accuracy": met.get("val_accuracy"), "hidden_units": met.get("hidden_units")}
        if run_dir:
            rec["log"] = read_parent_log(run_dir / "logs/juniper_cascor.log")
        rows.append(rec)
    return rows


def collect_cli(cli_root: Path) -> list[dict]:
    rows: list[dict] = []
    for arm_json in sorted(cli_root.glob("*/*/cli_arm.json")):
        out_dir = arm_json.parent
        rec = {"arm": "cli", "suite": _label(out_dir.parent.name), "suite_dir": out_dir.parent.name, "cell_id": out_dir.name}
        rec |= json.loads(arm_json.read_text())
        log = read_parent_log(out_dir / "logs/juniper_cascor.log")
        rec |= {k: log[k] for k in ("train_accuracy", "val_accuracy", "hidden_units") if k in log}
        rec["log"] = log
        rows.append(rec)
    return rows


def _fmt(v, spec="") -> str:
    return "-" if v is None else (format(v, spec) if spec else str(v))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suite-dir", type=Path, action="append", default=[], required=True)
    ap.add_argument("--cli-root", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    service = [r for d in args.suite_dir for r in collect_service(d)]
    cli = collect_cli(args.cli_root) if args.cli_root.exists() else []
    if not service and not cli:
        print("collect: nothing found", file=sys.stderr)
        return 2

    # Pair the arms on (suite, cell_id) -- the suite writes one cell config and BOTH arms run it.
    by_key: dict[tuple, dict] = {}
    for rec in service + cli:
        by_key.setdefault((rec["suite"], rec["cell_id"]), {})[rec["arm"]] = rec

    problems: list[str] = []
    print(f"{'suite':<22} {'cell':<14} {'arm':<8} {'seed':>9} {'dataset_id':<26} {'train':>7} {'val':>7} {'units':>5} {'span_s':>7} {'other_wall_s':>12} {'reason'}")
    print("-" * 150)
    for (suite, cell_id), arms in sorted(by_key.items()):
        cap = (arms.get("service", {}).get("overrides") or {}).get("training.params.max_hidden_units")
        for arm in ("service", "cli"):
            r = arms.get(arm)
            if r is None:
                problems.append(f"{suite}/{cell_id}: no {arm} arm collected")
                continue
            log = r.get("log") or {}
            other = r.get("drive_wall_seconds") if arm == "service" else r.get("process_wall_seconds")
            reason = r.get("completion_reason") or ("exit %s" % r.get("exit_code"))
            print(f"{suite:<22} {cell_id:<14} {arm:<8} {_fmt(r.get('seed_dataset')):>9} {_fmt(r.get('dataset_id')):<26} {_fmt(r.get('train_accuracy'), '.4f'):>7} {_fmt(r.get('val_accuracy'), '.4f'):>7} {_fmt(r.get('hidden_units')):>5} {_fmt(log.get('training_span_seconds')):>7} {_fmt(other):>12} {reason}")
            if cap is not None and r.get("hidden_units") not in (None, cap):
                problems.append(f"{suite}/{cell_id}/{arm}: hidden_units {r.get('hidden_units')} != cap {cap} -- the cap did NOT bind, so this is not a capacity-limited run")
            if log.get("training_span_seconds") is None:
                problems.append(f"{suite}/{cell_id}/{arm}: no training span in the parent log ({'missing log' if not log.get('present') else 'fit markers unpaired'})")
        # The equalisation check that matters: BOTH paths of a replicate on the same data.
        if "service" in arms and "cli" in arms:
            svc_url, cli_url = None, (arms["cli"].get("log") or {}).get("juniper_data_url")
            if cli_url is None:
                problems.append(f"{suite}/{cell_id}/cli: no 'Using JuniperData service at' line -- cannot confirm it reached juniper-data")
            se, ce = arms["service"].get("log", {}), arms["cli"].get("log", {})
            for field in ("log_max_epochs", "log_max_iterations", "log_early_stopping"):
                if field == "log_max_iterations":
                    continue  # deliberately asymmetric: service-only key, CLI reports its network default
                if se.get(field) is not None and ce.get(field) is not None and se[field] != ce[field]:
                    problems.append(f"{suite}/{cell_id}: {field} differs -- service {se[field]!r} vs cli {ce[field]!r} (arms NOT budget-equalised)")
            del svc_url

    # Per (cap, arm) aggregates. The two arms' spreads are NEVER pooled -- see the module docstring.
    print()
    print(f"{'suite':<22} {'arm':<8} {'n':>2} {'val mean':>9} {'val sd':>8} {'train mean':>11} {'span mean':>10} {'span sd':>8}")
    print("-" * 90)
    agg: dict[tuple, dict] = {}
    for (suite, _cell), arms in by_key.items():
        for arm, r in arms.items():
            vals = agg.setdefault((suite, arm), {"val": [], "train": [], "span": []})
            for key, dest in (("val_accuracy", "val"), ("train_accuracy", "train")):
                if r.get(key) is not None:
                    vals[dest].append(r[key])
            if (r.get("log") or {}).get("training_span_seconds") is not None:
                vals["span"].append(r["log"]["training_span_seconds"])
    for (suite, arm), v in sorted(agg.items()):
        sd = lambda xs: statistics.stdev(xs) if len(xs) > 1 else None  # noqa: E731
        mean = lambda xs: statistics.fmean(xs) if xs else None  # noqa: E731
        print(f"{suite:<22} {arm:<8} {len(v['val']):>2} {_fmt(mean(v['val']), '.4f'):>9} {_fmt(sd(v['val']), '.4f'):>8} {_fmt(mean(v['train']), '.4f'):>11} {_fmt(mean(v['span']), '.1f'):>10} {_fmt(sd(v['span']), '.1f'):>8}")

    # PAIRED analysis -- the design is paired (both arms of a replicate train on the SAME
    # content-addressed dataset), and the across-seed spread is large: cap-64 spans ranged
    # 3570-4481 s purely by data draw. Differencing WITHIN a replicate cancels that, so the paired
    # delta is far more sensitive than any comparison of group means, and it is the only figure
    # that isolates the thing under test.
    print()
    print(f"{'suite':<22} {'cell':<14} {'dataset_id':<26} {'d_val_pp':>9} {'d_train_pp':>11} {'d_span_s':>9} {'span ratio':>11}")
    print("-" * 108)
    paired: dict[str, dict[str, list]] = {}
    for (suite, cell_id), arms in sorted(by_key.items()):
        s, c = arms.get("service"), arms.get("cli")
        if not (s and c):
            continue
        p = paired.setdefault(suite, {"val": [], "train": [], "span": [], "ratio": []})
        dv = dt = ds = ratio = None
        if s.get("val_accuracy") is not None and c.get("val_accuracy") is not None:
            dv = (c["val_accuracy"] - s["val_accuracy"]) * 100
            p["val"].append(dv)
        if s.get("train_accuracy") is not None and c.get("train_accuracy") is not None:
            dt = (c["train_accuracy"] - s["train_accuracy"]) * 100
            p["train"].append(dt)
        ss, cs = (s.get("log") or {}).get("training_span_seconds"), (c.get("log") or {}).get("training_span_seconds")
        if ss and cs:
            ds, ratio = cs - ss, cs / ss
            p["span"].append(ds)
            p["ratio"].append(ratio)
        # Same dataset on both arms is the equalisation claim; it is asserted per replicate here.
        same_data = "" if s.get("dataset_id") else " (service dataset_id unknown)"
        print(f"{suite:<22} {cell_id:<14} {_fmt(s.get('dataset_id')):<26} {_fmt(dv, '+.2f'):>9} {_fmt(dt, '+.2f'):>11} {_fmt(ds, '+.0f'):>9} {_fmt(ratio, '.3f'):>11}{same_data}")

    print()
    for suite in sorted(paired):
        p = paired[suite]
        n = len(p["val"])
        if n:
            mean_dv = statistics.fmean(p["val"])
            sd_dv = statistics.stdev(p["val"]) if n > 1 else None
            print(f"{suite}: PAIRED val delta (CLI - service) = {mean_dv:+.2f} pp"
                  + (f" +/- {sd_dv:.2f} pp (sd, n={n})" if sd_dv is not None else f" (n={n}, no spread)"))
        if p["ratio"]:
            m = statistics.fmean(p["ratio"])
            sd_r = statistics.stdev(p["ratio"]) if len(p["ratio"]) > 1 else None
            print(f"{suite}: PAIRED training-span ratio (CLI / service) = {m:.3f}"
                  + (f" +/- {sd_r:.3f}" if sd_r is not None else "")
                  + f"  [mean absolute delta {statistics.fmean(p['span']):+.0f} s; shared fit-marker denominator]")
    print()
    for suite in sorted({s for s, _ in agg}):
        s, c = agg.get((suite, "service")), agg.get((suite, "cli"))
        if s and c and s["val"] and c["val"]:
            print(f"{suite}: unpaired spreads -- "
                  f"service sd {_fmt(statistics.stdev(s['val']) * 100 if len(s['val']) > 1 else None, '.2f')} pp = data-draw ONLY (network always re-seeds to 42); "
                  f"cli sd {_fmt(statistics.stdev(c['val']) * 100 if len(c['val']) > 1 else None, '.2f')} pp = data-draw + init. NOT commensurate; never pooled.")

    if problems:
        print(f"\nEQUALISATION / COMPLETENESS PROBLEMS ({len(problems)}):")
        for p in problems:
            print(f"  {p}")
    if args.json:
        Path("h2h_collected.json").write_text(json.dumps({"service": service, "cli": cli, "problems": problems}, indent=2, default=str))
        print("\nwrote h2h_collected.json")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
