#!/usr/bin/env bash
# File:    worktree_sweep_survey.bash
# Author:  Paul Calnon
# Created: 2026-05-31
# Purpose: One-shot survey of /home/pcalnon/Development/python/Juniper/worktrees/
#          for stale-worktree cleanup. Classifies each worktree as:
#           SAFE   — clean working tree + branch fully merged to origin/main
#                    (or branch already deleted on remote, or has no
#                    commits beyond origin/main).
#           ACTIVE — clean but has commits NOT in origin/main AND the
#                    branch is alive somewhere. Leave alone unless we
#                    can confirm the work is abandoned.
#           DIRTY  — uncommitted changes. NEVER touch.
#           BROKEN — worktree is in an inconsistent state (missing
#                    branch, detached HEAD on a deleted commit, etc.).
#                    Manual triage required.
#          Prints a tab-separated report to stdout; emits no destructive
#          actions. Pair with worktree_sweep_apply.bash to act on the
#          SAFE rows.
#
# Convention: this is an ad-hoc one-shot. Living under util/ad-hoc/ per
# the CLAUDE.md "Script placement" rule. Promote to util/ proper only if
# we end up running this more than twice.

set -euo pipefail

JUNIPER_BASE="${JUNIPER_WORKTREE_SWEEP_REPO_BASE:-/home/pcalnon/Development/python/Juniper}"
WORKTREES_ROOT="${JUNIPER_WORKTREE_SWEEP_ROOT:-${JUNIPER_BASE}/worktrees}"

# Map worktree dir name prefix -> the parent repo path that owns it.
# We use the parent repo to resolve "is this branch in origin/main".
declare -A REPO_OF=(
    [juniper-ml]="${JUNIPER_BASE}/juniper-ml"
    [juniper-canopy]="${JUNIPER_BASE}/juniper-canopy"
    [juniper-cascor]="${JUNIPER_BASE}/juniper-cascor"
    [juniper-data]="${JUNIPER_BASE}/juniper-data"
    [juniper-deploy]="${JUNIPER_BASE}/juniper-deploy"
    [juniper-cascor-worker]="${JUNIPER_BASE}/juniper-cascor-worker"
    [juniper-data-client]="${JUNIPER_BASE}/juniper-data-client"
    [juniper-cascor-client]="${JUNIPER_BASE}/juniper-cascor-client"
)

# Pre-fetch origin/main on each parent repo so the merged-status check is
# accurate. Background to parallelize; wait below before classifying.
for repo in "${REPO_OF[@]}"; do
    (git -C "$repo" fetch --quiet origin main 2>/dev/null || true) &
done
wait

printf "# %s\t%s\t%s\t%s\n" "STATUS" "REPO" "BRANCH" "WORKTREE"
printf "#"; printf -- '-%.0s' {1..130}; printf "\n"

for wt in "$WORKTREES_ROOT"/*/; do
    wt="${wt%/}"
    name=$(basename "$wt")
    # First two `--`-delimited tokens are the repo name (some repos have
    # `-` in their name, so this matches greedily on the longest known
    # repo prefix).
    repo_key=""
    for k in juniper-cascor-worker juniper-cascor-client juniper-data-client juniper-canopy juniper-cascor juniper-data juniper-deploy juniper-ml; do
        if [[ "$name" == "${k}--"* ]]; then
            repo_key="$k"
            break
        fi
    done
    if [[ -z "$repo_key" ]]; then
        printf "%s\t%s\t%s\t%s\n" "BROKEN" "?" "(no-repo-match)" "$name"
        continue
    fi
    repo="${REPO_OF[$repo_key]}"

    # Resolve the worktree's checked-out branch / detached HEAD.
    branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
    if [[ "$branch" == "HEAD" ]]; then
        # Detached. Substitute the short SHA so the user has something to grep.
        branch="(detached: $(git -C "$wt" rev-parse --short HEAD 2>/dev/null || echo '?'))"
    fi

    # Dirty? Plain --porcelain only: tracked modifications and untracked files
    # are dirt; GITIGNORED debris (caches, logs, decrypted secrets) is NOT --
    # every aged worktree accumulates it, and counting it made SAFE unreachable
    # in practice (2026-07-25 triage: 23/25 stale worktrees misclassified DIRTY).
    # The apply script still guards ignored content at removal time (default
    # skip; explicit --include-ignored to sweep it).
    # Force showUntrackedFiles=normal so a local/global "no" cannot hide
    # real untracked dirt and misclassify the worktree as SAFE.
    if [[ -n "$(git -C "$wt" -c status.showUntrackedFiles=normal status --porcelain 2>/dev/null)" ]]; then
        printf "%s\t%s\t%s\t%s\n" "DIRTY" "$repo_key" "$branch" "$name"
        continue
    fi

    # How many commits is the worktree's HEAD beyond origin/main?
    head_sha=$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")
    origin_main_sha=$(git -C "$repo" rev-parse origin/main 2>/dev/null || echo "")
    if [[ -z "$head_sha" || -z "$origin_main_sha" ]]; then
        printf "%s\t%s\t%s\t%s\n" "BROKEN" "$repo_key" "$branch" "$name"
        continue
    fi

    # Count commits in HEAD that are not in origin/main. Zero == fully merged
    # (or HEAD is on or behind origin/main, which is also safe).
    ahead=$(git -C "$wt" rev-list --count "origin/main..HEAD" 2>/dev/null || echo "?")

    if [[ "$ahead" == "0" ]]; then
        printf "%s\t%s\t%s\t%s\n" "SAFE" "$repo_key" "$branch" "$name"
    else
        printf "%s\t%s\t%s\t%s\n" "ACTIVE" "$repo_key" "$branch" "$name"
    fi
done
