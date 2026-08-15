# HANDOFF 2026-08-15 — wide-budget head-to-head (64–128 units) + methodology hardening

Successor to
[`HANDOFF_2026-08-14_cli-experimentation-p4-arc-complete.md`](HANDOFF_2026-08-14_cli-experimentation-p4-arc-complete.md).

**Nothing is in flight.** No PR of this arc is open in either repo. The P4 arc and its R-1..R-6
follow-up register are closed. What remains is one item that the closing evidence explicitly left
**OPEN and optional** — a *new campaign* that this handoff commissions, not unfinished work
carried over.

Throughout, section references written like "§6" mean a section of **this** document. References
to the source notes are always written with the document named, e.g. "the smoke note's §6".

## Codenames used below

| name | meaning |
|---|---|
| **E-A** | the P4 budget-sweep suite; its R-3 re-run (ml#1086) produced the pool-8 capacity column |
| **E-I** | the cap-ceiling suite that extended that column to 64 and 128 units |
| **R-3** | the fix that made `max_hidden_units` actually bind (before it, caps above `max_iterations` were unreachable) |
| **R-5** | "why does service spiral top out near 0.670 while the CLI reaches ~0.995?" — closed |
| **R-6** | the rule that suites must declare `execution.stall_seconds` (ml#1069) |
| **F-P1-3 / F-P1-3b** | the direct CLI hanging after training / the claim that it had structural compute overhead — **positively refuted by measurement** in ml#1114, not merely withdrawn |
| **F-P4-1** | the trap where the **SERVICE** path trained cascor's in-process fallback spiral instead of the configured juniper-data dataset (fixed by staging every generator through `POST /v1/training/dataset`). **Not a CLI trap** — the R-5 note records that the direct CLI does *not* generate its own spiral; it fetches from juniper-data with a mandatory pre-flight and no fallback. |
| **c000/c010** etc. | individual suite cells, numbered in run order |

---

## 1. What is already settled — do NOT re-measure

Three findings are closed and merged. Re-running them wastes GPU-hours and invites a
contradictory write-up.

| finding | closed by | result |
|---|---|---|
| **R-5** | **ml#1093** (`14be0e2`) | The gap was the **dataset**, not the service tier. At cap 8, moving `n_rotations` 3.0 → 1.0 took val **0.595 → 1.000**. |
| **Head-to-head, smoke scale** | **ml#1114** (`c87a4f2`) | **No path gap** at cap 2 / pool 4: val delta **0.00 pp** (easy) and **+1.00 pp** (hard). |
| **F-5** "genuine service-tier limitation" | ml#1093 + E-I + ml#1114 | **FALSE**, three independent lines. |

The smoke run also recorded walls of 36 s vs 46 s and 35 s vs 35 s. **Do not quote those as a
performance result** — the smoke note itself disowns them as a ratio (see §2.2a); they establish a
band only.

Also already fixed, and load-bearing here:

- **juniper-cascor#517** — the direct CLI hung after training under an interactive matplotlib
  backend (`--no-plots` + a backend guard). Before it, **no completed direct-CLI run existed**.
- **juniper-cascor#522** — the direct CLI ignored the configured output-epoch budget (finding
  L-1). **A pre-#522 checkout is not budget-equalised.**
- **juniper-cascor#514** — made the *configured* `candidate_patience` /
  `candidate_convergence_threshold` actually reach the candidate pool for the first time. For
  `spiral-baseline.yaml` the effect is candidate patience 50 → 100, because that file sets
  `candidate_patience: 100`; the mechanism is broader than that one number. **Spiral figures are
  not comparable across #514** — pin both arms to one side of it (§2.2c).

> **`candidate_patience` is not `patience`.** They are different knobs. `patience` is output-layer
> early stopping and **is** in the CLI's `_W11_TRAINING_KEY_MAP`. `candidate_patience` is the #514
> knob and is **absent** from that map, so the direct CLI cannot receive it at all. The smoke
> configs set only `patience: 50` and never set `candidate_patience`, which fell through to the
> module default **50** on both paths.
> **Leave `candidate_patience` unset** so both arms take the same module default — the
> omit-what-the-CLI-cannot-map rule in §3. Setting it in the shared config would be honoured by the
> service arm and ignored by the CLI arm, de-equalising the very knob #514 is about. If a
> non-default candidate patience is genuinely wanted, this comparison is **not available** until
> `_W11_TRAINING_KEY_MAP` carries the key — say so rather than running it.

Source of record:
[smoke note](../../notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md)
(its §6 limits, its §8 disposition),
[R-5 note](../../notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R5-SERVICE-VS-CLI-EVIDENCE.md),
and — the numeric basis for this campaign's sizing —
[E-I note](../../notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-E-I-CAP-CEILING-EVIDENCE.md).

---

## 2. The task

The smoke note's §8 disposition table leaves exactly one row open — quoted verbatim, it reads:
`| Wide-budget head-to-head (64–128 units) | **OPEN** — optional; §6 bounds what this run does not
cover |`

Close it, **and** repair three methodology weaknesses: two the smoke note's §6 admits (no shared
wall-clock denominator; smoke scale / one seed) and one its front-matter models rather than
confesses (pinning both arms to one cascor SHA). The smoke note's §6 has two further limits, both
handled here: its `n_rotations` 3.0 arm was floored by a 2-unit cap — no longer true at 64–128
units, which is the point of this campaign (§2.1) — and host state, covered in §4.

The goal is a result defensible as a **measurement** rather than as a band.

### 2.1 Why 64–128 specifically

E-I **extended** E-A's pool-8 column upward. The joined curve on the hard spiral
(`n_rotations` 3.0, pool 8):

| units | 4 | 8 | 16 | 32 | 64 | 128 |
|---|---|---|---|---|---|---|
| val | 0.545 | 0.595 | 0.610 | 0.735 | **0.945** | **0.995** |

Attribution, if you re-cite this: the first four points are **E-A's** (R-3 re-run, ml#1086). E-I
ran three cells — it re-ran cap 32 as a **control** (c000, which reproduced E-A's c010 exactly)
and contributed **64 and 128** as new measurements. That reproduced control is the cross-run
anchor that lets both campaigns be read on one axis.

The smoke head-to-head ran at a **2-unit cap**, where the hard arm is floored near chance by
design. 64 and 128 are where the curve is steep and then decelerating into its ceiling — the only
region where a *small* path gap could still hide. The smoke note's §6 says so: "it does not bound
a small one, and it says nothing about behaviour at the 64–128-unit budgets where E-I found the
interesting capacity curve."

### 2.2 The three methodology fixes — the substance

**(a) A shared wall-clock denominator.** The smoke note's §6 is blunt that its walls "share no
denominator": the service figure is the driver's poll-based drive loop, the CLI figure is
whole-process wall including interpreter start and dataset fetch. **Do not report a ratio until
both arms are measured over the same span.**

The promising approach — **verify before relying on it** — is that both paths run the same cascor
training code and emit the same parent log, so a log-derived training span may serve as a common
denominator. The smoke run harvested the CLI parent log and quoted its budget line. Confirm the
service arm emits a comparable line with usable timestamps. If it does not, say so and report the
band, exactly as the smoke run honestly did — an unverified denominator is worse than an admitted
one.

**Find the service arm's log before designing around it.** ml#1120 makes `cascor_up` export
`JUNIPER_CASCOR_LOG_DIR=$RUN_DIR/logs`, so the service arm's cascor writes a **per-run** log
rather than the checkout-shared one. That depends on juniper-cascor#523, which **merged on 2026-08-15** and is on cascor `origin/main`
(`3909d27`) — but was **not** in the local checkout at `3857d1e`, where the export is silently
ignored and the log falls back to `<checkout>/logs/juniper_cascor.log`. So the behaviour turns on
which cascor you pin, and simply pulling changes it. **Check, do not assume.** With #523 the
service arm gets a per-run log (which also removes the §4 shared-checkout rotation hazard for that
arm); without it, both arms share the checkout log and the §4 trap applies to both. The CLI arm is
unaffected either way — `2026-08-14_fp13_verify_fix.bash` hardcodes the checkout path.

**(b) Multiple seeds.** The smoke run was one cell per arm, one seed. At 64–128 units a 1-pp path
delta is inside plausible seed noise, so a single cell cannot distinguish "no gap" from "gap
smaller than our resolution." **Target 3 seeds per arm**, report mean ± sd, and state the
resolution the design achieves. Do not claim a gap smaller than it.

*Decide the seed contract explicitly — the two options are different experiments:*

- **`seed_policy: per_cell` (recommended).** `run_suite` derives `base_seed + cell.index` and
  rewrites **both** `experiment.seed` *and* `dataset.params.seed`. Because juniper-data dataset IDs
  are content-addressed on the dataset params, each replicate is a **fresh data draw on both
  arms**. That is the best error bar available here — but read the asymmetry below before
  designing the claim it supports.
  **You still need something to multiply the cells, and `run_suite` has no replicate primitive.**
  `per_cell` *derives* the seed from the cell index; it does not itself create replicates, and
  `SUITE_KEYS` / `EXECUTION_KEYS` contain no repeat/replicates key. Matrix axes must be dotted
  config paths, and an `experiment.seed` axis is overwritten by the index derivation anyway. So
  **name the structure explicitly in your design** rather than improvising — three operators would
  otherwise pick three different tricks (an inert axis, three `include:` entries, three separate
  suite files), each yielding different derived seeds and different cross-cap comparability.
  Recommended: **one 3-cell suite per cap**, which also makes the dataset-id count predictable
  (§4). Whatever you choose, write it down and state the resulting cell count.
- **Same dataset, varying only network init — NOT AVAILABLE.** Do not attempt it, and do not
  accept a design that claims to. `experiment.seed` reaches **no** training or network-init code
  on either arm: the direct CLI's `_load_experiment_blocks` reads only `dataset.params` and
  `training.params` and never touches the `experiment` block; the service's
  `POST /v1/training/start` body carries only `{start_fresh, epochs?, params}` and `TrainingParams`
  has no seed field; the driver uses `experiment.seed` solely as a `setdefault` for
  `dataset.params.seed` (a no-op once that key is set) plus a manifest record. So pinning the
  dataset and varying `experiment.seed` gives you **byte-identical CLI replicates with zero
  variance** — the worst possible outcome, since it looks like perfect agreement. Varying init
  independently of the data would need a cascor-side seed knob that does not exist; if that
  experiment is wanted, say so and stop, exactly as with `candidate_patience` in §1.

> **The two arms' error bars are NOT commensurate, and you must say so.** Varying
> `dataset.params.seed` gives a fresh data draw on both arms, but a fresh **network init on the CLI
> arm only**. The CLI threads the dataset seed into the network
> (`spiral_problem.py:445` passes `random_seed=self.random_seed`). The service network instead
> seeds from `self.config.random_seed or _CASCADE_CORRELATION_NETWORK_RANDOM_SEED`
> (`cascade_correlation.py:667`), which resolves to `_PROJECT_RANDOM_SEED = 42`, and **nothing the
> driver sends can reach it** — `TrainingParams` has no seed field, the start body is only
> `{start_fresh, epochs?, params}`, and `create_simple_config` receives no seed. With
> `start_fresh: true`, every service replicate re-seeds to the same 42 and initialises an identical
> network.
> **Consequence:** the service spread bounds *data-draw* variance; the CLI spread bounds
> *data-draw + init* variance. Report the two spreads **separately**, record this asymmetry as a
> named limit, and do not present a single pooled resolution as though both arms measured the same
> thing. This is the single most important honesty constraint on the campaign's headline claim.

**Note the `dataset.params.seed` rewrite is conditional** — `run_suite` only rewrites it when the
key already exists in the resolved config. It does exist in `spiral-baseline.yaml` and both smoke
configs, so the effect holds here; a config omitting it would silently diverge.

The E-I precedent suite pins `seed_policy: fixed` with no seed axis, so copying it verbatim yields
N **identical** replicates — the same silent null. This is the single easiest way to waste the
whole campaign.

**(c) Both arms on one side of cascor#514, pinned and recorded.** Record the exact
`juniper-cascor` SHA both arms ran and confirm it is post-#514 / #517 / #522. The smoke note's
**front-matter (its line 4)** models this: a single `Code:` line naming the cascor SHA with its
post-#514/#517/#522 annotation, plus the juniper-ml SHA. (Its §4 "Results" header records
hyperparameters, not SHAs.) This is the one place SHA discipline is stated in this document; §7
records the starting values only.

### 2.3 Scope — decisions already made for you

**Run the hard spiral (`n_rotations` 3.0) only.** The easy arm (1.0) already saturates at val
1.000 at a cap of 8 (ml#1093), so at 64–128 units it is pure ceiling effect: it would cost real
hours and answer nothing. Do **not** run it.

**Pool is 8, not 4.** Copy the smoke configs' *structure*, but not their `candidate_pool_size: 4`.
E-A settled that pool raises candidate correlation but not accuracy, so sweeping pool would
re-measure a closed question, and 8 is what the interesting region was characterised at.

**Caps are 64 and 128.**

**Design:** 2 caps × 2 paths × 3 seeds = **12 runs**.

> **You cannot both equalise the paths and land on E-I's curve. Choose equalisation.**
> E-I's cells inherited `spiral-baseline.yaml`, whose budgets are far larger than the smoke pair's:
> `max_epochs` 2000 vs 100, `candidate_epochs` 500 vs 50, `patience` 200 vs 50, plus
> `candidate_patience: 100`. E-I's matrix overrode only `max_hidden_units`, `candidate_pool_size`,
> `max_iterations` and `outputs.max_wall_seconds`.
> Inheriting `spiral-baseline` would make your absolute numbers comparable to §2.1 — but it sets
> `candidate_patience: 100`, which the CLI **cannot receive** (§1), so the two arms would differ on
> a candidate knob and the head-to-head would be invalid.
> **This campaign's purpose is the path comparison, not extending the capacity curve.** So
> equalise: leave `candidate_patience` unset and set the remaining budget knobs explicitly and
> identically for both arms. Two consequences to state plainly in the write-up:
> **(1)** the absolute accuracies will **not** sit on §2.1's curve — that curve is a *targeting*
> rationale (it identified 64–128 as the interesting region), not a comparison baseline; and
> **(2)** the wall estimate below is derived from E-I's larger per-pass budgets, so treat it as an
> **upper bound**.

**Budget it before starting.** E-I's measured *service* walls were **2907 s at cap 64** and
**4244 s at cap 128** (pool 8). Assuming the CLI arm costs about the same — which the smoke run
supports, where it was equal or faster — that is 3 × 2 × (2907 + 4244) ≈ **11.9 GPU-hours**;
plan for **up to ~14** and expect materially less at smaller per-pass budgets. Re-derive from your
first completed cell rather than trusting this number.

**If you must cut, cut cap-128 seeds first** — but then you no longer have a 3-seed error bar at
128, so report the reduced design explicitly and do not state a 128-unit spread you did not
measure. Silent truncation reads as coverage that was never there.

---

## 3. Configuration

`util/ad-hoc/2026-08-14_h2h_smoke_nrot1.yaml` and `..._nrot3.yaml` are the working design: **one
config file drives both arms**, so there is no second document to drift. They differ in exactly 4
of 35 keys — `experiment.name`, `experiment.description`, `dataset.tags`, and
`dataset.params.n_rotations`; every budget key is byte-identical. Copy that structure, change the
budget per §2.3.

Two files are involved and the keys below belong to different ones: `experiment.*`, `dataset.*`,
`training.*`, `runtime.*` are **run-config** keys and `suite.*` / `execution.*` are **suite** keys
consumed by `run_suite`. `outputs:` is legal in **both** schemas and means different things:
`outputs.max_wall_seconds` / `outputs.plots` below are run-config; the suite's `outputs:` block
holds `suite_dir` / `aggregate`. Do not confuse them.

> **Under a suite, the one-file principle needs one extra step.** The smoke run had no suite, so
> both arms literally read the same hand-written file. `run_suite` instead writes a fully-resolved
> `<suite_dir>/cells/<cell_id>/experiment.yaml` per cell, and the **service** arm runs *that*.
> `fp13_verify_fix.bash` takes a single config path with nothing connecting it to the suite, so
> you must hand the **CLI** arm that same generated cell file — not the hand-written base. Feeding
> it the base would silently give every CLI replicate one seed while the service arm varied, which
> is exactly the comparison this campaign exists to avoid. The §4 equalisation check catches it
> after the fact; catching it beforehand is cheaper.

| key | file | why |
|---|---|---|
| `dataset.params.n_rotations` = 3.0, set **explicitly** | run config | the only dataset knob that differs between paths by default (CLI `_SPIRAL_PROBLEM_NUM_ROTATIONS = 1` vs service baseline 3.0). Leaving it implicit is what invalidated the historical numbers. |
| `algorithm` / `radius` **omitted** | run config | the CLI's `_W11_DATASET_KEY_MAP` carries neither, so it *cannot* send them. Omitting makes equality **structural** rather than an assumption about juniper-data's defaults. |
| `training.params.candidate_pool_size` = **8** | run config | the value the interesting region was characterised at, and E-A settled that sweeping pool re-measures a closed question (§2.3). The smoke pair used 4. Note this alone does **not** make results E-I-comparable — see the §2.3 callout. |
| `training.params.max_hidden_units` = 64 / 128 | run config | the axis under test. |
| `training.params.max_iterations` ≥ largest cap (**128**) | run config | growth adds one unit per iteration, so a lower value stops growth before the cap binds — the R-3 defect in a new costume. See the two caveats after this table. |
| `candidate_patience` **unset** | run config | see the §1 callout — the CLI cannot receive it. This is why you must not inherit `spiral-baseline.yaml`, which sets it to 100 (§2.3). |
| `max_epochs`, `candidate_epochs`, `patience` — set **explicitly** | run config | the smoke pair carries 100 / 50 / 50; `spiral-baseline` (what E-I inherited) carries 2000 / 500 / 200. Whichever you pick, pick it **deliberately and identically for both arms**, and record it — leaving them at the smoke values silently makes every per-pass budget 4–20× smaller than the runs behind §2.1's numbers. All three are in the CLI's `_W11_TRAINING_KEY_MAP`, so both arms honour them. |
| `outputs.max_wall_seconds` **explicit** | run config | the driver's Q-2 budget is what actually ends a run. Unset silently inherits `spiral-baseline`'s 3600 s — the E-I budget trap. E-I used **14400**. |
| `outputs.plots: []` | run config | the CLI renders no plot files, so service-side plotting would add client work to one side of a wall-clock comparison. |
| `suite.seed_policy` | suite | `per_cell` recommended; see §2.2b. `fixed` + copying E-I gives identical replicates. |
| `execution.stall_seconds` = 1200 | suite | the Q-2 stall detector watches `current_epoch`, which **does not advance while the candidate pool trains**, and the candidate phase slows as the cascade widens. A healthy 128-unit cell otherwise reports `stalled`. **Nothing will catch this for you — see the warning below.** |

**The two `max_iterations` caveats.**

1. **`max_iterations` is CLI-unmappable too — but unlike `candidate_patience`, setting it is
   correct here.** It is absent from `_W11_TRAINING_KEY_MAP`
   (`juniper-cascor/src/main.py:238-249`), so it binds only the **service** arm; the CLI's growth
   is bounded by `max_hidden_units` alone. That is *equalising*, not de-equalising: it makes the
   service stop growing at the same place the CLI already does. `candidate_patience` is the
   opposite case — setting it would change candidate behaviour on one arm only. The test is
   whether the key makes the two paths behave the *same* or *differently*. Confirm it worked by
   checking `units == max_hidden_units` on both arms.
2. **Do not cite `derive_epochs_cap` as the reason the cap binds.** It computes
   `effective_iterations = min(max_iterations, max_hidden_units)`
   (`juniper-cascor/src/api/lifecycle/manager.py:1615` is the `def`; the computation is at
   `:1651`), but its own docstring (`:1636-1639`)
   calls that a *reporting/display* budget — the `Epoch: X / Y` denominator canopy consumes — and
   explicitly "not an enforced abort: enforcement stays with the granular limits themselves." The
   **smoke** config headers state this causal story wrongly; keep the rule, drop the bad
   mechanism. (E-I's header invokes the same formula legitimately — as a *cost* model, "cost is
   ~linear in the cap", which the docstring supports — and states the cap-binding reason correctly
   and separately. Do not "fix" it.)

> **CI will not catch a missing `stall_seconds` on this campaign.** The R-6 presence gate in
> `tests/test_experiment_suite_yamls.py` keys **solely on pool size** — `LARGE_POOL_THRESHOLD = 16`
> against `training.params.candidate_pool_size` — and *skips* any suite below it. This campaign
> runs at **pool 8**, so a wide-cap suite that omits `execution.stall_seconds` **passes the gate
> and ships**, then loses its 128-unit cells to a false `stalled` hours in. Two further edges: the
> gate reads only `matrix` / `include`, so a pool inherited from `base_config` is invisible to it;
> and what *is* always gated is key spelling via `run_suite.load_suite` (the `stall_second` typo
> class), not presence. **Set it explicitly and verify by eye.** Widening the gate to trigger on
> cap as well as pool would be a genuinely useful follow-up — it is **not** part of this
> deliverable.

Precedent for a wide-budget suite, including its budget reasoning:
`util/experiments/suites/p4/e-i-cascor-cap-ceiling.yaml`.

---

## 4. Operational traps (each has already cost a campaign)

- **`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing** when
  running suites from a worktree. Without it `base_config` resolves to a non-existent
  `.claude/worktrees/juniper-cascor/…` and **every cell fails to materialise**.
- Use the **JuniperCascor1** python (matplotlib present) and `JUNIPER_EXP_HEALTH_TIMEOUT=180` (the
  stack default is 90, too short for a cold start). Only `JuniperCascor1` and
  `JuniperCascor-DEPRECATED` exist; any instruction naming a plain `JuniperCascor` is stale.
- **Run CLI arms from a dedicated cascor worktree.** Its parent log is
  `<checkout>/logs/juniper_cascor.log`, and a shared checkout gets rotated out from under the run —
  this is how the 2026-08-14 arm evidence was lost. (See §2.2a for whether the *service* arm shares
  that file.)
- **Before starting**: `util/reap_pytest_orphans.bash --dry-run` and identify the live parent;
  `ss -tlnp` for another session's stack. The reaper classifies live **nohup-launched** experiment
  stacks as WOULD REAP (they reparent to `systemd --user`) — read before acting.
- **Host state affects the walls you are measuring.** The smoke run recorded that the isolated E2E
  stack's cascor was up but `STOPPED`/`IDLE`, holding GPU memory without competing for compute.
  Record the equivalent, and prefer an idle GPU for every arm.
- **Reading cap-bound cells**: a cap-bound cell reports `early_stopped`, the same reason as
  patience-exhausted and accuracy-target cells. **The units column disambiguates** —
  `units == max_hidden_units` means the cap bound.
- **Verify equalisation rather than asserting it.** juniper-data dataset IDs are content-addressed,
  so what must hold is that **the two paths of a given replicate resolve to the same id**. That is
  the check that matters. The *total* is **one id per distinct derived seed**. With the
  recommended structure — **two** 3-cell suites, one per cap — `cell["index"]` restarts at 0 for
  each suite, so both derive the *same* three seeds from the same base `experiment.seed`, and you
  will see **3 distinct ids in total, not 6**. That is the design working: it pairs each cap-64
  replicate with a cap-128 replicate on identical data. By contrast a single 6-cell suite would
  derive 6 distinct seeds and 6 ids, with cap-64 and cap-128 sharing no datasets — which is why
  one suite per cap is recommended (§2.2b). Note you will have **6 per-cell config files but only
  3 ids** — fewer ids than configs is correct here; **seeing 6 ids means you built one 6-cell
  suite instead of two 3-cell ones**, and the cap-64/cap-128 pairing is lost. Check with
  `curl -s "<DATA_URL>/v1/datasets?limit=50"`. Also confirm the CLI arm actually fetched from
  juniper-data by finding `Using JuniperData service at …` (`spiral_problem.py:548`) in its parent
  log. **This is not an F-P4-1 check** — the CLI has no in-process fallback to catch (it raises
  `ConfigurationError` / `SpiralDataProviderError` instead), and F-P4-1 was a *service*-path trap;
  see Codenames. It confirms the run reached the right service instance at the right URL.
- Aggregate with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`
  (screens `oom == 0`; exits 1 if an expected cell lacks a clean run).

Reproduction shape, from the smoke note's §7: `util/ad-hoc/2026-08-14_r5_stack_up.bash`, then
`util/experiments/run_experiment.py --config … --run-dir …` for the service arm and
`util/ad-hoc/2026-08-14_fp13_verify_fix.bash <DEDICATED_SRC> <config> <run-dir> <DATA_URL>
<timeout> -- --no-plots` for the CLI arm — and **always**
`util/experiment_stack.bash --down <RUN_ID>` to tear down. A run left up holds one port from each
of the three 30-slot ranges plus its lockdirs, which starves the next campaign.

---

## 5. Deliverable

One evidence note,
`notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md`,
modelled on the smoke note's structure — design, equalisation *proven*, results, what it settles,
**honest limits**, reproduction, disposition. Plus the run-config and suite YAMLs under `util/`.

**Attest teardown in the note**, as the smoke run did: 0 listeners across 8110-8139 / 8230-8259 /
8260-8289, 0 stale lockdirs, `artifacts/` preserved.

Then **update the smoke note's §8 disposition row** so the OPEN item does not outlive its answer.
Propagating a closure into stale registers is a recurring chore here (ml#1118 did exactly that for
F-P1-3b) — do it in the same PR.

**Report the honest outcome.** "No gap detectable at this resolution, and here is the resolution"
is a complete and valuable result. Manufacturing a gap, or claiming one smaller than the seed
spread supports, is the failure mode to avoid. Two limits are already known and **must** appear in
the note's honest-limits section rather than being discovered by a reader: the service and CLI
spreads are **not commensurate** (§2.2b), and the absolute accuracies are **not on E-I's capacity
curve** (§2.3).

---

## 6. Verification commands

Run from the juniper-ml repo root. The first two are pre-flight *and* pre-commit; the rest are
pre-flight.

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
grep -n "Wide-budget" notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md
nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader
util/reap_pytest_orphans.bash --dry-run
python3 -m unittest -v tests/test_experiment_suite_yamls.py   # NOTE: cannot catch a missing
                                                              # stall_seconds at pool 8 (see §3)
```

---

## 7. Git state

**Do not trust a SHA here — re-derive it.** Concurrent sessions push to `main` frequently; during
the 2026-08-15 status pass it moved three times in under an hour, twice while this document was
being written.

- `juniper-ml`: `origin/main` at `181f76d` (ml#1120) when this was written. Expect untracked files
  under `prompts/thread-handoff_automated-prompts/` in the primary checkout — other sessions
  archive handoffs continuously.
- `juniper-cascor`: no open PRs. The local checkout was clean at `3857d1e` (#522) while
  `origin/main` had already moved to `3909d27` (#523) — so a plain `git pull` changes the log
  location. See §2.2a.
- Environment: no experiment listeners on 8110-8139 / 8230-8259 / 8260-8289, no stale lockdirs, no
  reapable orphans, GPU idle apart from desktop applications. The juniper-deploy **Docker** stack
  (canopy 8050, cascor 8201, recurrence 8211) is up; canopy's healthcheck **flaps** (its Docker
  status alternates healthy/unhealthy), so do not read a stable label there. Irrelevant either
  way: it is not the host experiment stack and holds no GPU compute.
