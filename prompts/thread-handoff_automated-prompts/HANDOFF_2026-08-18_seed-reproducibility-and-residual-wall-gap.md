# HANDOFF 2026-08-18 — seeded-run reproducibility (blocker), then the residual CLI-vs-service wall gap

Successor to
[`HANDOFF_2026-08-15_wide-budget-head-to-head-campaign.md`](HANDOFF_2026-08-15_wide-budget-head-to-head-campaign.md).

**Nothing is in flight for this arc.** Every PR it opened is merged; the only open PRs in either
repo are unrelated (dependabot, an ecosystem-port docs PR, and a lockfile-refresh PR). Two tasks
remain and the order between
them is **not** negotiable — see §2.

Throughout, "§N" means a section of **this** document. References to other documents always name
the document. Commands are written to be run from the juniper-ml repo root.

---

## 1. What is settled, and what only LOOKS settled

### 1.1 Genuinely closed — do not re-measure

| finding | closed by | result |
| --- | --- | --- |
| BLAS thread policy split across entry points | **cascor#531** → **cascor#533** (`9a7e7e0`) | `main.py` capped OMP/MKL/OPENBLAS to 2; the service enters via `uvicorn api.app:create_app`, never ran that code, and `src/api/` set nothing. Fixed: one policy in `src/parallelism/blas_threads.py`, called by `main.py` **and `api/__init__.py`** (NOT `api/app.py` — it imports torch at module level, so a call there is silently inert). Default is a no-op; `JUNIPER_CASCOR_BLAS_THREADS` opts in. |
| `max_epochs` without `output_epochs` de-equalises the arms | **ml#1159** (`49cc073`) | Service applies `max_epochs` to the **initial** output pass only; later passes fall back to `output_epochs`' default **10000**. The CLI **aliases** `max_epochs → output_epochs`, so it bounds every pass. Now: driver `validation_warnings` carried **on the manifest**, 3 tests, **§5.6 rule 7** of the CLI-experimentation plan, AGENTS.md. |
| `pair_compare` compared in-flight runs | **ml#1160** (`9fd5b1a`) | A partial trace stops early and diffs like a divergence. Now refuses unless the log carries `Training completed.` |

> **Caveat on #533's safety check.** The service was verified byte-for-byte identical pre/post on
> **2 runs**. Under §3 that is not a determinism proof, so it is evidence #533 was harmless, not
> proof. Re-confirm it from the §3 service arm at N>=20 rather than re-running it standalone.

### 1.2 SUPERSEDED — the headline wall-clock number is stale

The wide-budget campaign (**ml#1143**, `294540a`) measured a span ratio of **1.99 ± 0.21** over 6
paired replicates. **Do not quote that number as current.** It ran on cascor **`3909d27`**, which is
**pre-#531/#533**: its CLI arm carried `main.py`'s `OMP=2` cap and its service arm did not. §4.1 puts that cap at
**1.30× of a 1.52×** candidate-phase penalty (cap-16 probe). The wide-budget gap
**on post-#533 main has never been measured**, and doing so is a §4 deliverable.

What survives from ml#1143 unchanged:

- **100% of the wall-clock difference is the candidate phase.** Output phase 1.03-1.05×, with both
  arms running exactly 130,000 output epochs on cap-64 r0.
- **The gap compounds per growth iteration** — which is why the 2-unit smoke run saw none of it.
  A residual measured at cap 16 therefore licenses **nothing** at cap 64/128 (see §4.1).

### 1.3 Accuracy: a small, consistent, ceiling-compressed delta

ml#1143 measured a paired Δval of **+0.75 ± 0.52 pp**, where **Δ = CLI − service** (so the CLI is
marginally ahead), over 6 paired replicates, one exactly 0.00.

Be careful how this is read. That the delta is ≥ 0 in 6 of 6 replicates is evidence of a **small
systematic** difference, not of "no difference" — do not cite the sign consistency as if it argued
the delta away. The reason it is nonetheless judged unimportant is **ceiling compression**: both
arms sat at 0.97-1.00, and at cap 128 both CLI arms hit exactly 1.0000, so a positive delta could
only be bounded there, never sized (limit 3 of
`notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md`).

Pairing cancels the **data-draw** term; it does **not** cancel §3's run-to-run nondeterminism,
whose per-run spread (~10 pp) dwarfs ±0.5 pp. **Treat "no accuracy gap worth acting on" as
well-supported but not immune to §3**; if §3 finds the service arm is also nondeterministic,
revisit rather than assume.

### 1.4 Open, not in scope unless you choose to take it

**cascor#530** — `TrainingParams` has no seed field, so the service network seed is unconditionally
**42** and no API caller can change it. Not required for §3 or §4, but relevant: a real seed field
would let the harness distinguish *"deterministic at seed 42"* from *"deterministic"*. Its own body
flags a follow-on worth carrying if you fix it — `_CANDIDATE_UNIT_RANDOM_SEED` (`constants.py:1046`)
must reach the candidate pool too, or it recreates the #505 class where configured knobs never
reached the workers.

---

## 2. Why reproducibility blocks the residual

**cascor#532**: identically seeded runs do not reproduce. Same content-addressed dataset, same
network seed 42, same thread budget, same checkout, same host — and runs diverge mid-training.
**3 of 5 run-pairs diverged**, with spreads up to **10 pp** validation accuracy and **16%** candidate
work.

Be precise about which measurements this threatens, because it is not all of them:

| §4 component | size | status under #532 |
| --- | --- | --- |
| candidate **epoch count** ratio | 1.03× | **swamped** — 16% run-to-run noise is larger |
| per-candidate-**epoch rate** ratio | 1.14× | **partially corroborated** — CLI n=3 across budgets (0.02394 / 0.02402 / 0.02641, itself a 10% spread) but **service n=1** (0.02102), so the denominator has no error bar |
| candidate-phase **span** ratio | 1.17× | **essentially unmeasured** — n=1 (1485 s vs 1441 s, **3%**), and that pair **did diverge** (val 0.8650 vs 0.7650) |

So the honest statement is *not* "any residual number is uninterpretable". It is:

- the **epoch-count** component (1.03×) is below a 16% run-to-run spread and cannot currently be claimed;
- the **rate** component (1.14×) is the strongest surviving signal, but its service denominator is n=1;
- the **span** component (1.17×) has exactly one repeated observation, at 3%. Note the tension that
  single point creates: 3% span variation alongside 16% candidate-work variation is only
  reconcilable if the two move oppositely, and it comes from a pair that **diverged** by 10 pp in
  accuracy — so a small span spread does **not** imply a stable trajectory. One point cannot bound
  the diverging population either way.

§3's harness must raise all three to N>=20 (§3.5 item 4). That is the concrete reason §3 precedes §4.

**§3 first. §4 only after §3 reaches its exit condition (§3.7).**

---

## 3. TASK ONE (blocker) — characterise, then root-cause, the nondeterminism

### 3.1 What is already known — do not re-derive

Divergence is **not** at the start: two cap-16 runs were bit-identical through iteration 1 and first
differed at iteration 2. That rules out the dataset, the network initialisation, and the first
candidate round by construction.

| configuration | first divergence | the two values (train loss) |
| --- | --- | --- |
| cap 16, `OMP=2` (pre-#533 tree) | iteration 2 | `0.229579` / `0.228024` |
| cap 4, `OMP=2` via RC-1 default (pre-#533 tree) | iteration 2 | `0.229579` / `0.228024` |
| cap 4, threads unset (post-#533 tree) | **iteration 1** | `0.235021` / `0.235058` |

The divergence point and value pair are **configuration-dependent**; an earlier claim that
divergence always lands on two values at iteration 2 was **withdrawn**. Note the last row differs in
the 5th significant figure vs the 3rd above it — at least as consistent with **accumulating
floating-point divergence** as with a discrete branch.

**Ruled out, with evidence — do not re-check:**

- **Thread count as the driver.** Two pairs at the *same* budget behaved differently, and #533
  (which unsets the env) does **not** fix it — a pair on the patched tree still diverged.
- **Dropped candidates.** Neither early-exit in `_collect_training_results` fired; all 8 candidates
  collected every round.
- **Candidate seeding / worker assignment.** Each `CandidateUnit` seeds from
  `random_seed + candidate_index` (`candidate_unit.py:207`), so a candidate's outcome does not
  depend on which worker ran it.

### 3.2 The one live code lead (and one that is NOT)

The list `results` is built in **arrival order** off the multiprocessing result queue, which is
timing-dependent. Exactly one consumer of that ordering is reachable on this campaign's config:

1. `cascade_correlation.py` `_process_training_results` —
   `results.sort(key=lambda r: (r.correlation is not None, np.abs(r.correlation)), reverse=True)`
   then `best_candidate_id = results[0].candidate_id`. `list.sort` is **stable**, so a tie is broken
   by whichever worker finished first. A deterministic secondary key (e.g. `candidate_id`) would be
   a cheap fix — but see §3.7: do not implement before the rate exists.
**NOT a lead — do not chase it.** `_select_best_candidates` (with its order-sensitive
`rng.sample(sorted_eligible, ...)`) is **unreachable** here: `grow_network` calls it only
`if effective_count > 1`, and `_effective_candidate_count()` returns 1 unless
`candidates_per_layer > 1` (never assigned) or `multi_candidate` is True (defaults False). Even if
reached, `rng.sample` sits in the `random` / `mixed` strategy branches while the default
`candidate_selection` is `top`, a pure slice that touches no RNG. Neither knob is set by the
campaign config, and neither is in the CLI's `_W11_TRAINING_KEY_MAP`. It becomes a lead only if a
future config enables multi-candidate selection.

(Line numbers shifted with #533; grep the function names rather than trusting a line number.)

### 3.3 Running the two arms — actual commands

Both arms share one **materialised** cell config. `--dry-run` does **not** materialise cells, so the
suite must be run for real once.

```bash
export JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper
export JUNIPER_EXP_HEALTH_TIMEOUT=180
PY=/opt/miniforge3/envs/JuniperCascor1/bin/python

# (a) materialise the cell + get one SERVICE run (~229 s)
$PY util/experiments/run_suite.py --suite util/experiments/suites/p4/e-l-determinism-cap4.yaml
SUITE_DIR=$(ls -dt ~/.local/state/juniper-experiments/suites/e-l-determinism-cap4-* | head -1)
CELL=$(find "$SUITE_DIR/cells" -mindepth 1 -maxdepth 1 -type d | head -1)

# (b) N CLI runs (~300-335 s each) against ONE stack. thread_probe starts nothing itself, so the
#     stack must be brought up first; eval binds RUN_ID/DATA_URL/RUN_DIR from its banner.
eval "$(bash util/ad-hoc/2026-08-14_r5_stack_up.bash)"
CASCOR_SRC=<fresh post-#533 cascor worktree>/src      # see §7: dedicated checkout, NOT the shared one
git -C "$CASCOR_SRC/.." rev-parse HEAD                 # record the SHA in the evidence note
for i in $(seq 1 20); do
  bash util/ad-hoc/2026-08-17_h2h_thread_probe.bash \
       "$CASCOR_SRC" "$CELL/experiment.yaml" "$OUT_ROOT/cli-$i" "$DATA_URL" 3600 default
done
bash util/experiment_stack.bash --down "$RUN_ID"
```

- `CASCOR_SRC` is the **`src/` directory of a cascor checkout** — per §7 a **dedicated worktree cut
  from post-#533 main**, not the shared `juniper-cascor/src`. It is **not** the same thing as §7's
  `CASCOR_SRC_DIR`, which is how `experiment_stack.bash` finds the checkout for the *service*.
- `SUITE_DIR` above is used only to locate `$CELL`. If you ever run
  `2026-08-18_h2h_determinism_sweep.bash`, its first argument is that same **materialised run
  directory** under `~/.local/state/juniper-experiments/suites/`, **not** the YAML.
- On **post-#533 main, `default` means genuinely unset** (a no-op). `thread_probe.bash`'s header
still describes it as RC-1's cap-to-2 — that wording is stale. Record the cascor SHA you ran:
`git -C <CASCOR_SRC>/.. rev-parse HEAD`.

Reuse ONE stack across all N CLI runs; `r5_stack_up.bash` resolves "the newest run dir with a
  `ports.json`", so do not launch anything else concurrently.
- Output lands under `<OUT_DIR>/{direct_cli.log,thread_probe.json,logs/juniper_cascor.log*}`.

### 3.4 Getting N runs per arm

**CLI arm**: loop `thread_probe.bash` N times against the one stack, varying only `<OUT_DIR>`.
Do **not** use `2026-08-18_h2h_determinism_sweep.bash` as-is: it is *pair*-shaped **and**
*thread-budget*-shaped (`for threads in 1 2 default; do for rep in a b`), so 4 of its 6 runs re-test
a variable §3.1 already ruled out.

**Service arm**: `run_suite` has **no replicate primitive**. Expand the suite with an inert
20-valued **`experiment.description`** matrix axis — the only legal, side-effect-free key
(`run_experiment.py` `EXPERIMENT_KEYS` is `{name, description, seed}` and `materialise_cell`
overwrites `name`). **Closest precedent**: `e-l-determinism-cap4.yaml` already carries a 1-valued
`matrix: {experiment.description: [...]}` axis — expanding that list to 20 is a one-line edit.
`util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml` shows the same idea via `include:`
entries if you prefer that form.

> **`seed_policy` MUST stay `fixed`.** `per_cell` derives `base_seed + cell.index`, so a 20-cell
> expansion silently becomes a **20-seed sweep** and reports a false "20 distinct outcomes, 100%
> nondeterministic". Keep `dataset.params.seed` and `experiment.seed` pinned at 42.

Any edited/new suite must still pass `tests/test_experiment_suite_yamls.py` (unknown `execution:`
keys are rejected). Keep `execution.stall_seconds: 1200`. The R-6 CI gate in `tests/test_experiment_suite_yamls.py`
triggers on `candidate_pool_size >= 16` **OR** `max_hidden_units >= 64` (the cap arm landed in
ml#1142) — **this campaign is cap 4 / pool 8, so neither fires and CI will NOT catch its
absence**, and a healthy cell then reports a false `stalled`.

### 3.5 Harness requirements

1. **Report a RATE, never a verdict from one pair.** The single most important constraint: three
   conclusions in this arc were withdrawn for generalising from small samples (§6).
2. **N >= 20 RUNS per arm, at cap 4** (= 10 pairs). Cap 4 because §3.1 shows divergence inside the
   first two iterations, so it buys the same signal at ~1/5 the cost of cap 16. If the rate lands
   near 50% and you need a tighter interval, extend rather than re-plan.
3. **Both arms.** The service reproduced bit-identically twice at cap 16 — that is **2 samples** and
   establishes nothing against a ~50%-of-pairs effect. The service is **UNTESTED, not immune**.
4. **Capture timing, not just outcomes** — per run: training span, candidate-phase span, candidate
   epoch count, s/candidate-epoch; report mean ± sd per arm. Without this §4 has no noise floor and
   you will need a second N-run campaign. `util/ad-hoc/2026-08-16_h2h_phase_split.py` already
   computes the phase split; `grep -c "CandidateUnit: train: Epoch" <run>/direct_cli.log` gives the candidate-epoch
   **record** count — **multiply by 10** for epochs (§4.1's 44,910 / 46,080 are the ×10 forms of
   raw counts 4,491 / 4,608). Anchor on the message text, not `candidate_unit.py: 695`: that line
   number shifts and a stale token silently returns 0. Assert the count is non-zero.
5. **Define "outcome" explicitly.** Recommended: the full per-iteration `grow_network` trace
   (loss, accuracy), since a cap-4 run has only 3 iterations and final-value identity is coarse.
   Report `n_runs`, `n_distinct_outcomes`, the outcome histogram, and the divergence-point histogram.
6. **Fix the grouping.** `2026-08-18_h2h_pair_compare.py` groups on a `-a`/`-b` suffix and does
   `a, b = runs[0], runs[1]` — members 3..N are **read and silently dropped**, and service run dirs
   (unique RUN_IDs) never group at all. An N-run harness must not inherit that. Keep its in-flight
   guard (ml#1160).
7. **Placement**: `util/ad-hoc/<YYYY-MM-DD>_<name>.py` with the standard header block, per the
   script-placement rule. Keep `pair_compare` working for its current callers or update them.
8. **Caveat when comparing arms**: the CLI's final accuracies come from `SpiralProblem.evaluate`'s
   post-fit `calculate_accuracy` pair; the service's come from `fit`'s own call sites. Same function,
   different provenance — verify they are comparable before reporting a cross-arm accuracy delta.

### 3.6 Cost

| item | count | each | total |
| --- | --- | --- | --- |
| CLI runs | 20 | ~305 s | ~1.7 h |
| Service runs | 20 | ~229 s | ~1.3 h |
| **characterisation subtotal** | | | **~3.0 h** |
| post-fix re-run (§3.7a), **both arms** | 20 + 20 | ~305 / ~229 s | ~3.0 h |

Arms must run **sequentially** (§7), and `run_suite` refuses parallel cascor cells, so there is no
compression. Budget **~3.0-3.2 h to characterise** (the upper figure uses the 335 s top of the CLI band) and
**~6 h including a §3.7(a) fix verification** — that re-run must cover **both** arms, since a fix
to a shared code path could regress the service. Add harness authoring and any cascor
instrumentation. Re-derive from your first completed run rather than trusting these.

### 3.7 Exit condition

§3 is complete when **either**:

- **(a) Fixed** — a root cause is identified, a cascor PR lands, and the harness re-run at N>=20
  shows a divergence rate of **0**; or
- **(b) Characterised and accepted** — the rate, the divergence points, and the timing noise floor
  are published, with a stated reason the cause cannot currently be removed.

Under (a), §4 proceeds as written. **Under (b), §4 must be re-planned**: single-run A/Bs are invalid,
so every §4 number becomes a many-run mean ± sd sized against the measured noise floor.

> **Both branches depart from the requester's wording, deliberately — confirm before relying on
> either.** The ask was to return to the residual *after the blocker is **resolved***. (b) permits
> proceeding when it is explicitly **not** resolved (justified only if the cause proves
> environmental), and (a) adds a fix-PR that goes beyond the literal "investigate". Under (b) the
> cause must be **identified but not removable**, or the search **documented as exhausted** — "we
> could not find it" is not an exit.

---

## 4. TASK TWO (blocked on §3) — the residual wall gap

### 4.1 What the residual actually is, and at what scale

From the **cap-16 `e-k` thread probe** in cascor#531 — **not** from the wide-budget campaign:

| | service | CLI @ `OMP=16` | ratio |
| --- | --- | --- | --- |
| candidate phase | 944 s | 1103 s | **1.17×** |
| candidate epochs | 44,910 | 46,080 | 1.03× |
| per-epoch rate | 0.02102 s | 0.02394 s | 1.14× |
| output phase | 16 s | 16 s | 1.00× |

**Every figure is a single run per arm**, hence §2/§3. And because the gap **compounds per growth
iteration**, a cap-16 residual says nothing about cap 64/128 — the wide-budget campaign saw ~2.09×
candidate ratio at cap 64 (pre-#533).

### 4.2 Already eliminated — verified at runtime, do not re-check

Configuration down to the CLI's private `_SPIRAL_PROBLEM_*` tier passed into the network config
(`convergence_threshold` 0.001, `candidate_learning_rate` 0.1, `candidate_patience` 50,
`candidate_convergence_threshold` 0.001, `random_value_scale` 0.1, `epochs_max` 100000000000, display
frequencies 10) — all identical to the service's config defaults. Architecture identical
(`input_size 2`, `output_size 2`, `Tanh`, same unit count). Thread budget — that was #531. Host
contention — 8% load1 difference. Logging volume — 30.3 vs 31.5 lines per candidate epoch.

### 4.3 Deliverable A — re-measure on post-#533 main

The 1.99× is superseded (§1.2). Re-measure the cap-64 ratio on post-#533 main, both arms at the **same recorded cascor SHA**.

**How many pairs is conditional on §3.7**, because a single pair is exactly the design §2, §4.1 and
§6 call invalid:

- **Under §3.7(a)** (divergence rate 0): one pair is licensed — the instrument is deterministic.
- **Under §3.7(b)** (nondeterminism accepted): **k pairs**, with k sized from §3's measured span
  noise floor so the interval is narrower than the effect being claimed. State k and its
  derivation in the note; do not publish a single-pair ratio.

This is the highest-value measurement available and it sizes everything else.

### 4.4 Deliverable B — root cause

Remaining hypotheses, all runtime-level:

- Candidate-pool process/thread topology differs between a forkserver child of `uvicorn` and one of
  a bare script (allocator state, copy-on-write layout, forkserver warmth).
- **Candidate early stopping still terminating differently at matched threads.** #531 showed the
  epoch ratio collapsing 1.21× → 1.03× at matched budgets, superseding the wide-budget note's
  "91% vs 63% of the epoch budget" mechanism — but 1.03× is not 1.00×. Cheap check:
  `grep -c "candidate_unit.py: 695"` per arm, now with §3's error bars.
- The service's drive loop polls `/metrics` every 5 s — a headwind the service overcomes, so the
  true gap may be *larger* than measured.

Prefer **profiling a candidate worker on each path** (`py-spy`, `cProfile` on one worker) over more
end-to-end timing: end-to-end is the instrument §3 shows to be noisy.

### 4.5 Deliverable C — impact

Quantify what the gap costs, so the fix can be prioritised honestly:

- wall-clock per campaign-hour at the caps actually used (64/128), not cap 16;
- consequences for `outputs.max_wall_seconds` sizing and for `execution.per_run_timeout_seconds`;
- bearing on the **gated perf lane** (§12 of
  `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`,
  phased in `notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`)
  — whether CLI and service numbers can share a baseline at all, and what that implies for its P3
  regression thresholds.

### 4.6 Deliverable D — fix

Design → cascor PR → verification arm at a matched SHA → a regression guard so it cannot silently
return. If the root cause proves environmental rather than fixable in cascor, say so explicitly and
record it as an accepted, documented asymmetry instead.

---

## 5. Deliverables and acceptance

| # | artifact | done when |
| --- | --- | --- |
| 1 | Determinism harness under `util/ad-hoc/`, merged | N>=20 both arms, reports a rate + timing distributions (§3.5) |
| 2 | Evidence note `notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md` | design, rate, divergence localisation, noise floor, honest limits, reproduction, disposition |
| 3 | Rate + findings posted to **cascor#532** | comment added; **also edit its title/body** — both still carry the superseded "~1 in 5" per-run rate, corrected only in a comment |
| 4 | §3.7 outcome recorded (fixed, or characterised-and-accepted) | stated explicitly in the note's disposition |
| 5A | §4.3 re-measure on post-#533 main | current cap-64 ratio published with the recorded cascor SHA and the pair count k (§4.3) |
| 5B | §4.4 root cause | a named mechanism with per-path profile evidence, **or** an explicit "not identified" with what was excluded |
| 5C | §4.5 impact | cost quantified at the caps actually used (64/128) with the perf-lane baseline implication written down |
| 5D | §4.6 fix | cascor PR merged + a regression guard, **or** a recorded, justified accepted asymmetry |
| 6 | Register propagation, same PR | see §5.1 |
| 7 | Teardown attestation in the note | 0 listeners on 8110-8139 / 8230-8259 / 8260-8289, 0 stale lockdirs, `artifacts/` preserved |

**Report the honest outcome.** "The rate is X% and here is the noise floor" is a complete result.
Manufacturing a cause, or quoting a rate from too few runs, is the failure mode this arc has already
hit three times (§6).

### 5.1 Register propagation (the recurring chore)

Already corrected on 2026-08-18: the withdrawn *"the service is deterministic"* claim in the `e-l`
suite header and the determinism-sweep header, and the perf-lane register (row G closed; **G1**
blocker and **G2** residual rows added).

**Still stale in `e-l-determinism-cap4.yaml`**: its header still prescribes the *pair-and-thread-
budget* design §3.4 supersedes ("at several thread budgets, **twice each**") and still calls the
service run a "control" rather than an N>=20 arm. Update it when you expand the suite.

**Still stale — propagate when you publish:**

- `notes/JUNIPER_2026-08-16_…WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md` §5 says *"Configuration is
  excluded"* — #531 is precisely a configuration/entry-point cause worth 1.30×; its §8 and limit 1
  need the same treatment, plus a note that the 1.99× is pre-#533.
- `notes/JUNIPER_2026-08-14_…HEAD-TO-HEAD-SMOKE-EVIDENCE.md` §5's scale qualifier quotes 1.99×.
- **cascor#532** title and body (item 3 above).

---

## 6. Methodology constraints — read before running anything

Three claims were made and **withdrawn** during this arc, all by the same error: generalising a
mechanism from too few samples.

1. *"19.5 pp accuracy spread is monotonic in thread count, not noise"* — three ordered points; a
   fourth at a duplicate setting landed outside the pattern.
2. *"The service is deterministic, the CLI is not"* — two service runs, against an effect that fires
   in ~half of pairs.
3. *"Every divergence lands on one of two values at iteration 2"* — one thread configuration.

Also: `2026-08-18_h2h_pair_compare.py` once reported a confident `NONDETERMINISTIC` verdict from a
**still-running** log. Guarded in ml#1160.

**The rule this arc earned: on a ~50%-of-pairs stochastic effect, no small sample supports a
mechanism claim. Report rates over N>=20, not verdicts over pairs.** Apply it to your own results,
including any this handoff invites.

---

## 7. Operational notes

- `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing from a worktree.
  For **this** suite the symptom is not a materialisation failure — `e-l`'s `base_config` is
  in-repo and resolves literally — it is that `experiment_stack.bash` derives
  `CASCOR_SRC_DIR="${PROJECT_DIR}/juniper-cascor/src"` from its own location and, unset, looks for
  the cascor checkout **under the session worktree**, so the service leg never launches. Cells
  materialising fine is not evidence the export is unnecessary.
- **JuniperCascor1** python (`thread_probe.bash` defaults to it; override with `JUNIPER_H2H_PYTHON`)
  and `JUNIPER_EXP_HEALTH_TIMEOUT=180` (stack default 90 is too short for a cold start).
- Workload is **CPU**-bound: ~8 forked candidate workers at ~90% CPU each, GPU ~1%. "GPU-hours" is a
  misnomer, and **arms must run sequentially** or any wall comparison is void.
- **One recorded cascor SHA for both arms.** Post-#533 `main` **is** the patched tree — the
  `patched-project` symlink farm is obsolete, and the pre-#533 CLI worktree
  (`…juniper-cascor--exp--h2h-wide--20260816-0755--3909d275`) must **not** be reused: it silently
  re-inserts the BLAS cap into the CLI arm. Cut a fresh cascor worktree at post-#533 main and record
  the SHA. (The `…blas-thread-entrypoint-parity…` worktree is merged and removable — but
  `patched-project/juniper-cascor` symlinks into it, so drop the farm first or the link dangles.)
- Run CLI arms from a **dedicated** cascor checkout: the parent log is `<checkout>/logs/`, and a
  shared checkout gets rotated out from under the run (how the 2026-08-14 arm evidence was lost).
  `thread_probe.bash` sidesteps this by setting `JUNIPER_CASCOR_LOG_DIR` per run.
- A cascor parent log **rotates within a single run** (a cap-64 cell wrote ~950 MB, leaving the
  `fit:` start marker in `juniper_cascor.log.1`). Read rotated segments; `2026-08-16_h2h_collect.py`
  and `2026-08-18_h2h_pair_compare.py` already do.
- Reading cap-bound cells: cap-bound, patience-exhausted and accuracy-target runs all report
  `early_stopped`; **`units == max_hidden_units` is the only disambiguator**.
- Screen wide-cap grids with `util/ad-hoc/2026-08-10_ea_aggregate_clean.py --suite <prefix> --expect <n>`
  (`oom == 0`), and verify both arms of a replicate resolve the **same content-addressed
  `dataset_id`**.
- Always `util/experiment_stack.bash --down <RUN_ID>`; a live run holds one port from each of the
  three 30-slot ranges plus its lockdirs.

### 7.1 Tooling inventory (all merged, on `main`)

**§3 (determinism):** `suites/p4/e-l-determinism-cap4.yaml` (cap-4 service control, single cell) ·
`2026-08-18_h2h_determinism_sweep.bash` (pair+budget shaped — see §3.4) ·
`2026-08-18_h2h_pair_compare.py` (first-divergent-iteration; in-flight guard; **drops runs 3..N**) ·
`2026-08-17_h2h_thread_probe.bash` (one CLI arm at a chosen budget) ·
`2026-08-17_h2h_fix_verify.bash` (one CLI arm against an arbitrary checkout) ·
`suites/perf/pf1-cascor-spiral-repeats.yaml` (the repeats precedent).

**§4 (wall gap):** `2026-08-16_h2h_phase_split.py` (**produced §4.1's split**) ·
`2026-08-16_h2h_collect.py` (both arms into one paired table) ·
`2026-08-16_h2h_preflight.py` (equalisation invariants before the compute — caught two design
errors) · `2026-08-16_h2h_marker_sentinel.bash` (rotation-proof span markers) ·
`2026-08-16_h2h_orchestrate.bash` (strict sequencing) · `2026-08-16_h2h_load_sampler.bash`
(contention) · `2026-08-16_h2h_cli_campaign.bash` / `_cli_arm.bash` / `_init_control.bash` ·
`2026-08-17_h2h_thread_campaign.bash` · `suites/p4/e-j-h2h-wide-cap{64,128}.yaml`,
`e-j-h2h-wide-cap64-init42.yaml`, `e-k-thread-probe-cap16.yaml`.

---

## 8. Deferred — not in scope, do not let them die silently

- **3-seed spread at cap 128** — the wide-budget campaign shipped n=2 there (traded for the init
  control). Its evidence note §8 records it NOT MEASURED.
- **cascor#530** seed field (§1.4).
- **Retrospective re-validation of the existing corpus.** Most of the E-A / E-I / P4 results are
  single-run, and the P3 acceptance rollup grades Reproducibility *"PASS — bit-identical"*; #532
  puts an undeclared ~10 pp on each. Re-validating that corpus is a **separate project** — raise it
  with the owner rather than absorbing it into §3 or §4.

---

## 9. Git state (re-derive; concurrent sessions push often)

- `juniper-ml` `origin/main` at **`9fd5b1a`** (ml#1160) when written; open PRs unrelated.
- `juniper-cascor` `origin/main` at **`9a7e7e0`** (cascor#533); open PRs dependabot only.
- Open issues owned by this arc: **cascor#530**, **cascor#532**. **cascor#531 is CLOSED** by #533.
- Authored from the session worktree `.claude/worktrees/cozy-dreaming-orbit` on branch
  `docs/handoff-determinism-and-residual`; working tree otherwise clean at hand-off time.
- **Both `origin/main` SHAs above move constantly** — two concurrent sessions pushed to each repo
  while this was being written. Always re-derive rather than trusting them.

## 10. Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main      # must be empty before committing
gh pr list --repo pcalnon/juniper-ml --state open
gh issue view 532 --repo pcalnon/juniper-cascor --json number,title,state,body
gh issue view 532 --repo pcalnon/juniper-cascor --json comments   # the corrections live HERE, not the body
# NB: the bare `gh issue view 532` and `--comments` forms both fail with a GraphQL projectCards
#     deprecation error on this gh build. Use --json.
python3 -m unittest tests/test_run_experiment.py              # 129 tests as of 9fd5b1a; count drifts
python3 -m unittest tests/test_experiment_suite_yamls.py      # every shipped suite still loads
util/reap_pytest_orphans.bash --dry-run                       # forkserver orphans outlive runs; reap before timing
nvidia-smi --query-gpu=memory.free,utilization.gpu --format=csv,noheader
```
