# Soak per-probe handoff — independent-agent consensus validation

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**Date**: 2026-09-04
**Status**: Round 2 complete on the adjudication lane; it overturned two round-1 calls
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
| **Iterations** | 2. Round 2 was briefed on the corrections, not the original, and changed §4.1, §4.3, §4.6, §4.8 and §6 — **two of its findings ran against the reconciler** |
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

P21 needs **n≥16**; P23 first resolves at **n=31**. Meanwhile P15 and P19 are *already* resolved
(§4.2). The plan spends 22–34 billed sessions to re-confirm what is settled and fail by
arithmetic on what is not.

**Worse: the top of the handoff's own range is the worst point in it.** Wilson's low-side
resolving threshold is `k ≤ 1` at n=8, n=9 **and** n=10, loosening to `k ≤ 2` only at n=11. Runs
9 and 10 therefore add Bernoulli trials against an unchanged cap, and **power falls**:

| true p | n=8 | n=9 | n=10 | n=11 |
|---|---|---|---|---|
| 0.20 | 0.5033 | 0.4362 | 0.3758 | 0.6174 |
| **0.25 (P21 observed)** | **0.3671** | 0.3003 | **0.2440** | 0.4552 |
| 0.333 | 0.1951 | 0.1431 | 0.1040 | 0.2341 |

So within "n≈8–10", **n=8 is the only value that can resolve P21 at all**, and each further
session strictly reduces the chance of an answer until n=11. (n=5–7 are worse still: the
threshold there is `k ≤ 0` and P21 already has k=1, so P(resolve) is exactly **0** — those runs
cannot produce an answer under any outcome.)

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
| +2 | 26/42 | 0.750002742 | none — but **2.7 parts per million** clear of the boundary |
| **+3** | **26/43** | **0.7363** | guard arms; `--dry-run` exits 2 empty; Regression Tests fail on 3.12/3.13/3.14 |

The +2 row is printed to full precision deliberately: at 4 dp it reads `0.7500`, from which a
reader cannot tell which side of the boundary it falls on. It is **not** terminal, by 2.7e-06.

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
| P15 dropped | 26/42 | 0.750002742 | no, by 2.7e-06 |

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

§15.4 carries a **second** rule that is also breached: *"The four probes are the only ones this
intervention touches."* The 8 post-intervention runs are P02, P21×2, P14, P23, P06, P15, P19 —
**4 of 8 are on probes rung 1 never touched**. So the post-intervention sample is not a clean
measurement of the intervention either; neither corpus is a clean read.

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

Follows were scored on two different evidences. Scoped to the 26 valid follows (the marker also
appears on one `miss` and inside one `invalidate` reason, so file-wide grep counts are 10):

- **8 follows** scored on tool **OUTPUT** (`RETRIEVED via search output` / `via-search-output`)
- **18 follows** scored on tool **INPUT** (`opened=` / `N refs`) — a residual, not a verified set

Score all 26 by what the ml#1644 instrument can actually see and the pooled rate is
**18/43 = 41.9%, `[0.284, 0.567]`**.

**But 41.9% is a floor produced by an amputated instrument, not "the standard applied
uniformly."** Corrected in round 2, and the distinction matters. §4 of
[`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md)
defines FOLLOW as *"the session demonstrably retrieved the fact (opened the destination,
**grepped it**, or otherwise read it)"*, and §7 scores *"using **the session's tool log** as the
evidence of retrieval"* — a tool log is inputs **and** results. `util/soak_run_probe.py` parses
only `tool_use` blocks; `grep -rn tool_result` across the three soak scripts returns **zero**. A
directory-scoped grep names `docs/`, not `docs/REFERENCE.md`, so protocol-conformant retrieval is
structurally invisible to it.

The ledger already priced this, in the invalidate row of 2026-08-22: *"the evidence scorer
inspected only tool INPUTS, so a directory-wide grep that returned docs/REFERENCE.md content read
as zero retrieval."*

So ml#1644 cured the false **positive** (reciting a path scored as reading it) and left the false
**negative** (reading via search output) in place. Under the protocol's own standard —
inputs ∪ results — the pooled rate stays **60.5%**. The live range is therefore **41.9% to
60.5%** depending on a standard nobody has ratified, which is the finding: per-probe stratum
membership is partly a **scoring choice**, not a latent property being estimated.

One of the 18 "tool INPUT" follows (P23, `2026-09-04T09:03:46Z`) carries no retrieval marker at
all — its note cites the document in prose, which is the class ml#1644 exists to reject.

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

## 6. Dissent — resolved and unresolved

Recorded rather than dropped, per procedure §5.3. Round 2 resolved three of these, **two against
the reconciler.**

- **"n=10 is worse than n=8"** (Lane B1). **RESOLVED IN THE VALIDATOR'S FAVOUR.** Round 1's
  reconciler tested the wrong quantity — the interval at the observed rate, where n=10 is
  strictly tighter — and recorded the claim Open. At the level the claim was actually about,
  **power over the sampling distribution**, it is true at every rate in range, because the
  resolving threshold `k ≤ 1` is unchanged across n=8, 9, 10. Now folded into §4.1.
- **The tool-*results* half of the scoring rule** (Lane B2). **RESOLVED: it HOLDS**, and it
  falsified the reconciler's framing of §4.8, which is corrected there. Promoted from lead to
  finding.
- **"The rung-1 rows are first to be truncated"** (Lane B2). **Refuted, but the reconciler's
  numbers were stale within the session.** Direction confirmed at
  [`notes/JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md)
  §2a: *"The loss is newest-first, and silent. Truncation keeps the first 200 lines / 25,000
  bytes."* Re-measured after a peer edit landed mid-session: **24,622 bytes / 149 lines**,
  headroom **378 bytes** (not 705), rung-1 rows now at lines **136–139** (not 135–138), **3,600
  trailing bytes** before they are reached. Ten rows die first, so the rejection stands — but the
  file grew 327 bytes *during this review*, and the byte cap binds long before the line cap.
  **A line-number citation with no content anchor does not survive a peer edit**; the row
  positions above will drift again.
- **The other two amputation leads** (Lane B2), spot-checked in round 2 and both holding:
  `util/ad-hoc/2026-08-21_soak_probe_evidence.py` is genuinely uninvoked by any script (every
  other hit is prose), and BET-FAILING's prescribed action really is *"Revisit owner decision #7.
  Never re-inline"* — neither quoted nor acted on anywhere in this arc.
- **Reconciler errors, recorded because they cut the same way.** Two of the reconciler's own
  re-derivations were wrong before they were right, and both errors made a validator look wrong:
  keying mutation records on `obs_id` instead of `invalidates`/`rescores` (yielding 49 valid and
  67.3% retention, with a clean-looking report), and matching one of the two lexical forms of the
  search-output marker (yielding 2 instead of 8). **A reducer that silently no-ops still prints a
  plausible report** — validate a reducer by reproducing the tool's published figures before
  trusting its novel ones.

  Sharpened in round 2: the naive `obs_id` reducer does **not** flip the verdict (27/49 → upper
  0.6815, still BET-FAILING). What it silently destroys is the **95.3% retention headline** —
  the one figure that reframes a failed bet as a safe relocation. A broken reducer that leaves
  the alarming number intact and quietly rewrites the reassuring one is the harder failure to
  notice.

- **And two more, found by round 2 in the round-1 corrections themselves** — §4.8's framing
  (above) and a `0.7500` that could not decide its own boundary (§4.3). Both were introduced by
  the fix pass, which is precisely what procedure §4 predicts: *"the fix pass is the least
  trustworthy part of any document."* Round 2 paid for itself on this row alone.

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
