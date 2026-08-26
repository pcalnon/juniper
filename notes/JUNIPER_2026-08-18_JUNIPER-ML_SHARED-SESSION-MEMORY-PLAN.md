# Shared Session Memory — Vetted Plan

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-26

---

## 0. What this is

The reconciled, executable plan for the memory-file size problem, produced by
eleven agents across four stages: two independent fact-finders, four independent
proposal authors, three independent validators, and two independent synthesists.

This document is the decision and the sequence. It deliberately does **not**
restate the evidence — that lives in the supporting documents, and a 60 KB plan
about file bloat would be its own refutation.

| Document                                                                                                 | Role                                                   |
|----------------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md)         | Measured sizes, growth curve, accretion signature      |
| [Mechanism facts](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md)                   | What Claude Code 2.1.235 actually does (docs + binary) |
| [Proposal A — Skills](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md)  | Rejected as architecture; parts retained               |
| [Proposal B — Locality](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md)         | Rejected                                               |
| [Proposal C — Dedup/prune](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md) | **Adopted** (corrected)                                |
| [Proposal D — Governance](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md) | **Adopted** (corrected, resequenced)                   |
| [Grounding audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-GROUNDING-AUDIT.md)           | 0 CRITICAL, 3 MAJOR                                    |
| [Arithmetic audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ARITHMETIC-AUDIT.md)         | 2 CRITICAL, 11 MAJOR                                   |
| [Adversarial audit](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-VALIDATION-ADVERSARIAL-AUDIT.md)       | 0 FATAL, 20 SERIOUS                                    |
| [Synthesis 1](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-ARCHITECTURE-SYNTHESIS-1.md)                          | Independent plan                                       |
| [Synthesis 2](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-ARCHITECTURE-SYNTHESIS-2.md)                          | Independent plan                                       |

---

## 1. The decision

**Adopt Proposal C's subtractive core, held in place by Proposal D's ratchet.
Reject B outright. Reject A's thesis; retain A's verified binary findings and
its skill-listing discipline for later, optional use.**

Both synthesists reached this independently, by the same three axes.

### Why not on the headline numbers

The eager-context column cannot choose. Normalised to one denominator:

|                     |      A |      B |      C |       D |
|---------------------|-------:|-------:|-------:|--------:|
| Eager after (chars) | 34,586 | 27,995 | 30,459 | 182,476 |
| % of a 200k window  |   6.8% |   6.0% |   6.3% |   25.3% |

A, B and C land within **0.8 points of a 200k window** of one another. Anyone
choosing on the advertised percentages (−87.9% / −84.6% / −90.3%) is comparing
three different denominators.

### The three axes that do decide

1. **Worst case, not average.** C −83.3% **unconditional**; A −3.5%; B −0.9%.
   C's content leaves the memory system, so it cannot come back. A's skills and
   B's nested files can all be pulled into one wide-ranging session. This is a
   choice about *variance*, and 73% of sessions being narrow does not help the
   27% that are not.
2. **Compaction.** A's and B's carriers sit in the "lost until re-triggered" row
   ([mechanism facts §4c-bis](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md)).
   This project's mitigation — handoff instead of compaction — is itself advisory
   prose with no compliance guarantee. C's residual is re-injected from disk.
3. **The content-loss screen.** `in_docs_scope` (`docs_additions_check.py:62-66`)
   returns **False** for every `.claude/` destination. C's `docs/REFERENCE.md`
   and D's `notes/` inbox are the only pair that keeps the corpus under the only
   mechanical content-loss alarm the fleet has — without a nine-repo `--scope`
   change.

### The tradeoff being accepted, stated plainly

**Guaranteed availability of component lore is traded for guaranteed,
unconditional context reduction.** Under C, an agent must decide to read
`docs/REFERENCE.md` rather than knowing a fact for free.

This is a real cost and it is only partly bought back (by a resident hazard list,
§4 P3). It is accepted because the alternatives purchase availability with
mechanisms that vanish at compaction, into destinations outside the only
content-loss alarm — and because the index-over-corpus pattern **already runs in
this project at 53:1** (154 auto-memory files, 1,082,901 bytes on disk, 20,388
loaded).

The pointer-follow rate is **not measurable in advance**. It is falsified ex post
by the N≥20 soak in §6, with a fixed escalation ladder: *index row → CI gate →
path-scoped rule*, **never re-inline**.

---

## 2. Corrections that must be applied before execution

Neither adopted proposal is executable as written. These are mandatory.

| # | Correction | Source | Verified |
| --- | ----------- | -------- | ---------- |
| C1 | **Ratchet ships BEFORE the cut**, not after. D sequences it last — correct for D alone, wrong for a hybrid: a two-week gap admits ~43,000 chars, then the ceiling is fixed at the inflated level. | Synthesis 2 | arithmetic |
| C2 | **`docs/REFERENCE.md` is the single destination.** C routes 4,417 chars to module docstrings; the symbol screen inventories only `FunctionDef`/`AsyncFunctionDef`/`ClassDef` (`symbol_loss_check.py:235-268`) and `.py` is outside the docs scope — so a module docstring is outside **both** screens. | Synthesis 2 | ✅ confirmed at source |
| C3 | **No-worsening rule**: the level gate fails only if the merge result exceeds the ceiling **and** exceeds the base. Keeps a hard ceiling without blocking an unrelated PR when main is already over. Stated by no proposal. | Synthesis 2 | design |
| C4 | **Canary must be plain text, not an HTML comment** — those are stripped before injection, so `ABSENT` would conflate "ancestor not loaded" with "comment stripped". Add a positive control. | Both synthesists, independently | ✅ mechanism facts §4d |
| C5 | **One heading needs byte-preservation, not two.** `#script-placement-mandatory` has 6 live inbound refs; both refs to `#worktree-procedures-mandatory--task-isolation` are in `notes/legacy/`, excluded at `ci.yml:1083`. | Synthesis 1 | ✅ confirmed |
| C6 | **The trimmed tree must retain a nested `agent_templates/` node.** B's and C's proposed top-level-only trees fail `tests/test_agents_md_tree_drift.py:114-116`. | Arithmetic audit | ✅ confirmed |
| C7 | **`MEMORY.md`: evict, then cap forward-only.** Eviction alone buys ~35 days; a 120 B cap on *new* entries only (zero churn) reaches ~69. | Mechanism facts §2b + Synthesis 2 | ✅ confirmed |
| C8 | **G3's negative control must be non-tautological**: a relocation carrying identifiers but dropping prose must FAIL. C's token-level G1 passes on exactly that loss. | Synthesis 1 | design |
| C9 | Gates go in a **standalone job**, absent from the Quality Gate `needs:` — D's pattern. A/B/C wire into `Regression Tests`, a required push-triggered context. | Adversarial audit | design |

---

## 3. Sequencing

Two clocks run at different speeds, and they invert the intuitive order.

- **`MEMORY.md` has a ~19-day fuse** and loses data **silently, newest-first**.
- **`AGENTS.md` loses nothing, ever** — it costs tokens and attention.
- **Any level fix without a rate fix is undone in 44 days.**

So: fix the thing that is actually losing data first; install the ratchet before
cutting; cut last.

```bash
P0  MEMORY.md eviction            ← urgent, independent, ~1 hour
P1  Worktree canary probe         ← gates P3 ordering, ~15 min
P2  Budget gate, ADVISORY         ← must precede the cut (C1)
P3  The cut                       ← C's phase-3 pattern
P4  Promote gate to BLOCKING      ← after soak
P5  Fleet rollout                 ← canopy, cascor, then the rest
```

---

## 4. Phases

### P0 — `MEMORY.md` eviction *(do this first; it is the only live data loss)*

Evict index rows whose work is finished (CLOSED / RESOLVED / COMPLETE / SHIPPED /
REFUTED). Recovers 90–148% of the 4,612-byte headroom depending on marker set,
and is **nearly free**: the topic file survives on disk, so the item moves from
resident to on-demand rather than being deleted.

Then apply a **forward-only** 120-byte cap on new entries (C7) — no rewriting of
existing rows.

- **Rollback**: restore the index from the topic files; nothing was deleted.
- **Negative control**: assert the evicted topic files still exist and are
  readable after eviction.

### P1 — Worktree canary probe *(gates P3)*

Resolve [mechanism facts §8c](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md):
does the main checkout's `AGENTS.md` load as an ancestor when it differs from the
worktree's? `claudeMdExcludes` is confirmed absent from
`.claude/settings.local.json`, so this is a clean two-way test between
content-dedup and worktree-aware root detection.

Method: add a **plain-text** marker (C4) to the main checkout's file, start a
session in a worktree, ask whether the marker is present. Positive control first:
marker in the worktree's own file, confirm it *is* seen.

**Why it gates P3**: under the dedup hypothesis, a trimmed worktree file against
an untrimmed main file causes **both** to load — context goes *up* by ~9% during
migration. That determines merge-to-main-first vs trim-in-worktree-first.

- **Rollback**: remove the marker.

### P2 — Budget gate, advisory *(must precede P3 — C1)*

A standalone CI job (C9) measuring `AGENTS.md` in **characters**, with:

- the **no-worsening rule** (C3),
- an `Allow-Budget-Overrun:` trailer as a **loan** (ceiling unchanged; debt
  visible), noting the adversarial audit's finding that with 23 worktrees there
  is no single "next author" — so the loan must be tracked centrally, not
  implicitly,
- a **ratchet** that can only tighten.

Soak advisory, exactly as this repo soaked `Sequence Safety` before promoting it.

- **Negative control**: a synthetic over-budget fixture must FAIL, and an empty
  file list must FAIL rather than pass vacuously.
- **Rollback**: delete the job; it is standalone and nothing depends on it.

### P3 — The cut

Target: **≤ 32,443 characters** (the corrected residue figure — the original
34,263 subtracted characters from bytes). Relocate `## Key Files`,
`## Repository Structure` and `## CI/CD Pipelines` into `docs/REFERENCE.md`
(C2 — no module docstrings), keeping:

- the genre-A behavioural core,
- a **resident hazard list** — the small set of directives whose non-application
  destroys work (the reaper's live-experiment protection, `KILL_WORKERS`, the
  `[skip ci]` orphan trap, the `max_epochs`/`output_epochs` divergence),
- `#script-placement-mandatory` **byte-preserved** (C5),
- a nested `agent_templates/` tree node (C6).

Use C's phase-3 pattern, which all three audits rated best-in-class. Each PR
carries `Allow-Docs-Rewrite:` **into the squash commit message** — and note that
the docs screen is blind to the pointer-shaped deletion at any magnitude
(mechanism facts §8d), so **the trailer is not the safety net; G3 is.**

- **Negative control (C8)**: a relocation that carries identifiers but drops
  prose must FAIL. Verify this before trusting the phase.
- **Rollback**: per-PR revert; content is relocated, never deleted, so a revert
  restores byte-for-byte.

### P4 — Promote the gate to blocking

Only after the P2 soak is clean and P3 has landed. Set the ceiling at the
achieved level, not the aspirational one.

### P5 — Fleet rollout

**Status: IN PROGRESS — 8 of 9 governable repos governed, all 8 BLOCKING with declared slack; none promoted.** Tracking issue:
[juniper-ml#1326](https://github.com/pcalnon/juniper-ml/issues/1326) — its comment thread is the live
per-repo ledger; read it before trusting this banner. Ports merged 2026-08-25:
[juniper-canopy#516](https://github.com/pcalnon/juniper-canopy/pull/516) (`611141c1`, ceiling 95,133) and
[juniper-cascor#585](https://github.com/pcalnon/juniper-cascor/pull/585) (`c83c3407`, ceiling 71,098);
merged 2026-08-26 under the owner's arc-wide authorization, squash-of-one each:
[juniper-cascor-client#139](https://github.com/pcalnon/juniper-cascor-client/pull/139) (`b1c1acd7`, 34,695),
[juniper-recurrence#131](https://github.com/pcalnon/juniper-recurrence/pull/131) (`369d8f59`, 11,578; standalone workflow),
[juniper-data-client#173](https://github.com/pcalnon/juniper-data-client/pull/173) (`918f1dee`, 28,369),
[juniper-data#291](https://github.com/pcalnon/juniper-data/pull/291) (`19b84a8a`, 43,493),
[juniper-cascor-worker#162](https://github.com/pcalnon/juniper-cascor-worker/pull/162) (`177c2a15`, 35,126),
[juniper-deploy#195](https://github.com/pcalnon/juniper-deploy/pull/195) (`7e046491`, 34,569).
juniper-slacker has no `AGENTS.md` and nothing to govern. **Preconditions 2–4 (step d) shipped 2026-08-26
evening — all 8 BLOCKING with declared slack**: one signed PR per repo on
`feat/memory-budget-blocking` removed `--advisory`, re-ran the three controls against the non-advisory
job, and raised the ceiling with an `Allow-Ceiling-Raise: AGENTS.md` trailer sized as max(largest
30-day growing commit, a 2,000 fan-out floor) —
[juniper-deploy#196](https://github.com/pcalnon/juniper-deploy/pull/196) (`1fe58592`, 34,569 → 36,569),
[juniper-recurrence#132](https://github.com/pcalnon/juniper-recurrence/pull/132) (`a80a7dc9`, 11,578 → 13,698),
[juniper-cascor-worker#163](https://github.com/pcalnon/juniper-cascor-worker/pull/163) (`cf5ae76d`, 35,126 → 37,126),
[juniper-cascor-client#140](https://github.com/pcalnon/juniper-cascor-client/pull/140) (`87464c35`, 34,695 → 37,277),
[juniper-data#294](https://github.com/pcalnon/juniper-data/pull/294) (`e0b738e6`, 43,493 → 45,493),
[juniper-cascor#591](https://github.com/pcalnon/juniper-cascor/pull/591) (`c6cd2f09`, 71,098 → 80,707, its own max),
[juniper-data-client#174](https://github.com/pcalnon/juniper-data-client/pull/174) (`a3226826`, 28,369 → 30,442);
[juniper-canopy#529](https://github.com/pcalnon/juniper-canopy/pull/529) (`9f6fac97`, 95,133 → 97,133).
`Memory Budget` reported SUCCESS on every one of those PR heads through the non-advisory job
(`[RAISE-WAIVED] … headroom=<slack>`), and every squash SHA above was re-probed against the ceiling in that
repo's `conf/memory_budget.json` and the checker's invocation line in its workflow. For all eight, all four
preconditions now hold; what remains is the promotion write itself — `require_context_safely.py --apply`,
per repo, on the owner's explicit go.
**Nothing is promoted.** *(Status updated 2026-08-26 evening; the same morning it read "2 of 9". Status
may not be demoted or left stale — §4a.)*

> **This section was a four-line stub until 2026-08-24.** The working procedure lived only in
> a session handoff, and handoffs lose material across generations — an earlier one in this
> arc amputated this recipe entirely and only independent validation caught it. It is written
> down here so the next attempt does not have to reconstruct it.

#### The order is mandatory: RATE axis before LEVEL axis

A ceiling set *after* a cut locks in the inflated level; a cut without a ceiling is undone in
about 44 days. `AGENTS.md` reached ~170K in this repo **while under four active CI gates** —
172 of 200 main-line merges grew it, 14 shrank it, by 2,628 bytes between them. Every one of
those gates enforced structure or currency; none measured size.

**Do not order the fleet by size** ("canopy is the big win, start there"). Port the ratchet
first, everywhere; cut afterwards.

#### Current sizes and rates — RE-MEASURE, never transcribe

Measured 2026-08-25 with
`python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth <repo-path> --days 30`
(`AGENTS.md` in **chars**, the unit the ceiling uses; `docs/REFERENCE.md` in bytes from the API
census). They move daily; the table is evidence that they move, and the **rate column is the
ordering input** — the size column is not. `measure-growth` measures the checkout's **HEAD**
unless you pass `--ref origin/main` after a fetch — do that: a primary that has not been pulled
reports yesterday's `main` as today's rate (the flag was lost in the #1378 → #1379 fold and
restored 2026-08-26; the `render-*` commands always measure the checkout, because a port renders
into it). Re-measured 2026-08-26 from primaries at `origin/main`: cascor and deploy unchanged.

| Repo | `AGENTS.md` | Rate/day | Net 30 d | Max single commit | `docs/REFERENCE.md` | Status |
|---|---:|---:|---:|---:|---:|---|
| juniper-cascor | 71,098 | **730** | +21,891 | 9,609 | **none — create first** | BLOCKING, ceiling 80,707 (#585 → #591) |
| juniper-cascor-client | 34,695 | 196 | +5,884 | 2,582 | 14,119 | BLOCKING, ceiling 37,277 (#139 → #140) |
| juniper-recurrence | 11,578 | 137 | +4,102 | 2,120 | **none — create first** | BLOCKING, ceiling 13,698 (#131 → #132, standalone workflow) |
| juniper-data-client | 28,369 | 135 | +4,055 | 2,073 | 11,976 | BLOCKING, ceiling 30,442 (#173 → #174) |
| juniper-data | 43,493 | 109 | +3,257 | 1,982 | 19,883 | BLOCKING, ceiling 45,493 (#291 → #294) |
| juniper-canopy | 95,133 | 81 | +2,425 | 1,982 | 9,328 | BLOCKING, ceiling 97,133 (#516 → #529) |
| juniper-cascor-worker | 35,126 | 66 | +1,982 | 1,982 | 12,122 | BLOCKING, ceiling 37,126 (#162 → #163) |
| juniper-deploy | 34,569 | 66 | +1,982 | 1,982 | 18,673 | BLOCKING, ceiling 36,569 (#195 → #196) |
| juniper-ml | 36,960 | — | — | — | 336,020 | GOVERNED, BLOCKING + required; ceiling 38,000 |
| juniper-slacker | — | — | — | — | — | no `AGENTS.md` at all |

Two things the table shows that the size axis hides. cascor's file is smaller than canopy's and
grows **nine times faster**, which is the whole case for ordering by rate. And the same **+1,982**
growth appears in six of eight repos: one fleet-wide `AGENTS.md` fan-out adds ~2K to every file
at once, so per-repo slack has to absorb that class — a zero-slack ceiling fires fleet-wide on
the first fan-out, by construction. Size the slack from `max`, not from the helper's `p90`, which
is unreliable below ~10 growing commits.

#### Per-repo recipe

**a. Copy three files.** [`util/memory_budget_check.py`](../util/memory_budget_check.py),
[`tests/test_memory_budget_check.py`](../tests/test_memory_budget_check.py),
[`conf/memory_budget.json`](../conf/memory_budget.json). Both scripts take `--repo-root` and
are repo-agnostic; nothing in them is juniper-ml-specific.

**b. Seed the ceiling IN the target repo — measured, never transcribed.** Not 38,000, not
32,443, not anything in the table above. `--ratchet` only **lowers** an existing `ceiling_chars`
entry (`if row["chars"] < row["ceiling"]` in `util/memory_budget_check.py`); it never raises one,
so a config copied from juniper-ml seeds nothing in a repo whose `AGENTS.md` is already larger
than 38,000 chars (canopy, cascor, data) and the first check fails as over-budget. Render the
config in the target instead — it writes the measured size as the ceiling — then confirm with
`--ratchet`, which prints `no ceiling could be tightened` when the ceiling is already exact:

```bash
python3 <juniper-ml>/util/ad-hoc/2026-08-25_p5_port_memory_budget.py render-config . --out conf/memory_budget.json
python3 util/memory_budget_check.py --repo-root . --ratchet
```

`--ratchet` **seeds** (down from a placeholder above the current size); it does not **tighten**
gracefully after a cut. Run in a repo that already has a ceiling, straight after a cut, it leaves
ZERO headroom and fails the next author on a single character — hand-edit with slack sized to the
observed burn instead (this repo: +937 over four days / five PRs, median +58, one docs PR +605).
*(Corrected 2026-08-26: this step used to say `--ratchet` alone was "the only correct way" to set
a first ceiling; for the three repos above it sets nothing.)*

**c. Copy the standalone `memory-budget` job** from [`ci.yml`](../.github/workflows/ci.yml)
(job `memory-budget`, `name: Memory Budget`). **Standalone — NOT in the Quality Gate
`needs:`** (correction C9). A `needs:` entry is the wrong promotion mechanism; the ruleset is
the right one, which is how `Sequence Safety` was promoted.

**d. Soak `--advisory`, remove it, then run three negative controls BEFORE promoting.**

| Control | Expected |
|---|---|
| clean tree | exit 0 |
| +500 chars to the governed file | exit 1 |
| `Allow-Budget-Overrun: <path>` trailer | exit 0 |

**A blocking gate that cannot fail is worse than none** — it converts an unmeasured risk into
a measured-looking one. Promotion to a required context is a governance change (owner-approved)
with **four preconditions, all of them**:

1. the port is merged to that repo's `main`;
2. `--advisory` has been **removed** from the job — promoting an advisory job creates a required
   check that cannot fail, the vacuous-pass class;
3. the three negative controls above were re-run against the **non-advisory** job — the controls
   gate removing `--advisory`, not promotion; an earlier handoff collapsed the two steps;
4. the ceiling has real slack. A ceiling seeded by `--ratchet` has none, and once blocking it
   fails the next author on one character. Raise it with an `Allow-Ceiling-Raise: AGENTS.md`
   commit trailer, sized to that repo's **re-measured** largest single commit (table above:
   canopy ≥ 2,000; cascor's largest was 9,609).

*Status 2026-08-26 evening: preconditions 1–4 hold for all eight repos (the banner above lists the PRs,
squash SHAs and ceilings); nothing is promoted — the ruleset write is the owner's decision, per repo.
Do not read `advisory=True` or a `NONE` REFERENCE.md from an unpatched
`util/ad-hoc/2026-08-26_p5_fleet_state.py` census as state: before ml#1403 it matched `--advisory`
anywhere in the workflow text (comments included) and turned any non-2xx API reply into "absent".
Probe the invocation line and the file directly.*

Only then, and with the writer that pre-flights the context string:

```bash
python3 util/ad-hoc/2026-08-20_require_context_safely.py --status                                  # what is required today
python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo <repo> --context 'Memory Budget'          # dry run (default)
python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo <repo> --context 'Memory Budget' --apply  # the write
```

It **refuses by default** unless that exact context string has been observed reporting on a
recent commit in that repo; `--allow-unobserved` is the dangerous opt-out, and there is no
`--require-observed` flag (one handoff cited one — observed-only is simply the default). It
snapshots the ruleset to disk before the PUT, carries `rules` and `bypass_actors` verbatim, and
re-reads after. Prefer it over `2026-08-20_add_required_context.py`, which writes no snapshot and
verifies contexts only — the gap it leaves is *"SILENT and TOTAL"*: a required context nothing
publishes is never satisfied, and that is how `main` went unmergeable on five repos.

Two things its pre-flight will show that are **not** defects, verified on all eight ports 2026-08-26.
Every port carries ml's guard `if: github.event_name == 'pull_request' || github.event_name ==
'merge_group'`, so the `Memory Budget` check-run on **every `main` commit has conclusion `skipped`**
(recurrence's standalone workflow is `pull_request`-only and publishes nothing on `main` at all) — the
ratchet is a diff-against-base rule and has no meaning on a push. And `observed_contexts()` reads
check-run **names** on the heads of the eight most recently updated PRs, conclusion-agnostic, so a
port is "observed" from the moment its own PR ran the job; the `skipped` rows on `main` neither help
nor hurt. **Do not reach for `--allow-unobserved` because `main` shows `skipped`.** The pre-flight
refuses honestly only when none of those eight PR heads ran the job at all.

**e. Then G3, then the cut.** Relocate with
[`util/ad-hoc/2026-08-19_p3_relocate_section.py`](../util/ad-hoc/2026-08-19_p3_relocate_section.py)
— byte-for-byte, so G3 passes by construction. **Its argument order is load-bearing**
(rationale at `:54-73`): reversed, it silently redirects every destination anchor back at the
source, with no error. Verify with
[`util/relocation_check.py`](../util/relocation_check.py) `--expect-removals`; that local run
IS the content-loss control, because G3 runs `--advisory` in CI and does not exist post-merge,
so a green PR proves nothing (§7.2).

For **juniper-cascor** and **juniper-recurrence**, create `docs/REFERENCE.md` before
relocating anything into it.

#### Porting hazards, measured on the first two ports — pre-commit catches NONE of these

- **`Version:` header lines cut both ways.** cascor forbids them repo-wide via a pytest test in a
  *different* file (`test_no_version_header_lines_in_source`, BUG-CC-04) that rglobs `src/**`, so
  a verbatim port fails while the ported file's own tests pass (cascor#585 was red for exactly
  this). juniper-data-client enforces the **inverse**: every `Version:` under `tests/` and the
  package must **equal `__version__`** (`tests/test_file_header_versions.py`). Both are invisible
  to pre-commit. **Run the target repo's FULL unit suite during a port.**
- **bandit strictness differs per repo, and `# nosec` codes must be SPACE-separated.** On bandit
  1.9.4 `# nosec B603,B607` suppressed B607 and left B603 reported — the count *drops*, so the
  comma form reads as applied. ml's own comma forms are inert (its hook skips those codes), so
  ml's copy is not evidence. Run the target repo's own `pre-commit run --files <paths>`.
- **`REPO_ROOT` depth.** `tests/` → `parents[1]`; `src/tests/` (canopy, cascor) → `parents[2]`;
  `juniper_data/tests/unit/` → `parents[3]`. Wrong depth does not raise; it resolves to the wrong
  directory and fails later as a missing config.
- **Test selection.** juniper-data's unit lane runs `-m "unit and not slow"` over
  `juniper_data/tests/unit` only; the ported test must live there and carry
  `pytestmark = pytest.mark.unit` (strict markers) or it is silently deselected — a vacuous port.
  The other repos run `pytest tests/` unfiltered.
- **Workflow shape.** juniper-recurrence has no `ci.yml`; its per-package lanes each carry a
  `required-checks` job. Use a **standalone workflow** like its `sequence-safety.yml`. juniper-deploy
  has no `conf/` — create it. Every repo's Python-version env var and pinned action SHAs differ;
  copy them from the target's own `ci.yml`, never from canopy's block.

#### HAZARD — do not demote this to a pointer

**The cut must land on that repo's `main`, with its primary checkout pulled, BEFORE any
worktree carries the trimmed file.** A trimmed worktree sitting over an untrimmed ancestor is
the **worst** case available: loaded context goes **UP**, not down, because both copies are
resident. This is the one ordering mistake that makes the whole exercise counter-productive.

---

## 4a. Execution log — P0 and P1 (2026-08-19)

### P0 — `MEMORY.md` eviction: DONE

Tool: [`util/ad-hoc/2026-08-19_memory_index_evict.py`](../util/ad-hoc/2026-08-19_memory_index_evict.py)
(explicit reviewed keep/evict lists; SHA-256 guard refuses to write if the file
changed underneath — not theoretical, see below).

| | Before | After |
|---|---:|---:|
| Lines | 140 | **123** |
| Bytes | 19,212 | **16,933** |
| % of the 25,000 cap | 77% | **68%** |
| Headroom | 5,788 B | **8,067 B** |
| Days to silent truncation @1.06/day | ~23 | **~32** |

All 155 topic files remain on disk; eviction demotes a row from resident to
on-demand, it does not delete. Spot-verified two evicted topics.

**The plan's estimate was optimistic — corrected.** §4 P0 claimed eviction
"recovers 90–148% of the 4,612-byte headroom". That came from marker-regex byte
counts, which include rows carrying **live** state. Judgement-based eviction of
the 17 genuinely-closed rows frees **2,374 bytes** — worth roughly **+9 days**,
not the projected ~35. Five rows matching a closure marker were deliberately
**kept** and are recorded in the tool.

Compression cannot close the gap: the longest rows cluster at 173–215 chars
against a 146.7 mean, so there is no outlier to trim. **`MEMORY.md` therefore
needs recurring curation, not a one-time pass** — which promotes D's forward-only
per-entry cap from optional to part of P0.

### A new rule, learned the hard way: status may not be demoted

While P0 ran, a **concurrent session** compressed the
`project_cascor_recurrence_cli_experimentation_plan.md` index row from ~900 chars
to ~150 — dropping an **open** `BLOCKER cascor#532`, the residual 1.17× wall gap,
the handoff pointer, three named traps, and the N≥20 method rule. Confirmed from
the pre-eviction backup: the loss predated this work.

The detail survives in the 89,048-byte topic file, so nothing was destroyed. But
the resident row was left reading *"all waves CLOSED"* while a blocker is open —
**worse than omission**, because nothing would prompt a reader to look further. A
95-byte status marker was restored, keeping the compression.

> **Rule for C's whole thesis, not just `MEMORY.md`: detail may be demoted to the
> corpus; STATUS may not.** An index row that misreports open/closed is a trap,
> not a pointer. Any relocation must leave the resident line carrying an accurate
> open/closed signal.

### P1 — the worktree ancestor canary: RESOLVED, and it changes the picture

Probe: [`util/ad-hoc/2026-08-19_build_ancestor_canary_probe.bash`](../util/ad-hoc/2026-08-19_build_ancestor_canary_probe.bash).
Positive control passed; the decisive probe returned **both** canaries.

**H-a (content dedup) is CONFIRMED, H-b refuted.** When the ancestor and worktree
`AGENTS.md` differ, **both load**. Full evidence:
[mechanism facts §8c-RESOLVED](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md).

**And it is not merely a migration hazard — it is the current state.** Of the 23
live worktrees, **11 distinct `AGENTS.md` contents exist and only 1 matches the
main checkout.** So **22 of 23 worktrees already load two full copies**: a session
in `cached-roaming-hamster` carries **344,450 chars ≈ 43% of a 200k window**,
against 204,889 (~26%) for the deduped case.

**The measured problem is roughly twice the baseline for almost every session.**

This adds a phase, and it is the cheapest win in the entire plan:

### P0b — worktree hygiene *(new; no authoring cost)*

Prune merged worktrees and rebase the rest so their `AGENTS.md` converges with
the main checkout. Every stale worktree is a permanent second copy of the file in
every session it hosts; converging one recovers **~170K chars per session** with
no content edit at all. It compounds with P3 rather than competing — after the
cut, a divergent worktree costs 2 × 32K instead of 2 × 173K.

Ordering consequence for **P3**: a trimmed worktree against an untrimmed main
checkout is the *worst* configuration (32K + 173K ≈ 205K — trimming would make
context go **up**). The cut must land on `main` with the primary checkout pulled
before worktrees carry the trimmed file.

---

## 4b. Execution log — P0b, P3 and P4 (2026-08-19 / 20): COMPLETE

### P3 — the cut: DONE, in four increments

| Increment | Section | Result |
|-----------|---------|--------|
| P3.1 | `### Tests` | −34,999 |
| P3.2 | `### Utilities` | −57,554 |
| P3.3 | `## Repository Structure` (partial — gate-minimal tree stays) | −18,764 |
| P3.4 | `## CI/CD Pipelines` | −15,861 |

**`AGENTS.md` 170,137 → 45,084 characters (−73.5%)**, ceiling ratcheted at each step.

Relocation was performed **by script, byte-for-byte**, so G3 passes *by
construction* rather than by the author's judgement — the failure this effort
exists to prevent is a well-meaning author keeping the identifiers and dropping the
prose.

**G3 caught two real losses that human judgement had approved.** Repairing a
concurrent session's accidental revert, it stopped four lines of that session's new
`safe_merge` documentation being destroyed. In P3.4 it refused a deletion of prose
that a table "obviously" superseded — the table lacked four specifics.

**The gates are complementary, not redundant.** G3 skips headings; the docs screen
is blind to prose-dropped-but-identifiers-kept. P3.4 needed both.

### P4 — the budget gate is BLOCKING and REQUIRED: DONE

`--advisory` removed, and `Memory Budget` added as a required context in the
`juniper-ml-rules` ruleset (15 → 16). Negative controls were run **before**
promoting — clean tree exit 0, +500 chars exit 1, waiver exit 0 — because a
blocking gate that cannot fail is worse than none.

**G3 deliberately stays advisory**: it has a documented false-positive class
(line-granular redistribution) and blocking on it would punish correct relocations.

### P0b — worktree hygiene: DONE, and it validated its own extra check

7 of 8 candidates removed; 17 worktrees remain, 2 now matching main.

**The liveness probe justified itself on first use.** `piped-drifting-dragon`
passed *every* gate `scripts/cleanup_session_worktrees.py` has — merged, clean,
unlocked, not the current cwd — while a live session held it, MCP servers rooted
inside. It was skipped. See
[`docs/REFERENCE.md` § Worktree Divergence Is a Memory Cost](../docs/REFERENCE.md#worktree-divergence-is-a-memory-cost).

Re-running the dry run first also mattered: state had moved from 23 worktrees /
7 candidates to 24 / 8 in the intervening hours.

### Combined effect, measured

| Session | Before | After |
|---------|-------:|------:|
| Divergent worktree | 344,450 | **~213,400** |
| Matching worktree (deduped) | 204,889 | **~110,900** |
| % of a 200k window (deduped) | ~26% | **~14%** |

P3 and P0b **compound**: the ancestor every session loads is now 45K rather than
173K, so even an un-converged worktree pays a far smaller duplicate.

### What remains

The 32,443 target is not reached (45,084). The remainder is many small sections
rather than one block, so the per-PR return has fallen sharply. The rate axis —
which is what actually prevents regression — is now in place and enforced, and
that was always the load-bearing half.

---

## 5. Owner decisions

| # | Decision                                | Recommendation                                                                                              |
|---|-----------------------------------------|-------------------------------------------------------------------------------------------------------------|
| 1 | Adopt C+D, reject B, reject A's thesis? | **Yes** — two independent synthesists converged; no dissenting analysis                                     |
| 2 | Target ceiling for `AGENTS.md`          | **32,443 chars**, ratcheting down; not the 200-line guideline, which is unreachable here without real loss  |
| 3 | Ratchet before the cut (C1)?            | **Yes** — otherwise the ceiling locks in ~43,000 chars of drift                                             |
| 4 | `MEMORY.md` forward-only cap value      | **120 bytes** on new entries; no rewriting of existing rows                                                 |
| 5 | Run the P1 canary before P3?            | **Yes** — it is 15 minutes and it determines migration ordering                                             |
| 6 | Waiver: loan or pass?                   | **Loan**, tracked centrally — the 23-worktree finding means implicit "next author" accounting will not work |
| 7 | Keep A's skills as a later probe?       | **Optional, deferred** — revisit only if the P3 soak shows a real pointer-follow problem                    |
| 8 | Address the parent `Juniper/AGENTS.md`? | **Yes, separately** — 11,016 additive bytes × 9 repos with no VCS, no CI, no gate                           |
| 9 | Fix the worktree settings asymmetry?    | **Yes, separately** — worktree sessions run without the local settings main-checkout sessions get           |

---

## 6. Falsifying the bet

The pointer-follow rate is the one load-bearing quantity nobody can measure in
advance. The soak: **N ≥ 20 sessions** after P3, tracking whether agents retrieve
relocated facts when relevant.

Escalation ladder, fixed in advance so the result cannot be rationalised:

1. Miss traced to discoverability → add an index row.
2. Miss traced to a *hazard* → promote to a CI gate or hook.
3. Systematic misses in one area → a path-scoped rule for that area.

**Never re-inline.** Re-inlining is how the file got here.

---

## 7. Residual risk after full execution

1. **The pointer-follow rate remains unmeasured until the soak.** This is the
   central bet.
2. **The docs screen still cannot see the pointer-shaped deletion**
   (`added == 0` required for FAIL). G3 is the only real control; if G3 is weak,
   there is none.
3. **The rate is bent, not reversed.** D alone still projects ~290 KB by
   February; with C's cut the level resets, but growth resumes.
4. **The parent `Juniper/AGENTS.md` is untouched** — ungoverned, unversioned,
   additive to all nine repos.
5. **`.claude/` destinations remain outside the content-loss screen** should any
   future work put content there.
6. **Compaction still drops path-scoped mechanisms** — relevant if the ladder
   ever reaches step 3.
7. **23 concurrent worktrees** make any central ledger (the waiver loan) a
   coordination problem that this plan specifies but does not solve.

---

## 8. Out of scope — file separately

Found during this work; unrelated to memory, and both are live:

1. **`tests/test_assert_release_tag.py` runs in zero workflows** — the only 1 of
   88 test files absent from `ci.yml`. It guards the `tr -d -- '-_'` bug that
   once made the publish-path version assertion pass **vacuously**. The test
   written to catch a vacuous pass is itself never executed.
2. **`AGENTS.md:485` documents `--ref-type` / `--ref-name`**;
   `util/assert_release_tag.bash:64` parses only `--ref`, and its header at
   `:38-44` explains why the two-flag form was *deliberately rejected* — "an
   assumption that is wrong here does not fail safe, it fails EVERY publish."
   An agent following the documentation gets `unknown argument` → exit 2, on all
   seven publishers.

These two are the duplication thesis proving itself: the drifted copy is the
always-loaded one, so an agent trusts the wrong interface for a publish-path
guard.
