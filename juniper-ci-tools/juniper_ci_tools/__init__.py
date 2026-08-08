"""``juniper-ci-tools`` -- shared CI / build tooling for the Juniper ecosystem.

Single-source-of-truth Python package for the dependency-documentation
generator that historically lived as a standalone
``scripts/generate_dep_docs.sh`` in every Juniper repo. Three variants drifted
on origin/main; the cascor 2026-05-20 bug fix (sed -> awk for YAML extraction)
shipped to 1 of 8 repos. This package replaces all of them with a single
PyPI-distributed implementation that survives single-repo CI checkouts and
cannot drift.

The public API is:

- :class:`GenerateResult` -- structured outcome of a generation run.
- :func:`generate_dep_docs` -- ergonomic library entry point.
- :class:`LintResult` / :class:`LintFinding` -- structured outcome of the
  workflow-script-path lint added in 0.2.0.
- :func:`lint_workflow_paths` -- ergonomic library entry point for the lint.
- :class:`AgentsMdLintResult` -- structured outcome of the AGENTS.md
  ``**Version**:`` drift lint added in 0.3.0.
- :func:`lint_agents_md_version` -- ergonomic library entry point for the
  AGENTS.md drift lint.
- :class:`CoverageReport` (with :class:`FileCoverage` / :class:`SubmoduleCoverage`)
  -- the per-file coverage-gap mapper added in 0.5.0 (advisory reporter by
  default; the CLI's opt-in ``--enforce`` mode, added in 0.6.0, turns it into a
  blocking gate on the statement / pooled bases).
- :func:`parse_coverage_json` / :func:`load_coverage_json` -- parse a
  ``coverage json`` into the structured report (the primary, fixture-testable
  path); :func:`run_coverage` runs a repo's real test command under the
  numpy-2.x-safe package-form ``--cov`` shim first.

For CLI usage, install the package and run :program:`juniper-generate-dep-docs`
(dep-docs generator), :program:`juniper-lint-workflow-paths` (workflow-script-
path lint), :program:`juniper-lint-agents-md-version` (AGENTS.md version
drift lint), :program:`juniper-coverage-gap-map` (advisory per-file
coverage-gap mapper), or ``python -m juniper_ci_tools`` (dep-docs generator).
The CLI surfaces are in :mod:`cli`, :mod:`cli_lint_workflow_paths`,
:mod:`cli_lint_agents_md_version`, and :mod:`cli_coverage_gap_mapper`.

See ``notes/JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md`` in the
juniper-ml repo for the design rationale, the incident-class motivation
(mirroring the 2026-05-18 doc-link validator incident), and the wave plan.
"""

# The two sequence-safety screens are re-exported as SUBMODULES (plus their two
# distinctly-named scope predicates), not flattened, because both modules define
# ``run`` / ``Finding`` / ``classify_file`` with different signatures -- flattening
# either into this namespace would silently shadow the other. Access those via the
# submodule: ``juniper_ci_tools.symbol_loss_check.run`` / ``...docs_additions_check.run``.
from juniper_ci_tools import docs_additions_check, symbol_loss_check
from juniper_ci_tools._version import __version__
from juniper_ci_tools.coverage_gap_mapper import (
    CoverageReport,
    FileCoverage,
    SubmoduleCoverage,
    load_coverage_json,
    package_cov_pytest_args,
    parse_coverage_json,
    run_coverage,
    write_include_coverage_config,
)
from juniper_ci_tools.docs_additions_check import in_docs_scope
from juniper_ci_tools.generate_dep_docs import (
    GenerateResult,
    generate_dep_docs,
    render_header,
)
from juniper_ci_tools.lint_agents_md_version import (
    AgentsMdLintResult,
    MultipleVersionHeadersError,
    RepoRootNotFoundError,
    find_agents_md_repo_root,
    lint_agents_md_version,
)
from juniper_ci_tools.lint_workflow_paths import (
    DEFAULT_ECOSYSTEM_SIBLING_PREFIXES,
    LintFinding,
    LintResult,
    extract_script_paths,
    find_repo_root,
    is_validatable,
    lint_workflow_paths,
)
from juniper_ci_tools.symbol_loss_check import in_scope

__all__ = [
    "__version__",
    "symbol_loss_check",
    "docs_additions_check",
    "in_scope",
    "in_docs_scope",
    "GenerateResult",
    "generate_dep_docs",
    "render_header",
    "DEFAULT_ECOSYSTEM_SIBLING_PREFIXES",
    "LintFinding",
    "LintResult",
    "extract_script_paths",
    "find_repo_root",
    "is_validatable",
    "lint_workflow_paths",
    "AgentsMdLintResult",
    "MultipleVersionHeadersError",
    "RepoRootNotFoundError",
    "find_agents_md_repo_root",
    "lint_agents_md_version",
    "CoverageReport",
    "FileCoverage",
    "SubmoduleCoverage",
    "parse_coverage_json",
    "load_coverage_json",
    "run_coverage",
    "package_cov_pytest_args",
    "write_include_coverage_config",
]
