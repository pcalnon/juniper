# HANDOFF 2026-08-15 — branch-protection arc: closure evidence and two corrections

**Scope: closure evidence only.** This document closes out
[`HANDOFF_2026-08-14_branch-protection-and-tier2-ci-hardening-closeout.md`](HANDOFF_2026-08-14_branch-protection-and-tier2-ci-hardening-closeout.md)
— it records which of that handoff's items are now closed, and corrects two errors it carried. It does
**not** own the live ruleset / bypass-actor family: that belongs to
[`HANDOFF_2026-08-15_ruleset-bypass-and-branch-protection-register.md`](HANDOFF_2026-08-15_ruleset-bypass-and-branch-protection-register.md)
(ml#1125), which is **authoritative** for ml#1011 and ml#1012 and is more current than anything here.
Read the register for what to *do*; read this for what *closed* and what the predecessor got wrong.

The predecessor listed 4 remaining items and 3 open questions. **Two items and one question are now
closed** — verified live 2026-08-15. The other two items (ml#1011, ml#1012) are owner decisions, held
by the register. No autonomous engineering work remains in this arc.

*On length:* the handoff procedure's ~500-word rule is deliberately exceeded, following the precedent
the register set the same day. This is closure evidence meant to outlive the session and carry each
item's proof with it, not a task baton.

## Closed — do not redo

| Predecessor item | Evidence |
| --- | --- |
| **1. cascor release round** | `juniper-cascor 0.9.0` live on PyPI (uploaded 2026-08-14T23:36:38Z); notes archived by ml#1108. The `v0.9.0` tag resolves to `1f2d9d9`, which is #519's own merge commit, so #517 and #520 shipped **inside** 0.9.0. Exactly two commits are past the tag — #522 (`3857d1e`) and #523 (`3909d27`, the 2026-08-15 tip) — so a fresh `[Unreleased]` is accumulating, two PRs deep. Normal cadence, not arc work. |
| **4. ml#1053 ceremony-monitor fix** | **Exercised by a real ceremony**, closing the "still unexercised" flag. |
| **Q. doc corruption on `main`** | Already repaired by ml#1090 (`8c4947e`), which landed after the offending `f366279`. Re-verified on `origin/main`: no `\|Documentation Links` row, no stray `Build P` line, and the `juniper-cascor-worker` Tier 1 block is a clean 19-entry list with `Bandit` restored. **Nothing to repair.** |

**ml#1053 detail.** Release-train run `31849001493` (started 2026-08-14T23:03:56Z, `mode=ceremony`;
ceremony job 23:04:36Z→23:06:36Z) published the `v0.9.0` Release at 23:05:07Z and logged
`state=PENDING_PYPI_APPROVAL` at 23:06:31Z — **~84 s** to terminal state, against the monitor's
`--monitor-timeout 900` (~15 min) bound. The job-level `timeout-minutes: 30` is deliberate headroom
above that, not the monitor's cap.

The correct pre-fix baseline is the **ceremony** runs that burned the job cap and surfaced as a bogus
`cancelled` — `31343724233` (31m13s), `31304571130` (31m09s), `31301879756` (31m08s) — which is exactly
what the predecessor's item 4 described. **Do not compare the ~84 s against the v0.8.0 publish cycle's
5h56m59s**: that is a publish run dominated by the owner-gated `pypi` Gate 2 wait, the same class of
quantity as v0.9.0's own 31m36s, which is correct and expected. Comparing monitor time to gate-wait time
implies a ~250× improvement ml#1053 never claimed. An earlier draft of this document made that error.

**Fresh ml#1011 soak evidence** (the register owns the decision; this is just a newer datapoint):
**12/12 `Sequence Safety` jobs green** across the last 12 `ci.yml` `pull_request` runs, enumerated
individually on 2026-08-15. The context remains absent from the ruleset's 14 required contexts.

## Still open — owned by no register

The predecessor's other two questions are **not** closed and **no live handoff owns them**. Checked:
neither ml#1125 (ruleset/bypass) nor ml#1124 (CLI plan) covers either. Carry them forward or file them
as issues — do not let the arc close with them orphaned.

- **Is `gh pr merge --auto`'s silent fallback to an immediate merge deliberate?** It does not arm; it
  merges. Unresolved.
- **Adopt a merge queue?** `strict_required_status_checks_policy` is `true` on all 9 repos — the
  deliberate anti-storm guarantee after the Cursor PR-storm damage. Its cost is PRs going `BEHIND`
  repeatedly under concurrent merges (ml#1076 needed three rebases). ml's `ci.yml` already has
  `merge_group:` wired (line 54) and the archive-guard job already short-circuits green on
  `merge_group`, so the wiring cost is low. Unresolved: whether the serialization is worth the latency.

## Corrections to the predecessor handoff

Both were stated as fact, are **wrong**, and are contradicted by the repo's own record
(`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`). They matter
because that handoff stays in the archive and will be read again.

1. **What made all nine repos unmergeable on 2026-08-10** was the **30-context
   `required_status_checks` fleet-union — 200 unsatisfiable contexts fleet-wide** (§1 of the record).
   The `code_scanning` fleet-union (7 tools where repos upload 1–2) was **blocker #2 in the chain**:
   the same failure class applied to a second rule, not the cause. The error lives in the predecessor's
   **Key context** bullet ("that single mistake, applied fleet-wide, is what made all nine repos
   unmergeable"), which contradicts its own **Completed** section — that one lists the five-blocker
   chain correctly, with the 30-context fleet-union first. The predecessor is internally inconsistent,
   not uniformly wrong; the Key-context bullet is the half to distrust.
   *The generalised lesson is still right, and is the one to carry:* never apply a fleet-union list to a
   per-repo rule. `required_status_checks` names each repo's actual CI job names and `code_scanning`
   names the tools that repo actually uploads SARIF for; neither can be uniform. The other seven rules
   can and should stay uniform.
2. **juniper-ml carries no `update` rule.** Its 8 rules are `deletion`, `non_fast_forward`,
   `code_scanning`, `code_quality`, `required_status_checks`, `required_signatures`, `creation`,
   `pull_request`. The `update` rule was **juniper-cascor-worker only** and was removed 2026-08-12.
   Merges during the outage got through by **admin/App bypass**, not by an `update` rule — the record's
   §1 says so explicitly ("unmergeable except by admin bypass"). The predecessor's stated reason for
   ml#1012 being *previously* unsafe was therefore wrong.

   **Do not replace it with "the bypass entries are no longer load-bearing"** — that is also false, and
   was caught in validation before this document shipped. Measured on 2026-08-15, every recorded
   `bypass` in the retained rule-suite window is actor `pcalnon` riding `RepositoryRole 5`. See the
   register §2.3 for why that entitlement is genuinely load-bearing and stays.

## What remains — held by the register, not here

ml#1011 (promote `Sequence Safety`) and ml#1012 (bypass-actor removals) are both owner decisions and
both ruleset edits. **Go to the register**, which carries the live nine-actor roster, the `1276151` =
"Amp for GitHub" identification, the newly-discovered unattributed `946600`, the `code_quality`
deadlock, and a suggested order. Two things worth restating because they are easy to get wrong:

- Apply `Sequence Safety` in the **ruleset**, never via the Quality Gate `needs:` — that job skips on
  `push` and would redden every merge.
- **Ruleset writes reject fine-grained PATs** (verified 2026-08-10; a write is the only test, so it has
  not been re-tested since). Use the web UI or a classic PAT. `Administration: Read and write` was
  granted and other admin writes succeed, yet ruleset `PATCH` 404s via both `gh` and raw `curl`.

**After any ruleset edit**, before treating it as landed:

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py     # expect BLOCKING=0 on all 9, unchanged
gh api '/repos/pcalnon/juniper-ml/rulesets/rule-suites?per_page=2' \
  --jq '.[]|"\(.after_sha[0:8]) \(.result)"'               # next real merge must read pass, not bypass
```

Have an **independent** checker confirm both — not the session that applied the edit. The failure mode
is silent: nothing goes red, PRs simply stop being mergeable.

## Verify starting state

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py                 # expect BLOCKING=0 on all 9
gh run list --repo pcalnon/juniper-ml --workflow main-verify.yml --limit 3   # expect success
gh api /repos/pcalnon/juniper-ml/rules/branches/main --jq '[.[].type]|length'          # 8
gh api /repos/pcalnon/juniper-recurrence/branches/main/protection                      # 404
gh issue list --repo pcalnon/juniper-ml --state open                   # 1011 / 1012 + backlog
```

## Git state

Archived from a worktree branched off `origin/main`. `main` moves continuously — it advanced five times
during this session's validation — so **re-probe before acting**; two facts in an earlier draft of this
document went stale between drafting and validation, and a third was superseded by ml#1125 merging
mid-validation. `gh pr list` dup-guard before touching anything: concurrent sessions own the
CLI-experimentation, canopy E2E, defect-register and release-train-signing arcs.
