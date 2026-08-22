# Bypass-candidate determination — `29110` and `1143301` resolved by mechanism

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-22
**Status**: **DETERMINED.** Both rows are **INERT** on all 9 repos under the scoping in force
today, and both are demonstrated — not inferred — to be unnecessary. Recommendation:
**remove, staged, paired with a scope guard.** Nothing has been changed; this is read-only.
**Scope**: **Read-only.** No ruleset, bypass row, or repository setting was modified.
**Supersedes**: [`…_BYPASS-ACTOR-CENSUS.md`](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_BYPASS-ACTOR-CENSUS.md)
§3c's UNDETERMINED verdict and §4's two open rows.
**Tool**: `util/ad-hoc/2026-08-22_bypass_candidate_determination.py` (re-runnable)

---

## 0. Bottom line

The census left both rows UNDETERMINED because the only available evidence was
**absence from history** — the standard §1 itself called insufficient, and §3c re-applied
to dependabot after §1's verdict was withdrawn.

That standard is now met with something better. Two independent lines of evidence:

| Line | What it shows |
| --- | --- |
| **Mechanism** | All 9 rulesets are scoped `~DEFAULT_BRANCH`. The `creation` / `deletion` / `non_fast_forward` / `required_signatures` rules are therefore **not evaluated** on non-default branches — which is where both bots exclusively operate. The row cannot be consumed. |
| **Existence proof** | On `juniper-ml`, **both bots operated for two months with no bypass row at all**, under exactly the scoping in force fleet-wide today. This is a positive demonstration, not an inference from silence. |

| Actor | Census verdict | This document |
| --- | --- | --- |
| `29110` **dependabot[bot]** | UNDETERMINED | **REMOVABLE** — inert 9/9; demonstrated working without the row |
| `1143301` **Copilot SWE Agent** | UNDETERMINED | **REMOVABLE** — inert 9/9; demonstrated working without the row |

Fleet scan: **INERT 9 / LOAD-BEARING 0 / probe failures 0.**

---

## 1. The mechanism — why §3c's puzzle had a configuration answer

§3c established *that* dependabot's behaviour changed on 2026-08-10 but could not establish
*why*, recording: *"the ruleset's `creation` rule and `~DEFAULT_BRANCH` scoping are unchanged
since at least 2026-08-12."* That is accurate — **and the change was on 08-10, one day
outside the interval examined.**

GitHub retains per-ruleset version history, which makes the scope in force at any past
moment directly readable:

```bash
gh api repos/{owner}/{repo}/rulesets/{id}/history
gh api repos/{owner}/{repo}/rulesets/{id}/history/{version_id}   # payload is under .state
```

`juniper-cascor-client`, ruleset `13490605`, across the 08-10 boundary:

| Version | `conditions.ref_name.include` |
| --- | --- |
| `44737982` (2026-07-29) | **`~ALL`** — every branch |
| `46148582` (2026-08-10) | **`~DEFAULT_BRANCH`** — `main` only |

That is the whole explanation:

- **Under `~ALL`**, the `creation` rule was evaluated on *every* branch creation, including
  `dependabot/*`. The row was genuinely **load-bearing** — which is why the census found 24
  `bypass` suites with `creation: fail`. **§1's withdrawn reasoning was correct for that
  configuration**, exactly as §3c said.
- **Under `~DEFAULT_BRANCH`**, `dependabot/*` creations are not evaluated by the ruleset at
  all, so no suite is produced and no bypass is consumed.

This *predicts* the 08-17 observation (branch creations, no rule suite) rather than merely
being consistent with it, which is what makes it a mechanism and not another inference.

### 1a. The record corroborates, and it is a record that provably logs this

A bypassed event **does** produce a rule suite — that is how the census counted 24 of them.
So the suite log is a record capable of showing consumption of this exact row:

```text
cascor-client 2026-08-10 bypass refs/heads/dependabot/github_actions/claude-code-action-1.0.187
cascor-client 2026-08-10 bypass refs/heads/dependabot/github_actions/codeql-action-6c7da2231a
cascor-client 2026-08-04 bypass refs/heads/dependabot/github_actions/pypa/gh-action-pypi-publish-1.14.2
…  (11 total, month window)
```

Every one is a `dependabot/*` **branch creation**; none is on `refs/heads/main`; and the
**most recent is 2026-08-10**, the narrowing date. Dependabot created branches on 08-17 and
produced nothing.

> **Why this is not the discredited argument.** §3c's objection was that absence from a log
> does not prove non-use. Here the absence is *predicted in advance* by a configuration
> change with a timestamp, and the log is demonstrably capable of recording the event in
> question — it recorded 24 of them under the previous configuration.

---

## 2. The existence proof — both bots already ran without the row

Stronger than either of the above, and it needed no experiment because it already happened.

`juniper-ml` ruleset `13805432` had **no version change between 2026-05-19 (`37820935`) and
2026-07-20 (`43762857`)**. Both versions read:

```json
{ "scope": ["~DEFAULT_BRANCH"],
  "bypass": ["DeployKey:null", "RepositoryRole:5",
             "Integration:1210556", "Integration:1236702", "Integration:1276151"] }
```

**Neither `29110` nor `1143301` is present.** Both were added later, in the 2026-08-10 edits.

In that same window, on that same repo:

| Actor | Activity while its row did **not exist** |
| --- | --- |
| dependabot | **10 PRs** — ml#582–584 (06-29), ml#622–625 (07-06), ml#644–646 (07-13). Four more on 07-20 are same-day as the version edit and are excluded as ambiguous. |
| Copilot SWE Agent | **ml#629** (07-06). ml#269 is same-day as the 05-19 version and is excluded as ambiguous. |

Both bots created branches and opened PRs, with no bypass row, under the identical
`~DEFAULT_BRANCH` scoping that all 9 repos carry today. The rows are not merely unused —
they are **demonstrably unnecessary in this configuration**.

---

## 3. What the rows still grant (the reason not to leave them)

They are not harmless leftovers. Both are `bypass_mode: always` on the ruleset governing
`main`, whose rules are:

```text
deletion · non_fast_forward · required_signatures · creation
code_quality · code_scanning · required_status_checks · pull_request
```

An `always` bypass on that ruleset permits **force-pushing or deleting `main`**, and merging
past every required check. Neither bot needs any of it: **every merge is performed by
`pcalnon`** — sampled across dependabot (deploy#185, data-client#153, data#271,
cascor-client#118) and all Copilot PRs (ml#629, deploy#21, cascor#94). Neither bot has ever
merged to `main` itself.

So the choice is not "remove a no-op". It is: retain two standing `always`-mode entitlements
over `main` for integrations that have been shown not to need them.

---

## 4. Recommendation

**Remove both rows — staged, verified, and paired with a guard.** Do not fan out blind:
the determination is *configuration-dependent*, and §1's history is precisely what happens
when that dependency is forgotten.

| Step | Action | Verification |
| --- | --- | --- |
| **1** | Remove `29110` + `1143301` from **`juniper-ml` only** | This is the repo where the existence proof holds — a configuration already demonstrated to work for two months. |
| **2** | Wait for the next dependabot run | Runs weekly, observed every Monday (06-29, 07-06, 07-13, 07-20, 07-27, 08-03, 08-10, 08-17). Next ≈ **2026-08-24**. Confirm PRs appear. |
| **3** | Fan out to the remaining 8 | Re-run the tool; expect INERT 9 / LOAD-BEARING 0. |
| **Rollback** | One API call per repo to re-add | Reversible at every step; nothing is destructive. |

### 4a. The guard this must ship with

**If any ruleset is ever re-scoped to `~ALL`, both rows become load-bearing again** and
§1's withdrawn reasoning becomes correct once more — dependency PRs would stop fleet-wide.
The removal is therefore safe *only while the scoping holds*, and that must be enforced
rather than remembered.

Add a `~ALL`-scope assertion to the existing per-PR ruleset audit
(`util/ad-hoc/2026-08-10_ruleset_context_audit.py`) so a re-scope fails loudly instead of
silently re-arming a dependency on rows that are no longer there.

### 4b. Not covered here

- **`4362741` release-train App — still DO NOT TOUCH.** Unchanged from census §4. Its
  `pull_request` bypass mode is narrower, and the named test (arm an archive PR with the row
  absent) has still not been run. Void justification ≠ demonstrated redundancy.
- **`DeployKey` (null) — RETAIN.** Resolved by the operator 2026-08-22: the 17 keys are two
  development machines (this workstation, plus "Turing", a macOS laptop used away from it).
  Both are live. Census §3b's identification stands; the deletion option it raised is
  declined.
- **`RepositoryRole 5` (pcalnon) — KEEP.** 614 bypasses in a month; emphatically load-bearing.

---

## 5. Reproduction

```bash
python3 util/ad-hoc/2026-08-22_bypass_candidate_determination.py          # fleet scan
python3 util/ad-hoc/2026-08-22_bypass_candidate_determination.py --json

# the scope change that explains §3c
gh api repos/pcalnon/juniper-cascor-client/rulesets/13490605/history
gh api repos/pcalnon/juniper-cascor-client/rulesets/13490605/history/44737982 --jq .state.conditions
gh api repos/pcalnon/juniper-cascor-client/rulesets/13490605/history/46148582 --jq .state.conditions

# the existence proof
gh api repos/pcalnon/juniper-ml/rulesets/13805432/history/37820935 --jq '.state.bypass_actors'
gh search prs --repo pcalnon/juniper-ml --author app/dependabot --limit 30 --json number,createdAt
```

> **Two query traps hit while producing this document**, both caught, both worth repeating:
> `gh search prs --owner X --repo X/Y` **silently ignores `--repo`** and returns cross-repo
> results; and `repos/{r}/pulls?state=closed` returns only the most recent page, so an empty
> dependabot result from it is a **vacuous zero**, not a finding. Every zero in this document
> was checked against a sibling query proven able to return a non-empty answer.
