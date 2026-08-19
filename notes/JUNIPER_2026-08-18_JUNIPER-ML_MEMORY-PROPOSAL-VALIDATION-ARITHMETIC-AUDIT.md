# Memory Proposal Validation — Arithmetic and Mechanical-Feasibility Audit

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose and standing

This is **validator 2 of 3** for the 2026-08-18 shared-session-memory design effort. Validator 1
audits citations; validator 3 attacks risk. **This document audits arithmetic and mechanical
feasibility only**: whether every headline number recomputes from its stated inputs, whether the
claimed savings are *mechanically* real under the loading semantics in the fact base, and whether
each migration phase can actually pass this repo's gates as written.

Under audit:

- [Proposal A — Progressive Disclosure via Skills](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md)
- [Proposal B — Path-Scoped Locality](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md)
- [Proposal C — Deduplication and Pruning](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md)
- [Proposal D — Governance and Enforcement](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md)

Against the fact base:

- [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) (**BASE**)
- [Memory mechanism facts](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) (**MECH**)

All measurements taken 2026-08-18 in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`,
`main` = `e209b74`, clean tree. Every number below was re-derived independently from the artifacts —
none was copied from a proposal and checked for plausibility. Reproduction commands are in
[Appendix A](#appendix-a--reproduction-commands).

**Nothing in this repository was modified apart from this file.**

---

## 0. Method, units, and what each verdict means

### 0.1 Verdict vocabulary

| Verdict | Meaning |
|---------|---------|
| **CRITICAL** | The claimed saving is not mechanically real, or the arithmetic is wrong in a way that changes what the owner should do. |
| **MAJOR** | A materially wrong number, or a phase that cannot ship as written. |
| **MINOR** | An error too small to change a decision, but real. |
| **CONFIRMED** | I recomputed it independently and it is correct. Reported because a validation that only reports faults is not a validation. |

"Could not verify" is tracked separately in [§11](#11-what-i-could-not-verify) and never presented as a pass.

### 0.2 The unit question, settled once

`wc` on this host reports, in GNU's fixed column order (lines, chars, bytes):

```text
$ wc -l -c -m AGENTS.md
  1115 168317 170137 AGENTS.md
```

Independently, via Python:

```text
bytes           : 170137
unicode codepts : 168317
JS content.length (UTF-16 units): 168317
non-ascii chars : 981   astral: 0
```

So: **168,317 characters, 170,137 bytes.** There are no astral-plane characters, so the JavaScript
`content.length` the CLI's own size check reads (MECH §1) is exactly 168,317.

This matters more than it looks, because **BASE labels characters as bytes in four places**
(§1, §3, §5, §8). BASE §3's "99,304 bytes / `## Key Files`" is 99,304 *characters*; the same line
range is 99,627 bytes. Proposals C and A both caught this and navigated it correctly; D caught the
file-level distinction but misdiagnosed the section-level one (see [AV-D-M1](#av-d-m1-minor--the-61-convention-note-misdiagnoses-its-own-gap-with-base)).

**This audit uses characters throughout**, because that is what the shipped check measures. Where a
proposal's figure is byte-based I say so. The two never differ by more than 1.1%, and no verdict here
turns on the difference — but a comparison table that silently mixes them is exactly the "quiet
wrongness" D's own §D1 warns about.

### 0.3 The eager baseline, measured

| Component | Chars | Bytes | Eager? |
|-----------|------:|------:|--------|
| `~/.claude/CLAUDE.md` | 3,341 | 3,349 | yes |
| `Juniper/CLAUDE.md` → `AGENTS.md` | 10,818 | 11,016 | yes (additive, MECH §7) |
| `juniper-ml/CLAUDE.md` → `AGENTS.md` | 168,317 | 170,137 | yes |
| **Eager subtotal `E₀`** | **182,476** | **184,502** | |
| Skill listing, 3 existing skills | 1,364 | — | yes (resident) |
| `MEMORY.md` index | 20,049 | 20,388 | yes (separate subsystem) |
| **Total always-on** | **203,889** | — | |

BASE §1's 204,890 is the all-byte version and omits the skill listing. At 4 chars/token that is
**50,631 tokens = 25.3% of a 200k window** before the first prompt — BASE's 25.6% recomputed on the
character basis.

---

## 1. The comparative savings table — recomputed from scratch

**This is the artifact the decision should rest on.** Every cell was recomputed by me from the
proposals' own stated inputs; where my figure differs from the proposal's, both are shown.

All figures are **characters**. "Eager" = injected at session start. `MEMORY.md` (20,049 chars) is
excluded from the eager columns because **no proposal changes it**, and is added back only in the
final `%` column so that column is comparable across all four.

| | **A** Skills | **B** Locality | **C** Prune | **D** Governance |
|---|---:|---:|---:|---:|
| Eager **before** | 182,476 | 182,476 | 182,476 | 182,476 |
| Eager **after** | **34,586** | **27,995** | **30,459** | **182,476** (today) |
| Eager Δ (my figure) | **−81.0%** | **−84.7%** | **−83.3%** | **0.0%** |
| Eager Δ (proposal's own headline) | −87.9% | −84.6% | −90.3% / −83% | n/a — D claims none |
| Lazy pool created | 141,439 | 152,900 | **0** (leaves the memory system) | 0 |
| **Best-case session** | 34,586 (−81.0%) | 27,995 (−84.7%) | 30,459 (−83.3%) | 182,476 (0%) |
| Modal session | 43,768–52,950 (−76% to −71%) | 55,394 (−69.7%) | 30,459 (−83.3%) | 182,476 (0%) |
| **Worst-case session** | 176,025 | 180,895 | **30,459** | 182,476 |
| Worst-case Δ | **−3.5%** | **−0.9%** | **−83.3%** | 0.0% |
| Expected value | not modelled | 59,687 (−67.3%) | 30,459 (−83.3%) | n/a |
| **% of 200k window, incl. `MEMORY.md`** | **6.8%** | **6.0%** | **6.3%** | **25.3%** |
| Confidence in my recomputation | High | High | High | High |
| Confidence the *saving is delivered* | **Medium** | **Medium** | **High** | High (of a zero saving) |

Supplementary rows:

| Variant | Eager after | Eager Δ | % of 200k incl. `MEMORY.md` | Note |
|---|---:|---:|---:|---|
| C + `claudeMdExcludes` on the parent | 19,641 | −89.2% | 5.0% | C marks it **unbanked**; the predicate `Rzr` is unverified (MECH §8.3) |
| D at its terminal allocation | 43,838 | −76.0% | 8.0% | **inert without a companion proposal** (D §10) |

### 1.1 Four readings a decision-maker should take from that table

1. **The published headlines are not comparable, and that materially misleads.** A quotes −87.9%
   against `AGENTS.md` alone; B quotes −84.6% against `AGENTS.md` plus the two ancestor files; C
   quotes both −90.3% and −83% in different sections. Normalized to one denominator the eager
   ordering is **B (−84.7%) > C (−83.3%) > A (−81.0%)** — a **3.7-point spread**, not the
   6-point spread the headlines suggest, and it reverses the impression that A's −87.9% beats B's
   −84.6%. See [AV-X-1](#av-x-1-critical--the-published-headline-percentages-are-not-comparable-and-normalizing-them-changes-the-apparent-ranking).

2. **Measured as a share of the context window, the three reorganisation proposals are effectively
   tied**: 6.0%, 6.3%, 6.8%. The gap between the best and worst of them is **0.8 percentage points
   of a 200k window (~1,600 tokens)**. The eager column should therefore *not* be the deciding input.

3. **The worst-case column is where they actually differ, and the difference is enormous.** C's
   saving is unconditional — 83.3% in every session, always. A's and B's collapse to −3.5% and
   −0.9% for a session that touches everything. That is the real axis of choice, and it is a
   choice about *variance*, not about *level*.

4. **The floor nobody moves is `MEMORY.md`.** 20,049 chars survive every proposal. It is 33% of B's
   post-migration always-on total and it is the one file that is actively losing data
   ([§3](#3-the-memorymd-headroom-adjudication)).

### 1.2 Why my A and C figures differ from theirs

| Proposal | Their figure | Mine | Gap explained |
|---|---|---|---|
| A | −87.9% | −81.0% | A's denominator is `AGENTS.md` alone (168,317). The 14,159 chars of ancestor files are eager before *and* after, so including them (as B and C's §12.4 do) lowers the percentage. A's arithmetic is right; its basis is narrower. |
| B | −84.6% | −84.7% | B's eager subtotal 182,682 mixes byte ancestors (14,365) with a character repo file. All-character is 182,476. 0.1-point effect. |
| C | −90.3% / −83% | −83.3% | −90.3% is `AGENTS.md`-only; −83% is C §12.4's ancestors-included figure and agrees with mine to 0.3 points. |
| D | 0% level | 0% | Agreed. D §9.1 states it outright: "It does not make `AGENTS.md` smaller." |

---

## 2. Mechanism verdict — are the savings mechanically real?

This was the crux of the mandate. The answer is **yes for all four**, and that is worth stating first
because the two fatal error classes MECH warns about are both absent.

### AV-X-C1 (CONFIRMED) — no proposal counts a saving from `@`-imports

MECH §3 is unambiguous: imports are eager and save zero. A design resting on them is void.

```text
$ grep -c "@path\|@-import\|@import" notes/…PROPOSAL-{A,B,C,D}*.md
A: 0    B: 1    C: 0    D: 1
```

The two hits are both explicit *rejections*:

- `…PROPOSAL-D…:112` — "**`@path` imports.** MECH §3 is unambiguous: imports load at launch and save zero tokens."
- B's §2.1 fact M4 — "`@path` imports are expanded at launch and save zero context. Any design resting on them is void."

A and C never invoke the mechanism at all. **Verified pass, all four.**

### AV-X-C2 (CONFIRMED) — no proposal counts a saving from splitting into ancestor-or-root files

MECH §1 consequence 1: the size check is per-file, so splitting a file into sub-40K files silences
the warning and saves nothing.

- **A** relocates into `.claude/skills/*/SKILL.md` — not memory files at all; bodies load only on
  invocation (MECH §4a, T1). Real.
- **B** relocates into *subdirectory* `CLAUDE.md` (lazy per MECH §4c) and `.claude/rules/` with
  `paths:` (lazy, code-proven in MECH §8b). Real. B explicitly **declines** `claudeMdExcludes` on the
  ancestor (§4.4 D-1), so it banks no ancestor saving.
- **C** deletes, or relocates into `docs/REFERENCE.md` and module docstrings — outside the memory
  system entirely. This is the *most* unambiguously real of the four: the bytes are not deferred,
  they are gone from the load path.
- **D** relocates nothing and banks nothing.

**Verified pass, all four.**

### AV-X-C3 (CONFIRMED) — A's crossover is computed correctly and is basis-invariant

A §8 defines crossover as `Σ_invoked bodies > B − R − L`:

```text
B − R − L = 168,317 − 15,157 − 5,270 = 147,890 chars
average reference body = 101,000 / 11 = 9,182 chars
crossover N* = 147,890 / 9,182 = 16.106  ->  "16.1"           CORRECT
```

Two checks A does not show, both of which it survives:

- **Basis invariance.** On my ancestors-included baseline the headroom is
  `182,476 − 34,586 = 147,890` — *identical*, because the ancestors are constant on both sides. The
  crossover is not an artefact of A's narrower denominator.
- **The average is the reference-skill average, but the shipped inventory is 14.** Using the true
  14-skill average (`130,650 / 14 = 9,332`), `N* = 147,890 / 9,332 = 15.85` — still above 14. The
  conclusion holds.

Every row of A's §8 table recomputes exactly:

| Scenario | A's chars | Mine | A's Δ | Mine |
|---|---:|---:|---:|---:|
| Nothing invoked | 20,427 | 20,427 | −87.9% | −87.86% |
| 1 average skill | 29,609 | 29,609 | −82.4% | −82.41% |
| 3 skills | 47,973 | 47,973 | −71.5% | −71.50% |
| All 11 bodies | 121,427 | 121,427 | −27.9% | −27.86% |
| All 14 + sub-files | 162,077 | 162,077 | −3.7% | −3.71% |

**Is the average-invocation assumption defensible?** The *count* assumption is not the load-bearing
one — see [AV-A-1](#av-a-1-major--the-cannot-be-worse-than-the-monolith-guarantee-is-conditional-on-an-unmeasured-compression-estimate-and-is-stated-as-unconditional). The corpus-size assumption is.

### AV-X-C4 (CONFIRMED) — B's saving holds at both launch points, with one exception

MECH §4c makes descendants lazy and ancestors eager. Sessions here launch from two places:

```text
$ pwd
/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus
$ ls /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees | wc -l
23
```

- **From the repo root** `juniper-ml/`: `util/`, `tests/`, `.github/`, `notes/`, `docs/`,
  `scripts/`, `prompts/`, and the six `juniper-*/` package dirs are all descendants → lazy. ✔
- **From a worktree** `juniper-ml/.claude/worktrees/<name>/`: a git worktree is a complete checkout,
  so `<worktree>/util/`, `<worktree>/tests/` … are descendants of *that* launch dir → lazy. ✔
  `.claude/rules/` is path-matched, not ancestry-based, so it is unaffected either way. ✔

**The exception B does not enumerate.** B places a `CLAUDE.md` at `.claude/` (§4.2.2, 1,302 chars).
From a worktree launch directory, `juniper-ml/.claude/` **is an ancestor directory**:

```text
ancestors of  …/juniper-ml/.claude/worktrees/swirling-kindling-octopus
  = …/juniper-ml/.claude/worktrees/   ->  …/juniper-ml/.claude/   ->  …/juniper-ml/  -> …
```

Under MECH §8c hypothesis **H-a** (ancestor walked, identical content deduped), the main checkout's
`.claude/CLAUDE.md` would load **eagerly** for every worktree session, and it cannot dedup against the
worktree's own copy because that copy is a *descendant* and therefore not loaded at launch. Magnitude:
1,302 chars, 0.7% of the eager baseline. Graded [AV-B-M6](#av-b-m6-minor--claudeclaudemd-is-on-the-worktree-ancestor-path) — structurally notable,
numerically negligible, and settled by the same two-minute probe MECH §8c already specifies.

---

## 3. The `MEMORY.md` headroom adjudication

The four proposals give three different answers. I re-derived it from the file.

### 3.1 The measurement

```text
$ wc -l -c -m ~/.claude/projects/-home-…-juniper-ml/memory/MEMORY.md
  139 20049 20388
```

139 lines / 20,049 chars / **20,388 bytes**. Every one of the 139 lines is a `- ` index entry; there
is no header, no frontmatter, no HTML comment. Every entry resolves to a real topic file (139/139).

MECH §8b establishes the cap from the shipped constant: `NOr` caps at `Tte=200` lines / **`qpe=25000`
bytes** — the earlier 25,600 estimate is superseded, and the cap is stated in **bytes**.

```text
headroom = 25,000 − 20,388 = 4,612 bytes
20 oldest entries: 2,688 B  ->  134.40 B/entry
20 newest entries: 4,695 B  ->  234.75 B/entry
all 139 entries : 20,388 B  ->  146.68 B/entry
```

### 3.2 Four independent estimators

| # | Basis | Entries remaining | Binds at line | Days @ 1.06 entries/day |
|---|-------|------------------:|--------------:|------------------------:|
| 1 | Blended 146.68 B/entry | **31.4** | 170 | **29.7** |
| 2 | Lifetime byte rate, measured directly (20,388 B / 131.1 d = 155.5 B/day) | — | — | **29.7** |
| 3 | **Recent 234.75 B/entry** | **19.6** | 159 | **18.5** |
| 4 | Recent byte rate, measured directly (last 20 entries = 4,695 B over a 26.6-day topic-mtime window = 176.5 B/day) | — | — | **26.1** |

Estimator 2 is estimator 1 restated, which is a useful cross-check: they must and do agree.
The entry-rate input is confirmed independently:

```text
all-entry topic-mtime span: 131.1 days ; entries/day = 1.06
```

### 3.3 Adjudication

**The defensible figure is ~20 entries at the recent rate, ~31 at the blended rate; the honest
horizon is ≈19–30 days, and the number to plan against is ≈19.** The orchestrator's re-derivation is
**CONFIRMED to the unit** on every input and every output.

Three reasons the recent rate is the right planning basis, not the blended one:

1. **Entry size is rising monotonically** — 134.4 → 234.8 B, +75%. A blended average of a rising
   series is a lower bound on the next value by construction.
2. **Estimator 4 is a floor, not a centre.** It counts only bytes arriving as *new* entries. Entries
   are also edited in place and grow: topic files behind the twenty **oldest** index entries have
   mtimes as recent as **2026-08-15**. That growth is invisible to every estimator here and can only
   push the horizon earlier.
3. **The failure is silent, irreversible, and newest-first** (MECH §2a). When the cost of being late
   is unbounded and the cost of being early is one curation pass, the conservative estimator is the
   correct one.

Line axis: at the recent rate the byte cap binds at line **159**, at the blended rate line **170** —
both well below 200. **Nobody should plan against the 61-line nominal headroom.** All four proposals
say this; all four are right about it.

### AV-M-1 (CRITICAL) — A and D overstate the horizon by ~1.8×, and A frames it as deferrable

| Proposal | Cap used | Rate used | Published answer | Correct answer |
|---|---|---|---|---|
| A §17 | ~25,600 (superseded) | blended 146.7 | headroom "~5,212", "**roughly 35 more entries**" | headroom 4,612; **~20** entries |
| B §11 | 25,600 (superseded) | none | "≈80% consumed, ~5,200 bytes of headroom" | 82%; 4,612 bytes |
| C §16 | **25,000** ✔ | blended 147 | "**about 31 more entries**" | 31 on that basis ✔; ~20 at the recent rate |
| D §7.2 | ~25,600 (superseded) | blended 146.7 | "**≈35 entries / ≈33 days**"; and, flagged, "≈30 days on the stricter 25,000 reading" | ~20 entries / **≈19 days** |

Evidence for the correct cap — MECH §8b, quoting the shipped binary:

> `NOr` caps at `Tte=200` lines / `qpe=25000` bytes. … **This confirms §2 from the implementation
> side**, and corrects the byte figure: the cap is **25,000 bytes**, not 25,600.

**Why this is CRITICAL rather than MAJOR.** It is the one arithmetic error in the whole set whose
correction changes *what must be done first*. A §17 closes with:

> Deferring it is a decision to accept silent memory loss in roughly 35 entries' time.

At ~20 entries and ≈19 days, "roughly 35 entries' time" is not a deferral window, it is
approximately September 6th. D is materially better here — D §12.2 and OQ-2 explicitly flag the
25,000-vs-25,600 question as "the single highest-consequence unverified fact in the document" and
publish the ≈30-day alternative — but D's *headline* is still 33 days, and D Phase 4 is conditioned
on "if the ~33-day truncation estimate holds". It does not.

**Recommended fix (applies to the final plan, not to any proposal):** state the horizon as
**≈19–30 days, plan against 19**, cite `qpe=25000`, and move `MEMORY.md` curation ahead of every
`AGENTS.md` phase in all four migration paths. C §16's per-entry cap and D's `--memory-index` checker
are the two concrete mechanisms already designed; neither depends on which `AGENTS.md` proposal wins.

### AV-M-2 (MINOR) — the per-entry-cap savings figures

| Claim | Recomputed |
|---|---|
| D OD-8: a 120-byte cap "frees 3,711 bytes ≈ 31 entries" | frees **3,873** bytes; `3,711/120 = 30.9` so the "≈31 entries" is self-consistent as *marginal* entries at the capped size, though post-cap total headroom is `25,000 − 16,515 = 8,485` B ≈ 70 entries |
| C §16: an ~180-char cap "would recover ~1,500 bytes" | recovers **1,351** bytes at a 180-**byte** cap (~10% optimistic) |

Distribution for reference: mean 146.7 B, median 134 B, p90 191 B, max **800 B** — one entry consumes
5.5 lines' worth of budget, which is the observation both C and D build on and it is correct.

---

## 4. Findings — Proposal A (Skills)

### AV-A-C1 (CONFIRMED) — the §7.1 section table is exact

I measured every H2 section independently (heading line through the line before the next H2). **Every
character figure in A's §7.1 matches mine exactly**, and the table sums to the file:

| A §7.1 | My measurement (chars) |
|---|---|
| header 331 · What This Is 596 · Build 4,617 · Publishing 3,641 · Shared Obs 1,495 · Shared SvcCore 3,512 · Repo Structure 20,469 · Key Files 99,304 · CI/CD 16,101 · Pre-commit 2,085 · SOPS 492 · Ecosystem 2,315 · Conventions 2,484 · PR 2,842 · Worktree 4,159 · Handoff 3,874 | identical, all 16 |
| **Total 1,115 / 168,317** | **1,115 / 168,317** ✔ |

Also confirmed: `### Utilities` 54,510 chars, `### Tests` 34,579, `### CI/CD Workflows` 8,136 — BASE
§3's figures reproduce exactly on the character basis.

### AV-A-C2 (CONFIRMED) — the residual sums to exactly 200 lines / 15,157 chars

```text
lines: 13+3+18+9+26+18+12+9+10+8+28+13+17+16 = 200
chars: 331+400+1,150+950+1,000+1,700+1,000+650+492+700+2,484+1,250+1,450+1,600 = 15,157
```

The "200 lines exactly" is not rounded to the guideline — the components genuinely add to 200.

**Is 15,157 achievable given what A keeps?** Partly verifiable, partly not. Three of the fourteen rows
are *unchanged measured sections* (header 331, SOPS 492, Conventions 2,484 = 3,307 chars, 21.8% of
the budget) — those are facts. One row is verifiable against a gate: the 26-line/1,000-char
gate-minimal tree, checked at [AV-A-C6](#av-a-c6-confirmed--the-gate-minimal-tree-reading-is-correct-and-a-is-the-only-proposal-that-gets-it-right). The remaining ten rows are *compression
targets* averaging a 3.6× cut (11,850 chars from 42,853 of source). That is a plan, not a
measurement, and A says so. **Verdict: arithmetically consistent, feasibility unproven but not
implausible** — the largest single ask is `## Build & Package Commands` 4,617 → 1,150, of which
3,314 chars is the mechanically-removable "Run all tests" block.

### AV-A-C3 (CONFIRMED) — 20,427, −87.9%, and the listing budget

```text
15,157 (residual) + 5,270 (listing) = 20,427                                     ✔
(168,317 − 20,427) / 168,317 = 87.86%  ->  "−87.9%"                              ✔
listing 5,270 vs the 8,000-char budget = 66% used, 2,730 headroom (34%)          ✔
```

The 8,000-char budget is itself derived correctly from A's §3.3 binary read
(`200000 × 4 × 0.01 = 8,000`) and is consistent with MECH §4a's "1% of the context window".

**Does the listing cost match the budget A derived?** Yes, with a small under-count. I measured the
proposed description text directly:

| | A's figure | Mine |
|---|---:|---:|
| 11 new descriptions | 3,535 | 3,600 (backticks stripped) / 3,744 (raw, as a YAML `description:` would carry them) |
| 11 × (name + 4) | 319 | 298 (measured names average 23.1, not 25) |
| 3 existing skills' entries | 1,403 | 1,364 (`service-smoke` 459, `template-agent` 486, `ui-test-author` 419) |
| **Total** | **5,270** | **5,419** (raw-backtick basis) |

**+2.8%**, taking budget consumption from 66% to 68%. No description is near the 1,536-char per-entry
cap. **The conclusion survives comfortably.** Graded [AV-A-M4](#av-a-m4-minor--description-char-counts-under-count-by-1859) / [AV-A-M5](#av-a-m5-minor--the-three-existing-skills-description-lengths-are-each-13-chars-high).

### AV-A-C4 (CONFIRMED) — the §5 inventory and §13.3 ledger both reconcile

```text
§5 source bytes:  23,321+10,220+26,923+6,517+3,900+10,479+11,737+11,135+11,925+6,607+22,911 = 145,675  ✔
§5 body targets:  14,000+9,000+15,000+6,500+5,000+9,000+10,000+9,000+10,000+6,500+7,000     = 101,000  ✔
§13.3 ledger:     15,157 + 101,000 + 11,000 + 33,825 + 7,335                                 = 168,317  ✔
```

I spot-checked seven of the eleven source line-ranges literally. Aggregate: A claims 100,399 for those
seven, I measure 99,626 bytes — **−0.8%**. Individual rows vary from −748 to +1,016 because four of
the ranges carry prose exclusions ("less publish/release rows") I could not apply literally. One row
(`experiments`, `:517-596` + `:682-709`) matched **exactly** at 26,923 bytes. **Verdict: accurate at
aggregate granularity; individual rows carry ±8%.**

### AV-A-C5 (CONFIRMED) — the compaction arithmetic

```text
per-skill re-attach cap  5,000 tok = 20,000 chars ; largest planned body 15,000  -> 25% margin  ✔
lint ceiling 16,000 chars                                                        -> 20% margin  ✔
total re-attach cap     25,000 tok = 100,000 chars ; 11-body corpus 101,000      -> one dropped ✔
```

A's observation that a fully-invoked session loses exactly one body across a compaction boundary is
arithmetically right and is the sharpest thing in §9.

### AV-A-C6 (CONFIRMED) — the gate-minimal tree reading is correct, and A is the only proposal that gets it right

A §7.3 reads [`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) as
requiring four things, including — uniquely among the four proposals — the literal `agent_templates/`:

```python
# tests/test_agents_md_tree_drift.py:114-116
def test_prompts_uses_agent_templates_not_stale_templates(self) -> None:
    # G-3 rename: the tree must cite the real prompts/agent_templates/ dir.
    self.assertIn("agent_templates/", self.tree)
```

Verified against the live file: 18 tracked non-hidden top-level dirs
(`git ls-tree -d --name-only HEAD`), the fenced block spans `AGENTS.md:183-374` (192 lines /
20,431 chars), and `agent_templates/` occurs **5 times inside it, all as nested content**. A
top-level-only tree drops all five. A's "23-line minimum, budget 26" is therefore correct and its
1,000-char allocation is realistic. See [AV-F-1](#av-f-1-major--b-and-c-both-specify-a-tree-that-fails-test_agents_md_tree_driftpy) for the two proposals that miss this.

### AV-A-1 (MAJOR) — the "cannot be worse than the monolith" guarantee is conditional on an unmeasured compression estimate, and is stated as unconditional

A §8 states:

> **The design cannot be worse than the monolith**, because the entire corpus is smaller than the
> headroom. That is a structural property, not a hope.

It is a property of the *planned* corpus, not of the design. The break-even, which A does not
publish:

```text
headroom                       = 168,317 − 20,427            = 147,890
procedural bodies (unavoidable)= 29,439                       (29,650 bytes)
=> the 11 reference skills + sub-files must total           <= 118,451
from 145,675 chars of source, that is a required cut of      18.7%
A plans 145,675 -> 112,000, a cut of                         23.1%
margin                                                        4.4 percentage points
```

At **zero** compression the corpus is 175,114 and the worst case is **+14.9% worse than today** — a
scenario A does not table. A *does* table the half-compression case in §13.3 ("the corpus becomes
~129,000 … the worst case becomes a small loss"), which I recompute as **+6.4%**, so the concession
exists; it is the §8 sentence that overstates. A also names 33,825 as "the least certain number in
this document".

**Fix:** restate §8 as "cannot be worse than the monolith *provided the corpus cap holds*", and make
the corpus cap the *first* gate shipped (A's Phase 1 already does this — the sentence, not the plan,
is what needs correcting).

### AV-A-2 (MAJOR) — A's §17 `MEMORY.md` numbers are the worst of the four

Covered under [AV-M-1](#av-m-1-critical--a-and-d-overstate-the-horizon-by-18-and-a-frames-it-as-deferrable). A alone offers no corrected alternative reading, and A alone
frames the delay in entry-counts ("roughly 35 entries' time") rather than days, which obscures that
the horizon is under three weeks.

### AV-A-M1 (MINOR) — a byte figure inside a character table

A §8's worst-case rows use **29,650** for the three procedural skill bodies. That is the *byte* count;
the character count is **29,439** (`wc`: 422 lines / 29,439 chars / 29,650 bytes). A's §5 preamble
declares that source sizes are bytes and body targets are characters, so this is disclosed — but it
lands inside a table whose other terms are characters. Effect: 211 chars, 0.13% of the worst case.

### AV-A-M2 (MINOR) — §13.2's "7.0%"

```text
55,497 / 4 = 13,874 tokens ; 13,874 / 200,000 = 6.94%
```

Reported as 7.0%; should be 6.9%. (My normalized figure including `MEMORY.md` is 6.8%, because I use
character ancestors rather than byte ancestors.)

### AV-A-M3 (MINOR) — the §13.3 deletion split is internally off by ±150

`§5` implies deleted-as-duplicated `= 145,675 − 112,000 = 33,675` and deleted-as-derivable
`= 168,317 − 145,675 − 15,157 = 7,485`. §13.3 publishes 33,825 and 7,335. The two errors are equal and
opposite, so the ledger still sums to 168,317; only the split between the two buckets is wrong.

### AV-A-M4 (MINOR) — description char counts under-count by 1.8%–5.9%

Per-row deltas run +0 to +12 against the backtick-stripped text (`juniper-ml-repo-map` +12,
`juniper-ml-experiments` +11). Total 3,535 claimed vs 3,600 measured / 3,744 raw. Immaterial against
an 8,000-char budget.

### AV-A-M5 (MINOR) — the three existing skills' description lengths are each 13 chars high

A: `template-agent` 481 / `ui-test-author` 414 / `service-smoke` 455. Measured from the frontmatter:
468 / 401 / 442. A's total (1,403) counts names + 4 on top of its own three figures; my equivalent is
1,364.

### AV-A-M6 (MINOR) — the §7.1 Thread-Handoff line count

A: 74 lines; measured 75 (the file's final line has no trailing newline). A's stated total of 1,115 is
correct for the file, so the table is off by one line against its own total.

---

## 5. Findings — Proposal B (Path-Scoped Locality)

### AV-B-C1 (CONFIRMED) — the §4.3 root target sums exactly

```text
after chars: 925+1,050+120+620+160+170+2,290+1,150+420+560+491+330+2,000+1,150+900+1,500 = 13,836  ✔
after lines: 19+24+2+8+3+3+44+14+6+6+10+5+24+14+20+26                                    =    228  ✔
(168,317 − 13,836) / 168,317 = 91.78%  ->  "−92%"                                                  ✔
```

B's refusal to fudge 228 down to the 200-line guideline is, on the arithmetic, the correct call: the
rows that would have to go are the genre-A ones.

### AV-B-C2 (CONFIRMED) — the relocation accounting is a genuine relocation, and the "~4%" is right

```text
104,488 (rules) + 48,412 (dir files) + 13,836 (root) = 166,736                    ✔
168,317 − 166,736 = 1,581  ->  −0.94%  ->  "−0.9%"                                ✔
1,581 + 5,400 (new orientation prose) = 6,981  ->  6,981/168,317 = 4.15%  -> "4.1%" ✔
```

This is the single most honest number in any of the four documents: B states plainly that its content
reduction is 4%, and the arithmetic backs it.

### AV-B-C3 (CONFIRMED) — every scenario and both expected values reproduce to the unit

| Scenario | Lazy components | B's total | Mine | B's Δ | Mine |
|---|---|---:|---:|---:|---:|
| 1 | — | 28,201 | 28,201 | −84.6% | −84.56% |
| 2 | tests 13,789 + drift-checks 13,404 | 55,394 | 55,394 | −69.7% | −69.68% |
| 3 | + util 7,226 + experiments 26,460 | 89,080 | 89,080 | −51.2% | −51.24% |
| 4 | + .github 15,077 + release-train 24,740 | 128,897 | 128,897 | −29.4% | −29.44% |
| 5 | all 152,900 | 181,101 | 181,101 | −0.9% | −0.87% |

```text
EV(write)  = .32(28,201)+.41(55,394)+.18(89,080)+.08(128,897)+.01(181,101) = 59,893.0  exact  ✔
EV(pessim) = one bucket right                                              = 93,749.0  exact  ✔
```

**The bracket brackets correctly.** Worst case −0.9% (parity, never regression) and best case −84.6%
are both right, and both bound the five scenarios.

### AV-B-C4 (CONFIRMED) — the eager/lazy split is accounted separately and correctly

B's §5.2 is the only budget table in the four that labels each layer eager-or-lazy explicitly. Eager
subtotal 182,682 → 28,201; lazy pool 0 → 152,900. On my all-character basis, 182,476 → 27,995 and
152,900 lazy. **−84.7% eager**, agreeing with B to 0.1 points.

### AV-B-C5 (CONFIRMED) — the tree measurement and the §8c analysis

- Tree block: B says 195 lines / 20,443 chars; I measure the fenced *body* at 192 lines / 20,431 chars,
  which is 195 / 20,443 once the two fence lines are included. ✔
- B's §7.3 worktree analysis is correct on the mechanism, correctly identifies the H-a hazard, and
  correctly quantifies it: under H-a a Phase-1 worktree session carries `13,836 + 168,317 = 182,153`,
  **+8.2% worse than today**, transiently. B is the only proposal that finds this, and its
  merge-then-`pull --ff-only` sequencing is a real fix that the repo's own worktree-cleanup Phase 7
  already mandates.

### AV-B-1 (MAJOR) — `notes/` and `docs/` are classed as non-memory-bearing in §3.4 but are given a `CLAUDE.md` in §4.2.2

B §3.4's bucket 0 is "root / `notes/` / `docs/` only — 193 PRs, 32%", and §5.3 scenario 1 accordingly
records **lazy = 0**. But §4.2.2 places `notes/CLAUDE.md` (1,533 chars) and `docs/CLAUDE.md` (632).
Reading any file in either directory fires the corresponding file.

`notes/` is B's own **most-touched unit at 39% of PRs**, so this is not a corner case: it is the
largest scenario in the model, and its lazy load is understated by up to 2,165 chars.

Magnitude, recomputed: adding an expected `0.39 × 1,533 + 0.08 × 632 ≈ 649` chars to every scenario
moves the EV from 59,893 to ≈60,542 and the headline from −67.2% to **−66.9%**; scenario 1 moves from
−84.6% to as low as **−83.4%**. **The number barely moves; the table contradicts the design.** Graded
MAJOR because it is a table-vs-design inconsistency in the document's central model, not because the
arithmetic effect is large.

### AV-B-2 (MAJOR) — a top-level-only tree fails the tree-drift gate

See [AV-F-1](#av-f-1-major--b-and-c-both-specify-a-tree-that-fails-test_agents_md_tree_driftpy).

### AV-B-M1 (MINOR) — the §3.1 and §4.3 tables do not sum to their own stated totals

```text
§3.1 rows sum to 168,302 chars / 1,116 lines ; stated total 168,317 / 1,115
§4.3 "Today" column sums to 168,302          ; stated total 168,317
```

Fifteen of sixteen sections are exactly 1 char below my measurement — a section-boundary convention
(the separator line). The stated totals are right for the file; the rows are 15 chars short in
aggregate. 0.009%.

### AV-B-M2 (MINOR) — the eager subtotal mixes units

182,682 = 168,317 chars + 14,365 **bytes**. All-character is 182,476. B's §0.1 declares byte figures
will be labelled; §5.2's column header says "(chars)". 0.11% effect.

### AV-B-M3 (MINOR) — two counts about the test suite are off

| B's claim | Measured |
|---|---|
| "`ci.yml` runs roughly 100 modules" | **87** distinct `tests/test_*.py` |
| "`AGENTS.md:39-96` lists 57" | **54** distinct modules (58 lines, 54 `unittest` invocations) |
| (implied) modules on disk | **88** |

B's point — the block is stale — is correct; the magnitude is 54-of-88, not 57-of-~100.

### AV-B-M4 (MINOR) — the §1 genre table leaves 1,581 chars unaccounted

`104,488 + 48,412 + 13,836 = 166,736` against a 168,317-char file (shares 62/29/8 = 99%). The residue
is exactly B's own §5.1 net reduction, so it is coherent — but the table is labelled "Bytes" while its
shares are computed against a character denominator.

### AV-B-M5 (MINOR) — §11's `MEMORY.md` figures use the superseded cap

"≈80% consumed … ~5,200 bytes of headroom" — against `qpe=25000` it is **82%** and **4,612** bytes.
B publishes no horizon, so nothing downstream is affected. B's item 5 would build a checker against
"200/25,600"; that constant needs updating before it ships.

### AV-B-M6 (MINOR) — `.claude/CLAUDE.md` is on the worktree ancestor path

See [AV-X-C4](#av-x-c4-confirmed--bs-saving-holds-at-both-launch-points-with-one-exception). 1,302 chars, contingent on MECH §8c resolving to H-a.

### AV-B-M7 (MINOR) — §2.2 is superseded by MECH §4c-bis

B correctly reported that its brief attributed a compaction fact to MECH that MECH did not contain,
and MECH §4c-bis was added in response, crediting B. The fact is now established from T1: nested
`CLAUDE.md` and `paths:` rules are **lost after compaction until re-triggered**. B designed for that
branch, so nothing in B changes — but §2.2's "UNVERIFIED" label is now stale, and the guardrails B
called "merely redundant if it is retained" are now **load-bearing**.

---

## 6. Findings — Proposal C (Deduplication and Pruning)

### AV-C-C1 (CONFIRMED) — the 15,860 unique-content figure is arithmetically forced by the measured section size

The mandate asked whether relocating everything else is arithmetically consistent with BASE's measured
sections. It is, and tightly so:

```text
### Utilities (AGENTS.md:403-596)                  = 54,510 chars   [my measurement = BASE §3]
  covered by a docs/REFERENCE.md section           = 38,650
  six subjects with none  -> new REFERENCE sections= 11,443
  small subjects with none-> docstrings/existing   =  4,417
                                            SUM    = 54,510  ✔ exact
  genuinely unique = 11,443 + 4,417                = 15,860  ✔
```

`4,417` is not an independent estimate — it is `54,510 − 38,650 − 11,443`, i.e. it is *pinned* by the
measured section size. The only free parameters are the 38,650 coverage split and the 11,443/4,417
boundary, both of which C derives by hand-corrected subject matching. **This is the most tightly
constrained headline number in the four documents.**

### AV-C-C2 (CONFIRMED) — every table in §12 reconciles

```text
§12.1 "After"  : 700+900+550+200+200+1,800+1,400+900+500+300+500+1,900+800+700+650+2,000+2,300 = 16,300  ✔
§12.1 "Removed": rows 1-15 = 156,318 ; rows 16-17 add 4,300 ; net = 152,018                              ✔
                168,317 − 152,018 = 16,299  ("±1 rounding", as C states)                                 ✔
§12.2 row 7    : 38,650+11,443+4,417+34,579+8,136+2,065+14 = 99,304  ✔ exact to the section
§12.3 ledger   : 68,409+41,544+18,669+6,684+11,443+4,417+6,311+241 = 157,718 ; −1,400 −4,300 = 152,018   ✔
§12.4          : 3,349+11,016+16,300 = 30,665 -> −83% ; 3,349+16,300 = 19,649 -> −89%                    ✔
                 45,700 -> 7,700 tokens -> 23% -> 4% of a 200k window                                    ✔
```

Four separately-constructed tables all land on 152,018 / 16,300. That is a strong internal-consistency
signal.

### AV-C-C3 (CONFIRMED) — the growth series and the "undone in two months" arithmetic

C's month-boundary sizes reproduce from git exactly (`git rev-list -1 --first-parent --before=…`):
38,248 → 64,965 → 120,685 → 170,137, giving 891 / 1,797 / **2,909** B/day. And:

```text
(40,000  − 16,300) / 2,000 = 11.9 d   ; / 2,909 =  8.1 d   -> "12 / 8"    ✔
(100,000 − 16,300) / 2,000 = 41.9 d   ; / 2,909 = 28.8 d   -> "42 / 29"   ✔
(170,137 − 16,300) / 2,000 = 76.9 d   ; / 2,909 = 52.9 d   -> "77 / 53"   ✔
```

### AV-C-C4 (CONFIRMED) — C is the only proposal that gets BASE's unit labelling exactly right

C §1.1: "`wc` reports 1,115 lines / 168,317 characters / 170,137 bytes … the baseline document's
*headline* figure (170,137) is bytes; its *per-section* table (99,304 / 20,469 / 16,101 / 4,617) is
characters — I reproduced those four numbers exactly on a character basis." **All of that is
independently confirmed**, including the derived `168,317 / 40,000 = 4.21×` (versus 4.25× on bytes).

Also confirmed: `docs/REFERENCE.md` = 1,865 lines / 161,487 chars / 162,231 bytes, exactly as C states
(BASE §5's "162,231 chars" is again bytes).

### AV-C-1 (MAJOR) — C's core destroys eight live heading anchors, failing a **required** CI check

C §4.1's outline replaces `### Script placement (mandatory)` with a `## Standing Rules` section that
"holds … script placement, worktrees, handoff, notes naming, PR conventions summary", and renames
`## Worktree Procedures (Mandatory -- Task Isolation)` to `## Worktree Procedures`.

Both headings are anchor targets today:

```text
$ grep -rhno "AGENTS\.md#[a-zA-Z0-9_-]*" docs/ notes/ .github/ util/ | sed 's/^[0-9]*://' | sort | uniq -c
      5 AGENTS.md#script-placement-mandatory
      2 AGENTS.md#worktree-procedures-mandatory--task-isolation
      …
$ grep -c "](#script-placement-mandatory)" AGENTS.md
      1                      # AGENTS.md:500, an intra-file link
```

Six references to `#script-placement-mandatory` and two to
`#worktree-procedures-mandatory--task-isolation`. The validator resolves anchors, not just files
([`juniper-doc-tools/juniper_doc_tools/check_doc_links.py:293`](../juniper-doc-tools/juniper_doc_tools/check_doc_links.py)
— `if anchor and anchor not in headings:`), and `Documentation Links` is a **required** status check:

```text
$ gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
    --jq '.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context'
Documentation Links
…
Sequence Safety
```

**Fix:** keep both heading texts verbatim (they are 2 of the ~193 lines), or update all eight
referring links in the same PR. Cheap, but it is a hard CI failure as written.

### AV-C-2 (MAJOR) — C's 18-node tree fails the tree-drift gate

See [AV-F-1](#av-f-1-major--b-and-c-both-specify-a-tree-that-fails-test_agents_md_tree_driftpy). C §4.4 specifies "18 top-level directory nodes plus the handful of root
files an agent must know", with no nested node — which drops all five occurrences of
`agent_templates/` from the fenced block.

### AV-C-M1 (MINOR) — the §2.5 row list over-counts by 460 against its own subtotal

```text
512+501+494+480+465+385+325+447+802+466 = 4,877   ; stated subtotal 4,417
```

The **subtotal is the correct figure** (it is forced by `54,510 − 38,650 − 11,443`), so the ten
published rows, not the total, carry the error — consistent with §12.2 calling it "**nine** small
subjects" against §2.5's ten rows. The grand total 15,860 and everything downstream are unaffected.

### AV-C-M2 (MINOR) — "binds at roughly 175 lines" should be ~170

C §16 computes the binding line from the **character** mean (143) against the **byte** cap:
`25,000 / 143 = 174.8`. On its own stated 147 B/line it is `25,000 / 146.7 = 170.4`. My independent
figure is 170 (blended) or 159 (recent rate).

### AV-C-M3 (MINOR) — "55 of 88" is 54 of 88

`ci.yml`'s "87 of 88" is exact; the `AGENTS.md:39-96` block names **54**.

### AV-C-M4 (MINOR) — C Phase 5(a) would create a gitignored `settings.json`

```text
$ git check-ignore -v .claude/settings.json
.gitignore:177:.claude/*	.claude/settings.json
```

MECH §8b already flags that this repo has no active `.claude/settings.json`. Creating one for
`claudeMdExcludes` would work **on one host** and would not be shared, reviewed, or portable to the
other eight repos — which undercuts the "−89%" variant's standing as a fleet remedy. C already marks
that variant unbanked; this is a second, independent reason to keep it so. The same applies to A's
`skillListingBudgetFraction` mitigation and B's settings-based fallbacks.

### AV-C-M5 (MINOR) — unit mixing in §9.2

The milestone table divides character targets (16,300) by byte rates (2,000 / 2,909 B/day) against
byte milestones (170,137). ~1% effect; C's §1.1 makes the general disclosure but not here.

---

## 7. Findings — Proposal D (Governance and Enforcement)

### AV-D-C1 (CONFIRMED) — §6.1's "Now" column is byte-exact, all fifteen rows

D's per-section byte figures match my independent measurement **exactly, every row**, and sum to the
file:

```text
929+4,617+3,656+1,505+3,531+21,833+99,627+16,167+2,085+492+2,315+2,488+2,853+4,165+3,874 = 170,137  ✔
```

This is the only complete, exactly-summing byte partition of the file in any of the four documents.

### AV-D-C2 (CONFIRMED) — the trailing-30-day series reproduces, and D's self-reported median fix is correct

D flagged §7.2 as its likeliest error and separately reported correcting a median from 13,105 to
12,672. I recomputed the whole series from git:

| Window ending | D says | Mine | Δ |
|---|---:|---:|---:|
| 2026-03-31 | +1,607 | +1,607 | 0 |
| 2026-04-14 | +13,522 | +13,522 | 0 |
| 2026-04-28 | +13,538 | +13,538 | 0 |
| 2026-05-12 | +2,261 | +2,261 | 0 |
| 2026-05-26 | +14,580 | +14,580 | 0 |
| 2026-06-09 | +12,672 | +12,672 | 0 |
| 2026-06-23 | +2,553 | +2,596 | +43 |
| 2026-07-07 | +28,013 | +28,013 | 0 |
| 2026-07-21 | +38,781 | +38,781 | 0 |
| 2026-08-04 | +54,071 | +54,071 | 0 |
| **2026-08-18** | **+92,796** | **+92,507** | −289 |

**Nine of eleven windows reproduce exactly.** The pre-flood set sorts to
`1,607 / 2,261 / 2,596 / 12,672 / 13,522 / 13,538 / 14,580` → **median 12,672, max 14,580** — the
corrected median is right, and my 43-char difference in one window does not move it.

Derived claims all check out:

```text
92,796 / 1,607                     = 57.7×   -> "58× in five months"      ✔
92,796 / 170,137                   = 54.5%   -> "55% of the entire file"  ✔
(170,137 − 34,263) / (92,796/30)   = 43.9 d  -> "44 days"                 ✔  (43.6 d on my 92,507)
34,263 + 92,796                    = 127,059                              ✔
```

**The "likeliest error" D nominated (§7.2's headroom) is indeed wrong** — but for a different reason
than D expected. The arithmetic is internally sound on both readings D offers; what is wrong is the
input constant and the choice of rate. See [AV-M-1](#av-m-1-critical--a-and-d-overstate-the-horizon-by-18-and-a-frames-it-as-deferrable).

### AV-D-C3 (CONFIRMED) — the terminal allocation, the ceiling derivation, and the token effect

```text
terminal allocation: 900+1,400+900+300+300+1,800+6,000+1,800+1,200+492+1,100+1,800+1,800+1,200+1,400 = 22,392  ✔
reserve            : 30,000 − 22,392 = 7,608                                                                   ✔
Δ                  : 170,137 − 22,392 = 147,745                                                                ✔
200 lines × 152.6 B/line = 30,520   (170,137/1,115 = 152.59)                                                   ✔
BASE §8 residue on D's partition: 170,137 − 137,627 = 32,510                                                   ✔
tokens: 30,000 B ≈ 29,679 chars / 4.017 = 7,388 ; 168,317/4.017 = 41,901 ; Δ 34,513 = 17.3% of 200k             ✔
three big sections = 137,627 / 170,137 = 80.89%  -> "80.9%"                                                    ✔
August: 49,452 B / 190 net lines = 260.3 B/line                                                                ✔
```

### AV-D-C4 (CONFIRMED) — the projection, including the ~290 KB February figure

```text
linear @ 3,093 B/day:  +30d 262,927 · +60d 355,717 · +90d 448,507 · +120d 541,297 · +180d 726,877   ✔ all exact
D-alone ladder:        170,137 +60k +30k +15k +5k +5k +5k = 290,137                                 ✔ exact
"2.5×-4.7× below status quo":  726,877/290,137 = 2.505×  ;  1,361,096/290,137 = 4.691×              ✔
rate schedule: 92,796/5,000 = 18.6× ; 60,000/92,796 = 65% ; 30,000/12,672 = 2.37× ; 5,000/30 = 167 B/d ✔
```

**The ~290 KB by February figure is correct** given D's own ladder, and the ladder is correctly
applied (six 30-day steps at 60k/30k/15k/5k/5k/5k). Checked against the measured growth series, the
counterfactual it is compared against is also right: linear extrapolation of the measured
+92,507/30 days reaches 726,000–727,000 at +180 days.

### AV-D-C5 (CONFIRMED) — D's migration is the only one with no CI exposure

No D phase deletes content from `AGENTS.md`, `docs/**`, or `notes/**`; every artifact it adds is new.
The docs deletion screen and the doc-link validator are both clean by construction. D also correctly
identifies the required-context naming trap ("renaming the job at promotion breaks the required
context") — verified: the live ruleset requires the literal context `Sequence Safety`.

### AV-D-1 (MAJOR) — the `MEMORY.md` headline

Covered under [AV-M-1](#av-m-1-critical--a-and-d-overstate-the-horizon-by-18-and-a-frames-it-as-deferrable). D is the *best* of the four on process here (it flags the
constant as its highest-consequence unknown and publishes the ≈30-day alternative) and still lands on
a headline that is ~1.8× too long, because it also uses the blended rather than the recent rate.

### AV-D-M1 (MINOR) — the §6.1 convention note misdiagnoses its own gap with BASE

D writes:

> BASE §3 reports 99,304 / 20,469 / 16,101 … against my 99,627 / 21,833 / 16,167 … **The gap is where
> a section's trailing `---` rule is attributed**, not a disagreement about content.

It is not. Measuring the *identical* line ranges both ways:

| Section | chars | bytes |
|---|---:|---:|
| `## Key Files` | 99,304 | 99,627 |
| `## Repository Structure` | 20,469 | 21,833 |
| `## CI/CD Pipelines` | 16,101 | 16,167 |
| `## Build & Package Commands` | 4,617 | 4,617 |

**The gap is bytes-versus-characters.** It even explains the anomaly D notices and cannot account for
— Build & Package agrees exactly because it is pure ASCII, while Repository Structure diverges most
because the tree is full of multi-byte `├ └ │` glyphs. D's own Appendix A prints both totals, so the
distinction was in hand; the causal attribution is wrong. No number changes.

### AV-D-M2 (MINOR) — D's own gate unit contradicts its own budget table

D §D1 states the gate will measure "**characters** for the CLAUDE.md family", and warns that
conflating the two "is precisely the kind of quiet wrongness that makes a number un-trustworthy
later." §6.1's entire budget — including the terminal ceiling, literally named `max_bytes` — is then
denominated in **bytes**. A 30,000-**byte** target enforced as 30,000 **characters** is 30,327 bytes.
1.08%, and ironic.

### AV-D-M3 (MINOR) — the +30d cell of the doubling column

`170,137 × 2^(30/60) = 240,610`. D publishes "~219,000". The other four cells of that column are exact
(340,274 / ~480,000 / 680,548 / 1,361,096). The error runs *against* D's own argument — it makes the
status quo look less alarming — so it is conservative, but it is wrong.

### AV-D-M4 (MINOR) — the headline 30-day net

+92,796 recomputes to **+92,507** (0.31% high); the 2026-06-23 window to 2,596 vs 2,553. The 44-day
figure, the 55%-of-file figure and the 58× multiplier all survive unchanged.

### AV-D-M5 (MINOR) — OD-8's 3,711 bytes

A 120-byte per-entry cap frees **3,873** bytes, not 3,711 (4.4% low). The "≈31 entries" is
self-consistent as marginal entries at the capped size.

---

## 8. Cross-cutting findings

### AV-X-1 (CRITICAL) — the published headline percentages are not comparable, and normalizing them changes the apparent ranking

Three different denominators are in use:

| Proposal | Denominator | Headline |
|---|---|---|
| A | `AGENTS.md` alone, 168,317 | −87.9% |
| B | `AGENTS.md` + both ancestors, 182,682 | −84.6% |
| C | both, in different sections | −90.3% and −83% |
| D | n/a | none claimed |

Read as published, A (−87.9%) appears to beat B (−84.6%). On one denominator it does not:

| | A | B | C |
|---|---:|---:|---:|
| Eager Δ, `AGENTS.md`-only basis | −87.9% | **−91.8%** | −90.3% |
| Eager Δ, ancestors-included basis | −81.0% | **−84.7%** | −83.3% |

**B > C > A on both bases.** The published ordering inverts A and B purely through the choice of
denominator. And once the two unchangeable ancestor files (14,159 chars) and the unchangeable
`MEMORY.md` index (20,049 chars) are held in view, all three land within **0.8 percentage points of a
200k context window** of each other (6.0% / 6.3% / 6.8%).

**Consequence for the decision.** The eager column cannot separate these three proposals; it is
effectively a tie. What separates them is the **worst case** (C −83.3%, A −3.5%, B −0.9%), the
**variance** (C zero, A and B session-shaped), and the **compaction behaviour** (MECH §4c-bis: A's and
B's lazy content is lost at a compaction boundary; C's residual is re-injected from disk). The final
plan should be argued on those axes and should present one normalized table, not four headlines.

### AV-X-2 (MAJOR) — BASE's own §8 figure is unit-inconsistent, and proposals inherit it

> Removing the three largest sections … leaves **34,263 chars** (170,137 − 135,874).

`135,874 = 99,304 + 20,469 + 16,101`, which are **characters**; `170,137` is **bytes**. On a pure
character basis the residue is `168,317 − 135,874 = 32,443`; on a pure byte basis it is
`170,137 − 137,627 = 32,510`. **The 34,263 figure exists in neither unit** and is 5.6% high.

It propagates: D §6.1 adopts it as an alternative ceiling (OD-1 offers "30,000 / **34,263** / other")
and D §3.2 uses it as the base for the "back to today's size in 44 days" calculation. The 44-day
result is unaffected to the day (43.9 vs 44.5 on the corrected base), but a ceiling constant should
not be a unit error. **Recommend BASE §8 be corrected to 32,443 chars / 32,510 bytes and the label on
§1/§3/§5 changed from "Chars" to "Bytes".**

### AV-X-3 (MINOR) — the 4-chars-per-token divisor is unverified and the sensitivity is large

Every token and window-percentage figure in all four proposals uses 4 chars/token. MECH §8 ("Still not
verified") lists "Whether `eR()` returns 4 or 3 for the model actually in use". At **3**:

| | @4 chars/tok | @3 chars/tok |
|---|---:|---:|
| Today's always-on (203,889 chars) | 50,972 tok = **25.5%** | 67,963 tok = **34.0%** |
| B after (48,044 chars incl. `MEMORY.md`) | 12,011 tok = 6.0% | 16,015 tok = 8.0% |

The *relative* savings are invariant, but the absolute urgency claim ("~25% of the window before the
first prompt", MECH §6) could be a third higher. Worth resolving with `/context`, which MECH §8b says
renders a `Memory files` token row directly.

### AV-X-4 (MINOR) — `.claude/rules/` is gitignored today; three of the four proposals need a negation

```text
$ git check-ignore -v .claude/rules/x.md .claude/skills/y/SKILL.md
.gitignore:177:.claude/*	.claude/rules/x.md
.gitignore:179:!.claude/skills/**	.claude/skills/y/SKILL.md
```

- **A** correctly states that skills need no change and that only `.claude/rules/` does (§15, Phase 7). ✔
- **B** Phase 2 ships the negation. ✔
- **D** Phase 5 ships it. ✔
- **C** Phase 5(b) proposes "a thin `.claude/rules/` layer" with no mention of the negation; the files
  would be untracked and invisible to review.

---

## 9. CI feasibility — which phases fail as written

### 9.1 The gates, verified live

```text
$ gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '…required_status_checks[].context'
Documentation Links · Dependency Documentation · Release-Train Archive Guard ·
Build and Validate Package · Quality Gate · Analyze (python) · Security Scan ·
Pre-commit (Python 3.12/3.13/3.14) · Regression Tests (Python 3.12/3.13/3.14) ·
Claude.yml Access Audit · Sequence Safety
```

`Sequence Safety` is required (ml#1166 at `e209b74`), and so is `Documentation Links`.

### 9.2 What the docs screen actually fails on — measured, not inferred

From the shipped source
([`juniper-ci-tools/juniper_ci_tools/docs_additions_check.py:22-27`](../juniper-ci-tools/juniper_ci_tools/docs_additions_check.py)):

- FAIL on a deleted markdown **heading**, unless the same hunk adds one (retitle → WARN).
- FAIL on a run of `>= min_run` (5) consecutive deleted lines **with no adjacent addition**
  (`added == 0 and deleted >= min_run`).
- WARN otherwise.

Default scope: `AGENTS.md` (+ its `CLAUDE.md` symlink), `docs/**/*.md`, `notes/**/*.md` — and
[`.github/workflows/ci.yml:877`](../.github/workflows/ci.yml) invokes it with **no** `--scope`, so
`AGENTS.md` is always screened. [`.github/workflows/main-verify.yml:196`](../.github/workflows/main-verify.yml)
repeats it post-merge over `BASE..<merge>`, which is why the trailer must survive the squash.

I proved both directions in a throwaway repo (never touching this worktree):

```text
# simulate a Phase-1/Phase-3-scale relocation: drop Repository Structure + Key Files + CI/CD Pipelines
$ juniper-docs-additions-check --base HEAD~1 --head HEAD
  [FAIL/heading-deletion] AGENTS.md {'headings': ['## Key Files', … 16 headings …],
                                     'deleted': 662, 'added': 1}
  FAIL: 1 unwaived docs-deletion finding(s).
EXIT=1

# same diff, with the trailer in the commit message
$ git commit --amend -m "trim: …\n\nAllow-Docs-Rewrite: AGENTS.md"
$ juniper-docs-additions-check --base HEAD~1 --head HEAD
  [WAIVED/heading-deletion] AGENTS.md {… 'waived_by': 'Allow-Docs-Rewrite trailer'}
  OK: no unwaived docs-deletion findings.
EXIT=0
```

And a *single-domain* relocation that removes no heading and leaves a pointer line in the same hunk:

```text
# remove AGENTS.md:428-459 (32 lines of release-train bullets), add one pointer line
$ juniper-docs-additions-check --base HEAD~1 --head HEAD
  [WARN/small-deletion] AGENTS.md {'deleted': 32, 'added': 1}
  OK: no unwaived docs-deletion findings.
EXIT=0
```

**The practical rule, therefore:** a phase needs `Allow-Docs-Rewrite:` iff it **deletes a markdown
heading** from `AGENTS.md` (or removes ≥5 lines with *nothing* added in the same hunk). A phase that
swaps a block for a pointer line and leaves the heading standing passes at WARN.

### 9.3 Per-phase verdict

| Proposal | Phase | Deletes a heading from `AGENTS.md`? | Trailer named? | Verdict |
|---|---|---|---|---|
| **A** | 0, 1 | no | n/a | **PASS** |
| A | 2 (repo-map) | yes — `### Package and Metadata`, `### Documentation`, `### Scripts and Launchers`, `### Configuration` | **yes** (`Allow-Docs-Rewrite: AGENTS.md`) | **PASS** |
| A | 3–6 | no (sub-bullets under retained H3s) | no | **PASS** (WARN) |
| A | 7 (ci-workflows + shared-packages) | **yes** — `## Shared Observability Helpers`, `## Shared Service-Core Contracts`, `## CI/CD Pipelines` and its six H3s | **no** | **FAIL as written** |
| A | 8 (residual trim) | **yes** — `## Key Files` replaced by `## Skill Index` | **no** | **FAIL as written** |
| A | 9 | no | n/a | PASS |
| **B** | 0 | no repo change | n/a | PASS |
| B | 1 (root trim, ~154K chars) | **yes**, many | **yes**, with the squash-carry instruction and the "token-diff before waiving" rule | **PASS** |
| B | 2–4 | `AGENTS.md` untouched (Phase 1 already left pointers); new files are outside the docs scope (`util/CLAUDE.md` etc. are not `AGENTS.md`/`docs/`/`notes/`) | n/a | **PASS** |
| B | 5, 6 | no | n/a | PASS |
| **C** | 0 | no | n/a | PASS |
| C | 1 (`/doctor` pass) | **yes** — `### Dependency extras reference`, tree restructure | **no** (says "`juniper-docs-additions-check` with a token diff" but not the trailer) | **FAIL as written** |
| C | 2 | additive to `docs/` | n/a | PASS |
| C | 3 (the big prune) | **yes**, many | **yes** — names the trailer, the squash-carry, the token diff, and the `#1165` "restore, do not waive" lesson | **PASS** (best-in-class) |
| C | 4 (resident core) | **yes** — `## Build & Package Commands`, `## Publishing`, and the two anchor headings | **no** | **FAIL as written**, twice (docs screen + `Documentation Links`) |
| **D** | 0–5 | no deletions anywhere | n/a | **PASS — the only fully clean migration** |

### AV-F-1 (MAJOR) — B and C both specify a tree that fails `test_agents_md_tree_drift.py`

Both propose a top-level-directory-only Repository-Structure tree:

- B §4.2.2: "A **top-level-only** tree satisfies both — measured at 42 lines / 2,204 chars … **The gate
  needs no amendment.**" B enumerates two of the four assertions in the module.
- C §4.4: "18 top-level directory nodes plus the handful of root files … This is the **minimum that
  satisfies the existing gate**."

There is a fourth assertion:

```python
# tests/test_agents_md_tree_drift.py:114-116
def test_prompts_uses_agent_templates_not_stale_templates(self) -> None:
    self.assertIn("agent_templates/", self.tree)
```

`self.tree` is the *fenced block*, and `agent_templates/` occurs there 5 times, every one of them
nested content that a top-level-only tree removes. Both proposals' trees therefore fail
`Regression Tests` — a required check. A's §7.3 gets this right and budgets one nested node for it.

**Fix:** one retained line, `│   ├── agent_templates/`, ~30 chars. Negligible cost; hard failure if
missed.

### AV-F-2 (MAJOR) — A's waiver plan is incomplete

A names `Allow-Docs-Rewrite:` on Phase 2 only. Phases 7 and 8 delete H2/H3 headings and need it too.
Because `main-verify.yml` re-runs the screen post-merge on the squash commit, a missed trailer reddens
`main` — the recurring class already recorded in this project's memory. **Fix:** add the trailer to the
Phase 7 and Phase 8 descriptions, with the squash-carry note B and C both include.

### AV-F-3 (MAJOR) — A, C and D do not address the MECH §8c worktree hazard

MECH §8c is explicit that it "must be settled **before** any migration begins, because getting it
wrong inverts the result", and that under hypothesis H-a "trimming the file would make context go
**up**". This project's own worktree policy means every migration PR is authored from
`.claude/worktrees/<name>/`.

**B is the only proposal that engages with it**, and it quantifies the exposure
(`13,836 + 168,317 = 182,153`, +8.2%) and prescribes merge-then-`pull --ff-only` sequencing. A, C and D
do not mention §8c. For A the same hazard is `15,157 + 168,317 = 183,474` (+9.0%); for C,
`16,300 + 168,317 = 184,617` (+9.7%). D is unaffected because it deletes nothing.

**Fix:** adopt B §7.3's probe and sequencing as a shared Phase 0 for whichever proposal wins. It costs
two minutes and it gates the ordering of every plan.

### AV-F-4 (MINOR) — C Phase 1 and Phase 4 need trailers they do not name

See the table above. C Phase 3's handling is the model the other two phases should copy verbatim.

---

## 10. Summary

### 10.1 Counts

64 findings in total.

| Severity | Count | IDs |
|---|---:|---|
| **CRITICAL** | **2** | AV-M-1, AV-X-1 |
| **MAJOR** | **11** | AV-A-1, AV-A-2, AV-B-1, AV-B-2, AV-C-1, AV-C-2, AV-D-1, AV-X-2, AV-F-1, AV-F-2, AV-F-3 |
| **MINOR** | **27** | AV-A-M1…M6 (6), AV-B-M1…M7 (7), AV-C-M1…M5 (5), AV-D-M1…M5 (5), AV-M-2, AV-X-3, AV-X-4, AV-F-4 |
| **CONFIRMED** | **24** | AV-X-C1…C4 (4), AV-A-C1…C6 (6), AV-B-C1…C5 (5), AV-C-C1…C4 (4), AV-D-C1…C5 (5) |

Attributed per proposal. AV-M-1 and AV-X-1 are shared; the `AV-F-*` feasibility findings are
attributed to each proposal they name, so their totals are counted more than once here on purpose.

| | CRITICAL | MAJOR | MINOR | CONFIRMED | Its MAJOR findings |
|---|---:|---:|---:|---:|---|
| **A** | shares AV-M-1 | 3 | 6 | 6 | AV-A-1, AV-A-2, AV-F-2 · shares AV-F-3 |
| **B** | — | 2 | 7 | 5 | AV-B-1 · shares AV-F-1 (as AV-B-2) |
| **C** | — | 3 | 6 | 4 | AV-C-1 · shares AV-F-1 (as AV-C-2) and AV-F-3 · also AV-F-4 (MINOR) |
| **D** | shares AV-M-1 | 1 | 5 | 5 | AV-D-1 · shares AV-F-3 (vacuously — D deletes nothing) |
| **Cross-cutting / fact base** | 2 | 1 | 3 | 4 | AV-X-2 (BASE §8 is unit-inconsistent) |

### 10.2 The three sentences that matter

1. **The arithmetic in all four documents is unusually good.** Twenty-four independently-recomputed headline
   figures reproduced exactly, including every row of A's crossover table, both of B's expected values
   to the unit, four separately-constructed tables in C that all land on 152,018, and fifteen of
   fifteen byte-exact section measurements plus nine of eleven growth windows in D. I found no case
   where a claimed saving rests on a mechanism that does not deliver it.
2. **The one number that is wrong in a way that changes the plan is the `MEMORY.md` horizon.** It is
   ~20 entries / ≈19 days at the recent rate, not 35 / 33 — and the loss is silent, irreversible, and
   newest-first. That work should be sequenced ahead of every `AGENTS.md` phase in every plan, and its
   deadline is inside three weeks.
3. **The eager-savings column cannot pick a winner.** Normalized, A/B/C are 6.8% / 6.0% / 6.3% of a
   200k window — a 0.8-point spread. The decision belongs to the **worst case** (C −83.3% versus A
   −3.5% and B −0.9%) and to what survives compaction (MECH §4c-bis), not to the headline.

---

## 11. What I could not verify

Stated explicitly so none of it is mistaken for a pass.

| # | Item | Why not |
|---|---|---|
| 1 | **Whether skills are model-invocable by default** (A §3.1). I confirmed the *arithmetic* that depends on it and the *existence* of `disable-model-invocation: true` in all three shipped skills, but I did not re-extract the binary constant, and no repo evidence exists because no model-invocable skill has ever shipped here. If A §3.1 is wrong, A's saving is unchanged but its *delivery* becomes manual. A's Phase 0 is the right test. |
| 2 | **MECH §8c hypothesis H-a vs H-b.** Requires starting a session from a worktree with a divergent main-checkout `AGENTS.md`. Read-only mandate; not attempted. |
| 3 | **The compression estimates.** A's 145,675 → 112,000 (−23.1%), C's 38,650-char coverage split, and every "After" column in every proposal are *plans*. I verified they are arithmetically consistent and that A's break-even is 18.7%; I cannot verify that the prose can actually be written that short without loss. |
| 4 | **B's Tier-1/Tier-2 relocation sizes** (104,488 / 48,412) and its component attribution of the 88,971 `### Utilities` + `### Tests` chars. B's `docs/REFERENCE.md`-independent method is reproducible in principle from §13.2 but was not re-run here; the totals are consistent with the measured section sizes. |
| 5 | **B's collision-reduction model** (Herfindahl-style pair sharing, 100% → 46.5%) and A's equivalent (1.00 → ≈0.17). Both rest on domain classifiers whose regex boundaries are judgements. Out of scope for an arithmetic audit; flagged for validator 3. |
| 6 | **`eR()` = 4 or 3 chars/token.** MECH §8 lists it as unverified; `/context` would settle it and is TUI-only. |
| 7 | **The eight sibling repos' ruleset state.** I confirmed `Sequence Safety` is required on `pcalnon/juniper-ml` live; the fleet-wide claim rests on `e209b74`'s commit message, which I did not independently re-query per repo. |
| 8 | **`MEMORY.md` in-place edit growth.** Topic files behind the oldest index entries have August mtimes, proving entries are edited after creation, but the byte volume of that editing is not recoverable from the filesystem. It can only shorten the horizon. |

---

## Appendix A — reproduction commands

```bash
# §0.2 -- units. GNU wc column order is lines, chars, bytes (regardless of flag order).
wc -l -c -m AGENTS.md
python3 -c "b=open('AGENTS.md','rb').read(); s=b.decode(); print(len(b), len(s), len(s.encode('utf-16-le'))//2)"

# §0.3 / §1 -- the eager baseline.
wc -l -c -m ~/.claude/CLAUDE.md /home/pcalnon/Development/python/Juniper/AGENTS.md AGENTS.md

# §4 -- per-H2 section sizes (heading line through the line before the next H2).
python3 - <<'PY'
lines = open('AGENTS.md', encoding='utf-8').read().split('\n')
idx = [i for i, l in enumerate(lines) if l.startswith('## ')]
def size(a, b):
    t = '\n'.join(lines[a:b]) + ('\n' if b < len(lines) else '')
    return b - a, len(t), len(t.encode())
print('HEADER', size(0, idx[0]))
for k, i in enumerate(idx):
    j = idx[k + 1] if k + 1 < len(idx) else len(lines)
    print(lines[i][:44], size(i, j))
PY

# §3 -- MEMORY.md entry statistics.
python3 - <<'PY'
p = '/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md'
raw = open(p, 'rb').read()
e = [l for l in raw.decode().split('\n') if l.startswith('- ')]
bl = lambda s: sum(len((l + '\n').encode()) for l in s)
print(len(raw), len(e), bl(e[:20]) / 20, bl(e[-20:]) / 20, bl(e) / len(e))
PY

# §7 -- D's trailing-30-day series, reproduced from git.
python3 - <<'PY'
import subprocess, datetime
def size_at(d):
    r = subprocess.run(['git', 'rev-list', '-1', '--first-parent', f'--before={d} 23:59:59', 'main'],
                       capture_output=True, text=True).stdout.strip()
    s = subprocess.run(['git', 'cat-file', '-s', f'{r}:AGENTS.md'], capture_output=True, text=True).stdout.strip()
    return int(s)
for e in ['2026-03-31', '2026-04-14', '2026-04-28', '2026-05-12', '2026-05-26', '2026-06-09',
          '2026-06-23', '2026-07-07', '2026-07-21', '2026-08-04', '2026-08-18']:
    s = (datetime.date.fromisoformat(e) - datetime.timedelta(days=30)).isoformat()
    print(e, size_at(e) - size_at(s))
PY

# §9 -- the tree-drift gate's four assertions, and the 18 tracked dirs.
git ls-tree -d --name-only HEAD | grep -v '^\.' | wc -l
python3 -m unittest -v tests/test_agents_md_tree_drift.py

# §9.2 -- the docs deletion screen, both directions (in a throwaway repo, never this one).
pip install "juniper-ci-tools>=0.8.0,<0.9.0"
juniper-docs-additions-check --base <BASE> --head HEAD          # exit 1 on a heading deletion
#   ... then add `Allow-Docs-Rewrite: AGENTS.md` to the commit message -> exit 0, WAIVED

# §8 / §9 -- live gate state.
git check-ignore -v .claude/rules/x.md .claude/skills/y/SKILL.md .claude/settings.json
grep -rhno "AGENTS\.md#[a-zA-Z0-9_-]*" docs/ notes/ .github/ util/ | sed 's/^[0-9]*://' | sort | uniq -c
gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
  --jq '.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context'

# BASE §2 -- the growth curve.
bash util/ad-hoc/2026-08-18_agents_md_growth_curve.bash
```

---

## Appendix B — related documents

- [Baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md)
- [Memory mechanism facts](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md)
- [Proposal A — Skills](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md)
- [Proposal B — Locality](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md)
- [Proposal C — Pruning](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-C-DEDUPLICATION-AND-PRUNING.md)
- [Proposal D — Governance](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-D-GOVERNANCE-AND-ENFORCEMENT.md)
- [`AGENTS.md`](../AGENTS.md) · [`docs/REFERENCE.md`](../docs/REFERENCE.md)
- [`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py)
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) · [`.github/workflows/main-verify.yml`](../.github/workflows/main-verify.yml)
- [`juniper-ci-tools/juniper_ci_tools/docs_additions_check.py`](../juniper-ci-tools/juniper_ci_tools/docs_additions_check.py)
- [`juniper-doc-tools/juniper_doc_tools/check_doc_links.py`](../juniper-doc-tools/juniper_doc_tools/check_doc_links.py)
