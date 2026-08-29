#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc/2026-08-28_extract_feb_archive.bash
# Author:      Paul Calnon
# Version:     1.0.0
# License:     MIT License
#
# Purpose:  Extract the 2026-02-27 project archive ONCE, applying the same repo-top-level exclude policy util/juniper-backup.bash
#           uses, so that the 111 GB plaintext tarball can be replaced by a compact, ENCRYPTED per-repo backup set.
#
#           The archive is a plaintext copy of the entire project on removable media -- precisely the exposure the backup script's
#           asymmetric encryption exists to prevent -- and it occupies half of EBC5-F0A3. Re-backing the same STATE through the
#           fixed script yields an encrypted set a fraction of the size.
#
#           ONE pass. The archive is ~111 GB compressed and streams at roughly 37 MB/s of uncompressed data, so a separate listing
#           pass would cost another hour for information this extraction already produces via -v.
#
#           The --exclude patterns and --strip-components depth were proved on a synthetic archive first, in
#           util/ad-hoc/2026-08-28_extract_pattern_probe.bash. Do not change them without re-running that probe: a mis-scoped
#           tar --exclude matches nothing, exits 0, and reports success -- the exact class that produced 100 GB archives.
#
# Usage:    bash util/ad-hoc/2026-08-28_extract_feb_archive.bash
#######################################################################################################################################################################################################################################################
set -euo pipefail

ARCHIVE="/media/pcalnon/EBC5-F0A3/Juniper-8.0.0.python/juniper-8.0.0_python_2026-02-27.tgz"
DEST_ROOT="${HOME}/juniper-restore-2026-02-27"
PREFIX="home/pcalnon/Development/python/Juniper"
MANIFEST="${DEST_ROOT}/.extract-manifest.txt"

# Repo-top-level directories that are regenerable bulk or local tooling state. Mirrors EXCLUDE_DIRS in util/juniper-backup.bash.
#   `data` alone is ~96 GB of the current tree; it is dataset output that juniper-data regenerates.
BULK_DIRS=( ".amp" ".benchmarks" ".claude" ".mypy_cache" ".playwright-mcp" ".pytest_cache" ".ruff_cache" ".serena" ".trunk" "dist" "logs" "reports" "resources" "data" "build" "venv" )

[[ -f "${ARCHIVE}" ]] || { echo "FATAL: archive not found: ${ARCHIVE}" >&2; exit 1; }

AVAIL_KB="$(df -Pk "${HOME}" | awk 'NR==2 {print $4}')"
(( AVAIL_KB > 200000000 )) || { echo "FATAL: want >200 GB free under ${HOME}, have $(( AVAIL_KB / 1048576 )) GB" >&2; exit 1; }

mkdir -p "${DEST_ROOT}"

EXCLUDES=()
for BULK in "${BULK_DIRS[@]}"; do
    EXCLUDES+=( "--exclude=${PREFIX}/*/${BULK}" )
done

echo "archive : ${ARCHIVE} ($(numfmt --to=iec "$(stat -c%s "${ARCHIVE}")"))"
echo "dest    : ${DEST_ROOT}"
echo "excludes: ${#BULK_DIRS[@]} repo-top-level directories"
echo "started : $(date -Is)"
echo

# --wildcards --no-wildcards-match-slash: `*` matches exactly ONE segment, so `<prefix>/*/data` is the repo's TOP-LEVEL data dir
#   and never `<repo>/src/nested/data`, which is source. Exclusion is matched against the ARCHIVED name, so patterns carry the
#   full prefix even though --strip-components later removes it.
tar -xvzf "${ARCHIVE}" -C "${DEST_ROOT}" \
    --wildcards --no-wildcards-match-slash \
    "${EXCLUDES[@]}" \
    --strip-components=5 \
    "${PREFIX}" > "${MANIFEST}" 2>"${DEST_ROOT}/.extract-errors.txt"

echo "finished: $(date -Is)"
echo "entries : $(wc -l < "${MANIFEST}")"
echo "size    : $(du -sh "${DEST_ROOT}" | cut -f1)"
echo
echo "top-level:"
find "${DEST_ROOT}" -mindepth 1 -maxdepth 1 -type d | sort | sed 's/^/   /'
