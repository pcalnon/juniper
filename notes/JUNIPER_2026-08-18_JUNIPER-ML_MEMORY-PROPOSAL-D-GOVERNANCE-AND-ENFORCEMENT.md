# Memory Proposal D — Govern the Write Path

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose

This is **Proposal D** of four independent, competing proposals for the shared-session-memory
size problem. It is a design-of-record draft, not a ratified plan; it deliberately argues one
thesis hard so the owner can compare it against three others that argue different ones.

**Status**: DRAFT — competing proposal, not ratified. Recommend an independent
cross-validation pass (§13) before any part of it is treated as decided.

Fact bases, which this document does not re-derive and must not contradict:

- [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md)
  — sizes, growth curve, where the bytes are, existing gates. Cited below as **BASE §n**.
- [Claude Code memory mechanisms](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md)
  — verified against official docs and the shipped 2.1.235 binary. Cited below as **MECH §n**.

Every mechanism claim in this document is grounded in MECH. Where MECH marks a fact
UNVERIFIED and this design depends on it, §12 says so explicitly and states what breaks if
the fact goes the other way.

---

## Table of contents

- [§1 The thesis](#1-the-thesis)
- [§2 Scope and non-goals](#2-scope-and-non-goals)
- [§3 The evidence](#3-the-evidence)
- [§4 The design](#4-the-design)
  - [D1 — The budget gate](#d1--the-budget-gate)
  - [D2 — The ratchet](#d2--the-ratchet)
  - [D3 — The waiver](#d3--the-waiver)
  - [D4 — Admission and routing](#d4--admission-and-routing)
  - [D5 — Concurrent write-path discipline](#d5--concurrent-write-path-discipline)
  - [D6 — Hooks](#d6--hooks)
  - [D7 — Periodic eviction](#d7--periodic-eviction)
- [§5 Confronting the objections](#5-confronting-the-objections)
- [§6 Budget arithmetic and growth projection](#6-budget-arithmetic-and-growth-projection)
- [§7 The MEMORY.md problem](#7-the-memorymd-problem)
- [§8 Migration path](#8-migration-path)
- [§9 What this proposal does NOT solve](#9-what-this-proposal-does-not-solve)
- [§10 Dependencies on companion proposals](#10-dependencies-on-companion-proposals)
- [§11 Owner decisions and open questions](#11-owner-decisions-and-open-questions)
- [§12 Facts this design needs that MECH leaves unverified](#12-facts-this-design-needs-that-mech-leaves-unverified)
- [§13 Verification strategy](#13-verification-strategy)
- [Appendix A — measurement commands](#appendix-a--measurement-commands)

---

## 1. The thesis

> **The other three proposals treat the symptom. The disease is an ungoverned write path.**

`AGENTS.md` grew ~20× in six months (BASE §2) **while under four active CI gates** (BASE §6).
Every one of those four gates enforces structure or currency. Not one enforces size, rate, or
admission. Each is satisfied by a commit that appends five hundred lines:

| Gate | Enforces | Satisfied by a +500-line append? |
|------|----------|----------------------------------|
| [`tests/test_agents_md_version_drift.py`](../tests/test_agents_md_version_drift.py) | header `**Version**` == `pyproject` | yes |
| [`tests/test_agents_md_header_schema.py`](../tests/test_agents_md_header_schema.py) | six header fields, ISO date | yes |
| [`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) | every top-level dir appears in the tree | yes — an append can only *help* |
| [`.github/workflows/agents-md-touch-up.yml`](../.github/workflows/agents-md-touch-up.yml) | `**Last Updated**` bumped | yes |

The file is *thoroughly* guarded — against everything except getting bigger.

Two consequences follow, and they are the whole proposal:

1. **A one-time reorganisation is undone.** At the measured trailing-30-day growth rate of
   **+92,796 bytes / 30 days** (§3.2), a cleanup to the ~34 KB genre-A residue (BASE §8) is
   fully reversed in **44 days**. Whatever Proposals A/B/C achieve, without a rate control it
   is a six-week reprieve.
2. **A ratchet is the only thing that makes a cleanup permanent.** Conversely, governance is
   the *only* one of the four proposals whose value compounds rather than decays.

The honest corollary, stated up front rather than buried: **governance alone bends the curve;
it does not reverse it.** Proposal D freezes and slows. Proposals A/B/C cut. The pairing is
what wins, and §10 names exactly which parts of this design require a companion.

---

## 2. Scope and non-goals

### In scope

- A **rate budget** and a **level budget** on the resident memory surface, enforced in CI in
  the idiom of this repo's existing `tests/test_agents_md_*.py` drift gates.
- A **ratchet** that cannot loosen silently.
- An **admission / routing decision procedure** an agent can execute correctly unattended.
- **Write-path discipline for concurrent sessions** — the stated root cause.
- **Hook conversion** for the small set of directives that can be enforced deterministically.
- **Periodic eviction**: cadence plus a measurable staleness signal.
- **`MEMORY.md`**, which lives outside the repo and is at ~80 % of a *hard, silent* limit
  (MECH §2). This proposal is the natural home for it and treats it as a first-class problem
  (§7), not an appendix.

### Non-goals

- **Rewriting `AGENTS.md`.** This proposal changes no prose in the resident file except where
  a hook or gate retires a directive (D6). The cutting is a companion proposal's work.
- **Reorganising `docs/`.** The destinations are named; their internal design is not mine.
- **`@path` imports.** MECH §3 is unambiguous: imports load at launch and save zero tokens.
  Nothing here rests on them.
- **Silencing the per-file CLI warning.** MECH §1 consequence 1: the check is per-file, so
  splitting one file into several sub-40 K files silences the warning and saves nothing.
  Every threshold in this document is a *token-cost* budget, never a warning-suppression one.
- **Fleet authoring behaviour.** The Cursor GitHub App (integration id 1210556,
  [flood analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md):33)
  is configured on a dashboard with no in-repo config. This proposal can reject its output at
  CI; it cannot change how it writes.

---

## 3. The evidence

BASE and MECH establish the sizes and the mechanisms. This section adds four measurements
taken for this proposal, each reproducible from [Appendix A](#appendix-a--measurement-commands),
at `main` = `e209b74`, clean tree.

### 3.1 The file has essentially never been cut

First-parent (main-line) accounting of every merge that touched `AGENTS.md`:

| Month | Main-line commits | Grew | Shrank | Net bytes |
|-------|------------------:|-----:|-------:|----------:|
| 2026-02 | 1 | 1 | 0 | +3,028 |
| 2026-03 | 7 | 7 | 0 | +1,607 |
| 2026-04 | 6 | 5 | 0 | +13,538 |
| 2026-05 | 23 | 21 | 0 | +14,564 |
| 2026-06 | 42 | 34 | 2 | +25,663 |
| 2026-07 | 86 | 71 | 12 | +55,796 |
| 2026-08 (to 08-18) | 35 | 33 | **0** | +50,430 |
| **Total** | **200** | **172** | **14** | **+164,626** |

- **172 merges grew the file. 14 shrank it.** A 12:1 event ratio.
- The **fourteen** shrinking merges removed **2,628 bytes between them**. The largest single
  reduction ever applied to this file is **−393 bytes**.
- The mean growing merge is **+972 bytes**; p90 **+2,091**; max **+13,835**.
- **August 2026: 35 merges, 33 grew, zero shrank.**

Reduction has never once been a first-class activity on this file. That is not a failure of
diligence — it is what an unpriced resource looks like. Nothing ever made anyone choose.

### 3.2 The rate is accelerating, and it is the decisive number

Trailing-30-day net growth of `AGENTS.md`, sampled fortnightly:

| Window ending | 30-day net bytes | |
|---------------|-----------------:|---|
| 2026-03-31 | +1,607 | pre-flood |
| 2026-04-14 | +13,522 | pre-flood |
| 2026-04-28 | +13,538 | pre-flood |
| 2026-05-12 | +2,261 | pre-flood |
| 2026-05-26 | +14,580 | pre-flood |
| 2026-06-09 | +12,672 | pre-flood |
| 2026-06-23 | +2,553 | pre-flood |
| 2026-07-07 | +28,013 | |
| 2026-07-21 | +38,781 | |
| 2026-08-04 | +54,071 | |
| **2026-08-18** | **+92,796** | |

Three readings, all load-bearing:

1. **58× in five months** (+1,607 → +92,796). BASE §2's "growth rate is growing" is not a
   qualitative impression; it is a 58× multiplier.
2. **The last four weeks alone nearly doubled the rate** (+54,071 → +92,796).
3. **The current 30-day net is 55 % of the entire file.** More than half of today's
   `AGENTS.md` did not exist a month ago.

Reading 3 is what kills the reorganisation-only strategy. Cut to 34,263 bytes (BASE §8) and,
at +92,796/30 days, you are back at 127,059 in a month and at today's 170,137 in **44 days**.

Pre-flood, this repo sustained a very different rate. Over the seven windows ending
2026-03-31 through 2026-06-23 the net readings sort to 1,607 / 2,261 / 2,553 / **12,672** /
13,522 / 13,538 / 14,580 — **median 12,672, maximum 14,580**. That measured historical
maximum is where §6.2's terminal rate budget comes from. It is not a guess.

### 3.3 Mandatory language is overwhelmingly *not* agent instruction

BASE §8 reports 164 lines carrying mandatory language and shows by sampling that most of it
describes utility internals rather than agent behaviour. Locating those lines by section:

| Lines with mandatory language | Section |
|------------------------------:|---------|
| 87 | `## Key Files` |
| 16 | `## CI/CD Pipelines` |
| 5 | `## Thread Handoff` |
| 4 | `## Shared Service-Core Contracts` |
| 4 | `## Repository Structure` |
| 3 | `## Conventions` |
| 2 | `## Publishing` |
| 2 | `## Worktree Procedures` |
| 1 | `## Pull Request Conventions` |
| **124** | **total** |

**107 of 124 — 86 % — sit inside the three genre-B sections.** Only seventeen lines in the
whole file are mandatory language attached to a genre-A agent behaviour, and of those, four
are section headings or restatements.

> *Counting note.* My regex is `\b(must|mandatory|never|prohibited)\b`, case-insensitive,
> counting **lines**: 124 lines, 144 occurrences. BASE §8 reports 164 under a regex it does
> not publish. The difference is regex breadth, not disagreement about the file. Nothing in
> this proposal turns on which figure is used; where a total is needed I cite BASE's 164.

This matters directly for D6. The popular framing — "turn the MUSTs into hooks, and the file
shrinks" — is **mostly false**, and the measurement is how we know. The hook-able set is
small (D6 sizes it at ~2,450 bytes). Hooks are worth doing for *correctness*. They are not a
size strategy.

### 3.4 `AGENTS.md` is the fleet's single hottest same-file cluster

From the flood analysis, over a 135-merge window
([`:36-37`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md)):
`AGENTS.md` **54** PRs, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` **53**, the release-train
runbook **34**, `docs/REFERENCE.md` **15**. `AGENTS.md` is number one.

And the same document records what that contention costs (`:450-451`):

> Docs (`AGENTS.md`/`REFERENCE.md`/cheatsheet) have **only** markdownlint + dangling-anchor
> check → prose/section deletions have **no** gate.

...and what happened (`:52`, `:229`): a docs merge took the branch side across
AGENTS.md/REFERENCE.md/cheatsheet, deleting sibling sections merged hours earlier — exemplars
#801, #803, adjudicated **NOT PREVENTED**, "prose deletion is invisible to doc-links → green".

That gap is now partly closed: `juniper-docs-additions-check` shipped, and as of `e209b74`
(#1166, 2026-08-18) the per-PR `Sequence Safety` screen is a **required** status check on all
nine repos. Proposal D builds directly on that screen — §5.4 shows the two form a vise.

---

## 4. The design

Seven elements. Each gets an honest four-part analysis. Where an element is weak I say so in
its own Weaknesses paragraph rather than in a footnote.

Three new artifacts carry the whole scheme:

| Artifact | Role | Modelled on |
|----------|------|-------------|
| `conf/memory_budget.toml` | the declared budgets — governed targets, level ceilings, rate ceilings, section allocations | `conf/` already exists (`AGENTS.md:180-376` tree), so no new top-level dir and no `test_agents_md_tree_drift.py` impact |
| `util/memory_budget_check.py` | the checker: OK / WARN / FAIL rows, `--json`, `--strict`, exit 0/1/2 | [`util/agent_suite_doctor.py:13-14`](../util/agent_suite_doctor.py) |
| `tests/test_memory_budget_check.py` | **the** gate — `util/` is outside every pre-commit Python hook's scope, so a unittest is the only gate | the stated convention for `util/env_floor_drift_check.py`, `util/release_train/archive_guard.py`, and every sibling |

---

### D1 — The budget gate

**Two axes, because one is not enough.**

| Axis | Metric | What it controls | Why it must exist |
|------|--------|------------------|-------------------|
| **RATE** | net bytes added to a governed file over a rolling 30 days, measured on `main` | the disease | satisfiable **today**, with no destination and no cleanup: add less, or offset |
| **LEVEL** | absolute bytes of a governed file | the terminal target | makes a cleanup *stick*; without it the rate axis alone permits indefinite slow growth |

The rate axis ships and blocks first. This is the crux of the design and the answer to the
central objection (§5.1): a level budget is unsatisfiable until somewhere else exists to put
the bytes, whereas a rate budget is satisfiable on day one by *any* author, in the PR they
are already writing.

#### What it measures, exactly

- **Bytes, UTF-8, not lines.** Lines are trivially gamed — this file already averages 152.6
  bytes/line, and August added +190 net lines for +49,452 bytes (260 bytes per net line). A
  line budget is satisfied by writing longer lines, which is the *worse* outcome. MECH §9.1
  says optimise for tokens; bytes are the cheapest dependency-free proxy. At the fact base's
  implied ratio (BASE §1: 204,890 chars ≈ 51 k tokens ⇒ 4.017 chars/token) a byte budget maps
  to tokens at ≈4:1 for this corpus.
- **Bytes vs characters — pick one and say which.** `AGENTS.md` is 170,137 **bytes** and
  168,317 **characters** (1.08 % apart; 981 non-ASCII characters). MECH §1's CLI warning
  measures `content.length`, i.e. characters; MECH §2's `MEMORY.md` limit is stated in
  **KB**, i.e. bytes. The gate therefore measures **bytes for `MEMORY.md`** and **characters
  for the CLAUDE.md family**, and `conf/memory_budget.toml` names the unit per target. A gate
  that conflates them is wrong by 1–2 %, which is small — and is precisely the kind of quiet
  wrongness that makes a number un-trustworthy later.
- **Governed targets are an explicit list**, never a glob. Today: `AGENTS.md`. Later,
  optionally, the eight sibling repos' `AGENTS.md` (BASE §7).
- **Per-section allocation is reported, not gated** — except for one declared **group**
  ceiling over `## Repository Structure` + `## Key Files` + `## CI/CD Pipelines`, which is
  where 80.9 % of the bytes live.

#### The failure message

The message is the product. It must teach the routing decision, not merely deny:

```text
FAIL  AGENTS.md  rate budget
  This PR adds +1,842 bytes to AGENTS.md.
  30-day net on main would become +94,638 (budget: +30,000).
  Top contributors in the window: #1154 +13,835, #1143 +4,116, #1140 +3,908.

  AGENTS.md is a RESIDENT file: every byte is loaded into every session of every
  agent, whether or not it touches this subject. Before adding, apply the
  cross-task test (docs/REFERENCE.md, Memory Budget Governance):

    "Would omitting this cause a mistake in a session that is NOT working on
     this component?"

  If NO, this content is genre B and belongs elsewhere:
    component contract / regression lore -> docs/REFERENCE.md + the pinning test's docstring
    multi-step procedure                 -> .claude/skills/<name>/SKILL.md
    only matters for certain paths       -> .claude/rules/<name>.md with `paths:`
    war story / post-mortem              -> notes/ (naming convention doc)
    not yet triaged, session ending      -> notes/memory-inbox/<UTC>_<slug>.md   <-- always valid

  If YES, it is resident content and must displace something: remove an equal
  number of bytes in this PR, or wait for the rolling window to clear.

  Emergency only: Allow-Budget-Overrun: AGENTS.md   (see D3 -- this is a LOAN,
  it blocks the next author until repaid, and it is reported in the monthly ledger.)
```

Note the last routing line. **There is always a valid destination** — the inbox accepts
anything, unconditionally, with no review. A gate whose failure message can end in "you have
nowhere to put this" is a gate that will be disabled; this one structurally cannot.

#### Where it runs

A standalone `memory-budget` job in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml),
following the `release-train-archive-guard` shape (`ci.yml:720-780`) exactly:

- `if: github.event_name == 'pull_request' || github.event_name == 'merge_group'`.
- `merge_group` short-circuits to a green notice **before any checkout** — a queued merge
  commit has no PR base to diff (`ci.yml:735-740`).
- `permissions: contents: read`. `fetch-depth: 0` (the rolling window needs 30 days of
  history; the `sequence-safety` job already does this at `ci.yml:812-815`).
- **Never path-filtered.** A PR that does not touch a governed file reports green with a
  `SKIP` notice. A required context that never *reports* is never *satisfied* — the
  `[skip ci]` orphan class that left cascor#515 permanently BLOCKED with every check at
  "expected" (`agents-md-touch-up.yml:26-33`), and the pre-flight lesson recorded in `e209b74`:
  *"a required context that never reports is never satisfied."*
- **Absent from the Quality Gate `needs:`** (`ci.yml:1305`), for the reason spelled out for
  `sequence-safety` at `ci.yml:787-794`: the gate is `if: always()` and treats any non-success
  need as fatal, so folding in a PR-only job fails every push to main. Promotion to required
  happens **in the branch ruleset**, never via the Quality-Gate `needs:`.

**Analysis**

**Strengths.**
- The rate axis is satisfiable on day one by every author with no prerequisite whatsoever.
  It is the only element here that has zero dependency on a companion proposal.
- It prices a resource that has been free for six months. §3.1 shows 172:14 grow:shrink — the
  gate makes reduction a thing anyone ever has a reason to do.
- Modelled line-for-line on live, exercised repo machinery: the archive-guard job shape, the
  doctor's OK/WARN/FAIL contract, the `util/`-needs-a-unittest convention. Nothing is novel
  infrastructure, which is why it is cheap to build and cheap to revert.
- Quantified effect: capping the 30-day net at the pre-flood maximum of 15,000 bytes is a
  **6.2× reduction** against the measured 92,796.

**Weaknesses.**
- **Bytes are a proxy for tokens, and a mediocre one.** A table of short cells and a dense
  paragraph of the same byte count do not cost the same attention. There is no cheap fix: a
  real tokenizer is a dependency that drifts with the model, and MECH §8.6 records that *no
  published Anthropic benchmark* measures adherence against memory size, so there is no
  empirical curve to calibrate against either. The budget is a discipline, not a measurement
  of harm.
- **The rate axis is order-dependent and therefore unfair.** Three PRs of +8,000 land; the
  fourth, adding +500, is the one that fails. It is a rate limiter, and rate limiters always
  do this.
- **The level axis is inert until a companion cuts the file.** Setting `max_bytes` at today's
  size plus slack constrains nothing on day one. Honest: on day one the level axis is a
  placeholder that exists so the ratchet has something to hold.
- **It governs one repo.** BASE §7 shows canopy at 94,373 and cascor at 70,118 on the same
  trajectory. Portability is designed in (the checker self-locates like
  `test_agents_md_header_schema.py:40-45`) but a fleet rollout is real work not costed here.

**Risks.**
- *Concrete scenario.* A session at 23:40 UTC finishes a genuine post-mortem, tries to append
  1.8 KB, is refused by a rate budget it did not know existed, and — under time pressure —
  pads the change into `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` instead, which is
  **ungoverned** and is the fleet's *second*-hottest cluster at 53 PRs (§3.4). The byte
  problem is not solved; it is relocated to a file nobody is watching, and the resident file's
  numbers look great.
- The gate becomes the thing that is worked around rather than the thing that changes
  behaviour, and the metric decouples from the goal (Goodhart, in its most ordinary form).

**Guardrails.**
- **Governed-target list is the mitigation, and it must grow with the leak.** The daily alarm
  (D3) reports 30-day net growth for `AGENTS.md`, `docs/REFERENCE.md`, and
  `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` **side by side**, gating only the first. If the
  cheatsheet's rate steps up as the resident file's steps down, displacement is visible in one
  table on day one. (Note this is *reporting*, not prevention: `docs/**` is read on demand, so
  its growth is not a token cost — the report exists to distinguish healthy routing from
  gaming, and only a human can tell those apart.)
- `tests/test_memory_budget_check.py::test_target_list_is_explicit_and_nonempty` — an empty or
  glob-derived target list is a **FAIL**, never a pass (§5.3).
- `tests/test_memory_budget_workflow.py` asserts the job is absent from the Quality Gate
  `needs:` and present on `pull_request` + `merge_group` — modelled on the existing
  [`tests/test_archive_guard_workflow.py`](../tests/test_archive_guard_workflow.py) and
  [`tests/test_ci_sequence_safety_hatch.py`](../tests/test_ci_sequence_safety_hatch.py).

---

### D2 — The ratchet

A budget that can be raised in the same commit that breaches it is not a budget.

**Three rules, all mechanical:**

1. **Monotone ceilings.** For every governed target, the value in `conf/memory_budget.toml` at
   `HEAD` must be `<=` the value at the PR's merge base. A raise fails unless waived by an
   `Allow-Budget-Raise:` trailer (D3). This is a diff-of-a-config-file check — the same shape
   as `test_agents_md_version_drift.py` comparing two declared values.
2. **Bounded headroom (anti-banking).** `max_bytes − actual_bytes <= LEVEL_SLACK` (proposed
   8,000). Its purpose is not to constrain growth — the rate axis does that — but to force the
   ceiling to *follow a cleanup down*. Without it, a companion proposal cuts the file to
   34 KB, the ceiling stays at 175 KB, and the level axis is dead for the next 140 KB of
   regrowth. With it, the cleanup PR **cannot merge** without lowering its own ceiling in the
   same commit.
3. **Scheduled rate step-down.** `max_net_bytes_30d` declines on a published schedule (§6.2).
   Each step requires the previous step to have held for 30 days with `<= 1` waiver. The step
   is applied by a human-or-agent-authored PR, never by a bot.

**Why no bot.** Auto-tightening the ceiling on merge is the obvious design and it is
**unavailable here**. A runner's local `git commit` is unsigned; `required_signatures` has
applied fleet-wide since 2026-08-12; an unsigned commit anywhere in a branch's history blocks
the merge and squash does not rescue it. That is exactly what removed the auto-bump from
`agents-md-touch-up.yml` (`:21-35`, juniper-ml#1099). The only signed automation path is the
GitHub API (`createCommitOnBranch`), which the repo has in
[`util/open_signed_pr.py`](../util/open_signed_pr.py) — and D5 uses it for curation. For the
ratchet itself, rule 2 makes a bot unnecessary: the cleanup PR *must* carry the tightening, so
the tightening is authored by whoever did the cleanup, and it is signed because they signed it.

**Analysis**

**Strengths.**
- Makes any reduction **permanent by construction**. This is the single property no other
  proposal can supply, and it is what converts a companion's one-time win into a floor.
- Rule 2 turns "remember to tighten the budget after cleanup" — a step every human forgets —
  into a merge blocker on the very PR that would forget it.
- Needs no bot, no token, no scheduled write, and therefore has no signing exposure.

**Weaknesses.**
- **A ratchet is only as good as its floor, and the floor is a judgement call.** Nothing in
  MECH tells us what `AGENTS.md` *should* weigh. MECH §5's "under 200 lines" is documentation
  guidance, and MECH §8.6 confirms no benchmark backs it. §6's 30,000-byte terminal target
  converges from two independent routes, but it remains a defensible guess.
- **Ratchets are brittle under legitimate regime change.** If the repo genuinely acquires a
  large new subsystem that every session must know about, the correct response is a *higher*
  ceiling, and the mechanism's whole design is to resist that. The escape is a waiver, i.e.
  the mechanism's own weakest point.
- Rule 3's cadence is arbitrary. 30 days is chosen to match the rate window; nothing measured
  says it is right.

**Risks.**
- *Concrete scenario.* Cleanup lands, file drops to 100 KB, ceiling correctly ratchets to
  108 KB. Two weeks later a revert is needed for an unrelated reason. The revert restores the
  file to 170 KB — and now **fails its own ceiling**, blocking a revert during an incident.
  Ratchets and reverts are natural enemies.
- Slower and nastier: `LEVEL_SLACK` is quietly raised from 8,000 to 40,000 in an unrelated PR.
  The ratchet still "passes" every check while having lost all its teeth.

**Guardrails.**
- **Revert lane.** `Allow-Budget-Overrun:` waives the level and rate checks but *not* rule 1,
  so a revert lands immediately without loosening anything permanent, and the ledger records
  it. This is the one waiver use the design considers unambiguously correct.
- `LEVEL_SLACK` and the rate schedule live in `conf/memory_budget.toml` and are covered by
  rule 1's monotonicity check — **raising the slack is itself a ratchet violation.** Pinned by
  `test_memory_budget_check.py::test_slack_increase_is_a_ratchet_violation`.
- `test_memory_budget_check.py::test_cleanup_without_ceiling_drop_fails` — a synthetic PR that
  drops the file 60 KB while leaving the ceiling alone must FAIL rule 2. Without this test,
  rule 2's entire purpose is unverified.

---

### D3 — The waiver

This repo has an established `Allow-*:` commit-trailer idiom, and Proposal D uses it rather
than inventing anything. The reference implementation is
[`util/release_train/archive_guard.py`](../util/release_train/archive_guard.py):

- `:187` — whole-body `MULTILINE` scan, case-insensitive, of every commit message in
  `BASE..HEAD`.
- `:190-208` — `parse_allow_trailers` returns `(tokens, wildcard)`; comma- or
  whitespace-separated; `*` sets the wildcard. *"Copied verbatim from the docs screen's
  `parse_allow_trailers` … so the two escapes are keystroke-compatible."*
- `:210-215` — `_waives`: wildcard, exact repo-relative path, or bare basename.
- `:224-236` — `change_waived`: the waiver's confinement, conjunctive over *every* path.
- The trailer text is **injected** via `--trailers-file`, produced by `ci.yml:775` with
  `git log --format=%B FETCH_HEAD..HEAD`, so the classifier stays pure and hermetically
  testable.

**Two trailers, with deliberately different economics:**

| Trailer | Waives | Economics |
|---------|--------|-----------|
| `Allow-Budget-Overrun: <file>\|*` | the rate check and the level check, **for this PR only** | a **loan**. The ceiling is unchanged, so the *next* PR touching that file inherits the overrun and fails until it is repaid or a raise is authorised. |
| `Allow-Budget-Raise: <file>\|*` | ratchet rule 1, permitting a declared ceiling to increase | a **permanent, legible** concession. The number goes up in a diff, in a config file, where a reviewer sees it. |

The loan structure is the anti-abuse mechanism, and it is the one thing here that
`Allow-Symbol-Loss:` does not have. A symbol-loss waiver is a free pass: it costs the author
nothing and imposes nothing on anyone. A budget overrun waiver **hands the bill to the next
author**, which converts casual use into a visible externality between colleagues. That is a
weaker deterrent than a hard block and a much stronger one than a warning.

**Visibility — three layers, because one is not enough.**

1. **Per-run.** Every waiver use emits a `::warning::` annotation (visible on the PR's checks
   tab without opening logs) *and* a `$GITHUB_STEP_SUMMARY` row naming the file, the bytes
   waived, the trailer's stated reason, and the commit author.
2. **Monthly ledger.** `.github/workflows/memory-budget-alarm.yml`, modelled directly on
   [`.github/workflows/pr-budget-alarm.yml`](../.github/workflows/pr-budget-alarm.yml): daily
   cron, `permissions: contents: read`, scans `git log` on main for `Allow-Budget-*` trailers
   in the trailing 30 days, **always** writes a step-summary table, and posts to Slack via
   `SLACK_WEBHOOK_URL` only on breach of `MEMORY_WAIVER_ALARM` (repo variable, default 3/month)
   — mirroring `pr-budget-alarm.yml:80-86`'s `PR_BUDGET_WARN` / `PR_BUDGET_ALARM` contract and
   its strictly-non-blocking Slack behaviour (`:149-166`).
3. **Ratchet interlock.** Waiver count is an input to D2 rule 3: a rate step-down requires
   `<= 1` waiver in the preceding window. **Waiver use directly and mechanically stalls the
   ratchet.** Over-waiving does not merely look bad; it freezes progress.

**Analysis**

**Strengths.**
- Zero new syntax for authors: identical grammar to `Allow-Symbol-Loss:` /
  `Allow-Docs-Rewrite:` / `Allow-Archive-Edit:`, which the team already writes.
- The trailer travels in git history, so it covers post-merge verification as well as the PR
  check — the same property that makes the sequence-safety trailer work for `main-verify.yml`.
- The loan structure and the ratchet interlock give waiver use two *automatic* costs that need
  no human policing.

**Weaknesses.**
- **A waiver is by definition a hole, and this design cannot close it.** Anyone who can push a
  commit can write the trailer. Three of the five always-bypass actors on the ruleset
  ([flood analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md):448-449)
  can click-merge past every non-nuclear stage regardless — including the Cursor App itself.
  **The gate's guaranteed value is the visible red at review, not prevention.** `ci.yml:787-794`
  already says exactly this about `sequence-safety`, and it is no less true here.
- The loan penalises the *wrong person*. The author who inherits the debt did not create it.
  That is intentional (it makes the externality visible) and it is also unjust, and both are
  true at once.
- **The squash trap.** Trailers live in commit messages; GitHub's squash merge composes a new
  message. AGENTS.md already carries this as a house gotcha for `Allow-Archive-Edit:`
  ("**Carry the trailer into the squash commit message**"). It will be forgotten, and the
  symptom is a *post-merge* failure on `main` after a green PR.

**Risks.**
- *Concrete scenario, and it has already happened in this repo.* On 2026-08-18 the
  docs-deletion screen went red on main for the third time. The first two recurrences were
  reflow artifacts, correctly waived. The third **looked identical** and was real content
  loss: `76e4513` reformatted nine notes files (568 insertions / 572 deletions — net *minus
  four lines*, the signature of a harmless reflow) and silently removed three substantive
  owner-decision blockquotes. It was fixed by restoration, not waiver, in `40230d2` (#1165).
  The pattern-match "this is the reflow thing again, waive it" was wrong precisely because the
  two are indistinguishable at the level anyone actually looks at.
- The general form: **a waiver used three times correctly trains everyone to use it the fourth
  time without looking.**

**Guardrails.**
- **Waivers are metered, not merely logged** — the `MEMORY_WAIVER_ALARM` Slack path and the
  ratchet interlock above. A trend is visible before it is a habit.
- **The trailer requires a free-text reason**, and the checker FAILs a bare
  `Allow-Budget-Overrun: AGENTS.md` with no `— <reason>` suffix. A waiver you must justify in
  prose is measurably harder to write reflexively than one you can paste.
  > **CORRECTION 2026-08-24 — NOT IMPLEMENTED, and the stated behaviour was inverted.** The
  > checker accepted **only** the bare form and silently discarded the `— <reason>` form this
  > bullet mandates. As of 2026-08-24 **both** forms are accepted and an unparseable claim is
  > reported rather than dropped; requiring a reason is still an open, deliberate decision. See
  > the correction in
  > [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-ARCHITECTURE-SYNTHESIS-2.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-ARCHITECTURE-SYNTHESIS-2.md).
- **The #1165 lesson, encoded**: the failure message for a *net-reduction* PR that also
  removes a heading routes to the docs screen rather than the budget gate, and says
  "restore, don't waive." The budget gate must never become the mechanism by which a content
  loss is waved through as a helpful shrink.
- `test_memory_budget_check.py::test_waiver_requires_reason` and
  `::test_waiver_does_not_waive_ratchet_rule_1` — the two properties that, if lost, turn the
  waiver into a free pass.

---

### D4 — Admission and routing

The rule an agent applies before writing anything into a resident file.

#### The cross-task test

The official guidance (MECH §5) is *"Would removing this cause Claude to make mistakes?"* For
this repo that question is nearly always answered **yes**, which is why the file is 170 KB:
every one of those 156 nested sub-bullets (BASE §4) was hard-won, and removing it would
plausibly cause a mistake *for someone*.

The discriminating question is one word longer:

> **Would omitting this cause a mistake in a session that is NOT working on this component?**

If **no**, the content is genre B (BASE §8) and does not belong in a resident file, however
true and however expensive it was to learn. This is the whole routing decision, and it is
decidable by an agent at 02:00 without judgement calls about importance.

#### The decision procedure

Ordered; take the first match.

| # | Question | Destination | Resident cost |
|---|----------|-------------|---------------|
| 1 | Can a machine check it deterministically? | a **hook** (D6) or a **CI gate**; delete the prose or reduce it to one line naming the gate | ~0 |
| 2 | Does it fail the cross-task test *and* describe a component's internal contract? | `docs/REFERENCE.md` section + the pinning test's docstring | 0 (read on demand) |
| 3 | Is it a multi-step procedure? | `.claude/skills/<name>/SKILL.md` — MECH §4a: body loads only on use | name + description only |
| 4 | Does it only matter when touching certain paths? | `.claude/rules/<name>.md` **with `paths:` frontmatter** — MECH §4b: triggers when Claude reads matching files | ~0 until triggered |
| 5 | Is it a war story, a post-mortem, an incident record? | `notes/` per the [naming convention](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) | 0 |
| 6 | Passes the cross-task test — every session needs it? | **resident core**, and it must displace an equal number of bytes | full |
| 7 | Cannot decide, or the session is ending? | `notes/memory-inbox/<UTC>_<slug>.md` (D5) | 0 |

Row 7 is not a cop-out; it is the load-bearing row. It guarantees the procedure **always
terminates in a write**, which is what stops a blocked append from becoming a lost lesson.

Three grounded warnings that belong beside the table:

- **Row 3 has a discovery budget.** MECH §4a: the skill listing shortens descriptions to fit
  **1 % of the context window**, dropping the least-invoked skills' descriptions first, capped
  at 1,536 chars each. A nine-repo rollout that creates dozens of skills starves its own
  discovery. Skills are for procedures, not for filing cabinets.
- **Row 4 needs a `.gitignore` change before it exists at all.** `.claude/` is fully ignored
  and only two subtrees are re-included (`.gitignore:172-181`: `!.claude/skills/`,
  `!.claude/agents/`). `.claude/rules/` requires a matching negation pair or it is untracked
  and unshared. This is a two-line prerequisite that is very easy to miss.
- **Row 6 is not free and must not be treated as free.** "Every session needs it" is the
  claim, and the budget is what forces it to be argued rather than assumed.

**Analysis**

**Strengths.**
- Decidable without judgement. The cross-task test is a *yes/no about scope*, not a weighing
  of value — which is exactly why an unattended agent can apply it consistently.
- Every destination named already exists or is a two-line change: `docs/REFERENCE.md` (28 H2 /
  73 H2+H3 sections, 162,231 bytes), `.claude/skills/` (3 skills), `notes/` (14 subdirs).
  MECH §4 confirms rows 3 and 4 genuinely defer loading — this is not `@`-import theatre
  (MECH §3).
- Row 2 is where the volume goes, and BASE §5 shows the destination is already built:
  `docs/REFERENCE.md` carries sections on precisely the subjects `## Key Files` documents at
  length, and **32 lines of `AGENTS.md` already end by pointing at the REFERENCE.md section
  holding the same material**. The routing is not hypothetical; it is half-done and stalled.

**Weaknesses.**
- **The procedure is prose, and prose is advisory.** MECH §6 is explicit: memory content is
  delivered as a user message, *"there's no guarantee of strict compliance."* An agent may
  simply not follow it. Only the gate is deterministic — the procedure's real enforcement is
  that ignoring it makes your PR red.
- **The Cursor fleet may never read it at all.** The flood analysis flags this as open
  question OQ3 (`:514`: *"whether Cursor reads repo `AGENTS.md` at [generation]"*) and it is
  still open. Since the fleet is the highest-volume writer, the routing procedure's coverage
  of the actual problem population is **unknown**.
- Row 2 has an ordering hazard: moving lore into `docs/REFERENCE.md` removes it from the
  resident file, which is a *deletion* — and deletions on `AGENTS.md` are exactly what the
  now-required docs screen blocks. §5.4 shows why that opposition is desirable, but it does
  mean row 2 is a two-file PR with a trailer, not a one-line edit.

**Risks.**
- *Concrete scenario.* An agent applies the procedure honestly, decides row 2, and appends the
  lore to `docs/REFERENCE.md` — which is 162,231 bytes and **also ungoverned**. Repeat 200
  times and `docs/REFERENCE.md` is 400 KB. Nothing has been fixed except which file is
  embarrassing; the difference is that `docs/REFERENCE.md` is read on demand, so the token cost
  really is gone — but a 400 KB reference nobody can navigate has its own failure mode.
- Row 4 rules proliferate to the point where a session reading one file triggers eight rules,
  and the lazy-loading advantage evaporates in aggregate.

**Guardrails.**
- Destination files get **reported** budgets in the daily alarm (D1 guardrails) from day one,
  and a `WARN` threshold. Reported-not-gated is deliberate: on-demand growth is not a token
  cost, so gating it would be enforcing the wrong thing.
- A `docs/REFERENCE.md` **navigability** signal in the monthly report — H2 count and mean
  section size — so "the reference became unusable" is visible before it is chronic. Reported
  only; there is no honest threshold for this.
- `.claude/rules/` count and aggregate `paths:` breadth reported by
  `util/agent_suite_doctor.py` (which already checks every suite layer,
  `agent_suite_doctor.py:76-210`), so rule sprawl surfaces in a tool the team already runs.

---

### D5 — Concurrent write-path discipline

**The stated root cause.** ≈1.3 merges/day into one file (BASE §2), from sessions that cannot
see each other. `AGENTS.md` is the fleet's #1 same-file cluster at 54 PRs (§3.4). The observed
damage is not merely growth: it is the wholesale-section-deletion class of #801/#803, where a
merge took the branch side and deleted sibling sections merged hours earlier.

**The mechanism: an append-only inbox with distinct filenames.**

```text
notes/memory-inbox/
  README.md                                  <- the contract, ~20 lines
  2026-08-18T1403Z_cascor-seed-repro.md
  2026-08-18T1412Z_wait-for-checks-absent-bucket.md
  2026-08-18T1547Z_experiment-stack-lock-release.md
```

Rules, all mechanical:

1. A session that learns something and cannot immediately route it (D4 rows 1–6) writes a
   **new file**. Never an edit to an existing one.
2. Filename `<UTC ISO basic>_<kebab-slug>.md`. The UTC timestamp makes collision effectively
   impossible and ordering free.
3. Inbox files are **never** loaded into any session. They cost zero resident tokens.
4. An inbox file may be **deleted only in a PR that also adds routed content elsewhere.** A
   structural guard enforces this — the exact shape of
   [`util/release_train/archive_guard.py`](../util/release_train/archive_guard.py), which
   already proves a PR's diff is add-only, path-confined, name-valid and single-purpose
   (`:9-25`). Here the rule inverts: a deletion from `notes/memory-inbox/` requires a
   non-inbox addition in the same diff. **Curation cannot silently drop knowledge.**

#### What happens when three sessions each add 40 lines to the same section on the same day

| | Status quo | Under D5 |
|---|---|---|
| Paths touched | all three edit `AGENTS.md § Key Files` | three distinct new files |
| Git outcome | overlapping hunks in a 54-PR cluster; two of three conflict | **zero conflicts, by construction** |
| Human action | rebase, then *re-author* the conflicted hunk by hand | none |
| Failure mode | the #801/#803 class: re-authoring takes one side and deletes the other; net-negative diffs pass as reflow (§3.4) | none available — no shared file, no merge, no re-authoring |
| Lost-update risk | real, and demonstrated | moved to the curation step, where guard rule 4 blocks it |
| Latency to resident | minutes (and wrong) | one curation cycle (and right) |
| Resident bytes added | +120 lines, unreviewed | 0 until curated |

The trade is explicit: **latency instead of loss.** Knowledge is durable and greppable
immediately; it becomes *resident* only after triage. A session running between the write and
the curation does not get the benefit. That is a real cost and I am not going to pretend it
away — it is the price of not letting three unreviewed appends into a file every agent loads.

#### The curation cycle

Weekly. A `planner`-designed, `task-executor`-executed pass ([`.claude/agents/`](../.claude/agents/))
that reads the inbox, applies D4 to each item, and opens **one** PR. Because
`required_signatures` applies fleet-wide, the PR is created through
[`util/open_signed_pr.py`](../util/open_signed_pr.py), which creates branch + commit + PR via
`createCommitOnBranch` so the commit is GitHub-signed and needs no working tree.

#### Rejected alternative: per-section ownership

The flood analysis already proposed per-class disjoint file scopes for the fleet
([`:502-504`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md): *"docs
automation owns `docs/**`+`AGENTS.md`, test automation owns `tests/**`"*). Rejected here as
the primary mechanism for three reasons: it is a Cursor-**dashboard** setting the repo cannot
verify or enforce; sections are not stable (the tree-drift gate exists precisely because
structure drifts); and a single owner per section is a serialisation bottleneck exactly where
throughput is the point. It remains a good *supplementary* control at the fleet's source, and
is listed as an owner decision in §11.

**Analysis**

**Strengths.**
- **Merge conflicts on the resident file go to zero for this class of write** — not reduced,
  eliminated, because no two sessions ever touch the same path.
- It removes the human re-authoring step that *caused* #801/#803. The damage in those cases
  was a manual conflict resolution, not the tooling.
- It decouples capture from admission, which is the actual conceptual error in the status
  quo: "I learned something" and "every future session must load this" are being treated as
  the same event, and they are not remotely the same event.
- Zero resident cost. Inbox files are never loaded.

**Weaknesses.**
- **Latency, unavoidably.** Up to one week between learning and residency.
- **The curator is a new single point of failure.** If the weekly pass does not happen, the
  inbox becomes a landfill: knowledge is technically preserved and practically lost. This is
  the classic fate of every inbox ever designed, and nothing in this proposal makes it immune.
- **It relies on the agent choosing the inbox.** No hook can force it (a `PreToolUse` hook can
  deny an edit to `AGENTS.md`, but it cannot make the session write the inbox file instead —
  and denying edits outright would be far too blunt).
- It is *additional* discipline, not a simplification. Honest count: one more directory, one
  more guard, one more recurring job.

**Risks.**
- *Concrete scenario.* Six weeks in, the inbox holds 90 files. The curation PR is now a
  90-item triage nobody wants to review, so it is deferred; at 200 files it is abandoned and
  someone proposes deleting the directory. The knowledge was captured and is now noise. This
  is the single most likely way Proposal D fails in practice, and it fails *quietly*.
- Second scenario: because the inbox always accepts, it becomes the path of least resistance
  for content that genuinely *should* be resident, and the resident core slowly stops
  reflecting reality.

**Guardrails.**
- **Inbox depth is an alarmed metric, not a hope.** The daily report includes inbox file count
  and oldest-file age, with `MEMORY_INBOX_WARN` (default 25 files or 14 days) and
  `MEMORY_INBOX_ALARM` (default 60 files or 30 days) repo variables, Slack on breach —
  identical contract to `pr-budget-alarm.yml:80-86`. A stalling curator is visible within two
  weeks, which is the difference between a recoverable backlog and a landfill.
- **Guard rule 4** (delete-only-with-a-routed-addition) makes the failure mode "the backlog
  grows" rather than "the knowledge disappears". Loud beats lossy.
- `README.md` in the inbox states the contract in ~20 lines, so a session that has never seen
  the scheme can follow it from the directory alone.
- The curation PR is opened by `util/open_signed_pr.py`, whose dup-guard refuses when an open
  PR already exists for the branch — so a doubled cron cannot produce two competing curations.

---

### D6 — Hooks

MECH §6 is the grounding, and it cuts both ways:

> "CLAUDE.md content is delivered as a user message after the system prompt … there's no
> guarantee of strict compliance."
> "To block an action regardless of what Claude decides, use a PreToolUse hook instead."

So the 164 mandatory lines are **advisory context competing for attention, not enforcement.**
A directive that must hold belongs in a hook or a CI gate.

**The honest sizing first, because the popular version of this argument is wrong.** §3.3
measured where the mandatory language actually lives: **86 % of it is inside the three genre-B
sections**, describing utility internals — specifications for scripts, already enforced by
those scripts' own tests. Those are not agent directives and converting them to hooks is
meaningless. The genuinely hook-able set is small:

| Directive | Location | Enforcement | Prose retired |
|-----------|----------|-------------|---------------:|
| Scripts go under `util/`; `/tmp/` is prohibited as a script home | `AGENTS.md:904-918` | `PreToolUse` on `Write`/`Edit`: deny a `.py`/`.bash`/`.sh` target under `/tmp/` | ~1,700 B |
| Never a bare `git push <tag>`; cut a GitHub Release | `AGENTS.md:113-114` | `PreToolUse` on `Bash`: deny `git push` matching a tag ref | ~400 B |
| Worktrees live in the centralized dir, never inside a repo | `AGENTS.md:1034` | `PreToolUse` on `Bash`: deny `git worktree add` outside the centralized path | ~200 B |
| Never `grep` `id_assignments.yaml` for content | `AGENTS.md:940` | `PreToolUse` on `Grep`/`Bash` targeting that path | ~150 B |
| **Total** | | | **~2,450 B** |

**~2,450 bytes of 170,137 — 1.4 % of the file, 7.5 % of the genre-A residue.**

That is the honest number and I am not going to dress it up. **Hooks are an enforcement
upgrade with a rounding-error size benefit.** Do them because "no guarantee of strict
compliance" is unacceptable for a rule about where secrets and scripts live, not because they
shrink anything.

Two directives that look hook-able and are not, worth naming so nobody tries:

- **Thread handoff at 95–99 % context** (`AGENTS.md:1042-1115`, 3,874 bytes — the second
  largest genre-A block). There is **no tool call to intercept**: it is a judgement about the
  session's own context utilisation. It stays prose, or becomes a Skill with a resident
  trigger line. No hook can help.
- **The worktree *procedure*** (`AGENTS.md:950-1041`, 4,165 bytes). The *destination* rule is
  hook-able (above); the seven-phase procedure is a Skill (D4 row 3), not a hook.

#### The scope limit that reorders the whole element

**A `PreToolUse` hook fires in a Claude Code session. It does not exist for the Cursor GitHub
App.** The fleet authors PRs through integration 1210556 with no in-repo config
([flood analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md):33),
and it is the **highest-volume writer** — 54 of the window's `AGENTS.md` PRs. So hooks cover
the *minority* of the write path by volume.

**Therefore: CI gates are primary and hooks are secondary**, and the D1/D2 elements carry the
load. This inverts the order the brief's framing might suggest, and the measurement is why.

**Analysis**

**Strengths.**
- The only *deterministic* enforcement available (MECH §6), for the four rules where
  probabilistic compliance is genuinely not good enough.
- Enforcement at the moment of action, not at PR time — the `/tmp/` script rule is worthless
  once the script is written and the session has ended, which is exactly how
  `phase4_consolidate.py` and `v2_citation_validate.py` were lost (`AGENTS.md:915`).
- Retires prose whose only job was to be obeyed.

**Weaknesses.**
- **Coverage is minority-by-volume**, as above. The largest writer is unreachable.
- **~1.4 % size benefit.** Not a size strategy.
- Hooks are local configuration, so they must be *distributed* to be real. The repo already
  has this pattern — [`util/install_agents.bash`](../util/install_agents.bash) mirrors
  `.claude/{agents,skills}` into `~/.claude` idempotently and reversibly — but hooks would
  need `.gitignore` negation for `.claude/hooks/` and `.claude/settings.json` (`.gitignore:172-181`
  re-includes only `skills/` and `agents/` today), plus an installer extension.
- **MECH does not verify the hook configuration schema.** See §12.1 — this is the single
  largest unverified dependency in the proposal.

**Risks.**
- *Concrete scenario.* A hook denies `Write` to `/tmp/*.py`. A session legitimately needs a
  throwaway analysis script, is denied, and — with no alternative offered — writes the
  analysis inline as a giant `bash -c` one-liner instead. Worse outcome, invisible to
  everyone, and the hook reports a successful block.
- A hook with a broad matcher denies a class of legitimate calls, the session cannot proceed,
  and the fastest fix is for the operator to delete `.claude/settings.json`. **All four hooks
  are then off, permanently and silently.**

**Guardrails.**
- Every deny message names the **allowed** alternative (for `/tmp/` scripts:
  `util/ad-hoc/<name>.py`, per `AGENTS.md:904-918`), so a denial is a redirect, never a wall.
  Same principle as D1's failure message.
- `util/agent_suite_doctor.py` gains a `check_hooks` row (OK/WARN/FAIL, `agent_suite_doctor.py:36`),
  so a deleted or empty hook config is reported by a tool the team already runs, rather than
  discovered a month later. **A hooks config that is absent must read `FAIL`, not `OK`** —
  this is the `check_discovery` fail-closed precedent (`agent_suite_doctor.py:167-186`).
- Each hook keeps a **matching CI gate** where one is possible, so a disabled hook degrades to
  late detection rather than none. The `/tmp/`-script rule, for instance, is partly checkable
  in CI by scanning the diff for new scripts outside `util/`.

---

### D7 — Periodic eviction

Governance that only ever admits is a queue, not a budget. Something has to leave.

**Cadence.** Monthly, on the schedule cron of `memory-budget-alarm.yml` (D3), report-only,
producing a ranked eviction-candidate list. The candidates are *proposed*; a human or a
`planner` pass decides.

**Three staleness signals, in descending confidence.**

| Signal | How measured | Strength | Verdict |
|--------|--------------|----------|---------|
| **Dead referent** | every backticked path-shaped token in the file; does the path resolve? | strongest available — a file documenting something that moved is wrong *now* | WARN + candidate |
| **Blame age** | `git blame` line age vs the file's median | weak on its own — a stable rule is old *because it is right* | tie-breaker only |
| **Closed-issue citation** | a line citing `#NNN` where the issue is closed **and** a pinning test exists | this repo's own convention says the test is then the record | WARN + candidate |

**The dead-referent signal, measured honestly.** Running it today over `AGENTS.md`: 164
distinct path-shaped backtick tokens, **7 unresolved**:

```text
util/generate_dep_docs.sh            (x4)   deliberately dead -- anti-resurrection reference
scripts/generate_dep_docs.sh                deliberately dead -- migrated to juniper-ci-tools
scripts/check_doc_links.py                  deliberately dead -- migrated to juniper-doc-tools
util/ad-hoc/2026-08-10_driver_stall_shim.py deliberately dead -- retired, guarded
tests/test_ws_tunables.py                   resolves at juniper-service-core/tests/...
websocket/tunables.py                       resolves at juniper-service-core/juniper_service_core/...
artifacts/results/stats.json                a runtime artifact path, not a repo file
```

**All seven are false positives.** Four are deliberate anti-resurrection references — the file
names them *because* they must never come back. Two are sub-package-relative paths that
resolve one directory down. One is a runtime path.

I am reporting this against my own mechanism because it is the most useful thing in this
section: the naive signal has a **100 % false-positive rate at this implementation**. It is
therefore specified as **WARN-only with a maintained allowlist**, never a gate, and the
allowlist's first seven entries are above. A future refinement (resolve against sub-package
roots; recognise an anti-resurrection sentence pattern) would improve precision — but it would
be dishonest to claim precision I have not built.

**Analysis**

**Strengths.**
- Makes eviction a *scheduled* activity with a candidate list, which is the difference between
  a policy and an intention. §3.1's 172:14 ratio is what "no scheduled eviction" looks like.
- The dead-referent signal, even at this precision, points at genuine rot: the four
  anti-resurrection entries are exactly the lines whose *content* has already migrated to
  `juniper-ci-tools` / `juniper-doc-tools`.
- Report-only means it cannot break anything, so it can ship in phase 1 with no soak.

**Weaknesses.**
- **No signal available distinguishes "stale" from "load-bearing and quiet."** A line that has
  not changed in six months is *more* likely to be a settled invariant than a stale one.
  Blame age is close to useless here, and I have marked it as a tie-breaker only rather than
  pretending otherwise.
- **Report-only means it may simply be ignored**, and a monthly report nobody reads is
  indistinguishable from no report.
- The closed-issue signal needs `gh` network calls, so it is best-effort and must degrade to
  `SKIP` rather than fail — which means it can be silently absent.

**Risks.**
- *Concrete scenario.* An eviction pass removes a line that reads like dead lore
  ("`Offline --local-git` must raise (open #773), not return `set()`") because #773 has since
  closed and a test pins it. Six weeks later a refactor reintroduces the bug in a code path
  the test does not cover. The eviction was defensible on every stated criterion and still
  wrong. Eviction has an irreducible error rate.
- The report becomes a ritual: candidates are generated, nothing is evicted, and the list
  itself becomes another artifact to maintain.

**Guardrails.**
- **Eviction is a move, never a delete.** Every evicted line lands in `docs/REFERENCE.md`, a
  rule, a skill, or `notes/` — so the scenario above costs a lookup, not the knowledge. This
  is enforced by the same structural guard as inbox rule 4.
- The now-required `Sequence Safety` docs screen (`e209b74`, #1166) fails on a deleted heading
  or a `>=5`-line deletion run, so a bulk eviction cannot ship as an unreviewed deletion.
  §5.4 develops this.
- **Eviction throughput is itself reported**: bytes evicted per month, alongside bytes
  admitted. If admission consistently exceeds eviction, the ratchet is not working and the
  report says so in one number rather than requiring anyone to infer it.

---

## 5. Confronting the objections

### 5.1 "Governance without a destination is just a wall"

**This is the strongest objection and it is substantially correct.**

If the gate refuses an append and no good home exists, three things happen, all bad: the
knowledge is lost; or the gate is gamed (padding an ungoverned file, cramming the content onto
an existing line, waiver abuse); or the gate is disabled. §3.1 is the evidence that this repo
will not simply absorb a wall — 172 growing merges is 172 authors who each had a reason.

Four answers, in decreasing strength.

1. **The rate axis is satisfiable with no destination at all.** This is the real answer and it
   is why D1 leads with rate rather than level. Staying under a rate budget requires only
   "add less than R this month, or offset." No new file, no migration, no companion proposal.
   The **level** axis is what needs destinations — which is exactly why it ships later and
   starts inert.
2. **The inbox is an unconditional destination** (D5, D4 row 7). It accepts anything,
   immediately, with no review and no gate. The routing procedure structurally cannot
   terminate in "nowhere to put this."
3. **The destinations are named and mostly already exist** (D4 table), and BASE §5 shows
   `docs/REFERENCE.md` is already half the intended destination — 32 `AGENTS.md` lines already
   end by pointing at the REFERENCE.md section holding the same material.
4. **The failure message routes** (D1). A gate that only denies teaches nothing; one that names
   six destinations and a default teaches the policy every time it fires.

**And now the part I am obliged to say plainly.** Answers 3–4 are about *where bytes go*, not
about *making the resident file good*. Proposal D can freeze `AGENTS.md` at 170 KB forever and
that is still a 42,000-token always-on tax. **The reduction is a companion proposal's work,
and Proposal D's value is conditional on someone doing it.** §10 enumerates exactly which
parts depend on which companion. I would rather state the dependency than quietly claim a
reduction the mechanism does not produce.

### 5.2 Gate fatigue and waiver abuse

This repo's own history is the evidence, and it is not favourable.

- The `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` trailers plus a WARN-only label hatch
  (`ci.yml:796-803`) exist because a hard screen needed relief valves within weeks.
- The documented failure: on 2026-08-18, main-verify's docs screen went red for the third
  time. Two prior recurrences were harmless reflows, correctly waived. The third was **real
  content loss** — `76e4513` reformatted nine notes files at 568 insertions / 572 deletions
  (net *−4 lines*, indistinguishable from a reflow) and removed three substantive
  owner-decision blockquotes. Restored, not waived, in `40230d2` (#1165).

What stops the budget waiver becoming the default path:

| Mechanism | Effect | Honest strength |
|-----------|--------|-----------------|
| **The loan structure** (D3) | an overrun hands the bill to the next author on that file | strong — it is the only mechanism here with an *automatic* cost |
| **Ratchet interlock** | `>1` waiver in the window stalls the rate step-down | strong — over-waiving freezes visible progress |
| **Mandatory free-text reason** | a bare trailer FAILs | moderate — friction, not prevention |
| **Slack alarm at 3/month** | trend visible before habit | moderate — depends on someone reading it |
| **`::warning::` + step summary** | visible without opening logs | weak alone, necessary in combination |

**What does *not* work, and I am not going to claim it does:** three of the ruleset's five
always-bypass actors can click-merge past every non-nuclear stage
([flood analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md):448-449),
including the Cursor App itself. `ci.yml:791-794` already concedes the equivalent point for
`sequence-safety`: *"Even promoted, the owner + Cursor App always-bypass it, so its guaranteed
value is the visible red at review."* **The same ceiling applies to every gate in this
proposal.** The budget gate's guaranteed value is a legible number at review time and a
metered ledger — not prevention.

### 5.3 The vacuous-pass class

This repo has a documented failure class where a check's machinery breaks and it reports
SUCCESS, with three instances recorded in a single day. A size gate is unusually exposed: it
measures the *wrong* file, or an *empty* file list, and passes forever while looking healthy.

**Four repo-specific ways this gate could go vacuous.**

1. **The `CLAUDE.md` symlink.** BASE §1: `CLAUDE.md` is a symlink to `AGENTS.md` — *the same
   170,137 bytes*. A gate that accidentally measures `CLAUDE.md` passes **identically today**
   and diverges silently the moment the symlink is replaced with a real file. This is a
   perfect vacuous-pass trap and it exists right now.
2. **Empty target list.** `conf/memory_budget.toml` loses its `[[targets]]` table in a merge;
   the checker iterates zero targets and reports OK.
3. **Unresolvable 30-day baseline.** `git rev-list --before=<30d>` returns empty on a shallow
   clone. A naive `size or 0` makes the projected net enormous (always fail — noisy but safe)
   or, if the coercion lands on the *other* side, always zero (**pass forever**). This repo has
   this exact bug on record: the release-train's `_gh_lines` returning `None` coerced by
   `or []` into an empty set, which made `diff_base_tag not in releases` always true and
   yielded a false TAG_ONLY for every package.
4. **Missing declared section.** A heading in the group ceiling is renamed; the checker finds
   no bytes for it and reports the group comfortably under budget.

**The negative-control design.** This repo already has the pattern:
[`tests/test_agents_md_tree_drift.py:109-112`](../tests/test_agents_md_tree_drift.py):

```python
def test_checker_flags_a_missing_dir(self) -> None:
    # Synthetic negative: a dir absent from the tree must be reported, while a
    # present one (conf/, added by G-3) must not -- proving the guard bites.
    self.assertEqual(missing_dirs(["conf", "zzz_not_a_real_dir"], self.tree), ["zzz_not_a_real_dir"])
```

`tests/test_memory_budget_check.py` carries the same discipline, one test per trap:

| Test | Pins |
|------|------|
| `test_synthetic_over_budget_fixture_fails` | the gate can fail at all — a fixture 1 byte over must FAIL, one at the limit must PASS |
| `test_target_list_is_explicit_and_nonempty` | zero targets is FAIL, never OK; no glob-derived targets |
| `test_governed_target_is_agents_md_not_the_symlink` | asserts the target resolves to `AGENTS.md`; asserts `CLAUDE.md` currently *does* share its bytes, so the test documents why the distinction matters |
| `test_unresolvable_baseline_raises` | a shallow / missing 30-day baseline exits **2**, never 0 — no `or 0` coercion anywhere |
| `test_declared_section_absent_fails` | a renamed heading is FAIL with a naming message, never a silent zero |
| `test_measured_size_matches_ground_truth` | the checker's byte count equals `os.stat().st_size` for the real file — the measurement path is exercised against reality, not against itself |

The last one is the general antidote and is worth stating as a principle: **a checker must be
tested against ground truth it did not compute.** A gate that only compares its own output to
its own expectations is a tautology with a green tick.

**Never-vacuous by design, additionally:** the daily alarm always writes the current sizes to
the step summary whether or not anything breached (the `pr-budget-alarm.yml:20-21` contract).
A gate that reports its input every day cannot silently measure nothing — the day the number
reads 0 bytes for a 170 KB file, it is visible.

### 5.4 False economy — compression that damages comprehension

A byte budget can be satisfied by making prose terser and denser while raising cognitive load.
This file is already showing the pathology: `AGENTS.md` averages **152.6 bytes/line** against
`docs/REFERENCE.md`'s **87.0** — the resident file is 1.75× denser per line than the reference
it duplicates, with a 512-character line-length limit permitting far more.

**The structural answer: the budget and the deletion screen form a vise.**

- The **size budget** (D1) penalises bytes in the resident file.
- The **docs deletion-magnitude screen** — `juniper-docs-additions-check`, **required** on all
  nine repos as of `e209b74` (#1166) — FAILs on a deleted Markdown heading or a `>=5`-line
  deletion run, over a scope that includes `AGENTS.md` (`ci.yml:873-877`).

Consider the three ways to satisfy the budget:

| Move | Budget | Docs screen | Result |
|------|--------|-------------|--------|
| Compress prose in place (delete lines, keep headings) | passes | **FAILS** on a `>=5`-line deletion run | blocked |
| Delete a subsection wholesale | passes | **FAILS** on the deleted heading | blocked |
| **Move** content to `docs/REFERENCE.md` / a rule / a skill, leaving a pointer | passes | FAILs → **waived with `Allow-Docs-Rewrite:`**, and the waiver is legitimate because the content demonstrably exists at the destination in the same PR | **the only clean path** |

**Compression is mechanically the hardest option and relocation is the easiest.** That is the
design: the two gates are opposed, and the opposition is the point.

Three honest qualifications:

- The third row still involves a waiver, and §5.2 says waivers erode. The mitigation is that
  *this* waiver is checkable by a reviewer in seconds — the content is visible in the same
  diff, at its destination.
- The #1165 case proves the screen's limits: a **net −4 line** reformat destroyed 116 tokens of
  owner decisions and was nearly waived as a reflow. A byte-neutral edit can be catastrophic,
  and no size budget will ever see it. The docs screen caught it; the size budget structurally
  could not have.
- A **density counter-metric**, reported never gated: mean bytes/line and the count of lines
  over 400 bytes. If a budget-satisfying PR raises mean line length, the step summary says so.
  Not gated, because a two-sided constraint on both total bytes and line density is a trap with
  no legal move — and a gate with no legal move gets deleted.

### 5.5 Concurrency mechanics — three sessions, one section, one day

Fully worked in [D5](#d5--concurrent-write-path-discipline). Summary: under the status quo,
three overlapping edits to `AGENTS.md § Key Files` produce two conflicts and a human
re-authoring step, which is the mechanism that produced #801/#803. Under D5 they produce three
distinct new files, zero conflicts, zero re-authoring, zero resident bytes, and one triage item
per session. The cost is latency to residency; the benefit is that the lost-update path is
removed rather than mitigated, and guard rule 4 blocks the remaining loss channel at curation.

---

## 6. Budget arithmetic and growth projection

### 6.1 Before / after allocation

Measured with the convention "H2 heading line through the line before the next H2, inclusive of
intervening rules"; the fifteen section figures sum exactly to 170,137
([Appendix A](#appendix-a--measurement-commands)).

> *Convention note.* BASE §3 reports 99,304 / 20,469 / 16,101 for the three largest sections
> against my 99,627 / 21,833 / 16,167; `## Build & Package Commands` agrees exactly at 4,617.
> The gap is where a section's trailing `---` rule is attributed, not a disagreement about
> content. BASE's figures are the fact base; mine are used only where a full partition summing
> to the file total is needed, and the convention is stated so a reviewer can reproduce either.

| Section | Now (B) | % | Genre | Terminal allocation (B) | Δ |
|---------|--------:|--:|-------|------------------------:|--:|
| header + `## What This Is` | 929 | 0.5 | A | 900 | −29 |
| `## Build & Package Commands` | 4,617 | 2.7 | mixed | 1,400 | −3,217 |
| `## Publishing` | 3,656 | 2.1 | B | 900 | −2,756 |
| `## Shared Observability Helpers` | 1,505 | 0.9 | B | 300 | −1,205 |
| `## Shared Service-Core Contracts` | 3,531 | 2.1 | B | 300 | −3,231 |
| `## Repository Structure` | 21,833 | 12.8 | B | 1,800 | −20,033 |
| `## Key Files` | 99,627 | 58.6 | B | 6,000 | −93,627 |
| `## CI/CD Pipelines` | 16,167 | 9.5 | B | 1,800 | −14,367 |
| `## Pre-commit Hooks` | 2,085 | 1.2 | A | 1,200 | −885 |
| `## Secrets Management (SOPS)` | 492 | 0.3 | A | 492 | 0 |
| `## Ecosystem Context` | 2,315 | 1.4 | A | 1,100 | −1,215 |
| `## Conventions` | 2,488 | 1.5 | A | 1,800 | −688 |
| `## Pull Request Conventions` | 2,853 | 1.7 | A | 1,800 | −1,053 |
| `## Worktree Procedures` | 4,165 | 2.4 | A | 1,200 | −2,965 |
| `## Thread Handoff` | 3,874 | 2.3 | A | 1,400 | −2,474 |
| **Allocated** | **170,137** | 100 | | **22,392** | **−147,745** |
| unallocated reserve | — | | | 7,608 | |
| **`max_bytes` ceiling** | — | | | **30,000** | |

Arithmetic: `900+1,400+900+300+300+1,800+6,000+1,800+1,200+492+1,100+1,800+1,800+1,200+1,400 = 22,392`;
`30,000 − 22,392 = 7,608` reserve.

**Why 30,000.** Two independent routes converge:

- MECH §5's target is **under 200 lines**. At this file's measured 152.6 bytes/line, 200 lines
  ≈ **30,520 bytes**.
- BASE §8: removing the three genre-B sections leaves **34,263** bytes, *"the natural order of
  magnitude for a target budget."* My partition gives 32,510 for the same residue. The 30,000
  figure sits just below both, i.e. the genre-A core with the genre-A fat also trimmed.

**Token effect.** 30,000 bytes ≈ 29,680 characters ≈ **7,400 tokens** (BASE §1's implied
4.017 chars/token). Today: 168,317 characters ≈ **41,900 tokens**. Reduction ≈ **34,500
tokens**, about **17 % of a 200 k context window** returned — against MECH §6's finding that
always-on memory currently consumes ~25 % of the window before the first prompt.

**The allocation column is a budget, not a promise.** Proposal D does not cut these sections;
it forces the allocation *conversation* and makes the result permanent. The column exists so a
reviewer can see the terminal budget is arithmetically reachable, not to pre-empt a companion
proposal's design.

### 6.2 The rate schedule

Each step requires the prior step held for 30 days with `<= 1` waiver.

| Phase | `max_net_bytes_30d` | Mode | Basis |
|-------|--------------------:|------|-------|
| P1 | 5,000 | **advisory** | deliberately set at the *terminal* value during soak so the report shows the true end-state bite rate (today: 18.6× over) while blocking nothing |
| P2 | 60,000 | blocking | ~⅔ of the measured 92,796 — a real constraint the current rate clearly breaches |
| P3 | 30,000 | blocking | ~2.4× the pre-flood median of 12,672; ≈1,000 B/day |
| P4 | 15,000 | blocking | the **measured** pre-flood sustained maximum (14,580, §3.2) |
| P5 | 5,000 | blocking | ≈165 B/day — roughly one short bullet per day |

Soaking at the terminal value and blocking on a ladder is deliberate: an advisory gate set at
the *blocking* threshold tells you only whether that threshold is survivable, whereas one set
at the terminal value tells you the full distance to be travelled.

### 6.3 Projected growth

Status quo, two projections, both from the fact base:
**(a)** linear at the measured 92,796 bytes/30 days = 3,093 B/day;
**(b)** BASE §2's characterisation — "roughly doubling every two months."

| Date | (a) linear | (b) doubling/2 mo | **Proposal D alone** | **D + a cleanup companion** |
|------|-----------:|------------------:|---------------------:|----------------------------:|
| 2026-08-18 | 170,137 | 170,137 | 170,137 | 170,137 |
| +30 d (2026-09-17) | 262,927 | ~219,000 | ≤230,137 (P2, R=60,000) | ≤230,137 |
| +60 d (2026-10-17) | 355,717 | 340,274 | ≤260,137 (P3, R=30,000) | ≤175,000 (cycle 1; ceiling ratchets to ≤183,000) |
| +90 d (2026-11-16) | 448,507 | ~480,000 | ≤275,137 (P4, R=15,000) | ≤120,000 |
| +120 d (2026-12-16) | 541,297 | 680,548 | ≤280,137 (P5, R=5,000) | ≤60,000 |
| +180 d (2027-02-14) | 726,877 | 1,361,096 | **≤290,137** | **≤30,000, held indefinitely** |

Read this table honestly:

- **Proposal D alone still grows** — to ~290 KB by February. It caps the trajectory at
  **2.5×–4.7× below** status quo, and that is a large win, and it is still not a reduction.
- **The reduction column requires a companion.** What Proposal D contributes to that column is
  the word *held*: without a ratchet, the 30,000 in the last cell is a waypoint on the way
  back to 170,000 in 44 days (§1).
- Column (b) crosses **one million bytes** inside six months. At ~4 chars/token that is ~250 k
  tokens of always-on memory — larger than the entire 200 k context window. The status quo is
  not merely suboptimal; it is on a path to being arithmetically impossible.

---

## 7. The `MEMORY.md` problem

Of the four proposals this one is the natural home for `MEMORY.md`, because `MEMORY.md` is
purely a governance problem: it has a **hard limit**, the overflow is **silent**, and there is
nothing to reorganise — it is a flat list of one-line index entries.

### 7.1 The position, measured

MECH §2 (T1, `/docs/en/memory`):

> "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at
> the start of every conversation. **Content beyond that threshold is not loaded at session
> start.**"

Frontmatter and block-level HTML comments are stripped before measuring (v2.1.211+).

Measured today at `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md`:

| Measure | Value | Limit | Nominal headroom |
|---------|------:|------:|-----------------:|
| Lines | 139 | 200 | 61 lines |
| Bytes | 20,388 | ~25,600 | 5,212 bytes |
| Characters | 20,049 | — | — |
| Mean bytes/line | **146.7** | — | — |
| Sibling topic files in the directory | 153 | — | — |
| Frontmatter / HTML comments present | **none** | — | every byte counts |

### 7.2 The real headroom is 43 % smaller than the line count suggests

`min(200 lines, 25 KB)` — and at 146.7 bytes/line the **byte axis binds first**:

- Byte headroom: `25,600 − 20,388 = 5,212` bytes ÷ 146.7 = **≈35 entries**.
- Line headroom: `200 − 139` = **61 entries**.
- The byte limit binds at **≈174 lines**, not 200. **The nominal line headroom overstates real
  headroom by 74 %.**

Rate: the directory's oldest topic file dates to 2026-04-09, so 139 index entries accumulated
over ≈131 days ≈ **1.06 entries/day** ≈ 156 bytes/day.

> **Time to silent truncation: ≈33 days — roughly 2026-09-20.**
> On the stricter reading of "25 KB" as 25,000 bytes, ≈30 days.

### 7.3 Truncation drops the newest entries first

`MEMORY.md` is append-ordered. Its head is `User Role`, `Requirements Snapshot 2026-05-15`,
`chop_all Echo Lines` (April); its tail is the August entries — `Publish-path authorization
2026-08-17`, `Juniper defect register 2026-08-14`, `main-verify red — RECURRING CLASS`,
`required_signatures broke runner-commit automations`, `CI waiter`, `GitHub PR CI trigger
traps`, `Validate handoff prompts independently`.

**Overflow therefore drops the most recent, most operationally relevant entries** — including
the ones that record active blockers and current traps. The failure is silent, and it is
worst-first.

That reframes urgency completely. MECH §1 establishes that `AGENTS.md` loses nothing (the cost
is tokens and attention). `MEMORY.md` **will lose data, silently, within about a month, and it
will lose the newest data.**

### 7.4 Enforcing a budget on a file outside the repo

The hard part: the file lives at `~/.claude/projects/…/memory/MEMORY.md`. **CI cannot see it.**
Three enforcement points, in the order they should be built.

**(1) A local check — primary, because it depends on nothing unverified.**

`util/memory_budget_check.py --memory-index` reports, offline, with no network and no repo
dependency:

- lines, and bytes **after** stripping frontmatter and block-level HTML comments (MECH §2 —
  a checker that does not strip will over-report by exactly the maintainer prose the mechanism
  makes free);
- both limits and the **binding** one, named explicitly — the whole §7.2 finding is that people
  read the wrong axis;
- WARN at 85 %, FAIL at 95 % of the binding axis;
- projected days-to-truncation at the trailing 30-day entry rate;
- exit 0 / 1 / 2, matching `agent_suite_doctor.py:13-14`.

Run manually, and invoked by [`scripts/wake_the_claude.bash`](../scripts/wake_the_claude.bash)
at session start as a **non-blocking** banner. Non-blocking is not timidity: a launcher that
refuses to start a session because a memory file is 96 % full is a launcher that gets edited
out within a day.

**(2) A `SessionStart` / `PreToolUse` hook — better, and unverified.** MECH §6 establishes
hooks as the deterministic enforcement mechanism but does **not** verify the event names, the
configuration schema, or the exit protocol. See §12.1. If hooks turn out to be unsuitable,
(1) stands alone and this proposal loses *timeliness*, not correctness.

**(3) Structural discipline on the index itself — the highest-leverage item, and available
today.** The index is a flat list whose mean entry is 146.7 bytes and whose longest is **791
bytes** — a single entry consuming 3.9 % of the entire budget. Three rules, checkable by (1):

| Rule | Effect |
|------|--------|
| **Per-entry cap of 120 bytes** | at 139 entries: `139 × 146.7 = 20,391` → `139 × 120 = 16,680`. **Frees 3,711 bytes ≈ 31 additional entries — nearly doubling the remaining headroom, with no entry removed.** |
| **One line per entry, no continuations** | keeps the line and byte axes proportional so §7.2's asymmetry cannot re-open |
| **Detail belongs in the topic file** | the index is an *index*; the 153 topic files are unbudgeted and free |

**(4) Eviction with a real criterion.** Same cadence as D7. `MEMORY.md`'s natural staleness
signal is stronger than `AGENTS.md`'s: an entry whose topic file has not been read or written
in 90 days **and** whose subject is marked CLOSED / RESOLVED / COMPLETE in its own text is an
eviction candidate. Several current entries advertise exactly this
(`F-P1-2 was a misdiagnosis — CLOSED 2026-08-16`, `cascor 2026-05-03 trio — RESOLVED`,
`juniper-cascor-worker _FILE indirection — RESOLVED`). Evicting an entry **does not delete the
topic file** — it removes the index line, so the knowledge remains on disk and greppable and
merely stops being resident. That is a genuinely cheap eviction, and it is the reason
`MEMORY.md` is more tractable than `AGENTS.md` despite the harder limit.

**Analysis**

**Strengths.**
- The per-entry cap alone roughly doubles remaining headroom without losing a single entry —
  the highest benefit-to-cost item anywhere in this proposal.
- Eviction here is nearly free (the topic file survives), unlike `AGENTS.md` eviction.
- The local check is offline, stdlib-only, and depends on no unverified mechanism.

**Weaknesses.**
- **No CI can enforce any of it.** Everything here is operator discipline plus a reminder. That
  is a categorically weaker guarantee than the rest of this proposal, and pretending otherwise
  would be the worst thing in the document.
- The file is written by the agent, not by a human following a convention — so the per-entry
  cap must be honoured by whatever writes the index, which this proposal cannot control.
- Doubling headroom buys ~33 more days at the current rate. It defers; it does not solve.

**Risks.**
- *Concrete scenario.* Truncation begins around 2026-09-20. Nothing announces it. Sessions
  simply stop knowing about the August entries — the defect register, the seed-reproducibility
  blocker, the CI-waiter guidance — and re-derive them, badly, at cost, while the file on disk
  looks complete and correct to any human who opens it. **The symptom of this failure is
  indistinguishable from an agent being unhelpful.**
- The 25 KB figure is documentation, and MECH §8 does not verify it against the binary. If the
  real limit is lower, truncation has already begun.

**Guardrails.**
- The session-start banner (1) makes the number visible **every session**, which is the only
  mechanism available that fires before the loss rather than after.
- A **canary entry**: a deliberately-last index line whose topic file states a unique token. If
  a session cannot recall the token when asked, truncation is confirmed empirically rather
  than inferred. This is cheap, it is the only *direct* test of the limit available to us, and
  it costs one index line — which, at the 120-byte cap, is 0.5 % of the budget for a definitive
  answer to §12.2.
- The monthly report tracks `MEMORY.md` bytes alongside `AGENTS.md`, so the two problems are
  never again reported in different places.

---

## 8. Migration path

Six phases. Each is independently shippable, independently revertible, and touches real files.
The soak-then-promote pattern follows the repo's own precedent: `Sequence Safety` ran advisory
from its introduction and was promoted to required fleet-wide in `e209b74` (#1166) — **in the
branch ruleset, never via the Quality-Gate `needs:`**.

### Phase 0 — Measure and report (advisory, zero risk)

| Adds | |
|------|--|
| `util/memory_budget_check.py` | checker: level, rate, per-section, `MEMORY.md` index; `--json`, `--strict`; exit 0/1/2 |
| `tests/test_memory_budget_check.py` | the gate for `util/`, incl. every §5.3 negative control |
| `conf/memory_budget.toml` | governed targets, units, ceilings, rate schedule, allowlists |
| `.github/workflows/memory-budget-alarm.yml` | daily report + waiver ledger + inbox depth; Slack on breach |
| CI wiring | one line in `ci.yml`'s Regression Tests run-list |

Blocks nothing. `RELEASE_TRAIN_MODE`-style kill switch: repo variable `MEMORY_BUDGET_MODE`
(`off` \| `report` \| `advisory` \| `blocking`, default `report`).
**Revert:** delete four files and one line.

### Phase 1 — Advisory PR gate + the inbox (soak)

| Adds | |
|------|--|
| `ci.yml` job `memory-budget` | `pull_request` + `merge_group`; **never** in the Quality Gate `needs:`; `merge_group` short-circuits green before checkout |
| `tests/test_memory_budget_workflow.py` | workflow lint, modelled on `tests/test_archive_guard_workflow.py` |
| `notes/memory-inbox/README.md` | the D5 contract, ~20 lines |
| `docs/REFERENCE.md` § Memory Budget Governance | the operator surface, incl. the D4 routing table |

Rate budget soaks at the **terminal** R = 5,000 (§6.2 P1). Job name carries an
`(Advisory)` suffix — the `e209b74` pre-flight note records that the suffix is part of the
context string, so **renaming the job at promotion breaks the required context**. Choose the
final name now.
**Revert:** delete the job.

### Phase 2 — Promote the rate axis to blocking

Promotion **preconditions** — and note these deliberately differ from the sequence-safety
criterion, because for a size gate "zero failures during soak" would be evidence the threshold
is useless:

1. `>=20` PR runs observed (the repo's own C2 bar is `>=5`; a gate whose *signal* is the
   failure needs more).
2. **Every advisory breach in the window was triaged** and classified as either correctly
   routed elsewhere, or a genuine resident addition that displaced something. **Zero cases of
   "no valid destination existed."** This is §5.1 turned into a merge condition — if the wall
   objection is live, this precondition fails and Phase 2 does not ship.
3. Destinations exist: the REFERENCE.md section, `notes/memory-inbox/`, and (if D4 row 4 is
   adopted) `.claude/rules/` with its `.gitignore` negation.
4. `test_memory_budget_check.py::test_synthetic_over_budget_fixture_fails` passes — the gate
   demonstrably bites.

Then: set `MEMORY_BUDGET_MODE=blocking`, R = 60,000, and promote in the **branch ruleset**.
**Revert:** flip the repo variable to `report`. No code change, no PR, no deploy.

### Phase 3 — Curation cycle

Weekly `planner`/`task-executor` pass over `notes/memory-inbox/`, opening one signed PR via
`util/open_signed_pr.py`. Adds the inbox structural guard (D5 rule 4) as an advisory `ci.yml`
job with its own tests.
**Revert:** stop scheduling; the inbox keeps accepting.

### Phase 4 — `MEMORY.md` governance

`--memory-index` wired into `scripts/wake_the_claude.bash` as a non-blocking banner; the
120-byte per-entry cap adopted; one eviction pass over CLOSED/RESOLVED entries; the canary
entry planted (§7 guardrails). **Independent of Phases 1–3** — it can and should ship first if
the ~33-day truncation estimate holds.
**Revert:** remove the banner call.

### Phase 5 — Level axis, ratchet, hooks

- `max_bytes` set to the then-current size + `LEVEL_SLACK`; ratchet rules 1 and 2 enabled.
- `.gitignore` negation for `.claude/rules/` and (if §12.1 resolves favourably)
  `.claude/hooks/` + `.claude/settings.json`; `util/install_agents.bash` extended.
- The four D6 hooks; `util/agent_suite_doctor.py` gains `check_hooks`.

**Sequencing constraint.** The level axis is inert until a companion proposal cuts the file
(§10). Phase 5 may ship before that — it simply does nothing until then, which is the correct
behaviour for a ratchet with nothing yet to hold.
**Revert:** unset `max_bytes`; delete the hooks directory.

---

## 9. What this proposal does NOT solve

Stated plainly, without hedging.

1. **It does not make `AGENTS.md` smaller.** Freezing is not shrinking. Absent a companion,
   the file sits at ~170–290 KB indefinitely and every session pays ~42,000 tokens.
2. **It does not improve the resident content.** A frozen 170 KB file is exactly as hard to
   read as an unfrozen one.
3. **It cannot govern the Cursor fleet's authoring**, only reject the result at CI — and three
   always-bypass actors can click-merge past that
   ([flood analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md):448-449).
   Whether the fleet even reads `AGENTS.md` is open question OQ3 (`:514`), still unresolved.
4. **It cannot enforce anything on `MEMORY.md` through CI.** §7.4 is a local check plus
   operator discipline. That is a categorically weaker guarantee than everything else here.
5. **It does not touch the parent ecosystem file.**
   `/home/pcalnon/Development/python/Juniper/AGENTS.md` is 11,016 bytes, MECH §7 confirms it is
   **fully additive** to every session in all nine repos — and **that directory is not a git
   repository at all** (no `.git`). It therefore has no version control, no CI, and no gate of
   any kind, and no mechanism in this proposal can reach it. The only available levers are
   MECH §4d's `claudeMdExcludes` or a local check. This is a genuine, unaddressed hole.
6. **It does not reduce the ~51 k-token always-on load by itself** (BASE §1). Only cutting
   does that.
7. **It does not address context rot within a long session** (MECH §6) — only the starting
   load.
8. **It adds process.** One directory, two CI jobs, one recurring curation, one config file,
   four hooks. Every one of those is a thing that can rot, and §5 names how each rots.

---

## 10. Dependencies on companion proposals

Which parts of Proposal D stand alone, and which do not. This is the honest accounting the
brief asks for, and it is unflattering in exactly two rows.

| Element | Stands alone? | Dependency |
|---------|---------------|------------|
| D1 **rate** axis | **Yes** | none — satisfiable today by any author |
| D1 **level** axis | **No** | inert until a companion cuts the file. Ships as a placeholder for the ratchet. |
| D2 ratchet rule 1 (monotone) | **Yes** | none |
| D2 rule 2 (anti-banking) | **No** | only fires when a cleanup PR exists — i.e. on a companion's PR |
| D2 rule 3 (rate step-down) | **Yes** | none |
| D3 waiver + ledger | **Yes** | none |
| D4 routing rows 1, 5, 7 (hook / notes / inbox) | **Yes** | none |
| D4 routing rows 2, 3, 4 (REFERENCE / skill / rule) | **Partly** | destinations exist, but the *bulk migration* into them is a companion's work. Proposal D routes marginal new content; it does not move the existing 137,627 bytes. |
| D5 inbox + curation | **Yes** | none |
| D6 hooks | **Yes** | subject to §12.1 |
| D7 eviction | **Partly** | needs destinations for evicted content (same as D4 rows 2–4) |
| §7 `MEMORY.md` | **Yes** | none — and it is the one part that ships fastest and matters soonest |

**The summary sentence.** Proposal D is a complete solution to *rate* and a partial solution to
*level*. A proposal that reorganises `AGENTS.md` is a complete solution to *level* and no
solution at all to *rate* — its work is undone in 44 days (§3.2). **Neither is sufficient; the
pair is.** If the owner adopts exactly one, adopt a cutting proposal, because 170 KB now is
worse than 290 KB later; if the owner adopts exactly one *and* expects it to still be true in
2027, adopt this one.

---

## 11. Owner decisions and open questions

Marked as decisions, not guessed at.

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| **OD-1** | Terminal `max_bytes` for `AGENTS.md` | 30,000 (§6.1) / 34,263 (BASE §8) / other | 30,000 — converges from two routes |
| **OD-2** | Rate schedule aggressiveness | §6.2 ladder / compressed / slower | as tabled; compress only after Phase 2's precondition 2 passes cleanly |
| **OD-3** | `LEVEL_SLACK` | 8,000 / other | 8,000 ≈ 2.6 days at the current rate, ≈ 16 days at R=15,000 |
| **OD-4** | Waiver alarm threshold | `MEMORY_WAIVER_ALARM` default 3/month | 3 |
| **OD-5** | Fleet-wide rollout | juniper-ml only / all nine (BASE §7) | ml first; revisit at Phase 3. canopy (94,373) and cascor (70,118) are on the same curve. |
| **OD-6** | Per-section ownership for the fleet | adopt as a Cursor-dashboard control / reject | request it as a *supplement* (flood analysis `:502-504`); do not make Proposal D depend on it |
| **OD-7** | Parent `Juniper/AGENTS.md` (§9.5) | leave / `claudeMdExcludes` / put it under version control | **decide explicitly** — it is 11,016 ungoverned additive bytes with no `.git` at all |
| **OD-8** | `MEMORY.md` per-entry cap | 120 bytes / other | 120 — frees 3,711 bytes ≈ 31 entries |
| **OD-9** | Does the `memory-budget` job name carry `(Advisory)`? | yes / no | decide **before** Phase 1: the suffix is part of the required-context string (`e209b74`) |

**Open questions.**

- **OQ-1.** Does the Cursor fleet read repo `AGENTS.md` at generation time? Open as OQ3 in the
  flood analysis (`:514`). If **no**, D4's routing procedure has no effect on the
  highest-volume writer and the gates carry 100 % of the load for that population.
- **OQ-2.** What is the true `MEMORY.md` byte limit — 25,000 or 25,600? A ~600-byte
  difference is ~4 entries and ~4 days. The canary entry (§7 guardrails) answers it empirically.
- **OQ-3.** Is the observed 1.06 entries/day for `MEMORY.md` stable, or does it track session
  volume? If the latter, §7.2's 33 days is optimistic.
- **OQ-4.** Does `docs/REFERENCE.md` have a usable size ceiling of its own, or is "read on
  demand" genuinely unbounded? D4's displacement risk depends on the answer.

---

## 12. Facts this design needs that MECH leaves unverified

Per the brief: state them, and state what breaks.

### 12.1 The hook configuration mechanism (D6, §7.4 item 2)

**What MECH establishes** (§6, T1): *"To block an action regardless of what Claude decides, use
a PreToolUse hook instead."*

**What MECH does NOT establish**, and this design would need:

- the settings key and file (`.claude/settings.json`? `settings.local.json`? user vs project scope);
- matcher syntax for tool name and argument patterns;
- the deny protocol (exit code? JSON on stdout? what the model is told?);
- whether hooks fire for **subagent** tool calls — load-bearing, since this repo runs six
  subagents ([`.claude/agents/`](../.claude/agents/));
- whether a `SessionStart`-class event exists at all (§7.4 item 2 assumes one).

**What breaks if these go the other way.**

- If hooks are **user-local only and not shareable via the repo**: D6 becomes per-operator
  configuration, `util/install_agents.bash` cannot distribute it, and the four directives stay
  prose. Cost: ~2,450 bytes not retired (1.4 % of the file) and no deterministic enforcement.
  **Nothing else in the proposal changes** — D1/D2/D3/D5 are pure CI and are unaffected.
- If hooks **do not fire for subagents**: the `/tmp/`-script rule is unenforced for exactly the
  agents most likely to write throwaway scripts. Partial mitigation: the matching CI gate.
- If there is **no `SessionStart` event**: §7.4 item 2 is void and item 1 (the launcher banner)
  stands alone. `MEMORY.md` loses timeliness, not correctness.

**Recommendation:** treat D6 and §7.4 item 2 as **contingent**, and do not let Phase 0–4 depend
on them. Phase 5 is where the contingency lands, deliberately last.

### 12.2 The `MEMORY.md` limit constant (§7)

MECH §2 quotes the docs for "200 lines or 25KB". MECH §8 does not list this among the verified
binary constants, and MECH §8.5 warns that *no Anthropic documentation page states 40,000
anywhere* — a reminder that documented and shipped constants can diverge.

**What breaks if it is lower than 25,600:** truncation has **already begun**, and §7.2's
33-day estimate is not a forecast but a post-mortem. This is the single highest-consequence
unverified fact in the document, which is why §7's guardrails include a direct empirical test
(the canary) rather than more inference.

### 12.3 The threshold formula's `r` (MECH §8.1)

MECH §8.1 marks the semantics of `Vk(e,jC())` as inferred. **Nothing in this proposal depends
on it.** Proposal D never optimises for the per-file warning (§2, non-goals), because MECH §1
consequence 1 establishes the warning is per-file and therefore gameable by splitting. Every
threshold here is a token-cost budget. If `r` is something other than the context-window size,
this document is unaffected.

### 12.4 Adherence degradation vs size (MECH §8.6)

**No published Anthropic benchmark** measures instruction-adherence degradation as a function
of CLAUDE.md size. So the claim "smaller is better" rests on documentation assertion (MECH §5)
plus general context-rot evidence (MECH §6), not on a measured curve.

**Consequence, stated rather than hidden:** §6.1's 30,000-byte terminal budget is a
*defensible* number — it converges from MECH §5's 200-line guidance and BASE §8's genre-A
residue — but it is **not an empirically optimal** one, and no one should present it as such.
If a benchmark later shows the knee is at 80 KB, the ratchet has overshot; if it shows 10 KB,
it has undershot. The ratchet's step schedule is designed to be re-tunable in
`conf/memory_budget.toml` for exactly this reason — and rule 1's monotonicity means a *loosening*
re-tune is itself a visible, waivered event.

---

## 13. Verification strategy

### 13.1 Unit and structural gates

| Test | Covers | Precedent |
|------|--------|-----------|
| `tests/test_memory_budget_check.py` | every §5.3 negative control; rate/level maths; ratchet rules 1–3; waiver parse incl. `test_waiver_requires_reason` and `test_waiver_does_not_waive_ratchet_rule_1`; `MEMORY.md` stripping + binding-axis selection; exit matrix 0/1/2 | `tests/test_release_train_archive_guard.py` — hermetic, injected diff, no network |
| `tests/test_memory_budget_workflow.py` | job present on `pull_request` + `merge_group`; **absent** from the Quality Gate `needs:`; `merge_group` short-circuit before checkout; `fetch-depth: 0`; `permissions: contents: read` | `tests/test_archive_guard_workflow.py`, `tests/test_ci_sequence_safety_hatch.py` |
| extension to `tests/test_agent_suite_doctor.py` | `check_hooks` fail-closed on absent/empty config | `DoctorDiscoveryCheckTest`, `agent_suite_doctor.py:167-186` |

All hermetic: synthetic fixture repos, injected diffs, `tests/redacted_env.py`'s `RedactedEnv`
for any subprocess environment (required by `tests/test_env_repr_safety.py`).

### 13.2 The property that matters most

**A gate that cannot fail is not a gate.** Every check ships with a synthetic case proving it
bites, in the idiom of `test_agents_md_tree_drift.py:109-112`. In review, the *first* thing to
look for in this proposal's test file is the negative controls; if they are absent or
tautological, reject the PR regardless of coverage numbers.

### 13.3 Live validation

- Phase 0: run `util/memory_budget_check.py` against real `AGENTS.md` and `MEMORY.md`;
  reconcile against BASE §1 and §3 and record any discrepancy rather than silently adopting the
  new number.
- Phase 1: after `>=20` PR runs, publish the breach distribution and the Phase-2 precondition-2
  triage. **This is the evidence that decides whether §5.1's objection is fatal.**
- Phase 4: plant the canary; confirm or refute §12.2 empirically within one session.

### 13.4 Independent cross-validation — recommended before ratification

This design proposes a **blocking** gate on the repo's hottest file, in a repo whose own memory
records that handoff documents *"inherit errors across generations"* and that three independent
validators found thirteen defects in one. Before any part of Proposal D is treated as decided,
run an independent pass specifically against:

1. every `file:line` citation in this document (the anti-hallucination sweep);
2. §3's four measurements, re-derived from [Appendix A](#appendix-a--measurement-commands) on a
   clean checkout;
3. §5.1 — whether the destinations named are genuinely sufficient, or whether the wall
   objection survives the four answers;
4. §6.3's projection arithmetic;
5. §7.2's headroom arithmetic, which is the most consequential calculation here and the one
   most likely to be wrong in a way nobody notices.

---

## Appendix A — measurement commands

All measurements in §3, §6.1 and §7 were taken in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`
at `main` = `e209b74`, clean tree, 2026-08-18. The growth curve in BASE §2 is reproducible with
[`util/ad-hoc/2026-08-18_agents_md_growth_curve.bash`](../util/ad-hoc/2026-08-18_agents_md_growth_curve.bash).

```bash
# §3.1 -- first-parent grow/shrink accounting per month.
# `git log -- AGENTS.md` without --first-parent walks both sides of every merge and
# double-counts (it reports +264,100 for July against the true +55,796); --first-parent
# is the main-line delta. size(rev) = `git cat-file -s <rev>:AGENTS.md`, compared to
# size(rev^) -- for a merge commit, ^ is the main tip before it landed.

# §3.2 -- trailing-30-day net, sampled fortnightly.
base=$(git rev-list -1 --first-parent --before=2026-07-19 main)
head=$(git rev-list -1 --first-parent --before=2026-08-18 main)
echo $(( $(git cat-file -s "$head:AGENTS.md") - $(git cat-file -s "$base:AGENTS.md") ))
# -> 92796

# §3.3 -- mandatory-language lines per H2 section (regex breadth noted in §3.3).
grep -ciE '\b(must|mandatory|never|prohibited)\b' AGENTS.md      # 124 lines
grep -oiE '\b(must|mandatory|never|prohibited)\b' AGENTS.md | wc -l   # 144 occurrences

# §6.1 -- per-section bytes. Convention: the H2 heading line through the line before
# the next H2, inclusive of intervening `---` rules. The 15 sections sum to 170,137.

# §6.1 / §7.1 -- bytes vs characters vs lines.
python3 -c 'import pathlib,sys
for a in sys.argv[1:]:
    b=pathlib.Path(a).read_bytes(); s=b.decode("utf-8")
    print(a, "bytes",len(b), "chars",len(s), "lines",len(s.splitlines()))' \
  AGENTS.md docs/REFERENCE.md
# AGENTS.md         bytes 170137 chars 168317 lines 1115   (152.6 B/line)
# docs/REFERENCE.md bytes 162231 chars 161487 lines 1865   ( 87.0 B/line)

# §7.1 -- MEMORY.md.
wc -l -c ~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md
# 139 20388
ls -1 ~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/ | wc -l
# 154  (MEMORY.md + 153 topic files)

# §D7 -- dead-referent scan: backticked path-shaped tokens in AGENTS.md that do not
# resolve in the worktree. 164 distinct tokens, 7 unresolved, all 7 false positives.
```

---

## Related documents

- [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md)
- [Claude Code memory mechanisms](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md)
- [Cursor PR flood remediation analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md)
- [notes/ file naming convention](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md)
- [Custom agent suite design](JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md)
- [Thread handoff procedure](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md)
