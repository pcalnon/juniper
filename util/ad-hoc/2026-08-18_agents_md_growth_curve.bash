#!/usr/bin/env bash
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# Version:     0.1.0
# License:     MIT License
#
# Purpose: Reconstruct the byte-size history of AGENTS.md (== CLAUDE.md) so the
# memory-file size problem can be reasoned about with a real growth curve rather
# than an impression. Single-use measurement support for the 2026-08-18
# shared-session-memory design effort.
#
# Usage: bash util/ad-hoc/2026-08-18_agents_md_growth_curve.bash [FILE]
# Output: TSV on stdout -- date<TAB>bytes<TAB>lines<TAB>short_sha

set -euo pipefail

FILE="${1:-AGENTS.md}"

printf 'date\tbytes\tlines\tsha\n'

git log --format='%H %ad' --date=short --reverse -- "$FILE" | while read -r sha date; do
    blob="${sha}:${FILE}"
    if git cat-file -e "$blob" 2>/dev/null; then
        bytes=$(git cat-file -p "$blob" | wc -c)
        lines=$(git cat-file -p "$blob" | wc -l)
        printf '%s\t%s\t%s\t%s\n' "$date" "$bytes" "$lines" "${sha:0:8}"
    fi
done
