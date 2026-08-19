# Memory Proposal C — Ruthless Deduplication and Pruning to a Navigational Core

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## 0. The bet, in one paragraph

`AGENTS.md` does not need a new loading mechanism. It needs to stop carrying content
that officially does not belong in a memory file and that already exists elsewhere in
this repository. Measured below: **96% of the distinctive tokens** in its three largest
sections are recoverable from `docs/REFERENCE.md`, `notes/`, or the code those sections
describe; **71%** of the `### Utilities` bytes sit under a `docs/REFERENCE.md` section on
the same subject; the `### Tests` prose is a **stale 55-of-88** copy of a list that
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) maintains correctly at 87-of-88.
The remedy is subtractive: delete the duplicates, relocate the genuinely-unique residue,
and leave a **≤200-line navigational core** that tells an agent *where to look*.

This proposal is honest about its two hard limits, and neither is fixable by trying
harder. First, **pruning converts free knowledge into a tool call that may never happen**
(§7). Second, **pruning changes the level, not the rate** — at the measured accretion the
core is back over 40,000 characters in 8–12 days and back at today's size in 52–76 days
(§9). The prune is therefore only half the proposal; the size-and-shape gate in §6/E6 is
the other half, and the proposal should be judged on both.

---

## 1. Grounding, method, and the limits of the method

All measurements taken 2026-08-18 in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`
at `main` = `e209b74`, clean tree. Mechanism claims are grounded in
[the mechanism fact base](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md);
size and growth claims in
[the baseline measurements](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md).
Nothing here re-derives or contradicts either.

### 1.1 One precision note, additive to the fact base

`wc` reports [`AGENTS.md`](../AGENTS.md) as **1,115 lines / 168,317 characters / 170,137
bytes**. The 1,820-byte gap is multi-byte UTF-8 punctuation (em dashes, arrows, `×`). The
baseline document's *headline* figure (170,137) is bytes; its *per-section* table
(99,304 / 20,469 / 16,101 / 4,617) is characters — I reproduced those four numbers
exactly on a character basis. This matters only because the shipped check compares
`s.content.length`, a JS string length (mechanism fact base §1), so the number the CLI
actually sees is 168,317. **No conclusion changes**: 168,317 is 4.21× the 40,000 floor
rather than 4.25×. Every table in this document is in **characters**, labelled.

### 1.2 The two measures used, and what each cannot see

**Measure A — subject coverage.** For each top-level `- \`subject\`` bullet in
`### Utilities` / `### Tests` / `### CI/CD Workflows`, does `docs/REFERENCE.md` carry a
section on that subject? Over-counts (a passing mention scores as covered) and
under-counts (a glob like `ci-*.yml` fails literal matching although
`docs/REFERENCE.md:1226 ## Shared-Package CI Workflows` covers it). Both directions were
corrected by hand for every entry over 500 characters.

**Measure B — token recoverability.** Extract every backticked token of 3–60 characters
from an entry (identifiers, flags, paths, constants) and ask whether that literal string
occurs in (a) `docs/*.md`, (b) `notes/**/*.md`, (c) the source the entry describes.
This is a **lower bound on loss, not a proof of no loss**: it measures whether the
*nouns* survive, not whether the *reasoning* does. Prose paraphrase is invisible to it.
It is used here to bound the relocation work, never to license a deletion on its own —
every deletion in §12 is justified by Measure A or by a named authoritative file.

Scripts used were throwaway analysis kept in the session scratchpad; nothing was added to
the repository. The two reproducible artifacts already committed by the fact-base work are
[`util/ad-hoc/2026-08-18_agents_md_growth_curve.bash`](../util/ad-hoc/2026-08-18_agents_md_growth_curve.bash)
and
[`util/ad-hoc/2026-08-18_build_memory_import_probe.bash`](../util/ad-hoc/2026-08-18_build_memory_import_probe.bash).

---

## 2. The overlap, measured

### 2.1 Subject-level coverage map

| `AGENTS.md` section | Chars | Entries | Chars whose subject has a `docs/REFERENCE.md` section | % |
|---|---:|---:|---:|---:|
| `### Utilities` (405–596) | 54,510 | 35 | 38,650 | **71%** |
| `### Tests` (599–712) | 34,579 | 57 | 12,753 | 37% |
| `### CI/CD Workflows` (715–742) | 8,136 | 13 | 6,795 literal → **8,136 after glob correction** | **100%** |
| `## CI/CD Pipelines` (753–844) | 16,101 | 8 subsections | ≈16,101 (six named `REFERENCE.md` sections) | ≈100% |

`### Tests`'s low score is not evidence of unique content — it is evidence that
`docs/REFERENCE.md` is the wrong destination for it. The authoritative test inventory is
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (§2.4).

`docs/REFERENCE.md` is 1,865 lines / 161,487 characters, with 73 sections on the same
subjects. It is not a stale target: **85 commits touched it since 2026-06-01**, the most
recent today (`604fefc docs(reference): declare the startup port overrides…`), and it grew
from 16,008 bytes on 2026-06-01 to 59,140 on 2026-08-01 to 162,231 today.

### 2.2 Three worked side-by-sides

**(a) `util/reap_pytest_orphans.bash` — 1,534 chars in `AGENTS.md:407–413`, 100% duplicated.**

| `AGENTS.md` claim | `docs/REFERENCE.md` location |
|---|---|
| purpose + `--dry-run` / `--verbose` | `493–506` (prose + a three-line invocation block + the exit codes) |
| candidate awk gate; empty set exits 0 | `507–516` *"Candidate awk filter (false-positive wall)"*, as a numbered 3-condition list |
| orphan predicate; `KEEP`; `SKIPPED` races | `534–543` *"Orphan decision and SKIPPED races"* |
| live-experiment protection checked first | `517–533` *"Live-experiment protection (checked FIRST)"* |
| P1 pidfile / P2 cmdline, `PROTECT` always | `525–528`, as a two-row table with a *Catches* column, plus the over-protection rationale at `533` |
| the 2026-08-16 `e-j-h2h-wide-cap6` incident | `521`, with the additional detail that a live sweep would have destroyed a multi-hour campaign |
| test hooks `JUNIPER_REAP_PROC_ROOT` / `_KILL_CMD` | `545–551`, a four-row override table that also documents the two run-root vars and their defaults |

Every claim is present downstream, and in every case the downstream form is **richer**.
`AGENTS.md:413` already ends with an `Operator surface:` trailer whose markdown link
targets the very `docs/REFERENCE.md` § *Pytest Orphan Reaper* anchor above — the author
wrote the pointer *and* the summary.

**(b) `util/wait_for_checks.py` — 3,632 chars in `AGENTS.md:490–499`, the single largest
non-experiment utility entry, and documented in no other markdown file in the repo
except one session handoff prompt (`grep -rln wait_for_checks --include='*.md'` returns
`AGENTS.md` and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-18_defect-register-round-3-and-ci-waiter.md`).**

Measure A scores this 0% covered. Measure B scores it 86% recoverable — because the
knowledge is in the module's own docstring:

- `AGENTS.md:493` "**Trap 1 — terminal is defined POSITIVELY.**" ↔
  `util/wait_for_checks.py:20` "**Trap 1 -- terminal must be defined POSITIVELY.**"
- `AGENTS.md:494` "**Trap 2 — the rollup GROWS…**" ↔ `util/wait_for_checks.py:28`
  "**Trap 2 -- the rollup GROWS, so …**"
- the read-only property, the `[skip ci]` absent-forever case, the
  `update-branch -X PUT` signing-safe fix, and the 0/1/2/3 exit matrix all appear at
  `util/wait_for_checks.py:41–60`.

This entry is the clean case for the official EXCLUDE item *"anything Claude can figure out
by reading code"*: it is a third copy of a docstring written specifically so nobody has to
rediscover the traps.

**(c) The extras table — 2,050 chars in `AGENTS.md:881–892`, one of five copies.**

`pyproject.toml` `[project.optional-dependencies]` is mirrored in `AGENTS.md:883–891`,
`README.md:90`, `docs/QUICK_START.md:63`, and `docs/REFERENCE.md:59–78`. The repository's
response to this five-way duplication was not to remove copies but to build a lockstep
gate: `tests/test_pyproject_extras.py:200 ExtrasDocsLockstepTest`, documented at
`docs/REFERENCE.md:93–99` as *"Any edit … must co-update, in the same PR … Documented
extras tables in `AGENTS.md`, `README.md`, `docs/QUICK_START.md`, and this section"*.
That is the duplication tax made explicit: a permanent CI obligation created to keep four
redundant copies honest.

### 2.3 Token-level recoverability

Across `### Utilities` + `### Tests` + `### CI/CD Workflows`: **945** distinct backticked
tokens.

| Corpus | Tokens present | % |
|---|---:|---:|
| `docs/*.md` | 567 | 60% |
| `notes/**/*.md` | 772 | 82% |
| code (`util/**`, `tests/*.py`, `.github/workflows/*.yml`, `scripts/*.bash`) | 881 | **93%** |
| **at least one of the three** | **909** | **96%** |

Thirty-six tokens matched nowhere. Inspected individually, **most are artifacts of the
tokenizer** (prose fragments captured between backticks: `` `. Empty/` ``,
`` `-row naming the released` ``, `` `Releases so a` ``) or globs whose expansion exists
(`` `.github/workflows/ci-*.yml` ``). The genuine residue is small and specific:
`driver.stall_window_inert`, `execution.per_run_timeout_seconds` — both of which do occur
in code (`util/experiments/run_experiment.py:1557`, `util/experiments/run_suite.py:64`)
and failed only because my match was whole-token.

**Reading.** Subject-level uniqueness is **29%** of `### Utilities`; token-level
uniqueness is **≤4%** overall. The honest interpretation of the gap: the file is almost
entirely recoverable, but ~29% of its subjects lack a *curated destination section*.
Creating those sections is the real relocation work, and it is bounded (§2.5).

### 2.4 What the duplication has already cost — six verified defects

These were found by auditing the file against the repository. Each is on-thesis: it is
the failure mode of keeping a hand-maintained parallel copy.

| # | Defect | Evidence |
|---|---|---|
| 1 | `AGENTS.md:485` documents flags `--ref-type` / `--ref-name`. The script parses **`--ref`** and its header explicitly explains the rejection of the two-flag form. | `util/assert_release_tag.bash:64` `--ref) REF="${2:-}"`; `:38–41` *"taken as the FULLY-FORMED `github.ref`, not `github.ref_name` plus a separate `github.ref_type`"*; `tests/test_assert_release_tag.py:42` drives `"--ref"` |
| 2 | `AGENTS.md:381` states the package version is `0.6.0`. | `pyproject.toml:7` `version = "0.7.1"`; `AGENTS.md:7` `**Version**: 0.7.1`. The existing gate `tests/test_agents_md_version_drift.py` checks only the header, so it passes over a contradiction two lines apart in the same file. |
| 3 | `AGENTS.md:381` lists the extras as `clients, worker, servers, tools, doc-tools, all` — omitting `recurrence`, which the same file lists at `:887`. | `pyproject.toml` `[project.optional-dependencies]` |
| 4 | `### Tests` names **55 of 88** real test files. 33 are absent, including `test_wait_for_checks.py`, `test_run_suite.py`, `test_juniper_plant_all.py`, `test_publish_testpypi_verify.py`, and every `test_main_verify_*.py`. The "Run all tests" block at `:39–94` names a *different* 54 — three files appear in one list and not the other, four in the reverse. | `ls tests/test_*.py` = 88 |
| 5 | The Repository-Structure tree omits `codeql.yml`, `agents-md-touch-up.yml`, `pr-budget-alarm.yml`, and two of three shipped skills (`service-smoke`, `ui-test-author`) — while the same file describes `tests/test_service_smoke_skill_lint.py` and `tests/test_ui_test_author_skill_lint.py` at length. `tests/test_agents_md_tree_drift.py` passes because it only checks top-level directories. | `ls .github/workflows/`, `ls .claude/skills/` |
| 6 | `AGENTS.md:626` calls `tests/test_assert_release_tag.py` "the gate" for `util/` (which is outside every pre-commit Python hook). **No workflow runs it.** It is the only one of 88 test files absent from `.github/workflows/ci.yml`, and neither `ci.yml` nor `main-verify.yml` uses `unittest discover`. | `grep -rn 'assert_release_tag' .github/workflows/` returns only the seven publishers invoking the *bash script* |

Defect 6 is the sharpest illustration available. The file asserts a protection that does
not exist (`AGENTS.md:626`, and the run-block entry at `:64`), for a script whose own history records that a `tr` portability bug once made
its central assertion **pass vacuously** (`AGENTS.md:483`; fix at
`util/assert_release_tag.bash:124`, pinned by `tests/test_assert_release_tag.py:121
test_version_mismatch_is_refused`). Nobody noticed, because the assertion lived in prose
inside 170 KB rather than in a check. *This is out of scope for this proposal and should
be filed separately.*

### 2.5 What exists ONLY in `AGENTS.md` — the relocation list

Measure A, hand-corrected, over `### Utilities`. These are the entries with **no**
`docs/REFERENCE.md` section, and they are the content that must be **relocated, not
deleted**. Total **15,860 characters**.

| Subject | Chars | Measure-B recovery from its own source | Destination |
|---|---:|---:|---|
| `util/wait_for_checks.py` | 3,632 | 86% | **new** `docs/REFERENCE.md` section |
| `util/release_train/ceremony.py` | 2,780 | 90% | **new** `docs/REFERENCE.md` section (the operator runbook covers the ceremony, not the module) |
| `util/open_signed_pr.py` | 1,527 | 100% | **new** `docs/REFERENCE.md` section |
| `util/assert_release_tag.bash` | 1,430 | 60% | **new** `docs/REFERENCE.md` section — lowest recovery in the set, and the entry with a factual error (§2.4 #1); this one needs a human write, not a copy |
| `util/experiments/run_suite.py` | 1,048 | 79% | **new** `docs/REFERENCE.md` section under Experiment Stack Utilities |
| `util/release_train/notes_render.py` | 1,026 | 76% | **new** `docs/REFERENCE.md` section |
| subtotal — six new sections | **11,443** | | |
| `util/requirements_drift_check.py` | 512 | 83% | module docstring |
| `util/scaffold_template.py` | 501 | 100% | module docstring |
| `util/template_data_resolver.py` | 494 | 100% | module docstring |
| `util/template_select_preview.py` | 480 | 100% | module docstring |
| `util/generated_prompt_index.py` | 465 | 100% | module docstring |
| `util/agent_suite_summary.py` | 385 | 100% | module docstring |
| `util/get_cascor_*.bash` | 325 | 50% | `docs/REFERENCE.md` § Environment Variables (the `CASCOR_HOST` vs `JUNIPER_CASCOR_*` trap is resident — §5) |
| sequence-safety screen flag summary | 447 | n/a | `docs/REFERENCE.md` § Fleet Triage and Sequence Safety (already exists; fold in) |
| `util/worktree_cleanup.bash` | 802 | 100% | `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` § Git Worktrees (already covers it) |
| `util/env_floor_drift_check.py` residue | 466 | 94% | existing REFERENCE section |
| subtotal — docstrings / existing sections | **4,417** | | |

**The relocation work is 11,443 characters of new `docs/REFERENCE.md` prose.** For scale,
`docs/REFERENCE.md` grew 6,064 bytes/day through August — this is under two days of its
normal growth.

### 2.6 The destination already exists and is already curated

[`docs/DOCUMENTATION_OVERVIEW.md:21–61`](../docs/DOCUMENTATION_OVERVIEW.md) is a **35-row,
task-indexed "I Want To" table** pointing at exactly the `docs/REFERENCE.md` anchors that
duplicate `AGENTS.md`'s big sections — *Host Orchestration Utilities*, *Pytest Orphan
Reaper*, *Environment Floor Drift Check*, *Agent Suite Doctor*, *Fleet Triage and Sequence
Safety*, *Experiment Stack*, *Flood-Remediation CI Gates*, *Post-Merge Main Verification*,
*Meta-Package Publish Pipeline*, *juniper-service-core*, and more.

The navigational core this proposal builds is therefore **not greenfield**. It is a ~14-row
condensation of a 35-row index that is already written, already maintained (last touched
2026-08-14), already link-validated, and simply **not loaded into context**.

---

## 3. The official EXCLUDE list, applied to the real sections

Mechanism fact base §5 names the official EXCLUDE items. Applied literally:

| EXCLUDE item | Sections it condemns | Chars | % of file |
|---|---|---:|---:|
| *file-by-file descriptions of the codebase* | `### Utilities` (35 per-script entries), `### Tests` (57 per-test entries), `### CI/CD Workflows` (13 per-workflow entries), `### Package and Metadata`, `### Documentation`, `### Scripts and Launchers`, `### Configuration` | 99,290 | 59% |
| *detailed API documentation (link instead)* | `## Shared Service-Core Contracts`, `## Shared Observability Helpers`, `### Dependency extras reference` | 7,057 | 4.2% |
| *information that changes frequently* | `### Dependency extras reference` (5 copies), the "Run all tests" block (3,315 chars, 54-of-88 and drifting), `### Package and Metadata` (already wrong, §2.4 #2) | ≈5,730 | 3.4% |
| *anything Claude can figure out by reading code* | `## Repository Structure` tree, `## Pre-commit Hooks` table, `## CI/CD Pipelines` | 38,655 | 23% |
| *long explanations* | the 156 nested sub-bullets — 44,350 chars, 26% of the file (baseline §4) — which sit almost entirely inside the four rows above | (overlaps) | — |

Deduplicating the overlaps, the EXCLUDE list condemns roughly **150,700 characters, 90% of
the file**. That is not a rhetorical figure: §12 removes 152,018 and the two lists agree to
within 1%.

`/doctor`'s own keep-rule agrees on the *first* three rows and disagrees on the fourth —
see §10.

---

## 4. The target: a ≤200-line `AGENTS.md`, section by section

### 4.1 Outline

```text
  1        # CLAUDE.md
  2-  8    header block — 6 required fields, ISO date          (pinned: tests/test_agents_md_header_schema.py)
  9- 12    --- + one-line purpose
 13- 16    ## What This Is                          3 content lines
 17- 40    ## Where To Look                        ~14 table rows      <- the navigational core (new)
 41- 58    ## Build, Test, Publish                 ~14 lines
 59- 86    ## Repository Layout                    18 dir nodes + fence (pinned: tests/test_agents_md_tree_drift.py)
 87-112    ## Standing Rules                       ~22 lines           <- agent behaviour, ungated
113-135    ## Traps With No Gate                   ~20 lines           <- resident lore (new)
136-150    ## Conventions                          ~13 lines
151-161    ## Worktree Procedures                  ~9 lines  (pointer)
162-172    ## Thread Handoff                       ~9 lines  (pointer + repo delta)
173-185    ## Pull Request Conventions             ~11 lines (verb table + pointer)
186-193    ## Ecosystem Context                    ~6 lines  (pointer)
```

**≈193 lines / ≈16,300 characters** — a 90.3% reduction from 168,317. The proposed gate
constants are **200 lines and 18,000 characters**, leaving ~1,700 characters of honest
headroom. At 193 lines that is ~84 characters per line; excluding blanks and headings,
~102 characters per content line, which is consistent with this repo's dense style under
its 512-character line-length convention. If the drafted core overshoots, the overflow
belongs in `docs/REFERENCE.md`, not in a raised ceiling.

### 4.2 `## Where To Look` — the navigational core

A ~14-row table, condensed from `docs/DOCUMENTATION_OVERVIEW.md:21–61`, indexed by **task**
rather than by artifact:

| Working on… | Read first |
|---|---|
| any `util/` script | `docs/REFERENCE.md` — operator contract for every shipped utility |
| host stack up / down | REFERENCE § Host Orchestration Utilities |
| crashed pytest / orphan processes | REFERENCE § Pytest Orphan Reaper |
| editable installs, env / floor drift | REFERENCE § Editable Install Drift Check, § Environment Floor Drift Check |
| experiments (`experiment_stack`, drivers, suites) | REFERENCE § Experiment Stack Utilities + the CLI experimentation plan |
| fleet PR triage, sequence safety | REFERENCE § Fleet Triage and Sequence Safety |
| CI, main-verify, flood gates | REFERENCE § Flood-Remediation CI Gates, § Post-Merge Main Verification |
| publishing any package | the PyPI publish procedure note; REFERENCE § Meta-Package Publish Pipeline / § Independent Sibling Package Publish Pipelines |
| the release train | the release-train operator runbook |
| `juniper-service-core` / `juniper-observability` | REFERENCE § juniper-service-core / § juniper-observability |
| what the test suite runs and why | `.github/workflows/ci.yml` — 87 named suites, each with a rationale comment |
| the custom-agent suite | `python util/agent_suite_summary.py`; `util/agent_suite_doctor.py` for health |
| anything else | `docs/DOCUMENTATION_OVERVIEW.md` — the 35-row "I Want To" index |

Three properties are deliberate: rows are **task-shaped** ("crashed pytest" not
"`reap_pytest_orphans.bash`"), because an agent knows its task before it knows the
artifact; every target is **one hop** and link-validated; and the last row is a
**catch-all**, so an unlisted subject still has a defined next move.

### 4.3 `## Build, Test, Publish`

Replaces `## Build & Package Commands` (4,617) + `## Publishing` (3,641). Keeps: the four
build/validate commands; `pip install -e ".[extra]"` with a pointer to
`docs/REFERENCE.md` § Extras Reference for the matrix; **one** test line
(`python3 -m unittest -v tests/<file>.py`) plus *"the authoritative suite list is
`.github/workflows/ci.yml`"*; `pre-commit run --all-files`; and the release convention as
a single mandatory sentence with its procedure pointer. Removes the 54-file run block
(3,315 chars, already wrong) and the per-package publishing history.

### 4.4 `## Repository Layout`

The 197-line tree becomes 18 top-level directory nodes plus the handful of root files an
agent must know (`pyproject.toml`, `AGENTS.md`, `CHANGELOG.md`, `claudey`). This is the
**minimum that satisfies the existing gate**: `tests/test_agents_md_tree_drift.py:39–65`
requires only that each tracked, non-hidden top-level directory appears as a
`├── name/` node inside the fenced block containing `└── util/` or `├── AGENTS.md`.
`git ls-tree -d --name-only HEAD` yields exactly 18 such directories.

### 4.5 `## Standing Rules` and `## Traps With No Gate`

The two resident sections, governed by §5. `## Standing Rules` holds the ungated
agent-behaviour rules that already exist in the file (script placement, worktrees, handoff,
notes naming, PR conventions summary). `## Traps With No Gate` holds one-line hazards, each
annotated with *why it is resident* — see §5.3 for the list, including four that do **not
exist in the file today** and which the prune therefore *adds*.

---

## 5. The residency decision rule

This is the load-bearing judgement of the whole proposal, so it is a rule, not a taste.

### 5.1 The rule

A line stays resident in `AGENTS.md` **iff all three hold**:

- **Q1 — Audience.** It constrains what *the agent* does, not what *a component* does.
  A sentence whose subject is a function, a flag, or a workflow job is a component
  contract and belongs with the component.
- **Q2 — Enforcement.** It is **not** already enforced by code plus a check that fails
  loudly. If a gate enforces it, *the gate is the memory*; the prose is a description of
  the gate and costs tokens on every session to restate what CI will say for free.
- **Q3 — Blast radius.** Violating it is irreversible or expensive — a destroyed
  campaign, a permanently unmergeable PR, a lost script, a wrong version on PyPI — **or**
  silently wrong, which counts as irreversible because the agent never learns it erred.

**Tie-breaker (the no-second-chance test).** If the agent would only discover the rule
*after* the damage, it stays resident. If the failure is loud and immediate — CI red,
`exit 2`, a refused command — the gate is the better memory.

### 5.2 The rule applied to the file's best-known lore

| Lore | Q1 | Q2 | Q3 | Verdict |
|---|---|---|---|---|
| Reaper live-experiment protection, checked **before** the orphan predicate (`AGENTS.md:408–412`) | component | **enforced** — `util/reap_pytest_orphans.bash:91,102,107–110,194`; pinned by `tests/test_reap_pytest_orphans.py:323 TestLiveExperimentProtection` | irreversible | **RELOCATE** |
| `tr -d -- '-_'` needs the `--`, or both sides normalise to empty and the mismatch check passes vacuously (`AGENTS.md:483`) | component | **enforced** — `util/assert_release_tag.bash:124`; pinned by `tests/test_assert_release_tag.py:121` (**but see §2.4 #6 — the pin does not run in CI**) | irreversible | **RELOCATE**, *conditional on wiring the test into CI* |
| CR-024 body limit, auth-before-rate-limit, 429 header passthrough (`AGENTS.md:168–170`) | component | enforced in `juniper-service-core` + its tests | expensive | **RELOCATE** — `docs/REFERENCE.md` § juniper-service-core is already the declared operator surface (`AGENTS.md:178`) |
| `max_epochs` without `output_epochs` runs 10,000 per later pass on the service (`AGENTS.md:576`) | component config | **warned, not enforced** — `load_config` emits a `validation_warning` and never raises; pinned by `tests/test_run_experiment.py:528` | expensive (a burned GPU campaign) | **SPLIT** — mechanism relocates; a one-line trap stays resident. This is the rule's genuine grey zone: a non-fatal warning is not a gate. |
| `/tmp/` is never the home of a script source file (`AGENTS.md:904–918`) | **agent** | **ungated** — no hook in `.pre-commit-config.yaml`, no test | irreversible (`phase4_consolidate.py` is gone) | **RESIDENT** |
| Never `grep` `id_assignments.yaml` for content — briefs are truncated (`AGENTS.md:940`) | **agent** | **ungated** | silently wrong | **RESIDENT** |
| Worktree isolation for all feature/bugfix work | **agent** | ungated | expensive | **RESIDENT** — one copy (§11.2) |
| Handoff instead of compaction at 95–99% | **agent** | ungated | expensive | **RESIDENT** — one copy |

### 5.3 The resident hazard list

Fourteen one-line entries, ~2,300 characters. Marked **[NEW]** where the rule is *not
currently stated* in `AGENTS.md` — the prune is not purely subtractive at the level of
rules.

1. `/tmp/` is never the home of a script source file → `util/` or `util/ad-hoc/`.
2. Never `grep` `notes/requirements/id_assignments.yaml` for content — briefs are truncated.
3. **[NEW]** Never put `[skip ci]` in a commit that can become a PR head — no required
   context ever reports on it, the aggregate rollup can read SUCCESS, and the PR is
   permanently unmergeable. *Today the file narrates this incident three times
   (`AGENTS.md:496`, `:735`, `:826`) and states the rule zero times.*
4. Never hand-roll a "wait for CI" loop — use `util/wait_for_checks.py`; a rollup that
   looks complete usually is not.
5. Cross-repo / headless PRs must carry GitHub-signed commits — use
   `util/open_signed_pr.py`; one unsigned commit anywhere blocks the merge and squash does
   not rescue it.
6. Publish by cutting a GitHub Release, never a bare `git push <tag>`.
7. Feature and bugfix work goes in a worktree under `Juniper/worktrees/`, never inside the
   repo directory.
8. Hand off at 95–99% of the compaction threshold; never let compaction run.
9. An experiment config that sets `max_epochs` must also set `output_epochs`.
10. `CASCOR_HOST` / `CASCOR_PORT` (the `util/get_cascor_*.bash` helpers, `AGENTS.md:595`)
    are **not** `JUNIPER_CASCOR_*` (plant/chop).
11. **[NEW]** A large markdown deletion trips `juniper-docs-additions-check` — token-diff
    before waiving; restore, do not waive. *Grounded in `40230d2` "restore three
    owner-decision blocks dropped by 76e4513 (#1165)".*
12. `notes/` filenames follow `JUNIPER_<DATE>_JUNIPER-<REPO>_<PHRASE>.md`.
13. **[NEW, owner decision]** Deployment / PyPI environment approvals are the owner's;
    never approve one. *Asserted from operating practice, not from a repo artifact — the
    owner should confirm or strike it.*
14. **[NEW, owner decision]** Merge only on the owner's explicit per-PR approval. *Same
    caveat as 13.*

Entries 1–2 and 6–10, 12 exist in the file today; 3, 11, 13, 14 are additions; 4 and 5
exist only as component descriptions and are promoted to rules.

---

## 6. Load-bearing design elements — strengths, weaknesses, risks, guardrails

### E1 — Delete what `docs/REFERENCE.md` already says (68,409 chars)

**Strengths.** The largest single win, and the cheapest: zero new prose, because the
destination text already exists and is measurably richer (§2.2a). Removes 41% of the file
by itself. Reversible in one `git revert`. Requires no mechanism, no setting, and no
Claude Code version dependency, so it cannot be invalidated by a client release.

**Weaknesses.** (i) It buys nothing for an agent that *never opens* `docs/REFERENCE.md` —
the whole of §7. (ii) `docs/REFERENCE.md` is itself on a super-linear curve
(16,008 → 162,231 bytes since 2026-06-01, 6,064 bytes/day in August); this proposal moves
knowledge to a place where it costs tokens only on demand, and does nothing about its
navigability at 500 KB. (iii) Measure A is subject-level: a 71% coverage figure does not
prove that *every sentence* is downstream, only that a section on the subject exists.

**Risks.** *Concrete scenario:* a session prunes the `predict_merge.py` entry on the
strength of `docs/REFERENCE.md:799 § Fleet Triage and Sequence Safety`, but that section
does not carry the nested detail at `AGENTS.md:470` that the gate battery runs over
`changed_existing` so a **pure-deletion PR can be gate-clean and still `DAMAGED-FIX-FIRST`**.
Six weeks later a fleet triage misreads a verdict. The loss is silent and undated.

**Guardrails.**
- **G1 — relocation-completeness gate** (new, `tests/test_agents_md_relocation.py`,
  modelled on `tests/test_ci_tools_drift.py`): for the prune PR, every backticked token
  removed from `AGENTS.md` must resolve somewhere in the repo at HEAD. My Measure-B run is
  the prototype (96% before any relocation; the target is 100% with a small, reviewed
  allowlist for tokenizer artifacts).
- **G2 — the existing sequence-safety screen.** `juniper-docs-additions-check`
  (`.github/workflows/ci.yml:877`, `.github/workflows/main-verify.yml:196`) FAILs on a
  deleted heading or a ≥5-line deletion run in `AGENTS.md`. It will fire on every phase of
  this migration — by design. It is the repo's existing content-loss alarm and the migration
  must satisfy it with evidence, not silence it (§13, §14).
- **G3 — a token diff in every prune PR body**, per the `#1165` lesson recorded in commit
  `40230d2`: *restore, do not waive*.

### E2 — Delete what the code already says (60,213 chars: tests 34,579 + layout 18,669 + config/misc 6,965)

**Strengths.** The `### Tests` case is unusually strong: the authoritative list is
`.github/workflows/ci.yml`, which names **87 of 88** files, each beside a comment giving
its rationale (`ci.yml:223`, `:233`, `:262`, `:526–531`, `:605–632`) — and unlike the prose
copy it *cannot* silently drift, because a renamed test breaks the build. The layout case
is exactly what `/doctor` is built to cut (§10). This element also removes the file's
largest *staleness surface*: four of the six defects in §2.4 live here.

**Weaknesses.** (i) `ci.yml` is an ordering, not an explanation: it says what runs, not
what a suite *means*. About a dozen entries carry design rationale beyond the inline
comment — those must land in the test module's own docstring, which is more work than a
delete. (ii) A workflow file is a worse read than prose for a human. (iii) Recovering the
layout requires tool calls (`ls`, `git ls-tree`) that cost turns.

**Risks.** *Concrete scenario:* an agent asked "which test gates the publish env tag
policy?" no longer finds `tests/test_publish_env_policy_drift.py` described in memory,
greps `tests/` for "tag policy", finds nothing (the phrase is "deployment ref policy"),
and concludes no gate exists — then writes a second one. Duplicate gates are how
`test_agent_suite_path_drift.py` and `test_agents_md_tree_drift.py` came to overlap.

**Guardrails.**
- **G4 — docstring-first convention, enforced where the repo already enforces it.** The
  repo's best test modules already lead with a purpose docstring —
  `tests/test_agents_md_tree_drift.py:1–18` is the model. Add to the drift-gate family a
  check that every `tests/*.py` has a non-trivial module docstring; that is a small,
  portable lint of exactly the kind this repo writes.
- **G5 — the `## Where To Look` row** "what the test suite runs and why → `ci.yml`" makes
  the redirect explicit rather than leaving a hole.
- **G6 — `tests/test_agents_md_tree_drift.py` is retained unchanged**; the pruned tree
  still satisfies it, so the layout can never lose a directory.

### E3 — Relocate the only-in-`AGENTS.md` content (22,171 chars)

**Strengths.** This is the element that makes the prune a *move* rather than a *deletion*,
and it is bounded and enumerated (§2.5): 11,443 characters into six new
`docs/REFERENCE.md` sections, 4,417 into module docstrings, 6,311 into `notes/` and the PR
template. Writing 11,443 characters into `docs/REFERENCE.md` is under two days of its
observed growth. Every destination file already exists.

**Weaknesses.** (i) It is the only labour-intensive element — the six sections need a
human or a careful agent, not a copy-paste, and `util/assert_release_tag.bash`'s entry is
**factually wrong today** (§2.4 #1), so relocation there means *re-deriving from source*.
(ii) Measure B's 60–100% recovery figures describe nouns, not reasoning: the `wait_for_checks`
entry's insight that `stalled` means "further polling cannot change the answer" is
paraphrase, and paraphrase does not show up in a token match.

**Risks.** *Concrete scenario:* the migration ships the deletions in Phase 2 and the six
`docs/REFERENCE.md` sections slip to Phase 3, which is deprioritised. For a fortnight the
only record of the `open_signed_pr.py` dup-guard and `expectedHeadOid` pinning is the
module docstring — adequate — but the `assert_release_tag.bash` contract exists **nowhere
correct**, since the `AGENTS.md` copy was deleted and it was wrong anyway.

**Guardrails.**
- **G7 — ordering constraint, not a wish: relocation lands BEFORE the matching deletion.**
  Each phase in §13 is written so the destination text is merged first. This is the single
  most important sequencing rule in the plan.
- **G8 — G1 (relocation-completeness) enforces it mechanically**: if the destination text
  is not in the tree, the tokens do not resolve and the prune PR fails.
- **G9 — `juniper-check-doc-links`** (pre-commit hook + the `docs` CI lane) proves every
  new pointer resolves; a pointer to a section that was never written is a hard failure,
  not a silent dead end.

### E4 — The ≤200-line navigational core

**Strengths.** Meets the official target exactly (mechanism fact base §5). Reduces
always-on memory from ~51k tokens to roughly ~9k (16,300 + 11,016 + 3,349 ≈ 30,700
characters), taking pre-prompt context consumption from ~25% of a 200k window to ~4%. The
structure is already proven in this repo by `docs/DOCUMENTATION_OVERVIEW.md:21–61` (§2.6).
And it directly serves the documented adherence claim — *"Bloated CLAUDE.md files cause
Claude to ignore your actual instructions"* — by putting the 14 hazards in a 20-line
section instead of burying them among 117 mandatory-language lines of which **105 (90%) are
component contracts, not instructions** (my count; the baseline's broader pattern gives 164).

**Weaknesses.** (i) The adherence benefit is a **documentation assertion, not a measured
one** — mechanism fact base §8 item 6 is explicit that no published Anthropic benchmark
measures adherence against `CLAUDE.md` size. The token saving is certain; the attention
benefit is asserted. (ii) 200 lines is a guideline with no mechanical meaning; the only
mechanical thresholds are the 40,000-character warning floor and the 4 MiB skip. (iii)
84 characters/line average is tight for this repo's style, and the core will feel cramped.

**Risks.** *Concrete scenario:* the core is drafted to 199 lines by writing denser prose
rather than by relocating, producing a file that is short, unreadable, and just as
unfollowable — the failure mode the official guidance warns about, reached from the other
direction.

**Guardrails.**
- **G10 — dual ceilings, lines *and* characters** (200 / 18,000). A characters-only gate
  invites long lines; a lines-only gate invites 400-character lines. This repo's 512-char
  line-length convention makes the second failure easy.
- **G11 — the `## Where To Look` catch-all row** guarantees any subject has a next move
  even when the core has no row for it.

### E5 — The residency decision rule (§5)

**Strengths.** Converts the hardest judgement in the proposal into three answerable
questions, each checkable against the repo. Every verdict in §5.2 cites the enforcing code
and its pin, so a reviewer can audit the rule rather than trust it. It also *surfaces* four
rules that do not exist today (§5.3), so the prune improves the rule set while shrinking
the file.

**Weaknesses.** (i) Q2 assumes a gate that fails loudly — §2.4 #6 proves that assumption
can be false while the file asserts otherwise. The rule is only as good as the claim
"a gate enforces this", and this repo has at least one gate that does not run. (ii) Q3's
"silently wrong counts as irreversible" is broad enough to readmit a great deal if applied
loosely. (iii) The `max_epochs` row shows a real grey zone: a non-fatal warning is neither
a gate nor nothing.

**Risks.** *Concrete scenario:* a session relocates a contract under Q2, citing a test
that exists but is not wired into any workflow. The contract is now documentation-only and
the protection is imaginary — precisely the `assert_release_tag` shape.

**Guardrails.**
- **G12 — Q2 must be answered with a *wired* gate.** A relocation on Q2 grounds must name
  the workflow line that runs the check, not just the test file. `tests/test_workflow_script_paths.py`
  already lints that workflow-referenced script paths exist; the mirror check — that every
  `tests/*.py` is referenced by a workflow — is a small addition that would have caught
  §2.4 #6 and should ship with Phase 0.
- **G13 — the residency rule lives in the core itself**, so a future session applying it
  reads it. A decision rule filed only in `notes/` is not a decision rule.

### E6 — The size-and-shape gate (the rate control)

**Strengths.** The only element that survives contact with §9's arithmetic. Two new lints
in the existing `tests/test_agents_md_*.py` family, wired into `.github/workflows/ci.yml`
beside `:633–636` where `test_agents_md_tree_drift.py` already runs:

- `tests/test_agents_md_size_budget.py` — hard ceilings, 200 lines / 18,000 characters.
- `tests/test_agents_md_shape.py` — forbids the accretion signature the baseline
  identified (§4): no list item nested two or more levels deep, no `#NNN` issue citations,
  no `Operator surface:` trailers (the pointer now lives once, in `## Where To Look`).

The shape gate is the important one: it attacks the *mechanism* (156 nested sub-bullets,
44,350 chars) rather than the symptom. Both are portable by construction, following
`tests/test_agents_md_header_schema.py`'s self-locating idiom, so the fleet rollout is a
file copy.

**Weaknesses.** (i) A hard ceiling **cannot make the destination attractive**; it can only
make `AGENTS.md` unavailable. If writing to `docs/REFERENCE.md` is more friction than
writing to `AGENTS.md`, the ceiling produces terser `AGENTS.md` prose, not relocation.
That is a human-factors bet with no mechanism behind it, and it is the weakest link in this
proposal. (ii) The gate is a test in the same repo; the PR that raises the constant passes
its own gate. (iii) A shape gate is a proxy — a session can write 400-character
non-nested bullets.

**Risks.** *Concrete scenario:* three months on, a session hits the ceiling mid-task, sees
`AGENTS_MD_MAX_CHARS = 18000` in a test it can edit, bumps it to 24,000 with the commit
message "budget was too tight", and CI goes green. The ratchet has become a formality. This
is not hypothetical for this file: **four gates already protect it and every one is
satisfied by an edit that appends 500 lines** (baseline §6).

**Guardrails.**
- **G14 — the constant carries a required-justification comment**, mirroring
  `EXPECTED_EXTRAS` in `tests/test_pyproject_extras.py:141`, and `.github/CODEOWNERS`
  (@pcalnon, all files) puts every raise in front of the owner.
- **G15 — a raise must cite the relocation it could not make.** Encode it: the gate reads
  a `# BUDGET-RAISE:` justification line and fails if it is absent or unchanged from the
  previous raise. Crude, but it converts a silent bump into a visible admission.
- **G16 — aggregate-aware budget.** The gate must count `AGENTS.md` **plus** the parent
  `Juniper/CLAUDE.md`, or the ceiling is trivially evaded by pushing bytes up the tree —
  which is worse, because ancestors are eager for all nine repos. Claude Code itself has
  no aggregate budget (mechanism fact base §8b), so we must model it.
- **G17 — redirect the convention where this repo already writes conventions**: a line in
  `.github/pull_request_template.md`, and a line in each `.claude/agents/*.md` prompt
  (`planner`, `auditor`, `task-executor`) saying post-mortem detail goes to
  `docs/REFERENCE.md`. Those files are already gated by `tests/test_agents_frontmatter.py`,
  so the convention has both a home and a check.

### E7 — `/doctor` as the Phase-1 accelerant (see §10)

### E8 — HTML-comment tombstones and `claudeMdExcludes` (see §11)

---

## 7. The central objection: a pointer that is not followed is information loss with extra steps

Today an agent knows the reaper's live-experiment protection rule without asking. Under
this design it must decide to read `docs/REFERENCE.md`. This is the strongest argument
against the proposal and it deserves better than reassurance.

### 7.1 What I can and cannot measure

I **cannot** measure the follow rate. There is no instrumentation for it, and the
mechanism fact base is explicit (§8 item 6) that no published benchmark measures
adherence as a function of memory-file size. Any number I offered would be invented.

### 7.2 Evidence that pointers work here

- **The repo already runs on them.** `AGENTS.md` contains **33** `Operator surface` /
  `Operator table` / `Operator detail` trailers and **59** lines referencing a runbook, the
  cheatsheet, or a `notes/` document. The deepest operator detail *already* lives one hop
  away and has done for months.
- **The index→corpus pattern is running in this project at 53:1.** Mechanism fact base
  §8b: 154 auto-memory topic files, 1,082,901 bytes on disk, 20,388 bytes loaded. The
  architecture this proposal reaches for is not speculative — it is operating next to the
  problem file.
- **The destination is alive.** `docs/REFERENCE.md`: 85 commits since 2026-06-01, one
  today, 6,064 bytes/day of growth in August.

### 7.3 Evidence against — and it is the more honest half

- **Those 33 pointers coexist with a full summary.** In every case the author wrote the
  pointer *and* restated the content. That is a revealed preference: the authors of this
  file did not trust the pointer. §2.2a is the clean example — `AGENTS.md:413` points at
  `docs/REFERENCE.md § Pytest Orphan Reaper` and duplicates all seven of its claims first.
- **Sessions write where they read.** Since 2026-06-01: `AGENTS.md` 285 commits,
  `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` 158, `docs/REFERENCE.md` 85. The
  always-loaded file gets 3.4× the traffic of the pointed-at one.
- **The auto-memory analogy is imperfect.** Auto-memory has purpose-built machinery and
  prompting for index→topic retrieval. `docs/REFERENCE.md` has a markdown link and hope.

### 7.4 The reframing that makes the risk tractable

The realistic failure is **not** "the agent refuses to read". It is **"the agent does not
know a hazard exists, so it never forms the intent to look"**. A pointer is followed when
the agent has already decided to work on that subject; it is not followed when the agent
is unaware there is anything to know.

That distinction is the whole design:

> **Pointers for subjects. Resident text for hazards.**

An agent about to run `util/reap_pytest_orphans.bash` will find the reaper row in
`## Where To Look` — it *knows* it is reaping. An agent that would blithely author a
script in `/tmp/` does not know the hazard exists, which is exactly why rule 1 of §5.3
stays resident. §5's three questions are the operationalisation of this sentence.

### 7.5 The residual exposure, named

After the residency rule, the exposure is: **component hazards, for an agent that edits
the component without reading it.** That is a narrow class, because editing a file
normally means reading it, and because the hazards in that class are pinned by tests that
fail loudly (§5.2). It is not zero: a `pre-commit` autofix, a mechanical rename, or an
agent editing by `sed` can all touch a file without reading its docstring.

### 7.6 What actually makes a pointer reliable

In descending order of reliability, with what this repo can supply:

1. **A gate.** The only mechanism with a guarantee. If the contract matters, the test that
   pins it must run in CI (G12) — then an agent that breaks it is *told*, and prose is
   irrelevant. This repo already prefers this: 88 test files, four of them dedicated to
   `AGENTS.md` alone.
2. **A path-scoped `.claude/rules/` file** (mechanism fact base §4b) — fires when Claude
   *reads a matching file*, not on agent judgement. Mechanically reliable and lazy.
   **Naming it honestly: adopting this is borrowing a different proposal's lever.** This
   proposal does not require it; §13 Phase 5 offers it as an optional de-risking layer for
   the handful of component hazards that survive §7.5, and it should be adopted only if
   the §14 soak shows the pointer failing.
3. **Task-shaped rows at one hop**, link-validated — what §4.2 supplies.
4. **A prose pointer to a 162 KB document with no anchor** — the weakest form, and the one
   this proposal deliberately does not use.

### 7.7 The rollback condition

If the §14 soak shows agents failing to reach relocated content on component-touching
tasks, the correct response is **not** to re-inline. It is, in order: (a) add the missing
`## Where To Look` row; (b) wire the gate (G12); (c) add a path-scoped rule. Re-inlining
returns the file to the state that produced §2.4's six defects.

---

## 8. Regression risk: what stops a future session re-adding what was pruned

The pruned content will look **missing** to the next agent that needs it, and this repo
merges ~1.3 PRs/day into this file. Four defences, weakest to strongest:

1. **Tombstones (weakest, cheapest).** A block-level HTML comment where a section was,
   naming the destination — `<!-- moved: per-utility contracts -> docs/REFERENCE.md -->`.
   Mechanism fact base §4d records these as stripped before injection, so they cost the
   agent nothing while giving the *editor* an in-file breadcrumb. Weakness: an agent that
   never opens `AGENTS.md` (it is injected, not read) never sees them; they help humans and
   file-editing sessions, not readers. **§11.1 states what breaks if the strip fact is wrong.**
2. **`## Where To Look` (structural).** A gap that has a row is not a gap. This is why the
   catch-all row matters.
3. **Convention redirect (G17).** PR template + the three `.claude/agents/*.md` prompts.
   Cheap, advisory, and — per mechanism fact base §6 — *not* enforcement.
4. **The shape and size gates (only real defence).** A re-add fails CI. The shape gate is
   the specific answer to re-accretion: the observed mechanism is nested sub-bullets under
   existing entries (156 of them, 26% of the file), and a gate that forbids depth-2 nesting
   blocks that mechanism directly, regardless of the total.

**Honest limit.** None of this stops the owner, and none stops a PR that edits the gate in
the same change. `.github/CODEOWNERS` puts every such PR in front of @pcalnon, which is a
review control, not a mechanism. If the owner wants a mechanism, it is a `PreToolUse` hook
(mechanism fact base §6) — and note that this repo currently has **no active
`.claude/settings.json`** at all (mechanism fact base §8b), so there is nowhere for a hook
to be configured until one is created (§11.2).

---

## 9. Concurrency and the rate — stated plainly

### 9.1 The arithmetic

`AGENTS.md` size at month boundaries, measured directly from git in this worktree:

| Date | Bytes | Δ | Rate |
|---|---:|---:|---:|
| 2026-06-01 | 38,248 | | |
| 2026-07-01 | 64,965 | +26,717 | 891 B/day |
| 2026-08-01 | 120,685 | +55,720 | 1,797 B/day |
| 2026-08-18 | 170,137 | +49,452 | **2,909 B/day** |

Derived from the baseline document's PR-merge counts instead: July +55,796 over 34 merges
= 1,641 B/merge; August +50,430 over 35 merges = 1,441 B/merge; at ~1.3 merges/day that is
**≈2,000 B/day**. The two methods bracket each other; take 2,000 as the conservative
planning rate and 2,909 as the pessimistic one.

### 9.2 What that does to a one-time prune

From a 16,300-character core:

| Milestone | at 2,000 B/day | at 2,909 B/day |
|---|---:|---:|
| back over the 40,000-char warning floor | **12 days** | **8 days** |
| back to 100,000 chars | 42 days | 29 days |
| back to today's 170,137 | **77 days (2.5 months)** | **53 days (1.8 months)** |

**A prune with no rate control is undone in roughly two months.** This confirms the
premise in the commissioning brief and it is the honest headline: measured against the
level, this proposal is transformative; measured against the rate, the prune alone does
nothing at all.

### 9.3 What in this proposal changes the rate

- **A hard ceiling converts an add into a trade.** Above 18,000 characters, adding requires
  deleting or relocating in the same PR. This is a genuine rate control, but it acts by
  *refusal*, not by making the alternative easy.
- **The shape gate blocks the observed mechanism.** Growth here is not new entries; it is
  nested post-mortem detail appended under existing ones (baseline §4). Forbidding depth-2
  nesting removes the path of least resistance that produced 44,350 characters.
- **The destination is already the busier file.** `docs/REFERENCE.md` grew 6,064 B/day in
  August against `AGENTS.md`'s 2,909. Sessions already know how to write there; the
  redirect is not asking for a new habit, only for a different default.

### 9.4 What does not

**Nothing in this proposal reduces the production of knowledge**, and nothing makes writing
to `docs/REFERENCE.md` easier than writing to `AGENTS.md`. The rate of *bytes produced*
stays ~2,000–2,900/day; the proposal redirects them to a lazily-loaded file. If the
redirect fails in practice, the ceiling will simply be raised (E6 risk), and this proposal
degrades to a one-time 90% cut with a two-month half-life. **That is the honest downside
case, and the §14 soak is designed to detect it early.**

---

## 10. The role of `/doctor`

Mechanism fact base §4d and §8b establish that our version (**2.1.235**, requirement
v2.1.206+) ships a purpose-built `CLAUDE.md` trim proposer which *"cuts content Claude can
derive from the codebase, such as directory layouts, dependency lists, and architecture
overviews, and keeps pitfalls, rationale, and conventions that differ from tool defaults"*,
and that its advisory *"estimates savings at ~30%"*.

### 10.1 How to use it

**As the Phase-1 accelerant, and only there.** Its stated cut-list is a near-exact match
for this file's three cheapest wins:

| `/doctor` cuts | Our section | Chars |
|---|---|---:|
| directory layouts | `## Repository Structure` | 20,469 |
| dependency lists | `### Dependency extras reference` + `### Package and Metadata` | 2,415 |
| architecture overviews | `## What This Is`, `## Ecosystem Context`, parts of `## CI/CD Pipelines` | ≈3,000 |

Run it, take its proposal as a **starting diff**, review it by hand, and ship it as Phase 1.
It should get to roughly 145,000 characters without an argument.

### 10.2 Why it is not sufficient — three specific reasons

1. **Its advertised yield is ~30%; the target requires ~90%.** 168,317 × 0.70 ≈ 118,000
   characters — still 2.9× the warning floor and ~29k tokens of always-on context. Measured
   against the ~152,000 characters that must go, `/doctor` removes about a third.
2. **Its keep-rule and our prune-rule disagree on the single largest category.** `/doctor`
   *keeps* "pitfalls, rationale". The 156 nested sub-bullets — 44,350 characters, 26% of
   the file — read as pitfalls by any reasonable classifier: a failure class, an issue
   number, the gate that now pins it. `/doctor` will preserve exactly the material this
   proposal most needs to relocate. §5's rule exists precisely because "is it a pitfall?" is
   the *wrong* question; the right one is "is it an *agent* pitfall that no gate catches?"
3. **It cannot know this repository's enforcement map.** Q2 of the residency rule requires
   knowing that `tests/test_reap_pytest_orphans.py:323` pins the reaper's protection and is
   wired into `ci.yml` — and that `tests/test_assert_release_tag.py` is **not**. No generic
   trim proposer has that; a proposal that outsourced the judgement to it would relocate
   the one contract whose pin does not run.

Operationally: `/doctor` is TUI-only (mechanism fact base §8b — no CLI subcommand reports
context accounting), so it cannot be a CI gate, and its output must be reviewed as a diff
like any other change.

---

## 11. HTML comments and `claudeMdExcludes`

### 11.1 Block-level HTML comments

Mechanism fact base §4d: *"Block-level HTML comments are stripped before injection —
maintainer notes cost nothing."* Two uses:

1. **Tombstones** (§8 defence 1) — one comment per pruned section naming its destination.
2. **The budget-raise justification** required by G15.

**If this fact goes the other way** — i.e. the strip is verified for the `MEMORY.md`
measurement path (fact base §2) but *not* for the project-scope `CLAUDE.md` injection path,
which §8b does not separately re-confirm — then tombstones cost their own bytes and become
visible noise in every session. Mitigation, applied unconditionally: **the size gate counts
characters including comments.** The design relies on the strip for *value*, never for
*budget*, so a wrong fact costs at most ~600 characters of tombstones and no gate breaks.

### 11.2 `claudeMdExcludes` for the additive parent

The parent `Juniper/CLAUDE.md` is **220 lines / 11,016 bytes** and is fully additive —
mechanism fact base §7: Claude Code concatenates rather than overriding, so the repo file
does not supersede it. Two of its sections are re-stated in `AGENTS.md`:

| Subject | User-global `~/.claude/CLAUDE.md` | Parent `Juniper/CLAUDE.md` | `juniper-ml/AGENTS.md` | Total paid |
|---|---:|---:|---:|---:|
| Thread handoff | 3,342 (`:8–66`) | — | 3,875 (`:1042–1115`) | **7,217** |
| Worktree procedures | — | 2,170 (`:119–171`) | 4,159 (`:950–1041`) | **6,329** |

I diffed the handoff sections line by line: the repo copy restates the global's
Policy / When-to-Trigger / How-to-Execute / Rules structure step for step. Its **only**
unique content is step 5, *"Archive the thread handoff prompt to
`prompts/thread-handoff_automated-prompts/` … `HANDOFF_YYYY-MM-DD_[Session
Description].md`"*. And the global already ends with *"If a project has a thread-handoff
procedure document in `notes/`, follow its project-specific templates"* — the pointer is
already there. So 3,875 characters reduce to one line plus the existing link to
[`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md).

**The `claudeMdExcludes` option.** Mechanism fact base §4d/§8b: it suppresses specific
ancestor files, matches absolute paths via picomatch, and applies to User / Project / Local
types. Excluding the parent would save 11,016 bytes.

**Recommendation: do it, but only after inlining what it carries — and not in Phase 1.**

- **In favour.** It is the documented answer to an over-broad ancestor file; the parent's
  load-bearing facts are already downstream (`docs/REFERENCE.md:130 § Service Ports`,
  `:1843 § Environment Variables`), and the rest of the parent (repo table, dependency
  graph, conda envs) compresses to ~15 lines in `## Ecosystem Context`. Net ≈ −9,800.
- **Against.** (a) The setting must live in a file Claude Code reads. **This repo has no
  active `.claude/settings.json`** — only `settings.local-ORIG_{1..5}.json` and
  `settings.local-WORKING.json`, none of which are read filenames (mechanism fact base
  §8b). Creating one is a prerequisite and has effects beyond this proposal. (b) The
  exclusion is per-project, so the parent keeps loading in the other eight repos —
  fleet-wide consistency degrades, and someone will eventually wonder why juniper-ml
  sessions do not know the port table. (c) `Rzr(r.path)` — the path-exclusion predicate —
  is **explicitly UNVERIFIED** as `claudeMdExcludes` (mechanism fact base §8 item 3). *If
  it is something else, the exclusion silently does nothing.* The guardrail is to verify
  empirically with `/context`'s per-file memory tree (fact base §8b) before relying on the
  saving, and to treat the 11,016 bytes as **unbanked** until then.

The cleaner long-run fix is to prune the parent itself — it is a shared file serving nine
repos and is on the same disease curve — but that is a cross-repo negotiation and does not
belong in this proposal's critical path.

---

## 12. Before / after byte budget

All figures in **characters**. Section sizes verified in this worktree; they reproduce the
baseline document's per-section table exactly.

### 12.1 Section budget

| # | Section (`AGENTS.md` lines) | Now | After | Removed |
|---|---|---:|---:|---:|
| 1 | Header + `## What This Is` (1–19) | 927 | 700 | 227 |
| 2 | `## Build & Package Commands` (20–108) | 4,617 | 900 | 3,717 |
| 3 | `## Publishing` (109–152) | 3,641 | 550 | 3,091 |
| 4 | `## Shared Observability Helpers` (153–163) | 1,495 | 200 | 1,295 |
| 5 | `## Shared Service-Core Contracts` (164–179) | 3,512 | 200 | 3,312 |
| 6 | `## Repository Structure` (180–376) | 20,469 | 1,800 | 18,669 |
| 7 | `## Key Files` (377–752) | 99,304 | 1,400 | 97,904 |
| 8 | `## CI/CD Pipelines` (753–844) | 16,101 | 900 | 15,201 |
| 9 | `## Pre-commit Hooks` (845–866) | 2,085 | 500 | 1,585 |
| 10 | `## Secrets Management (SOPS)` (867–876) | 492 | 300 | 192 |
| 11 | `## Ecosystem Context` + extras (877–892) | 2,315 | 500 | 1,815 |
| 12 | `## Conventions` + Script placement (893–920) | 2,484 | 1,900 | 584 |
| 13 | `## Pull Request Conventions` (921–949) | 2,842 | 800 | 2,042 |
| 14 | `## Worktree Procedures` (950–1041) | 4,159 | 700 | 3,459 |
| 15 | `## Thread Handoff` (1042–1115) | 3,875 | 650 | 3,225 |
| 16 | **NEW** `## Where To Look` | 0 | 2,000 | −2,000 |
| 17 | **NEW** `## Traps With No Gate` | 0 | 2,300 | −2,300 |
| | **TOTAL** | **168,317** | **16,300** | **152,017** |

Arithmetic: rows 1–15 remove 156,318; rows 16–17 add back 4,300; net **152,018**
(±1 rounding). 168,317 − 152,018 = **16,299**.

### 12.2 Decomposition of row 7 (`## Key Files`, 99,304)

| Part | Chars | Fate |
|---|---:|---|
| `### Utilities` — subjects with a `docs/REFERENCE.md` section | 38,650 | delete |
| `### Utilities` — six subjects with none | 11,443 | **relocate → six new `docs/REFERENCE.md` sections** |
| `### Utilities` — nine small subjects with none | 4,417 | **relocate → module docstrings / existing sections** |
| `### Tests` | 34,579 | delete (`ci.yml` names 87 of 88 with rationale; ~12 rationales → test docstrings) |
| `### CI/CD Workflows` | 8,136 | delete (`docs/REFERENCE.md`, 100% after glob correction) |
| `### Package and Metadata` / `### Documentation` / `### Scripts and Launchers` / `### Configuration` | 2,065 | delete (`pyproject.toml`, `docs/DOCUMENTATION_OVERVIEW.md`, `.pre-commit-config.yaml`) |
| `## Key Files` heading | 14 | condense |
| **subtotal** | **99,304** | of which **1,400** is retained as `## Where To Look` pointer rows |

### 12.3 Destination ledger — where every removed character lands

| Destination | Chars | Basis |
|---|---:|---|
| **Deleted** — already in `docs/REFERENCE.md` | **68,409** | 38,650 utilities + 8,136 workflows + 15,201 pipelines + 3,312 service-core + 1,295 observability + 1,815 extras |
| **Deleted** — derivable from repo code / config | **41,544** | 34,579 tests (`ci.yml` + docstrings) + 3,315 test-command block + 2,065 misc + 1,585 pre-commit table |
| **Deleted** — directory layout | **18,669** | tree beyond the 18 gate-required nodes |
| **Deleted** — already in the parent / user-global memory file | **6,684** | 3,459 worktree + 3,225 handoff |
| **RELOCATED** → six new `docs/REFERENCE.md` sections | **11,443** | §2.5 — content that exists only in `AGENTS.md` |
| **RELOCATED** → module docstrings / `--help` / existing sections | **4,417** | §2.5 |
| **RELOCATED** → `notes/`, `.github/pull_request_template.md`, `docs/QUICK_START.md` | **6,311** | 3,091 publishing + 2,042 PR conventions + 584 conventions + 402 install matrix + 192 SOPS |
| **Condensed in place** | **241** | header / purpose |
| *subtotal leaving the three big sections and their neighbours* | *157,718* | |
| *less: retained in `AGENTS.md` as `## Where To Look` rows* | *−1,400* | |
| *less: net new resident sections* | *−4,300* | `## Where To Look` 2,000 + `## Traps With No Gate` 2,300 |
| **NET REMOVED** | **152,018** | |

**Total genuinely new prose to be written: 22,171 characters** (the three RELOCATED rows),
of which 11,443 is `docs/REFERENCE.md` sections — under two days of that file's observed
August growth.

### 12.4 Always-on context, before and after

| File | Now (chars) | After | Note |
|---|---:|---:|---|
| `~/.claude/CLAUDE.md` | 3,349 | 3,349 | untouched |
| `Juniper/CLAUDE.md` (parent) | 11,016 | 11,016 → 0 | only if §11.2's `claudeMdExcludes` is verified; **treat as unbanked** |
| `juniper-ml/AGENTS.md` | 168,317 | 16,300 | |
| **Total** | **182,682** | **30,665** (or **19,649**) | **−83%** (or **−89%**) |

At ~4 chars/token that is ≈45,700 tokens → ≈7,700 (or ≈4,900): from ~23% of a 200k window
before the first prompt to **~4%** (or ~2.5%). `MEMORY.md`'s 20,388 bytes are a separate
subsystem and are excluded here (§16).

---

## 13. Migration path

Each phase is independently shippable and revertible; each names real files. **The
ordering rule is absolute: relocation lands before the matching deletion (G7).**

### Phase 0 — Guardrails first (no `AGENTS.md` change)

1. Add `tests/test_agents_md_size_budget.py` with the ceilings set to **today's values**
   (1,115 lines / 168,317 chars) so it is green on merge, and wire it into
   `.github/workflows/ci.yml` beside `:633–636`.
2. Add `tests/test_agents_md_shape.py`, initially `--advisory`-equivalent (report-only),
   for the same reason.
3. Add `tests/test_agents_md_relocation.py` (G1) with the Measure-B implementation.
4. **File the §2.4 #6 defect** — `tests/test_assert_release_tag.py` runs in no workflow —
   and add the mirror lint (G12): every `tests/*.py` must be referenced by a workflow.
   This is a prerequisite for any Q2-grounded relocation.

*Revert:* delete four test files and four `ci.yml` steps. *Verification:* CI green with no
`AGENTS.md` change.

### Phase 1 — `/doctor` pass: layout, dependency lists, architecture overview

Removes rows 6, 11 and part of 1 (§12.1): ~21,500 characters. Run `/doctor`, review its
proposal by hand, and hand-write the 18-node tree so
`tests/test_agents_md_tree_drift.py` still passes. Lower the size-budget constants to the
new value in the same PR.

*Revert:* `git revert`. *Verification:* `python3 -m unittest -v tests/test_agents_md_tree_drift.py`;
`juniper-check-doc-links`; `juniper-docs-additions-check` with a token diff in the PR body.

### Phase 2 — Write the six new `docs/REFERENCE.md` sections

**Additive only; `AGENTS.md` is not touched.** 11,443 characters for `wait_for_checks.py`,
`release_train/ceremony.py`, `open_signed_pr.py`, `assert_release_tag.bash`,
`experiments/run_suite.py`, `release_train/notes_render.py`. Add a `docs/DOCUMENTATION_OVERVIEW.md`
"I Want To" row for each. **Derive `assert_release_tag.bash` from source, not from
`AGENTS.md`** — the existing entry is wrong (§2.4 #1).

*Revert:* `git revert`. *Verification:* `juniper-check-doc-links`; each new section's flags
checked against the script's own argument parsing.

### Phase 3 — Prune `## Key Files` and `## CI/CD Pipelines`

The big one: rows 7 and 8, ~113,100 characters. Sequence within the phase:
(a) move the ~12 test rationales into their test modules' docstrings; (b) move the nine
small utility entries into their module docstrings; (c) delete `### Utilities`,
`### Tests`, `### CI/CD Workflows`, `### Package and Metadata`, `### Documentation`,
`### Scripts and Launchers`, `### Configuration`, `## CI/CD Pipelines`; (d) add
`## Where To Look`; (e) leave tombstone comments.

**This PR will trip `juniper-docs-additions-check` hard** — deleted headings plus deletion
runs far over `--min-run 5`. Handle it correctly: attach the token diff proving relocation
(G1/G3), then apply the `Allow-Docs-Rewrite:` trailer, **and carry the trailer into the
squash commit message** so `main-verify` (`.github/workflows/main-verify.yml:196`) does not
redden main afterwards. The standing lesson from commit `40230d2` (`#1165`) is *restore,
do not waive* — the token diff is what distinguishes this case from that one.

*Revert:* `git revert`. *Verification:* full `tests/` run; `juniper-check-doc-links`; the
relocation gate at 100%.

### Phase 4 — The remaining sections and the resident core

Rows 2, 3, 4, 5, 9, 10, 12, 13, 14, 15 (~19,900 characters) plus `## Traps With No Gate`.
Lower the size budget to **200 lines / 18,000 characters** and promote
`tests/test_agents_md_shape.py` from report-only to blocking in the same PR. Add G17's
convention lines to `.github/pull_request_template.md` and the three `.claude/agents/*.md`
prompts.

*Revert:* `git revert`. *Verification:* the four existing `test_agents_md_*` gates plus the
two new ones.

### Phase 5 — Optional, evidence-gated

Only if the §14 soak shows the pointer failing: (a) `claudeMdExcludes` for the parent,
after empirically verifying the exclusion with `/context` (§11.2) and creating a real
`.claude/settings.json`; (b) a thin `.claude/rules/` layer with `paths:` frontmatter for
the surviving component hazards — with §7.6's caveat that this borrows another proposal's
mechanism.

### Phase 6 — Fleet portability

Copy `tests/test_agents_md_size_budget.py` and `tests/test_agents_md_shape.py` into the
other eight repos using the self-locating idiom of
`tests/test_agents_md_header_schema.py`, with per-repo ceilings set to current size and
ratcheted down as each repo is pruned. **The gates port; the prune does not** — canopy
(94,373) and cascor (70,118) each need their own §2 analysis.

---

## 14. Verification strategy

### 14.1 Mechanical (CI, every PR)

| Check | What it proves |
|---|---|
| `tests/test_agents_md_size_budget.py` | the level holds |
| `tests/test_agents_md_shape.py` | the accretion *mechanism* is blocked |
| `tests/test_agents_md_relocation.py` | no token left the repo — the anti-content-loss gate |
| `tests/test_agents_md_tree_drift.py` (existing) | no directory lost from the pruned tree |
| `tests/test_agents_md_header_schema.py` / `_version_drift.py` (existing) | the header survives the rewrite |
| `juniper-check-doc-links` (pre-commit + `docs` CI lane) | every pointer in the core resolves |
| `juniper-docs-additions-check` (`ci.yml:877`, `main-verify.yml:196`) | the deletion is seen, reviewed, and justified rather than silent |
| G12 mirror lint (new) | every `tests/*.py` is actually wired into a workflow |

### 14.2 Behavioural — the soak that actually answers §7

Mechanical gates prove the bytes moved. They cannot prove an agent still finds them. Before
Phase 6, run a soak:

- **Population:** the next N ≥ 20 real component-touching tasks (not synthetic prompts).
- **Metric:** did the session open the relocated destination (`docs/REFERENCE.md` section,
  test docstring, `ci.yml`) before editing the component? Observable in the transcript.
- **Pass bar (owner to set):** suggested ≥ 80%, with **zero** incidents in which a session
  contradicted a relocated contract.
- **On failure:** apply §7.7's ladder — row, then gate, then path-scoped rule. Do not
  re-inline.

**This is the only honest test of the central objection, and the proposal should not be
declared successful before it runs.** Note the standing method rule from this project's
own experimental practice: on a stochastic effect, report **rates over N ≥ 20**, not
anecdotes.

### 14.3 Level and rate telemetry

`/context` renders a `Memory files` token row and a per-file tree (mechanism fact base
§8b) — a manual before/after screenshot is the cheapest confirmation that the saving is
real, and the only way to confirm §11.2's `claudeMdExcludes` actually applies. Re-run
`util/ad-hoc/2026-08-18_agents_md_growth_curve.bash` monthly: if the post-prune slope
approaches 2,000 B/day, the redirect has failed and E6's weakness (i) has materialised.

---

## 15. What this proposal does NOT solve

1. **The rate of knowledge production.** ~2,000–2,900 B/day of new operator knowledge keeps
   being produced. This redirects it; it does not reduce it (§9.4).
2. **`docs/REFERENCE.md`'s own growth.** 16,008 → 162,231 bytes since 2026-06-01, faster
   than `AGENTS.md`. On-demand loading makes it cheap, not navigable. At 500 KB it will
   need its own index — probably a per-subject split under `docs/`.
3. **`MEMORY.md`.** Different subsystem, different (hard) limit, no duplication to remove
   (§16).
4. **Enforcement.** The 14 resident hazards remain advisory. Mechanism fact base §6:
   `CLAUDE.md` is a user message, not a system prompt, and there is no guarantee of
   compliance. Rules that must hold belong in hooks or CI gates, and this repo has no
   active `.claude/settings.json` in which to configure a hook.
5. **The user-global file (3,349 chars)** — untouched, and outside this repo's control.
6. **The parent (11,016 chars)** — only via `claudeMdExcludes`, which is unbanked pending
   the §11.2 verification, and which does not help the other eight repos.
7. **The fleet.** The gates port; the prune does not. Canopy (94,373) and cascor (70,118)
   each need their own overlap analysis.
8. **Other resident budgets.** `.claude/agents/` has its own `EXl=15000` warning threshold
   and this repo ships six agents; the skill listing consumes ~1% of the context window
   with least-invoked descriptions dropped first (mechanism fact base §4a, §8b). Untouched
   here, and a constraint on any proposal that adds skills or agents.
9. **The 4 MiB hard skip** (mechanism fact base §8b), where a memory file is dropped
   *whole*. The size gate incidentally guards it; that is a side effect, not a goal.
10. **The six defects in §2.4.** This proposal removes the *conditions* that produced them;
    fixing #6 in particular is a separate, urgent piece of work.

---

## 16. The `MEMORY.md` problem

**Measured on this host, 2026-08-18:** 139 lines / 20,049 characters / **20,388 bytes**
against a hard **200 lines / 25,000 bytes** (mechanism fact base §2 and §8b, which
corrects the earlier 25,600 estimate from the shipped constant `qpe=25000`). That is
**70%** of the line budget and **82%** of the byte budget. Line-length distribution: mean
143, p50 131, p90 184, max 791 characters.

**Does this proposal help? Largely no, and I will not pretend otherwise.**

- **Duplication is not the problem there.** `MEMORY.md` is *already* the architecture this
  proposal advocates, operating better than anything in this repo: 154 topic files,
  1,082,901 bytes on disk, 20,388 loaded — **53:1** (mechanism fact base §8b). There is no
  redundant corpus to delete; every line is a distinct topic.
- **The growth mechanism is different.** `AGENTS.md` grows by *deepening* existing entries;
  `MEMORY.md` grows by *adding* entries, one per new topic, and topics only accumulate.
  Deduplication has no purchase on that.
- **The failure mode is worse.** `AGENTS.md` overflow costs tokens; `MEMORY.md` overflow is
  **silent content loss** at the next load.

What *does* transfer, honestly and only partially:

1. **The arithmetic.** At the observed 147 bytes/line, the byte axis binds first, at
   roughly **175 lines** — about **31 more entries**. The line budget is not the constraint;
   nobody should plan against 200.
2. **A per-entry character cap.** The mean is 143 and the max is 791 — one entry consumes
   5.5 lines' worth of budget. Capping entries at ~180 characters (today's p90) would
   recover ~1,500 bytes without losing a single topic. That is a *deduplication-adjacent*
   discipline and it is the one thing this thesis genuinely contributes.
3. **A budget gate.** The same shape as `tests/test_agents_md_size_budget.py`, but it
   cannot live in this repo's CI — `MEMORY.md` is outside the repository, at
   `~/.claude/projects/…/memory/`. A `util/` checker invoked manually or from a session
   hook is the realistic form, and that is a different proposal's territory.

**The real remedy for `MEMORY.md` is entry retirement and merging** — a curation policy,
not a deduplication one. It should be planned separately and should not wait for this
proposal, because it is the only one of the two problems where content is being lost.

---

## 17. Open questions and owner decisions

| # | Question | Why it is the owner's |
|---|---|---|
| OQ-1 | Gate constants: **200 lines / 18,000 characters**? A tighter 150/14,000 forces more relocation but risks an unreadable core. | Sets how much friction the team accepts. |
| OQ-2 | Should the shape gate forbid `#NNN` issue citations outright, or only depth-2 nesting? Issue numbers are dense provenance, and this repo values them. | A convention call, not a technical one. |
| OQ-3 | Adopt `claudeMdExcludes` for the parent (§11.2), accepting fleet inconsistency and the unverified `Rzr` predicate — or prune the parent in place as a cross-repo change? | Cross-repo consequence. |
| OQ-4 | Should Phase 5's `.claude/rules/` layer be adopted pre-emptively, or only on soak failure? Pre-emptive adoption reduces §7 risk and dilutes this proposal's thesis. | Whether purity or safety wins. |
| OQ-5 | Confirm or strike resident rules 13 and 14 (deployment approvals; merge only on explicit approval). I asserted them from operating practice, not from a repo artifact. | Only the owner knows the policy. |
| OQ-6 | Soak pass bar (§14.2): is ≥80% pointer-follow acceptable, and what is the rollback trigger? | Defines success. |
| OQ-7 | §2.4 #6 — `tests/test_assert_release_tag.py` runs in no workflow. Fix now as a standalone PR, or fold into Phase 0? | Priority against live publish risk. |

---

## 18. Risk register

| ID | Risk | Likelihood | Impact | Guardrail |
|---|---|---|---|---|
| R1 | A relocated component hazard is never read; a session repeats a known failure | **Medium** | High | G1 relocation gate; §5 residency rule; §14.2 soak; §7.7 ladder |
| R2 | The prune is undone in ~2 months by the observed accretion rate | **High** without E6 | High | Size + shape gates (E6); G14/G15/G16 |
| R3 | The size ceiling is raised instead of honoured | **Medium** | High | G14 justification comment; G15 `BUDGET-RAISE:` requirement; CODEOWNERS review |
| R4 | Phase 3 deletes content whose Phase 2 destination has not landed | Low | **High** | G7 ordering rule; G8 makes it mechanical; phases are independently revertible |
| R5 | `juniper-docs-additions-check` waived without evidence, hiding real loss | **Medium** | High | G3 token diff mandatory in the PR body; the `#1165` / `40230d2` precedent |
| R6 | A Q2 relocation cites a gate that does not run (the §2.4 #6 shape) | **Medium** | High | G12 mirror lint, shipped in Phase 0 |
| R7 | `claudeMdExcludes` silently does nothing (`Rzr` unverified) | Medium | Low | Treat the 11,016 bytes as unbanked; verify with `/context` before claiming it |
| R8 | HTML comments are not stripped on the `CLAUDE.md` path | Low | Low | Budget counts comments; exposure ≈600 characters |
| R9 | The core is written densely rather than by relocating — short but unusable | Medium | Medium | Dual ceilings (G10); overflow goes to `docs/REFERENCE.md`, never to a raised ceiling |
| R10 | `docs/REFERENCE.md` becomes unnavigable at 500 KB | **High** over 6 months | Medium | Out of scope; named in §15 item 2 as follow-on work |

---

## 19. Summary judgement

**What this proposal is strong at.** The overlap is real, large, and measured: 71% of
`### Utilities` bytes have a `docs/REFERENCE.md` section on the same subject; 96% of the
distinctive tokens in the three big sections are recoverable from the repo; the official
EXCLUDE list condemns ~90% of the file; the navigational destination
(`docs/DOCUMENTATION_OVERVIEW.md:21–61`) already exists and is maintained. The remedy needs
no new mechanism, no unverified fact, and no Claude Code feature — it cannot be invalidated
by a client release. It removes the conditions that produced six verified defects, and the
relocation obligation is bounded at 22,171 characters, of which 11,443 is under two days of
`docs/REFERENCE.md`'s normal growth.

**What it is weak at, without qualification.** It converts free knowledge into a tool call
whose follow rate I cannot measure and no published benchmark reports. Its best defence —
"pointers for subjects, resident text for hazards" — is a design principle, not a
mechanism, and the file's own history is evidence *against* it: 33 authors wrote a pointer
and then wrote the summary anyway. And the prune addresses the level while the problem is
the rate; the durable element is the gate, whose central weakness is that a ceiling can
refuse an add but cannot make the alternative attractive. If the redirect fails in
practice, this proposal degrades to a one-time 90% cut with a two-month half-life.

Adopt it for the deletions, which are near-free and overdue. Judge it on Phase 0's gates
and the §14.2 soak, which are the parts that decide whether it lasts.
