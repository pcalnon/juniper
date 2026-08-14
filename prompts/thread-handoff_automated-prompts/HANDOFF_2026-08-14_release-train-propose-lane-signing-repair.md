# HANDOFF 2026-08-14 — release-train propose-lane signing repair

Continue the Juniper branch-protection / release-train arc. Standing policy: headless merges only on
Paul's explicit per-PR/group approval; guardrails (checks RAN + green, verify `result=pass` not
`bypass`, defective PRs get corrected re-lands) always apply.

## Completed (this session)

- **Doc corruption repaired** (ml#1090, merged `8c4947e7`). `f366279` was a legitimate table-alignment
  reformat carrying two paste-damage sites. The load-bearing one fused two context names inside the
  **juniper-cascor-worker Tier 1 block** and deleted `Bandit` outright — 18 entries under a declared
  19 — in the block §6 tells operators to paste verbatim. All 9 blocks now reconcile
  `declared == actual`, and the repaired block is byte-identical to the live ruleset.
- **main-verify red cleared.** `68f62f5` demoted a heading to bold text in the canopy E2E matrix;
  the AST-blind docs screen read it as a heading deletion and the catch-up base re-reported it on
  every later commit. Cleared by `Allow-Docs-Rewrite`. (#1089, a concurrent session, landed the same
  waiver minutes earlier — mine was redundant.) main-verify green on the last 4; #1059 closed.
- **THE BIG FIND — the release-train propose lane could not produce a mergeable PR at all.** Driving
  the cascor 0.9.0 round surfaced two defects affecting **all 18 packages / 8 repos**:
  1. `propose.py` committed with `-c commit.gpgsign=false`. The **2026-08-12 `required_signatures`
     normalization — from this very arc** — turned that into a hard block. Proof it is new:
     cascor#497 (v0.8.0, merged 08-08) carried identically unsigned commits and merged fine.
  2. `propose.py` bumped `**Version**` but not `**Last Updated**`, so `agents-md-touch-up.yml` pushed
     a `[skip ci]` commit that became the PR head — no required context ever reports on it.
  Both fixed in **ml#1096**: `execute_proposal` **and** `execute_follow_on` (same defect) now share
  `_execute_signed_pr` using `createCommitOnBranch`; the local-`git` helper is **deleted** with an
  anti-resurrection test. cascor#515 closed with the diagnosis.
- **Issue #1099 filed** — the same root cause hits `agents-md-touch-up.yml` (all 9 repos) and the
  lockfile lanes: unsigned runner commits, now unmergeable.

## Remaining work

1. **Re-run the cascor 0.9.0 proposal** once #1096 lands:
   `gh workflow run release-train.yml -f mode=propose -f packages=juniper-cascor`.
   Verify the PR opens **signed**, with CI reporting and **no** touch-up commit. Detect already
   classifies `UNRELEASED_CHANGES` → minor, ship 3/0/1.
2. **#1099** — recommend making the touch-up *verify* the date rather than mutate the branch (kills
   both the unsigned and `[skip ci]` classes); use `propose.py`'s `create_signed_commit` as the
   reference for the lockfile lanes.
3. **#1011** promote Sequence Safety (soak ends ~2026-08-21) — in the **ruleset**, never the Quality
   Gate `needs:`. **#1012** bypass-actor removals.
4. **ml#1053 monitor fix still unexercised** — the cascor ceremony will be the first real test.

## Key context (hard-won this session)

- **A force-push does NOT fire `synchronize` for Actions here; a normal fast-forward push does.**
  Rebase and close/reopen both produced **zero** runs; an empty commit worked instantly. Looks
  identical to the `[skip ci]` orphan from the PR page. Cost three failed re-triggers.
- **Green check rollup ≠ mergeable.** #1096 sat `blocked` with all 18 checks passing on an unresolved
  `github-advanced-security` review thread (`required_review_thread_resolution: true`) — invisible to
  `gh pr checks`. Query `reviewThreads` via GraphQL when a PR is blocked with everything green.
- **Concurrent merges silently convert `pass` merges into `bypass`.** ml#1090 recorded `bypass` with
  `required_status_checks: fail — 14 of 14 expected`: three PRs landed between its green check and
  its merge, so the squash SHA had no reports yet and the owner's entitlement let it through. Content
  was fine (main-verify passed post-merge), but this erodes the property the arc established — a
  second data point for the **merge-queue** question after ml#1076's three rebases.
- `main` moved 4+ times during one PR, several as owner direct-pushes doing bulk doc reformatting
  (`f366279`, `68f62f5`, `a43cf57`) — that class is what produced both the corruption and the red.
- Concurrent sessions own the CLI-experimentation (#1097) and canopy E2E arcs. `gh pr list`
  dup-guard first — #1089/#1091 duplicated my main-verify work this session.

## Verify starting state

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py                        # BLOCKING=0 on all 9
gh run list --repo pcalnon/juniper-ml --workflow main-verify.yml --limit 3    # success
python -m unittest -q tests.test_release_train_propose                        # 132 OK
gh issue list --repo pcalnon/juniper-ml --state open                          # 1099 / 1012 / 1011
gh pr list --repo pcalnon/juniper-cascor --state open                         # empty until re-proposed
```

## Git status

juniper-ml `main` clean at `7acc4a9` — ml#1096 merged (release-train signing repair, rule suite
`pass`, all 3 `Allow-Symbol-Loss` trailers in the squash body); ml#1090 merged `8c4947e7` (doc
repair; recorded `bypass` for the concurrency reason above). cascor#515 closed unmerged by design.
Ruleset writes still reject fine-grained PATs — use the web UI or a classic PAT.
