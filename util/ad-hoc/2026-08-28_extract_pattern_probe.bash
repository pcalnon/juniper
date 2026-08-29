#!/usr/bin/env bash
#######################################################################################################################################################################################################################################################
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc/2026-08-28_extract_pattern_probe.bash
# Author:      Paul Calnon
# Version:     1.0.0
# License:     MIT License
#
# Purpose:  Prove -- on a 1-second synthetic archive -- that the --exclude patterns intended for the 111 GB 2026-02-27 project
#           archive actually exclude what they name, BEFORE spending ~1 hour of USB I/O on a pass that might silently keep everything.
#
#           This is the same failure class the backup script carried three times: `tar --exclude` accepts a malformed or
#           mis-scoped pattern, matches nothing, exits 0, and says nothing. The only defence is measuring the result.
#
#           Specifically under test:
#             a) `--wildcards --no-wildcards-match-slash` so that `*` matches exactly ONE path segment (the repo name), so
#                `<prefix>/*/data` hits `<repo>/data` at repo top level and NOT `<repo>/src/nested/data`.
#             b) --strip-components=5 turning `home/pcalnon/Development/python/Juniper/<repo>/...` into `<repo>/...`.
#             c) that exclusion is matched against the ARCHIVED member name, i.e. before --strip-components is applied.
#
# Usage:    bash util/ad-hoc/2026-08-28_extract_pattern_probe.bash
#######################################################################################################################################################################################################################################################
set -euo pipefail

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

PREFIX="home/pcalnon/Development/python/Juniper"
STAGE="${WORK}/stage/${PREFIX}"

# Mirror the real archive's shape: repo top-level bulk dirs that must go, and a nested dir sharing a bulk name that must STAY.
for REPO_NAME in juniper-data juniper-cascor juniper-legacy; do
    mkdir -p "${STAGE}/${REPO_NAME}/src/nested/data" "${STAGE}/${REPO_NAME}/data" "${STAGE}/${REPO_NAME}/logs" "${STAGE}/${REPO_NAME}/.git"
    echo "keep"          > "${STAGE}/${REPO_NAME}/src/main.py"
    echo "keep nested"   > "${STAGE}/${REPO_NAME}/src/nested/data/payload.json"
    echo "DROP bulk"     > "${STAGE}/${REPO_NAME}/data/big.npz"
    echo "DROP logs"     > "${STAGE}/${REPO_NAME}/logs/run.log"
    echo "keep git"      > "${STAGE}/${REPO_NAME}/.git/config"
done

tar -czf "${WORK}/probe.tgz" -C "${WORK}/stage" "home"

#######################################################################################################################################################################################################################################################
# The candidate flags, exactly as the real extraction will use them.
EXCLUDES=()
for BULK in data logs dist build reports resources venv .mypy_cache .pytest_cache .ruff_cache; do
    EXCLUDES+=( "--exclude=${PREFIX}/*/${BULK}" )
done

OUT="${WORK}/out"
mkdir -p "${OUT}"
tar -xzf "${WORK}/probe.tgz" -C "${OUT}" \
    --wildcards --no-wildcards-match-slash \
    "${EXCLUDES[@]}" \
    --strip-components=5 \
    "${PREFIX}"

echo "=============================================================="
echo "extracted tree"
echo "=============================================================="
( cd "${OUT}" && find . -mindepth 1 -maxdepth 2 | sort | sed 's/^/   /' )

echo
echo "=============================================================="
echo "assertions"
echo "=============================================================="
FAILURES=0
assert_absent() {
    if [[ -e "${OUT}/$1" ]]; then
        echo "   FAIL present but should be excluded: $1" >&2
        FAILURES=$(( FAILURES + 1 ))
    else
        echo "   OK   excluded: $1"
    fi
}
assert_present() {
    if [[ -e "${OUT}/$1" ]]; then
        echo "   OK   kept:     $1"
    else
        echo "   FAIL missing but should be kept: $1" >&2
        FAILURES=$(( FAILURES + 1 ))
    fi
}

for REPO_NAME in juniper-data juniper-cascor juniper-legacy; do
    assert_absent  "${REPO_NAME}/data"
    assert_absent  "${REPO_NAME}/logs"
    assert_present "${REPO_NAME}/src/main.py"
    # The whole point of --no-wildcards-match-slash: a nested dir named `data` is SOURCE and must survive.
    assert_present "${REPO_NAME}/src/nested/data/payload.json"
    assert_present "${REPO_NAME}/.git/config"
done

echo
if (( FAILURES == 0 )); then
    echo "RESULT: PASS -- patterns exclude repo-top-level bulk only, strip-components lands repos at the root."
else
    echo "RESULT: FAIL -- ${FAILURES} assertion(s) failed; do NOT run the 111 GB pass with these flags." >&2
    exit 1
fi
