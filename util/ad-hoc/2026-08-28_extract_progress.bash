#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc/2026-08-28_extract_progress.bash
# Author:      Paul Calnon
# Version:     1.0.0
# License:     MIT License
#
# Purpose:  Emit one progress line per minute for the 2026-02-27 archive extraction, and exit as soon as the extracting tar is gone.
#           Reports the uncompressed bytes tar has consumed (rchar) rather than output size, because the exclude list means output
#           size is a poor proxy for how far through the 111 GB stream we are.
#
# Usage:    bash util/ad-hoc/2026-08-28_extract_progress.bash [PID]
#######################################################################################################################################################################################################################################################
set -uo pipefail

DEST_ROOT="${HOME}/juniper-restore-2026-02-27"
TAR_PID="${1:-}"

if [[ -z "${TAR_PID}" ]]; then
    TAR_PID="$(pgrep -f 'tar -xvzf /media/pcalnon' | head -1)"
fi
[[ -n "${TAR_PID}" ]] || { echo "no extracting tar found"; exit 0; }

PREV=0
while :; do
    if [[ ! -r "/proc/${TAR_PID}/io" ]]; then
        echo "DONE: extraction process exited; extracted $(du -sh "${DEST_ROOT}" 2>/dev/null | cut -f1)"
        exit 0
    fi
    READ_BYTES="$(awk '/^rchar:/ {print $2}' "/proc/${TAR_PID}/io" 2>/dev/null)"
    [[ -n "${READ_BYTES}" ]] || { echo "DONE: extraction process exited"; exit 0; }
    RATE=$(( (READ_BYTES - PREV) / 60 ))
    PREV="${READ_BYTES}"
    printf 'read %s uncompressed | %s/s | extracted %s | %s entries\n' \
        "$(numfmt --to=iec "${READ_BYTES}")" \
        "$(numfmt --to=iec "${RATE}")" \
        "$(du -sh "${DEST_ROOT}" 2>/dev/null | cut -f1)" \
        "$(wc -l < "${DEST_ROOT}/.extract-manifest.txt" 2>/dev/null || echo 0)"
    sleep 60
done
