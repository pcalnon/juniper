## Summary

Corrects the base-branch guard's failure message, which currently states something **false** on all 9 repos.

Follow-up to the ml#434 rollout. The context string is unchanged (`Guard PR base branch`), so no ruleset change is needed and nothing is blocked by this PR.

## What was wrong

The shipped message says:

> This PR cannot merge as-is regardless of this guard: `ci.yml` is scoped to `main`, so none of this repo's other required checks will ever report on a PR based on `<branch>`.

The first clause is **not true**, and an independent fact-check against live state caught it:

```console
$ gh api repos/pcalnon/juniper-ml/rules/branches/feature%2Fsome-stacked-base --jq length
0
$ gh api repos/pcalnon/juniper-ml/rules/branches/main --jq length
9
```

Both rulesets are scoped `~DEFAULT_BRANCH`. A PR whose base is a feature branch is governed by **no ruleset at all** — its required contexts do not sit at `expected`, **they do not apply**. Such a PR has zero required status checks and **can be merged**, green badge and all, with nothing having run.

That is precisely how `juniper-recurrence#7`/`#8` and `juniper-canopy#365` stranded their content.

## Why this matters more than a wording nit

The old message falsely reassures: *"you can't merge this anyway."* A reader who believes it has no reason to treat the situation as dangerous.

The truth is the opposite — **you can merge it, and if you do, your work never reaches `main`.** The new message says that plainly:

> READ THIS BEFORE MERGING ANYWAY. The rulesets here are scoped to `main`, so a PR based on `<branch>` is governed by NO ruleset: it has zero required status checks and CAN be merged, green badge and all, with nothing having run. This check is the only thing watching.

## Also corrected

- The `stacked-pr` warn-arm message, which carried the same false claim.
- The header's "WHAT THIS GUARD IS AND IS NOT" section, which described the guard as a legibility measure over an already-blocked PR. It is in fact the **only** check that runs on a stacked PR, because it carries no `branches:` filter.
- The header now records what requiring the context actually buys: on a PR targeting the default branch it guarantees the guard ran, so a deleted or broken workflow cannot silently stop protecting.

## Testing

Context string asserted unchanged by parsing (`Guard PR base branch` — a change here would block every PR on every repo requiring it). `yamllint` clean, 0 errors. No trigger or logic change: only the header comment and the two message bodies differ.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

<https://claude.ai/code/session_01CeHVJMbbxw2BNd6fMx7zGw>
