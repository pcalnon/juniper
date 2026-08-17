#!/usr/bin/env bash
# reap_pytest_orphans.bash - Find and kill orphaned multiprocessing
# forkserver / worker children left behind by crashed pytest sessions
# in any Juniper worktree.
#
# Background: cascor (and other Juniper) tests use multiprocessing,
# typically via the forkserver context. When pytest is SIGKILL'd
# (OOM kill, terminal closed, kill -9, etc.) before its session-end
# cleanup can run, the forkserver and its worker children survive
# as orphans. The forkserver eventually notices the parent is gone
# via a heartbeat pipe, but that detection takes many minutes — and
# in the meantime each orphan can hold ~300-500 MB RSS.
#
# This script identifies orphans and reaps them safely:
#   - Targets only Python processes whose command-line references a
#     Juniper conda env or worktree path
#   - Checks each candidate's parent PID and only kills processes whose
#     parent (a) no longer exists OR (b) is PID 1 (init reparented).
#     Live-parent processes are skipped — they belong to a still-running
#     pytest session somewhere on the system.
#   - Protects live experiment stacks / campaigns outright, whatever their
#     parentage (see "Live-experiment protection" below).
#
# Usage:
#   reap_pytest_orphans.bash [--dry-run] [--verbose]
#
#   --dry-run   List what would be killed without actually killing
#   --verbose   Print every candidate considered, including kept ones
#
# Exit codes:
#   0 - success (zero or more orphans reaped)
#   2 - argument error
#
# Project:    Juniper
# Author:     Paul Calnon
# License:    MIT License

set -euo pipefail

DRY_RUN=0
VERBOSE=0
PROC_ROOT="${JUNIPER_REAP_PROC_ROOT:-/proc}"
KILL_CMD="${JUNIPER_REAP_KILL_CMD:-kill}"

usage() {
    cat <<EOF
Usage: $(basename "$0") [--dry-run] [--verbose]

Find and kill multiprocessing forkserver / worker orphans left behind
by crashed pytest sessions in any Juniper worktree.

Options:
  --dry-run   List candidates without killing them
  --verbose   Print every candidate, including those kept (live parent)
  -h, --help  Show this help

A process is considered an orphan if:
  - its command line references a Juniper conda env or worktrees/ path
  - AND its parent is gone, is PID 1 (init), or is the user-session
    "systemd --user" (which adopts orphaned user processes)
  - AND it is not part of a live experiment stack / campaign

Environment:
  JUNIPER_EXP_RUN_ROOT   experiment run root protected from reaping
                         (default: \${HOME}/.local/state/juniper-experiments)
  JUNIPER_E2E_RUN_DIR    isolated-stack run dir protected from reaping
                         (default: \${TMPDIR:-/tmp}/juniper-e2e)
EOF
}

# --- Live-experiment protection -------------------------------------------
#
# ``experiment_stack.bash`` and ``isolated_stack.bash`` launch their services
# with ``nohup`` inside a subshell, so the services reparent to
# ``systemd --user`` — which is precisely this script's orphan predicate. A
# campaign orchestrator or watchdog started with setsid/disown lands there
# too. Reaping any of them destroys a healthy, in-flight campaign, so they are
# excluded ahead of the orphan decision on two independent keys:
#
#   P1  the pid is recorded in a run-dir ``*.pid`` file  — the services, which
#       ``record_listener_pid`` pidfiles after their health gate
#   P2  the pid's cmdline references a run root          — orchestrators,
#       drivers and watchdog shells, none of which carry a pidfile
#
# Over-protection is deliberately the safe direction: the cost of a false
# protect is one retained orphan holding RSS until the next sweep, while the
# cost of a false reap is a destroyed multi-hour campaign.
EXP_RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME:-}/.local/state/juniper-experiments}"
E2E_RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"

declare -A PROTECTED_PIDS=()

collect_protected_pids() {
    local root pidfile pid
    for root in "${EXP_RUN_ROOT}" "${E2E_RUN_DIR}"; do
        [[ -n "${root}" && -d "${root}" ]] || continue
        # Service pidfiles sit at <root>/<RUN_ID>/<svc>.pid and relay pids at
        # <root>/<RUN_ID>/relays/<svc>.pid; the isolated stack writes at depth 1.
        while IFS= read -r pidfile; do
            pid=$(head -n 1 "${pidfile}" 2>/dev/null || true)
            [[ "${pid}" =~ ^[0-9]+$ ]] || continue
            PROTECTED_PIDS["${pid}"]=1
        done < <(find "${root}" -maxdepth 3 -type f -name '*.pid' 2>/dev/null)
    done
}

# True when this candidate belongs to a live experiment stack / campaign.
is_experiment_protected() {
    local pid="$1" cmdline="$2" root
    if [[ -n "${PROTECTED_PIDS[${pid}]:-}" ]]; then
        return 0
    fi
    for root in "${EXP_RUN_ROOT}" "${E2E_RUN_DIR}"; do
        if [[ -n "${root}" && "${cmdline}" == *"${root}"* ]]; then
            return 0
        fi
    done
    return 1
}

# Resolve the user's systemd --user PID once (the implicit reaper for
# user-process orphans on systemd-based systems).
resolve_user_systemd_pid() {
    local me
    me=$(id -un)
    ps -eo pid=,user=,cmd= |
        awk -v me="${me}" '$2 == me && $0 ~ /systemd --user/ {print $1; exit}'
}
SYSTEMD_USER_PID=$(resolve_user_systemd_pid || true)

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --verbose)
            VERBOSE=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

collect_protected_pids

# Collect candidate PIDs: any Python process whose cmdline references a
# Juniper conda env or a Juniper worktree path. ``ps -eo pid,cmd`` is
# portable; restrict to the current user via the absent --user filter
# falling back to ``id -un`` so we never touch other users' processes.
readarray -t CANDIDATES < <(
    ps -eo pid=,user=,cmd= |
        awk -v me="$(id -un)" '$2 == me && /python/ && (/JuniperC[a-z0-9]+/ || /Juniper\/worktrees\//) {print $1}'
)

if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
    echo "No Juniper python processes found."
    exit 0
fi

REAPED=0
KEPT=0
PROTECTED=0
SKIPPED=0

for pid in "${CANDIDATES[@]}"; do
    # Skip if the process disappeared between the ps and now.
    if [[ ! -d "${PROC_ROOT}/${pid}" ]]; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Read parent PID from /proc/<pid>/status.
    ppid=$(awk '/^PPid:/ {print $2}' "${PROC_ROOT}/${pid}/status" 2>/dev/null || echo "")
    if [[ -z "${ppid}" ]]; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Read the full cmdline (P2 matches against it) plus a short summary for
    # logging. Substring-slice rather than ``head -c`` so ``pipefail`` cannot
    # turn a truncated read into a script abort.
    cmd_full=$(tr '\0' ' ' <"${PROC_ROOT}/${pid}/cmdline" 2>/dev/null || echo "")
    cmd_summary=${cmd_full:0:120}

    # A live experiment stack / campaign is never an orphan, however it is
    # parented. Checked BEFORE the orphan predicate so the reported reason is
    # the real one rather than an incidental live-parent coincidence.
    if is_experiment_protected "${pid}" "${cmd_full}"; then
        echo "PROTECT    pid=${pid} ppid=${ppid} (live experiment) cmd=${cmd_summary}"
        PROTECTED=$((PROTECTED + 1))
        continue
    fi

    # Decide: orphan if parent is PID 1 (init), parent is the user's
    # ``systemd --user`` (the implicit reaper for orphaned user
    # processes), or parent process no longer exists. Anything else is
    # a live test run we mustn't disturb.
    is_orphan=0
    if [[ "${ppid}" == "1" ]]; then
        is_orphan=1
    elif [[ -n "${SYSTEMD_USER_PID}" && "${ppid}" == "${SYSTEMD_USER_PID}" ]]; then
        is_orphan=1
    elif [[ ! -d "${PROC_ROOT}/${ppid}" ]]; then
        is_orphan=1
    fi

    if [[ "${is_orphan}" == "1" ]]; then
        if [[ "${DRY_RUN}" == "1" ]]; then
            echo "WOULD REAP pid=${pid} ppid=${ppid} cmd=${cmd_summary}"
        else
            echo "REAP       pid=${pid} ppid=${ppid} cmd=${cmd_summary}"
            "${KILL_CMD}" -KILL "${pid}" 2>/dev/null || true
        fi
        REAPED=$((REAPED + 1))
    else
        if [[ "${VERBOSE}" == "1" ]]; then
            echo "KEEP       pid=${pid} ppid=${ppid} (live parent) cmd=${cmd_summary}"
        fi
        KEPT=$((KEPT + 1))
    fi
done

echo "---"
if [[ "${DRY_RUN}" == "1" ]]; then
    echo "Dry-run summary: ${REAPED} would be reaped, ${KEPT} kept (live parent), ${PROTECTED} protected (live experiment), ${SKIPPED} skipped."
else
    echo "Summary: ${REAPED} reaped, ${KEPT} kept (live parent), ${PROTECTED} protected (live experiment), ${SKIPPED} skipped."
fi
