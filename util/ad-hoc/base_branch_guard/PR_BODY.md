## Summary

Adds `.github/workflows/pr-base-branch-guard.yml` — a repository hygiene guard that flags any pull request whose base branch is not the repository default branch.

Part 1 of [juniper-ml#434](https://github.com/pcalnon/juniper-ml/issues/434). The workflow already runs on `juniper-recurrence`; this brings the other 8 repos to parity. **Advisory on arrival** — this PR does not change any ruleset.

## The failure it names

A PR based on another feature branch can squash-merge into that intermediate branch, stranding its content off `main` while GitHub shows a green **MERGED** badge. It has bitten this ecosystem three times: `juniper-recurrence#7` and `#8` (WS-4b app routes + publish workflow — the app was left unpublishable) and `juniper-canopy#365`.

## What this guard is, and what it is not

It is a **legibility** guard, not the thing that stops the merge — a distinction measured during an adversarial review, not assumed.

Every Juniper repo's `ci.yml` is scoped `pull_request: branches: [main, develop]`. So a PR whose base is a feature branch triggers **none** of that repo's 10–22 required contexts: they sit at `expected` and the PR is *already* unmergeable. What this workflow adds is a **named, actionable failure** in place of a silent stall with nothing red — which is precisely the state that made the three historical instances hard to notice.

That is also why the `stacked-pr` label cannot make a stacked PR mergeable. The label satisfies this guard; the other required contexts still never report. It means *"this stack is deliberate, stop flagging it"* — not *"this PR may merge here."*

## Fixes carried over the juniper-recurrence original

An adversarial audit of the original found defects that are corrected here:

- **`labeled` / `unlabeled` added to `types:`.** Without them the advertised `stacked-pr` escape hatch **cannot be actuated** — adding the label after the guard has failed produces no new run, so the failed check stands and the PR stays blocked by its own documented remedy.
- **Empty-`DEFAULT_BRANCH` now fails open, not closed.** An unresolved payload field previously fell through to the failure arm, which would fail *every* PR on the repo at once — with the only escape being the hatch that could not be actuated.
- **Failure message rewritten** to state that the PR cannot merge regardless of this guard, and to recommend **close-and-reopen** (`[retarget #NNN]`, the practice this fleet actually uses — cascor #189/#190, #214/#215) rather than in-place base editing, which has never been exercised here.
- **Header records the merge-ref semantics**: `pull_request` workflows are read from `refs/pull/N/merge`, so renaming the job or deleting the file changes/removes the published context. Both require un-requiring first.

## Not in this PR

Making `Guard PR base branch` a required status check. That is a ruleset write, owner-gated, and deliberately sequenced **after** the workflow is landed and observed reporting — requiring a context nothing publishes yet would block every open PR fleet-wide.

## Testing

- Parses under `yaml.safe_load`; `yamllint` clean.
- Context string verified exactly `Guard PR base branch` (the job `name:`, not the workflow `name:` and not the job id).
- The guard runs on its own introducing PR — `pull_request` workflows come from the merge ref — so this PR should show the check passing with base `main`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01CeHVJMbbxw2BNd6fMx7zGw
