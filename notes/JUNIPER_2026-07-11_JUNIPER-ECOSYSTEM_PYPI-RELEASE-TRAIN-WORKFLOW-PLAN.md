# Juniper Ecosystem — Automated PyPI Release-Train Workflow: Design & Implementation Plan

**Project**: Juniper ML Research Platform
**Repository**: cross-repo (`ECOSYSTEM`) — authored in `pcalnon/juniper-ml`
**Author**: planner agent (principal-engineer design author)
**Document Type**: Design-of-record + implementation plan (`-PLAN`)
**Status**: RATIFIED 2026-07-11 — all §14 owner decisions answered and ingested; Phases 0-4 green-lit (Phase 5 = deferred reevaluations)
**Last Updated**: 2026-07-11

---

## 1. Executive summary

This plan designs a **reusable, schedulable "PyPI release train"** for the Juniper ecosystem. Each run
answers one question per package — *does this package have changes that need a PyPI deploy?* — and then
performs the as-needed releases end-to-end under the owner's existing gate policy, stopping at exactly the
right guardrails.

It builds directly on the companion audit
[`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-SURFACE-AUDIT.md`](JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-SURFACE-AUDIT.md)
(hereafter **the audit**), which inventoried all **18 publishable packages** across 8 repos, classified
each (**7 UNRELEASED_CHANGES, 11 UP_TO_DATE, 0 BUMPED_NOT_RELEASED, 0 NEVER_RELEASED**), verified the
`pypi`/`testpypi` environment gates as uniform, and catalogued six drift findings (F-1..F-6). This plan
does **not** redo that inventory; it consumes the audit's §7 detection pipeline as its specification.

The central design idea is a **two-gate, three-mode** machine that removes manual toil *between* the
owner's two real decision points without ever removing the decision points themselves:

- **Gate 1 (kept): the release-proposal PR.** The train never auto-bumps a version. When it finds
  release-worthy changes, it opens a *standard-gated* PR carrying the version bump, the CHANGELOG
  `Unreleased`→versioned move, and the drafted release-notes content. The **owner reviews and merges**
  it. This is a normal, owner-approved PR.
- **Gate 2 (kept, untouched): the `pypi` environment.** Every publish workflow's PyPI job runs inside
  the `pypi` GitHub environment, protected by a **5-minute wait_timer + required reviewer `pcalnon`**
  (audit §3.3, lines 126-136). The train **never** approves, bypasses, or weakens it. An automated run's
  designed **terminal state is "N PyPI deployments PENDING owner approval."**

Between those two gates, the automated ceremony runs hands-free: it archives the release notes (the only
PR permitted to auto-merge, and only behind a structural guard that proves the diff is *nothing but* new
`notes/releases/RELEASE_NOTES_*` files), cuts the GitHub Release (which is the deploy trigger — never a
bare tag), and lets the existing per-package publish workflow push to **TestPyPI** with install
verification. The run then halts at Gate 2.

**Phase 0 alone is a deliverable**: a report-only scheduled run of the detection engine satisfies the
owner's "investigate and analyze which modules need a deploy" requirement without taking any action.

---

## 2. Goals and non-goals

### 2.1 Goals

- **G1** — A deterministic, re-runnable **detection engine** that classifies each of the 18 packages as
  needing a deploy or not, with machine-readable evidence, reusing the audit's §7 pipeline (R1).
- **G2** — A **reusable, self-contained, schedulable workflow** (cron + `workflow_dispatch`) that performs
  the as-needed deployments (R2, R4).
- **G3** — Full reuse of **existing conventions**: release-notes template + Keep-a-Changelog grouping,
  central `notes/releases/` archival, CHANGELOG `Unreleased`→section, SemVer derivation, and the
  Release-is-the-deploy ceremony (R3).
- **G4** — A **gate-exempt path for the notes-archive PR only**, behind a structural guard, with every
  other PR keeping the standard owner gate (R5).
- **G5** — A hands-free **happy path** per already-bumped package: notes → archive PR auto-merge → Release
  → publish → TestPyPI verify, with **no owner action** up to the PyPI gate (R6).
- **G6** — **PyPI production gates preserved exactly** on all repos (R7).

### 2.2 Non-goals

- **N1** — **Not** touching the `pypi` environment protection (wait_timer, required reviewer) on any repo.
  The train reads the gate; it never edits it (R7).
- **N2** — **Not** auto-approving anything except the exempt notes-archive PR. Version bumps, CHANGELOG
  edits, consumer ceiling-bump propagation PRs, and PyPI deployments all keep the standard owner gate.
- **N3** — **Not** a general CI/CD rewrite. The 18 existing `publish*.yml` workflows remain the publishers;
  the train orchestrates *around* them (it decides *when* to cut a Release; the Release still triggers the
  unchanged publish workflow).
- **N4** — **Not** a versioning oracle. SemVer bumps are *proposals* the owner may override in the
  proposal PR.
- **N5** — **Not** in scope: `juniper-deploy` and `juniper-slacker` (audit §2, lines 89-95 — neither is a
  PyPI package).

---

## 3. Current state (grounded in the audit)

The facts below are the audit's, cited for the design that follows. Do not re-derive them.

- **18 publishable packages** across 8 repos + 2 non-packages (audit §1 table, lines 49-70; §8, line 391).
  Homes: 7 in juniper-ml (meta + 6 sub-packages), 3 in juniper-cascor, 3 in juniper-recurrence, 5
  standalone siblings.
- **Version compare is insufficient.** All 18 have `pyproject == PyPI`, so a naive version diff finds
  nothing; the true signal is **release-worthy commits since the last release tag** (audit §7.1, line 344).
- **Two version sources.** 14 packages are static `[project].version`; **model-core + the 3 recurrence
  packages are `dynamic=["version"]`** → read `_version.py __version__` (audit §2, lines 84-87; §7.2).
- **Two trigger models.** 13 workflows fire on `release: published` (audit §3.1, lines 104-110); **5 fire
  on `push: tags`** — `juniper-cascor` `publish-cascor-model.yml` + `publish-protocol.yml`, and
  `juniper-recurrence` `publish-recurrence-app.yml` + `publish-recurrence-client.yml` +
  `publish-recurrence-model.yml` (audit §3.1, lines 111-118; confirmed on disk: the recurrence-model
  workflow triggers `push: tags: - "juniper-recurrence-model-v*"`). The tag model **structurally permits**
  the TAG_ONLY convention violation (F-4).
- **Uniform two-stage publish shape**: build+twine-check → TestPyPI (`environment: testpypi`, ungated) +
  install-verify → PyPI (`environment: pypi`, gated). OIDC trusted publishing, no API tokens (audit §3.2).
- **Gates, must-not-touch, uniform on all 8 publishing repos** (audit §3.3, lines 126-136): `pypi` =
  `required_reviewers=[pcalnon]` **and** `wait_timer=5`; `testpypi` = none.
- **Drift the train must absorb or route around**: **F-1** 3 TAG_ONLY releases; **F-2** 5 missing note
  archives; **F-3** central-vs-local archive split + `_v`/`-v` separator drift; **F-4** 5 tag-triggered
  workflows; **F-5** 8 leaf workflows still use the TestPyPI production-fallback the ml#384 policy warns
  against; **F-6** the juniper-ml worktree's local `origin/main` is stale (detector-correctness constraint)
  (audit §5, lines 260-308).
- **Automation precedent**: `.github/workflows/docs-full-check.yml` — weekly `cron "0 6 * * 1"` +
  `workflow_dispatch` (lines 63-65), clone-all-siblings loop (lines 99-106). **Precedent gap**: its repo
  list (lines 75-83) **omits `juniper-recurrence`** and does not model the multi-package repos; the
  `prompts/agent_templates/data/ecosystem.yaml` `repos:` list (lines 5-13) omits recurrence too.

---

## 4. Detection design (R1) — the release-train detector

The detector is a **`util/` Python driver** obeying the script-placement rule (mandatory `util/`, `/tmp`
prohibited for source), **gated by unittest** exactly like the existing drift checkers — the pattern of
`util/env_floor_drift_check.py` (data-driven env selection, no hardcoded names, explicit exit codes
0/1/2, lines 22-43) and `tests/test_env_floor_drift_check.py` (synthetic fixtures, no network, the house
`sys.path.insert` import idiom). `util/` is not pre-commit-lint-gated, so the unittest **is** the gate.

### 4.1 Inputs — a package registry

A new data file, `util/release_train/registry.yaml` (proposed; does not exist yet), is the single source
of truth for the 18 packages. It captures per-package the facts the audit enumerated so the detector is
data-driven, not hardcoded. Fields per package:

| Field            | Meaning                                                                                                  | Source                            |
|------------------|----------------------------------------------------------------------------------------------------------|-----------------------------------|
| `pypi_name`      | PyPI distribution name                                                                                   | audit §1                          |
| `repo`           | owning GitHub repo                                                                                       | audit §1                          |
| `path`           | subdir scope (`.`, `juniper-ci-tools/`, …; cascor app = repo-minus-subpkgs)                              | audit §1 / §7.4                   |
| `version_source` | `static` (`[project].version`) or `dynamic` (`_version.py`)                                              | audit §2 / §7.2                   |
| `tag_pattern`    | last-release-tag glob (`v*`, `juniper-<pkg>-v*`)                                                         | audit §7.3                        |
| `archive_name`   | central-archive filename template (`RELEASE_NOTES_v<ver>.md` meta; `RELEASE_NOTES_<pkg>_v<ver>.md` else) | procedure §11.3                   |
| `trigger`        | `release` or `tag` (→ target `release` after Phase 0)                                                    | audit §3.1                        |
| `verify`         | `strict` / `fallback` (→ target `strict` except meta)                                                    | audit §3.4 / F-5                  |
| `depends_on`     | upstream packages (for D6 ordering)                                                                      | parent `CLAUDE.md` graph + extras |

Registry drift is itself a lint (`tests/test_release_train_registry.py`, proposed): every registry entry
must resolve to a real `pyproject.toml`, and every ecosystem `pyproject.toml` with a `[project]` table
must appear in the registry — so a newly-added package cannot silently escape the train. The registry
also supersedes the recurrence-omission gap in `ecosystem.yaml`/`docs-full-check.yml` by listing all 8
publishing repos including `juniper-recurrence`.

### 4.2 The per-package detection algorithm (deterministic, re-runnable)

For each registry entry, in this order (mirroring audit §7):

1. **Released truth (PyPI JSON API).** `GET https://pypi.org/pypi/<pypi_name>/json` → `info.version` +
   latest file `upload_time_iso_8601`. This is authoritative for "what is actually deployed" and is
   immune to local/tag drift.
2. **Declared version.** Read `[project].version` (static) or `_version.py __version__` (dynamic). If
   `declared > released` ⇒ **BUMPED_NOT_RELEASED** (skip to §5 ceremony path). If `declared < released`
   ⇒ anomaly ⇒ **HALT + issue** (a yanked/rolled-back state a human must resolve).
3. **Diff base = the tag matching the released version.** Resolve the newest tag under `tag_pattern`
   whose stripped version equals `info.version` (audit §7.3: "prefer the tag that matches the current
   PyPI version").
4. **Remote-authoritative diff.** Compute `<tag>..main` **remote-authoritatively** — default via
   `gh api repos/<owner>/<repo>/compare/<tag>...main` (and `commits?path=&since=` for paging past the
   **300-file page cap**), *not* a local checkout, because local checkouts can be stale (F-6; the audit's
   own worktree was). Path-scope to `path`; for cascor the app scope is "repo minus the two subpkg dirs."
   A `--local-git` mode (fresh `git fetch` + `git log <tag>..origin/main`) exists for offline/dev use only.
5. **SHIP vs NON-SHIP filter** (audit §7.5, lines 357-365) — the correctness crux:
   - **SHIP** — files under the import package dir (`juniper_<pkg>/`, `src/`, `cascor_constants/`, …); or
     `pyproject.toml` `[project].dependencies` / runtime floors / `version`.
   - **NON-SHIP** — `notes/`, `docs/`, `README`/`CHANGELOG`/`AGENTS.md`, `.github/`, **`tests/`
     (including in-package `juniper_data/tests/`)**, `pyproject.toml` `test`-extra deps + pytest config,
     ruff-only lint reformats, and — **the live false-positive trap** — the **2026-07-04 notes-rename
     one-line doc-comment/link edits** that touched shipping `.py` files in data, data-client, and
     cascor-model. A naive "any `.py` under the package changed" rule misclassified **4 UP_TO_DATE
     packages** as needing a deploy. **Rule: a SHIP classification requires a *substantive, non-comment*
     hunk in a SHIP-path file.** The detector inspects the per-file patch text (available inline from the
     compare API) and discounts pure comment/docstring/link edits.
   - **Patch-unavailable fallback**: when GitHub omits the patch (over-large diff), classify
     **SHIP-UNCERTAIN**, never silent-skip — route to the proposal-PR-with-review path (§5).
6. **CHANGELOG `[Unreleased]` corroboration** (audit §7.6). Feature/fix/security bullets corroborate
   SHIP; CI/test/docs-only bullets corroborate NON-SHIP; a self-declared "no version bump" line
   (recurrence-client precedent) is machine-readable intent. **Corroborating, not authoritative** — the
   inverse risk (recurrence-model's real validation change is under-documented in `Unreleased`) means the
   commit-diff signal wins on conflict, and any conflict is surfaced in the manifest for human eyes.
7. **SemVer proposal** (§6). Derive a proposed bump from the `Unreleased` categories + commit-message
   classes. Advisory only.
8. **Release-hygiene flags** (orthogonal to "needs deploy"): `gh release view <tag>` == "release not
   found" ⇒ **TAG_ONLY**; missing central `notes/releases/RELEASE_NOTES_*<ver>*` ⇒ **NOTES_MISSING**
   (audit §7.7).

### 4.3 Output — the release manifest

The detector emits a machine-readable **release-manifest JSON** (and a human table + `--json`), one
record per package:

```json
{ "pypi_name": "...", "repo": "...", "released_version": "...", "declared_version": "...",
  "diff_base_tag": "...", "classification": "UNRELEASED_CHANGES | UP_TO_DATE | BUMPED_NOT_RELEASED |
     NEVER_RELEASED | SHIP_UNCERTAIN | ANOMALY",
  "proposed_bump": "minor|patch|major|none", "proposed_version": "...",
  "ship_evidence": [ {"file": "...", "reason": "substantive hunk|pyproject-runtime"} ],
  "nonship_discounted": [ {"file": "...", "reason": "notes-rename-comment|tests|ruff"} ],
  "changelog_unreleased_categories": ["Added","Fixed",...],
  "hygiene": {"tag_only": bool, "notes_missing": bool},
  "propagation_edges": [ {"consumer": "...", "reason": "escapes <ceiling pin"} ] }
```

Exit codes follow the house convention: `0` = clean scan, `1` = at least one package needs action
(UNRELEASED_CHANGES / BUMPED_NOT_RELEASED / anomaly), `2` = invocation/network error (a scan failure is a
hard stop, not a silent empty result).

**Phase 0 = run this in report-only mode on a schedule.** That alone satisfies R1: it *investigates and
analyzes* which modules and sub-modules need a deploy, with evidence, and takes no action.

---

## 5. Per-package release state machine

The machine has **two entry paths into a release**, which is what keeps the owner in control while
automating the toil.

### 5.1 States

| State                   | Meaning                                                 | Who acts                                                                       |
|-------------------------|---------------------------------------------------------|--------------------------------------------------------------------------------|
| `UP_TO_DATE`            | No release-worthy change since the diff-base tag.       | Train: nothing.                                                                |
| `UNRELEASED_CHANGES`    | Release-worthy commits, version **not** bumped.         | Train opens a **standard-gated proposal PR**; **owner** reviews/merges.        |
| `BUMPED_NOT_RELEASED`   | `declared > released`; no Release cut yet.              | Train runs the **automated ceremony** (exempt archive PR + Release + publish). |
| `NEVER_RELEASED`        | Not on PyPI at all (0 today).                           | Train ceremony **after** a trusted-publisher-config precheck; else HALT.       |
| `RELEASING`             | Ceremony in flight (concurrency-guarded).               | Train.                                                                         |
| `PENDING_PYPI_APPROVAL` | TestPyPI done; PyPI job waiting at the `pypi` env gate. | **Owner** approves the deploy. Terminal-healthy.                               |
| `HALTED`                | A precondition failed.                                  | Train opens/updates a **GitHub issue**; no further action on this package.     |

`TAG_ONLY` and `NOTES_MISSING` are **orthogonal hygiene flags**, not deploy-needing states; they feed
Phase 0 pre-work and the observability summary, not the ceremony.

### 5.2 Transitions

```bash
UP_TO_DATE ──(new substantive SHIP commit)──▶ UNRELEASED_CHANGES
UNRELEASED_CHANGES ──(owner merges proposal PR: version bump + CHANGELOG move)──▶ BUMPED_NOT_RELEASED
BUMPED_NOT_RELEASED ──(train: exempt archive PR auto-merges + Release cut)──▶ RELEASING
RELEASING ──(publish workflow: TestPyPI publish + install-verify OK)──▶ PENDING_PYPI_APPROVAL
PENDING_PYPI_APPROVAL ──(owner approves `pypi` env)──▶ UP_TO_DATE  (declared == released again)
any ──(precondition fails, §8)──▶ HALTED ──▶ issue
```

### 5.3 Why this reconciles R6 with R5/R7

R6's hands-free happy path (`generate notes → archive PR auto-merges → Release cut → publish → TestPyPI
verify → no owner action`) is precisely the **`BUMPED_NOT_RELEASED` → ceremony** arc. The version bump that
*makes* a package `BUMPED_NOT_RELEASED` arrived earlier via the **owner-approved proposal PR** (Gate 1),
and the PyPI deploy at the end still waits at the **`pypi` env gate** (Gate 2). So the automation touches
only the middle — notes authoring/archival, Release cutting, TestPyPI verification — never a version bump
without approval and never a PyPI deploy without approval. **The audit found 0 packages in
`BUMPED_NOT_RELEASED` today** (audit §8), so the ceremony path has no live inputs until the first proposal
PR merges — which makes juniper-ml sub-packages the natural, safe Phase-3 pilot.

### 5.4 Version + CHANGELOG handling (D2) — the proposal PR

Because only the notes-archive PR is gate-exempt (§7), **all version + CHANGELOG changes ride the standard
owner gate** inside one **release-proposal PR** per package, generated by the train from the manifest:

- **`pyproject.toml` / `_version.py`** version bump to `proposed_version`.
- **CHANGELOG**: move `[Unreleased]` bullets into a new `[<version>] - <date>` section, preserving the
  Keep-a-Changelog grouping (`CHANGELOG.md:5` declares KaC + SemVer; `:8` `[Unreleased]`; `:27`
  `[0.6.0] - 2026-05-23` is the section shape to emulate). A fresh empty `[Unreleased]` is left behind.
- **Drafted release-notes content** (from the template, §6) included in the PR body / a draft file for the
  owner to review — but **not** yet archived to `notes/releases/` (archival is the later exempt step).
- **Atomicity co-changes** the PR must carry so it lands green in one merge:
  - **AGENTS.md `**Version**` header** — kept in lockstep with `pyproject.toml` by
    `tests/test_agents_md_version_drift.py`; the meta-package bump must edit AGENTS.md in the same PR.
  - **`_version.py` `__version__` lockstep** — a static-version package that also ships a `_version.py`
    dunder (all five in-repo static packages) must have the dunder bumped in the same PR, or the shipped
    wheel's `__version__` lies (the ci-tools 0.7.0 / service-core 0.5.0 stale-dunder incidents; design
    [ml#701 follow-up doc](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)).
    `propose.py` emits this co-change automatically, auto-detected by `_version.py` presence (no registry
    field); the always-on gate is `tests/test_release_train_registry.py` (`VersionDunderLockstepTest`).
  - **Lockfile regeneration** after any runtime-floor bump (memory: "regen on floor bump or gate fails").
  - **Version+pin+lint atomicity** — the model-core precedent: bump, the consumer pin, and the drift-lint
    contract move together (memory: model-core crossval roadmap).
  - **Consumer ceiling propagation** — a **pre-1.0 MINOR bump escapes a consumer's `<next-minor` ceiling
    pin** (see §6), so it needs *coordinated ceiling-bump PRs* in the consumers. These are emitted as
    `propagation_edges` and become **separate, standard-gated follow-on PRs (D6)** — never folded into the
    exempt path. This is the exact failure class of the **2026-07-06 ci-tools incident** (six consumer
    pins `<0.5.0`→`<0.7.0` when ci-tools shipped 0.6.0; the audit references it as the pattern to avoid).

The proposal PR is **dup-guarded**: before opening one, the train runs `gh pr list` for an existing open
release PR for that package (concurrent Claude sessions are a real hazard — memory: "gh pr list dup-guard
first") and refreshes rather than duplicates.

---

## 6. SemVer derivation (D3)

Bumps are **proposals**; the owner may override in the proposal PR. Derivation combines two signals:

- **CHANGELOG `[Unreleased]` categories**: `Added`/`Changed`(non-breaking) ⇒ feature; `Fixed` ⇒ fix;
  `Security` ⇒ fix (or feature if it adds API surface); `Changed`(breaking) / `Removed` ⇒ breaking.
- **Commit-message classes** (Conventional-Commits-ish, as used across the fleet): `feat` ⇒ feature;
  `fix` ⇒ fix; `feat!`/`fix!`/`BREAKING CHANGE` ⇒ breaking.

**Pre-1.0 policy (the entire fleet is 0.x today).** The ecosystem pins consumers as
`>=floor,<next-minor` (e.g. `juniper-ci-tools>=0.1.0,<0.7.0`, `juniper-model-core>=0.1.0,<0.4.0`), which
makes **each `0.x` a compatibility boundary**. Therefore, pre-1.0:

| Change class            | Bump                            | Consumer impact                                        |
|-------------------------|---------------------------------|--------------------------------------------------------|
| breaking **or** feature | **MINOR** (`0.x.0`→`0.(x+1).0`) | Escapes `<next-minor` ceilings ⇒ propagation PRs (D6). |
| fix only                | **PATCH** (`0.x.y`→`0.x.(y+1)`) | Within ceilings; no propagation.                       |

**Post-1.0 (stated for the future, none apply today)**: breaking ⇒ MAJOR, feature ⇒ MINOR, fix ⇒ PATCH.
The precedent for the pre-1.0 rule is the CHANGELOG's own 0.5.0→0.6.0 "semver minor: existing callers … up
to the new floor minimums" note (`CHANGELOG.md:51-53`).

---

## 7. Gate & exemption policy (R5/R7) — the load-bearing guardrail

### 7.1 Verbatim-intent statement

- **R5** — The PR that **archives the generated release notes and contains no other changes** is exempt
  from the standard owner-approval gate and may auto-merge — **but only behind a structural guard job
  proving the diff is exactly new file(s) under `notes/releases/` matching the `RELEASE_NOTES_*` naming
  pattern (no modifications, no deletions, no other paths).** Every other PR keeps the standard owner gate.
- **R7** — The `pypi` environment's `wait_timer` (5 min) + required reviewer (`pcalnon`) stay exactly
  as-is on all repos; automation **never** approves, bypasses, or weakens them. The run ends with PyPI
  deployments **PENDING owner approval** — the designed terminal state.

### 7.2 Structural-guard job design

A required CI job on the archive PR (proposed `tests/test_release_train_archive_guard.py` driven by a
`.github/workflows/` guard lane, or a small composite action) computes the PR's file-change set against
the base and **passes only if all** hold:

1. **Add-only** — every change is status `A` (added). Any `M` (modified) or `D` (deleted) ⇒ **fail**.
2. **Path-confined** — every added path matches `^notes/releases/RELEASE_NOTES_.*\.md$`.
3. **Name-valid** — each added file matches the archive convention: `RELEASE_NOTES_v<semver>.md` (meta) or
   `RELEASE_NOTES_<pkg>_v<semver>.md` (every other package), with `<pkg>` a registry `pypi_name` and
   `<semver>` the package's `declared_version` (procedure §11.3, lines 505-509; naming exemption for
   `notes/releases/` in the naming convention, lines 43-51).
4. **Single-purpose** — no other path in the diff, at all.

If the guard **passes** and required checks are green, the train enables merge via
`gh pr merge --auto --squash`. If the guard **fails**, the PR is untouched and **falls back to the
standard owner gate** — it never auto-merges. The guard is added to the target repo's **required status
checks** so `--auto` cannot complete until it passes (auto-merge honours required checks).

### 7.3 Auto-merge preconditions (owner config, called out honestly)

`gh pr merge --auto` needs three repo-level conditions the implementation must confirm (not assumed):

- **"Allow auto-merge"** enabled in the target repo settings.
- The **structural-guard job is a required status check** in the branch ruleset.
- **No required human PR review** on `notes/releases/` paths that would block `--auto`. Since CODEOWNERS is
  `@pcalnon` for all files, a repo-wide required-review ruleset would hold the exempt PR for owner review —
  degrading "auto-merge" to "owner one-click merge."
  **Decided (Q-RULESET, 2026-07-11): path-scope the required-review ruleset to exclude `notes/releases/`** —
  true hands-free auto-merge for the guard-proven archive PR. The ruleset edit is an owner-console action,
  landed and confirmed at Phase 3 step 3.3; until it lands, the exempt PR degrades gracefully to the
  one-click fallback. This plan still does **not** assert the current ruleset contents — step 3.3 verifies
  them before relying on `--auto`.
  **Verified at 3.3 (2026-07-20): the live ruleset carries no required-review rule, so the path-scope is
  moot as configured** — no ruleset edit for reviews was needed; see the dated §12 step-3.3 entry for the
  full landed state (auto-merge flag + guard-as-required-check).

### 7.4 Why the exempt PR cannot leak into a deploy (R7 preserved)

Auto-merging the archive PR **merges a Markdown file to `main`; it deploys nothing.** The deploy is the
subsequent **Release cut**, which triggers the *unchanged* `publish*.yml`, whose PyPI job sits inside the
`pypi` environment and **waits for `pcalnon`**. Even though a bot identity cuts the Release, that identity
is **never added as a `pypi` environment reviewer** (a hard invariant, §9.3), so it cannot self-approve.
TestPyPI (ungated by design, audit §3.3) is the smoke-test stage; PyPI is always owner-gated.

---

## 8. "Nothing unexpected" preconditions (D7) — any failure halts that package

Each precondition is checked **per package** before the ceremony proceeds; **any failure → HALT that
package, open/update a GitHub issue, never proceed** (a halt on one package does not block the others):

| Precondition                           | Check                                                                                                                                                                          | Rationale / memory                                                                                                                                  |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| **Target main CI green**               | `gh run list --branch main --repo <repo>` latest = success.                                                                                                                    | Owner rule: "check main green before blaming a red PR." A red main means don't release.                                                             |
| **No open release PR for the package** | `gh pr list` dup-guard.                                                                                                                                                        | Concurrent Claude sessions are a real hazard (memory).                                                                                              |
| **Remote freshness**                   | Remote-authoritative diff only (§4.2); no local-checkout truth.                                                                                                                | F-6: the ml worktree was stale and would under-count.                                                                                               |
| **Declared ≥ released**                | §4.2 step 2.                                                                                                                                                                   | `declared < released` ⇒ yanked/rolled-back anomaly ⇒ HALT.                                                                                          |
| **TestPyPI install-verify success**    | The publish workflow's own verify step must pass.                                                                                                                              | **Hard gate**: the run is "healthy" only if TestPyPI verify passed before Gate 2.                                                                   |
| **Idempotent re-entry**                | PyPI/TestPyPI files are immutable; publish steps already use `skip-existing: true` (`publish-service-core.yml:139,185`); the train re-computes state from PyPI truth each run. | A re-run after partial failure resumes at the correct state (a half-cut Release ⇒ package is `RELEASING`/`PENDING_PYPI_APPROVAL`, not re-proposed). |
| **One train at a time**                | Workflow `concurrency: group: release-train, cancel-in-progress: false` (the `publish-service-core.yml:48-53` pattern).                                                        | No two trains racing the same immutable index.                                                                                                      |

**Trusted-publisher precheck for `NEVER_RELEASED`** (none today, but required for a first publish): confirm
the PyPI/TestPyPI pending-publisher config exists for the repo+workflow+environment before attempting
(procedure §3.3, lines 157-169); else HALT with an issue — the train never blindly first-publishes.

---

## 9. Automation architecture (D5)

### 9.1 Orchestrator: a scheduled GitHub Actions workflow in juniper-ml

**Recommendation: primary orchestrator is `.github/workflows/release-train.yml` in `juniper-ml`**
(proposed; does not exist yet), reusing the `docs-full-check.yml` clone-all scaffold with the recurrence
gap fixed. Rationale:

- The audit's automation precedent is exactly this shape (weekly cron + `workflow_dispatch` + clone-all),
  already trusted and reviewed (`docs-full-check.yml:63-106`).
- juniper-ml is the ecosystem's tooling hub and the **central `notes/releases/` archive home** (procedure
  §11.3) — the exempt archive PR is *always* against juniper-ml, so the guard + auto-merge live in one
  repo the owner already watches.
- The detector and its unittest gate live in juniper-ml's `util/` + `tests/`, consistent with every other
  drift checker.

**Why GitHub Actions over a Claude Code scheduled routine (weighed, per D5):** a Claude Code routine could
run the same driver, but Actions is preferred as the *primary* because (a) it is auditable and
reproducible with pinned action SHAs (the fleet convention — see `publish.yml:48` pinned checkout), (b) it
already holds the OIDC + environment plumbing, (c) it needs no always-on host, and (d) the owner's
"verify-before-first-cron" discipline (memory) applies cleanly to a `workflow_dispatch`. A Claude Code
routine remains a viable **fallback operator** for ad-hoc re-runs and for the judgement-heavy proposal-PR
*authoring* (release-notes prose), invoked manually — but the scheduled backbone is Actions.

### 9.2 Cross-repo write identity (PAT vs GitHub App)

`GITHUB_TOKEN` is single-repo, so cross-repo PRs and Releases (Phase 4: cascor, canopy, data, recurrence,
etc.) need a broader identity. Two options:

- **Fine-grained PAT** (secret e.g. `RELEASE_TRAIN_PAT`), scoped to the 8 publishing repos with
  `contents: write` (branches, tags, Releases) + `pull_requests: write`. Simple; but tied to Paul's
  account and carries an expiry to rotate.
- **GitHub App** (installation token), scoped to the same repos + permissions, not tied to a personal
  account, auto-rotating. Higher one-time setup.

**Recommendation: GitHub App for the durable fleet-wide identity; a fine-grained PAT is an acceptable
bootstrap for the Phase-3 pilot** — and the pilot (juniper-ml sub-packages) is **in-repo**, so its archive
PR + Release need only the workflow's own `GITHUB_TOKEN` (contents+PR write on juniper-ml), deferring the
PAT/App decision to the Phase-4 boundary.

**Decided (Q-IDENTITY, 2026-07-11): as recommended — GitHub App** for the durable fleet-wide identity,
set up at the Phase-4 boundary (step 4.1); the Phase-3 pilot runs on the workflow's own `GITHUB_TOKEN`
and needs neither. A fine-grained PAT remains a documented fallback only if App setup would stall Phase 4.

### 9.3 Hard invariant on the write identity (R7)

The release-train identity (PAT or App) is used **only** for: opening PRs, enabling auto-merge on the
exempt PR, and `gh release create`. It is **never** added as a reviewer on any `pypi` environment and
**never** granted deployment-approval rights. PyPI approval remains `pcalnon`-only (memory: "deploy
approvals are Paul's alone"). A guard test asserts the workflow contains no environment-mutating API calls.

### 9.4 Proposed file layout (all paths below are future — none exist yet)

```bash
util/release_train/
  __init__.py
  registry.yaml            # the 18-package registry (§4.1)
  detect.py                # detection engine → release-manifest JSON (§4.2/4.3)  [report-only in Phase 1]
  propose.py               # manifest → standard-gated proposal PR (§5.4)          [Phase 2]
  ceremony.py              # BUMPED_NOT_RELEASED → exempt archive PR + Release cut  [Phase 3]
  notes_render.py          # template-driven notes generation (§10)
tests/
  test_release_train_registry.py     # registry↔pyproject drift lint (§4.1)
  test_release_train_detect.py       # detector classification, synthetic fixtures, no network (§4.2)
  test_release_train_archive_guard.py# structural-guard proof (§7.2)  [the R5 guard]
  test_release_train_propose.py      # proposal-PR content + dup-guard (§5.4)
  test_release_train_ceremony.py     # ceremony ordering + PyPI-untouched invariant (§9.3)
.github/workflows/
  release-train.yml        # scheduled orchestrator (cron + dispatch), modes off|report|propose|ceremony
```

Mode is a **repo variable** `RELEASE_TRAIN_MODE ∈ {off, report, propose, ceremony}` (default `report`),
plus a `workflow_dispatch` input override — this is also the **disable/rollback switch** (§11).

Notifications use a repository secret **`SLACK_WEBHOOK_URL`** (owner-provisioned incoming webhook for the
Juniper Slack channel; §11, Q-CHANNEL). It is the only secret the train adds; absence of the secret skips
the notification step and never fails a run.

---

## 10. Release-notes generation & archival (D4) — resolving F-3

### 10.1 Generation

Notes are **template-driven** from
[`templates/TEMPLATE_RELEASE_NOTES.md`](templates/TEMPLATE_RELEASE_NOTES.md) (structure at lines 19-258;
naming `RELEASE_NOTES_v[VERSION].md`, location `notes/releases/`, lines 7-9). Content is organized by the
same **Keep-a-Changelog groups** the CHANGELOG uses, sourced from the versioned CHANGELOG section the
proposal PR created. When the release is security-bearing (several UNRELEASED_CHANGES items are — cascor
SEC-F19/F22, service-core SEC-F01, audit §4.A), the train selects
[`templates/TEMPLATE_SECURITY_RELEASE_NOTES.md`](templates/TEMPLATE_SECURITY_RELEASE_NOTES.md) instead
(the `Security` CHANGELOG category is the trigger). The **Release body is sourced from the archived notes
file** (`gh release create --notes-file …`, procedure §11.4, lines 522-528).

### 10.2 Archival location — central is canonical (resolving F-3)

**Recommendation: the central `juniper-ml/notes/releases/` archive is the canonical, single source of
truth for every package** (honouring procedure §11.3, lines 497-509), with the `_v` separator
(`RELEASE_NOTES_<pkg>_v<ver>.md`). Rationale: it is the ratified convention, it gives one fleet-wide
auditable record, the orchestrator lives in juniper-ml so it writes there natively, and the structural
guard then only ever reasons about one repo's layout. Consequences:

- The **exempt archive PR is always against juniper-ml**, even for a cascor/canopy/recurrence release.
- The **Release is cut on the owning repo**; its `--notes-file` is the just-archived central file (fetched
  into the ceremony runner).
- **App-repo local `notes/releases/`** practice (canopy/data/recurrence keep local copies today, audit
  F-3) is *permitted but non-canonical*: if a repo wants a local mirror, that copy is folded into its
  **standard-gated proposal PR** (owner-gated), keeping the exempt path single-repo and pure.

**F-3 migration** (Phase 0): backfill the central archive for the 5 NOTES_MISSING packages (doc-tools,
observability, cascor-protocol, canopy, cascor-worker — audit F-2) and the stale recurrence entries
(central stops at recurrence-model `_v0.1.2`; add `_v0.1.5` + the app/model `_v0.2.0`), normalizing any
`-v` to `_v`. This is a normal PR (backfilling history, not train output).

---

## 11. Failure handling, observability & rollback (D8)

- **Per-run summary** — a `GITHUB_STEP_SUMMARY` table of every package's classification + action, plus the
  release-manifest JSON as an uploaded **artifact** (the `docs-full-check.yml` reporting style). The
  terminal announcement is explicit: **"N PyPI deployments PENDING owner approval at &lt;env URLs&gt;"**
  with the `pypi` environment URLs.
- **Failure issues** — any HALT (§8) opens or updates a single deduplicated GitHub issue per package
  (title keyed on `pypi_name` + reason), never a flood.
- **Slack notification (Q-CHANNEL, decided 2026-07-11)** — each run posts a compact summary to the
  **Juniper Slack channel** via an owner-provisioned incoming-webhook secret (`SLACK_WEBHOOK_URL`, §9.4):
  run mode, classification counts, packages newly `PENDING_PYPI_APPROVAL` (with their `pypi` env URLs),
  and any HALTs. The step is **non-blocking** (`if: always()` + `continue-on-error: true` — a notification
  failure or a missing secret never fails the train) and posts only the summary (no secrets, no diff
  content). This restores a Slack signal via a self-contained webhook — it neither resurrects the removed
  slack MCP server (2026-06-15) nor depends on the non-packaged `juniper-slacker` bridge (audit §2). The
  step summary + dedup issues remain the canonical, auditable record; Slack is additive.
- **Rollback / disable** — set `RELEASE_TRAIN_MODE=off` (repo variable) to pause the train instantly with
  no code change; `report` to keep detection running while pausing all writes. Because PyPI files are
  immutable and the publish steps are `skip-existing`, a partial run is safe to re-enter.
- **Verify-before-first-cron** — mandatory: after each phase lands, trigger `release-train.yml` via
  `gh workflow run` immediately and confirm the run behaves before trusting the daily cron (memory:
  "verify any new scheduled workflow with an immediate manual run"; a lint-green workflow is not a
  runtime-green workflow).

---

## 12. Phased implementation plan (D9)

Each numbered step is a single, independently shippable, independently verifiable work unit
(PR-sized). No step depends on a later step.

### Phase 0 — Pre-work: close the drift that blocks a clean train (unblocks R3/F-4/F-3)

- **0.1** Migrate the 5 `push: tags` publish workflows to `release: published` (F-4), one PR per repo:
  `juniper-cascor` (`publish-cascor-model.yml`, `publish-protocol.yml`) and `juniper-recurrence`
  (`publish-recurrence-app.yml`, `publish-recurrence-client.yml`, `publish-recurrence-model.yml`). Model
  on `publish-service-core.yml:34-53` (single `release: published` trigger + concurrency group +
  tag-prefix `if:` guard + the `#555` double-fire rationale). **Verify**: `workflow_dispatch` dry-run + the
  next real Release for each fires exactly one publish run (no double-fire).
- **0.2** Standardize the 8 TestPyPI-fallback leaf workflows to strict `--no-deps` (F-5), keeping the
  meta's documented exception (`publish.yml:103-121`). Model on `publish-service-core.yml:150-157`. One PR
  per repo/package. **Verify**: `tests/test_workflow_script_paths.py` stays green; a dispatch shows the
  verify step resolves target-only.
- **0.3** Backfill the central archive (F-2/F-3): add the 5 missing `RELEASE_NOTES_*` files + the stale
  recurrence entries, normalize `-v`→`_v` (§10.2). Standard-gated PR in juniper-ml. **Verify**: every
  released version in the audit §1 table has a matching central archive file.
- **0.4** (optional, owner-gated) Backfill the 3 TAG_ONLY Releases (F-1) or explicitly accept them as
  legacy in the audit's ledger. **Verify**: `gh release view <tag>` resolves, or a documented waiver.

### Phase 1 — Detection engine, report-only (delivers R1)

- **1.1** `util/release_train/registry.yaml` + `tests/test_release_train_registry.py` (registry↔pyproject
  drift lint, §4.1). **Verify**: unittest green; all 18 packages + 8 repos present incl. recurrence.
- **1.2** `util/release_train/detect.py` + `tests/test_release_train_detect.py` (synthetic fixtures, no
  network, `sys.path.insert` idiom; §4.2/4.3). **Verify**: on the real fleet it reproduces the audit's **7
  UNRELEASED_CHANGES / 11 UP_TO_DATE / 0 BUMPED_NOT_RELEASED**, and the 4 notes-rename false-positives stay
  UP_TO_DATE.
- **1.3** `.github/workflows/release-train.yml` in `report` mode only: cron `0 13 * * *` (Q-CADENCE: daily 13:00 UTC = 08:00 America/Chicago under CDT; GitHub cron is UTC-only, so winter runs land 07:00 CST — accepted drift) + `workflow_dispatch` + `concurrency` + clone-all (recurrence added), runs `detect.py`, emits the manifest artifact + step summary. No PRs, no Releases. **Verify**: immediate `gh workflow run` (verify-before-first-cron); manifest matches 1.2.
- **1.4** Slack notification lane (Q-CHANNEL): add the non-blocking summary post (§11) to `release-train.yml`, keyed on the `SLACK_WEBHOOK_URL` secret. **Owner action**: create the incoming webhook for the Juniper Slack channel and add the repo secret. **Verify**: a manual dispatch posts the summary to the channel; with the secret absent the step skips and the run still succeeds.

### Phase 2 — Proposal-PR generation (standard-gated; delivers Gate 1 of R2/D2)

- **2.1** `util/release_train/notes_render.py` + `propose.py` + `tests/test_release_train_propose.py`:
  from the manifest, generate the version bump + CHANGELOG move + drafted notes + AGENTS.md/lockfile/pin
  co-changes + `propagation_edges`; dup-guard via `gh pr list`. **Verify**: unit tests; a dry-run prints a
  well-formed PR without opening it.
- **2.2** Wire `propose` mode into `release-train.yml` (opt-in via dispatch input / `RELEASE_TRAIN_MODE`).
  In-repo pilot uses `GITHUB_TOKEN`; cross-repo deferred to Phase 4. **Verify**: dispatch `propose` against
  **one** juniper-ml sub-package; owner reviews the generated PR end-to-end.

### Phase 3 — Automated ceremony for ONE pilot family: juniper-ml sub-packages (delivers R5/R6)

- **3.1** The structural-guard lane + `tests/test_release_train_archive_guard.py` (§7.2). **Verify**: guard
  passes a pure-notes diff, fails on any modify/delete/other-path (synthetic negative cases).
- **3.2** `util/release_train/ceremony.py` + `tests/test_release_train_ceremony.py`: for
  `BUMPED_NOT_RELEASED`, build the final central notes file, open the exempt archive PR, enable
  `gh pr merge --auto` behind the guard, cut the Release (`--latest=false` for a sub-package, procedure
  §11.4 lines 525-528), monitor the publish run, report `PENDING_PYPI_APPROVAL`. Assert the PyPI-untouched
  invariant (§9.3). **Verify**: end-to-end on a **real low-risk juniper-ml sub-package bump** (e.g. the next
  observability/ci-tools patch): archive PR auto-merges, Release fires the unchanged publish workflow,
  TestPyPI verify passes, PyPI **waits for owner** — confirm the run halts at Gate 2.
- **3.3** Confirm the auto-merge preconditions (§7.3) on juniper-ml and land the Q-RULESET decision: path-scope the required-review ruleset to exclude `notes/releases/` (owner console action). **Verify**: a guard-green synthetic archive PR completes `--auto` merge with no human click; document the resulting ruleset state here.
  - **LANDED 2026-07-20 (API, owner-directed).** Resulting state of ruleset `juniper-ml-rules` (id 13805432, target main, active): (1) repo flag `allow_auto_merge=true`; (2) `Release-Train Archive Guard` appended as the 13th required status check (the ci.yml guard lane runs on every PR and passes with a SKIP verdict on non-archive diffs, so requiring it blocks nothing else); (3) **Q-RULESET path-scope is moot as configured** — inspection showed the ruleset contains NO `pull_request` required-review rule at all (only 13 required checks, `required_signatures`, deletion/non-FF/creation/update, CodeQL scanning), so there is no review requirement to path-scope and §7.3's CODEOWNERS-hold concern does not arise; (4) `required_signatures` is satisfied on the auto-merge path because GitHub signs its own squash/merge commits; (5) bypass_actors: repository admins + 3 integrations bypass `always` (pre-existing). **Live verify deliberately deferred**: a synthetic archive PR would merge a junk notes file into `notes/releases/` (and a name-valid one would pre-empt a real future archive), so the no-human-click `--auto` proof rides the next REAL archive PR — the Phase-4 cascor-client ceremony, whose exempt archive PR lands in juniper-ml. Rollback: pre-change ruleset JSON captured session-side; revert = PUT it back + `allow_auto_merge=false`.

### Phase 4 — Fleet-wide + dependency ordering (delivers R2 at scale/D6)

- **4.1** Cross-repo write identity (GitHub App per Q-IDENTITY, §9.2; PAT only as documented fallback) +
  secret wiring; extend `propose.py`/`ceremony.py` to open cross-repo PRs and cut cross-repo Releases.
  **Verify**: `propose` mode against one sibling (e.g. cascor-worker) opens a PR in that repo.
- **4.2** Dependency-ordered scheduling (§13/D6): process shared libs → sub-libs → apps → meta; emit
  consumer ceiling-bump follow-on PRs (standard-gated, ordered upstream-first). **Verify**: a simulated
  upstream MINOR bump produces the expected downstream propagation edges.
- **4.3** Full `off|report|propose|ceremony` switch + operator runbook (a `notes/` doc) + explicit rollback
  steps. **Verify**: `RELEASE_TRAIN_MODE=off` fully quiesces the train.

### Phase 5 — Deferred reevaluations (tracking homes for Q-META / Q-NONSHIP)

These are **not** green-lit work; they are dated tracking entries so the deferred decisions cannot be lost.

- **5.1** **Q-META reevaluation (decided 2026-07-11: meta stays manual for now — revisit later).** After
  Phase 4 has run stably fleet-wide (suggested threshold: ≥2 consecutive clean scheduled cycles),
  reevaluate whether the `juniper-ml` meta-package rides the train. Inputs: the meta's bespoke
  extras-resolution TestPyPI verify (`publish.yml:105-121`), its releases-LAST position in the §13 DAG,
  and the observed reliability of the sub-package ceremony. **Verify / exit criterion**: a dated decision
  is appended to this step (ride vs stay manual); if "ride", the implementation lands as a new phase step
  with its own verification.
- **5.2** **Q-NONSHIP hygiene-sweep toggle (decided 2026-07-11: skip remains the default — consider the
  toggle later).** An optional (e.g. quarterly) sweep that proposes releases for packages with only
  NON-SHIP accumulation. If adopted, it ships as a new explicit opt-in mode value — never a default, and
  hygiene flags stay summary-only until then. **Verify / exit criterion**: a dated adopt/decline decision
  appended to this step.

---

## 13. Dependency-aware ordering (D6)

Within one train run, packages are processed **upstream-first** so a consumer's proposal never bumps a
floor to a version the upstream has not at least *released* (cut). The DAG (parent `CLAUDE.md` graph +
juniper-ml extras):

```bash
shared libs:  observability, service-core, model-core, config-tools, ci-tools, doc-tools
sub-libs:     data-client → {cascor, canopy};  cascor-client → canopy;
              cascor-model, cascor-protocol → cascor;  recurrence-model → {recurrence, recurrence-client}
apps:         cascor, canopy, data, recurrence
meta:         juniper-ml  (depends on all via extras — STAYS MANUAL per Q-META; reevaluation tracked as §12 step 5.1)
```

Ordering is **soft** for the deploy itself (both gates are owner-controlled), but **hard** for
**propagation**: a pre-1.0 MINOR bump that escapes a consumer's `<next-minor` pin produces a
standard-gated ceiling-bump follow-on PR in that consumer — **never** part of the exempt path (§5.4). The
2026-07-06 ci-tools incident is the canonical example the train must handle by construction.

---

## 14. Owner decisions (questions answered 2026-07-11 — RESOLVED)

All eight questions were answered by the owner on 2026-07-11 (verbatim answers preserved in §14.1; the
plan-text ingestion of each decision is mapped in §14.2). This section is the decision record; the
sections named in §14.2 are the operative design text.

| ID         | Question                                                                                                                                    | Planner recommendation                                                                                                                                    | Owner decision (2026-07-11)                                                                                                                     |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| Q-CADENCE  | Cron cadence — weekly Monday `0 6 * * 1` like the other crons, or offset to avoid the 06:00 UTC pile-up with docs-full-check/security-scan? | Weekly Monday, **offset to `0 7 * * 1`** to not contend with the two existing 06:00 jobs.                                                                 | **Daily at 08:00 America/Chicago** → cron `0 13 * * *` UTC (07:00 CST winter drift accepted).                                                   |
| Q-IDENTITY | Cross-repo write identity: fine-grained PAT vs GitHub App?                                                                                  | **GitHub App** for durability; PAT acceptable as Phase-3-pilot bootstrap (pilot is in-repo → neither needed yet).                                         | **As recommended** — GitHub App at the Phase-4 boundary; pilot uses `GITHUB_TOKEN` only.                                                        |
| Q-PILOT    | Which package family pilots the ceremony (Phase 3)?                                                                                         | **juniper-ml sub-packages** — in-repo (no cross-repo identity), low blast radius, owner already watches the repo.                                         | **As recommended** — juniper-ml sub-packages.                                                                                                   |
| Q-META     | Does the meta-package `juniper-ml` ride the train or stay manual?                                                                           | **Stay manual initially** — it depends on all others and its extras-resolution TestPyPI verify (`publish.yml:105-121`) is bespoke; revisit after Phase 4. | **Stays manual for now; revisit later** — reevaluation/implementation tracked as §12 step 5.1.                                                  |
| Q-RULESET  | Path-scope the required-review ruleset to exclude `notes/releases/` (true auto-merge), or accept "owner one-click" fallback?                | **Path-scope exclude** for true hands-free R6; the structural guard already proves the diff inert. Owner's security-posture call.                         | **Path-scope exclude `notes/releases/`** — landed/confirmed at §12 step 3.3.                                                                    |
| Q-NONSHIP  | Do NON-SHIP-only packages ever get an auto-proposed release (e.g. quarterly hygiene) or skip forever?                                       | **Skip forever** by default; surface TAG_ONLY/NOTES_MISSING hygiene in the summary, not as proposals. Optional quarterly hygiene sweep is a later toggle. | **As recommended** — skip; hygiene-sweep toggle considered later, tracked as §12 step 5.2.                                                      |
| Q-CHANNEL  | Notification channel for the run summary + halt issues — step summary + issues only, or also a chat ping?                                   | **Step summary + dedup issues** (self-contained, auditable); no external channel dependency (slack MCP was removed 2026-06-15).                           | **Restore Slack** — webhook-based notifications to the Juniper Slack channel (§11, §9.4, step 1.4), additive to step summary + dedup issues.    |
| Q-SEVERITY | Should a security-category release ever bypass the proposal-PR gate for speed?                                                              | **No** — security releases keep both gates; only the notes archival is exempt. Speed comes from automation, not from removing review.                     | **As recommended** — security-category releases keep the existing gates.                                                                        |

### 14.1 Verbatim owner answers (2026-07-11)

- **Q-CADENCE:** "cron should run daily at 8:00am CDT"
- **Q-IDENTITY:** "concur with recommendation"
- **Q-PILOT:** "concur with using juniper-ml sub-packages"
- **Q-META:** "stay manual for now and revisit later. ensure reevaluation/implementation step added to document for tracking"
- **Q-RULESET:** "let's path-scope to exclude notes/releases/"
- **Q-NONSHIP:** "concur with recommendation to skip & consider hygiene sweep toggle later"
- **Q-CHANNEL:** "let's restore slack integration and include notifications in juniper slack channel"
- **Q-SEVERITY:** "security-category release should keep existing gates."

### 14.2 Decision → plan ingestion map

| Decision   | Plan text updated                                                                                                          |
|------------|------------------------------------------------------------------------------------------------------------------------------|
| Q-CADENCE  | §12 step 1.3 (cron `0 13 * * *` + DST note); §11 verify-before-first-cron wording ("daily cron").                          |
| Q-IDENTITY | §9.2 (decision paragraph); §12 step 4.1.                                                                                   |
| Q-PILOT    | Phase 3 already designed around this pilot — affirmed, no text change needed.                                              |
| Q-META     | §13 DAG meta line; **new §12 step 5.1** (the owner-requested reevaluation/implementation tracking step).                   |
| Q-RULESET  | §7.3 (decision + graceful-degradation wording); §12 step 3.3 (landing + verification of the path-scope exclusion).         |
| Q-NONSHIP  | **New §12 step 5.2** (hygiene-sweep toggle tracking; skip remains default).                                                |
| Q-CHANNEL  | §11 (new Slack-notification bullet: non-blocking webhook design); §9.4 (`SLACK_WEBHOOK_URL` secret); **new §12 step 1.4**. |
| Q-SEVERITY | Affirms §7/§10.1 as written — no text change needed.                                                                       |
| (all)      | Header **Status** → RATIFIED 2026-07-11.                                                                                   |

---

## 15. Risks

- **R-DETECT-FP** — a mis-tuned SHIP filter re-introduces the notes-rename false positives (audit trap).
  *Mitigation*: substantive-hunk rule (§4.2 step 5) + the detector unit test asserts the 4 known
  false-positive packages stay UP_TO_DATE.
- **R-DETECT-FN** — an under-documented `Unreleased` hides a real change (recurrence-model precedent).
  *Mitigation*: commit-diff wins over CHANGELOG; conflicts surfaced in the manifest for human review.
- **R-AUTOMERGE-LEAK** — a bug lets a non-notes change ride the exempt path. *Mitigation*: the guard is
  **add-only + path-confined + name-valid + single-purpose** (§7.2) and fails closed to the owner gate;
  a synthetic negative test proves it bites.
- **R-IDENTITY-SCOPE** — the write identity gains deploy-approval rights. *Mitigation*: hard invariant
  §9.3 + a guard test that the workflow makes no environment-mutating calls.
- **R-CRON-UNVERIFIED** — a scheduled workflow ships lint-green but runtime-red. *Mitigation*: the
  verify-before-first-cron rule is a required step of every phase (§11).
- **R-CONCURRENCY** — two trains (or a train + a manual release) race the immutable index. *Mitigation*:
  workflow concurrency group + `skip-existing` publish steps (§8).

---

## 16. Verification strategy (summary)

- **Unit** — every `util/release_train/*.py` has a `tests/test_release_train_*.py` gate (util/ is not
  pre-commit-lint-gated; the unittest is the gate — the `env_floor_drift_check` precedent). Synthetic
  fixtures, no network, no real pip/gh.
- **Fleet-truth** — the detector's real-run output is checked against the audit's classification table
  (7/11/0/0) as the acceptance oracle for Phase 1.
- **End-to-end** — Phase 3 runs one real low-risk juniper-ml sub-package release through the full ceremony
  and confirms the run **halts at Gate 2** (PyPI pending), never earlier, never later.
- **Cross-validation** — before this plan is treated as ratified, an independent pass should re-confirm
  (a) the `pypi`/`testpypi` gate facts against live `gh api …/environments`, and (b) that no repo ruleset
  silently already requires a review that changes the §7.3 auto-merge analysis.

---

## Appendix A — Convention → source map (file:line)

| Convention consumed                                                                                                 | Source (verified)                                                                                                                          |
|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Release-is-the-deploy; never a bare tag; 11.1-11.6 ceremony                                                         | procedure §11 (heading `:470`; banner `:474-479`; steps `:481`/`:489`/`:497`/`:511`/`:538`/`:547`)                                         |
| Central archive `notes/releases/`; `RELEASE_NOTES_v<ver>` meta / `RELEASE_NOTES_<pkg>_v<ver>` else                  | procedure §11.3 `:497-509`                                                                                                                 |
| `gh release create … --notes-file …`; `--latest` meta / `--latest=false` sub-package                                | procedure §11.4 `:522-528`                                                                                                                 |
| Release-notes structure + `notes/releases/` location                                                                | [`templates/TEMPLATE_RELEASE_NOTES.md`](templates/TEMPLATE_RELEASE_NOTES.md) `:7-9`, `:19-258`                                             |
| Security-release variant selection                                                                                  | [`templates/TEMPLATE_SECURITY_RELEASE_NOTES.md`](templates/TEMPLATE_SECURITY_RELEASE_NOTES.md)                                             |
| Keep-a-Changelog + SemVer; `[Unreleased]`→`[x.y.z] - date` shape                                                    | `CHANGELOG.md:5`, `:8`, `:27`; pre-1.0 minor note `:51-53`                                                                                 |
| `notes/releases/` exempt from the naming convention                                                                 | [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) `:43-51`  |
| `release: published` trigger + tag-prefix `if:` guard (meta)                                                        | `.github/workflows/publish.yml:24-26`, `:45`                                                                                               |
| Meta extras-resolution TestPyPI verify (the fallback exception)                                                     | `.github/workflows/publish.yml:97-121`                                                                                                     |
| Sub-package: single `release: published`, concurrency, tag-guard, "require a Release", strict verify, skip-existing | `.github/workflows/publish-service-core.yml:34-53`, `:65`, `:76-92`, `:139`, `:150-157`, `:185`                                            |
| Scheduled clone-all precedent (cron+dispatch); recurrence-omission gap                                              | `.github/workflows/docs-full-check.yml:63-65`, `:75-83`, `:99-106`                                                                         |
| util/ driver pattern (data-driven, exit codes) + unittest-gate idiom                                                | `util/env_floor_drift_check.py:22-43`; `tests/test_env_floor_drift_check.py` header                                                        |
| AGENTS.md `**Version**` header lockstep lint                                                                        | `tests/test_agents_md_version_drift.py`                                                                                                    |
| Consumer pin-ceiling drift class                                                                                    | `tests/test_ci_tools_drift.py` / `tests/test_doc_tools_drift.py`; ci-tools 2026-07-06 incident                                             |
| Ecosystem repo/env facts (recurrence-omission mirror)                                                               | `prompts/agent_templates/data/ecosystem.yaml:5-13`, `:20-23`                                                                               |
| Full current-state inventory, gates, drift F-1..F-6, §7 pipeline                                                    | [`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-SURFACE-AUDIT.md`](JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-SURFACE-AUDIT.md) |

## Appendix B — Per-package release-ceremony matrix (from the audit)

Trigger/verify columns show `now → target` where Phase 0 normalizes them. Archive = central
`juniper-ml/notes/releases/` filename. Sub-package Releases use `--latest=false`.

| #  | Package                   | Repo                  | Path                         | Trigger now→target | Tag pattern                    | Central archive file                                | Verify now→target                  |
|----|---------------------------|-----------------------|------------------------------|--------------------|--------------------------------|-----------------------------------------------------|------------------------------------|
| 1  | juniper-ml                | juniper-ml            | `.`                          | release            | `v*`                           | `RELEASE_NOTES_v<ver>.md`                           | fallback (keep, documented)        |
| 2  | juniper-ci-tools          | juniper-ml            | `juniper-ci-tools/`          | release            | `juniper-ci-tools-v*`          | `RELEASE_NOTES_juniper-ci-tools_v<ver>.md`          | fallback→strict                    |
| 3  | juniper-config-tools      | juniper-ml            | `juniper-config-tools/`      | release            | `juniper-config-tools-v*`      | `RELEASE_NOTES_juniper-config-tools_v<ver>.md`      | strict                             |
| 4  | juniper-doc-tools         | juniper-ml            | `juniper-doc-tools/`         | release            | `juniper-doc-tools-v*`         | `RELEASE_NOTES_juniper-doc-tools_v<ver>.md`         | strict (F-1/F-2 backfill)          |
| 5  | juniper-model-core        | juniper-ml            | `juniper-model-core/`        | release            | `juniper-model-core-v*`        | `RELEASE_NOTES_juniper-model-core_v<ver>.md`        | strict                             |
| 6  | juniper-observability     | juniper-ml            | `juniper-observability/`     | release            | `juniper-observability-v*`     | `RELEASE_NOTES_juniper-observability_v<ver>.md`     | fallback→strict (F-1/F-2 backfill) |
| 7  | juniper-service-core      | juniper-ml            | `juniper-service-core/`      | release            | `juniper-service-core-v*`      | `RELEASE_NOTES_juniper-service-core_v<ver>.md`      | strict                             |
| 8  | juniper-cascor            | juniper-cascor        | `.` minus subpkgs            | release            | `v*`                           | `RELEASE_NOTES_juniper-cascor_v<ver>.md`            | fallback→strict                    |
| 9  | juniper-cascor-model      | juniper-cascor        | `juniper-cascor-model/`      | tag→release        | `juniper-cascor-model-v*`      | `RELEASE_NOTES_juniper-cascor-model_v<ver>.md`      | strict                             |
| 10 | juniper-cascor-protocol   | juniper-cascor        | `juniper-cascor-protocol/`   | tag→release        | `juniper-cascor-protocol-v*`   | `RELEASE_NOTES_juniper-cascor-protocol_v<ver>.md`   | fallback→strict (F-1/F-2 backfill) |
| 11 | juniper-canopy            | juniper-canopy        | `.`                          | release            | `v*`                           | `RELEASE_NOTES_juniper-canopy_v<ver>.md`            | strict (F-2 backfill)              |
| 12 | juniper-cascor-client     | juniper-cascor-client | `.`                          | release            | `v*`                           | `RELEASE_NOTES_juniper-cascor-client_v<ver>.md`     | fallback→strict                    |
| 13 | juniper-cascor-worker     | juniper-cascor-worker | `.`                          | release            | `v*`                           | `RELEASE_NOTES_juniper-cascor-worker_v<ver>.md`     | fallback→strict (F-2 backfill)     |
| 14 | juniper-data              | juniper-data          | `.`                          | release            | `v*`                           | `RELEASE_NOTES_juniper-data_v<ver>.md`              | fallback→strict                    |
| 15 | juniper-data-client       | juniper-data-client   | `.`                          | release            | `v*`                           | `RELEASE_NOTES_juniper-data-client_v<ver>.md`       | fallback→strict                    |
| 16 | juniper-recurrence        | juniper-recurrence    | `juniper-recurrence/`        | tag→release        | `juniper-recurrence-v*`        | `RELEASE_NOTES_juniper-recurrence_v<ver>.md`        | strict                             |
| 17 | juniper-recurrence-client | juniper-recurrence    | `juniper-recurrence-client/` | tag→release        | `juniper-recurrence-client-v*` | `RELEASE_NOTES_juniper-recurrence-client_v<ver>.md` | strict                             |
| 18 | juniper-recurrence-model  | juniper-recurrence    | `juniper-recurrence-model/`  | tag→release        | `juniper-recurrence-model-v*`  | `RELEASE_NOTES_juniper-recurrence-model_v<ver>.md`  | strict                             |

Non-packages excluded (audit §2): `juniper-deploy`, `juniper-slacker`.
