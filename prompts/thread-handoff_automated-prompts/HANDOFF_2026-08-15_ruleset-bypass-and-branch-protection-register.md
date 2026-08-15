# HANDOFF 2026-08-15 — the ruleset, bypass-actor and branch-protection register

**Scope: branch protection only.** This document owns one family — the juniper-ml ruleset, its bypass
actors, and the two `[owner-decision]` issues attached to them. It deliberately does **not** cover the
CLI-experimentation plan; a sibling handoff archived the same day owns that, and this one defers to it
rather than restating it.

**Four handoffs are live for 2026-08-15 and none supersedes another:**

| document | owns |
| --- | --- |
| `HANDOFF_2026-08-15_wide-budget-head-to-head-campaign.md` (ml#1122) | the wide-budget head-to-head campaign (64–128 units) |
| `HANDOFF_2026-08-15_api-primer-defect-register-outstanding-work.md` (ml#1121) | the defect register — 91 open defects |
| `HANDOFF_2026-08-15_q6-resolved-and-owner-decision-register.md` (ml#1124) | what is left of the CLI-experimentation *plan*, including every Q-* owner decision |
| **this one** | the **ruleset / bypass-actor / branch-protection** family |

**Nothing in this register is in flight**, and no engineering work is pending on it — every item is an
owner decision or a lookup only the owner can perform. `main` moves continuously (it advanced four times
while this was written), so **re-probe before acting**: two facts in an earlier draft of this very
document went stale between drafting and validation.

*On length:* the handoff procedure's ~500-word rule is deliberately exceeded. This is a register meant to
outlive the session and carry each item's evidence with it, not a task baton.

---

## 1. What this session contributed

No code, and no ruleset edit — ruleset edits are owner-gated. What changed is the accuracy of the register:

- **Integration `1276151` is identified** as "Amp for GitHub" (§2.1), closing an IDENTIFY-FIRST item open
  since 2026-08-05.
- **Integration `946600` was discovered missing** from every prior roster write-up (§2.2). It is a second,
  still-unidentified `always`-bypass App.
- **The "cascor is curated differently" finding is retired** (§2.2) — the rosters are now uniform.
- **The `code_quality` deadlock is surfaced as the root cause** (§2.4), tracked by neither open issue.

---

## 2. The ruleset family

All items concern juniper-ml ruleset `juniper-ml-rules` (id **13805432**). State below was read live from
the API on 2026-08-15. **Re-read before editing** — a ruleset edit is outward-facing and owner-gated.

### 2.1 The unattributed bypass App is identified

**Integration `1276151` = "Amp for GitHub"** (Sourcegraph's AI agentic coding tool), identified by the
owner on 2026-08-15 from Settings → Rules.

It is now **independently reproducible**: `gh api /apps/amp-for-github --jq .id` returns `1276151`. That
supersedes
[`notes/JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md:25`](../../notes/JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md),
which recorded the App as unresolved after ~190 public slug probes — the working slug is `amp-for-github`.
Worth remembering as technique: the research's probe list simply never tried that string.

The research found it posts no check-runs on any of the seven repos' `main` and no bot-login commits
anywhere, placing it in the same class as cursor and claude — an AI agent that operates through PRs and
never pushes `main` directly. **Recommendation: REMOVE.**

*(Corroborating detail: the primary checkout now carries an untracked `.amp/` directory — see §5.)*

### 2.2 Live bypass roster (juniper-ml, read 2026-08-15)

**Nine** actors. Every prior write-up of this roster, including the first draft of this document, listed
eight:

| Actor | Mode | Identity | Verdict |
| --- | --- | --- | --- |
| DeployKey (all) | `always` | writable deploy keys | identify-first |
| RepositoryRole 5 | `always` | repository admin (the owner) | keep — but see §2.3 |
| Integration 29110 | `always` | dependabot | keep |
| Integration **946600** | `always` | **UNIDENTIFIED** | **identify-first** — see below |
| Integration 1143301 | `always` | copilot-swe-agent | keep |
| Integration 1210556 | `always` | **cursor** | **REMOVE** (ml#1012) |
| Integration 1236702 | `always` | **claude** | **REMOVE** (ml#1012) |
| Integration 1276151 | `always` | **Amp for GitHub** | **REMOVE** (§2.1) |
| Integration 4362741 | `pull_request` | owner's release-train App (`vars.RELEASE_TRAIN_APP_ID`) | **KEEP** — required for the exempt archive lane |

**`946600` is the live exposure.**
[`…STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md:139`](../../notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md)
records it as "UNIDENTIFIED — not previously recorded anywhere" and **absent from juniper-ml**; it is
present now (ruleset `updated_at` 2026-08-12), and also on juniper-data, juniper-cascor-client and
juniper-deploy. Slug probes did not resolve it this session; its id sits in the same mid-2025 AI-agent
cohort as `gemini-code-assist` (956858) and `google-labs-jules` (842251). **Read the name in
Settings → Rules**, exactly as was done for Amp — far cheaper than probing.

**Rosters are uniform across repos, not per-repo curated.** juniper-cascor's ruleset (`15081045`) carries
an **identical** nine-actor list, release-train App included; juniper-data's matches too. The 2026-08-05
research note's "curated differently" finding — and its specific claim that cascor lacks the release-train
App — is **stale**. Removals must still be applied per-repo, but because the *same* removal has to be
repeated everywhere, not because the sets differ.

### 2.3 ml#1011 — promote Sequence Safety to required (open, dated)

`Sequence Safety` is **absent** from the ruleset's 14 required contexts, so the issue is unapplied. Its
soak evidence stands (advisory since 2026-07-30; ~75 PRs through the 2026-08-07 storm drain with zero
false blocks, per the ml#1011 body).

**This is scheduled, not merely pending.** The closeout plan gates promotion on a soak hold — §3.13
"A5 — The ~2026-08-21 sequence-safety promotion call", with a four-check decision checklist in **§A5.2**
to run on ~2026-08-21 and per-repo contexts in §A5.3. Its Q8 row reads "**Yes**, on ~2026-08-21 after the
§A5.2 checklist". **Run the checklist before promoting; do not promote early on this register's say-so.**

**The load-bearing caveat, verified live:** `RepositoryRole 5` (admin) holds `always` bypass, so promoting
Sequence Safety **would not constrain the owner's own merges**. That is exactly how the recurring
main-verify-red class kept recurring. Promotion is still worth doing — it makes the check load-bearing for
fleet PRs and every non-bypass path — but **it is not the fix for that failure mode**. ml#1012 is.

Change: add the `Sequence Safety` context to the ruleset's `required_status_checks` (a ruleset edit — *not*
the Quality Gate `needs:`, whose `pull_request`-only skip must not fail pushes). Rollback: remove the
context; the job stays advisory.

### 2.4 The `code_quality` deadlock — the untracked root cause

Verified live: the ruleset's `code_quality` rule carries `{"severity": "errors"}` and **no reporting
tool**, where the sibling `code_scanning` rule properly names CodeQL. Nothing ever reports against it, so
every **non-bypass** auto-merge waits forever on a check that never arrives.

That mis-wired rule is *why* the release-train App needed a bypass at all (research note §6 item 4: "the
reason 4362741 exists"). It is tracked by **neither** open issue and is the highest-leverage item here:
fix it and bypass actors stop accumulating.

Options: (a) attach a code-quality reporting tool, (b) drop the `code_quality` rule, (c) keep accumulating
per-app bypass workarounds. Research recommends (a) or (b).

### 2.5 Suggested order

1. Fix the `code_quality` rule (§2.4) — removes the reason bypasses accumulate.
2. Read the names behind **946600** and the writable DeployKey in Settings → Rules (§2.2).
3. Apply ml#1012's removals, now including Amp (§2.1) — repeated on **every** repo carrying the roster.
4. Apply ml#1011's promotion **on ~2026-08-21, after the §A5.2 checklist** (§2.3).

Each is one API call and each is reversible. **All are owner-gated — do not apply unilaterally.**

---

## 3. Other open juniper-ml issues (not this family)

- **#588** — consolidate `util/env_floor_drift_check.py` with the ci-tools `juniper-env-drift-check`
  console script.
- **#434** — sweep recent stacked-PR merges for the squash-into-stacked-branch footgun.
- **#358** / **#357** — gate the PyPI publish path on valid release tags. **Possibly already satisfied**
  by the Release-only publisher work (tag-prefix-guarded `publish-*.yml` + the meta `publish.yml` `v*`
  guard). *Unverified* — check before investing.

Every Q-* / F-P1-* / W-12 item belongs to the CLI-plan register (ml#1124), **not here**. In particular
**Q-6 was closed** by that session (cascor#523 + ml#1120) — any older document calling it open, including
an earlier draft of this one, is stale.

**juniper-cascor: zero open issues and zero open PRs.** Issue #521
(`[release-train] HALT: juniper-cascor -- main-ci-not-green`) was **closed 2026-08-15T08:59:56Z**. It had
fired 2026-08-14T22:50 on a transient `cancelled`; main CI went green on `3857d1ed` (23:45), v0.9.0 was
released at 23:05, and PyPI has served 0.9.0 since 23:36. The HALT was moot.

---

## 4. Worktree hygiene (started, then deferred)

Session worktrees under `.claude/worktrees/` had accumulated to **38**; concurrent sessions swept them to
**14** during this session. **Recount before acting** — this number moves fast.

If you resume the sweep, use the three gates from the **`project_worktree_branch_cleanup_playbook`
auto-memory** — **not live** (`/proc/*/cwd` prefix-match), **clean**, **merged** — with a TOCTOU re-check
immediately before each removal. Those gates live in that memory, *not* in
[`WORKTREE-CLEANUP-PROCEDURE-V2.md`](../../notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md),
which covers single-worktree cleanup only.

**Do not drive a bulk pass with `scripts/cleanup_session_worktrees.py`.** Its only liveness guard is
`_is_self_cwd`, which compares `Path.cwd()` alone; its removal gates are dirty + merged with no `/proc`
scan, so it *will* remove another live session's clean-and-merged worktree. Build an explicit live-aware
list instead.

---

## 5. Environment

For live experiment/service state, use ml#1124 §4 — it is more thorough and was probed the same day. Only
what this family needs is recorded here:

- **The primary checkout is tracked-clean but carries two untracked strays: `.amp/` and `bla`.**
  `util/worktree_cleanup.bash` Phase 1/7 gate on a non-empty `git status --porcelain`, so clear them
  before running a scripted cleanup.
- The isolated E2E stack is **down** (`:8202` / `:8101` / `:8051` all returned HTTP `000`); GPU carries
  desktop processes only; no experiment listeners; `/run/user/1000/juniper-experiments` is empty.
- **Do not relay the old `JuniperCascor1` stale-install warning as stated.** Installed `juniper-cascor`
  and pyproject both read 0.9.0 and `test_version_matches_pyproject` passes — but **version equality is
  not a drift check**: a physical site-packages copy shadows the editable install. ml#1124 §4.1 has the
  full diagnosis and the repair; defer to it.
- **Concurrent sessions push to `main` constantly.** With `strict_required_status_checks_policy` **on**
  (verified live), a behind branch is structurally unmergeable: re-check `behind_by == 0` immediately
  before every merge. This session watched a working tree that looked mid-edit (`ahead 1, behind 6`, a
  1039-line deletion) resolve itself to clean-and-synced within minutes — **do not "repair" a tree you did
  not dirty.**

---

## 6. Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main          # empty before committing
gh pr list  --repo pcalnon/juniper-ml     --state open            # expect other sessions' PRs
gh issue list --repo pcalnon/juniper-ml   --state open
gh issue list --repo pcalnon/juniper-cascor --state open           # expect empty
gh api repos/pcalnon/juniper-ml/rulesets/13805432 \
  --jq '{bypass: [.bypass_actors[] | {id: .actor_id, mode: .bypass_mode}],
         checks: [.rules[] | select(.type=="required_status_checks")
                           | .parameters.required_status_checks[].context]}'
gh api repos/pcalnon/juniper-cascor/rulesets/15081045 \
  --jq '[.bypass_actors[] | {id: .actor_id, mode: .bypass_mode}]'  # identical to ml's
gh api /apps/amp-for-github --jq .id                               # 1276151, confirms §2.1
git worktree list | grep -c '.claude/worktrees/'                   # recount before any sweep
```

## 7. Git state

- `juniper-ml`: primary checkout at `/home/pcalnon/Development/python/Juniper/juniper-ml` on `main`
  (untracked strays per §5). This handoff was authored in the centralized worktree
  `worktrees/juniper-ml--docs--handoff-2026-08-15-open-questions-register--20260815-1437--dff418d2`
  on branch `docs/handoff-2026-08-15-open-questions-register`, branched from `dff418d`.
  **Re-derive the SHA — concurrent sessions push to `main`.**
- `juniper-cascor`: primary checkout on `main`; zero open PRs and zero open issues.
- No experiment artifacts pending; no campaign in flight from this session.
