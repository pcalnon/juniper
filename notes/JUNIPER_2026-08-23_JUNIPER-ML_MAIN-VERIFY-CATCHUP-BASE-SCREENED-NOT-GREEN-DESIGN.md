# main-verify G3.1: the catch-up base must ratchet on SCREENED, not on GREEN

**Project**: juniper-ml
**Author**: Paul Calnon
**Date**: 2026-08-23
**Status**: Design of record — implemented in the same PR
**Area**: CI / post-merge verification
**Workflow**: [`.github/workflows/main-verify.yml`](../.github/workflows/main-verify.yml)
**Gate**: [`tests/test_main_verify_catchup_base.py`](../tests/test_main_verify_catchup_base.py)

---

## 1. Summary

`main-verify.yml`'s G3.1 catch-up base resolves to the head SHA of the most recent
**run-level `status=success`** main-verify run on `main`. That single predicate silently
conflates three unrelated properties, and the conflation is the mechanism behind a
**recurring** class of red `main` — four occurrences between 2026-08-12 and 2026-08-21.

This document specifies the fix: resolve the base from a signal that means *"this run
screened its window to a verdict"*, independent of what the verdict was and independent
of every other job in the run.

## 2. What the catch-up base is for

The post-merge screen exists because a quoted `[skip ci]` in a merge-commit body skips
`main-verify` entirely — that happened on ml#870 / #872 / #873 (the 2026-07-30 skip
incident), leaving three merge windows never screened. G3.1 answers it by making the
screen window reach back to the last known-screened tip rather than to `HEAD^1`, so the
next run that *does* fire sweeps everything skipped in between.

The property the base needs is therefore **coverage**: *"where does the un-screened
region begin?"* It is not, and never was, *"where were we last clean?"*

## 3. The defect

`.github/workflows/main-verify.yml:135`:

```bash
last_ok="$(gh api "repos/${REPO}/actions/workflows/main-verify.yml/runs?status=success&branch=main&per_page=1" --jq '.workflow_runs[0].head_sha' ...)"
```

`status=success` is a **run-level** predicate. A main-verify run contains three jobs —
`Symbol & Docs Screen`, `Regression Battery`, `Notify on Failure` — and the run is
`success` only when all of them are. So the query answers a much narrower question than
the base needs, and fails in two independent ways.

### 3a. A screen finding freezes the base (the recurring class)

When the screen reports a compositional-loss finding, the run is not `success`, so the
base does not advance. The next merge therefore re-screens a window that *still contains
the offending commit*, finds the same thing, and fails again. **Each red guarantees the
next**, and every commit merged during the streak is failed for damage someone else did.
The streak ends only when a human lands a waiver or a repair; one green run then
re-anchors the base and sweeps the whole backlog at once.

Confirmed empirically against two runs in the 2026-08-21 streak
(`14e7af41` → run 32537082565, `94dd3d64` → run 32541291579). Both show:

```text
JOB: Symbol & Docs Screen  [failure]
    step: Run sequence-safety screens (symbol + docs)  -> failure
JOB: Regression Battery    [success]
```

Both were **exit 1** — findings, not machinery errors. The window *was* screened to a
verdict in each case, so the base should have advanced past it and did not.

Recorded occurrences of the class: 2026-08-12 (symbol screen, a renamed test), 2026-08-13
(docs screen, a demoted heading), 2026-08-18 (docs screen, and here waiving would have
been *wrong* — it was real content loss), 2026-08-21 (a correct waiver orphaned by
squash-merge, five reds).

### 3b. An unrelated job failure freezes the base too

`Regression Battery` is path-gated and has nothing to do with sequence safety, yet its
failure makes the run non-`success` and so pins the sequence-safety base. This is
structurally certain from the run-level semantics above, and was observed at `b8201d0`
(ml#1059), where the tracking issue was filed describing a battery failure *with the
screen green*.

The two failure modes compose: a battery flake during a screen-red streak extends the
streak.

## 4. Why this is not a one-line change

The obvious repair — "advance the base whenever the screen job ran" — is wrong, because
the screen step's exit code carries two different meanings that the GitHub API cannot
distinguish:

| Exit | Meaning | Window screened? | Base should advance? |
|------|---------|------------------|----------------------|
| 0 | screens clean | yes | **yes** |
| 1 | compositional-loss finding(s) | **yes** — a verdict exists | **yes** |
| ≥2 | screen *invocation* error | **no** — no verdict | **no** |

Both 1 and ≥2 surface as a step conclusion of `failure`. Advancing on a ≥2 would
permanently skip an un-screened window — exactly the failure G3.1 exists to prevent. The
design must therefore make "reached a verdict" observable *separately* from "the verdict
was clean".

## 5. Design

### 5a. Split the screen step in three

The single `Run sequence-safety screens (symbol + docs)` step becomes three, so that each
property gets its own independently-queryable step conclusion:

| Step | Role | Exits non-zero when |
|------|------|---------------------|
| `Run sequence-safety screens (symbol + docs)` | run both screens; publish `src` / `drc` exit codes as step outputs | the tooling itself cannot be invoked |
| `Assert screens reached a verdict` | **coverage signal** | `src >= 2 \|\| drc >= 2` |
| `Assert screens clean` | **verdict signal** | `src >= 1 \|\| drc >= 1` |

The screens step no longer fails on findings; it records them. That is what lets the
coverage step run at all on a red screen.

Failure propagation is unchanged from the outside: on findings the job still fails, the
run still fails, and `Notify on Failure` still fires. Only the *shape* of the failure
changes — from one failing step to a passing coverage step plus a failing verdict step.

If the screens step dies outright (tooling crash, network), the two assert steps are
`skipped` by GitHub's default step gating, which is neither `success` nor a false
coverage claim. No `if:` condition is needed to get this right.

### 5b. Resolve the base from the coverage signal

The resolver walks recent completed runs newest-first and takes the first whose
`Symbol & Docs Screen` job has a step named `Assert screens reached a verdict` with
conclusion `success`, and whose head SHA is a usable ancestor of `HEAD`:

```text
GET /repos/{repo}/actions/workflows/main-verify.yml/runs?branch=main&status=completed&per_page=N
  → for each run, newest first:
GET /repos/{repo}/actions/runs/{id}/jobs
  → .jobs[] | select(.name == "Symbol & Docs Screen")
    | .steps[] | select(.name == "Assert screens reached a verdict") | .conclusion
```

The per-run job query was verified to return a `steps[]` array carrying `name` and
`conclusion` for every step, on both green and red runs.

Ancestry is checked *inside* the loop, so a run on a since-force-pushed or concurrent
descendant tip is skipped and the walk continues to an older, usable one — rather than
abandoning catch-up entirely as the single-shot query does.

### 5c. Tier order

1. **Screened tier** — §5b. The correct base.
2. **Legacy `status=success` tier** — the existing single-shot query, unchanged.
3. `github.event.before` — the push's first parent.
4. `HEAD^1` — force-push / initial / dispatch.

Tier 2 exists for two reasons. First, **transition**: no historical run carries the new
step name, so on the first run after this ships tier 1 finds nothing and tier 2 keeps the
sweep working. Second, **degradation**: if the jobs API is unavailable, tier 2 still
yields a sound (merely conservative) base.

Going forward tier 1 subsumes tier 2 — a run that succeeded necessarily reached a verdict
— so tier 2 fires only in those two situations, and never selects a *newer* base than
tier 1 would have.

### 5d. Cost

One extra API call in the common case: with the fix in place the immediately-preceding
run has a verdict whatever its colour, so the walk stops on its first iteration. The walk
goes deeper only across runs that were cancelled, skipped, or died before screening. The
scan is bounded at 20 runs.

## 6. The drift hazard this introduces

The resolver now depends on an **exact step name**. If `Assert screens reached a verdict`
is ever renamed, tier 1 matches nothing, the resolver falls silently through to tier 2,
and the original defect returns — with no error anywhere, because tier 2 is a legitimate
path.

That is the **vacuous-pass** shape — machinery that breaks while reporting success — the
same class catalogued in
[`JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md)
§12. It is closed by dedicated drift tests asserting the workflow actually contains a step
by that name inside the `symbol-screen` job, and that the resolver's shell greps for the
same literal. Both halves are required — either alone can drift past the other.

## 7. Verification

`tests/test_main_verify_catchup_base.py` extracts the workflow's own `Resolve catch-up
base` shell and drives it over a hermetic git fixture with a stubbed `gh`; it is the only
gate on this resolver. The stub becomes argument-aware, distinguishing the three request
shapes by URL (`status=completed` / `/jobs` / `status=success`).

The load-bearing new case is the regression itself:

> **a run whose screen FAILED still advances the base** — the assertion that would have
> caught this defect, and that fails against the pre-fix resolver.

Alongside it: the coverage-vs-verdict split (exit 2 must *not* advance), tier precedence,
the ancestry walk skipping an unusable newer run, and the two step-name drift guards. The
five pre-existing tests keep their names and semantics and now exercise tier 2.

## 8. What this does not change

- No change to what the screens check, their scope globs, or their waiver trailers.
- No change to `Regression Battery`, `Notify on Failure`, triggers, concurrency, or
  permissions (`actions: read` was already granted for the existing query).
- No required status check is affected: `main-verify` runs on `push: main` only, so none
  of its jobs is a required PR context. `Sequence Safety` in the ruleset is ci.yml's
  per-PR advisory screen, a different job in a different workflow.
- Direct-to-`main` pushes still bypass the per-PR screen; this fix changes only how far
  back the post-merge screen looks, not what fires it.

## 9. Residual risk

- **A ≥2 machinery error still freezes the base**, deliberately — that window genuinely
  has no verdict. It is now visible as a *failing coverage step*, which is a clearer
  signal than today's undifferentiated red, but it still needs a human.
- **The bounded scan** means a streak of more than 20 consecutive un-screened runs would
  fall through to tier 2. That is strictly better than today's behaviour and the bound is
  far above any observed streak (longest: five).
- **Tier 2 remains a silent fallback.** §6's drift test is what keeps it from becoming
  the permanent path.
