# CLI Experimentation — Post-Arc Determinism Evidence, and the Attribution of the Closure

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: juniper-ml (evidence spans juniper-cascor builds)
**Author**: Paul Calnon
**Date**: 2026-08-24
**Status**: Evidence of record — supersedes the "attribution open across 24 commits" framing of the 2026-08-24 handoff
**Related issues**: [cascor#532](https://github.com/pcalnon/juniper-cascor/issues/532) (the defect), [cascor#578](https://github.com/pcalnon/juniper-cascor/issues/578) (baseline-tier decision), [cascor#579](https://github.com/pcalnon/juniper-cascor/issues/579) (post-#563 worker profile), [cascor#572](https://github.com/pcalnon/juniper-cascor/issues/572) (latent numpy-position seeding defect), [cascor#530](https://github.com/pcalnon/juniper-cascor/issues/530) (service seed field)
**Predecessor evidence**: [seed-reproducibility note](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md) · [residual wall-gap note](JUNIPER_2026-08-21_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-RESIDUAL-WALL-GAP-EVIDENCE.md) · [fix design](JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md) · [perf-lane register](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md)

---

## 0. Headline, stated carefully

1. **The direct-CLI seeded-run reproducibility defect (cascor#532) no longer reproduces.** On the 2026-08-24 N=20 campaign (both arms at cascor `234c203`), the direct CLI measures **0/190 diverging pairs on both fingerprints** where the pre-arc build (`4bec1be`, #539) measured **0.768** [0.553, 0.847]. (§1)
2. **cascor#566 — the candidate-seed derivation fix — did NOT close it.** An N=20 instrumented arm at `e4e5b990` (#565), the **direct parent** of #566, is already fully deterministic: byte-identical per-round candidate-seed lists, identical installed-candidate sequences, identical exact correlations, 0/190 on both standard fingerprints. The closure therefore lies in `(#539, #565]`. (§3.3)
3. **The closure is attributed to cascor#563 — the ~9× logger fix — bracketed to ONE commit**: at `acf953b3` (#562, #563's direct parent) the CLI diverges at 0.847/0.932 (trace/correlations) at N=20; at `6a3d1a87` (#563) it reads 0/190. The mechanism, read off the #562 seed data: a **time-coupled parent-side consumer of the global `random` stream** (round-1 seed lists are shifted windows of one sequence; shift correlates r = 0.931 with round-0 wait-loop polls). #563 collapsed the waiting ~9×, pinning the consumption count — **the closure is emergent from speed, not designed**. (§3.5)
4. **#566 is thereby upgraded from hygiene to the structural guarantee**: it did not close the gap (its parent was already deterministic), but by making candidate seeds a function of `(random_seed, k)` it removes the *reader* of the stream the time-coupled consumer perturbs — on any pre-#566 build a sufficiently slow cell would re-diverge; post-#566 it cannot. Its deliberate golden-baseline reset stands on its own terms; its measured cross-arm round-0 offset fix addresses the **cross-arm** difference, not run-to-run.
5. **The two arms still disagree with each other** (11,310 CLI vs 13,140 service candidate epochs at cap 4 on `234c203`) while each is internally reproducible. Two structural causes are now identified in code; neither is a defect in the determinism sense. (§4)

Terminology (arm, cap-N, trace vs correlation fingerprint, `span = work × rate`) follows the 2026-08-24 handoff §1.8.

---

## 1. The post-arc campaign (what the handoff's §1.1 recorded, re-derived today)

Campaign: `util/ad-hoc/2026-08-20_determinism_campaign.bash`, N=20 per arm, cap 4, strictly sequential, both arms at cascor `234c203` (includes #566), host `nproc=16`, CLI-arm load1 8.44–10.43 (no load record exists for the service arm — the campaign samples `/proc/loadavg` only inside the CLI loop).

| arm | trace fingerprint | correlation fingerprint | distinct outcomes | candidate epochs |
| --- | --- | --- | --- | --- |
| service | 0/190 = 0.000 | 0/190 = 0.000 | 1 of 20 (`d52981ffdaf5`) | 13,140 ± 0 |
| direct CLI | 0/190 = 0.000 | 0/190 = 0.000 | 1 of 20 (`f939751d1347`) | 11,310 ± 0 |

Re-derived 2026-08-24 from the stored logs (`determinism-n20-postarc` + suite `e-l-determinism-cap4-20260824T003754Z`) with `util/ad-hoc/2026-08-20_determinism_nrun.py`; output matched the handoff's figures exactly.

**Why this zero is not vacuous** (each property checked, not assumed):

- 20/20 runs usable in both arms; no exclusions.
- The correlation fingerprint extracted `rounds=[4], values/run=[32]` in both arms, and the 32 values are non-degenerate and arm-distinct (CLI 0.009213–0.105662, service 0.032598–0.121684). The zero is a comparison of 32 real values per run over 190 pairs.
- The two arms carry different fingerprints, so the CLI arm did not silently run the service path.
- **Not evidence, and not offered as such**: the analyser's exit code (its stale-anchor `exit 2` does not guard the correlation marker — a dead `RE_CORR` still prints `0/190` and exits 0, betrayed only by `values/run=[0]`), and `length_mismatch_pairs=0` (entailed by the zero, not independent).

### 1.1 Timing upper bound (not a noise floor)

| arm | training span | candidate phase | output phase | candidate epochs | s / candidate epoch |
| --- | --- | --- | --- | --- | --- |
| CLI | 15.4 ± 0.5 s (cv 3.3%) | 11.0 ± 0.7 s | 3.9 ± 0.3 s | 11,310 ± 0 | 0.00097 ± 0.00006 |
| service | 17.4 ± 0.9 s (cv 5.1%) | 12.7 ± 1.0 s | 3.9 ± 0.3 s | 13,140 ± 0 | 0.00096 ± 0.00008 |

Read as an **upper bound**, for three verified reasons: (1) log timestamps have 1-second resolution — the CLI span takes exactly two values (15 s ×12, 16 s ×8) and its sd equals `sqrt(20/19 × 0.4 × 0.6)` to 16 digits, i.e. pure quantisation of a near-constant span, so the CLI's "cv 3.3%" measures the clock; (2) the arms ran as blocks, not interleaved, so the cross-arm span delta is not load-controlled — only the within-arm dispersions are; (3) detectability ≠ cv — at n=20 the cross-arm span difference resolves to ≈0.6 s at 80% power, but per (1) the underlying sd is an artefact. Sizing a cap-4 CLI comparison needs sub-second timestamps this instrument does not emit.

---

## 2. The pre-arc baseline, re-verified before being leaned on

Because §3 makes the pre-arc 0.768 load-bearing (it is the "before" of the closure), it was re-derived today from the preserved evidence rather than trusted:

- `determinism-n20/provenance.json` is intact: single line, `cascor_sha 4bec1beff89b...` (#539), a **dedicated** worktree as `cascor_src` (not the shared checkout), same content-addressed cell `c000-7749f335` as every later campaign.
- `cli-01/logs/` holds a single un-rotated trainer log — no §3.2-style two-builds-merged contamination.
- The analyser over the stored root reproduces: trace **0.632**, correlations **146/190 = 0.768** [0.553, 0.847], **7 distinct outcomes of 20**, candidate epochs **10,734 ± 276 (cv 2.6%)**, span 280.8 ± 14.7 s.

Note what the pre-arc data itself says: the divergence was not cosmetic — seven outcome classes, and the **work itself varied** run to run (±276 epochs), i.e. early stopping fired at different points on identical configuration.

---

## 3. Attribution of the closure

### 3.1 The surface, and what code reading eliminated

The pre-arc comparator (`4bec1be`, #539) and the campaign (`234c203`, #567) are 24 commits apart. The 2026-08-24 handoff named #556, #562, #565 as rivals to #566, with #556 ("W-11 full parity — the direct CLI now honours the keys it was dropping") the strongest.

**#556 is inert for this exact cell** (`e-l-determinism-cap4`, cell `c000-7749f335`):

- Of its nine un-dropped keys, **seven are absent from the cell YAML** and resolve to the same constants on both sides of #556.
- `early_stopping: true` equals `fit()`'s own pre-#556 default (`cascade_correlation.py`, `def fit(..., early_stopping: bool = True)` at `4bec1be`).
- `max_iterations: 128` never binds: a cap-4 run executes ~4 growth iterations, and the pre-#556 fallback (`_PROJECT_MODEL_MAX_ITERATIONS = 1000000`, or the config default) is equally non-binding. Inside `grow_network` the value reaches only a display callback and `ValidateTrainingInputs` bookkeeping.
- Independent of that: honouring config keys changes the *effective configuration*, which is constant across runs either way — a config-value shift cannot create or remove **run-to-run** variance on identical input. (It can and does matter for the **cross-arm** comparison, §4.)

**#567 is inert without its env var**: unset `JUNIPER_CASCOR_WORKER_PROFILE` costs one `os.environ.get` and a direct call to the extracted impl. No campaign run sets it.

That leaves #566 isolable by a single experiment at its direct parent.

### 3.2 The instrument

`util/ad-hoc/2026-08-21_cascor_seeds_and_balance_diag.patch` (log-only; three added INFO lines): per-round `candidate_seeds=[...]` as drawn in the parent, exact (unrounded) per-candidate correlations, and the installed candidate's index per iteration. Applied verbatim (offsets only) to each probe build and committed on a local `diag/*` branch, so every run's provenance SHA names an instrumented tree:

| probe build | base | diag branch (local-only) | worktree |
| --- | --- | --- | --- |
| #565 | `e4e5b990` | `diag/seed-instability-at-565` (`f6b8dd6`) | `worktrees/juniper-cascor--diag--seed-instability-at-565--20260824-0510--e4e5b990` |
| #563 | `6a3d1a87` | `diag/seed-instability-at-563` | `worktrees/juniper-cascor--diag--seed-instability-at-563--20260824-0540--6a3d1a87` |
| #562 | `acf953b3` | `diag/seed-instability-at-562` | `worktrees/juniper-cascor--diag--seed-instability-at-562--20260824-0540--acf953b3` |

Runner: `util/ad-hoc/2026-08-20_determinism_arm.bash` (N=20, `threads=default`, the same materialised cell as the post-arc campaign, one juniper-data stack, `setsid nohup`, strictly sequential arms — the per-run teardown pkills by cell path, so overlapping arms would kill each other). Analysis: `util/ad-hoc/2026-08-24_seedvar_analysis.py` (seed-level; carries named vacuity guards) plus the standard `2026-08-20_determinism_nrun.py` (both fingerprints). Chain driver for the bisection pair: `util/ad-hoc/2026-08-24_seedvar_probe_driver.bash`.

### 3.3 The decisive result: the CLI is already deterministic at #565

N=20 at `e4e5b990` (#565, direct parent of #566), load1 10.2–12.7, 20/20 clean exits, 20/20 instrumented:

- **Candidate-seed lists: byte-identical in every round across all 20 runs.** Four rounds per run, pool size 8, `network_seed=42`; 1 distinct list per round; seed-fingerprint pair divergence **0/190**.
- **Installed-candidate fingerprints (index + exact correlation per iteration): 1 distinct of 20.**
- Standard instrument: trace **0/190**, correlations **0/190** (`rounds=[4], values/run=[32]`), single outcome `6e385c505c20` × 20, candidate epochs **11,900 ± 0**.

Vacuity guards, all named and passing: every run carried DIAG lines (the instrument was verified live on run-01 before the arm was trusted); rounds/run `{4: 20}`; pool sizes `[8]`; the analyser's values are non-degenerate and build-distinct (the #565 outcome fingerprint differs from both `234c203` arms', as expected across #566's golden reset).

**Consequences:**

- **#566 did not close the within-CLI determinism gap.** The gap was already closed at its parent.
- The handoff §1.1's mechanism hypothesis — thread-context-dependent consumption of the global stream varying candidate seeds run to run — is **refuted at the seed level for this window**: seeds drawn off the global stream were already run-to-run constant at #565. (Whether they varied at the pre-arc build is what §3.5's #562 probe measures; constancy at #565 already severs #566 from the closure.)
- The closure lies in `(#539, #565]`.

### 3.4 What is in the window, and the leading hypothesis

Commits `4bec1be..e4e5b99` net of docs/CI: snapshot-path fixes (#542, #548, #551, #553, #554, #558–#561, #565 — save/load bookkeeping, no RNG or threading), settings cleanup (#549, orphaned constants), CORS (#540, service-only), W-11 parity (#556, inert per §3.1 for run-to-run variance), config-resize sync (#562, deterministic bookkeeping), `CandidateUnit.__repr__` (#564, representation only), and **#563 — `perf(logger): resolve the caller from f_back instead of walking the whole stack (~9x faster training)`**.

No commit in the window touches RNG derivation or thread policy. #563 is the only one that materially changes the training hot path's runtime behaviour — and the pre-arc mechanism was already known to be timing-linked (moving `fit()` to a pool thread cut divergence 0.768 → 0.337; BLAS `threads=1` did **not** fix it; the arrival-order tie-break was ruled out on 28/28 pairs). Hence the bisection pair: probe #563 (fast build, ~27 s/run) and its parent #562 (pre-#563 logging, ~280 s/run).

### 3.5 Bisection probes at #563 and #562: the closure is #563, bracketed to one commit

Both probes N=20, 20/20 clean exits, 20/20 instrumented, same cell / stack / host, chained strictly sequentially (`util/ad-hoc/2026-08-24_seedvar_probe_driver.bash`):

| build | seed lists run-to-run | trace fp | correlation fp | outcomes | candidate epochs | span |
| --- | --- | --- | --- | --- | --- | --- |
| `6a3d1a87` (#563) | identical every round | 0/190 | 0/190 | 1 of 20 (`6e385c505c20`) | 11,900 ± 0 | 20.2 ± 2.0 s |
| `acf953b3` (#562) | **round 0 identical; rounds 1–3 DIVERGE (5/6/8 distinct lists)** | **161/190 = 0.847** [0.684, 0.884] | **177/190 = 0.932** [0.795, 0.942] | 8 (trace) / 13 (corr) of 20 | 11,012 ± 872 | 347.8 ± 49.5 s |

`#562 → #563` is one commit. **cascor#563 — the `f_back` logger fix — closed the defect.** Both sides ran under identical harness conditions (same cell, same stack, same load regime, interleaving unnecessary because the claim is within-arm), so the bracket carries its own control: the harness demonstrably CAN show the divergence, one commit earlier. Note also that #563's and #565's outcome fingerprints are **identical** (`6e385c505c20`) — #564 and #565 do not move the trajectory at all, closing that inertness argument empirically rather than by inspection.

**The mechanism, read off the #562 data.** The round-1 seed lists across the 20 runs are **shifted windows of one deterministic stream** — e.g. `[2119634399, 3246059658, 3698408854, …]` (6 runs), the same sequence offset by one draw (6 runs), by two (3 runs), by three (4 runs), by five (1 run). So the pre-#563 nondeterminism was **variable consumption of the process-global `random` stream between candidate rounds**: every run draws the same values in the same order, but a run-varying number of them is consumed before each round's `candidate_seeds` draw, so different runs hand different seeds to rounds 1–3 — and diverge hard from there (0.932). Round 0, drawn before any waiting, is identical everywhere.

**The consumption is time-coupled.** Per run, the round-1 shift correlates at **r = 0.931** with the number of `_collect_training_results: Result queue empty, continuing` poll records in round 0 (≈1 s per poll; shift-0 runs polled 81–88 times, shift-5's run 123) — roughly one extra stream draw per ~7 s of parent-side waiting. A template-level diff of the full INFO-record sequences between a shift-0 and a shift-1 run shows **exactly one** template differing in count: that empty-poll line (86 vs 90). The drawing call path is therefore parent-side, exercised during the wait loop on a time-coupled cadence, and logged only below INFO. The complete stdlib-`random` surface at #562 (grepped across `src/` for every drawing method) is: network construction seeding, `CandidateUnit._initialize_randomness` / `_seed_random_generator` (`candidate_unit.py:319/:364`), and the per-round `candidate_seeds` draw — so the consumer is seeding-routine activity, not application logic. Eliminated by direct check: the logger itself (no `random` usage), worker retries/fallbacks (zero such events in any of the 20 logs), snapshot saves (exactly 5 per run at both #562 and #563 — count-deterministic, per-round-boundary), remote-worker paths (unused), and the workers themselves (separate processes; they cannot touch the parent's stream). The precise trigger is left untraced: it lives on a dead regime (#563 collapsed the waiting) and a decoupled surface (#566 removed the reader).

**Why a logger fix closes a seeding defect.** #563 made rounds ~9× faster (candidate phase 342 s → 15 s per run at cap 4). The time-coupled consumer's *count variance* scales with time spent waiting; at ~85 s rounds it wandered by 0–5 draws (⇒ 0.932 divergence), at ~4 s rounds it is pinned at a constant (⇒ 0.000). This is also quantitatively consistent with the pre-arc baseline (`4bec1be`: ~69 s rounds, 0.768) and with the thread-context mitigation's partial effect (changing scheduling changes the consumer's cadence without removing it: 0.768 → 0.337). The closure is therefore **emergent from speed, not designed**: on any pre-#566 build, a sufficiently slow cell (larger cap, slower host, heavier logging) would bring the variance back.

**This upgrades #566 from hygiene to the structural guarantee.** Post-#566, candidate seeds are a function of `(random_seed, k)` and *no training-relevant code reads the global stream after construction* — the time-coupled consumer may still run, but nothing listens. #563 is why today's cells read zero; **#566 is why tomorrow's slower cells will too.** The remaining stream-coupled surface is construction-time only: cascor#572 (+ #530), which is exactly where a designed guarantee should be finished.

### 3.6 The thread-context mitigation (handoff §4.9): DROP

`util/ad-hoc/2026-08-20_cascor_thread_context_diag.patch` (the artifact of record, on juniper-ml `main`) cut the pre-arc divergence 0.768 → 0.337 by moving the CLI's `fit()` onto a pool thread. On current builds the **unmitigated** CLI reads 0.000 at N=20 (at #565, and at `234c203`). It was always symptom-shaped; the symptom no longer reproduces. **Recommendation: do not merge; close it out in cascor#532.** The patch stays on `main` as the record; if attribution had landed somewhere unexpected, the question could be reopened from it.

---

## 4. The arms still disagree with each other (cross-arm, not run-to-run)

Each arm is internally reproducible on `234c203`; they produce different results from each other: **11,310 vs 13,140 candidate epochs**, train accuracy 0.6075 vs 0.6462. (Per the analyser's own cross-arm caveat, no `val` comparison is quoted — the CLI's figure is a post-fit test-set accuracy, the service's an in-loop validation accuracy.) Two structural causes are now located in code:

1. **The tiers give the dataset's test split different roles.** The service maps the NPZ's `X_test`/`y_test` into **validation tensors** (`src/api/lifecycle/manager.py:3391`, `new_val_x = torch.tensor(arrays["X_test"], ...)`) that feed patience and early stopping in-loop; the direct CLI passes no val tensors at all — every in-loop record reads `validate_training: Iteration N (no val data)` (verified in the stored campaign logs). Different stopping signals ⇒ different candidate-epoch totals, sufficient on its own.
2. **The arms differ from iteration 0** — CLI loss 0.239217 / acc 0.5787 vs service 0.240292 / 0.6088 (verified in stored logs) — i.e. before any candidate round, implicating construction-time state. Post-#566 the *candidate* seeds are path-independent, but network-level init still is not: `_seed_random_generator` draws its roll counts from the stdlib global stream (three construction-time consumers), and `SpiralProblem` (CLI-only) consumes extra values first — the same class of offset #566's comment measured for candidate seeds. That is exactly **cascor#572** (numpy's stream position is not a function of the seed), plus **cascor#530** (the service's seed is pinned at 42 with no `TrainingParams` field).

Neither is a run-to-run defect. Both belong to the cross-arm parity conversation (cascor#578's baseline-tier decision; a parity issue for the val-split asymmetry is proposed in §6).

---

## 5. The *work* term: three published values reconciled (handoff §4.11)

The handoff carried "three unreconciled values for one quantity". Reconciliation: **they are not one quantity.**

| value | quantity | convention | cap | build | source |
| --- | --- | --- | --- | --- | --- |
| 0.945× | candidate **work** (epochs) | cli/svc | 4 | pre-#563 (`362b88b1`-era) | residual note §3.3b |
| 1.206× | candidate **work** | cli/svc | 16 | pre-#563 | residual note |
| 1.454× | candidate **work** | cli/svc | 64 | pre-#563 | residual note |
| **1.230×** | candidate **work** | cli/svc | 16 | post-#563, pre-#566 (`f1-paired-cap16`) | fix design §verification |
| **1.308×** | candidate **phase** (wall-clock) — **not a work value** | cli/svc | 16 | post-#563, pre-#566 | fix design: `1.308 = 1.230 (work) × 1.065 (rate)` |
| **1.162×** | candidate **work** | **svc/cli** | 4 | post-#566 (`234c203`) | §1 campaign (13,140 / 11,310) |

So: the handoff's "predecessor: 1.308" entry mislabelled a phase ratio as a work ratio (the fix design itself decomposes it); and §1.2's 1.162 is the **reciprocal convention** — as cli/svc it is **0.861**, whose true comparator is the pre-#563 cap-4 value **0.945**, not the cap-16 1.230. The cap-4 work ratio moving 0.945 → 0.861 across the window is consistent with #566's deliberate golden reset (different seeds ⇒ different candidates ⇒ different work) and with the val-split asymmetry (§4.1); it is a **cross-arm** phenomenon and stays open under the G1/G2 successor items, not as a determinism defect.

The perf-lane register's G2 row ("The work term (1.230) is G1/G1a and untouched") should be annotated: 1.230 is the cap-16, post-#563/pre-#566 value; the term is cap-dependent and direction-flipping (0.945 / 1.206 / 1.454 at caps 4/16/64 pre-#563), and its open successor is the cross-arm disagreement (§4), not run-to-run nondeterminism (closed).

---

## 6. Register and tracker updates this note carries

| item | update |
| --- | --- |
| **G1** (cascor#532) | Post-arc: CLI 0/190 unmitigated at N=20 on two builds (#565, `234c203`). Closure attribution per §3.5. The "cause identified: fit() thread context" sentence is superseded — thread context modulated the pre-arc symptom (0.768 → 0.337) but the closure came from `(#539, #565]`, and candidate seeds were already run-to-run constant at #565. "Blocks P3 thresholds resting on direct-CLI single-run numbers" is lifted. |
| **G1a** (residual 0.337) | **CLOSED, explicitly**: it was a property of the *mitigated pre-arc* build; the current *unmitigated* CLI reads 0.000. Resume-from data if ever reopened: reproducibility note §4.4 (16/4 split, 2 correlation-outcome classes, 0.5 pp val). Closing it removes the last blocker on a CLI-side "reproducible" claim — a P3-gate consequence. |
| **G1b** | **SHIPPED** as cascor#564 (`CandidateUnit.__repr__`). |
| **G2** | Annotate the work-term sentence per §5. |
| **G4** | cascor#571 (no instrument yet; fixed overhead dominates post-#563). |
| **G5** | cascor#568 (F2) / #569 (F3), both gated by #570. |
| **G6 (new id)** | cascor#570 — forkserver isolation not delivered (workers carry the launcher's module table). Previously had no G-id. |
| new trackers | cascor#578 (baseline-tier decision, was handoff §4.12); cascor#579 (post-#563 worker profile, was handoff §4.10). Proposed additionally: a parity issue for the val-split asymmetry (§4.1 — the tiers give `X_test` different roles). |

---

## 7. Raw data and provenance

All under `~/.local/state/juniper-experiments/` (preserve per the handoff §3.2 rules — never sweep by name; a campaign's service arm lives in top-level run dirs referenced by `suites/*/registry.jsonl`, not in the campaign's `OUT_ROOT`):

| root | what |
| --- | --- |
| `determinism-n20/` | PRE-arc CLI arm (`4bec1be`, #539) — the 0.768 baseline. 1.1 GB. |
| `determinism-n20-postarc/` + `suites/e-l-determinism-cap4-20260824T003754Z/` | The `234c203` campaign, both arms (service via the suite registry). |
| `seedvar-n20-at565/` | This note's §3.3 arm: N=20 instrumented CLI at #565. `provenance.json`, `seedvar_report.json`, `at565/run-01..20/`. |
| `seedvar-n20-at563/`, `seedvar-n20-at562/` | §3.5 bisection probes (chained driver log: `seedvar_probe_driver.log`). |

Instrumented builds: the three `diag/seed-instability-at-56{2,3,5}` local branches (worktrees above). The diag patch and every analysis script are on juniper-ml `main` under `util/ad-hoc/`. Stack for all instrumented arms: run `20260824T095117Z-304c` (juniper-data `0.11.0` at `127.0.0.1:8110`).

Methodology observed throughout (handoff §5): N=20 for any zero; both fingerprints carried; message-text anchoring; instrument verified live before its zero was believed; the two named non-evidence properties of §1 excluded from the argument.
