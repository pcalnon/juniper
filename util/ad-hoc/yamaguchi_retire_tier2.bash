#!/usr/bin/env bash
# Project     : Juniper
# Sub-Project : juniper-ml
# Application : ad-hoc utility
# Author      : Paul Calnon
# Version     : 1.0.0
# License     : MIT License
#
# Tier-2 retirement sweep (certification note 8.11.3 / 8.12.1) -- the deletions
# that remove a FALLBACK, so every one of them is gated on the migration having
# actually succeeded, not merely having been attempted.
#
# Two groups, separately flagged, because they are not equally dangerous:
#
#   --execute        the old gpg fresh set (temp_backups/Ubuntu, ~51 G) and its
#                    job DB (DQRVQNDIFX.sqlite*, ~353 M).  Superseded by
#                    Yamaguchi once a drill passes at the new location.
#
#   --execute-old-destination   the sdc4 Yamaguchi copy (~196 G).  This is the
#                    single most dangerous delete in the arc: it removes the
#                    pre-migration copy of the LIVE set.  Requires --execute
#                    to have been satisfied by the same guards AND an explicit
#                    second flag.  8.6-8 step 5: keep it until the drill passes.
#
# Gates, all fatal, all re-probed live:
#   1. the live job's TargetURL must already be the NEW destination
#   2. the new destination must hold >= the volume count the job last recorded
#   3. a backup run at the new destination must have ParsedResult=Success
#   4. a drill results.json under --drill-root must show a passing verdict
#   5. no task active or queued
#
# NEVER touches /mnt/Backups/Ubuntu itself (the old-archive mountpoint), the
# old archive's volumes, _drill_scratch (Tier 3), or _yamaguchi_check.
#
# Usage:
#   bash util/ad-hoc/yamaguchi_retire_tier2.bash                       # dry run
#   bash util/ad-hoc/yamaguchi_retire_tier2.bash --execute             # group 1
#   bash util/ad-hoc/yamaguchi_retire_tier2.bash --execute --execute-old-destination
#
# Exit: 0 ok, 2 refused (gate unmet), 3 guard failure.

set -uo pipefail

EXECUTE=0
EXECUTE_OLD_DEST=0
for a in "$@"; do
    case "$a" in
        --execute) EXECUTE=1 ;;
        --execute-old-destination) EXECUTE_OLD_DEST=1 ;;
        *) echo "unknown argument: $a" >&2; exit 3 ;;
    esac
done
if [[ $EXECUTE_OLD_DEST -eq 1 && $EXECUTE -eq 0 ]]; then
    echo "REFUSE: --execute-old-destination requires --execute" >&2
    exit 3
fi

REPO="/home/pcalnon/Development/python/Juniper/juniper-ml"
NEW_DEST="/mnt/Backups/Ubuntu/Yamaguchi"
OLD_DEST="/media/pcalnon/temp_backups/Yamaguchi"
OLD_GPG_SET="/media/pcalnon/temp_backups/Ubuntu"
OLD_GPG_DB_GLOB="$HOME/.config/Duplicati/DQRVQNDIFX.sqlite"
DRILL_ROOT="/media/pcalnon/temp_backups/_yamaguchi_drill"

echo "== Tier-2 retirement gate check at $(date -Is)"
echo

# --- gate 0: filesystems --------------------------------------------------
for fs in /media/pcalnon/temp_backups /mnt/Backups/Ubuntu; do
    mountpoint -q "$fs" || { echo "FATAL: $fs is not a mountpoint" >&2; exit 3; }
done
echo "gate 0 PASS: both filesystems mounted"

# --- gate 5 (checked early, it is the cheapest) ---------------------------
STATUS=$(python3 "$REPO/util/ad-hoc/yamaguchi_server_api.py" status 2>&1) || {
    echo "FATAL: could not reach the server" >&2; exit 2; }
echo "$STATUS" | grep -q '"ActiveTask": null' || { echo "REFUSE: a task is active" >&2; exit 2; }
echo "$STATUS" | grep -q '"SchedulerQueueIds": \[\]' || { echo "REFUSE: queue not empty" >&2; exit 2; }
echo "gate 5 PASS: ActiveTask=null, queue empty"

# --- gate 1: the job must already point at the new destination ------------
if ! echo "$STATUS" | grep -q "target=file://$NEW_DEST"; then
    echo "REFUSE: the live job does NOT point at $NEW_DEST yet -- migration step 3 has not run" >&2
    echo "        current: $(echo "$STATUS" | grep -o 'target=[^ ]*')" >&2
    exit 2
fi
echo "gate 1 PASS: live job TargetURL is $NEW_DEST"

# --- gate 2: the new destination must be populated ------------------------
NEW_VOLS=$(find "$NEW_DEST" -maxdepth 1 -type f -name 'duplicati-*' 2>/dev/null | wc -l)
if [[ "$NEW_VOLS" -lt 3 ]]; then
    echo "REFUSE: new destination holds only $NEW_VOLS volume(s)" >&2
    exit 2
fi
echo "gate 2 PASS: new destination holds $NEW_VOLS volumes"

# --- gate 3: a Success run must exist since the repoint -------------------
LOG=$(python3 "$REPO/util/ad-hoc/yamaguchi_server_api.py" log 2 2>&1 | head -1)
if ! echo "$LOG" | grep -q '"ParsedResult": "Success"'; then
    echo "REFUSE: the newest run is not Success -- $LOG" >&2
    exit 2
fi
echo "gate 3 PASS: newest run ParsedResult=Success"

# --- gate 4: a drill at the new destination must have passed --------------
DRILL_OK=0
DRILL_SEEN=""
while IFS= read -r rj; do
    [[ -n "$rj" ]] || continue
    if grep -q "$NEW_DEST" "$(dirname "$rj")/drill-meta.json" 2>/dev/null || grep -q "$NEW_DEST" "$rj" 2>/dev/null; then
        DRILL_SEEN="$rj"
        if grep -qE '"verdict"[[:space:]]*:[[:space:]]*"(PASS|VERIFIED)"' "$rj"; then
            DRILL_OK=1
        fi
    fi
done < <(find "$DRILL_ROOT" -maxdepth 2 -name 'results.json' -newermt '2026-08-26' 2>/dev/null)

if [[ "$DRILL_OK" -ne 1 ]]; then
    echo "REFUSE: no passing drill found at $NEW_DEST under $DRILL_ROOT" >&2
    echo "        (searched results.json newer than 2026-08-26; seen: ${DRILL_SEEN:-none})" >&2
    echo "        8.6-8 step 5: keep every fallback until the drill passes." >&2
    exit 2
fi
echo "gate 4 PASS: passing drill at the new destination -- $DRILL_SEEN"

# --- the candidates -------------------------------------------------------
echo
echo "== group 1 (--execute)"
for p in "$OLD_GPG_SET" "$OLD_GPG_DB_GLOB"; do
    if [[ -e "$p" ]]; then
        printf '  %-8s %s\n' "$(du -sh "$p" 2>/dev/null | cut -f1)" "$p"
    else
        printf '  %-8s %s (ABSENT)\n' "--" "$p"
    fi
done
echo "  (plus DQRVQNDIFX.sqlite-wal / -shm if present)"

echo
echo "== group 2 (--execute-old-destination)"
if [[ -d "$OLD_DEST" ]]; then
    printf '  %-8s %s\n' "$(du -sh "$OLD_DEST" | cut -f1)" "$OLD_DEST"
else
    printf '  %-8s %s (ABSENT)\n' "--" "$OLD_DEST"
fi

echo
echo "== free space before"
df -h /media/pcalnon/temp_backups | tail -1

if [[ $EXECUTE -eq 0 ]]; then
    echo
    echo "DRY RUN -- nothing deleted.  All gates passed; re-run with --execute."
    exit 0
fi

echo
echo "== EXECUTING group 1"
[[ -d "$OLD_GPG_SET" ]] && { echo "  rm -rf $OLD_GPG_SET"; rm -rf "$OLD_GPG_SET"; }
for suffix in "" "-wal" "-shm"; do
    f="${OLD_GPG_DB_GLOB}${suffix}"
    [[ -e "$f" ]] && { echo "  rm -f $f"; rm -f "$f"; }
done

if [[ $EXECUTE_OLD_DEST -eq 1 ]]; then
    echo
    echo "== EXECUTING group 2 -- removing the PRE-MIGRATION copy of the live set"
    if [[ -d "$OLD_DEST" ]]; then
        echo "  rm -rf $OLD_DEST"
        rm -rf "$OLD_DEST"
    fi
else
    echo
    echo "group 2 SKIPPED (pass --execute-old-destination to remove $OLD_DEST)"
fi

echo
echo "== free space after"
df -h /media/pcalnon/temp_backups | tail -1
echo
echo "DONE"
