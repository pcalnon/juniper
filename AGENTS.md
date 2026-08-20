# CLAUDE.md

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-20

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
- **WS tunables are declared, not implicit** — `websocket/tunables.py` holds all eleven settings fields the WebSocket handlers read, each with its default and a `security` flag. Six are security controls: the Origin allowlist, the control-endpoint kill switch, the control rate limit, and the three handshake-cooldown parameters. Call sites pass only a name; the default lives in the registry.
  - The `getattr`-based decoupling is deliberate and kept — the shared package still never imports a consuming service's settings class. What changes is that a miss which looks like a misspelling now logs a WARNING naming both spellings, instead of silently reverting a security control to a library default forever (`ws_control_rate_limit_per_second` vs `..._per_sec`).
  - `resolve()` on an undeclared name raises rather than defaulting; `audit(settings)` is the boot-time counterpart, reporting defaulted security controls and suspected typos. Closes APD-SVCCORE-003 / -010. `tests/test_ws_tunables.py` pins the pre-refactor defaults byte-for-byte and source-scans both handlers so registry and call sites cannot drift.

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
│   ├── test_wait_for_checks.py           # Behavioural: util/wait_for_checks.py required-context CI waiter (hermetic scripted-gh stub; positive-terminal, growing-rollup + observed-anchor negative control, absent-vs-running, hard-error, read-only)
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
│       └── prompt_validator/             # PR 3: verdict.schema.json + verdict.sample.{pass,fail}.json (validator contr
│   # Doc-link validator regression tests moved to juniper-doc-tools/tests/
│   # (Wave 4 of the doc-link migration plan; published under the dedicated
│   #  juniper-doc-tools PyPI package).
│
└── util/                      # Utility scripts and tools
    ├── ad-hoc/                           # Single-use / temporary / unfinished scripts (see ad-hoc/README.md)
    ├── assert_release_tag.bash            # Publish guard (P3): ref must be a TAG, and the tag's version must match the wheel actually built
    ├── open_signed_pr.py                  # Cross-repo: open a PR on any Juniper repo with a GitHub-SIGNED commit (createCommitOnBranch)
    ├── wait_for_checks.py                  # Cross-repo: wait for a PR's REQUIRED status checks (ruleset-anchored) to finish; read-only, exit 0/1/2/3
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
