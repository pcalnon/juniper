#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Re-derive two lone findings about canopy's model/dataset selection deadlock
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-02_canopy_snap_and_null_state.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-02
# Last Modified: 2026-09-02
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     Reconciler re-derivation (independent-agent consensus procedure section 5.2) of two findings
#     each reported by exactly ONE agent, both load-bearing for the remediation design:
#
#       F-A: the dataset auto-snap branch in _gate_dataset_options_handler is UNREACHABLE on the
#            model-change path -- a model is only selectable when it is already compatible with the
#            current dataset, so the current dataset is never disabled when the handler fires.
#            If true, the feature's only conflict-resolution code has never executed in production.
#
#       F-B: the "cleared dataset" (dataset_value=None) state that design D4 / section 5.5 specified
#            is ALREADY fully implemented downstream; only clearable=False makes it unreachable.
#
#     F-A is established by exhaustive enumeration over the real seeds rather than by inspection.
#
#####################################################################################################################################################################################################
# Notes:
#     - Run with the JuniperCanopy1 environment (JuniperCanopy is DEPRECATED).
#     - Reads the shipped code only; mutates nothing.
#
#####################################################################################################################################################################################################

"""Re-derive the dead-snap and null-dataset-state findings against the real registry seeds."""

from __future__ import annotations

import sys
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")
sys.path.insert(0, str(CANOPY_SRC))

import model_registry as mr  # noqa: E402


def enabled_datasets(model_key: str) -> list[str]:
    """Dataset values the sidebar dropdown leaves selectable while ``model_key`` is active."""
    return [option["value"] for option in mr.gated_dataset_options(model_key) if not option.get("disabled")]


def selectable_models(dataset_value: str) -> list[str]:
    """Model keys whose modal Select button is ENABLED while ``dataset_value`` is active."""
    dataset = mr.get_dataset_spec(dataset_value)
    if dataset is None:
        return [model.key for model in mr.MODELS]
    return [model.key for model in mr.MODELS if mr.model_reason(model, dataset) is None]


def main() -> int:
    print("=== F-A: can the dataset auto-snap EVER fire on a model change? ===")
    print("The handler snaps only when the current dataset is NOT in the enabled set.")
    print("A model change can only originate from a model whose Select button was enabled,")
    print("which requires that model to be compatible with the dataset already selected.\n")

    fired = 0
    considered = 0
    for dataset in mr.DATASET_TYPES:
        for model in mr.MODELS:
            # A user can only click Select for `model` while `dataset` is active if it is enabled.
            if model.key not in selectable_models(dataset.value):
                continue
            considered += 1
            enabled = enabled_datasets(model.key)
            would_snap = dataset.value not in enabled and bool(enabled)
            fired += int(would_snap)
            print(f"  reachable model-change: dataset={dataset.value:14s} -> model={model.key:11s} " f"| dataset still enabled? {dataset.value in enabled} | SNAP FIRES? {would_snap}")

    print(f"\n  model changes a user can actually perform : {considered}")
    print(f"  of those, snap branch executes           : {fired}")
    print(f"  F-A verdict: {'CONFIRMED - snap is dead code on this path' if fired == 0 else 'REFUTED - snap does fire'}\n")

    print("=== F-B: is the cleared-dataset (None) state already implemented downstream? ===")
    from frontend.dashboard_manager import DashboardManager  # noqa: E402  (import cost is paid only here)

    table = DashboardManager._build_model_selection_table(None, mr.DEFAULT_MODEL_KEY)

    def walk(node):
        yield node
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                yield from walk(child)
        elif children is not None:
            yield from walk(children)

    buttons = [n for n in walk(table) if getattr(n, "id", None) and isinstance(getattr(n, "id"), dict) and n.id.get("type") == "model-select-btn"]
    print(f"  _build_model_selection_table(None, 'cascor') -> {len(buttons)} Select buttons")
    for button in buttons:
        print(f"    {button.id['index']:11s} disabled={button.disabled}")
    all_enabled = bool(buttons) and all(button.disabled is False for button in buttons)

    hint = DashboardManager._dataset_model_hint_handler(None)
    body = DashboardManager._resolve_oneshot_start_body_handler("one_shot", None)
    print(f"  _dataset_model_hint_handler(None)            -> {hint!r}")
    print(f"  _resolve_oneshot_start_body_handler(os,None) -> {body!r}")
    print(f"\n  F-B verdict: {'CONFIRMED - null state handled, only clearable=False blocks it' if all_enabled else 'REFUTED'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
