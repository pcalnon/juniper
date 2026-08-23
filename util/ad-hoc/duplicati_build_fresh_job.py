#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Build (and optionally create) the fresh Duplicati backup job.

Every value here traces to a measurement recorded in
``notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md``
rather than to a rule of thumb -- that plan exists because the *previous* job's
50 MB cap was chosen by feel and silently dropped four irreplaceable VM images.

The job's 37 existing exclusions are carried forward verbatim from the live job
config and six new ones are appended; nothing is invented here.

``--create`` writes the job through the local web API. Without it the script only
prints the configuration and validates it, which is the default because standing
up a backup job is not something to do by accident.

Deliberately does NOT set a passphrase. The caller must supply one via
``--passphrase-file``; there is no default and no placeholder, because a job
created with a weak or throwaway passphrase can silently encrypt a real backup
under a secret nobody recorded.

Usage
-----
    python3 util/ad-hoc/duplicati_build_fresh_job.py                # dry, prints config
    python3 util/ad-hoc/duplicati_build_fresh_job.py --create \
        --passphrase-file /path/to/archive-passphrase
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from duplicati_api import call  # noqa: E402

HOME = os.path.expanduser("~")

# Six additions, each justified in the plan's section 5 by measured size and by
# whether the content is regenerable.
NEW_EXCLUSIONS = [
    "%HOME%/.local/share/Steam/",                        # ~750 GiB, re-downloadable
    "%HOME%/snap/steam/",                                # ditto
    "%HOME%/StarfieldData/",                             # ~118 GiB game data
    "%HOME%/VirtualMachines/",                           # ~290 GiB + 10 of the 12 ISOs
    "%HOME%/.config/Duplicati/",                         # the backup's own databases
    "%HOME%/Development/python/Juniper/juniper-data/data/",  # re-fetchable datasets
]

# Name -> (value, why). The "why" is printed so the config can be reviewed
# against the plan without cross-referencing.
SETTINGS = [
    ("encryption-module", "gpg", "unchanged from the existing job"),
    ("compression-module", "zip", "unchanged"),
    ("--blocksize", "1MB",
     "IRREVERSIBLE after the first backup. Pinned explicitly rather than relying "
     "on the default so the choice is auditable and cannot drift. The old job's "
     "100 KB produced 28.5M blocks, a 13 GB database and a 49-day Recreate."),
    ("dblock-size", "500MB",
     "was 1 GB. Corruption destroys a whole volume, which is the granularity at "
     "which 1,208 volumes were just lost. Inside the documented 500-2000 MiB "
     "local band, and changeable later unlike blocksize."),
    ("--skip-files-larger-than", "2GB",
     "was 50 MB. With the six path exclusions this drops only 8 files / 24 GiB, "
     "and it KEEPS ~30 GiB of non-reproducible experiment logs (cascor#532) that "
     "the 50 MB cap silently discarded."),
    ("--no-auto-compact", "true",
     "an interrupted compact destroyed the previous archive. Do not enable until "
     "a restore has been proven on this set."),
    ("--allow-missing-source", "true", "unchanged; avoids spurious failures"),
]
# retention-policy is deliberately ABSENT: retention is what marked the
# intermediate filesets expendable. Add only once restores are proven.


def read_passphrase(path: str, key: str | None = None) -> str:
    """Read a named secret. `key` is required when the file holds several.

    Matching the first KEY=VALUE line is fine for a single-secret file and
    dangerous for a multi-secret one: this project's .env now holds both a new
    archive passphrase and the web-UI password, and picking by position would
    silently encrypt a backup under whichever happened to be first.
    """
    with open(path) as fh:
        raw = fh.read()
    pat = (rf"^[ \t]*(?:export[ \t]+)?{re.escape(key)}=(.*)$" if key
           else r"^[ \t]*(?:export[ \t]+)?[A-Za-z_][A-Za-z0-9_]*=(.*)$")
    m = re.search(pat, raw, re.M)
    if m:
        val = m.group(1).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        return val
    return raw.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="Ubuntu-fresh")
    ap.add_argument("--dest-dir", default="/media/pcalnon/temp_backups/Ubuntu")
    ap.add_argument("--source-job", type=int, default=2,
                    help="existing job whose sources/filters are carried forward")
    ap.add_argument("--passphrase-file", default=None)
    ap.add_argument("--passphrase-key", default="PASSPHRASE",
                    help="which KEY= entry to read when the file holds several "
                         "(default PASSPHRASE). Named explicitly because picking "
                         "by position can encrypt a backup under the wrong secret.")
    ap.add_argument("--create", action="store_true",
                    help="actually create the job (default: print and validate only)")
    args = ap.parse_args()

    status, cfg = call(f"backup/{args.source_job}")
    if status != 200:
        print(f"cannot read source job {args.source_job}: {status} {cfg}")
        return 2
    old = cfg["Backup"]

    filters = [dict(f) for f in old["Filters"]]
    start = max((f["Order"] for f in filters), default=-1) + 1
    for i, expr in enumerate(NEW_EXCLUSIONS):
        if any(f["Expression"] == expr for f in filters):
            print(f"  (already present, skipping) {expr}")
            continue
        filters.append({"Order": start + i, "Include": False, "Expression": expr})

    print(f"name        : {args.name}")
    print(f"destination : file://{args.dest_dir}")
    print(f"sources     : {old['Sources']}")
    print(f"filters     : {len(old['Filters'])} carried forward + "
          f"{len(filters) - len(old['Filters'])} new = {len(filters)}")
    print()
    print("settings:")
    for name, value, why in SETTINGS:
        print(f"  {name:<28} = {value}")
        print(f"      {why}")
    print("  retention-policy             = (ABSENT by design)")
    print("      retention is what marked the intermediate filesets expendable.")
    print()

    # ---- validate the exclusions actually resolve --------------------------
    print("exclusion path check (a typo'd exclusion silently protects nothing):")
    missing = 0
    for f in filters:
        p = f["Expression"].replace("%HOME%", HOME).rstrip("/")
        if not os.path.exists(p):
            missing += 1
            print(f"  MISSING  {f['Expression']}")
    print(f"  {len(filters) - missing}/{len(filters)} exclusion paths exist "
          f"({missing} missing -- harmless, but they protect nothing)")
    print()

    if not args.create:
        print("DRY RUN -- pass --create to actually create this job.")
        return 0

    if not args.passphrase_file:
        print("REFUSING: --create requires --passphrase-file. No default and no "
              "placeholder: a job created under a throwaway secret can encrypt a "
              "real backup that nobody can decrypt.")
        return 2
    passphrase = read_passphrase(args.passphrase_file, args.passphrase_key)
    if not passphrase:
        print(f"REFUSING: no {args.passphrase_key}= entry found in "
              f"{args.passphrase_file}")
        return 2
    if len(passphrase) < 12:
        print(f"REFUSING: passphrase from {args.passphrase_file} "
              f"({args.passphrase_key}) is too short: see duplicati_secret_check.py")
        return 2
    print(f"credential : {args.passphrase_file} key={args.passphrase_key}")

    settings = [{"Filter": "", "Name": n, "Value": v, "Argument": None}
                for n, v, _ in SETTINGS]
    settings.append({"Filter": "", "Name": "passphrase",
                     "Value": passphrase, "Argument": None})

    payload = {
        "Backup": {
            "Name": args.name,
            "Description": ("Fresh set after the 2026-07-13 data loss. Temporary "
                            "destination; returns to /mnt/Backups/Ubuntu."),
            "Tags": [],
            "TargetURL": f"file://{args.dest_dir}",
            "Sources": old["Sources"],
            "Settings": settings,
            "Filters": filters,
        },
        "Schedule": None,   # no schedule until a restore has been proven
    }
    st, body = call("backups", "POST", payload)
    print(f"create -> HTTP {st}")
    # Echo only the identifier, never the response body. The request payload
    # carried the passphrase, so anything derived from that exchange is
    # secret-adjacent -- Duplicati happens to return just {ID, Temporary}, but
    # relying on that is exactly the assumption that turns into a leak when the
    # API changes.
    if isinstance(body, dict) and body.get("ID"):
        print(f"created job id: {body['ID']}")
    elif st not in (200, 201):
        print("create FAILED; response withheld (may echo the request payload). "
              "Inspect the server log or re-run with a debugger if needed.")
    return 0 if st in (200, 201) else 1


if __name__ == "__main__":
    raise SystemExit(main())
