#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc/2026-08-28_backup_footprint.bash
# Author:      Paul Calnon
# Version:     1.0.0
# License:     MIT License
#
# Purpose:  Report the exact uncompressed footprint util/juniper-backup.bash would archive per repo, using the SAME exclude list and
#           the SAME measurement path the script itself uses. Answers the capacity question the lifecycle design SS6.4.2 records.
#
# Usage:    bash util/ad-hoc/2026-08-28_backup_footprint.bash
#######################################################################################################################################################################################################################################################
set -euo pipefail

PROJECT_DIR="${HOME}/Development/python/Juniper"
APPLICATION_REPOS=( "juniper-canopy" "juniper-cascor" "juniper-cascor-client" "juniper-cascor-worker" "juniper-data" "juniper-data-client" "juniper-deploy" "juniper-ml" "juniper-recurrence" "juniper-slacker" )
EXCLUDE_DIRS=( ".amp" ".benchmarks" ".claude" ".mypy_cache" ".playwright-mcp" ".pytest_cache" ".ruff_cache" ".serena" ".trunk" "dist" "logs" "reports" "resources" "data" "build" "venv" )

TOTAL_EXCLUDED=0
TOTAL_RAW=0
printf '%-26s %14s %14s\n' "repo" "archived" "unexcluded"
printf '%-26s %14s %14s\n' "--------------------------" "--------------" "--------------"

for REPO in "${APPLICATION_REPOS[@]}"; do
    [[ -d "${PROJECT_DIR}/${REPO}" ]] || continue
    ARGS=()
    for EXCLUDE_DIR in "${EXCLUDE_DIRS[@]}"; do
        if [[ -d "${PROJECT_DIR}/${REPO}/${EXCLUDE_DIR}" ]]; then
            ARGS+=( "--exclude=${REPO}/${EXCLUDE_DIR}" )
        fi
    done
    EXCLUDED_BYTES="$( cd "${PROJECT_DIR}" && du -sb "${ARGS[@]}" "${REPO}" | cut -f1 )"
    RAW_BYTES="$( cd "${PROJECT_DIR}" && du -sb "${REPO}" | cut -f1 )"
    TOTAL_EXCLUDED=$(( TOTAL_EXCLUDED + EXCLUDED_BYTES ))
    TOTAL_RAW=$(( TOTAL_RAW + RAW_BYTES ))
    printf '%-26s %14s %14s\n' "${REPO}" "$(numfmt --to=iec "${EXCLUDED_BYTES}")" "$(numfmt --to=iec "${RAW_BYTES}")"
done

printf '%-26s %14s %14s\n' "--------------------------" "--------------" "--------------"
printf '%-26s %14s %14s\n' "TOTAL" "$(numfmt --to=iec "${TOTAL_EXCLUDED}")" "$(numfmt --to=iec "${TOTAL_RAW}")"
printf '\nexact archived bytes: %d\n' "${TOTAL_EXCLUDED}"
printf 'reduction factor:     %sx\n' "$(( TOTAL_RAW / (TOTAL_EXCLUDED > 0 ? TOTAL_EXCLUDED : 1) ))"
