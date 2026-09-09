# Juniper Custom Agent Suite — Design & Roadmap

**Project**: juniper-ml — Meta-package & automation hub for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Document Type**: Design-of-record + roadmap
**Document Version**: v2 (validation-hardened)
**Status**: RATIFIED — round-1 build authorized (owner, 2026-06-24)
**Last Updated**: 2026-06-24

---

## 0. Status banner & revision history

> This is the **design-of-record** for the round-1 Juniper custom-agent suite. **v2** incorporates the
> findings of a five-reviewer adversarial validation pass (2026-06-24); the full verdict and
> finding→resolution map is **Appendix C**. The exploratory draft `scripts/custom_agent_dev.bash` is
> **already on `origin/main`** (committed + relocated from `notes/` by concurrent housekeeping, incl. #524);
> the only untracked artifact is *this design document*, which PR 1 commits.

| Version | Date | Change |
|---------|------|--------|
| v1 | 2026-06-23 | Initial design after corpus survey + primitive research |
| **v2** | **2026-06-24** | Validated & Hardened, 5-agents: concrete validator contract, bound loop; expand rubric (R1–R5); ground bundle gains symbol/dep/prov facts; `.gitignore` reality + `~/.claude` mirror + `--repo-root`; roadmap re-sliced & made CI-objective; factual corrections |
| **v2 — ratified** | **2026-06-24** | Owner ratified; round-1 build (PR 1) authorized |

---

## 1. Purpose & scope

Build a small suite of reusable **Claude Code automation units** ("agents") that mechanize recurring
phases of the Juniper development workflow. Round 1 delivers **4 agent types**, with the **Template
Agent** built first and deepest:

| # | Agent              | Job                                                                                                        | Round       |
|---|--------------------|------------------------------------------------------------------------------------------------------------|-------------|
| 1 | **Template Agent** | Turn an interactive task description into a validated, template-shaped, anti-hallucination-hardened prompt | **1 (now)** |
| 2 | **Planning Agent** | Produce a design / plan / analysis document in `notes/`                                                    | 2           |
| 3 | **Audit Agent**    | Systematic checklist review producing a findings report in `notes/`                                        | 2           |
| 4 | **Task Agent**     | Execute a concrete (often pre-generated) task, 1–3 repos, may fan out                                      | 2           |

Round-1 scope is the **Template Agent end-to-end plus its shared infrastructure** (template library,
validation rubric, environment-discovery helpers, data/field-population layer, validator subagent,
and the `~/.claude` mirror for cross-repo availability). The other three agents are **designed at suite
level here** (§6) so the architecture is coherent, but **built in round 2** because they reuse the same
infrastructure.

Out of scope for round 1: a persistent/queryable prompt database; the additional agent types from the
draft (Infrastructure / Review / Refactor / Test / Documentation); multi-machine distribution.

---

## 2. Background & genesis

This work realizes the vision Paul first sketched in `prompts/prompt-automation_2026-03-12.md`
(construct prompt-type templates, a data layer to populate template details, utility scripts for
environment discovery — prioritizing transparency, maintainability, flexibility). The
**`scripts/custom_agent_dev.bash`** draft (on `origin/main`, relocated from `notes/`) named the four agent types and a shared skeleton.

Two corpus facts ground the design:

1. **There is no `prompts/templates/` subdirectory.** The de-facto template set is the **seven**
   `prompts/common-prompt-template_*.md` files: `code-review`, `failing-tests`, `implement-plan`,
   `new-plan_failing-tests`, `proposal-analysis`, `regressions`, `release-and-deployment`. They are a
   **seed to mine, not a binding requirement** (per owner note).
2. **The seven converge on a skeleton** ~85–90 % aligned with the draft's structure and carry reusable
   **anti-hallucination doctrine** worth harvesting verbatim (§5.8, Appendix A).

### Corpus distillation (from survey)

- **Consensus skeleton**: `# Title → ## Role → ## Background/Resources → ## Objectives → ## Directives →
  ## Deliverables → ## Constraints → ## Finalize`. Proposal/synthesis templates condense.
- **Placeholder conventions are inconsistent** (mostly `[BRACKETS]`, sometimes blank). The suite
  establishes one systematic convention (§5.4).
- **Anti-hallucination phrasings already in use** (preserve verbatim): failing-tests' *"Do NOT delete,
  remove, disable, comment-out, or render inoperative ANY test … This is a CRITICAL and ABSOLUTE
  requirement"*; proposal-analysis' **sub-agent cross-validation**.
- **The corpus also carries live bugs the rubric must catch** (validation Appendix C): a `wake_the_claude.md`
  vs `.bash` reference; an "80 % / 90 %" handoff threshold that conflicts with the current "95–99 %"
  policy; "effectively error-free" as a non-measurable acceptance criterion; unfilled `-` stub bullets.
  These become negative-test fixtures.
- **Author voice / standing conventions** to inject: worktree isolation under
  `/home/pcalnon/Development/python/Juniper/worktrees/`; design-first; PR + JR-ID; *"Paul approves merges
  + PyPI / deploy gates"*; *"`gh pr list` before assuming a red PR is yours"*; deliverables to `notes/`;
  line-length 512; canonical file headers.

---

## 3. Ratified owner decisions (round 1)

| ID | Decision | Choice | Implication |
|----|----------|--------|-------------|
| **D-1** | Template Agent realization | **Hybrid**: interactive Skill front-end + headless validator subagent | Skill runs in main chat (asks clarifying Qs, iterates); delegates deep validation to an isolated subagent. §5.2–5.3. |
| **D-2** | Round-1 infrastructure depth | **Rich**: curated templates + rubric/registry + **discovery scripts** + **data layer** | Largest round-1 surface; sequenced so a *grounded* MVP ships before the data enrichment (§8). |
| **D-6** | Suite home & availability | **Project source-of-truth + `~/.claude` mirror** | Track `.claude/skills/**` + `.claude/agents/**` in juniper-ml via surgical `.gitignore` negations (PR-deliverable, versioned); a round-1 install step mirrors them into `~/.claude/` for global cross-repo use; discovery takes `--repo-root` to ground sibling repos. §5.6, §7, PR 1 & PR 6. |

Derived decisions (made here, open to revision on review):

- **D-3** Home = **juniper-ml project scope** as the versioned source-of-truth; the `~/.claude` mirror
  (D-6) provides availability from sibling-repo worktrees. `.claude/` is currently **fully gitignored**
  (`**/.claude/`), so PR 1 adds surgical negations for `.claude/skills/**` and `.claude/agents/**` only
  (worktrees + `settings.local.json` stay ignored).
- **D-4** Planning/Audit/Task = **subagents** (`.claude/agents/`); Template = **Skill** + one **validator
  subagent**.
- **D-5** Templates are **read-only sources**; the agent fills a **copy** (never mutates the template).

---

## 4. Suite architecture overview

```
                       ┌───────────────────────────────────────────────────────┐
   you (interactive) ──┤  /template-agent   (Skill, main conversation)         │
   task description    │   ingest → DISCOVER → expand(ask Qs) → categorize →   │
   (or @file/upstream) │   fill copy → VALIDATE(delegate) → [bounded loop] →   │
                       │   emit | emit-with-caveats | escalate-to-Paul         │
                       └───────┬─────────────────────────────────┬─────────────┘
                               │ reads                           │ delegates (Agent tool)
                ┌──────────────▼─────────────┐   ┌───────────────▼─────────────────────┐
                │ Template library           │   │ prompt-validator (subagent)         │
                │  prompts/templates/        │   │  applies RUBRIC R1–R5 →             │
                │   *.md, manifest.yaml      │   │  TYPED JSON verdict + per-finding   │
                │   (match_signals), RUBRIC, │   │  severity + independent re-probe    │
                │   data/*.yaml              │   │  of every claimed path/symbol/ver   │
                └──────────────┬─────────────┘   └─────────────────────────────────────┘
                               │ grounded by (closed-world fact set + provenance)
                ┌──────────────▼────────────────────────────────────────────────────────┐
                │ Discovery helpers  util/prompt_discovery/  (--repo-root, JSON bundle) │
                │  repo_context • test_status • file_probe • conventions • concurrency  │
                │  • symbol_probe(Serena) • dependency_facts • provenance{head_sha,ttl} │
                └───────────────────────────────────────────────────────────────────────┘

   Availability: util/install_agents.bash  symlinks .claude/{skills,agents}/* → ~/.claude/  (PR 6)
   Round 2:  .claude/agents/{planner,auditor,task-executor}.md   (reuse all shared infra)
```

**Shared infrastructure** (round 1, consumed by all four agents): template library + manifest + RUBRIC;
data/field-population layer; discovery helpers (the anti-hallucination backbone); the validator subagent;
the `~/.claude` mirror.

---

## 5. Template Agent — deep design

### 5.1 End-to-end flow (a bounded state machine)

`/template-agent` runs this loop in the main conversation. **Termination is explicit** — no "iterate
until clean" without a bound.

1. **Ingest** the task description (interactive from Paul; later a file/upstream agent). *The ingest
   source is itself subject to grounding* — do not trust assertions in an input file without checking.
2. **Discover** — run `util/prompt_discovery` against the **target** repo (`--repo-root`, default CWD) →
   a **grounding bundle** stamped with provenance `{head_sha, captured_at, dirty, ttl, per_probe_status}`.
   A discovery failure is a **hard stop**, never an empty-but-valid bundle.
3. **Interpret & expand** — analyze the task; surface implicit + explicit requirements; **ask Paul
   clarifying questions** for genuine ambiguities (the reason the front-end is a Skill, D-1).
4. **Categorize & select** — evaluate each template's `match_signals` from `manifest.yaml` in priority
   order (§5.4); on a thin margin between candidates, **ask Paul**; on no match, select `generic` and
   flag for possible **promotion** to a new named template.
5. **Fill a copy** — instantiate a copy of the selected template; populate placeholders from the
   expanded content + data layer + grounding bundle (D-5).
6. **Validate (delegate)** — if `head_sha` moved since step 2, **re-discover first**. Hand the drafted
   prompt + `RUBRIC.md` + grounding bundle to the `prompt-validator` subagent (Agent tool); receive a
   **typed JSON verdict** (§5.3).
7. **Loop control** — `PASS` → step 8. `FAIL` → apply only fixes the Skill agrees with; a fix that
   conflicts with task intent → **ask Paul**. Bounded at **max 3 rounds**; abort on no-progress
   (`delta_from_previous == 0`). On exhaustion → terminal **escalate-to-Paul** (emit best draft +
   explicit unresolved-findings block).
8. **Emit** — write linted markdown to `prompts/generated/` with a **collision-safe** name (§5.9); the
   Skill self-lints before writing (the dir is pre-commit-excluded). Report path + verdict summary.

Terminal states: `EMIT_CLEAN` · `EMIT_WITH_CAVEATS` (PASS-with-minors) · `ESCALATE_TO_PAUL`.

### 5.2 The Skill — `.claude/skills/template-agent/SKILL.md`

- **Why a Skill**: runs in the **main conversation**, so it can ask clarifying questions and iterate live
  (subagents are strictly headless). Interactivity is a property of running in the main thread and is
  **independent of invocation mode** — `disable-model-invocation: true` (user-only `/template-agent`)
  does **not** reduce interactivity; it only suppresses auto-invocation (we choose user-only initially,
  OQ-5).
- **Frontmatter** (verify exact fields against the installed Claude Code version at build):
  `name`, `description`, `argument-hint: "[task description | @file] [--repo-root <path>]"`,
  `allowed-tools` **must include** `Read, Grep, Glob, Bash` (discovery), `Write` (emission), `Agent`
  (delegate to the validator).
- **Skill → validator delegation** (Appendix B): a Skill executes inline in the main loop, which has the
  `Agent` tool, so delegation is expected to work — but this is a **PR-3/PR-5 build-time verification
  gate**. *Fallback if delegation is unavailable in the installed version*: the Skill performs an inline
  single-pass validation against `RUBRIC.md` (no isolated subagent) and notes the degradation.
- **Body**: the §5.1 state machine as explicit, ordered, bounded instructions.

### 5.3 The validator — `.claude/agents/prompt-validator.md` (subagent)

- **Why a subagent**: deep, possibly fan-out validation that must not pollute the main thread; returns
  only a typed verdict. `tools`: read-only + `Bash` (to **independently re-probe** the repo). `model`
  pinned after a cost/quality pass (OQ-4).
- **Typed verdict contract** (pinned schema — PR 3 ships a fixture; the Skill acts on this
  deterministically):

```json
{
  "validator_status": "ok | partial | error",
  "head_sha": "<must equal bundle.head_sha and current HEAD>",
  "iteration": 1,
  "findings": [
    {"id": "R2.0", "severity": "blocker | major | minor",
     "location": "§Resources / line 42", "problem": "...", "fix": "...",
     "evidence": "<exact command + observed output, or null>"}
  ],
  "hallucination_risk": [
    {"claim": "register_or_reuse(factory, name)", "class": "symbol",
     "grounded": false, "evidence": "grep + find_symbol output"}
  ],
  "overall": "PASS | FAIL"
}
```

- **PASS bar (measurable)**: `overall == PASS` **iff** zero `blocker` ∧ zero `major` findings ∧ every
  `hallucination_risk[].grounded == true`. `minor` findings are recorded as non-blocking warnings.
- **Independent re-verification**: for each claim the validator must **actively re-probe** (grep the
  path, resolve the symbol via Serena, check the pin) and attach `evidence`; a finding **without
  reproducible evidence is downgraded to `minor`** (cannot block) — this prevents validator false
  positives and breaks the shared-bundle single-point-of-failure.
- **Failure branches**: `validator_status == error` / malformed → Skill retries **once**, then
  **escalate-to-Paul**. Fan-out conflict rule: **any checker failing a criterion ⇒ criterion fails**.
- May **fan out** (one checker per criterion / per claim); nested subagents require a recent Claude Code
  version — confirm at build (Appendix B), else run checks sequentially in one subagent.

### 5.4 The template library — `prompts/templates/`

```
prompts/templates/
  README.md  manifest.yaml  RUBRIC.md  generic.md
  code-review.md  failing-tests.md  implement-plan.md
  proposal-analysis.md  regressions.md  release-and-deployment.md
  plan.md  audit.md  task.md          # round-2 skeletons (coherence)
  data/                               # field-population layer (§5.7)
```

**`new-plan_failing-tests` disposition** (the survey shows it *mirrors* `failing-tests` for the
multi-app case): it is folded into `failing-tests.md` as a documented **multi-app variant** (selectable
via a `match_signal`), not a separate file. Stated here so PR 2b coverage is unambiguous.

**Canonical skeleton** (unifies draft + corpus consensus):

```markdown
# {{CATEGORY_TITLE}}
## Role
## Resources            # grounding bundle injected here (real file:line, repo/branch, deps, conventions)
## Primary Objective
## Assigned Tasks / Directives
## Key Deliverables & Requirements
## Constraints          # optional
## Finalize / Validation # optional
```

**Placeholder convention** (the suite's single standard): `{{SNAKE}}` fill slot; `{{!REQUIRED: hint}}`
must be filled for validity; `{{?OPTIONAL: hint}}` may be dropped. The drift test asserts every
placeholder is declared in `manifest.yaml`.

**`manifest.yaml`** — registry with **deterministic selection** (not free-text):

```yaml
version: 1
skeleton: [title, role, resources, primary_objective, directives, deliverables, constraints, finalize]
placeholder: { fill: "{{SNAKE}}", required: "{{!REQUIRED:…}}", optional: "{{?OPTIONAL:…}}" }
templates:
  - id: failing-tests
    title: "Failing Tests"
    when_to_use: "Repair a red test suite without disabling tests."
    match_signals:                       # evaluated in priority order; Skill picks top; thin margin -> ask
      keywords: ["failing test", "test suite", "red", "pytest"]
      discovery: ["test_status.failing_count > 0"]
      variants: { multi_app: {keywords: ["across", "multiple apps", "ecosystem"]} }
    seed: prompts/common-prompt-template_failing-tests_2026-04-02.md
    required_fields: [application, failing_targets]
    class: execution            # gates R2.6 (verification & recoverability)
  - id: generic
    title: "Generic Task"
    when_to_use: "Fallback when no category matches; output is a promotion candidate."
    match_signals: { always: true }
    required_fields: [task_subject, deliverables]
    class: generic
```

A `manifest ⇄ templates ⇄ rubric` **drift test** (PR 2a) + a **selection unit test** (PR 2b) keep this
honest. **Promotion lifecycle**: a recurring `generic` output is proposed for graduation into a new
named template (small PR).

### 5.5 The validation RUBRIC — `prompts/templates/RUBRIC.md`

Stable-ID checklist the validator applies. Expanded after validation found the v1 three-criterion set was
**not collectively exhaustive** and conflated *prompt quality* with *deliverable correctness*.

**R1 — Intent fidelity** (the prompt expresses the task's intent)

- R1.1 every explicit requirement maps to ≥1 directive; no silent omissions.
- R1.2 no scope-creep / invented requirements beyond the task (+ approved expansions).
- R1.3 Primary Objective faithfully restates intent.
- **R1.4 scope correctness** — named repo(s)/app(s) match `bundle.repo_context`; authorized blast radius
  (tools, repo count, worktree/no-worktree) is proportionate.

**R2 — Actionability / sufficiency** (a competent agent could execute to a correct deliverable without
further questions — *deliverable correctness itself is undecidable from the prompt alone*)

- **R2.0 slot completion (hard gate)** — no `{{!REQUIRED}}`, empty mandated section, or bare-`-` stub
  remains; all `required_fields` populated with non-placeholder content. *(Cheapest, most decidable;
  catches the dominant corpus failure.)*
- R2.1 Role set; Resources cite concrete grounding (real `file:line`, repo/branch, deps).
- **R2.2 operational acceptance** — every criterion names a checkable command/artifact/observable;
  adjective-only criteria ("works correctly", "effectively error-free") **fail**.
- R2.3 directives ordered and unambiguous; deliverables enumerated.
- **R2.4 internal consistency** — no mutually-exclusive directives; file/script names + extensions
  consistent and present in the bundle; numeric thresholds non-conflicting.
- **R2.5 convention fidelity** — each injected standing rule matches the **current** canonical value in
  `data/*.yaml` / parent AGENTS.md (handoff threshold, deliverable locations, ports, line-length,
  worktree root); a *present-but-stale* convention is a `major`.
- **R2.6 verification & recoverability** (`class: execution` templates only) — prompt instructs how to
  verify success (tests/lint/observable) and how to recover/abort (no-merge-without-PR, worktree cleanup
  only on merge, `gh pr list` dup-guard).

**R3 — Anti-hallucination** (proactive steps so deliverables don't hallucinate)

- R3.1 names the **task-specific** verify commands (the actual test/lint command from discovery), not
  generic "run tests".
- R3.2 instructs verify-before-claim, cite `file:line`, do-not-invent (APIs/paths/flags/versions).
- R3.3 high-stakes work instructs sub-agent cross-validation.
- **R3.4 anchor grounding bind (hard gate)** — every asserted path/symbol/API/flag/version/port/env in
  Resources is present in the grounding bundle; any anchor not in the bundle goes to `hallucination_risk`
  and **fails R3**. (Claim taxonomy: R3.4a paths · R3.4b symbols · R3.4c versions · R3.4d ports/env ·
  R3.4e flags — the validator emits a per-class checked/flagged count for the drift test.)

**R4 — Clarity / unambiguity** — no undefined referent ("the issue", "this file") without a concrete
bound; each directive admits a single resolvable interpretation; reading order unambiguous.

**R5 — Right-sized scope** — states *what/why* + constraints, leaving implementation latitude unless the
owner pinned a design; flags over-specification that boxes the agent into a predetermined (possibly
wrong) solution. *(Counterpart to R1.2's scope-creep check.)*

**De-overlap**: grounding *presence* → R2.1; grounding *truthfulness* → R3.4. RUBRIC IDs are stable so the
verdict references exact checks and a drift test asserts rubric ↔ validator coverage.

### 5.6 Discovery helpers — `util/prompt_discovery/` (invoked by path; `util/` is not a package)

Invocation (matches house idiom — no `python -m`): `python util/prompt_discovery/cli.py --repo-root <path> --json`.

Emits a JSON **grounding bundle** = a **closed-world fact set** + provenance:

| Module | Probes | Anti-hallucination payoff |
|--------|--------|---------------------------|
| `repo_context.py` | repo name, branch, clean/dirty, HEAD sha (of `--repo-root`) | cites the *actual* target-repo state |
| `test_status.py` | last pytest result / failing names; **distinguishes `cold_cache`/`unavailable` from `empty`** | "no failures" can never masquerade as fact |
| `file_probe.py` | glob/grep for the task subject → candidate `file:line` anchors | Resources cite real anchors |
| `symbol_probe.py` | **resolve named symbols → signature + def `file:line`; grep-based in the path-invoked helper (it cannot call Serena), with a Serena `find_symbol`/`find_declaration` overlay planned at the Skill layer (OQ-8); else `UNRESOLVED`** | kills invented APIs/signatures |
| `dependency_facts.py` | `pyproject` extras + lockfile pins + sibling `dist-info`; ports/env from parent AGENTS.md | kills invented versions/ports/env names |
| `conventions.py` | AGENTS.md header, line-length, deliverable locations | conventions injected, not misremembered |
| `concurrency.py` | `gh pr list` + worktree scan (work dup-guard — **not** file-name collision) | flags duplicate *work* |

**Provenance envelope** stamped on the bundle: `{captured_at, head_sha, dirty, ttl_seconds,
per_probe_status: ok|stale|unavailable|cold_cache}`. The validator **rejects** a bundle whose `head_sha`
≠ current HEAD or that exceeds `ttl`; the Skill **re-discovers** if HEAD moved between fill and validate
(§5.1 step 6). Output schema is unit-tested (PR 4).

### 5.7 Data / field-population layer — `prompts/templates/data/`

Versioned YAML the resolver maps into template slots; this layer is the **canonical source** R2.5 checks
against:

- `standing_rules.yaml` — *"Paul approves merges + PyPI / deploy gates"*, worktree root, dup-guard rule.
- `anti_hallucination.yaml` — reusable doctrine blocks (verify-before-claim, cite `file:line`, no-invent).
- `conventions.yaml` — line-length 512, file-header schema, PR + JR-ID, **current handoff threshold (95–99 %)**.
- `ecosystem.yaml` — repo map, service ports, conda envs, dependency graph.

### 5.8 Anti-hallucination strategy (cross-cutting, defense-in-depth)

1. **Ground at generation time** (§5.6) — inject a closed-world fact set (now incl. symbol + dependency
   truth) so the prompt never asserts the unverified; reject stale/false grounding via provenance.
2. **Instruct grounding in the deliverable, enforceably** (R3) — the generated prompt embeds a
   **self-verification contract** ("re-confirm each cited `file:line`/symbol in-task; STOP-and-report
   rather than invent if not found") **plus a Deliverable-acceptance block** whose commands (repo
   drift-lint + `unittest` + `pre-commit`) produce the **evidence** — moving the burden from "agent
   promises" to "gate proves".
3. **Adversarial, independent validation** (§5.3) — the validator re-probes each claim itself (not just
   bundle-diffing) and binds ungrounded claims to a FAIL (R3.4).
4. **Post-hoc feedback** — when a deliverable later proves hallucinated, record the miss
   (`prompts/templates/data/known_misses.yaml`) and add it as a regression check in RUBRIC / the drift
   test, so the same hallucination can't ship twice.

### 5.9 Output naming & emission

Written to **`prompts/generated/`** with a **collision-safe** name (day-granularity collided in v1):
`{{PROJECT}}_{{APPLICATION}}_{{SUBJECT}}_{{TASK_TYPE}}_{{YYYY-MM-DD}}_{{HHMM}}.md`; **refuse-and-report**
if the path exists. The Skill **self-lints** the markdown before writing (the dir is pre-commit-excluded,
so no hook enforces it — the Skill / smoke test is the enforcer).

---

## 6. The other three agents (suite-level design, built round 2)

All three are **subagents** (`.claude/agents/`) reusing the library, rubric, data layer, discovery
helpers (with `--repo-root`), and the `~/.claude` mirror.

| Agent | File | Output | Naming | Tools |
|-------|------|--------|--------|-------|
| **Planning** | `planner.md` | design/plan/analysis doc | `JUNIPER_{{APP}}_{{SUBJECT}}_{{TYPE}}_{{DATE}}.md` in `notes/` | read-heavy + Write |
| **Audit** | `auditor.md` | findings report (cites doc `file:line`, code `file:line`, external URLs + downloaded content) | `JUNIPER_{{APP}}_{{SUBJECT}}_AUDIT_{{DATE}}.md` in `notes/` | read-heavy + WebFetch + Write |
| **Task** | `task-executor.md` | executes a (often pre-generated) task; 1–3 repos; may fan out | (usually no doc; reports progress) | Edit/Write/Bash; `isolation: worktree`; may nest |

---

## 7. File & directory layout (end of round 1)

```
juniper-ml/
├── .gitignore                                 # PR 1: surgical negations !.claude/skills/** !.claude/agents/**
├── .claude/
│   ├── skills/template-agent/SKILL.md         # PR 5  (interactive orchestrator; now tracked)
│   └── agents/prompt-validator.md             # PR 3  (headless validator; now tracked)
├── prompts/
│   ├── templates/                             # PR 2a (scaffold) + 2b (templates+RUBRIC)
│   │   ├── README.md  manifest.yaml  RUBRIC.md  generic.md
│   │   ├── code-review.md  failing-tests.md  implement-plan.md
│   │   ├── proposal-analysis.md  regressions.md  release-and-deployment.md
│   │   ├── plan.md  audit.md  task.md
│   │   └── data/                              # PR 6  (+ known_misses.yaml)
│   └── generated/                             # PR 5  (.gitkeep; emission target)
├── util/
│   ├── prompt_discovery/                      # PR 4  (cli.py + 7 probe modules; --repo-root)
│   └── install_agents.bash                    # PR 6  (~/.claude mirror; idempotent + reversible)
└── tests/
    ├── test_template_library_drift.py         # PR 2a (wired into ci.yml same PR)
    ├── test_template_selection.py             # PR 2b
    ├── test_prompt_validator_contract.py      # PR 3
    ├── test_prompt_discovery.py               # PR 4
    ├── test_template_agent_skill_lint.py      # PR 5
    └── test_template_data_resolver.py         # PR 6
```

---

## 8. Roadmap (single-work-unit PRs — re-sliced & CI-objective)

**Sequencing**: ship an *enforced* artifact early (green drift test at PR 2a), and put **discovery before
the Skill** so the MVP is genuinely grounded (validation found PR-4-MVP's value leaned on grounding).
Every acceptance criterion is a **static CI test**; live interactive paths are validated by **manual
dogfooding evidence attached to the PR** (an interactive Skill / subagent verdict cannot be exercised by
the repo's `unittest`-based CI). **Every PR that adds a tracked surface also: wires new test(s) into
`ci.yml`'s hardcoded `tests:` list, updates AGENTS.md (tree + Tests inventory), and confirms the file is
git-tracked** given the `prompts/**` exclude and `.claude` ignore.

| PR | Title | Delivers | Depends | CI-objective acceptance |
|----|-------|----------|---------|-------------------------|
| **1** | **Foundations & doc** | Surgical `.gitignore` negations (`!.claude/skills/**`, `!.claude/agents/**`); commit *this* design doc | — | `git check-ignore` shows skill/agent paths **not** ignored; doc tracked; CI green (AGENTS.md registration deferred to per-surface PRs — avoids registering non-existent surfaces + the touch-up orphan gotcha) |
| **2a** | **Library scaffold** | skeleton, `{{placeholder}}` convention, `manifest.yaml` (`match_signals`), `generic.md`, `README.md`, drift-test scaffold | 1 | `test_template_library_drift.py` green **and wired into ci.yml** |
| **2b** | **Templates + RUBRIC** | 6 seeded templates (+ `new-plan` variant), round-2 skeletons, full `RUBRIC.md` (R1–R5) | 2a | drift test covers all; `test_template_selection.py` green |
| **3** | **Validator subagent** | `.claude/agents/prompt-validator.md` + pinned verdict JSON schema + fixture | 2b | `test_prompt_validator_contract.py` (schema valid; every `R*.x` referenced exists in RUBRIC) green; **live dry-run evidence attached** |
| **4** | **Discovery helpers** | `util/prompt_discovery/` (7 probes incl. `symbol_probe`/`dependency_facts`) + `--repo-root` + provenance envelope | 1 | `test_prompt_discovery.py` green (bundle schema + provenance + cold/empty distinction) |
| **5** | **Skill MVP (grounded)** | `.claude/skills/template-agent/SKILL.md` — bounded state machine; wires library + validator + discovery | 2b, 3, 4 | `test_template_agent_skill_lint.py` (frontmatter + structure references real artifacts) green; **Skill→validator delegation confirmed at build**; **dogfooding artifact attached** |
| **6** | **Mirror + data layer** | `util/install_agents.bash` (`~/.claude` mirror) + `prompts/templates/data/*.yaml` + resolver + `known_misses.yaml` | 5 | mirror idempotent + reversible (asserted); `test_template_data_resolver.py` green |
| **7+** | **Round 2: Planning / Audit / Task** | three `.claude/agents/*.md` (one PR each) reusing shared infra | 2b, 4, 6 | each: frontmatter lint green; dogfooded artifact attached |

**Critical path to a grounded, usable Template Agent**: PR 1 → 2a → 2b → 3 → 4 → 5. PR 4 (discovery) can
run in **parallel** with PR 2/3. PR 6 enriches.

**Riskiest PR**: PR 5 (the Skill) — it is the integration point and the only piece not fully CI-testable;
mitigated by the static lint + the mandatory build-time delegation check + dogfooding evidence.

---

## 9. Testing & CI strategy

- **`prompts/**` is excluded from *all* pre-commit hooks** (`.pre-commit-config.yaml` global `exclude`,
  line 44) and from markdownlint (line 226). The template library therefore has **no pre-commit gate** —
  `test_template_library_drift.py`, **wired into `ci.yml`**, is the sole gate. (v1 misattributed this to
  `.markdownlint.yaml`, which has no exclude list — corrected.)
- **`ci.yml` runs a hardcoded test list** (27 entries today). Each new test is added to that list **in
  the same PR** as the code it covers (the repo's F14 history shows tests shipping unwired otherwise).
- **Interactive paths aren't CI-testable**: a Skill / subagent verdict needs a live model. So CI asserts
  the **static** surface (frontmatter lint, pinned schema, drift, unit tests); the **end-to-end run is a
  manual dogfooding gate** — run `/template-agent` once, attach the generated prompt + verdict to the PR.
- **`util/` is test-gated, not lint-gated** (pre-commit flake8 scopes to `scripts/` + `tests/` only);
  `test_prompt_discovery.py` carries the behavioral coverage, imported via the house `sys.path.insert`
  idiom.

---

## 10. Open questions & future work

- **OQ-1 (resolved into round 1)** — `~/.claude` mirror is now PR 6 (D-6), not deferred.
- **OQ-2 — prompt datastore**: YAML for round 1; a queryable store is future work if the snippet set grows.
- **OQ-3 — additional agent types** (Infrastructure/Review/Refactor/Test/Documentation): future rounds.
- **OQ-4 — validator model/cost** *(resolved 2026-06-24)*: `prompt-validator` pins `model: opus` (latest
  Opus) + `effort: max` — the suite's **standing default** for all agents and skills (owner directive);
  the validator is the last line of defense, so it runs at maximum capability/effort. Cost is bounded by
  the Skill's max-3-round fix loop.
- **OQ-5 — auto-invocation**: `/template-agent` user-only initially; revisit after dogfooding.
- **OQ-6 — scope precedence**: the two authoritative-mechanics passes disagreed on project-vs-user
  precedence. **Moot in round 1** because the `~/.claude` mirror is a *symlink to the project source*
  (identical content whichever wins); confirm at build.
- **OQ-7 — `.gitignore` negation review**: confirm the negations don't accidentally un-ignore session
  cruft (test with `git status` after PR 1).
- **OQ-8 — Serena symbol overlay** *(IMPLEMENTED 2026-06-25 — Skill-layer overlay + `util/prompt_discovery/symbol_overlay.py`; `symbol_probe` shipped grep-based in PR 4)*: the
  path-invoked `symbol_probe` resolves definitions with grep because a standalone script cannot reach the
  Serena MCP tools. A **Skill-layer overlay** can enrich (or supersede) those facts: the Template Agent
  Skill runs in the main conversation, which *does* have MCP access, so around the discovery step it may
  call Serena `find_symbol` / `find_declaration` for the task's named symbols and merge the results into
  the grounding bundle's `symbol_probe` slice (Serena-resolved wins; grep is the fallback; an unresolvable
  symbol stays `UNRESOLVED`). Deferred, separable follow-up (small PR): it touches only the Skill body and
  the bundle's `symbol_probe` consumer, **not** the path-invoked helper's contract — so it does not
  regress PR 4. Gated on Serena MCP availability (absent in headless/cron runs, where the grep fallback
  keeps the bundle valid). Related: §5.6 (`symbol_probe`), §5.2 (the Skill has MCP access in the main loop).

---

## 11. Conventions reference

- **Generated prompt names**: `{{PROJECT}}_{{APPLICATION}}_{{SUBJECT}}_{{TASK_TYPE}}_{{YYYY-MM-DD}}_{{HHMM}}.md`
  in `prompts/generated/` (refuse-and-report on collision).
- **Planning/Audit doc names**: `JUNIPER_{{APP}}_{{SUBJECT}}_{{TYPE|AUDIT}}_{{YYYY-MM-DD}}.md` in `notes/`.
- **Placeholders**: `{{SNAKE}}` / `{{!REQUIRED:…}}` / `{{?OPTIONAL:…}}`.
- **Script placement**: discovery + install helpers are permanent → `util/` (not `util/ad-hoc/`, not `/tmp/`).
- **Worktrees / PRs / handoff**: per parent + repo AGENTS.md.

---

## Appendix A — Seed-mining map (existing corpus → templates)

| New template | Seed source | Carry-over to preserve |
|--------------|-------------|------------------------|
| `code-review.md` | `…_code-review_2026-04-04.md` | issue-type taxonomy; severity/likelihood/scope/effort axes |
| `failing-tests.md` (+ multi-app variant) | `…_failing-tests_2026-04-02.md` **and** `…_new-plan_failing-tests_2026-04-27.md` | **anti-deletion doctrine** (verbatim); full-suite-pass acceptance; multi-app variant via `match_signal` |
| `implement-plan.md` | `…_implement-plan_2026-04-24.md` | plan-anchored execution; status-write-back |
| `proposal-analysis.md` | `…_proposal-analysis_2026-04-03.md` | **sub-agent cross-validation**; gap-capture |
| `regressions.md` | `…_regressions_2026-05-27.md` | regression-diagnosis framing (stub — complete it) |
| `release-and-deployment.md` | `…_release-and-deployment_2026-04-08.md` | planning-only caveat; changelog/version-semantics gates |
| `plan.md`/`audit.md`/`task.md` | `custom_agent_dev.bash` skeletons | per-agent structure for round 2 |
| `generic.md` | (new) | canonical skeleton + promotion-candidate marker |

## Appendix B — Primitive-mechanics reference (build-time)

- **Subagents** (`.claude/agents/*.md`): headless, isolated, **cannot ask the user mid-run**; `name`+
  `description` required, `tools`/`model`/`isolation` optional; can pin model + restrict tools; **may nest
  subagents on recent versions** (confirm installed version; else run checks sequentially).
- **Skills** (`.claude/skills/<name>/SKILL.md`): run in the **main conversation** (interactive, can ask
  questions — independent of `disable-model-invocation`); frontmatter `description`, `argument-hint`,
  `allowed-tools`, `model`, `disable-model-invocation`. Invoked `/name` and/or auto.
- **Skill → Agent delegation**: a Skill runs inline in the main loop, which has the `Agent` tool — so
  delegating to `prompt-validator` is expected to work, **but is a build-time gate** (PR 3/5) with an
  inline-validation fallback.
- **Scope**: `.claude/` is **fully gitignored** here; PR 1 adds surgical negations so the skill/agent are
  tracked. Project-scope availability requires CWD under juniper-ml → the **`~/.claude` mirror (PR 6)**
  provides cross-repo availability. Project-vs-user precedence is moot (mirror = symlink to source, OQ-6).

## Appendix C — Validation pass (2026-06-24)

Five independent adversarial reviewers (Claude-Code mechanics, architecture/flow, rubric completeness,
anti-hallucination rigor, roadmap slicing). **Consolidated verdict: NEEDS_REWORK** — spine endorsed,
substantial hardening required. All findings below are folded into v2.

**Repo facts I verified directly (two reviewer claims were wrong):**

- `.claude/` **is** fully gitignored (`**/.claude/`); `git check-ignore` confirms both deliverable paths
  ignored → **D-6 + PR 1 negations**.
- `custom_agent_dev.bash` **exists, is committed, and was relocated to `scripts/`** by concurrent
  housekeeping (shebang fix #524 + move commit 595811e); v1's "untracked in `notes/`" was stale →
  **§0/§2 corrected**. *(A live instance of the false-grounding risk the anti-hallucination reviewer
  raised — state moved under us twice: committed, then moved.)*
- `util/` is **not** a package (`packages=[]`, no `__init__.py`; tests use `sys.path.insert`) →
  **§5.6 path-based invocation**.
- `prompts/**` is **excluded from all pre-commit hooks**; `.markdownlint.yaml` has no exclude →
  **§9 corrected; drift test is sole gate**.
- `ci.yml` test list is **hardcoded** (27 entries) → **per-PR wiring made explicit**.
- 7 templates on disk incl. `new-plan_failing-tests` → **§5.4 fold-as-variant**.

**Finding → resolution map:**

| Severity | Finding | Resolved in |
|----------|---------|-------------|
| CRIT | unbounded iterate loop / "minor issues forever" | §5.1 bounded state machine; §5.3 PASS bar |
| CRIT | validator contract under-typed; failure path undefined | §5.3 typed schema + failure branches + fan-out rule |
| CRIT | grounding bundle lacks symbol/version/port truth; no freshness; single point of failure | §5.6 `symbol_probe`/`dependency_facts` + provenance; §5.3 independent re-probe |
| CRIT | `.claude/` gitignored → deliverables can't commit | D-6; PR 1 negations |
| CRIT | cross-repo scope: project Skill unavailable in sibling worktrees | D-6 `~/.claude` mirror + `--repo-root` |
| CRIT | rubric not collectively exhaustive; deliverable-correctness undecidable from prompt | §5.5 R1.4/R2.0/R2.2/R2.4/R2.5/R2.6/R3.4/R4/R5; R2 reframed |
| MAJ | manifest selection hand-wavy | §5.4 `match_signals` + selection test |
| MAJ | `python -m prompt_discovery` unrunnable | §5.6 path-based invocation |
| MAJ | PR-4 MVP value leaned on PR-5 grounding | §8 discovery reordered before Skill |
| MAJ | `prompts/generated/` name collisions; dup-guard mis-scoped | §5.9 HHMM + refuse-on-exist; §5.6 dup-guard clarified |
| MAJ | every new test must be wired into ci.yml; AGENTS.md per-PR | §8 standing per-PR items |
| MAJ | Layer 2 aspirational; no post-hoc feedback | §5.8 self-verification contract + acceptance block + `known_misses.yaml` |
| MIN | markdownlint misattribution; "linted" emission unenforced | §9 corrected; §5.9 Skill self-lints |
| MIN | PR 2 oversized | §8 split 2a/2b |
| MIN | `new-plan_failing-tests` dropped | §5.4 documented variant |
