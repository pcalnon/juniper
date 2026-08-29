#!/usr/bin/env bash
# Deploy the Duplicati server-DB snapshot timer (ROOT system lane).
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-29
# Status:     ad-hoc — owner decision 2026-08-29 (note §8.19): "automated root-owned copy"
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8.19);
#             util/systemd/yamaguchi-server-db-snapshot.{service,timer};
#             util/ad-hoc/yamaguchi_server_db_snapshot.py
#
# Run with sudo:  sudo bash util/ad-hoc/yamaguchi_server_db_deploy.bash
#
# Idempotent. Installs two ROOT units, reloads, enables the timer, and takes one snapshot now
# so the result is visible immediately rather than at the next 13:45Z elapse.
#
# THIS IS NOT THE DISABLED duplicati-backup.* USER LANE. That lane RUNS BACKUPS through the
# CLI, is 0-for-3, and is deliberately disabled with its paths pointing at deleted directories.
# Do not "repair" it. This unit only COPIES A FILE and never touches the destination.
set -euo pipefail

PRIMARY=/home/pcalnon/Development/python/Juniper/juniper-ml
UNIT_DIR=/etc/systemd/system
SNAPSHOT=util/ad-hoc/yamaguchi_server_db_snapshot.py

if [ "$(id -u)" -ne 0 ]; then
    echo "REFUSE: must run as root -- /usr/lib/duplicati/data is drwx------ root root" >&2
    exit 2
fi

# The unit's ExecStart names the PRIMARY checkout, matching yamaguchi-watchdog.service. If that
# checkout has not been synced to a main containing the script, every fire exits non-zero.
if [ ! -f "$PRIMARY/$SNAPSHOT" ]; then
    echo "REFUSE: $PRIMARY/$SNAPSHOT is missing -- sync the primary checkout to a main that" >&2
    echo "        contains it before deploying, or every timer fire exits non-zero." >&2
    exit 2
fi

install -m 0644 \
    "$PRIMARY/util/systemd/yamaguchi-server-db-snapshot.service" \
    "$PRIMARY/util/systemd/yamaguchi-server-db-snapshot.timer" \
    "$UNIT_DIR/"
systemctl daemon-reload
systemctl enable --now yamaguchi-server-db-snapshot.timer

echo "== taking one snapshot now"
systemctl start yamaguchi-server-db-snapshot.service

echo "== timer"
systemctl list-timers yamaguchi-server-db-snapshot.timer --no-pager
echo "== last run"
systemctl status yamaguchi-server-db-snapshot.service --no-pager -n 20 || true
echo "== snapshot on disk"
ls -la /home/pcalnon/.local/state/duplicati-server-db/ 2>&1 || true
