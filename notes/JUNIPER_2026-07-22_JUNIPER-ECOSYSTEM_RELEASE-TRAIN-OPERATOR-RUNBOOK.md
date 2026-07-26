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
| **`propose`** | detect + **propose** job | opens **standard-gated** release-proposal PRs (version bump + sibling/meta `AGENTS.md` **Version** co-change + CHANGELOG move + drafted notes + pin / `_version.py` dunder co-changes); **no** Releases, **no** (Test)PyPI | `propose` job `if: needs.detect.outputs.mode == 'propose'` (`release-train.yml:382`) |
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

#### Detect SHIP filter + SemVer (why a package shows `UNRELEASED_CHANGES`)

The detector's proposed bump feeds Gate 1. Two internals decide whether code ships and which SemVer
bucket `propose` suggests (`detect.py:has_substantive_hunk`, `local_git_compare`, `propose_semver`;
plan §4.2 / §6):

| Signal | Ships? | Notes |
|---|---|---|
| Whitespace-only hunk | **No** | Empty / space-only `+/-` lines are stripped before comment/code checks (`has_substantive_hunk`). |
| Pure comment / docstring / link edit | **No** | Notes-rename residue class — discounted. |
| Pure **code** deletion (with `file_text`) | **Yes** | `_removed_codeish` path; deleting a real statement must not thin SemVer. |
| Add / delete / rename / **copy** of a `.py` module (`A`/`D`/`R`/`C` in `local_git_compare`) | **Yes** | Inherently substantive — no blob compare (`detect.py:334-335`). Copy (`C075`) is rarer than A/D/R (needs copy detection) but shares the same short-circuit; do not expect a module copy to fall through to `SHIP_UNCERTAIN`. |
| Patch unavailable | **Uncertain** | Surfaces as `SHIP_UNCERTAIN`, not a silent `UP_TO_DATE`. |

Keep-a-Changelog categories + conventional-commit classes map to the proposed bump
(`FEATURE_CATEGORIES` / `FIX_CATEGORIES` / `BREAKING_CATEGORIES`, `detect.py:107-109`;
`propose_semver`, `detect.py:804-815`; pre-1.0 policy plan §6):

| Input | Proposed bump (pre-1.0) |
|---|---|
| `### Security` or `### Fixed` (or `fix:` commits) | **patch** |
| `### Added` / `### Changed` / `### Deprecated` (or `feat:` commits) | **minor** |
| `### Removed`, `feat!` / `fix!`, or a `BREAKING CHANGE` footer | **minor** (breaking is not major pre-1.0) |
| No release-worthy cats/classes | **none** |

When reviewing a Gate 1 PR, a `Security`-only Unreleased section should propose **patch**, not minor;
a `Changed` section should propose **minor**. A mismatch means the detector/SemVer path drifted —
re-run `report` mode before merging a hand-edited bump.

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

#### Gate 1 review — static `_version.py` dunder lockstep (ml#701 / juniper-ml#710)

All five in-repo **static** packages (`juniper-ci-tools`, `juniper-config-tools`, `juniper-doc-tools`,
`juniper-observability`, `juniper-service-core`) also ship `<import>/_version.py` `__version__`. A
pyproject-only bump used to ship wheels whose metadata was right while `__version__` lied (ci-tools
0.7.0 / service-core 0.5.0). As of juniper-ml#710, `propose.py` auto-detects that dunder by file
presence (no registry field) and bumps it in the same proposal (`build_proposal` step 3a; design
[`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)).

When reviewing a Gate 1 proposal for a static in-repo package, confirm:

1. **Both files move together (happy path)** — `pyproject.toml` `[project].version` **and**
   `<import>/_version.py` `__version__` in the Files-changed list (or the PR body's
   `### Version bump` names the lockstep dunder co-change). Single- or double-quoted
   `__version__ = …` both parse (`propose.py` `set_dynamic_version`).
2. **Already-at-target / re-entry (juniper-ml#712)** — a **pyproject-only** version diff with
   **no** dunder checklist item is valid when checkout `__version__` already equals the proposed
   `to_version` (partial heal / re-entry). Step 3a leaves a correct dunder alone and must **not**
   false-flag REQUIRED-manual. Confirm the match, then merge when the rest looks right.
3. **Checklist is honest (unparseable)** — if the co-change checklist says the dunder bump is
   `REQUIRED (... edit manually)` and the body does **not** claim a lockstep co-change, the file
   exists but is unparseable; hand-edit `__version__` in the same PR before merge (AGENTS.md-header
   precedent).
4. **Stale dunder still behind** — pyproject-only while checkout `__version__` is still at
   `from_version` (or any other mismatch) is the pre-#710 / stale-train failure class. Do **not**
   merge as-is; add the dunder bump or re-dispatch `propose` after #710/#712.
5. **CI gate** — `tests/test_release_train_registry.py::VersionDunderLockstepTest` (ships with
   juniper-ml#710) asserts pyproject == dunder for every in-repo static-with-dunder package
   (dynamic packages are exempt — their dunder *is* the source). A red
   `VersionDunderLockstepTest` means do not merge.

**Pitfall:** a pyproject-only diff is no longer automatically rejectable. Distinguish re-entry
(dunder already correct → OK) from the stale-dunder class (dunder still behind → block). After #712,
an already-correct dunder produces neither a `_version.py` edit nor a checklist line.

Dynamic packages (model-core + the three recurrence packages) are unchanged: the version bump *is*
the `_version.py` edit, so there is no separate lockstep co-change to look for.

#### Gate 1 review: sibling / meta `AGENTS.md` **Version** co-change (worker#140 / ml#706 / #720)

Every sibling repo's `AGENTS.md` `**Version**:` header tracks that repo's **primary** package
(`pypi_name == repo` in `util/release_train/registry.yaml`). Their CI runs the portable
`tests/test_agents_md_version_drift.py` lint, so a proposal that bumps `pyproject.toml` but leaves the
header stale fails Documentation Links — the [worker#140](https://github.com/pcalnon/juniper-cascor-worker/pull/140)
pilot class, fixed in juniper-ml#706 (`propose.py` step 5a). The meta-package (`juniper-ml`) uses the
older step-5 path for the same header lockstep (`tests/test_agents_md_version_drift.py` in this repo).

When reviewing a Gate 1 proposal for a **sibling primary** or the **meta** package, expect:

| Signal in the proposal PR | Meaning | Operator action |
|---|---|---|
| Diff edits `AGENTS.md` `**Version**:` in lockstep with the version bump | Normal co-change (header was at the from-version) | Merge when the rest of the proposal looks right |
| Checklist names the AGENTS.md bump as "included in this PR" | Train already applied the header edit | No extra manual edit |
| **No** `AGENTS.md` edit **and** **no** AGENTS checklist item; checkout header already equals `to_version` | Already-at-target / partial heal / re-entry (juniper-ml#720) — silent success; same class as the ml#701 dunder re-entry fix | Confirm the header really matches the proposed version, then merge when the rest looks right |
| Checklist item **REQUIRED**; file missing, or present without a `**Version**:` line | Train never invents a header (juniper-ml#720) | Add / restore `**Version**: <to_version>` by hand in the same PR before merge |
| Checklist item **REQUIRED**; header present but neither from-version nor to-version | Unexpected value — train left the file alone (never clobbers) | Verify / edit `**Version**:` by hand in the same PR before merge |
| Diff omits `AGENTS.md`, **no** checklist item, and checkout header is **not** at `to_version` | Pre-#706 / stale train / bug | Do **not** merge as-is; bump the header (or re-dispatch `propose` after #706+#720) |

**Does not apply when:** the bumped package is a **sub-package** hosted in a sibling (`pypi_name != repo`,
e.g. `juniper-cascor-model` in `juniper-cascor`) — the host header tracks the primary, so step 5a never
touches it.

Hermetic coverage: `tests/test_release_train_propose.py` (happy-path shapes in juniper-ml#706;
re-entry / absent / missing-header edges in juniper-ml#720).

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
  `release-train.yml:732-740`; `DEFAULT_MONITOR_TIMEOUT_SECONDS`, `ceremony.py:137`) until the run parks at
  the owner-gated `pypi` environment — GitHub reports that as run status `waiting`, which the train
  reports as **`PENDING_PYPI_APPROVAL`** (`ceremony.py:531`). **That terminal state is SUCCESS for the
  train** (plan §5.1). Terminal monitor returns are only
  `PENDING_PYPI_APPROVAL` / `RELEASED` / `HALT_TESTPYPI` / `HALT_PUBLISH`
  (`monitor_publish_run`, `ceremony.py:938-941`).
  - **`NOT_FOUND` is not terminal.** Right after `gh release create`, the publish workflow is often
    invisible for a poll or two (`classify_publish_run(None) -> NOT_FOUND`, `ceremony.py:505`). The
    monitor **keeps polling** — it must never stamp `NOT_FOUND` onto the ceremony result (that would
    skip waiting for Gate 2). Coverage: `MonitorTimeoutTest` in `tests/test_release_train_ceremony.py`
    (juniper-ml#744 / #745 / #747).
  - **Timeout → honest `IN_PROGRESS`.** If the wall clock elapses while the run is still building *or*
    still permanently missing (mis-tagged Release / workflow never triggered), the monitor returns
    **`IN_PROGRESS`** — never invents `PENDING_PYPI_APPROVAL` / `RELEASED` / a HALT
    (`ceremony.py:941`). Re-run ceremony mode to resume (idempotent). Operator check when you see
    `IN_PROGRESS` with no publish run: confirm the Release tag matched the workflow's `on:` filter and
    that the publish workflow actually fired (`gh run list --repo pcalnon/<owning-repo>`); fix the tag /
    workflow trigger, then re-run — do not approve a phantom Gate 2.
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

**Runner git identity (headless, unsigned) — must be `--global`.** Both write jobs run a
`Configure git identity (headless, unsigned)` step that sets `user.name`, `user.email`, and
`commit.gpgsign false` via `git config --global` (`release-train.yml:466-478` propose,
`675-687` ceremony). Cross-repo `propose` commits inside freshly-cloned **sibling** checkouts; a
repo-local `git config` on the juniper-ml checkout alone leaves those clones with
`Author identity unknown` (first cross-repo pilot failure, run 30040138774; fixed juniper-ml#705).
The hosted runner is ephemeral, so `--global` is still job-scoped. `propose.py` also passes
`-c commit.gpgsign=false` on its commit so a YubiKey-resident signing config never reaches a headless
run. The detect job must not configure identity (it never commits).

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
4. **Cross-repo pilot is owner-triggered.** The first live cross-repo `propose` dispatch
   (run 30040138774, `packages=juniper-cascor-worker`) failed at the commit step with
   `Author identity unknown` — **nothing was pushed** (worker repo stayed clean). Fixed by
   juniper-ml#705 (`git config --global` on both write jobs; §7). A successful cross-repo write
   (propose PR opened in a sibling, or ceremony cutting a sibling Release) still needs an owner
   re-dispatch to prove. Hermetic tests + `--dry-run` cover the logic
   (`tests/test_release_train_ceremony.py`).
5. **Archive-PR signature gate (RESOLVED 2026-07-23).** The juniper-ml ruleset's `required_signatures`
   rule evaluates a PR's source commits, so the exempt archive PR only auto-merges if its commit is
   signed. It now is: the archive branch + commit are created through the GitHub API (`git/refs` POST +
   `createCommitOnBranch`), yielding a **GitHub-signed / Verified** commit under the App / `GITHUB_TOKEN`
   identity (§3.3). Previously the commit was a plain unsigned runner-side `git commit`, so an all-green
   archive PR stayed BLOCKED behind that rule until an owner admin one-click (2026-07-23 run 30051952226
   / ml#707). Owner one-click is now only the degraded/manual fallback (e.g. `allow_auto_merge` off). No
   security-posture change — the PyPI deploy still waits at the owner-gated `pypi` environment (Gate 2).
   The **live proof** (an archive PR auto-merging with zero clicks) rides the next real ceremony dispatch.
6. **Summary / Slack `<<'PY'` late-failure class (RESOLVED #708 + #723).** Detect / propose / ceremony
   step-summary and Slack payload steps embed Python via `python - <<'PY' … PY`. A duplicated or missing
   `PY` terminator (run 30051952226 / ml#708) or a syntax-broken heredoc body (ml#723) fails **after**
   the real work finishes — the job goes red even though Gate 1/2 side effects already landed. Operator
   response: treat the run's proposal / archive / Release / `PENDING_PYPI_APPROVAL` outcomes as
   authoritative; fix the YAML and re-run only if a summary/Slack signal is still needed. Developers
   editing those blocks must keep openers and terminators 1:1 and keep each body `compile()`-clean —
   pinned by `HeredocBalanceTest` + `HeredocCompileTest` in `tests/test_release_train_workflow_guard.py`
   (four bodies today: detect summary, detect Slack, propose summary, ceremony summary).
7. **Sibling `Author identity unknown` (RESOLVED 2026-07-23, ml#705).** A red `propose` /
   `ceremony` job that dies at `git commit` inside a sibling clone with
   `Author identity unknown` / `Please tell me who you are` means the write job's identity step
   regressed to **repo-local** `git config` (or was removed). Confirm both write jobs still use
   `git config --global user.name|user.email|commit.gpgsign` (`release-train.yml:473-478`,
   `682-687`). Nothing is pushed when this fires — safe to re-dispatch after the workflow fix.
   Structural pin: juniper-ml#718 (`tests/test_release_train_workflow_guard.py` invariant `(g)`).
   (Numbered **#7** so open docs PR #725 can keep heredoc late-failure as §8 **#6**.)

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
- Guards: `tests/test_release_train_workflow_guard.py` (R7 boundary + mode matrix + summary rehearsal + `HeredocBalanceTest` / `HeredocCompileTest` for every `<<'PY'` block — ml#708 / ml#723),
  `tests/test_release_train_ceremony.py` (ceremony + HALT-issue degradation),
  `tests/test_release_train_registry.py::VersionDunderLockstepTest` (static pyproject == dunder, ml#701),
  `tests/test_release_train_propose.py` (sibling/meta AGENTS.md step-5/5a shapes — worker#140 / ml#706 / #720).
- Static `_version.py` lockstep (Gate 1 review):
  [`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)
  §6 / §6.1 (implemented by juniper-ml#710; hardened by juniper-ml#712).
- Release convention (cut a Release, archive notes centrally): repo `AGENTS.md` "Publishing" +
  [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.
