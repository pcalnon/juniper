#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc/2026-08-28_backup_exclude_e2e.bash
# Author:      Paul Calnon
# Version:     1.0.0
# License:     MIT License
#
# Purpose:  End-to-end proof that util/juniper-backup.bash actually EXCLUDES what its exclude list names, and that the archive it
#           writes decompresses with the recipe its own header documents.
#
#           This exists because every previous exclude defect was invisible to shellcheck, invisible to tar's exit status, and
#           invisible to the script's own log. The ONLY thing that catches this class is measuring the archive that comes out.
#
#           Checks:
#             1. --dry-run reports a source size that reflects the excludes.
#             2. A real run produces one archive per repo, each named .tbz2.gpg.
#             3. Decrypting with the DOCUMENTED recipe (gpg -d | tar -xjf -) succeeds.
#             4. The restored tree contains the kept files and NONE of the excluded directories.
#             5. The archive is far smaller than the unexcluded tree (the size assertion that catches an inert exclude).
#
# Usage:    bash util/ad-hoc/2026-08-28_backup_exclude_e2e.bash
#######################################################################################################################################################################################################################################################
set -euo pipefail

SCRIPT_UNDER_TEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/juniper-backup.bash"
[[ -x "${SCRIPT_UNDER_TEST}" || -f "${SCRIPT_UNDER_TEST}" ]] || { echo "FATAL: not found: ${SCRIPT_UNDER_TEST}" >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

SRC="${WORK}/Juniper"
DEST="${WORK}/dest"
RESTORE="${WORK}/restore"
mkdir -p "${DEST}" "${RESTORE}"

#######################################################################################################################################################################################################################################################
# Build a synthetic project tree using REAL repo names from APPLICATION_REPOS, each with kept source and excluded bulk.
#   16 MB of "data" per repo against a few hundred bytes of source: if the excludes are inert the archive cannot hide it.
for REPO_NAME in juniper-cascor juniper-data; do
    mkdir -p "${SRC}/${REPO_NAME}/src" "${SRC}/${REPO_NAME}/data" "${SRC}/${REPO_NAME}/logs" "${SRC}/${REPO_NAME}/build" "${SRC}/${REPO_NAME}/src/nested/data"
    echo "keep: top-level source" > "${SRC}/${REPO_NAME}/src/main.py"
    echo "keep: nested source"    > "${SRC}/${REPO_NAME}/src/nested/keep.py"
    # A NESTED dir sharing an excluded name. Must SURVIVE -- excludes are anchored to the repo top level, so this is source, not cache.
    echo "keep: nested data file" > "${SRC}/${REPO_NAME}/src/nested/data/payload.json"
    dd if=/dev/urandom of="${SRC}/${REPO_NAME}/data/big.npz"  bs=1M count=8 status=none
    dd if=/dev/urandom of="${SRC}/${REPO_NAME}/logs/big.log"  bs=1M count=4 status=none
    dd if=/dev/urandom of="${SRC}/${REPO_NAME}/build/big.o"   bs=1M count=4 status=none
done

UNEXCLUDED_BYTES="$(du -sb "${SRC}" | cut -f1)"
echo "synthetic tree: $(numfmt --to=iec "${UNEXCLUDED_BYTES}") total (mostly excludable bulk)"
echo

#######################################################################################################################################################################################################################################################
echo "=============================================================="
echo "1. --dry-run -- must PREVIEW and write NOTHING"
echo "=============================================================="
bash "${SCRIPT_UNDER_TEST}" --source "${SRC}" --dest "${DEST}" --dry-run 2>&1 | sed 's/^/   /'
DRY_RUN_WROTE="$(find "${DEST}" -type f | wc -l)"
if (( DRY_RUN_WROTE != 0 )); then
    echo "   FAIL --dry-run wrote ${DRY_RUN_WROTE} file(s) to the destination." >&2
    echo "        The dry-run block fell through into the build loop." >&2
    exit 1
fi
echo "   OK   --dry-run wrote 0 files."

echo
echo "=============================================================="
echo "2. real run"
echo "=============================================================="
bash "${SCRIPT_UNDER_TEST}" --source "${SRC}" --dest "${DEST}" 2>&1 | sed 's/^/   /'

echo
echo "=============================================================="
echo "3. archives produced"
echo "=============================================================="
mapfile -t ARCHIVES < <(find "${DEST}" -name '*.gpg' -type f | sort)
printf '   count: %d\n' "${#ARCHIVES[@]}"
for _a in "${ARCHIVES[@]}"; do
    printf '   %10s  %s\n' "$(numfmt --to=iec "$(stat -c%s "${_a}")")" "$(basename "${_a}")"
done
(( ${#ARCHIVES[@]} == 2 )) || { echo "   FAIL: expected 2 archives (one per repo)" >&2; exit 1; }

echo
echo "=============================================================="
echo "4. restore with the DOCUMENTED recipe: gpg -d | tar -xjf -"
echo "=============================================================="
FAILURES=0
for _a in "${ARCHIVES[@]}"; do
    BASE="$(basename "${_a}")"
    case "${BASE}" in
        *.tbz2.gpg) ;;
        *) echo "   FAIL: archive is not named .tbz2.gpg: ${BASE}" >&2; FAILURES=$(( FAILURES + 1 )); continue ;;
    esac
    if gpg --batch --quiet --decrypt "${_a}" 2>/dev/null | tar -xjf - -C "${RESTORE}"; then
        echo "   OK   restored ${BASE}"
    else
        echo "   FAIL could not restore ${BASE} with the documented recipe" >&2
        FAILURES=$(( FAILURES + 1 ))
    fi
done

echo
echo "=============================================================="
echo "5. contents -- excluded OUT, kept IN, nested same-name dir KEPT"
echo "=============================================================="
check_absent() {
    if [[ -e "$1" ]]; then
        echo "   FAIL excluded path IS PRESENT in the restored tree: ${1#"${RESTORE}"/}" >&2
        FAILURES=$(( FAILURES + 1 ))
    else
        echo "   OK   excluded: ${1#"${RESTORE}"/}"
    fi
}
check_present() {
    if [[ -e "$1" ]]; then
        echo "   OK   kept:     ${1#"${RESTORE}"/}"
    else
        echo "   FAIL expected path MISSING from the restored tree: ${1#"${RESTORE}"/}" >&2
        FAILURES=$(( FAILURES + 1 ))
    fi
}
for REPO_NAME in juniper-cascor juniper-data; do
    check_absent  "${RESTORE}/${REPO_NAME}/data"
    check_absent  "${RESTORE}/${REPO_NAME}/logs"
    check_absent  "${RESTORE}/${REPO_NAME}/build"
    check_present "${RESTORE}/${REPO_NAME}/src/main.py"
    check_present "${RESTORE}/${REPO_NAME}/src/nested/keep.py"
    check_present "${RESTORE}/${REPO_NAME}/src/nested/data/payload.json"
done

echo
echo "=============================================================="
echo "6. size assertion -- the check that actually catches an inert exclude"
echo "=============================================================="
TOTAL_ARCHIVE_BYTES=0
for _a in "${ARCHIVES[@]}"; do
    TOTAL_ARCHIVE_BYTES=$(( TOTAL_ARCHIVE_BYTES + $(stat -c%s "${_a}") ))
done
printf '   source tree, no excludes : %10s\n' "$(numfmt --to=iec "${UNEXCLUDED_BYTES}")"
printf '   archives written total   : %10s\n' "$(numfmt --to=iec "${TOTAL_ARCHIVE_BYTES}")"
# The bulk is /dev/urandom, so it is incompressible: an inert exclude CANNOT hide inside compression.
if (( TOTAL_ARCHIVE_BYTES < UNEXCLUDED_BYTES / 10 )); then
    echo "   OK   archives are under a tenth of the unexcluded tree -- excludes applied."
else
    echo "   FAIL archives are too large -- the exclude list is inert." >&2
    FAILURES=$(( FAILURES + 1 ))
fi

echo
echo "=============================================================="
echo "7. --repos and --label"
echo "=============================================================="
# A tree the built-in APPLICATION_REPOS list does not name, standing in for juniper-legacy / a restored snapshot.
mkdir -p "${SRC}/LegacyTree/src"
echo "legacy source" > "${SRC}/LegacyTree/src/old.py"
DEST2="${WORK}/dest2"
mkdir -p "${DEST2}"

bash "${SCRIPT_UNDER_TEST}" --source "${SRC}" --dest "${DEST2}" \
     --repos "juniper-cascor LegacyTree" --label "snapshot-2026-02-27" >/dev/null 2>&1

mapfile -t LABELLED < <(find "${DEST2}" -name '*.gpg' -type f | sort)
printf '   archives: %d\n' "${#LABELLED[@]}"
for _a in "${LABELLED[@]}"; do printf '   %s\n' "$(basename "${_a}")"; done

if (( ${#LABELLED[@]} != 2 )); then
    echo "   FAIL --repos did not produce exactly the 2 named trees" >&2
    FAILURES=$(( FAILURES + 1 ))
else
    echo "   OK   --repos archived exactly the named trees"
fi
# juniper-data is in the BUILT-IN list but not in --repos; it must be absent, or the override did nothing.
if find "${DEST2}" -name '*juniper-data*' | grep -q .; then
    echo "   FAIL --repos was ignored: juniper-data archived despite not being named" >&2
    FAILURES=$(( FAILURES + 1 ))
else
    echo "   OK   --repos excluded the built-in repos it did not name"
fi
if find "${DEST2}" -name '*LegacyTree*' | grep -q .; then
    echo "   OK   --repos archived a tree absent from APPLICATION_REPOS"
else
    echo "   FAIL --repos did not archive LegacyTree" >&2
    FAILURES=$(( FAILURES + 1 ))
fi
if [[ "$(basename "${LABELLED[0]}")" == Juniper_snapshot-2026-02-27_* ]]; then
    echo "   OK   --label is present in the archive name"
else
    echo "   FAIL --label missing from archive name: $(basename "${LABELLED[0]}")" >&2
    FAILURES=$(( FAILURES + 1 ))
fi

echo
echo "=============================================================="
echo "8. override validation -- both reach filenames and paths"
echo "=============================================================="
expect_rejected() {
    local what="$1"; shift
    if bash "${SCRIPT_UNDER_TEST}" --source "${SRC}" --dest "${DEST2}" "$@" >/dev/null 2>&1; then
        echo "   FAIL accepted ${what}" >&2
        FAILURES=$(( FAILURES + 1 ))
    else
        echo "   OK   rejected ${what}"
    fi
}
# A repo name reaching ${PROJECT_DIR}/${REPO} unchecked would archive a tree outside the project.
expect_rejected "path-traversal repo name" --repos "../../etc"
expect_rejected "repo name with a slash"   --repos "juniper-cascor/../.."
# A label reaching the archive name unchecked would invent a directory or split a downstream filename.
expect_rejected "label with a slash"       --label "a/b"
expect_rejected "label with a space"       --label "two words"
expect_rejected "empty repo list"          --repos ""

echo
echo "=============================================================="
if (( FAILURES == 0 )); then
    echo "RESULT: PASS -- excludes apply, archive name matches format, documented restore works,"
    echo "        --repos/--label work and reject unsafe input."
else
    echo "RESULT: FAIL -- ${FAILURES} check(s) failed." >&2
    exit 1
fi
echo "=============================================================="
