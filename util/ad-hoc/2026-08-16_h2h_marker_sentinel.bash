#!/usr/bin/env bash
# WIDE-BUDGET HEAD-TO-HEAD -- preserve the training-span markers against log rotation.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-16
# Status:      ad-hoc -- one-off (wide-budget head-to-head campaign)
# Retire when: the wide-budget head-to-head evidence note is merged; delete then.
# Related:     2026-08-16_h2h_collect.py (reads the markers.txt this writes).
#
# WHY THIS EXISTS
# The campaign's shared wall-clock denominator is the span between two INFO records that cascor
# emits around CascadeCorrelationNetwork.fit:
#     cascade_correlation.py:1918  "fit: Starting main training loop ..."   <- FIRST lines of a run
#     cascade_correlation.py:1936  "fit: Training completed."               <- last lines of a run
# juniper-cascor#523 put that log in the run's own directory, which solved cross-process
# clobbering. It did not solve ROTATION WITHIN one run: the cap-64 cell c000 wrote ~950 MB and
# rotated once, leaving the start marker in juniper_cascor.log.1 while juniper_cascor.log held
# only the tail. The collector reads rotated segments, so that case is covered -- but rotation
# keeps a bounded number of backups, and the marker at risk is the one on the FIRST line. A cell
# that rotates past the backup window loses its start marker permanently, and with it the only
# figure the two arms may be compared on.
#
# So this tails each run's log from line 1 the moment it appears and appends just those markers to
# a markers.txt sidecar that nothing rotates. It is read-only with respect to the run: it writes
# only its own sidecar, never touches the log, and cannot affect training.
#
# Only three patterns are captured -- the two fit markers and the CLI's juniper-data confirmation
# -- because those are the records that sit at the START of a run and are therefore the only ones
# rotation can take. Final accuracies and the unit count are emitted at the END, which rotation
# discards last, so they are always still in the live segment.
#
# Usage: util/ad-hoc/2026-08-16_h2h_marker_sentinel.bash <ROOT> [<ROOT> ...]
#        Run it in the background for the campaign's duration; stop it with SIGTERM.
set -uo pipefail

[[ $# -ge 1 ]] || { echo "usage: $0 <ROOT> [<ROOT> ...]" >&2; exit 2; }
ROOTS=("$@")
PATTERN='fit:1918|fit:1936|Using JuniperData service at'
# Only adopt logs that appear from now on, plus anything already live -- never walk the hundreds
# of historical run dirs under the run root (one idle tail each would be absurd).
START_STAMP="$(date '+%Y-%m-%d %H:%M:%S')"

cleanup() { pkill -P $$ tail 2>/dev/null; exit 0; }
trap cleanup TERM INT

echo "marker sentinel: watching ${ROOTS[*]} from ${START_STAMP}"
while :; do
    for root in "${ROOTS[@]}"; do
        [[ -d "${root}" ]] || continue
        while IFS= read -r log; do
            dir="$(dirname "${log}")"
            # One tail per log dir, ever. The guard file is what makes the loop idempotent.
            [[ -e "${dir}/.sentinel_claimed" ]] && continue
            : >"${dir}/.sentinel_claimed"
            # -n +1 so the start marker is captured even if the file already has content;
            # -F so the tail follows the file across a rotation instead of dying with the inode.
            tail -n +1 -F "${log}" 2>/dev/null | grep --line-buffered -E "${PATTERN}" >>"${dir}/markers.txt" &
            echo "marker sentinel: adopted ${log}"
        done < <(find "${root}" -mindepth 2 -maxdepth 4 -name juniper_cascor.log -newermt "${START_STAMP}" 2>/dev/null)
    done
    sleep 10
done
