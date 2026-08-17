# CLI Experimentation — E-I: the spiral capacity ceiling

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-ml / juniper-cascor
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-14

E-I continues E-A's capacity column upward. Suite `e-i-cascor-cap-ceiling-20260814T091542Z`,
3/3 cells `succeeded`, all screened `oom == 0`, 144.1 min total.

E-A under R-3 ([evidence](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R3-EA-RERUN-EVIDENCE.md),
ml#1086) made the `max_hidden_units` cap bind for the first time and reported best val **0.735**
at cap 32 / pool 8 — but 32 was where the *axis* ended, not where the model stopped improving,
and that note said so: accuracy was "still rising with unit count at the top of the sweep". This
suite doubles the cap twice more at fixed pool 8.

---

## 1. The ladder

| cell | cap | units | epoch | train  | val        | val loss | F1    | ROC-AUC   | wall   | completion      | best corr |
|------|-----|-------|-------|--------|------------|----------|-------|-----------|--------|-----------------|-----------|
| c000 | 32  | 32    | 33    | 0.7200 | 0.7350     | 0.1650   | 0.735 | 0.834     | 1497 s | `early_stopped` | 0.425     |
| c001 | 64  | 64    | 65    | 0.9613 | 0.9450     | 0.0748   | 0.945 | 0.982     | 2907 s | `early_stopped` | 0.425     |
| c002 | 128 | 128   | 129   | 0.9975 | **0.9950** | 0.0223   | 0.995 | **1.000** | 4244 s | `early_stopped` | 0.963     |

Joined to E-A's pool-8 column, the full capacity curve is:

| units | 4     | 8     | 16    | 32    | 64    | 128       |
|-------|-------|-------|-------|-------|-------|-----------|
| val   | 0.545 | 0.595 | 0.610 | 0.735 | 0.945 | **0.995** |

### 1.1 The control holds exactly

c000 is a control, not a measurement. `seed_policy: fixed` leaves `experiment.seed` and
`dataset.params.seed` at the baseline's `20260729`, and all three cells resolved to the **same
content-addressed `dataset_id`** (`spiral-1.0.0-7a9…`), so c000 trains the same network on the
same data as E-A's c010.

|                     | units | train  | val    | best corr |
|---------------------|-------|--------|--------|-----------|
| E-A c010 (recorded) | 32    | 0.7200 | 0.7350 | 0.425     |
| E-I c000 (this run) | 32    | 0.7200 | 0.7350 | 0.425     |

Identical on every trained quantity. The stack has not drifted, and the two extra override keys
c000 carries are inert exactly as designed — which is the part that matters, because the 64 and
128 cells depend on `max_iterations` beyond the cap being harmless. (Wall differs, 1497 s vs
1319 s: machine load, not trajectory.)

### 1.2 The ceiling is ≈0.995, and it is reached

Doubling capacity twice takes val from 0.735 to **0.995**, with ROC-AUC at exactly **1.000** and
a train/val gap of 0.25 pp (0.9975 / 0.9950). On a spiral generated at `noise: 0.05` that is
essentially the Bayes limit: there is at most half a point left anywhere.

The steepest gain is 32 → 64 (+0.210), not 64 → 128 (+0.050) — the curve is decelerating into
the ceiling rather than still climbing linearly. Note also that val exceeded train at 32 units
(0.735 vs 0.720) and only crosses to a normal, mild generalisation gap once the model has enough
capacity to actually fit the problem.

### 1.3 Honest limit: the cap still bound

Every cell reports `early_stopped` with `units == max_hidden_units`, which per the R-3 reading
rule means the **cap** bound — including at 128. So this campaign did not stop because the model
converged; it stopped because it was told to, again. What has changed is that the remaining
headroom is now bounded by the metric itself: at val 0.995 / train 0.9975 there is under half a
point available, so unlike 0.670 and 0.735, the number is no longer meaningfully suppressed by
the budget. `epoch == units + 1` in all three cells, confirming `derive_epochs_cap`'s model
(one initial output pass, then one candidate pass plus one output pass per growth iteration).

---

## 2. Relation to R-5 (closed independently, same day)

R-5 was closed hours before this campaign finished, by
[the service-vs-CLI evidence](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R5-SERVICE-VS-CLI-EVIDENCE.md)
(ml#1093), on a different axis: it holds the budget fixed and moves the dataset. E-I holds the
dataset fixed and moves the budget. Neither supersedes the other, and **this note does not close
R-5** — it corroborates that closure from the opposite direction and adds the capacity dimension.

Two claims in this note's first draft were wrong, and ml#1093 is what corrected them. Recording
that, because both came from citing a prior document instead of the code:

- The draft asserted, on ml#1075's authority, that the two paths generate **different spirals**
  (service `modern`, CLI the legacy `r = θ` family). They do not. ml#1093 §1.1–1.3 shows the
  direct CLI also fetches from juniper-data and sends no `algorithm` or `radius`, so both paths
  get `modern` at `radius: 10.0`; the ml#1075 check reimplemented functions that carry a
  `DeprecationWarning` and are no longer on the live path. The only dataset knob that differs is
  `n_rotations` — CLI **1**, service **3.0**.
- The draft treated the ≈0.995 comparator as a direct-CLI figure to be matched. It is not a CLI
  figure at all: ml#1093 §2 traces it to the `A ×4π` arm of an in-process **service-path** repro
  on route-fallback coordinates scaled ×12.566. There is no direct-CLI spiral accuracy on record.

### 2.1 What the two campaigns say jointly

F-5 offered three hypotheses for the gap. With both notes in hand, **the first two are true and
the third is false** — it was never a single-cause question:

| # | F-5 hypothesis                  | verdict   | evidence                                                           |
|---|---------------------------------|-----------|--------------------------------------------------------------------|
| 1 | budget ceiling                  | **true**  | E-I: at `n_rotations 3.0`, capacity alone takes val 0.735 → 0.995  |
| 2 | parameterisation difference     | **true**  | ml#1093: at cap 8, `n_rotations` 3.0 → 1.0 takes val 0.595 → 1.000 |
| 3 | genuine service-path limitation | **false** | both, independently                                                |

The two datasets meet on a shared anchor. ml#1093's control arm is E-A's c004 — service,
`n_rotations 3.0`, cap 8 — at val **0.595**, which is exactly the 8-unit point of the capacity
curve in §1. The campaigns agree where they overlap and diverge only in which variable they move.

### 2.2 The difficulty ratio, quantified

Reading the two together gives a number neither produces alone. To reach ≈1.0 validation on the
service tier:

| spiral                            | units required  |
|-----------------------------------|-----------------|
| `n_rotations 1.0` (the CLI's)     | **8** → 1.000   |
| `n_rotations 3.0` (the service's) | **128** → 0.995 |

Roughly a **16× capacity ratio** for three times the boundary alternations. That is what R-5's
0.670 was really measuring: not a tier penalty, and not merely a harder dataset, but a harder
dataset being run at a budget sized for the easier one.

The tier conclusion is now supported twice over from independent directions. ml#1093 shows the
service acing the *easy* spiral at a small budget; E-I shows it acing the *hard* one given
capacity. A tier that solves both is not the constraint.

---

## 3. cascor#512 at 128 units

288 samples at 30 s over the full 144 min. Compute-process count ran 5 (desktop baseline) to 19
at peak; free memory bottomed at 5218 MiB, leaving ~5 GiB headroom on an 8 GiB card.

At the four samples where the process count returned to the desktop baseline — the only points
where the reading is attributable to the experiment rather than to whatever is training — free
memory read:

```bash
6851 → 6848 → 6848 → 6848  MiB
```

Campaign-start and campaign-end spot reads were **6851 → 6852 MiB**. Net zero.

This matters because it is a harder test than E-A's. E-A ran twelve cells but none wider than 32
units; c002 alone holds a 128-unit cascade with a pool of 8 for 71 minutes, which is both the
widest and the longest single allocation the fix has faced. The pre-fix signature was ~285 MiB
lost per cell with forkserver children surviving teardown. No per-cell reaping was used here
either, deliberately — reaping was the workaround #512 removed the need for.

---

## 4. The cost model, checked against its own prediction

Predictions were recorded in the suite file *before* the run, from two models:

| | cap 64 | cap 128 |
| --- | --- | --- |
| linear in the cap (`derive_epochs_cap`) | 2640 s | 5280 s |
| E-A's measured 1.66× per doubling | 2150 s | 3500 s |
| **actual** | **2907 s** | **4244 s** |

Both predictions were anchored on E-A's 1319 s for the cap-32 cell, but the right anchor is this
campaign's own c000 at 1497 s — the same cell under this campaign's contention (§5). Re-anchored,
linear predicts 2994 / 5988 and the 1.66× model 2485 / 4125, so linear is near-exact at cap 64
(+3%) and the 1.66× model near-exact at cap 128 (−3%). The within-campaign ratios are the
contention-neutral statement: 32 → 64 was slightly *super*-linear (**1.94×**) and 64 → 128 clearly
*sub*-linear (**1.46×**), the latter because output training converges inside its patience more
often as the network widens.

Planning conclusion unchanged: the linear bound errs high, which is the safe direction, and the
resulting 14400 s driver budget was never within 3× of binding (widest cell 4244 s = 29% of it).

Worth carrying forward: the limit that actually ends a run is the **driver's**
`outputs.max_wall_seconds`, not the suite's `per_run_timeout_seconds` — `run_suite` never passes
`--max-wall-seconds`, so an unoverridden cell silently inherits `spiral-baseline`'s 3600. E-A's
write-up records its widest cell (c011, 2893 s) as never approaching the 7200 s per-cell timeout,
but it was within 707 s of the 3600 s budget that would actually have stopped it. Two of the three
cells here would have been truncated by that inherited default.

---

## 5. Conditions

The long-lived isolated E2E stack (cascor `:8202`, data `:8101`, canopy `:8051`) was up and
healthy throughout and was left untouched; it held zero GPU at campaign start, so the trace floor
is desktop/compositor overhead only (~935 MiB, 5 processes). Ports 8110–8139 / 8230–8259 were
clear at launch and no stale lockdirs existed under the lock root.

**The R-5 campaign (ml#1093) ran concurrently and shared the card**, in both directions: that
note records its S1 arm slowed to ~1196 s "a concurrent session was training throughout", and
this campaign's control took 1497 s against E-A's 1319 s for the identical cell — the same 13%
tax seen from the other side. It changes no result in either note. Trajectories here are
seed-determined, not timing-determined, which the control demonstrates directly: c000 reproduced
E-A's c010 to the digit while running 13% slower. Wall-clock is comparable *within* this
campaign (all three cells ran under the same contention) but should not be compared across
campaigns.

All three cells rendered the full §8.1 plot set (5/5, zero skips). Two cascor processes shared the
`juniper-cascor` checkout, which the one-cascor-per-checkout guidance (H-7, pending Q-6)
discourages; the shared resource is only the checkout's file log, while run dirs, snapshots, ports
and sampled metrics are per-run, so the recorded results are unaffected.

> **Update (2026-08-16) — "pending Q-6" is stale.** Q-6 is **resolved and shipped**:
> `JUNIPER_CASCOR_LOG_DIR` (cascor#523), exported per run by `util/experiment_stack.bash` (ml#1120).
> This paragraph's verdict is unchanged — these results came from per-run manifests and artifacts, not
> the shared file log. Note the sharper framing Q-6 settled: that log is the *only* place cascor's
> parent logger writes, so a co-tenant process **rotates** such evidence away rather than interleaving
> it. Plan §15.2 Q-6.

Artifacts: suite dir `~/.local/state/juniper-experiments/suites/e-i-cascor-cap-ceiling-20260814T091542Z`
(`aggregate.csv`, `REPORT.md`, `registry.jsonl`, per-cell configs); GPU trace and suite log under
`~/.local/state/juniper-experiments/traces/e-i-cap-ceiling-20260814T091542Z-*`. The trace is kept
under the run root rather than a session scratchpad so it outlives the session that produced it.
