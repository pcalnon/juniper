#!/usr/bin/env python
#####################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# File Name:     2026-09-02_canopy_model_dataset_reachability_probe.py
# Author:        Paul Calnon
# Version:       0.1.0
# Date:          2026-09-02
# License:       MIT License
# Description:   Lane A2 consensus probe: exhaustively enumerate the
#                (model, dataset) state graph juniper-canopy's two
#                selection gates permit, and report whether
#                (recurrence, equities_seq) is reachable from the
#                default (cascor, spirals).  Read-only against
#                juniper-canopy; imports src/model_registry.py only.
#####################################################################
"""Independent reachability measurement for the canopy model/dataset selection UI.

Instrument: build the transition relation directly from the two *registry-level*
gate functions the UI renders from --

  * ``gated_dataset_options(model_key)``  -> which dataset options are disabled
  * ``model_reason(model_spec, dataset)`` -> the model-table Select-disabled predicate

then BFS the state graph from ``(DEFAULT_MODEL_KEY, DEFAULT_DATASET_TYPE)``.

This deliberately does NOT read the dashboard_manager callbacks: it re-creates the
measurement from the primitives the tests assert on, so a defect in the callback
wiring cannot make the probe agree with the tests by construction.
"""

from __future__ import annotations

import sys
from pathlib import Path

CANOPY_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy/src")
sys.path.insert(0, str(CANOPY_SRC))

from model_registry import (  # noqa: E402
    DATASET_TYPES,
    DEFAULT_DATASET_TYPE,
    DEFAULT_MODEL_KEY,
    MODELS,
    gated_dataset_options,
    get_dataset_spec,
    get_model_spec,
    model_reason,
)


def dataset_moves(model_key: str, dataset_value: str) -> list[str]:
    """Dataset values the dropdown leaves selectable for ``model_key``."""
    out = []
    for option in gated_dataset_options(model_key):
        if option.get("disabled"):
            continue
        if option["value"] != dataset_value:
            out.append(option["value"])
    return out


def model_moves(model_key: str, dataset_value: str) -> list[str]:
    """Model keys whose table Select button is NOT disabled for ``dataset_value``.

    The table disables a row exactly when ``model_reason(model, dataset)`` is truthy
    (test_model_table.py's `_button_for(...).disabled` assertions), and treats an
    unresolvable dataset as ungated.
    """
    dataset_spec = get_dataset_spec(dataset_value)
    out = []
    for model in MODELS:
        if model.key == model_key:
            continue
        if dataset_spec is None:
            out.append(model.key)
            continue
        if model_reason(model, dataset_spec) is None:
            out.append(model.key)
    return out


def main() -> int:
    start = (DEFAULT_MODEL_KEY, DEFAULT_DATASET_TYPE)
    target = ("recurrence", "equities_seq")

    print(f"registry models   : {[m.key for m in MODELS]}")
    print(f"registry datasets : {[d.value for d in DATASET_TYPES]}")
    print(f"default state     : {start}")
    print(f"target state      : {target}")
    print()

    seen = {start}
    frontier = [start]
    edges: list[tuple[tuple[str, str], str, tuple[str, str]]] = []
    while frontier:
        model_key, dataset_value = frontier.pop()
        for nxt_dataset in dataset_moves(model_key, dataset_value):
            nxt = (model_key, nxt_dataset)
            edges.append(((model_key, dataset_value), "dataset", nxt))
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
        for nxt_model in model_moves(model_key, dataset_value):
            nxt = (nxt_model, dataset_value)
            edges.append(((model_key, dataset_value), "model", nxt))
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)

    print(f"reachable states from default ({len(seen)}):")
    for state in sorted(seen):
        print(f"    {state}")
    print()
    print(f"target reachable  : {target in seen}")
    print(f"target is a legal (compatible) pair: {model_reason(get_model_spec('recurrence'), get_dataset_spec('equities_seq')) is None}")
    print()

    # Which single gate blocks which edge, from the default state.
    m0, d0 = start
    print("blocking edges out of the default state:")
    for option in gated_dataset_options(m0):
        if option["value"] == "equities_seq":
            print(f"    dataset->equities_seq  disabled={option.get('disabled')!r}  label={option['label']!r}")
    rec = get_model_spec("recurrence")
    print(f"    model->recurrence      model_reason(recurrence, {d0}) = {model_reason(rec, get_dataset_spec(d0))!r}  (non-None => Select disabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
