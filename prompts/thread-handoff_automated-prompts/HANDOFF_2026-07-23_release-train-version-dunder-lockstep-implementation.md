# HANDOFF 2026-07-23 — Implement the release-train `_version.py` lockstep design (ml#701)

**Origin**: session "release-train pin-fix" (juniper-ml), after the SEC-F01 / loose-ends / recurrence-parity arcs completed and the design doc + drift heal merged (ml#701 + ml#702).
**Target**: a fresh Claude Code session started in `/home/pcalnon/Development/python/Juniper/juniper-ml`.
**Scope**: one repo (juniper-ml), one implementation PR (plus the standard owner-merge ceremony). Design of record: `notes/JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md` (read it FIRST — this handoff orients; the doc specifies).

Every `file:line` below was verified 2026-07-23 at juniper-ml main `69efc9c` and spot-rechecked at `17c9975`. Release-train Phase 4.x work is landing concurrently and `util/release_train/` moves often — **re-verify each anchor at your HEAD before editing; treat any drifted anchor as a stop-and-re-ground signal, not something to power through.** Do not invent paths, flags, registry fields, or test names: if a needed signal does not exist, stop and ask the owner.

---

## Completed so far (do NOT redo)

- The failure class is fully documented in the design doc (merged ml#701): static-version packages that also carry a `_version.py` dunder get only the pyproject bump from `util/release_train/propose.py`, so the shipped wheel's `__version__` lies. Two live incidents happened: juniper-ci-tools 0.7.0 (healed by ml#684) and juniper-service-core 0.5.0 (healed by ml#702).
- **Baseline is clean**: all five static in-repo packages (ci-tools, config-tools, doc-tools, observability, service-core) have pyproject == dunder at `17c9975` — so the new gate can land green with no companion heal.
- The dunder inventory, root cause, design, and acceptance criteria are in the doc's sections 2-4. Do not re-derive them; re-verify them.

## Remaining work

### Item 0 — Decision gate (ask ONLY if the owner is present at dispatch; otherwise default to Option A)

The doc names two paths.
**Option A (design of record — DEFAULT)**: teach `propose.py` to emit the dunder as a lockstep `FileEdit` + hermetic tests + a generic gate.
**Option B (alternative the owner may weigh)**: flip the five static packages to `dynamic = ["version"]`, dissolving the class — but note B is heavier than it reads: each package needs `[tool.setuptools.dynamic]` version wiring, `util/release_train/registry.yaml` `version_source` flips for five entries, and `tests/test_release_train_registry.py`'s dynamic-version-set assertions move.
Implement A unless the owner explicitly picks B.

### Item 1 — propose.py lockstep FileEdit (Option A)

- Anchors (@ `69efc9c`; re-verify): version-edit section comment `util/release_train/propose.py:279`; `_version_py_relpath(entry)` at `:285` (computes `<entry.path>/<import_package>/_version.py`); `set_pyproject_version` at `:289`; `set_dynamic_version` at `:308`; the either/or apply site at `:1033-1035` (`dynamic` -> `set_dynamic_version`, else `set_pyproject_version`).
- Change: in the static branch, after the pyproject edit, `sources.read_file(entry, _version_py_relpath(entry))`; when the file exists, apply `set_dynamic_version` to it and append the `FileEdit` — auto-detection by file presence, **no new registry field** (doc §3.1).
Surface the co-change in the proposal body / co-change checklist the same way the `AGENTS.md` co-change is surfaced (see `_co_change_checklist` and the S5.4 patterns nearby; the ml#661 in-repo co-change block at `propose.py:693-717` is the style precedent).
- Respect the module's hermetic-seams style: all file access goes through the injected `sources` seam; no direct filesystem reads in the new code path.

### Item 2 — hermetic propose tests

- Extend `tests/test_release_train_propose.py` (hermetic — no network/gh/writes; the suite is the sole gate because `util/` is not lint-gated). Three required shapes (doc §3.2): static-with-dunder bumps BOTH files in one proposal; static-without-dunder emits no phantom `_version.py` edit; the dynamic path is unchanged. Also assert the proposal body mentions the dunder co-change.
- The suite passed `OK` at `17c9975` — capture your HEAD's test count before editing and keep every pre-existing test green.

### Item 3 — generic pyproject==dunder gate + house registration co-changes

- New always-on lint asserting `[project].version == __version__` for every in-repo package that has BOTH a static pyproject version and a `_version.py` (doc §3.3). Home: extend `tests/test_release_train_registry.py` (it already resolves all in-repo package versions — check its helpers before writing new resolution code) or a standalone `tests/test_version_dunder_lockstep.py` if the registry test's structure resists. Dynamic packages are exempt (their dunder IS the source).
- If a new test FILE is created, the house co-changes are mandatory in the same PR: add it to `.github/workflows/ci.yml`'s per-file unittest list AND to `AGENTS.md` in all three places (the "Run all tests" command block, the repository-structure tree, and the "### Tests" bullet list). Precedent with exact shape: how `tests/test_env_repr_safety.py` was registered (see that name in both files).
- Note: the ci-tools-specific dunder gates (`tests/test_coverage_gap_mapper_drift.py` / `tests/test_env_drift_check_drift.py` `test_version_dunder_matches_pyproject`) stay as consumer-side belt-and-braces; do not remove them.

## Key context / gotchas

- **Concurrent sessions are the norm here** (release-train Phase 4.x is active; this arc collided once already). Before opening the PR: `gh pr list` in juniper-ml as a dup-guard AND re-check `git log origin/main` freshness. The codeql-duplicate incident happened because a session skipped exactly this.
- House worktree procedure: centralized `worktrees/` dir, `<repo>--<branch-with-slashes-as-double-dash>--<YYYYMMDD-HHMM>--<hash8>` naming; never work in the primary checkout.
- Headless commits MUST use `-c commit.gpgsign=false` (owner's YubiKey config otherwise hangs). juniper-ml main enforces `required_signatures`, so the PR will show BLOCKED even when green — the owner's merge handles it; never use `--admin`.
- One tidy commit per PR (squash-merge first-commit-only convention). PR body: reference the design doc + ml#701, list the acceptance criteria as a checklist, and include the standard `## Requirements` JR-ID section (omit with the no-tracked-ID note if none applies).
- `tests/redacted_env.py` exists — if any new test spawns a subprocess with an env mapping, build it with `RedactedEnv` or `tests/test_env_repr_safety.py` fails the build (this gate has already caught one live violation).
- `python3 -m unittest discover -s tests` shows ~12 pre-existing order-dependent failures in a single process on clean main (ci-tools drift family) — **CI runs each file in its own process and is green**; verify per-file, not via discover. Do NOT add `tests/__init__.py` to "fix" this (it changes discover semantics; mypy is handled via `explicit_package_bases` in pyproject).
- AGENTS.md's `**Last Updated**` auto-bumps via workflow; do not hand-edit that field.

## Session verification commands (run FIRST)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline -3 origin/main          # expect 17c9975 or newer
ls notes/JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md   # the spec
sed -n '279,320p;1025,1045p' util/release_train/propose.py    # re-verify the Item-1 anchors at your HEAD
python3 -m unittest tests.test_release_train_propose -q       # expect OK; note the count
for d in juniper-ci-tools juniper-config-tools juniper-doc-tools juniper-observability juniper-service-core; do \
  python3 -c "import re,pathlib; py=re.search(r'^version = \"([^\"]+)\"', pathlib.Path('$d/pyproject.toml').read_text(), re.M).group(1); ns={}; exec(pathlib.Path(next(pathlib.Path('$d').glob('juniper_*/_version.py'))).read_text(), ns); print('$d', py, ns['__version__'], 'OK' if py==ns['__version__'] else 'DRIFT')"; done
```

If any package prints `DRIFT`, a release landed between handoffs — heal it in a separate one-line PR first (the ml#702 precedent) so the new gate can land green.

## Git state at handoff

- juniper-ml: main @ `17c9975`, primary checkout clean and synced; no worktrees or branches belonging to this task exist yet.
- No other repo is touched by this task (Option A). Option B would touch only juniper-ml too (all five packages are in-repo), but see Item 0 before going there.

## Acceptance criteria (from the doc §4, restated)

1. A release-train proposal for any static-with-dunder in-repo package produces a PR diff bumping `pyproject.toml` AND `_version.py` together, with the co-change named in the proposal body.
2. `tests/test_release_train_propose.py` covers the three shapes and the full suite passes at your HEAD.
3. The generic pyproject==dunder gate runs in CI (per-file unittest battery) and is green — with ci.yml + AGENTS.md registration co-changes if a new test file was created.
4. `util/release_train/` docstrings + the release-train plan doc's co-change inventory mention the dunder artifact (grep `propose.py`'s module docstring and the S5.4 references; extend, don't rewrite).
5. One owner-merge PR, standard gates green (pre-commit + the repo's unittest battery), no self-merge.

## Validation record

Drafted 2026-07-23 by the origin session immediately after ml#701/#702 merged, from first-hand grounding: the propose.py anchors, the five-package dunder inventory, and the baseline-clean check were probed directly at `69efc9c` and spot-rechecked at `17c9975`; the concurrency, signing, worktree, and test-registration gotchas were all exercised live during the preceding arcs (SEC-F01 adoption, env-repr redaction, codeql fleet fix, ci-tools 0.7.0 unblock).
No independent validator pass was run on this prompt — its anchors are one day old at most; the re-verify-at-HEAD doctrine above is the compensating control.

---
/apps/juniper-release-train
