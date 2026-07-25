# CLAUDE.md

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-07-24

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
python3 -m unittest -v tests/test_reap_pytest_orphans.py
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
python3 -m unittest -v tests/test_workflow_script_paths.py
python3 -m unittest -v tests/test_doc_tools_drift.py
python3 -m unittest -v tests/test_pyproject_extras.py
python3 -m unittest -v tests/test_template_library_drift.py
python3 -m unittest -v tests/test_template_selection.py
python3 -m unittest -v tests/test_template_select_preview.py
python3 -m unittest -v tests/test_template_data_resolver.py
python3 -m unittest -v tests/test_scaffold_template.py
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
bash scripts/test_resume_file_safety.bash
# doc-link validator regression tests live in juniper-doc-tools/tests/
# and run under the dedicated `CI -- juniper-doc-tools` workflow.

# Run pre-commit hooks
pre-commit run --all-files

# Validate documentation links (requires `pip install juniper-doc-tools`
# or `pip install -e juniper-doc-tools/` for editable local development)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy

# Validate documentation links (including cross-repo)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy --cross-repo check
```

## Publishing

Releases are published via GitHub Actions (`.github/workflows/publish.yml`). The workflow is triggered by a GitHub release event and publishes first to TestPyPI (with install verification), then to PyPI. Both environments use trusted publishing (OIDC, no API tokens).

**Release convention (mandatory, all packages).** Every PyPI deploy — the meta-package and every
shared / sub-package — is performed by **cutting a GitHub Release** (never a bare `git push <tag>`),
and the release notes are authored from
[`notes/templates/TEMPLATE_RELEASE_NOTES.md`](notes/templates/TEMPLATE_RELEASE_NOTES.md) and
**archived under `notes/releases/`** (`RELEASE_NOTES_v<version>.md` for the meta-package;
`RELEASE_NOTES_<pkg>_v<version>.md` for a shared / sub-package). For the meta-package the Release
event triggers `publish.yml`; for a tag-triggered shared / sub-package, cutting the Release
**creates** the `juniper-<pkg>-v*` tag, which triggers its `publish-<pkg>.yml`. Full steps:
[`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11](notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md). (This convention drifted
during rapid concurrent refactoring — several sub-packages shipped tag-only — and is being restored.)

The shared `juniper-observability` package is published separately from the same repo (subdirectory `juniper-observability/`) by `.github/workflows/publish-observability.yml`, triggered by tags matching `juniper-observability-v*`.

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
the canonical implementation.

## Shared Observability Helpers

`juniper-observability` (this repo's `juniper-observability/` subdirectory, published as a standalone PyPI package) is the canonical home for cross-service observability primitives — middlewares, the build-info `Info` metric helper, structured-JSON logging, and **idempotent `prometheus_client` collector helpers**. Any new `Counter` / `Gauge` / `Histogram` / `Summary` / `Info` / `Enum` registration in any Juniper service should go through:

- `register_or_reuse(factory, name, *args, **kwargs)` — adopt-existing on duplicate (preserves accumulated samples; **default choice for almost every call site**).
- `register_fresh(factory, name, *args, **kwargs)` — drop-and-recreate (use only when test fixtures or migrations intentionally want different buckets/labels).
- `register_info_or_update(name, description, **info_labels)` — sugar for the `Info` two-step register-then-`.info({...})` pattern.
- `lazy_register_or_reuse(factory, name, *args, **kwargs)` — like `register_or_reuse` but caches the result in a module-private dict; for the lazy-init-with-`None`-sentinel pattern.

Tests touching these collectors should use `juniper_observability.testing.reset_prometheus_registry`. Minimum pin: `juniper-observability>=0.2.0`. See [`notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md`](notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md) for the design rationale and the migration history.

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
│   │   └── task-executor.md     # Round-2: Task subagent -> code changes via PR (worktree isolation; may fan out)
│   └── skills/
│       └── template-agent/SKILL.md  # PR 5: interactive orchestrator Skill (bounded state machine; opus + effort max)
│
├── .github/
│   ├── CODEOWNERS             # Code ownership (@pcalnon)
│   ├── dependabot.yml         # Automated dependency updates (pip + actions)
│   └── workflows/
│       ├── ci.yml             # Main CI pipeline (pre-commit, tests, build, docs, security)
│       ├── publish.yml        # PyPI publishing (TestPyPI + PyPI, OIDC)
│       ├── docs-full-check.yml# Weekly full documentation link validation (cross-repo)
│       ├── security-scan.yml  # Weekly pip-audit security scanning
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
│   ├── test_reap_pytest_orphans.py       # Orphan pytest process reaper tests
│   ├── test_requirements_drift_check.py  # Requirements snapshot drift checker tests
│   ├── test_editable_install_drift_check.py # Editable-install drift checker tests (orphaned / worktree-pinned)
│   ├── test_env_floor_drift_check.py     # Lint/behavioural: util/env_floor_drift_check.py floor-drift (I-2; synthetic dist-info)
│   ├── test_prompt_discovery.py          # Behavioural: util/prompt_discovery/ grounding-bundle (schema + provenance + cold/empty)
│   ├── test_symbol_overlay.py            # Serena symbol overlay (OQ-8) deterministic merge (Serena wins, grep fallback)
│   ├── test_generated_prompt_index.py    # Behavioural: util/generated_prompt_index.py index + safety-gated prune (P4)
│   ├── test_thread_handoff_archive.py    # Drift: archived handoff prompt filenames + top-level note references
│   ├── test_install_agents.py            # Behavioural: util/install_agents.bash ~/.claude mirror (idempotent/reversible/dry-run/no-clobber)
│   ├── test_agent_suite_doctor.py        # Behavioural: util/agent_suite_doctor.py suite health check (dogfood; consumes every layer)
│   ├── test_agent_suite_summary.py       # Behavioural: util/agent_suite_summary.py suite quick-reference (P3)
│   ├── test_workflow_script_paths.py     # Lint: every .github/workflows/*.yml script path exists
│   ├── test_doc_tools_drift.py           # Lint: consumer-repo juniper-doc-tools pins still admit current version (plan §5.1)
│   ├── test_pyproject_extras.py          # Lint: pyproject [project.optional-dependencies] surface matches the contract
│   ├── test_template_library_drift.py    # Lint: custom-agent template library (prompts/agent_templates/) manifest <-> templates
│   ├── test_template_selection.py        # Lint: custom-agent template match_signals selection coherence
│   ├── test_template_select_preview.py   # Behavioural: util/template_select_preview.py offline match_signals selector (P2)
│   ├── test_template_data_resolver.py    # Tests + drift gate: data layer (prompts/agent_templates/data/) + resolver
│   ├── test_scaffold_template.py         # Behavioural: util/scaffold_template.py new-template generator (P5; drift-compliant output)
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
│   ├── test_release_train_registry.py    # Lint + drift gate: util/release_train/registry.yaml (18 packages/8 repos/enums) <-> pyproject resolution (plan §4.1)
│   ├── test_release_train_detect.py      # Behavioural: util/release_train/detect.py detection engine (classifications, substantive-hunk, SemVer, exit codes; hermetic)
│   ├── test_release_train_propose.py     # Behavioural: util/release_train/{propose,notes_render}.py proposal-PR generator (dry-run bump+CHANGELOG move+notes, dup-guard, conflict refusal; hermetic) (plan §5.4)
│   ├── test_release_train_archive_guard.py # Behavioural: util/release_train/archive_guard.py exempt notes-archive structural guard (add-only/path-confined/name-valid/single-purpose; SKIP for non-archive; hermetic) (plan §7.2 / step 3.1)
│   ├── test_release_train_ceremony.py    # Behavioural: util/release_train/ceremony.py exempt-archive + Release ceremony (§8 HALTs, happy-path sequence, dup-guard/idempotent, R7 gh-surface, dry-run; hermetic) (plan §7/§8/§9.3 / step 3.2)
│   └── fixtures/
│       └── prompt_validator/             # PR 3: verdict.schema.json + verdict.sample.{pass,fail}.json (validator contract)
│   # Doc-link validator regression tests moved to juniper-doc-tools/tests/
│   # (Wave 4 of the doc-link migration plan; published under the dedicated
│   #  juniper-doc-tools PyPI package).
│
└── util/                      # Utility scripts and tools
    ├── ad-hoc/                           # Single-use / temporary / unfinished scripts (see ad-hoc/README.md)
    ├── requirements_drift_check.py       # Drift checker for the requirements snapshot (--mode quick)
    ├── editable_install_drift_check.py   # Drift checker for juniper editable installs across conda envs
    ├── env_floor_drift_check.py          # Floor-drift checker: installed juniper-* vs target-repo pyproject floors (I-2)
    ├── release_train/                     # PyPI release-train: registry.yaml (18-package registry) + detect.py (report-only "needs deploy?" engine, Phase 1) + propose.py/notes_render.py (manifest -> proposal-PR content, dry-run, Phase 2.1) + archive_guard.py (exempt notes-archive PR structural guard, Phase 3.1) + ceremony.py (exempt-archive + Release ceremony, dry-run, Phase 3.2)
    ├── prompt_discovery/                  # Custom-agent suite (PR 4): env-discovery probes -> JSON grounding bundle (path-invoked, --repo-root)
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
- `util/reap_pytest_orphans.bash` -- Safely reaps orphaned Juniper pytest multiprocessing children. Supports `JUNIPER_REAP_PROC_ROOT` and `JUNIPER_REAP_KILL_CMD` test hooks for deterministic regression tests.
- Documentation link validator now lives in [`juniper-doc-tools/`](juniper-doc-tools/) and is published to PyPI as `juniper-doc-tools` (Wave 4 of the doc-link migration plan; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`).
- `util/requirements_drift_check.py` -- Drift checker for the requirements snapshot at `notes/requirements/id_assignments.yaml`. Default `--mode quick` validates path resolution + structural line-range integrity for every citation; emits a human report or `--json`. Exit code 1 on any drift. Implements the spec in [the requirements next-steps doc §7](notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection); `--mode full` / `--mode rewrite` are reserved for future work.
- `util/template_data_resolver.py` -- Loader + dotted `resolve()` for the custom-agent suite data layer (`prompts/agent_templates/data/*.yaml`: standing rules, anti-hallucination doctrine, conventions, ecosystem facts, known-misses ledger). Path-invoked (`python util/template_data_resolver.py conventions.handoff_threshold`) or imported; the Template Agent maps these into template slots and RUBRIC R2.5 checks injected conventions against them. Tests: `tests/test_template_data_resolver.py`.
- `util/template_select_preview.py` -- Offline preview of the Template Agent's category selection (P2): given a task string, prints which template the Skill's `match_signals` step would pick (matched keywords + ranked runner-ups). A preview heuristic (keyword-substring scoring; `generic` fallback), not the Skill's exact judgement. `python util/template_select_preview.py "TASK" [--repo-root P] [--json] [--top N]`; exit 0 always. Tests: `tests/test_template_select_preview.py`.
- `util/editable_install_drift_check.py` -- Drift checker for juniper editable installs in the conda environments. Reads each env's `*.dist-info/direct_url.json` directly (robust to broken envs); classifies every `juniper-*` editable as `FRESH` / `WORKTREE_PINNED` (under a `worktrees` path) / `ORPHANED` (missing). `*-DEPRECATED` skipped by default; exit 1 on ORPHANED; `--json`; `--fix` re-points orphans to their canonical repo (`--dry-run` previews).
- `util/env_floor_drift_check.py` -- Floor-drift checker (gap I-2): reads each installed `juniper-*` version from its `*.dist-info/METADATA` and compares to the target repo's `pyproject.toml` floors -> `OK` / `BELOW_FLOOR` / `MISSING` -- the below-floor plain-wheel case the pins/editable checkers miss. Env selection is data-driven (`--site-packages`/`--env`/`ecosystem.yaml`); exit 1 on `BELOW_FLOOR` (`--strict` also `MISSING`); `--json`; structural CI gate. Tests: `tests/test_env_floor_drift_check.py`.
- `util/release_train/` -- PyPI release-train tooling (release-train plan §12). `registry.yaml`: the data-driven 18-package / 8-repo registry (§4.1). `detect.py`: the per-package "needs a PyPI deploy?" engine (§4.2/4.3, Phase 1, report-only) -- PyPI truth vs declared version, tag-matched diff base, `gh compare` (`--local-git` fallback past the 300-file cap), and a substantive-hunk SHIP filter discounting the notes-rename comment/docstring/link class; report-only, exit 0/1/2.
- `util/release_train/propose.py` -- Proposal-PR generator (Phase 2.1, plan §5.4): from `detect.py`'s manifest, for each `UNRELEASED_CHANGES` package builds the standard-gated proposal -- static/dynamic version bump, the CHANGELOG `[Unreleased]`->`[<version>]` move, a `notes_render` notes draft (not archived), the meta AGENTS.md co-change, and `propagation_edges`; dup-guard + `changelog_conflict` refusal via a seam. **`--dry-run` default writes nothing.** Tests: `tests/test_release_train_propose.py`.
- `util/release_train/notes_render.py` -- Template-driven release-notes generator (plan §10.1), imported by `propose.py` and independently invokable: renders a DRAFT from `TEMPLATE_RELEASE_NOTES.md` (or the security template when a `Security` category is present), grouping CHANGELOG `[Unreleased]` bullets by Keep-a-Changelog category, and surfaces the `notes/releases/RELEASE_NOTES_<pkg>_v<version>.md` archive convention (`--print-archive-name`). Tests: `tests/test_release_train_propose.py`.
- `util/release_train/archive_guard.py` -- Structural guard (Phase 3.1, plan §7.2) for the release-train's gate-exempt notes-archive PR. Passes a PR diff (`git diff --name-status`; injected) ONLY if it is **add-only**, **path-confined** to `notes/releases/RELEASE_NOTES_*.md`, **name-valid** (`_v<semver>`, registry `pypi_name`), and **single-purpose**; non-archive PRs `SKIP`, a violation only `FAIL`s the check (R7). Run by `ci.yml`'s PR-only lane. Tests: `tests/test_release_train_archive_guard.py`.
- `util/release_train/ceremony.py` -- Exempt-archive + Release ceremony (Phase 3.2, plan §7/§8/§10) for `BUMPED_NOT_RELEASED` packages: §8 preconditions (each HALTs + dedup issue), notes from the CHANGELOG `[<version>]` section, open the exempt archive PR (signed API commit), enable auto-merge, cut the Release (`--latest=false`; no `--verify-tag`), monitor -> `PENDING_PYPI_APPROVAL`. R7 gh-surface allowlist; idempotent re-entry. **`--dry-run` writes nothing.** Tests: `tests/test_release_train_ceremony.py`.
- `util/prompt_discovery/` -- Discovery helpers for the custom-agent suite (PR 4); path-invoked (`python util/prompt_discovery/cli.py --repo-root <path>`), emits a JSON grounding bundle (closed-world facts + provenance: `head_sha`/`dirty`/`ttl_seconds`/`per_probe_status`) from seven probes (`repo_context`, `test_status`, `file_probe`, `symbol_probe`, `dependency_facts`, `conventions`, `concurrency`). Accepts `--target-repo` (cross-repo alias of `--repo-root`). A discovery failure is a hard stop (exit 2).
- `util/generated_prompt_index.py` -- Indexes the Template Agent's `prompts/generated/` output (P4): lists each prompt parsed by the `PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md` convention, with `--older-than DAYS` + a safety-gated `--prune`/`--archive` (acts only with explicit `--yes`, never under `--dry-run`; `.gitkeep` / non-convention files never touched). The dir is read from `conventions.yaml`. Tests: `tests/test_generated_prompt_index.py`.
- `util/install_agents.bash` -- Mirrors this repo's `.claude/{agents,skills}/*` into `~/.claude` by symlink (design D-6) so the suite is available cross-repo; the project stays source of truth (OQ-6). Idempotent, reversible (`--reverse`), `--dry-run`; `JUNIPER_ML_REPO_ROOT`/`JUNIPER_CLAUDE_HOME` overrides for tests. Never clobbers a non-symlink; `--reverse` removes only owned links. Tests: `tests/test_install_agents.py`.
- `util/scaffold_template.py` -- Generates a new `prompts/agent_templates/<id>.md` (P5): writes the canonical skeleton with well-formed placeholders (so a new template can't drift from the library contract) and **prints** the `manifest.yaml` stanza to paste -- it deliberately does NOT edit the manifest (the human-curated selection contract). Refuses to overwrite. `python util/scaffold_template.py --id ID --title T --class C --keywords k1,k2 [--dry-run]`. Tests: `tests/test_scaffold_template.py`.
- `util/agent_suite_doctor.py` -- Read-only health check for the custom-agent suite (a `planner`-designed dogfood): reports existence + structural validity of every component (agents incl. `opus`/`max`, the Skill, the template library, `RUBRIC.md`, the data layer, the discovery CLI, the `~/.claude` mirror) as `OK`/`WARN`/`FAIL`. `python util/agent_suite_doctor.py [--repo-root P] [--json] [--strict] [--no-discovery]`; exit 0/1/2. Tests: `tests/test_agent_suite_doctor.py`.
- `util/agent_suite_summary.py` -- Quick-reference for the custom-agent suite (P3; the human counterpart to the doctor): lists the agents (name, model/effort, one-line description) and the templates (id, class, when-to-use). `python util/agent_suite_summary.py [--repo-root P] [--agents|--templates] [--json|--markdown]`; read-only, exit 0. Tests: `tests/test_agent_suite_summary.py`.
- `util/ad-hoc/` -- Home for single-use / temporary / unfinished scripts. See `util/ad-hoc/README.md` for file-header conventions and graduation lifecycle. `/tmp/` is prohibited for script source files per the [Script placement](#script-placement-mandatory) rule.
- Dependency-documentation generator now lives in [`juniper-ci-tools/`](juniper-ci-tools/) and is published to PyPI as `juniper-ci-tools` (Wave 4 of the dep-docs migration plan; install with `pip install juniper-ci-tools` and invoke via `juniper-generate-dep-docs`). The legacy `util/generate_dep_docs.sh` was deleted in juniper-ml#298.
- `util/juniper_plant_all.bash` -- Starts all Juniper ecosystem services. `JUNIPER_CASCOR_HOST` defaults to `localhost` and `JUNIPER_CASCOR_PORT` defaults to `8201`; both can be overridden via the environment (e.g. `JUNIPER_CASCOR_HOST=remote.example.com JUNIPER_CASCOR_PORT=8201 util/juniper_plant_all.bash`).
- `util/juniper_chop_all.bash` -- Stops all Juniper ecosystem services
- `util/isolated_stack.bash` -- Brings up / tears down the isolated training-runtime E2E trio (data 8101 dedicated `python3.14` venv, cascor 8202 `JuniperCascor1`, canopy 8051 `JuniperCanopy1` service mode) with the documented env (control-WS origin pair, `JUNIPER_DATA_URL`, `LD_LIBRARY_PATH=`); `--up`/`--down`/`--status`/`--dry-run`, ports 8101/8202/8051 (`JUNIPER_E2E_*` overrides), `--dry-run` starts nothing. See [E2E checklist](notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md).
- `util/get_cascor_*.bash` -- Cascor REST API query utilities (status, metrics, history, network, topology). These helpers read legacy `CASCOR_HOST` and `CASCOR_PORT` environment variables (with `localhost` / `8201` defaults). Do not confuse them with the `JUNIPER_CASCOR_*` variables used by `util/juniper_plant_all.bash`.

### Tests

- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`
- `tests/test_env_repr_safety.py` -- Lint + behaviour gate for the env-repr secret-leak class: forbids raw `os.environ`-derived subprocess `env=` mappings in `tests/` (they leak secrets through pytest `--showlocals`-style frame-local reprs) and proves `tests/redacted_env.py`'s `RedactedEnv` masks its repr while behaving as a normal subprocess env mapping. Includes a synthetic-violation self-test; `patch.dict(os.environ, ...)` is deliberately exempt.
- Doc-link validator regression tests live in [`juniper-doc-tools/tests/`](juniper-doc-tools/tests/) (Wave 4 of the doc-link migration; exercised by the dedicated `CI -- juniper-doc-tools` workflow).
- `tests/test_worktree_cleanup.py` -- Tests for `util/worktree_cleanup.bash` argument parsing, dry-run, and error handling
- `tests/test_worktree_sweep_scripts.py` -- Tests for `util/ad-hoc/worktree_sweep_*.bash`: survey/apply row compatibility, `SAFE`-only removal, and unknown-repo skips
- `tests/test_reap_pytest_orphans.py` -- Tests for `util/reap_pytest_orphans.bash` dry-run, live-parent safety, orphan detection, and isolated kill invocation
- `tests/test_requirements_drift_check.py` -- Tests for `util/requirements_drift_check.py`: structural range validation, BAD_PATH / BAD_RANGE classification, `--ecosystem-root` rewriting, CLI exit codes, JSON output
- `tests/test_editable_install_drift_check.py` -- Tests for `util/editable_install_drift_check.py`: FRESH / WORKTREE_PINNED / ORPHANED classification, `*-DEPRECATED` env exclusion, `--env` filtering, dedup across interpreter trees, CLI exit codes (0/1/2), JSON output, and `--fix --dry-run` canonical-source resolution (synthetic conda-dir fixture; no real pip)
- `tests/test_env_floor_drift_check.py` -- Tests for `util/env_floor_drift_check.py` (I-2): floor parsing (juniper-* `>=` bound; skips non-juniper/floorless/self-ref; dedup-highest), numeric version compare (`0.10.0 > 0.9.0`), OK/BELOW_FLOOR/MISSING classification, exit codes (0/1/2, `--strict`), `--json` -- via a synthetic site-packages fixture (no real pip/conda); also asserts no hardcoded env name. Sole gate (`util/` not lint-gated); real-env scan is manual-verify.
- `tests/test_workflow_script_paths.py` -- Lint test: every `python <path.py>` / `bash <path.bash>` invocation in `.github/workflows/*.yml` must reference a path that exists in the repo. Cross-repo paths (`juniper-X/...`) are skipped as runtime-resolved. Catches the failure class that broke 3 juniper-X CIs on 2026-05-18.
- `tests/test_doc_tools_drift.py` -- Lint test (plan §5.1) for `juniper-doc-tools` pins. Extracts the `juniper-doc-tools>=X,<Y` pin from juniper-ml's own workflows and each cloned consumer repo's `ci.yml`, then asserts the range still admits the current version (read from `juniper-doc-tools/pyproject.toml`). Soft-warns on pins more than 2 minors behind; hard-fails when the upper bound excludes current.
- `tests/test_pyproject_extras.py` -- Lint test pinning the `[project.optional-dependencies]` surface (`clients`, `worker`, `servers`, `tools`, `doc-tools`, `all`). Asserts the exact set of extras, the exact membership of each, that `[all]` aggregates every non-alias extra exactly once, and that `[project].version` is semver-ish. Added pre-0.5.0 after juniper-ml#295 introduced `[servers]` + `[tools]` without regression coverage; any future edit to extras must update the lint contract in the same PR.
  - juniper-ml's own pin check runs every PR; the cross-repo assertion auto-skips when siblings aren't on disk and additionally skips local runs by default. Set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to opt in locally.
- `tests/test_template_library_drift.py` -- Lint test enforcing manifest <-> template consistency for the custom-agent template library (`prompts/agent_templates/`): every registered template exists and every template is registered; each follows the canonical section skeleton in order; every `{{placeholder}}` matches the systematic convention; the `generic` fallback always matches.
  - The **sole gate** for the library because `prompts/**` is excluded from all pre-commit hooks, so it must stay wired into `ci.yml`. Design-of-record §5.4/§9.
- `tests/test_template_selection.py` -- Lint validating `manifest.yaml`'s `match_signals` support deterministic category selection: exactly one always-match fallback (`generic`), every other template has non-empty keyword signals, no two share an identical keyword set, and every `class` is allowed. Companion gate to the library drift test.
- `tests/test_template_select_preview.py` -- Tests for `util/template_select_preview.py` (the offline selection preview, P2): drives the real manifest (so it also guards selection drift) -- a task with a template's keyword selects that template (`failing-tests`), a no-keyword task falls back to `generic`, the ranked candidates exclude the always-match fallback, and the CLI exits 0 with the documented JSON shape.
- `tests/test_template_data_resolver.py` -- Tests + drift gate for the custom-agent suite data layer (PR 6b): the five `prompts/agent_templates/data/*.yaml` files load, `util/template_data_resolver.py`'s `load`/`resolve` (dotted lookup) work, and -- since `prompts/**` is pre-commit-excluded -- this is the sole gate; also asserts `conventions.line_length` matches `.markdownlint.yaml` and the handoff threshold is the current 95-99% (not a stale 80%).
- `tests/test_scaffold_template.py` -- Tests for `util/scaffold_template.py` (P5 generator): the generated template passes the real library-drift helpers (skeleton order + placeholder well-formedness), `--dry-run` writes nothing, refuse-on-collision (exit 1), bad-class / missing-keywords (exit 2), and -- the safety contract -- the tool NEVER edits `manifest.yaml` (prints the stanza).
- `tests/test_prompt_validator_contract.py` -- Static contract test for the `prompt-validator` subagent (`.claude/agents/prompt-validator.md`, PR 3): frontmatter shape (`tools` = exactly `Read, Grep, Glob, Bash`, `model` concretely pinned per OQ-4), every rubric ID it cites exists in `RUBRIC.md` (incl. the `R2.0`/`R3.4` hard gates), and the pinned verdict schema + PASS/FAIL samples in `tests/fixtures/prompt_validator/` match the §5.3 contract. E-3: re-probe block is `<target>`-qualified (not CWD).
- `tests/test_prompt_discovery.py` -- Behavioural tests for `util/prompt_discovery/` (custom-agent suite PR 4): the grounding-bundle schema + provenance envelope emitted by `cli.py`, per-probe graceful degradation, the hard-stop on a non-git root (exit 2), the `test_status` `cold_cache`/empty distinction, plus E-3 `--target-repo` cross-repo grounding. `util/` is not pre-commit-lint-gated (flake8/black scope to `scripts`+`tests`), so this unittest is the gate; imported via the `sys.path.insert` idiom.
- `tests/test_symbol_overlay.py` -- Tests for `util/prompt_discovery/symbol_overlay.py` (the Serena symbol overlay, design OQ-8): the deterministic merge of Skill-resolved Serena facts into a bundle's `symbol_probe` slice -- Serena-resolved wins, grep is the fallback, an unresolvable symbol stays `UNRESOLVED`, the input bundle is not mutated, and `cli.py`'s contract is untouched. Stdlib only; importlib-loaded.
- `tests/test_generated_prompt_index.py` -- Tests for `util/generated_prompt_index.py` (P4): name-convention parsing, `.gitkeep`/malformed ignored, and the destructive-path safety -- `--prune` without `--yes` (or under `--dry-run`) deletes nothing, `--prune --yes` removes only convention-named stale files (never `.gitkeep`/hand-placed), and the generated-dir location is read from `conventions.yaml`.
- `tests/test_thread_handoff_archive.py` -- Drift guard for `prompts/thread-handoff_automated-prompts/`: every archived handoff prompt filename must follow `HANDOFF_YYYY-MM-DD_subject.md` with ASCII subject text, and top-level `notes/*.md` references to archived handoff prompts must resolve to real files. Added after PR #617 standardized old `handoff_subject_YYYY-MM-DD.md` archive names.
- `tests/test_install_agents.py` -- Tests for `util/install_agents.bash` (custom-agent suite PR 6a): drives the `~/.claude` mirror against a synthetic source repo + throwaway target (`JUNIPER_ML_REPO_ROOT`/`JUNIPER_CLAUDE_HOME` overrides) and asserts it is idempotent, reversible (`--reverse`), `--dry-run`-safe, and never clobbers or removes a file it does not own.
- `tests/test_agent_suite_doctor.py` -- Tests for `util/agent_suite_doctor.py` (the suite health-check dogfood utility): the real suite has zero FAIL; synthetic trees missing a component FAIL the matching check (exit 1); `--json` shape; `--no-discovery` skips the subprocess; `--strict` promotes WARN to exit 1; a non-repo `--repo-root` exits 2. Stdlib-only; importlib-loaded.
- `tests/test_agent_suite_summary.py` -- Tests for `util/agent_suite_summary.py` (P3 quick-reference): drives the real suite so every agent and template appears, `--json` round-trips, and `--markdown` rows respect the 512-char line-length convention. Stdlib + PyYAML; importlib-loaded.
- `tests/test_template_agent_skill_lint.py` -- Static lint for the `template-agent` Skill (`.claude/skills/template-agent/SKILL.md`, PR 5): frontmatter (`allowed-tools` includes `Agent`, `model: opus` + `effort: max`, user-only) and that the bounded state machine wires to real artifacts (template library, `RUBRIC.md`, `util/prompt_discovery/cli.py`, the emission dir, the `prompt-validator` subagent). E-3: threads `<target>` to the validator. The Skill-surface gate (pre-commit-excluded except markdownlint).
- `tests/test_service_smoke_skill_lint.py` -- Static lint for the `service-smoke` Skill (`.claude/skills/service-smoke/SKILL.md`, E-1 Stage 1/2): the **Stage-2 boundary** -- a browser MCP (`mcp__playwright`) MUST be declared for the opt-in `--ui` smoke (inverts Stage 1's no-browser rule), `Agent` still forbidden -- plus `opus`+`max`/user-only frontmatter, browser-close teardown, the `--ui`/`/dashboard`/console smoke, `UI_UNHEALTHY_REPORTED`, and bounded waits. Structural-only gate.
- `tests/test_ui_test_author_skill_lint.py` -- Static lint for the `ui-test-author` Skill (E-6): frontmatter (suite `opus`+`max`, user-only, `Write` + a declared browser MCP, NO `Agent`) + that it models canopy's `src/tests/ui/` harness (`dashboard_page` / `@pytest.mark.ui` / the `dbc.Input` wall via `/api/state`), the browser-close teardown, the reviewed-never-auto-merged contract, terminal states, and bounded waits. Structural-only gate; live authoring = manual smoke-verify.
- `tests/test_agents_frontmatter.py` -- Suite-wide frontmatter gate over every `.claude/agents/*.md` (the `prompt-validator` plus the round-2 `planner` / `auditor` / `task-executor`): `name` equals the filename, the `description` is substantive, `tools` are declared, the body is non-trivial, and the owner-directed defaults `model: opus` + `effort: max` hold -- so a new agent cannot drift from the standing defaults. The shared invariant complementing `test_prompt_validator_contract.py`.
- `tests/test_ci_tools_drift.py` -- Lint test (dep-docs plan §5.1) for `juniper-ci-tools` pins. Mirrors `test_doc_tools_drift.py`: walks juniper-ml's own workflows (`ci.yml`, `lockfile-update.yml`, `docs-full-check.yml`) plus each cloned consumer repo's `ci.yml`, extracts the `juniper-ci-tools>=X,<Y` pin, and asserts the range still admits the current version (read from `juniper-ci-tools/pyproject.toml`). Same skip semantics and `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` override as the doc-tools sibling.
- `tests/test_coverage_gap_mapper_drift.py` -- Dogfood/drift gate (E-4 + C-0) for the `juniper-coverage-gap-map` console script in `juniper-ci-tools` (modeled on `test_ci_tools_drift.py`). STRUCTURAL: script registered, `_version.py` matches version, pins admit it, `--enforce`/`--fail-under-*`/`--omit` wired. END-TO-END (C-0): `--enforce` exits 1 on a gap / 0 clean over a synthetic `coverage.json`. Full matrix in `juniper-ci-tools/tests/`.
- `tests/test_env_drift_check_drift.py` -- Structural drift gate for the `juniper-env-drift-check` console script (env floor-drift guard, test-suite audit §10.1).
  - Mirrors `test_coverage_gap_mapper_drift.py`: asserts the entry point is registered (`juniper_ci_tools.cli_env_drift_check:main`), both module halves ship, version/pin coherence, **plus a class guard** that *every* `juniper_ci_tools/cli*.py` has a `[project.scripts]` entry.
  - Added in `juniper-ci-tools` 0.5.1 after #580 silently dropped the 0.5.0 entry point -- the always-on assertion the `python -m` behavioural dogfood (`tests/test_env_drift_check.py`) lacked.
- `tests/test_release_train_registry.py` -- Structural lint + registry<->pyproject drift gate for `util/release_train/registry.yaml` (plan §4.1): always-on checks (18 packages, 8 repos incl. `juniper-recurrence`, required fields, enums, the dynamic-version set, archive-name convention, `depends_on`) plus resolution -- the 7 in-repo juniper-ml packages unconditionally (forward + reverse), the 11 cross-repo entries via the `test_doc_tools_drift.py` sibling auto-skip.
- `tests/test_release_train_detect.py` -- Hermetic tests for `util/release_train/detect.py` (plan §4.2/4.3); no network / gh / pip (sources injected). Covers each classification, static/dynamic version reads, tag resolution, the substantive-hunk filter (discount comment/docstring/link; catch real code), path-scoping (subdir vs cascor repo-minus-subpkgs), CHANGELOG conflict surfacing, SemVer, manifest JSON shape, and exit codes 0/1/2. `util/` is not lint-gated, so this unittest is the gate.
- `tests/test_release_train_propose.py` -- Hermetic tests for `util/release_train/propose.py` + `notes_render.py` (Phase 2.1); no network / gh / repo writes. Covers a dry-run proposal for a static- and a dynamic-version package, the CHANGELOG move, notes render vs the template skeleton + the `RELEASE_NOTES_<pkg>_v<version>.md` convention, dup-guard suppression, the `changelog_conflict` refusal, and that a dry-run writes nothing. `util/` is not lint-gated, so this is the gate.
- `tests/test_release_train_archive_guard.py` -- Hermetic tests for `archive_guard.py` (Phase 3.1, §7.2); no network/git/gh. Drives the four-rule classifier with synthetic `git diff --name-status` sets + the CLI (`--name-status-file`) against the real `registry.yaml`: a pure notes-add PASSES, a non-archive PR SKIPs, and modify/delete/out-of-path/bad-name/mixed diffs each FAIL; plus filename convention, parsing, exit codes 0/1/2. The gate for `util/`.
- `tests/test_release_train_ceremony.py` -- Hermetic tests for `ceremony.py` (Phase 3.2, plan §7/§8/§9.3); no network/gh/git/writes. Covers every §8 precondition HALT (main-CI / anomaly / missing-CHANGELOG / TestPyPI-verify), the happy-path exact action sequence, dup-guard/idempotent re-entry, the R7 gh-surface invariant (live seam issues only the allowlisted verbs + the 2 archive api calls -- `git/refs` POST + `createCommitOnBranch`), and a dry-run leaving `git status` clean. The gate for `util/`.
- `tests/test_agents_md_version_drift.py` -- Lint test pinning `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s `[project].version`. Added after juniper-ml#295 bumped pyproject 0.4.1→0.5.0 but left AGENTS.md at 0.4.0 for ~6 days (fixed in juniper-ml#304); this lint makes the drift impossible to ship. Intentionally portable: auto-locates the repo root, so the module can be dropped into any Juniper repo's `tests/` (skips loudly if AGENTS.md has no canonical header).
- `tests/test_agents_md_header_schema.py` -- Lint pinning `AGENTS.md`'s canonical header schema. Six required fields in this relative order: `**Project**`, `**Repository**`, `**Author**`, `**License**`, `**Version**`, `**Last Updated**`. Extras (e.g. `**Python**:`) may be interleaved freely. Validates each value non-empty and `**Last Updated**` is `YYYY-MM-DD`. Currency of the date is enforced by `.github/workflows/agents-md-touch-up.yml`. Portable (self-locating).
- `tests/test_agents_md_tree_drift.py` -- Lint (gap G-3) asserting every tracked non-hidden top-level dir (`git ls-tree`; the `ls -d */` surface) appears as a node in `AGENTS.md`'s fenced Repository-Structure tree, catching the indented-tree omission the grep-based `test_agent_suite_path_drift.py` cannot (stale `templates/`, missing `conf/`/`papers/` + 6 sub-package dirs). Portable; a synthetic negative case proves it bites.
- `tests/test_isolated_stack_script.py` -- Contract tests for `util/isolated_stack.bash` (plan unit E1): `bash -n` syntax, launch-line text assertions (dedicated-venv install, `python -m juniper_data`, `uvicorn api.app:create_app --factory`, canonical canopy env vars, the control-WS origin/allowlist pair), and hermetic `--dry-run` behavioural checks (prints commands with ports expanded, touches nothing; misuse exits 2). Wired into `ci.yml` beside the `test_juniper_{plant,chop}_all.py` launcher tests.
- `scripts/test.bash` -- Manual end-to-end harness for session create/resume launcher flows
- `scripts/test_resume_file_safety.bash` -- Regression script ensuring invalid `--resume <file.txt>` input does not delete the source file

### CI/CD Workflows

- `.github/workflows/ci.yml` -- Main CI pipeline: pre-commit hooks, unit tests, the release-train archive-guard lane (PR-only), package build, doc validation, security audit, dependency docs
- `.github/workflows/publish.yml` -- PyPI publishing: TestPyPI with install verification, then PyPI (OIDC trusted publishing)
- `.github/workflows/docs-full-check.yml` -- Weekly full documentation link validation including cross-repo checks
- `.github/workflows/security-scan.yml` -- Weekly pip-audit dependency vulnerability scanning
- `.github/workflows/release-train.yml` -- Daily (13:00 UTC) PyPI release-train orchestrator.
  - The `detect` job (report path) runs `util/release_train/detect.py` over the 18-package registry and renders a step-summary table; it never writes.
  - Two opt-in write-scoped lanes gate on the resolved mode: `propose` (Phase 2.2/4.1 — standard-gated proposal PRs) and `ceremony` (Phase 4.3 — exempt archive PR + Release cut → owner-gated `pypi` Gate 2).
  - Mode switch / rollback: repo variable `RELEASE_TRAIN_MODE` (`off`|`report`|`propose`|`ceremony`, default `report`) + a dispatch `mode` override; `off` quiesces entirely.
  - Operator guide: `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`.
- `.github/workflows/claude.yml` -- Claude Code action for issue/PR automation (@claude mentions)
- `.github/workflows/agents-md-touch-up.yml` -- Auto-bumps `AGENTS.md`'s `**Last Updated**:` field to today's UTC date on every PR push that touches `AGENTS.md`. Idempotent (no-op when the date is already current); commits with `github-actions[bot]` authorship and `[skip ci]` so the bump itself does not re-trigger workflows. Companion to `tests/test_agents_md_header_schema.py`.

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

1. **pre-commit** -- Runs all pre-commit hooks (flake8, bandit, shellcheck, yamllint, markdownlint)
2. **tests** -- Python unittest (`test_wake_the_claude.py`, `test_workflow_script_paths.py`, etc.) and bash regression tests
3. **build** -- Package build, twine validation, extras metadata verification
4. **docs** -- Documentation link validation (`--cross-repo skip`)
5. **security** -- pip-audit for dependency vulnerabilities
6. **dependency-docs** -- Generates dependency documentation via the `juniper-generate-dep-docs` console script from the PyPI-published `juniper-ci-tools>=0.1.0,<0.2.0` package (replaces the legacy `util/generate_dep_docs.sh` deleted in juniper-ml#298)
7. **release-train-archive-guard** (PR-only) -- Runs `util/release_train/archive_guard.py` over the PR's changed files to prove the exempt notes-archive PR is add-only / path-confined / name-valid / single-purpose (plan §7.2 / step 3.1). SKIPs (passes) for any PR not touching `notes/releases/`, so it never blocks a normal PR; a violation fails only this check (the PR falls back to the standard owner gate). Standalone so the owner can later mark it a **required** status check (step 3.3).
8. **required-checks** -- Quality gate enforcing all checks must pass

### Publishing (`publish.yml`)

Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first (with install verification), then PyPI.

### Documentation Full Check (`docs-full-check.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch. Clones all Juniper ecosystem repos and runs full cross-repo documentation link validation.

### Security Scan (`security-scan.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch. Runs `pip-audit --strict --desc on` for dependency vulnerability scanning.

### Release Train (`release-train.yml`)

Daily schedule (13:00 UTC = 08:00 America/Chicago CDT; Q-CADENCE) and manual dispatch. Phase 1 report-only detection for the PyPI release train ([plan](notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 1.3): full-history clones of the 7 sibling package repos, then `util/release_train/detect.py --json` classifies all 18 registry packages; the run publishes the release-manifest artifact plus a step-summary table.

Detector exit 1 (action needed) is a normal green outcome; only exit >= 2 (hard source error) fails the run. The `detect` job writes nothing: no PRs, no Releases, no (Test)PyPI interaction. The `RELEASE_TRAIN_MODE` repo variable (`off`|`report`|`propose`|`ceremony`, default `report`; an unknown value warns and degrades to `report`) plus the `mode` dispatch input is the instant kill switch and mode selector (precedence: dispatch input > repo variable > `report`).
The operator's guide to the four modes, the two owner gates, the §8 HALT catalog, and rollback is [`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md).

**Propose mode (Phase 2.2, opt-in).** Dispatching with `mode=propose` (or setting `RELEASE_TRAIN_MODE=propose`) adds a second, **write-scoped** `propose` job — `permissions: {contents: write, pull-requests: write}`, gated `if: needs.detect.outputs.mode == 'propose'`.
So the detect/report path stays `contents: read` and the write scope is unreachable off the propose path — the R7 privilege boundary (plan §9.3), pinned by `tests/test_release_train_workflow_guard.py`.
It runs `util/release_train/propose.py --execute` to open **standard-gated** release-proposal PRs (owner reviews and merges; never auto-merged; touches neither TestPyPI nor PyPI). The optional `packages` dispatch input (whitespace/comma-separated pypi_names; empty = all eligible) restricts which packages are proposed.
**Cross-repo write identity (Phase 4.1, plan §9.2 / §12 step 4.1).** The propose job mints a GitHub App installation token (`actions/create-github-app-token`, SHA-pinned) scoped to the 8 publishing repos and passes `propose.py --cross-repo`, so a sibling package's proposal branches from that repo's `origin/main`, edits its own checkout, pushes with the App token, and opens the PR **in that sibling repo** (the dup-guard runs per-repo).
In-repo meta consumer-pin co-changes (the #661 RK-11 lockstep) apply only to juniper-ml packages; a sibling proposal never edits the meta from a sibling checkout — it emits the §13 propagation edge instead.
**Graceful degradation is mandatory:** the mint step is gated on the repo variable `RELEASE_TRAIN_APP_ID` (owner-provisioned with the `RELEASE_TRAIN_APP_PRIVATE_KEY` secret), and when it is unset the job falls back to the single-repo `GITHUB_TOKEN` and `propose.py` skips sibling packages with a clear reason — the prior in-repo-only behaviour.
The App private-key secret is referenced **only** in the mint step and the minted token **only** in the propose job (both pinned by `tests/test_release_train_workflow_guard.py`); the App token is never a `pypi` environment reviewer (R7).
The cross-repo **ceremony** (`ceremony.py --cross-repo`) keeps the exempt notes-archive PR **central in juniper-ml** (§10.2) while cutting the Release on the owning repo (`gh release create --repo pcalnon/<repo>`); its seam bounds every `--repo` — and the archive lane's two api calls' repo bind — to the 8 publishing repos without widening the verb allowlist.
`propose.py`'s proposal commits are unsigned local git commits (`git config commit.gpgsign false` + `-c commit.gpgsign=false`) so the headless run never trips the owner's YubiKey signing config. `ceremony.py`'s exempt-archive commit is instead created via the GitHub API (`createCommitOnBranch`, no local commit), so it is **GitHub-signed / Verified** and the PR satisfies the ruleset's `required_signatures` rule -> hands-free auto-merge (2026-07-23 ml#707 was the unsigned-commit block that motivated this).

**Ceremony mode (Phase 4.3, opt-in).** Dispatching with `mode=ceremony` (or setting `RELEASE_TRAIN_MODE=ceremony`) adds a second write-scoped `ceremony` job — identical `permissions: {contents: write, pull-requests: write}`, gated `if: needs.detect.outputs.mode == 'ceremony'`, with its own App-token mint step — that runs `util/release_train/ceremony.py --execute --monitor-timeout 900` for `BUMPED_NOT_RELEASED` packages.
It opens the central archive PR (branch + single-file commit via the GitHub API -> a **GitHub-signed** commit satisfying `required_signatures`, so the PR auto-merges hands-free), enables `--auto` behind the required guard, cuts the Release on the owning repo, and monitors the publish run to `PENDING_PYPI_APPROVAL`; the PyPI deploy still waits at the owner-gated `pypi` environment (Gate 2). The job renders a ceremony step summary (ceremonies / resume-monitors / HALTs / `PENDING_PYPI_APPROVAL`).
A per-package HALT (plan §8) is a normal green outcome surfaced in the step summary + a dedup issue + Slack (ceremony exit 1 does not fail the run; only exit >= 2 does). The HALT-issue upsert **degrades gracefully** if the App token lacks the Issues permission — a loud log line + a step-summary `halt_issue_failed` flag, never a crash (a `SeamViolation` code bug still propagates; the R7 gh surface is unchanged).
The workflow's R7 boundary — both write jobs' exact perms, the mode gates, off-quiescence, and the App secret referenced mint-only (once per write job) — is pinned by `tests/test_release_train_workflow_guard.py`, which also rehearses the actual mode-resolution shell and the ceremony summary via the YAML-extraction pattern.

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
| `recurrence` | `juniper-recurrence-model>=0.1.5,<0.2.0`, `juniper-recurrence>=0.2.0,<0.3.0`, `juniper-recurrence-client>=0.2.0,<0.3.0`                                                                                      |
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
