#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/e2e_topology_row_predicates.py`` -- the three
M-TOPOLOGY row predicates that scored the easier half of an OR.

``util/`` is outside every pre-commit Python hook's scope, so this suite
is the gate. Hermetic: no Playwright, no live canopy. The driver itself
cannot be imported (it ``_load``s sibling drivers at module level), so
the predicates were extracted and the driver is checked structurally
for the two sites that already call them.

What it pins, and why it mattered:

- M-TOPOLOGY-06 must require label AND hidden-count. The old
  ``label == want OR hidden == want`` PASSed on the counts branch
  while the label sat at ``"0 of 40"`` (F-CANOPY-042, found by eye).
- M-TOPOLOGY-07 must assert the label, not display alone. A visible
  container with ``label='0 of 40'`` is FAIL.
- M-TOPOLOGY-12 must BLOCKED (not FAIL) when the Clear-selection
  control is absent, and must not score the withdrawn empty-space
  gesture. canopy#573 restated the row; a missing affordance is not
  a product defect.
"""

from __future__ import annotations

import ast
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDICATES = REPO_ROOT / "util" / "ad-hoc" / "e2e_topology_row_predicates.py"
DRIVER = REPO_ROOT / "util" / "ad-hoc" / "e2e_seg17_topology_driver.py"


def _load():
    spec = importlib.util.spec_from_file_location("e2e_topology_row_predicates", PREDICATES)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


pred = _load()

_WANT = "20 of 40"


class ScoreMTopology06Test(unittest.TestCase):
    def test_both_halves_pass(self) -> None:
        self.assertTrue(pred.score_m_topology_06("keyboard", _WANT, _WANT, _WANT))

    def test_counts_alone_is_fail(self) -> None:
        """The live false-PASS: stats bar tracked the filter, label did not."""
        self.assertFalse(pred.score_m_topology_06("number-input", "0 of 40", _WANT, _WANT))

    def test_label_alone_is_fail(self) -> None:
        self.assertFalse(pred.score_m_topology_06("keyboard", _WANT, "40 of 40", _WANT))

    def test_no_idiom_is_fail_even_when_both_match(self) -> None:
        self.assertFalse(pred.score_m_topology_06(None, _WANT, _WANT, _WANT))

    def test_neither_half_is_fail(self) -> None:
        self.assertFalse(pred.score_m_topology_06("drag", "0 of 40", "40 of 40", _WANT))


class ScoreMTopology07Test(unittest.TestCase):
    def test_visible_all_is_pass(self) -> None:
        self.assertTrue(pred.score_m_topology_07("flex", "all"))

    def test_visible_wrong_label_is_fail(self) -> None:
        """The live false-PASS: container shown, label '0 of 40' at rest."""
        self.assertFalse(pred.score_m_topology_07("block", "0 of 40"))

    def test_hidden_all_is_fail(self) -> None:
        self.assertFalse(pred.score_m_topology_07("none", "all"))

    def test_missing_display_is_fail(self) -> None:
        self.assertFalse(pred.score_m_topology_07(None, "all"))


class ScoreMTopology12Test(unittest.TestCase):
    def test_no_selection_is_blocked(self) -> None:
        self.assertEqual(
            pred.score_m_topology_12(
                precondition_selected=False,
                control={"present": True, "visible": True},
                cleared=True,
            ),
            "BLOCKED",
        )

    def test_control_absent_is_blocked_not_fail(self) -> None:
        """A build with no affordance cannot be asked whether it works."""
        self.assertEqual(
            pred.score_m_topology_12(
                precondition_selected=True,
                control={"present": False, "visible": False},
                cleared=False,
            ),
            "BLOCKED",
        )

    def test_missing_control_dict_is_blocked(self) -> None:
        self.assertEqual(
            pred.score_m_topology_12(precondition_selected=True, control=None, cleared=False),
            "BLOCKED",
        )

    def test_control_hidden_is_fail(self) -> None:
        self.assertEqual(
            pred.score_m_topology_12(
                precondition_selected=True,
                control={"present": True, "visible": False},
                cleared=False,
            ),
            "FAIL",
        )

    def test_visible_cleared_is_pass(self) -> None:
        self.assertEqual(
            pred.score_m_topology_12(
                precondition_selected=True,
                control={"present": True, "visible": True, "clicked": True},
                cleared=True,
            ),
            "PASS",
        )

    def test_visible_survived_is_fail(self) -> None:
        self.assertEqual(
            pred.score_m_topology_12(
                precondition_selected=True,
                control={"present": True, "visible": True, "clicked": True},
                cleared=False,
            ),
            "FAIL",
        )

    def test_empty_space_miss_does_not_spoil_a_working_control(self) -> None:
        """The restatement: empty-space plotly_click=0 is recorded, not scored."""
        empty_cleared = False
        self.assertEqual(
            pred.score_m_topology_12(
                precondition_selected=True,
                control={"present": True, "visible": True},
                cleared=True,
            ),
            "PASS",
        )
        self.assertFalse(empty_cleared)


class SelectionIsClearedTest(unittest.TestCase):
    def test_hidden_is_cleared(self) -> None:
        self.assertTrue(pred.selection_is_cleared({"display": "none", "text": "Hidden 3"}))

    def test_empty_text_is_cleared(self) -> None:
        self.assertTrue(pred.selection_is_cleared({"display": "block", "text": "  "}))

    def test_named_selection_is_not_cleared(self) -> None:
        self.assertFalse(pred.selection_is_cleared({"display": "block", "text": "Hidden 3\nLayer: Hidden"}))


class DriverWiringTest(unittest.TestCase):
    """The extracted helpers only protect the matrix if the driver calls them."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.src = DRIVER.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.src)

    def test_driver_calls_score_m_topology_06(self) -> None:
        names = {node.id for node in ast.walk(self.tree) if isinstance(node, ast.Name)}
        self.assertIn("score_m_topology_06", names)

    def test_driver_calls_score_m_topology_07(self) -> None:
        names = {node.id for node in ast.walk(self.tree) if isinstance(node, ast.Name)}
        self.assertIn("score_m_topology_07", names)

    def test_driver_calls_selection_is_cleared(self) -> None:
        names = {node.id for node in ast.walk(self.tree) if isinstance(node, ast.Name)}
        self.assertIn("selection_is_cleared", names)

    def test_driver_does_not_keep_the_old_or(self) -> None:
        """A revert that inlines ``label == want or hidden == want`` must fail."""
        self.assertNotIn('k_label == want or k_counts["hidden"] == want', self.src)
        self.assertNotIn("k_label == want or k_counts['hidden'] == want", self.src)

    def test_predicates_module_has_no_playwright_import(self) -> None:
        tree = ast.parse(PREDICATES.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module.split(".", 1)[0])
        self.assertNotIn("playwright", imported)
        self.assertNotIn("sync_playwright", imported)


if __name__ == "__main__":
    unittest.main()
