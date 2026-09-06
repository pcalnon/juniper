#!/usr/bin/env python3
"""plots_cascor.py -- the SS8.1 cascor plot set, rendered client-side (Wave 2.4).

Project: juniper-ml
Sub-Project: cascor + recurrence CLI test/validation/experimentation program
Application: experiment driver plot renderers (util/experiments/)
Author: Paul Calnon
License: MIT License

Service-mode cascor runs keep the model in another process, so the driver plots
client-side from the JSON/array payloads it already collects (plan SS8.1) -- this
module NEVER imports cascor (``cascor_plotter`` imports torch, which would drag the
whole app into the driver's process and break the driver's env-independence; the
in-repo ``CascadeCorrelationPlotter`` remains the direct-CLI path).

Each renderer is a pure function: validated payload in, one PNG written to ``out_path``.
Renderers raise ``ValueError`` when the payload carries no renderable data (e.g. the
scalar eval block is all-null because ``JUNIPER_CASCOR_EVAL_METRICS_ENABLED`` was off);
``run_experiment.py`` maps that to a recorded per-plot skip, not a run failure.

matplotlib is imported at module import time on the headless ``Agg`` backend --
``run_experiment.py`` loads this module lazily (only when ``outputs.plots`` requests
something), so the driver itself stays importable without matplotlib.

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


def _class_labels(y: Any) -> np.ndarray:
    """Collapse a target array to 1-D integer class labels (one-hot ``(N, C)`` -> argmax)."""
    arr = np.asarray(y)
    if arr.ndim == 2 and arr.shape[1] > 1:
        return arr.argmax(axis=1)
    return arr.reshape(-1).astype(int)


def render_dataset(npz: Mapping[str, Any], title: str, out_path: Path) -> Path:
    """SS8.1 ``dataset.png``: 2-feature scatter coloured by class, every partition marked.

    ``val`` is drawn, not skipped. This plotted train and test only, so on a three-way
    artifact the validation rows were silently absent from the picture -- roughly a tenth
    of the dataset missing from the one artifact an operator uses to eyeball what was
    trained on, with nothing in the legend saying so. It stays presence-conditional
    because a legacy two-way artifact has no val partition at all.
    """
    x_train = np.asarray(npz["X_train"])
    x_test = np.asarray(npz["X_test"])
    if x_train.ndim != 2 or x_train.shape[1] != 2:
        raise ValueError(f"dataset plot requires 2-feature data, got shape {x_train.shape}")
    layers = [(x_train, _class_labels(npz["y_train"]), "o", "train")]
    if "X_val" in npz and "y_val" in npz and np.asarray(npz["X_val"]).shape[0]:
        layers.append((np.asarray(npz["X_val"]), _class_labels(npz["y_val"]), "^", "val"))
    layers.append((x_test, _class_labels(npz["y_test"]), "x", "test"))
    fig, ax = plt.subplots(figsize=(7, 6))
    for arr, labels, marker, suffix in layers:
        for cls in np.unique(labels):
            points = arr[labels == cls]
            ax.scatter(points[:, 0], points[:, 1], marker=marker, s=14, alpha=0.7, label=f"class {int(cls)} ({suffix})")
    ax.set_xlabel("feature 0")
    ax.set_ylabel("feature 1")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    return _finish(fig, out_path)


def render_decision_boundary(boundary: Mapping[str, Any], npz: Optional[Mapping[str, Any]], title: str, out_path: Path) -> Path:
    """SS8.1 ``decision_boundary.png``: the ``GET /v1/decision-boundary`` prediction grid + overlaid training samples.

    Payload contract (manager.get_decision_boundary, manager.py:4284-4291): ``x_range`` /
    ``y_range`` / ``resolution`` / ``grid_x`` / ``grid_y`` / ``predictions`` (all RxR lists).
    """
    grid_x = np.asarray(boundary["grid_x"], dtype=float)
    grid_y = np.asarray(boundary["grid_y"], dtype=float)
    predictions = np.asarray(boundary["predictions"], dtype=float)
    if predictions.size == 0:
        raise ValueError("decision-boundary payload carries an empty prediction grid")
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.contourf(grid_x, grid_y, predictions, alpha=0.35, cmap="coolwarm")
    if npz is not None:
        x_train = np.asarray(npz["X_train"])
        labels = _class_labels(npz["y_train"])
        for cls in np.unique(labels):
            points = x_train[labels == cls]
            ax.scatter(points[:, 0], points[:, 1], s=10, alpha=0.8, label=f"class {int(cls)}")
        ax.legend(loc="best", fontsize=8)
    x_range = boundary.get("x_range")
    y_range = boundary.get("y_range")
    if isinstance(x_range, (list, tuple)) and len(x_range) == 2:
        ax.set_xlim(float(x_range[0]), float(x_range[1]))
    if isinstance(y_range, (list, tuple)) and len(y_range) == 2:
        ax.set_ylim(float(y_range[0]), float(y_range[1]))
    ax.set_xlabel("feature 0")
    ax.set_ylabel("feature 1")
    ax.set_title(title)
    return _finish(fig, out_path)


def render_training_history(rows: List[Mapping[str, Any]], title: str, out_path: Path) -> Path:
    """SS8.1 ``training_history.png``: loss + accuracy over the metrics rows, hidden-unit-insertion markers.

    Rows are the ``/v1/metrics/history`` buffer dicts (monitor.on_epoch_end, monitor.py:301-320):
    ``loss`` / ``accuracy`` / ``hidden_units`` (+ nullable validation twins). Rendered in buffer
    order -- the ``kind`` mix (training_step vs throttled output_epoch) makes the raw ``epoch``
    field ambiguous as an x-axis, and buffer order is chronological.
    """
    usable = [row for row in rows if isinstance(row, Mapping) and isinstance(row.get("loss"), (int, float))]
    if not usable:
        raise ValueError("metrics history carries no renderable rows")
    x = np.arange(1, len(usable) + 1)
    loss = np.asarray([float(row["loss"]) for row in usable])
    accuracy = np.asarray([float(row["accuracy"]) if isinstance(row.get("accuracy"), (int, float)) else np.nan for row in usable])
    hidden = [int(row["hidden_units"]) if isinstance(row.get("hidden_units"), (int, float)) else None for row in usable]

    fig, ax_loss = plt.subplots(figsize=(8, 5))
    ax_loss.plot(x, loss, color="tab:red", label="loss")
    ax_loss.set_xlabel("metrics row (chronological)")
    ax_loss.set_ylabel("loss", color="tab:red")
    ax_acc = ax_loss.twinx()
    ax_acc.plot(x, accuracy, color="tab:blue", label="accuracy")
    ax_acc.set_ylabel("accuracy", color="tab:blue")
    for idx in range(1, len(hidden)):
        if hidden[idx] is not None and hidden[idx - 1] is not None and hidden[idx] > hidden[idx - 1]:
            ax_loss.axvline(x[idx], color="tab:green", linestyle=":", alpha=0.6)
    ax_loss.set_title(f"{title} (green: hidden-unit insertion)")
    return _finish(fig, out_path)


def render_candidate_correlation(series_rows: List[Mapping[str, str]], title: str, out_path: Path) -> Path:
    """SS8.1 ``candidate_correlation.png``: the poll-loop ``metrics_series.csv`` correlation gauge over time.

    The series is the SOLE source -- ``/v1/metrics/history`` rows carry no correlation field
    (it otherwise surfaces only in the WS ``cascade_add`` event). Rows are ``csv.DictReader``
    dicts of the driver's own CSV; empty correlation cells (sampling degraded, G-3) are skipped.
    """
    times: List[float] = []
    values: List[float] = []
    hidden: List[Optional[int]] = []
    for row in series_rows:
        raw = (row.get("juniper_cascor_candidate_correlation") or "").strip()
        if not raw:
            continue
        try:
            values.append(float(raw))
            times.append(float(row.get("ts_unix") or 0.0))
        except ValueError:
            continue
        raw_hidden = (row.get("current_hidden_units") or "").strip()
        hidden.append(int(float(raw_hidden)) if raw_hidden else None)
    if not values:
        raise ValueError("metrics_series.csv carries no candidate_correlation samples (metrics sampling degraded? G-3)")
    t0 = times[0]
    elapsed = [t - t0 for t in times]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(elapsed, values, marker="o", color="tab:purple")
    for idx in range(1, len(hidden)):
        if hidden[idx] is not None and hidden[idx - 1] is not None and hidden[idx] > hidden[idx - 1]:
            ax.axvline(elapsed[idx], color="tab:green", linestyle=":", alpha=0.6)
    ax.set_xlabel("elapsed seconds (poll loop)")
    ax.set_ylabel("juniper_cascor_candidate_correlation")
    ax.set_title(f"{title} (green: hidden-unit insertion)")
    return _finish(fig, out_path)


def render_eval_metrics(metrics_final: Mapping[str, Any], title: str, out_path: Path) -> Path:
    """SS8.1 ``eval_metrics.png``: F1 / precision / recall / ROC-AUC bars from the ``/v1/metrics`` scalar block."""
    pairs = [(name, metrics_final.get(name)) for name in ("f1", "precision", "recall", "roc_auc")]
    present: Dict[str, float] = {name: float(value) for name, value in pairs if isinstance(value, (int, float))}
    if not present:
        raise ValueError("no scalar eval metrics present (JUNIPER_CASCOR_EVAL_METRICS_ENABLED off, or none computed)")
    fig, ax = plt.subplots(figsize=(6, 4.5))
    names = list(present)
    ax.bar(names, [present[name] for name in names], color="tab:blue", alpha=0.8)
    ax.set_ylim(0.0, 1.05)
    for idx, name in enumerate(names):
        ax.text(idx, present[name] + 0.02, f"{present[name]:.3f}", ha="center", fontsize=9)
    ax.set_ylabel("score")
    ax.set_title(title)
    return _finish(fig, out_path)
