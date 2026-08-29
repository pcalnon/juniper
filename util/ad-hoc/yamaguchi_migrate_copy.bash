#!/usr/bin/env bash
# Project     : Juniper
# Sub-Project : juniper-ml
# Application : ad-hoc utility
# Author      : Paul Calnon
# Version     : 1.0.0
# License     : MIT License
#
# Migration step 2 (certification note 8.6-8): stage a COPY of the Yamaguchi
# destination onto sda1, the only fstab-managed backup-class filesystem on this
# host (8.10.2).  Copy only -- this script never touches the job definition,
# never repoints TargetURL, and never deletes the source.  Step 3 (the PUT) and
# step 5 (retiring the sdc4 copy) are separate and deliberately manual.
#
# Guards, all fatal:
#   * both filesystems mounted (the destination fs has no fstab entry, so a
#     bare-path copy onto / is exactly the failure this migration exists to fix)
#   * no active or queued task -- a copy taken mid-run is torn
#   * --checksum is used only when the target already holds volumes (on an
#     empty target it decides nothing and costs a full extra source read)
#   * free space at the target >= source size + 5 %
#
# Verifies by file count and byte total afterwards.  Integrity is NOT this
# script's job: run duplicati_decrypt_validate_all.bash against the copy next.
#
# Usage: bash util/ad-hoc/yamaguchi_migrate_copy.bash [--execute]
# Exit: 0 ok, 2 refused, 3 guard failure, 4 copy mismatch.

set -uo pipefail

EXECUTE=0
[[ "${1:-}" == "--execute" ]] && EXECUTE=1

REPO="/home/pcalnon/Development/python/Juniper/juniper-ml"
SRC="/media/pcalnon/temp_backups/Yamaguchi"
DST="/mnt/Backups/Ubuntu/Yamaguchi"
SRC_FS="/media/pcalnon/temp_backups"
DST_FS="/mnt/Backups/Ubuntu"
LOG="/media/pcalnon/temp_backups/_yamaguchi_check/migrate-copy-$(date +%Y%m%d-%H%M%S).log"

echo "== Yamaguchi migration copy at $(date -Is)"
echo "   source: $SRC"
echo "   target: $DST"
echo

# --- guard 1: both filesystems mounted ------------------------------------
for fs in "$SRC_FS" "$DST_FS"; do
    if ! mountpoint -q "$fs"; then
        echo "FATAL: $fs is not a mountpoint" >&2
        exit 3
    fi
done
echo "guard: both filesystems mounted"

# --- guard 2: no active or queued task ------------------------------------
STATUS=$(python3 "$REPO/util/ad-hoc/yamaguchi_server_api.py" status 2>&1) || {
    echo "FATAL: could not reach the server" >&2; exit 2; }
if ! echo "$STATUS" | grep -q '"ActiveTask": null'; then
    echo "REFUSE: a task is active -- a copy taken mid-run is torn" >&2
    exit 2
fi
if ! echo "$STATUS" | grep -q '"SchedulerQueueIds": \[\]'; then
    echo "REFUSE: the scheduler queue is not empty" >&2
    exit 2
fi
echo "guard: ActiveTask=null, queue empty"

# --- guard 3: how much does the target already hold? ----------------------
# This decides whether --checksum earns its cost.  On an EMPTY destination every
# file is missing and must be sent regardless, so --checksum buys nothing and
# costs a full extra read of the source: measured 2026-08-26, rsync read 21.8 GB
# in 122 s having written zero bytes, i.e. ~20 min of pre-pass on this 196 GiB
# set before a single byte moved.  On a POPULATED destination it is exactly the
# right flag, because it is what catches a silently-corrupt earlier copy.
# Integrity is proven either way by duplicati_decrypt_validate_all.bash, which
# does full AES/HMAC verification -- strictly stronger than an rsync checksum.
DST_EXISTING=0
if [[ -d "$DST" ]]; then
    DST_EXISTING=$(find "$DST" -maxdepth 1 -type f -name 'duplicati-*' | wc -l)
fi
if [[ "$DST_EXISTING" -gt 0 ]]; then
    RSYNC_VERIFY=(--checksum)
    echo "guard: target already holds $DST_EXISTING volume(s) -- using --checksum to reconcile"
else
    RSYNC_VERIFY=()
    echo "guard: target is empty -- omitting --checksum (it can decide nothing on a fresh copy)"
fi

# --- guard 4: free space --------------------------------------------------
SRC_BYTES=$(du -sb "$SRC" | cut -f1)
DST_AVAIL=$(df -B1 --output=avail "$DST_FS" | tail -1 | tr -d ' ')
NEED=$(( SRC_BYTES + SRC_BYTES / 20 ))
printf 'guard: source %s B, target free %s B, need >= %s B\n' "$SRC_BYTES" "$DST_AVAIL" "$NEED"
if [[ "$DST_AVAIL" -lt "$NEED" ]]; then
    echo "FATAL: insufficient free space at $DST_FS" >&2
    exit 3
fi

SRC_FILES=$(find "$SRC" -maxdepth 1 -type f | wc -l)
echo "source: $SRC_FILES files, $SRC_BYTES B"
echo

if [[ $EXECUTE -eq 0 ]]; then
    echo "DRY RUN -- nothing copied.  Re-run with --execute to apply."
    exit 0
fi

# --- the copy -------------------------------------------------------------
mkdir -p "$DST"
echo "== rsync starting, log: $LOG"
rsync -a "${RSYNC_VERIFY[@]}" --info=progress2 "$SRC/" "$DST/" 2>&1 | tee "$LOG" | tail -3
RC=${PIPESTATUS[0]}
echo "rsync rc=$RC"
if [[ "$RC" -ne 0 ]]; then
    echo "FATAL: rsync failed rc=$RC" >&2
    exit 4
fi

# --- verify by count and bytes -------------------------------------------
echo
echo "== verifying"
DST_FILES=$(find "$DST" -maxdepth 1 -type f | wc -l)
DST_BYTES=$(du -sb "$DST" | cut -f1)
printf '  source: %6s files  %s B\n' "$SRC_FILES" "$SRC_BYTES"
printf '  target: %6s files  %s B\n' "$DST_FILES" "$DST_BYTES"

if [[ "$SRC_FILES" != "$DST_FILES" || "$SRC_BYTES" != "$DST_BYTES" ]]; then
    echo "MISMATCH -- the copy is not byte-identical by count/size" >&2
    exit 4
fi
echo "  MATCH -- count and byte total agree"
echo
echo "NEXT: integrity is not proven by this script.  Run:"
echo "  bash util/ad-hoc/duplicati_decrypt_validate_all.bash \\"
echo "       $DST \$HOME/.config/duplicati-backup/env PASSPHRASE aes"
echo
echo "DONE at $(date -Is)"
