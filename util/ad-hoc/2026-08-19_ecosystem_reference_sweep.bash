#!/usr/bin/env bash
# Exhaustive cross-repo reference sweep: "have I found every place that names this thing?"
#
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-08-19
# Status: ad-hoc — investigation (reusable; produced the snapshot-directory move's reference list)
# Retire when: superseded by a real cross-repo symbol/reference index.
# Related: notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md,
#          juniper-cascor#536, juniper-cascor#537
#
# WHY IT EXISTS
#   Before moving or renaming anything shared, the question is not "where is it defined?"
#   but "what else names it?". Grepping the obvious module is how you miss the shell
#   config, the systemd unit, and the sibling repo. On the snapshot-directory move this
#   sweep turned a confident two-constant list into eight load-bearing references,
#   including a systemd ReadWritePaths entry whose omission silently EPERMs every save,
#   and a published sub-package that had never adopted an override at all.
#
# WHAT IT DOES
#   Greps every Juniper repo for the given patterns and reports hits grouped into
#   LOAD-BEARING (code / config / units / compose / workflows / tests) and DOCS. Read-only.
#
# GROUPING IS BY PATH, NOT BY LINE
#   `grep -rn` emits `path:lineno:content`. Filtering the whole line put markdown notes in
#   the CODE group, because their CONTENT cites things like `constants_hdf5.py:45`. Every
#   group filter is therefore anchored with `^[^:]*` so it can only match the path field.
#
# TRUNCATION IS THE ENEMY
#   The first run of this sweep piped through `head -50` and hid a cross-repo reference in
#   juniper-canopy that mattered. This script therefore prints FULL counts per group and
#   only elides with an explicit "... N more (use --all)" line, so a short read can never
#   look like a complete one.
#
# USAGE
#   util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash [--all] PATTERN [PATTERN...]
#
#     --all   print every hit (default: 25 per group, with the elision line)
#
#   Patterns are extended-regex, passed to grep -E.
#
# EXAMPLES
#   ... 'JUNIPER_CASCOR_SNAPSHOTS_DIR' 'src/snapshots' 'cascor_snapshots'
#   ... --all 'ReadWritePaths|ProtectSystem'

set -uo pipefail

ROOT="${JUNIPER_ROOT:-/home/pcalnon/Development/python/Juniper}"
LIMIT=25
if [ "${1:-}" = "--all" ]; then
    LIMIT=0
    shift
fi
if [ "$#" -eq 0 ]; then
    sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
fi

REPOS=(juniper-cascor juniper-ml juniper-canopy juniper-data juniper-deploy
    juniper-recurrence juniper-cascor-client juniper-cascor-worker juniper-data-client)

# Noise that is never a real reference: VCS, caches, build output, coverage HTML,
# rotated logs, vendored deps, and OTHER worktrees (which duplicate every hit).
EXCLUDES=(
    --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.mypy_cache
    --exclude-dir=.pytest_cache --exclude-dir=.ruff_cache --exclude-dir=node_modules
    --exclude-dir=.venv --exclude-dir=venv --exclude-dir=htmlcov --exclude-dir=dist
    --exclude-dir=build --exclude-dir=site-packages --exclude-dir=worktrees
    --exclude-dir=cascor-snapshots --exclude-dir=cascor_snapshots
    --exclude-dir=snapshots --exclude-dir=logs
    --exclude=*.log --exclude=*.log.* --exclude=*.h5 --exclude=*.ipynb
)

present=()
for r in "${REPOS[@]}"; do
    [ -d "$ROOT/$r" ] && present+=("$ROOT/$r")
done
if [ "${#present[@]}" -eq 0 ]; then
    echo "no Juniper repos found under $ROOT" >&2
    exit 2
fi

pattern="$(
    IFS='|'
    echo "$*"
)"
echo "pattern : $pattern"
echo "repos   : ${#present[@]} of ${#REPOS[@]}"
echo

# $1 = group label, $2 = grep -E filter applied to the PATH of each hit
emit() {
    local label="$1" pathfilter="$2" hits count
    hits=$(grep -rnI "${EXCLUDES[@]}" -E "$pattern" "${present[@]}" 2>/dev/null |
        grep -E "$pathfilter" | sed "s|$ROOT/||" | sort)
    count=$(printf '%s' "$hits" | grep -c . || true)
    echo "########## $label — $count hit(s)"
    if [ "$count" -eq 0 ]; then
        echo "  (none)"
    elif [ "$LIMIT" -eq 0 ] || [ "$count" -le "$LIMIT" ]; then
        printf '%s\n' "$hits" | sed 's/^/  /'
    else
        printf '%s\n' "$hits" | head -n "$LIMIT" | sed 's/^/  /'
        echo "  ... $((count - LIMIT)) more (use --all)"
    fi
    echo
}

# Load-bearing first: these are the ones that break something when missed.
emit "CODE (py/sh/bash)" '^[^:]*\.(py|sh|bash):'
emit "CONFIG (conf/ini/toml/env/yaml/yml/json)" '^[^:]*(\.(conf|cfg|ini|toml|env|ya?ml|json)|/\.env[^:]*):'
emit "SYSTEMD UNITS + COMPOSE" '^[^:]*(\.(service|socket|timer)|docker-compose[^:]*|compose\.ya?ml):'
emit "CI WORKFLOWS" '^[^:]*/\.github/'
emit "OWNERSHIP / IGNORE FILES" '^[^:]*(CODEOWNERS|\.gitignore|\.dockerignore):'
emit "DOCS + NOTES (rarely load-bearing, still update)" '^[^:]*\.(md|rst|txt):'

echo "REMINDER: a hit in a systemd unit, a shell config, or a sibling repo is as"
echo "load-bearing as one in the module you were looking at. Check each before moving on."
