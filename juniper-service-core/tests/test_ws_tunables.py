"""Tests for juniper_service_core.websocket.tunables (APD-SVCCORE-003 / -010).

What is being defended
----------------------
The WebSocket handlers read tunables off a consuming service's settings object with
``getattr(settings, name, default)``. That decoupling is deliberate and stays; what it
cost was that **a misspelled settings field was indistinguishable from an unconfigured
one**, and six of the eleven tunables are security controls. This suite pins:

- the registry is the single source of truth, and its defaults are **byte-for-byte the
  literals the call sites used before the refactor** (``PRE_REFACTOR_DEFAULTS``) -- a
  transcription slip here would silently change a security control's fallback, which is
  the very failure mode being fixed;
- **every call site resolves a declared name** (source-scanned, so adding an
  undeclared tunable fails here rather than at runtime);
- a near-miss is loud and a plain unconfigured tunable is quiet -- the WARNING is the
  entire point, so it is asserted, not assumed;
- ``audit`` reports the security subset and the suspected typos a service can surface
  at boot;
- the module adds no web-stack dependency of its own (its imports are stdlib, and it
  loads standalone with fastapi blocked) -- see TestStdlibOnly for the honest limit.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest

from juniper_service_core.websocket.tunables import (
    NEAR_MATCH_CUTOFF,
    SECURITY_TUNABLES,
    WS_TUNABLES,
    UnknownTunableError,
    audit,
    resolve,
)

_WS_DIR = Path(__file__).resolve().parent.parent / "juniper_service_core" / "websocket"
_HANDLERS = ("control_stream.py", "training_stream.py")

#: The literal defaults each call site carried BEFORE the registry existed. Pinned so a
#: transcription error during the refactor cannot silently change a fallback.
PRE_REFACTOR_DEFAULTS = {
    "ws_control_cooldown_rejections": 10,
    "ws_control_cooldown_window_sec": 60,
    "ws_control_cooldown_block_sec": 300,
    "disable_ws_control_endpoint": False,
    "ws_control_allowed_origins": None,
    "ws_control_rate_limit_per_sec": 10,
    "ws_control_idle_timeout_sec": 120,
    "ws_heartbeat_interval_sec": 30,
    "ws_heartbeat_pong_timeout_sec": 10,
    "ws_resume_handshake_timeout_s": 5.0,
    "ws_initial_metrics_count": 100,
}

#: The six the register classifies as security controls.
EXPECTED_SECURITY = {
    "disable_ws_control_endpoint",
    "ws_control_allowed_origins",
    "ws_control_rate_limit_per_sec",
    "ws_control_cooldown_rejections",
    "ws_control_cooldown_window_sec",
    "ws_control_cooldown_block_sec",
}


class _Settings:
    """A stand-in for a consuming service's settings object."""

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class TestRegistry:
    def test_defaults_match_the_pre_refactor_literals(self):
        assert {name: t.default for name, t in WS_TUNABLES.items()} == PRE_REFACTOR_DEFAULTS

    def test_security_subset_is_exactly_the_registers_six(self):
        assert set(SECURITY_TUNABLES) == EXPECTED_SECURITY
        assert len(SECURITY_TUNABLES) == 6

    def test_every_tunable_is_self_named(self):
        for name, tunable in WS_TUNABLES.items():
            assert tunable.name == name

    def test_every_tunable_carries_a_note(self):
        """The note is what makes the audit output actionable to an operator."""
        for name, tunable in WS_TUNABLES.items():
            assert tunable.note.strip(), f"{name} has no note"


class TestCallSiteDrift:
    """Source-scan gate: the registry and the handlers must not drift apart."""

    @staticmethod
    def _call_site_names() -> set[str]:
        names: set[str] = set()
        for fn in _HANDLERS:
            src = (_WS_DIR / fn).read_text(encoding="utf-8")
            names |= set(re.findall(r'_setting\(websocket,\s*"([a-z0-9_]+)"\s*\)', src))
        return names

    def test_every_call_site_resolves_a_declared_tunable(self):
        undeclared = self._call_site_names() - set(WS_TUNABLES)
        assert not undeclared, f"call sites reference undeclared tunables: {sorted(undeclared)}"

    def test_every_declared_tunable_is_actually_used(self):
        """A registry entry nobody reads is dead weight that will rot."""
        unused = set(WS_TUNABLES) - self._call_site_names()
        assert not unused, f"declared but never read: {sorted(unused)}"

    def test_no_call_site_still_passes_an_inline_default(self):
        """The default lives in the registry now; a second source of truth would drift."""
        for fn in _HANDLERS:
            src = (_WS_DIR / fn).read_text(encoding="utf-8")
            leftovers = re.findall(r'_setting\(websocket,\s*"[a-z0-9_]+"\s*,', src)
            assert not leftovers, f"{fn} still passes inline defaults: {leftovers}"

    def test_setting_helper_is_not_duplicated_by_body(self):
        """APD-SVCCORE-010: the two byte-identical implementations are gone.

        Each handler keeps a thin module-local ``_setting`` that delegates, but the
        old duplicated body -- which re-implemented the getattr chain -- must not
        reappear in either file.
        """
        for fn in _HANDLERS:
            src = (_WS_DIR / fn).read_text(encoding="utf-8")
            assert "getattr(settings, name, default)" not in src, f"{fn} re-implements the resolver"
            assert "from juniper_service_core.websocket.tunables import resolve" in src


class TestResolve:
    def test_configured_value_wins(self):
        assert resolve(_Settings(ws_control_rate_limit_per_sec=99), "ws_control_rate_limit_per_sec") == 99

    def test_falsy_configured_value_is_not_treated_as_missing(self):
        """0 and False are legitimate configured values, not 'unset'.

        A ``getattr(...) or default`` implementation would silently replace a
        deliberate 0 rate limit with the default of 10 -- turning a lockdown into a
        permissive setting.
        """
        assert resolve(_Settings(ws_control_rate_limit_per_sec=0), "ws_control_rate_limit_per_sec") == 0
        assert resolve(_Settings(disable_ws_control_endpoint=False), "disable_ws_control_endpoint") is False

    def test_absent_field_falls_back_to_declared_default(self):
        assert resolve(_Settings(), "ws_control_rate_limit_per_sec") == 10

    def test_none_settings_falls_back_to_declared_default(self):
        assert resolve(None, "ws_control_idle_timeout_sec") == 120

    def test_unknown_name_raises_rather_than_defaulting(self):
        with pytest.raises(UnknownTunableError):
            resolve(_Settings(), "ws_control_nonexistent_knob")


class TestNearMissWarning:
    """The named real-world failure: ``..._per_second`` where the library reads ``..._per_sec``."""

    def test_probable_typo_is_warned_naming_both_spellings(self, caplog):
        settings = _Settings(ws_control_rate_limit_per_second=1)
        with caplog.at_level(logging.WARNING, logger="juniper_service_core.websocket.tunables"):
            value = resolve(settings, "ws_control_rate_limit_per_sec")
        assert value == 10, "the misspelled field must NOT be read"
        assert len(caplog.records) == 1
        msg = caplog.records[0].getMessage()
        assert "ws_control_rate_limit_per_sec" in msg
        assert "ws_control_rate_limit_per_second" in msg
        assert "SECURITY CONTROL" in msg

    def test_plain_unconfigured_tunable_does_not_warn(self, caplog):
        """Most services configure only a few tunables; the rest must stay quiet."""
        with caplog.at_level(logging.WARNING, logger="juniper_service_core.websocket.tunables"):
            resolve(_Settings(unrelated_field=1), "ws_initial_metrics_count")
        assert caplog.records == []

    def test_merely_related_names_are_not_flagged_as_typos(self, caplog):
        """A settings object carrying a *sibling* tunable is not a misspelling.

        Guards the cutoff: too low and every heartbeat setting accuses its neighbour.
        """
        settings = _Settings(ws_heartbeat_interval_sec=5)
        with caplog.at_level(logging.WARNING, logger="juniper_service_core.websocket.tunables"):
            resolve(settings, "ws_heartbeat_pong_timeout_sec")
        assert caplog.records == []

    def test_cutoff_is_documented_and_sane(self):
        assert 0.0 < NEAR_MATCH_CUTOFF < 1.0


class TestAudit:
    def test_none_settings_defaults_everything(self):
        result = audit(None)
        assert result.configured == []
        assert set(result.defaulted) == set(WS_TUNABLES)
        assert set(result.defaulted_security) == EXPECTED_SECURITY
        assert result.suspected_typos == []
        assert result.has_findings is True

    def test_fully_configured_settings_has_no_findings(self):
        result = audit(_Settings(**{name: t.default for name, t in WS_TUNABLES.items()}))
        assert set(result.configured) == set(WS_TUNABLES)
        assert result.defaulted == []
        assert result.has_findings is False
        assert result.render() == ""

    def test_typo_is_reported_with_the_actual_attribute(self):
        result = audit(_Settings(ws_control_rate_limit_per_second=1))
        assert ("ws_control_rate_limit_per_sec", "ws_control_rate_limit_per_second") in result.suspected_typos
        assert result.has_findings is True

    def test_render_names_the_typo_and_the_defaulted_security_controls(self):
        text = audit(_Settings(ws_control_rate_limit_per_second=1)).render()
        assert "ws_control_rate_limit_per_second" in text
        assert "ws_control_allowed_origins" in text
        assert "fail-closed Origin allowlist" in text

    def test_non_security_defaults_alone_are_not_findings(self):
        """Defaulting a heartbeat interval is normal; defaulting an allowlist is not."""
        configured = {name: t.default for name, t in WS_TUNABLES.items() if t.security}
        result = audit(_Settings(**configured))
        assert result.defaulted_security == []
        assert result.defaulted, "non-security tunables should still be listed as defaulted"
        assert result.has_findings is False


class TestStdlibOnly:
    """The module's OWN imports carry no web stack.

    Deliberately does NOT claim the package path is importable without fastapi:
    ``juniper_service_core.websocket.__init__`` imports it, so it is not. An earlier
    version of this test asserted otherwise and failed, which is why the claim is
    stated narrowly here and in the module docstring. What is true, and what matters,
    is that this module adds no web-stack dependency of its own -- so ``audit`` stays
    cheap and the registry can be scanned without building an app.
    """

    def test_module_source_imports_only_stdlib(self):
        import ast

        src = (_WS_DIR / "tunables.py").read_text(encoding="utf-8")
        roots = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                roots |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
        allowed = {"__future__", "difflib", "logging", "dataclasses", "typing"}
        assert roots <= allowed, f"unexpected imports: {sorted(roots - allowed)}"

    def test_module_loads_standalone_with_the_web_stack_blocked(self):
        """Load by file path, bypassing the package __init__, with fastapi blocked."""
        import subprocess  # nosec B404 - fixed argv, no shell
        import sys

        target = str(_WS_DIR / "tunables.py")
        code = (
            "import importlib.util, sys\n"
            "for m in ('fastapi', 'pydantic', 'pydantic_settings'):\n"
            "    sys.modules[m] = None\n"
            f"spec = importlib.util.spec_from_file_location('t', {target!r})\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            # dataclass() resolves its module via sys.modules, so register first.
            "sys.modules['t'] = mod\n"
            "spec.loader.exec_module(mod)\n"
            "assert mod.audit(None).defaulted_security\n"
            "print('ok')\n"
        )
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)  # nosec B603
        assert proc.returncode == 0, proc.stderr
        assert "ok" in proc.stdout
