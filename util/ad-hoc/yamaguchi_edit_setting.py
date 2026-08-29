#!/usr/bin/env python3
"""Change ONE setting on the live Yamaguchi job (id 2) with the passphrase-safe GET/modify/PUT.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Companion to ``yamaguchi_edit_target.py`` (destination) and
``yamaguchi_edit_sources.py`` (source list), for the third editable surface: the
``Settings`` list.  Written 2026-08-28 to move ``--tempdir`` off the non-durable
sdc4 mount (note 8.14); kept general because the next setting change should not
need a fourth bespoke script.

The passphrase rule (note 8.6-4) applies unchanged.
    ``GET /api/v1/backup/<id>`` returns the ``passphrase`` setting as a 15-character
    MASK.  A PUT carrying the mask is refused or mangled by the server, so the real
    value is read from ``~/.config/duplicati-backup/env`` and substituted in place.
    The value is never printed; only its PBKDF2 fingerprint prefix is, and a
    mismatch refuses the PUT.

Guards, all fatal:

* Refuses (rc 3) while a task is active or queued -- a settings PUT mid-run is
  the one edit most likely to be read half-applied.
* Refuses (rc 4) unless the named setting exists **exactly once** already.  This
  script changes settings; it does not invent them, because a typo'd new name is
  silently accepted by the server and then silently ignored by the engine.
* Refuses (rc 4) if the new value equals the current one.
* With ``--path-value`` (the ``--tempdir`` case), refuses (rc 4) unless the value
  is a directory on a **mounted**, **non-volatile**, **fstab-managed** filesystem
  that is either outside every backup Source or covered by an exclude filter.
  Each clause is a real failure:
    - tmpfs: Duplicati's own default tempdir is ``/tmp``, which on this host is
      tmpfs -- the "run-1 trap" that put ``--tempdir`` in the job in the first
      place.  Re-introducing it by pointing the setting at another tmpfs would be
      the same defect wearing a different path.
    - not fstab-managed: the mount does not come back at boot, which is exactly
      the defect the 2026-08-26 destination migration existed to fix (note 8.10.2).
    - inside an unfiltered Source: Duplicati would scan the temp volumes it is in
      the middle of writing.
* Refuses (rc 5) on any passphrase-identity failure.
* After the PUT, re-GETs and requires the named setting to hold the new value
  while TargetURL, sources, filters, settings count, encryption module,
  passphrase masking and the schedule are all unchanged (rc 6 on any mismatch).

Exit: 0 verified, 1 PUT rejected, 3 busy, 4 value guard, 5 passphrase guard,
6 post-PUT verification.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess  # nosec B404
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

ENV_FILE = os.path.expanduser("~/.config/duplicati-backup/env")
MASK = "*" * 15
FINGERPRINT_SALT = b"juniper-yamaguchi-passphrase-fingerprint-v1"  # public and fixed: an identity check, not storage
FINGERPRINT_ROUNDS = 200_000
EXPECTED_FINGERPRINT_PREFIX = "1ff8be456de2752f"  # PASSPHRASE (Yamaguchi); recorded in note 8.9-3

# os.path.ismount() is true for all of these, so "is a mountpoint" is not "is storage".
VOLATILE_FSTYPES = {"tmpfs", "ramfs", "devtmpfs", "squashfs", "overlay"}


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
    return ", ".join(
        f"{s.get('Name')}={'<redacted>' if 'passphrase' in (s.get('Name') or '').lower() else s.get('Value')}"
        for s in settings
    )


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


def run(argv):
    # Fixed argv, no shell, read-only mount queries.
    return subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603


def mount_point_of(path):
    r = run(["findmnt", "-no", "TARGET", "--target", path])
    return r.stdout.strip() if r.returncode == 0 else None


def fstype_of(path):
    r = run(["findmnt", "-no", "FSTYPE", "--target", path])
    return r.stdout.strip() if r.returncode == 0 else None


def in_fstab(mount_target):
    """True when the mountpoint has an /etc/fstab entry -- i.e. it comes back at boot (note 8.10.2)."""
    return run(["findmnt", "-no", "SOURCE", "--fstab", "--target", mount_target]).returncode == 0


def as_dir(p):
    """Normalised directory prefix, always with a trailing separator, for prefix comparisons."""
    return os.path.realpath(p).rstrip(os.sep) + os.sep


def check_path_value(value, sources, filters):
    """Fatal guards for a setting whose value is a local directory (the --tempdir case)."""
    path = os.path.realpath(value)
    if not os.path.isdir(path):
        refuse(4, f"REFUSE (rc 4): value is not an existing directory: {path}")
    mp = mount_point_of(path)
    if not mp:
        refuse(4, f"REFUSE (rc 4): could not determine the mountpoint of {path}")
    fst = fstype_of(path)
    if fst in VOLATILE_FSTYPES:
        refuse(4, f"REFUSE (rc 4): {path} is on {mp} ({fst}), which is not durable storage. "
                  "Duplicati's built-in default tempdir is /tmp -- tmpfs on this host -- and "
                  "avoiding exactly that is why this setting exists.")
    if not in_fstab(mp):
        refuse(4, f"REFUSE (rc 4): {mp} has no /etc/fstab entry -- it does not come back at boot, "
                  "which is the defect the destination migration existed to fix (note 8.10.2).")
    print(f"guard       : {path} on {mp} ({fst}), fstab-managed")

    # A tempdir inside a backup source makes the job scan the volumes it is writing, unless an
    # exclude filter covers it.
    excludes = [f.get("Expression") for f in filters if f.get("Include") is False and f.get("Expression")]
    target = as_dir(path)
    for src in sources:
        if not src.startswith("/"):
            continue
        src_dir = as_dir(src)
        if not target.startswith(src_dir):
            continue
        covering = [e for e in excludes if e.startswith("/") and target.startswith(as_dir(e))]
        if not covering:
            refuse(4, f"REFUSE (rc 4): {path} is inside backup source {src} and no exclude filter "
                      "covers it -- the job would scan the temp volumes it is writing. Add an "
                      "exclude filter first, or choose a path outside every source.")
        print(f"guard       : inside source {src}, but excluded by {covering[0]}")
    return path


def main():
    ap = argparse.ArgumentParser(description="change one setting on a Duplicati server job, passphrase-safely")
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--name", required=True, help="setting name exactly as the server stores it, e.g. --tempdir")
    ap.add_argument("--value", required=True, help="the new value")
    ap.add_argument("--path-value", action="store_true",
                    help="treat the value as a local directory and apply the durability / source guards")
    ap.add_argument("--passphrase-key", default="PASSPHRASE")
    ap.add_argument("--expect-fingerprint-prefix", default=EXPECTED_FINGERPRINT_PREFIX,
                    help="the real passphrase's PBKDF2 fingerprint must start with this (note 8.9-3)")
    ap.add_argument("--dry-run", action="store_true", help="do everything except the PUT")
    args = ap.parse_args()

    tok = api.login()

    state = get_state(tok)
    if state.get("ActiveTask") or state.get("SchedulerQueueIds"):
        refuse(3, f"REFUSE (rc 3): a task is active or queued -- ActiveTask={state.get('ActiveTask')} "
                  f"SchedulerQueueIds={state.get('SchedulerQueueIds')}")
    proposed_before = state.get("ProposedSchedule")

    body = get_job(tok, args.backup_id)
    b = body["Backup"]
    sched = body.get("Schedule") or {}
    settings = b.get("Settings") or []
    sources_before = list(b.get("Sources") or [])
    filters_before = b.get("Filters") or []
    target_before = b.get("TargetURL")

    print(f"before      : id={b.get('ID')} name={b.get('Name')!r}")
    print(f"  target    : {target_before}")
    print(f"  sources   : {json.dumps(sources_before)}")
    print(f"  filters   : {len(filters_before)}")
    print(f"  settings  : {settings_summary(settings)}")

    matches = [s for s in settings if s.get("Name") == args.name]
    if len(matches) != 1:
        refuse(4, f"REFUSE (rc 4): expected exactly one {args.name!r} setting, found {len(matches)}. "
                  "This tool changes existing settings; it does not create them, because the server "
                  "accepts an unknown name silently and the engine then ignores it.")
    old_value = matches[0].get("Value")
    if old_value == args.value:
        refuse(4, f"REFUSE (rc 4): {args.name} is already {args.value!r}")

    new_value = args.value
    if args.path_value:
        new_value = check_path_value(args.value, sources_before, filters_before)

    # --- passphrase guard ---------------------------------------------------
    if [s.get("Name") for s in settings].count("passphrase") != 1:
        refuse(5, "REFUSE (rc 5): expected exactly one passphrase setting")
    real = read_passphrase(args.passphrase_key)
    if not real or real == MASK:
        refuse(5, "REFUSE (rc 5): the credentials file yielded an empty value or the mask itself")
    fp = fingerprint(real)
    if not fp.startswith(args.expect_fingerprint_prefix):
        refuse(5, f"REFUSE (rc 5): passphrase fingerprint {fp} does not start with "
                  f"{args.expect_fingerprint_prefix} -- wrong key selected?")
    for s in settings:
        if s.get("Name") == "passphrase":
            if s.get("Value") != MASK:
                print(f"  note      : server returned a {len(s.get('Value') or '')}-char passphrase value, "
                      "not the 15-char mask; replacing anyway")
            s["Value"] = real

    matches[0]["Value"] = new_value
    print(f"plan        : {args.name} {old_value!r} -> {new_value!r}; passphrase fingerprint {fp} OK")
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
        (f"{args.name} == new", setting_value(settings_after, args.name) == new_value,
         str(setting_value(settings_after, args.name))),
        ("TargetURL unchanged", ba.get("TargetURL") == target_before, str(ba.get("TargetURL"))),
        ("sources unchanged", list(ba.get("Sources") or []) == sources_before, json.dumps(ba.get("Sources"))),
        ("filters unchanged", len(ba.get("Filters") or []) == len(filters_before), str(len(ba.get("Filters") or []))),
        ("settings count unchanged", len(settings_after) == len(settings), str(len(settings_after))),
        ("encryption-module == aes", setting_value(settings_after, "encryption-module") == "aes",
         str(setting_value(settings_after, "encryption-module"))),
        ("passphrase reads back masked", setting_value(settings_after, "passphrase") == MASK,
         f"{len(setting_value(settings_after, 'passphrase') or '')} chars"),
        ("schedule Time/Repeat unchanged", (sa.get("Time"), sa.get("Repeat")) == (sched.get("Time"), sched.get("Repeat")),
         f"Time={sa.get('Time')} Repeat={sa.get('Repeat')}"),
        ("ProposedSchedule unchanged", state_after.get("ProposedSchedule") == proposed_before,
         json.dumps(state_after.get("ProposedSchedule"))),
    ]
    ok = True
    for label, passed, detail in checks:
        ok = ok and passed
        print(f"  {'PASS' if passed else 'FAIL'}      : {label} -> {detail}")
    print(f"after       : settings {settings_summary(settings_after)}")
    if not ok:
        sys.exit(6)
    print(f"VERIFIED    : {args.name} is now {new_value!r}.")


if __name__ == "__main__":
    main()
