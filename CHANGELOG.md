# Changelog

All notable changes to the `juniper-ml` meta-package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Release-train ceremony (`util/release_train/ceremony.py`) — the exempt notes-archive PR's commit is now GitHub-signed (created through the GitHub API), so the exempt PR auto-merges hands-free.** The archive lane no longer branches/commits/pushes with runner-side git; instead `open_archive_pr` creates `refs/heads/release-notes/<pkg>-v<ver>` via a REST `POST /repos/pcalnon/juniper-ml/git/refs` (`create_branch`) and adds the single archive file via the GraphQL `createCommitOnBranch` mutation (`create_signed_commit`; single-file addition, `expectedHeadOid` for optimistic concurrency, base64 content). A commit made through GitHub's API under the App / `GITHUB_TOKEN` identity is **GitHub-signed and Verified**, so the exempt archive PR satisfies the juniper-ml ruleset's `required_signatures` rule and **auto-merges with zero clicks** — a plain unsigned runner-side commit previously left an all-green archive PR BLOCKED behind that rule (2026-07-23 run 30051952226 / ml#707, resolved only by the owner's admin one-click); owner one-click is now only the degraded/manual fallback, with **no security-posture change** (the PyPI deploy still waits at the owner-gated `pypi` environment, Gate 2). The R7 seam keeps `api` forbidden for the general surface and sanctions **exactly** those two calls, each bound to the 8 publishing repos: `_assert_gh_allowed` dispatches an `api` argv to the new `_assert_api_allowed`, which accepts only a `repos/<owner>/<repo>/git/refs` POST creating a `refs/heads/*` ref, or an `api graphql` body containing `createCommitOnBranch` with `repoWithOwner` bound, and rejects any other path/mutation/repo (a stray `gh api environments/…` still raises `SeamViolation`). The archive is always in juniper-ml (plan §10.2), where both token modes hold `contents: write`, so the API path is unconditional (no local-git fallback). Because the API path never switches the operator's checkout, the (unreleased) 2026-07-19 branch capture/restore rough-edge fix is removed as moot — git is now used only for READS in the archive lane (freshen `origin/main`, resolve the base sha, inspect an existing branch for idempotent re-entry: reuse at base, reuse the single archive commit, or HALT on divergence). Hermetic coverage in `tests/test_release_train_ceremony.py` replaces the branch-restore tests with the signed-commit lane (the two api-call argv shapes, base64 content round-trip, `expectedHeadOid` threading, branch-exists re-entry reuse/re-commit/HALT, and the `_assert_api_allowed` positive/negative carve-out); `--dry-run` stays byte-identical (`git status` clean). `.github/workflows/release-train.yml` is unchanged (the ceremony job already holds `contents: write` on juniper-ml); `propose.py` proposal PRs are owner-merged and unaffected (a possible future consistency follow-up). **No ceremony runs live in this change** — hermetic tests + `--dry-run` only; the live proof (an archive PR auto-merging with zero clicks) rides the next real ceremony dispatch.
- **Notes-migration ad-hoc scripts retired.** The four one-off migration scripts (`2026-07-04_notes_rename_{convention,refupdate,context_revert,sibling_links}.py`) moved to `util/ad-hoc/retired/` with a `_RETIRED-2026-07-06` suffix per the `util/ad-hoc/` lifecycle, now that every migration PR (juniper-ml#620/#626 + the 7 sibling link-fix PRs) is merged and verified. The old→new mapping TSV stays in place as the durable record; the convention doc's migration-record section points at the retired paths.
- **Notes loose-ends cleanup (follow-up to the naming migration).** The 13 pre-existing stale citations in `notes/requirements/id_assignments.yaml` (and their echoes in the by-area/by-repo/by-status views) are repointed to the files' current homes — three juniper-ml docs long since archived to `notes/legacy/` (`CONVERGENCE_UI_FIX_PLAN`, `REMAINING_ISSUES_REMEDIATION_PLAN`, `DOCUMENTATION_AUDIT_AND_UPGRADE_PLAN`) and one juniper-cascor doc that moved from `notes/history/` to `notes/pull_requests/` — taking the requirements drift checker to zero findings. The obsolete scratch file `notes/JUNIPER_2026-05-02_JUNIPER-CANOPY_TEMP.md` (ex-`temp.md`, flagged by the 2026-06-21 docs-reality audit) is deleted.
- **`notes/` file naming convention adopted + 251 files renamed.** Every document in `notes/` (except the exempt `templates/`, `releases/`, `requirements/`, `legacy/` subdirectories and README files) now follows `JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<CONTENTS-DESCRIPTION-PHRASE>.md`, where REPO is one of ML / CANOPY / RECURRENCE / CASCOR / CASCOR-CLIENT / CASCOR-WORKER / DATA / DATA-CLIENT / DEPLOY / ECOSYSTEM (ECOSYSTEM = cross-repo/platform-wide). Dates were taken from the old filename when present, else the file's last git-commit date. All ~7,000 in-repo references (markdown links, workflow comments, `id_assignments.yaml` citations, test/util docstrings) were rewritten in the same branch; the planner/auditor agents and the plan/audit/code-review prompt templates now emit the new name shape. Convention source of truth: `notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`; full old→new mapping: `util/ad-hoc/2026-07-04_notes_rename_map.tsv`.
- **DP-3 follow-up: `[recurrence]` extra app + client pins bumped to `>=0.2.0,<0.3.0`; model floor tightened to `>=0.1.5,<0.2.0`.** Now that `juniper-recurrence` 0.2.0 and `juniper-recurrence-client` 0.2.0 are published to PyPI — the releases that expose the full DP-3 readout spectrum (`linear` / `rff` / `mlp`) plus `ridge="gcv"` over the HTTP / CLI / client edge — the `[recurrence]` extra (and thus `[all]`) bumps both pins from `>=0.1.0,<0.2.0` to `>=0.2.0,<0.3.0`, so `pip install juniper-ml[recurrence]` resolves the new edge features. The `juniper-recurrence-model` pin is **also bumped from `>=0.1.0,<0.2.0` to `>=0.1.5,<0.2.0`** to match the real floor: `juniper-recurrence` 0.2.0 itself requires `juniper-recurrence-model>=0.1.5` (the 0.1.5 `MLPReadoutSpec` the `readout="mlp"` edge needs), so the meta-package's declared floor now reflects the effective floor instead of understating it. Publish-first follow-up to the 0.2.0 releases; the matching lint contract in `tests/test_pyproject_extras.py` updates in lockstep (RK-11).
- **R5: new `[recurrence]` extra — the Δt-native recurrence stack.** Adds a dedicated `recurrence` optional-dependency group pinning `juniper-recurrence-model>=0.1.0,<0.2.0` (the closed-form variable-Δt LMU regressor on the `juniper-model-core` `TrainableModel` seam) `juniper-recurrence>=0.1.0,<0.2.0` (the FastAPI/CLI application that wraps it), and `juniper-recurrence-client>=0.1.0,<0.2.0` (the HTTP client for that service, DEP-8), now that all three are published to PyPI (WS-4 / WS-4b). `[all]` aggregates it, so `pip install juniper-ml[recurrence]` / `[all]` resolves the recurrence model + app + client. The matching lint contract in `tests/test_pyproject_extras.py` updates in lockstep (RK-11); the `AGENTS.md` / `README.md` / `docs/QUICK_START.md` / `docs/REFERENCE.md` extras tables pick up the new row.
- **WS-3 follow-up: `juniper-model-core` added to the `[tools]` extra (and thus `[all]`).** Now that `juniper-model-core` 0.1.0 is published to PyPI, `[tools]` pins `juniper-model-core>=0.1.0,<0.2.0` (capped per the pre-1.0 convention), so `pip install juniper-ml[tools]` / `[all]` resolves the shared model-contract package. This is the deferred, publish-first follow-up to juniper-ml#416 (the package scaffold), which intentionally withheld extras wiring until the package was on PyPI. The matching lint contract in `tests/test_pyproject_extras.py` updates in lockstep (RK-11), and a new `tests/test_model_core_drift.py` guards the pin against future version drift.
- **WS-2 follow-up: `juniper-service-core` added to the `[tools]` extra (and thus `[all]`).** Now that `juniper-service-core` 0.1.0 is published to PyPI, `[tools]` pins `juniper-service-core>=0.1.0,<0.2.0` (capped per the pre-1.0 convention), so `pip install juniper-ml[tools]` / `[all]` resolves the shared service-tier framework package (FastAPI app factory, settings base, security/middleware, `TrainingLifecycle`). This is the deferred, publish-first follow-up to the WS-2 merges (juniper-ml#417/#419/#420/#422), which withheld extras wiring until the package was on PyPI. The matching lint contract in `tests/test_pyproject_extras.py` updates in lockstep (RK-11), and a new `tests/test_service_core_drift.py` guards the pin against future version drift; both it and the pre-existing `tests/test_model_core_drift.py` (added in #418 but never wired into `ci.yml`) now run in CI. The `README.md` / `docs/QUICK_START.md` `[tools]` tables also pick up the `juniper-model-core` entry that #418 had omitted.
- **E.3 (juniper-ml STACK_REGRESSION_CORRECTIONS_2026-05-27 §E.3)**: `[clients]` extra now pins `juniper-cascor-client>=0.5.0` (was `>=0.4.0`). The 0.5.0 release adds the `origin=` keyword argument to `CascorTrainingStream` and `CascorControlStream`, forwarded to `websockets.connect(..., origin=…)` — required by juniper-canopy to connect to cascor's fail-closed `/ws/control` allowlist (juniper-cascor#129) from inside docker compose. Without bumping this pin, downstream `pip install juniper-ml[clients]` (or `[all]`) installations would still resolve to `juniper-cascor-client 0.4.x`, which lacks the `origin=` kwarg, and any consumer threading an Origin through `CascorControlStream(origin=…)` would `TypeError` at runtime. Companion PRs in this cascade: juniper-deploy#101 (✅ merged 2026-05-29), juniper-canopy#327 (✅ merged 2026-05-29), juniper-cascor-client#69, juniper-cascor#312, juniper-canopy#328, juniper-deploy#102. The matching lint contract in `tests/test_pyproject_extras.py` updates in lockstep.

### Added

- **Release-train Phase 4.3: full `off|report|propose|ceremony` mode switch + operator runbook + rollback (`release-train.yml`, `util/release_train/ceremony.py`).** Implements step 4.3 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) (§8 / §9.3-9.4 / §11 / §12 step 4.3). `ceremony` mode is now **wired** (it no longer degrades to `report`): a second write-scoped `ceremony` job — `needs: detect`, `if: needs.detect.outputs.mode == 'ceremony'`, identical `permissions: {contents: write, pull-requests: write}` + its own App-token mint step + sibling clones — runs `util/release_train/ceremony.py --execute --monitor-timeout 900` and renders a ceremony step summary (ceremonies / resume-monitors / HALTs / `PENDING_PYPI_APPROVAL`). Mode resolution accepts all four values (precedence: dispatch input > repo variable `RELEASE_TRAIN_MODE` > `report`); an unknown value warns and degrades to `report`; **`off` fully quiesces** (nothing runs beyond mode resolution). `ceremony.py` gains **graceful HALT-issue degradation** (`_file_halt_issue`): a failed `gh issue create/edit` during a HALT upsert — most plausibly the cross-repo App token lacking the Issues permission — degrades to a loud log line + a step-summary `halt_issue_failed` flag instead of crashing the run (a `SeamViolation` code bug still propagates; the R7 gh surface is unchanged), and `--execute` now emits one stable machine-parseable `ceremony-result:` line per package for the step summary. New operator runbook [`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md): the four modes + what each writes, mode-resolution precedence, the daily-cron / propose / ceremony cheat-sheet, the two owner gates, the §8 HALT catalog with responses, rollback procedures (`RELEASE_TRAIN_MODE=off`, deleting a bad Release/tag, closing a bad proposal, the immutable-index stance), and the App identity + R7 in operator terms (every claim cited to `file:line` / `§section`). `tests/test_release_train_workflow_guard.py` extends to pin both write jobs (perms, mode gates, mint-only App secret referenced exactly once per write job, off-quiescence) and **rehearses the actual workflow snippets** — the mode-resolution shell over the full matrix and the ceremony summary Python over a synthetic output — via the YAML-extraction pattern; `tests/test_release_train_ceremony.py` adds the HALT-issue-degradation unit + end-to-end coverage and the `ceremony-result:` output-format tests. **No cross-repo ceremony runs live in this change** — hermetic tests + `--dry-run` only; the owner triggers the pilot post-merge.
- **Release-train Phase 4.2: dependency-ordered scheduling + consumer ceiling-bump follow-on PRs (`util/release_train/propose.py`).** Implements step 4.2 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) (§13 / §5.4 / §6 / §12 step 4.2). (1) **Dependency-aware ordering.** When multiple packages are eligible in one run, `propose.py` now processes them **upstream-first** via a deterministic topological sort of the registry `depends_on` DAG (`topological_order`, Kahn's algorithm with a lexicographic `pypi_name` tie-break — derived from the registry, NOT hardcoded tiers; shared libs → sub-libs → apps → meta, with `juniper-ml` last); a cyclic `depends_on` graph is a hard invocation error (exit 2) naming the cycle (`CycleError`). (2) **Ceiling-bump follow-on PRs (D6).** Each propagation edge is annotated with a `consumer_pin_state` (`within_range` / `floor_only` / `escaped -> follow-on` / `escaped -> skipped(<reason>)`) read from the consumer's REAL pyproject on disk (both floor-only and `<ceiling` forms; the PEP 508 `[extras]` marker, e.g. `juniper-model-core[crossval]>=…`, is tolerated); for each escaped cross-repo consumer it builds a **standard-gated** ceiling-bump follow-on PR in that consumer's repo — the pin edit (ceiling raised to the upstream's next-minor, floors preserved byte-for-byte), branch `deps/<upstream>-ceiling-<new-ceiling>`, and a body citing §13 + the triggering proposal — **never** folded into the upstream proposal or the exempt notes-archive path (the 2026-07-06 ci-tools incident class; rec#85 is the hand-made shape). Cross-repo capability (Phase 4.1) gates the open (`escaped -> follow-on` when `--cross-repo` with the sibling checked out, else `escaped -> skipped`), and a per-consumer-repo dup-guard suppresses a duplicate. The meta (`juniper-ml`) never gets a follow-on: its pin rides #661's folded co-change when the upstream is in-repo and stays MANUAL (Q-META) otherwise. (3) The proposal JSON/report + PR body surface the per-run propagation picture (`follow_on_prs`, `consumer_pin_state`). Hermetic coverage in `tests/test_release_train_propose.py` (topological order over the real registry + a synthetic cycle → exit 2; the §12-4.2 verify — a simulated upstream MINOR bump produces the expected edges + follow-on content; escaped / within-range / floor-only / extras-form pins; degraded-mode skip; per-repo dup-guard; dry-run writes nothing). **No cross-repo write runs live in this change** — hermetic tests + `--dry-run` only.
- **Release-train Phase 4.1: cross-repo write identity + cross-repo `propose`/`ceremony` (`release-train.yml`, `util/release_train/propose.py`, `util/release_train/ceremony.py`).** Implements step 4.1 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) (§9.2–9.4 / §10.2 / §12 step 4.1). The `propose` job now mints a **GitHub App installation token** (`actions/create-github-app-token`, SHA-pinned `bcd2ba4` / v3.2.0) scoped to the 8 publishing repos and passes `propose.py --cross-repo`; `propose.py` replaces its hard `WRITABLE_REPO` guard with **capability-based** logic — given that cross-repo token and an on-disk sibling checkout (`--ecosystem-root`), a sibling package's proposal branches from that repo's `origin/main`, edits that checkout (the write/git seam is now **repo-aware**), pushes with the App token, and opens the PR **in the sibling repo** (the dup-guard runs per-repo); without the capability it skips siblings with the same clear reason as before (the degraded single-repo `GITHUB_TOKEN` path). The in-repo meta consumer-pin co-changes (#661 RK-11 lockstep) stay juniper-ml-only — a sibling proposal emits the §13 propagation edge instead of editing the meta from a sibling checkout. `ceremony.py` gains the same capability gate and a **repo split** (plan §10.2): the exempt notes-archive PR is **always** opened centrally in juniper-ml (`plan.archive_repo`) while the Release is cut on the **owning** repo (`gh release create --repo pcalnon/<repo>`) and that repo's publish run monitored; its R7 seam (`_assert_gh_allowed`) now bounds every `--repo` to the 8 publishing repos (registry-derived via `publishing_repo_slugs`) **without widening the verb allowlist**, and `create_release` renders the `--notes-file` to a scratch temp path instead of the checkout (the 07-19 stray-untracked-file fix). **Graceful degradation is mandatory**: the mint step is gated on the repo variable `RELEASE_TRAIN_APP_ID` (owner-provisioned with the `RELEASE_TRAIN_APP_PRIVATE_KEY` secret); when unset the job falls back to `GITHUB_TOKEN` and skips siblings. The App private-key secret is referenced **only** in the mint step and the minted token **only** in the propose job — pinned by `tests/test_release_train_workflow_guard.py`, whose `ALLOWED_SECRETS` allowlist is deliberately extended for `RELEASE_TRAIN_APP_PRIVATE_KEY`. Because App-created PRs trigger CI normally, the `GITHUB_TOKEN` no-checks caveat now applies **only** to the degraded no-App path (AGENTS.md + the workflow header updated accordingly). Hermetic coverage extends `tests/test_release_train_propose.py` (cross-repo opens in the sibling with the correct branch/base, no meta edits from a sibling context, degraded-path skip preserved) and `tests/test_release_train_ceremony.py` (cross-repo archive-in-juniper-ml while `release create` carries `--repo <owning>`; seam `--repo` accept/reject; temp-path notes render). **No cross-repo write runs live in this change** — hermetic tests + `--dry-run` only; the owner triggers the pilot post-merge.
- **Release-train Phase 3.2: exempt-archive + Release ceremony engine (`util/release_train/ceremony.py`).** Implements step 3.2 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) (§5.3 / §7 / §8 / §9.3 / §10). For each `BUMPED_NOT_RELEASED` package the detector reports (in-repo / juniper-ml only this phase — the `WRITABLE_REPO` guard reused from `propose.py`; sibling repos are skipped with a clear reason, deferred to Phase 4's GitHub App identity), the engine: (1) runs the §8 preconditions — target `main` CI green, the `declared >= released` re-check against live PyPI truth, a non-empty `CHANGELOG [<version>]` section, and (in the monitor) TestPyPI install-verify success — each failure **HALTs that package** with a deduplicated GitHub-issue payload (title keyed on `pypi_name` + reason), never blocking the others; (2) builds the FINAL central notes file via `notes_render` from the released package's `CHANGELOG [<version>]` section (`archive_name` from `registry.yaml`); (3) opens the exempt add-only, single-file archive PR (the diff the Phase 3.1 guard proves); (4) enables `gh pr merge --auto --squash` on it, **degrading gracefully** to the owner one-click merge when `allow_auto_merge` is off (step 3.3 has not landed — that is *not* a HALT); (5) cuts `gh release create <tag> --latest=false --notes-file <archive>` — the Release **creates** the sub-package tag (procedure §11.4), so there is deliberately **no** `--verify-tag`; (6) monitors the triggered publish run and reports the terminal state `PENDING_PYPI_APPROVAL` — the run legitimately parks at the owner-gated `pypi` environment, which **is success for the train**. The **R7 write-identity invariant (§9.3) is enforced in code**: every `gh` call is routed through `_assert_gh_allowed`, which permits exactly `{pr create, pr merge --auto, release create, run list/view, issue create/edit}` and rejects any `api` / environment / deployment / reviewer mutation, a bare `pr merge` without `--auto`, or a `release create --verify-tag`; `tests/test_release_train_ceremony.py` asserts the live seam's actual surface matches. **Idempotent re-entry** (§8): a re-run re-computes state from PyPI/Release truth — already-released is a no-op, an existing Release resumes at the monitor, and an open archive PR / already-archived file is reused, never duplicated. **`--dry-run` is the default and prints the full ceremony script of actions while writing nothing**; `--execute` exists but is not run against the real repo in this change. `util/` is not pre-commit-lint-gated, so the new hermetic unittest is the gate, wired into `ci.yml`. The live end-to-end (a real low-risk sub-package bump — `juniper-service-core` 0.5.0 is queued as exactly that payload) is owner-triggered **after** the step-3.3 auto-merge preconditions land.
- **Release-train Phase 3.1: structural archive-guard for the exempt notes-archive PR (`util/release_train/archive_guard.py` + `ci.yml` guard lane).** Implements step 3.1 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) (§7.2 / R5): the required-CI-job CHECK that proves the release-train's ONE gate-exempt PR — the one that archives the generated release notes and contains *no other change* — really is exactly that, so it can (later, step 3.3) auto-merge behind a required status check without leaking any code/config change past the owner gate. The path-invokable module computes a PR's changed-file set (`git diff --name-status <base>...<head>`, injected so the tests are hermetic) and passes ONLY if all four rules hold: **add-only** (every change status `A`), **path-confined** (each added path `^notes/releases/RELEASE_NOTES_.*\.md$`), **name-valid** (each filename `RELEASE_NOTES_v<semver>.md` meta / `RELEASE_NOTES_<pkg>_v<semver>.md` else, `<pkg>` a registry `pypi_name`, per procedure §11.3), and **single-purpose** (nothing else in the diff). A PR that does not touch `notes/releases/` is `SKIP` (passes), so the guard never blocks a normal PR; a violation merely fails the check (exit 1) and the PR falls back to the standard owner gate — the guard opens/merges nothing and mutates no environment (R7). A new PR-only `release-train-archive-guard` job in `ci.yml` runs it (standalone, so the owner can later mark it a required status check in the branch ruleset). New hermetic gate `tests/test_release_train_archive_guard.py` proves a pure notes-add passes and modify / delete / out-of-path / bad-name / mixed diffs each fail; `util/` is not pre-commit-lint-gated, so that unittest is the gate. No ceremony/auto-merge behaviour ships here (that is step 3.2); this is the guard alone.
- **Release-train Phase 2.2: `propose` mode wired into `release-train.yml` (opt-in, in-repo pilot).** Implements step 2.2 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) (§9.3 / §12 step 2.2). A **two-job privilege split** preserves the R7 write-identity invariant: the `detect` job keeps the workflow-level `contents: read` and now runs for both `report` and `propose` (detection is common) while exposing the resolved mode as a job output; a new **write-scoped `propose` job** — `permissions: {contents: write, pull-requests: write}`, `if: needs.detect.outputs.mode == 'propose'` (so the write scope is unreachable off the propose path) — downloads the release-manifest artifact and runs `util/release_train/propose.py --execute` to open **standard-gated** release-proposal PRs, never touching environments, deployments, Releases, or (Test)PyPI. `off`/`report`/`propose` are all valid modes now; only `ceremony` still degrades to `report`. A new `packages` dispatch input (whitespace/comma-separated pypi_names, validated against the pypi-name charset; empty = all eligible) restricts which packages are proposed. `propose.py` gains a **cross-repo guard**: under `--execute` a package whose registry `repo` is not `juniper-ml` is skipped with a clear reason (the single-repo `GITHUB_TOKEN` cannot open cross-repo PRs; cross-repo is Phase 4), and its commit passes `-c commit.gpgsign=false` (the job also runs `git config commit.gpgsign false`) so the headless runner never trips the owner's YubiKey signing config. New guards: `tests/test_release_train_workflow_guard.py` pins the R7 boundary (workflow-level `contents: read`; propose-job perms exactly `{contents: write, pull-requests: write}`; the mode-gated `if`; only `SLACK_WEBHOOK_URL` referenced), and `tests/test_release_train_propose.py` covers the cross-repo skip + the gpgsign fix; both are wired into `ci.yml`. **Known limitation** (accepted for the pilot): PRs opened with `GITHUB_TOKEN` do not trigger CI (GitHub's recursion guard), so a proposal PR shows no checks until the owner re-triggers (close/reopen, or push an empty commit); Phase 4's GitHub App resolves this. The real pilot dispatch (`gh workflow run release-train.yml -f mode=propose -f packages=<one>`) is owner-run post-merge.
- **Release-train Phase 2.1: proposal-PR generator (`util/release_train/propose.py` + `notes_render.py`).** Implements step 2.1 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) (§5.4 / §6 / §10.1): consumes the Phase 1.2 detector's release-manifest JSON (`detect.py --json`) and, for each `UNRELEASED_CHANGES` package, generates the complete **standard-gated** release-proposal PR content — the version bump (`[project].version` for static packages, `_version.py` `__version__` for the four dynamic ones), the CHANGELOG `[Unreleased]` → `[<version>] - <date>` move (a fresh empty `[Unreleased]` left behind), a template-driven release-notes draft (`notes_render.py`, sourced from `TEMPLATE_RELEASE_NOTES.md` or the security template when a `Security` category is present; **not** archived to `notes/releases/` — archival is the later exempt ceremony step), the meta-package `AGENTS.md` `**Version**` co-change, the §5.4 co-change checklist, and the `propagation_edges` (a pre-1.0 MINOR bump escapes a consumer's `<next-minor` ceiling pin → standard-gated follow-on PRs, the 2026-07-06 ci-tools incident class), plus the branch name, commit message, and PR title/body. The `gh pr list` dup-guard and the `changelog_conflict` refusal run behind an injectable seam so `tests/test_release_train_propose.py` is fully hermetic (no network / gh / repo writes). **`--dry-run` is the default and the only mode this step exercises**: it prints the well-formed proposal and writes nothing / opens nothing. The `--execute` code path and wiring the `propose` mode into `release-train.yml` are deferred to step 2.2. `util/` is not pre-commit-lint-gated, so the new unittest is the gate, wired into `ci.yml` alongside the detector tests.
- **Release-train Phase 1.4: non-blocking Slack notification lane in `release-train.yml`.** Each report run now posts a compact summary (classification counts, packages needing release action, run URL — no secrets, no diff content) to the Juniper Slack channel via the owner-provisioned `SLACK_WEBHOOK_URL` incoming-webhook repo secret (Q-CHANNEL decision, plan §11). Strictly non-blocking by construction: with the secret absent the step logs a skip and the run stays green, and a Slack post failure never fails the train (`continue-on-error: true`). The step-summary table + manifest artifact remain the canonical auditable record; Slack is additive signal only.
- **Release-train Phase 1.3: daily report-only orchestrator (`.github/workflows/release-train.yml`).** Implements step 1.3 of the [PyPI release-train plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md): a scheduled workflow (daily `0 13 * * *` UTC per the ratified Q-CADENCE decision, plus `workflow_dispatch`) that full-history-clones the 7 sibling package repos — including `juniper-recurrence`, which the `docs-full-check.yml` clone list omits — runs the Phase 1.1/1.2 detection engine (`util/release_train/detect.py`, juniper-ml#641) over the 18-package registry, uploads the release-manifest JSON as a run artifact, and renders a per-package classification table into the step summary. Report-only by construction: no PRs, no Releases, no (Test)PyPI writes; detector exit 1 ("action needed") is a normal green outcome and only a hard source error (exit >= 2) fails the run. The repo variable `RELEASE_TRAIN_MODE` (`off`|`report`, default `report`) with a dispatch-input override is the instant rollback switch; the future `propose`/`ceremony` modes degrade to `report` with a warning until those phases land.
- Host orchestration reference docs now distinguish the startup scripts' `JUNIPER_CASCOR_*` overrides from the `get_cascor_*.bash` query helpers' legacy `CASCOR_*` overrides, and document the host-facing `8201` / worker-health `8210` port map in `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, and `AGENTS.md`.
- Host-stack operations docs now include source-verified prerequisites, all `util/get_cascor_*.bash` endpoints, PID-file versus systemd lifecycle behavior, common startup/shutdown troubleshooting, and navigation links from `README.md`, `docs/QUICK_START.md`, and `docs/DOCUMENTATION_OVERVIEW.md`.
- **CFG-08** (v7 roadmap §13846): new "Rate Limiting Defaults" subsection under "Ecosystem Compatibility" in `docs/REFERENCE.md`. Documents the intentional split-default — `juniper-data` ships `rate_limit_enabled=True`, while `juniper-cascor` and `juniper-canopy` ship `False` — alongside the per-service env-var override names (`JUNIPER_<SERVICE>_RATE_LIMIT_ENABLED` / `JUNIPER_<SERVICE>_RATE_LIMIT_REQUESTS_PER_MINUTE`). Closes the documentation gap the roadmap CFG-08 entry called out (defaults differ across services but the rationale wasn't surfaced anywhere central). The per-minute threshold is uniform at 60 req/min across all three; only the enable flag varies. Source-of-truth file:line refs included so a future reader can re-verify against the live Settings classes. Per-service AGENTS.md cross-references are a deferred follow-up if the central reference proves insufficient.

### Fixed

- **Release-train ceremony (`util/release_train/ceremony.py`) — the publish-run monitor now reaches the designed terminal state instead of a premature `IN_PROGRESS`.** It polls the triggered run on a bounded wall clock (new `--monitor-timeout`, default ~15 min, at a short fixed interval) until the run is terminal (success/failure — existing handling) or parked at the owner-gated `pypi` deployment environment — GitHub reports that as run status `waiting` (a documented workflow-run status that `gh run view --json status` passes through verbatim), which the train reports as `PENDING_PYPI_APPROVAL` (plan §12-3.2, terminal-healthy) and exits 0. Only a genuine still-building timeout now yields `IN_PROGRESS` (honest, and the ceremony is idempotent so a re-run resumes at the monitor). No new `gh` surface: the fix stays within the R7 §9.3 read-only allowlist (`run list` / `run view`). Hermetic coverage in `tests/test_release_train_ceremony.py` (monitor → `PENDING_PYPI_APPROVAL` on a `waiting` fixture; honest `IN_PROGRESS` on timeout). (The same 2026-07-19 run's *other* rough edge — capturing/restoring the operator's checkout branch across the archive-PR git ops — is **superseded before release** by the signed-archive-commit change under `### Changed`: the archive lane no longer switches the checkout, so there is nothing to restore.)

## [0.6.0] - 2026-05-23

### Changed

- **Extras floor-bump to today's ecosystem release wave.**
  `[clients]`, `[worker]`, and `[servers]` now require the versions that
  shipped to PyPI on 2026-05-23 alongside the broader
  `juniper-cascor` 0.5.0 / `juniper-canopy` 0.5.0 /
  `juniper-cascor-worker` 0.4.0 / `juniper-cascor-client` 0.4.0 /
  `juniper-data-client` 0.4.1 release wave. Specifically:
  - `[clients]`: `juniper-data-client>=0.4.0` → `>=0.4.1`;
    `juniper-cascor-client>=0.3.0` → `>=0.4.0`.
  - `[worker]`: `juniper-cascor-worker>=0.3.0` → `>=0.4.0`.
  - `[servers]`: `juniper-canopy>=0.3.0` → `>=0.5.0`;
    `juniper-cascor>=0.3.17` → `>=0.5.0`; `juniper-data>=0.6.0` (unchanged).
  - `[tools]` and `[doc-tools]` unchanged at this release. The matching
    lint contract in `tests/test_pyproject_extras.py` updates in lockstep.
  Resolved doc surfaces brought into agreement: `README.md`,
  `AGENTS.md`, `docs/REFERENCE.md`, `docs/DOCUMENTATION_OVERVIEW.md`,
  and `docs/QUICK_START.md` all now declare the same pin set.
  Drive-by fix: the `juniper-config-tools` member of `[tools]` (added
  via CFG-06 / juniper-ml#320) is now visible in the README, AGENTS.md,
  REFERENCE.md, and QUICK_START.md tables, closing pre-existing doc
  drift between pyproject and human-readable extras references.
  Version bumped 0.5.0 → 0.6.0 (semver minor: existing callers pinning
  to `juniper-ml>=0.5.0` will be transparently upgraded to the new
  floor minimums).

- **TestPyPI extras-resolution verification extended to `[tools]`.**
  `.github/workflows/publish.yml` now runs a third `pip install` step
  after the bare-package install and the `[clients]` install: it also
  installs `juniper-ml[tools]==${VERSION}` from TestPyPI and imports
  the three `[tools]` packages (`juniper-ci-tools`,
  `juniper-doc-tools`, `juniper-observability`). Both light extras
  (`[clients]` + `[tools]`) are now exercised at publish time, closing
  the gap documented in the v0.5.0 release runbook §7 (which
  previously called out `[tools]` as caught only by the schema lint,
  not at publish time). `[servers]` and `[worker]` remain
  schema-lint-only because their dependency trees are too heavy to
  resolve in every release run. Matching runbook §7 update so the
  documented behavior matches reality.

- **`juniper-ml[all]` install-size advisory corrected** in
  `docs/QUICK_START.md`, `notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`,
  and `notes/JUNIPER_2026-05-21_JUNIPER-ML_META-PACKAGE-EXTRAS-REQUIREMENTS.md`. The
  original v0.5.0 estimate of "roughly 2 GB" understated the resolved
  on-disk footprint by ~2.5x: the actual figure measured against PyPI
  on 2026-05-21 (Python 3.13, Linux x86_64) was **5 GB on disk after
  install**. The advisory also now gives concrete per-extra footprints
  (`[clients]`, `[tools]`, `[doc-tools]` < 50 MB each; `[servers]`
  < 200 MB). Pure documentation correction; no code or pin changes.

## [0.5.0] - 2026-05-21

### Added

- **TestPyPI extras-resolution verification step** in
  `.github/workflows/publish.yml`. After the bare-package install
  verification, the workflow now also installs `juniper-ml[clients]`
  from TestPyPI and imports both client modules. This exercises the
  full `[project.optional-dependencies]` resolution path against the
  published metadata, so a broken extras declaration (mistyped name,
  missing roll-up into `[all]`, dangling self-reference) fails the
  publish rather than landing on PyPI silently. `[clients]` is chosen
  because it is the lightest extra (no torch) and still walks the full
  resolver path.

- **`notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`**
  -- runbook for the v0.5.0 release. Documents preconditions, the
  TestPyPI / PyPI flow, the new extras-resolution verification step,
  and the rollback options (yank vs. patch release) for a meta-package
  whose extras surface has expanded.

- **`tests/test_agents_md_version_drift.py`** -- new lint test pinning
  `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s
  `[project].version`. juniper-ml#295 bumped `pyproject.toml` from
  0.4.1 to 0.5.0 but left `AGENTS.md` at 0.4.0 for ~6 days (drift
  caught by ad-hoc grep + fixed in juniper-ml#304); this lint makes
  the failure class impossible to ship. Wired into the main CI tests
  job; intentionally portable (auto-locates the repo root) so the
  same module can be dropped into any Juniper repo's `tests/` to
  catch the same drift class there.

- **`notes/JUNIPER_2026-05-21_JUNIPER-ML_META-PACKAGE-EXTRAS-REQUIREMENTS.md`** -- source
  requirements doc for the meta-package extras surface. Specifies the
  declared groups, `[all]` aggregate semantics, version-bump policy,
  documentation-consistency surfaces, regression-coverage expectations,
  and the install-size advisory. Written in the source-doc format that
  the next snapshot consolidation pass can ingest; `JR-ML-*` IDs will
  be assigned at that pass and referenced retroactively in PRs #293,
  #295, #299.

- **Install-size advisory for `juniper-ml[all]`** in `docs/QUICK_START.md`.
  Calls out that `[all]` transitively pulls a multi-GB dependency tree
  (notably `torch` via `juniper-cascor-worker` and `juniper-cascor`,
  approx. 2 GB on a fresh env) and recommends narrower extras
  (`[clients]`, `[tools]`, `[doc-tools]`) when the worker / server
  distributions are not needed.

- **`tests/test_pyproject_extras.py`** -- new lint test pinning the
  `[project.optional-dependencies]` surface so accidental edits (drop,
  mistype, fail to roll up into `[all]`) fail loudly in CI. Schema-strict:
  any future change to extras must update the lint contract in the same
  PR. Wired into the main CI tests job; runs alongside
  `test_doc_tools_drift.py` and `test_workflow_script_paths.py`.

- **`[servers]` optional dependency group** for the three Juniper service
  packages on PyPI. `pip install juniper-ml[servers]` now installs
  `juniper-canopy>=0.3.0`, `juniper-cascor>=0.3.17`, and
  `juniper-data>=0.6.0` in a single step. Previously the meta-package
  only aggregated the client/worker libraries; the server distributions
  had to be installed by name.

- **`[tools]` optional dependency group** that aggregates the three
  PyPI-published Juniper tool packages: `juniper-ci-tools>=0.1.0`
  (dependency-documentation generator, Wave 1 of the dep-docs migration
  plan), `juniper-doc-tools>=0.1.0,<0.2.0` (markdown link validator),
  and `juniper-observability>=0.2.0` (shared Prometheus collector
  helpers + structured logging + Starlette middleware). The
  pre-existing `[doc-tools]` extra is retained for back-compat with
  callers that already installed via that name.

- **`[all]` extra expanded** to cover the new `[servers]` and `[tools]`
  groups in addition to `[clients]` and `[worker]`. A single
  `pip install juniper-ml[all]` now pulls in every published Juniper
  package: 3 servers, 2 clients, 1 worker, and 3 tools.

### Changed

- **Pre-tag docs polish for the 0.5.0 release.** Refreshes the three
  Ecosystem Compatibility tables (`README.md`, `docs/REFERENCE.md`,
  `docs/DOCUMENTATION_OVERVIEW.md`) to enumerate every package the
  meta-package now pins -- canopy / cascor / data / data-client /
  cascor-client / cascor-worker / ci-tools / doc-tools / observability
  -- with their actual pyproject pins (the previous tables only listed
  3-5 packages and used stale `0.4.x` headers). Adds `[servers]`,
  `[tools]`, and `[doc-tools]` editable-install commands to `AGENTS.md`
  and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, plus an explicit
  multi-GB callout on `[all]`.

- **Version bumped to 0.5.0** (semver minor) to mark the new optional
  dependency surface. No removals or breaking changes -- existing
  `[clients]`, `[worker]`, `[doc-tools]`, and `[all]` install commands
  continue to work; `[all]` is now a strict superset.
- **`juniper-observability` is now aggregated under `juniper-ml[tools]`
  and `juniper-ml[all]`.** Until 0.4.1 it was published from this
  repository as a sibling package that had to be installed directly.
  Documentation in `README.md`, `docs/QUICK_START.md`,
  `docs/REFERENCE.md`, and `docs/DOCUMENTATION_OVERVIEW.md` updated to
  reflect this. Independent versioning and the
  `juniper-observability-v*` tag pipeline are unchanged.

- **§5 drift-detection guard rails** for the `juniper-doc-tools` PyPI
  migration (plan
  [`notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md`](notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md)
  §5.1 + §5.2). Closes the open follow-ups from Wave 4.
  - `tests/test_doc_tools_drift.py` — consumer-version-pin lint. Reads
    the current `juniper-doc-tools` version from
    `juniper-doc-tools/pyproject.toml`, then walks each cloned consumer
    repo's `ci.yml` and asserts the `juniper-doc-tools>=X,<Y` pin still
    admits current. Soft-warns when a pin lags by more than 2 minors;
    hard-fails when the upper bound excludes current. Also lints
    juniper-ml's own `ci.yml` + `docs-full-check.yml` for the same pin
    rule (this case runs even per-PR; the cross-repo assertion auto-
    skips when siblings aren't on disk). Local runs skip the cross-repo
    assertion by default to avoid stale-working-tree false positives;
    set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to override.
  - `.github/workflows/docs-full-check.yml` — two new steps in the
    weekly cross-repo workflow:
    - "Lint doc-tools pins across consumer repos" invokes the new test.
    - "Downstream-consumer integration check" installs `juniper-doc-tools`,
      runs `juniper-check-doc-links` against each cloned consumer repo's
      docs with the canonical Juniper exclude set, and aggregates per-
      repo results. Per-repo failures are warned; the step fails only
      when `>=DOWNSTREAM_FAIL_THRESHOLD` consumers regress in the same
      week (default 5 of 6 = catastrophic juniper-doc-tools regression).

### Removed

- **`util/check_doc_links.py`** (the inline v0.7.0 validator) — Wave 2 + Wave 4 of the doc-link migration plan. Replaced by the PyPI-published `juniper-doc-tools` package; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`. The CI docs jobs (`ci.yml`, `docs-full-check.yml`) now install the package and run the console script. Inline copies in all 7 sibling repos (canopy / cascor / data / cascor-client / cascor-worker / data-client / ml) are deleted in the same wave.
- `scripts/check_doc_links.py` (symlink to the old `util/` copy), `util/check_doc_links.bash` (local-path-only convenience wrapper), and `tests/test_check_doc_links.py` (now covered by `juniper-doc-tools/tests/`).

### Added

- `util/check_doc_links.py` bumped to **v0.7.0**: classifies ecosystem-root paths (`../../CLAUDE.md`, `../../AGENTS.md`, `../../notes/`, `../../prompts/`, `../../resources/`, `../../backups/`, `../../logs/`, `../../worktrees/`, `../../juniper-legacy/`, `../../Juniper{,1}.code-workspace`) the same way as cross-repo `../juniper-X/` links: subject to the `--cross-repo` policy (skip/warn/check). Restores parity with the more permissive behavior repo docs were already relying on without silently accepting truly broken outside-repo links. 5 new regression tests in `tests/test_check_doc_links.py` cover the ecosystem-root paths and a guard against misclassifying intra-repo links that happen to traverse a `notes/`-named directory.
- `tests/test_workflow_script_paths.py` — new lint test that walks `.github/workflows/*.yml`, extracts every script path referenced via `python|bash <path>` / `python3 -m unittest ... <path.py>` / `$VAR <path>` patterns, and asserts each path exists in the repo. Cross-repo paths (`juniper-X/...`) are skipped as runtime-resolved. Catches the failure class that broke 3 juniper-X CIs on 2026-05-18 when a script was renamed without updating the workflow. Designed to be copy-and-paste portable into the other Juniper repos' `tests/` directories.
- **`juniper-doc-tools` subpackage scaffold** — Wave 0 of the doc-link
  validator PyPI migration ([plan](notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md)).
  New `juniper-doc-tools/` subdirectory packages the v0.7.0 markdown link
  validator as a PyPI distribution with a stable CLI surface
  (`juniper-check-doc-links` + `python -m juniper_doc_tools`), a small
  library API (`validate_directory`, `validate_file`, `ValidationResult`),
  and the new `--strict-repo-boundary` opt-out flag from §3.4.1 / §8.4.
  Tests use pytest (§8.1); 30 tests cover the v0.7.0 behavior, the new
  flag, and CLI argparse end-to-end. `.github/workflows/ci-doc-tools.yml`
  runs the test matrix (3.12/3.13/3.14) + build + wheel smoke-test on
  PRs touching `juniper-doc-tools/**`. `.github/workflows/publish-doc-tools.yml`
  publishes to TestPyPI → PyPI on tags matching `juniper-doc-tools-v*`,
  mirroring the existing `publish-observability.yml`.
- **`juniper-doc-tools` 0.1.0 published to PyPI** — Wave 1 of the
  migration plan. Tag `juniper-doc-tools-v0.1.0` cut from `main` on
  2026-05-19; OIDC trusted publish went through TestPyPI → PyPI without
  intervention (TestPyPI verified install + console-script + module-form
  on a fresh runner). `pip install juniper-doc-tools` now works from
  any environment. New `[doc-tools]` extra in this `pyproject.toml`
  pins the consumer to `>=0.1.0,<0.2.0` so a future breaking minor
  bump does not auto-adopt before Wave 2 swaps each repo's CI over.
  Next: Wave 2 (per-repo CI swap) starts in juniper-ml itself, then
  fans out to the 7 other ecosystem repos.

## [0.4.1] - 2026-04-28

### Added

- **`juniper-observability` package (alpha `0.1.1a`)** — new sibling package living under `juniper-observability/` (METRICS-MON R2.1.1, PR #155). Provides cross-cutting observability primitives shared by every Juniper server: health models (`DependencyStatus`, `ReadinessResponse`), the synchronous `probe_dependency` helper, structured-JSON logging (`JuniperJsonFormatter`, `configure_logging`) with `request_id` propagation, Starlette middlewares (`RequestIdMiddleware`, `PrometheusMiddleware` with bounded label cardinality per R1.1), pinned cross-service constants (`UNMATCHED_ENDPOINT_LABEL`, `READINESS_HEADER`, `LIVENESS_TICK_BUDGET_MS`, `LIVENESS_STALENESS_SECONDS`), Prometheus utilities (`get_prometheus_app`, `set_build_info`), and Sentry init (`configure_sentry`) with the SEC-10 `before_send` hook always installed. Optional extras: `[prometheus]`, `[sentry]`, `[all]`. Per-service metric definitions intentionally stay in their owning repos; this package only exposes cross-cutting infrastructure.
- `.github/workflows/ci-observability.yml` — dedicated CI pipeline for the observability package.
- `.github/workflows/publish-observability.yml` — OIDC trusted-publishing workflow for `juniper-observability` (TestPyPI → install verification → PyPI), triggered by tags matching `juniper-observability-v*` so it stays decoupled from the meta-package's own `v*` release tags. `workflow_dispatch` is enabled so operators can re-fire a publish against any tag.
- Hardcoded-values refactor (Wave 3 + Wave 4): all 6 `util/get_cascor_*.bash` REST query utilities now read `CASCOR_HOST` and `CASCOR_PORT` from the environment (defaulting to `localhost` / `8201`) so a single environment override targets every utility instead of editing each script individually.
- `util/juniper_plant_all.bash` `JUNIPER_CASCOR_HOST` is now an env-var override (`JUNIPER_CASCOR_HOST=${JUNIPER_CASCOR_HOST:-localhost}`) — useful for orchestrating remote services from a control host.
- New regression test suite `tests/test_worktree_cleanup.py` covering argument parsing, dry-run output, error handling, and the critical safety property that the new worktree is created before the old one is removed (CWD-trap prevention).
- Metrics-monitoring roadmap and design notes under `notes/code-review/` covering R1.1–R1.3 contracts and the R2.1 shared-observability migration sequence; ongoing Track 1–6 status sweeps marking shipped/blocked/open work across the ecosystem.

### Changed

- `.github/workflows/publish-observability.yml` — `verbose: true` enabled on both the TestPyPI and PyPI `pypa/gh-action-pypi-publish` steps so upload failures surface the underlying response body instead of twine's bare `Bad Request` line.
- Hardcoded-values refactor (Wave 3): `util/worktree_cleanup.bash` `MAIN_REPO` is now derived from `${BASH_SOURCE[0]}` (one directory up from the script) instead of being hardcoded to `/home/pcalnon/Development/python/Juniper/juniper-ml`. An optional `JUNIPER_ML_MAIN_REPO` environment variable overrides the derived path for test fixtures and unusual layouts. This makes the script portable across machines and CI runners.
- Test timeout constants extracted in `tests/test_wake_the_claude.py` and `tests/test_worktree_cleanup.py` (`SCRIPT_TIMEOUT_SECONDS`) instead of inline `subprocess.run(..., timeout=30)` calls.
- AGENTS.md "Utilities" section updated to document the new env-var overrides for `worktree_cleanup.bash`, `juniper_plant_all.bash`, and the `get_cascor_*.bash` utilities.

### Notes

- All 88 unittest tests pass plus the bash `test_resume_file_safety.bash` regression script; pre-commit (17 hooks: flake8, bandit, shellcheck, markdownlint, yamllint, sops-check) is clean.
- This branch is on `feature/hardcoded-values-wave3` rather than `wave1` because juniper-ml had no Wave 1 task in the master roadmap (the meta-package owns no application code that needed a constants module).
- `juniper-observability` is not yet wired into the `juniper-ml[all]` extras. It will be added once the alpha graduates and downstream services start importing from it as part of the R2.1 migration.

## [0.4.0] - 2026-04-09

**Summary**: Microservices orchestration layer (`juniper_plant_all.bash` / `juniper_chop_all.bash`), full systemd integration, V2 worktree cleanup orchestrator with CWD-safe session continuity, CasCor REST API query utilities, the `claudey` interactive launcher, and ecosystem version convergence — extras bumped to track the latest released `juniper-data-client`, `juniper-cascor-client`, and `juniper-cascor-worker`. Also incorporates the cross-project release-prep code review and remediation plan.

See [`notes/releases/RELEASE_NOTES_v0.4.0.md`](notes/releases/RELEASE_NOTES_v0.4.0.md) for the full release notes.

### Changed

- Bumped minimum versions of optional dependency extras to track latest releases:
  - `juniper-data-client` from `>=0.3.0` to `>=0.4.0` (adds batch operations and dataset versioning)
  - `juniper-cascor-client` from `>=0.1.0` to `>=0.3.0` (adds worker/snapshot/dataset methods, testing module)
  - `juniper-cascor-worker` from `>=0.1.0` to `>=0.3.0` (WebSocket-based agent, TLS support, deprecates legacy mode)

### Added

- `util/juniper_plant_all.bash` -- Microservices startup script with health checks, conda environment activation, and PID file management
- `util/juniper_chop_all.bash` -- Microservices shutdown script with graceful SIGTERM/SIGKILL escalation, PID file parsing, and orphaned worker cleanup
- Systemd integration (`--systemd` mode) for both startup and shutdown scripts, including `juniper-all-ctl` management script and `juniper-all.target` unit
- Cascor-worker integration into systemd target and startup/shutdown scripts (Phase 3)
- `util/worktree_cleanup.bash` -- V2 automated worktree cleanup orchestrator with CWD-safe session continuity
- `tests/test_worktree_cleanup.py` -- Regression tests for worktree cleanup argument parsing, dry-run, and error handling
- `util/worktree_new.bash`, `util/worktree_activate.bash`, `util/worktree_close.bash`, `util/worktree_wipeout.bash` -- Worktree management utilities
- `util/get_cascor_status.bash`, `util/get_cascor_metrics.bash`, `util/get_cascor_history.bash`, `util/get_cascor_network.bash`, `util/get_cascor_topology.bash` -- CasCor REST API query utilities
- `scripts/claude_interactive.bash` -- Interactive Claude Code agent launcher (`claudey` symlink at repo root)
- Cross-project regression analysis, remediation plans, and development roadmaps in `notes/`

### Changed

- `AGENTS.md` updated to v0.4.0 with comprehensive structure documentation, CI/CD pipeline details, and worktree/handoff procedures
- Dependabot CI action version bumps: `anthropics/claude-code-action` (1.0.62 -> 1.0.89), `actions/cache` (4.2.3 -> 5.0.4), `actions/upload-artifact` (6.0.0 -> 7.0.0), `actions/download-artifact` (8.0.0 -> 8.0.1)
- Moved worktree management and documentation utilities from `scripts/` to `util/`

### Fixed

- CI `dependency-docs` job path corrected from `scripts/generate_dep_docs.sh` to `util/generate_dep_docs.sh`
- PID file parsing in `juniper_chop_all.bash` replaced `read -d ''` (whitespace splitting) with `mapfile -t` (line-oriented) to handle multi-word PID file lines correctly
- Removed contradictory `done < PID_FILE` redirect from for-loop that iterated over an already-populated array
- `juniper_chop_all.bash` `KILL_WORKERS` default changed from hardcoded `"1"` to `"0"` to match documented behavior
- `juniper_chop_all.bash` `SIGTERM_TIMEOUT` default changed from hardcoded `"10"` to environment-variable-driven `"15"` to match documented behavior
- Worker search term narrowed from `"cascor"` to `"juniper-cascor-worker"` to prevent false-positive matches against the cascor backend
- Added `test_worktree_cleanup.py` to CI pipeline test execution
- PID reference fixes in startup scripts (`juniper_plant_all.bash`)
- Test script paths updated after `scripts/` to `util/` migration

## [0.3.0] - 2026-03-12

### Added

- `scripts/activate_conda_env.bash` — Bash helper for conda environment activation/deactivation with structured sections for compilation workflows
- `scripts/cleanup_open_worktrees.bash` — Automates git worktree cleanup by iterating through worktrees and performing status/add/pull/push operations
- `scripts/prune_git_branches_without_working_dirs.bash` — Prunes local git branches that lack corresponding working directories; supports standard and forced deletion modes
- `scripts/remove_stale_worktrees.bash` — Iterates through and removes stale git worktrees
- `scripts/test_resume_file_safety.bash` — Focused regression script that verifies invalid `--resume <file.txt>` input returns non-zero and preserves the source file
- `notes/stack_overflow_answer.txt` — Reference material on managing conda environments programmatically in bash scripts
- `notes/pull_requests/JUNIPER_2026-03-15_JUNIPER-ML_PR-TOOLING-MORE-CLAUDE-UTILS.md` — PR description archive
- `notes/DEVELOPER_CHEATSHEET.md` — Added session ID workflow documentation, `wake_the_claude.bash` quick runbook, regression-test commands, `--resume` alias handling, interactive-vs-headless launch behavior, and troubleshooting sections
- `docs/DOCUMENTATION_OVERVIEW.md` — Added navigation links for Claude session tooling runbooks
- New test coverage in `tests/test_wake_the_claude.py` for default launcher argument forwarding, permissions handling, and prompt token validation

### Changed

- `scripts/wake_the_claude.bash` — Uncommented `EFFORT_VALUE` and `MODEL_VALUE` assignments; refactored nohup logging to handle missing log files; changed debug output to standard echo; consolidated exit status checks
- `.github/workflows/ci.yml` — Standardized comment spacing for action version tags (dependabot version bumps)
- `notes/JUNIPER_2026-03-15_JUNIPER-ML_CONDA-DEPENDENCY-FILE-HEADER.md` — Renamed back from `.yaml` to `.md` (matching all other repos' naming convention)
- `CHANGELOG.md` — Added version identifiers to section headers for released versions
- Documentation formatting pass across `notes/` planning documents — standardized Markdown table alignment, added `bash` language tags to code blocks, converted URLs to Markdown link syntax

### Fixed

- `scripts/wake_the_claude.bash` — Replaced `eval`-based flag matching in `matches_pattern()` with split-and-compare logic
- `scripts/wake_the_claude.bash` — Moved `debug_log` and `redact_uuid` definitions before top-level calls to prevent `command not found` stderr noise
- `scripts/wake_the_claude.bash` — Hardened `--id` (without value) session generation to validate UUIDs across multiple fallback sources when `uuidgen` is unavailable

### Security

- `scripts/wake_the_claude.bash` — Removed a latent command-injection vector by eliminating `eval` from pattern matching

## [0.2.1] - 2026-03-06

### Added, 0.2.1

- `scripts/wake_the_claude.bash` — Shell script to launch Claude Code sessions with configurable flags, session persistence, and resume support
- `notes/SESSION_ID_VALIDATION_BUGFIX_PLAN.md` — Root cause analysis and fix plan
- `notes/SECURITY_REMEDIATION_PLAN.md` — Security vulnerability analysis and remediation plan
- `notes/pull_requests/JUNIPER_2026-03-06_JUNIPER-ML_PR-SESSION-ID-VALIDATION-BUGFIX.md` — PR description archive
- `notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md` — PR description template (adopted from sibling repos)

### Fixed, 0.2.1

- **Session ID validation**: Redirected diagnostic `echo` statements to stderr (`>&2`) in `is_valid_uuid`, `retrieve_session_id`, and `validate_session_id`, reserving stdout exclusively for return values captured via `$(...)`
- **Subshell exit status**: Moved `RETURN_VALUE=$?` to a separate line after command substitution so the exit status propagates to the parent scope
- **Double usage print**: Replaced `usage`/`exit` calls with `return` inside `validate_session_id`, since `exit` inside `$(...)` only terminates the subshell
- **Ambiguous log message**: Added `session_id_filename` local variable to preserve the original filename for the "from file" log message

### Security, 0.2.1

- **Path traversal in `--resume`** (High): Reject filenames containing path separators (`/`) or lacking `.txt` extension; removed destructive `rm -f` from `retrieve_session_id`; suppressed raw file content in error logs
- **Arbitrary file write in `save_session_id`** (High): Added UUID format validation before any filesystem write; applied `basename` defense-in-depth; scoped `session_id` as `local`
- **Argument injection via `CLAUDE_CODE_PARAMS`** (Medium): Converted from flat string to bash array; execute with `"${CLAUDE_CODE_PARAMS[@]}"` to prevent word-splitting injection

## [0.2.0] - 2026-02-27

### Added, 0.2.0

- CLAUDE.md for Claude Code onboarding
- PyPI publishing procedure documentation (`notes/pypi-publish-procedure.md`)

### Changed, 0.2.0

- Renamed package from `juniper` to `juniper-ml`
- Raised minimum Python version to `>=3.12`
- Expanded keywords in package metadata

### Fixed, 0.2.0

- Added `attestations: false` to publish.yml for both TestPyPI and PyPI steps

## [0.1.0] - 2026-02-22

### Added, 0.1.0

- Initial `juniper` meta-package with `pyproject.toml`
- Optional dependency extras: `clients`, `worker`, `all`
- GitHub Actions CI/CD publish workflow (TestPyPI + PyPI with trusted publishing)
- README with installation instructions and ecosystem overview
- MIT License

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/pcalnon/juniper-ml/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/pcalnon/juniper-ml/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/pcalnon/juniper-ml/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/pcalnon/juniper-ml/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/pcalnon/juniper-ml/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/v0.1.0
