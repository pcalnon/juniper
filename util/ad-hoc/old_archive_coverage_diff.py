#!/usr/bin/env python3
"""What would the old-gpg-archive purge actually destroy? Path-level coverage diff.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Written 2026-08-28 for the old-archive purge decision (note 8.15).  Purging
``/mnt/Backups/Ubuntu``'s 5,366 ``.gpg`` volumes frees ~2.38 TiB and is what
actually gates consolidating backups onto sda1 -- but only if nothing in it is
the *last* copy of something.  This answers that, by path, with sizes.

Two design points, each of which a simpler tool would get wrong:

* **Union every fileset, not just the newest.**  The old archive holds 10
  restore points spanning 2024-03-04 .. 2026-07-11.  A file deleted in 2025 is
  absent from the newest fileset but present in an older one -- and purging
  destroys it just the same.  Comparing newest-to-newest understates the loss.
  ``--all-filesets`` (the default) decrypts all 10; ``--newest-only`` is the
  cheap approximation and says so in its own output.
* **Compare by path, report by top-level directory.**  A raw count of 400,000
  orphaned paths is not decidable; "``~/.local/share/Steam`` 611 GiB, all
  re-downloadable" is.  Sizes come from the archive's own manifest, so a path
  present in several filesets at different sizes is counted at its largest.

The comparison is against the LIVE set's newest fileset -- what a restore today
could actually produce.  A path in the live set is considered covered even if
its contents have since changed: this tool answers "is this path backed up
somewhere else", not "is this exact version".  That limit is stated in the
output, because it is the difference between "covered" and "identical".

Read-only on both destinations.  Plaintext goes to a scratch filesystem that
must differ from both.  Passphrases are read by variable name and never printed.

Exit: 0 diff produced, 2 setup error.
"""

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import tempfile
import zipfile

CRED_FILE_DEFAULT = os.path.expanduser("~/.config/duplicati-backup/env")


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(2)


def load_passphrase(cred_file, key):
    import re
    try:
        with open(cred_file) as fh:
            for line in fh:
                m = re.match(rf"^\s*(?:export\s+)?{re.escape(key)}=(.*)$", line)
                if m and m.group(1).strip():
                    return m.group(1).strip().strip("'\"")
    except OSError as exc:
        fail(f"cannot read {cred_file}: {exc}")
    fail(f"no {key}= in {cred_file}")


def mount_point_of(path):
    p = os.path.realpath(path)
    while not os.path.ismount(p) and p != "/":
        p = os.path.dirname(p)
    return p


def decrypt(src, dst, passphrase, encryption):
    if encryption == "aes":
        proc = subprocess.run(  # nosec B603 -- fixed argv, no shell
            ["duplicati-aescrypt", "d", passphrase, src, dst], capture_output=True, check=False
        )
        if proc.returncode != 0:
            fail(f"aescrypt rc={proc.returncode} on {os.path.basename(src)}")
    else:
        with open(dst, "wb") as out:
            proc = subprocess.run(  # nosec B603 -- fixed argv, no shell
                ["gpg", "--batch", "--quiet", "--no-tty", "--pinentry-mode", "loopback",
                 "--passphrase-fd", "0", "--decrypt", src],
                input=(passphrase + "\n").encode(), stdout=out, stderr=subprocess.PIPE, check=False,
            )
        if proc.returncode != 0:
            fail(f"gpg rc={proc.returncode} on {os.path.basename(src)}: "
                 f"{proc.stderr.decode(errors='replace')[:200]}")


def read_fileset(dest, dlist_name, passphrase, encryption, scratch):
    """Return {path: size} for File entries in one dlist. Sizes are the archive's own."""
    workdir = tempfile.mkdtemp(prefix="cov-diff-", dir=scratch)
    try:
        plain = os.path.join(workdir, "dlist.zip")
        decrypt(os.path.join(dest, dlist_name), plain, passphrase, encryption)
        with zipfile.ZipFile(plain) as zf:
            filelist = json.loads(zf.read("filelist.json"))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    out = {}
    for e in filelist:
        if e.get("type") != "File":
            continue
        p = e.get("path")
        if not p:
            continue
        s = int(e.get("size", 0) or 0)
        if s > out.get(p, -1):
            out[p] = s
    return out


def top_level(path, depth):
    """Group key: the first `depth` path segments, so the report is readable."""
    parts = [x for x in path.split("/") if x]
    return "/" + "/".join(parts[:depth]) if parts else path


def human(n):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} TiB"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--old-dest", default="/mnt/Backups/Ubuntu")
    ap.add_argument("--old-encryption", choices=["gpg", "aes"], default="gpg")
    ap.add_argument("--old-cred-key", default="PASSPHRASE_OLD")
    ap.add_argument("--live-dest", default="/mnt/Backups/Ubuntu/Yamaguchi")
    ap.add_argument("--live-encryption", choices=["gpg", "aes"], default="aes")
    ap.add_argument("--live-cred-key", default="PASSPHRASE")
    ap.add_argument("--cred-file", default=CRED_FILE_DEFAULT)
    ap.add_argument("--scratch", default="/home/pcalnon/.cache")
    ap.add_argument("--newest-only", action="store_true",
                    help="only the newest old fileset (cheap; UNDERSTATES the loss)")
    ap.add_argument("--depth", type=int, default=3, help="path segments to group by (default 3)")
    ap.add_argument("--top", type=int, default=30, help="groups to print (default 30)")
    ap.add_argument("--json", help="write the full orphan grouping to this JSON file")
    ap.add_argument("--dump-orphans", metavar="FILE",
                    help="write every orphan as 'size<TAB>path'. Decrypting all 10 filesets costs "
                         "~10 min; dump once and every later question is a grep over this file.")
    args = ap.parse_args()

    for d in (args.old_dest, args.live_dest):
        if not os.path.isdir(d):
            fail(f"not a directory: {d}")
    scratch_mp = mount_point_of(args.scratch)
    if scratch_mp in (mount_point_of(args.old_dest), mount_point_of(args.live_dest)):
        fail(f"scratch {args.scratch} shares a filesystem with a destination -- "
             "plaintext must never land on the disk holding the encrypted set")

    old_dlists = sorted(n for n in os.listdir(args.old_dest) if ".dlist." in n)
    live_dlists = sorted(n for n in os.listdir(args.live_dest) if ".dlist." in n)
    if not old_dlists or not live_dlists:
        fail("a destination has no dlist")
    chosen = old_dlists[-1:] if args.newest_only else old_dlists

    old_pass = load_passphrase(args.cred_file, args.old_cred_key)
    live_pass = load_passphrase(args.cred_file, args.live_cred_key)

    print(f"== old-archive purge: coverage diff at {args.old_dest}")
    print(f"   old  : {len(old_dlists)} fileset(s), reading {len(chosen)} "
          f"({'NEWEST ONLY -- understates loss' if args.newest_only else 'ALL -- union'})")
    print(f"   live : {live_dlists[-1]} (newest of {len(live_dlists)})")

    old_files = {}
    for name in chosen:
        got = read_fileset(args.old_dest, name, old_pass, args.old_encryption, args.scratch)
        for p, s in got.items():
            if s > old_files.get(p, -1):
                old_files[p] = s
        print(f"   read {name}: {len(got)} files (union now {len(old_files)})")

    live_files = read_fileset(args.live_dest, live_dlists[-1], live_pass,
                              args.live_encryption, args.scratch)
    print(f"   read {live_dlists[-1]}: {len(live_files)} files")

    live_paths = set(live_files)
    orphans = {p: s for p, s in old_files.items() if p not in live_paths}
    orphan_bytes = sum(orphans.values())
    old_bytes = sum(old_files.values())

    print("\n== totals")
    print(f"   old union      : {len(old_files):>9} files  {human(old_bytes)}")
    print(f"   live newest    : {len(live_files):>9} files  {human(sum(live_files.values()))}")
    print(f"   ONLY in old    : {len(orphans):>9} files  {human(orphan_bytes)}"
          f"   <- destroyed by the purge")
    covered = len(old_files) - len(orphans)
    pct = (100.0 * covered / len(old_files)) if old_files else 0.0
    print(f"   also in live   : {covered:>9} files  ({pct:.1f}% of old paths)")

    groups = {}
    for p, s in orphans.items():
        k = top_level(p, args.depth)
        g = groups.setdefault(k, [0, 0])
        g[0] += 1
        g[1] += s
    ranked = sorted(groups.items(), key=lambda kv: -kv[1][1])

    print(f"\n== where the ONLY-in-old bytes live (top {args.top} of {len(ranked)} groups, depth {args.depth})")
    for k, (cnt, byt) in ranked[: args.top]:
        print(f"   {human(byt):>12}  {cnt:>8} files  {k}")
    if len(ranked) > args.top:
        rest_c = sum(c for _, (c, _) in ranked[args.top:])
        rest_b = sum(b for _, (_, b) in ranked[args.top:])
        print(f"   {human(rest_b):>12}  {rest_c:>8} files  ... {len(ranked) - args.top} more groups")

    print("\n== honest limits")
    print("   * 'covered' means the PATH exists in the live set, not that the CONTENT matches;")
    print("     a file changed since 2026-07-11 is backed up, but only in its current form.")
    if args.newest_only:
        print("   * --newest-only was used: paths deleted before 2026-07-11 are NOT counted.")
    else:
        print(f"   * all {len(chosen)} old filesets unioned, so deleted-then-purged files ARE counted.")

    if args.dump_orphans:
        with open(args.dump_orphans, "w") as fh:
            for p, s in sorted(orphans.items(), key=lambda kv: -kv[1]):
                fh.write(f"{s}\t{p}\n")
        print(f"\norphans     : {args.dump_orphans} ({len(orphans)} lines, size<TAB>path, largest first)")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({
                "old_dest": args.old_dest, "live_dest": args.live_dest,
                "old_dlists_read": chosen, "live_dlist": live_dlists[-1],
                "old_files": len(old_files), "old_bytes": old_bytes,
                "live_files": len(live_files), "live_bytes": sum(live_files.values()),
                "orphan_files": len(orphans), "orphan_bytes": orphan_bytes,
                "groups": [{"group": k, "files": c, "bytes": b} for k, (c, b) in ranked],
            }, fh, indent=2)
        print(f"\njson        : {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
