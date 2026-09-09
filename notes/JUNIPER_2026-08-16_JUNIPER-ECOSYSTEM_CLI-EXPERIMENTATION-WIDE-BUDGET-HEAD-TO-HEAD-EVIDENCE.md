# CLI Experimentation — direct CLI vs service, wide-budget head-to-head (64–128 units)

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-ml / juniper-cascor
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-17

**Code**: juniper-cascor `3909d27` (post-#514, post-#517, post-#522, post-#523) — **both arms, one
SHA**, the service arm from the canonical checkout and the CLI arm from a dedicated worktree cut
from it · juniper-ml `main` @ `7156d6d`
**Runs**: 12 runs / 6 paired replicates, 2026-08-16 07:55 → 2026-08-17 04:22 CDT (~20.5 h).
Suites `e-j-h2h-wide-cap64-20260816T125456Z`, `e-j-h2h-wide-cap128-20260816T222432Z`,
`e-j-h2h-wide-cap64-init42-20260817T065901Z`; CLI arms under
`~/.local/state/juniper-experiments/h2h-wide-2026-08-16/cli/`. All cells `succeeded`, all screened
`oom == 0`.
> **SUPERSEDED HEADLINE (2026-08-20).** The `1.99 ± 0.21×` below was measured on cascor `3909d27`,
> which is **pre-#531/#533**: the CLI arm carried `main.py`'s `OMP=2` BLAS cap and the service arm
> did not. (#531 valued that cap at 1.30× of a 1.52× candidate-phase penalty; a k=3 rep-paired
> re-measurement on 2026-08-22 puts it at **1.016× [0.885, 1.148]** — see the correction in §6
> limit 1.) **Do not
> quote 1.99× as the current gap.** What survives: the difference is wholly in the candidate phase
> and it compounds per growth iteration. See §6 limit 1 and §8.

**Verdict**: **no accuracy gap worth acting on — and a real ~2× wall-clock gap.** On identical data
at an identical budget the two paths agree on validation accuracy to **+0.75 ± 0.52 pp** (CLI
ahead, six paired replicates, one of them exactly 0.00 pp), while the direct CLI takes **1.99 ±
0.21×** the training time. **100% of that time difference is the candidate phase**; the output
phase is identical (1.03–1.05×). It is not the initialisation asymmetry — a control with both arms
on network seed 42 widened the gap to 2.17× — and it is not host contention. This is the finding
the smoke scale could not reach, because the gap compounds per growth iteration and a 2-unit cap
has almost none.

---

## 1. What this closes, and what it deliberately does not re-open

The [head-to-head smoke note](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md)
§8 left exactly one row open — *"Wide-budget head-to-head (64–128 units) — **OPEN**; §6 bounds what
this run does not cover"*. This closes it, and repairs three methodology weaknesses along the way:
the two that note's §6 admits (no shared wall-clock denominator; smoke scale / one seed) and one
its front-matter models rather than states (pinning both arms to a single cascor SHA).

Three findings are already settled and were **not** re-measured. Re-running them would have cost
hours and invited a contradictory write-up:

| finding | closed by | result |
| --- | --- | --- |
| R-5 — why service spiral topped out near 0.670 while the CLI reached ~0.995 | ml#1093 (`14be0e2`) | the **dataset**, not the service tier: at cap 8, `n_rotations` 3.0 → 1.0 moved val 0.595 → 1.000 |
| Head-to-head at smoke scale | ml#1114 (`c87a4f2`) | **no path gap** at cap 2 / pool 4 — val delta 0.00 pp (easy), +1.00 pp (hard) |
| F-5 "genuine service-tier limitation" | ml#1093 + E-I + ml#1114 | **FALSE**, three independent lines |

### 1.1 Why 64 and 128

E-I extended E-A's pool-8 capacity column upward. Joined, on the hard spiral (`n_rotations` 3.0,
pool 8):

| units | 4 | 8 | 16 | 32 | 64 | 128 |
| --- | --- | --- | --- | --- | --- | --- |
| val | 0.545 | 0.595 | 0.610 | 0.735 | **0.945** | **0.995** |

The first four points are **E-A's** (R-3 re-run, ml#1086). E-I contributed **64 and 128** as new
measurements and re-ran cap 32 as a control that reproduced E-A's c010 exactly — that reproduced
control is the cross-run anchor that lets both campaigns be read on one axis.

The smoke head-to-head ran at a **2-unit cap**, where the hard arm is floored near chance by
design. 64 and 128 are where the curve is steep and then decelerating into its ceiling — the only
region where a *small* path gap could still hide.

**This is a targeting rationale, not a comparison baseline.** §2.2 explains why these absolute
accuracies cannot sit on that curve, and §6 keeps it as a named limit.

---

## 2. Design — one config file, both arms

`util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml` is the single source. The **service** arm is driven by
`run_suite` through `util/experiments/suites/p4/e-j-h2h-wide-cap{64,128}.yaml`; the **direct-CLI**
arm is driven by `util/ad-hoc/2026-08-16_h2h_cli_arm.bash`.

**Under a suite, "one config" needs one extra step.** The smoke run had no suite, so both arms
literally read the same hand-written file. `run_suite` instead writes a fully-resolved
`<suite_dir>/cells/<cell_id>/experiment.yaml` per cell and the service arm runs *that*. The CLI arm
must therefore be handed **the same generated cell file** — feeding it the hand-written base would
give every CLI replicate one seed while the service arm varied, which is precisely the artifact
this campaign exists to avoid. The arm runner refuses any path that is not `*/cells/*/experiment.yaml`.

### 2.1 The equalisation doctrine

The direct CLI can only receive keys carried by `_W11_DATASET_KEY_MAP` / `_W11_TRAINING_KEY_MAP`
(`juniper-cascor/src/main.py:228-249`). Every key is therefore in exactly one of three buckets:

| bucket | meaning | keys here |
| --- | --- | --- |
| **MAPPED** | in the CLI map; both arms honour the configured value | `n_spirals`, `n_points_per_spiral`, `n_rotations`, `noise`, `train_ratio`, `test_ratio`, `seed`; `max_hidden_units`, `candidate_pool_size`, `learning_rate`, `correlation_threshold`, `patience`, `candidate_epochs`, `max_epochs`, `output_epochs` |
| **EQUALISE** | not in the CLI map, but the value makes the service behave the way the CLI already does by default | `max_iterations`, `early_stopping` |
| **OMIT** | not in the CLI map, and setting it would move one arm only — left unset so **both** fall through to the same `cascor_constants` default | `candidate_patience`, `candidate_learning_rate`, `convergence_threshold`, `candidate_convergence_threshold`; `algorithm`, `radius` |

The OMIT bucket is why this campaign does **not** inherit
`juniper-cascor/conf/experiments/spiral-baseline.yaml` the way E-I did: that file sets
`candidate_patience: 100`, which the CLI cannot receive (`candidate_patience` is not `patience` —
the latter is output-layer early stopping and *is* mapped). Inheriting it would leave the two arms
differing on a candidate knob and invalidate the head-to-head. Both arms therefore take the module
default `_PROJECT_MODEL_CANDIDATE_PATIENCE = 50`.

Omission is doing real work, not hand-waving: `algorithm` is absent from the CLI's dataset map, and
`spiral-baseline` sets `algorithm: modern`. Leaving it out means **neither** arm sends it and both
take juniper-data's default — which the dataset metadata confirms *is* `modern`. Equality becomes
structural rather than an assumption about anyone's defaults.

### 2.2 A trap this campaign found: `max_epochs` alone de-equalises the arms

Not in the smoke pair's reasoning, and material at these caps.

* **CLI** — `_W11_TRAINING_KEY_MAP` aliases `max_epochs → output_epochs`, so `max_epochs` sets the
  budget for **every** output pass.
* **SERVICE** — `TrainingParams.max_epochs` is the **initial** output pass only. Every later
  per-round pass reads `self.output_epochs` (`cascade_correlation.py:4591`, `:4768`, `:4820`), which
  falls back to `_PROJECT_MODEL_OUTPUT_EPOCHS = 10000` when unset (`:716`). The source says so at
  `:1876-1882`: *"The two therefore agree only while a caller leaves `max_epochs` unset"*.

So `max_epochs: 2000` **alone** would have given the CLI 2000 epochs per pass and the service 10000
on every round after the first — a 5× per-pass asymmetry across 64–128 rounds, making the service
arm both slower *and* better-trained. Setting **both** keys to the same value removes the question:
the CLI takes the explicit `output_epochs` (which wins over the alias, `main.py:291-292`) and the
service gets initial == per-round. The smoke pair set only `max_epochs`; at a 2-unit cap there was
one round and the trap could not bite.

This is also the second reason the absolute numbers here cannot be read against E-I's curve: E-I
ran per-round output passes at the 10000 default while these run at 2000.

### 2.3 Scope, and the decisions behind it

| choice | reason |
| --- | --- |
| hard spiral only (`n_rotations` 3.0) | the easy arm already saturates at val 1.000 at a cap of 8 (ml#1093); at 64–128 units it is pure ceiling effect — real hours, no answer |
| pool **8**, not swept | the value the interesting region was characterised at; E-A settled that pool raises candidate correlation but not accuracy |
| caps 64 and 128 | §1.1 |
| `max_iterations: 128` on both caps | must clear the largest cap or growth stops before the cap binds — the R-3 defect in a new costume. Holding it constant keeps the two suites differing in the axis under test alone |
| per-pass budgets 2000 / 500 / patience 200 | spiral-baseline's, **not** the smoke pair's 100 / 50 / 50: under-training each of 64–128 units would compress both arms toward a floor and destroy the resolution this campaign is buying |
| `outputs.plots: []`, `runtime.eval_metrics_enabled: false` | the CLI renders no plot files and computes no eval-metric forward pass, so both would add service-side work inside a wall-clock comparison. `eval_metrics_enabled` gates **only** the F1/precision/recall/ROC-AUC pass (`api/lifecycle/manager.py:1893`) — `train_accuracy` / `val_accuracy` are unaffected |
| `outputs.max_wall_seconds: 14400` explicit | unset silently inherits the driver's 3600 s — the E-I budget trap |

**Design: 2 caps × 2 paths × 3 seeds = 12 runs.**

### 2.4 The seed contract, and what it does *not* buy

`run_suite` has **no replicate primitive** — `SUITE_KEYS` / `EXECUTION_KEYS` contain no repeat key,
and matrix axes must be dotted config paths. `seed_policy: per_cell` *derives* a seed
(`base_seed + cell.index`, rewritten into **both** `experiment.seed` and `dataset.params.seed`) but
does not itself create replicates. The multiplier chosen here is a 3-valued matrix axis on
**`experiment.description`** — the only key that is legal (driver `EXPERIMENT_KEYS`), inert
(recorded in the manifest, never sent to any service — `run_experiment.py:1390`), and side-effect
free. It is named explicitly here because three operators would otherwise pick three different
tricks, each yielding different derived seeds.

**One 3-cell suite per cap.** `cell.index` restarts at 0 in each suite, so both derive the *same*
three seeds (20260729 / 20260730 / 20260731). Because juniper-data dataset ids are content-addressed
on the dataset params, that pairs each cap-64 replicate with a cap-128 replicate on **identical
data**, and the campaign resolves to **3 dataset ids across 6 cell configs** — fewer ids than
configs is the design working. A single 6-cell suite would have derived 6 seeds and 6 ids, and the
caps would have shared no datasets.

> **The two arms' error bars are not commensurate, and this note does not pool them.**
> Varying `dataset.params.seed` gives a fresh **data draw on both arms**, but a fresh **network init
> on the CLI arm only**. The CLI threads the dataset seed into the network
> (`spiral_problem.py:445` passes `random_seed=self.random_seed`; `:416-418` seed torch / numpy /
> random from it). The service network instead seeds from
> `self.config.random_seed or _CASCADE_CORRELATION_NETWORK_RANDOM_SEED` (`cascade_correlation.py:667`)
> = `_PROJECT_RANDOM_SEED` = **42**, and nothing the driver can send reaches it: `TrainingParams` has
> no seed field and is `extra="forbid"`, and the start body is only `{start_fresh, epochs?, params}`.
> With `start_fresh: true` every service replicate re-seeds to 42 and initialises an **identical
> network**.
> **Consequence:** the service spread bounds *data-draw* variance; the CLI spread bounds *data-draw +
> init* variance. They are reported separately throughout and never combined into a single
> resolution figure. This is the strongest constraint on the headline claim.

The obvious alternative — pin the dataset and vary `experiment.seed` for a pure init sweep — is
**not available** and was not attempted. `experiment.seed` reaches no training or network-init code
on either path (the driver uses it solely as a `setdefault` for `dataset.params.seed` plus a
manifest record), so it would have produced byte-identical CLI replicates with zero variance: the
worst possible outcome, because it looks like perfect agreement.

Copying E-I's `seed_policy: fixed` would have been the same silent null by a different route — with
no seed axis it yields N identical replicates.

---

## 3. Equalisation, proven rather than asserted

Four independent proofs, none of them "we set the same YAML key".

**(a) The CLI says so itself.** Every arm logs which YAML keys reached it and which it had to drop
(`main.py:427` / `:429`, the W-1 doctrine of reporting unmapped keys loudly):

```
W-11 experiment-YAML overrides active: ['candidate_epochs', 'candidate_pool_size',
  'correlation_threshold', 'learning_rate', 'max_hidden_units', 'n_points', 'n_rotations',
  'n_spirals', 'noise', 'output_epochs', 'patience', 'random_seed', 'test_ratio', 'train_ratio']
W-11: experiment-YAML keys with no direct-CLI counterpart (service-tier only), IGNORED here:
  ['training.params.early_stopping', 'training.params.max_iterations']
```

Fourteen MAPPED keys arrived; the IGNORED list is **exactly and only** the two EQUALISE keys, and
no OMIT-bucket key appears anywhere because none was set. `max_epochs` is absent from the active
list because the explicit `output_epochs` won the alias, exactly as `main.py:291-292` specifies.

**(b) Identical data, verified by content address.** The CLI arms ran against their own
juniper-data instance. After all three cap-64 arms it held exactly **three** datasets:

```
spiral-1.0.0-171add81e5c79010   spiral-1.0.0-45492cd2af666a41   spiral-1.0.0-7a976ad47ea86fe7
```

byte-identical to the three ids the service arms independently recorded — so each replicate's two
arms provably trained on the same data, and the two caps share their datasets as designed (the
cap-128 replicates re-resolved `…7a976ad4` and `…45492cd2`). The CLI also confirmed it reached the
service rather than falling back in-process: `SpiralProblem: generate_n_spiral_dataset: Using
JuniperData service at http://127.0.0.1:8110` (`spiral_problem.py:548`).

**(c) Identical resolved budget, from both arms' own logs.** Both print the resolved budget as
they enter the training loop (`cascade_correlation.py:1918`):

| arm | line |
| --- | --- |
| service | `max_epochs: 2000, max_iterations: 128, early stopping: True` |
| CLI | `max_epochs: 2000, max_iterations: 1000000, early stopping: True` |

`max_epochs` and `early_stopping` agree. `max_iterations` deliberately does not: it is unmappable,
so it binds the service only, and 1000000 is the CLI's network default — the cap is what stops
growth on both, which is why `units == max_hidden_units` is the check that matters rather than
this number. Output-pass volume confirms the budget bit: **13000** output-epoch progress records
on each arm of c000 — 130,000 epochs, identical.

**(d) Identical architecture.** Service `topology.json` reports `input_size: 2`, `output_size: 2`,
`Tanh`; the CLI summary reports the same. (Worth checking rather than assuming: the service builds
through `create_simple_config`, whose signature defaults `output_size=1` — the lifecycle manager
overrides it from the staged dataset.)

**What could not be equalised, and was therefore measured instead.** Beyond the YAML, the CLI
passes its own `_SPIRAL_PROBLEM_*` constant tier into the network config (`spiral_problem.py:420-445`),
which the service never sees. Every one of those was resolved at runtime against the service's
config default and they agree: `convergence_threshold` 0.001, `candidate_learning_rate` 0.1,
`candidate_patience` 50, `candidate_convergence_threshold` 0.001, `random_value_scale` 0.1,
`epochs_max` 100000000000. `CascadeCorrelationConfig` has no `early_stopping` or
`candidate_early_stopping` kwarg at all — candidate early stopping is the constant
`_PROJECT_MODEL_CANDIDATE_EARLY_STOPPING = True` on both paths.

That exhausts the configuration surface. **The network initialisation is the one difference that
survives**, it cannot be closed through configuration, and §4.3 shows it is not a formality.

---

## 4. Results

Hard spiral (`n_rotations` 3.0), pool 8, `output_epochs` = `max_epochs` = 2000, patience 200,
`candidate_epochs` 500, `candidate_patience` 50 (module default, unset on both arms).

### 4.1 Cap 64 — three paired replicates

| replicate | dataset | arm | train | **val** | units | training span |
| --- | --- | --- | --- | --- | --- | --- |
| r0 | `…7a976ad4` | service | 0.9862 | **0.9700** | 64 | 3570 s |
| r0 | `…7a976ad4` | CLI | 0.9975 | **0.9800** | 64 | 7412 s |
| r1 | `…45492cd2` | service | 0.9975 | **0.9900** | 64 | 4481 s |
| r1 | `…45492cd2` | CLI | 0.9950 | **0.9950** | 64 | 7109 s |
| r2 | `…171add81` | service | 1.0000 | **0.9800** | **46** | 3764 s |
| r2 | `…171add81` | CLI | 0.9950 | **0.9800** | 64 | 7719 s |

Paired deltas (CLI − service), which is the statistic this design supports — the replicates differ
by data draw, and differencing *within* a replicate cancels that:

| replicate | Δ val | Δ train | span ratio |
| --- | --- | --- | --- |
| r0 | +1.00 pp | +1.13 pp | 2.076 |
| r1 | +0.50 pp | −0.25 pp | 1.586 |
| r2 | +0.00 pp | −0.50 pp | 2.051 |
| **mean** | **+0.50 ± 0.50 pp** | +0.13 pp | **1.904 ± 0.276** |

**The accuracy delta is not distinguishable from zero**: +0.50 pp against a paired sd of 0.50 pp,
with the per-replicate values (+1.00 / +0.50 / +0.00) straddling it. The span ratio behaves
completely differently — all three replicates agree that the CLI is slower, and 1.904 sits well
clear of its own spread. §4.3 is about why that ratio is nonetheless not yet a statement about the
paths.

r2 is the sharpest single illustration of the initialisation asymmetry: on **identical data** the
service stopped at 46 units and the CLI grew to 64 — different architectures at termination —
and the two still landed on exactly the same validation accuracy, 0.9800.

### 4.2 Cap 128 — two paired replicates

Reduced from three; see §6 and the suite header.

| replicate | dataset | arm | train | **val** | units | training span |
| --- | --- | --- | --- | --- | --- | --- |
| r0 | `…7a976ad4` | service | 1.0000 | **0.9950** | **97** / 128 | 5144 s |
| r0 | `…7a976ad4` | CLI | 0.9988 | **1.0000** | 128 | 11127 s |
| r1 | `…45492cd2` | service | 1.0000 | **0.9900** | **69** / 128 | 4997 s |
| r1 | `…45492cd2` | CLI | 0.9975 | **1.0000** | 128 | 9493 s |

| replicate | Δ val | Δ train | span ratio |
| --- | --- | --- | --- |
| r0 | +0.50 pp | −0.12 pp | 2.163 |
| r1 | +1.00 pp | −0.25 pp | 1.900 |
| **mean** | **+0.75 ± 0.35 pp** | −0.19 pp | **2.031 ± 0.186** |

**The two arms terminate for different reasons here.** Both service cells saturated training
accuracy at 1.0000 and early-stopped short of the cap — at 97 and 69 units — while both CLI cells
ran to the full 128. So at these budgets a 128-unit cap is not a capacity-limited measurement on
the service side at all: it is the same solved problem with headroom. The `units ==
max_hidden_units` check is what distinguishes that from a cap-bound run, since **both cases report
`early_stopped`**.

**And the accuracy axis is out of room.** Both CLI cells reached val **1.0000** exactly. At the
ceiling a positive Δ val can only be bounded, never measured — cap 128 can say the CLI is not
*worse*, but it cannot size a CLI advantage, because there is nowhere above 1.0000 to put one.

Read across the caps on identical data, capacity buys progressively less on the service arm:

| replicate | cap 64 | cap 128 | Δ |
| --- | --- | --- | --- |
| r0 | 0.9700 (64 u) | 0.9950 (97 u) | +2.50 pp |
| r1 | 0.9900 (64 u) | 0.9900 (69 u) | +0.00 pp |

All cells in both caps screened GPU-clean (`oom == 0`) via
`util/ad-hoc/2026-08-10_ea_aggregate_clean.py`.

### 4.2a All five paired replicates together

| cap | replicate | Δ val | span ratio |
| --- | --- | --- | --- |
| 64 | r0 | +1.00 pp | 2.076 |
| 64 | r1 | +0.50 pp | 1.586 |
| 64 | r2 | +0.00 pp | 2.051 |
| 128 | r0 | +0.50 pp | 2.163 |
| 128 | r1 | +1.00 pp | 1.900 |
| | **mean** | **+0.60 ± 0.42 pp** | **1.955 ± 0.220** |

The two axes behave nothing alike, and that contrast is the campaign's central observation. The
accuracy delta is small, includes an exact **0.00 pp** replicate, and is comparable to its own
spread — while every one of the five span ratios exceeds 1.58 and the mean sits nine spreads above
1.0. Whatever separates these arms, it costs roughly a factor of two in time and buys at most
about half a point of accuracy.

### 4.3 Where the wall-clock difference actually lives

The span ratio is stable at ~1.9×, so it deserves an explanation rather than a headline. Splitting
each run's span into its candidate and output phases (`util/ad-hoc/2026-08-16_h2h_phase_split.py`)
localises it completely — candidates are ~98% of the span on both arms:

| replicate | output phase | candidate phase |
| --- | --- | --- |
| r0 | 66 → 68 s (**1.03×**) | 3495 → 7294 s (**2.09×**) |
| r1 | 67 → 70 s (**1.04×**) | 4409 → 6995 s (**1.59×**) |
| r2 | 47 → 71 s (1.51×, 46 vs 64 iterations) | 3713 → 7601 s (**2.05×**) |

**The output phase is identical.** Both arms ran 130,000 output epochs on r0 — 13000 progress
records each — in the same time. Whatever the difference is, it is not general compute throughput.

The candidate phase splits further into *work* and *rate*. On r0 the CLI ran **233,970 candidate
epochs against the service's 162,250** (1.44×) for the same 512 candidate trainings (64 iterations
× pool 8, identical on both). Per iteration:

| replicate | service | CLI | ratio |
| --- | --- | --- | --- |
| r0 | 54.6 s | 114.0 s | 2.09× |
| r1 | 68.9 s | 109.3 s | 1.59× |
| r2 | 80.7 s | 118.8 s | 1.47× |
| | mean 68 ± 13 s | **mean 114 ± 5 s** | |

The shape is the finding: **the CLI's candidate cost is near-constant while the service's varies
with the data and is always lower.** In epochs, the CLI's candidates run ~457 of their 500-epoch
budget (91%) where the service's run ~317 (63%) — the CLI's candidates rarely stop early, the
service's usually do.

Both arms carry the same `candidate_epochs` 500, `candidate_patience` 50 and
`candidate_convergence_threshold` 0.001 (§3), and `_PROJECT_MODEL_CANDIDATE_EARLY_STOPPING` is a
constant `True` on both. What differs is the network the candidates are fitting — which is exactly
the one thing §3 could not equalise, and which §4.4 tests directly.

### 4.4 The initialisation control — the hypothesis is refuted

§4.3 left one explanation standing: the arms start from different networks, so their candidates
converge differently. The control tests it directly. Because the CLI derives its network seed from
`dataset.params.seed`, a run at seed **42** puts it exactly where the service's already is —
`CascadeCorrelationConfig.random_seed` **defaults to 42**, so `create_simple_config` gives the
service network seed 42 without anyone asking. Both arms therefore provably ran network seed 42 on
the same dataset (`spiral-1.0.0-cc74e49e366cfc9f`), cap 64, both cap-bound at 64 units.

| arm | train | **val** | units | span | candidate phase | output phase | candidate epochs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| service | 0.9888 | **0.9750** | 64 | 2697 s | 2623 s (41.0 s/iter) | 65 s | 134,500 |
| CLI | 0.9975 | **0.9900** | 64 | **5849 s** | 5742 s (89.7 s/iter) | 68 s | 215,610 |
| ratio | | **+1.50 pp** | | **2.169** | **2.19×** | **1.05×** | **1.60×** |

**The gap does not close — it is the widest in the campaign.** 2.169 against the main campaign's
1.904 ± 0.276 (cap 64) and 2.031 ± 0.186 (cap 128). Both components of §4.3 survive: the CLI still
runs 1.60× the candidate epochs *and* is still ~1.37× slower per candidate epoch (2.19 / 1.60).

**Host contention is ruled out here as well.** The control is the one pair with a load sample
covering both arms: mean load1 **8.7** during the service arm and **9.4** during the CLI arm, on a
16-core host. An 8% difference in background load cannot produce a 2.17× span.

So with the dataset identical, the network seed identical, every configuration knob verified equal
(§3), the same 64 growth iterations on both arms, and comparable host conditions, **the direct CLI
still takes 2.17× as long, and all of it is in the candidate phase.**

*One honest caveat on what "identical initialisation" bought.* The two runs are not bit-identical
after the first output pass — iteration 0 already differs (train loss 0.239994 / acc 0.6088 on the
service vs 0.239272 / 0.5775 on the CLI), because the two processes consume randomness differently
downstream of construction. The control removes the *structural seed asymmetry* documented in
§2.4, which is what it was built to remove; it does not make the two trajectories the same run.
(And note that initial train accuracy is **not** a usable init signature: it reads 0.5138 on both
control arms and 0.5188 on both main-campaign r0 arms, whose seeds genuinely differ — it reflects
the data under a near-random boundary, not the weights.)

---

## 5. What this settles

**The accuracy question is closed: no path gap worth acting on.** Six paired replicates (three at
cap 64, two at cap 128, one control), each with both arms on the same content-addressed dataset:

| | Δ val (CLI − service) |
| --- | --- |
| cap 64 (n=3) | +0.50 ± 0.50 pp |
| cap 128 (n=2) | +0.75 ± 0.35 pp |
| init control (n=1) | +1.50 pp |
| **all six** | **+0.75 ± 0.52 pp** |

Every replicate is ≥ 0, so this is not quite "no difference" — it is a small, consistent CLI edge
of well under one point, on a task where the arms sit at 0.97–1.00. One replicate came in at
exactly **0.00 pp**, and at cap 128 the CLI hit val **1.0000**, where no larger difference could
have shown. Practically: **the two paths reach the same answer**, which is what the smoke run
found at cap 2 and what R-5 / ml#1093 / E-I found by other routes.

**The wall-clock question is closed too, and the answer is new: there IS a path difference at wide
budgets, and it is about a factor of two.** This is the finding the smoke scale could not reach,
and its §6 said so — *"it does not bound a small one, and it says nothing about behaviour at the
64–128-unit budgets"*.

| | span ratio (CLI / service) |
| --- | --- |
| cap 64 (n=3) | 1.904 ± 0.276 |
| cap 128 (n=2) | 2.031 ± 0.186 |
| init control (n=1) | 2.169 |
| **all six** | **1.99 ± 0.21** |

All six exceed 1.58; the mean sits ~4.7 spreads above parity. Three things make this a measurement
rather than a band:

1. **A shared denominator.** Both arms are timed between the same pair of records around the same
   `CascadeCorrelationNetwork.fit` (§2.2a) — the thing the smoke note could not do, and which only
   became possible for the service arm with juniper-cascor#523.
2. **It is localised.** The output phase is identical on every replicate (1.03–1.05×, and both
   arms ran exactly 130,000 output epochs on cap-64 r0). **100% of the difference is the candidate
   phase**, which is ~98% of the training span at these caps.
3. **The obvious confounds are eliminated, not assumed away.** Configuration is equal down to the
   CLI's private `_SPIRAL_PROBLEM_*` constant tier (§3); the datasets are the same content
   addresses; the initialisation asymmetry was removed by direct experiment (§4.4) and the gap got
   *wider*; and host load differed by 8% across the control's two arms.

**Why the smoke run saw none of this.** The gap lives in the candidate phase and therefore
compounds per growth iteration. At a 2-unit cap there are ~2 candidate phases and the effect is
invisible — the smoke run measured 36 s vs 46 s and 35 s vs 35 s. At 64–128 units there are 64–128
of them and the candidate phase is 98% of the run. The two results are consistent; this one simply
operates where the term matters.

**One mechanism explains both axes.** The CLI's candidates run to ~91% of their 500-epoch budget
where the service's stop at ~63%, so the CLI buys marginally better candidates (hence the ~+0.75 pp)
by spending markedly more time (hence the ~2×). The service's per-iteration candidate cost *falls*
across a run (79.6 → 54.6 s/iter on cap-64 r0) as early stopping fires more readily; the CLI's
*rises* (104.1 → 114.0), so the two diverge as the cascade widens.

**What this does NOT settle.** The *cause* of that divergence is not identified. The residual
splits into ~1.6× more candidate epochs and ~1.4× lower per-candidate-epoch throughput, and both
survive the control. Every configuration explanation was checked and eliminated, so the remaining
candidates are runtime-level (process/thread topology of the candidate pool under uvicorn vs a
bare script, forkserver warmth, RNG-stream divergence feeding the early-stopping criterion). That
is a new question this campaign opens, not one it closes — see §8.

**Unaffected by all of the above:** F-5 remains **FALSE** — the service tier is not accuracy-
handicapped. If anything the service reaches comparable accuracy in half the wall-clock.

---

## 6. Honest limits

Ordered by how much they constrain the headline.

**1. The mechanism behind the ~2× is not identified — and the "every configuration explanation was
eliminated" claim below was WRONG.** *(Updated 2026-08-20.)* The gap is real, reproduces six times,
is confined to the candidate phase, and survives both the initialisation control and a contention
check. But the sentence "Every configuration explanation was checked and eliminated (§3), which
narrows it to the runtime level" did not hold: **juniper-cascor#531** found that the two entry
points loaded BLAS with *different thread pools* — `main.py` capped `OMP_/MKL_/OPENBLAS_NUM_THREADS`
to 2, `uvicorn api.app:create_app` never executed that code — and #531 reported that cap as **1.30× of
a 1.52×** candidate-phase penalty at cap 16, acting through throughput *and* through epoch count
(thread count changes BLAS reduction order, hence where a patience-based early stop fires).

§3's equalisation was not sloppy; it was scoped to what a config file can express, and this was a
decision made by *which file the process started in*. That is the lesson worth carrying: "every
configuration key is equalised" is not the same statement as "the two processes are configured
identically". Fixed in **#533** (one policy in `parallelism/blas_threads.py`, default no-op, opt in
via `JUNIPER_CASCOR_BLAS_THREADS`). A residual remains and is unmeasured on post-#533 `main`.

**2. The two arms' seed spreads are not commensurate, and are never pooled here.** Varying
`dataset.params.seed` gives a fresh data draw on both arms but a fresh network init on the **CLI
arm only** (§2.4). Every service replicate re-seeds to 42. So the service spread bounds data-draw
variance and the CLI spread bounds data-draw + init variance; §4 reports them separately and the
headline uses the *paired* statistic, which differences within a replicate and is unaffected. This
was predicted before the run and is why the init control (§4.4) was run — the control then showed
the asymmetry does not drive the wall-clock result, but it remains a limit on the *unpaired*
per-arm spreads, which are the only figures that would have inherited it.

**2a. The control equalises the seed, not the trajectory.** §4.4's two runs diverge after the
first output pass. What was controlled is the structural seed asymmetry; the runs are not the same
run. A stricter control would need determinism guarantees neither path currently offers.

**3. The cap-128 accuracy axis is at its ceiling.** Both CLI cells returned val exactly **1.0000**.
A ceiling can bound a difference but cannot size one, so the cap-128 Δ val of +0.75 pp is a
*lower* bound on nothing and an upper bound on the CLI's advantage — it is not a measurement of it.
The cap-64 replicates, at 0.97–0.995, are the ones carrying real accuracy resolution.

**4. Cap 128 was reduced to two replicates.** n = 2, and no 3-seed spread at 128 units exists. The
cap-64 measurements showed a CLI arm costs ~1.8-2× its service counterpart, which put the full
design near 23 h against the ~12 h this was scoped for; the hours went to the init control instead
(rationale in `e-j-h2h-wide-cap128.yaml`'s header). That is a deliberate trade, not an accident,
and the cap-128 figures must always be quoted with their n.

**5. Host contention is uncontrolled for the cap-64 pairs.** The arms must run in different time
windows — sharing 16 cores would inflate both walls — so this is a shared desktop measured at
different times. A load sampler ran from 13:26 onward (mean load1 11.6 in the cap-64 CLI window vs
11.0 in the cap-128 service window, on 16 cores, so those two are comparable), but the cap-64
*service* cells ran before it started and have no contemporaneous record. The span ratios should
be read as "measured under broadly similar but not pinned host conditions".

**6. The service arm's cap did not bind at 128.** Its cells stopped at 97 and 69 units on training
saturation, so the cap-128 service column measures headroom, not capacity. Only the cap-64 cells
(and both cap-128 CLI cells) are cap-bound runs.

**7. These accuracies are not on E-I's capacity curve, for two independent reasons.** The
equalisation doctrine forced `candidate_patience` to the module default 50 where
`spiral-baseline` — which E-I inherited — sets 100; and `output_epochs` is pinned at 2000 here
where E-I left it at the 10000 default (§2.2). E-I's curve identified 64–128 units as the region
worth probing; it is a targeting rationale and must not be used as a baseline for these numbers.

**8. One host, one generator, one difficulty.** Hard spiral only (`n_rotations` 3.0), one machine,
one cascor SHA. The easy spiral was deliberately not run — it saturates at val 1.000 at a cap of 8
(ml#1093), so at these caps it would have cost hours and answered nothing.

**9. Second-resolution timestamps.** The shared training-span denominator comes from log records
stamped to the second, so each endpoint carries ±1 s. At spans of 3500–11000 s that is negligible,
but it is why no ratio is quoted to more than three significant figures.

---

## 7. Reproduction

```bash
# 0. invariants, BEFORE the GPU-hours — materialises every cell through run_suite's own code and
#    asserts the seed derivation, the max_epochs/output_epochs pairing, that no unmapped key moves
#    one arm only, and that max_iterations clears the cap.
python util/ad-hoc/2026-08-16_h2h_preflight.py

# 1. the SERVICE arm (per cap). JUNIPER_EXP_PROJECT_DIR is load-bearing from a worktree: without
#    it base_config resolves under .claude/worktrees/juniper-cascor/... and no cell materialises.
export JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper JUNIPER_EXP_HEALTH_TIMEOUT=180
python util/experiments/run_suite.py --suite util/experiments/suites/p4/e-j-h2h-wide-cap64.yaml
python util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite e-j-h2h-wide-cap64 --expect 3

# 2. the DIRECT-CLI arm over the SAME generated cells, from a dedicated cascor checkout at the
#    same SHA. One stack for the whole suite: the dataset listing it prints before teardown is the
#    equalisation evidence.
util/ad-hoc/2026-08-16_h2h_cli_campaign.bash \
    <SUITE_DIR> <CLI_ROOT> \
    /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--exp--h2h-wide--20260816-0755--3909d275/src

# 3. the INIT CONTROL -- the only cell where both arms share a network initialisation
util/ad-hoc/2026-08-16_h2h_init_control.bash <CLI_ROOT> <CASCOR_SRC>

# 4. both arms into one table, with the equalisation checks re-run as assertions
python util/ad-hoc/2026-08-16_h2h_collect.py --suite-dir <CAP64_SUITE_DIR> --suite-dir <CAP128_SUITE_DIR> \
                                             --suite-dir <INIT42_SUITE_DIR> --cli-root <CLI_ROOT>

# 5. localise any wall-clock difference to a phase before attributing it to anything
python util/ad-hoc/2026-08-16_h2h_phase_split.py <SERVICE_RUN_DIR>/logs <CLI_ARM_DIR>/logs
```

Phases 2-5 were chained by `util/ad-hoc/2026-08-16_h2h_orchestrate.bash` so they ran back to back
and strictly sequentially — two arms sharing 16 cores would inflate both walls, and this workload
is CPU-bound (GPU utilisation stayed at ~1%; the candidate pool is ~8 forked workers at ~90% CPU
each). `util/ad-hoc/2026-08-16_h2h_load_sampler.bash` recorded host load per minute alongside.

Two supporting tools exist because the campaign needed them, and both are worth keeping:

* `2026-08-16_h2h_preflight.py` materialises every cell through `run_suite`'s own code and asserts
  the invariants **before** the compute is spent. It caught two design errors during setup.
* `2026-08-16_h2h_marker_sentinel.bash` tails each run's parent log from line 1 into a
  rotation-proof `markers.txt`. juniper-cascor#523 gave each run its own log but does not stop that
  log **rotating within a run**: the first cap-64 cell wrote ~950 MB and rotated, leaving the
  `fit:` start marker in `juniper_cascor.log.1`. The collector reads rotated segments, but
  `backupCount` is finite and the marker at risk is the one on the first line — so on a long cell
  the training span, which is the whole shared denominator, is exactly what rotation would take.

### 7.1 Evidence and teardown

Evidence preserved under `~/.local/state/juniper-experiments/`: the three suite dirs (each with
`registry.jsonl`, `aggregate.csv`, `REPORT.md` and the per-cell resolved `experiment.yaml`), the
per-cell service run dirs (manifest, `artifacts/results/`, per-run `logs/juniper_cascor.log*`), and
`h2h-wide-2026-08-16/` holding every CLI arm's `cli_arm.json`, `direct_cli.log`, per-run parent log
and the per-suite `datasets.json` equalisation listing, plus `host_load.tsv`. ~9 GB for the CLI
side alone; `artifacts/` preserved throughout.

**Teardown attested** after the final run: experiment ranges **8110-8139 / 8230-8259 / 8260-8289 —
0 listeners**; **0** stale lockdirs under `/run/user/1000/juniper-experiments`; `artifacts/`
preserved; `util/reap_pytest_orphans.bash --dry-run` → **0 would be reaped**. None of this
campaign's runs used an operator port.

The reaper does report **1 protected** process — the pre-existing isolated E2E stack's cascor on
`:8202`, which something restarted at 04:06 during the control arm. On the tree this campaign ran
against, that process was reported `WOULD REAP`: the long-standing nohup / `systemd --user` false
positive. juniper-ml#1133 landed the fix while this campaign was in flight, and it now classifies
correctly as `PROTECT … (live experiment)`. Worth recording because the campaign is a live example
of exactly the class #1133 addresses — a long-running experiment stack that the old heuristic would
have offered to kill.

---

## 8. Disposition

| item | status |
| --- | --- |
| **Wide-budget head-to-head (64–128 units)** — the smoke note's one OPEN row | **CLOSED** (§5) — but see the two SUPERSEDED rows at the foot of this table before quoting either headline number. Accuracy: no gap worth acting on, +0.75 ± 0.52 pp over six paired replicates. Wall clock: a **1.99 ± 0.21×** CLI penalty, wholly in the candidate phase, **measured pre-#533** |
| Shared wall-clock denominator (smoke §6 limit 2) | **REPAIRED** (§2.2a) — both arms timed between the same `fit:` records; possible for the service arm only since juniper-cascor#523 |
| Smoke scale / one seed (smoke §6 limit 1) | **REPAIRED** — 6 paired replicates, paired statistics, spreads reported per arm and never pooled |
| Both arms on one cascor SHA (smoke front-matter) | **DONE** — `3909d27` for every one of the 12 runs |
| `n_rotations` 3.0 floored by a 2-unit cap (smoke §6 limit 3) | **RESOLVED** — at 64–128 units the hard spiral reaches 0.97–1.00 on both arms |
| Host state (smoke §6 limit 4) | **PARTIALLY REPAIRED** — per-minute load sampling from 13:26; the control has both arms sampled (load1 8.7 vs 9.4). The cap-64 pairs predate the sampler (§6 limit 5) |
| F-5 "genuine service-tier limitation" | **STILL FALSE** — a fourth independent line; the service matches on accuracy at half the wall clock |
| **Why the CLI's candidate phase costs ~2×** | **SUPERSEDED by juniper-cascor#531/#533** — see the row below. As written this row says "Configuration is excluded (§3)", and that turned out to be wrong in a specific and load-bearing way: the *entry point* was setting BLAS thread counts differently on the two paths (`main.py` capped OMP/MKL/OPENBLAS to 2; `uvicorn api.app:create_app` never ran that code), which is a configuration cause. (#531 sized it at **1.30× of a 1.52×** at cap 16; re-measured rep-paired at k=3 on 2026-08-22 it is **1.016× [0.885, 1.148]** — the asymmetry was real, its cost was not. See the 2026-08-21 residual note §4.3a.) §3's equalisation checked every key the *config file* can express; it could not see a decision made by which file the process started in. Initialisation (§4.4) and contention remain excluded |
| **The 1.99 ± 0.21× headline** | **SUPERSEDED — do not quote as current.** Every one of the 12 runs was cascor `3909d27`, i.e. **pre-#531/#533**: the CLI arm carried `main.py`'s `OMP=2` cap and the service arm did not. The gap on post-#533 `main` has never been measured; doing so is a deliverable of the successor arc. What survives unchanged: 100% of the difference is the candidate phase (output 1.03–1.05×), and it compounds per growth iteration, so a residual measured at cap 16 licenses nothing at cap 64/128 |
| **Reproducibility of every single-run number here** | **QUALIFIED by [juniper-cascor#532](https://github.com/pcalnon/juniper-cascor/issues/532)** — identically-seeded runs do not reliably reproduce. Pairing cancels the data-draw term but not this, so the paired Δval above is sound while any *single-run* figure carries an undeclared spread. Characterised at N=20 in [`JUNIPER_2026-08-20_…SEED-REPRODUCIBILITY-EVIDENCE.md`](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md) |
| 3-seed spread at cap 128 | **NOT MEASURED** — deliberately traded for the init control; n = 2 there (§6 limit 4) |
| R-6 stall-seconds gate blind at pool < 16 | **OPEN** — the gate keys only on `candidate_pool_size >= 16`, so this pool-8 campaign's wide caps were invisible to it and `execution.stall_seconds` had to be set by hand. Widening it to trigger on cap as well as pool remains a useful follow-up (out of scope here) |
