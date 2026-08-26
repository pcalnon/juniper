#!/usr/bin/env python3
"""Repoint the live Yamaguchi job (id 2) at a new destination with the passphrase-safe GET/modify/PUT.

Migration step 3 (certification note §8.6-8).  This is the single most dangerous
edit in the arc: a ``TargetURL`` pointed at an incomplete or absent destination
presents to Duplicati as *every remote volume missing* against a populated local
job DB.  Every guard below exists for that one failure.

The passphrase rule (note §8.6-4) applies unchanged.
    ``GET /api/v1/backup/<id>`` returns the ``passphrase`` setting as a 15-character
    MASK.  A PUT carrying the mask is refused or mangled by the server, so the
    real value is read from ``~/.config/duplicati-backup/env`` and substituted in
    place.  The value is never printed; only its PBKDF2 fingerprint prefix is,
    and a mismatch refuses the PUT.

Guards specific to a destination change, all fatal:

* Refuses (rc 3) while a task is active or queued.
* Refuses (rc 4) unless the new path exists, is a directory, and sits on a
  **mounted** filesystem.
* Refuses (rc 4) unless the new destination holds **at least as many
  ``duplicati-*`` volumes as the current one, and the same byte total** -- the
  copy must be complete and verified before the job is allowed to follow it.
* Refuses (rc 4) if the new target equals the current one.
* Refuses (rc 7) unless the new filesystem has an ``/etc/fstab`` entry, because
  boot-durability is the reason this migration exists (§8.10.2).  Override with
  ``--allow-non-durable`` only deliberately.
* Refuses (rc 5) on any passphrase-identity failure.
* After the PUT, re-GETs and requires TargetURL to be the new value while
  sources, filters, settings count, encryption module, passphrase masking and
  the schedule are all unchanged (rc 6 on any mismatch).

Exit: 0 verified, 1 PUT rejected, 3 busy, 4 destination guard, 5 passphrase
guard, 6 post-PUT verification, 7 non-durable target.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess  # nosec B404
import sys
from urllib.parse import unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

ENV_FILE = os.path.expanduser("~/.config/duplicati-backup/env")
MASK = "*" * 15
FINGERPRINT_SALT = b"juniper-yamaguchi-passphrase-fingerprint-v1"  # public and fixed: an identity check, not storage
FINGERPRINT_ROUNDS = 200_000
EXPECTED_FINGERPRINT_PREFIX = "1ff8be456de2752f"  # PASSPHRASE (Yamaguchi); recorded in note §8.9-3


def fingerprint(value):
    """16-hex identity prefix of a secret: PBKDF2-HMAC-SHA256, fixed public salt, expensive on purpose."""
    return hashlib.pbkdf2_hmac("sha256", value.encode(), FINGERPRINT_SALT, FINGERPRINT_ROUNDS).hex()[:16]


def refuse(code, msg):
    """Print the refusal and exit with the documented code (``sys.exit(str)`` would always be 1)."""
    print(msg, file=sys.stderr)
    sys.exit(code)


def read_passphrase(key):
    with open(ENV_FILE) as fh:
        for line in fh:
            m = re.match(rf"^\s*(?:export\s+)?{re.escape(key)}=(.*)$", line)
            if m and m.group(1).strip():
                return m.group(1).strip().strip("'\"")
    sys.exit(f"FATAL: no {key}= in {ENV_FILE}")


def settings_summary(settings):
    return ", ".join(f"{s.get('Name')}={'<redacted>' if 'passphrase' in (s.get('Name') or '').lower() else s.get('Value')}" for s in settings)


def setting_value(settings, name):
    vals = [s.get("Value") for s in settings if s.get("Name") == name]
    return vals[0] if len(vals) == 1 else None


def get_job(tok, backup_id):
    st, body = api.req("GET", f"/api/v1/backup/{backup_id}", tok)
    if st != 200 or "Backup" not in body:
        sys.exit(f"FATAL: GET backup {backup_id} -> {st}: {json.dumps(body)[:300]}")
    return body


def get_state(tok):
    st, state = api.req("GET", "/api/v1/serverstate", tok)
    if st != 200:
        sys.exit(f"FATAL: serverstate -> {st}: {json.dumps(state)[:300]}")
    return state


def local_path(target_url):
    """Local filesystem path behind a ``file://`` TargetURL, or None for a remote backend."""
    if not target_url or not target_url.startswith("file://"):
        return None
    return unquote(urlparse(target_url).path) or None


def census(path):
    """(volume count, byte total) of the ``duplicati-*`` files directly under *path*."""
    count = 0
    total = 0
    with os.scandir(path) as it:
        for e in it:
            if e.is_file() and e.name.startswith("duplicati-"):
                count += 1
                total += e.stat().st_size
    return count, total


def run(argv):
    # Fixed argv, no shell, read-only mount queries.
    return subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603


def is_mounted(path):
    return run(["mountpoint", "-q", path]).returncode == 0


def mount_point_of(path):
    r = run(["findmnt", "-no", "TARGET", "--target", path])
    return r.stdout.strip() if r.returncode == 0 else None


def in_fstab(mount_target):
    """True when the mountpoint has an /etc/fstab entry -- i.e. it comes back at boot (§8.10.2)."""
    return run(["findmnt", "-no", "SOURCE", "--fstab", "--target", mount_target]).returncode == 0


def main():
    ap = argparse.ArgumentParser(description="repoint a Duplicati server job at a new destination, passphrase-safely")
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--new-target", required=True, metavar="PATH", help="new destination directory (a local path; converted to file://)")
    ap.add_argument("--passphrase-key", default="PASSPHRASE", help="key in ~/.config/duplicati-backup/env (PASSPHRASE = Yamaguchi; PASSPHRASE_OLD = old archive)")
    ap.add_argument("--expect-fingerprint-prefix", default=EXPECTED_FINGERPRINT_PREFIX, help="the real passphrase's PBKDF2 fingerprint must start with this (note §8.9-3); refuses otherwise")
    ap.add_argument("--allow-non-durable", action="store_true", help="permit a target whose filesystem has no /etc/fstab entry (refused by default -- boot durability is the point of the migration)")
    ap.add_argument("--allow-shrink", action="store_true", help="permit a target holding FEWER volumes than the current one (refused by default)")
    ap.add_argument("--dry-run", action="store_true", help="do everything except the PUT")
    args = ap.parse_args()

    new_path = os.path.abspath(args.new_target)
    tok = api.login()

    state = get_state(tok)
    if state.get("ActiveTask") or state.get("SchedulerQueueIds"):
        refuse(3, f"REFUSE (rc 3): a task is active or queued -- ActiveTask={state.get('ActiveTask')} SchedulerQueueIds={state.get('SchedulerQueueIds')}")
    proposed_before = state.get("ProposedSchedule")

    body = get_job(tok, args.backup_id)
    b = body["Backup"]
    sched = body.get("Schedule") or {}
    old_url = b.get("TargetURL")
    sources_before = list(b.get("Sources") or [])
    filters_before = len(b.get("Filters") or [])
    settings = b.get("Settings") or []
    settings_before = len(settings)

    print(f"before      : id={b.get('ID')} name={b.get('Name')!r}")
    print(f"  target    : {old_url}")
    print(f"  sources   : {json.dumps(sources_before)}")
    print(f"  filters   : {filters_before}")
    print(f"  settings  : {settings_summary(settings)}")
    print(f"  schedule  : Time={sched.get('Time')} Repeat={sched.get('Repeat')} LastRun={sched.get('LastRun')}")

    new_url = "file://" + new_path
    if new_url == old_url:
        refuse(4, f"REFUSE (rc 4): new target equals the current one ({old_url})")

    # --- destination guards -------------------------------------------------
    if not os.path.isdir(new_path):
        refuse(4, f"REFUSE (rc 4): new target is not an existing directory: {new_path}")
    new_mp = mount_point_of(new_path)
    if not new_mp or not is_mounted(new_mp):
        refuse(4, f"REFUSE (rc 4): new target is not on a mounted filesystem: {new_path}")
    print(f"guard       : new target on mounted filesystem {new_mp}")

    if not in_fstab(new_mp):
        msg = (
            f"REFUSE (rc 7): {new_mp} has no /etc/fstab entry -- it will not come back at boot.\n"
            "              Migrating to a non-durable mount reproduces the very defect this\n"
            "              migration exists to fix (note §8.10.2).  Pass --allow-non-durable\n"
            "              only if that is deliberate."
        )
        if args.allow_non_durable:
            print("WARNING     : " + msg.replace("REFUSE (rc 7): ", ""), file=sys.stderr)
        else:
            refuse(7, msg)
    else:
        print(f"guard       : {new_mp} is fstab-managed -- boot-durable")

    old_path = local_path(old_url)
    new_count, new_bytes = census(new_path)
    if old_path and os.path.isdir(old_path):
        old_count, old_bytes = census(old_path)
        print(f"census      : current {old_count} volumes / {old_bytes} B   ->   new {new_count} volumes / {new_bytes} B")
        if new_count < old_count and not args.allow_shrink:
            refuse(4, f"REFUSE (rc 4): new target holds FEWER volumes ({new_count}) than the current one ({old_count}) -- the copy is incomplete")
        if new_bytes != old_bytes and not args.allow_shrink:
            refuse(4, f"REFUSE (rc 4): byte totals differ (current {old_bytes}, new {new_bytes}) -- the copy is not identical")
        print("guard       : destination census matches -- the copy is complete")
    else:
        print(f"census      : new {new_count} volumes / {new_bytes} B (current target not a readable local path -- no comparison)")
        if new_count == 0:
            refuse(4, "REFUSE (rc 4): new target holds no duplicati-* volumes and the current one could not be compared")

    # --- passphrase guard ---------------------------------------------------
    if [s.get("Name") for s in settings].count("passphrase") != 1:
        refuse(5, "REFUSE (rc 5): expected exactly one passphrase setting")
    real = read_passphrase(args.passphrase_key)
    if not real or real == MASK:
        refuse(5, "REFUSE (rc 5): the credentials file yielded an empty value or the mask itself")
    fp = fingerprint(real)
    if not fp.startswith(args.expect_fingerprint_prefix):
        refuse(5, f"REFUSE (rc 5): passphrase fingerprint {fp} does not start with {args.expect_fingerprint_prefix} -- wrong key selected?")
    for s in settings:
        if s.get("Name") == "passphrase":
            if s.get("Value") != MASK:
                print(f"  note      : server returned a {len(s.get('Value') or '')}-char passphrase value, not the 15-char mask; replacing anyway")
            s["Value"] = real

    b["TargetURL"] = new_url
    print(f"plan        : TargetURL {old_url} -> {new_url}; passphrase fingerprint {fp} OK")
    if args.dry_run:
        print("DRY RUN     : no PUT sent")
        return

    st, resp = api.req("PUT", f"/api/v1/backup/{args.backup_id}", tok, body={"Backup": b, "Schedule": sched})
    print(f"PUT         : {st} {json.dumps(resp)[:200]}")
    if st != 200:
        sys.exit(1)

    after = get_job(tok, args.backup_id)
    ba = after["Backup"]
    sa = after.get("Schedule") or {}
    settings_after = ba.get("Settings") or []
    state_after = get_state(tok)
    checks = [
        ("TargetURL == new", ba.get("TargetURL") == new_url, str(ba.get("TargetURL"))),
        ("sources unchanged", list(ba.get("Sources") or []) == sources_before, json.dumps(ba.get("Sources"))),
        ("filters unchanged", len(ba.get("Filters") or []) == filters_before, str(len(ba.get("Filters") or []))),
        ("settings count unchanged", len(settings_after) == settings_before, str(len(settings_after))),
        ("encryption-module == aes", setting_value(settings_after, "encryption-module") == "aes", str(setting_value(settings_after, "encryption-module"))),
        ("passphrase reads back masked", setting_value(settings_after, "passphrase") == MASK, f"{len(setting_value(settings_after, 'passphrase') or '')} chars"),
        ("schedule Time/Repeat unchanged", (sa.get("Time"), sa.get("Repeat")) == (sched.get("Time"), sched.get("Repeat")), f"Time={sa.get('Time')} Repeat={sa.get('Repeat')}"),
        ("ProposedSchedule unchanged", state_after.get("ProposedSchedule") == proposed_before, json.dumps(state_after.get("ProposedSchedule"))),
    ]
    ok = True
    for label, passed, detail in checks:
        ok = ok and passed
        print(f"  {'PASS' if passed else 'FAIL'}      : {label} -> {detail}")
    print(f"after       : settings {settings_summary(settings_after)}")
    if not ok:
        sys.exit(6)
    print("VERIFIED    : job repointed.  Keep the OLD destination until a run and a drill pass at the new one.")


if __name__ == "__main__":
    main()
