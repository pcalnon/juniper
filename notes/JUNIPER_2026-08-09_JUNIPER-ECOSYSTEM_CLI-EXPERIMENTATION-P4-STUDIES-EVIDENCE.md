# CLI Experimentation — P4 Studies Evidence (E-A…E-H)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Sub-Project**: CLI test / validation / experimentation program (plan §10.5, P4)
**Author**: Paul Calnon
**Date**: 2026-08-09
**Status**: EXECUTED — all nine §10.5 studies complete (55/55 cells terminal-succeeded); headline finding **F-P4-1** (service-path spiral training) raised to owner
**Plan of record**: [JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §10.5
**Operator runbook**: [REFERENCE — P4 Campaign Suites](../docs/REFERENCE.md#p4-campaign-suites) (current 19-YAML catalog; this note's 55-cell / nine-file census is the 2026-08-09 E-A…E-H pass)
**Prior evidence**: [P0](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md) · [P1](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md) · [P2](JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P2-DATASET-MATRIX-EVIDENCE.md) · [P3](JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md)

---

## 1. Method

Nine suite definitions under `util/experiments/suites/p4/` (committed with this document), executed by the Wave-7 `run_suite.py` — per-cell `experiment_stack --up → run_experiment → --down`, registry + aggregation per suite, `--resume` for recovery.
55 cells expanded; every suite's cells driver-validated at materialisation.
Suites E-F and E-G ran in **bounded-parallel mode** (`max_parallel: 2`, the Wave-7.5 dogfood) with the H-11 thread budget recorded per cell.
Seeds fixed per base config; SUITE_DIRs (registries, aggregates, cell configs) durable under `~/.local/state/juniper-experiments/suites/`.

P4 cells ran **unscraped by design**: `run_suite` does not pass `--grafana-bridge`, so no Prometheus target files were written (the observability lane was proven in P1.6/P2/P3; the driver's own loopback `/metrics` sampling still fed each cell's `metrics_series.csv`).

## 2. Recurrence studies

### E-D — d-sweep × three primaries (9 cells, all succeeded)

CV r² (5-fold expanding walk-forward per the base config; rff readout, reference-config params — jitter 0.3 for irregular_sine, NOT the bench's 0.6, so trends are comparable but absolute values intentionally differ from `bench/results/`):

| dataset        | d=8    | d=16       | d=32       |
|----------------|--------|------------|------------|
| irregular_sine | 0.9593 | **0.9749** | 0.9694     |
| multi_sine     | 0.9895 | 0.9965     | **0.9970** |
| mackey_glass   | 0.9822 | 0.9800     | **0.9936** |

Output (r²-vs-d): irregular_sine peaks at d=16 at this jitter; the regular-grid synthetics keep improving toward d=32 (multi_sine saturating). Consistent with the bench `_D_GRID` picture.

### E-E — readout spectrum on delay_product + irregular_sine (6 cells)

| base           | linear      | rff    | mlp    |
|----------------|-------------|--------|--------|
| irregular_sine | **0.9836**  | 0.9749 | 0.9803 |
| delay_product  | **−0.0053** | 0.9083 | 0.9414 |

**The DP-3 capacity separation reproduced in service mode**: on the bilinear `delay_product` target the linear readout collapses (≈0) while rff/mlp fit (gaps **+0.91 / +0.95**); on near-linear `irregular_sine` the three readouts tie (linear marginally best). Matches the W-8 offline bench signature (+0.83/+0.87 at bench params).

Two **service-contract finds** surfaced by the first E-E run (4 cells 422-rejected; suite corrected, kept in the registry history):

1. `rff_features`/`rff_gamma` are only valid with `readout='rff'` — cells overriding the readout on an `*-rff` base must null them (the driver's `_lmu_hyperparams` omits None keys).
2. `ridge` is not applicable to `readout='mlp'` ("the MLP regularises via weight decay") — mlp cells must null `train.ridge` too.

Both are the service's validation working as designed; the suite-authoring lesson is that readout-crossing sweeps must carry the readout-specific key set per cell. One additional transient: the first irregular-mlp attempt died SIGKILL (−9) 12.7 s in and succeeded identically on `--resume --only` retry (0.9803).

### E-F — irregularity sweep (4 cells, parallel×2, all succeeded)

| jitter | 0.0    | 0.1    | 0.3    | 0.5    |
|--------|--------|--------|--------|--------|
| CV r²  | 0.9815 | 0.9807 | 0.9749 | 0.9655 |

Output (Δt-advantage vs jitter): graceful degradation — the Δt-native LMU holds r² > 0.96 through jitter 0.5. Cells completed out of order (true parallelism) with `thread_budget` recorded per row.

### E-G — CV scheme × embargo (6 cells, parallel×2, all succeeded)

| scheme    | embargo 0 | embargo 2 | embargo 5 |
|-----------|-----------|-----------|-----------|
| expanding | 0.9749    | 0.9749    | 0.9749    |
| rolling   | 0.9668    | 0.9668    | 0.9667    |

Output (CV stability): both schemes are embargo-stable to 4 decimal places at these settings; expanding is uniformly ≈0.008 higher. No instability finding.

### E-H (recurrence) — real data vs synthetic control (2 cells, all succeeded)

| cell                                                | CV r²       |
|-----------------------------------------------------|-------------|
| irregular_sine control (rff)                        | 0.9749      |
| equities_seq AAPL 2015–2022 (log_return, ridge 1.0) | **−0.1825** |

Output: the **efficient-market-ceiling sanity check holds** — real next-day log-returns sit at r² ≈ 0 (mildly negative across CV folds), not the pathological blowup class (the historical ridge=0 −4422 artifact); the ridge + log_return doctrine (recurrence#28) does its job.

## 3. Cascor studies

### E-B — dataset difficulty at a fixed smoke budget (6 cells)

Fixed budget = the `spiral-smoke` training block (`max_epochs 50, max_iterations 2, max_hidden_units 2, candidate_pool_size 4`). Val accuracy (train where val absent) vs majority class:

| cell          | val acc (train where no val) | majority | hidden units | wall (s) |
|---------------|------------------------------|----------|--------------|----------|
| spiral (base) | 0.5050 (train)               | 0.500    | 1            | 46       |
| xor           | 0.9600                       | 0.500    | 2            | 127      |
| circles       | 0.9650                       | 0.500    | 2            | 157      |
| moon          | 0.9950                       | 0.500    | 1            | 49       |
| gaussian      | 1.0000                       | 0.333    | 1            | 67       |
| checkerboard  | 0.5000                       | 0.501    | 1            | 32       |

Output — difficulty ranking at the smoke budget, with an honest re-frame: **moon/gaussian easiest** (1 unit, ≥0.995), **xor/circles middle** (2 units, ≈0.96), **checkerboard beyond this budget's capacity** (0.500 ≈ majority — the P2 under-fit observation confirmed at n=2000), and **spiral unmeasurable on the service path pending F-P4-1 (§4)**: the service terminates spiral training at ≈epoch 2 with ≤1 hidden unit at every budget tested, so a fixed-budget comparison against it is degenerate rather than "hardest".
The five stageable generators' ranking feeds the §12 difficulty axis; spiral's slot awaits the F-P4-1 resolution.

### E-C — noise robustness on spiral + moon (8 cells) — RE-MEASURED AT CAP 64, 2026-08-29

> **This table replaces the cap-12 surface published 2026-08-26** (itself a replacement for the
> 08-09/08-11 smoke-cap rows; both supersessions remain in git history). That grid's four spiral
> rows were `max_iterations`-bound at 12 units and flat at ≈0.63–0.66, and `moon-n20` was bound at
> the same 12 — a capacity artifact, not a noise result. The suite now pins the budget itself
> (ml#1409): `max_hidden_units: 64` **and** `max_iterations: 64`, on the matrix and repeated on
> each moon `include` (`expand_cells` does not hand includes the matrix). Re-measured at cascor
> **`67d7ea3`** — the T6 pin — suite dir `e-c-cascor-noise-robustness-20260829T003546Z`,
> 8/8 `succeeded`, 2,437 s. Conditions and provenance: **F-P4-7** (§4).

| cell     | generator | noise | units | epoch | train  | val        | wall (s) | completion         |
|----------|-----------|-------|-------|-------|--------|------------|----------|--------------------|
| c000     | spiral    | 0.00  | 64    | 65    | 0.8638 | **0.8050** | 491.4    | `early_stopped`    |
| c001     | spiral    | 0.05  | 64    | 65    | 0.9950 | **1.0000** | 552.0    | `early_stopped`    |
| c002     | spiral    | 0.10  | 64    | 65    | 0.9838 | **0.9800** | 499.1    | `early_stopped`    |
| c003     | spiral    | 0.20  | 64    | 65    | 0.9738 | **0.9750** | 512.3    | `early_stopped`    |
| moon-n0  | moon      | 0.00  | 2     | 3     | 1.0000 | 1.0000     | 42.8     | `early_stopped`    |
| moon-n05 | moon      | 0.05  | 1     | 2     | 1.0000 | 1.0000     | 29.7     | `early_stopped`    |
| moon-n10 | moon      | 0.10  | 3     | 4     | 1.0000 | 1.0000     | 52.0     | `early_stopped`    |
| moon-n20 | moon      | 0.20  | 32    | 33    | 0.9775 | **0.9650** | 257.7    | `below_threshold`  |

**Walls here are ADVISORY, not comparable to the T6 grid.** An unrelated 13-hour `clamscan` ran
throughout. The overhead is measurable rather than guessed: `c001` is budget-equivalent to E-I
`c001` and took 552.0 s against its 516.9 s — **+6.8%**. Accuracy is seed-deterministic and
unaffected.

Output (accuracy-vs-noise):

**The flatness was the cap.** ≈0.63–0.66 across all four noise levels becomes a curve spanning
0.805–1.000. R-4's diagnosis was correct and simply had not been carried far enough; the cap-12
reading measured the budget, exactly as the 2-unit smoke cap had before it.

**The control reproduces exactly.** `spiral-baseline` pins `noise: 0.05`, so `c001` is
**budget-equivalent** to E-I `c001` — and returns identical val (1.0000), train (0.9950), units
(64) and epoch (65). Two campaigns two days apart, different suites, different ports, and run from
a *pinned worktree* rather than the primary checkout (ml#1412). That is simultaneously a
cross-campaign determinism check and the end-to-end validation that worktree pinning reproduces
what the primary produced.

*Equivalent, not identical* — stated precisely because the determinism claim rests on it. The two
cell YAMLs differ in **three** keys, so `config_sha256` differs (`experiment.name` alone would do
that): `experiment.name`, `max_iterations` (E-I 128, E-C 64) and `outputs.max_wall_seconds` (14400
vs 3600). **Neither budget key binds.** The 64-unit stop comes from `check_hidden_units_max()`
(`len(self.hidden_units) >= self.max_hidden_units`, `cascade_correlation.py:5767`) → `early_stop` →
break at `:4955`, not from the iteration bound; and both cells finished in ~9 minutes against wall
budgets of one and four hours. `dataset_id` (`spiral-1.0.0-7a976ad4…`) and seed (20260729) are the
same.

> Note `effective_iterations = min(max_iterations, max_hidden_units)` — quoted elsewhere in this
> document and in the suite YAMLs — lives in `derive_epochs_cap` and is a **reporting/display**
> budget (the `Epoch: X / Y` denominator), *not* the enforced abort; its own docstring says so.
> Enforcement is the granular limits. The formula still predicts which cap bites first, which is
> why it is a sound planning rule — but do not cite it as the mechanism.

**`moon-n20`'s 0.975 was confounded.** Freed of the cap it grows to 32 units and lands at
**0.9650** `below_threshold` — a real measurement, and slightly *worse*: the extra capacity costs a
little generalization. The moon curve is now 1.0 / 1.0 / 1.0 / 0.965 with nothing cap-bound, and
is the study's clean deliverable.

**The spiral curve is NON-MONOTONIC, and capacity is not the dominant constraint on the dip.** noise 0.00 → 0.8050 sits
*below* noise 0.05 → 1.0000, which is backwards for a robustness curve. Noise is additive Gaussian
jitter on x and y (`SpiralGenerator._make_noise`), so the parameter is applied, and all eight cells
carry distinct content-addressed `dataset_id`s. Because every spiral cell consumed its **entire**
64-unit budget, the dip was initially confounded with starvation — E-I's saturation at noise 0.05
(cap 64 and cap 128 both 1.0000) does not transfer to noise 0.00. A one-cell probe settles it
(`util/ad-hoc/2026-08-28_ec_noise0_cap128_probe.yaml`, suite dir
`ec-noise0-cap128-probe-20260829T012038Z`):

| probe            | noise | cap | units | epoch | train  | val        | wall (s) |
|------------------|-------|-----|-------|-------|--------|------------|----------|
| noise-0 @ cap128 | 0.00  | 128 | 128   | 129   | 0.8413 | **0.8450** | 909.3    |

Doubling the budget buys **+0.04** (0.8050 → 0.8450) while the noise-0.05 row reaches 1.0000 on
*half* of it. **That comparison is what carries the conclusion**: it is between cells measured on
the same tier, under the same split roles, so capacity is **not the dominant constraint in this
range**.

> **Stated no more strongly than that, deliberately.** The probe's pre-registered rule was "jumps
> toward 1.0 → capacity; stays near 0.805 → real"; 0.8450 is neither, and the cap-128 cell *also*
> recruited exactly its cap, so no unconstrained stopping point was ever observed. Capacity is not
> excluded outright — only shown to buy little here. An earlier draft said the probe "rules out
> capacity"; it does not.

> **CORRECTION 2026-08-29 — do not read train-vs-val here as a fit diagnostic.** This paragraph
> originally argued that train accuracy falling below val (0.8638 → 0.8413 vs 0.8450) showed the
> network "is not fitting its training set", and inferred an optimization / geometry limit from
> that. **cascor#582 (open) invalidates the inference**: on the SERVICE tier `_reload_dataset` maps
> the artifact's `X_test`/`y_test` into *validation tensors* that then feed patience and early
> stopping **in-loop** (`src/api/lifecycle/manager.py:3391`), whereas the direct CLI passes no val
> tensors at all. Both noise-0 cells — the cap-64 grid row and the cap-128 probe — terminated `early_stopped`, i.e. that very series drove their stop. (Not every E-C cell did: `moon-n20` ended `below_threshold`.)
> Train sitting below an in-loop-selected val is an expected signature of that promotion, not free
> evidence about fit. The **capacity** conclusion is unaffected — it rests on the cross-cell
> comparison above, not on train-vs-val.

**The noise-free spiral is nonetheless harder for this learner at every budget tested** (0.8050 at
cap 64, 0.8450 at cap 128, against 1.0000 at noise 0.05 and cap 64) — plausibly because with zero
jitter the two arms lie exactly on a 1-D manifold with no margin anywhere. Why that is so is **not
answered here**, and the mechanism is now *less* constrained than the original wording implied;
recorded as an open item in **F-P4-7**. It is a property of the learner, not of the suite, so it
does not qualify the noise rows at 0.05 / 0.10 / 0.20.

The E-A / E-I currency caveat the old marker carried (both published grids predated cascor#514)
is resolved the same way: both were re-measured at `67d7ea3` in the same campaign — see
[E-A / E-I re-baselined](#e-a--e-i-re-baselined-2026-08-26-cascor-67d7ea3--t6) below.

### E-H (cascor) — real equities vs spiral control (2 cells)

| cell                    | val acc                | majority                  | hidden | wall (s) |
|-------------------------|------------------------|---------------------------|--------|----------|
| spiral control          | 0.5050 (train; F-P4-1) | 0.500                     | 1      | 43       |
| equities AAPL 2015–2022 | 0.5284                 | 0.5318 (up-day base rate) | 0      | 52       |

Output: the **efficient-market-ceiling check holds on the cascor side too** — next-day-direction accuracy 0.528 ≈ the up-day base rate (no exploitable signal; 0 hidden units recruited), the tabular mirror of the recurrence side's r² ≈ 0. The networked generation ran clean (1,762 samples).

### E-A — cascade budget × candidate pool on spiral (12 cells, baseline budget)

All 12 cells (4×3 grid minus exclude, plus `wide-pool-long`) completed mechanically: exit 0, walls 30–50 s, `train_accuracy ≈ 0.505`, **hidden units = 0 in every cell** (0.52 for wide-pool-long).
The intended accuracy/units/wall-clock surface is **entirely degenerate — this is the F-P4-1 measurement, not a budget surface**: at the full baseline budget (`max_epochs 2000 × max_iterations 12 × max_hidden_units ≤32`, patience 200) the service path never recruits a single candidate on spiral and reports final metrics at epoch ≈2.
The suite artifacts (12 registries, aggregates, per-cell manifests) are the reproducible evidence base for the F-P4-1 investigation.

### E-A / E-I re-baselined (2026-08-26, cascor `67d7ea3`) — T6

The post-F-P4-1 E-A grid ([R-3 re-run, 2026-08-14](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R3-EA-RERUN-EVIDENCE.md))
and the E-I capacity ladder ([2026-08-14](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-E-I-CAP-CEILING-EVIDENCE.md))
both predate cascor#514, which R-5 §5.1 made a comparability boundary. The T6 campaign re-measured
both, together with E-C above, at **one** cascor commit — `67d7ea3` (== `origin/main` at launch,
tree clean; SHA re-read and unchanged around every suite; the `campaign.jsonl` ledger in
`~/.local/state/juniper-experiments/t6-rebaseline-20260826T075112Z` is the SHA record, since the
per-cell manifest carries no git field). Suite dirs `e-a-cascor-budget-sweep-20260826T075112Z`
(12/12 `succeeded`, 1,587 s) and `e-i-cascor-cap-ceiling-20260826T081740Z` (3/3, 1,781 s). The
reference-wall columns are **context only** — they straddle #514 and #563 and are not attributable
to either (F-P4-6).

**E-A** — `max_hidden_units` × `candidate_pool_size` on spiral, `max_iterations 32` (R-3):

| cell           | pool | cap          | units | epoch | train  | val        | wall (s) | pre-#514 08-14 wall | attempt-1 08-23 wall      | completion      |
|----------------|------|--------------|-------|-------|--------|------------|----------|---------------------|---------------------------|-----------------|
| c000           | 4    | 4            | 4     | 5     | 0.6012 | 0.5900     | 49.8     | 215.3               | 285.0                     | `early_stopped` |
| c001           | 8    | 4            | 4     | 5     | 0.5700 | 0.5150     | 54.7     | 285.8               | 436.6                     | `early_stopped` |
| c002           | 16   | 4            | 4     | 5     | 0.5725 | 0.5300     | 59.7     | 437.3               | 621.3                     | `early_stopped` |
| c003           | 4    | 8            | 8     | 9     | 0.6425 | 0.6400     | 82.0     | 365.8               | 496.5                     | `early_stopped` |
| c004           | 8    | 8            | 8     | 9     | 0.6587 | 0.6300     | 84.7     | 536.4               | 571.3                     | `early_stopped` |
| c005           | 16   | 8            | 8     | 9     | 0.6212 | 0.5750     | 89.7     | 743.9               | 895.1                     | `early_stopped` |
| c006           | 4    | 16           | 16    | 17    | 0.6100 | 0.6100     | 129.8    | 556.6               | 671.8                     | `early_stopped` |
| c007           | 8    | 16           | 16    | 17    | 0.6675 | 0.6550     | 134.9    | 807.3               | 1052.7                    | `early_stopped` |
| c008           | 16   | 16           | 16    | 17    | 0.5425 | 0.5200     | 150.4    | 1494.3              | 1749.9                    | `early_stopped` |
| c009           | 4    | 32           | 32    | 33    | 0.6975 | 0.6950     | 225.3    | 937.9               | 676.9                     | `early_stopped` |
| c010           | 8    | 32           | 32    | 33    | 0.8825 | **0.8400** | 245.3    | 1319.4              | 146.4 (`torn_down_early`) | `early_stopped` |
| wide-pool-long | 32   | 24 (5000 ep) | 24    | 25    | 0.9437 | **0.9200** | 280.6    | 2893.1              | 3616.1 (`timed_out`)      | `early_stopped` |

**E-I** — capacity ladder at pool 8, `max_iterations 128`:

| cell | cap | units | epoch | train  | val        | wall (s) | pre-#514 08-14 wall | completion      |
|------|-----|-------|-------|--------|------------|----------|---------------------|-----------------|
| c000 | 32  | 32    | 33    | 0.8825 | 0.8400     | 260.4    | 1497.4              | `early_stopped` |
| c001 | 64  | 64    | 65    | 0.9950 | **1.0000** | 516.9    | 2907.1              | `early_stopped` |
| c002 | 128 | 128   | 129   | 0.9975 | **1.0000** | 1004.2   | 4243.6              | `early_stopped` |

Reading, in the order the tables support it:

1. **The surface is cap-bound everywhere, as under R-3.** Every E-A cell stops `early_stopped` with
   `units == max_hidden_units` (4/8/16/32; `wide-pool-long` at the inherited 24), and every E-I rung
   fills its cap. Attempt 1's cap-16/cap-32 cells at `341ffa3` had stalled at 15 units
   `below_threshold`; at `67d7ea3` that stall does not occur. The R-3 control therefore still holds:
   caps bind, and the comparison across cells is a capacity comparison.
2. **The control cell reproduces exactly.** E-I c000 (pool 8 / cap 32 / 128 iterations) and E-A c010
   (pool 8 / cap 32 / 32 iterations) report identical trajectories — 32 units, epoch 33, train
   0.8825, val 0.8400 — as the 2026-08-14 pair did (0.7200 / 0.7350 then). With the cap binding
   before the iteration budget matters, the two configs are the same run, and at `67d7ea3` (which
   includes cascor#566's network-owned candidate RNG) they land on the same numbers.
3. **Accuracy at equal capacity is higher than the pre-#514 grid**, most at the top of the ladder:
   cap 32 / pool 8 val 0.735 → **0.840**; `wide-pool-long` (24 units) 0.665 → **0.920**; E-I cap 64
   0.945 → **1.000** and cap 128 0.995 → **1.000**. The spiral (`n_rotations 3.0`) ceiling the
   2026-08-14 ladder reached at 128 units is now reached at **64**. Caps 4–16 move within noise
   (±0.05, both directions). This is an observation across the whole #514 … #589 span, **not** an
   attribution: #514 (candidate patience reaching the pool), #566 (seeding reset) and the training
   fixes between them are all inside the interval, and no control arm at a single intermediate
   commit was run (F-P4-6).
4. **Wall time is 4–12× shorter than either reference**, and the ratio grows with pool size (pool 4:
   ≈4–6×, pool 16: ≈10–12× vs attempt 1). That shape matches cascor#563 — the logger's frame
   inspection was ~78% of candidate-**worker** CPU, so the saving scales with the number of workers —
   and is the reason the reference walls cannot be read as a #514 cost (F-P4-6). Within this
   campaign the walls are comparable to each other: E-A 1,587 s, E-I 1,781 s, E-C 622 s, 66 min
   end to end on a host at load 2.3/3.5/3.8 at launch with no maintenance process running.

## 4. Findings

### F-P4-7 — E-C re-measured at cap 64: the flat spiral curve was the cap; the noise-0 dip is not mainly capacity

**Status: the E-C study is COMPLETE. One learner-level question is raised and left open.**

F-P4-6 closed the T6 re-baseline but recorded E-C's spiral rows as still capacity-bound — one cap
up from the R-4 finding, with the inherited `max_iterations: 12` playing the unit cap's old role.
The prescription carried in that item, *"an E-I-class `max_iterations` (≥ 64)"*, was **incomplete
and would not have worked**: `derive_epochs_cap` computes
`effective_iterations = min(max_iterations, max_hidden_units)` and `spiral-baseline` caps
`max_hidden_units: 24`, so raising iterations alone moves the bind from 12 to 24 — still far short
of where spiral resolves. Both knobs move together (ml#1409), which is what E-A (`[32]`) and E-I
(`[128]`) had already been doing since R-3.

**Run conditions.** cascor `67d7ea3`, the T6 pin, from a **pinned worktree** rather than the
primary checkout — the primary was in use by an unrelated live E2E stack, and ml#1412 made that a
non-blocker. The pin was verified three independent ways rather than trusted: the import-provenance
probe (`util/ad-hoc/2026-08-26_cascor_import_provenance.py`) resolved all six top-level cascor
modules inside the worktree; the live service's `/proc/<pid>/cwd` was that worktree's `src`; and
`JUNIPER_CASCOR_GIT_SHA` read `67d7ea359f2b`. The third alone is **vacuous** — the launcher stamps
it from the requested tree, so it cannot disagree — and is evidence only alongside the other two.
`base_config` resolved through the same pinned tree (`JUNIPER_EXP_PROJECT_DIR`), so this is pinned
code *and* pinned config, not the mixed tree ml#1412 also fixed.

**Results** (§3): the spiral curve gains real structure (0.805 / 1.000 / 0.980 / 0.975 against a
flat ≈0.63–0.66); `moon-n20`'s cap-bound 0.975 resolves to a genuine 0.965 at 32 units; and `c001`
reproduces E-I `c001` **exactly** on val, train, units and epoch — a cross-campaign determinism
check that doubles as end-to-end validation of worktree pinning.

**Open — the noise-0 dip is not mainly a budget effect.** The curve is non-monotonic:
noise 0.00 (0.8050) sits below noise 0.05 (1.0000). A cap-128 probe shows capacity is not the
dominant constraint — doubling the budget moves val only 0.8050 → 0.8450 while noise 0.05 saturates
at 1.0000 on half of it (it does **not** exclude capacity outright; see §3's caveat). That
**cross-cell comparison, on one tier under identical split roles, is the whole basis**; see §3's
CORRECTION 2026-08-29 for why the train-vs-val reading originally offered alongside it does not
survive cascor#582 (the service promotes `X_test`/`y_test` to in-loop validation that drives the
early stop; every cell here terminated `early_stopped`). *Why* the noise-free spiral is harder is
unanswered and now less constrained than first written — a cascor-learner investigation rather than
a suite change. It does not qualify the 0.05 / 0.10 / 0.20 rows.

**Scope, restated because this grid publishes an accuracy jump.** The cap-12 → cap-64 improvement
is a BUDGET change measured at one cascor sha; no part of it is attributed to any commit. Attribution
across the #514 … #589 interval still needs the control arm F-P4-6 named and never budgeted.

**Two rows remain cap-terminated.** `c002` (0.9800) and `c003` (0.9750) recruited exactly their
64-unit cap and were never probed above it — only noise 0.00 was. Do not read this grid as "nothing
is cap-bound"; read it as "the 12-unit iteration cap no longer binds, and the one row probed above
64 gained +0.04".

> **`completion_reason: early_stopped` does NOT mean "converged before the cap."** Hitting the unit
> cap *produces* that label:
> `early_stop = early_stopping and (train_accuracy_reached or max_units_reached or patience_exhausted)`
> (`src/cascade_correlation/cascade_correlation.py:5697`, set at `:4954`). `max_iterations` appears
> only on the for-else, so a run that exhausts its UNIT cap reports `early_stopped` while a run that
> exhausts its ITERATION cap reports `max_iterations`. Every spiral cell in this grid, in E-I, and
> in the cap-128 probe lands on its own cap while reporting `early_stopped`. **Read `units` against
> `max_hidden_units`; never infer convergence from the label.**

**Also confirmed in the field:** every cell's manifest carries
`teardown_preempt: {"attempted": false, "settled": null}` — all eight succeeded, which is terminal
service-side, so ml#1408's teardown stop correctly never fired. The regression suite asserts this;
this is the live confirmation.

**Not measured.** Walls are advisory — an unrelated 13-hour `clamscan` ran throughout, costing a
measured **+6.8%** on the budget-equivalent `c001` (552.0 s vs E-I's 516.9 s). Every cell also logs
the `max_epochs` / `output_epochs` split warning, inherited from `spiral-baseline`; the T6 grids ran
under the identical condition, so the comparison is like-for-like, and it would only bite a
CLI-vs-service comparison, which this is not.

### F-P4-6 — the T6 re-baseline: first attempt partial (timings NOT usable); second attempt complete

**Status: RESOLVED 2026-08-26.** The re-baseline ran to completion on the second attempt — 23/23
cells at cascor `67d7ea3`, published in §3 ([E-C](#e-c--noise-robustness-on-spiral--moon-8-cells--re-measured-at-cap-64-2026-08-29),
[E-A / E-I](#e-a--e-i-re-baselined-2026-08-26-cascor-67d7ea3--t6)); the record of that run is at
the end of this finding. The first attempt's analysis is kept below because its conclusion —
**do not cite its wall-clock deltas as a cascor#514 measurement** — still governs how the
reference-wall columns in §3 must be read.

The T6 re-baseline (E-A → E-I → E-C against one post-#514 cascor) was first attempted 2026-08-23
with cascor pinned at `341ffa3`. **E-A completed 10 of 12 cells in 11,221 s; E-I was killed
5 m 07 s in (307 s, corroborated from `teardown.json` mtimes); E-C never started.** Artifacts:
`~/.local/state/juniper-experiments/t6-rebaseline-20260823T200328Z` and suite dir
`e-a-cascor-budget-sweep-20260823T200329Z`. Reference data only — see the second-attempt record
for why it was not resumed.

Matched-cell wall time against the pre-#514 grid (2026-08-14) came out **+16.9%** (6,381 s →
7,457 s), nine of ten cells slower (+6.5% to +52.8%) and one *faster* (−27.8% at pool 4 / cap 32).

**That number is confounded and must not be attributed to #514.** The host was chosen on a
load-average lull of 4.09; across the campaign the 15-minute average was **19.55**, with a
`duplicati` backup consuming >200% CPU throughout. A single cell moving the other way is also not
what a uniform code-induced slowdown looks like. Separating the two needs a control — either a
re-run on a genuinely quiet host, or the same grid re-measured at the pre-#514 commit under the
same conditions. The re-baseline was therefore re-run from scratch (second attempt, below); the
E-C table at §3 has been replaced and its KNOWINGLY STALE marker lifted.

Two cell-level results DO stand, because neither depends on wall-clock precision:

- **`wide-pool-long` (pool 32 / `max_epochs` 5000) no longer fits the inherited 3,600 s budget.**
  It ran 2,893.1 s pre-#514 and was stopped at 3,616.1 s. The driver stopped it and wrote an honest
  `timed_out` manifest — the ordering ml#1200 fixed — so the truncation is recorded rather than
  silent. Budget raised to 5,400 s (still 1,800 s below the suite's 7,200 s subprocess timeout, so
  the driver still wins); rationale in the suite file. Note the suite had already raised the
  *timeout* 3,600 → 7,200 "for the R-3 unit budget" while leaving the driver's budget at the base's
  3,600 — headroom the driver could never reach. This is the other half of that change.
- **`c010` (pool 8 / cap 32) was killed externally, not by the experiment.** `torn_down_early`,
  exit 3 (`EXIT_UNREACHABLE`), service `Connection refused` 141 s in, with no CUDA OOM, no kernel
  OOM and 60 GB RAM free. Infrastructure, not a finding; the cell needs re-running.

**Method note that generalises — long campaigns cannot run as harness background tasks.** The
campaign itself was killed, as was `c010`'s service. This is the population documented in
[`JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SAFE-MERGE-KILL-FORENSICS.md`](JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SAFE-MERGE-KILL-FORENSICS.md)
§3.4: the host `[bg]` worker holds a ~3,600 s lease and the task dies when it expires, with no
per-task cause — 19 such kills were catalogued before this one. A 7–9 h campaign must therefore be
launched **detached** (`setsid`), not via a tracked background task, and the driver
(`util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash`) re-checks the cascor SHA around every suite
so a kill-and-restart cannot silently split the baseline across two commits.

A killed campaign also leaves its stack up, and the reaper **protects** it — a live run-dir pidfile
still exists even though the driver is gone (ml#1133's guard inverted into a false positive). Tear
it down with `experiment_stack.bash --down <RUN_ID>` rather than waiting for the reaper. The
2026-08-21 orphan found during T1 was the same class.

**Second attempt (2026-08-26) — complete.** Launched 02:51 CDT (07:51:12Z) from a juniper-ml
worktree at `main` `c36bc886` via `util/ad-hoc/2026-08-25_t6_launch.bash` →
`2026-08-23_t6_rebaseline_campaign.bash`, detached (`setsid nohup`); interpreter JuniperCascor1
Python 3.13.13 (the attempt-1 provenance interpreter). cascor pinned at **`67d7ea3`** — the primary
checkout, == `origin/main`, tree clean, re-read unchanged before and after each of the three
suites (ledger `t6-rebaseline-20260826T075112Z/campaign.jsonl`: `start`, three `suite_start` /
`suite_end` pairs with `sha_before == sha_after`, `complete rc=0`). **23/23 cells `succeeded`**:
E-A 12 in 1,588 s, E-I 3 in 1,781 s, E-C 8 in 623 s; `CAMPAIGN COMPLETE` at 08:57:44Z, 66 min
after launch. Attempt 1 was **not** resumed: a `--resume` would have kept ten cells measured at
`341ffa3` beside two at `67d7ea3`, across #563 (wall) and #566 (numerics) — the exact
incomparability the re-baseline exists to remove.

Host conditions, this time measured on the right instruments: the campaign waited for a drain
watch gating on the **15-minute** load average (< 4.5), **live** CPU of maintenance processes
(none above 20% — `top`'s second frame, because `ps %CPU` is a lifetime average and had read an
idle `duplicati-server` at 45% all of 2026-08-25, holding the previous session's watch shut for
a day after the backup ended), GPU below 1,200 MiB and every experiment / E2E port clear, for
two consecutive minutes. At launch: load `2.26 / 3.48 / 3.76`, GPU 907 MiB, zero maintenance
processes, reaper clean, port-lock root empty. Four peer sessions held GPU work and a checkout
freeze on the cascor primary between the launch and completion announcements; the freeze was
respected (the ledger shows it). Post-campaign attest: experiment ports clear, zero port locks,
GPU 722 MiB, reaper clean. **cascor#589** (shutdown joins training before uvicorn's SIGTERM
re-raise) is inside the pin, and the 23 inter-cell stops left zero `/dev/shm` `juniper_train_*` /
`sem.mp-*` objects, zero `training thread still running` warnings, and nothing for the narrow
orphan sentinel (`util/ad-hoc/2026-08-25_t6_orphan_sentinel.bash`, run beside the campaign) to
reap — **but read that correctly**: every one of the 23 teardown SIGTERMs landed on a service
whose training had *already ended* 2.0–6.9 s earlier (`Training ended` precedes `shutting down`
in all 23 engine logs, lifecycle shut down in 0.00 s; scan by the stop-fix session,
`reports/stop-during-training-2026-08-25/t6_production_verification_scan.txt`), because
`run_experiment.py` drives training to a terminal state before teardown and no cell timed out.
The campaign therefore confirms the fix does **no harm on the idle-stop path** across 23 real
stops; it did **not** exercise the stop-during-training path #589 was written for. ~~A live run of
both triggers at `67d7ea3` is still owed (that session's item, not T6's).~~ **DISCHARGED
2026-08-26 by ml#1397** (*"docs(shm): live-verify the stop-during-training fix on deployed
`67d7ea3`; T6 tested only the idle path"* — the second clause is the one this paragraph is about,
so it is quoted in full), by the stop-fix session as expected; its body records live runs of **both**
triggers (`hidden_unit` and `candidate_round`). This paragraph's "still owed" stood stale for three
days and is corrected here. The campaign finished five hours before the 09:00 CDT production
backup, so no maintenance contention occurred.

What this resolves and what it does not:

- **Resolved**: the three grids are comparable to each other at one SHA, the E-C surface is
  current, and the E-A / E-I currency caveat is discharged. The `wide-pool-long` budget question
  is moot at this commit (280.6 s against a 5,400 s budget) — the budget stays, as headroom.
- **Not resolved, by design**: a "#514 cost N%" figure. The re-baselined walls are 4–12× *shorter*
  than both the pre-#514 grid and attempt 1, dominated by #563; the +16.9% above and the
  accuracy gains in §3 sit across the same multi-commit span. Attribution would need the control
  arm this finding named from the start (the same grid at a single intermediate commit under
  equal conditions), which was neither scheduled nor budgeted.
- ~~**Open, owner decision**: E-C's spiral rows are `max_iterations`-bound at 12 units under the
  inherited `spiral-baseline` budget (§3), so a spiral noise-robustness curve still needs an
  E-I-class `max_iterations` (≥ 64) on those four cells.~~ **CLOSED 2026-08-29 by
  [F-P4-7](#f-p4-7--e-c-re-measured-at-cap-64-the-flat-spiral-curve-was-the-cap-the-noise-0-dip-is-not-mainly-capacity).**
  Note the prescription recorded here was **incomplete**: `≥ 64` on `max_iterations` alone moves the
  bind to `spiral-baseline`'s `max_hidden_units: 24`, not to 64, because
  `effective_iterations = min(max_iterations, max_hidden_units)`. Both knobs were required.

Method notes that generalise, added by the second attempt: a host-drain gate must read
instantaneous CPU, not `ps %CPU`; a freed GPU window on this host is claimed by another session
within a minute, so peer agreements come *before* the window and the launch re-checks every gate
in the same second it launches; and a monitor that fires while its session is not awake is
indistinguishable from one that never fired — the drain watch fired at 19:33 the evening before
and the session was not re-invoked until 02:30, and the completion at 03:58 was not acted on
until 12:30 — so completion obligations to peers must be discharged by whichever process is
awake, and the ledger's terminal line is the authoritative signal, not the announcement.


### F-P4-1 — the cascor SERVICE path does not train spiral (study-blocking for spiral surfaces; raised to owner)

At **every budget tested** — the smoke block (E-B/E-C/E-H control cells) and the full baseline block (`max_epochs 2000 × max_iterations 12 × max_hidden_units ≤32`, patience 200; all 12 E-A cells) — a service-mode spiral run completes in 30–50 s with `train_accuracy ≈ 0.505` (chance), **0–1 hidden units recruited**, and `metrics_final` reporting epoch ≈ 2.
Retroactively, **P1.1's certified reference run shows the identical signature** (0.505 / f1 0.505 / roc_auc 0.59 / 1 unit / epoch 2) — P1–P3 validated mechanics (exit codes, plots, artifacts, parity), and P4's studies are the first to measure spiral learning on this path.
The contrast that localises it: the **direct-CLI** path on the same machine trains spiral hard (the P1.2/F-P1-3b profiling runs ground through 156-candidate pools for minutes), and the service path **does** train the easy staged tasks (xor 0.96 / moon 1.0 / gaussian 1.0 recruit units normally) — so the defect class is service-boundary training-termination semantics (early-stop / convergence-threshold / iteration handling around `POST /v1/training/start` params), not the trainer itself.
Everything needed to reproduce is in the suite artifacts (12 E-A registries + manifests).
Until resolved, E-A's budget surface and the spiral rows of E-B/E-C are **measurements of F-P4-1, not of spiral difficulty**.

> **Correction (2026-08-15) — the supporting parenthetical in the paragraph above is wrong; the conclusion is not.**
> "the P1.2/F-P1-3b profiling runs **ground through 156-candidate pools for minutes**" mis-reads a *block*
> as a *workload*. Those runs were not computing for minutes: training finished in ~39 s and the process
> then parked in a post-training `plt.show()`
> ([F-P1-3 root cause](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md), cascor#517).
> That is the same error F-P1-3b made, reused here as evidence.
>
> **The contrast itself survives on better evidence.** The direct CLI *does* train spiral — arm A/C
> reach train ≈ 0.956–0.970 — so "CLI trains spiral, service did not" holds; only the "for minutes"
> timing claim is withdrawn. Do not cite this parenthetical as evidence of direct-CLI slowness: the
> [head-to-head](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md)
> measured no path gap at all.

### Operational findings (the campaign's own lessons)

1. **Cascor cell failures partition into three honest classes**:
    (a) *contention* — running the two study groups concurrently pushed cascor cold-starts past the 90 s health gate (the first-pass E-B trio and early E-C cells);
    (b) *a broken-checkout window* — between 08:17 and 08:48 UTC a concurrent session's `.h5` snapshot-debris cleanup (`cascor@4081f5b`, the F-P1-4 item) swept five snapshot **modules** with it, making every cascor boot die on `ModuleNotFoundError: snapshots.snapshot_errors`;
      - another concurrent session diagnosed and restored them as **cascor#501** within ~31 minutes,
      - after which the same cells passed unchanged
        - the E-B retries at the raised 180 s gate fell inside this window — their failures were the breakage, not timing;
    (c) *one transient SIGKILL* (irregular-mlp, succeeded identically on retry).
    (d) Recommendations adopted:
      - `JUNIPER_EXP_HEALTH_TIMEOUT=180` for campaign use,
      - study groups sequential unless recurrence-light,
      - the health gate cannot distinguish "slow boot" from "crashed at import"
        - this is a launcher improvement worth a follow-up
        - a dead-process fast-fail would have turned 180 s waits into instant, correctly-classified failures.
    (e) An operator error is recorded honestly:
      - the first E-B retry was itself launched concurrently with E-C, violating the one-cascor-per-checkout doctrine (H-7) for that window.
2. **Session-restart resilience**: a mid-campaign Claude session restart orphaned two suite chains.
    - Recovery was exactly the §13 design: append-only `registry.jsonl` (last-row-wins) + `--resume` skipped every succeeded cell across four resume passes; `list_runs --state stale` found the one mid-flight corpse run and `--prune --yes` removed it; two stale port lockdirs (verified listener-free) were cleared by hand — the open-#979-class residual.
3. **Bounded-parallel worked as shipped**: E-F/E-G's `max_parallel: 2` completed cells out of order with H-11 budgets recorded and lock-safe registries — the Wave-7.5 surface's first production use.
4. **E-E service-contract finds** (§2): readout-crossing sweeps must carry readout-consistent key sets (`rff_*` only with rff; no `ridge` with mlp) — the service's fail-loud validation working as designed, now encoded in the committed suite.

## 5. Acceptance

Every cell inherits the P2 per-dataset acceptance (§10.5): **55/55 cells terminal-succeeded** (driver exit 0 + `acceptance: true` manifests) after the resume passes; per-suite `aggregate.csv` + `REPORT.md` + `suite_manifest.json` written for all nine suites (suite-level evidence per §10.5); per-cell teardown throughout.
Post-campaign attest: both experiment port ranges empty, zero port lockdirs, zero stale runs (`list_runs`), the one mid-flight corpse pruned. Registry history preserves every failed/retried attempt — nothing was rewritten.

## 6. Program state

P0–P3 ✓ · Wave 4 ✓ · Wave 5 ✓ · Wave 6 ✓ · Wave 7 ✓ · **P4 ✓ (this document)**.
The §10.5 outputs now exist for all nine studies.
Raised to owner from this phase: **F-P4-1** (service-path spiral training termination — the priority follow-up; blocks meaningful E-A/E-B/E-C spiral surfaces and re-frames the P1.1 reference).
Remaining program items: W-12/Q-7 (csv_import corpus — parked), Q-6 (log-dir override; would retire the one-cascor-per-checkout rule and unlock cascor-parallel suites), F-P1-2 (Grafana render — context package in P3), PF threshold ratification (§12), and the §12 perf lane proper (F-P1-3b profiling) — for which the PF suites and the E-B difficulty ranking are now standing inputs.

> **Update (2026-08-15) — register refresh.** Two entries above have moved:
>
> - **F-P4-1** is **ROOT-CAUSED and fixed**, no longer study-blocking. The cause was the spiral-only
>   inline `dataset` source making cascor materialize its in-process fallback (unit-radius, params
>   silently ignored) instead of the configured juniper-data dataset; spiral now stages like every
>   other generator
>   ([F-P4-1 root cause](JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md);
>   fidelity fix cascor#504 merged, candidate-param plumbing gap cascor#505 closed).
>   Its "raised to owner / priority follow-up" framing above is therefore spent, and the claim it
>   rested on — that the service tier is handicapped — is **false**, confirmed three independent ways
>   (ml#1093, E-I, and the
>   [head-to-head](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md)).
> - "the §12 perf lane proper (**F-P1-3b profiling**)" — F-P1-3b is **REFUTED** (§5 of the head-to-head;
>   withdrawn in the [F-P1-3 root cause](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md)).
>   The perf lane remains open on the PF suites and the E-B ranking; it no longer has an F-P1-3b premise.
>
> **W-12/Q-7, F-P1-2, PF threshold ratification and Q-6 are unchanged and still open.** On **Q-6**
> specifically, this arc supplied the field evidence the plan anticipated: H-7's "accepted residual
> risk" materialized. The arm A/B root-cause evidence was **lost** because the runs wrote to a shared
> checkout's `logs/juniper_cascor.log`, which the live `:8202` service rotated away mid-arc. The
> current mitigation is the one-cascor-per-checkout rule (run experiments from a dedicated worktree) —
> which is exactly the rule a `JUNIPER_CASCOR_LOG_DIR` override would retire. Recommend resolving Q-6
> **yes**; it is now a demonstrated evidence-integrity issue, not only a concurrency nicety.
>
> **Update (2026-08-16) — Q-6 is RESOLVED; the two Q-6 claims above are superseded.** The block
> immediately above was written hours before the fix merged, so both of its Q-6 statements are now
> stale and must not be picked up as work:
>
> - "W-12/Q-7, F-P1-2, PF threshold ratification and **Q-6** are unchanged and still open" — Q-6 is
>   **closed**. The other three are unchanged and still open.
> - "**Recommend resolving Q-6 yes**" — that recommendation was **accepted and executed**.
>
> Likewise in §6's original paragraph: "Remaining program items: … **Q-6** (log-dir override; would
> retire the one-cascor-per-checkout rule and unlock cascor-parallel suites)" — no longer a remaining
> item. `JUNIPER_CASCOR_LOG_DIR` ships in **cascor#523** (merged `3909d275`; direct CLI at
> `src/cascor_constants/constants.py:434-438`, service at `api/observability.py::_resolve_log_dir` and
> `api/service_launcher.py::_resolve_log_dir`, both reading the env at *call* time), and **ml#1120**
> exports it per run at all three `cascor_up` sites in `util/experiment_stack.bash`. Unset/blank keeps
> `<repo>/logs` byte-identically.
>
> This note's diagnosis was right and is worth preserving: the arc's lost arm A/B evidence was an
> **evidence-integrity** failure, not a concurrency nicety, because cascor's parent logger writes only
> to that file — a second process rotates the evidence away rather than interleaving it.
>
> **One half of the consequence did not follow.** "unlock cascor-parallel suites" has **not** happened:
> `util/experiments/run_suite.py:112` still refuses `app: cascor` with `parallel > 1`, because
> `run_suite` cannot verify the *installed* cascor honours the override — against a pre-#523 cascor the
> export is silently ignored and parallel cells race the log again with no signal. That needs a cascor
> version floor at suite load, and **no released cascor carries #523 yet** (PyPI latest `0.9.0`, cut
> before the merge). See the plan's Wave 5 table and §15.2 Q-6.
