# Quick Start Guide

## Install Juniper Packages with juniper-ml

**Version:** 0.3.11
**Status:** Active
**Last Updated:** 2026-09-04
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Install](#1-install)
- [Verify](#2-verify)
- [Next Steps](#3-next-steps)

---

## Prerequisites

- **Python 3.12+** (`python --version`)

---

## 1. Install

`juniper-ml` is a meta-package with no code of its own. Choose the extra that matches your use case:

```bash
# Client libraries only (juniper-data-client + juniper-cascor-client)
pip install juniper-ml[clients]

# Distributed training worker only (juniper-cascor-worker)
pip install juniper-ml[worker]

# Server packages (juniper-canopy + juniper-cascor + juniper-data)
pip install juniper-ml[servers]

# Shared tooling (juniper-ci-tools + juniper-doc-tools + juniper-observability)
pip install juniper-ml[tools]

# Markdown link validator only (back-compat alias for one entry in [tools])
pip install juniper-ml[doc-tools]

# Everything
pip install juniper-ml[all]
```

> **Note on install size.** `juniper-ml[all]` transitively pulls a multi-GB dependency tree (notably `torch` via `juniper-cascor-worker` and `juniper-cascor`). On a fresh environment this resolves to approximately **5 GB on disk after install** (measured on Python 3.13 + Linux x86_64 against PyPI on 2026-05-21).
> Callers who do not need the worker or server distributions should prefer a narrower extra: `[clients]`, `[tools]`, and `[doc-tools]` each resolve to under 50 MB; `[servers]` is under 200 MB (no torch).

### What Each Extra Installs

| Extra       | Packages                                                                                                                                                                                                     |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clients`   | `juniper-data-client>=0.4.1`, `juniper-cascor-client>=0.5.0`                                                                                                                                                 |
| `worker`    | `juniper-cascor-worker>=0.4.0`                                                                                                                                                                               |
| `servers`   | `juniper-canopy>=0.5.0`, `juniper-cascor>=0.5.0`, `juniper-data>=0.6.0`                                                                                                                                      |
| `tools`     | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.2.0`, `juniper-service-core>=0.2.0,<0.8.0` |
| `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)                                                                                                                     |
| `recurrence`| `juniper-recurrence-model>=0.1.5,<0.3.0`, `juniper-recurrence>=0.2.0,<0.5.0`, `juniper-recurrence-client>=0.2.0,<0.3.0`                                                                                      |
| `all`       | All packages from `clients` + `worker` + `servers` + `tools` + `recurrence`                                                                                                                                  |

### Shared Observability Package

Since `juniper-ml` 0.5.0, `juniper-observability` is also aggregated under the `[tools]` and `[all]` extras, so a `pip install juniper-ml[all]` will install it alongside the rest of the platform. Callers that only want the shared observability primitives without the full meta-package can still install it directly:

```bash
pip install "juniper-observability[all]"
```

See [`../juniper-observability/README.md`](../juniper-observability/README.md) for its public surface and independent release workflow.

---

## 2. Verify

```bash
# Check installed packages
pip list | grep juniper
```

Expected output (with `[all]`):

```bash
juniper-canopy           0.5.x
juniper-cascor           0.5.x
juniper-cascor-client    0.5.x
juniper-cascor-worker    0.4.x
juniper-ci-tools         0.4.x
juniper-config-tools     0.1.x
juniper-data             0.6.x
juniper-data-client      0.4.x
juniper-doc-tools        0.1.x
juniper-ml               0.6.0
juniper-observability    0.2.x
```

```python
# Verify client imports
from juniper_data_client import JuniperDataClient
from juniper_cascor_client import JuniperCascorClient
from juniper_cascor_worker import CandidateTrainingWorker
```

REST `base_url` is normalised at construction on GitHub-main of the three HTTP clients (whitespace, case-insensitive `http(s)://`, host required, trailing `/v1` stripped). A hostless value raises `Juniper*ConfigurationError` rather than failing inside `requests` on the first call. `pip install juniper-ml[clients]` does **not** yet require those tips — see [HTTP Client Base-URL Contract](REFERENCE.md#http-client-base-url-contract).

---

## 3. Next Steps

- [Documentation Overview](DOCUMENTATION_OVERVIEW.md) -- navigation index
- [Reference](REFERENCE.md) -- extras, compatibility, and version reference
- [Host Orchestration Utilities](REFERENCE.md#host-orchestration-utilities) -- run services on-host with `util/juniper_plant_all.bash` and `util/juniper_chop_all.bash`
- [Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety) -- `predict_merge` + `Allow-Docs-Rewrite` trailer parity (#926)
- [Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates) -- G4 pre-commit split, advisory Sequence Safety / Fleet PR Lint, post-merge `main-verify` catch-up
- [Post-Merge Main Verification](REFERENCE.md#post-merge-main-verification) -- G3 / G3.1 catch-up BASE, stable-title failure notify, trailers vs labels, battery path-gate
- [YubiKey GPG Provisioning](REFERENCE.md#yubikey-gpg-provisioning) -- ed448-on-card caveat + pointer to the validated transfer procedure
- [Open-PR Budget Alarm](REFERENCE.md#open-pr-budget-alarm) -- daily report-only open-PR / `cursor/` queue guardrail
- [Ruleset Scope Guard](REFERENCE.md#ruleset-scope-guard) -- `~ALL` re-arms deleted dependabot/Copilot bypass rows; exit 2 is not clean
- [Experiment Stack Utilities](REFERENCE.md#experiment-stack-utilities) -- per-run cascor/recurrence experiments via `util/experiment_stack.bash` + `run_experiment.py` (failed `--up` auto-tears down)
- [Shared-Package CI Workflows](REFERENCE.md#shared-package-ci-workflows) -- the six in-repo `ci-<pkg>.yml` contracts (paths, floors, coverage enforce)
- [Docs Full Check](REFERENCE.md#docs-full-check) -- weekly cross-repo link validation + the `ECOSYSTEM_REPOS` clone-list lockstep
- [Scheduled Security Scan and Lockfile Update](REFERENCE.md#scheduled-security-scan-and-lockfile-update) -- weekly `pip-audit --strict` + the lockfile refresh PR
- [Release-Train Detect Summary and Slack](REFERENCE.md#release-train-detect-summary-and-slack) -- action set vs the ceremonial class, hard-fail banner
- [AGENTS.md Date Check](REFERENCE.md#agentsmd-date-check) -- verifies `**Last Updated**:` was bumped on PRs touching `AGENTS.md`
- [Claude.yml Access Validation](REFERENCE.md#claudeyml-access-validation) -- L2/L3 `ANTHROPIC_API_KEY` safeguards + `DEFAULT_REPOS` fan-out
- [juniper-service-core](REFERENCE.md#juniper-service-core) -- body limit, 429 headers, control-WS sanitizer, `/ws/workers` contracts
- [HTTP Client Base-URL Contract](REFERENCE.md#http-client-base-url-contract) -- shared REST `_normalize_url`, TLS-downgrade pitfall, WS streams still rstrip-only
- [juniper-observability README](../juniper-observability/README.md) -- shared observability primitives
- [juniper-data-client Quick Start](https://github.com/pcalnon/juniper-data-client) -- dataset client usage
- [juniper-cascor-client Quick Start](https://github.com/pcalnon/juniper-cascor-client) -- training client usage
- [juniper-cascor-worker Quick Start](https://github.com/pcalnon/juniper-cascor-worker) -- worker setup

---

**Last Updated:** 2026-09-04
**Version:** 0.3.11
**Status:** Active
