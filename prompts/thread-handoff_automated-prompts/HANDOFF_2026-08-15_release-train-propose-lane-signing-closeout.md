# HANDOFF 2026-08-15 — release-train propose-lane signing repair: ARC CLOSED

Closeout for the branch-protection / release-train arc. The prior handoff
(`HANDOFF_2026-08-14_release-train-propose-lane-signing-repair.md`) listed four remaining items;
**three were completed by a later session and are now live-verified, and the fourth was answered
with evidence.** Nothing in this arc is blocked on engineering work.

Standing policy unchanged: headless merges only on Paul's explicit per-PR/group approval;
guardrails (checks RAN + green, verify `result=pass` not `bypass`, defective PRs get corrected
re-lands) always apply.

## Verified complete

- **Item 1 — cascor 0.9.0 proposal re-run: DONE, ml#1096 live-proven.** cascor#518's release
  commit `efd2bbf8` is `verified=true / valid`; merged with rule suite **`result: pass`**; no
  touch-up commit on the branch. The signed-commit propose lane works end to end.
- **Item 2 — #1099: CLOSED.** 11 PRs / 8 repos. `agents-md-touch-up.yml` now *verifies* the
  `**Last Updated**` date instead of mutating the branch (kills the unsigned-commit and
  `[skip ci]`-orphan classes at once); lockfile lanes commit via `createCommitOnBranch`.
- **Item 4 — ml#1053 monitor fix: exercised and PASSED (first real test).** Ceremony log:
  `ceremony-result: plan=CEREMONY_PLANNED state=PENDING_PYPI_APPROVAL pkg=juniper-cascor
  version=0.9.0 issue=- issue_failed=0`. Job ran **2m00s**, not a 15-min-per-package monitor
  burn — `select_publish_run` correctly dropped the two skipped tag-guarded siblings. Zero HALTs.
  Full chain: propose → signed merge → ceremony → archive PR ml#1108 (auto-merged) → Release
  v0.9.0 → publish success → **PyPI serves juniper-cascor 0.9.0**.

## Remaining — both owner-decision, no code work

- **#1011 promote Sequence Safety to required.** Soak ends ~2026-08-21. Apply in the **ruleset**,
  never the Quality Gate `needs:` (its `pull_request`-only skip must not fail pushes).
- **#1012 remove cursor/claude always-bypass.** Evidence posted 2026-08-15
  (`issues/1012#issuecomment-5301668312`): across the full retained rule-suite window for ml main
  (32 suites) — 23 `pass`/pcalnon, 8 `bypass`/pcalnon, 1 `pass`/`juniper-release-train[bot]`.
  **Zero** bypasses attributable to a cursor or claude App, so the REMOVE is safe. Say the word
  and the ruleset edit can be applied via API.

## Key context

- **Read #1012's scope before reasoning about "bypass."** It removes only the cursor/claude
  *Integration* grants and KEEPS `RepositoryRole id=5` (owner) + `Integration 4362741`
  (release-train App, `bypass_mode: pull_request`). Conflating them gives the wrong answer.
- **Integration IDs cannot be mapped to App names from the CLI** — `GET /user/installations`
  403s for a user token and there is no public app-by-id endpoint. The unidentified `1276151`
  and the writable DeployKey need the Settings → Rules bypass-list UI.
- **The `update` ("Restrict updates") rule is gone from all 9 repos**, which now carry an
  identical 8-rule set. The old ml#925-era trap ("removing bypass while `update` remains makes
  main unmergeable by anyone") is retired; so is the recurrence 6-vs-8 rule gap.
- **`RepositoryRole id=5` is load-bearing** (matters only to a *future* proposal to drop it):
  all 8 bypasses ran through it — 5 direct pushes to main, 1 squash-SHA-had-no-reports race
  (#1115; same signature as #1090), 1 unresolved `github-advanced-security` review thread
  (#1113, invisible to `gh pr checks` — query `reviewThreads` via GraphQL).
- Concurrent sessions own the canopy E2E and CLI-experimentation arcs and are actively pushing
  to main. `gh pr list` dup-guard before starting anything.

## Verify starting state

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py                     # BLOCKING=0 on all 9
python -m unittest -q tests.test_release_train_propose                     # 132 OK
gh run list --repo pcalnon/juniper-ml --workflow main-verify.yml --limit 3 # success
gh issue list --repo pcalnon/juniper-ml --state open                       # 1011 / 1012 remain
curl -s https://pypi.org/pypi/juniper-cascor/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"  # 0.9.0
```

## Git status

juniper-ml `main` clean and in sync with `origin/main`. No uncommitted work from this session —
its only repo artifact is this handoff. The two local doc commits from the prior session
(`db8deae`, `f5779bb`) were rebased and pushed by a concurrent session as `25e4582` / `27c6fb3`.
Ruleset writes still reject fine-grained PATs — use the web UI or a classic PAT.
