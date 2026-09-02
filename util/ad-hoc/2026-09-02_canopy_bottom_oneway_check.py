#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   JuniperML
# Application:   util/ad-hoc
# Purpose:       Round-2 review instrument: is the cleared-dataset state BOTTOM a one-way door?
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-02_canopy_bottom_oneway_check.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-02
# Last Modified: 2026-09-02
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     The reachability design calls BOTTOM "a transit state, not a destination" and a "universal
#     cut vertex". A cut vertex is only a transit state if you can LEAVE it. This BFSes forward
#     from (cascor, BOTTOM) under three availability fixtures and reports what is reachable.
#
#####################################################################################################################################################################################################
# Notes:
#     - Run with the JuniperCanopy1 environment.
#     - Read-only simulation.
#
#####################################################################################################################################################################################################

"""BFS forward from the cleared state to test whether BOTTOM can be left."""

from __future__ import annotations

import sys
from collections import deque

sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-canopy/src")

import model_registry as mr  # noqa: E402

MODELS = list(mr.MODELS)
DATASETS = list(mr.DATASET_TYPES)


def bfs(start, unavailable):
    def enabled(model_key):
        spec = mr.get_model_spec(model_key)
        return [d.value for d in DATASETS if mr.dataset_reason(d, spec) is None and d.value not in unavailable]

    def selectable(dataset_value):
        if dataset_value is None:
            return [m.key for m in MODELS]
        spec = mr.get_dataset_spec(dataset_value)
        return [m.key for m in MODELS if spec is not None and mr.model_reason(m, spec) is None]

    def snap(model_key, current):
        options = enabled(model_key)
        return current if (current in options or not options) else options[0]

    seen = {start}
    queue = deque([start])
    while queue:
        model_key, dataset_value = queue.popleft()
        nxt = [(model_key, v) for v in enabled(model_key)]
        if dataset_value is not None:
            nxt.append((model_key, None))
        nxt += [(m, snap(m, dataset_value)) for m in selectable(dataset_value)]
        for state in nxt:
            if state not in seen:
                seen.add(state)
                queue.append(state)
    return seen


def main() -> int:
    fixtures = (
        ("all available", frozenset()),
        ("equities_seq unavailable", frozenset({"equities_seq"})),
        ("ALL unavailable", frozenset(d.value for d in DATASETS)),
    )
    for label, unavailable in fixtures:
        reached = bfs(("cascor", None), unavailable)
        pretty = sorted((m, d or "BOTTOM") for m, d in reached)
        leaves = [s for s in pretty if s[1] != "BOTTOM"]
        print(f"{label:26} | from (cascor, BOTTOM): {len(reached)} states {pretty}")
        print(f"{'':26} | can LEAVE BOTTOM to a committed dataset? {'YES' if leaves else 'NO  <-- one-way door'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
