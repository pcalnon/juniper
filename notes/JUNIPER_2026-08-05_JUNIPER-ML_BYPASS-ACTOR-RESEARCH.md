# Bypass-Actor Research — ruleset 13805432 (flood-remediation §4 item 4)

**Project**: Juniper — juniper-ml
**Author**: Claude (flood-remediation program; R5 research agent), for Paul Calnon
**Date**: 2026-08-05
**Status**: Research complete — owner discussion agenda in §6; two identities need owner-UI confirmation
**Context**: The owner's §4-item-4 answer in [the flood analysis](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) was "additional research, planning, and discussion" — this document is that research. Probed live 2026-08-05 (during the August Cursor PR storm) via read-only `gh api`; no settings were changed.

---

## §0 Premise correction (load-bearing)

The ruleset does **not** have six *always*-bypass actors. Live JSON shows **five `always` + one `pull_request`**: the post-analysis addition **4362741 is `bypass_mode: pull_request`, NOT `always`** — and it is the owner's own **release-train GitHub App** (see §2), not an unknown third party. Also changed since the analysis: `strict_required_status_checks_policy` is now **`true`** (the owner's 2026-07-29 hardening).

**What a bypass skips (both modes):** the ruleset's rules are deletion, non_fast_forward, code_scanning (CodeQL), **code_quality (severity=errors)**, required_status_checks (13 checks + strict), **required_signatures**, update, creation. `always` skips them on *any* path (direct push to main OR PR merge); `pull_request` skips them **only** when the change lands via a PR merge — a direct push stays governed.

## §1 Per-actor analysis

| actor | identity + evidence | bypass permits TODAY (strict=true) | observed main usage | removal risk | rec |
|---|---|---|---|---|---|
| DeployKey (null), **always** | all repo deploy keys. 2 keys, both `read_only:false`: `143887186` "juniper deploy key" last_used **2026-08-03**; `144170492` "…- Turing" last_used 2026-05-07 | any key holder can push/force-push/**delete** main past all 13 checks + strict + signatures | none proven; `last_used` counts fetch too; the 2026-06-24 cleanup treated the SSH key as *not* a bypass (branch deletes needed the admin API) | unknown — a writable key authenticated 2 days ago; owner-only | **IDENTIFY-FIRST** |
| RepositoryRole 5, **always** | admin = the owner (pcalnon) | owner merges/pushes past everything — **why strict=true is toothless vs owner batch-merges** (the storm damage vector) | owner merges everything (committer=GitHub web-merge dominates the 25 recent main commits) | self-lockout (no self-approval; emergency fixes; release-train flows) | **KEEP** |
| Integration **1210556 = cursor**, always | `gh api /apps/cursor` → id 1210556; live-storm PRs are `app/cursor` | could self-merge PRs to main past checks (it does not) | authors merged PRs (A:cursor[bot], C:GitHub) — never a *direct* pusher | ~zero (owner merges; PR-creation is not a main-ref op) | **REMOVE** |
| Integration **1236702 = claude**, always | `gh api /apps/claude` → id 1236702 | could merge @claude changes to main past checks | **none** — no claude[bot] author/committer in 25 recent main commits | zero — claude.yml operates via PRs/comments, never pushes main; smoke-test @claude on a scratch PR after removal | **REMOVE** |
| Integration **1276151 = ?**, always | unresolved after ~190 public slug probes; **also always-bypass on juniper-cascor**; id-cohort of cursor / amazon-q (1220912) / claude — a mid-2025 AI-agent-era registration | full always-bypass on main, on both repos | none — posts no check-runs on any of the 7 repos' main; no bot-login commits anywhere | unknown until named | **IDENTIFY-FIRST** |
| Integration **4362741 = release-train App**, **pull_request** | the owner's own App: the owner memory records "release-train App (Integration 4362741, pull_request mode) added … so the exempt archive lane auto-merges"; equals `vars.RELEASE_TRAIN_APP_ID` used at `release-train.yml:399-402`; ml-only (absent from cascor's list); no marketplace slug because it is owner-registered | bypass **only via PR merge**, so the release-train exempt notes-archive PR can auto-merge past the code_quality deadlock (§3) | by design, on the central archive lane only | re-breaks the hands-free archive-PR auto-merge | **KEEP** |

## §2 Identification evidence and cross-repo state

- Resolved via public `gh api /apps/<slug>`: cursor=1210556, claude=1236702, dependabot=29110, copilot-swe-agent=1143301, and cursor-automation=**3544784** (a real but *different* app — ruling it out for either mystery id).
- **juniper-cascor's ruleset `15081045`** bypass list = {DeployKey, Role5, 29110 dependabot, 1143301 copilot-swe-agent, 1210556 cursor, 1236702 claude, **1276151**}, all `always` — ~~the per-repo lists are curated **differently** (ml lacks dependabot/copilot entries; cascor lacks the release-train App)~~ — **STALE 2026-08-18:** after the ml#1012 removals all 9 rosters are identical (`DeployKey`, `RepositoryRole 5`, `29110`, `1143301`, `4362741` in `pull_request` mode), except juniper-deploy which correctly lacks `4362741` (no PyPI package).
- ~~**Why 4362741 exists (root cause):** the ruleset's `code_quality (severity=errors)` rule has **no reporting tool behind it**, so every non-bypass auto-merge waits forever on a check that never arrives; the App's `pull_request`-mode bypass is a **workaround** for that mis-wired rule (§6 item 4 proposes the clean fix).~~
  > **CORRECTION 2026-08-18 — this root cause is FALSE.** Two independent audits found `code_quality`
  > has never blocked anything: **779/785** and **399/399** rule-suite evaluations `pass`, **0 fail**,
  > across 2,632 merges. The actual blocker was the **`update` ("Restrict updates") rule** — suite
  > `3485854412` (ml#860) records `update: fail` **while `code_quality: pass` in the same suite**.
  > `update` was removed fleet-wide 2026-08-10. The premise was also a category error: "a required tool
  > is not configured" is a documented blocking condition of **`code_scanning`**, not `code_quality`,
  > which has no tools parameter at all. See
  > [`JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md).
  > **Implication:** the stated justification for the `4362741` bypass entry does not hold. That does
  > not by itself mean the entry should be dropped — it is narrowly scoped (`pull_request` mode) and
  > also covers the strict up-to-date policy during serial ceremony merges — but it should be
  > re-justified on those grounds, not this one.

## §3 DeployKey audit path (owner-side)

Deploy keys are repo-scoped SSH keys; an `always` DeployKey bypass lets *any* holder push/force-push/delete `main` past every rule. Enumerated (read-only): juniper-ml has the 2 writable keys in §1; juniper-cascor likewise (`143581480` last_used **2026-07-30**, `144170557` "-Turing"). No SSH-push-to-main automation was found in `util/`, `scripts/`, or `docs/` (grep clean). Owner check: Settings → Deploy keys; identify what "juniper deploy key" and the "Turing" host key authenticate for — if they only fetch/clone, the bypass entry is dead weight → remove; if something pushes main via a key, keep and document it.

## §4 The claude-app question

`claude.yml` (`anthropics/claude-code-action`) responds to @claude mentions via PRs and comments and **never pushes main**. Its `always` bypass is far broader than the workflow needs, and no claude-app main push exists in recent history. The flood analysis P1's "removal is zero-risk" claim **holds**; the post-removal check is a scratch-PR @claude smoke-test.

## §5 Cursor bypass and the live storm

Restating the validated P3 finding with fresh evidence: PR **creation** is not a `main`-ref operation and `cursor/**` branches are ungoverned (ruleset targets `~DEFAULT_BRANCH` only), so cursor's bypass has **zero effect on the live August storm** (ml PRs to #917, cascor to #475, all `app/cursor`). The bypass matters **only if a merge-queue rule is added** — every `always` actor skips a queue, so removing the app bypasses is a **prerequisite** for a queue to bind fleet PRs. Even then, Role5 means a queue never binds *owner* batch-merges unless the owner voluntarily routes through "Merge when ready" — the post-merge net (main-verify) remains the owner-merge residual's only check. Caveat discovered en route: the owner's notes record the `merge_queue` rule **422-ing on personal-account repos** (plan-gated) — verify availability in the UI before planning around it.

## §6 Owner discussion agenda

1. **Identify 1276151** (Settings → Rules → bypass list renders app names; or Settings → GitHub Apps) — an unnamed `always` actor on ml **and** cascor. Then KEEP (if a deliberate main-writer) or REMOVE. *Recommendation: identify; expect REMOVE.*
2. **DeployKey bypass** — audit the two writable keys (especially the 2026-08-03-active one) per §3. *Recommendation: REMOVE the bypass entry after confirming fetch-only usage.*
3. **App-bypass hygiene** — remove cursor (1210556) and claude (1236702) `always` entries (defense-in-depth, ~zero risk); **keep** release-train (4362741, `pull_request`); keep Role5. *Recommendation: remove the two.*
4. **Fix the `code_quality`-no-tool deadlock** (the reason 4362741 exists): (a) attach a code-quality reporting tool, (b) drop the `code_quality` rule, or (c) keep per-app bypass workarounds. *Recommendation: (a) or (b) — a clean fix lets auto-merge work without accumulating bypass actors.*
5. **Merge-queue ↔ bypass coupling** (ties to the §4-item-1 queue decision): a queue binds fleet PRs only after the app bypasses are removed, and never binds owner batch-merges (Role5). *Recommendation: if the queue proves available (see §5 caveat), remove app bypasses first; pair with the post-merge net for the owner-merge residual.*

## §7 Could not determine (owner-UI required)

- **1276151's identity** — unresolved by ~190 slug probes, silent on all 7 repos' main, unnamed in the owner's notes; genuinely owner-UI only.
- **DeployKey usage** — what the two keys authenticate for and whether either ever pushes main (`last_used` counts fetches).
- **Merge-queue availability** on this User-owned public repo (the 422 report suggests plan-gating; UI check required).
- Whether the DeployKey `always` bypass predates or postdates the 2026-06-24 branch-cleanup incident — ruleset change history is not exposed to the read-only API.
