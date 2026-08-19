# Sequence-Safety Context Rename — execution record

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-19
**Status**: **COMPLETE** — all 8 sibling repos renamed and re-required
**Related**: [juniper-ml#1011](https://github.com/pcalnon/juniper-ml/issues/1011)

---

## 1. What changed

The sequence-safety check on the eight sibling repos was renamed from
`Sequence Safety (Advisory)` to `Sequence Safety`. It became a **required** status check on
2026-08-18; a required gate labelled "advisory" is actively misleading. juniper-ml was already
plain `Sequence Safety` and was not touched.

Both occurrences per workflow were renamed: the workflow-level `name:` (the Actions-UI label)
and the **indented job-level** `name:` — only the latter is the required-context string.

Tool: `util/ad-hoc/2026-08-19_sequence_safety_context_rename.py` (`--phase status|unrequire|pr|require`,
dry-run default).

## 2. The ordering trap

The job name **is** the required-context string, so this is a two-sided change — and the naive
order deadlocks:

> A PR that renames the job publishes the **NEW** name on its own CI run. The currently required
> `Sequence Safety (Advisory)` context therefore never reports on it, and the rename PR is
> **permanently blocked by itself.**

The only order that works:

| Phase | Action | Effect |
| --- | --- | --- |
| 1 | `--phase unrequire` | drop the old context from the ruleset |
| 2 | `--phase pr` + merge | rename the job |
| 3 | `--phase require` | add the new context |

Between 1 and 3 the screen is **not enforced**. That is deliberate — it is the state the screen
was in until 2026-08-18, and far preferable to blocking every merge on eight repos.

## 3. The incident: I made `main` unmergeable on five repos

**This is the important part of this document.**

Phase 1's ruleset write rebuilt every required context as
`{"context": c, "integration_id": 15368}` — hardcoding the GitHub Actions integration id.

That was wrong. On five repos the `Bandit` context comes from integration **57789**, not
Actions. After the edit GitHub expected `Bandit` *from GitHub Actions*, which never reports it.

**Result: a required context that can never be satisfied — `main` unmergeable on
juniper-cascor, juniper-data, juniper-data-client, juniper-cascor-client and
juniper-cascor-worker, with nothing going red.** This is precisely the failure class the whole
branch-protection effort exists to prevent.

### How it presented

Five PRs sat `BLOCKED` with **zero** pending checks, **zero** unresolved review threads, no
failing checks, and every required context reporting `SUCCESS`. `gh pr merge` said only
*"the base branch policy prohibits the merge"*.

### How it was found

A perfect correlation: the five blocked repos required `Bandit + CodeQL` in the `code_scanning`
rule; the three that merged required `CodeQL` only. Reading the ruleset **history** version from
immediately before the edit showed the true value:

```text
"57789|Bandit"
```

The timeline confirmed causation — juniper-cascor#537 merged at 21:42:55Z, the ruleset edit
landed at 22:48:53Z, and every PR after that was blocked.

### How it was repaired

Reconstruct `context -> integration_id` from the pre-edit history version and re-apply the
current context list with the correct ids. All five verified `remaining mismatches=none`, and
all five flipped `BLOCKED -> CLEAN` immediately.

### Why the guards missed it

The write already asserted rule count, rule-type set, bypass-actor count, `strict` policy and
ref targeting. It verified the **shape** of the ruleset but not the **identity of what satisfies
it**. Two fixes, both now in the tool:

- `set_contexts` **preserves** each context's existing `integration_id`; only a genuinely new
  context defaults to Actions.
- A **post-write assertion** fails if any surviving context's `integration_id` drifted.

> **Rule for any future ruleset edit: a required status check is `(context, integration_id)`,
> not a string.** Rewriting the pair from a constant silently retargets the check at an app that
> will never report it.

## 4. Second trap: a ruleset edit is not a PR event

After the repair the five PRs were `CLEAN` with auto-merge armed — and still did not merge.

Auto-merge had been armed while they were `BLOCKED`; the thing that unblocked them was a
**ruleset edit**, which is not a PR event, so nothing re-evaluated them. The fix is to **re-arm**
(`--disable-auto`, then `--auto` again). All five merged within seconds of the toggle.

Never reach for `--admin` here: it would bypass the very checks being enforced.

## 5. Final state (verified 2026-08-19)

- All 8 repos: `Sequence Safety` required; zero `(Advisory)` occurrences on remote `main`.
- Context counts: cascor 22, canopy 19, data 20, data-client 18, cascor-client 18, worker 20,
  deploy 10, recurrence 9.
- **`BLOCKING=0` across all 9**, `matched == required` everywhere.
- `integration_ids` verified unclobbered on all 8.
- No open PR anywhere in the 8 was stranded by the rename.

## 6. Rollback

Reverse the phases: `--phase unrequire` (removing `Sequence Safety`), revert the workflow
rename, then re-add the old context. Cheaper in practice: revert the eight workflow commits and
re-run phases 1 and 3 with the names swapped.
