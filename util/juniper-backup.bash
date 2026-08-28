#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     juniper-backup.bash
# Author:        Paul Calnon
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#     Archive the Juniper project tree, encrypt it once, and replicate it to every attached
#     external drive.
#
#     Encryption is ASYMMETRIC (`gpg -r <recipient> -e`), to YubiKey-backed public keys. So no
#     YubiKey is needed to RUN this script -- only to RESTORE from its output. The consequence is
#     that key loss is a RESTORE-side single point of failure, which is why ENCRYPT_KEYS below holds
#     TWO independent recipients: any one of them can decrypt any archive. Add recipients before
#     writing archives; you cannot retro-fit one onto an archive already written.
#
# Usage:
#     util/juniper-backup.bash [--dry-run] [--source DIR] [--dest DIR]
#
#     --dest DIR overrides the MEDIA_NAMES fan-out entirely and writes exactly one archive to DIR.
#
# Exit codes:
#     0  every configured device received a verified archive
#     1  fatal -- nothing was written (bad source, no usable device, missing recipient, build failed)
#     2  misuse (bad argument)
#     4  PARTIAL -- at least one device has a verified archive, but not all of them do.
#        Deliberately non-zero: degraded redundancy must be visible to cron, not silent.
#
#######################################################################################################################################################################################################################################################
# Notes:
#     date +%Y%m%d_%H%M%S.%N-%Z : 20260821_085919.898543514-CDT
#
#     STREAMED, not staged. The original draft wrote a full plaintext .tgz to
#     ${TOOL_DIR}/Juniper_<uuid>/ and then encrypted it. Two problems with that: it needs as much
#     free scratch space as the tree is large (~126 GB today), and it leaves an unencrypted copy of
#     the entire project on local disk until something removes it -- nothing did. Piping tar into
#     gpg removes both. `set -o pipefail` is what makes the pipe safe to rely on.
#
#     BUILD ONCE, REPLICATE. The multi-device revision originally ran the whole
#     `tar -czf - | gpg -e` pipeline once PER DEVICE -- reading, compressing and encrypting ~126 GB
#     twice. It now builds to the first usable device and COPIES the finished ciphertext to the
#     rest. Every device therefore holds a byte-identical archive under one filename (same UUID and
#     timestamp), which is also what makes "these two files are the same backup" checkable.
#
#     THE BUG THIS REPLACES: the draft assigned `ENCRPYTED` but the gpg line read `${ENCRYPTED}`.
#     Undefined, so it expanded to empty, so `gpg -o ""`. Nothing ever landed on the drive, and
#     with no `set -u` the script exited 0 while doing so. Both spellings are now gone; there is one
#     variable, used once.
#
#     THE SECOND BUG OF THAT CLASS, and why the loop below recomputes its target: the multi-device
#     revision computed `GPG_PATH` ONCE from `MEDIA_NAMES[0]` and then reassigned only `EXT_DRIVE`
#     inside the loop. Both iterations wrote the SAME path on the FIRST drive, the second `gpg
#     --yes` silently clobbered the first, and the second drive received nothing -- while the log
#     printed the second drive's name and "OK". A destination is now derived from its device in one
#     place (`target_path_for`) and never carried across an iteration.
#
#     MOUNT CHECK IS ON THE MOUNT ROOT, NOT THE BACKUP DIR. `mountpoint -q` is true only for an
#     actual mount point. When `BACKUP_DIR` was appended to `EXT_DRIVE`, the check began testing
#     `<mount>/Juniper-8.0.0.python` -- a plain subdirectory, never a mount point -- so preflight
#     FATALed on every run even with both drives correctly attached. The two questions are now asked
#     separately: is the DEVICE mounted, and does its BACKUP_DIR exist and accept writes.
#######################################################################################################################################################################################################################################################

set -euo pipefail

TRUE="0"
FALSE="1"


#######################################################################################################################################################################################################################################################
# Environment constants
DEVELOPMENT_NAME="Development"
LANGUAGE_NAME="python"
PROJECT_NAME="Juniper"
APPLICATION_NAME="juniper-ml"

MOUNT_NAME="media"
USER_NAME="pcalnon"
BACKUP_DIR="Juniper-8.0.0.python"

# Every attached device named here receives a copy of the SAME archive. Order matters only in that
# the first usable device is the one the archive is BUILT on; the rest are copies of it.
MEDIA_NAMES=( "EBC5-F0A3" "DFF3-2782" )

APPLICATION_REPOS=( "juniper-canopy" "juniper-cascor" "juniper-cascor-client" "juniper-cascor-worker" "juniper-data" "juniper-data-client" "juniper-deploy" "juniper-ml" "juniper-recurrence" "juniper-slacker" )
echo "application repos: ${APPLICATION_REPOS[*]}"

ORDER_OF_MAGNITUDE_LABELS=("B" "KB" "MB" "GB" "TB" "PB" "EB" "ZB" "YB")
ORDER_OF_MAGNITUDE=1024

TAR_EXT="tgz"
GPG_EXT="gpg"

# INCLUDE_CASCOR_SNAPSHOTS="${FALSE}"
INCLUDE_CASCOR_SNAPSHOTS="${TRUE}"


#######################################################################################################################################################################################################################################################
# Define tar arguments
IGNORE_FAILED_READ_ARG="--ignore-failed-read"

# Exclude directories from the backup
# EXCLUDE_DIRS=( "dist/" "logs/" "reports/" "resources/" ".claude/worktrees/" ".mypy_cache/" "data/" "venv/" )
# EXCLUDE_DIRS=( ".amp/" ".benchmarks/" ".claude/" ".mypy_cache/" ".playwright-mcp/" ".pytest_cache/" ".ruff_cache/" ".serena/" "dist/" "logs/" "reports/" "resources/" )
EXCLUDE_DIRS=( ".amp" ".benchmarks" ".claude" ".mypy_cache" ".playwright-mcp" ".pytest_cache" ".ruff_cache" ".serena" ".trunk" "dist" "logs" "reports" "resources" "data" "build" "venv" )
if [[ "${INCLUDE_CASCOR_SNAPSHOTS:-${FALSE}}" == "${TRUE}" ]]; then
    EXCLUDE_DIRS=( "${EXCLUDE_DIRS[@]}" "cascor-snapshots" )
fi
EXCLUDE_DIRS_ARG=()

EXCLUDE_BACKUPS_ARG="--exclude-backups"
EXCLUDE_CACHES_ALL_ARG="--exclude-caches-all"
EXCLUDE_CACHES_UNDER_ARG="--exclude-caches-under"
# EXCLUDE_VCS_ARG="--exclude-vcs"

EXCLUDE_ARGS=( "${EXCLUDE_BACKUPS_ARG}" "${EXCLUDE_CACHES_ALL_ARG}" "${EXCLUDE_CACHES_UNDER_ARG}" )
echo "exclude args: ${EXCLUDE_ARGS[*]}"


#######################################################################################################################################################################################################################################################
# MULTIPLE RECIPIENTS, deliberately. gpg encrypts a session key to each, so ANY ONE of these keys
# can decrypt the archive independently. This is the mitigation for the restore-side single point of
# failure: `gpg -r <pub> -e` needs no YubiKey to WRITE a backup, only to READ one -- so with a single
# recipient, losing that one key makes every archive it ever produced unrecoverable.
#
# Cost of an extra recipient is a few hundred bytes per archive, once. Add more here rather than
# re-encrypting later; you cannot retro-fit a recipient onto archives already written.
ENCRYPT_KEYS=(
    "Paul Calnon (PaulCalnon_overtoad.research@gmail.com_Yubikey-3c_2026-08-06) <paul.calnon@gmail.com>"
    "Paul Calnon (PaulCalnon_overtoad.research@gmail.com_Yubikey-3a_2026-08-11) <paul.calnon@gmail.com>"
)


#######################################################################################################################################################################################################################################################
# Derived paths
ROOT_DIR="${HOME}/${DEVELOPMENT_NAME}/${LANGUAGE_NAME}"
PROJECT_DIR="${ROOT_DIR}/${PROJECT_NAME}"


#######################################################################################################################################################################################################################################################
# Parse and Validate Command line arguments
DRY_RUN=0
DEST_OVERRIDE=""

while (( $# > 0 )); do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --source)  PROJECT_DIR="${2:?--source requires a DIR}"; shift 2 ;;
        --dest)    DEST_OVERRIDE="${2:?--dest requires a DIR}"; shift 2 ;;
        -h|--help) sed -n '12,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done


#######################################################################################################################################################################################################################################################
# Define archive naming. Computed ONCE so that every device holds the same filename for one backup.
DATE_STAMP="$(date +%Y%m%d_%H%M%S.%N-%Z)"
UUID_VALUE="$(uuidgen)"


#######################################################################################################################################################################################################################################################
# Validate application repos.
APPLICATION_REPOS_ARGS=()
function check_application_repos() {
    for REPO in "${APPLICATION_REPOS[@]}"; do
        if [[ ! -d "${PROJECT_DIR}/${REPO}" ]]; then
            echo "WARNING: application repo not found: ${PROJECT_DIR}/${REPO}" >&2
            continue
        fi
        APPLICATION_REPOS_ARGS+=("${REPO}")
    done
    echo "application repos args: ${APPLICATION_REPOS_ARGS[*]}"
}


#######################################################################################################################################################################################################################################################
# Validate exclude directories for a given application directory.
EXCLUDE_DIRS_VALIDATED=()

function validate_exclude_dirs() {
    local application_dir="$1"
    local exclude_dirs_array=()
    local current_exclude_dir=""
    local current_exclude_path=""

    for exclude_dir in "${EXCLUDE_DIRS[@]}"; do

        local current_exclude_dir="${application_dir}/${exclude_dir}"
        echo "current exclude path: ${current_exclude_dir}"

        current_exclude_path="$(realpath "${current_exclude_dir}")"
        echo "current exclude path: ${current_exclude_path}"

        # if [[ -d "${application_dir}/${EXCLUDE_DIR}" ]]; then
        if [[ -d "${current_exclude_path}" ]]; then
            # exclude_dirs_arg+=("--exclude ${EXCLUDE_DIR}")
            # exclude_dirs_arg+=("--exclude=./${EXCLUDE_DIR}")
            # exclude_dirs_arg+=("--exclude=${EXCLUDE_DIR}")
            exclude_dirs_array+=("${current_exclude_path}")
        fi
    done

    # printf '%s\n' "${exclude_dirs_array[@]}" | tr '\n' ' '
    printf '%s ' "${exclude_dirs_array[@]}"

    EXCLUDE_DIRS_VALIDATED=( "${exclude_dirs_array[@]}" )

    return 0
}


#######################################################################################################################################################################################################################################################
# Build the exclude directories argument.
EXCLUDE_DIRS_ARG=()

function build_exclude_dirs_arg() {
    local exclude_dirs_arg=()

    echo -ne "0. Exclude Dir Args Number: ${#EXCLUDE_DIRS_VALIDATED[@]}\n\n"
    echo -ne "EXCLUDE_DIRS_VALIDATED: ${EXCLUDE_DIRS_VALIDATED[*]}\n\n"

    # for exclude_dir in "${EXCLUDE_DIRS_VALIDATED[@]}"; do
    #     exclude_dirs_arg+=("--exclude=${exclude_dir}")
    # done
    exclude_dirs_arg=( $(printf -- '--exclude="%s" ' "${EXCLUDE_DIRS_VALIDATED[@]}") )

    echo -ne "1. Exclude Dir Args Number: ${#exclude_dirs_arg[@]}\n\n"
    # printf '%s ' "${exclude_dirs_arg[@]}" | tr '\n' ' '

    echo -ne "exclude dirs arg: ${exclude_dirs_arg[*]}\n\n"

    echo -ne "printf: exclude_dirs_arg[@]\n"
    printf '%s ' "${exclude_dirs_arg[@]}"
    echo -ne "\n"

    echo -ne "2. Exclude Dir Args Number: ${#exclude_dirs_arg[@]}\n\n"

    EXCLUDE_DIRS_ARG=( "${exclude_dirs_arg[@]}" )

    echo -ne "3. Exclude Dir Args Number: ${#EXCLUDE_DIRS_ARG[@]}\n\n"
    echo -ne "EXCLUDE_DIRS_ARG: ${EXCLUDE_DIRS_ARG[*]}\n\n"

    return 0
}


#######################################################################################################################################################################################################################################################
# Get the order of magnitude of a given directory tree size in bytes and display it in a human-readable format.
function get_order_of_magnitude_display() {
    local value="$1"
    local magnitude=0
    while (( value >= ORDER_OF_MAGNITUDE )); do
        value=$( echo "${value} / ${ORDER_OF_MAGNITUDE}" | bc )
        magnitude=$(( magnitude + 1 ))
    done
    echo "${value} ${ORDER_OF_MAGNITUDE_LABELS[${magnitude}]}"
}


#######################################################################################################################################################################################################################################################
# Remove the IN-PROGRESS archive on failure, so a partial write is never left looking like a backup.
#
# Only ${IN_PROGRESS} is removed. Archives already written AND verified on earlier devices are
# deliberately KEPT: if device 2 fails, a good archive on device 1 is exactly what a backup tool
# exists to have produced, and deleting it would turn a partial success into a total loss.
IN_PROGRESS=""
function cleanup_partial() {
    local rc=$?
    if (( rc != 0 )) && [[ -n "${IN_PROGRESS}" && -f "${IN_PROGRESS}" ]]; then
        echo "FAILED (exit ${rc}) -- removing partial archive ${IN_PROGRESS}" >&2
        rm -f "${IN_PROGRESS}"
    fi
    return "${rc}"
}
trap cleanup_partial EXIT


#######################################################################################################################################################################################################################################################
# Where a given device's archive goes. ONE definition, so a destination can never be carried over
# from a previous loop iteration (see "THE SECOND BUG OF THAT CLASS" above).
function target_dir_for() {
    printf '%s\n' "/${MOUNT_NAME}/${USER_NAME}/$1/${BACKUP_DIR}"
}


#######################################################################################################################################################################################################################################################
# Validate one device and report why it is unusable. Returns 0 if writable, 1 otherwise.
#
# The mount check is on the MOUNT ROOT: `mountpoint -q` is only ever true of an actual mount point,
# so asking it about the BACKUP_DIR subdirectory is always false. Without the mount check, an
# unmounted drive leaves a stale empty directory and the archive silently fills the system disk.
function validate_external_media() {
    local media_name="$1"
    local mount_root="/${MOUNT_NAME}/${USER_NAME}/${media_name}"
    local backup_path
    backup_path="$(target_dir_for "${media_name}")"
    if ! mountpoint -q "${mount_root}" 2>/dev/null; then
        echo "  SKIP ${media_name}: ${mount_root} is not a mount point -- drive not attached?" >&2
        echo "       (writing to an unmounted path would silently fill the system disk)" >&2
        return 1
    fi
    if [[ ! -d "${backup_path}" ]]; then
        echo "  SKIP ${media_name}: ${backup_path} does not exist" >&2
        return 1
    fi
    if [[ ! -w "${backup_path}" ]]; then
        echo "  SKIP ${media_name}: not writable: ${backup_path}" >&2
        return 1
    fi
    return 0
}


#######################################################################################################################################################################################################################################################
# Verify an archive WITHOUT a YubiKey. `--list-packets` parses the OpenPGP structure and confirms
# the recipient key ids, so it is safe to run unattended.
#
# It does NOT prove the tar inside is intact. The PIPELINE that produces it was proven byte-for-byte
# on 2026-08-26 by util/ad-hoc/2026-08-26_backup_restore_drill.bash; what remains unproven is that
# the owner's YubiKey-backed key can decrypt a REAL archive. See the lifecycle design SS6.4.2 q3.
function verify_archive() {
    local path="$1"
    [[ -s "${path}" ]] || { echo "FATAL: archive is empty: ${path}" >&2; return 1; }
    if ! gpg --list-packets --list-only "${path}" >/dev/null 2>&1; then
        echo "FATAL: output is not a parseable OpenPGP message: ${path}" >&2
        return 1
    fi
    # Count the pubkey-encrypted session-key packets. One per recipient -- so this proves the
    # redundancy actually landed, rather than assuming it did because the command line asked for it.
    local found
    found="$(gpg --list-packets --list-only "${path}" 2>/dev/null | grep -c '^:pubkey enc packet:' || true)"
    if [[ "${found}" -ne "${#ENCRYPT_KEYS[@]}" ]]; then
        echo "FATAL: archive encrypted to ${found} recipient(s), expected ${#ENCRYPT_KEYS[@]}: ${path}" >&2
        return 1
    fi
    echo "  verified: valid OpenPGP message, ${found} recipient(s)"
    return 0
}


#######################################################################################################################################################################################################################################################
# Preflight -- every one of these is a way the draft failed silently

# Validate project directory.
[[ -d "${PROJECT_DIR}" ]] || { echo "FATAL: source not found: ${PROJECT_DIR}" >&2; exit 1; }

# Validate application repos.
check_application_repos
(( ${#APPLICATION_REPOS_ARGS[@]} == 0 )) && { echo "FATAL: no application repos found" >&2; exit 1; }
echo "application repos args: ${APPLICATION_REPOS_ARGS[*]}"

# Every recipient must resolve BEFORE we spend an hour building a tarball. A missing key here is
# also the failure that would quietly halve the redundancy this list exists to provide. Device
# independent, so it is checked ONCE rather than per device.
GPG_RECIPIENT_ARGS=()
for _key in "${ENCRYPT_KEYS[@]}"; do
    gpg --list-keys "${_key}" >/dev/null 2>&1 || { echo "FATAL: gpg recipient not found: ${_key}" >&2; exit 1; }
    GPG_RECIPIENT_ARGS+=(-r "${_key}")
done
echo "recipients: ${#ENCRYPT_KEYS[@]} (archive is readable by any one of them)"

# Resolve the target list. --dest overrides the fan-out entirely: one explicit directory, validated
# for writability but not for mount status, because an explicit path is the caller's decision.
TARGET_DIRS=()
TARGET_LABELS=()
CONFIGURED_COUNT=0

if [[ -n "${DEST_OVERRIDE}" ]]; then
    CONFIGURED_COUNT=1
    if [[ -d "${DEST_OVERRIDE}" && -w "${DEST_OVERRIDE}" ]]; then
        TARGET_DIRS+=("${DEST_OVERRIDE}")
        TARGET_LABELS+=("--dest")
    else
        echo "FATAL: --dest is not a writable directory: ${DEST_OVERRIDE}" >&2
        exit 1
    fi
else
    CONFIGURED_COUNT="${#MEDIA_NAMES[@]}"
    echo "devices: checking ${CONFIGURED_COUNT} configured"
    for MEDIA_NAME in "${MEDIA_NAMES[@]}"; do
        if validate_external_media "${MEDIA_NAME}"; then
            TARGET_DIRS+=("$(target_dir_for "${MEDIA_NAME}")")
            TARGET_LABELS+=("${MEDIA_NAME}")
            echo "  OK   ${MEDIA_NAME}"
        fi
    done
fi

# A missing drive degrades redundancy; it must not cancel the backup to the drive that IS present.
# Zero usable devices is the only fatal case.
if (( ${#TARGET_DIRS[@]} == 0 )); then
    echo "FATAL: no usable destination -- is any external drive attached?" >&2
    exit 1
fi

for REPO in "${APPLICATION_REPOS_ARGS[@]}"; do
    APPLICATION_NAME="${REPO}"
    APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_NAME}"
    ARCHIVE_ROOT="${PROJECT_NAME}_${APPLICATION_NAME}_${UUID_VALUE}_${DATE_STAMP}"
    GPG_FILE="${ARCHIVE_ROOT}.${TAR_EXT}.${GPG_EXT}"

    # EXCLUDE_DIRS_ARG=("$(validate_exclude_dirs "${APPLICATION_DIR}")")
    # EXCLUDE_DIRS_ARG=( "${$(validate_exclude_dirs "${APPLICATION_DIR}")[@]}" )
    # EXCLUDE_DIRS_VALIDATED="$(validate_exclude_dirs "${APPLICATION_DIR}")"
    validate_exclude_dirs "${APPLICATION_DIR}"

    echo "exclude dirs validated: ${EXCLUDE_DIRS_VALIDATED[*]}"
    echo "exclude dir validated 0: ${EXCLUDE_DIRS_VALIDATED[0]}"
    echo "exclude dir validated 1: ${EXCLUDE_DIRS_VALIDATED[1]}"
    echo "exclude dir validated 2: ${EXCLUDE_DIRS_VALIDATED[2]}"

    # EXCLUDE_DIRS_ARG=( "${EXCLUDE_DIRS_VALIDATED[@]}" )
    build_exclude_dirs_arg

    echo "exclude dirs: ${EXCLUDE_DIRS_ARG[*]}"
    echo "exclude dir 0: ${EXCLUDE_DIRS_ARG[0]}"
    echo "exclude dir 1: ${EXCLUDE_DIRS_ARG[1]}"
    echo "exclude dir 2: ${EXCLUDE_DIRS_ARG[2]}"

    # `du -sk` walks the whole tree and is slow on ~126 GB, so it runs ONCE rather than per device.
    # SOURCE_KB="$(du -sk "${APPLICATION_DIR}" | cut -f1)"
    # - SC2068
    # SOURCE_BYTES="$(du -sb ${EXCLUDE_DIRS_ARG[@]} "${APPLICATION_DIR}" | cut -f1)"
    # SOURCE_BYTES=$(du -sb ${EXCLUDE_DIRS_ARG[@]} "${APPLICATION_DIR}" | cut -f1)
    # SOURCE_BYTES=$(du -sb $(echo "${EXCLUDE_DIRS_ARG[@]}" | tr '\n' ' ') "${APPLICATION_DIR}" | cut -f1)


    echo "1. du -sb \$(printf \"%s \" \"${EXCLUDE_DIRS_ARG[*]}\") \"${APPLICATION_DIR}\" | cut -f1"
    echo "2. du -sb $(printf "%s " "${EXCLUDE_DIRS_ARG[@]}") \"${APPLICATION_DIR}\" | cut -f1"

    echo "du -sb $(printf '%s ' "${EXCLUDE_DIRS_ARG[@]}") \"${APPLICATION_DIR}\" | cut -f1"
    COMMAND="du -sb $(printf '%s ' "${EXCLUDE_DIRS_ARG[@]}") \"${APPLICATION_DIR}\" | cut -f1"
    echo "COMMAND: ${COMMAND}"

    SOURCE_BYTES="$(eval "${COMMAND}")"
    echo "source bytes: ${SOURCE_BYTES}"

    # SOURCE_BYTES="$(du -sb $(printf "%s " "${EXCLUDE_DIRS_ARG[@]}") "${APPLICATION_DIR}" | cut -f1)"
    # echo "source bytes: ${SOURCE_BYTES}"

    SOURCE_SIZE_DISPLAY="$(get_order_of_magnitude_display "${SOURCE_BYTES}")"
    printf 'source: %s  (%s uncompressed)\n' "${APPLICATION_DIR}" "${SOURCE_SIZE_DISPLAY}"

    for _index in "${!TARGET_DIRS[@]}"; do
        DEST_DIR="${TARGET_DIRS[${_index}]}"
        # DEST_BYTES="$(df -Pk "${DEST_DIR}" | awk 'NR==2 {print $4}')"
        # DEST_BYTES="$(df -Pb "${DEST_DIR}" | awk 'NR==2 {print $4}')"
        DEST_BYTES="$(df --block-size=1 "${DEST_DIR}" | awk 'NR==2 {print $4}')"
        DEST_SIZE_DISPLAY="$(get_order_of_magnitude_display "${DEST_BYTES}")"
        echo "dest:   ${DEST_DIR}/${GPG_FILE}"
        # echo "free:   $(( DEST_KB / 1024 / 1024 )) GiB on ${DEST_DIR}"
        echo "free:   ${DEST_SIZE_DISPLAY} on ${DEST_DIR}"
        # Two thresholds, because this tree is mostly ALREADY-COMPRESSED .h5 / .npz / .gpg and gzip does
        # not reliably reach 2:1 on it -- it can even expand incompressible input slightly. So "free
        # space >= half the source" is NOT the safe line; "free space >= the whole uncompressed source"
        # is the only one that survives a 1:1 outcome. A single <50% warning let a drive with barely
        # break-even headroom pass silently.
        if (( DEST_BYTES < SOURCE_BYTES / 2 )); then
            # echo "WARNING: ${TARGET_LABELS[${_index}]} has under HALF the uncompressed source free ($(( DEST_KB / 1024 / 1024 )) GiB vs $(( SOURCE_KB / 1024 / 1024 )) GiB)." >&2
            # echo "WARNING: ${TARGET_LABELS[${_index}]} has under HALF the uncompressed source free ($(( DEST_KB / 1024 / 1024 )) GiB vs $(( SOURCE_KB / 1024 / 1024 )) GiB)." >&2
            echo "WARNING: ${DEST_DIR} has under HALF the uncompressed source size free (${DEST_SIZE_DISPLAY} vs ${SOURCE_SIZE_DISPLAY})." >&2
            echo "         This needs better than 2:1 compression to fit, which this tree does not reliably give." >&2
        elif (( DEST_BYTES < SOURCE_BYTES )); then
            # echo "WARNING: ${TARGET_LABELS[${_index}]} has less free space than the uncompressed source ($(( DEST_KB / 1024 / 1024 )) GiB vs $(( SOURCE_KB / 1024 / 1024 )) GiB)." >&2
            # echo "WARNING: ${TARGET_LABELS[${_index}]} has less free space than the uncompressed source ($(( DEST_KB / 1024 / 1024 )) GiB vs $(( SOURCE_KB / 1024 / 1024 )) GiB)." >&2
            echo "WARNING: ${DEST_DIR} has less free space than the uncompressed source (${DEST_SIZE_DISPLAY} vs ${SOURCE_SIZE_DISPLAY})." >&2
            echo "         It fits only if compression helps; on mostly .h5/.npz content that is not guaranteed." >&2
        fi
    done
    echo "----------------------------------------"
done

if (( DRY_RUN )); then
    for REPO in "${APPLICATION_REPOS_ARGS[@]}"; do
        APPLICATION_NAME="${REPO}"
        APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_NAME}"
        SOURCE_PARENT="${PROJECT_DIR}"
        SOURCE_LEAF="${APPLICATION_NAME}"

        ARCHIVE_ROOT="${PROJECT_NAME}_${APPLICATION_NAME}_${UUID_VALUE}_${DATE_STAMP}"
        GPG_FILE="${ARCHIVE_ROOT}.${TAR_EXT}.${GPG_EXT}"

        EXCLUDE_DIRS_ARG=("$(validate_exclude_dirs "${APPLICATION_DIR}")")
        TAR_ARGS=( "${EXCLUDE_DIRS_ARG[@]}" "${EXCLUDE_ARGS[@]}" "${IGNORE_FAILED_READ_ARG}" )
        echo "tar args: ${TAR_ARGS[*]}"

        echo "[dry-run] would build once: tar -czf - ${TAR_ARGS[*]} -C ${SOURCE_PARENT} ${SOURCE_LEAF} | gpg --batch --yes ${GPG_RECIPIENT_ARGS[*]} -e -o ${TARGET_DIRS[0]}/${GPG_FILE}"
        for _index in "${!TARGET_DIRS[@]}"; do
            if (( _index == 0 )); then
                echo "[dry-run]   build  -> ${TARGET_DIRS[0]}/${GPG_FILE}"
            else
                echo "[dry-run]   copy   -> ${TARGET_DIRS[${_index}]}/${GPG_FILE}"
            fi
        done
        echo "----------------------------------------"
    done
fi


#######################################################################################################################################################################################################################################################
# Build ONCE on the first usable device.
#
# tar with -C so paths are stored relative to the parent ("Juniper/..."), not as absolute paths that
# tar would strip with a warning and that restore into an unexpected location.

# BUILD_PATH="${TARGET_DIRS[0]}/${GPG_FILE}"
# IN_PROGRESS="${BUILD_PATH}"
for REPO in "${APPLICATION_REPOS_ARGS[@]}"; do
    APPLICATION_NAME="${REPO}"
    APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_NAME}"

    ARCHIVE_ROOT="${PROJECT_NAME}_${APPLICATION_NAME}_${UUID_VALUE}_${DATE_STAMP}"
    GPG_FILE="${ARCHIVE_ROOT}.${TAR_EXT}.${GPG_EXT}"

    # SOURCE_PARENT="$(dirname "${APPLICATION_DIR}")"
    SOURCE_PARENT="${PROJECT_DIR}"
    # SOURCE_LEAF="$(basename "${APPLICATION_DIR}")"
    SOURCE_LEAF="${APPLICATION_NAME}"

    # EXCLUDE_DIRS_ARG=()
    EXCLUDE_DIRS_ARG=("$(validate_exclude_dirs "${APPLICATION_DIR}")")
    echo "exclude dirs: ${EXCLUDE_DIRS_ARG[*]}"

    TAR_ARGS=( "${EXCLUDE_DIRS_ARG[@]}" "${EXCLUDE_ARGS[@]}" "${IGNORE_FAILED_READ_ARG}" )
    echo "tar args: ${TAR_ARGS[*]}"

    BUILD_PATH="${TARGET_DIRS[0]}/${GPG_FILE}"
    IN_PROGRESS="${BUILD_PATH}"

    echo "building ${APPLICATION_NAME} tarball on ${TARGET_LABELS[0]} ..."
    echo "tar -cjf - ${TAR_ARGS[*]} -C ${SOURCE_PARENT} ${SOURCE_LEAF} | gpg --batch --yes ${GPG_RECIPIENT_ARGS[*]} --compress-algo=none -z 0 -e -o ${BUILD_PATH}"
    tar -cjf - "${TAR_ARGS[@]}" -C "${SOURCE_PARENT}" "${SOURCE_LEAF}" | gpg --batch --yes "${GPG_RECIPIENT_ARGS[@]}" --compress-algo=none -z 0 -e -o "${BUILD_PATH}"
    verify_archive "${BUILD_PATH}" || exit 1
    sync
    IN_PROGRESS=""
    echo "OK  $(du -h "${BUILD_PATH}" | cut -f1)  ${BUILD_PATH}"

    # echo "building on ${TARGET_LABELS[0]} ..."
    # echo "tar -czf - ${TAR_ARGS[*]} -C ${SOURCE_PARENT} ${SOURCE_LEAF} | gpg --batch --yes ${GPG_RECIPIENT_ARGS[*]} -e -o ${BUILD_PATH} "
    # tar -czf - "${TAR_ARGS[*]}" -C "${SOURCE_PARENT}" "${SOURCE_LEAF}" | gpg --batch --yes "${GPG_RECIPIENT_ARGS[@]}" -e -o "${BUILD_PATH}"
    #
    # verify_archive "${BUILD_PATH}" || exit 1
    # sync
    # IN_PROGRESS=""
    # echo "OK  $(du -h "${BUILD_PATH}" | cut -f1)  ${BUILD_PATH}"

    SUCCEEDED=1
    FAILED_LABELS=()

    APPLICATION_REPOS_ARGS=()

    #######################################################################################################################################################################################################################################################
    # Replicate the finished ciphertext to the remaining devices. A copy failure on one device leaves
    # every already-verified archive in place and is reported as PARTIAL, never as success.
    for _index in "${!TARGET_DIRS[@]}"; do
        (( _index == 0 )) && continue

        COPY_PATH="${TARGET_DIRS[${_index}]}/${GPG_FILE}"
        IN_PROGRESS="${COPY_PATH}"
        echo "copying to ${TARGET_LABELS[${_index}]} ..."

        if ! cp -- "${BUILD_PATH}" "${COPY_PATH}"; then
            echo "ERROR: copy to ${TARGET_LABELS[${_index}]} failed" >&2
            rm -f "${COPY_PATH}"
            FAILED_LABELS+=("${TARGET_LABELS[${_index}]}")
            IN_PROGRESS=""
            continue
        fi

        if ! verify_archive "${COPY_PATH}"; then
            echo "ERROR: verification failed on ${TARGET_LABELS[${_index}]}" >&2
            rm -f "${COPY_PATH}"
            FAILED_LABELS+=("${TARGET_LABELS[${_index}]}")
            IN_PROGRESS=""
            continue
        fi

        sync
        IN_PROGRESS=""
        SUCCEEDED=$(( SUCCEEDED + 1 ))
        echo "OK  $(du -h "${COPY_PATH}" | cut -f1)  ${COPY_PATH}"
    done

    echo "Completed ${APPLICATION_NAME} tarball replication to ${TARGET_LABELS[*]} ..."
    echo "----------------------------------------"
done


#######################################################################################################################################################################################################################################################
# Report. Degraded redundancy exits non-zero so it is visible to cron rather than silent.

echo
echo "archive: ${GPG_FILE}"
echo "written and verified on ${SUCCEEDED} of ${CONFIGURED_COUNT} configured device(s)"

if (( ${#FAILED_LABELS[@]} > 0 )); then
    echo "failed: ${FAILED_LABELS[*]}" >&2
fi

if (( SUCCEEDED < CONFIGURED_COUNT )); then
    echo "PARTIAL: redundancy is degraded -- ${SUCCEEDED} of ${CONFIGURED_COUNT} device(s) hold this archive." >&2
    exit 4
fi

echo "COMPLETE: every configured device holds a verified archive."
