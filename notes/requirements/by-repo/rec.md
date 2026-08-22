# Requirements — juniper-recurrence (rec)

**Total entries**: 11

**By status**: proposed=1 | shipped=9 | deferred=1

**By priority**: P0=2 | P1=4 | P2=4 | P3=1

**By category**: TEST=3 | TRAIN=2 | TOOL=2 | DATA=1 | API=1 | OBS=1 | DEP=1

---

### JR-REC-TRAIN-001 — Δt-native LMU sequence regressor with ratified acceptance bands

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-DESIGN.md` (lines 97-109)
- `juniper-recurrence/bench/run_benchmark.py` (lines 137-149)

**Detail**:

The variable-Δt LMU must (band 1) cut RMSE ≥ 25% vs the fixed-Δt control on irregular-Δt data, (band 2) beat naive persistence and match/beat the linear ridge baseline on every primary dataset, and (band 3) tie fixed-Δt on regular grids. The pre-registered `PRIMARY_DATASETS` + `evaluate_bands` are the sole scoring authority (DP-5 guardrail).

### JR-REC-TRAIN-002 — Readout spectrum (linear / RFF / MLP) with a capacity instrument

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md` (lines 31-43)
- `juniper-recurrence/bench/datasets.py` (lines 15-27)

**Detail**:

Nonlinear readouts must demonstrate capacity the linear readout provably lacks on the bilinear `delay_product` target (measured gaps: RFF +0.83, MLP +0.87 r²) while merely tying linear on near-linear synthetics. A miss is a finding to record, never a threshold to tune.

### JR-REC-DATA-001 — 3-D irregular-Δt NPZ sequence contract consumption

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md` (lines 1-13)
- `juniper-data-client/juniper_data_client/contract.py` (lines 41-53)

**Detail**:

Consume `{X,y,dt,target_dt,observed_mask}_{train,test,full}` with `dt[:,0]==0`; equities sequences use the stationary `y_reg_*` log-return target (the r²≈−50 raw-price artifact class), never the one-hot direction label.

### JR-REC-API-001 — Service train/predict/crossval referencing content-addressed datasets

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 363-375)
- `juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/training.py` (lines 37-49)

**Detail**:

Synchronous `POST /v1/train` (response = completion); `predict`/`crossval` reference `dataset_id` only (never bare `name`); crossval reuses the train hyperparameters for bench comparability. Raw pydantic response bodies (no envelope) — a deliberate contrast with cascor's `{status,data,meta}`.

### JR-REC-TEST-001 — Bench harness with pre-registered scope as scoring authority

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-recurrence/bench/run_benchmark.py` (lines 137-149)
- `juniper-recurrence/bench/datasets.py` (lines 262-274)
- `juniper-recurrence/bench/test_bench_smoke.py` (lines 1-13)

**Detail**:

Primary bands scored only on the pre-registered set; extensions (noise sweep, `ar_p` linear floor, `delay_product` capacity, `equities_seq` real data) are informational. Committed `bench/results/` baselines are reproducible from seeds.

### JR-REC-TEST-002 — Service-vs-bench parity as a regression criterion

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md` (lines 1-13)

**Detail**:

A service-mode run with bench-primary-matched params must land inside the same OQ-14 bands as the offline bench; divergence is a service-path defect. Candidate for a periodic (release-gate or scheduled) automated check once `run_suite.py` (Wave 7.1) exists.

### JR-REC-TOOL-001 — Experiment YAML config layer (`service:` projection)

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 264-276)
- `juniper-recurrence/juniper-recurrence/juniper_recurrence/settings.py` (lines 60-72)

**Detail**:

`JUNIPER_RECURRENCE_CONFIG_FILE` activates a `service:`-block-only projection with precedence CLI/init > YAML > env > defaults; forbidden infra keys (`host`/`port`/`juniper_data_url`) fail loud; deliberately **no** `.env` tier (env-file-leak doctrine).

### JR-REC-TOOL-002 — Direct-CLI `train:` block seeding (W-11)

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: rec

**Sources**:
- `juniper-recurrence/juniper-recurrence/juniper_recurrence/main.py` (lines 96-108)

**Detail**:

The `train` subcommand seeds unset argparse flags from the experiment YAML's `train:` block; explicit CLI flags win; unmodeled keys warn and are never silently applied.

### JR-REC-TEST-003 — Concurrent bench runs (per-run results dir)

**Status**: shipped  **Priority**: P2  **Category**: TEST  **Owner**: rec

**Sources**:
- `juniper-recurrence/bench/run_benchmark.py` (lines 4-16)

**Detail**:

`python -m bench.run_benchmark --results-dir DIR` routes per-dataset JSON + REPORT.md; the default stays the committed `bench/results/` byte-identically.

### JR-REC-OBS-001 — Experiment-lane observability toggles

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 444-456)
- `juniper-ml/util/experiment_stack.bash` (lines 7-19)

**Detail**:

Metrics exposition on + rate-limit off for per-run scrape lanes; targets labeled `service`/`environment=host-experiment`/`run_id`/`experiment` via the launcher's file_sd bridge.

### JR-REC-DEP-001 — Dedicated conda environment decision (Q-10)

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: rec

**Sources**:
- `juniper-ml/notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (lines 1262-1274)

**Detail**:

Recurrence currently rides `JuniperCascor1` (works today; editable install + console script live there). A dedicated lighter env is probably right for hygiene — explicitly an owner call; nothing blocks on it.
