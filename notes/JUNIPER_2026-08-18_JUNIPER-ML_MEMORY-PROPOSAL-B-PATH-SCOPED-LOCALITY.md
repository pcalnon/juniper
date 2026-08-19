# Memory Proposal B — Path-Scoped Locality

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## 0. What this document is, and what it is not

This is **one of four independent, competing proposals** for the `AGENTS.md` size problem. It
argues a single architectural thesis to its limit so the owner can compare it fairly against the
other three. It is **not** a consensus plan and it is **not** ratified.

Its assigned thesis: **content should live next to the code it describes**, exploiting the two
path-triggered mechanisms that Claude Code actually implements — per-subdirectory `CLAUDE.md`
(ancestors eager, descendants lazy) and `.claude/rules/` with `paths:` frontmatter.

Every mechanism claim is grounded in
[`JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md)
(hereafter **MECH**). Every size claim is grounded in
[`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md)
(hereafter **BASE**) or on measurements taken for this document and reproducible from the recipes
in §13.

Measurements here were taken in worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`
at `main` = `e209b74`, clean tree, 2026-08-18 — the same anchor BASE used.

### 0.1 A units reconciliation, stated once

BASE reports `AGENTS.md` as **170,137 chars**. That figure is `wc -c` — **bytes**. The file is
**168,317 characters** (`wc -m`); the 1,820 difference is multi-byte box-drawing glyphs
(`├`, `└`, `│`) in the Repository-Structure tree and typographic punctuation (`—`, `→`, `≈`).

This document does its section arithmetic in **characters**, because the mechanism MECH §1
documents measures a JavaScript `content.length` — UTF-16 code units, i.e. characters, not bytes.
Where a BASE byte figure is quoted it is labelled. The two never disagree by more than 1.1%, and
no conclusion here turns on the difference.

---

## 1. The bet, in one page

The file is not one thing. Measured at the granularity that matters for placement:

| Genre | Bytes | Share | Wants to be |
|-------|-------|-------|-------------|
| Component contract lore (`### Utilities` + `### Tests` + per-workflow prose + `## Publishing`) | 104,488 | 62% | loaded **when working on that component** |
| Directory orientation (tree subtrees, the "Run all tests" block, per-directory conventions) | 48,412 | 29% | loaded **when working in that directory** |
| Agent behaviour (conventions, script placement, worktrees, handoff, PR conventions) | 13,836 | 8% | **always on** |

Only the third genre needs to be eager. The mechanisms MECH §4b and §4c document let the first two
be lazy — genuinely lazy, unlike `@`-imports (MECH §3), which relocate bytes and save nothing.

The bet is therefore: **push 91% of the file down the tree, keep 8% at the root, and pay the rest
only when a session actually opens the code it describes.**

**The honest bracket, derived in §5:**

- Eager load falls from **182,682 → 28,201 chars** (−84.6%, ≈38,600 tokens returned).
- A *typical* session, once lazily-loaded content is counted, carries **49% to 67% less** than today.
- A session that touches everything carries **0.9% less** than today. Worst case is parity, not
  regression — but it is *only* parity, and §7.1 does not pretend otherwise.

The proposal is a **relocation, not a diet**. Total retained content falls only ~4% (§5.1). Anyone
looking for a smaller *corpus* should read a different proposal; this one makes the corpus
conditional.

---

## 2. Mechanism grounding — including one fact the brief attributes to MECH that MECH does not contain

### 2.1 What I rely on, all from MECH

| # | Fact | Source |
|---|------|--------|
| M1 | "CLAUDE.md and CLAUDE.local.md files in the directory hierarchy **above** the working directory are loaded in full at launch. Files in **subdirectories load on demand** when Claude reads files in those directories." | MECH §4c (T1) |
| M2 | Rules **without** `paths:` load at launch. Rules **with** `paths:` trigger "when Claude reads files matching the pattern, not on every tool use." Budget: 1,000 expanded patterns / 4 MiB per rule's `paths` list. | MECH §4b (T1) |
| M3 | Nothing truncates. The 40,000 figure is a **per-file** CLI performance warning with a `max()` floor, never an aggregate and never a data loss. Optimise for tokens, never for silencing the warning. | MECH §1 |
| M4 | `@path` imports are expanded at launch and save zero context. Any design resting on them is void. | MECH §3 |
| M5 | All discovered memory files are **concatenated**, not overridden. The parent `Juniper/CLAUDE.md` (11,016 B) is fully additive. | MECH §7 |
| M6 | `claudeMdExcludes` (glob/path, merges across settings layers) suppresses specific ancestor files. | MECH §4d |
| M7 | Block-level HTML comments are stripped before injection — maintainer prose is free. | MECH §4d |
| M8 | CLAUDE.md is delivered as a user message, not the system prompt: "there's no guarantee of strict compliance… To block an action regardless of what Claude decides, use a PreToolUse hook instead." | MECH §6 (T1) |
| M9 | Official guidance: "If an entry is a multi-step procedure or **only matters for one part of the codebase**, move it to a skill or a **path-scoped rule** instead." Target under 200 lines. | MECH §5 (T1) |

M9 is worth pausing on: the official documentation names *exactly* this proposal's mechanism for
*exactly* this proposal's content class. That is the strongest external support Proposal B has,
and it is the only external support it has.

### 2.2 A correction to my own brief

The brief that commissioned this document states:

> doc 2 states nested `CLAUDE.md` and `paths:`-scoped rules are *lost after compaction until a
> matching file is read again*.

**MECH does not contain that statement.** I re-read it end to end. MECH §4a discusses compaction
*only* for Skills ("Post-compaction re-attach is capped at 5,000 tokens per skill / 25,000 total;
truncation keeps the start of the file"). §4b and §4c say nothing about compaction at all, and §8
does not list it among the explicit unknowns.

I therefore treat **post-compaction persistence of lazily-loaded memory as UNVERIFIED**, and I
design for the worse branch — see §7.2. Concretely: if lazy content is dropped at compaction,
Proposal B's behaviour degrades exactly as §7.2 describes and the guardrails in §7.2 are load-bearing.
If it is retained, those guardrails are merely redundant. Nothing in the placement map changes
either way, because nothing safety-critical is placed lazily by construction (§7.4).

### 2.3 Two further facts this proposal needs that are NOT established anywhere

| # | Assumption | Status | If it goes the other way |
|---|-----------|--------|--------------------------|
| **U1** | Nested `AGENTS.md` symlinked as nested `CLAUDE.md` triggers M1 identically to a plain nested `CLAUDE.md`. | UNVERIFIED. MECH §7 confirms the symlink bridge *at the repo root* ("Claude Code reads `CLAUDE.md`, not `AGENTS.md`; our symlink is the officially documented bridge") and MECH §8 item 8 records that "agents.md nesting behaviour in Claude Code was not runtime-tested." | If symlinks are not followed for nested files, write nested files as **plain `CLAUDE.md`** with no `AGENTS.md` twin. This costs only the loss of naming symmetry with the root pair. §9 Phase 1 verifies it before anything else ships. |
| **U2** | From a worktree launch directory, the *main checkout's* `juniper-ml/CLAUDE.md` — a genuine ancestor — is not loaded. | UNVERIFIED, but see the direct observation in §7.3. | If ancestors *are* walked, a worktree session pays the main checkout's file **on top of** its own during the migration window. §7.3 gives the sequencing that makes this a non-event and the two-minute probe that settles it. |

Nothing else in this document rests on an unverified fact.

---

## 3. The problem re-measured at placement granularity

BASE §3 established that three H2 sections hold 79% of the file, and that `### Utilities` +
`### Tests` alone are 52%. Placement needs finer resolution than that. Measured for this document
(reproduce with §13.1):

### 3.1 Where every byte goes, by H2 section

| Lines | Chars | Section | Line |
|------:|------:|---------|-----:|
| 13 | 330 | *(header block)* | `AGENTS.md:1` |
| 6 | 595 | `## What This Is` | `AGENTS.md:14` |
| 89 | 4,616 | `## Build & Package Commands` | `AGENTS.md:20` |
| 44 | 3,640 | `## Publishing` | `AGENTS.md:109` |
| 11 | 1,494 | `## Shared Observability Helpers` | `AGENTS.md:153` |
| 16 | 3,511 | `## Shared Service-Core Contracts` | `AGENTS.md:164` |
| 197 | 20,468 | `## Repository Structure` | `AGENTS.md:180` |
| 376 | 99,303 | `## Key Files` | `AGENTS.md:377` |
| 92 | 16,100 | `## CI/CD Pipelines` | `AGENTS.md:753` |
| 22 | 2,084 | `## Pre-commit Hooks` | `AGENTS.md:845` |
| 10 | 491 | `## Secrets Management (SOPS)` | `AGENTS.md:867` |
| 16 | 2,314 | `## Ecosystem Context` | `AGENTS.md:877` |
| 28 | 2,483 | `## Conventions` | `AGENTS.md:893` |
| 29 | 2,841 | `## Pull Request Conventions` | `AGENTS.md:921` |
| 92 | 4,158 | `## Worktree Procedures` | `AGENTS.md:950` |
| 75 | 3,874 | `## Thread Handoff` | `AGENTS.md:1042` |
| **1,115** | **168,317** | | |

Within `## Key Files`: `### Utilities` 194 lines / 54,509 chars (`AGENTS.md:403`), `### Tests`
116 lines / 34,578 chars (`AGENTS.md:597`), `### CI/CD Workflows` 30 lines / 8,135 chars
(`AGENTS.md:713`); the four remaining H3s total 2,061 chars.

### 3.2 The critical discovery: the bulk is component-shaped, not directory-shaped

The brief observes that `### Utilities` and `### Tests` "map almost one-to-one onto `util/` and
`tests/`". They do — but that is the *wrong cut*, and measuring it is what makes this proposal
different from a naive directory split.

I parsed all 35 `### Utilities` entries and all 57 `### Tests` entries and assigned each to the
**component** it documents (§13.2). The result:

| Destination | Chars | Share of the 88,971 |
|-------------|------:|--------------------:|
| `experiments` (run_experiment / run_suite / experiment_stack / isolated_stack + their 4 test modules) | 26,460 | 30% |
| `agent-suite` (templates / discovery / skills / fleet-triage + their 14 test modules) | 16,212 | 18% |
| `release-train` (detect / propose / notes_render / archive_guard / ceremony / registry + 5 tests) | 15,613 | 18% |
| `drift-checks` (editable-install / env-floor / requirements / doc-tools / ci-tools / service-fork + tests) | 13,404 | 15% |
| `host-orchestration` (plant / chop / reapers / kill helpers + tests) | 6,050 | 7% |
| `cross-repo-pr` (`open_signed_pr.py` / `wait_for_checks.py` + tests) | 5,889 | 7% |
| `worktree-tooling` (cleanup / sweep / session-cleaner + tests) | 2,359 | 3% |
| `agents-md-meta` (the three `test_agents_md_*` lints) | 469 | 1% |
| **falls through to `util/`** | 1,604 | 2% |
| **falls through to `tests/`** | 911 | 1% |

**97% of the two biggest subsections is component lore, not directory lore.** Only 2,515 chars
survive as genuinely directory-level material. That is because of a hard local convention: in this
repo a utility ships with its gate test in the same PR — `util/` is outside every pre-commit Python
hook's scope (`.pre-commit-config.yaml:103,116,136,152,174` all scope to `^(scripts|tests)/.*\.py$`),
so the unittest **is** the gate. The phrase "`util/` is not lint-gated, so this unittest is the gate"
appears verbatim throughout `AGENTS.md:403-712`. The consequence: a `util/` fact and its `tests/`
fact are one fact wearing two hats.

A directory-only split therefore cuts across the grain of the content. The design in §4 uses
directory files for what is genuinely directory-shaped and `paths:` rules — which can span
`util/` + `tests/` + `.github/` in one `paths:` list (M2) — for what is component-shaped.

### 3.3 The concurrency driver, quantified

BASE §2 reports ≈1.3 merges/day into this one file since June. Measured directly (§13.3): **285
commits touched `AGENTS.md` since 2026-06-01**; **23 session worktrees exist under
`.claude/worktrees/` right now**.

Pairwise, every one of the 40,470 commit pairs contends for the same file today. Modelling the
split three ways:

| Split model | Pairs still sharing a file | Reduction |
|-------------|---------------------------:|----------:|
| Today (monolith) | 100% | — |
| **Directory-only** (`util/` / `tests/` / `.github/` / root) | 71.8% | **28.2%** |
| **Component rules only** | 51.5% | **48.5%** |
| **Proposal B** (component rules + directory files + slim root) | 46.5% | **53.5%** |

Excluding the `**Last Updated**` header bump — which is a 1-line same-place edit, not content
contention — the numbers are 78.2% / 53.2% / 45.7%.

**A directory-only split buys 28%. Component scoping nearly doubles that.** This is the single
strongest empirical argument in the document, and it is an argument against the naive form of my
own thesis.

The number that matters most is not the aggregate, though. It is this: **commits touching the root
`AGENTS.md` fall from 285/285 (100%) to 21/285 (7%)** — the file with four CI gates
(`tests/test_agents_md_version_drift.py`, `tests/test_agents_md_header_schema.py`,
`tests/test_agents_md_tree_drift.py`, `.github/workflows/agents-md-touch-up.yml`) and the highest
review scrutiny stops being the hotspot. `ci.yml`'s own fleet lint already flags it as one
(`.github/workflows/ci.yml:989-990` emits ":fire: touches **AGENTS.md** (a flood hotspot…)").

### 3.4 How wide is a real session? (the number §7.1 lives or dies on)

611 squash-merged first-parent commits since 2026-06-01, classified by which top-level units their
changed files touch (§13.4):

| Distinct top-level units touched | PRs | Share |
|---------------------------------:|----:|------:|
| 1 | 351 | 57% |
| 2 | 139 | 23% |
| 3 | 52 | 9% |
| 4 | 53 | 9% |
| 5+ | 16 | 3% |

Restricted to units that would carry a nested memory file under this proposal:

| Memory-bearing units touched | PRs | Share | Cumulative |
|-----------------------------:|----:|------:|-----------:|
| 0 (root / `notes/` / `docs/` only) | 193 | 32% | 32% |
| 1 | 252 | 41% | 73% |
| 2 | 109 | 18% | 91% |
| 3 | 50 | 8% | 99% |
| 4+ | 7 | 1% | 100% |

Unit frequency: `notes/` 39%, `tests/` 26%, `util/` 22%, root 22%, `prompts/` 20%, `.github/` 18%,
`docs/` 8%, `juniper-service-core/` 6%.

**73% of PRs touch at most one memory-bearing directory.** That is far narrower than the brief's
premise assumes — and §7.1 explains, at length, why this measurement is an *optimistic* bound and
what the pessimistic bound looks like.

---

## 4. The design

### 4.1 Three tiers

**Tier 0 — root `AGENTS.md` (eager, every session, every agent).**
Genre A only: things whose absence causes an agent to do damage in the first five minutes, before
it has read anything. Target ≤ 230 lines / ≤ 14,000 chars (§4.4).

**Tier 1 — per-directory `CLAUDE.md` (lazy, M1).**
*Orientation*: what lives in this directory, its local conventions, its lint scope, its "this is the
gate" rule, and its slice of the Repository-Structure tree. Hard cap **60 lines**. These answer
"I've just opened a file here — what do I need to know about *here*?"

**Tier 2 — `.claude/rules/<component>.md` with `paths:` (lazy, M2).**
*Component contract lore*: the 44,350 chars of nested post-incident sub-bullets BASE §4 identified,
plus the per-entry prose they hang under. Each rule's `paths:` spans every directory the component
lives in. These answer "I've just opened `util/release_train/ceremony.py` — what has already gone
wrong here?"

The division is not aesthetic. Tier 1 content is *about a location*; Tier 2 content is *about a
thing that spans locations*. §3.2 measured that 97% of the bulk is the latter.

### 4.2 The placement map

#### 4.2.1 Tier 2 — `.claude/rules/`

Eleven rules. Sizes are measured relocations, not estimates, except where marked.

| Rule file | `paths:` (illustrative — exact globs are a Phase-2 deliverable) | Chars | Sourced from |
|-----------|----------------------------------------------------------------|------:|--------------|
| `.claude/rules/experiments.md` | `util/experiments/**`, `util/experiment_stack.bash`, `util/isolated_stack.bash`, `tests/test_run_experiment.py`, `tests/test_run_suite.py`, `tests/test_list_runs.py`, `tests/test_experiment_*.py`, `tests/test_isolated_stack_script.py`, `conf/experiments/**` | 26,460 | `AGENTS.md:403-712` entries |
| `.claude/rules/release-train.md` | `util/release_train/**`, `tests/test_release_train_*.py`, `.github/workflows/release-train.yml`, `tests/test_release_train_workflow_guard.py` | 24,740 | + `AGENTS.md:805-840` |
| `.claude/rules/agent-suite.md` | `.claude/agents/**`, `.claude/skills/**`, `prompts/agent_templates/**`, `util/prompt_discovery/**`, `util/fleet_triage/**`, `util/template_*.py`, `util/agent_suite_*.py`, `util/install_agents.bash`, `util/scaffold_template.py`, `util/generated_prompt_index.py`, `tests/test_template_*.py`, `tests/test_prompt_*.py`, `tests/test_agent_suite_*.py`, `tests/test_predict_merge.py`, `tests/test_*_skill_lint.py`, `tests/test_agents_frontmatter.py`, `tests/test_fleet_supervisor_contract.py`, `tests/test_symbol_overlay.py` | 16,212 | `AGENTS.md:403-712` entries |
| `.claude/rules/drift-checks.md` | `util/editable_install_drift_check.py`, `util/env_floor_drift_check.py`, `util/requirements_drift_check.py`, `tests/test_*_drift*.py`, `tests/test_service_fork_drift.py`, `tests/test_pyproject_extras.py` | 13,404 | `AGENTS.md:403-712` entries |
| `.claude/rules/host-orchestration.md` | `util/juniper_plant_all.bash`, `util/juniper_chop_all.bash`, `util/reap_pytest_orphans.bash`, `util/kill_all_pythons.bash`, `util/juniper_worker_kill.bash`, `util/check_conda_env_torch.bash`, `util/get_cascor_*.bash`, `tests/test_juniper_*_all.py`, `tests/test_kill_helpers.py`, `tests/test_reap_pytest_orphans.py`, `tests/test_check_conda_env_torch.py`, `scripts/juniper-all-ctl` | 6,050 | `AGENTS.md:403-712` entries |
| `.claude/rules/cross-repo-pr.md` | `util/open_signed_pr.py`, `util/wait_for_checks.py`, `tests/test_open_signed_pr.py`, `tests/test_wait_for_checks.py` | 5,889 | `AGENTS.md:403-712` entries |
| `.claude/rules/publish-path.md` | `.github/workflows/publish*.yml`, `util/assert_release_tag.bash`, `tests/test_assert_release_tag.py`, `tests/test_publish_*.py` | 5,397 | `AGENTS.md:109-152`, `:774-785` |
| `.claude/rules/worktree-tooling.md` | `util/worktree_*.bash`, `util/cleanup_open_worktrees.bash`, `util/remove_stale_worktrees.bash`, `scripts/cleanup_session_worktrees.py`, `tests/test_worktree_*.py`, `tests/test_cleanup_session_worktrees.py` | 2,359 | `AGENTS.md:403-712` entries |
| `.claude/rules/packaging-extras.md` | `pyproject.toml`, `.github/workflows/ci-*.yml`, `.github/workflows/publish*.yml` | 1,984 *(est.)* | `AGENTS.md:881-892` extras table |
| `.claude/rules/tooling-scope.md` | `.pre-commit-config.yaml`, `.markdownlint.yaml`, `.yamllint.yaml` | 1,524 *(est.)* | `AGENTS.md:845-866` hook table |
| `.claude/rules/agents-md-meta.md` | `AGENTS.md`, `tests/test_agents_md_*.py`, `.github/workflows/agents-md-touch-up.yml` | 469 | `AGENTS.md:403-712` entries |
| **Total** | | **104,488** | |

**Sizing rule (binding):** no rule may exceed **20,000 chars**. `experiments` (26,460) and
`release-train` (24,740) violate it on day one and split in Phase 3 — `experiments` into
`experiments-driver` / `experiments-stack` (measured 15,258 / 11,202); `release-train` into
`release-train-engine` / `release-train-ceremony`. I deliberately do **not** publish post-split
figures for the release-train pair because I have not measured that cut, and inventing it would be
exactly the kind of thing §0 says this document does not do.

#### 4.2.2 Tier 1 — per-directory `CLAUDE.md`

| File | Chars | Contents |
|------|------:|----------|
| `tests/CLAUDE.md` | 13,789 | the "Run all tests" block (`AGENTS.md:39-96`, 3,313 chars — it is a `tests/` fact living in `## Build & Package Commands`); the `tests/` subtree of the Repository-Structure tree (8,765); the 911 chars of non-component test prose; **plus the local rule that `util/` is unlinted so the unittest is the gate**, and the `RedactedEnv` / `patch.dict` convention |
| `.github/CLAUDE.md` | 15,077 | `### CI/CD Workflows` (8,135), `## CI/CD Pipelines` minus the release-train and publish subsections (5,216), the `.github/` subtree (1,126), plus orientation |
| `util/CLAUDE.md` | 7,226 | the `util/` subtree (4,822), the 1,604 chars of non-component utility prose (`util/ad-hoc/`, the two "moved to a package" pointers, the shared-screen note), plus the script-placement restatement and the ad-hoc lifecycle |
| `juniper-service-core/CLAUDE.md` | 3,511 | `## Shared Service-Core Contracts` (`AGENTS.md:164-179`) verbatim — six load-bearing invariants that only matter when editing that package or auditing its two forks |
| `notes/CLAUDE.md` | 1,533 | the `notes/` subtree (933) + the full naming convention, which today sits in `## Conventions` as one 700-char bullet |
| `scripts/CLAUDE.md` | 1,612 | `### Scripts and Launchers` (659) + the `scripts/` subtree (953) |
| `juniper-observability/CLAUDE.md` | 1,494 | `## Shared Observability Helpers` (`AGENTS.md:153-163`) verbatim |
| `.claude/CLAUDE.md` | 1,302 | the `.claude/` subtree (902) + the suite's own conventions + the `.gitignore` negation rule |
| `prompts/CLAUDE.md` | 636 | the `prompts/` subtree (336) + the handoff-archive naming rule |
| `docs/CLAUDE.md` | 632 | the `docs/` subtree (332) + "REFERENCE.md is the operator surface; AGENTS.md points at it, never duplicates it" |
| `juniper-ci-tools/`, `juniper-config-tools/`, `juniper-doc-tools/`, `juniper-model-core/CLAUDE.md` | 1,600 | new orientation, ~400 each (console-script names, version/pin lockstep, `ruff` scope per `.pre-commit-config.yaml:197`) |
| **Total** | **48,412** | |

Two placements deserve their reasoning stated:

- **`tests/CLAUDE.md` gets the "Run all tests" block.** It is 58 lines of `python3 -m unittest`
  invocations that only matter once you are in `tests/`, and it is *already stale*:
  `.github/workflows/ci.yml` runs roughly 100 modules while `AGENTS.md:39-96` lists 57. Moving it
  next to the suite makes the staleness visible to the person who can fix it.
- **The Repository-Structure tree is split, not deleted.** `tests/test_agents_md_tree_drift.py:47`
  locates the tree by `if "└── util/" in body or "├── AGENTS.md" in body`, and
  `test_every_tracked_top_level_dir_is_in_the_tree` requires every tracked top-level directory to
  appear as a node. A **top-level-only** tree satisfies both — measured at 42 lines / 2,204 chars,
  versus 195 lines / 20,443 today. The 18,240 chars of sub-tree detail move to the matching
  `CLAUDE.md`. The gate needs no amendment.

#### 4.2.3 What stays eager, and why each one cannot be conditional

| Root section | Rationale |
|--------------|-----------|
| Header block | Three CI gates read it (`test_agents_md_header_schema.py:43`, `test_agents_md_version_drift.py:32`, `agents-md-touch-up.yml`) |
| `## What This Is` | Orientation before any file is read |
| `## Build & Package Commands` (minus the tests block) | An agent runs `python -m build` / `pip install -e .` before reading anything |
| `## Repository Structure` (top-level only) | Required by `test_agents_md_tree_drift.py`; also the map that makes lazy loading *findable* |
| `## Conventions` incl. `### Script placement (mandatory)` | §7.4 — the `/tmp` prohibition must fire on file **creation**, when nothing has been read |
| `## Secrets Management (SOPS)` | Prevents committing an unencrypted `.env`; 491 chars |
| `## Pull Request Conventions` (condensed) | Applies at PR time, which follows no read |
| `## Worktree Procedures` (condensed) | Applies before the first file is opened |
| `## Thread Handoff` (condensed) | The trigger fires on context pressure, not on a read — see §7.2 |
| `## Key Files` → routing table | The index that tells an agent lazy content exists |
| Pointers | One line each to `.github/CLAUDE.md`, `tests/CLAUDE.md`, the rules directory, `docs/REFERENCE.md` |

### 4.3 Root `AGENTS.md` target, with the arithmetic

| Block | Today (lines / chars) | After (lines / chars) | Disposition |
|-------|----------------------:|----------------------:|-------------|
| Header + `## What This Is` | 19 / 925 | 19 / 925 | verbatim |
| `## Build & Package Commands` — build/install/lint | 31 / 1,303 | 24 / 1,050 | trim the six install-variant lines to three |
| `## Build & Package Commands` — "Run all tests" (`:39-96`) | 58 / 3,313 | 2 / 120 | → `tests/CLAUDE.md` + pointer |
| `## Publishing` | 44 / 3,640 | 8 / 620 | → `publish-path.md` + the release convention (one paragraph, stays) |
| `## Shared Observability Helpers` | 11 / 1,494 | 3 / 160 | → `juniper-observability/CLAUDE.md` |
| `## Shared Service-Core Contracts` | 16 / 3,511 | 3 / 170 | → `juniper-service-core/CLAUDE.md` |
| `## Repository Structure` | 197 / 20,468 | 44 / 2,290 | top-level nodes only (measured 42 / 2,204 + heading + fence) |
| `## Key Files` | 376 / 99,303 | 14 / 1,150 | → rules + directory files; leave a routing table |
| `## CI/CD Pipelines` | 92 / 16,100 | 6 / 420 | → `.github/CLAUDE.md` + two rules |
| `## Pre-commit Hooks` | 22 / 2,084 | 6 / 560 | keep the **scope** fact (it is why `util/` needs unittests); table → `tooling-scope.md` |
| `## Secrets Management (SOPS)` | 10 / 491 | 10 / 491 | verbatim |
| `## Ecosystem Context` | 16 / 2,314 | 5 / 330 | extras table → `packaging-extras.md` |
| `## Conventions` | 28 / 2,483 | 24 / 2,000 | drop the `/tmp` incident narrative — the parent carries it (§4.4) |
| `## Pull Request Conventions` | 29 / 2,841 | 14 / 1,150 | keep the verb table; drop the three lookup recipes |
| `## Worktree Procedures` | 92 / 4,158 | 20 / 900 | parent carries location + naming + rules (§4.4); keep the When-to-Use table and the two `notes/` pointers |
| `## Thread Handoff` | 75 / 3,874 | 26 / 1,500 | keep triggers + rules; the procedure is already in `notes/` |
| **Total** | **1,115 / 168,317** | **228 / 13,836** | **−92%** |

**228 lines against an official guideline of 200 (M9).** I will not fudge this: locality alone
does **not** reach 200 lines, and the residual 28 lines are irreducible *within this thesis*
because they are genre-A directives that §7.4 shows must not be path-conditional.

Two honest routes to 200, both explicitly outside this proposal's thesis and both offered as
owner options rather than smuggled in:

- **B-lite (recommended if 200 is a hard requirement):** move the Worktree and Thread-Handoff
  *procedures* to Skills. MECH §4a sanctions exactly this — "Create a skill when… a section of
  CLAUDE.md has grown into a procedure rather than a fact." That removes ~40 lines and lands at
  ~188. It borrows a different proposal's mechanism for two sections, and it introduces the
  skill-listing budget risk MECH §4a flags (1% of context, least-invoked descriptions dropped first
  — material for a 9-repo rollout). It is not free.
- **B+prune:** apply the official EXCLUDE list (MECH §5) to the retained genre-A text. That is a
  different proposal's thesis and is not costed here.

**My position: ship 228 lines.** It is 20% of the current file, 5.6× better than the 1,115 we
have, and the marginal 28 lines are the ones you least want to get wrong.

### 4.4 The parent `Juniper/CLAUDE.md`, and whether to use `claudeMdExcludes`

Facts: 11,016 bytes; a symlink to `Juniper/AGENTS.md`; **fully additive**, never overridden (M5).
Its sections measure: Ecosystem Overview 2,204 · Worktree Procedures 2,169 · Cross-Project
Conventions 1,716 · Parent Directory Structure 1,550 · Working Across Projects 1,077 · Conda
Environments 898 · Project-Level Agent Files 727 · Data Contract 266.

**Recommendation: do NOT use `claudeMdExcludes`. Instead, exploit the additivity in the other
direction.**

Reasoning:

1. **The upside is small and the blast radius is wide.** Excluding it saves 11,016 bytes — 6.0% of
   today's eager load, and after Proposal B lands it would be 39% of a 28,201-char eager budget,
   which sounds impressive until you notice the absolute figure is 2,754 tokens. `claudeMdExcludes`
   merges across settings layers (M6), so a user-scope entry would strip the ecosystem map from
   sessions in **all nine repos**, including cross-repo work where the service-port table and the
   conda-environment table are the whole point.
2. **MECH §8 item 3 lists the exclusion predicate `Rzr(r.path)` as "almost certainly
   `claudeMdExcludes`, unconfirmed."** Building a load-bearing saving on an unconfirmed predicate
   for a 6% return is a bad trade.
3. **Additivity is a *dedup* opportunity, and the leverage is on our side of the boundary.** The
   parent is loaded unconditionally either way. Anything present in both files is pure waste, and
   the right place to delete is the repo file, where we have four CI gates and a review process:
   - Parent `## Worktree Procedures` (2,169) already carries the centralized location, the
     `<repo>--<branch>--<timestamp>--<hash>` naming convention, the per-repo procedure pointers,
     the cross-repo guidance, and the five Rules. The repo's 4,158-char section restates all of it
     and adds a `Quick Reference` bash block (1,892 chars) that itself duplicates
     [`JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`](JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md)
     and
     [`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md).
     **Saving: ~3,250 chars, at zero information loss, because the reader already has the parent's copy.**
   - Parent `## Cross-Project Conventions` (1,716) carries the full Script-placement rule including
     the `/tmp` prohibition and the `phase4_consolidate.py` incident. The repo's
     `### Script placement (mandatory)` (1,602) restates it. Keep a three-line restatement in the
     repo — §7.4 argues this directive is too important to hold in only one place — and drop the
     incident narrative. **Saving: ~500 chars.**
   - The user-global `~/.claude/CLAUDE.md` (3,349) carries the Thread Handoff policy in full. The
     repo's `## Thread Handoff` (3,874) restates it and adds the trigger table. Keep the triggers,
     drop the restatement. **Saving: ~2,370 chars.**

   Total dedup against already-eager ancestors: **~6,120 chars**, more than half of what excluding
   the parent would have saved, with none of the risk and no loss of any fact from any session.

4. **The one exclusion worth considering is scoped and reversible.** If the owner later wants the
   parent's 1,550-char `## Parent Directory Structure` gone (it is a directory listing — precisely
   what MECH §4d says `/doctor` cuts as derivable), the correct fix is to prune the parent file,
   not to exclude it. Excluding is all-or-nothing at file granularity.

**Owner decision D-1 (§12):** whether to adopt `claudeMdExcludes` for the parent. My recommendation
is no; the dedup in point 3 is the better trade and is a prerequisite for the §4.3 line budget
either way.

---

## 5. Byte budget — eager vs lazy, best and worst

### 5.1 Content accounting (a relocation, not a diet)

| | Chars |
|---|------:|
| `AGENTS.md` today | 168,317 |
| → Tier 2 rules | 104,488 |
| → Tier 1 directory files | 48,412 |
| → root `AGENTS.md` | 13,836 |
| **Total after** | **166,736** |
| Net change | **−1,581 (−0.9%)** |

That total *includes* ~5,400 chars of newly-written orientation prose in the Tier-1 files. Netting
it out, **~6,980 chars (4.1%) of the original text is dropped** — and all of it is the
already-eager-elsewhere duplication identified in §4.4, plus the `.serena/` subtree (71 chars,
derivable).

**State it plainly: Proposal B removes almost nothing. It makes almost everything conditional.**

### 5.2 The budget table

| Layer | Before (chars) | Before: eager? | After (chars) | After: eager? |
|-------|---------------:|----------------|--------------:|---------------|
| `~/.claude/CLAUDE.md` | 3,349 | **eager** | 3,349 | **eager** |
| `Juniper/CLAUDE.md` | 11,016 | **eager** | 11,016 | **eager** (§4.4: keep) |
| `juniper-ml/CLAUDE.md` → `AGENTS.md` | 168,317 | **eager** | 13,836 | **eager** |
| 11 `.claude/rules/*.md` | — | — | 104,488 | *lazy, per matched path* |
| 14 nested `CLAUDE.md` | — | — | 48,412 | *lazy, per directory read* |
| **Eager subtotal** | **182,682** | | **28,201** | |
| **Lazy pool** | **0** | | **152,900** | |

Eager reduction: **182,682 → 28,201 = −154,481 chars = −84.6%**. At 4 chars/token (MECH §1's
`eR()` returns 4 or 3), that is **≈38,620 tokens**, or **≈19.3% of a 200k context window returned
before the first prompt**. MECH §6 puts today's always-on memory at ≈25% of the window; this takes
it to ≈4%.

*(`MEMORY.md`, 20,388 chars, is a separate subsystem and is excluded from both columns. See §11.)*

### 5.3 What a session actually carries — five scenarios

Using the measured PR-breadth distribution of §3.4 and the measured Tier-1/Tier-2 sizes of §4.2:

| # | Session shape | Share of PRs | Eager | Lazy loaded | Total | vs today |
|---|---------------|-------------:|------:|------------:|------:|---------:|
| 1 | Root / `notes/` / `docs/` only — a design doc, a release-notes archive, a `CHANGELOG` edit | 32% | 28,201 | 0 | **28,201** | **−84.6%** |
| 2 | One directory + one rule (`tests/` + `drift-checks`) | 41% | 28,201 | 27,193 | **55,394** | **−69.7%** |
| 3 | Two directories + two rules (`util/` + `tests/`, `experiments` + `drift-checks`) | 18% | 28,201 | 60,879 | **89,080** | **−51.2%** |
| 4 | Three directories + three rules (+ `.github/`, + `release-train`) | 8% | 28,201 | 100,696 | **128,897** | **−29.4%** |
| 5 | **Full fan-out — every directory read, every rule fired** | ≤1% | 28,201 | 152,900 | **181,101** | **−0.9%** |

Expected value, weighting by measured **write** breadth: **59,893 chars (−67.2%)**.

Expected value under a **pessimistic read model** — every session reads one more memory-bearing unit
than it writes, which is the honest correction for "you read the gate test even when you don't
change it": **93,749 chars (−48.7%)**.

**Headline, stated as a bracket rather than a point estimate: a typical session carries 49–67%
less always-on memory. Best case 85% less. Worst case 1% less.**

### 5.4 The fragmentation overhead, counted

Scenario 5 is −0.9%, not +5%, because the ~5,400 chars of new orientation prose is more than offset
by the ~6,980 chars of ancestor-duplication removed. There is no hidden per-file tax: MECH documents
no envelope, header, or delimiter cost for memory files. But two real overheads exist and are not in
the table:

- **Cross-reference prose.** Splitting one file into 26 requires each fragment to say where it sits.
  I have budgeted this inside the 5,400 chars; if it runs to 10,000 the scenario-5 figure becomes
  roughly +2% versus today.
- **The root routing table** (1,150 chars) is pure new overhead, paid eagerly, every session. It is
  in the §4.3 budget. It is also the thing that makes the whole design discoverable, so it is not
  optional.

---

## 6. Four-part analysis of each load-bearing element

The instruction was to name where this is weak rather than to advocate. Each element below gets
strengths, inherent (unfixable) weaknesses, a concrete failure scenario, and the specific guardrail.
Guardrails prefer mechanisms this repo already runs.

---

### E1 — Per-subdirectory `CLAUDE.md` (the eager/lazy asymmetry)

**Strengths**

- Documented, first-class, and *actually* lazy (M1) — unlike `@`-imports (M4), which are the trap
  most people fall into.
- Moves **48,412 chars** off the eager path (29% of the file) with no mechanism risk beyond U1.
- Zero new tooling. No settings change, no new file format, no `paths:` glob to get wrong.
- Discovery is inherent: you get `util/CLAUDE.md` precisely when you open something in `util/`.
- Portable to all nine repos (BASE §7) with no per-repo configuration.
- Solves the `notes/`-heavy session case perfectly: 39% of PRs touch `notes/`, and `notes/CLAUDE.md`
  is 1,533 chars.

**Weaknesses (inherent)**

- **Granularity is the filesystem's, not the concept's.** §3.2 measured that only 2,515 of 88,971
  chars are genuinely directory-shaped. The mechanism cannot express "everything about the release
  train", and no amount of care fixes that — it is what the mechanism *is*.
- **Trigger is read, not intent.** Creating a file in a directory need not read one.
- **All-or-nothing per directory.** Opening `util/get_cascor_status.bash` loads the whole 7,226-char
  `util/CLAUDE.md`, including the ad-hoc lifecycle you did not want.
- **No expiry.** Once loaded it is resident for the session (by analogy with MECH §4a's Skills
  statement; not separately documented for nested files).
- **`.github/CLAUDE.md` is 15,077 chars** — over a third of the Tier-1 pool in one file, loaded
  whole whenever any workflow is opened.

**Risks — concrete scenario**

> A session is asked to "add a `--json` flag to `util/env_floor_drift_check.py`". It reads that one
> file, edits it, and writes a brand-new `tests/test_env_floor_json.py` with `Write` — no read in
> `tests/` ever occurs. `tests/CLAUDE.md` never loads. The new test does not use `RedactedEnv`
> (`tests/redacted_env.py`), and `tests/test_env_repr_safety.py` fails in CI with a lint error the
> session has no context for. Net effect: one wasted CI round-trip and a confused debugging loop.

A second, sharper one:

> A session creates `/tmp/analyze_drift.py` because the script-placement rule lives in the root file
> and the root file is 228 lines of competing instructions. The script is lost when the sandbox is
> reaped. This is the exact incident BASE §8 and `AGENTS.md:904-917` were written about. Note this
> failure is *not* caused by Proposal B — it is the status quo failure — but Proposal B must not
> make it more likely, which is why §7.4 keeps that directive eager.

**Guardrails**

| Risk | Guardrail | Precedent in this repo |
|------|-----------|------------------------|
| Directory file drifts from its directory's contents | **New** `tests/test_nested_memory_drift.py`: every directory listed in the root routing table has a `CLAUDE.md`; every nested `CLAUDE.md` is in the routing table; each is ≤ 60 lines; each carries the `<!-- juniper-memory: tier1 -->` marker. Self-locating, droppable into any Juniper repo. | Modelled on `tests/test_agents_md_tree_drift.py` and `tests/test_template_library_drift.py` (which exists precisely because `prompts/**` is pre-commit-excluded) |
| A nested file re-accretes | The 60-line cap in the same test, failing loudly with the offending file and line count. | Same pattern as the 500-line Skill guidance |
| Tree drift after the split | `tests/test_agents_md_tree_drift.py` already enforces the top-level nodes. **Extend** it to assert each top-level directory's *sub-tree* lives in that directory's `CLAUDE.md`. | Direct extension of `tree_block()` at `tests/test_agents_md_tree_drift.py:44-50` |
| Genre-B leaks back into the root | **New** lint: no `- \`util/…\`` or `- \`tests/…\`` per-file bullet in root `AGENTS.md`. Trivially checkable, and it is the exact accretion signature BASE §4 identified. | Same shape as `tests/test_agent_suite_path_drift.py`'s substring scan |
| Nested files are markdown-unlinted | They already are not: `.pre-commit-config.yaml:226` excludes only `CHANGELOG.md`, `notes/`, `docs/`, `prompts/`, `scripts/test_prompt-*.md`. `util/CLAUDE.md` etc. get markdownlint **and** `juniper-check-doc-links` (`files: \.md$`, `.pre-commit-config.yaml:263`) for free. | Existing |

---

### E2 — `.claude/rules/` with `paths:` frontmatter

**Strengths**

- **This is the element that carries the proposal.** 104,488 chars — 62% of the file — and the only
  mechanism whose scope matches the content's shape (§3.2).
- `paths:` can span directories. One `release-train.md` covers `util/release_train/**`,
  `tests/test_release_train_*.py`, and `.github/workflows/release-train.yml` — the three places a
  release-train change always lands together.
- **Nearly doubles the concurrency win**: 48.5% pairwise collision reduction versus 28.2% for a
  directory-only split (§3.3).
- Explicitly the officially recommended destination for this content class (M9: "only matters for
  one part of the codebase → move it to a skill or a path-scoped rule").
- Generous budget: 1,000 expanded patterns / 4 MiB per rule (M2). Our largest `paths:` list is ~20
  globs.
- Unlike Skills, rules have **no listing cost** — MECH §4a's 1%-of-context listing budget and
  1,536-char per-entry cap apply to skills, not rules. A proposal that created 11 skills could
  starve its own discovery; 11 rules cannot.

**Weaknesses (inherent)**

- **The `paths:` list is a second source of truth about the codebase, and it drifts.** Rename
  `util/fleet_triage/` and the glob silently stops matching. Nothing errors; the rule just never
  fires again. This is the classic *vacuous-pass* class the owner has flagged repeatedly — a check
  whose machinery breaks and reports success.
- **Read-triggered, exactly like E1** — same discovery gap, same `Write`-without-`Read` hole.
- **Component boundaries are a judgement call and will be wrong at the margins.** Is
  `util/assert_release_tag.bash` release-train or publish-path? (I put it in publish-path. A
  reasonable person disagrees.) Content on a boundary either gets duplicated into two rules or falls
  between them.
- **Two rules exceed the 20,000-char cap on day one** (§4.2.1). A session doing experiments work
  pays 26,460 chars — 6,600 tokens — the moment it opens `run_experiment.py`.
- **Non-negotiable prerequisite: `.claude/rules/` is currently gitignored.** `.gitignore:151` sets
  `.claude/*`, and the negation block at `.gitignore:176-181` re-includes **only** `.claude/skills/`
  and `.claude/agents/`. Without a matching negation, every rule file is invisible to git and the
  whole proposal silently does nothing in CI and for every other session.

**Risks — concrete scenario**

> Phase 3 splits `experiments.md`. The new `experiments-stack.md` carries
> `paths: ["util/experiment_stack.bash", "util/isolated_stack.bash"]`. Six weeks later a refactor
> moves the stack launchers to `util/stacks/`. The glob still parses, the file still exists, CI is
> green, and the rule never fires again. The next session to touch `experiment_stack.bash` does not
> learn the **F-6 pid rule** — that `$!` after `( cd … && nohup … & )` is the *subshell*, not the
> server (`AGENTS.md:538-540`) — and reintroduces exactly the bug that rule was written to prevent.
> Nothing detects this until a live experiment orphans listeners on ports 8110-8139.

**Guardrails**

| Risk | Guardrail | Precedent |
|------|-----------|-----------|
| **Dead glob (the vacuous-pass class)** | **New** `tests/test_rules_paths_resolve.py`: every glob in every rule's `paths:` must match **at least one tracked file** (`git ls-files`). A glob matching zero files is a hard failure naming the rule and the glob. **This is the single most important guardrail in the document** — without it the mechanism fails silently. | Exactly the shape of `tests/test_workflow_script_paths.py`, which asserts every `python <path>` in a workflow resolves |
| Component coverage gaps | Same test, inverted: every tracked path under `util/`, `tests/`, `.github/workflows/` must be matched by **at least one** rule glob **or** be explicitly listed in an `UNCOVERED` allowlist with a reason. A two-sided ledger. | `tests/test_service_fork_drift.py`'s `ENFORCED` / `KNOWN_GAP` two-sided registry — same anti-rot design |
| Rules become invisible to git | `.gitignore` negation added in Phase 2 **plus** a test asserting `git check-ignore .claude/rules/<file>` returns non-zero for every rule. | The `.gitignore:176-181` negation precedent |
| Rule oversize | Same test: hard-fail above 20,000 chars. | New; mirrors the 500-line Skill guidance |
| Rules accidentally mirrored to `~/.claude` | `util/install_agents.bash:51-52` defines only `SRC_AGENTS` / `SRC_SKILLS`. **Add an anti-resurrection assertion to `tests/test_install_agents.py`** that the script never references `rules`. Mirroring rules to `~/.claude/rules/` would make juniper-ml's component lore load in *every* repo's sessions — the exact opposite of the thesis. | `tests/test_ci_tools_drift.py`'s `SequenceSafetyPackageMigrationTest` anti-resurrection pattern |
| A rule silently loads eagerly | Same test: every rule file **must** declare a non-empty `paths:`. A rule without `paths:` loads at launch (M2) and quietly reverts a 26,460-char saving. | New; this is the highest-value single assertion after the dead-glob check |

---

### E3 — The slim eager root

**Strengths**

- **−84.6% eager**, ≈38,600 tokens, ≈19.3% of a 200k window, on every session in the repo.
- Directly targets MECH §5's named failure — "If your CLAUDE.md is too long, Claude ignores half of
  it because important rules get lost in the noise." The 164 mandatory directives BASE §8 counted
  currently compete with 99,303 chars of component prose. After: ~30 directives compete with 13,836
  chars.
- Root contention drops from 100% to 7% of `AGENTS.md`-touching commits (§3.3) — the four existing
  gates and the review process stop being a queue.
- The four gates need **no amendment** (§4.2.2).

**Weaknesses (inherent)**

- **228 lines, not 200** (§4.3). Locality does not reach the guideline.
- **The routing table is new eager overhead** — 1,150 chars paid by every session forever, including
  the 32% that never load anything lazily.
- **"Slim" is a state, not a property.** Nothing about the mechanism keeps it slim; that is entirely
  the guardrails' job.
- **MECH §8 item 6 is blunt: no published Anthropic benchmark measures adherence versus CLAUDE.md
  size.** The adherence argument is a documentation assertion plus general context-rot evidence.
  The *token* argument is solid arithmetic; the *adherence* argument is plausible and unmeasured. I
  am not going to dress it up as more than that.

**Risks — concrete scenario**

> Six weeks after the migration, a session fixes a subtle bug in `util/wait_for_checks.py`. Its
> post-mortem finding is genuinely valuable ("`absent` must be its own bucket, not folded into
> `running`"). The session writes it where every previous session wrote such things — a nested
> sub-bullet in the root `AGENTS.md`. No gate objects: the header is fine, the tree is fine, the
> date is bumped. Repeat 285 times over ten weeks and the root file is back to four figures. **The
> observed growth mechanism (BASE §4) reasserts itself against a structure that has no opinion about
> it.**

**Guardrails**

| Risk | Guardrail | Precedent |
|------|-----------|-----------|
| **Root re-accretion — the primary failure mode** | **New** `tests/test_agents_md_size_budget.py`: hard-fail above **250 lines / 16,000 chars** (10% headroom over the 228/13,836 target). BASE §6 is explicit that all four existing gates "are satisfied by an edit that appends 500 lines" — this is the missing one. Portable and self-locating like its three siblings. | `tests/test_agents_md_header_schema.py:26-29` documents the self-locating convention verbatim |
| Genre-B creeps back | The per-file-bullet lint from E1. A `- \`util/foo.py\` -- …` bullet in root is a structural error, not a style preference. | `tests/test_agent_suite_path_drift.py` substring scan |
| The budget test gets raised instead of the content moved | Require the ceiling to be a **named constant with a comment naming this document**, so raising it is a visible, reviewable diff. Culturally this repo already does this (see the `KNOWN_GAP` ledger). | `tests/test_service_fork_drift.py` |
| The routing table goes stale | Covered by `tests/test_nested_memory_drift.py` (E1) — bidirectional. | `tests/test_template_library_drift.py`'s manifest↔template bidirectionality |

---

### E4 — Ancestor dedup instead of `claudeMdExcludes`

**Strengths**

- **~6,120 chars removed from the repo file with zero information loss** — every deleted fact is
  still eagerly present from the parent or the user-global file (§4.4).
- No settings change, no unverified predicate (MECH §8 item 3), no cross-repo blast radius.
- Reversible by a single revert.
- It is the *only* lever available against a file we do not control the loading of.

**Weaknesses (inherent)**

- **It relies on the ancestor staying put.** If `Juniper/AGENTS.md`'s Worktree Procedures section is
  ever trimmed, juniper-ml silently loses a mandatory directive it deleted on the strength of the
  parent having it. Cross-repo coupling with no cross-repo gate.
- **11,016 chars remain unconditionally eager and this proposal cannot touch them.** After the
  migration the parent is 39% of the eager budget. Locality has no answer for an ancestor.
- The user-global file (3,349) is likewise untouchable from here.

**Risks — concrete scenario**

> Someone prunes `Juniper/AGENTS.md` (it is on the same growth curve — BASE §7 shows canopy at
> 94,373 and cascor at 70,118, so a fleet-wide prune is likely) and removes the worktree naming
> convention as "derivable". juniper-ml deleted its copy in Phase 1. Sessions now create worktrees
> with ad-hoc names, `util/worktree_cleanup.bash`'s `--old-worktree` matching degrades, and stale
> worktrees accumulate. **No CI in any repo detects a directive that vanished from a file in a
> different repository.**

**Guardrails**

| Risk | Guardrail | Precedent |
|------|-----------|-----------|
| Parent-file dedup silently breaks | **New** `tests/test_ancestor_dedup.py`: for each directive juniper-ml deleted on the strength of the parent, assert the parent still contains a marker string. Runs under the same cross-repo gating as the existing drift tests (`GITHUB_ACTIONS=true` **or** `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`; skips loudly when the sibling is absent). It bites weekly in `docs-full-check.yml`, the only job that clones siblings. | `tests/test_doc_tools_drift.py` / `tests/test_service_fork_drift.py` — identical gating idiom |
| A deleted directive matters more than the gate | Keep a **three-line restatement** in the root for the two highest-consequence rules (script placement, handoff triggers) rather than a pure pointer. Deliberate, costed redundancy — 400 chars against an irrecoverable-work incident. | `AGENTS.md:904-917` exists today for the same reason |
| `claudeMdExcludes` adopted later without review | Record it as owner decision **D-1** (§12) with the 6% figure attached, so it is decided rather than drifted into. | — |

---

## 7. The four objections, confronted

### 7.1 The wide-ranging-session objection — the strongest attack

**The objection.** A typical task here touches `util/`, `tests/`, and `.github/`. If a session reads
one file in each, it loads all three nested files, fires several rules, and pays nearly the full
monolith cost — plus fragmentation overhead. Locality then buys nothing and costs coordination.

**This objection is correct in its worst case and wrong about its frequency.** Both halves matter.

**Where it is right.** Scenario 5 in §5.3 is real: full fan-out is **−0.9%**. Proposal B's worst case
is parity. Anyone hoping locality guarantees a saving should stop here — it guarantees only that the
saving is *conditional*, and the condition is session narrowness.

**Where it is wrong — the measurement (§3.4).** Across 611 squash-merged PRs since 2026-06-01:

- **32% touch no memory-bearing directory at all.** These are `notes/` design docs, release-notes
  archives, `CHANGELOG` edits. They pay 28,201 chars — a flat 85% saving. This bucket is *larger*
  than the objection's mental model allows for, and it is the single largest scenario.
- **41% touch exactly one.** 73% cumulative at ≤1.
- **Only 9% touch three or more.**

The tri-directory session the objection describes is **8% of PRs**, not the typical case. And even
that 8% lands at **−29.4%**, not parity — because scenario 4 loads three of eleven rules, not all
eleven.

**Where the measurement is weak, stated without hedging.** *Changed files are a lower bound on read
files.* A session that edits `util/foo.bash` almost certainly reads `tests/test_foo.py` first,
because this repo's convention makes the test the gate. My measurement counts the write, not the
read. The gap is real and I cannot measure it from git.

**So I bracket it.** Pessimistic model: every session reads one more memory-bearing unit than it
writes — shift the whole distribution one bucket right. Expected load becomes **93,749 chars
(−48.7%)** versus **59,893 (−67.2%)** under writes-equal-reads.

**Honest answer to "what fraction of sessions are narrow enough to benefit":**

- Sessions that benefit *substantially* (≥50% reduction): **91%** optimistic / **73%** pessimistic.
- Sessions that benefit *marginally* (<30% reduction): **8%** optimistic / **9%** pessimistic.
- Sessions at parity: **≤1%** either way.
- Expected saving: **49–67%**, not the 85% headline. **The headline is the eager figure and it is not
  the number to plan with.**

**Two things make the wide session cheaper than the objection assumes**, and one makes it worse:

- *Cheaper:* rules are component-scoped, so a wide session fires the rules for the components it
  touched, not all eleven. A session spanning `util/` + `tests/` + `.github/` for *one* component
  (the common shape — §3.2) loads three directory files and **one** rule.
- *Cheaper:* the 32% bucket is not a rounding error. `notes/` is the single most-touched unit in the
  repo (39% of PRs), and it is nearly free under this design.
- *Worse:* nothing unloads. A session that reads one `.github/` file at minute 3 to check a workflow
  name carries all 15,077 chars for the remaining four hours. There is no eviction, and I know of no
  mechanism to request one.

**Guardrail.** Measure it rather than argue about it. `util/prompt_discovery/cli.py` already emits a
JSON grounding bundle with per-probe provenance; extend it (or add
`util/ad-hoc/<date>_memory_load_probe.py`) to record, per session, which nested files and rules were
loaded. Re-run the §5.3 table against real data after 30 days and publish the delta. **If the
measured expected saving is below 40%, the thesis has failed and should be replaced** — that is the
falsification criterion, stated in advance.

### 7.2 Compaction

**First, the correction from §2.2:** MECH does **not** state that nested `CLAUDE.md` and
`paths:`-scoped rules are lost after compaction. It states the re-attach cap for **Skills** only
(§4a). Post-compaction persistence of lazily-loaded memory is **UNVERIFIED**. I design for the worse
branch.

**If lazy memory is dropped at compaction, here is what breaks.** A four-hour session opens
`util/experiment_stack.bash` at minute 10 and absorbs the F-6 pid rule from `experiments.md`. At hour
three it compacts. At hour three-thirty it edits `experiment_stack.bash` again — this time via
`Edit`, which requires a prior `Read`, so the rule re-fires and the rule is fine. **But** it also
writes a *new* helper `util/experiments/teardown_helper.bash` with `Write` and no prior read in that
tree. The F-6 rule is gone from context and does not re-fire. The helper records `$!` after a
backgrounded subshell. Live experiment listeners orphan on ports 8110-8139, and
`util/reap_pytest_orphans.bash` — which has a deliberate live-experiment protection path — cannot
help because the pidfile now holds the wrong pid.

**Three structural answers, in decreasing order of how much they survive:**

1. **Nothing safety-critical is placed lazily.** §7.4 enumerates the directives that stay eager. Post-
   compaction loss of a *component contract* costs a re-read; post-compaction loss of "scripts never
   go in `/tmp`" costs irrecoverable work. The former is acceptable; the latter is why the latter is
   not lazy.
2. **MECH §6 is the real answer and it is not a memory answer at all.** "CLAUDE.md content is
   delivered as a user message after the system prompt… there's no guarantee of strict compliance.
   To block an action regardless of what Claude decides, use a PreToolUse hook instead." A directive
   that must hold deterministically was **never** safe in prose — not before compaction and not
   after. Compaction does not create this problem; it exposes it. Proposal B's response is to move
   the small number of genuinely must-hold rules to hooks and CI gates (§8), which are
   compaction-proof by construction.
3. **The handoff policy must stay eager, and it must stay eager *because* of this.** `AGENTS.md:1042`
   makes thread handoff mandatory *instead of* compaction, precisely so this scenario is rare. That
   policy is itself advisory context (MECH §6) — if it is the thing that vanishes, everything
   downstream of it vanishes too. It is 1,500 chars in the eager budget and it is the cheapest
   insurance in the document.

**Guardrails**

| Risk | Guardrail |
|------|-----------|
| A safety-critical convention is placed lazily by a later PR | `tests/test_agents_md_size_budget.py` gets a companion assertion: a curated list of **directive marker strings** (e.g. `/tmp/` is prohibited, `handoff`, `worktree`, `never merge directly to main`) must be present in the **root** file. If someone moves one down the tree, CI fails and names it. Two-sided, like `test_service_fork_drift.py`. |
| Post-compaction behaviour is unknown | Settle it. §13.5 gives a probe. Until it is settled, treat the pessimistic branch as true. |
| Prose is doing a hook's job | Inventory the ~6 truly must-hold directives and route each to a `PreToolUse` hook or an existing CI gate (§8). This is worth doing **whichever proposal wins**. |

### 7.3 The worktree launch directory — load-bearing, and partly unverified

**The setup.** Sessions here run from two places: the repo root
(`/home/pcalnon/Development/python/Juniper/juniper-ml`) and a session worktree
(`.../juniper-ml/.claude/worktrees/<name>/`). **23 such worktrees exist right now.** This document
was written in one of them.

**The claim the whole proposal rests on:** from a worktree launch directory, `util/`, `tests/`, and
`.github/` are still *descendants* — they are `<worktree>/util/` etc., because a git worktree is a
complete checkout. M1 says descendants load on demand. **The asymmetry therefore holds identically
from a worktree and from the repo root.** This follows directly from M1 plus the filesystem layout;
it needs no additional assumption. Same for `.claude/rules/` (M2 is path-matching, not
ancestry-based).

**The wrinkle, and it is a real one.** Because worktrees live *inside* the repo at
`.claude/worktrees/<name>/`, the **main checkout's** `juniper-ml/CLAUDE.md` is a genuine **ancestor**
of a worktree launch directory. Under a literal reading of M1, a worktree session should load *both*
the main checkout's 168,317-char file **and** the worktree's own copy — ≈336K eagerly.

**Direct observation (this session, Claude Code 2.1.235, 2026-08-18).** The memory files injected
into this session's context were exactly three:

1. `/home/pcalnon/.claude/CLAUDE.md`
2. `/home/pcalnon/Development/python/Juniper/CLAUDE.md`
3. `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus/CLAUDE.md`

`/home/pcalnon/Development/python/Juniper/juniper-ml/CLAUDE.md` **exists** (verified: it is a symlink
to `AGENTS.md`) and is an ancestor, and was **not** injected. The double-load does not happen in
practice.

**But the mechanism is UNVERIFIED (U2), and the candidate explanations differ in consequence:**

| Hypothesis | Consequence if true |
|------------|---------------------|
| **H-a: content dedup.** The ancestor *is* walked; the main checkout and the worktree were byte-identical (both at `e209b74`, clean), so one copy was suppressed. | **Real migration hazard.** During Phase 1 the worktree's trimmed `AGENTS.md` differs from main's fat one, dedup fails, and a worktree session loads **13,836 + 168,317 = 182,153** — worse than today. Transient, but it would look like the proposal backfiring. |
| **H-b: the walk stops at a boundary** (git worktree root, or a `.claude/` segment). | No hazard. The proposal works as designed from day one. |
| **H-c: `Rzr(r.path)` / `claudeMdExcludes` suppresses it** (MECH §8 item 3 lists this predicate as unconfirmed). | No hazard, but the behaviour could change with a settings edit no one associates with memory. |

**Discriminating probe (2 minutes, §13.5).** Insert a unique canary line into the **main checkout's**
`AGENTS.md` (uncommitted), then start a session from an existing worktree and ask it to report the
canary. Canary visible ⇒ **H-a** (ancestor walked; dedup was the reason). Canary absent ⇒ **H-b** or
**H-c** (ancestor genuinely skipped). Either result is actionable, and the probe costs one
`git checkout -- AGENTS.md` to undo.

**Sequencing that makes H-a a non-event, and which I recommend regardless of the probe's outcome:**

1. Land the root trim on `main` **first**, in a PR merged from a worktree created *before* the trim.
2. Immediately after merge, run `git -C <main-checkout> pull --ff-only origin main` so the main
   checkout carries the trimmed file. This is already the mandated Phase 7 of the worktree cleanup
   procedure (`AGENTS.md:1018-1020`).
3. Only then create the worktrees for Phases 2+.

Under this ordering, the two files are byte-identical at trimmed size at every point where a new
session starts, so H-a costs at most 13,836 extra chars for the duration of a single PR.

**Guardrails**

| Risk | Guardrail |
|------|-----------|
| U2 stays unverified and someone builds on the wrong branch | Run §13.5 **before Phase 2**. Record the answer in this document's §12 as decision **D-2**. Do not proceed to Phase 2 on an assumption. |
| A stale main checkout re-creates the divergence | The worktree cleanup procedure already mandates restoring the primary checkout to up-to-date `main` and `util/worktree_cleanup.bash` already implements it as Phase 7 (`AGENTS.md:1018-1020`). **Extend `tests/test_worktree_cleanup.py`** to assert Phase 7 is unconditional. |
| A future launcher change moves the worktree root outside the repo | `scripts/wake_the_claude.bash` and `scripts/cleanup_session_worktrees.py` own that path. Add an assertion to `tests/test_cleanup_session_worktrees.py` that the session worktree root remains under the repo. |

### 7.4 Discovery — which directives may never be path-conditional

**The gap, precisely.** M1 and M2 both trigger on **read**. In this harness the `Edit` tool requires
a prior `Read` of the target (an observed harness behaviour, not a documented memory-mechanism fact),
so *editing* an existing file effectively triggers its directory and rules. **Creating** a file with
`Write` does not. So the failure is sharpest exactly where the placement rules matter most: the
moment a new file is born.

**Method note.** BASE §8 reports **164 lines carrying mandatory language**. Its regex is not
published; a case-insensitive line match on `must|mandatory|never|prohibited` reproduces **125** of
them. The residual is method, not disagreement, and the *distribution* is what matters here:

| Mandatory lines | Section |
|----------------:|---------|
| 53 | `### Utilities` (`AGENTS.md:403`) |
| 25 | `### Tests` (`AGENTS.md:597`) |
| 10 | `### CI/CD Workflows` (`AGENTS.md:713`) |
| 16 | `## CI/CD Pipelines` (`AGENTS.md:753`) |
| 4 | `## Shared Service-Core Contracts` (`AGENTS.md:164`) |
| 4 | `## Repository Structure` (`AGENTS.md:180`) |
| 3 | `### Script placement (mandatory)` (`AGENTS.md:904`) |
| 5 | `## Thread Handoff` (`AGENTS.md:1042`) |
| 2 | `## Worktree Procedures` (`AGENTS.md:950`) |
| 3 | remaining sections |

**108 of 125 (86%) are component contracts** — "`touches_releases` inspects both sides of a
rename/copy", "Offline `--local-git` must raise". BASE §8 already classified these as genre B. They
are *specifications for scripts*, and a session that never opens the script cannot violate them.
**These are safe to make path-conditional**, and that is the bulk of the win.

**The residual 17 are not safe, and they stay eager.** The test is: *does violating this cost
something irrecoverable, before any file has been read?*

| Directive | Root section | Why it cannot be path-conditional |
|-----------|--------------|-----------------------------------|
| Scripts go under `util/`; **`/tmp/` is prohibited** for script source | `### Script placement` | Fires at **file creation**, when nothing has been read. BASE §8 / `AGENTS.md:915` record the irrecoverable-work incident. |
| Handoff instead of compaction; the 95–99% trigger | `## Thread Handoff` | Fires on context pressure, not on a read. §7.2 makes it self-referentially critical. |
| Use worktrees; never create them inside the repo directory | `## Worktree Procedures` | Fires before the first file is opened. |
| Never merge directly to `main`; open a PR | `## Worktree Procedures` | Fires at PR time, downstream of every read. |
| Never commit an unencrypted `.env` | `## Secrets Management` | Fires at commit; 491 chars total. |
| `notes/` naming convention | `## Conventions` | Fires when *creating* a note. `notes/CLAUDE.md` would not have loaded — this document's own creation is the proof. |
| Line length 512; Python ≥3.12 | `## Conventions` | Fires on the first line written in a new file. |

**Every one of these is enforceable, and three already are.** That is the real answer to the
discovery gap — see §8.

**Guardrails**

| Risk | Guardrail |
|------|-----------|
| A must-hold directive drifts down the tree in a later PR | The **directive-marker assertion** of §7.2 — a curated list of marker strings required in the root file. Two-sided and self-maintaining. |
| The eager set grows back by adding "just one more critical rule" | The 250-line / 16,000-char budget test (E3) makes every addition compete against a fixed ceiling, forcing the trade to be explicit. |
| A directive is genuinely critical but only enforceable by prose | Record it in a short `notes/` ledger with the reason. Do not silently accept it. |

### 7.5 Concurrency — the actual driver, and what stops re-accretion

**The benefit, quantified** (full derivation in §3.3, method in §13.3):

| Measure | Today | Proposal B |
|---------|------:|-----------:|
| Commits touching `AGENTS.md` (2026-06-01 → 2026-08-17) | 285 | — |
| Commits touching the **root** file | 285 (100%) | **21 (7%)** |
| Pairwise same-file contention | 40,470 (100%) | 18,817 (46.5%) |
| Reduction | — | **53.5%** (54.3% excluding header bumps) |
| Commits touching exactly one destination | 0 | 131 (46%) |

Two second-order wins the table understates:

- **The header-bump collision mostly disappears.** 104 of 285 commits bumped `**Last Updated**`.
  `agents-md-touch-up.yml` is path-filtered to `AGENTS.md`, so a PR that only edits
  `.claude/rules/release-train.md` does not touch the root file, does not need a date bump, and
  cannot collide on line 8. **Nested memory files must therefore carry no 6-field header** — they
  are not the repo contract, and giving them one would drag the whole date-gate machinery down the
  tree and recreate the collision N times over. This is a design constraint, not an oversight.
- **Sequence-safety screens get quieter.** `juniper-docs-additions-check` runs with **no `--scope`**
  over the universal docs cluster including `AGENTS.md` (`.github/workflows/ci.yml:874-877`,
  `.github/workflows/main-verify.yml:194-196`). Today every `AGENTS.md` edit is screened against a
  single 1,115-line file where a section reflow reads as a large deletion run — the recurring
  false-positive class. After the split, a rewrite of one 400-line rule file is a smaller,
  better-localised diff.

**What stops each new file from re-accreting? Honestly: partly nothing.**

Splitting reduces *contention*; it does not change the behaviour that causes growth. BASE §4
identified the mechanism — successive sessions append per-incident detail as nested sub-bullets
(44,350 chars, 26% of the file). Nothing about being in `experiments.md` instead of `AGENTS.md`
discourages that. Indeed **it gets easier**: `experiments.md` has no CI gate, no reviewer habit, and
no visible size signal.

So re-accretion is not prevented; it is **redirected and capped**:

| Mechanism | What it does | Precedent |
|-----------|--------------|-----------|
| **Per-file size caps in CI** (rules ≤20,000 chars; nested `CLAUDE.md` ≤60 lines; root ≤250 lines / 16,000 chars) | Growth hits a wall in the file where it happens, and the wall names the file. This is the mechanism BASE §6 says is entirely absent today. | `tests/test_service_fork_drift.py` registry style |
| **The cap forces a decision, not a diff** | Exceeding it means splitting the rule or moving detail to `docs/REFERENCE.md`. `docs/REFERENCE.md` is 162,231 chars with 73 sections on precisely these subjects (BASE §5) and is read on demand. BASE §4 counted **32 lines** of `AGENTS.md` that already end by pointing at it — the habit exists and is under-used. | Existing |
| **Blast radius** | 285 commits over 10 weeks spread across 26 files is ~11 per file, versus 285 today. Even unchecked accretion takes ~11× longer to reach today's pathology in any one file. | — |
| **Redirect the genre** | The 44,350 chars of post-mortem sub-bullets are *reference material*. `docs/REFERENCE.md` is where they belong. A rule should carry the invariant ("`--fail-fast` returns on the first failed required context"), not the incident narrative. | The 32 existing REFERENCE.md pointers |

**I will not claim this solves growth.** It buys roughly an order of magnitude of time and makes the
growth visible at the moment it happens instead of six months later. That is worth a lot, and it is
less than a solution.

---

## 8. Guardrail summary — the full CI/test/hook inventory

Every item below is either an existing gate or a new test in the style of an existing one. This repo
has ~100 unittest modules wired into `.github/workflows/ci.yml`; adding six is idiomatic.

### 8.1 New tests

| Test | Asserts | Modelled on |
|------|---------|-------------|
| `tests/test_rules_paths_resolve.py` | **(a)** every `paths:` glob matches ≥1 tracked file (the vacuous-pass killer); **(b)** every rule declares a non-empty `paths:` (a rule without one loads eagerly, M2); **(c)** no rule exceeds 20,000 chars; **(d)** every tracked path under `util/`, `tests/`, `.github/workflows/` is matched by ≥1 rule or is in an `UNCOVERED` allowlist with a reason; **(e)** a synthetic negative proves the checker bites | `tests/test_workflow_script_paths.py`; two-sided ledger from `tests/test_service_fork_drift.py` |
| `tests/test_nested_memory_drift.py` | Root routing table ↔ nested `CLAUDE.md` set is bidirectional; each ≤60 lines; each carries the tier marker; none carries a 6-field header (§7.5); `git check-ignore` returns non-zero for each | `tests/test_template_library_drift.py` |
| `tests/test_agents_md_size_budget.py` | Root ≤250 lines / ≤16,000 chars; no per-file `- \`util/…\`` / `- \`tests/…\`` bullets; **the directive-marker list is present in the root** (§7.2 / §7.4); ceiling is a commented named constant | `tests/test_agents_md_header_schema.py` (self-locating, portable to all 9 repos) |
| `tests/test_ancestor_dedup.py` | Parent `Juniper/AGENTS.md` still contains each directive juniper-ml deleted on its strength; cross-repo-gated (`GITHUB_ACTIONS=true` / `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`), skips loudly when absent | `tests/test_doc_tools_drift.py` |

### 8.2 Extensions to existing tests

| Existing test | Extension |
|---------------|-----------|
| `tests/test_agents_md_tree_drift.py` | Keep the top-level assertion unchanged (a top-level-only tree satisfies it — §4.2.2). **Add**: each top-level directory's sub-tree detail lives in that directory's `CLAUDE.md`. |
| `tests/test_install_agents.py` | Anti-resurrection: `util/install_agents.bash` must never reference `rules` (mirroring component lore to `~/.claude` inverts the thesis). `util/install_agents.bash:51-52` is the current, correct state. |
| `tests/test_worktree_cleanup.py` | Assert Phase 7 (restore the primary checkout to up-to-date `main`) is unconditional — it is the mitigation for §7.3 H-a. |
| `tests/test_agent_suite_doctor.py` / `util/agent_suite_doctor.py` | Add memory-layer checks (rules present + `paths:`-valid, nested files present, root within budget) so `util/agent_suite_doctor.py` reports memory health beside suite health. It is already the dogfood health check. |

### 8.3 Configuration changes

| Change | File | Why |
|--------|------|-----|
| `!.claude/rules/` + `!.claude/rules/**` after `.gitignore:181` | `.gitignore` | **Blocking prerequisite.** `.gitignore:151` + `:176-181` currently re-include only `skills/` and `agents/`; without this every rule is untracked and the proposal silently does nothing. |
| Wire the four new tests into `.github/workflows/ci.yml` | `ci.yml` | `util/` and `prompts/` are outside every pre-commit Python hook (`.pre-commit-config.yaml:103,116,136,152,174`); the unittest **is** the gate. Same reason `tests/test_template_library_drift.py` had to be wired. |
| No markdownlint change | — | `.pre-commit-config.yaml:226` excludes only `CHANGELOG.md`, `notes/`, `docs/`, `prompts/`, `scripts/test_prompt-*.md`. Nested `CLAUDE.md` and `.claude/rules/*.md` get markdownlint **and** `juniper-check-doc-links` (`files: \.md$`, `:263`) automatically. |

### 8.4 Hooks — where prose was never enough

MECH §6: "To block an action regardless of what Claude decides, use a `PreToolUse` hook instead."
Three of the §7.4 directives are cheaply enforceable and should be, **whichever proposal wins**:

| Directive | Hook |
|-----------|------|
| `/tmp/` is prohibited for script source | `PreToolUse` on `Write`: refuse a `.py`/`.bash` target under `/tmp/`. Converts the incident class from advisory to impossible. |
| `notes/` naming convention | `PreToolUse` on `Write`: refuse a `notes/*.md` target not matching `JUNIPER_<date>_JUNIPER-<REPO>_<PHRASE>.md`, honouring the `templates/`, `releases/`, `requirements/`, `legacy/` exemptions ([`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md)). |
| Never commit an unencrypted `.env` | **Already enforced** by the `no-unencrypted-env` pre-commit hook (`.pre-commit-config.yaml:281-285`). |

Each hook that lands lets its prose shrink to one line — a small, real, and *permanent* reduction in
the eager budget.

---

## 9. Migration path

Six phases. Each is independently shippable, independently revertible, and leaves a working system.
**Phase 0 gates everything.**

### Phase 0 — Verify the two unverified mechanisms *(no repo change)*

1. Run the U1 probe (§13.6): does a nested `CLAUDE.md` symlinked to a nested `AGENTS.md` trigger?
2. Run the U2 probe (§13.5): is the main checkout's `CLAUDE.md` loaded from a worktree?

Record both as decisions D-2 / D-3 in §12. **If U1 fails, nested files become plain `CLAUDE.md` with
no `AGENTS.md` twin** — a naming change only. **If U2 resolves to H-a, Phase 1's merge-then-pull
ordering becomes mandatory rather than advisory.** No code changes; fully revertible by doing nothing.

### Phase 1 — Ancestor dedup and the root trim *(one PR, root file only)*

Touches: `AGENTS.md` only.

1. Delete the duplication identified in §4.4 (worktree location/naming/rules, script-placement
   incident narrative, handoff procedure restatement) — ~6,120 chars, every fact still eagerly
   present from the parent or user-global file.
2. Collapse `## Repository Structure` to top-level nodes (195 → 42 lines).
3. Condense `## Publishing`, `## Shared Observability Helpers`, `## Shared Service-Core Contracts`,
   `## CI/CD Pipelines`, `## Key Files` to pointers **that point at sections which do not exist yet**
   — pointing at `docs/REFERENCE.md` in the interim, which already covers all of them (BASE §5).
4. Add the routing table.
5. **Immediately after merge**, `git -C <main-checkout> pull --ff-only origin main` (§7.3).

**The `Allow-Docs-Rewrite:` trailer is required.** `juniper-docs-additions-check` runs with no
`--scope` over `AGENTS.md` (`.github/workflows/ci.yml:874-877`) and post-merge in
`.github/workflows/main-verify.yml:194-196`. A ~150,000-char deletion will FAIL on deleted headings
and deletion runs. **Carry the trailer into the squash commit message**, and follow the standing
rule for this class: token-diff before waiving, and confirm the content is *relocated* rather than
lost. In Phase 1 the honest answer is that it is *deleted* (duplication) or *condensed*, which the
PR body must state explicitly rather than hiding behind the trailer.

*Revert:* `git revert`. Nothing else exists yet.

### Phase 2 — `.gitignore` negation + two pilot rules *(one PR)*

Touches: `.gitignore`, `.claude/rules/release-train.md`, `.claude/rules/experiments.md`,
`tests/test_rules_paths_resolve.py`, `ci.yml`.

Release-train and experiments first: they are the two largest (24,740 / 26,460) and release-train is
the busiest (127 of 285 commits — §3.3), so the pilot exercises the mechanism where it matters most.
Content is *moved*, not copied — the root file already points at `docs/REFERENCE.md` after Phase 1.

*Revert:* delete the two rules and the `.gitignore` lines; the content lives in git history and in
`docs/REFERENCE.md`.

### Phase 3 — Remaining nine rules *(three PRs, grouped by component)*

`agent-suite` + `drift-checks`; then `host-orchestration` + `cross-repo-pr` + `worktree-tooling`;
then `publish-path` + `packaging-extras` + `tooling-scope` + `agents-md-meta`. Split any rule over
20,000 chars during its own PR (§4.2.1), so the cap is never violated on `main`.

### Phase 4 — Nested `CLAUDE.md` *(two PRs)*

PR 1: `util/`, `tests/`, `.github/` (the three that carry 36,092 of the 48,412 chars) plus
`tests/test_nested_memory_drift.py`.
PR 2: the eleven small ones (`scripts/`, `notes/`, `docs/`, `prompts/`, `.claude/`, and the six
sub-package directories).

The Repository-Structure sub-trees move here; extend `tests/test_agents_md_tree_drift.py` in PR 1.

### Phase 5 — Budget gate and hooks *(one PR)*

`tests/test_agents_md_size_budget.py` with the directive-marker list; `tests/test_ancestor_dedup.py`;
the `tests/test_install_agents.py` anti-resurrection assertion; the two `PreToolUse` hooks (§8.4).

**This phase is what makes the migration durable.** Landing Phases 1-4 without Phase 5 buys ten weeks
and then regresses.

### Phase 6 — Measure, then decide *(30 days later, no code)*

Re-run §13 against 30 days of post-migration history and publish: actual eager bytes, actual
per-session lazy load (from the §7.1 probe), actual collision reduction, and per-file growth rates.
**Falsification criterion, fixed in advance: if measured expected saving is below 40%, or if any
rule has grown past its cap twice, the thesis has failed and Proposal B should be replaced rather
than patched.**

### Fleet rollout

BASE §7 argues any remedy must be portable across nine repos, and this one is: no settings change,
no new file format, and the four new tests follow the self-locating convention documented at
`tests/test_agents_md_header_schema.py:26-29`. **But do not roll out until Phase 6.** Canopy
(94,373 B) and cascor (70,118 B) are the next candidates and their component structure differs —
cascor's bulk is model-internals prose, which may not decompose the same way. Verify per repo.

---

## 10. What this proposal does NOT solve

Stated plainly, without softening.

1. **It does not reduce total content.** −0.9% (§5.1). Every byte still exists and is still
   maintained. If the corpus itself is the problem, this is the wrong proposal.
2. **It does not reach the 200-line guideline.** 228 lines (§4.3). Getting there needs Skills or
   pruning — other proposals' theses.
3. **It does not help the widest sessions.** Full fan-out is −0.9% (§5.3 scenario 5). ~9% of PRs
   land in the weak region (−29% to −51%).
4. **It does not prevent re-accretion; it caps and redirects it** (§7.5). The behaviour that grew
   the file 20× in six months is untouched.
5. **It does not touch the parent (11,016 B) or user-global (3,349 B) files.** After migration they
   are **51%** of the eager budget. Locality has no lever against an ancestor; §4.4 argues
   `claudeMdExcludes` is not worth its risk for 6%.
6. **It does not make any directive enforceable.** MECH §6 is unchanged: memory is advisory context.
   The hooks in §8.4 are a *separate* remedy this proposal recommends but does not depend on.
7. **It does not address `docs/REFERENCE.md`'s 162,231-char duplication** (BASE §5). It *relocates*
   the duplicate rather than resolving it — a rule and a REFERENCE section can still say the same
   thing twice. Merging them is a different (and probably better) project.
8. **It does not help `MEMORY.md`.** §11.
9. **It adds 26 files and four CI gates.** That is real maintenance cost, real review surface, and
   real cognitive load for a human navigating the repo. The §3.3 collision numbers say the trade is
   worth it; they do not say it is free.
10. **Its central saving is conditional on session narrowness**, and the narrowness measurement
    (§3.4) is derived from *written* files, which is a lower bound on *read* files. The 49–67%
    bracket is honest, but it is a bracket, not a number.

---

## 11. The `MEMORY.md` problem

**Proposal B does not help. Not partially — not at all.** Saying otherwise would be the single
easiest place in this document to mislead.

The facts (MECH §2): `MEMORY.md` is governed by a genuinely hard limit — first 200 lines **or** first
25KB, whichever comes first; content beyond is **not loaded** and the loss is **silent**. Frontmatter
and block-level HTML comments are stripped before measuring (v2.1.211+). Current position: **139
lines / 20,388 bytes**, ≈80% consumed on the byte axis, ~5,200 bytes of headroom.

Why locality cannot touch it:

- `MEMORY.md` lives at `~/.claude/projects/<project-slug>/memory/MEMORY.md`, **outside the
  repository entirely**. Nothing in `.claude/rules/`, no nested `CLAUDE.md`, and no `.gitignore`
  change reaches it.
- It is explicitly excluded from the CLAUDE.md size check (MECH §1 item 4: "excludes `AutoMem`") and
  governed by a different subsystem.
- It is an **index**, not prose. Its 139 lines are one-line pointers to topic files that are already
  lazily loaded. It is *already* the architecture Proposal B argues for — an index over deferred
  detail — and it is *still* at 80% of its limit. That is a genuinely uncomfortable data point for
  this proposal's thesis, and it deserves to be stated as one: **indexing buys time, not immunity.**

What actually helps, none of which is Proposal B:

1. **Entry-length discipline.** The byte axis is the binding one (80% vs 70% on lines), so the fix
   is *shorter entries*, not fewer. Several entries run 400+ characters with embedded parenthetical
   findings — the same accretion signature BASE §4 found in `AGENTS.md`, in a file where overflow is
   silent and lossy.
2. **Merge related topics.** Multiple entries cover one long-running arc.
3. **Archive closed arcs.** Entries marked RESOLVED / CLOSED / COMPLETE can move to a
   `<slug>_archive.md` topic file referenced by a single index line.
4. **Exploit the HTML-comment strip (MECH §2).** Maintainer prose in block-level HTML comments does
   not count against the limit — free structure for section dividers and provenance.
5. **Add a measurement gate.** A tiny `util/` script (a `memory_index_budget.py` in the mould of
   `util/requirements_drift_check.py`) reporting lines/bytes against 200/25,600 and exiting 1 above
   90%. It cannot run in CI — the file is outside the repo — but it can run from
   `util/agent_suite_doctor.py`, which is already the read-only health check.

**Recommendation: treat `MEMORY.md` as a separate work item with its own owner and its own
deadline.** MECH §9 item 6 says the same. It is the *more urgent* of the two problems — `AGENTS.md`
costs tokens, `MEMORY.md` costs data — and folding it into an `AGENTS.md` proposal, including this
one, is how it gets deferred again.

---

## 12. Owner decisions and open questions

| # | Decision | Recommendation | Consequence if reversed |
|---|----------|----------------|-------------------------|
| **D-1** | Adopt `claudeMdExcludes` for `Juniper/CLAUDE.md`? | **No.** 6% of today's eager load, an unconfirmed predicate (MECH §8 item 3), and a nine-repo blast radius. Do the §4.4 dedup instead. | +11,016 eager chars retained; the ecosystem map stays available for cross-repo work. |
| **D-2** | (Phase 0) Does a worktree session load the main checkout's `CLAUDE.md`? | Settle by probe §13.5 before Phase 2. | If **H-a**, the Phase 1 merge-then-pull ordering is mandatory, not advisory. |
| **D-3** | (Phase 0) Does a nested `AGENTS.md` + `CLAUDE.md` symlink pair trigger M1? | Settle by probe §13.6. | If no, nested files are plain `CLAUDE.md` with no twin. Naming only. |
| **D-4** | Accept 228 root lines, or take B-lite to ~188 via Skills? | **Accept 228.** B-lite borrows another proposal's mechanism and imports the skill-listing budget risk (MECH §4a) for 40 lines. | B-lite reaches the guideline and adds two skills to the nine-repo listing budget. |
| **D-5** | Rule granularity: 11 rules, or 13 after the mandated splits? | **13.** Ship 11, split `experiments` and `release-train` in Phase 3. | Fewer, larger rules mean cheaper maintenance and more bytes per trigger. |
| **D-6** | Fleet rollout before or after Phase 6 measurement? | **After.** BASE §7 wants portability; it does not want eight unmeasured migrations. | Rolling out early risks propagating a design whose measured saving is below the §9 falsification threshold. |

**Open questions I could not resolve:**

- **OQ-1.** Is lazily-loaded memory retained across compaction? UNVERIFIED (§2.2). Designed for the
  worse branch.
- **OQ-2.** Does a *nested* rule directory exist (e.g. `util/.claude/rules/`)? Not documented in
  MECH. If it does, component rules could sit inside the component and the `paths:` drift risk (E2)
  would largely vanish. Worth 10 minutes of probing before Phase 2.
- **OQ-3.** Do `paths:` globs match on `Glob`/`Grep` results, or only on an explicit `Read`? M2 says
  "when Claude reads files matching the pattern". If `Grep` counts, discovery is materially better
  than §7.4 assumes. Unverified; §7.4 assumes the pessimistic reading.
- **OQ-4.** Is there any way to *unload* lazily-loaded memory mid-session? Not documented. If not,
  the "nothing unloads" weakness in §7.1 is permanent.

---

## 13. Verification — reproduce every number here

All commands run from the repository root (or any worktree of it).

**13.1 Section sizes (§3.1).** Split `AGENTS.md` on `^## ` / `^### ` and report per-section line and
character counts. Cross-check the total against `wc -l -m AGENTS.md` → `1115 168317`, and against
`wc -c` → `170137` (§0.1).

**13.2 Component allocation (§3.2, §4.2.1).** Parse top-level `- ` bullets in `AGENTS.md:403-596`
and `:597-712`; classify each by the keyword sets in §4.2.1; sum characters per component.
Sanity check: the parts sum to 88,971 against a measured section total of 54,509 + 34,578 = 89,087
(the 116-char gap is the two H3 heading lines and the blank line before the first bullet).

**13.3 Collision model (§3.3).** For each commit touching `AGENTS.md` since 2026-06-01: resolve the
parent blob, compute its H2/H3 line map, run `git diff -U0 <parent> <commit> -- AGENTS.md`, map each
hunk's *old-side* line range onto that map, project each label onto a destination unit, then compute
pairwise set intersection over all `C(285,2) = 40,470` pairs. Run it three times with three
projections (directory-only, component-only, Proposal B) to reproduce 71.8% / 51.5% / 46.5%.

**13.4 Session breadth (§3.4).** `git log --first-parent --no-merges --format=%H --since=2026-06-01`
(626 commits, 611 with files), then per commit `git show --pretty= --name-only` and count distinct
first path segments, and separately count distinct **memory-bearing** segments (`util`, `tests`,
`.github`, `scripts`, `.claude`, `prompts`, `juniper-*`).

**13.5 The U2 worktree probe (§7.3) — 2 minutes, fully revertible.**

```bash
# In the MAIN checkout (not a worktree):
cd /home/pcalnon/Development/python/Juniper/juniper-ml
printf '\n<!-- JUNIPER-MEMORY-CANARY-U2-20260818 -->\n' >> AGENTS.md

# From an EXISTING worktree, headless:
cd .claude/worktrees/<any-existing-worktree>
claude -p "Reply with exactly CANARY-PRESENT if the text JUNIPER-MEMORY-CANARY-U2-20260818 \
appears anywhere in your project instructions, otherwise reply exactly CANARY-ABSENT."

# Undo, unconditionally:
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git checkout -- AGENTS.md
```

`CANARY-PRESENT` ⇒ **H-a**: the ancestor *is* walked and identical content was being deduped. Adopt
the Phase 1 merge-then-pull ordering as mandatory.
`CANARY-ABSENT` ⇒ **H-b/H-c**: the ancestor is genuinely skipped. No migration hazard.
Use an HTML comment (as above) so the canary is stripped before injection per MECH §4d — if it is
*still* reported, that is additional information about the strip path and should be noted.

**13.6 The U1 nested-symlink probe (§2.3) — 3 minutes, fully revertible.**

```bash
mkdir -p /tmp/u1probe/sub && cd /tmp/u1probe && git init -q
printf '# root\n' > CLAUDE.md
printf 'NESTED-MARKER-U1: the magic word is ossifrage.\n' > sub/AGENTS.md
ln -s AGENTS.md sub/CLAUDE.md
printf 'x = 1\n' > sub/thing.py
claude -p "Read sub/thing.py. Then reply with the magic word if you were given one, else NONE."
rm -rf /tmp/u1probe
```

Magic word returned ⇒ U1 holds; nested `AGENTS.md` + `CLAUDE.md` symlink pairs work, matching the
root convention. `NONE` ⇒ write nested files as plain `CLAUDE.md`.
*(This probe is a throwaway scratch tree, not repository content — `/tmp/` is permitted here per the
`AGENTS.md:913` carve-out for transient data. The probe **script**, if one is written, belongs in
`util/ad-hoc/`.)*

**13.7 Post-migration measurement (Phase 6).** Re-run 13.1, 13.3, and 13.4 against 30 days of
post-migration history; add the per-session load probe from §7.1. Publish the delta against §5.3's
predicted table, including where the prediction was wrong.

---

## 14. Recommendation to the reviewer

Proposal B is the right answer **if** the owner's priority is (a) cutting always-on tokens hard and
immediately, and (b) reducing merge contention in a repo running ~23 concurrent session worktrees at
≈1.3 merges/day into one file.

It is the wrong answer if the priority is a *smaller corpus* (it removes ~4%), the 200-line guideline
as a hard target (it lands at 228), or a guaranteed floor on session cost (it guarantees only that
worst case is parity).

**The three things a reviewer should check hardest, because they are where I am least confident:**

1. **§7.1's narrowness measurement is derived from written files, not read files.** If real sessions
   read much more broadly than they write, the expected saving moves toward the −29% end. The §7.1
   probe settles it; nothing else will.
2. **§2.3 U2** — the worktree ancestor question. If it resolves to H-a and the Phase 1 ordering is
   not followed, the first migration PR looks like a regression.
3. **§7.5's re-accretion answer is a cap, not a cure.** If the owner does not want to add four CI
   gates, Phase 5 does not land, and the whole thing regresses in ten weeks. **Phases 1-4 without
   Phase 5 are worse than doing nothing**, because they add 26 files and buy only temporary relief.

Given the stakes, this document should get an **independent cross-validation pass** before it is
treated as ratified — specifically on the §3.3 collision arithmetic, the §5.3 scenario table, and the
§2.2 correction to the brief.

---

## 15. References

- [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) — measured baseline (BASE)
- [`JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) — verified mechanisms (MECH)
- [`../AGENTS.md`](../AGENTS.md) — the subject file
- [`../docs/REFERENCE.md`](../docs/REFERENCE.md) — 162,231 chars, 73 sections; the on-demand destination for relocated detail
- [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md)
- [`JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`](JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md) — design D-6, the `.gitignore` negation precedent for `.claude/`
- [`JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`](JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md) · [`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md) · [`JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md) — the three procedure documents the root file duplicates
- [`../tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) · [`../tests/test_agents_md_header_schema.py`](../tests/test_agents_md_header_schema.py) · [`../tests/test_agents_md_version_drift.py`](../tests/test_agents_md_version_drift.py) — the three existing structural gates
- [`../tests/test_workflow_script_paths.py`](../tests/test_workflow_script_paths.py) — the model for `test_rules_paths_resolve.py`
- [`../tests/test_service_fork_drift.py`](../tests/test_service_fork_drift.py) — the two-sided `ENFORCED` / `KNOWN_GAP` ledger pattern
- [`../tests/test_template_library_drift.py`](../tests/test_template_library_drift.py) — the bidirectional manifest↔artifact pattern
- [`../util/install_agents.bash`](../util/install_agents.bash) — mirrors `agents`/`skills` only; must never mirror `rules`
- [`../util/agent_suite_doctor.py`](../util/agent_suite_doctor.py) — the existing read-only health check to extend
- [`../util/ad-hoc/README.md`](../util/ad-hoc/README.md) — ad-hoc script conventions for the §13 probes
