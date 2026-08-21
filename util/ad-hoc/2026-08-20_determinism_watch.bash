#!/usr/bin/env bash
# Emit one line per completed cell/run of the N=20 determinism campaign.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-20
# Status:      ad-hoc -- one-off (juniper-cascor#532 campaign progress watch)
# Retire when: the campaign is written up; delete with the rest of the #532 tooling.
# Related:     2026-08-20_determinism_campaign.bash (what this watches).
#
# The campaign runs for hours across two arms. This exists so progress arrives as events rather
# than as repeated manual polling, and so a stall is visible as SILENCE against a known cadence
# rather than being mistaken for "still working".
#
# Usage: util/ad-hoc/2026-08-20_determinism_watch.bash <SUITE_DIR> [OUT_ROOT] [POLL_SECONDS]
set -uo pipefail

SUITE_DIR="${1:?usage: $0 <SUITE_DIR> [OUT_ROOT] [POLL_SECONDS]}"
OUT_ROOT="${2:-${HOME}/.local/state/juniper-experiments/determinism-n20}"
POLL="${3:-30}"

prev_cells=0
prev_cli=0
while true; do
    if [[ -f "${SUITE_DIR}/registry.jsonl" ]]; then
        cells="$(wc -l <"${SUITE_DIR}/registry.jsonl")"
        if ((cells > prev_cells)); then
            wall="$(tail -1 "${SUITE_DIR}/registry.jsonl" | sed -n 's/.*"wall_seconds": \([0-9.]*\).*/\1/p')"
            outcome="$(tail -1 "${SUITE_DIR}/registry.jsonl" | sed -n 's/.*"outcome": "\([a-z_]*\)".*/\1/p')"
            echo "service arm: ${cells}/20 cells ($(date -u +%H:%M:%S)) last=${outcome} wall=${wall}s"
            prev_cells="${cells}"
        fi
    fi
    cli="$(find "${OUT_ROOT}" -maxdepth 2 -name thread_probe.json 2>/dev/null | wc -l)"
    if ((cli > prev_cli)); then
        echo "CLI arm: ${cli}/20 runs ($(date -u +%H:%M:%S))"
        prev_cli="${cli}"
    fi
    if ((prev_cells >= 20 && prev_cli >= 20)); then
        echo "campaign: BOTH ARMS COMPLETE"
        break
    fi
    sleep "${POLL}"
done
