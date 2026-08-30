# Changelog

All notable changes to the `juniper-doc-tools` package are documented in this
file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-08-30

### Fixed

- `ECOSYSTEM_REPOS` was missing **`juniper-recurrence`** and **`juniper-slacker`**,
  two repos added to the polyrepo after the set was written. Drift here is silent
  and misattributed: a repo absent from the set is never classified as a cross-repo
  link, so `../juniper-recurrence/notes/x.md` is resolved as an ordinary intra-repo
  path, fails, and is reported as a **broken link** — blaming the link rather than
  the stale roster. Nothing tested the set; juniper-ml's
  `tests/test_doc_tools_drift.py` now pins it against
  `util/release_train/registry.yaml` (the same authority the claude.yml fan-out
  uses), so the next repo added to the ecosystem cannot drift in silence.

### Changed

- CI now enforces a **blocking per-file coverage gate** via
  `juniper-coverage-gap-map --enforce` (from `juniper-ci-tools>=0.6.0`):
  every source file must reach >=90% statement coverage and the package's
  pooled (statement-weighted) coverage must reach >=95%. Expanded the test
  suite with targeted tests for `check_doc_links.py` (file-argument and
  out-of-tree scan paths, `data:`/`//` links, the cross-repo symlink-escape
  boundary check, verbose OK/SKIP tracing) and `cli.py` (the `--cross-repo
  check` discovery branches) plus an in-process `runpy` smoke test for the
  `__main__` entry shim, lifting measured coverage from 87.33% to 99.33%
  pooled. Per-file coverage rollout C-3 (juniper-ml
  notes/JUNIPER_2026-06-30_JUNIPER-ECOSYSTEM_PER-FILE-COVERAGE-ROLLOUT-SCOPING.md).
  No runtime or behavioral change.

## [0.1.1] - 2026-05-19

### Fixed

- CLI summary line "FOUND N broken link(s) in M file(s)" -- the M count
  now matches the inline-script behavior it replaced. The 0.1.0 CLI
  estimated M by string-deduping error prefixes, which double-counted
  any markdown file that had *both* a broken-anchor error (prefixed
  with the absolute ``Path``) and a broken-link error (prefixed with
  the path relative to ``repo_root``). The count is now tracked at
  iteration time in :func:`validate_directory` and exposed on
  :class:`ValidationResult` as the new ``files_with_errors`` attribute.
- Programmatic consumers gain access to the file count via
  ``ValidationResult.files_with_errors`` (additive; existing fields
  unchanged).

No behavioral change beyond the summary line: the per-error output and
the exit code are unchanged.

## [0.1.0] - 2026-05-18

### Added

- **First public release.** Packages the Juniper documentation link
  validator (previously a per-repo `scripts/check_doc_links.py` script) as
  a single PyPI distribution with a stable CLI surface and a small Python
  library API.
- `juniper-check-doc-links` console script (plan §8.2).
- `python -m juniper_doc_tools` module-form invocation (plan §8.3).
- `--strict-repo-boundary` flag for opt-out of ecosystem-root link
  classification (plan §3.4.1 / §8.4). Default is off; ecosystem-root
  links like `../../CLAUDE.md` are subject to the `--cross-repo` policy.
- `--repo-root` flag for explicit repository-root resolution (helpful in
  CI matrix runners that may not run from the repo root).
- `--version` flag for printing the package version.
- Public library API: `ValidationResult` dataclass, `validate_directory`,
  `validate_file`, `discover_ecosystem_root`.
- Constants and regex helpers extracted into a separate
  `juniper_doc_tools._ecosystem` module (`ECOSYSTEM_REPOS`,
  `ECOSYSTEM_ROOT_ITEMS`, `CROSS_REPO_PATTERN`, `ECOSYSTEM_ROOT_PATTERN`,
  `CROSS_REPO_MODES`, `MAX_TRAVERSAL_DEPTH`) so future ecosystem-wide
  tools can reuse them.

### Behavior parity with `juniper-ml/util/check_doc_links.py` v0.7.0

This first release is **functionally equivalent** to the v0.7.0 standalone
script that shipped on 2026-05-18 to fix the immediate CI failure. The
only intentional behavior addition is the `--strict-repo-boundary` flag;
default-on ecosystem-root classification is unchanged.

### Notes

- Pure stdlib; no runtime dependencies.
- Tests use pytest (plan §8.1) for parity with the rest of the Juniper
  ecosystem.
