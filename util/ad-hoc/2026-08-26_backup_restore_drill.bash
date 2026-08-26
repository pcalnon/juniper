#!/usr/bin/env bash
# Restore drill for util/juniper-backup.bash -- proves the tar SURVIVES the gpg round-trip.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-08-26
# Status:      ad-hoc -- investigation
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:     notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md
#              SS6.4.2 q3 / SS6.4.3 (the drill this answers); util/juniper-backup.bash:173
#
# WHAT THIS ANSWERS
#     juniper-backup.bash line 173 says, of its own two unattended checks:
#
#         "It does NOT prove the tar inside is intact -- a real restore drill is the only
#          thing that does, and that belongs in the backup design arc."
#
#     The lifecycle design (SS6.4.2 q3) then makes that drill a hard precondition for ever
#     revisiting the no-deletion policy, and records that no drill has ever been run.
#
#     A full drill has TWO independent failure classes and only one of them is testable
#     unattended:
#
#       1. PIPELINE  -- does `tar -czf - | gpg -e` round-trip a tree byte-for-byte, and do
#                       the script's two verifications actually fire?   <-- THIS SCRIPT
#       2. KEY       -- can the owner's YubiKey-backed private key decrypt a REAL archive?
#                       Owner-gated: the recipients are YubiKey-backed, so this needs the
#                       hardware and cannot be run unattended. NOT covered here.
#
#     Retiring (1) leaves a precisely-scoped owner action instead of an open-ended "no drill
#     has ever been run".
#
# SAFETY
#     - Uses a THROWAWAY keypair in an isolated $GNUPGHOME under a temp dir. The real keyring
#       is never read and never written. No YubiKey is touched.
#     - Never writes to the external drive, and never invokes juniper-backup.bash itself --
#       it reproduces that script's pipeline verbatim against a synthetic tree.
#     - Everything lands under a mktemp -d that is removed on exit.
#
# NON-VACUITY
#     A drill that only ever passes proves nothing. Phase 5 deliberately CORRUPTS a byte in
#     the ciphertext and asserts the restore FAILS. If that phase does not fail, the drill
#     itself is broken and the script says so.
#
# USAGE
#     bash util/ad-hoc/2026-08-26_backup_restore_drill.bash
#     KEEP_WORKDIR=1 bash util/ad-hoc/2026-08-26_backup_restore_drill.bash   # leave artifacts

set -euo pipefail

WORKDIR="$(mktemp -d -t juniper-restore-drill-XXXXXXXX)"
export GNUPGHOME="${WORKDIR}/gnupg"

cleanup() {
    # gpg-agent holds the socket dir open; stop it before removing, or rm races it.
    if command -v gpgconf >/dev/null 2>&1; then
        gpgconf --kill gpg-agent >/dev/null 2>&1 || true
    fi
    if [[ "${KEEP_WORKDIR:-0}" == "1" ]]; then
        echo "KEEP_WORKDIR=1 -- artifacts left in ${WORKDIR}"
    else
        rm -rf "${WORKDIR}"
    fi
}
trap cleanup EXIT

mkdir -p "${GNUPGHOME}"
chmod 700 "${GNUPGHOME}"

FAILURES=0
pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1" >&2; FAILURES=$((FAILURES + 1)); }

echo "=== Restore drill for util/juniper-backup.bash ==="
echo "workdir: ${WORKDIR}"
echo

#######################################################################################################################################################################################################################################################
# Phase 1 -- a synthetic tree that exercises what a real archive contains.
echo "[1/5] building synthetic source tree"

SRC_PARENT="${WORKDIR}/src"
SRC_LEAF="Juniper"
TREE="${SRC_PARENT}/${SRC_LEAF}"
mkdir -p "${TREE}/nested/deeper" "${TREE}/empty-dir"

# Text, and text with content that compresses well (tar -z is in the pipeline).
printf 'plain ascii content\n' > "${TREE}/plain.txt"
head -c 200000 /dev/zero | tr '\0' 'a' > "${TREE}/compressible.txt"

# Binary, incompressible -- the case where a corrupted stream is most likely to go unnoticed.
head -c 1048576 /dev/urandom > "${TREE}/random.bin"

# An .h5-shaped file, because the archive this protects is 28k HDF5 snapshots.
head -c 65536 /dev/urandom > "${TREE}/nested/cascor_snapshot_20260826_000000_drill.h5"

# Names that a naive tar/shell pipeline mangles.
printf 'unicode payload\n' > "${TREE}/nested/deeper/ünïcödé — name.txt"
printf 'spaces payload\n'  > "${TREE}/nested/deeper/name with spaces.txt"

# Symlinks and permissions: tar preserves them, and a restore that silently flattens a
# symlink into a copy is a real (and quiet) corruption.
ln -s ../../plain.txt "${TREE}/nested/deeper/link-to-plain.txt"
printf '#!/bin/sh\necho drill\n' > "${TREE}/executable.sh"
chmod 755 "${TREE}/executable.sh"

# Manifest BEFORE archiving. Sorted so the comparison is order-independent.
MANIFEST_BEFORE="${WORKDIR}/manifest-before.txt"
( cd "${TREE}" && find . -type f -print0 | sort -z | xargs -0 sha256sum ) > "${MANIFEST_BEFORE}"
PERMS_BEFORE="${WORKDIR}/perms-before.txt"
( cd "${TREE}" && find . -printf '%y %m %p -> %l\n' | sort ) > "${PERMS_BEFORE}"
echo "  $(wc -l < "${MANIFEST_BEFORE}") files, $(du -sh "${TREE}" | cut -f1)"

#######################################################################################################################################################################################################################################################
# Phase 2 -- two throwaway recipients, mirroring ENCRYPT_KEYS' two-recipient redundancy.
echo "[2/5] generating two throwaway GPG recipients (isolated GNUPGHOME)"

for KEY_INDEX in 1 2; do
    gpg --batch --quiet --passphrase '' --pinentry-mode loopback \
        --quick-generate-key "Juniper Drill Key ${KEY_INDEX} <drill${KEY_INDEX}@invalid>" \
        default default never >/dev/null 2>&1
done

# Take the PRIMARY key fingerprint only. `--list-keys` emits an `fpr` record for the primary
# AND for each subkey, so a naive `/^fpr:/` grep reports 4 fingerprints for 2 keys -- and gpg
# then dedupes them back to 2 recipients ("public key already present"), so the count check
# fails against a correct archive. Latch on `pub:` and take the next `fpr:`.
mapfile -t DRILL_FPRS < <(gpg --batch --with-colons --list-keys 2>/dev/null | awk -F: '$1=="pub"{want=1} $1=="fpr" && want {print $10; want=0}')
if [[ "${#DRILL_FPRS[@]}" -lt 2 ]]; then
    echo "FATAL: expected 2 drill keys, got ${#DRILL_FPRS[@]}" >&2
    exit 1
fi
echo "  recipients: ${#DRILL_FPRS[@]}"

GPG_RECIPIENT_ARGS=()
for FPR in "${DRILL_FPRS[@]}"; do
    GPG_RECIPIENT_ARGS+=("-r" "${FPR}")
done

#######################################################################################################################################################################################################################################################
# Phase 3 -- the pipeline, verbatim from juniper-backup.bash, plus its two verifications.
echo "[3/5] archiving via the juniper-backup.bash pipeline"

GPG_PATH="${WORKDIR}/drill.tgz.gpg"
tar -czf - -C "${SRC_PARENT}" "${SRC_LEAF}" | gpg --batch --yes "${GPG_RECIPIENT_ARGS[@]}" -e -o "${GPG_PATH}"

if [[ -s "${GPG_PATH}" ]]; then
    pass "archive is non-empty ($(du -h "${GPG_PATH}" | cut -f1))"
else
    fail "archive is empty"
fi

if gpg --list-packets --list-only "${GPG_PATH}" >/dev/null 2>&1; then
    pass "output is a parseable OpenPGP message"
else
    fail "output is not a parseable OpenPGP message"
fi

FOUND_RECIPIENTS="$(gpg --list-packets --list-only "${GPG_PATH}" 2>/dev/null | grep -c '^:pubkey enc packet:' || true)"
if [[ "${FOUND_RECIPIENTS}" -eq "${#DRILL_FPRS[@]}" ]]; then
    pass "encrypted to ${FOUND_RECIPIENTS} recipient(s), redundancy landed"
else
    fail "encrypted to ${FOUND_RECIPIENTS} recipient(s), expected ${#DRILL_FPRS[@]}"
fi

#######################################################################################################################################################################################################################################################
# Phase 4 -- THE PART THE SCRIPT CANNOT DO: decrypt, untar, and compare byte-for-byte.
echo "[4/5] restoring and comparing"

RESTORE_DIR="${WORKDIR}/restore"
mkdir -p "${RESTORE_DIR}"

if gpg --batch --quiet --decrypt "${GPG_PATH}" 2>/dev/null | tar -xzf - -C "${RESTORE_DIR}"; then
    pass "decrypt | untar completed"
else
    fail "decrypt | untar FAILED -- the archive does not restore"
fi

RESTORED_TREE="${RESTORE_DIR}/${SRC_LEAF}"
MANIFEST_AFTER="${WORKDIR}/manifest-after.txt"
PERMS_AFTER="${WORKDIR}/perms-after.txt"
( cd "${RESTORED_TREE}" && find . -type f -print0 | sort -z | xargs -0 sha256sum ) > "${MANIFEST_AFTER}"
( cd "${RESTORED_TREE}" && find . -printf '%y %m %p -> %l\n' | sort ) > "${PERMS_AFTER}"

if diff -q "${MANIFEST_BEFORE}" "${MANIFEST_AFTER}" >/dev/null; then
    pass "all $(wc -l < "${MANIFEST_BEFORE}") files match by SHA-256"
else
    fail "content mismatch after restore:"
    diff "${MANIFEST_BEFORE}" "${MANIFEST_AFTER}" | head -20 >&2
fi

if diff -q "${PERMS_BEFORE}" "${PERMS_AFTER}" >/dev/null; then
    pass "file types, modes and symlink targets preserved"
else
    fail "type/mode/symlink mismatch after restore:"
    diff "${PERMS_BEFORE}" "${PERMS_AFTER}" | head -20 >&2
fi

#######################################################################################################################################################################################################################################################
# Phase 5 -- NON-VACUITY. Corrupt the ciphertext; the restore MUST fail.
# Without this, a drill that silently restored nothing would still report all-pass.
echo "[5/5] negative control -- corrupting the archive"

CORRUPT_PATH="${WORKDIR}/corrupt.tgz.gpg"
cp "${GPG_PATH}" "${CORRUPT_PATH}"

# Flip bytes deep in the payload, past the OpenPGP header packets, so the damage lands in the
# encrypted stream rather than making the file trivially unparseable.
CORRUPT_AT=$(( $(stat -c%s "${CORRUPT_PATH}") / 2 ))
printf '\xde\xad\xbe\xef' | dd of="${CORRUPT_PATH}" bs=1 seek="${CORRUPT_AT}" conv=notrunc status=none

CORRUPT_RESTORE="${WORKDIR}/restore-corrupt"
mkdir -p "${CORRUPT_RESTORE}"

if gpg --batch --quiet --decrypt "${CORRUPT_PATH}" 2>/dev/null | tar -xzf - -C "${CORRUPT_RESTORE}" 2>/dev/null; then
    fail "corrupted archive restored CLEANLY -- this drill cannot detect corruption"
else
    pass "corrupted archive refused to restore, so the drill discriminates"
fi

#######################################################################################################################################################################################################################################################
echo
if [[ "${FAILURES}" -eq 0 ]]; then
    echo "RESULT: PIPELINE VERIFIED -- tar survives the gpg round-trip byte-for-byte."
    echo "STILL OWED (owner-gated): decrypt a REAL archive with the YubiKey-backed key."
    echo "  This drill uses throwaway keys, so it proves the PIPELINE, never KEY AVAILABILITY."
    exit 0
fi

echo "RESULT: ${FAILURES} FAILURE(S) -- see above." >&2
exit 1
