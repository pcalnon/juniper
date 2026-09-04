# Soak per-probe handoff — independent-agent consensus validation

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**Date**: 2026-09-04
**Status**: Round 1 complete; round 2 briefed on the corrections
**License**: MIT License

---

## 1. What this is

A consensus validation of
[`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-04_soak-per-probe-characterisation.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-04_soak-per-probe-characterisation.md),
which was written under context pressure and archived (ml#1658) carrying an explicit
**UNVERIFIED** banner. That banner was honest and load-bearing: the document is wrong in ways
that would have cost sessions and turned `main` red.

Run under
[`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).
Sizing per its §3: **high uncertainty** (self-declared unverified, n=3–4 per probe, novel
instrument, universal quantifiers) × **high criticality** (gates a merge; sanctions bypassing a
spend guard) → top-right cell, so **3+ Lane A on distinct entry points, 2+ Lane B on opposing
briefs, ≥2 iterations**.

**This document decides no owner question.** §8 records the open ones unchanged.

## 2. Verdict

**FAIL — do not execute as written.** Three independent reasons, any one sufficient:

1. the immediate task **cannot succeed** at the sample size it specifies;
2. executing it **turns `main`'s required checks red**;
3. its central premise rests on a verdict that is **one observation deep** and computed by a
   method the protocol of record forbids.

## 3. Minimum record (procedure §7)

| | |
|---|---|
| **Instrument** | the ledger's own `wilson()` and `soak_ledger.py report`, validated by reproducing the tool's published figures before use |
| **Could it have produced a different answer?** | Yes for `outcome` (3 values, real per-probe spread). **No** for `arm` (`"seeded"` in all 49), `scored_by` (one rater, all 49), `miss_class` (only `discoverability`/null), and `resolve` (zero records) |
| **Sample size** | 43 valid observations over 15 probes; per-probe n = 2–5 |
| **Agents / entry points** | 5 in round 1 — Lane A: raw JSONL, git+`gh` history, instrument source. Lane B: statistical refutation, executability+amputation. Round 2: 2 agents, briefed on the corrections |
| **Iterations** | round 1 complete; round 2 in flight at time of writing |
| **Unresolved dissent** | §6 |
| **What the evidence cannot support** | §7 |

Four of the five validators reached the CI diagnosis independently, from four different entry
points. That is the convergence the procedure's §2 asks for; agreement among agents sharing an
entry point would not have counted.

## 4. Corrections to the predecessor

Ordered by consequence. Every row was re-derived by the reconciler, not accepted on an agent's
report.

### 4.1 The immediate task cannot succeed at n≈8–10 — CRITICAL

The handoff asks to "drive the ambiguous probes toward n≈8–10 to resolve which stratum each
belongs to". At the observed rates, using the repo's own `wilson()`:

| probe | now | n=8 | n=10 | n=16 | n=26 |
|---|---|---|---|---|---|
| P21 (0.25) | 1/4 | `[0.071, 0.591]` | `[0.057, 0.510]` | **`[0.102, 0.495]` resolves** | `[0.110, 0.421]` |
| P23 (0.33) | 1/3 | `[0.137, 0.694]` | `[0.108, 0.603]` | `[0.142, 0.556]` | `[0.194, 0.538]` — still spans 0.50 |

P21 needs **n≥16**; P23 does not resolve even at **n=26**. Meanwhile P15 and P19 are *already*
resolved (§4.2). The plan spends 22–34 billed sessions to re-confirm what is settled and fail by
arithmetic on what is not.

### 4.2 "Every probe's CI spans 50%" is FALSE — CRITICAL

Under the same Wilson method that produced the quoted pooled `[0.456, 0.736]`:

- **P15 0/4 → `[0.0000, 0.4899]`** — excludes 0.50
- **P19 0/4 → `[0.0000, 0.4899]`** — excludes 0.50

This sentence is the stated justification for "per-probe membership is not established", and it
fails for exactly the two probes carrying the most never-follow data. The same claim in
[`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`](JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md)
§9.2 ("No probe's interval excludes the pooled 65%") is contradicted by the table printed five
lines above it.

### 4.3 Executing the task turns `main` red — CRITICAL

`main` sits at 26/40, `[0.495, 0.779]`, INCONCLUSIVE. The terminal-verdict guard in
`util/soak_run_probe.py` precedes the `--dry-run` branch, so:

| after N more non-follow rows | pooled | Wilson upper | effect |
|---|---|---|---|
| +2 | 26/42 | 0.7500 | none |
| **+3** | **26/43** | **0.7363** | guard arms; `--dry-run` exits 2 empty; Regression Tests fail on 3.12/3.13/3.14 |

The named probes run 0–33% follow, so three non-follows is the *expected* case. **No code change
is required to break `main`** — three rows suffice. Fixed by ml#1690 (§5).

### 4.4 The blocker was misdiagnosed; all three proposed causes are refuted — CRITICAL

The failures are the **pre-existing** `DryRunDoesNotLeakTheTask` tests
(`tests/test_soak_run_probe.py:68`, `:94`), not the new ones.

| handoff's guess | verdict |
|---|---|
| the 3 appended tests | **refuted** — all 3 `RetrievalChannelIgnoresAnswerText` tests pass |
| a black/format issue | **refuted** — Pre-commit green on all three Pythons |
| an unrelated `main` breakage | **refuted** — `main` green at `42d33634` |

`return 2` at `util/soak_run_probe.py:279` is the file's **only** exit-2 path, so attribution is
proven rather than inferred. The trigger is the PR's **data**, not its code: the guard and
`--force` were already on `main`.

Also: `mergeStateStatus` is **BLOCKED**, not BEHIND — so the handoff's remedy ("drive
`update-branch` when BEHIND") would not have fixed it. **Regression Tests 3.12** and **Quality
Gate** also fail and are unlisted. And the stated repro passes on `main` (10 tests OK), so a
literal reader concludes "cannot reproduce".

### 4.5 The BET-FAILING verdict is one observation deep and self-produced — CRITICAL

| | follows/n | Wilson upper | terminal? |
|---|---|---|---|
| as recorded | 26/43 | 0.7363 | **yes** |
| P15 scored `follow` (what the OLD channel returned) | 27/43 | 0.7562 | no |
| P15 dropped | 26/42 | 0.7500 | no |

Margin **0.0137**. The PR's own channel fix is what reclassified P15, and that single
reclassification is the whole difference between INCONCLUSIVE and *terminal*. The fix is correct
— P15's transcript has zero tool calls touching the pointer document — but a verdict one
observation from its own boundary should not be driving a terminal stopping rule, still less be
the premise for bypassing it.

### 4.6 The verdict uses a statistic the protocol forbids — CRITICAL

§15.4 of
[`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md)
states: *"Do not pool post-intervention runs with the 35 pre-intervention ones."* Split as
required:

- **pre-intervention: 24/35 = 68.6%, `[0.520, 0.814]` — NOT terminal**
- post-intervention: 2/8 = 25.0%, far below `TARGET_PROBE_RUNS = 35`

`analyse()` has no era filter, so the instrument structurally cannot honour §15.4 and emitted the
forbidden statistic on request.

### 4.7 Retention moved 20.9 points by relabelling — MAJOR

`RESCORE_OUTCOMES = ("source-recovered",)` — the rescore verb is **one-way** and can only move a
row in the retention-raising direction.

| | follow / source-recovered / miss | retention |
|---|---|---|
| as originally recorded | 26 / 6 / 11 | **74.4%** |
| after 9 rescores | 26 / 15 / 2 | **95.3%** |

95.3% is the figure that converts a failed bet into "relocation is safe". It should not be quoted
without its provenance.

### 4.8 Two retrieval standards are live in one corpus — MAJOR

Follows were scored on two different evidences, in two lexical forms
(`RETRIEVED via search output` ×7, `via-search-output` ×3):

- **8 follows** scored on tool **OUTPUT**
- **18 follows** scored on tool **INPUT**

Apply the current standard (tool inputs only, post-ml#1644) uniformly and the pooled rate is
**18/43 = 41.9%, `[0.284, 0.567]`** — not 60.5%. Per-probe stratum membership is therefore
partly a **scoring choice**, not a latent property being estimated.

### 4.9 `--force` is not sanctioned by the section cited for it — MAJOR

The handoff calls `--force` "expected and sanctioned" per §8.3 of
[`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`](JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md).
§8.3 says: *"The guard is not harmful — it still prevents unattended runaway spend … **Left in
place for now; flagged so it is changed deliberately rather than discovered later.**"* Its
conclusion is *leave it and change it deliberately*. §10.5 of the same document lists the
`--force` question as an **open owner decision**, which the handoff's own "do not decide these"
list omits and then decides.

### 4.10 Not executable as written — MAJOR

- Bare probe ids do not resolve: `--probe-id P19` → `no such probe: P19`. Real ids are full
  slugs (`P19-port-check-fail-opens`); no full id appears in the document. **All three** command
  templates fail.
- `--outcome miss` is rejected without `--class` (`discoverability | hazard | pointer-defect`),
  which the record command omits — one third of its own outcome menu.
- `util/wait_for_checks.py` has **no `--auto`** flag; `--auto` is a `gh pr merge` passthrough
  inside `util/safe_merge.py`.
- Nothing in "Verify first" produces the per-probe f/n table the task works from.
  `soak_next_probe.py --status` reports **post-intervention run counts**, a different quantity in
  a confusable format.
- Worktree `.claude/worktrees/nifty-tinkering-wave` is on branch `worktree-nifty-tinkering-wave`,
  not `feat/soak-bet-failing-and-channel-fix`, which is checked out in no worktree; the local ref
  for that branch was 7 commits behind origin.

### 4.11 Instrument validity — MAJOR

All **15** probes share one pointer document, `docs/REFERENCE.md`, differing only by `#anchor`,
which is stripped before matching. With `hit = doc in blob` a substring test over `json.dumps` of
every tool input, the detector's target is a **per-probe constant**, and any touch of that file
for any reason scores as following the pointer.

**Caveat that bounds this**: the channel only `suggests`; a human supplies `--outcome`. So the
defect biases the scorer's anchor rather than setting the recorded number directly.

## 5. What was shipped

**ml#1690** — `fix(soak): a dry run spends no session, so the stopping rule must not gate it`.
Exempts `--dry-run` from the terminal-verdict guard, extracts `refuses_terminal_verdict()` so the
ordering hazard is testable without a live ledger, and notes the terminal state on stderr instead
of hiding it. Verified against the exact failure condition (ml#1644's ledger installed: 15/15,
`--dry-run` rc=0, where that ledger previously produced `FAILED (failures=2)`), with a negative
control confirming 5 tests fail when the exemption is removed.

Deliberately **not** fixed there: the guard also **fails open** — `st.returncode` is never
checked, so an unreadable ledger yields `verdict=""` and the spend control passes.

## 6. Unresolved dissent

Recorded rather than dropped, per procedure §5.3.

- **"n=10 is worse than n=8"** (Lane B1). Not reproducible at the interval level — n=10 is
  strictly tighter. The claim rests on power discreteness over the sampling distribution, which
  the reconciler did not verify. **Open.**
- **"The rung-1 rows are first to be truncated"** (Lane B2). Mechanism confirmed — the cap is
  silent and drops the newest rows — but the ordering does not follow. Measured: **705 bytes** to
  truncation onset, **4,305 bytes** before those rows are reached. **Immediacy overstated.**
- **Amputation findings** (Lane B2): the tool-*results* half of the scoring rule, the
  contamination screen `util/ad-hoc/2026-08-21_soak_probe_evidence.py` not being invoked by the
  harness, and BET-FAILING's prescribed action ("Revisit owner decision #7. Never re-inline").
  Single-source **leads, not facts** — not re-derived by the reconciler.
- **Reconciler errors, recorded because they cut the same way.** Two of the reconciler's own
  re-derivations were wrong before they were right, and both errors made a validator look wrong:
  keying mutation records on `obs_id` instead of `invalidates`/`rescores` (yielding 49 valid and
  67.3% retention, with a clean-looking report), and matching one of the two lexical forms of the
  search-output marker (yielding 2 instead of 8). **A reducer that silently no-ops still prints a
  plausible report** — validate a reducer by reproducing the tool's published figures before
  trusting its novel ones.

## 7. What this evidence cannot support

- Anything about the **organic arm** — `arm` is `"seeded"` in all 49 records; `organic: runs 0`
  is an unfed instrument, not a measurement.
- **Inter-rater reliability** — `scored_by` is one rater across all 49.
- **`index-recovery` rates** — there is no `rung` field in the ledger or in
  `conf/soak_probes.json`, no detector in code, and no such outcome. The "1 of 4" is transcript
  prose, so "a floor, not an estimate" has no instrument behind it.
- **`pointer_defects = 0`** — `miss_class` has only ever been `discoverability` or null, so that
  counter has never had an input that could make it non-zero.

Separately: `p = 0.0017` reproduces as a **parametric bootstrap**, not the permutation test it is
labelled; a true label-shuffle gives p ≈ 0.0002–0.0006. The conclusion (p ≪ 0.05) survives; the
label does not.

## 8. Open owner decisions — NOT decided here

Carried forward unchanged from the handoff, plus one it omitted:

1. Whether **index-recovery** becomes a scored outcome (registry + ledger change).
2. Whether **BET-FAILING** feeds back into relocation policy.
3. Whether the stopping rule should be re-keyed off the pooled verdict.
4. P06's discriminator under-specifies. Registry-author item.
5. **(omitted by the handoff)** Whether to `--force` past a terminal verdict at all — §10.5 of
   `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` records this as
   owner-facing and open.

Given §4.1, a sixth is now live: **whether the per-probe campaign runs at all**, since it cannot
resolve P21 or P23 at the sample size proposed.

## 9. Reproduction

```bash
git show origin/feat/soak-bet-failing-and-channel-fix:reports/soak/pointer_follow_soak.jsonl > /tmp/pr.jsonl
python3 util/ad-hoc/2026-09-04_soak_handoff_consensus_checks.py /tmp/pr.jsonl
```

Reproduces §4.7 (retention 74.4% → 95.3%), §4.8 (8 vs 18 follows; 41.9% uniform) and §4.6
(pre-intervention 24/35 = 68.6%, not terminal). Mutation records name their target in
`invalidates` / `rescores`, **not** in their own `obs_id`.

**CHANGED**: this file, and `util/ad-hoc/2026-09-04_soak_handoff_consensus_checks.py` (new).
