# Required-Status-Check Context Lists — Per-Repo Correction + Roadmap

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (9 publishing repos)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-08-10

**Operator surface (2026-09-04):** [`docs/REFERENCE.md` § Ruleset Context Audit](../docs/REFERENCE.md#ruleset-context-audit). This note is the 2026-08-10 incident record; §1 counts are historical. Re-run `util/ad-hoc/2026-08-10_ruleset_context_audit.py` rather than quoting them.

---

## 1. Why this document exists

The 2026-08-10 ruleset normalization applied one **fleet-union list of 30
`required_status_checks` contexts** to all 9 repos. Seven of the eight rules normalize
correctly and should stay uniform. `required_status_checks` **cannot** — it names each
repo's *actual* CI job names, which differ per repo by design.

A required context that never reports is never satisfied. The result:

| Repo                  | Required | Matched | **Blocking** |
|-----------------------|----------|---------|--------------|
| juniper-ml            | 30       | 7       | **23**       |
| juniper-cascor        | 30       | 12      | **18**       |
| juniper-canopy        | 30       | 10      | **20**       |
| juniper-data          | 30       | 10      | **20**       |
| juniper-cascor-worker | 30       | 10      | **20**       |
| juniper-deploy        | 30       | 4       | **26**       |
| juniper-data-client   | 30       | 8       | **22**       |
| juniper-cascor-client | 30       | 8       | **22**       |
| juniper-recurrence    | 30       | 1       | **29**       |
| **TOTAL**             |          |         | **200**      |

**Every repo's `main` is currently unmergeable except by admin bypass** — the exact
opposite of the headless-merge goal.

**Evidence (not inference):** juniper-ml#1062 was rebased onto current `main` and
force-pushed. It reports `mergeable: MERGEABLE` with `mergeStateStatus: BLOCKED`,
waiting permanently on contexts that will never report.

Regenerate all data in this document with:

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py          # human report
python util/ad-hoc/2026-08-10_ruleset_context_audit.py --json   # machine-readable
```

---

## 2. Methodology — why these lists are safe

Tier 1 is **not** simply "every check that reports". Two filters matter:

1. **Path-gating.** A context that reports on only *some* PRs is path-gated. Requiring it
   permanently blocks every PR that does not touch its paths — recreating the current bug
   in a subtler form. Tier 1 admits only contexts observed on **every** sampled PR.
   Per-PR-type variation is real and preserved: juniper-ml dependabot/docs PRs carry ~22
   checks while full code PRs carry ~37, and **docs and dependabot PRs must stay
   mergeable too**.
2. **Anomalous rollups are excluded.** A PR merged before CI settled (juniper-ml#1061
   merged carrying 5 of ~37 checks) would make every context look path-gated and collapse
   Tier 1 to nothing. Rollups below half the median check count are dropped.

Also excluded from Tier 1 on principle:

- **Third-party fleet automation** — `Cursor Automation: *`, `claude`. Not ours; may not run.
- **Deliberately advisory gates** — `Sequence Safety (Advisory)`, `Fleet PR Lint`. Promotion
  is tracked by juniper-ml#1011 (soak hold ~2026-08-21), and belongs in the ruleset, never
  in the Quality Gate `needs:`.
- **Notification / mutation side-jobs** — `Build Notification`, `Notify Downstream Repos`,
  `Bump AGENTS.md Last Updated`, `Update requirements.lock`. They report but assert nothing.
- **`CodeQL`** — the umbrella entry; the real gate is `Analyze (python)`.

---

## 3. Tier 1 — apply now (makes merging work again)

Exact strings. Case, spacing, and parentheses are significant.

### juniper-ml (14)

```bash
Analyze (python)
Build and Validate Package
Claude.yml Access Audit
Dependency Documentation
Documentation Links
Pre-commit (Python 3.12)
Pre-commit (Python 3.13)
Pre-commit (Python 3.14)
Quality Gate
Regression Tests (Python 3.12)
Regression Tests (Python 3.13)
Regression Tests (Python 3.14)
Release-Train Archive Guard
Security Scan
```

### juniper-cascor (21)

```bash
Analyze (python)
Async-route audit (BUG-JD-10 class)
Bandit
Build Package
Dependency Documentation
Docker Build & Smoke Test
Documentation Links
Full Integration Tests
Golden / Snapshot Regression
Lockfile Freshness
Pre-commit (Python 3.12)
Pre-commit (Python 3.13)
Pre-commit (Python 3.14)
Quality Gate
Quick Integration Tests
Security Scans
Unit Tests + Coverage (Python 3.12 on macos-latest)
Unit Tests + Coverage (Python 3.12 on ubuntu-latest)
Unit Tests + Coverage (Python 3.13 on ubuntu-latest)
Unit Tests + Coverage (Python 3.14 on ubuntu-latest)
model-core Conformance
```

### juniper-canopy (18)

```bash
Analyze (python)
Async-route audit (BUG-JD-10 class)
Build Distribution
Dependency Documentation
Docker Build & Smoke Test
Documentation Links
Integration Tests
Lockfile Freshness
Pre-commit (Python 3.12)
Pre-commit (Python 3.13)
Pre-commit (Python 3.14)
Quality Gate
Security Scans
UI Sub-suite (Playwright)
Unit Tests + Coverage (Python 3.12 on macos-latest)
Unit Tests + Coverage (Python 3.12 on ubuntu-latest)
Unit Tests + Coverage (Python 3.13 on ubuntu-latest)
Unit Tests + Coverage (Python 3.14 on ubuntu-latest)
```

### juniper-data (19)

```bash
Analyze (python)
Async-route audit (BUG-JD-10 class)
Bandit
Build Package
Dependency Documentation
Docker Build & Smoke Test
Documentation Links
Integration Tests
Lockfile Freshness
Pre-commit (Python 3.12)
Pre-commit (Python 3.13)
Pre-commit (Python 3.14)
Quality Gate
Security Scans
Slow Tests
Unit Tests + Coverage (Python 3.12 on macos-latest)
Unit Tests + Coverage (Python 3.12 on ubuntu-latest)
Unit Tests + Coverage (Python 3.13 on ubuntu-latest)
Unit Tests + Coverage (Python 3.14 on ubuntu-latest)
```

### juniper-cascor-worker (19)

```bash
Analyze (python)
Async-route audit (BUG-JD-10 class)
Bandit
Build Package
Dependency Documentation
Documentation Links
Integration Tests (Python 3.12)
Integration Tests (Python 3.13)
Integration Tests (Python 3.14)
Lockfile Freshness
Pre-commit (Python 3.12)
Pre-commit (Python 3.13)
Pre-commit (Python 3.14)
Quality Gate
Security Scans
Unit Tests + Coverage (Python 3.12 on macos-latest)
Unit Tests + Coverage (Python 3.12 on ubuntu-latest)
Unit Tests + Coverage (Python 3.13 on ubuntu-latest)
Unit Tests + Coverage (Python 3.14 on ubuntu-latest)
```

### juniper-deploy (6)

```bash
Compose Validation
Gitleaks
Pre-commit
Quality Gate
SOPS Validation
Unit Tests
```

### juniper-data-client (17)

```bash
Analyze (python)
Bandit
Build Package
Dependency Documentation
Documentation Links
Integration Tests (Python 3.12)
Integration Tests (Python 3.13)
Integration Tests (Python 3.14)
Pre-commit (Python 3.12)
Pre-commit (Python 3.13)
Pre-commit (Python 3.14)
Quality Gate
Security Scans
Unit Tests + Coverage (Python 3.12 on macos-latest)
Unit Tests + Coverage (Python 3.12 on ubuntu-latest)
Unit Tests + Coverage (Python 3.13 on ubuntu-latest)
Unit Tests + Coverage (Python 3.14 on ubuntu-latest)
```

### juniper-cascor-client (17)

```bash
Analyze (python)
Bandit
Build Package
Dependency Documentation
Documentation Links
Integration Tests (Python 3.12)
Integration Tests (Python 3.13)
Integration Tests (Python 3.14)
Pre-commit (Python 3.12)
Pre-commit (Python 3.13)
Pre-commit (Python 3.14)
Quality Gate
Security Scans
Unit Tests + Coverage (Python 3.12 on macos-latest)
Unit Tests + Coverage (Python 3.12 on ubuntu-latest)
Unit Tests + Coverage (Python 3.13 on ubuntu-latest)
Unit Tests + Coverage (Python 3.14 on ubuntu-latest)
```

### juniper-recurrence (3) — ⚠️ structurally different

```bash
Documentation links
Guard PR base branch
Pre-commit (all-files)
```

**Do not simply accept 3.** recurrence's real gates are all path-gated and therefore
unsafe to require as-is:

| Context                                                      | Reports on |
|--------------------------------------------------------------|------------|
| `Required checks`                                            | 4/7 PRs    |
| `Test (Python 3.12/3.13/3.14)`                               | 4/7        |
| `Lint (ruff)`                                                | 4/7        |
| `Build distribution`                                         | 4/7        |
| `Docker Build & Smoke Test`                                  | 4/7        |
| `Bench required checks`                                      | 3/7        |
| `Bench smoke (Python 3.12/3.13/3.14)`                        | 3/7        |
| `Test — torch MLP readout (Rung 2b; optional [torch] extra)` | 1/7        |

recurrence runs two disjoint CI configurations (main CI vs bench CI) on complementary path
filters, so almost nothing runs on every PR. Note also `Documentation links` is
lower-case `l` here and `Required checks` replaces `Quality Gate` — recurrence never
adopted the fleet naming. **Fix the CI structure first** (§5), then require the real gates.

---

## 4. Defects found while deriving the lists

1. ~~**Typo — juniper-cascor ruleset**: `Integration Tests (Python 3.12 on macos-lates)`
   and three `ubuntu-lates` siblings.~~ **FIXED 2026-08-12.**
2. ~~**Typo — juniper-data ruleset**: `Regression Tests (Python 3.12 on macos-lates)`
   plus three `ubuntu-lates` siblings.~~ **FIXED 2026-08-12.**
3. ~~**Truncation — juniper-deploy ruleset**:
   `Unit Tests + Coverage (Python 3.12 on macos-latest` — missing closing paren.~~
   **FIXED 2026-08-12.**
4. **Unexpanded matrix expression — juniper-data.** *Investigated 2026-08-12:*
   **not a workflow defect — no fix needed.** The job name at
   `juniper-data/.github/workflows/ci.yml:228` is correct GitHub Actions syntax, and
   `unit-tests` declares `needs: [pre-commit]`. On juniper-data#253 the rollup carries
   **both** an un-interpolated `Unit Tests + Coverage (Python ${{ matrix.python-version }}
   on ${{ matrix.os }})` with `conclusion: CANCELLED` **and** all four properly expanded
   names with `conclusion: SUCCESS`. Two runs: an earlier one cancelled by
   `concurrency: {group: ci-${{ github.ref }}, cancel-in-progress: true}`
   (`ci.yml:48-50`) when a second push landed, plus the run that actually completed.
   **A matrix job cancelled before expansion is reported by GitHub under its literal name
   template.** Routine for any repo combining a matrix with `cancel-in-progress`.
   *Consequence:* never add the literal `${{ … }}` string as a required context — it
   appears only on cancelled runs. The auditor already classifies it path-gated `[1/8]`
   and excludes it from Tier 1, which is the correct handling.
5. ~~**juniper-cascor-worker still carries the `update` rule**~~ **FIXED 2026-08-12** —
   now the fleet-standard 8 rules.

### 4a. Post-application state (2026-08-12)

Tier 1 applied by the owner via the web UI. Re-audit result — **200 blocking contexts
reduced to 9**, all one systematic cause:

| Repo                  | Required | Blocking | Remaining issue                                     |
|-----------------------|----------|----------|-----------------------------------------------------|
| juniper-ml            | 14       | **0**    | ✅ clean                                            |
| juniper-cascor        | 21       | 1        | `Security Scan`                                     |
| juniper-canopy        | 18       | 1        | `Security Scan`                                     |
| juniper-data          | 19       | 1        | `Security Scan`                                     |
| juniper-cascor-worker | 19       | 1        | `Security Scan`                                     |
| juniper-deploy        | 7        | 1        | `Security Scan`                                     |
| juniper-data-client   | 17       | 1        | `Security Scan`                                     |
| juniper-cascor-client | 17       | 1        | `Security Scan`                                     |
| juniper-recurrence    | 6        | 3        | `Security Scan`, `Analyze (python)`, `Quality Gate` |

**Cause:** `Security Scan` (singular) was added fleet-wide, but **only juniper-ml names
its job that way**. Six repos emit `Security Scans` (plural); deploy and recurrence have
no security-scan job at all.

**Fix:**

| Repo                                                            | Action                                                                               |
|-----------------------------------------------------------------|--------------------------------------------------------------------------------------|
| cascor, canopy, data, cascor-worker, data-client, cascor-client | `Security Scan` → **`Security Scans`**                                               |
| deploy                                                          | **remove** `Security Scan` — no such job (Tier 2 adds one)                           |
| recurrence                                                      | **remove** `Security Scan`, `Analyze (python)`, `Quality Gate` — none exist (Tier 2) |
| juniper-ml                                                      | none — already correct                                                               |

---

## 4b. Validation — headless merge proven on all 9 repos (2026-08-12)

A probe PR was opened in every repo (docs-only — deliberately the **stricter** case, most
likely to expose a wrongly-required path-gated context). Every merge was verified against
its ruleset rule-suite: `result: pass` means the rules were **evaluated and satisfied**;
`bypass` would mean admin override. **All ten merges recorded `pass`.**

| Repo                  | PR                | Merge SHA  | Rule suite |
|-----------------------|-------------------|------------|------------|
| juniper-ml            | #1071             | `21beca1a` | `pass`     |
| juniper-ml            | #1070 (re-signed) | `c90584cd` | `pass`     |
| juniper-cascor        | #510              | `ed7c5907` | `pass`     |
| juniper-canopy        | #487              | `1cec3328` | `pass`     |
| juniper-data          | #259              | `08e9a416` | `pass`     |
| juniper-cascor-worker | #150              | `82686487` | `pass`     |
| juniper-deploy        | #174              | `11150bc5` | `pass`     |
| juniper-data-client   | #147              | `7a28b0b0` | `pass`     |
| juniper-cascor-client | #114              | `270c2669` | `pass`     |
| juniper-recurrence    | #106              | `0bfe142b` | `pass`     |

### The blocker chain (each masked the next)

1. `required_status_checks` — fleet-union of 30 contexts; 200 unsatisfiable fleet-wide.
2. `code_scanning` — a **second** fleet-union: 7 tools where repos upload only 1–2.
3. `require_last_push_approval: true` — requires approval of the last push *by someone
   other than the pusher*. Structurally unsatisfiable for a solo maintainer, who also
   cannot approve their own PR. Meaningful only alongside
   `required_approving_review_count >= 1`; with 0 it just deadlocks.
4. **Legacy branch protection on juniper-recurrence** (§4c).
5. Stale auto-merge queue — a ruleset edit is not a PR event.

### 4c. Legacy branch protection — juniper-recurrence only

`/repos/pcalnon/juniper-recurrence/branches/main/protection` returned a full **classic
branch-protection** config living *alongside* the ruleset. **Both layers are enforced**,
and the ruleset work never touched it. It carried two independent blockers:

- `required_pull_request_reviews.required_approving_review_count: 1` (the ruleset says 0)
- required contexts `Test — torch MLP readout (Rung 2b; optional [torch] extra)` (reports
  on 1/7 PRs) and `Bench required checks` (3/7) — both path-gated, so neither ever reports
  on a docs-only PR

All 8 sibling repos return `404 Branch not protected`. Deleted 2026-08-12 after the
ruleset was confirmed to cover the same ground; the pre-delete config was captured first.

**Check this layer first** when a repo is BLOCKED with every ruleset rule satisfied —
`/rules/branches/main` does **not** surface it.

### 4d. Operational findings

| Finding | Consequence |
|---|---|
| **REST contents API creates UNSIGNED commits** | Unusable under `required_signatures`. Only the GraphQL `createCommitOnBranch` mutation signs. Same class as the #1070 unsigned-commit block, reached from the other direction. |
| **An unsigned commit anywhere on a PR branch blocks the merge** | Squash-merge does **not** rescue it (this supersedes the older "squash is GitHub-signed so branch commits don't matter" belief). |
| **`allow_auto_merge: false` on 8 of 9 repos** (only juniper-ml `true`) | `gh pr merge --auto` there **silently falls back to an immediate merge** instead of arming. Sharp edge for any automated flow. |
| **A PR stuck at `CLEAN`** | Re-arm auto-merge — a ruleset edit is not a PR event, so nothing re-evaluates the queue. Do **not** admin-merge. |
| **canopy requires the macOS unit-test leg** | It carries the known CSRF-TTL flake (`test_validate_refreshes_ttl`; 1 failed / 5645 passed, green on rerun). juniper-data runs its macOS leg `continue-on-error` while keeping the Linux legs required — canopy is inconsistent with that. See Tier 2. |
| **Renaming a test is a symbol LOSS to post-merge `main-verify`** | The screen is AST-based and does not know a rename from a deletion, so the old qualified name must be waived on the squash commit or `main-verify` goes red on `main` — see §4e. |
| **Demoting a `###` heading is a docs DELETION to post-merge `main-verify`** | The docs screen counts headings, not prose, so turning `### X` into `**X**:` reads as `heading-deletion` even when the content is untouched. Same stickiness, different screen and different trailer (`Allow-Docs-Rewrite`) — see §4f. |

### 4e. Renames need a waiver trailer on the *squash* commit

Renaming `FleetSupervisorAgentTest.test_body_notes_gpgsign_for_delegated_commits` in ml#1062
(a deliberate, documented rename) left post-merge **main-verify** red on `main`: the symbol
screen reported `[FAIL/LOST] … method:FleetSupervisorAgentTest.test_body_notes_gpgsign_for_delegated_commits`
because the squash commit carried no waiver trailer.

Three things make this bite harder than it looks:

1. **The screen cannot distinguish a rename from a deletion.** It compares AST symbol
   inventories between base and head; the old qualified name is simply gone.
2. **The trailer must be on the commit that actually lands on `main`.** A trailer written only
   on a branch commit is discarded by squash-merge. Set it in the squash body at merge time.
3. **A red `main-verify` is sticky.** Its catch-up base is the last *successful* main-verify tip
   that is an ancestor of HEAD, so once the streak starts the screened window keeps growing and
   the same finding re-reports on every later commit — including commits from other sessions
   that had nothing to do with it. One waiver clears the whole streak.

Diagnosis note: this streak began earlier, on 2026-08-10 at `b8201d0`, with a **different** job
failing (`Regression Battery`, symbol screen green). That resolved on its own, and by
2026-08-14 the battery was green on every run while the symbol screen was the sole failure.
Check *which job* failed before assuming a streak has one cause.

### 4f. The same trap on the *docs* screen — heading demotion (2026-08-14)

§4e's streak cleared, and `main` went red again two days later from the **sibling** screen. The
cause was `68f62f5` ("docs: update validation records and improve table formatting"), which
demoted a heading in the canopy E2E matrix note:

```text
files_screened=5 findings=132 fail=1 by_reason={'heading-deletion': 1, 'small-deletion': 131}
  [FAIL/heading-deletion] notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md
                          {'headings': ['### Validation record'], 'deleted': 1, 'added': 1}
```

`### Validation record` became `**Validation record**:` — the section survived verbatim, only its
markup changed. `deleted: 1, added: 1` is the tell: a *retitle-shaped* edit, not a content loss.

What generalises from §4e, and what does not:

| Property | §4e (symbol screen) | §4f (docs screen) |
|---|---|---|
| Trailer | `Allow-Symbol-Loss` | `Allow-Docs-Rewrite` |
| Must ride the squash commit | yes | yes |
| Sticky via the G3.1 catch-up base | yes | yes |
| Token matched | qualified symbol name | **file path or bare basename** |
| Failing job name | `Symbol & Docs Screen` | `Symbol & Docs Screen` (same job — check the `by_reason` line, not the job name) |

Two additions to the §4e playbook:

1. **Both screens run in one job**, so the job name alone does not tell you which fired. Read the
   `by_verdict=` (symbol) vs `by_reason=` (docs) summary line.
2. **Only `FAIL`-severity findings need waiving.** The run above reported 132 findings but
   `fail=1`; the 131 `small-deletion` rows are WARN and never block. Waive the one FAIL path —
   do not reach for the `*` wildcard.

The trailer is `Allow-Docs-Rewrite: <path>`, and it accepts the bare basename as well as the
repo-relative path (`_waives()` in `juniper_ci_tools/docs_additions_check.py`).

#### Promoting `Sequence Safety` to required would not have prevented this

The natural conclusion — "`68f62f5` reached `main` without per-PR screening, so promote the
advisory gate" (§2, juniper-ml#1011) — **does not follow**, and acting on it would leave the hole
open while looking closed.

`juniper-ml-rules` (`13805432`, `enforcement=active`) *already* carries a `pull_request` rule.
`68f62f5` still landed as a direct push, because the ruleset grants `RepositoryRole id=5`
(**Admin**) a bypass of mode `always`. An `always` bypass skips `required_status_checks` exactly as
it skips the PR requirement — so a check promoted from advisory to required is still never
consulted on an admin push. **#1011 does not close this path; juniper-ml#1012 (bypass-actor
removal) is the item that does.** Until then the only reliable mitigations are behavioural: route
the change through a PR even when you *can* bypass, or know to carry the trailer in the pushed
commit itself.

Contrast **juniper-cascor**, whose analogous incident looks identical from the outside and has the
opposite remedy: `4081f5b` swept five live `snapshot_*.py` modules out with stale `.h5` artifacts on
a direct push, breaking `create_app` at import (caught by this same post-merge net; restored by
cascor#501, adjudicated in cascor#500). There the repo genuinely *lacked* a `pull_request` rule, and
adding one closed it. **ml's gap is the bypass, not a missing rule — the cascor remediation does not
transfer.** Check which of the two shapes you have before prescribing a fix.

---

## 5. Tier 2 — roadmap (checks each repo would benefit from)

Ordered by value. "N/A" reasons are given where a fleet check does not apply.

### juniper-ml

| Check                     | Why                                                                                                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Gitleaks`                | Repo carries SOPS-encrypted `.env` / `.env.secrets`; secret scanning is the natural guard and the `no-unencrypted-env` pre-commit hook only covers committed plaintext. |
| `SOPS Validation`         | `.sops.yaml` is live but nothing validates encryption in CI. deploy already has this job to copy.                                                                       |
| `Unit Tests + Coverage`   | ml has `Regression Tests` only — no coverage gate, while every sibling enforces one.                                                                                    |
| `Lockfile Freshness`      | `lockfile-update.yml` regenerates weekly, but no PR check catches a stale `conf/requirements_ci.txt`.                                                                   |
| Promote `Sequence Safety` | ml#1011, after the ~2026-08-21 soak.                                                                                                                                    |

### juniper-cascor

| Check                     | Why                                              |
|---------------------------|--------------------------------------------------|
| `Gitleaks`                | Not present; cascor holds API-key handling code. |
| Promote `Sequence Safety` | ml#1011.                                         |

*N/A: `Release-Train Archive Guard` (juniper-ml only), `Compose Validation` (deploy only).*

### juniper-canopy

| Check                     | Why                                                              |
|---------------------------|------------------------------------------------------------------|
| **macOS leg decision**    | **Raised by the 2026-08-12 validation.** canopy *requires* `Unit Tests + Coverage (Python 3.12 on macos-latest)`, and that leg carries the known CSRF-TTL flake (`test_validate_refreshes_ttl`) — so headless merge here fails intermittently and needs a rerun. Either fix the flake or run the macOS leg `continue-on-error` and require only the Linux legs, which is what juniper-data already does. |
| `Bandit`                  | canopy is the only service repo without a standalone Bandit job. |
| `Gitleaks`                | Handles `CANOPY_API_KEY` / CSRF secrets.                         |
| Promote `Sequence Safety` | ml#1011.                                                         |

### juniper-data

| Check                              | Why                                                              |
|------------------------------------|------------------------------------------------------------------|
| Fix the unexpanded matrix job name | Defect 4 above — currently emits a literal `${{ ... }}` context. |
| `Gitleaks`                         | Handles `JUNIPER_DATA_API_KEY`.                                  |
| Promote `Sequence Safety`          | ml#1011.                                                         |

### juniper-cascor-worker

| Check                       | Why                                                                         |
|-----------------------------|-----------------------------------------------------------------------------|
| `Docker Build & Smoke Test` | The only containerized service repo without one; the worker ships an image. |
| `Gitleaks`                  | `_FILE` secret-indirection code path (worker#94/#95).                       |
| Promote `Sequence Safety`   | ml#1011.                                                                    |

### juniper-deploy — ⚠️ thinnest CI in the fleet (6 checks)

| Check                        | Why                                                               |
|------------------------------|-------------------------------------------------------------------|
| `Analyze (python)` (CodeQL)  | No static analysis at all today, despite shipping Python tooling. |
| `Documentation Links`        | Large `docs/` surface, entirely unvalidated.                      |
| `Dependency Documentation`   | No dependency-doc generation, unlike all 8 siblings.              |
| `Security Scans` (pip-audit) | No dependency CVE screen.                                         |
| `Lockfile Freshness`         | No lockfile drift gate.                                           |

### juniper-data-client / juniper-cascor-client

| Check                     | Why                                                   |
|---------------------------|-------------------------------------------------------|
| `Lockfile Freshness`      | Both lack the drift gate their sibling services have. |
| `Gitleaks`                | Both handle API keys.                                 |
| Promote `Sequence Safety` | ml#1011.                                              |

*N/A: `Docker Build & Smoke Test`, `Compose Validation` (libraries, no image).*

### juniper-recurrence — ⚠️ largest gap; structural fix first

| Step                           | Why                                                                                                                                                                                                  |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1. Core suite, all PRs**     | Req for everything. `Test`, `Lint (ruff)`, `Build distribution`, `Required checks` path-gate: 4/7 PRs, No meaningful checks required. Drop path filters on core lane or add always-run fallback job. |
| **2. Adopt fleet naming**      | `Required checks` → `Quality Gate`; `Documentation links` → `Documentation Links`. Removes a standing drift class.                                                                                   |
| 3. `Analyze (python)` (CodeQL) | No static analysis today.                                                                                                                                                                            |
| 4. `Security Scans` + `Bandit` | No dependency CVE or security-lint screen.                                                                                                                                                           |
| 5. `Dependency Documentation`  | Absent, unlike all siblings.                                                                                                                                                                         |
| 6. `Lockfile Freshness`        | Absent.                                                                                                                                                                                              |
| 7. Coverage gate               | No `Unit Tests + Coverage` equivalent.                                                                                                                                                               |
| 8. `Gitleaks`                  | Absent.                                                                                                                                                                                              |
| 9. ~~**Re-add `code_scanning` + `code_quality`**~~ **— DONE, and the rationale was wrong.** | Both rules were removed from recurrence's ruleset on 2026-08-12 and have since been **restored**: as of 2026-08-20 `juniper-recurrent-rules` carries all **8** fleet-standard rules (`deletion`, `non_fast_forward`, `creation`, `required_signatures`, `pull_request`, `required_status_checks`, `code_scanning`, `code_quality`). Verify with `gh api repos/pcalnon/juniper-recurrence/rulesets/20634527`. **Correction to the stated reason:** `code_quality` was never "unsatisfiable" in the blocking sense — it is **INERT** (779/785 and 399/399 evaluations pass, 0 fail); the real July blocker was the `update` rule, removed 2026-08-10. Do not re-remove either rule on that reasoning. See [`…_BYPASS-ACTOR-CENSUS.md`](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_BYPASS-ACTOR-CENSUS.md) and the release-train runbook §8 item 5. |

recurrence is a **publishing repo shipping 3 packages** and has the weakest CI of the nine
— worth a dedicated hardening pass. It was also the only repo carrying legacy branch
protection (§4c), and the only one that started this arc with no ruleset at all.

---

## 6. Applying the Tier 1 lists

Repository ruleset writes reject fine-grained PATs (verified 2026-08-10: `Administration:
Read and write` granted and repo-scoped, other admin writes succeed, ruleset `PATCH`
returns 404 via both `gh` and raw `curl`, on active and disabled rulesets alike, with no
`X-Accepted-GitHub-Permissions` header). Apply via **Settings → Rules → the active ruleset
→ Require status checks to pass**, or via a classic PAT with `repo` scope.

Order of operations per repo:

1. Remove **all 30** existing contexts (every one is either wrong or a duplicate variant).
2. Add the Tier 1 list verbatim.
3. Leave **Require branches to be up to date** (`strict`) **ON** — deliberate, retained as
   the anti-storm guarantee after the Cursor-generated PR-storm damage.
4. juniper-cascor-worker only: also drop the `update` rule (defect 5).

Verify per repo afterwards:

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py --repo juniper-ml
# expect: BLOCKING=0
```

Then confirm end-to-end on a live PR — `mergeStateStatus` should reach `CLEAN`:

```bash
gh pr view <N> --repo pcalnon/<repo> --json mergeable,mergeStateStatus
```

---

## 7. Related

- juniper-ml#1011 — promote per-PR Sequence Safety to required (soak hold ~2026-08-21)
- juniper-ml#1012 — bypass-actor removals (safe only once Tier 1 lands, else `main`
  becomes unmergeable by anyone)
- juniper-ml#1062 — the live BLOCKED proof case
