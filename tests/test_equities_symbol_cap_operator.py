#!/usr/bin/env python3
"""Operator-surface pins for the shipped 14-symbol equities refuse (data#354).

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

The refuse itself lives in juniper-data. This repo can still silently defeat it:

- A suite cell with ``dataset.generator: equities`` / ``equities_seq`` and no short
  ``symbols`` list (and no ``allow_truncation``) hits HTTP 422 against the bundled 503
  names. ``tests/test_experiment_suite_yamls.py`` never looks at generator or symbols.
- ``max_symbols`` alone does not save a default-universe cell — a request may only
  *lower* the deployment ceiling; 503 names still exceed 14.
- A cascor-path cell with ``equities_seq`` is ``ConfigError`` before any download
  (not in ``STAGEABLE_GENERATOR_ALIASES``). The recurrence E-H suite is the legitimate
  home for that generator.
- ``experiment_stack.bash`` ``data_up`` sets ``JUNIPER_DATA_EQUITIES_CACHE_DIR`` and
  must not assign ``JUNIPER_DATA_EQUITIES_MAX_SYMBOLS`` or
  ``JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION``. Existing stack tests only assert the
  cache dir is *present* — a helpful ``ALLOW_TRUNCATION=true`` would stay green and
  opt the whole stack into prefix cuts.

Hermetic: YAML + script-text only. No live data service, no yfinance, no network.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITES_ROOT = REPO_ROOT / "util" / "experiments" / "suites"
STACK_PATH = REPO_ROOT / "util" / "experiment_stack.bash"
DRIVER_PATH = REPO_ROOT / "util" / "experiments" / "run_experiment.py"

EQUITIES_GENERATORS = frozenset({"equities", "equities_seq"})
SYMBOL_CAP = 14
CACHE_DIR_VAR = "JUNIPER_DATA_EQUITIES_CACHE_DIR"
CAP_VARS = (
    "JUNIPER_DATA_EQUITIES_MAX_SYMBOLS",
    "JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION",
)
_ASSIGN = re.compile(
    r"\b(?P<name>JUNIPER_DATA_EQUITIES_(?:MAX_SYMBOLS|ALLOW_TRUNCATION|CACHE_DIR))\s*="
)


def _suite_files() -> list[Path]:
    return sorted(p for p in SUITES_ROOT.rglob("*.yaml") if p.is_file())


def _dataset_params(overrides: dict[str, Any]) -> dict[str, Any]:
    """Collect ``dataset.params`` from dotted, nested, or wholesale-dict forms."""
    params: dict[str, Any] = {}
    wholesale = overrides.get("dataset.params")
    if isinstance(wholesale, dict):
        params.update(wholesale)
    nested = overrides.get("dataset")
    if isinstance(nested, dict) and isinstance(nested.get("params"), dict):
        params.update(nested["params"])
    prefix = "dataset.params."
    for key, value in overrides.items():
        if isinstance(key, str) and key.startswith(prefix):
            params[key[len(prefix) :]] = value
    return params


def _generator(overrides: dict[str, Any]) -> str | None:
    dotted = overrides.get("dataset.generator")
    if isinstance(dotted, str):
        return dotted
    nested = overrides.get("dataset")
    if isinstance(nested, dict) and isinstance(nested.get("generator"), str):
        return nested["generator"]
    return None


def equities_cell_verdict(overrides: dict[str, Any]) -> str | None:
    """How an override map sits against the 14-symbol refuse.

    ``None`` — not an equities cell.
    ``ok-short-list`` — explicit ``symbols`` of length 1..14.
    ``ok-opt-in`` — ``allow_truncation`` is YAML true (authorised prefix cut).
    ``refuse`` — would 422 against the default 503-name universe.
    """
    generator = _generator(overrides)
    if generator not in EQUITIES_GENERATORS:
        return None
    params = _dataset_params(overrides)
    if params.get("allow_truncation") is True:
        return "ok-opt-in"
    symbols = params.get("symbols")
    if isinstance(symbols, list) and 1 <= len(symbols) <= SYMBOL_CAP:
        return "ok-short-list"
    return "refuse"


def iter_override_maps(doc: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Named override maps a suite can produce without resolving sibling base_config."""
    found: list[tuple[str, dict[str, Any]]] = []
    for item in doc.get("include") or []:
        if not isinstance(item, dict):
            continue
        overrides = item.get("overrides") or {}
        if isinstance(overrides, dict):
            name = str(item.get("name") or "include")
            found.append((name, overrides))
    matrix = doc.get("matrix") or {}
    if isinstance(matrix, dict):
        gens = matrix.get("dataset.generator")
        if isinstance(gens, list):
            for idx, gen in enumerate(gens):
                if isinstance(gen, str):
                    found.append((f"matrix[{idx}]", {"dataset.generator": gen}))
    return found


def iter_equities_cells(doc: dict[str, Any]) -> list[tuple[str, dict[str, Any], str]]:
    cells: list[tuple[str, dict[str, Any], str]] = []
    for name, overrides in iter_override_maps(doc):
        verdict = equities_cell_verdict(overrides)
        if verdict is not None:
            cells.append((name, overrides, verdict))
    return cells


def assigned_equities_env(text: str) -> dict[str, list[str]]:
    """Every assignment of the three equities env vars, keyed by name."""
    found: dict[str, list[str]] = {CACHE_DIR_VAR: [], **{name: [] for name in CAP_VARS}}
    for match in _ASSIGN.finditer(text):
        found[match.group("name")].append(match.group(0))
    return found


def _extract_fn(script: str, name: str) -> str:
    header = re.search(rf"^{re.escape(name)}\(\)\s*\{{", script, re.MULTILINE)
    if header is None:
        raise AssertionError(f"{name}() not found")
    start = header.start()
    depth = 0
    for idx, char in enumerate(script[start:], start=start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return script[start : idx + 1]
    raise AssertionError(f"{name}() is unclosed")


def _stageable_aliases() -> set[str]:
    text = DRIVER_PATH.read_text(encoding="utf-8")
    block = re.search(r"^STAGEABLE_GENERATOR_ALIASES:.*?=\s*\{(.*?)^\}", text, re.MULTILINE | re.DOTALL)
    if block is None:
        raise AssertionError("STAGEABLE_GENERATOR_ALIASES dict not found in run_experiment.py")
    return set(re.findall(r'"([a-z_]+)"\s*:', block.group(1)))


class EquitiesVerdictUnitTest(unittest.TestCase):
    """Predicate arms the shipped-suite scan cannot see (synthetics)."""

    def test_cap_is_the_shipped_fourteen(self) -> None:
        """data#354 shipped 14; raising this constant would bless a 15-name list."""
        self.assertEqual(SYMBOL_CAP, 14)

    def test_short_list_holds(self) -> None:
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {"symbols": ["AAPL"]}}),
            "ok-short-list",
        )
        fourteen = [f"S{i:02d}" for i in range(SYMBOL_CAP)]
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities_seq", "dataset.params": {"symbols": fourteen}}),
            "ok-short-list",
        )

    def test_default_universe_refuses(self) -> None:
        self.assertEqual(equities_cell_verdict({"dataset.generator": "equities"}), "refuse")
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {}}),
            "refuse",
        )

    def test_empty_and_oversized_lists_refuse(self) -> None:
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {"symbols": []}}),
            "refuse",
        )
        fifteen = [f"S{i:02d}" for i in range(SYMBOL_CAP + 1)]
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {"symbols": fifteen}}),
            "refuse",
        )

    def test_max_symbols_alone_does_not_opt_in(self) -> None:
        """A request may only lower the ceiling; 503 names still exceed 14."""
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {"max_symbols": 10}}),
            "refuse",
        )
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {"max_symbols": 50}}),
            "refuse",
        )

    def test_allow_truncation_opts_in(self) -> None:
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {"allow_truncation": True}}),
            "ok-opt-in",
        )
        fifteen = [f"S{i:02d}" for i in range(SYMBOL_CAP + 1)]
        self.assertEqual(
            equities_cell_verdict(
                {"dataset.generator": "equities", "dataset.params": {"symbols": fifteen, "allow_truncation": True}}
            ),
            "ok-opt-in",
        )

    def test_string_true_is_not_opt_in(self) -> None:
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params": {"allow_truncation": "true"}}),
            "refuse",
        )

    def test_non_equities_is_out_of_scope(self) -> None:
        self.assertIsNone(equities_cell_verdict({"dataset.generator": "spiral"}))
        self.assertIsNone(equities_cell_verdict({"dataset.generator": "xor", "dataset.params": {"symbols": ["AAPL"]}}))
        self.assertIsNone(equities_cell_verdict({}))

    def test_dotted_and_nested_forms(self) -> None:
        self.assertEqual(
            equities_cell_verdict({"dataset.generator": "equities", "dataset.params.symbols": ["MSFT"]}),
            "ok-short-list",
        )
        self.assertEqual(
            equities_cell_verdict({"dataset": {"generator": "equities", "params": {"symbols": ["GOOGL"]}}}),
            "ok-short-list",
        )


class ShippedSuiteEquitiesCapTest(unittest.TestCase):
    """Every shipped equities cell must stay inside the refuse, or opt in."""

    def test_suite_files_are_discovered(self) -> None:
        self.assertTrue(_suite_files(), f"no suite YAMLs under {SUITES_ROOT}")

    def test_known_e_h_cells_are_visible(self) -> None:
        """Anti-vacuous: if include-overrides are skipped, the gate would pass on zero cells."""
        names: set[str] = set()
        for path in _suite_files():
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(doc, dict):
                continue
            for cell_name, _overrides, _verdict in iter_equities_cells(doc):
                names.add(f"{path.name}:{cell_name}")
        self.assertIn("e-h-real-data.yaml:equities-aapl", names)
        self.assertIn("e-h-recurrence-real-data.yaml:equities-seq-aapl", names)

    def test_shipped_equities_cells_hold_the_refuse(self) -> None:
        failures: list[str] = []
        for path in _suite_files():
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(doc, dict):
                continue
            for cell_name, overrides, verdict in iter_equities_cells(doc):
                if verdict == "refuse":
                    failures.append(f"{path.relative_to(REPO_ROOT)}:{cell_name} {_generator(overrides)} -> {verdict}")
        self.assertEqual(failures, [], "suite cells that would 422 against the default 503-name universe")

    def test_e_h_is_a_one_symbol_list_without_opt_in(self) -> None:
        """Docs: E-H sets symbols: [AAPL] and does not set max_symbols or allow_truncation."""
        for rel in (
            "p4/e-h-real-data.yaml",
            "p4/e-h-recurrence-real-data.yaml",
        ):
            path = SUITES_ROOT / rel
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            cells = iter_equities_cells(doc)
            self.assertEqual(len(cells), 1, rel)
            _name, overrides, verdict = cells[0]
            self.assertEqual(verdict, "ok-short-list", rel)
            params = _dataset_params(overrides)
            self.assertEqual(params.get("symbols"), ["AAPL"], rel)
            self.assertNotIn("allow_truncation", params, rel)
            self.assertNotIn("max_symbols", params, rel)

    def test_cascor_suites_do_not_stage_equities_seq(self) -> None:
        stageable = _stageable_aliases()
        self.assertIn("equities", stageable)
        self.assertNotIn("equities_seq", stageable)
        failures: list[str] = []
        for path in _suite_files():
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(doc, dict):
                continue
            app = (doc.get("suite") or {}).get("app")
            if app != "cascor":
                continue
            for cell_name, overrides, _verdict in iter_equities_cells(doc):
                if _generator(overrides) == "equities_seq":
                    failures.append(f"{path.name}:{cell_name}")
        self.assertEqual(failures, [], "cascor cells with equities_seq are ConfigError before download")


class ExperimentStackDoesNotSetTheCapTest(unittest.TestCase):
    """data_up sets the cache dir and inherits the deployment ceiling / opt-in."""

    def test_data_up_sets_cache_dir_at_every_site(self) -> None:
        script = STACK_PATH.read_text(encoding="utf-8")
        data_up = _extract_fn(script, "data_up")
        assigned = assigned_equities_env(data_up)
        self.assertGreaterEqual(
            len(assigned[CACHE_DIR_VAR]),
            3,
            "announce + record_launch_env + nohup launch must all set the cache dir",
        )
        self.assertIn("${RUN_DIR}/equities-cache", data_up)

    def test_data_up_does_not_assign_cap_or_opt_in(self) -> None:
        script = STACK_PATH.read_text(encoding="utf-8")
        data_up = _extract_fn(script, "data_up")
        assigned = assigned_equities_env(data_up)
        self.assertEqual(assigned[CAP_VARS[0]], [])
        self.assertEqual(assigned[CAP_VARS[1]], [])

    def test_whole_script_does_not_assign_cap_or_opt_in(self) -> None:
        script = STACK_PATH.read_text(encoding="utf-8")
        assigned = assigned_equities_env(script)
        self.assertEqual(assigned[CAP_VARS[0]], [])
        self.assertEqual(assigned[CAP_VARS[1]], [])
        self.assertTrue(assigned[CACHE_DIR_VAR], "CACHE_DIR must still be assigned somewhere")

    def test_assignment_scanner_sees_a_planted_cap(self) -> None:
        """Negative control: a comment mentioning the name is fine; an assignment is not."""
        planted = 'export JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION=true\n# JUNIPER_DATA_EQUITIES_MAX_SYMBOLS mentioned\n'
        assigned = assigned_equities_env(planted)
        self.assertEqual(assigned[CAP_VARS[1]], ["JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION="])
        self.assertEqual(assigned[CAP_VARS[0]], [])


if __name__ == "__main__":
    unittest.main()
