# HANDOFF 2026-08-07 — juniper-ml + juniper-cascor PR-backlog processing (fleet merge waves)

Continue working through the open GitHub PR backlogs in **pcalnon/juniper-ml** and **pcalnon/juniper-cascor** per the fleet-supervisor triage plans and Paul's standing authorization.

## Authorization (given 2026-08-07, in-session)

- **Merge all green ready PRs as we go**, honoring all guardrails against destructive PR-storm merges (checks must have RUN and passed; predicted-merge verdicts respected; no union-style conflict resolutions).
- **Flip DRAFT → ready + merge per the supervisor plans**, healing reds as they surface.
- **Approved dup-closes** (execute only AFTER the keeper merges, diff-verify nothing unique is lost first): close ml#972 + ml#974 (keeper **#973**); close ml#934 + ml#942 (keeper **#944**, reworked as in-place edit); close ml#936 (keeper **#968**).

## Signing regime (CHANGED — supersedes older memory)

Headless signing **WORKS**: `user.signingkey=B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!` (ed25519 subkey, new v4 primary `06DBAC38…6DABC4`, uid paul.calnon@gmail.com). Commit **normally** (signed); verify `git log --format='%G?' -1` = `G`. No more `-c commit.gpgsign=false`, no createCommitOnBranch needed. If signing ever times out (agent cache expiry), probe with `echo x | gpg --clearsign -u <key> >/dev/null` and fall back to createCommitOnBranch only if genuinely broken.

## Completed this session

- **Merged**: cascor#450 (f4059ba7), cascor#449 (e8f8c7ea), cascor#447 (2005f028 — after my C901 heal `e378570`: extracted `_artifact_to_tensors` in `src/api/lifecycle/manager.py`, 50/50 PR tests pass). Branches deleted. cascor now ~31 open.
- **ml#938 healed** (`c7f230b`): setUpClass class-attr annotations for the mypy lane on `tests/test_publish_testpypi_verify.py`. NOTE: #938 is still **CONFLICT**-classed (W5 ci.yml cluster) — needs conflict-aware update, not just green checks.
- **ml#947 updated** (my docs branch `docs/ed448-compliance-gate-ubuntu-scope`): rescoping + Paul's format pass (`a724e31`) + stray ssh-ed25519 line folded into §5.7 fence (`98c6c74`).
- **ml#999 opened**: `docs/REFERENCE.md` de-dup heal (deleted older duplicate `## Fleet Triage and Sequence Safety` copy + dup TOC line; kept the #926-superset copy). Commit + PR body carry the `Allow-Docs-Rewrite: docs/REFERENCE.md` trailer. **Prerequisite (step 0) for the ml docs wave.**
- **ml#1000 opened — MERGE THIS FIRST**: heals main's RED CI (red since #924/#915 landed): black on 3 test files, `# nosec B105/B106` on throwaway literals, `RedactedEnv(os.environ, GIT_*=…)` in `test_main_verify_catchup_base._git()`. All hooks + 18 tests green locally. **Every open PR inherits main's red through merge-result CI until this lands.**
- **16 PRs flipped ready + branch-updated** (CI was queued BEFORE #1000, so they will still show inherited reds): ml 957 958 978 989 992 985 986 984 997 993 965 982; cascor 459 468 469 479.

## Remaining work (in order)

1. Poll #1000 → REST-merge when green: `gh api -X PUT repos/pcalnon/juniper-ml/pulls/1000/merge -f merge_method=squash` (the `gh pr merge` CLI preflight is over-conservative; REST enforces the real rules — this pattern was proven on cascor#450/449/447). Delete branch after.
2. Re-run/update the inherited-red PRs: `gh pr update-branch N` on #999, #947, and the 16 above (post-#1000 base) → merge each as it greens. #947 and #999 are docs-only and safe. For the 16: merge in supervisor order (985→986, 984→997→993, 965→982 within clusters; solos any order). cascor's 4 (459/468/469/479) likely green already (cascor main is green) — merge on green.
3. **ml W3 black/mypy heal family** (all DRAFT, same defect class as `c7f230b`): #976 #959 #956 #955 #963 #967 #961 #941 #943 #949 #933(READY) #940. Fix = run repo black hook + annotate setUpClass attrs (mypy `attr-defined`); #961 additionally `Need type annotation for "boundary"` at tests/test_run_experiment.py:1268. Then ready+update+merge. Good task-executor fan-out candidates (instruct: signed commits, verify %G?=G).
4. **ml W4–W6 conflict waves** (42 PRs) per the supervisor plan in the prior session transcript — key rules: #977 first (re-land heal; then 930/961/982 re-validate); docs cluster (29-way on DEVELOPER_CHEATSHEET/DOCUMENTATION_OVERVIEW/REFERENCE/QUICK_START + AGENTS.md) resolves ONLY as in-place edits of existing sections (10 PRs re-add sections that already exist — never union); consider a single consolidation PR instead of 29 serial resolutions; re-run `python util/fleet_triage/predict_merge.py --pr N` (or `--batch`) after every merge in a cluster.
5. **cascor waves**: #463 (black reformat of `worker_stream.py`) then ready+merge; W2 rebases done (step 2); W4 code conflicts order: #460, #474 BEFORE #471 (same ownership block), #451(READY), #454, #461, #462, #470, #471, #472 (careful: tensor-literal conflict — a careless union changes test semantics), #475, #477 (drop its duplicate empty-weights guard — main already has it in validate_tensors; keep the rest); W5 docs 15-way serial (cheatsheet `**Version**:` line is the serialization point — every merge invalidates the rest; consider consolidation + flag the version-line hazard to Paul).
6. Dup-closes per authorization above, each AFTER its keeper merges.
7. Loose ends: pre-existing broken links in `notes/releases/RELEASE_NOTES_juniper-canopy_v0.6.0.md` (2 links → canopy-repo notes; the link_base class — separate small fix); this handoff file is untracked — commit it with any convenient PR; memory topic `project_code_signing_key_migration_2026-07-16` may deserve a "signing now works headlessly" addendum once Paul confirms the regime is permanent.

## Key context / gotchas

- **predict_merge re-validation**: after every merge, re-run for PRs sharing touched files. Evidence JSONs from the triage are in the (ephemeral, SHARED) scratchpad — regenerate rather than trust.
- **REST-merge pattern**: `gh pr merge` says "add --auto/--admin" even when actually mergeable; `gh api -X PUT …/pulls/N/merge -f merge_method=squash` gives the true answer. cascor requires 16 named contexts green; ml similar. Squash is allowed in both repos.
- **Ruleset**: ml main has `required_signatures` — fleet/Cursor commits are GitHub-signed (verified), session commits are signed now; keep it that way.
- **Worktrees**: session worktree `shimmying-twirling-clarke` currently on branch `fix/main-ci-red-heal`; `main` is checked out by another session's worktree (`soft-scribbling-sphinx`) — use `git switch --detach origin/main` or feature branches, never take `main` here. Primary checkout was on `cursor/missing-test-coverage-1f31` (another session) — leave it alone.
- **Never quote** Allow-* or skip-ci markers in prose in commit messages/PR bodies (whole-body trailer parser).
- Supervisor plans' full per-PR tables live in the 2026-08-07 session transcript (session "code signing", purple). The wave memberships above are complete; per-PR detail (behind/delta/deps) can be regenerated via `predict_merge.py --batch`.

## Verify starting state

```bash
gh pr view 1000 --repo pcalnon/juniper-ml --json state,mergeStateStatus   # the linchpin
gh run list --repo pcalnon/juniper-ml --branch main --limit 3             # main CI red until #1000
gh pr list --repo pcalnon/juniper-ml --state open --limit 80 | wc -l      # ~66 pre-merges
gh pr list --repo pcalnon/juniper-cascor --state open --limit 50 | wc -l  # ~31
git -C /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/shimmying-twirling-clarke status
```
