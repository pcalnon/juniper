#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Reachability probe for the juniper-canopy model/dataset selection state graph
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-02_canopy_selection_reachability.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-02
# Last Modified: 2026-09-02
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     Independent instrument for the model/dataset selection catch-22. Builds the DIRECTED
#     state-transition graph over (model_key, dataset_value) pairs strictly from what the two
#     shipped UI gates admit -- gated_dataset_options() for the sidebar dropdown, and the per-row
#     Select `disabled` flag from _build_model_selection_table() for the model modal -- then
#     computes the set reachable from the default state by breadth-first search.
#
#     This is the reconciler's own measurement (independent-agent consensus procedure section 5.2:
#     re-derive anything load-bearing). It deliberately reads the REAL registry seeds rather than
#     fixtures, so a newly seeded model or dataset changes the answer.
#
#####################################################################################################################################################################################################
# Notes:
#     - Instrument adequacy: the probe prints the full edge set, not only the verdict, so a
#       "0 edges" result is distinguishable from a harness that cannot construct an edge at all.
#     - Run with the JuniperCanopy1 environment (JuniperCanopy is DEPRECATED).
#
#####################################################################################################################################################################################################

"""Compute the reachable (model, dataset) set for canopy's selection UI."""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")
sys.path.insert(0, str(CANOPY_SRC))

import model_registry as mr  # noqa: E402


def dataset_edges(model_key: str) -> list[str]:
    """Dataset values the sidebar dropdown would let a user pick while ``model_key`` is active."""
    return [option["value"] for option in mr.gated_dataset_options(model_key) if not option.get("disabled")]


def model_edges(dataset_value: str) -> list[str]:
    """Model keys whose modal Select button is ENABLED while ``dataset_value`` is active.

    Mirrors dashboard_manager._build_model_selection_table's ``disabled=not is_compatible`` rule
    (model_reason(...) is None <=> compatible), without importing the Dash layer.
    """
    dataset = mr.get_dataset_spec(dataset_value)
    if dataset is None:
        return [model.key for model in mr.MODELS]
    return [model.key for model in mr.MODELS if mr.model_reason(model, dataset) is None]


def main() -> int:
    all_pairs = [(model.key, dataset.value) for model in mr.MODELS for dataset in mr.DATASET_TYPES]
    compatible_pairs = [(model.key, dataset.value) for model in mr.MODELS for dataset in mr.DATASET_TYPES if mr.compatible(dataset, model)]

    start = (mr.DEFAULT_MODEL_KEY, mr.DEFAULT_DATASET_TYPE)
    seen: set[tuple[str, str]] = {start}
    queue: deque[tuple[str, str]] = deque([start])
    edges: list[tuple[tuple[str, str], tuple[str, str], str]] = []

    while queue:
        model_key, dataset_value = queue.popleft()
        for nxt in dataset_edges(model_key):
            target = (model_key, nxt)
            if target != (model_key, dataset_value):
                edges.append(((model_key, dataset_value), target, "pick-dataset"))
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        for nxt in model_edges(dataset_value):
            target = (nxt, dataset_value)
            if target != (model_key, dataset_value):
                edges.append(((model_key, dataset_value), target, "pick-model"))
                if target not in seen:
                    seen.add(target)
                    queue.append(target)

    print(f"models        : {[m.key for m in mr.MODELS]}")
    print(f"datasets      : {[d.value for d in mr.DATASET_TYPES]}")
    print(f"start state   : {start}")
    print(f"total pairs   : {len(all_pairs)}")
    print(f"COMPATIBLE    : {len(compatible_pairs)} -> {sorted(compatible_pairs)}")
    print(f"REACHABLE     : {len(seen)} -> {sorted(seen)}")
    print(f"edges found   : {len(edges)} (instrument adequacy: a non-zero edge count proves the probe CAN report reachability)")
    for src, dst, kind in edges:
        print(f"  {src} --{kind}--> {dst}")

    unreachable = sorted(set(compatible_pairs) - seen)
    print()
    print(f"COMPATIBLE BUT UNREACHABLE: {len(unreachable)} -> {unreachable}")
    return 1 if unreachable else 0


if __name__ == "__main__":
    raise SystemExit(main())
