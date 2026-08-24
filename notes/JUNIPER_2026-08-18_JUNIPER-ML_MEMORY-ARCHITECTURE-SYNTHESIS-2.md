# Shared Session Memory — Recommended Plan (Synthesis 2 of 2)

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose and standing

This is one of two **independent** syntheses over the four competing shared-session-memory
proposals and the three validation audits. It is the plan I would stake the project on.

Inputs, all read in full:

- [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) — **BASE**
- [Claude Code memory mechanisms](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) — **MECH**
- [Proposal A — Skills](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md) ·
  [B — Path-scoped locality](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md) ·
  [C — Deduplication and pruning](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md) ·
  [D — Govern the write path](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md)
- [Grounding audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-GROUNDING-AUDIT.md) ·
  [Arithmetic audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ARITHMETIC-AUDIT.md) ·
  [Adversarial audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ADVERSARIAL-AUDIT.md)

Everything below was re-measured in this worktree at `main` = `e209b74`, clean tree, against the
installed `juniper-ci-tools` **0.8.0** — the version `ci.yml` and `main-verify.yml` pin. Where a
number differs from a proposal's, mine is shown and the source is named. **This document is the
only file written.**

**Reading convention.** Every path, test module, workflow, job name and CLI flag cited with a
`file:line` reference **exists today and was verified in this worktree**. Every artifact introduced
under a phase's "**Ships:**" list — `util/memory_index_check.py`, `util/memory_relocation_proof.py`,
`util/memory_budget_check.py`, `conf/memory_budget.toml`, `conf/memory_destinations.yaml`,
`notes/memory-inbox/`, the `memory-budget` `ci.yml` job, the `MEMORY_BUDGET_MODE` repo variable, and
the six new `tests/test_*.py` gates — **does not exist and is proposed here**. Nothing in between.

### Nine measurements I re-derived rather than inherited

| Quantity | My measurement | Agrees with |
|---|---|---|
| `AGENTS.md` | 1,115 lines / **168,317 chars** / 170,137 bytes | BASE §1, arithmetic audit §0.2 |
| Three largest H2 sections | 20,469 + 99,304 + 16,101 = **135,874 chars**; residue **32,443** | BASE §8 as corrected |
| Per-H2 partition | 16 segments summing **exactly** to 168,317 | BASE §3 |
| `MEMORY.md` | 139 lines / 20,049 chars / **20,388 bytes**; oldest-20 2,688 B, newest-20 **4,695 B** | MECH §2a |
| `MEMORY.md` closed-tail eviction, strict uppercase 5 markers | **24 entries / 4,147 B** | MECH §2b row 1, reproduced exactly |
| Accretion signature | **156** nested sub-bullets, 126 top-level bullets, **32** `Operator …` pointer lines, **69** `#NNN` lines | BASE §4 |
| Tracked non-hidden top-level dirs | **18** | adversarial audit AV-G7 |
| `docs/REFERENCE.md` | 1,865 lines / 161,487 chars / 162,231 bytes; **28** H2 sections | BASE §5 |
| Parent `Juniper/AGENTS.md` | 11,016 bytes, **no `.git`** | adversarial audit AV-O1 |

Two facts I established that no proposal or audit records:

1. **The main checkout's `.claude/settings.local.json` (1,801 B) contains no `claudeMdExcludes`
   key** (`grep -c` → 0). That eliminates hypothesis **H-c** from Proposal B §7.3 and reduces the
   MECH §8c canary to a clean two-way discrimination.
2. **The best `MEMORY.md` lever is eviction *plus a forward-only* entry cap, and neither
   proposal states that pair.** MECH §2b (added after the proposals, from synthesis agent 1) is
   right that eviction beats a per-entry cap — clipping to 120 B rewrites **113 of 139** live
   entries. But eviction *alone* leaves the byte axis binding and buys only ~35 days. Capping
   **new** entries at 120 B costs zero churn, because it applies only to what the agent writes
   next, and takes the pair to **~69 days**. I also retract a claim I nearly published: the
   BYTE→LINE axis flip I measured is an artefact of the *clip-all* lever MECH §2b rejects; under
   eviction the byte axis stays binding in all four marker sets. See [§4.5](#45-memorymd-measured).

---

## 1. The decision

**Adopt C + D, corrected. Reject B outright. Reject A's thesis, adopt three of A's parts.**

### 1.1 Why C is the level fix

Three settled findings converge and none of them is about the headline percentage.

**The eager column cannot choose.** Normalized to one denominator, eager-after is A 34,586 /
B 27,995 / C 30,459 chars — 6.8% / 6.0% / 6.3% of a 200k window (arithmetic audit §1). A
0.8-point spread is not a decision input.

**The worst case can, and it is not close.** C **−83.3% unconditionally**, in every session,
regardless of breadth. A **−3.5%**, B **−0.9%** for a session that touches everything. The choice
is about *variance*, not level, and C is the only one of the three whose saving is a floor rather
than an expectation.

**Compaction settles it.** MECH §4c-bis: `paths:` rules and nested `CLAUDE.md` are *lost until
re-triggered*; skill bodies re-attach capped at 25,000 tokens total, oldest dropped. C's residual
is the project-root file, which is **re-injected from disk**. This project's standing policy is
*handoff instead of compaction* — but handoff is a convention the agent must choose to follow, and
MECH §6 says memory content carries no compliance guarantee. A design whose safety depends on a
policy that the design itself cannot enforce is a design with a hidden single point of failure.
C has none (adversarial AV-C3).

### 1.2 Why D is the rate fix, and why a level fix alone is not a plan

172 of 200 first-parent merges grew the file; the trailing-30-day net is **+92,507 chars**
(arithmetic audit AV-D-C2, reproducing nine of eleven windows exactly). A cut to the genre-A core
is undone in **44 days**. C's own §19 concedes it: *"if the redirect fails in practice, this
proposal degrades to a one-time 90% cut with a two-month half-life."*

D is the only proposal that makes a reduction permanent, and the mechanism is one rule: the
declared ceiling may only ever decrease, and a PR that cuts the file must lower its own ceiling in
the same commit (D2 rules 1 and 2). D also has the only correct CI topology in the set (AV-G4),
the only complete vacuous-pass treatment (AV-V1), and the only destination that guarantees a
blocked append terminates in a write rather than a lost lesson (D5).

### 1.3 Why C + D and not C + anything else

The adversarial audit's judgement is that C+D is complementary, A+B compounding, B+D cancelling.
The non-obvious reason it gives is the one that decided this:

> **both keep the corpus inside the docs screen's scope** — C's destination is
> `docs/REFERENCE.md`, D's inbox is `notes/**`, both `in_docs_scope == True`. The pair is the only
> combination that does not create the #1 risk.

Re-verified from the pinned source, `docs_additions_check.py:62-66`:

```python
def in_docs_scope(path: str) -> bool:
    """AGENTS.md (+ its CLAUDE.md symlink), docs/**/*.md, notes/**/*.md."""
```

`.claude/skills/**`, `.claude/rules/**` and `util/CLAUDE.md` all return **False**. A moves ~101,000
chars and B ~152,900 chars out of a file under a *required* deletion screen into files under none.
Choosing `docs/**` + `notes/**` destinations avoids that entirely — and avoids the coordination
cost nobody costed: the required context is `Sequence Safety` on juniper-ml and
`Sequence Safety (Advisory)` on the other eight (verified in the `e209b74` commit body, which
states the suffix is part of the context string), so extending `--scope` is a **nine-repo change**.
**We do not need it.** That is a concrete, quantified benefit of rejecting A and B.

### 1.4 What is rejected, and why

**Proposal B — rejected outright.** Not for lack of quality: its measurement work is the most
precise in the set (grounding audit §9), and it is the only proposal that got the compaction
question right before the fact base recorded it. It is rejected because six independent findings
all land on the same two mechanisms:

1. 152,900 of 166,736 chars (92%) sit in the two mechanisms MECH §4c-bis places in the "lost after
   compaction" row (AV-C1), and B's mitigation depends on an unverified property of the harness.
2. Those same files leave the docs-deletion screen entirely, and B §7.5 presents this as a benefit
   — *"the screens get quieter"*. It is the one place in the four documents where a stated weakness
   is inverted (AV-O2a). Quieter is silent.
3. `paths:` rules fire on **reads**. The utilities whose misuse destroys live compute
   (`juniper_chop_all.bash` with `KILL_WORKERS=1`, `reap_pytest_orphans.bash`,
   `experiment_stack.bash --down --all-mine`) are **invoked**, not read (AV-D2).
4. B's riskiest single act — deleting ~6,120 chars from `AGENTS.md` on the strength of the parent
   `Juniper/AGENTS.md` — is guarded by `tests/test_ancestor_dedup.py`, which can never execute:
   `docs-full-check.yml` clones *repos*, and `/home/pcalnon/Development/python/Juniper/` has no
   `.git` (verified). A guard that can only skip is the documented vacuous-pass class (AV-V3).
5. Its coverage ledger makes every new file under `util/`, `tests/`, `.github/workflows/` an edit
   to a shared rule file — a new collision surface its 53.5% contention figure does not count
   (AV-N1).
6. Worst-case saving −0.9%, and **B + D cancel**: D's rate axis would police a file that no longer
   contains the growth.

**Proposal A's thesis — rejected.** Eleven model-invocable reference skills as the primary carrier
of genre-B content. Rejected because: worst case −3.5%; the re-attach corpus is 141,650 chars ≈
35,412 tokens against a 25,000-token cap, so **three to four bodies drop, oldest-invoked first**
(AV-C2); ~101,000 chars leave the docs screen (AV-G1); every gate is empty-list-vacuous with no
negative control (AV-V2); and the whole thesis rests on model-invocable skills auto-invoking here,
which has never shipped — all three existing skills set `disable-model-invocation: true`. A's own
Phase 0 is the right test, and it is a test the plan below does not need to run because it ships
no new skills.

**Adopted from A anyway** — three parts that are correct and that C gets wrong:

- **A's reading of the tree gate.** `tests/test_agents_md_tree_drift.py:114-116` asserts the
  literal string `agent_templates/` is in the fenced block. B's 42-line and C's 18-node
  top-level-only trees both drop it and **fail a required check** (AV-F-1). A budgets one nested
  node. Cost of the fix: ~30 chars.
- **A's Tier-1 / Tier-2 / Tier-3 vocabulary** as the naming for the residency rule's outcomes.
- **A's `## Invariants`-first body ordering principle** (start-preserving truncation keeps the
  start) — applied here to `docs/REFERENCE.md` sections, not to skills.

**Rejected from D** — four elements, each for a named reason:

| D element | Verdict | Reason |
|---|---|---|
| Rate axis as a **blocking, rolling-window** check | **Rejected** | Under `strict_required_status_checks_policy: true` the act required to merge (update-branch) is the act that can break the check, and the author has no repair (AV-N3). Replaced: level blocking, rate reported. |
| `Allow-Budget-Overrun` as a **loan** | **Rejected** | With 23 session worktrees the debt bills every in-flight PR at once, none of which created it; and >1 waiver freezes the ratchet, so the mechanism intended to make overruns expensive freezes D's only claim to permanence (AV-W1). |
| Net-of-deletions rate metric | **Rejected** | A net budget can be paid by deleting someone else's lore, and the deletion shape that pays it is `small-deletion / WARN` — green, no trailer (AV-W2, AV-G2). Additions-only. |
| D6 hooks in the critical path | **Deferred** | MECH §12.1 leaves the hook config schema unverified; `.claude/settings.json` is gitignored (`.gitignore:177`); and that file also carries **permissions**, which must be owner-authored (AV-O2d). ~1.4% size benefit. Worth doing; not on this path. |

**Rejected from C** — two specifics, both hard CI failures as written:

- C §4.1 renames `### Script placement (mandatory)` and `## Worktree Procedures (Mandatory -- Task
  Isolation)`. Those anchors are live: **6** references to `#script-placement-mandatory` (including
  an intra-file link at `AGENTS.md:500`) and **3** to
  `#worktree-procedures-mandatory--task-isolation`, resolved by
  `juniper-doc-tools/juniper_doc_tools/check_doc_links.py:293` under the **required**
  `Documentation Links` context (AV-C-1). **Both heading texts are kept verbatim.**
- C's 18-node tree fails the tree gate (above).

And one correction to C's destination policy, which is mine, not an audit's:

> **`docs/REFERENCE.md` is the single authoritative destination for relocated genre-B content.
> Module docstrings may carry a copy; never the only copy.**

C routes 4,417 chars to module docstrings and ~12 test rationales to test docstrings. A module
docstring is not a `def`, so the AST symbol screen (`--scope 'tests/*.py' --scope 'util/**/*.py'`,
`ci.yml:868`) does not guard it, and `.py` is not in the docs screen's scope either. Content
relocated there has **no deletion alarm at all** — the same exposure that disqualifies A and B,
arriving through the back door. One destination also preserves the property AV-N2 names: a merge
conflict is currently the only signal two sessions get that they independently discovered the same
failure class.

### 1.5 The load-bearing tradeoff I am accepting

**We are trading a measurable, unconditional token reduction for an unmeasurable pointer-follow
rate.**

After P5, every session pays ~29,782 chars instead of 182,476, in every session regardless of
breadth. In exchange, an agent that needs the reaper's live-experiment protection rule must
*decide* to open `docs/REFERENCE.md`. There is no instrumentation for that decision and no
published benchmark (MECH §8 item 6). C's own file is evidence against it: **32 lines already end
by pointing at the `docs/REFERENCE.md` section holding the same material, and then restate it
anyway** (my count; BASE §5 says 32).

I accept it for four reasons, in descending strength:

1. **The counter-evidence is local, large, and running.** MECH §8b measures the auto-memory index
   at **53:1** — 1,082,901 bytes on disk, 20,388 loaded — in this very project, beside the problem
   file. An index over a deferred corpus demonstrably works here.
2. **The residency rule keeps the irreversible content resident.** A pointer miss costs a tool
   call; it does not cost a destroyed campaign, because the campaign-destroying rules never leave
   the root file.
3. **The bet is falsifiable and has a stated ladder.** C §14.2's soak (N ≥ 20 real
   component-touching tasks, transcript-observable) measures it ex post, and the response to
   failure is row → gate → path-scoped rule, **never re-inline**.
4. **Every alternative carries the same bet plus more.** A and B make the *same* discovery wager
   and add compaction fragility and loss of the deletion alarm on top of it.

A second, smaller trade, stated so it is not discovered later: **D5 buys latency instead of loss.**
A session that learns something between an inbox write and the weekly curation does not get the
benefit. That is real and it is the price of not letting three unreviewed appends per day into a
file every agent loads.

---

## 2. Sequencing: two clocks, one plan

| Clock | What it governs | Deadline |
|---|---|---|
| **`MEMORY.md` fuse** | **silent, irreversible, newest-first content loss** | **≈19 days** (2026-09-06) at the recent 234.75 B/entry rate; ≈30 at the blended rate |
| **`AGENTS.md` regrowth** | tokens and attention only; **nothing is lost** | a cut is undone in **44 days** at +92,507 chars/30 d |

Two consequences that fix the ordering:

**`MEMORY.md` goes first, and it is independent of everything else.** It shares no mechanism, no
destination and no gate with the `AGENTS.md` work. Deferring it is not a scheduling choice; it is a
decision to accept silent loss of the newest entries — the defect register, the seed-reproducibility
blocker, the CI-waiter guidance — while the file on disk still looks complete to any human who
opens it.

**The ratchet ships *before* the cut, not after.** Proposal D puts the level axis and ratchet in its
last phase, which is correct for D standing alone (the level axis is inert with nothing to hold) and
**wrong for a C+D hybrid**. If the ceiling arrives after the prune, a two-week gap at 3,083 chars/day
admits ~43,000 chars of regrowth, and then D2 rule 2 fixes the ceiling at that inflated level. In
this plan the monotone ceiling is live at P2 at today's value, and **each prune PR lowers its own
ceiling in the same commit**. There is no window.

Phase order, with the clock each serves:

```
P0  MEMORY.md triage                         <- the 19-day fuse. Ships alone, day 0.
P1  Canary + prerequisites                   <- gates the ORDERING of P4/P5 (MECH §8c)
P2  Ceiling + ratchet + shape gate + inbox   <- the 44-day clock, armed before the cut
P3  Write the six docs/REFERENCE.md sections <- additive; G7 ordering rule
P4  Prune Key Files + CI/CD Pipelines        <- the big one; ceiling -> 60,000
P5  Prune the rest; write the resident core  <- ceiling -> 18,000 (terminal)
P6  Soak, then promote                       <- evidence gate on the pointer bet
P7  Fleet                                    <- gates port; the prune does not
```

P0 and P1 may run concurrently (disjoint files). P3 may start as soon as P1 lands. P4 → P5 is
strictly ordered. P6 begins the day P5 merges.

---

## 3. The pre-migration canary (MECH §8c) — gates the ordering of P4 and P5

MECH §8c: *"It must be settled before any migration begins, because getting it wrong inverts the
result."* Proposals A, C and D do not mention it (AV-F-3). B does, and prescribes the right probe;
the probe as B writes it has a defect.

**The question.** The main checkout's `juniper-ml/CLAUDE.md` **is** a filesystem ancestor of
`.claude/worktrees/<name>/`, so MECH §4c predicts it loads eagerly. It does not appear in a
worktree session's context. Two hypotheses survive:

| | Mechanism | Consequence during migration |
|---|---|---|
| **H-a** | content dedup — identical content injected once | The moment a worktree carries a trimmed `AGENTS.md` and main still carries 168,317 chars, they stop matching and **both** load. Eager goes from 182,476 to ≈213,176 chars (**+16.8%**) for the life of that PR. Trimming makes context go **up**. |
| **H-b** | worktree-aware root detection — the ancestor is genuinely skipped | No hazard. Phases may be authored in parallel worktrees. |

B lists a third (`claudeMdExcludes`). **Ruled out here**: the main checkout's
`.claude/settings.local.json` (1,801 B) contains no `claudeMdExcludes` key. The probe is therefore a
clean two-way discrimination.

**The defect in B's probe, and the fix.** B §13.5 uses an HTML comment as the marker. MECH §4d
states block-level HTML comments are **stripped before injection** — so `CANARY-ABSENT` would be
ambiguous between "the ancestor was not loaded" and "the marker was stripped", and *absent* is
precisely the result we would act on. **Use a plain, non-comment marker line.**

**The probe** (≈2 minutes, fully revertible; run it twice — see the negative control):

```bash
# 1. In the MAIN checkout (not a worktree), uncommitted:
cd /home/pcalnon/Development/python/Juniper/juniper-ml
printf '\nJUNIPER-MEMORY-CANARY-H-20260818: ossifrage.\n' >> AGENTS.md

# 2. From an EXISTING worktree whose own AGENTS.md does NOT carry the marker:
cd .claude/worktrees/<any-existing-worktree>
claude -p "Reply exactly CANARY-PRESENT if the token JUNIPER-MEMORY-CANARY-H-20260818 appears \
anywhere in your project instructions, otherwise reply exactly CANARY-ABSENT."

# 3. Revert, unconditionally:
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git checkout -- AGENTS.md

# 4. NEGATIVE CONTROL -- re-run step 2 after the revert. It MUST now say CANARY-ABSENT.
#    Same answer both times => the probe is broken; do not act on it.
```

If a script is written for this it belongs in `util/ad-hoc/` per the script-placement rule
(`AGENTS.md:904-918`), never in `/tmp/`.

**What each answer changes:**

- **CANARY-PRESENT (H-a).** Migration ordering becomes mandatory and serial: author each prune PR
  in a worktree created *before* the trim; merge; immediately
  `git -C <main-checkout> pull --ff-only origin main`; only then create the next worktree. This is
  already Phase 7 of the worktree cleanup procedure, implemented in `util/worktree_cleanup.bash`
  and documented at `AGENTS.md:1018-1020`. Additionally: **do not run P4 and P5 concurrently.**
- **CANARY-ABSENT (H-b).** No hazard. P4 and P5 may be authored in parallel worktrees.

Record the answer in P1's PR body. **Do not proceed to P4 on an assumption.**

---

## 4. Target budget, with arithmetic

All figures are **characters**, because that is what the shipped CLI check measures
(`content.length`, MECH §1) and because BASE labels characters as bytes in four places. My
per-H2 partition sums to exactly 168,317.

### 4.1 The mechanical residue, and why the target sits below it

`## Repository Structure` 20,469 + `## Key Files` 99,304 + `## CI/CD Pipelines` 16,101 =
**135,874**. `168,317 − 135,874 = ` **32,443 chars** (BASE §8 as corrected by AV-X-2; the
previously published 34,263 subtracted characters from bytes).

32,443 is *"delete the three big sections and change nothing else"*. It is the **ceiling of the
plausible target, not the target**, because the remaining twelve sections carry genre-B fat of
their own — a 3,315-char test-run block that is already wrong (it names 54 files; `ci.yml` runs 87
of 88), a 3,512-char restatement of `docs/REFERENCE.md:1449 ### juniper-service-core`, and a
1,495-char restatement of `:1421 ### juniper-observability`.

### 4.2 The section-by-section target

| Section (measured) | Now | Target | Basis |
|---|---:|---:|---|
| header + preamble | 331 | 331 | pinned by `tests/test_agents_md_header_schema.py` (6 fields, ISO date) |
| `## What This Is` | 596 | 400 | condense |
| `## Build & Package Commands` | 4,617 | 900 | 4 build commands, extras pointer, **one** test line + "the authoritative list is `ci.yml`", pre-commit line |
| `## Publishing` | 3,641 | 550 | one mandatory sentence + pointer to the publish procedure note |
| `## Shared Observability Helpers` | 1,495 | 200 | pointer → `docs/REFERENCE.md:1421` |
| `## Shared Service-Core Contracts` | 3,512 | 250 | pointer → `docs/REFERENCE.md:1449` (already the declared operator surface) |
| `## Repository Structure` | 20,469 | 1,900 | 18 top-level nodes **+ one nested `agent_templates/` node** + ~6 root files |
| `## Key Files` → `## Where To Look` | 99,304 | 2,000 | ~14 task-shaped pointer rows + a catch-all row |
| `## CI/CD Pipelines` | 16,101 | 900 | one paragraph + pointers to `ci.yml` and `docs/REFERENCE.md` |
| `## Pre-commit Hooks` | 2,085 | 500 | setup commands + pointer to `.pre-commit-config.yaml` |
| `## Secrets Management (SOPS)` | 492 | 492 | already minimal |
| `## Ecosystem Context` | 2,315 | 500 | pointer to the parent guide + extras pointer |
| `## Conventions` (incl. `### Script placement (mandatory)`) | 2,484 | 1,900 | **heading text kept verbatim** — 6 live anchors |
| `## Pull Request Conventions` | 2,842 | 800 | JR-ID verb table + pointer |
| `## Worktree Procedures (Mandatory -- Task Isolation)` | 4,159 | 700 | **heading text kept verbatim** — 3 live anchors; pointer to the two procedure notes |
| `## Thread Handoff (Mandatory -- Replaces Thread Compaction)` | 3,874 | 700 | trigger + rule; pointer to the procedure note |
| **NEW** `## Traps With No Gate` | 0 | 2,600 | ~16 one-line resident hazards (§6.2) |
| **TOTAL** | **168,317** | **15,623** | **−152,694 (−90.7%)** |

Target column sums: `(331+400+900+550) + (200+250+1,900+2,000) + (900+500+492+500) +
(1,900+800+700+700) + 2,600 = 2,181 + 4,350 + 2,392 + 4,100 + 2,600 = 15,623`.

### 4.3 The declared ceilings

**18,000 characters and 200 lines**, dual — a character-only gate invites 512-char lines under this
repo's line-length convention; a line-only gate invites the same thing from the other direction.
Headroom over the drafted target: `18,000 − 15,623 = 2,377` chars. At ~193 content lines that is
~81 chars/line, dense but consistent with this repo's style.

**If the drafted core overshoots, the overflow goes to `docs/REFERENCE.md`, never to a raised
ceiling.**

### 4.4 Whole-session effect

| Component | Now | After | Note |
|---|---:|---:|---|
| `~/.claude/CLAUDE.md` | 3,341 | 3,341 | user-global; outside this repo |
| `Juniper/CLAUDE.md` → parent `AGENTS.md` | 10,818 | 10,818 | ungoverned; OD-4 |
| `juniper-ml/AGENTS.md` | 168,317 | 15,623 | ceiling 18,000 |
| **Eager subtotal** | **182,476** | **29,782** | **−83.7%** (−82.4% at the ceiling) |
| `MEMORY.md` index (separate subsystem) | 20,049 | **15,986** | P0 eviction; see §4.5 |
| **Always-on total** | **202,525** | **45,768** | |

At 4 chars/token: ≈50,631 → ≈11,442 tokens, i.e. **25.3% → 5.7%** of a 200k window before the
first prompt. **The divisor is unverified** — MECH §8 lists "whether `eR()` returns 4 or 3" as
open, and at 3 the absolute figures are a third higher (33.8% → 7.6%). The *relative* saving is
invariant.

### 4.5 `MEMORY.md`, measured

Cap is 200 lines / **25,000 bytes** (`qpe=25000`, MECH §8b — the 25,600 figure used by A, B and
D is superseded). MECH §2b establishes that **eviction of the finished tail is the primary lever**,
not a per-entry cap; my strict-uppercase count reproduces its first row exactly (24 entries /
4,147 B). All scenarios below assume new entries continue at the recent 234.75 B/entry unless a
forward-only cap is adopted.

| Scenario | Bytes | Lines | Byte-entries left | Line-entries left | Binding | Days @ 1.06/day |
|---|---:|---:|---:|---:|---|---:|
| Do nothing | 20,388 | 139 | 19.6 | 61 | BYTE | **18.5** |
| Evict 24 (strict uppercase, 5 markers) | 16,241 | 115 | 37.3 | 85 | BYTE | 35.2 |
| Evict 41 (broad, case-insensitive + `fixed`/`done`) | 13,813 | 98 | 47.7 | 102 | BYTE | 45.0 |
| **Evict 24 + cap NEW entries at 120 B** | 16,241 | 115 | 73.0 | 85 | BYTE | **68.9** |
| Evict 41 + cap NEW entries at 120 B | 13,813 | 98 | 93.2 | 102 | BYTE | 87.9 |

My case-insensitive counts (33 / 5,202 and 41 / 6,575) run slightly below MECH §2b's (35 / 5,471
and 43 / 6,844) — a regex-boundary difference, not a disagreement; §2b's figures are authoritative
and the conclusion is identical on either.

**Three readings.** (i) Eviction is nearly free — the index line goes, the topic file stays on
disk, so a finished item is demoted from resident to on-demand rather than deleted. (ii) Eviction
*alone* buys ~35 days, which is a reprieve, not a fix. (iii) The forward-only cap is the cheap
other half: it rewrites nothing, applies only to what is written next, and nearly doubles the
horizon again. **Do not clip existing entries** — MECH §2b measures that at 113 of 139 rewritten
for less benefit, and rewriting a live entry is exactly the kind of churn that loses content.

The BYTE axis stays binding in every scenario above, so the arithmetic is byte-bound throughout —
but the checker must still *name* the binding axis, because it is a `min()` of two limits and the
one that binds is not obvious to a reader looking at 61 spare lines.

---

## 5. Phases

Each is independently shippable and revertible. The CI verdict is stated for each, with the trailer
where one is needed. **`AGENTS.md`'s `**Last Updated**` must be today's date or changed in the PR's
own diff** (`agents-md-touch-up.yml`); a stacked pair that sits overnight needs its base re-bumped,
not the child edited.

### P0 — `MEMORY.md` triage (the 19-day fuse). Ships alone, day 0.

**Ships:**

1. `util/memory_index_check.py` — offline, stdlib-only, no network, no repo dependency. Reports
   lines and bytes **after stripping frontmatter and block-level HTML comments** (MECH §2 — a
   checker that does not strip over-reports by exactly the maintainer prose the mechanism makes
   free), both limits, and **names the binding axis** (§4.5 is the reason). WARN at 85%, FAIL at
   95% of the binding axis; projected days-to-truncation at the trailing rate; `--json`;
   exit 0/1/2, matching `util/agent_suite_doctor.py`'s contract.
2. `tests/test_memory_index_check.py` — the gate, because `util/` is outside every pre-commit
   Python hook's scope.
3. A **non-blocking** session-start banner from `scripts/wake_the_claude.bash`. Non-blocking is not
   timidity: a launcher that refuses to start gets edited out within a day.
4. **One eviction pass** over the finished tail (MECH §2b; ≥24 entries / ≥4,147 B, scope per
   OD-3), and adoption of a **forward-only** 120-byte per-entry cap. Existing entries are **not**
   rewritten.
5. A **canary index entry** — a deliberately-last line whose topic file states a unique token. If a
   session cannot recall it, truncation is confirmed empirically rather than inferred. Costs one
   index line (120 B, 0.5% of budget) for a definitive answer to the 25,000-vs-25,600 question.

**CI:** touches no screened path. Clean, no trailer.
**Verification:** `python3 -m unittest -v tests/test_memory_index_check.py`; the checker's own
output before and after the eviction pass.
**Rollback:** delete two files and the banner call. The eviction is reversible from the topic files,
which are never deleted.

### P1 — Canary and prerequisites (no `AGENTS.md` change)

**Ships:**

1. The **MECH §8c canary probe** (§3), run, with both the positive and the negative-control result
   recorded in the PR body.
2. **`tests/test_every_test_is_wired.py`** — C's G12 mirror lint: every `tests/*.py` must be named
   by at least one `.github/workflows/*.yml`. This is a prerequisite, not a nicety: three of the
   four proposals route content on the premise *"the gate is the memory"*, and that premise is
   false today for exactly one module. `tests/test_assert_release_tag.py` is absent from every
   workflow (verified: `grep -rn "test_assert_release_tag" .github/workflows/` returns nothing),
   and it pins `AGENTS.md:483` — the repo's own canonical vacuous-pass lesson.
3. **`util/memory_relocation_proof.py`** + tests — the block-level relocation proof (§6.1).
4. **`conf/memory_destinations.yaml`** — the two-sided destination ledger (§6.1), seeded from
   C §2.5's enumeration.

**CI:** additive. Clean, no trailer. `test_every_test_is_wired.py` ships **red-then-fixed** (OD-9)
or with `test_assert_release_tag.py` in an explicit `UNWIRED` allowlist carrying a reason and an
issue reference.
**Verification:** the four new/changed test modules; `juniper-check-doc-links`.
**Rollback:** delete the added files and their `ci.yml` lines.

### P2 — Ceiling, ratchet, shape gate, inbox (armed before the cut)

**Ships:**

1. `conf/memory_budget.toml` — governed targets (an **explicit list**, never a glob), units, the
   ceiling ladder, `LEVEL_SLACK`, the reported-only rate window.
2. `util/memory_budget_check.py` + `tests/test_memory_budget_check.py`.
3. A standalone **`memory-budget`** job in `ci.yml`, on the `release-train-archive-guard` shape
   (`ci.yml:720-740`) **exactly**: `if: github.event_name == 'pull_request' || github.event_name ==
   'merge_group'`; `merge_group` short-circuits to a green notice **before any checkout**;
   `permissions: contents: read`; **absent from the Quality Gate `needs:`** (`ci.yml:1305`);
   promotion to required happens in the **branch ruleset**, never via that `needs:` list.
4. `tests/test_agents_md_shape.py` — **report-only** at this phase.
5. `notes/memory-inbox/README.md` (~20 lines) and the inbox structural guard.
6. `docs/REFERENCE.md § Memory Budget Governance` — the operator surface and the routing table.

**Ceiling at P2: 170,000 chars / 1,150 lines; `LEVEL_SLACK` 20,000.** Green on merge, constrains
nothing today, and the *monotonicity* rule is live from this moment so the ladder can only descend.

**The three rules, corrected from D:**

- **No-worsening.** A PR fails only if `size(merge result) > ceiling` **and** `size(merge result) >
  size(base)`. A PR that does not grow `AGENTS.md` is green even when main is over budget. This
  removes AV-G4's "one unit over blocks every PR in the repo" and AV-O2b's concurrent-merge red-main
  class, while keeping a hard ceiling for anyone who grows the file. **No proposal states this rule.**
- **Monotone ceilings** (D2 rule 1). `conf/memory_budget.toml`'s ceiling and `LEVEL_SLACK` at HEAD
  must be ≤ their value at the merge base, unless waived by `Allow-Budget-Raise:`.
- **Anti-banking, scoped** (D2 rule 2, corrected). `ceiling − actual ≤ LEVEL_SLACK` is checked
  **only on a PR whose diff reduces the governed file by more than `LEVEL_SLACK`** — so a cleanup
  PR cannot merge without lowering its own ceiling, and a bystander PR is never billed for someone
  else's cut.

**The rate axis is reported, not gated.** `additions`-only bytes per PR and a trailing-30-day
additions total, written to the step summary and to a daily alarm modelled on
`.github/workflows/pr-budget-alarm.yml`, alongside `docs/REFERENCE.md` and
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (64,267 bytes, the fleet's second-hottest file, 158
commits since 2026-06-01) so displacement is visible in one table. Gated: none of those three.

**The waiver.** `Allow-Budget-Overrun: <file> — <reason>`, per-PR only, **no loan**. The checker
FAILs a bare trailer with no `— <reason>` suffix, and the reason **must contain an inbox path**, so
the cheapest green path routes *through* the capture mechanism rather than around it (AV-W3's fix,
converting a hole into a funnel). Waivers are metered to the daily alarm.

> **CORRECTION 2026-08-24 — the paragraph above describes an INTENT that was never built, and
> stated the checker's behaviour as the exact inverse of the truth.** `util/memory_budget_check.py`
> accepted **only** the bare `<path>` form; the `— <reason>` form this document mandates parsed as
> nothing at all, and was discarded **without a diagnostic**. An author following this page wrote a
> waiver that did nothing and stayed red with the trailer sitting in their commit message. No commit
> on `main` has ever carried either trailer at line start, so the divergence was never exercised and
> never noticed.
>
> **Actual behaviour as of 2026-08-24:** both forms are accepted — bare `<path>`, and
> `<path> <sep> <reason>` where `<sep>` is `-`, `–` or `—`. Anything that claims to be one of the
> two trailers and fails to parse is now **reported** as a `::warning::` rather than dropped, which
> is what [`docs/REFERENCE.md`](../docs/REFERENCE.md) already promised ("Waivers are always
> reported, never silent") and the code did not deliver.
>
> **Still NOT implemented:** requiring a reason, and requiring that reason to contain an inbox path.
> The funnel argument stands on its own merits and is a live option — but it is a deliberate
> tightening of a blocking gate, to be decided and shipped as such, not smuggled in while repairing
> a parse bug. Until then, treat this paragraph as a proposal, not a description.

**CI:** additive. Clean, no trailer.
**Verification:** the new test modules; `tests/test_memory_budget_workflow.py` (modelled on
`tests/test_archive_guard_workflow.py`) asserting the job is absent from the Quality Gate `needs:`
and present on `pull_request` + `merge_group`.
**Rollback:** flip the repo variable `MEMORY_BUDGET_MODE` to `report`. No code change, no PR.

### P3 — Write the six `docs/REFERENCE.md` sections (additive; `AGENTS.md` untouched)

`docs/REFERENCE.md` has 28 H2 sections and none for: `util/wait_for_checks.py`,
`util/open_signed_pr.py`, `util/assert_release_tag.bash`, `util/experiments/run_suite.py`,
`util/release_train/ceremony.py`, `util/release_train/notes_render.py`. Verified. ~11,443 chars —
under two days of that file's observed August growth.

**Derive `assert_release_tag.bash` from source, not from `AGENTS.md`.** The existing entry at
`AGENTS.md:485` documents `--ref-type` / `--ref-name` / `--dist-dir` / `--expect-prefix`; C §2.4
found and the grounding audit confirmed that the script does not accept those flags as written.
Relocating a wrong entry propagates the defect.

Each section opens with an `## Invariants`-equivalent first paragraph (A's start-first principle),
and gets a `docs/DOCUMENTATION_OVERVIEW.md` "I Want To" row (`:23`).

**CI:** purely additive to `docs/`. Clean, no trailer.
**Verification:** `juniper-check-doc-links`; each new section's flags checked against the script's
own argument parsing.
**Rollback:** `git revert`.

### P4 — Prune `## Key Files` and `## CI/CD Pipelines` (the big one)

Removes 97,304 + 15,201 = **112,505 chars**. `## Key Files` becomes `## Where To Look` (2,000);
`## CI/CD Pipelines` becomes a paragraph plus pointers (900). File after: **55,812**. Ceiling
lowered to **60,000 / 400 lines** in the same commit; `LEVEL_SLACK` to 10,000.

**Sequence within the phase:** (a) confirm every destination row in
`conf/memory_destinations.yaml` resolves at HEAD; (b) delete `### Utilities`, `### Tests`,
`### CI/CD Workflows`, `### Package and Metadata`, `### Documentation`, `### Scripts and
Launchers`, `### Configuration`, `## CI/CD Pipelines`; (c) add `## Where To Look`; (d) lower the
ceiling.

**CI verdict: FAILS the required `Sequence Safety` context without a trailer.** It deletes
markdown headings — `docs_additions_check.py:194` FAILs on a deleted heading with no added heading
in the same hunk. Required:

```text
Allow-Docs-Rewrite: AGENTS.md
```

**Carry the trailer into the squash commit message.** `main-verify.yml:196` re-runs the screen
post-merge over `BASE..<merge>`; a trailer that lives only on a branch commit reddens `main` after
a green PR — the recurring class this project has already paid for three times.

**Never `Allow-Docs-Rewrite: *`.** `docs_additions_check.py:208-227` treats `*` as waiving every
screened deletion, and post-merge the G3.1 catch-up base sweeps a *window* of merges, so a wildcard
silently waives other people's deletions too.

**The trailer is not the control.** Verified against the pinned 0.8.0: a hunk deleting **40** lines
with **one** added line classifies `small-deletion / WARN`, and WARN never fails
(`docs_additions_check.py:196,199`). "Delete a block, leave a pointer, keep the heading" — the exact
shape of this migration — is green at any magnitude with no trailer and nothing to review. **The
block-level relocation proof (§6.1) is the control**; the trailer is bookkeeping.

**Verification:** the relocation proof at 100%; the four existing `test_agents_md_*` gates; full
`tests/` run; `juniper-check-doc-links`.
**Rollback:** `git revert`. The ceiling revert is a `Allow-Budget-Raise:` case — the one waiver use
this design considers unambiguously correct, since a revert must not be blocked by its own ratchet.

### P5 — Prune the rest; write the resident core

Removes the remaining 40,189 net chars (18,569 from `## Repository Structure`, 21,620 from the
twelve smaller sections, less 2,600 added for `## Traps With No Gate`). File after: **15,623** —
reconciling exactly to §4.2. Ceiling to **18,000 / 200 lines**; `LEVEL_SLACK` to 3,000;
`tests/test_agents_md_shape.py` promoted from report-only to blocking.

**Three things that must not be got wrong:**

1. **Keep `### Script placement (mandatory)` and `## Worktree Procedures (Mandatory -- Task
   Isolation)` verbatim.** 6 + 3 live anchors, resolved under the required `Documentation Links`
   context.
2. **Keep one nested tree node**, `│   ├── agent_templates/`. `tests/test_agents_md_tree_drift.py:114-116`
   asserts the literal string is in the fenced block; a top-level-only tree fails a required check.
   All 18 tracked non-hidden top-level dirs must also appear as `├── name/` nodes.
3. Also add `.github/pull_request_template.md` and the three `.claude/agents/*.md` prompts
   (`planner`, `auditor`, `task-executor`) a one-line routing convention: post-mortem detail goes to
   `docs/REFERENCE.md`, not to `AGENTS.md`. Those files are already gated by
   `tests/test_agents_frontmatter.py`.

**CI verdict: FAILS without `Allow-Docs-Rewrite: AGENTS.md`.** It deletes `### Dependency extras
reference` and other H3s, and the 197-line tree replacement will produce at least one pure-deletion
hunk ≥5 lines. Same squash-carry requirement; same never-`*` rule.

**Verification:** as P4, plus the shape gate blocking and the size gate at the terminal ceiling.
**Rollback:** `git revert` + `Allow-Budget-Raise:`.

### P6 — Soak, then promote

**The soak is the evidence gate on §1.5's bet.** Population: the next **N ≥ 20** real
component-touching tasks, not synthetic prompts — this project's own standing method rule is to
report rates over N ≥ 20 on a stochastic effect. Metric: did the session open the relocated
destination before editing the component? Observable in the transcript. Pass bar and rollback
trigger: **OD-6**.

On failure, apply the ladder — add a `## Where To Look` row; then wire a gate; then, only as a last
resort, a `paths:`-scoped rule for that one subject, accepting AV-C1's compaction exposure
explicitly. **Never re-inline.**

Also at P6, if and only if the soak passes: promote `memory-budget` to a **required** context in the
branch ruleset (never via the Quality-Gate `needs:`), and decide OD-2 on the rate axis.

**CI:** no code change for the soak itself.
**Rollback:** demote the context in the ruleset.

### P7 — Fleet

Copy `tests/test_agents_md_size_budget.py` and `tests/test_agents_md_shape.py` into the other eight
repos using the self-locating idiom of `tests/test_agents_md_header_schema.py:40-48`, with per-repo
ceilings set to current size and ratcheted down as each repo is pruned. See §9.

---

## 6. Guardrails, each with a negative control

This repo has a documented vacuous-pass class — *"a check whose machinery breaks and reports
SUCCESS; three instances in one day"*. Every gate below therefore ships with a synthetic negative
that must **fail**, modelled on `tests/test_agents_md_tree_drift.py:109-112`
(`test_checker_flags_a_missing_dir`), which is the repo's own reference implementation of the idea.

### 6.1 The block-level relocation proof — the single most important new control

**Why it exists.** The docs screen is structurally blind to this migration's edit shape (§P4), and
C's own G1 — "every removed backticked token resolves somewhere at HEAD" — passes on the loss it
exists to prevent: a stub that copies every identifier and drops every sentence of reasoning scores
100% (AV-V4). C says so itself in §1.2 and then relies on the gate in E3.

**Spec.** `util/memory_relocation_proof.py --base <ref> --head HEAD [--json]`:

- Parse `git diff <base>..HEAD -- AGENTS.md` into **removed blocks**: a heading and its body up to
  the next heading of equal-or-higher level, or a top-level `- ` bullet with its nested sub-bullets.
- For each block require **either** (a) a named destination path at HEAD containing a normalized
  match of ≥ a declared fraction of the block's *content lines* — not tokens — **or** (b) an
  explicit `DELETED-AS-DERIVABLE` row in `conf/memory_destinations.yaml` naming the deriving
  artifact (`ci.yml`, `pyproject.toml`, `git ls-tree`).
- Emit a markdown table into the PR body and upload it as an artifact. Exit 1 on any unaccounted
  block.

**Negative controls.** (i) A synthetic PR that deletes a block and writes nothing at the
destination must FAIL. (ii) A synthetic PR that copies **only the backticked identifiers** must
FAIL — this is AV-V4's counterexample, executable. (iii) An empty diff must produce zero blocks and
exit 0 *with an explicit "0 blocks examined" line*, so a broken parser is visible rather than green.

### 6.2 The resident hazard list — `## Traps With No Gate`

C's §5.3 list of fourteen, corrected. **Add `KILL_WORKERS`**: it is the one directive in the whole
corpus whose misuse kills live compute, and it is lazy in all four proposals (AV-D3). C's own list
omits it. `docs/REFERENCE.md` carries the full disambiguation; the resident line is the hazard, not
the explanation:

> `KILL_WORKERS=1` reaches outside the pidfile set — never set it while a campaign is running.

**Add the invocation class generally.** `paths:` rules and nested files fire on reads; scripts are
*run*. Every utility that terminates a process keeps a one-line resident hazard, whatever else is
relocated.

**Negative control** for the list's guardrail: `tests/test_agents_md_shape.py` asserts a curated set
of marker strings is present in the root file (B's directive-marker idea, two-sided), and a
synthetic root file with a marker removed must FAIL.

### 6.3 The destination ledger — two-sided, borrowed from B and from an existing repo pattern

`conf/memory_destinations.yaml`, modelled on `tests/test_service_fork_drift.py`'s
`ENFORCED` / `KNOWN_GAP` idiom: every relocated subject has a named destination **or** an explicit
`UNCOVERED` entry with a reason. This is B's clause (d) — the best anti-vacuous design among the
cutting proposals — applied to the *destination inventory* rather than to `paths:` globs, which is
what makes it useful without creating B's new shared-edit surface (AV-N1).

**Negative control:** with an empty ledger, every relocated subject is uncovered and the gate FAILs
loudly. An `UNCOVERED` row that becomes covered must FAIL and instruct promotion, so the ledger
cannot rot into a list of things that used to be true.

### 6.4 The size and ratchet gates

`tests/test_agents_md_size_budget.py`, wired into `ci.yml`'s `tests` job beside `:626` / `:636`
where the sibling `test_agents_md_*` gates run — but the **no-worsening** comparison lives in the
standalone `memory-budget` job, because it needs a base.

**Negative controls:** (i) a synthetic over-ceiling fixture must FAIL; (ii) a synthetic diff raising
the declared ceiling must FAIL monotonicity; (iii) a synthetic diff raising `LEVEL_SLACK` must FAIL
(D's own point: raising the slack is itself a ratchet violation); (iv) a synthetic cleanup that
drops 60,000 chars without lowering its ceiling must FAIL rule 2; (v) the measured size must be
asserted against `os.stat` ground truth the checker did not compute — D's
`test_measured_size_matches_ground_truth`, the correct general antidote; (vi) the **symlink trap** —
`CLAUDE.md` is a symlink to `AGENTS.md` today, so the gate must name `AGENTS.md` explicitly, and the
day they diverge must produce a **warning**, not a red test (D's residual, AV-V1).

### 6.5 The shape gate

`tests/test_agents_md_shape.py` attacks the accretion *mechanism*, not the symptom: no list item
nested two or more levels deep (**156** exist today), no `#NNN` issue citations (**69** lines), no
`Operator surface:` / `Operator detail:` trailers (**32** lines — the pointer now lives once, in
`## Where To Look`).

That last assertion is not a style rule. It is the mechanism that stops the observed behaviour from
re-running: 32 authors wrote a pointer and then wrote the summary anyway, and any hybrid that adopts
pointers must forbid the trailer or it will simply happen again (AV-D5).

**Negative controls:** a synthetic depth-2 bullet must FAIL; a synthetic `Operator surface:` line
must FAIL; a zero-length input must FAIL rather than pass vacuously.

### 6.6 The inbox structural guard

Inverts `util/release_train/archive_guard.py`: a **deletion** from `notes/memory-inbox/` requires a
non-inbox **addition** in the same diff, so curation cannot silently drop knowledge.

**Plus a control no proposal has.** `notes/**/*.md` **is** in the docs screen's scope, so every
weekly curation PR deletes headings and needs `Allow-Docs-Rewrite:`. The cheapest form is `*`, and
`*` is accepted — which would manufacture a weekly habit of writing the exact reflexive wildcard
waiver D §5.2 identifies as the failure mode (AV-N4). **The curation tool emits an enumerated
trailer naming each deleted inbox file, and the guard FAILs on a wildcard in a curation PR.** The
tool already knows the file list; this is trivial to generate. It reads the trailers from an
injected file, the same way `ci.yml:776` feeds the archive guard.

**Negative controls:** an inbox deletion with no routed addition must FAIL; a curation PR carrying
`Allow-Docs-Rewrite: *` must FAIL; an empty inbox must not vacuously pass — the guard reports
"0 inbox files examined" explicitly.

### 6.7 The G12 mirror lint

Every `tests/*.py` must be named by at least one `.github/workflows/*.yml`. Ships in P1, **before**
any relocation justified on "the gate holds it" grounds.

**Negative control:** a synthetic unwired module must FAIL. It also has a live positive: exactly one
of 88 modules violates it today, so a run that reports zero violations before OD-9 is resolved is
itself evidence the lint is broken.

### 6.8 The post-compaction duplication lint (report-only)

**No proposal has this, and it hits all four** (AV-C5). Immediately after a compaction the only
memory a session can see is the root file, so a session that re-derives a relocated fact and
helpfully records it writes it **into the root file** — a duplicate of content in a lazy artifact it
cannot see. All four cap the root file's volume; none detects the duplication. Report-only lint: for
each content line in `AGENTS.md`, flag a normalized near-match in `docs/REFERENCE.md` or
`.claude/**/*.md`. The point is that the condition becomes visible.

**Negative control:** a synthetic root file containing a verbatim `docs/REFERENCE.md` paragraph must
be reported.

### 6.9 The canary

Covered in §3. Its negative control is the re-run after `git checkout --`: the same answer both
times means the probe is broken and must not be acted on.

---

## 7. Owner decisions

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **OD-1** | Terminal `AGENTS.md` ceiling | **18,000 chars / 200 lines** · 32,443 (the mechanical residue) · other | **18,000 / 200.** 32,443 is the residue of deleting three sections and changing nothing else; the drafted core is 15,623, so 18,000 gives 2,377 chars of honest headroom without inviting a dense-but-unreadable core. |
| **OD-2** | Rate axis after P6 | reported forever · promote to blocking (additions-only, per-PR) | **Reported forever, level blocking.** With the file at 15,623 against an 18,000 ceiling, the level axis is the binding constraint and it is per-PR deterministic. A blocking rolling-window rate under `strict_required_status_checks_policy: true` re-opens AV-N3 for no additional protection. |
| **OD-3** | `MEMORY.md` — which lever, and how far to evict | evict only · **evict + cap NEW entries at 120 B** · cap all entries (rewrite) | **Evict + forward-only 120 B cap.** Eviction is primary (MECH §2b): the strict set alone is 24 entries / 4,147 B ≈ 90% of the headroom, and it is nearly free. Eviction alone buys ~35 days; the forward-only cap costs zero churn and takes it to ~69. Reject the clip-all variant (113 of 139 live entries rewritten for less). How far to evict — strict 24 / MECH's 35 / broad 43 — is the owner's call on what "finished" means; I would take the broad set and rely on the topic files. |
| **OD-4** | Parent `Juniper/AGENTS.md` (11,016 B, additive to all nine repos, **no `.git`**) | leave · `claudeMdExcludes` · **put under version control** | **Version control it** — its own small repo carrying the same four `AGENTS.md` gates, or a hashed snapshot vendored into juniper-ml with a drift test. `claudeMdExcludes` rests on the unverified `Rzr` predicate (MECH §8 item 3), lives in a gitignored settings file, and does not help the other eight repos. This is a prerequisite for anyone ever *deleting on the strength of* the parent — which is why B's position is untenable and A's (which *adds* ~150 chars to it) is worse than it looks. |
| **OD-5** | Two resident rules asserted from operating practice, not from a repo artifact — "deployment / PyPI approvals are the owner's" and "merge only on the owner's explicit per-PR approval" | confirm · strike · reword | **Confirm both.** They are recorded in the project's auto-memory index as standing feedback, not in any repo artifact — which is exactly why they belong in `## Traps With No Gate`. But the owner is the only source. |
| **OD-6** | Soak pass bar and rollback trigger (§P6) | ≥80% pointer-follow · other · no bar | **≥80% follow, and zero incidents in which a session contradicted a relocated contract.** The second half matters more than the first: a low follow rate costs turns, a contradicted contract costs work. |
| **OD-7** | Fleet scope and timing | ml only · ml + canopy + cascor at P7 · all nine | **Gates to all nine at P7; prune ml only.** See §9 — the prune is not portable without a per-repo destination analysis. |
| **OD-8** | The `memory-budget` job's final name — does it carry an `(Advisory)` suffix? | yes · no | **No suffix.** Decide **before P2**: the `e209b74` commit body states the suffix is part of the context string, so renaming at promotion breaks the required context. Ship the final name from day one. |
| **OD-9** | `tests/test_assert_release_tag.py` runs in no workflow, and `AGENTS.md:485` documents flags the script does not accept | fix now as a standalone PR · allowlist in P1 and fix later | **Fix now, standalone.** It is a live publish-path defect, it is out of this plan's scope, and it **gates** P1's G12 lint and every Q2-grounded relocation in P4/P5. File it as its own issue and PR. |

---

## 8. Residual risk after full execution

Stated plainly. None of these is solved by this plan.

1. **The pointer-follow rate remains unmeasured until P6, and unmeasurable in advance.** If the
   soak fails, the plan degrades to a large one-time cut plus a ratchet — still better than today,
   but the attention benefit is asserted, not demonstrated. MECH §8 item 6: no published Anthropic
   benchmark measures adherence against memory size.
2. **Post-compaction re-accretion has only a report-only detector** (§6.8). A report nobody reads is
   indistinguishable from no report.
3. **The docs screen stays blind to this migration's edit shape.** After P5, "delete four
   sub-bullets, add a pointer line, keep the heading" is still `small-deletion / WARN`, green, at any
   magnitude. The block-relocation proof covers the migration PRs; ordinary future PRs are covered
   only by the standing convention *token-diff before waiving; restore, don't waive*. That is a
   convention, not a mechanism. An upstream `juniper-ci-tools` issue for a `--max-net-deletion` rule
   counting per-file net removed lines independently of the pure-run predicate is the right long-term
   fix and is **not** in this plan.
4. **`MEMORY.md` cannot be enforced by CI.** It lives outside the repository. Everything in P0 is a
   local check plus operator discipline, and the file is written by the agent, not by a human
   following a convention. P0 buys ~69 days on the strict eviction set (~88 on the broad
   one), not a solution.
5. **The parent `Juniper/AGENTS.md`** stays ungoverned unless OD-4 says otherwise — 10,818 chars
   additive to every session in all nine repos, with no history, no diff, no review, no revert.
6. **`docs/REFERENCE.md` grows unboundedly.** 162,231 bytes and rising faster than `AGENTS.md`.
   On-demand loading makes it cheap, not navigable; at 500 KB it needs its own split. This plan
   *reports* its rate and does not gate it, because gating a read-on-demand file would be enforcing
   the wrong thing.
7. **The highest-volume writer may not read `AGENTS.md` at all.** Whether the Cursor fleet reads
   repo `AGENTS.md` at generation time is still open (flood analysis OQ3). If it does not, the
   routing procedure has no effect on that population and the gates carry 100% of the load — and
   three always-bypass actors can click-merge past every gate anyway. **The guaranteed value of
   every gate here is the visible red at review, not prevention.**
8. **`main-verify.yml`'s battery-sync convention has an observed ~20% miss rate** (18 of 88 test
   modules absent, AV-G5). Assume any new gate does **not** run post-merge unless someone checks.
9. **Skill and agent budgets are untouched.** `.claude/agents/` has its own `EXl=15000` warning
   threshold and this repo ships six agents; the skill listing consumes ~1% of the context window
   with least-invoked descriptions dropped first. This plan adds neither, which is a benefit, not a
   fix.
10. **The 4 MiB whole-file skip** (MECH §8b) is not near-term — we are at 4% — but it is the actual
    cliff and it fails by dropping the file **whole**, silently. The size gate guards it incidentally.
11. **`eR()` = 4 or 3 chars/token is unverified.** At 3, today's always-on load is 34.0% of a 200k
    window rather than 25.3%. `/context` would settle it and is TUI-only.

---

## 9. Fleet applicability

BASE §7: canopy **94,373** chars, cascor **70,118**, data 41,371, deploy 33,373, worker 33,203,
cascor-client 29,457, data-client 24,706, recurrence 9,990. A canopy session already carries ≈109K
of always-on instructions before its own work begins.

**The gates port. The prune does not.**

- **Portable, at P7:** `tests/test_agents_md_size_budget.py`, `tests/test_agents_md_shape.py`, the
  G12 mirror lint, and the `memory-budget` job shape. The precedent is already in this repo:
  `tests/test_agents_md_header_schema.py:40-48` is deliberately self-locating and droppable into any
  Juniper repo's `tests/`. Per-repo ceilings start at current size and ratchet down.
- **Not portable:** the deletions. juniper-ml's entire thesis rests on 162,231 bytes of
  already-written `docs/REFERENCE.md`. **Whether canopy and cascor have an equivalent destination is
  unverified and must be measured before anything is deleted there.** If they do not, P7 for those
  repos is gates-only plus a P3-equivalent authoring effort, and the schedule is materially longer.
- **What we deliberately avoided.** Because the destinations are `docs/**` and `notes/**`, the docs
  screen's `--scope` is unchanged, so **no nine-repo coordination is required**. Under A or B it
  would have been: the required context is `Sequence Safety` on ml and `Sequence Safety (Advisory)`
  on the other eight, the suffix is part of the string, and `--scope` **replaces** the default rather
  than extending it.
- **The parent file is the fleet's single largest ungoverned lever** (OD-4) and it affects all nine
  at once.

---

## 10. What I am not confident in

- **The 15,623-char target is a plan, not a measurement.** Every "After" column in every proposal is
  a plan; the arithmetic audit says so of all four. I verified the arithmetic reconciles exactly
  through the P4/P5 ladder. I cannot verify that `## Where To Look` can be written in 2,000 chars and
  still be navigable, nor that the twelve smaller sections survive their targets. If the core
  overshoots, the ceiling holds and the overflow goes to `docs/REFERENCE.md` — but the *readability*
  of the result is the thing I would check hardest at P5 review.
- **The soak's pass bar is a guess.** ≥80% is C's suggestion and mine; no evidence sets it.
- **The `MEMORY.md` entry rate (1.06/day) may track session volume rather than time.** If it does,
  P0's ~69 days is optimistic. The entry-size trend (134.4 → 234.8 B, +75%) is also unexplained;
  entries are additionally edited in place and grow, which is invisible to every estimator and can
  only push the horizon earlier.
- **The `no-worsening` rule is my design, not an audited proposal element.** I believe it removes
  AV-G4 and AV-O2b cleanly, and I cannot point to an existing gate in this repo shaped that way. It
  should be reviewed on its own merits.
- **Whether the harness's "`Edit` requires a prior `Read`" bookkeeping survives compaction** is
  unresolved (adversarial §"could not verify" item 1). It does not affect this plan, because this
  plan uses no `paths:` rules — but it *would* affect the P6 failure ladder's last rung.
- **`/doctor`'s trim proposer** (C §10, C's Phase 1 accelerant) is TUI-only and was not exercised by
  any validator. I have deliberately not made any phase depend on it. It is worth running by hand
  before P5 as an accelerant with a hand-reviewed diff, which is C's own posture.
- **I did not re-query the eight sibling repos' ruleset state.** The fleet-wide claim about
  `Sequence Safety (Advisory)` rests on the `e209b74` commit body, which I read, not on nine live
  API calls.

---

## Related documents

| Document | Role |
|---|---|
| [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) | BASE — sizes, growth curve, existing gates |
| [Memory mechanism facts](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) | MECH — §2a the fuse, **§2b eviction over capping**, §4c-bis compaction, §8c the canary, §8d the screen |
| [Proposal A](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md) · [B](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md) · [C](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md) · [D](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md) | the four subjects |
| [Grounding audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-GROUNDING-AUDIT.md) · [Arithmetic audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ARITHMETIC-AUDIT.md) · [Adversarial audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ADVERSARIAL-AUDIT.md) | the three validation passes |
| [`../AGENTS.md`](../AGENTS.md) | the file under discussion |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | the single authoritative relocation destination |
| [`../docs/DOCUMENTATION_OVERVIEW.md`](../docs/DOCUMENTATION_OVERVIEW.md) | the "I Want To" index `## Where To Look` is modelled on |
| [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) | `:626` / `:636` the `test_agents_md_*` wiring · `:720-740` the standalone-job shape · `:776` the trailers-file idiom · `:868` / `:877` the two screens |
| [`../.github/workflows/main-verify.yml`](../.github/workflows/main-verify.yml) | `:196` the post-merge docs screen — why the trailer must survive the squash |
| [`../.github/workflows/agents-md-touch-up.yml`](../.github/workflows/agents-md-touch-up.yml) | the date check every multi-phase migration trips |
| [`../.github/workflows/pr-budget-alarm.yml`](../.github/workflows/pr-budget-alarm.yml) | the daily-alarm contract the memory alarm is modelled on |
| [`../tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) | `:109-112` the negative-control model · `:114-116` the `agent_templates/` assertion |
| [`../tests/test_agents_md_header_schema.py`](../tests/test_agents_md_header_schema.py) | `:40-48` the self-locating idiom that makes the gates portable |
| [`../tests/test_service_fork_drift.py`](../tests/test_service_fork_drift.py) | the two-sided ledger pattern the destination inventory copies |
| [`../tests/test_archive_guard_workflow.py`](../tests/test_archive_guard_workflow.py) | the workflow-lint model for `test_memory_budget_workflow.py` |
| [`../util/release_train/archive_guard.py`](../util/release_train/archive_guard.py) | the structural-guard shape the inbox guard inverts |
| [`../util/assert_release_tag.bash`](../util/assert_release_tag.bash) · [`../tests/test_assert_release_tag.py`](../tests/test_assert_release_tag.py) | OD-9 — the pin that runs in no workflow |
| [`../util/worktree_cleanup.bash`](../util/worktree_cleanup.bash) | Phase 7, the main-checkout refresh the H-a ordering depends on |
| [`../scripts/wake_the_claude.bash`](../scripts/wake_the_claude.bash) | P0's session-start banner host |
| [Cursor PR flood remediation analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) | the #801/#803 prose-deletion class the docs screen exists for; OQ3 on the fleet |
| [notes/ naming convention](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) | this document's filename rules |
