#!/usr/bin/env python3
"""plots_recurrence.py -- the SS8.2 recurrence plot set, rendered client-side (Wave 2.5, closes G-5).

Project: juniper-ml
Sub-Project: cascor + recurrence CLI test/validation/experimentation program
Application: experiment driver plot renderers (util/experiments/)
Author: Paul Calnon
License: MIT License

The recurrence service exposes no plotting at all (gap G-5), so the driver renders the
SS8.2 set from the payloads it already holds: the fetched 3-D NPZ artifact
(``{X,y,dt,target_dt}_{split}`` keys -- ``juniper_data/generators/_sequence.py:252-256``;
equities adds ``y_reg_{split}``), the ``POST /v1/predict`` response, and the
``POST /v1/crossval`` response. There is deliberately NO training-history plot: it is
API-infeasible today -- ``TrainResponse`` exposes only ``final_metrics`` / ``n_epochs`` /
``stopped_reason``, no per-epoch series (SS8.2 note).

Target-key rule (SS8.2): ``y_{split}`` for the synthetics; ``y_reg_{split}`` ONLY for
``equities_seq`` -- when both exist (equities: ``y`` is the classification target,
``y_reg`` the regression one) the regression driver wants ``y_reg``, so
:func:`resolve_target_key` prefers it.

Conventions mirror ``plots_cascor.py``: pure functions (payload in, one PNG out), a
``ValueError`` means no-renderable-data (the driver records a per-plot skip, not a run
failure), matplotlib pinned to the headless ``Agg`` backend at import, and the module is
loaded lazily by ``run_experiment.py`` so the driver stays importable without matplotlib.

``util/`` is not pre-commit-lint-gated; ``tests/test_run_experiment.py`` is the gate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (backend must be pinned before pyplot)
import numpy as np  # noqa: E402

_DPI = 120
_MAX_OVERVIEW_WINDOWS = 6
_MAX_TABLE_METRICS = 12
_MAX_FOLD_METRICS = 4


def load_npz_bytes(raw: bytes) -> Dict[str, np.ndarray]:
    """Materialise a fetched NPZ artifact (the juniper-data ``/artifact`` body) into arrays."""
    import io

    with np.load(io.BytesIO(raw), allow_pickle=False) as bundle:
        return {key: bundle[key] for key in bundle.files}


def _finish(fig: "plt.Figure", out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


def resolve_target_key(npz: Mapping[str, Any], split: str) -> str:
    """SS8.2 target-key rule: prefer ``y_reg_{split}`` (equities regression target) over ``y_{split}``."""
    for prefix in ("y_reg", "y"):
        key = f"{prefix}_{split}"
        if key in npz:
            return key
    raise ValueError(f"dataset carries neither y_reg_{split} nor y_{split}")


def _flatten_outputs(values: Any, label: str) -> np.ndarray:
    """Collapse an ``(n,)`` / ``(n, 1)`` / ``(n, k)`` output array to the 1-D first-output series."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError(f"{label} is empty")
    if arr.ndim > 1:
        arr = arr.reshape(arr.shape[0], -1)[:, 0]
    return arr.reshape(-1)


def render_dataset_overview(npz: Mapping[str, Any], split: str, title: str, out_path: Path) -> Path:
    """SS8.2 ``dataset_overview.png``: a few sampled windows of ``X`` (feature 0) with the target marked."""
    x_key = f"X_{split}"
    if x_key not in npz:
        raise ValueError(f"dataset carries no {x_key}")
    x = np.asarray(npz[x_key])
    if x.ndim != 3 or x.shape[0] == 0:
        raise ValueError(f"{x_key} is not a non-empty 3-D (windows, lookback, features) array: shape {x.shape}")
    y = _flatten_outputs(npz[resolve_target_key(npz, split)], f"target for {split}")
    n_windows, lookback = x.shape[0], x.shape[1]
    picks = np.unique(np.linspace(0, n_windows - 1, min(_MAX_OVERVIEW_WINDOWS, n_windows)).astype(int))
    fig, ax = plt.subplots(figsize=(8, 5))
    for idx in picks:
        line = ax.plot(np.arange(lookback), x[idx, :, 0], alpha=0.75, label=f"window {int(idx)}")
        if idx < len(y):
            ax.scatter([lookback], [y[idx]], marker="*", s=80, color=line[0].get_color(), zorder=3)
    ax.set_xlabel("window step (feature 0 shown; * = target at horizon)")
    ax.set_ylabel("value")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    return _finish(fig, out_path)


def render_dt_histogram(npz: Mapping[str, Any], split: str, title: str, out_path: Path) -> Path:
    """SS8.2 ``dt_histogram.png``: per-step Delta-t distribution + the ``target_dt`` horizon -- the irregularity signature."""
    dt_key, target_key = f"dt_{split}", f"target_dt_{split}"
    if dt_key not in npz or target_key not in npz:
        raise ValueError(f"dataset carries no {dt_key}/{target_key} (not a Delta-t sequence artifact)")
    dt = np.asarray(npz[dt_key], dtype=float).reshape(-1)
    dt = dt[dt > 0]  # each window's first step is 0.0 by construction (_sequence.py)
    target_dt = np.asarray(npz[target_key], dtype=float).reshape(-1)
    if dt.size == 0 and target_dt.size == 0:
        raise ValueError("dt arrays are empty")
    fig, (ax_step, ax_target) = plt.subplots(1, 2, figsize=(10, 4.5))
    ax_step.hist(dt, bins=30, color="tab:blue", alpha=0.8)
    ax_step.set_xlabel("per-step Delta-t (window-leading zeros dropped)")
    ax_step.set_ylabel("count")
    ax_target.hist(target_dt, bins=20, color="tab:orange", alpha=0.8)
    ax_target.set_xlabel("target_dt (forecast horizon)")
    fig.suptitle(title)
    return _finish(fig, out_path)


def render_forecast_vs_truth(predictions: Any, y_true: Any, title: str, out_path: Path) -> Path:
    """SS8.2 ``forecast_vs_truth.png``: predicted vs actual over the held-out window index."""
    pred = _flatten_outputs(predictions, "predictions")
    truth = _flatten_outputs(y_true, "targets")
    if len(pred) != len(truth):
        raise ValueError(f"prediction count {len(pred)} != target count {len(truth)}")
    idx = np.arange(len(pred))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(idx, truth, color="tab:blue", label="actual", alpha=0.85)
    ax.plot(idx, pred, color="tab:red", label="predicted", alpha=0.85, linestyle="--", marker=".", markersize=4)
    ax.set_xlabel("held-out window index")
    ax.set_ylabel("target value")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    return _finish(fig, out_path)


def render_residuals(predictions: Any, y_true: Any, target_dt: Optional[Any], title: str, out_path: Path) -> Path:
    """SS8.2 ``residuals.png``: residual series + histogram (+ residual-vs-``target_dt`` scatter when available)."""
    pred = _flatten_outputs(predictions, "predictions")
    truth = _flatten_outputs(y_true, "targets")
    if len(pred) != len(truth):
        raise ValueError(f"prediction count {len(pred)} != target count {len(truth)}")
    residuals = pred - truth
    dt_arr: Optional[np.ndarray] = None
    if target_dt is not None:
        candidate = np.asarray(target_dt, dtype=float).reshape(-1)
        if len(candidate) == len(residuals):
            dt_arr = candidate
    n_panels = 3 if dt_arr is not None else 2
    fig, axes = plt.subplots(1, n_panels, figsize=(4.5 * n_panels, 4.5))
    axes[0].plot(np.arange(len(residuals)), residuals, color="tab:purple", alpha=0.85)
    axes[0].axhline(0.0, color="black", linewidth=0.8)
    axes[0].set_xlabel("held-out window index")
    axes[0].set_ylabel("residual (predicted - actual)")
    axes[1].hist(residuals, bins=20, color="tab:purple", alpha=0.8)
    axes[1].set_xlabel("residual")
    axes[1].set_ylabel("count")
    if dt_arr is not None:
        axes[2].scatter(dt_arr, residuals, s=14, alpha=0.7, color="tab:green")
        axes[2].axhline(0.0, color="black", linewidth=0.8)
        axes[2].set_xlabel("target_dt")
        axes[2].set_ylabel("residual")
    fig.suptitle(title)
    return _finish(fig, out_path)


def render_crossval_folds(crossval: Mapping[str, Any], title: str, out_path: Path) -> Path:
    """SS8.2 ``crossval_folds.png``: per-fold eval-metric bars with the aggregate line (CrossValResponse folds)."""
    folds = crossval.get("folds")
    if not isinstance(folds, list) or not folds:
        raise ValueError("crossval payload carries no folds")
    aggregate = crossval.get("eval_aggregate") if isinstance(crossval.get("eval_aggregate"), Mapping) else {}
    std = crossval.get("eval_std") if isinstance(crossval.get("eval_std"), Mapping) else {}
    metric_names = sorted(name for name, value in aggregate.items() if isinstance(value, (int, float)))
    if not metric_names:
        first_eval = folds[0].get("eval_metrics") if isinstance(folds[0], Mapping) else None
        if isinstance(first_eval, Mapping):
            metric_names = sorted(name for name, value in first_eval.items() if isinstance(value, (int, float)))
    metric_names = metric_names[:_MAX_FOLD_METRICS]
    if not metric_names:
        raise ValueError("crossval payload carries no numeric eval metrics")
    fig, axes = plt.subplots(len(metric_names), 1, figsize=(8, 3.2 * len(metric_names)), squeeze=False)
    fold_ids = [int(fold.get("fold", pos)) for pos, fold in enumerate(folds)]
    for row, metric in enumerate(metric_names):
        ax = axes[row][0]
        values = [float(fold.get("eval_metrics", {}).get(metric)) if isinstance(fold.get("eval_metrics", {}).get(metric), (int, float)) else np.nan for fold in folds]
        ax.bar([str(fold_id) for fold_id in fold_ids], values, color="tab:blue", alpha=0.8)
        agg = aggregate.get(metric)
        if isinstance(agg, (int, float)):
            label = f"aggregate {float(agg):.4g}"
            spread = std.get(metric)
            if isinstance(spread, (int, float)):
                label += f" +/- {float(spread):.3g}"
            ax.axhline(float(agg), color="tab:red", linestyle="--", linewidth=1.2, label=label)
            ax.legend(loc="best", fontsize=8)
        ax.set_xlabel("fold")
        ax.set_ylabel(metric)
    fig.suptitle(title)
    return _finish(fig, out_path)


def render_metrics_table(final_metrics: Mapping[str, Any], crossval: Optional[Mapping[str, Any]], title: str, out_path: Path) -> Path:
    """SS8.2 ``metrics_table.png``: the train ``final_metrics`` plus CV aggregate +/- std, as a rendered table."""
    rows: List[List[str]] = []
    for name in sorted(final_metrics)[:_MAX_TABLE_METRICS]:
        value = final_metrics[name]
        if isinstance(value, (int, float)):
            rows.append([f"train {name}", f"{float(value):.6g}"])
    if isinstance(crossval, Mapping):
        aggregate = crossval.get("eval_aggregate") if isinstance(crossval.get("eval_aggregate"), Mapping) else {}
        std = crossval.get("eval_std") if isinstance(crossval.get("eval_std"), Mapping) else {}
        for name in sorted(aggregate)[:_MAX_TABLE_METRICS]:
            value = aggregate[name]
            if isinstance(value, (int, float)):
                spread = std.get(name)
                rendered = f"{float(value):.6g}"
                if isinstance(spread, (int, float)):
                    rendered += f" +/- {float(spread):.3g}"
                rows.append([f"cv {name}", rendered])
    if not rows:
        raise ValueError("no numeric metrics to tabulate")
    fig, ax = plt.subplots(figsize=(6, 0.5 + 0.4 * len(rows)))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=["metric", "value"], loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.3)
    ax.set_title(title, pad=12)
    return _finish(fig, out_path)
