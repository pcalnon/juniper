#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc/2026-08-28_exclude_arg_repro.bash
# Author:      Paul Calnon
# Version:     1.0.0
# License:     MIT License
#
# Purpose:  Reproduce, in isolation, the exclude-argument defect that shipped in util/juniper-backup.bash on main (99df9bf0).
#
#           build_exclude_dirs_arg() emits array elements of the form:  --exclude="/abs/path"<space>
#           Two independent faults, EITHER of which alone makes the tar exclude inert:
#             (a) literal double-quote characters are baked into the argv value (quoting is a shell-parse artifact, not part of a value)
#             (b) the pattern is an ABSOLUTE path, but `tar -C parent leaf` stores members RELATIVE ("leaf/...")
#
#           The `du` path escapes fault (a) only because it runs through `eval`, which re-parses the quotes away.
#           That is precisely why du and tar disagree about what is excluded -- the same divergence the 08-27 review named as the whole bug.
#
# Usage:    bash util/ad-hoc/2026-08-28_exclude_arg_repro.bash
#######################################################################################################################################################################################################################################################
set -euo pipefail

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

PROJECT_DIR="${WORK}/Juniper"
APPLICATION_NAME="fake-repo"
APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_NAME}"

# A repo with a small source tree and one big excluded "data" dir, mirroring juniper-data.
mkdir -p "${APPLICATION_DIR}/src" "${APPLICATION_DIR}/data" "${APPLICATION_DIR}/logs"
echo "keep me" > "${APPLICATION_DIR}/src/main.py"
dd if=/dev/zero of="${APPLICATION_DIR}/data/big.npz" bs=1M count=8 status=none
dd if=/dev/zero of="${APPLICATION_DIR}/logs/big.log" bs=1M count=4 status=none

EXCLUDE_DIRS=( "data" "logs" )

#######################################################################################################################################################################################################################################################
# VERBATIM copies of the two functions as they stand on main (99df9bf0, util/juniper-backup.bash :181-199).
EXCLUDE_DIRS_VALIDATED=()
function validate_exclude_dirs() {
    local application_dir="$1"
    local exclude_dirs_array=()
    local current_exclude_dir=""
    local current_exclude_path=""
    for exclude_dir in "${EXCLUDE_DIRS[@]}"; do
        local current_exclude_dir="${application_dir}/${exclude_dir}"
        current_exclude_path="$(realpath "${current_exclude_dir}")"
        if [[ -d "${current_exclude_path}" ]]; then
            exclude_dirs_array+=("${current_exclude_path}")
        fi
    done
    EXCLUDE_DIRS_VALIDATED=( "${exclude_dirs_array[@]}" )
    return 0
}

EXCLUDE_DIRS_ARG=()
function build_exclude_dirs_arg() {
    local exclude_dirs_arg=()
    for exclude_dir in "${EXCLUDE_DIRS_VALIDATED[@]}"; do
        exclude_dirs_arg+=("$(printf -- '--exclude="%s" ' "${exclude_dir}")")
    done
    EXCLUDE_DIRS_ARG=( "${exclude_dirs_arg[@]}" )
    return 0
}
#######################################################################################################################################################################################################################################################

validate_exclude_dirs "${APPLICATION_DIR}"
build_exclude_dirs_arg

echo "=============================================================="
echo "1. What build_exclude_dirs_arg actually produces"
echo "=============================================================="
printf '   elements: %d\n' "${#EXCLUDE_DIRS_ARG[@]}"
for _i in "${!EXCLUDE_DIRS_ARG[@]}"; do
    printf '   [%d] <%s>\n' "${_i}" "${EXCLUDE_DIRS_ARG[${_i}]}"
done
echo "   ^ note the LITERAL double-quotes and the TRAILING SPACE inside each value."

echo
echo "=============================================================="
echo "2. The du path (goes through eval -- quotes get re-parsed away)"
echo "=============================================================="
COMMAND="du -sb $(printf '%s ' "${EXCLUDE_DIRS_ARG[@]}") \"${APPLICATION_DIR}\" | cut -f1"
echo "   command: ${COMMAND}"
DU_EXCLUDED="$(eval "${COMMAND}")"
DU_PLAIN="$(du -sb "${APPLICATION_DIR}" | cut -f1)"
printf '   du WITHOUT excludes : %12d bytes\n' "${DU_PLAIN}"
printf '   du AS THE SCRIPT RUNS IT: %12d bytes\n' "${DU_EXCLUDED}"

echo
echo "=============================================================="
echo "3. The tar path (direct array expansion -- quotes stay literal)"
echo "=============================================================="
TAR_ARGS=( "${EXCLUDE_DIRS_ARG[@]}" "--ignore-failed-read" )
tar -cf "${WORK}/as_shipped.tar" "${TAR_ARGS[@]}" -C "${PROJECT_DIR}" "${APPLICATION_NAME}"
AS_SHIPPED=$(stat -c%s "${WORK}/as_shipped.tar")
AS_SHIPPED_HITS=$(tar -tf "${WORK}/as_shipped.tar" | grep -cE '/(data|logs)/' || true)
printf '   archive size            : %12d bytes\n' "${AS_SHIPPED}"
printf '   excluded-dir members    : %12d  <-- should be 0\n' "${AS_SHIPPED_HITS}"

echo
echo "=============================================================="
echo "4. Isolating each of the two faults"
echo "=============================================================="
# 4a: drop the literal quotes, KEEP the absolute path.
ABS_ARGS=()
for _d in "${EXCLUDE_DIRS_VALIDATED[@]}"; do ABS_ARGS+=( "--exclude=${_d}" ); done
tar -cf "${WORK}/abs.tar" "${ABS_ARGS[@]}" -C "${PROJECT_DIR}" "${APPLICATION_NAME}"
ABS=$(stat -c%s "${WORK}/abs.tar")
ABS_HITS=$(tar -tf "${WORK}/abs.tar" | grep -cE '/(data|logs)/' || true)
printf '   4a quotes removed, ABSOLUTE path : %10d bytes, %d excluded members\n' "${ABS}" "${ABS_HITS}"

# 4b: drop the quotes AND anchor relative to the leaf -- the correct form.
REL_ARGS=()
for _d in "${EXCLUDE_DIRS[@]}"; do REL_ARGS+=( "--exclude=${APPLICATION_NAME}/${_d}" ); done
tar -cf "${WORK}/rel.tar" "${REL_ARGS[@]}" -C "${PROJECT_DIR}" "${APPLICATION_NAME}"
REL=$(stat -c%s "${WORK}/rel.tar")
REL_HITS=$(tar -tf "${WORK}/rel.tar" | grep -cE '/(data|logs)/' || true)
printf '   4b quotes removed, RELATIVE path : %10d bytes, %d excluded members\n' "${REL}" "${REL_HITS}"

echo
echo "=============================================================="
echo "5. Verdict"
echo "=============================================================="
printf '   du reports        : %12d bytes\n' "${DU_EXCLUDED}"
printf '   tar actually wrote: %12d bytes\n' "${AS_SHIPPED}"
if (( AS_SHIPPED > DU_EXCLUDED * 2 )); then
    printf '   DIVERGENT: tar archived %sx what du predicted.\n' "$(( AS_SHIPPED / (DU_EXCLUDED > 0 ? DU_EXCLUDED : 1) ))"
    echo "   The exclude list is INERT for tar and LIVE for du. Defect confirmed on main."
else
    echo "   du and tar agree -- defect NOT reproduced."
fi

echo
echo "=============================================================="
echo "6. TAR_EXT vs. compressor (the .tgz-is-a-lie defect)"
echo "=============================================================="
tar -cjf "${WORK}/mislabelled.tgz" -C "${PROJECT_DIR}" "${APPLICATION_NAME}/src"
printf '   file(1) says: %s\n' "$(file -b "${WORK}/mislabelled.tgz")"
if tar -xzf "${WORK}/mislabelled.tgz" -C "${WORK}" 2>/dev/null; then
    echo "   documented restore (tar -xzf): OK"
else
    echo "   documented restore (tar -xzf): FAILS  <-- every archive this script writes"
fi
if tar -xjf "${WORK}/mislabelled.tgz" -C "${WORK}" 2>/dev/null; then
    echo "   actual format    (tar -xjf): OK"
fi
