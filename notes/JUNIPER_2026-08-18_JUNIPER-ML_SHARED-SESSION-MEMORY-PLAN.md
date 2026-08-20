# Shared Session Memory — Vetted Plan

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

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

canopy (94,373) and cascor (70,118) are on the same trajectory; nine repos share
the pattern. Port the gate first (it is portable in this repo's established
self-locating style), then the cut, repo by repo.

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
