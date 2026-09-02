#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Round-2 review instrument: simulate the RECOMMENDED F1 fix (clearable=True) the same
#                way F2 (the unary guard) was simulated, so the two are compared on ONE instrument.
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-02_canopy_clearable_f1_simulation.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-02
# Last Modified: 2026-09-02
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     ``2026-09-02_canopy_unary_guard_simulation.py`` measured family F2 and reported 5
#     reachable-but-invalid states in the container case (S3). The evaluation then FLIPPED its
#     recommendation to family F1 (``clearable=True``) WITHOUT running F1 through the same
#     instrument. This script closes that gap.
#
#     Transition relation, mirroring the shipped handlers:
#       pick-dataset   from (m, d): every option NOT disabled by gated_dataset_options
#                      composed with apply_availability_gate  -> (m, v)
#       clear-dataset  F1 only, from (m, d) with d != None    -> (m, BOTTOM)
#                      (gate_dataset_options reads the dataset as State :2609, so a clear does
#                       NOT re-fire the gate; the cleared value persists)
#       pick-model     from (m, d): _build_model_selection_table:3018/3033 makes EVERY Select
#                      button enabled when d is None; otherwise model_reason(m', d) is None.
#                      Landing applies _gate_dataset_options_handler:2704-2706's snap.
#
#     Two invalid-state definitions are reported, because the documents silently switch between
#     them:
#       STRICT   invalid = Reach - {(m,d) : compatible(d,m)}          (the definition the F2 table used)
#       DESIGN   invalid = Reach - ({(m,d) : compatible(d,m)} u {(m,BOTTOM)})
#                (the design's "BOTTOM is compatible with every model" universal-cut-vertex claim)
#
#     Also reported: START-LIVE-AT-BOTTOM -- states where _update_button_appearance_handler:7206
#     would leave Start ENABLED (it keys on model_is_trainable only, with NO dataset input) while
#     no dataset is committed. The design's Section 2 asserts BOTTOM "is not trainable".
#
#####################################################################################################################################################################################################
# Notes:
#     - Run with the JuniperCanopy1 environment (JuniperCanopy is DEPRECATED).
#     - Simulation only: no canopy file is modified.
#
#####################################################################################################################################################################################################

"""Measure family F1 (clearable=True) on the same instrument that measured family F2."""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import replace
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")
sys.path.insert(0, str(CANOPY_SRC))

import model_registry as mr  # noqa: E402

BOTTOM = None  # the cleared dataset value the dropdown writes when clearable=True


def reachable(models, datasets, *, clearable: bool, unary: bool = False, unavailable: frozenset = frozenset()):
    """BFS the (model, dataset) graph. ``clearable`` adds the F1 clear edge and the BOTTOM value."""

    def enabled_datasets(model_key):
        spec = next((m for m in models if m.key == model_key), None)
        out = []
        for dataset in datasets:
            if spec is not None and mr.dataset_reason(dataset, spec) is not None:
                continue
            if dataset.value in unavailable:
                continue
            out.append(dataset.value)
        return out

    def selectable_models(dataset_value):
        # _build_model_selection_table:3018 -> dataset = get_dataset_spec(v) if v else None
        #                            :3033 -> reason = model_reason(...) if dataset is not None else None
        # => a cleared dataset enables EVERY Select button.
        if dataset_value is BOTTOM:
            return [m.key for m in models]
        dataset = next((d for d in datasets if d.value == dataset_value), None)
        out = []
        for model in models:
            if unary:
                if any(mr.compatible(d, model) for d in datasets):
                    out.append(model.key)
            elif dataset is not None and mr.model_reason(model, dataset) is None:
                out.append(model.key)
        return out

    def snap(model_key, current):
        enabled = enabled_datasets(model_key)
        if current in enabled or not enabled:
            return current
        return enabled[0]

    start = (models[0].key, datasets[0].value)
    seen = {start}
    queue = deque([start])
    while queue:
        model_key, dataset_value = queue.popleft()
        for nxt in enabled_datasets(model_key):
            if (model_key, nxt) not in seen:
                seen.add((model_key, nxt))
                queue.append((model_key, nxt))
        if clearable and dataset_value is not BOTTOM:
            if (model_key, BOTTOM) not in seen:
                seen.add((model_key, BOTTOM))
                queue.append((model_key, BOTTOM))
        for nxt in selectable_models(dataset_value):
            landed = (nxt, snap(nxt, dataset_value))
            if landed not in seen:
                seen.add(landed)
                queue.append(landed)

    compatible = {(m.key, d.value) for m in models for d in datasets if mr.compatible(d, m)}
    return seen, compatible


def _fmt(states):
    return sorted((m, "BOTTOM" if d is BOTTOM else d) for m, d in states)


def report(title, models, datasets, *, clearable, unary=False, unavailable=frozenset()):
    seen, compat = reachable(models, datasets, clearable=clearable, unary=unary, unavailable=unavailable)
    missing = sorted(compat - seen)
    strict_invalid = _fmt(s for s in seen if s not in compat)
    design_invalid = _fmt(s for s in seen if s not in compat and s[1] is not BOTTOM)
    start_live_at_bottom = _fmt(s for s in seen if s[1] is BOTTOM and mr.model_is_trainable(s[0], models=tuple(models)))
    print(f"\n--- {title} ---")
    print(f"  reachable {len(seen)} | compatible {len(compat)}")
    print(f"  COMPATIBLE BUT UNREACHABLE      : {missing if missing else 'none'}")
    print(f"  REACHABLE-INVALID  (STRICT defn): {len(strict_invalid)}  {strict_invalid if strict_invalid else 'none'}")
    print(f"  REACHABLE-INVALID  (DESIGN defn): {len(design_invalid)}  {design_invalid if design_invalid else 'none'}")
    print(f"  START LIVE, NO DATASET COMMITTED: {len(start_live_at_bottom)}  {start_live_at_bottom if start_live_at_bottom else 'none'}")
    return missing, strict_invalid, design_invalid


def main() -> int:
    models, datasets = list(mr.MODELS), list(mr.DATASET_TYPES)
    print("models   :", [m.key for m in models])
    print("datasets :", [d.value for d in datasets])

    print("\n=== REAL SEEDS (2-component partition) ===")
    report("T1  today: joint guard, clearable=False", models, datasets, clearable=False)
    report("T2  F1: clearable=True, all available", models, datasets, clearable=True)
    report("T3  F1: clearable=True, equities_seq UNAVAILABLE (container case, = S3)", models, datasets, clearable=True, unavailable=frozenset({"equities_seq"}))
    report("T4  F1: clearable=True, ALL datasets unavailable (G1d)", models, datasets, clearable=True, unavailable=frozenset(d.value for d in datasets))
    report("T3b F2: unary guard, equities_seq UNAVAILABLE (reproduce S3 for comparison)", models, datasets, clearable=False, unary=True, unavailable=frozenset({"equities_seq"}))

    print("\n\n=== SYNTHETIC 3-COMPONENT REGISTRY (G1c) ===")
    d3 = datasets + [replace(datasets[0], value="graph_ds", label="Graph", task_type="classification", ndim=4, temporal="none")]
    m3 = models + [replace(models[0], key="gnn", label="GNN", input_ndim=frozenset({4}), family="gnn")]
    report("T5  today: joint guard", m3, d3, clearable=False)
    report("T6  F1: clearable=True", m3, d3, clearable=True)
    report("T7  F1: clearable=True, graph_ds UNAVAILABLE", m3, d3, clearable=True, unavailable=frozenset({"graph_ds"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
