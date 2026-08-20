# Adversarial audit — `pr-base-branch-guard.yml` before fleet rollout as a REQUIRED check

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-20
**Status**: Audit COMPLETE, findings ACTED ON, rollout SHIPPED. See §-1 below.
**Original verdict** (preserved, and correct for the file as it stood): *"Do not require this context
on the 8 target repos as written."* The blocking findings were fixed first; the rollout then went
ahead. Nothing below has been rewritten to match the outcome.
**Scope**: **Read-only.** No workflow, ruleset, label, PR, or repository setting was created or modified.
**Artifact under review**: `.github/workflows/pr-base-branch-guard.yml`, present only in `pcalnon/juniper-recurrence`
**Proposed action under review**: copy to `juniper-ml`, `juniper-cascor`, `juniper-canopy`, `juniper-data`, `juniper-data-client`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-deploy`, and add `Guard PR base branch` to each repo's ruleset as a required status check.

---

## -1. Resolution — what was done about each blocking finding (added 2026-08-20, post-rollout)

This section was appended after the audit, by the rollout. **The audit body below is unedited**, so
the reasoning that produced each finding survives independently of the outcome.

Three of the audit's findings were then tested empirically on throwaway PRs
(`juniper-recurrence#118` and `#120`, both closed, branches deleted). Two confirmed the audit; one
**refuted** its worst case.

| Finding | Disposition |
| --- | --- |
| **F-01** label hatch unactuatable (`labeled` missing from `types:`) | **CONFIRMED EMPIRICALLY, then FIXED.** On `#118` the label was applied at `23:21:06Z` and produced **zero** new workflow runs; the failed check stood. `labeled` + `unlabeled` added to `types:` in the rolled-out file. |
| **F-02** `stacked-pr` label absent from all 9 repos | **FIXED.** Created on all 9 (`util/ad-hoc/base_branch_guard/make_labels.py`). |
| **F-03** stacked PRs already unmergeable, so requiring adds ~no protection | **ACCEPTED AS TRUE, and it reframed the change.** The guard is a **legibility** measure — a named failure instead of a silent stall — not the thing that stops the merge. The rolled-out file and its PR body now say so explicitly rather than implying the label makes a stacked PR mergeable. Owner decided to proceed on that understanding. |
| **F-04** rollout ordering wedges open PRs | **HANDLED.** Workflow landed on all 9 default branches first; the require step is gated by a pre-flight (`2026-08-20_require_context_safely.py`) that **refuses** to require a context nothing has been observed publishing. The 4 open PRs fleet-wide were then unstuck with `update-branch`. |
| **F-06** context-string fragility | **PINNED.** Job `name:` asserted exactly `Guard PR base branch` by parsing before rollout; header now records that renaming the job or deleting the file requires un-requiring first. |
| **F-07** no `DEFAULT_BRANCH` sanity check → could fail every PR | **FIXED.** Empty expansion now warns and `exit 0` (fails **open**), instead of falling through to the failure arm. |
| **F-13** fail path never executed in 137 runs | **EXECUTED.** `#118` drove it: `completed failure`, correct annotation, `BASE_REF`/`DEFAULT_BRANCH`/`HAS_BYPASS` all resolved correctly. This is the test the workflow's own header asked for at its `:38`. |
| **F-11** duplicate same-name check runs, resolution rule unknown | **RESOLVED — the reassuring way.** On `#120`, unchanged head `435f95e22311`, two runs coexisted (`failure` @`23:24:33`, `success` @`23:24:48`) and `gh pr checks` reported the context as **pass**. **GitHub takes the latest.** The audit's "all-must-pass" horn — which would have made retarget a permanent block — does not hold. |
| **F-16** does `edited` fire on a base change? (audit could not verify) | **ANSWERED: yes.** Retargeting `#120` at `23:24:42Z` produced a new guard run within seconds. |

**One finding the audit did not have, discovered by the same probe.** Retargeting a PR re-runs the
guard but re-runs **nothing else**: every `ci-*.yml` uses the DEFAULT `pull_request` types
`[opened, synchronize, reopened]`, which exclude `edited`. On `#120` required contexts sat at
**1/9 finished** after a retarget and reached **9/9** only after close-and-reopen. The original
guard's advice — *"Edit -> change base"* — therefore leaves the PR stuck on eight never-reported
contexts. The rolled-out message recommends **close and reopen** (`[retarget #NNN]`), which is both
the house practice and the one that works.

**A second-order find:** `util/wait_for_checks.py` kept the **first** check run per context name, so
on `#120` it reported `FAILURE` for a context GitHub considered **passing** — it would declare a
recoverable PR permanently failed. Fixed to latest-wins, with regression tests in both directions
(stale failure must not gate; a genuine *later* failure must still be caught). The pre-existing 33
tests passed before and after, so nothing had covered this.

**Final state:** all 9 repos carry the guard **and** require `Guard PR base branch`
(`integration_id: 15368`). Fleet BLOCKING contexts: **0**. Required contexts 152 → 160 (exactly +8),
with `Bandit`'s `integration_id: 57789` intact on the five repos that use it.

---

## 0. Bottom line

The guard's *detection logic* is sound and its motivating incident is real (verified: juniper-recurrence
#7 and #8 both merged into stacked bases, §6). Every finding below is about what happens when this
particular file is made a **required** context on eight repos whose CI is configured the way it actually is.

Three results dominate:

1. **The documented escape hatch does not work — three independent reasons, any one sufficient.**
   `labeled` is not in the trigger list, so adding the label the failure message tells you to add does
   not re-run the guard (F-01). The `stacked-pr` label does not exist in any of the nine repos (F-02).
   And even if both were fixed, a base≠`main` PR on all eight targets produces **none** of that repo's
   10–22 required contexts, because every `ci.yml` is `pull_request: branches: [main, develop]` (F-03).
   The workflow's own header — *"base != default branch AND the PR carries the `stacked-pr` label ->
   warn but pass (intentional stacks opt out)"* (`:25-26`) — describes an opt-out that cannot exist on
   the target fleet.

2. **The fail path has never executed.** 137/137 runs concluded `success` (§4, F-13). The workflow header
   itself asks for the missing test: *"Confirm the fail path once with a throwaway PR against a
   non-default base."* (`:38`). It was made a required check on juniper-recurrence without that
   confirmation. The `exit 1` arm, the `::error` annotation, and the label-bypass arm are all
   unexercised in production — the vacuous-pass class in its guard form.

3. **`required` does not constrain the actor whose mistake this catches.** Independently measured on
   juniper-ml over the last month: **401 of 612 rule-suite evaluations (65.5%) were `bypass`, all of them
   on `refs/heads/main`** (F-14). The stranded-PR defect class is an owner-merge defect; the owner
   bypasses the ruleset roughly two updates in three.

**Recommendation**: adopt the workflow on all 8 repos **as an advisory (non-required) check first**, fix
F-01/F-02/F-06/F-07, run the fail-path test the header asks for, then re-evaluate requiring it. The
current benefit of requiring it is near zero on the 8 targets — a stacked PR is *already* unmergeable
there (F-03) — while every blocking finding below is a new way to wedge a legitimate PR.

---

## 1. Checklist applied

| ID | Criterion | Pass means | Result |
| --- | --- | --- | --- |
| C-A1 | Escape hatches | No path lets a stacked PR pass while stranding content, and the documented hatch actually works | **FAIL** (F-01, F-02, F-05, F-08, F-09, F-10, F-14) |
| C-A2 | Trigger coverage | Base changes always re-evaluate; no stale base can be reported | **PARTIAL FAIL** (F-01, F-08, F-09, F-10; F-16 could not verify) |
| C-A3 | Required-check trap | Every PR class produces a check run | **FAIL** (F-04, F-05, F-06 blocking; F-11, F-12 latent/informational) |
| C-A4 | Name stability | The produced context string is stable and is the string being required | **FAIL** (F-06) |
| C-A5 | Per-repo portability | Behaves identically on all 8 targets | **FAIL** (F-03); default-branch portability claim **PASSES** (§5) |
| C-A6 | Legitimate stacked work today | No open PR would be broken by requiring it today | **PASS** (§6) |
| C-A7 | Injection / expression safety | Untrusted values cannot reach the shell body or forge outcomes | **PASS** (§7) |
| C-A8 | Negative-path evidence | The failing branch has demonstrably executed | **FAIL** (F-13) |

---

## 2. The artifact (verbatim, load-bearing lines)

Retrieved live:

```bash
gh api repos/pcalnon/juniper-recurrence/contents/.github/workflows/pr-base-branch-guard.yml --jq '.content' | base64 -d
```

```yaml
42  name: PR Base-Branch Guard
43
44  on:
45    pull_request:
46      types: [opened, reopened, edited, synchronize]
47
48  permissions:
49    contents: read
50
51  jobs:
52    guard-base-branch:
53      name: Guard PR base branch
54      runs-on: ubuntu-latest
55      steps:
56        - name: Require PR base to be the default branch
57          env:
58            BASE_REF: ${{ github.base_ref }}
59            DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
60            HAS_BYPASS: ${{ contains(github.event.pull_request.labels.*.name, 'stacked-pr') }}
61          run: |
...
66            if [ "${BASE_REF}" = "${DEFAULT_BRANCH}" ]; then
...
71            if [ "${HAS_BYPASS}" = "true" ]; then
...
79            exit 1
```

Header claims under test (`pr-base-branch-guard.yml:25-26`, `:28-29`, `:38`):

```text
25  #      - base != default branch AND the PR carries the ``stacked-pr`` label
26  #                                -> warn but pass (intentional stacks opt out)
28  #    The default branch is read dynamically from the event payload, so this workflow
29  #    is portable to any repository without edits.
38  #    Confirm the fail path once with a throwaway PR against a non-default base.
```

---

## 3. Findings that BLOCK MERGES (severe)

### F-01 — BLOCKER — The `stacked-pr` hatch cannot be actuated: `labeled` is not a trigger type

**Location**: `pr-base-branch-guard.yml:46` (trigger list) vs `:78` (remediation text)

**Problem**: The failure message instructs the user to *"add the `stacked-pr` label"*. Adding a label
fires `pull_request.labeled` — an activity type that is **not** in `types: [opened, reopened, edited,
synchronize]`. No new run is produced; the failing check run stands; the merge stays blocked. The user
must additionally push a commit or edit the title/body to force a re-evaluation, which the message never
says.

**Evidence** — the file's own text (`:46`, `:78`):

```yaml
    types: [opened, reopened, edited, synchronize]
```

```text
Fix: retarget this PR to '${DEFAULT_BRANCH}' (Edit -> change base). If a stacked PR is intentional, add the 'stacked-pr' label AND re-land the stack on ${DEFAULT_BRANCH} after merge.
```

`labeled` and `unlabeled` are distinct activity types, not folded into `edited`. Fetched
<https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=edited>, verbatim list for
`pull_request`:

> `"assigned, auto_merge_disabled, auto_merge_enabled, closed, converted_to_draft, demilestoned, dequeued, edited, enqueued, labeled, locked, milestoned, opened, ready_for_review, reopened, review_request_removed, review_requested, stacked, synchronize, unassigned, unlabeled, unlocked"`

**Failing scenario**: PR opened, base `feature/x` → guard fails → operator follows the printed
instruction → nothing happens → PR appears permanently red with a message that says it was fixed.

**Fix**: add `labeled, unlabeled` to `types:`.

---

### F-02 — MAJOR — The `stacked-pr` label does not exist in any of the nine repos

**Location**: repository label sets (live API)

**Problem**: The bypass depends on a label nobody can apply, including on juniper-recurrence where the
context is **already required**.

**Evidence**:

```bash
gh api repos/pcalnon/juniper-recurrence/labels --jq '.[].name' | tr '\n' ' '
# bug documentation duplicate enhancement good first issue help wanted invalid question wontfix

gh api repos/pcalnon/juniper-ml/labels --paginate --jq '.[].name' | tr '\n' ' '
# automated bug dependencies documentation duplicate enhancement good first issue help wanted invalid main-verify question wontfix
```

The same command on `juniper-cascor`, `juniper-canopy`, `juniper-data`, `juniper-deploy`,
`juniper-data-client`, `juniper-cascor-client`, `juniper-cascor-worker` returns label sets that likewise
contain no `stacked-pr` (cascor adds `main-verify`; canopy adds `dependencies`/`python`; data adds
`workstream:WS-1`/`workstream:WS-4`; the other four are the stock nine).

**Note on the pattern**: `allow-symbol-loss` and `docs-rewrite` — the WARN-only Sequence Safety hatches
documented in `AGENTS.md` — are likewise absent from the juniper-ml label set. Label-based hatches in
this fleet are documented but not provisioned.

**Fix**: create the label in each repo as part of the rollout, or drop the label mechanism.

---

### F-03 — BLOCKER — The "intentional stacks opt out" is architecturally impossible on all 8 targets

**Location**: `pr-base-branch-guard.yml:25-26` (the claim) vs each repo's `ci.yml` `on.pull_request.branches`

**Problem**: Every one of the eight target repos filters its main CI workflow to PRs targeting
`main`/`develop`. A PR whose base is a feature branch therefore produces **zero** of that repo's required
contexts. Per GitHub's documentation those checks stay Pending and block the merge. So even with F-01 and
F-02 fixed, a `stacked-pr`-labelled PR with a green `Guard PR base branch` still cannot merge — the other
10–22 required contexts never report.

**Evidence** — `on.pull_request.branches` per repo (local checkouts; origin state re-verified via
`gh api .../contents/.github/workflows/ci.yml` for canopy and cascor-worker, identical):

| Repo | `ci.yml` lines | Filter |
| --- | --- | --- |
| juniper-ml | `47-50` | `branches: [main, develop]` |
| juniper-cascor | `45-48` | `branches: [main, develop]` |
| juniper-canopy | `47-50` | `branches: [main, develop]` |
| juniper-data | `43-46` | `branches: [main, develop]` |
| juniper-data-client | `43-46` | `branches: [main, develop]` |
| juniper-cascor-client | `43-46` | `branches: [main, develop]` |
| juniper-cascor-worker | `43-46` | `branches: [main, develop]` |
| juniper-deploy | `37-40` | `branches: [main, develop]` |

juniper-ml's `codeql.yml:25-26` is stricter still: `pull_request: branches: [main]`.

Fetched <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax>, verbatim:

> "When using the `pull_request` and `pull_request_target` events, you can configure a workflow to run only for pull requests that target specific branches."

> "If a workflow is skipped due to path filtering, branch filtering, or a commit message, then checks associated with that workflow will remain in a 'Pending' state. A pull request that requires those checks to be successful will be blocked from merging."

Required-context counts per repo (from each ruleset's `required_status_checks.required_status_checks[].context`):
ml 16, cascor 22, canopy 19, data 20, data-client 18, cascor-client 18, cascor-worker 20, deploy 10.

**Consequence, both directions**:

- The guard's *bypass* arm is inert on all 8 — it cannot unblock anything.
- The guard's *blocking* value is also near zero on all 8 — a stacked PR was already unmergeable before
  the guard existed. What the guard adds is a legible error message in place of a silent stall. That is
  worth having; it is not worth a required context.

**Fix**: state the real remediation in the failure text ("close this PR and reopen it against `main`"),
and either (a) keep the guard advisory, or (b) if the stack opt-out is genuinely wanted, the branch
filters in all 8 `ci.yml` files must change first — a much larger, separate decision.

---

### F-04 — BLOCKER — Rollout ordering: PRs open at the moment the context is required are wedged

**Location**: inherent to `on: pull_request` + `required_status_checks`

**Problem**: Workflows are event-driven. Adding `pr-base-branch-guard.yml` to `main` does not
retroactively produce a check run on already-open PRs. If `Guard PR base branch` is added to the ruleset
in the same change, every already-open PR sits at "expected" until it receives a fresh `pull_request`
event.

**Evidence** — the two PRs open right now on juniper-ml, both `base: main`, neither touched since
creation:

```bash
gh api repos/pcalnon/juniper-ml/pulls/1205 --jq '[.number,.head.ref,.head.sha[0:8],.base.ref,.created_at,.updated_at]|@tsv'
# 1205  exp/determinism-n20-seed-reproducibility  5385149f  main  2026-08-20T15:18:45Z  2026-08-20T15:18:45Z
gh api repos/pcalnon/juniper-ml/pulls/1206 --jq '[.number,.head.ref,.head.sha[0:8],.base.ref,.created_at,.updated_at]|@tsv'
# 1206  feat/pointer-follow-soak-instrument       62307b95  main  2026-08-20T20:09:04Z  2026-08-20T20:09:04Z
```

Fetched <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks>, verbatim:

> "A required status check must have completed successfully in the chosen repository during the past seven days."

and the same page requires the check to pass "on the latest commit SHA".

**Fix**: land the workflow file, wait for every open PR to be touched (or push an empty commit to each),
*then* add the context to the ruleset. Never in one change. The seven-day clause also means a PR parked
longer than a week needs a re-run regardless.

---

### F-05 — BLOCKER — `[skip ci]`-class commit markers wedge the guard, and this fleet has been bitten before

**Location**: inherent to `on: pull_request`

**Problem**: A commit-message skip marker suppresses the entire workflow run; the required context never
reports and the PR cannot merge. GitHub's own documentation tells you not to require such a workflow.

**Evidence** — fetched <https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs>, verbatim:

> "Workflows that would otherwise be triggered using `on: push` or `on: pull_request` won't be triggered if you add any of the following strings to the commit message"

with the strings `[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`, `[actions skip]` and the
`skip-checks:true` trailer; and:

> "If a workflow is skipped due to path filtering, branch filtering or a commit message (see below), then checks associated with that workflow will remain in a 'Pending' state."
> "A pull request that requires those checks to be successful will be blocked from merging."

The troubleshooting page states the guidance outright: **"avoid requiring workflows that can be skipped."**

**Ecosystem precedent**: this exact class already produced a permanently BLOCKED PR in the fleet
(cascor#515, recorded in `AGENTS.md` under `agents-md-touch-up.yml`: *"the `[skip ci]` bump commit became
the PR head so no required context ever reported on it -- the PR sat permanently BLOCKED with every check
at 'expected'"*).

**Status**: not *differential* — every existing required context has this property — but it is one more
context that a single stray commit message can wedge, on a workflow whose only output is a two-line
string comparison.

---

### F-06 — BLOCKER — Context-string fragility: the required string is the job `name:`, and it is read from the PR's merge ref

**Location**: `pr-base-branch-guard.yml:42` (workflow `name:`), `:52` (job id), `:53` (job `name:`)

**Problem**: A required status check is matched by context string. Three different strings exist in this
one file and only one is the context. Worse, the string is read from the **PR's own merge ref**, so a PR
that renames the job produces the new context while the ruleset still requires the old one — that PR, and
the PR that would revert it, are both unmergeable.

**Evidence — the produced context is `Guard PR base branch`** (the job `name:` at `:53`):

```bash
gh api repos/pcalnon/juniper-recurrence/actions/runs/32310736828/jobs --jq '.jobs[] | [.id, .name, .conclusion] | @tsv'
# 96253015259   Guard PR base branch    success

gh api repos/pcalnon/juniper-recurrence/commits/bc997503/check-runs --jq '.check_runs[] | [.name, .conclusion, .app.slug] | @tsv'
# ... Guard PR base branch  success  github-actions ...
```

It is **not** `PR Base-Branch Guard` (the workflow `name:` at `:42`, which is the string shown in the
Actions sidebar and the most likely mis-copy) and **not** `guard-base-branch` (the job id at `:52`, which
is what the context would silently become if `name:` at `:53` were deleted).

**Evidence — workflows are read from the PR's merge ref, not from `main`**: the guard ran on its own
introducing branch before it existed on `main`:

```bash
gh api --paginate "repos/pcalnon/juniper-recurrence/actions/workflows/pr-base-branch-guard.yml/runs?per_page=100" \
  --jq '.workflow_runs[] | [.created_at, .head_branch, .head_sha[0:8], .conclusion] | @tsv' | tail -3
# 2026-06-17T20:57:21Z  ci/pr-base-branch-guard  81b13018  success
# 2026-06-17T20:56:15Z  ci/pr-base-branch-guard  81b13018  success
# 2026-06-17T20:54:17Z  ci/pr-base-branch-guard  25941294  success
```

**Evidence — this drift class is live in this fleet right now**. `agents-md-touch-up.yml` currently reads:

```text
58  name: AGENTS.md Date Check
75      name: Verify AGENTS.md Last Updated
```

while a check run named **`Bump AGENTS.md Last Updated`** is still attached to juniper-ml#995's head SHA:

```bash
gh api repos/pcalnon/juniper-ml/commits/418f1eb0350f62e0725d33127d1cd202d3b2502b/check-runs --jq '[.check_runs[]|.name]|join(", ")'
# Quality Gate, CodeQL, ..., Bump AGENTS.md Last Updated, ...
```

That workflow's job name changed and its context string changed with it. Had it been required, the
renaming PR would have been unmergeable.

**Corollary (one-way door)**: because the file is read from the merge ref, a PR that **deletes**
`pr-base-branch-guard.yml` produces no run at all → the required context never reports → the guard cannot
be removed without first editing the ruleset. Plan the un-require step before the require step.

**Mitigating**: `Guard PR base branch` is plain ASCII with single spaces — unlike juniper-recurrence's
`Test — torch MLP readout (Rung 2b; optional [torch] extra)`, whose em dash is already flagged as a
copy-exactly trap in `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md:171`.
Transcription risk is low; rename risk is not.

**Fix**: pin the ruleset entry to `integration_id: 15368` (juniper-recurrence already does; the eight
targets' entries must too), and treat `:53` as a frozen string with a comment saying so.

---

### F-07 — MAJOR — No sanity check on `DEFAULT_BRANCH`: an empty expansion fails every PR on every repo

**Location**: `pr-base-branch-guard.yml:59`, `:66`, `:79`

**Problem**: The script compares two raw strings and defaults to `exit 1`. If
`github.event.repository.default_branch` ever expands empty, `BASE_REF` (non-empty on any `pull_request`
event) will not equal it, the bypass label will not be present, and **every PR on every repo carrying
this file fails simultaneously** — with the only documented hatch being the one that does not work
(F-01/F-02/F-03).

**Evidence** (`:59`, `:66`, `:76-79`):

```yaml
            DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
...
            if [ "${BASE_REF}" = "${DEFAULT_BRANCH}" ]; then
...
            exit 1
```

There is no `if [ -z "${DEFAULT_BRANCH}" ]` arm anywhere in the file.

**Likelihood**: the payload field is reliably present today for `pull_request` (all 137 recurrence runs
succeeded, so it expanded correctly every time) — this is a blast-radius finding, not a
likely-tomorrow finding. The **code path** is verified; the **trigger** is not, and I mark it so.

**Fix**: three lines — if `DEFAULT_BRANCH` is empty, emit `::warning` and `exit 0`. A hygiene guard should
never be the thing that takes the fleet down.

---

## 4. Findings that MISS a stacked PR, or void the guard's value (less severe for merges)

### F-08 — MAJOR — Stale-payload re-run bypass

**Problem**: `github.event` is frozen at trigger time. A run created while the base was `main` can be
re-run *after* the PR is retargeted, and will re-post `SUCCESS` computed from the stale payload.

**Evidence** — fetched <https://docs.github.com/en/actions/reference/workflows-and-actions/contexts>, verbatim:

> `github.event`: "The full event webhook payload. ... This object is identical to the webhook payload of the event that triggered the workflow run"

> `github.base_ref`: "The `base_ref` or target branch of the pull request in a workflow run. This property is only available when the event that triggers a workflow run is either `pull_request` or `pull_request_target`."

Fetched <https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs>, verbatim:

> "The workflow will also use the same `GITHUB_SHA` (commit SHA) and `GITHUB_REF` (git ref) of the original event that triggered the workflow run."

with a window of "up to 30 days after its initial run" and "a maximum of 50 times".

**Residual uncertainty**: the fetched sentence covers `GITHUB_SHA`/`GITHUB_REF` explicitly; that the full
stored payload (hence `base_ref`) is replayed is a strong implication of the `github.event` definition but
is **not** stated verbatim on the re-run page. Marked accordingly.

**Whether it actually bypasses** depends on F-11.

---

### F-09 — MAJOR — Queued-run stale-base race (no `concurrency` group)

**Problem**: The workflow declares no `concurrency:` key (verified: `grep -n "concurrency" ` on the file
returns nothing). Nothing serialises runs. A `synchronize` run queued before a retarget carries
`base_ref: main` in its frozen payload and can complete *after* the retarget's `edited` run, writing a
newer `SUCCESS` on top of the correct `FAILURE`.

**Evidence of the timing window**: the job body executes in ~4 seconds
(`started_at 2026-08-14T01:41:56Z`, `completed_at 2026-08-14T01:42:00Z`), so the whole window is runner
queue latency — tens of seconds is ordinary.

**Note**: adding `concurrency` naively would introduce a *worse* problem — a `cancelled` run reports a
non-success conclusion on a required context. If added, it must be `cancel-in-progress: false`.

---

### F-10 — MINOR — `contains()` is case-insensitive, widening the bypass

**Location**: `pr-base-branch-guard.yml:60`

**Evidence** — fetched <https://docs.github.com/en/actions/reference/workflows-and-actions/expressions>, verbatim:

> "`contains( search, item )` Returns `true` if `search` contains `item`. If `search` is an array, this function returns `true` if the `item` is an element in the array. If `search` is a string, this function returns `true` if the `item` is a substring of `search`. **This function is not case sensitive.** Casts values to a string."

So `Stacked-PR`, `STACKED-PR`, `Stacked-Pr` all bypass. Array membership is exact-element (not substring),
so `stacked-pr-wip` does **not** match — that half of the concern is unfounded and dropped.

---

### F-11 — MAJOR — Duplicate same-name check runs coexist on one SHA; the resolution rule is UNVERIFIED

**Problem**: Because `edited` fires on title/body edits as well, the guard commonly produces **two or more
check runs with the identical name** on a single head SHA. Which one branch protection honours decides
whether F-08 and F-09 are bypasses or non-issues — and decides whether a retarget *back* to `main` clears
the earlier failure or leaves the PR wedged.

**Evidence — duplicates are real, not theoretical** (juniper-recurrence#112, one commit, base `main`):

```bash
gh api "repos/pcalnon/juniper-recurrence/commits/415c8c97/check-runs?check_name=Guard%20PR%20base%20branch" \
  --jq '.total_count, (.check_runs[] | [.id, .name, .status, .conclusion, .started_at] | @tsv)'
# 2
# 94648390642  Guard PR base branch  completed  success  2026-08-14T01:41:56Z
# 94648178584  Guard PR base branch  completed  success  2026-08-14T01:40:31Z
```

Both appear in the merge box's rollup:

```bash
gh api graphql -f query='{repository(owner:"pcalnon",name:"juniper-recurrence"){pullRequest(number:112){commits(last:1){nodes{commit{statusCheckRollup{contexts(first:100){nodes{__typename ... on CheckRun{name conclusion startedAt checkSuite{workflowRun{databaseId}}}}}}}}}}}}'
# Guard PR base branch  SUCCESS  2026-08-14T01:40:31Z  31761343605
# Guard PR base branch  SUCCESS  2026-08-14T01:41:56Z  31761414448
```

The PR was created `01:40:24` and has exactly one commit (`01:40:04`), so the second run came from a
non-`synchronize` event on an unchanged SHA — i.e. `edited` does re-trigger the guard, and does **not**
retract the earlier check run.

**Why I could not settle the resolution rule**: `filter=latest` on the REST check-runs endpoint dedupes
*within a check suite*, not across them — fetched <https://docs.github.com/en/rest/checks/runs>, verbatim:

> "Filters check runs by their `completed_at` timestamp. `latest` returns the most recent check runs."

but the two runs above are in different check suites and both survive the default filter. The
troubleshooting page addresses only the check-vs-commit-status collision — verbatim:

> "If a check and a commit status have the same name, both must pass when that name is required."

It says nothing about two *check runs* of the same name. **COULD NOT VERIFY.** Both outcomes are bad in
one direction: latest-wins makes F-08/F-09 live bypasses; all-must-pass makes a retarget-to-`main` leave a
permanent failure and wedges the PR (a merge-blocking outcome).

**Fix that closes it either way**: add `concurrency: { group: base-guard-${{ github.event.pull_request.number }}, cancel-in-progress: false }`
only if you have verified the resolution rule; otherwise reduce `types:` to the minimum that covers base
changes and label changes, so fewer duplicates are generated.

---

### F-12 — MINOR (latent) — No `merge_group` trigger, unlike its sibling workflows

**Evidence** — fetched <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks>, verbatim:

> repositories using GitHub Actions for required checks need to update workflows to include the `merge_group` event as an additional trigger, or "status checks will not be triggered when you add a pull request to a merge queue."

juniper-ml's own workflows already carry it for exactly this reason —
`ci.yml:51-54` (*"merge_group: required so every gating context re-runs on the queued merge commit"*) and
`codeql.yml:27-29` (*"the required 'Analyze (python)' context must also report on the queued merge commit,
else the merge queue stalls"*). The guard has no such trigger.

**Currently latent**: no repo's ruleset contains a `merge_queue` rule (verified across all 8 target
rulesets plus recurrence), consistent with the standing "merge queues unavailable for user-owned repos"
policy. Flagged so the guard is not the one workflow left behind if that ever changes.

---

### F-13 — MAJOR — The fail path has never executed; the guard is an all-green check

**Evidence**:

```bash
gh api --paginate "repos/pcalnon/juniper-recurrence/actions/workflows/pr-base-branch-guard.yml/runs?per_page=100" \
  --jq '.workflow_runs[] | .conclusion' | sort | uniq -c
#     137 success
```

Every run since 2026-06-17 concluded `success`. No run has taken the `exit 1` arm (`:79`), the `::error`
annotation (`:76-78`), or the label-bypass arm (`:71-73` — impossible anyway, since the label does not
exist, F-02). The workflow header asked for precisely this test and it was never done (`:38`):

> `#    Confirm the fail path once with a throwaway PR against a non-default base.`

This is the **vacuous-pass class** already catalogued for this fleet: machinery that runs, reports
`success`, and has never been shown capable of reporting anything else. It is currently a *required*
context on juniper-recurrence in that state.

**Fix**: run the header's own test on juniper-recurrence (throwaway branch → throwaway PR against it →
observe `failure` → observe the label arm → close) **before** copying anywhere.

---

### F-14 — MAJOR — `required` does not constrain the actor whose mistake this is meant to catch

**Problem**: All eight target rulesets grant `RepositoryRole 5` (repository admin) `bypass_mode: always`.
That is not a theoretical entitlement in this fleet — it is the dominant merge path.

**Evidence** — measured independently for this audit:

```bash
gh api -X GET "repos/pcalnon/juniper-ml/rulesets/rule-suites" -f time_period=month -f rule_suite_result=all \
  -f per_page=100 --paginate --jq '.[] | [.result, (if .ref=="refs/heads/main" then "main" else "topic" end)] | @tsv' | sort | uniq -c
#     401 bypass  main
#       2 fail    main
#       2 fail    topic
#     203 pass    main
#       4 pass    topic
```

**401 of 612 juniper-ml rule-suite evaluations in the last month (65.5%) were `bypass`, and every one of
them was on `refs/heads/main`.** juniper-cascor over the same window: 151 `bypass` / 54 `pass`.

Full bypass roster, identical on 7 of 8 targets:

| Actor | `bypass_mode` | Identified as |
| --- | --- | --- |
| `RepositoryRole 5` | `always` | repository admin (`pcalnon`) |
| `DeployKey` (null id) | `always` | unidentified — widest entitlement in the roster |
| Integration `29110` | `always` | `dependabot` (`gh api /apps/dependabot --jq .id` → `29110`) |
| Integration `1143301` | `always` | `copilot-swe-agent` (`gh api /apps/copilot-swe-agent --jq .id` → `1143301`) |
| Integration `4362741` | `pull_request` | release-train App (per `notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_BYPASS-ACTOR-CENSUS.md:27`; not resolvable via `/apps/{slug}`) |

**Portability delta**: `juniper-deploy`'s ruleset omits the `4362741` row (4 bypass actors, not 5).

**Consequence**: the stranded-PR incident (juniper-recurrence #7/#8) was an owner-merge defect. Making
this a required check adds a gate the owner steps over roughly two default-branch updates in three. The
guard's real value is the **annotation on the PR**, which an advisory check delivers identically.

---

### F-15 — MINOR — Fork PRs from first-time contributors produce no check run until approved

**Evidence**:

```bash
gh api repos/pcalnon/juniper-ml/actions/permissions/fork-pr-contributor-approval
# {"approval_policy":"first_time_contributors"}
gh api repos/pcalnon/juniper-recurrence/actions/permissions/fork-pr-contributor-approval
# {"approval_policy":"first_time_contributors"}
```

All nine repos are public with `allow_forking: true`. Fetched
<https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows>, verbatim:

> "When a first-time contributor submits a pull request to a public repository, a maintainer with write access may need to approve running workflows on the pull request."

**Not differential** — every existing required context has the same property — and empirically moot:
`gh pr list --state all --json isCrossRepository` returns **0** fork PRs in juniper-ml's 400-PR window and
0 in juniper-recurrence's entire history. Reported for completeness, not as a blocker.

**Also verified for fork PRs**: `github.event.repository` on a `pull_request` event is the base repo, so
`default_branch` resolves against the upstream, not the fork. No fork PR exists in this fleet to confirm
empirically; the payload semantics are documented in the `github.event` definition quoted in F-08.

---

### F-16 — COULD NOT VERIFY — Does `edited` fire on a base-branch change?

**What the guard depends on**: `edited` is the only listed type that could cover an in-place retarget.

**What I could establish**:

- `edited` **does** re-trigger the guard on an unchanged head SHA (F-11 evidence: two runs, one commit,
  84 seconds apart).
- I could **not** retrieve a verbatim GitHub sentence stating that `edited` fires when the base branch is
  changed. Three fetches of
  <https://docs.github.com/en/webhooks/webhook-events-and-payloads> (with and without `?actionType=edited`)
  returned the activity-type list but no per-action description; the page renders those client-side.
  <https://raw.githubusercontent.com/octokit/webhooks/main/payload-schemas/schema/pull_request/edited.schema.json>
  returned HTTP 404 and the path is not present in the repo's contents API.
- I could **not** verify it empirically either: a GraphQL scan of the last 100 PRs of juniper-ml and
  juniper-cascor for `BASE_REF_CHANGED_EVENT` returned **zero** matching timeline nodes.

```bash
gh api graphql -f query='{repository(owner:"pcalnon",name:"juniper-cascor"){pullRequest(number:441){timelineItems(first:40,itemTypes:[BASE_REF_CHANGED_EVENT]){totalCount nodes{__typename}}}}}' \
  --jq '.data.repository.pullRequest.timelineItems | {totalCount, types: [.nodes[].__typename] | group_by(.) | map({t:.[0], n:length})}'
# {"totalCount":37,"types":[]}       <- filter honoured on nodes; totalCount is unfiltered
```

**What this reveals instead**: this fleet **does not retarget in place**. Its practice is close-and-reopen
— `gh api -X GET search/issues -f q='org:pcalnon is:pr retarget in:title'` returns juniper-cascor #189
("[retarget #184]"), #190 ("[retarget #187]"), #214 ("[retarget #200]"), #215 ("[retarget #201]"), each a
*new* PR. A new PR fires `opened`, which the guard covers correctly.

**Consequence**: the guard's failure message advises "Edit -> change base" (`:78`) — a workflow this fleet
has never used, on a trigger path this audit could not confirm. Recommend changing the message to
"close this PR and open a new one against `main`", which is both the verified fleet practice and the only
path that reliably re-runs *all* the other required contexts (F-03).

---

## 5. A5 — per-repo portability

**The dynamic-default-branch claim (`:28-29`) holds.** All nine repos have `default_branch: main`:

```bash
gh api repos/pcalnon/<repo> --jq '[.name,.default_branch,(.private|tostring),(.allow_forking|tostring),(.archived|tostring)]|@tsv'
# juniper-ml             main  false  true  false
# juniper-cascor         main  false  true  false
# juniper-canopy         main  false  true  false
# juniper-data           main  false  true  false
# juniper-data-client    main  false  true  false
# juniper-cascor-client  main  false  true  false
# juniper-cascor-worker  main  false  true  false
# juniper-deploy         main  false  true  false
# juniper-recurrence     main  false  true  false
```

No repo has a `develop` branch (`gh api repos/pcalnon/juniper-ml/branches/develop` → 404; same for
juniper-cascor), even though eight `ci.yml` files declare `develop` a supported PR base. If a `develop`
branch were ever created and used, **the guard would fail every PR targeting it** — a design-intent
conflict between the guard and the fleet's own CI configuration. Low likelihood today; note it.

**Differences found across the 8 targets**:

| Axis | Finding |
| --- | --- |
| Default branch | Identical (`main`) on all 9 — no per-repo edit needed. **PASS** |
| Actions enabled | `enabled: true` on all 9. **PASS** |
| `allowed_actions` | `selected` on all 8 targets; `all` on juniper-recurrence. **Irrelevant here** — the guard contains zero `uses:` steps (`grep -n "uses:"` → no match), so no allow-list can block it. |
| `sha_pinning_required` | `false` on all 9. No impact. |
| `ci.yml` PR branch filter | `[main, develop]` on all 8 → **F-03** |
| Ruleset bypass roster | 5 actors on 7 repos; **juniper-deploy has 4** (no `4362741`) |
| `strict_required_status_checks_policy` | `true` on all 8. Does **not** rescue F-11: a head cut from `feature/x` is already "up to date" with `feature/x`, so a retarget need not force a new SHA. |
| Required-context naming style | deploy uses `Pre-commit` (unsuffixed) where the others use `Pre-commit (Python 3.12/3.13/3.14)`; unrelated to this guard but confirms per-repo context lists are hand-maintained. |
| Merge methods | `["merge","squash"]` on all 8 primary rulesets (rebase excluded) |
| yamllint | Ecosystem `.yamllint.yaml` sets `line-length: max 512, level: warning`; the guard's longest line is 244 chars → **no pre-commit breakage on adoption. PASS** |
| Name collision | `gh api -X GET search/code -f q='org:pcalnon "Guard PR base branch"'` → 4 hits, all documentation plus the one workflow. No existing job produces this context. **PASS** |

---

## 6. A6 — legitimate stacked work today

**Answer: none. Requiring this guard today breaks zero open PRs.**

```bash
gh api graphql -f query='{a:repository(owner:"pcalnon",name:"juniper-ml"){pullRequests(states:OPEN){totalCount}} ... }'
# ml 2, cascor 0, canopy 0, data 0, data-client 0, cascor-client 0, cascor-worker 0, deploy 0, recurrence 0
```

`gh pr list --repo pcalnon/<repo> --state open --limit 300 --json baseRefName --jq '.[]|select(.baseRefName!="main")'`
returns nothing for all nine repos. The only two open PRs anywhere (juniper-ml #1205, #1206) both target
`main` — but see **F-04**: they are still wedged by rollout ordering.

**Historically, though, stacked merges are a real and recurring practice** — 18 merged non-default-base
PRs across the nine repos:

```bash
gh api -X GET search/issues -f q='org:pcalnon is:pr is:merged -base:main' -f per_page=100 \
  --jq '.items[] | [(.repository_url|split("/")|last), .number, .title] | @tsv'
```

| Repo | Count | PRs |
| --- | --- | --- |
| juniper-cascor | 8 | #126, #171, #173, #184, #187, #190, #200, #201 |
| juniper-deploy | 4 | #20, #22, #23, #41 |
| juniper-ml | 2 | #17, #18 |
| juniper-recurrence | 2 | #7, #8 |
| juniper-canopy | 1 | #365 |
| juniper-data | 1 | #30 |

(The search's `total_count` of 25 includes 5 in `JuniperLegacy` and 2 in `samich`, both out of scope.)

**The motivating incident is confirmed**:

```bash
gh api repos/pcalnon/juniper-recurrence/pulls/8 --jq '{number,base:.base.ref,head:.head.ref,merged:.merged,merged_at:.merged_at}'
# {"base":"feature/ws4b-app-routes","head":"feature/ws4b-app-publish-docs","merged":true,"merged_at":"2026-06-16T11:29:39Z","number":8}
gh api repos/pcalnon/juniper-recurrence/pulls/7 --jq '{number,base:.base.ref,head:.head.ref,merged:.merged,merged_at:.merged_at}'
# {"base":"feature/ws4b-app-skeleton","head":"feature/ws4b-app-routes","merged":true,"merged_at":"2026-06-16T11:27:53Z","number":7}
```

The guard's premise is sound and it would have flagged all 18. Note that 8 of the 18 (cascor) were
*deliberate* stacks with `[stacked on #NNN]` in the title — i.e. the workflow the label was meant to
permit is a workflow this team really does use, and F-03 says the opt-out cannot work.

---

## 7. Verified passes (checked, and not a problem — recorded so they are not re-litigated)

| # | Concern | Verdict | Evidence |
| --- | --- | --- | --- |
| P-1 | Draft PRs produce no check run | **UNFOUNDED** | juniper-ml#995 (`draft: true`) carries 21 check runs on head `418f1eb0` |
| P-2 | `allowed_actions: selected` would block the guard on the 8 targets | **UNFOUNDED** | zero `uses:` steps in the file |
| P-3 | Shell / workflow-command injection via branch name | **UNFOUNDED** | all `${{ }}` are confined to `env:` (`:58-60`); the `run:` body uses `${VAR}` only. Git refnames cannot contain `:`, so `::` annotation forging is impossible. (A `%`-escape in a branch name could add a spurious *log annotation*; it cannot change the exit code, and `permissions: contents: read` grants nothing.) |
| P-4 | Job-level `if:` could make it a silent skipped-pass | **NOT PRESENT TODAY** | no `if:` in the file. Worth pinning: GitHub counts "success, skipped, and neutral" as successful required statuses, so adding an `if:` later would silently void the guard. |
| P-5 | Path filters could skip it | **UNFOUNDED** | no `paths:`/`paths-ignore:` in the file — correct, and necessary for a required context |
| P-6 | Branch filters could skip it | **UNFOUNDED** | no `on.pull_request.branches` in the file — correct; adding one would be fatal (it must run on non-`main` bases by definition) |
| P-7 | `contains()` substring match could let `stacked-pr-wip` bypass | **UNFOUNDED** | array form is exact-element membership (docs, F-10) |
| P-8 | yamllint / pre-commit would reject the file on adoption | **UNFOUNDED** | 244-char max line vs `line-length: max 512, level: warning` |
| P-9 | Job would need a checkout / token / network | **UNFOUNDED** | no `actions/checkout`, no API call; `permissions: contents: read` suffices; ~4 s runtime |

---

## 8. Summary

| Severity | Count | IDs |
| --- | --- | --- |
| **Blocker** (wrongly blocks merges) | 5 | F-01, F-03, F-04, F-05, F-06 |
| **Major** | 7 | F-02, F-07, F-08, F-09, F-11, F-13, F-14 (F-02 and F-07 are the merge-blocking majors; F-11 is also a could-not-verify) |
| **Minor** | 3 | F-10, F-12, F-15 |
| **Could not verify** | 2 | F-11 (duplicate check-run resolution rule), F-16 (`edited` on base change) |
| **Verified pass** | 9 | P-1 … P-9 |

### Could not check, and why

- **F-11 resolution rule** — GitHub does not document how branch protection resolves two *check runs* of
  the same name in different check suites on one SHA. Settling it requires creating a PR that produces a
  failure then a success (or vice versa) and observing the merge box. Out of scope for a read-only audit.
- **F-16 `edited` semantics** — the per-action webhook descriptions are client-rendered and were not
  retrievable; and this fleet has never retargeted a PR in place, so there is no historical event to
  inspect.
- **`DeployKey` bypass actor identity** — `actor_id: null`; there is no API that resolves it. Already
  flagged IDENTIFY-FIRST in `notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_BYPASS-ACTOR-CENSUS.md:150`.
- **Integration `4362741`** — not resolvable via `/apps/{slug}` (tried `cursor`, `codex`,
  `chatgpt-codex-connector`, `gemini-code-assist`, `claude`); identified only by cross-reference to the
  same-day census note.

### Minimum change set before requiring this context anywhere

1. Add `labeled, unlabeled` to `types:` (F-01).
2. Create the `stacked-pr` label in each repo (F-02).
3. Rewrite the failure message: "close this PR and reopen it against `main`" — not "Edit -> change base"
   (F-03, F-16). Drop the label sentence unless F-03 is separately resolved.
4. Add an empty-`DEFAULT_BRANCH` guard that warns and exits 0 (F-07).
5. Run the fail-path test the header already asks for (F-13, `:38`).
6. Land the file on all 8, wait for every open PR to receive an event, **then** edit the rulesets — with
   `integration_id: 15368` on every new entry, and the exact string `Guard PR base branch` (F-04, F-06).
7. Write down that the file cannot be deleted or its job renamed without un-requiring the context first
   (F-06 corollary).

Until steps 1–5 are done, **advisory only**. The guard's value is the annotation, and an advisory check
delivers that at zero merge-blocking risk — which matters most given F-14, where the actor this guard
exists to protect bypasses the ruleset on 65% of default-branch updates.
