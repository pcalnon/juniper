#!/usr/bin/env bash
# WIDE-BUDGET HEAD-TO-HEAD -- sample host load so the wall-clock columns can be qualified.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-16
# Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
# Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the wide-budget head-to-head evidence note is merged; delete then.
# Related:     2026-08-16_h2h_phase_split.py (the phase decomposition this qualifies).
#
# WHY
# The campaign's two arms necessarily run in DIFFERENT time windows -- they must, because sharing
# 16 cores would inflate both walls and make the comparison meaningless. That trade buys a clean
# per-arm measurement at the cost of a confound: this is a shared desktop, and the background load
# (browser, grafana, docker stack) is not constant across a 17-hour campaign. The cap-64 r0 pair
# measured the CLI candidate phase at 2.09x the service's while doing only 1.44x the candidate
# epochs, leaving ~1.45x of per-epoch throughput unexplained -- exactly the kind of gap that is
# irresponsible to attribute to "the path" without knowing what else the host was doing.
#
# So this records load average and non-experiment CPU every 60 s. It cannot retro-fit the arms
# already run (cap-64 r0's pair has no sample and must be reported as such), but it lets every
# later arm state the conditions it was measured under.
#
# Deliberately cheap: one /proc/loadavg read plus one `ps` per minute. It must not become part of
# what it measures.
#
# READ load1 / load5, NOT the cpu columns. `ps -eo pcpu` reports each process's average CPU over
# its LIFETIME, not its instantaneous use, so the cascor_cpu / other_cpu sums are a rough
# composition hint only -- summing them across long-lived desktop processes overstates present
# load badly (they read ~7-8 "cores" against a true load average of ~11 on a 16-core host). The
# load averages are genuine runnable-task counts and are the figures the evidence note quotes.
# The cpu columns are kept because attributing a spike to python-vs-not is still useful, and
# because changing the schema mid-campaign would split the series.
#
# Usage: util/ad-hoc/2026-08-16_h2h_load_sampler.bash <OUT_TSV>
set -uo pipefail
OUT="${1:?usage: $0 <OUT_TSV>}"
[[ -s "${OUT}" ]] || printf 'ts\tload1\tload5\tcascor_cpu\tother_cpu\n' >"${OUT}"
while :; do
    read -r l1 l5 _ < <(awk '{print $1, $2, $3}' /proc/loadavg)
    # Split total CPU into "this campaign's python" and everything else, so a spike can be
    # attributed rather than guessed at.
    cascor=$(ps -eo pcpu,args --no-headers 2>/dev/null | awk '/[p]ython|[u]vicorn/ {s += $1} END {printf "%.1f", s+0}')
    other=$(ps -eo pcpu,args --no-headers 2>/dev/null | awk '!/[p]ython|[u]vicorn/ {s += $1} END {printf "%.1f", s+0}')
    printf '%s\t%s\t%s\t%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${l1}" "${l5}" "${cascor}" "${other}" >>"${OUT}"
    sleep 60
done
