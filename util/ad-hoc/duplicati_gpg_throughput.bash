#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  util/ad-hoc
# Author:       Paul Calnon
# License:      MIT
############################################################################################################################################################
#
# Measures how long `gpg --symmetric` takes on a Duplicati-sized volume.
#
# WHY THIS EXISTS
#   On 2026-08-23 the fresh backup failed with:
#
#     CryptographicException: Failure while invoking GnuPG, program won't flush
#     output   at Duplicati.Library.Encryption.GPGStreamWrapper.Dispose
#
#   Duplicati's GPG wrapper spawns gpg per volume and waits a bounded time for
#   the child to flush and exit. With --dblock-size=500MB, the encryption of one
#   volume can approach that bound, so the failure appears only under load --
#   208 volumes succeeded before the first failure. This script measures the
#   actual margin instead of reasoning about it.
#
#   The same code path is the best explanation for the earlier hang: threads
#   parked in wait_for_partner / anon_pipe_read with no gpg child alive.
#
# The passphrase is read from a KEY=VALUE file and passed on fd 3, never on the
# command line (/proc/<pid>/cmdline is world-readable) and never printed.
#
# Usage: duplicati_gpg_throughput.bash [size_mb] [cred_file] [cred_key]
############################################################################################################################################################

set -euo pipefail

SIZE_MB="${1:-500}"
CRED_FILE="${2:-${HOME}/.config/duplicati-backup/env}"
CRED_KEY="${3:-PASSPHRASE}"
WORK_DIR="${GPG_BENCH_DIR:-/media/pcalnon/temp_backups/_duplicati_tmp}"

[[ -r "${CRED_FILE}" ]] || { echo "cannot read ${CRED_FILE}" >&2; exit 1; }
mkdir -p "${WORK_DIR}"

PLAIN="${WORK_DIR}/gpgbench-$$.bin"
CIPHER="${WORK_DIR}/gpgbench-$$.gpg"
cleanup() { rm -f "${PLAIN}" "${CIPHER}"; }
trap cleanup EXIT

echo "generating ${SIZE_MB} MiB of incompressible test data in ${WORK_DIR} ..."
dd if=/dev/urandom of="${PLAIN}" bs=1M count="${SIZE_MB}" status=none

PASS="$(grep -E "^(export[[:space:]]+)?${CRED_KEY}=" "${CRED_FILE}" | head -1 | cut -d= -f2-)"
PASS="${PASS%\"}"; PASS="${PASS#\"}"
[[ -n "${PASS}" ]] || { echo "no ${CRED_KEY}= entry in ${CRED_FILE}" >&2; exit 1; }

echo "encrypting with gpg --symmetric (AES256, no compression) ..."
START="$(date +%s.%N)"
printf '%s' "${PASS}" | gpg --batch --yes --quiet \
    --pinentry-mode loopback --passphrase-fd 0 \
    --symmetric --cipher-algo AES256 --compress-algo none \
    -o "${CIPHER}" "${PLAIN}"
END="$(date +%s.%N)"

unset PASS

ELAPSED="$(awk -v a="${START}" -v b="${END}" 'BEGIN{printf "%.2f", b-a}')"
RATE="$(awk -v s="${SIZE_MB}" -v e="${ELAPSED}" 'BEGIN{printf "%.1f", s/e}')"

echo
echo "size    : ${SIZE_MB} MiB"
echo "elapsed : ${ELAPSED} s"
echo "rate    : ${RATE} MiB/s"
echo
echo "Duplicati's GPG wrapper waits a bounded time for the child to exit."
echo "If elapsed is within a small multiple of that bound, --dblock-size is too"
echo "large for this machine under load."
