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
# Usage: util/ad-hoc/duplicati_purge_dryrun.bash [dbpath] [dest-url]

set -uo pipefail

DBPATH="${1:-/media/pcalnon/temp_backups/_drill_scratch/drill.sqlite}"
DEST="${2:-file:///mnt/Backups/Ubuntu}"
MOUNT=/mnt/Backups/Ubuntu

if ! mountpoint -q "$MOUNT"; then
    echo "REFUSING: $MOUNT is not a mountpoint. A purge against an unmounted" >&2
    echo "destination is how a configuration error becomes data loss." >&2
    exit 2
fi
echo "mount check   : OK ($MOUNT)"

VOLCOUNT=$(find "$MOUNT" -maxdepth 1 -name '*.gpg' | wc -l)
echo "volumes visible: $VOLCOUNT"
if [ "$VOLCOUNT" -lt 100 ]; then
    echo "REFUSING: only $VOLCOUNT volumes visible; that is what an unmounted or" >&2
    echo "wrong destination looks like." >&2
    exit 2
fi

if [ ! -r "$DBPATH" ]; then
    echo "REFUSING: database not readable: $DBPATH" >&2
    exit 2
fi
case "$DBPATH" in
    */.config/Duplicati/SJTCQIIZSJ.sqlite)
        echo "REFUSING: that is the LIVE job database (mid-Recreate)." >&2
        exit 2 ;;
    */.config/Duplicati/backup*)
        echo "REFUSING: that is the archived ORIGINAL; use a disposable copy." >&2
        exit 2 ;;
esac
echo "database      : $DBPATH (disposable copy)"

PASSPHRASE=$(tr -d '\r\n' < resources/duplicati.env)
export PASSPHRASE

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
timeout 5400 "${CMD[@]}" 2>&1
echo "rc: $?"
echo "end: $(date +%H:%M:%S)"
