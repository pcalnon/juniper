#!/usr/bin/env python3
"""
M-TOPOLOGY-03 / -14 / -18 scoring contracts (the leftovers #1673 cannot see).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-04
Status: ad-hoc — investigation (extracted so the contracts have a gate)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: F-CANOPY-041b (blank heatmap certified PASS), F-CANOPY-047 (CSP filed as environment),
         F-CANOPY-040 (unreadable store scored as empty FAIL)

``e2e_seg17_topology_driver.py`` already scores these rows. The predicates lived inline
with zero tests. Each can certify the wrong thing:

- M-TOPOLOGY-03 used to assert only ``any(type == "heatmap")``. canopy#558 shipped a
  heatmap whose vertical_spacing equalled plotly's limit, so 41 rows rendered at ZERO
  height. Every trace object was present; the canvas was blank; the row PASSED
  (F-CANOPY-041b). ``plot_area < 0.05`` must FAIL. ``plot_area is None`` (older
  fig_info) must not.
- M-TOPOLOGY-14 splits into a product half and an environment half. A control that
  only tried ``blob:`` reproduced canopy's own CSP and "confirmed" a browser
  limitation that does not exist. ``data:`` works + ``blob:`` blocked is PRODUCT
  FAIL (F-CANOPY-047). Neither scheme working is BLOCKED. Bad export config is
  FAIL without a download.
- M-TOPOLOGY-18: the first version counted browser requests to ``/api/topology/raw``
  (always 0 — the fetch is server-side) and then read an unreadable store as empty,
  producing a confident FAIL against a working gate. Unreadable is BLOCKED. An
  already-populated store that then fills is INDETERMINATE, not PASS.

Tiny testability extract only. Scoring behavior is unchanged. The driver calls
these functions; a revert that inlines the old easier-half logic fails the
structural gate in ``tests/test_e2e_topology_score_contracts.py``.

See ``util/ad-hoc/README.md`` for the ad-hoc-script convention.
"""

from __future__ import annotations

import re
import struct
from typing import Any, Mapping, Optional

EXPORT_FILENAME_RE = re.compile(r"canopy_network_\d{8}_\d{6}\Z")
EXPORT_DOWNLOAD_RE = re.compile(r"canopy_network_\d{8}_\d{6}\.png\Z")
PLOT_AREA_MIN = 0.05
SCALE_TARGET = 2.0
SCALE_TOLERANCE = 0.15


def export_filename_ok(filename: Any) -> bool:
    """Product half of M-TOPOLOGY-14: ``toImageButtonOptions.filename`` shape."""
    return bool(EXPORT_FILENAME_RE.fullmatch(str(filename or "")))


def download_filename_ok(suggested_filename: Any) -> bool:
    """Caught-download half of M-TOPOLOGY-14: suggested filename plus ``.png``."""
    return bool(EXPORT_DOWNLOAD_RE.fullmatch(str(suggested_filename or "")))


def export_config_ok(*, camera_present: Any, fmt: Any, scale: Any, filename: Any) -> bool:
    """Camera button + ``format: png`` + ``scale: 2`` + dated filename.

    A regression in any of those is product-owned and needs no download to see.
    """
    return bool(camera_present and fmt == "png" and scale == 2 and export_filename_ok(filename))


def png_dims(path: str) -> Optional[tuple[int, int]]:
    """``(width, height)`` straight out of the PNG IHDR — no image library needed."""
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def score_m_topology_03(*, is_heat: bool, plot_area: Any) -> str:
    """Weight-matrix row. A heatmap that occupies no canvas is not a render."""
    area_ok = plot_area is None or plot_area >= PLOT_AREA_MIN
    return "PASS" if (is_heat and area_ok) else "FAIL"


def score_m_topology_14(
    *,
    camera_present: Any,
    fmt: Any,
    scale: Any,
    filename: Any,
    download_caught: bool,
    suggested_filename: Any = None,
    png_w: Any = None,
    png_h: Any = None,
    graph_css_w: Any = None,
    raster_control: Optional[Mapping[str, Any]] = None,
) -> str:
    """Modebar camera / PNG export. Product FAIL and environment BLOCKED stay distinct.

    Order is load-bearing: bad config fails before a download is considered; a
    caught download is scored from the raster, not from the CSP control; the
    control is consulted only when no file arrived.
    """
    if not export_config_ok(camera_present=camera_present, fmt=fmt, scale=scale, filename=filename):
        return "FAIL"
    if download_caught:
        w = png_w or 0
        cw = graph_css_w or 0
        scale_seen = round(w / cw, 2) if cw else 0
        raster_ok = bool(w and cw and abs(scale_seen - SCALE_TARGET) <= SCALE_TOLERANCE)
        return "PASS" if (download_filename_ok(suggested_filename) and raster_ok) else "FAIL"
    control = raster_control or {}
    if control.get("blob_blocked"):
        # data: rasterises and blob: does not -> the page's CSP is the blocker
        # (F-CANOPY-047). A product defect, not an environment one.
        return "FAIL"
    if not control.get("ok"):
        # this browser cannot rasterise SVG by ANY scheme
        return "BLOCKED"
    # the browser rasterises by both schemes, yet no download arrived
    return "FAIL"


def score_m_topology_18(
    *,
    readable: bool,
    empty_in_node_graph: Any = None,
    populated_in_weight_matrix: Any = None,
) -> str:
    """Raw-topology store gate. Unreadable is BLOCKED, never empty FAIL."""
    if not readable or empty_in_node_graph is None:
        return "BLOCKED"
    if (not empty_in_node_graph) and populated_in_weight_matrix:
        return "INDETERMINATE"
    if empty_in_node_graph and populated_in_weight_matrix:
        return "PASS"
    return "FAIL"


if __name__ == "__main__":  # pragma: no cover — imported by the driver and the tests
    raise SystemExit("import e2e_topology_score_contracts; do not run it as a script")
