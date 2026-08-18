# Cost/Benefit Audit — `strict_required_status_checks_policy: true` Across the 9 Juniper Repos

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml (cross-repo subject: all 9 publishing/consuming repos)
**Author**: Paul Calnon
**License**: MIT License
**Document type**: Findings report (audit) — read-only; nothing outside this file was changed
**Last Updated**: 2026-08-18

---

## 0. Bottom line

**Keep `strict_required_status_checks_policy: true` on all 9 repos as-is.** Add the cheap mitigations in
§9.2. Do **not** relax it anywhere, including the low-traffic repos — they pay essentially nothing for it.

But **correct the record**: the internal flood-remediation table's claim that `strict=true` would have
prevented ~5 of the 8 storm incidents is **not supported by the evidence** (§7). Verified score is **0/8**.
`strict` is worth keeping for a *different* reason than the one it was adopted for — a reason that is
independently demonstrated twice in the last three weeks (§6.1).

| | Measured, 2026-07-29 → 2026-08-18 (20.83 d, all 9 repos) |
|---|---|
| **Cost** | 281 re-sync pushes; **~34% of all PR CI on juniper-ml and juniper-cascor**; ≈92 CI-hours (≈31 CI-h/week, unbilled — public repos); ≈23 h merge-blocking wall-clock (≈7.8 h/week); 0.65 extra full CI passes per merged PR |
| **Cost concentration** | juniper-ml 195 syncs + juniper-cascor 73 = **95% of the total**; 5 of 9 repos recorded **1 or 2 syncs each**, and none more |
| **Benefit** | **2 verified prevented main breakages** (ml#1142, cascor#472) + 1 minor merge-invalidated check (ml#1141); 0 from the 224 pure-freshness re-tests |
| **Exchange rate** | ≈140 re-syncs and ≈46 CI-hours per verified prevented main breakage |
| **Why it is still worth it** | A broken `main` reddens **every** open PR on that repo (PR CI checks out `refs/pull/N/merge` — §8.2); the observed concurrency peak was **54 open PRs on juniper-ml**. No merge queue is available. GitHub never re-runs PR CI when the base moves (§8.2), so without `strict` the last green run can be arbitrarily stale. |

---

## 1. Scope

Audit the cost and the benefit of `required_status_checks.strict_required_status_checks_policy: true`
("require branches to be up to date before merging") on the 9 owner (`pcalnon`) repositories:
`juniper-ml`, `juniper-cascor`, `juniper-canopy`, `juniper-data`, `juniper-data-client`,
`juniper-cascor-client`, `juniper-cascor-worker`, `juniper-deploy`, `juniper-recurrence`.

Lens: **decision support** — is the setting worth its cost, and does the answer differ per repo? Options in
play: keep as-is / keep with cheaper mitigations / relax / relax selectively.

Constraint carried in: a GitHub merge queue (the standard remedy) is unavailable because the repos are
User-owned (§8.1).

**Method**: read-only. Every number below is accompanied by the command that produced it. Sampling windows
are stated per finding. Intermediate JSON dumps were written to the session scratchpad only; **no
repository file other than this report was created or modified**, and no ruleset, PR, issue, or repo
setting was touched.

---

## 2. Checklist applied

| ID | Criterion | "Pass" means |
|---|---|---|
| **A** | Establish the true configured state and the adoption date | `strict` value and its first-true ruleset version recovered per repo from the API |
| **B** | Measure how often PRs actually go `BEHIND` and are re-synced | Per-repo count of own-branch merge-of-`main` commits on merged PRs, with a pre-adoption comparison window |
| **C** | Measure the CI burned by a re-sync | Real per-SHA job durations and wall-clock from `actions/runs`, not assumed |
| **D** | Measure merge frequency (the collision driver) and cost concentration | Merged-PR counts per repo per week |
| **E** | Find cases where `strict` demonstrably paid off | A PR that went `BEHIND`, was re-synced, and the re-run went RED for a reason the pre-sync run could not have seen |
| **F** | Validate the flood analysis's per-incident prevention claims | Each incident independently re-adjudicated against the actual PRs and the actual CI record |
| **G** | Assess redundancy against the newer controls | Determine what the sequence-safety screens and post-merge G3 now cover, and whether PR CI already tests the merge result |
| **H** | Assess whether the gate is binding at all | Rate of merges landing with a red or unfinished head |
| **I** | Name what could not be verified | Explicit list with reasons |

---

## 3. Verified baseline state (criterion A — **verified pass**)

**A-1. `strict=true` on all 9 repos, confirmed live.**

```bash
# per repo: gh api repos/pcalnon/<repo>/rulesets/<id> \
#   --jq '.rules[]|select(.type=="required_status_checks")|.parameters.strict_required_status_checks_policy'
juniper-ml               strict=true   n_required=15  rules=code_quality,code_scanning,creation,deletion,non_fast_forward,pull_request,required_signatures,required_status_checks
juniper-cascor           strict=true   n_required=22  (same 8-rule set)
juniper-canopy           strict=true   n_required=19
juniper-data             strict=true   n_required=20
juniper-data-client      strict=true   n_required=18
juniper-cascor-client    strict=true   n_required=18
juniper-cascor-worker    strict=true   n_required=20
juniper-deploy           strict=true   n_required=10
juniper-recurrence       strict=true   n_required=9
```

All 9 carry an identical 8-rule set. Ruleset ids: 13805432 / 15081045 / 14249530 / 14748749 / 13316681 /
13490605 / 14250447 / 14715370 / 20634527.

**A-2. Adoption date recovered exactly from ruleset version history.** Walking
`repos/pcalnon/<repo>/rulesets/<id>/history` and reading `.state.rules[]…strict_…`:

| Repo | First version with `strict=true` | Last version seen `false` |
|---|---|---|
| juniper-ml | 2026-07-29T00:10:58-05:00 (v 44737966) | 2026-07-20T17:43:18-05:00 |
| juniper-cascor | 2026-07-29T00:11:00-05:00 (v 44737970) | 2026-06-18 |
| juniper-canopy | 2026-07-29T00:11:01-05:00 (v 44737972) | 2026-05-20 |
| juniper-data | 2026-07-29T00:11:03-05:00 (v 44737976) | 2026-05-20 |
| juniper-data-client | 2026-07-29T00:11:05-05:00 (v 44737979) | 2026-05-19 |
| juniper-cascor-client | 2026-07-29T00:11:06-05:00 (v 44737982) | 2026-05-19 |
| juniper-cascor-worker | 2026-07-29T00:11:08-05:00 (v 44737984) | 2026-05-19 |
| juniper-deploy | 2026-07-29T00:11:09-05:00 (v 44737985) | 2026-05-19T15:28:21-05:00 |
| juniper-recurrence | 2026-08-10T05:39:25-05:00 (v 46073440) | never (ruleset created strict) |

**8 of 9 repos flipped in a single batch at 2026-07-29 00:11 CDT = 2026-07-29 05:11 UTC**, one day after
the flood analysis was written. `juniper-recurrence`'s ruleset was created `strict=true` on 2026-08-10.

**Sampling window used throughout this report: `[2026-07-29T05:11Z, 2026-08-19T00:00Z)` = 20.83 days
("POST"), with two equal-length pre-adoption comparison windows** `[2026-07-08, 2026-07-29)` ("PRE", the
Cursor-storm window) and `[2026-06-17, 2026-07-08)` ("PRE2", calm).

**A-3. Merge settings, all 9 (`gh api repos/pcalnon/<r> --jq '…'`).** `owner.type=User`, `private=false`,
`allow_update_branch=false`, squash+merge+rebase all enabled. `allow_auto_merge=true` on **juniper-ml
only**; `false` on the other 8.

**A-4. `Sequence Safety` became a REQUIRED status check on all 9 repos today (2026-08-18).** Latest
ruleset version per repo, with the previous version's context set for contrast:

```
juniper-ml            2026-08-17T23:27:34-05:00  n=15 seq=1   prev_n=14 prev_seq=0   (= 2026-08-18T04:27Z)
juniper-cascor        2026-08-18T03:17:49-05:00  n=22 seq=1   prev_n=21 prev_seq=0
juniper-canopy        2026-08-18T03:17:51-05:00  n=19 seq=1   prev_n=18 prev_seq=0
juniper-data          2026-08-18T03:17:52-05:00  n=20 seq=1   prev_n=19 prev_seq=0
juniper-data-client   2026-08-18T03:17:54-05:00  n=18 seq=1   prev_n=17 prev_seq=0
juniper-cascor-client 2026-08-18T03:17:34-05:00  n=18 seq=1   prev_n=17 prev_seq=0
juniper-cascor-worker 2026-08-18T03:17:56-05:00  n=20 seq=1   prev_n=19 prev_seq=0
juniper-deploy        2026-08-18T03:17:58-05:00  n=10 seq=1   prev_n=9  prev_seq=0
juniper-recurrence    2026-08-18T03:18:00-05:00  n=9  seq=1   prev_n=8  prev_seq=0
```

Corroborated by `gh issue view 1011 --repo pcalnon/juniper-ml` → `CLOSED closed=2026-08-18T08:22:12Z
[owner-decision] Promote per-PR Sequence Safety to a required check`, and
`gh pr view 1166` → `MERGED 2026-08-18T09:42:39Z chore(sequence-safety): promote the per-PR screen to
required, fleet-wide`.

---

## 4. Findings — COST (criteria B, C, D)

### C-1 — `major` — The re-sync tax is real and is ~34% of PR CI on the two busy repos

**Location**: GitHub API, all 9 repos, POST window.

**Method**. A "re-sync" is an own-branch merge of `main` into the PR branch. Detected from the GraphQL
`pullRequests(states:MERGED){ commits{ nodes{ commit{ messageHeadline committer{name} } } } }` payload by
matching `^Merge [remote-tracking ]branch 'origin/main'[ into <branch>]` where the `into` token is a prefix
of the PR's own `headRefName`. Prefix, not equality: GraphQL's `messageHeadline` truncates long headlines
with an ellipsis, and an equality test silently drops long branch names (this undercounted by ~24% on the
first pass — see §10 U-1).

**Evidence** (`scratchpad/sync_v2.py`, driving the dumps from
`gh api graphql -F owner=pcalnon -F name=<repo> -f query=@prq.graphql`):

```
=== POST (strict=true): merged in [2026-07-29, 2026-08-19) ===
repo                   merged  syncs  PRs>=1  PRs>=2  PRs>=3  tail  sync/mrg webflow
juniper-ml                251    195     127      43      15   148      0.78     173
juniper-cascor             76     73      39      17       9    64      0.96      47
juniper-canopy             18      4       4       0       0     3      0.22       4
juniper-data               20      2       2       0       0     2      0.10       2
juniper-data-client        13      2       2       0       0     2      0.15       2
juniper-cascor-client       9      1       1       0       0     1      0.11       1
juniper-cascor-worker       9      1       1       0       0     1      0.11       1
juniper-deploy             16      2       2       0       0     2      0.12       2
juniper-recurrence         18      1       1       0       0     1      0.06       1
TOTAL                     430    281     179      60      24   224      0.65     233
```

- **281 re-syncs against 430 merged PRs** = 0.65 extra full CI passes per merged PR.
- **179 of 430 PRs (42%)** needed at least one; 60 needed ≥2; 24 needed ≥3; worst was 6 (ml#1141).
- **233 of 281 (83%) carry committer `GitHub`** — the web "Update branch" button, i.e. the literal
  strict-tax gesture.
- **224 of 281 (80%) are *trailing*** — the last commit(s) on the branch, with no content change after:
  pure freshness re-verification of unchanged code.

**Share of CI** (`scratchpad/share_v2.py` over `gh api repos/.../actions/runs?event=pull_request&created=%3E%3D2026-07-29`):

```
juniper-ml:     sample runs=1000 on sync SHAs=337 (33.7%); distinct SHAs=423, sync=143 (33.8%)
juniper-cascor: sample runs=979  on sync SHAs=319 (32.6%); distinct SHAs=206, sync= 69 (33.5%)
juniper-canopy: sample runs=104  on sync SHAs= 11 (10.6%); distinct SHAs= 38, sync=  4 (10.5%)
```

**About one in three PR CI runs on juniper-ml and juniper-cascor exists only to re-verify unchanged code
against a moved base.**

**Recommended fix**: none — this is the intended mechanism. It is quantified here so the decision is made
against a number rather than an impression. See §9.2 for reductions that do not require relaxing the policy.

---

### C-2 — `major` — Absolute cost: ≈92 CI-hours and ≈23 h of merge-blocking wall-clock per 3 weeks

**Method**. Per-SHA compute = sum of non-skipped job durations across *all* `pull_request` workflow runs
for that head SHA (`gh api repos/.../actions/runs/<id>/jobs`), median over the most recent successful
full passes per repo (`scratchpad/job_minutes.py`). Per-SHA wall-clock = `max(updated_at) −
min(run_started_at)` over all completed runs for a SHA, median over the window
(`scratchpad/sha_wallclock.py`).

Measured per-SHA cost (sample medians; n=8 for ml, 6 for cascor, 4 for the rest):

| Repo | CI minutes / SHA | Wall-clock / SHA (median) |
|---|---|---|
| juniper-canopy | 55.3 | 877 s |
| juniper-cascor | 33.4 | 574 s |
| juniper-cascor-worker | 18.3 | 347 s |
| juniper-data | 15.7 | 306 s |
| juniper-ml | 14.2 | 189 s |
| juniper-data-client | 9.3 | 191 s |
| juniper-cascor-client | 9.1 | 198 s |
| juniper-deploy | 2.8 | 56 s |
| juniper-recurrence | 2.2 | 81 s |

Applied to the 281 syncs (`scratchpad/final_cost_benefit.py`):

```
repo                    syncs   CI_min  wall_h
juniper-ml                195     2769    10.2
juniper-cascor             73     2438    11.6
juniper-canopy              4      221     1.0
juniper-data                2       31     0.2
juniper-data-client         2       19     0.1
juniper-cascor-client       1        9     0.1
juniper-cascor-worker       1       18     0.1
juniper-deploy              2        6     0.0
juniper-recurrence          1        2     0.0
TOTAL                     281     5514    23.3
  => 91.9 CI-hours over 20.83 days = 30.9 CI-h/week
  => 23.3 h merge-blocking wall-clock = 7.8 h/week
```

**[ESTIMATE]** These are extrapolations from sample medians onto exact sync counts. Docs-only PRs cost less
than the median (path filters), so the CI-minute figure is an upper-ish bound.

**Honesty note that matters for the decision**: all 9 repos are `private=false`, so **GitHub Actions
minutes are not billed**. The 92 CI-hours are a *throughput* and *queue* cost, not a dollar cost. The cost
that is actually felt is the 23 h of merge-blocking wall-clock and the operator gestures behind it.

---

### C-3 — `minor` — Thrash exists but is moderate; ~15% of syncs are invalidated inside one CI cycle

**Evidence** (`scratchpad/thrash.py`):

```
=== juniper-ml (median CI wall-clock 189s) ===
  syncs-per-PR distribution: {1: 67, 2: 26, 3: 6, 4: 4, 5: 1, 6: 1}
  inter-sync gaps n=59  median=786s  p25=306s  p75=2642s
  gaps shorter than one CI cycle: 9/59 (15%)
=== juniper-cascor (median CI wall-clock 574s) ===
  syncs-per-PR distribution: {1: 16, 2: 5, 3: 2, 4: 2, 5: 1}
  inter-sync gaps n=19  median=1054s  p25=740s  p75=2553s
  gaps shorter than one CI cycle: 3/19 (16%)
```

(Distribution here is from the earlier stricter matcher, so it under-reports slightly; the *shape* holds.)

The flood analysis predicted "**High** — O(N²) Update-branch thrash at ~50 PRs"
(`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md:291`). Observed: the
superlinear shape is present, but at current volumes only ~15% of syncs are invalidated before their CI
finishes, and the worst single PR needed 6 syncs. **The predicted cost is real but was overstated in
degree.**

---

### C-4 — `major` — Most of the observed tax is driven by merge *volume*, not by the `strict` flag

This is the finding that most changes the relax/keep calculus, and it cuts *against* relaxing.

**Evidence** — same detector, three windows (`scratchpad/sync_v2.py`):

| Window | Regime | Merged | Syncs | sync/merge |
|---|---|---|---|---|
| PRE2 2026-06-17 → 07-08 | strict=**false**, calm | 316 | 32 | **0.10** |
| PRE 2026-07-08 → 07-29 | strict=**false**, Cursor storm | 404 | 153 | **0.38** |
| POST 2026-07-29 → 08-18 | strict=**true** | 430 | 281 | **0.65** |

Weekly, juniper-ml (`scratchpad` weekly recompute with the corrected matcher):

```
week          merged  syncs  sync/merge  strict
2026-06-22        61      4        0.07   false
2026-06-29        44      5        0.11   false
2026-07-06        19      0        0.00   false
2026-07-13        31      1        0.03   false
2026-07-20        83     32        0.39   false     <-- 11.9 merges/day
2026-07-27       128    127        0.99    true
2026-08-03       114    104        0.91    true
2026-08-10        76     45        0.59    true     <-- 10.9 merges/day
2026-08-17        30     25        0.83    true     (partial week: 2 days => ~15/day)
```

The cleanest natural experiment available — **same repo, near-identical merge volume, opposite `strict`
setting**: week of 2026-07-20 (83 merges, strict=false) → **0.39**; week of 2026-08-10 (76 merges,
strict=true) → **0.59**.

**Interpretation**: the marginal effect of `strict` at juniper-ml's ~11 merges/day is roughly
**+0.20 syncs per merge — about one third of the observed rate**. The other two thirds is merge volume:
at ≤44 merges/week the rate is 0.00–0.11 *with `strict` off*, and juniper-cascor shows 0.00 at 13
merges/week off and 1.15 at 55 merges/week on. **[ESTIMATE — confounded]**: the PRE window is the storm,
during which the owner was already refreshing stale branches voluntarily
(`…FLOOD-REMEDIATION-ANALYSIS.md:41`: "With strict=false, each of the 125 cursor PRs was manually
true-merged; stale branches were refreshed via GitHub-web **Update branch**"). So the strict=false
baseline at high volume is *elevated by behaviour*, and the true marginal effect could be larger than
+0.20. It cannot be smaller than ~0 and the matched pair bounds it well below the gross 0.65.

**Consequence for the decision**: relaxing `strict` would recover materially less than the gross 281
syncs suggest, because a large majority of that gesture was already being performed voluntarily at
comparable traffic.

---

### C-5 — `minor` — Cost is concentrated in 2 of 9 repos; 5 repos pay essentially nothing

From C-1: juniper-ml (195) + juniper-cascor (73) = **268 of 281 (95%)**. The remaining seven repos
between them recorded **13 syncs in 20.83 days**, and five of them recorded **exactly 1 or 2**:

```
juniper-data 2 | juniper-data-client 2 | juniper-cascor-client 1
juniper-cascor-worker 1 | juniper-recurrence 1 | juniper-deploy 2 | juniper-canopy 4
```

Merge frequency (POST window / 2.976 weeks): juniper-ml **84.3/wk**, juniper-cascor 25.5/wk, everything
else **3.0–6.7/wk**.

**Consequence**: there is no per-repo relaxation that buys anything. The 7 low-traffic repos are not
paying a tax to relax, and the 2 high-traffic repos are the ones where collision risk is real.

---

## 5. Findings — is the gate even binding? (criterion H)

### H-1 — `major` — 1.9% of merges land with a RED head; `strict` does not bind the owner

**Evidence** (`scratchpad/final_head_state.py`; per merged PR, `check-runs` on the PR's final commit):

```
repo                   merged  GREEN   RED  PEND  NOCHK   red%
juniper-ml                251    246     5     0      0   2.0%
juniper-cascor             76     73     2     1      0   2.6%
juniper-data               20     19     1     0      0   5.0%
(canopy / data-client / cascor-client / cascor-worker / deploy / recurrence: 0 red)
TOTAL                     430    421     8     1      0   1.9%

=== merged with a RED final head ===
  juniper-ml#1062  head=3f62ab64ef merged=2026-08-12T08:35:07Z failed=['Sequence Safety']
  juniper-ml#1051  head=c0fb1a8e1d merged=2026-08-10T06:28:43Z failed=['Quality Gate','Regression Tests (Python 3.13)']
  juniper-ml#1003  head=1881517066 merged=2026-08-08T04:19:26Z failed=['Release-Train Archive Guard']
  juniper-ml#928   head=40c11b7a72 merged=2026-08-06T21:06:00Z failed=['Quality Gate','Regression Tests (3.12/3.13/3.14)']
  juniper-ml#881   head=af6168fdfb merged=2026-07-31T19:28:14Z failed=['Sequence Safety']
  juniper-cascor#448 head=b386fdf7fd merged=2026-08-06T23:07:28Z failed=['Quality Gate']
  juniper-cascor#431 head=97b134af22 merged=2026-08-04T03:43:27Z failed=['Quality Gate','Unit Tests + Coverage (x4)']
  juniper-data#253   head=850e76f54f merged=2026-08-05T15:12:20Z failed=['Quality Gate']
```

Bypass actors on juniper-ml (`gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.bypass_actors[]'`):
`DeployKey mode=always`, **`RepositoryRole id=5 mode=always`** (admin = owner), `Integration 29110
always`, `Integration 1143301 always`, `Integration 4362741 pull_request`.

This confirms the flood analysis's own caveat verbatim (`…FLOOD-REMEDIATION-ANALYSIS.md:523`): "**RepositoryRole-5
admin bypass still lets the owner click merge past it** — so it informs, it does not bind."

### H-2 — `major` — ~12% of freshness-synced PRs merged before the re-test could finish

**Evidence** (`scratchpad/resync_to_merge.py`; gap = `mergedAt − committedDate(last sync)`, compared to the
repo's own median CI wall-clock):

```
repo                   tailPRs  medCIs  med_gap_s  <CI   <CI% nochecks
juniper-ml                  90     189        324   10    11%        4
juniper-cascor              24     574        926    4    17%        0
juniper-canopy               2     877       2136    0     0%        0
juniper-deploy               2      56        210    0     0%        0
fleet: 14/118 (12%) merged in less than the repo's median CI wall-clock after the final sync
gap quantiles (s): p10=178 p25=225 p50=549 p75=1014 p90=9668
```

Worked example — **juniper-ml#932**: last branch action was a web "Update branch" at
2026-08-06T21:23:21Z (`4c13fc89b0`); the PR merged **66 seconds later** at 21:24:27Z; that head SHA carries
**zero non-Cursor check runs** (`gh api repos/pcalnon/juniper-ml/commits/4c13fc89b0.../check-runs`); and
`main` then went RED on Pre-commit 3.12/3.13/3.14 (merge commit `136718321`, failing on
`Format with Black` + `Security scan Python files with Bandit`).

**This is the single most important operational finding.** `strict` guarantees *freshness*; it delivers the
*re-verification* only if the merge waits for the re-run. 1 in 8 did not, and 4 juniper-ml PRs merged on a
synced head that had run no CI at all. **The cost was paid and the benefit was discarded.**

**Recommended fix**: never merge on a synced head without `python util/wait_for_checks.py --pr N`
(`util/wait_for_checks.py`, present in tree — the shared required-context waiter, read-only by
construction, exit 0/1/2/3).

---

## 6. Findings — BENEFIT (criterion E)

This was hunted specifically, as instructed: every one of the 281 sync-commit SHAs (and its immediate
predecessor on the branch) was queried via
`gh api repos/pcalnon/<repo>/commits/<sha>/check-runs?per_page=100` and classified
(`scratchpad/final_cost_benefit.py`).

```
sync-SHA verdicts: {'GREEN': 222, 'NOCHECKS': 4, 'RED': 54, 'ERR': 1}
prev->cur:  ('GREEN','GREEN') 184 | ('RED','GREEN') 34 | ('RED','RED') 33 | ('GREEN','RED') 21 | …
GREEN->RED: 21  (GENUINE 9, GATE-ONLY 12)
```

"GATE-ONLY" = the only failing context is `Quality Gate` while its `needs:` were **cancelled** — an artifact
of the *next* push superseding the run (concurrency cancel), i.e. a symptom of the thrash, not a detection.
Verified case by case (`scratchpad/classify_red.py`), e.g. juniper-ml#1134 `1774ee2337`:
`fail=['Quality Gate'] cancelled=['Regression Tests (Python 3.12/3.13/3.14)']`.

### B-1 — `blocker`-grade *positive* evidence — two verified prevented `main` breakages

Adjudicating the 9 GENUINE `GREEN→RED` transitions:

| Case | What the re-test found | Outcome | Verdict |
|---|---|---|---|
| **juniper-ml#1142** `fa3119cc88` | `Regression Tests` 3.12/3.13/3.14 | fix commit, then merged green | **TRUE SAVE** |
| **juniper-cascor#472** `680cc838bc` | `Unit Tests + Coverage` all 4 matrix legs | fix commit, then merged green | **TRUE SAVE** |
| juniper-ml#1141 `c62eb8a894` | `Verify AGENTS.md Last Updated` | fix commit, then merged green | minor true catch |
| juniper-ml#872 `ca82a7da49` | Pre-commit (black) ×3 | fix commit "linting fixes" | `[skip ci]`-orphan unmask (§6.2) |
| juniper-ml#929 `e666464524` | Pre-commit (black + mypy) ×3 | fix commits | `[skip ci]`-orphan unmask (§6.2) |
| juniper-ml#1051 `c0fb1a8e1d` | `Regression Tests 3.13` | **merged RED** (bypass) | no defect prevented |
| juniper-ml#928 `81d72fcc10` | Pre-commit 3.12 | **merged RED** (bypass) | no defect prevented |
| juniper-ml#881 `af6168fdfb` | `Sequence Safety` (advisory then) | **merged RED** (bypass) | no defect prevented |
| juniper-cascor#519 `c61d8b217d` | `Unit Tests 3.14` | no content fix; later sync green | transient / main-side |

**Save 1 — juniper-ml#1142, the archetype, verified end to end.**

```bash
gh api "repos/pcalnon/juniper-ml/pulls/1142/commits?per_page=100" \
  --jq '.[]|"\(.commit.committer.date) \(.sha[0:10]) \(.commit.message|split("\n")[0])"'
2026-08-17T09:44:16Z 3b31ed9f49 chore(experiments): forward the suite wall budget, widen the R-6 gate to cap
2026-08-17T21:06:30Z fa3119cc88 Merge branch 'main' into chore/experiment-suite-budget-and-gate   <-- RED
2026-08-17T21:16:44Z d395d92e69 Merge remote-tracking branch 'origin/main' into …
2026-08-17T21:19:01Z 450a56f6a1 fix(experiments): read base_config budgets in the wall gate; un-inert pf3's stall window
```

- `gh pr view 1143` → merged **2026-08-17T21:06:29Z**, `docs(evidence): close the wide-budget head-to-head (64-128 units)`.
- `git log --diff-filter=A --format='%H %cI %s' origin/main -- 'util/experiments/suites/p4/e-j-h2h-wide-cap*.yaml'`
  → `294540aed9 2026-08-17T16:06:28-05:00 … (#1143)` — the offending suite YAMLs entered `main` **in #1143**.
- The sync was clicked **1 second after #1143 landed**, and the re-run failed with:
  `AssertionError: [] is not true : e-j-h2h-wide-cap128.yaml sweeps max_hidden_units up to 128 but pins no
  wall budget…` (job 95509186829).
- The fix commit `450a56f6a1` has zero failing checks; #1142 merged 21:23:36Z.

Both PRs were green independently; **the union was red**. This is the textbook logical/semantic merge
conflict, and `strict` is the only control in the stack that forces the union to be tested at merge time.

**Save 2 — juniper-cascor#472, same shape, independently verified.** The sync `680cc838bc` is a *pure*
merge of `origin/main` (it authors no content), and it flipped the branch from green to
`FAILED src/tests/unit/api/test_metrics_r5_4_pre.py::TestPendingTasksGaugeAudit_4_2::test_pending_tasks_count_drops_to_zero_after_cancel_round
- AttributeError: 'object' object has no attribute 'assigned_worker_id'`. Because the merge introduced only
`main`'s content, `main`'s content caused the failure. The next commit is
`7d9d43ae8a test(api): model real PendingTask surface in pending-tasks gauge stub`; final head
`acab51382b` has zero failing checks; merged 2026-08-07T22:10:37Z.

**Rate: 2 verified saves in 20.83 days across 9 repos ≈ 0.67/week fleet-wide.**

### B-2 — `minor` — 2 of the 9 genuine catches will not recur (root cause removed)

juniper-ml#872 and #929 both have a `github-actions[bot] … chore(agents-md): bump Last Updated … [skip ci]`
commit immediately before the red sync (`gh api repos/pcalnon/juniper-ml/pulls/{872,929}/commits`). The
`[skip ci]` head orphaned the branch's checks, so the "GREEN" predecessor was a false green; the sync
merely caused CI to run for the first time on that content, exposing branch-authored black/mypy failures.
Those are not merge-result findings, and the `[skip ci]` bot commit was removed by juniper-ml#1099
(`.github/workflows/agents-md-touch-up.yml` now **verifies** the date rather than pushing a commit —
see AGENTS.md § `agents-md-touch-up.yml`). **This class of accidental benefit is gone.**

### B-3 — `major` — Zero of the 224 pure-freshness re-tests prevented a defect

The 80% of syncs that changed nothing but the base were separately adjudicated
(`scratchpad/final_cost_benefit.py`, trailing-sync arm):

```
freshness-only (trailing) sync SHAs that went RED: 17 (GENUINE 10)
```

All 10 genuine ones resolve to: **merged RED anyway** (ml#1062, ml#1051, ml#928 ×2, ml#881),
**already-red-before-the-sync** (ml#915 ×4 — `prev_v=RED` on every one), or **transient/main-side**
(cascor#519). Both true saves (§6.1) came from syncs that were *followed by a fix commit*, so neither is a
trailing sync.

**The 224 pure-freshness re-tests cost ≈ 3,700 CI-minutes and produced no prevented defect in this
window.** That is the honest shape of the benefit: it is rare, lumpy, and worth it only if the value of
each save exceeds ~140 syncs' cost (§9.1).

### B-4 — `minor` — Post-merge `main` health improved, but the improvement is heavily confounded

**Evidence** (`scratchpad/main_health_like.py`; fraction of `main` commits with ≥1 failing push-triggered
workflow run, excluding the *new* `Post-Merge Main Verification` workflow — created 2026-07-30, after the
window boundary — and excluding `CodeQL Analysis`, which had an unrelated dependabot split-bump defect
closed 2026-07-22):

| Window | Regime | main SHAs | red SHAs (like-for-like) | rate |
|---|---|---|---|---|
| PRE2 2026-06-17 → 07-08 | strict=false, calm (8 repos) | 300 | 19 | **6.3%** |
| PRE 2026-07-08 → 07-29 | strict=false, storm (8 repos) | 209 | 24 | **11.5%** |
| POST 2026-07-29 → 08-18 | strict=true (9 repos) | 452 | 14 | **3.1%** |

Directionally a 2×–4× improvement. **But do not attribute it to `strict`**: the same window saw the
sequence-safety rollout, the G4 pre-commit split, `main-verify`, the CodeQL fix, and a work-mix change. And
`juniper-ml`'s own `main` push runs before 2026-07-27 fall outside the API's 1000-run retention, so ml is
absent from both PRE windows (marked TRUNCATED in the tool output). Recorded as *consistent with* benefit,
not as proof of it.

### B-5 — `major` — The largest single source of post-adoption `main` breakage is a path `strict` does not touch

Enumerating juniper-ml's non-`main-verify` `main` failures in the POST window with their commit subjects
(`scratchpad/main_reds_post.py`), then asking each commit for its PRs
(`gh api repos/pcalnon/juniper-ml/commits/<sha>/pulls --jq 'length'`):

```
2026-08-06T18:05:12Z CI/CD Pipeline 42cc489e6 docs(chop): … (#927)                        -> PR [927]
2026-08-06T21:24:35Z CI/CD Pipeline bb2ed045e test(ad-hoc): … (#915)                      -> PR
2026-08-06T21:46:37Z CI/CD Pipeline f10a1df63 docs(ci): … (#931)                          -> PR
2026-08-06T21:54:29Z CI/CD Pipeline 136718321 docs(fleet-triage): … (#932)                -> PR
2026-08-10T07:37:13Z CI/CD Pipeline 00f9621af docs(prompts): archive the F-P4-1 …         -> 0 PRs
2026-08-10T07:54:43Z CI/CD Pipeline b44de412e formatting fixes for handoff prompt          -> 0 PRs
2026-08-10T08:59:47Z CI/CD Pipeline b8201d021 fix(scripts): update model version …         -> 0 PRs
2026-08-16T00:18:19Z CI/CD Pipeline 087ca3e42 feat(handoff): add new handoff documents …   -> 0 PRs
2026-08-16T00:20:14Z CI/CD Pipeline 52f81c26b renamed handoff prompt file                  -> 0 PRs
```

**5 of 9 came from direct pushes to `main` with no PR at all.** juniper-cascor shows the same pattern
(`74a75c649 "serena config yaml"` → 0 PRs; `4d07a88c1 "Merge branch 'main' of github.com-juniper-cascor:…"`
→ 0 PRs).

Of the 4 that did come from PR merges, two (`bb2ed045e`, `136718321`) failed on
`Pre-commit (Python 3.12/3.13/3.14)` — i.e. the `--all-files` union class (§7, V-3).

**Recommended fix**: routing owner commits through PRs would remove more `main` breakage than any change to
`strict`. Out of scope here; flagged as the higher-yield lever.

---

## 7. Findings — validation of the flood-analysis prevention table (criterion F)

Source under test: `notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md:222-233`,
which scores `strict=true` at "**~5/8** — #751/#729/#759/#782 + #738 partial; **misses #801/#803/batch**"
(also at `:291`, `:588`, `:666`).

The claim reduces to one testable proposition: *would the same CI suite, run on the same merged content,
have gone red?* `strict` changes only *when* the merge result is tested, not *what* is tested.

### V-1 — `blocker` — For all 10 incident merges, `main`'s own CI was GREEN on the tree containing the damage

**Evidence** (`scratchpad/incident_main_after.py`; the next **completed, non-cancelled** `CI/CD Pipeline`
push run on `main` at or after each merge):

```
#759 merged 2026-07-26T23:26:00Z: next completed main run 2026-07-27T03:17:41Z -> success (2 cancelled skipped)
#738 merged 2026-07-27T00:45:53Z: next completed main run 2026-07-27T03:17:41Z -> success (2 cancelled skipped)
#782 merged 2026-07-27T22:10:38Z: next completed main run 2026-07-27T22:10:40Z -> success (4 cancelled skipped)
#801 merged 2026-07-27T22:45:54Z: next completed main run 2026-07-27T22:45:56Z -> success (3 cancelled skipped)
#744 merged 2026-07-27T23:00:26Z: next completed main run 2026-07-27T23:03:16Z -> success (4 cancelled skipped)
#751 merged 2026-07-27T23:00:38Z: next completed main run 2026-07-27T23:03:16Z -> success (4 cancelled skipped)
#739 merged 2026-07-27T23:01:19Z: next completed main run 2026-07-27T23:03:16Z -> success (4 cancelled skipped)
#753 merged 2026-07-27T23:02:41Z: next completed main run 2026-07-27T23:03:16Z -> success (4 cancelled skipped)
#803 merged 2026-07-27T23:20:20Z: next completed main run 2026-07-27T23:25:18Z -> success (5 cancelled skipped)
#729 merged 2026-07-27T23:22:53Z: next completed main run 2026-07-27T23:25:18Z -> success (5 cancelled skipped)
```

The damage was on `main` and CI could not see it — which is exactly why the analysis had to find it with a
bespoke offline AST symbol inventory (`…FLOOD-REMEDIATION-ANALYSIS.md:87`: "AST symbol inventory … 2078
symbol comparisons across 40 files"). **A `strict` re-test runs that same blind CI. It would have been
green too.**

**Verdict: strict would have prevented 0 of the 8, not ~5 of 8.**

### V-2 — `blocker` — Three incident branches were *already up to date and green* — `strict`'s precondition was satisfied and the damage landed anyway

**Evidence** (`gh api repos/pcalnon/juniper-ml/pulls/<n>/commits`, and head `check-runs`):

```
#751 head=85dd5832ec merge=31286e8fe1 parents=2 head_checks=20 head_fail=[]
#729 head=ff947aa4d2 merge=e7bb523f50 parents=2 head_checks=20 head_fail=[]
#738 head=8411db967e merge=1fd7d7cb1a parents=2 head_checks=20 head_fail=[]
#782 head=f2b66a2bcc merge=182927e7c5 parents=2 head_checks=20 head_fail=[]
#801 head=bf05f05266 merge=3ba289befa parents=2 head_checks=21 head_fail=[]
#803 head=ea35875400 merge=8f4bcba237 parents=2 head_checks=21 head_fail=[]
```

All 10 incident PRs merged as **true 2-parent merge commits**; 9 of 10 had a fully green head. And their
branches already carried web "Update branch" merges:

```
# ml#738
2026-07-26T22:36:34Z 0e4ae3248b GitHub | Merge branch 'main' into cursor/missing-test-coverage-f87b
2026-07-26T23:32:32Z bff6be7d87 GitHub | Merge branch 'main' into cursor/missing-test-coverage-f87b
2026-07-26T23:43:10Z 8411db967e Paul Calnon | fix(tests): restore _run_git helper dropped by sibling-rename merge
# ml#729 — eleven "Update branch" merges, eight "chore: re-trigger CI against current main",
#          and one commit literally titled "trying to finish this endless rebase"
# ml#751
2026-07-26T18:23:37Z 5ba9bbca92 GitHub | Merge branch 'main' into cursor/missing-test-coverage-8fff
```

ml#751's final head `85dd5832ec` was green on **all 20** contexts including `Regression Tests (Python
3.12/3.13/3.14)` — directly contradicting the table's "#751 PREVENTED — NameError → Regression Tests red".
The `NameError` was already fixed on the branch (`628bf4bc93 fixed undefined variable in tests`) by ordinary
branch CI, with no help from `strict`.

Incidental but notable: **ml#729's branch shows the exact thrash the flood analysis predicted `strict`
would *introduce* — while `strict` was still `false`.** Further support for C-4.

### V-3 — `major` — The "#759 PREVENTED" claim is doubly refuted, and its mechanism no longer exists

(a) **#759 merged with the check red and still running.** `gh api repos/pcalnon/juniper-ml/commits/b9a9b78e46/check-runs`:

```
2026-07-26T23:26:07Z success Documentation Links
2026-07-26T23:26:41Z failure Pre-commit (Python 3.13)
2026-07-26T23:26:45Z failure Pre-commit (Python 3.14)
2026-07-26T23:26:46Z failure Pre-commit (Python 3.12)
2026-07-26T23:26:52Z failure Quality Gate
```

PR merged at **23:26:00Z** — *before* any of those completed. The failure mode was merge-before-checks via
admin bypass, which `strict` does not address at all.

(b) **The mechanism the claim relies on has since been removed from the PR lane.** `ci.yml` now runs
pre-commit changed-files-scoped on `pull_request`, and its own comment states the consequence:

> `ci.yml:126-129` — "changed-files-only is BLIND to a union effect in a file the PR did NOT touch (a
> formatting conflict two unrelated branches create in an untouched file); that residual is exactly what
> G3's post-merge `--all-files` (+ the G1 merge-ref symbol screen) then cover"

`ci.yml:114-117` names #759 as the motivating incident. So the union-non-clean-black class that `strict`
was credited with catching pre-merge is now **deliberately** deferred to post-merge detection. B-5 confirms
it still lands: two POST-window PR merges reddened `main` on `Pre-commit … ×3` while their PR lane was green.

### V-4 — `minor` — The table's own rows already conceded 3.5 of the 8

`…:229-231` records `#801` **NOT PREVENTED**, `#803` **NOT PREVENTED**, `#738` **PARTIAL**, 23:01Z batch
**PARTIAL/NOT**. That was accurate. The error is confined to the four "PREVENTED" rows
(#751/#729/#759/#782), which V-1/V-2/V-3 refute.

**Recommended fix**: amend `…FLOOD-REMEDIATION-ANALYSIS.md:222-233` and its downstream summaries
(`:291`, `:565`, `:588`, `:666`) to record the re-adjudicated score, citing this report. The correct
justification for `strict` is the semantic-conflict class of §6.1, **not** the storm incidents — those are
covered by the sequence-safety screens, which is precisely why they were built and promoted (A-4).

---

## 8. Findings — redundancy and alternatives (criterion G)

### G-1 — `major` — Merge queue: permanently unavailable; verified in-repo, **not** independently verifiable from GitHub docs

`gh api repos/pcalnon/<r> --jq '.owner.type'` returns **`User` for all 9**, and no ruleset carries a
`merge_queue` rule (rule sets are exactly the 8 listed in A-1). ml#1128 (CLOSED 2026-08-17T09:45:35Z)
records the empirical UI check:

> "GitHub's availability statement: *Pull request merge queues are available in any public repository owned
> by an organization, or in private repositories owned by organizations using GitHub Enterprise Cloud.*
> `juniper-ml` is `visibility: public` but `owner.type: **User**` … Confirmed empirically: **"Require merge
> queue" is absent** from the Add-rule list … Two independent confirmations agree."

**Could not verify externally.** `WebFetch` of
`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue`
and of `.../managing-rulesets/available-rules-for-rulesets` returned pages that **do not contain** that
availability sentence in the fetched content ("there are **no statements** specifying which repository
types … support merge queues"). The claim rests on in-repo evidence plus the API-verified `owner.type=User`.
Treated as **established but not externally corroborated**; it does not change the recommendation, since a
queue being available would only strengthen the case for keeping an equivalent guarantee.

What GitHub's docs *do* confirm, fetched from
`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`:

> "The branch **must** be up to date with the base branch before merging. This is the default behavior for
> required status checks. **More builds may be required, as you'll need to bring the head branch up to date
> after other collaborators update the target branch.**"

> "The merge queue provides the same benefits as the **Require branches to be up to date before merging**
> branch protection, but does not require a pull request author to update their pull request branch and
> wait for status checks to finish before trying to merge."

That is the cost mechanism (C-1/C-2) and the unavailable remedy, in GitHub's own words.

### G-2 — `major` — PR CI **already** tests the merge result; `strict`'s unique contribution is freshness only

This corrects a widely-relied-upon framing ("M2 — test the prospective merge result"). On `pull_request`
events `actions/checkout` uses the GitHub-computed merge ref. From the juniper-ml#1142 job log
(`gh api repos/pcalnon/juniper-ml/actions/jobs/95509186829/logs`):

```
[command]/usr/bin/git checkout --progress --force refs/remotes/pull/1142/merge
HEAD is now at b1b7b31 Merge fa3119cc8826da229b8edd2340ceb9fadc33c780 into 294540aed953bb08593d2a68fd60c7cb86014e07
```

No `ref:` override appears on any `actions/checkout` step in `ci.yml`. So every PR run already tests
head-merged-into-base-tip **as of the moment the run started**.

The gap `strict` closes is that **GitHub does not re-run PR CI when the base moves**. Verified empirically:

```
ci.yml runs: 421   distinct head_sha: 420
runs-per-sha distribution: [(1, 419), (2, 1)]
```

419 of 420 juniper-ml PR head SHAs have exactly one `CI/CD Pipeline` run. The only way to obtain a re-test
against a moved base is a new head commit — i.e. a sync. **Without `strict`, the last green run can be
arbitrarily stale, and there is no other control in the stack that forces refreshment.** This is the whole
of `strict`'s value, and it is exactly what produced both saves in §6.1.

### G-3 — `minor` — The new controls cover a *different* class, so redundancy is low; they also have zero soak

`main-verify.yml` runs the two sequence-safety screens on every push to `main`
(`.github/workflows/main-verify.yml:91` — "symbol-screen (ALWAYS runs): the bypass-proof
compositional-loss net"; `:189`/`:196` invoke `juniper-symbol-loss-check` and
`juniper-docs-additions-check`). The per-PR screens use
`base = github.event.pull_request.base.sha` (`ci.yml:836-844`).

- The screens catch **symbol deletion and docs-section deletion** — the flood damage class (V-1), which CI
  never saw.
- `strict` catches **the union of two individually-green changes being red** — the §6.1 class, which the
  screens do not look for.

**These are complements, not substitutes.** Removing `strict` would not be covered by the screens.

Two caveats worth recording: (i) the screens became required **today** (A-4), so they carry **0 hours of
soak** — this is not yet a control with a track record; (ii) the required context on the 8 non-ml repos is
literally named `Sequence Safety (Advisory)` while being non-advisory (A-1 listing) — harmless but a naming
trap for anyone auditing the ruleset later.

### G-4 — `minor` — Documentation drift created today

`notes/JUNIPER_2026-08-16_JUNIPER-ML_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md:293-295` says the
`juniper-docs-additions-check` screen "is **advisory**, not a required context (ml#1011)". As of A-4 that is
false: ml#1011 is closed and the screen is required on all 9. One-line correction.

---

## 9. Recommendation

### 9.1 The exchange rate, stated plainly

Over 20.83 days across 9 repos: **281 re-syncs, ≈92 CI-hours, ≈23 h of merge-blocking wall-clock → 2
verified prevented `main` breakages.** That is ≈140 syncs and ≈46 CI-hours per save.

Whether that is a good trade turns on the cost of one `main` breakage. It is high, and measurably so:

- Because PR CI checks out `refs/pull/N/merge` (G-2), a red `main` immediately reddens **every open PR** on
  that repo. The measured concurrency peak in this window was **54 open PRs on juniper-ml** and 29 on
  juniper-cascor (lower bounds — merged PRs only; `scratchpad` concurrency scan over `createdAt`/`mergedAt`).
- The repo has a documented precedent for the blast radius: `ci.yml:114-117` — a union-non-clean `main`
  "paint[ed] EVERY open PR red until a manual re-push (#759)".
- `juniper-ml` median PR lifetime is 2.6 h (p90 47.1 h), so a breakage that persists an hour touches most of
  the open set.

One prevented breakage plausibly saves more wall-clock than a week of re-syncs. The trade is favourable.

### 9.2 Decision: **keep `strict=true` on all 9 repos**, unchanged, plus five cheap mitigations

**Keep, because:**

1. It is the **only** control that closes the staleness window (G-2), and no merge queue is available (G-1).
2. It has **paid out twice in three weeks** with verified, reproducible evidence (B-1).
3. Its cost is **not what it appears**: at matched merge volume the sync rate moved 0.39 → 0.59, so roughly
   two thirds of the observed tax is merge volume, not the flag (C-4). Relaxing recovers much less than the
   gross figure suggests.
4. **5 of 9 repos recorded 1 or 2 syncs each in 20.83 days** (C-5). There is nothing to relax there.

**Do not relax selectively.** The intuitive move — keep it on juniper-ml/juniper-cascor, relax the seven
quiet repos — inverts the evidence: the quiet repos pay ~0 and the busy repos are where the union risk is
real. There is no repo where relaxing buys more than it costs.

**Mitigations to adopt (none require a policy change):**

| # | Action | Expected effect | Evidence |
|---|---|---|---|
| M-1 | Never merge a synced head without `python util/wait_for_checks.py --pr N` | Recovers the benefit already paid for on the 12% of syncs merged before the re-run finished; would have caught ml#932 | H-2 |
| M-2 | Use `gh api -X PUT /repos/pcalnon/<repo>/pulls/<N>/update-branch` rather than a local rebase | One call, server-side, GitHub-signed (satisfies `required_signatures`); no checkout | runbook §8.1; proven twice on ml#1134 |
| M-3 | Enable `allow_auto_merge` on the 8 repos where it is `false`, and route merges through `--auto` | Merges the instant the fresh run is green, shrinking the re-invalidation window that costs ~15% of syncs | A-3, C-3 |
| M-4 | Batch merges into windows rather than interleaving all day | The tax is superlinear in merge rate: ml 0.59 at 76 merges/week vs 0.99 at 128 | C-4 |
| M-5 | Route owner commits through PRs instead of pushing to `main` | Removes the **largest** single source of post-adoption `main` breakage (5 of ml's 9) | B-5 |

**Record correction (not optional if the analysis is to stay trustworthy):** amend
`…FLOOD-REMEDIATION-ANALYSIS.md:222-233` (and `:291`, `:565`, `:588`, `:666`) — the verified prevention
score for `strict=true` against the 8 storm incidents is **0/8**, not ~5/8 (§7). Keeping the wrong number in
the record risks the opposite error later: relaxing `strict` on the grounds that "it did not prevent the
flood incidents anyway", when its actual demonstrated value lies elsewhere (§6.1) and is unrelated to that
table.

---

## 10. Could not verify

| ID | Item | Why |
|---|---|---|
| **U-1** | Exact sync counts are a **lower bound** | GraphQL `messageHeadline` truncates; the corrected prefix matcher (C-1) recovers truncated cases but a rebase-based sync (force-push, no merge commit) leaves no detectable artifact. Force-push events could not be counted: `timelineItems(itemTypes:[HEAD_REF_FORCE_PUSHED_EVENT]).totalCount` **ignores the `itemTypes` filter** (it returned the total timeline-item count — ml PR values 4–21 with a mode of 6, clearly not force-pushes), so that axis was dropped rather than reported wrongly. |
| **U-2** | juniper-ml `main` push-run history before 2026-07-27T03:17:41Z | GitHub's `actions/runs` list API caps at 1000 results. ml is therefore absent from both PRE windows in B-4 (marked TRUNCATED in the tool output). |
| **U-3** | The merge-queue availability sentence, from GitHub's own docs | Three `WebFetch` attempts against the merge-queue and rulesets doc pages returned content that does not contain it (G-1). Established from in-repo evidence + API-verified `owner.type=User` instead. |
| **U-4** | Whether GitHub auto-merge auto-updates a behind branch under `strict` | `WebFetch` of the auto-merge doc page: "there is **no information** about whether auto-merge automatically updates a pull request branch that is out of date". Indirect in-repo evidence says no: juniper-ml has `allow_auto_merge=true` and still recorded 173 manual web "Update branch" clicks (C-1). Recorded as **uncertain**; M-3's benefit is the shortened window, not automatic updating. |
| **U-5** | The counterfactual "damage that did not happen" | Unobservable by construction. The benefit figures in §6 are a **floor**, not a total. |
| **U-6** | Whether the sequence-safety screens will catch the flood class in practice | Required for 0–8 hours as of writing (A-4). No soak. |
| **U-7** | Per-incident re-adjudication of #782 and the 23:01Z batch beyond the V-1 test | V-1 (main CI green on the containing tree) applies to all of them and is decisive for the "would CI have gone red" question, but the finer damage attribution in `…FLOOD-REMEDIATION-ANALYSIS.md` §1 was not independently re-derived. |
| **U-8** | Survivorship bias | Only **merged** PRs were sampled (`--state merged`). A PR abandoned *because* of re-sync fatigue is invisible here, so the cost in §4 is also a floor. Open-PR counts at audit time were low (17 fleet-wide), so the unmeasured tail is small **now**, but it would not have been during the storm. |

---

## 11. Summary

| Severity | Count | IDs |
|---|---|---|
| **blocker** | 2 | V-1, V-2 (the flood table's prevention claims are refuted) |
| **major** | 10 | C-1, C-2, C-4, B-3, B-5, H-1, H-2, V-3, G-1, G-2 |
| **minor** | 7 | C-3, C-5, B-2, B-4, V-4, G-3, G-4 |
| **positive findings** | 2 | B-1 (ml#1142, cascor#472 — verified saves) |
| **could not verify** | 8 | U-1 … U-8 |

**Verdict: keep `strict_required_status_checks_policy: true` as-is on all 9 repos**, adopt M-1 through M-5,
and correct the prevention table in the flood-remediation analysis.

---

## Appendix A — reproduction

All commands are read-only. Substitute `<repo>` from
`{juniper-ml, juniper-cascor, juniper-canopy, juniper-data, juniper-data-client, juniper-cascor-client,
juniper-cascor-worker, juniper-deploy, juniper-recurrence}`.

```bash
# A-1 configured state
gh api repos/pcalnon/<repo>/rulesets --jq '.[]|"\(.id) \(.name) \(.enforcement)"'
gh api repos/pcalnon/<repo>/rulesets/<id> \
  --jq '.rules[]|select(.type=="required_status_checks")|.parameters.strict_required_status_checks_policy'
gh api repos/pcalnon/<repo>/rulesets/<id> \
  --jq '.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context'

# A-2 adoption date (walk history oldest-first; the flag lives under .state)
gh api repos/pcalnon/<repo>/rulesets/<id>/history --jq '[.[].version_id]|reverse|.[]'
gh api repos/pcalnon/<repo>/rulesets/<id>/history/<version_id> \
  --jq '"\(.updated_at) \([.state.rules[]?|select(.type=="required_status_checks")|.parameters.strict_required_status_checks_policy]|join(","))"'

# A-3 merge settings
gh api repos/pcalnon/<repo> --jq '{owner:.owner.type,private,allow_auto_merge,allow_update_branch}'

# B/C-1 merged PRs with commit lists (GraphQL; `gh pr list --json commits` exceeds the node budget)
gh api graphql -F owner=pcalnon -F name=<repo> -f query='
  query($owner:String!,$name:String!,$cursor:String){repository(owner:$owner,name:$name){
    pullRequests(states:MERGED,first:25,after:$cursor,orderBy:{field:UPDATED_AT,direction:DESC}){
      pageInfo{hasNextPage endCursor}
      nodes{number title createdAt mergedAt headRefName author{login}
        commits(first:100){totalCount nodes{commit{oid messageHeadline committedDate committer{name email}}}}}}}}'

# C-2 CI cost
gh api "repos/pcalnon/<repo>/actions/runs?event=pull_request&created=%3E%3D2026-07-29&per_page=100&page=N"
gh api "repos/pcalnon/<repo>/actions/runs/<run_id>/jobs?per_page=100"

# E / B-1 benefit hunt
gh api "repos/pcalnon/<repo>/commits/<sync_sha>/check-runs?per_page=100" \
  --jq '.check_runs[]|"\(.completed_at) \(.conclusion) \(.name)"'
gh api "repos/pcalnon/<repo>/actions/jobs/<job_id>/logs"

# F incident validation
gh api repos/pcalnon/juniper-ml/pulls/<n>                       # merge_commit_sha, head.sha
gh api repos/pcalnon/juniper-ml/commits/<merge_sha>             # .parents | length
gh api "repos/pcalnon/juniper-ml/pulls/<n>/commits?per_page=100"
gh api repos/pcalnon/juniper-ml/commits/<sha>/pulls --jq 'length'   # 0 => direct push to main
gh api "repos/pcalnon/<repo>/actions/runs?event=push&branch=main&created=%3E%3D2026-06-15&per_page=100&page=N"

# G-2 merge-ref proof (in the checkout step of any pull_request run's log)
gh api repos/pcalnon/juniper-ml/actions/jobs/95509186829/logs | grep 'refs/remotes/pull'

# V-3 / G-3 in-tree citations
sed -n '110,130p' .github/workflows/ci.yml     # G4 changed-files split + the blind-spot comment
sed -n '830,880p' .github/workflows/ci.yml     # sequence-safety base resolution
sed -n '85,100p;180,200p' .github/workflows/main-verify.yml
```

## Appendix B — key artifact index

| Claim | Primary artifact |
|---|---|
| `strict=true` on 9 repos, 8-rule set | ruleset ids 13805432 / 15081045 / 14249530 / 14748749 / 13316681 / 13490605 / 14250447 / 14715370 / 20634527 |
| Adoption 2026-07-29T05:11Z | ruleset versions 44737966 / 70 / 72 / 76 / 79 / 82 / 84 / 85; recurrence 46073440 |
| Sequence Safety required 2026-08-18 | ruleset versions 46817511 (ml) + the 08-18 03:17–03:18 CDT batch; ml#1011 closed 08-18T08:22:12Z; ml#1166 merged 08-18T09:42:39Z |
| Save 1 | juniper-ml#1142 sync `fa3119cc88` → fix `450a56f6a1`; cause juniper-ml#1143 merge `294540aed9` |
| Save 2 | juniper-cascor#472 sync `680cc838bc` → fix `7d9d43ae8a`; final head `acab51382b` |
| Benefit discarded | juniper-ml#932 sync `4c13fc89b0` 21:23:21Z → merged 21:24:27Z → `main` red at `136718321` |
| #759 merged red + in flight | head `b9a9b78e46`, merged 2026-07-26T23:26:00Z, Pre-commit ×3 completing 23:26:41–46Z |
| Merge-ref proof | juniper-ml job 95509186829, `HEAD is now at b1b7b31 Merge fa3119cc88… into 294540aed9…` |
| Merge queue unavailable | juniper-ml#1128 (CLOSED 2026-08-17T09:45:35Z); `notes/JUNIPER_2026-08-16_JUNIPER-ML_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md` |
| Claims under test | `notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md:222-233` |
