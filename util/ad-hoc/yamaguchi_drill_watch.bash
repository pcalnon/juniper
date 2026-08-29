#!/usr/bin/env bash
# Watch a transient drill unit: emit each new last-line of its log, then the verdict.
#
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-08-25
# Status: ad-hoc — investigation (Yamaguchi drill 2 session watcher)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: util/ad-hoc/duplicati_drill_fresh.py
#
# Exists because the worktree-isolation hook refuses compound inline shell, and the
# background-worker lease kills long in-process waits: the drill runs as a
# `systemd-run --user` unit and this watcher only READS its log. Usage:
#     bash util/ad-hoc/yamaguchi_drill_watch.bash <unit> <logfile> [poll-seconds]
set -u
UNIT="${1:?unit name}"
LOG="${2:?log file}"
POLL="${3:-60}"
last=""
# a misspelled or already-vanished unit "shows" Result=success -- refuse to watch nothing
if [[ "$(systemctl --user show "${UNIT}" -p LoadState --value 2>/dev/null)" == "not-found" ]]; then
    echo "UNIT NOT FOUND: ${UNIT} (transient units unload on exit -- read the log instead)"
    exit 1
fi
while systemctl --user is-active --quiet "${UNIT}"; do
    cur="$(tail -n 1 "${LOG}" 2>/dev/null || true)"
    if [[ "${cur}" != "${last}" ]]; then
        echo "PROGRESS: ${cur}"
        last="${cur}"
    fi
    sleep "${POLL}"
done
echo "UNIT FINISHED: ${UNIT} $(systemctl --user show "${UNIT}" -p Result -p ExecMainStatus 2>/dev/null | tr '\n' ' ') (a transient unit reads success once unloaded -- the verdict lines below are the signal)"
grep -E 'single restore invocation|RESTORED\+VERIFIED|live-source oracle|RESULT:|FATAL|Traceback|drilled dlist' "${LOG}" || echo "NO VERDICT LINES IN ${LOG}"
