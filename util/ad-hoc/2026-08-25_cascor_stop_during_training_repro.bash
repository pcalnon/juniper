#!/usr/bin/env bash
# Reproduce (and, against a patched tree, verify the fix for) the cascor stop-during-training leak.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-25
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-25_JUNIPER-CASCOR_DEV-SHM-LEAK-CHARACTERISATION.md §6;
#             the 2026-08-25 snapshot-arc handoff §2; util/ad-hoc/uvicorn_sigterm_atexit_probe.py
#
# What it does
# ------------
# Brings up ONE throwaway juniper-cascor service from an arbitrary source tree (so a patched
# scratch copy can be exercised without touching the shared checkout), on its own port with its
# own snapshot root and log dir, starts a real GPU training run on the in-process spiral
# fallback (no juniper-data leg needed), waits until the first hidden unit has been installed
# (=> the persistent candidate-worker pool exists and a deferred-unlink SharedMemory block is
# on disk), then sends exactly one SIGTERM to the uvicorn pid — the stop every fleet stop tool
# sends — and measures:
#
#   * time from SIGTERM to process death, and the wait status (143 / "killed by 15" is what
#     uvicorn's capture_signals re-raise produces; a clean exit is 0),
#   * which /dev/shm entries the run created and which of them survive the death,
#   * which descendant processes (forkserver, resource tracker, candidate workers) are
#     orphaned by the death, and whether the residue changes once they are SIGKILLed the way
#     util/reap_pytest_orphans.bash would kill them.
#
# It never touches any process it did not start: every pid it signals is either the uvicorn
# child it launched or a descendant recorded from that pid's process tree while it was alive.
# It never touches the shared snapshot archive (JUNIPER_CASCOR_SNAPSHOTS_DIR is redirected) and
# never rotates the shared checkout's log (JUNIPER_CASCOR_LOG_DIR is redirected).
#
# Attribution of /dev/shm entries (why the peer guard exists): the "created by this run" list is
# a before/after diff of /dev/shm restricted to the two cascor prefixes (juniper_train_* and
# sem.mp-*). That is only attributable to THIS run if no other host cascor process can create
# such entries during the window, so the script REFUSES to start while any host process has a
# cwd inside a juniper-cascor tree (a peer service, its workers, a worktree stack; Docker
# containers have their own /dev/shm namespace and are not a concern), and re-checks at the end:
# if a peer appeared mid-run, the report flags the leak lists as NOT SAFE TO REMOVE. Never feed
# shm_leaked_after_reap.txt to rm without that flag being false -- unlinking a peer's pending
# SharedMemory block is exactly the failure the characterisation doc's section 4 warns about.
#
# Usage
# -----
#   2026-08-25_cascor_stop_during_training_repro.bash <cascor-src-dir> <run-dir> [port]
#
# Environment: JUNIPER_CASCOR1_PY (default /opt/miniforge3/envs/JuniperCascor1/bin/python).
# Output: <run-dir>/report.json plus the raw evidence files it names. Exit 0 when the
# measurement completed (regardless of whether a leak was observed), non-zero on a harness
# failure (service never healthy, training never reached a hidden unit, ...).
set -euo pipefail

APP_DIR="${1:?usage: $0 <cascor-src-dir> <run-dir> [port]}"
RUN="${2:?usage: $0 <cascor-src-dir> <run-dir> [port]}"
PORT="${3:-8209}"
PY="${JUNIPER_CASCOR1_PY:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"
UVICORN="$(dirname "${PY}")/uvicorn"
BASE="http://127.0.0.1:${PORT}"
HIDDEN_UNIT_WAIT_S="${HIDDEN_UNIT_WAIT_S:-600}"
DEATH_WAIT_S="${DEATH_WAIT_S:-60}"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S.%N | cut -c1-12)" "$*"; }
now() { date +%s.%N; }

mkdir -p "${RUN}/logs" "${RUN}/snapshots"
: >"${RUN}/report.json"

# ------------------------------------------------------------------------------------------
# 0. Pre-flight: the port must be free, and nothing of ours may already be running.
# ------------------------------------------------------------------------------------------
if ss -tlnH "sport = :${PORT}" | grep -q .; then
    log "ERROR: something already listens on ${PORT}; refusing to proceed"
    exit 2
fi
# T6 re-baseline tripwire (2026-08-25 cross-session agreement): a cascor listener on 8230-8259
# means the GPU campaign is live; a 5-minute GPU contention would confound one of its cells.
if ss -tlnH | awk '{print $4}' | grep -Eq ':82[3-5][0-9]$'; then
    log "ERROR: a listener on 8230-8259 is present (T6 campaign tripwire); deferring this run"
    exit 5
fi
# Peer-cascor guard: any host process whose cwd is inside a juniper-cascor tree (service, worker,
# worktree stack) can create juniper_train_* / sem.mp-* entries and would corrupt the attribution
# below. Keyed on /proc/<pid>/cwd, not argv (argv lies; cwd does not).
peer_cascor_cwds() {
    # cwd inside a juniper-cascor tree AND a python interpreter: shells and editors parked in a
    # cascor checkout are not peers; a service, a forkserver, a worker or a stack driver is.
    local cwd pid exe
    while read -r cwd; do
        pid="${cwd#/proc/}"; pid="${pid%/cwd}"
        [[ "${pid}" == "$$" ]] && continue
        exe="$(readlink "/proc/${pid}/exe" 2>/dev/null || true)"
        case "$(basename "${exe}")" in python*) echo "${cwd}" ;; esac
    done < <(find /proc -maxdepth 2 -name cwd -lname '*juniper-cascor*' 2>/dev/null || true)
}
if [[ -n "$(peer_cascor_cwds)" ]]; then
    log "ERROR: another host process is running from a juniper-cascor tree; /dev/shm entries could not be attributed to this run. Refusing."
    peer_cascor_cwds | head -5 | while read -r p; do log "  peer: ${p} -> $(readlink "${p}" 2>/dev/null)"; done
    exit 6
fi
ls -1 /dev/shm | sort >"${RUN}/shm_before.txt"

# ------------------------------------------------------------------------------------------
# 1. Launch the service through a wrapper subshell that records the wait status.
# ------------------------------------------------------------------------------------------
(
    cd "${APP_DIR}"
    env LD_LIBRARY_PATH= \
        JUNIPER_CASCOR_SNAPSHOTS_DIR="${RUN}/snapshots" \
        JUNIPER_CASCOR_LOG_DIR="${RUN}/logs" \
        "${UVICORN}" api.app:create_app --factory --host 127.0.0.1 --port "${PORT}" \
        >"${RUN}/logs/uvicorn.stdout" 2>&1 &
    child=$!
    echo "${child}" >"${RUN}/uvicorn.pid"
    rc=0
    wait "${child}" || rc=$?
    echo "${rc} $(date +%s.%N)" >"${RUN}/uvicorn.exit"
) &
WRAPPER=$!

for _ in $(seq 1 240); do
    if curl -sf "${BASE}/v1/health" >/dev/null 2>&1; then break; fi
    sleep 0.5
done
if ! curl -sf "${BASE}/v1/health" >/dev/null 2>&1; then
    log "ERROR: service never became healthy on ${PORT}"
    kill -KILL "$(cat "${RUN}/uvicorn.pid" 2>/dev/null)" 2>/dev/null || true
    exit 3
fi
PID="$(cat "${RUN}/uvicorn.pid")"
log "service up: pid ${PID} on ${PORT} (tree ${APP_DIR})"

# ------------------------------------------------------------------------------------------
# 2. Start a real training run (in-process spiral fallback; both epoch knobs set, per hazard).
# ------------------------------------------------------------------------------------------
START_BODY='{"dataset":{"generator":"spiral","params":{"n_points_per_spiral":300,"n_rotations":2.0,"noise":0.05,"seed":7}},"params":{"max_epochs":10000,"output_epochs":10000,"max_iterations":30,"max_hidden_units":40}}'
START_RESP="$(curl -s -X POST "${BASE}/v1/training/start" -H 'content-type: application/json' -d "${START_BODY}")"
echo "${START_RESP}" >"${RUN}/start_response.json"
log "start: $(echo "${START_RESP}" | cut -c1-160)"

# ------------------------------------------------------------------------------------------
# 3. Wait until the first hidden unit is installed: pool alive + deferred-unlink block on disk.
# ------------------------------------------------------------------------------------------
hidden_units() {
    curl -s "${BASE}/v1/network" | "${PY}" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(-1); sys.exit(0)
d = d.get("data", d) if isinstance(d, dict) else {}
print(int(d.get("hidden_units", -1)))'
}
deadline=$(( $(date +%s) + HIDDEN_UNIT_WAIT_S ))
hu=-1
while (( $(date +%s) < deadline )); do
    hu="$(hidden_units)"
    if (( hu >= 1 )); then break; fi
    sleep 0.2
done
if (( hu < 1 )); then
    log "ERROR: no hidden unit within ${HIDDEN_UNIT_WAIT_S}s (hidden_units=${hu})"
    kill -KILL "${PID}" 2>/dev/null || true
    exit 4
fi
log "hidden_units=${hu}: training is in the output-retrain phase with a live pool"

# ------------------------------------------------------------------------------------------
# 4. Record the live state: descendants (2 levels: forkserver/tracker -> workers) and /dev/shm.
# ------------------------------------------------------------------------------------------
descendants() {
    local root="$1" kids grand
    kids="$(pgrep -P "${root}" || true)"
    for k in ${kids}; do
        echo "${k}"
        grand="$(pgrep -P "${k}" || true)"
        for g in ${grand}; do echo "${g}"; done
    done
}
descendants "${PID}" | sort -n >"${RUN}/descendants.txt"
ps -o pid=,ppid=,stat=,etimes=,args= -p "$(paste -sd, "${RUN}/descendants.txt")" >"${RUN}/descendants_ps.txt" 2>/dev/null || true
ls -1 /dev/shm | sort >"${RUN}/shm_live.txt"
# Prefix-restricted: only the two names cascor creates. Attributable to this run because the
# peer guard held at pre-flight (and is re-checked at the end).
comm -13 "${RUN}/shm_before.txt" "${RUN}/shm_live.txt" | grep -E '^(juniper_train_|sem\.mp-)' >"${RUN}/shm_created_by_run.txt" || true
log "descendants: $(wc -l <"${RUN}/descendants.txt"); /dev/shm entries created by this run: $(wc -l <"${RUN}/shm_created_by_run.txt")"
curl -s "${BASE}/v1/training/status" >"${RUN}/status_before_sigterm.json" || true

# ------------------------------------------------------------------------------------------
# 5. ONE SIGTERM to the uvicorn pid, then time its death.
# ------------------------------------------------------------------------------------------
T_SIG="$(now)"
kill -TERM "${PID}"
log "SIGTERM sent to ${PID}"
T_DEAD=""
end=$(( $(date +%s) + DEATH_WAIT_S ))
while (( $(date +%s) < end )); do
    if ! kill -0 "${PID}" 2>/dev/null; then T_DEAD="$(now)"; break; fi
    sleep 0.05
done
if [[ -z "${T_DEAD}" ]]; then
    log "process ${PID} still alive after ${DEATH_WAIT_S}s -> SIGKILL (recording as a hang)"
    kill -KILL "${PID}" 2>/dev/null || true
    sleep 0.5
    T_DEAD="$(now)"
    HUNG=1
else
    HUNG=0
fi
wait "${WRAPPER}" 2>/dev/null || true
EXIT_LINE="$(cat "${RUN}/uvicorn.exit" 2>/dev/null || echo 'unknown')"
sleep 1.0
ls -1 /dev/shm | sort >"${RUN}/shm_after_death.txt"
comm -12 "${RUN}/shm_created_by_run.txt" "${RUN}/shm_after_death.txt" >"${RUN}/shm_leaked_after_death.txt"
ALIVE_ORPHANS="$(for p in $(cat "${RUN}/descendants.txt"); do kill -0 "$p" 2>/dev/null && echo "$p"; done | paste -sd, || true)"
log "dead after $("${PY}" -c "print(round(${T_DEAD}-${T_SIG},3))")s; wait status line: ${EXIT_LINE}; orphans alive: ${ALIVE_ORPHANS:-none}"

# ------------------------------------------------------------------------------------------
# 6. Reaper-equivalent: SIGKILL every surviving descendant we recorded, then re-list /dev/shm.
# ------------------------------------------------------------------------------------------
for p in $(cat "${RUN}/descendants.txt"); do
    kill -KILL "$p" 2>/dev/null || true
done
sleep 2.0
ls -1 /dev/shm | sort >"${RUN}/shm_after_reap.txt"
comm -12 "${RUN}/shm_created_by_run.txt" "${RUN}/shm_after_reap.txt" >"${RUN}/shm_leaked_after_reap.txt"
# Peer re-check: if a peer cascor appeared during the window, the lists above may contain ITS
# entries and must not be removed.
PEER_AT_END=0
if [[ -n "$(peer_cascor_cwds)" ]]; then
    PEER_AT_END=1
    log "WARNING: a peer juniper-cascor process appeared during the run; shm_leaked_* lists are NOT safe to remove"
fi

# ------------------------------------------------------------------------------------------
# 7. Report.
# ------------------------------------------------------------------------------------------
"${PY}" - "${RUN}" "${T_SIG}" "${T_DEAD}" "${HUNG}" "${EXIT_LINE}" "${ALIVE_ORPHANS:-}" "${APP_DIR}" "${PEER_AT_END}" <<'EOF'
import json, os, sys
run, t_sig, t_dead, hung, exit_line, orphans, app_dir, peer_at_end = sys.argv[1:9]
def lines(name):
    p = os.path.join(run, name)
    return [l for l in open(p).read().splitlines() if l] if os.path.exists(p) else []
rc = exit_line.split()[0] if exit_line and exit_line != "unknown" else None
report = {
    "app_dir": app_dir,
    "hung_past_death_wait": bool(int(hung)),
    "sigterm_to_death_s": round(float(t_dead) - float(t_sig), 3),
    "wait_status": rc,
    "wait_status_meaning": ("killed by signal %d" % (int(rc) - 128)) if rc and rc.isdigit() and int(rc) > 128 else ("exit %s" % rc),
    "descendants_recorded": len(lines("descendants.txt")),
    "orphans_alive_after_death": [p for p in orphans.split(",") if p],
    "shm_created_by_run": lines("shm_created_by_run.txt"),
    "shm_leaked_after_death": lines("shm_leaked_after_death.txt"),
    "shm_leaked_after_reap": lines("shm_leaked_after_reap.txt"),
}
segs = [n for n in report["shm_leaked_after_reap"] if n.startswith("juniper_train_")]
sems = [n for n in report["shm_leaked_after_reap"] if n.startswith("sem.mp-")]
report["leak_signature"] = {"juniper_train_segments": len(segs), "sem_mp": len(sems)}
report["peer_cascor_present_at_end"] = bool(int(peer_at_end))
report["leak_lists_safe_to_remove"] = not bool(int(peer_at_end))
with open(os.path.join(run, "report.json"), "w") as fh:
    json.dump(report, fh, indent=2)
print(json.dumps(report, indent=2))
EOF
