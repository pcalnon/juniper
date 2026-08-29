#!/usr/bin/env bash
# Drive the two armed juniper-ml PRs (#1330 then #1304) to merge, strictly in sequence.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-24
# Status:      RETIRED 2026-08-25 -- purpose complete, and superseded.
# Retired because: both PRs merged (#1330 as d29d8b594, #1304 as 77e55b76), and
#   2026-08-24_bot_pr_converge.py now DISCOVERS its targets instead of carrying a frozen
#   list, so it covers the juniper-ml leg too. Kept rather than deleted because the
#   sequential-within-a-repo reasoning below is the thing worth re-reading before the next
#   sweep, and because notes/ and PR bodies from 2026-08-24 name this path.
#
# What it produced: drove ml#1330 then ml#1304 to merge on 2026-08-24. #1304 is the
#   instructive one -- it reached GREEN 17/17 twice and went BEHIND both times before
#   merging on the third update, because juniper-ml's main takes a commit every ~13 min
#   against a ~10 min pipeline. That margin, not any defect in the PR, is what made this
#   script necessary.
#
# juniper-ml is the fast-moving repo: main takes commits every 5-10 min against a ~10 min
# pipeline, and the repo pairs strict_required_status_checks_policy=true with
# allow_update_branch=false. So an armed PR that goes BEHIND cannot self-clear, and two
# armed PRs in the SAME repo cannot both be up to date -- merging one re-BEHINDs the other.
# Hence: one at a time, update, wait for the armed auto-merge to fire, then the next.
#
# Never merges: it only issues update-branch on PRs already armed by an explicit owner
# decision, leaving GitHub's checks-gated auto-merge as the thing that actually merges.
# A gh failure is retried, never treated as an answer about the PR.
#
# Usage: bash util/ad-hoc/2026-08-24_ml_pr_converge.bash [deadline_minutes]
set -uo pipefail

REPO="pcalnon/juniper-ml"
PRS=(1330 1304)
DEADLINE_MIN="${1:-20}"
END=$(( SECONDS + DEADLINE_MIN * 60 ))

state_of() {  # echoes "STATE|MERGESTATE|ARMED", retrying transient gh failures
    local pr="$1" i out
    for i in 1 2 3; do
        out="$(gh pr view "$pr" --repo "$REPO" \
                 --json state,mergeStateStatus,autoMergeRequest \
                 --jq '"\(.state)|\(.mergeStateStatus)|\(.autoMergeRequest != null)"' 2>/dev/null)"
        if [ -n "$out" ]; then
            printf '%s' "$out"
            return 0
        fi
        sleep $(( 5 * i ))
    done
    printf 'TRANSIENT||'
}

for pr in "${PRS[@]}"; do
    while true; do
        if [ "$SECONDS" -ge "$END" ]; then
            echo "DEADLINE reached with #${pr} unresolved"
            exit 1
        fi
        IFS='|' read -r st ms armed <<< "$(state_of "$pr")"
        case "$st" in
            MERGED) echo "MERGED  #${pr}"; break ;;
            CLOSED) echo "CLOSED  #${pr} (not merged)"; break ;;
            TRANSIENT) echo "retry   #${pr} (gh unreachable)"; sleep 60; continue ;;
        esac
        if [ "$armed" != "true" ]; then
            echo "SKIP    #${pr} NOT ARMED -- refusing to touch"
            break
        fi
        if [ "$ms" = "BEHIND" ]; then
            echo "update  #${pr} (BEHIND)"
            gh api -X PUT "repos/${REPO}/pulls/${pr}/update-branch" \
                -H "Accept: application/vnd.github+json" >/dev/null 2>&1 \
                || echo "        update-branch call failed, will retry"
        fi
        sleep 60
    done
done
echo "ml leg done"
