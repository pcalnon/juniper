#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/canopy_poller_inventory.py`` -- the AST census of
interval-driven Dash callbacks that sizes the F-CANOPY-027 12-slot starvation
budget.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the
gate. Hermetic: every fixture is a TemporaryDirectory of synthetic ``.py``
files; nothing reads a sibling canopy checkout.

Why this census has to be right in BOTH directions (same class as the X7
offload gate that certified a partial fix):

- Missing a poller under-states concurrent load and makes a 12-slot budget look
  healthy while a live tab is still starving.
- Counting a click handler as a poller, or treating an ungated interval as
  tab-gated, makes the always-on set look smaller than it is -- the dangerous
  direction. Sibling ``canopy_poller_budget_probe.py`` already records that the
  AST walk resolves only 151 of 182 callbacks; these pins keep that hole from
  widening silently, and they lock the paths the census *does* claim to see.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "canopy_poller_inventory.py"


def _load():
    spec = importlib.util.spec_from_file_location("canopy_poller_inventory", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


PLAIN_POLLER = """
class Panel:
    def register(self, app):
        @app.callback(Output("store", "data"), Input("global-interval", "n_intervals"))
        def tick(_n):
            return {}
"""

FSTRING_POLLER = """
class MetricsPanel:
    def __init__(self, component_id="metrics-poll"):
        self.component_id = component_id

    def register(self, app):
        @app.callback(
            Output(f"{self.component_id}-store", "data"),
            Input(f"{self.component_id}-interval", "n_intervals"),
        )
        def tick(_n):
            return {}
"""

UNRESOLVABLE_FSTRING = """
class OtherPanel:
    def register(self, app):
        @app.callback(
            Output("store", "data"),
            Input(f"{self.other_attr}-interval", "n_intervals"),
        )
        def tick(_n):
            return {}
"""

CLICK_ONLY = """
class Panel:
    def register(self, app):
        @app.callback(Output("store", "data"), Input("go-btn", "n_clicks"))
        def on_click(_n):
            return {}
"""

TAB_INPUT = """
class Panel:
    def register(self, app):
        @app.callback(
            Output("store", "data"),
            Input("fast-interval", "n_intervals"),
            Input("visualization-tabs", "active_tab"),
        )
        def tick(_n, _tab):
            return {}
"""

TAB_STATE = """
class Panel:
    def register(self, app):
        @app.callback(
            Output("store", "data"),
            Input("fast-interval", "n_intervals"),
            State("visualization-tabs", "active_tab"),
        )
        def tick(_n, _tab):
            return {}
"""

WRONG_TAB_ID = """
class Panel:
    def register(self, app):
        @app.callback(
            Output("store", "data"),
            Input("fast-interval", "n_intervals"),
            Input("viz-tabs", "active_tab"),
        )
        def tick(_n, _tab):
            return {}
"""

BARE_CALLBACK = """
from dash import callback, Input, Output

@callback(Output("store", "data"), Input("global-interval", "n_intervals"))
def tick(_n):
    return {}
"""

KEYWORD_INPUT = """
class Panel:
    def register(self, app):
        @app.callback(
            Output("store", "data"),
            Input(component_id="global-interval", component_property="n_intervals"),
        )
        def tick(_n):
            return {}
"""

TWO_INTERVALS = """
class Panel:
    def register(self, app):
        @app.callback(
            Output("store", "data"),
            Input("fast-interval", "n_intervals"),
            Input("slow-interval", "n_intervals"),
        )
        def tick(_a, _b):
            return {}
"""

BODY_ASSIGNED_ID = """
class Panel:
    def __init__(self):
        self.component_id = "body-poll"

    def register(self, app):
        @app.callback(
            Output("store", "data"),
            Input(f"{self.component_id}-interval", "n_intervals"),
        )
        def tick(_n):
            return {}
"""

ATTR_DEPS = """
class Panel:
    def register(self, app):
        @self.app.callback(
            dash.Output("store", "data"),
            dash.Input("global-interval", "n_intervals"),
        )
        def tick(_n):
            return {}
"""


def _analyse(src: str, name: str = "panel.py"):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(src, encoding="utf-8")
        return mod.analyse_file(str(path))


def _pollers(rows):
    return [r for r in rows if r["intervals"]]


class AnalyseFileTest(unittest.TestCase):
    def test_plain_string_n_intervals_is_a_poller(self):
        rows = _analyse(PLAIN_POLLER)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["intervals"], ["global-interval"])
        self.assertEqual(rows[0]["func"], "tick")
        self.assertFalse(rows[0]["tab_input"])
        self.assertFalse(rows[0]["tab_state"])

    def test_fstring_component_id_resolves_from_init_default(self):
        """The designed path: ``f"{self.component_id}-interval"`` + ``__init__`` default."""
        rows = _analyse(FSTRING_POLLER)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["intervals"], ["metrics-poll-interval"])
        self.assertEqual(rows[0]["outputs"], [("metrics-poll-store", "data")])

    def test_unresolvable_fstring_does_not_invent_an_interval_id(self):
        """Known undercount: an f-string the walker cannot resolve is dropped, not guessed.

        Inventing an id would be a different lie; dropping it is why the sibling
        budget probe exists (151 of 182). Pin both: no invented token, and the
        callback is therefore NOT a poller -- a widening of this hole (also
        dropping resolvable f-strings) is what these tests exist to catch.
        """
        rows = _analyse(UNRESOLVABLE_FSTRING)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["intervals"], [])
        self.assertEqual(_pollers(rows), [])

    def test_click_input_is_not_a_poller(self):
        rows = _analyse(CLICK_ONLY)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["intervals"], [])
        self.assertEqual(_pollers(rows), [])

    def test_tab_as_input_is_gated_input(self):
        rows = _analyse(TAB_INPUT)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["tab_input"])
        self.assertFalse(rows[0]["tab_state"])
        self.assertEqual(rows[0]["intervals"], ["fast-interval"])

    def test_tab_as_state_is_gated_state_not_input(self):
        """Markdown prints ``Input`` if tab_input else ``State``. Conflating the
        two hides whether the tab is a claimed Input (costs a slot on every tab
        change) or only a State (read when the interval fires)."""
        rows = _analyse(TAB_STATE)
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["tab_input"])
        self.assertTrue(rows[0]["tab_state"])

    def test_near_miss_tab_id_is_ungated(self):
        """``visualization-tabs`` is exact. A renamed tab id silently moves the
        poller into the always-on bucket -- or, if the constant loosens, an
        unrelated Input would look silencable."""
        rows = _analyse(WRONG_TAB_ID)
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["tab_input"])
        self.assertFalse(rows[0]["tab_state"])
        self.assertEqual(rows[0]["intervals"], ["fast-interval"])

    def test_two_intervals_on_one_callback_are_both_counted(self):
        rows = _analyse(TWO_INTERVALS)
        self.assertEqual(rows[0]["intervals"], ["fast-interval", "slow-interval"])

    def test_attribute_form_deps_and_self_app_callback(self):
        rows = _analyse(ATTR_DEPS)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["intervals"], ["global-interval"])
        self.assertEqual(rows[0]["outputs"], [("store", "data")])

    def test_bare_callback_name_is_currently_invisible(self):
        """Characterization of a miss: ``@callback(...)`` is a Name, and the
        walker only accepts ``<expr>.callback``. A file that imported the
        decorator directly would vanish from the census -- the same
        expression-shape hole the X7 gate had."""
        rows = _analyse(BARE_CALLBACK)
        self.assertEqual(rows, [])

    def test_keyword_input_form_is_currently_invisible(self):
        """Characterization: only positional ``Input(id, prop)`` is read.
        ``Input(component_id=..., component_property=...)`` is a live Dash
        spelling and is dropped today."""
        rows = _analyse(KEYWORD_INPUT)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["intervals"], [])

    def test_body_assigned_component_id_does_not_resolve(self):
        """Only the ``__init__`` default is consulted. An assignment in the
        body is the other half of the 151/182 undercount."""
        rows = _analyse(BODY_ASSIGNED_ID)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["intervals"], [])

    def test_syntax_error_file_is_skipped_not_raised(self):
        rows = _analyse("def broken(\n")
        self.assertEqual(rows, [])


class MainWalkTest(unittest.TestCase):
    def test_nested_directory_walk_finds_every_poller(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "top.py").write_text(PLAIN_POLLER, encoding="utf-8")
            nested = root / "panels"
            nested.mkdir()
            (nested / "inner.py").write_text(FSTRING_POLLER, encoding="utf-8")
            (nested / "notes.txt").write_text(PLAIN_POLLER, encoding="utf-8")
            buf = io.StringIO()
            with patch.object(sys, "argv", ["canopy_poller_inventory.py", "--root", str(root)]):
                with redirect_stdout(buf):
                    rc = mod.main()
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("callbacks found            : 2", out)
            self.assertIn("interval-driven (pollers)  : 2", out)
            self.assertIn("un-gated pollers    : 2", out)
            self.assertIn("global-interval", out)
            self.assertIn("metrics-poll-interval", out)

    def test_markdown_distinguishes_input_gate_from_state_gate(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "input_gate.py").write_text(TAB_INPUT, encoding="utf-8")
            (root / "state_gate.py").write_text(TAB_STATE, encoding="utf-8")
            (root / "open.py").write_text(PLAIN_POLLER, encoding="utf-8")
            buf = io.StringIO()
            with patch.object(sys, "argv", ["canopy_poller_inventory.py", "--root", str(root), "--markdown"]):
                with redirect_stdout(buf):
                    rc = mod.main()
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertRegex(out, r"input_gate\.py:\d+.*\| Input \|")
            self.assertRegex(out, r"state_gate\.py:\d+.*\| State \|")
            self.assertRegex(out, r"open\.py:\d+.*\| — \|")


if __name__ == "__main__":
    unittest.main()
