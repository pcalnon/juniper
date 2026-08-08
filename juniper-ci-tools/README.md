<!-- markdownlint-disable -->

# juniper-ci-tools

Shared CI / build tooling for the [Juniper ML platform](https://github.com/pcalnon/juniper-ml).

This package is the **single source of truth** for the dependency-documentation
generator that historically lived as `scripts/generate_dep_docs.sh` (or
`util/generate_dep_docs.sh`) in every Juniper repo. Three variants of that
script drifted on `origin/main`; the 2026-05-20 bug fix in
[juniper-cascor#276](https://github.com/pcalnon/juniper-cascor/pull/276)
(switching the conda-dependency extraction from `sed` to `awk` to avoid
emitting an invalid trailing `prefix:` / `variables:` key) shipped in 1 of 8
repos. This package distributes that fix as `pip install`-able tooling so it
cannot drift again.

This work mirrors the
[`juniper-doc-tools` PyPI migration plan](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md)
that addressed the analogous 2026-05-18 doc-link validator incident.

## Installation

```bash
pip install juniper-ci-tools
```

This installs the following console scripts (see the package's
`[project.scripts]` for the authoritative set):

- `juniper-generate-dep-docs` — dependency-documentation generator (the
  consolidated `scripts/generate_dep_docs.sh` port; see "Usage" below).
- `juniper-lint-workflow-paths` — lints that every
  `python|bash <path>` invocation in `.github/workflows/*.yml`
  references a file that exists on disk. Added in 0.2.0;
  consolidates the 6 byte-identical copies of
  `util/test_workflow_script_paths.py` that existed across consumer
  repos.
- `juniper-lint-agents-md-version` — lints that the `AGENTS.md`
  `**Version**:` header matches `pyproject.toml` `[project].version`
  (added in 0.3.0).
- `juniper-lint-agents-md-header` — lints the `AGENTS.md` canonical
  six-field header schema (added in 0.4.0).
- `juniper-coverage-gap-map` — per-file coverage-gap mapper (added in 0.5.0;
  **enforcing mode added in 0.6.0**): parses a `coverage json` and reports the
  per-file distribution, the files below a threshold (default 90 %), and each
  sub-module's average vs a bar (default 95 %). **Advisory by default** (exit 0
  always — it reports, it never fails a build); the opt-in `--enforce` flag
  turns it into a blocking gate (exit 1 on a per-file statement gap or a
  sub-module pooled gap). Carries a documented numpy-2.x package-form `--cov`
  shim. See "Per-file coverage gate" below.
- `juniper-symbol-loss-check` — AST symbol-loss screen (added in 0.8.0):
  FAILs when a def/class/method (or bash function) is silently deleted, gutted
  past threshold, or duplicated between BASE and HEAD. See "Sequence-safety
  screens" below.
- `juniper-docs-additions-check` — markdown deletion-magnitude screen (added
  in 0.8.0): FAILs on a deleted heading or a run of `>= N` consecutive deleted
  lines. See "Sequence-safety screens" below.

The package requires Python 3.11 or newer and depends on PyYAML and packaging.

## Usage

Run from the root of any Juniper repo that has a `pyproject.toml`:

```bash
juniper-generate-dep-docs
```

Equivalent module form:

```bash
python -m juniper_ci_tools
```

This will:

1. Create `conf/` if needed.
2. Back up any existing `conf/requirements_ci.txt` with a timestamp infix.
3. Render `notes/JUNIPER_2026-03-11_JUNIPER-ML_PIP-DEPENDENCY-FILE-HEADER.md` (substituting placeholders
   like `<X.Y.Z ...>`, `<YYYY-MM-dd ...>`, `<Python Version>`, `<Pip Version>`)
   and append `pip list --format=freeze` output.
4. If `conda` is on `PATH`: back up any existing
   `conf/conda_environment_ci.yaml`, render
   `notes/JUNIPER_2026-03-15_JUNIPER-ML_CONDA-DEPENDENCY-FILE-HEADER.md`, append the dependency block
   extracted from `conda env export --no-builds` (using the awk-equivalent
   logic that produces valid YAML), and validate the result with
   `yaml.safe_load`.

If conda is not available the conda step is skipped with a warning (matches
the legacy bash script). If the generated YAML fails to parse, the command
exits non-zero.

### CLI options

| Flag | Default | Purpose |
|---|---|---|
| `--repo-root` | cwd | Repo root containing `pyproject.toml` |
| `--conf-dir` | `conf` | Output directory |
| `--notes-dir` | `notes` | Directory containing header templates |
| `--pip-header` | `JUNIPER_2026-03-11_JUNIPER-ML_PIP-DEPENDENCY-FILE-HEADER.md` | Pip header template filename |
| `--conda-header` | `JUNIPER_2026-03-15_JUNIPER-ML_CONDA-DEPENDENCY-FILE-HEADER.md` | Conda header template filename |
| `--pip-filename` | `requirements_ci.txt` | Pip output filename |
| `--conda-filename` | `conda_environment_ci.yaml` | Conda output filename |
| `--no-conda` | off | Skip conda generation even if conda is installed |
| `--no-yaml-validation` | off | Skip `yaml.safe_load` on generated conda file |

## Environment floor-drift check (`juniper-env-drift-check`)

Run from (or against) any Juniper repo to assert the active environment is not
*below* the client floors the repo's `pyproject.toml` declares — the durable,
reusable form of the dependency-satisfaction guard (added in 0.5.0). Unlike
`util/editable_install_drift_check.py`, it reads versions via
`importlib.metadata`, so **plain wheels are checked identically to editable
installs** (the 2026-06-26 canopy "green tests / dead app" incident class).

```bash
# Scan the active interpreter against ./pyproject.toml
juniper-env-drift-check

# Check a specific repo, and also assert its lockfile pins satisfy the floors
juniper-env-drift-check --repo-root /path/to/repo --check-lock

# Scan a specific environment's site-packages (e.g. a conda env), as JSON
juniper-env-drift-check --site-packages /opt/miniforge3/envs/MyEnv/lib/python3.13/site-packages --json
```

Exit codes: `0` (no floor below its requirement), `1` (drift — an installed
wheel, or a `--check-lock` lock pin, below a floor), `2` (usage error — no
`pyproject.toml`, no `juniper-*` floors, or `--check-lock` with no lockfile). A
not-installed floor is a soft note unless `--strict` is given. Every floor (OK
and drifted alike) is listed — no silent truncation.

## Per-file coverage gate (`juniper-coverage-gap-map`)

Parse a `coverage json` (coverage.py / pytest-cov `--cov-report=json`) and map
the per-file coverage gaps. **Advisory by default; enforcing is opt-in.**

```bash
# Advisory (default): report only, exit 0 always.
juniper-coverage-gap-map --coverage-json coverage.json
juniper-coverage-gap-map --coverage-json coverage.json --json   # machine output

# Run the repo's real test command under coverage first (secondary path):
juniper-coverage-gap-map --repo-root . --package my_pkg \
    --test-command "python -m pytest"

# Enforcing gate (opt-in, added 0.6.0): exit 1 if any source file's STATEMENT
# coverage < 90 OR any sub-module's POOLED coverage < 95; exit 0 when clean.
juniper-coverage-gap-map --coverage-json coverage.json --enforce \
    --fail-under-file 90 --fail-under-submodule 95 --omit '*/__main__.py'
```

The enforcing gate deliberately uses different bases than the advisory display,
so it stays apples-to-apples across units (work-unit C-0 of the per-file
coverage rollout):

- **Per-file basis = statement** coverage (`covered_statements /
  num_statements`), **not** the branch-inclusive `percent_covered` the report
  shows (a repo running `branch = true` reports a branch-inclusive percent).
- **Sub-module basis = pooled** (statement-weighted `Σcovered / Σstatements`),
  **not** the mean-of-files average the report shows (the two diverge for small
  files and can flip a sub-module's outcome).
- `--omit <glob>` (repeatable) excludes files from the report **and** the gate,
  applied to the parsed JSON before gating — the tool is the single source of
  truth for what counts. Zero-statement files (re-export `__init__.py`) already
  score 100 %, so `--omit` is for thin `__main__.py` / CLI shims and the like.

Scope the gate to repos or sub-packages with importable source trees. `--omit`
is a measured-file exclusion, not a whole-repo escape hatch: use it for specific
paths that appear in `coverage.json` and match the rollout's exclusion policy
(for example a thin dispatch-only `__main__.py`). Repos with no importable
package, such as the `juniper-ml` meta-package (`packages = []`) or
`juniper-deploy`, are accounted for by the Phase C exemption ledger instead of
by running the mapper against an empty source tree.

Exit codes: `0` (advisory always, or an enforcing run that is clean), `1`
(enforcing only — a file or sub-module is under its floor; every offender is
listed, no silent truncation), `2` (usage / structural error — no input, an
unreadable or malformed `coverage.json`, or a dotted `--package`).

## Sequence-safety screens (`juniper-symbol-loss-check` / `juniper-docs-additions-check`)

Two ref-diff screens (added in 0.8.0) that answer the one question a per-PR check
cannot: what was *silently deleted* between BASE and HEAD. They productionize the
2026-07-28 Cursor-fleet flood census (Proposal P2) and are the single,
PyPI-distributed source of truth for the sequence-safety gates that previously
lived as hand-copied `util/sequence_safety/` trees. Both are pure git + stdlib
(no network, gh, or pip), advisory-capable, and honor a commit-trailer waiver.

```bash
# Symbol-loss screen (gate G1 / G3): FAIL on a silently deleted / gutted /
# duplicated def/class/method (or bash function). Default scope = the historical
# juniper-ml surface (tests/*.py + util/**); pass --scope to screen another tree.
juniper-symbol-loss-check --base origin/main --head HEAD
juniper-symbol-loss-check --base <merge>^1 --head <merge> --scope 'src/**/*.py'

# Docs deletion-magnitude screen (gate G2 / G3): FAIL on a deleted heading or a
# run of >= --min-run (default 5) consecutive deleted lines. Default scope is the
# universal docs cluster (AGENTS.md + docs/**/*.md + notes/**/*.md).
juniper-docs-additions-check --base origin/main --head HEAD
juniper-docs-additions-check --base origin/main --head HEAD --min-run 8

# Advisory mode (print findings but exit 0 even on an unwaived FAIL) + JSON:
juniper-symbol-loss-check --base <b> --head <h> --advisory --json

# Module form (both):
python -m juniper_ci_tools.cli_symbol_loss_check --help
python -m juniper_ci_tools.cli_docs_additions_check --help
```

`--scope GLOB` (repeatable, POSIX path globs with explicit `**` recursion) selects
the screened surface per repo; with no `--scope` each screen reproduces its
historical hard-coded predicate verbatim, so a default run is byte-identical to
the pre-migration util scripts. `--files PATH ...` bypasses scope entirely.

Escape hatches travel in git history (so they work for both the per-PR and the
post-merge gate): an `Allow-Symbol-Loss: <qualified.symbol>[, ...]` /
`Allow-Docs-Rewrite: <path>[, ...]` commit trailer in the BASE..HEAD range waives
the enumerated symbols / files (a `*` symbol wildcard is rejected; a `*` docs
wildcard waives all). Exit codes: `0` clean, `1` >= 1 unwaived FAIL, `2` usage /
invocation error (never masked by `--advisory`).

## Library API

```python
from juniper_ci_tools import generate_dep_docs

result = generate_dep_docs(repo_root="/path/to/repo")
print(result.pip_file, result.conda_file, result.yaml_validated)
```

See the package's `juniper_ci_tools/generate_dep_docs.py` docstring for the
full surface.

## Development

```bash
cd juniper-ci-tools
pip install -e ".[test]"
pytest
```

## License

MIT. Copyright (c) 2024-2026 Paul Calnon.
