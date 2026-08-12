# CLI Experimentation — P4 Spiral Re-Surface Evidence

**Project**: Juniper
**Sub-Project**: juniper-ml / juniper-cascor
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-08-12

---

## 1. Summary

The P4 study suites E-A, E-B and E-C were re-run against the F-P4-1-fixed stack. **F-P4-1 is confirmed dead**: the cascor service path now trains spiral properly, recruiting hidden units up to its budget where the original campaign recruited **zero units in all twelve E-A cells**.

Two previously unknown defects were found during the re-run, both of which corrupt experiments **silently** — the affected runs report `outcome: succeeded` with exit 0 while carrying scientifically wrong numbers:

| # | Defect | Effect | Status |
|---|--------|--------|--------|
| 1 | **F-P4-1** — spiral received cascor's in-process fallback instead of the configured juniper-data dataset | 0 units, chance accuracy, `below_threshold` at iteration 1 | FIXED — juniper-ml#1055, juniper-cascor#504 |
| 2 | **GPU leak** — candidate forkserver children survive teardown holding CUDA contexts | card fills across a campaign; candidates die at instantiation; run reports `succeeded` / `no_candidate` / 1 unit | RAISED — juniper-cascor#509; worked around by reaping before every cell |
| 3 | **Stall window** — `run_suite` could not pass `--stall-seconds`, and no epoch progress is reported during candidate training | healthy large-pool cells killed at 120 s and recorded as `stalled` / 0 units | FIXED — juniper-ml#1069 (`execution.stall_seconds`) |

Because defects 2 and 3 present as plausible results rather than as errors, **the original P4 evidence for E-B and E-C is suspect** (§6). Every number in this document was collected with an explicit `oom == 0` filter and a reap before each cell.

---

## 2. What was re-run, and why

E-A's twelve cells and the spiral rows of E-B / E-C were measurements *of* F-P4-1 rather than of the cascade algorithm: the driver's spiral-only inline `dataset` source made cascor substitute its param-deaf, unit-radius in-process fallback for the configured dataset, so best-of-pool candidate correlation pinned at ≈2.7e-4 and `grow_network` broke on `below_threshold` at iteration 1.

E-B and E-C were re-run **whole** rather than only their spiral rows: the non-spiral rows are cheap at smoke budget, and one self-consistent table per suite beats splicing new spiral numbers into an old one. That decision turned out to matter — the non-spiral rows had changed too (§6).

Root cause: [`JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md`](JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md).
Original campaign: [`JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md`](JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md).

---

## 3. Method and validity controls

Stack: `util/experiment_stack.bash` per-run instances (data 8110-8139 / cascor 8230-8259), driver `util/experiments/run_experiment.py`, suite driver `util/experiments/run_suite.py`, cascor at `e1e2e38` (includes #504), juniper-ml at `3f82d77` (includes #1055). Campaign env `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`, `JUNIPER_EXP_HEALTH_TIMEOUT=180`. Strictly sequential — cascor is one-per-checkout (H-7).

Three controls, each added in response to something that had already produced bad data:

1. **Per-cell orphan reap.** `util/reap_pytest_orphans.bash` runs before **every** cell, and GPU headroom is logged alongside. Reaping once per suite is not enough: the card refills after 4-5 healthy cells.
2. **`oom == 0` filter.** A cell is admitted only if its `logs/juniper-cascor.log` contains zero `out of memory` lines. Aggregation is by `util/ad-hoc/2026-08-10_ea_aggregate_clean.py`, which keeps the newest clean run per `cell_id` across suite directories and reports anything still missing.
3. **Widened stall window** for cells whose candidate phase exceeds 120 s.

Tooling used for the campaign lives in `util/ad-hoc/` with retirement conditions in each header.

---

## 4. Results

### 4.1 E-A — cascade budget × candidate pool on spiral (12/12 clean)

Base `juniper-cascor/conf/experiments/spiral-baseline.yaml` (spiral, 500 points/arm, 3.0 rotations, noise 0.05; `max_epochs` 2000, `max_iterations` 12).

| cell | pool | unit cap | units | train acc | val acc | wall (s) | completion | best corr |
|------|-----:|---------:|------:|----------:|--------:|---------:|------------|----------:|
| c000 | 4 | 4 | 4 | 0.545 | 0.570 | 246 | `early_stopped` | 0.0727 |
| c001 | 8 | 4 | 4 | 0.605 | 0.545 | 353 | `early_stopped` | 0.1382 |
| c002 | 16 | 4 | 4 | 0.616 | 0.610 | 513 | `early_stopped` | 0.0727 |
| c003 | 4 | 8 | 8 | 0.635 | 0.625 | 447 | `early_stopped` | 0.1427 |
| c004 | 8 | 8 | 8 | 0.631 | 0.595 | 695 | `early_stopped` | 0.1382 |
| c005 | 16 | 8 | 8 | 0.630 | 0.580 | 870 | `early_stopped` | 0.2696 |
| c006 | 4 | 16 | 12 | 0.615 | 0.615 | 599 | `max_iterations` | 0.1822 |
| c007 | 8 | 16 | 12 | 0.661 | 0.645 | 885 | `max_iterations` | 0.1971 |
| c008 | 16 | 16 | 12 | 0.620 | 0.620 | 1258 | `max_iterations` | 0.2696 |
| c009 | 4 | 32 | 12 | 0.615 | 0.615 | 596 | `max_iterations` | 0.1822 |
| c010 | 8 | 32 | 12 | 0.661 | 0.645 | 858 | `max_iterations` | 0.1971 |
| c011 | 32 | (5000 ep) | 12 | 0.638 | **0.670** | 2494 | `max_iterations` | **0.4195** |

Original campaign, every one of these twelve cells: **0 hidden units, chance accuracy**.

### 4.2 E-B — dataset difficulty at smoke budget (6/6 clean)

Base `spiral-smoke.yaml` (`max_epochs` 50, `max_iterations` 2, `max_hidden_units` 2, pool 4).

| generator | units | train acc | val acc | completion |
|-----------|------:|----------:|--------:|------------|
| moon | 2 | 0.998 | **1.000** | `early_stopped` |
| gaussian | 2 | 0.990 | 0.994 | `early_stopped` |
| circles | 2 | 0.955 | 0.965 | `early_stopped` |
| xor | 2 | 0.951 | 0.960 | `early_stopped` |
| checkerboard | 2 | 0.458 | 0.475 | `early_stopped` |
| spiral | 2 | 0.575 | 0.350 | `early_stopped` |

### 4.3 E-C — noise robustness at smoke budget (8/8 clean)

| dataset | noise | units | train acc | val acc |
|---------|------:|------:|----------:|--------:|
| spiral | 0.00 | 2 | 0.656 | 0.488 |
| spiral | 0.05 | 2 | 0.575 | 0.350 |
| spiral | 0.10 | 2 | 0.572 | 0.363 |
| spiral | 0.20 | 2 | 0.619 | 0.488 |
| moon | 0.00 | 1 | 1.000 | 1.000 |
| moon | 0.05 | 1 | 1.000 | 1.000 |
| moon | 0.10 | 2 | 0.998 | 1.000 |
| moon | 0.20 | 2 | 0.968 | 0.965 |

---

## 5. Findings

**F-1 — the budget surface exists.** Units track the unit cap (4 → 4, 8 → 8, 16 → 12), wall time scales 246 s → 2494 s, and completion reasons are legitimate (`early_stopped` / `max_iterations`) rather than `below_threshold`. Candidate correlation is one to two orders of magnitude above the F-P4-1 signature.

**F-2 — `max_iterations`, not `max_hidden_units`, is the binding constraint.** Cascade installs one unit per iteration and `spiral-baseline.yaml` sets `max_iterations: 12`, so no cell can exceed 12 units. The `cap: 16` and `cap: 32` rows are therefore *the same experiment*, and they came back **bit-identical** (c006 ≡ c009 at val 0.615 / corr 0.182186; c007 ≡ c010 at val 0.645 / corr 0.197113). That identity doubles as a reproducibility check on the whole harness. **Any future E-A must raise `max_iterations` alongside the cap**, or half the grid is wasted.

**F-3 — candidate pool raises correlation, at a fixed unit count.** Holding units at 12: 0.1822 (pool 4) → 0.1971 (pool 8) → 0.2696 (pool 16) → 0.4195 (pool 32), monotone. At smaller unit budgets the ordering is noisy (the cap-4 row runs 0.0727 / 0.1382 / 0.0727), because `best corr` is a maximum over rounds and more rounds means more draws. Correlation is the quantity the pool improves; see F-4.

**F-4 — pool size does not translate into accuracy.** Validation accuracy spans 0.545-0.670 with no systematic ordering by pool: the largest pool is best in the cap-4 row and worst in the cap-8 row. With one seed per cell the within-row spread (0.03-0.065) is not distinguishable from seed noise. **A better candidate is not the same as a better network.**

**F-5 — spiral remains hard at this budget.** The best cell reaches 0.670 validation accuracy, far above the 0.500 the broken runs sat at but far below the ≈0.995 the direct CLI reaches on a radius-10 spiral. Whether this is a budget ceiling (12 units), a scale/parameterisation difference between the service and CLI paths, or a genuine service-path limitation is **open** and is the natural successor question to F-P4-1.

**F-6 — at smoke budget, spiral is beyond budget, alongside checkerboard.** With a 2-unit cap, spiral (0.350) and checkerboard (0.475) are both at or below chance while moon/gaussian/circles/xor all clear 0.96. E-C's spiral rows are therefore **not** a usable noise-robustness measurement: the curve is flat because the unit cap binds, not because spiral is noise-robust. A meaningful spiral noise curve needs a budget nearer E-A's.

**F-7 — moon degrades gracefully.** 1.000 / 1.000 / 1.000 / 0.965 across noise 0.00-0.20, with the model spending a second unit from noise 0.10 onward.

---

## 6. Corrections to the original P4 evidence

The original campaign ran 55 cells sequentially on one GPU. Given the leak measured here (≈285 MiB per cell on an 8 GiB card), its later suites were almost certainly contaminated, and the corruption is invisible in the recorded outcome.

Direct evidence from this re-run, where the same cells were measured contaminated and clean:

| cell | contaminated | clean | delta |
|------|-------------|-------|-------|
| E-B circles | 0.715 (1 unit, `no_candidate`, 24 OOM) | **0.965** (2 units) | +0.250 |
| E-B xor | 0.875 (1 unit, `no_candidate`, 19 OOM) | **0.960** (2 units) | +0.085 |
| E-C moon-n20 | 0.860 (1 unit, 23 OOM) | **0.965** (2 units) | +0.105 |
| E-A c010 | 0.585 (12 units, 202 OOM) | **0.645** (12 units) | +0.060 |

Consequences for the published P4 document:

- Its E-B ranking ("moon/gaussian easiest → xor/circles → checkerboard beyond budget") **overstates the gap** between the easy pair and xor/circles. Cleanly, all four clear 0.96.
- Its E-C moon finding ("flat to 0.10, dip at 0.20") **overstates the dip**: 0.965, not 0.86.
- Contamination is not always a collapse. The E-A c010 row kept its full 12 units and merely lost 0.06 of accuracy — the most dangerous form, because nothing about it looks wrong.

The E-A conclusions in the original document are unaffected in direction: they were degenerate from F-P4-1, and this document supersedes them outright.

---

## 7. Recommended follow-ups

| # | Item | Owner decision |
|---|------|----------------|
| R-1 | juniper-cascor#509 — stop forkserver children outliving teardown; and independently, **do not report `succeeded` when zero candidates were installable because of allocation failures** | cascor |
| R-2 | Re-run the remaining P4 suites (E-D through E-H) under the `oom == 0` discipline, and mark the original numbers provisional until then | owner |
| R-3 | Raise `max_iterations` with the unit cap in any future E-A, per F-2 | suite design |
| R-4 | Give E-C's spiral rows an E-A-class budget, or drop them and keep E-C a moon-only noise study, per F-6 | suite design |
| R-5 | Investigate the service-vs-CLI spiral accuracy gap (F-5) | open question |
| R-6 | Adopt `execution.stall_seconds` (juniper-ml#1069) in the P4 suites and retire the ad-hoc shim | juniper-ml |

---

## 8. Reproduction

```bash
# Every cell reaps orphans first and logs GPU headroom; the aggregate admits oom == 0 only.
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_EXP_HEALTH_TIMEOUT=180 \
  util/ad-hoc/2026-08-10_p4_spiral_resurface_campaign.bash

# Cells whose candidate phase exceeds the stall window (candidate_pool_size >= 16):
#   with juniper-ml#1069 merged, set execution.stall_seconds in the suite YAML instead of the shim.
JUNIPER_SUITE_DRIVER=util/ad-hoc/2026-08-10_driver_stall_shim.py JUNIPER_EXP_STALL_SECONDS=1200 \
  util/ad-hoc/2026-08-10_ea_finish_cells.bash <CELL_ID> ...

python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py     # clean grid + missing-cell report
```

Health check before trusting any cascor experiment result:

```bash
nvidia-smi --query-gpu=memory.free --format=csv
grep -c "out of memory" <run_dir>/logs/juniper-cascor.log
```

Suspect contamination when several cells share a `best corr` to six significant figures, when a cell reports `no_candidate` at 1 unit, when wall time is implausibly short for the budget, or when results degrade with position in a campaign.

Post-campaign attest: 0 listeners on both experiment port ranges, 0 lockdirs, orphans reaped.
