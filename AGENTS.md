# CLAUDE.md

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-22

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

This is `juniper-ml`, a **meta-package** for the Juniper ML research platform. It provides a single `pip install juniper-ml[all]` entry point that pulls in the actual Juniper packages as dependencies, and also contains internal automation scripts used for Claude Code workflows, utility tooling for the Juniper ecosystem, and project documentation.

There is no importable Python application package in this repository. Functional behavior here is primarily package metadata (`pyproject.toml`) plus shell tooling in `scripts/` and `util/`, with regression coverage in `tests/`.

## Hazards (resident — do not relocate)

Directives whose **non-application destroys work**. Everything else in this file may
be demoted to [`docs/REFERENCE.md`](docs/REFERENCE.md) under the memory budget; these
may not, because a pointer only helps an agent that already knows to look. Adding a
new hazard here is legitimate — ratchet space out of a reference section in the same
PR rather than waiving the budget gate.

- **The orphan reaper can kill live experiments.** `util/reap_pytest_orphans.bash`
  treats reparenting to `systemd --user` as the orphan predicate — and
  `experiment_stack.bash` / `isolated_stack.bash` launch services under `nohup`, so
  healthy experiment services, orchestrators and watchdogs land there too. Two
  protection keys, either sufficient: the pid appears in a run-dir `*.pid`, or its
  cmdline references a run root. Observed 2026-08-16: a dry run called the
  orchestrator, the live cascor service and the watchdog all `WOULD REAP`.
- **`KILL_WORKERS=1` is opt-in and kills worker processes.** Default `0` in
  `util/juniper_chop_all.bash`; nohup-only, ignored under `--systemd`. Do not set it
  to "be thorough".
- **A CI-skip marker on the head commit orphans every required check.** The PR
  becomes permanently unmergeable while the aggregate rollup can still read SUCCESS —
  every context sits at "expected" forever. Never put that marker on a PR head; the
  repair is the server-side `update-branch` API, not a force-push.
- **`max_epochs` alone silently diverges the service from the CLI.** The service
  applies it only to the *initial* output pass; later passes read `output_epochs`,
  which falls back to 10000. The direct CLI aliases the two. **Any CLI-vs-service
  comparison must set both, to the same value**, or the service is quietly
  better-trained and slower than the config appears to ask for.

---

## Build & Package Commands

```bash
# Build
pip install build twine
python -m build

# Validate package
twine check dist/*

# Install locally (editable)
pip install -e .               # base (no deps)
pip install -e ".[clients]"    # client libraries
pip install -e ".[worker]"     # distributed worker
pip install -e ".[servers]"    # canopy + cascor + data service packages
pip install -e ".[tools]"      # ci-tools + doc-tools + observability
pip install -e ".[doc-tools]"  # markdown link validator (back-compat alias)
pip install -e ".[all]"        # everything (multi-GB; pulls torch via worker)

# Run all tests
python3 -m unittest -v tests/test_wake_the_claude.py
python3 -m unittest -v tests/test_env_repr_safety.py
python3 -m unittest -v tests/test_worktree_cleanup.py
python3 -m unittest -v tests/test_worktree_sweep_scripts.py
python3 -m unittest -v tests/test_cleanup_session_worktrees.py
python3 -m unittest -v tests/test_reap_pytest_orphans.py
python3 -m unittest -v tests/test_kill_helpers.py
python3 -m unittest -v tests/test_check_conda_env_torch.py
python3 -m unittest -v tests/test_requirements_drift_check.py
python3 -m unittest -v tests/test_editable_install_drift_check.py
python3 -m unittest -v tests/test_env_floor_drift_check.py
python3 -m unittest -v tests/test_prompt_discovery.py
python3 -m unittest -v tests/test_symbol_overlay.py
python3 -m unittest -v tests/test_generated_prompt_index.py
python3 -m unittest -v tests/test_thread_handoff_archive.py
python3 -m unittest -v tests/test_install_agents.py
python3 -m unittest -v tests/test_agent_suite_doctor.py
python3 -m unittest -v tests/test_agent_suite_summary.py
python3 -m unittest -v tests/test_predict_merge.py
python3 -m unittest -v tests/test_fleet_supervisor_contract.py
python3 -m unittest -v tests/test_workflow_script_paths.py
python3 -m unittest -v tests/test_doc_tools_drift.py
python3 -m unittest -v tests/test_service_fork_drift.py
python3 -m unittest -v tests/test_publish_env_policy_drift.py
python3 -m unittest -v tests/test_assert_release_tag.py
python3 -m unittest -v tests/test_pyproject_extras.py
python3 -m unittest -v tests/test_template_library_drift.py
python3 -m unittest -v tests/test_template_selection.py
python3 -m unittest -v tests/test_template_select_preview.py
python3 -m unittest -v tests/test_template_data_resolver.py
python3 -m unittest -v tests/test_scaffold_template.py
python3 -m unittest -v tests/test_open_signed_pr.py
python3 -m unittest -v tests/test_wait_for_checks.py
python3 -m unittest -v tests/test_prompt_validator_contract.py
python3 -m unittest -v tests/test_template_agent_skill_lint.py
python3 -m unittest -v tests/test_service_smoke_skill_lint.py
python3 -m unittest -v tests/test_ui_test_author_skill_lint.py
python3 -m unittest -v tests/test_agents_frontmatter.py
python3 -m unittest -v tests/test_agents_md_version_drift.py
python3 -m unittest -v tests/test_agents_md_header_schema.py
python3 -m unittest -v tests/test_agents_md_tree_drift.py
python3 -m unittest -v tests/test_coverage_gap_mapper_drift.py
python3 -m unittest -v tests/test_env_drift_check_drift.py
python3 -m unittest -v tests/test_release_train_registry.py
python3 -m unittest -v tests/test_release_train_detect.py
python3 -m unittest -v tests/test_release_train_propose.py
python3 -m unittest -v tests/test_release_train_archive_guard.py
python3 -m unittest -v tests/test_release_train_ceremony.py
python3 -m unittest -v tests/test_experiment_stack_script.py
python3 -m unittest -v tests/test_run_experiment.py
python3 -m unittest -v tests/test_list_runs.py
python3 -m unittest -v tests/test_snapshot_index.py
python3 -m unittest -v tests/test_snapshot_classify.py
python3 -m unittest -v tests/test_run_suite.py
python3 -m unittest -v tests/test_experiment_config_schemas.py
python3 -m unittest -v tests/test_experiment_suite_yamls.py
bash scripts/test_resume_file_safety.bash
# doc-link validator regression tests live in juniper-doc-tools/tests/
# and run under the dedicated `CI -- juniper-doc-tools` workflow.

# Run pre-commit hooks
pre-commit run --all-files

# Validate documentation links (requires `pip install juniper-doc-tools`
# or `pip install -e juniper-doc-tools/` for editable local development)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy --exclude pull_requests --exclude releases --exclude analysis --exclude fixes --exclude development --exclude CHANGELOG.md --cross-repo skip

# Validate documentation links (including cross-repo)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy --exclude pull_requests --exclude releases --exclude analysis --exclude fixes --exclude development --exclude CHANGELOG.md --cross-repo check
```

## Publishing

Releases are published via GitHub Actions (`.github/workflows/publish.yml`). The workflow is triggered by a GitHub release event and publishes first to TestPyPI (with install verification), then to PyPI. Both environments use trusted publishing (OIDC, no API tokens).

**Release convention (mandatory, all packages).** Every PyPI deploy — the meta-package and every
shared / sub-package — is performed by **cutting a GitHub Release** (never a bare `git push <tag>`),
and the release notes are authored from
[`notes/templates/TEMPLATE_RELEASE_NOTES.md`](notes/templates/TEMPLATE_RELEASE_NOTES.md) and
**archived under `notes/releases/`** (`RELEASE_NOTES_v<version>.md` for the meta-package;
`RELEASE_NOTES_<pkg>_v<version>.md` for a shared / sub-package). For the meta-package the Release
event triggers `publish.yml`; for a shared / sub-package, cutting the Release **creates** the
`juniper-<pkg>-v*` tag and fires its `publish-<pkg>.yml` through `release: published` (those
workflows deliberately do **not** also subscribe to `push: tags` — that double-fire raced the
immutable TestPyPI upload in juniper-ml#555). Full steps:
[`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11](notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md). (This convention drifted
during rapid concurrent refactoring — several sub-packages shipped tag-only — and is being restored.)

The shared `juniper-observability` package is published separately from the same repo (subdirectory `juniper-observability/`) by `.github/workflows/publish-observability.yml`, fired by a Release whose tag matches `juniper-observability-v*`. The remaining in-repo shared publishers follow the same Release-only pattern: `publish-ci-tools.yml`, `publish-config-tools.yml`, `publish-doc-tools.yml`, `publish-model-core.yml`, and `publish-service-core.yml`.

The shared `juniper-doc-tools` package (Wave 0 scaffold, plan
[`notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md`](notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md))
is published from subdirectory `juniper-doc-tools/` by
`.github/workflows/publish-doc-tools.yml`, triggered by tags matching
`juniper-doc-tools-v*`. It packages the markdown link validator
(`juniper-check-doc-links` console script + `python -m juniper_doc_tools`
module form) so that the 8 ecosystem repos can replace their inline
`scripts/check_doc_links.py` copies with a single PyPI dependency.

The shared `juniper-ci-tools` package (Wave 0 scaffold, plan
[`notes/JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md`](notes/JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md))
is published from subdirectory `juniper-ci-tools/` by
`.github/workflows/publish-ci-tools.yml`, triggered by tags matching
`juniper-ci-tools-v*`. It packages the dependency-documentation generator
(`juniper-generate-dep-docs` console script + `python -m juniper_ci_tools`
module form), Python port of the legacy `scripts/generate_dep_docs.sh` that
drifted across 8 Juniper repos. Replaces all consumer inline copies via a
single PyPI dependency; carries the cascor 2026-05-20 awk-extraction fix as
the canonical implementation. As of **0.8.0** it also ships the two
sequence-safety ref-diff screens — `juniper-symbol-loss-check` (AST symbol-loss)
and `juniper-docs-additions-check` (markdown deletion-magnitude), both gaining a
repeatable `--scope GLOB` knob — migrated from the two hand-copied
`util/sequence_safety/` trees (Wave 0 of the sequence-safety ecosystem rollout,
plan `notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`).

## Shared Observability Helpers

`juniper-observability` (this repo's `juniper-observability/` subdirectory, published as a standalone PyPI package) is the canonical home for cross-service observability primitives — middlewares, the build-info `Info` metric helper, structured-JSON logging, and **idempotent `prometheus_client` collector helpers**. Any new `Counter` / `Gauge` / `Histogram` / `Summary` / `Info` / `Enum` registration in any Juniper service should go through:

- `register_or_reuse(factory, name, *args, **kwargs)` — adopt-existing on duplicate (preserves accumulated samples; **default choice for almost every call site**).
- `register_fresh(factory, name, *args, **kwargs)` — drop-and-recreate (use only when test fixtures or migrations intentionally want different buckets/labels).
- `register_info_or_update(name, description, **info_labels)` — sugar for the `Info` two-step register-then-`.info({...})` pattern.
- `lazy_register_or_reuse(factory, name, *args, **kwargs)` — like `register_or_reuse` but caches the result in a module-private dict; for the lazy-init-with-`None`-sentinel pattern.

Tests touching these collectors should use `juniper_observability.testing.reset_prometheus_registry`. Minimum pin: `juniper-observability>=0.2.0`. See [`notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md`](notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md) for the design rationale and the migration history.

## Shared Service-Core Contracts

The load-bearing invariants a well-meaning refactor silently breaks in the shared FastAPI service tier. Moved to [`docs/REFERENCE.md` § Shared Service-Core Contracts](docs/REFERENCE.md#shared-service-core-contracts) — read it when working on this area.

## Repository Structure

The fully annotated repository tree, with the purpose of every directory and key file. Moved to [`docs/REFERENCE.md` § Repository Structure Reference](docs/REFERENCE.md#repository-structure-reference) — read it when working on this area.

```bash
juniper-ml/
├── AGENTS.md                  # This file (CLAUDE.md is a symlink to it)
├── conf/                      # Project configuration, incl. memory_budget.json
├── docs/                      # User-facing documentation (REFERENCE.md is the deep reference)
├── images/                    # Project branding
├── juniper-ci-tools/          # Published sub-package: CI tooling + sequence-safety screens
├── juniper-config-tools/      # Published sub-package: env-prefix migration helpers
├── juniper-doc-tools/         # Published sub-package: markdown link validator
├── juniper-model-core/        # Published sub-package: model conformance kit
├── juniper-observability/     # Published sub-package: prometheus/middleware/logging
├── juniper-service-core/      # Published sub-package: shared FastAPI service tier
├── logs/                      # Runtime log output
├── notes/                     # Design docs, plans, procedures, audits
├── papers/                    # Research papers and references
├── prompts/                   # Claude Code session prompts
│   └── agent_templates/       # Custom-agent template library + data layer
├── reports/                   # Per-run evidence artifacts
├── resources/                 # External resources
├── scripts/                   # Launcher and session scripts
├── tests/                     # Regression suites
└── util/                      # Utility scripts and tools
```

## Key Files

### Package and Metadata

- `pyproject.toml` -- Package metadata, version (`0.6.0`), and optional dependency groups (`clients`, `worker`, `servers`, `tools`, `doc-tools`, `all`)
- `README.md` -- PyPI landing page content
- `CHANGELOG.md` -- Version history in Keep a Changelog format
- `MANIFEST.in` -- Source distribution file includes
- `LICENSE` -- MIT License

### Documentation

- `docs/DOCUMENTATION_OVERVIEW.md` -- Navigation index for all juniper-ml documentation
- `docs/QUICK_START.md` -- Installation and verification guide
- `docs/REFERENCE.md` -- Technical reference: extras, compatibility matrix, service ports, environment variables
- `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` -- Quick-reference card for development tasks

### Scripts and Launchers

- `scripts/wake_the_claude.bash` -- Claude Code launcher with flag parsing, session ID persistence, resume handling, and interactive/headless execution modes
- `scripts/claude_interactive.bash` -- Main interactive Claude Code agent launcher
- `scripts/default_interactive_session_claude_code.bash` -- Configuration template for default interactive Claude sessions
- `scripts/activate_conda_env.bash` -- Conda environment activation and management
- `scripts/resume_session.bash` -- Convenience wrapper for resuming a Claude Code session
- `claudey` -- Repo-root symlink to `scripts/claude_interactive.bash` for interactive sessions

### Utilities

Per-script reference for everything in `util/`, including the failure class each guard encodes. Moved to [`docs/REFERENCE.md` § Utility Script Reference](docs/REFERENCE.md#utility-script-reference) — read it when working on this area.

### Tests

Per-suite descriptions for every regression test, and the failure class each one pins. Moved to [`docs/REFERENCE.md` § Test Suite Reference](docs/REFERENCE.md#test-suite-reference) — read it when working on this area.

### CI/CD Workflows

- `.github/workflows/ci.yml` -- Main CI pipeline: pre-commit (G4 changed-files split — `pull_request` / `merge_group` use `--from-ref <BASE> --to-ref HEAD`; `push` keeps `--all-files`), unit tests, release-train archive-guard (PR-only), the two ADVISORY standalone jobs `Sequence Safety` (per-PR G1/G2 screens + `sequence-safety-report` artifact + WARN-only `allow-symbol-loss` / `docs-rewrite` label hatch) and `Fleet PR Lint` (`cursor/*`, warnings-only), build, docs, security, dependency docs.
- `.github/workflows/main-verify.yml` -- Post-merge main-verification (P2 gate G3): on `push:main` (per-SHA, no-cancel) it installs `juniper-ci-tools` (>=0.8.0) and runs the `juniper-symbol-loss-check` (explicit ml `--scope`) + `juniper-docs-additions-check` screens over `BASE..<merge>` (`sequence-safety-report`), a path-gated battery mirror + failure-only `notify`. G3.1 CATCH-UP BASE = last successful main-verify tip that is an ancestor of HEAD, else `github.event.before`, else `HEAD^1`.
- `.github/workflows/publish.yml` -- Meta PyPI publish: TestPyPI **Gate 1** verify (bare -> `[clients]` -> `[tools]`, never `--no-deps`, never the heavy extras), then PyPI (`needs: testpypi`, OIDC). The `build` job is tag-guarded to `v*` Releases so a `juniper-<pkg>-v*` Release cannot fire the meta publisher. Gate: `tests/test_publish_testpypi_verify.py`. Operator surface: [`docs/REFERENCE.md` § Meta-Package Publish Pipeline](docs/REFERENCE.md#meta-package-publish-pipeline).
- `.github/workflows/publish-*.yml` -- Six shared sub-package publishers. All are **Release-only** (`release: published` + `workflow_dispatch`; deliberately **no** `push: tags`, which double-fired and raced TestPyPI in juniper-ml#555), each build job gated on its own `startsWith(github.event.release.tag_name, '<pkg>-v')`, with a `--no-deps` TestPyPI-only verify and `skip-existing: true` on both publish steps. Operator table: [`docs/REFERENCE.md` § Independent Sibling Package Publish Pipelines](docs/REFERENCE.md#independent-sibling-package-publish-pipelines).
- `.github/workflows/ci-*.yml` -- Six in-repo shared-package CIs (`ci-tools` / `config-tools` / `doc-tools` / `model-core` / `observability` / `service-core`), distinct from meta `ci.yml` and from `publish-*.yml`.
  Path filters must include `<subdir>/**` **and** the workflow's own path; matrices carry declared Python floors; coverage uses `--cov-fail-under` plus a blocking `juniper-coverage-gap-map --enforce` (only ci-tools may `--omit`
  `__main__.py`); `build.needs: test`; service-core installs sibling `juniper-model-core` from the monorepo root (no test-job `working-directory`).
  Gate: `tests/test_subpackage_ci_workflows.py`. Operator table: [`docs/REFERENCE.md` § Shared-Package CI Workflows](docs/REFERENCE.md#shared-package-ci-workflows).
- `.github/workflows/docs-full-check.yml` -- Weekly full documentation link validation including cross-repo checks. `env.ECOSYSTEM_REPOS` (the clone list) must equal the registry's publishing repos minus `juniper-ml` plus `juniper-deploy`; omitting a sibling silently drops it from every weekly screen. Gate: `tests/test_docs_full_check_ecosystem.py`. Operator surface: [`docs/REFERENCE.md` § Docs Full Check](docs/REFERENCE.md#docs-full-check).
- `.github/workflows/security-scan.yml` -- Weekly `pip-audit --strict --desc on` after `pip install -e .` (read-only permissions). Deliberately unlike the per-PR `ci.yml` `security` job, which uses `--skip-editable` and omits `--strict` so an unreleased editable meta install cannot fail every PR. Do not copy either contract onto the other path. Gate: `tests/test_security_scan_workflow.py`.
- `.github/workflows/lockfile-update.yml` -- Weekly (Monday 08:00 UTC) `juniper-generate-dep-docs` refresh; a SHA-pinned `peter-evans/create-pull-request` opens `chore/lockfile-update` with labels `dependencies` + `automated` (permissions exactly `contents: write` + `pull-requests: write`). Never resurrect the deleted `util/generate_dep_docs.sh` (juniper-ml#298). Gates: `tests/test_lockfile_update_workflow.py` (structure) + `tests/test_ci_tools_drift.py` (pin ceiling).
- `.github/workflows/release-train.yml` -- Daily (13:00 UTC) PyPI release-train orchestrator.
  - The `detect` job (report path) runs `util/release_train/detect.py` over the 18-package registry and renders a step-summary table; it never writes.
  - Two opt-in write-scoped lanes gate on the resolved mode: `propose` (Phase 2.2/4.1 — standard-gated proposal PRs) and `ceremony` (Phase 4.3 — exempt archive PR + Release cut → owner-gated `pypi` Gate 2).
  - Mode switch / rollback: repo variable `RELEASE_TRAIN_MODE` (`off`|`report`|`propose`|`ceremony`, default `report`) + a dispatch `mode` override; `off` quiesces entirely.
  - Operator guide: `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`.
- `.github/workflows/pr-budget-alarm.yml` -- Daily (14:00 UTC) scheduled open-PR budget alarm (flood-remediation guardrail, analysis §4 item 9 / P1 §5): counts total open PRs + `cursor/`-headed PRs against repo variables `PR_BUDGET_WARN` (default 15) / `PR_BUDGET_ALARM` (default 30), always writes a step-summary table, and on breach posts to Slack via `SLACK_WEBHOOK_URL` under the non-blocking contract mirrored from `release-train.yml`. Report-only -- a breach never blocks a PR.
- `.github/workflows/claude.yml` -- Claude Code action for issue/PR automation (@claude mentions)
- `.github/workflows/agents-md-touch-up.yml` -- **Verifies** (never rewrites) `AGENTS.md`'s `**Last Updated**:` field on every PR that touches `AGENTS.md`: the value must be a well-formed `YYYY-MM-DD`, not in the future, and **either already equal to today's UTC date OR changed in this PR** (`git diff <base>...HEAD`); a missing field warns and passes. Job `Verify AGENTS.md Last Updated`, `permissions: contents: read`, no fork guard (verification needs no token).
  - The **already-today** arm is a real escape hatch, not a rounding of the rule: a second same-day PR touching `AGENTS.md` — or a **stacked** PR whose base branch already carries the bump, so the line legitimately does not appear in its own diff — passes on the value alone. Only the changed-in-this-PR arm is available once the date is stale, which is why a stacked pair that sits overnight needs its base re-bumped rather than the child edited.
  - It used to bump the date and push the commit itself. Removed in juniper-ml#1099: a runner's local `git commit` is UNSIGNED, which `required_signatures` rejects (an unsigned commit anywhere in the history blocks the merge; squash does not rescue it), and the `[skip ci]` bump commit became the PR head so **no required context ever reported on it** -- the PR sat permanently BLOCKED with every check at "expected" (cascor#515). It also raced `Update Lockfile (Dependabot)` for the push slot.
  - The predicate is "the line changed", not "equals today", so a PR that spans days keeps passing on re-run. `propose.py` sets the header in its own commit, so release proposals satisfy it as authored.
  - Companion to `tests/test_agents_md_header_schema.py`; gate: `tests/test_agents_md_touch_up.py` (11 arms incl. an anti-resurrection assertion that the shell can never `git commit` / `git push` / `sed -i`). Operator surface: [`docs/REFERENCE.md` § AGENTS.md Date Check](docs/REFERENCE.md#agentsmd-date-check).
- `util/validate_claude_yaml_access.bash` -- Structural auditor for public-repo `ANTHROPIC_API_KEY` safeguards (L2: no `pull_request_target` / `workflow_run`; L3: the `claude:` job `if:` must `contains(..., '@claude')`).
  Per-PR via `ci.yml`'s `claude-yaml-audit` job (Quality Gate); weekly via `docs-full-check.yml` under `JUNIPER_ROOT`. The `JUNIPER_ROOT` fan-out iterates the hard-coded `DEFAULT_REPOS` array (registry publishers plus `juniper-deploy`),
  **not** every cloned directory — it is orthogonal to `ECOSYSTEM_REPOS`, and the two lists must move together when a publishing sibling is added.
  Gate: `tests/test_validate_claude_yaml_access.py`. Operator surface: [`docs/REFERENCE.md` § Claude.yml Access Validation](docs/REFERENCE.md#claudeyml-access-validation).

### Configuration

- `.pre-commit-config.yaml` -- Pre-commit hooks: flake8, bandit, shellcheck, markdownlint, yamllint, SOPS env check
- `.markdownlint.yaml` -- Markdown linting rules (line length: 512, ol-prefix disabled)
- `.sops.yaml` -- SOPS encryption configuration for `.env` and `.env.secrets` using age key
- `.serena/project.yml` -- Serena code agent integration (project: juniper_ml, language: python)
- `.gitattributes` -- Git LFS tracking for image files (jpg, png, ico, xcf, svg, etc.)
- `.github/CODEOWNERS` -- Code ownership: @pcalnon for all files
- `.github/dependabot.yml` -- Automated dependency updates: pip (weekly) and github-actions (weekly)

## CI/CD Pipelines

What each workflow does, its triggers, and the contract each job must not break. Moved to [`docs/REFERENCE.md` § CI/CD Pipeline Reference](docs/REFERENCE.md#cicd-pipeline-reference) — read it when working on this area.

### PR base-branch guard (required check)

`.github/workflows/pr-base-branch-guard.yml` fails any PR whose base is not the default
branch. Its job name -- **`Guard PR base branch`** -- is a **required status check**, so
renaming the job or deleting the file makes `main` unmergeable until it is un-required.
A stacked PR is governed by **no ruleset at all** (both are `~DEFAULT_BRANCH`-scoped), so
it merges with zero checks; this guard is the only thing that runs there. Moved to
[`docs/REFERENCE.md` § PR Base-Branch Guard](docs/REFERENCE.md#pr-base-branch-guard) --
read it when working on this area.

## Pre-commit Hooks

Setup:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Configured hooks (`.pre-commit-config.yaml`):

| Hook Group         | Version   | Scope                                            | Purpose                                                                                                                       |
|--------------------|-----------|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| pre-commit-hooks   | v4.6.0    | All files                                        | YAML/TOML/JSON check, EOF fixer, trailing whitespace, merge conflicts, large files, AST check, debug statements, private keys |
| flake8             | 7.1.1     | `scripts/`, `tests/` `.py`                       | Python linting (max-line-length: 512) with bugbear, comprehensions, simplify                                                  |
| bandit             | 1.9.4     | `scripts/`, `tests/` `.py`                       | Python security scanning                                                                                                      |
| shellcheck         | v0.10.0.1 | `.sh`, `.bash`                                   | Shell script linting (severity: warning)                                                                                      |
| markdownlint       | v0.42.0   | `.md` (excl. CHANGELOG, notes/, docs/, prompts/) | Markdown linting with auto-fix                                                                                                |
| yamllint           | v1.35.1   | YAML files                                       | YAML linting (relaxed mode)                                                                                                   |
| no-unencrypted-env | local     | `.env`, `.env.secrets`                           | Blocks unencrypted env files from commit                                                                                      |

## Secrets Management (SOPS)

The repository uses [SOPS](https://github.com/getsops/sops) with age encryption for secrets:

- **Encrypted files**: `.env`, `.env.secrets` (matched by `.sops.yaml`)
- **Encryption key**: age key configured in `.sops.yaml`
- **Existing encrypted file**: `.env.enc`
- **Pre-commit protection**: The `no-unencrypted-env` hook blocks unencrypted `.env` files from being committed
- **Usage guide**: `notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md`

## Ecosystem Context

This repo is part of the broader Juniper ecosystem. See the parent directory's `CLAUDE.md` at `/home/pcalnon/Development/python/Juniper/CLAUDE.md` for the full project map, dependency graph, shared conventions, and conda environment details.

### Dependency extras reference

| Extra        | Packages                                                                                                                                                                                                     |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clients`    | `juniper-data-client>=0.4.1`, `juniper-cascor-client>=0.5.0`                                                                                                                                                 |
| `worker`     | `juniper-cascor-worker>=0.4.0`                                                                                                                                                                               |
| `servers`    | `juniper-canopy>=0.5.0`, `juniper-cascor>=0.5.0`, `juniper-data>=0.6.0`                                                                                                                                      |
| `tools`      | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.2.0`, `juniper-service-core>=0.2.0,<0.6.0` |
| `doc-tools`  | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)                                                                                                                     |
| `recurrence` | `juniper-recurrence-model>=0.1.5,<0.3.0`, `juniper-recurrence>=0.2.0,<0.4.0`, `juniper-recurrence-client>=0.2.0,<0.3.0`                                                                                      |
| `all`        | All of the above                                                                                                                                                                                             |

## Conventions

- Python >=3.12 required (classifiers include 3.12, 3.13, 3.14)
- Package name on PyPI: `juniper-ml`
- Import name: none (meta-package, no importable modules)
- Version tracked in `pyproject.toml` under `[project].version`
- Line length: 512 for all linters (flake8, markdownlint)
- Shell scripts use bash with `shellcheck` compliance
- Markdown files use `.markdownlint.yaml` configuration
- `notes/` documents are named `JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<CONTENTS-DESCRIPTION-PHRASE>.md` (REPO one of ML / CANOPY / RECURRENCE / CASCOR / CASCOR-CLIENT / CASCOR-WORKER / DATA / DATA-CLIENT / DEPLOY / ECOSYSTEM). Exempt: `notes/{templates,releases,requirements,legacy}/` and README files. Full rules + migration record: [`notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md)

### Script placement (mandatory)

Utility, single-use, temporary, and unfinished scripts MUST be created under `util/`:

| Script type                                    | Destination                    |
| ---------------------------------------------- | ------------------------------ |
| Permanent utility, regularly used              | `util/<name>.{py,bash}`        |
| Single-use, temporary, ad-hoc, or unfinished   | `util/ad-hoc/<name>.{py,bash}` |

**`/tmp/` is prohibited** as the home for any script that produces, modifies, or analyzes repository content. `/tmp/` is reaped when sessions / sandboxes / containers end, and scripts placed there are lost. `/tmp/` remains acceptable as a scratch *workspace* for intermediate artifacts that the script itself creates and reads (e.g., `uv pip compile -o /tmp/lock && mv /tmp/lock requirements.lock`) — the prohibition is on script *source files*, not on transient data.

**Incident motivating this rule**: `phase4_consolidate.py` and `v2_citation_validate.py` were authored in `/tmp/` across the v1-v4 requirements snapshot effort and are now irrecoverable. See [`notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §7](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection) and [plan-doc §12](notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md#12-open-issues--questions-discovered-during-execution).

See [`util/ad-hoc/README.md`](util/ad-hoc/README.md) for the ad-hoc-script convention (file-header requirements, when to graduate to `util/` proper).

---

## Pull Request Conventions

### Requirements (JR-ID) cross-references

PR descriptions on juniper-ml SHOULD include a `## Requirements` section that lists the [`JR-<REPO>-<AREA>-<NNN>` IDs](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md) this PR touches. The repository-level [`.github/pull_request_template.md`](.github/pull_request_template.md) pre-fills the section; delete it only if no tracked requirement applies.

**Verb conventions** (from [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §4](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#4-jr-id-references-in-prs)):

| Verb                    | Meaning                                                                            | Refresh-time effect       |
| ----------------------- | ---------------------------------------------------------------------------------- | ------------------------- |
| `Closes JR-*`           | This PR fully satisfies the requirement.                                           | Status → `shipped`.       |
| `Partially closes JR-*` | This PR satisfies some of the requirement; describe which parts in the same line.  | Status unchanged.         |
| `References JR-*`       | This PR is informed by but does not change the requirement.                        | Status unchanged.         |
| `Supersedes JR-*`       | This PR's design replaces an earlier requirement.                                  | Old entry → `superseded`. |

**Looking up an ID**:

- Browse [`notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md) or [`notes/requirements/by-area/<CODE>.md`](notes/requirements/) for human-readable views.
- For programmatic queries, see [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §3 recipes](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#3-snapshot-consumption-recipes).
- Never `grep` `id_assignments.yaml` for content — briefs there are truncated.

**Scope**: Apply the convention in PR *descriptions* only — not commit messages. CI lint validating IDs is deferred until the convention has organic uptake (see [`JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §6](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#6-ci-lint-validating-jr-id-references)).

### Other PR description conventions

For larger / cross-cutting PRs, the long-form template at [`notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md`](notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md) covers Summary, Context, Priority table, Keep-a-Changelog grouping, Impact/SemVer, Testing, and rollback plans. The repo-level `.github/pull_request_template.md` is the lightweight default; the long-form template is opt-in for PRs that warrant it.

---

## Worktree Procedures (Mandatory -- Task Isolation)

> **OPERATING INSTRUCTION**: All feature, bugfix, and task work SHOULD use git worktrees for isolation. Worktrees keep the main working directory on the default branch while task work proceeds in a separate checkout.

### What This Is

Git worktrees allow multiple branches of a repository to be checked out simultaneously in separate directories. For the Juniper ecosystem, all worktrees are centralized in **`/home/pcalnon/Development/python/Juniper/worktrees/`** using a standardized naming convention.

The full setup and cleanup procedures are defined in:

- **`notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`** -- Creating a worktree for a new task
- **`notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`** -- Merging, removing, and pushing after task completion (V2 -- fixes CWD-trap bug)

Read the appropriate file when starting or completing a task.

### Worktree Directory Naming

Format: `<repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>`

Example: `juniper-ml--chore--update-deps--20260225-1430--519bda91`

- Slashes in branch names are replaced with `--`
- All worktrees reside in `/home/pcalnon/Development/python/Juniper/worktrees/`

### When to Use Worktrees

| Scenario                                    | Use Worktree? |
| ------------------------------------------- | ------------- |
| Feature development (new feature branch)    | **Yes**       |
| Bug fix requiring a dedicated branch        | **Yes**       |
| Quick single-file documentation fix on main | No            |
| Exploratory work that may be discarded      | **Yes**       |
| Hotfix requiring immediate merge            | **Yes**       |

### Quick Reference

**Setup** (full procedure in `notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`):

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git checkout main && git pull origin main
BRANCH_NAME="chore/my-task"
git branch "$BRANCH_NAME" main
REPO_NAME=$(basename "$(pwd)")
SAFE_BRANCH=$(echo "$BRANCH_NAME" | sed 's|/|--|g')
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/${REPO_NAME}--${SAFE_BRANCH}--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD)"
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
cd "$WORKTREE_DIR"
```

**Cleanup** (full procedure in `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`):

```bash
# Phase 1: Push current work
cd "$OLD_WORKTREE_DIR" && git push origin "$OLD_BRANCH"
# Phase 2: Create new worktree BEFORE removing old (prevents CWD-trap)
git fetch origin
git worktree add "$NEW_WORKTREE_DIR" -b "$NEW_BRANCH" origin/main
cd "$NEW_WORKTREE_DIR"
# Phase 3: Create PR (do NOT merge directly to main)
gh pr create --base main --head "$OLD_BRANCH" --title "<title>" --body "<body>"
# Phase 4: Cleanup
git worktree remove "$OLD_WORKTREE_DIR"
git branch -d "$OLD_BRANCH"
git worktree prune
# Phase 6: Sync to latest main (Case A — still in the continuity worktree): sync in place
git fetch --all && git pull --ff-only origin main
# Case B (terminal — no session worktrees left): git fetch --all && git checkout main && git pull --ff-only origin main
# Phase 7 (always, after every merged-PR cleanup): restore the PRIMARY checkout to up-to-date main
# (skip if its tree is dirty — F-6 stale-checkout guard)
cd <path-to-repo-root> && git checkout main && git pull --ff-only origin main
```

**Automated cleanup** (via script):

```bash
util/worktree_cleanup.bash \
  --old-worktree "$OLD_WORKTREE_DIR" \
  --old-branch "$OLD_BRANCH" \
  --parent-branch main
```

### Rules

- **Centralized location**: All worktrees go in `/home/pcalnon/Development/python/Juniper/worktrees/`. Never create worktrees inside the repo directory.
- **Clean before you start**: Ensure the main working directory is clean before creating a worktree.
- **Push before you merge**: Always push the working branch to remote before merging (backup).
- **Prune after cleanup**: Run `git worktree prune` after removing a worktree to clean metadata.
- **Do not leave stale worktrees**: Clean up worktrees promptly after merging.

---

## Thread Handoff (Mandatory -- Replaces Thread Compaction)

> **CRITICAL OPERATING INSTRUCTION**: Thread handoff MUST be performed instead of
> thread compaction. This section defines mandatory behavior that overrides Claude
> Code's default compaction process.

### What This Is

When a long-running conversation approaches context limits, Claude Code normally
performs **thread compaction** -- summarizing prior context to free token capacity.
This introduces information loss. Instead, Claude Code instances working on this
project MUST perform a **proactive thread handoff**: transferring a curated,
high-signal summary to a fresh thread with full context capacity.

The full handoff protocol is defined in **`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`**.
Read that file when a handoff is triggered.

### When to Trigger a Handoff

**Automatic trigger (pre-compaction threshold):** Initiate a thread handoff when
token utilization reaches **95% to 99%** of the level at which thread compaction
would normally be triggered. This means the handoff fires when you are within
**1% to 5%** of the compaction threshold, ensuring the handoff completes before
compaction would occur.

Concretely:

- If compaction would trigger at N% context utilization, begin handoff at
  (N - 5)% to (N - 1)%.
- **Self-assessment rule**: At each turn where you are performing multi-step work,
  assess whether you are approaching the compaction threshold. If you estimate you
  are within 5% of it, begin the handoff protocol immediately.
- When the system compresses prior messages or you receive a context compression
  notification, treat this as a signal that handoff should have already occurred --
  immediately initiate one.

**Additional triggers** (from `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`):

| Condition                   | Indicator                                            |
| --------------------------- | ---------------------------------------------------- |
| **Context saturation**      | 15+ tool calls or 5+ files edited                    |
| **Phase boundary**          | Logical phase of work is complete                    |
| **Degraded recall**         | Re-reading files or re-asking resolved questions     |
| **Multi-file transition**   | Moving between major concerns                        |
| **User request**            | User says "hand off", "new thread", or similar       |

**Do NOT handoff** when:

- Task is nearly complete (< 2 remaining steps)
- Current thread is still sharp and producing correct output
- Work is tightly coupled and splitting would lose in-flight state

### How to Execute a Handoff

1. **Checkpoint**: Inventory what was done, what remains, what was discovered,
   and what files are in play
2. **Compose the handoff goal**: Write a concise, actionable summary
   (see templates in `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`)
3. Combine checkpoint and handoff goal to create a detailed thread handoff prompt
4. **Present to user**: Output the handoff prompt and recommend starting a new
   thread with that handoff as the initial prompt
5. Archive the thread handoff prompt to prompts/thread-handoff_automated-prompts/ dir with filename convention: HANDOFF_YYYY-MM-DD_[Session Description].md
6. **Include verification commands**: Specify how the new thread should verify
   its starting state in the handoff prompt
7. **State git status**: Mention branch, staged files, and uncommitted work in handoff prompt

### Rules

- **This is not optional.** Every Claude Code instance on this project must
  follow these rules.
- **Handoff early, not late.** A handoff at 70% context is better than
  compaction at 95%.
- **Do not duplicate CLAUDE.md content** in the handoff goal.
- **Be specific**: Include file paths, decisions made, and verification status.
