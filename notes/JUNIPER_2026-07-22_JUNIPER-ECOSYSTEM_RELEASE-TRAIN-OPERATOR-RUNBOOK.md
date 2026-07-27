# Juniper PyPI Release-Train — Operator Runbook

**Project**: Juniper — PyPI release-train automation
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.2.3
**Last Updated**: 2026-07-26

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

#### When you see `SHIP_UNCERTAIN` (soft-fail — do not treat as up-to-date)

`SHIP_UNCERTAIN` is an **action** classification (`ACTION_CLASSIFICATIONS`, `detect.py:98`): the daily
report and Slack "Needs release action" count include it, and exit 1 is expected. It means the detector
**could not prove** ship or no-ship — never invent `UP_TO_DATE` / `BUMPED_NOT_RELEASED` from a soft fail
(`classify_package`, `detect.py:885-974`). Read the per-package note lines under the step summary (also in
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

#### Hygiene line: `TAG_ONLY` / `NOTES_MISSING` (orthogonal to "needs deploy")

The table footer `hygiene: TAG_ONLY=…, NOTES_MISSING=…` (`detect.py:996-999`) counts packages whose
last released version lacks a GitHub Release (`tag_only`) or a central `notes/releases/` archive
(`notes_missing`). Both are **convention debt**, not deploy triggers.

- **True `tag_only`**: tag exists but no GitHub Release for it — restore the Release ceremony (§8 item 3 /
  plan §12 step 0.4); do not push a bare tag.
- **`tag_only` unavailable** (`None`): `list_releases` raised `SourceError` (gh blip). The detector keeps
  the package classification (often `UP_TO_DATE`), sets `hygiene.tag_only = None` (falsy → **not** counted
  in `TAG_ONLY=`), still evaluates `notes_missing`, and appends
  `release-hygiene (tag_only) unavailable: …` (`detect.py:971-973`; coverage juniper-ml#761). **Do not**
  treat a quiet `TAG_ONLY=0` plus that note as "hygiene cleared" — re-check Releases when gh recovers.
  A regression that re-raises would exit 2 the whole detect job; inventing `tag_only=True` would spam false
  TAG_ONLY on every blip.

### 3.2 Dispatching `propose` against specific packages (Gate 1)

```bash
# Open standard-gated proposal PRs for one (or a few) packages. Empty `packages` = all eligible.
gh workflow run release-train.yml -f mode=propose -f packages=juniper-observability
```

- The `packages` input is whitespace/comma-separated `pypi_name`s, validated against the pypi-name
  charset (`release-train.yml`, the propose run step's parser). Empty = all eligible.
- The resulting PRs are **standard-gated**: the owner reviews and merges them. This is **Gate 1** (the
  version bump only ships with owner approval; plan §5.3).
- **In-repo pilot vs cross-repo**: with the GitHub App token minted (§7 below) sibling-repo packages get
  PRs in their own repos; on the degraded no-App path only juniper-ml packages are proposed and siblings
  are skipped with a clear reason.

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

**Pitfalls:**

- A meta proposal titled `# juniper-ml …` means `display_name` drifted — fix before ceremony archives it.
- A MAJOR bump labeled PATCH (or Breaking stuck at NO despite a `### Removed` section) means the
  bump→`release_type` map or the Removed membership check drifted.
- Prefer `-` in hand-edited CHANGELOG, but do not reject a proposal solely because Unreleased used `*`.

Coverage pins: `tests/test_release_train_propose.py` (juniper-ml#756).

### 3.3 Dispatching `ceremony` against specific packages (drives toward Gate 2)

```bash
# Run the exempt-archive + Release ceremony for BUMPED_NOT_RELEASED packages.
gh workflow run release-train.yml -f mode=ceremony -f packages=juniper-observability
```

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
  train** (plan §5.1). If the run is still building at timeout it reports `IN_PROGRESS` (honest; re-run
  ceremony mode to resume — it is idempotent).
- Two **failure** terminals are distinct (§4): `HALT_TESTPYPI` (TestPyPI job failed → dedup issue) vs
  `HALT_PUBLISH` (run completed `failure`/`cancelled`/`timed_out` after TestPyPI succeeded → note only,
  no issue). Do not expect a GitHub issue for the latter.
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
- **Gate 2 is yours**: the publish workflow's `pypi`-environment deploy job waits for the owner to
  approve. The train never approves it (§7). Approve it in the run's environment-review UI when ready.
- **Re-entry is a named plan state, not a full re-ceremony.** When the Release tag already exists,
  `plan_ceremony` sets `plan.state = RESUME_MONITOR` and the action list is **only** `monitor_publish`
  (`ceremony.py:892-897`). Execute keeps `plan_state=RESUME_MONITOR` while `state` becomes the monitor
  verdict (`PENDING_PYPI_APPROVAL` / `HALTED` / …) — so the ceremony step summary buckets it under
  **resume-monitor**, not a new ceremony (`ceremony.py:980-983`, `release-train.yml:775-789`). A
  TestPyPI failure on resume still HALTs and files `testpypi-verify-failed` **without** re-opening the
  archive PR or re-cutting the Release (`execute_ceremony` monitor branch, `ceremony.py:1016-1024`;
  coverage: juniper-ml#726). Distinct from `ALREADY_RELEASED` (PyPI already serves the target — pure
  no-op, `ceremony.py:861-866`). See §5.5.

**Archive-lane failure edges (signed API path — do not invent a sha).** The happy path above is the
common case. When a ceremony fails *inside* `open_archive_pr` / `create_branch` / `create_signed_commit`
(`ceremony.py:688-765`), treat these as **hard stops that must never invent a base sha or commit onto a
ghost tip** (pinned by `tests/test_release_train_ceremony.py` / juniper-ml#714). They surface as
`SourceError` (or `SeamViolation` for R7 code bugs) and stop that package's ceremony before a bad
archive commit lands:

| Symptom in the ceremony log | Cause | Operator response |
|---|---|---|
| `could not resolve origin/<base> … to base the archive branch on` | `git rev-parse origin/<base>` returned empty after fetch (`open_archive_pr`, `ceremony.py:758-760`) — **no** `git/refs` POST and **no** GraphQL commit are issued | Confirm the juniper-ml checkout has a freshened `origin/main` (clone depth / fetch failure). Re-run ceremony once the ref resolves; never hand-push an archive branch at a guessed sha. |
| `gh failed (api repos): HTTP 401` (or any non-422 refs error) | Branch-create POST failed for auth/transport; `create_branch` re-raises and **does not** enter tip-inspection (`ceremony.py:703-705`) | Check the App / `GITHUB_TOKEN` credentials and `contents: write` on juniper-ml. A 401 is **not** the idempotent "branch already exists" path. |
| `archive branch … exists on origin but its tip could not be resolved` | 422/already-exists re-entry, but `FETCH_HEAD` tip was empty (`ceremony.py:708-710`) — HALT rather than commit onto a ghost tip | Inspect `release-notes/<pkg>-v<ver>` on origin; delete or reset the branch by hand if it is corrupted, then re-run. |
| `archive branch … exists but diverged from base …` | Branch tip is neither `origin/<base>` nor a single archive commit atop it (`ceremony.py:716`) | Human resolve: close/delete the stray branch (or the open archive PR) so re-entry can recreate a clean one-commit branch. |
| Signed commit returns empty oid / PR still opens | Malformed or empty `createCommitOnBranch` GraphQL payload — oid extraction is best-effort and returns `""` without raising (`ceremony.py:743-747`); `gh pr create` still runs | Inspect the archive PR tip commit; if the file is missing, close the PR + delete the branch and re-run. Do not treat an empty oid alone as success proof. |

**Idempotent re-entry (expected shapes).** When the archive branch already exists (HTTP 422 /
"already exists"), `create_branch` reuses it only in two safe shapes (`ceremony.py:692-716`): tip ==
`origin/<base>` (commit onto it) or tip's parent == base (single archive commit already present — skip
re-commit). Anything else is the diverged HALT above. Forbidden tokens (`environment` / `deployment` /
`review` / …) riding an otherwise-sanctioned `git/refs` POST or `createCommitOnBranch` call still raise
`SeamViolation` (`_assert_api_allowed`, `ceremony.py:297-299`) — that is a **code** bug, not an operator
recovery path.

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
| `main-ci-not-green` | target `main` CI latest conclusion ≠ `success` | `ceremony.py:735` | Fix `main` CI (owner rule: check main green before blaming a red PR); re-run ceremony. |
| `declared-lt-released-anomaly` | declared version < the version PyPI already serves (yank/rollback) | `ceremony.py:724` | Investigate the PyPI yank/rollback manually; do NOT release. Reconcile the declared version. |
| `pypi-truth-missing` | manifest said released, but PyPI now returns no version | `ceremony.py:726` | A first-publish/yank a human must resolve — confirm the trusted-publisher config (procedure §3.3) before re-running. |
| `changelog-section-missing` | no non-empty `CHANGELOG [<version>]` section to source the notes | `ceremony.py:741` | The proposal PR (Gate 1) should have created it — merge the proposal first, or add the section, then re-run. |
| `notes-render-failed` | `notes_render.render_notes` raises `OSError` while building the final archive body from `CHANGELOG [<version>]` (missing/unreadable `notes/templates/TEMPLATE_RELEASE_NOTES.md`, or the security template when a `Security` category is present) | `ceremony.py:887-890` | Distinct from `changelog-section-missing`. Restore the template under ceremony `--repo-root` (juniper-ml), confirm CI can read it, re-run — no Release was cut. Coverage: juniper-ml#741. |
| `missing-declared-version` | manifest has no `declared_version` for a `BUMPED_NOT_RELEASED` pkg | `ceremony.py:711` | A malformed manifest — re-run detection (`report` mode) to regenerate it. |
| `not-in-registry` | package is `BUMPED_NOT_RELEASED` in the manifest but absent from `registry.yaml` | `ceremony.py` (`_plans_for`) | Add the package to `util/release_train/registry.yaml` (registry lint gates it). |
| `testpypi-verify-failed` | (during the monitor) `classify_publish_run` → `HALT_TESTPYPI`: a job whose name contains `testpypi` concluded `failure` | `ceremony.py:514-515`, `1018-1023` | The run is not healthy — inspect the publish run's TestPyPI job; fix and re-cut is idempotent. A dedup issue **is** filed. |

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
assertion `_assert_api_allowed` (`ceremony.py:283`) which accepts ONLY a `git/refs` POST creating a
`refs/heads/*` ref or a `createCommitOnBranch` body with `repoWithOwner` bound — every other `gh api`
(a different path, a different mutation, a non-POST ref write, an out-of-allowlist repo) raises
`SeamViolation`. Every `--repo` — and both archive-lane calls' repo bind — is bounded to the 8
publishing repos. **The identity is never a `pypi` environment reviewer and never approves/mutates a
deployment** — PyPI approval stays owner-only (Gate 2). The workflow-level `contents: read` plus the two
mode-gated write jobs are pinned by `tests/test_release_train_workflow_guard.py`; the archive-lane api
carve-out and its negative case are pinned by `tests/test_release_train_ceremony.py`.

**Runner git identity (headless, unsigned) — must be `--global`.** Both write jobs run a
`Configure git identity (headless, unsigned)` step that sets `user.name`, `user.email`, and
`commit.gpgsign false` via `git config --global` (`release-train.yml:466-478` propose,
`675-687` ceremony). Cross-repo `propose` commits inside freshly-cloned **sibling** checkouts; a
repo-local `git config` on the juniper-ml checkout alone leaves those clones with
`Author identity unknown` (first cross-repo pilot failure, run 30040138774; fixed juniper-ml#705).
The hosted runner is ephemeral, so `--global` is still job-scoped. `propose.py` also passes
`-c commit.gpgsign=false` on its commit so a YubiKey-resident signing config never reaches a headless
run. The detect job must not configure identity (it never commits).

## 8. Known limitations (accepted)

1. **Degraded no-App mode (in-repo only).** When `RELEASE_TRAIN_APP_ID` is unset, `propose`/`ceremony`
   run on the built-in `GITHUB_TOKEN` and **skip sibling-repo packages** with a clear reason
   (`ceremony.py:writable_repo_skip_reason`, `377`); only juniper-ml packages (the meta + 6 sub-packages)
   are acted on. Additionally, a PR opened with `GITHUB_TOKEN` does **not** auto-trigger CI (GitHub's
   recursion guard), so a proposal PR shows no checks until re-triggered (close/reopen, or push an empty
   commit). When the App token IS minted, PRs are opened by the App identity and CI runs normally.
2. **Issues permission (HALT-issue degradation).** The App installation may not have the **Issues**
   permission (owner-grantable later). Until then, a HALT that would file a dedup issue in a sibling repo
   degrades to a loud log + step-summary flag and does not crash the run (§4). Operator response: file
   the issue manually, or grant the App the Issues permission on the 8 repos.
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
- Propose CLI registry-miss skip + `--execute` seam gates (operator §3.2): juniper-ml#764
  (`CliTest.test_manifest_package_absent_from_registry_is_skipped` + `ExecuteProposalSeamTest`).
- Guards: `tests/test_release_train_workflow_guard.py` (R7 boundary + mode matrix + summary rehearsal),
  `tests/test_release_train_ceremony.py` (ceremony + HALT-issue degradation),
  `tests/test_release_train_registry.py::VersionDunderLockstepTest` (static pyproject == dunder, ml#701),
  `tests/test_release_train_propose.py` (sibling/meta AGENTS.md step-5/5a shapes — worker#140 / ml#706 / #720;
  CHANGELOG refuse clear-on-refuse stub shape — juniper-ml#751).
- Static `_version.py` lockstep (Gate 1 review):
  [`JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md`](JUNIPER_2026-07-23_JUNIPER-ML_RELEASE-TRAIN-VERSION-DUNDER-LOCKSTEP-FOLLOWUP.md)
  §6 / §6.1 (implemented by juniper-ml#710; hardened by juniper-ml#712).
- Release convention (cut a Release, archive notes centrally): repo `AGENTS.md` "Publishing" +
  [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.
