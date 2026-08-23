#!/usr/bin/env bash
# Launch a long campaign fully detached, so it outlives the shell that started it.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-21
# Status:      ad-hoc -- one-off (residual wall gap, cap-64 campaign)
# Retire when: the residual wall-gap evidence note is merged; delete then.
#
# A cap-64 paired campaign runs ~10 hours. Anything supervising it -- an agent session, a
# background worker lease, an ssh connection -- is shorter-lived than that, and when the supervisor
# dies a normally-backgrounded job dies with it: the campaign's children are in the supervisor's
# process group and take the same signal. Ten hours of compute then vanishes with nothing to
# resume from, because `run_suite` has no checkpoint.
#
# `setsid` puts the campaign in its OWN session and process group, so a signal to the launching
# shell's group never reaches it. Progress goes to a log file that any later process can read, and
# the PID is recorded so the campaign can be found again -- and stopped deliberately -- after the
# thing that started it is gone.
#
# Usage: util/ad-hoc/2026-08-21_detach_campaign.bash <LOG_FILE> <COMMAND> [ARGS...]
set -uo pipefail

LOG="${1:?usage: $0 <LOG_FILE> <COMMAND> [ARGS...]}"
shift
mkdir -p "$(dirname "${LOG}")" || exit 2

setsid nohup "$@" >"${LOG}" 2>&1 &
PID=$!
# Record beside the log so a later session can check liveness without guessing the pattern.
echo "${PID}" >"${LOG}.pid"
echo "detached: pid=${PID} log=${LOG}"
echo "detached: check with  kill -0 ${PID}  /  tail -f ${LOG}"
