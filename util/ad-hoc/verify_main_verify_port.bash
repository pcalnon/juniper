#!/usr/bin/env bash
# Project     : Juniper
# Sub-Project : juniper-ml
# Application : cross-repo test fan-out verification (ad-hoc)
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-09-08
#
# Generate one repo's port of the main-verify catch-up-base test union, then PROVE
# it against that repo's REAL main-verify.yml -- positively (17 pass) and
# negatively (a one-character step rename must break it).
#
# Why the negative half is not optional
# -------------------------------------
# The whole failure mode being guarded is silent: rename the verdict step and the
# resolver quietly drops to the legacy tier while every check stays green. A port
# that cannot FAIL is worth nothing, and both upstream references SKIP rather than
# fail when the workflow or step is missing -- so a misplaced copy is silently
# green too. This script refuses to report success unless the drift case fails.
#
# The fixture is a throwaway root holding a COPY of the repo's workflow, so the
# sibling repo's working tree is never written to.
#
# Usage: bash util/ad-hoc/verify_main_verify_port.bash <repo-dir> <repo-slug> <project> <out-file> [marker]

set -uo pipefail

REPO_DIR="${1:?repo dir}"
SLUG="${2:?repo slug}"
PROJECT="${3:?project}"
OUT="${4:?out file}"
MARKER="${5:-}"

WF="$REPO_DIR/.github/workflows/main-verify.yml"
if [[ ! -f "$WF" ]]; then
    echo "FATAL: $WF not found" >&2
    exit 2
fi

GEN_ARGS=(--repo-slug "$SLUG" --project "$PROJECT" --out "$OUT")
if [[ -n "$MARKER" ]]; then
    GEN_ARGS+=(--marker "$MARKER")
fi
python3 util/ad-hoc/port_main_verify_drift_tests.py "${GEN_ARGS[@]}" || exit 3

FIX=$(mktemp -d)
trap 'rm -rf "$FIX"' EXIT

mkdir -p "$FIX/ok/.github/workflows" "$FIX/ok/tests"
cp "$WF" "$FIX/ok/.github/workflows/"
cp "$OUT" "$FIX/ok/tests/test_main_verify_catchup_base.py"

cp -r "$FIX/ok" "$FIX/drift"
sed -i 's/Assert screens reached a verdict/Assert screens reached a VERDICT/' "$FIX/drift/.github/workflows/main-verify.yml"

echo "== $PROJECT : POSITIVE (expect 17 OK)"
pos_out=$(cd "$FIX/ok" && python3 -m unittest tests.test_main_verify_catchup_base 2>&1)
pos_rc=$?
echo "$pos_out" | tail -3

echo "== $PROJECT : NEGATIVE (a renamed step MUST fail)"
neg_out=$(cd "$FIX/drift" && python3 -m unittest tests.test_main_verify_catchup_base 2>&1)
neg_rc=$?
echo "$neg_out" | tail -3

ran=$(sed -n 's/^Ran \([0-9]*\) tests.*/\1/p' <<<"$pos_out" | tail -1)

if (( pos_rc != 0 )); then
    echo "RESULT $PROJECT: FAIL -- the port does not pass against the real workflow"
    exit 1
fi
if (( neg_rc == 0 )); then
    echo "RESULT $PROJECT: FAIL -- VACUOUS: the drift case still passed"
    exit 1
fi
if [[ "$ran" != "17" ]]; then
    echo "RESULT $PROJECT: FAIL -- expected 17 tests, ran ${ran:-unknown}"
    exit 1
fi
echo "RESULT $PROJECT: PASS -- 17/17 green, drift case correctly red"
