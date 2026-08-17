#!/usr/bin/env bash
# Plausibility probe: is grafana-server's HTTP port settable at START TIME, without root?
#
# Project: juniper-ml
# Sub-Project: ad-hoc tooling
# Author: Paul Calnon
# Created: 2026-08-17
# Status: ad-hoc — investigation (answers the owner's F-P1-2 / D-1 question)
# Retire when: the native grafana-server is repointed or disabled and D-1 is closed.
# Related: notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_F-P1-2-GRAFANA-RENDER-CLOSURE-EVIDENCE.md
#          (§5, D-1 and its 2026-08-17 update), juniper-ml#1136
#
# WHY
#   D-1 recorded that the packaged grafana-server is in a hard restart loop because it cannot
#   bind :3000 (the Domotz agent owns it), and proposed a root-level systemd drop-in. The owner
#   asked whether the port could instead be configured at server start — command line, env var,
#   or config file — before settling for a hard-coded fix. This answers that empirically rather
#   than from documentation.
#
# WHAT IT PROVES
#   Runs the PACKAGED grafana binary as the CURRENT (unprivileged) user against scratch
#   data/log/plugin dirs, once per mechanism, and checks whether it actually binds the target
#   port and serves /api/health.
#
# SAFETY
#   Touches nothing under /etc, /var, or the running grafana-server unit; starts nothing on
#   :3000; each case is bounded (~25 s) and killed afterwards; residual listeners are reported.
#   It only ever READS the packaged binary.
#
# USAGE
#   util/ad-hoc/2026-08-17_grafana_port_probe.sh <scratch-dir> [port]
#
# RESULT ON THIS HOST (2026-08-17, grafana 13.0.1): both mechanisms bound :3002 with
# /api/health -> 200 "database: ok". The port is hard-coded nowhere; the only real blocker to
# applying it to the SYSTEM service is file ownership (root), which is a property of system
# services and outside juniper-ml's scope.

set -u

SCRATCH="${1:?usage: $0 <scratch-dir> [port]}"
PORT="${2:-3002}"
GRAFANA_BIN="${GRAFANA_BIN:-/usr/share/grafana/bin/grafana}"
GRAFANA_HOME="${GRAFANA_HOME:-/usr/share/grafana}"

if [ ! -x "$GRAFANA_BIN" ]; then
    echo "grafana binary not executable: $GRAFANA_BIN" >&2
    exit 2
fi
if ss -tlnH "sport = :${PORT}" | grep -q .; then
    echo "refusing: something already listens on :${PORT}" >&2
    exit 2
fi

mkdir -p "$SCRATCH"/{data,logs,plugins,provisioning}

run_case() {
    local label="$1"
    shift
    echo "=== $label ==="
    ("$@" >"$SCRATCH/${label}.log" 2>&1 & echo $! >"$SCRATCH/${label}.pid")
    local pid bound="" code=""
    pid=$(cat "$SCRATCH/${label}.pid")
    for _ in $(seq 1 25); do
        sleep 1
        code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/api/health" 2>/dev/null || true)
        if [ "$code" = "200" ]; then
            bound=yes
            break
        fi
        kill -0 "$pid" 2>/dev/null || break
    done
    if [ "$bound" = yes ]; then
        echo "  RESULT: bound :$PORT, /api/health -> 200"
        curl -s "http://127.0.0.1:${PORT}/api/health" | head -5 | sed 's/^/    /'
    else
        echo "  RESULT: did NOT bind :$PORT (last code='${code:-none}')"
        tail -6 "$SCRATCH/${label}.log" 2>/dev/null | sed 's/^/    /'
    fi
    kill "$pid" 2>/dev/null
    wait "$pid" 2>/dev/null
    echo
}

# (a) command line — the same cfg: override the packaged unit already uses for its four paths
run_case cli "$GRAFANA_BIN" server \
    --homepath="$GRAFANA_HOME" \
    "cfg:server.http_port=${PORT}" \
    "cfg:paths.data=$SCRATCH/data" \
    "cfg:paths.logs=$SCRATCH/logs" \
    "cfg:paths.plugins=$SCRATCH/plugins" \
    "cfg:paths.provisioning=$SCRATCH/provisioning"

# (b) environment variable — GF_<SECTION>_<KEY>, the form /etc/default/grafana-server would carry
GF_SERVER_HTTP_PORT="$PORT" \
    GF_PATHS_DATA="$SCRATCH/data" \
    GF_PATHS_LOGS="$SCRATCH/logs" \
    GF_PATHS_PLUGINS="$SCRATCH/plugins" \
    GF_PATHS_PROVISIONING="$SCRATCH/provisioning" \
    run_case env "$GRAFANA_BIN" server --homepath="$GRAFANA_HOME"

echo "=== residual listeners on :$PORT (expect none) ==="
ss -tlnH "sport = :$PORT" || true
