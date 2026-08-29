#!/usr/bin/env bash
#
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# Version:     0.1.0
# License:     MIT License
#
# Poll the Duplicati server's progress endpoint for the running Yamaguchi
# task and emit one line per phase transition, any error text, and a final
# line when the task ends. Designed as a Monitor event stream: quiet while
# nothing changes.

set -u
# Both paths below were hardcoded to a moment in time and drifted:
#   * API pointed into the sibling worktree .claude/worktrees/mossy-growing-salamander,
#     a retirement candidate -- removing it would have broken this script silently,
#     at the moment it was most needed.
#   * DEST pointed at the pre-migration destination on sdc4 (moved 2026-08-26,
#     note 8.13), so every "dest files" count would have described the wrong dir.
#
# Usage: bash util/ad-hoc/yamaguchi_watch.bash [DEST]
#        Override YAMAGUCHI_API when running from a non-standard checkout.
API="${YAMAGUCHI_API:-/home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_server_api.py}"
DEST="${1:-/mnt/Backups/Ubuntu/Yamaguchi}"
prev=""
while :; do
    out="$(python3 "${API}" progress 2>&1)"
    if echo "${out}" | grep -q "no active task"; then
        echo "YAMAGUCHI TASK ENDED -- dest files: $(find "${DEST}" -maxdepth 1 -type f 2>/dev/null | wc -l)"
        break
    fi
    phase="$(echo "${out}" | grep -oE '"Phase": "[^"]*"' | head -1)"
    if [[ -n "${phase}" && "${phase}" != "${prev}" ]]; then
        count="$(echo "${out}" | grep -oE '"ProcessedFileCount": [0-9]*' | head -1)"
        echo "phase change: ${phase} | ${count} | dest files: $(find "${DEST}" -maxdepth 1 -type f 2>/dev/null | wc -l)"
        prev="${phase}"
    fi
    echo "${out}" | grep -iE 'error|exception|fatal' | head -2
    sleep 120
done
