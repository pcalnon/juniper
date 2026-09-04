# CLI-Launched Test, Validation & Experimentation Program — juniper-cascor + juniper-recurrence

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml (cross-repo: juniper-cascor, juniper-recurrence, juniper-data, juniper-data-client, juniper-deploy)
**Author**: Paul Calnon
**Document Type**: Design + Implementation Plan (design of record)
**Status**: Proposed (draft for owner review)
**Last Updated**: 2026-07-29
**Scope repos**: `juniper-ml` (tooling home), `juniper-cascor`, `juniper-recurrence`, `juniper-data`, `juniper-data-client`, `juniper-deploy`

Operator surface for the shipped suite driver (`util/experiments/run_suite.py`, Wave 7.1 / 7.5): [`docs/REFERENCE.md` § Suite driver](../docs/REFERENCE.md#suite-driver).

---

## 1. Purpose & Scope

### 1.1 Goal

Establish a repeatable, reproducible, concurrency-safe program for **testing, validating, and experimenting with the `juniper-cascor` and `juniper-recurrence` applications launched from the command line as on-host services** — with metrics observable in Grafana, plots and statistics emitted at run completion, and experimental parameters fully specifiable in YAML.

### 1.2 In scope

1. Fully specified on-host CLI launch recipes for juniper-data, cascor (service + direct CLI), and recurrence (service + headless train CLI).
2. Convenience launcher + run-driver tooling in `juniper-ml` (`util/`).
3. A YAML experiment-config layer for cascor and recurrence, layered **over** (not replacing) the existing constants files and env-var settings.
4. Metrics reaching the existing dockerized Prometheus + Grafana for host-run processes.
5. End-of-run plots (datasets, cascor decision boundaries, training curves, inference results) plus a numeric results/statistics summary.
6. Concurrency and data-loss safety for multiple simultaneous sessions.
7. Enablement of every compatible dataset per app, with explicit work items for the stubbed / unregistered / partially-hooked cases.
8. Design *beginnings* for (a) performance testing / benchmarking / optimization and (b) multi-run experiment automation.

### 1.3 Non-goals (explicit)

| Non-goal                                  | Reason                                                                                                                                                                                                                                     |
|-------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **`juniper-canopy` is NOT used, at all**  | The observation surface is **Grafana** plus the driver's own artifacts. Canopy is not launched, configured, or depended upon. No canopy port is allocated; no `JUNIPER_CANOPY_*` / `CANOPY_*` variable appears in any launch recipe below. |
| Containers for cascor / recurrence / data | This program is on-host CLI only. The **only** container involvement is the pre-existing Prometheus + Grafana pair (§7), which stays dockerized.                                                                                           |
| Distributed cascor workers                | `juniper-cascor-worker` is out of scope; cascor's scheduler is local-first (`juniper-cascor/src/parallelism/task_distributor.py:24`), so candidate training runs in-process. Worker-mode experiments are a later phase.                    |
| Model/algorithm changes                   | No changes to cascade-correlation or LMU numerics. This is harness, config, observability, and reporting work.                                                                                                                             |
| Replacing the existing constants layer    | The YAML layer is strictly additive: missing YAML keys fall back to the existing constants/settings defaults (§5).                                                                                                                         |
| CI-gating the experiment runs             | Experiment runs are operator-invoked. CI additions are limited to unit/lint gates for the new tooling (§10.6).                                                                                                                             |

### 1.4 Genesis

Three converging pressures:

1. **Ad-hoc experimentation.** cascor's direct CLI trains exactly one problem — `SpiralProblem` (`juniper-cascor/src/main.py:335`) — with hyperparameters baked into `src/cascor_constants/`. Recurrence's `bench/` harness hardcodes its sweep (`juniper-recurrence/bench/run_benchmark.py:30-33`: `_HEADLINE_D = 16`, `_D_GRID = (8, 16, 32)`, `_N_FOLDS = 5`, `_EMBARGO = 2`). Neither can be re-parameterised without editing source.
2. **No host→Grafana metrics path.** Prometheus scrapes five *container* targets only (`juniper-deploy/prometheus/prometheus.yml:61-126`); nothing reaches a host-run process. Recurrence additionally has **zero** Grafana dashboards.
3. **No concurrency policy.** The isolated-stack helper proved the port-isolation pattern (`juniper-ml/util/isolated_stack.bash:58-60`), but there is no allocation policy for N simultaneous experiment sessions, and several fixed paths (cascor `src/snapshots/`, recurrence `bench/results/`) are shared per checkout.

---

## 2. Grounding & Provenance

### 2.1 Method

Five read-only reconnaissance passes over the live sibling checkouts (cascor; recurrence; data + data-client; deploy/observability; juniper-ml tooling + conventions) produced digests. The author then **spot-verified 30+ load-bearing citations directly against the live repos** — entry points, port and boolean defaults, the generator registry, metrics gating, plot APIs, snapshot dirs, request schemas, JR-IDs.

Corrections found during spot-checking are recorded in §2.3; the live repo wins in every case. The digests were session scratch artifacts; **the `repo/path:line` citations in this document are the durable ground truth**. This document is written to be adversarially validated: every current-state claim carries a citation, every non-existent artifact is marked **PROPOSED**, and every gap in knowledge is an `OPEN QUESTION`.

### 2.2 Repository state at authoring time

| Repo                         | HEAD      | Branch                                            | Notes                                                               |
|------------------------------|-----------|---------------------------------------------------|---------------------------------------------------------------------|
| `juniper-cascor`             | `927e26b` | `main`                                            | app version `0.6.0` (`juniper_cascor/__init__.py:3`)                |
| `juniper-recurrence`         | `f23f3ba` | `main`                                            | monorepo: app `0.2.0`, model `0.1.5`, client `0.2.0`, plus `bench/` |
| `juniper-data`               | `b4334e2` | `main`                                            | 16 registered generators                                            |
| `juniper-data-client`        | `bf08ef6` | `main`                                            |                                                                     |
| `juniper-deploy`             | `8657330` | `main`                                            | sole home of Prometheus config + Grafana dashboards                 |
| `juniper-ml` (this worktree) | `4927c78` | `docs/cascor-recurrence-cli-experimentation-plan` | hosts `juniper-observability/` `0.4.0`, `juniper-service-core/`     |

#### 2.2a Provenance re-pin — recurrence (F-7, closed 2026-08-16)

The table above is the **authoring-time** snapshot and is deliberately left as written; a
provenance record that gets silently overwritten is not provenance. [P0 preflight](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md)
finding **F-7** recorded that `juniper_recurrence` had already drifted past that snapshot
(live `0.3.0` against the `0.2.0` recorded above) and deferred the re-pin to *"when Wave 3
touches the recurrence repo"*. Wave 3 has shipped, so the re-pin is recorded here:

| Package / repo                     | At authoring (§2.2) | Re-pinned 2026-08-16 |
|------------------------------------|---------------------|----------------------|
| `juniper-recurrence` HEAD          | `f23f3ba`           | `59be8de` (`main`)   |
| app `juniper_recurrence`           | `0.2.0`             | **`0.4.0`**          |
| model `juniper_recurrence_model`   | `0.1.5`             | **`0.2.0`**          |
| client `juniper_recurrence_client` | `0.2.0`             | `0.2.0` (unchanged)  |

Each version is read from that package's `_version.py`; all three declare
`[tool.setuptools.dynamic] version.attr`, so the dunder **is** the version. F-7's companion
observation — that the dist-info floor table lagged at `0.2.0` through editable-metadata
staleness — is the STALE-metadata class now covered by
`util/editable_install_drift_check.py --strict-version`.

Note the drift is two minors on the app and one on the model: any §3 or §5.5 claim that
depends on a *recurrence-side* API shape should be re-verified against `59be8de` rather
than assumed from the authoring snapshot.

### 2.3 Live-host environment facts (verified 2026-07-29) and corrections to the recon digests

| Fact | Evidence | Correction? |
| --- | --- | --- |
| Live conda envs are `JuniperCascor1`, `JuniperCanopy1`, `JuniperData`. The historic `JuniperCascor` / `JuniperCanopy` are now `JuniperCascor-DEPRECATED` / `JuniperCanopy-DEPRECATED`. | `ls /opt/miniforge3/envs/` | **Yes** — `juniper-cascor/scripts/juniper-cascor.service:30` still has `ExecStart=/opt/miniforge3/envs/JuniperCascor/bin/python server.py`, a path that no longer exists on this host. Recorded as gap **G-13**. |
| `JuniperCascor1`: Python 3.13.13, torch 2.11.0+cu130, matplotlib 3.10.9, PyYAML 6.0.3, numpy 2.4.4, `prometheus_client`, `requests`, `httpx`, `h5py` 3.16.0. No HF `datasets`, no `yfinance`/`pandas`. | env probe | — |
| `JuniperData`: Python 3.14.2, uvicorn 0.40.0, `juniper_data` 0.6.0 **editable** → canonical repo, matplotlib 3.10.8, PyYAML 6.0.3, **`yfinance` 1.4.1 + `pandas` 3.0.3 present**. No HF `datasets`. | env probe; `*.dist-info/direct_url.json` | **Yes** — the digest read `isolated_stack.bash:13-14` ("base install has no server") as meaning the JuniperData env cannot serve. It can: `conda activate JuniperData && python -m juniper_data` works today. |
| `juniper_recurrence` 0.2.0 is **editable-installed in `JuniperCascor1`**, console script at `/opt/miniforge3/envs/JuniperCascor1/bin/juniper-recurrence`. | `direct_url.json`; `ls` | **Yes** — `juniper-recurrence/AGENTS.md:96` states "No dedicated on-host conda env carries the app's deps". Literally true (there is no *dedicated* env) but `JuniperCascor1` does carry them. |
| `mnist` is the **only** registry generator reporting `available=False` in the JuniperData env; all 15 others report `True`, including `equities` and `equities_seq`. | live evaluation of `generator_available()` over `GENERATOR_REGISTRY` in the JuniperData env | **Refines** the digest's "equities gated `[equities]`" — the gate exists (`juniper-data/juniper_data/generators/equities/generator.py:131`) and is **satisfied** on this host. |
| `pydantic-settings` `2.12.0` (JuniperData) / `2.14.0` (JuniperCascor1) with `YamlConfigSettingsSource` importable. | env probe | — (the `PydanticBaseSettingsSource` hook this supplies is what makes §5.2's projection source implementable with no new dependency in cascor) |
| `juniper-data-client`'s parity test asserts **both** directions — `test_every_server_generator_has_client_constant` (`tests/test_generator_parity.py:72-76`) — but against a **hand-maintained, stale** `EXPECTED_SERVER_GENERATORS` frozenset of 9 names (`:27-39`) that omits all 7 newer generators (6 sequence/regression + `equities`). | file read | **Yes** — the digest said the test "asserts only one direction". The real defect is a stale duplicated mirror, so the reverse assertion passes vacuously. |
| `JUNIPER_WORKER_HEALTH_PORT` defaults to **8210** (`juniper-ml/util/juniper_plant_all.bash:183`), the same port juniper-recurrence binds by default (`juniper_recurrence/settings.py:47`; README `juniper-recurrence serve --host 127.0.0.1 --port 8210`, `juniper-recurrence/README.md:37`). | file reads | **New hazard**, not in any digest. Recorded as **G-12** / hazard H-2. |
| `generate_dataset_id` is deterministic **only when `params['seed']` is present and non-`None`**; otherwise a UUID nonce is mixed in. | `juniper-data/juniper_data/core/dataset_id.py:23-34` | **New**, load-bearing for reproducibility (§13.4). |

Line-number nits corrected against the live repos and used throughout: cascor `main()` is at `src/server.py:15-25`; `Settings.host` / `.port` at `src/api/settings.py:132-133`; `metrics_trusted_ips` at `:383`; `sys.exit(3)` at `src/main.py:319` and `sys.exit(4)` at `:331`; `--profile-output` at `:439`; `if __name__ == "__main__"` at `:448-449`.

### 2.4 Independent validation record

Three independent read-only validator agents ran on 2026-07-29 against the live repos, with no access to the drafting agent's sources:

1. **Adversarial citation verification** — ~330 `repo/path:line` claims re-probed: 327 confirmed, 0 refuted, 0 hallucinated artifacts, 3 line-number drifts (folded in: the recurrence coverage `fail_under` cite, the `prometheus.demo.yml` environment-label cite, the `generate_plots` flag cite).
2. **Mechanical / design verification** — 61 mechanism claims examined: 51 sound; 1 blocker (a `host-gateway`-addressed scrape can never reach a loopback-bound service — §7 redesigned to the launcher-owned relay) + 4 majors (the §5.2 YAML projection source, cascor bind authority via the uvicorn CLI, `eval_metrics_enabled` as env not Settings, the candidate-correlation plot source) + 5 minors — all folded in.
3. **Requirements-coverage & consistency audit** — R-coverage graded; 5 majors + 11 minors folded in (including the new W-11 / W-12 work items and the P0.10 → step 0.2b sequencing fix).

Corrections were applied in the same change that added this record; the pre-validation draft is preserved in git history.

---

## 3. Current-State Survey

### 3.1 juniper-data (the dataset service both apps depend on)

- **No console script.** Two supported launches: `python -m juniper_data [--host --port --storage-path --log-level --reload]` → `uvicorn.run("juniper_data.api.app:get_app", factory=True, ...)` (`juniper-data/juniper_data/__main__.py:66-73`, argparse `:17-50`), or `uvicorn --factory juniper_data.api.app:get_app --reload` binding `127.0.0.1:8100` (`juniper-data/README.md:64`).
- **Defaults**: host `127.0.0.1` (`juniper_data/api/settings.py:126`, const `:35`), port `8100` (`:127`, const `:37`), env prefix `JUNIPER_DATA_` (`:111`), `storage_path` (`:119`).
- **Auth**: `X-API-Key`; disabled entirely when `api_keys` is empty (`juniper_data/api/security.py:55`; field `settings.py:133`, `require_auth` `:141`).
- **Registry**: a single module dict `GENERATOR_REGISTRY` (`juniper_data/api/routes/generators.py:44`) with 16 entries at `:54-175`. Availability is probed through the optional `is_available()` hook by `generator_available()` (`:178-200`); only `mnist`, `equities`, `equities_seq` declare it (`generators/{mnist,equities,equities_seq}/generator.py:47,131,67`).
- **Key endpoints**: `GET /v1/generators` (`routes/generators.py:203`), `GET /v1/generators/{name}/schema` (`:225`), `POST /v1/datasets` → 201 (`routes/datasets.py:71-73`), `GET /v1/datasets/{id}/artifact` (`:676`), `GET /v1/health{,/live,/ready}` (`routes/health.py:117,146,186`).
- **Error mapping**: unknown generator → 400 (`routes/datasets.py:93-97`); missing optional extra → **501** with the install hint (`:165-168`).
- **Determinism**: `dataset_id = generate_dataset_id(generator, version, params)` (`routes/datasets.py:114-118`; impl `core/dataset_id.py:23`) — content-addressed, deterministic **iff `params['seed']` is set**.
- **Contract**: 2-D `X_train/y_train/X_test/y_test/X_full/y_full` float32 with one-hot `y` (`docs/api/JUNIPER_DATA_API.md:867-893`). The 3-D sequence variant dispatches on `X.ndim` (`juniper_data/core/meta.py:119-124`) with `dt_{split}` `(W,L)` and the `dt[:,0] == 0` convention (`generators/_sequence.py:120-121`).
- **Client-side validation**: `validate_npz_contract()` (`juniper-data-client/juniper_data_client/contract.py:41`) returns `"tabular"` or `"sequence"`.
- **Client**: `JuniperDataClient` (`juniper-data-client/juniper_data_client/client.py:125`); `create_dataset(generator, params, persist=True, name, description, created_by, parent_dataset_id, tags, ttl_seconds)` (`:412-423`), `download_artifact_npz` (`:547`), `wait_for_ready` (`:347-371`). **No client-side disk cache** — every fetch is an in-memory HTTP GET, so there is no cache-file race surface.

### 3.2 juniper-cascor

- **No `[project.scripts]`, no `python -m` service form** (`juniper-cascor/pyproject.toml`); `juniper_cascor/__init__.py:3` is metadata-only.
- **Service entry**: `main()` at `src/server.py:15-25` (parses **no CLI flags**) → `uvicorn.run(app, host=settings.host, port=settings.port, log_level=...)`. Canonical launches per `AGENTS.md:25-27`: `cd src && python server.py` and `uvicorn api.app:create_app --factory --host 0.0.0.0 --port 8200`. Factory: `create_app(settings: Settings | None = None) -> FastAPI` (`src/api/app.py:590`). Note `src/server.py:6`'s docstring says `uvicorn api.app:app` — **stale**, there is no module-level `app`.
- **Direct CLI**: `cd src && python main.py [--profile|--profile-memory] [--profile-output DIR] [--profile-top-n N]` (`src/main.py:435-441`, dispatch `:448-449`). Hard preconditions: `JUNIPER_DATA_URL` unset → `sys.exit(3)` (`:316-319`); juniper-data `/v1/health` unreachable → `sys.exit(4)` (`:321-331`). Trains `SpiralProblem` (`:335`).
- **Direct-CLI side effects**: sets `OMP/MKL/OPENBLAS_NUM_THREADS=2` via `setdefault` before BLAS import (`src/main.py:48-50`) and calls `load_dotenv()` (`:172`).
- **Config**: `Settings(BaseSettings)` at `src/api/settings.py:117`, `env_prefix="JUNIPER_CASCOR_"` + `env_file=".env"` (`:124-129`), `@lru_cache get_settings()` (`:506-507`). Constants live in `src/cascor_constants/` (`constants.py` 1245 lines, plus `constants_problem/`, `constants_model/`, `constants_candidates/`, `constants_activation/`, `constants_logging/`, `constants_hdf5/`, `constants_api/`).
- **No app/experiment config-file loader**: `conf/logging_config.yaml` is the only runtime-loaded YAML (`src/log_config/logger/logger.py:611`); `conf/*.conf` are sourced bash.
- **Verified defaults**: host `127.0.0.1` / port `8200` (`settings.py:132-133`); `metrics_enabled` **False** (`:373`, const `:67-68`); `metrics_trusted_ips = ["127.0.0.1", "::1"]` (`:383`); `require_auth` False (`:168`); `auto_start` **False** (`:428`, const + rationale `:70-78`); `auto_dataset = "spiral"` (`:433`); `auto_start_data_service` / `_canopy` both False (`:429`, `:431`).
- **Upstream URL**: `juniper_data_url` is `None` by default (`settings.py:422`) with fallback `http://localhost:8100` (`src/cascor_constants/constants_api/constants_api_defaults.py:114`).
- **Training routes** (router prefix `src/api/routes/training.py:20`, all under `/v1`): `POST /start` (`:30`), `/stop` (`:102`), `/pause` (`:110`), `/resume` (`:122`), `/reset` (`:134`), `GET /status` (`:179`), `GET|PATCH /params` (`:194`,`:203`), `POST|DELETE /dataset` (`:237`,`:249`), `POST|DELETE /dataset/live` (`:274`,`:301`).
- **Read routes**: `GET /v1/metrics` (`routes/metrics.py:17`), `/history?count=N` (`:26`), `/transport` (`:36`); `GET /v1/decision-boundary?resolution=N` (`routes/decision_boundary.py:20`); `GET /v1/network{,/topology,/stats}` (`routes/network.py:34,55,67`).
- **Start-request schema**: `TrainingStartRequest` (`src/api/models/training.py:147`) carries `epochs` (`:153`), `dataset: DatasetSource` (`:154`), `inline_data` (`:155`), `params: TrainingParams` (`:156`), `start_fresh` (`:167`).
- **`TrainingParams`** (`src/api/models/training.py:32`) is `extra="forbid"` (`:44`) with range-checked `max_epochs`, `max_iterations`, `early_stopping`, `learning_rate`, `candidate_learning_rate`, `correlation_threshold`, `candidate_pool_size`, `max_hidden_units`, `patience`, `convergence_threshold`, `candidate_convergence_threshold`, `candidate_patience`, `candidate_epochs` (`:51-72`).
- **`StageDatasetRequest`** (`src/api/models/training.py:180`) has `dataset_type: Literal["spirals","xor","mnist","circles","moons","equities"]` (`:188`), typed `n_samples`/`noise`/`rotations`/`n_spirals` (`:189-192`), plus a generic `params` passthrough (`:200`).
- **Staged dataset path**: builds a `JuniperDataClient`, then `create_dataset(..., persist=True)` + `download_artifact_npz` (`src/api/lifecycle/manager.py:3356-3362`), translating canopy-dialect names via `_STAGED_GENERATOR_ALIASES = {"spirals": "spiral", "moons": "moon"}` (`:3251`) and per-generator param remapping (`:3254-3300`).
- **In-process fallback**: `POST /v1/training/start` with `dataset.generator == "spiral"` generates locally and never calls juniper-data (`routes/training.py:75`, generator `:328-360`); **any other `generator` value is silently ignored** — the dataset field is dropped with no error.
- **Completion detection**: FSM `TrainingStatus` ∈ `STOPPED/STARTED/PAUSED/COMPLETED/FAILED/RESUME_READY/INVESTIGATING/REPLAYING` (`src/api/lifecycle/state_machine.py:24-52`); poll `GET /v1/training/status`, or the `/ws/training` stream (`src/api/app.py:664`).
- **Outputs**: service snapshots to a **fixed** `<repo>/src/snapshots/` (`src/api/lifecycle/manager.py:4300-4304`, no env override); direct-CLI snapshots to `<repo>/src/cascor_snapshots/` (`src/cascor_constants/constants_hdf5/constants_hdf5.py:45-46`); logs to `<repo>/logs/juniper_cascor.log` (`src/cascor_constants/constants.py:418,460-461`); profiles to `./profiles` relative to CWD (`src/main.py:439`).
- **Plotting EXISTS**: `CascadeCorrelationPlotter` (`src/cascor_plotter/cascor_plotter.py:50`) with `plot_dataset` (`:76`), `plot_decision_boundary` (`:128`), `plot_training_history` (`:197`); matplotlib at `:39`. Wired into the direct CLI through `SpiralProblem`'s `generate_plots` flag (`src/spiral_problem/spiral_problem.py:134,349`).
- **Prometheus**: `/metrics` is mounted **only** when `settings.metrics_enabled` (`src/api/app.py:671-675`), wrapped in `MetricsAuthMiddleware`. Domain families via `register_or_reuse` (`src/api/observability.py:194`, 23 call sites): `juniper_cascor_training_sessions_{active,completed_total}`, `_training_epochs_total{phase}`, `_training_loss{phase,loss_type}`, `_training_accuracy_ratio{phase}`, `_hidden_units_total`, `_candidate_correlation`, `_training_step_duration_seconds` (`:219-290`).
- **Scalar eval metrics** (F1/precision/recall/ROC-AUC) on `/v1/metrics{,/history}` gate on `JUNIPER_CASCOR_EVAL_METRICS_ENABLED`, default true (`src/api/lifecycle/manager.py:32-39`).
- **Performance suite**: `src/tests/performance/` — `test_baselines.py`, `test_micro_{forward_pass,candidate,correlation,output_training,autograd}.py`, `test_concurrency_scaling.py`, `test_endtoend_profiling.py`, `test_shared_memory.py`, plus `baselines/baseline_20260526.json`. Double-gated on `--run-performance` **or** `CASCOR_BENCHMARK_MODE=1` (`src/tests/conftest.py:207`, gate `:260-266`); harness flag `-p|--performance` (`src/tests/run_tests.bash:156`).

### 3.3 juniper-recurrence

- **Console script**: `juniper-recurrence = "juniper_recurrence.main:main"` (`juniper-recurrence/juniper-recurrence/pyproject.toml:110-111`), subparsers `{serve,train}` (`juniper_recurrence/main.py:41`).
- **Serve**: `juniper-recurrence serve [--host H] [--port P]` (`main.py:43-45`) → `uvicorn.run("juniper_recurrence.app:app", host=host, port=port)` (`:80`); module-level `app = build_app()` (`juniper_recurrence/app.py:152`) so `uvicorn juniper_recurrence.app:app` works too. Defaults `0.0.0.0:8210` (`settings.py:46-47`); README local recipe `juniper-recurrence serve --host 127.0.0.1 --port 8210` (`README.md:37`).
- **Headless train**: `juniper-recurrence train (--dataset ID | --name N | --generator G) [--split train] [--d 16] [--theta θ] [--ridge x|gcv] [--readout linear|rff|mlp] [--rff-features N] [--rff-gamma γ|median] [--mlp-*] [--out model.npz]` (`main.py:47-63`); no ref → exit 2 (`:92-94`); persists via `LMUSerializer().save` (`:134-136`).
- **Config**: `Settings(SettingsBase)` with `env_prefix="JUNIPER_RECURRENCE_"`, `extra="ignore"`, and **deliberately no `env_file`** (`settings.py:38`). **No YAML/TOML loader anywhere** in the monorepo.
- **Verified defaults**: `host "0.0.0.0"` (`settings.py:46`), `port 8210` (`:47`), `log_format "text"` (`:54`), `api_keys None` (`:57`), `require_auth False` (`:64`), `rate_limit_enabled True` / `60` rpm (`:65-66`), `juniper_data_url "http://localhost:8100"` with `JUNIPER_DATA_URL` alias (`:69-72`), `default_d 16` (`:76`), `default_theta None` (`:77`), `default_ridge 0.0` (`:78`), `metrics_enabled` **True** (`:81`), `metrics_trusted_ips` loopback (`:85`).
- **Train/predict API**: `POST /v1/train` (`routers/training.py:37`) is **synchronous inline**; a second concurrent call → 409 via `train_lock` (`:44-46`); `readout="mlp"` without torch → 503 (`:86`). `GET /v1/training/status` (`:108`). `POST /v1/predict` (`routers/predict.py:29`).
- **Cross-validation API**: `POST /v1/crossval` (`routers/crossval.py:53`) always over the `full` split (`:72`) with its own `crossval_lock` (`:60-62`); `GET /v1/crossval/status` (`:136`). `GET /v1/model` and `GET /v1/dataset` 409 until trained.
- **Health** (from service-core): `GET /v1/health` → `{"status":"ok"}`, `/v1/health/ready` → `{"status":"ready"}` (`juniper-ml/juniper-service-core/juniper_service_core/health.py:31-39`).
- **Schemas**: `DatasetRef` (`schemas.py:72`) precedence `dataset_id → name → generator+params`, `split` default `"train"`; `TrainRequest` (`:106`) `{dataset, d, theta, ridge, readout, rff_*, mlp_*}`; `TrainResponse` (`:145`) `{final_metrics, n_epochs, stopped_reason}`; `CrossValRequest` (`:206`) `{dataset, n_folds>=2, scheme expanding|rolling, embargo, min_train, d, theta, ridge, readout, rff_*, mlp_*}`.
- **Bench harness**: `python -m bench.run_benchmark` from the repo root → `bench/results/<dataset>.json` + `REPORT.md` (`bench/run_benchmark.py:29`, writer `:341,347`). Registry `DATASETS` (`bench/datasets.py:244-262`); `PRIMARY_DATASETS = ("irregular_sine","multi_sine","mackey_glass")` (`:236`).
- **Committed bench results**: `equities_seq`, `irregular_sine{,_noise0.10,_noise0.25}`, `mackey_glass`, `multi_sine{,_noise0.10,_noise0.25}` + `REPORT.md` — **no `delay_product.json`**.
- **Metrics**: `/metrics` is mounted only when `metrics_enabled` **and** `juniper-observability` is importable (`app.py:107-132`, ImportError warning `:117`). Collectors via `register_or_reuse` (`metrics.py:29-36`): `juniper_recurrence_train_runs_total`, `_predict_requests_total`, `_crossval_runs_total`, `_train_last_metric{metric}`, `_train_last_duration_seconds`, `_crossval_last_metric{metric}`, `_crossval_last_duration_seconds`; recorders at `:50-70`; no-ops without the extra (`:40-41`).
- **Plotting: NONE.** Zero `matplotlib`/`pyplot` references anywhere in the monorepo. Analysis output is the markdown bands report (`bench/run_benchmark.py:134-257` `evaluate_bands`, renderer `:260-324`).
- **Persistence**: the server keeps the model **in memory only** (`juniper_recurrence/state.py` module docstring — "persistence and scale-out are deferred to WS-8"); the CLI `--out` `.npz` is the only artifact.
- **Startup quirk** (verbatim, `juniper-recurrence/Dockerfile:88-91`): "start-period=40s: the app imports a heavy pure-Python stack (service-core, model-core, recurrence-model, data-client, numpy, fastapi) — ~10-15s — before uvicorn binds". Any health gate must tolerate this.
- **Tests**: no custom pytest markers, `--strict-markers` everywhere (app `pyproject.toml:134`), coverage `fail_under = 90` (`:164`). No `performance` marker exists.

### 3.4 Observability (juniper-deploy) — the Grafana path

- **Prometheus config**: `juniper-deploy/prometheus/prometheus.yml` (canonical) + `prometheus.demo.yml`. Globals `scrape_interval: 15s`, `evaluation_interval: 15s`, `scrape_timeout: 10s`, `external_labels: {deployment: "docker-compose"}` (`:45-49`); `rule_files:` at `:56`.
- **Five scrape jobs, all `static_configs`**: `prometheus` → `localhost:9090` (`:61-68`), `juniper-data` → `juniper-data:8100` @10s (`:73-83`), `juniper-cascor` → `juniper-cascor:8200` @10s (`:87-97`), `juniper-recurrence` → `juniper-recurrence:8210` @15s (`:104-114`), `juniper-canopy` → `juniper-canopy:8050` @15s (`:116-126`). Each target carries static labels `service: <name>` + `environment: "docker"` and `honor_labels: false` (e.g. `:78,82-83`).
- **No service discovery** of any kind (`file_sd_configs` / `dns_sd_configs` / `docker_sd_configs` / `relabel_configs` — zero hits in `juniper-deploy/prometheus/`). **No `extra_hosts` / `host.docker.internal` / `host-gateway` anywhere** in juniper-deploy. **Pushgateway is absent and explicitly rejected** (`juniper-ml/notes/legacy/METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md:81,83`).
- **Enabling facts**: Prometheus runs with `--web.enable-lifecycle` (`juniper-deploy/docker-compose.yml:854`) so `POST /-/reload` works; its config dir is mounted **read-only** `./prometheus:/etc/prometheus:ro` (`:858`); it publishes `127.0.0.1:9090:9090` (`:856`) and joins `backend, data, frontend, monitoring` (`:859-863`).
- **Grafana service**: `grafana/grafana:12.4.0`, `profiles: ["observability"]`, published `127.0.0.1:${GRAFANA_HOST_PORT:-3001}:3000` (`docker-compose.yml:918-923`), provisioning bind-mounted `./grafana/provisioning:/etc/grafana/provisioning:ro` (`:934`).
- **Grafana dashboard provider**: folder "Juniper", `type: file`, `updateIntervalSeconds: 30`, `allowUiUpdates: true`, path `/etc/grafana/provisioning/dashboards` (`grafana/provisioning/dashboards/dashboard-providers.yml:5-15`) — **drop a JSON in the dir and it appears within 30 s**.
- **Existing dashboards (4)**: `juniper-overview.json`, `juniper-cascor.json`, `juniper-data.json`, `juniper-canopy.json`. **There is no `juniper-recurrence` dashboard.**
- **Dashboard invariants (test-pinned)**: every panel needs a unique **integer** `id` and the top-level `id` must be `null` (`juniper-deploy/tests/test_grafana_dashboard_ids.py:33-45,54-60`).
- **Metrics auth is IP-allowlist only, no token**: `MetricsAuthMiddleware` (`juniper-ml/juniper-observability/juniper_observability/middleware/metrics_auth.py:104-183`), default `("127.0.0.1", "::1")` (`:49`). Compose env enables all four services' metrics (`juniper-deploy/.env.observability:24-27`) and extends allowlists with compose CIDRs while **always keeping loopback** (`:61-64`, rationale `:56-57`). **Implication: a host-bound `/metrics` on 127.0.0.1 needs no auth change.**
- **Bring-up**: `make obs` / `make monitor` (full profile, `juniper-deploy/Makefile:144-152`) and `make obs-demo` (`:154-163`).
- **Run-scoped labels**: no `run_id` / `experiment_id` precedent exists, and the ecosystem enforces the **anti-precedent** "R1.1 cardinality discipline" — closed-set labels validated at the helper boundary (`juniper-cascor/src/api/observability.py:384-389`).
- Sanctioned identity vehicles: (a) `Info` metrics via `register_info_or_update(name, description, **info_labels)` (`juniper-observability/juniper_observability/prometheus_helpers.py:214`), and (b) **scrape-side static target labels** with `honor_labels: false`.

### 3.5 juniper-ml tooling to build on

- **`util/isolated_stack.bash`** — the model. Non-default ports data `8101` / cascor `8202` / canopy `8051` (`:58-60`), rationale `:5-11`; `RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"` with `LOG_DIR` and per-service pidfiles (`:67-69`).
- Its health gate `wait_for_health()` polls `/v1/health` every 2 s to `JUNIPER_E2E_HEALTH_TIMEOUT` default 60 (`:134-147`, `:71`); teardown is **kill-by-port** via `port_pid()` scraping `ss -tlnpH "sport = :${port}"` (`:127-131`); `activate_conda()` does `set +u` → `conda activate` → `set -u` (`:150-165`); `--dry-run` starts and kills nothing.
- Operator contract: [`docs/REFERENCE.md`](../docs/REFERENCE.md) Isolated Stack E2E section; recipe: [`JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md`](JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md).
- **`util/juniper_plant_all.bash` / `util/juniper_chop_all.bash`** — the operator host stack: data `8100`, cascor `8201`, canopy `8050`, worker health `8210` (`plant:111,125,148,183`); a single shared `JuniperProject.pid` (`plant:84-85`); port preflight `check_port_available()` (`plant:192-202`, calls `:375-378`). **Neither script knows about juniper-recurrence** (zero matches for `recurrence` in either).
- **`util/get_cascor_*.bash`** — six curl helpers reading legacy `CASCOR_HOST` / `CASCOR_PORT` (default `localhost:8201`), hitting `/v1/training/status`, `/v1/metrics`, `/v1/metrics/history?count=10|100`, `/v1/network`, `/v1/network/topology`.
- **`conf/`** in juniper-ml is env-provenance snapshots only — **not** an app-config dir; no YAML app-config loader exists in the repo.

---

## 4. Gap Analysis

| ID       | Gap                                                                                                                  | Evidence                                                                                                         | Severity   |
|----------|----------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|------------|
| **G-1**  | No experiment-config file layer in either app. Hyperparameters and dataset choices are constants-file                | cascor `src/api/settings.py:124-129` (env/`.env` only) + `src/cascor_constants/`;                                | **High**   |
|          |   or env-only, so an experiment cannot be captured as a versionable artifact.                                        |   recurrence `settings.py:38` (no `env_file`), no YAML loader                                                    |            |
| **G-2**  | No host→Prometheus path. A CLI-launched cascor/recurrence on an experiment port is invisible to Grafana.             | five `static_configs` container targets only (`juniper-deploy/prometheus/prometheus.yml:61-126`);                | **High**   |
|          |                                                                                                                      |   no `extra_hosts`/`host.docker.internal` in juniper-deploy                                                      |            |
| **G-3**  | cascor Prometheus metrics are **off by default**, so a naive CLI launch exports nothing.                             | `metrics_enabled: bool = False` (`juniper-cascor/src/api/settings.py:373`, const `:67-68`)                       | **High**   |
| **G-4**  | No juniper-recurrence Grafana dashboard exists, despite recurrence exporting seven domain collectors.                | zero `recurrence` matches under `juniper-deploy/grafana/`; collectors `juniper_recurrence/metrics.py:29-36`      | **Medium** |
| **G-5**  | Recurrence has **zero plotting code**; there is no forecast-vs-truth, residual, or dataset visual anywhere.          | no `matplotlib`/`pyplot` in the monorepo; analysis is the markdown bands report `bench/run_benchmark.py:260-324` | **High**   |
| **G-6**  | cascor's in-process training-start fallback **silently ignores** every generator except `spiral` —                   | `src/api/routes/training.py:75` (`== "spiral"` only); no else-branch                                             | **High**   |
|          |   an experiment asking for `xor` trains on whatever data is already loaded, with no error.                           |                                                                                                                  |            |
| **G-7**  | cascor's staged `dataset_type` Literal admits only 6 names, omitting `gaussian`, `checkerboard`,                     | `src/api/models/training.py:188`; `manager.py:3289-3292` names `gaussian` in comment, no typed field             | **Medium** |
|          |   sequence generators; `gaussian` reachable only as untyped passthrough.                                             |                                                                                                                  |            |
| **G-8**  | `ar_p` is fully implemented in juniper-data but **not registered** in recurrence's bench registry,                   | registry `juniper-data/juniper_data/api/routes/generators.py:137`; absent from `bench/datasets.py:244-262`       | **Medium** |
|          |   so it is unreachable from `bench/`.                                                                                |                                                                                                                  |            |
| **G-9**  | `delay_product` (the DP-3 nonlinear-capacity probe) is registered in bench but has **no committed result**,          | `bench/datasets.py:137-182`; `git ls-files bench/results/` has no `delay_product.json`                           | **Medium** |
|          |   so the capacity claim has no reproducible in-repo artifact.                                                        |                                                                                                                  |            |
| **G-10** | `juniper-data-client` lacks name constants for all 7 newer generators (6 sequence/regression + `equities`), and      | `juniper_data_client/constants.py:138-150`; `tests/test_generator_parity.py:27-39,72-76`                         | **Medium** |
|          |   parity gate cann't catch this because `EXPECTED_SERVER_GENERATORS` is **stale hand-maintained mirror** of 9 names. |                                                                                                                  |            |
| **G-11** | Fixed shared output paths make two same-checkout runs unsafe: cascor service `src/snapshots/`, cascor CLI            | `manager.py:4300-4304`; `constants_hdf5.py:45-46`; `constants.py:460-461`; `bench/run_benchmark.py:29`           | **High**   |
|          |   `src/cascor_snapshots/`, shared `logs/juniper_cascor.log`, recurrence `bench/results/`.                            |                                                                                                                  |            |
| **G-12** | On-host port collision: juniper-recurrence binds `8210` by default, which is also                                    | `juniper_recurrence/settings.py:47`; `juniper-ml/util/juniper_plant_all.bash:183`                                | **Medium** |
|          |   `JUNIPER_WORKER_HEALTH_PORT`'s default in the operator stack.                                                      |                                                                                                                  |            |
| **G-13** | The cascor systemd unit points at a conda env that no longer exists on this host                                     | `juniper-cascor/scripts/juniper-cascor.service:30`; `ls /opt/miniforge3/envs/`                                   | **Low**    |
|          |   (`JuniperCascor`, now `-DEPRECATED`).                                                                              | _                                                                                                                |            |
| **G-14** | No per-run identity in metrics, and the ecosystem's cardinality discipline forbids inventing                         | no `run_id` precedent; R1.1 anti-precedent `juniper-cascor/src/api/observability.py:384-389`                     | **Medium** |
|          |   a high-cardinality `run_id` sample label.                                                                          |                                                                                                                  |            |
| **G-15** | No concurrent-session port-allocation policy anywhere; `check_port_available()`                                      | `plant:192-202`, `plant:84-85`; nothing in `notes/concurrency/` covers multi-session                             | **High**   |
|          |   is a bare pre-flight with a TOCTOU window, and `JuniperProject.pid` is a single shared file.                       |                                                                                                                  |            |
| **G-16** | `mnist` is unavailable on this host (HF `datasets` absent from both candidate envs), so a cascor mnist               | live `generator_available()` = `False`; 501 mapping `juniper-data/juniper_data/api/routes/datasets.py:165-168`   | **Low**    |
|          |   experiment 501s at juniper-data.                                                                                   |                                                                                                                  |            |
| **G-17** | Recurrence has no `performance` pytest marker and its bench emits **no Prometheus metrics** — offline JSON only,     | no `pytest.mark.performance` in the monorepo; `bench/run_benchmark.py` writes files only                         | **Medium** |
|          |   so recurrence benchmark timings cannot land in Grafana today.                                                      |                                                                                                                  |            |
| **G-18** | Recurrence's server-side model is memory-only, so a service-mode experiment leaves no model artifact                 | `juniper_recurrence/state.py` docstring ("deferred to WS-8")                                                     | **Low**    |
|          |   unless the driver saves one.                                                                                       |                                                                                                                  |            |

---

## 5. YAML Experiment-Config Layer (design)

### 5.1 Ratified precedence

```text
CLI args  >  YAML config file  >  process env vars  >  .env (where the app already supports it)  >  constants / field defaults
```

Rationale: **a run is fully reproducible from its YAML** (the YAML beats ambient env, which is what makes a captured experiment portable between shells and sessions), while **the launcher still wins for infrastructure it allocates** — ports, bind host, upstream data URL — because the bind rides CLI flags (the uvicorn CLI for cascor, `serve --host/--port` for recurrence), which sit above YAML,
and `service.host` / `service.port` / `service.juniper_data_url` are additionally rejected outright in experiment YAML (§5.6 rule 6). Env stays below YAML but above constants so existing container/compose deployments keep behaving identically when no YAML is supplied.

**Alternatives considered (brief).**

- *(a) Env-above-YAML* — the pydantic-settings default ordering; rejected because a stale exported `JUNIPER_CASCOR_PORT` in the operator's shell would silently override a checked-in experiment, defeating reproducibility.
- *(b) YAML-only, no env* — rejected: it would break the compose/Docker deployments that configure exclusively through env.
- *(c) A separate runner process holding all config and pushing it over REST* — rejected as the *primary* mechanism, because service-level knobs (bind host/port, metrics enablement, data URL) are read at startup, before any REST call. It survives as the mechanism for the *per-run* training parameters the driver POSTs (§6.3).

### 5.2 Implementation mechanism (both apps)

Both apps already use pydantic-settings; both hosts already have `pydantic-settings` ≥ 2.12 (so the `PydanticBaseSettingsSource` hook and the stock `YamlConfigSettingsSource` are importable), and cascor already depends on `PyYAML>=6.0` (`juniper-cascor/pyproject.toml:100`).

**The stock YAML source alone is insufficient — this is why the loader is a custom projection source.** `YamlConfigSettingsSource(settings_cls, yaml_file=<experiment.yaml>)` reads the file's **top-level mapping** as field values, and the experiment YAML's top level is `schema_version` / `experiment` / `service` / `dataset` / `training` / `runtime` / `outputs` (§5.4-§5.5) — none of which is a Settings field.
Both apps additionally set `extra="ignore"` (cascor `src/api/settings.py:129`; recurrence `juniper_recurrence/settings.py:38`), so every key would be **silently dropped**: the stock source would no-op the whole layer.
**PROPOSED** in both repos instead: a small custom `ExperimentYamlSettingsSource(PydanticBaseSettingsSource)` that parses the experiment YAML once and yields **only the `service:` block's keys** as settings values; the other blocks (`dataset:`, `training:` / `train:`, `crossval:`, `predict:`, `runtime:`, `outputs:`) are consumed by the driver / launcher layers (§6) and **never** by `Settings`. The source is inserted between init-kwargs and env via `settings_customise_sources`:

```python
# PROPOSED — juniper-cascor/src/api/settings.py (inside class Settings)
@classmethod
def settings_customise_sources(cls, settings_cls, init_settings, env_settings,
                               dotenv_settings, file_secret_settings):
    """CLI/init > YAML service: block > env > .env > defaults (experiment-config layer)."""
    yaml_path = os.environ.get("JUNIPER_CASCOR_CONFIG_FILE")  # PROPOSED env var
    sources = [init_settings]
    if yaml_path:
        sources.append(ExperimentYamlSettingsSource(settings_cls, yaml_file=yaml_path))
    sources += [env_settings, dotenv_settings, file_secret_settings]
    return tuple(sources)
```

- **PROPOSED** new env var `JUNIPER_CASCOR_CONFIG_FILE` and **PROPOSED** flag `--config PATH` on `src/server.py` and `src/main.py`; the flag sets the env var before `get_settings()` is first called (necessary because `get_settings()` is `@lru_cache`d at `src/api/settings.py:506-507`). `server.py --config` is a Wave-3 **operator convenience only** — the experiment stack launches the cascor service through the uvicorn-factory CLI form, which owns the bind (§6.1/§6.2), threading the config path as the env var.
- **PROPOSED** mirror for recurrence: env var `JUNIPER_RECURRENCE_CONFIG_FILE` and `--config PATH` on both `serve` and `train` subcommands (`juniper_recurrence/main.py:43-63`). Recurrence does **not** currently declare PyYAML, so this also needs a **PROPOSED** dependency addition (`pydantic-settings[yaml]` or an explicit `PyYAML>=6.0`).
- **Fail-loud on unknown keys.** Because both `Settings` classes are `extra="ignore"` (`settings.py:129`; recurrence `:38`), model-level rejection cannot be relied on: the **projection source itself** validates the `service:` block's key set against the model's field names, and the loader validates the top-level block set, raising before the app boots (§5.6 rules 1 and 6). This mirrors the precedent already set by `TrainingParams`' `extra="forbid"` (`src/api/models/training.py:44`).

### 5.3 File location and naming

- **cascor**: `juniper-cascor/conf/experiments/<name>.yaml` — `conf/` exists and already hosts runtime-loaded YAML (`conf/logging_config.yaml`, loaded at `src/log_config/logger/logger.py:611`); `conf/experiments/` is **PROPOSED**.
- **recurrence**: `juniper-recurrence/conf/experiments/<name>.yaml` — the repo has **no** `conf/` directory today; both the dir and its contents are **PROPOSED**.
- The run driver (§6.3) additionally accepts a path anywhere on disk, and always copies the resolved YAML into the run's artifact dir so the run is self-describing.

### 5.4 cascor experiment YAML — schema sketch (PROPOSED)

Every key below maps to a real, verified target. `service:` keys map to `Settings` fields (via the §5.2 projection source); `training.params` keys map 1:1 to `TrainingParams` (`src/api/models/training.py:51-72`); `dataset` maps to the juniper-data generator params for the named generator; `runtime:` and `outputs:` are experiment-only blocks consumed by the launcher / driver, never by `Settings`.

```yaml
# PROPOSED: juniper-cascor/conf/experiments/spiral-baseline.yaml
schema_version: 1                      # PROPOSED: loader rejects unknown majors
experiment:
  name: spiral-baseline
  description: "Two-arm spiral, default cascade budget, decision-boundary plots"
  seed: 20260729                       # REQUIRED: pins juniper-data dataset determinism

service:                               # -> juniper-cascor Settings (projected per §5.2; launcher CLI still wins)
  log_level: INFO                      # settings.py:170
  metrics_enabled: true                # settings.py:373 (code default FALSE — must be set)
  auto_start: false                    # settings.py:428 — keep OFF; the driver starts training
  auto_start_data_service: false       # settings.py:429 — never let cascor spawn a data service
  # host / port / juniper_data_url are launcher-owned and REJECTED here (§5.6 rule 6)

dataset:                               # -> juniper-data POST /v1/datasets
  generator: spiral                    # GENERATOR_REGISTRY key (generators.py:54)
  persist: true                        # client.py:415
  tags: ["experiment", "spiral-baseline"]
  ttl_seconds: 86400                   # client.py:422 — reaps the artifact with the run
  params:                              # spiral/params.py:68-128
    n_spirals: 2
    n_points_per_spiral: 500
    n_rotations: 3.0
    noise: 0.05
    algorithm: modern                  # modern | legacy_cascor
    train_ratio: 0.8
    test_ratio: 0.2
    seed: 20260729

training:                              # -> POST /v1/training/start
  start_fresh: true                    # models/training.py:167
  epochs: null                         # models/training.py:153 (shorthand for params.max_epochs)
  params:                              # TrainingParams — extra="forbid" (models/training.py:44)
    max_epochs: 2000                   # :51  (1..1_000_000)
    max_iterations: 12                 # :52
    early_stopping: true               # :53
    learning_rate: 0.05                # :54  (0 < x <= 10.0)
    candidate_learning_rate: 0.05      # :55
    correlation_threshold: 0.2          # :56  (0 < x <= 1.0)
    candidate_pool_size: 8             # :57  (1..256)
    max_hidden_units: 24               # :58  (1..10_000)
    patience: 200                      # :68
    convergence_threshold: 1.0e-5      # :69
    candidate_patience: 100            # :71
    candidate_epochs: 500              # :72

runtime:                               # PROPOSED experiment-only block — launcher-exported process env, never Settings
  num_processes: 4                     # -> CASCOR_NUM_PROCESSES (cascade_correlation.py:2281)
  blas_threads: 2                      # -> OMP/MKL/OPENBLAS_NUM_THREADS (main.py:48-50)
  eval_metrics_enabled: true           # -> JUNIPER_CASCOR_EVAL_METRICS_ENABLED (manager.py:32-39)

outputs:                               # PROPOSED experiment-only block, consumed by the driver/launcher
  decision_boundary_resolution: 200    # -> GET /v1/decision-boundary?resolution=
  metrics_history_count: 1000          # -> GET /v1/metrics/history?count=
  plots: [dataset, decision_boundary, training_history]
  snapshot_at_end: true                # -> POST /v1/snapshots (routes/snapshots.py:144)
  max_wall_seconds: 3600               # wall-clock budget for the drive loop (Q-2)
  grafana_bridge: true                 # false = no §7.3 relay, no target file; run-local metrics_series.csv capture still works (§6.3)
```

`eval_metrics_enabled` lives in `runtime:`, **not** `service:` — the manager reads `JUNIPER_CASCOR_EVAL_METRICS_ENABLED` from the process environment directly (`src/api/lifecycle/manager.py:32-39`); no such field exists on `Settings`, so the launcher exports it as process env. An optional future cascor work item could promote it to a real `Settings` field.

### 5.5 recurrence experiment YAML — schema sketch (PROPOSED)

```yaml
# PROPOSED: juniper-recurrence/conf/experiments/irregular-sine-rff.yaml
schema_version: 1
experiment:
  name: irregular-sine-rff
  description: "Irregular-Δt sine, RFF readout, walk-forward CV (DP-3 rung 2a)"
  seed: 20260729

service:                               # -> juniper_recurrence Settings
  log_level: INFO                      # settings.py:50 (via SettingsBase)
  log_format: text                     # settings.py:54
  metrics_enabled: true                # settings.py:81 (already default true)
  rate_limit_enabled: false            # settings.py:65 — a tight driver loop must not be throttled
  default_d: 16                        # settings.py:76
  default_theta: null                  # settings.py:77 — null = data-driven θ
  default_ridge: 0.0                   # settings.py:78 (float or "gcv")
  # host / port / juniper_data_url are launcher-owned and REJECTED here (§5.6 rule 6)

dataset:                               # -> DatasetRef (schemas.py:72-88)
  generator: irregular_sine            # GENERATOR_REGISTRY key (generators.py:145)
  split: train                         # schemas.py:80
  params:                              # irregular_sine/params.py:30-35 + _synthetic.py:48-73
    n_steps: 4000
    lookback: 64
    horizon: 1
    sample_dt: 1.0
    jitter: 0.30
    n_components: 3
    noise_std: 0.10
    train_ratio: 0.8
    scaling: standardize               # identity | standardize
    seed: 20260729

train:                                 # -> POST /v1/train (schemas.py:106-119)
  d: 16
  theta: null
  ridge: 1.0                           # float or "gcv"
  readout: rff                         # linear | rff | mlp
  rff_features: 256                    # _readout.py:37-48 default 256
  rff_gamma: median                    # positive float or "median"

crossval:                              # -> POST /v1/crossval (schemas.py:206-230)
  enabled: true
  n_folds: 5                           # >= 2
  scheme: expanding                    # expanding | rolling
  embargo: 2
  min_train: null

predict:                               # -> POST /v1/predict (routers/predict.py:29)
  enabled: true
  from_dataset_split: test             # driver re-refs the same dataset with split=test

outputs:                               # PROPOSED driver-consumed block
  plots: [dataset_overview, dt_histogram, forecast_vs_truth, residuals, crossval_folds]
  grafana_bridge: true                 # false = no §7.3 relay, no target file
  save_model: true                     # service mode leaves NO model artifact (G-18); true = the driver re-runs `juniper-recurrence train --out` with identical parameters as an explicit, manifest-recorded extra step (main.py:134-136)
```

### 5.6 Loader validation rules (PROPOSED)

1. Unknown top-level block, or unknown key inside a known block → **error before boot**, listing the offending keys and the nearest valid names. Unknown keys **within `service:`** are rejected fail-loud by the §5.2 projection source itself — both apps' `Settings` are `extra="ignore"` (cascor `settings.py:129`; recurrence `:38`), so model-level rejection cannot be relied on.
2. `schema_version` absent or > the loader's max → error.
3. `experiment.seed` absent → error. Rationale: `generate_dataset_id` is only deterministic when `params['seed']` is set (`juniper-data/juniper_data/core/dataset_id.py:30-34`), so a seedless experiment is not reproducible by construction.
4. `dataset.generator` is checked against the live `GET /v1/generators` response (which reports `available`) **before** the run starts, so an unavailable generator (e.g. `mnist` on this host) fails fast with the install hint instead of surfacing as a mid-run 501.
5. Values are range-validated by the existing pydantic models — the YAML source feeds the same `Settings` / `TrainingParams` / `TrainRequest` validators, so no new range logic is written.
6. **Infrastructure keys are rejected, not honoured**: `service.host`, `service.port`, and `service.juniper_data_url` in an experiment YAML → error. Infrastructure is launcher-owned (CLI flags / process env, §6); experiment YAML owns science parameters only. `service.eval_metrics_enabled` is likewise invalid — it is not a `Settings` field and belongs in `runtime:` (§5.4).
7. **`max_epochs` without `output_epochs` → WARN, recorded on the manifest** (added 2026-08-17 from juniper-ml#1143 §2.2). The two keys are not the same budget and the difference is silent:
   * **service** — `TrainingParams.max_epochs` bounds only the **initial** output pass; every later per-round pass reads `self.output_epochs` (`cascade_correlation.py:4591`/`:4768`/`:4820`), which falls back to `_PROJECT_MODEL_OUTPUT_EPOCHS = 10000` when unset (`:716`). The network says so at `:1876-1882` — *"The two therefore agree only while a caller leaves `max_epochs` unset"*.
   * **direct CLI** — `_W11_TRAINING_KEY_MAP` **aliases** `max_epochs → output_epochs` (`main.py:238-249`), so it bounds every pass; an explicit `output_epochs` wins over the alias (`:291-292`).

   A config carrying only `max_epochs: N` therefore runs the CLI at N epochs per output pass and the service at N then **10000** — a several-fold per-pass asymmetry over a 64–128-unit run, which makes the service arm both slower and better-trained than the config appears to request. It is invisible at smoke scale, where there is only the initial pass.

   **Standard procedure**: any config used for a CLI-vs-service comparison MUST set `max_epochs` and `output_epochs` **to the same value**; a service-only config MAY set only `max_epochs`, and the warning then documents that the split is deliberate. Deliberately non-fatal — `spiral-baseline.yaml` ships with the split, so erroring would break the canonical baseline and every suite inheriting it. Gate: `ConfigValidationTest.test_max_epochs_without_output_epochs_warns`.
8. `OPEN QUESTION Q-1`: should the loader also *emit* a fully-resolved YAML (every default materialised) into the run dir, alongside the as-written file? A resolved copy is far better provenance but doubles the artifacts and can drift from the app's own defaults if the dump is hand-rolled. Recommendation: yes, dumped from the live `Settings` object rather than reconstructed.

---

## 6. Launch & Run Tooling (design)

### 6.1 Canonical launch commands as they exist TODAY (no new tooling)

These are the recipes the tooling automates; each is runnable now. Ports here are the **experiment** ranges proposed in §9.3. The recipes reference `$RUN_DIR`: for a manual run any writable directory works — `RUN_DIR=$(mktemp -d)` is enough — and §6.2 formalises the real run-dir contract.

```bash
# ---- juniper-data (dedicated per-run instance) --------------------------------------
# Live env already carries uvicorn 0.40.0 + editable juniper_data 0.6.0.
conda activate JuniperData
cd /home/pcalnon/Development/python/Juniper/juniper-data
JUNIPER_DATA_STORAGE_PATH="$RUN_DIR/data" \
JUNIPER_DATA_METRICS_ENABLED=true \
JUNIPER_DATA_EQUITIES_CACHE_DIR="$RUN_DIR/equities-cache" \
PYTHON_GIL=0 python -m juniper_data --host 127.0.0.1 --port 8110
curl -sf http://127.0.0.1:8110/v1/health          # gate
curl -s  http://127.0.0.1:8110/v1/generators      # live availability per generator
```

```bash
# ---- juniper-cascor service ---------------------------------------------------------
conda activate JuniperCascor1
cd /home/pcalnon/Development/python/Juniper/juniper-cascor/src
LD_LIBRARY_PATH='' \
JUNIPER_CASCOR_METRICS_ENABLED=true \
JUNIPER_CASCOR_AUTO_START=false \
JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false \
JUNIPER_CASCOR_LOG_LEVEL=INFO \
JUNIPER_DATA_URL=http://127.0.0.1:8110 \
uvicorn api.app:create_app --factory --host 127.0.0.1 --port 8230
# The uvicorn CLI owns the bind: host/port arrive as CLI flags, which sit ABOVE YAML in the
# §5.1 precedence, so an experiment YAML can never override the launcher's port allocation.
# `python server.py` remains the operator/systemd form only — server.py parses NO CLI flags
# (src/server.py:15-25), so under it the bind would ride env, which sits BELOW YAML.
curl -sf http://127.0.0.1:8230/v1/health
curl -sfL http://127.0.0.1:8230/metrics | head   # -L required: the ASGI mount 307-redirects /metrics -> /metrics/; only non-404 because METRICS_ENABLED=true
```

`LD_LIBRARY_PATH=''` is carried over from `util/isolated_stack.bash:208` (the libtorch/python collision class); the uvicorn-factory launch form is the same one `isolated_stack.bash:211` already uses. `JUNIPER_CASCOR_METRICS_ENABLED=true` is **mandatory** — the code default is `False` (`src/api/settings.py:373`).

```bash
# ---- juniper-cascor direct training CLI (no service) --------------------------------
conda activate JuniperCascor1
cd /home/pcalnon/Development/python/Juniper/juniper-cascor/src
JUNIPER_DATA_URL=http://127.0.0.1:8110 python main.py                 # exit 3 if URL unset, 4 if data unhealthy
JUNIPER_DATA_URL=http://127.0.0.1:8110 python main.py --profile --profile-output "$RUN_DIR/profiles"
```

```bash
# ---- juniper-recurrence service -----------------------------------------------------
conda activate JuniperCascor1        # the only env carrying juniper_recurrence today
JUNIPER_RECURRENCE_METRICS_ENABLED=true \
JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false \
JUNIPER_DATA_URL=http://127.0.0.1:8110 \
juniper-recurrence serve --host 127.0.0.1 --port 8260
# Allow ~10-15 s before the port binds (heavy import stack, Dockerfile:88-91)
curl -sf http://127.0.0.1:8260/v1/health/ready
```

```bash
# ---- juniper-recurrence headless train CLI (no service) -----------------------------
conda activate JuniperCascor1
mkdir -p "$RUN_DIR/artifacts/results"   # LMUSerializer.save is a bare np.savez — it creates no parent dirs
JUNIPER_DATA_URL=http://127.0.0.1:8110 \
juniper-recurrence train --generator irregular_sine --split train \
  --d 16 --ridge 1.0 --readout rff --rff-features 256 --rff-gamma median \
  --out "$RUN_DIR/artifacts/results/model.npz"
```

```bash
# ---- juniper-recurrence bench harness (offline, model-level) ------------------------
conda activate JuniperCascor1
cd /home/pcalnon/Development/python/Juniper/juniper-recurrence
python -m bench.run_benchmark        # writes bench/results/*.json + REPORT.md (fixed path — see H-6)
```

### 6.2 `util/experiment_stack.bash` (PROPOSED, juniper-ml)

Modeled directly on `util/isolated_stack.bash` — same shape, same `--dry-run` discipline, same health gating — but **per-run** rather than singleton, and with **no canopy service**.

| Behaviour | Design | Precedent |
| --- | --- | --- |
| Actions | exactly one of `--up`, `--down`, `--status`, plus optional `--dry-run`; misuse → exit 2 | `isolated_stack.bash:320-348` |
| Run identity | `RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$(openssl rand -hex 2)"` | **PROPOSED** |
| Run dir | `RUN_DIR="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}/${RUN_ID}"` — under `$HOME`, **not** `/tmp`, so a reaped sandbox cannot destroy results | departs deliberately from `isolated_stack.bash:67` (`/tmp/juniper-e2e`) |
| Port allocation | per candidate port in the app's range: `mkdir "$LOCK_ROOT/$port.lock"` (fails if held) **then** confirm nothing is listening via `ss -tlnH "sport = :$port"`; hold the lockdir for the run, release on teardown. **Serialises experiment launchers against each other**; the residual race vs non-participating processes surfaces as the service's own bind failure, caught by the health gate | closes the `plant:192-202` TOCTOU *among participants*; `ss` idiom from `isolated_stack.bash:127-131` |
| cascor launch form | `uvicorn api.app:create_app --factory --host 127.0.0.1 --port $CASCOR_PORT` — the uvicorn CLI owns the bind, so experiment YAML can never override the launcher's allocation (`src/server.py:15-25` parses no flags; `python server.py` stays the operator/systemd form) | `isolated_stack.bash:211`; §6.1 |
| Lock root | `LOCK_ROOT="${JUNIPER_EXP_LOCK_ROOT:-${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments}"` — a lock is ephemeral state, so runtime-dir placement is correct here | **PROPOSED** |
| Services | `data` (dedicated per-run instance, default on; `--shared-data URL` to reuse one), `cascor` (`--cascor`), `recurrence` (`--recurrence`); at least one app required. **Never canopy.** | **PROPOSED** |
| Config | `--config PATH` threaded to the app — recurrence via `serve --config`, cascor via the `JUNIPER_CASCOR_CONFIG_FILE` env var (its service launch is the uvicorn-factory CLI, which takes no app flags); all other per-run config passed as **process env only**, never written to any `.env` | cascor reads `.env` from CWD (`settings.py:126`), so writing one would cross-talk |
| Env pinning | `LD_LIBRARY_PATH=''`, `JUNIPER_DATA_URL=http://127.0.0.1:$DATA_PORT`, `JUNIPER_DATA_METRICS_ENABLED=true`, `JUNIPER_CASCOR_METRICS_ENABLED=true`, `JUNIPER_RECURRENCE_METRICS_ENABLED=true`, `JUNIPER_CASCOR_AUTO_START=false`, `JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false`, `JUNIPER_DATA_STORAGE_PATH=$RUN_DIR/data`, `JUNIPER_DATA_EQUITIES_CACHE_DIR=$RUN_DIR/equities-cache` | §6.1; §7.3 toggles |
| Health gating | `wait_for_health` polling `/v1/health` (data, cascor) and `/v1/health/ready` (recurrence) every 2 s to `JUNIPER_EXP_HEALTH_TIMEOUT` (default **90** — higher than isolated-stack's 60 because recurrence needs 10-15 s of import before binding) | `isolated_stack.bash:134-147`; `juniper-recurrence/Dockerfile:88-91` |
| Order | data → cascor → recurrence (recurrence never depends on cascor; the order is just deterministic) | `isolated_stack.bash:266-268` |
| Pidfiles | `$RUN_DIR/juniper-{data,cascor,recurrence}.pid`. **`JuniperProject.pid` is never read or written** — that file belongs to `juniper_plant_all.bash`/`chop_all` | `isolated_stack.bash:188,212,237`; hazard from `plant:84-85` |
| Teardown | kill **by recorded pid** first, verify the port is free, fall back to kill-by-port only for the recorded port; then release the port lockdirs and write `$RUN_DIR/teardown.json`. Reverse order recurrence → cascor → data | pid-first improves on `isolated_stack.bash:246-257`'s pure kill-by-port, which could kill an unrelated process that grabbed the port |
| Grafana bridge | only when the run enables it (`outputs.grafana_bridge: true`): on `--up`, discover the gateway IP and start one `socat` relay per scraped service (§7.3, pidfiles under `$RUN_DIR/relays/`), then write `$TARGETS_DIR/$RUN_ID.json`; on `--down`, kill the recorded relay pids and remove the target file (§7.2) | **PROPOSED** |
| `--dry-run` | prints every command with ports/paths expanded; creates nothing, starts nothing, kills nothing, writes no target file | `isolated_stack.bash:249,288` |
| Conda | `activate_conda()` with `set +u` → `conda activate` → `set -u` | `isolated_stack.bash:150-165`; `plant:407-412` |

### 6.3 `util/experiments/run_experiment.py` (PROPOSED, juniper-ml)

Path-invoked (`python util/experiments/run_experiment.py --config ... --run-dir ...`), stdlib + `numpy` + `matplotlib` + `PyYAML` + `requests` — all four verified present in `JuniperCascor1`; verify in `JuniperData` during P0.3. Deliberately **not** a console script and **not** dependent on any Juniper package, so it runs from whichever env hosts the app.

Responsibilities, in order:

1. **Load + validate** the experiment YAML (§5.6); resolve the app kind from its shape (`training:` ⇒ cascor, `train:` ⇒ recurrence).
2. **Health-wait** on the target service (`/v1/health` or `/v1/health/ready`), bounded.
3. **Pre-flight the dataset**: `GET /v1/generators` on the run's juniper-data, assert `dataset.generator` present **and** `available: true`.
4. **Drive the run.**
   - *cascor*: `POST /v1/datasets` on juniper-data (recording the returned `dataset_id`), then `POST /v1/training/start` with `{dataset: {...}, params: {...}, start_fresh: true}`, then poll `GET /v1/training/status` until the FSM reaches `COMPLETED` or `FAILED` (`src/api/lifecycle/state_machine.py:24-52`) or the wall-clock budget expires.
   - *cascor, non-spiral*: because of **G-6**, when `dataset.generator != "spiral"` the driver **must** stage through `POST /v1/training/dataset` (`routes/training.py:237`) rather than relying on `start`'s `dataset` field, and must then assert the loaded dataset's shape via `GET /v1/network` / `GET /v1/training/status` before accepting the run as valid.
   - *cascor, metrics series*: on each poll interval the driver also GETs the app's own loopback `/metrics` endpoint and appends an allowlisted subset — at minimum `juniper_cascor_candidate_correlation`, `juniper_cascor_hidden_units_total`, `juniper_cascor_training_loss`, `juniper_cascor_training_accuracy_ratio`, and the `juniper_cascor_training_step_duration_seconds` histogram sum/count — to `RUN_DIR/artifacts/results/metrics_series.csv`.
     Candidate correlation exists **only** there and in the WS `cascade_add` event — `/v1/metrics/history` rows carry no correlation field — so this series is the poll path's sole source for it. Side benefit: run-local metric capture works even with the Grafana bridge disabled.
   - *recurrence*: `POST /v1/train` (synchronous — the response **is** completion, `routers/training.py:37`), then optional `POST /v1/predict` against the `test` split, then optional `POST /v1/crossval`.
5. **Collect results**: cascor → `GET /v1/metrics`, `/v1/metrics/history?count=N`, `/v1/decision-boundary?resolution=R`, `/v1/network/topology`, and optionally `POST /v1/snapshots`; recurrence → `TrainResponse.final_metrics`, `PredictResponse`, `CrossValResponse` folds.
6. **Emit artifacts** into `$RUN_DIR/artifacts/{plots,results,logs}` (§8).
7. **Write the run manifest** `$RUN_DIR/manifest.json` (§13.4) and print a one-screen summary.
8. **Exit codes**: `0` success; `1` run did not meet acceptance criteria (including `stalled` runs, Q-2); `2` misuse / validation error; `3` service unreachable; `4` run reached `FAILED` / a 5xx.

`OPEN QUESTION Q-2`: cascor exposes no explicit "run finished" event other than the FSM reaching `COMPLETED`; with `early_stopping` and cascade growth, a long run can legitimately sit in `STARTED`. The driver needs both a wall-clock budget and a **stall** detector (no `current_epoch` change for N polls). Proposal: budget from the YAML (`outputs.max_wall_seconds`, default 3600) and stall = 120 s of no epoch progress → exit 1 with `outcome: "stalled"`, never a silent hang.

### 6.4 RUN_DIR layout (PROPOSED)

```bash
${JUNIPER_EXP_RUN_ROOT:-~/.local/state/juniper-experiments}/
└── 20260729T143012Z-9f2a/                     # RUN_ID = <UTC timestamp>-<4 hex>
    ├── manifest.json                          # run manifest (§13.4)
    ├── config/
    │   ├── experiment.yaml                    # verbatim copy of the input YAML
    │   └── experiment.resolved.yaml           # SHIPPED (Q-1): driver-resolved config + the service's own params echo, each tagged
    ├── env/
    │   └── launch.env                         # exact env each service was launched with (secrets redacted)
    ├── ports.json                             # {"data":8110,"cascor":8230,"recurrence":null}
    ├── juniper-data.pid
    ├── juniper-cascor.pid                     # only for the services this run started
    ├── relays/                                # socat relay pidfiles, one per scraped service (only when outputs.grafana_bridge — §7.3)
    ├── logs/
    │   ├── juniper-data.log
    │   ├── juniper-cascor.log
    │   └── run_experiment.log
    ├── data/                                  # JUNIPER_DATA_STORAGE_PATH for this run
    ├── equities-cache/                        # JUNIPER_DATA_EQUITIES_CACHE_DIR for this run
    ├── snapshots/                             # PROPOSED target once JUNIPER_CASCOR_SNAPSHOTS_DIR lands (W-6)
    ├── profiles/                              # cascor --profile-output target
    └── artifacts/
        ├── plots/     dataset.png, decision_boundary.png, training_history.png, …
        ├── results/   metrics_final.json, metrics_history.json, metrics_series.csv,
        │              decision_boundary.npz, topology.json, summary.md, stats.json, model.npz
        └── prometheus_target.json             # copy of the file_sd target written for this run
```

---

## 7. Metrics → Grafana for CLI-Launched Runs (design)

### 7.1 Chosen approach: file-based service discovery into the existing dockerized Prometheus

Keep `make obs` / `make obs-demo` exactly as-is (`juniper-deploy/Makefile:144-163`) and teach the existing Prometheus about host targets. Three **PROPOSED** juniper-deploy changes:

1. **Name the host-side destination.** Add to the `prometheus` service (`juniper-deploy/docker-compose.yml:842-866`):

   ```yaml
   # PROPOSED (juniper-deploy/docker-compose.yml, prometheus service)
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

   No such mapping exists today anywhere in juniper-deploy; the idiom appears only in service READMEs (`juniper-cascor/README.md:100`).
   **What this does — and does not — do**: inside the container, `host.docker.internal` resolves to the docker **bridge-gateway IP** (e.g. `172.17.0.1`), *not* to the host's loopback. A TCP connection addressed to that gateway IP can **never** be accepted by a socket bound to `127.0.0.1` — the kernel refuses it before any middleware runs, and the failure signature is **connection refused**, not 403.
   The experiment services stay loopback-bound, so the scrape's last hop is carried by the launcher-owned relay in §7.3.

2. **Give Prometheus a target dir.** The config mount is read-only (`docker-compose.yml:858`). Options are a nested dir under that mount, or a separate one:

   ```yaml
   # PROPOSED (same service) — see Q-3 on whether the second mount is needed at all
   volumes:
     - ./prometheus:/etc/prometheus:ro
     - ./prometheus/targets:/etc/prometheus/targets:ro   # host-writable dir, container-read-only
   ```

   `OPEN QUESTION Q-3`: `./prometheus/targets` sits inside the already-`:ro`-mounted `./prometheus`, so the nested mount is redundant unless the dir moves outside (e.g. `./prometheus-targets`). Prometheus only needs to **read** the target files; the *host* writes them. Recommendation: keep target files at `./prometheus/targets/`, rely on the existing `:ro` mount — no second volume — and gitignore the dir contents apart from a `.gitkeep`. Owner to confirm.

3. **Add the scrape job.** A single `file_sd_configs` job, appended after the five static jobs (`prometheus/prometheus.yml:61-126`):

   ```yaml
   # PROPOSED (juniper-deploy/prometheus/prometheus.yml)
   - job_name: "juniper-host-experiments"
     metrics_path: "/metrics"
     scheme: http
     scrape_interval: 10s
     scrape_timeout: 10s
     honor_labels: false
     file_sd_configs:
       - files:
           - "/etc/prometheus/targets/*.json"
         refresh_interval: 15s
   ```

   Prometheus picks up added/removed target files automatically at `refresh_interval`; `POST http://127.0.0.1:9090/-/reload` remains available for the `prometheus.yml` change itself because `--web.enable-lifecycle` is already set (`docker-compose.yml:854`).

### 7.2 Per-run target file (written by the launcher, PROPOSED)

```json
[
  {
    "targets": ["host.docker.internal:8230"],
    "labels": {
      "service": "juniper-cascor",
      "environment": "host-experiment",
      "run_id": "20260729T143012Z-9f2a",
      "experiment": "spiral-baseline"
    }
  },
  {
    "targets": ["host.docker.internal:8110"],
    "labels": {
      "service": "juniper-data",
      "environment": "host-experiment",
      "run_id": "20260729T143012Z-9f2a",
      "experiment": "spiral-baseline"
    }
  }
]
```

Why this respects the cardinality rules: `run_id` is a **scrape-side target label**, not a per-sample label baked into application code. With `honor_labels: false` (matching every existing job, e.g. `prometheus.yml:78`) Prometheus-side labels win, so the app never has to know a run id and the closed-set discipline enforced at cascor's helper boundary (`src/api/observability.py:384-389`) is untouched.

Cardinality is bounded by *concurrent* runs, and a completed run's target file is deleted at teardown, so the series go stale and age out of the active set. `environment: "host-experiment"` deliberately parallels the existing `docker` / `docker-demo` values (`prometheus.yml:82-83`; `prometheus.demo.yml:61`) so existing dashboards can be filtered by it.

**Secondary, in-app identity (PROPOSED, optional).** For a run id visible even when scraping is misconfigured, add a `register_info_or_update("juniper_cascor_experiment", "Current experiment run", run_id=..., experiment=...)` call behind an env var (`juniper-observability/juniper_observability/prometheus_helpers.py:214`).

Note this **requires app-side code in cascor and recurrence** — `set_build_info` cannot carry it, since its keyword surface is fixed to `git_sha` / `build_date` (`juniper-observability/juniper_observability/prometheus.py:29-35`). Ship the scrape-side path first; the `Info` metric is a nice-to-have.

### 7.3 Reaching a loopback-bound service — the launcher-owned relay, plus prerequisite toggles

**The bridge cannot reach loopback by itself.** As §7.1 item 1 states, `host-gateway` resolves to the docker bridge-gateway IP; a connection addressed to it can never land on a `127.0.0.1`-bound socket (kernel refusal — **connection refused**, not 403 — before any middleware runs). The apps must stay loopback-bound, so the launcher bridges the last hop itself.

**Launcher-owned per-run relay (PROPOSED — the recommended path).** When a run's config sets `outputs.grafana_bridge: true`, the launcher starts **one relay per scraped service**:

```bash
socat "TCP-LISTEN:${port},bind=${GATEWAY_IP},fork,reuseaddr" "TCP:127.0.0.1:${port}"
```

- The gateway IP is discovered at launch: `docker network inspect` of the monitoring network's gateway, falling back to the default-bridge gateway.
- Each relay's pid is recorded in `$RUN_DIR/relays/` and killed at teardown (§6.2).
- The apps stay loopback-bound — cascor's non-loopback bind attestation guard (`src/api/settings.py:143-161`) is never tripped.
- The app-side `MetricsAuthMiddleware` sees the **relay's loopback source address**, so **no allowlist changes are needed** (`metrics_auth.py:49` loopback defaults suffice).
- `socat` becomes a preflight-checked dependency (P0.11, §10.1).
- Prometheus-side target files keep pointing at `host.docker.internal:<port>` (§7.2). The PROPOSED `extra_hosts` entry must map it to that gateway IP **explicitly** (`"host.docker.internal:<monitoring-gateway>"`): the `host-gateway` *keyword* resolves to the default-bridge gateway (172.17.0.1), not the monitoring network's — the 2026-07-30 P0 evidence run proved the explicit-IP form end-to-end (F-2).

**Alternatives considered.** *(b)* Binding the services to the gateway IP / `0.0.0.0` plus attestation env flags — rejected: it weakens the loopback security posture and deliberately trips cascor's bind guard (`src/api/settings.py:143-161`). *(c)* A host-network-mode Prometheus — rejected: it breaks the existing container-DNS scrapes of the dockerized services.

**Prerequisite toggles (must be set, else Grafana shows nothing):**

| Toggle                                       | Required value                                               | Default                                                     | Cite                                             |
|----------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------------|--------------------------------------------------|
| `JUNIPER_CASCOR_METRICS_ENABLED`             | `true`                                                       | **`false`**                                                 | `juniper-cascor/src/api/settings.py:373`         |
| `JUNIPER_RECURRENCE_METRICS_ENABLED`         | `true`                                                       | `true` (already)                                            | `juniper_recurrence/settings.py:81`              |
| recurrence `[observability]` extra installed | required                                                     | present in `JuniperCascor1` (`juniper_observability` 0.4.0) | `juniper_recurrence/app.py:107-117`              |
| `JUNIPER_DATA_METRICS_ENABLED`               | `true`                                                       | disabled by default                                         | `juniper-data/juniper_data/api/settings.py:171`  |
| metrics allowlists                           | **no change** — the relay presents a loopback source address | loopback already trusted everywhere                         | `metrics_auth.py:49`; `.env.observability:56-64` |

`OPEN QUESTION Q-4` — re-scoped by validation (it is **not** an allowlist question): validate gateway-IP discovery + relay reachability end-to-end. **Answered empirically by P0.10** (run per step 0.2b against a hand-applied, uncommitted copy of the §7 overlay): the expected failure signature *without* the relay is connection-refused; success is the `juniper-host-experiments` targets turning `up == 1` in Prometheus.
**ANSWERED 2026-07-30** — executed exactly as specified: control arm `dial tcp 172.31.0.1:<port>: connect: connection refused`, relay arm `up == 1` (2/2) with run-scoped labels flowing into PromQL; see [the P0 preflight evidence](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md).

### 7.4 New dashboards (PROPOSED, juniper-deploy)

| Dashboard | Contents | Constraints |
| --- | --- | --- |
| `grafana/provisioning/dashboards/juniper-recurrence.json` | RED row from the generic `juniper_http_*` families scoped by the `service` label (as-built; no `namespace` kwarg, `app.py:118`; deploy#166); rates of the 3 `juniper_recurrence_*_total` counters; `_train_last_metric` / `_crossval_last_metric` gauges; both `_last_duration_seconds` gauges; a `juniper_recurrence_build_info` table | unique integer panel ids; top-level `id: null` (`juniper-deploy/tests/test_grafana_dashboard_ids.py:33-45,54-60`) |
| `grafana/provisioning/dashboards/juniper-experiments.json` | Templated on a `run_id` variable (`label_values(run_id)` filtered to `environment="host-experiment"`); a cascor training-progress row (the `juniper_cascor_training_*` families plus `_hidden_units_total`, `_candidate_correlation`, step-duration p50/p95); a recurrence row; a run-inventory table | same id invariants; must degrade gracefully to "No data" when no experiment is running |

Both land in the provisioning dir and appear in the "Juniper" folder within 30 s (`dashboard-providers.yml:5-15`) — no Grafana restart.

`OPEN QUESTION Q-5`: should `juniper-experiments.json` be provisioned permanently, or generated per-run through the Grafana HTTP API? Provisioned-and-templated is simpler, survives restarts, and needs no Grafana credentials in the driver. Recommendation: provisioned + templated.

---

## 8. End-of-Run Plots & Reports (design)

### 8.1 cascor plot set

Reuse the existing plotter — `CascadeCorrelationPlotter.plot_dataset` (`juniper-cascor/src/cascor_plotter/cascor_plotter.py:76`), `.plot_decision_boundary` (`:128`), `.plot_training_history` (`:197`) — for **direct-CLI** runs, where `SpiralProblem`'s `generate_plots` flag already drives it (`src/spiral_problem/spiral_problem.py:134,349`). For **service** runs the plotter lives in a different process from the model, so the driver plots **client-side** from JSON/array payloads:

| Plot | Data source | Applicability |
| --- | --- | --- |
| `dataset.png` — scatter coloured by class, train/test split marked | the NPZ fetched from juniper-data (`X_full`/`y_full`) | any 2-feature classification generator |
| `decision_boundary.png` — prediction grid + overlaid samples | `GET /v1/decision-boundary?resolution=R` (`src/api/routes/decision_boundary.py:20`) | **2-D input only** — the route documents "Requires a network with 2D input"; mnist/arc_agi/equities are excluded |
| `training_history.png` — loss + accuracy vs epoch, hidden-unit-insertion markers | `GET /v1/metrics/history?count=N` (`src/api/routes/metrics.py:26`) | all runs |
| `candidate_correlation.png` — best candidate correlation per growth round | the driver's poll-loop `metrics_series.csv` (§6.3), sampled from the app's own loopback `/metrics` gauge `juniper_cascor_candidate_correlation` — `/v1/metrics/history` rows carry **no** correlation field (it otherwise surfaces only in the WS `cascade_add` event) | all runs |
| `eval_metrics.png` — F1 / precision / recall / ROC-AUC bars | `/v1/metrics` scalar eval block, gated by `JUNIPER_CASCOR_EVAL_METRICS_ENABLED` (`src/api/lifecycle/manager.py:32-39`) | classification runs |
| `topology.txt` / `topology.json` — final network structure | `GET /v1/network/topology` (`src/api/routes/network.py:55`) | all runs |

**PROPOSED work item**: extract the boundary/history rendering so the driver can reuse cascor's plotting *style* without importing cascor (the plotter imports `torch`, `cascor_plotter.py:41`, which would drag the whole app into the driver's process). Cleanest split — the driver owns the matplotlib code for service runs; `CascadeCorrelationPlotter` stays the direct-CLI path. Duplication is real but small, and the alternative (importing cascor internals into the driver) breaks the driver's env-independence.

### 8.2 recurrence plot set (entirely new — G-5)

| Plot                                                                                          | Data source                                                                                                                                              |
|-----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `dataset_overview.png` — a few sampled windows of `X` with the target marked                  | fetched NPZ — `X_{split}` plus the target key: `y_{split}` for the synthetics (`irregular_sine`, `multi_sine`, `mackey_glass`, `delay_product`, `ar_p`), |
|                                                                                               |   `y_reg_{split}` for `equities_seq` only (or normalize via the data-client contract helper)                                                             |
| `dt_histogram.png` — distribution of per-step Δt plus `target_dt`; the irregularity signature | `dt_{split}` `(W,L)` and `target_dt_{split}` `(W,)` (`juniper-data/juniper_data/generators/_sequence.py:203-207,291-295`)                                |
| `forecast_vs_truth.png` — predicted vs actual over the held-out window index                  | `POST /v1/predict` response vs the test-split target (`y_test` for the synthetics, `y_reg_test` for `equities_seq`)                                      |
| `residuals.png` — residual series + histogram + optional residual-vs-`target_dt` scatter      | same                                                                                                                                                     |
| `crossval_folds.png` — per-fold r²/MSE bars with the aggregate line                           | `CrossValResponse` folds (`schemas.py:248-266`)                                                                                                          |
| `metrics_table.png` / `stats.json`                                                            | final + CV metrics                                                                                                                                       |

**Why there is no training-history plot in this set**: it is API-infeasible today — `TrainResponse` exposes only `final_metrics` / `n_epochs` / `stopped_reason` (`schemas.py:145`), no per-epoch series. Revisit if WS-8 or an mlp-readout history endpoint lands; until then the CV-fold bars are the interim training-performance surface.

### 8.3 Statistics summary (both apps)

`artifacts/results/stats.json` plus a human-readable `summary.md`:

- **Identity**: `run_id`, experiment name, config SHA-256, git SHAs of every participating repo, package versions, seeds.
- **Dataset**: `dataset_id` (content-addressed, `juniper-data/juniper_data/core/dataset_id.py:23`), generator + version, params, resolved shapes (`n_windows`/`lookback`/`n_features` for 3-D; `n_train`/`n_test`/`n_features`/`n_classes` for 2-D), class balance or target summary stats.
- **Outcome**: terminal state, wall-clock, and per-phase timings.
- **cascor**: final loss/accuracy (train + test), F1/precision/recall/ROC-AUC when eval metrics are on, hidden units added, epochs per growth round, best candidate correlation per round and `training_step_duration` p50/p95 — both from the driver's poll-loop `metrics_series.csv` (§6.3; neither exists in the `/v1/metrics/history` rows).
- **recurrence**: `final_metrics` from `TrainResponse` (`schemas.py:148`), `n_epochs`, `stopped_reason`, per-fold and aggregate CV metrics, resolved θ (data-driven when `theta: null`, `juniper-recurrence-model/juniper_recurrence_model/model.py:172-179`), readout rung and its hyperparameters.
- **Provenance/health**: whether metrics were scraped (target file written and Prometheus reported the target `up`), and any degraded-mode notes (e.g. eval metrics disabled, `[observability]` extra absent).

---

## 9. Concurrency & Data-Safety (design)

### 9.1 Hazard → mitigation table

| ID | Hazard | Evidence | Mitigation |
| --- | --- | --- | --- |
| **H-1** | Two runs bind the same port; cascor and recurrence both have fixed defaults (8200 / 8210). | `juniper-cascor/src/api/settings.py:133`; `juniper_recurrence/settings.py:47` | Per-run allocation from the dedicated ranges in §9.3 (lockdir + `ss` probe), never the defaults. |
| |                                                                                            |                                                                               | The lockdir serialises experiment launchers against each other; the residual race vs non-participating processes is detected by the service's own bind failure, which the health gate surfaces. |

| **H-2** | An experiment recurrence on `8210` collides with the operator stack's worker health listener. | `juniper-ml/util/juniper_plant_all.bash:183` | Experiment recurrence range starts at **8260**; `8210`/`8211` are never used by this program. |
| **H-3** | Shared `.env` cross-talk: cascor loads `.env` from CWD via pydantic-settings and `load_dotenv()`. | `src/api/settings.py:126`; `src/main.py:172` | **Process env only.** The launcher never creates, edits, or deletes any `.env`. Per-run values are exported into the child process. |
| **H-4** | cascor **service** snapshots use a hard-coded `<repo>/src/snapshots/` with no env override; the collision-suffix check is existence-then-write — a cross-process TOCTOU. | `manager.py:4300-4304`, ID logic `:4305-4323` | **PROPOSED setting `JUNIPER_CASCOR_SNAPSHOTS_DIR`** (W-6) so each run writes to `RUN_DIR/snapshots/`. **Interim rule: one cascor instance per checkout** — a second run needs a second worktree, enforced by a per-checkout lockdir (refuse, exit 1). |
| **H-5** | cascor **direct-CLI** snapshots share `<repo>/src/cascor_snapshots/`. | `src/cascor_constants/constants_hdf5/constants_hdf5.py:45-46` | Same interim per-checkout lock; W-6 covers this dir too. |
| **H-6** | recurrence `bench/` writes a fixed `bench/results/` — concurrent bench runs in one checkout clobber each other's JSON and `REPORT.md`. | `bench/run_benchmark.py:29` | **PROPOSED `--results-dir` flag** on `bench.run_benchmark` (W-7); until then, one bench run per checkout, enforced by the same lock. |
| **H-7** | Shared `logs/juniper_cascor.log` — interleaved writes and rotation-under-write across instances. | `src/cascor_constants/constants.py:418,460-461` | Launcher redirects each service's stdout/stderr to `RUN_DIR/logs/<svc>.log`. The app's own file logger still targets repo `logs/`; **accepted residual risk** under the one-instance-per-checkout rule — *conditional on that rule*: lifting it (Wave 5.3) requires resolving `OPEN QUESTION Q-6`: is a `JUNIPER_CASCOR_LOG_DIR` override worth a work item? |
| **H-8** | Shared juniper-data storage: a `name`-based ref can resolve to a *newer* version created by a concurrent run. | `create_dataset(..., persist=True)` (`manager.py:3360`); `get_latest(name)` (`data.py:40`) | **Dedicated per-run data instance by default** (`JUNIPER_DATA_STORAGE_PATH=$RUN_DIR/data`), reaped with the run; datasets addressed by `dataset_id` or `generator+params`, **never bare `name`**. Shared-instance fallback: `ttl_seconds` + run-scoped `tags` (`client.py:421-422`). |

| **H-9** | Shared equities cache across processes. | `JUNIPER_DATA_EQUITIES_CACHE_DIR`, default `~/.cache/juniper_data/equities` (`juniper-data/juniper_data/generators/equities/generator.py:83`) | Point it at `$RUN_DIR/equities-cache` per data instance. Trade-off: repeated network fetches. `--shared-equities-cache` opt-in for iterating on equities experiments (read-mostly, so low risk). |
| **H-10** | `JuniperProject.pid` clobber / cross-session reaping: `plant` truncates it, `chop` can kill another session's services. | `plant:84-85,515-523`; `chop:285-299` | The experiment stack **never touches** `JuniperProject.pid`. It keeps per-run pidfiles in `RUN_DIR` and tears down only pids it recorded. |
| **H-11** | CPU oversubscription: the candidate pool is sized from `sched_getaffinity` unless overridden; the direct CLI sets BLAS threads to 2 but the **server path does not**. | `cascade_correlation.py:2281-2299`; `src/main.py:48-50` | Launcher exports `OMP/MKL/OPENBLAS_NUM_THREADS` + `CASCOR_NUM_PROCESSES` from the YAML `runtime:` block, defaulting to a **budget split** (`max(1, floor(nproc / (2 * max_runs)))`, BLAS = 2) recorded in the manifest, so timings are compared only across equal budgets. |
| **H-12** | Orphaned forkserver/multiprocessing children survive a hard kill. | reaper precedent `juniper-ml/util/reap_pytest_orphans.bash` | Teardown kills the recorded pid, waits, then re-probes the port; the run report flags any surviving listener. Operators use the existing reaper for orphan cleanup; the launcher never blanket-kills by name. |
| **H-13** | cascor could spawn companion services and race the fixed data port. | `JUNIPER_CASCOR_AUTO_START_DATA_SERVICE` / `_CANOPY` (`settings.py:429,431`), launcher `src/api/service_launcher.py` | Both pinned `false` in every launch line, and asserted `false` in P0 pre-flight. Also the mechanical guarantee that **no canopy process is ever started** by this program. |
| **H-14** | Prometheus target-file collision between runs. | §7.2 | One file per `RUN_ID` (`$RUN_ID.json`), written on `--up`, removed on `--down`; a leftover file from a crashed run yields a `down` target — a visible, self-healing signal rather than silent corruption. |
| **H-15** | Results lost to sandbox/session reaping. | juniper-ml convention: `/tmp/` is prohibited for anything that must survive | `RUN_DIR` lives under `$HOME/.local/state/juniper-experiments` by default — **not** `/tmp` (a deliberate departure from `isolated_stack.bash:67`). Only ephemeral port lockdirs live under `$XDG_RUNTIME_DIR`. |

> **Update (2026-08-16) — H-7's "accepted residual risk" is retired; Q-6 shipped.**
> `JUNIPER_CASCOR_LOG_DIR` now overrides the shared `logs/juniper_cascor.log` in both tiers
> (cascor#523, merged `3909d275`), and `util/experiment_stack.bash` exports it per run, so each run's
> app-level log lands in `RUN_DIR/logs/`. **The row's risk statement understated it**: interleaving was
> never the real hazard. cascor's parent logger writes *only* to that file, so a second process
> **rotates the evidence away** rather than merely interleaving it — one other process is enough, and
> the one-instance-per-checkout rule never protected a run from a long-lived service sharing its
> checkout. That is how the F-P1-3 arm A/B logs were lost. Full closure record: §15.2 Q-6.
> Wave 5.3 remains only **partly** unblocked (`run_suite.py:112`; see the Wave 5 table).

### 9.2 Concurrency invariants (the short version)

1. One `RUN_DIR` per run; nothing outside it is written except the Prometheus target file, the port lockdirs, and the append-only global run registry `${JUNIPER_EXP_RUN_ROOT}/index.jsonl` (§13.3).
2. Ports are allocated atomically, from disjoint per-app ranges, and released on teardown.
3. All per-run configuration travels as process env or the `--config` YAML — never through a shared file.
4. At most one cascor instance and one bench run per checkout, until W-6 / W-7 land.
5. Datasets are addressed by `dataset_id` or `generator+params`, never by bare `name`.
6. Teardown kills only pids this run recorded.

### 9.3 Port-range policy (PROPOSED)

| Range       | Purpose                                 | Avoids                                                                                                                                    |
|-------------|-----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `8110-8139` | experiment juniper-data instances       | operator `8100` (`plant:111`), E2E `8101` (`isolated_stack.bash:58`)                                                                      |
| `8230-8259` | experiment juniper-cascor instances     | cascor default `8200` (`settings.py:133`), operator `8201` (`plant:125`), E2E `8202` (`isolated_stack.bash:59`)                           |
| `8260-8289` | experiment juniper-recurrence instances | recurrence default `8210` and deploy host `8211` (`settings.py:47`; `docker-compose.yml:535`), **and worker health `8210`** (`plant:183`) |
| never used  | `8050` / `8051` (canopy)                | canopy is out of scope — the ranges deliberately leave its ports untouched                                                                |

Thirty ports per app bounds concurrent runs at 30, far above any realistic session count, and every range is contiguous and documented so an operator can `ss -tlnH 'sport >= :8110 and sport <= :8289'` to see all experiment listeners at once.

---

## 10. Test & Validation Program

Five phases. Each is independently runnable; each names its exact commands, acceptance criteria, and the evidence to file under the run's `artifacts/`.

### 10.1 P0 — Preflight (environment and plumbing truth)

| Step | Command / check | Acceptance |
| --- | --- | --- |
| P0.1 | `ls /opt/miniforge3/envs/` | `JuniperCascor1`, `JuniperData` present; the `-DEPRECATED` envs are not used |
| P0.2 | `/opt/miniforge3/envs/JuniperCascor1/bin/python -c "import juniper_cascor, juniper_recurrence, torch, matplotlib, yaml"` | all import; record versions |
| P0.3 | `/opt/miniforge3/envs/JuniperData/bin/python -c "import juniper_data, uvicorn, matplotlib, yaml, numpy, requests"` | all import (also settles the §6.3 driver-dependency claim for this env) |
| P0.4 | `python util/editable_install_drift_check.py` and `python util/env_floor_drift_check.py --env JuniperCascor1 --env JuniperData` (juniper-ml; the bare floor-check invocation exits 2 from juniper-ml — no conda env maps to it in `ecosystem.yaml`) | no `ORPHANED`, no `BELOW_FLOOR` for the participating packages |
| P0.5 | Launch a data instance on 8110; `curl /v1/generators` | 15 of 16 `available: true`; `mnist` `false` (expected on this host, G-16) |
| P0.6 | Launch cascor on 8230 with `JUNIPER_CASCOR_METRICS_ENABLED=true`; `curl -sf /metrics` | non-empty exposition; `juniper_cascor_build_info` present |
| P0.7 | Same with the flag unset | `/metrics` **404s** — confirms G-3 is a real trap, not folklore |
| P0.8 | Launch recurrence on 8260; time to first successful `/v1/health/ready` | binds within the health timeout; record the actual seconds (expect 10-15 s) |
| P0.9 | `make obs` in juniper-deploy; `curl -s localhost:9090/api/v1/targets` | the five container jobs are visible (baseline before any change) |
| **P0.10** | Against a **hand-applied, uncommitted** copy of the §7 compose/prometheus overlay (step 0.2b): write a target file, start the §7.3 relay, wait `refresh_interval`, re-query `/api/v1/targets` | the `juniper-host-experiments` targets turn **`up == 1`**. Control arm: without the relay, `lastError` shows **connection refused** (a gateway-addressed scrape can never land on a loopback bind). Answers Q-4 empirically; this evidence gates merging Wave 1.1. |
| P0.11 | `docker network inspect` the monitoring/backend networks; `command -v socat` | record the gateway IP the §7.3 relays will bind; `socat` present (relay dependency) |
| P0.12 | per sub-range, before starting: `ss -tlnH 'sport >= :8110 and sport <= :8139'` (data), the same for `:8230`-`:8259` (cascor) and `:8260`-`:8289` (recurrence) | all three sub-ranges empty — the naive full 8110-8289 span also catches unrelated ambient listeners (e.g. the operator cascor on 8200) and must not be the acceptance check |

**Evidence**: filed 2026-07-30 as [`JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md`](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md) — every command's output, the recurrence bind latency, the Prometheus targets JSON for both P0.10 arms, and the resolved gateway IPs.

### 10.2 P1 — Smoke (one minimal run per app, per launch mode)

| Step | Run                                                                                      | Acceptance                                                                                                                                  |
|------|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| P1.1 | cascor **service**: spiral, `max_hidden_units: 2`, `max_iterations: 2`, `max_epochs: 50` | FSM reaches `COMPLETED`; `/v1/metrics/history` non-empty; three plots written; `manifest.json` valid                                        |
| P1.2 | cascor **direct CLI**: `python main.py` against the run's data instance                  | exit 0; plots under the CLI's own output path; exit 3 / exit 4 arms verified by unsetting `JUNIPER_DATA_URL` and by pointing at a dead port |
| P1.3 | recurrence **service**: `irregular_sine`, `d: 8`, `n_steps: 500`, `readout: linear`      | `POST /v1/train` 200 with `final_metrics`; `/v1/predict` 200; `/v1/crossval` (`n_folds: 2`) 200; five plots written                         |
| P1.4 | recurrence **train CLI**: same dataset, `--out model.npz`                                | exit 0; metrics printed; `.npz` written and loadable                                                                                        |
| P1.5 | `--dry-run` for every launcher invocation above                                          | nothing created, started, or killed; no target file; run-root unchanged                                                                     |
| P1.6 | Grafana: open the experiments dashboard during P1.1 and P1.3                             | live series for both `run_id`s; panels render (no "No data")                                                                                |
| P1.7 | Teardown                                                                                 | ports free (`ss` empty for the range), pidfiles gone, target file removed, no orphan python under the run's pids                            |

### 10.3 P2 — Dataset-matrix functional coverage

Run the smallest meaningful configuration for every compatible dataset, per app, in **both** launch modes where applicable.

**cascor matrix** (2-D classification; decision boundary requires 2 input features):

| Dataset | Generator + key params | Boundary plot? | Status / prerequisite |
| --- | --- | --- | --- |
| `spiral` | `n_spirals=2, n_points_per_spiral=500, n_rotations=3, noise=0.05, seed` | Yes | Ready. Staged Literal `"spirals"` (`models/training.py:188`) aliases to `spiral` (`manager.py:3251`); also the only generator the in-process fallback handles (`routes/training.py:75`) |
| `xor` | `n_points_per_quadrant=250, noise=0.05, margin, seed` | Yes | Ready via staging |
| `circles` | `n_samples=1000, outer_radius, factor, noise` | Yes | Ready via staging (`"circles"` in the Literal) |
| `moon` | `n_samples=1000, noise=0.1, seed` | Yes | Ready via staging (`"moons"` → `moon`, `manager.py:3251`) |
| `gaussian` | `n_classes=3, n_samples_per_class=300, n_features=2, class_std, seed` | Yes (only with `n_features=2`) | **Needs W-3**: absent from the staged Literal (`models/training.py:188`); reachable today only as an untyped passthrough |
| `checkerboard` | `n_samples=2000, n_squares=4, noise` | Yes | **Needs W-3**: absent from the staged Literal |
| `mnist` | `dataset=mnist, n_samples=2000, flatten=true, normalize=true` | **No** (F=784, `mnist/generator.py:125-126`) | **Needs W-4**: HF `datasets` absent on this host → `available=False` → 501 (`datasets.py:165-168`) |
| `equities` | `symbols=[…], start_date, end_date, normalize_features, max_symbols, seed` | **No** (F=10, `equities/generator.py:426`) | Ready on this host (`yfinance` 1.4.1 + `pandas` 3.0.3 present); needs network at generation time; rides the generic `params` dict (`models/training.py:200`) |
| `csv_import` | `file_path, feature_columns, label_column` | Depends on `len(feature_columns)` | Deferred — no experiment corpus defined yet (`OPEN QUESTION Q-7`; W-12 defines the corpus + params and adds this matrix row once Q-7 is answered) |
| `arc_agi` | `source, n_tasks, pad_to, flatten_pairs` | **No** | Deferred — grid-pair task, not a cascade-correlation target for this program |

**recurrence matrix** (3-D sequence regression):

| Dataset | Δt character | Key params | Status / prerequisite |
| --- | --- | --- | --- |
| `multi_sine` | regular | `n_steps, lookback, horizon, sample_dt, n_components, noise_std, seed` | Ready; a `PRIMARY_DATASETS` member (`bench/datasets.py:236`) |
| `mackey_glass` | regular, chaotic | `+ tau, beta, gamma, n_exp, discard` | Ready; primary |
| `irregular_sine` | genuinely non-uniform | `+ jitter, n_components, noise_std` | Ready; primary; the known-answer irregular case |
| `delay_product` | non-uniform + bilinear target | `+ jitter, lag1, lag2, n_components, noise_std` | Ready to run; **needs W-8** to commit a baseline result (no `bench/results/delay_product.json`) |
| `ar_p` | regular, linear-stochastic | `+ coefficients, const, sigma, burn_in` | **Needs W-5**: implemented in juniper-data (`generators.py:137`) but absent from `bench/datasets.py:244-262`; reachable now only via service `generator+params` or `train --generator ar_p` |
| `equities_seq` | irregular calendar-day Δt | inherits `EquitiesParams` + `lookback` (default 64) | Ready on this host; needs network; the only real-data irregular-Δt source |

**Per-dataset acceptance**: the run completes; the NPZ passes `validate_npz_contract` (returns `"tabular"` for cascor, `"sequence"` for recurrence — `juniper-data-client/juniper_data_client/contract.py:41`); every plot in the dataset's applicable set is written and non-degenerate (non-empty, finite axes); metrics land in Prometheus with the run's labels; `manifest.json` records `dataset_id`, resolved shapes, and seeds.

**Anti-silence check (G-6).** For every non-`spiral` cascor dataset, the driver must additionally assert that the loaded dataset actually changed — comparing `GET /v1/network` input/output dims and the dataset descriptor in `GET /v1/training/status` against the requested generator's expected shape. A run that "succeeds" while training on stale data is the exact failure `routes/training.py:75` invites.

### 10.4 P3 — Acceptance / validation criteria

| Class | Criterion |
| --- | --- |
| **Correctness (cascor)** | Spiral baseline reaches test accuracy ≥ the value recorded in the P1 reference run, within tolerance; hidden units added ≤ `max_hidden_units`; the decision-boundary grid separates classes visibly. Separability sanity: `xor` and `circles` must exceed majority-class accuracy by a clear margin. |
| **Correctness (recurrence)** | The ratified OQ-14 bands in the evaluation-design doc (§17.1), as implemented by `bench/run_benchmark.py:134-257` `evaluate_bands`, remain the scoring authority for the three `PRIMARY_DATASETS`. Service-mode runs must land inside the same bands as the offline bench for identical params — a divergence is a **service-path defect**, not a new result. Further context: the findings doc (§17.1) §3.2. |
| **Readout spectrum** | For `delay_product`, `readout: rff` must beat `readout: linear` on r², per [`JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md`](JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md). If it does not, that is a finding to record — not a threshold to tune away. |
| **Reproducibility** | Two runs of the same YAML on the same SHAs produce the same `dataset_id` and metrics equal within a documented tolerance. Any residual nondeterminism (multiprocessing candidate order, BLAS reductions) is characterised, not hidden. |
| **Config precedence** | Empirically proven in all four directions: CLI flag beats YAML; YAML beats an exported env var; env beats `.env`; absent keys fall back to constants. Each arm is a named test (§10.6). |
| **Observability** | Every completed run appears in Prometheus under its `run_id`, and the experiments dashboard renders it. `up == 1` for the run's targets throughout. |
| **Artifacts** | Every run dir contains a valid `manifest.json`, the config copy, the full plot set for its dataset, `stats.json`, and `summary.md`. |
| **Isolation** | Two runs launched within seconds of each other complete independently: distinct ports, distinct run dirs, distinct `dataset_id`s where params differ, no interleaved artifacts, both visible in Grafana. |
| **Cleanliness** | After teardown: no listeners in the experiment ranges, no target files, no orphan processes, `JuniperProject.pid` byte-identical to before the run (proving H-10 holds). |

### 10.5 P4 — Experimentation runs (the point of all of this)

| Study                               | Shape                                                                                  | Output                                                                  |
|-------------------------------------|----------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| **E-A cascor cascade budget**       | Sweep `max_hidden_units ∈ {4,8,16,32}` × `candidate_pool_size ∈ {4,8,16}` on spiral    | accuracy / units / wall-clock surface; boundary plots per cell          |
| **E-B cascor dataset difficulty**   | Fixed budget across spiral / xor / circles / moon / gaussian / checkerboard            | difficulty ranking with boundary plots; feeds the perf scenarios in §12 |
| **E-C cascor noise robustness**     | `noise ∈ {0.0, 0.05, 0.1, 0.2}` on spiral and moon                                     | accuracy-vs-noise curve                                                 |
| **E-D recurrence d-sweep**          | `d ∈ {8,16,32}` (mirrors `_D_GRID`, `bench/run_benchmark.py:31`) × the three primaries | r²-vs-d curves; direct comparability to the committed bench results     |
| **E-E recurrence readout spectrum** | `readout ∈ {linear, rff, mlp}` on `delay_product` and `irregular_sine`                 | capacity separation; the DP-3 claim, reproducibly                       |
| **E-F recurrence irregularity**     | `jitter ∈ {0.0, 0.1, 0.3, 0.5}` on `irregular_sine`                                    | Δt-native advantage vs jitter                                           |
| **E-G recurrence CV scheme**        | `scheme ∈ {expanding, rolling}` × `embargo ∈ {0,2,5}`                                  | CV-stability comparison                                                 |
| **E-H real data**                   | `equities` (cascor) and `equities_seq` (recurrence)                                    | the efficient-market-ceiling sanity check the findings doc predicts     |

Each study is a **suite** in the §13 sense; P4 is where §13's automation earns its place. Until `run_suite.py` exists, each cell is a separate `run_experiment.py` invocation driven by a shell loop, sequentially.

**Acceptance / evidence**: each suite cell inherits P2's per-dataset acceptance criteria (§10.3) unchanged; suite-level evidence is `SUITE_DIR/REPORT.md` plus `aggregate.csv`, filed with the run artifacts.

### 10.6 Regression tests for the new tooling (juniper-ml)

Following the repo's established gate pattern (`util/` is not lint-gated, so a unittest **is** the gate):

| Test (PROPOSED) | Covers |
| --- | --- |
| `tests/test_experiment_stack_script.py` | `bash -n`; launch-line text assertions (metrics flags present, `LD_LIBRARY_PATH=''`, no canopy anywhere, no `JuniperProject.pid` reference); `--dry-run` creates/starts/kills nothing; misuse exit 2; port-allocation lockdir logic with a fake `ss`; relay pids started/killed only when `outputs.grafana_bridge` is enabled; teardown kills only recorded pids. Modeled on `tests/test_isolated_stack_script.py`. |
| `tests/test_run_experiment.py` | YAML validation (unknown key → error, missing `seed` → error, bad `schema_version` → error); precedence resolution; cascor and recurrence drive loops against a stub HTTP server (completion, `FAILED`, stall, timeout); manifest schema; plot files produced from synthetic payloads; exit-code matrix. |
| `tests/test_experiment_config_schemas.py` | Every key in every shipped `conf/experiments/*.yaml` maps to a real field in the target app's model — a drift gate that bites when cascor or recurrence renames a setting. |
| juniper-deploy `tests/test_grafana_dashboard_ids.py` | Already exists and automatically covers both new dashboards (it globs the provisioning dir, `tests/test_grafana_dashboard_ids.py:23`). |
| juniper-deploy `tests/test_prometheus_host_sd.py` (PROPOSED) | The `juniper-host-experiments` job exists, uses `file_sd_configs`, keeps `honor_labels: false`, and the `extra_hosts` gateway mapping is present on the prometheus service. |

---

## 11. Dataset Enablement Work Items

This table is the W-item register. W-11 and W-12 (added by the validation pass) extend it slightly beyond dataset enablement proper so that every W-item lives in exactly one table.

| ID | Work item | Repo | Size | Detail |
| --- | --- | --- | --- | --- |
| **W-1** | Fix the silent non-spiral dataset drop on `POST /v1/training/start` | juniper-cascor | M | `routes/training.py:75` handles only `generator == "spiral"`; every other value is ignored with no error. Either route non-spiral generators through the same juniper-data fetch path `_reload_dataset` uses (`manager.py:3356-3362`) or **reject** them with a 422 naming the staging endpoint. Silent-wrong-data is the worst of the three options. |
| **W-2** | Add typed sequence support or an explicit rejection for 3-D datasets in cascor | juniper-cascor | M | cascor's staged Literal has no sequence generators, and its NPZ path assumes 2-D tensors (`manager.py:3367-3377`). The 3-D ingestion boundary is already designed — see [`JUNIPER_2026-06-14_JUNIPER-RECURRENCE_RECURSE-OQ4-CASCOR-3D-INGESTION-GATE.md`](JUNIPER_2026-06-14_JUNIPER-RECURRENCE_RECURSE-OQ4-CASCOR-3D-INGESTION-GATE.md). Minimum viable: a clear error naming the tier boundary. |
| **W-3** | Extend the staged `dataset_type` Literal to `gaussian` + `checkerboard` (with typed params) | juniper-cascor | S | `models/training.py:188`; `manager.py:3289-3292` already routes "circles / moon / mnist / gaussian" through the `n_samples`-direct branch, so the translation exists — only the Literal and the typed fields are missing. `checkerboard` additionally needs `n_squares`. |
| **W-4** | Make `mnist` availability explicit and actionable | juniper-data / env | S | `mnist` reports `available=False` on this host. Either install HF `datasets` into `JuniperData`, or have the driver's §5.6 rule 4 pre-flight surface the install hint before the run starts. Prefer the pre-flight (no env mutation) plus a documented opt-in install. |
| **W-5** | Register `ar_p` in the recurrence bench registry | juniper-recurrence | S | Add an `ar_p` factory to `bench/datasets.py` alongside `multi_sine` (`:91-114`) and register it in `DATASETS` (`:244-262`). It stays out of `PRIMARY_DATASETS` (the ratified bands are pre-registered for three datasets only, `:236`). |
| **W-6** | `JUNIPER_CASCOR_SNAPSHOTS_DIR` setting | juniper-cascor | M | `manager.py:4300-4304` hard-codes `<repo>/src/snapshots/`; `constants_hdf5.py:45-46` hard-codes `<repo>/src/cascor_snapshots/`. Add a settings field (default = today's path, so no behaviour change) honoured by both the service and the direct CLI. Unblocks concurrent cascor runs in one checkout (H-4/H-5). |
| **W-7** | `--results-dir` for `bench.run_benchmark` | juniper-recurrence | S | `bench/run_benchmark.py:29` pins `_RESULTS`. A flag (default unchanged) unblocks concurrent bench runs (H-6). |
| **W-8** | Commit a `delay_product` bench baseline | juniper-recurrence | S | Run the harness and commit `bench/results/delay_product.json` + the refreshed `REPORT.md`, so the DP-3 capacity claim has a reproducible in-repo artifact (G-9). |
| **W-9** | Add the 7 missing generator constants **and** derive the parity gate from the live registry | juniper-data-client | M | `constants.py:138-150` lacks `equities`, `equities_seq`, `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product`. Critically, `tests/test_generator_parity.py:27-39`'s `EXPECTED_SERVER_GENERATORS` is a stale hand-kept mirror, so the reverse assertion at `:72-76` passes vacuously. Derive it from juniper-data when importable (else skip). |
| **W-10** | Document the on-host generator-availability matrix | juniper-ml | S | Add a `docs/REFERENCE.md` subsection recording which generators are available in which env and what each gate needs, with the `generator_available()` probe as the one-liner to re-derive it. |
| **W-11** | Direct-CLI YAML mapping | juniper-cascor + juniper-recurrence | M | Closes the R4 gap: `--config` reaches only `Settings` — nothing routes the `training:`/`dataset:` (cascor) or `train:` (recurrence) blocks into the direct CLIs. cascor `src/main.py` gains a thin adapter building problem/training params from those blocks (`cascor_constants` fallback); recurrence `train` seeds its argparse defaults from `train:`. Wave 3; until it lands, full YAML coverage is service-tier only (Q-11). |
| **W-12** | `csv_import` corpus + matrix row | juniper-ml / juniper-data | S | Gated on Q-7: define the experiment corpus and its `file_path`/`feature_columns`/`label_column` params, then add the cascor dataset-matrix row (§10.3). Wave 5. |

---

## 12. Performance Testing, Benchmarking & Optimization — Design Beginning

**This section is a design start, not a final design.** It fixes the reuse decisions and the measurement contract; the scenario matrix and thresholds need a ratification pass of their own.
> **Update (2026-08-16) — §12 development is GATED, per owner direction.** The owner concurs that
> this lane is open engineering and requires **design → planning → verification → documentation
> before development begins**. The four phases, their exit criteria, and their **priority relative to
> every other outstanding and in-progress program item** are recorded in
> [§12 phasing and work prioritisation](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md).
>
> Two standing inputs are banked and do not decay: the **PF suites** (six suites / 31 cells, ml#1033)
> and the **E-B difficulty ranking**. **Q-8 is answered** — run-level baselines get a *dedicated, new
> directory* — and that answer is a **design-phase input** here (location, layout, retention, and
> writer are part of the design), not an implementation detail.
>
> Note this lane no longer has an F-P1-3b premise: that finding was withdrawn and then positively
> refuted. The lane stands on its own inputs. The trap that produced it is a design-phase hazard
> worth carrying: the driver's `outputs.max_wall_seconds`, not the suite's
> `per_run_timeout_seconds`, is what actually ends a run — **a timeout is not a measurement.**


### 12.1 Reuse, do not rebuild

| Asset | Reuse decision |
| --- | --- |
| cascor `src/tests/performance/` (10 modules) | The micro-benchmark and scaling layer. Invoked as `pytest tests/performance/ --run-performance -v` or with `CASCOR_BENCHMARK_MODE=1` (double gate at `src/tests/conftest.py:207,260-266`), or via `src/tests/run_tests.bash -p` (`:156`). |
| cascor `src/tests/performance/baselines/baseline_20260526.json` | The persisted-baseline mechanism and its regression tolerances stay authoritative for micro-level work. |
| cascor `--profile` / `--profile-memory` (`src/main.py:435-441`) + `src/profiling/{deterministic,memory}.py` | The deterministic and memory profiling entry points; the experiment stack points `--profile-output` at `$RUN_DIR/profiles`. |
| recurrence `bench/run_benchmark.py` | The model-level evaluation instrument (walk-forward CV, d-grid, ratified bands). Not to be reimplemented. |
| `juniper_cascor_training_step_duration_seconds` (Histogram, `src/api/observability.py:161-167`, registered `:285-290`) and `juniper_recurrence_{train,crossval}_last_duration_seconds` (`metrics.py:33-36`) | The already-exported timing series. Grafana panels read these; **no new metric families are needed for phase 1**. |
| Recording rules `juniper:http_request_duration_seconds:p50\|p95\|p99` (`juniper-deploy/prometheus/recording_rules.yml:31,40,49`) | Reused for request-level latency — **but** the existing expressions aggregate only the `juniper_{data,cascor,canopy}_http_request_duration_seconds_bucket` series; Wave 1.3 extends all three rules with the generic `juniper_http_request_duration_seconds_bucket` series — recurrence's as-built family (§7.4 correction) — so recurrence latency participates. |

### 12.2 What is genuinely missing

1. **Run-level durations are not a metric.** Total run wall-clock, per-phase timings, and epochs-per-second are computed by the driver but exist only in `stats.json`. Options: (a) driver-computed only — no app change, but invisible in Grafana; (b) a **PROPOSED** cascor Summary/Gauge for run duration; (c) rate panels derived from the existing `juniper_cascor_training_epochs_total` counter. **Recommendation: (c) first, (a) always, (b) only if a gap survives.**
2. **Recurrence has no `performance` marker and its bench exports no metrics** (G-17). Two sub-items: add a `performance` marker to the recurrence app's pytest config for future micro-benchmarks, and let the **driver** publish bench-equivalent timings via the service path (`/v1/train` already records `_train_last_duration_seconds`), so recurrence timings reach Grafana without touching the offline harness.
3. **No cross-app comparison surface.** A single Grafana row comparing cascor and recurrence run durations across `run_id`s is a small dashboard addition once §7 lands.

### 12.3 Scenario list (draft)

| ID   | Scenario                                                                                              | Instrument                                               | Primary metric                                                                                      |
|------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| PF-1 | cascor spiral, fixed budget, N repeats                                                                | driver + `training_step_duration` histogram              | p50/p95 step duration; total wall-clock                                                             |
| PF-2 | cascor dataset-size scaling (`n_points_per_spiral ∈ {250,500,1000,2000}`)                             | driver                                                   | wall-clock vs samples; memory RSS                                                                   |
| PF-3 | cascor candidate-pool scaling (`candidate_pool_size ∈ {2,4,8,16}` × `CASCOR_NUM_PROCESSES ∈ {1,2,4}`) | `tests/performance/test_concurrency_scaling.py` + driver | speedup curve; oversubscription onset                                                               |
| PF-4 | cascor micro-benchmarks (forward, candidate, correlation, output, autograd)                           | existing perf suite vs `baseline_20260526.json`          | per-op timings; regression %                                                                        |
| PF-5 | recurrence `d`-scaling (`d ∈ {8,16,32,64}`)                                                           | driver + `_train_last_duration_seconds`                  | fit time vs `d`; r² vs fit time                                                                     |
| PF-6 | recurrence dataset-size scaling (`n_steps ∈ {1000,4000,16000}`)                                       | driver                                                   | fit time vs windows                                                                                 |
| PF-7 | recurrence readout-rung cost (`linear` / `rff` / `mlp`)                                               | driver                                                   | fit time + r² per rung (the DP-3 cost/benefit)                                                      |
| PF-8 | two-run concurrency cost                                                                              | two simultaneous runs with pinned, equal thread budgets  | wall-clock inflation vs solo baseline — the empirical answer to "how many runs can this host take?" |

### 12.4 Baseline and regression policy (draft)

1. **Micro level**: cascor's existing baseline JSON + tolerances stay authoritative (`src/tests/performance/test_baselines.py:48-60`).
2. **Run level**: a baseline is a *set of run manifests* under a named tag (**storage location is `OPEN QUESTION Q-8`**). A regression is a statistically meaningful slowdown of the same YAML on the same hardware with the same thread budget — **never** a comparison across differing `runtime:` blocks, which is why H-11 records the budget in every manifest.
3. **Reporting**: report-only at first. No CI gate on run-level timings until variance is characterised on this host (a shared workstation, not a quiesced runner).
4. Existing perf alerts (`SlowDatasetGeneration`, `CascorTrainStepLatencyFastBurn/SlowBurn`, `juniper-deploy/prometheus/alert_rules.yml:207,697,766`) must be reviewed before host-experiment series start firing them. `OPEN QUESTION Q-9`: should experiment targets be excluded from alert rules (by `environment != "host-experiment"`) so an intentionally brutal benchmark does not page? Recommendation: **yes, exclude**, and add experiment-scoped alerts separately if wanted.

### 12.5 Optimization: sequencing only

Optimization work is explicitly gated behind measurement: PF-1 → PF-8 first, then bottleneck attribution from the profiling tooling (§12.1), then targeted changes with a micro-benchmark guard each. `JR-CAS-PERF-005`'s continuous-profiling ambition (Grafana Pyroscope) is noted as a possible later phase, not a commitment.

---

## 13. Multi-Run Experiment Automation — Design Beginning

**Design start.** Phase 1 is sequential and deliberately boring; parallelism is deferred until the concurrency mitigations (§9) are proven and W-6/W-7 have landed.

### 13.1 Suite manifest (PROPOSED)

A suite is a YAML file describing a **cross-product or an explicit list** over one or more base configs, meta-parameter overrides, and datasets:

```yaml
# PROPOSED: juniper-ml util/experiments/suites/cascor-budget-sweep.yaml
schema_version: 1
suite:
  name: cascor-budget-sweep
  description: "E-A: cascade budget × candidate pool on spiral"
  app: cascor                            # cascor | recurrence
  base_config:                           # one or more experiment configs; cells = configs × matrix
    - ../../../../juniper-cascor/conf/experiments/spiral-baseline.yaml
  seed_policy: fixed                     # fixed | per_cell (per_cell: seed = base_seed + index)
execution:
  mode: sequential                       # sequential | parallel (parallel = PHASE 2)
  max_parallel: 1
  continue_on_failure: true              # a failed cell must not abort the suite
  per_run_timeout_seconds: 3600
matrix:                                  # cross-product over override paths (dotted into the base config)
  training.params.max_hidden_units: [4, 8, 16, 32]
  training.params.candidate_pool_size: [4, 8, 16]
include:                                 # explicit extra cells appended to the product
  - name: wide-pool-long
    overrides:
      training.params.candidate_pool_size: 32
      training.params.max_epochs: 5000
exclude:                                 # cells to skip (cost control)
  - {training.params.max_hidden_units: 32, training.params.candidate_pool_size: 16}
outputs:
  suite_dir: null                        # null = ${JUNIPER_EXP_RUN_ROOT}/suites/<suite-id>
  aggregate: [csv, markdown, plots]
```

A recurrence suite is the same shape with `app: recurrence` and override paths into `train.*` / `crossval.*` / `dataset.params.*`, e.g. `train.d: [8,16,32]` × `train.readout: [linear, rff]`.

### 13.2 `util/experiments/run_suite.py` (PROPOSED)

```text
run_suite.py --suite SUITE.yaml [--dry-run] [--resume SUITE_ID] [--only CELL_ID ...] [--max-parallel N]
```

1. **Expand** `base_config` × the matrix into an ordered cell list (every listed config crossed with every override combination); assign each cell a deterministic `cell_id` (index + a hash of its config path and override set) so `--resume` and `--only` are stable across invocations.
2. **Materialise** each cell's fully-resolved experiment YAML into `SUITE_DIR/cells/<cell_id>/experiment.yaml` — every cell is independently re-runnable by `run_experiment.py` with no suite machinery.
3. **Execute** cells sequentially: allocate ports, `experiment_stack.bash --up`, `run_experiment.py`, `--down`. `continue_on_failure` records the failure and proceeds.
4. **Record** each cell's outcome into `SUITE_DIR/registry.jsonl` (append-only, one JSON per cell: `cell_id`, `run_id`, overrides, config hash, outcome, headline metrics, timings, artifact path).
5. **Aggregate** on completion: `SUITE_DIR/aggregate.csv` (one row per cell), `SUITE_DIR/REPORT.md` (ranked table plus sweep curves and heatmaps for 2-D matrices), and `SUITE_DIR/suite_manifest.json`.
6. **Resume** by reading `registry.jsonl` and skipping cells already terminal; `--dry-run` prints the expanded cell list and every command, writing nothing.

**Phase 2 (deferred)**: bounded parallelism via a worker pool of size `max_parallel`, each worker holding its own port allocation and run dir. Hard prerequisites: W-6 (per-run cascor snapshot dir) and the H-11 thread-budget split, since N parallel cascor runs each sizing a pool from `sched_getaffinity` would thrash the host.

### 13.3 Run registry

- **Per-suite**: `registry.jsonl` (append-only; crash-safe by construction).
- **Global**: `${JUNIPER_EXP_RUN_ROOT}/index.jsonl`, one line per run (suite or standalone), so `run_experiment.py` and `run_suite.py` share a single discovery surface.
- A companion `util/experiments/list_runs.py` (**PROPOSED**) lists / filters / prunes it with the same safety discipline as `util/generated_prompt_index.py` — destructive actions require explicit `--yes` and never act under `--dry-run`.

### 13.4 Reproducibility guarantees (the run manifest)

Every run — standalone or suite cell — writes `manifest.json` containing at minimum:

| Field                                                                                | Source                                                                                                                                                                                            |
|--------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `run_id`, `suite_id`, `cell_id`                                                      | launcher / suite driver                                                                                                                                                                           |
| `experiment.name`, `description`                                                     | the YAML                                                                                                                                                                                          |
| `config_sha256`                                                                      | SHA-256 of the resolved config bytes                                                                                                                                                              |
| `config_path`, `config_copy_path`                                                    | run dir                                                                                                                                                                                           |
| `dataset_id` + `generator` + `version` + `params`                                    | the `POST /v1/datasets` response; the id is **content-addressed** (`juniper-data/juniper_data/core/dataset_id.py:23`) and deterministic **only because the config mandates a seed** (§5.6 rule 3) |
| `git` — per repo: path, HEAD SHA, dirty flag                                         | `git -C <repo> rev-parse HEAD` / `status --porcelain` for cascor, recurrence, data, data-client, deploy, juniper-ml                                                                               |
| `packages` — name → version + editable-source path                                   | `importlib.metadata` + `direct_url.json`                                                                                                                                                          |
| `python`, `platform`, `nproc`, thread budget, `CASCOR_NUM_PROCESSES`                 | environment probe (H-11)                                                                                                                                                                          |
| `seeds` — experiment seed and every derived seed                                     | the YAML + derivation rule                                                                                                                                                                        |
| `ports`, `service_urls`                                                              | launcher                                                                                                                                                                                          |
| `timings` — per-phase and total                                                      | driver                                                                                                                                                                                            |
| `outcome` — `succeeded` \| `failed` \| `stalled` \| `timed_out` \| `torn_down_early` | driver                                                                                                                                                                                            |
| `metrics_scraped` — bool + the Prometheus target file path                           | launcher + a `/api/v1/targets` confirmation                                                                                                                                                       |
| `artifacts` — relative paths of every plot and result file                           | driver                                                                                                                                                                                            |

**The reproducibility claim, stated honestly**: given the same manifest, the same host, and clean checkouts at the recorded SHAs, a re-run reproduces the same `dataset_id` **exactly** (content-addressed + seeded) and the same metrics **within a characterised tolerance**.

Exact metric equality is not claimed: cascor's multiprocessing candidate pool and BLAS reduction order introduce nondeterminism that P3 measures rather than assumes away. A dirty tree at run time is recorded as `dirty: true` and downgrades the run to "not reproducible" in the aggregate report.

---

## 14. Work-Item Summary & Sequencing

Dependency-ordered. Size: S ≈ one focused sitting, M ≈ a day, L ≈ multi-day. Each row is intended as **its own PR** unless noted.

### Wave 0 — Ground truth (no code)

| #    | Item                                                                                                                                                                                                                                                                                                                                                                                                    | Repo       | Size | Depends on |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|------|------------|
| 0.1  | This plan, reviewed and ratified by the owner — **DONE 2026-07-30** (PR #867 merged; every Q-1…Q-12 recommendation concurred)                                                                                                                                                                                                                                                                           | juniper-ml | S    | —          |
| 0.2  | Execute P0 preflight (§10.1) steps P0.1-P0.9 + P0.11-P0.12 and file the evidence — **DONE 2026-07-30, all PASS** ([evidence](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md); two command-form errata folded back into §10.1)                                                                                                                                        | —          | S    | 0.1        |
| 0.2b | Execute **P0.10** against a hand-applied, **uncommitted** copy of the §7 compose/prometheus overlay — answers Q-4 empirically (relay reachability; the without-relay control arm shows connection-refused); its evidence gates merging Wave 1.1 — **DONE 2026-07-30**: control arm = connection refused, relay arm = `up` 2/2 with run-scoped labels; **Wave 1.1 unblocked** (evidence F-2/F-3 binding) | —          | S    | 0.2        |

### Wave 1 — Observability bridge (unblocks every "in Grafana" requirement)

| #   | Item                                                                                                                                | Repo           | Size | Depends on    |
|-----|-------------------------------------------------------------------------------------------------------------------------------------|----------------|------|---------------|
| 1.1 | Prometheus `extra_hosts` gateway mapping + `juniper-host-experiments` `file_sd_configs` job + `prometheus/targets/.gitkeep`         | juniper-deploy | S    | 0.2b          |
| 1.2 | `tests/test_prometheus_host_sd.py` structural gate                                                                                  | juniper-deploy | S    | 1.1 (same PR) |
| 1.3 | `grafana/provisioning/dashboards/juniper-recurrence.json` (closes G-4) + extend the three `juniper:http_request_duration_seconds:*` | juniper-deploy | M    | 1.1           |
|     | recording rules with recurrence's as-built generic `juniper_http_request_duration_seconds_bucket` series (§12.1, corrected)         |                |      |               |
| 1.4 | `grafana/provisioning/dashboards/juniper-experiments.json` (run-scoped, templated)                                                  | juniper-deploy | M    | 1.1           |

### Wave 2 — Launcher + driver (the usable core)

| #   | Item                                                                                | Repo       | Size | Depends on |
|-----|-------------------------------------------------------------------------------------|------------|------|------------|
| 2.1 | `util/experiment_stack.bash` + `tests/test_experiment_stack_script.py`              | juniper-ml | L    | 1.1        |
| 2.2 | `util/experiments/run_experiment.py` + `tests/test_run_experiment.py` (cascor path) | juniper-ml | L    | 2.1        |
| 2.3 | `run_experiment.py` recurrence path (train / predict / crossval)                    | juniper-ml | M    | 2.2        |
| 2.4 | Plotting: cascor set (§8.1)                                                         | juniper-ml | M    | 2.2        |
| 2.5 | Plotting: recurrence set (§8.2 — closes G-5)                                        | juniper-ml | M    | 2.3        |
| 2.6 | `stats.json` + `summary.md` renderers                                               | juniper-ml | S    | 2.4, 2.5   |
| 2.7 | `docs/REFERENCE.md` operator section + cheatsheet entries for the new tooling       | juniper-ml | S    | 2.6        |

### Wave 3 — YAML config layer

| #   | Item                                                                                                                                                                                                                                                                                                                 | Repo                                | Size | Depends on |
|-----|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|------|------------|
| 3.1 | cascor: `settings_customise_sources` + `ExperimentYamlSettingsSource` (`service:`-block projection, §5.2) + `JUNIPER_CASCOR_CONFIG_FILE` + `--config` on `server.py` (operator convenience — the experiment stack uses the uvicorn-factory CLI, §6.1) and `main.py` + unknown-key/infra-key rejection (§5.6) + tests | juniper-cascor                      | L    | 0.1        |
| 3.2 | cascor: `conf/experiments/` with 2-3 reference YAMLs                                                                                                                                                                                                                                                                 | juniper-cascor                      | S    | 3.1        |
| 3.3 | recurrence: same projection mechanism + `--config` on `serve` and `train` + the PyYAML/`pydantic-settings[yaml]` dependency + tests                                                                                                                                                                                  | juniper-recurrence                  | L    | 0.1        |
| 3.4 | recurrence: new `conf/experiments/` with 2-3 reference YAMLs                                                                                                                                                                                                                                                         | juniper-recurrence                  | S    | 3.3        |
| 3.5 | `tests/test_experiment_config_schemas.py` drift gate                                                                                                                                                                                                                                                                 | juniper-ml                          | S    | 3.2, 3.4   |
| 3.6 | **W-11** direct-CLI YAML mapping: cascor `src/main.py` thin adapter (experiment `training:`/`dataset:` blocks → problem/training params, `cascor_constants` fallback); recurrence `train` seeds its argparse defaults from `train:`                                                                                  | juniper-cascor + juniper-recurrence | M    | 3.1, 3.3   |

### Wave 4 — Dataset enablement (§11; independent of Waves 1-3, parallelisable)

| #   | Item                                                                             | Repo                      | Size |
|-----|----------------------------------------------------------------------------------|---------------------------|------|
| 4.1 | **W-1** non-spiral silent-drop fix (highest-value correctness item in this plan) | juniper-cascor            | M    |
| 4.2 | **W-3** `gaussian` + `checkerboard` staged Literal + typed params                | juniper-cascor            | S    |
| 4.3 | **W-5** register `ar_p` in the bench registry                                    | juniper-recurrence        | S    |
| 4.4 | **W-8** commit the `delay_product` baseline                                      | juniper-recurrence        | S    |
| 4.5 | **W-9** data-client constants + registry-derived parity gate                     | juniper-data-client       | M    |
| 4.6 | **W-4** mnist availability pre-flight + documented install path                  | juniper-data / juniper-ml | S    |
| 4.7 | **W-10** on-host generator-availability matrix in `docs/REFERENCE.md`            | juniper-ml                | S    |
| 4.8 | **W-2** cascor 3-D ingestion: typed support or explicit rejection                | juniper-cascor            | M    |

### Wave 5 — Concurrency hardening (unblocks parallel suites)

| #   | Item                                                                                                                                       | Repo                      | Size |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|------|
| 5.1 | **W-6** `JUNIPER_CASCOR_SNAPSHOTS_DIR` (service + direct CLI)                                                                              | juniper-cascor            | M    |
| 5.2 | **W-7** `bench.run_benchmark --results-dir`                                                                                                | juniper-recurrence        | S    |
| 5.3 | Drop the one-instance-per-checkout restriction in the launcher; add a two-run concurrency test. **Explicitly depends on resolving Q-6**    | juniper-ml                | S    |
|     |   (a per-run `JUNIPER_CASCOR_LOG_DIR`-class item): W-6/W-7 cover snapshots and bench results only, so the shared `logs/juniper_cascor.log` |                           |      |
|     |   race (H-7) returns otherwise. Until Q-6 is resolved, 5.3 is scoped to concurrent runs in **distinct checkouts** only                     |                           |      |
| 5.4 | Fix the stale conda-env path in the cascor systemd unit (G-13)                                                                             | juniper-cascor            | S    |
| 5.5 | **W-12** `csv_import` corpus + matrix row (gated on Q-7)                                                                                   | juniper-ml / juniper-data | S    |

> **Update (2026-08-16) — 5.3's Q-6 dependency is DISCHARGED; 5.3 itself is not yet done.** Read the
> row above as one item, not two. **Q-6 is resolved and shipped** (§15.2): `JUNIPER_CASCOR_LOG_DIR`
> lands in cascor#523 and `util/experiment_stack.bash` exports it per run, so the H-7 shared-log race
> no longer "returns otherwise" — do **not** re-open Q-6 as a precondition.
>
> What still blocks 5.3 is a **different** gate that did not exist when the row was written:
> `util/experiments/run_suite.py:112` refuses `app: cascor` with `parallel > 1` because `run_suite`
> cannot verify the **installed** cascor honours the override. Against a pre-#523 cascor the export is
> silently ignored and parallel cells race the shared log exactly as before, **with no signal** — a
> silent return of the evidence-destruction bug, which is why ml#1120 deliberately did not lift it.
> The fix is a `juniper-cascor` version floor asserted at suite load, then relaxing the refusal,
> keeping the failure loud when the floor is unmet. **It cannot be written yet**: PyPI's latest
> `juniper-cascor` is `0.9.0`, cut 2026-08-14 *before* #523 merged, and `main`'s pyproject still reads
> `0.9.0`, so no released version carries Q-6. Do not guess `>=0.9.1`. `tests/test_run_suite.py:152`
> pins the `Q-6` ID in the refusal message — keep it greppable. Not urgent: sequential cascor suites
> work, and every campaign to date has used them.
> **Update (2026-08-16) — owner decisions change the standing of BOTH remaining Wave 5 rows.**
>
> - **5.3 — "Not urgent" above is SUPERSEDED.** The owner's Q-6 answer is *"parallel execution
>   on-stack is becoming important."* Lifting `run_suite.py:112` is therefore demand-driven, and 5.3
>   should be scheduled as soon as its precondition clears. The precondition is unchanged and is
>   **external**: a `juniper-cascor` release carrying #523, which does not exist yet. Re-check
>   `curl -s https://pypi.org/pypi/juniper-cascor/json` each pass; do not guess a floor. Everything
>   else for 5.3 is ready.
> - **5.5 / W-12 is UN-PARKED, and its scope grew.** Q-7 is answered **yes**, and *wider than the
>   question asked*: the owner requires a `csv_import` option for **both the cascor and the
>   recurrence corpus**, whereas Q-7 asked only about the cascor dataset matrix. W-12 therefore needs
>   a sequence-shaped (3-D) import path in addition to the tabular one, and two matrix rows rather
>   than one. **Re-estimate before scheduling** — the row's `S` predates this widening.


### Wave 6 — Program execution

| #   | Item                                          | Repo | Size | Depends on |
|-----|-----------------------------------------------|------|------|------------|
| 6.1 | P1 smoke, all four launch modes               | —    | S    | 2.6, 1.4   |
| 6.2 | P2 dataset matrix (post-Wave-4)               | —    | M    | Wave 4     |
| 6.3 | P3 acceptance criteria evaluated and recorded | —    | M    | 6.2        |
| 6.4 | P4 experimentation studies E-A…E-H            | —    | L    | 6.3        |

### Wave 7 — Automation + performance (design-start follow-ons)

| #   | Item                                                                                  | Repo                        | Size |
|-----|---------------------------------------------------------------------------------------|-----------------------------|------|
| 7.1 | `util/experiments/run_suite.py` (sequential) + registry + aggregation + tests         | juniper-ml                  | L    |
| 7.2 | `util/experiments/list_runs.py` (safety-gated)                                        | juniper-ml                  | S    |
| 7.3 | Perf scenarios PF-1…PF-8 wired to the driver; Grafana perf panels for run-level rates | juniper-ml / juniper-deploy | M    |
| 7.4 | Alert-rule scoping so `environment="host-experiment"` does not page (Q-9)             | juniper-deploy              | S    |
| 7.5 | Bounded-parallel suite execution                                                      | juniper-ml                  | M    |
| 7.6 | Propose the `JR-REC-*` ID block (§16)                                                 | juniper-ml                  | S    |

---

## 15. Risks & Open Questions

### 15.1 Risks

| ID | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R-1 | A container→host scrape addressed to the bridge-gateway IP cannot reach a loopback-bound service — the kernel refuses the connection before any middleware runs (**connection refused**, not 403). | **High** (structural) | High — kills the whole Grafana story if unaddressed | The launcher-owned per-run `socat` relay (§7.3) listens on the gateway IP and forwards to loopback; P0.10 (step 0.2b) proves it end-to-end. Apps never bind non-loopback; no allowlist change (the relay's source is loopback). |
| R-2 | `host.docker.internal:host-gateway` behaves differently across the operator's docker/podman setups. | Medium | High | P0.10 verifies empirically; the launcher discovers the gateway via `docker network inspect` (monitoring network, falling back to the default bridge); fallback is that gateway IP written directly into the target file (a one-line launcher change). |
| R-3 | W-1's fix changes cascor's `POST /v1/training/start` behaviour for an existing consumer. | Medium | Medium | Prefer the 422-with-guidance variant, which is strictly more informative than today's silent drop, and check consumers first — canopy is out of scope for this program but not for the repo. |
| R-4 | The YAML precedence override (env below YAML) surprises someone relying on an exported env var. | Medium | Medium | The layer is inert unless `--config` / `*_CONFIG_FILE` is supplied; document loudly; log the resolved provenance of each setting at startup. |
| R-5 | Host resource contention makes performance numbers noisy (shared workstation, GPU present, other sessions). | **High** | Medium | Thread budgets pinned and recorded (H-11); PF-8 measures the concurrency cost; report-only, no CI gate (§12.4). |
| R-6 | Equities experiments fail or throttle on network/API limits. | Medium | Low | Cache per run by default with a `--shared-equities-cache` opt-in; equities rows are informational, never gating (matching the bench's graceful skip, `bench/run_benchmark.py:336-339`). |
| R-7 | Scope creep: the launcher grows into a mini orchestration framework. | Medium | Medium | Hard boundary — `experiment_stack.bash` only starts/stops/health-gates and allocates ports; all logic lives in the Python driver; `run_suite.py` is Wave 7 and sequential-first. |
| R-8 | Two Claude/operator sessions run experiments simultaneously and collide despite the policy. | Medium | High | Port lockdirs are the enforcement point (not advisory docs); per-checkout cascor lock until W-6; P3's isolation criterion tests it deliberately. |
| R-9 | The proposed cascor/recurrence changes (Wave 3) are large PRs against actively-developed repos. | Medium | Medium | Wave 3 is independent of Waves 1-2, so the program is usable (env-configured) before the YAML layer lands. Ship 3.1 and 3.3 as separate PRs per repo. |
| R-10 | Dashboards drift from the metric names they query as apps evolve. | Low | Medium | The panel-id test already exists; a metric-name-existence gate is a possible follow-on but is not proposed here (it needs a live scrape to be meaningful). |

### 15.2 Open questions (owner decisions)

| ID       | Question                                                                                                        | Recommendation                                                                                                                                                         |
|----------|-----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Q-1**  | Should the driver emit a fully-resolved `experiment.resolved.yaml` beside the verbatim config?                  | Yes — dumped from the live `Settings` object, not hand-reconstructed.                                                                                                  |
| **Q-2**  | cascor completion detection: what wall-clock budget and stall threshold?                                        | Budget from YAML (`outputs.max_wall_seconds`, default 3600); stall = 120 s without epoch progress → `outcome: "stalled"`, exit 1. Never hang silently.                 |
| **Q-3**  | Prometheus target-file location: nested in the existing `:ro` mount, or a separate dir + second mount?          | Nested at `./prometheus/targets/`, no second mount (Prometheus only reads; the host writes).                                                                           |
| **Q-4**  | Gateway-IP discovery + relay reachability: does the launcher-owned §7.3 `socat` relay make the                  | Answered empirically by P0.10 (step 0.2b): without the relay expect **connection refused** (a gateway-addressed connection can never land on a loopback bind); with it |
|          | container→host scrape land? (Re-scoped — **not** an allowlist question.)                                        | the `juniper-host-experiments` targets report `up == 1`. No allowlist change; never bind non-loopback (cascor's attestation guard, `src/api/settings.py:143-161`)      |
| **Q-5**  | `juniper-experiments.json`: provisioned + templated, or API-generated per run?                                  | Provisioned + templated on `run_id`.                                                                                                                                   |
| **Q-6**  | Is a `JUNIPER_CASCOR_LOG_DIR` override worth a work item, or is run-dir stdout capture enough?                  | Defer for single-instance-per-checkout use — but note it is now a **precondition for Wave 5.3** (lifting the one-instance rule);                                       |
|          |                                                                                                                 | until resolved, 5.3 is scoped to distinct checkouts (H-7).                                                                                                             |
| **Q-7**  | Should `csv_import` be in the cascor dataset matrix, and if so with what corpus?                                | Defer until a corpus is defined (W-12 tracks defining it and adding the matrix row); it is the one generator whose params are entirely dataset-specific.               |
| **Q-8**  | Where do run-level performance baselines live — juniper-ml `notes/`, a dedicated dir, or per-app repos?         | juniper-ml, beside the tooling that produces them; per-app repos keep only their micro-baselines. Owner call.                                                          |
| **Q-9**  | Should `environment="host-experiment"` targets be excluded from the existing alert rules?                       | Yes — exclude, then add experiment-scoped alerts if wanted. A deliberate stress benchmark must not page.                                                               |
| **Q-10** | Does recurrence deserve a dedicated `JuniperRecurrence` conda env, rather than riding `JuniperCascor1`?         | Probably yes for hygiene (recurrence's stack is much lighter than cascor's), but not a blocker — `JuniperCascor1` works today. Owner call.                             |
| **Q-11** | Should the direct-CLI paths (`cascor main.py`, `recurrence train`) be first-class in the YAML layer,            | First-class as the goal — stated honestly for v1: `--config` reaches only `Settings` (the `service:` block), so **full YAML coverage is service-tier**;                |
|          | or service-mode only?                                                                                           | the direct CLIs gain the `training:`/`dataset:`/`train:` blocks via W-11 (Wave 3.6). The direct CLI remains the cheapest reproducible unit for a sweep cell.           |
| **Q-12** | Is a `JR-REC-*` ID block wanted now, or should recurrence requirements wait for the next full snapshot refresh? | Propose the block now (Wave 7.6) so this plan's recurrence work is traceable rather than orphaned.                                                                     |




> **Update (2026-08-16) — Q-6 is RESOLVED and shipped; its row above is spent.** The answer was
> **yes**, and the override exists in both tiers:
>
> - **cascor#523** (merged `3909d275`) adds `JUNIPER_CASCOR_LOG_DIR`. Direct CLI reads it at *import*
>   time (`src/cascor_constants/constants.py:434-438`); the service reads it at *call* time in
>   `src/api/observability.py::_resolve_log_dir` (`:50`) and
>   `src/api/service_launcher.py::_resolve_log_dir` (`:85`). The call-time read is load-bearing — in
>   both helpers the `os.environ.get` precedes the `cascor_constants.constants` import, and the
>   `except ImportError` arm returns a hardcoded path that never consults the constants, so an
>   import-time-only override would be silently dropped exactly there.
> - **ml#1120** exports it per run at all three `cascor_up` sites in `util/experiment_stack.bash`
>   (`:618` announce, `:631` `record_launch_env`, `:643` live `nohup`).
> - Unset, blank, or whitespace-only keeps `<repo>/logs` **byte-identically** (`.strip()` folds them
>   to falsy and the `else` branch is the untouched prior expression), so no existing deployment
>   changed behaviour. Regression: `src/tests/unit/api/test_q6_log_dir_override.py` (20 tests).
>
> **The framing in the original row was wrong, and that is the durable lesson.** Q-6 was filed as a
> *concurrency* nicety and H-7 accepted the shared log as residual risk. It is an **evidence-integrity**
> defect. cascor's parent logger writes **only** to that file — stdout carries just candidate-worker
> lines — so the markers that decide a run's verdict (`Training completed`,
> `src/cascade_correlation/cascade_correlation.py:1936`; `Completed solving`, `src/main.py:512`; both
> `logger.info`) exist nowhere else. A second cascor process does not interleave the log, it **rotates
> the evidence away**. One other process is enough, so the one-instance rule never protected an
> individual run from a long-lived service sharing its checkout. That is how the F-P1-3 arm A/B logs
> were lost ([F-P1-3 root cause](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md)).
>
> **Wave 5.3 is only PARTLY unblocked** — see the Wave 5 table and H-7. The mechanism now exists, but
> `util/experiments/run_suite.py:112` still refuses `app: cascor` with `parallel > 1`, because
> `run_suite` cannot verify the *installed* cascor honours the override: against a pre-#523 cascor the
> export is silently ignored and parallel cells race the shared log exactly as before, **with no
> signal**. Lifting it needs a `juniper-cascor` version floor asserted at suite load — and **no
> released cascor carries #523 yet** (PyPI latest `0.9.0`, cut 2026-08-14 *before* the merge; `main`'s
> pyproject is still `0.9.0`). The floor cannot be written until the next cascor release; **do not
> guess `>=0.9.1`.**
> **Owner decisions (2026-08-16) — Q-6, Q-7, Q-8, Q-10 are ANSWERED.** Recorded verbatim in intent;
> each row above is superseded accordingly. Q-1..Q-5, Q-9, Q-11, Q-12 were ratified 2026-07-30 and
> are unchanged.
>
> | ID | Decision | Consequence |
> |---|---|---|
> | **Q-6** | **Yes — worth doing.** "Parallel execution on-stack is becoming important." | Already shipped (cascor#523 + ml#1120). The owner's rationale **raises the priority** of the remaining half: lifting `run_suite.py:112` so cascor suites can run parallel cells. That is now demand-driven work, not opportunistic — but it still cannot land until a cascor release carries #523 (see the Q-6 block above). **Re-check the release on every pass.** |
> | **Q-7** | **Yes — `csv_import` is needed, for BOTH corpora.** A CSV import option must be available to the **cascor** and the **recurrence** corpus. | **Un-parks W-12** (Wave 5.5), which the plan gated on this question and which has been parked since 2026-08-08. Note the scope is *wider* than the original Q-7 wording, which asked only about the **cascor dataset matrix**: the decision extends it to recurrence, so W-12 must cover a sequence-shaped (3-D) import path as well as the tabular one, and the matrix row work is now two rows. W-12's original "gated on Q-7" size estimate (S) should be re-estimated before scheduling. |
> | **Q-8** | **A dedicated, NEW directory.** | Supersedes the recommendation above ("juniper-ml, beside the tooling that produces them"). Run-level performance baselines get their own directory rather than living beside the tooling or in per-app repos. The directory's location, name, and retention contract are part of the §12 design phase (below), not an implementation detail to be improvised — and Q-8 also gates the `JR-CAS-OBS-004` targets (§16). |
> | **Q-10** | **Yes — juniper-recurrence gets a dedicated conda env.** | Supersedes "probably yes … but not a blocker". A `JuniperRecurrence` env joins `JuniperCanopy` / `JuniperCascor` / `JuniperData` as a first-class ecosystem environment, which makes it a documentation change as well as a provisioning one (the parent `CLAUDE.md` env table, `docs/REFERENCE.md`, and `experiment_stack.bash`'s recurrence launch path, which currently rides `JuniperCascor1`). |
>
> **Still open owner items after this round:** F-P1-4 (snapshot lifecycle — owner directed a
> designed/validated/documented systems solution, explicitly **not** an ad-hoc sweep) and the §12 PF
> threshold ratification. **F-P1-2 is CLOSED** (premise refuted —
> [closure evidence](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_F-P1-2-GRAFANA-RENDER-CLOSURE-EVIDENCE.md)).


---

## 16. Requirements Traceability

Verified against [`notes/requirements/by-area/TEST.md`](requirements/by-area/TEST.md), [`OBS.md`](requirements/by-area/OBS.md), [`PERF.md`](requirements/by-area/PERF.md), and [`TRAIN.md`](requirements/by-area/TRAIN.md); index at [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`](JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md). Verbs per the repo's PR conventions.

- **Partially closes `JR-CAS-TEST-006`** — "Establish performance testing infrastructure with reproducible baselines and CI/CD integration." (proposed, P1; `TEST.md:466-478`). §12 reuses the existing 5-phase performance suite and its persisted baselines and adds the run-level measurement contract; CI integration is explicitly deferred (§12.4), hence *partially*.
- **Partially closes `JR-CAS-OBS-004`** — "Define performance targets for latency and throughput." Notes: "Benchmark harness needed to measure actual performance against targets." (proposed, P2; `OBS.md:1579-1589`). §12.3's scenario list plus §7's Grafana surface provide the measurement harness; the *targets* themselves remain an owner decision (Q-8).
- **References `JR-CAS-TEST-018`** — "Create end-to-end integration tests spinning up JuniperData and full pipeline." Detail: "No automated integration tests spin up JuniperData and verify full pipeline (Cascor → JuniperData → artifact → tensor conversion → training). All current tests use mocks." (proposed, P3; `TEST.md:1562-1573`). §10.2-10.3 exercise exactly that pipeline for real, on-host — as an operator-invoked program rather than automated tests, so *references*.
- **References `JR-CAS-OBS-002`** — "Define Prometheus histogram buckets for latency metrics per observability requirements." (**shipped**, P2; `OBS.md:1013-1021`). §12.1 consumes the shipped `juniper_cascor_training_step_duration_seconds` buckets rather than adding new ones.
- **References `JR-CAS-PERF-004`** — "Create baseline performance profiles using py-spy for regression detection." (deferred, P3; `PERF.md:385-395`). §12.1 uses cascor's in-repo `--profile` / `--profile-memory` tooling instead of py-spy; the requirement stays deferred.
- **References `JR-CAS-PERF-005`** — "Infrastructure enhancements: GPU/CUDA support, continuous profiling (Grafana Pyroscope), large file refactoring, auto-generated API docs." (proposed, P3; `PERF.md:407-419`). §12.5 notes continuous profiling as a possible later phase; nothing here commits to it.
- **References `JR-CAS-TEST-019`** — "Test WebSocket responsiveness during training under load via asyncio.run_in_executor()." (proposed, P3; `TEST.md:1623-1633`). Out of scope (this program polls REST; §3.2 records the `/ws/training` alternative), but the CLI harness is the natural future host for such a load test.
- **References `JR-CAS-OBS-005`** — "Verify WebSocket responsiveness under load when training runs via asyncio.run_in_executor()." (proposed, P2; `OBS.md:2333-2338`). Same relationship as TEST-019.
- **References `JR-CAS-TRAIN-010`** — "Cascor must implement mini-batch training for the output-layer trainer…" with proposed config knobs `use_mini_batch` / `mini_batch_size` (proposed, P0; `TRAIN.md:211-222`). Cited as the **config-knob precedent**: any knob that requirement adds should be exposed through the §5.4 YAML layer, not a new env-only path.

**No `JR-REC-*` requirement IDs exist.** The owner enum is fixed at `notes/requirements/README.md:20` (`cas/can/dat/dep/ml/cwk/ccl/dcl`) and the snapshot is "as of 2026-05-12"; juniper-recurrence postdates it, and a repo-wide grep for `JR-REC-` across `notes/requirements/by-area/` returns nothing. Every recurrence work item in this plan is therefore traceable only through the design notes in §17.

**Work item 7.6 (PROPOSED)**: extend the owner enum with a `rec` tag and mint a `JR-REC-*` block covering, at minimum, the experiment-config layer (§5.5), the plotting gap (G-5), the bench `--results-dir` and `ar_p` registration (W-5/W-7), the missing Grafana dashboard (G-4), and the absent `performance` marker (G-17) — so recurrence requirements stop being untrackable.

---

## 17. References

### 17.1 juniper-ml notes (relative links; all verified present)

- [`JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md`](JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md) — the isolated-stack recipe this program's launcher is modeled on; the source of the port-isolation discipline.
- [`JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-DESIGN.md`](JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-DESIGN.md) — the ratified OQ-14 acceptance bands the bench implements; the scoring authority for §10.4.
- [`JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-FINDINGS.md`](JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-FINDINGS.md) — Δt-proof findings, including the ridge-variant / equities-ceiling result (§3.2) that E-H should reproduce.
- [`JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md`](JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md) — the linear → RFF → MLP rung spectrum that maps 1:1 to `--readout` and to E-E.
- [`JUNIPER_2026-06-18_JUNIPER-RECURRENCE_METRICS-ENDPOINT-DESIGN.md`](JUNIPER_2026-06-18_JUNIPER-RECURRENCE_METRICS-ENDPOINT-DESIGN.md) — the design of the `/metrics` surface §7 scrapes.
- [`JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-DATASET-AUDIT.md`](JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-DATASET-AUDIT.md) — the dataset-capability audit behind the §10.3 recurrence matrix.
- [`JUNIPER_2026-06-14_JUNIPER-RECURRENCE_RECURSE-OQ4-CASCOR-3D-INGESTION-GATE.md`](JUNIPER_2026-06-14_JUNIPER-RECURRENCE_RECURSE-OQ4-CASCOR-3D-INGESTION-GATE.md) — the cascor↔recurrence 3-D seam that W-2 must respect.
- [`JUNIPER_2026-05-08_JUNIPER-ECOSYSTEM_METRICS-DOCUMENTATION.md`](JUNIPER_2026-05-08_JUNIPER-ECOSYSTEM_METRICS-DOCUMENTATION.md) — the ecosystem metrics catalogue underpinning §7 and §12.
- [`observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md`](observability/JUNIPER_2026-05-10_JUNIPER-DEPLOY_GRAFANA-DASHBOARDS-STATE-AND-GAPS.md) — prior dashboard state-and-gaps analysis; §7.4 extends it.
- [`JUNIPER_2026-06-17_JUNIPER-RECURRENCE_STATE-ASSESSMENT-AND-ROADMAP.md`](JUNIPER_2026-06-17_JUNIPER-RECURRENCE_STATE-ASSESSMENT-AND-ROADMAP.md) — recurrence roadmap context (WS-8 persistence, referenced by G-18).
- [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) — the naming rules this document follows.
- [`JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`](JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md) and [`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md) — the isolation procedure for the second checkout that the interim one-cascor-per-checkout rule (H-4) requires.
- [`requirements/by-area/TEST.md`](requirements/by-area/TEST.md), [`requirements/by-area/OBS.md`](requirements/by-area/OBS.md), [`requirements/by-area/PERF.md`](requirements/by-area/PERF.md), [`requirements/by-area/TRAIN.md`](requirements/by-area/TRAIN.md) — the JR-ID entries in §16.

### 17.2 juniper-ml docs

- [`docs/REFERENCE.md`](../docs/REFERENCE.md) — operator contracts for `isolated_stack.bash`, host orchestration, and the port table; W-10 and item 2.7 add sections here.

### 17.3 Primary code anchors (plain code spans — cross-repo, deliberately not links)

- **juniper-cascor**: `src/server.py:15-25` · `src/main.py:48-50,172,316-331,435-441,448-449` · `src/api/app.py:590,664-666,671-675` · `src/api/settings.py:117,124-129,132-133,143-161,168-170,373,383,422,428-434,506-507`
- **juniper-cascor (routes/models)**: `src/api/routes/training.py:20,30,75,179,237,328-360` · `src/api/routes/metrics.py:17,26,36` · `src/api/routes/decision_boundary.py:20` · `src/api/routes/network.py:34,55,67` · `src/api/models/training.py:32,44,51-72,147-167,180-200`
- **juniper-cascor (lifecycle/obs/plots)**: `src/api/lifecycle/manager.py:32-39,3251,3254-3300,3356-3362,3367-3377,4300-4304,4305-4323` · `src/api/lifecycle/state_machine.py:24-52` · `src/api/observability.py:161-167,194,219-290,384-389` · `src/cascor_plotter/cascor_plotter.py:39,41,50,76,128,197` · `src/cascade_correlation/cascade_correlation.py:2281-2299`
- **juniper-cascor (constants/tests)**: `src/cascor_constants/constants.py:418,460-461` · `src/cascor_constants/constants_hdf5/constants_hdf5.py:45-46` · `src/cascor_constants/constants_api/constants_api_defaults.py:114` · `src/tests/conftest.py:207,260-266` · `src/tests/run_tests.bash:156` · `src/tests/performance/test_baselines.py:48-60` · `scripts/juniper-cascor.service:30`
- **juniper-recurrence**: `juniper-recurrence/juniper_recurrence/main.py:41-63,80,92-94,134-136` · `juniper_recurrence/settings.py:38,46-47,54,64-78,81-85` · `juniper_recurrence/app.py:48,107-132,152` · `juniper_recurrence/metrics.py:29-36,40-41,50-70` · `juniper_recurrence/schemas.py:72-88,106-119,145-150,206-230,248-266` · `juniper_recurrence/routers/{training,predict,crossval}.py:37,29,53` · `Dockerfile:88-91`
- **juniper-recurrence (bench/model)**: `bench/run_benchmark.py:29-39,134-257,260-324,336-339,341,347` · `bench/datasets.py:91-114,137-182,236,244-262` · `juniper-recurrence-model/juniper_recurrence_model/model.py:172-179`
- **juniper-data**: `juniper_data/api/routes/generators.py:44,54-175,178-200,203,225` · `juniper_data/api/routes/datasets.py:71-73,93-97,114-118,165-168,676` · `juniper_data/api/settings.py:111,119,126-127,133,141,171` · `juniper_data/api/security.py:55` · `juniper_data/__main__.py:17-50,66-73` · `juniper_data/core/dataset_id.py:23-34` · `juniper_data/core/meta.py:119-124` · `juniper_data/generators/_sequence.py:120-121,203-207,291-295` · `juniper_data/generators/equities/generator.py:83,131,426`
- **juniper-data-client**: `juniper_data_client/client.py:125,347-371,412-423,547` · `juniper_data_client/constants.py:138-150` · `juniper_data_client/contract.py:41` · `tests/test_generator_parity.py:27-39,72-76`
- **juniper-deploy**: `prometheus/prometheus.yml:45-49,56,61-126` · `prometheus/prometheus.demo.yml:61` · `prometheus/recording_rules.yml:31,40,49` · `prometheus/alert_rules.yml:207,697,766` · `docker-compose.yml:535,842-866,918-940` · `grafana/provisioning/dashboards/dashboard-providers.yml:5-15` · `tests/test_grafana_dashboard_ids.py:23,33-45,54-60` · `.env.observability:24-27,56-64` · `Makefile:144-163`
- **juniper-ml packages**: `juniper-observability/juniper_observability/prometheus.py:29-35` · `juniper-observability/juniper_observability/prometheus_helpers.py:214` · `juniper-observability/juniper_observability/middleware/prometheus.py:49-66` · `juniper-observability/juniper_observability/middleware/metrics_auth.py:49,104-183` · `juniper-service-core/juniper_service_core/health.py:31-39`
- **juniper-ml tooling**: `util/isolated_stack.bash:58-60,67-71,127-131,134-147,150-165,208-211,246-257,266-268,320-348` · `util/juniper_plant_all.bash:84-85,111,125,148,183,192-202,375-378,407-412,515-523` · `util/juniper_chop_all.bash:285-299`

---

**End of document.** Status: **Executed against; ratification partial** (updated 2026-08-16).
The independent adversarial validation pass is **complete** — three validators, findings folded
in — and recorded in §2.4.

The original trailer read *"Proposed (draft for owner review). Ratification requires owner
decisions on Q-1 through Q-12"*, which stayed unchanged while the whole program executed against
this plan. The honest state of the Q-table (§13):

| Q | State |
|---|---|
| Q-1 | **SHIPPED 2026-08-21**, re-scoped by owner decision. `config/experiment.resolved.yaml` is now written on both app paths, from the same `finally` that writes the manifest (so every run has one, including failed / stalled / timed-out). The original wording — *dumped from the live `Settings` object* — is **not implementable as written**: the driver is an HTTP client and never constructs the app's `Settings`; cascor exposes no settings endpoint (`GET /v1/training/params` covers `TrainingParams` only) and recurrence exposes no equivalent at all. Building one would also mean designing redaction — cascor's `Settings` carries `api_keys` among 56 fields — which is the hand-maintained-artifact class Q-1 was written to avoid. The file therefore records only what can be **verified**, each half tagged with its source: `driver_resolved` (the input YAML after the driver's own defaulting) and `service_training_params` (the service's echo, or a stated reason there is none). `_meta.scope` names what is **not** covered — app-level `Settings` — inside the artifact, so it cannot be mistaken for a complete picture. Nothing is reconstructed. |
| Q-2 | **Decided and wired.** Both knobs now reach the driver from a suite: `execution.stall_seconds` (ml#1069) and `execution.max_wall_seconds`. |
| Q-3, Q-4, Q-5 | **Decided**; Q-4 answered empirically by P0.10. |
| Q-6 | **Resolved** by `JUNIPER_CASCOR_LOG_DIR` (juniper-cascor#523). The §13 row itself belongs to the dedicated Q-6 register-propagation change (juniper-ml#1129), which sweeps every site still calling it open; this trailer deliberately does not edit that row. |
| Q-7, Q-8, Q-10 | **ANSWERED 2026-08-16** (ml#1136) — see the owner-decision block above. Q-7 yes, for BOTH corpora (un-parks W-12, scope widened); Q-8 a dedicated NEW directory; Q-10 yes, a `JuniperRecurrence` env. This row previously read "open owner calls", which contradicted that block; corrected here. |
| Q-9 | **Decided and shipped** — every alert in `juniper-deploy/prometheus/alert_rules.yml` carries `environment!="host-experiment"`. |
| Q-11 | **Decided**; the direct CLIs gained the `training:` / `dataset:` blocks via W-11 (Wave 3.6). |
| Q-12 | **Decided** (`propose now`), and Wave 7.6's verb is *Propose* — the proposal exists, so the wave item is done. Ratification into the requirements snapshot is still outstanding; there are zero `JR-REC-` IDs in the index today. |

So ratification is no longer blocked on twelve open questions. **Every Q-1…Q-12 is now answered** —
Q-6/Q-7/Q-8/Q-10 by the 2026-08-16 owner round (ml#1136) recorded above. What remains is not a
question but follow-through: Q-1's emitter is unimplemented, Q-12 awaits a requirements snapshot
refresh, and §12's performance lane is **GATED** behind its design→planning→verification→documentation
phasing (see the §12 block above) and remains **unexecuted**. §12 still describes itself as *"a design
start, not a final design"*.
