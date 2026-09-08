"""Index-based walk-forward fold generation (shape-agnostic).

The folds are returned as integer index arrays into the ordered whole-dataset arrays, so the same
function serves 2-D tabular ``(n, F)`` and 3-D sequence ``(n, T, F)`` data identically -- the
executor slices ``X`` / ``y`` / ``aux`` by these indices (decision D-CV-4: folds are derived
client-side over the whole dataset; no ``juniper-data`` change is required for v1). Since decision
11 of the partition design (juniper-ml
``notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`` §9.5;
juniper-data#369) the producer no longer emits a ``*_full`` family: the caller rebuilds the whole
dataset from the ``train`` / ``val`` / ``test`` partitions -- ``juniper_recurrence_model.data.
derive_full_split`` is the reference implementation, and its ORDER matters, because these folds
slice by row index. A legacy artifact that still carries ``*_full`` may be used as-is.

The clamp/ordering conventions mirror ``juniper-data``'s ``core/split.py:temporal_split_index``
(the single-cut chronological boundary this generalizes to many folds), so a caller that already
trusts that boundary sees consistent behavior here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

__all__ = ["Fold", "walk_forward_folds"]


@dataclass(frozen=True)
class Fold:
    """One walk-forward fold: integer indices into the ordered full arrays.

    ``train_idx`` always precedes ``eval_idx`` in time order (an ``embargo`` gap may separate
    them), so slicing ``X[train_idx]`` / ``X[eval_idx]`` never leaks future information backward.
    """

    train_idx: np.ndarray
    eval_idx: np.ndarray


def walk_forward_folds(
    n_samples: int,
    *,
    n_folds: int,
    scheme: Literal["expanding", "rolling"] = "expanding",
    min_train: int | None = None,
    embargo: int = 0,
    order: np.ndarray | None = None,
    groups: np.ndarray | None = None,
) -> list[Fold]:
    """Generate time-ordered walk-forward folds over ``n_samples`` rows.

    The series is cut into ``n_folds + 1`` equal blocks of ``fold_size = n_samples // (n_folds + 1)``;
    fold ``i`` (0-indexed) evaluates on block ``i + 1`` and trains on everything legally before it.

    Args:
        n_samples: number of rows in the ordered full arrays.
        n_folds: number of folds to produce (>= 1).
        scheme: ``"expanding"`` (train grows from the start each fold) or ``"rolling"`` (train is a
            fixed-length trailing window).
        min_train: for ``"expanding"``, the minimum train size -- folds with fewer training rows are
            skipped; for ``"rolling"``, the fixed train-window length (defaults to ``fold_size``).
        embargo: number of rows dropped before the start of eval to prevent leakage across the
            boundary (>= 0). With ``groups=None`` this is a single global gap of ``embargo`` rows (in
            ``order`` rank); with ``groups`` supplied it is applied **per group** (see ``groups``).
        order: optional 1-D sort key of length ``n_samples`` (e.g. ``window_end_date``); folds are
            built over the order-sorted positions but the returned indices reference the *original*
            row positions, so the caller slices the unsorted arrays directly. ``None`` assumes the
            arrays are already chronologically ordered.
        groups: optional 1-D per-sample entity id of length ``n_samples`` (e.g. ``ticker_code``) for
            multi-entity ("panel") data. ``None`` (default) is single-series and behaves exactly as
            before. When supplied, folds stay **pooled and date-ordered** (train = all entities'
            windows before each cut; eval = the next block across all entities), but the ``embargo``
            purge is applied **per group**: from each fold's train side, the last ``embargo`` windows
            *of each entity* (by that entity's own ``order``) are dropped. This prevents same-entity
            look-back overlap at the boundary, which a single global-rank embargo does not -- on a
            panel, a global gap of ``embargo`` rows mostly drops *other* entities' windows. Set
            ``embargo`` to at least the look-back length (expressed in windows) to fully purge a
            per-window-step look-back.

    Returns:
        A list of :class:`Fold`, earliest eval block first.

    Raises:
        ValueError: on ``n_samples < 2``, ``n_folds < 1``, ``embargo < 0``, an unknown ``scheme``, an
            ``order`` / ``groups`` whose length != ``n_samples``, too few samples for ``n_folds``, or
            when no fold satisfies the constraints (every fold empty after ``embargo`` / ``min_train``).
    """
    if n_samples < 2:
        raise ValueError(f"n_samples must be >= 2, got {n_samples}")
    if n_folds < 1:
        raise ValueError(f"n_folds must be >= 1, got {n_folds}")
    if embargo < 0:
        raise ValueError(f"embargo must be >= 0, got {embargo}")
    if scheme not in ("expanding", "rolling"):
        raise ValueError(f"scheme must be 'expanding' or 'rolling', got {scheme!r}")

    if order is not None:
        order = np.asarray(order)
        if order.shape[0] != n_samples:
            raise ValueError(f"order length {order.shape[0]} != n_samples {n_samples}")
        ordered = np.argsort(order, kind="stable")
    else:
        ordered = np.arange(n_samples)

    if groups is not None:
        groups = np.asarray(groups)
        if groups.shape[0] != n_samples:
            raise ValueError(f"groups length {groups.shape[0]} != n_samples {n_samples}")

    fold_size = n_samples // (n_folds + 1)
    if fold_size < 1:
        raise ValueError(f"not enough samples ({n_samples}) for {n_folds} folds; need >= {n_folds + 1}")

    window = min_train if (scheme == "rolling" and min_train is not None) else fold_size

    folds: list[Fold] = []
    for i in range(n_folds):
        eval_start = (i + 1) * fold_size
        eval_stop = (i + 2) * fold_size
        eval_pos = ordered[eval_start:eval_stop]
        if eval_pos.shape[0] == 0:
            continue

        if groups is None:
            # Single global embargo gap (in `order` rank) between train end and eval start.
            train_end = eval_start - embargo
            train_start = 0 if scheme == "expanding" else max(0, train_end - window)
            if train_end - train_start < 1:
                continue
            if scheme == "expanding" and min_train is not None and (train_end - train_start) < min_train:
                continue
            train_pos = ordered[train_start:train_end]
        else:
            # Pooled date-ordered train candidate (no global gap), then a PER-GROUP embargo purge:
            # drop, for each entity, its last `embargo` windows before the cut (by `order`).
            cand_start = 0 if scheme == "expanding" else max(0, eval_start - window)
            train_candidate = ordered[cand_start:eval_start]
            if embargo > 0 and train_candidate.shape[0] > 0:
                cand_groups = groups[train_candidate]
                keep = np.ones(train_candidate.shape[0], dtype=bool)
                for group_id in np.unique(cand_groups):
                    members = np.flatnonzero(cand_groups == group_id)  # ascending == `order` order
                    keep[members[-embargo:]] = False  # this entity's most-recent-before-cut windows
                train_pos = train_candidate[keep]
            else:
                train_pos = train_candidate
            if train_pos.shape[0] < 1:
                continue
            if scheme == "expanding" and min_train is not None and train_pos.shape[0] < min_train:
                continue

        folds.append(Fold(train_idx=np.asarray(train_pos), eval_idx=np.asarray(eval_pos)))

    if not folds:
        raise ValueError("no valid folds produced; reduce n_folds / embargo / min_train relative to n_samples")
    return folds
