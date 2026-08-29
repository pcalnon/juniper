#!/usr/bin/env bash
#
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# Version:     0.1.0
# License:     MIT License
#
# Decrypt-validate EVERY .gpg volume of a Duplicati destination to /dev/null
# (gpg performs full MDC integrity verification on the stream). Closes the
# ciphertext-authorship residual that whole-file hash comparison cannot: the
# recorded Remotevolume.Hash is the hash of whatever the encryption stage
# wrote, so a garbled-before-hashing stream would pass it — but not this.
#
# Read-only on the destination. Passphrase key named explicitly; only its
# sha256[:16] is logged. Exit 0 = all valid; 1 = any failure; 2 = operational.

set -uo pipefail

DEST="${1:-/media/pcalnon/temp_backups/Ubuntu}"
CRED_FILE="${2:-${HOME}/.config/duplicati-backup/env}"
CRED_KEY="${3:-PASSPHRASE}"
ENCRYPTION="${4:-gpg}"   # gpg | aes (aes: SharpAESCrypt, rc3=HMAC mismatch rc4=bad password)

mountpoint -q /media/pcalnon/temp_backups || { echo "FATAL: scratch fs not mounted" >&2; exit 2; }
[[ -d "${DEST}" ]] || { echo "FATAL: no such destination ${DEST}" >&2; exit 2; }

PASS="$(grep -E "^(export[[:space:]]+)?${CRED_KEY}=" "${CRED_FILE}" | head -1 | cut -d= -f2-)"
PASS="${PASS%\"}"; PASS="${PASS#\"}"
[[ -n "${PASS}" ]] || { echo "FATAL: no ${CRED_KEY}= in ${CRED_FILE}" >&2; exit 2; }
echo "credential : ${CRED_FILE} key=${CRED_KEY} (sha256[:16]=$(printf '%s' "${PASS}" | sha256sum | cut -c1-16))"
echo "destination: ${DEST}"

total=0; bad=0
start="$(date +%s)"
if [[ "${ENCRYPTION}" == "aes" ]]; then
    GLOB='*.aes'
else
    GLOB='*.gpg'
fi
while IFS= read -r f; do
    total=$((total + 1))
    if [[ "${ENCRYPTION}" == "aes" ]]; then
        # password on argv: accepted deviation on this single-user host
        if ! duplicati-aescrypt d "${PASS}" "${DEST}/${f}" /dev/null 2>/tmp/gpg_dv_err.$$; then
            bad=$((bad + 1))
            echo "DECRYPT FAIL: ${f} :: $(head -c 200 /tmp/gpg_dv_err.$$)"
        fi
    elif ! printf '%s\n' "${PASS}" | gpg --batch --quiet --pinentry-mode loopback \
            --passphrase-fd 0 --decrypt "${DEST}/${f}" > /dev/null 2>/tmp/gpg_dv_err.$$; then
        bad=$((bad + 1))
        echo "DECRYPT FAIL: ${f} :: $(head -c 200 /tmp/gpg_dv_err.$$)"
    fi
    if (( total % 40 == 0 )); then
        echo "[$(( $(date +%s) - start ))s] validated ${total} volumes, ${bad} failures"
    fi
done < <(find "${DEST}" -maxdepth 1 -name "${GLOB}" -printf '%f\n' | sort)
rm -f /tmp/gpg_dv_err.$$

echo
echo "validated  : ${total} volumes in $(( $(date +%s) - start ))s"
echo "failures   : ${bad}"
if (( bad == 0 )); then
    if [[ "${ENCRYPTION}" == "aes" ]]; then
        echo "RESULT: ALL VOLUMES DECRYPT-VALID (full HMAC verification)"
    else
        echo "RESULT: ALL VOLUMES DECRYPT-VALID (full MDC verification)"
    fi
    exit 0
fi
echo "RESULT: ${bad} INVALID VOLUME(S)"
exit 1
