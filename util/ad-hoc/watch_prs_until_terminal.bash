#!/usr/bin/env bash
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  CI watch helper (ad-hoc)
# Author:       Paul Calnon
# License:      MIT
#
# Purpose: A `Monitor`-shaped wrapper around `util/wait_for_checks.py`: emit ONE
#          line per PR when it reaches a terminal state, exit when all have.
#
#          It adds exactly ONE thing the shared waiter does not cover, and that is
#          the only reason it exists: **unresolved review threads**. A PR can sit at
#          all-required-green and still be unmergeable because CodeQL posted a
#          review thread — measured three times on 2026-08-29 (canopy#537 at 23
#          SUCCESS / 0 failures held by two `py/mixed-returns`; ml#1444 by five
#          `File is not always closed`; ml#1480 by one `py/empty-except`). So each
#          line reports fail=, threads= and mergeState= together.
#
# ---------------------------------------------------------------------------
# DO NOT REPLACE THE wait_for_checks.py CALL WITH A HAND-ROLLED POLL. Two versions
# of this script already did, and each hit a documented trap within the hour:
#
#   v1 called `gh pr checks --json`, a flag gh 2.46.0 does not have. It exits
#   "unknown flag" with status 0, so the loop saw an empty result, hit `continue`,
#   and emitted NOTHING for 45 minutes — indistinguishable from "still running".
#
#   v2 polled `gh pr view --json statusCheckRollup` and treated "no entry has a
#   null conclusion" as terminal. **The rollup GROWS as jobs start**: it held 7
#   entries mid-run where the finished suite had 26, so a lull between waves reads
#   as completion. It declared ml#1480 terminal while `Analyze (python)` was still
#   QUEUED — the exact trap `wait_for_checks.py --anchor observed` exists to
#   reproduce, and which its default (anchor on the ruleset's REQUIRED contexts)
#   prevents.
#
# The general rule both violated: **terminal must be defined POSITIVELY, against a
# closed set.** "Everything I can see is done" is not "it is done", because what
# you can see is open-ended. Anchor on the required contexts; let the shared waiter
# do it.
# ---------------------------------------------------------------------------
#
# Usage:
#   util/ad-hoc/watch_prs_until_terminal.bash juniper-ml:1480 juniper-canopy:537
#
# Env: OWNER (default pcalnon), PER_PR_TIMEOUT (default 2400 seconds).
#
# Exit: 0 once all watched PRs are terminal, 1 if any timed out, 2 on bad
#       invocation or a broken probe.

set -uo pipefail

OWNER="${OWNER:-pcalnon}"
PER_PR_TIMEOUT="${PER_PR_TIMEOUT:-2400}"

_HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAITER="${_HERE}/../wait_for_checks.py"

if [[ $# -eq 0 ]]; then
    echo "usage: $0 <repo>:<pr> [<repo>:<pr> ...]" >&2
    exit 2
fi
if [[ ! -f "$WAITER" ]]; then
    echo "PROBE-ERROR: shared waiter not found at ${WAITER}" >&2
    echo "PROBE-ERROR: run this from a juniper-ml checkout; do NOT substitute a hand-rolled poll." >&2
    exit 2
fi

rc=0

for spec in "$@"; do
    repo="${spec%%:*}"
    pr="${spec##*:}"

    out="$(python3 "$WAITER" --pr "$pr" --repo "$repo" --owner "$OWNER" \
        --json --timeout "$PER_PR_TIMEOUT" 2>&1)"
    waiter_rc=$?

    if ! jq -e . >/dev/null 2>&1 <<<"$out"; then
        # Exit 3 is the waiter's own hard-error code; anything unparseable is a
        # broken probe and must be LOUD, never silence.
        echo "PROBE-ERROR ${repo}#${pr} waiter rc=${waiter_rc}, unparseable output: ${out:0:200}"
        rc=2
        continue
    fi

    status="$(jq -r '.status' <<<"$out")"
    failed="$(jq -r '.failed | length' <<<"$out")"
    state="$(jq -r '.merge_state // "?"' <<<"$out")"
    prstate="$(jq -r '.pr_state // "?"' <<<"$out")"

    if [[ "$prstate" != "OPEN" ]]; then
        echo "DONE ${repo}#${pr} state=${prstate} (no longer open)"
        continue
    fi

    # The bit the shared waiter does not do.
    gql="{repository(owner:\"${OWNER}\",name:\"${repo}\"){pullRequest(number:${pr}){reviewThreads(first:50){nodes{isResolved isOutdated}}}}}"
    threads="$(gh api graphql -f query="$gql" \
        -q '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false and .isOutdated == false)] | length' \
        2>/dev/null)" || threads="UNKNOWN(probe-failed)"

    if [[ "$status" == "timeout" ]]; then
        running="$(jq -r '(.running // []) | join(", ")' <<<"$out")"
        absent="$(jq -r '(.absent // []) | join(", ")' <<<"$out")"
        echo "TIMEOUT ${repo}#${pr} after ${PER_PR_TIMEOUT}s — NOT a verdict. running=[${running}] absent=[${absent}]"
        rc=1
        continue
    fi

    echo "DONE ${repo}#${pr} status=${status} fail=${failed} threads=${threads} mergeState=${state}"
done

exit "$rc"
