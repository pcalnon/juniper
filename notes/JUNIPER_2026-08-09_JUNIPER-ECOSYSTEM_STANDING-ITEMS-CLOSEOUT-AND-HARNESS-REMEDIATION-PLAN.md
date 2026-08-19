# Standing-Items Arc Closeout and Agentic-Harness Remediation — Plan

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml (subject spans the 9-repo ecosystem)
**Author**: Paul Calnon
**Document Type**: Implementation Plan + owner decision package
**Status**: DRAFT — owner decisions pending (§11); nothing in this document has been executed
**Last Updated**: 2026-08-09

---

## 0. How to read this document, and what "verified" means here

This is a **plan only**. The authoring session executed nothing: no ruleset was edited, no PR was opened, no
config file was modified, no `activate_project` call was made. Every command in this document is written for
the owner (or a later, explicitly-approved session) to run.

Three evidence classes are used, and they are labelled inline:

| Label | Meaning |
|---|---|
| **[live 2026-08-09]** | Re-probed by this session against the live API / filesystem during authoring. Cited with the probe. |
| **[repo]** | Read from the repository at `file:line`. Re-confirmable with `Read`. |
| **[audit]** | Established by the sibling audit document (below) and *not* re-derived here, to avoid duplicating its hunt. |

The parallel audit — [`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md`](JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md)
— is the **findings** half of this pair. It owns the stale-key hunt (its §3.1, findings `A1-F1`/`A1-F2`), the
Serena root-cause ranking (its §4.1, `A2-F1`…`A2-F13`), and the guardrail attachment-point inventory (its §6,
`G1`…`G18`). This document owns the **remedies**. Where the audit already names a location, this plan cites the
audit's finding ID rather than re-listing the search; §5.7 (the signing repoint step) is deliberately a pointer,
not a second inventory.

Two related prior documents are load-bearing and are cited rather than restated:

- [`notes/JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md`](JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md) — the per-actor analysis of ruleset `13805432`, the `code_quality` deadlock diagnosis (its line 32), and the owner agenda (its §6, lines 48-51).
- [`notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md) — the all-advisory rollout whose decision **D8** ("promote any advisory workflow to required — later, per-repo, after soak") is the open item this plan closes (its line 347).

---

## 1. Purpose, scope, non-goals

### 1.1 Purpose

Turn two loosely-tracked bodies of work into executable, reversible, owner-gated steps:

- **Part A — the standing-items arc.** Six open items carried since the 2026-08-07/08 storm drain and the
  bypass-actor research. Each gets verified state, options, a recommendation, exact execution steps, a
  verification probe, and a rollback.
- **Parts B and C — two agentic-harness remediations.** (B) headless code signing has no preflight, so a
  blocked signature can silently stall or mis-sign a flow; (C) the Serena MCP harness is connected but
  project-less, and every layer that could have surfaced that is silent.
- **Part D — sequencing.** How the above is sliced into PRs, which slices may merge under the owner's new
  conditional gate, and the per-slice verification/rollback matrix.

### 1.2 Scope

`pcalnon/juniper-ml` plus the 8 sibling repos for the ruleset/branch-protection items; the owner's workstation
(`yamaguchi`) for the signing and MCP items, which are **local machine state**, not repository content.

### 1.3 Non-goals

- **Not** a re-audit. The audit document is authoritative for findings; contradicting it is a defect in one of
  the two, to be resolved before either is ratified (§10.4).
- **Not** a change to the owner-gated deploy posture. PyPI / environment approvals stay owner-only; nothing
  here touches `publish*.yml`, the `pypi` environment, or the release-train's Gate 2.
- **Not** an expansion of the release-train's `gh` surface (R7). No new verbs, no new write scopes.
- **Not** key-material work. No key generation, rotation, `keytocard`, or GitHub GPG-key upload is proposed;
  §5.7 is a documentation/reference repoint only.
- **Not** a Serena *usage* mandate. Part C makes Serena available and its absence loud; it does not require any
  agent to use it.

---

## 2. Standing doctrine this plan must obey

Restated only where it constrains a step below.

| # | Rule | Effect on this plan |
|---|---|---|
| D-1 | Ruleset / branch-protection edits are **owner-gated**. | Every Part-A mutation is written as a dry-run-first helper the owner runs, or a UI procedure. No session applies one on its own initiative. |
| D-2 | PyPI / environment approvals are owner-only. | Untouched. Noted because A3/A4 interact with the release-train, whose Gate 2 stays as-is. |
| D-3 | Headless merges only on the owner's explicit per-PR (or per-group) approval. | Part D's merge column is "eligible", never "will merge". |
| D-4 | **New conditional gate (owner, 2026-08-09):** arc PRs merge headlessly only once code signing verifiably uses the correct ed25519 key. | §5.6 operationalizes this as a machine-checkable preflight; §7.3 states exactly which slices it unlocks. |
| D-5 | `gh pr list` dup-guard before opening any PR. | §7.2. Current open-PR set re-probed **[live 2026-08-09]**: 4 open (`#1048`, `#1043`, `#1041`, `#1039`) — none overlaps this plan's slices. |
| D-6 | Headless PR-branch work uses GitHub-signed API commits (`createCommitOnBranch`). | Distinguished from local-commit flows in §5.5; the preflight gates only the latter. |
| D-7 | Per-agent scratch subdirectories; never run release-train live seams from a shared clone. | The Part-A helper (§3.7) writes snapshots under an explicit `--snapshot-dir`, never into a checkout. |
| D-8 | Script placement: permanent → `util/`, single-use → `util/ad-hoc/`; `/tmp/` is prohibited for script *source*. | The ruleset helper is `util/ad-hoc/`; the signing preflight is permanent `util/`. |
| D-9 | Never quote a full waiver trailer or a CI-skip marker in prose. | Trailer *names* only (`Allow-Symbol-Loss`, `Allow-Docs-Rewrite`) appear below; no colon-and-value form. |

---

# PART A — Standing-items closeout decision package

## 3. Part-A ground truth (re-probed 2026-08-09)

### 3.1 juniper-ml ruleset `13805432` — live state

**[live 2026-08-09]** `gh api repos/pcalnon/juniper-ml/rulesets/13805432`:

- `name` `juniper-ml-rules`, `target` `branch`, `enforcement` `active`, `conditions.ref_name.include = ["~DEFAULT_BRANCH"]`, `exclude = []`.
- `bypass_actors` (6): `DeployKey`/`actor_id: null`/**always**; `RepositoryRole` `5`/**always**; `Integration` `1210556`/**always**; `Integration` `1236702`/**always**; `Integration` `1276151`/**always**; `Integration` `4362741`/**pull_request**.
- `rules` (8): `deletion`, `non_fast_forward`, `code_scanning` (CodeQL, `alerts_threshold: errors`, `security_alerts_threshold: high_or_higher`), **`code_quality`** (`severity: errors`), `required_status_checks` (`strict_required_status_checks_policy: true`, `do_not_enforce_on_create: true`, **13** contexts), `required_signatures`, `update`, `creation`.
- The 13 required contexts: `Pre-commit (Python 3.12|3.13|3.14)`, `Regression Tests (Python 3.12|3.13|3.14)`, `Build and Validate Package`, `Documentation Links`, `Security Scan`, `Quality Gate`, `Analyze (python)`, `Dependency Documentation`, `Release-Train Archive Guard`.
- **No `merge_queue` rule**, **no `pull_request` (required-review) rule**.

Repo settings **[live 2026-08-09]**: `visibility: public`, `owner.type: User`, `allow_auto_merge: true`, `delete_branch_on_merge: true`.

### 3.2 Fleet bypass census — new finding

**[live 2026-08-09]** Bypass actors across all 8 sibling rulesets (juniper-recurrence has none — see §3.4):

| Repo | Ruleset | Integration bypass actor IDs (all `always` unless noted) |
|---|---|---|
| juniper-ml | 13805432 | 1210556, 1236702, 1276151, **4362741 (`pull_request`)** |
| juniper-cascor | 15081045 | 29110, 1143301, 1210556, 1236702, 1276151 |
| juniper-canopy | 14249530 | 29110, 1236702, 1276151 |
| juniper-data | 14748749 | 29110, **946600**, 1143301, 1210556, 1236702, 1276151 |
| juniper-data-client | 13316681 | 29110, 1210556, 1236702, 1276151 |
| juniper-cascor-client | 13490605 (`Bubba Says No`) | 29110, **946600**, 1210556, 1236702, 1276151 |
| juniper-cascor-worker | 14250447 | 29110, 1236702, 1276151 |
| juniper-deploy | 14715370 | 29110, **946600**, 1143301, 1210556, 1236702, 1276151 |

All 8 additionally carry `DeployKey`/always and `RepositoryRole 5`/always; juniper-cascor-client also carries
`RepositoryRole 2`/always.

**Identification method (new, and it works).** A ruleset `bypass_actors[].actor_id` of type `Integration` is the
**GitHub App ID**, not an installation ID — proved by `gh api /apps/dependabot` returning `id: 29110`, which is
exactly the census value. Public Apps can therefore be named without owner UI by probing `/apps/<slug>` and
matching the returned `id`. **[live 2026-08-09]** a ~190-slug sweep resolved:

| App ID | Slug | Name | Status |
|---|---|---|---|
| 29110 | `dependabot` | Dependabot | identified |
| 1143301 | `copilot-swe-agent` | **Copilot SWE Agent** | identified |
| 1210556 | `cursor` | Cursor | identified |
| 1236702 | `claude` | Claude | identified |
| 4362741 | *(private/unlisted; `/apps/juniper-release-train` → 404)* | the owner's release-train App | identified by behaviour: `juniper-release-train[bot]` is a PR author and commit author on juniper-ml **[live 2026-08-09]**, and the ID equals `vars.RELEASE_TRAIN_APP_ID` used at `.github/workflows/release-train.yml:399-402` [audit / research §1] |
| **1276151** | — | — | **UNIDENTIFIED** |
| **946600** | — | — | **UNIDENTIFIED — not previously recorded anywhere** |

`946600` does not appear in the bypass-actor research note (grep: no match) because that note scoped to
juniper-ml, where `946600` is absent. It is present on **juniper-data, juniper-cascor-client, juniper-deploy**.
This is a net-new identify-first item.

Both unidentified IDs behave like the release-train App: `/apps/<slug>` 404s for every candidate slug tried,
which is the signature of a **private / unlisted** GitHub App. `/user/installations` is unavailable to the
session token (**[live 2026-08-09]**: HTTP 403, "You must authenticate with an access token authorized to a
GitHub App"), and `/app/installations/<id>` requires an App JWT (**[live 2026-08-09]**: HTTP 401). Owner UI is
therefore genuinely required (§3.3).

### 3.3 Deploy keys

**[live 2026-08-09]**, all `read_only: false`, all added by pcalnon:

| Repo | ID | Title | Created | Last used |
|---|---|---|---|---|
| juniper-ml | 143887186 | `juniper deploy key` | 2026-02-25 | 2026-08-03 |
| juniper-ml | 144170492 | `Juniper ML Deploy Key - Turing` | 2026-02-28 | 2026-05-07 |
| juniper-cascor | 143581480 | `juniper-cascor deploy key` | 2026-02-21 | 2026-08-06 |
| juniper-cascor | 144170557 | `Juniper Cascor Deploy Key - Turing` | 2026-02-28 | 2026-05-07 |

Owner decision 2026-08-09 (session record): **Turing keys RETAINED.** This plan therefore does not propose
removing any deploy key, and does not propose removing the `DeployKey` bypass entry — see §3.4/A1 for the
residual note.

### 3.4 juniper-recurrence uses CLASSIC branch protection, not a ruleset

**[live 2026-08-09]** `gh api repos/pcalnon/juniper-recurrence/rulesets` → `[]`. `…/branches/main/protection`:

- `required_status_checks.strict: true`, contexts (3, all `app_id: 15368` = GitHub Actions):
  `Guard PR base branch`, `Test — torch MLP readout (Rung 2b; optional [torch] extra)` (em dash — copy it exactly),
  `Bench required checks`.
- `required_signatures.enabled: true`; `required_pull_request_reviews.required_approving_review_count: 1`;
  `enforce_admins.enabled: false`; `required_linear_history.enabled: false`.
- The sub-resource `…/protection/required_status_checks` and its `contexts_url` both exist **[live 2026-08-09]** — that is the safe, narrow edit surface (§3.6/A5), not the whole-protection `PUT`.

### 3.5 Sequence-safety soak — re-measured

**[live 2026-08-09]** Standalone `sequence-safety.yml` run conclusions (all runs to date, `per_page=100`):

| Repo | success | cancelled | failure |
|---|---|---|---|
| juniper-cascor | 49 | 1 | 0 |
| juniper-canopy | 3 | 0 | 0 |
| juniper-deploy | 2 | 0 | 0 |
| juniper-recurrence | 2 | 0 | 0 |
| juniper-data | 1 | 0 | 0 |
| juniper-data-client | 1 | 0 | 0 |
| juniper-cascor-client | 1 | 0 | 0 |
| juniper-cascor-worker | 1 | 0 | 0 |
| **total** | **60** | **1** | **0** |

juniper-ml runs the screen as a **job inside `ci.yml`**, not a standalone workflow. **[live 2026-08-09]** the
`Sequence Safety` job succeeded on **15/15** of the last 15 `pull_request` `ci.yml` runs.

Job / context names **[repo]**:

- juniper-ml: `.github/workflows/ci.yml:741-744` — job `sequence-safety`, **`name: Sequence Safety`**, `if: github.event_name == 'pull_request' || github.event_name == 'merge_group'`. `ci.yml:49` wires `merge_group:`.
- All 7 consumers: standalone `sequence-safety.yml`, **`name: Sequence Safety (Advisory)`** at both workflow and job level, e.g. `juniper-cascor/.github/workflows/sequence-safety.yml:55,80`; canopy `:64,95`; data `:59,84`; worker `:65,90`; deploy `:69,94`; recurrence `:60,85`; data-client `:67,93` and cascor-client `:64,89` (**[live 2026-08-09]** read from the remote — the local checkouts of those two are stale, §3.8).
- **Every consumer workflow is `pull_request`-only** (e.g. cascor `:57-61`). None listens on `merge_group`. This is load-bearing for A4/A5 (§3.6).

### 3.6 The `code_quality` rule has no reporting tool — corroboration

> **CORRECTION 2026-08-18 — the three signals below are individually accurate but the CONCLUSION drawn
> from them is false.** "No reporting tool" is true and irrelevant: `code_quality` has no tools
> parameter *by design*, and GitHub documents "a required tool is not configured" as a blocking
> condition of **`code_scanning`**, a different rule. `code_quality` gates on the GitHub Code Quality
> product, which returns 404 "not available for this repository" on all 9 (it requires Team/GHEC;
> these are User-owned), so none of its three documented blocking conditions can fire. Measured:
> **779/785** and **399/399** rule-suite evaluations `pass`, **0 fail**, across 2,632 merges. The
> real blocker in the cited period was the **`update` rule** (suite `3485854412` shows `update: fail`
> beside `code_quality: pass`), removed fleet-wide 2026-08-10. Signal 3 below — that GraphQL omits
> `CODE_QUALITY` while REST reports it — remains correct and is the signature of a preview-stage rule,
> not of a mis-wired one. Full evidence:
> [`JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md).
>
> **Forward risk (CQ-9):** all 9 rulesets are already armed at `severity: errors`. Moving the fleet to
> an organization on Team/GHEC — the same change that would make merge queues available — would arm
> this rule live on all 9 with no soak period. Drop or downgrade it in that same change.

Three independent signals, none of which requires owner UI:

1. **[research]** `notes/JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md:32` states the rule has no reporting tool behind it, and that this is *why* the release-train App (`4362741`) holds a `pull_request` bypass.
2. **[live 2026-08-09]** `gh api repos/pcalnon/juniper-ml/commits/b64eaaf/check-suites` returns exactly two apps — `cursor` (1210556) and `github-actions` (15368, ×4). No code-quality producer posts on a merged commit.
3. **[live 2026-08-09]** GraphQL introspection of `RepositoryRuleType` returns 32 values — `CREATION, UPDATE, DELETION, REQUIRED_LINEAR_HISTORY, MERGE_QUEUE, …, CODE_SCANNING, COPILOT_CODE_REVIEW, LICENSE_COMPLIANCE_SCANNING, …` — and **does not include `CODE_QUALITY`**, while REST reports `code_quality` on the ruleset. That asymmetry is the signature of a preview-stage rule.

### 3.7 Merge-queue rule — what is verifiable without mutating anything

**[live 2026-08-09]** GraphQL introspection confirms `MERGE_QUEUE` is a real `RepositoryRuleType`, and that
`MergeQueueParameters` has exactly seven **non-null** fields:

| GraphQL field | Type | REST snake_case (derived) |
|---|---|---|
| `checkResponseTimeoutMinutes` | `Int!` | `check_response_timeout_minutes` |
| `groupingStrategy` | `MergeQueueGroupingStrategy!` (`ALLGREEN`, `HEADGREEN`) | `grouping_strategy` (`ALLGREEN` / `HEADGREEN`) |
| `maxEntriesToBuild` | `Int!` | `max_entries_to_build` |
| `maxEntriesToMerge` | `Int!` | `max_entries_to_merge` |
| `mergeMethod` | `MergeQueueMergeMethod!` (`MERGE`, `SQUASH`, `REBASE`) | `merge_method` |
| `minEntriesToMerge` | `Int!` | `min_entries_to_merge` |
| `minEntriesToMergeWaitMinutes` | `Int!` | `min_entries_to_merge_wait_minutes` |

The REST spellings are a **derivation** from the GraphQL schema, not something this session observed on the
wire. The plan therefore recommends **UI-first configuration and API read-back** (§3.10/A4), so the canonical
JSON is captured from GitHub rather than hand-authored.

### 3.8 Local checkout freshness — the A6 item, re-scoped

**[live 2026-08-09]**, comparing each primary checkout's `refs/heads/main` against the remote tip:

| Repo | local `main` | remote `main` | `compare` verdict |
|---|---|---|---|
| **juniper-ml** | `be9f1319` | `577cd500` | **behind 2**, strict fast-forward (`status: ahead`, `behind_by: 0`) |
| **juniper-data-client** | `5d5b3801` | `e5042ae8` | **behind 1**, strict fast-forward |
| **juniper-cascor-client** | `94a21a55` | `1a99958b` | **behind 3**, strict fast-forward |
| juniper-cascor / canopy / data / cascor-worker / deploy | — | — | in sync |
| **juniper-recurrence** | `91cced96` | `91cced96` | **in sync — the tracked A6 item is already satisfied** |

The recurrence checkout carries both `.github/workflows/sequence-safety.yml` and `main-verify.yml` at mtime
2026-08-09 03:53, i.e. after recurrence#104/#105 merged. A6 is therefore re-scoped in §3.12.

---

## 3.9 A1 — Identify Integration `1276151` (and `946600`, and `1143301` on cascor)

### A1.1 Verified current state

`1276151` holds an **always** bypass on **all 8** ruleset repos (§3.2) — the widest grant of any Integration in
the fleet. `946600` holds one on 3 repos and was previously unrecorded. `1143301` is resolved: **Copilot SWE
Agent** (§3.2), present on cascor, data, deploy. `1210556`/`1236702`/`4362741`/`29110` are resolved.

Neither `1276151` nor `946600` resolves through any public-App endpoint reachable by the session token (§3.2).

### A1.2 Options

| Option | Description | Trade-off |
|---|---|---|
| **O1** | Owner names them in the UI, then decide KEEP / REMOVE per identity class. | Requires ~5 minutes of owner UI time. Only option that produces a *name*. |
| O2 | Remove both blind ("unknown ⇒ untrusted"). | Fast, but can silently break an integration the owner deliberately installed; the failure surfaces later as an unexplained blocked automation. Violates identify-first. |
| O3 | Leave as-is. | The status quo: two unnamed actors with unconditional authority to push, force-push, or delete `main` past all 8 rules on up to 8 repos. |

### A1.3 RECOMMENDATION

**O1 — identify first, then act.** This is the doctrine the research note already set (`…BYPASS-ACTOR-RESEARCH.md:48`),
and the census result strengthens it: an actor present on *every* repo is far more likely to be something the
owner installed on purpose than a stray.

### A1.4 Execution steps (owner UI; ~5 minutes)

The single most direct path — the **ruleset bypass list renders App names**, while the API returns only IDs:

1. Open `https://github.com/pcalnon/juniper-ml/settings/rules` → **juniper-ml-rules** → scroll to **Bypass list**.
   Record the display name shown beside each of the three unnamed rows (`1210556`/`1236702` will render as
   *Cursor* / *Claude*, which confirms the reading is correct; the third is `1276151`).
2. Repeat on `https://github.com/pcalnon/juniper-data/settings/rules` to name `946600` (it is absent from ml).
3. Cross-check the App ID (the UI shows names, not IDs). For an App **the owner created**:
   `https://github.com/settings/apps` → open the app → its settings page shows **App ID**. Match against
   `1276151` / `946600`. This is exactly how `4362741` is confirmable as the release-train App.
4. If it is *not* one of the owner's own Apps: `https://github.com/settings/installations` lists third-party
   Apps installed on the personal account; and `https://github.com/pcalnon/juniper-ml/settings/installations`
   lists Apps with access to that repo. Cross-reference by name.
5. Record the answer in this file's §11 decision table and in the bypass-actor research note.

Optional, cheap, non-mutating confirmation the token *can* do afterwards, if the App posts checks anywhere:

```bash
gh api repos/pcalnon/juniper-data/commits/main/check-suites --jq '.check_suites[]|[.app.id,.app.slug,.app.name]|@tsv'
```

### A1.5 What to do after identification, per plausible identity class

| Identity class | Action | Rationale |
|---|---|---|
| An App **the owner created** that pushes or merges `main` (a second automation like the release-train App) | **KEEP**, but narrow `always` → `pull_request` if it only ever lands via PR. | Mirrors the `4362741` posture: the narrowest mode that still works. |
| An App the owner created that only *reads* (dashboards, notifications, sync) | **REMOVE the bypass** (keep the installation). | A read-only App never needs to bypass branch rules; the entry is pure blast radius. |
| A third-party code-agent App (the Cursor/Claude/Copilot class) | **REMOVE the bypass**, same reasoning as A2. | Fleet PRs already traverse the full check battery; the grant adds risk, not capability. |
| A CI/security scanner that posts checks | **REMOVE the bypass**; a check producer never needs to skip rules. | — |
| Not identifiable even in the UI (orphaned installation) | **Uninstall the App**, which removes its ability to act; then remove the now-dead bypass row. | An unidentifiable actor with `always` on 8 repos is the worst case; removing the installation is stronger than removing the row. |

In every REMOVE case, apply it with the §3.7 helper exactly as A2 does (same mechanism, different ID list), one
repo at a time, verifying after each.

### A1.6 Verification probe

```bash
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '[.bypass_actors[]|(.actor_type + ":" + ((.actor_id // 0)|tostring) + ":" + .bypass_mode)]|join(" , ")'
```

Expect the removed ID to be absent and every retained entry byte-identical to §3.1.

### A1.7 Rollback

Re-add the removed row via the same helper with the snapshot JSON (§3.7 writes one before every PATCH), or in
the UI: Bypass list → Add bypass → select the App → set the recorded mode. Removing a bypass never destroys
data; the only cost of a wrong removal is a blocked automation, which fails loudly.

### A1.8 Residual note — the `DeployKey` bypass

Not proposed for change (owner retained the Turing keys, §3.3). Recorded for completeness: the
`DeployKey`/`always` row grants *any* holder of *any* writable deploy key on that repo the ability to push,
force-push, or delete `main` past all 8 rules, and `last_used` counts fetches, so an idle timestamp is not
evidence of non-use. If the owner later wants to keep the keys but drop the grant, the two are independent: the
bypass row can be removed while both keys stay installed, and the only flows that would break are ones that push
`main` over SSH with a deploy key — none was found in `util/`, `scripts/`, or `docs/` [research §3].

---

## 3.10 A2 — Remove the Cursor (`1210556`) and Claude (`1236702`) always-bypasses

### A2.1 Verified current state

Both hold `always` on juniper-ml (§3.1) and on most siblings (§3.2). Tracking issue **ml#1012** — *"[owner-decision]
Implement the ml#925 bypass-actor recommendations (remove cursor/claude always-bypass)"* — is **open** **[live 2026-08-09]**
and already carries the recommendation, so this section supplies the mechanics, not a new proposal. Do not open a
duplicate issue (D-5).

An `always` bypass skips **every** rule on **every** path, including a direct push to `main` and including
`required_signatures` and all 13 required contexts [research line 15].

### A2.2 Options

| Option | Description | Trade-off |
|---|---|---|
| **O1** | Remove both Integration rows on juniper-ml only. | Smallest blast radius; ml is where the fleet lands most volume and where the merge queue (A4) would go. |
| **O2** | Remove both on all 8 repos. | Consistent posture; 8 edits, 8 verifications, 8 rollback snapshots. |
| O3 | Narrow `always` → `pull_request` instead of removing. | Keeps a bypass for PR-merge paths only; but neither App self-merges [research line 522], so the narrowed grant is still unused — complexity with no benefit. |
| O4 | Leave as-is. | Two third-party code agents retain unconditional authority over `main` on 8 repos. |

### A2.3 RECOMMENDATION

**O1 now, O2 as a follow-up sweep.** Do juniper-ml first because it is the repo where A3/A4/A5 also land, so one
repo carries all the risk of the first attempt. Once ml is green for a week (one full weekly-workflow cycle),
repeat mechanically on the other 7 with the same helper.

Sequencing constraint (important): **land A3 before A2.** With `code_quality` still present and the bypass
removed, any actor that relies on auto-merge would sit forever behind a check that never reports (§3.6). Removing
the deadlock first means the removal cannot strand anything. See §7.1.

### A2.4 Execution — the derive-from-GET helper

Do **not** hand-author the PATCH body. `bypass_actors` is a full replacement, and the `DeployKey` row carries a
`null` `actor_id` that is easy to mistranscribe. The safe pattern is: GET → snapshot → filter → PATCH → verify.

Create `util/ad-hoc/2026-08-09_ruleset_edit.py` (single-use ⇒ `util/ad-hoc/` per D-8):

```python
#!/usr/bin/env python3
"""2026-08-09_ruleset_edit.py -- owner-gated ruleset editor (single-use, snapshot-first).

Derives every PATCH body from the LIVE GET so no field is hand-transcribed. Writes a timestamped
rollback snapshot before any mutation. --execute is required; default is a dry run that prints the
body and sends nothing. Ruleset edits are OWNER-GATED (plan D-1): a session runs this only on the
owner's explicit, per-invocation approval.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys


def gh_json(args):
    p = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)
    if p.returncode != 0:
        raise SystemExit(f"gh api failed: {p.stderr.strip()[:400]}")
    return json.loads(p.stdout)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Snapshot-first ruleset bypass/context editor.")
    ap.add_argument("--repo", required=True, help="owner/repo, e.g. pcalnon/juniper-ml")
    ap.add_argument("--ruleset", required=True, type=int)
    ap.add_argument("--snapshot-dir", required=True, help="rollback snapshots; NEVER inside a checkout")
    ap.add_argument("--drop-integration", action="append", type=int, default=[], help="repeatable App ID")
    ap.add_argument("--drop-rule", action="append", default=[], help="repeatable rule type, e.g. code_quality")
    ap.add_argument("--add-context", action="append", default=[], help="repeatable required status-check context")
    ap.add_argument("--execute", action="store_true", help="actually PATCH (default: dry run)")
    a = ap.parse_args(argv)

    cur = gh_json([f"repos/{a.repo}/rulesets/{a.ruleset}"])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snap = pathlib.Path(a.snapshot_dir).expanduser() / f"{a.repo.replace('/', '_')}-ruleset-{a.ruleset}-{stamp}.json"
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(cur, indent=2), encoding="utf-8")
    print(f"snapshot: {snap}")

    body: dict = {}
    if a.drop_integration:
        drop = set(a.drop_integration)
        keep, removed = [], []
        for b in cur["bypass_actors"]:
            (removed if (b.get("actor_type") == "Integration" and b.get("actor_id") in drop) else keep).append(b)
        print(f"bypass: removing {len(removed)} row(s): {[b.get('actor_id') for b in removed]}")
        if not removed:
            print("bypass: nothing to remove -- already absent (idempotent no-op)")
        body["bypass_actors"] = keep

    if a.drop_rule or a.add_context:
        rules = [r for r in cur["rules"] if r.get("type") not in set(a.drop_rule)]
        for r in rules:
            if r.get("type") == "required_status_checks" and a.add_context:
                have = {c["context"] for c in r["parameters"]["required_status_checks"]}
                for ctx in a.add_context:
                    if ctx in have:
                        print(f"context: {ctx!r} already required (no-op)")
                    else:
                        r["parameters"]["required_status_checks"].append({"context": ctx})
                        print(f"context: adding {ctx!r}")
        dropped = [r["type"] for r in cur["rules"] if r.get("type") in set(a.drop_rule)]
        if a.drop_rule:
            print(f"rules: dropping {dropped or '(none present)'}")
        body["rules"] = rules  # NOTE: full replacement, derived from the GET above

    print(json.dumps(body, indent=2))
    if not a.execute:
        print("DRY RUN -- nothing sent. Re-run with --execute after owner approval.")
        return 0

    p = subprocess.run(
        ["gh", "api", "-X", "PATCH", f"repos/{a.repo}/rulesets/{a.ruleset}", "--input", "-"],
        input=json.dumps(body), capture_output=True, text=True, check=False,
    )
    if p.returncode != 0:
        print(f"PATCH FAILED (nothing changed if the API rejected it): {p.stderr.strip()[:600]}", file=sys.stderr)
        print(f"rollback snapshot: {snap}", file=sys.stderr)
        return 1
    print("PATCH ok. Verify with the probe in the plan, then diff against the snapshot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Invocation for A2 (dry run first, always):

```bash
python3 util/ad-hoc/2026-08-09_ruleset_edit.py --repo pcalnon/juniper-ml --ruleset 13805432 --snapshot-dir ~/.local/state/juniper-ruleset-snapshots --drop-integration 1210556 --drop-integration 1236702
# review the printed body, then, on owner approval:
python3 util/ad-hoc/2026-08-09_ruleset_edit.py --repo pcalnon/juniper-ml --ruleset 13805432 --snapshot-dir ~/.local/state/juniper-ruleset-snapshots --drop-integration 1210556 --drop-integration 1236702 --execute
```

For review convenience, the **expected resulting `bypass_actors`** — derived from the §3.1 GET, to be re-derived
at execution time rather than pasted:

```json
{
  "bypass_actors": [
    { "actor_id": null, "actor_type": "DeployKey", "bypass_mode": "always" },
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" },
    { "actor_id": 1276151, "actor_type": "Integration", "bypass_mode": "always" },
    { "actor_id": 4362741, "actor_type": "Integration", "bypass_mode": "pull_request" }
  ]
}
```

(`1276151` stays until A1 names it. `4362741` stays at `pull_request` — see A3.)

UI equivalent, if the owner prefers: `Settings → Rules → juniper-ml-rules → Bypass list` → remove the *Cursor*
and *Claude* rows → Save.

### A2.5 Verification probe

The §A1.6 probe. Expect exactly the four rows above. Then confirm nothing else moved:

```bash
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '[.rules[].type]|join(",")'
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks|length'
```

Expect the §3.1 rule list (or the A3 result if A3 already landed) and `13` contexts (or `14` after A5).

Behavioural check: open (or observe) one `cursor/*` PR and confirm the merge box now shows the required checks
as gating rather than "bypassed".

### A2.6 Rollback

Re-run the helper with no `--drop-integration` is *not* a rollback (it is a no-op). Roll back by PATCHing the
`bypass_actors` array from the snapshot file:

```bash
python3 -c "import json,subprocess,sys;d=json.load(open(sys.argv[1]));subprocess.run(['gh','api','-X','PATCH','repos/pcalnon/juniper-ml/rulesets/13805432','--input','-'],input=json.dumps({'bypass_actors':d['bypass_actors']}),text=True,check=True)" ~/.local/state/juniper-ruleset-snapshots/<snapshot>.json
```

Cost of rollback: seconds. Cost of *not* rolling back a bad removal: an automation blocks loudly at merge time.
This is a low-stakes, fully reversible change.

---

## 3.11 A3 — The `code_quality`-rule-without-a-reporting-tool deadlock

### A3.1 Verified current state

`code_quality` (`severity: errors`) is rule #4 on juniper-ml (§3.1) and is present on **all 8** ruleset repos
(§3.2 rule lists). Nothing reports it (§3.6). It is the documented reason the release-train App holds a
`pull_request` bypass [research line 26, line 32]: without that bypass, the exempt notes-archive PR — which the
ceremony opens and auto-merges hands-free — would wait forever on a check that never arrives.

### A3.2 Options

| Option | Description | Trade-off |
|---|---|---|
| **Oa** | Attach a code-quality reporting tool so the rule can be satisfied. | The "correct" fix if the feature is available; but GitHub Code Quality is preview-stage (§3.6 signal 3), availability on a personal public repo is unverified, and it introduces a new blocking gate whose false-positive behaviour on this codebase is unknown. |
| **Ob** | **Drop the `code_quality` rule** from the ruleset. | One filtered rule, derived from the GET, instantly reversible. Removes a permanent deadlock. Security value lost today is zero — nothing evaluates it. CodeQL coverage is unaffected (separate `code_scanning` rule + the required `Analyze (python)` context). |
| Oc | Keep the rule and keep accreting per-App `pull_request` bypasses. | The status quo. Every future automation that needs auto-merge needs its own bypass row — the accretion mechanism that produced today's bypass list. |

### A3.3 RECOMMENDATION

**Ob — drop the rule on juniper-ml now**, and treat Oa as a separate, later evaluation if the owner wants a
code-quality gate. Reasons, in order:

1. A rule that can never be satisfied is not a control; it is a latent outage that manifests as "auto-merge hangs
   with no explanation". It has already cost one bypass-actor row.
2. It is the *root cause* under A2: leaving it in place while removing bypasses converts a dormant deadlock into
   an active one (§A2.3).
3. Its removal is the cheapest reversible experiment in this whole plan — one array element, snapshot-protected.

**KEEP `4362741` at `pull_request` for now.** Two reasons. First, one change at a time: dropping the rule and
removing the release-train's bypass in the same window makes a failed ceremony hard to attribute. Second — the
subtle one — while the bypass is in force the archive PR skips *all* rules, so we cannot observe whether it would
pass them; the only way to learn is to remove the bypass and watch one ceremony. That is a deliberate, separate
experiment (§A3.6).

### A3.4 Execution

```bash
python3 util/ad-hoc/2026-08-09_ruleset_edit.py --repo pcalnon/juniper-ml --ruleset 13805432 --snapshot-dir ~/.local/state/juniper-ruleset-snapshots --drop-rule code_quality
# then, on owner approval, re-run with --execute
```

UI equivalent: `Settings → Rules → juniper-ml-rules` → uncheck **Require code quality** → Save.

Note the helper sends `rules` as a **full replacement derived from the live GET**, so the `code_scanning`
thresholds, `strict_required_status_checks_policy: true`, `do_not_enforce_on_create: true`, and all 13 contexts
ride through byte-identical. That is exactly why it must not be hand-authored.

### A3.5 Verification probe

```bash
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '[.rules[].type]|join(",")'
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.rules[]|select(.type=="code_scanning")|.parameters'
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.rules[]|select(.type=="required_status_checks")|.parameters.strict_required_status_checks_policy'
```

Expect `code_quality` gone, seven rules remaining, CodeQL parameters unchanged (`errors` / `high_or_higher`), and
`strict` still `true`.

### A3.6 Follow-up experiment (separate, owner-gated, after one clean release-train cycle)

Remove `4362741`'s `pull_request` bypass and observe the next ceremony's archive PR. Expected: it now runs the 13
required contexts (a notes-only PR should pass all of them, and the `Release-Train Archive Guard` job is
explicitly designed to PASS an add-only, path-confined, name-valid archive PR — `.github/workflows/ci.yml:657-700`
[repo]) and auto-merges normally, in which case the bypass row is genuinely dead and stays removed.

Watch for two failure modes: (i) an archive PR that stalls, in which case restore the row from the snapshot; and
(ii) **latency** — the ceremony monitors to `PENDING_PYPI_APPROVAL` under `--monitor-timeout 900` (15 minutes),
set at `.github/workflows/release-train.yml:740` with the rationale at `:732` [repo]. Making the archive PR wait
on a full CI battery consumes that budget. If it becomes tight, raise the timeout in the same PR rather than
restoring the bypass.

### A3.7 Rollback

PATCH `rules` back from the snapshot, exactly as A2.6 does for `bypass_actors` (substitute the `rules` key).

---

## 3.12 A4 — Merge-queue availability check and rule addition

### A4.1 Verified current state

No `merge_queue` rule on juniper-ml (§3.1) or on any sibling (§3.2). The **prerequisites are already wired** on
juniper-ml [repo]:

- `.github/workflows/ci.yml:46-49` — `merge_group:` trigger, with the comment "required so every gating context re-runs on the queued merge commit … Without it no required context posts and the queue stalls".
- `.github/workflows/codeql.yml:27-29` — `merge_group:` trigger so the required `Analyze (python)` context re-posts.
  **This is the accepted CodeQL divergence**: juniper-ml is the only repo whose `codeql.yml` carries `merge_group`
  (cascor / canopy / data all have zero occurrences **[live grep 2026-08-09]**), while the file's own header
  (`codeql.yml:4-13`) declares it a fleet template. The divergence is deliberate and documented in-file;
  **propagate it to a sibling only when that sibling enables its own queue**, never as a “consistency” sweep.
- `ci.yml:657-680` — the `Release-Train Archive Guard` job admits `merge_group` and short-circuits to a green notice (`:675-677`), so the required context re-posts on a queued merge without re-diffing.
- `ci.yml:744` — the `Sequence Safety` job also runs on `merge_group`, and `ci.yml:409` notes merge_group is screened strict (no label hatch, since there is no PR object).
- `docs/REFERENCE.md:1558-1567` already documents the concurrency/merge-queue contract, and `:1627` lists "Merge queue stuck with no required check" as an operator pitfall.

`allow_auto_merge: true` on juniper-ml **[live 2026-08-09]**.

**Availability is the open question.** The owner reports having seen a `422` when adding a merge-queue rule on a
personal repository, possibly plan-gated. This session cannot test it without mutating a config, which is out of
scope. What *is* established: `MERGE_QUEUE` exists in the live GraphQL rule-type enum (§3.7), and juniper-ml is a
**public** repo owned by a **User** (§3.1) — the configuration most likely to be supported, but not proof.

### A4.2 Options

| Option | Description | Trade-off |
|---|---|---|
| **O1** | Verify availability in the UI, and if available add the rule **in the same change window as A2**. | The flagship fix: a queue validates the *actual merge result* before landing, which is the only lever that binds the union-merge class the fleet produces [flood analysis lines 524, 566]. |
| O2 | Skip the queue; rely on `strict_required_status_checks_policy: true` (already on). | Strict re-runs checks against an updated base but does not validate the merge result and does not bind. Already in place, so this is "do nothing more". |
| O3 | Add the queue but keep the App bypasses. | Pointless: a bypassing actor skips the `merge_queue` rule along with everything else, so the queue would bind nothing new. |

### A4.3 RECOMMENDATION

**O1, coupled to A2, and only if the UI confirms availability.** The coupling is the whole point: the queue binds
non-bypassing actors, so it takes effect on fleet PRs exactly when (and only when) the Cursor/Claude always-bypass
rows are gone. Conversely `RepositoryRole 5`/always **stays**, so the owner's admin batch-merge path is *not*
queued — which is the desired asymmetry (fleet PRs queue; owner batches do not).

If the UI shows the rule is unavailable, **stop**: record the observation in §11 and keep `strict=true` as the
fallback. Do not attempt an API-only workaround for a feature the UI says is not offered.

### A4.4 Execution steps

**Step 1 — availability verification (UI, owner, ~2 minutes).**
`https://github.com/pcalnon/juniper-ml/settings/rules` → **juniper-ml-rules** → **Add rule**. Look for
**"Require merge queue"** in the rule list.

- If it is **absent or disabled/greyed with an upgrade prompt** → unavailable. Record and stop.
- If it is **present** → tick it, leave the defaults GitHub proposes, **Save**. If saving returns `422`, that is
  the reported plan-gate manifesting; record the exact message and stop.

**Step 2 — read back the canonical JSON** (this is why UI-first is recommended: it produces the authoritative
parameter set instead of a derived guess):

```bash
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.rules[]|select(.type=="merge_queue")'
```

Paste that object into §11 of this document and into `docs/REFERENCE.md`'s merge-queue subsection so the rollback
and any sibling rollout use observed values.

**Step 3 — API-only alternative** (use only if the owner prefers scripting and Step 1 confirmed availability).
The rule object has this shape, with parameter names **derived** from the live GraphQL schema (§3.7) and therefore
to be confirmed by the Step-2 read-back before being relied on:

```json
{
  "type": "merge_queue",
  "parameters": {
    "check_response_timeout_minutes": 60,
    "grouping_strategy": "ALLGREEN",
    "max_entries_to_build": 5,
    "max_entries_to_merge": 5,
    "merge_method": "SQUASH",
    "min_entries_to_merge": 1,
    "min_entries_to_merge_wait_minutes": 5
  }
}
```

Parameter rationale for this repo: `merge_method: SQUASH` matches the house squash convention (and
`ceremony.py:783` enables auto-merge with `--squash` [repo]); `min_entries_to_merge: 1` with a short wait keeps
single-PR latency low; `ALLGREEN` is the conservative grouping (a failing entry does not drag its neighbours in);
`check_response_timeout_minutes: 60` comfortably exceeds the observed `ci.yml` wall time. All seven fields are
non-null in the schema, so all seven must be supplied.

**Step 4 — order with A2.** Add the queue rule **and** remove the two App bypasses in the same session, queue
first, bypasses second, verifying between. If the queue turns out to misbehave, removing it restores the
pre-change behaviour even with the bypasses already gone (fleet PRs then simply face the normal required checks).

### A4.5 Verification probe

```bash
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '[.rules[].type]|join(",")'
```

Then a **live behavioural** check, which matters more than the JSON: take one small, low-risk PR (a docs slice
from Part D is ideal), press **Merge when ready**, and confirm:

1. the PR enters the queue rather than merging immediately;
2. a `merge_group` run of `ci.yml` **and** of `codeql.yml` appears, and every one of the required contexts
   re-posts on it (this is the stall class `docs/REFERENCE.md:1627` warns about);
3. the queued commit lands on `main` and post-merge `main-verify.yml` runs normally.

If any required context fails to post on the `merge_group` run, remove the rule immediately (A4.6) and fix the
trigger wiring before retrying.

### A4.6 Rollback

`Settings → Rules → juniper-ml-rules` → delete the merge-queue rule (or `--drop-rule merge_queue` with the §A2.4
helper). Any PR already sitting in the queue merges or is ejected normally; nothing is lost. Restore
`bypass_actors` from the snapshot if the queue is being rolled back because bypass removal proved premature.

### A4.7 Interaction warnings (read before enabling)

1. **The release-train archive lane.** While `4362741` holds its `pull_request` bypass it also skips the
   `merge_queue` rule, so the ceremony's archive PR still merges immediately. If A3.6's follow-up experiment
   removes that bypass *while a queue is live*, the archive PR joins the queue and the ceremony's
   `--monitor-timeout 900` (`release-train.yml:740`) must absorb the extra latency. **Do not do both at once.**
2. **Owner "Update branch" habit.** With a queue, manually updating a branch before merge is redundant and adds
   churn; the queue builds the merge itself.
3. **Consumers are not ready.** No sibling `sequence-safety.yml` listens on `merge_group` (§3.5). Enabling a queue
   on a sibling *after* promoting that context to required (A5) would stall it. Order there is: wire
   `merge_group` into the sibling's workflows first, then queue.

---

## 3.13 A5 — The ~2026-08-21 sequence-safety promotion call

### A5.1 Verified current state

Advisory everywhere. Soak evidence in §3.5: **60 successes, 1 cancellation, 0 failures** across the 8 standalone
consumer workflows, plus **15/15** on juniper-ml's in-`ci.yml` job. Tracking issue **ml#1011** —
*"[owner-decision] Promote per-PR Sequence Safety to a required check"* — is **open** **[live 2026-08-09]** and
already states the exact change and rollback; this section supplies the per-repo mechanics it does not have. Do
not open a duplicate (D-5).

Rollout-plan decision **D8** (`…SEQUENCE-SAFETY-ROLLOUT-PLAN.md:347`) deferred promotion to "later, per-repo,
after soak", and §10 of that plan (`:354-363`) notes every wave is reversible *precisely because* nothing is
required yet — so promotion is the one step that exits that safety property, and it must be per-repo and
individually reversible.

Promotion criterion (rollout plan D8 as operationalized in the arc): **a storm survived OR ~2 weeks clean.** The
2026-08-07 storm drain processed ~75 PRs against the screens with zero false blocks (ml#1011 body), so the first
disjunct is arguably already met for juniper-ml and juniper-cascor; the ~2026-08-21 date is the second disjunct
for the repos that have only 1-3 runs.

### A5.2 The decision checklist (run this on ~2026-08-21)

Promote a repo only if **all** of the following hold for that repo:

| # | Check | How |
|---|---|---|
| C1 | Zero `failure` conclusions on its sequence-safety runs since 2026-08-07 | `gh api -X GET repos/pcalnon/<repo>/actions/workflows/sequence-safety.yml/runs -f per_page=100 --jq '.workflow_runs[].conclusion'` (juniper-ml: the `Sequence Safety` job in `ci.yml`) |
| C2 | ≥5 runs, or one storm-scale batch | Same probe; count. A repo with 1 run has not soaked. |
| C3 | No open finding awaiting adjudication | `gh issue list --repo pcalnon/<repo> --state open --label main-verify` and the `sequence-safety-report` artifact of the last red, if any |
| C4 | Its `main-verify.yml` post-merge screen has been green | `gh api -X GET repos/pcalnon/<repo>/actions/workflows/main-verify.yml/runs -f per_page=30 --jq '.workflow_runs[].conclusion'` |
| C5 | The waiver path has been exercised at least once fleet-wide | Already true: both the label hatch and the trailer escapes are proven in live use (ml#1011) |
| C6 | The repo has **no** merge queue, or its sequence-safety workflow listens on `merge_group` | §3.5 — today no consumer does, so C6 reduces to "no queue there", which is true for all 8 |

**Keep-advisory fallback.** C1/C2 are per-repo. If any repo shows a flake or has too few runs, promote the rest
and leave that one advisory; the workflows are independent files, so a partial promotion is coherent and needs no
coordination. Record which repos were held and re-check at the next cadence point.

### A5.3 Per-repo promotion mechanics — exact contexts

**Do not** promote by adding the job to a Quality-Gate `needs:`. `ci.yml:724-731` [repo] documents why in the
job's own header: the job is `pull_request`/`merge_group`-only and the Quality Gate is `if: always()` treating any
non-success need as fatal, so folding it in would fail every push to `main`. Promotion happens **in branch
protection**, and only there. `docs/REFERENCE.md:1593` states the same rule.

| Repo | Mechanism | **Exact context string** | Notes |
|---|---|---|---|
| juniper-ml | Ruleset `13805432` → `required_status_checks` | **`Sequence Safety`** | From `ci.yml:742`. **Not** "(Advisory)" — ml's job name has no suffix. Takes the required count 13 → 14. Runs on `merge_group` (`ci.yml:744`), so it is queue-safe. |
| juniper-cascor | Ruleset `15081045` | `Sequence Safety (Advisory)` | `sequence-safety.yml:80` |
| juniper-canopy | Ruleset `14249530` | `Sequence Safety (Advisory)` | `sequence-safety.yml:95` |
| juniper-data | Ruleset `14748749` | `Sequence Safety (Advisory)` | `sequence-safety.yml:84` |
| juniper-data-client | Ruleset `13316681` | `Sequence Safety (Advisory)` | remote `sequence-safety.yml:93` |
| juniper-cascor-client | Ruleset `13490605` (`Bubba Says No`) | `Sequence Safety (Advisory)` | remote `sequence-safety.yml:89` |
| juniper-cascor-worker | Ruleset `14250447` | `Sequence Safety (Advisory)` | `sequence-safety.yml:90` |
| juniper-deploy | Ruleset `14715370` | `Sequence Safety (Advisory)` | `sequence-safety.yml:94` |
| **juniper-recurrence** | **CLASSIC branch protection** (no ruleset) | `Sequence Safety (Advisory)` | `sequence-safety.yml:85`. Different API surface — see A5.5. |

The "(Advisory)" suffix is part of the **name**, so it stays in the required context string even after promotion.
Renaming the job to drop the word would be a cosmetic change that breaks the required context — if the owner wants
the rename, it must be a separate PR that lands the rename and the context edit atomically, and it is not
recommended.

### A5.4 Execution — the 8 ruleset repos

```bash
python3 util/ad-hoc/2026-08-09_ruleset_edit.py --repo pcalnon/juniper-ml --ruleset 13805432 --snapshot-dir ~/.local/state/juniper-ruleset-snapshots --add-context 'Sequence Safety'
# review, then --execute

python3 util/ad-hoc/2026-08-09_ruleset_edit.py --repo pcalnon/juniper-cascor --ruleset 15081045 --snapshot-dir ~/.local/state/juniper-ruleset-snapshots --add-context 'Sequence Safety (Advisory)'
# ... and so on per the A5.3 table
```

UI equivalent per repo: `Settings → Rules → <ruleset> → Require status checks to pass` → add the context by name.

### A5.5 Execution — juniper-recurrence (classic protection)

The whole-protection `PUT` is a **full replacement** of the protection object and is the wrong tool here: a
mistake silently drops `required_signatures`, the review requirement, or a context. Use the narrow sub-resource,
which was confirmed to exist **[live 2026-08-09]** (`…/protection/required_status_checks` with a `contexts_url`).

Preferred — additive, cannot disturb the other three contexts or any other protection field:

```bash
gh api -X POST repos/pcalnon/juniper-recurrence/branches/main/protection/required_status_checks/contexts -f 'contexts[]=Sequence Safety (Advisory)'
```

Snapshot first:

```bash
gh api repos/pcalnon/juniper-recurrence/branches/main/protection --jq . > /dev/null  # capture via the ad-hoc helper's snapshot pattern instead of a shell redirect
```

Caveat to record: the three existing entries appear in the `checks` form pinned to `app_id: 15368` (GitHub
Actions). A context added through the `contexts` endpoint is stored with **no app pinning**, so any app could in
principle satisfy it. If the owner wants parity, use the `checks` form on the sub-resource instead:

```bash
gh api -X PATCH repos/pcalnon/juniper-recurrence/branches/main/protection/required_status_checks --input -
# body: {"strict": true, "checks": [ …the three existing {context, app_id:15368} objects…, {"context":"Sequence Safety (Advisory)","app_id":15368} ]}
```

Build that body by filtering the live GET, never by hand — same doctrine as A2.4. Note the em dash in
`Test — torch MLP readout (Rung 2b; optional [torch] extra)`; a transcription that turns it into a hyphen silently
creates a **new, never-satisfied** required context and blocks the repo. Deriving from the GET eliminates that
class entirely.

Also note `enforce_admins: false` on recurrence, so the owner is not bound by the new context there — the same
asymmetry as `RepositoryRole 5` elsewhere.

### A5.6 Verification probe

```bash
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context'
gh api repos/pcalnon/juniper-recurrence/branches/main/protection/required_status_checks --jq '{strict:.strict, contexts:.contexts}'
```

Then behavioural, per repo: open (or re-run) one PR and confirm the sequence-safety check appears in the
**Required** section of the merge box, and that a clean PR still merges.

### A5.7 Rollback

Remove the context: `--drop`-style filter on the ruleset (or the UI checkbox); on recurrence,
`gh api -X DELETE …/protection/required_status_checks/contexts -f 'contexts[]=Sequence Safety (Advisory)'`. The
job stays advisory exactly as today — this is precisely the rollback ml#1011 already promises.

### A5.8 Residual risk

Promotion removes the rollout plan's "nothing is required" reversibility property (`…ROLLOUT-PLAN.md:351-352`).
Mitigation is layered and already built: the `allow-symbol-loss` / `docs-rewrite` labels give a per-PR WARN-only
downgrade read live via `gh pr view` (`ci.yml:789-797`), and the `Allow-Symbol-Loss` / `Allow-Docs-Rewrite`
commit trailers remain the primary auditable waiver that also covers post-merge `main-verify`. A promoted context
is therefore never a hard wall.

---

## 3.14 A6 — Housekeeping

### A6.1 Local checkout freshness — re-scoped

The tracked item ("ff-pull Paul's local juniper-recurrence checkout") is **already satisfied**: that checkout is
at the remote tip `91cced96` **[live 2026-08-09]** (§3.8). Close it.

Three *other* primary checkouts are behind, all strict fast-forwards (§3.8). Exact commands (run each from
outside the repo, so no CWD trap):

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-ml status --porcelain
git -C /home/pcalnon/Development/python/Juniper/juniper-ml fetch origin
git -C /home/pcalnon/Development/python/Juniper/juniper-ml pull --ff-only origin main

git -C /home/pcalnon/Development/python/Juniper/juniper-data-client fetch origin
git -C /home/pcalnon/Development/python/Juniper/juniper-data-client pull --ff-only origin main

git -C /home/pcalnon/Development/python/Juniper/juniper-cascor-client fetch origin
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor-client pull --ff-only origin main
```

Run the `status --porcelain` check first on each: `--ff-only` refuses to clobber, but a dirty tree means a session
left work behind and that should be understood before pulling. Note this is the same restoration
`util/worktree_cleanup.bash:484` Phase 7 performs automatically after a merged-PR cleanup, and it skips on a dirty
tree by design [repo] — the three behind checkouts are simply ones whose last cleanup did not run.

Verification: re-run the §3.8 comparison; each local `main` should equal the remote tip.
Rollback: none needed — a fast-forward creates nothing and discards nothing.

### A6.2 Stale `~/.claude.json` project entries

**[live 2026-08-09]** `~/.claude.json` has 7 `projects` keys, of which **five point at directories that do not
exist**:

- `…/Juniper/JuniperCanopy/juniper_canopy` — carries `mcpServers`: alphavantage, exa, hf-mcp-server, kaggle, **serena**
- `…/Juniper/JuniperCascor/juniper_cascor` — carries hf-mcp-server, kaggle, **serena**
- `…/Juniper/JuniperData/juniper_data` — carries **serena**
- `…/Juniper/juniper` — no `mcpServers`
- (the two live entries, `…/Juniper` and `…/Juniper/juniper-cascor`, have no `mcpServers`; `…/Juniper/juniper-ml` has `playwright` only)

These are the pre-polyrepo paths [audit `A2-F9`, `L7`]. Each dead serena entry launches
`uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context claude-code --project <dead path>`.

**Recommendation: prune the five dead keys — but only *after* Part C lands.** They are inert (Claude Code keys
project config by CWD, and none of those CWDs exists), and they are the only surviving record of how serena was
once wired, which §6.1 uses as the shape reference. Prune as a single local edit with a backup:

```bash
python3 -c "import json,shutil,os,datetime;p=os.path.expanduser('~/.claude.json');shutil.copy2(p,p+'.bak-'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S'));d=json.load(open(p));dead=[k for k in d.get('projects',{}) if not os.path.isdir(k)];print('would remove:',dead)"
```

Run that first (it only prints). Only when the list matches the five above, re-run with the removal and a
`json.dump` back. Claude Code must not be running while `~/.claude.json` is rewritten, or it will be overwritten
on exit. Rollback: restore the `.bak-*` copy.

Optional, lower value: the worktree `.claude/` directory holds six stale `settings.local-*` backups and no active
settings file [audit `L6`]; `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/settings.local-ORIG_{1..5}.json`
and `settings.local-WORKING.json` **[live 2026-08-09]**. Deleting them is cosmetic; not recommended as part of
this arc.

---

# PART B — Headless-signing preflight and fix

## 4. Part-B ground truth (verified this session)

### 4.1 The signing identity is already correct

**[live 2026-08-09]** `git config --global`:

| Key | Value |
|---|---|
| `user.signingkey` | `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!` |
| `gpg.program` | `gpg2` |
| `commit.gpgsign` | `true` |
| `tag.gpgsign` | `true` |
| `user.name` / `user.email` | `Paul Calnon` / `paul.calnon@gmail.com` |

**[live 2026-08-09]** keyring (`gpg2 --list-secret-keys --with-colons`, GnuPG 2.4.8):

- Certify primary `084FA27B796DABC4`, fpr `06DBAC384131E0380D89923F084FA27B796DABC4`, ed25519, capability `cESCA`, secret **not** available locally (`#` — offline, as designed).
- Signing subkey `BA18D1A733B1831A`, fpr **`B5619F58FDA4D94E2D73D8BABA18D1A733B1831A`**, ed25519, card-bound.
- Encrypt `57E275E9F67430CE` (cv25519) and auth `F6D949CF7D344E31` (ed25519), same card binding.
- Legacy rsa4096 `B5AFCD0686585249` (card `…0006 09258397`) — the 2019 key, expired resolution path.
- ed448 `93E8591643C507FF` — secret material **on disk** (`+`), signing-capable.

### 4.2 The card gotcha, and why serial comparison is the wrong check

**[live 2026-08-09]** all three subkey stubs record card serial `D2760001240100000006**24955323**0000`, while
`gpg2 --card-status --with-colons` reports the **connected** card as `serial:24955114:` — the backup YubiKey. The
card's `fpr:` line is `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A:7F69F9332EAFB7ECA3F4AE5257E275E9F67430CE:301C7D6201E3158A6A6EEF68F6D949CF7D344E31:` — i.e. the **signature slot carries exactly the expected subkey**, and
`uif:0:1:1:` (Sign UIF off, so no touch is required).

Running `--card-status` did **not** rewrite the stub to `24955114`. So the stub/card serials remain mismatched.

**And signing still works.** **[live 2026-08-09]**, bounded and side-effect-free:

```text
timeout 25 gpg2 --status-fd 1 --local-user 'B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!' --detach-sign --output /dev/null <file>
  [GNUPG:] KEY_CONSIDERED 06DBAC384131E0380D89923F084FA27B796DABC4 0
  [GNUPG:] BEGIN_SIGNING H10
  [GNUPG:] SIG_CREATED D 22 10 00 1786314535 B5619F58FDA4D94E2D73D8BABA18D1A733B1831A
  exit 0
```

This is a direct, reproducible answer to the audit's §8 open item 3 ("whether the card-serial mismatch actually
stalls a signature"): on this host, in an agent-cached session, **it does not**. The design consequence is
concrete — the preflight must compare the **card's signature-slot fingerprint**, and must **accept any serial**
that carries it. A preflight that compared serials would false-fail today on the working backup card.

### 4.3 Signature census on `main` — the two classes, visible

**[live 2026-08-09]** `git log --format='%h %G? %GK %s'` in this worktree:

| Commit | `%G?` | `%GK` | Class |
|---|---|---|---|
| `b64eaaf` | `E` | `B5690EEEBB952194` | GitHub-signed squash merge (`E` locally only because the keyring lacks GitHub's web-flow public key) |
| `e835e2b` | `E` | `B5690EEEBB952194` | same |
| `731302a` | **`G`** | **`BA18D1A733B1831A`** | locally signed with the correct ed25519 subkey |
| `5ff81d8`, `1d2e376`, `386c78e` | `G` | `BA18D1A733B1831A` | same |

Two signing paths coexist and must not be conflated: **local** commits (owner host, ed25519 card) and **GitHub**
commits (API/merge, web-flow key). Only the first needs a preflight.

### 4.4 The gap

There is **no** preflight anywhere. The repo's only signing-validation artifact is
`util/test_gpg_signing.bash:3-7` [repo], four lines that hard-code `93E8591643C507FF` — the **superseded ed448
key** [audit `A1-F1`] — with no timeout, no fingerprint assertion, and no failure contract. The canonical signing
note is likewise stale [audit `A1-F2`]. No `.github/` file in any of the nine repos references signing config at
all [audit `G18`].

Existing mitigations that make today tolerable (and that the preflight must **not** disturb) [repo]:

- `util/release_train/propose.py:985,1441-1444` — `-c commit.gpgsign=false` on proposal commits.
- `util/fleet_triage/predict_merge.py:84-90` — `-c commit.gpgsign=false` / `-c tag.gpgsign=false` on throwaway merges.
- `.github/workflows/release-train.yml:478,687` — `git config --global commit.gpgsign false` in both write jobs.
- `util/release_train/ceremony.py` — archive commits via `createCommitOnBranch`, GitHub-signed [audit `G17`].

---

## 5. Design — `util/headless_signing_preflight.bash`

### 5.1 Purpose and placement

A permanent, read-only, timeout-bounded gate that answers one question with a machine-checkable verdict: *can this
host produce a correctly-signed local commit right now, unattended?* Permanent utility ⇒ `util/` (D-8). Bash,
because the callers are bash and it must be shellcheck-clean under the repo-wide hook
(`.pre-commit-config.yaml:205-212`, `--severity=warning`, `files: \.(sh|bash)$` [repo]).

It **replaces** `util/test_gpg_signing.bash`; that file is deleted in the same PR (which is itself a symbol-loss
event for the sequence-safety screen — see §7.4).

### 5.2 Constants

```bash
# The ed25519 signing SUBKEY fingerprint. Source of truth: `gpg2 --list-secret-keys --with-colons`
# (subkey BA18D1A733B1831A) and `git config --global user.signingkey`, both verified 2026-08-09.
# The primary certify key 06DBAC384131E0380D89923F084FA27B796DABC4 is offline and is NOT used to sign.
readonly EXPECTED_SIGNING_FPR="B5619F58FDA4D94E2D73D8BABA18D1A733B1831A"
```

One constant, one key. The test suite asserts no *second* 40-hex fingerprint appears in the file (§5.9 arm 12), so
a future edit cannot quietly reintroduce a stale key alongside the right one.

### 5.3 The four checks

| # | Check id | What it proves | How | FAIL when |
|---|---|---|---|---|
| C1 | `git-config` | Git is configured to sign with the expected key. | `git config --global --get user.signingkey`, strip a trailing `!`, upper-case, compare to `EXPECTED_SIGNING_FPR`; also read `gpg.program` (default `gpg2`) and `commit.gpgsign`. | mismatch, unset, or `commit.gpgsign` not `true`. A short key-id (16 hex) that is a **suffix** of the expected fingerprint is a WARN, not a pass — it is ambiguous, which is the exact class that produced the 2019 `KEYEXPIRED` incident [audit `A1-F6`]. |
| C2 | `toolchain-card` | The signing binary exists and a card is present. | `command -v "$GPG_BIN"`; then `timeout "$CARD_TIMEOUT" "$GPG_BIN" --card-status --with-colons`. | binary missing, non-zero exit, timeout, or no `serial:` line. |
| C3 | `card-signature-slot` | The **present** card carries the expected signing subkey. | Parse the `fpr:` colon record from C2's output; field 2 is the signature-slot fingerprint. Compare to `EXPECTED_SIGNING_FPR`. **Record the serial; never compare it.** | signature-slot fingerprint ≠ expected, or no `fpr:` record. |
| C4 | `test-signature` | A signature can actually be produced **right now, unattended** (PIN cached / no touch required). | `timeout "$SIGN_TIMEOUT" "$GPG_BIN" --batch --no-tty --status-fd 1 --local-user "${EXPECTED_SIGNING_FPR}!" --detach-sign --output /dev/null "$SELF"` where `$SELF` is the script's own path. Require exit 0 **and** a `[GNUPG:] SIG_CREATED` status line naming `EXPECTED_SIGNING_FPR`. | non-zero exit, timeout, missing `SIG_CREATED`, or `SIG_CREATED` naming a different fingerprint. |

Four notes that are load-bearing:

- **C3 accepts any serial by design** (§4.2). The reason is stated in the script's own comment so a later
  "hardening" does not add a serial comparison: the keyring stubs bind `24955323`, the working backup card is
  `24955114`, and signing succeeds across that mismatch. Both cards carry the same subkey; either is acceptable.
- **C4 never trusts the exit code alone.** `SIG_CREATED` with the right fingerprint is the only proof; an exit-0
  from a wrapper or a differently-keyed signature must fail.
- **`--batch --no-tty` and never `--pinentry-mode loopback`.** With `--batch --no-tty`, an uncached PIN fails fast
  instead of prompting. Loopback is explicitly warned against for flows involving both a passphrase and a card PIN
  (`docs/REFERENCE.md:1657` [repo]) and would defeat the point of the check.
- **`timeout` on every external call** is the belt to `--batch`'s braces: even a pathological pinentry cannot hang
  a headless flow. Defaults: `--card-timeout 15`, `--timeout 20`, both overridable.

### 5.4 CLI, exit codes, output

```text
util/headless_signing_preflight.bash [--json] [--quiet] [--timeout N] [--card-timeout N]
                                     [--file-issue] [--repo OWNER/REPO]
                                     [--expect-fpr FPR] [--gpg-bin PATH] [--git-bin PATH]
```

| Exit | Meaning |
|---|---|
| `0` | all four checks pass — the calling flow may proceed unattended |
| `1` | ≥1 check FAILed — the calling flow must **stop** |
| `2` | misuse (bad flag, non-numeric timeout) |

`--expect-fpr` / `--gpg-bin` / `--git-bin` exist for the hermetic tests (same spirit as `JUNIPER_ML_REPO_ROOT` in
`util/install_agents.bash` and `JUNIPER_CONDA_DIR` in `util/check_conda_env_torch.bash` [repo]); `--expect-fpr`
must be logged loudly when used, so an override can never be mistaken for a real pass.

`--json` emits one object:

```json
{
  "status": "ok",
  "host": "yamaguchi",
  "expected_fpr": "B5619F58FDA4D94E2D73D8BABA18D1A733B1831A",
  "card_serial": "24955114",
  "checks": [
    {"id": "git-config", "status": "OK", "reason": "user.signingkey matches (commit.gpgsign=true, gpg.program=gpg2)"},
    {"id": "toolchain-card", "status": "OK", "reason": "gpg2 2.4.8; card serial 24955114"},
    {"id": "card-signature-slot", "status": "OK", "reason": "signature slot carries the expected subkey (serial not compared)"},
    {"id": "test-signature", "status": "OK", "reason": "SIG_CREATED by B5619F58...831A in 0.4s"}
  ]
}
```

### 5.5 Failure contract — a blocked merge is never silent

Three layers, in order:

**(1) Non-zero exit.** Callers use it directly; no output parsing required.

**(2) An unmistakable multi-line stderr banner.** Deliberately louder than the repo's usual `log_error`, because
its audience is a human scanning a headless transcript:

```text
################################################################################
##
##  HEADLESS SIGNING PREFLIGHT: BLOCKED
##
##  failed check : card-signature-slot
##  reason       : connected card's signature slot carries 7F69F933...30CE,
##                 expected B5619F58...831A
##  card serial  : 24955114   (serial is informational; not a pass/fail input)
##
##  NOTHING WAS SIGNED, COMMITTED, PUSHED, OR MERGED.
##
##  Remediation:
##    1. Insert a YubiKey whose SIGNATURE slot holds B5619F58...831A
##       (primary 24955323 or backup 24955114 both qualify).
##    2. Warm the PIN cache once:  <the C4 command, run interactively>
##    3. Re-run this preflight. On exit 0 the blocked flow resumes with no
##       further manual steps.
##
##  Detail: notes/JUNIPER_2026-08-09_..._STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md §5
################################################################################
```

**(3) An opt-in, stable-title tracking issue on juniper-ml** (`--file-issue`; off by default so an interactive run
does not file issues, on in every headless wrapper). This reuses the `main-verify.yml` notify dedup pattern
verbatim in structure, adapted for a locally-run script:

- Stable title: `headless-signing preflight: blocked on <hostname>` — one issue per blocked streak, mirroring
  `main-verify.yml:401` and the rationale at `:408-411`.
- **Authorship-bound match**, mirroring `main-verify.yml:421`: query
  `repos/<REPO>/issues?state=open&creator=<LOGIN>&per_page=100` (with `LOGIN` from `gh api /user --jq .login`) and
  select `.pull_request == null` **and** exact title. The `#928` lesson stated in `main-verify.yml:413-420` is that
  on a public repo a title alone is forgeable and must never be the trust boundary; the local analogue of
  `github-actions[bot]` is the running `gh` identity, so the creator binding is preserved rather than dropped.
- Existing open issue → `gh issue comment` with the new timestamp, failed check, and card serial
  (`main-verify.yml:422-435` shape). No existing issue → `gh label create headless-signing … 2>/dev/null || true`
  then `gh issue create` (`main-verify.yml:464-470` shape).
- **The issue upsert can never mask the verdict.** Any `gh` failure prints `preflight: tracking issue could not be
  filed (<reason>)` to stderr and the script still exits `1`. This inverts `main-verify.yml:472-473` (where a failed
  create *is* the failure) because here the tracker is a notification, not the point.
- **Never auto-close on recovery.** Same convention as `main-verify.yml:460-461`: the owner closes after
  adjudication. A subsequent green run does not touch the issue.

**Post-restore behaviour.** The script is idempotent and read-only, so after the owner re-inserts the card and/or
warms the PIN, re-running it returns `0` and the blocked flow proceeds with **no** manual intervention beyond that
re-run. Callers should therefore invoke it at flow start, not cache a result.

### 5.6 Integration points — which flows call it, and which must not

The discriminator is precise: **does this flow create a git object that `commit.gpgsign` / `tag.gpgsign` will
cause the local GPG to sign?** If yes → preflight. If the object is created by GitHub → no preflight.

**MUST call (blocking):**

| Flow | Anchor [repo] | Why |
|---|---|---|
| `util/worktree_cleanup.bash`, non-`main` parent path | `:361-364` — `checkout` / `pull` / **`merge`** / `push` | Line 363 creates a **new local merge commit** under `commit.gpgsign=true`. If signing is broken this fails mid-phase, after Phase 2 has already created a new worktree. Call the preflight once in `main()` before Phase 1 whenever `PARENT_BRANCH != main` (skip under `--dry-run`). |
| Any session flow that will `git commit` locally on this host | — | The agent's own arc commits. Invoke at session start (see below) or immediately before the first commit. |
| `git tag -s` / release-tag creation on the host | — | `tag.gpgsign=true`. Not currently in any script, but stated so a future one inherits the rule. |

**SHOULD call (advisory, non-blocking):**

| Flow | Anchor [repo] | Why |
|---|---|---|
| `scripts/wake_the_claude.bash` / `scripts/claude_interactive.bash` | — | A session-start advisory run makes the state visible in the transcript *before* work accumulates. Advisory (WARN, exit ignored) so an unplugged card cannot block a read-only or planning session. |

**MUST NOT call (these are GitHub-signed or deliberately unsigned):**

| Flow | Anchor [repo] | Why |
|---|---|---|
| `util/release_train/propose.py` | `:985`, `:1441-1444` | Explicitly `-c commit.gpgsign=false`; runs on a CI runner with no key. |
| `util/fleet_triage/predict_merge.py` | `:84-90` | Throwaway detached-clone merges, signing disabled, never pushed. |
| `.github/workflows/release-train.yml` propose/ceremony jobs | `:478`, `:687` | `git config --global commit.gpgsign false`; there is no card in a runner. |
| `util/release_train/ceremony.py` archive commit | `createCommitOnBranch` [audit `G17`] | GitHub creates and signs the commit; that is *why* it satisfies `required_signatures` hands-free. |
| `gh pr merge` / queued merges | — | The merge commit is GitHub-signed (`%GK B5690EEEBB952194`, §4.3). |

Wiring `worktree_cleanup.bash`: add an early guard, not a per-phase sprinkle.

```bash
# in main(), before phase_1_save_and_push:
if [[ "${DRY_RUN}" != "${TRUE}" && ( "${PARENT_BRANCH}" != "main" || "${REQUIRE_SIGNING}" == "${TRUE}" ) ]]; then
    "${SCRIPT_DIR}/headless_signing_preflight.bash" --quiet || exit 1
fi
```

with a new `--require-signing` flag (default off) so a caller that knows it will commit can opt in. Phase 1's
pushes (`:244`, `:250`) and Phase 3's `push` (`:364`) move **already-signed** objects and need no preflight — the
gate belongs before the object is created, not before it is transmitted.

### 5.7 The owner's conditional-merge gate, operationalized

**Gate (owner, 2026-08-09):** *arc PRs merge headlessly only once code signing verifiably uses the correct ed25519
key.*

Operational rule, stated so a session can apply it without interpretation:

> A session may merge an arc PR headlessly only if, **within that same session and on this host**,
> `util/headless_signing_preflight.bash --json` exited `0`, and the JSON verdict is visible in the transcript.
> The verdict is not cacheable across sessions.

Two clarifications that prevent the gate from being misapplied:

1. **The merge commit is GitHub-signed, not host-signed.** The preflight does not sign the merge. What the gate
   actually asserts is that *this host is in a known-good signing state* — so the arc's own local commits are
   correctly signed and there is no chance of a stale-key commit entering the arc under a headless flow. That is
   the risk the gate exists to close, and the preflight is a faithful, machine-checkable proxy for it.
2. **The gate is additive, never substitutive.** D-3 stands: the owner's explicit per-PR approval is still
   required. Green preflight + owner approval ⇒ eligible; green preflight alone ⇒ not eligible.

Recording: paste the `--json` verdict into the merge-approval comment (or the session log) so the gate is
auditable after the fact.

### 5.8 Stale-reference repoint step (contingent on the audit)

The audit owns the inventory. Its already-published anchors are `A1-F1`
(`util/test_gpg_signing.bash:4,6,7` — the only in-repo signing check, pinned to the superseded ed448 key) and
`A1-F2` (`notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md` — stale, names the
wrong current key), with `G13`/`G14` as the attachment points.

This plan's repoint step is therefore a **placeholder bound to the audit's final list**, not a second hunt:

1. Read the audit's §3.1 result set immediately before executing.
2. For each listed location, repoint to `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A` (subkey) — never to the offline
   primary, never to a 16-hex short id (the ambiguity class, audit `A1-F6`).
3. `util/test_gpg_signing.bash` is **deleted**, not repointed; the preflight supersedes it (§5.1).
4. The migration-status note gets a dated "superseded — current key is the ed25519 subkey" header plus a pointer
   to this plan's §4.1/§4.2 evidence table. Also correct
   `notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md:64`, which likewise
   describes the ed448 key as "the current git `user.signingkey`" [repo] — that sentence is now false.
5. Add a **Headless Signing Preflight** subsection to `docs/REFERENCE.md`, adjacent to the existing
   *YubiKey GPG Provisioning* section (`docs/REFERENCE.md:1631-1668` [repo]) and cross-linked from its *Related*
   list at `:1665-1668`.
6. Add one `AGENTS.md` Utilities bullet for the new script, in the `### Utilities` block (`AGENTS.md:337` [repo]).

If the audit's final list contains a location this plan did not anticipate, it is covered by step 1 — that is the
point of binding to the audit rather than enumerating here.

### 5.9 Hermetic tests — `tests/test_headless_signing_preflight.py`

Modelled on `tests/test_kill_helpers.py` (PATH-stub bin dir + `RedactedEnv` + `write_executable`, `:29-95` [repo])
and `tests/test_check_conda_env_torch.py` (argv-switching stub binary + `SCRIPT_TIMEOUT_SECONDS`, `:25-95` [repo]).
No real `gpg`, no real card, no network, no live PIDs.

Fixture: a tempdir `bin/` prepended to `PATH` containing
- a stub `gpg2` that switches on argv — `--card-status --with-colons` prints a chosen `serial:`/`fpr:` block; `--detach-sign` prints a chosen `[GNUPG:] SIG_CREATED …` line and exits with a chosen code; a `hang` mode `sleep 60`;
- a stub `git` answering `config --global --get <key>` from fixture values;
- a stub `gh` that appends every invocation to a log file and can be told to succeed/fail, and to report an existing issue or none.

| # | Arm | Expect |
|---|---|---|
| 1 | all four green | exit `0`; `--json` shape matches §5.4; **no** `gh` invocation without `--file-issue` |
| 2 | `user.signingkey` is a different fingerprint | exit `1`; banner names `git-config`; JSON `checks[0].status == "FAIL"` |
| 3 | `user.signingkey` is the 16-hex short id `BA18D1A733B1831A` | WARN, not silent pass (ambiguity class) |
| 4 | `--card-status` exits non-zero (no card) | exit `1`; check `toolchain-card` FAIL |
| 5 | card present, signature-slot fpr ≠ expected | exit `1`; check `card-signature-slot` FAIL |
| 6 | **card serial `24955114` while the expected-stub serial is `24955323`, fpr matches** | **exit `0`** — pins the accept-any-serial contract (§4.2) |
| 7 | sign stub exits `0` but prints no `SIG_CREATED` | exit `1` — never trust the exit code alone |
| 8 | sign stub prints `SIG_CREATED` naming a *different* fingerprint | exit `1` |
| 9 | `gpg2` hangs; `--timeout 2` | exit `1` within ~2 s + slack; proves no pinentry hang |
| 10 | `--file-issue`, no existing issue | exactly one `issue create` with the stable title; `label create` tolerated-failing |
| 11 | `--file-issue`, existing owner-authored open issue with the exact title | `issue comment`, **no** second `issue create` |
| 12 | `--file-issue`, `gh` fails entirely | still exit `1`; stderr contains the "could not be filed" line (never masks) |
| 13 | `--timeout abc` | exit `2` |
| 14 | contract: `bash -n` clean; exactly one 40-hex fingerprint literal in the file; the literal equals the documented constant | guards against a second/stale key creeping in |

Wire into **both** batteries, matching the house pattern:
`.github/workflows/ci.yml` tests job (beside `python3 -m unittest -v tests/test_check_conda_env_torch.py` at
`:631` [repo]) and `.github/workflows/main-verify.yml` battery (beside `:367` [repo]).

### 5.10 Keyring hygiene — options, all owner calls, none recommended as blocking

| Item | Evidence | Option | Recommendation |
|---|---|---|---|
| Legacy rsa4096 `B5AFCD0686585249` stub (old card `0006 09258397`) | §4.1 | Keep (harmless — a card-bound stub with no card present cannot sign) or `gpg --delete-secret-keys` + `--delete-keys`. | **Keep.** It is inert, and it is the only local means of *verifying* pre-2026-07-14 commits signed with it. Removing it would make historical signatures unverifiable on this host for no security gain. Revisit only if the ambiguity class (audit `A1-F6`) causes a concrete misresolution. |
| ed448 `93E8591643C507FF` with **on-disk** signing-capable secret | §4.1; audit `A1-F7` | Keep / move the secret offline / delete. | **Owner call.** It is the only signing-capable private key on this disk (the ed25519 signing key is card-resident), so it is the one whose theft would allow forged Juniper-attributable signatures. Moving the secret to offline media preserves the key while removing the standing exposure. Not urgent, not this arc — but it should not be forgotten, and §11 tracks it. |
| GPG-key registration on GitHub | audit `A1-F12`, `§8` item 1 | Confirm whether the legacy RSA key is still registered. | Blocked on token scope: `gh api /user/gpg_keys` needs `admin:gpg_key`. If the owner wants it resolved: `gh auth refresh -h github.com -s admin:gpg_key` then re-query. Low priority — it only affects whether a *future* stale-key signature would fail loudly. |
| `~/.gnupg` backup archive + `*-DELETE_ME` dirs at 664/775 | audit `A1-F8`, `L1` | Move offline / tighten modes. | **Owner call**, out of this arc's scope. Flagged because key-backup material inside a live keyring directory at group-readable modes is the higher-consequence of the hygiene items. |

---

# PART C — Serena re-enablement and guardrails

## 6. Part-C ground truth (verified this session)

Three independent defects, each sufficient on its own to produce "Serena connects but has no project":

1. **The live MCP entry binds no project.** `/home/pcalnon/Development/python/Juniper/juniper-ml/.mcp.json:14-26`
   defines `serena` as
   `uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context claude-code` — with **no
   `--project`**. **[live 2026-08-09]** `claude mcp list` confirms it end-to-end: `serena: uvx --from
   git+https://github.com/oraios/serena serena start-mcp-server --context claude-code - ✔ Connected`. Connected,
   project-less. [audit `A2-F1`, `G7`]
2. **juniper-ml is absent from Serena's registry.** `~/.serena/serena_config.yml:74-79` lists five projects: the
   Juniper parent dir, canopy, cascor, cascor-client, cascor-worker. **juniper-ml and juniper-data are missing
   despite both having a valid `.serena/project.yml`.** [audit `A2-F2`, `G8`]
3. **The stale `~/.claude.json` entries are a red herring, not the cause.** The three serena entries there point
   at pre-polyrepo paths that no longer exist (§A6.2), so they never load. Fixing only those would not have helped.

Supporting inventory **[live 2026-08-09]**:

| Repo | `.serena/project.yml` | `project_name` | In registry |
|---|---|---|---|
| juniper-ml | yes | `juniper_ml` | **no** |
| juniper-cascor | yes | `juniper_cascor` | yes |
| juniper-canopy | yes | `juniper-canopy` | yes |
| juniper-data | yes | `juniper_data` | **no** |
| juniper-cascor-client | yes | `juniper-cascor-client` | yes |
| juniper-cascor-worker | yes | `juniper-cascor-worker` | yes |
| juniper-data-client | **no** | — | no |
| juniper-deploy | **no** | — | no |
| juniper-recurrence | **no** | — | no |

Note the naming eras collide (`juniper_ml` vs `juniper-canopy`) [audit `A2-F10`] — which is why §6.2 recommends
activating by **absolute path**, never by name.

Two more facts that shape the design:

- `.mcp.json` is **gitignored** (`.gitignore:170` [repo]) and contains a plaintext credential [audit `A2-F12`,
  `L5`]. It is local machine state: **no PR can carry it**, and it must not be tracked as-is.
- Consequently **no worktree under `.claude/worktrees/` inherits it** [audit `A2-F4`, `G9`]. Worktree sessions —
  which is where the work actually happens — get project-scope MCP only if a user-scope entry exists.
- `.claude/skills/template-agent/SKILL.md:47` [repo] instructs "**Skip silently** if Serena is unavailable", two
  lines below `:39`'s much stricter "**stop and report**" for a discovery failure. The lenient doctrine is the
  instruction-level source of the silence [audit `A2-F3`, `G6`].
- `util/prompt_discovery/symbol_overlay.py:50` [repo] sets `slice_["overlay"] = "serena"` **unconditionally**, so a
  bundle whose every symbol came from grep is indistinguishable from a Serena-enriched one — and
  `tests/test_symbol_overlay.py:90-93` [repo] *pins* that behaviour [audit `A2-F5`, `G3`, `G4`].
- `util/agent_suite_doctor.py:219-224` [repo] registers seven checks; **none** touches MCP or Serena [audit
  `A2-F6`, `G1`].

## 6.1 C1 — Re-wire the client config for the active repos

### Options

| Option | Description | Trade-off |
|---|---|---|
| **O1** | Add `--project <canonical abs path>` to the existing `serena` entry in each repo's project-scope `.mcp.json`. | Fixes root cause 1 at the source, per repo, with the correct path baked in. Does **not** reach worktrees (gitignored file). |
| O2 | Single **user-scope** entry (`~/.claude.json` top-level `mcpServers`) with no `--project`; rely on per-session `activate_project`. | Reaches every CWD including worktrees; but reintroduces "No active project" as the default state, i.e. it fixes reach and not binding. |
| **O3** | **Both**: O1 for canonical repo roots, plus a user-scope entry (no `--project`) as the fallback that reaches worktrees. | Layered: bound-by-default in the repo, available-and-activatable everywhere else. Two places to maintain. |

### RECOMMENDATION

**O3.** O1 alone leaves the worktree sessions — the ones doing the work — with no Serena at all. O2 alone leaves
every session project-less. Together they give: bound automatically at a canonical root, available for on-demand
activation in a worktree (which is what §6.2 argues a worktree session should do anyway).

Scope precedence note: Claude Code resolves MCP scopes local → project → user, so a project-scope `.mcp.json`
entry should win over the user-scope one inside the repo. **Confirm with `claude mcp list` after the edit** (the
output names the resolved server) rather than assuming; if the precedence is the other way round, drop the
user-scope entry and instead teach worktree sessions to activate explicitly (which §6.2 already requires).

### Execution — O1, per repo with a `.serena/project.yml`

Canonical paths only. **Never** a `.claude/worktrees/*` path in a config file: that would silently ground every
session against a stale tree, which is the exact hallucination class the discovery suite exists to prevent.

```bash
claude mcp add serena -s project -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context claude-code --project /home/pcalnon/Development/python/Juniper/juniper-ml
```

Run once per repo from that repo's root, substituting the path:
`juniper-ml`, `juniper-cascor`, `juniper-canopy`, `juniper-data`, `juniper-cascor-client`, `juniper-cascor-worker`.
(`claude mcp add [options] <name> <commandOrUrl> [args...]` with `-s, --scope <local|user|project>`, verified
**[live 2026-08-09]** from `claude mcp add --help`.) `claude mcp add` rewrites the existing entry in the repo's
`.mcp.json`; back the file up first, because it also holds a credential:

```bash
python3 -c "import shutil,datetime,sys;p=sys.argv[1];shutil.copy2(p,p+'.bak-'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S'));print('backed up',p)" /home/pcalnon/Development/python/Juniper/juniper-ml/.mcp.json
```

Equivalent hand-edit — the only change is appending two array elements to the existing `args` at
`.mcp.json:17-24`:

```json
"serena": {
  "type": "stdio",
  "command": "uvx",
  "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server",
           "--context", "claude-code",
           "--project", "/home/pcalnon/Development/python/Juniper/juniper-ml"],
  "env": {}
}
```

### Execution — O3's user-scope fallback (once, not per repo)

```bash
claude mcp add serena -s user -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context claude-code
```

No `--project` here **on purpose**: a user-scope binding to one repo would be wrong in every other CWD. Worktree
sessions activate explicitly (§6.2).

### Verification / rollback

`claude mcp list` shows `serena … ✔ Connected` with `--project` present at a canonical root, and without it
elsewhere. Rollback: `claude mcp remove serena -s project` (or restore the `.bak-*`), and the same at user scope.
Purely local; nothing to revert in git.

## 6.2 C2 — Registry and activation

### Registry

Register the canonical paths of the repos that have a `.serena/project.yml` and are missing from
`~/.serena/serena_config.yml:74-79` — **juniper-ml** and **juniper-data**. Two ways:

- **Hand-edit (recommended):** back up, then append two `- <abs path>` lines to the `projects:` block. Deterministic, reviewable, no MCP side effects mid-session.
- **Activate once per repo:** an `activate_project` call registers the path as a side effect. Fewer keystrokes, but it mutates machine state from inside a session, which conflicts with keeping config changes explicit and auditable.

Backup first:

```bash
python3 -c "import shutil,datetime,os;p=os.path.expanduser('~/.serena/serena_config.yml');shutil.copy2(p,p+'.bak-'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S'));print('backed up',p)"
```

Do **not** attempt to reconcile the `juniper_ml` / `juniper-canopy` naming eras now — see below.

For `juniper-data-client`, `juniper-deploy`, `juniper-recurrence` (no `.serena/project.yml`): creating one is a
small, tracked, per-repo PR — **defer**, low value until someone actually needs symbol tooling there. Recorded in
§11.

### Activation doctrine — always by absolute path

**Never activate by project name.** The registry mixes naming conventions [audit `A2-F10`], so a name-based
activation is a guess that can silently bind the wrong project. An absolute path is unambiguous and self-checking.

### Worktree sessions — the decision, and why

**Decision: a session running under `.claude/worktrees/*` (or `Juniper/worktrees/*`) that needs symbol-level
facts calls `activate_project <its own worktree absolute path>` on demand; otherwise it uses grep and says so.**

Justification:

- **Correctness dominates.** Symbol facts must describe the tree being edited. Activating the canonical repo from
  a worktree session returns `file:line` anchors from a *different* checkout — anchors that look authoritative and
  are wrong. That is precisely the anti-hallucination failure the grounding bundle exists to prevent, and it would
  be *worse* than grep, because grep at least reads the current tree.
- **On demand, not at startup.** First activation of a path builds an LSP index; paying that for a session that
  never needs symbol lookup is waste. Activate only when a symbol operation is actually about to happen.
- **The fallback is now honest.** With C4's loud provenance, a session that stays on grep produces a bundle that
  *says* it is grep-derived, so the cheap path is safe to take.

Accepted cost: the registry accumulates one entry per activated worktree, most of which are deleted within days.
This is why C4's doctor check WARNs on registry paths that no longer exist (§6.4) — it converts the bloat into a
visible, actionable hygiene signal instead of silent rot, and it also catches the pre-existing dead entries.

## 6.3 C3 — Steering (one line in `AGENTS.md`)

Insert into the `## Conventions` bullet list (`AGENTS.md:714-723` [repo]), after the line-length bullet:

```markdown
- Symbol-level operations (locate a definition, enumerate a file's symbols, check rename safety) SHOULD prefer the Serena MCP tools when the session has them and a project is active — activate by **absolute path** (`activate_project <repo-or-worktree path>`), never by name; grep is the fallback and must be **reported as the fallback**, never presented as a Serena-grade fact. Operator detail: [`docs/REFERENCE.md` § Serena MCP Wiring](docs/REFERENCE.md#serena-mcp-wiring).
```

One bullet, one rule, one pointer. The operator detail (paths, `claude mcp add` invocations, the worktree doctrine,
the doctor check's status matrix) lives in the new `docs/REFERENCE.md` § **Serena MCP Wiring**, placed adjacent to
§ *Agent Suite Doctor* (`docs/REFERENCE.md:524-571` [repo]) and cross-linked from it.

Also change `.claude/skills/template-agent/SKILL.md:47` from "Skip silently if Serena is unavailable" to a
*record-the-skip* doctrine, e.g. "If Serena is unavailable, proceed on the grep bundle **and say so in the emitted
prompt's grounding section** — never present grep facts as Serena-resolved." The stricter sibling doctrine two
lines up (`SKILL.md:39`, "stop and report") is the in-file precedent [audit `G6`]. Note that `SKILL.md` is covered
by `tests/test_template_agent_skill_lint.py` [repo], so verify that lint still passes after the edit.

## 6.4 C4 — Guardrails

### (a) `check_serena_wiring` in `util/agent_suite_doctor.py`

Append one member to the check registry at `util/agent_suite_doctor.py:219-224` [repo]:

```python
def run_checks(root: Path, no_discovery: bool = False):
    checks = [check_agents, check_skill, check_templates, check_rubric, check_data_layer]
    if not no_discovery:
        checks.append(check_discovery)
    checks.extend([check_mirror, check_serena_wiring])
    return [fn(root) for fn in checks]
```

**Read-only. It must never spawn a Serena server** (unlike `check_discovery`, which deliberately does run a
subprocess at `:171-177`). It only reads files:

- `root/.serena/project.yml`
- `~/.serena/serena_config.yml` (override `JUNIPER_SERENA_CONFIG` for tests)
- `root/.mcp.json`, then `~/.claude.json` (`projects[<root>].mcpServers`, then top-level `mcpServers`) (override `JUNIPER_CLAUDE_JSON`)

Env overrides mirror `check_mirror`'s existing `JUNIPER_CLAUDE_HOME` idiom (`agent_suite_doctor.py:196` [repo]).

Status matrix:

| Condition | Status | Reason contains |
|---|---|---|
| `.serena/project.yml` absent | `OK` | `no serena project config (repo does not use serena)` — a repo that opts out must not be penalised; the doctor has no `SKIP`, and `check_discovery`'s precedent is omission, not a synthetic row |
| `project.yml` present but unparseable / no `project_name` | **`FAIL`** | `project.yml` + the parse error |
| serena MCP entry exists and its argv `--project` names a path that **does not exist**, or a path under `.claude/worktrees/` / `worktrees/` | **`FAIL`** | `binds a stale/worktree project path` — a *wrong* binding silently grounds against another tree and is worse than none |
| `project.yml` present, repo path **absent** from the registry `projects:` | `WARN` | the exact `- <abs path>` line to add |
| `project.yml` present, **no** `serena` entry in any resolved MCP client config | `WARN` | `serena is not wired for this repo` |
| serena entry present but argv has **no `--project`** | `WARN` | `serena MCP entry does not bind a project (the "No active project" root cause)` |
| `~/.serena/serena_config.yml` absent / unreadable | `WARN` | `serena not installed on this host` |
| registry lists ≥1 `projects:` path that no longer exists | `WARN` | names up to 3 dead paths (hygiene; also catches the worktree-activation bloat of §6.2) |
| all clear | `OK` | `serena wired: project.yml + registry + --project binding` |

`--strict` promotes those WARNs to exit 1, consistent with the existing semantics
(`agent_suite_doctor.py:273-274` [repo]). No new CLI flag: the check spawns nothing, so there is no `--no-serena`
analogue to `--no-discovery`.

Add the matrix to `docs/REFERENCE.md` § Agent Suite Doctor as a sibling of the existing *Discovery check* table
(`:546-560`) and extend the Troubleshooting table at `:562-571`.

### (b) Loud provenance in `util/prompt_discovery/symbol_overlay.py`

Three changes to `merge_symbol_probe` (currently `:26-52` [repo]):

1. **Honest overlay marker.** `slice_["overlay"]` becomes `"serena"` only when ≥1 symbol ended with
   `source == "serena"`; otherwise `"grep-fallback"`. Today `:50` sets `"serena"` unconditionally.
2. **Counts.** Add `slice_["overlay_counts"] = {"serena": n, "grep": m, "unresolved": k}` so a consumer can see the
   enrichment ratio, not just a boolean.
3. **A provenance WARN.** When `n == 0`, append to `out["provenance"]["warnings"]` (creating the list, and the
   `provenance` dict if the input lacks one):
   `"symbol_overlay: 0/<N> symbols resolved via Serena — every symbol fact in this bundle is grep-derived"`.

**Deep-copy trap — this is the part a careless implementation gets wrong.** `:32` does `out = dict(bundle)`, a
*shallow* copy, so writing into `out["provenance"]` would mutate the caller's bundle and break the pinned contract
at `tests/test_symbol_overlay.py:84-88` ("merge must not mutate the input bundle"). The provenance slice must be
copied before it is written, exactly as `:33-34` already do for `symbol_probe` and its `symbols` map.

**Companion test edit (expected, not a surprise red):** `tests/test_symbol_overlay.py:90-93`
(`test_empty_serena_preserves_grep`) currently asserts `overlay == "serena"` for an empty-serena merge. Under this
change the correct assertion is `"grep-fallback"` [audit `G4`]. Change it in the same PR, and say so in the PR body
so the diff does not read as a weakened test.

`cli.py`'s own contract is untouched: `build_bundle` (`util/prompt_discovery/cli.py:38-75` [repo]) keeps its
`schema_version` / `provenance{captured_at, head_sha, dirty, ttl_seconds, per_probe_status}` shape. A future,
larger option — surfacing `serena: ok|unavailable` inside `per_probe_status` (`cli.py:49-57`) [audit `G5`] — is
deliberately **out of scope** here: `cli.py` cannot reach MCP, so only the overlay knows, and adding a key the CLI
can never populate honestly would be its own small lie.

Also out of scope, recorded as follow-up: teaching `prompt-validator`'s R3.4b (`.claude/agents/prompt-validator.md:96`
[audit `G11`]) to *reject* a grep-only bundle when the task demanded symbol-level precision. That is a validator
behaviour change and deserves its own design.

### (c) Hermetic tests

**`tests/test_agent_suite_doctor.py`** — a new `DoctorSerenaWiringTest` modelled on the existing
`DoctorDiscoveryCheckTest` (`:109-176` [repo]): synthetic `--repo-root` trees plus env-pointed fake
`serena_config.yml` / `.mcp.json` / `.claude.json`, one arm per status-matrix row. Plus the **no-spawn** arm: put a
stub `uvx` on `PATH` that writes a marker file, run the doctor, assert the marker does not exist.

**`tests/test_symbol_overlay.py`** — new arms: all-grep ⇒ `overlay == "grep-fallback"` **and** exactly one
provenance warning; ≥1 Serena ⇒ `overlay == "serena"`, correct `overlay_counts`, no warning; input bundle
unmutated **including the nested `provenance` dict** (compare a `json.dumps(..., sort_keys=True)` snapshot, as
`:84-88` already does); an input with **no** `provenance` key gets one created carrying the warning.

Both files are already wired into `ci.yml` (`:321`, `:337`) and `main-verify.yml` (`:318`, `:322`) [repo], so no
workflow edit is needed for these — only the new Part-B test file needs wiring (§5.9).

## 6.5 C5 — Post-fix live validation

Run in order; each step's failure localizes the problem.

1. **Restart the Claude Code session** — MCP config is read at startup.
2. `claude mcp list` → `serena … ✔ Connected`, and the printed argv now contains `--project <canonical path>` when
   run from a canonical repo root.
3. **In-session**: confirm Serena reports an active project (no "No active project"). If it does not, the scope
   precedence assumption in §6.1 was wrong — fall back to an explicit
   `activate_project /home/pcalnon/Development/python/Juniper/juniper-ml` and record the correction.
4. **A real symbol lookup**, on a symbol chosen because it is unambiguous and verified to exist:
   `find_symbol` for **`run_fix`** — expected `util/editable_install_drift_check.py:252`
   (`def run_fix(plan, conda_dir: Path, dry_run: bool):`, **[live 2026-08-09]**). A second, harder probe if wanted:
   `discover_canonical`, same file, `:220`.
5. **Doctor**: `python util/agent_suite_doctor.py --repo-root /home/pcalnon/Development/python/Juniper/juniper-ml --json`
   → `serena_wiring` is `OK` and no other check regressed.
6. **Round-trip the overlay**:
   `python util/prompt_discovery/cli.py --repo-root <canonical> --symbols run_fix` to produce a bundle, supply a
   Serena result for `run_fix`, merge with `util/prompt_discovery/symbol_overlay.py`, and confirm
   `symbol_probe.overlay == "serena"` with **no** provenance warning. Then repeat with an empty Serena map and
   confirm `"grep-fallback"` **with** the warning — i.e. prove the honesty works in both directions.
7. **A transcript-visible Serena call in the next real session.** The acceptance criterion for the whole of Part C
   is not a config diff; it is that the next working session actually uses Serena and the transcript shows it.
   Record the session and the tool call in §11.

Rollback for all of C: restore the `.bak-*` copies of `.mcp.json`, `~/.serena/serena_config.yml`, and
`~/.claude.json`; revert the doctor / overlay PR. All local state; no service, no CI, no remote.

---

# PART D — Execution sequencing

## 7. Slicing, gating, verification, rollback

### 7.1 Dependency order

```text
A1 identify (owner UI)  ──┐
                          ├─▶ A2 remove cursor/claude bypass ──▶ A4 merge queue (if available)
A3 drop code_quality  ────┘                                              │
                                                                         ▼
A5 promote sequence-safety (ml first, then per-repo)  ◀── independent, but do not land the same day as A4
A6 housekeeping — independent, anytime
B  preflight  — independent of A; UNLOCKS the D-4 conditional merge gate for every other slice
C  serena     — independent of A and B
```

Two hard constraints and one soft one:

- **A3 before A2** (§A2.3): removing bypasses while an unsatisfiable rule stands converts a dormant deadlock into
  an active one.
- **A2 before/with A4** (§A4.3): a queue binds nothing while the fleet Apps bypass everything.
- **Soft:** do not land A4 and A5 on the same day. Both change what "required" means; separating them keeps
  attribution clean if a PR stalls.

**B first in wall-clock terms**, because it is the slice that satisfies D-4 and therefore unlocks headless merging
of the rest.

### 7.2 PR slices, with the dup-guard result

Dup-guard **[live 2026-08-09]**: `gh pr list --repo pcalnon/juniper-ml --state open` → 4 PRs (`#1048`
docs/handoff, `#1043` / `#1041` / `#1039` release-notes archives). **No overlap** with any slice below. Re-run the
dup-guard immediately before opening each PR (D-5). Owner-decision issues **ml#1011** and **ml#1012** already exist
and must be *referenced*, never duplicated.

| Slice | Contents | Artifacts | Kind | Est. effort |
|---|---|---|---|---|
| **S0 — docs** | This plan + the audit already in the tree | `notes/JUNIPER_2026-08-09_…_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md`, `notes/JUNIPER_2026-08-09_…_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md` | PR | ~0 (written) |
| **S1 — signing preflight** | `util/headless_signing_preflight.bash`; **delete** `util/test_gpg_signing.bash`; `tests/test_headless_signing_preflight.py`; wire into `ci.yml` + `main-verify.yml`; `worktree_cleanup.bash` guard + `--require-signing`; `docs/REFERENCE.md` § Headless Signing Preflight; `AGENTS.md` Utilities bullet | PR | **~1 focused day** (script ~250 lines shellcheck-clean; 14 hermetic arms is the bulk) |
| **S2 — signing repoint** | Per the audit's final §3.1 list: repoint/annotate `notes/JUNIPER_2026-07-16_…_CODE-SIGNING-KEY-MIGRATION-STATUS.md`, fix `notes/JUNIPER_2026-08-03_…_KEYTOCARD-PROCEDURE.md:64`, plus anything else the audit names | PR | ~1-2 h |
| **S3 — serena guardrails** | `check_serena_wiring` in `util/agent_suite_doctor.py`; honest provenance in `util/prompt_discovery/symbol_overlay.py`; test extensions in both existing test files; `SKILL.md:47` doctrine; `AGENTS.md` Conventions bullet; `docs/REFERENCE.md` § Serena MCP Wiring | PR | **~half a day** |
| **S4 — serena machine state** | `.mcp.json` `--project` per repo; user-scope entry; `~/.serena/serena_config.yml` registration; `~/.claude.json` prune | **NO PR — documented operator step** (§6.1/§6.2/§A6.2). All files are gitignored or outside the repo. | ~30 min + a session restart |
| **S5 — ruleset A3+A2 (+A4)** | `util/ad-hoc/2026-08-09_ruleset_edit.py`; then owner-run edits | Helper lands as a PR; **the edits are owner-gated API/UI actions, not a PR** | helper ~2 h; edits ~30 min incl. verification |
| **S6 — A5 promotion** | 8 ruleset context additions + 1 classic-protection addition | **No PR** — owner-gated config, on ~2026-08-21 after the §A5.2 checklist | ~45 min for all 9 |
| **S7 — A6 housekeeping** | 3 ff-pulls; `~/.claude.json` prune | **No PR** — local operator steps | ~10 min |

Note the shape: **only S0, S1, S2, S3 and the S5 helper are PRs.** Everything else is owner-gated config or local
machine state, which is exactly why this document exists — those changes have no diff to review, so the review
happens here.

### 7.3 Applying the D-4 conditional-merge gate

| Slice | May merge headlessly? |
|---|---|
| **S0** | **Yes**, once S1's preflight is green on this host *or* the owner merges it manually. S0 is docs-only and is the natural first candidate for the A4 behavioural test (§A4.5). |
| **S1** | Chicken-and-egg by construction. Resolve it explicitly: run the preflight **from the branch, before merge** (`bash util/headless_signing_preflight.bash --json` in the PR checkout). Green ⇒ the gate is satisfied by the very artifact being merged, and S1 may merge headlessly on the owner's approval. Red ⇒ **owner merges manually** after fixing the host; do not merge a preflight that cannot pass on the host it is written for. |
| **S2, S3** | **Yes**, once S1 is merged and the preflight is green in the session doing the merging. |
| **S5 helper** | **Yes**, same condition as S2/S3. |
| **S4, S6, S7** | Not applicable — no PR. Each is an owner action or an owner-approved session action against local/config state. |

In all cases D-3 stands: green preflight makes a PR *eligible*; the owner's explicit approval makes it *merge*.

### 7.4 Slice-specific hazards

- **S1 deletes `util/test_gpg_signing.bash`.** That file is inside the ml symbol-loss scope
  (`--scope 'util/**/*.bash'`, `ci.yml:805` [repo]), so the deletion is a genuine `LOST` finding. Waive it with the
  `Allow-Symbol-Loss` commit **trailer** (not the label — the trailer travels in history and therefore also covers
  the post-merge `main-verify` G3 screen, `docs/REFERENCE.md:1590` [repo]), and **carry the trailer into the squash
  commit message**, which is the documented way this waiver is lost.
- **S3 changes an assertion in `tests/test_symbol_overlay.py`.** Expected and explained in §6.4(b); call it out in
  the PR body so it does not read as a weakened test.
- **S3 edits `.claude/skills/template-agent/SKILL.md`,** which is linted by
  `tests/test_template_agent_skill_lint.py` [repo]. Run that test locally before pushing.
- **S1 and S3 add/modify `docs/**` and `AGENTS.md`,** in the docs deletion-magnitude screen's universal scope. All
  changes are additive, so no waiver should be needed; if the screen fires, inspect rather than reflexively waive.
- **S5's helper is `util/ad-hoc/`**, which is not flake8-scoped (`.pre-commit-config.yaml:136`: `^(scripts|tests)/.*\.py$`
  [repo]). It has no unit test by design (single-use), so its safety comes from `--execute` being opt-in, the
  snapshot-before-mutate rule, and the dry-run default.

### 7.5 Verification matrix

| Slice | Structural | Behavioural | Live |
|---|---|---|---|
| S0 | `juniper-check-doc-links` (the `docs` CI job); markdownlint | — | link check in the weekly `docs-full-check.yml` |
| S1 | `bash -n`; shellcheck (`--severity=warning`); the 14 hermetic arms; `tests/test_workflow_script_paths.py` proves the new workflow path resolves | full battery in `ci.yml` + `main-verify.yml` | **run the preflight on the host**: expect exit 0, `card_serial: 24955114`, `SIG_CREATED` naming `B5619F58…831A`; then unplug the card and confirm exit 1 + banner + (with `--file-issue`) exactly one tracking issue |
| S2 | doc-link validator; no stale fingerprint remains (grep for the ed448 and rsa key ids) | — | — |
| S3 | `tests/test_agent_suite_doctor.py`, `tests/test_symbol_overlay.py`, `tests/test_template_agent_skill_lint.py` | doctor on the real repo has zero FAIL | `python util/agent_suite_doctor.py --json` after S4 → `serena_wiring: OK` |
| S4 | — | — | §6.5 steps 1-7, ending in a transcript-visible Serena call |
| S5 | helper dry-run prints a body identical to §A2.4's expected JSON | — | §A1.6 / §A3.5 / §A4.5 probes; one small PR through the queue |
| S6 | — | — | §A5.6 probe + one PR per repo showing the check under **Required** |
| S7 | — | — | re-run the §3.8 comparison; three checkouts equal their remote tips |

### 7.6 Rollback per slice

| Slice | Rollback | Cost |
|---|---|---|
| S0 | `git revert` | trivial |
| S1 | `git revert`; the guard in `worktree_cleanup.bash` is behind a condition and defaults off for the `main`-parent path, so a revert restores exact prior behaviour | minutes |
| S2 | `git revert` | trivial |
| S3 | `git revert`; the doctor loses one check, the overlay returns to the unconditional marker | minutes |
| S4 | restore the three `.bak-*` files; restart the session | minutes |
| S5 | PATCH from the ruleset snapshot (§A2.6 / §A3.7); or the UI | seconds |
| S6 | remove the context (§A5.7); the job returns to advisory | seconds |
| S7 | none needed (fast-forwards create and discard nothing) | — |

**No slice in this plan is irreversible.** That is deliberate: every step is either a revertible commit, a
snapshot-protected config PATCH, or a backed-up local file.

---

## 8. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Merge queue turns out to be unavailable (the reported `422`) | Medium | Low | A4 stops at Step 1 with a recorded observation; `strict=true` remains the fallback and is already on. Nothing else in the plan depends on A4. |
| R2 | Removing the Cursor/Claude bypass blocks something unforeseen | Low | Low | Neither App self-merges [research line 522]; the owner retains `RepositoryRole 5`/always. Rollback is seconds (§A2.6). Land A3 first so nothing is stranded behind the deadlock. |
| R3 | Dropping `code_quality` removes a control the owner wanted | Low | Low | Nothing reports it (§3.6), so no control is lost today. If GitHub Code Quality later goes GA, re-add the rule *with* a tool attached — the better end state anyway. |
| R4 | Promoting sequence-safety produces a false block during a busy window | Low | Medium | 60/60 + 15/15 clean (§3.5); label hatch and trailer escapes are live and proven; per-repo promotion means one repo's flake never blocks the fleet; rollback is one context removal. |
| R5 | `1276151` / `946600` turn out to be load-bearing and were removed | Low | Medium | Identify-first (A1) exists precisely to prevent this; no removal happens before a name exists. |
| R6 | The preflight itself becomes a false blocker (e.g. an agent-cache expiry mid-flow) | Medium | Medium | It is a *precondition* check, not a per-commit hook, and it fails in ≤20 s with a remediation banner. `--require-signing` defaults off. The post-restore re-run needs no manual steps (§5.5). |
| R7 | The preflight's expected fingerprint goes stale after a future key rotation | Low | High (silent) | Test arm 14 asserts exactly one fingerprint literal; the constant carries a comment naming its source; §11 tracks rotation as an event that must update the constant, `docs/REFERENCE.md`, and the migration note together. |
| R8 | Serena activation against a worktree path bloats the registry | High | Very low | Converted into a visible WARN by the doctor's dead-path rule (§6.4(a)); prune periodically. |
| R9 | A worktree session silently grounds against the canonical tree instead of its own | Low | High (silent) | §6.2's path-activation doctrine plus the doctor's **FAIL** on a `--project` that points into `worktrees/` — the one condition promoted to FAIL rather than WARN, precisely because it is silent and wrong. |
| R10 | The audit and this plan diverge on a fact | Low | Medium | §10.4: reconcile before either is treated as ratified. All overlapping facts were cross-checked during authoring and agree. |

---

## 9. Testing strategy (summary)

Three tiers, matching house practice:

1. **Structural / lint.** `bash -n` + shellcheck for the new script; the existing frontmatter, drift, and skill
   lints for the touched agent-suite surfaces; `tests/test_workflow_script_paths.py` for the workflow wiring.
   `util/` Python is **not** flake8-gated (`.pre-commit-config.yaml:136`), so its unit test *is* the gate — the
   standing convention this plan follows for both new/changed `util/` modules.
2. **Hermetic behavioural.** `tests/test_headless_signing_preflight.py` (14 arms, PATH-stubbed `gpg2`/`git`/`gh`,
   no real card, no network) and the two extended suites for the doctor and the overlay. Every one runs in both
   `ci.yml` and the `main-verify.yml` battery.
3. **Live smoke, once.** The card-present/card-absent preflight pair; the Serena activation + `find_symbol run_fix`
   round trip; the ruleset probes after each owner edit; one PR through the merge queue if A4 lands.

What is deliberately **not** automated: the ruleset/branch-protection edits. They are owner-gated (D-1), infrequent,
and snapshot-protected; a CI job that could mutate branch protection would be a larger risk than the drift it
guards against. The compensating control is the §A1.6 / §A3.5 / §A5.6 probes, which are cheap enough to run
whenever the posture is in doubt.

---

## 10. Cross-validation and confidence

### 10.1 What was independently re-verified for this plan

Ruleset JSON and rule list; the 8-repo bypass census; App-ID→slug resolution (a method the prior research did not
use, which resolved `1143301` and confirmed `1210556`/`1236702`); deploy keys; recurrence's classic protection and
its `required_status_checks` sub-resource; the full sequence-safety soak counts and every job/context name; the
GraphQL `MERGE_QUEUE` / `MergeQueueParameters` / enum introspection; `git config` signing state; the full secret-key
listing; live `--card-status`; **a real detached test signature**; the `%G?`/`%GK` census on `main`; `claude mcp
list`; `.mcp.json`; `~/.serena/serena_config.yml`; `~/.claude.json`; nine local-checkout freshness comparisons; the
open PR and issue sets.

### 10.2 Where this plan corrects or extends prior records

1. **A6 is already done** for juniper-recurrence; three *other* checkouts are behind (§3.8).
2. **`946600` is a previously unrecorded bypass actor** on three repos (§3.2).
3. **`1143301` = Copilot SWE Agent**, resolved by App-ID lookup (§3.2).
4. **Serena's root cause is the missing `--project` in a live, connected entry** — not the dead `~/.claude.json`
   paths, which are inert (§6).
5. **The card-serial mismatch does not block signing** on this host (§4.2) — a direct answer to the audit's §8 open
   item 3, and the reason the preflight compares fingerprints, not serials.

### 10.3 Known unknowns (stated, not guessed)

- The identities of `1276151` and `946600` — owner UI only (§3.2).
- Merge-queue availability on this account — UI only (§3.7).
- REST spellings of `merge_queue` parameters — derived from GraphQL; read back from GitHub after a UI apply (§A4.4 Step 2).
- MCP scope precedence between project and user scope — confirm with `claude mcp list` (§6.1).
- Whether the legacy RSA key is still registered on the GitHub account — needs `admin:gpg_key` (§5.10).

### 10.4 Recommended cross-validation before ratification

This plan proposes changes to branch protection on 9 repos and to the owner's signing gate. Before it is treated as
ratified, an **independent pass** should confirm, at minimum: (a) the §3.1 ruleset snapshot and the §3.2 census
against a fresh probe; (b) that the §A5.3 context strings match the live job names character-for-character
(including the em dash in recurrence's existing context); and (c) that this plan and the sibling audit do not
disagree on any fact. Items (a) and (b) are the ones where a single wrong character creates a permanently
unsatisfiable required check.

---

## 11. Owner decisions and open questions

| # | Decision / question | Recommendation | Status |
|---|---|---|---|
| Q1 | Name Integration `1276151` (all 8 repos) | Identify in the UI (§A1.4), then act per §A1.5; expect REMOVE | **OPEN — owner UI** |
| Q2 | Name Integration `946600` (data / cascor-client / deploy) | Same procedure; new finding | **OPEN — owner UI** |
| Q3 | Remove Cursor `1210556` + Claude `1236702` always-bypass | **Yes**, juniper-ml first, then the other 7 (ml#1012) | **OPEN — owner-gated** |
| Q4 | `code_quality` deadlock | **Drop the rule** (Ob); keep `4362741` at `pull_request` for now | **OPEN — owner-gated** |
| Q5 | Remove `4362741`'s bypass after Q4 | Later, as the §A3.6 single-ceremony experiment; **not** together with A4 | **DEFERRED** |
| Q6 | Merge queue | Verify availability in the UI; if available, add **with** Q3, params per §A4.4 | **OPEN — owner UI** |
| Q7 | Record the canonical `merge_queue` rule JSON | Paste the §A4.4 Step-2 read-back here and into `docs/REFERENCE.md` | **PENDING Q6** |
| Q8 | Promote sequence-safety to required | **Yes**, on ~2026-08-21 after the §A5.2 checklist; per-repo; contexts per §A5.3 (ml#1011) | **OPEN — dated** |
| Q9 | Keep the legacy RSA stub in the keyring | **Keep** (inert; needed to verify historical signatures) | Recommendation stands |
| Q10 | The ed448 key's on-disk signing-capable secret | **Owner call** — move offline or accept; it is the only signing-capable private key on this disk | **OPEN** |
| Q11 | Confirm whether the legacy RSA key is still registered on GitHub | `gh auth refresh -h github.com -s admin:gpg_key`, then `gh api /user/gpg_keys`; low priority | **OPEN — optional** |
| Q12 | Create `.serena/project.yml` for data-client / deploy / recurrence | **Defer** until symbol tooling is actually needed there | **DEFERRED** |
| Q13 | Reconcile the Serena project-name eras (`juniper_ml` vs `juniper-canopy`) | **Defer** — path-based activation makes it cosmetic | **DEFERRED** |
| Q14 | Prune the 5 dead `~/.claude.json` project keys | **Yes, after Part C lands** (§A6.2) | **OPEN** |
| Q15 | ff-pull the three behind checkouts (ml / data-client / cascor-client) | **Yes** (§A6.1); recurrence is already current | **OPEN — trivial** |
| Q16 | Record the transcript-visible Serena call that closes Part C | §6.5 step 7 | **PENDING S4** |

---

## 12. Appendix — probe index

Every command this session ran that produced a cited fact, so any claim can be re-derived. All are read-only.

```bash
# Part A
gh api repos/pcalnon/juniper-ml/rulesets/13805432
gh api repos/pcalnon/juniper-ml/rulesets/13805432 --jq '.rules[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context'
gh api repos/pcalnon/<repo>/rulesets                      # per repo, 9 repos
gh api repos/pcalnon/<repo>/rulesets/<id>                 # bypass + rule census, 8 repos
gh api /apps/<slug>                                       # ~190 slugs; App-ID resolution
gh api /apps/dependabot                                   # proves actor_id == App ID (29110)
gh api /user/installations                                # 403 -- identification limit
gh api /app/installations/1276151                         # 401 -- needs an App JWT
gh api repos/pcalnon/juniper-ml/keys ; gh api repos/pcalnon/juniper-cascor/keys
gh api repos/pcalnon/juniper-recurrence/branches/main/protection
gh api repos/pcalnon/juniper-recurrence/branches/main/protection/required_status_checks
gh api -X GET repos/pcalnon/<repo>/actions/workflows/sequence-safety.yml/runs -f per_page=100 --jq '.workflow_runs[].conclusion'
gh api -X GET repos/pcalnon/juniper-ml/actions/workflows/ci.yml/runs -f event=pull_request -f per_page=15 --jq '.workflow_runs[].id'
gh api repos/pcalnon/juniper-ml/actions/runs/<id>/jobs --jq '.jobs[]|select(.name=="Sequence Safety")|.conclusion'
gh api repos/pcalnon/juniper-ml/commits/b64eaaf/check-suites --jq '.check_suites[]|[.app.id,.app.slug,.app.name]|@tsv'
gh api graphql   # __type(MergeQueueParameters) ; __type(RepositoryRuleType) ; the two MergeQueue enums
gh api repos/pcalnon/<repo>/commits/main --jq .sha        # checkout freshness, 9 repos
gh api repos/pcalnon/<repo>/compare/<local>...<remote>    # ahead/behind, 3 repos
gh pr list --repo pcalnon/juniper-ml --state open ; gh issue list --repo pcalnon/juniper-ml --state open

# Part B
git config --global --get user.signingkey ; ... gpg.program ; commit.gpgsign ; tag.gpgsign
gpg2 --list-secret-keys --keyid-format LONG --with-colons
timeout 20 gpg2 --card-status --with-colons
timeout 25 gpg2 --status-fd 1 --local-user 'B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!' --detach-sign --output /dev/null <file>
git log -6 --format='%h %G? %GK %s' ; git log -1 --format='%H %G? %GK %GS' 731302a

# Part C
claude mcp list ; claude mcp add --help
# reads: <repo>/.mcp.json ; ~/.serena/serena_config.yml ; ~/.claude.json ; <repo>/.serena/project.yml (9 repos)
```

---

## 13. Related documents

- [`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md`](JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md) — the findings half of this pair; owns the stale-key hunt (§3.1), the Serena root-cause ranking (§4.1) and the attachment-point inventory (§6).
- [`notes/JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md`](JUNIPER_2026-08-05_JUNIPER-ML_BYPASS-ACTOR-RESEARCH.md) — per-actor analysis of ruleset 13805432; the `code_quality` deadlock diagnosis.
- [`notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md) — the all-advisory rollout; decision **D8** is what A5 closes.
- [`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md) — §4 item 1 is the merge-queue proposal A4 executes.
- [`notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md`](JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md) — **stale**; S2 corrects it.
- [`notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md`](JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md) — the hardware constraint; its line 64 needs the same correction.
- `docs/REFERENCE.md` § *Flood-Remediation CI Gates* (`:1529`), § *YubiKey GPG Provisioning* (`:1631`), § *Agent Suite Doctor* (`:524`) — the three operator surfaces this plan extends.
- GitHub issues **ml#1011** (promote sequence-safety) and **ml#1012** (bypass removal) — the pre-existing owner-decision trackers for A5 and A2; reference, never duplicate.
