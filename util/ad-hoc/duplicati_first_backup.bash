#!/usr/bin/env bash
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# License:     MIT License
#
# Run the FIRST backup of the fresh set via duplicati-cli.
#
# Why the CLI and not the UI: the server's single worker is occupied by a
# database Recreate with 13 backups queued behind it (~47 days). A job started
# through the UI would queue behind all of that. `duplicati-cli backup` runs in
# its own process and does not touch the server's task queue.
#
# The --dbpath must match the DBPath the server assigned to the job, so that the
# UI job and this CLI run are the same backup rather than two unrelated ones.
#
# Safety posture:
#   * refuses unless the destination is a real mountpoint with room;
#   * refuses an empty/short passphrase;
#   * refuses if the destination already holds Duplicati volumes, so a rerun
#     cannot silently append to a set created under a different passphrase;
#   * never puts the passphrase on the command line (visible in `ps`).
#
# Usage:
#   util/ad-hoc/duplicati_first_backup.bash <passphrase-file> <dbpath> [dest-dir]

set -uo pipefail

PPFILE="${1:?usage: $0 <passphrase-file> <dbpath> [dest-dir] [key]}"
DBPATH="${2:?usage: $0 <passphrase-file> <dbpath> [dest-dir] [key]}"
DESTDIR="${3:-/media/pcalnon/temp_backups/Ubuntu}"
# Select the secret by NAME. The credential file holds several 32-char secrets,
# so neither position nor length distinguishes them -- picking the wrong one
# encrypts the backup under a secret nobody recorded as belonging to it, and
# nothing about the run would look wrong until a restore was attempted.
PPKEY="${4:-PASSPHRASE}"
MOUNT=/media/pcalnon/temp_backups

if ! mountpoint -q "$MOUNT"; then
    echo "REFUSING: $MOUNT is not a mountpoint." >&2
    exit 2
fi
AVAIL_GB=$(df -BG --output=avail "$MOUNT" | tail -1 | tr -dc '0-9')
if [ "${AVAIL_GB:-0}" -lt 250 ]; then
    echo "REFUSING: only ${AVAIL_GB}G free at $MOUNT; the set needs ~181 GiB plus headroom." >&2
    exit 2
fi
echo "destination : $DESTDIR  (${AVAIL_GB}G free)"

EXISTING=$(find "$DESTDIR" -maxdepth 1 -name '*.dblock.*' 2>/dev/null | wc -l)
if [ "$EXISTING" -gt 0 ]; then
    echo "REFUSING: $DESTDIR already holds $EXISTING dblock volume(s)." >&2
    echo "Appending to an existing set under a possibly different passphrase is how" >&2
    echo "an archive becomes half-readable. Point at an empty directory." >&2
    exit 2
fi

if [ ! -r "$PPFILE" ]; then
    echo "REFUSING: passphrase file not readable: $PPFILE" >&2
    exit 2
fi
if grep -qE "^[[:space:]]*(export[[:space:]]+)?${PPKEY}=" "$PPFILE" 2>/dev/null; then
    PASSPHRASE=$(sed -nE "s/^[[:space:]]*(export[[:space:]]+)?${PPKEY}=(.*)$/\2/p" \
                 "$PPFILE" | head -1)
    case "$PASSPHRASE" in
        \'*\') PASSPHRASE=${PASSPHRASE#\'}; PASSPHRASE=${PASSPHRASE%\'} ;;
        \"*\") PASSPHRASE=${PASSPHRASE#\"}; PASSPHRASE=${PASSPHRASE%\"} ;;
    esac
else
    PASSPHRASE=$(tr -d '\r\n' < "$PPFILE")
fi
if [ "${#PASSPHRASE}" -lt 12 ]; then
    echo "REFUSING: passphrase is ${#PASSPHRASE} chars; too short for an archive" >&2
    echo "that must stay readable for years." >&2
    exit 2
fi
export PASSPHRASE
# Print a hash prefix, not the secret: length alone cannot distinguish two
# 32-char secrets, and this is the only cheap way to confirm which one ran.
echo "credential  : $PPFILE key=$PPKEY (${#PASSPHRASE} chars, sha256[:16]=$(printf '%s' "$PASSPHRASE" | sha256sum | cut -c1-16))"
echo "dbpath      : $DBPATH"
echo

# Settings mirror duplicati_build_fresh_job.py exactly. If they drift, the CLI
# run and the UI job describe different backups.
CMD=(duplicati-cli backup "file://$DESTDIR" "$HOME"
     "--dbpath=$DBPATH"
     --encryption-module=gpg
     --compression-module=zip
     --blocksize=1MB
     --dblock-size=500MB
     --skip-files-larger-than=2GB
     --no-auto-compact=true
     --allow-missing-source=true)

# Exclusions, carried from the job config. Duplicati takes them as repeated
# --exclude arguments on the CLI.
while IFS= read -r expr; do
    [ -z "$expr" ] && continue
    CMD+=("--exclude=${expr//\%HOME\%/$HOME}")
done < <(python3 - "$HOME" <<'PY'
import sqlite3, sys
c = sqlite3.connect('file:/home/pcalnon/.config/Duplicati/Duplicati-server.sqlite?mode=ro',
                    uri=True)
for (e,) in c.execute(
        'SELECT Expression FROM Filter WHERE BackupID=2 AND Include=0 ORDER BY "Order"'):
    print(e)
for e in ("%HOME%/.local/share/Steam/", "%HOME%/snap/steam/", "%HOME%/StarfieldData/",
          "%HOME%/VirtualMachines/", "%HOME%/.config/Duplicati/",
          "%HOME%/Development/python/Juniper/juniper-data/data/"):
    print(e)
PY
)

echo "exclusions  : $(( ${#CMD[@]} - 11 ))"
echo
echo "start: $(date +%Y-%m-%dT%H:%M:%S)"
"${CMD[@]}" 2>&1
RC=$?
echo "rc: $RC"
echo "end: $(date +%Y-%m-%dT%H:%M:%S)"
exit "$RC"
