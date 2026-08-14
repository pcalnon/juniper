# CLI Experimentation — R-5 Service-vs-CLI Spiral Comparison (Corrected Framing)

**Project**: Juniper — cascor + recurrence CLI test/validation/experimentation
**Author**: Paul Calnon
**Date**: 2026-08-14
**Status**: R-5 CLOSED — not a defect
**Related**: P4 §7 register item R-5 / finding F-5;
[R-3 E-A re-run evidence](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R3-EA-RERUN-EVIDENCE.md);
[F-P4-1 root cause](JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md);
[P4 spiral re-surface](JUNIPER_2026-08-12_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-SPIRAL-RESURFACE-EVIDENCE.md);
[P1 smoke](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md)

---

## 0. Outcome

R-5 asked why the **service** spiral tops out around 0.670 while the **direct CLI** reaches
≈0.995. The answer is that the two numbers were never measurements of one problem, and one of
them was never a direct-CLI measurement at all.

| # | Finding | Kind |
|---|---|---|
| 1 | The direct CLI does **not** generate its own spiral — it fetches from juniper-data, exactly as the service does. | source |
| 2 | Both paths therefore get `algorithm: modern` at `radius: 10.0`. The **only** dataset knob that differs is `n_rotations`: CLI default **1**, service config **3.0**. | source |
| 3 | The ≈0.995 comparator is **not a direct-CLI result**. It is the `A ×4π` arm of an in-process **service-path** repro, on coordinates scaled ×12.566. | source |
| 4 | The direct CLI has never been run to completion anywhere in this arc, and still cannot be at a controlled budget (F-P1-3, reproduced today). | source + measured |
| 5 | At an identical budget, the service on the **CLI's** dataset (`n_rotations 1.0`) reaches **val 1.000** vs **0.595** on its own (`n_rotations 3.0`). | measured |

Finding 5 is the whole gap, reproduced inside the service tier by moving one dataset knob —
and it lands *above* the ≈0.995 the service was said to be unable to reach. **There is no
service-tier penalty to explain.** R-5 is closed.

---

## 1. The premise had to be rebuilt twice

R-3 already moved two legs of R-5's premise: the two paths appeared to use different spiral
generators (ml#1075), and the 0.670 figure turned out to be a `max_iterations: 12` budget
artifact (real value 0.735, still climbing). This pass moves the rest — including the ml#1075
premise check itself, which examined the wrong code path.

### 1.1 The direct CLI is not self-contained

`SpiralProblem.generate_n_spiral_dataset` delegates to juniper-data:

```text
juniper-cascor/src/spiral_problem/spiral_problem.py:524-535
    provider = SpiralDataProvider(juniper_data_url)
    provider.validate_configuration()
    return provider.get_spiral_dataset(n_spirals=..., n_points=..., n_rotations=...,
                                       noise_level=..., clockwise=..., train_ratio=...,
                                       test_ratio=..., seed=self.random_seed)
```

`JUNIPER_DATA_URL` is **required** — `main.py:397-400` exits **3** without it, which is exactly
what a first attempt to run this arm produced. Every local generator in `spiral_problem.py`
(`_make_coords`, `_generate_base_radial_distance`, `_generate_raw_spiral_coordinates`,
`_generate_xy_coordinates`, `_generate_spiral_coordinates`, `_generate_angular_offset`) carries
a `DeprecationWarning` reading *"Dataset generation is now handled by JuniperData service."*

### 1.2 So both paths get the same generator

`SpiralDataProvider.get_spiral_dataset` declares `algorithm: Optional[str] = None`
(`data_provider.py:119`) and builds its request at `data_provider.py:147-159`:

```python
params = {"n_spirals": ..., "n_points_per_spiral": ..., "n_rotations": ...,
          "noise": ..., "clockwise": ..., "train_ratio": ..., "test_ratio": ...}
if seed is not None:       params["seed"] = seed
if algorithm is not None:  params["algorithm"] = algorithm
```

`algorithm` is an **optional** provider argument defaulting to `None`, and
`generate_n_spiral_dataset` **never passes it**. No `radius` is sent either. So juniper-data's
`SpiralParams` defaults apply — `algorithm="modern"`, `radius=10.0` — which is precisely what
`spiral-baseline.yaml` requests. Same service, same generator, same algorithm, same radius,
same noise model.

### 1.3 The one knob that does differ

| knob | direct CLI | service (`spiral-baseline.yaml`) |
|---|---|---|
| `algorithm` | `modern` (juniper-data default, not sent) | `modern` (explicit) |
| `radius` | `10.0` (juniper-data default, not sent) | `10.0` (default) |
| `noise` | `0.05` | `0.05` |
| **`n_rotations`** | **1** — `_SPIRAL_PROBLEM_NUM_ROTATIONS`, via `_CASCOR_NUM_ROTATIONS` | **3.0** |

A 3-rotation spiral demands roughly three times the boundary alternations of a 1-rotation
spiral along a radial cut. That is a large difficulty difference, and it was the *only*
dataset difference between the two quoted numbers.

### 1.4 Correction: the ml#1075 premise check modelled a dead code path

`util/ad-hoc/2026-08-13_spiral_service_vs_cli_compare.py` reimplemented cascor's
`SpiralProblem._make_coords` / `generate_n_spiral_dataset` legacy family — and its own header
annotates those sources *"both deprecated in favour of the service"*. It concluded:

> **1.** Different generators, not one problem measured twice. […] the CLI uses the legacy
> family (sqrt radii, r = theta, UNIFORM noise).
> **2.** `n_rotations` is inert in the legacy family.

For the **live** CLI path both statements are wrong in the way that matters. The CLI has not
used the legacy family since dataset generation moved to juniper-data; it requests `modern`,
the same as the service. And `n_rotations` is not inert — it is the single knob that *does*
differ, and W-11 maps it (`main.py:_W11_DATASET_KEY_MAP`).

The check's *conclusion* — that R-5's premise does not hold as stated — was right. Its
*mechanism* was not. Worth recording, because the script reads convincingly: it reimplements
real functions from real line numbers, and the only tell is the deprecation annotation in its
own docstring. **A reimplementation is only as good as its choice of source, and a reachability
check is part of that choice.**

---

## 2. The ≈0.995 comparator is a service-path number

Tracing F-5's figure to its origin:

> [F-P4-1 root cause](JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md) §3
>
> | arm | data | result |
> |---|---|---|
> | A | route fallback, scale ×1 (as shipped) | best corr 0.0007 → `below_threshold` @ iter 1, **0 units**, acc 0.505, 18 s |
> | **A ×4π** | identical but coordinates ×12.566 | corr 0.05–0.39/iter, **12 units**, acc **0.995**, `max_iterations`, 1074 s |

That is `juniper-cascor/util/ad-hoc/f_p4_1_spiral_service_repro.py`, which the note describes
as replaying *"the exact service path in-process"*. The 0.995 is therefore:

- a **service-path** result, not a direct-CLI result;
- measured on the **route-fallback** dataset, not a juniper-data one;
- with coordinates **scaled ×4π**, a dataset neither path produces in normal operation.

F-5 rendered it as "the ≈0.995 the direct CLI reaches on a radius-10 spiral". Every clause of
that attribution is incorrect. The prose next to the table ("the direct CLI's `spiral_problem`
generates at radius 10") is about a *different* arm of the same investigation, and the two
appear to have fused when F-5 was written.

### 2.1 There is no direct-CLI spiral accuracy on record

[P1 smoke](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md)
finding **F-P1-3** records that the direct CLI has never completed a run in this arc:

> Launch + dataset fetch + live training demonstrated (26 k log lines, candidate training
> progressing, snapshots written); killed at the smoke's 480 s bound (exit 124) — the direct
> CLI exposes **no budget flags** […] a smoke-scale completion is structurally unreachable

**Reproduced today.** A deliberately tiny arm (`max_hidden_units: 2`, `candidate_pool_size: 4`,
`candidate_epochs: 50`, `max_epochs: 100`) trained its 8 candidates across 2 growth rounds in
~4 minutes — reaching its 2-unit cap — then produced **no further log output for ~11 minutes**
while the process and its forkserver stayed alive, and had to be killed. So even a budget
chosen to be trivially small did not complete, and the phase it stalls in is not the one the
W-11-mapped knobs govern.

That is F-P1-3 unchanged, two waves after W-11 was supposed to address it. Diagnosing *which*
budget actually governs that phase is out of scope here and is left with F-P1-3. What matters
for R-5 is the consequence: **the direct CLI still cannot be run at a controlled, comparable
budget**, which is why the empirical arm below is run on the service path instead, at the
CLI's dataset.

---

## 3. The measurement

Since both paths draw the same dataset from the same service, the tier question can be asked
without the CLI's unbounded budget: put the **service** on the **CLI's** dataset and compare
against the service on its own, with everything else held fixed.

| arm | path | `n_rotations` | budget | source |
|---|---|---|---|---|
| **c004** (anchor) | service | **3.0** | cap 8 / pool 8 / iter 32 | R-3 E-A grid |
| **S1** | service | **1.0** | cap 8 / pool 8 / iter 32 | this note |

`util/ad-hoc/2026-08-14_r5_arm_s1_service_nrot1.yaml` is `spiral-baseline.yaml` with exactly
two deltas: `n_rotations 3.0 → 1.0`, and the cap/iteration pair set to reproduce c004's budget.
Generator, noise, point count, ratios, seed, learning rates, thresholds, pool size and epoch
budgets are byte-identical. **S1 − c004 is a one-variable measurement of dataset difficulty.**

### 3.1 Result

| cell | `n_rotations` | units | train | **val** | wall (s) | completion |
|---|---|---|---|---|---|---|
| c004 | 3.0 | 8 | 0.6312 | **0.595** | 536 | `early_stopped` |
| **S1** | **1.0** | 8 | **0.9938** | **1.000** | ~1196 | `early_stopped` |

S1's full eval block, `GET /v1/metrics` at completion:

```json
{"hidden_units": 8, "train_accuracy": 0.99375, "val_accuracy": 1.0,
 "train_loss": 0.009550425224006176, "val_loss": 0.005691874772310257,
 "f1": 1.0, "precision": 1.0, "recall": 1.0, "roc_auc": 1.0,
 "eval_metrics": {"split": "validation", "n_samples": 200, "n_classes": 2}}
```

Both cells are cap-bound: both recruited exactly 8 units and stopped at `max_hidden_units`,
so neither was budget-starved relative to the other (per R-3, `early_stopped` at
`units == max_hidden_units` is the cap binding, not patience).

**Reading.** Changing `n_rotations` from 3.0 to 1.0 — nothing else — moves the service from
0.595 to a *perfect* 1.000 on validation, with every classification metric saturated. The gap
R-5 attributed to the service tier is reproduced end-to-end **inside the service tier**, by
moving the one dataset knob that actually differs between the two paths. And 1.000 does not
merely approach the ≈0.995 comparator, it exceeds it: on the direct CLI's own dataset the
service solves the problem outright.

**Wall-clock is not comparable here and is not part of the finding.** S1's ~1196 s against
c004's 536 s reflects GPU contention — a concurrent session was training throughout, holding
7 × 116 MiB — not a property of either dataset. Only the accuracy comparison is controlled.

### 3.2 Reproducing it

```bash
# 1. per-run stack (data + an idle cascor); prints RUN_ID and DATA_URL
util/ad-hoc/2026-08-14_r5_stack_up.bash

# 2. the arm. --stall-seconds is REQUIRED: the Q-2 detector watches current_epoch, which does
#    not advance while the pool trains, so the 120 s driver default aborts a healthy pool-8
#    cell at ~120 s (ml#1074 / R-6 — the suites carry stall_seconds: 1200 for this reason).
python util/experiments/run_experiment.py \
    --config util/ad-hoc/2026-08-14_r5_arm_s1_service_nrot1.yaml \
    --run-dir <RUN_DIR> --stall-seconds 1200

# 3. teardown
util/experiment_stack.bash --down <RUN_ID>
```

Artifacts: `<RUN_DIR>/artifacts/results/r5_s1_final.json` (the status + metrics + network
capture quoted above), alongside the driver's plots from the first attempt.

Two operational notes for anyone repeating this:

- The first attempt **did** hit the 120 s stall abort. The service kept training regardless, so
  the naive re-run then failed with `HTTP 409: Training already in progress` — `start_fresh:
  true` does not stop an in-flight session. `util/ad-hoc/2026-08-14_r5_poll_training.py`
  attaches to the live session instead of restarting it, which is what produced this result.
- The direct-CLI runner (`util/ad-hoc/2026-08-14_r5_run_direct_cli.bash`) is kept because it
  is what reproduces F-P1-3 (§2.1). It must **not** export `PYTHON_GIL=0` — the experiment
  stack sets that for juniper-data's free-threaded `python3.14t`, but `JuniperCascor1` is a
  normal GIL build and aborts at interpreter preinit.

---

## 4. Why R-5 closes

R-5 asked whether the shortfall was a budget ceiling, a dataset/parameterisation difference, or
a genuine service-path limitation. All three legs now have answers, and none of them is the
service tier:

1. **Budget ceiling** — real, and already fixed. `max_iterations: 12` made every
   `max_hidden_units` above 12 unreachable; with the cap binding, spiral reaches 0.735 and is
   still climbing (R-3, ml#1086).
2. **Dataset difference** — real, and the dominant term. `n_rotations` 1 vs 3 is the only
   dataset knob separating the two paths, and moving it inside the service reproduces the gap.
3. **Service-path limitation** — **no evidence for one**, and the comparator that suggested it
   was itself a service-path number on a rescaled dataset. Given the CLI's dataset, the
   service reaches 1.000.

Put the other way round: the service was never failing to match the CLI. It was solving a
harder problem — three spiral rotations instead of one — under a cap that stopped it early,
and being scored against a number produced by neither path on a dataset produced by neither
path.

The corrected framing R-3 asked for — *same dataset on both paths, equalised budget, compared
against 0.735 rather than 0.670* — is satisfied in the only form the code permits: the same
dataset (both paths fetch it from juniper-data), an equalised budget (cap 8 / pool 8 on both
sides of the S1/c004 pair), and no reliance on the superseded 0.670.

---

## 5. What was not done, and why

- **No completed direct-CLI run.** Its output-epoch budget is not governed by any W-11-mapped
  knob (§2.1), so a budget-comparable CLI run is not reachable today. This is F-P1-3, still
  open, and it is now the *only* thing standing between this analysis and a direct
  head-to-head. It is a CLI-ergonomics gap, not a correctness one.
- **No `algorithm: legacy_cascor` arm.** The R-3 note suggested equalising by setting the
  service to the legacy family. That equalisation is unnecessary: §1.2 shows the CLI already
  requests `modern`, so switching the service to `legacy_cascor` would have *introduced* a
  difference rather than removed one.

### 5.1 S1 was run on the pre-cascor#514 code, deliberately

cascor#514 (the fix for #505) merged the same day as this measurement. It makes
`candidate_patience` / `candidate_convergence_threshold` actually reach the candidate pool for
the first time — and `spiral-baseline.yaml` sets `candidate_patience: 100`.

So **every spiral number in this arc — 0.735, 0.670, c004's 0.595, and S1 — was measured with
the candidate pool running patience 50, not the configured 100.** S1 was therefore run against
the cascor primary checkout pinned at `ddd5146` (the c004 anchor's code), so that S1 − c004
isolates `n_rotations` and nothing else.

The consequence is forward-looking and worth flagging loudly: **spiral runs after cascor#514
are not directly comparable to this arc's figures.** Candidates now get twice the patience the
whole E-A surface was measured with. Any future re-run that wants to sit alongside these
numbers must either pin the pre-#514 code or re-baseline the grid.

---

## 6. Operational finding — the orphan reaper will kill live experiment stacks

Not R-5, but discovered in the course of it and worth a line in the record.

`util/reap_pytest_orphans.bash --dry-run` during this campaign classified as **`WOULD REAP`**:

- `pid=3014490` — this campaign's **own live** experiment-stack cascor;
- `pid=2998041` — a **concurrent session's live** experiment cascor, mid-training (its pool held
  7 × 116 MiB of GPU at the time).

Both are healthy, wanted processes. They match the orphan predicate because
`experiment_stack.bash` launches services under `nohup` inside a subshell, so they reparent to
`systemd --user` — which is exactly the reaper's "parent is 1 / `systemd --user` / parent gone"
orphan test. The long-lived isolated E2E stack is correctly `KEEP` (its supervising parent is
alive), so the hazard is specific to nohup-launched per-run stacks.

**Always `--dry-run` the reaper and read the candidate list before running it live**, and never
run it live while any experiment stack is up. The handoff advice to "reap before every cell" is
obsolete anyway now that cascor#512 is field-validated (ml#1086); this is a second, independent
reason not to reach for it reflexively.

---

## 7. Register update

| item | status |
|---|---|
| R-5 — investigate the service-vs-CLI spiral accuracy gap (F-5) | **CLOSED — not a defect** (this note) |
| F-5 — spiral remains hard at this budget | superseded: the budget was the cap (R-3), the comparator was misattributed (§2) |
| F-P1-3 — direct CLI exposes no budget knobs | **still open**, and now the blocker for any true head-to-head (§5) |
| cascor#505 — candidate params never reach the pool | **fixed and merged** (cascor#514) — noted here because §2.4 of the F-P4-1 note filed it |

Two consequences beyond R-5 itself:

- **`n_rotations` is a first-order difficulty lever, not a cosmetic one.** 1 → 3 takes the same
  network at the same budget from 1.000 to 0.595. E-B's difficulty ranking places "spiral"
  as a single point; it is really a family, and any future ranking should state the rotation
  count alongside it.
- **Spiral figures are not comparable across cascor#514** (§5.1). Everything in this arc was
  measured with the candidate pool at patience 50 while the config asked for 100.
