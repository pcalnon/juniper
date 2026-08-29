#!/usr/bin/env bash
# Deploy (or re-deploy) alerting candidate B: the Yamaguchi server-run backup watchdog on a user timer.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-08-26
# Status:     ad-hoc — one-off (Paul's 2026-08-26 pick: architecture B; re-runnable after a reboot or re-clone)
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8.6-4);
#             util/systemd/yamaguchi-watchdog.{service,timer}; util/ad-hoc/yamaguchi_watchdog.py
#
# Idempotent. Copies the two units from the PRIMARY checkout (the unit's ExecStart names that
# checkout's script, so it must be synced to main >= 19207308 first), reloads, enables the timer
# persistently (WantedBy=timers.target, Persistent=true), runs one check now, and prints the
# durable status line. B depends on Linger=yes for the user -- a lingerless session is the
# 42-day-outage mechanism -- so that is asserted first.
set -euo pipefail

PRIMARY=/home/pcalnon/Development/python/Juniper/juniper-ml
UNIT_DIR="$HOME/.config/systemd/user"
STATE_DIR="$HOME/.local/state/duplicati"

if [ ! -f "$PRIMARY/util/ad-hoc/yamaguchi_watchdog.py" ]; then
    echo "REFUSE: $PRIMARY lacks util/ad-hoc/yamaguchi_watchdog.py -- sync the primary checkout to main first" >&2
    exit 2
fi
linger=$(loginctl show-user "$USER" -p Linger --value)
if [ "$linger" != "yes" ]; then
    echo "REFUSE: Linger=$linger for $USER -- the timer would not fire without a login session (loginctl enable-linger)" >&2
    exit 2
fi

install -m 0644 "$PRIMARY/util/systemd/yamaguchi-watchdog.service" "$PRIMARY/util/systemd/yamaguchi-watchdog.timer" "$UNIT_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now yamaguchi-watchdog.timer
# One check now. A non-zero exit IS the alert (the durable record is already written);
# keep going so the status line below is still printed.
if ! systemctl --user start yamaguchi-watchdog.service; then
    echo "ALERT: the first check did not read OK -- see $STATE_DIR/server-failures.log" >&2
fi
echo "== timer"
systemctl --user list-timers yamaguchi-watchdog.timer --no-pager
echo "== enabled: $(systemctl --user is-enabled yamaguchi-watchdog.timer)"
echo "== status"
cat "$STATE_DIR/server-watchdog.status"
