#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E arc -- F-CANOPY-040 residual / F-CANOPY-043 fix verification (ad-hoc)
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

Answers two questions about ONE canopy checkout, by running its real
``DashboardManager`` rather than by reading its diff:

  1. F-CANOPY-040 RESIDUAL -- is ``network-visualizer-display-mode`` an **Input**
     of the ``-raw-topology-store`` poll, or merely a State? As a State,
     selecting Weight Matrix does not trigger the fetch, so the store fills only
     on the next 5 s ``tabpoll-topology`` tick and a reader arriving inside that
     window sees an unpainted heatmap.

  2. F-CANOPY-043 -- does the poll SUPPRESS a byte-identical weight payload?
     ``-raw-topology-store`` is an Input of the topology rebuild, and Dash fires
     every consumer of a store on any write, identical or not. Since
     dash-renderer's ``getUniqueIdentifier`` hashes a callback's inputs/outputs/
     state and NOT its trigger, an unchanged 5 s rewrite retires the IN-FLIGHT
     rebuild instead of queueing behind it -- F-CANOPY-039's mechanism on a
     second store.

WHY THIS EXISTS AS A SEPARATE INSTRUMENT. The fix ships with unit tests, but a
test living in the same tree as the fix cannot demonstrate that it FAILS without
it -- and this arc has twice shipped a check that could not fail (canopy#558's
``assert min(a,b) <= b`` tautology, and M-TOPOLOGY-03's ``any(type ==
"heatmap")`` predicate that passed on 41 zero-height traces). Pointing this at
the PARENT checkout and then at the fixed one is the falsification step.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/2026-09-02_f043_suppression_probe.py --src <canopy>/src

Exit: 0 when BOTH properties hold (the fixed state), 1 when either does not.
      The parent checkout is expected to exit 1 -- that is the point.

See util/ad-hoc/README.md for the ad-hoc-script convention.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

STORE = "network-visualizer-raw-topology-store"
DISPLAY_MODE = "network-visualizer-display-mode"

RAW = {
    "hidden_units": 3,
    "input_units": 2,
    "layers": [{"index": 0, "weights": [[0.1, 0.2], [0.3, 0.4]]}],
}


def _resp(payload):
    r = MagicMock()
    r.status_code = 200
    r.ok = True
    r.json.return_value = payload
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="path to a canopy checkout's src/ directory")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    if not (src / "frontend" / "dashboard_manager.py").is_file():
        print(f"FAIL: {src} does not look like a canopy src/ (no frontend/dashboard_manager.py)", file=sys.stderr)
        return 2
    sys.path.insert(0, str(src))

    import dash

    from frontend.dashboard_manager import DashboardManager

    dm = DashboardManager({})
    print(f"checkout : {src}")

    # ---- Q1: is display-mode a TRIGGER? -----------------------------------
    entry = None
    for key, candidate in dm.app.callback_map.items():
        if key.startswith(f"{STORE}.data"):
            entry = candidate
            break
    if entry is None:
        print(f"FAIL: no callback writes {STORE}")
        return 1

    input_ids = {d["id"] for d in (entry.get("inputs") or []) if isinstance(d, dict)}
    state_ids = {d["id"] for d in (entry.get("state") or []) if isinstance(d, dict)}
    triggers = DISPLAY_MODE in input_ids
    print(f"  inputs : {sorted(input_ids)}")
    print(f"  state  : {sorted(state_ids)}")
    print(f"Q1 display-mode is an Input (switch triggers the fetch) : {'YES' if triggers else 'NO -- F-CANOPY-040 residual'}")

    # ---- Q2: is an identical payload suppressed? --------------------------
    # Probe the handler through its real signature. A checkout without the fix
    # has no ``current`` parameter at all, which is itself the answer.
    import inspect

    sig = inspect.signature(DashboardManager._update_raw_topology_store_handler)
    has_current = "current" in sig.parameters
    if not has_current:
        suppresses = False
        print(f"Q2 identical payload suppressed                        : NO -- handler has no `current` parameter {tuple(sig.parameters)}")
    else:
        with patch("requests.get", return_value=_resp(dict(RAW))):
            with dm.app.server.test_request_context(base_url="http://localhost:8050"):
                result = dm._update_raw_topology_store_handler(n=1, active_tab="topology", display_mode="weight_matrix", current=dict(RAW))
        suppresses = result is dash.no_update
        print(f"Q2 identical payload suppressed                        : {'YES' if suppresses else 'NO -- F-CANOPY-043'}")

        # A suppressor that also swallows real changes would be worse than none.
        with patch("requests.get", return_value=_resp(dict(RAW))):
            with dm.app.server.test_request_context(base_url="http://localhost:8050"):
                changed = dm._update_raw_topology_store_handler(n=1, active_tab="topology", display_mode="weight_matrix", current=dict(RAW, hidden_units=2))
        if changed != RAW:
            print(f"FAIL: a CHANGED payload was not written back ({changed!r}) -- suppression is over-broad")
            return 1
        print("   (changed payload still writes: OK)")

    ok = triggers and suppresses
    print(f"\nVERDICT: {'FIXED' if ok else 'DEFECTIVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
