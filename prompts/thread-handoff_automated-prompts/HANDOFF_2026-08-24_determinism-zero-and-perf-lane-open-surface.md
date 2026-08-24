# HANDOFF 2026-08-24 — the CLI determinism gap reads ZERO, three fixes landed, and the perf lane is finally issue-tracked

Successor to
[`HANDOFF_2026-08-23_logging-pathology-fallout-and-perf-lane.md`](HANDOFF_2026-08-23_logging-pathology-fallout-and-perf-lane.md).

That handoff's **§2.1 row 1** (determinism-unchanged check) and all of **§3** (three unmerged fixes)
are **CLOSED**. **§2.1 row 2 — the post-fix worker profile — was never run and is still open; see
§4.10.** Its §4 work order is re-derived below, because closing §2.1 row 1 changed what is worth
doing next.

**The headline needs care.** On the current build the direct-CLI arm measures **0/190 diverging
pairs** where the pre-arc build measured **0.768** [0.553, 0.847]. That is one campaign, on a build
carrying four merged changes, and **attribution is NOT established**. Read §1.1 before repeating the
claim anywhere.

Throughout, "§N" means a section of **this** document. Commands run from the juniper-ml repo root.

---

## 1. What is settled — do not re-measure

| finding | evidence | status |
| --- | --- | --- |
| Post-arc determinism: **CLI 0/190** (was 0.768), on **both** fingerprints | §1.1 | **MEASURED — the result stands; its ATTRIBUTION is open across 24 commits (§4.1). Do not re-measure the *current* build; §4.1 may deliberately measure an EARLIER one.** |
| Service arm 0/190 | §1.1 | **RE-CONFIRMED** — the service was already 0/190 at N=20 pre-arc; only the CLI arm moved |
| Timing noise floor (deferred since 2026-08-16) | §1.2 | **MEASURED** |
| Candidate seeds no longer read the process-global `random` stream | cascor#566 | **FIXED** |
| The installed candidate's identity is recoverable from a stock log | cascor#564 | **FIXED** |
| Forked candidate workers can be profiled at all | cascor#567 | **SHIPPED** |
| Root cause of the *rate* term: `inspect.getmodule` per log record | cascor#563 | **FIXED** (previous arc) |
| Wall-gap decomposition `work × rate` reproduces the phase ratio to 0.002 | ml#1278 (a PR) | MERGED |

### 1.1 The determinism result, stated honestly

Campaign: `util/ad-hoc/2026-08-20_determinism_campaign.bash`, **N=20 per arm**, cap 4, strictly
sequential, both arms at **cascor `234c203`** (which **includes** #566 — this is the *after* side),
host `nproc=16`.

**Not a quiet host, contrary to an earlier draft.** `cli_load.jsonl` records load1 **8.44–10.43**
throughout the CLI arm (the pre-arc campaign, never described as quiet, ran at 5.24–9.66). There is
**no load record at all for the service arm** — the campaign samples `/proc/loadavg` only inside the
CLI loop. This does not touch the within-arm determinism zeros; it does bear on §1.2.

```text
CLI arm      ~/.local/state/juniper-experiments/determinism-n20-postarc
service arm  ~/.local/state/juniper-experiments/suites/e-l-determinism-cap4-20260824T003754Z
```

**The suite dir is a SIBLING of the output root, not a child** — `determinism-n20-postarc/suites/`
does not exist. §8 has the working re-derive command.

| arm | trace fingerprint | correlation fingerprint | distinct outcomes |
| --- | --- | --- | --- |
| **service** | 0/190 = 0.000 | 0/190 = 0.000 | 1 of 20 |
| **direct CLI** | 0/190 = 0.000 | 0/190 = 0.000 | 1 of 20 |

**Why this is not a vacuous zero** — checked, because this arc shipped a vacuous check once:

- 20/20 runs usable in both arms; `excluded_no_trace=[]`, `excluded_in_flight=[]`.
- **The load-bearing check:** the correlation fingerprint extracted **`rounds=[4], values/run=[32]`**
  in *both* arms, and those 32 values are non-degenerate and arm-distinct (CLI spans
  0.009213–0.105662, service 0.032598–0.121684). It is comparing 32 real values per run over 190
  pairs, not an empty set.
- The two arms carry **different** fingerprints (`f939751d1347` CLI vs `d52981ffdaf5` service), so
  the CLI arm did not silently run the service path.

Two things that are **not** evidence, contrary to an earlier draft of this document:

- **The exit code does not guard the correlation marker.** The analyser's stale-anchor `exit 2`
  covers only `span_s` / `cand_total_s` / `cand_epochs`, plus the global "no usable runs" path. A
  dead `RE_CORR` still prints `0/190 = 0.000` and exits 0 — betrayed only by `values/run=[0]`.
  Verified by monkeypatching each marker dead in turn. The correlation zero rests on the
  `values/run=[32]` check above, **not** on the exit code.
- **`length_mismatch_pairs=0` is entailed by the zero**, not independent: the counter only
  increments inside the `fps[i] != fps[j]` branch.

**What is NOT established: which change closed it — and the surface is far wider than it looks.**
The pre-arc comparator ran at `4bec1be` (#539) and this campaign at `234c203`: **24 commits apart**,
not four. Among them is **#556, `feat(cli): W-11 full parity — the direct CLI now honours the keys it
was dropping`** — a change to the exact code path under comparison, and on its face at least as
plausible a cause as #566 — plus #562 and #565. One campaign cannot attribute across 24 commits.
**Do not write "F1 closed the determinism gap" anywhere.**

**Hypothesis worth testing (§4.1), not asserting.** The predecessor's mechanism ("the two entry
points run `fit()` on different threads") and the seed defect may be *the same mechanism*. The old
code drew candidate seeds from the process-global `random` stream; if thread context varied how much
of that stream was consumed before `_generate_candidate_tasks`, candidate seeds would vary run to
run on the CLI path — producing exactly the observed nondeterminism. That would also explain why the
thread-context mitigation only reached 0.768 → 0.337 (it reduced the variability) while cascor#566
severs the coupling outright (0.000).

### 1.2 Timing noise floor — measured, publishable

Deliberately unpublished before now because every earlier opportunity was contended. Same campaign,
quiet host:

| arm | training span | candidate phase | output phase | candidate epochs | s / candidate epoch |
| --- | --- | --- | --- | --- | --- |
| CLI | 15.4 ± 0.5 s (cv **3.3%**) | 11.0 ± 0.7 s (cv 6.6%) | 3.9 ± 0.3 s | 11,310 ± 0 | 0.00097 ± 0.00006 |
| service | 17.4 ± 0.9 s (cv **5.1%**) | 12.7 ± 1.0 s (cv 7.8%) | 3.9 ± 0.3 s | 13,140 ± 0 | 0.00096 ± 0.00008 |

**Read these as an UPPER BOUND, not a noise floor.** Three caveats, all verified:

1. **1-second resolution.** Log timestamps carry no sub-second field, so every figure above is an
   integer count of seconds. The CLI span takes exactly **two** values (15 s ×12, 16 s ×8) and its
   reported sd of 0.5026246899500346 equals `sqrt(20/19 × 0.4 × 0.6)` to 16 digits — i.e. it is
   precisely the quantisation of a near-constant span. **The CLI's "cv 3.3%" measures the clock, not
   the host.** The service arm (5 distinct values, 16–20 s) does carry real dispersion. Sizing a
   cap-4 CLI comparison needs sub-second timestamps that this instrument does not emit.
2. **The arms ran as blocks, not interleaved** (service 00:37–00:50Z, then CLI 00:50–00:58Z) —
   contradicting §5.4, which this arc wrote for good reason. The hazard is live in this harness: the
   pre-arc service block drifted 3–4× within itself (first four runs 665–825 s, remaining sixteen
   190–250 s). **The cross-arm span delta (15.4 vs 17.4 s) is therefore not load-controlled.** Only
   the within-arm dispersions are.
3. **Detectability ≠ cv.** At n=20 the cross-arm span difference resolves to ≈0.6 s (≈4% of the CLI
   span) at 80% power — but per caveat 1 the underlying sd is a quantisation artefact anyway.

### 1.3 NEW, and unexplained: the two arms still disagree with each other

cascor#566 made the seed *derivation* identical on both paths. The arms nonetheless produce
**different results**: **11,310 vs 13,140 candidate epochs**, train **0.6075 vs 0.6462**. Each arm is
now internally reproducible; they are not reproducible *against each other*.

> **Do NOT quote a val delta.** An earlier draft cited "val 0.5550 vs 0.5700". The two numbers are
> not the same quantity: **the CLI arm runs with no validation split at all** — every in-loop record
> reads `validate_training: Iteration N (no val data)` — so its 0.5550 is a *post-fit test-set*
> accuracy from `SpiralProblem.evaluate`, while the service's 0.5700 is an *in-loop validation*
> accuracy that also feeds patience and early stopping. The analyser's own docstring carries a
> "CROSS-ARM ACCURACY CAVEAT" forbidding exactly this comparison. `train` and `candidate epochs`
> survive; `val` does not.

So "the two entry points train different candidates on identical configuration" is **still true**,
just no longer because of seed derivation. The remaining cause is untraced — most likely dataset
provenance (the CLI arm builds data via `SpiralProblem`, the service fetches from juniper-data), but
that is a guess and is written here as one. Tracked as §4.2.

### 1.4 Numbers that were CORRECTED in earlier arcs — do not resurrect

| superseded claim | replicated value |
| --- | --- |
| "the `OMP=2` cap costs **1.30×**" (cascor#531) | **1.016×** [0.885, 1.148] at k=3 — no effect |
| "the residual is **~1.17×**" (cap 16) | **1.706×** at k=4 |
| "#533 removed 1.30× of the gap" | cap-64 1.924 ± 0.486 vs pre-#533 1.99 ± 0.21 — overlapping |

### 1.4a Numbers that are BUILD-SPECIFIC, not wrong — do NOT discard

| claim | standing |
| --- | --- |
| "CLI diverges on **0.768** of seeded pairs" [0.553, 0.847] | **Correct, on the PRE-ARC build.** Current build reads 0.000 (§1.1). This is a baseline, not a dead attribution: **§4.1 needs it to attribute** and **§3.2 preserves its 1.1 GB of evidence for exactly that**. Do not delete either. |
| "the *work* term is **1.308**" (predecessor) / "**1.230**" (perf-lane register G2 row) | Both pre-arc. §1.2 re-measures it as **1.162×** at cap 4 (13,140 / 11,310 candidate epochs). **Three unreconciled values for one quantity — see §4.11.** |

### 1.5 Every published cap-series ratio is PRE-F1 and historical

The span series (1.459 / 1.735 / 1.924 at caps 4/16/64) predates cascor#563. Post-F1 at cap 16, k=4:
rate ratio **1.065** [0.869, 1.262]; span ratio **1.817** and now dominated by fixed overhead, not
throughput (§4.4). **Do not quote the pre-F1 series as current.**

### 1.6 Eliminated at runtime — do NOT re-check

Each was a live hypothesis, tested and killed. Cheap to re-propose, expensive to re-test.

| eliminated | evidence |
| --- | --- |
| **Thread context is not the wall mechanism** — moving `fit()` to a pool thread changed span by 0.7% (280.8 → 282.9 s) against a service arm at 192.5 s | residual note §4.1 |
| **Pool packing is not it** — LPT imbalance ratio **1.012×**; both arms pack equally badly | residual note §4.3 |
| **The pool is created ONCE** for 16 rounds, not re-forked per iteration | residual note §4.4a |
| **cProfile is the wrong instrument for timing** — it *destroys* the effect (9.2 ms/epoch gap reads 1.9 ms; per-call 0.944). Use `py-spy --native` | residual note §4.3b |
| **BLAS thread count is not the driver** — `threads=1` does not fix determinism; `OMP=2` costs 1.016×. Revived once from 8 runs split 4/4, and died again | reproducibility note §3.8 |
| **The arrival-order tie-break ("near-tie") is not the mechanism** — `_process_training_results` stable-sorts an arrival-ordered list and the pool completed in a different order on 28/28 pairs, yet **0** divergences localised to selection-given-equal-correlations. This is the first thing anyone proposes for §4.2 and §4.11; it is dead | reproducibility note §3.2 |

### 1.7 The documents this handoff is shorthand for

| shorthand | path (all in juniper-ml `notes/`) |
| --- | --- |
| "reproducibility note" | `JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md` |
| "residual note" | `JUNIPER_2026-08-21_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-RESIDUAL-WALL-GAP-EVIDENCE.md` |
| "fix design" (F1/F2/F3) | `JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md` |
| "perf-lane register" (G1–G5) | `JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md` |
| "the §12 perf lane" | `JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` §12 |
| "the P3 rollup" | `JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md` |

**Repos**: `main.py`, `cascade_correlation.py`, `candidate_unit.py`, `logger.py`, `constants*.py` are
**juniper-cascor** (`src/…`). `run_experiment.py`, `experiment_stack.bash`, `util/ad-hoc/*` and all
`notes/` are **juniper-ml**.

### 1.8 Terms — define these before reading §4

- **Arm** — one entry point under test: the **direct CLI** (`python main.py`, trains in-process) or
  the **service** (the juniper-cascor REST tier, driven by `run_experiment.py`).
- **cap-N** — the candidate-round cap set in the suite YAML. cap 4 ⇒ 4 rounds × 8 candidates = 32
  candidates, which is why §1.1's correlation fingerprint reads `rounds=[4], values/run=[32]`.
- **Trace fingerprint** — derived from the per-iteration `grow_network` log line. **Blind to the
  final candidate round, which emits no such line.**
- **Correlation fingerprint** — the per-round candidate correlations; sees every round. **Carry
  both** (§5.3): trace-only rates read 0.632 where correlations read 0.768.
- **The decomposition: `span = work × rate`.**
  - ***rate*** — seconds per candidate epoch. Closed by #563 (1.065, interval includes 1.0).
  - ***work*** — candidate epochs actually executed. Register G1/G1a: **1.230**; predecessor:
    **1.308**; §1.2 re-measures **1.162** at cap 4. **Still open — §4.11.**
  - ***span*** — total training wall-clock (1.817), now dominated by fixed overhead, not throughput
    (§4.4).

---

## 2. Merged / filed this arc

| item | what |
| --- | --- |
| **cascor#564** | `CandidateUnit.__repr__` — the installed candidate is named in stock logs (perf-lane G1b) |
| **cascor#566** | Candidate seeds from a network-owned `random.Random(random_seed)`. **Deliberate golden baseline reset** — see §3.1 |
| **cascor#567** | `JUNIPER_CASCOR_WORKER_PROFILE` — opt-in per-worker cProfile for the forked pool |
| **cascor#568–573** | The perf-lane open surface, finally issue-tracked (F2, F3, forkserver isolation, G4, latent seeding defect, logging redesign) |
| **cascor#532** | Updated with what shipped and what remains |

All three PRs verified green on `main` per-commit on the **required** contexts (anchored per §3.6),
including `Test (Python 3.12)`, `Post-Merge Main Verification`, `Golden Regression (WS-6 Gate)` and
`Conformance (WS-6 Gate)`. cascor#564's `Test (Python 3.12)` **did** fail first — the §3.4 mirror
miss — and was fixed inside that same PR and re-verified before merge.

Those are **workflow** names. The *required status contexts* they emit are named differently —
`Symbol & Docs Screen`, `Golden / Snapshot Regression`, `model-core Conformance` — so grepping a
check-runs list for the workflow name finds nothing. Anchor on the required contexts
(`util/wait_for_checks.py --anchor required` does this for you).

**Verify before trusting this table** — concurrent sessions merge often:
`gh pr view 566 --repo pcalnon/juniper-cascor --json state,mergedAt`.

---

## 3. Hazards this arc created or confirmed — read before touching anything

### 3.1 The seed-42 golden baseline was deliberately reset (cascor#566)

Candidate seeds moved on **every** path, not just the CLI. The reason is not obvious:
`_seed_random_generator` seeds numpy/torch but draws its **roll count from the stdlib global
stream**, three times during construction, so the old seeds came from an arbitrary (if
deterministic) offset into it.

Consequences, all live:

- `golden_trajectory_seed42.json`, `golden_predict_seed42.json` and 3 API snapshots were regenerated
  with `GOLDEN_CAPTURE=1`. Network **architecture is unchanged** (still 2 hidden units, same shapes);
  only learned values moved.
- **Every pre-#566 experimental baseline is incomparable.** Any comparison spanning 2026-08-23 must
  say so.
- The remaining instance of that defect (numpy's stream position not being a function of the seed)
  is **cascor#572**, and fixing it will move numbers **again** — batch it with any other seeding
  change rather than taking a third discontinuity.

### 3.2 Do NOT overwrite the pre-F1 determinism evidence

`util/ad-hoc/2026-08-20_determinism_campaign.bash` defaults `OUT_ROOT` to
`~/.local/state/juniper-experiments/determinism-n20` — which holds **1.1 GB of PRE-F1 evidence**
(`cascor_sha 4bec1be`, genuinely pre-#563) that the before/after comparison needs. **Always pass an
explicit third argument.** The post-arc run used `determinism-n20-postarc`.

Re-using an existing `OUT_ROOT` does **not** cleanly overwrite it, which is worse than loss:
`provenance.json` is **truncated** (destroying the SHA that makes the old data interpretable) while
`cli_arm.log` and `cli_load.jsonl` are **appended**, and the per-run trainer logs reuse the same
`cli-NN/logs/`. The analyser merges rotated log siblings oldest-first, so it will parse **two builds
as one run** and emit a plausible, wrong fingerprint on the arc's headline question.

**A campaign's SERVICE arm does NOT live in its `OUT_ROOT`.** `registry.jsonl` points at top-level
`~/.local/state/juniper-experiments/<TIMESTAMP>-<hash>/` run dirs; the `OUT_ROOT` holds the **CLI arm
only**. So a name-based allowlist that keeps only the campaign directories silently deletes half of
every campaign, including the data behind §1.1.

Never sweep `~/.local/state/juniper-experiments/` (**46 GB**) by name. Preserve, non-negotiably:

- **`suites/` in full** and `index.jsonl`;
- **every top-level `<TIMESTAMP>-<hash>` run dir referenced by a `suites/*/registry.jsonl`** —
  resolve `run_dir` out of the registries first, do not guess from names;
- the CLI-arm roots: `determinism-n20`, `determinism-n20-postarc`,
  `h2h-paired-e-k-thread-probe-cap16`, `h2h-paired-e-m-h2h-paired-cap64`, `h2h-thread-sweep`,
  `f1-paired-cap16`, `profile-cap4`, `pyspy-out`.

### 3.3 The orphan reaper will kill a live campaign

`util/reap_pytest_orphans.bash` treats reparenting to `systemd --user` as the orphan predicate, and
a campaign's nohup'd **services** land there. **Do not run it non-dry while a campaign is in
flight.** Two protection keys, either sufficient (`reap_pytest_orphans.bash:80-83`): **P1** the pid
appears in a run-dir `*.pid`; **P2** the pid's cmdline references a run root.

Precision, because the previous handoff overstated this: the candidate filter (`:161`) requires
`/python/`, so the campaign's **bash** driver is never a reap candidate — the exposure is the python
services, and P1/P2 are what protect them. Protection also covers `${TMPDIR:-/tmp}/juniper-e2e`;
those pidfiles are all that keep another session's E2E stack alive, and they live in `/tmp`, so
anything that clears `/tmp` removes the protection.

Related, and undocumented until now: `2026-08-17_h2h_thread_probe.bash:77` runs
`pkill -f "main.py --config ${CONFIG}"`, and the campaign resolves its cell from *the newest suite
dir matching `e-l-determinism-cap4-*`*. **Two concurrent campaigns will resolve the same `CONFIG`
and each will kill the other's trainer.** Never run two determinism campaigns at once.

A campaign must be launched with `setsid nohup`, **not** as a harness background task — those carry
a ~3600s lease that would kill it mid-run and strand a stack holding ports.

### 3.4 `juniper-cascor-model` is a byte-identical extraction — mirror or CI fails

`juniper-cascor-model/` holds verbatim copies of `candidate_unit`, `utils`, `log_config`,
`cascor_constants` from `src/`, drift-guarded byte-for-byte by
`juniper-cascor-model/tests/test_drift.py`. **Any `src/` edit under those four trees must be mirrored
in the same commit** (`cp src/<rel> juniper-cascor-model/<rel>`), or `Test (Python 3.12)` goes red.
Only `log_config/logger/logger.py` is allowlisted. Caught live on cascor#564.

`cascade_correlation.py` is **not** in the extracted set and needs no mirror.

### 3.5 Extract-method trips Sequence Safety — waive in ONE commit

An extract-method refactor fails the symbol screen as `WEAKENED` even though nothing is deleted
(cascor#567: `ratio 0.38`). Reproduce and prove the waiver **locally** before spending a CI run:

```bash
juniper-symbol-loss-check --scope 'src/**/*.py' --base origin/main --head HEAD   # cascor's exact scope
# want: [WAIVED/WAIVED] ... {'waived_by': 'Allow-Symbol-Loss trailer'}
```

Trailer form for a method is `Allow-Symbol-Loss: method:<Class>.<name>`. It **must live in the
single/first commit** — a waiver in a follow-up commit passes the PR screen and then turns
`Post-Merge Main Verification` red on `main` after the squash. Verified on cascor#567 that the
trailer survived the squash and main-verify came back success.

### 3.6 Quality Gate can read SUCCESS while a required job fails

Observed again on cascor#564: `Test (Python 3.12)` FAILURE alongside `Quality Gate` SUCCESS. Anchor
on the **required contexts**, never the aggregate rollup:
`python3 util/wait_for_checks.py --pr N --repo juniper-cascor --anchor required`.

### 3.7 A PR that goes BEHIND needs the server-side update-branch

`gh api repos/pcalnon/juniper-cascor/pulls/<n>/update-branch -X PUT`. A local merge + push is
**unsigned**, and `required_signatures` rejects it. Needed twice this session (#566, #567) because
concurrent sessions merge frequently.

---

## 4. OPEN WORK — ordered

**Work it in this sequence.** The ordering changed because §2.1 closed.

| # | item | why here | gate |
| --- | --- | --- | --- |
| 1 | **§4.1 attribute the determinism closure** | the arc's biggest claim is currently unattributed | none |
| 2 | **§4.10 post-F1 worker profile** | never run; without it the 9× is also unattributed | none |
| 3 | **§4.11 G1a and the *work* term** | three unreconciled values; the last open tracker for *work* | none |
| 4 | **§4.2 cross-arm disagreement** | newly isolated, and it is what "CLI vs service" now means | none |
| 5 | **§4.12 the §12 baseline decision (FILE AN ISSUE)** | the only open-surface item with no tracker | none |
| 6 | **§4.3 write the evidence note + update the register** | the §1.1/§1.2 numbers exist ONLY in this document | none |
| 7 | **§4.5 forkserver isolation (cascor#570)** | **gates cascor#568 AND cascor#569** | none |
| 8 | **§4.6 F3 preload (cascor#569)** | its ~12.8 s estimate is unsound until §4.5 resolves | fork-safety audit |
| 9 | **§4.7 F2 import hygiene (cascor#568)** | may be moot if §4.5's leak is closed | after §4.5 |
| 10 | **§4.4 G4 fixed overhead (cascor#571)** | now the dominant cost; needs an instrument built first | none |
| 11 | §4.8 deferred items (bullets 1–4) | independent | — |
| 12 | **§4.9 the thread-context mitigation** | recommend DROP; settle it once §4.1 lands | after §4.1 |
| — | **§4.8 bullet 5 — retrospective corpus re-validation** | **owner decides** — raise, do not absorb | owner |
| — | **§4.13 logging redesign (cascor#573)** | owner-raised, its own design doc | **owner decides timing** |

**§4.5 gates §4.6 AND §4.7, and that is not obvious from reading those sections in order.** §4.6's
"~12.8 s per pool creation" assumes workers inherit the forkserver's table — §4.5 measured that they
do **not**. If §4.5's leak is closed, §4.6 must be re-sized and §4.7 may be moot. **Do not start
either before §4.5.** (The predecessor carried this same warning for the same reason: a reader who
jumps straight to a §4.x section never sees the table.)

### 4.1 Attribute the determinism closure — do this first

The claim "the CLI seeded-run gap is closed" currently rests on one campaign over a **24-commit**
span (`4bec1be`..`234c203`), not the four merges this arc happens to remember.

**Start by narrowing the surface, not by re-running.** The strongest rival to #566 is **#556**
(`feat(cli): W-11 full parity — the direct CLI now honours the keys it was dropping`), which changed
the direct-CLI configuration path itself; #562 and #565 are also in range. Read those three diffs
before designing any experiment — the answer may be obvious from the code.

Then, cheapest decisive test, in order:

1. **Instrument rather than re-run.** cascor#566 makes round-*k* seeds a function of
   `(random_seed, k)`. On the **pre-#566** build, log `candidate_seeds` across N CLI runs and check
   whether they varied run to run. If they did, the mechanism in §1.1 is confirmed and no second
   campaign is needed. The instrumentation already exists — the `util/ad-hoc/*_diag.patch` files and
   the `rescue/*` branches in §6.1.

   > **Pre-#566 base: cascor `362b88b1`.** Three worktrees under `Juniper/worktrees/` are already
   > pinned to it (e.g. `juniper-cascor--exp--residual-wall-gap--20260821-0800--362b88b1`). Confirm
   > with `git -C juniper-cascor merge-base --is-ancestor 4a07b49 362b88b` returning **non-zero**.
   > **Do NOT use `exp--determinism-postarc`** — its `234c203` *includes* #566 (merged 19:14, campaign
   > 19:27), so it is the *after* side and seeds there are deterministic by construction.
2. If instrumenting is impractical, re-run the campaign against a reverted build — but **read this
   first, or the result will be confidently wrong**:

   > **The campaign's same-SHA pre-flight reads `git rev-parse HEAD`, which cannot see a working-tree
   > revert.** A `git revert` left uncommitted passes the guard *vacuously* while the CLI arm runs
   > reverted code and the service arm does not — precisely the "cross-arm comparison at two
   > checkouts" failure the script's header says it exists to prevent.

   Do it properly: create a **new** worktree on a **branch** at the pre-#566 commit, revert there,
   and check the **same** commit out for the service arm (`$JUNIPER_EXP_PROJECT_DIR/juniper-cascor`)
   after confirming no other session is using that checkout. Never revert inside
   `exp--determinism-postarc` — it is detached (a commit there is the loss class this arc already
   produced once) and it is the provenance record for §1.1. Budget ~35 minutes of quiet host per arm
   at cap 4.

   **The goldens will fail on a reverted build. That is expected and correct — leave them failing.**
   Every golden failure message tells you to run `GOLDEN_CAPTURE=1`; doing so here rewrites
   `src/tests/fixtures/golden/*` **and** `two_spiral_seed42.npz` in place, with no prompt, no backup
   and no diff, silently re-baselining the suite onto a pre-#566 build. Capture is legitimate *only*
   inside a PR that deliberately moves the baseline, with `git diff` on the golden files reviewed.

**Do not use a small screen.** An n=6 screen read **0/15** where N=20 read **0.337** on this exact
question. Anything below N≈20 cannot answer it.

**Then update cascor#532** with the attribution, and close it if the mechanism is confirmed.

### 4.2 Why do the two arms still disagree? (§1.3)

Each arm is internally reproducible; they produce different results from each other (11,310 vs
13,140 candidate epochs).

**Two concrete leads, both cheap:**

1. **The arms already differ at iteration 0** — before any candidate round runs (CLI loss 0.239217 /
   acc 0.5787; service 0.240292 / 0.6088). Whatever differs is present *at construction*, not
   accumulated during training. That alone rules out most candidate-side explanations.
2. **Only the service carves a validation split.** Both arms hold 800 training samples
   (`manager.py: _reload_dataset: Reloaded dataset 'spirals' (800 train samples)`; CLI
   `x_full: torch.Size([1000, 2])` → 800/200), but the CLI trains with **no val data** (§1.3), so
   patience and early stopping see different signals on the two paths. That is sufficient on its own
   to produce different candidate-epoch totals.

Suggested probe: hash the training tensors on both paths before the first candidate round. If they
differ, everything downstream follows and no further search is needed; if they match, lead 2 is the
answer.

This matters beyond curiosity: **a P3 threshold calibrated on one tier and applied to the other is
still wrong**, and §12 of the perf lane contemplates `python main.py --profile` while
`run_experiment.py` drives training entirely through the service REST API. Either the lane measures
one tier, or it keeps two baselines. This has still not reached the §12 design.

### 4.3 Write the evidence note — §1.1 and §1.2 exist only here

Nothing in `notes/` yet records the post-arc campaign. Write
`notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-POST-ARC-DETERMINISM-EVIDENCE.md`
carrying: the §1.1 table, the non-vacuity checks, the explicit non-attribution, the §1.2 noise floor,
and the §1.3 cross-arm finding. Then update the **perf-lane register**: G1b is shipped (cascor#564);
**G1a — do NOT mark it moot without doing §4.11 first**, because the register's G2 row ties the
*work* term to G1/G1a and annotating it away extinguishes the last open tracker for that term; G4 is
cascor#571; G5 is cascor#568/#569; **cascor#570 has no G-id — give it one.**

Raw data: `~/.local/state/juniper-experiments/determinism-n20-postarc/` (`nrun_report.json`,
`provenance.json`, `campaign.log`, `cli-01..20/`) and suite dir
`.../suites/e-l-determinism-cap4-20260824T003754Z/`.

### 4.4 G4 — per-run fixed overhead is the dominant cost (cascor#571)

Before #563 the candidate phase was **98%** of a service cap-16 span (890 s of 908 s); after, it is
**66%** (41 s of 62 s). Those are **single-pair** values from the fix design's per-pair table, not
campaign means — the k=4 means are service **827 s → 89 s**. Quote them as an illustration, not as
the campaign figure. Either way the conclusion holds: startup, dataset fetch, output passes and
teardown now set the wall, and the span ratio (1.817) measures *those*, not throughput.

**No instrument exists.** `util/ad-hoc/2026-08-16_h2h_phase_split.py` splits candidate vs output
only. **Build the decomposition first, measure second.** Anchor every boundary on log **message
text**, never `file.py: func:LINE`.

### 4.5 Forkserver isolation is not delivered (cascor#570) — gates #568 and #569

Workers measure **1,871** (CLI) / **1,410** (service) modules — within a handful of their
*launchers* (1,867 / 1,416), far above a clean forkserver table (1,091 preload, 1,333 with the
trainer). The route by which the launcher's import graph reaches the workers is **untraced**. Worth
checking specifically whether the forkserver is started *after* the launcher has already imported its
full graph — which would explain the numbers exactly and make the fix structural (start it early)
rather than about the preload list.

Forkserver architecture *is* in use: the start method is set in
`cascor_constants/constants_model/constants_model.py` (`_PROJECT_MODEL_CANDIDATE_TRAINING_CONTEXT =
"forkserver"`), and the persistent pool creates each worker with `self._mp_ctx.Process` in
`cascade_correlation.py`. Seven processes, both arms. **Anchor on those symbol names, not on line
numbers** (§5.5).

cascor#567's `JUNIPER_CASCOR_WORKER_PROFILE` is the way to instrument inside a forked worker — but
use it for **attribution, not timing** (§1.6).

### 4.6 F3 — forkserver preload set (cascor#569), BLOCKED

Current preload set:

```python
["os", "uuid", "torch", "numpy", "random", "logging", "datetime"]
```

| entry | +modules | import | verdict |
| --- | ---: | ---: | --- |
| `torch` | 886 | 2.938 s | keep |
| `numpy` | 109 | 0.153 s | keep |
| `os` | **0** | 0.000 s | pure no-op — already imported before the list is read |
| `uuid`/`random`/`logging`/`datetime` | 19 total | 0.021 s | harmless |
| **missing `cascade_correlation`** | **242** | **1.822 s** | the candidate — **~12.8 s per pool creation** (7 workers) |

Preloading runs import-time side effects **inside the forkserver**, inherited by every worker across
the fork — the classic fork-safety hazard, and `cascade_correlation` has a large import graph.
**The audit is not done and F3 must not land before it is.** The ~12.8 s figure is unsound until
§4.5 resolves (it assumes workers inherit the forkserver's table; §4.5 measured that they do not).

Also in scope: `cascade_correlation.py` still carries a commented-out `mp.get_context("forkserver")`
above a garbled note reading *"…did not corrUse 'fork' context for better compatibility with
BaseManager on Linux"*. The code uses forkserver; the comment says otherwise. Anchor on the text —
the line number has drifted twice.

### 4.7 F2 — CLI import hygiene (cascor#568), demoted

**GATED on §4.5 — may be moot if the leak is closed. Do not start the import trace first.**

`import main` pulls **1,867** modules including **fastapi and pydantic**; `import api.app` pulls
1,416. #563 removed the performance motivation. Remaining value: import time, worker memory, and not
shipping a web stack in a trainer. **The import edge is still not traced** — that is F2's first task:
`python -X importtime`, **or** bisect `sys.modules` against a deliberately trimmed import.
`-X importtime` alone will not find the edge if it is a transitive re-export.

### 4.8 Deferred — do not let these die silently

- **Re-measure the cap series post-F1** — everything published is pre-F1 (§1.5). Now cheap (~9×
  shorter runs). Instruments, all on `main`: `util/ad-hoc/2026-08-21_h2h_paired_campaign.bash`
  (interleaved, SHA + `config_sha256` guards) + `2026-08-21_h2h_paired_ratio.py` (ratio-of-pairs +
  required-k); sweep roll-up `2026-08-22_h2h_sweep_ratios.py`.
- **3-seed spread at cap 128** — still NOT MEASURED. As a task: copy
  `e-m-h2h-paired-cap64.yaml` to a cap-128 variant, 3 seeds × 2 arms via
  `2026-08-21_h2h_paired_campaign.bash`, analyse with `_paired_ratio.py`. **Cost gate first**: a
  cap-64 CLI leg wrote a 637 MB trainer log (§6), so cap 128 may be log-bound rather than
  wall-bound. Extrapolate from §1.2 before committing the host; if the budget does not clear, say so
  and park it explicitly rather than carrying it to a fourth handoff unchanged.
- **cascor#530** — `TrainingParams` has no seed field; the service network seed is unconditionally
  42. Follow-on: `_CANDIDATE_UNIT_RANDOM_SEED` must reach the candidate pool too.
- **cascor#572** — the latent seeding defect (§3.1). Batch with other seeding work.
- **Retrospective corpus re-validation** — most E-A/E-I/P4 results are single-run and the P3 rollup
  grades Reproducibility "PASS — bit-identical". With #566 having moved every number, this is now
  more pressing. **Raise with the owner; do not absorb it.**

### 4.9 The thread-context mitigation — probably DROP it

`util/ad-hoc/2026-08-20_cascor_thread_context_diag.patch` on juniper-ml `main` is **the artifact of
record** — no branch or worktree is needed to keep this decision open. (The rescue branch
`rescue/candidate-seed-derivation-wip` held the *seed fix* WIP, not this; see §6.1.)

It cut the CLI divergence 0.768 → 0.337 on the **pre-arc** build. On the current build the CLI arm
measures **0.000 without it**.

It is therefore a mitigation for a symptom that no longer reproduces, and it was always
symptom-shaped (an executor bolted into `main.py`). **Recommendation: do not merge.** Close it out
once §4.1 confirms the mechanism; if §4.1 shows the closure came from something other than #566,
reopen the question.

### 4.10 Post-F1 worker profile — NEVER RUN (predecessor §2.1, row 2)

The fix design's verification plan has four rows. Two ran (the paired campaign and the per-epoch
ratio), one ran this arc (§1.1's determinism check). **This one has still never run:** `inspect`
frames should fall from **~78% of candidate-worker self time to negligible** after #563.

Until it does, *"#563 caused the 9×"* is an unattributed correlation — the same error §1.1 refuses to
make about determinism, made silently about performance.

Tooling, all on `main`: `util/ad-hoc/2026-08-23_pyspy_conda_shim.bash` +
`_h2h_native_profile_diff.py`; worker-level `_h2h_worker_profile_diff.py`, now drivable through
cascor#567's `JUNIPER_CASCOR_WORKER_PROFILE`. Remember `py-spy --native` must be an **ancestor**
(`ptrace_scope=1`) and cannot be combined with `--nonblocking`; and use cProfile for attribution,
never for timing (§1.6). **File an issue** — it is not covered by cascor#568–573.

### 4.11 G1a and the *work* term — still open, and now re-measured by accident

The perf-lane register's G2 row states: *"the **work** term (1.230) is G1/G1a and untouched."* The
predecessor put it at **1.308**. §1.2 measures it again without saying so: 13,140 (service) vs 11,310
(CLI) candidate epochs = **1.162×** at cap 4.

**Three values for one quantity, none reconciled.** Do that before annotating the register, and say
which build each belongs to.

G1a's own residual (0.337) is plausibly moot — it was a property of the *mitigated pre-arc* build,
and the current *unmitigated* CLI reads 0.000. **Say that explicitly when closing it rather than
letting it lapse.** Resume-from data if §4.1 reopens the question: the 20 runs split **16 / 4** —
group A val 0.6350 / 10,960 candidate epochs, group B val 0.6400 / 10,950 — 1 distinct trace outcome,
2 distinct correlation outcomes (reproducibility note §4.4), worth **0.5 pp** of validation accuracy.
The register notes G1a "blocks a CLI-side reproducible claim", so closing it has a P3-gate
consequence.

### 4.12 The lane still has no baseline decision — FILE AN ISSUE

`run_experiment.py` drives training **entirely through the service REST API** and never invokes
`main.py`, while §12 of the perf lane contemplates `python main.py --profile`. §1.2 now shows the two
tiers differ in fixed overhead **and** in work (11,310 vs 13,140 candidate epochs), so a P3 threshold
calibrated on one tier and applied to the other is wrong.

**Decide: one tier, or two maintained baselines.** This has never reached the §12 design, and it is
the **only** item on the open surface with no tracker — cascor#568–573 cover the other six. File it.

### 4.13 TABLED — logging redesign (cascor#573, owner-raised)

**The owner decides timing. Do not start without them.** Scope as raised: a clean stream to
stdout/stderr; richer sinks (formatted, colourised file output); **per-logger** levels settable via
config file *and* environment variable; possibly streaming to an ELK/Kibana backend.

Deliberately **not** folded into #563: F1 was a hot-path bug fix any redesign would have to make
anyway, and equally the redesign must not be justified by F1's number, since F1 already banks it.

Carry into the design: `logger.py` `_log_at_level` **`open()`s the log file per record** — the same
class of per-record cost #563 removed, and it should not survive a redesign — and it `print()`s to
stdout unconditionally (which is why pytest summaries vanish locally, §6). Full framing: fix design
§8.

---

## 5. Methodology this arc earned — apply it

1. **No small sample supports a mechanism claim.** Three published attributions died under
   replication (§1.4), plus two of this arc's own predictions — the near-tie hypothesis and the
   thread-count hypothesis, the latter revived once from 8 runs split 4/4 (§1.6).
2. **An n=6 screen can read as a clean zero.** The thread-context mitigation showed 0/15 at n=6 and
   0.337 at N=20.
3. **Carry two fingerprints.** A cap-4 run trains 32 candidates but logs 3 iterations; its final
   candidate round is invisible to the trace. Trace-only rates read 0.632 where correlations read
   0.768.
4. **Interleave arms; never run them in blocks.** A load that drifts across a block boundary biases
   one arm irrecoverably.
5. **Anchor log parsing on message TEXT, never `file.py: func:LINE`.** Line anchors in this arc have
   silently parsed nothing twice. `_add_best_candidate` alone moved
   `:4850 (#539) → :4864 (#555) → :4898 (#562) → :4936 (#566) → :4983 (#567)` — five positions in
   one arc, and it will have moved again by the time you read this.
6. **Verify a guard by making it fail.** Every guard added this session was proved by reverting the
   fix: cascor#564 5-of-6 fail, cascor#566 4-of-5 fail, cascor#567 2-of-5 fail. **One test was
   caught being vacuous this way** — it seeded the global stream *before* constructing the network,
   which the constructor's own `random.seed()` then wipes, so it passed with the bug present.
7. **Say which of your tests are NOT guards.** Each PR above names the cases that pass either way
   (property assertions, forward-guards) so they are not mistaken for regression coverage.
8. **Check a zero for vacuity before believing it — and check the CHECKS.** §1.1 is a zero. Its
   credibility rests on one verified property (`values/run=[32]`, non-degenerate, arm-distinct). Two
   of the four reasons an earlier draft gave were themselves defective: the exit code does not guard
   the correlation marker, and `length_mismatch=0` is entailed by the zero it was offered as
   evidence for. **A reassuring list of reasons is not a check until each reason is tested.**
9. **A timing figure is not a noise floor until you know the instrument's resolution.** §1.2's CLI
   span looked like a 3.3% cv and is actually 1-second quantisation of a near-constant value — its
   sd matches the quantisation formula to 16 digits.
10. **Never compare two fields across arms until you have confirmed they mean the same thing.** The
    `val` column exists on both arms and means different things on each (§1.3); the analyser
    documents that caveat and an earlier draft published the delta anyway.

---

## 6. Operational notes

- `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing from a worktree;
  `JUNIPER_EXP_HEALTH_TIMEOUT=180` (the 90 default is too short for a cold start). The campaign
  script already defaults both correctly.
- **`JUNIPER_EXP_CONDA_DIR`** points the launcher at a shim conda tree — how the service was profiled.
  `ptrace_scope=1` means py-spy must be an **ancestor**; there is no passwordless sudo.
- py-spy `--native` **cannot** be combined with `--nonblocking`.
- Python env is **`/opt/miniforge3/envs/JuniperCascor1`** (torch 2.11.0+cu130, numpy 2.4.4, py 3.13.13
  — the exact environment the goldens were captured in). Note `columnar` is NOT installed there, so
  `juniper-cascor-model/tests/test_utils_optional_deps.py::TestColumnarImportGuard` fails locally and
  passes in CI. That failure is environmental, not yours.
- cascor's logger `print()`s to stdout unconditionally, which **swallows pytest summary lines** in
  local runs. Trust the exit code, not the absence of a summary. (Carried into cascor#573.)
- A cap-64 CLI leg wrote a **637 MB** trainer log; the experiment state dir holds **46 GB**. This
  constrains `k` independently of wall-clock.
- Always `util/experiment_stack.bash --down <RUN_ID>`, using the RUN_ID from your own
  `provenance.json`; a live run holds one port from each of the three 30-slot ranges plus lockdirs.
  `--status` lists every run. **`--down --all-mine` tears down EVERY run under the run root — there
  is no per-session ownership filter** (`experiment_stack.bash:41`, `:1056-1066`), so it will kill
  another session's live stack. The predecessor handoff described it as "closes yours"; that was
  wrong. Reach for it only after `--status` and `ps` show nothing that is not yours.
- **Concurrent sessions are active and merge frequently.** This session found another session running
  a 3-hour `e-a-cascor-budget-sweep` out of the primary cascor checkout; three cascor PRs and 20+
  juniper-ml commits landed from other sessions while this one ran. **Never fast-forward the primary
  checkout or launch a campaign without checking `ps`, the lockdirs, and the three port ranges first.**

### 6.1 Worktrees — READ BEFORE REMOVING ANY

Two entries in an earlier handoff draft were listed as "safe to clean up" while holding uncommitted
work on **detached HEADs**, where removal destroys it and `git worktree prune` orphans any rescue
commit.

**`git status --porcelain` does NOT see ignored files, and `git worktree remove` deletes them
anyway — with or without `--force`.** Every cascor worktree that ran the CLI or the service has a
gitignored `cascor-snapshots/` full of `.h5` models, and `util/snapshot_index.py` roots at the
*primary* checkout, so those models are un-indexed and their disappearance is invisible. Counts at
time of writing: residual-wall-gap **450**, logger-frame-resolution **73**, seeds-and-balance **17**,
candidate-seed-derivation **11** — ~110 MB that five "clean" worktrees are silently holding.

Before removing any cascor worktree:

```bash
git -C <wt> status --porcelain --ignored | head        # the ONLY view that shows the risk
find <wt>/cascor-snapshots -name '*.h5' | wc -l
```

Prefer `util/worktree_cleanup.bash`, which **refuses** on a non-empty snapshot root (see its
`phase_4_cleanup` comment) — but **not** on the `rescue/*` rows below: its `git branch -d` failure
path falls through to `git branch -D`, which would destroy an unmerged local-only branch.

| worktree (under `Juniper/worktrees/`) | state | action |
| --- | --- | --- |
| `juniper-cascor--exp--determinism-postarc--20260823-1945--234c2031` | detached at the campaign SHA, clean | **keep until §4.1 is done** — it is the **POST-#566** CLI arm's checkout, i.e. the *after* side, and `provenance.json:cascor_src` points at it. **§4.1 step 1 needs a PRE-#566 tree (`362b88b1`), NOT this one.** **Do not move its HEAD** — checking out another build here breaks the §1.1 provenance link without changing a single file |
| `juniper-cascor--fix--candidate-seed-derivation--20260823--362b88b1` | `rescue/candidate-seed-derivation-wip` (8870bf9) — **local-only, unpushed, NOT an ancestor of `origin/main`** | cascor#566 shipped the *fix* but **not** the `DIAG:` instrumentation this branch carries, which is exactly what §4.1 step 1 needs (`git grep DIAG origin/main -- src` → nothing). Redundant **only** against `util/ad-hoc/2026-08-23_cascor_seedfix_and_worker_diag.patch` on juniper-ml `main` — confirm that file exists before removing, and keep it |
| `juniper-cascor--diag--seeds-and-balance--20260821-2115--362b88b1` | `rescue/seeds-and-balance-diag-wip` (70590f2) — same, local-only | same caveat; its twin is `util/ad-hoc/2026-08-21_cascor_seeds_and_balance_diag.patch` |
| `juniper-cascor--fix--logger-frame-resolution--20260823-1200--acf953b3` | branch, merged (cascor#563) | safe to remove — **after** the snapshot check above (73 `.h5`) |
| `juniper-cascor--exp--residual-wall-gap--20260821-0800--362b88b1` | detached, clean | safe to remove — **after** the snapshot check (450 `.h5`, 89 MB of its 105 MB) |
| everything else listed by `git -C ../juniper-cascor worktree list` | other sessions' work | **leave alone** |

Note the campaign's own retirement note (`2026-08-20_determinism_campaign.bash` header: *"Retire
when: #532 is root-caused … delete then"*) targets the same `util/ad-hoc/*.patch` files that make the
`rescue/*` branches redundant. **Do not retire the patches and delete the branches in the same arc**
— that is the only pair of copies.

This session created and removed three worktrees — `fix--candidate-unit-repr`,
`fix--candidate-seed-derivation--20260823-1840`, `feat--worker-profile-dispatcher`. They ran only
pytest, which redirects snapshots to a `tempfile.mkdtemp()` (`src/tests/conftest.py:105-108`), so
they held no models. That is *why* their removal was safe — not the absent `--force`.

### 6.2 Tooling on `main`, and how to land a change

All under juniper-ml `util/ad-hoc/` unless noted. **"Now cheap" claims in §4.8 are only true if you
know which script to run.**

- **Determinism:** `2026-08-20_determinism_nrun.py` (rate + bootstrap CI + dual fingerprint;
  `--dir-arm` / `--suite-arm`) · `_campaign.bash` · `_arm.bash` · `_localize.py` · `_diag.py` ·
  `_report.bash` · `_watch.bash` / `_await.bash`
- **Wall gap:** `2026-08-21_h2h_paired_campaign.bash` · `_paired_ratio.py` · `_h2h_pool_balance.py`
  (LPT critical path) · `2026-08-22_h2h_sweep_ratios.py` · `2026-08-21_detach_campaign.bash` ·
  `2026-08-16_h2h_phase_split.py`
- **Profiling:** `2026-08-23_pyspy_conda_shim.bash` · `_pyspy_cli_leg.bash` ·
  `_h2h_native_profile_diff.py` · `_h2h_worker_profile_diff.py`
- **Suites** (`util/experiments/suites/p4/`): `e-l-determinism-cap4.yaml` (20 replicates),
  `e-m-h2h-paired-cap64.yaml`, `e-n-profile-cap4.yaml`

**Landing path — direct pushes to `main` are blocked on every repo:**

```bash
python3 util/wait_for_checks.py --pr N --repo juniper-cascor --anchor required
util/safe_merge.py --pr N --repo juniper-cascor --merge-method squash --execute
```

---

## 7. Git state (re-derive; concurrent sessions push often)

**Every SHA below is stale the moment it is written — other sessions merge constantly. Re-derive.**

- **juniper-cascor** `origin/main` at `4a92082`. Two snapshot fixes (#574 `fcb4192`, #575 `4a92082`)
  landed *after* the campaign SHA `234c203`; verified by `git show --stat` that both touch only
  `src/snapshots/snapshot_serializer.py` and snapshot tests — **neither touches seeding, logging or
  the candidate path, so the §1.1 campaign stands.**
  ⚠ The **shared checkout** `Juniper/juniper-cascor` is at `fcb4192`, one behind `origin/main`. A
  successor who works there is not on the SHA this document quotes.
- **juniper-ml** `origin/main` at `8862ad0`; this session's worktree branch at `32fc963`, several
  behind. Sync before branching.
- Authored from session worktree `.claude/worktrees/swirling-spinning-torvalds`.
- Open cascor issues owned by this arc: **#532** (determinism), **#568–573** (the perf-lane surface),
  plus **#530** (service seed field).

## 8. Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main    # expect commits: sessions merge often

gh pr list --repo pcalnon/juniper-cascor --state open
gh issue list --repo pcalnon/juniper-cascor --state open --limit 20
gh issue view 532 --repo pcalnon/juniper-cascor --json number,title,state,comments
# NB: bare `gh issue view 532` and `--comments` fail with a projectCards GraphQL
#     deprecation on this gh build. Use --json. `gh pr edit --body-file` fails the same
#     way; edit a PR body with the REST route instead:
#       gh api -X PATCH repos/pcalnon/<repo>/pulls/<n> -F body=@body.md

# Re-derive the determinism result without re-running the campaign (~seconds, reads logs):
python3 util/ad-hoc/2026-08-20_determinism_nrun.py \
  --suite-arm service ~/.local/state/juniper-experiments/suites/e-l-determinism-cap4-20260824T003754Z/registry.jsonl \
  --dir-arm cli ~/.local/state/juniper-experiments/determinism-n20-postarc

python3 -m unittest tests/test_experiment_suite_yamls.py
util/reap_pytest_orphans.bash --dry-run    # NEVER while a campaign is in flight (§3.3)
ss -ltn | awk 'NR>1{split($4,a,":"); p=a[length(a)]+0; if ((p>=8110&&p<=8139)||(p>=8230&&p<=8259)||(p>=8260&&p<=8289)) print p}'
ls -1 /run/user/1000/juniper-experiments   # non-zero may be a CONCURRENT session, not a leak
```
