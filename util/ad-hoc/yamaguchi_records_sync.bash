#!/usr/bin/env bash
# Mirror the Yamaguchi certification records (logs, JSON, results -- never restored copies, temp trees or DB files) off the source spindle to sda1.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-26
# Status:     ad-hoc — one-off (the 2026-08-25 handoff's records re-sync, made a file because the
#             worktree hook refuses a `mountpoint -q … && rsync …` chain at the prompt)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8);
#             prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-25_duplicati-widened-scope-recertified-paul-gated-tail.md (§2 item 7)
set -euo pipefail

SRC_ROOT=/media/pcalnon/temp_backups
DEST=/mnt/Backups/Ubuntu/_yamaguchi_records

# /mnt/Backups itself is NOT a mountpoint (§5): every write under it is guarded on the sda1 mount,
# else a vanished mount would land the records on the root filesystem.
if ! mountpoint -q /mnt/Backups/Ubuntu; then
    echo "REFUSE: /mnt/Backups/Ubuntu is not a mountpoint" >&2
    exit 2
fi
if ! mountpoint -q "$SRC_ROOT"; then
    echo "REFUSE: $SRC_ROOT is not a mountpoint" >&2
    exit 2
fi

# Same exclusions as the handoff's command: restored trees (~70 GB), temp/work dirs, every
# SQLite file (temp DBs from drills), and the dlist-query extraction dirs.
exec rsync -a --itemize-changes \
    --exclude='restored/' --exclude='tmp/' --exclude='work/' --exclude='*.sqlite*' --exclude='dlist-query-*/' \
    "$SRC_ROOT/_yamaguchi_check" "$SRC_ROOT/_fresh_dlist_check" "$SRC_ROOT/_yamaguchi_drill" "$SRC_ROOT/_fresh_drill" \
    "$DEST/"
