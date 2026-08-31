# juniper-observability

[![PyPI](https://img.shields.io/pypi/v/juniper-observability)](https://pypi.org/project/juniper-observability/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

**Shared observability primitives for the Juniper platform — health models, structured logging,
middleware, and crash-safe Prometheus collector registration.**

`juniper-observability` is the single place every Juniper service gets its cross-cutting observability
wiring, so each service doesn't re-implement it: Pydantic health-response models for the
`/v1/health/ready` endpoint, structured-JSON logging with `request_id` propagation, the Starlette
`RequestIdMiddleware` and `PrometheusMiddleware`, **idempotent `prometheus_client` collector helpers**,
the matching pytest reset fixture, and Sentry initialisation.

The collector helpers are the headline. Registering a `Counter` / `Gauge` / `Histogram` / … twice —
across a module reload or a pytest-fixture reset — normally raises
`Duplicated timeseries in CollectorRegistry`. `register_or_reuse` adopts the existing collector
instead, so registration is safe to repeat.

> **Part of the Juniper platform.** juniper-observability is the shared observability layer of
> [Juniper](https://github.com/pcalnon/juniper-ml) — a multi-package ML research platform built around
> constructive (Cascade-Correlation) and recurrent neural networks. It's a small infrastructure
> library; you don't need the rest of the platform to use it.

## Install

```bash
pip install juniper-observability                 # core
pip install "juniper-observability[prometheus]"   # + Prometheus middleware/utilities
pip install "juniper-observability[sentry]"       # + Sentry init
pip install "juniper-observability[all]"          # everything
```

It is also pulled in by the meta-package's `juniper-ml[tools]` and `juniper-ml[all]` extras.

## Quick start

```python
from prometheus_client import CollectorRegistry, Counter
from juniper_observability import register_or_reuse

registry = CollectorRegistry()
c1 = register_or_reuse(Counter, "demo_total", "demo counter", registry=registry)
c2 = register_or_reuse(Counter, "demo_total", "demo counter", registry=registry)
assert c1 is c2   # the second call adopts the existing collector — no exception
```

For tests that touch collector state, use the canonical reset fixture:

```python
from juniper_observability.testing import reset_prometheus_registry  # pytest fixture
```

## What's in the box

| Surface | What it gives you |
|---|---|
| `register_or_reuse` / `register_fresh` / `register_info_or_update` / `lazy_register_or_reuse` | Idempotent `prometheus_client` collector registration (adopt-existing is the default). |
| `testing.reset_prometheus_registry` | Pytest fixture that resets collector state between tests. |
| `RequestIdMiddleware`, `PrometheusMiddleware` | Starlette middlewares applied across the service fleet. |
| Health-response models | Pydantic models for the `/v1/health/ready` endpoint. |
| Structured-JSON logging | Logging configuration with `request_id` propagation. |
| Sentry init | Initialisation surface with the SEC-10 `before_send` hook always installed. |

**Per-service metrics stay in each repo.** This package exposes only *cross-cutting* infrastructure;
service-specific metric definitions (training-loop counters, dataset-gen histograms, websocket gauges)
live in their owning repo and register via `register_or_reuse` against `prometheus_client.REGISTRY`.

## Consumers

The service repos — [`juniper-data`](https://github.com/pcalnon/juniper-data),
[`juniper-cascor`](https://github.com/pcalnon/juniper-cascor),
[`juniper-canopy`](https://github.com/pcalnon/juniper-canopy) — import the middlewares, health models,
and collector helpers (pin `>=0.2.0`). The client libraries
([`juniper-data-client`](https://github.com/pcalnon/juniper-data-client),
[`juniper-cascor-client`](https://github.com/pcalnon/juniper-cascor-client)) pull it in via their
`[observability]` extra for `X-Request-ID` propagation and Prometheus counters.

## Status

**Live** on PyPI, published independently of the meta-package on `juniper-observability-v*` tags. The
current version is shown by the badge above; see [`CHANGELOG.md`](./CHANGELOG.md). Consumers pin
`juniper-observability>=0.2.0`.

### Compatibility policy — pinning, not deprecation cycles

This package ships **no deprecation machinery**: no `DeprecationWarning`, no
`PendingDeprecationWarning`, no legacy aliases. That is deliberate, not an oversight
(defect-register `APD-ECO-007`).

While pre-1.0, compatibility is managed by **external pinning** — consumers pin a floor
and a ceiling, so each `0.x` is a compatibility boundary and a breaking change is
absorbed by a ceiling raise the consumer performs deliberately. That holds while the
consumer set is a known, enumerable handful of first-party repositories.

**What would change this:** a third-party dependant, or 1.0 — at which point the
consumer set stops being enumerable and a census stops being a sufficient substitute
for a deprecation cycle. When that happens, reuse the implementations this ecosystem
already has rather than writing a third:
`juniper_config_tools.env_with_legacy_alias` for env-var renames, and the
`juniper-data-client` alias pattern (a `DeprecationWarning` with a correct `stacklevel`
and a **dated** removal window) for API renames. Re-derivation is exactly how the
env-var lookup drifted across three services before it was consolidated.

## Design

Part of the [Juniper](https://github.com/pcalnon) ML research platform. Rationale and history:

- [`register_or_reuse` helper design + migration history](../notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md)
- [METRICS-MON R2.1 shared-observability design](../notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md) (archived)

## License

MIT — see [LICENSE](../LICENSE).
