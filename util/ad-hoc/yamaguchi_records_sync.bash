#!/usr/bin/env bash
# Mirror the Yamaguchi certification records (logs, JSON, results -- never restored copies, temp trees or DB files) off the source spindle to sda1.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-26
# Status:     ad-hoc — one-off (the 2026-08-25 handoff's records re-sync). NOTE 2026-08-29: the
#             original reason given here — "the worktree hook refuses a `mountpoint -q … && rsync …`
#             chain" — is FALSE and was propagated into a later handoff before validation caught it.
#             Plain `&&` chains run fine; the hook refuses git aimed at ANOTHER checkout
#             (`cd <other> && git …`, `git -C <other> …`) plus a complexity heuristic on
#             multi-statement lines. The file is still worth keeping: the exclusion list is the
#             load-bearing part and must not be retyped by hand.
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
#
# NOTE 2026-08-29: Tier 3 retirement deleted the 63.9 GB the `restored/` exclusion was written
# to block, so it now guards ~16 KB across three drill dirs. KEEP IT ANYWAY -- it is a standing
# guard against the next drill recreating a large tree, not a statement about today's sizes.
rsync -a --itemize-changes \
    --exclude='restored/' --exclude='tmp/' --exclude='work/' --exclude='*.sqlite*' --exclude='dlist-query-*/' \
    "$SRC_ROOT/_yamaguchi_check" "$SRC_ROOT/_fresh_dlist_check" "$SRC_ROOT/_yamaguchi_drill" "$SRC_ROOT/_fresh_drill" \
    "$DEST/"

# _drill_scratch is a SEPARATE invocation, and deliberately so.
#
# Its restored/ is not a restored tree -- it is the nine PRESERVED SAMPLES that Tier 3 gate 5
# kept as the durable evidence of the class-2 restore drill (260 KB). They belong on sda1. But
# they were placed there ONCE, by the Tier 3 tool, and this script could not maintain them:
# _drill_scratch was absent from the source list AND `restored/` is excluded above.
#
# The filters are not merged into the call above because rsync matches each rule against the
# path relative to EACH transfer root. An `--include=/restored/***` broad enough to rescue
# _drill_scratch/restored would equally un-exclude _yamaguchi_drill/*/restored -- re-arming the
# 70 GB copy the exclusion exists to prevent. A second invocation cannot make that mistake.
DRILL_SCRATCH="$SRC_ROOT/_drill_scratch"
if [[ -d "$DRILL_SCRATCH" ]]; then
    # Preserved samples are ~260 KB. A drill that dumps a full restored tree here would
    # otherwise be copied silently; refuse loudly instead and let Tier 3 prune it first.
    scratch_kb=$(du -sk "$DRILL_SCRATCH" | cut -f1)
    if (( scratch_kb > 51200 )); then
        echo "REFUSE: $DRILL_SCRATCH is ${scratch_kb} KB (> 50 MB) -- expected the ~260 KB of" >&2
        echo "        preserved drill samples. Run util/ad-hoc/yamaguchi_retire_tier3.py first," >&2
        echo "        or raise this cap deliberately if the contents are genuinely wanted." >&2
        exit 3
    fi
    exec rsync -a --itemize-changes \
        --exclude='tmp/' --exclude='work/' --exclude='*.sqlite*' --exclude='dlist-query-*/' \
        "$DRILL_SCRATCH" "$DEST/"
fi
