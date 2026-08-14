# HANDOFF 2026-08-14 — branch-protection + Tier 2 CI hardening closeout

Continue the Juniper branch-protection / CI-hardening arc. Standing policy: headless merges only
on Paul's explicit per-PR/group approval; guardrails (checks RAN + green, verify `result=pass` not
`bypass`, defective PRs get corrected re-lands) always apply.

## Completed (this arc)

- **Headless merge works fleet-wide.** All 9 repos merge with rule-suite `result=pass` (not
  `bypass`). Five blockers, each masking the next: a 30-context `required_status_checks`
  fleet-union (200 unsatisfiable contexts); a *second* fleet-union in `code_scanning` (7 tools where
  repos upload 1–2); `require_last_push_approval: true` (unsatisfiable solo — you cannot approve
  your own PR); **legacy branch protection on juniper-recurrence only**, enforced alongside rulesets
  and invisible to `/rules/branches/main`; and a stale auto-merge queue.
- **9/9 at the fleet-standard 8 rules**, `BLOCKING=0` everywhere. recurrence and deploy both
  restored `code_scanning` scoped to **`CodeQL` only** and were validated with docs-only probes.
- **Tier 2 CI hardening.** recurrence: all 4 package gates now report on every PR and are required
  (previously *nothing* gated its 3 published packages — a PR breaking the app merged red).
  deploy: CodeQL + doc-link validation + pip-audit. ml: Gitleaks (+ the load-bearing
  `.gitleaks.toml`) and SOPS validation. canopy: the macOS CSRF-TTL flake fixed at root via an
  injectable clock.
- **Duplicate CI runs eliminated on all 9** — every PR ran its whole suite twice.
- **main-verify green**, clearing a 4-day streak.

## Remaining work

1. **cascor release round.** `[Unreleased]` carries the protocol-floor `Changed` entry, so the next
   detect classifies `UNRELEASED_CHANGES` → minor proposal (0.9.0, pre-1.0). Nothing blocks it.
2. **ml#1011** — promote per-PR Sequence Safety to required. Soak ends ~2026-08-21. Promote in the
   **ruleset**, never via the Quality Gate `needs:` (it skips on push and would redden every merge).
3. **ml#1012** — bypass-actor removals. **Now safe**: previously it would have made `main`
   unmergeable by anyone, because the `update` rule was the only thing letting merges through.
4. **ml#1053 monitor fix is still unexercised** by a real ceremony. The next
   `BUMPED_NOT_RELEASED` cycle should reach `PENDING_PYPI_APPROVAL` in minutes rather than burning
   the 30-min cap.

## Open questions (owner decisions)

- **Doc corruption on `main`, unrepaired.** `f366279` injected paste damage into
  `notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`: a table row
  ending `|Documentation Links`, a stray `Build P` line, and — most consequential — a concatenation
  **inside the juniper-cascor-worker Tier 1 code block**, which is the copy-paste source for ruleset
  config. Left unreverted because it came from an owner commit. Repair?
- **`allow_auto_merge: false` on 8 of 9** (only juniper-ml `true`). Consequence: there
  `gh pr merge --auto` **silently falls back to an immediate merge** instead of arming. Deliberate?
- **Merge queue?** `strict_required_status_checks_policy` is on fleet-wide (the deliberate
  anti-storm guarantee after the Cursor PR-storm damage). Cost: PRs go `BEHIND` repeatedly under
  concurrent merges — ml#1076 needed three rebases. ml's `ci.yml` already has `merge_group:` wired.

## Key context

- **Verify a merge was genuinely non-bypass**, never trust `CLEAN` alone:
  `gh api '/repos/pcalnon/<repo>/rulesets/rule-suites?per_page=2' --jq '.[]|"\(.after_sha[0:8]) \(.result)"'`
- **Legacy branch protection is invisible to `/rules/branches/main`.** When a repo is BLOCKED with
  every ruleset rule green, check `/repos/O/R/branches/main/protection` first.
- **Never list a `code_scanning` tool that does not upload SARIF for that repo** — that single
  mistake, applied fleet-wide, is what made all nine repos unmergeable on 2026-08-10.
- **A waiver trailer must be set in the squash body at merge time** (`gh pr merge --squash
  --body-file`). One written only on a branch commit is discarded. Renames read as symbol LOSS to
  the AST-based screen. A red main-verify is sticky — its catch-up base is the last *successful*
  tip, so one finding re-reports on every later commit until waived.
- **The REST contents API creates UNSIGNED commits**; only the GraphQL `createCommitOnBranch`
  mutation signs. An unsigned commit anywhere on a PR branch blocks the merge — squash does **not**
  rescue it.
- **Verify gaps against job *contents*, not check *names*.** The Tier 2 roadmap over-reported:
  Gitleaks was already a step inside `Security Scans` in six repos, and canopy already had Bandit.
- Tooling: `util/ad-hoc/2026-08-10_ruleset_context_audit.py` (`--json`, `--repo`),
  `2026-08-12_open_branch_protection_probes.py`, `2026-08-13_sweep_duplicate_ci_runs.py` — all
  dry-run by default. Record: `notes/JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`.
- Concurrent sessions own the CLI-experimentation (P4 spiral) and canopy E2E arcs. `gh pr list`
  dup-guard before touching anything.

## Verify starting state

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py            # expect BLOCKING=0 on all 9
gh run list --repo pcalnon/juniper-ml --workflow main-verify.yml --limit 3   # expect success
gh api /repos/pcalnon/juniper-recurrence/rules/branches/main --jq '[.[].type]|length'   # 8
gh api /repos/pcalnon/juniper-deploy/rules/branches/main --jq '[.[].type]|length'       # 8
gh api /repos/pcalnon/juniper-recurrence/branches/main/protection   # expect 404 (legacy removed)
gh issue list --repo pcalnon/juniper-ml --state open                # 1011 / 1012 + backlog
```

## Git status

juniper-ml `main` at `c6b356a` plus this handoff commit; working tree clean, no stashes. All arc
branches merged. Ruleset writes reject fine-grained PATs — apply those via the web UI or a classic
PAT (verified: `Administration: Read and write` granted, other admin writes succeed, ruleset `PATCH`
404s via both `gh` and raw `curl`).
