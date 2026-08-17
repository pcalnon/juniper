# CLI Experimentation — P4 Studies Evidence (E-A…E-H)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Sub-Project**: CLI test / validation / experimentation program (plan §10.5, P4)
**Author**: Paul Calnon
**Date**: 2026-08-09
**Status**: EXECUTED — all nine §10.5 studies complete (55/55 cells terminal-succeeded); headline finding **F-P4-1** (service-path spiral training) raised to owner
**Plan of record**: [JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §10.5
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

### E-C — noise robustness on spiral + moon (8 cells)

| cell                        | noise | val acc (train where no val) | hidden | wall (s) |
|-----------------------------|-------|------------------------------|--------|----------|
| moon-n0                     | 0.00  | 1.0000                       | 1      | 74       |
| moon-n05                    | 0.05  | 1.0000                       | 1      | 74       |
| moon-n10                    | 0.10  | 1.0000                       | 2      | 104      |
| moon-n20                    | 0.20  | 0.9650                       | 2      | 75       |
| spiral n∈{0.0,0.05,0.1,0.2} | —     | ≈0.505 (train)               | ≤1     | ≈35      |

Output (accuracy-vs-noise): the **moon curve** is the study's deliverable — flat at 1.0 through noise 0.10 (recruiting a second unit at 0.10), dipping to 0.965 at 0.20: graceful noise robustness. The four **spiral rows are F-P4-1-degenerate** (all ≈chance regardless of noise; the three that first ran inside the broken-checkout window were re-run after cascor#501 and complete mechanically with the same F-P4-1 signature).

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

## 4. Findings

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
