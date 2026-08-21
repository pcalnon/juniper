## Summary

Documents the `Guard PR base branch` required status check and its `stacked-pr` escape hatch in this repo's `AGENTS.md`.

Closes finding **F-9** of the adversarial audit for [juniper-ml#434](https://github.com/pcalnon/juniper-ml/issues/434). Documentation only — no workflow, ruleset, or code change.

## The gap

`Guard PR base branch` became a **merge-blocking required context** on all 9 repos on 2026-08-20, and `stacked-pr` was created as its escape hatch. Grepping each default branch for either string found **1 mention across 9 repos** — a required context that can block `main`, written down almost nowhere.

That is the condition under which someone debugs a blocked PR from scratch at the worst possible moment.

## What the entry records

Four things that are not guessable from the workflow file:

1. **The job `name:` *is* the required context string.** Renaming the job or deleting the file makes `main` unmergeable until the context is un-required first — the file cannot simply be removed.

2. **Why it matters more than it looks.** Both rulesets are scoped `~DEFAULT_BRANCH`, so a PR based on a feature branch is governed by **no ruleset at all** — zero required checks, merges clean with nothing having run. This guard carries no `branches:` filter, making it the *only* check that runs there.

3. **Retargeting is not enough.** Every `ci*.yml` uses the default `pull_request` types `[opened, synchronize, reopened]`, which exclude `edited`. A retarget re-runs this guard and nothing else, so the PR stays blocked on its other contexts. The remedy is **close and re-open** (`[retarget #NNN]`).

4. **What the label does and does not do.** It silences this guard; it does not make the PR mergeable into `main` and does not re-land the stack.

## Notes

The `**Last Updated**` header is bumped in the same signed commit, which is what satisfies `agents-md-touch-up.yml` — that workflow verifies the field and no longer bumps it itself (a runner commit is unsigned, and `required_signatures` rejects it).

`AGENTS.md` was fetched from `main` immediately before this commit was authored, because the tool that opens these PRs uploads whole files and a stale local copy would silently revert anything that landed in between.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01CeHVJMbbxw2BNd6fMx7zGw
