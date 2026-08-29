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

It is 9,672 chars (chars, not the 9,676 bytes `wc -c` reports — the ceiling's unit is chars) spread
over 11 content sections pointing into a 38-file `docs/` tree (`api/`, `cascor/`, `cassandra/`,
`ci_cd/`, `demo/`, `deployment/`, `history/`, `redis/`, `testing/`). Relocating ~50K of `AGENTS.md`
prose into it would swamp that role.

**"It is an index" is only half true, corrected 2026-08-29.** Measured per section: five of the
eleven carry **inline content** rather than links — Environment Variables Quick Reference (2,219, an
18-row table, and *missing from the file's own ToC*), Configuration Reference (1,161), WebSocket
Reference (1,045), Constants Reference (478), Overview (325). That is **5,228 of 9,672 = 54.1%
inline**. So it is a hybrid: a hub for half its bulk and a content file for the other half. The
index-vs-destination conclusion stands for the pointer half, but anyone relocating into it must plan
to *merge* with existing content rather than append. Under the decision recorded in §7 nothing bulky
lands there at all, so this does not bite — but that Environment Variables table is itself a
relocation candidate the next pass should look at.

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
| **subtotal** | **27,687 (29.1%)** |

*The 27,687 is the **sum of those seven discrete sections**, which are not contiguous in the file —
measuring any span between two of them instead (e.g. `## Documentation Organization` →
`## Definition of Done` = 29,130) counts intervening sections and gives a different, larger number.
Re-derived 2026-08-29 with `2026-08-28_p5_cut_section_sizes.py`: 6,771 + 5,109 + 4,896 + 3,720 +
3,334 + 3,186 + 671 = 27,687 of 95,133.*

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
(`prepare | ship | waive | bump-date | raise-ceiling | status`; `status` is the read-only one).

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

### The agreed resident set — five bullets

Settled with the `canopy e2e` session, which verified every line reference against the file and ran
an independent keyword sweep (`silent|silently|irrecoverab|cannot be undone|clobber|data loss`) that
surfaced **nothing the block scorer missed** — two methods converging on the same set. Ranked by
what it costs to learn each the hard way:

| # | Source | Directive |
|---|---|---|
| 1 | **NEW TEXT — not in `AGENTS.md` at all** | **Dash `no_update` chaining.** A clientside producer that returns `no_update` when idle must NEVER be an Input to an interval-driven callback — Dash skips that callback for that tick, and the lane simply stops firing with no error and no failing test. Justification is the `CRITICAL` label its own author gave it plus the silence of the failure mode — **not** an incident receipt; see the correction below. |
| 2 | `AGENTS.md` L1325 | "Do not change existing payload keys without versioning" — silent to the author, breaks clients, and it sat inside a relocation target. |
| 3 | L887 | No global mutable state without locks. `TrainingState`'s lock is load-bearing; F-CANOPY-036 accumulates under it. A lockless shared write corrupts a run silently. |
| 4 | L888 | Long-lived collections must be size-bounded. Documented memory pressure (`REPLAY_WEIGHT_BUFFER_MAX` reasons about a few-hundred-MB peak); unbounded growth kills a long run with no warning. |
| 5 | L1420 | The `/tmp/` prohibition — the one hazard here with an actual incident record, and this arc added a second data point (§6b). |

> **Correction, 2026-08-29 — bullet 1's original rationale was refuted, and the bullet survives on a
> narrower basis.** It was first proposed with the claim that chained `no_update` had "already cost
> a P0/P1". An adversarial fact-check found that unsourced, and the ledger contradicts it:
> [`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:414-419`](JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md)
> records the closest tested instance — `visualization-tabs.active_tab` as an Input poisoning a
> writer, *"with a comment naming this hazard as 'the I-1 starvation'"* — and rules it **"Plausible,
> and *wrong*: moving it to `State` … left the panel exactly as dead. Reverted."** F-CANOPY-027's
> actual root cause was dash-renderer's hard-coded 12-slot pool.
>
> What survives is enough on its own: the comment is real, its author labelled it `CRITICAL`, the
> Dash execution-model property it describes is genuine, violating it is **silent**, and it is
> absent from `AGENTS.md`. Promote it on the CRITICAL-label + silent-failure basis. **Do not carry
> any "already cost a P0/P1" wording.** Noted here because promoting on an unre-measured rationale
> is the exact failure this whole prerequisite exists to prevent — the prerequisite caught itself.

> **A second live instance of the same class, 2026-08-29, volunteered by the owning session against
> its own work.** Its F-CANOPY-039 headline — *"the client's copy of `network-visualizer-topology-store`
> is permanently the 75-byte empty default; it never advances, not once"* — was **wrong**, and had
> already been written into an evidence ledger, a click-by-click matrix, a PR test docstring and a
> handoff. The probe log's first four samples showed `eq=False, cur_len=75`; its **last eleven**
> showed `eq=True, cur_len=7059` over one continuous 71-second window with no restart. The store is
> empty for ~22 s and then converges.
>
> **The mistake was not the measurement. It was reading the head of an instrument's output and
> writing the generalisation into four documents before reading the tail.**
>
> What caught it is the counter-practice worth copying: the session had just generalised that
> one-off probe into a **re-runnable tool** — motivated by an earlier amputation finding, so the
> instrument would not be lost — and the first thing it did was replay it over its own archived
> evidence. The tool refuted its author on first use. It has since been changed to print the
> distinct values unconditionally, so that specific generalisation cannot recur silently.
>
> *(The underlying finding got stronger, not weaker: over the same window the rebuild renders empty,
> which it can only do via its `input_units == 0` fast path — so the store's writer sees 7,059 bytes
> while its reader sees 0, simultaneously, for one store id. That is a duplicate-instance signature
> evidenced from both sides rather than inferred from absence, and a `dcc.Store` renders no DOM,
> which is why a clean static layout check missed it. It does not change bullet 1's narrowed basis.)*

**Bullet 1 is the finding that justifies the whole prerequisite, and no scan of `AGENTS.md` could
have produced it.** It lives at `src/frontend/dashboard_manager.py:3869`, labelled `CRITICAL` by its
own author; `grep -icE "no_update|execution model|starv" AGENTS.md` → **0**. A cut that only decides
where existing text goes will never surface it — it has to be *written*, not relocated. That is why
[`util/ad-hoc/2026-08-28_resident_gap_scan.py`](../util/ad-hoc/2026-08-28_resident_gap_scan.py)
exists: it asks the complementary question (what is hazard-shaped in the **source** and resident
nowhere?) and independently rediscovers that same block at `dashboard_manager.py:3858`, plus 63
further candidates across 217 hazard-marked comment blocks.

**Rejected, by agreement:** L767 (`JUNIPER_CANOPY_` prefix) is a convention — violating it fails
loudly, the setting just doesn't take. L456 (counter semantics) is descriptive, not directive.

**Deliberately NOT folded in:** L2675 (thread handoff) and L1122 (the CI check that cannot block).
Both are real and both stay resident, but they are operating procedure and CI topology, not code
hazards. juniper-ml's block works because all four bullets answer one question — *what will silently
destroy work while you are editing code*. Mixing in process directives dilutes it into a general
"important stuff" section, which is how these grow back. Keep them as their own resident sections.

**Sequence: promote first, then cut around the resident set.**

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

## 6c. BLOCKER FOUND AND FIXED — the relocate tool would have silently mangled canopy

Found during this prep, before any canopy PR existed.
[`util/ad-hoc/2026-08-19_p3_relocate_section.py`](../util/ad-hoc/2026-08-19_p3_relocate_section.py)
— the tool that performed all three cuts on 2026-08-28 — was **fence-blind**, and its
`heading_level` cannot distinguish a markdown heading from a shell comment: both are `# text` at
column 0. So the first `# Run all tests` inside a code block ended a `##` section, because level 1
is `<= 2`.

canopy's `AGENTS.md` carries **136 heading-looking lines inside fences**. Simulated against `main`
before the fix — 8 of 11 candidate sections truncate:

| Section | true chars | extracted | orphaned |
|---|---:|---:|---:|
| Quick Start Commands | 10,009 | **62** | 9,947 |
| Documentation File Types | 6,771 | 354 | 6,417 |
| Code Style Guidelines | 4,580 | 314 | 4,266 |
| Archive Procedures | 3,720 | 185 | 3,535 |
| Documentation Standards | 5,109 | 2,043 | 3,066 |
| Configuration Management | 7,272 | 5,240 | 2,032 |
| Documentation Maintenance Workflow | 4,896 | 3,077 | 1,819 |
| API and WebSocket Contracts | 4,194 | 3,808 | 386 |
| Architecture / Update Triggers / Documentation Organization | — | — | 0 (unaffected) |

**Nothing in the gate chain would have caught it.** The move succeeds; the remainder sits orphaned
under a "Moved to …" pointer; and **G3 still PASSES** — every line it *did* remove is present in the
destination, and G3 has no way to notice lines that were never removed. The heading-presence check
from §6a passes too, on the headings that did move. The only symptom would be *"the cut removed less
than expected"*, which nothing measures.

> **Generalises beyond this tool: a completeness check that verifies what moved cannot see what
> failed to move.**

**Fixed** with a CommonMark fence mask (a fence closes only on ≥ the opening run with no info
string), applied both to the heading *match* and to the section-end scan — so a `## X` shown as a
markdown example can no longer be mistaken for the real section either.

**Blast radius, checked rather than assumed:**

- **The three cuts shipped 2026-08-28 are unaffected.** Verified against `main` after merge: even
  fence parity, no four-backtick fences, and all 16 relocated sections contain the pointer line
  only, with no orphaned prose. Their fenced examples carry no column-0 `#` comments.
- **cascor is unaffected: 9 of 9 tier-A sections extract fully** (Directory Structure 10,577,
  CI/CD Pipelines 8,141, REST API 4,037, WebSocket Protocol 2,769, Core Components 2,444, Middleware
  Stack 2,418, Constants Configuration 1,973, Documentation Files 1,740, Key Dependencies 1,687 —
  each `true == extracted`). This was canopy-specific.
- **canopy after the fix: 9 of 9 re-simulated sections extract fully.**

Pinned by [`tests/test_p3_relocate_section.py`](../tests/test_p3_relocate_section.py) — 12 tests,
wired into `ci.yml` (that list is hand-maintained; new tests do not self-register). Negative control
run: against the old fence-blind logic the load-bearing case extracts 3 lines where 11 are needed,
so the suite bites. It also pins the four-backtick fence, the info-string closing rule, and
heading-inside-a-fence non-matching.

## 6d. KNOWN GAP — the agreed canopy split is not executable by the current tooling

Raised by the validators on the arc-wide handoff (ml#1456) and confirmed here. The two-destination
canopy plan agreed in §7 — documentation-about-documentation to `docs/DOCUMENTATION_OVERVIEW.md`,
everything else to a new `docs/AGENTS_REFERENCE.md` — **cannot be run by the tooling as it stands**:

- [`util/relocation_check.py`](../util/relocation_check.py) takes a **single** `--dest`
  (`ap.add_argument("--dest", default="docs/REFERENCE.md")`, not `action="append"`). It diffs the
  whole of `AGENTS.md`, so a per-destination run sees the *other* destination's removals too and
  reports them unmatched. G3 over a two-destination cut therefore needs either a repeatable
  `--dest`, or one run per destination with the pass condition being **every removed line matched in
  at least one run** — a union, which no current invocation computes.
- [`util/ad-hoc/2026-08-28_p5_cut.py`](../util/ad-hoc/2026-08-28_p5_cut.py) hard-codes
  `DEST = "docs/REFERENCE.md"` as a module constant, threaded through the relocation loop, the TOC
  maintenance and the waiver's heading verification. It has **no per-section destination**.

Neither is hard to fix, and neither is fixed here — execution is blocked on other prerequisites
anyway, and building it before the destination decision is final would be speculative. But it must
be done *before* the canopy cut, and the union pass-condition matters: running G3 twice and
accepting "both passed" is wrong, because each run legitimately reports the other's lines as
unmatched. **The safe form is one G3 run per destination with the results unioned, or a repeatable
`--dest`; anything else either fails spuriously or passes without checking.**

cascor is unaffected — it is a single-destination cut into a `docs/REFERENCE.md` that must first be
created.

## 7. Decisions — ALL RESOLVED (owner, 2026-08-29)

1. **canopy's destination — TWO SEQUENTIAL SINGLE-DESTINATION PRs.** The split agreed with the
   owning session is by *subject*, not convenience: documentation-about-documentation goes to
   `docs/DOCUMENTATION_OVERVIEW.md`, which is literally the file whose subject that is; everything
   else reference-shaped goes to a new `docs/AGENTS_REFERENCE.md`; `REFERENCE.md` gains one row per
   destination and keeps its index role.

   **Delivered as two PRs in sequence, each targeting one destination** — PR 1 (doc-about-doc), then
   PR 2 branched from the new `main` (the remainder). This is what dissolves §6d: each PR is a
   single-destination relocation, so `relocation_check.py` runs cleanly on it as-is. No repeatable
   `--dest`, no union pass-condition, and therefore no opportunity for someone to hit a spurious
   per-destination failure and "fix" it by relaxing G3. It also halves each diff.

   Note the destination scaffold: the relocate script reads the destination file and requires
   exactly one `--insert-before` heading, so `AGENTS_REFERENCE.md` must be created with a header, a
   ToC and at least one terminal section **before** the first relocation into it.

   Still to do in the same arc: correct the inherited `_README` line in canopy's
   `conf/memory_budget.json`, which asserts something false about that repo — a stale pointer inside
   the config for the gate whose purpose is to prevent exactly that.

2. **cascor — TIER A, nine sections** (~35,786 chars; §4.2), landing `AGENTS.md` near 37,500. Pure
   lookup-reference; nothing operational moves. Its `docs/REFERENCE.md` must be created first, and
   its relationship to the existing `docs/INDEX.md` settled at that point — INDEX.md is 5,262 chars
   and is the natural place to add the one pointer row.

3. **cascor-worker and deploy — CUT BOTH.** They are the same shape as the three that shipped
   2026-08-28: an existing `docs/REFERENCE.md` content file, a single destination, and the proven
   driver. See §7.1 for the section sets and the exclusion rule applied to them.

4. **The canopy hazards block — a SEPARATE PR, before the cut.** Promote the resident set first,
   then cut around it; the cut cannot relocate something already pinned as resident. Bullet 1 is new
   text drafted from the source comment, for the owning session to review before it lands.

5. ~~**Sequencing with `canopy e2e`**~~ — **RESOLVED, see §2.1.** Waiting on its teardown ping only.

### 7.1 worker and deploy — sections, and the exclusion rule

Applied here for the first time and worth stating as a rule: **exclude from a cut any section
carrying a score ≥ 2 candidate from the hazard triage.** A relocation turns a resident fact into a
reference someone must know to look up, so a section holding a silent-failure directive should not
move at all — which is cheaper than splitting the section and loses only its reference value.

| Repo | Relocate | Excluded, and why |
|---|---|---|
| cascor-worker | Directory Layout 3,782 · Application Architecture 1,757 · Public API 2,179 · Test Details 2,085 · CLI Reference 1,665 (**11,468**) | `## CI/CD` — the no-`branches:`-filter fact (only check on a stacked PR, cannot block the merge). `## Constants` — *"a mismatch **silently** breaks worker connectivity"*. |
| deploy | Environment Variables 5,809 · Directory Layout 3,983 · Security Architecture 2,428 · Testing 1,802 · Documentation 675 (**14,697**) | `## CI/CD Pipeline` — the same no-filter fact, plus the base-branch-guard warning that renaming the job makes `main` unmergeable. |

Score-1 hits inside the retained sets were inspected and are false positives: worker L319 matches
**"WARNING" as a log level** in a flag table; deploy L580 is a test-markers table.

Both destinations already exist and carry 0% overlapping content (measured), so the two name
collisions — worker's `CLI Reference`, deploy's `Environment Variables` — are resolved with distinct
destination titles rather than by skipping the sections.

## 8. Urgency — neither is close to firing

| Repo | AGENTS.md | ceiling | headroom | rate/day | implied days |
|---|---:|---:|---:|---:|---:|
| juniper-canopy | 95,133 | 97,133 | 2,000 | 66 (30 d) | ~30 |
| juniper-cascor | 71,098 | 80,707 | 9,609 | **711 (30 d) / 142 (14 d)** | **~13 or ~68** |

**A "days remaining" figure for cascor is not trustworthy, and an earlier draft of this note stated
~47 days as though it were.** Corrected after a peer read a different number from the same helper.
cascor's rate is entirely window-dependent — 711/day over 30 days (14 commits, 9 growing, largest
**9,609**), 142/day over 14 days (one growing commit). An earlier 14-day read the same day gave 205.
The measurement is not wrong; the *summary statistic* is, because the growth is bursty and n is 1–14.

**State the risk structurally instead.** cascor's headroom is 9,609 and its largest observed single
commit is 9,609 — identical, because the slack rule sized the ceiling from exactly that commit. So:
**one commit of a size cascor has already produced once exhausts its entire headroom.** That is the
real exposure, it does not depend on a window, and it is a stronger argument for cutting cascor than
any days figure. Re-measure before scheduling; do not schedule from this table.

**The ordering correction still stands, with a narrower claim.** Plan §P5 orders by rate and names
cascor "start here" — that was the input for the **port**. For the **cut** the input is
`headroom ÷ rate`. That reordering is right in principle; what it does *not* support is the specific
conclusion "cascor is the least urgent repo in the fleet", which the 30-day window contradicts.

## 9. Tooling produced by this prep (juniper-ml, `util/ad-hoc/`)

| Script | Purpose |
|---|---|
| `2026-08-28_p5_cut_section_sizes.py` | Per-section char inventory of any repo's `AGENTS.md`; CommonMark-correct fence handling |
| `2026-08-28_p5_cut_overlap_probe.py` | `AGENTS.md` vs its own `docs/REFERENCE.md`, per section |
| `2026-08-28_p5_docs_tree_overlap.py` | `AGENTS.md` vs the whole `docs/` tree, with best-matching document |
| `2026-08-28_p5_cut.py` | The cut driver, six modes — `prepare`, `ship`, `waive`, `bump-date`, `raise-ceiling`, `status` (read-only): worktree + dup-guard, verbatim relocation, TOC, date bump, ceiling with re-measured slack, controls, signed PR |
| `2026-08-28_p5_worktree_cleanup.py` | Gated arc cleanup: PR MERGED read live, unoccupied via `/proc/<pid>/cwd`, clean, no unrecognised ignored payload (size + newest mtime printed per entry) |
| `2026-08-28_hazard_triage.py` | Ranks `AGENTS.md` directives that must stay resident; positive-controlled against juniper-ml's own Hazards block |
| `2026-08-28_resident_gap_scan.py` | The complementary pass — hazard-shaped directives in SOURCE that are resident nowhere |
