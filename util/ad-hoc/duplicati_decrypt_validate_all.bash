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
#
# DEST is REQUIRED and the mount guard is DERIVED from it. Until 2026-08-30 this
# script defaulted to the pre-migration destination and asserted a hardcoded
# `mountpoint -q /media/pcalnon/temp_backups` that $1 could not influence -- so it
# guarded a filesystem it was not reading, and would have refused every
# destination once that scratch mount went away (note 8.20.3).

set -uo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: $0 DEST [CRED_FILE] [CRED_KEY] [gpg|aes]" >&2
    echo "  DEST is REQUIRED -- no default, deliberately (note 8.21)." >&2
    echo "  Live Yamaguchi set : /mnt/Backups/Ubuntu/Yamaguchi        (aes)" >&2
    echo "  Old gpg fresh set  : /media/pcalnon/temp_backups/Ubuntu   (gpg)" >&2
    exit 2
fi

DEST="$1"
CRED_FILE="${2:-${HOME}/.config/duplicati-backup/env}"
CRED_KEY="${3:-PASSPHRASE}"
ENCRYPTION="${4:-gpg}"   # gpg | aes (aes: SharpAESCrypt, rc3=HMAC mismatch rc4=bad password)

# Containing mountpoint of $1, found by walking up; prints "/" when nothing else
# matches. Mirrors mount_point_of() in duplicati_dlist_crosscheck.py.
mount_point_of() {
    local p
    p="$(readlink -f "$1")"
    while [[ "${p}" != "/" ]] && ! mountpoint -q "${p}"; do
        p="$(dirname "${p}")"
    done
    printf '%s\n' "${p}"
}

[[ -d "${DEST}" ]] || { echo "FATAL: no such destination ${DEST}" >&2; exit 2; }
DEST_MP="$(mount_point_of "${DEST}")"
if [[ "${DEST_MP}" == "/" ]]; then
    echo "FATAL: destination ${DEST} is not on a mounted filesystem (walked up to /)" >&2
    exit 2
fi

PASS="$(grep -E "^(export[[:space:]]+)?${CRED_KEY}=" "${CRED_FILE}" | head -1 | cut -d= -f2-)"
PASS="${PASS%\"}"; PASS="${PASS#\"}"
[[ -n "${PASS}" ]] || { echo "FATAL: no ${CRED_KEY}= in ${CRED_FILE}" >&2; exit 2; }
echo "credential : ${CRED_FILE} key=${CRED_KEY} (sha256[:16]=$(printf '%s' "${PASS}" | sha256sum | cut -c1-16))"
echo "destination: ${DEST}"
echo "dest mount : ${DEST_MP}"

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
# Zero volumes is an OPERATIONAL failure, not a pass. Until 2026-08-30 an empty
# destination fell through to "ALL VOLUMES DECRYPT-VALID" and exit 0 -- a vacuous
# pass, and precisely what an unmounted, mistyped, or wrong-ENCRYPTION destination
# looks like. The hardcoded mount gate was the accidental proxy for this check;
# de-drifting that gate without adding this would have widened the hole.
if (( total == 0 )); then
    echo "RESULT: NO VOLUMES FOUND -- no ${GLOB} in ${DEST}"
    echo "        (refusing to report a clean validation over an empty set;"
    echo "         check the destination path and the encryption argument)"
    exit 2
fi
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
