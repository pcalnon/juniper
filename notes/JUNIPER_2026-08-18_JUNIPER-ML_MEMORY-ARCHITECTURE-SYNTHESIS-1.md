# Shared Session Memory — Recommended Plan (Synthesis 1 of 2)

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose and standing

This is **synthesis 1 of 2**, produced independently of synthesis 2 from the same evidence
package. It is the plan I would stake the project on: what to adopt, what to reject, in what
order, with the gates that make each step verifiable and the risks that survive full execution.

**Status**: RECOMMENDED PLAN — not ratified. It proposes deleting ~89% of the file that governs
every session in this repo. It should be read against synthesis 2 and decided by the owner.

Inputs (this document does not re-derive them and must not contradict them):

| Role | Document |
|------|----------|
| Measured baseline (**BASE**) | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) |
| Verified mechanisms (**MECH**) | [`JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) |
| Proposal A — Skills | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md) |
| Proposal B — Path-scoped locality | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md) |
| Proposal C — Deduplication and pruning | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md) |
| Proposal D — Governance | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md) |
| Grounding audit (0 CRITICAL, 3 MAJOR) | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-GROUNDING-AUDIT.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-GROUNDING-AUDIT.md) |
| Arithmetic audit (2 CRITICAL, 11 MAJOR) | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ARITHMETIC-AUDIT.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ARITHMETIC-AUDIT.md) |
| Adversarial audit (0 FATAL, 20 SERIOUS) | [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ADVERSARIAL-AUDIT.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ADVERSARIAL-AUDIT.md) |

All independent re-verification for this document was done at `main` = `e209b74`, clean tree,
in worktree `.claude/worktrees/swirling-kindling-octopus`, against the installed
`juniper-ci-tools` **0.8.0** — the version `ci.yml` and `main-verify.yml` pin. Sixteen facts
were re-confirmed at source; three refinements to the audits are marked **[re-verified]** where
they change what a phase must do.

---

## 1. Decision

### 1.1 What is adopted

**A subtractive core (Proposal C) held in place by a governance ratchet (Proposal D), with a
short list of imports from B and A.** Concretely:

| Adopted | From | Why, against the evidence |
|---------|------|---------------------------|
| Delete what `docs/REFERENCE.md` and the code already say; relocate the 15,860-char unique residue; leave a ≤200-line navigational core | **C** | Worst-case session **−83.3% unconditionally** vs A −3.5% / B −0.9% (finding 5). The eager column is a 0.8-point tie; the worst case is the only axis that separates the three, and C's saving has no session-shape condition. |
| Every destination stays inside `docs/**` / `notes/**` | **C** | The docs-deletion screen's scope (`docs_additions_check.py:62-66`) covers `AGENTS.md`, `docs/**`, `notes/**` and **not** `.claude/**` (finding 4). A relocates ~101,000 chars and B ~152,900 chars out of the only content-loss alarm the repo has. C's destinations keep it. |
| The residency rule Q1/Q2/Q3 (audience / enforcement / blast radius) and the resident hazard list | **C** | It is the only residency rule in the four that survives its own counterexample — C found that `tests/test_assert_release_tag.py` runs in no workflow and made its Q2 relocation conditional on wiring it. |
| Level ceiling + ratchet (monotone ceilings; anti-banking so a cleanup PR must lower its own ceiling) | **D** | 172 of 200 merges grew the file; a cut to the core is undone in 44 days (finding 6). A level fix alone is a six-week reprieve. |
| The CI topology: standalone job, `pull_request` + `merge_group`, `merge_group` short-circuits green before checkout, **absent from the Quality Gate `needs:`**, promoted only in the branch ruleset | **D** | Verified: `required-checks` `needs:` is `[pre-commit, tests, build, docs, security, claude-yaml-audit, dependency-docs, sops-validation]` (`ci.yml:1305`) and the `sequence-safety` job documents exactly why a PR-only job must stay out of it (`ci.yml:787-794`). A/B/C all wire shared-budget gates into `Regression Tests`, which is required **and** push-triggered — a shared budget there reddens main for a state each PR was green on. |
| The vacuous-pass negative-control discipline, one control per gate, including ground-truth measurement the checker did not compute | **D** | The repo has a documented vacuous-pass class with three instances in one day. D's §5.3 is the only complete treatment in the four documents. |
| `MEMORY.md` triage: eviction pass, per-entry discipline, offline checker, canary entry | **D** | The only genuinely urgent item (§2). |
| The two-sided ledger pattern (`ENFORCED` / `KNOWN_GAP`, modelled on [`tests/test_service_fork_drift.py`](../tests/test_service_fork_drift.py)) applied to the **destination inventory** | **B** | B's best single anti-vacuous idea: with an empty input the gate fails loudly instead of passing. Applied here to "every relocated block has a named destination, or an explicit exception with a reason". |
| The MECH §8c worktree canary and merge-then-`pull --ff-only` sequencing | **B** | B is the only proposal that found it; the arithmetic audit rates it a shared Phase-0 for whichever plan wins. |
| The gate-minimal-tree reading (23-line minimum including one nested `agent_templates/` node) | **A** | A is the only proposal that read all four assertions in [`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py); B's and C's trees fail `:114-116` (finding 7). |

### 1.2 What is rejected, and why

**Proposal B is rejected outright as an architecture.** Four independent reasons, each
sufficient on its own:

1. **92% of its corpus lands in mechanisms that die at compaction.** MECH §4c-bis places both
   `.claude/rules/` with `paths:` and nested `CLAUDE.md` in the "lost until re-triggered" row;
   B's own budget puts 104,488 + 48,412 = 152,900 of 166,736 chars there. B designed for the
   pessimistic branch before it was verified, which is to its credit — but the branch is now
   verified, and its mitigation ("`Edit` requires a prior `Read`, so the rule re-fires") rests
   on whether the harness's read-tracking is conversation context or harness state, which
   nobody has probed.
2. **It exits the only content-loss alarm and calls that a benefit.** B §7.5 says "sequence-safety
   screens get quieter". Measured: `in_docs_scope('.claude/rules/experiments.md')` is `False`
   and `in_docs_scope('util/CLAUDE.md')` is `False` (`docs_additions_check.py:62-66`). Quieter
   is silent, for 92% of the corpus, permanently, in a repo with 23 concurrent worktrees.
3. **Its riskiest deletion is guarded by a gate that cannot fire.** B Phase 1 deletes ~6,120
   chars on the strength of the parent `Juniper/AGENTS.md` carrying them; the guardrail is a
   cross-repo drift test biting "weekly in `docs-full-check.yml`". **[re-verified]**
   `/home/pcalnon/Development/python/Juniper/.git` does not exist, so there is no repo to clone
   and the test can only ever take its skip path (finding 8).
4. **It buys −0.9% of content and −0.9% in the worst case**, and B+D cancel (finding 11): D's
   rate axis would govern a file that no longer contains the growth.

Two artifacts are salvaged from B (the two-sided ledger; the §8c canary). The rest is not.

**Proposal A is rejected as the primary architecture, and deferred as an optional follow-on.**

- Its thesis rests on a fact with **zero in-repo precedent**: all three shipped skills set
  `disable-model-invocation: true` and three lints assert it. The grounding audit re-extracted
  the binary constant and confirms the default is model-invocable; nobody has observed it here.
- Its worst case is **−3.5%** with a 4.4-percentage-point margin that depends on an unmeasured
  23.1% compression of 145,675 chars. At zero compression the worst case is **+14.9% worse than
  today**. That is a plan, not a property.
- It relocates ~101,000 chars outside the docs screen (reason 2 above applies).
- **A + C compound**: two claimants (skill body, `docs/REFERENCE.md`) on the same subjects
  reproduces the circular-authority pathology A itself diagnoses.

A's Phase 0 probe (does a model-invocable skill auto-invoke here?) is worth running as an
independent half-day experiment (**OD-8**) because the answer is useful to any future design.
It is not on this plan's critical path.

**Proposal D's rate axis is rejected as a blocking gate; adopted as report-only.**
`strict_required_status_checks_policy: true` is live on the ruleset (verified). With 23
worktrees, the act required to merge — update your branch — pulls other people's merges into a
30-day rolling window and can break the required check the author cannot repair. The overrun
"loan" then bills every in-flight PR at once, and >1 waiver freezes the ratchet through D's own
step-down interlock. The **level** axis is deterministic per-commit and has none of this
behaviour; it becomes the blocking one.

**Proposal D's inbox (D5) is deferred, not adopted.** `notes/memory-inbox/` is inside the docs
screen's scope, so every weekly curation PR deletes files under a required check and needs a
waiver; the cheapest form is `Allow-Docs-Rewrite: *`, which is accepted and waives *every*
deleted `.md` in the window — manufacturing a weekly habit of the exact reflexive waiver D
identifies as its own failure mode. Revisit at Phase 7 (**OD-3**) if the soak shows capture
being lost.

### 1.3 The load-bearing tradeoff I am accepting

**I am trading guaranteed availability of component lore for guaranteed, unconditional context
reduction, and I am buying back only part of that guarantee with a resident hazard list.**

Today an agent knows the reaper's live-experiment protection rule without asking. After this
plan it must decide to read `docs/REFERENCE.md`. Nobody can measure that follow rate; MECH §8
item 6 records that no published benchmark measures adherence against memory size either. The
file's own history is evidence *against* pointers: 32 `AGENTS.md` lines already end by pointing
at the `docs/REFERENCE.md` section holding the same material, and their authors wrote the
pointer **and** the summary.

I accept the trade for three reasons:

1. The alternatives that preserve automatic availability buy it with mechanisms that vanish at
   compaction (A partly, B almost entirely) and with destinations outside the only content-loss
   alarm.
2. The index-over-deferred-corpus pattern is **already running in this project at 53:1** —
   154 auto-memory files, 1,082,901 bytes on disk, 20,388 loaded (MECH §8b). It is not
   speculative here.
3. The residency rule keeps every irrecoverable-consequence directive resident, and §6's soak
   (N ≥ 20, transcript-observable) is a pre-declared falsification test with a rollback ladder
   that is **not** "re-inline".

What I am not trading away: nothing in this plan places safety-critical content in a mechanism
that silently disappears. The resident core is the project-root file, which MECH §4c-bis says
is **re-injected** after compaction.

---

## 2. Sequencing — two clocks, running at different speeds

| Clock | Reading | Consequence of being late |
|-------|---------|---------------------------|
| **`MEMORY.md`** | 20,388 of 25,000 bytes; 4,612 headroom; recent entries 234.8 B ⇒ **≈20 entries, ≈19 days** | **Silent, irreversible, newest-first data loss.** Re-verified: 139 entries, 20,388 B, oldest-20 134.4 B/entry, newest-20 234.8 B/entry. |
| **`AGENTS.md`** | 168,317 chars = 4.21× the 40,000 per-file **warning** floor | Tokens and attention. **Nothing is truncated** (finding 1). |
| **The rate** | 172 of 200 merges grew the file; a cut to the core is undone in **44 days** | A level fix without a rate fix is a six-week reprieve (finding 6). |

Three ordering rules follow, and they are binding:

1. **`MEMORY.md` goes first and is independent of everything else.** It touches no repo
   markdown, needs no canary, and its deadline is inside three weeks. Do not fold it into the
   `AGENTS.md` work; that is how it gets deferred again.
2. **The ratchet must be live *during* the cuts, not after.** The interlock that achieves this
   is D's anti-banking rule: the ceiling ships at today's value (inert, green) in Phase 2, and
   **every cutting phase lowers its own ceiling in the same PR**. There is never a window in
   which a cut exists without a ceiling holding it.
3. **Destinations land before deletions.** Phase 3 writes the six new `docs/REFERENCE.md`
   sections additively; Phases 4–6 then delete. This is mechanically enforced by the relocation
   check (§6 G3), not left to discipline.

---

## 3. The pre-migration canary (MECH §8c) — gates the ordering of every cutting phase

MECH §8c: the main checkout's `juniper-ml/CLAUDE.md` **is** a filesystem ancestor of
`.claude/worktrees/<name>/`, so §4c predicts it loads eagerly — and it does not. Two hypotheses
fit, and they diverge exactly during migration:

- **H-a (content dedup):** the ancestor *is* walked; the two files are byte-identical today
  (re-verified: `md5sum` matches) so one copy is suppressed. The moment a worktree carries a
  trimmed `AGENTS.md` while main carries the 170K original, **both** load. Under this plan the
  transient cost is `18,007 + 168,317 = 186,324` chars — **+10.7% worse than today**, and it
  would look like the plan backfiring on its first PR.
- **H-b / H-c (walk stops at a boundary, or the path is excluded):** no hazard.

### 3.1 The probe, with the correction that matters

B §13.5 proposes an **HTML-comment** canary. **Do not use one.** MECH §4d records that
block-level HTML comments are stripped before injection, so an ABSENT result would conflate
"the ancestor is not loaded" with "the comment was stripped" — a false H-b in the dangerous
direction. Use a plain-text line.

```bash
# 1. POSITIVE CONTROL first -- prove the probe can see a marker at all.
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<name>
printf '\nJUNIPER-MEMORY-CANARY-LOCAL-20260818\n' >> AGENTS.md
claude -p "Reply exactly CANARY-PRESENT if JUNIPER-MEMORY-CANARY-LOCAL-20260818 appears \
anywhere in your project instructions, otherwise reply exactly CANARY-ABSENT."
git checkout -- AGENTS.md      # must have answered CANARY-PRESENT

# 2. THE PROBE -- marker in the MAIN checkout only, uncommitted.
cd /home/pcalnon/Development/python/Juniper/juniper-ml
printf '\nJUNIPER-MEMORY-CANARY-ANCESTOR-20260818\n' >> AGENTS.md
cd .claude/worktrees/<name>
claude -p "Reply exactly CANARY-PRESENT if JUNIPER-MEMORY-CANARY-ANCESTOR-20260818 appears \
anywhere in your project instructions, otherwise reply exactly CANARY-ABSENT."

# 3. Undo, unconditionally.
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git checkout -- AGENTS.md
```

**Step 1 is the negative control for the probe itself**: without it, `CANARY-ABSENT` in step 2
is indistinguishable from "the session did not answer the question". A gate that cannot
demonstrate it can fire is not a gate — this repo has three recorded instances of that class in
a single day.

### 3.2 What each outcome changes

| Outcome | Meaning | Binding consequence |
|---------|---------|---------------------|
| Step 1 `CANARY-ABSENT` | The probe is broken | Stop. Do not interpret step 2. |
| Step 2 `CANARY-PRESENT` | **H-a** — the ancestor is walked and dedup was hiding it | Merge-then-pull ordering is **mandatory** for Phases 4, 5 and 6: land the PR on `main`, then immediately `git -C <main-checkout> pull --ff-only origin main` **before** creating the next worktree. |
| Step 2 `CANARY-ABSENT` | **H-b / H-c** — the ancestor is skipped | No hazard. Adopt the same ordering anyway; it costs one command and is already mandated as Phase 7 of the worktree-cleanup procedure. |

Record the result in this document's §7 as **OD-0** before Phase 4 begins. Do not proceed to a
cutting phase on an assumption.

---

## 4. Target budget, in characters

Basis: **168,317 characters** (`wc -m AGENTS.md`, re-verified), which is what the shipped
per-file check measures (`s.content.length`). The three largest sections are 99,304 + 20,469 +
16,101 = **135,874**, so the genre-A residue is `168,317 − 135,874` = **32,443** (the corrected
figure; BASE's original 34,263 subtracted characters from bytes).

32,443 is an **upper bound**, not the target: 11,962 chars of genre B survive inside it —
`## Publishing` 3,641, `## Shared Observability Helpers` 1,495, `## Shared Service-Core
Contracts` 3,512, and the 3,314-char "Run all tests" block inside `## Build & Package Commands`.

| Section (current chars re-verified) | Now | Target | Basis for the target |
|---|---:|---:|---|
| header block | 331 | **331** | verbatim — three gates read it |
| `## What This Is` | 596 | 400 | condense |
| `## Build & Package Commands` | 4,617 | 1,200 | drop the 3,314-char run-all-tests block (already 54-of-88 and stale); keep build / install / pre-commit |
| `## Publishing` | 3,641 | 700 | the mandatory Release-not-bare-tag convention + one pointer |
| `## Shared Observability Helpers` | 1,495 | 200 | pointer |
| `## Shared Service-Core Contracts` | 3,512 | 400 | four one-line security invariants + pointer |
| `## Repository Structure` | 20,469 | 1,100 | gate-minimal tree: fence + root + `├── AGENTS.md` + 18 dir nodes + one nested `agent_templates/` node = 23 lines minimum |
| `## Key Files` → `## Where To Look` | 99,304 | 2,200 | ~14 task-shaped routing rows + catch-all |
| `## CI/CD Pipelines` | 16,101 | 900 | the 15 required context names + the `RELEASE_TRAIN_MODE` kill switch |
| `## Pre-commit Hooks` | 2,085 | 600 | the three load-bearing scope facts |
| `## Secrets Management (SOPS)` | 492 | **492** | verbatim |
| `## Ecosystem Context` | 2,315 | 600 | ports + pointer |
| `## Conventions` (incl. `### Script placement (mandatory)`) | 2,484 | **2,484** | verbatim — genre A, and the heading is an anchor target (§5.4) |
| `## Pull Request Conventions` | 2,842 | 1,100 | verb table + scope |
| `## Worktree Procedures` | 4,159 | 1,400 | rules + when-to-use table + the two `notes/` pointers |
| `## Thread Handoff` | 3,874 | 1,500 | triggers + rules + pointer |
| **NEW** `## Traps With No Gate` | 0 | 2,400 | the resident hazard list (§5.6) |
| **TOTAL** | **168,317** | **18,007** | **−150,310 (−89.3%)** |

Cross-check: the residue goes `32,443 → 11,407` (−64.8%); the three big sections go
`135,874 → 4,200` (−96.9%); plus 2,400 new. `11,407 + 4,200 + 2,400 = 18,007`.

**Always-on context.** Verified components: `~/.claude/CLAUDE.md` 3,341 chars, parent
`Juniper/CLAUDE.md` 10,818 chars (both eager and untouched by this plan), `MEMORY.md` 20,049
chars (a separate subsystem).

| | Before | After |
|---|---:|---:|
| Eager memory files | 182,476 | **32,166** |
| Eager Δ | — | **−82.4%** |
| Incl. `MEMORY.md` | 202,525 | 52,215 |
| At 4 chars/token, % of a 200k window | 25.3% | **6.5%** |

**Ceiling and slack.** Terminal ceiling **24,000 chars / 260 lines**; `LEVEL_SLACK` = 6,000
chars (`24,000 − 18,007 = 5,993`); WARN at 21,000 / 230. 6,000 chars is ≈ 6 mean growing merges
at the measured +972 B/merge — enough notice to route rather than to panic, tight enough that
the ceiling follows a cleanup down. The slack constant is itself under the monotonicity rule, so
raising it is a ratchet violation. **OD-1** offers a tighter alternative.

---

## 5. Phases

Nine phases. Each is one PR, independently shippable, independently revertible, and **CI-clean
as written**. Every phase that trips the docs screen names its trailer.

### 5.0 The waiver rule that applies to Phases 4, 5 and 6

**[re-verified]** The docs screen FAILs only on (a) a deleted markdown heading with no heading
added in the same hunk, or (b) `added == 0 and deleted >= min_run` (`docs_additions_check.py:194`
and `:196`, default `min_run = 5` at `:56`). Everything else is `small-deletion / WARN`, and
WARN never fails.

Two consequences the plan must absorb:

- **Hunk boundaries are not author-controlled.** A phase that keeps a heading and adds a pointer
  line *may* land the pointer in a different hunk from the deletion, flipping WARN to FAIL. So
  Phases 4–6 declare the trailer regardless of the predicted classification.
- **`main-verify.yml:196` re-runs the screen post-merge over `BASE..<merge>` with no `|| true`.**
  A trailer that does not survive the squash reddens `main`. **Carry
  `Allow-Docs-Rewrite: AGENTS.md` into the squash commit message.**

Two hard rules:

- **Enumerate, never wildcard.** `Allow-Docs-Rewrite: *` is accepted and waives *every* deleted
  `.md` in the screened range (`docs/REFERENCE.md:826`), which post-merge is a window of merges
  — it would waive other people's deletions. Always `Allow-Docs-Rewrite: AGENTS.md`.
- **The PR label is not the waiver.** The `docs-rewrite` label only demotes the advisory per-PR
  job to WARN-only and is invisible to `main-verify` (`docs/REFERENCE.md:828`).

The trailer is a *classification* waiver, never a *loss* waiver. The 2026-08-18 lesson stands:
a net −4-line reflow destroyed 116 tokens of owner decisions and was nearly waived as cosmetic;
the fix was restoration (ml#1165), not a waiver. §6 G3 makes "prove it was relocated" mechanical
rather than conventional.

### Phase 0 — `MEMORY.md` triage *(no `AGENTS.md` change; the ~19-day fuse)*

Ships:

- `util/memory_index_check.py` — offline, stdlib-only. Reports lines, and bytes **after**
  stripping frontmatter and block-level HTML comments (MECH §2), both limits, the **binding**
  axis named explicitly, and projected days-to-truncation at the trailing entry rate. WARN at
  85%, FAIL at 95% of the binding axis; exit 0/1/2 matching
  [`util/agent_suite_doctor.py`](../util/agent_suite_doctor.py).
- `tests/test_memory_index_check.py` — the gate (`util/` is outside every pre-commit Python
  hook's scope).
- A **non-blocking** banner call from [`scripts/wake_the_claude.bash`](../scripts/wake_the_claude.bash).
  Non-blocking is deliberate: a launcher that refuses to start a session gets edited out.
- One eviction pass. **[re-verified] 35 of 139 index entries carry a CLOSED / RESOLVED /
  COMPLETE / SHIPPED / REFUTED marker and total 5,471 bytes** — more than the entire 4,612-byte
  headroom. Eviction removes the *index line only*; the topic file stays on disk and greppable,
  which is why `MEMORY.md` is more tractable than `AGENTS.md` despite the harder limit. Expect a
  conservative pass to take roughly half; even half moves the horizon from ≈19 to ≈29 days.
- One **canary entry**: a deliberately-last index line whose topic file states a unique token.
  If a session cannot recall it when asked, truncation is confirmed empirically rather than
  inferred. This is the only direct test of the 25,000 constant available.

Per-entry cap: **[re-verified]** a 120-byte cap frees 3,873 bytes but requires rewriting **113
of 139** entries; a 150-byte cap frees 1,892 by rewriting **20**. Recommend 150 as a stated
discipline in the resident core, not a rewrite campaign (**OD-9**).

*CI*: additive only. **PASS, no trailer.**
*Rollback*: `git revert`; delete two files and one banner call. The evicted index lines are
recoverable from git only for the checker — the `MEMORY.md` edit itself is outside the repo, so
**snapshot `MEMORY.md` to `notes/` before the eviction pass** and record the snapshot path in
the PR body.

### Phase 1 — Verification prerequisites *(no `AGENTS.md` change)*

Ships:

- **The §8c canary**, run and recorded as OD-0.
- **The wired-gate lint** (`tests/test_every_test_is_wired.py`): every `tests/test_*.py` is
  referenced by at least one `.github/workflows/*.yml`, with a two-sided `UNWIRED` ledger.
  **[re-verified] `tests/test_assert_release_tag.py` is the sole violation among 88 modules.**
  It ships in the ledger with a reason and a link to the separately-filed issue — this plan does
  not fix that defect (out of scope), it makes the *premise* verifiable. Three of the four
  proposals route content on the assumption that "a wired gate holds this"; without this lint
  that assumption is unchecked.
- **The relocation checker** (`util/memory_relocation_check.py`, §6 G3) at block granularity,
  plus its tests.
- **The anchor-inventory check** (§6 G4).

*CI*: additive only. **PASS, no trailer.**
*Rollback*: delete four files and their `ci.yml` run lines.

### Phase 2 — Governance skeleton, report-only *(no `AGENTS.md` change)*

Ships:

- `conf/memory_budget.toml` — governed targets (an explicit list, never a glob), units declared
  per target (**characters** for the CLAUDE.md family, **bytes** for `MEMORY.md`), ceilings set
  to **today's values** so it is green on merge.
- `util/memory_budget_check.py` + `tests/test_memory_budget_check.py` with every §6 negative
  control.
- `tests/test_agents_md_shape.py`, **report-only** in this phase.
- A standalone `memory-budget` job in `ci.yml` on the archive-guard shape: `pull_request` +
  `merge_group`, `merge_group` short-circuits to a green notice before any checkout,
  `permissions: contents: read`, never path-filtered (a required context that never reports is
  never satisfied), and **absent from the Quality Gate `needs:`**.
- `tests/test_memory_budget_workflow.py`, modelled on the existing
  `tests/test_archive_guard_workflow.py`.
- `docs/REFERENCE.md` § Memory Budget Governance — the operator surface and the routing table.
- The rate axis: **report-only, permanently** (§1.2). Reported side by side with
  `docs/REFERENCE.md` and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` so displacement is visible in
  one table.

*CI*: additive only. **PASS, no trailer.**
*Rollback*: set the repo variable `MEMORY_BUDGET_MODE=off`; no code change. Or revert the PR.

### Phase 3 — Write the destinations *(additive to `docs/` only)*

Six new `docs/REFERENCE.md` sections, 11,443 chars, for the subjects with no existing section:
`util/wait_for_checks.py` (3,632), `util/release_train/ceremony.py` (2,780),
`util/open_signed_pr.py` (1,527), `util/assert_release_tag.bash` (1,430),
`util/experiments/run_suite.py` (1,048), `util/release_train/notes_render.py` (1,026). Plus a
`docs/DOCUMENTATION_OVERVIEW.md` "I Want To" row for each (that table currently has 33 rows).

**`util/assert_release_tag.bash` must be derived from source, not copied.** The `AGENTS.md`
entry documents `--ref-type` / `--ref-name`; the script parses `--ref` (finding 12). Copying the
entry propagates the defect into the new authority.

**Route to `docs/REFERENCE.md` by default.** C routes 4,417 chars to module docstrings; prefer
`docs/REFERENCE.md` for anything on the hazard list, because a `.py` docstring is inside neither
the docs screen (`in_docs_scope` is `False` for `.py`) nor the symbol screen (a docstring is not
a `def`). Docstrings are a supplement, never the sole home for a hazard.

*CI*: additive only. **PASS, no trailer.**
*Rollback*: `git revert`. Nothing depends on it yet.

### Phase 4 — Retire `## Key Files` and `## Repository Structure` *(−116,473 chars)*

`## Repository Structure` 20,469 → 1,100 (gate-minimal tree). `## Key Files` 99,304 → 2,200
(`## Where To Look`). Sequence within the phase: (a) move the ~12 test rationales into their
test modules' docstrings; (b) delete `### Utilities`, `### Tests`, `### CI/CD Workflows`,
`### Package and Metadata`, `### Documentation`, `### Scripts and Launchers`,
`### Configuration`; (c) add `## Where To Look`; (d) leave HTML-comment tombstones naming each
destination (free — stripped before injection, MECH §4d; and the size gate counts them anyway,
so a wrong strip fact costs bytes, never a broken gate).

**Lower the ceiling to 58,000 chars in the same PR** (post-phase ≈ 51,844 + 6,000 slack).

*CI*: **deletes H3 headings → FAIL.** Requires `Allow-Docs-Rewrite: AGENTS.md`, **carried into
the squash commit**, plus the §6 G3 relocation report attached to the PR body. Tree gate: the
new tree must retain one nested `agent_templates/` node or
`tests/test_agents_md_tree_drift.py:114-116` fails.
*Rollback*: `git revert` restores the exact prior bytes; the Phase-3 destinations remain and are
harmless duplicates until re-attempted.

### Phase 5 — Retire the remaining genre-B sections *(−25,966 chars)*

`## CI/CD Pipelines` 16,101 → 900; `## Build & Package Commands` 4,617 → 1,200;
`## Publishing` 3,641 → 700; `## Shared Service-Core Contracts` 3,512 → 400;
`## Shared Observability Helpers` 1,495 → 200.

**Lower the ceiling to 32,000 chars in the same PR** (post-phase ≈ 25,878 + 6,000).

*CI*: `## CI/CD Pipelines`' H3 subsections are deleted → **FAIL**. Requires
`Allow-Docs-Rewrite: AGENTS.md` + squash-carry + the G3 report.
*Rollback*: `git revert`; the ceiling reverts with it because both live in the same commit.

### Phase 6 — The resident core *(−7,871 net)*

Trim `## What This Is`, `## Pre-commit Hooks`, `## Ecosystem Context`,
`## Pull Request Conventions`, `## Worktree Procedures`, `## Thread Handoff` to the §4 budget;
add `## Traps With No Gate`; add the destination rule to `## Conventions`; add the routing line
to [`.github/pull_request_template.md`](../.github/pull_request_template.md) and to the three
`planner` / `auditor` / `task-executor` prompts under `.claude/agents/`.

**Anchor constraint (binding).** **[re-verified]** `### Script placement (mandatory)`
(`AGENTS.md:904`) has **six** live inbound references — four in top-level `notes/*.md`, one in
[`util/ad-hoc/README.md`](../util/ad-hoc/README.md), one intra-file at `AGENTS.md:500` — and
`Documentation Links` is a **required** status check that resolves anchors
(`check_doc_links.py:293`). **Keep the heading text byte-identical.** By contrast the two
references to `#worktree-procedures-mandatory--task-isolation` are both in `notes/legacy/`,
which the CI invocation excludes (`ci.yml:1083`) — so that heading is not CI-gating, but there
is no reason to retitle it either. General rule: **no surviving heading may be retitled, and
every deleted heading must have zero live inbound anchors**, checked mechanically by §6 G4.

**Lower the ceiling to the terminal 24,000 chars / 260 lines in the same PR** and promote
`tests/test_agents_md_shape.py` from report-only to blocking.

*CI*: `## Worktree Procedures` and `## Thread Handoff` carry H3 subsections that are deleted →
**FAIL**. Requires `Allow-Docs-Rewrite: AGENTS.md` + squash-carry + the G3 report.
*Rollback*: `git revert`.

### Phase 7 — Turn on the ratchet and promote *(config only)*

- Enable ratchet rule 1 (monotone ceilings in `conf/memory_budget.toml`, waivable only by an
  `Allow-Budget-Raise:` trailer with a mandatory free-text reason) and rule 2 (anti-banking:
  `ceiling − actual <= LEVEL_SLACK`).
- Promote the `Memory Budget` context to **required in the branch ruleset** — never via the
  Quality Gate `needs:` — after ≥20 observed PR runs and a triage showing zero cases of "no
  valid destination existed".
- Choose the job name **now**: the suffix is part of the required-context string, so renaming at
  promotion breaks the required context.
- Run the §6 soak and publish its result.

*CI*: config only. **PASS, no trailer.**
*Rollback*: `MEMORY_BUDGET_MODE=report` (repo variable) — no code change, no PR, no deploy. If
the ruleset promotion has happened, remove the context from the ruleset.

### Phase 8 — Fleet *(per-repo, after Phase 7's soak)*

**The gates port; the prune does not.** Copy `tests/test_agents_md_size_budget.py` and
`tests/test_agents_md_shape.py` into the eight siblings using the self-locating idiom documented
in [`tests/test_agents_md_header_schema.py`](../tests/test_agents_md_header_schema.py), with
per-repo ceilings set to *current* size and ratcheted down as each repo is pruned. canopy
(94,373 B) and cascor (70,118 B) each need their own overlap analysis first (§9).

*CI*: additive per repo. **PASS, no trailer** — unless a repo's own prune lands in the same PR,
which it must not.
*Rollback*: per repo, `git revert`.

---

## 6. Guardrails — each with a negative control

The repo has a documented vacuous-pass class: a check whose machinery breaks and reports
SUCCESS, three instances in one day. **Every gate below ships with a synthetic case proving it
can fail**, in the idiom of `tests/test_agents_md_tree_drift.py:109-112`
(`test_checker_flags_a_missing_dir`). In review, look at the negative controls first; if they
are absent or tautological, reject the PR regardless of coverage.

| # | Guardrail | What it protects | **Negative control** |
|---|-----------|------------------|----------------------|
| **G1** | `tests/test_agents_md_size_budget.py` — hard fail above 24,000 chars **or** 260 lines; warn at 21,000 / 230. Dual axis, because a chars-only gate invites 400-char lines and a lines-only gate invites long ones. | The level | A fixture 1 char over must **FAIL** and one exactly at the ceiling must **PASS**; plus `test_measured_size_matches_ground_truth` comparing the checker's count against `len(Path("AGENTS.md").read_text())` — **a checker must be tested against ground truth it did not compute**. |
| **G2** | `tests/test_agents_md_shape.py` — forbids the measured accretion mechanism: no list item nested two or more levels deep, no `#NNN` issue citations, no `Operator surface:` trailers in the core. | The **rate** | A synthetic file with one depth-2 bullet must **FAIL**; a file with only depth-1 bullets must **PASS**. Without both arms the gate is a no-op on an empty file. |
| **G3** | `util/memory_relocation_check.py` — **block** granularity, not token. For each heading and each contiguous content block removed from `AGENTS.md` in the PR, assert a normalized match exists at a **named destination path at HEAD**; emit the destination ledger as the required PR artifact. | Content loss during migration | A synthetic PR that deletes a block and relocates only its **identifiers** (not its prose) must **FAIL**. This is the exact counterexample that defeats a token-level check: `util/wait_for_checks.py` scores 86% on tokens *because the identifiers are in its docstring*, while the insight ("`stalled` means further polling cannot change the answer") is paraphrase and invisible to a token match. |
| **G4** | Anchor-inventory check — for every heading removed in the PR, zero live inbound `AGENTS.md#<slug>` references from non-excluded paths (`ci.yml:1082-1088` names the exclusions). | The required `Documentation Links` context | A synthetic removal of `### Script placement (mandatory)` must **FAIL** naming all six referrers; removal of a heading with zero referrers must **PASS**. |
| **G5** | `tests/test_every_test_is_wired.py` — every `tests/test_*.py` referenced by ≥1 workflow, two-sided `UNWIRED` ledger. | The premise that "a wired gate holds this lore" | It has exactly **one** real violation today (`test_assert_release_tag.py`), which serves as the live positive case; plus a synthetic module absent from every workflow and from the ledger must **FAIL**, and an entry left in the ledger after it *is* wired must also **FAIL** (so the ledger cannot rot into a list of things that used to be true). |
| **G6** | `tests/test_memory_budget_check.py` — the ratchet | Permanence | `test_cleanup_without_ceiling_drop_fails` (rule 2's entire purpose is unverified without it); `test_slack_increase_is_a_ratchet_violation`; `test_target_list_is_explicit_and_nonempty` (zero targets is FAIL, never OK); `test_unresolvable_baseline_raises` (exit **2**, never an `or 0` coercion — the release-train `_gh_lines` `or []` class); **`test_governed_target_is_agents_md_not_the_symlink`** — `CLAUDE.md` is byte-identical to `AGENTS.md` today, so a gate measuring the symlink passes identically and diverges silently later (make the "currently identical" half a warning, so the legitimate day someone replaces the symlink is not a red). |
| **G7** | `tests/test_memory_index_check.py` | `MEMORY.md` | A 24,999-byte fixture **PASSES** and a 25,001-byte fixture **FAILS**; the frontmatter / HTML-comment strip is asserted against a fixture that contains both; the binding-axis selection is asserted in both directions (a 199-line / 26,000-byte file must report **bytes** binding; a 201-line / 10,000-byte file must report **lines**). |
| **G8** | `tests/test_memory_budget_workflow.py` | CI topology | Asserts the job is present on `pull_request` **and** `merge_group`, **absent** from the Quality Gate `needs:`, short-circuits before checkout on `merge_group`, and carries `permissions: contents: read`. Negative control: a synthetic workflow with the job listed in `needs:` must **FAIL**. |

Two properties that hold across the set:

- **Never vacuous by reporting.** The `memory-budget` job always writes the current sizes to the
  step summary whether or not anything breached — the contract already used by
  [`.github/workflows/pr-budget-alarm.yml`](../.github/workflows/pr-budget-alarm.yml). A gate
  that reports its input every run cannot silently measure nothing.
- **`util/` is the gate's own blind spot.** Every checker lives in `util/`, which is outside all
  five pre-commit Python hooks, so the unittest **is** the gate — the same reason
  `tests/test_template_library_drift.py` had to be wired explicitly.

### 6.1 The behavioural soak — the only honest test of §1.3

Mechanical gates prove the bytes moved. They cannot prove an agent still finds them.

- **Population**: the next **N ≥ 20** real component-touching tasks, not synthetic prompts. (The
  project's own standing method rule: on a stochastic effect, report rates over N ≥ 20.)
- **Metric**: did the session open the relocated destination before editing the component?
  Observable in the transcript.
- **Pass bar (owner, OD-6)**: recommended ≥80%, with **zero** incidents in which a session
  contradicted a relocated contract.
- **On failure, the ladder — and it is not "re-inline"**: (a) add the missing `## Where To Look`
  row; (b) wire the pinning gate; (c) only then consider a path-scoped rule, accepting that it
  imports the compaction exposure that got B rejected.

---

## 7. Owner decisions

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| **OD-0** | The §8c canary result | H-a / H-b / H-c | Run it in Phase 1 and record the answer here. **Adopt merge-then-`pull --ff-only` ordering regardless** — it costs one command and is already Phase 7 of the worktree-cleanup procedure. |
| **OD-1** | Terminal ceiling and slack | 24,000 chars / 260 lines, slack 6,000 · or 20,000 / 220, slack 2,000 | **24,000 / 260 / 6,000.** The tighter option is crossed by ~2 mean merges and turns the gate into a nuisance; the rate control is G2, not a tight ceiling. |
| **OD-2** | The rate axis | report-only forever · blocking after soak | **Report-only forever.** `strict_required_status_checks_policy: true` plus 23 worktrees makes a rolling-window required gate a deadlock: the act required to merge is the act that breaks the check. |
| **OD-3** | The `notes/memory-inbox/` capture mechanism | adopt now · defer · reject | **Defer to Phase 7.** It trips the required docs screen weekly and trains the wildcard waiver. Revisit only if the §6.1 soak shows capture being lost. |
| **OD-4** | `claudeMdExcludes` for the parent | adopt · decline | **Decline.** 10,818 chars for an exclusion predicate MECH §8 item 3 lists as unconfirmed, a nine-repo blast radius, and — decisively — the setting would have to live somewhere that reaches worktrees, which today it does not (see OD-7). Treat the bytes as unbanked. |
| **OD-5** | Put `/home/pcalnon/Development/python/Juniper/` under version control | own repo · vendored snapshot + drift test in juniper-ml · leave | **Own repo, with the same four `AGENTS.md` gates.** 11,016 additive bytes, nine repos, no history, no diff, no revert, no CI. Not a blocker for Phases 0–8 — this plan deliberately deletes *nothing* on the parent's strength — but it is the largest ungoverned surface in the ecosystem. |
| **OD-6** | Soak pass bar and rollback trigger | ≥80% / other | **≥80% with zero contradicted-contract incidents**, ladder as §6.1. |
| **OD-7** | The settings asymmetry | do nothing · track a project `.claude/settings.json` | **Do nothing for this plan** — nothing here depends on settings. If hooks are ever adopted, note that `.claude/settings.json` is gitignored by `.gitignore:177`, that the main checkout has an active `settings.local.json` (1,801 B) which worktrees do not inherit, and that a settings file also carries **permissions**, so it must be owner-authored. |
| **OD-8** | Run A's model-invocable-skill probe as an independent experiment | yes · no | **Yes, off the critical path.** Half a day, revertible by deleting one directory, and the answer is useful to any future design. |
| **OD-9** | `MEMORY.md` per-entry discipline | 120-byte cap · 150-byte cap · none | **150 bytes as a stated discipline, not a rewrite campaign.** 120 frees 3,873 bytes but touches 113 of 139 entries; 150 frees 1,892 by touching 20. The eviction pass (5,471 bytes of candidates) is the real lever. |

---

## 8. Residual risk after full execution

Stated plainly.

1. **The pointer-follow rate is still unmeasured, and the migration is irreversible in
   practice.** A `git revert` restores the bytes; it does not restore six weeks of sessions that
   worked without the lore. The soak is a *detector*, not a preventer.
2. **The parent `Juniper/AGENTS.md` is untouched** — 11,016 additive bytes across nine repos,
   no VCS, no CI, no gate. After this plan it is **34%** of the eager budget. OD-5 names the fix;
   this plan does not deliver it.
3. **`MEMORY.md` is deferred, not solved.** Eviction plus discipline roughly doubles the fuse
   (≈19 → ≈29 days on a conservative pass). Nothing in CI can ever enforce it: the file is
   outside the repository. The banner and the canary are the whole mechanism.
4. **Post-migration deletion of the *destinations* is WARN-only.** `docs/REFERENCE.md` is inside
   the docs screen, so a whole-section deletion FAILs on the heading rule — but a sub-block
   deletion with a pointer added is `small-deletion / WARN` at any magnitude. G3 runs on
   migration PRs; after Phase 6 the relocated corpus has heading-level protection only.
5. **Nothing here enforces anything.** MECH §6: memory content is delivered as a user message
   with "no guarantee of strict compliance". The 14 resident hazards remain advisory. Hooks
   would change that and are contingent on a configuration schema MECH does not verify.
6. **`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` is the displacement target** — 158 commits since
   2026-06-01, 64,267 chars, no size or shape gate. It costs no tokens (read on demand), so
   gating it would be enforcing the wrong thing; this plan **reports** its rate beside the
   governed file so gaming is visible, and does nothing more.
7. **`docs/REFERENCE.md` grows faster than `AGENTS.md` did** (16,008 → 162,231 bytes since
   2026-06-01; 6,064 B/day in August). This plan actively directs content there. On-demand
   loading makes it cheap, not navigable; at 500 KB it needs its own split. Out of scope, named.
8. **Whether the Cursor fleet reads `AGENTS.md` at generation time is unresolved.** If it does
   not, the routing convention has no effect on the highest-volume writer and the gates carry
   100% of the load for that population.
9. **The shape gate is a proxy.** A session can write 400-char non-nested bullets. If G2 proves
   gameable, the rate axis has to come back — and OD-2 says it cannot come back as a blocking
   gate under `strict: true`. That is a real dead end with no designed successor.

---

## 9. Fleet applicability

BASE §7: canopy 94,373 B and cascor 70,118 B are on the same trajectory; a canopy session
already carries ≈109 KB of always-on instructions across three files. Six sub-40 KB repos follow.

What ports and what does not:

| Portable | Not portable |
|----------|--------------|
| G1 (size budget), G2 (shape), G5 (wired-gate lint), G8 (workflow topology) — all self-locating, in the idiom of `tests/test_agents_md_header_schema.py` | The prune itself. Each repo needs its own §2-style overlap analysis; cascor's bulk is model-internals prose and may not decompose into a `docs/REFERENCE.md` the way ml's does. |
| The residency rule and the resident hazard list *format* | The hazard *contents* |
| The `Allow-Docs-Rewrite` + squash-carry discipline (the screen is already fleet-wide) | — |

Two coordination costs nobody has priced:

- **The required context name is shared.** `Sequence Safety` is required on all nine repos; the
  eight siblings publish `Sequence Safety (Advisory)`. Any change to how that screen is invoked
  is a nine-repo change. This plan deliberately requires **no** change to the screen's scope —
  which is a direct consequence of rejecting `.claude/**` destinations, and one of the strongest
  practical arguments for the choice.
- **The post-merge battery sync is unreliable.** `main-verify.yml` carries a documented
  obligation to mirror `ci.yml`'s test enumeration and currently omits 18 of 88 modules. Assume
  a new gate does **not** run post-merge unless someone checks.

Sequencing: **do not roll out until Phase 7's soak has published.** Rolling out early
multiplies the waiver surface across nine repos at once for a design whose central risk is still
unmeasured — which this repo's own recent history argues against.

---

## 10. What I am not confident in

1. **That 18,007 chars is writable without loss.** Ten of the seventeen rows in §4 are
   compression targets, not measurements. If the core lands at 24,000 instead, the ceiling
   absorbs it and nothing breaks — but the "200-line guideline" framing does.
2. **That the canary's `CANARY-ABSENT` is conclusive.** The positive control rules out a broken
   probe; it does not rule out a fourth mechanism nobody has hypothesised. Treat H-b as
   "no evidence of the hazard", not "the hazard is impossible", and keep the ordering anyway.
3. **The 4-chars-per-token divisor.** MECH §8 lists `eR()` returning 4 or 3 as unverified. At 3,
   today's always-on load is 34% of a 200k window rather than 25%, and the post-plan figure is
   8.7% rather than 6.5%. **Relative** savings are invariant; the urgency claim is not.
4. **Whether relocation merely moves the growth.** Nothing in this plan makes writing to
   `docs/REFERENCE.md` *easier* than writing to `AGENTS.md`; the ceiling can refuse an add but
   cannot make the alternative attractive. That is a human-factors bet with no mechanism behind
   it and it is the weakest link.
5. **The eviction yield for `MEMORY.md`.** 5,471 bytes of candidates is a *pool*; some CLOSED
   arcs still carry live traps. I expect roughly half to survive triage and I have not verified
   that entry by entry.

---

## 11. Recommendation on cross-validation

This plan proposes deleting ~89% of the file that governs every session in this repo, behind a
waiver on a **required** status check, in a repo whose own memory records that handoff and
planning documents "inherit errors across generations". Before ratification:

1. Read it against **synthesis 2**, produced independently from the same package.
2. Re-verify the four numbers that decide phase content: the §4 per-section characters, the
   corrected 32,443 residue, the 35-entry / 5,471-byte `MEMORY.md` eviction pool, and the
   six-reference `#script-placement-mandatory` anchor inventory.
3. Run the §3 canary before anyone opens a Phase-4 branch.
4. Confirm that G3's negative control — a relocation that carries identifiers but drops prose
   must FAIL — is present and non-tautological. If it is not, the migration has no content-loss
   control at all: the docs screen's WARN band is blind to exactly the edit shape this plan
   makes.

---

## Related documents

| Document | Role |
|----------|------|
| [`../AGENTS.md`](../AGENTS.md) | the subject |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | the destination (161,487 chars, 28 H2 sections) |
| [`../docs/DOCUMENTATION_OVERVIEW.md`](../docs/DOCUMENTATION_OVERVIEW.md) | the 33-row "I Want To" index the navigational core condenses |
| [`../tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) | the tree gate, incl. the `agent_templates/` assertion at `:114-116` |
| [`../tests/test_agents_md_header_schema.py`](../tests/test_agents_md_header_schema.py) | the self-locating idiom every new gate follows |
| [`../tests/test_service_fork_drift.py`](../tests/test_service_fork_drift.py) | the two-sided `ENFORCED` / `KNOWN_GAP` ledger pattern |
| [`../juniper-ci-tools/juniper_ci_tools/docs_additions_check.py`](../juniper-ci-tools/juniper_ci_tools/docs_additions_check.py) | the docs screen — scope at `:62-66`, FAIL predicates at `:194` / `:196` |
| [`../juniper-doc-tools/juniper_doc_tools/check_doc_links.py`](../juniper-doc-tools/juniper_doc_tools/check_doc_links.py) | anchor resolution at `:293` |
| [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) · [`../.github/workflows/main-verify.yml`](../.github/workflows/main-verify.yml) | the per-PR and post-merge screens |
| [`../util/release_train/archive_guard.py`](../util/release_train/archive_guard.py) | the `Allow-*` trailer reference implementation |
| [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) | this document's naming rules |
| [`JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md) | the policy that keeps compaction rare — and stays resident |
