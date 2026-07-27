#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Worktree Cleanup Script
# Author:       Paul Calnon
# Version:      1.1.0
# License:      MIT
############################################################################################################################################################
#
# Automates the V2 worktree cleanup procedure:
#   1. Pushes current worktree branch to remote
#   2. Creates a new worktree for session continuity
#   3. Creates a PR (or merges into parent branch + PR)
#   4. Removes the old worktree and cleans up branches
#   5. Syncs the continuity worktree to the latest origin/main
#
# The key safety property: a new worktree is created BEFORE the old one is removed,
# preventing the CWD-trap bug where the shell ends up in a non-existent directory.
#
# Usage:
#   scripts/worktree_cleanup.bash \
#     --old-worktree /path/to/old/worktree \
#     --old-branch worktree-branch-name \
#     [--parent-branch main] \
#     [--new-worktree /path/to/new/worktree] \
#     [--new-branch new-branch-name] \
#     [--skip-pr] \
#     [--skip-remote-delete] \
#     [--dry-run]
#
############################################################################################################################################################

set -euo pipefail

############################################################################################################################################################
# Constants
############################################################################################################################################################

# Derive MAIN_REPO from this script's location (util/worktree_cleanup.bash
# lives at <MAIN_REPO>/util/, so MAIN_REPO is one directory up). Allow an
# environment override for test fixtures and unusual layouts.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
MAIN_REPO_DEFAULT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly MAIN_REPO="${JUNIPER_ML_MAIN_REPO:-${MAIN_REPO_DEFAULT}}"
readonly WORKTREE_BASE="${MAIN_REPO}/.claude/worktrees"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_NAME
readonly TRUE=0
readonly FALSE=1

############################################################################################################################################################
# Globals
############################################################################################################################################################

OLD_WORKTREE=""
OLD_BRANCH=""
PARENT_BRANCH="main"
NEW_WORKTREE=""
NEW_BRANCH=""
SKIP_PR="${FALSE}"
SKIP_REMOTE_DELETE="${FALSE}"
DRY_RUN="${FALSE}"

############################################################################################################################################################
# Logging
############################################################################################################################################################

log_info() {
    echo "[INFO]  ${SCRIPT_NAME}: ${*}" >&2
}

log_warn() {
    echo "[WARN]  ${SCRIPT_NAME}: ${*}" >&2
}

log_error() {
    echo "[ERROR] ${SCRIPT_NAME}: ${*}" >&2
}

log_step() {
    echo "" >&2
    echo "======================================================================" >&2
    echo "  ${*}" >&2
    echo "======================================================================" >&2
}

############################################################################################################################################################
# Usage
############################################################################################################################################################

usage() {
    cat <<'USAGE_EOF'
Usage: worktree_cleanup.bash [OPTIONS]

Required:
  --old-worktree PATH      Path to the worktree being cleaned up
  --old-branch NAME        Branch name of the old worktree

Optional:
  --parent-branch NAME     Parent branch (default: main)
  --new-worktree PATH      Path for the new worktree (auto-generated if omitted)
  --new-branch NAME        Branch name for the new worktree (auto-generated if omitted)
  --skip-pr                Skip PR creation
  --skip-remote-delete     Skip remote branch deletion (useful when PR is open)
  --dry-run                Print commands without executing

Output:
  On success, prints the new worktree path to stdout (for use with cd).
  All logging goes to stderr.
USAGE_EOF
    exit "${1:-1}"
}

############################################################################################################################################################
# Argument Parsing
############################################################################################################################################################

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "${1}" in
            --old-worktree)
                OLD_WORKTREE="${2}"
                shift 2
                ;;
            --old-branch)
                OLD_BRANCH="${2}"
                shift 2
                ;;
            --parent-branch)
                PARENT_BRANCH="${2}"
                shift 2
                ;;
            --new-worktree)
                NEW_WORKTREE="${2}"
                shift 2
                ;;
            --new-branch)
                NEW_BRANCH="${2}"
                shift 2
                ;;
            --skip-pr)
                SKIP_PR="${TRUE}"
                shift
                ;;
            --skip-remote-delete)
                SKIP_REMOTE_DELETE="${TRUE}"
                shift
                ;;
            --dry-run)
                DRY_RUN="${TRUE}"
                shift
                ;;
            -h|--help)
                usage 0
                ;;
            *)
                log_error "Unknown argument: ${1}"
                usage 1
                ;;
        esac
    done
}

############################################################################################################################################################
# Validation
############################################################################################################################################################

validate_args() {
    local errors=0

    if [[ -z "${OLD_WORKTREE}" ]]; then
        log_error "--old-worktree is required"
        errors=$((errors + 1))
    elif [[ ! -d "${OLD_WORKTREE}" ]]; then
        log_error "Old worktree directory does not exist: ${OLD_WORKTREE}"
        errors=$((errors + 1))
    fi

    if [[ -z "${OLD_BRANCH}" ]]; then
        log_error "--old-branch is required"
        errors=$((errors + 1))
    fi

    if [[ ! -d "${MAIN_REPO}" ]]; then
        log_error "Main repo directory does not exist: ${MAIN_REPO}"
        errors=$((errors + 1))
    fi

    if (( errors > 0 )); then
        usage 1
    fi
}

############################################################################################################################################################
# Helper: Execute or dry-run a command
############################################################################################################################################################

run_cmd() {
    if [[ "${DRY_RUN}" == "${TRUE}" ]]; then
        echo "[DRY-RUN] ${*}" >&2
    else
        log_info "Running: ${*}"
        "${@}"
    fi
}

############################################################################################################################################################
# Phase 1: Save & Push
############################################################################################################################################################

phase_1_save_and_push() {
    log_step "Phase 1: Save & Push Current Work"

    if [[ "${DRY_RUN}" == "${TRUE}" ]]; then
        echo "[DRY-RUN] git -C ${OLD_WORKTREE} status --porcelain" >&2
        echo "[DRY-RUN] git -C ${OLD_WORKTREE} push origin ${OLD_BRANCH}" >&2
        log_info "Old worktree is clean (dry-run — skipped check)"
        return 0
    fi

    # Check if old worktree is clean
    local status
    status="$(git -C "${OLD_WORKTREE}" status --porcelain)"
    if [[ -n "${status}" ]]; then
        log_warn "Old worktree has uncommitted changes:"
        echo "${status}" >&2
        log_error "Commit or stash changes before running cleanup"
        exit 1
    fi
    log_info "Old worktree is clean"

    # Check if branch has a remote tracking branch
    local remote_branch
    remote_branch="$(git -C "${OLD_WORKTREE}" rev-parse --abbrev-ref "${OLD_BRANCH}@{upstream}" 2>/dev/null || echo "")"

    if [[ -n "${remote_branch}" ]]; then
        # Check if we need to push
        local ahead
        ahead="$(git -C "${OLD_WORKTREE}" rev-list --count "${remote_branch}..${OLD_BRANCH}" 2>/dev/null || echo "0")"
        if (( ahead > 0 )); then
            log_info "Pushing ${ahead} commit(s) to remote"
            run_cmd git -C "${OLD_WORKTREE}" push origin "${OLD_BRANCH}"
        else
            log_info "Branch is up to date with remote"
        fi
    else
        log_info "No remote tracking branch — pushing to origin"
        run_cmd git -C "${OLD_WORKTREE}" push -u origin "${OLD_BRANCH}"
    fi
}

############################################################################################################################################################
# Phase 2: Create New Worktree
############################################################################################################################################################

generate_worktree_name() {
    # Use Claude Code's worktree naming if not provided
    if [[ -z "${NEW_BRANCH}" ]]; then
        local random_suffix
        random_suffix="$(head -c 4 /dev/urandom | od -An -tx1 | tr -d ' \n')"
        NEW_BRANCH="worktree-cleanup-${random_suffix}"
    fi

    if [[ -z "${NEW_WORKTREE}" ]]; then
        local safe_branch
        safe_branch="$(echo "${NEW_BRANCH}" | sed 's|worktree-||; s|/|--|g')"
        NEW_WORKTREE="${WORKTREE_BASE}/${safe_branch}"
    fi
}

phase_2_create_new_worktree() {
    log_step "Phase 2: Create New Worktree for Session Continuity"

    generate_worktree_name

    log_info "New worktree: ${NEW_WORKTREE}"
    log_info "New branch:   ${NEW_BRANCH}"

    # Fetch latest
    run_cmd git -C "${MAIN_REPO}" fetch origin

    # Create new worktree based on origin/main
    if [[ -d "${NEW_WORKTREE}" ]]; then
        log_error "New worktree directory already exists: ${NEW_WORKTREE}"
        exit 1
    fi

    run_cmd git -C "${MAIN_REPO}" worktree add "${NEW_WORKTREE}" -b "${NEW_BRANCH}" origin/main

    # Verify
    if [[ "${DRY_RUN}" != "${TRUE}" ]]; then
        if [[ ! -d "${NEW_WORKTREE}" ]]; then
            log_error "Failed to create new worktree at: ${NEW_WORKTREE}"
            exit 1
        fi
        log_info "New worktree created successfully"
        log_info "CWD should now be changed to: ${NEW_WORKTREE}"
    fi
}

############################################################################################################################################################
# Phase 3: Merge & PR
############################################################################################################################################################

phase_3_merge_and_pr() {
    log_step "Phase 3: Merge & Pull Request"

    if [[ "${SKIP_PR}" == "${TRUE}" ]]; then
        log_info "Skipping PR creation (--skip-pr)"
        return 0
    fi

    if [[ "${DRY_RUN}" == "${TRUE}" ]]; then
        log_info "Would check commits ahead and create PR"
        if [[ "${PARENT_BRANCH}" == "main" ]]; then
            echo "[DRY-RUN] gh pr create --repo pcalnon/juniper-ml --base main --head ${OLD_BRANCH}" >&2
        else
            echo "[DRY-RUN] git -C ${MAIN_REPO} checkout ${PARENT_BRANCH}" >&2
            echo "[DRY-RUN] git -C ${MAIN_REPO} merge ${OLD_BRANCH}" >&2
            echo "[DRY-RUN] git -C ${MAIN_REPO} push origin ${PARENT_BRANCH}" >&2
            echo "[DRY-RUN] gh pr create --repo pcalnon/juniper-ml --base main --head ${PARENT_BRANCH}" >&2
        fi
        return 0
    fi

    # Check if old branch has any commits ahead of parent
    local ahead
    ahead="$(git -C "${MAIN_REPO}" rev-list --count "origin/${PARENT_BRANCH}..origin/${OLD_BRANCH}" 2>/dev/null || echo "0")"

    if (( ahead == 0 )); then
        log_warn "Branch '${OLD_BRANCH}' has no commits ahead of '${PARENT_BRANCH}' — skipping PR"
        return 0
    fi

    log_info "Branch '${OLD_BRANCH}' is ${ahead} commit(s) ahead of '${PARENT_BRANCH}'"

    if [[ "${PARENT_BRANCH}" == "main" ]]; then
        # Parent is main: create PR directly
        log_info "Creating PR: ${OLD_BRANCH} → main"

        # Check if PR already exists
        local existing_pr
        existing_pr="$(gh pr list --repo pcalnon/juniper-ml --head "${OLD_BRANCH}" --state open --json number --jq '.[0].number' 2>/dev/null || echo "")"

        if [[ -n "${existing_pr}" ]]; then
            log_info "PR #${existing_pr} already exists for branch '${OLD_BRANCH}'"
        else
            run_cmd gh pr create \
                --repo pcalnon/juniper-ml \
                --base main \
                --head "${OLD_BRANCH}" \
                --title "Merge ${OLD_BRANCH} into main" \
                --body "Automated PR created by worktree cleanup script."
        fi
    else
        # Parent is not main: merge into parent, then PR parent → main
        log_info "Merging ${OLD_BRANCH} into ${PARENT_BRANCH}"

        run_cmd git -C "${MAIN_REPO}" checkout "${PARENT_BRANCH}"
        run_cmd git -C "${MAIN_REPO}" pull origin "${PARENT_BRANCH}"
        run_cmd git -C "${MAIN_REPO}" merge "${OLD_BRANCH}"
        run_cmd git -C "${MAIN_REPO}" push origin "${PARENT_BRANCH}"

        log_info "Creating PR: ${PARENT_BRANCH} → main"

        local existing_pr
        existing_pr="$(gh pr list --repo pcalnon/juniper-ml --head "${PARENT_BRANCH}" --state open --json number --jq '.[0].number' 2>/dev/null || echo "")"

        if [[ -n "${existing_pr}" ]]; then
            log_info "PR #${existing_pr} already exists for branch '${PARENT_BRANCH}'"
        else
            run_cmd gh pr create \
                --repo pcalnon/juniper-ml \
                --base main \
                --head "${PARENT_BRANCH}" \
                --title "Merge ${PARENT_BRANCH} into main" \
                --body "Automated PR created by worktree cleanup script."
        fi
    fi
}

############################################################################################################################################################
# Phase 4: Cleanup Old Worktree
############################################################################################################################################################

phase_4_cleanup() {
    log_step "Phase 4: Remove Old Worktree"

    # Remove old worktree
    log_info "Removing worktree: ${OLD_WORKTREE}"
    run_cmd git -C "${MAIN_REPO}" worktree remove "${OLD_WORKTREE}" || {
        log_warn "Standard removal failed, trying --force"
        run_cmd git -C "${MAIN_REPO}" worktree remove --force "${OLD_WORKTREE}"
    }

    # Delete local branch
    log_info "Deleting local branch: ${OLD_BRANCH}"
    run_cmd git -C "${MAIN_REPO}" branch -d "${OLD_BRANCH}" || {
        log_warn "Standard delete failed (branch not fully merged), trying -D"
        run_cmd git -C "${MAIN_REPO}" branch -D "${OLD_BRANCH}"
    }

    # Delete remote branch (unless skipped or PR is open).
    # Fail CLOSED on an indeterminate open-PR query: treating gh/auth/network
    # failure as "0 open PRs" would delete the remote head under a live PR
    # (backup branch loss / broken PR head). Prefer a warn-and-skip over a
    # destructive push --delete when we cannot prove it is safe.
    if [[ "${SKIP_REMOTE_DELETE}" == "${TRUE}" ]]; then
        log_info "Skipping remote branch deletion (--skip-remote-delete)"
    elif [[ "${DRY_RUN}" == "${TRUE}" ]]; then
        echo "[DRY-RUN] git -C ${MAIN_REPO} push origin --delete ${OLD_BRANCH}" >&2
    else
        local open_prs=""
        local gh_status=0
        open_prs="$(gh pr list --repo pcalnon/juniper-ml --head "${OLD_BRANCH}" --state open --json number --jq 'length' 2>/dev/null)" || gh_status=$?

        if (( gh_status != 0 )); then
            log_warn "Could not query open PRs for branch '${OLD_BRANCH}' (gh exit ${gh_status}) — skipping remote branch deletion"
        elif [[ ! "${open_prs}" =~ ^[0-9]+$ ]]; then
            log_warn "Unexpected open-PR query result for branch '${OLD_BRANCH}' — skipping remote branch deletion"
        elif (( open_prs > 0 )); then
            log_warn "PR is open for branch '${OLD_BRANCH}' — skipping remote branch deletion"
        else
            log_info "Deleting remote branch: ${OLD_BRANCH}"
            run_cmd git -C "${MAIN_REPO}" push origin --delete "${OLD_BRANCH}" 2>/dev/null || {
                log_warn "Remote branch '${OLD_BRANCH}' may not exist on remote"
            }
        fi
    fi

    # Prune
    run_cmd git -C "${MAIN_REPO}" worktree prune
}

############################################################################################################################################################
# Phase 5: Verify
############################################################################################################################################################

phase_5_verify() {
    log_step "Phase 5: Verification"

    if [[ "${DRY_RUN}" == "${TRUE}" ]]; then
        log_info "[DRY-RUN] Would verify: worktree list, branch list, status"
        return 0
    fi

    log_info "Worktree list:"
    git -C "${MAIN_REPO}" worktree list >&2

    log_info "Local branches:"
    git -C "${MAIN_REPO}" branch >&2

    log_info "New worktree status:"
    git -C "${NEW_WORKTREE}" status >&2

    log_info "Cleanup complete!"
}

############################################################################################################################################################
# Phase 6: Sync to Latest main
############################################################################################################################################################

phase_6_sync_main() {
    log_step "Phase 6: Sync to Latest main"

    # The script always leaves a fresh continuity worktree in place (Case A of
    # the procedure), so fast-forward that worktree to the latest origin/main.
    # It cannot check out main (that branch is checked out in MAIN_REPO, and a
    # branch can live in only one worktree), so it syncs the new worktree's
    # branch in place. Best-effort: a branch that cannot fast-forward is
    # warned-and-skipped, never fatal to the cleanup.
    run_cmd git -C "${NEW_WORKTREE}" fetch --all
    run_cmd git -C "${NEW_WORKTREE}" pull --ff-only origin main || {
        log_warn "Could not fast-forward '${NEW_BRANCH}' to origin/main — skipping"
    }
}

############################################################################################################################################################
# Phase 7: Restore MAIN_REPO Checkout to main
############################################################################################################################################################

phase_7_restore_main_checkout() {
    log_step "Phase 7: Restore MAIN_REPO checkout to up-to-date main"

    # The primary checkout can be left sitting on a stale non-main branch by
    # release or hotfix work (the F-6 stale-checkout class; e.g. the main
    # checkout stranded on release/juniper-service-core-v0.5.0, 2026-07-18).
    # After every merged-PR cleanup, return it to an up-to-date main.
    # Safety gates: never touch a dirty tree, and treat a main branch that is
    # checked out in another worktree as a warn-and-skip, never fatal.
    if [[ "${DRY_RUN}" == "${TRUE}" ]]; then
        echo "[DRY-RUN] git -C ${MAIN_REPO} checkout main  (only if tree clean and not already on main)" >&2
        echo "[DRY-RUN] git -C ${MAIN_REPO} pull --ff-only origin main" >&2
        return 0
    fi

    local current_branch dirty
    current_branch="$(git -C "${MAIN_REPO}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
    dirty="$(git -C "${MAIN_REPO}" status --porcelain 2>/dev/null | head -1)"

    if [[ -n "${dirty}" ]]; then
        log_warn "MAIN_REPO tree is dirty — leaving checkout on '${current_branch}' (restore to main manually)"
        return 0
    fi
    if [[ "${current_branch}" != "main" ]]; then
        log_info "MAIN_REPO is on '${current_branch}' — checking out main"
        run_cmd git -C "${MAIN_REPO}" checkout main || {
            log_warn "Could not check out main in MAIN_REPO (checked out in another worktree?) — skipping"
            return 0
        }
    fi
    run_cmd git -C "${MAIN_REPO}" pull --ff-only origin main || {
        log_warn "Could not fast-forward MAIN_REPO main — skipping"
    }
}

############################################################################################################################################################
# Main
############################################################################################################################################################

main() {
    parse_args "${@}"
    validate_args

    log_info "Worktree Cleanup V2"
    log_info "Old worktree:   ${OLD_WORKTREE}"
    log_info "Old branch:     ${OLD_BRANCH}"
    log_info "Parent branch:  ${PARENT_BRANCH}"

    phase_1_save_and_push
    phase_2_create_new_worktree
    phase_3_merge_and_pr
    phase_4_cleanup
    phase_5_verify
    phase_6_sync_main
    phase_7_restore_main_checkout

    # Output the new worktree path to stdout (for the caller to cd into)
    echo "${NEW_WORKTREE}"
}

main "${@}"
