# HANDOFF — P5 step e COMPLETE fleet-wide; Hazards blocks in all 9; records-of-truth still stale

**Date**: 2026-08-30
**Origin session**: `p5 memory`, worktree `.claude/worktrees/mighty-greeting-mochi`
**Validation**: three adversarial agents (numeric / procedure-usability / omission), each prompted to
refute. **37 findings across the three lenses, all applied.** See §4 — the P0s were mine and they were real.

---

## Handoff prompt (copy the fenced block into the new thread)

```text
Continue the Juniper shared-session-memory arc, plan §P5. Step e (the cut) is DONE in all 9
governed repos — do not re-plan it. What remains is stale records, four owner-taken decisions,
and residual fixes.

DUP-GUARD FIRST, before any work: `gh pr list` on the target repo, then
`python3 util/ad-hoc/2026-08-28_p5_cut.py status <repo>` (its state file goes stale slower than
the PR list), then comment on juniper-ml#1326 naming your branch. Two sessions once shipped
duplicate PRs 14 minutes after a clean dup-guard read.

READ FIRST (paths from juniper-ml root):
  notes/JUNIPER_2026-08-28_JUNIPER-ECOSYSTEM_P5-CUT-CANOPY-CASCOR-PREP.md   <- what was measured
  notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md  §P5
  gh issue view 1326 --repo pcalnon/juniper-ml --comments               <- the live ledger

REMAINING WORK
1. BOTH RECORDS OF TRUTH ARE STALE and §4a forbids that. Plan §P5's banner still says "cut 3 of
   them, removing ~50,200 ... canopy and cascor still uncut"; issue #1326's title still says
   "5 cut ... canopy + cascor still blocked". Truth: 7 cut, net -135,118 chars. Rewrite both.
2. Land juniper-ml#1506 (scaffold support; one file, util/ad-hoc/2026-08-28_p5_cut.py). It is
   OPEN and BEHIND. ASK PAUL FOR MERGE APPROVAL FIRST — a handoff cannot carry it forward.
   On juniper-ml use `gh pr merge 1506 --squash --auto` + util/wait_for_checks.py; do NOT use
   safe_merge --no-auto-fallback (main merges every ~8-15 min against ~10 min CI, so the
   client-side race is unwinnable and it exits 0 having merged nothing).
3. Owner decisions C.1/C.2/C.5/C.6 were TAKEN on 2026-08-29/30 and are UNSTARTED work, not
   settled positions — read #1326 comment 5467340380 for their text before assuming otherwise.
4. HEADROOM IS THE URGENT RISK, not size: juniper-data-client has 486 chars and cascor-worker
   783, against a BLOCKING required gate. One added paragraph in either FAILS CI. Check with
   `python3 util/ad-hoc/2026-08-26_p5_fleet_state.py` before editing any AGENTS.md.
5. Residual fixes, each a one-file change: canopy docs/REFERENCE.md never got the
   AGENTS_REFERENCE.md row prep-note §7.1 promised; canopy AND recurrence conf/memory_budget.json
   still assert "docs/REFERENCE.md ... is the migration DESTINATION", which is false in both.
6. Deeper cuts the Hazards blocks unlocked (ASK PAUL; do not start): cascor `## CI/CD Pipelines`
   +`## Middleware Stack`, worker `## Constants`, data-client `## Exception Hierarchy`.

KEY CONTEXT — do not re-derive
- Promote hazards BEFORE cutting. Only canopy did; the other six were cut first and relied on the
  exclusion rule instead (see §3). Never relocate a section holding a SILENT-failure directive.
- relocation_check.py takes ONE --dest, so every cut is single-destination. Do not "fix" a
  per-destination failure by relaxing G3 (G3 = the relocation-completeness gate,
  util/relocation_check.py).
- G3 does not examine headings; `unmatched=0` says nothing about heading survival.
- Every cut FAILS Sequence Safety [heading-deletion]; remedy is the `Allow-Docs-Rewrite: AGENTS.md`
  trailer. The docs-rewrite LABEL is WARN-only and does not unblock a merge.
- safe_merge prints the HEAD it merged, not the squash SHA, and can exit 0 without merging. Read
  `gh pr view <n> --json state,mergeCommit,autoMergeRequest`.
- Backticks inside a double-quoted shell arg are command substitution: `git commit -m` and
  `gh pr comment --body` silently DELETE the identifier and exit 0. Always -F / --body-file.
```

---

## 2. Record — what this session completed

All "now" figures are **live from `origin/main`** at handoff, i.e. **after** the Hazards blocks,
which added chars back. "before cut" is each repo at its ARC START, re-derived from the parent of
its first arc commit — **not** the seed in `memory_budget.json`, which is 176 chars stale for
canopy. canopy is the only repo whose Hazards block landed BEFORE its cut, so its pre-cut size was
97,723 while its arc start was 95,309.

| Repo | before cut | now | net | ceiling | headroom |
|---|---:|---:|---:|---:|---:|
| juniper-canopy | 95,309 | 48,915 | −46,394 | 51,329 | 2,414 |
| juniper-cascor | 72,188 | 50,696 | −21,492 | 58,189 | 7,493 |
| juniper-cascor-client | 34,695 | 16,599 | −18,096 | 18,414 | 1,815 |
| juniper-data | 43,493 | 25,732 | −17,761 | 26,965 | 1,233 |
| juniper-deploy | 34,569 | 21,841 | −12,728 | 23,074 | 1,233 |
| juniper-data-client | 28,369 | 17,118 | −11,251 | 17,604 | **486** |
| juniper-cascor-worker | 35,126 | 26,049 | −9,077 | 26,832 | **783** |
| juniper-recurrence | 11,578 | 13,259 | **+1,681** | 20,000 | 6,741 |
| **net** | | | **−135,118** | | |

recurrence took a **policy ceiling raise instead of a cut** (owner decision) and then gained a
Hazards block, so it is the only repo that grew.

**Merged squashes** — cuts: canopy `1a29ca4e`+`f7e0213e`, cascor `9820ebd6`, data `9f9c0b8c`,
worker `9abbe3cc`, deploy `4d2a66fa`, cascor-client `e19d7926`, data-client `e3a8ddb9`,
recurrence raise `315d014b`. Hazards blocks (**all 9**, was 1): canopy `c73e01e5`, cascor
`9c813ba5`, recurrence `201eb21c`, cascor-client `5d696a0d`, data `327ea1de`, data-client
`5cae837d`, worker `44358bf0`, deploy `4019d113`. juniper-ml tooling: `#1403`, `#1450`, `#1500`.

**Arc tooling** (`util/ad-hoc/`, all on `main`): `2026-08-28_p5_cut.py` (driver:
`prepare|ship|waive|bump-date|raise-ceiling|status`), `_p5_cut_section_sizes.py` (fence-aware
inventory), `_p5_cut_overlap_probe.py`, `_p5_docs_tree_overlap.py`, `_p5_worktree_cleanup.py`
(gated sweep, `--harvest`), `_hazard_triage.py`, `_resident_gap_scan.py`,
`2026-08-26_p5_fleet_state.py`, `_p5_promote_ready.py`, `_p5_advisory_invocation_probe.py`,
`2026-08-25_p5_port_memory_budget.py` (`measure-growth` **needs `--ref origin/main`**),
`_p5_port_verify.bash`, `2026-08-19_p3_relocate_section.py`, `util/relocation_check.py`.

## 3. Known gaps in this arc's own work

- **Six of seven repos were cut BEFORE their Hazards block** — only canopy followed the sequencing
  lesson the arc discovered. Mitigation differed: cascor/worker/deploy were protected by the
  **exclusion rule** (triage run pre-cut, hazard-bearing sections withheld); cascor-client/data/
  data-client predate the triage entirely and were **verified after the fact** — the CI/CD hits
  were false positives from the pointer text I wrote, and data-client's `## Exception Hierarchy`
  survived only because a destination name collision made the cut skip it. No hazard was
  relocated, but two of those three were luck.
- **`resident_gap_scan.py` has run on canopy only**, leaving 63 candidates untriaged there and
  8 repos never scanned. A Hazards block built from `hazard_triage.py` alone cannot contain a
  directive that was never in `AGENTS.md` — which is how canopy's strongest hazard was found.
- **juniper-ml's own `Memory Budget` required context has no `integration_id`** (the other eight
  pin `15368`), so it matches any app publishing that name — on the repo governing this arc's PRs.
  Repair is a ruleset write and needs an owner claim.
- **`MEMORY.md` is at 24,034 / 25,000 bytes.** Truncation is silent and drops the NEWEST rows, and
  `2026-08-19_memory_index_evict.py` is spent (`freed: 0` and exits clean). Compaction is
  owner-DEFERRED to a concurrent session; the margin is the risk, not the policy.
- **`Allow-Budget-Overrun` loans have no central ledger** — a loan is visible only in its trailer.

## 4. Validation findings applied

| Lens | Found | Most consequential |
|---|---:|---|
| numeric / SHA | 7 | canopy's "before" was the **seed** in `memory_budget.json` (95,133), 176 chars stale — the file measured 95,309 at arc start. Out of **111 claims checked**, all 17 SHAs, all 8 ceilings and all 4 section sizes verified clean |
| procedure + usability | 16 | The `AGENTS.md` column was **pre-Hazards while the ceilings were live**, so six of eight rows contradicted the document's own verification command — and the claim "every figure re-derived" was false for exactly that column |
| omission | 14 | Both records of truth (plan banner, tracker title) still say canopy and cascor are uncut; §4a forbids leaving status stale |

Also corrected: an unconditional `--execute` merge command that would have run an **unapproved**
merge using the shape known to fail on juniper-ml; a `grep p5-` verification that **cannot match**
`p5cut` and so printed "no arc worktrees" unconditionally (vacuous-pass); "zero arc worktrees
anywhere" (six exist under `.claude/worktrees/`); a 689-word prompt block against the ~500 rule;
and a follow-up list that flagged the **safest** repo (recurrence, 6,741) while omitting the two
nearest breach (data-client 486, worker 783).

## 5. Git status at handoff

- Branch `feat/p5cut-scaffold-support`, one signed commit, pushed, **PR #1506 OPEN and BEHIND**
  (one file: `util/ad-hoc/2026-08-28_p5_cut.py`). This handoff is committed on its own branch.
- Zero arc worktrees under `Juniper/worktrees/`. **Six remain under `.claude/worktrees/`**
  (session worktrees, outside the sweeper's hardcoded root) including this one, which is locked.
- Every governed primary is on `main`, clean, fast-forwarded onto its own merge commit.
- juniper-canopy and juniper-cascor were released to the `canopy e3e` session for F-CANOPY-039.
  A fourth canopy worktree (`fix--f039-topology-noop-suppression--…--f7e0213e`) is theirs, created
  off this arc's canopy squash. Three July canopy worktrees are older and belong to neither.
