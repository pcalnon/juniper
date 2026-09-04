#!/usr/bin/env python3
"""Hermetic tests for topology-driver ``--step`` order preservation.

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``tests/test_e2e_topology_score_contracts.py`` (#1676) pins M-TOPOLOGY-18
INDETERMINATE when the raw-topology store is already populated. That suite
cannot see the CLI loop that *causes* the pre-fill: ``--step`` walks the
operator's list, and ``topo`` then ``topostate`` on one page fills the store
before the two-sided gate can be measured.

A rewrite that iterates ``STEPS`` insertion order (or sorts names) silently
reorders ``topostate,topo`` into ``topo,topostate`` and recreates the harness
artifact. This suite is that leftover. Tests import
``e2e_topology_step_cli.py`` only — never the Playwright driver. Do not open
a second PR on this file.
"""

from __future__ import annotations

import ast
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / "util" / "ad-hoc" / "e2e_topology_step_cli.py"
DRIVER = REPO_ROOT / "util" / "ad-hoc" / "e2e_seg17_topology_driver.py"

# Insertion order of STEPS in the driver (topo before topostate). Used only
# to prove parse_step_arg does NOT adopt this order.
_STEPS_INSERTION = (
    "probe",
    "topodiag",
    "rebuildprobe",
    "wirecensus",
    "quietread",
    "topo",
    "topoevents",
    "topostate",
    "topoexport",
    "storestorm",
    "f031",
    "theme",
)


def _load():
    spec = importlib.util.spec_from_file_location("e2e_topology_step_cli", HELPER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


cli = _load()


def _driver_tree() -> ast.Module:
    return ast.parse(DRIVER.read_text(encoding="utf-8"))


def _main(tree: ast.Module) -> ast.FunctionDef:
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")


def _steps_keys(tree: ast.Module) -> list[str]:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "STEPS" for t in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        keys: list[str] = []
        for key in node.value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.append(key.value)
        return keys
    raise AssertionError("STEPS dict not found at module level")


class ParseStepArgPreservesOperatorOrder(unittest.TestCase):
    def test_topostate_then_topo_stays_in_that_order(self) -> None:
        wanted, bad = cli.parse_step_arg("topostate,topo", _STEPS_INSERTION)
        self.assertEqual(wanted, ["topostate", "topo"])
        self.assertEqual(bad, [])

    def test_topo_then_topostate_stays_in_that_order(self) -> None:
        wanted, bad = cli.parse_step_arg("topo,topostate", _STEPS_INSERTION)
        self.assertEqual(wanted, ["topo", "topostate"])
        self.assertEqual(bad, [])

    def test_the_two_orders_are_not_the_same_list(self) -> None:
        a, _ = cli.parse_step_arg("topostate,topo", _STEPS_INSERTION)
        b, _ = cli.parse_step_arg("topo,topostate", _STEPS_INSERTION)
        self.assertNotEqual(a, b)

    def test_operator_order_is_not_steps_insertion_order(self) -> None:
        wanted, _ = cli.parse_step_arg("topostate,topo", _STEPS_INSERTION)
        insertion = [n for n in _STEPS_INSERTION if n in wanted]
        self.assertEqual(insertion, ["topo", "topostate"])
        self.assertEqual(wanted, ["topostate", "topo"])

    def test_unknown_step_is_listed_in_bad_and_kept_in_wanted(self) -> None:
        wanted, bad = cli.parse_step_arg("topo,nope", _STEPS_INSERTION)
        self.assertEqual(wanted, ["topo", "nope"])
        self.assertEqual(bad, ["nope"])

    def test_empty_and_whitespace_tokens_are_dropped(self) -> None:
        wanted, bad = cli.parse_step_arg(" topo, ,topostate ", _STEPS_INSERTION)
        self.assertEqual(wanted, ["topo", "topostate"])
        self.assertEqual(bad, [])

    def test_duplicates_are_preserved(self) -> None:
        wanted, bad = cli.parse_step_arg("topo,topo", _STEPS_INSERTION)
        self.assertEqual(wanted, ["topo", "topo"])
        self.assertEqual(bad, [])


class DriverWalksWantedNotSteps(unittest.TestCase):
    def test_driver_steps_keys_match_the_insertion_tuple(self) -> None:
        self.assertEqual(_steps_keys(_driver_tree()), list(_STEPS_INSERTION))

    def test_driver_steps_lists_topo_before_topostate(self) -> None:
        keys = _steps_keys(_driver_tree())
        self.assertIn("topo", keys)
        self.assertIn("topostate", keys)
        self.assertLess(keys.index("topo"), keys.index("topostate"))

    def test_main_calls_parse_step_arg(self) -> None:
        main = _main(_driver_tree())
        calls = [
            n.func.attr
            for n in ast.walk(main)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        ]
        names = [
            n.func.id
            for n in ast.walk(main)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        ]
        self.assertTrue(
            "parse_step_arg" in calls or "parse_step_arg" in names,
            "main() must call parse_step_arg so --step order is not re-inlined",
        )

    def test_main_iterates_wanted_not_steps(self) -> None:
        main = _main(_driver_tree())
        for_iters = []
        for node in ast.walk(main):
            if isinstance(node, ast.For) and isinstance(node.iter, ast.Name):
                for_iters.append(node.iter.id)
        self.assertIn("wanted", for_iters)
        self.assertNotIn("STEPS", for_iters)

    def test_unknown_step_returns_2(self) -> None:
        main = _main(_driver_tree())
        returns = [
            n.value.value
            for n in ast.walk(main)
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, int)
        ]
        self.assertIn(2, returns)

    def test_driver_loads_this_helper(self) -> None:
        source = DRIVER.read_text(encoding="utf-8")
        self.assertIn("e2e_topology_step_cli.py", source)

    def test_helper_refuses_to_run_as_a_script(self) -> None:
        source = HELPER.read_text(encoding="utf-8")
        self.assertIn("do not run it as a script", source)


if __name__ == "__main__":
    unittest.main()
