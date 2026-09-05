# Cursor-Fleet Flood #2 — Disposition Analysis of Record

**Project**: Juniper (ecosystem-wide)
**Author**: Paul Calnon
**Status**: Active — the flood is still running by owner decision
**Date**: 2026-09-05
**Applies to**: juniper-ml, juniper-data, juniper-canopy, juniper-data-client

---

## §0 What this document is

The disposition record for the **second** Cursor-fleet PR flood. The first is analysed in
[`JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md);
that arc built the machinery this one used. Read that first for the incident taxonomy and the
owner decision list; read this one for what round 2 actually found, and — most importantly — for
**§4, the register of claims that did not survive re-derivation**, which is the part with the
longest shelf life.

---

## §1 Scope, and how it differs from round 1

| | round 1 (2026-07-26) | round 2 (2026-09-04/05) |
|---|---|---|
| PRs | 134 over ~25 h | **~135 open at any moment**, still running |
| rate | ~5.4/h, peak 48 per 6-h bucket | **~8.3/h sustained**, peak 36 in one clock hour |
| repos | juniper-ml only | **four**: ml, data, canopy, data-client |
| PR state | ready | **draft** — owner decision §4.5 of the round-1 analysis, working as intended |
| damage in the diffs | 20 test classes + 13 grafts lost in merge; 6 doc-union files not clean | **none found** (see §3) |
| outcome | 133 merged, 5 heal PRs needed | 13 merged, 10 consolidated + closed, rest open |

**The fleet is five automations, and the roster is readable in-repo** — contradicting round 1's
§1(b) conclusion that "all configuration lives on the Cursor dashboard; there is no in-repo
config". Any fleet PR's check list (`gh pr checks <N> | grep -i cursor`) enumerates them:
*Add test coverage*, *Generate docs*, *Find critical bugs*, *Find vulnerabilities*, *Assign PR
reviewers*, each with its own `cursor.com/agents/bc-…` id. Four generators plus one
reviewer-assigner. This answers the round-1 §4 decision-5 probe "confirm the automation count
(3 vs 4)": it is **5**. The *configuration* (cadence, concurrency cap, file scopes, PR budget)
remains dashboard-only.

**The backlog refills.** Over this session 13 PRs were merged and 10 closed, and the open-draft
count returned to roughly where it started (133 → 134). Draining is not convergent while the
source runs; that is an accepted owner decision, not an oversight.

---

## §2 Quality — measured, not assumed

Three independent Lane A passes (per
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md))
plus two opposing Lane B briefs.

- **Tests are behavioural, not decoration.** A 34-mutation battery across 7 PRs killed **30
  (88%)**. Stratified 22-PR sample: 15 SOLID / 6 WEAK / 1 BROKEN. Consistent blind spot:
  `startswith` → substring mutations survive (no negative case supplied).
- **Docs are well-grounded but decay fast.** 313 assertions checked across 28 docs PRs:
  **10.2% false**, and **every false claim was a stale snapshot** — true when the branch was cut,
  false by the time it was read. Nothing was fabricated. 11 of 28 sampled PRs had zero refutations.
- **~24 of 49 `test(...)` PRs also rewrite production code** (behaviour-preserving extract-method
  to create a testable seam). They are not test-only PRs and must not be reviewed as such.
- **CI never ran most of these suites.** The bot's files are not black-formatted → `Pre-commit`
  fails → `ci.yml`'s `tests: needs: [pre-commit]` → `Regression Tests` reports *skipping*. So
  "wired into `ci.yml`" is not evidence a suite ever executed. The wiring itself is not evidence
  of diligence either: `tests/test_ci_test_wiring_drift.py` mechanically compels it.

---

## §3 Deterministic triage — and the vacuous half of it

`util/fleet_triage/predict_merge.py --batch` over all four repos:

| repo | PRs | MERGE-CLEAN | NEEDS-UPDATE | DAMAGED | CONFLICT |
|---|---|---|---|---|---|
| juniper-ml | 99 | 3 | 29 | 24 | 43 |
| juniper-data | 30 | 0 | 13 | 6 *(all false — see below)* | 11 |
| juniper-canopy | 10 | 1 | 4 | 4 | 0 |
| juniper-data-client | 2 | 0 | 2 | 0 | 0 |

**`DAMAGED-FIX-FIRST` is almost entirely cosmetic**: on juniper-ml, 20 of 24 are `black`-only and
the other 4 are extract-method refactors the AST screen flags `weakened` by design.

**The trap, and the reason this section exists.** Reading that table as "0 docs deletions across
all 99" is **wrong**. Both compositional-loss screens hard-code `{"status": "skip"}` when the merge
does not apply (`predict_merge.py:359`), so on a `CONFLICT` PR they answer *nothing*:

| gate | pass | fail | **skip** |
|---|---|---|---|
| `ast_symbol_screen` | 52 | 4 | **43** |
| `docs_additions_only` | 56 | 0 | **43** |

All 43 skips are exactly the `CONFLICT` set — i.e. the PRs whose damage would live in the conflict
*resolution*, which is where round 1's damage came from. The honest statement is **"0 across the
56 that were screened; 43 unscreened."** This is the resident vacuous-pass shape: *a correct
predicate over an incomplete site enumeration*. Fixed in juniper-ml#1740 (`screen_coverage()` now
reports the honest denominator and names the unscreened PRs).

---

## §4 Claims that did not survive re-derivation

**This is the most reusable part of this document.** Every one of these was stated confidently,
by a capable reader, before being checked. The deterministic instrument held up under scrutiny in
every case; the *narrative* claims about individual PRs did not.

| claim | status | what the artifact says |
|---|---|---|
| `predict_merge.py` exits 0 when `gh` fails | **FALSE** | Exits **2**. The 0 came from a `nohup … &` wrapper reporting the outer shell. |
| "0 docs deletions across all 99" | **OVER-STATED** | 0 across **56**; 43 unscreened (§3). |
| "all 4 AST hits are `func:main`" | **FALSE** | #1676's is `func:_png_dims`. |
| juniper-ml #1721 is a hollow test | **FALSE** | 19 tests over a real predicate + real repo files, with **two** anti-vacuous controls. Closing it would have destroyed good work. |
| juniper-ml #1699's module is not on main | **FALSE** | `util/ad-hoc/2026-09-04_soak_handoff_consensus_checks.py` is present; its base was retargeted to `main`. |
| "the conflicts are caused by version churn" | **HALF TRUE** | True for ~21 of 43. 22 of 43 have a conflicted file with no version header at all. Confirmed live: the consolidation resolver halted **four** times, every halt a real two-sided edit. |
| juniper-data #357 reverts the SEC look-ahead-leak fix, cuts `EQUITIES_FEATURE_COLUMNS` 16→10 | **FABRICATED** | main's `equities/generator.py` is **610** lines (not 753); #357's head is **625** — larger. `reindex(...).ffill()` is present in **both** (main:430, PR:445) — it *is* main's code. `dropna(subset=["filed"])`, `actions=True`, `days_since_report`, `EQUITIES_FEATURE_COLUMNS` appear in **neither** file. |
| two `conf/soak_probes.json` anchors are missing from `REFERENCE.md` | **FALSE** | Both headings exist (`REFERENCE.md:765`, `:409`). The *instrument* was wrong: its slugifier collapsed whitespace runs (GitHub does not → `--`) and stripped underscores (GitHub keeps them). Fixed by copying `util/soak_ledger.py:_slugs` verbatim. |

**The lesson, stated once:** for machine-generated PRs, a claim about *one PR* is worth nothing
until re-derived from the file. Two of the eight above came from adversarial agents that were
otherwise excellent and produced findings that were both real and load-bearing. Mixed reliability
within one report is the norm; check each claim, not each reporter.

---

## §5 Confirmed findings, and what was done with them

| finding | status | carried by |
|---|---|---|
| `compare_baseline` verdict-ordering fail-open (ml #1626) | **CONFIRMED** | Test only — `tests/test_compare_baseline.py`, ml#1742. **#1626's patch was NOT adopted.** |
| `n_features` hardcodes 2 on an empty train partition | **CONFIRMED** | juniper-data#365 |
| juniper-data #330 re-opens the DoS byte cap | **CONFIRMED** | Close #330; #336 is the better implementation |
| `predict_merge` scores a MISSING hook as a gate FAILURE | **CONFIRMED** | ml#1740 |
| 8 tests invisible to `python3 <file>` (already on main via #1683) | **CONFIRMED** | ml#1740 |
| `DOCUMENTATION_OVERVIEW.md` carries duplicated index rows | **CONFIRMED** | ml#1746 collapses 4 rows → 2 |

### §5.1 The #1626 finding is the sharpest one

`tests/test_compare_baseline.py` already had a guard named `test_waiver_does_not_mask_a_refusal`.
**It could not detect the regression its name promises**: it passes ONE suite whose identity is
unknown, which yields no scenario result, so an implementation that asks "did work move?" before
consulting the refusal reasons still finds nothing moved and falls through to `REFUSED`.

It takes **two** suites — one with moved work, one that refuses — before a waiver can wrongly win.
Under #1626's ordering the two new sibling tests go red and **all 25 pre-existing tests stay
green**. Because #1626 is `CONFLICT`, every mechanical gate skipped it; a human reading the diff
was the only thing that caught it.

### §5.2 `predict_merge` was juniper-ml-shaped

`PRECOMMIT_HOOKS` was hardcoded to `black/isort/flake8/mypy/check-ast`. juniper-data lints with
**ruff** and defines none of them, so pre-commit answered ``No hook with id `black` `` and the
runner scored that as a gate FAILURE — 6 false `DAMAGED` verdicts. The mirror risk was worse:
`ruff` was in **no** repo's battery, so a juniper-data PR could read `MERGE-CLEAN` while CI failed
it. `tests/test_predict_merge.py` had zero `ruff` references — nothing covered the eight non-ml
repos.

---

## §6 The disposition, and why merging one at a time does not work

`juniper-ml-rules` sets `strict_required_status_checks_policy: true`, **17 required contexts**,
`allow_update_branch: false`. 87 of 99 juniper-ml PRs touch `docs/REFERENCE.md`. So every merge
makes the rest `BEHIND`, each resync is a full 17-check battery, and — the part that makes it
**degrade rather than merely crawl** — each landed merge advances the file's `**Version:**` line,
which every sibling also rewrites. The natural experiment ran itself mid-flood:

- 34/34 docs PRs based on doc-version **0.6.15** → CONFLICTING
- 0/12 docs PRs based on **0.6.22** → MERGEABLE

One merge bumped seven versions and converted the whole clean cohort at once. **#1707 went
`DIRTY` mid-train** and demonstrated it live.

**What was done:**

1. **Merged individually (13):** the provably-clean set — screens actually *ran* (not skipped),
   all lints pass, no code-file collision with a sibling, CI green. Computed by
   `util/ad-hoc/2026-09-05_fleet_provably_clean.py`: 15 of 99, minus #1701/#1705 which both add a
   `## Pointer-Follow Soak` H2 (neither a superset — both deferred to harvest).
2. **Consolidated (10 → 1):** juniper-ml#1746. Verified in **both** directions — every added
   `.md` line present, and `juniper-docs-additions-check` clean against `main`. The ten originals
   were then closed with comments naming #1746.
3. **Harvested, not merged:** findings re-derived and reimplemented against current `main`
   (§5), because the bot branches are stale re-applications whose risk is in what they take away.

**Closing is not destructive.** GitHub retains a closed PR's diff indefinitely, so closing costs
the *merge path*, not the content. That is what makes harvest-then-close safe.

---

## §7 Tooling added

All under `util/ad-hoc/` per the script-placement rule (they analyse or modify repo content, so
`/tmp/` is prohibited):

- `2026-09-04_fleet_flood2_census.py` — contention histogram + docs/code split
- `2026-09-05_fleet_provably_clean.py` — the 6-gate provably-clean filter, treating `skip` as
  *unscreened*, never as pass
- `2026-09-05_fleet_anchor_collision.py` — heading/anchor collisions + `conf/soak_probes.json`
  pointer validation, slug rule copied verbatim from `util/soak_ledger.py:_slugs`
- `2026-09-05_fleet_merge_train.py` — serial merge driver; re-reads PR state from `gh` after every
  attempt because `util/safe_merge.py` can exit 0 without merging
- `2026-09-05_fleet_docs_consolidate.py` — fail-closed N-branch consolidator + two-direction verify
- `2026-09-05_fleet_docs_reinsert.py` — anchored re-insertion of deferred lines
- `2026-09-05_fleet_close_superseded.py` — refuses to close unless the carrying PR is MERGED

---

## §8 Open items

- **~134 drafts remain** across the four repos and the count is stable rather than falling.
- **Harvest not yet done:** juniper-data #336 (csv_import truncation + cache key) and #357 (symbol
  cap before cache hash); four juniper-canopy findings (X7 slice-1a gate soundness, F-CANOPY-042
  bounds-sync, -046 rebuild consumer, -047 PNG export); juniper-data-client NPZ_SPLITS val; and the
  `## Pointer-Follow Soak` pair (#1701 / #1705, plus #1621 / #1660 in the wider 4-way cluster).
- **Close #330** (superseded by #336 **and** it re-opens the DoS byte cap).
- **`startswith` blind spot** in the fleet's test corpus — no negative case where a substring match
  would differ.
- **Round-1 §4 decision 6** (advisory → strict → draft-only/integration-branch → full mediation)
  pre-authorised escalation "if damage recurs". Round 2 recurred faster but produced **no damage in
  the diffs**, so the escalation trigger is arguably unmet. Owner's call; the fleet runs on.

---

## §9 Files changed by this arc

**Merged:** juniper-ml #1627, #1655, #1702 (individually); #1746 (the ten-PR docs consolidation).
**Opened:** juniper-ml #1740 (`util/fleet_triage/predict_merge.py`, `tests/test_predict_merge.py`,
`tests/test_make_baseline.py`, `tests/test_read_run_metrics.py`, three `util/ad-hoc/` scripts);
juniper-ml #1742 (`tests/test_compare_baseline.py`, two `util/ad-hoc/` scripts);
juniper-data #365 (`juniper_data/core/meta.py`, `juniper_data/tests/unit/test_meta_dispatch.py`).
**Closed as superseded:** juniper-ml #1707, #1709, #1711, #1715, #1716, #1718, #1720, #1724,
#1726, #1727.
**Created:** this file,
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`.
