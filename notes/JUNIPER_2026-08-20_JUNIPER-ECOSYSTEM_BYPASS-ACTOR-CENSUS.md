# Bypass-actor census — the evidence the ml#1012 decision was waiting on

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-20
**Status**: Census COMPLETE; **two later corrections folded in (§3b, §3c)** — `DeployKey`
is IDENTIFIED, and §1's dependabot verdict is WITHDRAWN. Both removal candidates were left
**UNDETERMINED**, on the same absence-from-history evidence §1 itself called insufficient.
**SUPERSEDED 2026-08-22 for both candidates and for `DeployKey`** — see §4 and
[`…_BYPASS-CANDIDATE-DETERMINATION.md`](JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md).
The census's per-repo data (§2) and its two method lessons (§3, §3c) remain valid as written.
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
| `29110` **dependabot[bot]** | bypass 24 / pass 0 — but **all 2026-07-20 → 08-10** | **UNDETERMINED** — §1's verdict is WITHDRAWN, see §3c. It created branches on 08-17 with no suite at all. |
| `1143301` **Copilot SWE Agent** | **absent entirely** | removal argument survives |
| `RepositoryRole 5` **pcalnon** | bypass 614 / pass 208 / fail 1 | **KEEP** — confirms the §1 caveat, emphatically |
| `4362741` release-train App | pass 1 | consistent with *"test it or leave it"*; nothing new |
| `DeployKey` (null) | absent | **IDENTIFIED 2026-08-21 (§3b)** — this operator's own machines, 17 write-enabled keys. Absent from suites because the row is barely exercisable, not because the actor was unknown. |

Tools (both in-repo, re-runnable):
`util/ad-hoc/2026-08-20_bypass_actor_census.py`, `util/ad-hoc/2026-08-20_creation_rule_scan.py`.

---

## 1. ~~Why the dependabot argument fails~~ — **WITHDRAWN 2026-08-21, see §3c**

> **Do not act on this section.** Its reasoning was sound for the configuration in force
> 2026-07-20 → 2026-08-10, which is the whole window its 24 events fall in. Dependabot
> created branches again on 2026-08-17 and produced **no rule suite at all**, so the
> `creation` rule is no longer firing on them and no bypass is being consumed. The error
> was reading a one-month event window as a statement about today without checking whether
> the configuration changed inside it. It did. §3c has the detail.

The original text follows unedited, because the reasoning is still the right shape — it is
the currency of its evidence that failed.


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

## 3b. `DeployKey` — IDENTIFIED 2026-08-21

The one row the census left unresolved, and the widest in the roster. `actor_id: null` means
**any deploy key on that repo**, so the entitlement is exactly as wide as the set of
write-enabled deploy keys — and a repo with none would have an inert row.

**It is not a third party. It is the operator's own machines.**
`util/ad-hoc/2026-08-21_deploykey_bypass_audit.py` matches every repo's deploy keys against
this host's `~/.ssh/*.pub`:

| family | count | matches this host | `added_by` | `last_used` |
| --- | ---: | --- | --- | --- |
| `<repo> deploy key` (+ `local-dev-key` on deploy) | 9 | **yes**, `id_ed25519_gh_*` | `pcalnon` | current |
| `… Deploy Key - Turing` | 8 | no — a second machine | `pcalnon` | **all 2026-05-07** |

17 write-enabled keys across 9 repos. Every one is `read_only: false` and `added_by: pcalnon`.

Confirmed by asking GitHub directly rather than inferring:

```console
$ ssh -T git@github.com-juniper-ml
Hi pcalnon/juniper-ml! You've successfully authenticated, ...
```

`Hi <owner>/<repo>!` is the **deploy-key** response; a user key answers `Hi <user>!`. So this
workstation's every `git push` to these repos authenticates as the DeployKey bypass actor.

> **`last_used` IS NOT A RECENCY SIGNAL — do not retire a key on it.** The juniper-ml key
> reported `last_used: 2026-08-17` immediately after a successful `ssh -T` *and* after ~30
> pushes the same day. The "Turing" family reads 2026-05-07, which is consistent with a
> retired machine but does **not** establish one.

**What the row actually enables, and what it does not.** The primary ruleset is
`~DEFAULT_BRANCH`-scoped, and `juniper-no-direct-push` (`bypass_actors: []`) binds deploy keys
like everyone else — so this row **cannot** enable a direct push to `main`. Pushes to feature
branches are not evaluated at all (zero rule suites on non-`main` refs). The residual is
narrow but real: the primary ruleset's `deletion` and `non_fast_forward` rules on `main`,
which a deploy key bypasses. Whether `no-direct-push`'s `pull_request` rule independently
blocks a *deletion* is **UNTESTED** — and not a thing to test on a live default branch.

**Disposition, for the owner:**

1. **Lowest-risk hygiene, no ruleset edit:** if the "Turing" machine is retired, delete those
   **8 keys**. That narrows the entitlement by nearly half and touches no ruleset.
2. **The row itself:** removal looks low-impact — this host's normal operations (feature-branch
   pushes, `gh`-API merges under a token as `pcalnon`) do not appear to rely on it — but
   "appears not to" is not "does not", and the safe order is (1) first, then re-census.

---

## 3c. CORRECTION to §1 — the dependabot conclusion does not hold as stated

§1 concluded that removing row `29110` **"stops dependency PRs fleet-wide"**, on 24 bypass
events all showing `creation: fail`. That conclusion is **withdrawn**; the evidence does not
support it for the *current* configuration.

All 24 events fall between **2026-07-20 and 2026-08-10**. Dependabot created branches again on
**2026-08-17** (cascor-client #117, #118) and produced **no rule suite at all** — not a bypass,
not a failure, nothing. So its branch creations are no longer being evaluated, and no bypass is
being consumed.

I could not pin the cause: the ruleset's `creation` rule and `~DEFAULT_BRANCH` scoping are
unchanged since at least 2026-08-12, and `do_not_enforce_on_create` is unset in both the
current and historical versions. So **why** it changed is UNDETERMINED — but **that** it
changed is not.

> **The method error, which is the reusable part.** I read a one-month bypass window and drew
> a conclusion about today, without checking whether the ruleset changed *inside* that window.
> It did, on 2026-08-10. This is the trap the kill-forensics doc states explicitly — *"anchor
> on the ruleset version in effect at the event, never the current one"* — applied in reverse:
> I anchored on events and assumed the configuration was constant. **A bypass census is a
> statement about a configuration, and the configuration has a version.**

Current status of the two removal candidates: **both UNDETERMINED**, on the same evidence
type (absence-from-recent-history), which is exactly the standard §1 said was insufficient.

---

## 4. What is still open

> **RESOLVED 2026-08-22 for the first three bullets.** Both candidate rows are DETERMINED,
> and `DeployKey` is decided. See
> [`…_BYPASS-CANDIDATE-DETERMINATION.md`](JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md).
> The determination did **not** come from a wider history window — it came from the ruleset
> **version history**, which makes the scope in force at any past moment readable. §3c's
> UNDETERMINED cause was a scope change from `~ALL` to `~DEFAULT_BRANCH` on 2026-08-10, one
> day outside the interval §3c examined. Only the `4362741` bullet below is still open.

- ~~**`DeployKey` (null) — IDENTIFY-FIRST, unresolved.**~~ **RETAIN, decided 2026-08-22.**
  §3b's identification stands; the operator confirms the 17 keys are two live development
  machines (this workstation plus "Turing", a macOS laptop used away from it). The deletion
  option §3b raised is declined — the second machine is in use, not retired.
- ~~**`1143301` Copilot SWE Agent.**~~ **REMOVABLE** — and the check this bullet asked for was
  run. It does *not* need branch creation under the current scoping: `~DEFAULT_BRANCH` does
  not evaluate `creation` off `main`. Better, the row is shown unnecessary by demonstration
  rather than by absence — Copilot opened ml#629 (2026-07-06) while its row **did not exist**
  on `juniper-ml`.
- ~~**`29110` dependabot[bot]** (§3c)~~ — **REMOVABLE**, on the same two grounds: inert 9/9,
  and 10 PRs created on `juniper-ml` between 2026-05-19 and 2026-07-13 with no row present.
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
