#!/usr/bin/env bash
# Project     : Juniper
# Sub-Project : juniper-ml
# Application : ad-hoc utility
# Author      : Paul Calnon
# Version     : 1.0.0
# License     : MIT License
#
# Tier-1 retirement sweep for the Yamaguchi backup arc (certification note 8.11.3).
#
# Deletes ONLY the paths approved as Tier 1 -- drill `restored/` trees, one stale
# drill `tmp/`, the stale CONTENTS of the live job's tempdir, `_gpg_repro/`, and
# the disabled updates tree.  Everything else is refused by construction: the
# script has no path argument and no wildcard expansion beyond the tempdir
# contents.
#
# HARD RULES encoded here (note 8.8 / 8.11.3):
#   * `_duplicati_tmp/` is the LIVE job's --tempdir.  Its CONTENTS may go; the
#     DIRECTORY never may, and never while a run is active.
#   * `_drill_scratch/` is Tier 3 (BLOCKED) -- the old archive's only local DB.
#     It is absent from this script entirely.
#   * `/mnt/Backups/Ubuntu` is the old-archive MOUNTPOINT.  Nothing is ever
#     deleted there.  Only `/media/pcalnon/temp_backups/Ubuntu` is a candidate,
#     and that is Tier 2 -- also absent from this script.
#   * `_yamaguchi_check/` and `_fresh_dlist_check/` are on the KEEP list.
#   * Every drill log / results.json / provenance.txt stays.
#
# Refuses to run unless the server reports ActiveTask=null AND an empty
# SchedulerQueueIds.
#
# Usage:
#   bash util/ad-hoc/yamaguchi_retire_tier1.bash            # dry run (default)
#   bash util/ad-hoc/yamaguchi_retire_tier1.bash --execute   # actually delete
#
# Exit: 0 ok, 2 refused (a run is active / server unreachable), 3 guard failure.

set -uo pipefail

EXECUTE=0
[[ "${1:-}" == "--execute" ]] && EXECUTE=1

REPO="/home/pcalnon/Development/python/Juniper/juniper-ml"
TB="/media/pcalnon/temp_backups"
TMPDIR_LIVE="$TB/_duplicati_tmp"

# --- guard 1: the destination filesystem must be mounted -------------------
if ! mountpoint -q "$TB"; then
    echo "REFUSE: $TB is not a mountpoint" >&2
    exit 3
fi

# --- guard 2: no run may be active ----------------------------------------
echo "== checking server state"
STATUS=$(python3 "$REPO/util/ad-hoc/yamaguchi_server_api.py" status 2>&1) || {
    echo "REFUSE: could not reach the server" >&2; exit 2; }
echo "$STATUS" | grep -E '"(ActiveTask|SchedulerQueueIds)"'

if ! echo "$STATUS" | grep -q '"ActiveTask": null'; then
    echo "REFUSE: a task is active -- never sweep the live tempdir during a run" >&2
    exit 2
fi
if ! echo "$STATUS" | grep -q '"SchedulerQueueIds": \[\]'; then
    echo "REFUSE: the scheduler queue is not empty" >&2
    exit 2
fi
echo "   ActiveTask=null, queue empty -- proceeding"
echo

# --- the approved Tier-1 set ----------------------------------------------
# Whole directories to remove.
TARGETS=(
    "$TB/_yamaguchi_drill/drill-20260825-183711/restored"
    "$TB/_yamaguchi_drill/drill-20260825-075730/restored"
    "$TB/_yamaguchi_drill/drill-20260825-075352/tmp"
    "$TB/_fresh_drill/drill-20260824-142353/restored"
    "$TB/_gpg_repro"
    "$HOME/.config/Duplicati/updates.disabled-2026-08-25"
)

# Paths that must NEVER appear as a target, checked at runtime rather than
# trusted from the list above.
FORBIDDEN=(
    "/mnt/Backups/Ubuntu"
    "$TB/Ubuntu"
    "$TB/_drill_scratch"
    "$TB/_yamaguchi_check"
    "$TB/_fresh_dlist_check"
    "$TB/Yamaguchi"
    "$TMPDIR_LIVE"
)

echo "== Tier 1 targets"
for t in "${TARGETS[@]}"; do
    for f in "${FORBIDDEN[@]}"; do
        if [[ "$t" == "$f" || "$t" == "$f"/* ]]; then
            echo "REFUSE: target '$t' is inside forbidden path '$f'" >&2
            exit 3
        fi
    done
    if [[ -d "$t" ]]; then
        printf '  %-8s %s\n' "$(du -sh "$t" | cut -f1)" "$t"
    else
        printf '  %-8s %s (ABSENT -- skipped)\n' "--" "$t"
    fi
done

echo
echo "== live tempdir contents (CONTENTS ONLY -- the directory stays)"
if [[ -d "$TMPDIR_LIVE" ]]; then
    printf '  %-8s %s/*\n' "$(du -sh "$TMPDIR_LIVE" | cut -f1)" "$TMPDIR_LIVE"
    find "$TMPDIR_LIVE" -maxdepth 1 -type f -name 'dup-*' -printf '    %10s  %TY-%Tm-%Td %TH:%TM  %f\n' | sort -k2
else
    echo "  ABSENT -- skipped"
fi

echo
echo "== free space before"
df -h "$TB" | tail -1

if [[ $EXECUTE -eq 0 ]]; then
    echo
    echo "DRY RUN -- nothing deleted.  Re-run with --execute to apply."
    exit 0
fi

echo
echo "== EXECUTING"
for t in "${TARGETS[@]}"; do
    if [[ -d "$t" ]]; then
        echo "  rm -rf $t"
        rm -rf "$t"
    fi
done

if [[ -d "$TMPDIR_LIVE" ]]; then
    echo "  deleting CONTENTS of $TMPDIR_LIVE (directory preserved)"
    find "$TMPDIR_LIVE" -maxdepth 1 -mindepth 1 -name 'dup-*' -delete
    if [[ ! -d "$TMPDIR_LIVE" ]]; then
        echo "FATAL: the live tempdir was removed -- recreating" >&2
        mkdir -p "$TMPDIR_LIVE"
        exit 3
    fi
    echo "  tempdir still present: $(ls -ld "$TMPDIR_LIVE" | awk '{print $1, $3, $4}')"
fi

echo
echo "== free space after"
df -h "$TB" | tail -1
echo
echo "DONE"
