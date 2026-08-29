#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  CI watch helper (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: Emit ONE line per PR the moment its checks reach a terminal state, and
#          exit when every watched PR has done so. Intended as a `Monitor` command.
#
#          It reports the three things that actually gate a merge here, because a
#          green rollup does NOT mean mergeable:
#            * fail=       failing checks
#            * threads=    UNRESOLVED, NON-OUTDATED review threads. CodeQL posts
#                          these; they block the merge while the check rollup reads
#                          entirely green. Measured twice on 2026-08-29:
#                          juniper-canopy#537 sat at 23 SUCCESS / 0 failures and was
#                          held by two `py/mixed-returns` threads; juniper-ml#1444 by
#                          five `File is not always closed` threads.
#            * mergeState= GitHub's own verdict (CLEAN / BLOCKED / BEHIND / UNKNOWN).
#                          BLOCKED does NOT mean behind -- BEHIND is its own value.
#
# ---------------------------------------------------------------------------
# THIS SCRIPT'S FIRST VERSION FAILED SILENTLY FOR 45 MINUTES. Read before editing.
#
#   It called `gh pr checks <n> --json name,bucket`. **`--json` does not exist on
#   `gh pr checks` in gh 2.46.0** (the pinned fleet version): it exits with
#   "unknown flag" AND status 0. The result was assigned to an empty string, the
#   loop hit `continue`, and the monitor emitted NOTHING for its entire 45-minute
#   window -- indistinguishable from "CI is still running".
#
#   The header of that version claimed "silence means still running and never
#   failed quietly." That claim was false for the one path that mattered: its own
#   tool call failing. A zero is not a result until you know the instrument could
#   have produced a non-zero.
#
#   Two consequences, both now enforced below:
#     1. Query via `gh pr view --json statusCheckRollup`, which 2.46.0 DOES
#        support, and verify support once at startup rather than per-round.
#     2. **Never `continue` past a failed probe.** Emit a PROBE-ERROR event. A
#        monitor whose failure mode is silence cannot be trusted to be watching.
# ---------------------------------------------------------------------------
#
# Usage:
#   util/ad-hoc/watch_prs_until_terminal.bash juniper-ml:1444 juniper-canopy:537
#
# Exit: 0 once all watched PRs are terminal, 1 on timeout, 2 on bad invocation.

set -uo pipefail

OWNER="${OWNER:-pcalnon}"
POLL_SECONDS="${POLL_SECONDS:-45}"
MAX_ROUNDS="${MAX_ROUNDS:-80}"
CONSECUTIVE_ERROR_LIMIT="${CONSECUTIVE_ERROR_LIMIT:-4}"

if [[ $# -eq 0 ]]; then
    echo "usage: $0 <repo>:<pr> [<repo>:<pr> ...]" >&2
    exit 2
fi

# Fail LOUDLY and immediately if the query form is unsupported, rather than
# discovering it as silence 45 minutes later.
probe_repo="${1%%:*}"
probe_pr="${1##*:}"
if ! gh pr view "$probe_pr" --repo "${OWNER}/${probe_repo}" --json statusCheckRollup >/dev/null 2>&1; then
    echo "PROBE-ERROR startup: 'gh pr view --json statusCheckRollup' failed for ${probe_repo}#${probe_pr}."
    echo "PROBE-ERROR check gh auth and that the PR exists. gh version: $(gh --version 2>&1 | head -1)"
    exit 2
fi

declare -A done_pr=()
errors=0

for ((round = 1; round <= MAX_ROUNDS; round++)); do
    for spec in "$@"; do
        repo="${spec%%:*}"
        pr="${spec##*:}"
        [[ -n "${done_pr[$spec]:-}" ]] && continue

        rollup="$(gh pr view "$pr" --repo "${OWNER}/${repo}" \
            --json statusCheckRollup,mergeStateStatus,state 2>&1)"
        if [[ $? -ne 0 || -z "$rollup" ]] || ! jq -e . >/dev/null 2>&1 <<<"$rollup"; then
            errors=$((errors + 1))
            echo "PROBE-ERROR ${repo}#${pr} round=${round} consecutive=${errors}: ${rollup:0:160}"
            if [[ "$errors" -ge "$CONSECUTIVE_ERROR_LIMIT" ]]; then
                echo "PROBE-ERROR giving up after ${errors} consecutive failures — NOT a CI verdict"
                exit 1
            fi
            continue
        fi
        errors=0

        # A merged/closed PR is terminal too; without this the watch hangs on it.
        pr_state="$(jq -r '.state' <<<"$rollup")"
        if [[ "$pr_state" != "OPEN" ]]; then
            echo "DONE ${repo}#${pr} state=${pr_state} (no longer open)"
            done_pr[$spec]=1
            continue
        fi

        pending="$(jq -r '[.statusCheckRollup[]? | select(.conclusion == null)] | length' <<<"$rollup")"
        [[ "$pending" != "0" ]] && continue

        failed="$(jq -r '[.statusCheckRollup[]? | select(.conclusion == "FAILURE" or .conclusion == "TIMED_OUT" or .conclusion == "CANCELLED" or .conclusion == "ACTION_REQUIRED")] | length' <<<"$rollup")"
        state="$(jq -r '.mergeStateStatus' <<<"$rollup")"

        gql="{repository(owner:\"${OWNER}\",name:\"${repo}\"){pullRequest(number:${pr}){reviewThreads(first:50){nodes{isResolved isOutdated}}}}}"
        threads="$(gh api graphql -f query="$gql" \
            -q '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false and .isOutdated == false)] | length' \
            2>/dev/null)" || threads="UNKNOWN(probe-failed)"

        echo "DONE ${repo}#${pr} fail=${failed} threads=${threads} mergeState=${state}"
        done_pr[$spec]=1
    done

    if [[ "${#done_pr[@]}" -ge $# ]]; then
        exit 0
    fi
    sleep "$POLL_SECONDS"
done

echo "TIMEOUT after $((MAX_ROUNDS * POLL_SECONDS))s; ${#done_pr[@]} of $# watched PRs reached terminal"
exit 1
