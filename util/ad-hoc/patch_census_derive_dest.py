#!/usr/bin/env python3
"""One-shot patch: make yamaguchi_census.py derive its destination from the job.

Ad-hoc, single-use (note 8.13).  Kept under util/ad-hoc/ rather than /tmp per the
repo's script-placement rule.  Idempotent: re-running it is a no-op.

The defect: yamaguchi_census.py hardcoded --dest to the pre-migration destination
and hardcoded its mount guard to /media/pcalnon/temp_backups.  After the 2026-08-26
move to sda1 it censused the OLD directory while printing the NEW TargetURL, so its
reconcile line compared mismatched witnesses and printed a false DIVERGE.  Once the
old directory is retired it would have censused zero files.
"""

import io
import sys

PATH = "util/ad-hoc/yamaguchi_census.py"

OLD = '''    ap.add_argument("--dest", default="/media/pcalnon/temp_backups/Yamaguchi")
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--runs", type=int, default=5, help="newest N run results to print in full")
    args = ap.parse_args()

    if not os.path.ismount("/media/pcalnon/temp_backups"):
        sys.exit("FATAL: /media/pcalnon/temp_backups is not a mountpoint")
    n_files, n_bytes = fs_census(args.dest)

    tok = api.login()
    _, state = api.req("GET", "/api/v1/serverstate", tok)
    print(f"\\n== server state: ProgramState={state.get('ProgramState')} ActiveTask={state.get('ActiveTask')} ProposedSchedule={state.get('ProposedSchedule')}")
    status, cfg = api.req("GET", f"/api/v1/backup/{args.backup_id}", tok)
    if status != 200:
        sys.exit(f"FATAL: GET backup {args.backup_id} -> {status}")
    b = cfg["Backup"]
'''

NEW = '''    ap.add_argument("--dest", default=None, help="destination directory; default: DERIVED from the job's own TargetURL")
    ap.add_argument("--backup-id", default="2")
    ap.add_argument("--runs", type=int, default=5, help="newest N run results to print in full")
    args = ap.parse_args()

    tok = api.login()
    status, cfg = api.req("GET", f"/api/v1/backup/{args.backup_id}", tok)
    if status != 200:
        sys.exit(f"FATAL: GET backup {args.backup_id} -> {status}")
    b = cfg["Backup"]

    # The destination is DERIVED from the job, never assumed.  A hardcoded default
    # survives a destination migration and then censuses the PRE-migration directory:
    # the reconcile line compares the wrong filesystem against the right server
    # metadata and prints a false DIVERGE -- and once the old directory is retired it
    # would census zero files and read as catastrophic loss.  Observed 2026-08-26
    # (note 8.13): this tool printed DIVERGE while both witnesses were in fact
    # perfectly consistent, because only one of them had followed the move.
    dest = args.dest
    if dest is None:
        target = b.get("TargetURL") or ""
        if not target.startswith("file://"):
            sys.exit(f"FATAL: job {args.backup_id} TargetURL is not a local file:// path ({target}); pass --dest explicitly")
        dest = unquote(urlparse(target).path)
    if not os.path.isdir(dest):
        sys.exit(f"FATAL: destination {dest} is not a directory")
    # Mount guard, also derived: walk up to the containing mountpoint rather than
    # naming one filesystem, so it cannot rot the way the hardcoded sdc4 check did.
    mp = os.path.abspath(dest)
    while mp != "/" and not os.path.ismount(mp):
        mp = os.path.dirname(mp)
    if mp == "/":
        sys.exit(f"FATAL: destination {dest} is not on a mounted filesystem (walked up to /)")
    n_files, n_bytes = fs_census(dest)

    _, state = api.req("GET", "/api/v1/serverstate", tok)
    print(f"\\n== server state: ProgramState={state.get('ProgramState')} ActiveTask={state.get('ActiveTask')} ProposedSchedule={state.get('ProposedSchedule')}")
'''

IMPORT_ANCHOR = "\nimport sys\n"
IMPORT_LINE = "\nimport sys\nfrom urllib.parse import unquote, urlparse\n"


def main():
    text = io.open(PATH, encoding="utf-8").read()

    if OLD not in text:
        if "DERIVED from the job's own TargetURL" in text:
            print("already patched -- no-op")
            return 0
        print("FATAL: anchor not found and file is not already patched", file=sys.stderr)
        return 1

    text = text.replace(OLD, NEW)

    if "from urllib.parse import" not in text:
        if IMPORT_ANCHOR not in text:
            print("FATAL: import anchor not found", file=sys.stderr)
            return 1
        text = text.replace(IMPORT_ANCHOR, IMPORT_LINE, 1)

    io.open(PATH, "w", encoding="utf-8").write(text)
    print("patched: destination and mount guard are now derived from the job")
    return 0


if __name__ == "__main__":
    sys.exit(main())
