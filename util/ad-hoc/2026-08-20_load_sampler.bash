#!/usr/bin/env bash
# Sample host load for the duration of a campaign, so a timing noise floor stays interpretable.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-20
# Status:      ad-hoc -- one-off (juniper-cascor#532 campaign instrumentation)
# Retire when: the campaign is written up; delete with the rest of the #532 tooling.
#
# The determinism campaign reports mean +/- sd for training span and candidate throughput, and
# that sd is the number the next measurement gets sized against. An sd inflated by an unrelated
# 21-hour antivirus scan is not the trainer's noise floor, and there is no way to tell the two
# apart after the fact unless contention was recorded WHILE the runs happened. Sampling costs
# nothing; reconstructing it later is impossible.
#
# It also bears on external validity in a way specific to this defect. If the divergence
# mechanism is scheduling variability under an oversubscribed thread pool, then the rate itself
# may depend on how loaded the host was -- so the load distribution is part of the result, not
# just a footnote to it.
#
# Usage: util/ad-hoc/2026-08-20_load_sampler.bash <OUT_FILE> [INTERVAL_SECONDS]
set -uo pipefail

OUT="${1:?usage: $0 <OUT_FILE> [INTERVAL_SECONDS]}"
INTERVAL="${2:-30}"

while true; do
    read -r l1 l5 l15 rest </proc/loadavg
    printf '{"utc":"%s","load1":%s,"load5":%s,"load15":%s,"running":"%s"}\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${l1}" "${l5}" "${l15}" "${rest%% *}" >>"${OUT}"
    sleep "${INTERVAL}"
done
