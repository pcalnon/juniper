# JR-REC-* Requirements Block — Proposal (Wave 7.6 / Q-12)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Sub-Project**: Requirements snapshot — juniper-recurrence owner block
**Author**: Paul Calnon
**Date**: 2026-08-08
**Status**: PROPOSAL — IDs become official only at the next snapshot refresh
**Motivating gap**: [CLI experimentation plan](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §16 — *"No `JR-REC-*` requirement IDs exist… juniper-recurrence postdates the snapshot"* (Q-12: propose the block now so recurrence work is traceable rather than orphaned).

---

## 1. Enum change proposed

`notes/requirements/README.md` owner-repo enum (currently `cas/can/dat/dep/ml/cwk/ccl/dcl`, fixed as of the 2026-05-12 snapshot) gains:

| Code | Repo |
| --- | --- |
| `rec` | `juniper-recurrence` (monorepo: app + `juniper-recurrence-model` + `juniper-recurrence-client` + `bench/`) |

No new area codes — the locked 15 suffice. ID format unchanged: `JR-REC-<AREA>-<NNN>`.

## 2. Proposed starter block

Statuses reflect as-built reality at proposal time (most items shipped before the block existed — the point of Q-12 is retroactive traceability plus a home for what's next). Sources cite the authoritative design docs and code; line numbers deliberately omitted where files churn.

### JR-REC-TRAIN-001 — Δt-native LMU sequence regressor with ratified acceptance bands

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: rec
**Sources**: `juniper-ml/notes/JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-DESIGN.md` (OQ-14 bands); `juniper-recurrence/bench/run_benchmark.py` (`evaluate_bands`)
**Detail**: The variable-Δt LMU must (band 1) cut RMSE ≥ 25% vs the fixed-Δt control on irregular-Δt data, (band 2) beat naive persistence and match/beat the linear ridge baseline on every primary dataset, and (band 3) tie fixed-Δt on regular grids. The pre-registered `PRIMARY_DATASETS` + `evaluate_bands` are the sole scoring authority (DP-5 guardrail).

### JR-REC-TRAIN-002 — Readout spectrum (linear / RFF / MLP) with a capacity instrument

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: rec
**Sources**: `juniper-ml/notes/JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md`; `bench/results/delay_product.json` (in-repo baseline, W-8)
**Detail**: Nonlinear readouts must demonstrate capacity the linear readout provably lacks on the bilinear `delay_product` target (measured gaps: RFF +0.83, MLP +0.87 r²) while merely tying linear on near-linear synthetics. A miss is a finding to record, never a threshold to tune.

### JR-REC-DATA-001 — 3-D irregular-Δt NPZ sequence contract consumption

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: rec
**Sources**: WS-1 data foundation (juniper-data#168); `juniper-data-client` `validate_npz_contract`; `juniper-ml/notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md`
**Detail**: Consume `{X,y,dt,target_dt,observed_mask}_{train,test,full}` with `dt[:,0]==0`; equities sequences use the stationary `y_reg_*` log-return target (the r²≈−50 raw-price artifact class), never the one-hot direction label.

### JR-REC-API-001 — Service train/predict/crossval referencing content-addressed datasets

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: rec
**Sources**: CLI experimentation plan §5.5/§6.3 (H-8); `juniper_recurrence` service routes
**Detail**: Synchronous `POST /v1/train` (response = completion); `predict`/`crossval` reference `dataset_id` only (never bare `name`); crossval reuses the train hyperparameters for bench comparability. Raw pydantic response bodies (no envelope) — a deliberate contrast with cascor's `{status,data,meta}`.

### JR-REC-TEST-001 — Bench harness with pre-registered scope as scoring authority

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: rec
**Sources**: `bench/run_benchmark.py`; `bench/datasets.py` (`PRIMARY_DATASETS` vs extensions); `bench/test_bench_smoke.py`
**Detail**: Primary bands scored only on the pre-registered set; extensions (noise sweep, `ar_p` linear floor, `delay_product` capacity, `equities_seq` real data) are informational. Committed `bench/results/` baselines are reproducible from seeds.

### JR-REC-TEST-002 — Service-vs-bench parity as a regression criterion

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: rec
**Sources**: [P3 acceptance roll-up](JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md) §2 (precedent: bit-identical parity measured 2026-08-08)
**Detail**: A service-mode run with bench-primary-matched params must land inside the same OQ-14 bands as the offline bench; divergence is a service-path defect. Candidate for a periodic (release-gate or scheduled) automated check once `run_suite.py` (Wave 7.1) exists.

### JR-REC-TOOL-001 — Experiment YAML config layer (`service:` projection)

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: rec
**Sources**: CLI experimentation plan §5.2/§5.6; `juniper_recurrence/settings.py` (`ExperimentYamlSettingsSource`)
**Detail**: `JUNIPER_RECURRENCE_CONFIG_FILE` activates a `service:`-block-only projection with precedence CLI/init > YAML > env > defaults; forbidden infra keys (`host`/`port`/`juniper_data_url`) fail loud; deliberately **no** `.env` tier (env-file-leak doctrine).

### JR-REC-TOOL-002 — Direct-CLI `train:` block seeding (W-11)

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: rec
**Sources**: recurrence#99; `juniper_recurrence/main.py` (`_experiment_train_overrides` / `_apply_train_overrides`)
**Detail**: The `train` subcommand seeds unset argparse flags from the experiment YAML's `train:` block; explicit CLI flags win; unmodeled keys warn and are never silently applied.

### JR-REC-TEST-003 — Concurrent bench runs (per-run results dir)

**Status**: shipped  **Priority**: P2  **Category**: TEST  **Owner**: rec
**Sources**: recurrence#102 (W-7 / hazard H-6)
**Detail**: `python -m bench.run_benchmark --results-dir DIR` routes per-dataset JSON + REPORT.md; the default stays the committed `bench/results/` byte-identically.

### JR-REC-OBS-001 — Experiment-lane observability toggles

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: rec
**Sources**: CLI experimentation plan §6.1/§7; `util/experiment_stack.bash` recurrence recipe
**Detail**: Metrics exposition on + rate-limit off for per-run scrape lanes; targets labeled `service`/`environment=host-experiment`/`run_id`/`experiment` via the launcher's file_sd bridge.

### JR-REC-DEP-001 — Dedicated conda environment decision (Q-10)

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: rec
**Sources**: CLI experimentation plan §15 Q-10
**Detail**: Recurrence currently rides `JuniperCascor1` (works today; editable install + console script live there). A dedicated lighter env is probably right for hygiene — explicitly an owner call; nothing blocks on it.

## 3. Process notes

- IDs above are **reserved by this proposal** but become official only when the snapshot refresh (`requirements-next-steps` §7 rewrite mode) ingests them; until then PR descriptions may reference them with the `References JR-REC-…` verb marked *(proposed)*.
- Interim PR descriptions during Waves 4–5 used descriptive placeholders (e.g. `JR-RECURRENCE-BENCH-001`); the refresh should map those to `JR-REC-TEST-001`/`JR-REC-TEST-003` rather than minting the long-form spellings.
- `by-repo/rec.md` and `id_assignments.yaml` entries are generated artifacts of the refresh — this proposal deliberately edits neither.
