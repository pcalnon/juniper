# HANDOFF 2026-08-31 — the partition arc: measurements done, plan NOT approved, shared prerequisite LANDED

Successor to `HANDOFF_2026-08-26_perf-lane-live-remeasure-586-570-579-closed-f3-landing.md`.
Its §3 work order is **mostly** discharged — rows 3 and 5 are not (cascor#530, #578, #550 are all
still OPEN, see §1 item 5) — and its **inherited deferred list is untouched**, carried verbatim into
§1 item 6. This handoff carries a different shape of problem: the measurements came back against the
design's *framing* — its substance survived — and a three-round adversarial review returned **do not
implement** on the plan built from them.

"§N" means a section of this document. Repo roots are
`/home/pcalnon/Development/python/Juniper/<repo>`.

---

## 1. The goal statement

Continue the cascor#582 partition arc. **Do not implement from the partition plan** — it is merged
(ml#1520) but its own status line says *"Do not implement from this document"*, and its §9 carries
seven open findings from a review round that never terminated. **Read the plan
(`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`) and the slot
investigation (`notes/JUNIPER_2026-08-31_JUNIPER-CASCOR_TEST-PARTITION-SLOT-INVESTIGATION.md`) in
full before acting** — §3 and §4 here are pointers, not substitutes.

**Completed, with receipts** (every PR verified MERGED via `gh pr list --json state`; see §6):

- **Both gated measurements done. Both changed the design's argument; neither changed its
  substance** — the results doc's own §4 says so: *"The design's substance — juniper-data owns a
  third partition, `train` does not shrink — is unaffected."*
  - **Selection bias (#582): not resolvable at either budget.** cap 4 n=8 CI `[−0.0136, +0.0311]`;
    cap 16 n=20 CI `[−0.0100, +0.0210]`, sign split exactly 10/10. This **bounds** the effect
    (larger than ~2.1 pp excluded at 95 %); it does **not** show the effect is zero. Cap 64 remains
    unmeasured but is **explicitly no longer the obvious next question** — two budgets differing 4×
    in selection pressure both returned intervals containing zero. **The consequence that matters:
    the motivation for the three-way split is *methodological, not performance*** — selection and
    reporting must not share rows, which is provable without statistics. The design must **not**
    claim the reported numbers are inflated; measurably, they are not. Owner decision 4
    (re-measure) survives anyway, for the unrelated V-1 reason below: the old numbers are not
    inflated, they describe *different data*. (ml#1477, ml#1493; collector
    `util/ad-hoc/2026-08-29_val_split_bias_collect.py`, suites `e-o-val-split-bias-cap4.yaml` /
    `e-p-val-split-bias-cap16.yaml`)
  - **V-1: FALSE.** All **6 of 6 cascor-relevant** juniper-data generators produce different rows
    for N+M vs N at the same seed. The count is preserved, the content is not — so the design's
    baseline-preservation benefit does not exist. (ml#1492; instrument
    `util/ad-hoc/2026-08-30_v1_generator_prefix_check.py`, which now **refuses to report stability
    when both runs return the same row count** — its first version reported PREFIX-STABLE
    vacuously, because a wrong size kwarg was silently ignored by pydantic.)
- **cascor#572 CONFIRMED, fix deliberately deferred.** `_seed_random_generator` draws its roll from
  the global `random` module; only the `np.random.seed` call site diverges — all 63 `manual_seed`
  pairs match. Not float noise. The fix moves every numpy-drawn candidate init, so it is held until
  it will not invalidate in-flight measurements (owner instruction). (ml#1451)
- **Logging hot path: worker self time 84.96 s → 43.20 s (−49 %)** — **a 32-profile cap-4 corpus
  (before) against one profiled cap-4 cell `e-n-profile-cap4` (after)**, and the after-run did
  **15 % more logging** (646,016 → 746,410 calls), so cascor#598's own body calls the headline
  *approximate*. **Quote the work-independent ratios instead**: `__format__` calls 3,626,636 →
  2,912 (1,245×) and `_filter_by_level` 17.3 µs → 1.6 µs per call (10.8×). Nothing here was
  measured at cap 16. (cascor#598, merged)
- **Naming SETTLED: `X_val` / `y_val`, not `X_eval`.** `eval` aliases to **test** in HuggingFace
  `datasets` (the split-keyword map in `datasets/data_files.py`), so `train/eval/test` would resolve
  as two test splits. Do not relitigate. (ml#1469)
- **Plan v3 through three consensus rounds** (ml#1520). Round 1 reviewed v1 and rejected it; the fix
  passes producing v2 and v3 each introduced new defects that the following round caught. Round 3
  never terminated.
- **cascor#614 MERGED** — `15fd35475aa0261dd8aa6bb1fde423f08d8fac63` at `2026-08-31T23:11:40Z`,
  3 files, +229. The shared prerequisite (§2).

**Remaining work, in order:**

1. **Finish the shared prerequisite.** #614 delivered roughly half of the slot investigation's
   six-item minimum (items 1, 3, 4, and the `_PreSwapSnapshot` third of item 2). **Still live — all
   line numbers below are `origin/main` POST-#614, re-verified 2026-08-31:** the **artifact ingress
   at `manager.py:3631`** and the **inline ingress at `:2271`** never write `_test_x` (`_test_x` is
   written only at `:1187` init and `:3391` snapshot-restore). The investigation's pre-#614 `:3533`
   and `:2195` now land on *unrelated but syntactically plausible* code, and the shift is **not
   uniform** (+76 / +87 / +98), so it cannot be corrected arithmetically — **re-grep for
   `self._val_x = `**. The **`"validation"` label** at `:2778` still calls a selected-on number
   held-out; and **`InlineDataset` still silently drops an unknown `test_x`**
   (`src/api/models/training.py:19` declares no `model_config`, so it does not inherit
   `TrainingParams`' `extra="forbid"` at `:62`).
2. **Get D-1 and D-2 ruled** (plan §3). Both are owner decisions. Per plan `:80` verbatim — *"D-1
   gates the sequence chunk, not Chunk 3"* — do not over-block on it. **D-1's premise in the plan
   is false**; re-pose it before asking (§4 S-2).
3. **Wire `_test_x` to the ruled source — do not re-decide the source.** #614 left the slot
   unpopulated, but *how* it gets populated is **already settled**: the artifact's `X_val` once
   juniper-data emits it (design §6, **O-1**), falling back to `X_test` **only** behind an explicit
   run-with-warnings switch (§6.1), with §6.4's gated choice for legacy artifacts that have neither.
   **O-2 — cascor sub-splitting `X_train` locally — is explicitly *not* adopted, "even as a
   fallback"** (design `:161`). A Lane B lens argued for it and plan `:210-213` records that its
   case *"is not refuted here"* — but that bullet's subject is *"That the ecosystem change is the
   right call"*, and its closing sentence, **"The owner elected to proceed with it on the record,"**
   means the owner chose **the ecosystem change** over the unrefuted local fix. Do not read it as
   endorsing the local split.
4. **Work plan §9's S-2 … S-7** (§4 below). S-7 is unrelated to this arc and wants its own ticket.
5. **Owner-timed and unblocked**: cascor#573 items 3–4 (per-logger levels; optional ELK export —
   scoped in the logging design and its call-site analysis, §8); **F-3a**, the swallowed-pytest
   investigation the logging design deferred to its own document; **V-3**, measuring what CLI early
   stopping changes (owner decision 5 makes it mandatory, and it is a behavioural change to an arm
   that was previously unregularised); and cascor#550, #530, #578, #590, #602.
6. **The predecessor's inherited deferred list — carried, NOT closed.** From the 2026-08-26 handoff
   §3 row 6 (itself inherited from 2026-08-24 §4.8 via 2026-08-25 §5), unchanged: cap-series
   re-measure post-F1 (now cheap — a cap-16 k=4 paired campaign runs ~11 min end to end); cap-128
   3-seed spread (**cost-gate first** — the cap-64 log was 637 MB); **retrospective corpus
   re-validation — raise with the owner, do NOT absorb**; #566's "a slow cell would re-diverge"
   corollary (cap-64/128 N≥10 falsifier, never run); optional service-arm census. The host is
   **shared, not exclusive** — coordinate with live peers via `ListAgents` before any multi-hour
   campaign.

**Key context:**

- The **plan is a surveyed map, not instructions.** Its §§2–7 are v3-*as-reviewed*, not
  v3-*as-corrected*; round 3's findings sit in §9 verbatim precisely because folding corrections in
  is what produced the v2 and v3 defects.
- **cascor had no end-of-training evaluation at all** before #614 — every metric was gated on a new
  training-history row and cached, so the "final" number was whichever mid-training computation ran
  last. That gap was upstream of *both* candidate designs, which is why the prerequisite could land
  without settling the design choice.
- **Containers are ground truth, not the host.** A permission-denied docker volume enumerates as
  *empty* and a plausible total still renders; that produced a wrong store-root count inside a
  section certifying personal re-derivation. Use `docker exec`. (S-6; memory
  `containers-are-ground-truth-not-host`)
- **Golden tests sit behind three independent opt-in gates** (`--slow --integration --golden`), each
  revealed only after the previous is satisfied. `exit 0` from that suite means nothing until you
  check the progress line for `s`.

---

## 2. What is in flight

| item | state at handoff | action |
| --- | --- | --- |
| **cascor#614** | **MERGED** `15fd3547`, 3 files / +229 — `_test_x`/`_test_y` slots, `_reported_split()` (deliberately **no** training fallback), `_compute_final_eval_metrics()` on the success path only, per-run reset, `_PreSwapSnapshot` carry, `final` in the payload, 10 new tests of which **one** (`test_does_NOT_fall_back_to_training`) is mutation-verified, one golden line regenerated | Nothing. Re-verify with §6 if in doubt |
| Local cascor worktrees | 22 exist; four belong to this arc: `feat--test-partition-slot--…` (#614 — its remote branch is now deleted and the checkout is ~2 revisions stale), `diag--tensor-hash-probe-572`, `diag--valsplit-cap16-582`, `perf--logging-hot-path`. **All 22 are clean** | The two `diag/*` branches are **local-only provenance refs — never pushed, not for merge**. Do not delete without updating this table. Do not resume work in the `feat/*` checkout; branch from fresh `origin/main` |

## 3. Settled — do NOT relitigate

**Partition design** (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9, owner-settled 2026-08-29):

1. **juniper-data owns the split.** cascor consumes; it may fall back to `X_test` only behind an
   explicit switch. Legacy gaps are repaired by juniper-data via generation or re-partitioning,
   **not** by cascor sub-splitting.
2. **`train` does not shrink.** The requested training count is honoured literally; `eval`/`test`
   are *additional* generated points. Default `100/40/30` → 1000/400/300 (normalised 59/23/18 —
   derived, not configured). **Adjustable** by switch / env / config, **or forced** when no
   generator or generator specs exist, or the data is not synthesisable (design §6.3) — that carve-up
   path is required for the real-data suites, so do not implement additive sizing without it.
3. **Legacy artifacts without the eval partition: a gated choice, never a silent default** — fill
   synthetically / continue with recorded warning / back to dataset config / cancel. **Headless
   default is refuse-and-shut-down, overridable only by an explicit run-with-warnings or
   add-synthetic-data switch.**
4. **Pre-change results: re-measure preferentially, retain the originals annotated** — so nothing is
   silently compared across the semantics boundary.
5. **The CLI early-stops.** No fundamental structural or methodological difference between the CLI
   and canopy arms.

Plus the design's §5 invariant: **`test` is touched exactly once, after training completes** — the
invariant #614 built the machinery for.

**Logging design** (`…LOGGING-REDESIGN-DESIGN.md` §7, owner-settled 2026-08-29): (1) measure the
discarded-record share **before** building — **already DISCHARGED**, do not re-run it (results doc
§4); (2) flush **per record**; (3) **per-process file handle**, lazily opened after fork —
**explicitly provisional**, per-PID files and a parent writer thread stay on the table; (4) keep
**stdout** — relocation is not the fix for the swallowed-pytest problem, which gets F-3a —
**also provisional, revisit if it becomes problematic**; (5) call-site migration scope **deferred,
still the owner's call** — the analysis found 1,885 sites / 879 f-strings, but 36 % of sites and
essentially all tensor formatting live in two files, so hot-path-only is a ~150-site diff, and it
recommends guards + `%`-args on the hot path, explicitly **not** a full sweep; (6) structured JSON
**through `juniper-observability`**, no cascor-local second implementation.

The measurements changed the logging design's **priority order** (§5's payoff table is superseded)
but left decisions 2–6 untouched — they concern sinks and levels, not what gets interpolated.

Still open in the partition design: **V-2** (measure the leak before removing it) and **V-3**.

## 4. Round 3's open findings (plan §9), condensed

- **S-1 — PARTIALLY answered by cascor#614.** The *diagnosis* was right (as of `da262a76` there was
  no test slot and no end-of-training evaluation); both now exist, and the *fix* is half-delivered.
  See remaining-work item 1 for the three live pieces.
- **S-2 — D-1's premise is FALSE.** The plan says `full == train + test` is "already violated by
  every shuffled tabular generator". The clauses are `len()` identities; shuffling cannot violate a
  length, and `test_e2e_workflow.py:299-301` asserts it passing. **Re-pose D-1 before asking the
  owner to rule.** A fourth option is live and unstated: ratify the current superset semantics.
- **S-3 — extending `NPZ_SPLITS` is owned by no chunk.** v3 cut the dangerous half of a correction
  and the legitimate half with it; Chunk 1 *pins* the 3-tuple, freezing the gap.
  `validate_npz_contract` **does** have a fleet consumer — verified at
  `juniper-recurrence/juniper-recurrence/juniper_recurrence/data.py:77` (note the doubled directory;
  that repo has **no** `src/`, and the plan's `src/`-bearing path does not resolve). The plan's §1
  says there is no consumer and its §2 contradicts it.
- **S-4 — §6a's gate spec says "`X_val` ⟹ 2-D"**, which rejects every sequence val artifact the
  deferred chunk would ship. Needs the ndim dispatch `contract.py:67-73` already has.
- **S-5 — three of four juniper-ml homes are wrong.** `ecosystem.yaml:31` (`npz_contract:` — the
  plan's `:32` is off by one) is documentation-only; nothing reads it. Homing an ml file inside a
  juniper-data chunk makes that chunk cross-repo.
- **S-6 — the store-root count was vacuous.** ≥4 reachable roots, not 3, of which only 1 is live;
  the live docker volume holds artifacts present nowhere on the host. **R-3's blast radius includes
  a store the plan did not know existed.**
- **S-7 — side-finding, unrelated to this arc:** `juniper-canopy/src/demo_mode.py:1845` justifies a
  hand-rolled probe because `validate_npz_contract` is "absent from the pinned client". The live
  canopy container runs 0.4.2 and **has** it; only the stale local `JuniperCanopy1` env (0.4.1)
  lacks it. **Wants its own ticket.**

## 5. Traps this session confirmed

1. **A handoff's "merged/filed" table is a plan, not a receipt.** The predecessor asserted a PR was
   opened; none ever existed. Probe with `gh pr list --head <branch> --state all` — `--state open`
   cannot distinguish "never opened" from "already merged".
2. **`--auto` alone does not merge on these repos.** Green + armed + `BEHIND` sits forever; an
   explicit `update-branch` is required. Confirmed three times this session (#614 happened not to
   need it).
3. **`juniper-symbol-loss-check` screens 0 files** without an explicit `--files` list, and still
   reports `OK`.
4. **`log_config/logger/logger.py` is on `test_drift.py`'s `_INTENTIONAL_DIVERGENCE` allowlist** —
   mirroring it into `juniper-cascor-model` **fails** the drift gate. `candidate_unit.py` is
   byte-gated and **must** be mirrored. They are not the same rule. The allowlist is
   `src/tests/.../test_drift.py:31`. **The memory `cascor-model-verbatim-extraction-drift` already
   states the exception correctly in its body** — only its one-line `description:` frontmatter
   carries the blanket "mirror or CI fails" version, so read the body, not the summary. No
   `docs/REFERENCE.md` in either repo states a mirror rule at all.
5. **Run `black` before mirroring**, never after — the hook covers only `src/`.
6. The isolated-session command guard refuses `for` loops, heredocs, `${PIPESTATUS}`, the bare word
   `enable`, and `git -C` aimed at **this** repo (primary or sibling worktree). `git -C <other
   repo>` is fine. Multi-step logic goes in a `util/ad-hoc` script.

## 6. Verification commands

```bash
# The shared prerequisite — check origin/main, NOT the frozen primary checkout (see §7)
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor fetch origin
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor show \
  origin/main:src/api/lifecycle/manager.py | grep -c '_test_x'   # 7 post-#614 (0 on the stale primary)
gh pr view 614 --repo pcalnon/juniper-cascor --json state,mergedAt,mergeCommit

# Session receipts — all nine should read MERGED.
# ASSERT THE COUNT FIRST. This query walks a rolling window: at 2026-08-31 a --limit of 200 already
# truncated at #1340, only 77 PRs below the oldest cited (#1417). Once the window passes it, the
# listing silently prints fewer rows and STILL EXITS 0 — trap 1 reproduced inside its own receipt.
# If this prints < 9, RAISE THE LIMIT; do not read a short listing as "PR absent".
gh pr list --repo pcalnon/juniper-ml --state all --limit 400 --json number \
  --jq '[.[]|select(.number|IN(1417,1451,1465,1469,1477,1492,1493,1520,1523))]|length'   # must be 9
gh pr list --repo pcalnon/juniper-ml --state all --limit 400 --json number,state,title \
  --jq '.[] | select(.number|IN(1417,1451,1465,1469,1477,1492,1493,1520,1523)) | "\(.number) \(.state) \(.title[0:68])"'
gh pr view 598 --repo pcalnon/juniper-cascor --json state --jq .state

# The arc's issues, open AND closed — so a closure is visible rather than a silent absence
gh issue list --repo pcalnon/juniper-cascor --state all --limit 60 --json number,state,title \
  --jq '.[] | select(.number >= 530) | "\(.number) \(.state) \(.title[0:60])"'

# Is the cascor primary safe to pull? (non-zero => FROZEN, do not pull)
# FAILS OPEN: ~449 of 875 /proc entries are permission-denied, so it cannot see other users'
# processes. A zero is "I saw nothing", not "nothing is there". The count is also volatile —
# it read 10 then 3 within minutes as candidate workers came and went.
ls -l /proc/[0-9]*/cwd 2>/dev/null | grep -c 'juniper-cascor/src'

# Ground truth for the dataset store — NOT `ls`
docker volume ls | grep juniper-data-datasets                                    # 4 (1 live)
docker exec juniper-data sh -c 'ls -1 /app/data/datasets/*.meta.json | wc -l'    # 5

# Golden suite — needs ALL THREE flags or it silently skips.
# DO NOT RUN THIS FROM THE PRIMARY CHECKOUT. That tree is 8 behind: it has no
# tests/unit/api/test_lifecycle_reported_split.py and its metrics_post_train.json has no "final"
# key, so it goes GREEN while blind to everything #614 changed. Run it from a fresh worktree
# cut from origin/main (§2), and check the progress line for `s`.
cd <fresh-worktree>/src && \
  python -m pytest tests/integration/api/test_golden_api_snapshots.py -m "" --slow --integration --golden -q
```

## 7. Git state at handoff

- **This session**: juniper-ml worktree `.claude/worktrees/smooth-sauteeing-sunset`, branch
  `worktree-smooth-sauteeing-sunset`, HEAD `c92fec36`, clean apart from this handoff file. It was
  level with `origin/main` when written and drifts behind as peers merge — **re-check, do not
  assume; other sessions are merging into this repo continuously.**
- **cascor primary** (`/home/pcalnon/Development/python/Juniper/juniper-cascor`): clean, **8 commits
  behind `origin/main`**, and **FROZEN** — 3 processes hold `juniper-cascor/src` as cwd, including a
  uvicorn on `:8202` up since 03:58. **Do not pull it.** Its `manager.py` has **zero** `_test_x`
  hits; that is a stale-checkout artifact, not evidence about #614 (memory
  `cascor-primary-frozen-while-any-stack-imports-it`).
- **`git worktree list` returns 22 entries — 21 worktrees plus the primary above. All 22 are
  clean.** Note `git status --porcelain` is blind to ignored files; `.h5` artifacts hide in "clean"
  cascor worktrees, and `git worktree remove` deletes them.
- **Conda env for cascor is `JuniperCascor1`** (torch 2.11.0+cu130). `JuniperCascor` has **no
  interpreter at all** — `/opt/miniforge3/envs/JuniperCascor/bin/python` does not exist. The older
  "torch ImportError" description of this trap is obsolete.

## 8. Source documents

All under `juniper-ml/notes/`:

- `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` — v3, ml#1520, **NOT
  approved**; §3 D-1/D-2, §8 the unrefuted local-fix case, §9 S-1…S-7
- `JUNIPER_2026-08-31_JUNIPER-CASCOR_TEST-PARTITION-SLOT-INVESTIGATION.md` — ml#1523; §3's six-item
  minimum, §5 what the evidence cannot support
- `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` — ml#1465; §5 the
  once-only invariant, §9 the five settled decisions, §9.1 V-1/V-2/V-3, §10 naming
- `JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md` — ml#1465; §7 six decisions, §7.1 F-3a
- `JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md` — the ~150-site scope
- `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_PARTITION-NAMING-VALIDATION.md` — ml#1469; the `eval`→test alias
- `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md` — ml#1477; both gated measurements
- `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — the review procedure

## 9. Validation record

Written per `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`, validated under
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**Sizing**: medium uncertainty × high criticality (a successor acts on it unread) → 2 Lane A +
2 Lane B, escalated to **3 Lane A + 2 Lane B across two iterations**. Escalators applied: this
handoff is written by the session whose work it summarises, so the self-serving-framing lens is
mandatory rather than optional; and iteration 1 surfaced an **inverted owner decision**, a
terminate-blocking class under §4.

**Iteration 1** — 4 agents, distinct entry points. A1: git/`gh` state re-derivation. A2: source
re-read of every cited `file:line`. B1: refute-prompted analysis review. B2: procedure compliance +
self-serving framing.

Findings, all corrected in this revision: cascor#614 **merged mid-review** (§2 had said OPEN); the
cascor primary is **8 behind and FROZEN** (§7 had said "one commit behind, not frozen"); a dangling
`T-1` reference (→ S-2); "10 mutation-verified tests" (→ 1 of 10); "both block Chunk 3" (→ D-1 gates
chunk 3b); "S-1 ANSWERED" (→ partially; 3 items still live); **owner decision 1 inverted** by
half-quoting plan §8 — the sentence *"The owner elected to proceed with it on the record"* had been
dropped; decisions 2–5 and all six logging decisions **absent**; `ecosystem.yaml:32` → `:31`; both
§6 `for` loops **refused** by the isolated-session guard; the `_test_x` grep aimed at the frozen
primary, where it returns 0 and would have read as "#614 did not land"; source documents unnamed;
the predecessor's deferred list written off as closed.

**Iteration 2** — 2 agents. **A3** took an entry point neither A1 nor A2 used: it **executed** every
command in §6 verbatim and re-derived the numbers, rather than reasoning about them. **B3** was
briefed on this project's recorded worst failure mode — *the correction pass introduces the
critical* — and told to assume iteration 1's fixes were defective.

**They were.** B3 found the round-1 fix for the inverted owner decision had **re-inverted it**:
restoring plan §8's dropped sentence attached "proceed with **it**" to a lead-in whose nearest
antecedent was the *local* fix, when that bullet's subject is *"That the ecosystem change is the
right call"*. The handoff then contradicted its own §3 by offering cascor sub-splitting as a live
option — which design `:161` says is *"explicitly not adopted even as a fallback"*. A successor
would have implemented the one option the owner rejected, believing it endorsed. Item 3 is
rewritten.

Also fixed, each verified against the primary source: the −49 % logging figure was attributed to
**cap 16** when cascor#598 measured **cap 4**, with the wrong caveat attached (the real one is that
the after-run did 15 % *more* logging, which the PR body itself calls out); the §6 golden command
pointed at the **frozen primary**, where it goes green while blind to everything #614 changed
(vacuous-pass); the receipts query's `--limit 200` was **already truncating** at #1340, 77 PRs from
the oldest cited — trap 1 reproduced inside its own receipt, now count-asserted; the predecessor's
five inherited deferred items were **pointed at but never carried** (now §1 item 6); §3's new
paraphrases had **dropped five qualifiers** — decision 2's carve-up path, decision 3's override
switch, logging 4's provisionality, logging 5's "still owner's call", and that logging 1 is already
discharged; both ingress line numbers were pre-#614 (`:3533`/`:2195` → `:3631`/`:2271`, and the
shift is non-uniform so it cannot be corrected by arithmetic); trap 4 cited two sources that do not
say what was claimed; the juniper-recurrence path carried a `src/` that does not exist; "22
worktrees" double-counted the primary; the `JuniperCascor` env has no interpreter at all rather than
a torch ImportError; and the `/proc` freeze probe **fails open** on other users' processes.

A3 additionally confirmed by execution what iteration 1 could only read: the three golden gates
really do reveal one at a time (`ss` → `need --slow` → `need --integration` → `need --golden`, exit
0 throughout); `juniper-symbol-loss-check` really does print `files_screened=0 … OK`; the guard
really does refuse `for` loops and `git -C` at this repo; and `test_e2e_train_test_split_ratios`
**passes when run**, which is S-2's claim demonstrated rather than asserted.

Termination: iteration 2 produced **no finding that survives into the document** — every defect
above is corrected in this revision. The remaining known-weak points are stated in place as
warnings (§6's fail-open probes, §7's drift) rather than silently carried.
