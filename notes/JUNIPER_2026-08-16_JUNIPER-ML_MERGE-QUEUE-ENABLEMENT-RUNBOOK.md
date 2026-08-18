# juniper-ml Merge Queue — Enablement Runbook

**Project**: juniper-ml
**Author**: Paul Calnon
**Date**: 2026-08-16
**Status**: **BLOCKED — merge queue is unavailable to this repository.** Retained as a conditional runbook; §5 becomes executable only if the repository moves to organization ownership.
**Tracking issue**: [juniper-ml#1128](https://github.com/pcalnon/juniper-ml/issues/1128)

---

## 0. Finding (2026-08-16) — merge queue is unavailable, and this is not fixable by configuration

**GitHub merge queues require organization ownership.** The availability statement:

> Pull request merge queues are available in any public repository owned by an organization, or in
> private repositories owned by organizations using GitHub Enterprise Cloud.

`juniper-ml` is `visibility: public` but `owner.type: **User**`. It therefore does not qualify.

**Confirmed empirically:** the **"Require merge queue"** rule is **not present** in the Add-rule list
on the `juniper-ml-rules` ruleset page. Two independent confirmations — the documented availability
scope and the rule's absence from the UI — agree.

This resolves the open question the flood-remediation analysis flagged as "the one nuance
unconfirmable by read-only API". The answer is **no**.

### Consequences

- **The fallback is already in force and is correct.** Flood analysis §4 decision 1 reads "queue if
  available, else strict". `strict_required_status_checks_policy` is `true` on all 9 repos. Nothing
  needs to change; there is no gap to close.
- **Nothing was mis-wired.** The `merge_group:` triggers in `ci.yml` and `codeql.yml` and the
  `release-train-archive-guard` reconciliation are inert without a queue (the `merge_group` event
  never fires) and cost nothing. **Leave them in place** — they are the completed Step 0 for any
  future org migration, and removing them would only have to be redone.
- **The rebase tax that motivated #1128 is unresolved.** See §9 for what remains available.
- Everything in §2–§3 (the required-context audit, the signing analysis) was verified before the
  availability answer landed and stays valid. It is retained so a future org migration does not have
  to redo it.

---

## 1. Why this was proposed

`strict_required_status_checks_policy` ("require branches to be up to date before merging") is `true`
on all 9 Juniper repos — the deliberate anti-storm guarantee adopted after the Cursor PR-storm damage.
Its cost is that PRs repeatedly go `BEHIND` under concurrent merges and must be re-synced by hand
(ml#1076 needed three rebases). A merge queue delivers the same guarantee without the manual rebase.

This is **not a new proposal**. The merge queue is the flagship P1 recommendation of
[`JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md)
§4 owner decision 1, where the recorded answer is *"i concur with recommendation."* That decision left
exactly two unblockers: a **UI availability check** and a **`merge_group` smoke test**. Step 0 (the
`merge_group` wiring) is now complete.

The queue is strictly stronger than `strict=true`: strict implements only **M2** (re-test the
prospective merge result), while the queue also implements **M1** (it *performs* the clean automated
merge-or-eject, replacing the manual Update-branch that authored the #801/#803 damage).

---

## 2. Preconditions — all verified 2026-08-16

| Precondition                                               | Status                                               |
|------------------------------------------------------------|------------------------------------------------------|
| `merge_group:` wired in `ci.yml` (line 54)                 | ✅ done                                              |
| `merge_group:` wired in `codeql.yml`                       | ✅ done                                              |
| `release-train-archive-guard` reconciled for `merge_group` | ✅ `ci.yml:706` runs + green short-circuit           |
| All 14 required contexts report on `merge_group`           | ✅ audited job-by-job (§3)                           |
| Quality Gate `needs:` free of merge_group-skipped jobs     | ✅ all 8 needs unconditional                         |
| `allow_auto_merge`                                         | ✅ `true`                                            |
| `required_approving_review_count`                          | ✅ `0` (no review gate to block headless auto-merge) |

### Required-context audit

All 14 contexts in the `required_status_checks` rule post on a `merge_group` event:

| Source                                 | Contexts                                   | How it reports on `merge_group`                                               |
|----------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------|
| `ci.yml` `pre-commit`                  | `Pre-commit (Python 3.12/3.13/3.14)`       | unconditional job                                                             |
| `ci.yml` `tests`                       | `Regression Tests (Python 3.12/3.13/3.14)` | unconditional job                                                             |
| `ci.yml` `build`                       | `Build and Validate Package`               | unconditional job                                                             |
| `ci.yml` `docs`                        | `Documentation Links`                      | unconditional job                                                             |
| `ci.yml` `security`                    | `Security Scan`                            | unconditional job                                                             |
| `ci.yml` `claude-yaml-audit`           | `Claude.yml Access Audit`                  | unconditional job                                                             |
| `ci.yml` `dependency-docs`             | `Dependency Documentation`                 | unconditional job                                                             |
| `ci.yml` `release-train-archive-guard` | `Release-Train Archive Guard`              | `if: pull_request \|\| merge_group`; green notice before any base-ref diffing |
| `ci.yml` `required-checks`             | `Quality Gate`                             | `if: always()`; `needs:` are all unconditional                                |
| `codeql.yml` `analyze`                 | `Analyze (python)`                         | `merge_group:` wired                                                          |

The advisory `sequence-safety` and `fleet-pr-lint` jobs are deliberately **absent** from the Quality
Gate `needs:`, so their skips cannot redden the gate.

> **Latent trap (not a blocker).** `Security Scan` is a job name in **two** workflows — `ci.yml:1074`
> (push / PR / merge_group) and `security-scan.yml:13` (schedule / dispatch only; workflow titled
> "Scheduled Security Scan"). Only the `ci.yml` job fires on `merge_group`, so the required context is
> satisfied. Renaming one of them would remove the ambiguity.

---

## 3. The signing question — answered

**Condition: mandatory code signing must survive the queue. It does — provided the queue's merge
method is `squash` (or merge-commit), never `rebase`.**

1. Ruleset `13805432` targets **`~DEFAULT_BRANCH` only** (`include: ["~DEFAULT_BRANCH"]`,
   `exclude: []`). The queue's temporary `gh-readonly-queue/*` branches are therefore **ungoverned** —
   `required_signatures` never evaluates them.
2. The only commit that must satisfy `required_signatures` is the final one landing on `main`. That is
   the queue's *speculative commit*, constructed **server-side by GitHub** and documented as "the exact
   commit that will end up on the target branch". GitHub signs commits it creates with its web-flow
   key — the same mechanism that already makes this repo's squash merges `Verified`.
3. PR-side commits are already GitHub-signed fleet-wide after ml#1099 (`createCommitOnBranch`), so the
   "an unsigned commit anywhere in history blocks the merge" trap is already closed.

**The trap:** GitHub's rebase-and-merge re-creates commits and adds them *without* signature
verification. A rebase-method queue would push unsigned commits at `main` and deadlock against
`required_signatures`.

> **Honesty note.** GitHub's documentation never states merge-queue / required-signatures
> compatibility either way. The above is an inference from ruleset scope plus how GitHub signs
> server-created commits. **Step 5.4 is what settles it empirically** — do not skip it.

---

## 4. Availability — RESOLVED: unavailable

**Answered 2026-08-16 — see §0.** Merge queues require organization ownership; `juniper-ml` is
User-owned, and "Require merge queue" is absent from the ruleset UI. §5 is not executable.

For the record, the ambiguity that made this worth testing: the 2024-02-27 rulesets changelog
(merge queue rule, public beta) describes the rule as applying to repository-level rulesets in
"personal or organization-owned repositories" and says only *organization rulesets* are unsupported —
which reads as permitting a personal repo. The product availability statement is the narrower and
governing one. **Do not re-litigate this from the changelog wording; the UI is the ground truth.**

> **The merge queue rule also cannot be configured via the API** ("This feature will be available in
> the near future" — 2024-02-27 changelog). Even where available, the web UI is the only path. Do not
> attempt a ruleset `PATCH`.

---

## 5. Procedure — NOT EXECUTABLE TODAY

> **This section is conditional.** It becomes executable only if `juniper-ml` moves to organization
> ownership (§9.3). Retained so the analysis does not have to be redone. Do not attempt §5.2 today —
> the rule is not offered.

### 5.1 Availability check (the gate)

Settings → Rules → Rulesets → **juniper-ml-rules** (`13805432`) → **Add rule**.

Is **"Require merge queue"** present and selectable?

- **No** → stop. See §0 / §4. ← **this is the current state, checked 2026-08-16**
- **Yes** → continue.

### 5.2 Add the merge queue rule

Configure exactly:

| Setting                                  | Value                | Why                                              |
|------------------------------------------|----------------------|--------------------------------------------------|
| **Merge method**                         | **Squash and merge** | The signing constraint (§3). **Never `rebase`.** |
| **Maximum pull requests to merge**       | **1**                | See the strict-compatibility note below.         |
| **Minimum pull requests to merge**       | 1                    | —                                                |
| **Wait time to meet minimum**            | 5 min (default)      | Irrelevant at group size 1.                      |
| **Build concurrency**                    | 5 (default)          | Number of `merge_group` webhooks dispatched.     |
| **Only merge non-failing pull requests** | **on**               | Never land a group whose members failed.         |
| **Status check timeout**                 | 60 min (default)     | ml's full battery + CodeQL fits comfortably.     |

> **Group size 1 vs. strict.** "Require branches to be up to date before merging" is **not compatible
> with a batch size > 1** and must be unset in that case. Two coherent configurations:
>
> - **(a) Conservative — group size 1, keep `strict=true`.** Fully serialized; strict stays as a
>   belt-and-braces second gate. Highest latency, zero change to the existing anti-storm guarantee.
>   **Recommended for the first run.**
> - **(b) Throughput — group size 5, unset `strict`.** The queue supersedes strict entirely (it is a
>   superset: M1 + M2). Batches merges, much lower latency under load.
>
> Start with (a). Move to (b) only after the queue has proven itself, and note the rollback ordering
> in §7.

### 5.3 Drop `rebase` from the allowed merge methods

Same ruleset → the **Require a pull request before merging** rule → **Allowed merge methods**.

Current: `["merge", "squash", "rebase"]` → set to `["merge", "squash"]`.

Rationale: rebase strips commit signatures, so it can never produce a `required_signatures`-compliant
merge. Removing it makes the one method that would deadlock `main` unselectable. This is
defense-in-depth and is independent of the queue.

### 5.4 Smoke test — do not skip

```bash
git checkout -b test/merge-queue-smoke origin/main
# make a trivial no-op change, e.g. touch a scratch file under util/ad-hoc/
gh pr create --base main --head test/merge-queue-smoke \
  --title "test: merge queue smoke" --body "throwaway — verifies queue + signing"

gh pr merge <N> --auto --squash        # EXPECT: "added to the merge queue", NOT an immediate merge
```

Then confirm, in order:

```bash
# 1. a merge_group run actually fired
gh api /repos/pcalnon/juniper-ml/actions/runs --jq \
  '[.workflow_runs[]|select(.event=="merge_group")][0]|{name,head_branch,conclusion}'

# 2. all 14 required contexts reported on it (none missing => no stall)
gh api /repos/pcalnon/juniper-ml/commits/main/check-runs --jq \
  '[.check_runs[]|{name,conclusion}]|sort_by(.name)'

# 3. THE SIGNING ANSWER — must be verified:true
gh api /repos/pcalnon/juniper-ml/commits/main --jq '.commit.verification|{verified,reason}'
```

Step 3 is the empirical resolution of §3. If it reports `verified: false`, **roll back immediately**
(§7) — `required_signatures` and the queue are incompatible in this configuration.

### 5.5 Post-edit verification — by an independent checker

Per the standing rule, the session that applied the edit must **not** be the one that confirms it.

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py     # expect BLOCKING=0 on all 9, unchanged
gh api '/repos/pcalnon/juniper-ml/rulesets/rule-suites?per_page=2' \
  --jq '.[]|"\(.after_sha[0:8]) \(.result)"'               # next real merge must read pass
```

The failure mode is silent: nothing goes red, PRs simply stop being mergeable.

---

## 6. What changes operationally

- **Merging becomes "Merge when ready"**, not "Squash and merge". Stop using manual Update-branch.
- `gh pr merge --auto` now **queues** instead of merging on the spot. This also removes the standing
  foot-gun where `--auto` on an already-green PR merged immediately because there was nothing to wait
  for (documented in `gh pr merge --help`).
- The release-train hands-free archive-PR path is unaffected: `Release-Train Archive Guard` posts
  green on `merge_group`, `required_approving_review_count` is `0`, and the App-signed commit still
  satisfies `required_signatures`.
- **Latency tax:** every merge waits for a full battery + CodeQL cycle, serialized at group size 1.
  The benefit is storm-concentrated; between storms this is pure cost.

### Bypass interaction (honest)

Both queue and strict rules are **skipped by bypass actors**. Every recorded bypass in the retained
rule-suite window is `pcalnon` on `RepositoryRole 5`, which stays. So the queue's teeth come from
routing merges through "Merge when ready", **not** from enforcement — it does not bind the
admin-batch path. Making it binding is [juniper-ml#1012](https://github.com/pcalnon/juniper-ml/issues/1012),
a separate owner decision.

---

## 7. Rollback

Delete the **Require merge queue** rule from the ruleset. There is no intermediate broken state.

**Ordering matters if you chose configuration (b):** re-enable `strict_required_status_checks_policy`
**before** removing the queue, or `main` is briefly left with neither merge-result gate.

Under configuration (a), `strict=true` never left, so removing the queue returns to exactly today's
behavior.

---

## 8. The rebase tax — what remains available

The queue is out. The problem that motivated #1128 — PRs going `BEHIND` repeatedly under concurrent
merges, ml#1076 needing three rebases — is unchanged. Options, cheapest first.

### 8.1 Use the update-branch API instead of a local rebase (cheap, available now)

```bash
gh api -X PUT /repos/pcalnon/juniper-ml/pulls/<N>/update-branch
```

One call clears `BEHIND`. It is a **server-side merge**, so the resulting commit is GitHub-signed and
satisfies `required_signatures` — unlike a local rebase, which rewrites commits and (for a signing
setup that is not fully headless) can strip or re-prompt for signatures. No checkout required, which
also makes it usable from a session confined to one worktree.

This does not reduce the *number* of syncs; it reduces each one to a single API call. Most of the
felt tax is the manual rebase ceremony, not the waiting.

**Caveat, and it is a real one:** the flood analysis attributes the #801/#803 damage to exactly this
operation — a manual Update-branch that silently re-authored wholesale doc-section deletions which
then passed CI green, because prose deletion is invisible to the doc-link validator. That gap is now
partly covered by the `juniper-docs-additions-check` sequence-safety screen (deleted-heading and
`>=N`-line-deletion-run detection), which did not exist during the storm — but it is **advisory**, not
a required context (ml#1011). Prefer update-branch over a local rebase; do not treat either as
self-verifying.

### 8.2 Batch merges into quiet windows (free, behavioural)

The tax is `O(concurrent merges)`. Landing a group of PRs back-to-back in one window, rather than
interleaved with other sessions' merges all day, collapses most of the re-sync churn. This is a
scheduling change, not a config change.

### 8.3 Move to a GitHub organization (unlocks the queue, but is a real migration)

Transferring the Juniper repos to an org-owned account makes merge queues available in public repos
at no plan cost, and §5 becomes executable as written.

This is **not** a small change and should not be undertaken for the merge queue alone. Scoped from the
tree on 2026-08-16, it touches at minimum:

- **504 tracked files contain a `pcalnon/` string** (`git grep -l 'pcalnon/' | wc -l`) — overwhelmingly
  doc and issue links, but they all rot on transfer. GitHub redirects transferred repos, so these
  degrade rather than break immediately.
- **Owner-coupled code**, which does break: `util/open_signed_pr.py` (`--owner` defaults to `pcalnon`,
  line 183), `util/release_train/ceremony.py`, and `.github/workflows/publish.yml`.
- **PyPI trusted publishing** — OIDC subjects pin the repository owner, so all 7 publishers must be
  re-registered on PyPI *and* TestPyPI before the next release, or every publish fails at the gate.
- **The 9 rulesets**, including the bypass-actor entries and their numeric App IDs.
- **The release-train GitHub App** installation and its `RELEASE_TRAIN_APP_ID` repo variable.

Note what is *not* affected, which narrows the job usefully: `util/release_train/registry.yaml`,
`ECOSYSTEM_REPOS` in `docs-full-check.yml`, and `DEFAULT_REPOS` in `validate_claude_yaml_access.bash`
all carry **bare repo names** with no owner prefix, and need no change.

If it is ever considered, it should be scoped as its own arc with the merge queue as one benefit
among several — not as the driver.

### 8.4 Do nothing (defensible)

`strict=true` is the documented fallback and was accepted as such when the decision was recorded. The
tax is real but bounded, and every alternative above costs more than it saves at the current merge
volume.

---

## 9. References

- [`JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) — §1 queue vs strict, §4 decision 1 (approved)
- [`JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`](JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md) — per-repo required contexts
- [juniper-ml#1128](https://github.com/pcalnon/juniper-ml/issues/1128) — tracking issue
- [juniper-ml#1012](https://github.com/pcalnon/juniper-ml/issues/1012) — bypass-actor removal (makes the queue binding)
