# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **`crossval/splits.py`'s module docstring described a void premise.** It said folds are "derived
  client-side from the `*_full` arrays" (decision D-CV-4). Since decision 11 of the partition design
  (juniper-ml `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.5;
  juniper-data#369, 2026-09-06) the producer emits no `*_full` family, so a reader following that
  docstring would look for arrays that no current artifact carries. The docstring now says the folds
  index the whole dataset the caller rebuilds from `train` / `val` / `test` (reference implementation:
  `juniper_recurrence_model.data.derive_full_split`, juniper-recurrence#150), that the rebuild's row
  ORDER matters because folds slice by index, and that a legacy `*_full` may still be used as-is.
  Docstring only — `walk_forward_folds` is unchanged; the published 0.3.1 wheel carries the stale text
  until the next release.

## [0.3.1] - 2026-07-28

### Fixed

- Lint-conformance fixes from the sub-package Ruff governance adoption (juniper-ml#508, audit B4/F3): explicit `strict=False` on the monotonicity check's `zip` in `juniper_model_core/validation.py` (behavior-identical), N803/N806 ignores for the ecosystem NPZ data-contract names in `pyproject.toml`, and test-suite lint fixes. Docstring references updated to the juniper-ml `notes/` naming convention (the 2026-07-04 migration). No functional changes.

## [0.3.0] - 2026-06-18

### Added

- **Multi-entity ("panel") walk-forward folds (`walk_forward_folds(..., groups=)`).** An additive,
  keyword-only `groups` parameter (per-sample entity id, e.g. `ticker_code`) generalizes the splitter
  to panel data. Folds stay pooled and date-ordered (train = all entities' windows before each cut;
  eval = the next block across all entities), but the `embargo` purge is applied **per group** -- from
  each fold's train side, the last `embargo` windows *of each entity* (by that entity's own `order`)
  are dropped. This closes the same-entity look-back leak at the fold boundary that a single
  global-rank embargo leaves open on a panel (where a global gap mostly drops *other* entities'
  rows). `groups=None` (default) is byte-identical to the prior single-series behavior, so the
  change is fully backward compatible.

## [0.2.0] - 2026-06-17

### Added

- **Cross-validation / fold-executor layer (`juniper_model_core.crossval`).** An optional,
  model-agnostic orchestration tier above a single model: `walk_forward_folds` (index-based,
  expanding/rolling, `embargo` + chronological `order`), `cross_validate` (fresh model per fold via
  a factory -> held-out predict -> external score -> per-metric mean/std aggregate), and the
  `Fold` / `FoldResult` / `CrossValResult` value types. Built purely on the `TrainableModel`
  contract; serial by default with an optional `map_fn` seam for a future parallel/distributed
  worker. Behind the new `[crossval]` extra (numpy); **not** re-exported from the top-level
  package, so `import juniper_model_core` stays dependency-free.
- **Held-out scoring (`crossval.metrics`).** `regression_metrics` plus a `score(task_type, ...)`
  dispatch (regression implemented; classification raises `NotImplementedError` -- an additive
  drop-in later).
- **Shared metric source (`juniper_model_core._metrics`).** The canonical regression-metric math
  now lives in one private module that both `crossval.metrics` and the conformance kit's reference
  model call, so the two implementations cannot drift.

### Changed

- **`TrainableModel.predict` contract widened to `predict(self, X, **kw)`** (additive, LSP-safe):
  sequence models may read `dt` / `readout_mask` / `seq_lengths` from `**kw`, symmetric with `fit`
  (decision D3). Existing bare `predict(X)` implementers and callers are unaffected.

## [0.1.0] - 2026-06-14

### Added

- **Initial scaffold (WS-3).** `juniper-model-core` defines the shared model-contract template
  for the Juniper ML platform, designed against two real implementers (Cascade-Correlation +
  the Δt-native LMU) per the ratified decision ledger D1–D10
  (`notes/JUNIPER_2026-06-14_JUNIPER-ML_MODEL-CORE-INTERFACE-DESIGN.md`):
  - `TrainableModel` / `GrowableModel` ABCs (`interfaces.py`) — numpy at the boundary, no
    classification assumptions in the generic surface (RK-6); `GrowableModel` kept minimal /
    provisional until RCC is the second implementer (RK-4).
  - The `TrainingEvent` vocabulary (`events.py`) and the `describe_topology()` schema
    (`topology.py`) — the model-agnostic monitoring and rendering seams.
  - The `ModelSerializer` strategy interface (`serialization.py`).
  - Inspectable validation free functions (`validation.py`): `validate_metrics`,
    `validate_topology`, `legal_event_order` — the shared behavior the ABCs deliberately
    exclude (C1).
  - The `TrainingLifecycleBase` seam (`lifecycle.py`) — declared in WS-3; body deferred to
    WS-2 (co-designed with juniper-service-core).
  - The reusable conformance kit (`conformance/`) — `TrainableModelConformance` /
    `GrowableModelConformance` plus a reference regression model that serves as the kit's own
    RK-6 canary.
- **Dependency-free contract.** `import juniper_model_core` pulls no third-party runtime
  dependency (numpy is type-annotation-only); numpy/pytest live in the `[conformance]` extra.

### Notes

- Not yet published to PyPI. Per the publish-first rule, juniper-ml's `[all]`/`[tools]` extras
  will pin `juniper-model-core` only after a TestPyPI soak (a follow-up PR).
