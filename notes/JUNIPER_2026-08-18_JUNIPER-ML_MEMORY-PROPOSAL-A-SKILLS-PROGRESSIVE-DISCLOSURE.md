# Memory Proposal A — Progressive Disclosure via Skills

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-18

---

## Purpose and standing

This is **Proposal A** of four independent, competing proposals for the 2026-08-18
shared-session-memory design effort. It is not a plan of record. It argues one
architectural bet as hard and as honestly as it can, so the owner can compare four
arguments rather than four summaries.

**The bet:** the bulk of `AGENTS.md` should become **Skills**, whose bodies load only when
invoked while only `name` + `description` stay resident.

Grounding:

- Measurements: [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) (**doc 1**).
- Mechanisms: [`JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) (**doc 2**).

Every mechanism claim below is grounded in doc 2, or — in three places, all flagged — in a
fresh read of the same shipped **2.1.235** binary doc 2 was built from. Those three readings
**extend** doc 2 in areas doc 2 is silent on; none contradicts it. New measurements taken for
this proposal are reproducible from the commands in [Appendix A](#appendix-a--reproducing-every-number-in-this-document).

Repo state at authoring: worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-kindling-octopus`,
`main` = `e209b74`, clean tree.

### A note on units

`AGENTS.md` is **170,137 bytes** (`wc -c`, doc 1's figure) and **168,317 characters**
(`wc -m`). The CLI's own size check reads `s.content.length` — a JavaScript string length,
i.e. characters — and the skill-listing budget is also computed in characters
([§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters)). Section
arithmetic in this document is therefore on the **character** basis and reconciles to 168,317;
where a table is byte-measured it says so. The two differ by 1.1% and the distinction is
immaterial at budget granularity. Doc 1's headline 170,137 is used whenever quoting doc 1.

Token conversions use **4 characters per token**, which is the binary's own `fgf = 4`
constant ([§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters))
and matches doc 1's 204,890 chars ≈ 51k tokens.

---

## 1. The problem, restated in the terms this proposal acts on

Doc 1 establishes the shape. Three additions, measured for this proposal, sharpen it into
something a design can target.

### 1.1 The accretion is almost perfectly localized

| Metric | Value | Source |
|--------|-------|--------|
| Bytes in nested `  - ` sub-bullets | 44,567 | measured |
| …of those, inside `## Key Files` | **43,842 (98.4%)**, 154 of 156 sub-bullets | measured |

Doc 1 §4 identifies per-incident sub-bullets as the growth mechanism. They are **not spread
through the file**: 154 of 156 are inside one section. The remaining two are in
`## Shared Service-Core Contracts` (`AGENTS.md:175` and one sibling). A design that relocates
`## Key Files` relocates essentially the entire accretion surface.

### 1.2 The churn is concentrated in the same place, and it is single-domain

Attributing every added line since 2026-06-01 to the H2 section it landed in
(285 commits, 2,011 added lines):

| Added lines | % | Commits touching | Section |
|-------------|---|------------------|---------|
| 1,298 | 64.5% | **225 of 285 (79%)** | `## Key Files` |
| 222 | 11.0% | 70 | `## CI/CD Pipelines` |
| 209 | 10.4% | **114 of 285 (40%)** | `## Repository Structure` |
| 103 | 5.1% | 102 | header block (`**Last Updated**` / `**Version**`) |
| 69 | 3.4% | 58 | `## Build & Package Commands` |
| 38 | 1.9% | 10 | Worktree + Handoff + Conventions + PR Conventions, combined |

Then attributing the 1,298 `## Key Files` lines to *domains* (the boundaries this proposal
draws), 225 commits touched that section and:

| Distinct domains touched | Commits |
|--------------------------|---------|
| **exactly 1** | **164 (73%)** |
| 2 | 31 |
| 3 | 9 |
| 4 | 14 |
| 5 | 7 |

**73% of the commits into the busiest section are single-domain.** That is the number that
decides whether splitting reduces the collision surface or merely relocates it
([§10](#10-concurrency--does-this-reduce-the-collision-surface-or-move-it)).

Per-domain share of those 1,298 lines: release-train 40.2% (120 commits), host-orchestration
25.0% (82), experiments 15.6% (45), env/install drift 8.9% (42), agent-suite 5.3% (37),
fleet/sequence-safety 2.2% (8), other 2.6% (9).

### 1.3 The mandatory language is overwhelmingly *not* agent behaviour

Doc 1 §8 counts 164 lines carrying mandatory language and argues they mix two genres. Locating
them by section (predicate: case-insensitive `must|mandatory|never|prohibited|always|required`,
which yields 160 lines — the nearest reproducible predicate to doc 1's 164; the distribution,
not the total, is what matters here):

| Lines | Section | Genre |
|-------|---------|-------|
| 110 | `## Key Files` | B — component contract |
| 21 | `## CI/CD Pipelines` | B |
| 8 | `## Repository Structure` | B |
| 5 | `## Shared Service-Core Contracts` | B, but **security**-load-bearing |
| 5 | `## Thread Handoff` | **A — agent behaviour** |
| 4 | `## Conventions` | **A** |
| 4 | `## Worktree Procedures` | **A** |
| 2 | `## Publishing` | **A** (the Release convention) |
| 1 | `## Pull Request Conventions` | **A** |

**139 of 160 (87%) live in the three sections this proposal relocates. Only 16 are genre A** —
and all 16 fit comfortably inside a 200-line residual file. This is the single most important
fact for the discovery-failure analysis in [§9](#92-discovery-failure--which-directives-are-too-dangerous-to-make-lazy).

### 1.4 Some lore is duplicated four ways

`AGENTS.md:407-413` documents `util/reap_pytest_orphans.bash` in seven sub-bullets. Every fact
in them — the awk candidate gate, the orphan predicate, the P1/P2 protection keys, `PROTECT`
being un-gated by `--verbose`, the 2026-08-16 `e-j-h2h-wide-cap6` incident, the
over-protection direction — appears at greater length in
[`docs/REFERENCE.md`](../docs/REFERENCE.md) `## Pytest Orphan Reaper` (`docs/REFERENCE.md:493`,
4,777 chars). The `AGENTS.md` bullet adds two test-hook env-var names and a pointer back to
the very section it summarizes.

Worse, the `[skip ci]` orphan class exists in **four** places at once:

| Location | Evidence |
|----------|----------|
| `AGENTS.md:735` and `AGENTS.md:826` | two prose retellings |
| `docs/REFERENCE.md:1374` | table row in `## AGENTS.md Date Check` |
| `.github/workflows/agents-md-touch-up.yml:20-45` | 26-line header comment |
| `~/.claude/…/memory/MEMORY.md` | index entry `project_juniper_ml_agents_md_touchup_skipci_orphan` |

And the pointers are circular: `docs/REFERENCE.md:1719` sends the reader to
"AGENTS.md CI/CD Pipelines" for the deep dive, while 32 lines of `AGENTS.md` send the reader
to `docs/REFERENCE.md`. **Neither file is the authority; each defers to the other.** Any
proposal that only moves bytes without settling authority leaves this intact.

---

## 2. What Skills actually give us, and what they do not

From doc 2 §4a, verbatim where load-bearing:

- **In context before invocation: `name` + `description` only** (plus `when_to_use`).
- Doc 2 quotes T1 `/docs/en/skills`: *"a skill's body loads only when it's used, so long
  reference material costs almost nothing until you need it"*, and *"Create a skill … when a
  section of CLAUDE.md has grown into a procedure rather than a fact."* That second sentence
  describes `## Key Files` exactly.
- **Recurring cost:** once invoked, the body "stays there for the rest of the session".
- **Post-compaction re-attach:** capped at **5,000 tokens per skill / 25,000 total**, oldest
  dropped; **truncation keeps the start of the file.**
- **Listing budget:** every skill *name* is always present; descriptions are shortened to fit
  a budget of **1% of the context window**, dropping descriptions for least-invoked skills
  first. Per-entry cap **1,536 chars**; tunable via `skillListingBudgetFraction` /
  `SLASH_COMMAND_TOOL_CHAR_BUDGET`.

Two things Skills do **not** give us, stated up front so nothing later quietly assumes them:

1. **They are not enforcement.** Doc 2 §6: CLAUDE.md content "is delivered as a user message
   after the system prompt… there's no guarantee of strict compliance", and "to block an
   action regardless of what Claude decides, use a PreToolUse hook instead." A skill body is
   *weaker* than resident prose, because it must first be invoked. Anything that must hold
   deterministically belongs in a hook or a CI gate, and this proposal does not pretend
   otherwise.
2. **They do not reduce the total corpus.** Moving 145,675 bytes into skill bodies writes
   145,675 bytes somewhere. The saving is entirely about *when* it is paid for. Actual
   deletion in this proposal comes from de-duplicating against `docs/REFERENCE.md`, and it is
   accounted separately in [§13](#13-beforeafter-byte-budget).

---

## 3. Three facts read fresh from the 2.1.235 binary

Doc 2 is the authority. These three readings cover ground doc 2 is silent on, and each is
load-bearing for a decision below. They are marked **T1-BIN-A** (this proposal's own binary
reads) to keep them distinguishable from doc 2's evidence. All were taken from
`/home/pcalnon/.local/share/claude/versions/2.1.235`.

### 3.1 Verified: skills are model-invocable by default

This is the single fact the whole proposal rests on, and doc 2 does not mention the frontmatter
key that controls it. All three skills this repo ships set `disable-model-invocation: true`
(`.claude/skills/{template-agent,service-smoke,ui-test-author}/SKILL.md`), and three lint tests
*assert* it — [`tests/test_template_agent_skill_lint.py:108-109`](../tests/test_template_agent_skill_lint.py),
`tests/test_service_smoke_skill_lint.py:157-158`, `tests/test_ui_test_author_skill_lint.py:142-143`.
So the repo has never shipped a model-invocable skill and has no empirical evidence that they
work.

The binary settles the default:

```js
disableModelInvocation: typeof e.disableModelInvocation === "function" ? !0 : e.disableModelInvocation ?? !1,
userInvocable: e.userInvocable ?? !0,
```

`?? !1` is `?? false`. **A skill that omits the key is model-invocable**, and separately
user-invocable by default. The key appears 16 times as `disable-model-invocation` and 33 times
as `disableModelInvocation` in the shipped binary.

**What breaks if this reading is wrong:** everything. If reference skills cannot be
auto-invoked, Proposal A degrades to a manual `/skill` menu, which is a materially weaker
product and probably loses to the other three proposals. [§14 Phase 0](#phase-0--settle-the-thesis-half-a-day-revertible-by-deletion) makes
settling this empirically the first, cheapest, independently revertible step.

### 3.2 Verified: an over-budget skill loses its description **entirely**, not gradually

```js
function G7v(e){ let t = tcr(e), r = Qlr(); return t.length > r ? t.slice(0, r - 1) + "…" : t }
function W7v(e){ … return `- ${e.name}: ${G7v(e)}` }
```

and in the budget solver `mgf(…)`: a fitting entry costs `name.length + 4 + descLen`; a
non-fitting one is reduced to `name.length + 2` — i.e. **name only**. The solver sorts
candidates by a priority score, greedily funds descriptions from the highest score down, and
puts the rest in `budgetTruncatedSkills`. Doc 2's "dropping descriptions for least-invoked
skills first" is the ordering; this is the mechanism.

Two consequences the design must absorb:

- **Degradation is all-or-nothing per skill.** There is no half-description. A starved skill
  routes on its *name alone*. This is why [§6](#6-discovery-design--names-descriptions-and-the-listing-budget)
  makes the name carry the trigger.
- **The 1,536-char per-entry cap truncates with `slice(0, cap-1)` — it keeps the start.** Doc 2
  verifies start-preserving truncation for post-compaction *bodies* and is silent on
  descriptions; this closes that gap. Front-loading keywords in a description is correct.

### 3.3 Verified from the binary: the listing budget is exactly 8,000 characters

```js
function ecr(e, t = fgf){ let r = lee(process.env.SLASH_COMMAND_TOOL_CHAR_BUDGET); if (r) return r;
  let n = j7v(), o = (e ?? F7v) * t * n; return Math.max(1, Math.floor(o)) }
var B7v = 0.01, fgf = 4, F7v = 200000, U7v = 1536;
```

The setting's own description string, shipped in the binary: *"Fraction of the context window
(in characters) reserved for the skill listing sent to Claude (default: 0.01 = 1%)."*

So on a 200,000-token window: `200000 × 4 × 0.01` = **8,000 characters**. Every listing
calculation in this document uses that number, and it is a computed constant, not an estimate.

Also verified in the same region: the listing entry text is
`tcr(e) = e.whenToUse ? \`${e.description} - ${e.whenToUse}\` : e.description` — **`when_to_use`
shares the same 1,536-char entry cap as the description.** A design that puts routing hints in
`when_to_use` pays for them out of the same budget.

### 3.4 A fleet risk outside the repo's control

The same settings block documents `syncClaudeAiSkills`: skills enabled on claude.ai are synced
into `~/.claude/skills/synced`, are *"available in every session"*, and **only `false` is
honored** — the feature is enabled server-side per account. Those skills consume the same
8,000-char listing budget and cannot be pre-empted from a repo. Today this is inert: on this
host `~/.claude/skills/` **does not exist at all** (nor does `~/.claude/agents/`), so the
`util/install_agents.bash` mirror has never been deployed and there are no synced skills.
[§11](#11-the-nine-repo-ecosystem) treats this as a standing budget hazard.

---

## 4. Granularity — derived, not asserted

Choosing the number of skills is the central design decision, and it is over-determined: four
independent constraints bound it, and they intersect narrowly.

**Constraint 1 — body ceiling (from doc 2 §4a).** Post-compaction re-attach caps at 5,000
tokens per skill = **20,000 characters**, truncating from the end. A body above that silently
loses its tail after the first compaction. Design ceiling with a 20% margin: **16,000 chars per
`SKILL.md`**. This also sits under the official "keep `SKILL.md` under 500 lines" guidance at
this repo's prose density.

**Constraint 2 — minimum count.** Relocated corpus ≈ 101,000 chars of skill bodies
([§5](#5-the-skill-inventory)). At 16,000 max, `N ≥ ceil(101,000 / 16,000)` = **7**.

**Constraint 3 — maximum count (listing budget, [§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters)).**
8,000-char budget; a well-written description runs ~320 chars, plus `name.length + 4`
(~29) ≈ 350 chars per entry. `8,000 / 350` ≈ **22 entries total**, minus the 3 existing
procedural skills (1,403 chars measured) → ~18 new. Designing to 100% of a budget is how you
discover the budget; design ceiling **14 total**, i.e. ≤11 new.

**Constraint 4 — domain coherence (measured, [§1.2](#12-the-churn-is-concentrated-in-the-same-place-and-it-is-single-domain)).**
73% of `## Key Files` commits touch exactly one of seven observed domains. Splitting *finer*
than the observed co-edit clusters converts single-file edits into multi-file edits and throws
away the concurrency win. Splitting *coarser* than seven merges domains that demonstrably do
not co-edit.

**Intersection: N ∈ [7, 11]. This proposal picks 11**, which is seven measured domains plus
four structural additions, each justified individually:

- release-train **split into two** (`release-train` / `publish-path`): the merged domain's
  source is 23,321 + 10,220 = 33,541 bytes, well over the 16,000 ceiling, and the seam is
  real — proposal/ceremony automation versus publish-path authorization, which already have
  separate designs of record ([release-train plan / runbook] and
  [`JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md`](JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md)).
- `worktree-ops` **split from** `host-orchestration`: different lifecycle (per-task versus
  per-boot) and different owner surface; merging them makes a 10,000-char body that every
  worktree question drags service-orchestration lore into.
- `shared-packages` **added**: `## Shared Observability Helpers` + `## Shared Service-Core
  Contracts` are H2 sections today, not `## Key Files` entries, so they carry no `## Key Files`
  churn signal — but they are 5,007 chars of pure component contract.
- `repo-map` **added**: `## Repository Structure` is its own 20,469-char section with its own
  114-commit churn stream.

---

## 5. The skill inventory

Eleven **reference skills**, all repo-scoped, all model-invocable, all under
`.claude/skills/juniper-ml-<domain>/SKILL.md`.

Source sizes are UTF-8 **bytes** as measured from the line ranges named; body targets are
**character** budgets. (The 1.1% divergence is immaterial at this granularity.)

| # | Skill | Source material in `AGENTS.md` | Source bytes | Body target |
|---|-------|--------------------------------|--------------|-------------|
| 1 | `juniper-ml-release-train` | `:428-459` (registry/detect/propose/notes_render/archive_guard/ceremony) + `:666-678` (their tests) + `:805-840` (`### Release Train`) + `:722` (workflow bullet) | 23,321 | **14,000** + `reference/halt-catalog.md` ≈ 6,000 |
| 2 | `juniper-ml-publish-path` | `:480-485` (`assert_release_tag`) + `:624-634` (publish/tag tests) + `:774-785` (`### Publishing`) + publisher workflow bullets + `:115-152` | 10,220 | **9,000** |
| 3 | `juniper-ml-experiments` | `:517-596` (isolated_stack, experiment_stack, run_experiment, run_suite, get_cascor) + `:682-709` (tests) | 26,923 | **15,000** + `reference/driver-exit-matrix.md` ≈ 5,000 |
| 4 | `juniper-ml-host-orchestration` | `:407-413` (reaper) + `:502-516` (plant/chop) + `:605-608` (tests) | 6,517 | **6,500** |
| 5 | `juniper-ml-worktree-ops` | `:405-406` (`worktree_cleanup`) + `:602-604` (tests) + `:984-1031` (Quick Reference command blocks) | 3,900 | **5,000** |
| 6 | `juniper-ml-env-drift` | `:415`, `:418-427` + `:609-616`, `:619-623`, `:660-665` (tests) | 10,479 | **9,000** |
| 7 | `juniper-ml-agent-suite` | `:416-417`, `:460`, `:472-479` + `:635-639`, `:643-646`, `:650-659` (tests) | 11,737 | **10,000** |
| 8 | `juniper-ml-fleet-triage` | `:461-471` (screens, `predict_merge`) + `:486-499` (`open_signed_pr`, `wait_for_checks`) + `:618`, `:640-642`, `:647-649` | 11,135 | **9,000** |
| 9 | `juniper-ml-ci-workflows` | `### CI/CD Workflows` `:713-742` less publish/release rows + `## CI/CD Pipelines` `:753-844` less its release/publish subsections + `:617` | 11,925 | **10,000** |
| 10 | `juniper-ml-shared-packages` | `## Shared Observability Helpers` `:153-163` + `## Shared Service-Core Contracts` `:164-179` + extras table `:881-892` | 6,607 | **6,500** |
| 11 | `juniper-ml-repo-map` | `## Repository Structure` `:180-376` + `## Key Files` `:377-404`, `:743-752` | 22,911 | **7,000** |
| | **Total** | | **145,675** | **101,000** (+ 11,000 sub-files) |

The 145,675 → 101,000 compression (−31%) is **not** hand-waving: it is exactly the
duplication with `docs/REFERENCE.md` documented in [§1.4](#14-some-lore-is-duplicated-four-ways).
Every skill body is written under one rule:

> A skill body carries **the invariant, the failure class that produced it, and the CI pin that
> holds it**. It carries a link, never a copy, of the operator surface already in
> `docs/REFERENCE.md`.

`juniper-ml-repo-map` takes the largest cut (22,911 → 7,000) because the file-by-file tree is
the purest instance of doc 2 §5's official EXCLUDE list — *"file-by-file descriptions of the
codebase"*, *"anything Claude can figure out by reading code"*. What survives is the part
`ls` cannot answer: which file is the gate for which surface.

### 5.1 Skill descriptions, as designed

Each is written keyword-first, because truncation keeps the start
([§3.2](#32-verified-an-over-budget-skill-loses-its-description-entirely-not-gradually)),
and ends with an explicit `Use before editing <path glob>` clause so the routing signal is a
path the model is about to touch, not a topic it has to infer.

| Skill | Description (as proposed) | Chars |
|-------|---------------------------|-------|
| `juniper-ml-release-train` | Release-train internals: `detect.py` classifications (UNRELEASED_CHANGES / BUMPED_NOT_RELEASED / SHIP_UNCERTAIN / TAG_ONLY), `propose.py` version+CHANGELOG+AGENTS.md edits, `notes_render`, `archive_guard`'s four rules, ceremony HALTs and publish-run selection, `registry.yaml`. Use before editing anything under `util/release_train/` or `release-train.yml`. | 340 |
| `juniper-ml-publish-path` | PyPI publish path: the 7 publishers, tag-only environment ref policies, `assert_release_tag.bash`, job-scoped `id-token`, TestPyPI Gate 1 extras verify, the Release-not-bare-tag convention. Use before editing `publish.yml` / `publish-*.yml`, a pypi/testpypi environment, or `util/assert_release_tag.bash`. | 295 |
| `juniper-ml-experiments` | Experiment stack and drivers: `experiment_stack.bash` port ranges / RUN_DIR / F-6 listener-pid rule, `run_experiment.py` config schema, drive loops, Q-2 stall+wall budgets, exit matrix 0-4, plots/stats, `run_suite.py` cells and budget forwarding, suite YAML gate. Use before editing `util/experiment_stack.bash`, `util/experiments/**`, or a `suites/**.yaml`. | 335 |
| `juniper-ml-host-orchestration` | Host service bring-up and teardown: `juniper_plant_all` / `juniper_chop_all` (systemd and nohup arms, `safe_conda_activate` nounset, KILL_WORKERS), `isolated_stack.bash` trio, `reap_pytest_orphans` live-experiment PROTECT keys. Use before editing `util/juniper_*_all.bash`, `util/isolated_stack.bash`, or `util/reap_pytest_orphans.bash`. | 315 |
| `juniper-ml-worktree-ops` | Worktree tooling internals: `worktree_cleanup.bash` phases 1-7, the dirty-tree exit-1 gate, path-collision refusal, `cleanup_session_worktrees` fail-closed merged-PR check, the sweep scripts. The RULES for when to use a worktree stay in AGENTS.md; this holds the script contracts. Use before editing `util/worktree_*.bash` or `scripts/cleanup_session_worktrees.py`. | 350 |
| `juniper-ml-env-drift` | Environment and install drift checkers: `editable_install_drift_check` path vs version axes (FRESH/WORKTREE_PINNED/ORPHANED × MATCH/STALE/UNKNOWN), `env_floor_drift_check` BELOW_FLOOR, `requirements_drift_check`, the doc-tools/ci-tools pin lints, service-fork drift ledger. Use before editing `util/*drift*.py` or a consumer pin. | 320 |
| `juniper-ml-agent-suite` | Custom-agent suite internals: `prompt_discovery` grounding bundle, the `agent_templates` library + manifest `match_signals`, the data-layer resolver, `scaffold_template`, `agent_suite_doctor`/`summary`, `install_agents` mirror, and every `.claude/agents` + `.claude/skills` lint. Use before editing `.claude/**`, `prompts/agent_templates/**`, or the suite utilities. | 340 |
| `juniper-ml-fleet-triage` | Fleet PR triage and CI waiting: `predict_merge` four verdicts and TRUE delta, the sequence-safety symbol/docs screens and their `Allow-*` trailers, `wait_for_checks` required-vs-observed anchor traps, `open_signed_pr` signed-commit path. Use before editing `util/fleet_triage/**`, `util/wait_for_checks.py`, or `util/open_signed_pr.py`. | 315 |
| `juniper-ml-ci-workflows` | CI workflow contracts: `ci.yml` job set and the Quality Gate `needs:` list, `main-verify` G3 catch-up base, `docs-full-check` ECOSYSTEM_REPOS, security-scan vs per-PR pip-audit, lockfile-update, pr-budget-alarm, `agents-md-touch-up` verify-not-bump, the six `ci-*.yml` sub-package CIs. Use before editing `.github/workflows/**`. | 305 |
| `juniper-ml-shared-packages` | In-repo published sub-packages: `juniper-observability` `register_or_reuse` family, `juniper-service-core` load-bearing security invariants (CR-024 body limit, auth-before-rate-limit, 429 headers, WS tunables), model-core / ci-tools / doc-tools / config-tools, and the pyproject extras contract. Use before editing `juniper-*/` subdirectories or pyproject extras. | 350 |
| `juniper-ml-repo-map` | Repository layout beyond top-level directories: what lives under `util/`, `tests/`, `scripts/`, `conf/`, `notes/`, `prompts/`, `docs/`, and each `juniper-*/` sub-package, plus which file is the gate for which surface. Use when you need to find where something lives and `ls`/glob has not answered it. | 270 |
| | **Total description chars** | **3,535** |

None of these uses `when_to_use`: it shares the same 1,536-char entry cap
([§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters)), so a
second field buys nothing the description cannot carry more cheaply.

---

## 6. Discovery design — names, descriptions, and the listing budget

### 6.1 Listing cost, computed

| Component | Chars |
|-----------|-------|
| 11 reference descriptions | 3,535 |
| 11 × (`name.length` + 4), names averaging 25 | 319 |
| 3 existing procedural skills (`template-agent` 481, `ui-test-author` 414, `service-smoke` 455, + names) | 1,403 |
| 13 inter-entry separators | 13 |
| **Total listing** | **5,270** |
| **Budget** ([§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters)) | **8,000** |
| **Headroom** | **2,730 (34%)** — roughly 8 further skills |

Every entry is far below the 1,536-char per-entry cap, so no description is ever truncated
mid-entry in juniper-ml alone.

### 6.2 The naming convention, and why it is load-bearing

Two classes, deliberately named differently:

| Class | Members | Naming | Mirrored to `~/.claude`? | Invocation |
|-------|---------|--------|--------------------------|------------|
| **Procedural** | the 3 existing (`template-agent`, `service-smoke`, `ui-test-author`) | unprefixed — they are fleet-wide procedures and their names are already correct | **yes** | user-only (`disable-model-invocation: true`, asserted by three lints) |
| **Reference** | the 11 new | `juniper-ml-<domain>` | **no** ([§11](#11-the-nine-repo-ecosystem)) | model-invocable (key omitted) |

The prefix is not decoration. [§3.2](#32-verified-an-over-budget-skill-loses-its-description-entirely-not-gradually)
establishes that a starved skill degrades to `- <name>:` with no description at all. The name
is therefore the last line of routing, and `juniper-ml-release-train` routes on its own while
`release-train` does not disambiguate from a sibling repo's or a cloud-synced skill of the
same topic. Cost: ~11 chars × 11 skills = 121 chars of permanent listing budget, 1.5% of it.

### 6.3 Description authoring rules, lint-enforced

1. **Keyword-first.** The first 80 characters must contain the domain nouns a session would
   use. Truncation keeps the start.
2. **End with `Use before editing <path glob>`.** Routing on the path about to be touched is
   far more reliable than routing on an inferred topic.
3. **160-400 chars.** Below 160 the description under-specifies; above 400, eleven of them
   crowd the budget.
4. **No `when_to_use`.** Same cap, no benefit.
5. **Disjoint path globs.** Two skills claiming `util/**` guarantees a coin-flip.

---

## 7. What is left in `AGENTS.md` — the residual, with arithmetic

### 7.1 Current sections, character basis (reconciles to 168,317)

| Lines | Chars | Section | Disposition |
|-------|-------|---------|-------------|
| 13 | 331 | header block | keep verbatim (schema gate) |
| 6 | 596 | `## What This Is` | condense |
| 89 | 4,617 | `## Build & Package Commands` | drop the 54-line unittest list (3,119 chars) |
| 44 | 3,641 | `## Publishing` | keep the mandatory Release convention only |
| 11 | 1,495 | `## Shared Observability Helpers` | → skill 10 |
| 16 | 3,512 | `## Shared Service-Core Contracts` | → skill 10 + a `paths:` rule ([§12.8](#128-d8--path-scoped-rules-for-the-security-invariants-secondary)) |
| 197 | 20,469 | `## Repository Structure` | → skill 11; keep a gate-minimal tree |
| 376 | 99,304 | `## Key Files` | → skills 1-11; replaced by a Skill Index |
| 92 | 16,101 | `## CI/CD Pipelines` | → skills 1, 2, 9; keep required-context names |
| 22 | 2,085 | `## Pre-commit Hooks` | condense to the three load-bearing scope facts |
| 10 | 492 | `## Secrets Management (SOPS)` | keep verbatim |
| 16 | 2,315 | `## Ecosystem Context` | extras table → skill 10 |
| 28 | 2,484 | `## Conventions` | **keep verbatim — genre A** |
| 29 | 2,842 | `## Pull Request Conventions` | keep verbs + scope + the `id_assignments` prohibition |
| 92 | 4,159 | `## Worktree Procedures` | keep rules; command blocks → skill 5 |
| 74 | 3,874 | `## Thread Handoff` | keep triggers + rules; how-to already in the procedure note |
| **1,115** | **168,317** | | |

### 7.2 The residual budget

| Lines | Chars | Section |
|-------|-------|---------|
| 13 | 331 | header block (unchanged) |
| 3 | 400 | `## What This Is` |
| 18 | 1,150 | `## Build & Package Commands` |
| 9 | 950 | `## Publishing` — the mandatory Release convention |
| 26 | 1,000 | `## Repository Structure` — gate-minimal tree ([§7.3](#73-the-gate-minimal-tree-is-a-verified-constraint-not-a-guess)) |
| 18 | 1,700 | `## Skill Index` — replaces `## Key Files` |
| 12 | 1,000 | `## CI/CD Pipelines` — required contexts + `RELEASE_TRAIN_MODE` kill switch |
| 9 | 650 | `## Pre-commit Hooks` |
| 10 | 492 | `## Secrets Management (SOPS)` (unchanged) |
| 8 | 700 | `## Ecosystem Context` |
| 28 | 2,484 | `## Conventions` (unchanged) |
| 13 | 1,250 | `## Pull Request Conventions` |
| 17 | 1,450 | `## Worktree Procedures` |
| 16 | 1,600 | `## Thread Handoff` |
| **200** | **15,157** | **Total** |

**200 lines exactly — the official guideline in doc 2 §5 — and 15,157 characters, 9.0% of
today's file.**

The `## Skill Index` is the load-bearing new section: one table row per skill, `| skill | what
it holds | when to reach for it |`, ≈100 chars per row × 14 rows plus a header. It is
deliberately redundant with the runtime listing, because it is the one thing that keeps working
if [§3.1](#31-verified-skills-are-model-invocable-by-default) turns out wrong: a resident index
makes every skill reachable by explicit user invocation.

### 7.3 The gate-minimal tree is a verified constraint, not a guess

[`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) is stricter than
its docstring suggests, and a naive minimal tree fails it. Reading the assertions:

- `tree_block()` (`:44-49`) locates the fenced block by searching for `└── util/` **or**
  `├── AGENTS.md` — one of those literals must survive.
- `top_level_dir_nodes()` (`:52-59`) matches `^[├└]──\s+(\S+)` and keeps only names ending in
  `/`. Only **top-level directory** nodes count; files and nested nodes are ignored.
- `test_every_tracked_top_level_dir_is_in_the_tree` (`:93-102`) requires all **18** tracked
  non-hidden top-level dirs (`git ls-tree -d --name-only HEAD`).
- `test_prompts_uses_agent_templates_not_stale_templates` (`:114-116`) additionally asserts the
  literal `agent_templates/` appears **anywhere** in the block — so one nested node must be
  retained.

Minimum conforming tree: fence open, root line, `├── AGENTS.md`, 18 `├── <dir>/` nodes, one
nested `│   └── agent_templates/`, fence close = **23 lines**. Budget 26 with a heading and a
one-line pointer to `juniper-ml-repo-map`.

This matters far beyond byte count. The convention that *every new file appears in the tree* is
what drove **114 of 285 commits (40%)** to touch `## Repository Structure`
([§1.2](#12-the-churn-is-concentrated-in-the-same-place-and-it-is-single-domain)). A tree of
top-level directories changes only when a top-level directory is added — which has happened
6 times in the repo's life. **That obligation essentially disappears**, and the gate still
passes unmodified.

---

## 8. The recurring-cost trap, quantified

This is the objection that kills naive Skills proposals, so it gets explicit arithmetic.

Doc 2 §4a: once invoked, a body "stays there for the rest of the session". A session that
invokes six skills carries six bodies. The question is where the crossover sits.

Let:

- `B` = baseline resident = **168,317** chars (`AGENTS.md` alone)
- `R` = residual resident = **15,157** chars
- `L` = listing = **5,270** chars ([§6.1](#61-listing-cost-computed))
- `s_i` = body of skill *i*

Session cost after = `R + L + Σ_invoked s_i`. Crossover when
`Σ_invoked s_i > B − R − L` = 168,317 − 20,427 = **147,890 chars (36,973 tokens)**.

| Scenario | Chars carried | vs baseline |
|----------|---------------|-------------|
| Nothing invoked | 20,427 | **−87.9%** |
| 1 average skill (9,182) | 29,609 | **−82.4%** |
| 2 skills | 38,791 | **−77.0%** |
| 3 skills (realistic ceiling for one session) | 47,973 | **−71.5%** |
| 5 skills | 66,337 | **−60.6%** |
| **All 11 reference bodies** (101,000) | 121,427 | **−27.9%** |
| **All 11 + all 3 procedural** (130,650) | 151,077 | **−10.2%** |
| **All 14 + every `reference/` sub-file** (141,650) | 162,077 | **−3.7%** |

**Crossover is at 16.1 average-sized skill invocations. The design ships 14 skills.** The
absolute worst case — a session that invokes every skill and reads every sub-file — is
**3.7% cheaper** than today's monolith.

Two honest readings of that last row:

1. **The design cannot be worse than the monolith**, because the entire corpus is smaller than
   the headroom. That is a structural property, not a hope.
2. **The margin in the worst case is 6,240 chars — 3.7%.** That is thin. It means the corpus
   cap is not a nice-to-have; it is the invariant that makes the whole proposal true, and it
   must be a CI gate ([§12.6](#126-d6--the-corpus-cap-invariant), [§15](#15-guardrail-inventory)).
   Add 7,000 chars of new lore anywhere without deleting anything and the worst case becomes a
   loss.

**Realistic expectation.** From [§1.2](#12-the-churn-is-concentrated-in-the-same-place-and-it-is-single-domain),
73% of commits into the busiest section are single-domain. A session that edits one domain
invokes ~1-2 reference skills. The modal saving is therefore in the **−77% to −82%** band, not
the worst case.

---

## 9. Runtime failure modes: compaction and discovery

### 9.1 Compaction behaviour

Doc 2 §4a: re-attach is capped at **5,000 tokens per skill / 25,000 total, oldest dropped**,
and **truncation keeps the start of the file**.

Three design consequences, each already priced in:

**(a) Per-skill cap → the 16,000-char body ceiling.** 5,000 tokens = 20,000 chars. Every body
in [§5](#5-the-skill-inventory) is ≤15,000, leaving ≥25% margin. A body that grew past 20,000
would silently lose its tail after the first compaction — silently, because nothing reports it.
This is exactly the "vacuous pass" class the repo already names: a mechanism that degrades
without going red. The 16,000-char lint is the detector.

**(b) Start-preserving truncation → a mandatory body layout.** Every `SKILL.md` opens with an
`## Invariants` block — the things a refactor must not break — before any narrative. If
anything is ever lost to truncation it is the history, not the rule.

**(c) 25,000-token total cap → post-compaction bodies are partially reclaimed.** 25,000 tokens
= 100,000 chars. The full 11-body corpus is 101,000. So a session that had invoked all eleven
would, after compaction, re-attach ten and drop the oldest. This is simultaneously:

- *good* for the recurring-cost trap — context is reclaimed automatically past the cap; and
- *bad* for correctness — a rule the session was relying on can vanish across a compaction
  boundary with no signal.

The mitigation is the repo's existing one, and it is the honest one:
[**handoff instead of compaction**](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md).
That policy is already mandatory (`AGENTS.md:1042-1057`) and stays resident in the residual
file. A session that hands off before compacting never reaches the re-attach path at all. If a
session *does* compact, the fallback is that the skill can simply be re-invoked — bodies are
idempotent, not stateful.

### 9.2 Discovery failure — which directives are too dangerous to make lazy

The question this proposal must answer honestly: **when the model does not invoke the skill
holding a safety rule, what is lost?**

The measurement in [§1.3](#13-the-mandatory-language-is-overwhelmingly-not-agent-behaviour)
makes the answer unusually clean. Of the 160 lines carrying mandatory language, **139 (87%) are
component contracts inside the three sections this proposal relocates**, and **16 are genre A**.
Those two populations have completely different consequences on a miss, so they get completely
different dispositions.

**Tier 1 — stays resident in `AGENTS.md` (16 lines).** Every genre-A directive, enumerated:

| Directive | Location today | Mechanically gated? |
|-----------|----------------|---------------------|
| Cut a GitHub Release; **never a bare `git push <tag>`** | `AGENTS.md:113-114` | **No** |
| Scripts go under `util/`; **`/tmp/` is prohibited** for script source | `AGENTS.md:904-915` | **No** |
| Never `grep` `id_assignments.yaml` for content — briefs are truncated | `AGENTS.md:940` | **No** |
| Worktrees live in the centralized dir; never inside the repo | `AGENTS.md:1034` | **No** |
| Push before you merge | `AGENTS.md:1036` | **No** |
| Phase 7: restore the primary checkout to up-to-date `main` | `AGENTS.md:1018` | **No** |
| Handoff **replaces** compaction; not optional | `AGENTS.md:1042-1053`, `:1110` | **No** |
| Python `>=3.12` | `AGENTS.md:895` | yes (`pyproject` classifiers, CI matrix) |

Seven of the eight have **no mechanical gate whatsoever**. They are precisely the directives that
must never become lazy, and all of them fit inside the 200-line residual
([§7.2](#72-the-residual-budget)) — combined they are **1,561 characters** as currently written (measured across the 13 directive lines themselves). This proposal keeps
every one of them resident and unchanged.

It also states plainly that keeping them resident is **not the same as enforcing them**
(doc 2 §6). The `/tmp/` rule in particular guards against a permanent data loss that has already
happened once (`AGENTS.md:915`), and it is a `Write`-tool path predicate that a `PreToolUse` hook
could enforce exactly. That is [open question 3](#18-open-questions-for-the-owner), and it is out
of scope here only because it is orthogonal to the Skills bet, not because it is unimportant.

**Tier 2 — `paths:`-scoped rules (5 lines).** The `juniper-service-core` security invariants
(`AGENTS.md:168-171`, `:175`) are genre B — they bind only when editing that subdirectory — but a
miss is a security regression rather than rework. They therefore get a lazy mechanism whose
trigger is a **file read rather than a model decision**
([§12.8](#128-d8--path-scoped-rules-for-the-security-invariants-secondary)), and are additionally
carried in `juniper-ml-shared-packages` so the rule is a net, not the sole copy.

**Tier 3 — lazy in a skill (the remaining 139).** These are safe to make lazy for a reason that
is structural rather than optimistic: **the prose was never what held them.** Examples, with
their actual enforcement:

| "MUST" in `AGENTS.md` | What actually holds it |
|-----------------------|------------------------|
| `select_publish_run` must drop skipped runs (`AGENTS.md:453-457`) | `SelectPublishRunTest`, [`tests/test_release_train_ceremony.py:719`](../tests/test_release_train_ceremony.py) |
| `touches_releases` must inspect both sides of a rename (`AGENTS.md:446`) | `tests/test_release_train_archive_guard.py` |
| Offline `list_releases` must raise, not return `set()` (`AGENTS.md:431`) | `tests/test_release_train_detect.py` |
| Every tracked top-level dir must appear in the tree (`AGENTS.md:681`) | [`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) |
| An oversize cascor suite must declare `execution.stall_seconds` (`AGENTS.md:705-709`) | `tests/test_experiment_suite_yamls.py` |

**51 of the 154 `## Key Files` sub-bullets name their own pin in-line**, and the repo ships
**89 test modules** against **65 non-ad-hoc `util/` scripts** — a ratio that exists precisely
because `util/` is outside every pre-commit Python hook's scope, so unittests are the gate. The
lore's function is to save a round-trip and explain *why* a gate exists; the gate is what stops
the regression.

**Where this argument is weakest, stated plainly.** 103 of the 154 sub-bullets do **not** name a
pin. Some are pinned and simply do not say so; some are genuinely unpinned observations (the
2026-08-16 `e-j-h2h-wide-cap6` reaper incident, for instance, is an observation, not an
invariant). This proposal does **not** claim all 139 are CI-enforced — it claims that the ones
whose violation is *costly* are, and that the residue is advisory either way, resident or lazy.
A reviewer who disagrees should sample twenty of the unpinned sub-bullets before Phase 3 and
promote any that turn out to be load-bearing-and-unpinned into Tier 1 or into a new test.

---

## 10. Concurrency — does this reduce the collision surface, or move it?

Doc 1 §2 identifies ~1.3 PR merges/day into one file as the driver. This section answers
directly, with the measurement from [§1.2](#12-the-churn-is-concentrated-in-the-same-place-and-it-is-single-domain).

### 10.1 Today's collision surface

Every session that adds lore edits **one file**, and — because
[`.github/workflows/agents-md-touch-up.yml:60-64`](../.github/workflows/agents-md-touch-up.yml)
fires `on: pull_request` with `paths: ["AGENTS.md"]` and requires `**Last Updated**` to be
today-or-changed-in-this-PR — a large share of them also edit **the same header line**
(102 of 285 commits touched the header block). Two concurrent PRs adding unrelated lore
therefore collide on a line that has nothing to do with either change.

Concentration, measured as the Herfindahl index of destinations (Σ p²; 1.0 = everything in one
file): **1.00**.

### 10.2 After the split

Distributing the 285 commits by measured domain (with the multi-domain commits counted in each
domain they touch, which is the conservative direction):

| Destination | Commits since 2026-06-01 | Share |
|-------------|--------------------------|-------|
| `juniper-ml-release-train` + `-publish-path` | 120 | 26.4% |
| `juniper-ml-host-orchestration` + `-worktree-ops` | 82 | 18.0% |
| `juniper-ml-ci-workflows` | 70 | 15.4% |
| `juniper-ml-repo-map` | 114 → **≈6** ([§7.3](#73-the-gate-minimal-tree-is-a-verified-constraint-not-a-guess)) | 1.3% |
| `juniper-ml-experiments` | 45 | 9.9% |
| `juniper-ml-env-drift` | 42 | 9.2% |
| `juniper-ml-agent-suite` | 37 | 8.1% |
| `juniper-ml-fleet-triage` | 8 | 1.8% |
| residual `AGENTS.md` | 10 (genre-A sections) + 58 (build commands) | 15.0% |

Herfindahl index of that distribution: **≈0.17**. Expected same-destination collisions between
two randomly chosen concurrent PRs drop by a factor of roughly **six**.

Three further effects, each concrete:

- **The header-line collision mostly disappears.** A PR touching only a skill does not touch
  `AGENTS.md`, so `agents-md-touch-up.yml` never fires and there is no `**Last Updated**` line
  to contend for. The 102 header-block edits become the small subset that genuinely edits the
  residual file.
- **The repo-map obligation collapses.** 114 commits touched `## Repository Structure` because
  new files must appear in the tree. Under a top-level-dirs-only tree, that reason evaporates.
- **73% of edits stay single-file.** From [§1.2](#12-the-churn-is-concentrated-in-the-same-place-and-it-is-single-domain),
  164 of 225 `## Key Files` commits touch exactly one domain. The split does not turn one edit
  into many for the common case; it turns one *shared* edit into one *private* one.

### 10.3 Where new lore goes, and what stops the destination growing

**Destination rule (proposed, and it must be written into `## Conventions`):**

> Post-mortem detail about a component goes in that component's skill body, under
> `## Failure classes`. If the component has no skill, it goes in `docs/REFERENCE.md`. It does
> **not** go in `AGENTS.md` unless it changes an agent-behaviour rule.

That rule alone is worth nothing — it is exactly the kind of convention that produced the
current file. What stops the skills becoming eleven small monoliths is three mechanical gates
([§15](#15-guardrail-inventory)):

1. **Per-file ceiling** — 16,000 chars per `SKILL.md`, hard fail. There is no "just this once".
2. **Corpus ceiling** — Σ all `SKILL.md` ≤ 110,000 chars, hard fail. Growth in one skill must
   be paid for by pruning another. This is the invariant [§8](#8-the-recurring-cost-trap-quantified)
   depends on.
3. **Per-PR growth budget** — a PR may add at most **1,500 chars** net across the skill corpus
   without an `Allow-Skill-Growth: <skill>` commit trailer. This deliberately reuses the repo's
   own `Allow-*` trailer idiom (`Allow-Archive-Edit:` at `AGENTS.md:447`; `Allow-Symbol-Loss:`
   / `Allow-Docs-Rewrite:` at `docs/REFERENCE.md:822-829`), so it needs no new concept — only a
   new predicate.

**Honest statement of what this does and does not fix.** Gate 3 is the only one that addresses
the *rate*; gates 1 and 2 address the *level*. A determined stream of sessions can still fill
110,000 chars and then start trading, and trading requires judgement no gate supplies. This
proposal makes unbounded growth impossible and makes bounded growth a visible, reviewed
transaction. It does not make the judgement for anyone.

---

## 11. The nine-repo ecosystem

### 11.1 The starvation arithmetic

`util/install_agents.bash:99-104` symlinks **every** directory under `.claude/skills/` into
`~/.claude/skills/`, so a mirrored skill is visible from every repo:

```bash
for d in "$SRC_SKILLS"/*/; do
    [[ -d "$d" ]] || continue
    link_one "${d%/}" "${TARGET}/skills/$(basename "$d")"
done
```

If reference skills were mirrored and the pattern were adopted fleet-wide, the listing cost
would be roughly **9 repos × 11 skills × 350 chars ≈ 34,650 chars against an 8,000-char
budget — 4.3× over**. Per [§3.2](#32-verified-an-over-budget-skill-loses-its-description-entirely-not-gradually)
the solver would then reduce most entries to name-only, and juniper-ml's own skills would be
starved by canopy's. **A naive fleet rollout destroys its own discovery.**

### 11.2 The rule

**Reference skills are never mirrored. Procedural skills are.**

- Reference skills answer "how does *this repo's* component work" and are only useful inside
  the repo, where `.claude/skills/` already provides them.
- Procedural skills (`template-agent`, `service-smoke`, `ui-test-author`) are fleet-wide
  procedures and are exactly what the mirror exists for.

Concrete change to [`util/install_agents.bash`](../util/install_agents.bash): honour an
`x-juniper-mirror: false` frontmatter key (skip the link), defaulting to mirror-on so existing
behaviour is unchanged. Approximately 6 lines, covered by the existing
`tests/test_install_agents.py` harness pattern.

Steady-state listing per repo: that repo's ~11 reference skills (≈3,850 chars) plus the 3
mirrored procedural skills (1,403) = **≈5,250 chars against 8,000**. Constant in the number of
repos, which is the property that matters.

### 11.3 Portability

Doc 1 §7 asks for portability across all nine repos, noting `tests/test_agents_md_header_schema.py`
is deliberately self-locating and droppable into any repo's `tests/`. Every gate proposed in
[§15](#15-guardrail-inventory) follows that pattern: repo-root discovery by walking up for
`.github/workflows/`, exactly as
[`tests/test_agents_frontmatter.py:27-31`](../tests/test_agents_frontmatter.py) already does.
The *inventory* is per-repo (canopy's domains are not ml's); the *contract* is fleet-wide.

Note the current fleet baseline: only juniper-ml has a `.claude/skills/` directory at all, so
there is no incumbent to migrate and no cross-repo name collision today.

### 11.4 The budget hazard nobody in this repo controls

Per [§3.4](#34-a-fleet-risk-outside-the-repos-control), claude.ai-synced skills land in
`~/.claude/skills/synced`, are available in every session, and are opt-**out** only. They
consume the same 8,000-char budget. The mitigation, if the listing ever starves, is a settings
change (`skillListingBudgetFraction`, or `syncClaudeAiSkills: false`) — not a repo change. The
suite doctor should report the observed listing size so the condition is visible before it
matters.

---

## 12. Load-bearing design elements — strengths, weaknesses, risks, guardrails

### 12.1 D1 — Skills as the primary carrier of genre-B content

**Strengths.** The only mechanism doc 2 §9 ranks first for deferred loading, and the only one
whose saving survives scrutiny: `@`-imports save nothing (doc 2 §3), and per-subdirectory
`CLAUDE.md` (doc 2 §4c) cannot help a repo whose content is about `util/` and `tests/` files
that a session reads constantly. Quantified: **−87.9% resident, −71.5% in the realistic
3-skill session** ([§8](#8-the-recurring-cost-trap-quantified)). Doc 2 §4a's authoring guidance
names this exact case — *"when a section of CLAUDE.md has grown into a procedure rather than a
fact"*.

**Weaknesses.** Inherent, not fixable by effort:

- **Lazy means conditional.** Resident prose is read once per session with certainty; a skill
  body is read only if the model decides to invoke it. Trading certainty for tokens is the
  whole bet, and it is a real trade.
- **Skills are weaker than prose, which is already weaker than enforcement.** Doc 2 §6:
  CLAUDE.md is a user message with "no guarantee of strict compliance". A skill adds an
  invocation decision *before* that.
- **The corpus does not shrink by being relocated.** The −31% in [§5](#5-the-skill-inventory)
  comes from de-duplicating `docs/REFERENCE.md`, which any proposal could do.

**Risks.** *Concrete scenario:* a session edits `util/release_train/ceremony.py` to "simplify"
the publish-run monitor. It never invokes `juniper-ml-release-train`, so it never sees the
`select_publish_run` invariant now at `AGENTS.md:453-457` — that a Release fires every
`release: published` publisher and the tag-guarded ones finish `completed/skipped` sharing the
real run's `displayTitle` and `headBranch`. It reintroduces the 2026-08-09/10 bug where the
monitor burns its whole timeout per package.

**Guardrails.**

- The regression is caught by `SelectPublishRunTest` at
  [`tests/test_release_train_ceremony.py:719`](../tests/test_release_train_ceremony.py), which
  is wired into `ci.yml`. **The prose was never the enforcement.** Its value is saving a
  round-trip, not preventing the defect. This generalizes: the repo ships **89 test modules**
  for **65 non-ad-hoc `util/` scripts**, and 51 of the 154 `## Key Files` sub-bullets name
  their own pin explicitly.
- New gate `tests/test_skills_frontmatter.py`, modelled directly on
  [`tests/test_agents_frontmatter.py`](../tests/test_agents_frontmatter.py): every
  `.claude/skills/*/SKILL.md` has a `name` matching its directory, a description obeying
  [§6.3](#63-description-authoring-rules-lint-enforced), a body opening with `## Invariants`,
  and a size within ceiling.
- New gate `tests/test_skill_index_drift.py`: every skill appears as a row in `AGENTS.md`'s
  `## Skill Index`, and every row names a real skill. This is the same class as
  [`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) and the same
  class as `tests/test_agent_suite_path_drift.py`.

---

### 12.2 D2 — Eleven skills at domain granularity

**Strengths.** Derived from four independent constraints that intersect at [7, 11]
([§4](#4-granularity--derived-not-asserted)), not chosen by taste. The boundaries are
*measured* co-edit clusters, so 73% of edits remain single-file. Bodies land at 5,000-15,000
chars — comfortably under the 20,000-char compaction ceiling and the 500-line guidance.

**Weaknesses.**

- **Domains are drawn from six weeks of churn.** A domain that has been quiet since June is
  under-weighted; a domain that appears in September has no home and will be jammed into the
  nearest skill.
- **Some content is genuinely cross-domain.** `wait_for_checks.py` is CI *and* fleet triage;
  `assert_release_tag.bash` is publish-path *and* release-train. Wherever it is filed, someone
  looks in the other place.
- **11 destinations is 11 places to look** for a human reading the repo without a model.

**Risks.** *Concrete scenario:* a session works on `util/experiments/run_suite.py`'s budget
forwarding, which touches both `juniper-ml-experiments` (the suite driver) and
`juniper-ml-ci-workflows` (the campaign's CI surface). It invokes one, gets half the picture,
and re-derives the other half incorrectly — the exact `max_epochs`-without-`output_epochs`
class where a config looks like it asks for one thing and the service does another.

**Guardrails.**

- **Disjoint path globs**, lint-enforced: `tests/test_skills_frontmatter.py` asserts no two
  skill descriptions claim overlapping `Use before editing` globs. A genuine overlap forces an
  explicit cross-reference rather than a silent split.
- **Mandatory `## See also` footer** in every body, naming sibling skills by exact name — so a
  model that lands in one is one step from the other.
- **Quarterly re-derivation.** Re-run the churn attribution
  ([Appendix A](#appendix-a--reproducing-every-number-in-this-document)); if a domain's share
  has moved by more than 2×, revisit the boundary. This is a review ritual, not a gate, and it
  will be skipped sometimes. Stated as such.

---

### 12.3 D3 — Model-invocable reference skills (a category new to this repo)

**Strengths.** Invocation without user action is what makes progressive disclosure automatic
rather than a menu. [§3.1](#31-verified-skills-are-model-invocable-by-default) verifies from
the shipped binary that omitting `disable-model-invocation` yields exactly this.

**Weaknesses.**

- **Zero in-repo precedent.** All three existing skills are user-only and three lints assert
  it. This proposal introduces a category with no operational history here.
- **Invocation is a model judgement**, so it has a false-negative rate nobody has measured for
  this repo's descriptions. Doc 2 §8 note 6 records that no published Anthropic benchmark
  measures adherence as a function of memory size either; there is no external number to
  borrow.
- **Auto-invocation can also fire when it should not**, spending 9,182 chars on a skill the
  task did not need.

**Risks.** *Concrete scenario, and it is the one that sinks the proposal:* the binary reading
in [§3.1](#31-verified-skills-are-model-invocable-by-default) is correct about the default but
some other gate — a settings key, a permission rule (the binary contains a
`"Skill execution blocked by permission rules"` deny path), or a plan-mode restriction —
suppresses model invocation in this environment. Then 145,675 bytes of hard-won lore become
invisible to every session that does not ask for it by name.

**Guardrails.**

- **[Phase 0](#phase-0--settle-the-thesis-half-a-day-revertible-by-deletion) settles it
  empirically before anything is moved.** One throwaway model-invocable skill, a task that
  should trigger it, and a check for whether the body appears. Half a day, revertible by
  deleting one directory.
- **The resident `## Skill Index`** ([§7.2](#72-the-residual-budget)) makes every skill
  reachable by explicit invocation regardless. Auto-invocation is an optimisation over a
  working manual path, not a single point of failure.
- **Phase ordering** ([§14](#14-migration-path)) moves the *lowest*-stakes domain first
  (`juniper-ml-repo-map`, which is derivable content) so the first real-world test of
  auto-invocation risks nothing.
- **Suite doctor extension.** [`util/agent_suite_doctor.py:105`](../util/agent_suite_doctor.py)
  currently hardcodes `.claude/skills/template-agent/SKILL.md`. Extend it to enumerate all
  skills and report each one's invocation mode, so a stray
  `disable-model-invocation: true` on a reference skill is a `FAIL`, not a mystery.

---

### 12.4 D4 — The 200-line residual `AGENTS.md`

**Strengths.** Hits doc 2 §5's stated target exactly. Retains **all 16 genre-A mandatory
directives** ([§1.3](#13-the-mandatory-language-is-overwhelmingly-not-agent-behaviour)) —
nothing that governs agent behaviour becomes lazy. Passes all four existing gates unmodified
([§7.3](#73-the-gate-minimal-tree-is-a-verified-constraint-not-a-guess)). Reduces resident
context by **−87.9%**, and the always-on aggregate from 25.6% to 7.0% of a 200k window
([§13](#13-beforeafter-byte-budget)).

**Weaknesses.**

- **200 lines is a budget, not a natural size.** Reaching it required trimming `## Worktree
  Procedures` (92 → 17) and `## Thread Handoff` (74 → 16) to rules-only, relying on the two
  procedure notes to hold the how-to. If a session ignores the pointer, the procedure is one
  file-read away instead of resident — a real, if small, regression for two genre-A subjects.
- **The line target is soft in a way the byte target is not.** A future session can honour "200
  lines" with 200 very long lines. The gate must bound both.

**Risks.** *Concrete scenario:* six months on, the residual file is 400 lines because "this one
really is agent behaviour" happened forty times. Nothing about Skills prevents that; only the
gate does — and the current file's history is precisely that four gates protected structure and
currency while none protected size (doc 1 §6).

**Guardrails.**

- New gate `tests/test_agents_md_size_budget.py`: **hard fail** above 260 lines **or** 22,000
  chars (30% and 45% headroom over the 200/15,157 target); **warn** above 220 lines. Written
  self-locating so it drops into all nine repos, with the ceiling read from a constant at the
  top of the file so raising it is a visible, reviewed diff.
- Wire it into [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) beside the four
  existing `test_agents_md_*.py` invocations (`ci.yml:611-636`), which is where the repo
  already runs this exact class of check.
- The `## Conventions` destination rule ([§10.3](#103-where-new-lore-goes-and-what-stops-the-destination-growing))
  tells an author where to put the content the gate just refused.

---

### 12.5 D5 — Description and name design for discovery

**Strengths.** Grounded in verified mechanism rather than intuition: front-loading is correct
because truncation is `slice(0, cap-1)`; repo-prefixed names are correct because degradation is
to name-only; `when_to_use` is omitted because it shares the same cap
([§3.2](#32-verified-an-over-budget-skill-loses-its-description-entirely-not-gradually),
[§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters)). Total
listing 5,270 of 8,000 chars, 34% headroom.

**Weaknesses.**

- **The `Use before editing <glob>` convention assumes the model knows what it is about to
  edit.** For exploratory work ("why is main red?") the path is the *output* of the
  investigation, not its input, so path-based routing is weakest exactly when the session is
  most lost.
- **Descriptions are prose competing with every other description.** There is no relevance
  scoring the repo can influence beyond word choice.
- **The priority score `t()` in the budget solver is not decompiled.** Doc 2 states the
  ordering is by least-invoked; this proposal does not verify the metric. If it were something
  else — alphabetical, or by registration order — a `juniper-ml-` prefix could systematically
  disadvantage all eleven at once.

**Risks.** *Concrete scenario:* the owner enables three claude.ai skills. The listing exceeds
8,000 chars. Because all eleven reference skills share a prefix and (plausibly) a low
invocation count, they are the block that loses descriptions together, and every session
degrades simultaneously with no error anywhere.

**Guardrails.**

- **Budget headroom as policy, not luck:** `tests/test_skills_frontmatter.py` computes the
  listing exactly as [§6.1](#61-listing-cost-computed) does and fails above **6,400 chars**
  (80% of budget), leaving 20% for synced and procedural skills.
- **Names route alone.** Every reference skill name must contain both the repo token and a
  domain noun — lint-enforced — so the name-only mode remains usable.
- **The resident `## Skill Index`** is the floor: even a fully starved listing leaves the model
  a resident table naming all fourteen.
- **Escape hatch, documented in `docs/REFERENCE.md`:** raise `skillListingBudgetFraction` or
  set `SLASH_COMMAND_TOOL_CHAR_BUDGET`. Both are verified settings
  ([§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters)).

---

### 12.6 D6 — The corpus cap invariant

**Strengths.** It is what makes [§8](#8-the-recurring-cost-trap-quantified)'s claim structural:
worst case ≤ baseline, by arithmetic rather than optimism. It is also the answer to "what stops
the skills becoming the next 170K" — the honest answer being a number in CI, not a convention.

**Weaknesses.**

- **A cap creates pressure, and pressure finds an outlet.** When the corpus is full, the path
  of least resistance is `docs/REFERENCE.md` (uncapped, 162,231 chars) or a new `notes/`
  document. The bytes are then lazy — which is the goal — but the *placement* discipline
  erodes, and `docs/REFERENCE.md` is already 4× the size of the residual file.
- **110,000 chars is a judgement call**, derived from the current corpus plus ~9% headroom. It
  is defensible, not derived.

**Risks.** *Concrete scenario:* two concurrent sessions each add 1,400 chars — each under the
per-PR budget, each green. The corpus crosses 110,000 on the second merge and **main goes red
for a PR that was individually compliant**. That is the same self-perpetuating red-main class
the repo has already lived through with the sequence-safety screens.

**Guardrails.**

- **Warn band before the wall:** the gate warns from 100,000 and fails at 110,000, so the
  10,000-char band gives roughly seven PRs of notice.
- **Fail the *corpus* check on `pull_request` only**, mirroring how
  `release-train-archive-guard` is PR-scoped in `ci.yml`; on `push: main` it warns. A shared
  budget must not be able to red main for a PR that was green.
- **`Allow-Skill-Growth:` trailer** for a deliberate, reviewed increase, following the repo's
  `Allow-*` idiom exactly.

---

### 12.7 D7 — `reference/*.md` sub-files as a third tier

**Strengths.** Keeps the two largest bodies (release-train 14,000, experiments 15,000) under
the compaction ceiling while retaining their long tails (the HALT catalog, the driver exit
matrix). Doc 2 §4a records the official guidance: *"keep `SKILL.md` under 500 lines; move
detail to separate files."*

**Weaknesses.**

- **Doc 2 does not verify sub-file loading semantics.** It records the guidance to move detail
  out; it does not state that sub-files are excluded from the injected body. **This is an
  inference, and it is flagged as one.**
- Reaching a sub-file costs an extra tool call, so it is meaningfully less likely to be read.
- Sub-files are outside the 16,000-char per-`SKILL.md` lint unless the lint is written to cover
  the whole directory.

**Risks.** *Concrete scenario:* if sub-files *are* loaded eagerly with the body, then
`juniper-ml-experiments` costs 20,000 chars on invocation, not 15,000; the corpus becomes
112,000 and the worst case in [§8](#8-the-recurring-cost-trap-quantified) turns from −3.7% into
roughly break-even-or-worse.

**What breaks if the inference is wrong:** not the design — the *cap placement*. The fix is
one line in the lint: bound `du -c` of the whole skill directory rather than `SKILL.md` alone,
and re-plan the two large skills as three. Stated explicitly so a reviewer can price it.

**Guardrails.**

- **Phase 0 measures it** alongside the invocation test: invoke a skill with a large sub-file
  and observe whether context grows by body-only or body-plus-sub-file.
- **The lint bounds the directory, not the file**, from day one — 16,000 chars for `SKILL.md`
  and 24,000 for the directory. That is correct under either answer, so the gate does not
  depend on the unverified fact.

---

### 12.8 D8 — path-scoped rules for the security invariants (secondary)

This is the one place a mechanism other than Skills carries load, and it is deliberate.

Five of `## Shared Service-Core Contracts`' mandatory lines are security invariants (`AGENTS.md:168-171`,
`:175`): the CR-024 body limit, auth-before-rate-limit, 429 header passthrough, control-WS log
sanitizing. These are genre B — they only bind when editing `juniper-service-core/` — but the
cost of missing one is a security regression, not a rework.

Doc 2 §4b: rules **with** `paths:` "trigger when Claude reads files matching the pattern, not
on every tool use", and rules **without** `paths:` load at launch (no saving).

**Strengths.** Trigger is a *file read*, not a model decision — so it does not share D3's
false-negative risk. Cost is zero until a `juniper-service-core/**` file is read. Small: ~3,512
chars for the whole set.

**Weaknesses.** A second mechanism to maintain, lint, and explain. Doc 2 gives no budget
guidance beyond 1,000 expanded patterns / 4 MiB per rule. And it does not help a session that
*writes* a new file without reading an existing one first.

**Risks.** `.claude/rules/` is **not** in the `.gitignore` re-include block: `.gitignore:176-181`
negates only `.claude/skills/` and `.claude/agents/`. A rules directory added without that
change is silently untracked, works locally, and does not exist for anyone else — a
particularly nasty version of "works on my machine" for a security control.

**Guardrails.**

- Extend the `.gitignore` negation to `.claude/rules/**` **in the same PR** that adds the
  directory.
- `tests/test_skills_frontmatter.py` gains a companion assertion: every file under
  `.claude/rules/` is tracked by `git ls-files` and declares a non-empty `paths:` (a rule
  without `paths:` is eager and silently reintroduces the problem this proposal solves).
- The service-core invariants remain **additionally** present in `juniper-ml-shared-packages`,
  so the rule is a safety net rather than the sole copy.

---

### 12.9 D9 — Not mirroring reference skills to `~/.claude`

**Strengths.** Keeps the listing constant in the number of repos
([§11.2](#112-the-rule)) — the property that makes the pattern survive fleet adoption. Costs
~6 lines in [`util/install_agents.bash`](../util/install_agents.bash).

**Weaknesses.** A session in `juniper-canopy` that legitimately needs juniper-ml's release-train
lore (cross-repo release work is real and frequent) does not see the skill. It must read the
file by path — which works, because the path is stable and documented, but it is a manual step.

**Risks.** *Concrete scenario:* a cross-repo release ceremony run from a canopy worktree misses
the archive-PR structural rules and opens a PR that fails `release-train-archive-guard`. Cost:
one failed check and a rework, not a data loss.

**Guardrails.**

- The parent `Juniper/CLAUDE.md` (11,016 chars, fully additive per doc 2 §7 — it is **not**
  overridden by the repo file) is the correct home for a two-line cross-repo pointer: "for
  juniper-ml component internals, read `juniper-ml/.claude/skills/juniper-ml-<domain>/SKILL.md`".
  Two lines of always-on cost across nine repos.
- `util/agent_suite_doctor.py` reports mirror state per skill, so "why can't I see it" has a
  one-command answer.

---

### 12.10 D10 — Retiring the Key Files section for a Skill Index

**Strengths.** Removes 99,304 chars — 59% of the file — and with it 154 of 156 accretion
sub-bullets and 110 of 160 mandatory-language lines. The 18-line index preserves *navigability*
at 1.7% of the cost.

**Weaknesses.** `## Key Files` is genuinely useful to a **human** skimming the repo, and an
18-row table is not the same document. That reader is served by `docs/REFERENCE.md` and by
`juniper-ml-repo-map` — both a click away, neither as immediate.

**Risks.** *Concrete scenario, and it is the top migration risk:* the PR that deletes 915 lines
from `AGENTS.md` trips `juniper-docs-additions-check`, which fails on a deleted heading or ≥5
consecutive deleted lines across `AGENTS.md` + `docs/**` + `notes/**`. As of **HEAD (`e209b74`,
2026-08-18, ml#1166)** the `Sequence Safety` check (`.github/workflows/ci.yml:804-805`) is a
**REQUIRED** status check on all nine repos — so the migration PR is *blocked*, not merely
warned. The post-merge screen in
[`.github/workflows/main-verify.yml:196`](../.github/workflows/main-verify.yml) runs without
`|| true` and turns **main** red.

**Guardrails.**

- **Every migration PR carries `Allow-Docs-Rewrite: AGENTS.md` in its commit message, and the
  trailer must survive into the squash commit** — the trailer parser reads `BASE..HEAD`, and a
  squash that drops the body drops the waiver. This is the documented escape hatch
  (`docs/REFERENCE.md:823`), and `Allow-Docs-Rewrite: *` is explicitly accepted
  (`docs/REFERENCE.md:829`), unlike the symbol-loss wildcard.
- **Waiving is not sufficient — prove nothing was lost.** The repo's own 2026-08-18 lesson from
  ml#1165 is that a screen finding treated as a reflow was **real content loss (116 tokens)**.
  Every migration PR must therefore attach a **token-level diff** showing that every token
  removed from `AGENTS.md` appears in a named skill body or in `docs/REFERENCE.md`. Restore,
  do not waive, anything that does not.
- **Per-phase, not big-bang** ([§14](#14-migration-path)): each phase deletes one domain, so
  each token-diff is reviewable by a human in minutes rather than being a 915-line wall.

---

## 13. Before/after byte budget

### 13.1 `AGENTS.md` itself (character basis)

| | Lines | Chars | Tokens (÷4) |
|---|-------|-------|-------------|
| Before | 1,115 | 168,317 | 42,079 |
| After — residual file | 200 | 15,157 | 3,789 |
| After — skill listing (always resident) | — | 5,270 | 1,318 |
| **After — total always-on** | **200** | **20,427** | **5,107** |
| **Delta** | **−915** | **−147,890** | **−36,972** |
| **Reduction** | −82.1% | **−87.9%** | −87.9% |

### 13.2 Whole-session always-on context (doc 1 §1, byte basis)

| File | Before (bytes) | After (bytes) |
|------|----------------|---------------|
| `~/.claude/CLAUDE.md` | 3,349 | 3,349 |
| `Juniper/CLAUDE.md` (additive, doc 2 §7) | 11,016 | 11,016 + ~150 cross-repo pointer |
| `juniper-ml/CLAUDE.md` → `AGENTS.md` | **170,137** | **15,324** |
| Skill listing | 0 | 5,270 |
| `MEMORY.md` (separate subsystem, [§17](#17-the-memorymd-problem)) | 20,388 | 20,388 |
| **Total** | **204,890** | **55,497** |
| **Tokens** | **≈51,222** | **≈13,874** |
| **% of a 200k window consumed before the first prompt** | **25.6%** | **7.0%** |

### 13.3 Where the 168,317 characters go

| Destination | Chars | Note |
|-------------|-------|------|
| Stays resident in `AGENTS.md` | 15,157 | 9.0% |
| Relocated to 11 skill bodies | 101,000 | lazy; median session pays 0-2 of these |
| Relocated to `reference/` sub-files | 11,000 | third tier |
| **Deleted as duplicated with `docs/REFERENCE.md`** | **≈33,825** | see below |
| **Deleted as derivable** | **≈7,335** | the 54-line unittest list (3,119) + trimmed procedure blocks |
| **Total** | **168,317** | |

The 33,825 deleted-as-duplicated figure is the residue of relocating 145,675 bytes of source
into a 112,000-char corpus. It is the least certain number in this document, because it is a
*plan* to compress rather than a *measurement* of compression — and it will only be confirmed
phase by phase. The evidence that it is achievable is [§1.4](#14-some-lore-is-duplicated-four-ways):
for `reap_pytest_orphans` specifically, essentially 100% of the `AGENTS.md` content is already
in `docs/REFERENCE.md`. **If it turns out only half is achievable, the corpus becomes ~129,000
chars and the worst case in [§8](#8-the-recurring-cost-trap-quantified) becomes a small loss
rather than a small win** — the median-session saving is unaffected, but the structural
guarantee weakens to "no worse than break-even in practice". That is the number to watch during
migration, and it is why the corpus cap is a gate rather than a target.

---

## 14. Migration path

Nine phases. Each is one PR, independently shippable, independently revertible, and leaves the
repo in a working state.

### Phase 0 — settle the thesis (half a day, revertible by deletion)

Create one throwaway skill `.claude/skills/juniper-ml-probe/SKILL.md` with
`disable-model-invocation` **omitted**, a distinctive body, and a large
`reference/big.md` sub-file. Then in a fresh session:

1. Ask a question its description matches. **Did the body appear without being asked for?**
2. Measure context growth. **Was it body-only, or body-plus-sub-file?**
3. Run `/context` (or equivalent) and record the observed listing size.

Record all three in `docs/REFERENCE.md`. **If (1) is negative, stop — Proposal A does not
work as designed** and the owner should choose a different proposal. This is the cheapest
possible test of the most expensive assumption. Delete the probe skill afterwards.

### Phase 1 — the gates, before any content moves

Add, wired into `ci.yml` beside `ci.yml:611-636`:

- `tests/test_skills_frontmatter.py` (frontmatter, description rules, per-file and per-directory
  size, disjoint globs, listing-budget total)
- `tests/test_skill_index_drift.py` (index ↔ skills bidirectional)
- `tests/test_agents_md_size_budget.py` (initially warn-only, ceiling set **above** the current
  file so it is green on day one)

No content moves. Reverting is deleting three files.

### Phase 2 — `juniper-ml-repo-map` (lowest stakes first)

Move `## Repository Structure` (20,469 chars) and the `## Key Files` preamble subsections. Leave
the gate-minimal 26-line tree ([§7.3](#73-the-gate-minimal-tree-is-a-verified-constraint-not-a-guess)).
Chosen first because it is the most derivable content in the file, so a discovery failure costs
nothing — and it removes the largest *co-edit obligation* (114 commits) immediately.

Carries `Allow-Docs-Rewrite: AGENTS.md` plus the token-diff proof
([§12.10](#1210-d10--retiring-the-key-files-section-for-a-skill-index)).

### Phase 3 — `juniper-ml-release-train` + `juniper-ml-publish-path`

The highest-churn domain (40.2% of `## Key Files` additions), so the concurrency benefit lands
early. Two skills, one PR — they were split from one body and their cross-references must land
together.

### Phase 4 — `juniper-ml-host-orchestration` + `juniper-ml-worktree-ops`

Second-highest churn (25.0%). `## Worktree Procedures`' command blocks move here; the rules
stay.

### Phase 5 — `juniper-ml-experiments`

15.6% of churn, and the largest single body (15,000 + a 5,000-char sub-file). By this phase
Phase 0's sub-file measurement has been confirmed in practice twice.

### Phase 6 — `juniper-ml-env-drift`, `-agent-suite`, `-fleet-triage`

Three mid-size domains; may be one PR or three. The `-agent-suite` skill is self-referential
(it documents the skill lints), so it lands after the lints have been in CI for several weeks.

### Phase 7 — `juniper-ml-ci-workflows` + `juniper-ml-shared-packages`

`## CI/CD Pipelines` and the two shared-package H2 sections. Adds `.claude/rules/service-core.md`
with `paths: juniper-service-core/**`, **and** the `.gitignore` negation for `.claude/rules/**`
in the same PR ([§12.8](#128-d8--path-scoped-rules-for-the-security-invariants-secondary)).

### Phase 8 — residual trim and gate tightening

Condense `## Build & Package Commands`, `## Pre-commit Hooks`, `## Ecosystem Context`,
`## Pull Request Conventions`, `## Worktree Procedures`, `## Thread Handoff` to the
[§7.2](#72-the-residual-budget) budget. Add the `## Skill Index`. Add the destination rule to
`## Conventions`. **Then** lower `tests/test_agents_md_size_budget.py` to its real ceiling
(260 lines / 22,000 chars) and switch it from warn to fail.

### Phase 9 — mirror scoping and fleet handoff

Add `x-juniper-mirror` support to [`util/install_agents.bash`](../util/install_agents.bash);
extend [`util/agent_suite_doctor.py`](../util/agent_suite_doctor.py) to enumerate all skills,
report invocation mode and mirror state, and report the computed listing size. Add the two-line
cross-repo pointer to the parent `Juniper/CLAUDE.md`. Write the pattern up for canopy (94,373
chars) and cascor (70,118 chars) — the two siblings doc 1 §7 identifies as on the same
trajectory.

### Revert story

Every phase is `git revert` of one PR. Because each phase moves content into a *new* file and
deletes from `AGENTS.md` in the same commit, a revert restores the exact prior bytes. No phase
depends on a later phase; Phases 2-7 can stop at any point and leave a smaller-but-coherent
`AGENTS.md`.

---

## 15. Guardrail inventory

Consolidated, so a reviewer can see the whole enforcement surface at once. Every one follows an
existing repo pattern; none invents a new mechanism.

| Gate | Type | Detects | Modelled on |
|------|------|---------|-------------|
| `tests/test_skills_frontmatter.py` | new unittest | frontmatter shape; `name` == directory; description 160-400 chars, keyword-first, ends in `Use before editing`; `## Invariants` first section; **`SKILL.md` ≤16,000 chars, directory ≤24,000**; **listing total ≤6,400 chars**; disjoint path globs; invocation mode correct per class | [`tests/test_agents_frontmatter.py`](../tests/test_agents_frontmatter.py) |
| `tests/test_skill_index_drift.py` | new unittest | every skill has an `AGENTS.md` `## Skill Index` row and vice versa | [`tests/test_agents_md_tree_drift.py`](../tests/test_agents_md_tree_drift.py) |
| `tests/test_agents_md_size_budget.py` | new unittest | residual `AGENTS.md` >260 lines or >22,000 chars (fail); >220 lines (warn). Self-locating, fleet-portable | [`tests/test_agents_md_header_schema.py`](../tests/test_agents_md_header_schema.py) |
| skill-corpus budget | new `ci.yml` step, **PR-scoped** | Σ all `SKILL.md` >110,000 chars (fail on PR, warn on push); >100,000 (warn) | `release-train-archive-guard` PR-scoping in `ci.yml` |
| `Allow-Skill-Growth:` trailer | commit trailer | waives the per-PR 1,500-char corpus growth budget | `Allow-Archive-Edit:` (`AGENTS.md:447`), `Allow-Docs-Rewrite:` (`docs/REFERENCE.md:823`) |
| `.claude/rules/` tracking assertion | added to `test_skills_frontmatter.py` | a rules file untracked by git, or lacking `paths:` | `tests/test_agent_suite_path_drift.py` |
| `util/agent_suite_doctor.py` extension | existing utility | enumerates every skill; reports invocation mode, mirror state, computed listing size | it already checks the suite; `:105` currently hardcodes one skill |
| `util/install_agents.bash` `x-juniper-mirror` | existing utility | prevents reference skills reaching `~/.claude` | its own `link_one` idempotence contract |

Four things worth saying plainly about this table:

- **`.claude/**` is excluded from every pre-commit hook except markdownlint**
  (`.pre-commit-config.yaml:35-56` does not list it; the markdownlint exclude at `:226` covers
  `notes/`, `docs/`, `prompts/` but not `.claude/`). So these unittests are the *only* gate on
  the skill surface — the same situation the three existing skill lints were written for, and
  the same reason `util/` is covered by unittests rather than linters.
- **Skill bodies are markdownlint-checked**, since `.claude/` is not excluded. Bodies must obey
  `.markdownlint.yaml` (512-char lines).
- **Every gate is structural.** None of them can verify that a skill body is *correct* — only
  that it exists, fits, and is discoverable. Correctness remains the reviewer's job, as it is
  today.
- **New skills are tracked automatically.** `.gitignore:176-181` re-includes `.claude/skills/**`,
  so no `.gitignore` change is needed for skills (only for `.claude/rules/`).

---

## 16. What this proposal does NOT solve

Stated plainly, because a proposal that claims to solve everything should not be trusted.

1. **It does not enforce anything.** Doc 2 §6 is unambiguous: memory content is advisory. This
   proposal moves 139 advisory `MUST` lines from one advisory location to another, lazier
   advisory location. Directives that must hold deterministically need a `PreToolUse` hook or a
   CI gate, and this proposal adds none for the 16 genre-A directives it keeps resident. **The
   `/tmp/` prohibition, the Release-not-bare-tag convention, and the worktree-location rule are
   exactly as unenforced after this change as before it.**
2. **It does not settle `docs/REFERENCE.md`'s growth.** At 162,231 chars it is 10× the residual
   `AGENTS.md`, uncapped, and this proposal actively directs content toward it. It is lazy
   (read on demand), so it costs nothing per session — but the circular-authority problem in
   [§1.4](#14-some-lore-is-duplicated-four-ways) is only half fixed: `AGENTS.md` stops being an
   authority, while `docs/REFERENCE.md` and the skill bodies now both claim the same subjects.
   Assigning that split — operator surface versus agent invariants — is a convention, not a
   gate.
3. **It does not reduce the parent `Juniper/CLAUDE.md`** (11,016 chars, fully additive per doc 2
   §7) or the user-global file (3,349). Doc 2 §4d names `claudeMdExcludes` as the documented
   answer for an over-broad ancestor; this proposal does not use it, and adds ~150 chars to the
   parent file for the cross-repo pointer.
4. **It does not help a session that never invokes a skill.** Whatever the false-negative rate
   of auto-invocation is, this proposal converts that rate directly into a
   "worked-without-the-lore" rate. Nobody has measured it for this repo.
5. **It does not fix the underlying incentive.** Sessions append post-mortem detail because
   doing so is how hard-won knowledge survives a thread boundary. This proposal gives that
   impulse a better-shaped destination and a budget. It does not reduce the volume of knowledge
   being produced, and the fleet trend in doc 1 §7 will continue.
6. **It does not address canopy (94,373) or cascor (70,118)** except by producing a pattern.
   Phase 9 is a handoff, not a rollout.
7. **It does not meaningfully help `MEMORY.md`** — see [§17](#17-the-memorymd-problem).

---

## 17. The `MEMORY.md` problem

Doc 2 §2 establishes this as *separate and harder*: the limit is real, hard, and silent.

| Measure | Value | Limit | Headroom |
|---------|-------|-------|----------|
| Lines | 139 | 200 | 61 |
| Bytes | 20,388 | ~25,600 | ~5,212 |

Confirmed on this host at authoring time: 139 lines / 20,388 bytes, with **154 files** in
`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`.

At the observed density of 146.7 chars/line, 200 lines would be 29,340 bytes — above the ~25,600
byte limit. **The byte axis binds first, at roughly 35 more entries.**

**Does Proposal A help? Barely, and honesty requires saying so up front.**

- **Direct effect: ~3%.** Five index entries are prefixed `reference_` — the trap/reference
  genre this proposal consolidates into skills (`reference_vacuous_pass_check_class`,
  `reference_sequence_safety_local_repro`, `reference_ci_wait_for_checks`,
  `reference_github_pr_ci_trigger_traps`, `reference_experiment_evidence_capture`). Together
  they are ≈880 chars. If their content lived in the corresponding skill bodies, those index
  lines could shrink to bare pointers, recovering ≈680 bytes — **13% of the remaining headroom,
  3.3% of the file.** That buys perhaps five more entries. It is not a solution.
- **No effect on the bulk.** The 17 `feedback_*` and ~130 `project_*` entries are session-arc
  narrative — what was decided, what was tried, what was withdrawn. Skills are a *repo* artifact
  scoped to a repo's components; they are not a home for cross-session narrative, and pretending
  otherwise would be exactly the category error this proposal criticises in `AGENTS.md`.
- **One real structural contribution.** [§1.4](#14-some-lore-is-duplicated-four-ways) shows the
  `[skip ci]` orphan class existing in four places simultaneously, one of which is `MEMORY.md`.
  Establishing *one* durable, git-tracked, reviewed home for the "component trap" genre removes
  the reason a session writes that genre into `MEMORY.md` at all — because a memory entry is
  written when there is nowhere better to put it. This lowers the future *rate* of a subset of
  entries. It does not lower today's 20,388 bytes.

**Recommendation, offered without claiming it as this proposal's contribution:** `MEMORY.md`
needs its own remedy — index-line compaction (the index is a pointer list; multi-clause entries
of 300+ chars are the growth mechanism, exactly as sub-bullets are in `AGENTS.md`) plus
migration of settled arcs into topic files with one-line index stubs. That work is orthogonal to
every one of the four proposals and should be planned separately. Deferring it is a decision to
accept silent memory loss in roughly 35 entries' time.

---

## 18. Open questions for the owner

These are decisions, not gaps. Each is marked as belonging to the owner rather than guessed.

1. **Ship Phase 0 before choosing between the four proposals?** It costs half a day and settles
   whether Proposal A is viable at all. Recommended regardless of which proposal is favoured,
   because the answer is useful to any design that touches skills.
2. **Is 200 lines the right residual target, or is 300 more honest?** Reaching 200 required
   trimming `## Worktree Procedures` and `## Thread Handoff` to rules-only. A 300-line target
   would keep both procedures resident at the cost of missing doc 2 §5's stated guideline. This
   is a judgement about how much the two procedure notes are actually read.
3. **Should the 16 genre-A directives get `PreToolUse` hooks?** Doc 2 §6 says that is the only
   way to make them binding. This proposal scopes hooks out — but the `/tmp/` script-placement
   rule in particular is a `Write`-tool predicate that a hook could enforce exactly, and the
   incident that motivated the rule (`AGENTS.md:915`) is a permanent data loss.
4. **Corpus ceiling: 110,000 chars?** Derived from the planned corpus plus ~9%. Raising it
   weakens [§8](#8-the-recurring-cost-trap-quantified)'s guarantee proportionally; lowering it
   forces earlier trading.
5. **Fleet rollout timing.** Phase 9 hands the pattern to canopy and cascor. Doing it
   concurrently with juniper-ml's migration would multiply the sequence-safety waiver surface
   across nine repos at once, which the repo's own recent history argues against.

---

## 19. Verification recommendation

This is a high-stakes design: it proposes deleting 91% of the file that governs every session in
this repo. Before it is treated as ratified:

1. **Run Phase 0.** [§3.1](#31-verified-skills-are-model-invocable-by-default) and
   [§12.7](#127-d7--referencemd-sub-files-as-a-third-tier) rest on one verified binary reading
   and one flagged inference respectively. Both are cheap to settle empirically and expensive to
   get wrong.
2. **Independent cross-validation of the binary readings.** [§3.1](#31-verified-skills-are-model-invocable-by-default),
   [§3.2](#32-verified-an-over-budget-skill-loses-its-description-entirely-not-gradually), and
   [§3.3](#33-verified-from-the-binary-the-listing-budget-is-exactly-8000-characters) are new
   evidence not present in doc 2. A second agent should re-extract them from the same binary and
   confirm, or fold them into doc 2 as verified additions.
3. **Re-derive the churn attribution** ([§1.2](#12-the-churn-is-concentrated-in-the-same-place-and-it-is-single-domain))
   independently. The 73%-single-domain figure is what justifies the granularity, and it comes
   from a heuristic domain classifier
   ([Appendix A](#appendix-a--reproducing-every-number-in-this-document)) whose regex boundaries
   are a judgement.
4. **Sanity-check the 33,825-char de-duplication estimate** ([§13.3](#133-where-the-168317-characters-go))
   against two domains by hand before Phase 3. It is the least certain number here and it is
   what makes the worst case a win rather than a loss.

---

## Appendix A — reproducing every number in this document

All commands are run from the repo root.

```bash
# File size, three ways (bytes / characters / lines)
wc -c -m -l AGENTS.md

# Per-H2 section sizes (character basis; reconciles to wc -m)
awk '/^## / { if (s!="") printf "%7d %5d  %s\n", b, l, s; s=$0; b=0; l=0 }
     { b+=length($0)+1; l++ }
     END { if (s!="") printf "%7d %5d  %s\n", b, l, s }' AGENTS.md

# Accretion signature: nested sub-bullets, and how many are in Key Files
awk '/^## / {s=$0} /^  - / {n++; b+=length($0)+1; if (s ~ /Key Files/) {kn++; kb+=length($0)+1}}
     END {print b" bytes / "n" sub-bullets total; "kb" / "kn" inside Key Files"}' AGENTS.md

# Mandatory-language distribution by section
awk '/^## / {s=substr($0,4)} tolower($0) ~ /\y(must|mandatory|never|prohibited|always|required)\y/ {c[s]++}
     END {for (k in c) printf "%4d  %s\n", c[k], k}' AGENTS.md | sort -rn

# Sub-bullets that name their own CI pin
awk '/^## / {s=$0} s ~ /Key Files/ && /^  - / {n++; if ($0 ~ /[Pp]in|[Gg]ate|tests\/|test_/) m++}
     END {print m" of "n}' AGENTS.md

# Tracked top-level directories (the tree-drift gate's surface)
git ls-tree -d --name-only HEAD | grep -v '^\.'

# Growth curve (doc 1 §2)
bash util/ad-hoc/2026-08-18_agents_md_growth_curve.bash
```

**Churn attribution** ([§1.2](#12-the-churn-is-concentrated-in-the-same-place-and-it-is-single-domain))
was produced by, for each of the 285 commits touching `AGENTS.md` since 2026-06-01: reconstructing
that commit's `AGENTS.md`, building a line-number → H2-section map from it, then walking
`git diff -U0 <sha>^ <sha> -- AGENTS.md` and attributing each `+` line to the section at its
post-image line number. Domain attribution repeats the procedure with a line-number → domain map
built from the nearest preceding top-level bullet's leading code-span token, classified by these
regexes (the judgement a re-derivation should challenge):

| Domain | Regex over the bullet's leading token |
|--------|---------------------------------------|
| release-train | `release_train\|assert_release_tag\|publish[-_]\|notes_render\|archive_guard\|ceremony\|release-train\|open_signed_pr` |
| experiments | `experiment\|isolated_stack\|run_suite\|run_experiment\|get_cascor\|plots_\|stats_summary\|list_runs` |
| agent-suite | `prompt_discovery\|template_\|scaffold_template\|agent_suite\|install_agents\|generated_prompt_index\|symbol_overlay\|skill\|agents_frontmatter\|prompt_validator\|fleet_supervisor` |
| fleet-and-seq-safety | `predict_merge\|fleet_triage\|sequence[-_]safety\|symbol-loss\|docs-additions\|wait_for_checks` |
| env-and-install-drift | `editable_install\|env_floor\|requirements_drift\|env_drift\|doc_tools_drift\|ci_tools_drift\|coverage_gap\|pyproject_extras\|service_fork_drift` |
| host-orchestration | `plant_all\|chop_all\|reap_pytest\|kill_helpers\|kill_all\|check_conda\|worktree\|cleanup_session\|wake_the_claude\|env_repr\|resume` |
| agents-md-gates | `agents_md` |

**Binary readings** ([§3](#3-three-facts-read-fresh-from-the-21235-binary)) were taken from
`/home/pcalnon/.local/share/claude/versions/2.1.235` by locating each needle's byte offset and
slicing a surrounding window — the same technique doc 2 used, with `grep -a` (the binary flag is
required; without it `grep` reports nothing and the absence reads as a negative result).
Needles: `disableModelInvocation`, `skillListingMaxDescChars`, `function mgf(e,t,r,n,o=fgf)`,
`syncClaudeAiSkills:`.

---

## Appendix B — related documents

| Document | Role |
|----------|------|
| [`JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-FILE-SIZE-BASELINE-MEASUREMENTS.md) | doc 1 — measured fact base |
| [`JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md`](JUNIPER_2026-08-18_JUNIPER-ML_CLAUDE-CODE-MEMORY-MECHANISM-FACTS.md) | doc 2 — verified mechanism facts |
| [`../AGENTS.md`](../AGENTS.md) | the subject |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | the 162,231-char operator reference this proposal de-duplicates against |
| [`JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`](JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md) | the compaction mitigation [§9](#91-compaction-behaviour) relies on |
| [`JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`](JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md) | holds the worktree how-to the residual file points at |
| [`JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`](JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md) | ditto |
| [`JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`](JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md) | existing home for release-train operator surface |
| [`JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md`](JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md) | the design of record behind skill 2 |
| [`JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`](JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md) | this document's naming rules |
