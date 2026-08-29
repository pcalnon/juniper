#!/usr/bin/env bash
# Duplicati --run-script-after hook for the server-run Yamaguchi job (candidate A for
# plan §7 criterion 4). Runs AS ROOT inside duplicati-server after every operation.
#
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-08-25
# Status: ad-hoc — wip (DRAFT; not deployed; Paul picks the alerting architecture)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8),
#          util/ad-hoc/yamaguchi_watchdog.py (candidate B -- the one that also catches "never ran")
#
# DEPLOYMENT CONTRACT (security-relevant): the server runs this as root, so the
# deployed copy MUST be root-owned and not user-writable, or any user-level write
# becomes a root escalation. /usr/local/lib/duplicati/ does not exist yet -- `-D`
# creates it. Deploy with
#     sudo install -D -o root -g root -m 0755 util/ad-hoc/yamaguchi_run_script_after.bash \
#          /usr/local/lib/duplicati/yamaguchi_run_script_after.bash
# then add the job setting (GET/modify/PUT of backup 2 -- Paul-gated, it edits the live job):
#     --run-script-after=/usr/local/lib/duplicati/yamaguchi_run_script_after.bash
# Prove it on a forced failure with a THROWAWAY job (unreachable destination) carrying the
# same setting -- never by breaking the live job.
#
# Duplicati exports DUPLICATI__EVENTNAME (AFTER), DUPLICATI__OPERATIONNAME (Backup, ...),
# DUPLICATI__PARSED_RESULT (Success|Warning|Error|Fatal|Unknown), DUPLICATI__RESULTFILE
# (path to the result text), DUPLICATI__REMOTEURL, DUPLICATI__LOCALPATH -- and the job name
# as lower-case DUPLICATI__backup_name (RunScript.cs at the installed 2.3.0.4 tag sets
# option-derived names without case change; see /usr/lib/duplicati/run-script-example.sh).
#
# Limitation, by construction: this fires only when a run HAPPENS. A job that never
# runs (scheduler dead, job vanished, server down) never invokes it -- pair with the
# watchdog for that class.

set -uo pipefail

STATE_DIR="/var/local/duplicati-yamaguchi"
DESKTOP_USER="pcalnon"
DESKTOP_UID="1000"

mkdir -p "${STATE_DIR}"
chmod 0755 "${STATE_DIR}"

WHEN="$(date -Is)"
RESULT="${DUPLICATI__PARSED_RESULT:-Unknown}"
OP="${DUPLICATI__OPERATIONNAME:-?}"
NAME="${DUPLICATI__backup_name:-?}"

# Durable record first; world-readable so the user-side tooling can show it.
printf '%s %s %s result=%s\n' "${WHEN}" "${NAME}" "${OP}" "${RESULT}" >> "${STATE_DIR}/runs.log"
printf '%s %s %s result=%s\n' "${WHEN}" "${NAME}" "${OP}" "${RESULT}" > "${STATE_DIR}/last-run.status"
chmod 0644 "${STATE_DIR}/runs.log" "${STATE_DIR}/last-run.status"

if [[ "${RESULT}" != "Success" ]]; then
    {
        printf '=== %s  %s  %s  result=%s ===\n' "${WHEN}" "${NAME}" "${OP}" "${RESULT}"
        if [[ -n "${DUPLICATI__RESULTFILE:-}" && -r "${DUPLICATI__RESULTFILE}" ]]; then
            head -n 80 "${DUPLICATI__RESULTFILE}"
        else
            printf -- '--- no result file ---\n'
        fi
        printf '\n'
    } >> "${STATE_DIR}/failures.log"
    chmod 0644 "${STATE_DIR}/failures.log"

    # Best-effort desktop notification on the user's session bus. Never allowed to
    # affect the exit status; the durable record above is the real alert.
    if command -v notify-send > /dev/null 2>&1 && [[ -S "/run/user/${DESKTOP_UID}/bus" ]]; then
        runuser -u "${DESKTOP_USER}" -- env "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/${DESKTOP_UID}/bus" \
            notify-send --urgency=critical "Duplicati ${NAME} ${OP}: ${RESULT}" \
            "${WHEN}
See ${STATE_DIR}/failures.log" > /dev/null 2>&1 || true
    fi
fi

# Exit 0: the hook reported. A non-zero here only adds a warning to a run whose
# result is already recorded.
exit 0
