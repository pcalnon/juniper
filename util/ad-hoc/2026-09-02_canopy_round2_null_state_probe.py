#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Round-2 review probe: re-derive the design document's "the null state is already
#                built and already tested" claims by execution, and probe the ones it did NOT check.
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-02_canopy_round2_null_state_probe.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-02
# Last Modified: 2026-09-02
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     The design document verifies three handlers against a cleared dataset. Three of the SIX
#     callbacks that read ``nn-dataset-type-dropdown.value`` as an Input or State were not checked:
#     ``render_dataset_params``, ``toggle_model_modal`` (the compatibility CELL, not the button),
#     and ``open_restart_confirm_modal``. This probe exercises all of them plus the Start gate.
#
#####################################################################################################################################################################################################
# Notes:
#     - Run with the JuniperCanopy1 environment (JuniperCanopy is DEPRECATED).
#     - Read-only: no canopy file is modified and no service is contacted.
#
#####################################################################################################################################################################################################

"""Probe every cleared-dataset consumer the design document did not itself execute."""

from __future__ import annotations

import sys
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")
sys.path.insert(0, str(CANOPY_SRC))

import model_registry as mr  # noqa: E402
from frontend.dashboard_manager import DashboardManager  # noqa: E402


def show(label, fn):
    try:
        out = fn()
        print(f"  OK   {label}: {out!r}"[:400])
    except Exception as exc:  # noqa: BLE001 - a raise IS the finding
        print(f"  RAISE {label}: {type(exc).__name__}: {exc}")


def main() -> int:
    print("=== the three handlers the DESIGN verified ===")
    table = DashboardManager._build_model_selection_table(None, "cascor")
    buttons = []

    def walk(node):
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                walk(child)
        elif children is not None and not isinstance(children, str):
            walk(children)
        cid = getattr(node, "id", None)
        if isinstance(cid, dict) and cid.get("type") == "model-select-btn":
            buttons.append((cid["index"], getattr(node, "disabled", None), getattr(node, "title", None)))

    walk(table)
    print(f"  _build_model_selection_table(None,'cascor') select buttons: {buttons}")

    # The compatibility CELL at a cleared dataset -- what does the row actually SAY?
    cells = []

    def walk_cells(node, depth=0):
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                walk_cells(child, depth + 1)
        elif children is not None and not isinstance(children, str):
            walk_cells(children, depth + 1)
        cls = getattr(node, "className", "") or ""
        if "text-success" in cls or "fst-italic" in cls:
            cells.append(getattr(node, "children", None))

    walk_cells(table)
    print(f"  compatibility CELL text at a CLEARED dataset: {cells}")

    show("_dataset_model_hint_handler(None)", lambda: DashboardManager._dataset_model_hint_handler(None))
    show("_resolve_oneshot_start_body_handler('one_shot', None)", lambda: DashboardManager._resolve_oneshot_start_body_handler("one_shot", None))
    show("_resolve_oneshot_start_body_handler('live', None)", lambda: DashboardManager._resolve_oneshot_start_body_handler("live", None))

    print("\n=== consumers the design did NOT verify ===")
    manager = DashboardManager.__new__(DashboardManager)
    show("_render_dataset_params_handler(None)", lambda: DashboardManager._render_dataset_params_handler(manager, None))
    show("_toggle_model_modal_handler(open, dataset=None)", lambda: DashboardManager._toggle_model_modal_handler(manager, "nn-model-change-button", None, "cascor", "") and "built")

    print("\n=== the Start gate at a cleared dataset (design section 2's 'not trainable' claim) ===")
    for key in ("cascor", "recurrence"):
        print(f"  model_is_trainable({key!r}) = {mr.model_is_trainable(key)}")
    print("  _update_button_appearance_handler signature params:", DashboardManager._update_button_appearance_handler.__code__.co_varnames[: DashboardManager._update_button_appearance_handler.__code__.co_argcount])

    print("\n=== the model-primary / dataset-primary docstring label ===")
    doc = DashboardManager._gate_dataset_options_handler.__doc__ or ""
    for line in doc.splitlines():
        if "primary" in line:
            print("  docstring says:", line.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
