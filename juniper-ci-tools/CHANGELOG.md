<!-- markdownlint-disable -->

# Changelog

All notable changes to `juniper-ci-tools` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Two sequence-safety ref-diff screens migrated from the two hand-copied inline
  `util/sequence_safety/` trees (juniper-ml + juniper-cascor) into this package as
  the single, PyPI-distributed source of truth (Wave 0 of the sequence-safety
  ecosystem rollout, plan
  `notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`):
  - `juniper_ci_tools.symbol_loss_check` + `juniper-symbol-loss-check` console
    script — AST symbol-loss screen (gate G1 / G3): FAIL on a silently deleted
    (LOST), gutted-past-threshold (WEAKENED), or duplicated (DUPLICATED)
    def/class/method (or bash function) between BASE and HEAD, with
    qualified-name / body-similarity relocation downgrade, the
    `@property`/`@x.setter` accessor-pair guard (`_accessor_suffix`), and an
    `Allow-Symbol-Loss:` commit-trailer waiver (a `*` wildcard is rejected).
  - `juniper_ci_tools.docs_additions_check` + `juniper-docs-additions-check`
    console script — markdown deletion-magnitude screen (gate G2 / G3): FAIL on a
    deleted heading or a run of `>= --min-run` (default 5) consecutive deleted
    lines, WARN on small in-place swaps, with an `Allow-Docs-Rewrite:`
    commit-trailer waiver. `--min-run` is tunable.
- `--scope GLOB` — a new, repeatable POSIX-path-glob argument on both screens
  (owner-decided scope-delivery design; plan D2). With no `--scope`, each screen
  reproduces its historical hard-coded predicate **verbatim** (symbol:
  `tests/*.py` + `util/**`; docs: `AGENTS.md` + `docs/**` + `notes/**`), so a
  default run is byte-identical to the pre-migration util scripts; a caller may
  instead scope a different surface (e.g. `--scope 'src/**/*.py'`). A tested
  3.11-floor-safe `_match_scope` implements explicit `**` recursion (no
  `PurePath.full_match`, which is 3.13+). `--files` still bypasses scope entirely.
- Both screens ship the logic module + a thin `cli_*.py` argparse wrapper per the
  house pattern; the `cli*.py` → `[project.scripts]` class guard covers both new
  console scripts automatically.

## [0.7.1] - 2026-07-28

### Fixed

- `juniper_ci_tools/_version.py` `__version__` healed `0.6.0` -> `0.7.0` (the ml#701 stale-dunder class, first live instance; healed in juniper-ml#684). The 0.7.0 wheel on PyPI carries correct metadata but its `__version__` dunder reports `0.6.0`; this patch release ships the corrected dunder. The release-train now bumps a static package's `_version.py` in lockstep with `pyproject.toml` (juniper-ml#710), so the class cannot recur.

## [0.7.0] - 2026-07-19

### Changed

- Default header-template filenames for `juniper-generate-dep-docs` renamed to
  track the 2026-07-04 notes/ naming convention: `--pip-header` now defaults to
  `JUNIPER_2026-03-11_JUNIPER-ML_PIP-DEPENDENCY-FILE-HEADER.md` (was
  `PIP_DEPENDENCY_FILE_HEADER.md`) and `--conda-header` to
  `JUNIPER_2026-03-15_JUNIPER-ML_CONDA-DEPENDENCY-FILE-HEADER.md` (was
  `CONDA_DEPENDENCY_FILE_HEADER.md`); the matching `generate_dep_docs()`
  `pip_header_name` / `conda_header_name` parameters default to the same new
  names. This keeps a default (no-flag) invocation resolving the header
  template in `--notes-dir` after the notes/ files were renamed (juniper-ml's
  own `ci.yml`, `lockfile-update.yml`, and `docs-full-check.yml` all invoke the
  console script without the header flags); callers that pass the header
  filenames explicitly are unaffected.

## [0.6.0] -- 2026-06-30

Adds an **opt-in enforcing mode** to `juniper-coverage-gap-map` (non-breaking:
the advisory exit-0-always behavior remains the default; no other console
script is affected). This is work-unit **C-0** of the per-file coverage rollout
(`notes/JUNIPER_2026-06-30_JUNIPER-ECOSYSTEM_PER-FILE-COVERAGE-ROLLOUT-SCOPING.md`).

### Added

- `juniper-coverage-gap-map --enforce` — opt-in blocking gate. When set, the
  CLI exits `1` if, after `--omit` exclusions, **any** source file's
  **statement** coverage is below `--fail-under-file` (default `90`) **or**
  **any** sub-module's **pooled** (statement-weighted) coverage is below
  `--fail-under-submodule` (default `95`); it exits `0` when clean and lists
  every offending file and sub-module (no silent truncation). Without
  `--enforce` the output and exit code are unchanged (advisory, exit 0 always).
- `--fail-under-file` / `--fail-under-submodule` — enforcing thresholds,
  independent of the advisory `--file-threshold` / `--submodule-bar` display
  cuts.
- `--omit GLOB` (repeatable) — `fnmatch` exclusion applied to the parsed
  `coverage.json` **before** aggregation and gating (the report and the gate
  both honor it), so the tool is the single source of truth for what counts
  (it does not rely on coverage's own `[report] omit`). For thin `__main__.py`
  / CLI shims etc. per the rollout's excluded-files policy.
- `FileCoverage.statement_percent` (property) — statement-only coverage
  (`covered_statements / num_statements`); the enforcing per-file basis,
  distinct from the branch-inclusive advisory `percent_covered` display. Also
  surfaced in the `--json` per-file objects.
- `SubmoduleCoverage.below_pooled_bar(bar)` and
  `CoverageReport.files_below_statement_threshold(threshold)` /
  `CoverageReport.submodules_below_pooled_bar(bar)` — the enforcing query
  methods (statement / pooled bases), alongside the unchanged advisory
  `below_bar` / `files_below_threshold` / `submodules_below_bar`.
- `parse_coverage_json` / `load_coverage_json` / `run_coverage` gained an
  `omit=` parameter (forwarded from the CLI's `--omit`).
- New enforcing-mode tests in `tests/test_coverage_gap_mapper.py` (clean→0,
  per-file statement gap→1, sub-module pooled gap→1, `--omit` exclusion,
  advisory-default→0, and the two basis distinctions: branch<90/statement≥90
  PASSES, mean≥95/pooled<95 FAILS). Both changed modules stay at 100 % line
  coverage; the suite's `--cov-fail-under=85` gate stays green.

### Rationale (the two enforcing bases)

The enforcing gate uses different bases than the advisory display so the gate
is apples-to-apples across units regardless of each unit's branch setting:
per-file gates on **statement** coverage (not the branch-inclusive
`percent_covered` a `branch = true` repo reports), and per-sub-module gates on
the **pooled** statement-weighted figure (not the mean-of-files average) — the
two diverge for small files and can flip outcomes.

### Migration context

Additive minor bump. juniper-ml's own workflow pins (`ci.yml`,
`lockfile-update.yml`, `docs-full-check.yml`) are widened from `<0.6.0` to
`<0.7.0` in the same PR to admit 0.6.0; the dogfood gate
`juniper-ml tests/test_coverage_gap_mapper_drift.py` gains a structural check
(the `--enforce` flag is wired) and an end-to-end synthetic-`coverage.json`
invocation of the shipped entry point. **No `--enforce` invocation is turned on
as a blocking gate on any unit's CI yet** — that is work-unit C-1+.

## [0.5.1] -- 2026-06-29

### Fixed

- Restored the `juniper-env-drift-check` console-script entry point in
  `[project.scripts]` (and the package description suffix), inadvertently
  dropped in 0.5.0 by a semantic merge conflict between #579 and #580 — the
  0.5.0 wheel shipped the `env_drift_check` module but not the
  `juniper-env-drift-check` script (exit 127; reachable only via
  `python -m juniper_ci_tools.cli_env_drift_check`).

### Added

- `tests/test_env_drift_check_drift.py` (wired into the always-on pytest job) —
  a structural drift gate with a **class guard** that **every**
  `juniper_ci_tools/cli*.py` module has a corresponding `[project.scripts]`
  entry, so a future concurrent-merge clobber that drops any tool's console
  script fails loudly in CI rather than silently at publish.

## [0.5.0] -- 2026-06-28

Adds the advisory per-file coverage-gap mapper as a fifth console script
(non-breaking; existing `juniper-generate-dep-docs`,
`juniper-lint-workflow-paths`, `juniper-lint-agents-md-version`, and
`juniper-lint-agents-md-header` callers are unaffected).

### Added

- `juniper_ci_tools.coverage_gap_mapper` — Python library that parses a
  `coverage json` (coverage.py / pytest-cov `--cov-report=json`) and emits
  three views: (a) the per-file coverage distribution (a histogram of file
  percentages), (b) the list of files below a threshold (default 90 %), and
  (c) each sub-module's average coverage vs a bar (default 95 %). A
  *sub-module* is the directory a file lives in. Public API:
  `FileCoverage`, `SubmoduleCoverage`, `CoverageReport`,
  `parse_coverage_json`, `load_coverage_json`, `run_coverage`,
  `package_cov_pytest_args`, `write_include_coverage_config`.
- `juniper-coverage-gap-map` console script (plus the
  `python -m juniper_ci_tools.cli_coverage_gap_mapper` module form). Supports
  **both** inputs: `--coverage-json PATH` parses a pre-generated report (the
  primary, deterministic path), and `--repo-root . --package PKG
  --test-command "..."` runs the repo's real test command under coverage
  first. Flags: `--include` (report-scoping glob, repeatable),
  `--file-threshold`, `--submodule-bar`, `--json`, `--version`.
- **Advisory-first posture (exit-code contract):** the CLI exits `0` whenever
  it produces a report — **always**, regardless of how many files are below
  the threshold or sub-modules are under the bar. It reports; it never fails a
  build on coverage findings. Exit `2` is reserved for structural / usage
  errors (no input, an unreadable or malformed `coverage.json`, a dotted
  `--package`). Promotion to a blocking per-file gate is a separate, per-repo,
  owner-signed decision.
- **numpy-2.x dotted-`--cov` shim (documented):** `package_cov_pytest_args`
  builds coverage invocations with the **package-form** `--cov=<package>` and
  scopes any narrowing through a `[report] include=` config written by
  `write_include_coverage_config` — never the dotted `--cov=pkg.submodule`
  form, which trips numpy 2.x's "cannot load module more than once per
  process" guard at pytest-cov startup (hit 2026-06-25, juniper-recurrence
  #70). The helper refuses a dotted package argument outright.
- 28 new tests under `tests/test_coverage_gap_mapper.py` driving synthetic
  `coverage.json` fixtures (no real coverage run): the per-file distribution,
  the strict `<90` list, the sub-module mean-vs-bar classification,
  exit-0-always, the full CLI exit-code matrix, JSON output shape, the
  package-form shim (including dotted-rejection), and the run-coverage path
  via a monkeypatched subprocess.

### Migration context

Hosts enhancement **E-4** of the juniper-ml custom-agent-suite enhancement
plan (`notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md`
§6.7, Phase-2 PR-6). Addresses the systemic gap surfaced by the 2026-06-26
ecosystem test-suite audit: no per-file coverage gate exists anywhere across
the Juniper repos. juniper-ml's own workflow pins (`ci.yml`,
`lockfile-update.yml`, `docs-full-check.yml`) are widened to admit 0.5.0 in
the same PR; the dogfood gate is `juniper-ml tests/test_coverage_gap_mapper_drift.py`.

## [0.4.0] -- 2026-05-22

Adds the AGENTS.md header-schema lint as a fourth console script
(non-breaking; existing `juniper-generate-dep-docs`,
`juniper-lint-workflow-paths`, and `juniper-lint-agents-md-version`
callers are unaffected).

### Added

- `juniper_ci_tools.lint_agents_md_header` — Python library that
  validates a repo's `AGENTS.md` header bullet block against the
  canonical six-field schema (`**Project**`, `**Repository**`,
  `**Author**`, `**License**`, `**Version**`, `**Last Updated**` in
  that relative order; each non-empty; `**Last Updated**` formatted
  as `YYYY-MM-DD`). Extra fields (e.g. `**Python**:`) are permitted
  and may be interleaved freely.
- `juniper-lint-agents-md-header` console script. Auto-discovers the
  repo root by walking up looking for `AGENTS.md` next to `.github/`
  (unlike the version-drift sibling, no `pyproject.toml` is
  required, so the lint applies to `juniper-deploy` as well).
  Supports `--repo-root`, `--exit-zero`, `--json`, `--version`. Exit
  codes: 0 (conformant), 1 (schema drift), 2 (structural error:
  missing AGENTS.md, repo root not found).
- Public API additions: `REQUIRED_FIELDS`,
  `AgentsMdHeaderLintResult`, `RepoRootNotFoundError`,
  `extract_header_bullets`, `find_agents_md_header_repo_root`,
  `lint_agents_md_header`.
- 24 new tests under `tests/test_lint_agents_md_header.py` covering
  walk-up discovery, header termination at `---` / `## `, missing /
  empty / mis-ordered required fields, freely-interleaved extras,
  bad `Last Updated` format, missing `AGENTS.md`, walk-up
  auto-discovery, and the full CLI exit-code matrix (including JSON
  output on success and drift).

### Migration context

This release is Phase 4 (per
`juniper-ml notes/JUNIPER_2026-05-22_JUNIPER-ECOSYSTEM_AGENTS-MD-HEADER-STANDARDIZATION-PLAN.md`)
of the AGENTS.md header standardization initiative kicked off in
juniper-ml#316. The canonical inline lint at
`juniper-ml tests/test_agents_md_header_schema.py` and the auto-bump
workflow at `juniper-ml .github/workflows/agents-md-touch-up.yml`
shipped first; this release packages the lint logic for ecosystem
fanout. Subsequent PRs in each sibling repo will bump the
`juniper-ci-tools>=...,<X.Y.Z` pin range to admit 0.4.0, adopt the
`juniper-lint-agents-md-header` invocation in `ci.yml`, copy the
`agents-md-touch-up.yml` workflow file, and bump `**Last Updated**`
to today.

## [0.3.0] -- 2026-05-21

Adds the AGENTS.md version-drift lint as a third console script
(non-breaking; existing `juniper-generate-dep-docs` and
`juniper-lint-workflow-paths` callers are unaffected).

### Added

- `juniper_ci_tools.lint_agents_md_version` — Python library that
  reads a repo's `AGENTS.md` `**Version**:` header and compares it to
  `pyproject.toml`'s `[project].version`. Catches the same drift class
  that motivated `juniper-ml#304` (pyproject 0.4.1 → 0.5.0 shipped
  while AGENTS.md stayed at 0.4.0 for 6 days).
- `juniper-lint-agents-md-version` console script. Auto-discovers the
  repo root by walking up looking for both `pyproject.toml` and
  `AGENTS.md`; supports `--repo-root`, `--exit-zero`, `--json`,
  `--version`. Exit codes: 0 (in sync OR opted out by omitting the
  header), 1 (drift), 2 (structural error: missing file, multiple
  headers, missing `[project].version` key).
- Public API additions: `AgentsMdLintResult`,
  `MultipleVersionHeadersError`, `RepoRootNotFoundError`,
  `find_agents_md_repo_root`, `lint_agents_md_version`.
- 18 new tests under `tests/test_lint_agents_md_version.py` covering
  in-sync detection, drift detection, opt-out (no header), multiple
  headers, missing files, missing pyproject `[project].version`,
  walk-up auto-discovery, full CLI exit-code matrix, and JSON output.

### Migration context

Replaces the byte-identical inline copies of
`util/test_agents_md_version_drift.py` that exist across 6 consumer
repos (juniper-canopy, juniper-cascor, juniper-cascor-client,
juniper-cascor-worker, juniper-data, juniper-data-client) plus
juniper-ml's `tests/test_agents_md_version_drift.py`. A follow-up
consumer-adoption PR series will swap the inline copies for
`pip install "juniper-ci-tools>=0.3.0,<0.4.0"` +
`juniper-lint-agents-md-version`.

## [0.2.0] -- 2026-05-21

Adds the workflow-script-path lint as a second console script
(non-breaking; existing `juniper-generate-dep-docs` callers are
unaffected).

### Added

- `juniper_ci_tools.lint_workflow_paths` — Python library that walks
  every `*.yml` / `*.yaml` file under a repo's `.github/workflows/`
  and validates that every `python <path.py>` / `bash <path.{sh,bash}>`
  invocation references a file that exists on disk. Catches the
  failure class that broke 3 juniper-X CIs on 2026-05-18 (script
  rename without workflow update).
- `juniper-lint-workflow-paths` console script. Auto-discovers the
  repo root via `.github/workflows/`; supports `--repo-root`,
  `--workflows-dir`, `--exit-zero`, `--json`, `--version`. Exit
  codes: 0 (clean), 1 (missing paths), 2 (repo root or workflows
  dir not discoverable).
- Public API additions: `LintResult`, `LintFinding`,
  `lint_workflow_paths`, `extract_script_paths`, `is_validatable`,
  `find_repo_root`, `DEFAULT_ECOSYSTEM_SIBLING_PREFIXES`.
- 23 new tests under `tests/test_lint_workflow_paths.py` covering
  extraction edge cases (YAML parse failure, multi-version python,
  bash invocations, unittest positional args), cross-repo prefix
  skipping with configurable sibling list, repo-root walk-up
  discovery, end-to-end lint runs against synthetic repos, and full
  CLI exit-code matrix including JSON output.

### Migration context

Replaces the 6 byte-identical copies of
`util/test_workflow_script_paths.py` that existed across consumer
repos. A future consumer-adoption PR series will swap the inline
copies for `pip install "juniper-ci-tools>=0.2.0,<0.3.0"` +
`juniper-lint-workflow-paths` (or `python3 -m unittest` of the
in-package test, depending on each repo's preferred runner).

## [0.1.0] -- 2026-05-20

Initial PyPI scaffold (Wave 0 of the `juniper-ci-tools` migration; plan doc
`notes/JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md` in the juniper-ml repo).

### Added

- `juniper_ci_tools.generate_dep_docs` -- Python port of the legacy
  `scripts/generate_dep_docs.sh` that drifted across 8 Juniper repos. The
  cascor 2026-05-20 awk-extraction fix is the canonical implementation;
  the pre-fix sed pipeline has been deliberately abandoned.
- `juniper-generate-dep-docs` console script and `python -m juniper_ci_tools`
  module form.
- `juniper_ci_tools.render_header` helper exposed for tests and ad-hoc
  callers; substitutes the historical `<X.Y.Z ...>`, `<YYYY-MM-dd ...>`,
  `<Python Version>`, `<Pip Version>` placeholders.
- 40+ pytest-based regression tests under `juniper-ci-tools/tests/` covering
  the awk-extraction fix (trailing `prefix:` / `variables:` exclusion,
  uppercase-key termination, nested pip indent preservation, empty inputs),
  end-to-end happy path, backup behavior, no-conda / no-validation paths,
  error cases (missing or malformed pyproject), and CLI exit codes.
- `ci-ci-tools.yml` and `publish-ci-tools.yml` GitHub Actions workflows in
  the juniper-ml repo (the package's home), mirroring the doc-tools
  precedent.
