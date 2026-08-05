# Validating `ANTHROPIC_API_KEY` Org-Secret Access on Public Repos

**Author**: Paul Calnon (Claude-assisted)
**Date**: 2026-05-10
**Companion to**: [`JUNIPER_2026-05-09_JUNIPER-DEPLOY_GO-PUBLIC-ANALYSIS.md`](./JUNIPER_2026-05-09_JUNIPER-DEPLOY_GO-PUBLIC-ANALYSIS.md) §6.4 / item #7
**Status**: Walkthrough — execute end-to-end after any repo flips visibility (last flip: `juniper-deploy` 2026-05-10).

---

## 0. Why this matters

`anthropics/claude-code-action` consumes `secrets.ANTHROPIC_API_KEY` at runtime. The key is billed against your Anthropic account, so an attacker who can trigger a workflow run that resolves the secret can burn budget (worst case) or exfiltrate the key (catastrophic case). Going public on `pcalnon/juniper-deploy` (and any of the 7 already-public sister repos) means anyone on the internet can:

- open an issue,
- comment on an issue,
- comment on a PR,
- submit a PR review,

and those events are exactly what `claude.yml` listens to. The safeguards that keep this safe are **layered**, and this walkthrough confirms each layer is intact.

The four layers, weakest to strongest:

| # | Layer | Failure mode if absent |
|---|-------|------------------------|
| L1 | Org-secret **scope** (which repos can read it) | An over-broadly-scoped secret leaks to repos you didn't intend to enroll. |
| L2 | `claude.yml` **trigger surface** (no `pull_request_target` / `workflow_run`) | Fork-PRs would inherit secrets and could exfiltrate by echoing them. |
| L3 | `claude.yml` **`if:` guard** (requires literal `@claude` in body/title) | Drive-by spam runs the action at zero authentication cost to attackers. |
| L4 | GitHub's built-in **fork-PR secret-redaction** (since 2023) | Even with all the above, missing this would expose secrets to PR contributors. |

Validating all four takes ~15 minutes. Skip none.

---

## 1. Inventory: where is the key actually defined?

### 1.1 Decide if it's an *org* secret or a *repo* secret

```bash
# Org-level secrets (Actions): admin only, requires `gh auth refresh -s admin:org` if you hit 403
gh api -H "Accept: application/vnd.github+json" \
  /orgs/pcalnon/actions/secrets 2>&1 | jq -r '.secrets[]?.name' || echo "(not an org / no access)"
```

For `pcalnon/juniper-*` the owner is a personal account, not an org, so there are no org-scoped Actions secrets. The key is therefore a **repository secret** on each repo that uses `claude.yml`.

```bash
# Per-repo secrets — list each
for repo in juniper-cascor juniper-data juniper-data-client juniper-cascor-client \
            juniper-cascor-worker juniper-ml juniper-canopy juniper-deploy; do
  printf '\n--- pcalnon/%s ---\n' "$repo"
  gh secret list --repo "pcalnon/$repo" 2>&1 | grep -E 'ANTHROPIC|^[A-Z]' || true
done
```

Expected: `ANTHROPIC_API_KEY` listed on every repo whose `.github/workflows/claude.yml` references it. **Document the value of `Updated` on each row** — multiple values for the same logical key across repos is a sign that they have drifted (different keys, different rotation dates).

### 1.2 If the value is shared across repos

If you're using the same API key in all 8 repos, you have *N* copies of the same secret with *N* independent rotation surfaces. Two acceptable models:

- **Model A — per-repo secret, manually synced**: current state. Rotate everywhere on a schedule; document the rotation procedure in `docs/SECRETS_ONBOARDING.md` of one canonical repo.
- **Model B — convert pcalnon → an org**: GitHub orgs have org-level Actions secrets with selectable repo access (the "Selected repositories" radio). Out of scope for this walkthrough but worth raising as a future-state if rotation friction ever bites.

Either model is safe; just be honest about which you have.

---

## 2. L1 — Org-secret scope (skip for personal-owner setup)

If `pcalnon` were a GitHub org, you would verify scope here:

1. Open `https://github.com/organizations/<ORG>/settings/secrets/actions`
2. Find `ANTHROPIC_API_KEY` in the table
3. Click the secret name
4. Under **"Repository access"**, the radio should read one of:
   - `All repositories` — **DO NOT USE on a public-org account**: any new public repo automatically inherits the secret.
   - `Private repositories` — fine if `juniper-deploy` is now public *and* that's the only public repo, but inverted from what we want.
   - `Selected repositories` — **the correct setting**; click "Manage" and verify the list is exactly the 8 Juniper repos.

CLI equivalent (org-only):

```bash
gh api /orgs/<ORG>/actions/secrets/ANTHROPIC_API_KEY \
  --jq '{visibility, selected_repositories_url}'
gh api /orgs/<ORG>/actions/secrets/ANTHROPIC_API_KEY/repositories \
  --jq '.repositories[].full_name'
```

For the current personal-owner setup, this section is a no-op.

---

## 3. L2 — Trigger surface audit (every claude.yml across the fleet)

This is the most important check. The rule is:

> `claude.yml` MUST NOT use `pull_request_target` or `workflow_run`.
> It SHOULD only use `issue_comment` / `issues` / `pull_request_review` / `pull_request_review_comment`.

`pull_request_target` runs in the *base* repo's context with full secret access *even on fork PRs*. `workflow_run` is similarly dangerous because it runs after a triggering workflow finishes and inherits its event context. Either one would defeat L4 entirely.

### 3.1 Scan all 8 repos at once

```bash
JUNIPER_ROOT=/home/pcalnon/Development/python/Juniper

for repo in juniper-cascor juniper-data juniper-data-client juniper-cascor-client \
            juniper-cascor-worker juniper-ml juniper-canopy juniper-deploy; do
  f="$JUNIPER_ROOT/$repo/.github/workflows/claude.yml"
  [ -f "$f" ] || { printf '%-25s NO claude.yml\n' "$repo"; continue; }
  if grep -qE '^\s*(pull_request_target|workflow_run):' "$f"; then
    printf '%-25s ❌ DANGEROUS TRIGGER FOUND\n' "$repo"
    grep -nE '^\s*(pull_request_target|workflow_run):' "$f"
  else
    printf '%-25s ✅ no dangerous triggers\n' "$repo"
  fi
done
```

Expected output: ✅ on every repo. A ❌ row is a **stop-the-line finding**: rotate the API key immediately and rewrite the trigger before doing anything else.

### 3.2 Spot-check the trigger block

Pick one repo and read the `on:` block to confirm it matches the canonical template:

```bash
sed -n '/^on:/,/^[a-z]/p' "$JUNIPER_ROOT/juniper-deploy/.github/workflows/claude.yml"
```

Canonical content (matches `juniper-ml/.github/workflows/claude.yml` and the source-of-truth comment in `juniper-deploy/.github/workflows/claude.yml`):

```yaml
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]
```

Any divergence (e.g. someone added `push:` or `pull_request:`) is an audit finding — investigate the commit and the rationale before clearing.

---

## 4. L3 — `if:` guard audit

The `if:` clause must require literal `@claude` in event-specific bodies. Without it, **every** issue/comment/review event would spend an Anthropic API call.

```bash
for repo in juniper-cascor juniper-data juniper-data-client juniper-cascor-client \
            juniper-cascor-worker juniper-ml juniper-canopy juniper-deploy; do
  f="$JUNIPER_ROOT/$repo/.github/workflows/claude.yml"
  [ -f "$f" ] || continue
  guard=$(awk '/^\s*claude:/{flag=1} flag && /^\s*if:/{found=1} flag && /^\s*runs-on:/{exit} END{print found?"yes":"no"}' "$f")
  if [ "$guard" = "yes" ]; then
    printf '%-25s ✅ has if-guard\n' "$repo"
  else
    printf '%-25s ❌ MISSING if-guard\n' "$repo"
  fi
done
```

For each ✅ row, eyeball the actual condition and confirm it includes a `contains(..., '@claude')` clause for every event the workflow listens to. The juniper-deploy / juniper-ml canonical condition:

```yaml
if: |
  (github.event_name == 'issue_comment'
    && contains(github.event.comment.body, '@claude')) ||
  (github.event_name == 'pull_request_review_comment'
    && contains(github.event.comment.body, '@claude')) ||
  (github.event_name == 'pull_request_review'
    && contains(github.event.review.body, '@claude')) ||
  (github.event_name == 'issues'
    && (contains(github.event.issue.body, '@claude')
        || contains(github.event.issue.title, '@claude')))
```

Drift to watch for:

- A `github.event_name` listed in `on:` but not in the `if:` clause → that event runs the action unconditionally.
- A new event type added to `on:` without a matching `contains(...)` clause.
- `'claude'` (no `@`) instead of `'@claude'` → 100× more drive-by triggers from ordinary discussion.

---

## 5. L4 — Confirm GitHub's built-in fork-PR secret redaction

Since 2023, GitHub does **not** pass repository or org secrets to workflows triggered by `pull_request` events from forks. This is the silent layer that makes L2/L3 mistakes survivable.

### 5.1 Verify org/account setting (no opt-out)

There is no UI to "enable" this — it's the platform default and cannot be disabled per-repo. The only way to leak secrets to a fork PR is to use `pull_request_target` or `workflow_run` (covered in §3) or to manually echo a secret into a build artifact.

### 5.2 Spot-check by inspecting a real run

Trigger one yourself: open a draft issue on `pcalnon/juniper-deploy` titled `@claude please ignore — testing access` (or comment on an existing issue). After the run completes:

```bash
# List the most recent claude.yml runs
gh run list --workflow claude.yml --repo pcalnon/juniper-deploy -L 3

# Inspect the run and confirm the API key is masked
RUN_ID=$(gh run list --workflow claude.yml --repo pcalnon/juniper-deploy -L 1 --json databaseId --jq '.[0].databaseId')
gh run view "$RUN_ID" --repo pcalnon/juniper-deploy --log 2>&1 | grep -iE '(anthropic_api_key|sk-ant-)' | head
```

Expected: every appearance of the secret value in logs is rendered as `***`. If you ever see the literal `sk-ant-...` in a log, **rotate the key immediately** and audit the action version that exposed it.

### 5.3 Probe from a fork (optional, gold-standard test)

To prove no secret reaches a fork-PR job:

1. From a different GitHub account (or a friend's account), fork `pcalnon/juniper-deploy`.
2. In that fork, create a no-op branch, push a commit, and open a PR back to `pcalnon/juniper-deploy:main`.
3. Add a PR review comment containing `@claude please run`.
4. Watch the workflow run that fires in `pcalnon/juniper-deploy/actions`. Confirm:
   - Event = `pull_request_review_comment` (the legitimate trigger).
   - The "Run Claude Code" step runs in the **base** repo's context — i.e. it has access to the secret because the comment was made on the base repo, not because the PR came from a fork.
   - **Crucially**, GitHub does not need to pass secrets to anything in the fork's checkout because no fork-side workflow runs.

If you instead saw a workflow run in the *fork's* `actions/` tab that received the secret, that would be a leak — file an issue with GitHub Support. (This has never happened; document the test result either way.)

---

## 6. Cost & abuse hygiene

L1–L4 stop **secret theft**. They don't stop **budget burn**. Anyone who learns the `@claude` trigger phrase and is willing to keep typing can cost you Anthropic API spend with no work on their part.

### 6.1 Confirm budget alarms exist

- Anthropic Console → Billing → confirm a hard spend cap is set, not just a soft notification threshold. Note the value.
- Set a daily-spend email alert at, e.g., 25% of monthly budget so a runaway abuse loop pages you within hours, not weeks.

### 6.2 Add a per-repo runaway brake (optional, recommended)

GitHub Actions concurrency:

```yaml
concurrency:
  group: claude-${{ github.event.issue.number || github.event.pull_request.number || github.run_id }}
  cancel-in-progress: false
```

A more aggressive pattern: gate `claude.yml` on the commenter being in a list (e.g. via a custom `if:` clause referencing `github.event.comment.user.login`). Trade-off: less open / collaborative. Reasonable for a private-feel public repo.

### 6.3 Watch the Anthropic Console usage tab

Spend changes in dollars/hour, not in PR-cycles. After flipping juniper-deploy public, refresh the Anthropic Console daily for the first week and weekly thereafter. Anomalies > 10× baseline are the fingerprint of an abuse run.

---

## 7. One-shot validation script — SHIPPED

The validator lives at [`util/validate_claude_yaml_access.bash`](../util/validate_claude_yaml_access.bash) in juniper-ml. It performs the L2 / L3a / L3b checks from §3-§4 and exits non-zero on any finding. Behaviors:

- `util/validate_claude_yaml_access.bash` — defaults to `juniper-ml/.github/workflows/claude.yml`.
- `util/validate_claude_yaml_access.bash <file-or-dir> ...` — explicit targets (a directory is resolved to `<dir>/.github/workflows/claude.yml`).
- `JUNIPER_ROOT=/path/to/Juniper util/validate_claude_yaml_access.bash` — fans out across all 8 canonical sibling repos.
- `VERBOSE=1` — emits per-file trace lines.

Exit codes: `0` clean, `1` finding, `2` usage / I/O error.

### CI integration — also SHIPPED

`juniper-ml/.github/workflows/ci.yml` now has a dedicated `claude-yaml-audit` job (`needs: [pre-commit]`) that runs the validator against the live `.github/workflows/claude.yml` on every push and PR. It is wired into `required-checks`, so a regression in the workflow blocks merge.

The validator's own unit tests (`tests/test_validate_claude_yaml_access.py`, 8 cases covering the happy path, both L2 trigger variants, both L3 variants, the directory-argument resolver, and the usage-error path) run inside the existing Python regression matrix on Python 3.12 / 3.13 / 3.14.

### Cross-repo coverage — ALSO SHIPPED

`juniper-ml/.github/workflows/docs-full-check.yml` (weekly schedule + `workflow_dispatch`) now runs the validator across all 8 sibling repos after the existing cross-repo doc-link check. It clones the 7 siblings into `$GITHUB_WORKSPACE`, then invokes:

```bash
JUNIPER_ROOT="$GITHUB_WORKSPACE" \
  bash juniper-ml/util/validate_claude_yaml_access.bash
```

The job blocks (exits non-zero) on any structural finding in any cloned repo. Because the workflow is schedule/dispatch only — never on PRs — developer velocity is unaffected even when a sibling repo introduces a regression. Either fix the sibling and re-dispatch, or open a triage issue on the affected repo.

The result: the per-PR `claude-yaml-audit` job in juniper-ml's `ci.yml` catches local regressions on every push; the weekly `docs-full-check` job catches cross-repo drift in every sibling. Both feed off the same `util/validate_claude_yaml_access.bash` so a fix applied to the validator propagates everywhere.

---

## 8. Sign-off checklist

Run through each item once after `juniper-deploy` flips public, and again after any future visibility flip or `claude.yml` edit. Save the timestamped output of the script in §7 to your records (or attach it to the corresponding analysis-doc PR).

- [ ] `gh secret list --repo pcalnon/juniper-deploy` lists `ANTHROPIC_API_KEY` and matches `Updated` timestamps with the other Juniper repos.
- [ ] §3.1 scan: ✅ on every repo.
- [ ] §3.2 spot-check: `on:` block matches the canonical template on at least 2 repos.
- [ ] §4 scan: ✅ on every repo.
- [ ] §5.2: most recent run's logs show `***` where the API key would appear.
- [ ] §5.3 (gold-standard): fork-PR test confirms no fork-side workflow receives the secret. (Optional but recommended once.)
- [ ] §6.1: Anthropic Console hard-cap is set; soft-alert wired to email.
- [ ] §6.3: baseline spend recorded ($/day) so a future anomaly is detectable.
- [x] §7 script committed and wired into juniper-ml CI as `claude-yaml-audit` (2026-05-10).

If every box is checked, you can close item #7 of the public-release analysis as
**Validated 2026-05-10 (or whatever date you ran this)** and move on.

---

## 9. If something fails

In rough order of severity:

| Finding | Severity | Action |
|---------|---------:|--------|
| §5.2 shows literal `sk-ant-...` in a log | **CRITICAL** | Rotate the key in Anthropic Console immediately, revoke the action SHA from `claude.yml`, audit billing. |
| §3.1 finds `pull_request_target` / `workflow_run` | **CRITICAL** | Rotate the key, rewrite the trigger, force-push the fix; audit recent runs from forks for log artifacts. |
| §4 finds a missing `if:` guard | **HIGH** | Add the guard, push a fix; audit Anthropic spend for unauthorized runs back to the moment the workflow shipped. |
| §1.1 shows different `Updated` timestamps across repos | **MEDIUM** | Decide whether the repos use distinct keys (drift hazard) or stale copies of the same key (rotation hazard); pick a model and document. |
| §6.1 shows no spend cap | **MEDIUM** | Set one. |
| §5.3 fork-PR probe receives the secret | **CRITICAL** | This would be a GitHub platform bug; file with GitHub Support and rotate the key. |

The remediation pattern is always the same:

1. Rotate the Anthropic key first (assume any failure means it's exposed).
2. Patch the workflow second.
3. Audit logs last (now that the bleeding has stopped).

Don't skip step 1 even if you "know" only one of the layers failed — defense-in-depth means assuming you don't know which other layer is also degraded.
