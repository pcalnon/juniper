#!/usr/bin/env python3
"""Execute the old-archive purge, option (b): delete the volumes, keep the ten dlists.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Paul's decision 2026-08-28 on note §8.15.6: purge the old gpg archive's data
volumes and keep its ten ``.dlist`` files (~978 MB) as a permanently queryable
record of what was on this machine 2024-03-04 .. 2026-07-11.  §8.15 established
that nothing in the archive is the last copy of irreplaceable data.

This deletes ~2,375 GiB across 5,356 files and cannot be undone, so every claim
it relies on is re-proven here at run time rather than trusted from the note.
Dry run by default; ``--execute`` is required to delete anything.

Gates, all fatal, checked before a single file is removed:

* **0** archive root is mounted, and is the fstab-managed sda1 filesystem.
* **1** no Duplicati task is active or queued -- deleting 2.3 TiB out from under
  a running job is the one way to damage the *live* set from here.
* **2** the live job's TargetURL is the ``Yamaguchi/`` **subdirectory**, which is
  what makes a non-recursive root delete safe.  If the live job ever pointed at
  the root itself, this tool must refuse.
* **3** the live set reconciles -- filesystem file count and byte total equal the
  server's ``TargetFilesCount``/``TargetFilesSize``.  Do not purge a fallback
  while the thing it is a fallback for is unhealthy.
* **4** exactly ten dlists, and **every one decrypts and is a Zip**.  The record
  being kept is verified before the volumes that make it redundant are removed.
* **5** the record is *useful*: a dlist is queried in isolation, with zero
  dindex and zero dblock present, and must yield its full file listing.  This is
  the gate that validates option (b) itself -- if a dlist needed its volumes to
  be readable, (b) would preserve nothing and this tool must refuse.
* **6** the deletion set is exactly the root-level ``.dblock``/``.dindex``
  volumes: nothing under ``Yamaguchi/``, nothing under ``_yamaguchi_records/``,
  and **zero dlists**, asserted explicitly rather than assumed from the glob.
* **7** the ten dlists are copied to a second filesystem and byte-verified
  there before anything is deleted.

Exit: 0 done (or dry run clean), 3 a gate refused, 4 deletion incomplete.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamaguchi_server_api as api  # noqa: E402 -- sibling module; path fixed one line above

ARCHIVE = "/mnt/Backups/Ubuntu"
LIVE_SUBDIR = "Yamaguchi"
RECORDS_SUBDIR = "_yamaguchi_records"
CRED_FILE = os.path.expanduser("~/.config/duplicati-backup/env")
CRED_KEY = "PASSPHRASE_OLD"
EXPECTED_DLISTS = 10
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")

README = """\
# Old Duplicati gpg archive -- dlists retained, volumes purged

The data volumes of this archive were deleted {when} under note section 8.15.6,
option (b): the analysis in section 8.15 established that nothing in the archive
was the last copy of irreplaceable data -- every large group was either a
deliberate exclusion in the live Yamaguchi job's own filters, or content already
deleted from disk and re-obtainable upstream (Llama-2 / CodeLlama weights,
anaconda3 environments).

What was removed: {ndel} volumes ({freed}).
What is kept: the {ndlist} .dlist files below -- a complete, queryable record of
every path that existed on this machine across ten restore points spanning
2024-03-04 .. 2026-07-11.

These dlists are self-contained. A dlist does NOT need its dblock volumes to be
read; it was verified in isolation, with zero volumes present, before the purge.
What they can no longer do is RESTORE -- the file data is gone. They answer
"what existed, how big was it, and when", not "give it back".

Keep all ten. Older filesets record paths the newest does not: the Llama-2
weights, for instance, were deleted from disk before the final 2026-07-11
fileset and appear only in earlier ones.

Query them with (from the juniper-ml repo):

    python3 util/ad-hoc/duplicati_dlist_query.py \\
        --dest {archive} --encryption gpg --cred-key PASSPHRASE_OLD \\
        --scratch /home/pcalnon/.cache --match '<regex>'

The passphrase is PASSPHRASE_OLD in ~/.config/duplicati-backup/env. That tool
reads the NEWEST dlist in --dest; to query an older restore point, put just that
dlist in a directory of its own and point --dest at it.

A second copy of these dlists is at: {mirror}
"""


def refuse(msg):
    print(f"\nREFUSED: {msg}", file=sys.stderr)
    sys.exit(3)


def human(n):
    v = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(v) < 1024 or unit == "TiB":
            return f"{v:.1f} {unit}" if unit != "B" else f"{int(v)} B"
        v /= 1024.0
    return f"{v:.1f} TiB"


def load_passphrase():
    import re
    with open(CRED_FILE) as fh:
        for line in fh:
            m = re.match(rf"^\s*(?:export\s+)?{re.escape(CRED_KEY)}=(.*)$", line)
            if m and m.group(1).strip():
                return m.group(1).strip().strip("'\"")
    refuse(f"no {CRED_KEY}= in {CRED_FILE}")


def gpg_decrypt(path, passphrase):
    """Decrypt to memory. Returns bytes, or None on failure."""
    proc = subprocess.run(  # nosec B603 -- fixed argv, no shell
        ["gpg", "--batch", "--quiet", "--no-tty", "--pinentry-mode", "loopback",
         "--passphrase-fd", "0", "--decrypt", path],
        input=passphrase.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800,
    )
    return proc.stdout if proc.returncode == 0 else None


def mount_source(path):
    """Return the device backing `path`'s mountpoint, from /proc/mounts."""
    p = os.path.realpath(path)
    while not os.path.ismount(p) and p != "/":
        p = os.path.dirname(p)
    best, src = "", ""
    with open("/proc/mounts") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 2 and p == parts[1] and len(parts[1]) >= len(best):
                best, src = parts[1], parts[0]
    return p, src


def in_fstab(mount_target):
    try:
        with open("/etc/fstab") as fh:
            for line in fh:
                s = line.strip()
                if s and not s.startswith("#"):
                    f = s.split()
                    if len(f) >= 2 and f[1] == mount_target:
                        return True
    except OSError as exc:
        # Fail SAFE and say so. An unreadable /etc/fstab means "cannot prove this mount is
        # boot-durable", which gate 0 must treat as a refusal -- but silently returning False
        # would make an unreadable file indistinguishable from a genuinely absent entry.
        print(f"   cannot read /etc/fstab ({exc}) -- treating {mount_target} as NOT fstab-managed",
              file=sys.stderr)
    return False


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--archive", default=ARCHIVE)
    ap.add_argument("--mirror", default="/media/pcalnon/temp_backups/_old_archive_dlists",
                    help="second filesystem for the retained dlists (gate 7)")
    ap.add_argument("--execute", action="store_true", help="actually delete (default: dry run)")
    args = ap.parse_args()

    archive = os.path.realpath(args.archive)
    live = os.path.join(archive, LIVE_SUBDIR)
    print(f"== old-archive purge (option b) at {archive}")
    print(f"   mode: {'EXECUTE' if args.execute else 'DRY RUN'}")

    # ---- gate 0: the archive filesystem
    mp, src = mount_source(archive)
    if mp == "/":
        refuse(f"{archive} is not on a mounted filesystem")
    if not in_fstab(mp):
        refuse(f"{mp} ({src}) has no /etc/fstab entry -- refusing to purge on a non-durable mount")
    print(f"gate 0 PASS: {archive} on {src} at {mp}, fstab-managed")

    # ---- gates 1-3: the live job must be idle, correctly targeted, and healthy
    tok = api.login()
    st, state = api.req("GET", "/api/v1/serverstate", tok)
    if st != 200:
        refuse(f"serverstate -> {st}")
    if state.get("ActiveTask") or state.get("SchedulerQueueIds"):
        refuse(f"a task is active or queued: ActiveTask={state.get('ActiveTask')} "
               f"queue={state.get('SchedulerQueueIds')}")
    print("gate 1 PASS: ActiveTask=null, scheduler queue empty")

    st, body = api.req("GET", "/api/v1/backup/2", tok)
    if st != 200 or "Backup" not in body:
        refuse(f"GET backup 2 -> {st}")
    target = body["Backup"].get("TargetURL", "")
    expect = f"file://{live}"
    if target.rstrip("/") != expect.rstrip("/"):
        refuse(f"live TargetURL is {target!r}, expected {expect!r} -- a non-recursive root delete "
               "is only safe while the live set is a SUBDIRECTORY")
    print(f"gate 2 PASS: live TargetURL is the subdirectory {target}")

    meta = {m["Name"]: m["Value"] for m in body["Backup"].get("Metadata", [])} \
        if isinstance(body["Backup"].get("Metadata"), list) else dict(body["Backup"].get("Metadata") or {})
    live_files, live_bytes = 0, 0
    with os.scandir(live) as it:
        for e in it:
            if e.is_file():
                live_files += 1
                live_bytes += e.stat().st_size
    want_c, want_s = int(meta.get("TargetFilesCount", -1)), int(meta.get("TargetFilesSize", -1))
    if (live_files, live_bytes) != (want_c, want_s):
        refuse(f"live set does not reconcile: filesystem {live_files}/{live_bytes} vs "
               f"server {want_c}/{want_s} -- do not purge the fallback while the live set is off")
    print(f"gate 3 PASS: live set reconciles -- {live_files} files / {live_bytes} B AGREE")

    # ---- gate 4: every retained dlist decrypts and is a Zip
    names = sorted(n for n in os.listdir(archive) if os.path.isfile(os.path.join(archive, n)))
    dlists = [n for n in names if n.endswith(".dlist.zip.gpg")]
    dblocks = [n for n in names if n.endswith(".dblock.zip.gpg")]
    dindexes = [n for n in names if n.endswith(".dindex.zip.gpg")]
    other = [n for n in names if n not in set(dlists) | set(dblocks) | set(dindexes)]
    if len(dlists) != EXPECTED_DLISTS:
        refuse(f"expected {EXPECTED_DLISTS} dlists, found {len(dlists)}")
    passphrase = load_passphrase()
    for n in dlists:
        plain = gpg_decrypt(os.path.join(archive, n), passphrase)
        if plain is None or not plain.startswith(ZIP_MAGIC):
            refuse(f"dlist {n} did not decrypt to a Zip -- the record being KEPT is not sound")
    print(f"gate 4 PASS: all {len(dlists)} dlists decrypt and are Zip")

    # ---- gate 5: a dlist is useful with zero volumes present (validates option b)
    probe_dir = os.path.join("/home/pcalnon/.cache", "purge-gate5-probe")
    shutil.rmtree(probe_dir, ignore_errors=True)
    os.makedirs(probe_dir)
    try:
        shutil.copy2(os.path.join(archive, dlists[-1]), probe_dir)
        # NOT an assert: this is the isolation the gate depends on, and `python -O` strips
        # asserts -- a safety gate that can be compiled away is not a gate.
        stray = [x for x in os.listdir(probe_dir) if ".dblock." in x or ".dindex." in x]
        if stray:
            refuse(f"gate 5 probe dir is not isolated, found volumes: {stray}")
        plain = gpg_decrypt(os.path.join(probe_dir, dlists[-1]), passphrase)
        tmpzip = os.path.join(probe_dir, "probe.zip")
        with open(tmpzip, "wb") as fh:
            fh.write(plain)
        with zipfile.ZipFile(tmpzip) as zf:
            entries = json.loads(zf.read("filelist.json"))
        if len(entries) < 1000:
            refuse(f"isolated dlist yielded only {len(entries)} entries -- record is not usable alone")
        print(f"gate 5 PASS: isolated dlist (0 dblock, 0 dindex) yielded {len(entries)} entries")
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)

    # ---- gate 6: the deletion set, asserted rather than assumed
    doomed = [os.path.join(archive, n) for n in dblocks + dindexes]
    if any(p.endswith(".dlist.zip.gpg") for p in doomed):
        refuse("a dlist is in the deletion set")
    for p in doomed:
        rel = os.path.relpath(p, archive)
        if os.sep in rel:
            refuse(f"deletion set escapes the archive root: {rel}")
        if rel.startswith(LIVE_SUBDIR) or rel.startswith(RECORDS_SUBDIR):
            refuse(f"deletion set touches a protected subtree: {rel}")
    doomed_bytes = sum(os.path.getsize(p) for p in doomed)
    print(f"gate 6 PASS: deletion set is {len(doomed)} root-level volumes "
          f"({len(dblocks)} dblock + {len(dindexes)} dindex), {human(doomed_bytes)}; "
          f"0 dlists, 0 files under {LIVE_SUBDIR}/ or {RECORDS_SUBDIR}/")
    if other:
        print(f"   note: {len(other)} other root file(s) NOT in the deletion set: {other[:5]}")

    # ---- gate 7: mirror the retained dlists to a second filesystem
    mirror = os.path.realpath(args.mirror)
    mmp, msrc = mount_source(mirror if os.path.isdir(mirror) else os.path.dirname(mirror))
    if mmp == mp:
        refuse(f"mirror {mirror} is on the same filesystem as the archive ({mp})")
    if not args.execute:
        print(f"gate 7 (dry run): would mirror {len(dlists)} dlists to {mirror} on {msrc}")
    else:
        os.makedirs(mirror, exist_ok=True)
        for n in dlists:
            s, d = os.path.join(archive, n), os.path.join(mirror, n)
            if not (os.path.exists(d) and os.path.getsize(d) == os.path.getsize(s)):
                shutil.copy2(s, d)
        bad = [n for n in dlists
               if sha256_file(os.path.join(archive, n)) != sha256_file(os.path.join(mirror, n))]
        if bad:
            refuse(f"mirror verification failed for {bad}")
        print(f"gate 7 PASS: {len(dlists)} dlists mirrored to {mirror} on {msrc}, sha256-verified")

    print("\n== summary")
    print(f"   delete : {len(doomed)} volumes  {human(doomed_bytes)}")
    print(f"   keep   : {len(dlists)} dlists   "
          f"{human(sum(os.path.getsize(os.path.join(archive, n)) for n in dlists))}")
    st = os.statvfs(archive)
    print(f"   free now: {human(st.f_bavail * st.f_frsize)}")

    if not args.execute:
        print("\nDRY RUN -- nothing deleted. All gates passed; re-run with --execute.")
        return 0

    removed = 0
    freed = 0
    for p in doomed:
        try:
            sz = os.path.getsize(p)
            os.remove(p)
            removed += 1
            freed += sz
        except OSError as exc:
            print(f"   ! {os.path.basename(p)}: {exc}", file=sys.stderr)
    print(f"\ndeleted {removed}/{len(doomed)} volumes, freed {human(freed)}")

    left = sorted(n for n in os.listdir(archive) if os.path.isfile(os.path.join(archive, n)))
    left_dlists = [n for n in left if n.endswith(".dlist.zip.gpg")]
    if len(left_dlists) != EXPECTED_DLISTS:
        print(f"FATAL: {len(left_dlists)} dlists remain, expected {EXPECTED_DLISTS}", file=sys.stderr)
        return 4
    if any(n.endswith((".dblock.zip.gpg", ".dindex.zip.gpg")) for n in left):
        print("FATAL: volumes remain at the archive root", file=sys.stderr)
        return 4

    with open(os.path.join(archive, "README.md"), "w") as fh:
        fh.write(README.format(
            when="2026-08-28", ndel=removed, freed=human(freed), ndlist=len(left_dlists),
            archive=archive, mirror=mirror))
    st = os.statvfs(archive)
    print(f"kept {len(left_dlists)} dlists + README.md; free now {human(st.f_bavail * st.f_frsize)}")
    if removed != len(doomed):
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
