"""Tests that pin the public API surface.

Consumers import ``from juniper_observability import …``. If a symbol
is removed or renamed, this test fails first — protecting the cross-
service contract.
"""

import juniper_observability

EXPECTED_PUBLIC_SYMBOLS = {
    # Version
    "__version__",
    # Constants
    "HEADER_X_REQUEST_ID",
    "LIVENESS_STALENESS_SECONDS",
    "LIVENESS_TICK_BUDGET_MS",
    "READINESS_HEADER",
    "UNMATCHED_ENDPOINT_LABEL",
    # Health
    "DependencyStatus",
    "ReadinessResponse",
    "probe_dependency",
    # Logging
    "DEFAULT_LOG_FORMAT_PLAIN",
    "JuniperJsonFormatter",
    "LOG_FORMAT_JSON",
    "configure_logging",
    # Middleware
    "METRICS_DEFAULT_TRUSTED_IPS",
    "MetricsAuthMiddleware",
    "PrometheusMiddleware",
    "RequestIdMiddleware",
    "TrustedNetwork",
    "normalize_client_ip",
    "parse_trusted_networks",
    "request_id_var",
    # Prometheus utils
    "get_prometheus_app",
    "set_build_info",
    # Prometheus collector helpers (idempotent registration patterns)
    "lazy_register_or_reuse",
    "register_fresh",
    "register_info_or_update",
    "register_or_reuse",
    # Sentry
    "DEFAULT_SENTRY_TRACES_SAMPLE_RATE",
    "configure_sentry",
}


def test_all_expected_symbols_are_exported():
    """Every consumer-facing symbol must be in ``__all__`` and importable."""
    for symbol in EXPECTED_PUBLIC_SYMBOLS:
        assert hasattr(juniper_observability, symbol), f"missing public symbol: {symbol}"


def test_no_unexpected_public_symbols():
    """``__all__`` must not silently grow without test acknowledgement."""
    declared = set(juniper_observability.__all__)
    extra = declared - EXPECTED_PUBLIC_SYMBOLS
    missing = EXPECTED_PUBLIC_SYMBOLS - declared
    assert not extra, f"juniper_observability.__all__ has undeclared symbols: {extra}"
    assert not missing, f"juniper_observability.__all__ missing expected symbols: {missing}"


def test_middleware_all_is_fully_reexported_by_the_package():
    """APD-OBS-004: two ``__all__`` lists must agree, and nothing checked it.

    ``juniper_observability.middleware.__all__`` and the ``# Middleware`` block of
    ``juniper_observability.__all__`` are maintained by hand in two files. The package
    deliberately re-exports the whole middleware surface, so a name added to the submodule
    and forgotten here breaks ``from juniper_observability import <name>`` for every
    consumer -- silently, because each list is internally consistent.

    Asserted as a subset, not equality: the package list also carries health, logging,
    prometheus and sentry names that must NOT appear in the middleware submodule.
    """
    from juniper_observability import middleware

    submodule = set(middleware.__all__)
    package = set(juniper_observability.__all__)
    orphaned = submodule - package
    assert not orphaned, f"exported by juniper_observability.middleware but not re-exported by the package: {sorted(orphaned)}"


def test_middleware_reexports_are_the_same_objects():
    """A name present in both lists must still resolve to one object.

    The subset check above passes on a name that both files merely *mention*. This pins
    that the package re-export is the submodule's object rather than a shadowing
    redefinition -- the failure a names-only check cannot see.
    """
    from juniper_observability import middleware

    for name in middleware.__all__:
        assert hasattr(juniper_observability, name), f"{name} is in middleware.__all__ but not importable from the package"
        assert getattr(juniper_observability, name) is getattr(middleware, name), f"juniper_observability.{name} is not the object exported by .middleware"


def test_version_is_stable_string():
    """0.4.0 — additive minor: build provenance. ``set_build_info`` gains
    keyword-only ``git_sha`` / ``build_date`` passthrough labels, and
    ``ReadinessResponse`` gains optional ``git_sha`` / ``build_date`` fields
    (juniper-ml ``notes/JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md``). Both are
    backward-compatible — no public-symbol change vs ``0.3.1``. Consumers
    wanting the deployed-revision labels should pin
    ``juniper-observability>=0.4.0``.

    0.3.1 — patch bump that adds a ``logging.warning`` to
    ``MetricsAuthMiddleware`` when ``scope["client"][0]`` is not a
    parseable IP. No API change vs ``0.3.0``; aligns the wrapper with
    the behaviour juniper-cascor added inline in its #313 merge so the
    two implementations can be collapsed into the single shared source.
    0.3.0 was the additive minor bump that promoted
    ``MetricsAuthMiddleware`` (plus ``parse_trusted_networks`` /
    ``normalize_client_ip`` / ``METRICS_DEFAULT_TRUSTED_IPS`` /
    ``TrustedNetwork``) from the inline duplicates that shipped in
    juniper-data #157 and juniper-cascor #313. No breaking changes vs
    ``0.2.0``; consumers should pin ``juniper-observability>=0.3.1``
    going forward to get the warning-log behaviour. 0.2.0 added the
    ``register_or_reuse`` helpers and
    ``juniper_observability.testing.reset_prometheus_registry``; 0.1.1
    was the pre-helpers baseline.
    """
    assert juniper_observability.__version__ == "0.4.0"


def test_constants_match_documented_values():
    """The R1.1/R1.2 contract values must not drift."""
    assert juniper_observability.UNMATCHED_ENDPOINT_LABEL == "_unmatched"
    assert juniper_observability.READINESS_HEADER == "X-Juniper-Readiness"
    assert juniper_observability.LIVENESS_TICK_BUDGET_MS == 250
    assert juniper_observability.LIVENESS_STALENESS_SECONDS == 30.0
    assert juniper_observability.HEADER_X_REQUEST_ID == "X-Request-ID"
