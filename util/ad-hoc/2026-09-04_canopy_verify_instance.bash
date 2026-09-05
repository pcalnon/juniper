#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
# Bring up a SECOND canopy, from a worktree, beside the arc's shared isolated
# stack — so a fix can be verified live without tearing down the instance other
# sessions may be driving.
#
# WHY THIS EXISTS. "A checkout is not a deployment": the long-running canopy on
# :8051 serves the code it imported at launch, so a merged-or-not fix in a
# worktree is invisible to it. The naive move is to restart :8051 against the
# worktree, which makes the shared stack briefly disappear and silently swaps
# what every other session is looking at. A second instance on its own port,
# sharing the same cascor and juniper-data, changes nothing anyone else is using:
# canopy is a read-only dashboard over cascor's topology, and the controls under
# test here (the depth filter, the selection panel) are client-side.
#
# The cascor fixture is NEVER touched — this script does not POST /v1/network.
#
# REAPER NOTE. The instance is launched with nohup and so reparents to
# `systemd --user`, which is `util/reap_pytest_orphans.bash`'s orphan predicate.
# A pid file is written next to the log for exactly that reason: a pid appearing
# in a run-dir `*.pid` is one of the reaper's two protection keys. Leave it in
# place for the life of the instance.
#
# Usage:
#   2026-09-04_canopy_verify_instance.bash up   <worktree-src-dir> [port]
#   2026-09-04_canopy_verify_instance.bash down [port]
# ---------------------------------------------------------------------------
set -euo pipefail

ACTION="${1:-}"
RUN_DIR="${CANOPY_VERIFY_RUN_DIR:-/tmp/juniper-canopy-verify}"

case "$ACTION" in
up)
    SRC_DIR="${2:-}"
    PORT="${3:-8052}"
    if [[ -z "$SRC_DIR" || ! -f "$SRC_DIR/main.py" ]]; then
        echo "usage: $0 up <worktree-src-dir containing main.py> [port]" >&2
        exit 2
    fi
    mkdir -p "$RUN_DIR"
    LOG="$RUN_DIR/canopy-$PORT.log"
    PIDFILE="$RUN_DIR/canopy-$PORT.pid"

    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "already up: pid $(cat "$PIDFILE") on port $PORT" >&2
        exit 0
    fi

    # Same backends as the arc's isolated stack; only the listen port and the
    # WS origin allow-list differ, because those are the two settings that would
    # otherwise collide with :8051.
    export JUNIPER_CANOPY_SERVER__HOST=127.0.0.1
    export JUNIPER_CANOPY_SERVER__PORT="$PORT"
    export JUNIPER_CANOPY_CASCOR_SERVICE_URL="${JUNIPER_CANOPY_CASCOR_SERVICE_URL:-http://127.0.0.1:8202}"
    export JUNIPER_CANOPY_JUNIPER_DATA_URL="${JUNIPER_CANOPY_JUNIPER_DATA_URL:-http://127.0.0.1:8101}"
    export JUNIPER_CANOPY_CASCOR_WS_ORIGIN="http://127.0.0.1:$PORT"
    export JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS="[\"http://127.0.0.1:$PORT\",\"http://localhost:$PORT\"]"
    export JUNIPER_CANOPY_DEMO_MODE=0
    export JUNIPER_CANOPY_SNAPSHOT_DIR="${JUNIPER_CANOPY_SNAPSHOT_DIR:-/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots}"
    # JuniperCanopy1 is isolated from rust_mudgeon's LIBTORCH; the conda hooks
    # that strip these do NOT run when the interpreter is invoked directly.
    export LIBTORCH=
    export LD_LIBRARY_PATH=

    cd "$SRC_DIR"
    nohup /opt/miniforge3/envs/JuniperCanopy1/bin/python main.py >"$LOG" 2>&1 &
    echo $! >"$PIDFILE"
    echo "launched pid $(cat "$PIDFILE") on port $PORT"
    echo "  src : $SRC_DIR"
    echo "  log : $LOG"
    echo "  pid : $PIDFILE"

    for _ in $(seq 1 60); do
        code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:$PORT/v1/health" || true)
        if [[ "$code" == "200" ]]; then
            echo "healthy after $SECONDS s"
            exit 0
        fi
        sleep 1
    done
    echo "did NOT become healthy within 60 s — see $LOG" >&2
    exit 1
    ;;
down)
    PORT="${2:-8052}"
    PIDFILE="$RUN_DIR/canopy-$PORT.pid"
    if [[ ! -f "$PIDFILE" ]]; then
        echo "no pid file at $PIDFILE — nothing to stop" >&2
        exit 0
    fi
    PID=$(cat "$PIDFILE")
    # Teardown BY PID, never by port: killing whatever listens on a port stops
    # processes this script did not start.
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        for _ in $(seq 1 20); do
            kill -0 "$PID" 2>/dev/null || break
            sleep 1
        done
        kill -0 "$PID" 2>/dev/null && kill -9 "$PID" || true
        echo "stopped pid $PID"
    else
        echo "pid $PID not running"
    fi
    rm -f "$PIDFILE"
    ;;
*)
    echo "usage: $0 {up <worktree-src-dir> [port] | down [port]}" >&2
    exit 2
    ;;
esac
