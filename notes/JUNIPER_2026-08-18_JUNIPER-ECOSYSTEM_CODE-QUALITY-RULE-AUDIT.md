# `code_quality` Branch-Ruleset Rule — Fleet Audit

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (all 9 repos, owner `pcalnon`)
**Author**: Paul Calnon
**Status**: AUDIT — read-only; nothing was modified
**Date**: 2026-08-18
**Auditor lens**: correctness of an internal register claim, verified against the live GitHub API

---

## 0. Bottom line

**The register's claim is FALSE.** Not overstated — false in its central assertion, and false in its
causal attribution.

| Register assertion | Verdict | Basis |
|---|---|---|
| `code_quality` "carries `{severity: errors}` with no reporting tool" | **Half-true, but a category error** | The parameters are exactly that (§2), but `code_quality` has **no tools parameter by design** — it is not a bring-your-own-tool rule (§3). |
| "…so every *non-bypass* auto-merge waits forever" | **PROVEN FALSE** | `code_quality` evaluated **`pass` 779 times and `fail` 0 times** across 785 rule suites in 9 repos over a 30-day window (§4). A non-owner App's armed auto-merge fired in **3 m 07 s** with the suite recording `result: pass` on all 8 rules (§5). |
| "…is why bypass actors accumulate" | **PROVEN FALSE** | The blocker that actually failed on the cited PRs was the **`update` ("Restrict updates") rule**, whose failure detail is literally `"Cannot update this protected ref."` (§6). It was removed 2026-08-10; auto-merge started firing hands-free 4 days later, with `code_quality` untouched. |
| "Fixing it … is higher leverage than any individual removal" | **FALSE** | There is nothing to fix. The rule is inert. |
| The supporting probe, "probe-confirmed on ml#864" | **INVALID EVIDENCE** | The probe commit was **unsigned** against an active `required_signatures` rule, and the `update` rule was simultaneously in force. Two sufficient non-`code_quality` blockers; the probe isolated nothing (§7). |

**Recommended action: DO NOTHING to the `code_quality` rule.** Leave it in place on all 9 repos.
Do not attach a tool (there is no tool slot). Do not drop it (it costs nothing, and dropping it is a
9-repo ruleset write with a non-zero chance of clobbering something). The only warranted action is
**documentation repair** — three notes documents still assert the false claim and are still being read
and cited (§9, finding CQ-7).

---

## 1. Scope and checklist

**Scope.** The `code_quality` rule on the `main` branch ruleset of the 9 owner-`pcalnon` repos:
`juniper-ml`, `juniper-cascor`, `juniper-canopy`, `juniper-data`, `juniper-data-client`,
`juniper-cascor-client`, `juniper-cascor-worker`, `juniper-deploy`, `juniper-recurrence`.

**Method.** Read-only. Every claim below carries a `gh api` command + output, a `file:line`, or a
fetched URL + excerpt. No ruleset, repo setting, PR, issue, or file was modified other than this one
document. All API calls were `GET` (the only exception being `gh api graphql` read queries).

| ID | Checklist item | Pass criterion | Result |
|----|----------------|----------------|--------|
| C1 | Is `code_quality` a real, documented ruleset rule type? | Named in GitHub's own docs | **Verified pass** (§3) |
| C2 | Exact parameters on each of the 9 repos | Recorded verbatim; differences noted | **Verified** — identical everywhere (§2) |
| C3 | Does the rule accept a reporting-tool parameter? | Schema inspected | **Verified: it does not** (§3) |
| C4 | Has `code_quality` ever evaluated to a failure? | Per-rule evaluation census | **Verified fail-free**: 0/785 (§4) |
| C5 | Is a non-bypass evaluation reachable, and does it satisfy the rule? | A `pass` suite / non-owner merge exists | **Verified pass** (§5) |
| C6 | Is any PR currently blocked, or auto-merge armed-but-unfired, because of it? | Live merge-state census | **Verified: none** (§8) |
| C7 | What actually caused the 2026-07-29 incident the register cites? | Per-rule evaluation of the cited merges | **Verified: the `update` rule** (§6, §7) |
| C8 | Under what conditions *would* the rule bite? | Product docs + repo config | **Conditional** (§10) |
| C9 | Did it ever block before 2026-07-19? | Rule-suite history | **COULD NOT VERIFY** — API retention (§11) |

---

## 2. What is configured (C2) — verified, identical on all 9

```bash
gh api /repos/pcalnon/<repo>/rules/branches/main --jq '.[]|select(.type=="code_quality")'
```

| Repo | Ruleset id | `code_quality` parameters (verbatim) |
|---|---|---|
| juniper-ml | 13805432 | `{"parameters":{"severity":"errors"},"ruleset_id":13805432,"ruleset_source":"pcalnon/juniper-ml","ruleset_source_type":"Repository","type":"code_quality"}` |
| juniper-cascor | 15081045 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |
| juniper-canopy | 14249530 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |
| juniper-data | 14748749 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |
| juniper-data-client | 13316681 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |
| juniper-cascor-client | 13490605 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |
| juniper-cascor-worker | 14250447 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |
| juniper-deploy | 14715370 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |
| juniper-recurrence | 20634527 | `{"parameters":{"severity":"errors"},…,"type":"code_quality"}` |

**No divergence.** The single parameter `severity: errors` is byte-identical across the fleet.

Contrast, same endpoint, same repo:

```
$ gh api /repos/pcalnon/juniper-ml/rules/branches/main --jq '.[]|select(.type=="code_scanning")'
{"parameters":{"code_scanning_tools":[{"alerts_threshold":"errors","security_alerts_threshold":"high_or_higher","tool":"CodeQL"}]},…,"type":"code_scanning"}
```

`code_scanning` carries a `code_scanning_tools` array. `code_quality` carries no such key — and that is
the point the register misread (see §3).

**Provenance.** `code_quality` is not new and was not added by accident. Ruleset version history shows it
present in **every recorded version** of all 9 rulesets, back to the earliest snapshot in each:

```bash
gh api /repos/pcalnon/juniper-ml/rulesets/13805432/history?per_page=100
gh api /repos/pcalnon/juniper-ml/rulesets/13805432/history/<version_id>
```

- juniper-data-client `v29814253`, **2026-02-27T04:10:30-06:00** — earliest sighting anywhere.
- juniper-ml `v30768045`, 2026-03-11T18:31:56-05:00 — present in the *second* version of the ruleset
  (the first, `v30767869`, 18:28 the same evening, had only `deletion, non_fast_forward`).
- juniper-recurrence is the only repo with a gap: dropped `v46374240` (2026-08-12T17:52), restored
  `v46498547` (2026-08-13T20:34). It is present today.

That is ~5.7 months of continuous presence with the merge pipeline running normally throughout.

---

## 3. What the rule *is* (C1, C3)

### 3.1 It is documented — as a product rule, not a BYO-tool rule

Verbatim source, `github/docs` repo, `content/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets.md:209-217`:

```bash
gh api /repos/github/docs/contents/content/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets.md --jq '.content' | base64 -d
```

> ```
> 209: ## Require code quality results
> 210:
> 211: If your repositories are configured with {% data variables.product.prodname_code_quality %}, you can use rulesets to prevent pull requests from being merged when one of the following conditions is met:
> 212:
> 213: * Analysis is still in progress.
> 214: * Analysis fails for any reason, for example: you have exhausted your budget for actions minutes.
> 215: * {% data variables.product.prodname_code_quality_short %} found a result of a severity of the level defined in the ruleset, or a higher severity.
> 216:
> 217: For more information, see [AUTOTITLE](https://docs.github.com/en/code-security/concepts/code-quality/code-quality) and [AUTOTITLE](https://docs.github.com/en/code-security/how-tos/maintain-quality-code/set-pr-thresholds).
> ```

Read the conditional: **"If your repositories are configured with GitHub Code Quality"**. All three
blocking conditions are predicated on that feature running. With the feature off there is no analysis
to be in progress, no analysis to fail, and no result to exceed a severity — so **none of the three
blocking conditions can be met, and the rule passes vacuously**. That is precisely what §4 measures.

Note also that the adjacent "Restrict code coverage" rule carries an explicit
`{% data variables.release-phases.public_preview %}` note at line 222 while "Require code quality
results" does **not** — consistent with GitHub Code Quality having reached GA.

### 3.2 It has no `tools` parameter — the register's category error

`code_scanning` names its tools because code scanning is a **multi-vendor SARIF ingest**: the rule must
be told which uploader to wait for. `code_quality` names none because it gates on exactly one
first-party analyzer — GitHub Code Quality — that you either have enabled or you do not.

The register's framing ("no reporting tool … so it waits forever on a check that never arrives")
transplants `code_scanning`'s failure mode onto a rule whose schema has no such slot. Verified by
inspection of the live parameters (§2) plus:

- **REST API reference** (<https://docs.github.com/en/rest/repos/rules>): the documented rule-type enum
  lists 23 values — `creation, update, deletion, required_linear_history, merge_queue,
  required_deployments, required_signatures, pull_request, required_status_checks, non_fast_forward,
  commit_message_pattern, commit_author_email_pattern, committer_email_pattern, branch_name_pattern,
  tag_name_pattern, workflows, code_scanning, copilot_code_review, license_compliance_scanning,
  file_path_restriction, max_file_path_length, file_extension_restriction, max_file_size` — and
  **`code_quality` is not among them**.
- **GraphQL introspection**, live 2026-08-18:

  ```bash
  gh api graphql -f query='{ __type(name:"RepositoryRuleType") { enumValues { name } } }'
  ```

  returns 32 values including `CODE_SCANNING` and `COPILOT_CODE_REVIEW` but **not** `CODE_QUALITY`.

So `code_quality` is a UI-configurable, REST-emitted rule that the machine-readable schema references
have not yet caught up with. It is real and documented as a *feature*; it is undocumented as a *type*.

### 3.3 What GitHub Code Quality is, and its relation to Copilot code review

`github/docs`, `content/code-security/concepts/code-quality/code-quality.md`:

> "{% data variables.product.prodname_code_quality %} analyzes your code for quality and coverage
> issues and delivers {% data variables.product.prodname_copilot_short %}-powered fixes you can apply
> in one click."
>
> "## Availability and billing — Usage costs are determined by: * A per-seat license fee based on
> active committers."
>
> "> [!NOTE] On pull requests, {% data variables.product.prodname_code_quality_short %} posts
> rules-based {% data variables.product.prodname_codeql %} findings only. If you also want AI-powered
> reviews of your pull requests, you can enable {% data variables.copilot.copilot_code-review %}
> separately."

`data/reusables/gated-features/code-quality-availability.md` (the `product:` gate on both the concept
and the enablement how-to):

> ```
> {% ifversion fpt or ghec %}
> {% data variables.product.prodname_team %} or {% data variables.product.prodname_ghe_cloud %}
> {% endif %}
> ```

i.e. **GitHub Team or GitHub Enterprise Cloud**. And `content/code-security/how-tos/maintain-quality-code/enable-code-quality.md`:

> "## Prerequisites
> * An enterprise owner must have allowed {% data variables.product.prodname_code_quality_short %} in
>   your enterprise. …
> * {% data variables.product.prodname_actions %} must be enabled …"
> "1. Click **Enable code quality**."

It is an explicit, licensed, opt-in enablement — not something a repo acquires passively.

**Copilot code review is a separate rule.** `copilot_code_review` appears in both the REST enum and the
GraphQL enum, and it was literally a distinct rule on one of these repos: juniper-data-client's ruleset
carried `RULES=deletion,non_fast_forward,required_signatures,required_status_checks,code_scanning,copilot_code_review,code_quality`
from `v29814253` (2026-02-27) through `v44817588` (2026-07-29), dropped by `v46135309` (2026-08-10).
So `code_quality` ≠ Copilot code review; they coexisted on the same ruleset.

GitHub changelog, 2026-08-07, *"GitHub Code Quality no longer adds Copilot as a reviewer"*
(<https://github.blog/changelog/2026-08-07-github-code-quality-no-longer-adds-copilot-as-a-reviewer/>):

> "When Code Quality became generally available on July 20, 2026, it automatically created a repository
> ruleset named `"Code Quality Copilot review for default branch"` that targeted the default branch…
> You told us that adding a reviewer should be your choice, so we've reversed that."

**No such auto-created ruleset exists on any of the 9 repos** — each has exactly one branch ruleset,
its own hand-made `<repo>-rules`:

```bash
gh api /repos/pcalnon/<repo>/rulesets --jq '.[]|"id=\(.id) name=\"\(.name)\""'
```

```
juniper-ml            id=13805432 name="juniper-ml-rules"
juniper-cascor        id=15081045 name="juniper-cascor-rules"
juniper-canopy        id=14249530 name="juniper-canopy-rules"
juniper-data          id=14748749 name="juniper-data-rules"
juniper-data-client   id=13316681 name="data-client-rules"
juniper-cascor-client id=13490605 name="juniper-cascor-client-rules"
juniper-cascor-worker id=14250447 name="juniper-cascor-worker-rules"
juniper-deploy        id=14715370 name="juniper-deploy-rules"
juniper-recurrence    id=20634527 name="juniper-recurrent-rules"
```

That is corroborating (not conclusive) evidence that GitHub Code Quality is **not** enabled here.

---

## 4. Has it ever blocked anything? (C4) — 785-suite census, zero failures

### 4.1 Method, and why rule suites are the right instrument

A **rule suite** records the per-rule evaluation of a ref update. Critically, the per-rule results are
computed **independently of bypass**: bypass only decides whether the push is *allowed*, and shows up as
the suite-level `result: bypass`. Proof that the two axes are independent, from this very dataset: the
owner holds `RepositoryRole 5 : always` bypass on all 9 repos, yet **141 of his suites are `result:
pass`** (nothing failed, so no bypass was needed) and 620 are `result: bypass` (something failed).

**Therefore every bypass suite is a free counterfactual**: it tells you exactly what would have happened
to a non-bypass actor. That is what makes this question answerable at all.

Default `time_period` on the endpoint is `day`; the maximum is `month`. All figures below use `month`.

```bash
gh api "/repos/pcalnon/<repo>/rulesets/rule-suites?per_page=100&page=N&time_period=month" --jq '.[].id'
gh api "/repos/pcalnon/<repo>/rulesets/rule-suites/<id>"
```

Sweep script (scratch, not committed): every suite id in the month window for all 9 repos, then the
detail for each. **785 suites**, window `2026-07-19T03:05:38-05:00` → `2026-08-18T16:07:00-05:00`.

### 4.2 The result

| rule | `pass` | `fail` | absent |
|---|---:|---:|---:|
| **`code_quality`** | **779** | **0** | 6 |
| `code_scanning` | 566 | **173** | 46 |
| `required_status_checks` | 545 | **240** | 0 |

Per repo, `code_quality`:

```
     47 juniper-canopy        pass
     98 juniper-cascor        pass
     55 juniper-cascor-client pass
     22 juniper-cascor-worker pass
     37 juniper-data          pass
     13 juniper-data-client   pass
     26 juniper-deploy        pass
    480 juniper-ml            pass
      6 juniper-recurrence    ABSENT     <- the 2026-08-12 → 08-13 removal window
      1 juniper-recurrence    pass
```

**Zero failures, in every repo, in every suite.** The 6 `ABSENT` rows are juniper-recurrence during the
36 hours the rule was removed from its ruleset; the one recurrence suite *after* restoration
(`3677136215`, 2026-08-13T20:43:18-05:00) records `code_quality: pass` and suite `result: pass` — so
restoring it re-blocked nothing.

Independent confirmation from a different query path (the endpoint's own `rule_suite_result` filter):

```bash
gh api "/repos/pcalnon/<repo>/rulesets/rule-suites?per_page=100&time_period=month&rule_suite_result=fail" --jq 'length'
```

returns **0 for all 9 repos**. No ref update was blocked outright anywhere in the window.

### 4.3 `code_quality` never even emits a `details` string

Across all 785 suites, the `details` field on the `code_quality` evaluation is empty **785/785 times**.
Compare the `code_scanning` failures, which are voluble:

```
  23  Waiting for Code Scanning results. Code Scanning may not be configured for the target branch.
   2  Code scanning is waiting for results from CodeQL for the commit 27c6fb3.
   1  CodeQL has detected 2 alerts blocking this code from being merged.
   1  Code scanning is waiting for results from gitleaks for the commits fd86df8 or 403e18e.
   …
```

That first line — *"Waiting for Code Scanning results. Code Scanning may not be configured for the
target branch."* — **is** the "no reporting tool → waits forever" pathology the register described. It
occurred 23 times, on **juniper-deploy (19)** and **juniper-cascor-client (4)**. It belongs to
`code_scanning`. The register attached the symptom to the wrong rule.

### 4.4 Exhibit A — the two rules side by side, same commit, same evaluation

```bash
gh api /repos/pcalnon/juniper-ml/rulesets/rule-suites/3720498723
```

> ```json
> {"id":3720498723,"actor_name":"pcalnon","after_sha":"d163f079…","ref":"refs/heads/main",
>  "pushed_at":"2026-08-18T04:15:27-05:00","result":"bypass","rule_evaluations":[
>   {"enforcement":"active","result":"fail","rule_type":"code_scanning",
>    "details":"Code scanning is waiting for results from CodeQL for the commit d163f07."},
>   {"enforcement":"active","result":"fail","rule_type":"required_status_checks",
>    "details":"15 of 15 required status checks are expected."},
>   {"enforcement":"active","result":"fail","rule_type":"pull_request",
>    "details":"Changes must be made through a pull request."},
>   {"enforcement":"active","result":"pass","rule_type":"required_signatures"},
>   {"enforcement":"active","result":"pass","rule_type":"creation"},
>   {"enforcement":"active","result":"pass","rule_type":"code_quality"},
>   …]}
> ```

One evaluation. One commit. `code_scanning` **fails**, waiting on a tool that has not reported.
`code_quality` **passes**. If the register's model were right, `code_quality` would have failed here
identically. It did not. This single suite falsifies the claim.

### 4.5 Exhibit B — three-way contrast on juniper-deploy

```bash
gh api /repos/pcalnon/juniper-deploy/rulesets/rule-suites/3618801259
```

> ```json
> {"id":3618801259,"actor_name":"pcalnon","ref":"refs/heads/main",
>  "pushed_at":"2026-08-10T03:41:23-05:00","result":"bypass","evals":[
>   {"rule_type":"update","result":"fail","details":"Cannot update this protected ref."},
>   {"rule_type":"code_scanning","result":"fail",
>    "details":"Waiting for Code Scanning results. Code Scanning may not be configured for the target branch."},
>   {"rule_type":"required_signatures","result":"pass","details":null},
>   {"rule_type":"code_quality","result":"pass","details":null},
>   {"rule_type":"required_status_checks","result":"pass","details":null},
>   {"rule_type":"pull_request","result":"pass","details":null},
>   {"rule_type":"creation","result":"pass","details":null},
>   {"rule_type":"non_fast_forward","result":"pass","details":null},
>   {"rule_type":"deletion","result":"pass","details":null}]}
> ```

Three distinct behaviours in one evaluation: a categorically-unsatisfiable rule (`update`), a
waiting-on-an-absent-tool rule (`code_scanning`), and an inert rule (`code_quality`).

---

## 5. Is the mechanism reachable, and is it satisfied? (C5) — yes, by a non-owner bot

The task asked whether a **non-bypass** merge has ever occurred and whether `code_quality` was satisfied
on it. It has, and it was.

```bash
gh api /repos/pcalnon/juniper-ml/rulesets/rule-suites/3689919174
```

> ```json
> {"id":3689919174,"actor_id":307885744,"actor_name":"juniper-release-train[bot]",
>  "after_sha":"a5d02238ac056df6d7a01089510c980f9ff73da9","ref":"refs/heads/main",
>  "repository_name":"juniper-ml","pushed_at":"2026-08-14T18:08:12-05:00","result":"pass",
>  "rule_evaluations":[
>   {"enforcement":"active","result":"pass","rule_type":"required_signatures"},
>   {"enforcement":"active","result":"pass","rule_type":"pull_request"},
>   {"enforcement":"active","result":"pass","rule_type":"creation"},
>   {"enforcement":"active","result":"pass","rule_type":"required_status_checks"},
>   {"enforcement":"active","result":"pass","rule_type":"code_quality"},
>   {"enforcement":"active","result":"pass","rule_type":"code_scanning"},
>   {"enforcement":"active","result":"pass","rule_type":"non_fast_forward"},
>   {"enforcement":"active","result":"pass","rule_type":"deletion"}]}
> ```

Suite `result: **pass**` — **not** `bypass`. All eight rules satisfied, `code_quality` among them, by an
actor who is not the owner.

The corresponding PR:

```bash
gh pr view 1108 --repo pcalnon/juniper-ml --json number,title,mergedAt,mergedBy,author,autoMergeRequest
```

> ```json
> {"number":1108,"title":"release-notes: juniper-cascor v0.9.0",
>  "author":{"login":"app/juniper-release-train"},
>  "autoMergeRequest":{"enabledAt":"2026-08-14T23:05:06Z",
>                      "enabledBy":{"login":"app/juniper-release-train"},"mergeMethod":"SQUASH"},
>  "mergedAt":"2026-08-14T23:08:13Z","mergedBy":"app/juniper-release-train"}
> ```

**Auto-merge armed by a bot at 23:05:06Z; fired at 23:08:13Z. Elapsed: 3 minutes 7 seconds.** The
register says such a merge "waits forever."

And `pass` suites — full-ruleset satisfaction with no bypass needed — exist in **every one of the 9
repos** (141 total in the window): juniper-ml 84, juniper-cascor 15, juniper-data 10, juniper-canopy 7,
juniper-recurrence 7, juniper-deploy 6, juniper-cascor-client 4, juniper-cascor-worker 4,
juniper-data-client 4.

---

## 6. What actually blocked auto-merge: the `update` rule (C7)

### 6.1 The rule

GitHub docs, *Available rules for rulesets*, "Restrict updates":

> "only users with bypass permissions can push to branches or tags whose name matches the pattern you
> specify."

All 9 rulesets target `~DEFAULT_BRANCH`. With `update` active, **no non-bypass actor can update `main`
by any means, including a PR merge.** That is a categorical, permanent, unsatisfiable-by-construction
block. Its failure detail is `"Cannot update this protected ref."` — no check, no tool, no waiting; a
flat denial.

### 6.2 It was in force during the entire period the register describes

From ruleset version history (`…/rulesets/<id>/history/<version_id>`):

| Repo | `update` present through | first version without `update` |
|---|---|---|
| juniper-ml | `v44817590` 2026-07-29T16:27:30-05:00 | `v46060919` 2026-08-10T03:21:29-05:00 |
| juniper-cascor | `v46072599` 2026-08-10T05:24:38-05:00 | `v46123775` 2026-08-10T13:43:20-05:00 |
| juniper-canopy | `v46072598` 2026-08-10T05:24:38-05:00 | `v46073441` 2026-08-10T05:39:26-05:00 |
| juniper-data | `v44737976` 2026-07-29T00:11:03-05:00 | `v46133733` 2026-08-10T15:25:31-05:00 |
| juniper-cascor-worker | `v46138316` 2026-08-10T16:18:46-05:00 | `v46148578` 2026-08-10T19:36:44-05:00 |
| juniper-deploy | `v44737985` 2026-07-29T00:11:09-05:00 | `v46135854` 2026-08-10T15:43:33-05:00 |
| juniper-data-client | never had it | — |
| juniper-cascor-client | never had it | — |
| juniper-recurrence | never had it (earliest recorded version 2026-08-10) | — |

The whole fleet shed `update` on **2026-08-10**.

### 6.3 The decisive exhibit — the exact PRs the register cites

The operator runbook asserts, at
`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md:565-571`:

> "- **Ruleset `code_quality` blocked the armed auto-merge (2026-07-29) — resolved via App bypass actor.**
>    The juniper-ml ruleset's `code_quality` (severity: errors) rule has **no reporting tool behind it**, so
>    it can never be satisfied and every **non-bypass** merge stays `BLOCKED` even with all required checks
>    green, a Verified commit, and a current base (archive PRs #860–#863; probe-confirmed on ml#864)."

Those four archive PRs merged at 06:01:03Z / 06:01:06Z / 06:01:10Z / 06:01:13Z on 2026-07-29, producing
four rule suites at 01:01:02 / 01:01:06 / 01:01:09 / 01:01:13 CDT. Take the first:

```bash
gh pr view 860 --repo pcalnon/juniper-ml --json mergeCommit,mergedAt
# {"mergedAt":"2026-07-29T06:01:03Z","sha":"580bda47"}

gh api /repos/pcalnon/juniper-ml/rulesets/rule-suites/3485854412
```

> ```json
> {"id":3485854412,"actor_name":"pcalnon","after_sha":"580bda47",
>  "pushed_at":"2026-07-29T01:01:02-05:00","result":"bypass","evals":[
>   {"rule_type":"update","result":"fail","details":"Cannot update this protected ref."},
>   {"rule_type":"required_signatures","result":"pass","details":null},
>   {"rule_type":"creation","result":"pass","details":null},
>   {"rule_type":"required_status_checks","result":"pass","details":null},
>   {"rule_type":"code_quality","result":"pass","details":null},
>   {"rule_type":"code_scanning","result":"pass","details":null},
>   {"rule_type":"non_fast_forward","result":"pass","details":null},
>   {"rule_type":"deletion","result":"pass","details":null}]}
> ```

`after_sha` `580bda47` **is** ml#860's merge commit. At the exact moment the runbook says `code_quality`
blocked the merge, GitHub's own per-rule evaluation records `code_quality: pass` and **`update: fail —
"Cannot update this protected ref."` as the sole failing rule.**

The same pattern one ruleset-generation later, on ml#1052's merge:

```bash
gh api /repos/pcalnon/juniper-ml/rulesets/rule-suites/3617375022
```

> ```json
> {"actor_name":"pcalnon","after_sha":"8e4f74cc","pushed_at":"2026-08-10T01:26:38-05:00","result":"bypass",
>  "evals":[{"rule_type":"update","result":"fail","details":"Cannot update this protected ref."},
>           {"rule_type":"required_signatures","result":"pass"},{"rule_type":"creation","result":"pass"},
>           {"rule_type":"required_status_checks","result":"pass"},{"rule_type":"code_quality","result":"pass"},
>           {"rule_type":"code_scanning","result":"pass"},{"rule_type":"non_fast_forward","result":"pass"},
>           {"rule_type":"deletion","result":"pass"}]}
> ```

Everything green except `update`.

### 6.4 The behavioural timeline corroborates it

Every release-train archive PR on juniper-ml, arm time vs merge time:

```bash
gh pr list --repo pcalnon/juniper-ml --state merged --limit 100 --search "author:app/juniper-release-train" \
  --json number,mergedAt,mergedBy,autoMergeRequest
```

| PR | armed by App | merged | merged by | `update` in ruleset? |
|---|---|---|---|---|
| #860 | 2026-07-29T05:25:34Z | 06:01:03Z | **pcalnon** | yes |
| #861 | 2026-07-29T05:27:15Z | 06:01:06Z | **pcalnon** | yes |
| #862 | 2026-07-29T05:28:40Z | 06:01:10Z | **pcalnon** | yes |
| #863 | 2026-07-29T05:42:48Z | 06:01:13Z | **pcalnon** | yes |
| #1039 | 2026-08-09T08:01:49Z | 2026-08-09T23:07:51Z | **pcalnon** | yes |
| #1041 | 2026-08-09T08:54:16Z | 2026-08-09T23:07:55Z | **pcalnon** | yes |
| #1043 | 2026-08-09T09:09:37Z | 2026-08-09T23:07:59Z | **pcalnon** | yes |
| #1051 | 2026-08-10T00:11:57Z | 2026-08-10T06:28:43Z | **pcalnon** | yes (removed 08:21Z) |
| #1052 | 2026-08-10T00:27:03Z | 2026-08-10T06:26:38Z | **pcalnon** | yes (removed 08:21Z) |
| **#1108** | **2026-08-14T23:05:06Z** | **2026-08-14T23:08:13Z** | **app/juniper-release-train** | **no** |

Armed auto-merge never fired while `update` was in the ruleset — the owner always had to merge by hand.
The first armed auto-merge after `update` was removed fired **on its own, in 3 minutes**.
`code_quality` was present, unchanged, at `severity: errors`, on **both** sides of that line.

Note the sequencing that breaks the register's causal story: the release-train App bypass
(`Integration 4362741`, `pull_request` mode) was added at `v44817590`, **2026-07-29T16:27:30-05:00** —
i.e. 15 hours *after* the #860–#863 merges. It cured the symptom because it granted bypass over
`update`, which requires bypass by definition. Attributing the cure to circumventing `code_quality` is
an inference with no supporting evaluation anywhere in the data.

---

## 7. The probe (ml#864) proves nothing (C7)

The runbook's "probe-confirmed on ml#864" is the only purpose-built experiment behind the claim. It is
confounded twice over.

```bash
gh pr view 864 --repo pcalnon/juniper-ml --json number,title,state,mergeStateStatus,createdAt,closedAt
# {"number":864,"title":"probe: auto-merge blocker diagnosis (temporary)","state":"CLOSED",
#  "mergeStateStatus":"BLOCKED","createdAt":"2026-07-29T15:43:59Z","closedAt":"2026-07-29T15:49:01Z"}
```

All 20 checks were `SUCCESS` or `NEUTRAL` (including `Analyze (python)`, `CodeQL`, and `Quality Gate`),
and GraphQL shows `reviewThreads: {nodes: []}` — no unresolved conversation. So far, consistent with
the runbook's reading. But:

**Confound 1 — the probe commit is unsigned.**

```bash
gh api /repos/pcalnon/juniper-ml/pulls/864/commits --jq '[.[]|{sha:.sha[0:8],verified:.commit.verification.verified,reason:.commit.verification.reason}]'
# [{"reason":"unsigned","sha":"03515de8","verified":false}]
```

**Confound 2 — the ruleset in force contained both `required_signatures` and `update`.** The probe ran
15:43–15:49 UTC on 2026-07-29; the ruleset version in force was `v44737966`
(2026-07-29T00:10:58-05:00), the next edit being `v44817590` at 16:27 CDT — after the probe closed:

```bash
gh api /repos/pcalnon/juniper-ml/rulesets/13805432/history/44737966
```

> `"rules":[{"type":"deletion"},{"type":"non_fast_forward"},{"type":"code_scanning",…},
> {"type":"code_quality","parameters":{"severity":"errors"}},{"type":"required_status_checks",…},
> {"type":"required_signatures"},{"type":"update"},{"type":"creation"}]`

An unsigned commit against an active `required_signatures` rule is a sufficient blocker on its own — a
failure mode the *same runbook* documents four lines earlier at
`…RELEASE-TRAIN-OPERATOR-RUNBOOK.md:555-563` ("A plain runner-side `git commit` is unsigned and left an
all-green archive PR BLOCKED behind that rule … 2026-07-23 run 30051952226 / ml#707"). `update` is a
second, independent sufficient blocker. The probe could not distinguish among three candidates and did
not try; it observed `BLOCKED` and assigned it to the rule the author already suspected.

---

## 8. Live state today (C6) — nothing is stuck

Open-PR census, all 9 repos, 2026-08-18 (`mergeable` warmed with a first GraphQL call, then re-read):

- **29 open PRs.** Every one has **all commits signature-verified**.
- **2 are `CLEAN`** — `juniper-ml#1168` and `juniper-deploy#182`. `CLEAN` means mergeable with **no
  blocking rule**. A PR cannot reach `CLEAN` if `code_quality` is unsatisfiable.

  ```bash
  gh api graphql -f query='{ repository(owner:"pcalnon",name:"juniper-ml"){ pullRequest(number:1168){ mergeable mergeStateStatus } } }'
  # {"mergeable":"MERGEABLE","mergeStateStatus":"CLEAN"}
  ```

- **9 are `BEHIND`** — stale branches under `strict_required_status_checks_policy: true`. Unrelated.
- **16 are `BLOCKED`** — each with required checks `QUEUED` / `IN_PROGRESS` / failing. Example,
  `juniper-ml#1147`: commits `verified: true`, and 8 checks pending
  (`Pre-commit (Python 3.13)` IN_PROGRESS, `Pre-commit (Python 3.14)` QUEUED, `Sequence Safety` QUEUED,
  `Security Scan` QUEUED, …). Ordinary transient state.

**Important control**: `mergeStateStatus` is *not* discounted by the viewer's bypass. The owner holds
`always` bypass yet still sees `#1147` as `BLOCKED`. So `#1168`'s `CLEAN` is a genuine "all rules
satisfied" signal, not a bypass artefact.

**Zero open PRs anywhere have auto-merge armed** — so there is no "armed but never fired" case in
existence right now:

```bash
gh pr list --repo pcalnon/<repo> --state open --limit 60 --json number,autoMergeRequest \
  --jq '.[]|select(.autoMergeRequest!=null)'   # empty for all 9
```

The owner's observation that **CodeQL is enabled and reporting on all repos** is confirmed:

```bash
gh api /repos/pcalnon/<repo>/code-scanning/analyses?per_page=5 --jq '[.[]|"\(.tool.name)@\(.created_at[0:10])"]|unique'
```

```
juniper-ml            CodeQL@2026-08-18
juniper-cascor        Bandit@2026-08-18 CodeQL@2026-08-18
juniper-canopy        CodeQL@2026-08-17 CodeQL@2026-08-18
juniper-data          Bandit@2026-08-18 CodeQL@2026-08-18
juniper-data-client   Bandit@2026-08-17 Bandit@2026-08-18 CodeQL@2026-08-18
juniper-cascor-client Bandit@2026-08-17 CodeQL@2026-08-17 CodeQL@2026-08-18
juniper-cascor-worker Bandit@2026-08-17 Bandit@2026-08-18 CodeQL@2026-08-18
juniper-deploy        CodeQL@2026-08-18
juniper-recurrence    CodeQL@2026-08-17 CodeQL@2026-08-18
```

---

## 9. Findings

### CQ-1 — `code_quality` has never blocked anything — **major** (documentation defect)

**Location**: `notes/JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md:32`;
`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md:565-571` and `:1009-1015`;
`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md:515-529`.

**Problem**: All three assert the rule "can never be satisfied" / "blocks all non-bypass merges
(fleet-wide)".

**Evidence**: §4 — 779 `pass` / **0 `fail`** across 785 rule suites, 9 repos, 2026-07-19 → 2026-08-18;
`rule_suite_result=fail` returns 0 suites for all 9; §4.4 shows `code_scanning` failing and
`code_quality` passing in the same evaluation of the same commit.

**Fix**: Correct the three documents (or mark them superseded by
`notes/JUNIPER_2026-08-17_JUNIPER-ML_HELD-PLANNING-ITEMS-REGISTER.md` §1 and by this audit). No
ruleset change.

### CQ-2 — the cited proof (ml#864) is invalid — **major**

**Location**: `…RELEASE-TRAIN-OPERATOR-RUNBOOK.md:568` ("probe-confirmed on ml#864").

**Problem**: The probe is presented as isolating `code_quality`. It isolates nothing.

**Evidence**: §7 — probe commit `03515de8` is `verified: false, reason: "unsigned"` while
`required_signatures` was active; and `update` was simultaneously active
(ruleset `v44737966`, in force for the probe's entire 6-minute life).

**Fix**: Strike the probe as evidence. If a future probe is wanted, it must use a **GitHub-signed** API
commit and be run against a ruleset with `update` absent — otherwise it re-confounds.

### CQ-3 — the real blocker was the `update` rule — **major** (mis-attributed root cause)

**Problem**: The "waits forever" symptom is real and was correctly observed; the cause was
misidentified.

**Evidence**: §6.3 — rule suite `3485854412`, the merge of ml#860 (`after_sha 580bda47`, one of the four
PRs the runbook names), records `update: fail — "Cannot update this protected ref."` as the **only**
failing rule, with `code_quality: pass`. §6.4 — armed auto-merge fired hands-free (3 m 07 s) on the
first attempt after `update` was removed fleet-wide on 2026-08-10, with `code_quality` unchanged.

**Fix**: Record `update` as the root cause. Consequence: the recorded justification for the
`Integration 4362741 : pull_request` bypass row ("a workaround for that mis-wired rule",
`BYPASS-ACTOR-RESEARCH.md:26,32`) is **void** — the row worked because `update` requires bypass. This
does **not** by itself mean the row should be removed; re-derive its necessity from current behaviour
(§12) before acting.

### CQ-4 — "no reporting tool" is a category error — **minor**

**Evidence**: §2 (no `tools` key in the live parameters), §3.2 (absent from both the REST rule-type enum
and the GraphQL `RepositoryRuleType` enum), §3.1 (docs: the rule gates on the GitHub Code Quality
*feature*, not a nominated tool). `code_quality` cannot be "wired to a tool"; option (a) of
`BYPASS-ACTOR-RESEARCH.md:51` ("attach a code-quality reporting tool") is not a thing that exists.

### CQ-5 — the described pathology is real, but belongs to `code_scanning` — **minor**

**Evidence**: §4.3 — 23 suites carry `code_scanning` detail *"Waiting for Code Scanning results. Code
Scanning may not be configured for the target branch."*, on juniper-deploy (19) and juniper-cascor-client
(4). §4.5 shows it and `code_quality: pass` in one evaluation.

**Fix**: If any residual "why doesn't this merge?" energy is to be spent, spend it here — verify each
repo's `code_scanning` tool list matches the analyses it actually uploads. Both repos show current
CodeQL analyses today (§8), so this may already be resolved; the historical rows are the evidence that
it was once live.

### CQ-6 — stale note: recurrence `code_quality` "unsatisfiable" — **minor**

**Location**: `notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md:561`.

**Problem**: States both `code_scanning` and `code_quality` "were unsatisfiable" on juniper-recurrence
and were removed 2026-08-12 to unblock merging.

**Evidence**: Version history shows `code_scanning` dropped first (`v46359755`, 08-12T15:04) with
`code_quality` retained; `code_quality` dropped separately at `v46374240` (08-12T17:52); **both restored**
at `v46498547` (08-13T20:34). Post-restoration suite `3677136215` (2026-08-13T20:43:18-05:00) records
`code_quality: pass`, `code_scanning: pass`, suite `result: pass`. Restoring `code_quality` re-blocked
nothing; the genuinely unsatisfiable rule there was `code_scanning`. The note's "until then recurrence's
ruleset is 6 rules where the fleet standard is 8" is also stale — recurrence is back to 8.

### CQ-7 — three uncorrected documents still carry the false claim — **minor** (but this is the one action worth taking)

**Evidence**: The 2026-08-17 register corrected §2.4 and recommended "leave it"
(`…HELD-PLANNING-ITEMS-REGISTER.md:16-90`), but `BYPASS-ACTOR-RESEARCH.md:26,32,51`,
`…RELEASE-TRAIN-OPERATOR-RUNBOOK.md:565-571,949,1009-1015`, and
`…STANDING-ITEMS-CLOSEOUT…:515-529,1688,1768` are unchanged and remain linked from the closeout plan's
reference list. A reader arriving via the runbook (the operator-facing document) gets the false version.

### CQ-8 — the register's cited source could not be located — **minor / could not verify**

`…HELD-PLANNING-ITEMS-REGISTER.md:20` attributes the claim to "the 2026-08-15 ruleset register §2.4".
No such file exists under `notes/` (nor anywhere under the Juniper root by that date stamp). The claim
text audited here is the one that **is** in the repo, at `BYPASS-ACTOR-RESEARCH.md:32`, which is
verbatim-equivalent. Flagged so nobody hunts for a missing document.

### CQ-9 — dormant-armed: the one genuine forward risk — **informational / conditional**

**Evidence**: §3.1 — the rule blocks when Code Quality analysis is *in progress*, *fails for any reason
(e.g. exhausted Actions minutes)*, or *finds a result at/above the configured severity*. Configured
severity here is `errors`, on all 9 repos, and `severity: errors` on a fresh analyzer over 9 mature
repos is an unknown-magnitude blast radius.

If GitHub Code Quality is ever enabled — deliberately, or by an org/enterprise-level rollout — these 9
rulesets are **already armed to block on it**, with no soak period and no advisory phase. That is the
opposite of the register's concern, and it is the only reason to think about this rule again.

**Recommendation**: leave the rule; if Code Quality is ever enabled, enable it on **one** repo first and
watch the rule's evaluation before letting it reach the other eight.

### CQ-10 — schema-gap hazard for ruleset tooling — **informational; currently clean**

`code_quality` is emitted by REST but absent from the documented REST rule-type enum and the GraphQL
`RepositoryRuleType` enum (§3.2). Ruleset updates are **full replacement** PUTs, so any tool that
rebuilds the `rules` array from a schema-derived allowlist would silently drop `code_quality` (and
`copilot_code_review`, and `license_compliance_scanning` where present).

**Verified clean today**: the one ruleset-writing utility in the repo,
`util/ad-hoc/2026-08-18_promote_sequence_safety.py:123-149`, carries every rule through verbatim —

```python
def build_payload(rs: dict) -> dict:
    """Carry everything through verbatim; append exactly one context."""
    rules = []
    for rule in rs["rules"]:
        if rule["type"] != "required_status_checks":
            rules.append(rule)
            continue
```

— and only rewrites the `required_status_checks` entry. Keep that property in any future ruleset editor.

---

## 10. Under what conditions would the claim become true? (C8)

**Conditionally true only under all of**: (1) the account is on GitHub Team or GitHub Enterprise Cloud;
(2) an enterprise owner has allowed Code Quality; (3) Code Quality is explicitly enabled on the repo;
and then (4) analysis is pending, failing, or finding `errors`-severity results.

Evidence that (1)–(3) do not hold here:

- `gh api /repos/pcalnon/juniper-ml --jq .security_and_analysis` →
  `{"dependabot_security_updates":{"status":"enabled"},"secret_scanning":{"status":"enabled"},
  "secret_scanning_non_provider_patterns":{"status":"disabled"},
  "secret_scanning_push_protection":{"status":"enabled"},
  "secret_scanning_validity_checks":{"status":"disabled"}}` — no code-quality entry.
- Repo owner type is `User`; visibility `public`. Code Quality is gated to Team / GHEC (§3.3).
- None of the 9 repos has the auto-created `"Code Quality Copilot review for default branch"` ruleset
  that GA enablement produces (§3.3).
- `code_quality` returns `details: null` in 785/785 evaluations — the signature of a rule with nothing
  behind it, as opposed to `code_scanning`'s explicit waiting/blocking messages (§4.3).

**Could not verify**: the account's exact plan. `gh api /user --jq '{login,type,plan:.plan.name}'`
returns `{"login":"pcalnon","type":"User","plan":null}` — the token's scopes
(`admin:public_key, delete_repo, gist, read:org, repo, workflow`) omit `user`, so the plan field is not
returned. The four independent signals above are consistent with "not enabled" but the plan itself is
unconfirmed. This does not affect any conclusion: the vacuous-pass measurement in §4 is the
load-bearing observation regardless of *why* it is vacuous.

---

## 11. What could not be checked

| Item | Why |
|---|---|
| Whether `code_quality` ever failed **before 2026-07-19** | The rule-suites endpoint's `time_period` maxes out at `month`; there is no older window and no other retention surface. The rule has existed since 2026-02-27 (§2), so ~5 months are unobservable. Classify as **untested**, not as "never happened". Mitigation: the rule's parameters and the repos' Code Quality status have not changed in that period, so there is no mechanism by which it would have behaved differently. |
| The account's GitHub plan | Token lacks the `user` scope (§10). |
| Whether GitHub Code Quality is definitively disabled | No public API surface exposes its per-repo enablement. Inferred from four independent signals (§10), not directly read. |
| The "2026-08-15 ruleset register §2.4" | File not found (finding CQ-8). |
| Non-`main` refs | Every ruleset targets `~DEFAULT_BRANCH` only (`conditions.ref_name.include: ["~DEFAULT_BRANCH"]`, `exclude: []`), so there is nothing else in scope. |

---

## 12. Recommendation

**Do nothing to the `code_quality` rule.** Plainly: no action is warranted.

- **Do not attach a tool.** There is no tool parameter (CQ-4). The option as written is not
  implementable.
- **Do not drop the rule.** It is inert (0/785 failures), it costs nothing, dropping it is nine
  full-replacement ruleset PUTs, and if Code Quality ever becomes available the rule is the thing you
  would want already in place — with the caveat in CQ-9 about enabling the *feature* carefully.
- **Do correct the documentation** (CQ-1, CQ-2, CQ-3, CQ-6, CQ-7). This is the only action with value.
  The runbook is operator-facing; leaving a false root cause in it will cost someone a debugging session.

**One follow-on worth flagging, not recommending.** The `Integration 4362741 : pull_request` bypass row
(present on 8 of 9 repos; absent on juniper-deploy) was justified in the notes as a `code_quality`
workaround. That justification is void (CQ-3). Whether the row is still *needed* is a separate question
this audit did not test — it may still be load-bearing for the strict-up-to-date policy on serial
archive PRs, which the runbook also cites at `:565-571`. Do not remove it on the strength of this
finding alone; test it (arm an archive PR with the row temporarily absent) or leave it.

---

## 13. Summary

| Severity | Count | IDs |
|---|---:|---|
| blocker | 0 | — |
| **major** | **3** | CQ-1, CQ-2, CQ-3 |
| minor | 4 | CQ-4, CQ-5, CQ-6, CQ-7 |
| informational | 2 | CQ-9, CQ-10 |
| could not verify | 1 | CQ-8 (+ four items in §11) |

**Register claim: FALSE.** `code_quality` is inert, not deadlocked: 779 passes, 0 failures, 785 suites,
9 repos, 30 days. A non-owner bot's armed auto-merge fired in 3 minutes with the rule satisfied. The
"every non-bypass merge waits forever" symptom was real and was caused by the **`update` ("Restrict
updates") rule**, which fails with `"Cannot update this protected ref."` and was removed fleet-wide on
2026-08-10 — after which hands-free auto-merge began working with `code_quality` untouched.

**Action: none on the ruleset; repair the three notes documents.**

---

## Appendix A — reproduce

```bash
# A1. The rule, per repo (all 9 identical)
for r in juniper-ml juniper-cascor juniper-canopy juniper-data juniper-data-client \
         juniper-cascor-client juniper-cascor-worker juniper-deploy juniper-recurrence; do
  echo "== $r"; gh api "/repos/pcalnon/$r/rules/branches/main" --jq '.[]|select(.type=="code_quality")'
done

# A2. Has any ref update been blocked outright? (0 for all 9)
gh api "/repos/pcalnon/<repo>/rulesets/rule-suites?per_page=100&time_period=month&rule_suite_result=fail" --jq 'length'

# A3. Per-rule census (NOTE: default time_period=day returns ~13 suites; use month)
gh api "/repos/pcalnon/<repo>/rulesets/rule-suites?per_page=100&time_period=month" --jq '.[].id' \
| while read -r id; do
    gh api "/repos/pcalnon/<repo>/rulesets/rule-suites/$id" \
      --jq '.rule_evaluations[]? | "\(.rule_type)\t\(.result)"'
  done | sort | uniq -c

# A4. The four decisive exhibits
gh api /repos/pcalnon/juniper-ml/rulesets/rule-suites/3485854412      # ml#860 merge: update=fail, code_quality=pass
gh api /repos/pcalnon/juniper-ml/rulesets/rule-suites/3617375022      # ml#1052 merge: update=fail only
gh api /repos/pcalnon/juniper-ml/rulesets/rule-suites/3689919174      # release-train bot: result=pass, 8/8 pass
gh api /repos/pcalnon/juniper-deploy/rulesets/rule-suites/3618801259  # update fail + code_scanning fail + code_quality pass

# A5. The probe's two confounds
gh api /repos/pcalnon/juniper-ml/pulls/864/commits --jq '[.[]|{verified:.commit.verification.verified,reason:.commit.verification.reason}]'
gh api /repos/pcalnon/juniper-ml/rulesets/13805432/history/44737966 --jq '[.state.rules[].type]'

# A6. Rule-type schema gap
gh api graphql -f query='{ __type(name:"RepositoryRuleType") { enumValues { name } } }' --jq '[.data.__type.enumValues[].name]'

# A7. Docs, verbatim
gh api /repos/github/docs/contents/content/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets.md --jq '.content' | base64 -d | sed -n '205,232p'
gh api /repos/github/docs/contents/data/reusables/gated-features/code-quality-availability.md --jq '.content' | base64 -d
```

## Appendix B — external sources

| Source | Used for |
|---|---|
| <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets> (and its `github/docs` markdown source) | "Require code quality results" text; "Restrict updates"; "Require signed commits" |
| <https://docs.github.com/en/rest/repos/rules> | Documented rule-type enum (23 values; no `code_quality`) |
| <https://docs.github.com/en/rest/repos/rule-suites> | `time_period` default `day`, max `month`; `rule_suite_result` filter |
| <https://github.blog/changelog/2026-08-07-github-code-quality-no-longer-adds-copilot-as-a-reviewer/> | Code Quality GA date (2026-07-20); auto-created Copilot-review ruleset; its reversal |
| `github/docs` `content/code-security/concepts/code-quality/code-quality.md` | What Code Quality is; per-seat licence |
| `github/docs` `data/reusables/gated-features/code-quality-availability.md` | Team / GHEC gating |
| `github/docs` `content/code-security/how-tos/maintain-quality-code/enable-code-quality.md` | Explicit enablement + enterprise-owner prerequisite |
