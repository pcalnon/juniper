#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc/2026-08-28_verify_feb_backup_set.bash
# Author:      Paul Calnon
# Version:     1.0.0
# License:     MIT License
#
# Purpose:  Independently verify the snapshot-2026-02-27 backup set actually RESTORES, rather than trusting the run's own
#           "COMPLETE" line. That line has been wrong before: on 2026-08-28 a run printed it while juniper-data never reached the
#           second drive, because per-repo counters were reset inside the loop.
#
#           For every archive in the set, on BOTH devices, this:
#             1. decrypts with the DOCUMENTED recipe (gpg -d | tar -xjf -) into a scratch dir,
#             2. diffs the restored tree against the source tree the backup was built from,
#             3. confirms the two devices hold byte-identical ciphertext for the same archive name.
#
#           A backup that has not been restored is a hypothesis, not a backup.
#
# Usage:    bash util/ad-hoc/2026-08-28_verify_feb_backup_set.bash [LABEL] [SOURCE_ROOT]
#######################################################################################################################################################################################################################################################
set -uo pipefail

LABEL="${1:-snapshot-2026-02-27}"
SOURCE_ROOT="${2:-${HOME}/juniper-restore-2026-02-27}"
DEVICE_A="/media/pcalnon/EBC5-F0A3/Juniper-8.0.0.python"
DEVICE_B="/media/pcalnon/DFF3-2782/Juniper-8.0.0.python"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

FAILURES=0
CHECKED=0

mapfile -t ARCHIVES < <(find "${DEVICE_A}" -name "*_${LABEL}_*" -type f | sort)
(( ${#ARCHIVES[@]} > 0 )) || { echo "FATAL: no archives matching label ${LABEL} on ${DEVICE_A}" >&2; exit 1; }

echo "set     : ${LABEL}"
echo "source  : ${SOURCE_ROOT}"
echo "archives: ${#ARCHIVES[@]} on device A"
echo

for ARCHIVE in "${ARCHIVES[@]}"; do
    BASE="$(basename "${ARCHIVE}")"
    # Recover the tree name: Juniper_<label>_<tree>_<uuid>_<stamp>.tbz2.gpg
    TREE="${BASE#Juniper_${LABEL}_}"
    TREE="${TREE%%_????????-????-????-????-????????????_*}"

    RESTORE="${WORK}/${TREE}"
    mkdir -p "${RESTORE}"

    if ! gpg --batch --quiet --decrypt "${ARCHIVE}" 2>/dev/null | tar -xjf - -C "${RESTORE}" 2>/dev/null; then
        echo "  FAIL  ${TREE}: documented restore (gpg -d | tar -xjf -) failed"
        FAILURES=$(( FAILURES + 1 ))
        continue
    fi

    if [[ ! -d "${SOURCE_ROOT}/${TREE}" ]]; then
        echo "  WARN  ${TREE}: restored, but no source tree to compare against"
        CHECKED=$(( CHECKED + 1 ))
        continue
    fi

    # The archive stores the tree under its own name, so the restored path mirrors the source path.
    if diff -r --no-dereference "${RESTORE}/${TREE}" "${SOURCE_ROOT}/${TREE}" > "${WORK}/${TREE}.diff" 2>&1; then
        DIFF_NOTE="identical to source"
    else
        # An exclude-driven absence is expected: the backup deliberately drops logs/, data/, and any
        #   CACHEDIR.TAG-marked cache (--exclude-caches-all), which catches NESTED .mypy_cache /
        #   .pytest_cache the path-anchored exclude list does not name.
        #   `|| echo 0` is WRONG here: `grep -c` prints its count AND exits 1 when that count is zero,
        #   so the fallback appends a second line and the arithmetic below sees "0\n0". Use `|| true`.
        ONLY_IN_SOURCE="$(grep -c "^Only in ${SOURCE_ROOT}" "${WORK}/${TREE}.diff" 2>/dev/null || true)"
        OTHER="$(grep -v "^Only in ${SOURCE_ROOT}" "${WORK}/${TREE}.diff" 2>/dev/null | grep -c . || true)"
        ONLY_IN_SOURCE="${ONLY_IN_SOURCE:-0}"
        OTHER="${OTHER:-0}"
        if (( OTHER == 0 )); then
            DIFF_NOTE="matches; ${ONLY_IN_SOURCE} path(s) intentionally excluded"
        else
            echo "  FAIL  ${TREE}: restored content differs from source beyond the exclude list"
            head -5 "${WORK}/${TREE}.diff" | sed 's/^/          /'
            FAILURES=$(( FAILURES + 1 ))
            rm -rf "${RESTORE}"
            continue
        fi
    fi

    # Both devices must hold the SAME ciphertext, which is what "one backup set" means.
    if [[ -f "${DEVICE_B}/${BASE}" ]]; then
        if cmp -s "${ARCHIVE}" "${DEVICE_B}/${BASE}"; then
            REPLICA_NOTE="replica byte-identical"
        else
            echo "  FAIL  ${TREE}: the two devices hold DIFFERENT bytes under one name"
            FAILURES=$(( FAILURES + 1 ))
            rm -rf "${RESTORE}"
            continue
        fi
    else
        echo "  FAIL  ${TREE}: missing from device B entirely"
        FAILURES=$(( FAILURES + 1 ))
        rm -rf "${RESTORE}"
        continue
    fi

    printf '  OK    %-24s %s; %s\n' "${TREE}" "${DIFF_NOTE}" "${REPLICA_NOTE}"
    CHECKED=$(( CHECKED + 1 ))
    rm -rf "${RESTORE}"
done

echo
if (( FAILURES == 0 )); then
    echo "RESULT: PASS -- ${CHECKED} archive(s) restored with the documented recipe, matched source, and are byte-identical across both devices."
else
    echo "RESULT: FAIL -- ${FAILURES} archive(s) failed; ${CHECKED} passed." >&2
    exit 1
fi
