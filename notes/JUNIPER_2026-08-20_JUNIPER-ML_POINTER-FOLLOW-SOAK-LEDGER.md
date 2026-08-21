# Pointer-Follow Soak — Protocol and Ledger

**Project**: juniper-ml
**Author**: Paul Calnon
**Status**: OPEN — instrument built, soak **not yet started** (0 / 20 sessions).
**DO NOT RECORD OBSERVATIONS YET.** Three independent analyses (2026-08-21) found the
instrument cannot currently falsify the bet: the dominant miss class is structurally
unobservable, and every error term in the design points the same way. §6's thresholds
are **withdrawn** pending the redesign. See §11.
**Plan**: [`JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md) §6
**Instrument**: `util/soak_ledger.py` · **Data**: `reports/soak/pointer_follow_soak.jsonl`
**Last Updated**: 2026-08-21

---

## 1. What this measures, and why it is the whole bet

P3 moved ~124,000 characters out of `AGENTS.md` — which every session loads — into
`docs/REFERENCE.md`, which a session reads only if it follows a pointer. The plan is
blunt about what that costs:

> The pointer-follow rate is the one load-bearing quantity nobody can measure in
> advance. — plan §6

and lists it first among the residual risks:

> **The pointer-follow rate remains unmeasured until the soak.** This is the central
> bet. — plan §7.1

If agents follow the pointers, the cut was free. If they do not, the cut traded
context for silent wrongness — the worst possible outcome, because nothing fails
loudly. The soak is the falsification test, and it could not begin because there was
no instrument: no definition of a miss, nowhere to put an observation, no start
marker. This document is the protocol; `util/soak_ledger.py` is the mechanism.

**Everything in §3–§6 is fixed in advance.** That is deliberate and it is the point:
thresholds chosen after seeing the data are not thresholds, they are rationalisations.

---

## 2. Start marker and scope

The soak counts only what happens at or after **`500508b`** (#1196, *"restore the
resident hazard list P3 was required to keep"*) — the first commit at which
`AGENTS.md` is in its final post-P3, hazards-correct shape (43,720 chars).

A session whose `HEAD` does not descend from that commit is **out of scope**. Its
observations are still recorded — they are not lies, they are just about a different
file — but they never count toward the rate. `soak_ledger.py` computes this
automatically via `git merge-base --is-ancestor` and stores it as `in_scope`.

This matters more than it sounds: at the time of writing, **18 of 24 worktrees still
carry a pre-cut `AGENTS.md`**, some as large as 147,840 chars. An observation from one
of those is an observation about the *old* architecture.

---

## 3. The unit of observation

**One row per _occasion_, not per session.**

An **occasion** is a moment in a session where a fact that lives behind a pointer was
*relevant to the work in hand*. A session may present zero occasions, or several.

> **Relevance test** (objective, so it is not a judgement call): would a reviewer
> holding that fact say the session's action should have **changed**, or should have
> been **explicitly justified against it**? If yes, it was an occasion.

Counting one row per session would pad the denominator with sessions that never tested
anything, and the follow rate would look good for free. So `N` — the plan's "N ≥ 20
sessions" — is the number of **distinct sessions that produced at least one occasion**.
Sessions with no occasion are simply not recorded.

---

## 4. Definitions: follow, miss

**FOLLOW** — the session demonstrably retrieved the fact (opened the destination,
grepped it, or otherwise read it) **before** acting.

**MISS** — the fact was relevant, and the session **acted, or presented a conclusion,
without it**.

> **A miss does not require a wrong answer.** If the session reached a correct result
> without consulting the fact, that is *still a miss*: the retrieval mechanism failed
> and correctness was coincidence. Scoring on outcome instead of on retrieval is
> exactly how this measurement would rationalise itself into a pass.

### Not an occasion (excluded, fixed in advance)

| Situation | Why excluded |
|---|---|
| The fact was already in context from earlier in the same session | No retrieval was required; nothing was tested |
| The user supplied the fact | Ditto |
| The fact is in the resident `## Hazards` section of `AGENTS.md` | Never relocated — it is always loaded by design |
| The fact was never relocated (still inline) | Not a pointer-follow event |

---

## 5. Miss classes → the ladder

The plan fixes the escalation ladder in advance (§6). Each recordable class maps onto
exactly one rung, so an observation selects its own remedy and no one has to argue:

| `--class` | Meaning | Remedy (ladder rung) |
|---|---|---|
| `discoverability` | The agent never knew to look | **1** — add an index row |
| `hazard` | The missed fact was hazard-class | **2** — promote to a CI gate or hook |
| `pointer-defect` | The pointer was wrong or stale | *Off-ladder* — fix the pointer, not the architecture |
| *(derived)* `area-systematic` | ≥3 misses sharing one `--area` | **3** — path-scoped rule for that area |

Two deliberate asymmetries:

- **`area-systematic` is not recordable.** It is derived from three observations and
  refused at the CLI. If an author could type it, the escalation could be *declared*
  rather than earned — the rationalisation the plan forbids.
- **`pointer-defect` is excluded from the architectural rate**, and still reported.
  The agent *did* try to follow, so discoverability worked and the target was broken;
  folding it in would blame the architecture for a typo. Reporting it separately means
  a pile of broken pointers can never read as success.

### Never re-inline

> **Never re-inline.** Re-inlining is how the file got here. — plan §6

There is no rung that returns content to `AGENTS.md`. Additions relocate, with a
pointer that keeps an accurate open/closed status.

**Caveat on rung 3** (plan §7.6): a path-scoped rule is **lost at compaction**. If the
ladder reaches rung 3, that limitation must be stated in the same breath as the remedy.

---

## 6. Verdicts — thresholds fixed in advance

> **WITHDRAWN 2026-08-21.** The table below is the *original* proposal and is retained
> only so the record shows what was proposed and why it failed review. Do not implement
> against it. `BET-HOLDS ≥ 0.90` is unreachable at any study size this project will run
> (it needs 35 consecutive perfect occasions for the lower bound to clear 0.90), the
> design has ~55% power against its own hypothesis, and `AREA_SYSTEMATIC_THRESHOLD = 3`
> is an absorbing barrier that fires 47% of the time under the null at 60 occasions.
> **None of that is the main problem** — see §11 D1. Replacement thresholds are pending
> the measurement redesign.

`python3 util/soak_ledger.py status` computes these. Exit 1 means an escalation is due.

| Verdict | Condition | Action |
|---|---|---|
| `ESCALATE-HAZARD` | **any** hazard-class miss | Rung 2, **immediately** |
| `ESCALATE-AREA` | any area with ≥3 misses | Rung 3 |
| `IN-PROGRESS` | N < 20 sessions | Keep soaking |
| `BET-HOLDS` | N ≥ 20 and follow rate ≥ **90%** | The cut was free; close the bet |
| `LADDER-1` | N ≥ 20 and **70%** ≤ rate < 90% | Rung 1, then re-soak |
| `BET-FAILING` | N ≥ 20 and rate < **70%** | Revisit owner decision #7 (Proposal A skills probe) |

Hazard and area escalations fire **regardless of N**. A hazard miss is a live defect,
not a statistic to be accumulated to significance.

> These three numbers (20 / 90% / 70%) are the one part of this protocol the plan did
> not specify. They are proposed here so they exist *before* the data does, and are
> **open to owner ratification** — but they must be settled before the first
> observation is recorded, not after.

---

## 7. How to record

One command, at the moment of observation:

```bash
# the fact was behind a pointer, and the session read it before acting
python3 util/soak_ledger.py record --outcome follow \
    --fact 'publish-gate1-never-no-deps' \
    --pointer 'docs/REFERENCE.md#meta-package-publish-pipeline' \
    --area publish \
    --task 'adding a TestPyPI verify step'

# the fact was relevant and the session acted without it
python3 util/soak_ledger.py record --outcome miss --class discoverability \
    --fact 'ECOSYSTEM_REPOS-must-match-registry' \
    --pointer 'docs/REFERENCE.md#docs-full-check' \
    --area docs-ci \
    --task 'adding a sibling repo to the weekly screen'
```

`--session` defaults to `$CLAUDE_CODE_SESSION_ID`. `--dry-run` prints the row without
writing. Retrospective recording from a transcript is legitimate — pass `--session`
explicitly and note it.

Read the state:

```bash
python3 util/soak_ledger.py report              # human summary
python3 util/soak_ledger.py report --markdown   # regenerates §9 below
python3 util/soak_ledger.py status              # verdict; exit 1 if an escalation is due
```

### Why JSONL and not a markdown table

Plan §7.7 names this as specified-but-unsolved: ~24 concurrent worktrees make any
central ledger a coordination problem. A markdown table conflicts on every concurrent
append. An append-only JSONL under `merge=union` (wired in `.gitattributes`) does not —
union merge on a file whose lines are only ever added is precisely its intended use,
and the `(session, seq)` key means a duplicate produced by union merge is deduped on
read rather than double-counted.

---

## 8. Known gap — the instrument is not yet discoverable

**This is the one thing standing between "instrument exists" and "soak is running",
and it is an owner decision, not an oversight.**

For a session to self-report, it has to know the soak exists. The only always-loaded
surface is `AGENTS.md` — which has **1,364 chars of headroom** under a blocking,
required gate. Putting the instruction in `docs/REFERENCE.md` instead is circular: the
agent would have to follow a pointer to learn that pointer-following is being measured.

The options, with their costs:

| Option | Cost | Consequence |
|---|---|---|
| **A.** Minimal always-loaded line in `AGENTS.md` | **698 chars** measured (the 308 first quoted omitted the command block and the still-a-miss rule) | Live self-reporting — **and a validity cost not known when this table was written; see §11 D2** |
| **B.** Retrospective recording only | 0 chars | No gate cost; lower fidelity, and it only samples sessions someone reviews — **which is §11 D1, the dominant error term** |
| **C.** A hook | 0 chars of `AGENTS.md` | Note plan §7.5: any `.claude/` destination is **outside the docs content-loss screen entirely** |

**Resolved 2026-08-21: option A is LIVE**, not B. `AGENTS.md` carries a
`## Pointer-Follow Soak (active)` section immediately after the hazard list. Budget
gate 44,418 / 45,084, headroom **666** (not the 1,364 this table originally cited).

No ratchet was paid, contrary to this table's original Option A row. The `## Hazards`
carve-out prescribes ratchet-to-pay for a new **hazard**; this is not a hazard, the gate
passes on headroom without a waiver, and `conf/memory_budget.json` is an owner-level
policy surface — tightening it to the new size would fail the next author's addition.
Recorded here because the table said otherwise and **§10 forbids leaving that stale**.

---

## 9. Ledger

Regenerate this section with `python3 util/soak_ledger.py report --markdown`.

| # | Date | Session | Task | Fact needed | Pointer | Outcome | Class |
|---|------|---------|------|-------------|---------|---------|-------|
| _no observations recorded yet_ | | | | | | | |

**Sessions** 0/20 &nbsp;&nbsp; **Occasions** 0 &nbsp;&nbsp; **Follows** 0 &nbsp;&nbsp; **Misses** 0 &nbsp;&nbsp; **Pointer defects** 0 &nbsp;&nbsp; **Follow rate** n/a

**Verdict**: `IN-PROGRESS`

---

## 10. Status may not be demoted

Per the rule learned in P0 (plan §4a) and restated in the segment handoff: **detail may
be demoted; STATUS may not.** When this document is summarised anywhere — an index row,
a handoff, `MEMORY.md` — the summary must carry that the soak is **OPEN and not
started**, not merely that the instrument was built. A row reading "soak instrument
shipped" over a soak that never ran is worse than omission.

---

## 11. Validation findings — 2026-08-21 (thresholds withdrawn)

Three independent agents reviewed this design: a statistical/measurement lens, a
decision-theoretic/cost-asymmetry lens, and an adversarial lens. They were not shown
each other's work. **All three independently identified the same dominant defect.**

### The finding that withdraws the thresholds

**D1 / Flag 4 — ascertainment bias. The denominator is conditioned on the outcome.**
An occasion is recorded only if someone *notices* a relocated fact was relevant. The
dominant failure of a pointer architecture is *the agent never knew the fact existed* —
and that agent cannot notice. So `P(record | follow) ≈ 1` while
`P(record | miss-by-ignorance) ≪ 1`. Those events enter neither numerator nor
denominator; they do not even dilute.

Let `q_m` be the probability a miss is ever logged. Observed rate
`= p / (p + (1−p)·q_m)`:

| true rate | q_m = 1.00 | 0.50 | 0.30 | 0.25 | 0.10 |
|---|---|---|---|---|---|
| 0.70 | 0.700 | 0.824 | 0.886 | **0.903** | 0.959 |
| 0.60 | 0.600 | 0.750 | 0.833 | 0.857 | 0.938 |

**At `q_m` ≈ 0.26, a true 0.70 — a BET-FAILING rate — prints as exactly 0.900,
BET-HOLDS, with no sampling noise required.** This bias is undetectable by `analyse()`,
its sign is known, and it points at the flattering answer. §3's relevance test already
named the required observer — *"would a reviewer **holding that fact**…"* — and this
protocol never staffed the role.

**No threshold change fixes this.** It is larger than the sampling error by an order of
magnitude.

### D2 — the instrument now lives inside the surface it measures

Option A (§8) added an always-loaded section telling every session that pointer-following
is being measured and that `docs/REFERENCE.md` holds facts it may need. That (a) primes
the behaviour under test, and (b) partially re-supplies the discoverability whose absence
*is* the bet. The soak would measure a configuration that does not ship. §8 presented
A/B/C as a pure character-cost trade; it is not — **A costs validity and B maximises D1.
There is no option that avoids both.**

### Why 0.90 was never reachable

Wilson 95% intervals at an observed 0.900:

| occasions | 95% CI | width |
|---|---|---|
| 20 | [0.699, 0.972] | 27.3 pts |
| 30 | [0.744, 0.965] | 22.2 pts |
| 60 | [0.799, 0.953] | 15.5 pts |

The whole LADDER-1 band is 20 points wide; at 30 occasions the interval is **wider than
the decision band**. For a Wilson lower bound to clear 0.90 needs **35 consecutive
perfect occasions**, or 53 with one miss. An observed 0.900 never certifies ≥0.90 at any
n — it approaches from below. With a Jeffreys prior, `P(p ≥ 0.90 | 90/100) = 0.482`.

Three further consequences, each measured:

- **The design cannot confirm its own hypothesis.** At a true rate of exactly 0.90 the
  current rule prints `BET-HOLDS` only **55.4%** of the time — ~55% power against its
  own point alternative.
- **Occasions cluster within sessions.** At ρ=0.3 the design effect is ≈1.75: discount
  logged occasions by ~43%. As ρ→1, `n_eff` collapses to the *session* count.
- **`AREA_SYSTEMATIC_THRESHOLD = 3` is an absorbing barrier.** A fixed absolute count,
  re-evaluated on every append, fires eventually under the null: family-wise false-positive
  rate **47% at 60 occasions** (74.5% with realistic non-uniform area usage), → 100% with
  exposure. Raising the count only postpones it.

### Verdict-flipping defects in the implementation

| ID | Defect | Demonstrated effect |
|---|---|---|
| D5 | `pointer-defect` is a reporter-chosen ejector from the denominator; `--pointer` unvalidated | 20 follows + 20 pointer-defect misses → `BET-HOLDS` at a 50% miss rate |
| D6 | `sessions` counted over all in-scope rows, not rate-bearing ones | 19 pointer-defect sessions + 1 follow → `BET-HOLDS` on n=1 |
| D7 | if/elif precedence + append-only ledger, no discharge | An 11% rate reports as "add a CI gate"; one old hazard miss pins the verdict permanently |
| D4 | Scope gate fails **open** when the marker object is absent | Stale pre-cut worktrees are exactly the ones lacking it |
| D3 | `seq` computed at record time collides under concurrency | Distinct observations **deleted**; survivor depends on merge order. Subagents inherit the parent `CLAUDE_CODE_SESSION_ID` |
| D8 | Absent/empty/corrupt ledger → `IN-PROGRESS`, exit 0; nothing invokes `status` | A destroyed instrument reads healthy |
| D9 | `--area` optional and free-text, tallied only over misses | Rung 3 is opt-in and defeated by spelling; no per-area denominator |
| D11 | Ledger path follows `cwd` | A `cd` into a subdirectory forks a phantom ledger, silently |

Three tests in `tests/test_soak_ledger.py` are themselves **vacuous passes**: the
union-merge test writes the *identical* line three times (pinning the harmless case and
never the harmful one), the scope test hand-writes `in_scope=False` without ever calling
`at_or_after_marker`, and `test_excluded_from_architectural_rate_but_reported` asserts
D5's behaviour is correct.

### What all three agreed on

**Every error term in this design has the same sign.** Nothing in it can make the
measured rate look worse than the truth. That is a confirmation procedure with error
bars, not a falsification test.

The unanimous recommendation is a **seeded arm**: pre-register ~15 tasks whose correct
execution provably requires a specific relocated fact, hand them to fresh sessions, and
score retrieval externally. The denominator is then known by construction, so
`q_m = q_f = 1` and the estimate is unbiased. **Fifteen seeded occasions are worth more
than sixty self-reported ones** — 14/15 alone gives a lower bound of 0.681.

And name the verdict after what was proven: `BET-HOLDS` asserts something no feasible
study here can carry, and — per §10 — promoting the *strength* of a status is the same
sin as demoting it. A verdict that authorises the P5 fleet rollout across nine repos
must not be printable off a 0.75-grade interval.
