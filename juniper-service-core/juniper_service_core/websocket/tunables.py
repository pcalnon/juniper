"""Declared registry for the WebSocket tunables read off a consuming service's settings.

Project: juniper-service-core
Author: Paul Calnon
License: MIT License

Why this exists (APD-SVCCORE-003 / APD-SVCCORE-010)
---------------------------------------------------
The WebSocket handlers read their tunables with ``getattr(settings, name, default)``,
guarded by ``getattr(app.state, "settings", None)`` -- both defaulted. That
indirection buys something real, and the trade is deliberate: the shared package
never imports a consuming service's settings class, and each service declares only
the tunables it actually uses. Nothing here gives that up.

What it *cost* is that **a misspelled settings field is indistinguishable from an
unconfigured one**. Eleven distinct tunables are read this way and **six of them are
security controls** -- the fail-closed Origin allowlist, the control-endpoint kill
switch, the control rate limit, and the three handshake-cooldown parameters. Writing
``ws_control_rate_limit_per_second`` where the library reads ``..._per_sec`` reverts
the control WebSocket to library defaults silently, forever, with no log line and no
test able to see it. The naming is not uniformly regular either --
``ws_resume_handshake_timeout_s`` ends ``_s`` where every other duration ends
``_sec`` -- which is exactly the shape that invites a typo.

This module changes two things and keeps everything else:

1. **The default lives in the registry, not at the call site.** Previously each of the
   13 call sites carried its own literal default, so the set of tunables existed only
   as an emergent property of the code. Now it is declared, which is what makes it
   auditable at all.
2. **A miss that looks like a typo is loud.** On a miss the resolver looks for a
   near-match among the settings object's own attributes; finding one means the
   service almost certainly meant to configure this and misspelled it, so it logs a
   WARNING naming both spellings. A miss with no near-match is an ordinary
   unconfigured tunable and stays quiet at DEBUG.

:func:`audit` is the boot-time counterpart: it reports which security tunables are
running on library defaults and which look like typos, so a service can surface that
once at startup instead of never.

Stdlib-only on purpose -- this module itself imports no ``fastapi`` and no
``pydantic``, so :func:`audit` is cheap to call and cheap to test, and the registry
can be reasoned about (or scanned by a drift test) without constructing a web app.

Note the honest limit of that: importing it by its package path still executes
``juniper_service_core.websocket.__init__``, which *does* import fastapi. The
stdlib-only property is about this module's own dependencies, not a promise that
``from juniper_service_core.websocket.tunables import audit`` works in an environment
without fastapi installed. Any service reaching the WebSocket layer already has it.
"""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass, field
from typing import Any, Mapping

# Public surface. Declared explicitly because several of these exist for
# *consumers* rather than for this module's own internals -- notably
# ``SECURITY_TUNABLES``, which a service uses to check just the security subset
# and which CodeQL otherwise (correctly) reports as an unused global.
__all__ = [
    "NEAR_MATCH_CUTOFF",
    "SECURITY_TUNABLES",
    "SettingsAudit",
    "Tunable",
    "UnknownTunableError",
    "WS_TUNABLES",
    "audit",
    "resolve",
]

logger = logging.getLogger("juniper_service_core.websocket.tunables")

#: Similarity threshold for treating a settings attribute as a probable misspelling.
#: 0.8 accepts ``ws_control_rate_limit_per_second`` vs ``..._per_sec`` (the named
#: real-world case) while rejecting merely-related names such as
#: ``ws_heartbeat_interval_sec`` vs ``ws_heartbeat_pong_timeout_sec``.
NEAR_MATCH_CUTOFF = 0.8


@dataclass(frozen=True)
class Tunable:
    """One settings field the WebSocket layer reads off the consuming service."""

    name: str
    default: Any
    security: bool = False
    note: str = ""


def _t(name: str, default: Any, *, security: bool = False, note: str = "") -> Tunable:
    return Tunable(name=name, default=default, security=security, note=note)


#: Every tunable the WebSocket handlers read, with its default. This is the single
#: source of truth: call sites pass only the name. ``security=True`` marks a control
#: whose silent reversion to a default is a security regression rather than a
#: configuration inconvenience.
WS_TUNABLES: Mapping[str, Tunable] = {
    t.name: t
    for t in (
        # --- control-plane security controls -------------------------------------
        _t("disable_ws_control_endpoint", False, security=True, note="kill switch for /ws/control"),
        _t("ws_control_allowed_origins", None, security=True, note="fail-closed Origin allowlist"),
        _t("ws_control_rate_limit_per_sec", 10, security=True, note="control-command rate limit"),
        _t("ws_control_cooldown_rejections", 10, security=True, note="handshake cooldown: rejections before block"),
        _t("ws_control_cooldown_window_sec", 60, security=True, note="handshake cooldown: rejection window"),
        _t("ws_control_cooldown_block_sec", 300, security=True, note="handshake cooldown: block duration"),
        # --- liveness / sizing (not security controls) ---------------------------
        _t("ws_control_idle_timeout_sec", 120, note="idle disconnect for /ws/control"),
        _t("ws_heartbeat_interval_sec", 30, note="heartbeat ping interval"),
        _t("ws_heartbeat_pong_timeout_sec", 10, note="heartbeat pong timeout"),
        _t("ws_resume_handshake_timeout_s", 5.0, note="resume-frame wait; note the _s suffix, not _sec"),
        _t("ws_initial_metrics_count", 100, note="metrics backfill on connect"),
    )
}

#: The security subset, precomputed for callers that only care about those.
SECURITY_TUNABLES: tuple[str, ...] = tuple(name for name, t in WS_TUNABLES.items() if t.security)


class UnknownTunableError(KeyError):
    """A tunable was requested that is not declared in :data:`WS_TUNABLES`.

    This is a library bug, not a configuration problem: it means a handler asked for
    a name nobody declared, so there is no default to fall back to and no audit entry
    for it. Raised rather than defaulted so it cannot reach production silently.
    """


def _near_match(name: str, settings: Any) -> str | None:
    """Return an attribute of ``settings`` that looks like a misspelling of ``name``.

    Only considers names the settings object actually carries, and never returns an
    exact match (an exact match would not be a miss in the first place).
    """
    try:
        candidates = [a for a in dir(settings) if not a.startswith("_") and a != name]
    except Exception:  # pragma: no cover - exotic settings objects
        return None
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=NEAR_MATCH_CUTOFF)
    return matches[0] if matches else None


def resolve(settings: Any, name: str) -> Any:
    """Resolve tunable ``name`` off ``settings``, falling back to its declared default.

    Args:
        settings: The consuming service's settings object, or ``None``.
        name: A key of :data:`WS_TUNABLES`.

    Returns:
        The configured value, or the declared default when unset.

    Raises:
        UnknownTunableError: ``name`` is not declared.
    """
    try:
        tunable = WS_TUNABLES[name]
    except KeyError as exc:
        raise UnknownTunableError(f"{name!r} is not a declared WebSocket tunable; add it to WS_TUNABLES") from exc

    if settings is None:
        return tunable.default

    sentinel = object()
    value = getattr(settings, name, sentinel)
    if value is not sentinel:
        return value

    suspect = _near_match(name, settings)
    if suspect is not None:
        logger.warning(
            "settings has no %r but does have %r -- probable misspelling; %s is running on the library default %r%s",
            name,
            suspect,
            name,
            tunable.default,
            " (SECURITY CONTROL)" if tunable.security else "",
        )
    else:
        logger.debug("%r not configured; using library default %r", name, tunable.default)
    return tunable.default


@dataclass
class SettingsAudit:
    """Result of :func:`audit`."""

    configured: list[str] = field(default_factory=list)
    defaulted: list[str] = field(default_factory=list)
    defaulted_security: list[str] = field(default_factory=list)
    suspected_typos: list[tuple[str, str]] = field(default_factory=list)

    @property
    def has_findings(self) -> bool:
        """True when something is worth telling an operator about."""
        return bool(self.suspected_typos or self.defaulted_security)

    def render(self) -> str:
        """One-screen human summary; empty string when there is nothing to say."""
        if not self.has_findings:
            return ""
        lines = []
        if self.suspected_typos:
            lines.append("WebSocket settings: probable misspellings (the declared field is NOT being read):")
            lines.extend(f"  {name}  <-- settings has {suspect!r} instead" for name, suspect in self.suspected_typos)
        if self.defaulted_security:
            lines.append("WebSocket settings: security controls running on library defaults:")
            lines.extend(f"  {name} = {WS_TUNABLES[name].default!r}  ({WS_TUNABLES[name].note})" for name in self.defaulted_security)
        return "\n".join(lines)


def audit(settings: Any) -> SettingsAudit:
    """Report which declared tunables a settings object actually supplies.

    Boot-time counterpart to :func:`resolve`. A service can call this once at startup
    and log :meth:`SettingsAudit.render`, which turns "silently defaulted forever"
    into a single visible line -- without the shared package importing anything of
    the service's.
    """
    result = SettingsAudit()
    for name, tunable in WS_TUNABLES.items():
        sentinel = object()
        value = sentinel if settings is None else getattr(settings, name, sentinel)
        if value is not sentinel:
            result.configured.append(name)
            continue
        result.defaulted.append(name)
        if tunable.security:
            result.defaulted_security.append(name)
        suspect = _near_match(name, settings) if settings is not None else None
        if suspect is not None:
            result.suspected_typos.append((name, suspect))
    return result
