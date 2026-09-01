#!/usr/bin/env python3
"""stats_summary.py -- the SS8.3 ``stats.json`` + ``summary.md`` renderers (Wave 2.6).

Project: juniper-ml
Sub-Project: cascor + recurrence CLI test/validation/experimentation program
Application: experiment driver statistics renderers (util/experiments/)
Author: Paul Calnon
License: MIT License

Builds the SS8.3 statistics summary for a single run -- ``artifacts/results/stats.json``
plus the human-readable ``artifacts/results/summary.md`` -- from data the driver already
holds: the assembled SS13.4 manifest dict, the collected ``/v1/metrics`` scalar block
(cascor), the driver's own ``metrics_series.csv`` rows (cascor -- the SOLE source for
candidate correlation and step-duration statistics; neither exists in
``/v1/metrics/history`` rows, SS6.3), and the train/crossval payloads (recurrence).

Honesty notes baked into the output:

* ``training_step_duration`` p50/p95 are computed over the PER-POLL MEAN step duration
  (delta-sum / delta-count between consecutive samples of the histogram's ``_sum`` /
  ``_count`` exposition) -- true per-step quantiles are not recoverable from a sum/count
  pair, and the stats say so rather than pretending otherwise.
* "best candidate correlation per round" groups the sampled correlation gauge by the
  concurrently-sampled ``current_hidden_units`` value -- a round boundary is a
  hidden-unit increment.
* Degraded-mode notes (SS8.3 provenance/health) surface metrics-sampling errors,
  collection errors, per-plot skips, and disabled eval metrics instead of hiding them.

Stdlib only (loaded by ``run_experiment.py`` through the same sibling-module file-path
loader as the plot modules, but with no matplotlib/numpy dependency, so stats render on
any host the driver runs on). ``util/`` is not pre-commit-lint-gated;
``tests/test_run_experiment.py`` is the gate.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

STATS_SCHEMA = "juniper-experiment-stats/1"

CORRELATION_COLUMN = "juniper_cascor_candidate_correlation"
HIDDEN_COLUMN = "current_hidden_units"
STEP_SUM_COLUMN = "juniper_cascor_training_step_duration_seconds_sum"
STEP_COUNT_COLUMN = "juniper_cascor_training_step_duration_seconds_count"


def _to_float(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def percentile(values: List[float], q: float) -> Optional[float]:
    """Linear-interpolation percentile (q in 0..100) over an unsorted sample list."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (q / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def correlation_per_round(series_rows: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Best sampled candidate correlation per growth round (round = a ``current_hidden_units`` value)."""
    best: Dict[int, float] = {}
    for row in series_rows:
        value = _to_float(row.get(CORRELATION_COLUMN))
        hidden = _to_float(row.get(HIDDEN_COLUMN))
        if value is None or hidden is None:
            continue
        key = int(hidden)
        if key not in best or value > best[key]:
            best[key] = value
    rounds = [{"hidden_units": key, "best_correlation": best[key]} for key in sorted(best)]
    return {
        "per_round": rounds,
        "max": max(best.values()) if best else None,
        "samples": sum(1 for row in series_rows if _to_float(row.get(CORRELATION_COLUMN)) is not None),
    }


def step_duration_stats(series_rows: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Per-poll mean step-duration stats from the sampled histogram ``_sum``/``_count`` pair.

    A (delta-sum / delta-count) sample exists only for polls where the count advanced;
    p50/p95 are over those per-poll means -- true per-step quantiles are NOT recoverable
    from a sum/count exposition, and the ``basis`` field says so.
    """
    per_poll_means: List[float] = []
    prev_sum: Optional[float] = None
    prev_count: Optional[float] = None
    last_sum: Optional[float] = None
    last_count: Optional[float] = None
    for row in series_rows:
        cur_sum = _to_float(row.get(STEP_SUM_COLUMN))
        cur_count = _to_float(row.get(STEP_COUNT_COLUMN))
        if cur_sum is None or cur_count is None:
            continue
        last_sum, last_count = cur_sum, cur_count
        if prev_sum is not None and prev_count is not None and cur_count > prev_count:
            per_poll_means.append((cur_sum - prev_sum) / (cur_count - prev_count))
        prev_sum, prev_count = cur_sum, cur_count
    overall_mean = (last_sum / last_count) if last_sum is not None and last_count else None
    return {
        "basis": "per-poll mean (delta-sum/delta-count); true per-step quantiles are not recoverable from a sum/count exposition",
        "total_steps": int(last_count) if last_count is not None else None,
        "overall_mean_seconds": overall_mean,
        "p50_seconds": percentile(per_poll_means, 50.0),
        "p95_seconds": percentile(per_poll_means, 95.0),
        "poll_samples": len(per_poll_means),
    }


def _dataset_block(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    dataset = manifest.get("dataset") if isinstance(manifest.get("dataset"), Mapping) else {}
    meta = dataset.get("meta") if isinstance(dataset.get("meta"), Mapping) else {}
    if meta.get("sequence"):
        shapes: Dict[str, Any] = {
            "kind": "sequence",
            "n_windows": meta.get("n_samples"),
            "lookback": meta.get("lookback"),
            "n_features": meta.get("n_features"),
            "n_train": meta.get("n_train"),
            "n_test": meta.get("n_test"),
        }
    else:
        shapes = {
            "kind": "tabular",
            "n_train": meta.get("n_train"),
            "n_test": meta.get("n_test"),
            "n_features": meta.get("n_features"),
            "n_classes": meta.get("n_classes"),
        }
    return {
        "dataset_id": dataset.get("dataset_id"),
        "generator": dataset.get("generator"),
        "generator_version": dataset.get("version"),
        "split": dataset.get("split"),
        "params": dataset.get("params"),
        "task_type": meta.get("task_type"),
        "shapes": shapes,
        "class_distribution": meta.get("class_distribution"),
    }


def _degraded_notes(manifest: Mapping[str, Any], kind: str, metrics_final: Optional[Mapping[str, Any]]) -> List[str]:
    notes: List[str] = []
    drive_loop = manifest.get("drive_loop") if isinstance(manifest.get("drive_loop"), Mapping) else {}
    sampling_errors = drive_loop.get("metrics_sampling_errors")
    if isinstance(sampling_errors, int) and sampling_errors > 0:
        notes.append(f"/metrics sampling degraded on {sampling_errors} poll(s) (G-3: is JUNIPER_CASCOR_METRICS_ENABLED=true?)")
    for err in manifest.get("collect_errors") or []:
        if isinstance(err, Mapping):
            notes.append(f"collect: {err.get('artifact')} failed ({err.get('error')})")
    driver = manifest.get("driver") if isinstance(manifest.get("driver"), Mapping) else {}
    plots = driver.get("plots") if isinstance(driver.get("plots"), Mapping) else {}
    for skip in plots.get("skipped") or []:
        if isinstance(skip, Mapping):
            notes.append(f"plot {skip.get('name')} skipped: {skip.get('reason')}")
    if kind == "cascor" and isinstance(metrics_final, Mapping):
        eval_block = metrics_final.get("eval_metrics")
        if isinstance(eval_block, Mapping) and eval_block.get("enabled") is False:
            notes.append("scalar eval metrics disabled (JUNIPER_CASCOR_EVAL_METRICS_ENABLED)")
    g6 = manifest.get("g6_shape_check")
    if isinstance(g6, Mapping) and not g6.get("ok"):
        notes.append("G-6 shape check FAILED: loaded network input width does not match the requested dataset")
    return notes


def build_stats(
    manifest: Mapping[str, Any],
    kind: str,
    series_rows: Optional[List[Mapping[str, Any]]] = None,
    metrics_final: Optional[Mapping[str, Any]] = None,
    train_summary: Optional[Mapping[str, Any]] = None,
    crossval: Optional[Mapping[str, Any]] = None,
    train_config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the SS8.3 stats dict from the manifest + kind-specific collected payloads."""
    git_block = {}
    for repo, info in (manifest.get("git") or {}).items():
        if isinstance(info, Mapping):
            git_block[repo] = {"head_sha": info.get("head_sha"), "dirty": info.get("dirty")} if "head_sha" in info else {"error": info.get("error")}
    packages = {name: (info.get("version") if isinstance(info, Mapping) else info) for name, info in (manifest.get("packages") or {}).items()}

    stats: Dict[str, Any] = {
        "schema": STATS_SCHEMA,
        "identity": {
            "run_id": manifest.get("run_id"),
            "experiment": (manifest.get("experiment") or {}).get("name"),
            "description": (manifest.get("experiment") or {}).get("description"),
            "config_sha256": manifest.get("config_sha256"),
            "seeds": manifest.get("seeds"),
            "git": git_block,
            "packages": packages,
        },
        "dataset": _dataset_block(manifest),
        "outcome": {
            "outcome": manifest.get("outcome"),
            "acceptance": manifest.get("acceptance"),
            "wall_seconds": (manifest.get("timings") or {}).get("total"),
            "timings": manifest.get("timings"),
        },
        "provenance": {
            "metrics_scraped": manifest.get("metrics_scraped"),
            "degraded_notes": _degraded_notes(manifest, kind, metrics_final),
        },
    }

    if kind == "cascor":
        rows = series_rows or []
        final = metrics_final if isinstance(metrics_final, Mapping) else {}
        stats["cascor"] = {
            "final": {name: final.get(name) for name in ("epoch", "train_loss", "train_accuracy", "val_loss", "val_accuracy", "hidden_units")},
            "eval_scalars": {name: final.get(name) for name in ("f1", "precision", "recall", "roc_auc")},
            "completion_reason": manifest.get("completion_reason"),
            "candidate_correlation": correlation_per_round(rows),
            "training_step_duration": step_duration_stats(rows),
        }
    else:
        train = train_summary if isinstance(train_summary, Mapping) else {}
        cfg = train_config if isinstance(train_config, Mapping) else {}
        cv_block = None
        if isinstance(crossval, Mapping):
            cv_block = {
                "n_folds": crossval.get("n_folds"),
                "task_type": crossval.get("task_type"),
                "eval_aggregate": crossval.get("eval_aggregate"),
                "eval_std": crossval.get("eval_std"),
                "folds": [
                    {"fold": fold.get("fold"), "eval_metrics": fold.get("eval_metrics"), "n_epochs": fold.get("n_epochs")}
                    for fold in (crossval.get("folds") or [])
                    if isinstance(fold, Mapping)
                ],
            }
        stats["recurrence"] = {
            "final_metrics": train.get("final_metrics"),
            "n_epochs": train.get("n_epochs"),
            "stopped_reason": train.get("stopped_reason"),
            "dataset_descriptor": train.get("dataset"),
            "theta": {"value": cfg.get("theta"), "note": "data-driven (resolved from per-window elapsed time)" if cfg.get("theta") is None else "explicit"},
            "readout": {"rung": cfg.get("readout") or "linear", "hyperparameters": {key: value for key, value in cfg.items() if key not in {"readout"} and value is not None}},
            "crossval": cv_block,
        }
    return stats


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _metric_lines(block: Optional[Mapping[str, Any]]) -> List[str]:
    if not isinstance(block, Mapping):
        return ["(none)"]
    lines = [f"- {name}: {_fmt(value)}" for name, value in sorted(block.items()) if value is not None]
    return lines or ["(none)"]


def render_summary_md(stats: Mapping[str, Any]) -> str:
    """Render the human-readable SS8.3 ``summary.md`` from a :func:`build_stats` dict."""
    identity = stats.get("identity") or {}
    dataset = stats.get("dataset") or {}
    outcome = stats.get("outcome") or {}
    provenance = stats.get("provenance") or {}
    shapes = dataset.get("shapes") or {}
    lines: List[str] = [
        f"# Run summary — {identity.get('run_id')}",
        "",
        f"**Experiment**: {identity.get('experiment')} — {identity.get('description') or '(no description)'}",
        f"**Outcome**: {outcome.get('outcome')} (acceptance ok: {(outcome.get('acceptance') or {}).get('ok')}) in {_fmt(outcome.get('wall_seconds'))}s",
        f"**Config SHA-256**: `{identity.get('config_sha256')}`",
        f"**Seeds**: {identity.get('seeds')}",
        "",
        "## Dataset",
        "",
        f"- generator: {dataset.get('generator')} v{dataset.get('generator_version')} (task: {dataset.get('task_type')})",
        f"- dataset_id: `{dataset.get('dataset_id')}`",
        f"- shapes: {', '.join(f'{key}={_fmt(val)}' for key, val in shapes.items() if val is not None)}",
    ]
    if dataset.get("class_distribution"):
        lines.append(f"- class distribution: {dataset.get('class_distribution')}")
    lines += ["", "## Timings", ""]
    lines += [f"- {phase}: {_fmt(seconds)}s" for phase, seconds in sorted((outcome.get("timings") or {}).items())]

    if "cascor" in stats:
        cascor = stats["cascor"] or {}
        lines += ["", "## cascor", "", "### Final metrics", ""]
        lines += _metric_lines(cascor.get("final"))
        lines += ["", "### Eval scalars", ""]
        lines += _metric_lines(cascor.get("eval_scalars"))
        correlation = cascor.get("candidate_correlation") or {}
        lines += ["", "### Candidate correlation (per growth round; from metrics_series.csv)", ""]
        rounds = correlation.get("per_round") or []
        lines += [f"- hidden_units={entry.get('hidden_units')}: best {_fmt(entry.get('best_correlation'))}" for entry in rounds] or ["(no samples)"]
        duration = cascor.get("training_step_duration") or {}
        lines += ["", "### Training step duration", ""]
        lines += [
            f"- total steps: {_fmt(duration.get('total_steps'))}, overall mean: {_fmt(duration.get('overall_mean_seconds'))}s",
            f"- p50: {_fmt(duration.get('p50_seconds'))}s, p95: {_fmt(duration.get('p95_seconds'))}s ({duration.get('basis')})",
        ]
        if cascor.get("completion_reason"):
            lines.append(f"- completion reason: {cascor.get('completion_reason')}")

    if "recurrence" in stats:
        recurrence = stats["recurrence"] or {}
        lines += ["", "## recurrence", "", "### Train", ""]
        lines += _metric_lines(recurrence.get("final_metrics"))
        lines += [
            f"- n_epochs: {_fmt(recurrence.get('n_epochs'))}, stopped_reason: {recurrence.get('stopped_reason')}",
            f"- theta: {(recurrence.get('theta') or {}).get('value')} ({(recurrence.get('theta') or {}).get('note')})",
            f"- readout: {(recurrence.get('readout') or {}).get('rung')} {(recurrence.get('readout') or {}).get('hyperparameters')}",
        ]
        cv_block = recurrence.get("crossval")
        lines += ["", "### Cross-validation", ""]
        if isinstance(cv_block, Mapping):
            lines.append(f"- {cv_block.get('n_folds')} folds ({cv_block.get('task_type')}); aggregate:")
            lines += [f"  - {name}: {_fmt(value)} ± {_fmt((cv_block.get('eval_std') or {}).get(name))}" for name, value in sorted((cv_block.get("eval_aggregate") or {}).items())]
        else:
            lines.append("(disabled or failed)")

    lines += ["", "## Provenance / health", ""]
    scraped = provenance.get("metrics_scraped") or {}
    # Report BOTH facts, and never let the local one stand in for the remote one. A target file
    # written is not a scrape confirmed: five bridged PF-1 runs wrote the file and Prometheus held
    # no series for any of them. ``scrape_confirmed`` is tri-state — None means the question could
    # not be asked (Prometheus unreachable), which is not the same finding as "nothing was scraped".
    # ``present`` is the pre-2026-09-01 key name, read as a fallback so old manifests still render.
    written = scraped.get("target_file_written", scraped.get("present"))
    confirmed = scraped.get("scrape_confirmed", "n/a (pre-2026-09-01 manifest)")
    lines.append(f"- grafana bridge: {scraped.get('grafana_bridge')}, target file written: {written}, scrape confirmed: {confirmed}")
    if scraped.get("reason"):
        lines.append(f"  - {scraped['reason']}")
    notes = provenance.get("degraded_notes") or []
    if notes:
        lines += ["- degraded-mode notes:"] + [f"  - {note}" for note in notes]
    else:
        lines.append("- degraded-mode notes: none")
    lines += ["", "## Git provenance", ""]
    for repo, info in sorted((identity.get("git") or {}).items()):
        if isinstance(info, Mapping) and info.get("head_sha"):
            lines.append(f"- {repo}: `{info['head_sha'][:12]}`{' (DIRTY — not reproducible)' if info.get('dirty') else ''}")
        else:
            lines.append(f"- {repo}: (unavailable)")
    return "\n".join(lines) + "\n"
