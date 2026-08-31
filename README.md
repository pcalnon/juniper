<!-- markdownlint-disable MD013 MD033 MD041 -->
<!--
  MD013 (line-length): README contains prose paragraphs that intentionally
                       exceed the 512-char ecosystem limit. Disabled file-wide
                       since wrapping mid-sentence harms PyPI rendering.
  MD033 (no-inline-html): The right-aligned logo + spacing rely on HTML.
  MD041 (first-line-heading): The HTML logo is the first line by design.
-->
<div align="right" width="150px" height="150px" align="right" valign="top"> <img src="images/Juniper_Logo_150px.png" alt="Juniper" align="right" valign="top" width="150px" /></div>
<br /> <br /> <br /> <br />

# Juniper: Dynamic Neural Network Research Platform

Juniper is an AI/ML research platform for investigating dynamic neural network architectures and novel learning paradigms.  The project emphasizes ground-up implementations from primary literature, enabling a more transparent exploration of fundamental algorithms.

## Juniper ML

`juniper-ml` is the **public face of the Juniper platform on PyPI**. It is the meta-distribution that aggregates the platform's services (`juniper-canopy`, `juniper-cascor`, `juniper-data`), client libraries (`juniper-data-client`, `juniper-cascor-client`), distributed worker (`juniper-cascor-worker`), and shared tooling (`juniper-ci-tools`, `juniper-doc-tools`, `juniper-observability`) behind a single installation entry point. The package additionally serves as the version-anchor for cross-component compatibility, the home of the platform-level documentation index, and the host repository for independently-tagged sibling packages such as `juniper-observability` and `juniper-doc-tools`. External callers who want to interact with Juniper services from their own Python code should start here.

## Distribution

`juniper-ml` is published on PyPI as **[`juniper-ml`](https://pypi.org/project/juniper-ml/)**. It provides a single installation entry point for the platform's client stack:

```bash
pip install juniper-ml[all]
```

Published components — `juniper-canopy`, `juniper-cascor`, `juniper-data`, `juniper-data-client`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-ci-tools`, `juniper-doc-tools`, and `juniper-observability` — remain installable in isolation for callers that require finer control over their dependency surface.

## Ecosystem Compatibility

This meta-package is part of the [Juniper](https://github.com/pcalnon/juniper-ml) ecosystem.
The pyproject pins matching `juniper-ml` 0.6.0:

| Package                 | Pin               |
|-------------------------|-------------------|
| `juniper-canopy`        | `>=0.5.0`         |
| `juniper-cascor`        | `>=0.5.0`         |
| `juniper-data`          | `>=0.6.0`         |
| `juniper-data-client`   | `>=0.4.1`         |
| `juniper-cascor-client` | `>=0.5.0`         |
| `juniper-cascor-worker` | `>=0.4.0`         |
| `juniper-ci-tools`      | `>=0.1.0`         |
| `juniper-config-tools`  | `>=0.1.0,<0.2.0`  |
| `juniper-doc-tools`     | `>=0.1.0,<0.2.0`  |
| `juniper-observability` | `>=0.2.0`         |

For full-stack Docker deployment and integration tests, see [`juniper-deploy`](https://github.com/pcalnon/juniper-deploy). For the non-Docker host-mode stack, use the [Host Orchestration Utilities](docs/REFERENCE.md#host-orchestration-utilities) runbook in this repository.

## Architecture

`juniper-ml` is a meta-package: it ships no importable code of its own. Its role is to declare, version, and install the libraries through which external callers interact with the platform's services. The diagram below reproduces the platform's dependency graph from the parent ecosystem documentation; `juniper-ml` sits at the bottom-right, aggregating the client side.

```text
juniper-cascor ──uses──> juniper-data-client ──calls──> juniper-data
juniper-cascor ──managed by──> juniper-cascor-worker (distributed training, architectural only — no code import dependency)
juniper-cascor-client ──calls──> juniper-cascor (REST/WebSocket)
juniper-canopy ──uses──> juniper-data-client ──calls──> juniper-data
juniper-canopy ──uses──> juniper-cascor-client ──calls──> juniper-cascor
juniper-deploy ──orchestrates──> juniper-data, juniper-cascor, juniper-canopy (Docker)
juniper-ml ──meta-package──> juniper-canopy, juniper-cascor, juniper-data,
                              juniper-data-client, juniper-cascor-client, juniper-cascor-worker,
                              juniper-ci-tools, juniper-doc-tools, juniper-observability
juniper-ml ──hosts independent package workflows──> juniper-observability, juniper-doc-tools
```

## Related Services

| Component | Relationship | Notes |
|-----------|-------------|-------|
| [juniper-canopy](https://github.com/pcalnon/juniper-canopy) | Aggregated under `[servers]` and `[all]` | `pip install juniper-canopy` |
| [juniper-cascor](https://github.com/pcalnon/juniper-cascor) | Aggregated under `[servers]` and `[all]` | `pip install juniper-cascor` |
| [juniper-data](https://github.com/pcalnon/juniper-data) | Aggregated under `[servers]` and `[all]` | `pip install juniper-data` |
| [juniper-data-client](https://github.com/pcalnon/juniper-data-client) | Aggregated under `[clients]` and `[all]` | `pip install juniper-data-client` |
| [juniper-cascor-client](https://github.com/pcalnon/juniper-cascor-client) | Aggregated under `[clients]` and `[all]` | `pip install juniper-cascor-client` |
| [juniper-cascor-worker](https://github.com/pcalnon/juniper-cascor-worker) | Aggregated under `[worker]` and `[all]` | `pip install juniper-cascor-worker` |
| [juniper-ci-tools](https://github.com/pcalnon/juniper-ml/tree/main/juniper-ci-tools) | Aggregated under `[tools]` and `[all]`; published from this repository | `pip install juniper-ci-tools` |
| [juniper-doc-tools](juniper-doc-tools/README.md) | Aggregated under `[doc-tools]`, `[tools]`, and `[all]`; published from this repository | `pip install juniper-doc-tools` |
| [juniper-observability](juniper-observability/README.md) | Aggregated under `[tools]` and `[all]`; published independently from this repository | `pip install "juniper-observability[all]"` |

### Extras

| Extra        | Packages Included                                                                                |
|--------------|--------------------------------------------------------------------------------------------------|
| `clients`    | `juniper-data-client>=0.4.1`, `juniper-cascor-client>=0.5.0`                                     |
| `worker`     | `juniper-cascor-worker>=0.4.0`                                                                   |
| `servers`    | `juniper-canopy>=0.5.0`, `juniper-cascor>=0.5.0`, `juniper-data>=0.6.0`                          |
| `tools`      | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.2.0`, `juniper-service-core>=0.2.0,<0.8.0` |
| `doc-tools`  | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)         |
| `recurrence` | `juniper-recurrence-model>=0.1.5,<0.3.0`, `juniper-recurrence>=0.2.0,<0.5.0`, `juniper-recurrence-client>=0.2.0,<0.3.0`                                                                                      |
| `all`        | All of the above                                                                                 |

## Active Research Components

The active research components of the Juniper platform are surfaced through the component repositories listed below. Each repository's README documents the algorithms, datasets, protocols, or operational primitives it implements; `juniper-ml` aggregates their client surfaces and does not host research code of its own.

| Component | Research artifact |
|-----------|-------------------|
| [juniper-cascor](https://github.com/pcalnon/juniper-cascor) | Cascade-Correlation reference implementation (Fahlman & Lebiere, 1990), candidate-pool training protocol, multi-network orchestration |
| [juniper-data](https://github.com/pcalnon/juniper-data) | Dataset-generation service, named-version registry, ARC-AGI dataset families |
| [juniper-canopy](https://github.com/pcalnon/juniper-canopy) | Real-time training-dynamics visualisation, network-topology renderer, WebSocket control surface |
| [juniper-cascor-worker](https://github.com/pcalnon/juniper-cascor-worker) | Distributed candidate-unit training over a WebSocket worker protocol |
| [juniper-cascor-client](https://github.com/pcalnon/juniper-cascor-client) | REST + WebSocket training-stream and control-stream client protocols |
| [juniper-observability](juniper-observability/README.md) | Idempotent Prometheus collector helpers (`register_or_reuse` family), structured-JSON logging, Starlette middleware |
| [juniper-doc-tools](juniper-doc-tools/README.md) | `juniper-check-doc-links` CLI for cross-repo and ecosystem-root markdown link validation |

## Quick Start Guide

### Prerequisites

- Python ≥ 3.12

The meta-package itself has no other prerequisites. Component-specific requirements (e.g. a running `juniper-data` or `juniper-cascor` service) are documented in the corresponding component repository.

### Installation

```bash
pip install juniper-ml[all]            # all servers, clients, worker, and tools
pip install juniper-ml[servers]        # juniper-canopy + juniper-cascor + juniper-data
pip install juniper-ml[clients]        # juniper-data-client + juniper-cascor-client
pip install juniper-ml[worker]         # juniper-cascor-worker
pip install juniper-ml[tools]          # juniper-ci-tools + juniper-doc-tools + juniper-observability
pip install juniper-ml[doc-tools]      # juniper-doc-tools only (back-compat alias)
```

### Verification

Confirm the client libraries are importable:

```python
from juniper_data_client import JuniperDataClient
from juniper_cascor_client import JuniperCascorClient
```

Confirm the documentation tooling CLI is on `PATH`:

```bash
juniper-check-doc-links --version
```

### Next Steps

- [`docs/QUICK_START.md`](docs/QUICK_START.md) — installation and verification guide
- [`docs/REFERENCE.md`](docs/REFERENCE.md) — extras, compatibility matrix, environment variables, service ports, and host-mode stack utilities
- [`juniper-deploy`](https://github.com/pcalnon/juniper-deploy) — Docker Compose orchestration for the full-stack platform

## Research Philosophy

The Juniper platform exists to study learning algorithms whose network architecture is not fixed in advance. Its initial anchor is the Cascade-Correlation algorithm of Fahlman and Lebiere (1990), implemented from the primary literature without recourse to higher-level abstractions that elide the algorithm's operational detail. The organising commitment is that algorithm implementations remain inspectable at the level at which they were originally specified: candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper. This permits comparative work — across algorithms, datasets, and hyperparameter regimes — to be conducted on a known and reproducible substrate.

The current platform comprises a Cascade-Correlation training service exposing a REST and WebSocket interface, a dataset-generation service with a named-version registry that includes the ARC-AGI families, a real-time monitoring dashboard for inspecting training dynamics as they occur, and a distributed worker that parallelises candidate-unit training across hosts. Near-term work extends the architectural-growth catalogue beyond Cascade-Correlation, introduces multi-network orchestration for comparative experiments at the level of network populations rather than individual runs, and tightens the dataset–training–monitoring loop into a reproducible research workbench. The longer-term direction is the systematic empirical study of constructive and architecture-growing learning algorithms, with first-class infrastructure for the ablation, comparison, and replication that such a study requires.

Within this programme, `juniper-ml` is the integration surface: a single installation entry point that aggregates the client libraries needed to interact with the platform from external Python code, and a version-anchor that makes the compatibility of components legible at a glance.

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/DOCUMENTATION_OVERVIEW.md`](docs/DOCUMENTATION_OVERVIEW.md) | Navigation index for all `juniper-ml` documentation |
| [`docs/QUICK_START.md`](docs/QUICK_START.md) | Installation and verification guide |
| [`docs/REFERENCE.md`](docs/REFERENCE.md) | Extras, compatibility matrix, environment variables, service ports, and host-mode stack utilities |
| [`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`](docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md) | Quick-reference card for development tasks |
| [`notes/JUNIPER_2026-05-19_JUNIPER-ECOSYSTEM_README-NORMALIZATION-PLAN.md`](notes/JUNIPER_2026-05-19_JUNIPER-ECOSYSTEM_README-NORMALIZATION-PLAN.md) | Ecosystem-wide README normalization plan (this README is its reference implementation) |
| [`notes/JUNIPER_2026-05-19_JUNIPER-ECOSYSTEM_RESEARCH-PHILOSOPHY-CANONICAL-DRAFT.md`](notes/JUNIPER_2026-05-19_JUNIPER-ECOSYSTEM_RESEARCH-PHILOSOPHY-CANONICAL-DRAFT.md) | Source-of-truth for the Research Philosophy text inlined above |

## License

MIT License — Copyright (c) 2024-2026 Paul Calnon

## Support

You can support continued development of the Juniper project on [`Patreon`](https://www.patreon.com/cw/JuniperML)

- The Juniper Go-Live [`announcement`](https://www.patreon.com/JuniperML/posts/juniperml-is-164484818)

Or just buy me a [`coffee`](https://buymeacoffee.com/overtoad)!

---
