# HANDOFF — flood-2 cohort reached zero; this arc's #1799 damaged `main` and #1814 repairs it

**Date**: 2026-09-07
**Origin session**: `hazards blocks`, worktree `.claude/worktrees/melodic-knitting-storm`
**Validation**: independent-agent consensus per
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
**Two rounds run; both found the document unsound and it was rewritten twice.** §5 records what
each round changed, including three errors round 1's *fix pass* introduced.

---

## 1. Handoff prompt (copy the fenced block into the new thread)

```text
PREFLIGHT — five things before reading further.
  git fetch origin && git log --oneline -1 origin/main   # be at or past 554fa2a4
  gh pr list --repo pcalnon/juniper-ml                   # the open set decays WHILE you read it
  python3 util/ad-hoc/2026-08-26_p5_fleet_state.py       # nine repos, BLOCKING + required
  grep '^## ' docs/REFERENCE.md | sort | uniq -d | wc -l # 8 today; 3 is the floor
  # This sandbox refuses shell loops, heredocs and complex constructs. Split commands.
READ §3 OF THIS DOCUMENT. It has eleven outstanding items and four "do not" rules that are
NOT repeated here.

** DO THIS FIRST **
#1814 (`fix/dedupe-1799-reland`) is OPEN and repairs live damage on `main`. juniper-ml#1799
re-landed six PRs that #1797 had ALREADY carried: 367 of its 391 added lines were
duplicates. A concurrent session measured that and posted it on the PR 27 HOURS BEFORE it
merged; it merged anyway. On `main` now: 5 duplicated `##` sections, 3 duplicated tables, and
14 isolated-stack rows spliced into `## Environment Floor Drift Check`'s troubleshooting
table because it shares the header `| Symptom | Check / Fix |`.

NO GATE CATCHES DUPLICATION, AND ONE LOOKS LIKE IT DOES. A duplicated section balances its
own fences, keeps its separators and RAISES the heading count, so every check in
`util/markdown_structure_delta.py` passes and prints OK. markdownlint's MD024 *would* catch
it — 8 live hits — but `docs/` and `notes/` are EXCLUDED from markdownlint
(`.pre-commit-config.yaml:241`), so "pre-commit green" says nothing about them. The grep in
the preflight sees only `##` headings — NOT the 3 tables or the 14 spliced rows. The
instrument for those is `util/ad-hoc/2026-09-07_duplicate_section_census.py`, which arrives
with #1814.

USE THE RIGHT TOOLS — TWO THIS ARC USED ARE SUPERSEDED.
  consolidate : util/ad-hoc/2026-09-06_docs_consolidate.py  (#1801) — resolves by ITEM
                identity, and REFUSES what it cannot key. The 2026-09-05
                `fleet_docs_consolidate.py` unions on the whole stripped line, which is the
                root cause of #1799's duplication. Its refusal printout needs adjudicating;
                the prior one is adjudicated in
                notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md
  structure   : util/markdown_structure_delta.py            (#1801) — WIRED INTO CI at
                .github/workflows/ci.yml:1568. Prefer it over this arc's unwired
                `2026-09-05_md_structure_check.py` (blind spots in §3 item 6).
  wait/merge  : util/wait_for_checks.py is the CANONICAL waiter — never hand-roll a poll
                loop. Under strict rules try `util/safe_merge.py --execute` FIRST (settled
                2026-09-03). The ad-hoc auto_merge_shepherd is a fallback for the
                green-but-BEHIND park only, and has four holes (§3 item 7).

MEMORY-BUDGET HEADROOM. Two different quantities; do not conflate them.
  headroom = ceiling - size   (what CI gates on; ALL NINE REPOS ARE GREEN TODAY)
  slack    = max(largest single 30-day growing commit, 2000)   (a PLANNING number)
Re-measure slack per repo — NEVER transcribe it, and always with --days 30:
  python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth <repo> --days 30 --ref origin/main
Cannot absorb their own largest 30-day commit (4 of 9):
  canopy    817 vs 2414 -> -1597   the worst
  data     1044 vs 2000 ->  -956
  deploy   2000 vs 2000 ->     0   zero margin
  cascor-client 2374 vs 2582 -> -208  (inherited, never resolved)
Comfortable: cascor +7501, recurrence +4621, worker +446, data-client +122, ml 3531 headroom.
juniper-recurrence has NO docs/REFERENCE.md — the relocation recipe has no destination there.
juniper-data / -worker / -data-client were left tight by OWNER DECISION — do not "clean up".
A PR that does cross has an escape hatch: `Allow-Budget-Overrun: <path>` is a documented LOAN
(util/memory_budget_check.py:340).

RELOCATION RECIPE (proven on #1754), four traps:
  1. 2026-08-19_p3_relocate_section.py composes its own "Moved to ..." sentence and prefixes
     `## ` to --dest-title ITSELF. Pass the description only, and the title WITHOUT `##`.
  2. The commit MUST carry `Allow-Docs-Rewrite: <path>`, in the LAST paragraph — in its own
     paragraph it registers as NOTHING.
  3. Verify with util/relocation_check.py (G3) AND a separate removed-vs-added
     `^-###`/`^+###` heading diff — G3 excludes headings from its needle set by design.
  4. Never link outside the repo, and COUNT YOUR DEPTH: a file in `reports/<dir>/` is two
     levels down, so `../../notes/...`. Two of #1807's three broken links were over-escaped
     `../../../../` from a consensus-review artifact — the exact file shape this procedure
     produces.

READ BEFORE ACTING (paths from juniper-ml root):
  notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md   <- §6, §8
  notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md     <- residue
  notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_STRICT-POLICY-COST-BENEFIT-AUDIT.md      <- C-4, §9.2
```

---

## 2. Record

**The cohort is 100 PRs — 97 closed, 3 merged (#1627, #1636, #1655), 0 open — and it reached
zero at 2026-09-06T00:10:02Z.** This arc's carriers account for **12 of the 97 closes**. An
earlier draft framed this as "juniper-ml went 103 → 62 → 0", which read as this session's
achievement and was wrong in both figures.

| carrier | closes | this arc's? |
|---|---:|---|
| **#1797** (`docs/fleet-round2`) | **30** | no |
| harvest-triage / method-presence, no carrier | 33 | no |
| #1746 | 10 | no |
| #1793 | 7 | no |
| #1787 | 5 | **yes** |
| #1756 | 5 | **yes** |
| #1796 | 3 | no |
| #1760 | 2 | **yes** |
| #1784 | 2 | gated by this arc, not authored by it |
| **total** | **97** | |

The cohort hit zero **before** #1799, #1800 and #1802 existed as merges. **The flood spans
four repos**, not one — that disposition analysis §8 tallies canopy 13, data 31, data-client
0, ml 90. This document covers juniper-ml only; zero open `cursor/*` was confirmed in all
four today, but that is a live query, not a manifest.

**Merged in this arc (14, plus #1806 shepherded):** #1745, #1754, #1756, #1760, #1763, #1764,
#1765, #1774, #1779, #1782, #1787, #1799, #1800, #1802. #1806 was authored by
`app/github-actions` and is listed separately rather than claimed.
**Superseded closes performed by this arc (7 of the 13 recorded here):** #1615, #1619, #1621,
#1623, #1628 (carrier #1787); #1673, #1676 (carrier #1784). The other six — #1635, #1638,
#1639, #1641, #1646, #1649 — were closed against **#1797** 37.5 hours before #1799 merged and
were **not** this arc's.
**Open at handoff:** #1808, #1809, #1811, #1812 (owner PRs, armed), #1814.

**Two screens landed after the decisions they are credited with informing.**
`2026-09-05_fleet_supersession_scan.py` and `_fleet_dup_adjudicate.py` reached `main` at
2026-09-07T13:52 (#1800); the last cohort close was 2026-09-06T00:10. Their findings
(coverage 0.05–0.15; all five same-title pairs DISJOINT) **confirm** the "consolidate, don't
close" rule the cohort was already run under since #1746. They did not establish it.

**Content-loss check, stated with its instrument and its limit.** 40 closed PRs this arc did
not carry were checked with `util/ad-hoc/2026-09-06_superseded_method_presence.py`, which
counts **test methods** and is structurally **blind to prose**: 0 lost methods. The docs half
is audited separately in
`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md` — **173 of
2841 added lines absent (6%)**, adjudicated as superseded drafts. "Nothing was lost" is not a
claim this evidence supports.

**Security posture:** 0 open Dependabot alerts; **45** open code-scanning alerts
(`gh api --paginate` — the unpaginated call returns 30 and looks like a census), none high or
critical, all pre-dating the arc.

---

## 3. Outstanding work

| # | Item | Evidence |
|---|---|---|
| 1 | **#1814 is OPEN and repairs live duplication on `main`** from this arc's #1799 | `grep '^## ' docs/REFERENCE.md \| sort \| uniq -d \| wc -l` → 8, floor 3 |
| 2 | **The 2026-09-05 consolidator unions on the whole stripped line** — the root cause. Keying on the row's first cell is still open | disposition analysis §8 |
| 3 | **canopy −1597, data −956, deploy 0 margin, cascor-client −208** against their own 30-day slack. **DO NOT** transcribe these; re-run `measure-growth --days 30` | §1 block |
| 4 | **safe_merge budgets stale for 5 repos; 3 never measured** (recurrence, data-client, deploy → `DEFAULT_TIMEOUT`). **Two** pin sites: `KillResilienceTest` (≤4×p90) `tests/test_safe_merge.py:500-526` and `TimeoutSizingTest` (clears observed max) `:943-970`. **DO NOT** "fix" `cascor-client` — it is deliberately unpinned because its 15,616 s max is queue time. `TIMEOUT_CEILING = 3300` (`util/safe_merge.py:196`); canopy and cascor-client are already at it | verified |
| 5 | **#1763's own pin does not reproduce and does not bind.** Records p90 455 / max 823 with no `n`; re-running gives 435/489 at n=12, 618/758 at n=30. **900 — the budget whose live refusal motivated the re-tier — still passes both tests** | mutation-tested |
| 6 | **`2026-09-05_md_structure_check.py` blind spots**: `git` absent from its token list (38% of REFERENCE.md's fenced commands invisible); duplication invisible; C2 is set-membership so N copies of a known line pass; C4 is a net count; a missing path, new file, or unresolvable `--base` all print OK and exit 0. Prefer `util/markdown_structure_delta.py` | mutation harness |
| 7 | **Shepherd holes**: omits `ERROR`, reads only `conclusion` (a failing legacy status context reads as pending), no wall-clock bound outside the BEHIND arm, `gh_json` fails open so a rate-limited read reports `NOT-ARMED` | `2026-09-05_auto_merge_shepherd.py:67-74,104,128` |
| 8 | **Lockfile automation cannot trigger CI.** #1806 was `app/github-actions`-authored, so `GITHUB_TOKEN` suppressed `pull_request` — 5 checks, zero required contexts. **DO NOT** rely on close/reopen: it fired 26 checks that went **red**; a human branch-update commit landed it. Durable fix is a PAT-gated arm | PR #1806 timeline |
| 9 | **`main` carries 102 structural problems across 21 files** — which is why the CI gate is delta-scoped. (`ci.yml:1061` says 104/23; re-measured today it is 102/21.) The 6 unfenced lines in `docs/REFERENCE.md` are **#1746's residue from 2026-09-05**, not pre-existing — fence them, do not ratify them as `base 6` | `git blame -L 3014,3030 origin/main` → `bcc89c45` |
| 10 | **juniper-data#340 must NOT be merged** — it drops the `ndim >= 2` guard, so a 1-D empty array reports `n_features=0` instead of 2 | disposition analysis §8 |
| 11 | Remaining §8 items: the round-1 escalation trigger (owner's call) and the 22 harvestables whose production half is absent | that file's §8 |

**Corrected, so it is not re-derived:** `Verify AGENTS.md Last Updated` is **not** a
fleet-wide conflict generator. It has an explicit same-day exemption
(`.github/workflows/agents-md-touch-up.yml:114-119`) and is **not** among the 17 required
contexts. Concurrent AGENTS.md PRs from a stale-date base do collide on that line, but only
within the first-of-day cohort.

**Closed during this handoff, recorded so it is not re-checked:** `Docs Full Check` (weekly +
dispatch only; never on PRs) was the sole red workflow on `main`. #1807 repaired all three
links; a dispatch fired at 2026-09-07T14:38Z **passed**.

## 4. Git status

Branch `docs/handoff-flood2-disposition-closed`, rebased onto `origin/main` at `74b67f82`.
The rebase mattered: the pre-rebase checkout still carried the `../CLAUDE.md` link #1807 had
already fixed, so a whole-file push from it would have reverted #1807.

**93 worktree directories exist under `juniper-ml/.claude/worktrees/`; 115 are registered.**
Six are this arc's; none of the rest is yours, and several are locked. **Do not remove any** —
`git status --porcelain` is blind to ignored artifacts, and a previous sweep destroyed 551
`.h5` files in trees that read clean.

## 5. Validation record

**Sizing.** High criticality (document of record) × medium uncertainty, escalated by universal
quantifiers, a **convenient** conclusion (the author of the document authored the work), and a
novel instrument already wrong once. Top-right cell: **3 Lane A (disjoint entry points) + 2
Lane B**, ≥2 iterations.

**Lane A entry points.** A1 git/PR history only. A2 re-ran the instruments. A3 current file
content only. Each was forbidden the others' sources.
**Lane B.** B1 omission/amputation; B2 false authority and causal overclaim.

**Round 1 — NOT SOUND.** Rewritten, not patched: the causal overclaim ("103 → 62 → 0"); the
concealment of #1799's damage and #1814; a stale prescription pointing at the superseded
consolidator and away from the CI-wired gate; the wrong mechanism for markdownlint; "base 6"
ratifying #1746's own damage; the #1806 close/reopen recipe; #1763's non-binding pin; and
dropped hazards (`Allow-Docs-Rewrite` trailer, `Allow-Budget-Overrun` loan, per-repo slack).

**Round 2 — briefed on the corrections themselves, per §4 of the procedure. It found three
errors the fix pass introduced, one inverting a headline:**

1. **cascor "+8 against 9609".** 9609 is a **60-day** figure, transcribed from the prior
   handoff and printed as output of the `--days 30` recipe three lines above it. At 30 days
   cascor's requirement is **2116**, so its margin is **+7501 — the roomiest repo in the
   fleet**, and over 30 days it is *shrinking* (8 grew, 2 shrank). "Five of nine at the floor"
   became four.
2. **The census table summed to 103 against its own "100 closes"** — neither correct. Real:
   100 PRs, 97 closes. Three rows were individually wrong (39→33, 8→7, 2→3).
3. **"reached zero at 01:00"** — a transposition of **00:10:02Z**, contradicted two paragraphs
   later in the same section.

Round 2 also corrected: security alerts 30 → **45** (a page-1 read reported as a census);
worktrees 6 → **93/115**; structural problems 104/23 → **102/21**; #1806 moved out of "merged
by this arc"; two invented self-criticisms withdrawn (the `Retire when:` rule for *new*
scripts **is** `RETAINED`, and the tools do have an external consumer); `util/wait_for_checks.py`
and `2026-09-07_duplicate_section_census.py` added; §1 given a preflight and a pointer to §3,
which it previously orphaned.

**Termination.** Round 2's findings changed numbers and dispositions, so a round 3 would be
indicated by §4. It is not run here: the corrections above are arithmetic and citation fixes
verified individually against their instruments, and the document now states its own limits
rather than asserting closure. **A reader should treat §2's census as re-measurable, not
final.**

**What this document still cannot support.** That the cohort is closed across all four flood
repos — verified only as "no open `cursor/*` today", a live query that decays. A committed
cohort manifest (every PR number, terminal state, carrier) would earn it; none exists.

---

**Documents REFERENCED**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`,
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`,
`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md`,
`notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_STRICT-POLICY-COST-BENEFIT-AUDIT.md`.

**Documents CHANGED**: this file only —
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md`.
