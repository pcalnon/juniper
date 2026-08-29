# P5 step e — canopy and cascor cut preparation

**Project**: Juniper — shared-session-memory plan §P5 step e (the cut)
**Author**: Paul Calnon
**Date**: 2026-08-28
**Status**: PREP ONLY — nothing written to juniper-canopy or juniper-cascor
**Plan**: [`JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` §P5](JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md)
**Tracker**: [juniper-ml#1326](https://github.com/pcalnon/juniper-ml/issues/1326)

---

## 1. Why this document exists

Three cuts shipped on 2026-08-28 — cascor-client #142, data #296, data-client #176 — plus a
recurrence ceiling raise (#135). canopy and cascor are the two governed repos still uncut. Both
turned out to be **materially different from the three that shipped**, in ways that would have
produced a bad PR if the same recipe had been applied mechanically. This records what differs,
what was measured, and what decision is owed before execution.

**Neither repo was written to.** No worktree, branch, PR, or file was created in either.

## 2. Execution is blocked right now — live services on both primaries

Measured 2026-08-28 from `/proc/<pid>/cwd` and `ss -tlnpH`, not inferred:

| | juniper-canopy | juniper-cascor |
|---|---|---|
| Service on the **primary** | `main.py` pid 1379952, `:8051`, up ~11.2 h | `uvicorn` pid 1379625, `:8202`, up ~11.2 h, + forkserver + resource_tracker |
| Worktrees | **11** (5 created 08-27/08-28) | 14 (mostly stale experiment trees) |
| Occupied worktree | `fix/f039-stale-shortcircuit` — **dirty**, pid 2797792 on `:8052` | none |

**Why a live service on the primary blocks the cut, rather than merely complicating it.** The
plan's standing hazard is that a cut must land on `main` **with the primary pulled** before any
worktree carries the trimmed file, because a worktree whose `AGENTS.md` differs from the primary's
loads **both copies** (the P1 ancestor canary measured this; it is not theoretical). A service
running out of the primary means the primary cannot be pulled. Merging a cut then leaves `main`
trimmed and the primary untrimmed, and **every worktree created from `origin/main` afterwards loads
both** — for canopy that would be ~16K + 95K instead of 95K. The peer session `canopy e2e` is
creating canopy worktrees daily, so that cost lands on it.

**Merging the cut without being able to pull the primary is worse than not cutting.**

Precondition for execution, both repos: the primary is free of live services, and the cut's merge
and the primary pull happen in the same pass.

### 2.1 Confirmed with the owning session (2026-08-28)

The peer session `canopy e2e` owns **both** primary services — they are one isolated E2E trio for
the canopy F-CANOPY-037/039 arc, canopy on `:8051` and cascor uvicorn on `:8202`. It confirmed:

- **Window**: the stack is not idle (mid-investigation; F-039 just root-caused off it), but the
  remaining work is a write-up plus one runtime probe. It will signal when both primaries are free,
  and can re-create the stack cheaply (`util/isolated_stack.bash --up`, ~7 min) if torn down early.
- **No `AGENTS.md` conflict**: none of its merged canopy PRs (#531–#536) touched `AGENTS.md` or
  `CLAUDE.md`, and its one open branch (`fix/f039-stale-shortcircuit` → #537) does not either.
- **The `:8052` leg is transient** — a second canopy run from a worktree, used to A/B a fix against
  the primary. It comes and goes and never blocks a pull. Do not treat it as a blocker.
- **Worktree disposition**: six are sweepable now (f012 #535, f026 #534, f036 #536, f037 #531,
  p2-wave-a #532, p2-wave-b #533) plus the finished detached-HEAD `ab-premerge-9f6fac9`.
  **KEEP `fix/f039-stale-shortcircuit`** — PR #537 is open and may still drive a leg.

It also flagged, independently, that the canopy **primary** carries ~60 ignored entries — the
`worktree remove` deletes-ignored-files hazard. `2026-08-28_p5_worktree_cleanup.py` already gates on
`git status --porcelain --ignored` and refuses anything not matching a known-disposable pattern.

## 3. The destination problem — this is the real blocker, not the services

The three shipped cuts all relocated into an existing `docs/REFERENCE.md` that was a genuine
**content** file with its own TOC and section structure. Neither remaining repo is in that position.

### 3.1 canopy's `docs/REFERENCE.md` is an INDEX, not a destination

It says so in its own Overview:

> This document serves as a central index for all technical reference documentation in
> juniper-canopy. Each section links to the detailed reference document for that subsystem.

It is 9,672 chars of pointers into a 38-file `docs/` tree (`api/`, `cascor/`, `cassandra/`,
`ci_cd/`, `demo/`, `deployment/`, `history/`, `redis/`, `testing/`). Relocating ~50K of `AGENTS.md`
prose into it would destroy that role and leave the repo with no index.

This conflicts with canopy's own `conf/memory_budget.json`, whose `_README` states
*"docs/REFERENCE.md is deliberately NOT governed. It is the migration DESTINATION"*. That line was
inherited verbatim from the juniper-ml template during the P5 port and was never checked against
what canopy's REFERENCE.md actually is.

### 3.2 cascor has no `docs/REFERENCE.md` at all

It has `docs/{api,ci_cd,install,overview,source,testing}` plus `DEVELOPER_CHEATSHEET.md` (40,219),
`DOCUMENTATION_OVERVIEW.md` (28,319) and `INDEX.md` (5,262). A REFERENCE.md must be created, and
its relationship to the existing `INDEX.md` decided.

### 3.3 The content is NOT already documented elsewhere — the cut is a real relocation

The obvious hope was that `AGENTS.md` duplicates the `docs/` tree, making the cut a cheap
deletion-plus-pointer. Measured with
[`util/ad-hoc/2026-08-28_p5_docs_tree_overlap.py`](../util/ad-hoc/2026-08-28_p5_docs_tree_overlap.py),
comparing every substantive `AGENTS.md` line against every `.md` under `docs/`:

| Repo | docs files | AGENTS.md substantive lines already under `docs/` |
|---|---:|---|
| juniper-canopy | 38 | **2 / 522 (0%)** |
| juniper-cascor | 27 | **0 / 255 (0%)** |

Both cuts are genuine relocations. Nothing can be deleted as redundant.

## 4. Measured section inventories

Both tables produced by
[`util/ad-hoc/2026-08-28_p5_cut_section_sizes.py`](../util/ad-hoc/2026-08-28_p5_cut_section_sizes.py)
against `main`, chars (the ceiling's unit).

### 4.1 juniper-canopy — 95,133 chars, 34 sections

**Nearly a third of the always-resident file is documentation-about-documentation:**

| Section | chars |
|---|---:|
| Documentation File Types | 6,771 |
| Documentation Standards | 5,109 |
| Documentation Maintenance Workflow | 4,896 |
| Archive Procedures | 3,720 |
| Documentation Organization | 3,334 |
| Update Triggers | 3,186 |
| Documentation Update Workflow | 671 |
| **subtotal** | **27,687 (29%)** |

That is rules for *authoring documentation*, resident in every session regardless of task — the
strongest relocation candidate in the fleet so far. Technical reference is the next group:
Architecture 12,414, Configuration Management 7,272, API and WebSocket Contracts 4,194
(**23,880**). Together ~51,600 chars, which after ~10 pointers lands `AGENTS.md` near **46,000**.

Keep resident: Quick Start Commands (10,009), AI Agent Quick Start, File Placement Rules, Demo Mode
Contract, Common Issues, Thread Handoff, Worktree Procedures, Definition of Done.

### 4.2 juniper-cascor — 71,098 chars, 29 sections

| Tier | Sections | chars |
|---|---|---:|
| **A — core reference** | Directory Structure 10,577, CI/CD Pipelines 8,141, REST API 4,037, WebSocket Protocol 2,769, Core Components 2,444, Middleware Stack 2,418, Constants Configuration 1,973, Documentation Files 1,740, Key Dependencies 1,687 | **35,786** |
| **B — add if wanted** | Remote Worker System 6,331, Testing Infrastructure 4,261 | 10,592 |

Tier A alone lands `AGENTS.md` near **37,500**; A+B near **27,500**. Keep resident: Quick Reference
(7,429 — commands), Programming Conventions, Script Placement, Security Notes, Known Issues,
Thread Handoff, Worktree Procedures.

## 5. A defect found in the tooling — and what it invalidated

The section-size script tracked fenced code with a naive `startswith("```")` toggle. **canopy's
`AGENTS.md` wraps three-backtick examples in FOUR-backtick fences**, so the inner fences flipped the
parity: 189 fence lines, odd. Everything after the first such block was inverted — **13 real
headings were swallowed** and two markdown examples were promoted into sections, one of them a
phantom "REST API Endpoints" of 15,209 chars. The first canopy inventory produced from it was wrong
(28 sections; the true count is 34).

Fixed to the CommonMark rule: a fence opens with ≥3 of `` ` `` or `~` and is closed only by a fence
of the same character, at least as long, carrying **no info string**.

**Checked what else this could have touched.** The three cuts merged earlier the same day used
explicit `--heading` arguments through `2026-08-19_p3_relocate_section.py`, whose `extract()` is
*also* not fence-aware — a `##` inside a code block could have truncated a section mid-move.
Verified against `main` after merge: all three files have **even fence parity and no four-backtick
fences**, and **all 16 relocated sections contain the pointer line only**, with no orphaned prose.
The shipped work is sound; only canopy's planning table was affected.

Related caution for the cut itself: much of both files is fenced content, not prose. cascor's
"Quick Reference" is 7,429 chars but **1** substantive line; "REST API" is 4,024 chars and 1 line.
G3 (`relocation_check`) counts substantive prose, so for such sections it has almost nothing to
verify and will report a low `removed_substantive`. **The heading-presence check added on 2026-08-28
is doing the real work there** — see §6.

## 6. Gates a cut must satisfy (learned from the three that shipped)

1. **Sequence Safety fails every cut** with `[heading-deletion]`. The plan text calling this "a WARN
   at any magnitude" is **wrong** — it is a FAIL. Remedy is an `Allow-Docs-Rewrite: AGENTS.md`
   commit trailer. The `docs-rewrite` / `allow-symbol-loss` **labels are WARN-only and do NOT
   unblock a merge**; only the trailer does.
2. **G3 does not examine headings.** `relocation_check` matches substantive prose, so `unmatched=0`
   is silent on whether headings survived. Verify heading presence in the destination separately
   before waiving — the two gates are complementary and neither alone covers a relocation.
3. **The AGENTS.md Date Check** fails any PR touching `AGENTS.md` without advancing
   `**Last Updated**:`.
4. **`relocation_check` needs a commit** — run against an uncommitted tree it exits 2 with
   *"would have passed vacuously"*.
5. **Lower the ceiling by hand**, never bare `--ratchet` (it leaves zero headroom).

All five are handled by [`util/ad-hoc/2026-08-28_p5_cut.py`](../util/ad-hoc/2026-08-28_p5_cut.py)
(`prepare | ship | waive | bump-date | raise-ceiling`).

## 6a. PREREQUISITE — a hazards triage must precede the canopy cut

Raised by the `canopy e2e` session and adopted. canopy's `AGENTS.md` has **no `## Hazards`
section**; juniper-ml's does, with the rationale spelled out — these are directives whose
*non-application* destroys work, kept resident because *"a pointer only helps an agent that already
knows to look"*. **A size-driven cut cannot distinguish a lookup-reference from a
must-not-look-up warning.**

The framing that settles it: **a relocation is the same move as a rename — it turns a resident fact
into a reference someone has to follow.** That session recorded three instances in three days of a
guard that existed, read as correct, and never fired because it named something that had moved
(F-CANOPY-039 still naming `fast-update-interval` after F-027 replaced it; F-038's Stage 2
suppression never biting; F-033 attributing a reset storm from a stale itempath index).

### The triage tool needed a positive control before it could be believed

[`util/ad-hoc/2026-08-28_hazard_triage.py`](../util/ad-hoc/2026-08-28_hazard_triage.py) scores
blocks for four signals: prohibition, silent-failure, irreversibility, hazard-noun.

Its **first version scored per line and found ZERO candidates in juniper-ml's `AGENTS.md`** — a file
whose `## Hazards` section contains four bullets. A hazard-finder that finds no hazards is the
vacuous-pass class, and only a positive control against a file known to contain them caught it.
Cause: the directives are wrapped prose, so "Do not set it" and "silently diverges" land on
different lines and no line reaches two signals. Now scored per **block**; re-validated to find all
four of ml's hazards, ranked top. A later pass excluded fenced code, which had produced a false
positive off a `try/except` sample's own comments.

### Result for canopy

Four candidates at ≥2 signals, **none in a section proposed for relocation**: Testing Guidelines
(the no-`branches:`-filter check), File Placement Rules ×2 (the `/tmp/` prohibition and its
incident pointer), Thread Handoff (the CRITICAL OPERATING INSTRUCTION).

**But at ≥1 signal, inside proposed relocation targets:**

| line | section | text |
|---|---|---|
| L1325 | API and WebSocket Contracts | **"Do not change existing payload keys without versioning"** |
| L887 | Code Style Guidelines | "No global mutable state without locks — all shared state must use `threading.Lock()`" |
| L888 | Code Style Guidelines | "Any long-lived collections must be size-bounded … prevent memory leaks" |
| L767 | Configuration Management | "All new env vars must use the `JUNIPER_CANOPY_` prefix" |
| L456 | Architecture | training counter semantics |

**L1325 vindicates the prerequisite.** It is a contract hazard whose violation is silent to the
author and breaks clients, and the plan as drafted would have relocated it into a reference file.
Section titles would never have surfaced it.

Recommendation to the owning session (not executed): promote L1325 and probably L887/L888;
L767 is a convention whose violation is loud; L456 reads descriptive. That is 2–3 bullets against
juniper-ml's 4. **Sequence: promote first, then cut around the resident set.**

## 6b. The sweeper gate earned its keep, and got better

Running the gated sweeper over canopy's 11 worktrees returned **0 removable, 11 blocked** — and for
the six the owning session believed were sweepable, the blocker was **not** PR state but `logs/` and
`snapshots/`. Asking rather than generalising surfaced a **real evidence loss**: the session checked,
found the worktree logs boring, and discovered that F-CANOPY-039's root cause — 35 `TOPOPROBE` lines
showing the client's topology store pinned at the 75-byte empty default while the server returned
7,059 bytes every tick — existed only in `/tmp/juniper-e2e/juniper-canopy-ab.log`, which is reaped
at session end. Now harvested to `reports/e2e/20260828T132533Z/f039_evidence/`.

**`logs/`/`snapshots/` were deliberately NOT added to the disposable list.** The distinguishing fact
was not the filename but *whether a live leg had ever run from that tree* — which no pattern can
see. Instead the blocked-reason line now prints size and newest mtime per entry, so a 0-byte
`custom.log` from three weeks ago is visibly different from a 425 KB `system.log` written twenty
minutes ago. Keep the friction; reduce the noise.

## 7. Decisions owed before execution

1. **canopy's destination — RESOLVED in principle**, refined by the owning session, which
   independently verified that `REFERENCE.md`'s 13 sections are one-line descriptions plus tables of
   links, i.e. a hub. The two options are **not alternatives, they are two different materials**:
   - the ~27.7K of documentation-**about**-documentation → `docs/DOCUMENTATION_OVERVIEW.md`, which is
     literally the file whose subject that is (29% off the resident file on its own);
   - everything else reference-shaped → a new `docs/AGENTS_REFERENCE.md`;
   - `REFERENCE.md` gains one row per destination and **stays an index**.

   Splitting by subject rather than convenience keeps either destination from becoming a junk
   drawer. Still to do: correct the inherited `_README` line in canopy's `conf/memory_budget.json`,
   which asserts something false about that repo — a stale pointer inside the config for the gate
   whose purpose is to prevent exactly that.
2. **cascor's new `REFERENCE.md`** and its relationship to the existing `docs/INDEX.md`.
3. **cascor tier A or A+B.**
4. ~~**Sequencing with `canopy e2e`**~~ — **RESOLVED, see §2.1.** It owns both primaries, has no
   `AGENTS.md` work in flight, will signal when the stack is down, and has identified 7 of its 11
   worktrees as sweepable. The remaining coordination is only *when*, and the answer is "whenever it
   signals" — §8 shows neither repo is close to firing, so waiting costs nothing.

## 8. Urgency — neither is close to firing

Re-measured 2026-08-28 (`measure-growth --ref origin/main`):

| Repo | AGENTS.md | ceiling | headroom | rate/day | days |
|---|---:|---:|---:|---:|---:|
| juniper-canopy | 95,133 | 97,133 | 2,000 | 66 | ~30 |
| juniper-cascor | 71,098 | 80,707 | 9,609 | 205 | ~47 |

**Note the ordering correction.** Plan §P5 says order by rate and names cascor "start here" — that
was the input for the **port**. For the **cut** the input is `headroom ÷ rate`, and by that measure
cascor is the least urgent repo in the fleet. Waiting for a clean window costs nothing.

## 9. Tooling produced by this prep (juniper-ml, `util/ad-hoc/`)

| Script | Purpose |
|---|---|
| `2026-08-28_p5_cut_section_sizes.py` | Per-section char inventory of any repo's `AGENTS.md`; CommonMark-correct fence handling |
| `2026-08-28_p5_cut_overlap_probe.py` | `AGENTS.md` vs its own `docs/REFERENCE.md`, per section |
| `2026-08-28_p5_docs_tree_overlap.py` | `AGENTS.md` vs the whole `docs/` tree, with best-matching document |
| `2026-08-28_p5_cut.py` | The cut driver — worktree, relocation, TOC, date bump, ceiling, controls, signed PR |
| `2026-08-28_p5_worktree_cleanup.py` | Gated arc cleanup (PR merged, unoccupied, clean, no unrecoverable ignored files) |
