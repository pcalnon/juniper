# HANDOFF — memory-budget headroom + resident-hazard arc CLOSED; two owner decisions open

**Date**: 2026-09-04
**Origin session**: `hazards blocks, stale RoT`, worktree `.claude/worktrees/zippy-questing-wilkinson`
**Validation**: independent-agent consensus per
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — see §5.

---

## Handoff prompt (copy the fenced block into the new thread)

```text
The P5 memory-budget arc and the resident-hazard triage are both CLOSED. Trackers juniper-ml#1326
and #1611 are closed; do not reopen either to "finish" them.

DUP-GUARD FIRST: `gh pr list --repo pcalnon/juniper-ml` and the same for any repo you touch.
Seven-plus sessions run concurrently and one shipped a duplicate PR 14 minutes after a clean
dup-guard read.

VERIFY YOUR STARTING STATE (all read-only):
  python3 util/ad-hoc/2026-08-26_p5_fleet_state.py
  python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-ml \
      --context 'Memory Budget' --status
  gh pr view 1682 --repo pcalnon/juniper-ml --json state,mergeCommit

Expect: nine repos BLOCKING+required, every headroom >= 1982; Memory Budget
integration_id=15368; ml#1682 MERGED (63ca9306). Nothing is in flight. If any of those three
reads differently, something changed after 2026-09-04T22:35Z — investigate before acting.

"HEADROOM BELOW REQUIRED SLACK" IS NOT A CI FAILURE. util/memory_budget_check.py fails only when
size exceeds ceiling_chars, or when ceiling_chars was RAISED without an Allow-Ceiling-Raise
trailer. It never reads "required slack" — that comes from the separate measure-growth PLANNING
tool and is used to size a ceiling, not to gate a PR. Every repo below is CI-green today. Do not
start an emergency relocation on these numbers.

READ BEFORE ACTING (paths from juniper-ml root):
  notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md   <- §7b, §7c
  notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md          <- §P5
  notes/JUNIPER_2026-08-28_JUNIPER-ECOSYSTEM_P5-CUT-CANOPY-CASCOR-PREP.md    <- §7.1 exclusion rule

TWO OWNER DECISIONS ARE OPEN. Neither is yours to take unilaterally.

1. THE MERGE TREADMILL IS REAL; MY PROPOSED FIX FOR IT IS NOT VERIFIED — treat it as a hypothesis.
   Observed: juniper-ml has strict_required_status_checks_policy=true, so every time main moves an
   armed PR goes BEHIND and its green goes stale. ml#1612 went GREEN on FOUR separate heads before
   one survived. That part is measured.
   NOT measured: that `gh api repos/pcalnon/juniper-ml -X PATCH -f allow_update_branch=true` fixes
   it. A reviewer reads that field as governing only whether a branch may be updated when it is NOT
   required to be up to date — which is precisely the case a strict repo never has — making the flip
   a probable NO-OP here. I asserted it as "one field" without testing it. It is also GitHub's
   untouched default on ml/cascor/canopy/data alike, so it was never a hardened choice.
   util/safe_merge.py ALREADY handles BEHIND — it drives `update-branch` and polls until the ref
   actually moves (the 202-Accepted race, safe_merge.py:240). I hand-drove update-branch through
   this whole arc while the repo's own tool did it correctly.
   BUT SAFE_MERGE IS NOT A DROP-IN ANSWER EITHER, measured on THIS handoff's own PR (ml#1702):
   its per-repo CI budget for juniper-ml is 900s (safe_merge.py:200) — shorter than a busy queue —
   and on timeout it REFUSES *and DISARMS the auto-merge net it armed*, then EXITS 0. The PR is
   then left with no net and no merge, i.e. worse than before the call. safe_merge.py:159-169
   already records that 900s was below the observed max on three repos; juniper-ml was not raised.
   PRACTICAL RECIPE, in order: (a) `gh pr merge <N> --squash --auto`; (b) drive
   `gh api .../pulls/<N>/update-branch -X PUT` when it goes BEHIND; (c) if you use safe_merge, pass
   `--timeout` well above 900 and CHECK ITS OUTPUT FOR "MERGED" — exit 0 does not mean merged.
   Record: a comment on the closed ml#1611; no standalone tracker.

2. juniper-data core/limits.py:17 ("truncation must be loud") is a real hazard candidate that was
   REJECTED as mid-flight work. THAT GATE WAS ALREADY STALE WHEN WRITTEN: the docstring it quotes
   shipped in juniper-data#326 (`cf387a82`), merged 2026-09-04T10:07:45Z — 12 hours BEFORE the
   rejection was recorded. What remains open is a DIFFERENT sub-part of APD-DATA-018 (the equities
   symbol-cap arm, draft PRs data#349/#350), not the csv_import truncation contract already landed.
   So: the csv_import half is settled and re-evaluable NOW; check data#349/#350 before touching the
   equities half. Do not wait on "APD-DATA-018" as a whole — it is a compound initiative that may
   never fully close.

KEY CONTEXT — do not re-derive

* SLACK IS NOT A FLAT 2,000. It is max(largest single 30-day growing commit, 2,000 floor), defined
  per repo in conf/memory_budget.json. Reading it as a constant produced a plan that pointed at the
  wrong repos: canopy is the SLOWEST-growing repo in the fleet (~81 chars/day) and was the loosest;
  cascor is the fastest (~730/day, largest commit 9,609) and was starved at 3,575. Re-measure with
  util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth --days 30 --ref origin/main.

* THE GAP-CANDIDATE COUNT GROWS AS THE ARC SUCCEEDS: 285 -> 281 -> 282 -> 323. Cutting moves facts
  out of AGENTS.md, so the gap predicate starts matching them. A bigger number is NOT a regression.
  The health signal is the score>=3 count (7, all adjudicated) and whether anything NEW appears
  there. §7c of the triage note.

* THE RESIDENCY TEST decides promotions, not severity alone: "does reading the code recover the
  fact?" Four genuinely severe candidates were rejected on it (cascor extra="forbid", data-client
  fake_client, canopy main.py:243, data limits.py). A hazard entry is believed by construction, so
  promoting stale or self-evident prose is worse than leaving it in a reference doc.

* PROMOTING HAZARDS SPENDS FAN-OUT SLACK. cascor's ceiling was never wrong. Three hazards promoted
  during this arc added 3,917 chars (#609 +1,418, #613 +1,024, #615 +1,475) — that is 65% of the
  6,034 by which cascor's AGENTS.md grew after its cut, and 41% of its 9,609 slack. (An earlier
  draft said "65% of its 9,609 slack", mixing the two denominators; 6,034 is the one 65% belongs
  to.) cascor#619 paid it back. If you promote, pay for it in the SAME PR by relocating a reference
  section — the Hazards preamble says so.

* CASCOR'S MARGIN IS 8 CHARACTERS. headroom 9,617 against required 9,609, on the FASTEST-growing
  repo in the fleet (~730 chars/day, largest single commit 9,609). That is the tightest real margin
  anywhere here — tighter than the ml and cascor-client cases this document spends more words on.
  It is not CI-red (see the planning-heuristic note above), but one more hazard promotion in cascor
  without a paired relocation puts it under.

* Relocations: use util/ad-hoc/2026-08-19_p3_relocate_section.py, verify with util/relocation_check.py
  (G3), and CHECK HEADINGS SEPARATELY by diffing removed vs added `^-###` / `^+###` sets — G3 does
  not examine headings, and grepping guessed heading names matched 2 of 7 on canopy.

* Commit trailers (Allow-Docs-Rewrite / Allow-Ceiling-Raise / Allow-Budget-Overrun) must be in the
  LAST paragraph. One in its own paragraph registers as NOTHING and the gate fails blaming the diff.
  Verify: git log -1 --format="%(trailers:key=Allow-Docs-Rewrite)".

* Appending a TestCase after `if __name__ == "__main__"` makes it invisible to `python3 <file>`
  while `-m unittest` still finds it — both print OK with different counts. Run both.
```

---

## 2. Record — what this session completed

**Fleet headroom** (`2026-08-26_p5_fleet_state.py`). All nine clear 1,982 — but that headline is the
weaker claim, and this document elsewhere tells you not to use a flat number. **By each repo's OWN
measured requirement, juniper-cascor-client is short by 208** (2,374 against 2,582, both direct
instrument outputs). The arc was closed with that shortfall known and accepted, not resolved:

| Repo | ceiling | chars | headroom | required slack |
|---|---:|---:|---:|---:|
| juniper-cascor | 58,189 | 48,572 | 9,617 | 9,609 |
| juniper-recurrence | 20,000 | 13,259 | 6,741 | policy ceiling |
| juniper-ml | 38,000 | 34,784 | 3,216 | ~4,084 † |
| juniper-cascor-worker | 26,832 | 24,386 | 2,446 | 2,000 |
| juniper-canopy | 48,581 | 46,167 | 2,414 | 2,414 |
| juniper-cascor-client | 18,414 | 16,040 | 2,374 | 2,582 |
| juniper-data | 26,965 | 24,619 | 2,346 | 2,000 |
| juniper-data-client | 17,604 | 15,409 | 2,195 | 2,073 |
| juniper-deploy | 21,744 | 19,744 | 2,000 | 2,000 |

† **This figure is a JUDGEMENT, not an instrument output — treat it accordingly.**
`measure-growth` on juniper-ml emits `median 498  p90 2838  max 61435` and has **no
exclusion/outlier flag**, so it cannot produce 4,084. That number is the third-largest single
growth event (`f2195940` +4,084), reached by hand-dropping two structural one-offs
(`c3cf3951` +61,435, a safe-merge rewrite; `32be3897` +13,758, a docs consolidation) from a
per-commit listing. Every other row in the "required slack" column IS a direct `measure-growth`
max; this one is not, and the column's uniform appearance hides that.

**The conclusion drawn from it is contingent.** juniper-ml's headroom is 3,216. Against the
hand-derived 4,084 it is under by 868; against `p90` 2,838 — the only other figure the instrument
actually emits — it is **over** by 378. Whether juniper-ml is "under its requirement" therefore
depends on a choice this instrument cannot make for you. **cascor-client's −208 is not contingent**:
2,374 headroom against a measured max of 2,582, both direct instrument outputs.

Do not re-measure juniper-ml and expect 4,084. Either re-derive the per-commit listing, or pick a
defensible statistic and say which.

**THREE REPOS WERE DELIBERATELY LEFT TIGHT — do not "clean them up".** juniper-data (+346),
juniper-cascor-worker (+446) and juniper-data-client (+122) sit only just above their requirement,
and that was a decision, not an oversight: tightening them buys ~2,000 chars fleet-wide while
putting three repos within ~20 chars of their own worst observed commit. juniper-recurrence keeps
its 20,000 **policy** ceiling (owner decision 2026-08-28: the size at which a cut becomes worthwhile
there), which is NOT slack-derived and must not be re-derived as if it were. Full reasoning: the
closing comment on juniper-ml#1326.

**Merged this session** (squash SHAs are `mergeCommit.oid`): ml#1518 `3f8017e6`, #1519 `535283b2`,
#1533 `51d23a6c`, #1542 `143f83fc`, #1579 `019a2dca`, #1586 `5b20688f`, #1612 `b5da69e3`;
cascor#609 `da262a76`, #613 `7247f953`, #615 `f07bcb6c`, #619 `90071c56`; canopy#548 `0d0204e8`,
#554 `9a4a2f22`, #563 `66fd4158`; data#312 `b11b84ad`; data-client#185 `0fbcd670`;
worker#169 `fc9b6112`, #170 `01df4c2f`; deploy#203 `933fe3d4`, #205 `040eb61e`; recurrence#146
`831543af`.

**Ruleset**: juniper-ml `Memory Budget` now pins `integration_id=15368`; all 17 required contexts
uniform. Rollback snapshot at
`~/.local/state/juniper-ruleset-snapshots/juniper-ml-juniper-ml-rules-20260904-090723-pre-require-guard.json`.

**Hazards**: 7 entries promoted across 6 PRs, **16** rejections recorded with reasons, residual
triaged (§7b). (The triage note's §7a says "14"; §7b of the same note then records two more —
canopy `main.py:243` and data `core/limits.py:17` — without updating the running total. 16 is the
figure as of this handoff.) **Tools added**: `2026-08-31_p5_arc_net_delta.py` (`--check-shas` asserts ancestry, not
existence), `2026-08-31_resident_gap_triage.py` (`--self-check`), `2026-09-02_worktree_inuse_probe.py`,
and `--amend-integration-id` in `2026-08-20_require_context_safely.py`.

## 3. In flight — NOTHING

**ml#1682 merged** (`63ca9306`, 2026-09-04T22:35:33Z), verified an ancestor of `origin/main`. It was
OPEN when this handoff was first written and the armed auto-merge landed it during the validation
pass; the Lane A reviewer caught the stale claim. There is no in-flight work.

## 4. Git status

Branch `docs/triage-residual-closed`, one signed commit, **merged as ml#1682**. Working tree clean.

**THIS SESSION's worktrees are swept** — none remain under `Juniper/worktrees/`. That is narrower
than "the arc's": several worktrees from EARLIER sessions of this same arc are still live under
`juniper-ml/.claude/worktrees/`, including `docs/handoff-memory-governance-p5`,
`docs/handoff-2026-08-30-p5-step-e-complete`, `docs/handoff-shared-session-memory`,
`docs/handoff-2026-08-28-arc-remaining-work`, `docs/handoff-2026-08-25-p5-ports-split` and
`docs/handoff-2026-08-26-p5-promotion-preconditions`. They are not mine to remove and were not
audited here — check ownership before touching any of them. The session worktree
`.claude/worktrees/zippy-questing-wilkinson` is live and locked.

## 5. Validation record

Per §7 of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**Sizing.** High criticality (document of record, acted on by a fresh thread) × low-medium
uncertainty, escalated by universal quantifiers ("all nine", "every candidate at score ≥ 2") and by
§2's rule that the author of a measurement is its worst reviewer. Cell: 2 Lane A + 1–2 Lane B.
Run: **2 Lane A + 2 Lane B, 2 iterations.**

**Lane A — entry points deliberately disjoint.** A1 from git/PR history only (`merge-base
--is-ancestor` plus `gh pr view --json mergeCommit`), forbidden the notes. A2 by re-running the
instruments (`p5_fleet_state.py`, `measure-growth`, `require_context_safely --status`, raw
`gh api` on the ruleset), forbidden git history. Sample: 21 squash SHAs, 9 fleet rows, 8 slack
figures, 17 ruleset contexts, 1 snapshot file.

**Lane B — opposing lenses.** B1 omission/amputation, B2 false authority/self-serving framing.
Both prompted to refute, told a finding of soundness is worth nothing.

**Instrument adequacy.** A1's checks are failure-sensitive: `--is-ancestor` exits non-zero on a
dangling head, the exact error this arc produced earlier. A2 demonstrated it could disagree — it
REFUSED to reproduce the juniper-ml 4,084. Known blind spot: A2 ran the same tools the author ran,
so a bug inside `fleet_state.py` / `measure-growth` arithmetic would reproduce identically for both
and is NOT covered.

**What each round changed** (a round that changes nothing must be recorded as such — §6):

| Round | Changed |
|---|---|
| 1 (Lane A) | `ml#1682` corrected OPEN → MERGED; juniper-ml's 4,084 re-labelled a judgement, not an instrument output, with the contingency stated |
| 2 (Lane B) | `allow_update_branch` downgraded from "the fix" to an unverified hypothesis, pointing at `safe_merge.py` instead; APD-DATA-018 gate corrected (already-stale by 12h); 65% denominator fixed; rejections 14 → 16; cascor's 8-char margin surfaced; "all arc worktrees swept" narrowed to this session's; the three deliberately-tight repos restored; the required-slack-is-not-a-CI-gate note added |

**Unresolved dissent.** B2 argues that closing juniper-ml#1326 with "do not reopen" while
cascor-client is −208 against its own measured requirement is an overclaim. I did not reopen the
tracker; the shortfall is now stated in §2 rather than only in a table cell. A reader may
legitimately judge that closure premature.

**WHAT THIS EVIDENCE CANNOT SUPPORT.**

1. That flipping `allow_update_branch` fixes the merge treadmill. Never tested; a reviewer's
   reading of the API says it is likely a no-op under a strict policy.
2. That juniper-ml is "under its requirement". That depends on a hand-picked statistic the
   instrument cannot produce; by `p90` it is over.
3. That the score-1 residual contains no hazard. **229 rows, 12 sampled** — a 5% sample supports
   "consistent with the noise classes", not "contains none".
4. That the fleet is correct beyond the tools' own arithmetic. Both Lane A entry points ultimately
   trust `fleet_state.py` and `measure-growth`; neither re-implemented them.
5. That worktrees outside `Juniper/worktrees/` are clean. Not audited.
