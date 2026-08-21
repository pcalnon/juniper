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
#     Archive the Juniper project tree and encrypt it to an external drive, in one streamed pass.
#
#     Encryption is ASYMMETRIC (`gpg -r <recipient> -e`), to the YubiKey-backed public key. That
#     means the YubiKey is NOT required to run this script -- only to RESTORE. Which is also the
#     risk: lose the YubiKey and every archive it produced is unrecoverable. Keep a revocation
#     certificate and/or a second recipient off-device.
#
# Usage:
#     util/juniper-backup.bash [--dry-run] [--source DIR] [--dest DIR]
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
#     THE BUG THIS REPLACES: the draft assigned `ENCRPYTED` but the gpg line read `${ENCRYPTED}`.
#     Undefined, so it expanded to empty, so `gpg -o ""`. Nothing ever landed on the drive, and
#     with no `set -u` the script exited 0 while doing so. Hence: no .tar* artifact exists anywhere
#     on this host. Both spellings are now gone; there is one variable, used once.
#######################################################################################################################################################################################################################################################

set -euo pipefail


#######################################################################################################################################################################################################################################################
# Environment constants
DEVELOPMENT_NAME="Development"
LANGUAGE_NAME="python"
PROJECT_NAME="Juniper"

MOUNT_NAME="media"
USER_NAME="pcalnon"
MEDIA_NAME="DFF3-2782"

TAR_EXT="tgz"
GPG_EXT="gpg"

ENCRYPT_KEY="Paul Calnon (PaulCalnon_overtoad.research@gmail.com_Yubikey-3c_2026-08-06) <paul.calnon@gmail.com>"


#######################################################################################################################################################################################################################################################
# Derived paths
ROOT_DIR="${HOME}/${DEVELOPMENT_NAME}/${LANGUAGE_NAME}"
PROJECT_DIR="${ROOT_DIR}/${PROJECT_NAME}"
EXT_DRIVE="/${MOUNT_NAME}/${USER_NAME}/${MEDIA_NAME}"

DRY_RUN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --source)  PROJECT_DIR="${2:?--source requires a DIR}"; shift 2 ;;
        --dest)    EXT_DRIVE="${2:?--dest requires a DIR}"; shift 2 ;;
        -h|--help) sed -n '12,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

DATE_STAMP="$(date +%Y%m%d_%H%M%S.%N-%Z)"
UUID_VALUE="$(uuidgen)"

ARCHIVE_ROOT="${PROJECT_NAME}_${UUID_VALUE}_${DATE_STAMP}"
GPG_FILE="${ARCHIVE_ROOT}.${TAR_EXT}.${GPG_EXT}"
GPG_PATH="${EXT_DRIVE}/${GPG_FILE}"

SOURCE_PARENT="$(dirname "${PROJECT_DIR}")"
SOURCE_LEAF="$(basename "${PROJECT_DIR}")"


#######################################################################################################################################################################################################################################################
# Preflight -- every one of these is a way the draft failed silently
[[ -d "${PROJECT_DIR}" ]] || { echo "FATAL: source not found: ${PROJECT_DIR}" >&2; exit 1; }

# The destination is a REMOVABLE drive. If it is not mounted, ${EXT_DRIVE} may still exist as an
# empty stale mountpoint -- writing there fills the system disk instead and looks like success.
if ! mountpoint -q "${EXT_DRIVE}" 2>/dev/null; then
    echo "FATAL: ${EXT_DRIVE} is not a mount point -- is the external drive attached?" >&2
    echo "       (writing to an unmounted path would silently fill the system disk)" >&2
    exit 1
fi
[[ -w "${EXT_DRIVE}" ]] || { echo "FATAL: not writable: ${EXT_DRIVE}" >&2; exit 1; }

gpg --list-keys "${ENCRYPT_KEY}" >/dev/null 2>&1 \
    || { echo "FATAL: gpg recipient not found: ${ENCRYPT_KEY}" >&2; exit 1; }

SOURCE_KB="$(du -sk "${PROJECT_DIR}" | cut -f1)"
DEST_KB="$(df -Pk "${EXT_DRIVE}" | awk 'NR==2 {print $4}')"
echo "source: ${PROJECT_DIR}  ($(( SOURCE_KB / 1024 / 1024 )) GiB uncompressed)"
echo "dest:   ${GPG_PATH}"
echo "free:   $(( DEST_KB / 1024 / 1024 )) GiB on ${EXT_DRIVE}"
if (( DEST_KB < SOURCE_KB / 2 )); then
    echo "WARNING: destination free space is under half the uncompressed source size." >&2
    echo "         gzip on this tree does not reliably reach 2:1 -- it is mostly .h5 and .npz." >&2
fi

if (( DRY_RUN )); then
    echo "[dry-run] would run: tar -czf - -C ${SOURCE_PARENT} ${SOURCE_LEAF} | gpg -r <key> -e -o ${GPG_PATH}"
    exit 0
fi


#######################################################################################################################################################################################################################################################
# Archive + encrypt, streamed. A partial output on failure is removed rather than left to look
# like a backup.
cleanup_partial() {
    local rc=$?
    if (( rc != 0 )) && [[ -f "${GPG_PATH}" ]]; then
        echo "FAILED (exit ${rc}) -- removing partial archive ${GPG_PATH}" >&2
        rm -f "${GPG_PATH}"
    fi
    return "${rc}"
}
trap cleanup_partial EXIT

# -C so paths are stored relative to the parent ("Juniper/..."), not as absolute paths that tar
# would strip with a warning and that restore into an unexpected location.
tar -czf - -C "${SOURCE_PARENT}" "${SOURCE_LEAF}" \
    | gpg --batch --yes -r "${ENCRYPT_KEY}" -e -o "${GPG_PATH}"


#######################################################################################################################################################################################################################################################
# Verify. `--list-packets` parses the OpenPGP structure and confirms the recipient key id WITHOUT
# needing the YubiKey, so it is safe to run unattended. It does NOT prove the tar inside is intact
# -- a real restore drill is the only thing that does, and that belongs in the backup design arc.
[[ -s "${GPG_PATH}" ]] || { echo "FATAL: archive is empty: ${GPG_PATH}" >&2; exit 1; }

if gpg --list-packets --list-only "${GPG_PATH}" >/dev/null 2>&1; then
    echo "verified: valid OpenPGP message"
else
    echo "FATAL: output is not a parseable OpenPGP message: ${GPG_PATH}" >&2
    exit 1
fi

sync
echo "OK  $(du -h "${GPG_PATH}" | cut -f1)  ${GPG_PATH}"
