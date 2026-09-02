#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Simulate the candidate unary-guard fix and re-measure reachability
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-02_canopy_unary_guard_simulation.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-02
# Last Modified: 2026-09-02
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     Measures the candidate remediation BEFORE it is written into a design document. The candidate
#     replaces the model-table Select guard (dashboard_manager.py:3050, currently
#     ``disabled=not is_compatible`` -- a JOINT predicate reading the peer dataset) with a UNARY
#     predicate depending only on the model's own axis: disable only when the model has no
#     compatible dataset at all.
#
#     Three scenarios are measured against the real registry seeds:
#       S1  today (joint guard)                     -- expected: 5 of 6 reachable
#       S2  unary guard, all datasets available      -- the claimed fix
#       S3  unary guard, equities_seq UNAVAILABLE    -- the juniper-deploy container case, where the
#           availability gate disables the LMU's only dataset and the snap's ``or not enabled``
#           branch returns no_update
#
#     S3 is the case Lane B raised and the reason the fix is necessary-but-not-sufficient. It is
#     measured here rather than argued.
#
#     A 3-COMPONENT synthetic registry is also exercised, because with the shipped 2-component
#     partition a naive implementation of almost any proposal passes.
#
#####################################################################################################################################################################################################
# Notes:
#     - Run with the JuniperCanopy1 environment (JuniperCanopy is DEPRECATED).
#     - Simulation only: no canopy file is modified.
#
#####################################################################################################################################################################################################

"""Measure the unary-guard candidate fix against the real seeds and a 3-component registry."""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import replace
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")
sys.path.insert(0, str(CANOPY_SRC))

import model_registry as mr  # noqa: E402


def reachable(models, datasets, *, unary: bool, unavailable: frozenset[str] = frozenset()):
    """BFS the (model, dataset) state graph under the chosen Select-guard policy.

    ``unary``      -- False reproduces today's joint guard; True applies the candidate fix.
    ``unavailable`` -- dataset values the availability gate disables (composed AFTER compatibility,
                       matching dataset_schema.apply_availability_gate).
    """

    def enabled_datasets(model_key):
        spec = next((m for m in models if m.key == model_key), None)
        out = []
        for dataset in datasets:
            if spec is not None and mr.dataset_reason(dataset, spec) is not None:
                continue  # disabled by the compatibility gate
            if dataset.value in unavailable:
                continue  # disabled by the availability gate
            out.append(dataset.value)
        return out

    def selectable_models(dataset_value):
        dataset = next((d for d in datasets if d.value == dataset_value), None)
        out = []
        for model in models:
            if unary:
                # Candidate: depends only on the model's own axis.
                if any(mr.compatible(d, model) for d in datasets):
                    out.append(model.key)
            else:
                # Today: joint predicate against the peer's current value.
                if dataset is not None and mr.model_reason(model, dataset) is None:
                    out.append(model.key)
        return out

    def snap(model_key, current):
        """Reproduce _gate_dataset_options_handler's repair, including its no_update branch."""
        enabled = enabled_datasets(model_key)
        if current in enabled or not enabled:
            return current  # <- the 'or not enabled' branch: stays on an invalid dataset
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
        for nxt in selectable_models(dataset_value):
            landed = (nxt, snap(nxt, dataset_value))
            if landed not in seen:
                seen.add(landed)
                queue.append(landed)

    compatible = {(m.key, d.value) for m in models for d in datasets if mr.compatible(d, m)}
    return seen, compatible


def report(title, models, datasets, *, unary, unavailable=frozenset()):
    seen, compat = reachable(models, datasets, unary=unary, unavailable=unavailable)
    missing = sorted(compat - seen)
    invalid = sorted(s for s in seen if s not in compat)
    print(f"\n--- {title} ---")
    print(f"  reachable {len(seen)} | compatible {len(compat)}")
    print(f"  COMPATIBLE BUT UNREACHABLE : {missing if missing else 'none'}")
    print(f"  REACHABLE BUT INVALID      : {invalid if invalid else 'none'}")
    return missing, invalid


def main() -> int:
    models, datasets = list(mr.MODELS), list(mr.DATASET_TYPES)

    print("=== REAL SEEDS (2-component partition) ===")
    report("S1  today: joint guard", models, datasets, unary=False)
    report("S2  candidate: unary guard, all available", models, datasets, unary=True)
    report("S3  candidate: unary guard, equities_seq UNAVAILABLE (container case)", models, datasets, unary=True, unavailable=frozenset({"equities_seq"}))

    # A 3rd component: with only 2 components a naive fix can pass by accident.
    print("\n\n=== SYNTHETIC 3-COMPONENT REGISTRY ===")
    d3 = datasets + [replace(datasets[0], value="graph_ds", label="Graph", task_type="classification", ndim=4, temporal="none")]
    m3 = models + [replace(models[0], key="gnn", label="GNN", input_ndim=frozenset({4}), family="gnn")]
    report("S4  today: joint guard", m3, d3, unary=False)
    report("S5  candidate: unary guard", m3, d3, unary=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
