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

# Volume staging. A sibling of the destination, NOT a child of it -- a child
# would sit inside the directory Duplicati enumerates as the backend.
# Same filesystem as the destination on purpose: the finished volume then moves
# by rename instead of a 500 MB copy.
TEMP_DIR="${DUPLICATI_TEMP_DIR:-/media/pcalnon/temp_backups/_duplicati_tmp}"

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

# --- Guard 1: the secret must be present and plausible -----------------------
# The length floor mirrors util/ad-hoc/duplicati_first_backup.bash. It cannot
# detect a WRONG passphrase -- nothing here can, because Duplicati will happily
# encrypt a fresh set under any value -- but it does catch a truncated or
# partially-substituted credential file, which is the realistic edit accident.
[[ -n "${PASSPHRASE:-}" ]] || fail "PASSPHRASE is unset or empty; refusing to run"
[[ "${#PASSPHRASE}" -ge 12 ]] \
    || fail "PASSPHRASE is ${#PASSPHRASE} chars, under the 12-char floor; refusing to run"

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

# --- Guard 3b: volume staging must NOT be on tmpfs ---------------------------
# Observed 2026-08-23: with --tempdir unset, Duplicati staged its 500 MB volumes
# in /tmp, which is tmpfs -- 8.4 GB of RAM held in in-flight volumes while swap
# sat at 17 GB of 20 GB. Staging in RAM also loses all in-flight state on reboot.
mkdir -p "${TEMP_DIR}" || fail "cannot create ${TEMP_DIR}"
[[ -w "${TEMP_DIR}" ]] || fail "${TEMP_DIR} is not writable"
TEMP_FSTYPE="$(stat -f -c '%T' "${TEMP_DIR}" 2>/dev/null || echo unknown)"
if [[ "${TEMP_FSTYPE}" == "tmpfs" || "${TEMP_FSTYPE}" == "ramfs" ]]; then
    fail "${TEMP_DIR} is ${TEMP_FSTYPE} (RAM-backed); refusing to stage 500 MB volumes in memory"
fi

# --- skip helper -------------------------------------------------------------
# A skip is NOT silently successful. Two things make it safe:
#   1. It stamps last-run.status with a CURRENT timestamp, so the file cannot
#      freeze at an old result and read as "still fine".
#   2. If no run has actually SUCCEEDED within STALE_DAYS, the skip escalates to
#      a hard failure so OnFailure= fires. Without this, a persistently hung
#      duplicati (which happened on 2026-08-23 and whose root cause is still
#      open) would make every nightly run skip, systemd would report success,
#      and the backup would silently stop -- the exact failure this whole lane
#      exists to prevent.
STALE_DAYS="${DUPLICATI_STALE_DAYS:-3}"

skip_or_fail() {
    local reason="$1"
    local last_ok=0
    if [[ -r "${STATUS_FILE}" ]] && grep -q '^result=OK' "${STATUS_FILE}"; then
        last_ok="$(stat -c '%Y' "${STATUS_FILE}" 2>/dev/null || echo 0)"
    fi
    local age_days=$(( ( $(date +%s) - last_ok ) / 86400 ))
    if [[ "${age_days}" -gt "${STALE_DAYS}" ]]; then
        fail "${reason}; and no successful run in ${age_days} days (limit ${STALE_DAYS}) -- escalating"
    fi
    log "${reason}; skipping this run"
    write_status SKIPPED "${reason}"
    exit 0
}

# --- Guard 4: exactly one runner ---------------------------------------------
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    skip_or_fail "another run holds ${LOCK_FILE}"
fi

# --- Guard 5: nothing else is already writing this local database -------------
# flock only serialises runs started THROUGH this script. Anything else that
# opens the same local DB corrupts it, and there are at least three ways in:
#   * a hand-started `duplicati-cli backup` (how the 2026-08-23 set was seeded)
#   * the same, invoked by absolute path -- a name-anchored regex MISSES this
#   * duplicati-server running the job in-process from the web UI, which never
#     spawns a `duplicati-cli` child at all and so cannot be found by name
# So the check is on the DATABASE, not the process name: if any live process
# holds the dbpath open, stand down. That covers all three, including ones not
# yet imagined.
# `pgrep -f` must NOT be used for process-name checks here -- it self-matches.
#
# ONE `find` over the fd directories, not a `readlink` fork per fd on the host.
# The per-fd loop this replaces cost 59.17 s against 10,211 open fds (measured
# 2026-08-29 on Yamaguchi); this costs 0.41 s and returns the same pids. That
# time was spent on EVERY run, before any backup work started -- it is pure
# preflight overhead, and it grows with the whole machine's fd count rather than
# with anything about the backup.
#
# `%l` is the raw link target. The kernel already stores /proc/<pid>/fd/<n>
# fully resolved, so DBPATH must be resolved too: the old code compared a
# resolved fd target against DBPATH *verbatim*, which silently matched nothing
# whenever DBPATH reached the database through a symlinked directory -- a live
# holder went undetected and the corruption guard passed. Verified 2026-08-29:
# with DBPATH configured via a symlinked parent the old comparison MISSES and
# this one MATCHES.
db_holder_pids() {
    local resolved fd_path fd_target pid
    resolved="$(readlink -f "${DBPATH}" 2>/dev/null || printf '%s' "${DBPATH}")"
    while IFS=' ' read -r fd_path fd_target; do
        [[ "${fd_target}" == "${resolved}" ]] || continue
        pid="${fd_path#/proc/}"; pid="${pid%%/*}"
        [[ "${pid}" == "$$" ]] && continue
        printf '%s\n' "${pid}"
    done < <(find /proc/[0-9]*/fd -mindepth 1 -maxdepth 1 -type l -printf '%p %l\n' 2>/dev/null) | sort -u
}

HOLDERS="$(db_holder_pids || true)"
if [[ -n "${HOLDERS}" ]]; then
    skip_or_fail "another process already has ${DBPATH} open (pids: ${HOLDERS//$'\n'/ })"
fi

log "starting backup"
log "  source      ${SOURCE_PATH}"
log "  destination ${DEST_URL}"
log "  dbpath      ${DBPATH}"
log "  tempdir     ${TEMP_DIR} (${TEMP_FSTYPE})"

# GPGFlushError mitigations (2026-08-24; fixes 2 & 3 of
# notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md §9):
#
#   --gpg-encryption-switches=--compress-algo none
#     Duplicati spawns gpg without --no-options, so ~/.gnupg/gpg.conf's
#     "compress-algo ZLIB" governs -- deflating already-zip-compressed volumes
#     at ~17 s of gpg CPU per 500 MB volume vs ~1.6 s without (measured).
#     Disabling it shrinks the tail work inside GPGStreamWrapper's hardcoded
#     5 s Join by ~10x. The command line overrides the conf file.
#
#   --asynchronous-upload-limit=1
#     Encryption pre-starts at QUEUE time (BackendManager.cs:316 at the
#     installed tag), so the default of 4 let >=6 gpg pipelines run
#     concurrently and one host-global stall on 2026-08-23 missed the 5 s
#     bound on ~6 volumes at once. A limit of 1 serializes uploads and
#     shrinks the blast radius to ~1 volume. Upload is nowhere near the local
#     bottleneck (~7 s/volume vs ~2 min to produce one), so the cost is
#     negligible.
#
# The 5 s Join itself remains (upstream defect, unchanged since 2019), and a
# miss is still unretryable by construction -- these two shrink the exposure,
# they do not remove it. Do not remove them without re-reading the note.
set +e
duplicati-cli backup "${DEST_URL}" "${SOURCE_PATH}" \
    --dbpath="${DBPATH}" \
    --tempdir="${TEMP_DIR}" \
    --encryption-module=gpg \
    "--gpg-encryption-switches=--compress-algo none" \
    --asynchronous-upload-limit=1 \
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
