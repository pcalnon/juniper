"""Boot-time auth-posture self-check (SEC-F01) — fail closed before a service binds open.

The security companion to the E-8 dependency-floor self-check (:mod:`dependency_floors`):
that stops a service serving on top of a below-floor wheel; this stops a service that is
*meant* to require API-key auth from silently serving **wide open** because no keys were
configured. A service calls :func:`enforce_auth_posture` at startup — before it binds —
passing its resolved API keys and whether auth is required in this deployment. If auth is
required but no real key is configured, the call raises :class:`AuthPostureError` and the
server fails loudly instead of coming up with authentication silently disabled.

This is the failure mode confirmed in the containerized-stack security audit (SEC-F01 /
HO-2): every juniper HTTP service computes ``enabled = len(api_keys) > 0`` and, with an
empty/placeholder secret, disables ``APIKeyAuth`` and serves protected routes
unauthenticated — with no startup error and a ``healthy`` health check. ``prepare_secrets``
maps the ``CHANGE_BEFORE_PRODUCTION_USE`` placeholder to an *empty* file, so a missing or
undecryptable secret bundle silently drops the whole stack into an open posture.

**Posture, not authentication.** This helper does not authenticate anyone; it asserts that
the *intended* posture matches the *configured* one. Three outcomes:

* auth configured (>=1 real key)     -> ``INFO`` (secured), returns;
* no keys + ``require_auth`` False    -> loud ``WARNING`` (running OPEN), returns;
* no keys + ``require_auth`` True     -> ``CRITICAL`` + raise :class:`AuthPostureError`.

Keep ``require_auth`` False for an intentional open dev/demo profile; set it True (and
populate the key secret) for any secured deployment, so an empty secret is a boot failure
rather than open access.

**Dependency-light.** Stdlib only, preserving the dependency-free ``import
juniper_service_core`` guarantee.

**Escape hatch.** ``JUNIPER_SKIP_AUTH_POSTURE_CHECK`` (by default), when truthy, bypasses
the check — logged loudly — so a false positive can never permanently block a legitimate
start.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Collection

_LOG = logging.getLogger("juniper_service_core.auth_posture")

#: Default escape-hatch environment variable; set truthy to bypass the check.
DEFAULT_SKIP_ENV_VAR = "JUNIPER_SKIP_AUTH_POSTURE_CHECK"

_TRUTHY = {"1", "true", "yes", "on"}


class AuthPostureError(RuntimeError):
    """Raised when a service requires API-key auth but no real key is configured."""


def _is_truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in _TRUTHY


def real_keys(api_keys: Collection[str] | None) -> list[str]:
    """Return the non-blank keys among ``api_keys``.

    Same blank-filter rule as ``APIKeyAuth`` (which ignores blank/whitespace entries before
    enabling): an empty collection — or one holding only blank/whitespace strings, as an
    empty secret file resolves to — is not real auth. Pure and side-effect-free: the
    testable core of the check.
    """
    if not api_keys:
        return []
    return [k for k in api_keys if isinstance(k, str) and k.strip()]


def auth_is_configured(api_keys: Collection[str] | None) -> bool:
    """True when at least one real (non-blank) API key is configured."""
    return bool(real_keys(api_keys))


def enforce_auth_posture(
    api_keys: Collection[str] | None,
    *,
    require_auth: bool,
    service_name: str = "service",
    skip_env_var: str = DEFAULT_SKIP_ENV_VAR,
    logger: logging.Logger | None = None,
) -> None:
    """Assert the configured auth posture matches the intended one; fail loud on mismatch.

    Call at service startup, **before binding**. ``api_keys`` is the service's resolved key
    collection (e.g. ``settings.api_keys`` / the input to ``APIKeyAuth``). ``require_auth``
    is whether this deployment expects authentication to be on — source it from the
    service's settings / compose profile (e.g. a ``JUNIPER_<SVC>_REQUIRE_AUTH`` flag,
    defaulting True outside an explicit dev/open profile).

    * A real key is configured -> log ``INFO`` and return.
    * No key and ``require_auth`` False -> log a loud ``WARNING`` (the service is running
      open) and return.
    * No key and ``require_auth`` True -> log ``CRITICAL`` and raise
      :class:`AuthPostureError`, so the server fails to start rather than serving open.

    The ``skip_env_var`` escape hatch (default ``JUNIPER_SKIP_AUTH_POSTURE_CHECK``), when
    truthy (``1``/``true``/``yes``/``on``), logs loudly and returns without enforcing — so a
    false positive can never permanently block a legitimate start.
    """
    log = logger or _LOG
    if skip_env_var and _is_truthy(os.getenv(skip_env_var)):
        log.warning(
            "Auth posture check SKIPPED via %s — %s may be serving with authentication disabled.",
            skip_env_var,
            service_name,
        )
        return

    keys = real_keys(api_keys)
    if keys:
        log.info("Auth posture OK: API-key auth is enabled for %s (%d key(s) configured).", service_name, len(keys))
        return

    if require_auth:
        message = f"Auth posture FAILED — {service_name} requires API-key authentication (require_auth=True) but NO API key is configured, so every protected route would serve UNAUTHENTICATED. Refusing to start (fail-closed). Populate the API-key secret (an empty/placeholder secret file counts as unset), or set require_auth false for an intentional open dev/demo run (or {skip_env_var}=1 to bypass, at your own risk)."
        log.critical(message)
        raise AuthPostureError(message)

    log.warning(
        "%s is running OPEN — no API-key authentication is configured and require_auth is False, so protected routes will serve UNAUTHENTICATED. Set require_auth=True and populate the API-key secret to fail closed in a secured deployment.",
        service_name,
    )
