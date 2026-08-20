# Bypass-actor census — the evidence the ml#1012 decision was waiting on

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-20
**Status**: Census COMPLETE. **One of the two removal candidates is refuted by evidence.**
**Scope**: **Read-only.** No ruleset, bypass row, or repository setting was changed.
**Related**: `HANDOFF_2026-08-19` §2.5; ml#1012;
[`…_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md)

---

## 0. Bottom line

The handoff framed the open decision as *"remove `29110` (dependabot) and `1143301` (Copilot
SWE Agent), both of which work solely via PRs on their own branches, and the rulesets target
`~DEFAULT_BRANCH` only"* — flagging correctly that **"never exercised a bypass" was an
INFERENCE, not a finding**, and asking for a full 9-repo census first.

The census was run. It splits the two candidates:

| Actor | Suites (1 month, 9 repos) | Verdict |
| --- | --- | --- |
| `29110` **dependabot[bot]** | **bypass 24 / pass 0 / fail 0** | **DO NOT REMOVE — refuted** |
| `1143301` **Copilot SWE Agent** | **absent entirely** | removal argument survives |
| `RepositoryRole 5` **pcalnon** | bypass 614 / pass 208 / fail 1 | **KEEP** — confirms the §1 caveat, emphatically |
| `4362741` release-train App | pass 1 | consistent with *"test it or leave it"*; nothing new |
| `DeployKey` (null) | absent | still **IDENTIFY-FIRST**; absence is not identification |

Tools (both in-repo, re-runnable):
`util/ad-hoc/2026-08-20_bypass_actor_census.py`, `util/ad-hoc/2026-08-20_creation_rule_scan.py`.

---

## 1. Why the dependabot argument fails — the premise is true AND insufficient

The removal argument rests on the rulesets being scoped to `~DEFAULT_BRANCH`, so an actor
that only ever pushes its own branches never meets them. **That scoping claim is correct.**
Every per-repo ruleset on all nine repos includes exactly `~DEFAULT_BRANCH` and excludes
nothing.

It is still insufficient, because of the `creation` rule. Rule suite `3625611564`
(juniper-cascor-client, 2026-08-10T12:29:55-05:00):

```text
actor_name : dependabot[bot]
ref        : refs/heads/dependabot/github_actions/anthropics/claude-code-action-1.0.187
before_sha : 0000000000000000000000000000000000000000     <-- a branch CREATION
result     : bypass
  creation            : fail  "Cannot create ref due to creations being restricted."
  required_signatures : pass
  …
```

A `creation` rule evaluates against dependabot **creating its own update branch**, which is
not a push to the default branch and is therefore not what the `~DEFAULT_BRANCH` argument
predicts. dependabot's `always` bypass is the only thing carrying that creation through.

**This is not confined to one repo.** `creation` is present in the primary ruleset of **all
nine**:

| repo | ruleset carrying `creation` |
| --- | --- |
| juniper-ml | `juniper-ml-rules` |
| juniper-cascor | `juniper-cascor-rules` |
| juniper-canopy | `juniper-canopy-rules` |
| juniper-data | `juniper-data-rules` |
| juniper-data-client | `data-client-rules` |
| juniper-cascor-client | `juniper-cascor-client-rules` |
| juniper-cascor-worker | `juniper-cascor-worker-rules` |
| juniper-deploy | `juniper-deploy-rules` |
| juniper-recurrence | `juniper-recurrent-rules` |

(The `juniper-no-direct-push` ruleset carries only `pull_request` and is not implicated.)

**Consequence: removing row `29110` stops dependency PRs across the fleet**, not merely on
juniper-cascor-client. dependabot's 24 recorded suites are *all* bypasses — it has never once
satisfied these rulesets without the entitlement.

> **Generalise the lesson, not the row.** `~DEFAULT_BRANCH`-scoping is a sound argument for
> retiring a bypass **only when the ruleset contains no `creation` rule**. That qualifier is
> what retired cursor / claude / Amp / Copilot-code-review safely — those actors were being
> compared against the same rulesets, so it is worth spot-checking whether any of them also
> needed branch creation and simply has not been exercised since.

---

## 2. Per-repo census

Window: `time_period=month`, `rule_suite_result=all`, 823 suites total.

| repo | suites | actors (result:count) |
| --- | --- | --- |
| juniper-ml | 509 | `juniper-release-train[bot]`(pass:1), `pcalnon`(bypass:390, fail:1, pass:117) |
| juniper-cascor | 108 | `pcalnon`(bypass:83, pass:25) |
| juniper-cascor-client | 57 | **`dependabot[bot]`(bypass:24)**, `pcalnon`(bypass:27, pass:6) |
| juniper-canopy | 51 | `pcalnon`(bypass:40, pass:11) |
| juniper-data | 41 | `pcalnon`(bypass:27, pass:14) |
| juniper-deploy | 32 | `pcalnon`(bypass:20, pass:12) |
| juniper-cascor-worker | 24 | `pcalnon`(bypass:18, pass:6) |
| juniper-data-client | 17 | `pcalnon`(bypass:9, pass:8) |
| juniper-recurrence | 9 | `pcalnon`(pass:9) |

**`pcalnon` bypassed 614 times in one month.** The handoff's §1 caveat — that a required check
does not constrain the owner, and that `safe_merge` is discipline rather than enforcement — is
not a theoretical point. It is the single most exercised entitlement in the roster.

---

## 3. A near-miss worth keeping — the census that could not find anything

The first run of the census tool reported:

```text
BYPASSES ACTUALLY EXERCISED
  NONE in the retained history window on any of the 9 repos.
```

That output is **wrong**, and acting on it would have removed dependabot's row and broken
dependency updates on all nine repos.

Cause: `GET /repos/{owner}/{repo}/rulesets/rule-suites` takes a **`time_period` parameter that
defaults to `day`**. Omitting it yields a 24-hour census that is formatted, and reads, exactly
like a full one — 35 suites, nine repos, a clean summary, a confident "NONE". The retention
window was never the limit; the query was.

This is the **vacuous-pass class** in its audit form: the machinery ran, reported clean, and
was **structurally incapable of finding the thing it was looking for**. The tell was
present in the output and easy to skim past — every repo's `oldest` column read `2026-08-19`,
one day back, on repos with months of history.

The tool now defaults to `--time-period month` and prints the window on every run, because a
census that cannot state its own coverage is not a census.

---

## 4. What is still open

- **`DeployKey` (null) — IDENTIFY-FIRST, unresolved.** Absent from a month of suites, which is
  *not* identification. It remains the widest entitlement in the roster (push / force-push /
  **delete** `main` past all checks) and nothing here narrows it.
- **`1143301` Copilot SWE Agent.** Absent from the window. The removal argument survives, but
  note it survives on the *same* evidence type that proved insufficient for dependabot —
  absence-from-history. Before removing, check whether it needs branch **creation**; if it
  does, §1 applies to it verbatim and the row is load-bearing for the same reason.
- **`4362741` release-train App — still DO NOT TOUCH.** One `pass` suite in a month is not
  evidence of redundancy. The handoff's trap stands: its recorded justification (the
  `code_quality` deadlock) is refuted, but *void justification ≠ demonstrated redundancy*.
  The named test — arm an archive PR with the row temporarily absent — has not been run.

---

## 5. Reproduction

```bash
python3 util/ad-hoc/2026-08-20_bypass_actor_census.py --time-period month
python3 util/ad-hoc/2026-08-20_creation_rule_scan.py
gh api repos/pcalnon/juniper-cascor-client/rulesets/rule-suites/3625611564
```

> **Retention caveat, stated because §3 exists.** `month` is the widest value the endpoint
> accepts. "Not seen in a month" is exactly that, and must not be written up as "never".
