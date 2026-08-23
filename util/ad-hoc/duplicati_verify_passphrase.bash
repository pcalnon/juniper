#!/usr/bin/env bash
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# License:     MIT License
#
# Empirically verify the Duplicati archive passphrase by GPG-decrypting the
# smallest real volume in the destination.
#
# Why empirical: Duplicati stores a `passphrase` verification hash and a
# `passphrase-salt` in its Configuration table, but the exact derivation is not
# documented and guessing it produces false negatives that look like "wrong
# passphrase". Decrypting an actual volume tests the thing we care about.
#
# Does not modify the archive. NOTE: it DOES write decrypted plaintext to a
# mktemp file (owner-only) for the duration of the check, because PIPESTATUS is
# not observable after a command substitution under `set -u`. A trap removes it
# on any exit path, including interrupt.
#
# Usage: util/ad-hoc/duplicati_verify_passphrase.bash [dest_dir] [env_file]

set -uo pipefail

DEST="${1:-/mnt/Backups/Ubuntu}"
ENVFILE="${2:-.env}"

if [ ! -r "$ENVFILE" ]; then
    echo "FAIL: cannot read env file: $ENVFILE" >&2
    exit 2
fi
# Accept BOTH credential file shapes without sourcing. Sourcing a bare-password
# file executes it as shell: a password containing `$` then dies with "unbound
# variable" under `set -u`, and one containing backticks would EXECUTE. Parse it
# instead -- never source a file that may not be shell.
if grep -qE '^[[:space:]]*(export[[:space:]]+)?PASSPHRASE=' "$ENVFILE" 2>/dev/null; then
    PASSPHRASE=$(sed -nE 's/^[[:space:]]*(export[[:space:]]+)?PASSPHRASE=(.*)$/\2/p' \
                 "$ENVFILE" | head -1)
    case "$PASSPHRASE" in
        \'*\') PASSPHRASE=${PASSPHRASE#\'}; PASSPHRASE=${PASSPHRASE%\'} ;;
        \"*\") PASSPHRASE=${PASSPHRASE#\"}; PASSPHRASE=${PASSPHRASE%\"} ;;
    esac
else
    PASSPHRASE=$(tr -d '\r\n' < "$ENVFILE")
fi
if [ -z "${PASSPHRASE:-}" ]; then
    echo "FAIL: no passphrase recovered from $ENVFILE" >&2
    exit 2
fi
echo "credential  : $ENVFILE (${#PASSPHRASE} chars)"

# awk, not `sort -n | head -1`: head exits after one line and SIGPIPEs sort,
# which prints "sort: write failed: Broken pipe" to stderr on every run.
SMALL=$(find "$DEST" -maxdepth 1 -name '*.dindex.zip.gpg' -printf '%s %p\n' \
        | awk 'NR==1||$1<m{m=$1;f=substr($0,index($0," ")+1)}END{print f}')
if [ -z "$SMALL" ]; then
    echo "FAIL: no dindex volume found in $DEST" >&2
    exit 2
fi
echo "test volume : $(basename "$SMALL")"
echo "size        : $(stat -c %s "$SMALL") bytes"

ERR=$(mktemp)
OUT=$(mktemp)
# Without this, Ctrl-C during gpg leaks a decrypted-plaintext temp file on disk.
trap 'rm -f "$OUT" "$ERR"' EXIT INT TERM
# Decrypt to a temp file rather than a pipe: PIPESTATUS is not observable after
# a command substitution under `set -u`. The pass/fail signal is the ZIP magic
# bytes below, NOT $RC -- that is deliberate and more robust, since it does not
# depend on gpg's exit-code behaviour for symmetric wrong-passphrase failures.
# $RC is printed for diagnosis only.
printf '%s' "$PASSPHRASE" \
    | gpg --batch --yes --quiet --passphrase-fd 0 --pinentry-mode loopback \
          --output "$OUT" --decrypt "$SMALL" 2>"$ERR"
RC=$?
MAGIC=$(head -c 2 "$OUT" 2>/dev/null | od -An -tx1 | tr -d ' \n')
rm -f "$OUT"

echo "gpg exit    : $RC"
echo "first bytes : ${MAGIC:-<none>}"
if [ "$MAGIC" = "504b" ]; then
    # 50 4b == "PK", the ZIP local-file-header magic Duplicati volumes carry.
    echo "RESULT: PASSPHRASE CORRECT (decrypted to a valid ZIP stream)"
    rm -f "$ERR"
    exit 0
fi
echo "RESULT: passphrase did NOT produce a ZIP stream"
echo "--- gpg stderr ---"
head -8 "$ERR"
rm -f "$ERR"
exit 1
