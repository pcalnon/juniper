# Worktree Cleanup Procedure V2

**Purpose**: Standardized procedure for completing work in a worktree, merging, creating PRs, and transitioning to a new worktree — without trapping the Claude Code session in an invalid CWD
**Project**: juniper-ml
**Last Updated**: 2026-06-25

---

## Why This Procedure Exists

Claude Code sessions run with their CWD set to a worktree directory. The V1 procedure removed the worktree directory without first creating a replacement, leaving the session trapped in a non-existent path. This V2 procedure creates a new worktree and switches the CWD **before** removing the old one.

---

## Prerequisites

- All work in the worktree is committed
- The `gh` CLI is authenticated (`gh auth status`)
- The main repo directory is accessible at `/home/pcalnon/Development/python/Juniper/juniper-ml`

---

## Variables Reference

Set these at the start of cleanup:

```bash
# Old worktree (the one being cleaned up)
OLD_WORKTREE_DIR="<current worktree path>"
OLD_BRANCH="<current worktree branch name>"
PARENT_BRANCH="<branch that was active when worktree was created>"

# Main repo
MAIN_REPO="/home/pcalnon/Development/python/Juniper/juniper-ml"
```

---

## Phase 1: Save & Push Current Work

### Step 1: Verify Clean State

```bash
cd "$OLD_WORKTREE_DIR"
git status
```

**GATE**: Working tree must be clean. If dirty, commit remaining changes:

```bash
git add <files>
git commit -m "<final commit message>"
```

### Step 2: Push Worktree Branch to Remote

```bash
git push origin "$OLD_BRANCH"
```

---

## Phase 2: Create New Worktree (Session Continuity)

This phase MUST complete before Phase 4 (old worktree removal).

### Step 3: Fetch Latest and Generate New Worktree Metadata

```bash
git fetch origin
NEW_BRANCH="worktree-<claude-session-name>"
NEW_WORKTREE_DIR="${MAIN_REPO}/.claude/worktrees/<claude-session-name>"
```

### Step 4: Create New Worktree

```bash
git worktree add "$NEW_WORKTREE_DIR" -b "$NEW_BRANCH" origin/main
```

### Step 5: Switch CWD to New Worktree

```bash
cd "$NEW_WORKTREE_DIR"
```

### Step 6: Verify New CWD

```bash
pwd
git status
git branch --show-current
```

**GATE**: CWD must be inside the new worktree. `pwd` must match `$NEW_WORKTREE_DIR`. Do NOT proceed to Phase 4 until this is confirmed.

---

## Phase 3: Merge & Pull Request

### Step 7: Determine Merge Strategy

| Parent Branch | Strategy |
|---------------|----------|
| `main` | Create PR directly: `old-branch → main` |
| Not `main` | Merge `old-branch → parent`, then create PR: `parent → main` |

### Step 8a: If Parent Is `main`

Create a pull request (do NOT merge directly):

```bash
gh pr create \
  --repo pcalnon/juniper-ml \
  --base main \
  --head "$OLD_BRANCH" \
  --title "<short descriptive title>" \
  --body "<PR description>"
```

**PR description**: Generate using:
- Template: `notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md`
- Reference: `notes/pull_requests/PR_*.md` (format and content examples)

### Step 8b: If Parent Is NOT `main`

First merge the worktree branch into the parent branch:

```bash
cd "$MAIN_REPO"
git checkout "$PARENT_BRANCH"
git pull origin "$PARENT_BRANCH"
git merge "$OLD_BRANCH"
git push origin "$PARENT_BRANCH"
cd "$NEW_WORKTREE_DIR"
```

Then create a PR from parent to main:

```bash
gh pr create \
  --repo pcalnon/juniper-ml \
  --base main \
  --head "$PARENT_BRANCH" \
  --title "<short descriptive title>" \
  --body "<PR description>"
```

### Step 8c: Merge Conflict Handling

If the merge in Step 8b produces conflicts:

```bash
git merge --abort
```

Create a PR instead and resolve conflicts there:

```bash
gh pr create \
  --repo pcalnon/juniper-ml \
  --base "$PARENT_BRANCH" \
  --head "$OLD_BRANCH" \
  --title "Merge $OLD_BRANCH into $PARENT_BRANCH"
```

---

## Phase 4: Remove Old Worktree

**PREREQUISITE**: CWD must be in the new worktree (verified in Step 6).

### Step 9: Remove Old Worktree Directory

```bash
git worktree remove "$OLD_WORKTREE_DIR"
```

If removal fails (uncommitted changes):

```bash
git worktree remove --force "$OLD_WORKTREE_DIR"
```

### Step 10: Delete Old Branch (Local)

```bash
git branch -d "$OLD_BRANCH"
```

If the branch is not fully merged (e.g., PR pending):

```bash
git branch -D "$OLD_BRANCH"
```

### Step 11: Delete Old Branch (Remote)

> **IMPORTANT**: If a PR is open for this branch, do NOT delete the remote branch.
> Deleting the remote branch will close/invalidate the PR. The PR merge process
> on GitHub will handle remote branch cleanup automatically.

Only delete after the PR is merged or the branch is no longer needed:

```bash
# First check for open PRs
gh pr list --head "$OLD_BRANCH" --state open

# Only if no open PRs:
git push origin --delete "$OLD_BRANCH"
```

### Step 12: Prune

```bash
git worktree prune
```

---

## Phase 5: Verify

### Step 13: Final Verification

```bash
# CWD is valid
pwd && ls

# Worktree list is clean
git worktree list

# Branch list is clean
git branch

# Working tree is clean
git status
```

---

## Phase 6: Sync to Latest `main`

Once the old worktree directory and branch are removed, bring your checkout up
to date with the latest remote `main`. Which form applies depends on whether a
worktree or branch tied to this session is still live.

> **Why two forms**: a branch can be checked out in only one worktree at a time,
> and `main` is checked out in `MAIN_REPO`. While you are still inside a session
> worktree, `git checkout main` would fail — so you fast-forward your current
> branch toward `main` in place. Only once every session worktree is gone do you
> check `main` out and fast-forward it directly.

### Step 14: Sync (Case A — a session worktree/branch is still in use)

Standard flow: the continuity worktree created in Phase 2 is still your working
checkout (or some other session worktree/branch is not yet ready to be removed).
Stay in it and fast-forward to the latest `main` without switching branches:

```bash
git fetch --all && git pull --ff-only origin main
```

`--ff-only` is intentional: if the current branch carries commits that are not on
`origin/main`, the pull refuses rather than creating a merge commit — the signal
to finish or hand off that branch before syncing.

### Step 15: Sync (Case B — all session worktrees, dirs, and branches are gone)

Terminal cleanup: every worktree, directory, and branch associated with this
session has been removed and you are back in `MAIN_REPO`. Check `main` out and
fast-forward it:

```bash
git fetch --all && git checkout main && git pull --ff-only origin main
```

---

## Phase 7: Restore the MAIN_REPO Checkout to `main` (always)

Regardless of Case A/B above, finish every merged-PR cleanup by returning the
**primary checkout** (the repo root, not a worktree) to an up-to-date `main`.
Release and hotfix work can leave it stranded on a non-`main` branch — the F-6
stale-checkout class; e.g. the main checkout sat on
`release/juniper-service-core-v0.5.0` after the 2026-07-18 release — where it
silently feeds stale state to every tool that reads the primary checkout.

### Step 16: Restore and fast-forward

```bash
cd <path to root of current repo>
git checkout main
git pull --ff-only origin main
```

Safety gates (the script automates these): skip with a warning if the primary
checkout's tree is dirty (never clobber uncommitted work), and treat a
`checkout main` refusal (main checked out in another worktree) as
warn-and-skip, never fatal.

---

## Quick Reference (Copy-Paste)

```bash
# --- Phase 1: Save & Push ---
cd "$OLD_WORKTREE_DIR"
git status  # must be clean
git push origin "$OLD_BRANCH"

# --- Phase 2: New Worktree (MUST complete before Phase 4) ---
git fetch origin
git worktree add "$NEW_WORKTREE_DIR" -b "$NEW_BRANCH" origin/main
cd "$NEW_WORKTREE_DIR"    # CRITICAL: CWD must move here before old worktree is removed
pwd && git status          # verify CWD is valid

# --- Phase 3: PR (if parent is main — do NOT merge directly) ---
gh pr create --repo pcalnon/juniper-ml --base main --head "$OLD_BRANCH" \
  --title "<title>" --body "<body>"

# --- Phase 4: Cleanup ---
git worktree remove "$OLD_WORKTREE_DIR"
git branch -D "$OLD_BRANCH"    # -D because branch is not merged locally (PR pending)
# Do NOT delete remote branch if PR is open — GitHub handles this after merge
git worktree prune

# --- Phase 5: Verify ---
pwd && git worktree list && git branch && git status

# --- Phase 6: Sync to latest main ---
# Case A (standard flow — still in the continuity worktree): sync in place.
git fetch --all && git pull --ff-only origin main
# Case B (terminal — no session worktrees left): check out main first.
# git fetch --all && git checkout main && git pull --ff-only origin main

# --- Phase 7: Restore MAIN_REPO checkout to main (always; skip if tree dirty) ---
cd "$MAIN_REPO" && git checkout main && git pull --ff-only origin main
```

---

## Script Automation

The procedure above can be automated using:

```bash
NEW_WORKTREE="$(util/worktree_cleanup.bash \
  --old-worktree "$OLD_WORKTREE_DIR" \
  --old-branch "$OLD_BRANCH" \
  --parent-branch "$PARENT_BRANCH" \
  --skip-remote-delete)"
cd "$NEW_WORKTREE"
```

**Important**: The script outputs the new worktree path to stdout. The caller MUST `cd` to that path after the script completes. The script cannot change the caller's CWD because it runs in a subshell.

Use `--skip-remote-delete` when a PR was created, since the remote branch is needed for the PR. The PR merge process (on GitHub) will handle remote branch cleanup.

See `util/worktree_cleanup.bash --help` for full options and `--dry-run` support.

---

## Edge Cases

### PR Already Exists for Branch

Check before creating:

```bash
gh pr list --head "$OLD_BRANCH" --state open
```

### Multiple Worktrees Needing Cleanup

Run `util/worktree_cleanup.bash` for each, or use `util/cleanup_open_worktrees.bash` for batch operations.

### Batch Stale-Worktree Sweep

Use the ad-hoc sweep pair only when cleaning the centralized Juniper worktree pool at `/home/pcalnon/Development/python/Juniper/worktrees/`. The scripts are intentionally conservative:

- `util/ad-hoc/worktree_sweep_survey.bash` prints a tab-separated report: `STATUS`, `REPO`, `BRANCH`, `WORKTREE`.
- `util/ad-hoc/worktree_sweep_apply.bash` reads that report from stdin and acts only on `SAFE` rows.
- `DIRTY`, `ACTIVE`, `BROKEN`, unknown-repo, missing-directory, non-worktree, and no-longer-safe rows are skipped.
- Apply revalidates every `SAFE` row immediately before removal: the target directory must still be a git worktree, have a clean working tree (tracked/untracked only), and have `rev-list --count origin/main..HEAD == 0`.

**Dirt vs gitignored debris (ml#715 / coverage ml#716).** Survey classifies dirt with plain `git status --porcelain` — tracked modifications and untracked files only. GITIGNORED debris (caches, logs, decrypted secrets) does **not** make a worktree `DIRTY`; ignored-only trees with `ahead == 0` classify as `SAFE`. Apply keeps a separate ignored-content guard at removal time because deleting a worktree also deletes that debris, which may be precious (the decrypted-secrets class):

| Apply mode | Ignored-only SAFE row | Tracked/untracked dirt |
|------------|----------------------|------------------------|
| Default | Skipped (`ignored files present; rerun with --include-ignored…`) | Hard skip (always) |
| `--include-ignored` | Removed | Hard skip (always) |
| `--dry-run --include-ignored` (either flag order) | Prints `DRY:…` only; never deletes | Hard skip (always) |

Unknown apply flags print `unknown flag: …` on stderr and exit `2` (fail-closed). Contract pins: `tests/test_worktree_sweep_scripts.py`.

Recommended operator flow:

```bash
bash util/ad-hoc/worktree_sweep_survey.bash > /tmp/juniper-worktree-sweep.tsv
# Review SAFE rows; expect aged worktrees with only caches/logs to be SAFE, not DIRTY.
bash util/ad-hoc/worktree_sweep_apply.bash --dry-run < /tmp/juniper-worktree-sweep.tsv
# Default: skips ignored-only SAFE rows (protective).
bash util/ad-hoc/worktree_sweep_apply.bash < /tmp/juniper-worktree-sweep.tsv
# After confirming no precious ignored content remains in those trees:
bash util/ad-hoc/worktree_sweep_apply.bash --include-ignored < /tmp/juniper-worktree-sweep.tsv
```

Status meanings:

| Status | Meaning | Action |
|--------|---------|--------|
| `SAFE` | No tracked/untracked dirt; `HEAD` has no commits beyond the parent repo's `origin/main`. Ignored debris alone still yields `SAFE`. | Eligible for apply (default still skips if ignored files are present; pass `--include-ignored` after review). |
| `ACTIVE` | Clean (tracked/untracked) worktree with commits not in `origin/main`. | Leave for manual ownership/PR triage. |
| `DIRTY` | Tracked modifications or untracked files (`git status --porcelain`). | Never remove in the sweep. |
| `BROKEN` | The script could not resolve repo, branch, `HEAD`, or `origin/main` state. | Manual git triage required. |

For tests or unusual local layouts, set both overrides so the scripts do not assume the default Juniper checkout paths:

```bash
JUNIPER_WORKTREE_SWEEP_REPO_BASE=/path/to/repos \
JUNIPER_WORKTREE_SWEEP_ROOT=/path/to/worktrees \
bash util/ad-hoc/worktree_sweep_survey.bash
```

### Worktree Removal Fails

```bash
git worktree remove --force "$OLD_WORKTREE_DIR"
git worktree prune
```

### Parent Branch Has Diverged

Rebase before merging:

```bash
cd "$OLD_WORKTREE_DIR"
git fetch origin
git rebase "origin/$PARENT_BRANCH"
git push origin "$OLD_BRANCH" --force-with-lease
```

---

## Supersedes

This procedure replaces `notes/WORKTREE_CLEANUP_PROCEDURE.md` (V1).
The V1 file has been moved to `notes/legacy/WORKTREE_CLEANUP_PROCEDURE.md` (consolidated from `notes/history/` 2026-05-05).
