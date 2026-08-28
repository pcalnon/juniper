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
#     Archive the Juniper project tree ONE APPLICATION REPO PER ARCHIVE, encrypt each once, and
#     replicate each to every attached external drive.
#
#     Every repo listed in APPLICATION_REPOS becomes its own encrypted tarball. All archives from a
#     single run share one UUID and one timestamp, which is what groups them into one backup SET --
#     restoring a coherent snapshot means taking every archive bearing the same UUID.
#
#     Archives are bzip2 (`tar -cjf`) and named `.tbz2.gpg`. RESTORE:
#
#         gpg -d Juniper_<repo>_<uuid>_<stamp>.tbz2.gpg | tar -xjf -
#
#     Note -xjf, not -xzf. An earlier revision named these archives `.tgz` while writing bzip2, so
#     the documented gzip restore failed on every archive it produced. TAR_COMPRESS_FLAG and TAR_EXT
#     are now defined together and the dry-run preview is rendered from them.
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
#     --dest DIR overrides the MEDIA_NAMES fan-out entirely and writes one archive PER REPO to DIR.
#
# Exit codes:
#     0  every configured device received a verified archive OF EVERY REPO
#     1  fatal -- nothing was written (bad source, no usable device, missing recipient, build failed)
#     2  misuse (bad argument)
#     4  PARTIAL -- fewer archive copies landed than expected, across all repos and devices.
#        Deliberately non-zero: degraded redundancy must be visible to cron, not silent.
#        Judged on CROSS-REPO totals; per-repo counters alone let a mid-run failure report COMPLETE.
#
#######################################################################################################################################################################################################################################################
# Notes:
#     date +%Y%m%d_%H%M%S.%N-%Z : 20260821_085919.898543514-CDT
#
#     STREAMED, not staged. The original draft wrote a full plaintext .tgz to ${TOOL_DIR}/Juniper_<uuid>/ and then encrypted it.
#       Two problems with that: it needs as much free scratch space as the tree is large (~126 GB today), and it leaves an unencrypted copy of the entire project on local disk until something removes it -- nothing did.
#       Piping tar into gpg removes both. `set -o pipefail` is what makes the pipe safe to rely on.
#
#     BUILD ONCE, REPLICATE. The multi-device revision originally ran the whole `tar | gpg -e` pipeline once PER DEVICE -- reading, compressing and encrypting the tree twice.
#       It now builds each repo's archive to the first usable device and COPIES the finished ciphertext to the rest. Every device therefore holds a byte-identical archive under one filename (same UUID and timestamp), which is also what makes "these two files are the same backup" checkable.
#
#     SILENT EXCLUSION, THREE TIMES. `tar --exclude` and `du --exclude` both accept a malformed pattern, match nothing, and exit 0 -- so a broken exclude list is invisible unless you measure the OUTPUT SIZE.
#       Three revisions shipped one: a space-joined string quoted into a single argv element; then `printf '--exclude="%s" '`, which bakes literal quote characters into the value; and in both cases an ABSOLUTE pattern that cannot match the RELATIVE member names `tar -C` stores.
#       All three were shellcheck-clean. The `du` side masked it further by running its flags through `eval`, which re-parsed the quotes away -- so du reported ~205 MB while tar wrote ~103 GB of the same repo.
#       There is now ONE relative pattern list (`build_exclude_dirs_arg`) consumed by BOTH `du` and `tar` from the same working directory. Regression: util/ad-hoc/2026-08-28_exclude_arg_repro.bash.
#
#     THE BUG THIS REPLACES: the draft assigned `ENCRPYTED` but the gpg line read `${ENCRYPTED}`.
#       Undefined, so it expanded to empty, so `gpg -o ""`. Nothing ever landed on the drive, and with no `set -u` the script exited 0 while doing so. Both spellings are now gone; there is one variable, used once.
#
#     THE SECOND BUG OF THAT CLASS, and why the loop below recomputes its target:
#       The multi-device revision computed `GPG_PATH` ONCE from `MEDIA_NAMES[0]` and then reassigned only `EXT_DRIVE` inside the loop.
#       Both iterations wrote the SAME path on the FIRST drive, the second `gpg --yes` silently clobbered the first, and the second drive received nothing -- while the log printed the second drive's name and "OK".
#       A destination is now derived from its device in one place (`target_dir_for`) and never carried across an iteration.
#
#     MOUNT CHECK IS ON THE MOUNT ROOT, NOT THE BACKUP DIR.
#       Statement `mountpoint -q` is true only for an actual mount point. When `BACKUP_DIR` was appended to `EXT_DRIVE`, the check began testing `<mount>/Juniper-8.0.0.python` -- a plain subdirectory, never a mount point -- so preflight FATALed on every run even with both drives correctly attached.
#       The two questions are now asked separately: is the DEVICE mounted, and does its BACKUP_DIR exist and accept writes.
#######################################################################################################################################################################################################################################################

#######################################################################################################################################################################################################################################################
# Define constants and environment variables for the script.
#######################################################################################################################################################################################################################################################
set -euo pipefail

TRUE="0"
FALSE="1"


#######################################################################################################################################################################################################################################################
# Environment constants
DEVELOPMENT_NAME="Development"
LANGUAGE_NAME="python"
PROJECT_NAME="Juniper"
APPLICATION_REPOS=( "juniper-canopy" "juniper-cascor" "juniper-cascor-client" "juniper-cascor-worker" "juniper-data" "juniper-data-client" "juniper-deploy" "juniper-ml" "juniper-recurrence" "juniper-slacker" )

#######################################################################################################################################################################################################################################################
# Exclude directories from the backup
# Named for what it DOES. The previous name said INCLUDE_CASCOR_SNAPSHOTS while setting it to TRUE *added* cascor-snapshots to the
#   EXCLUDE list -- so the flag did the opposite of its name, and reading it told you the wrong thing about the archive's contents.
#   FALSE (current, deliberate): cascor-snapshots IS archived. It is ~1.7 GB / 28k files and is the corpus the snapshot arc depends on.
EXCLUDE_CASCOR_SNAPSHOTS="${FALSE}"

EXCLUDE_DIRS=( ".amp" ".benchmarks" ".claude" ".mypy_cache" ".playwright-mcp" ".pytest_cache" ".ruff_cache" ".serena" ".trunk" "dist" "logs" "reports" "resources" "data" "build" "venv" )
EXCLUDE_DIRS_ARG=()

if [[ "${EXCLUDE_CASCOR_SNAPSHOTS:-${FALSE}}" == "${TRUE}" ]]; then
    EXCLUDE_DIRS=( "${EXCLUDE_DIRS[@]}" "cascor-snapshots" )
fi


#######################################################################################################################################################################################################################################################
# Every attached device named here receives a copy of the SAME archive. Order matters only in that the first usable device is the one the archive is BUILT on; the rest are copies of it.
MEDIA_NAMES=( "EBC5-F0A3" "DFF3-2782" )
MOUNT_NAME="media"
USER_NAME="pcalnon"
BACKUP_DIR="Juniper-8.0.0.python"


#######################################################################################################################################################################################################################################################
# Derived paths
ROOT_DIR="${HOME}/${DEVELOPMENT_NAME}/${LANGUAGE_NAME}"
PROJECT_DIR="${ROOT_DIR}/${PROJECT_NAME}"


#######################################################################################################################################################################################################################################################
# Define archive naming. Computed ONCE so that every device holds the same filename for one backup.
DATE_STAMP="$(date +%Y%m%d_%H%M%S.%N-%Z)"
UUID_VALUE="$(uuidgen)"


#######################################################################################################################################################################################################################################################
# Define constants for the script.
ORDER_OF_MAGNITUDE_LABELS=("B" "KB" "MB" "GB" "TB" "PB" "EB" "ZB" "YB")
ORDER_OF_MAGNITUDE=1024

# The extension MUST name the compressor the build actually uses. It previously said "tgz" while the build ran `tar -cjf` (bzip2), so
#   every archive this script wrote was undecompressable by the documented `gpg -d | tar -xzf -` restore recipe. An archive that exists
#   and does not restore is the worst failure a backup tool has. TAR_COMPRESS_FLAG and TAR_EXT are defined adjacently, and the dry-run
#   preview is rendered FROM them, so the name and the format cannot drift apart again.
TAR_COMPRESS_FLAG="-j"      # bzip2  -- paired with TAR_EXT below
TAR_EXT="tbz2"              # restore: gpg -d <archive> | tar -xjf -
GPG_EXT="gpg"


#######################################################################################################################################################################################################################################################
# Define tar arguments
IGNORE_FAILED_READ_ARG="--ignore-failed-read"

EXCLUDE_BACKUPS_ARG="--exclude-backups"
# --exclude-caches-all drops the CACHEDIR.TAG directory entirely; --exclude-caches-under drops its contents but keeps the directory.
#   Passing both is redundant and the weaker one only muddies intent, so only the total form is used.
EXCLUDE_CACHES_ALL_ARG="--exclude-caches-all"
# EXCLUDE_VCS_ARG="--exclude-vcs"

EXCLUDE_ARGS=( "${EXCLUDE_BACKUPS_ARG}" "${EXCLUDE_CACHES_ALL_ARG}" )


#######################################################################################################################################################################################################################################################
# MULTIPLE RECIPIENTS, deliberately. gpg encrypts a session key to each, so ANY ONE of these keys can decrypt the archive independently.
#   This is the mitigation for the restore-side single point of failure: `gpg -r <pub> -e` needs no YubiKey to WRITE a backup, only to READ one -- so with a single recipient, losing that one key makes every archive it ever produced unrecoverable.
#   Cost of an extra recipient is a few hundred bytes per archive, once. Add more here rather than re-encrypting later; you cannot retro-fit a recipient onto archives already written.
ENCRYPT_KEYS=(
    "Paul Calnon (PaulCalnon_overtoad.research@gmail.com_Yubikey-3c_2026-08-06) <paul.calnon@gmail.com>"
    "Paul Calnon (PaulCalnon_overtoad.research@gmail.com_Yubikey-3a_2026-08-11) <paul.calnon@gmail.com>"
)


#######################################################################################################################################################################################################################################################
# Parse and Validate Command line arguments
#######################################################################################################################################################################################################################################################
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
# Define functions to be used throughout the script.
#######################################################################################################################################################################################################################################################

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
}

#######################################################################################################################################################################################################################################################
# Build the exclude flags for ONE application repo, as a real argv array.
#
#   THE THIRD BUG OF THE SILENT-EXCLUSION CLASS. Two earlier revisions produced exclude flags that tar accepted and ignored, so the
#   archive silently contained everything the exclude list named. Both were invisible to shellcheck. Neither made tar complain.
#
#     rev 1  a single space-joined string, array-quoted at two of its three call sites, so tar saw ONE run-on pattern.
#     rev 2  `printf -- '--exclude="%s" '` -- which bakes LITERAL double-quote characters and a trailing space INTO the argv value.
#            tar then searched for a path beginning with a `"` character. Nothing matches that, ever.
#
#   Quoting is a shell-PARSE artifact, not part of a value. An argv element must hold the pattern and nothing else. The `"` only ever
#   disappeared on the `du` side because that path ran the string back through `eval`, which re-parsed the quotes away -- which is
#   exactly WHY du and tar disagreed about what was excluded. That divergence WAS the bug: du sized ~205 MB while tar wrote ~103 GB.
#
#   The pattern must also be RELATIVE, not an absolute realpath. `tar -C <parent> <leaf>` stores members as "<leaf>/...", and tar
#   matches --exclude against the stored MEMBER NAME. An absolute pattern cannot match a relative member name, so removing the quotes
#   alone still left the excludes inert -- proved in util/ad-hoc/2026-08-28_exclude_arg_repro.bash step 4a.
#
#   Emitting "<leaf>/<name>" also anchors each pattern to the repo's TOP level, matching what the `-d` test below actually checked. An
#   unanchored bare "<name>" matches at ANY depth, which would silently drop src/**/data/ and src/**/build/ -- source loss, not cache loss.
#
#   ONE list feeds BOTH consumers. `du` is run from ${PROJECT_DIR} against the same relative leaf, so it constructs the same
#   "<leaf>/..." names tar stores and the same patterns apply. Structurally, du and tar can no longer disagree.
EXCLUDE_DIRS_ARG=()
function build_exclude_dirs_arg() {
    local application_leaf="$1"
    local exclude_dirs_arg=()
    local exclude_dir=""
    for exclude_dir in "${EXCLUDE_DIRS[@]}"; do
        if [[ -d "${PROJECT_DIR}/${application_leaf}/${exclude_dir}" ]]; then
            exclude_dirs_arg+=( "--exclude=${application_leaf}/${exclude_dir}" )
        fi
    done
    EXCLUDE_DIRS_ARG=( "${exclude_dirs_arg[@]}" )
    return 0
}

#######################################################################################################################################################################################################################################################
# Uncompressed size of one repo, measured with the SAME exclude flags tar will be given, from the SAME working directory.
#   Never re-derive the flags here and never route them through `eval`; that is precisely how the two paths drifted apart before.
function repo_source_bytes() {
    local application_leaf="$1"
    ( cd "${PROJECT_DIR}" && du -sb "${EXCLUDE_DIRS_ARG[@]}" "${application_leaf}" | cut -f1 )
}

#######################################################################################################################################################################################################################################################
# Get the order of magnitude of a given directory tree size in bytes and display it in a human-readable format. This function echo's output for use with command substitution.
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
#   Only ${IN_PROGRESS} is removed. Archives already written AND verified on earlier devices are deliberately KEPT: if device 2 fails, a good archive on device 1 is exactly what a backup tool exists to have produced, and deleting it would turn a partial success into a total loss.
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
# Where a given device's archive goes. ONE definition, so a destination can never be carried over from a previous loop iteration (see "THE SECOND BUG OF THAT CLASS" above).
function target_dir_for() {
    printf '%s\n' "/${MOUNT_NAME}/${USER_NAME}/$1/${BACKUP_DIR}"
}

#######################################################################################################################################################################################################################################################
# Validate one device and report why it is unusable. Returns 0 if writable, 1 otherwise.
#   The mount check is on the MOUNT ROOT: `mountpoint -q` is only ever true of an actual mount point, so asking it about the BACKUP_DIR subdirectory is always false. Without the mount check, an unmounted drive leaves a stale empty directory and the archive silently fills the system disk.
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
# Verify an archive WITHOUT a YubiKey. `--list-packets` parses the OpenPGP structure and confirms the recipient key ids, so it is safe to run unattended.
#   It does NOT prove the tar inside is intact. The PIPELINE that produces it was proven byte-for-byte on 2026-08-26 by util/ad-hoc/2026-08-26_backup_restore_drill.bash; what remains unproven is that the owner's YubiKey-backed key can decrypt a REAL archive. See the lifecycle design SS6.4.2 q3.
function verify_archive() {
    local path="$1"
    [[ -s "${path}" ]] || { echo "FATAL: archive is empty: ${path}" >&2; return 1; }
    if ! gpg --list-packets --list-only "${path}" >/dev/null 2>&1; then
        echo "FATAL: output is not a parseable OpenPGP message: ${path}" >&2
        return 1
    fi
    # Count the pubkey-encrypted session-key packets. One per recipient -- so this proves the redundancy actually landed, rather than assuming it did because the command line asked for it.
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
#######################################################################################################################################################################################################################################################

#######################################################################################################################################################################################################################################################
# Validate project directory.
[[ -d "${PROJECT_DIR}" ]] || { echo "FATAL: source not found: ${PROJECT_DIR}" >&2; exit 1; }

#######################################################################################################################################################################################################################################################
# Validate application repos.
check_application_repos
(( ${#APPLICATION_REPOS_ARGS[@]} == 0 )) && { echo "FATAL: no application repos found" >&2; exit 1; }
echo "application repos args: ${APPLICATION_REPOS_ARGS[*]}"

#######################################################################################################################################################################################################################################################
# Every recipient must resolve BEFORE we spend an hour building a tarball. A missing key here is also the failure that would quietly halve the redundancy this list exists to provide. Device independent, so it is checked ONCE rather than per device.
GPG_RECIPIENT_ARGS=()
for _key in "${ENCRYPT_KEYS[@]}"; do
    gpg --list-keys "${_key}" >/dev/null 2>&1 || { echo "FATAL: gpg recipient not found: ${_key}" >&2; exit 1; }
    GPG_RECIPIENT_ARGS+=(-r "${_key}")
done
echo "recipients: ${#ENCRYPT_KEYS[@]} (archive is readable by any one of them)"

#######################################################################################################################################################################################################################################################
# Resolve the target list. --dest overrides the fan-out entirely: one explicit directory, validated for writability but not for mount status, because an explicit path is the caller's decision.
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

#######################################################################################################################################################################################################################################################
# A missing drive degrades redundancy; it must not cancel the backup to the drive that IS present. Zero usable devices is the only fatal case.
if (( ${#TARGET_DIRS[@]} == 0 )); then
    echo "FATAL: no usable destination -- is any external drive attached?" >&2
    exit 1
fi


#######################################################################################################################################################################################################################################################
# Validate the archive size and available space on each target device.
#######################################################################################################################################################################################################################################################
for REPO in "${APPLICATION_REPOS_ARGS[@]}"; do
    APPLICATION_NAME="${REPO}"
    APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_NAME}"
    ARCHIVE_ROOT="${PROJECT_NAME}_${APPLICATION_NAME}_${UUID_VALUE}_${DATE_STAMP}"
    GPG_FILE="${ARCHIVE_ROOT}.${TAR_EXT}.${GPG_EXT}"
    build_exclude_dirs_arg "${APPLICATION_NAME}"
    SOURCE_BYTES="$(repo_source_bytes "${APPLICATION_NAME}")"
    echo "source bytes: ${SOURCE_BYTES}"
    SOURCE_SIZE_DISPLAY="$(get_order_of_magnitude_display "${SOURCE_BYTES}")"
    printf 'source: %s  (%s uncompressed)\n' "${APPLICATION_DIR}" "${SOURCE_SIZE_DISPLAY}"
    for _index in "${!TARGET_DIRS[@]}"; do
        DEST_DIR="${TARGET_DIRS[${_index}]}"
        DEST_BYTES="$(df --block-size=1 "${DEST_DIR}" | awk 'NR==2 {print $4}')"
        DEST_SIZE_DISPLAY="$(get_order_of_magnitude_display "${DEST_BYTES}")"
        echo "dest:   ${DEST_DIR}/${GPG_FILE}"
        echo "free:   ${DEST_SIZE_DISPLAY} on ${DEST_DIR}"
        # Two thresholds, because this tree is mostly ALREADY-COMPRESSED .h5 / .npz / .gpg and gzip does not reliably reach 2:1 on it -- it can even expand incompressible input slightly.
        # So "free space >= half the source" is NOT the safe line; "free space >= the whole uncompressed source" is the only one that survives a 1:1 outcome. A single <50% warning let a drive with barely break-even headroom pass silently.
        if (( DEST_BYTES < SOURCE_BYTES / 2 )); then
            echo "WARNING: ${DEST_DIR} has under HALF the uncompressed source size free (${DEST_SIZE_DISPLAY} vs ${SOURCE_SIZE_DISPLAY})." >&2
            echo "         This needs better than 2:1 compression to fit, which this tree does not reliably give." >&2
        elif (( DEST_BYTES < SOURCE_BYTES )); then
            echo "WARNING: ${DEST_DIR} has less free space than the uncompressed source (${DEST_SIZE_DISPLAY} vs ${SOURCE_SIZE_DISPLAY})." >&2
            echo "         It fits only if compression helps; on mostly .h5/.npz content that is not guaranteed." >&2
        fi
    done
    echo "----------------------------------------"
done
echo -ne "\n"


#######################################################################################################################################################################################################################################################
# Perform a dry run if the DRY_RUN flag is set.
#######################################################################################################################################################################################################################################################
if (( DRY_RUN )); then
    for REPO in "${APPLICATION_REPOS_ARGS[@]}"; do
        APPLICATION_NAME="${REPO}"
        APPLICATION_DIR="${PROJECT_DIR}/${APPLICATION_NAME}"
        SOURCE_PARENT="${PROJECT_DIR}"
        SOURCE_LEAF="${APPLICATION_NAME}"
        ARCHIVE_ROOT="${PROJECT_NAME}_${APPLICATION_NAME}_${UUID_VALUE}_${DATE_STAMP}"
        GPG_FILE="${ARCHIVE_ROOT}.${TAR_EXT}.${GPG_EXT}"
        build_exclude_dirs_arg "${APPLICATION_NAME}"
        TAR_ARGS=( "${EXCLUDE_DIRS_ARG[@]}" "${EXCLUDE_ARGS[@]}" "${IGNORE_FAILED_READ_ARG}" )
        echo "tar args: ${TAR_ARGS[*]}"
        # Rendered from the SAME variables the real build uses. The previous preview hardcoded `tar -czf` and a bare `gpg -e` while the
        #   build ran `tar -cjf` with `--compress-algo=none -z 0` -- so --dry-run, the one tool for checking what WOULD happen, described
        #   a pipeline that was never run. A preview that can drift from the build is worse than no preview.
        echo "[dry-run] would build once: tar -c${TAR_COMPRESS_FLAG#-}f - ${TAR_ARGS[*]} -C ${SOURCE_PARENT} ${SOURCE_LEAF} | gpg --batch --yes ${GPG_RECIPIENT_ARGS[*]} --compress-algo=none -z 0 -e -o ${TARGET_DIRS[0]}/${GPG_FILE}"
        echo "[dry-run]   restore with: gpg -d ${GPG_FILE} | tar -x${TAR_COMPRESS_FLAG#-}f -"
        echo "[dry-run]   would archive: $(get_order_of_magnitude_display "$(repo_source_bytes "${APPLICATION_NAME}")") uncompressed"
        for _index in "${!TARGET_DIRS[@]}"; do
            if (( _index == 0 )); then
                echo "[dry-run]   build  -> ${TARGET_DIRS[0]}/${GPG_FILE}"
            else
                echo "[dry-run]   copy   -> ${TARGET_DIRS[${_index}]}/${GPG_FILE}"
            fi
        done
        echo "----------------------------------------"
    done
    # --dry-run PREVIEWS; it must never write. Without this exit, control fell through into the build loop below and --dry-run
    #   produced real encrypted archives on the real destination -- hours of work and ~100 GB written by the one command whose
    #   entire purpose is to tell you what WOULD happen. Caught by util/ad-hoc/2026-08-28_backup_exclude_e2e.bash, which found
    #   twice as many archives as repos and a "COMPLETE: every configured device holds a verified archive" line from a dry run.
    echo "[dry-run] no archives were written."
    exit 0
fi


#######################################################################################################################################################################################################################################################
# Build the compressed, encrypted archive once, on the first usable device, then replicate the finished ciphertext to the remaining devices.
#######################################################################################################################################################################################################################################################

#######################################################################################################################################################################################################################################################
# Build ONCE on the first usable device.  Script uses tar with -C so paths are stored relative to the parent ("Juniper/..."), not as absolute paths that tar would strip with a warning and that restore into an unexpected location.
#######################################################################################################################################################################################################################################################
# Cross-repo accounting. These MUST live outside the per-repo loop.
#   THE FOURTH BUG OF THE REPORT-SUCCESS-PRODUCE-NOTHING CLASS: SUCCEEDED / FAILED_LABELS were reset at the top of each repo iteration,
#   so the final report described only the LAST repo. A copy failure on repo 3 of 10 was erased by repo 4, and the script printed
#   "COMPLETE: every configured device holds a verified archive" over a backup set that was missing an archive.
TOTAL_EXPECTED=0
TOTAL_WRITTEN=0
FAILED_LABELS=()
REPO_REPORT_LINES=()

for REPO in "${APPLICATION_REPOS_ARGS[@]}"; do
    APPLICATION_NAME="${REPO}"
    ARCHIVE_ROOT="${PROJECT_NAME}_${APPLICATION_NAME}_${UUID_VALUE}_${DATE_STAMP}"
    GPG_FILE="${ARCHIVE_ROOT}.${TAR_EXT}.${GPG_EXT}"
    SOURCE_PARENT="${PROJECT_DIR}"
    SOURCE_LEAF="${APPLICATION_NAME}"
    build_exclude_dirs_arg "${APPLICATION_NAME}"
    TAR_ARGS=( "${EXCLUDE_DIRS_ARG[@]}" "${EXCLUDE_ARGS[@]}" "${IGNORE_FAILED_READ_ARG}" )
    BUILD_PATH="${TARGET_DIRS[0]}/${GPG_FILE}"
    IN_PROGRESS="${BUILD_PATH}"
    SUCCEEDED=0
    TOTAL_EXPECTED=$(( TOTAL_EXPECTED + CONFIGURED_COUNT ))

    #######################################################################################################################################################################################################################################################
    # Build the tarball on the first usable device.
    echo "building ${APPLICATION_NAME} tarball on ${TARGET_LABELS[0]} ..."
    tar -c"${TAR_COMPRESS_FLAG#-}"f - "${TAR_ARGS[@]}" -C "${SOURCE_PARENT}" "${SOURCE_LEAF}" | gpg --batch --yes "${GPG_RECIPIENT_ARGS[@]}" --compress-algo=none -z 0 -e -o "${BUILD_PATH}"
    verify_archive "${BUILD_PATH}" || exit 1
    sync
    IN_PROGRESS=""
    SUCCEEDED=1
    TOTAL_WRITTEN=$(( TOTAL_WRITTEN + 1 ))
    echo "OK  $(du -h "${BUILD_PATH}" | cut -f1)  ${BUILD_PATH}"

    #######################################################################################################################################################################################################################################################
    # Replicate the finished ciphertext to all remaining devices. A copy failure on one device leaves every already-verified archive in place and is reported as PARTIAL, never as success.
    for _index in "${!TARGET_DIRS[@]}"; do
        (( _index == 0 )) && continue
        COPY_PATH="${TARGET_DIRS[${_index}]}/${GPG_FILE}"
        IN_PROGRESS="${COPY_PATH}"
        echo "copying to ${TARGET_LABELS[${_index}]} ..."
        if ! cp -- "${BUILD_PATH}" "${COPY_PATH}"; then
            echo "ERROR: copy to ${TARGET_LABELS[${_index}]} failed" >&2
            rm -f "${COPY_PATH}"
            FAILED_LABELS+=("${APPLICATION_NAME}:${TARGET_LABELS[${_index}]}")
            IN_PROGRESS=""
            continue
        fi
        if ! verify_archive "${COPY_PATH}"; then
            echo "ERROR: verification failed on ${TARGET_LABELS[${_index}]}" >&2
            rm -f "${COPY_PATH}"
            FAILED_LABELS+=("${APPLICATION_NAME}:${TARGET_LABELS[${_index}]}")
            IN_PROGRESS=""
            continue
        fi
        sync
        IN_PROGRESS=""
        SUCCEEDED=$(( SUCCEEDED + 1 ))
        TOTAL_WRITTEN=$(( TOTAL_WRITTEN + 1 ))
        echo "OK  $(du -h "${COPY_PATH}" | cut -f1)  ${COPY_PATH}"
    done
    REPO_REPORT_LINES+=("$(printf '  %-24s %d/%d device(s)  %s' "${APPLICATION_NAME}" "${SUCCEEDED}" "${CONFIGURED_COUNT}" "${GPG_FILE}")")
    echo "Completed ${APPLICATION_NAME} tarball replication: ${SUCCEEDED}/${CONFIGURED_COUNT} device(s)"
    echo "----------------------------------------"
done
echo -ne "\n"


#######################################################################################################################################################################################################################################################
# Report. Degraded redundancy exits non-zero so it is visible to cron rather than silent.
#######################################################################################################################################################################################################################################################
echo "----------------------------------------"
echo "backup set: ${UUID_VALUE} ${DATE_STAMP}"
echo "restore:    gpg -d <archive> | tar -x${TAR_COMPRESS_FLAG#-}f -"
echo "per-repo:"
printf '%s\n' "${REPO_REPORT_LINES[@]}"
echo "written and verified: ${TOTAL_WRITTEN} of ${TOTAL_EXPECTED} expected archive copies across ${#APPLICATION_REPOS_ARGS[@]} repo(s)"
if (( ${#FAILED_LABELS[@]} > 0 )); then
    echo "failed: ${FAILED_LABELS[*]}" >&2
fi
# Judged on the CROSS-REPO totals. Judging on the last repo's counters is what let a mid-run failure print COMPLETE.
if (( TOTAL_WRITTEN < TOTAL_EXPECTED )); then
    echo "PARTIAL: redundancy is degraded -- ${TOTAL_WRITTEN} of ${TOTAL_EXPECTED} expected archive copies were written." >&2
    exit 4
fi
echo "COMPLETE: every configured device holds a verified archive of every repo."
echo "----------------------------------------"
echo -ne "\n"
