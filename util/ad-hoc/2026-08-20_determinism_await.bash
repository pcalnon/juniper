#!/usr/bin/env bash
# Block until a determinism arm reaches its target run count, then exit.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-20
# Status:      ad-hoc -- one-off (juniper-cascor#532 campaign)
# Retire when: the campaign is written up; delete with the rest of the #532 tooling.
# Related:     2026-08-20_determinism_watch.bash (per-run events; this is the one-shot form).
#
# The watch script emits an event per completed run, which is right while the pace is still
# unknown and pure noise once it is steady. This is the single-notification counterpart: it exits
# when the arm is done, or when the campaign driver has clearly stopped producing runs.
#
# It deliberately also exits on a STALLED campaign rather than blocking forever. A run count that
# stops advancing looks exactly like a slow host until you check, and "still waiting" is the
# failure mode that quietly eats an afternoon.
#
# Usage: util/ad-hoc/2026-08-20_determinism_await.bash <TARGET> [OUT_ROOT] [POLL] [STALL_POLLS]
set -uo pipefail

TARGET="${1:?usage: $0 <TARGET> [OUT_ROOT] [POLL] [STALL_POLLS]}"
OUT_ROOT="${2:-${HOME}/.local/state/juniper-experiments/determinism-n20}"
POLL="${3:-60}"
STALL_POLLS="${4:-25}"

last=-1
stalled=0
while true; do
    count="$(find "${OUT_ROOT}" -maxdepth 2 -name thread_probe.json 2>/dev/null | wc -l)"
    if ((count >= TARGET)); then
        echo "CLI arm COMPLETE: ${count}/${TARGET} runs at $(date -u +%H:%M:%SZ)"
        exit 0
    fi
    if ((count == last)); then
        stalled=$((stalled + 1))
        if ((stalled >= STALL_POLLS)); then
            echo "CLI arm STALLED at ${count}/${TARGET} -- no new run in $((STALL_POLLS * POLL))s ($(date -u +%H:%M:%SZ))"
            exit 1
        fi
    else
        stalled=0
        last="${count}"
    fi
    sleep "${POLL}"
done
