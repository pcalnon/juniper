# Held Planning Items — Design Advancement Register

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**Status**: PLANNING ONLY — nothing applied, no code written
**Date**: 2026-08-17

Companion to
[`JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md`](JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md),
which owns the publish-path family (TestPyPI gap + #357 / #358). This document advances the four
remaining held items.

---

## 1. `code_quality` ruleset rule — **prior analysis CORRECTED, priority drops**

### 1.1 What the register claimed

The 2026-08-15 ruleset register §2.4 recorded the tool-less `code_quality` rule as *"the untracked
root cause"* — that because it carries `{severity: errors}` with no reporting tool, *"every
non-bypass auto-merge waits forever on a check that never arrives"*, making it *"the
highest-leverage item here"* and the reason bypass actors accumulate.

### 1.2 What the live evidence shows

**The rule has never blocked anything.** Across the entire retained rule-suite window for
juniper-ml `main` (13 suites, 7 `bypass` / 6 `pass`):

| rule                                                              | pass   | fail  |
|-------------------------------------------------------------------|--------|-------|
| **`code_quality`**                                                | **13** | **0** |
| `code_scanning`                                                   | 8      | 5     |
| `pull_request`                                                    | 8      | 5     |
| `required_status_checks`                                          | 6      | 7     |
| `required_signatures`, `creation`, `deletion`, `non_fast_forward` | 13     | 0     |

Reproduce:

```bash
gh api 'repos/pcalnon/juniper-ml/rulesets/rule-suites?per_page=100' --jq '.[].id' \
  | while read -r id; do
      gh api "repos/pcalnon/juniper-ml/rulesets/rule-suites/$id" \
        --jq '.rule_evaluations[]? | "\(.rule_type)\t\(.result)"'
    done | sort | uniq -c
```

`code_quality` evaluates **`pass`**, not "in progress". Where a required *status check* that never
reports blocks permanently, this rule with no analysis behind it passes **vacuously**. The two
behave oppositely, and the register generalised from the wrong one.

The actual blockers are `required_status_checks`, `code_scanning`, and `pull_request` — which is
exactly the three-cause breakdown already recorded in the headless-merge memory (direct pushes to
main; squash-SHA carrying no reports yet; an unresolved `github-advanced-security` review thread).
No fourth, hidden cause was operating.

### 1.3 Corrected understanding of the rule

`code_quality` is not a "bring your own tool" rule — unlike `code_scanning`, which takes a
`code_scanning_tools` list, it has **no tool parameter by design**. It belongs to **GitHub Code
Quality** (public preview), a first-party feature that runs deterministic CodeQL rules plus
AI analysis on changed files and can block on findings at/above the configured severity. The rule
only has teeth when that feature is enabled on the repository.

`GET /repos/pcalnon/juniper-ml` shows no Code Quality entry under `security_and_analysis` (only
dependabot + secret scanning), consistent with the feature being off — though the preview may
simply not surface there yet, so treat that as suggestive rather than proof. The vacuous-pass
evidence in §1.2 is the load-bearing observation either way.

**Likely provenance of the Copilot bypass actor**: enabling GitHub Code Quality *used to* create a
ruleset that automatically requested Copilot code review, which GitHub removed on 2026-08-07
("GitHub Code Quality no longer adds Copilot as a reviewer"). That is a plausible mechanism for how
`Integration 946600` ("Copilot code review") arrived in the bypass roster on 2026-08-12 without
deliberate action — worth keeping in mind, but not verified.

### 1.4 Options, re-ranked

| # | Option                     | Assessment                                                                                                                                                                                                          |
|---|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A | **Leave it**               | Now the default. Inert, passing, costs nothing.                                                                                                                                                                     |
| B | Drop the rule              | Tidies the ruleset; removes a rule that does nothing. Low value, non-zero churn (a ruleset edit on 9 repos).                                                                                                        |
| C | Enable GitHub Code Quality | Gives the rule teeth — but it is **public preview**, it would newly *block* merges on findings, and it was the likely source of the unwanted Copilot reviewer/bypass. Evaluate on one repo only, never fleet-first. |

**Recommendation: A (leave it), and strike §2.4 from the register.** It is not a root cause and not
high-leverage. If tidiness matters later, B. C is a feature-adoption decision on its own merits,
not a fix for anything currently broken.

**Net effect on the bypass family**: removing bypass actors was worth doing on its own terms, but
there is no "fix this and bypasses stop accumulating" lever here. Bypasses accumulated because the
owner merges through `RepositoryRole 5` for the three documented structural reasons.

---

## 2. ml#1011 — promote Sequence Safety to required

**No design work outstanding.** This is a dated, gated decision, not an open question.

- **Gate**: the §A5.2 four-check decision checklist in the standing-items closeout plan, to run
  on **~2026-08-21** (5 days out). Per-repo contexts are in §A5.3.
- **State**: `Sequence Safety` is absent from the ruleset's 14 required contexts (verified
  2026-08-16). The job exists and is advisory; job name for promotion is exactly `Sequence Safety`
  (`ci.yml:783`).
- **Soak signal**: the last 6 `main-verify` runs are all `success` — the recurring main-verify-red
  class is quiet going into the call.
- **Standing caveat**: `RepositoryRole 5` holds `always` bypass, so promotion does **not**
  constrain owner merges. It makes the check load-bearing for fleet PRs and every non-bypass path.
  It is not the fix for the main-verify-red class.

**Action on ~08-21**: run §A5.2, then a single ruleset edit adding the context. Rollback: remove
the context; the job returns to advisory.

---

## 3. #588 — consolidate `util/env_floor_drift_check.py` with `juniper-env-drift-check`

The issue already carries the recommended direction. What planning adds is the **delta audit
first, decide second** sequencing and a concrete acceptance bar.

### 3.1 The two implementations

|                | `util/env_floor_drift_check.py`                                            | `juniper-env-drift-check` (ci-tools ≥0.5.0)                                         |
|----------------|----------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| Distribution   | in-repo, juniper-ml only                                                   | PyPI console script, fleet-wireable                                                 |
| Version source | `*.dist-info/METADATA`                                                     | `importlib.metadata`                                                                |
| Classes        | `OK` / `BELOW_FLOOR` / `MISSING`                                           | same                                                                                |
| Extra          | env selection via `--site-packages` / `--env` / `ecosystem.yaml` `used_by` | `--check-lock` (lockfile pins vs floors), plain-wheel aware, R3.3 keep-lowest dedup |
| Coverage       | `tests/test_env_floor_drift_check.py`                                      | ~95%, in ci-tools                                                                   |

The console script is the superset on distribution and lock-checking; the `util/` script's
distinctive asset is its **env-resolution precedence** (`--site-packages` → `--env` →
`ecosystem.yaml` `used_by`, exit 2 with a reason rather than inventing an env name).

### 3.2 Plan

1. **Delta audit** — enumerate every capability of the `util/` script absent from the console
   script. Specifically check: the resolve-precedence chain and its exit-2 honesty, multi-site
   keep-highest behaviour, and the malformed-METADATA skip. Produce a table; do not write code yet.
2. **Decide per capability**: port into ci-tools, or declare out of scope for a shared tool.
3. **Then** either retire `util/env_floor_drift_check.py` (updating its test + `AGENTS.md`) or
   reduce it to a thin wrapper. Prefer **retire** — a wrapper keeps two call paths and is the drift
   this issue exists to remove.
4. Ship as: ci-tools feature release → pin bump in ml → deletion PR. Three PRs, not one.

**Acceptance**: one implementation of the floor-drift logic in the tree; `AGENTS.md` and
`docs/REFERENCE.md` reference only the console script; `tests/test_env_drift_check_drift.py`'s
entry-point class guard still passes.

**Constraint (do not skip)**: the ci-tools 0.5.1 lesson — #580 silently dropped the 0.5.0 entry
point. Any ci-tools change here must keep the `[project.scripts]` guard green in the same PR.

---

## 4. #434 — sweep stacked-PR merges for the squash-into-stacked-branch footgun

### 4.1 Both named instances are already resolved

The issue names juniper-recurrence #7 / #8 as known-stranded. **They are not stranded now**:

```bash
#7 [MERGED] base=feature/ws4b-app-skeleton  head=04f1e918   → vs main: ahead_by=0, behind_by=209bash
#8 [MERGED] base=feature/ws4b-app-routes    head=06bf7a57   → vs main: ahead_by=0, behind_by=208bash
```

`ahead_by=0` means each head commit **is** an ancestor of `main` — both diffs landed. canopy #365bash
was likewise recovered by #366 at the time.bash

**Consequence**: the sweep's remediation urgency is gone. What remains is (abash) confirming no
*unnamed* instance is still stranded, and (b) the forward-looking policy — which is the durable
value.

### 4.2 Plan, re-scoped

1. **Detection pass** (read-only, scriptable, no repo writes):
   for each merged PR since 2026-06-01 across the 9 repos where `baseRefName ∉ {main, develop}`,
   test reachability via the compare API — `ahead_by == 0` against `main` means it landed.
   The API form avoids needing 9 local checkouts, which the issue's
   `git merge-base --is-ancestor` sketch would require.
2. **Report** `(repo, PR, baseRef, landed? y/n)`; remediate only genuine misses.
3. **Policy** — the durable half:
   - prefer retarget-to-`main`-then-merge over merging into a stacked base;
   - after any stacked merge, verify the diff is reachable from `main`;
   - never trust the MERGED badge alone.

### 4.3 Note on the underlying memory

The "squash ships only the first commit" belief has three recorded incidents, but the memory itself
attributes #2 to a **push-vs-merge race** and #3 to the **stacked-branch** shape — neither is
squash dropping commits. Only the original juniper-deploy#92 observation matches the literal claim,
and standard GitHub squash does combine all commits. Worth re-testing deliberately before the
policy asserts the mechanism: the *outcome* (a diff that never reaches `main`) is well evidenced;
the *stated cause* may be over-generalised from one case.

Cheap test: open a throwaway 2-commit PR where commit 2 modifies commit 1's file, squash-merge it,
and inspect the merge commit's diff. One PR settles it.

---

## 5. Summary of what changed in this pass

| Item           | Before                                   | After                                                    |
|----------------|------------------------------------------|----------------------------------------------------------|
| `code_quality` | "untracked root cause, highest-leverage" | **inert; passes 13/13; leave it**                        |
| ml#1011        | pending                                  | unchanged — dated ~08-21, checklist-gated                |
| #588           | "consolidate"                            | sequenced: audit delta → port → retire, as 3 PRs         |
| #434           | 2 known-stranded PRs                     | **both already landed**; re-scoped to detection + policy |
| TestPyPI gap   | one env unprotected                      | **all 18 envs accept any ref** — see companion doc       |

---

## 6. Sources

- [GitHub — Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [GitHub Code Quality](https://docs.github.com/en/code-security/concepts/code-quality/code-quality)
- [Changelog — GitHub Code Quality no longer adds Copilot as a reviewer (2026-08-07)](https://github.blog/changelog/2026-08-07-github-code-quality-no-longer-adds-copilot-as-a-reviewer/)
- [Changelog — Copilot code review: independent repository rule (2025-09-10)](https://github.blog/changelog/2025-09-10-copilot-code-review-independent-repository-rule-for-automatic-reviews/)
- [GitHub — REST API endpoints for rules](https://docs.github.com/en/rest/repos/rules)
