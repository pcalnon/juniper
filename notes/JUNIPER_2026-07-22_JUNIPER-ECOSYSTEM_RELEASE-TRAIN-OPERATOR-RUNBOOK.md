# Juniper PyPI Release-Train — Operator Runbook

**Project**: Juniper — PyPI release-train automation
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.2.3
**Last Updated**: 2026-08-05

---

This runbook is the **operator's guide** to the automated PyPI release-train orchestrated by
[`.github/workflows/release-train.yml`](../.github/workflows/release-train.yml). It documents the four
run modes and exactly what each writes, the mode-resolution precedence, the day-to-day cheat-sheet, the
per-package HALT catalog, and the rollback procedures. It is the Phase 4.3 deliverable of the
[PyPI release-train plan](JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md)
(§12 step 4.3).

Every claim below is grounded in the real code or plan — cited as `path:line` or `§section`. Nothing here
describes behavior the code does not implement.

## 0. TL;DR — the two things an operator must remember

1. **`RELEASE_TRAIN_MODE=off` is the instant kill switch.** Set the repo variable to `off` (or dispatch
   with `mode=off`) and the next run is a green no-op: detection is skipped and both write jobs are
   unreachable (release-train plan §11; `release-train.yml:182-190` quiesce step).
2. **The owner still holds both gates.** The train never bumps a version without the owner-approved
   proposal PR (Gate 1) and never deploys to PyPI without the owner approving the `pypi` environment
   (Gate 2). The train automates only the middle arc (plan §5.3; `ceremony.py:1-11`).

## 1. The four modes and exactly what each writes

Mode is resolved once by the detect job's `id: mode` step (`release-train.yml:161-178`) and exposed as
`needs.detect.outputs.mode`; the two write jobs gate on it.

| Mode | Runs | Writes | Gate on |
|---|---|---|---|
| **`off`** | nothing beyond mode resolution | **nothing** — detection is skipped, both write jobs unreachable | quiesce step `release-train.yml:182-190` |
| **`report`** (default) | detect job only | **nothing** to GitHub/PyPI — only a step-summary table + the `release-manifest.json` run artifact + a non-blocking Slack post | detect job, workflow-level `contents: read` (`release-train.yml:139`) |
| **`propose`** | detect + **propose** job | opens **standard-gated** release-proposal PRs (version bump + CHANGELOG move + drafted notes + pin / `_version.py` dunder co-changes) **upstream-first**, plus D6 ceiling-bump follow-ons when a consumer pin escapes; **no** Releases, **no** (Test)PyPI | `propose` job `if: needs.detect.outputs.mode == 'propose'` (`release-train.yml:382`) |
| **`ceremony`** | detect + **ceremony** job | for `BUMPED_NOT_RELEASED` packages: opens the add-only notes-archive PR (central in juniper-ml, via a **GitHub-signed API commit** → auto-merges hands-free), enables `--auto`, **cuts the Release** on the owning repo, monitors its publish run to `PENDING_PYPI_APPROVAL`; **never** touches (Test)PyPI | `ceremony` job `if: needs.detect.outputs.mode == 'ceremony'` (`release-train.yml:587`) |

Notes:

- `report` is the **only** mode the daily cron ever runs (`RELEASE_TRAIN_MODE` defaults to `report`;
  `propose`/`ceremony` are opt-in via `workflow_dispatch` or an owner-set repo variable). An unknown
  value warns and degrades to `report` (`release-train.yml:173-176`).
- Both write jobs carry job-level `permissions: {contents: write, pull-requests: write}` and **nothing
  broader** — no `id-token`, no `environments`, no `deployments` (`release-train.yml:388-389`,
  `593-595`). This is pinned by `tests/test_release_train_workflow_guard.py`.
- `propose` and `ceremony` gate on **distinct** modes, so at most one write lane runs per run.

## 2. Mode-resolution precedence

The resolver (`release-train.yml:171`) is `mode="${MODE_INPUT:-${MODE_VAR:-report}}"`, i.e.:

```text
workflow_dispatch input `mode`   (highest precedence)
  > repo variable RELEASE_TRAIN_MODE
    > "report"                    (default)
```

- A `workflow_dispatch` `mode` input **wins** over the repo variable (dispatch `mode=propose` while the
  variable is `off` → `propose`).
- An empty input falls through to the repo variable; an empty variable falls through to `report`.
- Any value other than `off|report|propose|ceremony` warns (`::warning::`) and resolves to `report`
  (`release-train.yml:172-177`).

This exact matrix (including `ceremony` now first-class, and the input-over-variable precedence) is
rehearsed by running the workflow's own resolver shell in
`tests/test_release_train_workflow_guard.py::ModeResolutionMatrixTest`.

## 3. Normal-operations cheat-sheet

### 3.1 Reading the daily cron (report mode)

The cron fires daily at `0 13 * * *` UTC = 08:00 America/Chicago under CDT (`release-train.yml:115`;
Q-CADENCE, plan §12 step 1.3). Each run produces:

- a **step-summary classification table** (per-package `classification` + proposed bump), rendered by the
  detect job's "Render step summary" step;
- the **`release-manifest.json`** run artifact (the machine-readable manifest `detect.py --json` emits);
- a **non-blocking Slack post** to the Juniper channel when `SLACK_WEBHOOK_URL` is set
  (`release-train.yml:325-366`) — `Release train (<mode> mode): … Needs release action: …` + the run URL
  (`release-train.yml:356-358`). A missing secret skips the post and a post failure never fails the run.

Detector classifications you will see (`detect.py:90-94`): `UP_TO_DATE`, `UNRELEASED_CHANGES` (has
release-worthy CHANGELOG changes not yet in a proposal), `BUMPED_NOT_RELEASED` (declared > released; the
**ceremonial** class), `SHIP_UNCERTAIN`, `NEVER_RELEASED`. **Detector exit 1 ("action needed") is a
NORMAL green outcome** — only a hard source error (exit ≥ 2) fails the run (`release-train.yml`, detect
step; plan §11).

#### Detect SHIP filter + SemVer (why a package shows `UNRELEASED_CHANGES`)

The detector's proposed bump feeds Gate 1. Two internals decide whether code ships and which SemVer
bucket `propose` suggests (`detect.py:has_substantive_hunk`, `local_git_compare`, `propose_semver`;
plan §4.2 / §6):

| Signal | Ships? | Notes |
|---|---|---|
| Whitespace-only hunk | **No** | Empty / space-only `+/-` lines are stripped before comment/code checks (`has_substantive_hunk`). |
| Pure comment / docstring / link edit | **No** | Notes-rename residue class — discounted. |
| Pure **code** deletion (with `file_text`) | **Yes** | `_removed_codeish` path; deleting a real statement must not thin SemVer. |
| Add / delete / rename / **copy** of a `.py` module (`A`/`D`/`R`/`C` in `local_git_compare`) | **Yes** | Inherently substantive — no blob compare (`detect.py:334-335`). Copy (`C075`) is rarer than A/D/R (needs copy detection) but shares the same short-circuit; do not expect a module copy to fall through to `SHIP_UNCERTAIN`. |
| Patch unavailable | **Uncertain** | Surfaces as `SHIP_UNCERTAIN`, not a silent `UP_TO_DATE`. |

Keep-a-Changelog categories + conventional-commit classes map to the proposed bump
(`FEATURE_CATEGORIES` / `FIX_CATEGORIES` / `BREAKING_CATEGORIES`, `detect.py:107-109`;
`propose_semver`, `detect.py:804-815`; pre-1.0 policy plan §6):

| Input | Proposed bump (pre-1.0) |
|---|---|
| `### Security` or `### Fixed` (or `fix:` commits) | **patch** |
| `### Added` / `### Changed` / `### Deprecated` (or `feat:` commits) | **minor** |
| `### Removed`, `feat!` / `fix!`, or a `BREAKING CHANGE` footer | **minor** (breaking is not major pre-1.0) |
| No release-worthy cats/classes | **none** |

When reviewing a Gate 1 PR, a `Security`-only Unreleased section should propose **patch**, not minor;
a `Changed` section should propose **minor**. A mismatch means the detector/SemVer path drifted —
re-run `report` mode before merging a hand-edited bump.

#### Hygiene cleared (healthy path)

The step-summary footer `hygiene: TAG_ONLY=…, NOTES_MISSING=…` (`detect.py:996-999`) is **convention
debt**, not a deploy trigger. When a package is `UP_TO_DATE` **and** both bits are false, the detector
found a matching GitHub Release for `diff_base_tag` **and** a central
`notes/releases/RELEASE_NOTES_<pypi>_v<released>.md` archive (`detect.py:967-969`, `notes_missing` at
`detect.py:879-882`; coverage juniper-ml#756). That is the healthy clear — do **not** confuse it with a
quiet `TAG_ONLY=0` that still carries a `release-hygiene (tag_only) unavailable:` note. A `list_releases`
`SourceError` sets `hygiene.tag_only = None` (falsy → not counted in `TAG_ONLY=`) while still evaluating
`notes_missing` (`detect.py:971-973`); re-check Releases when gh recovers.

`released_upload` in the manifest is the **earliest** PyPI `upload_time_iso_8601` for the released
version (`detect.py:_upload_time`); missing/empty upload times → `None` (never invent a timestamp).

#### Live `gh compare` 300-file fallback (SemVer)

GitHub's compare API caps the `files` array at **300**. Live detect (`make_live_sources().compare`,
`detect.py:362-373`) must not leave busy subdir packages with a thinned path-scoped window:

| Condition | Behavior |
|---|---|
| `len(files) >= 300` | Fall back to path-scoped `local_git_compare` (cap-free). When that local compare succeeds **and** the remote payload had commits, **keep the remote commit first-lines** for the SemVer signal (`detect.py:368-371`) — local commit messages are discarded. |
| Below 300 | Use the `gh` payload as-is — `local_git_compare` is **not** called. |
| Compare missing / not found | Return error (`ok=False`) — **no** local fallback. |
| Cap hit but local compare fails | Surface the local error (never invent an empty `UP_TO_DATE`). |

Full-history sibling clones exist so this fallback has tags + history (`release-train.yml` detect
checkout note). A residual detector note `compare diff hit the 300-file cap with no ship evidence in
view…` (`detect.py:954-957`) means ship evidence was still absent after the fallback window — re-run
locally with `--local-git` or inspect the path-scoped diff by hand. Coverage pin: open
juniper-ml#729 `LiveCompareCapFallbackTest`.

#### When you see `SHIP_UNCERTAIN` (soft-fail — do not treat as up-to-date)

`SHIP_UNCERTAIN` is an **action** classification (`ACTION_CLASSIFICATIONS`, `detect.py:98`): the daily
report and Slack "Needs release action" count include it, and exit 1 is expected. It means the detector
**could not prove** ship or no-ship — never invent `UP_TO_DATE` / `BUMPED_NOT_RELEASED` from a soft fail
(`classify_package`, `detect.py:899-973`). Read the per-package note lines under the step summary (also in
`release-manifest.json` → `packages[].notes`).

| Note / signal | Cause | Operator action |
|---|---|---|
| `could not read declared version from the checkout` | Missing/unparseable `pyproject.toml` / `_version.py` for that package path (`detect.py:899-902`) | Fix the checkout (sibling clone missing? wrong `path:` in `registry.yaml`?) and re-run `report`. |
| `no tag under '<pattern>' matches released <ver>` | Released version has no matching git tag (`detect.py:917-920`) | Cut/restore the Release+tag convention (never bare-tag; §8 item 3), then re-run. |
| `compare … not found` / `compare unavailable` / other `comp.error` | Soft-fail compare (`comp.ok=False`, `detect.py:923-926`) — missing base/head, transport | Confirm the tag exists on the owning repo and `gh` auth; re-run. Do **not** hand-propose from a quiet report. |
| `compare diff hit the 300-file cap with no ship evidence in view; page or re-run (--local-git)` | Truncated compare window, no ship file in view (`detect.py:954-957`) | Live detect already falls back to `local_git_compare` past the 300-file cap (`make_live_sources`, `detect.py:360-372`; pin in juniper-ml#729). If you still see this note, re-run locally with `--local-git` or inspect the package path-scoped diff by hand. |
| `ship_uncertain` file rows in the manifest (no truncated note) | Patch unavailable / ambiguous hunks (`detect.py:952-955`, patch-unavailable → uncertain) | Open the listed files; decide ship vs discount; prefer a CHANGELOG corroboration before `propose`. |

`SHIP_UNCERTAIN` can still carry a `proposed_bump` / `proposed_version` when SemVer inputs are available
(`detect.py:963-964`) — treat that as a **hint**, not a Gate 1 mandate, until the uncertainty is cleared.

#### Hygiene degrade: `tag_only=None` / unavailable (orthogonal to "needs deploy")

The table footer `hygiene: TAG_ONLY=…, NOTES_MISSING=…` (`detect.py:996-999`) counts packages whose
last released version lacks a GitHub Release (`tag_only`) or a central `notes/releases/` archive
(`notes_missing`). Both are **convention debt**, not deploy triggers. (Healthy clear —
`TAG_ONLY=0` + `NOTES_MISSING=0` with no unavailable note — means Release + archive exist; see the
sibling hygiene-cleared guidance when present.)

- **True `tag_only`**: tag exists but no GitHub Release for it — restore the Release ceremony (§8 item 3 /
  plan §12 step 0.4); do not push a bare tag.
- **`tag_only` unavailable** (`None`): `list_releases` raised `SourceError` (gh blip). The detector keeps
  the package classification (often `UP_TO_DATE`), sets `hygiene.tag_only = None` (falsy → **not** counted
  in `TAG_ONLY=`), still evaluates `notes_missing`, and appends
  `release-hygiene (tag_only) unavailable: …` (`detect.py:971-973`; coverage juniper-ml#761). **Do not**
  treat a quiet `TAG_ONLY=0` plus that note as "hygiene cleared" — re-check Releases when gh recovers.
  A regression that re-raises would exit 2 the whole detect job; inventing `tag_only=True` would spam false
  TAG_ONLY on every blip.
- **Offline `--local-git`**: `make_local_git_sources.list_releases` must **raise** `SourceError` (open
  juniper-ml#773) so hygiene takes the `tag_only=None` path above. Returning `set()` falsely marks every
  package TAG_ONLY (`diff_base_tag not in set()` is always True). Until #773 lands, prefer live detect
  (or ignore `TAG_ONLY=` under `--local-git`).

### 3.2 Dispatching `propose` against specific packages (Gate 1)

```bash
# Open standard-gated proposal PRs for one (or a few) packages. Empty `packages` = all eligible.
gh workflow run release-train.yml -f mode=propose -f packages=juniper-observability
```

- The `packages` input is whitespace/comma-separated `pypi_name`s with a hard charset reject (see
  below). Empty = all eligible.
- The resulting PRs are **standard-gated**: the owner reviews and merges them. This is **Gate 1** (the
  version bump only ships with owner approval; plan §5.3).
- **In-repo pilot vs cross-repo**: `--cross-repo` is emitted **only** when the App token is non-empty
  (see below / §7). On the degraded no-App path only juniper-ml packages are proposed and siblings
  are skipped with a clear reason.

#### Reading the propose step summary

After a `mode=propose` run, open the job's GitHub **step summary** (not only the log). `propose.py`
prints one machine line per package (`propose.py` execute loop):

| Line prefix | Meaning |
|---|---|
| `opened: <pypi_name> (<repo>) -- <url>` | a standard-gated proposal PR was opened |
| `skip: <pypi_name> (<repo>) -- <reason>` | no PR (dup-guard, no-App sibling skip, empty URL, …) |

The workflow's "Render propose step summary" step (`release-train.yml:539-568`) buckets those lines into
operator-facing markdown:

| Summary signal | What it means | Operator action |
|---|---|---|
| `N proposal PR(s) opened, M skipped.` | count of `opened:` / `skip:` lines | Follow the **Opened** links for Gate 1 review |
| `### Opened (standard-gated -- owner reviews & merges)` | each opened package + PR URL | Review / merge (Gate 1); never auto-merged |
| `### Skipped` | each skip reason (e.g. duplicate open PR, `--cross-repo required…`) | Expected on re-dispatch / no-App path — do **not** re-open by hand |
| `**propose.py produced no output**` | `propose-output.txt` empty / missing | Treat as a crash — read the run log; do **not** assume zero eligible packages |
| Counts `0` / `0` **without** the crash banner | non-empty no-op output (e.g. no `UNRELEASED_CHANGES`) | Healthy idle — nothing to propose |

The summary footer always reminds Gate-1 framing: App-minted PRs get normal CI + sibling-repo targeting;
the degraded no-App path skips siblings and may need a close/reopen (or empty commit) to start checks
(`release-train.yml:565`). Hermetic pin of the renderer: `ProposeSummaryRehearsalTest` in
`tests/test_release_train_workflow_guard.py` (juniper-ml#730) — YAML-extraction twin of
`CeremonySummaryRehearsalTest`.

#### `packages` dispatch charset + `--cross-repo` gate

Both write jobs (`propose` and `ceremony`) share the same shell prefix **before** python runs
(`release-train.yml:494-519` propose; `:706-731` ceremony). Structural substring pins alone can miss a
weakened regex or a reordered `APP_TOKEN` gate — open juniper-ml#729 `PackagesInputRehearsalTest`
extracts and *runs* the real prefix.

| Input / condition | Result |
|---|---|
| Empty `packages` | No `--package` filter → all eligible (`package filter: <all eligible packages>`) |
| Comma- or whitespace-separated tokens | Equivalent — `juniper-observability, juniper-ci-tools` → two `--package` args |
| Token matching `^[a-z0-9][a-z0-9-]*$` | Accepted (lowercase letters, digits, hyphens; e.g. `juniper-observability`) |
| Garbage token (`Juniper-Observability`, `juniper_observability`, `../x`, `a;rm …`) | Job exits **2** with `::error::invalid package token …` **before** `propose.py` / `ceremony.py` runs |
| `APP_TOKEN` non-empty (App mint succeeded) | `--cross-repo` appended (Phase 4.1) |
| `APP_TOKEN` empty (`RELEASE_TRAIN_APP_ID` unset) | No `--cross-repo`; siblings skipped — degraded in-repo path (§7) |

**Pitfall:** Title Case, underscores, path fragments, and shell metacharacters fail the write job hard
(exit ≥ 2). Fix the dispatch input and re-run — do not treat it as a python / §8 HALT failure.

#### When propose skips (refusal stubs)

`build_proposal` returns a **skipped** stub (`skipped_reason` set; no PR opened) when inputs are
unusable — it never invents a shippable bump or an empty CHANGELOG section (`propose.py:1029-1107`).
`execute_proposal` already no-ops on `skipped`, so these are dry-run / JSON / step-summary signals.
Coverage: juniper-ml#749 (`BuildProposalTest` refusal cases).

| `skipped_reason` contains | Cause | Operator response |
|---|---|---|
| `dup-guard: open release PR already exists` | Concurrent / prior proposal still open | Review / merge / close the existing PR; do not force a second |
| `changelog conflict -- refuse to auto-author` | Detector flagged Unreleased vs ship evidence mismatch | Fix CHANGELOG or ship evidence by hand; re-run `report` then `propose` |
| `no proposable version` (`bump=none` / missing `proposed_version`) | SemVer inputs empty (often test/docs-only tip → no ship) | Confirm detect did not invent `UNRELEASED_CHANGES`; no Gate 1 PR expected |
| `could not read the version file` | Missing `pyproject.toml` / `_version.py` for the package path | Restore the version file on `main`; re-run propose |
| `could not locate the version assignment` | File present but assignment unparseable | Fix the version assignment syntax; re-run propose |
| `CHANGELOG move refused` (`no content to move` / missing Unreleased heading) | Empty or missing `## [Unreleased]` body | Add real Unreleased bullets (or drop the false `UNRELEASED_CHANGES`); never invent an empty section |
| `could not read …/CHANGELOG.md` | CHANGELOG missing after version staging | Restore CHANGELOG; re-run propose |

**Upstream of propose — test paths never ship.** `classify_change` discounts `_is_test_path` matches
(`tests/` / `test/` path segments, `test_*.py`, `*_test.py`, `conftest.py`) as `nonship` **before** the
substantive-hunk filter (`detect.py:658-663`, `735-736`). A tip that only touches tests will not become
`UNRELEASED_CHANGES` and therefore will not open a Gate 1 PR — even if the hunks look like "real code".
Coverage: juniper-ml#749 (`test_test_paths_are_nonship_even_with_code_hunks`).

#### Gate 1 review — static `_version.py` dunder lockstep (ml#701 / juniper-ml#710)

All five in-repo **static** packages (`juniper-ci-tools`, `juniper-config-tools`, `juniper-doc-tools`,
`juniper-observability`, `juniper-service-core`) also ship `<import>/_version.py` `__version__`. A
pyproject-only bump used to ship wheels whose metadata was right while `__version__` lied (ci-tools
0.7.0 / service-core 0.5.0). As of juniper-ml#710, `propose.py` auto-detects that dunder by file
presence (no registry field) and bumps it in the same proposal (`build_proposal` step 3a; design
[`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)).

When reviewing a Gate 1 proposal for a static in-repo package, confirm:

1. **Both files move together (happy path)** — `pyproject.toml` `[project].version` **and**
   `<import>/_version.py` `__version__` in the Files-changed list (or the PR body's
   `### Version bump` names the lockstep dunder co-change). Single- or double-quoted
   `__version__ = …` both parse (`propose.py` `set_dynamic_version`).
2. **Already-at-target / re-entry (juniper-ml#712)** — a **pyproject-only** version diff with
   **no** dunder checklist item is valid when checkout `__version__` already equals the proposed
   `to_version` (partial heal / re-entry). Step 3a leaves a correct dunder alone and must **not**
   false-flag REQUIRED-manual. Confirm the match, then merge when the rest looks right.
3. **Checklist is honest (unparseable)** — if the co-change checklist says the dunder bump is
   `REQUIRED (... edit manually)` and the body does **not** claim a lockstep co-change, the file
   exists but is unparseable; hand-edit `__version__` in the same PR before merge (AGENTS.md-header
   precedent).
4. **Stale dunder still behind** — pyproject-only while checkout `__version__` is still at
   `from_version` (or any other mismatch) is the pre-#710 / stale-train failure class. Do **not**
   merge as-is; add the dunder bump or re-dispatch `propose` after #710/#712.
5. **CI gate** — `tests/test_release_train_registry.py::VersionDunderLockstepTest` (ships with
   juniper-ml#710) asserts pyproject == dunder for every in-repo static-with-dunder package
   (dynamic packages are exempt — their dunder *is* the source). A red
   `VersionDunderLockstepTest` means do not merge.

**Pitfall:** a pyproject-only diff is no longer automatically rejectable. Distinguish re-entry
(dunder already correct → OK) from the stale-dunder class (dunder still behind → block). After #712,
an already-correct dunder produces neither a `_version.py` edit nor a checklist line.

Dynamic packages (model-core + the three recurrence packages) are unchanged: the version bump *is*
the `_version.py` edit, so there is no separate lockstep co-change to look for.

#### Gate 1 review: sibling / meta `AGENTS.md` **Version** co-change (worker#140 / ml#706 / #720)

Every sibling repo's `AGENTS.md` `**Version**:` header tracks that repo's **primary** package
(`pypi_name == repo` in `util/release_train/registry.yaml`). Their CI runs the portable
`tests/test_agents_md_version_drift.py` lint, so a proposal that bumps `pyproject.toml` but leaves the
header stale fails Documentation Links — the [worker#140](https://github.com/pcalnon/juniper-cascor-worker/pull/140)
pilot class, fixed in juniper-ml#706 (`propose.py` step 5a). The meta-package (`juniper-ml`) uses the
older step-5 path for the same header lockstep (`tests/test_agents_md_version_drift.py` in this repo).

When reviewing a Gate 1 proposal for a **sibling primary** or the **meta** package, expect:

| Signal in the proposal PR | Meaning | Operator action |
|---|---|---|
| Diff edits `AGENTS.md` `**Version**:` in lockstep with the version bump | Normal co-change (header was at the from-version) | Merge when the rest of the proposal looks right |
| Checklist names the AGENTS.md bump as "included in this PR" | Train already applied the header edit | No extra manual edit |
| **No** `AGENTS.md` edit **and** **no** AGENTS checklist item; checkout header already equals `to_version` | Already-at-target / partial heal / re-entry (juniper-ml#720) — silent success; same class as the ml#701 dunder re-entry fix | Confirm the header really matches the proposed version, then merge when the rest looks right |
| Checklist item **REQUIRED**; file missing, or present without a `**Version**:` line | Train never invents a header (juniper-ml#720) | Add / restore `**Version**: <to_version>` by hand in the same PR before merge |
| Checklist item **REQUIRED**; header present but neither from-version nor to-version | Unexpected value — train left the file alone (never clobbers) | Verify / edit `**Version**:` by hand in the same PR before merge |
| Diff omits `AGENTS.md`, **no** checklist item, and checkout header is **not** at `to_version` | Pre-#706 / stale train / bug | Do **not** merge as-is; bump the header (or re-dispatch `propose` after #706+#720) |

**Does not apply when:** the bumped package is a **sub-package** hosted in a sibling (`pypi_name != repo`,
e.g. `juniper-cascor-model` in `juniper-cascor`) — the host header tracks the primary, so step 5a never
touches it.

Hermetic coverage: `tests/test_release_train_propose.py` (happy-path shapes in juniper-ml#706;
re-entry / absent / missing-header edges in juniper-ml#720).

#### Gate 1 review: `AGENTS.md` per-package version TABLE row (juniper-ml#851)

Some repos carry, in addition to the header, a **per-package version table** that a repo-local
`version-drift` hook pins against each package's `_version.py` — today only
[juniper-recurrence](https://github.com/pcalnon/juniper-recurrence) (`AGENTS.md:22-24` vs
`scripts/check_version_drift.py`, hook id `version-drift`). Before juniper-ml#851 the train moved the
header and knew nothing about those rows, so **every** recurrence proposal failed that repo's
`Pre-commit (all-files)` gate and had to be healed by hand
([recurrence#92](https://github.com/pcalnon/juniper-recurrence/pull/92) /
[#93](https://github.com/pcalnon/juniper-recurrence/pull/93)). `propose.py` step 5a now rewrites the
row generically (issue option 2 — any `|`-row naming the package in backticks with a standalone
version cell), so a repo that adopts the same pattern later needs no new code.

Unlike the header, the table is **per package**: a sub-package (`juniper-recurrence-model`) bumps its
own row while the host header — which tracks the primary package — stays put. Header + row + the
in-repo extras-pin true-up compose into **one** `AGENTS.md` file edit.

| Signal in the proposal PR | Meaning | Operator action |
|---|---|---|
| Diff edits the package's table row in lockstep with the version bump; checklist says "version-table row … included in this PR" | Normal co-change (row was at the from-version) | Merge when the rest looks right |
| **No** `AGENTS.md` row edit and **no** table checklist item | Either the repo has no such table (7 of the 8 repos) or the row already equals `to_version` (partial heal / re-entry) — silent success | Nothing to do |
| Checklist item **REQUIRED** (version-table row) | A row names the package but its cell is neither the from- nor the to-version, or the row is ambiguous (two version cells) — the train never guesses at a cell | Fix the row by hand in the same PR before merge |
| Row diff touches a **different** package's row | Should be impossible (the needle is the backtick-delimited name, byte-identical to the target repo's own `_agents_table_version`) | Treat as a bug; do not merge |

**Open question (deliberately out of scope):** the recurrence `AGENTS.md` also mentions package
versions in **prose** (`AGENTS.md:118`, the Status paragraph). Its drift hook does not check prose
(invariants 1–3 cover `_version.py` ↔ CHANGELOG ↔ table cell ↔ header), so the train leaves prose
alone rather than invent an ungated rewrite. If a repo ever gates prose, that is a separate change.

Hermetic coverage: `tests/test_release_train_propose.py` (`AgentsTableVersionHelperTest` +
`BuildProposalAgentsTableTest`, juniper-ml#851 — a table-bearing sibling fixture mirroring the real
recurrence shape).

#### Gate 1 — Phase 4.2 dependency order + consumer ceiling-bump follow-ons

As of the Phase 4.2 land (`propose.py`, plan §13 / §12 step 4.2; CHANGELOG Unreleased), a `mode=propose`
run does two operator-visible things beyond the per-package proposal itself:

1. **Upstream-first scheduling.** Eligible `UNRELEASED_CHANGES` packages are processed in a
   deterministic topological order of the registry `depends_on` DAG (`topological_order`,
   `propose.py:552`) with a lexicographic `pypi_name` tie-break — shared libs → sub-libs → apps →
   meta (`juniper-ml` last). The tier list is documentation; the registry edges are the truth. A cyclic
   `depends_on` graph is a hard invocation error (**exit 2**) naming the cycle (`CycleError`,
   `propose.py:547` / `1382-1385`). Empty `packages=` therefore does **not** mean “filesystem
   order” — expect upstream proposals (and their follow-ons) before consumers.
2. **Standard-gated ceiling-bump follow-on PRs (D6).** When a proposed upstream bump is a pre-1.0
   MINOR/MAJOR that escapes a consumer’s `<next-minor` ceiling, `propose.py` annotates each
   `propagation_edges` row with a `consumer_pin_state` read from that consumer’s real pyproject and —
   for each escaped **non-meta** consumer — opens (or dry-run previews) a **separate** follow-on PR in
   the consumer’s repo (`enrich_edges_with_pin_state` / `execute_follow_on`, `propose.py:837` /
   `891`, execute loop `1432-1454`). Branch shape: `deps/<upstream>-ceiling-<new-ceiling>` (e.g.
   `deps/juniper-model-core-ceiling-0.5.0`). The pin edit raises **only** the escaped ceiling; floors
   and other specifiers are preserved byte-for-byte. Follow-ons trail their upstream proposals in the
   same run and are **never** folded into the upstream proposal or the exempt notes-archive path
   (2026-07-06 ci-tools incident class; rec#85 is the hand-made model).

| `consumer_pin_state` | Meaning | Operator action |
|---|---|---|
| `within_range` | Consumer pin already admits the new version | None — no follow-on |
| `floor_only (no ceiling)` | Floor-only pin; no `<ceiling` to raise | None — no follow-on |
| `escaped -> follow-on` | Ceiling escapes; follow-on PR opened (or dry-run previewed) | **Gate 1 review** the follow-on in the **consumer** repo (pin-only diff) |
| `escaped -> skipped(<reason>)` | Escaped, but this run cannot open (no `--cross-repo` / sibling missing / dup-guard) | Read the reason; on the degraded no-App path, open/merge the ceiling bump by hand (or re-run with App + sibling checkouts) |
| `escaped -> deferred (juniper-ml meta…)` | Meta pin escaped a **sibling** upstream | Manual Q-META — bump the meta pin when the meta itself is next released (in-repo upstreams stay on the #661 folded co-change; meta never gets a follow-on) |
| `no_versioned_pin (…)` / `unknown (…)` | Registry edge without a versioned requirement, or unreadable pyproject | Investigate the consumer pin / checkout; do not invent a ceiling |

**Reviewing a follow-on PR (Gate 1, consumer repo):**

1. **Pin-only** — Files changed should be the consumer `pyproject.toml` (ceiling raise only). Reject
   anything that looks like a version bump, CHANGELOG move, or notes archive.
2. **Branch / title** — Head starts with `deps/<upstream>-ceiling-`; title cites the upstream and new
   ceiling. Dup-guard: an open PR with the same `deps/<upstream>-ceiling-` prefix suppresses a second
   open (`find_existing_follow_on_pr`, `propose.py:776`).
3. **Merge timing** — Upstream-first ordering is **soft for deploy** but **hard for propagation**: merge
   the upstream proposal (and complete its release) before relying on the consumer pin; the follow-on
   can land once the new upstream version is the one you intend consumers to admit.
4. **Cross-repo capability** — Follow-ons in sibling repos require the same App-token `--cross-repo`
   path as sibling proposals (§7). Without it they surface as `escaped -> skipped(...)` and do **not**
   open.

Hermetic pins: `tests/test_release_train_propose.py` (topological order over the real registry + synthetic
cycle → exit 2; escaped / within-range / floor-only / extras-form pins; degraded skip; per-repo
dup-guard; dry-run writes nothing).

#### Gate 1 review — notes draft (`notes_render`)

`propose` attaches a **DRAFT** release-notes file rendered from CHANGELOG `[Unreleased]`
(`notes_render.render_notes`; plan §10.1). Review these header signals before merge — a wrong draft
still archives at ceremony time:

| Signal in the drafted notes | Expected | Source |
|---|---|---|
| Title `# … vX.Y.Z Release Notes` | Meta-package → **`# Juniper ML v…`** (not `# juniper-ml v…`); every other dist keeps its `pypi_name` | `display_name` (`notes_render.py:93-95`) |
| `**Release Type:** …` | `major` → **MAJOR**, `minor` → **MINOR**, `patch`/`none`/unknown → **PATCH** | `release_type` / `_RELEASE_TYPE` (`notes_render.py:52`, `89-90`) |
| `**Breaking changes:** …` | **YES** only when a Keep-a-Changelog **`Removed`** category is present (case-insensitive); otherwise **NO** | `notes_render.py:239` |
| Bullets under What's New | Both `-` and `*` markers; indented / bare continuations fold into the current bullet; stray prose before any marker is ignored | `_split_bullets` (`notes_render.py:101-120`) / `parse_unreleased` |
| Repo-relative CHANGELOG links | Rewritten absolute via `link_base` (table below) so centrally archived notes do not 404 | `rewrite_relative_links` (`notes_render.py:373-388`) |

**Pitfalls:**

- A meta proposal titled `# juniper-ml …` means `display_name` drifted — fix before ceremony archives it.
- A MAJOR bump labeled PATCH (or Breaking stuck at NO despite a `### Removed` section) means the
  bump→`release_type` map or the Removed membership check drifted.
- Prefer `-` in hand-edited CHANGELOG, but do not reject a proposal solely because Unreleased used `*`.
- A drafted or archived note that still shows repo-relative `[text](docs/…)` / `[text](notes/…)` links means
  the caller omitted `link_base` — fix the call site (or pass CLI `--link-base`); do not hand-edit the
  archive to absolute URLs.

##### `link_base` — absolute CHANGELOG links in archived notes

Release notes are archived centrally under `notes/releases/` in **juniper-ml**, but CHANGELOG bullets
often carry links relative to the **owning** repo's tree. Archived verbatim, those targets 404 when
read outside that repo (the canopy v0.6.0 archive class).

`notes_render.rewrite_relative_links` prefixes relative inline-markdown targets with a `link_base`
URL (`https://github.com/<owner>/<repo>/blob/<ref>`, no trailing slash). Callers set it as follows
(also overridable via CLI `--link-base`):

| Caller | Default `link_base` | Source |
|---|---|---|
| **ceremony** (central archive) | Owning repo's **tag-pinned** blob URL — `…/blob/{plan.tag}` | `ceremony.py` → `render_notes(…, link_base=…)` |
| **propose** (Gate 1 draft) | Owning repo's `blob/main` — `…/blob/main` | `propose.py` → `render_notes(…, link_base=…)` |
| CLI / offline | Explicit `--link-base URL`, or omit (no rewrite; back-compat) | `notes_render.py` CLI |

What is rewritten vs left alone (`test_rewrite_relative_links_shapes`, juniper-ml#877):

| Link form | Treatment |
|---|---|
| `[t](notes/X.md)`, `[t](./notes/X.md#sec)`, `[t](docs/Y.md "Title")` | → `{link_base}/notes/X.md` (leading `./` stripped; path anchors + markdown titles kept) |
| Absolute `https://…` / `http://…` | Untouched |
| `mailto:…`, bare `#anchor`, protocol-relative `//…` | Untouched |

**Gate 1 check:** open the drafted notes (or the archive PR file) and confirm CHANGELOG-sourced relative
links resolve to the owning repo (tag tip for ceremony; `main` for propose). Coverage pins:
`tests/test_release_train_propose.py` (juniper-ml#756 header signals + juniper-ml#877 `link_base`).

#### CHANGELOG refuse clears staged edits (juniper-ml#751)

`build_proposal` stages the version bump (and optional static `_version.py` dunder) **before** the
CHANGELOG `[Unreleased]` → `[<version>]` move (`propose.py` steps 3 / 3a / 4). When step 4 refuses —
empty / missing Unreleased body (`CHANGELOG move refused: …`) or a missing CHANGELOG
(`could not read …/CHANGELOG.md`) — juniper-ml#751 clears any edits already staged
(`prop.edits.clear()`) so the skipped stub matches the dup-guard / `bump=none` shape:
`edits=[]`, `branch=None`, `skipped_reason` set (`propose.py` ~1099–1110 after #751).

| Signal (dry-run / `--json` / step summary) | Meaning | Operator response |
|---|---|---|
| `skip:` + `CHANGELOG move refused` / `could not read …/CHANGELOG.md` **and** `edits=[]` | Honest refusal stub (post-#751) | Fix Unreleased bullets or restore CHANGELOG; re-run `report` then `propose` |
| Same `skipped_reason` **but** `edits` still lists a pyproject / dunder bump | Pre-#751 half-proposal — `execute_proposal` still no-ops on `skipped`, but JSON looks shippable | Do **not** treat leftover edits as a Gate 1 candidate; upgrade train past #751, then re-run |

**Why this matters:** `execute_proposal` already guards on `prop.skipped` (`propose.py` ~1310), so a
half-staged stub never opened a PR. Operators reading dry-run JSON still saw leftover version edits and
learned to ignore them — #751 makes the stub shape honest. Full refusal-reason catalog (including
`bump=none` / unreadable version): open docs PR juniper-ml#768 (coverage #749) when merged.

Hermetic coverage: `tests/test_release_train_propose.py`
(`BuildProposalTest.test_changelog_move_refused_clears_staged_edits`,
`test_unreadable_changelog_clears_staged_edits`).

#### Manifest / registry miss + `--execute` seam gates

Orthogonal to `build_proposal` refusal stubs (coverage juniper-ml#749): these are `propose.main` /
`execute_proposal` gates **before** a proposal is built or written. A registry miss must **skip**, not
abort the whole propose job mid-loop; a miswired `--execute` seam must hard-fail before any partial
write.

| Signal | Cause | Operator response |
|---|---|---|
| Dry-run / JSON `skipped_reason="package not in registry.yaml"`; summary counts a skip | A proposable manifest package's `pypi_name` is absent from `registry.yaml` (`propose.py:1415-1418`). Loop continues for remaining packages. | Add the package to `util/release_train/registry.yaml` (registry lint) or drop the stale manifest entry; re-run `report` then `propose`. Ceremony's parallel for `BUMPED_NOT_RELEASED` is the `not-in-registry` HALT (§4). |
| `--package` / dispatch `packages=` names an unknown `pypi_name` → exit 2 | Invocation error before the loop (`propose.py:1388-1392`) — not a skip stub | Fix the `packages=` input against `registry.yaml` |
| `--execute` exits 2: `execute mode needs write_file/run_git/open_pr seam members` | Live seam missing a write member (`execute_proposal` / `execute_follow_on`, `propose.py:1319-1320`, `896`) | Workflow / wiring bug — re-dispatch the GitHub Actions job; do not hand-run `--execute` without live sources |
| `skip: …` / empty URL; no branch, commit, or PR | `prop.skipped` or `branch is None` → `execute_proposal` returns `""` and issues **zero** write/git/pr calls (`propose.py:1321-1322`) | Expected for registry-miss / refusal stubs; read the printed skip reason |

Coverage (hermetic): juniper-ml#764 —
`CliTest.test_manifest_package_absent_from_registry_is_skipped` + `ExecuteProposalSeamTest`.

### 3.3 Dispatching `ceremony` against specific packages (drives toward Gate 2)

```bash
# Run the exempt-archive + Release ceremony for BUMPED_NOT_RELEASED packages.
gh workflow run release-train.yml -f mode=ceremony -f packages=juniper-observability
```

The `packages` / `--cross-repo` shell contract is **identical** to §3.2 (same charset reject +
`APP_TOKEN` gate; `release-train.yml:706-731`).

Dispatch caveats (2026-07-29): `gh workflow run` can occasionally **double-fire** — the concurrency group
(`release-train`, `cancel-in-progress: false`) makes the duplicate **queue** (it does not kill the live
run); cancel the queued duplicate and let the first proceed. A ceremony **cancelled mid-run** is safe to
re-dispatch as-is: the reuse / Release-exists arms below make re-entry idempotent (proven live — the
2026-07-29 five-package batch was cancelled mid-ceremony after 3 of 5 Releases and recovered with one
scoped re-dispatch).

**`main-ci-not-green` self-observation HALT — FIXED (2026-08-08).** Before this fix, a `ceremony`
**dispatched** via `workflow_dispatch` (`mode=ceremony`) **deterministically self-halted** every eligible
package with `main-ci-not-green` even when `main` was fully green: the §8 precondition probe read the
newest run of ANY workflow on `main`, which under dispatch is the **in-progress release-train run itself**
(empty conclusion → `None` ≠ `success` → HALT). This produced the 2026-07-29 #854–#857 HALT batch and the
juniper-ci-tools W1 HALT (dedup issue #855, run 31257045597). The probe is now scoped to the newest
**completed** run of the package's own main-CI workflow (`gh run list --workflow <name> --status
completed`; the workflow name is the registry's `main_ci_workflow`, default `ci.yml`, per §4's
`main-ci-not-green` row), so a dispatched ceremony no longer observes itself. If you still see
`main-ci-not-green` after this fix, `main` CI really is not green for that package (or has no completed run
of its workflow yet) — treat it as a genuine gate, not the old artifact.

For each `BUMPED_NOT_RELEASED` package the ceremony (`ceremony.py:1-45`): runs the §8 preconditions,
builds the central notes file, opens the **add-only** archive PR (always in juniper-ml — the central
`notes/releases/` archive, plan §10.2), enables `gh pr merge --auto --squash` behind the required
archive-guard check, **cuts the Release** on the owning repo (`gh release create <tag> --latest=false`;
the Release **creates** the tag, so deliberately **no** `--verify-tag`, `ceremony.py:225-226`), and
monitors the triggered publish run.

- **The archive PR auto-merges hands-free.** The archive branch **and** its single-file commit are
  created through the GitHub API — a `git/refs` POST plus a `createCommitOnBranch` GraphQL mutation
  (`ceremony.py:open_archive_pr`). A commit made through GitHub's API under the App / `GITHUB_TOKEN`
  identity is **GitHub-signed / Verified**, so the exempt archive PR satisfies the juniper-ml ruleset's
  `required_signatures` rule and the armed `--auto` merge **completes with zero clicks**. (A plain
  runner-side `git commit` is unsigned and left an all-green archive PR BLOCKED behind that rule until an
  owner admin one-click — 2026-07-23 run 30051952226 / ml#707; the API commit removes that block with no
  security-posture change.) **Owner one-click is now only the degraded/manual fallback** — e.g. if
  `allow_auto_merge` is off (a graceful degrade, not a HALT) or the auto-merge never lands.

- **Ruleset `code_quality` blocked the armed auto-merge (2026-07-29) — resolved via App bypass actor.**
  The juniper-ml ruleset's `code_quality` (severity: errors) rule has **no reporting tool behind it**, so
  it can never be satisfied and every **non-bypass** merge stays `BLOCKED` even with all required checks
  green, a Verified commit, and a current base (archive PRs #860–#863; probe-confirmed on ml#864). The
  release-train App (Integration `4362741`) is now a ruleset **bypass actor in `pull_request` mode**, so
  the armed `--auto` merge completes again — this also covers the strict up-to-date policy when a
  multi-package ceremony's serial archive PRs go stale as their siblings merge. If the `code_quality`
  rule is ever removed (deferred until the code-signing work lands), the bypass entry can be dropped too.

- **Archive PR reuse / already-on-main (idempotent re-entry).** Before cutting a Release the planner
  inspects juniper-ml (central archive, plan §10.2) for an open PR on the archive branch and for the
  notes file already on `main` (`ceremony.py:902-914`):

  | Truth | Plan actions | Execute contract |
  |---|---|---|
  | Open archive PR already exists | `enable_auto_merge` → `cut_release` → `monitor_publish` (**no** `open_archive_pr`) | Must **not** open a duplicate exempt PR. `enable_automerge` receives `pr_ref or plan.archive_branch` so a reused plan (no fresh `pr_url`) still arms `--auto` against the **branch** (`ceremony.py:1008`). |
  | Archive file already on `main` | `cut_release` → `monitor_publish` only | **No** archive-PR / auto-merge seam calls — only `create_release` (+ monitor). |
  | Neither | full happy path: open → auto-merge → cut → monitor | Fresh signed archive PR as in the bullet above. |

  Re-dispatching `ceremony` while an archive PR is still open (or after it merged to `main` but before
  the Release exists) is therefore safe — do **not** close a healthy open archive PR to "start over".
  Hermetic execute pins: juniper-ml#730 (`ExecuteTest` open-PR reuse + archive-already-on-main).
  (Release-already-cut → `RESUME_MONITOR` is the sibling re-entry; see §5.5 / juniper-ml#726.)

#### Archive-guard triage (required check `Release-Train Archive Guard`)

The ceremony arms `--auto` behind `ci.yml`'s PR-only `release-train-archive-guard` lane, which runs
`util/release_train/archive_guard.py` over the PR's `git diff --name-status` (plan §7.2). Verdicts
(`archive_guard.py:100-108`, `174-217`):

| Verdict | CI outcome | Meaning | Operator action |
|---|---|---|---|
| `SKIP` | pass | Diff does **not** touch `notes/releases/` — not an archive PR | None. Normal PRs always SKIP so the required check never blocks them. |
| `OK` | pass | Pure `A` adds of well-formed `notes/releases/RELEASE_NOTES_*.md`; all four rules hold | Auto-merge proceeds (with the signed archive commit, above). |
| `FAIL` | fail (exit 1) | One or more rule violations | The PR **falls back to the standard owner gate** and **never auto-merges** (`archive_guard.py:271`). Fix or close; do not force-merge a dirty archive PR onto the exempt path. |

`touches_releases` inspects **every** path on a change — including **both** sides of a rename/copy
(`archive_guard.py:169-171`). That is the load-bearing contract against destination-only blindness:
a rename **out** of `notes/releases/` is still an archive PR and must **FAIL**, never SKIP. Non-add
statuses that FAIL as archive PRs (pinned by juniper-ml#754 coverage):

| Diff shape | Why it is still an archive PR | Typical violations |
|---|---|---|
| `R notes/releases/X.md → docs/moved.md` (rename-OUT) | Source path is under `notes/releases/` | rule1 (add-only) + rule4 (single-purpose) |
| `C` (Copy) into `notes/releases/` | Status letter is not `A` (git may emit `C075`) | rule1 (+ rule4 if the copy source is out of path) |
| `T` (Typechange) on an archive path | Non-add mutation of an existing archive file | rule1 |
| `M` / `D` / rename-IN / mixed with non-archive paths | Classic non-add or multi-purpose | rule1 and/or rule2/rule3/rule4 |

**Do not** try to clear a FAIL by renaming the notes file out of `notes/releases/` hoping for SKIP —
both rename paths count, so that still FAILs. Close the PR (or land a pure-`A` follow-up) and let
ceremony re-open a single-file Add. Local smoke:

```bash
# Against a PR tip (or any base...head range)
python util/release_train/archive_guard.py --base origin/main --head HEAD --json
```

- The monitor polls a bounded ~15-minute wall clock (`--monitor-timeout 900`,
  `release-train.yml:732-740`; `DEFAULT_MONITOR_TIMEOUT_SECONDS`, `ceremony.py:137`) until the run parks at
  the owner-gated `pypi` environment — GitHub reports that as run status `waiting`, which the train
  reports as **`PENDING_PYPI_APPROVAL`** (`ceremony.py:531`). **That terminal state is SUCCESS for the
  train** (plan §5.1). Terminal monitor returns are only
  `PENDING_PYPI_APPROVAL` / `RELEASED` / `HALT_TESTPYPI` / `HALT_PUBLISH`
  (`monitor_publish_run`, `ceremony.py:938-941`).
  - **`NOT_FOUND` is not terminal.** Right after `gh release create`, the publish workflow is often
    invisible for a poll or two (`classify_publish_run(None) -> NOT_FOUND`, `ceremony.py:505`). The
    monitor **keeps polling** — it must never stamp `NOT_FOUND` onto the ceremony result (that would
    skip waiting for Gate 2). Coverage: `MonitorTimeoutTest` in `tests/test_release_train_ceremony.py`
    (juniper-ml#744 / #745 / #747).
  - **Timeout → honest `IN_PROGRESS`.** If the wall clock elapses while the run is still building *or*
    still permanently missing (mis-tagged Release / workflow never triggered), the monitor returns
    **`IN_PROGRESS`** — never invents `PENDING_PYPI_APPROVAL` / `RELEASED` / a HALT
    (`ceremony.py:941`). Re-run ceremony mode to resume (idempotent). Operator check when you see
    `IN_PROGRESS` with no publish run: confirm the Release tag matched the workflow's `on:` filter and
    that the publish workflow actually fired (`gh run list --repo pcalnon/<owning-repo>`); fix the tag /
    workflow trigger, then re-run — do not approve a phantom Gate 2.
  - **`RELEASED` = both gates already done (not a HALT).** When the publish run's top-level status is
    `completed` with conclusion `success`, `classify_publish_run` returns **`RELEASED`**
    (`ceremony.py:519-521`) — Gate 2 was already approved and the PyPI job finished. `execute_ceremony`
    surfaces that as the package final state (`result["state"] = verdict`, `ceremony.py:1029`) and does
    **not** file a halt issue (coverage: `ExecuteTest.test_execute_both_gates_done_is_released`,
    juniper-ml#741). Treat step-summary / Slack `RELEASED` as **done** — do not re-approve Gate 2 and do
    not expect a `testpypi-verify-failed` / `HALT_PUBLISH` issue.
  - **Do not confuse `RELEASED` with `ALREADY_RELEASED`.** `ALREADY_RELEASED` is a **plan-time** no-op
    when live PyPI already serves the target version before any archive/Release actions
    (`ceremony.py:863-866`). `RELEASED` is a **monitor-time** terminal after the ceremony cut (or resumed)
    a Release and watched the publish workflow finish successfully.
- **Gate 2 is yours**: the publish workflow's `pypi`-environment deploy job waits for the owner to
  approve. The train never approves it (§7). Approve it in the run's environment-review UI when ready.
  If the monitor already returned `RELEASED`, Gate 2 was approved earlier — no further click.
- **Re-entry is a named plan state, not a full re-ceremony.** When the Release tag already exists,
  `plan_ceremony` sets `plan.state = RESUME_MONITOR` and the action list is **only** `monitor_publish`
  (`ceremony.py:892-897`). Execute keeps `plan_state=RESUME_MONITOR` while `state` becomes the monitor
  verdict (`PENDING_PYPI_APPROVAL` / `HALTED` / …) — so the ceremony step summary buckets it under
  **resume-monitor**, not a new ceremony (`ceremony.py:980-983`, `release-train.yml:775-789`). A
  TestPyPI failure on resume still HALTs and files `testpypi-verify-failed` **without** re-opening the
  archive PR or re-cutting the Release (`execute_ceremony` monitor branch, `ceremony.py:1016-1024`;
  coverage: juniper-ml#726). Distinct from `ALREADY_RELEASED` (PyPI already serves the target — pure
  no-op, `ceremony.py:864-866`). See §5.5.

### 3.4 The two owner gates (never automated)

| Gate | What it guards | Who | Where |
|---|---|---|---|
| **Gate 1** | the version bump (+ static `_version.py` dunder lockstep when present) **and** any D6 ceiling-bump follow-on | owner reviews + merges each standard-gated PR | the upstream `propose` PR **and** any `deps/<upstream>-ceiling-*` follow-on in a consumer repo |
| **Gate 2** | the PyPI deploy | owner approves the `pypi` environment | the publish run's environment review |

Neither gate is ever a release-train identity action (plan §9.3; enforced in code by
`ceremony.py:_assert_gh_allowed`, §7 below).

## 4. The §8 "nothing unexpected" HALT catalog

Each **precondition** is checked **per package** before the ceremony proceeds; **any failure → HALT that
package, open/update a deduplicated GitHub issue, never proceed** — and a halt on one package does not
block the others (plan §8; `ceremony.py:22-31`). A HALT is a **normal green outcome** of the run (it does
not turn the run red); it is surfaced in the ceremony step summary, a dedup issue (when one is filed),
and Slack. The `ceremony.py` exit is `1` when any package HALTED (owner attention), `2` only on an
invocation error (`ceremony.py:71-72`).

| `reason_key` | Trigger | Code | Operator response |
|---|---|---|---|
| `main-ci-not-green` | newest **completed** run of the package's own main-CI workflow (registry `main_ci_workflow`, default `ci.yml`; the 3 recurrence packages → their path-scoped `ci-recurrence-*.yml` lane) on `main` has conclusion ≠ `success` | `ceremony.py:893` (probe `654-664`) | Fix `main` CI (owner rule: check main green before blaming a red PR); re-run ceremony. **Self-observation class FIXED (2026-08-08):** pre-fix the probe read the newest run of ANY workflow on `main`, so a `workflow_dispatch` ceremony read the in-progress release-train run ITSELF (empty conclusion → HALT) and dispatched ceremonies self-halted deterministically on a fully-green `main` (run 31257045597 / issue #855; the 2026-07-29 #854–#857 batch was this class). The probe is now `--workflow <name> --status completed`-scoped, so an in-progress self-run can no longer be read; a genuine red `main` (or a brand-new repo with zero completed runs of that workflow) still HALTs fail-closed (correct). |
| `declared-lt-released-anomaly` | declared version < the version PyPI already serves (yank/rollback) | `ceremony.py:724` | Investigate the PyPI yank/rollback manually; do NOT release. Reconcile the declared version. |
| `pypi-truth-missing` | manifest said released, but PyPI now returns no version | `ceremony.py:726` | A first-publish/yank a human must resolve — confirm the trusted-publisher config (procedure §3.3) before re-running. |
| `changelog-section-missing` | no non-empty `CHANGELOG [<version>]` section to source the notes | `ceremony.py:741` | The proposal PR (Gate 1) should have created it — merge the proposal first, or add the section, then re-run. |
| `notes-render-failed` | `notes_render.render_notes` raises `OSError` (missing/unreadable `notes/templates/TEMPLATE_RELEASE_NOTES.md` or the security template) while building the central archive content | `ceremony.py:887-890` | Restore the template under `notes/templates/` in the **central** juniper-ml checkout the ceremony uses as `repo_root`; do not invent archive body by hand. Re-run ceremony — it re-plans from CHANGELOG truth (coverage: `PreconditionHaltTest.test_notes_render_failed_halts`, juniper-ml#741). |
| `missing-declared-version` | manifest has no `declared_version` for a `BUMPED_NOT_RELEASED` pkg | `ceremony.py:711` | A malformed manifest — re-run detection (`report` mode) to regenerate it. |
| `not-in-registry` | package is `BUMPED_NOT_RELEASED` in the manifest but absent from `registry.yaml` | `ceremony.py` (`_plans_for` / `ceremony.py:1152`) | Add the package to `util/release_train/registry.yaml` (registry lint gates it). Propose's parallel for `UNRELEASED_CHANGES` is a **skip stub** (`skipped_reason="package not in registry.yaml"`, §3.2) — not a HALT. |
| `testpypi-verify-failed` | (during the monitor) the publish workflow's TestPyPI install-verify failed before Gate 2 | `ceremony.py:876` | The run is not healthy — inspect the publish run's TestPyPI job; fix and re-cut is idempotent. |

### 4.1 Monitor terminals after the Release is cut

After the archive PR + Release succeed, `monitor_publish` maps the publish workflow via
`classify_publish_run` (`ceremony.py:497-532`) and `execute_ceremony` handles the two failure classes
**asymmetrically** (`ceremony.py:1016-1028`; pinned by `tests/test_release_train_ceremony.py`):

| Terminal | Classifier trigger | Dedup issue? | Operator response |
|---|---|---|---|
| `HALT_TESTPYPI` | any `*testpypi*` job `conclusion=failure` | **Yes** — `reason_key=testpypi-verify-failed` via `upsert_halt_issue` | Inspect TestPyPI install-verify; fix; re-cut (idempotent). |
| `HALT_PUBLISH` | run `status=completed` and `conclusion` in `{failure, cancelled, timed_out}` **and** TestPyPI did **not** fail (so this is post-TestPyPI) | **No** — note only: `"the publish run failed before the pypi gate."` | Open the publish run UI; diagnose the non-TestPyPI failure (cancelled deploy, timed-out job, etc.). Do **not** wait for a GitHub issue. Archive + Release were already cut — re-entry resumes at the monitor and must not re-cut. |
| `PENDING_PYPI_APPROVAL` | run `waiting` / TestPyPI ok + pypi job parked | n/a (success for the train) | Approve Gate 2 when ready (§3.3). |
| `RELEASED` | run completed `success` (both gates done) | n/a | Owner already approved; nothing to do. |

**Why the asymmetry.** `testpypi-verify-failed` is a named, recoverable §8 class with a stable
`reason_key` for dedup. A generic post-TestPyPI failure has no single reason key worth filing — the
step-summary note + Slack + the publish-run URL are the signal. Looking for a missing issue is the
wrong recovery path.

**HALT-issue degradation (Phase 4.3).** Filing the dedup issue is **best-effort**: if the `gh issue`
API itself fails — most plausibly the cross-repo App token lacking the **Issues** permission — the
upsert degrades gracefully to a loud log line + a step-summary flag (`halt_issue_failed`), and the
package stays HALTED without crashing the run (`ceremony.py:_file_halt_issue`, `801`). When you see
"HALT issue could NOT be filed" in the ceremony step summary, **file the issue manually** (or grant the
App the Issues permission — §8). The HALT itself is still surfaced in the summary and Slack. This
degradation path applies only when the code *attempts* an upsert (`HALT_TESTPYPI` + precondition HALTs)
— not to `HALT_PUBLISH`.

## 5. Rollback procedures

### 5.1 Quiesce the whole train instantly (no code change)

```bash
gh variable set RELEASE_TRAIN_MODE --body off        # repo variable; next run is a green no-op
# or, for a single run:  gh workflow run release-train.yml -f mode=off
```

`off` skips detection and makes both write jobs unreachable (`release-train.yml:182-190`; plan §9.4/§11).
This is the primary rollback/disable switch.

### 5.2 Pause all writes but keep detection running

```bash
gh variable set RELEASE_TRAIN_MODE --body report     # detection continues; propose/ceremony disabled
```

`report` keeps the daily classification table + Slack signal while guaranteeing no PRs/Releases
(plan §11 "Rollback / disable").

### 5.3 Undo a bad Release (and its tag)

The ceremony's Release **creates** the sub-package tag (`ceremony.py:201-202`; procedure §11.4). To
recover a Release that should not have been cut — **before** the owner approves Gate 2 (nothing has
reached PyPI yet, since the deploy job is parked at the `pypi` environment):

```bash
gh release delete <tag> --repo pcalnon/<owning-repo> --cleanup-tag --yes
# if --cleanup-tag is unavailable, delete the tag explicitly:
git push --delete origin <tag>            # e.g. juniper-observability-v0.5.0
```

- **Never pre-create/push the `juniper-<pkg>-v*` tag by hand** before the ceremony. The Release must
  create it; the ceremony deliberately passes no `--verify-tag` (and `ceremony.py:_assert_gh_allowed`
  forbids `--verify-tag`, `ceremony.py:201-202`). A pre-existing tag changes what the tag-triggered
  publish workflow checks out (the tag-ref gotcha; §8).
- Deleting the Release + tag also lets a corrected re-run start clean: the ceremony is idempotent and
  re-computes state from PyPI/Release truth (plan §8 last row; `ceremony.py:53-56`).

### 5.4 Close a bad proposal PR

Proposal PRs are standard-gated and merge nothing on their own. Simply close the PR (and delete its
branch); the dup-guard means a corrected re-dispatch will open a fresh one rather than duplicate it
(`propose.py` dup-guard). No environment or PyPI state is touched by a proposal PR (plan §7.4).

### 5.5 The immutable-index recovery stance (§11)

**PyPI and TestPyPI files are immutable**, and the publish steps use `skip-existing: true`
(plan §8 "Idempotent re-entry", citing `publish-service-core.yml:139,185`). Consequences for recovery:

- A **partial run is safe to re-enter**: a re-run re-computes state from PyPI/Release truth
  (`ceremony.py:plan_ceremony`). Operator-visible plan states:

  | Truth on re-entry | `plan.state` | Execute does | Step-summary bucket |
  |---|---|---|---|
  | PyPI already serves `target` | `ALREADY_RELEASED` | nothing (idempotent no-op) | already-released / DONE |
  | Release tag exists, PyPI not yet | `RESUME_MONITOR` | **only** `monitor_publish` — no `open_archive_pr` / `enable_automerge` / `create_release` | resume-monitor / RESUME |
  | Neither | `CEREMONY_PLANNED` | full archive → auto-merge → cut Release → monitor | ceremony / CEREMONY |

  `plan_state` stays at the classification while `state` becomes the monitor verdict
  (`ceremony.py:980-983`). On `RESUME_MONITOR` + `HALT_TESTPYPI`, the train files the dedup issue and
  stops **without** re-cutting (`ceremony.py:1016-1024`; juniper-ml#726). Do **not** delete a healthy
  Release just to "start over" when you only need Gate 2 or another monitor poll — re-dispatch
  `mode=ceremony` (§3.3).
- You **cannot** "un-publish" a version by overwriting it — if a bad version reaches PyPI, **yank** it on
  PyPI and ship a fixed higher version. The train will then see the yank and classify accordingly.
- Only **one train runs at a time** (`concurrency: group: release-train, cancel-in-progress: false`,
  `release-train.yml`), so two runs never race the same immutable index (plan §8).

## 6. Owner setup actions (one-time, provisioning)

These are **not** train actions — they are owner console/CLI actions the train depends on:

| Item | What | Why |
|---|---|---|
| `RELEASE_TRAIN_MODE` | repo variable (`off`/`report`/`propose`/`ceremony`) | the mode + kill switch (§2/§5) |
| `RELEASE_TRAIN_APP_ID` | repo variable = the GitHub App's id | gates the App-token mint step (`release-train.yml:399`, `605`) |
| `RELEASE_TRAIN_APP_PRIVATE_KEY` | repo secret = the App private key | minted into the cross-repo token (§7) |
| `SLACK_WEBHOOK_URL` | repo secret (optional) | the non-blocking Slack summary (`release-train.yml:325-366`) |

**Verify-before-first-cron (mandatory).** After any change to the train, trigger it once with
`gh workflow run release-train.yml` and confirm the run behaves before trusting the daily cron
(plan §11; a lint-green workflow is not a runtime-green workflow).

## 7. The App identity & the R7 invariant (in operator terms)

**Scope.** The cross-repo write identity is a **GitHub App installation token** minted per write job
(`actions/create-github-app-token`, SHA-pinned, `release-train.yml:400`, `606`), scoped to exactly the
**8 publishing repos** (juniper-ml, -data, -data-client, -cascor, -cascor-client, -cascor-worker,
-canopy, -recurrence). The mint step is gated on `vars.RELEASE_TRAIN_APP_ID` so an absent App config
**degrades gracefully** to the built-in single-repo `GITHUB_TOKEN`.

**What the identity may do (and nothing else) — R7 (plan §9.3).** The ceremony routes every `gh` call
through `ceremony.py:_assert_gh_allowed` (`197`), which permits **exactly**
`{pr create, pr merge --auto, release create, run list/view, issue create/edit}`
(`GH_MUTATING_SURFACE`, `ceremony.py:150`) — **plus the archive lane's two GitHub-signed-commit calls**
(a `repos/<owner>/<repo>/git/refs` POST and a `createCommitOnBranch` GraphQL mutation) — and rejects any
`environment` / `deployment` / `review` / `--admin` token (`GH_FORBIDDEN_TOKENS`, `ceremony.py:177`), a
bare `pr merge` without `--auto`, or a `release create --verify-tag`. `api` **stays forbidden for the
general surface**; the sole carve-out is those two archive-lane calls, dispatched to the sibling
assertion `_assert_api_allowed` (`ceremony.py:283`) which accepts ONLY a `git/refs` POST with an
**explicit** `ref=refs/heads/*` field — missing or empty `ref=` is also a `SeamViolation` (juniper-ml#770;
pre-#770 only rejected a *present* non-heads value and deferred an omitted `ref=` to the live GitHub API) —
or a `createCommitOnBranch` body with `repoWithOwner` bound. Every other `gh api` (a different path, a
different mutation, a non-POST ref write, an out-of-allowlist repo) raises `SeamViolation`. Every `--repo`
— and both archive-lane calls' repo bind — is bounded to the 8 publishing repos. **The identity is never
a `pypi` environment reviewer and never approves/mutates a deployment** — PyPI approval stays owner-only
(Gate 2). The workflow-level `contents: read` plus the two mode-gated write jobs are pinned by
`tests/test_release_train_workflow_guard.py`; the archive-lane api carve-out and its negative cases
(including missing/empty `ref=`) are pinned by `tests/test_release_train_ceremony.py`.

#### R7 archive-lane `ref=` contract (juniper-ml#770)

A ceremony log matching `archive-branch ref create must target refs/heads/*, got ref=None` (or `ref=''`)
is a **code** `SeamViolation` from `_assert_api_allowed` — not an auth/network blip and not an operator
recovery path. Do **not** hand-craft a `gh api …/git/refs` POST to "fix" it. Confirm juniper-ml#770 is on
the train's checkout, then re-dispatch `ceremony`; if it still fires, the call site omitted `ref=` (file a
bug — the happy path always passes `ref=refs/heads/release-notes/…`). Hermetic pin:
`tests/test_release_train_ceremony.py` (`test_assert_api_allowed_rejects_refs_post_without_ref_field`).

**Runner git identity (headless, unsigned) — must be `--global`.** Both write jobs run a
`Configure git identity (headless, unsigned)` step that sets `user.name`, `user.email`, and
`commit.gpgsign false` via `git config --global` (`release-train.yml:466-478` propose,
`675-687` ceremony). Cross-repo `propose` commits inside freshly-cloned **sibling** checkouts; a
repo-local `git config` on the juniper-ml checkout alone leaves those clones with
`Author identity unknown` (first cross-repo pilot failure, run 30040138774; fixed juniper-ml#705).
The hosted runner is ephemeral, so `--global` is still job-scoped. `propose.py` also passes
`-c commit.gpgsign=false` on its commit so a YubiKey-resident signing config never reaches a headless
run. The detect job must not configure identity (it never commits).

**Runner git identity (headless, unsigned) — must be `--global`.** Both write jobs run a
`Configure git identity (headless, unsigned)` step that sets `user.name`, `user.email`, and
`commit.gpgsign false` via `git config --global` (`release-train.yml:466-478` propose,
`675-687` ceremony). Cross-repo `propose` commits inside freshly-cloned **sibling** checkouts; a
repo-local `git config` on the juniper-ml checkout alone leaves those clones with
`Author identity unknown` (first cross-repo pilot failure, run 30040138774; fixed juniper-ml#705).
The hosted runner is ephemeral, so `--global` is still job-scoped. `propose.py` also passes
`-c commit.gpgsign=false` on its commit so a YubiKey-resident signing config never reaches a headless
run. The detect job must not configure identity (it never commits).


**Ruleset bypass (2026-07-29).** Beyond the workflow-side R7 fence above, the App is a juniper-ml
**repository-ruleset bypass actor** in `pull_request` mode — the narrowest scope that lets the armed
archive-lane auto-merge clear the unsatisfiable `code_quality` rule (and the strict up-to-date policy on
serial archive PRs). The bypass applies **only to merging PRs on juniper-ml**; it grants nothing on the
`pypi` environments (Gate 2 stays owner-only) and nothing outside pull-request merges.

## 8. Known limitations (accepted)

1. **Degraded no-App mode (in-repo only).** When `RELEASE_TRAIN_APP_ID` is unset, `propose`/`ceremony`
   run on the built-in `GITHUB_TOKEN` and **skip sibling-repo packages** with a clear reason
   (`ceremony.py:writable_repo_skip_reason`, `377`); only juniper-ml packages (the meta + 6 sub-packages)
   are acted on. Additionally, a PR opened with `GITHUB_TOKEN` does **not** auto-trigger CI (GitHub's
   recursion guard), so a proposal PR shows no checks until re-triggered (close/reopen, or push an empty
   commit). When the App token IS minted, PRs are opened by the App identity and CI runs normally.
2. **Issues permission (HALT-issue degradation) — RETIRED 2026-07-30.** Owner-verified: the App's
   repository permissions include **Issues: Read and write** (and were already granted pre-verification),
   the installation carries it, and the mint steps pass no `permission-*` narrowing — so minted tokens
   hold Issues write and the HALT-issue upsert will succeed when a HALT fires. No live HALT has yet
   exercised the path (all ceremony runs to date were happy-path); the graceful-degradation branch
   (loud log + `halt_issue_failed` step-summary flag, never a crash) REMAINS in the code as defense
   against a future permission regression — if the flag ever appears, re-check the installation grant.
3. **Tag-ref workflow gotcha (0.4 backfill).** Some legacy sub-package releases were shipped **tag-only**
   (a bare `git push <tag>`) rather than by cutting a GitHub Release — the convention now being restored
   (CLAUDE.md "Release convention"; plan §12 step 0.4). The ceremony **always cuts a Release** (never a
   bare tag) and never pre-creates the tag, so it does not reproduce that gotcha. Operator corollary:
   when recovering by hand, **cut a Release** (or delete Release + tag together, §5.3) — never push a
   bare `juniper-<pkg>-v*` tag, which would trigger the tag/`release`-driven publish workflow against a
   tag the Release did not create.
4. **Cross-repo pilot is owner-triggered.** The first live cross-repo `propose` dispatch
   (run 30040138774, `packages=juniper-cascor-worker`) failed at the commit step with
   `Author identity unknown` — **nothing was pushed** (worker repo stayed clean). Fixed by
   juniper-ml#705 (`git config --global` on both write jobs; §7). A successful cross-repo write
   (propose PR opened in a sibling, or ceremony cutting a sibling Release) still needs an owner
   re-dispatch to prove. Hermetic tests + `--dry-run` cover the logic
   (`tests/test_release_train_ceremony.py`).
5. **Archive-PR signature gate (RESOLVED 2026-07-23).** The juniper-ml ruleset's `required_signatures`
   rule evaluates a PR's source commits, so the exempt archive PR only auto-merges if its commit is
   signed. It now is: the archive branch + commit are created through the GitHub API (`git/refs` POST +
   `createCommitOnBranch`), yielding a **GitHub-signed / Verified** commit under the App / `GITHUB_TOKEN`
   identity (§3.3). Previously the commit was a plain unsigned runner-side `git commit`, so an all-green
   archive PR stayed BLOCKED behind that rule until an owner admin one-click (2026-07-23 run 30051952226
   / ml#707). Owner one-click is now only the degraded/manual fallback (e.g. `allow_auto_merge` off). No
   security-posture change — the PyPI deploy still waits at the owner-gated `pypi` environment (Gate 2).
   The **live proof** (an archive PR auto-merging with zero clicks) rides the next real ceremony dispatch.
6. **Summary / Slack `<<'PY'` late-failure class (RESOLVED #708 + #723).** Detect / propose / ceremony
   step-summary and Slack payload steps embed Python via `python - <<'PY' … PY`. A duplicated or missing
   `PY` terminator (run 30051952226 / ml#708) or a syntax-broken heredoc body (ml#723) fails **after**
   the real work finishes — the job goes red even though Gate 1/2 side effects already landed. Operator
   response: treat the run's proposal / archive / Release / `PENDING_PYPI_APPROVAL` outcomes as
   authoritative; fix the YAML and re-run only if a summary/Slack signal is still needed. Developers
   editing those blocks must keep openers and terminators 1:1 and keep each body `compile()`-clean —
   pinned by `HeredocBalanceTest` + `HeredocCompileTest` in `tests/test_release_train_workflow_guard.py`
   (four bodies today: detect summary, detect Slack, propose summary, ceremony summary).
7. **Sibling `Author identity unknown` (RESOLVED 2026-07-23, ml#705).** A red `propose` /
   `ceremony` job that dies at `git commit` inside a sibling clone with
   `Author identity unknown` / `Please tell me who you are` means the write job's identity step
   regressed to **repo-local** `git config` (or was removed). Confirm both write jobs still use
   `git config --global user.name|user.email|commit.gpgsign` (`release-train.yml:473-478`,
   `682-687`). Nothing is pushed when this fires — safe to re-dispatch after the workflow fix.
   Structural pin: juniper-ml#718 (`tests/test_release_train_workflow_guard.py` invariant `(g)`).


5. **`code_quality` ruleset rule blocks all non-bypass merges (fleet-wide).** Most repo rulesets carry a
   `code_quality` (severity: errors) rule with **no code-quality tool reporting**, so ordinary auto-merge
   can never complete anywhere — only bypass actors (owner-admin, or the App on juniper-ml) merge.
   Accepted for now (option B, 2026-07-29): removal (option A) is deferred until the code-signing work is
   configured, at which point the rule set can be revisited repo-by-repo. Related: PRs with **unsigned**
   runner-side commits are additionally held by `required_signatures` (by design — owner YubiKey flow;
   the archive lane avoids it via API-created, GitHub-signed commits).

## 9. Quick reference

```bash
# Read the latest report run
gh run list --workflow release-train.yml --limit 5
gh run view <run-id>                         # step summary + artifacts

# Kill switch / pause
gh variable set RELEASE_TRAIN_MODE --body off      # quiesce entirely
gh variable set RELEASE_TRAIN_MODE --body report   # detection only, no writes

# Opt-in write runs (owner)
gh workflow run release-train.yml -f mode=propose  -f packages=juniper-observability   # Gate 1 PRs
gh workflow run release-train.yml -f mode=ceremony -f packages=juniper-observability   # archive PR + Release -> Gate 2

# Recover a mis-cut Release (before Gate 2 approval)
gh release delete <tag> --repo pcalnon/<owning-repo> --cleanup-tag --yes
```

## 10. References

- Plan: [`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md)
  — §5 states, §5.4 atomicity co-changes (incl. static `_version.py` lockstep), §8 HALT preconditions,
  §9.2-9.4 identity + R7 + rollback switch, §10.2 central archive, §11 failure/observability/rollback,
  §12 phased plan (steps 1.3/2.2/4.1/4.3).
- Static-with-dunder lockstep design + implementation record:
  [`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)
  (ml#701 / juniper-ml#710; edge-case coverage + already-at-target checklist fix juniper-ml#712).
- Orchestrator: [`.github/workflows/release-train.yml`](../.github/workflows/release-train.yml).
- Engines: `util/release_train/detect.py`, `propose.py`, `ceremony.py`, `registry.yaml`.
- Guards: `tests/test_release_train_workflow_guard.py` (R7 boundary + mode matrix + summary
  rehearsal + write-job `--global` git identity, ml#705 / #718 + `HeredocBalanceTest` /
  `HeredocCompileTest` for every `<<'PY'` block — ml#708 / ml#723),
  `tests/test_release_train_ceremony.py` (ceremony + HALT-issue degradation),
  `tests/test_release_train_registry.py::VersionDunderLockstepTest` (static pyproject == dunder, ml#701),
  `tests/test_release_train_propose.py` (sibling/meta AGENTS.md step-5/5a shapes — worker#140 / ml#706 / #720;
  CHANGELOG refuse clear-on-refuse stub shape — juniper-ml#751).
- Static `_version.py` lockstep (Gate 1 review):
  [`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)
  §6 / §6.1 (implemented by juniper-ml#710; hardened by juniper-ml#712).
- Notes-draft + healthy-hygiene operator edges (Gate 1 title/MAJOR/Breaking; `TAG_ONLY`/`NOTES_MISSING`
  clear when Release + archive exist): coverage juniper-ml#756; this runbook §3.1 / §3.2.
- `link_base` relative-link rewrite (central-archive correctness; canopy v0.6.0 404 class): coverage
  juniper-ml#877; this runbook §3.2 “Gate 1 review — notes draft”.
- Release convention (cut a Release, archive notes centrally): repo `AGENTS.md` "Publishing" +
  [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.
