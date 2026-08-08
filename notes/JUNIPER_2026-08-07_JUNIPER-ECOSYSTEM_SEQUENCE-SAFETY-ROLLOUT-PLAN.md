# Sequence-Safety Ecosystem Rollout Plan

**Project:** Juniper — cross-repo (juniper-ml canonical; 8 active repos)
**Repository:** pcalnon/juniper-ml (package + plan land here; consumers roll out per-repo)
**Author:** Paul Calnon (drafted by the planner agent)
**Document Type:** Implementation plan / roadmap
**Status:** Draft — awaiting owner ratification (decision list §8)
**Last Updated:** 2026-08-07
**Context:** Port the flood-remediation sequence-safety screens (Proposal P2 gates G1/G2/G3) from
two hand-copied inline trees into the published `juniper-ci-tools` package, then fan out to the
remaining six repos as an all-advisory net. Grounded in the real repos on disk plus `origin/main`
of juniper-cascor (fetched read-only) and the OPEN juniper-ml PR #1004.

---

## 1. Background & genesis

The 2026-07-25→28 Cursor-fleet PR flood merged whole test classes and doc sections into oblivion
while every per-PR check stayed green: the damage was **compositional** — serial same-file merges
fused/deleted sibling content, and a deleted test cannot fail. The forensic record and the three
validated guardrail proposals are in
[the flood-remediation analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md)
(§3 Proposal P2). P2's productionization shipped two ref-diff screens — an AST symbol-loss screen
and a markdown deletion-magnitude screen — plus a bypass-proof post-merge workflow.

The stack is **live in two repos, as two hand-copied trees**:

- **juniper-ml (native):** `util/sequence_safety/{symbol_loss_check,docs_additions_check}.py` +
  `__init__.py`; the post-merge `.github/workflows/main-verify.yml` (G3); a per-PR advisory
  `sequence-safety:` job folded into `.github/workflows/ci.yml`; gated by
  `tests/test_symbol_loss_check.py` + `tests/test_docs_additions_check.py`.
- **juniper-cascor (ported copy, cascor#482, MERGED 2026-08-07):** the same modules **re-scoped to
  `src/**`**, plus a *standalone* `.github/workflows/sequence-safety.yml` and its own
  `main-verify.yml`.

The two copies **already diverged once**: cascor's `src/` surface has `@property`/`@x.setter`
accessor pairs, so its port added a `_accessor_suffix` disambiguator; juniper-ml lacked it. The OPEN
juniper-ml PR #1004 (`fix/fleet-tooling-followups`) **backports** `_accessor_suffix` and lands docs
threshold-parity in `predict_merge`. That is exactly the inline-copy drift class the house killed
twice before by packaging: the doc-link validator
([doc-tools plan](JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md)) and the dep-docs
generator ([ci-tools plan](JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md)). Owner
directive (memory: "ci-tools fan-out keeps juniper-ml canonical — delete consumer copies; ml
dogfoods") mandates the same shape here.

## 2. Purpose & scope

**Goal.** Make the two screens a single PyPI-distributed source of truth in `juniper-ci-tools`,
fan the *advisory* net out to all eight repos, delete the two inline copies, and gate against
resurrection — with **zero ruleset changes anywhere** (every gate stays advisory; promotion to
required is a later per-repo owner call).

**In scope:** package migration; a GitHub-Release ceremony; per-PR + post-merge advisory workflows
in the six new repos; retrofitting ml + cascor to consume the package.

**Non-goals (§6 expands):** packaging `util/fleet_triage/` (stays ml-native v1); per-repo Slack
notify; per-repo full regression **battery** jobs in `main-verify` (screens-only for now);
promotion of any workflow to a required status check; ruleset / `required_signatures` / bypass-actor
changes. This plan touches no branch protection.

## 3. Current state (grounded)

### 3.1 Module & workflow inventory (the pioneers)

| Artifact | juniper-ml (native) | juniper-cascor (cascor#482) |
|---|---|---|
| symbol module | `util/sequence_safety/symbol_loss_check.py` | same path, `src/**` scope |
| docs module | `util/sequence_safety/docs_additions_check.py` | same path, identical scope |
| per-PR advisory | `ci.yml` `sequence-safety:` job (name "Sequence Safety") | standalone `sequence-safety.yml` (name "Sequence Safety (Advisory)") |
| post-merge (G3) | `main-verify.yml` v0.3.0 (catch-up base + stable-title notify) | `main-verify.yml` v0.1.0 |
| gating tests | `tests/test_symbol_loss_check.py` (461 ln), `tests/test_docs_additions_check.py` (369 ln) | ported alongside modules |

Both modules are pure git + stdlib (no network, gh, or pip). CLI surface today (verified on ml
`main` + cascor `origin/main`): `--base`, `--head`, `--files`, `--repo-root`, `--advisory`,
`--json`; docs adds `--min-run`. Exit codes: `0` clean / `1` findings / `2` usage. Escape hatches:
`Allow-Symbol-Loss:` and `Allow-Docs-Rewrite:` commit trailers. Shared thresholds are byte-identical
across both repos: `WEAKEN_RATIO = 0.6`, `WEAKEN_MIN_DELTA = 4` (symbol), `DEFAULT_MIN_RUN = 5`
(docs). There is **no `--scope` argument today** — scope is a hard-coded `in_scope()` / `in_docs_scope()`.

### 3.2 The scope divergence (the crux)

Only the **symbol** screen's scope diverges; the **docs** scope is identical in every repo.

| Screen | Scope predicate (in_scope) | ml | cascor |
|---|---|---|---|
| symbol | Python/bash surface | `tests/*.py` (top-level) + `util/**/*.py` + `util/**/*.bash` | `src/**/*.py` (incl. `src/tests/**`) |
| docs | markdown cluster | `AGENTS.md` (+`CLAUDE.md` symlink) + `docs/**/*.md` + `notes/**/*.md` | **identical** |

So parameterization is a **symbol-screen concern**; the docs default is universal.

### 3.3 Consumer repo layout matrix (the six new repos)

| Repo | Py floor | Source / damage locus | Test root | Formatter | Workflows | `required_signatures` | `pull_request` rule |
|---|---|---|---|---|---|---|---|
| juniper-data-client | ≥3.12 | `juniper_data_client/` | `tests/` | black+flake8 | `ci.yml` only | yes | no |
| juniper-cascor-client | ≥3.12 | `juniper_cascor_client/` | `tests/` | black+flake8 | `ci.yml` only | yes | no |
| juniper-cascor-worker | ≥3.12 | `juniper_cascor_worker/` | `tests/` | black+ruff | `ci.yml` only | yes | no |
| juniper-data | ≥3.12 | `juniper_data/` (`src`→symlink) | `juniper_data/tests` | **ruff** (no black) | `ci.yml` only | yes | yes |
| juniper-canopy | ≥3.11 | `src/**` (like cascor) | `src/tests` | black+ruff | `ci.yml` only | yes | yes |
| juniper-deploy | n/a (compose/Helm) | no Python app | `tests/`, `k8s/.../templates/tests` | n/a | `ci.yml` only | yes | yes |

Every repo has an `AGENTS.md`. **All eight repos enforce `required_signatures`** on `main`
(read-only `gh api repos/.../rules/branches/main`) — a rollout-mechanics constraint (§7 R1), not a
gate this plan changes. Every consumer already pins `juniper-ci-tools` for dep-docs; current pins
are `>=0.2.0,<0.7.0` (canopy `>=0.6.0,<0.7.0`) — note these **already exclude the current 0.7.1**
(latent drift, §7 R6 / decision D4).

### 3.4 Target package (`juniper-ci-tools`)

Dist `juniper-ci-tools`, import `juniper_ci_tools`, version **0.7.1**, `requires-python >=3.11`,
subdir `juniper-ci-tools/` of juniper-ml. House pattern per tool: a logic module `<name>.py` + a
thin `cli_<name>.py` (argparse + `main`) + a `[project.scripts]` entry. The **class guard**
`tests/test_env_drift_check_drift.py::test_every_cli_module_has_a_console_script` asserts *every*
`juniper_ci_tools/cli*.py` maps to a `[project.scripts]` entry — so the two new CLIs must be wired
or the always-on battery fails. Release is tag-triggered (`publish-ci-tools.yml`, on the `release`
event when the tag starts `juniper-ci-tools-v`); ci-tools is a registered release-train package
(`util/release_train/registry.yaml`; `ship_paths: ["juniper-ci-tools/juniper_ci_tools/"]` already
covers new modules — no registry edit needed).

## 4. Design — the package migration

### 4.1 Where the screens land

Add four modules to `juniper-ci-tools/juniper_ci_tools/`, splitting logic from CLI per house style:

| New file | Role | Console script |
|---|---|---|
| `symbol_loss_check.py` | logic: AST inventory, classify, relocation, waivers, `run()` | — |
| `cli_symbol_loss_check.py` | argparse (adds `--scope`) + `main()` | `juniper-symbol-loss-check` |
| `docs_additions_check.py` | logic: hunk parse, magnitude classify, waivers, `run()` | — |
| `cli_docs_additions_check.py` | argparse (adds `--scope`, keeps `--min-run`) + `main()` | `juniper-docs-additions-check` |

`__init__.py` re-exports the public API (`run`, `Finding`, `in_scope`/`in_docs_scope`, the classify
helpers). Console-script entries added to `[project.scripts]` — the class guard then covers them
automatically; **no new class-guard test is required**.

### 4.2 Scope parameterization (the hard part)

**Requirement:** ml scopes `tests/*.py`+`util/**`; cascor scopes `src/**`; six more repos each need a
different surface — *without* forking the code again. Everything else (`--files` override, both
trailers, `--advisory`, `--min-run`, exit codes, `--json`, human/JSON output) must stay **byte-identical**.

**Options considered:**

- **(A) `--scope GLOB` CLI args, repeatable, passed by each repo's workflow** *(chosen).* A path is
  in scope iff it matches any `--scope` glob AND carries a screenable extension (`.py`/`.bash` for
  symbol, `.md` for docs). Explicit, greppable in the workflow, and mirrors how cascor already
  encodes its divergence. When **no** `--scope` is passed, fall back to the built-in default that
  reproduces the historical `in_scope()` predicates **verbatim** (ml symbol default; universal docs
  default) — so ml's own retrofit needs no `--scope` and stays byte-identical.
- **(B) `[tool.juniper_sequence_safety]` pyproject table** (`symbol_scope`, `docs_scope`, `min_run`)
  read when `--scope` is absent. Better local-dev parity (bare invocation matches CI) but adds a
  config surface and a TOML read. **Offer as an optional Wave-0.5 enhancement (defer; decision D2).**
- **(C) named presets (`--profile cascor-src`)** — rejected: bakes repo identity into the shared package.

**Glob-matching caveat (grounded):** ci-tools floors at `>=3.11`, so `PurePosixPath.full_match`
(3.13+) is unavailable. Add a small tested `_match_scope(path, globs)` (POSIX, explicit `**`
recursion, via `fnmatch.translate` with `**`→`.*`). The **default path bypasses the glob engine
entirely** and keeps the exact `startswith`/`endswith` predicates, so pioneer behavior cannot drift.
Hermetic tests pin: default==historical predicate; `--scope 'src/**/*.py'` matches `src/tests/a.py`
but not `util/a.py`; extension gate still applies; `--files` still bypasses scope.

**Per-repo symbol scope (recommended):**

| Repo | `--scope` (symbol screen) | Docs screen |
|---|---|---|
| juniper-data-client | `'juniper_data_client/**/*.py' 'tests/**/*.py'` | default (universal) |
| juniper-cascor-client | `'juniper_cascor_client/**/*.py' 'tests/**/*.py'` | default |
| juniper-cascor-worker | `'juniper_cascor_worker/**/*.py' 'tests/**/*.py'` | default |
| juniper-data | `'juniper_data/**/*.py'` (covers `juniper_data/tests`) | default |
| juniper-canopy | `'src/**/*.py'` (mirrors cascor; tests under `src/tests`) | default |
| juniper-deploy | minimal `'tests/**/*.py'` **or omit** (decision D3) | default, higher `--min-run` (D6) |

The docs screen ships the universal default for all six, so `--scope` is a symbol-screen-only knob
in practice.

### 4.3 Carry the #1004 module state

Wave 0 lifts the **post-#1004** module state, not what is on `main` today:

- `_accessor_suffix(node)` in `symbol_loss_check.py` (`@x.setter`/`@x.deleter` keyed distinctly so a
  legitimate accessor pair is never a false `DUPLICATED`). Already present in cascor's port; #1004
  backports it to ml.
- The #1004 threshold-parity is in **`predict_merge`** (fleet-triage): it delegates the docs screen
  to `docs_additions_check.py` so a per-PR fleet verdict is byte-identical to the post-merge gate
  (small in-place swap → WARN, not the old any-removed-line FAIL). The screen modules' own
  thresholds are unchanged (5 / 0.6 / 4). Wave 0 assumes **#1004 merges first** (or Wave 0 carries
  its two module deltas explicitly — see §7 R7).

### 4.4 Tests migrate

Move `tests/test_symbol_loss_check.py` + `tests/test_docs_additions_check.py` into
`juniper-ci-tools/tests/`, converting from ml's importlib path-loading of the util script to package
imports / CLI invocation (`python -m juniper_ci_tools.cli_symbol_loss_check`). They are already
hermetic (tmp git repos, git-read-only, nothing signs), so no secret surfaces; keep them hermetic
and follow the ci-tools `conftest.py` submodule-registration idiom. Add scope-parameterization tests
(§4.2). The RedactedEnv discipline applies only if any test grows a subprocess `env=` mapping —
today none do (git reads only).

### 4.5 Version, lockstep, registry

- **0.7.1 → 0.8.0** (minor: two new console scripts = new features; pre-1.0 SemVer). Bump
  `pyproject.toml [project].version` **and** `juniper_ci_tools/_version.py` in the same commit
  (`test_version_dunder_matches_pyproject` enforces lockstep).
- Registry: no change (ship_paths already includes the package dir). CHANGELOG `[Unreleased]` gets an
  `Added` entry for both scripts + `--scope`.

### 4.6 What stays behind in ml (temporarily)

`util/fleet_triage/predict_merge.py` stays **ml-native v1** — it is not packaged. Today it consumes
the symbol screen by subprocess to the util path (`_SYMBOL_LOSS_CHECK`), and post-#1004 also the docs
screen (`_DOCS_ADDITIONS_CHECK`). Wave 3 switches those two path constants to the console-script /
module form. Fleet-triage packaging is a non-goal (§6).

## 5. Roadmap (waves)

Each numbered step is a single, independently shippable, independently verifiable work unit.

### Wave 0 — package migration (juniper-ml PR)

0.1 Land / confirm #1004 on `main` (module state precondition).
0.2 Add the four modules (§4.1); logic lifted verbatim except `run()` gains a `scope` parameter and
    the default preserves the historical predicate.
0.3 Add `--scope` + `_match_scope` to both CLIs; wire two `[project.scripts]` entries.
0.4 Migrate the two tests + add scope tests to `juniper-ci-tools/tests/`.
0.5 Bump 0.8.0 (pyproject + `_version.py`); CHANGELOG `Added`.
0.6 `juniper-ci-tools/README.md` + juniper-ml `AGENTS.md` note the two new scripts.

**Acceptance:** ci-tools CI green; `python -m build` from `juniper-ci-tools/` clean; class guard +
lockstep + drift tests pass; modules pass ci-tools **ruff** (`select E,F,W,B,I,N`, 512) (§7 R2);
`juniper-symbol-loss-check --help` / `juniper-docs-additions-check --help` resolve; default-scope
run byte-identical to the pre-migration util script on a fixture repo.

### Wave 1 — release (owner ceremony)

1.1 Author `notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.8.0.md` from
    `notes/templates/TEMPLATE_RELEASE_NOTES.md`.
1.2 Cut a **GitHub Release** with tag `juniper-ci-tools-v0.8.0` (never a bare `git push <tag>`) —
    `publish-ci-tools.yml` fires on the release event: TestPyPI (install-verify) → **owner-gated
    PyPI (Gate 2)**. The release-train `detect` will also classify it (`BUMPED_NOT_RELEASED` →
    `RELEASED`).

**Acceptance:** `pip install "juniper-ci-tools==0.8.0"` from a clean venv exposes both console
scripts; `juniper-symbol-loss-check --json` runs on a throwaway repo.

### Wave 2 — consumer rollout matrix (six new repos, one PR each)

Each PR adds two advisory workflows + an `AGENTS.md` co-change + the pin, and **nothing else** (so it
is file-disjoint from any live fleet PR):

- `sequence-safety.yml` — **per-PR advisory** (`on: pull_request`; `concurrency` per-PR ref +
  `cancel-in-progress: true`; `pip install "juniper-ci-tools>=0.8.0,<0.9.0"`; run
  `juniper-symbol-loss-check --scope <repo globs> --base <pr base sha> --head HEAD` +
  `juniper-docs-additions-check --base <base> --head HEAD`; `allow-symbol-loss`/`docs-rewrite`
  labels → `--advisory`; upload `sequence-safety-report`). Ports the ml `ci.yml` advisory job (= the
  cascor standalone workflow).
- `main-verify.yml` — **post-merge, bypass-proof** (`on: push: [main]`; `concurrency: group:
  main-verify-${{ github.sha }}` + `cancel-in-progress: false`; catch-up-base resolver; stable-title
  tracking-issue notify; non-blocking Slack). **Screens-only — no battery job** (per-repo battery is
  deferred, §6).

| Repo | Symbol `--scope` | Notes / quirk | Order |
|---|---|---|---|
| juniper-data-client | `juniper_data_client/**` + `tests/**` | small; black/flake8 | 1 |
| juniper-cascor-client | `juniper_cascor_client/**` + `tests/**` | small | 2 |
| juniper-cascor-worker | `juniper_cascor_worker/**` + `tests/**` | black+ruff | 3 |
| juniper-data | `juniper_data/**` | **ruff-only** repo — the two YAML + AGENTS.md edits must be ruff/yamllint-clean (migrated *code* lives in ci-tools, already ruff-formatted) | 4 |
| juniper-canopy | `src/**/*.py` | heavy suite + UI split; screens-only keeps cost seconds (no battery) | 5 |
| juniper-deploy | minimal / omit (D3) | compose/YAML/Helm — **docs screen is the value**; symbol scope minimal; consider higher `--min-run` (D6) | 6 |

Pin ceiling `>=0.8.0,<0.9.0` (house `>=X,<X+1` minor window). **Recommend also widening the existing
dep-docs pin `<0.7.0`→`<0.9.0` in the same PR** to heal the latent drift (D4). **Sequencing vs the
storm:** consumer PRs are file-disjoint from fleet PRs; run `gh pr list` dup-guard first (memory:
concurrent-session discipline); land least-risky → riskiest.

**Acceptance (per repo):** both workflows appear green (advisory) on a smoke PR; the symbol scope
actually screens a planted deletion in the repo's source tree (not a silent no-op); the docs screen
FAILs a planted heading deletion; the pin admits 0.8.0.

### Wave 3 — retrofit the two pioneers (ml + cascor)

3.1 **juniper-ml PR:** switch the `ci.yml` `sequence-safety:` job + `main-verify.yml` from
    `python util/sequence_safety/*.py` to `pip install "juniper-ci-tools>=0.8.0,<0.9.0"` +
    `juniper-symbol-loss-check` (ml relies on the built-in default scope — no `--scope` needed) +
    `juniper-docs-additions-check`; switch `predict_merge` `_SYMBOL_LOSS_CHECK` /
    `_DOCS_ADDITIONS_CHECK` to `python -m juniper_ci_tools.cli_symbol_loss_check` /
    `...cli_docs_additions_check`; **delete `util/sequence_safety/`**; drop the two moved tests from
    the `ci.yml` + `main-verify.yml` enumerated batteries (they now live in ci-tools/tests).
3.2 **juniper-cascor PR:** same switch with `--scope 'src/**/*.py'`; delete cascor's
    `util/sequence_safety/`.
3.3 **Anti-resurrection drift gate:** extend `tests/test_ci_tools_drift.py` to also scan each
    consumer's `sequence-safety.yml` + `main-verify.yml` pins (so the new-screen pin drift is caught
    alongside dep-docs); add a small always-on ml test asserting ml's own tree has **no**
    `util/sequence_safety/*.py` after Wave 3 (resurrection guard). The `cli*.py` class guard already
    covers the two new scripts.

**Acceptance:** ml + cascor CI green off the package; `grep -r sequence_safety util/` empty in both;
`predict_merge` end-to-end verdict unchanged on a fixture; drift gate bites on a synthetic stale pin.

## 6. Deferred / non-goals

Fleet-triage packaging (stays ml-native v1); per-repo Slack notify; per-repo full-battery
`main-verify` jobs; promotion of any advisory workflow to a **required** status check (a per-repo
owner call after soak); the `[tool.juniper_sequence_safety]` pyproject config surface (D2); the
ml#1004-class ergonomic label hatch per repo (labels are honored via `--advisory`, but wiring the
label read into each consumer workflow beyond the two default labels is deferred); ruleset /
`required_signatures` / bypass-actor changes.

## 7. Risks & open questions (owner)

- **R1 — `required_signatures` on all 8 repos.** Rollout-PR commits that reach `main` must be signed.
  Owner-merge via the GitHub UI produces a GitHub-signed merge commit (fine). A **headless**
  task-executor must either be owner-merged or use GitHub-signed API commits (the release-train
  `createCommitOnBranch` pattern); a plain headless `git push` of unsigned commits will be blocked.
- **R2 — ci-tools ruff over the migrated modules.** ci-tools lints `select E,F,W,B,I,N` (512). The
  screens were written under ml's flake8/black; expect a few B/N nits — a Wave-0 fix, not a redesign.
- **R3 — `**` glob on the 3.11 floor.** Mitigated by the tested `_match_scope`; the default path
  never touches the glob engine.
- **R4 — mis-set scope = false green.** A wrong `--scope` silently screens nothing (or over-scopes to
  noise). Mitigation: the Wave-2 per-repo acceptance step plants a deletion and asserts a FAIL.
- **R5 — canopy/data CI cost.** Mitigated by screens-only `main-verify` (seconds; AST + git) and a
  per-PR advisory job that adds seconds to already-heavy CI. Owner confirm acceptable (D5).
- **R6 — release timing + latent pin drift.** Consumers already pin `<0.7.0` (excludes 0.7.1); 0.8.0
  needs a ceiling widen anyway. Decide whether to cut 0.8.0 during or after the live storm and
  whether to heal the dep-docs pin in the same PRs (D4/D7).
- **R7 — #1004 is OPEN.** The post-#1004 module state is taken from the PR diff; Wave 0 must land
  #1004 first or carry its two deltas. Also: after Wave 3, `predict_merge` screens arbitrary cloned
  repos — passing the true-delta via `--files` (scope-agnostic) is the clean cross-repo path (open).

**Three biggest open questions:** (Q1) scope delivery — `--scope` CLI globs per workflow
(recommended) vs a `[tool.juniper_sequence_safety]` pyproject table (D2)? (Q2) does juniper-deploy
get the symbol screen at all (minimal `tests/**` scope) or docs-screen-only (D3)? (Q3) release timing
vs the live storm, and do we heal the pre-existing `<0.7.0` dep-docs pin ceiling in the Wave-2 PRs
(D4/D7)?

## 8. Decision list (owner)

| ID | Decision | Recommendation |
|---|---|---|
| D1 | Version for the new scripts | 0.8.0 (minor) |
| D2 | Scope delivery mechanism | `--scope` CLI args in each workflow; defer pyproject table |
| D3 | juniper-deploy symbol screen | docs-screen-only (symbol scope minimal or omitted) |
| D4 | Heal latent `<0.7.0` dep-docs pin drift in Wave-2 PRs | Yes (widen to `<0.9.0`) |
| D5 | Consumer `main-verify` battery | Defer — screens-only |
| D6 | Docs `--min-run` per repo | Keep 5; raise on deploy if docs FP noise appears |
| D7 | Release timing vs storm | Owner call (recommend after the storm quiesces) |
| D8 | Promote any advisory workflow to required | Later, per-repo, after soak (out of scope now) |

## 9. Per-wave acceptance criteria

Summarized inline per wave (§5). Global gate: no ruleset touched in any repo; every new workflow is a
non-required context; the two inline copies gone after Wave 3; drift + class guards green.

## 10. Rollback

Every wave is reversible without touching branch protection (that is the point of all-advisory):

- **Wave 1 (release):** yank 0.8.0 on PyPI; revert the ml pin; no consumer is affected yet.
- **Wave 2 (per repo):** delete the two advisory workflow files (or pin-freeze). Advisory workflows
  are not required contexts, so removal blocks nothing; the repo returns to its pre-rollout CI.
- **Wave 3 (retrofit):** revert the ml/cascor consumer PR to restore the inline `util/sequence_safety/`
  tree; the package keeps working for the other repos. Because the inline copies are deleted only in
  Wave 3 (after 0.8.0 has soaked), each earlier wave is independently reversible.

---

**References:** [flood-remediation analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md),
[doc-tools migration plan](JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md),
[ci-tools migration plan](JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md),
[notes naming convention](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md). Code paths
(`util/sequence_safety/`, `juniper-ci-tools/`, `.github/workflows/`) are given as plain in-repo refs;
cross-repo paths (`juniper-cascor/...`) are plain refs by design so the doc-links validator stays green.
