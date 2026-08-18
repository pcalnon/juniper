# Branch-Protection Investigation — Synthesis and Recommendations

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-18
**Scope**: adjudicates two independent investigations per topic; states the recommendations

---

## 0. What this is

Two questions were investigated by **four independent agents**, two per topic, deliberately given
different framings so their findings would be *replicated* rather than merely reviewed. This document
adjudicates them and states what to do.

| Topic | Investigation | Adversarial / independent replication |
| --- | --- | --- |
| `code_quality` rule | [`…_CODE-QUALITY-RULE-AUDIT.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md) | tasked to **disprove** the claim |
| `strict` policy ("rebase tax") | [`…_STRICT-POLICY-COST-BENEFIT-AUDIT.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_STRICT-POLICY-COST-BENEFIT-AUDIT.md) | independent benefit-side investigation |

---

## 1. `code_quality` — SETTLED. Do nothing to the rule.

Both agents converged by different methods. **The register's claim is false.**

| Measure | Investigation | Replication |
| --- | --- | --- |
| `code_quality` evaluations | 785 suites / 30 d → **779 pass, 0 fail** | 399 suites carrying the rule → **399 pass, 0 fail** |
| `rule_suite_result=fail` | zero suites on all 9 | — |
| Merges under the rule | since 2026-03-11 | **2,632** |

**The actual July blocker was the `update` ("Restrict updates") rule**, unsatisfiable by construction
for a non-bypass actor. Rule suite `3485854412` (ml#860) records `update: fail "Cannot update this
protected ref"` **while `code_quality: pass` in the same suite**. `update` was removed fleet-wide on
2026-08-10 and the next App-armed auto-merge (ml#1108) fired unaided in 3 m 07 s with `code_quality`
unchanged at `severity: errors`.

The claim's premise was a **category error**: GitHub documents *"a required tool is not configured"*
as a blocking condition of **`code_scanning`**, not `code_quality`. Clean A/B on one push (suite
`3720498723`): `code_scanning` **fails** ("waiting for results from CodeQL") while `code_quality`
**passes**.

Two results make this decisive rather than merely suggestive:

- A **non-bypass** merge exists — suite `3689919174`, `juniper-release-train[bot]` updating `main`,
  `result: pass` on all 8 rules. So this is not "untested because everything bypasses".
- ml#1168 reached `mergeStateStatus: CLEAN` with **zero** code-quality check-runs or commit statuses
  on its head — precisely the state the claim says is impossible. `mergeStateStatus` was separately
  proven not to collapse to CLEAN for an admin viewer (the same viewer sees `BLOCKED`/`BEHIND` on
  other PRs at the same moment).

**Why it is inert:** `gh api /repos/pcalnon/<repo>/code-quality/setup` → **404, "Code quality is not
available for this repository"**, on all 9. GitHub Code Quality requires **Team / Enterprise Cloud**;
these are User-owned personal repos, so no analysis ever runs and none of its three blocking
conditions can fire.

### ⚠️ CQ-9 — the org-migration coupling (both agents, independently)

`code_quality` is inert **only because the product is unavailable on a User account** — the *same*
ownership constraint that makes merge queues unavailable
([merge-queue runbook](JUNIPER_2026-08-16_JUNIPER-ML_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md)).

All 9 rulesets are **already armed at `severity: errors`**. Migrating the fleet to an organization on
Team/GHEC would unlock merge queues **and simultaneously turn `code_quality` into a live blocking gate
on all 9, with no soak period.** Any org-migration plan must drop or downgrade that rule *in the same
change*.

Also latent but not currently armed: GitHub staff state a Code Quality rule covering non-default
branches "will always block". All 9 target `~DEFAULT_BRANCH` only — **do not widen that targeting**.

**Action: none on the rule.** Repair the three notes documents still carrying the false claim.

---

## 2. `strict` policy — the two reports DISAGREE. Adjudication below.

### 2.1 What both agree on (independently established — treat as settled)

1. **The flood analysis's per-incident table is refuted.** It claims `strict` would have PREVENTED
   ~5 of 8 storm incidents. Verified score is **0/8**. For all 10 incident merges the next completed
   `main` CI run was `success` — the damage was invisible to CI, so a strict re-test of that same CI
   would have been green too. Several rows are also individually wrong: #759 was already non-black-clean
   **on its own branch** (not a union effect) and was merged red; #729 and #782 lost nothing at merge;
   #801/#803 were pure *additions* — the victims of a later stale merge, not its perpetrators.
2. **The loss-carrying operation is the manual "Update branch" conflict resolution** — which `strict`
   *mandates more of*, adding only a CI re-run that was green on the damaged result every time.
3. **The sequence-safety screens see this damage class and `strict` does not.** Running the real
   installed screens over the storm merges FAILs every incident that truly destroyed content
   (#738 → 8 lost symbols, #751 → 4 lost + 1 weakened, #759 → 8, the 23:01Z batch → 6). Those screens
   became **required on all 9 repos on 2026-08-18** (ml#1011).
4. **`strict` does not bind the owner** (`RepositoryRole 5` = `always`) and **has no jurisdiction over
   direct pushes to `main`** — which is where the real damage now lands (§2.4).

### 2.2 Where they disagree

| | Cost/benefit audit | Benefit-side replication |
| --- | --- | --- |
| Verified saves in the window | **2** (ml#1142, cascor#472) | **1** (ml#1142 only) |
| Recommendation | **Keep as-is on all 9** | `strict` is the weaker control and a **candidate to relax** |

The count differs because the two used different detectors: the replication scanned for a `success`
run followed by a `failure` run *on a different head*, which structurally cannot see cascor#472 (a pure
`origin/main` merge that flipped green→red on `AttributeError: 'object' object has no attribute
'assigned_worker_id'`). The replication documented this blind spot itself. **2 is the better number.**

### 2.3 Adjudication — keep `strict`, and the disagreement largely dissolves

The replication's recommendation was **explicitly conditional**: *"If the parallel cost measurement
shows a material tax, `strict` is the weaker of the two controls and the reasonable candidate to
relax."* The cost measurement came back and **the condition is not met**:

- A matched-volume natural experiment in the same repo across adjacent regimes (juniper-ml: week of
  07-20, 83 merges, `strict=false` → 0.39 syncs/merge; week of 08-10, 76 merges, `strict=true` →
  0.59) puts **`strict`'s marginal effect at ≈ +0.20 syncs/merge — about one third of the observed
  rate.** Most of the "rebase tax" is *merge volume*, not the policy. Relaxing `strict` would remove
  roughly a third of a cost that is itself modest.
- **CI minutes are unbilled** — all 9 repos are public — so the ~92 CI-hours are not a real budget
  line. The felt cost is ≈ 23 h of merge-blocking wall-clock over 20.8 days (≈ 7.8 h/week), 95 % of it
  in just two repos (ml 195 syncs, cascor 73). Five repos recorded 1–2 syncs each in the whole window.

Against that: a red `main` reddens **every** open PR, because PR CI checks out `refs/pull/N/merge`.
Measured concurrency peaked at 54 open PRs on juniper-ml in the window (97 during the storm). The
exchange rate — ≈140 syncs per save — is unattractive in isolation but is buying insurance against a
correlated failure whose blast radius scales with open-PR count.

**Recommendation: keep `strict=true` on all 9, unchanged.** It is a modest, mostly-volume-driven cost
with a small but real benefit, and no cheaper equivalent exists now that the merge queue is
permanently unavailable. Revisit only if merge volume rises materially without a matching rise in
saves.

**Do not relax the quiet repos either.** Their cost is already ~0 (1–2 syncs in 20.8 days), so
relaxing them buys nothing and costs uniformity.

### 2.4 The findings that matter MORE than the strict decision

Both reports independently landed on the same conclusion: **`strict` is not where the leverage is.**

1. **12 % of freshness-synced PRs merged before the re-test could finish** — the cost was paid and the
   benefit discarded. ml#932 merged **66 seconds** after its sync on a head with **zero** CI check-runs,
   and `main` then went red on Pre-commit ×3. ml#924 merged **25 seconds** after an update-branch head
   was created, with zero CI ever run on it, and introduced the lint violation that reddened `main`.
   *This is a strictly-worse outcome than not syncing at all.* Fix: gate merges on the already-present
   `util/wait_for_checks.py`.
2. **Direct pushes to `main` are the dominant main-health problem.** 5 of juniper-ml's 9 post-adoption
   `main` breakages came from direct pushes with **no PR at all**, and **both** true content-destruction
   events of the strict era were direct pushes — ml `76e4513b` (three deletion runs of 16/14/16 lines,
   healed by a *restore* commit) and cascor `4d07a88c` (**136 lost symbols**, five whole
   `src/snapshots/*.py` modules, healed 30 min later). No per-PR control — `strict` or sequence-safety —
   has jurisdiction over that path.
3. **`strict` was never active during the storm it was adopted for** (last storm merge 2026-07-28T03:09Z;
   policy flipped 2026-07-29T05:11Z), and during the *second* fleet burst on 2026-08-06/07 (peak 83 open
   PRs) it produced **zero** payoff catches.

---

## 3. Recommendations

| # | Action | Priority | Rationale |
| --- | --- | --- | --- |
| R1 | **No change to `code_quality`** on any repo | — | Proven inert; 0 failures in 785 suites |
| R2 | **Record CQ-9 against any org-migration plan** — drop/downgrade `code_quality` in the same change | High *if* migration is ever considered | Migration arms it at `severity: errors` on all 9 with no soak |
| R3 | **Keep `strict=true` on all 9, unchanged** | — | Marginal cost ≈ +0.20 syncs/merge; 2 verified saves; no cheaper equivalent |
| R4 | **Gate merges on `util/wait_for_checks.py`** so a synced head is never merged before its re-test finishes | **Highest** | 12 % of syncs discard the benefit they just paid for; two reddened `main` |
| R5 | **Address direct pushes to `main`** | **High** | 5 of 9 breakages and both true-loss events; outside every per-PR control |
| R6 | **Correct the flood analysis's per-incident table** (verified 0/8, not ~5/8) and the three notes docs repeating the `code_quality` claim | Medium | Both are load-bearing documents that have already misdirected work |

R4 and R5 are the substantive wins. R1 and R3 are "do nothing", which is the correct outcome for both
questions as originally posed.

---

## 4. Method note

Four agents, two per topic, one per topic framed adversarially. Both topics ended by **refuting a
claim from the project's own internal documents** — the `code_quality` diagnosis and the flood
analysis's prevention table. Both refutations required going to the live API and re-running the real
screens over historical merges rather than reading the notes.

The recurring lesson, now demonstrated twice in one day: **configuration is not behaviour, and an
internal document asserting a mechanism is not evidence that the mechanism fired.**
