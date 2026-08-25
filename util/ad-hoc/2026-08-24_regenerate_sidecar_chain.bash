#!/usr/bin/env bash
# Regenerate the snapshot sidecar chain end to end, in dependency order.
#
# Project:      Juniper
# Sub-Project:  juniper-ml
# File Name:    2026-08-24_regenerate_sidecar_chain.bash
# Author:       Paul Calnon
# License:      MIT License
# Status:       ad-hoc -- operational (one-off, may graduate to util/)
# Retire when:  a supported "refresh the sidecars" entry point exists in util/.
#
# WHY A CHAIN. The four sidecars are strictly ordered: index -> classification ->
# attribution -> backfill. Each reads its predecessor's output, so regenerating one
# in isolation leaves the rest describing a different archive. Attribution in
# particular reads the classification sidecar and covers only what it lists, so a
# stale classification silently caps attribution's coverage.
#
# WHY THE ENV VAR IS DELIBERATELY *NOT* SET. `JUNIPER_CASCOR_SNAPSHOTS_DIR` is BOTH
# cascor's snapshot write directory AND `snapshot_index.default_root()`. The probe
# scripts in this directory redirect it so they cannot grow the archive; this script
# must NOT, or every tool would look for the archive in the scratch dir. `--root` is
# passed explicitly instead, so resolution does not depend on the environment at all.
# None of these four tools trains, so none can create a snapshot: they load and
# forward-pass only, and each carries an AST test proving it has no delete path.
#
# Usage:
#     util/ad-hoc/2026-08-24_regenerate_sidecar_chain.bash [--root DIR] [--dry-run] [--skip-index]
#
# BACK UP FIRST. The sidecars are gitignored, and a full run costs the better part of
# an hour. This script refuses to start unless a backup directory is named.

set -euo pipefail

ROOT="/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots"
REPO="/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/merry-puzzling-quasar"
PYTHON="/opt/miniforge3/envs/JuniperCascor1/bin/python"
DRY_RUN=0
SKIP_INDEX=0
BACKUP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        --repo) REPO="$2"; shift 2 ;;
        --python) PYTHON="$2"; shift 2 ;;
        --backup) BACKUP="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --skip-index) SKIP_INDEX=1; shift ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

if [[ ! -d "$ROOT" ]]; then
    echo "ERROR: snapshot root not found: $ROOT" >&2
    exit 2
fi
if [[ -z "$BACKUP" ]]; then
    echo "ERROR: --backup DIR is required; the sidecars are gitignored and a rebuild costs ~1h" >&2
    exit 2
fi
if [[ ! -d "$BACKUP" ]]; then
    echo "ERROR: backup directory does not exist (create it and copy the sidecars first): $BACKUP" >&2
    exit 2
fi
for name in snapshots_index snapshots_classification snapshots_attribution snapshots_backfill; do
    if [[ ! -f "${BACKUP}/${name}.jsonl" ]]; then
        echo "ERROR: backup is incomplete -- missing ${name}.jsonl in ${BACKUP}" >&2
        exit 2
    fi
done

echo "root:   ${ROOT}"
echo "backup: ${BACKUP} (verified complete)"
echo "python: ${PYTHON}"
echo "files on disk: $(find "$ROOT" -maxdepth 1 -name '*.h5' -type f | wc -l)"
echo

run_stage() {
    local label="$1"; shift
    echo "=================================================================="
    echo "STAGE: ${label}"
    echo "  \$ $*"
    echo "  started $(date -Is)"
    echo "=================================================================="
    if (( DRY_RUN )); then
        echo "  [dry-run] not executed"
        return 0
    fi
    local start finish
    start="$(date +%s)"
    "$@"
    finish="$(date +%s)"
    echo "  ${label} finished in $((finish - start))s at $(date -Is)"
    echo
}

cd "$REPO"

if (( ! SKIP_INDEX )); then
    # Append-only: indexes snapshots not already present, so it is cheap even though
    # the archive has grown. --rebuild is deliberately NOT used.
    run_stage "1/4 index (append-only scan)" "$PYTHON" util/snapshot_index.py --root "$ROOT" --scan
fi

# No incremental mode: this re-derives every row, and it is the expensive stage
# (~15 min) because it asks cascor's own loader about each file.
run_stage "2/4 classify (--stage load)" "$PYTHON" util/snapshot_classify.py --root "$ROOT" --stage load --write

# The regeneration this chain exists for: schema v2, both floors.
run_stage "3/4 attribute (two-floor, schema v2)" "$PYTHON" util/snapshot_attribute.py --root "$ROOT" --write --stats

# Consolidates the three above into one record per snapshot.
run_stage "4/4 backfill (consolidate)" "$PYTHON" util/snapshot_backfill.py --root "$ROOT" --write --stats

echo "=================================================================="
echo "CHAIN COMPLETE $(date -Is)"
echo "=================================================================="
wc -l "$ROOT"/snapshots_index.jsonl "$ROOT"/snapshots_classification.jsonl \
      "$ROOT"/snapshots_attribution.jsonl "$ROOT"/snapshots_backfill.jsonl
