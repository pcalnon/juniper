# Shared Session Memory — Baseline Measurements

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose

This document is the **measured fact base** for the 2026-08-18 shared-session-memory
design effort. Every proposal, validation, and plan produced in that effort must
ground its numbers here rather than re-deriving or estimating them.

All measurements were taken on 2026-08-18 in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`
at `main` = `e209b74`, clean tree.

Reproduce the growth curve with
[`util/ad-hoc/2026-08-18_agents_md_growth_curve.bash`](../util/ad-hoc/2026-08-18_agents_md_growth_curve.bash).

---

## 1. What is loaded into every session

| File | Chars | Role |
|------|-------|------|
| `~/.claude/CLAUDE.md` | 3,349 | User-global instructions (handoff policy) |
| `Juniper/CLAUDE.md` → `AGENTS.md` | 11,016 | Parent ecosystem guide |
| `juniper-ml/CLAUDE.md` → `AGENTS.md` | **170,137** | **Repo instructions — the problem file** |
| `~/.claude/projects/…/memory/MEMORY.md` | 20,388 | Auto-memory index (separate subsystem) |
| **Total** | **204,890** | ≈ 51k tokens of always-on context |

`CLAUDE.md` in this repo is a symlink to `AGENTS.md`; they are the same 170,137 bytes.
No `@path` import syntax appears anywhere in the file.

---

## 2. Growth curve

End-of-month size of `AGENTS.md`, across 323 commits:

| Month | Bytes | Commits touching the file |
|-------|-------|---------------------------|
| 2026-02 | 8,539 | 2 |
| 2026-03 | 10,146 | 8 |
| 2026-04 | 23,684 | 6 |
| 2026-05 | 38,248 | 22 |
| 2026-06 | 63,911 | 42 |
| 2026-07 | 119,707 | 208 |
| 2026-08 (to 08-17) | 170,137 | 35 |

**≈20× in six months, roughly doubling every two months.** The curve is
super-linear, not linear: the file is not merely growing, its growth *rate* is
growing. Recent commits are overwhelmingly add-only (`+N / −0`).

PR-merge commits touching `AGENTS.md` per month: 3 (Apr), 12 (May), 41 (Jun),
34 (Jul), 35 (Aug). Since June that is **≈1.3 merges per day** landing edits into
one file — the concurrent-session signature.

---

## 3. Where the bytes are

By H2 section:

| Bytes | % of file | Section |
|-------|-----------|---------|
| 99,304 | 58% | `## Key Files` |
| 20,469 | 12% | `## Repository Structure` |
| 16,101 | 9.5% | `## CI/CD Pipelines` |
| 4,617 | 2.7% | `## Build & Package Commands` |
| — | — | *(11 further sections, each < 5K)* |

**Three sections hold 79% of the file.**

Within `## Key Files`, by H3:

| Bytes | % of file | Subsection |
|-------|-----------|------------|
| 54,510 | 32% | `### Utilities` — per-script prose |
| 34,579 | 20% | `### Tests` — per-test-file prose |

Those two subsections alone are **52% of the entire file**.

---

## 4. The accretion signature

| Metric | Value |
|--------|-------|
| Top-level `- \`entry\`` bullets | 126 |
| Nested `  - ` sub-bullets | 156 |
| Bytes in nested sub-bullets | **44,350 (26% of the file)** |
| Lines citing an issue/PR number (`#NNN`) | 70 |
| Lines pointing at `docs/REFERENCE.md` ("Operator surface/detail/table…") | 32 |
| Lines naming a gate/pin/test | 34 |

The dominant growth mechanism is visible in the shape of the file: successive
sessions do not add new entries so much as **append per-incident detail as nested
sub-bullets under entries that already exist**. Those sub-bullets are now a
quarter of the file. They read as post-mortem findings — a failure class, the
issue number that found it, the gate that now pins it.

This is *valuable* knowledge, honestly earned. The problem is placement, not
quality: it is loaded into every session of every agent regardless of task.

---

## 5. Duplication with `docs/`

| File | Chars |
|------|-------|
| `docs/REFERENCE.md` | 162,231 |
| `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` | 64,267 |
| `docs/DOCUMENTATION_OVERVIEW.md` | 16,955 |
| `docs/QUICK_START.md` | 7,803 |
| **Total `docs/`** | **251,256** |

`docs/REFERENCE.md` already carries 73 sections on precisely the subjects
`## Key Files` documents at length — *Editable Install Drift Check*, *Pytest Orphan
Reaper*, *Environment Floor Drift Check*, *Agent Suite Doctor*, *Isolated Stack E2E
Utilities*, *Fleet Triage and Sequence Safety*, *Experiment Stack Utilities*,
*Docs Full Check*, *Shared-Package CI Workflows*, *Release-Train Detect Summary*,
and more.

**AGENTS.md has grown a parallel, always-loaded summary of a 162KB reference
document that already exists and is read on demand.** 32 lines in AGENTS.md
explicitly end by pointing at the REFERENCE.md section that holds the same
material. This is the largest single structural redundancy in the file.

---

## 6. Existing gates on AGENTS.md

| Gate | Enforces |
|------|----------|
| `tests/test_agents_md_version_drift.py` | Header `**Version**` == `pyproject` version |
| `tests/test_agents_md_header_schema.py` | 6-field header, ISO date |
| `tests/test_agents_md_tree_drift.py` | Every tracked top-level dir appears in the tree |
| `.github/workflows/agents-md-touch-up.yml` | `**Last Updated**` is today-or-changed-in-PR |

Four gates protect this file's *structure and currency*. **None enforces a size
budget, and none constrains what may be added.** Every gate is satisfied by an
edit that appends 500 lines. The file has guardrails against staleness and none
against growth — which is precisely the failure mode observed.

---

## 7. This is a fleet trend, not one bad file

| Repo | `AGENTS.md` chars |
|------|-------------------|
| juniper-ml | **170,137** |
| juniper-canopy | 94,373 |
| juniper-cascor | 70,118 |
| juniper-data | 41,371 |
| juniper-deploy | 33,373 |
| juniper-cascor-worker | 33,203 |
| juniper-cascor-client | 29,457 |
| juniper-data-client | 24,706 |
| juniper-recurrence | 9,990 |

juniper-ml is the extreme case, but canopy and cascor are on the same trajectory
and are already large enough to matter. A session in any repo loads the
user-global file plus the parent ecosystem guide plus that repo's `AGENTS.md`, so
a canopy session already carries ≈109K of always-on instructions.

Any remedy should therefore be **portable across all nine repos**, not tailored to
juniper-ml. The repo has precedent for this: `tests/test_agents_md_header_schema.py`
is deliberately written to be self-locating and droppable into any Juniper repo's
`tests/`.

---

## 8. Two genres are conflated in one file

Lines carrying mandatory language are attached overwhelmingly **not** to agent
behaviour but to the internal contracts of specific utilities:

> **Predicate corrected 2026-08-18** (grounding validator). This section first
> reported "164 lines … (`MUST` / `MANDATORY` / `NEVER` / `PROHIBITED`)". The
> count of 164 came from a **seven**-term grep that also included `REQUIRED`,
> `do not ` and `always ` — so the stated word list did not produce the stated
> number, and 164 is not reproducible from it. The validator reproduced every
> proposal's figure exactly against its own declared predicate:
>
> | Count | Predicate | Used by |
> |------:|-----------|---------|
> | 124 | `\b(must\|mandatory\|never\|prohibited)\b` | Proposal D |
> | 125 | same words, no word boundaries | Proposal B |
> | 160 | six terms with word boundaries | Proposal A |
>
> **The conclusion is unaffected and is robust across all three predicates:**
> 139/160, 108/125 and 107/124 of the mandatory lines sit in genre-B sections —
> 86–87% in every case.

> `touches_releases` inspects **both** sides of a rename/copy so a rename-OUT of
> `notes/releases/` is still an archive PR and FAILs (never SKIP).

> Offline `--local-git` must raise (open #773), not return `set()`.

That is a specification for a script, not an instruction to the agent reading it.
The file therefore mixes two genres with very different loading requirements:

| Genre | Example | Needs to be… |
|-------|---------|--------------|
| **A — Agent behaviour** | use worktrees; handoff instead of compaction; scripts go in `util/`, never `/tmp`; PR conventions | always on |
| **B — Component contract / regression lore** | how `predict_merge` classifies a verdict; what `SHIP_UNCERTAIN` means; the `ref=` requirement on the archive lane | on hand *when working on that component* |

Genre B dominates by volume and is the entirety of the three largest sections.
It is hard-won knowledge and must not be discarded — but it is being paid for on
every session of every agent, including agents that will never touch the
component in question.

**Sizing implication.** Removing the three largest sections — `## Key Files`,
`## Repository Structure`, `## CI/CD Pipelines` — leaves **32,443 characters
(32,510 bytes)**. That is roughly the size of the genre-A core plus the smaller
sections, and it is the natural order of magnitude for a target budget.

> **Corrected 2026-08-18** (arithmetic validator, finding AV-X-2). This figure was
> first published as **34,263**, computed as `170,137 − 135,874` — subtracting a
> *character* total from a *byte* total. The file is **168,317 characters /
> 170,137 bytes**; the per-section table above is on a character basis. The
> correct arithmetic is `168,317 − 135,874 = 32,443` chars, or
> `170,137 − 137,627 = 32,510` bytes — a 1,820-char overstatement.
>
> This matters beyond bookkeeping: **Proposal D adopted 34,263 as a candidate
> budget ceiling**, so the error propagated. It also fixes the unit to use when
> reasoning about the CLI warning — the shipped check compares `content.length`,
> i.e. **characters**, making the file 4.21× the 40,000 floor, not 4.25×.

---

## 9. Open questions delegated to fact-finding agents

Two facts are load-bearing for any proposal and were not derivable from the repo:

1. **The limit.** Whether Claude Code documents a specific character/token
   threshold for memory files, and whether the behaviour at that threshold is
   hard truncation or a soft warning. A hard truncation means content is being
   *silently lost today*; a soft warning means the cost is attention and tokens.
   These imply materially different urgencies.
2. **Import semantics.** Whether `@path` imports are resolved eagerly at session
   start. If eager, modularization relocates bytes without reducing loaded
   context, and any proposal resting on "split the file up" is void.

Findings are recorded in the proposals and the final plan.
