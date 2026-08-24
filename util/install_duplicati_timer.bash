#!/usr/bin/env bash
############################################################################################################################################################
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  Duplicati Scheduled-Backup Installer
# Author:       Paul Calnon
# Version:      1.0.0
# License:      MIT
############################################################################################################################################################
#
# Installs the `systemd --user` scheduled-backup lane:
#
#   ~/.local/bin/duplicati-scheduled-backup.bash     the runner
#   ~/.local/bin/duplicati-backup-failure.bash       the OnFailure reporter
#   ~/.config/systemd/user/duplicati-backup.service
#   ~/.config/systemd/user/duplicati-backup.timer
#   ~/.config/systemd/user/duplicati-backup-failure.service
#
# WHY THE SCRIPTS ARE COPIED RATHER THAN SYMLINKED
#   The canonical copies live in a git worktree. Worktrees are routinely created
#   and destroyed. A symlink into one turns an ordinary `git worktree remove`
#   into a silent breakage of the backup lane -- the same class of fragility that
#   left the only copy of a live passphrase inside a disposable worktree. Copies
#   are durable; re-run this script to update them.
#
# WHAT THIS SCRIPT DELIBERATELY DOES NOT DO
#   It does not `enable --now` the timer. Enabling while a first full backup is
#   still in flight risks a second run against the same local database. Enable it
#   only once the first backup has completed AND a restore drill against the new
#   set has passed:
#
#       systemctl --user enable --now duplicati-backup.timer
#
#   Verify afterwards with:
#       systemctl --user list-timers duplicati-backup.timer
############################################################################################################################################################

set -euo pipefail

REPO_UTIL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"
CRED_FILE="${HOME}/.config/duplicati-backup/env"

install -d -m 0755 "${BIN_DIR}"
install -d -m 0755 "${UNIT_DIR}"

echo "==> installing runner scripts into ${BIN_DIR}"
install -m 0755 "${REPO_UTIL}/duplicati_scheduled_backup.bash" \
    "${BIN_DIR}/duplicati-scheduled-backup.bash"
install -m 0755 "${REPO_UTIL}/duplicati_backup_failure.bash" \
    "${BIN_DIR}/duplicati-backup-failure.bash"

echo "==> installing units into ${UNIT_DIR}"
for unit in duplicati-backup.service duplicati-backup.timer duplicati-backup-failure.service; do
    install -m 0644 "${REPO_UTIL}/systemd/${unit}" "${UNIT_DIR}/${unit}"
    echo "    ${unit}"
done

echo "==> checking the credential file"
if [[ ! -r "${CRED_FILE}" ]]; then
    echo "!!  ${CRED_FILE} is missing." >&2
    echo "!!  The service will refuse to start without PASSPHRASE." >&2
    exit 1
fi
CRED_MODE="$(stat -c '%a' "${CRED_FILE}")"
if [[ "${CRED_MODE}" != "600" ]]; then
    echo "!!  ${CRED_FILE} is mode ${CRED_MODE}; expected 600." >&2
    exit 1
fi
grep -q '^PASSPHRASE=' "${CRED_FILE}" \
    || { echo "!!  ${CRED_FILE} has no PASSPHRASE= entry." >&2; exit 1; }
echo "    ok (mode 600, PASSPHRASE present)"

echo "==> checking linger"
if [[ "$(loginctl show-user "${USER}" --property=Linger --value 2>/dev/null)" != "yes" ]]; then
    echo "!!  Linger is NOT enabled. The user manager will exit at logout and the" >&2
    echo "!!  timer will not fire. Fix with: loginctl enable-linger ${USER}" >&2
    exit 1
fi
echo "    ok (Linger=yes)"

echo "==> systemctl --user daemon-reload"
systemctl --user daemon-reload

echo
echo "Installed. The timer is NOT enabled yet -- that is deliberate."
echo "Enable it only after the first full backup completes and a restore drill passes:"
echo
echo "    systemctl --user enable --now duplicati-backup.timer"
echo "    systemctl --user list-timers duplicati-backup.timer"
echo
