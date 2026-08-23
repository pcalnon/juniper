#!/usr/bin/env bash
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# License:     MIT License
#
# purge-broken-files DRY RUN.
#
# purge-broken-files is the destructive counterpart to list-broken-files: it
# removes files "from the database AND remote storage". --dry-run is documented
# as "Performs the operation, but does not write changes to the local database
# or the remote storage".
#
# Safety posture, deliberately belt-and-braces because this command deletes
# archive data and the archive is currently the only copy of anything older
# than 2025-11-12:
#
#   1. Refuses unless the destination is actually mounted. An unmounted mount
#      point lists as empty, and a purge against "nothing there" is exactly the
#      shape that turns a config error into data loss.
#   2. Refuses unless --dry-run is present in the arguments actually passed to
#      duplicati-cli -- the flag is verified in the assembled command, not
#      assumed from a variable.
#   3. Operates on a DISPOSABLE COPY of the archived job database, never the
#      live one (mid-Recreate) and never the archived original.
#   4. Prints the exact command before running it.
#
# Applying the purge for real is a SEPARATE, deliberate act. This script cannot
# do it: it hard-codes --dry-run and verifies its presence.
#
# Usage: util/ad-hoc/duplicati_purge_dryrun.bash [dbpath] [dest-url] [timeout-seconds]
#
# NOTE ON TIMEOUT: Duplicati's own list-broken-files spent 90 minutes on this
# database without completing (it contends with an in-flight Recreate). A run
# killed by timeout is NOT a result -- it tells you nothing either way -- so the
# default here is deliberately generous.

set -uo pipefail

DBPATH="${1:-/media/pcalnon/temp_backups/_drill_scratch/drill.sqlite}"
DEST="${2:-file:///mnt/Backups/Ubuntu}"
TIMEOUT="${3:-28800}"   # 8h default; a killed run is not a result

# Derive the mount to check FROM $DEST. It used to be a hardcoded literal, which
# meant overriding the destination -- a documented, supported usage -- validated
# /mnt/Backups/Ubuntu while purging somewhere entirely unexamined. Both guards
# passed while protecting the wrong filesystem.
case "$DEST" in
    file://*) MOUNT=${DEST#file://} ;;
    /*)       MOUNT=$DEST ;;
    *)        echo "REFUSING: only local file:// destinations are supported here;" >&2
              echo "a remote destination cannot be mount-checked. Got: $DEST" >&2
              exit 2 ;;
esac
MOUNT=${MOUNT%/}
echo "destination   : $DEST"
echo "mount to check: $MOUNT"

if ! mountpoint -q "$MOUNT"; then
    echo "REFUSING: $MOUNT is not a mountpoint. A purge against an unmounted" >&2
    echo "destination is how a configuration error becomes data loss." >&2
    exit 2
fi
echo "mount check   : OK"

VOLCOUNT=$(find "$MOUNT" -maxdepth 1 -name '*.gpg' | wc -l)
echo "volumes visible: $VOLCOUNT"
if [ "$VOLCOUNT" -lt 100 ]; then
    echo "REFUSING: only $VOLCOUNT volumes visible at $MOUNT; that is what an" >&2
    echo "unmounted or wrong destination looks like." >&2
    exit 2
fi

if [ ! -r "$DBPATH" ]; then
    echo "REFUSING: database not readable: $DBPATH" >&2
    exit 2
fi

# Compare by RESOLVED IDENTITY, not by string shape. The previous lexical `case`
# match was bypassable four ways, all of them plausible during an incident:
#   * a relative path (`SJTCQIIZSJ.sqlite` from inside ~/.config/Duplicati)
#     contains no "/.config/Duplicati/" substring and matched nothing;
#   * a symlink pointing at the live DB;
#   * `.../Duplicati/../Duplicati/SJTCQIIZSJ.sqlite`;
#   * a real file on disk today, SJTCQIIZSJ_2026-08-22-backup.sqlite, which
#     matches neither `SJTCQIIZSJ.sqlite` nor `backup*` yet IS a copy of the
#     live job database.
# device:inode comparison after realpath catches all of these.
DBREAL=$(readlink -f -- "$DBPATH") || DBREAL=""
DBID=$(stat -c '%d:%i' -- "$DBREAL" 2>/dev/null || echo "")
if [ -z "$DBID" ]; then
    echo "REFUSING: cannot resolve database identity for $DBPATH" >&2
    exit 2
fi

PROTECTED_DIR=/home/pcalnon/.config/Duplicati
for prot in "$PROTECTED_DIR"/SJTCQIIZSJ*.sqlite "$PROTECTED_DIR"/backup*.sqlite \
            "$PROTECTED_DIR"/Duplicati-server*.sqlite; do
    [ -e "$prot" ] || continue
    pid=$(stat -c '%d:%i' -- "$prot" 2>/dev/null || echo "")
    if [ -n "$pid" ] && [ "$pid" = "$DBID" ]; then
        echo "REFUSING: $DBPATH resolves to a PROTECTED database:" >&2
        echo "  $prot" >&2
        echo "Use a disposable COPY, never the live job DB or an archived original." >&2
        exit 2
    fi
done
# Belt and braces: refuse anything that resolves inside the Duplicati config dir
# at all, even a file the glob above did not enumerate.
case "$DBREAL" in
    "$PROTECTED_DIR"/*)
        echo "REFUSING: $DBREAL lives in $PROTECTED_DIR." >&2
        echo "Operate on a disposable copy outside that directory." >&2
        exit 2 ;;
esac
echo "database      : $DBPATH"
echo "  resolves to : $DBREAL  (verified not a protected database)"

# Passphrase: no implicit path. Refuse rather than silently proceeding with an
# empty or wrong secret.
# The ARCHIVE GPG passphrase -- NOT the web-UI password. They are different
# secrets; the wrong one fails as "Bad session key", which reads like a corrupt
# archive rather than a credential mix-up. No default: resources/duplicati.env
# was removed on the 2026-08-23 UI-password rotation, and silently falling back
# to .env would supply the UI password here.
PPFILE="${DUPLICATI_PW_FILE:-}"
if [ -z "$PPFILE" ]; then
    echo "REFUSING: set DUPLICATI_PW_FILE to the ARCHIVE passphrase file." >&2
    echo "It is NOT the web-UI password in .env -- different secret." >&2
    exit 2
fi
if [ ! -r "$PPFILE" ]; then
    echo "REFUSING: passphrase file not readable: $PPFILE" >&2
    echo "Set DUPLICATI_PW_FILE to override." >&2
    exit 2
fi
if grep -qE '^[[:space:]]*(export[[:space:]]+)?PASSPHRASE=' "$PPFILE" 2>/dev/null; then
    PASSPHRASE=$(sed -nE 's/^[[:space:]]*(export[[:space:]]+)?PASSPHRASE=(.*)$/\2/p' \
                 "$PPFILE" | head -1)
    case "$PASSPHRASE" in
        \'*\') PASSPHRASE=${PASSPHRASE#\'}; PASSPHRASE=${PASSPHRASE%\'} ;;
        \"*\") PASSPHRASE=${PASSPHRASE#\"}; PASSPHRASE=${PASSPHRASE%\"} ;;
    esac
else
    PASSPHRASE=$(tr -d '\r\n' < "$PPFILE")
fi
if [ -z "$PASSPHRASE" ]; then
    echo "REFUSING: empty passphrase recovered from $PPFILE" >&2
    exit 2
fi
export PASSPHRASE
echo "credential    : $PPFILE (${#PASSPHRASE} chars)"

CMD=(duplicati-cli purge-broken-files "$DEST"
     "--dbpath=$DBPATH"
     --encryption-module=gpg
     --dry-run=true)

# Verify the safety flag is actually in the command we are about to run.
printf '%s\n' "${CMD[@]}" | grep -qx -- '--dry-run=true' || {
    echo "REFUSING: --dry-run=true not present in the assembled command." >&2
    exit 3
}

echo
echo "command:"
printf '  %q' "${CMD[@]}"; echo
echo
echo "start: $(date +%H:%M:%S)"
timeout "$TIMEOUT" "${CMD[@]}" 2>&1
echo "rc: $?"
echo "end: $(date +%H:%M:%S)"
