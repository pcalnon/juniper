# Juniper PyPI Release-Train — Operator Runbook

**Project**: Juniper — PyPI release-train automation
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.2.1
**Last Updated**: 2026-07-26

---

This runbook is the **operator's guide** to the automated PyPI release-train orchestrated by
[`.github/workflows/release-train.yml`](../.github/workflows/release-train.yml). It documents the four
run modes and exactly what each writes, the mode-resolution precedence, the day-to-day cheat-sheet, the
per-package HALT catalog, and the rollback procedures. It is the Phase 4.3 deliverable of the
[PyPI release-train plan](JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md)
(§12 step 4.3).

Every claim below is grounded in the real code or plan — cited as `path:line` or `§section`. Nothing here
describes behavior the code does not implement.

## 0. TL;DR — the two things an operator must remember

1. **`RELEASE_TRAIN_MODE=off` is the instant kill switch.** Set the repo variable to `off` (or dispatch
   with `mode=off`) and the next run is a green no-op: detection is skipped and both write jobs are
   unreachable (release-train plan §11; `release-train.yml:182-190` quiesce step).
2. **The owner still holds both gates.** The train never bumps a version without the owner-approved
   proposal PR (Gate 1) and never deploys to PyPI without the owner approving the `pypi` environment
   (Gate 2). The train automates only the middle arc (plan §5.3; `ceremony.py:1-11`).

## 1. The four modes and exactly what each writes

Mode is resolved once by the detect job's `id: mode` step (`release-train.yml:161-178`) and exposed as
`needs.detect.outputs.mode`; the two write jobs gate on it.

| Mode | Runs | Writes | Gate on |
|---|---|---|---|
| **`off`** | nothing beyond mode resolution | **nothing** — detection is skipped, both write jobs unreachable | quiesce step `release-train.yml:182-190` |
| **`report`** (default) | detect job only | **nothing** to GitHub/PyPI — only a step-summary table + the `release-manifest.json` run artifact + a non-blocking Slack post | detect job, workflow-level `contents: read` (`release-train.yml:139`) |
| **`propose`** | detect + **propose** job | opens **standard-gated** release-proposal PRs (version bump + CHANGELOG move + drafted notes + pin / `_version.py` dunder co-changes); **no** Releases, **no** (Test)PyPI | `propose` job `if: needs.detect.outputs.mode == 'propose'` (`release-train.yml:382`) |
| **`ceremony`** | detect + **ceremony** job | for `BUMPED_NOT_RELEASED` packages: opens the add-only notes-archive PR (central in juniper-ml, via a **GitHub-signed API commit** → auto-merges hands-free), enables `--auto`, **cuts the Release** on the owning repo, monitors its publish run to `PENDING_PYPI_APPROVAL`; **never** touches (Test)PyPI | `ceremony` job `if: needs.detect.outputs.mode == 'ceremony'` (`release-train.yml:587`) |

Notes:

- `report` is the **only** mode the daily cron ever runs (`RELEASE_TRAIN_MODE` defaults to `report`;
  `propose`/`ceremony` are opt-in via `workflow_dispatch` or an owner-set repo variable). An unknown
  value warns and degrades to `report` (`release-train.yml:173-176`).
- Both write jobs carry job-level `permissions: {contents: write, pull-requests: write}` and **nothing
  broader** — no `id-token`, no `environments`, no `deployments` (`release-train.yml:388-389`,
  `593-595`). This is pinned by `tests/test_release_train_workflow_guard.py`.
- `propose` and `ceremony` gate on **distinct** modes, so at most one write lane runs per run.

## 2. Mode-resolution precedence

The resolver (`release-train.yml:171`) is `mode="${MODE_INPUT:-${MODE_VAR:-report}}"`, i.e.:

```text
workflow_dispatch input `mode`   (highest precedence)
  > repo variable RELEASE_TRAIN_MODE
    > "report"                    (default)
```

- A `workflow_dispatch` `mode` input **wins** over the repo variable (dispatch `mode=propose` while the
  variable is `off` → `propose`).
- An empty input falls through to the repo variable; an empty variable falls through to `report`.
- Any value other than `off|report|propose|ceremony` warns (`::warning::`) and resolves to `report`
  (`release-train.yml:172-177`).

This exact matrix (including `ceremony` now first-class, and the input-over-variable precedence) is
rehearsed by running the workflow's own resolver shell in
`tests/test_release_train_workflow_guard.py::ModeResolutionMatrixTest`.

## 3. Normal-operations cheat-sheet

### 3.1 Reading the daily cron (report mode)

The cron fires daily at `0 13 * * *` UTC = 08:00 America/Chicago under CDT (`release-train.yml:115`;
Q-CADENCE, plan §12 step 1.3). Each run produces:

- a **step-summary classification table** (per-package `classification` + proposed bump), rendered by the
  detect job's "Render step summary" step;
- the **`release-manifest.json`** run artifact (the machine-readable manifest `detect.py --json` emits);
- a **non-blocking Slack post** to the Juniper channel when `SLACK_WEBHOOK_URL` is set
  (`release-train.yml:325-366`) — `Release train (<mode> mode): … Needs release action: …` + the run URL
  (`release-train.yml:356-358`). A missing secret skips the post and a post failure never fails the run.

Detector classifications you will see (`detect.py:90-94`): `UP_TO_DATE`, `UNRELEASED_CHANGES` (has
release-worthy CHANGELOG changes not yet in a proposal), `BUMPED_NOT_RELEASED` (declared > released; the
**ceremonial** class), `SHIP_UNCERTAIN`, `NEVER_RELEASED`. **Detector exit 1 ("action needed") is a
NORMAL green outcome** — only a hard source error (exit ≥ 2) fails the run (`release-train.yml`, detect
step; plan §11).

### 3.2 Dispatching `propose` against specific packages (Gate 1)

```bash
# Open standard-gated proposal PRs for one (or a few) packages. Empty `packages` = all eligible.
gh workflow run release-train.yml -f mode=propose -f packages=juniper-observability
```

- The `packages` input is whitespace/comma-separated `pypi_name`s, validated against the pypi-name
  charset (`release-train.yml`, the propose run step's parser). Empty = all eligible.
- The resulting PRs are **standard-gated**: the owner reviews and merges them. This is **Gate 1** (the
  version bump only ships with owner approval; plan §5.3).
- **In-repo pilot vs cross-repo**: with the GitHub App token minted (§7 below) sibling-repo packages get
  PRs in their own repos; on the degraded no-App path only juniper-ml packages are proposed and siblings
  are skipped with a clear reason.

#### When propose skips (refusal stubs)

`build_proposal` returns a **skipped** stub (`skipped_reason` set; no PR opened) when inputs are
unusable — it never invents a shippable bump or an empty CHANGELOG section (`propose.py:1029-1107`).
`execute_proposal` already no-ops on `skipped`, so these are dry-run / JSON / step-summary signals.
Coverage: open juniper-ml#749 (`BuildProposalTest` refusal cases).

| `skipped_reason` contains | Cause | Operator response |
|---|---|---|
| `dup-guard: open release PR already exists` | Concurrent / prior proposal still open | Review / merge / close the existing PR; do not force a second |
| `changelog conflict -- refuse to auto-author` | Detector flagged Unreleased vs ship evidence mismatch | Fix CHANGELOG or ship evidence by hand; re-run `report` then `propose` |
| `no proposable version` (`bump=none` / missing `proposed_version`) | SemVer inputs empty (often test/docs-only tip → no ship) | Confirm detect did not invent `UNRELEASED_CHANGES`; no Gate 1 PR expected |
| `could not read the version file` | Missing `pyproject.toml` / `_version.py` for the package path | Restore the version file on `main`; re-run propose |
| `could not locate the version assignment` | File present but assignment unparseable | Fix the version assignment syntax; re-run propose |
| `CHANGELOG move refused` (`no content to move` / missing Unreleased heading) | Empty or missing `## [Unreleased]` body | Add real Unreleased bullets (or drop the false `UNRELEASED_CHANGES`); never invent an empty section |
| `could not read …/CHANGELOG.md` | CHANGELOG missing after version staging | Restore CHANGELOG; re-run propose |

**Upstream of propose — test paths never ship.** `classify_change` discounts `_is_test_path` matches
(`tests/` / `test/` path segments, `test_*.py`, `*_test.py`, `conftest.py`) as `nonship` **before** the
substantive-hunk filter (`detect.py:658-663`, `735-736`). A tip that only touches tests will not become
`UNRELEASED_CHANGES` and therefore will not open a Gate 1 PR — even if the hunks look like "real code".
Coverage: juniper-ml#749 (`test_test_paths_are_nonship_even_with_code_hunks`).

#### Gate 1 review — static `_version.py` dunder lockstep (ml#701 / juniper-ml#710)

All five in-repo **static** packages (`juniper-ci-tools`, `juniper-config-tools`, `juniper-doc-tools`,
`juniper-observability`, `juniper-service-core`) also ship a `_version.py` `__version__` dunder. A
pyproject-only bump ships a wheel whose metadata is right while `__version__` lies (ci-tools 0.7.0 /
service-core 0.5.0; design
[`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md);
implementation juniper-ml#710).

When reviewing a Gate 1 proposal for one of those packages, expect:

| Signal in the proposal PR | Meaning | Operator action |
|---|---|---|
| Diff edits **both** `pyproject.toml` `[project].version` **and** `<import>/_version.py` | Normal lockstep co-change (`propose.py` step 3a; auto-detected by file presence, no registry field). Single- or double-quoted `__version__` both count. | Merge when the rest of the proposal looks right |
| Body names a lockstep `__version__` dunder co-change + checklist "included in this PR" | Train already applied the dunder edit | No extra manual edit |
| Checklist item **REQUIRED** (`__version__` assignment not found); body does **not** claim a lockstep co-change | File exists but is unparseable — train left it alone (AGENTS.md-header precedent) | Edit `__version__` by hand in the same PR before merge |
| Diff touches **only** `pyproject.toml` for version; **no** dunder checklist item; `__version__` already equals `to_version` | Partial heal / re-entry — step 3a left a correct dunder alone (silent success; juniper-ml#712) | Confirm the dunder is already at the proposed version, then merge |
| Diff touches **only** `pyproject.toml` for version; dunder still at `from_version` (or missing) | Pre-#710 / stale train / bug — the old failure class | Do **not** merge as-is; add the dunder bump (or re-dispatch `propose`) |

**Pitfall (pre-#712 only):** if a proposal still shows checklist **REQUIRED** while `__version__` already equals the proposed version, that is a false alarm from the #710 checklist shape — do **not** "fix" a correct dunder; merge after confirming, or re-dispatch `propose` once #712 is on main.

Always-on CI gate (train or no train; lands with juniper-ml#710): `tests/test_release_train_registry.py`
(`VersionDunderLockstepTest`) asserts pyproject == dunder for every in-repo static-with-dunder package.
Dynamic packages (`juniper-model-core` + the three recurrence packages) are exempt — their `_version.py`
**is** the version source. Manual hand-bumps outside the train must still move both files together.

### 3.3 Dispatching `ceremony` against specific packages (drives toward Gate 2)

```bash
# Run the exempt-archive + Release ceremony for BUMPED_NOT_RELEASED packages.
gh workflow run release-train.yml -f mode=ceremony -f packages=juniper-observability
```

For each `BUMPED_NOT_RELEASED` package the ceremony (`ceremony.py:1-45`): runs the §8 preconditions,
builds the central notes file, opens the **add-only** archive PR (always in juniper-ml — the central
`notes/releases/` archive, plan §10.2), enables `gh pr merge --auto --squash` behind the required
archive-guard check, **cuts the Release** on the owning repo (`gh release create <tag> --latest=false`;
the Release **creates** the tag, so deliberately **no** `--verify-tag`, `ceremony.py:225-226`), and
monitors the triggered publish run.

- **The archive PR auto-merges hands-free.** The archive branch **and** its single-file commit are
  created through the GitHub API — a `git/refs` POST plus a `createCommitOnBranch` GraphQL mutation
  (`ceremony.py:open_archive_pr`). A commit made through GitHub's API under the App / `GITHUB_TOKEN`
  identity is **GitHub-signed / Verified**, so the exempt archive PR satisfies the juniper-ml ruleset's
  `required_signatures` rule and the armed `--auto` merge **completes with zero clicks**. (A plain
  runner-side `git commit` is unsigned and left an all-green archive PR BLOCKED behind that rule until an
  owner admin one-click — 2026-07-23 run 30051952226 / ml#707; the API commit removes that block with no
  security-posture change.) **Owner one-click is now only the degraded/manual fallback** — e.g. if
  `allow_auto_merge` is off (a graceful degrade, not a HALT) or the auto-merge never lands.
- The monitor polls a bounded ~15-minute wall clock (`--monitor-timeout 900`,
  `release-train.yml:733`; `DEFAULT_MONITOR_TIMEOUT_SECONDS`, `ceremony.py:137`) until the run parks at
  the owner-gated `pypi` environment. **`PENDING_PYPI_APPROVAL`** is SUCCESS for the train (plan §5.1;
  `ceremony.py:526-531`) when either:
  - the **run** top-level `status` is `waiting`, **or**
  - TestPyPI jobs all succeeded **and** every non-TestPyPI `*pypi*` job has `status` in
    `{waiting, queued, pending, ""}` (belt-and-suspenders: the run may still show `in_progress` before
    GitHub flips it to `waiting`). Misclassifying `queued` / `pending` / `""` as `IN_PROGRESS` would
    keep ceremony polling past Gate 2. Coverage: juniper-ml#749
    (`test_job_level_queued_pending_empty_statuses_park_at_gate`).
  If the run is still building at timeout it reports `IN_PROGRESS` (honest; re-run ceremony mode to
  resume — it is idempotent).
- **Gate 2 is yours**: the publish workflow's `pypi`-environment deploy job waits for the owner to
  approve. The train never approves it (§7). Approve it in the run's environment-review UI when ready.

### 3.4 The two owner gates (never automated)

| Gate | What it guards | Who | Where |
|---|---|---|---|
| **Gate 1** | the version bump (+ static `_version.py` dunder lockstep when present) | owner reviews + merges the proposal PR | the standard-gated `propose` PR |
| **Gate 2** | the PyPI deploy | owner approves the `pypi` environment | the publish run's environment review |

Neither gate is ever a release-train identity action (plan §9.3; enforced in code by
`ceremony.py:_assert_gh_allowed`, §7 below).

## 4. The §8 "nothing unexpected" HALT catalog

Each precondition is checked **per package** before the ceremony proceeds; **any failure → HALT that
package, open/update a deduplicated GitHub issue, never proceed** — and a halt on one package does not
block the others (plan §8; `ceremony.py:22-31`). A HALT is a **normal green outcome** of the run (it does
not turn the run red); it is surfaced in the ceremony step summary, a dedup issue, and Slack. The
`ceremony.py` exit is `1` when any package HALTED (owner attention), `2` only on an invocation error
(`ceremony.py:71-72`).

| `reason_key` | Trigger | Code | Operator response |
|---|---|---|---|
| `main-ci-not-green` | target `main` CI latest conclusion ≠ `success` | `ceremony.py:735` | Fix `main` CI (owner rule: check main green before blaming a red PR); re-run ceremony. |
| `declared-lt-released-anomaly` | declared version < the version PyPI already serves (yank/rollback) | `ceremony.py:724` | Investigate the PyPI yank/rollback manually; do NOT release. Reconcile the declared version. |
| `pypi-truth-missing` | manifest said released, but PyPI now returns no version | `ceremony.py:726` | A first-publish/yank a human must resolve — confirm the trusted-publisher config (procedure §3.3) before re-running. |
| `changelog-section-missing` | no non-empty `CHANGELOG [<version>]` section to source the notes | `ceremony.py:741` | The proposal PR (Gate 1) should have created it — merge the proposal first, or add the section, then re-run. |
| `missing-declared-version` | manifest has no `declared_version` for a `BUMPED_NOT_RELEASED` pkg | `ceremony.py:711` | A malformed manifest — re-run detection (`report` mode) to regenerate it. |
| `not-in-registry` | package is `BUMPED_NOT_RELEASED` in the manifest but absent from `registry.yaml` | `ceremony.py` (`_plans_for`) | Add the package to `util/release_train/registry.yaml` (registry lint gates it). |
| `testpypi-verify-failed` | (during the monitor) the publish workflow's TestPyPI install-verify failed before Gate 2 | `ceremony.py:876` | The run is not healthy — inspect the publish run's TestPyPI job; fix and re-cut is idempotent. |

**HALT-issue degradation (Phase 4.3).** Filing the dedup issue is **best-effort**: if the `gh issue`
API itself fails — most plausibly the cross-repo App token lacking the **Issues** permission — the
upsert degrades gracefully to a loud log line + a step-summary flag (`halt_issue_failed`), and the
package stays HALTED without crashing the run (`ceremony.py:_file_halt_issue`, `801`). When you see
"HALT issue could NOT be filed" in the ceremony step summary, **file the issue manually** (or grant the
App the Issues permission — §8). The HALT itself is still surfaced in the summary and Slack.

## 5. Rollback procedures

### 5.1 Quiesce the whole train instantly (no code change)

```bash
gh variable set RELEASE_TRAIN_MODE --body off        # repo variable; next run is a green no-op
# or, for a single run:  gh workflow run release-train.yml -f mode=off
```

`off` skips detection and makes both write jobs unreachable (`release-train.yml:182-190`; plan §9.4/§11).
This is the primary rollback/disable switch.

### 5.2 Pause all writes but keep detection running

```bash
gh variable set RELEASE_TRAIN_MODE --body report     # detection continues; propose/ceremony disabled
```

`report` keeps the daily classification table + Slack signal while guaranteeing no PRs/Releases
(plan §11 "Rollback / disable").

### 5.3 Undo a bad Release (and its tag)

The ceremony's Release **creates** the sub-package tag (`ceremony.py:201-202`; procedure §11.4). To
recover a Release that should not have been cut — **before** the owner approves Gate 2 (nothing has
reached PyPI yet, since the deploy job is parked at the `pypi` environment):

```bash
gh release delete <tag> --repo pcalnon/<owning-repo> --cleanup-tag --yes
# if --cleanup-tag is unavailable, delete the tag explicitly:
git push --delete origin <tag>            # e.g. juniper-observability-v0.5.0
```

- **Never pre-create/push the `juniper-<pkg>-v*` tag by hand** before the ceremony. The Release must
  create it; the ceremony deliberately passes no `--verify-tag` (and `ceremony.py:_assert_gh_allowed`
  forbids `--verify-tag`, `ceremony.py:201-202`). A pre-existing tag changes what the tag-triggered
  publish workflow checks out (the tag-ref gotcha; §8).
- Deleting the Release + tag also lets a corrected re-run start clean: the ceremony is idempotent and
  re-computes state from PyPI/Release truth (plan §8 last row; `ceremony.py:53-56`).

### 5.4 Close a bad proposal PR

Proposal PRs are standard-gated and merge nothing on their own. Simply close the PR (and delete its
branch); the dup-guard means a corrected re-dispatch will open a fresh one rather than duplicate it
(`propose.py` dup-guard). No environment or PyPI state is touched by a proposal PR (plan §7.4).

### 5.5 The immutable-index recovery stance (§11)

**PyPI and TestPyPI files are immutable**, and the publish steps use `skip-existing: true`
(plan §8 "Idempotent re-entry", citing `publish-service-core.yml:139,185`). Consequences for recovery:

- A **partial run is safe to re-enter**: a re-run re-computes state from PyPI/Release truth. If PyPI
  already serves the target version the ceremony is a no-op (`ALREADY_RELEASED`); if the Release tag
  already exists it resumes at the monitor (never re-cutting, never duplicating the archive PR)
  (`ceremony.py:53-56`).
- You **cannot** "un-publish" a version by overwriting it — if a bad version reaches PyPI, **yank** it on
  PyPI and ship a fixed higher version. The train will then see the yank and classify accordingly.
- Only **one train runs at a time** (`concurrency: group: release-train, cancel-in-progress: false`,
  `release-train.yml`), so two runs never race the same immutable index (plan §8).

## 6. Owner setup actions (one-time, provisioning)

These are **not** train actions — they are owner console/CLI actions the train depends on:

| Item | What | Why |
|---|---|---|
| `RELEASE_TRAIN_MODE` | repo variable (`off`/`report`/`propose`/`ceremony`) | the mode + kill switch (§2/§5) |
| `RELEASE_TRAIN_APP_ID` | repo variable = the GitHub App's id | gates the App-token mint step (`release-train.yml:399`, `605`) |
| `RELEASE_TRAIN_APP_PRIVATE_KEY` | repo secret = the App private key | minted into the cross-repo token (§7) |
| `SLACK_WEBHOOK_URL` | repo secret (optional) | the non-blocking Slack summary (`release-train.yml:325-366`) |

**Verify-before-first-cron (mandatory).** After any change to the train, trigger it once with
`gh workflow run release-train.yml` and confirm the run behaves before trusting the daily cron
(plan §11; a lint-green workflow is not a runtime-green workflow).

## 7. The App identity & the R7 invariant (in operator terms)

**Scope.** The cross-repo write identity is a **GitHub App installation token** minted per write job
(`actions/create-github-app-token`, SHA-pinned, `release-train.yml:400`, `606`), scoped to exactly the
**8 publishing repos** (juniper-ml, -data, -data-client, -cascor, -cascor-client, -cascor-worker,
-canopy, -recurrence). The mint step is gated on `vars.RELEASE_TRAIN_APP_ID` so an absent App config
**degrades gracefully** to the built-in single-repo `GITHUB_TOKEN`.

**What the identity may do (and nothing else) — R7 (plan §9.3).** The ceremony routes every `gh` call
through `ceremony.py:_assert_gh_allowed` (`197`), which permits **exactly**
`{pr create, pr merge --auto, release create, run list/view, issue create/edit}`
(`GH_MUTATING_SURFACE`, `ceremony.py:150`) — **plus the archive lane's two GitHub-signed-commit calls**
(a `repos/<owner>/<repo>/git/refs` POST and a `createCommitOnBranch` GraphQL mutation) — and rejects any
`environment` / `deployment` / `review` / `--admin` token (`GH_FORBIDDEN_TOKENS`, `ceremony.py:177`), a
bare `pr merge` without `--auto`, or a `release create --verify-tag`. `api` **stays forbidden for the
general surface**; the sole carve-out is those two archive-lane calls, dispatched to the sibling
assertion `_assert_api_allowed` (`ceremony.py:283`) which accepts ONLY a `git/refs` POST creating a
`refs/heads/*` ref or a `createCommitOnBranch` body with `repoWithOwner` bound — every other `gh api`
(a different path, a different mutation, a non-POST ref write, an out-of-allowlist repo) raises
`SeamViolation`. Every `--repo` — and both archive-lane calls' repo bind — is bounded to the 8
publishing repos. **The identity is never a `pypi` environment reviewer and never approves/mutates a
deployment** — PyPI approval stays owner-only (Gate 2). The workflow-level `contents: read` plus the two
mode-gated write jobs are pinned by `tests/test_release_train_workflow_guard.py`; the archive-lane api
carve-out and its negative case are pinned by `tests/test_release_train_ceremony.py`.

## 8. Known limitations (accepted)

1. **Degraded no-App mode (in-repo only).** When `RELEASE_TRAIN_APP_ID` is unset, `propose`/`ceremony`
   run on the built-in `GITHUB_TOKEN` and **skip sibling-repo packages** with a clear reason
   (`ceremony.py:writable_repo_skip_reason`, `377`); only juniper-ml packages (the meta + 6 sub-packages)
   are acted on. Additionally, a PR opened with `GITHUB_TOKEN` does **not** auto-trigger CI (GitHub's
   recursion guard), so a proposal PR shows no checks until re-triggered (close/reopen, or push an empty
   commit). When the App token IS minted, PRs are opened by the App identity and CI runs normally.
2. **Issues permission (HALT-issue degradation).** The App installation may not have the **Issues**
   permission (owner-grantable later). Until then, a HALT that would file a dedup issue in a sibling repo
   degrades to a loud log + step-summary flag and does not crash the run (§4). Operator response: file
   the issue manually, or grant the App the Issues permission on the 8 repos.
3. **Tag-ref workflow gotcha (0.4 backfill).** Some legacy sub-package releases were shipped **tag-only**
   (a bare `git push <tag>`) rather than by cutting a GitHub Release — the convention now being restored
   (CLAUDE.md "Release convention"; plan §12 step 0.4). The ceremony **always cuts a Release** (never a
   bare tag) and never pre-creates the tag, so it does not reproduce that gotcha. Operator corollary:
   when recovering by hand, **cut a Release** (or delete Release + tag together, §5.3) — never push a
   bare `juniper-<pkg>-v*` tag, which would trigger the tag/`release`-driven publish workflow against a
   tag the Release did not create.
4. **Cross-repo pilot is owner-triggered.** No cross-repo write has run live from this automation yet;
   the ceremony's live cross-repo path is exercised only under owner-initiated dispatch. Hermetic tests
   + `--dry-run` cover the logic (`tests/test_release_train_ceremony.py`).
5. **Archive-PR signature gate (RESOLVED 2026-07-23).** The juniper-ml ruleset's `required_signatures`
   rule evaluates a PR's source commits, so the exempt archive PR only auto-merges if its commit is
   signed. It now is: the archive branch + commit are created through the GitHub API (`git/refs` POST +
   `createCommitOnBranch`), yielding a **GitHub-signed / Verified** commit under the App / `GITHUB_TOKEN`
   identity (§3.3). Previously the commit was a plain unsigned runner-side `git commit`, so an all-green
   archive PR stayed BLOCKED behind that rule until an owner admin one-click (2026-07-23 run 30051952226
   / ml#707). Owner one-click is now only the degraded/manual fallback (e.g. `allow_auto_merge` off). No
   security-posture change — the PyPI deploy still waits at the owner-gated `pypi` environment (Gate 2).
   The **live proof** (an archive PR auto-merging with zero clicks) rides the next real ceremony dispatch.

## 9. Quick reference

```bash
# Read the latest report run
gh run list --workflow release-train.yml --limit 5
gh run view <run-id>                         # step summary + artifacts

# Kill switch / pause
gh variable set RELEASE_TRAIN_MODE --body off      # quiesce entirely
gh variable set RELEASE_TRAIN_MODE --body report   # detection only, no writes

# Opt-in write runs (owner)
gh workflow run release-train.yml -f mode=propose  -f packages=juniper-observability   # Gate 1 PRs
gh workflow run release-train.yml -f mode=ceremony -f packages=juniper-observability   # archive PR + Release -> Gate 2

# Recover a mis-cut Release (before Gate 2 approval)
gh release delete <tag> --repo pcalnon/<owning-repo> --cleanup-tag --yes
```

## 10. References

- Plan: [`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md)
  — §5 states, §5.4 atomicity co-changes (incl. static `_version.py` lockstep), §8 HALT preconditions,
  §9.2-9.4 identity + R7 + rollback switch, §10.2 central archive, §11 failure/observability/rollback,
  §12 phased plan (steps 1.3/2.2/4.1/4.3).
- Static-with-dunder lockstep design + implementation record:
  [`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)
  (ml#701 / juniper-ml#710; edge-case coverage + already-at-target checklist fix juniper-ml#712).
- Orchestrator: [`.github/workflows/release-train.yml`](../.github/workflows/release-train.yml).
- Engines: `util/release_train/detect.py`, `propose.py`, `ceremony.py`, `registry.yaml`.
- Guards: `tests/test_release_train_workflow_guard.py` (R7 boundary + mode matrix + summary rehearsal),
  `tests/test_release_train_ceremony.py` (ceremony + HALT-issue degradation),
  `tests/test_release_train_registry.py::VersionDunderLockstepTest` (static pyproject == dunder, ml#701).
- Static `_version.py` lockstep (Gate 1 review):
  [`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)
  (implemented by juniper-ml#710).
- Release convention (cut a Release, archive notes centrally): repo `AGENTS.md` "Publishing" +
  [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.
