#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Duplicati Scheduled Backup Runner
# Author:       Paul Calnon
# Version:      1.0.0
# License:      MIT
############################################################################################################################################################
#
# Runs the "Ubuntu-fresh" Duplicati backup under `systemd --user`, independent of
# the GNOME tray instance and of Duplicati's own internal scheduler.
#
# WHY THIS EXISTS
#   The 2026-07-13 archive damage went undetected for six weeks because the only
#   thing running backups was a gnome-shell-launched scope under a user manager
#   with Linger=no: it died at logout and nothing said so. Measured 2026-08-23:
#   the server DB's Schedule table is EMPTY -- neither job is scheduled at all.
#   This script plus its .timer is the replacement, and it depends on neither the
#   tray process nor the Duplicati server.
#
# GUARDS -- each encodes a failure actually observed in this arc
#   1. PASSPHRASE must be present and non-empty. Otherwise Duplicati either
#      prompts (hanging a timer job forever) or writes an archive nobody can open.
#   2. The destination must be a real mountpoint. An unmounted path resolves to an
#      empty directory on / and reads to Duplicati as "everything is missing",
#      which is not an error -- it is a silently wrong answer.
#   3. The destination must be empty, or already hold duplicati-* volumes. Catches
#      a mount that succeeded onto the WRONG filesystem.
#   4. flock, non-blocking. Two concurrent runs against one local DB corrupt it.
#      `pgrep -f <pattern>` must NOT be used for this: it matches its own command
#      line and returns a false positive. That bug already produced a wrong status
#      line once in this arc.
#
# NOTES ON PRESERVED FLAGS
#   --no-auto-compact=true is deliberate and load-bearing. An interrupted compact
#   on 2026-07-13 deleted 1,208 dblock/dindex pairs and wrote zero replacements,
#   which is what destroyed the July restore points. Do not remove it without a
#   considered decision about compaction safety.
#
# Every knob is overridable by environment, so the pending migration back to
# /mnt/Backups/Ubuntu is a config edit rather than a script edit.
############################################################################################################################################################

set -euo pipefail

DEST_URL="${DUPLICATI_DEST_URL:-file:///media/pcalnon/temp_backups/Ubuntu}"
DEST_PATH="${DUPLICATI_DEST_PATH:-/media/pcalnon/temp_backups/Ubuntu}"
DEST_MOUNT="${DUPLICATI_DEST_MOUNT:-/media/pcalnon/temp_backups}"
DBPATH="${DUPLICATI_DBPATH:-/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite}"
SOURCE_PATH="${DUPLICATI_SOURCE:-/home/pcalnon}"
STATE_DIR="${DUPLICATI_STATE_DIR:-${HOME}/.local/state/duplicati}"

LOCK_FILE="${STATE_DIR}/backup.lock"
TS="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="${STATE_DIR}/backup-${TS}.log"
STATUS_FILE="${STATE_DIR}/last-run.status"

mkdir -p "${STATE_DIR}"

log() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "${LOG_FILE}"; }

write_status() {
    printf 'result=%s\nwhen=%s\nreason=%s\nlog=%s\n' \
        "$1" "$(date -Is)" "$2" "${LOG_FILE}" > "${STATUS_FILE}"
}

fail() {
    log "FATAL: $*"
    write_status FAILED "$*"
    exit 1
}

# --- Guard 1: the secret must be present -------------------------------------
[[ -n "${PASSPHRASE:-}" ]] || fail "PASSPHRASE is unset or empty; refusing to run"

# --- Guard 2: the destination must actually be mounted -----------------------
mountpoint -q "${DEST_MOUNT}" \
    || fail "${DEST_MOUNT} is NOT a mountpoint; refusing (an unmounted destination reads as 'everything is missing')"

[[ -d "${DEST_PATH}" ]] || fail "${DEST_PATH} does not exist"
[[ -w "${DEST_PATH}" ]] || fail "${DEST_PATH} is not writable"

# --- Guard 3: empty, or already ours -----------------------------------------
if [[ -n "$(ls -A "${DEST_PATH}" 2>/dev/null)" ]]; then
    compgen -G "${DEST_PATH}/duplicati-*" > /dev/null \
        || fail "${DEST_PATH} is non-empty but holds no duplicati-* volumes; wrong filesystem?"
fi

# --- Guard 4: exactly one runner ---------------------------------------------
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    log "another run holds ${LOCK_FILE}; exiting 0 (not an error)"
    exit 0
fi

# --- Guard 5: no hand-started backup already in flight ------------------------
# flock only serialises runs started THROUGH this script. A backup launched by
# hand -- exactly how the 2026-08-23 fresh set was seeded -- holds no lock, so
# the timer could otherwise start a second writer against the same local DB.
# The bracket in '[d]uplicati-cli' keeps this grep from matching itself; a plain
# `pgrep -f` here would always self-match and report a permanent false positive.
if ps -eo args | grep -q '^[d]uplicati-cli backup'; then
    log "a duplicati-cli backup is already running (started outside this script); exiting 0"
    exit 0
fi

log "starting backup"
log "  source      ${SOURCE_PATH}"
log "  destination ${DEST_URL}"
log "  dbpath      ${DBPATH}"

set +e
duplicati-cli backup "${DEST_URL}" "${SOURCE_PATH}" \
    --dbpath="${DBPATH}" \
    --encryption-module=gpg \
    --compression-module=zip \
    --blocksize=1MB \
    --dblock-size=500MB \
    --skip-files-larger-than=2GB \
    --no-auto-compact=true \
    --allow-missing-source=true \
    "--exclude=/home/pcalnon/Development/rust/tch-rs/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/juniper/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/juniper/libs/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/tensors/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/min_via/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/adamo/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/mandelbrot/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/advent_of_code/2021/day24/prob1/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/advent_of_code/2021/day19/prob1/target/" \
    "--exclude=/home/pcalnon/Development/rust/rust_mudgeon/reference/nerd_snipe/target/" \
    "--exclude=/home/pcalnon/Development/llms/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/jupyter/backups/.ipynb_checkpoints/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/logs/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/resources/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/data/" \
    "--exclude=/home/pcalnon/.sudo_as_admin_successful" \
    "--exclude=/home/pcalnon/.python_history-58693.tmp" \
    "--exclude=/home/pcalnon/.python_history-32739.tmp" \
    "--exclude=/home/pcalnon/.bash_history-51918.tmp" \
    "--exclude=/home/pcalnon/.bash_history-40075.tmp" \
    "--exclude=/home/pcalnon/.bash_history-25805.tmp" \
    "--exclude=/home/pcalnon/.bash_history-21251.tmp" \
    "--exclude=/home/pcalnon/.bash_history-09616.tmp" \
    "--exclude=/home/pcalnon/.bash_history-11775.tmp" \
    "--exclude=/home/pcalnon/SteamMods/" \
    "--exclude=/home/pcalnon/SteamGames/" \
    "--exclude=/home/pcalnon/StarfieldMods/" \
    "--exclude=/home/pcalnon/Dropbox/" \
    "--exclude=/home/pcalnon/FiraxisLive/" \
    "--exclude=/home/pcalnon/Downloads/" \
    "--exclude=/home/pcalnon/Desktop/" \
    "--exclude=/home/pcalnon/.thunderbird/" \
    "--exclude=/home/pcalnon/.dropbox/" \
    "--exclude=/home/pcalnon/.dropbox-dist/" \
    "--exclude=/home/pcalnon/.steam/steam/steamapps/common/Stardew Valley/Mods/zoe_mods/" \
    "--exclude=/home/pcalnon/snap/" \
    "--exclude=/home/pcalnon/.cache/" \
    "--exclude=/home/pcalnon/.local/share/Steam/" \
    "--exclude=/home/pcalnon/snap/steam/" \
    "--exclude=/home/pcalnon/StarfieldData/" \
    "--exclude=/home/pcalnon/VirtualMachines/" \
    "--exclude=/home/pcalnon/.config/Duplicati/" \
    "--exclude=/home/pcalnon/Development/python/Juniper/juniper-data/data/" \
    "--exclude=/home/pcalnon/.config/duplicati-backup/" \
    >> "${LOG_FILE}" 2>&1
RC=$?
set -e

if [[ ${RC} -eq 0 ]]; then
    log "backup completed OK"
    write_status OK ""
else
    log "backup FAILED rc=${RC}"
    write_status FAILED "duplicati-cli rc=${RC}"
fi

exit "${RC}"
