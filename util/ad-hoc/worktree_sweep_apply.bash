#!/usr/bin/env bash
# File:    worktree_sweep_apply.bash
# Author:  Paul Calnon
# Created: 2026-05-31
# Purpose: Remove SAFE-classified stale worktrees from
#          /home/pcalnon/Development/python/Juniper/worktrees/. SAFE means:
#          (a) clean working tree (no uncommitted changes), and
#          (b) every commit on the worktree's branch is either:
#                - in origin/main directly (rev-list ahead == 0), OR
#                - the source side of a MERGED pull request on GitHub
#                  (i.e., squash-merged — the worktree's commit hash isn't
#                  in main's linear history but the work is already shipped).
#          For each SAFE worktree the script:
#              1. git -C <parent-repo> worktree remove <wt>
#              2. git -C <parent-repo> branch -D <branch>
#              3. git -C <parent-repo> worktree prune  (after the batch)
#          DIRTY / unresolvable rows are skipped with a warning.
#
# Run with --dry-run to print what would happen without acting.
# Default is to apply.
#
# Ignored-content guard: by default a worktree containing GITIGNORED files
# (caches, logs, decrypted secrets) is skipped even when otherwise SAFE --
# ignored content is deleted with the worktree and may be precious (the
# decrypted-secrets class). Pass --include-ignored to sweep such worktrees
# anyway; tracked/untracked dirt is ALWAYS a hard skip regardless.
# Both porcelain probes force -unormal so status.showUntrackedFiles=no cannot
# blind the dirt / ignored guards (git worktree remove succeeds on ignored-
# only debris; a false-negative here is silent secret deletion).
# Convention: ad-hoc one-shot script, lives under util/ad-hoc/ per
# CLAUDE.md "Script placement". Companion to worktree_sweep_survey.bash.

set -euo pipefail

DRY_RUN=0
INCLUDE_IGNORED=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --include-ignored) INCLUDE_IGNORED=1 ;;
        *) echo "unknown flag: $arg" >&2; exit 2 ;;
    esac
done

JUNIPER_BASE="${JUNIPER_WORKTREE_SWEEP_REPO_BASE:-/home/pcalnon/Development/python/Juniper}"
WORKTREES_ROOT="${JUNIPER_WORKTREE_SWEEP_ROOT:-${JUNIPER_BASE}/worktrees}"

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

trim_field() {
    local value="${1:-}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

remove_worktree() {
    local wt="$1" branch="$2" repo_key="$3"
    local repo="${REPO_OF[$repo_key]}"
    if (( DRY_RUN )); then
        echo "DRY: git -C $repo_key worktree remove $wt && branch -D $branch"
        return
    fi
    # Run from /tmp to avoid the CWD-trap if the caller is inside the wt.
    pushd /tmp >/dev/null
    # Force untracked visibility: git worktree remove consults
    # status.showUntrackedFiles, and with that set to "no" it silently
    # deletes worktrees that contain untracked WIP (git 2.43 observed).
    if git -C "$repo" -c status.showUntrackedFiles=normal worktree remove "$wt" 2>/dev/null; then
        if git -C "$repo" show-ref --verify --quiet "refs/heads/$branch"; then
            git -C "$repo" branch -D "$branch" >/dev/null 2>&1 || \
                echo "    warning: branch -D $branch failed (not a fast-forward?)"
        fi
        echo "removed: $repo_key / $branch"
    else
        echo "skipped (remove failed): $repo_key / $branch / $wt"
    fi
    popd >/dev/null
}

# Iterate the survey output. Survey is pre-fetched; this script acts only
# on SAFE rows so DIRTY / ACTIVE / BROKEN worktrees cannot be removed by
# accidentally piping the full survey output.
#
# Input format (tab-separated): STATUS<TAB>REPO_KEY<TAB>BRANCH<TAB>WORKTREE_NAME
# (matches worktree_sweep_survey.bash's 4-column output exactly.)
while IFS=$'\t' read -r status repo_key branch wt_name _extra; do
    status=$(trim_field "$status")
    repo_key=$(trim_field "$repo_key")
    branch=$(trim_field "$branch")
    wt_name=$(trim_field "$wt_name")

    [[ -z "${status:-}" ]] && continue
    [[ "$status" =~ ^# ]] && continue   # comment / header
    if [[ "$status" != "SAFE" ]]; then
        echo "skipped (status $status not safe): $wt_name"
        continue
    fi
    if [[ -z "${REPO_OF[$repo_key]+x}" ]]; then
        echo "skipped (unknown repo): $repo_key / $wt_name"
        continue
    fi
    wt="$WORKTREES_ROOT/$wt_name"
    if [[ ! -d "$wt" ]]; then
        echo "skipped (missing dir): $wt_name"
        continue
    fi
    if ! git -C "$wt" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "skipped (not a git worktree): $wt_name"
        continue
    fi
    current_branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || true)
    if [[ -z "$current_branch" ]]; then
        echo "skipped (not on a branch): $wt_name"
        continue
    fi
    if [[ "$current_branch" != "$branch" ]]; then
        echo "skipped (branch mismatch: row=$branch current=$current_branch): $wt_name"
        continue
    fi
    # -c status.showUntrackedFiles=normal: local/global "no" blinds both
    # plain porcelain and --ignored (empty output even when files exist),
    # which would let us call worktree remove on precious untracked/ignored
    # debris. Override at the call site so the dirty + ignored guards stay
    # honest regardless of caller config.
    if [[ -n "$(git -C "$wt" -c status.showUntrackedFiles=normal status --porcelain 2>/dev/null)" ]]; then
        echo "skipped (no longer safe; dirty): $wt_name"
        continue
    fi
    if (( ! INCLUDE_IGNORED )) && [[ -n "$(git -C "$wt" -c status.showUntrackedFiles=normal status --porcelain --ignored 2>/dev/null)" ]]; then
        echo "skipped (ignored files present; rerun with --include-ignored to sweep them): $wt_name"
        continue
    fi
    ahead=$(git -C "$wt" rev-list --count "origin/main..HEAD" 2>/dev/null || echo "?")
    if [[ "$ahead" != "0" ]]; then
        echo "skipped (no longer safe; ahead=$ahead): $wt_name"
        continue
    fi
    remove_worktree "$wt" "$branch" "$repo_key"
done

# Prune all repos once at the end so each repo's worktree metadata is clean.
for repo in "${REPO_OF[@]}"; do
    (( DRY_RUN )) || git -C "$repo" worktree prune >/dev/null 2>&1 || true
done
echo "done"
