#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E Phase 4 -- plan §7.5 F-CANDIDATE reproduction probe
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

Reproduces, without a browser or a stack, the §7.5 "F-CANDIDATE": with no
``recurrence_service_url`` configured, ``POST /api/model/select`` for the recurrence
(LMU) model is ACCEPTED (200), the live backend stays the default cascor/demo backend,
and nothing on the server side gates the selection -- while ``model_is_trainable``
keeps Start enabled for the (``status="live"``) recurrence spec. The D-8 docstring in
``src/backend/__init__.py`` claims "the A1 selection UI gates an unconfigured
recurrence model out of the picker"; this probe shows the API layer does not.

Usage (from a canopy checkout root; the arc's canopy env):

    LD_LIBRARY_PATH= PYTHONPATH=<canopy>/src \
        /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_fcandidate_model_select_probe.py

Exit 0 when the reproduction holds (selection accepted, backend unchanged), 1 otherwise.
"""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    os.environ.setdefault("JUNIPER_CANOPY_DEMO_MODE", "1")
    os.environ.pop("JUNIPER_CANOPY_RECURRENCE_SERVICE_URL", None)
    os.environ.pop("JUNIPER_CANOPY_CASCOR_SERVICE_URL", None)

    from fastapi.testclient import TestClient

    import main as canopy_main
    from backend.demo_backend import DemoBackend
    from demo_mode import DemoMode
    from model_registry import get_model_spec, model_is_trainable

    settings = canopy_main.settings
    print(f"recurrence_service_url={settings.recurrence_service_url!r}")
    # A bare TestClient never runs the lifespan (arc trap) -- install a demo backend directly.
    canopy_main.backend = DemoBackend(DemoMode(update_interval=1.0))
    spec = get_model_spec("recurrence")
    print(f"registry: key={spec.key} status={spec.status} provider={spec.provider} execution={spec.execution}")
    print(f"model_is_trainable('recurrence') = {model_is_trainable('recurrence')}")
    print(f"_selection_targets_recurrence('recurrence') = {canopy_main._selection_targets_recurrence('recurrence')}")

    client = TestClient(canopy_main.app)
    r = client.post("/api/model/select", json={"nn_model": "recurrence"})
    body = r.json()
    print(f"POST /api/model/select -> {r.status_code} {json.dumps(body)}")
    ok = r.status_code == 200 and body.get("nn_model") == "recurrence" and body.get("backend") != "recurrence" and body.get("swapped") is False and body.get("status") == "live"
    print("REPRODUCED: selection accepted, backend unchanged, status live, Start not gated" if ok else "NOT REPRODUCED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
