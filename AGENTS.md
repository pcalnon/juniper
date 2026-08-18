# CLAUDE.md

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

This is `juniper-ml`, a **meta-package** for the Juniper ML research platform. It provides a single `pip install juniper-ml[all]` entry point that pulls in the actual Juniper packages as dependencies, and also contains internal automation scripts used for Claude Code workflows, utility tooling for the Juniper ecosystem, and project documentation.

There is no importable Python application package in this repository. Functional behavior here is primarily package metadata (`pyproject.toml`) plus shell tooling in `scripts/` and `util/`, with regression coverage in `tests/`.

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

`juniper-service-core` (this repo's `juniper-service-core/` subdirectory) owns the shared FastAPI middleware, the `/ws/control` security + command dispatch, and the distributed worker pool that model services inject executors into. The load-bearing invariants — the ones a well-meaning refactor silently breaks:

- **CR-024 body limit** — `RequestBodyLimitMiddleware` treats `Content-Length` as an early-reject hint only and **always** stream-caps `POST` / `PUT` / `PATCH` against the cumulative limit (default 10 MiB), so an under-declared header or a chunked body with none still 413s. Skipping the stream when the declared length is present-and-small is the classic bypass.
- **Auth before rate limit** — with API keys configured, `APIKeyAuth` runs first, so a 401 never consumes a rate-limit token. Blank / whitespace-only configured keys are filtered out (the `auth_posture.real_keys` rule) so an empty secret file cannot enable auth that then accepts an empty `X-API-Key`.
- **429 header passthrough** — `RateLimiter` raises `HTTPException` carrying `Retry-After` + `X-RateLimit-*`; `SecurityMiddleware.dispatch` must rebuild `JSONResponse(..., headers=exc.headers)`. RateLimiter unit tests alone do not exercise that catch path.
- **Control-WS log sanitizing** — reject logs that interpolate untrusted Origin / command text go through the module-local `_sanitize_for_log` helpers (`control_security` strips `\r`/`\n`; `control_stream` also drops other C0 controls, keeping tab) so CRLF cannot forge multi-line control-plane records. Sanitizing changes log records only, never handshake outcomes or ack JSON.
- **Zero rate limit** — `ws_control_rate_limit_per_sec=0` builds a `LeakyBucket` with no refill; `retry_after` returns `3600.0` (hard backoff) rather than dividing by zero and tearing down the receive loop.
- **`/ws/workers` fail-closed** — a bad/missing `X-API-Key` closes **4001** without accepting; a non-object or shape-invalid registration closes **4008** with no `registration_ack`; `submit_result` rejects wrong-worker / unassigned results before the protocol parse; binary attachments over 100 MB get `Binary frame too large`. Control receive rejects malformed / non-object JSON with close **1003** rather than an `AttributeError`.

Operator surface: [`docs/REFERENCE.md` § juniper-service-core](docs/REFERENCE.md#juniper-service-core).

## Repository Structure

```bash
juniper-ml/
├── AGENTS.md                  # This file (CLAUDE.md is a symlink to this)
├── CHANGELOG.md               # Version history (Keep a Changelog format)
├── LICENSE                    # MIT License
├── MANIFEST.in                # Source distribution includes
├── README.md                  # PyPI landing page content
├── pyproject.toml             # Package metadata, version, dependency extras
├── claudey                    # Symlink -> scripts/claude_interactive.bash
│
├── .claude/                   # Custom-agent suite surface (git-tracked via .gitignore negation; design D-6)
│   ├── agents/
│   │   ├── prompt-validator.md  # PR 3: headless validator subagent (applies RUBRIC R1-R5 -> pinned typed JSON verdict)
│   │   ├── planner.md           # Round-2: Planning subagent -> design/plan/analysis doc in notes/ (read-heavy + Write)
│   │   ├── auditor.md           # Round-2: Audit subagent -> findings report in notes/ (read-heavy + WebFetch + Write)
│   │   ├── mock-seam-auditor.md # E-5: read-only masked-seam hunter (autouse/session mocks of an integration boundary)
│   │   ├── task-executor.md     # Round-2: Task subagent -> code changes via PR (worktree isolation; may fan out)
│   │   └── fleet-supervisor.md  # Flood §4 item 7: read-only open-PR-set triage (predicted-merge via util/fleet_triage; cluster/order/dup; never pushes)
│   └── skills/
│       └── template-agent/SKILL.md  # PR 5: interactive orchestrator Skill (bounded state machine; opus + effort max)
│
├── .github/
│   ├── CODEOWNERS             # Code ownership (@pcalnon)
│   ├── dependabot.yml         # Automated dependency updates (pip + actions)
│   └── workflows/
│       ├── ci.yml             # Main CI pipeline (pre-commit, tests, build, docs, security)
│       ├── main-verify.yml    # Post-merge main verification (G3: symbol/docs-loss screen + gated battery + notify)
│       ├── publish.yml        # PyPI publishing (TestPyPI + PyPI, OIDC)
│       ├── docs-full-check.yml# Weekly full documentation link validation (cross-repo; ECOSYSTEM_REPOS clone list)
│       ├── security-scan.yml  # Weekly pip-audit --strict security scanning
│       ├── lockfile-update.yml# Weekly juniper-generate-dep-docs -> chore/lockfile-update PR
│       ├── ci-*.yml           # Six shared sub-package CIs (ci-tools/config-tools/doc-tools/model-core/observability/service-core)
│       ├── publish-*.yml      # Six shared sub-package PyPI publishers (Release-tag-prefix guarded)
│       ├── release-train.yml  # Daily PyPI release-train detection (report-only, Phase 1)
│       └── claude.yml         # Claude Code action for issue/PR automation
│
├── .serena/                   # Serena code agent integration config
│   └── project.yml            # Project: juniper_ml, language: python
│
├── juniper-ci-tools/          # Published sub-package: dependency-docs generator (juniper-generate-dep-docs)
├── juniper-config-tools/      # Published sub-package: env-prefix migration helpers (stdlib-only)
├── juniper-doc-tools/         # Published sub-package: markdown link validator (juniper-check-doc-links)
├── juniper-model-core/        # Published sub-package: model-core conformance kit + crossval layer
├── juniper-observability/     # Published sub-package: shared prometheus/middleware/logging helpers
├── juniper-service-core/      # Published sub-package: shared FastAPI service-tier primitives
│
├── docs/                      # User-facing documentation
│   ├── DOCUMENTATION_OVERVIEW.md         # Navigation index for all docs
│   ├── QUICK_START.md                    # Installation and verification guide
│   ├── REFERENCE.md                      # Extras, compatibility, env vars, service ports
│   └── DEVELOPER_CHEATSHEET_JUNIPER-ML.md# Quick-reference card for development tasks
│
├── conf/                      # Project configuration files
├── images/                    # Project branding (logos v0-v9 in PNG/XCF/ICO, tree photos)
├── logs/                      # Runtime log output (.gitkeep)
├── papers/                    # Research papers and references
├── reports/                   # Per-run evidence artifacts (e2e/<RUN_ID>/statuses.tsv — canopy E2E arc verdicts)
├── resources/                 # External resources (AppImages, etc.)
│
├── notes/                     # Development notes, plans, and procedures
│   ├── JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md       # Worktree creation procedure
│   ├── JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md  # Worktree cleanup procedure (CWD-safe)
│   ├── JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md       # Thread handoff protocol
│   ├── JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md              # Secrets encryption guide
│   ├── backups/               # Backup analysis/plan documents
│   ├── concurrency/           # Concurrency-related handoff notes
│   ├── development/           # Development analysis documents
│   ├── documentation/         # Documentation audit plans
│   ├── history/               # Historical plans and procedures
│   ├── proposals/             # Research proposals
│   ├── pull_requests/         # PR description archives
│   └── templates/             # Document templates (roadmap, issue, PR, release notes)
│
├── prompts/                   # Claude Code session prompts (chronological archive)
│   ├── agent_templates/       # Custom-agent prompt templates: manifest.yaml + generic.md + RUBRIC (drift-linted)
│   │   └── data/              # PR 6b: data layer (standing_rules/anti_hallucination/conventions/ecosystem/known_misses .yaml)
│   └── generated/             # PR 5: emission target for /template-agent output (.gitkeep)
│
├── scripts/                   # Claude Code launcher and test scripts
│   ├── wake_the_claude.bash              # Core launcher: flag parsing, session persistence, resume
│   ├── claude_interactive.bash           # Interactive Claude Code agent launcher
│   ├── default_interactive_session_claude_code.bash  # Config template for interactive sessions
│   ├── activate_conda_env.bash           # Conda environment management
│   ├── resume_session.bash               # Session resume convenience wrapper
│   ├── cleanup_session_worktrees.py      # Bulk-clean Claude Code session worktrees in .claude/worktrees/
│   ├── test.bash                         # End-to-end test harness for launcher flows
│   ├── test_resume_file_safety.bash      # Regression: invalid --resume input safety
│   ├── test_prompt-*.md                  # Test prompt files for launcher testing
│   ├── sessions/                         # Session ID storage (.gitkeep)
│   └── backups/                          # Backup copies of older script versions
│
├── tests/                     # Regression test suites (Python unittest)
│   ├── test_wake_the_claude.py           # Launcher script regression (1470 lines)
│   ├── redacted_env.py                   # RedactedEnv helper: subprocess env mapping with masked repr (secret-leak class)
│   ├── test_env_repr_safety.py           # Lint gate: no raw os.environ-derived subprocess env in tests/ + RedactedEnv behaviour
│   ├── test_worktree_cleanup.py          # Worktree cleanup script tests (225 lines)
│   ├── test_worktree_sweep_scripts.py    # Ad-hoc sweep script safety/contract tests
│   ├── test_cleanup_session_worktrees.py # Session .claude/worktrees cleaner (merged-PR fail-closed + dry-run)
│   ├── test_reap_pytest_orphans.py       # Orphan pytest process reaper tests
│   ├── test_kill_helpers.py              # Emergency kill helpers: process-filter / kill-path (hermetic PATH stubs)
│   ├── test_check_conda_env_torch.py     # Hermetic P-5 torch._C shadow diagnostic exit matrix (0/1/2/3/4)
│   ├── test_requirements_drift_check.py  # Requirements snapshot drift checker tests
│   ├── test_editable_install_drift_check.py # Editable-install drift checker tests (orphaned / worktree-pinned)
│   ├── test_env_floor_drift_check.py     # Lint/behavioural: util/env_floor_drift_check.py floor-drift (I-2; synthetic dist-info)
│   ├── test_prompt_discovery.py          # Behavioural: util/prompt_discovery/ grounding-bundle (schema + provenance + cold/empty)
│   ├── test_symbol_overlay.py            # Serena symbol overlay (OQ-8) deterministic merge (Serena wins, grep fallback)
│   ├── test_generated_prompt_index.py    # Behavioural: util/generated_prompt_index.py index + safety-gated prune/archive (P4)
│   ├── test_thread_handoff_archive.py    # Drift: archived handoff prompt filenames + top-level note references
│   ├── test_install_agents.py            # Behavioural: util/install_agents.bash ~/.claude mirror (idempotent/reversible/dry-run/no-clobber)
│   ├── test_agent_suite_doctor.py        # Behavioural: util/agent_suite_doctor.py suite health check (dogfood; consumes every layer)
│   ├── test_agent_suite_summary.py       # Behavioural: util/agent_suite_summary.py suite quick-reference (P3)
│   ├── test_predict_merge.py             # Behavioural: util/fleet_triage/predict_merge.py predicted-merge (4 verdicts, TRUE-delta, cluster/order, no-mutate, exit codes; hermetic)
│   ├── test_fleet_supervisor_contract.py # Lint: fleet-supervisor subagent frontmatter + body wiring (predict_merge.py, 4 verdicts, read-only/never-push, two-key DUP-CLOSE)
│   ├── test_workflow_script_paths.py     # Lint: every .github/workflows/*.yml script path exists
│   ├── test_doc_tools_drift.py           # Lint: consumer-repo juniper-doc-tools pins still admit current version (plan §5.1)
│   ├── test_service_fork_drift.py        # Drift gate: security guards that must not diverge across the data/cascor service-core forks (register §2.3; ENFORCED + self-maintaining KNOWN_GAP ledger)
│   ├── test_publish_env_policy_drift.py  # Drift gate: publish envs stay tag-only ref-gated (publish-path design §6/§12); settings-not-code, so nothing else would notice a deletion
│   ├── test_assert_release_tag.py        # Behavioural + wiring: util/assert_release_tag.bash (P3) — tag-shape + tag<->built-wheel version, and that all 7 publishers invoke it with the right prefix
│   ├── test_pyproject_extras.py          # Lint: pyproject [project.optional-dependencies] surface matches the contract
│   ├── test_template_library_drift.py    # Lint: custom-agent template library (prompts/agent_templates/) manifest <-> templates
│   ├── test_template_selection.py        # Lint: custom-agent template match_signals selection coherence
│   ├── test_template_select_preview.py   # Behavioural: util/template_select_preview.py offline match_signals selector (P2)
│   ├── test_template_data_resolver.py    # Tests + drift gate: data layer (prompts/agent_templates/data/) + resolver
│   ├── test_scaffold_template.py         # Behavioural: util/scaffold_template.py new-template generator (P5; drift-compliant output)
│   ├── test_open_signed_pr.py            # Behavioural: util/open_signed_pr.py signed cross-repo PR opener (hermetic gh stub; dry-run/dup-guard/refs-ref=/deletions)
│   ├── test_experiment_stack_script.py   # Contract + behavioural: util/experiment_stack.bash per-run launcher (§6.1 recipes, §6.4 RUN_DIR, §7.2 target file, §9.3 ranges, F-6 listener pid, dry-run + teardown; hermetic)
│   ├── test_run_suite.py                 # Behavioural: util/experiments/run_suite.py suite driver (expansion + cell_ids, per_cell seeds, driver-validated cells, stubbed up/drive/down loop, registry/index/aggregate, resume, both Q-2 budget flags; hermetic)
│   ├── test_list_runs.py                 # Behavioural: util/experiments/list_runs.py lister/pruner (state classification, --older-than, prune safety gates; hermetic RUN_ROOT fixtures)
│   ├── test_run_experiment.py            # Behavioural: util/experiments/run_experiment.py cascor + recurrence driver (§6.3 drive loops, Q-2 stall/budget, F-1 redirect sampling, G-6 staging, §5.5 blocks + G-18 save_model, §8.1/§8.2 plot sets, §8.3 stats/summary, §13.4 manifest, exit matrix 0-4; hermetic stub HTTP)
│   ├── test_experiment_config_schemas.py # Drift gate (Wave 3.5): sibling conf/experiments/*.yaml ↔ driver load_config + AST-extracted app Settings fields (CI/force-local gated; always-on extractor self-check)
│   ├── test_experiment_suite_yamls.py    # Drift gate (R-6): every util/experiments/suites/**/*.yaml passes run_suite.load_suite + oversize cascor suites (pool >= 16 OR cap >= 64) declare execution.stall_seconds (ml#1069) + wide-cap suites pin a wall budget; anti-resurrection for the ad-hoc stall shim
│   ├── test_prompt_validator_contract.py # Lint: prompt-validator subagent frontmatter + pinned verdict schema/fixtures
│   ├── test_template_agent_skill_lint.py # Lint: template-agent Skill frontmatter + wiring to real artifacts (PR 5)
│   ├── test_service_smoke_skill_lint.py  # Lint: service-smoke Skill frontmatter (declared browser MCP for opt-in --ui, NO Agent) + teardown wiring (E-1 Stage 1/2)
│   ├── test_ui_test_author_skill_lint.py # Lint: ui-test-author Skill frontmatter (Write + declared browser MCP, NO Agent) + models canopy src/tests/ui/ + teardown (E-6)
│   ├── test_agents_frontmatter.py        # Lint: every .claude/agents/*.md honours the suite frontmatter contract (opus+max)
│   ├── test_agents_md_version_drift.py   # Lint: AGENTS.md **Version** header matches pyproject.toml [project].version
│   ├── test_agents_md_header_schema.py   # Lint: AGENTS.md canonical header schema (6 required fields, ISO date format)
│   ├── test_agents_md_tree_drift.py       # Lint: every tracked top-level dir appears in the Repository-Structure tree (G-3)
│   ├── test_coverage_gap_mapper_drift.py  # Dogfood/drift (E-4): juniper-coverage-gap-map console script registered + version/pin coherent (ci-tools)
│   ├── test_env_drift_check_drift.py      # Dogfood/drift (§10.1): juniper-env-drift-check entry point registered + every cli*.py wired (0.5.1 #580-clobber guard)
│   ├── test_release_train_registry.py    # Lint + drift gate: util/release_train/registry.yaml (18 packages/8 repos/enums) <-> pyproject resolution (plan §4.1) + the ml#701 static-package pyproject==dunder lockstep gate
│   ├── test_release_train_detect.py      # Behavioural: util/release_train/detect.py detection engine (classifications, substantive-hunk, SemVer, exit codes; hermetic)
│   ├── test_release_train_propose.py     # Behavioural: util/release_train/{propose,notes_render}.py proposal-PR generator (dry-run bump+CHANGELOG move+notes, dup-guard, conflict refusal; hermetic) (plan §5.4)
│   ├── test_release_train_archive_guard.py # Behavioural: util/release_train/archive_guard.py exempt notes-archive structural guard (add-only/path-confined/name-valid/single-purpose; SKIP for non-archive; hermetic) (plan §7.2 / step 3.1)
│   ├── test_release_train_ceremony.py    # Behavioural: util/release_train/ceremony.py exempt-archive + Release ceremony (§8 HALTs, happy-path, signed-archive HALT/parse edges, dup-guard/idempotent, R7 gh-surface, dry-run; hermetic) (plan §7/§8/§9.3 / step 3.2)
│   └── fixtures/
│       └── prompt_validator/             # PR 3: verdict.schema.json + verdict.sample.{pass,fail}.json (validator contract)
│   # Doc-link validator regression tests moved to juniper-doc-tools/tests/
│   # (Wave 4 of the doc-link migration plan; published under the dedicated
│   #  juniper-doc-tools PyPI package).
│
└── util/                      # Utility scripts and tools
    ├── ad-hoc/                           # Single-use / temporary / unfinished scripts (see ad-hoc/README.md)
    ├── assert_release_tag.bash            # Publish guard (P3): ref must be a TAG, and the tag's version must match the wheel actually built
    ├── open_signed_pr.py                  # Cross-repo: open a PR on any Juniper repo with a GitHub-SIGNED commit (createCommitOnBranch)
    ├── requirements_drift_check.py       # Drift checker for the requirements snapshot (--mode quick)
    ├── editable_install_drift_check.py   # Drift checker for juniper editable installs across conda envs
    ├── env_floor_drift_check.py          # Floor-drift checker: installed juniper-* vs target-repo pyproject floors (I-2)
    ├── release_train/                     # PyPI release-train: registry.yaml (18-package registry) + detect.py (report-only "needs deploy?" engine, Phase 1) + propose.py/notes_render.py (manifest -> proposal-PR content, dry-run, Phase 2.1) + archive_guard.py (exempt notes-archive PR structural guard, Phase 3.1) + ceremony.py (exempt-archive + Release ceremony, dry-run, Phase 3.2)
    ├── prompt_discovery/                  # Custom-agent suite (PR 4): env-discovery probes -> JSON grounding bundle (path-invoked, --repo-root)
    ├── fleet_triage/                      # Flood §4 item 7 (Stage-0 supervisor script layer): predict_merge.py -- detached-clone predicted-merge per PR (4 verdicts, TRUE delta, cluster map + order; delegates the 2 screens to juniper-ci-tools console scripts); --pr N | --batch, exit 0/2
    ├── generated_prompt_index.py         # Custom-agent suite (P4): index + safety-gated prune of prompts/generated/
    ├── template_data_resolver.py         # Custom-agent suite (PR 6b): loads prompts/agent_templates/data/*.yaml (data-layer resolver)
    ├── template_select_preview.py        # Custom-agent suite (P2): offline preview of the Template Agent's match_signals selection
    ├── install_agents.bash               # Custom-agent suite (PR 6a): mirror .claude/{agents,skills} -> ~/.claude (idempotent, reversible)
    ├── scaffold_template.py              # Custom-agent suite (P5): generate a new prompts/agent_templates/ template + manifest stanza
    ├── agent_suite_doctor.py             # Custom-agent suite: read-only health check (dogfood; OK/WARN/FAIL over every layer)
    ├── agent_suite_summary.py            # Custom-agent suite (P3): quick-reference listing of agents + templates
    ├── worktree_cleanup.bash             # V2 cleanup orchestrator (CWD-safe)
    ├── worktree_new.bash                 # Creates new git worktree
    ├── worktree_activate.bash            # Bash helper for worktree activation
    ├── worktree_close.bash               # Removes a worktree, branch, and prunes
    ├── worktree_wipeout.bash             # Bulk removal by pattern
    ├── remove_stale_worktrees.bash       # Removes all stale worktrees
    ├── cleanup_open_worktrees.bash       # Removes all active worktrees
    ├── prune_git_branches_without_working_dirs.bash  # Branch hygiene
    ├── juniper_plant_all.bash            # Starts all Juniper ecosystem services
    ├── juniper_chop_all.bash             # Stops all Juniper ecosystem services
    ├── isolated_stack.bash               # Isolated training-runtime E2E trio (data 8101 / cascor 8202 / canopy 8051): --up/--down/--status/--dry-run
    ├── experiment_stack.bash             # Per-run experiment launcher (data 8110-8139 / cascor 8230-8259 / recurrence 8260-8289): --up/--down/--status/--dry-run
    ├── experiments/                      # Experiment driver layer (Waves 2.2-2.6): run_experiment.py single-run cascor + recurrence driver (§6.3) + plots_cascor.py / plots_recurrence.py (§8.1 + §8.2 plot sets; 2.5 closes G-5) + stats_summary.py (§8.3 stats.json + summary.md) + list_runs.py (Wave 7.2: safety-gated lister/pruner) + run_suite.py + suites/ (Waves 7.1+7.5: suite driver — matrix expansion, per-cell up→drive→down, registry/index/aggregate; parallel + H-11 split, cascor refused per Q-6)
    ├── get_cascor_status.bash            # GET /v1/training/status
    ├── get_cascor_metrics.bash           # GET /v1/metrics
    ├── get_cascor_history.bash           # GET /v1/metrics/history?count=10
    ├── get_cascor_history-plus.bash      # GET /v1/metrics/history?count=100
    ├── get_cascor_network.bash           # GET /v1/network
    ├── get_cascor_topology.bash          # GET /v1/network/topology
    ├── kill_all_pythons.bash             # Emergency Python process terminator
    ├── search_file_in_all_repos_and_worktrees.bash   # Cross-repo file search
    └── global_text_replace.bash          # Batch sed find-and-replace
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

- `util/worktree_cleanup.bash` -- Automated worktree cleanup with CWD-safe session continuity (V2 procedure). `MAIN_REPO` derives from `${BASH_SOURCE[0]}` (one dir up) with a `JUNIPER_ML_MAIN_REPO` override for test fixtures. Flags: `--old-worktree`, `--old-branch`, `--parent-branch`, `--new-worktree`, `--new-branch`, `--skip-pr`, `--skip-remote-delete`, `--dry-run`. Phase 7 always restores the primary checkout to up-to-date `main` (skips on dirty tree or checkout refusal; F-6 stale-checkout class).
  - Phase 1: non-empty `status --porcelain` in the old worktree → `exit 1` (`Commit or stash…`) before any push; `--dry-run` skips the check. Clean tree then pushes when ahead / `-u` when no upstream / skips when synced. Phase 2 refuses an existing `NEW_WORKTREE` path (`exit 1`, never clobbers).
- `util/reap_pytest_orphans.bash` -- Safely reaps orphaned Juniper pytest multiprocessing children (`--dry-run` / `--verbose`).
  - Candidate awk gate: current-user + `/python/` + (`JuniperC[a-z0-9]+` conda path or `Juniper/worktrees/`); empty set exits 0 with "No Juniper python processes found."
  - Orphan when ppid is `1`, user `systemd --user`, or parent gone; live parents KEEP. `SKIPPED` on ps→gone race or missing `PPid:` (never kill).
  - **Live-experiment protection, checked BEFORE the orphan predicate.** `experiment_stack.bash` / `isolated_stack.bash` launch services under `nohup` in a subshell, so they reparent to `systemd --user` — the orphan predicate itself; orchestrators / watchdogs started with `setsid`/`disown` land there too.
  - Two protection keys, either sufficient: **P1** the pid is in a run-dir `*.pid`; **P2** the pid's cmdline references a run root (`JUNIPER_EXP_RUN_ROOT`, default `~/.local/state/juniper-experiments`, or `JUNIPER_E2E_RUN_DIR`). Prints `PROTECT` **always** (not `--verbose`-gated) and counts separately.
  - Observed live 2026-08-16 on campaign `e-j-h2h-wide-cap6`: a dry run called the orchestrator, the experiment cascor service, and the watchdog all `WOULD REAP` while healthy. Over-protection is the deliberate safe direction — a stale pidfile still protects.
  - Test hooks: `JUNIPER_REAP_PROC_ROOT`, `JUNIPER_REAP_KILL_CMD` (plus the two run-root vars, redirected per-test). Operator surface: [docs/REFERENCE.md § Pytest Orphan Reaper](docs/REFERENCE.md#pytest-orphan-reaper).
- Documentation link validator now lives in [`juniper-doc-tools/`](juniper-doc-tools/) and is published to PyPI as `juniper-doc-tools` (Wave 4 of the doc-link migration plan; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`).
- `util/requirements_drift_check.py` -- Drift checker for the requirements snapshot at `notes/requirements/id_assignments.yaml`. Default `--mode quick` validates path resolution + structural line-range integrity for every citation; emits a human report or `--json`. Exit code 1 on any drift. Implements the spec in [the requirements next-steps doc §7](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection); `--mode full` / `--mode rewrite` are reserved for future work.
- `util/template_data_resolver.py` -- Loader + dotted `resolve()` for the custom-agent suite data layer (`prompts/agent_templates/data/*.yaml`: standing rules, anti-hallucination doctrine, conventions, ecosystem facts, known-misses ledger). Path-invoked (`python util/template_data_resolver.py conventions.handoff_threshold`) or imported; the Template Agent maps these into template slots and RUBRIC R2.5 checks injected conventions against them. Tests: `tests/test_template_data_resolver.py`.
- `util/template_select_preview.py` -- Offline preview of the Template Agent's category selection (P2): given a task string, prints which template the Skill's `match_signals` step would pick (matched keywords + ranked runner-ups). A preview heuristic (keyword-substring scoring; `generic` fallback), not the Skill's exact judgement. `python util/template_select_preview.py "TASK" [--repo-root P] [--json] [--top N]`; exit 0 always. Tests: `tests/test_template_select_preview.py`.
- `util/editable_install_drift_check.py` -- Drift checker for juniper editable installs in the conda environments. Reads each env's `*.dist-info/direct_url.json` directly (robust to broken envs); classifies every `juniper-*` editable as `FRESH` / `WORKTREE_PINNED` (under a `worktrees` path) / `ORPHANED` (missing). `*-DEPRECATED` skipped by default; exit 1 on ORPHANED; `--json`; `--fix` re-points orphans to their canonical repo (`--dry-run` previews).
  - **Version axis** (`MATCH` / `STALE` / `UNKNOWN`), orthogonal to the path axis: compares the version the install RECORDED at pip time against the version its target declares NOW. An editable never re-derives its version — `import` follows the live tree while `*.dist-info/METADATA` stays frozen — so a `FRESH` install can be badly stale.
  - Blind spot it closes: on 2026-08-14 **7 of 8** installs on this host were FRESH *and* stale (juniper-data 5 minors behind, `0.6.0` vs `0.11.0`), invisible to both the path axis and `juniper-env-drift-check`'s floor check — a stale editable sits above every floor and is still wrong. It breaks whatever reads the *installed* version: a repo's `version == pyproject` self-check (cascor's `test_version_matches_pyproject`) and a host-launched service's build-info metric.
  - STALE is **soft** (exit 0 — `import` still resolves); `--strict-version` makes it exit 1, while `--strict` stays about the path axis. `--fix-stale` refreshes stale installs against the path they ALREADY point at (`drift: "stale-metadata"`) rather than a canonical-discovery result, which would risk re-pointing a deliberate checkout; ORPHANED repair is unchanged (`drift: "path"`).
  - Dynamic versions are read only from an explicit `[tool.setuptools.dynamic] version.attr` (flat or `src/`) / `[tool.hatch.version] path` declaration — an unrecognized backend reports UNKNOWN instead of guessing at a `_version.py`. Operator surface: [`docs/REFERENCE.md` § Editable Install Drift Check](docs/REFERENCE.md#editable-install-drift-check).
  - Ambiguous canonical (juniper-ml#795 coverage): `discover_canonical` returns `(None, [.., ..])` when two+ non-worktree checkouts share a `[project].name`; `--fix` then `action=SKIP` with `reason` containing `ambiguous` (never picks `candidates[0]`). Operator surface: `docs/REFERENCE.md` Editable Install Drift Check + cheatsheet tip.
  - Live `--fix` actions (juniper-ml#802 coverage): `run_fix` marks `FIXED` on successful `pip install -e <canonical> --no-deps --force-reinstall`; `OSError` / `CalledProcessError` become `action=ERROR` (stderr truncated to 500 chars) without aborting later plan items; after a non-dry run, `main` re-scans so exit `1` still reflects remaining orphans. Operator surface: `docs/REFERENCE.md` Editable Install Drift Check + cheatsheet tip.
- `util/env_floor_drift_check.py` -- Floor-drift checker (gap I-2): reads each installed `juniper-*` version from its `*.dist-info/METADATA` and compares to the target repo's `pyproject.toml` floors -> `OK` / `BELOW_FLOOR` / `MISSING` -- the below-floor plain-wheel case the pins/editable checkers miss. Env selection is data-driven (`--site-packages`/`--env`/`ecosystem.yaml`); exit 1 on `BELOW_FLOOR` (`--strict` also `MISSING`); `--json`; structural CI gate. Tests: `tests/test_env_floor_drift_check.py`.
  - `resolve_site_dirs` precedence: `--site-packages` → `--env` → `ecosystem.yaml` `used_by` for `[project].name`; unresolved paths exit 2 with the reason string (never invent an env name). Operator surface: `docs/REFERENCE.md` Environment Floor Drift Check.
  - Multi-site / multi-interpreter: `installed_juniper_versions` keeps the **highest** version across site-packages dirs; malformed / unreadable `METADATA` and non-`juniper-*` are skipped. Coverage: open #796 / #802.
- `util/release_train/` -- PyPI release-train tooling (release-train plan §12). `registry.yaml`: the data-driven 18-package / 8-repo registry (§4.1). `detect.py`: the per-package "needs a PyPI deploy?" engine (§4.2/4.3, Phase 1, report-only) -- PyPI truth vs declared version, tag-matched diff base, `gh compare` (`--local-git` fallback past the 300-file cap), and a substantive-hunk SHIP filter discounting the notes-rename comment/docstring/link class; report-only, exit 0/1/2.
  - SHIP / SemVer edges: whitespace + pure comment deletion discounted; pure code deletion ships; `local_git_compare` A/D/R/**C** of a `.py` module is inherently substantive (no blob compare); Keep-a-Changelog `Security` → patch, `Changed`/`feat!`/`BREAKING CHANGE` → minor pre-1.0. Operator tables: release-train operator runbook §3.1.
  - Soft-fail `SHIP_UNCERTAIN` (unreadable declared version / missing tag / `comp.ok=False` / truncated empty window / patch-uncertain) is an action class — never silent `UP_TO_DATE`.
  - Hygiene `list_releases` `SourceError` sets `tag_only=None` + an unavailable note (does not exit 2 or invent TAG_ONLY). Offline `--local-git` must raise (open #773), not return `set()`. Operator tables: release-train runbook §3.1.
  - On the live daily path a Releases-API 404 / `None` from `_gh_lines` must **raise** rather than coerce via `or []` into an empty set — an empty set makes `diff_base_tag not in releases` always true and yields a false TAG_ONLY for every package. An *authenticated* empty Releases list remains a genuine TAG_ONLY.
  - Detect step summary / Slack footers: report and propose count the full action set `UNRELEASED_CHANGES` + `BUMPED_NOT_RELEASED` + `SHIP_UNCERTAIN`, while the ceremony footer counts **only** `BUMPED_NOT_RELEASED` (the ceremonial class). A missing or empty `release-manifest.json` surfaces the hard-fail banner / `FAILED HARD` Slack line, never a quiet clear.
    Pins: `DetectSummaryRehearsalTest` / `DetectSlackPayloadRehearsalTest`. Operator surface: [`docs/REFERENCE.md` § Release-Train Detect Summary and Slack](docs/REFERENCE.md#release-train-detect-summary-and-slack).
- `util/release_train/propose.py` -- Proposal-PR generator (Phase 2.1, plan §5.4): from `detect.py`'s manifest, for each `UNRELEASED_CHANGES` package builds the standard-gated proposal -- static/dynamic version bump, the CHANGELOG `[Unreleased]`->`[<version>]` move, a `notes_render` notes draft (not archived), the meta AGENTS.md co-change, and `propagation_edges`; dup-guard + `changelog_conflict` refusal via a seam. **`--dry-run` default writes nothing.** Tests: `tests/test_release_train_propose.py`.
  - ml#701 dunder lockstep: a static-version package that also ships a `_version.py` gets BOTH files bumped in one proposal (auto-detected by file presence; no registry field), with the co-change named in the PR body + the S5.4 checklist. Gate: `VersionDunderLockstepTest` in `tests/test_release_train_registry.py`.
  - Sibling/meta AGENTS.md **Version** (worker#140 / ml#706): step 5 (meta) / 5a (sibling primary, `pypi_name == repo`) rewrites a from-version header; sub-packages never touch the host header.
  - Already-at-target / re-entry + absent edges (juniper-ml#720): header already at `to_version` is silent success (no false `REQUIRED`); absent file or missing `**Version**` line surfaces checklist `REQUIRED` (never invents a header).
  - AGENTS.md per-package version TABLE row (juniper-ml#851; the worker#140 class, table variant): step 5a's `set_agents_table_version` bumps the version cell of any `|`-row naming the released `pypi_name` in backticks with exactly one standalone version cell -- recurrence's `AGENTS.md:22-24` table is pinned to `_version.py` by its `version-drift` hook, so header-only proposals shipped red (recurrence#92/#93). Per-PACKAGE, not per-repo: a sub-package bumps its own row, never the host header.
  - Table honesty rules + single-edit composition (juniper-ml#851): already-at-target is silent success, no such table = no phantom edit and no checklist noise, an unexpected/ambiguous cell is byte-untouched + checklist `REQUIRED`, prose version mentions are left alone (the target hook does not gate prose); the header, table-row, and extras-pin true-ups compose into ONE `AGENTS.md` `FileEdit`. Operator triage: release-train runbook §3.2.
  - CHANGELOG refuse clear-on-refuse (juniper-ml#751): empty/missing Unreleased or missing CHANGELOG after the version/dunder bump is staged → `prop.edits.clear()` so the skipped stub is `edits=[]` + `skipped_reason` (matches dup-guard / `bump=none`). Operator guidance: release-train runbook §3.2.
- `util/release_train/notes_render.py` -- Template-driven release-notes generator (plan §10.1), imported by `propose.py` and independently invokable: renders a DRAFT from `TEMPLATE_RELEASE_NOTES.md` (or the security template when a `Security` category is present), grouping CHANGELOG `[Unreleased]` bullets by Keep-a-Changelog category, and surfaces the `notes/releases/RELEASE_NOTES_<pkg>_v<version>.md` archive convention (`--print-archive-name`). Tests: `tests/test_release_train_propose.py`.
  - `link_base` rewrite (`--link-base`; ceremony = owning repo's tag-pinned blob URL, propose = `blob/main`): repo-relative CHANGELOG links render absolute so centrally archived notes don't 404 (the canopy v0.6.0 class).
  - Gate 1 draft signals: meta `display_name` → `Juniper ML`; `release_type("major")` → MAJOR (`none`/unknown → PATCH); Breaking YES iff a `Removed` category is present; `_split_bullets` accepts `*` as well as `-` and folds continuations. Operator table: release-train runbook §3.2 (coverage juniper-ml#756).
- `util/release_train/archive_guard.py` -- Structural guard (Phase 3.1, plan §7.2) for the release-train's gate-exempt notes-archive PR. Passes a PR diff (`git diff --name-status`; injected) ONLY if it is **add-only**, **path-confined** to `notes/releases/RELEASE_NOTES_*.md`, **name-valid** (`_v<semver>`, registry `pypi_name`), and **single-purpose**; non-archive PRs `SKIP`, a violation only `FAIL`s the check (R7). Run by `ci.yml`'s PR-only lane. Tests: `tests/test_release_train_archive_guard.py`.
  - `touches_releases` inspects **both** sides of a rename/copy so a rename-OUT of `notes/releases/` is still an archive PR and FAILs (never SKIP). Copy (`C`) and Typechange (`T`) are non-`A` and FAIL rule1. Operator triage: release-train runbook §3.3.
  - `Allow-Archive-Edit: <path>|<basename>|*` commit trailer (house `Allow-*` idiom; injected via `--trailers-file`, produced by `ci.yml` from `git log --format=%B FETCH_HEAD..HEAD`) waives rules 1/4 for in-place edits of FLAT `notes/releases/RELEASE_NOTES_*.md` files -> distinct `WAIVED` verdict (exit 0, waived paths named); anything dragging an out-of-archive or nested path still FAILs. The #1003 link-repair class / issue #1013. **Carry the trailer into the squash commit message.**
- `util/release_train/ceremony.py` -- Exempt-archive + Release ceremony (Phase 3.2, plan §7/§8/§10) for `BUMPED_NOT_RELEASED` packages: §8 preconditions (each HALTs + dedup issue), notes from the CHANGELOG `[<version>]` section, open the exempt archive PR (signed API commit), enable auto-merge, cut the Release (`--latest=false`; no `--verify-tag`), monitor -> `PENDING_PYPI_APPROVAL`. R7 gh-surface allowlist; idempotent re-entry. **`--dry-run` writes nothing.** Tests: `tests/test_release_train_ceremony.py`.
  - Signed-archive re-entry: reuse tip-at-base / single-commit-atop-base; HALT on unresolvable base/tip, non-422 refs errors, or diverged branch (never invent a sha). Operator table: release-train operator runbook §3.3.
  - Open archive-PR reuse (juniper-ml#730): `enable_automerge(…, pr_ref or plan.archive_branch)`; archive-already-on-main → release only; Release-exists → `RESUME_MONITOR`.
  - Precondition: `notes-render-failed` HALTs when `notes_render.render_notes` raises `OSError` (missing/unreadable `TEMPLATE_RELEASE_NOTES.md` / security template) — restore the template, re-run; never invent archive body. Operator catalog: release-train operator runbook §4.
  - Monitor: `NOT_FOUND` (run invisible right after `cut_release`) is **not** terminal — keep polling; timeout while still building or permanently missing → honest `IN_PROGRESS` (never invent PENDING/RELEASED/HALT). Operator guidance: release-train operator runbook §3.3.
  - Monitor run **selection** (`select_publish_run`): a Release fires EVERY `release: published` publisher in the owning repo, and the tag-guarded ones finish `completed/skipped`
    sharing the real run's `displayTitle` **and** `headBranch`. Feeding a skipped run to `classify_publish_run` yields `IN_PROGRESS` forever, so the monitor burns its whole
    `--monitor-timeout` per package and the ceremony job's `timeout-minutes: 30` kills the run — surfacing as a bogus `cancelled` (the 2026-08-09/10 class; both legs of the
    cascor 0.8.0 + protocol 0.2.0 ceremony hit it). Selection drops `skipped` runs, prefers an exact `headBranch` match over a substring `displayTitle` match (bare `v0.2.0` is a
    substring of `juniper-cascor-protocol v0.2.0`), and prefers an unfinished run over a finished one. All-skipped → `None` → non-terminal `NOT_FOUND`. Pin: `SelectPublishRunTest`.
  - R7 archive-lane (`_assert_api_allowed`): a `git/refs` POST must carry explicit `ref=refs/heads/*` — missing/empty `ref=` is `SeamViolation` (juniper-ml#770; pre-#770 deferred omit to the live API).
  - Execute terminal `RELEASED`: publish run `completed`+`success` (both gates done) surfaces as final state with **no** halt issue — distinct from plan-time `ALREADY_RELEASED` (PyPI already serves target). Operator guidance: runbook §3.3.
- `util/prompt_discovery/` -- Discovery helpers for the custom-agent suite (PR 4); path-invoked (`python util/prompt_discovery/cli.py --repo-root <path>`), emits a JSON grounding bundle (closed-world facts + provenance: `head_sha`/`dirty`/`ttl_seconds`/`per_probe_status`) from seven probes (`repo_context`, `test_status`, `file_probe`, `symbol_probe`, `dependency_facts`, `conventions`, `concurrency`). Accepts `--target-repo` (cross-repo alias of `--repo-root`). A discovery failure is a hard stop (exit 2).
- The **sequence-safety screens** now ship in `juniper-ci-tools` (>=0.8.0) as two console scripts; rollout W3 deleted the inline `util/sequence_safety/` copy (unit tests → `juniper-ci-tools/tests/`; resurrection-guarded by `tests/test_ci_tools_drift.py`). `juniper-symbol-loss-check` -- symbol-loss screen (P2 gate G1/G3): AST inventory of BASE vs HEAD; FAIL on a deleted (`LOST`) / gutted (`WEAKENED`) / duplicated def, with an SF3 qualified-name relocation downgrade and a `Allow-Symbol-Loss:` trailer escape.
- `juniper-docs-additions-check` -- docs deletion-magnitude screen (P2 gate G2 / G3 step 4): for `AGENTS.md` + `docs/**` + `notes/**`, FAIL on a deleted heading or a `>=N`-line deletion run (default 5, `--min-run`); WARN on small deletions / swaps / retitles; `Allow-Docs-Rewrite:` trailer escape.
- Both screens keep `--base/--head [--files] [--advisory] [--json]`, exit 0/1/2, the WARN-only `--advisory` label hatch (SF5), and add a repeatable `--scope GLOB`. juniper-ml's `ci.yml` (per-PR) + `main-verify.yml` (post-merge G3) install the package; the symbol screen passes the explicit ml scope `--scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash'` (docs = universal default), reproducing the in-repo predicate byte-for-byte.
- `util/fleet_triage/predict_merge.py` -- Deterministic predicted-merge triage for third-party fleet PRs (Stage-0 supervisor script layer; flood §4 item 7). Per PR, in a throwaway detached `git clone` under the system tempdir (never a `git worktree`, never a push), merges `origin/main` into the branch tip and on the result runs the repo-pinned fast gates + an AST symbol-loss screen + a docs additions-only screen. `--pr N | --batch [--json] [--repo-root P]`; exit 0/2. Tests: `tests/test_predict_merge.py`.
  - Emits per-PR JSON (`verdict` MERGE-CLEAN / NEEDS-UPDATE-BRANCH / DAMAGED-FIX-FIRST / CONFLICT + the TRUE changed-file delta from the merge result, NOT `gh --json files`); `--batch` builds the same-file cluster map + a heal-first (`restore`/`heal`/`repair`/`fix-first`), least-colliding merge order.
    - The read-only `fleet-supervisor` agent invokes it once per batch.
    - The AST symbol + docs screens shell out to the `juniper-ci-tools` console scripts (`juniper-symbol-loss-check` / `juniper-docs-additions-check`, >=0.8.0) on the merged RESULT (same CLIs as post-merge `main-verify`; rollout W3 replaced the in-repo `util/sequence_safety/` paths). predict_merge therefore now **requires juniper-ci-tools installed** alongside `gh`; an absent console script degrades that screen to `skip` (never crashes the report).
    - The docs screen counts removed content `-` lines on changed `.md` only (ignores unified-diff `---` headers); no-`.py` TRUE deltas skip the pre-commit battery.
    - `--pr` / `triage_pr`: a `gh` nonzero exit or non-JSON response raises `PredictMergeError` -> CLI exit `2` (hard-fail; there is no partial report worth printing). `--batch` / `triage_batch`: the same condition becomes a soft `ERROR` row and the rest of the open-PR set still runs.
    - The gate battery runs over `changed_existing` (TRUE delta filtered to paths that still resolve as a blob at `HEAD`), so a **deleted** `.py` stays in `true_delta` for the symbol screen but is never passed to `pre-commit --files` — a pure-deletion PR can be gate-clean and still `DAMAGED-FIX-FIRST`. `JUNIPER_FLEET_SKIP_PRECOMMIT=1` forces hook `skip_all`.
    - Operator surface: [`docs/REFERENCE.md` § Fleet Triage and Sequence Safety](docs/REFERENCE.md#fleet-triage-and-sequence-safety).
- `util/generated_prompt_index.py` -- Indexes the Template Agent's `prompts/generated/` output (P4): lists each prompt parsed by the `PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md` convention, with `--older-than DAYS` + a safety-gated `--prune`/`--archive` (acts only with explicit `--yes`, never under `--dry-run`; `.gitkeep` / non-convention files never touched). The dir is read from `conventions.yaml`. Tests: `tests/test_generated_prompt_index.py`.
- `util/install_agents.bash` -- Mirrors this repo's `.claude/{agents,skills}/*` into `~/.claude` by symlink (design D-6) so the suite is available cross-repo; the project stays source of truth (OQ-6). Idempotent, reversible (`--reverse`), `--dry-run`; `JUNIPER_ML_REPO_ROOT`/`JUNIPER_CLAUDE_HOME` overrides for tests. Never clobbers a non-symlink; `--reverse` removes only owned links. Tests: `tests/test_install_agents.py`.
- `util/scaffold_template.py` -- Generates a new `prompts/agent_templates/<id>.md` (P5): writes the canonical skeleton with well-formed placeholders (so a new template can't drift from the library contract) and **prints** the `manifest.yaml` stanza to paste -- it deliberately does NOT edit the manifest (the human-curated selection contract). Refuses to overwrite. `python util/scaffold_template.py --id ID --title T --class C --keywords k1,k2 [--dry-run]`. Tests: `tests/test_scaffold_template.py`.
- `util/agent_suite_doctor.py` -- Read-only health check for the custom-agent suite (a `planner`-designed dogfood): reports existence + structural validity of every component (agents incl. `opus`/`max`, the Skill, the template library, `RUBRIC.md`, the data layer, the discovery CLI, the `~/.claude` mirror) as `OK`/`WARN`/`FAIL`.
  - `python util/agent_suite_doctor.py [--repo-root P] [--json] [--strict] [--no-discovery]`; exit 0/1/2.
  - Discovery (`check_discovery`) is fail-closed unless `--no-discovery`: missing `util/prompt_discovery/cli.py`, nonzero CLI exit, non-JSON stdout, or bundle missing `schema_version` / `provenance.head_sha` → `FAIL` (never silent OK). `--no-discovery` omits the check (no `SKIP` row).
  - Operator surface: [docs/REFERENCE.md § Agent Suite Doctor](docs/REFERENCE.md#agent-suite-doctor). Tests: `tests/test_agent_suite_doctor.py`.
- `util/agent_suite_summary.py` -- Quick-reference for the custom-agent suite (P3; the human counterpart to the doctor): lists the agents (name, model/effort, one-line description) and the templates (id, class, when-to-use). `python util/agent_suite_summary.py [--repo-root P] [--agents|--templates] [--json|--markdown]`; read-only, exit 0. Tests: `tests/test_agent_suite_summary.py`.
- `util/assert_release_tag.bash` -- Publish-path guard invoked by all 7 publishers' build jobs (P3; [design](notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md) §6 Option B, closing the surviving asks of juniper-ml#357 / #358).
  - Asserts (1) the run is on a **tag**, not a branch, and the tag carries this package's prefix; (2) the tag's version equals the version actually built.
  - The built version is read from the **wheel filename**, not `pyproject.toml` -- it is the version that will really be uploaded, and it works identically for static and dynamic (setuptools-scm / hatch) version backends where parsing pyproject reports nothing useful.
  - Versions compare PEP 440-normalized, so a `v1.0.0-rc1` tag agrees with a `1.0.0rc1` wheel. `tr -d -- '-_'` needs the `--`: some `tr` builds (the Rust coreutils rewrite) parse a leading-dash SET as an option, and without it BOTH sides normalize to empty, making the mismatch check pass **vacuously**. An explicit empty-result guard backs that up.
  - **Defense in depth, not the control.** Anyone who can edit a workflow can delete this step; the environment tag policy is what survives that. Value here is failing earlier, naming the reason, and keeping the invariant visible in the repo.
  - `--ref-type` / `--ref-name` / `--dist-dir` / `--expect-prefix`; exit 0 pass / 1 assertion failed / 2 misuse. Tests: `tests/test_assert_release_tag.py`.
- `util/open_signed_pr.py` -- Opens a PR on any Juniper repo whose commit is **GitHub-signed**, by creating branch + commit + PR through the API (`createCommitOnBranch`) instead of a local checkout. Promoted from `util/ad-hoc/` after it landed the ml#1099 signing fan-out across 8 repos.
  - Why it exists: `required_signatures` (2026-08-12) rejects unsigned commits fleet-wide, GPG/YubiKey signing is unavailable to a runner, and an unsigned commit **anywhere** in a branch's history blocks the merge (squash does not rescue it). GitHub signs API-authored commits, so this is the portable way to land a signed change. It needs no working tree, which also makes it the path of choice when a session is confined to one worktree and cannot commit in sibling checkouts.
  - `python util/open_signed_pr.py --repo R --branch B --add LOCAL:REPOPATH [--delete REPOPATH] --message M --title T --body-file F [--base main] [--owner pcalnon] [--dry-run]`. `--add` / `--delete` are repeatable and together express a file move; at least one is required. Exit 0 opened / 1 refused / 2 hard error.
  - Safety: refuses on an existing open PR for the branch (dup-guard -- concurrent sessions are a real hazard here) and on an existing branch (never force-updates another ref); `expectedHeadOid` is pinned to the resolved base sha so a concurrent push fails loudly rather than clobbering; `--dry-run` resolves read-only and writes nothing. Mirrors `util/release_train/propose.py`'s `create_signed_commit`. Tests: `tests/test_open_signed_pr.py`.
- `util/ad-hoc/` -- Home for single-use / temporary / unfinished scripts. See `util/ad-hoc/README.md` for file-header conventions and graduation lifecycle. `/tmp/` is prohibited for script source files per the [Script placement](#script-placement-mandatory) rule.
- Dependency-documentation generator now lives in [`juniper-ci-tools/`](juniper-ci-tools/) and is published to PyPI as `juniper-ci-tools` (Wave 4 of the dep-docs migration plan; install with `pip install juniper-ci-tools` and invoke via `juniper-generate-dep-docs`). The legacy `util/generate_dep_docs.sh` was deleted in juniper-ml#298.
- `util/juniper_plant_all.bash` -- Starts all Juniper ecosystem services. `JUNIPER_CASCOR_HOST` defaults to `localhost` and `JUNIPER_CASCOR_PORT` defaults to `8201`; both can be overridden via the environment (e.g. `JUNIPER_CASCOR_HOST=remote.example.com JUNIPER_CASCOR_PORT=8201 util/juniper_plant_all.bash`).
  - `safe_conda_activate` nounset (juniper-ml#795 coverage): `set +u` → `conda activate` → `set -u` (ADDR2LINE class). A `+u`/`+u` restore silently disables nounset for the rest of host bring-up — isolated-stack `activate_conda` must match. Operator surface: `docs/REFERENCE.md` Host Orchestration + cheatsheet tip. Tests: `tests/test_juniper_plant_all.py` (`TestSafeCondaActivate`).
  - The helper is also fail-closed for OR-list callers (`if ! conda activate …; then set -u; return 1; fi`), so a masked activate failure cannot launch the next service on the ambient PATH even though today's plant call sites are bare under `set -e`.
  - `--systemd` / `USE_SYSTEMD=1` enters the user-unit arm before nohup preflight: dependency-ordered `systemctl --user start` (data→cascor→canopy→worker), `curl`-only gate (no `ss`), no `JuniperProject.pid`.
  - Missing `curl` aborts before any start. Worker HTTP-ready + inactive unit → WARNING + `status --no-pager`, still exit 0.
  - Mid-plant health timeout runs `cleanup_on_failure` but does **not** `systemctl stop` (systemd starts are never in `STARTED_PIDS`) — operators must chop with `--systemd`.
  - Hermetic pins: `tests/test_juniper_plant_all.py` `TestSystemdModeBehavioral` (open juniper-ml#804). Operator detail: [`docs/REFERENCE.md`](docs/REFERENCE.md) § systemd mode.
- `util/juniper_chop_all.bash` -- Stops all Juniper ecosystem services from `JuniperProject.pid` (`SIGTERM_TIMEOUT` default 15; `KILL_WORKERS`; `--systemd` / `USE_SYSTEMD`).
  - `orphaned_worker_cleanup` (juniper-ml#791 coverage): opt-in `KILL_WORKERS=1` (default `0`, nohup-only — ignored under systemd). `pgrep -af juniper-cascor-worker` then strict cmdline filter (`juniper-cascor-worker` / `juniper_cascor_worker` / search term; rejects over-greedy `cascor.*worker`).
  - Each match: `graceful_stop <pid> cascor-worker 5` (hard-coded 5s, not `SIGTERM_TIMEOUT`). Post-pidfile call uses `|| true` so a benign return 1 cannot abort chop under `set -e`. Operator surface: `docs/REFERENCE.md` Host Orchestration + cheatsheet. Tests: `tests/test_juniper_chop_all.py` (`TestOrphanedWorkerCleanup`).
  - Missing or empty (zero-byte) `JuniperProject.pid`: logs the matching ERROR, calls `orphaned_worker_cleanup` (honors `KILL_WORKERS`), then `exit 1` — never enters the service-stop loop (open #798).
  - Early cleanup call sites are hard (no `|| true`); the post-pidfile site is soft so a benign "nothing to clean" return cannot abort a successful chop under `set -e`.
  - `--systemd` / `USE_SYSTEMD=1` stops units in reverse dependency order (worker→canopy→cascor→data), soft-fails per unit, and always `exit 0`.
  - Never falls through to the pidfile parser or `orphaned_worker_cleanup` / `KILL_WORKERS`.
  - Hermetic pins: `tests/test_juniper_chop_all.py` `TestSystemdModeBehavioral` (open juniper-ml#804). Operator detail: [`docs/REFERENCE.md`](docs/REFERENCE.md) § systemd mode.
- `util/isolated_stack.bash` -- Brings up / tears down the isolated training-runtime E2E trio (data 8101 dedicated `python3.14` venv, cascor 8202 `JuniperCascor1`, canopy 8051 `JuniperCanopy1` service mode) with the documented env (control-WS origin pair, `JUNIPER_DATA_URL`, `LD_LIBRARY_PATH=`); `--up`/`--down`/`--status`/`--dry-run`, ports 8101/8202/8051 (`JUNIPER_E2E_*` overrides), `--dry-run` starts nothing. See [E2E checklist](notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md).
  - Live compose (juniper-ml#813): `cascor_up` empties `LD_LIBRARY_PATH`, points `JUNIPER_DATA_URL` at isolated data, sets control-WS allowlist to `CANOPY_ORIGIN`, writes `juniper-cascor.pid`, then health-gates; `canopy_up` forces `DEMO_MODE=0`, wires isolated cascor/data URLs + matching `CASCOR_WS_ORIGIN`, writes `juniper-canopy.pid`, then health-gates. Missing `conda.sh` aborts before launch/pid. Operator details: [`docs/REFERENCE.md` Isolated Stack E2E](docs/REFERENCE.md#isolated-stack-e2e-utilities).
  - `data_up` (juniper-ml#807): dedicated `${RUN_DIR}/.venv-data` via `python3.14 -m venv` (skip create if present), `pip install -e juniper-data[${JUNIPER_E2E_DATA_EXTRAS:-api}] prometheus_client juniper-observability`, launch with `PYTHON_GIL=0`, write `juniper-data.pid`, health-gate; missing `python3.14` aborts via `require_cmd` before side effects. `do_up` order is data → cascor → canopy.
  - Nounset (juniper-ml#785): `activate_conda` must `set -u` after `conda activate` (matching plant `safe_conda_activate`); pre-#785 left `set +u` so live `--up` ran without nounset after cascor/canopy activate.
  - Partial-failure teardown: `do_up` absorbs each leg as `*_up || failed=1` and on failure logs `bring-up failed — tearing the partial trio back down`, then calls `do_down` (experiment_stack parity) so a mid-bring-up failure cannot orphan listeners on 8101/8202/8051. Because the OR-list disables `set -e` inside each `*_up`, critical steps must end with `|| return 1` or a mid-function failure false-greens.
  - Fail-closed `activate_conda` under those OR-list callers: `source … || return 1` and `if ! conda activate …; then set -u; return 1; fi` (both arms restore nounset). A bare activate followed by a successful trailing `set -u` would return 0 and launch cascor/canopy on the ambient PATH.
  - Teardown: `--down` is kill-by-port via `port_pid`/`stop_port` (`ss` first `pid=`), canopy→cascor→data, then RUN_DIR + `snapshot_*` cleanup — not `JuniperProject.pid`. Empty/`ss` soft-fail is a noop; `--dry-run` never kills.
  - Health: `wait_for_health` polls `/v1/health` every 2s until `JUNIPER_E2E_HEALTH_TIMEOUT` (default 60); `--status` `probe_health` reports code + pid and does not fail the script. Operator details: [`docs/REFERENCE.md` Isolated Stack E2E](docs/REFERENCE.md#isolated-stack-e2e-utilities).
- `util/experiment_stack.bash` -- Brings up / tears down a **per-run** experiment stack (dedicated juniper-data + `--cascor` and/or `--recurrence`; never canopy) for the
  [CLI experimentation plan](notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §6.2 (Wave 2.1).
  `--up` (with `--shared-data URL` / `--config PATH` / `--experiment NAME` / `--grafana-bridge`), `--down <RUN_ID>|--all-mine`, `--status [RUN_ID]`, `--dry-run`; misuse exits 2.
  Services launch from direct env-bin paths (`JUNIPER_EXP_CONDA_DIR`, default `/opt/miniforge3`) with the §6.1 env sets verbatim: `PYTHON_GIL=0` + per-run
  `JUNIPER_DATA_STORAGE_PATH`/`_EQUITIES_CACHE_DIR`; cascor `LD_LIBRARY_PATH=''` + `uvicorn api.app:create_app --factory` from `juniper-cascor/src` with AUTO_START off;
  recurrence `serve` with metrics on / rate-limit off — all three metrics toggles on and `JUNIPER_DATA_URL` at the run's data port.
  - RUN_DIR contract (§6.4): `RUN_ID=<UTC yyyymmddThhmmssZ>-<4 hex>` under `JUNIPER_EXP_RUN_ROOT` (default `~/.local/state/juniper-experiments` — under `$HOME`, **not** `/tmp`,
    so a reaped sandbox cannot destroy results, H-15); everything (pidfiles, `logs/`, `relays/`, `config/`, `env/launch.env`, `data/`, `equities-cache/`,
    `artifacts/{plots,results}/`, `ports.json`, `teardown.json`) lives inside it. `JuniperProject.pid` is never read or written, no repo `.env` is ever written (all per-run
    config is process env, H-3), and operator ports 8100/8200/8201/8210/8050 are never touched.
  - Ports (§9.3): first free port in data `8110-8139` / cascor `8230-8259` / recurrence `8260-8289`, claimed by an atomic `mkdir "$LOCK_ROOT/<port>.lock"`
    (`JUNIPER_EXP_LOCK_ROOT`, default `${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments`) plus an `ss` probe, released at teardown. The lockdir serialises experiment launchers
    against each other; the residual race vs a non-participating binder is deliberately left to surface as the service's own bind failure through the health gate (H-1).
  - **F-6 pid rule (binding)**: `$!` after `( cd … && nohup <server> … & )` is the backgrounded **subshell**, not the server, so no `*_up` records it. Each service's pidfile
    is written by `record_listener_pid` from `ss -tlnpH "sport = :<port>"` **after** the health gate, with the process cmdline stored alongside; teardown kills pidfile-first
    and only after proving the pid is alive, owned by the current uid, and still running the recorded cmdline (SIGTERM then bounded SIGKILL). If the pidfile path refuses
    (pid gone / wrong uid / cmdline mismatch), `stop_service` logs `pidfile path refused — falling back to the recorded port <N>` and kills via `ss` only on that run's
    recorded port. `artifacts/` is never deleted.
  - Partial-failure teardown: `do_up` writes `ports.json` before any `*_up`; on `failed=1` it logs
    `bring-up failed — tearing the partial run back down` and calls `teardown_run` (live only; not `--dry-run`), keeping `logs/` + `artifacts/` and releasing lockdirs.
  - Health: `wait_for_health` polls `/v1/health` (data, cascor) and `/v1/health/ready` (recurrence) every 2s until `JUNIPER_EXP_HEALTH_TIMEOUT` (default **90** — F-8 sizes it
    for a cold start; the 1.1 s warm number is not the design point).
  - **Dead-process fast-fail**: `wait_for_health` takes an optional 4th arg, a `pgrep -f` liveness pattern, and each leg passes a **port-scoped** one (`-m juniper_data .*--port
    ${DATA_PORT}` / `api.app:create_app .*--port ${CASCOR_PORT}` / `juniper-recurrence serve .*--port ${RECURRENCE_PORT}`) so a sibling run can never satisfy this run's gate.
    Two **consecutive** misses end the wait with `process is gone … died during startup` naming the leg's log, instead of burning the full 90 s per leg on a process that already
    exited (the P4-campaign class). Two misses, not one, and the first probe runs after the first sleep — the launch subshell returns before its child execs, so fork+exec keeps a
    >=4 s grace. **F-6 intact**: the pattern is only ever read; it never resolves a pid and never kills. No `pgrep` on PATH degrades to the prior timeout-only behaviour (an
    unavailable probe must never manufacture a failure), and passing no pattern is unchanged back-compat. Pins: `TestHealthGateLiveness` in `tests/test_experiment_stack_script.py`.
  - **OR-list fail-closed**: `do_up` invokes `*_up || failed=1`, which disables `set -e` inside each body. `require_env_bin` / `activate_conda` / `wait_for_health` / `record_listener_pid` therefore each end with `|| return 1`, or a health
    timeout with a live listener false-greens `--up` and skips `teardown_run`. A mid-`allocate_port` failure calls `release_held_locks` (else prior `*.lock` dirs starve later `--up`), and an opt-in `bridge_up` failure after healthy
    services logs `grafana bridge failed — tearing the run back down` and runs `teardown_run` instead of a bare `set -e` abort.
  - **Staging lock release (fixed by #979)**: `create_run_dir` / `stage_config` / `write_ports_json` each `|| { release_held_locks; …; }`, so a missing `--config` no longer exits
    with the lockdirs held and `ports.json` unwritten — the state `--down` could not recover, which starved the 30-port ranges. Should leftovers ever appear (an operator `kill -9`
    mid-staging), clear them under `JUNIPER_EXP_LOCK_ROOT` only after confirming no live listener holds the port.
  - Grafana bridge is **opt-in** (`--grafana-bridge`): only then does it preflight `socat`, discover the monitoring gateway by network-name **suffix**
    (`docker network ls | grep -E '_monitoring$'` — a worktree-launched compose project renames the network; loud default-bridge fallback), start one
    `socat "TCP-LISTEN:<port>,bind=<gateway>,fork,reuseaddr" "TCP:127.0.0.1:<port>"` relay per scraped service (pids under `RUN_DIR/relays/`), and write the §7.2 target file
    to `<JUNIPER_EXP_DEPLOY_DIR>/prometheus/targets/<RUN_ID>.json` (labels `service` / `environment=host-experiment` / `run_id` / `experiment`; removed at teardown).
    Without it `--status` reports the run as UNSCRAPED.
- `util/experiments/run_experiment.py` -- Single-run experiment driver (plan §6.3; Wave 2.2 = the cascor **service** path, Wave 2.3 = the recurrence **service** path, Waves 2.4/2.5 = the §8.1/§8.2 plot sets via `plots_cascor.py` / `plots_recurrence.py` (2.5 closes G-5), Wave 2.6 = the §8.3 stats/summary via `stats_summary.py`).
  - Stats (§8.3): every run also writes `artifacts/results/stats.json` + human-readable `summary.md` (stdlib-only renderer, every outcome incl. stalled/failed): identity / dataset-shape (tabular vs sequence from meta) / outcome-timing blocks from the manifest, cascor candidate-correlation-per-round + step-duration p50/p95 from the driver's own `metrics_series.csv` (honestly labeled per-poll means -- true per-step quantiles are not recoverable from a sum/count exposition), the recurrence train/CV/θ/readout block.
  - Stats degraded-mode notes surface G-3 sampling errors, collect errors, plot skips, eval-disabled, and G-6 failures; a stats failure is recorded on the manifest (`stats_error`), never fatal.
  - Recurrence plots (§8.2): `dataset_overview` (sampled 3-D windows, target starred), `dt_histogram` (per-step Δt + `target_dt` -- the irregularity signature; skips non-Δt artifacts), `forecast_vs_truth` + `residuals` (predict response vs the predict split's target, `y_reg_{split}` preferred over `y_{split}` -- the equities regression target; residual-vs-`target_dt` panel when available), `crossval_folds` (per-fold eval bars + aggregate line), `metrics_table` (train + CV ± std).
  - A disabled/failed predict or crossval phase is a per-plot SKIP. Deliberately NO recurrence training-history plot (TrainResponse carries no per-epoch series -- §8.2 note).
  - Plots (§8.1, `outputs.plots`, validated per kind): `dataset` (fetched NPZ artifact scatter; 2-feature generators only), `decision_boundary` (collected grid + sample overlay), `training_history` (history rows, hidden-unit-insertion markers), `candidate_correlation` (from the driver's own `metrics_series.csv` -- the sole source), `eval_metrics` (scalar bars) -- rendered client-side by `plots_cascor.py` (lazy-loaded, Agg backend; NEVER imports cascor, whose plotter imports torch).
  - Plot semantics: structurally-unavailable data = recorded per-plot SKIP (exit 0); a render error / failed fetch / missing matplotlib on a requested plot = acceptance failure (exit 1); the manifest `driver.plots` block records requested/rendered/skipped.
  - A renderer `ValueError` is the explicit **no-renderable-data contract**: recorded as a per-plot SKIP only, with no PNG and no acceptance error (exit 0) — distinct from a non-`ValueError` render exception, a failed payload fetch, or a
    missing matplotlib on a requested plot, which are SKIP **and** acceptance failure. Soft edges that deliberately do not raise: a misaligned optional `target_dt` just omits the residual-vs-dt panel, and an empty `eval_aggregate` falls
    back to `folds[0].eval_metrics`. Operator table: [`docs/REFERENCE.md` § Plot SKIP vs acceptance](docs/REFERENCE.md#plot-skip-vs-acceptance-valueerror-contract).
  Path-invoked: `python util/experiments/run_experiment.py --config <yaml> --run-dir <RUN_DIR>` against a stack from `experiment_stack.bash` -- service URLs resolve from the run's `ports.json` (`--data-url` / `--cascor-url` override). Stdlib + PyYAML; numpy lazily only for the `.npz` artifact (JSON fallback); HTTP via redirect-following `urllib` GETs (F-1: bare `/metrics` 307s to `/metrics/`).
  - Validates the §5.4/§5.5 YAML (driver-owned §5.6 subset): unknown blocks/keys rejected, `schema_version` gated, `experiment.seed` REQUIRED (with the `dataset.params.seed` derivation rule + run-scoped default tags), rule-6 infra keys (`service.host/port/juniper_data_url/eval_metrics_enabled`) rejected; `training:` selects the cascor path, `train:`/`crossval:`/`predict:` (+ `dataset.split`) the recurrence path.
  - Drive: generator preflight (`GET /v1/generators` must report `available: true`), `POST /v1/datasets` (content-addressed `dataset_id` recorded), then `POST /v1/training/start` and poll `GET /v1/training/status` to `COMPLETED`/`FAILED` under the Q-2 wall-clock budget (`outputs.max_wall_seconds`, CLI `--max-wall-seconds` wins) + stall detector (no `current_epoch` progress for `--stall-seconds`, default 120 -> `outcome: "stalled"`).
  - Every cascor-path generator stages through `POST /v1/training/dataset` (alias map incl. gaussian/checkerboard since W-3, juniper-cascor#490) with a post-run G-6 input-width assert (mismatch = acceptance failure).
    - Spiral joined the staged path with F-P4-1: the old spiral-only inline `dataset` source made cascor materialize its in-process fallback (unit-radius, params silently ignored) instead of the configured juniper-data dataset, terminating every service spiral run below_threshold with zero hidden units.
    - Root-cause note: [`notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md`](notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_F-P4-1-SERVICE-SPIRAL-ROOT-CAUSE.md); cascor-side fidelity fix cascor#504; candidate-param plumbing gap cascor#505.
  - Each poll samples the loopback `/metrics` allowlist (`candidate_correlation` / `hidden_units_total` / `training_loss` / `training_accuracy_ratio` / step-duration sum+count) into `artifacts/results/metrics_series.csv` -- correlation exists ONLY there, never in `/v1/metrics/history` rows; a 404 (metrics disabled, G-3) degrades sampling, not the run.
  - Recurrence drive (Wave 2.3): health-gates `/v1/health/ready`, then the **synchronous** `POST /v1/train` (the response IS completion — no poll loop; the Q-2 budget is the request's socket timeout → `timed_out`), then optional `POST /v1/predict` (`predict.from_dataset_split`, default `test`) and `POST /v1/crossval` (same LMU hyperparams as `train:` for bench comparability); every phase refs the dataset by content-addressed `dataset_id` (H-8).
  - Predict/crossval failures are recorded and the run continues to the manifest (acceptance failure), never dying mid-evidence. `outputs.save_model: true` (G-18) re-runs the `juniper-recurrence train` CLI with `--dataset <dataset_id>` + identical hyperparam flags + `--out .../model.npz` as a manifest-recorded extra step (the CLI has no `--params` flag, so the dataset_id ref is the only faithful form).
  - Collects `metrics_final.json` / `metrics_history.json` / `topology.json` / `decision_boundary.npz` (2-D input only) + optional `POST /v1/snapshots` (cascor), `train_response.json` / `predict_response.json` / `crossval_response.json` (recurrence); ALWAYS writes the §13.4 `manifest.json` (also for stalled / timed-out / failed runs) and prints a one-screen summary.
  - **409 preempt (§3.4)**: `start_fresh: true` does NOT stop a live run — the lifecycle lock is held, so the 409 is raised before `start_fresh` is consulted, and after a driver-side stall/budget abort the naive re-run dies on `Training already in progress`. A 409 now gets ONE preemption attempt: `POST /v1/training/stop`, wait for the lifecycle to leave the active set, retry start once.
  - Preemption is decided on **lifecycle state, not message text**: cascor's `routes/training.py:117` wraps every start failure as 409 (including "Training data not provided"), so only `STARTED` / `PAUSED` are preempted. `REPLAYING` rejects all training commands (exit is `/replay/control`) and `INVESTIGATING` needs `/retrain` / `/resume` — a stop there would fail and bury the real reason.
  - **Inert stall window**: when `--stall-seconds >=` the resolved wall budget the Q-2 stall detector can never fire (the budget ends the run first) — a healthy long candidate phase is then labelled `timed_out` rather than `stalled`. Reported as a WARNING plus `driver.stall_window_inert` on the manifest, never fatal: the run is valid, only its guard is weaker than declared.
  - The driver is the sole place both Q-2 knobs are resolved, so it is the only layer that can see their interaction — the suite gate structurally cannot, since a budget may be inherited from `base_config` (`pf3-cascor-pool-scaling` shipped exactly this shape: a 1200 s window against a 600 s inherited budget).
  - Exit codes: 0 success / 1 acceptance (stalled, timed_out, G-6 mismatch, missing essential artifact) / 2 misuse-validation / 3 unreachable / 4 FAILED-5xx. Tests: `tests/test_run_experiment.py`.
- `util/experiments/run_suite.py` -- Suite driver. `EXECUTION_KEYS` forwards **both** Q-2 budget knobs to the driver: `execution.stall_seconds` → `--stall-seconds` (ml#1069) and `execution.max_wall_seconds` → `--max-wall-seconds`. Absent key ⇒ flag omitted entirely, so the driver keeps owning its default.
  - Do not confuse `execution.max_wall_seconds` with `execution.per_run_timeout_seconds`: the latter is only the **subprocess** timeout, which kills the driver from the OUTSIDE and records `timed_out` where the driver would otherwise write an honest `timed_out` manifest (§13.4). Size `per_run_timeout_seconds` ABOVE the wall budget so the driver is the one that stops.
  - A suite could always reach the budget through a dotted `outputs.max_wall_seconds` override (`suites/p4/e-i-cascor-cap-ceiling.yaml:71` does exactly that), but before this key an un-overridden cell silently inherited `base_config`'s value — 3600 s for `spiral-baseline` — with no signal. Both mechanisms are accepted by the R-6 gate. Tests: `tests/test_run_suite.py`.
- `util/get_cascor_*.bash` -- Cascor REST API query utilities (status, metrics, history, network, topology). These helpers read legacy `CASCOR_HOST` and `CASCOR_PORT` environment variables (with `localhost` / `8201` defaults). Do not confuse them with the `JUNIPER_CASCOR_*` variables used by `util/juniper_plant_all.bash`.

### Tests

- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`
- `tests/test_env_repr_safety.py` -- Lint + behaviour gate for the env-repr secret-leak class: forbids raw `os.environ`-derived subprocess `env=` mappings in `tests/` (they leak secrets through pytest `--showlocals`-style frame-local reprs) and proves `tests/redacted_env.py`'s `RedactedEnv` masks its repr while behaving as a normal subprocess env mapping. Includes a synthetic-violation self-test; `patch.dict(os.environ, ...)` is deliberately exempt.
- Doc-link validator regression tests live in [`juniper-doc-tools/tests/`](juniper-doc-tools/tests/) (Wave 4 of the doc-link migration; exercised by the dedicated `CI -- juniper-doc-tools` workflow).
- `tests/test_worktree_cleanup.py` -- Tests for `util/worktree_cleanup.bash` argument parsing, dry-run, and error handling; Phase 1 dirty porcelain exit-1 gate (juniper-ml#747) and clean push / Phase 2 path-collision arms (open #753) drive fixture repos via sourced `phase_1_save_and_push` / `phase_2_create_new_worktree`
- `tests/test_worktree_sweep_scripts.py` -- Tests for `util/ad-hoc/worktree_sweep_*.bash`: survey/apply row compatibility, `SAFE`-only removal, and unknown-repo skips
- `tests/test_cleanup_session_worktrees.py` -- Hermetic tests for `scripts/cleanup_session_worktrees.py`: `_has_merged_pr` fail-closed (gh fail / bad JSON), dirty/unmerged/detached keeps, self-cwd skip, and `--dry-run` remove of main-ancestor / MERGED-PR clean tips
- `tests/test_reap_pytest_orphans.py` -- Tests for `util/reap_pytest_orphans.bash` dry-run, live-parent safety, orphan detection, and isolated kill invocation
  - `TestLiveExperimentProtection`: the P1 pidfile + P2 cmdline keys, reproducing the three shapes a 2026-08-16 dry run would have killed (service / orchestrator / watchdog); the load-bearing live-mode arm proving a genuine orphan still dies while the protected service does not; stale-pidfile conservatism; and a malformed pidfile not aborting the sweep under `set -euo pipefail`
- `tests/test_kill_helpers.py` -- Hermetic process-filter / kill-path tests for `util/kill_all_pythons.bash` and `util/juniper_worker_kill.bash` (PATH-stubbed `ps`/`sudo`/`kill`; bash `kill` builtin disabled; never touches live PIDs)
- `tests/test_check_conda_env_torch.py` -- Hermetic exit-matrix tests for `util/check_conda_env_torch.bash` (P-5 torch._C shadow diagnostic: 0/1/2/3/4 via `JUNIPER_CONDA_DIR` + stub python; no real conda/torch)
- `tests/test_requirements_drift_check.py` -- Tests for `util/requirements_drift_check.py`: structural range validation, BAD_PATH / BAD_RANGE classification, `--ecosystem-root` rewriting, CLI exit codes, JSON output
- `tests/test_editable_install_drift_check.py` -- Tests for `util/editable_install_drift_check.py`: FRESH / WORKTREE_PINNED / ORPHANED classification, `*-DEPRECATED` env exclusion, `--env` filtering, dedup across interpreter trees, CLI exit codes (0/1/2), JSON output, and `--fix --dry-run` canonical-source resolution (synthetic conda-dir fixture; no real pip)
  - `VersionDriftTest` (version axis): static + dynamic version resolution (setuptools `attr` flat and `src/` layouts, hatch `path`), MATCH/STALE classification, orthogonality (a WORKTREE_PINNED install still gets a version verdict), STALE soft by default / hard under `--strict-version` with `--strict` unaffected, the summary+JSON version fields, and `--fix-stale` repairing in place (`drift: "stale-metadata"`, canonical == the recorded path) while ORPHANED repair still resolves canonically
  - Honesty pins in the same class: an undeclared `_version.py` is **never** guessed at (unrecognized backend → UNKNOWN, so no `STALE` can be manufactured from the wrong file), and an ORPHANED target is UNKNOWN rather than a fabricated comparison
  - Ambiguous canonical SKIP (open #795): two non-worktree checkouts with the same `[project].name` → `discover_canonical` returns `(None, [..])`; `--fix --dry-run` emits `action=SKIP` with `ambiguous` in `reason` (never re-points to `candidates[0]`).
  - Live `run_fix` (open #802): mocked `subprocess.run` covers `FIXED` on success, `ERROR` on `CalledProcessError`, and `ERROR` then `FIXED` when the first item raises `OSError` (plan continues).
- `tests/test_env_floor_drift_check.py` -- Tests for `util/env_floor_drift_check.py` (I-2): floor parsing (juniper-* `>=` bound; skips non-juniper/floorless/self-ref; dedup-highest), numeric version compare (`0.10.0 > 0.9.0`), OK/BELOW_FLOOR/MISSING classification, exit codes (0/1/2, `--strict`), `--json` -- via a synthetic site-packages fixture (no real pip/conda); also asserts no hardcoded env name. Sole gate (`util/` not lint-gated); real-env scan is manual-verify.
  - Open #796 adds `ResolveSiteDirsTest` (`--site-packages` wins, `--env` expand, ecosystem `used_by`, exit-2 reasons). Open #802 adds `InstalledVersionsTest` (highest-across-dirs, malformed/unreadable skip, underscore normalize).
- `tests/test_workflow_script_paths.py` -- Lint test: every `python <path.py>` / `bash <path.bash>` invocation in `.github/workflows/*.yml` must reference a path that exists in the repo. Cross-repo paths (`juniper-X/...`) are skipped as runtime-resolved. Catches the failure class that broke 3 juniper-X CIs on 2026-05-18.
- The sequence-safety screen unit tests (symbol + docs: `LOST`/`WEAKENED`/`DUPLICATED`, SF3 masking pin, relocation WARN, heading / `>=N`-run FAIL, both trailer escapes + wildcard, `--min-run`, the `--scope` glob engine, exit codes 0/1/2) moved to `juniper-ci-tools/tests/` with the package migration (rollout W3); they run under the dedicated `CI -- juniper-ci-tools` workflow. juniper-ml's `tests/test_ci_tools_drift.py` carries the anti-resurrection guard + the two new screen-pin drift checks.
- `tests/test_doc_tools_drift.py` -- Lint test (plan §5.1) for `juniper-doc-tools` pins. Extracts the `juniper-doc-tools>=X,<Y` pin from juniper-ml's own workflows and each cloned consumer repo's `ci.yml`, then asserts the range still admits the current version (read from `juniper-doc-tools/pyproject.toml`). Soft-warns on pins more than 2 minors behind; hard-fails when the upper bound excludes current.
- `tests/test_service_fork_drift.py` -- Drift gate for the security guards that must hold identically in `juniper-data`'s and `juniper-cascor`'s forks of the `juniper-service-core` middleware / security code (defect-register §2.3 "Copy drift").
  - A registry of named guards, each detected by a small source marker, rather than a file diff: the forks diverge legitimately and constantly (juniper-data deliberately holds API keys in a `list` for `compare_digest` timing where service-core uses a `set`), so a diff would drown the signal.
  - Two-sided by design. `ENFORCED` guards must be **present** in every fork; their disappearance is a regression. `KNOWN_GAP` guards must still be **absent** -- when someone closes one, the gate fails and instructs them to promote the row to `ENFORCED`, so the ledger cannot rot into a list of things that used to be true.
  - Cross-repo assertions gate exactly like `test_ci_tools_drift.py` (`GITHUB_ACTIONS=true` or `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`); the registry-structure checks and the matcher's negative control always run. It bites in `docs-full-check.yml`, the only job that clones the siblings. The register's "OPTIONS bypass" row is deliberately **not** encoded: it landed in no copy, so there is no reference implementation to derive a marker from.
- `tests/test_assert_release_tag.py` -- Behavioural tests for `util/assert_release_tag.bash` plus a **wiring gate** asserting all 7 publishers invoke it with their own `--expect-prefix`, and that **no publisher grants `id-token` at workflow level** (P4).
  - Drives synthetic dist directories: happy paths (meta, sub-package, `-rc1` normalization, alpha), and the refusals that matter -- branch ref, **empty** ref_type (must fail closed, not read as a tag), tag/version mismatch, wrong package prefix, missing dist dir, sdist-only, version-less tag, misuse exit 2.
  - The mismatch case is a live regression guard: it originally passed because `tr -d '-_'` errored on this host and both sides normalized to empty. `util/` is outside every pre-commit Python hook's scope, so this suite is the gate.
- `tests/test_publish_env_policy_drift.py` -- Drift gate for the **tag-only deployment ref policy** on every `pypi` / `testpypi` environment ([publish-path design](notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md) §6 Option A / §12.5).
  - The control lives in GitHub **settings, not the repo**: no test covered it, no reviewer sees a diff when a policy is deleted, and the failure is silent -- the publish path just becomes permissive again.
  - Two load-bearing invariants: **no branch-type policy may exist** (adding a `main` branch policy re-opens branch dispatch while every tag pattern stays intact and the environment still looks configured -- owner decision D3 was tag-only), and **`pypi` must retain `required_reviewers`** (a `PUT` is create-or-update, so a careless payload clears the human gate while successfully setting a ref policy -- the environment then looks *more* configured while being weaker).
  - Structural checks + the detector's **negative control** always run offline (a gate that cannot fail is not a gate; an untyped policy must read as `branch`, never `tag`). The live half is gated on `GITHUB_ACTIONS=true` / `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` and is read-only (`gh api` GETs).
  - **No silent caps**: per-PR CI's built-in `GITHUB_TOKEN` reaches juniper-ml only, so the live half partitions the registry repos into readable / unreadable, verifies the readable ones, **names** the unverified ones, and refuses to pass if nothing at all was readable. A repo that IS readable but whose environment 404s is a real finding (deleted environment), not a permission skip. Full-fleet cover: `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`.
  - Repair: `util/ad-hoc/2026-08-17_apply_env_tag_policies.bash --apply <repo> <env>`.
- `tests/test_pyproject_extras.py` -- Lint test pinning the `[project.optional-dependencies]` surface (`clients`, `worker`, `servers`, `tools`, `doc-tools`, `all`). Asserts the exact set of extras, the exact membership of each, that `[all]` aggregates every non-alias extra exactly once, and that `[project].version` is semver-ish. Added pre-0.5.0 after juniper-ml#295 introduced `[servers]` + `[tools]` without regression coverage; any future edit to extras must update the lint contract in the same PR.
  - juniper-ml's own pin check runs every PR; the cross-repo assertion auto-skips when siblings aren't on disk and additionally skips local runs by default. Set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to opt in locally.
- `tests/test_template_library_drift.py` -- Lint test enforcing manifest <-> template consistency for the custom-agent template library (`prompts/agent_templates/`): every registered template exists and every template is registered; each follows the canonical section skeleton in order; every `{{placeholder}}` matches the systematic convention; the `generic` fallback always matches.
  - The **sole gate** for the library because `prompts/**` is excluded from all pre-commit hooks, so it must stay wired into `ci.yml`. Design-of-record §5.4/§9.
- `tests/test_template_selection.py` -- Lint validating `manifest.yaml`'s `match_signals` support deterministic category selection: exactly one always-match fallback (`generic`), every other template has non-empty keyword signals, no two share an identical keyword set, and every `class` is allowed. Companion gate to the library drift test.
- `tests/test_template_select_preview.py` -- Tests for `util/template_select_preview.py` (the offline selection preview, P2): drives the real manifest (so it also guards selection drift) -- a task with a template's keyword selects that template (`failing-tests`), a no-keyword task falls back to `generic`, the ranked candidates exclude the always-match fallback, and the CLI exits 0 with the documented JSON shape.
- `tests/test_template_data_resolver.py` -- Tests + drift gate for the custom-agent suite data layer (PR 6b): the five `prompts/agent_templates/data/*.yaml` files load, `util/template_data_resolver.py`'s `load`/`resolve` (dotted lookup) work, and -- since `prompts/**` is pre-commit-excluded -- this is the sole gate; also asserts `conventions.line_length` matches `.markdownlint.yaml` and the handoff threshold is the current 95-99% (not a stale 80%).
- `tests/test_open_signed_pr.py` -- Tests for `util/open_signed_pr.py` (signed cross-repo PR opener). Hermetic: `gh` is a PATH stub that records argv and replays canned stdout, so no network / repo / `git` is touched.
  - Pins the mutation name (`createCommitOnBranch` -- the whole point), `expectedHeadOid` == the resolved base sha, base64 additions, `fileChanges.deletions` present for `--delete` and **omitted** when unused, and the explicit `ref=refs/heads/<branch>` on the refs POST (the ml#770 R7 lesson).
  - Also pins every refusal path writing nothing: dup-guard exit 1, existing-branch exit 1, no-changes exit 2, unreadable source exit 2. `util/` is outside every pre-commit Python hook's scope, so this suite is the gate.
- `tests/test_scaffold_template.py` -- Tests for `util/scaffold_template.py` (P5 generator): the generated template passes the real library-drift helpers (skeleton order + placeholder well-formedness), `--dry-run` writes nothing, refuse-on-collision (exit 1), bad-class / missing-keywords (exit 2), and -- the safety contract -- the tool NEVER edits `manifest.yaml` (prints the stanza).
- `tests/test_prompt_validator_contract.py` -- Static contract test for the `prompt-validator` subagent (`.claude/agents/prompt-validator.md`, PR 3): frontmatter shape (`tools` = exactly `Read, Grep, Glob, Bash`, `model` concretely pinned per OQ-4), every rubric ID it cites exists in `RUBRIC.md` (incl. the `R2.0`/`R3.4` hard gates), and the pinned verdict schema + PASS/FAIL samples in `tests/fixtures/prompt_validator/` match the §5.3 contract. E-3: re-probe block is `<target>`-qualified (not CWD).
- `tests/test_prompt_discovery.py` -- Behavioural tests for `util/prompt_discovery/` (custom-agent suite PR 4): the grounding-bundle schema + provenance envelope emitted by `cli.py`, per-probe graceful degradation, the hard-stop on a non-git root (exit 2), the `test_status` `cold_cache`/empty distinction, plus E-3 `--target-repo` cross-repo grounding. `util/` is not pre-commit-lint-gated (flake8/black scope to `scripts`+`tests`), so this unittest is the gate; imported via the `sys.path.insert` idiom.
- `tests/test_symbol_overlay.py` -- Tests for `util/prompt_discovery/symbol_overlay.py` (the Serena symbol overlay, design OQ-8): the deterministic merge of Skill-resolved Serena facts into a bundle's `symbol_probe` slice -- Serena-resolved wins, grep is the fallback, an unresolvable symbol stays `UNRESOLVED`, the input bundle is not mutated, and `cli.py`'s contract is untouched. Stdlib only; importlib-loaded.
- `tests/test_predict_merge.py` -- Hermetic tests for `util/fleet_triage/predict_merge.py` (Stage-0 supervisor script layer): bare-origin + branch fixtures drive the four verdicts (symbol-loss / docs-deletion / injected gate-fail DAMAGED, plus MERGE-CLEAN / NEEDS-UPDATE-BRANCH / CONFLICT), TRUE-delta-vs-stale-file-list discrimination, `--batch` cluster map + order (fake `gh`), detached-clone-never-mutates-source, CLI exit codes.
  - Also covers docs-screen edges (header ignore / additions-only / non-`.md`), no-`.py` gate skip, and `repair`/`fix-first` heal tokens (juniper-ml#910). `util/` not lint-gated so this is the gate; `sys.path.insert` + `RedactedEnv`.
- `tests/test_fleet_supervisor_contract.py` -- Static contract for the `fleet-supervisor` subagent (`.claude/agents/fleet-supervisor.md`, flood §4 item 7): frontmatter (`tools` == exactly `{Read,Grep,Glob,Bash}`, `model` opus + `effort` max, name == stem) and body wiring -- references `util/fleet_triage/predict_merge.py`, documents all four verdict tokens, states the read-only / never-push mandate + the two-key DUP-CLOSE rule (overlap AND owner confirmation). Modeled on `test_prompt_validator_contract.py`.
- `tests/test_generated_prompt_index.py` -- Tests for `util/generated_prompt_index.py` (P4): name-convention parsing, `.gitkeep`/malformed ignored, and the destructive-path safety -- `--prune`/`--archive` without `--yes` (or under `--dry-run`) delete/move nothing, `--prune --yes` / `--archive DIR --yes` act only on convention-named stale files (never `.gitkeep`/hand-placed), and the generated-dir location is read from `conventions.yaml`.
- `tests/test_thread_handoff_archive.py` -- Drift guard for `prompts/thread-handoff_automated-prompts/`: every archived handoff prompt filename must follow `HANDOFF_YYYY-MM-DD_subject.md` with ASCII subject text, and top-level `notes/*.md` references to archived handoff prompts must resolve to real files. Added after PR #617 standardized old `handoff_subject_YYYY-MM-DD.md` archive names.
- `tests/test_install_agents.py` -- Tests for `util/install_agents.bash` (custom-agent suite PR 6a): drives the `~/.claude` mirror against a synthetic source repo + throwaway target (`JUNIPER_ML_REPO_ROOT`/`JUNIPER_CLAUDE_HOME` overrides) and asserts it is idempotent, reversible (`--reverse`), `--dry-run`-safe, and never clobbers or removes a file it does not own.
- `tests/test_agent_suite_doctor.py` -- Tests for `util/agent_suite_doctor.py` (the suite health-check dogfood utility): the real suite has zero FAIL; synthetic trees missing a component FAIL the matching check (exit 1); `--json` shape; `--no-discovery` skips the subprocess; `--strict` promotes WARN to exit 1; a non-repo `--repo-root` exits 2. Stdlib-only; importlib-loaded.
  - `DoctorDiscoveryCheckTest` (juniper-ml#825): pins discovery fail-closed arms (missing CLI / nonzero exit / invalid JSON / missing schema or provenance / well-formed OK) via hermetic fake `cli.py`.
- `tests/test_agent_suite_summary.py` -- Tests for `util/agent_suite_summary.py` (P3 quick-reference): drives the real suite so every agent and template appears, `--json` round-trips, and `--markdown` rows respect the 512-char line-length convention. Stdlib + PyYAML; importlib-loaded.
- `tests/test_template_agent_skill_lint.py` -- Static lint for the `template-agent` Skill (`.claude/skills/template-agent/SKILL.md`, PR 5): frontmatter (`allowed-tools` includes `Agent`, `model: opus` + `effort: max`, user-only) and that the bounded state machine wires to real artifacts (template library, `RUBRIC.md`, `util/prompt_discovery/cli.py`, the emission dir, the `prompt-validator` subagent). E-3: threads `<target>` to the validator. The Skill-surface gate (pre-commit-excluded except markdownlint).
- `tests/test_service_smoke_skill_lint.py` -- Static lint for the `service-smoke` Skill (`.claude/skills/service-smoke/SKILL.md`, E-1 Stage 1/2): the **Stage-2 boundary** -- a browser MCP (`mcp__playwright`) MUST be declared for the opt-in `--ui` smoke (inverts Stage 1's no-browser rule), `Agent` still forbidden -- plus `opus`+`max`/user-only frontmatter, browser-close teardown, the `--ui`/`/dashboard`/console smoke, `UI_UNHEALTHY_REPORTED`, and bounded waits. Structural-only gate.
- `tests/test_ui_test_author_skill_lint.py` -- Static lint for the `ui-test-author` Skill (E-6): frontmatter (suite `opus`+`max`, user-only, `Write` + a declared browser MCP, NO `Agent`) + that it models canopy's `src/tests/ui/` harness (`dashboard_page` / `@pytest.mark.ui` / the `dbc.Input` wall via `/api/state`), the browser-close teardown, the reviewed-never-auto-merged contract, terminal states, and bounded waits. Structural-only gate; live authoring = manual smoke-verify.
- `tests/test_agents_frontmatter.py` -- Suite-wide frontmatter gate over every `.claude/agents/*.md` (the `prompt-validator` plus the round-2 `planner` / `auditor` / `task-executor`): `name` equals the filename, the `description` is substantive, `tools` are declared, the body is non-trivial, and the owner-directed defaults `model: opus` + `effort: max` hold -- so a new agent cannot drift from the standing defaults. The shared invariant complementing `test_prompt_validator_contract.py`.
- `tests/test_ci_tools_drift.py` -- Lint test (dep-docs plan §5.1) for `juniper-ci-tools` pins. Mirrors `test_doc_tools_drift.py`: walks juniper-ml's own workflows (`ci.yml`, `main-verify.yml`, `lockfile-update.yml`, `docs-full-check.yml`) plus each cloned consumer repo's `ci.yml`, extracts the `juniper-ci-tools>=X,<Y` pin, and asserts the range still admits current (read from `juniper-ci-tools/pyproject.toml`). Same skip semantics + `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` override as the doc-tools sibling.
  - Also carries the **sequence-safety anti-resurrection gate** (rollout W3 / plan §W3 step 3.3): `SequenceSafetyPackageMigrationTest` asserts juniper-ml's tree has no resurrected inline `util/sequence_safety/` copy or the two moved screen tests (a synthetic-fixture negative proves it bites); `main-verify.yml` in the scanned workflows enforces the two new `>=0.8.0,<0.9.0` screen pins still admit current.
- `tests/test_coverage_gap_mapper_drift.py` -- Dogfood/drift gate (E-4 + C-0) for the `juniper-coverage-gap-map` console script in `juniper-ci-tools` (modeled on `test_ci_tools_drift.py`). STRUCTURAL: script registered, `_version.py` matches version, pins admit it, `--enforce`/`--fail-under-*`/`--omit` wired. END-TO-END (C-0): `--enforce` exits 1 on a gap / 0 clean over a synthetic `coverage.json`. Full matrix in `juniper-ci-tools/tests/`.
- `tests/test_env_drift_check_drift.py` -- Structural drift gate for the `juniper-env-drift-check` console script (env floor-drift guard, test-suite audit §10.1).
  - Mirrors `test_coverage_gap_mapper_drift.py`: asserts the entry point is registered (`juniper_ci_tools.cli_env_drift_check:main`), both module halves ship, version/pin coherence, **plus a class guard** that *every* `juniper_ci_tools/cli*.py` has a `[project.scripts]` entry.
  - Added in `juniper-ci-tools` 0.5.1 after #580 silently dropped the 0.5.0 entry point -- the always-on assertion the `python -m` behavioural dogfood (`tests/test_env_drift_check.py`) lacked.
- `tests/test_release_train_registry.py` -- Structural lint + registry<->pyproject drift gate for `util/release_train/registry.yaml` (plan §4.1): always-on checks (18 packages, 8 repos incl. `juniper-recurrence`, required fields, enums, the dynamic-version set, archive-name convention, `depends_on`) plus resolution -- the 7 in-repo juniper-ml packages unconditionally (forward + reverse), the 11 cross-repo entries via the `test_doc_tools_drift.py` sibling auto-skip.
  - Also home of the always-on `VersionDunderLockstepTest` (ml#701): every in-repo static-version package with a `_version.py` must keep `[project].version` == `__version__` (dynamic packages exempt -- their dunder IS the source); the ci-tools 0.7.0 / service-core 0.5.0 stale-dunder class.
- `tests/test_release_train_detect.py` -- Hermetic tests for `util/release_train/detect.py` (plan §4.2/4.3); no network / gh / pip (sources injected). Covers each classification, static/dynamic version reads, tag resolution, the substantive-hunk filter (discount comment/docstring/link; catch real code), path-scoping (subdir vs cascor repo-minus-subpkgs), CHANGELOG conflict surfacing, SemVer, manifest JSON shape, and exit codes 0/1/2. `util/` is not lint-gated, so this unittest is the gate.
  - Soft-fail pins: truncated-without-ship / unreadable-declared / compare-not-ok → `SHIP_UNCERTAIN` (juniper-ml#763); hygiene `SourceError` → `tag_only=None` (juniper-ml#761); offline `list_releases` raise (open #773).
- `tests/test_release_train_propose.py` -- Hermetic tests for `util/release_train/propose.py` + `notes_render.py` (Phase 2.1); no network / gh / repo writes. Covers a dry-run proposal for a static- and a dynamic-version package, the CHANGELOG move, notes render vs the template skeleton + the `RELEASE_NOTES_<pkg>_v<version>.md` convention, dup-guard suppression, the `changelog_conflict` refusal, and that a dry-run writes nothing. `util/` is not lint-gated, so this is the gate.
  - ml#701 dunder-lockstep shapes: static-with-dunder bumps BOTH files; static-without-dunder emits no phantom `_version.py` edit; the dynamic path is unchanged; a present-but-unparseable dunder is flagged REQUIRED-manual in the checklist.
  - Sibling/meta AGENTS.md shapes (ml#706 / #720): primary co-change; sub-package host skip; unexpected header REQUIRED; already-at-target silent; absent / missing-Version REQUIRED.
  - notes_render meta/MAJOR/Breaking/`*` bullets: juniper-ml#756.
- `tests/test_release_train_archive_guard.py` -- Hermetic tests for `archive_guard.py` (Phase 3.1, §7.2); no network/git/gh. Drives the four-rule classifier with synthetic `git diff --name-status` sets + the CLI (`--name-status-file`) against the real `registry.yaml`: a pure notes-add PASSES, a non-archive PR SKIPs, and modify/delete/out-of-path/bad-name/mixed diffs each FAIL; plus filename convention, parsing, exit codes 0/1/2. The gate for `util/`.
- `tests/test_release_train_ceremony.py` -- Hermetic tests for `ceremony.py` (Phase 3.2, plan §7/§8/§9.3); no network/gh/git/writes.
  Covers every §8 precondition HALT (main-CI / anomaly / missing-CHANGELOG / notes-render-failed / TestPyPI-verify), execute `RELEASED` when both publish gates completed, the happy-path exact action sequence, dup-guard/idempotent re-entry, the R7 gh-surface invariant (live seam issues only the allowlisted verbs + the 2 archive api calls -- `git/refs` POST + `createCommitOnBranch`), and a dry-run leaving `git status` clean. The gate for `util/`.
  - Execute-time open-PR reuse + archive-already-on-main idempotent re-entry arms (juniper-ml#730).
  - R7 archive-lane `ref=` required (juniper-ml#770): missing/empty `ref=` on a `git/refs` POST is `SeamViolation` (not deferred to the live API).
- `tests/test_agents_md_version_drift.py` -- Lint test pinning `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s `[project].version`. Added after juniper-ml#295 bumped pyproject 0.4.1→0.5.0 but left AGENTS.md at 0.4.0 for ~6 days (fixed in juniper-ml#304); this lint makes the drift impossible to ship. Intentionally portable: auto-locates the repo root, so the module can be dropped into any Juniper repo's `tests/` (skips loudly if AGENTS.md has no canonical header).
- `tests/test_agents_md_header_schema.py` -- Lint pinning `AGENTS.md`'s canonical header schema. Six required fields in this relative order: `**Project**`, `**Repository**`, `**Author**`, `**License**`, `**Version**`, `**Last Updated**`. Extras (e.g. `**Python**:`) may be interleaved freely. Validates each value non-empty and `**Last Updated**` is `YYYY-MM-DD`. Currency of the date is enforced by `.github/workflows/agents-md-touch-up.yml`. Portable (self-locating).
- `tests/test_agents_md_tree_drift.py` -- Lint (gap G-3) asserting every tracked non-hidden top-level dir (`git ls-tree`; the `ls -d */` surface) appears as a node in `AGENTS.md`'s fenced Repository-Structure tree, catching the indented-tree omission the grep-based `test_agent_suite_path_drift.py` cannot (stale `templates/`, missing `conf/`/`papers/` + 6 sub-package dirs). Portable; a synthetic negative case proves it bites.
- `tests/test_isolated_stack_script.py` -- Contract tests for `util/isolated_stack.bash` (plan unit E1): `bash -n` syntax, launch-line text assertions (dedicated-venv install, `python -m juniper_data`, `uvicorn api.app:create_app --factory`, canonical canopy env vars, the control-WS origin/allowlist pair), and hermetic `--dry-run` behavioural checks (prints commands with ports expanded, touches nothing; misuse exits 2).
- `tests/test_experiment_stack_script.py` -- Contract + behavioural tests for `util/experiment_stack.bash` (CLI experimentation plan Wave 2.1; `util/` is not
  pre-commit-lint-gated, so this unittest is the gate): `bash -n` syntax, the CLI misuse matrix (exit 2), the §9.3 port ranges and §6.4 RUN_DIR contract, the §6.1 launch
  recipes env-set by env-set, the **F-6** listener-pid rule (no `$!` in any `*_up`; `record_listener_pid` runs after `wait_for_health`; teardown verifies uid + cmdline),
  §7.3 suffix-based `_monitoring$` gateway discovery + the exact socat relay line, the §7.2 target file rendered and parsed as JSON (four labels), and the operator-safety
  invariants (no `JuniperProject.pid`, no canopy, no repo `.env` write, no operator port).
  - Behavioural arms are hermetic: `JUNIPER_EXP_{RUN,LOCK}_ROOT` / `_DEPLOY_DIR` / `_CONDA_DIR` redirect every path into a tempdir and `ss`/`curl`/`docker`/`socat` are PATH
    stubs -- `--dry-run --up` prints all three launch classes with allocated ports expanded while leaving run root / lock root / targets dir non-existent; `allocate_port`
    skips locked and bound ports and fails loudly on an exhausted range; `--down` kills a self-spawned detached child through the **pidfile** path (the stubbed `ss` reports
    no listener, so kill-by-port cannot be what fired), removes the target file, releases the lockdirs, writes `teardown.json`, and preserves `artifacts/`.
  Live `cascor_up` / `canopy_up` compose pins (`TestCascorUp` / `TestCanopyUp` — fake `conda.sh` + PATH stubs; juniper-ml#813). Wired into `ci.yml` beside the `test_juniper_{plant,chop}_all.py` launcher tests.
  - Live compose coverage for `data_up` (`TestDataUpLive`: venv create/skip, pip extras, `PYTHON_GIL=0`, pidfile, missing-`python3.14` abort — juniper-ml#807).
- `tests/test_run_experiment.py` -- Hermetic tests for `util/experiments/run_experiment.py` (CLI experimentation plan Waves 2.2-2.6: the cascor + recurrence service paths, the §8.1 + §8.2 plot sets, and the §8.3 stats/summary renderers (e2e stats assertions for both kinds + every-outcome coverage + the `StatsSummaryUnitTest` percentile/delta/grouping/degraded-notes units) --
  plot arms cover all-rendered PNGs for both kinds (sequence-NPZ stub artifact for §8.2), per-kind plot-name validation, skip-vs-acceptance semantics (eval-disabled / degraded-sampling / disabled-phase skips, matplotlib-unavailable failure), and the `plots_cascor.py` / `plots_recurrence.py` renderer units incl. the `y_reg_` target-key preference;
  `util/` is not pre-commit-lint-gated, so this unittest is the gate). A scripted stub HTTP server stands in for juniper-data, cascor, and recurrence (no live services): the
  §5.6 YAML validation arms (unknown block/key, `schema_version`, mandatory `experiment.seed`, the rule-6 infra-key rejection, kind resolution, the §5.5 recurrence blocks
  incl. `dataset.split` / `crossval.n_folds` / `predict.from_dataset_split`), the cascor drive loop (completion / `FAILED` / Q-2 stall / wall-clock budget with
  CLI-beats-YAML precedence), the F-1 `/metrics` 307-redirect sampling arm + the G-3 404 degrade, the G-6 staging path (alias map, no inline `dataset` on start,
  shape-assert pass/mismatch, unstageable-generator refusal), the recurrence path (synchronous train 200/409/422/socket-timeout arms, predict/crossval `dataset_id` refs +
  record-and-continue on failure, the G-18 `save_model` CLI re-run via a PATH stub + missing-CLI acceptance failure), `ports.json` endpoint resolution, the §13.4 manifest
  written for every outcome, and the full 0/1/2/3/4 exit matrix incl. `RedactedEnv` subprocess arms.
- `tests/test_experiment_config_schemas.py` -- Wave 3.5 drift gate (§10.6 row 3): walks the sibling checkouts' `conf/experiments/*.yaml` (cascor Wave 3.2, recurrence Wave 3.4) and asserts each loads through the driver's §5.6 `load_config` AND that every `service:` key names a real app `Settings` field --
  extracted statically via AST (cascor `Settings`; recurrence `Settings` + the in-repo service-core `SettingsBase`), so no torch-heavy app import is needed. Cross-repo walk gated like `test_doc_tools_drift.py` (`GITHUB_ACTIONS=true` or `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`; sibling-absent skips loudly); the AST-extractor self-check always runs.
- `tests/test_experiment_suite_yamls.py` -- Drift gate (R-6) over the shipped suites in `util/experiments/suites/**`, which no test loaded before it: every suite must pass `run_suite.load_suite` (catching the unknown-`execution:`-key / `stall_second` typo class that otherwise surfaces hours into a GPU campaign), and any oversize `app: cascor` suite must declare an `execution.stall_seconds` above the driver's `DEFAULT_STALL_SECONDS` (read from the driver source, not hardcoded).
  - **Oversize is pool OR cap.** The original gate triggered on `candidate_pool_size >= 16` only, so a wide-**cap** suite at a modest pool shipped and then lost its widest cells to a false `stalled` hours in — the candidate phase slows every iteration as the cascade widens each candidate's input, i.e. "the ml#1069 class, arriving through width instead of through pool size" (`suites/p4/e-i-cascor-cap-ceiling.yaml:46-50`). `max_hidden_units >= 64` now triggers too.
  - **Third contract — wide-cap suites must pin a wall budget**, via either `execution.max_wall_seconds` or a dotted `outputs.max_wall_seconds` override (E-I uses the latter, so accepting only the former would fail a correctly-budgeted suite). Thresholds are measured, not guessed: E-I at fixed pool 8 ran cap 32 → 1497.4 s, cap 64 → 2907.1 s, cap 128 → **4243.6 s** against a 3600 s inherited default, so 128 would have been truncated and 64 clears by only 693 s.
  - **Known limitation**: only the suite's own `matrix` / `include` are read, so a pool or cap inherited from `suite.base_config` is invisible — deliberate, because resolving `base_config` reaches into sibling repos and would turn a structural gate into one that skips whenever the ecosystem is not checked out.
  The Q-2 detector watches `current_epoch`, which does not advance while the CANDIDATE pool trains, so those cells are recorded `stalled` while perfectly healthy -- the P4 E-A grid lost its pool-16 cells to exactly that. Structural only: deliberately never calls `expand_cells`, which would resolve sibling-repo `base_config` and turn the gate into a skip. Carries a negative control plus an anti-resurrection check for the retired `util/ad-hoc/2026-08-10_driver_stall_shim.py`.
- `scripts/test.bash` -- Manual end-to-end harness for session create/resume launcher flows
- `scripts/test_resume_file_safety.bash` -- Regression script ensuring invalid `--resume <file.txt>` input does not delete the source file

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

### Main CI (`ci.yml`)

Triggered on push to `main`/`develop`/`feature/**`/`fix/**` branches and PRs to `main`/`develop`.

Jobs:

1. **pre-commit** -- Runs all pre-commit hooks (flake8, bandit, shellcheck, yamllint, markdownlint). G4 changed-files split (flood §4 item 8 phase 2): `pull_request` / `merge_group` scope to the event's changed files (`--from-ref <BASE> --to-ref HEAD`); `push` keeps `--all-files`. The 3 required `Pre-commit (Python 3.1x)` context names are unchanged.
2. **tests** -- Python unittest (`test_wake_the_claude.py`, `test_workflow_script_paths.py`, etc.) and bash regression tests
3. **build** -- Package build, twine validation, extras metadata verification
4. **docs** -- Documentation link validation (`--cross-repo skip`)
5. **security** -- pip-audit for dependency vulnerabilities
6. **dependency-docs** -- Generates dependency documentation via the `juniper-generate-dep-docs` console script from the PyPI-published `juniper-ci-tools>=0.1.0,<0.2.0` package (replaces the legacy `util/generate_dep_docs.sh` deleted in juniper-ml#298)
7. **release-train-archive-guard** (`pull_request` + `merge_group`) -- Runs `util/release_train/archive_guard.py` over the PR's changed files to prove the exempt notes-archive PR is add-only / path-confined / name-valid / single-purpose (plan §7.2 / step 3.1). SKIPs (passes) for any PR not touching `notes/releases/`, so it never blocks a normal PR; a violation fails only this check (the PR falls back to the standard owner gate).
    It also admits `merge_group` so the required context re-posts on a queued merge commit — but `merge_group` has no `github.base_ref`, so the job short-circuits to a green notice before any checkout and every real work step stays
    `if: github.event_name == 'pull_request'`. Standalone (and absent from the Quality Gate `needs:`) so the owner can later mark it a **required** status check (step 3.3). Gate: `tests/test_archive_guard_workflow.py`.
8. **sequence-safety** (ADVISORY; `pull_request` + `merge_group`) -- Installs `juniper-ci-tools` (>=0.8.0) + runs `juniper-symbol-loss-check` (explicit ml `--scope`) + `juniper-docs-additions-check` over the PR base..HEAD (P2 G1/G2); uploads `sequence-safety-report` (G5-vi). Standalone, ABSENT from the Quality Gate `needs:` so its skip-on-push never fails the gate — soak-advisory, promoted in the ruleset later, never via the QG `needs:`. WARN-only `allow-symbol-loss` / `docs-rewrite` label hatch.
9. **fleet-pr-lint** (ADVISORY; `cursor/*` PRs only) -- Warnings-only signals to the step summary (P2 G5-iv; flood §4 item 8 phase 4): commit count, `black --check`, fan-out, and AGENTS.md / cheatsheet hotspot notes. Never fails, never comments.
10. **required-checks** -- Quality gate enforcing all checks must pass

### Publishing (`publish.yml`)

Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first, then PyPI (`pypi needs: testpypi`). The Gate 1 verify installs `juniper-ml` bare, then `[clients]`, then `[tools]` from TestPyPI with PyPI as the extra index — never `--no-deps`, and never the heavy `[worker]` / `[servers]` / `[all]` / `[recurrence]` extras. The `build` job skips `juniper-<pkg>-v*` tags. Gate: `tests/test_publish_testpypi_verify.py`.

**Publish-path authorization (all 7 publishers, 2026-08-17).** Three layers, in decreasing order of how much they survive:

1. **Environment tag policies** — the actual control. Each `pypi` / `testpypi` environment admits only release tags (`v*`, `juniper-*-v*`, `rc*`, `juniper-*-rc*`, `hf*`, `juniper-*-hf*`), so a dispatch from a branch is refused **before the job starts** and no OIDC credential is minted. It is settings, not code, so it survives a workflow edit — and is guarded by `tests/test_publish_env_policy_drift.py`.
2. **P3 `util/assert_release_tag.bash`** — the build job asserts ref-is-a-tag and tag-version-equals-built-wheel. Defense in depth: deletable by anyone editing the workflow, but fails earlier and names the reason.
3. **P4 job-scoped `id-token`** — `id-token: write` sits on the two publish jobs, never the workflow block, so the build job cannot mint a PyPI credential at all. Job-level `permissions` **replace** the workflow block rather than merging, so each publish job restates `contents: read` for its checkout.

Full design + the controls that proved it: [`notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md`](notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md).

### Documentation Full Check (`docs-full-check.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch. Clones the siblings named in `env.ECOSYSTEM_REPOS` and runs full cross-repo documentation link validation (`--cross-repo check`), the consumer `juniper-doc-tools` / `juniper-ci-tools` pin lints plus downstream integration, and the L2/L3 `claude.yml` audit in `JUNIPER_ROOT` mode.

`ECOSYSTEM_REPOS` membership must equal the registry publishing repos minus `juniper-ml` (already the workflow checkout) plus `juniper-deploy` (a doc / `claude.yml` consumer with no PyPI package). The clone list historically omitted
`juniper-recurrence`, silently dropping that publishing sibling from every weekly screen; `tests/test_docs_full_check_ecosystem.py` now pins the membership, and `tests/test_doc_tools_drift.py` walks every consumer
`.github/workflows/*.{yml,yaml}` so a pin declared in `ci-docs.yml` (recurrence) is not skipped.

### Security Scan (`security-scan.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch, permissions `contents: read`. Installs the meta-package editable, then runs a **sole** `pip-audit --strict --desc on` (no `--skip-editable`). This is the hard weekly CVSS screen — distinct from the per-PR `ci.yml` `security` job, which intentionally uses `--skip-editable` and omits `--strict` so an unreleased editable meta install does not fail every PR. Do not copy either contract onto the other path. Gate: `tests/test_security_scan_workflow.py`.

### Lockfile Update (`lockfile-update.yml`)

Weekly schedule (Monday 08:00 UTC) and manual dispatch, permissions exactly `contents: write` + `pull-requests: write`. Installs `juniper-ci-tools` from PyPI, runs `juniper-generate-dep-docs` to regenerate `conf/requirements_ci.txt` +
`conf/conda_environment_ci.yaml`, and opens a PR on `chore/lockfile-update` (labels `dependencies` + `automated`) via SHA-pinned `peter-evans/create-pull-request` when the tree changes. A clean tree opens no PR, and the PR is reviewed
like any dependency change — never auto-merged. The legacy `util/generate_dep_docs.sh` was deleted in juniper-ml#298; this workflow must keep the console-script path. Gates: `tests/test_lockfile_update_workflow.py` +
`tests/test_ci_tools_drift.py`.

### Release Train (`release-train.yml`)

Daily schedule (13:00 UTC = 08:00 America/Chicago CDT; Q-CADENCE) and manual dispatch. Phase 1 report-only detection for the PyPI release train ([plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 1.3): full-history clones of the 7 sibling package repos, then `util/release_train/detect.py --json` classifies all 18 registry packages; the run publishes the release-manifest artifact plus a step-summary table.

Detector exit 1 (action needed) is a normal green outcome; only exit >= 2 (hard source error) fails the run. The `detect` job writes nothing: no PRs, no Releases, no (Test)PyPI interaction. The `RELEASE_TRAIN_MODE` repo variable (`off`|`report`|`propose`|`ceremony`, default `report`; an unknown value warns and degrades to `report`) plus the `mode` dispatch input is the instant kill switch and mode selector (precedence: dispatch input > repo variable > `report`).
The operator's guide to the four modes, the two owner gates, the §8 HALT catalog, and rollback is [`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md).

**Propose mode (Phase 2.2, opt-in).** Dispatching with `mode=propose` (or setting `RELEASE_TRAIN_MODE=propose`) adds a second, **write-scoped** `propose` job — `permissions: {contents: write, pull-requests: write}`, gated `if: needs.detect.outputs.mode == 'propose'`.
So the detect/report path stays `contents: read` and the write scope is unreachable off the propose path — the R7 privilege boundary (plan §9.3), pinned by `tests/test_release_train_workflow_guard.py`.
It runs `util/release_train/propose.py --execute` to open **standard-gated** release-proposal PRs (owner reviews and merges; never auto-merged; touches neither TestPyPI nor PyPI). The optional `packages` dispatch input (whitespace/comma-separated pypi_names; empty = all eligible) restricts which packages are proposed.
Garbage `packages` tokens (Title Case, underscores, path fragments, shell metacharacters) exit **2** with `::error::` in **both** write jobs before python runs (`release-train.yml` propose/ceremony shell; pin open juniper-ml#729 `PackagesInputRehearsalTest`). `--cross-repo` is appended **only** when `APP_TOKEN` is non-empty. Operator: runbook §3.2.
**Cross-repo write identity (Phase 4.1, plan §9.2 / §12 step 4.1).** The propose job mints a GitHub App installation token (`actions/create-github-app-token`, SHA-pinned) scoped to the 8 publishing repos and passes `propose.py --cross-repo`, so a sibling package's proposal branches from that repo's `origin/main`, edits its own checkout, pushes with the App token, and opens the PR **in that sibling repo** (the dup-guard runs per-repo).
In-repo meta consumer-pin co-changes (the #661 RK-11 lockstep) apply only to juniper-ml packages; a sibling proposal never edits the meta from a sibling checkout — it emits the §13 propagation edge instead.
**Graceful degradation is mandatory:** the mint step is gated on the repo variable `RELEASE_TRAIN_APP_ID` (owner-provisioned with the `RELEASE_TRAIN_APP_PRIVATE_KEY` secret), and when it is unset the job falls back to the single-repo `GITHUB_TOKEN` and `propose.py` skips sibling packages with a clear reason — the prior in-repo-only behaviour.
The App private-key secret is referenced **only** in the mint step and the minted token **only** in the propose job (both pinned by `tests/test_release_train_workflow_guard.py`); the App token is never a `pypi` environment reviewer (R7).
The cross-repo **ceremony** (`ceremony.py --cross-repo`) keeps the exempt notes-archive PR **central in juniper-ml** (§10.2) while cutting the Release on the owning repo (`gh release create --repo pcalnon/<repo>`); its seam bounds every `--repo` — and the archive lane's two api calls' repo bind — to the 8 publishing repos without widening the verb allowlist.
**Both** write lanes create their commits through the GitHub API (`createCommitOnBranch`, no local commit), so every commit is **GitHub-signed / Verified** and satisfies the ruleset's `required_signatures` rule -> hands-free auto-merge (2026-07-23 ml#707 was the unsigned-commit block that motivated this for `ceremony.py`).
`propose.py` previously made **unsigned** local git commits (`-c commit.gpgsign=false`) so a headless run never tripped the owner's YubiKey config. Once the 2026-08-12 branch-protection normalization added `required_signatures` to all 9 repos, that made every proposal PR unmergeable — an unsigned commit anywhere on the branch blocks the merge and squash does not rescue it (cascor#515; the pre-normalization cascor#497 merged with the identical unsigned commits).
`execute_proposal` and `execute_follow_on` both route through one `_execute_signed_pr` helper, and `propose.py` deliberately carries **no** local-`git` helper so the unsigned path cannot grow back (anti-resurrection pin: `ExecuteCrossRepoGuardTest.test_execute_path_makes_no_local_git_commit`). The API path needs no working tree — checkouts are read-only inputs.

`propose.py` also bumps the `AGENTS.md` **Last Updated** header in the same edit as **Version**, which now satisfies the `agents-md-touch-up.yml` **date check** as authored (the lane verifies the header rather than rewriting the branch — juniper-ml#1099).
Before #1099 that lane pushed its own `[skip ci]` commit when the date was stale; that commit became the PR head, and because it carried `[skip ci]` **no required context ever reported on it**, leaving the proposal permanently BLOCKED with every check stuck at "expected" (the other half of cascor#515). It also raced `Update Lockfile (Dependabot)`, whose push was then rejected. Pre-setting the date remains correct and is now the *only* thing needed.
Both write jobs must configure that headless git identity with `git config --global` (not repo-local) so sibling clones inherit `user.name` / `user.email` / `commit.gpgsign` — a juniper-ml-only identity fails the first sibling commit with `Author identity unknown` (ml#705 / run 30040138774; workflow-guard invariant `(g)` in #718).

**Ceremony mode (Phase 4.3, opt-in).** Dispatching with `mode=ceremony` (or setting `RELEASE_TRAIN_MODE=ceremony`) adds a second write-scoped `ceremony` job — identical `permissions: {contents: write, pull-requests: write}`, gated `if: needs.detect.outputs.mode == 'ceremony'`, with its own App-token mint step — that runs `util/release_train/ceremony.py --execute --monitor-timeout 900` for `BUMPED_NOT_RELEASED` packages.
It opens the central archive PR (branch + single-file commit via the GitHub API -> a **GitHub-signed** commit satisfying `required_signatures`, so the PR auto-merges hands-free), enables `--auto` behind the required guard, cuts the Release on the owning repo, and monitors the publish run to `PENDING_PYPI_APPROVAL`; the PyPI deploy still waits at the owner-gated `pypi` environment (Gate 2). The job renders a ceremony step summary (ceremonies / resume-monitors / HALTs / `PENDING_PYPI_APPROVAL`).
A per-package HALT (plan §8) is a normal green outcome surfaced in the step summary + a dedup issue + Slack (ceremony exit 1 does not fail the run; only exit >= 2 does). The HALT-issue upsert **degrades gracefully** if the App token lacks the Issues permission — a loud log line + a step-summary `halt_issue_failed` flag, never a crash (a `SeamViolation` code bug still propagates; the R7 gh surface is unchanged).
The workflow's R7 boundary — both write jobs' exact perms, the mode gates, off-quiescence, and the App secret referenced mint-only (once per write job) — is pinned by `tests/test_release_train_workflow_guard.py`, which also rehearses the actual mode-resolution shell, the ceremony **and** propose step summaries (`ProposeSummaryRehearsalTest`: `opened:`/`skip:` bucketing + empty-output banner, juniper-ml#730), and the `packages` / `--cross-repo` shell prefix (juniper-ml#729) via the YAML-extraction pattern.

The same guard pins every `<<'PY'` heredoc as balanced (`HeredocBalanceTest`, ml#708) and `compile()`-clean (`HeredocCompileTest`, ml#723) so a broken summary/Slack body cannot turn a successful run red only after the real work finishes.

**Known limitation (degraded no-App path only):** on the fallback path (`RELEASE_TRAIN_APP_ID` unset), a PR opened with the built-in `GITHUB_TOKEN` does **not** trigger CI workflows (GitHub's recursion guard), so a proposal PR shows **no checks** until the owner re-triggers them — close and reopen the PR, or push an empty commit.
When the GitHub App token is minted (the primary Phase 4.1 path) the PR is opened by the App identity and CI runs normally, so the caveat no longer applies; the repo's `can_approve_pull_request_reviews` setting is already enabled.

With the `SLACK_WEBHOOK_URL` repo secret present (owner-provisioned incoming webhook; Q-CHANNEL), each run also posts a compact summary — classification counts, packages needing action, run URL — to the Juniper Slack channel. Strictly non-blocking: a missing secret skips the step, and a post failure never fails the run.

### Claude Code Action (`claude.yml`)

Triggered by issue/PR comments and events mentioning @claude. Uses `anthropics/claude-code-action` for automated issue/PR assistance.

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
