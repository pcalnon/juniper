#!/usr/bin/env bash
# Block until a PR leaves the OPEN state, then print its final disposition.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-24
# Status:      RETIRED 2026-08-25 -- purpose complete.
# Retired because: ml#1316 merged (2a914f7bc). A single-PR wait is now covered by
#   2026-08-24_bot_pr_census.py for surveys and by util/wait_for_checks.py for the
#   authoritative required-context read.
#
# What it produced: confirmed ml#1316 MERGED after util/safe_merge.py REFUSED it. The
#   refusal is the lesson -- safe_merge exits 0 when it refuses, so its exit code says
#   nothing; only the "MERGED #<N> at <sha>" line does. See
#   notes/ and the memory entry safe-merge-exits-zero-without-merging.
#
# Why this exists: `util/safe_merge.py` REFUSES on a repo whose main outruns its CI
# (strict_required_status_checks_policy=true + a ~10 min pipeline + commits every
# 5-10 min), and it disarms its own auto-merge net on refusal. The correct fallback is
# GitHub's NATIVE auto-merge, which moves the head server-side instead of racing it from
# a client. This script only WATCHES that outcome -- it never merges, arms, or pushes.
#
# Usage: bash util/ad-hoc/2026-08-24_await_pr_merge.bash <pr> [repo] [interval_seconds]
set -uo pipefail

PR="${1:?usage: $0 <pr> [repo] [interval]}"
REPO="${2:-juniper-ml}"
INTERVAL="${3:-60}"
OWNER="pcalnon"

while true; do
    state="$(gh pr view "$PR" --repo "${OWNER}/${REPO}" --json state --jq .state 2>/dev/null || true)"
    if [ -z "$state" ]; then
        # transient gh/network failure must not kill the watch
        sleep "$INTERVAL"
        continue
    fi
    if [ "$state" != "OPEN" ]; then
        break
    fi
    sleep "$INTERVAL"
done

gh pr view "$PR" --repo "${OWNER}/${REPO}" \
    --json state,mergedAt,mergeCommit \
    --jq '"FINAL state=\(.state) mergedAt=\(.mergedAt) commit=\(.mergeCommit.oid[0:9] // "none")"'
