# Cursor Dashboard Config-Request Pack — Per-Automation Settings + Specific Feedback

**Project**: Juniper — juniper-ml (meta-package)
**Author**: Claude (task-executor PR-CE), for Paul Calnon
**Date**: 2026-07-30
**Status**: Owner action pack — every control below is **dashboard-only** (Cursor's automation config lives only in the Cursor dashboard / GitHub App installation settings; there is no in-repo Cursor config file, so **nothing in this document changes repository behavior**). Each capability is unverified vendor surface and is marked *verify-in-dashboard*.
**Source**: analysis-of-record [`§4 item 5`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) (owner answer: *"let's automate this, with specific feedback where necessary"*) + P3 §2 dashboard asks / OQ1–OQ2. Incident classes are drawn from the concurrency memory log's *"2026-07-26: Cursor Automation fleet"* section.

---

## 0. Purpose and caveats

- This is the **request pack** the owner executes by hand in the Cursor dashboard. It is a checklist + rationale, not a code change.
- **Nothing here is assumed.** Every ask is *verify-in-dashboard*: if Cursor does not expose a given control, record that in the §5 checklist and move on — do **not** treat any capability as confirmed. (P3 flagged every one of these as unverified vendor surface, OQ2.)
- **Companion in-repo detector.** The report-only open-PR budget alarm workflow (`.github/workflows/pr-budget-alarm.yml`, the sibling PR-C of this flood-remediation wave) is the repo-side smoke detector for when these source-side caps are absent or not honored. It counts open + `cursor/`-headed PRs against `PR_BUDGET_WARN` / `PR_BUDGET_ALARM` and alarms non-blockingly to Slack. The dashboard caps below are the *source-side* throttle; the alarm is the *detection* backstop.
- **Scope of the flood** (why this matters): the 2026-07-26 → 29 fleet opened ~125 PRs (134 created / 133 merged, #710–#843) with heavy same-file clusters that the owner's serial "Update branch" 3-way merges then fused and mangled — seven documented damage incidents (#729/#738/#751/#759/#782/#801/#803 + the 23:01Z batch), all since healed. Source-side caps attack that at the root: fewer concurrent same-file PRs.

---

## 1. Automation inventory and the 3-vs-4 question

The fleet runs under these check names (memory log, 2026-07-26), each opening a distinct `cursor/…` branch class:

| # | Check name (dashboard)     | Branch class                              | Automation UUID (dashboard mapping)          |
| - | -------------------------- | ----------------------------------------- | -------------------------------------------- |
| 1 | Add test coverage          | `cursor/missing-test-coverage-*`          | `4e249ce1-d08d-4b6a-b9a7-6897dc9852d0` (§4)  |
| 2 | Generate docs              | `cursor/engineering-documentation-updates-*` | `294b2ed6-5c33-4413-aea6-450ca4fdb9b7` (§4) |
| 3 | Find critical bugs         | `cursor/critical-bug-investigation-*`     | *owner to capture from a representative PR*   |
| 4 | Find vulnerabilities       | *branch pattern owner to confirm*         | *owner to capture from a representative PR*   |

**3-vs-4 question (confirm first).** The ml#844 remediation-plan body described **three** automations, but the 2026-07-26 fleet note recorded **four** distinct check names (the four above). **Confirm in the dashboard how many automations are actually enabled**, and whether "Find critical bugs" and "Find vulnerabilities" are two separate automations or one. This determines how many per-automation configs (§2) the owner applies and whether §2.5 is a live section.

---

## 2. Per-automation requested settings

All values are *targets to request*, each *verify-in-dashboard* (support unconfirmed).

### 2.1 Common asks (apply to every enabled automation)

| Setting                | Requested value                                                   | Rationale |
| ---------------------- | ---------------------------------------------------------------- | --------- |
| Concurrency cap        | **≤ 5** simultaneous open PRs per automation (≤ owner triage rate) | The flood peaked at ~73 open at once; cap intake to what one maintainer can review. |
| Cadence / schedule     | **Weekly batch, not a monthly storm** — a slower, bounded cadence | The storm is bimodal (2026-03: 43, 2026-07: 129 cursor merges months apart); a bounded weekly cadence trades burst for reviewability. |
| Per-run PR budget      | **≤ 10** PRs opened per scheduled run                            | Hard ceiling on a single run's output so one run cannot re-create the pile-up. |
| Draft-PR creation      | **On, if supported** (open as *draft*)                          | Drafts cannot be merged until marked ready — feeds a future supervisor/staging gate (P3 Stage 2). *Do not assume Cursor supports it.* |
| Target-branch selection| **Non-`main` integration branch, if supported** (e.g. `fleet/incoming`) | Targeting a non-`main` branch stops fleet branches racing `main` and authoring stale-base merges (§3.4). *Verify support.* |

### 2.2 Add test coverage — `cursor/missing-test-coverage-*` — automation `4e249ce1-…`

- **File scope: `tests/**` ONLY.** This automation must **never** touch `AGENTS.md` or `docs/**`. Test-coverage work that also edits docs is the same-file-fan-out contributor (§3.2).
- Plus every §2.1 common ask.

### 2.3 Generate docs — `cursor/engineering-documentation-updates-*` — automation `294b2ed6-…`

- **File scope: `docs/**` + `AGENTS.md` ONLY**, with an **additions-only preference** (a docs PR whose diff-vs-`main` shows `-` lines is presumed a silent section deletion — the #801/#803 class, which CI cannot see beyond a dangling anchor).
- Plus every §2.1 common ask.

### 2.4 Find critical bugs — `cursor/critical-bug-investigation-*` — automation *owner to capture*

- **Prefer report-only *issues* over PRs.** A bug investigation should file a findings **issue** (report-only) rather than open a code PR; a read-only report cannot mangle a same-file cluster.
- If PRs are unavoidable: keep them **small, single-purpose, report-first** (describe the defect + minimal fix), never broad refactors.
- Plus every §2.1 common ask.

### 2.5 Find vulnerabilities — 4th check — automation *owner to capture* (gated on the §1 3-vs-4 answer)

- If this is a separate enabled automation: same posture as §2.4 — **report-only issues preferred over PRs**; if PRs, small and single-purpose.
- If it is not separately enabled, mark this section N/A in the §5 checklist.

---

## 3. Specific feedback (the owner's "specific feedback where necessary")

Each item cites a real failure class from the fleet incident log with concrete PR examples, and states the dashboard/behavioral ask that would prevent it.

### 3.1 Run the repo-pinned formatters before opening the PR

- **Class:** the fleet emits **multi-line string concatenations that `black` 26.3.1 (line-length 512) collapses onto one line**, so nearly every fleet PR arrived black-dirty; the owner ran the pinned hooks by hand pre-merge ("linting test file" commits).
- **Ask:** before opening a PR, run the repo-pinned hooks on changed files and commit the result — `pre-commit run black isort flake8 mypy check-ast --files <changed>`. **Run the `mypy` hook too:** flake8 here ignores `F811`, so `mypy`'s no-redef is what catches byte-identical duplicate members (the #729 dup-member class). If Cursor supports a pre-PR command/hook, wire the pinned `pre-commit` there.

### 3.2 No same-file fan-out beyond the declared scope

- **Class:** dozens of PRs raced to mutate one file — `AGENTS.md` was touched by **54** PRs and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` by **53** (runbook 34, `REFERENCE.md` 15) — and the owner's serial "Update branch" merges fused/dropped sibling edits.
- **Ask:** the per-class disjoint file scopes (§2.2–§2.4) + per-run budget ≤ 10 + concurrency ≤ 5 directly cap this; additionally, **batch same-file edits into a single PR** rather than fanning one file across many.

### 3.3 Near-duplicate titles are NOT necessarily duplicates — do not title-dedup

- **Class:** **#772 vs #774** had near-identical titles but genuinely different content — they were *not* duplicates.
- **Feedback (caution, not a suppression request):** do **not** add title-similarity auto-suppression — it would drop real work. The correct levers are the concurrency/scope caps (§2), which reduce collisions without judging by title. Dup detection, if any, must key on **content**, not titles.

### 3.4 Stale-branch policy: rebase; never resolve conflicts by taking your own side wholesale

- **Class:** the #751/#782 damage — a "Merge branch 'main'" into a stale `cursor/` branch resolved conflicts by taking the **branch side wholesale**, producing an empty always-pass stub + `NameError` (#751) and an on-branch class fusion → `F821` (#782).
- **Ask:** when a branch is behind `main`, **rebase** (or leave it for owner merge-order decisions); **never** resolve conflicts by taking your own side wholesale. If Cursor exposes a merge/update strategy, prefer rebase over union-merge; the §2.1 target-branch ask (a non-`main` integration branch) removes the race against `main` entirely.

### 3.5 Keep branches fresh so the PR file list is the true delta

- **Class:** **#729**'s GitHub file list showed **12** files (including an unparseable test that broke `check-ast` and CodeQL), but that list was computed against a **stale base** — after merging healed `main` the true delta was **2** files of intended content. A kitchen-sink file list hides the real change and invites bad merge resolutions.
- **Ask:** keep the branch fresh (rebase on `main`) so the PR reflects the true delta, and **declare the intended touched-file scope in the PR body** so a reviewer (or the planned supervisor) can cross-check the stated scope against the real merge delta.

---

## 4. UUID references (dashboard mapping)

The two automation UUIDs below were surfaced by the "View Automation" links in the fleet PR bodies; they let the owner open each automation directly in the dashboard and apply the §2 settings to the correct class. **Only these two are known from the healed PR set** — the "Find critical bugs" and "Find vulnerabilities" automation IDs are *owner to capture* from a representative PR of each class (do not invent them).

| Automation (check name)     | Automation UUID                          | Dashboard URL                                                     | Surfaced in |
| --------------------------- | ---------------------------------------- | ---------------------------------------------------------------- | ----------- |
| Add test coverage           | `4e249ce1-d08d-4b6a-b9a7-6897dc9852d0`   | `https://cursor.com/automations/4e249ce1-d08d-4b6a-b9a7-6897dc9852d0` | PR **#729** body |
| Generate docs               | `294b2ed6-5c33-4413-aea6-450ca4fdb9b7`   | `https://cursor.com/automations/294b2ed6-5c33-4413-aea6-450ca4fdb9b7` | PR **#746** body |
| Find critical bugs          | *owner to capture*                       | *`https://cursor.com/automations/<uuid>`*                        | a `cursor/critical-bug-investigation-*` PR body |
| Find vulnerabilities        | *owner to capture*                       | *`https://cursor.com/automations/<uuid>`*                        | a representative PR body (if enabled) |

Per-run agent (chat) companions, for cross-reference if useful: `#729` → `bc-ab2d1762-a552-42a4-9a69-3db91a99e405`; `#746` → `bc-ace5e28a-98cc-45f1-b6b6-b5dd6deaa4fc` (these are the individual agent runs, not the reusable automation IDs above).

---

## 5. Verification checklist

Fill `dashboard-supported?` after probing each control, and `applied?` after setting it. `N/A` where a §1 answer removes the row.

| Setting                       | Automation(s)                    | Requested value                          | Dashboard-supported? | Applied? |
| ----------------------------- | -------------------------------- | ---------------------------------------- | -------------------- | -------- |
| Automation count confirmed    | (all)                            | 3 vs 4 — resolve §1                       | [ ]                  | [ ]      |
| Concurrency cap               | Add test coverage                | ≤ 5                                       | [ ]                  | [ ]      |
| Concurrency cap               | Generate docs                    | ≤ 5                                       | [ ]                  | [ ]      |
| Concurrency cap               | Find critical bugs               | ≤ 5                                       | [ ]                  | [ ]      |
| Concurrency cap               | Find vulnerabilities             | ≤ 5                                       | [ ]                  | [ ]      |
| Cadence                       | (all)                            | weekly batch, not monthly storm           | [ ]                  | [ ]      |
| Per-run PR budget             | (all)                            | ≤ 10 PRs / run                            | [ ]                  | [ ]      |
| File scope                    | Add test coverage                | `tests/**` only (never AGENTS.md/docs)    | [ ]                  | [ ]      |
| File scope                    | Generate docs                    | `docs/**` + `AGENTS.md` only, additions-only | [ ]               | [ ]      |
| Report-only issues over PRs   | Find critical bugs / vulns       | prefer issues; small PRs only if needed   | [ ]                  | [ ]      |
| Draft-PR creation             | (all)                            | on, if supported                          | [ ]                  | [ ]      |
| Target-branch selection       | (all)                            | non-`main` integration branch, if supported | [ ]               | [ ]      |
| Pre-push formatter run        | (all)                            | pinned `pre-commit` on changed files before PR | [ ]             | [ ]      |
| Rebase-not-union stale policy | (all)                            | rebase; never take-own-side wholesale     | [ ]                  | [ ]      |
| Declare touched-file scope    | (all)                            | list intended paths in the PR body        | [ ]                  | [ ]      |

---

*This document records requests only. It performs no dashboard change, no GitHub App change, and no repository behavior change. See [`§4 item 5`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) for the owner decision this pack answers, and the sibling PR-C (`.github/workflows/pr-budget-alarm.yml`) for the repo-side detection backstop.*
