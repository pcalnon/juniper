#!/usr/bin/env bash
# Watch a detached campaign's launch log: emit progress lines, exit on its terminal marker or pid death.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-26
# Status:      ad-hoc -- one-off (perf-lane re-measure watches, post-#587/#588/#589)
# Retire when: RETAINED (owner policy 2026-08-25 -- no retirement deadline). Previously: the
#              perf-lane re-measure evidence is posted (cascor#571 / #570); delete then.
# Related:     util/ad-hoc/2026-08-21_detach_campaign.bash (writes the <LOG>.pid this reads);
#              util/ad-hoc/2026-08-21_h2h_paired_campaign.bash (terminal marker `paired: done ->`).
#
# WHY THIS EXISTS
# A campaign's completion marker is SCRIPT-SPECIFIC (handoff 2026-08-25 section 4.1): the paired
# campaign ends with `paired: done ->`, the determinism campaign with `campaign: done`, run_suite
# with `[suite] wrote`. A watcher armed on the wrong marker times out silently while the campaign
# finished long ago -- and a watcher that greps only the success marker is silent through a
# pre-flight refusal or a crash. So the caller names BOTH the done regex and the fail regex, and
# the watcher also treats the recorded pid vanishing without a done marker as terminal (exit 1),
# so that silence can never be mistaken for "still running".
#
# Each emitted line is one event for a harness Monitor; nothing is emitted twice.
#
# Usage: 2026-08-26_watch_detached_launch.bash <LOG> <DONE_REGEX> <FAIL_REGEX> [PROGRESS_REGEX] [POLL_SECONDS]
#   LOG            the launch log written by 2026-08-21_detach_campaign.bash (reads <LOG>.pid beside it)
#   DONE_REGEX     extended regex whose first match means the campaign completed (exit 0)
#   FAIL_REGEX     extended regex whose first match means it failed / refused (exit 2)
#   PROGRESS_REGEX extended regex for lines worth emitting while it runs (default: DONE|FAIL only)
#   POLL_SECONDS   default 10
# Exit: 0 done marker seen; 1 pid gone without a done marker; 2 fail marker seen; 3 usage.
set -uo pipefail

LOG="${1:?usage: $0 <LOG> <DONE_REGEX> <FAIL_REGEX> [PROGRESS_REGEX] [POLL_SECONDS]}"
DONE_RE="${2:?usage: see header}"
FAIL_RE="${3:?usage: see header}"
PROG_RE="${4:-${DONE_RE}|${FAIL_RE}}"
POLL="${5:-10}"
PIDF="${LOG}.pid"

emitted=0
while true; do
    if [[ -f "${LOG}" ]]; then
        total=$(grep -cE "${PROG_RE}|${DONE_RE}|${FAIL_RE}" "${LOG}" 2>/dev/null || true)
        total="${total:-0}"
        if (( total > emitted )); then
            grep -E "${PROG_RE}|${DONE_RE}|${FAIL_RE}" "${LOG}" | sed -n "$((emitted + 1)),${total}p"
            emitted="${total}"
        fi
        if grep -qE "${DONE_RE}" "${LOG}" 2>/dev/null; then
            echo "TERMINAL done: $(grep -E "${DONE_RE}" "${LOG}" | tail -1)"
            exit 0
        fi
        if grep -qE "${FAIL_RE}" "${LOG}" 2>/dev/null; then
            echo "TERMINAL fail: $(grep -E "${FAIL_RE}" "${LOG}" | tail -1)"
            exit 2
        fi
    fi
    if [[ -f "${PIDF}" ]]; then
        pid=$(cat "${PIDF}" 2>/dev/null || true)
        if [[ -n "${pid}" ]] && ! kill -0 "${pid}" 2>/dev/null; then
            echo "TERMINAL pid ${pid} gone without a done marker; last line: $(tail -n 1 "${LOG}" 2>/dev/null)"
            exit 1
        fi
    fi
    sleep "${POLL}"
done
