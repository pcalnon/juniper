#!/usr/bin/env bash
# Block until a named workflow finishes for a given SHA, then print its conclusion.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-24
# Status:      RETIRED 2026-08-25 -- purpose complete.
# Retire when: n/a. Kept for the reasoning below, which outlives the run.
#
# What it produced: confirmed `Post-Merge Main Verification @ 2a914f7b: success` for
#   ml#1316 -- the run that proves an `Allow-Symbol-Loss:` waiver actually SURVIVED the
#   squash. That is the whole reason this watch existed: the waiver passes the PR screen
#   from any commit in the range, but main-verify re-runs the screens against main, so a
#   trailer lost in the squash reddens main THERE and nowhere earlier. #1316's trailer
#   landed at line 62 of the squash commit, verified explicitly rather than assumed.
#
# Why this exists: a waived symbol-loss finding only proves itself AFTER the squash --
# `Post-Merge Main Verification` re-runs the sequence-safety screens against main, and a
# trailer that failed to survive the squash reddens main there and nowhere earlier
# (the recurring class in notes/...MAIN-VERIFY-RED...). Read-only: never merges or pushes.
#
# Usage: bash util/ad-hoc/2026-08-24_await_main_verify.bash <sha> [workflow-name] [repo] [interval]
set -uo pipefail

SHA="${1:?usage: $0 <sha> [workflow-name] [repo] [interval]}"
WF="${2:-Post-Merge Main Verification}"
REPO="${3:-juniper-ml}"
INTERVAL="${4:-45}"
OWNER="pcalnon"

while true; do
    row="$(gh run list --repo "${OWNER}/${REPO}" --limit 30 \
             --json name,conclusion,status,headSha \
             --jq ".[] | select(.headSha==\"${SHA}\" and .name==\"${WF}\") | \"\(.status)|\(.conclusion // \"\")\"" \
           2>/dev/null | head -1 || true)"
    if [ -z "$row" ]; then
        sleep "$INTERVAL"          # not registered yet, or a transient gh failure
        continue
    fi
    status="${row%%|*}"
    concl="${row##*|}"
    if [ "$status" = "completed" ]; then
        echo "${WF} @ ${SHA:0:8}: ${concl}"
        [ "$concl" = "success" ] && exit 0
        exit 1
    fi
    sleep "$INTERVAL"
done
