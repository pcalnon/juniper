#!/usr/bin/env python3
"""
Remove explicit Sources entries from the live Yamaguchi job (id 2) with the passphrase-safe GET/modify/PUT.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc — one-off (Paul's 2026-08-26 decision: exclude the running win11 VM's VDI, note §8.6-2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (§8.6-2, §8.6-4 PUT rule);
         util/ad-hoc/yamaguchi_switch_aes.py (the reference GET/modify/PUT pattern)

THE PUT RULE (note §8.6-4)
    ``GET /api/v1/backup/<id>`` returns the ``passphrase`` setting as a 15-character
    mask (``***************``). A PUT that carries the mask is refused or mangled by
    the server, so the real value is re-read from ``~/.config/duplicati-backup/env``
    (key ``PASSPHRASE`` -- the Yamaguchi key; ``PASSPHRASE_OLD`` is the old archive's)
    and put back in place before the PUT -- exactly what ``yamaguchi_switch_aes.py``
    does. Two guards make PUTting a wrong key structurally hard: the value must not be
    the mask, and its FINGERPRINT must start with the recorded prefix; a mismatch
    refuses the PUT. The fingerprint is PBKDF2-HMAC-SHA256 over the value with a fixed
    public salt (``FINGERPRINT_SALT``) and 200,000 rounds -- deliberately expensive, so
    the 16-hex prefix recorded in the notes/handoffs is not an offline oracle at
    plain-hash speed (the first revision used bare sha256; CodeQL
    py/weak-sensitive-data-hashing, alert 586 on ml#1394). The real value is never
    printed and the job body is never dumped once it carries it. Recorded prefixes:
    certification note §8.9-3.

SAFETY
    Refuses (rc 3) while a task is active or queued -- editing a job mid-run is the
    §5 class. Refuses (rc 4) if an entry to remove is not present verbatim, or if
    nothing would remain. Verifies after the PUT by re-reading the job: sources are
    exactly the planned list, filter and setting counts unchanged, encryption-module
    still ``aes``, the passphrase reads back masked, and the server's
    ProposedSchedule did not move (rc 6 on any mismatch).

    python3 util/ad-hoc/yamaguchi_edit_sources.py --remove <exact Sources entry> --dry-run
    python3 util/ad-hoc/yamaguchi_edit_sources.py --remove <exact Sources entry>
"""

import argparse
import hashlib
import json
import os
import re
import sys

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


def main():
    ap = argparse.ArgumentParser(description="remove explicit Sources entries from a Duplicati server job, passphrase-safely")
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--remove", action="append", required=True, metavar="PATH", help="exact Sources entry to remove (repeatable)")
    ap.add_argument("--passphrase-key", default="PASSPHRASE", help="key in ~/.config/duplicati-backup/env (PASSPHRASE = Yamaguchi; PASSPHRASE_OLD = old archive)")
    ap.add_argument("--expect-fingerprint-prefix", default=EXPECTED_FINGERPRINT_PREFIX, help="the real passphrase's PBKDF2 fingerprint must start with this (recorded in note §8.9-3); refuses otherwise")
    ap.add_argument("--dry-run", action="store_true", help="do everything except the PUT")
    args = ap.parse_args()

    tok = api.login()

    state = get_state(tok)
    if state.get("ActiveTask") or state.get("SchedulerQueueIds"):
        refuse(3, f"REFUSE (rc 3): a task is active or queued -- ActiveTask={state.get('ActiveTask')} SchedulerQueueIds={state.get('SchedulerQueueIds')}")
    proposed_before = state.get("ProposedSchedule")

    body = get_job(tok, args.backup_id)
    b = body["Backup"]
    sched = body.get("Schedule") or {}
    sources = list(b.get("Sources") or [])
    filters_before = len(b.get("Filters") or [])
    settings = b.get("Settings") or []
    settings_before = len(settings)
    print(f"before      : id={b.get('ID')} name={b.get('Name')!r} target={b.get('TargetURL')}")
    print(f"  sources   : {json.dumps(sources)}")
    print(f"  filters   : {filters_before}")
    print(f"  settings  : {settings_summary(settings)}")
    print(f"  schedule  : Time={sched.get('Time')} Repeat={sched.get('Repeat')} LastRun={sched.get('LastRun')}")
    print(f"  proposed  : {json.dumps(proposed_before)}")

    missing = [r for r in args.remove if r not in sources]
    if missing:
        refuse(4, f"REFUSE (rc 4): not present verbatim in Sources: {json.dumps(missing)}")
    new_sources = [s for s in sources if s not in args.remove]
    if not new_sources:
        refuse(4, "REFUSE (rc 4): removal would leave the job with no sources")

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
    b["Sources"] = new_sources
    print(f"plan        : sources {len(sources)} -> {len(new_sources)}; removing {json.dumps(args.remove)}; passphrase fingerprint {fp} OK")
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
        ("sources == plan", list(ba.get("Sources") or []) == new_sources, json.dumps(ba.get("Sources"))),
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
    print("VERIFIED    : job updated; watch the next run's ParsedResult")


if __name__ == "__main__":
    main()
