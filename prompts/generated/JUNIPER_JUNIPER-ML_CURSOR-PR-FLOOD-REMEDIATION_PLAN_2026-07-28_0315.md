# Plan / Design — Cursor-fleet PR-flood remediation for pcalnon/juniper-ml: damage census, root-cause consolidation, and independently-validated guardrail proposals

<!--
Generated prompt (Template Agent convention): category template `plan` (class=planning), selected by
match_signals (runner-up: audit). Grounded 2026-07-28 against juniper-ml main @ ac2ec9d7 (clean;
util/prompt_discovery bundle captured, all probes ok). Validated pre-emission by the house triple:
prompt-validator (RUBRIC R1-R5: PASS, iteration 1, 2 minors fixed), adversarial fact-refuter
(45 confirmed / 5 refuted -> corrections applied below), feasibility reviewer (PASS-conditional ->
all 7 SHOULD-FIXes + NITs applied). Owner approval gates every destructive or outward-facing step;
this prompt performs no merges and no repo-settings/dashboard changes — its only writes are
owner-merged heal PRs and the owner-merged results-doc PR.
-->

## Role

You are a principal engineer / architect for the Juniper ecosystem, executing a multi-agent remediation program for the 2026-07-25→28 Cursor-fleet PR flood on `pcalnon/juniper-ml`. You weigh options, dispatch and adjudicate specialist agents, and commit to defensible, owner-actionable recommendations. You never merge, never change repo settings, and never act on the Cursor dashboard — those are owner decisions this program prepares.

## Resources

- Grounding bundle: `util/prompt_discovery/cli.py --repo-root <checkout>` at main `ac2ec9d` (dirty=False; all seven probes ok: repo_context/test_status/file_probe/symbol_probe/dependency_facts/conventions/concurrency). Re-run at YOUR head before executing; a drifted anchor is a stop-and-re-ground signal.
- Phase-0 forensic findings (already completed 2026-07-28 by two independent read-only agents; §"Phase 0" below summarizes; the incident log lives in the owner-memory topic file `/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_juniper_ml_concurrent_session_activity.md`, section "2026-07-26: Cursor Automation fleet").
- House machinery to use: the custom-agent suite (`.claude/agents/`: `planner`, `auditor`, `prompt-validator`, `task-executor`; template library `prompts/agent_templates/`, templates incl. `plan`, `audit`, `proposal-analysis`), `util/generated_prompt_index.py`, `prompts/agent_templates/data/conventions.yaml` (line length 512; generated-prompt naming `PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md`). The notes/ naming convention `JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<PHRASE>.md` is specified in `AGENTS.md` and `notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md` (NOT in conventions.yaml).
- Incident repair recipes: AST per-method loss-screen vs `<merge-sha>^1` baselines, graft-method restores, and the docs additions-only diff rule are documented in the memory topic above; the `git log -m -S<symbol>` merge-resolution-deletion unmasking technique is documented in heal PR #843's body. Heal-PR precedents: #838/#842/#843.

## Primary Objective

Deliver, with independent multi-agent validation at every stage: (1) a definitive damage census of the flood with heal PRs for anything still broken or silently deleted; (2) a consolidated root-cause finding; (3) three independent, validated guardrail/process proposals for the owner to choose among; (4) a process-validation record; (5) a single results document in `notes/`, linting, owner-merge PR'd.

## Phase 0 — COMPLETED grounding (verified 2026-07-28; do NOT redo, re-verify at HEAD)

- **Scope**: 134 PRs created in the window (span #710–#843; 63 `cursor/missing-test-coverage-*`, 57 `cursor/engineering-documentation-updates-*`, 6 `cursor/critical-bug-investigation-*`, 8 non-cursor incl. heals #838/#842/#843); 133 merged (125 cursor), 1 closed (#743), 0 open. Creation ran ~25 hours (2026-07-25 19:41Z → 07-26 20:14Z, containing a 10-hour lull; merge activity continued through 07-28), peaking at 48 PRs per fixed 6-hour UTC bucket; parallel same-second dispatch pairs observed; ~monthly storm precedent (2026-03: 47, 05: 10, 06: 28, 07: 130 cursor PRs). The owner-observed "600+" counter = repo-lifetime closed PRs (835), not the flood.
- **Merge mechanics**: 100% true merges (no squashes); 136 `Merge branch 'main' into <branch>` union-carrier commits rode in on second parents. No `merge=union` driver exists — the damage is ordinary 3-way (ort) hunk fusion/loss on append-heavy files during stale-branch updates.
- **Root cause chain**: Cursor GitHub App (id 1210556; three dashboard automations, per-class UUIDs in PR bodies; no in-repo config — the control surface is entirely the Cursor dashboard) → same-file fan-out (top clusters: `AGENTS.md` 53 PRs, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` 53, release-train operator runbook 33, `docs/REFERENCE.md` 15; `tests/test_release_train_detect.py` 12, `_workflow_guard` 10, `_ceremony` 10, `_propose` 9, `test_worktree_cleanup.py` 10) → ruleset `juniper-ml-rules` (id 13805432) has `strict_required_status_checks_policy: false` (branches need NOT be up to date), NO required-review rule, NO merge queue → owner manually true-merged all 125, using GitHub-web "Update branch" (committer `GitHub` + author `pcalnon` signature) to refresh stale branches — those 3-way merges fused/deleted sibling content that was individually green → damaged states merged green. The Cursor app holds **always-bypass** on the ruleset, as do two unidentified integrations (ids 1236702, 1276151).
- **Current health at `ac2ec9d`**: full per-file unittest battery GREEN; `pre-commit run --all-files` clean; main CI + CodeQL green; the three chop/plant/stack cluster test files pass. The primary checkout (found parked on incident #782's branch, 338 behind) has been restored to main.
- **Known-unaudited residue** (the census target; counts are the PR-files metric, i.e. merge-base…head branch-side diffs): Python — `tests/test_release_train_detect.py` (12 touching merges), `tests/test_release_train_workflow_guard.py` (10 branch-side / 7 net), `tests/test_release_train_ceremony.py` (10), `tests/test_juniper_plant_all.py` (5), `util/release_train/propose.py` (5, production); docs — cheatsheet (53), operator runbook (33; #843 flagged a mid-flood RESUME_MONITOR coverage drop 4→2 — at `ac2ec9d` the runbook has 3 mentions and the PRE-FLOOD baseline was 0, so C2 adjudicates fresh rather than chasing a stale count), `REFERENCE.md` (15), `DOCUMENTATION_OVERVIEW.md` (7), worktree-cleanup procedure (7). Census universe bound: 76 test-touching, 16 util-touching, 61 doc-touching, 9 `.github/workflows/ci.yml`-touching true merges.

## Assigned Tasks / Directives

### Task 1 — Definitive damage census (concurrent agent fan-out; audit-class)

0. **Pinned census universe** (compute ONCE, share with C1/C2/C3 so all derive identical sets): window merges = `git log --first-parent --merges --since=2026-07-25 --until=2026-07-29 --format=%H origin/main`, filtered to `Merge pull request #`; per-merge touched files = the PR-files metric `git diff --name-only $(git merge-base <M>^1 <M>^2) <M>^2`. Expected sizes at `ac2ec9d`: 76 test-touching, 16 util-touching, 61 doc-touching, 9 ci.yml-touching (±1 window-edge drift tolerated; reconcile explicitly if larger).
1. **Python census** (agent C1, `auditor`-class dispatched in return-findings mode): for every `tests/*.py` and `util/**` Python/bash file touched by the 76 + 16 true merges, run the proven AST per-method loss-screen: symbol inventory (classes, methods, module helpers, imports, constants) at each merge's `^1` main-side parent vs current main; classify LOST / WEAKENED (source-segment shrunk) / DUPLICATED / OK. Use `git log -m -S<symbol>` (the #843 technique) to attribute each loss to its merge. Baselines: `bd25e31` (post-#842) and #843's merge `df32640` are known-good waypoints. ALSO screen the 9 ci.yml-touching merges (line-diff vs `^1`; `test_workflow_script_paths.py` + green CI only partially guard workflows). Output: per-file findings table with the guilty merge SHA and the last-good blob (`<merge>^1:<path>`).
2. **Docs census** (agent C2, `auditor`-class in return-findings mode, concurrent with C1): for the 6 doc-union files, reconstruct expected content as (pre-flood blob) + each merged PR's OWN intended additions, extracted with the verified recipe: per merge `M`, intended commits = `git log --no-merges <M>^2 --not <M>^1`, each patch via `git show` — `<M>^2` is the branch tip at merge time and is ALWAYS locally reachable from main (do not rely on `refs/pull/*` or stale `origin/cursor/*` refs). Diff the reconstruction against current main; any missing section/bullet/anchor is a finding. Adjudicate RESUME_MONITOR runbook coverage fresh (mid-flood 4→2, 3 at `ac2ec9d`, pre-flood 0). The doc-links validator only catches dangling anchors — prose loss needs this reconstruction, there is no cheaper gate.
3. **Completeness critic** (agent C3, after C1/C2, return-findings mode): what did the census NOT cover (non-cluster files touched once, scripts/, config)? Spot-check 5 random single-touch merges for the same loss classes.
4. **Heal**: for confirmed findings, restore verbatim from the last-good blob (graft method; never rewrite), one heal PR per file-cluster, full battery + pre-commit + (for docs) doc-links green, owner merges. Re-run the census after heals → censusclean statement.

### Task 2 — Root-cause consolidation (planner-class agent; mostly synthesis)

1. Consolidate Phase 0's two forensic reports plus the memory incident log (incidents #1–#7+, the failure-class taxonomy, repair recipes) into the findings section of the Task-5 notes document — mechanism chain, timeline, quantified damage, what already healed.
2. Owner-side open probes to REQUEST (not perform): names of always-bypass integrations 1236702/1276151; the three Cursor automation configs (schedule, concurrency, per-class prompts, file-scope settings) from the dashboard UUIDs in PR bodies (#729, #746).

### Task 3 — Three INDEPENDENT guardrail proposals (concurrent proposal agents; each blind to the others)

Dispatch three `planner`/`proposal-analysis`-class agents with disjoint mandates; each must cover, at minimum, its assigned angle on the owner's six required components (excessive-queue guardrails; earlier-PRs-not-breaking-later-PRs checks; whole-sequence compositional success; agent PRs following documented Juniper best practices; the option of blocking direct Cursor PR creation; a custom-agent supervisory layer over third-party agent PR creation):

- **P1 — Repository-side guardrails (GitHub controls)**: merge queue on main OR `strict_required_status_checks_policy: true` (require-branches-up-to-date) — quantify against the 8 documented incidents (all would have been caught: checks would run on the true merge result); a `pull_request` required-review rule (CODEOWNERS is advisory today); removing the Cursor app's always-bypass (and adjudicating integrations 1236702/1276151); auto-merge and update-branch policy; open-PR budget alarms. Each control: exact setting, cost to the owner's solo-maintainer flow, and which incident class it kills.
- **P2 — Compositional CI (sequence-safety gates)**: a symbol-loss CI gate (per-PR: AST symbol inventory of merge-ref vs base for every touched Python file — fail on silent deletion of tests/helpers; PROPOSES productionizing the Task-1 census tooling into `util/` + a lint test per house pattern — no code ships during Task 3); a docs additions-only gate for docs-class PRs (`git diff base -- <docs>` minus-lines ⇒ fail unless explicitly labeled); a post-merge main-verification workflow (battery + loss-screen on every push to main, so damage is caught at the FIRST bad merge, not incident #7); pre-commit merge-ref contamination remedy (the stale `--all-files` class).
- **P3 — Supervisory layer + fleet policy**: a Claude-side supervisor custom agent (triage every fleet PR before owner merge: dup/supersession detection, same-file cluster map, proposed merge ORDER, per-PR predicted merge-result validation — effectively pre-computing what the merge queue would do, plus judgment); Cursor-dashboard controls to request (concurrency cap, schedule cadence, per-class disjoint file scopes, PR budget); an AGENTS.md "third-party agent PR contract" section (single tidy commit, repo-pinned formatters before push, dup-guard, no same-file fan-out, additions-only docs); and the explicit evaluation of BLOCKING direct Cursor PR creation (remove write/bypass; fleet output routed through the supervisor as draft PRs or patches) — with the trade-offs stated, not assumed.

**Per-proposal validation (before any proposal reaches the owner)**: each proposal is independently reviewed by (a) an adversarial hallucination/fact refuter (every claimed setting, API, incident reference re-probed against the repo/GitHub — a GitHub control that does not exist as described kills the claim), (b) a correctness/best-practices reviewer (against the documented Juniper conventions: worktrees, owner-merge, notes/prompts conventions, lint gates), and (c) an effectiveness reviewer (does it actually kill the incident classes; cost/benefit for a solo owner + agent fleet). At most TWO revise-and-revalidate cycles per proposal; anything still contested after cycle 2 surfaces to the owner as an explicit disagreement rather than being silently resolved.

### Task 4 — Process validation

The program itself is validated: this prompt passed the pre-emission triple (prompt-validator RUBRIC R1-R5 with per-claim re-probe, adversarial fact-refuter, feasibility reviewer — findings incorporated before emission); at execution, each task's outputs carry their own validator sign-offs (Task 1 census re-run after heals; Task 3 per-proposal triple); and the Task-5 document gets a final independent read-through agent checking internal consistency (numbers, PR references, claims) before the PR opens.

### Task 5 — Results document

Write `notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md` (date = execution date; the `-ANALYSIS` ending satisfies the notes doc-type convention; refuse and report if the path exists; the ORCHESTRATOR writes this file — dispatched planner/auditor agents only contribute section content in return-findings mode): incident narrative + quantified scope, root-cause chain, damage census results + heals, the three validated proposals with their validation records and a comparison matrix, owner decision list (merge-queue/strict choice; review rule; bypass removals; Cursor dashboard changes; blocking option; supervisor adoption), and the process-validation record. Must pass `juniper-check-doc-links` (CI flags) and the applicable pre-commit hooks; land via an owner-merge PR carrying the `## Requirements` JR-ID section per repo convention (state "no tracked JR-ID applies" if none does). The PR also commits this prompt file's index presence — verify with `util/generated_prompt_index.py`, NO pruning.

## Key Deliverables & Requirements

- Damage-census findings tables + heal PRs (owner-merge) + a censusclean statement re-verified after heals.
- The consolidated root-cause section with evidence citations (ruleset id + parameters, app id, merge-commit signatures, cluster counts).
- Three independently-validated proposals, each covering the six owner-required components from its angle, with validation records attached.
- The Task-5 notes document, linting, PR'd; every `file:line`/PR#/SHA cited is real (present in the grounding bundle, the forensic evidence, or re-probed) — no invented paths, settings, or GitHub features.
- All fan-out agents receive explicit read-only vs write mandates and are dispatched in **return-findings mode** — the house `planner`/`auditor` contracts write notes/ documents by default, which is SUPPRESSED here (findings return to the orchestrator; no intermediate notes/ files). Only heal PRs and the results-doc PR write anything, and nothing self-merges.
- Any census/screen script an agent needs lives in `util/ad-hoc/` (per the mandatory script-placement rule), NEVER `/tmp/` — `/tmp/` is reaped and this exact class of loss is the rule's founding incident. `/tmp/` remains fine for intermediate data artifacts.

## Constraints

- **Owner-only decisions** — merging any PR; any ruleset/branch-protection change; any Cursor-dashboard change; blocking or restricting the Cursor app; adopting the supervisor. The program PREPARES these with evidence; it never performs them.
- Concurrent sessions are the norm in this repo: `gh pr list` dup-guard before opening ANY PR; re-fetch main before computing any merge status; expect main to move mid-task.
- House rules: centralized worktrees; `-c commit.gpgsign=false` headless commits; one tidy commit per PR; required_signatures leaves PRs BLOCKED-until-owner (normal); `tests/redacted_env.py` for any subprocess env mapping in new test code.
- Do not run destructive git operations in the primary checkout; the census reads history only.

## Finalize / Validation

- Re-confirm every anchor (SHAs, PR numbers, ruleset parameters, file cluster counts) at YOUR head before acting on it; drop or flag any that drifted rather than inventing.
- The program is complete when: census is clean post-heals; the three proposals carry passing validation records; the notes document is merged (or open awaiting the owner) and the owner has an explicit decision list; and this prompt's `prompts/generated/` entry is indexed by `util/generated_prompt_index.py` without convention violations.
