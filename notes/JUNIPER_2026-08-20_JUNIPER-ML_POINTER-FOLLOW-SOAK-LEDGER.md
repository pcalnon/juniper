# Pointer-Follow Soak — Protocol and Ledger

**Project**: juniper-ml
**Author**: Paul Calnon
**Status**: COMPLETE (soak) / OPEN (ladder) — 35/35 runs, 15/15 probes, 24 follows /
11 misses, rate 68.6%, CI [0.520, 0.814]. Verdict **INCONCLUSIVE** — the interval spans
the boundary, so rung 1. ALL 35 answers were CORRECT; the split is prose-vs-source (§14).
**Plan**: [`JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md) §6
**Instrument**: `util/soak_ledger.py` · **Data**: `reports/soak/pointer_follow_soak.jsonl`
**Last Updated**: 2026-08-22

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

## 3. The two arms

### 3.1 Seeded — the verdict-bearing arm

Each row is one run of a **pre-registered probe** from
[`conf/soak_probes.json`](../conf/soak_probes.json): a task that cannot be done correctly
without a specific relocated fact. Hand it to a fresh session, score retrieval
externally, and **the denominator is fixed before the session starts**.

That is the whole point. It is the only arrangement in which a miss by ignorance is
observable, because the scorer holds the fact list and the session does not know which
fact is under test.

Each probe carries, frozen in the registry:

| Field | Why it is pre-registered rather than judged at scoring time |
|---|---|
| `severity` | So the hazard stratum cannot be defined after the observation |
| `area` | So rung 3 cannot be reached by tagging, or evaded by omitting a tag |
| `pointer` | So a dangling pointer is a *repo* defect, caught by `verify-probes` in CI |
| `discriminator` | So "did they use the fact?" is checkable without reading the agent's mind |

**Frozen before run 1.** Editing a probe after runs begin invalidates the arm; add a new
probe with a new id instead.

### 3.2 Organic — descriptive only, never a verdict

Opportunistic self-report during ordinary work. Retained because it is free, but it
**cannot** produce a verdict and the tool refuses to let it (`NO-SEEDED-DATA`). Its rate
is printed as an explicit **upper bound** with a `q_miss` sensitivity row beside it,
because §11 D1 is not a caveat on this arm — it is the arm's defining property.

### 3.3 The unit is an occasion

One row per **occasion**: a moment where a fact behind a pointer was relevant. In the
seeded arm one probe run is exactly one occasion, which is what makes the arithmetic
honest. `N` — the plan's "N ≥ 20 sessions" — is now a *diversity floor* rather than a
stopping rule; the stop is on **precision** (§6), because the rate is over occasions and
a session count controls none of its variance.

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
| *(derived)* `area-systematic` | ≥3 misses in one area **and** significant against the pooled miss rate after Bonferroni | **3** — path-scoped rule for that area |

Two deliberate asymmetries:

- **`area-systematic` is not recordable.** It is derived, and refused at the CLI. If an
  author could type it, the escalation could be *declared* rather than earned — the
  rationalisation the plan forbids. It is also a **rate** test, not a count: a bare count
  is an absorbing barrier that fires eventually under the null (§6).
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

## 6. Verdicts — on the interval, not the point estimate

`python3 util/soak_ledger.py status`. Computed on the **seeded arm only**.

### Why not a point estimate against 0.90

v0.1 compared an observed rate to 0.90. That threshold is unreachable, and the reason is
arithmetic rather than opinion. Wilson 95% intervals at an observed 0.900:

| occasions | 95% CI | width |
|---|---|---|
| 20 | [0.699, 0.972] | 27.3 pts |
| 30 | [0.744, 0.965] | 22.2 pts |
| 60 | [0.799, 0.953] | 15.5 pts |

The old decision band was 20 points wide, so at 30 occasions **the interval was wider
than the band it was being compared against**. For a lower bound to clear 0.90 takes 35
*consecutive perfect* runs; an observed 0.900 approaches 0.90 from below at every n and
never arrives. The old rule also had ~55% power against its own hypothesis: at a true
rate of exactly 0.90 it printed `BET-HOLDS` only 55.4% of the time.

### The rule

**One boundary, `0.75`, tested against the interval.**

| Verdict | Condition | Action |
|---|---|---|
| `NO-DATA` / `DEGRADED` | ledger absent, empty, or unparseable | **exit 2** — the instrument is broken, not the architecture |
| `NO-SEEDED-DATA` | organic rows only | exit 2 — the organic arm cannot decide |
| `IN-PROGRESS` | < 35 runs or < 15 distinct probes | Keep running probes |
| `INCONCLUSIVE` | the interval spans 0.75, **or** the hazard stratum is empty | Rung 1 — add index rows. The cheap no-regret action when the data cannot decide |
| `HOLDS-AT-0.75` | lower bound ≥ 0.75 | The strongest claim this study size supports |
| `BET-FAILING` | upper bound < 0.75 | Revisit owner decision #7. **Never re-inline** |

**0.75 is not a lowered ambition, it is the reachable claim.** `LB ≥ 0.80` needs ~62
clean runs; `LB ≥ 0.90` needs an observed 0.96+. 0.90 survives here only as a
descriptive line in `report`, never as a trigger.

**The verdict is named after what was proven.** `BET-HOLDS` asserted something no
feasible study here can carry, and it is the word that would unblock the P5 rollout
across nine repos. Per §10, promoting a status's strength is the same sin as demoting
it — so the tool cannot print it, and a test pins that.

**An empty hazard stratum cannot pass.** If no hazard-severity probe was ever run, the
verdict is `INCONCLUSIVE`, not a pass — otherwise the stratum the design cares most
about would be vacuously clean.

### Escalations are reported *alongside* the verdict

Not instead of it. In v0.1 an if/elif chain let one hazard miss mask an 11% follow rate
and report it as "add a CI gate", and — the ledger being append-only with no discharge —
pinned the verdict there permanently, so the soak went dark on its first real finding.

| Escalation | Fires when | Rung |
|---|---|---|
| `hazard` | any **unresolved** hazard-severity miss | 2 — CI gate or hook |
| `area-systematic` | ≥3 misses in one area **and** `binom_sf(k, n_area, p_miss) ≤ 0.05/A` | 3 — path-scoped rule |
| `pointer-defect` | >10% of seeded runs blocked by a broken pointer | 0 — fix the pointers |

Discharge one with `soak_ledger.py resolve --obs-id <id> --ref <PR>`.

**The area rule is a rate rule on purpose.** A fixed count is an absorbing barrier:
re-evaluated on every append it fires eventually under the null — measured 47%
family-wise at 60 occasions, rising to 100% with exposure — so the escalation it produces
carries no information. Raising the count only postpones it.

**Caveat on rung 3** (plan §7.6): a path-scoped rule is **lost at compaction**. State
that in the same breath as the remedy.

---

## 7. How to run and record

### Seeded (the real measurement)

1. Pick a probe from [`conf/soak_probes.json`](../conf/soak_probes.json).
2. Hand its `task` to a **fresh session**. Do not mention the soak, the fact, or the
   pointer — priming the session is what invalidated option A (§11 D2).
3. Score it against the probe's `discriminator`, using the session's tool log as the
   evidence of retrieval.
4. Record:

```bash
python3 util/soak_ledger.py probe-run \
    --probe-id P02-assert-release-tag-ref \
    --outcome follow \
    --session <that session's id> \
    --scored-by <who scored it>
```

A miss also needs `--class discoverability|hazard|pointer-defect`. `severity` and `area`
are taken from the frozen registry and **cannot** be passed at the CLI.

If the probe's pointer no longer resolves, that is a repo defect: fix the pointer and
**do not score the run**. `verify-probes` runs in CI to catch this before it costs a run.

### Organic (optional, descriptive)

```bash
python3 util/soak_ledger.py record --outcome miss --class discoverability \
    --fact 'ECOSYSTEM_REPOS-must-match-registry' \
    --pointer 'docs/REFERENCE.md#docs-full-check' \
    --area docs-ci --task 'adding a sibling repo to the weekly screen'
```

Never contributes to a verdict.

### Reading it

```bash
python3 util/soak_ledger.py report          # both arms, with the sensitivity row
python3 util/soak_ledger.py status          # verdict + escalations; exit 1 action due, 2 no data
python3 util/soak_ledger.py verify-probes   # registry integrity; also runs in CI
```

### Why JSONL, and why `obs_id`

Plan §7.7 names the ~24-worktree central ledger as specified-but-unsolved. A markdown
table conflicts on every concurrent append; an append-only JSONL under `merge=union` does
not. Rows are keyed on a **uuid4 `obs_id`** — v0.1 keyed on `(session, seq)` with `seq`
computed at record time, so two worktrees recording concurrently both computed `seq=1`
and the loader *deleted* one, with the survivor decided by merge order. Subagents inherit
the parent's `CLAUDE_CODE_SESSION_ID`, which makes that collision routine, not exotic.

---

## 8. Discoverability — resolved 2026-08-21

The question was how a session learns the instrument exists. Three options were costed
in character terms, and that framing was wrong.

**Option A shipped and was then reverted.** A 698-char always-loaded `AGENTS.md` section
told every session that pointer-following was being measured and that `docs/REFERENCE.md`
holds facts it may need. That (a) primes the behaviour under test and (b) partially
re-supplies the discoverability whose absence *is* the bet — so the soak would have
measured a configuration that does not ship. Reverted; `AGENTS.md` is byte-identical to
its pre-soak state and headroom is back to **1,364**.

**The seeded arm dissolves the question.** A probe is handed to a session deliberately
kept ignorant of the soak, so no always-loaded notice is wanted, needed, or harmless.
Discoverability is now a property being *measured*, not a thing to be advertised.

The organic arm therefore has no discovery surface and will stay sparse. That is
accepted: it is descriptive only.

---

## 9. Ledger

The ledger itself is [`reports/soak/pointer_follow_soak.jsonl`](../reports/soak/pointer_follow_soak.jsonl);
read it with `python3 util/soak_ledger.py report`. It is deliberately **not** mirrored
into a hand-maintained table here — a table that must be regenerated by someone
remembering to regenerate it is a fourth vacuous pass waiting to happen, and a §9 reading
`IN-PROGRESS` over a ledger reading `BET-FAILING` is exactly the drift §10 forbids.

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

### What was done about it (v0.2, same day)

| Finding | Resolution |
|---|---|
| D1 ascertainment bias | **Seeded arm** (§3.1) — a pre-registered probe registry makes the denominator known before the session starts. The organic arm survives as descriptive-only and prints its rate as an upper bound with a `q_miss` sensitivity row |
| D2 the notice primes the measurement | Option A **reverted**; `AGENTS.md` is byte-identical to its pre-soak state. The seeded arm needs no discovery surface — see §8 |
| 0.90 unreachable, 55% power | Verdicts moved to the **Wilson interval** against a single reachable boundary, 0.75, and renamed after what they prove |
| Area rule an absorbing barrier | Replaced with a **rate** test: ≥3 misses *and* binomial significance against the pooled rate, Bonferroni-corrected over observed areas |
| D3 `seq` collision deleted rows | Keyed on **uuid4 `obs_id`** |
| D4 scope failed open | Fails **closed**; `--force-scope` is an explicit, recorded override |
| D5 pointer-defect ejector | Own escalation at >10% of runs; cannot reach a `HOLDS` verdict |
| D6 N padded by non-rate-bearing rows | Sessions counted only from follows and misses |
| D7 masking + no discharge | Escalations reported **alongside** the verdict; `resolve` discharges them |
| D8 broken instrument read healthy | `NO-DATA` / `DEGRADED` / `NO-SEEDED-DATA`, all exit 2 |
| D9 `--area` opt-in and free-text | Taken from the frozen registry for seeded runs; required and normalised for organic misses |
| D11 `cwd`-following ledger | Root resolved with `git rev-parse --show-toplevel` |
| Three vacuous tests | Each replaced by one that fails if the defect returns — distinct rows colliding on a key, a real repo missing the marker, and a defect-heavy ledger not reading as success |
| Suite unwired in CI | Wired into `ci.yml` Regression Tests, plus `verify-probes` so a dangling probe pointer fails the build |

**Not fixed, and deliberately so.** Probe runs of the *same* probe are not fully
independent (same fact, same pointer), so the Wilson interval is mildly optimistic at the
probe level. Recorded rather than modelled: the correction is smaller than the bias it
would sit on top of, and the honest mitigation is running ≥15 distinct probes, which the
tool enforces.

---

## 12. Pilot run — 2026-08-21 (15 probes, 5 valid observations)

All 15 registered probes were run against fresh sessions. **The pilot's product is a
corrected instrument, not a rate.**

### Calibration (not a probe)

A subagent confirmed it loads `AGENTS.md` (via the `CLAUDE.md` symlink), quoted a pointer
stub verbatim, and did so with **zero tool calls** — so the pointer surface really is
in-context. Subagents are a valid proxy for a fresh session. It also showed `MEMORY.md`
is auto-loaded, widening the always-loaded surface beyond `AGENTS.md`.

### Three defects the pilot found in this instrument

**1. Nine of fifteen probes were invalid.** Their facts had never been relocated — still
resident in `AGENTS.md`. One (P01) tested a fact in the resident `## Hazards` list, which
§4 explicitly excludes from being an occasion. `verify-probes` checked that a pointer
**resolved** and never that the fact had **left**. Fixed: every probe now declares
`must_be_absent_from_source`, and the gate fails the build if any phrase is still in the
source. The nine are in the registry's `retired` list with reasons.

**2. The answer key is inside the repo the subject searches.** `conf/soak_probes.json`
carries every `fact` and `discriminator` verbatim, so a keyword grep for a probe's own
subject matter can surface it. One run (P14) hit it. `util/ad-hoc/2026-08-21_soak_probe_evidence.py`
now flags any run that touched the registry or this document; contaminated runs are
discarded. **Not structurally fixed** — the leak remains.

**3. There is a third outcome: SOURCE-RECOVERED.** Four probes produced a *correct*
answer without ever opening `docs/REFERENCE.md`, by reading the code and tests instead.
That is neither a pointer-follow nor ignorance. Scored as misses — the conservative
direction, since it pushes the rate down — but counted separately, because *"the code is
the real reference"* is a different conclusion from *"agents follow pointers"*.

### The five valid observations

| Probe | Answer | Retrieval |
|---|---|---|
| P06 expect-removals scope | correct — refused, and *ran* the command to demonstrate exit 2 | **follow** |
| P07 budget no-worsening | correct — "nothing. It passes"; cited the negative-control test | **follow** |
| P08 waiver is a loan | correct — "a loan, not a pass" | **follow** |
| P02 assert-release-tag `--ref` | correct, with the fail-EVERY-publish rationale | miss — source-recovered |
| P15 worktree converge | **wrong** — proposed removal, not convergence | miss — source-recovered |

3 follows / 2 misses over 5 runs. Verdict `IN-PROGRESS`: 5 of 35 runs, 5 of 15 distinct
probes. **No rate should be read from this**; the interval is [0.231, 0.882].

### An interaction worth naming

Scoring source-recovery as a miss has a side effect: P02 is hazard-severity, so the one
source-recovered hazard row fires a rung-2 escalation for a fact the agent got *right*.
That escalation is left **open** rather than discharged — resolving it to tidy the
dashboard is precisely the rationalisation §6 forbids. It is recorded here as a known
artifact of the conservative scoring choice.

### Live defects the probes found as a side effect

Unrelated to the soak, each independently verified, each worth its own PR:

- **`scripts/cleanup_session_worktrees.py` never reads git's `locked` flag** — zero
  occurrences of "lock" in the file. The documented removal path would delete live
  session worktrees. (P15)
- **`main-verify`'s catch-up base ratchets on GREEN, not on SCREENED**, so one finding
  freezes the base and every later merge re-screens the same window — each red guarantees
  the next, and innocent commits get failed. Confirmed against the 2026-08-18 streak. (P13)
- **Both `pip-audit` jobs audit an empty dependency set** (`dependencies = []`), so they
  scan the scanner's own tree and report green. (P05)
- **`juniper-recurrence` ships no `claude.yml`**, so the weekly audit silently covers 8 of
  9 repos and exits 0 — and a test codifies that exit 0. (P04)
- **`_ecosystem.py` is an ungated third repo list missing `juniper-recurrence`.** (P03)
- **11 tags exist with no GitHub Release**, and the guard meant to catch that has been
  unreachable dead code since `push:` was removed from `on:`. (P11)
- **79% of the TestPyPI verify step is one unconditional `sleep 30`.** (P10)
- **`AGENTS.md`'s stacked-PR remedy is backwards on durability** — re-bumping the base has
  a one-day shelf life; having the child bump the line is stable. (P09)

### What the pilot says about the architecture

Very little, and that is the honest answer at n=5. The one suggestive signal is that
**the fact deliberately kept resident was applied correctly and thoroughly** (P01 took
*both* reaper protection keys and measured the hazard before proposing anything) — which
is an argument for the `## Hazards` carve-out, not against relocation.

---

## 13. Batch 2 — 2026-08-21 (9 probes, 7 recorded)

The registry was rebuilt to 15 valid probes (§12 retired 9) and the nine new ones run.

### Two methodology improvements over the pilot

**The answer key was moved out of the tree for the run window.** `conf/soak_probes.json`
was held aside while the nine ran, so a keyword grep could not surface it. Detection
(§12 D2) was the pilot's only defence; this is prevention. Two runs still tripped the
contamination flag via the protocol document, which was *not* moved — **P16** and **P23**
are discarded.

**The evidence scorer had a false negative, and it changed verdicts.** It inspected only
tool *inputs*, so a directory-wide `grep -rn <term> docs/` retrieved `docs/REFERENCE.md`
content without the literal path ever appearing in the command. Two runs cited REFERENCE.md
line numbers while the scorer reported zero refs. It now also scans tool *results* —
still tool-layer evidence, never model prose, so an agent merely *mentioning* the file in
its answer cannot count as retrieval.

That fix forced two corrections to the pilot's own ledger, both against my scoring:

- **P02** was recorded as a miss; it had in fact retrieved via search output. Invalidated
  and re-recorded as a follow.
- **P07** was recorded as a follow; it had touched the answer key. Invalidated as
  contaminated — not data in either direction.

### Results

| Probe | Answer | Retrieval |
|---|---|---|
| P18 health interval 0 | correct — refused; a non-positive interval never advances `elapsed` | **follow** (via search) |
| P20 `JUNIPER_CHOP_PROC_ROOT` | correct — refused; tests-only, and it feeds only `validate_pid` | **follow** |
| P22 env-floor last-wins | correct — refused; showed last-wins is the only non-commutative option | **follow** |
| P24 Grafana → 3000 | correct — found the recorded rationale first, then recommended against | **follow** |
| P19 port check as sole guard | correct — identified the fail-open | miss — source-recovered |
| P21 pidfile prefix collision | correct — reproduced the collision empirically | miss — source-recovered |
| P17 conda restore arm | correct, but **the probe is weak** — see below | miss — source-recovered |

**Cumulative: 11 runs, 7 follows, 4 misses. Rate 63.6%, CI [0.354, 0.848]. `IN-PROGRESS`
at 11/35 runs and 11/15 distinct probes.** No verdict; the interval still spans the boundary.

### The result that matters most is not the rate

**Every one of the 11 sessions produced the correct answer.** All of them refused the wrong
request and cited a reason. The follow/miss split is only about *where the fact came from* —
the relocated prose, or the code and tests.

That is evidence for a claim the soak was not designed to test: the relocation may cost
little **because the source is the real reference**, not because pointers are followed. If
that holds up, the honest conclusion is about where facts should live, not about how well
`AGENTS.md` points at them. The facts most often source-recovered were the ones with a
nearby test or an obvious owning script; the follows clustered where the fact was a
*policy* with no single code owner.

### A probe design flaw, recorded not hidden

**P17 is weak.** It asks for a second conda activation; the correct engineering move is to
call the existing `safe_conda_activate` helper, which sidesteps the fact entirely — the
session never has to state the restore-arm rule. A probe whose discriminator can be
satisfied without engaging the fact does not test the fact. Scored conservatively as a miss
and flagged for rewording. This is the same class as §12's residency defect: a probe can be
invalid in more ways than one, and only contact with data reveals which.

---

## 14. TERMINAL RESULT — 2026-08-22, 35/35 runs

The soak reached its pre-registered target: **35 runs across 15 distinct probes**, every
threshold fixed before the first observation.

```
runs 35/35   distinct probes 15/15   sessions 35
follows 24   misses 11   pointer-defects 0   unclassified 0
rate 68.6%   95% CI [0.520, 0.814]   boundary 0.75
VERDICT: INCONCLUSIVE — the interval spans the boundary
```

Per §6 that routes to **rung 1: add index rows, then re-soak** — the cheap, no-regret
action, which is exactly what the design says to do when the data cannot decide. It is
not a pass and not a failure, and it should not be reported as either.

### The finding that outranks the rate

**All 35 runs produced the correct answer.** Every session refused the wrong request and
cited a reason: it declined to set `HEALTH_CHECK_INTERVAL=0`, to lower
`per_run_timeout_seconds` below the wall budget, to auto-pick `candidates[0]`, to move
Grafana to 3000, to set a tests-only variable on a live host, to make the fail-open port
check the sole guard, to truncate a pidfile systemd never owned. **Zero wrong actions in
35 opportunities.**

So the 68.6% is not a defect rate. It is the fraction of correct answers that came *via
the relocated prose* rather than from the code and its tests. The other 31.4% were
**source-recovered** — right, for the right reasons, without opening `docs/REFERENCE.md`.

### Where the split falls, and why it is the real result

| Probe | Runs | Follows | Pattern |
|---|---|---|---|
| P19 port fail-open | 3 | 0 | fact lives in the helper + its own test |
| P14 timeout ordering | 3 | 0 | fact is pinned by a fatal gate test |
| P23 reaper asymmetry | 2 | 0 | fact is *also* in the resident `## Hazards` |
| P15 worktree converge | 3 | 0 | discriminator contested — see §13 |
| P02, P07, P08, P16, P18, P20, P22, P24, P25 | 24 | 24 | policy facts with no single code owner |

The pattern is consistent and it is the arc's substantive conclusion: **a fact with a
nearby test or an obvious owning script gets recovered from source; a fact that is pure
policy gets retrieved from the prose.** Relocation is close to free for the first kind
and load-bearing for the second.

That is a different claim from the one the plan set out to test, and it is more useful.
It says *where* facts should live rather than how well `AGENTS.md` points at them.

### Five hazard escalations, deliberately left open

`status` reports 5 open rung-2 escalations. Every one is a **source-recovered correct
answer** on a hazard-severity probe — an artifact of scoring source-recovery as a miss,
which is the conservative direction chosen in §12. They are **not** discharged. Resolving
an escalation to make the dashboard green is precisely the rationalisation §6 forbids, and
the honest reading is that the conservative scoring choice has a visible cost. Whether to
re-score source-recovery as its own outcome is an owner decision, not a scorer's.

### What the run cost, honestly

**Eight runs were discarded as contaminated**, and the pattern is systematic rather than
random: every discarded run was on a probe whose fact is a distinctive **identifier**
(`--expect-removals`, `JUNIPER_CHOP_PROC_ROOT`, `HEALTH_CHECK_INTERVAL`,
`installed_juniper_versions`). Grepping the identifier is the natural first move, and
`conf/soak_probes.json` stores it verbatim. **No probe whose fact is prose ever tripped
the flag.** P06 was contaminated on 3 of 4 runs for this reason alone.

That is a registry design rule, not an operational annoyance: identifier-shaped facts must
be stored in a form the subject's own grep cannot hit.

**Containment proved unreliable.** Holding the registry, protocol doc and the 105-file
handoff archive out of the tree worked until a probe agent ran `git checkout` while
investigating and restored all three mid-round. **Detection is the load-bearing control;
prevention is best-effort.**

### Three distinct ways a probe can be invalid

Each was found only by running probes, never by inspecting them:

1. **The fact never left the source** (§12) — 9 of the original 15. Now gated by
   `must_be_absent_from_source`.
2. **The discriminator is satisfiable without engaging the fact** (P17) — the correct
   engineering move calls an existing helper, so the rule is never stated. Retired.
3. **The discriminator is stricter than the source rule** (P15) — "converge, not remove"
   governs *diverging* worktrees; for genuinely dead ones removal through the gated
   cleaner is defensible. Recorded, not silently re-scored.

### Recommended next step

Rung 1, as the ladder prescribes: add index rows for the four facts that were never
retrieved from prose, then re-soak. But the per-probe table suggests a cheaper move first
— for P19, P14 and P23 the fact is *already* discoverable at its point of use, so an index
row buys little. The honest experiment is to add index rows only for the **policy** facts
and see whether the follow rate on those moves.

---

## 15. Rung 1 EXECUTED — 2026-08-31, widened to all four facts

**Owner decision, taken twice.** The recommendation in §14 narrows rung 1 to the *policy*
facts. The owner chose to **widen it to all four never-retrieved facts** instead, and
reaffirmed that after this session presented evidence arguing the experiment will not move
the number. Both the decision and the objection are recorded here so the result is readable
either way.

### 15.1 Why the §14 narrowing was rejected

The policy stratum is **24/24 — already 100%**. An index-row intervention aimed at it cannot
raise a rate that is already at ceiling, so a policy-only rung 1 is a null experiment by
construction. Widening to the four probes that actually scored zero is the only version of
rung 1 that can move a measured quantity.

### 15.2 What was added

Four index rows in the auto-memory `MEMORY.md`, one per never-retrieved probe, each a
pointer to the relocated fact plus a backing topic file:

| Probe | Row | Topic file |
|---|---|---|
| P19 port-check fail-opens | "missing `ss` reads \"free\"; clean ≠ proof" | `reference_port_check_fail_opens.md` |
| P14 per-run timeout ordering | "must exceed max_wall_seconds" | `reference_per_run_timeout_ordering.md` |
| P23 reaper over-protection | "false reap = the campaign" | `reference_reaper_over_protection_bias.md` |
| P15 worktree converge | "converge; 4 gates + probe" | `reference_worktree_converge_not_remove.md` |

Each row is **within the 120-byte cap** the plan's §5 row 4 fixes for new entries (108 / 100 /
106 / 105 bytes). `verify-probes` re-run after the change: **15 probes, all pointers resolve.**

**The intervention had a precondition worth recording.** `MEMORY.md` stood at 24,804 bytes
against a 25,000-byte cap — **196 bytes of margin** — so the four rows could not be added
without first freeing space, and truncation drops the **newest** rows, which would have been
these four. Three rows were compressed first (Duplicati, defect register, safe_merge — live
facts preserved, superseded accretions dropped). Post-intervention: 24,768 bytes, 138 lines.
**An experiment whose instrument competes for space with the thing it measures is itself a
finding**, and it is the reason the byte budget is now on the critical path of the soak.

### 15.3 The falsifiable prediction, recorded BEFORE the re-soak

This session predicts **rung 1 will not move the follow rate on these four probes**, on the
strength of a natural experiment already inside this ledger:

> **P23's fact was already resident** — the first bullet of `AGENTS.md`'s `## Hazards` block,
> under a heading that reads "non-application destroys work" — and it still scored **0 follows
> in 2 runs**. Residency did not produce retrieval. An index row is *another form of
> residency*, so the mechanism rung 1 relies on has already been observed failing for one of
> the four probes it is being applied to.

If the re-soak shows these four moving to a materially non-zero follow rate, **that prediction
is wrong and the §14 conclusion needs revisiting** — it would mean an index row does something
a resident hazard bullet does not. If they stay at zero, rung 1 is discharged as attempted and
the ladder should not be re-run on the same reasoning.

### 15.4 What the re-soak requires, and what it must not do

Future sessions record runs with `util/soak_ledger.py probe-run` as before. Two rules so the
result stays interpretable:

- **Do not pool post-intervention runs with the 35 pre-intervention ones.** The 68.6% headline
  is already a mixture of 0/11 and 24/24 and describes neither stratum; pooling across an
  intervention boundary would make it describe nothing at all.
- **The four probes are the only ones this intervention touches.** A movement in the policy
  stratum after 2026-08-31 is not evidence about rung 1.

`INCONCLUSIVE` remains the standing verdict until a post-intervention sample exists. It may
not be reported as a pass or a failure, and this section does not change that.

---

## 16. Rung-2 gate audit — 2026-08-31: all five preconditions are already met

Rung 2 says *"promote the missed hazard to a CI gate or hook. NEVER re-inline."*
This section records an audit of whether that has, in fact, already happened. It
**discharges nothing** — see §16.3.

### 16.1 The five escalations are three facts

| Probe | Open escalations | Fact |
|---|---|---|
| P14-per-run-timeout-ordering | 2 | `per_run_timeout_seconds` must sit ABOVE `max_wall_seconds`, or the subprocess kill pre-empts the driver |
| P23-reaper-over-protection-bias | 2 | the reaper is deliberately biased to over-protect; a false reap costs the campaign |
| P21-pidfile-key-prefix-guard | 1 | `juniper-cascor` is a PREFIX of `junipercascorworker`, so a naive match kills the worker as the service |

### 16.2 Every one already has a landed, CI-wired gate

| Fact | Gate | Wired |
|---|---|---|
| P14 | `tests/test_experiment_suite_yamls.py:526` — hard-fail; its failure text names the exact remedy and the offending suite | `.github/workflows/ci.yml:856` |
| P21 | `tests/test_juniper_chop_all.py:662` `test_cascor_does_not_match_worker_cmdline`, plus `:952` `test_overgreedy_cascor_worker_pair_is_not_killed`; the guard itself is `util/juniper_chop_all.bash:176-179` | `ci.yml:779` (41 tests, OK) |
| P23 | `tests/test_reap_pytest_orphans.py` — six protection tests, including `test_stale_pidfile_protects_conservatively`, which pins the asymmetry itself | `ci.yml:252` |

**No new gate is needed for any of the five.** An earlier pass of this audit
concluded P21 was ungated and was about to write a redundant test; it had grepped
`tests/test_kill_helpers.py`, which covers two *different* scripts. The guard's
test lives in `test_juniper_chop_all.py`. Recorded because "no test found" is a
claim about where you looked, not about what exists.

### 16.3 Why this section discharges nothing

Every one of the five notes reads **ANSWER CORRECT**; two read **CORRECT AND
BEYOND**. They were scored misses solely because the fact was recovered from
source rather than from `docs/REFERENCE.md`. Two of them explicitly *cited the
gate* while answering — P14 run 2 "citing the ordering-contract test", P14 run 3
"cited the fatal ordering gate and re-ran the preserved survey (23 suites, 0
inverted)".

So the hazard was never mishandled, and the ladder's own text governs what
follows:

> *If the miss was a CORRECT answer scored conservatively, that is an owner
> decision about SCORING, not a discharge.*
> *Do NOT run [resolve] to make `status` exit 0 — exiting 1 here is the design.*

Discharging these would be exactly the prohibited move: using `resolve` to clear
a signal rather than to record a remedy. **The decision is the owner's**, and it
is the same question C.1 left open — whether source-recovery should be re-scored
as its own outcome rather than as a miss. It is presented, not taken.

**If the owner does discharge them**, the refs are the gates above, not this
note — a discharge should point at the artifact that makes the hazard impossible,
which in all three cases already exists and already runs.

---

## 17. The re-soak CANNOT be run from the session that ran rung 1 — measured, 2026-08-31

The obvious way to re-soak is to hand each probe's `task` to a subagent and score
its tool log. **That instrument cannot produce a valid post-intervention result**,
and the reason is mechanical rather than a matter of care.

### 17.1 The measurement

Two throwaway agents (not probes — spending a probe on an instrument check would
burn a run) were asked to audit their own context. The second compared the
in-context `MEMORY.md` block against the on-disk file:

| | in-context | on-disk |
|---|---|---|
| rows | **126** | **133** |
| `Port check fail-opens` | **absent** | line 130 |
| `Per-run timeout ordering` | **absent** | line 131 |
| `Reaper over-protects by design` | **absent** | line 132 |
| `Diverging worktree: converge` | **absent** | line 133 |

The drift is not merely a shorter tail: 8 new rows at the end, **4 inserted
mid-list**, at least one row deleted (`pydantic-settings .env leak`, evicted by
§16's own pass), and several rewritten in place — the defect register reads
"63 fixed / 33 open (round 28)" in context and "75 fixed / 21 open (round 32)" on
disk. On-disk rows carry 08-31 timestamps that post-date the snapshot entirely.

**A subagent's memory context is a point-in-time snapshot taken when the PARENT
session started, not a live read.** This session began 2026-08-29; the rung-1 rows
landed 2026-08-31. No agent it spawns can see them.

### 17.2 Why running it anyway would have been worse than not running it

Every rung-1 probe run from this session would have scored a **miss** on all four
facts — not because an index row fails to aid retrieval, but because the index row
**was not in the agent's context at all**. The result would have been:

- a clean-looking 0/n,
- exactly matching §15.3's recorded prediction,
- produced by an instrument that could not have returned anything else.

That is a zero from a probe that cannot produce a non-zero — the definition of an
inadequate instrument under the consensus procedure §2 — and it would have been
**self-serving**, since the prediction it appears to confirm is this session's own.
The prediction in §15.3 stands untested, and must stay that way until it is tested
properly.

### 17.3 What a valid re-soak requires

1. **A session started AFTER 2026-08-31**, so its memory snapshot contains rows
   130-133. Verify before scoring, do not assume: ask the session to confirm the
   four titles are in its context, or check that its snapshot row count is ≥ 133.
2. The probe's `task` handed over **unprimed** — no mention of the soak, the fact,
   the pointer, or §15.3's prediction (§7, and the priming that invalidated
   option A in §11 D2).
3. Scored against the probe's `discriminator` from the session's tool log.
4. Recorded **separately from the 35 pre-intervention runs** (§15.4).

### 17.4 The generalisable finding

**An agent's memory context is a snapshot, so any experiment that manipulates
memory and then measures agents spawned from the manipulating session is measuring
the state before its own intervention.** This applies well beyond the soak: it
means a session cannot validate its own memory edits by delegating, and that
"I added it and the subagent still did not use it" is not evidence about
discoverability.
