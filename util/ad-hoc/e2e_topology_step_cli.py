#!/usr/bin/env python3
"""Parse ``--step`` for the canopy topology driver (order-preserving).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-04
Status: ad-hoc — extracted so tests do not import the Playwright driver
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1709 (operator surface); M-TOPOLOGY-18 INDETERMINATE after ``topo``

``e2e_seg17_topology_driver.py --step`` is order-preserving on one browser page.
``topo`` fills the raw-topology store; a later ``topostate`` then scores
M-TOPOLOGY-18 ``INDETERMINATE``. Re-drive ``--step topostate`` alone (or first).
A rewrite that walks ``STEPS`` insertion order (or sorts names) silently
reorders the operator's list and recreates that harness artifact.

This module is importable without Playwright. Do not run it as a script.
"""

from __future__ import annotations

from collections.abc import Container


def parse_step_arg(raw: str, known: Container[str]) -> tuple[list[str], list[str]]:
    """Split a comma-separated ``--step`` value, preserving operator order.

    Empty tokens (``topo,,topostate`` or stray whitespace) are dropped.
    Unknown names stay in ``wanted`` and are also listed in ``bad`` so the
    driver can reject them before Playwright starts.
    """
    wanted = [s.strip() for s in raw.split(",") if s.strip()]
    bad = [s for s in wanted if s not in known]
    return wanted, bad


if __name__ == "__main__":
    raise SystemExit("import e2e_topology_step_cli; do not run it as a script")
