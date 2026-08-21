## Summary

Adds a `merge_group:` trigger to the base-branch guard, with the early-exit that makes it safe. Closes audit findings **F-6** (implemented) and **F-5** (closed as a reasoned no-change, documented in the file).

Context string is unchanged (`Guard PR base branch`), so no ruleset edit is needed and nothing is blocked by this PR.

## F-6 — the trap in the obvious fix

`ci.yml` carries `merge_group:` precisely so gating contexts re-post on the queued merge commit; this guard did not, so if a merge queue were ever enabled the context would never post and the queue would stall.

But **adding the trigger alone would have been worse than omitting it.** A `merge_group` payload carries neither `pull_request` nor `base_ref`. Trace the existing logic with that payload:

```
BASE_REF=""            DEFAULT_BRANCH="main"   (merge_group payloads do carry `repository`)
empty-default guard -> does not fire
"" = "main"          -> false
HAS_BYPASS           -> false
                     -> exit 1
```

**Every queued merge would hard-fail.** So the trigger comes with an explicit early-exit: a queued merge has already been accepted into the queue for a specific target branch, so there is no PR base to police.

## This is tested, because it cannot be tested where it runs

Merge queues are unavailable on user-owned accounts, so the `merge_group` arm **cannot be exercised on any of these repos**. The only way to know it works is to run the shell directly, which `test_guard_shell.py` does — extracting the `run:` block from the YAML and executing it under bash with the env each event would supply.

Six cases, all passing, and **mutation-checked**: disabling the early-exit fails 2 of 6, confirming the `exit 1` trap above is real rather than theoretical.

That matters here specifically. This guard's failure arm went 137+ runs without executing once, and when finally driven its label hatch turned out not to work at all. "It reads correctly" has already been shown to be insufficient for this file.

## F-5 — `concurrency:`, deliberately not added

The audit flagged that six trigger types let a busy PR accumulate several same-named check runs. Left alone, with the reasoning recorded in the file:

1. **Duplicates are benign.** GitHub counts the newest run — measured on recurrence#120, where a stale `failure` and a newer `success` sat on the same head and `gh pr checks` reported **pass**.
2. **The obvious fix is worse.** `cancel-in-progress: true` produces `cancelled` conclusions, and `cancelled` is a **non-success** conclusion on a required context. Whether a *superseded* `cancelled` run is ignored the way a superseded `failure` is has **not** been measured — and a required-context gate is the wrong place to find out.
3. **Concurrency without cancellation doesn't solve it.** It serialises runs; it doesn't reduce their number.

The real fix was in the **consumer** and already shipped: `wait_for_checks.py` kept the *first* run per context name and so reported FAILURE for a context GitHub considered passing. It now selects by timestamp.

Revisit only with a measurement showing a superseded `cancelled` run does not gate.

## Testing

`yaml.safe_load` parses; context string asserted exactly `Guard PR base branch`; `yamllint` 0 errors; 6/6 shell cases pass, mutation-checked.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01CeHVJMbbxw2BNd6fMx7zGw
