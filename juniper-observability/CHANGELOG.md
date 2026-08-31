# Changelog

All notable changes to the `juniper-observability` package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with [PEP 440](https://peps.python.org/pep-0440/) pre-release identifiers.

## [Unreleased]

### Fixed

- **Inbound `X-Request-ID` is validated before propagation** (defect-register `APD-OBS-001`,
  [ml#1156](https://github.com/pcalnon/juniper-ml/pull/1156)). The header is attacker-controlled and
  its value flows into a process-wide `ContextVar` that any consumer may write to a line-oriented
  sink, and that is echoed back on the response. That was contained only *incidentally*, by machinery
  this package does not own: h11 caps the whole request head at `max_incomplete_event_size` (16384 by
  default, and uvicorn leaves it alone) and rejects CR/LF in header values outright. Both are h11
  defaults, so the guarantee was borrowed rather than held. Ingress validation moves it here: a new
  `MAX_REQUEST_ID_LENGTH` (128 — generous beside a 36-character UUID4 or a 55-character W3C
  `traceparent`, small enough not to bloat a log line) and an **allowlist** pattern
  `[A-Za-z0-9._:-]+`, chosen over a denylist because the set of characters safe in *every* downstream
  sink is far easier to enumerate correctly than the set dangerous in any of them. An invalid inbound
  value is replaced with a freshly generated ID rather than rejected.
- **`register_info_or_update` declares its real return type** (defect-register `APD-OBS-003`,
  [ml#1245](https://github.com/pcalnon/juniper-ml/pull/1245)). It returned `Any`, which silently
  laundered the type for every caller. It now returns `Info`, imported under `TYPE_CHECKING` only —
  `prometheus_client` is an optional extra and must never be imported at runtime here, and
  `from __future__ import annotations` makes the annotation a string, so the import costs nothing
  outside a type checker.
- **`__all__` is pinned against the module's actual public surface** (defect-register `APD-OBS-004`,
  [ml#1245](https://github.com/pcalnon/juniper-ml/pull/1245)). A guard test now fails when the two
  disagree, so an export can no longer be added or removed without the advertised surface following.
- **The `py.typed` marker is actually shipped in the wheel** (defect-register `APD-OBS-002`,
  [ml#1237](https://github.com/pcalnon/juniper-ml/pull/1237)). The package carried the
  `Typing :: Typed` classifier while the marker was not included as package data, so every consumer's
  type checker silently treated this package as untyped. Part of the six-sub-package packaging sweep.

> These four entries are a **backfill**: the changes shipped between 0.4.0 and this release with an
> empty `[Unreleased]` section, which is what the release-train detector reported as
> "CHANGELOG [Unreleased] has no feature/fix/security bullets (under-documented)". All four are
> fixes; none adds package-level public API — `is_valid_request_id` and `MAX_REQUEST_ID_LENGTH` are
> module-level and are not exported from `juniper_observability.__init__`. The bump this documents is
> therefore a **patch**, which is what `detect.py --local-git` proposes for this package.

## [0.4.0] - 2026-06-14

### Added

- **Build provenance.** ``set_build_info(namespace, version, *, git_sha=None,
  build_date=None)`` now accepts keyword-only ``git_sha`` and ``build_date``
  and, when provided, emits them as additional labels on the
  ``<namespace>_build`` Info metric so the deployed source revision is
  visible in Prometheus/Grafana. They are omitted (not blank) when ``None``.
- ``ReadinessResponse`` gains optional ``git_sha`` / ``build_date`` fields
  (default ``None``) so ``/v1/health/ready`` can carry the same provenance.

Both changes are additive and backward-compatible: existing two-argument
``set_build_info`` callers and pre-0.4.0 ``ReadinessResponse`` consumers are
unaffected (no public-symbol change). This is the foundation release for the
ecosystem build-provenance / stale-image-detection effort — see juniper-ml
``notes/JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md``. Consumers wanting the
provenance labels should pin ``juniper-observability>=0.4.0``.

## [0.3.1] - 2026-05-30

### Changed

- **``MetricsAuthMiddleware`` now logs the deny reason when
  ``scope["client"][0]`` is not a parseable IP.** Previously the
  ``except ValueError`` branch was silent (``pass``) — operators saw
  only a 403 with no signal to distinguish "legitimately blocked
  scraper" from "ingress / sidecar is putting a hostname into
  ``scope["client"][0]``". The new behaviour emits a
  ``logging.warning`` on the
  ``juniper_observability.middleware.metrics_auth`` logger with the
  offending ``client_ip`` repr so the misconfiguration is visible at
  the first denied scrape.

  This aligns the shared middleware with the implementation
  juniper-cascor carried inline in its
  [#313](https://github.com/pcalnon/juniper-cascor/pull/313) merge,
  which had been logging the same warning since promotion of the
  inline copy. Consumers migrating from those inline copies to the
  shared wrapper now see identical observability behaviour. The
  deny outcome (403, no fall-through to the wrapped app) is
  unchanged.

  New regression test ``test_malformed_client_address_logs_warning``
  in ``tests/test_metrics_auth_middleware.py`` pins the new log
  record — message must contain ``"unparseable client IP"`` and the
  ``repr`` of the offending value. The pre-existing
  ``test_malformed_client_address_rejects`` continues to pin the
  403.

  Consumers should pin ``juniper-observability>=0.3.1`` if they
  rely on the new deny-reason warning. The migration follow-ups
  (juniper-data + juniper-cascor swap inline copy for shared
  import) move to this floor going forward.

## [0.3.0] - 2026-05-29

### Added

- **``MetricsAuthMiddleware``** — IP-allowlist ASGI wrapper for
  ``/metrics`` mounts. Promoted from the inline duplicates that
  shipped in juniper-data
  [#157](https://github.com/pcalnon/juniper-data/pull/157) and
  juniper-cascor
  [#313](https://github.com/pcalnon/juniper-cascor/pull/313). Two
  consumers maintaining the same shape was the deferred follow-up in
  POC remediation §6 ("Promote ``MetricsAuthMiddleware`` to
  ``juniper-observability``"); this release fires that trigger.

  Public surface added to ``juniper_observability``:

  - ``MetricsAuthMiddleware`` — the ASGI wrapper. Bare-IP and CIDR
    allowlist with IPv6 zone-id strip and IPv4-mapped IPv6 unwrap so
    Docker bridge clients appearing as ``::ffff:172.18.0.5`` match an
    IPv4 ``172.18.0.0/16`` allowlist entry. Returns 403 from the
    middleware (no fallthrough to the wrapped app) when the client IP
    is missing, malformed, or not in any allowlist network. Non-HTTP
    scopes (WebSocket, lifespan) pass through.
  - ``METRICS_DEFAULT_TRUSTED_IPS = ("127.0.0.1", "::1")`` — loopback-
    only default consumed when ``trusted_ips`` is ``None``. Mirrors the
    per-service ``Settings.metrics_trusted_ips`` defaults.
  - ``parse_trusted_networks(raw) -> tuple[TrustedNetwork, ...]`` —
    compiles bare-IP literals and CIDR strings to ``ip_network``
    objects. Fail-loud on unparseable entries — operator typos
    surface as ``ValueError`` at init, not as silent 403s on every
    scrape. Per-service fail-loud Pydantic ``field_validator`` calls
    this same function so the error surfaces at ``Settings()``.
  - ``normalize_client_ip(client_ip) -> IPv4Address | IPv6Address`` —
    strips IPv6 zone-ids and unwraps IPv4-mapped IPv6.
  - ``TrustedNetwork`` — type alias for ``Union[IPv4Network, IPv6Network]``.

  Public-API regression test (``tests/test_public_api.py``) updated
  to pin the seven new symbols + the version bump.

  Consumers should pin ``juniper-observability>=0.3.0`` going forward.
  Migration follow-ups in juniper-data and juniper-cascor (replace
  inline copy with import from this package) are tracked in the
  deploy-side PR queue.

  New regression test ``tests/test_metrics_auth_middleware.py`` (22
  cases) pins: default constant, ``parse_trusted_networks`` host-
  network widening for bare IPv4/IPv6 + mixed + fail-loud,
  ``normalize_client_ip`` zone-strip + ipv4-mapped unwrap + passthrough,
  middleware default-loopback allow/reject, CIDR v4 allow + miss,
  mixed CIDR + literal, CIDR v6, ipv4-mapped IPv6 against IPv4 CIDR
  (the docker-bridge regression), IPv6 zone-id strip, malformed
  client rejects, missing-client rejects, invalid-CIDR raises at
  init, non-HTTP scopes pass through, response passthrough verbatim,
  and a source-level guard that the ``metrics_auth`` module does not
  import starlette (kept ASGI-only so future consumers can strip the
  starlette runtime dep if they only want this surface).

### Changed

- ``PrometheusMiddleware.__init__`` and ``set_build_info`` now use the
  canonical ``register_or_reuse`` / ``register_info_or_update`` helpers
  introduced in ``0.2.0`` instead of inlining the try/except + REGISTRY-
  lookup pattern. Pure internal refactor — production behaviour and the
  collectors' wire format are unchanged. Phase 1 of the migration plan
  in ``notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md``.

## [0.2.0] - 2026-05-05

Minor bump for additive new public API surface. No breaking changes vs `0.1.1`; existing consumers of `PrometheusMiddleware`, `set_build_info`, `configure_logging`, etc. continue to work unchanged. Recommended pin for new consumers: `juniper-observability>=0.2.0`.

### Added

- ``juniper_observability.prometheus_helpers`` — four idempotent
  ``prometheus_client`` collector helpers retiring the ~10 inline
  copies of the same try/except pattern that had accumulated in
  consumer repos through 2026-05-04. Public API:
  - ``register_or_reuse(factory, name, *args, **kwargs)`` —
    adopt-existing on duplicate (the default choice for almost every
    call site; samples preserved, latest call's args ignored).
  - ``register_fresh(factory, name, *args, **kwargs)`` —
    drop-and-recreate on duplicate (samples discarded, latest call's
    args take effect). Use only when test fixtures or migrations
    intentionally want different buckets/labels.
  - ``register_info_or_update(name, description, **info_labels)`` —
    sugar over ``register_or_reuse`` for the ``Info`` collector type.
  - ``lazy_register_or_reuse(factory, name, *args, **kwargs)`` —
    cached ``register_or_reuse`` for the lazy-init sentinel pattern;
    process-wide module-private cache keyed by metric name.
  All four lazy-import ``prometheus_client`` so callers without the
  optional dependency only pay the import cost on the path that
  actually needs the SDK.
- ``juniper_observability.testing`` (new sub-module) —
  ``reset_prometheus_registry`` pytest fixture replacing the file-
  scoped autouse fixtures consumer test suites had been hand-rolling.
  Function-scoped, opt-in; consumers wire it autouse in their own
  ``conftest.py``. Caused the juniper-data ``TestSEC16MetricsAppIntegration``
  failure on 2026-05-04 because the file-scoped variant only saw
  collectors registered during its own tests.

### Notes

- See
  ``notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md``
  in the juniper-ml repo for the full analysis, design rationale,
  trade-off comparison vs cascor's pre-existing ``_register_or_reuse``,
  and the phased migration plan for the 11 production call sites.

## [0.1.1] - 2026-04-29

### Changed

- **First stable promotion** (METRICS-MON R2.1.3 / seed-06). Promoted from pre-release to stable now that the first consumer (juniper-data, [pcalnon/juniper-data#60](https://github.com/pcalnon/juniper-data/pull/60)) has shipped without surfacing a wire-format regression. **No public-API changes** vs `0.1.1a` — same surface, same behavior; only the version string and trove classifier change.
- Trove classifier moved from `Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta` to reflect the 0.1.x stability commitment.
- Consumers should pin `juniper-observability>=0.1.1` going forward. Existing pins of `>=0.1.0a0` / `>=0.1.1a` continue to resolve to the latest published version, which is now `0.1.1`.

### Notes

- The previous alphas (`0.1.0a0`, `0.1.1a`) remain on PyPI for reproducibility of historical builds. Yanking is intentionally avoided; consumers can downgrade in a hotfix scenario by pinning explicitly.

## [0.1.1a] - 2026-04-28

### Changed

- First publishable alpha. Republishes the `0.1.0a*` source tree under a clean PEP 440 alpha version (`0.1.1a`) following pending-publisher reconfiguration on TestPyPI / PyPI. No source changes from `0.1.0a2`; the bump is required to obtain a fresh, never-uploaded version after the earlier publish attempts under `0.1.0a0` / `0.1.0a2` failed at the trusted-publisher handshake.

### Notes

- `juniper-observability` is not yet wired into the `juniper-ml[all]` extras. It will be added once the alpha graduates and downstream services start importing from it as part of the METRICS-MON R2.1 migration.

## [0.1.0a0] - 2026-04-28 (unpublished)

Initial source drop, never released to PyPI / TestPyPI.

### Added

- **Health models** — Pydantic `DependencyStatus` and `ReadinessResponse` for the standard `/v1/health/ready` response shape used by every Juniper server.
- **`probe_dependency`** — synchronous HTTP health-check helper that returns a populated `DependencyStatus`.
- **Structured logging** — `JuniperJsonFormatter` plus the `configure_logging` helper, with `request_id` propagation across log records.
- **Middleware**
  - `RequestIdMiddleware` — assigns / forwards the `X-Request-ID` header and binds it to the logging context.
  - `PrometheusMiddleware` — request-count + latency middleware with bounded label cardinality per the R1.1 cross-service contract (`UNMATCHED_ENDPOINT_LABEL`).
- **Cross-service constants** — `UNMATCHED_ENDPOINT_LABEL`, `READINESS_HEADER`, `LIVENESS_TICK_BUDGET_MS`, `LIVENESS_STALENESS_SECONDS` (pinned from the R1.1 / R1.2 / R1.3 contracts).
- **Prometheus utilities** — `get_prometheus_app` (mountable ASGI app) and `set_build_info` (for setting the `*_build_info` gauge from `pyproject.toml` metadata).
- **Sentry init** — `configure_sentry` with the SEC-10 `before_send` hook always installed.
- **Package extras** — `[prometheus]`, `[sentry]`, `[all]`.
- **Docs** — design + 5-PR migration sequence in `notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md` (parent juniper-ml repo; archived to `notes/legacy/` 2026-05-05).

### Notes

- Per-service metric definitions intentionally stay in their owning repo and use the lazy-init pattern with `prometheus_client` directly. This package only exposes cross-cutting infrastructure.

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/juniper-observability-v0.1.1...HEAD
[0.1.1]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.1.1
[0.1.1a]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.1.1a
