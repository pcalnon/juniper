#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/e2e_topology_score_contracts.py`` — M-TOPOLOGY-03 / -14 / -18.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the gate.
Hermetic: no Playwright, no canopy process, no network. Complementary to
``tests/test_e2e_topology_row_predicates.py`` (M-TOPOLOGY-06 / -07 / -12); do not
merge the two files.

What it pins, and why each mattered:

- M-TOPOLOGY-03: a heatmap *trace* is not a visible render. ``plot_area < 0.05``
  must FAIL (F-CANOPY-041b blank-canvas class). ``plot_area is None`` (older
  fig_info) must not fail the row. Existence-only scoring PASSes a blank canvas.
- M-TOPOLOGY-14: product FAIL and environment BLOCKED stay distinct. Bad export
  config is FAIL with no download. ``data:`` works + ``blob:`` blocked is FAIL
  (F-CANOPY-047 CSP). Neither scheme working is BLOCKED. A caught download is
  scored from the raster scale, not trusted from the config.
- M-TOPOLOGY-18: an unreadable store is BLOCKED, never empty FAIL. Already
  populated then filled is INDETERMINATE, not PASS. Empty then filled is PASS.
- The live driver calls these functions. A revert that inlines the old
  easier-half logic fails the structural gate.
"""

from __future__ import annotations

import ast
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = REPO_ROOT / "util" / "ad-hoc" / "e2e_topology_score_contracts.py"
DRIVER = REPO_ROOT / "util" / "ad-hoc" / "e2e_seg17_topology_driver.py"


def _load():
    spec = importlib.util.spec_from_file_location("e2e_topology_score_contracts", CONTRACTS)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _png(width: int, height: int) -> bytes:
    """Minimal IHDR-only PNG bytes. Enough for ``png_dims``; not a valid image."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return PNG_SIG + struct.pack(">I", 13) + b"IHDR" + ihdr + b"\x00\x00\x00\x00"


class Topology03HeatmapAreaTest(unittest.TestCase):
    def test_heatmap_with_real_area_passes(self) -> None:
        self.assertEqual(mod.score_m_topology_03(is_heat=True, plot_area=0.20), "PASS")

    def test_heatmap_at_the_floor_passes(self) -> None:
        self.assertEqual(mod.score_m_topology_03(is_heat=True, plot_area=0.05), "PASS")

    def test_blank_canvas_heatmap_fails(self) -> None:
        """F-CANOPY-041b: traces present, vertical_spacing at plotly's limit, height 0."""
        self.assertEqual(mod.score_m_topology_03(is_heat=True, plot_area=0.0), "FAIL")

    def test_just_under_the_floor_fails(self) -> None:
        self.assertEqual(mod.score_m_topology_03(is_heat=True, plot_area=0.049), "FAIL")

    def test_missing_measurement_does_not_fail_the_row(self) -> None:
        """Older fig_info without ``plot_area`` — say so, do not treat as passing *or* failing on area."""
        self.assertEqual(mod.score_m_topology_03(is_heat=True, plot_area=None), "PASS")

    def test_no_heatmap_fails_even_with_area(self) -> None:
        self.assertEqual(mod.score_m_topology_03(is_heat=False, plot_area=0.50), "FAIL")

    def test_existence_only_would_pass_the_blank(self) -> None:
        """The mutation this suite exists to catch: drop the area check."""
        is_heat, plot_area = True, 0.0
        existence_only = "PASS" if is_heat else "FAIL"
        self.assertEqual(existence_only, "PASS")
        self.assertEqual(mod.score_m_topology_03(is_heat=is_heat, plot_area=plot_area), "FAIL")


class Topology14ExportTest(unittest.TestCase):
    def test_filename_shape_is_exact(self) -> None:
        self.assertTrue(mod.export_filename_ok("canopy_network_20260904_214900"))
        self.assertFalse(mod.export_filename_ok("canopy_network_20260904_214900.png"))
        self.assertFalse(mod.export_filename_ok("canopy-network_20260904_214900"))
        self.assertFalse(mod.export_filename_ok("canopy_network_20260904"))
        self.assertFalse(mod.export_filename_ok(""))
        self.assertFalse(mod.export_filename_ok(None))

    def test_download_filename_requires_png_suffix(self) -> None:
        self.assertTrue(mod.download_filename_ok("canopy_network_20260904_214900.png"))
        self.assertFalse(mod.download_filename_ok("canopy_network_20260904_214900"))
        self.assertFalse(mod.download_filename_ok("plot.png"))

    def test_bad_config_fails_without_a_download(self) -> None:
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=True,
                fmt="png",
                scale=1,  # dropped scale
                filename="canopy_network_20260904_214900",
                download_caught=True,
                suggested_filename="canopy_network_20260904_214900.png",
                png_w=1600,
                graph_css_w=800,
            ),
            "FAIL",
        )

    def test_missing_camera_fails_even_if_the_raster_would_pass(self) -> None:
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=False,
                fmt="png",
                scale=2,
                filename="canopy_network_20260904_214900",
                download_caught=True,
                suggested_filename="canopy_network_20260904_214900.png",
                png_w=1600,
                graph_css_w=800,
            ),
            "FAIL",
        )

    def test_caught_download_at_scale_2_passes(self) -> None:
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=True,
                fmt="png",
                scale=2,
                filename="canopy_network_20260904_214900",
                download_caught=True,
                suggested_filename="canopy_network_20260904_214900.png",
                png_w=1600,
                png_h=1200,
                graph_css_w=800,
            ),
            "PASS",
        )

    def test_caught_download_at_scale_1_fails(self) -> None:
        """Scale is verified against the raster, not trusted from the config."""
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=True,
                fmt="png",
                scale=2,
                filename="canopy_network_20260904_214900",
                download_caught=True,
                suggested_filename="canopy_network_20260904_214900.png",
                png_w=800,
                graph_css_w=800,
            ),
            "FAIL",
        )

    def test_caught_download_wrong_name_fails(self) -> None:
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=True,
                fmt="png",
                scale=2,
                filename="canopy_network_20260904_214900",
                download_caught=True,
                suggested_filename="download.png",
                png_w=1600,
                graph_css_w=800,
            ),
            "FAIL",
        )

    def test_csp_blob_block_is_product_fail(self) -> None:
        """F-CANOPY-047: ``img-src 'self' data:`` omits ``blob:``."""
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=True,
                fmt="png",
                scale=2,
                filename="canopy_network_20260904_214900",
                download_caught=False,
                raster_control={"ok": True, "blob_blocked": True, "data": {"ok": True}, "blob": {"ok": False}},
            ),
            "FAIL",
        )

    def test_neither_scheme_is_environment_blocked(self) -> None:
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=True,
                fmt="png",
                scale=2,
                filename="canopy_network_20260904_214900",
                download_caught=False,
                raster_control={"ok": False, "blob_blocked": False, "data": {"ok": False}, "blob": {"ok": False}},
            ),
            "BLOCKED",
        )

    def test_both_schemes_work_but_no_download_is_product_fail(self) -> None:
        self.assertEqual(
            mod.score_m_topology_14(
                camera_present=True,
                fmt="png",
                scale=2,
                filename="canopy_network_20260904_214900",
                download_caught=False,
                raster_control={"ok": True, "blob_blocked": False, "data": {"ok": True}, "blob": {"ok": True}},
            ),
            "FAIL",
        )

    def test_png_dims_reads_ihdr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.png"
            path.write_bytes(_png(1600, 1200))
            self.assertEqual(mod.png_dims(str(path)), (1600, 1200))

    def test_png_dims_rejects_non_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.bin"
            path.write_bytes(b"not a png")
            self.assertIsNone(mod.png_dims(str(path)))


class Topology18StoreGateTest(unittest.TestCase):
    def test_unreadable_is_blocked_not_empty_fail(self) -> None:
        self.assertEqual(
            mod.score_m_topology_18(readable=False, empty_in_node_graph=None, populated_in_weight_matrix=None),
            "BLOCKED",
        )

    def test_unreadable_is_not_fail_even_when_the_store_looks_empty(self) -> None:
        """The mutation: treat unreadable as empty → FAIL (the first-run mistake)."""
        self.assertNotEqual(
            mod.score_m_topology_18(readable=False, empty_in_node_graph=True, populated_in_weight_matrix=False),
            "FAIL",
        )
        self.assertEqual(
            mod.score_m_topology_18(readable=False, empty_in_node_graph=True, populated_in_weight_matrix=False),
            "BLOCKED",
        )

    def test_empty_then_filled_passes(self) -> None:
        self.assertEqual(
            mod.score_m_topology_18(readable=True, empty_in_node_graph=True, populated_in_weight_matrix=True),
            "PASS",
        )

    def test_never_fills_fails(self) -> None:
        """F-CANOPY-040's shape: the poll never fires."""
        self.assertEqual(
            mod.score_m_topology_18(readable=True, empty_in_node_graph=True, populated_in_weight_matrix=False),
            "FAIL",
        )

    def test_already_populated_then_filled_is_indeterminate(self) -> None:
        """Cannot test the first half; do not score a half-measured row as PASS."""
        self.assertEqual(
            mod.score_m_topology_18(readable=True, empty_in_node_graph=False, populated_in_weight_matrix=True),
            "INDETERMINATE",
        )

    def test_already_populated_and_never_fills_fails(self) -> None:
        self.assertEqual(
            mod.score_m_topology_18(readable=True, empty_in_node_graph=False, populated_in_weight_matrix=False),
            "FAIL",
        )


class DriverWiresTheContractsTest(unittest.TestCase):
    def test_driver_calls_the_three_scorers(self) -> None:
        tree = ast.parse(DRIVER.read_text(encoding="utf-8"))
        called = {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and node.attr in {"score_m_topology_03", "score_m_topology_14", "score_m_topology_18"}
        }
        self.assertEqual(
            called,
            {"score_m_topology_03", "score_m_topology_14", "score_m_topology_18"},
            "a revert that inlines the old easier-half logic drops these calls",
        )

    def test_driver_loads_this_module(self) -> None:
        source = DRIVER.read_text(encoding="utf-8")
        self.assertIn("e2e_topology_score_contracts.py", source)


if __name__ == "__main__":
    unittest.main()
