# HANDOFF 2026-08-10 — release-train closeout: ruleset rollout, signing gap, remaining owner decisions

Continue the Juniper release-train / branch-protection arc. Standing policy: headless merges only on
Paul's explicit per-PR/group approval; guardrails (checks RAN+green, no union resolutions, defective
PRs get corrected re-lands) always apply.

## Completed (this arc)

- **On PyPI**: juniper-cascor **0.8.0** + juniper-cascor-protocol **0.2.0** (Gate-2 approved).
- **ml#1053** — the "ceremony runs keep getting cancelled" mystery SOLVED and fixed. There was never a
  canceller: the ceremony job's `timeout-minutes: 30` kills the run, and GitHub records that as
  `conclusion: cancelled`. Root cause of the 30 min: `publish_run_status` matched the FIRST run whose
  tag matched, but a Release fires every publisher and the tag-guarded ones finish `completed/skipped`
  sharing the real run's `displayTitle` AND `headBranch`; a skipped run classifies `IN_PROGRESS`
  forever, so the monitor burned its full 900s per package. New pure `select_publish_run` drops skipped
  runs, prefers exact `headBranch` over substring `displayTitle`, prefers unfinished over finished.
- **ml#1054 + ml#1056** — service-core CHANGELOG reconciled. Its `[Unreleased]` bullets had already
  shipped in the 0.5.1 wheel (bump landed before #984/#986/#993/#997, tag cut after), so propose
  correctly opened 0 PRs. Moved them into `[0.5.1]` and corrected that section's date to 2026-08-09.
  `changelog_conflict` now reads `None`.
- **cascor#506** — protocol floor `>=0.1.0a0` → `>=0.2.0`, #463 `BinaryFrame` shim retired to a plain
  re-export, `requirements.lock` in lockstep. Squash carried `Allow-Symbol-Loss: class:BinaryFrame,
  method:BinaryFrame.decode`; all five cascor main gates green on `222203b0`.
- **Branch protection: `update` rule dropped from juniper-ml — headless merges now WORK, proven.**
  ml#1056 merged with no admin flag and rule suite `3618661680` records `result=pass`, every rule
  passing — the first non-bypass merge in the repo's recent history (all prior suites were `bypass`).

## Remaining work (in order)

1. **Fleet `update`-rule sweep.** Five repos still block headless merges: **juniper-cascor,
   juniper-canopy, juniper-data, juniper-cascor-worker, juniper-deploy**. Already clean:
   juniper-ml (fixed), juniper-data-client, juniper-cascor-client. Dropping it is lossless — the rule
   carries no parameters (`{"type":"update"}`). Requires an **admin-scoped token**: the gh CLI's `gho_`
   token 404s on ruleset PATCH even with repo `permissions.admin: true`.
   ```
   gh api /repos/pcalnon/<repo>/rulesets/<id> \
     | jq '{rules: [.rules[] | select(.type != "update")]}' \
     | gh api -X PATCH /repos/pcalnon/<repo>/rulesets/<id> --input -
   ```
2. **juniper-recurrence has NO rulesets at all** — `/rules/branches/main` returns `[]` and `/rulesets`
   is empty. A publishing repo (3 packages) with zero protection on main. Owner decision: provision a
   ruleset mirroring ml's post-fix set (required_status_checks + required_signatures + pull_request +
   creation/deletion/non_fast_forward, **no** `update`).
3. **Unsigned agent-authored commits.** Both cascor#506 commits were `verified=false` despite
   `commit.gpgsign=true` in BOTH global and cascor-local config — a second independent blocker against
   `required_signatures` (7 repos enforce it). Root-cause which tool path bypassed signing. Main
   integrity was never at risk (GitHub signs the squash; cascor `222203b0` is `verified=true`).
   Check before assuming a headless PR is cleanly mergeable:
   `gh api /repos/O/R/pulls/N/commits --jq '.[].commit.verification'`
4. **Live-verify the monitor fix.** ml#1053 is merged but has not yet run a real ceremony. The next
   `BUMPED_NOT_RELEASED` cycle should reach `PENDING_PYPI_APPROVAL` in minutes, not burn 15 min/package
   and die at the 30-min cap. If it behaves, consider whether `timeout-minutes: 30` still needs raising
   (probably not) — that was a symptom, not the disease.
5. **Owner decisions**: **ml#1011** (Sequence-Safety required promotion; standing-items memory says
   soak-hold ~2026-08-21) and **ml#1012** (bypass-actor removals). ⚠️ **Interaction:** removing bypass
   actors is now safe on juniper-ml, but on any repo still carrying `update` it would make main
   **unmergeable by anyone**. Decide per-repo, and drop `update` first.
6. **cascor release round.** cascor's `[Unreleased]` now carries the protocol-floor `Changed` entry →
   next detect classifies it `UNRELEASED_CHANGES` → minor proposal (0.9.0 pre-1.0). cascor#504 (F-P4-1
   spiral) is open and may add more first.
7. **Optional / low priority**: cascor test-suite audit for under-modeled bare-`object()` stubs (the
   #472 class); the local-ceremony tag-creation restriction that local tokens can't bypass (the Actions
   path works, so this is a curiosity).

## Key context

- **GitHub auto-merge is event-driven.** After the rule drop, ml#1056 sat at `CLEAN` with auto-merge
  armed for 6+ minutes — a *ruleset edit* is not a PR event, so nothing re-evaluated the queue.
  Toggling auto-merge off/on merged it instantly. Real ceremony PRs open first and their checks
  complete after (a genuine event), so this should not bite them. **If one stalls at `CLEAN`, re-arm —
  do not admin-merge.**
- **Archive PRs are never on the release critical path.** The Release is cut and the publish run parks
  at Gate 2 regardless of whether the notes-archive PR merged.
- **Diagnose merge blocks with rule evaluations, not guesswork**:
  `gh api /repos/O/R/rulesets/rule-suites` then `.../rule-suites/<id>` → `rule_evaluations` names the
  failing rule. Two wrong hypotheses died this way (`code_quality` and `code_scanning` both `pass`).
- Concurrent sessions own: CLI experimentation (F-P4-1), canopy E2E arc. Dup-guard (`gh pr list`)
  before touching anything. A direct push of a handoff archive referencing a not-yet-merged notes doc
  reddened ml main for ~30 min today — land the notes doc first.

## Verify starting state

```bash
gh run list --repo pcalnon/juniper-ml --branch main --limit 3        # expect green at cbdb026+
gh api /repos/pcalnon/juniper-ml/rules/branches/main --jq '[.[].type]|sort'   # no "update"
gh api /repos/pcalnon/juniper-cascor/rules/branches/main --jq '[.[].type]|sort' # still has "update"
gh api /repos/pcalnon/juniper-recurrence/rulesets                    # expect [] — the gap in item 2
pip index versions juniper-cascor                                    # 0.8.0
pip index versions juniper-cascor-protocol                           # 0.2.0
gh pr list --repo pcalnon/juniper-ml --state open                    # concurrent-session PRs only
gh issue list --repo pcalnon/juniper-ml --state open                 # 1011/1012 + backlog
```

Git: work was done from the session worktree `parallel-percolating-fairy`; all branches merged and
deleted. No uncommitted work pending after this handoff merges. juniper-ml main at `cbdb026`
(+ this handoff commit); juniper-cascor main at `222203b0`, all gates green.
