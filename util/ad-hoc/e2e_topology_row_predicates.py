"""
Pure M-TOPOLOGY row predicates for the canopy e2e scorer.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-04
Status: ad-hoc — extracted so the three predicates that scored the easier
        half of an OR can be unit-tested without importing the Playwright
        driver (which `_load`s sibling drivers at module level).
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: F-CANOPY-042, F-CANOPY-046, ml#1672, M-TOPOLOGY-06, M-TOPOLOGY-07, M-TOPOLOGY-12

``util/ad-hoc/e2e_seg17_topology_driver.py`` is the caller. These functions
are the only place the three verdicts are decided, so a revert to
``label == want OR hidden == want`` (or a display-only -07, or a missing
clear-control scored as FAIL) fails this module's tests rather than
shipping as a green matrix row.
"""

from __future__ import annotations

from typing import Any, Mapping


def score_m_topology_06(
    idiom: object,
    label: object,
    hidden_count: object,
    want: object,
) -> bool:
    """PASS iff the slider landed AND the label AND the stats-bar count match.

    The old predicate was ``idiom is not None and (label == want or
    hidden == want)``. It passed on the counts branch for the whole
    F-CANOPY-042 arc: the stats bar tracked the filter while the label
    beside the slider sat at ``"0 of 40"``. An OR over two independent
    claims scores the easier one, so the row could not fail on the
    defect it names.
    """
    return idiom is not None and label == want and hidden_count == want


def score_m_topology_07(
    display: object,
    label: object,
    want_label: str = "all",
) -> bool:
    """PASS iff the depth container is visible AND the label is ``want_label``.

    The old predicate scored ``display`` alone. The label was read into
    the record as decoration, so ``label='0 of 40'`` on a freshly loaded
    40-unit network still PASSed — F-CANOPY-042's defect B, sitting in
    the scorer's own output.
    """
    return display not in (None, "none") and label == want_label


def selection_is_cleared(info: Mapping[str, Any] | None) -> bool:
    """A selection panel is gone when it is hidden or has no text."""
    state = info or {}
    return state.get("display") in (None, "none") or not (state.get("text") or "").strip()


def score_m_topology_12(
    *,
    precondition_selected: bool,
    control: Mapping[str, Any] | None,
    cleared: bool,
) -> str:
    """Return PASS / FAIL / BLOCKED for "a selection can be cleared".

    The row used to score the empty-space click. plotly emits
    ``plotly_click`` only on a POINT hit, so that gesture produced no
    event and the row FAILed a withdrawn promise. canopy#573 ships a
    Clear-selection control instead.

    - Nothing selected → BLOCKED (a vacuous clear says nothing).
    - Control absent → BLOCKED (a product with no affordance cannot be
      asked whether its affordance works). Not FAIL.
    - Control present but hidden → FAIL.
    - Control visible → PASS iff the selection actually cleared.

    The empty-space click is recorded by the driver, not scored here.
    Passing ``empty_cleared=False`` alongside a working control must
    still be PASS — that is the restatement.
    """
    if not precondition_selected:
        return "BLOCKED"
    state = control or {}
    if not state.get("present"):
        return "BLOCKED"
    if not state.get("visible"):
        return "FAIL"
    return "PASS" if cleared else "FAIL"
