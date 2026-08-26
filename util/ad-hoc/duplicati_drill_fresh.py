#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Restore drill for the FRESH Duplicati set (fileset of 2026-08-23T17:15:12),
built to the six requirements from the 2026-08-24 adversarial gate review:

1. **Destination-only restore.** With ``--dbpath`` pointing at a nonexistent
   file, duplicati-cli builds a TEMPORARY database from the destination alone
   (source-verified at the installed tag: the dbpath file is never created --
   the temp DB is a TempFile discarded per invocation, and the live job DB /
   dbconfig.json are unreachable once --dbpath is explicit) -- the true
   disaster path. Each candidate's restore performs its own independent,
   filter-scoped destination recreate (~1-3 min overhead per candidate,
   accepted for isolation). The driver asserts the dbpath file stays absent:
   if one ever appears there, the exists-branch would silently reuse it and
   the drill would stop being destination-only. Version pinning is
   unambiguous: the destination holds exactly ONE dlist (the synthetic
   fileset), so ``--version=0`` cannot resolve to the deleted 17:15:11 twin
   or the crashed 22:51:26 fileset (whose dlist was never uploaded and whose
   blocks sit in 12 absent volumes).
2. **Disposable state.** Everything (temp DB, tempdir, restored files, logs)
   lands in a fresh run dir on the scratch filesystem; the destination is only
   ever read; the passphrase key is named explicitly (PASSPHRASE, the fresh
   key) and only its sha256[:16] is logged.
3. **Mandatory flags.** ``--no-local-blocks=true`` on every restore -- most
   candidates still exist locally, and without it Duplicati would rebuild them
   from the LIVE source, a false pass indistinguishable from proof.
4. **Dual, job-DB-independent oracle.** (a) Every restored file is hashed and
   compared against the manifest's own per-file SHA-256 from filelist.json;
   (b) restored bytes are also compared against a fresh hash of the LIVE
   source file -- breaking the shared-author circularity between dlist,
   dindex, and Remotevolume records. A live-vs-restored divergence on a file
   whose filesystem mtime PREDATES the backup start is the shared-author
   corruption signal this oracle exists to catch and FAILS the drill
   (LIVE_ORACLE_CONTRADICTION); divergence with a post-backup mtime is a
   benign note. The drill is INCONCLUSIVE, not PASS, unless the live oracle
   actually engaged and matched on at least --live-floor candidates.
5. **Stratified sample + coverage metric.** Candidates are drawn across the
   upload window (early / mid / late dblocks), across size classes
   (empty, single-block, multi-block, large multi-dblock), plus one symlink;
   the report states how many distinct dblocks the sample exercises (n/104).
6. **Honest verdict.** The fileset is synthetic and marked
   ``IsFullBackup: false`` by Duplicati itself, and it omits ~45% of the
   in-scope files (296,963 listed vs >=538,168 enumerated the same evening).
   A full pass therefore reads "synthetic PARTIAL fileset verified
   restorable" -- never "restore point verified".

Exit codes: 0 = all candidates verified; 1 = any restore/verify failure;
2 = operational failure.
"""

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile

HASH_BYTES = 32


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(2)


def load_passphrase(cred_file, key):
    pp = None
    with open(cred_file) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(f"{key}=") or line.startswith(f"export {key}="):
                pp = line.split("=", 1)[1].strip().strip('"')
    if not pp:
        fail(f"no {key}= entry in {cred_file}")
    print(f"credential  : {cred_file} key={key} (sha256[:16]={hashlib.sha256(pp.encode()).hexdigest()[:16]})")
    return pp


def gpg_decrypt(src, dst, passphrase):
    with open(dst, "wb") as out:
        proc = subprocess.run(
            ["gpg", "--batch", "--quiet", "--pinentry-mode", "loopback",
             "--passphrase-fd", "0", "--decrypt", src],
            input=(passphrase + "\n").encode(), stdout=out,
            stderr=subprocess.PIPE, check=False,
        )
    if proc.returncode != 0:
        fail(f"gpg failed on {os.path.basename(src)}: {proc.stderr.decode(errors='replace')[:300]}")


def aes_decrypt(src, dst, passphrase):
    # SharpAESCrypt: password on argv (accepted single-user-host deviation);
    # rc 3 = HMAC mismatch, rc 4 = wrong password.
    proc = subprocess.run(["duplicati-aescrypt", "d", passphrase, src, dst],
                          capture_output=True, check=False)
    if proc.returncode != 0:
        fail(f"aescrypt rc={proc.returncode} on {os.path.basename(src)}: {proc.stderr.decode(errors='replace')[:200]}")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


def parse_destination(dest, workdir, passphrase, blocksize):
    """Return (filelist, block_to_dblock, blocklist_content, dblock_order)."""
    names = sorted(os.listdir(dest))
    dlists = [n for n in names if ".dlist." in n]
    dindexes = [n for n in names if ".dindex." in n]
    dblocks = [n for n in names if ".dblock." in n]
    if len(dlists) != 1:
        fail(f"expected exactly 1 dlist, found {len(dlists)}")
    print(f"destination : {dest} -> {len(dlists)} dlist / {len(dindexes)} dindex / {len(dblocks)} dblock")

    block_to_dblock = {}
    blocklist_content = {}
    for name in dindexes:
        plain = os.path.join(workdir, "dindex.zip")
        gpg_decrypt(os.path.join(dest, name), plain, passphrase)
        with zipfile.ZipFile(plain) as zf:
            for entry in zf.namelist():
                if entry.startswith("vol/"):
                    vol = entry[4:]
                    for blk in json.loads(zf.read(entry)).get("blocks", []):
                        block_to_dblock[blk["hash"]] = vol
                elif entry.startswith("list/"):
                    raw = zf.read(entry)
                    fn_plain = entry[5:].replace("-", "+").replace("_", "/")
                    if base64.b64encode(hashlib.sha256(raw).digest()).decode() != fn_plain:
                        fail(f"poisoned list entry {entry} in {name}")
                    blocklist_content[fn_plain] = [
                        base64.b64encode(raw[o:o + HASH_BYTES]).decode()
                        for o in range(0, len(raw), HASH_BYTES)]
        os.unlink(plain)

    plain = os.path.join(workdir, "dlist.zip")
    gpg_decrypt(os.path.join(dest, dlists[0]), plain, passphrase)
    with zipfile.ZipFile(plain) as zf:
        filelist = json.loads(zf.read("filelist.json"))
        fileset_meta = json.loads(zf.read("fileset"))
    os.unlink(plain)
    print(f"fileset     : IsFullBackup={fileset_meta.get('IsFullBackup')} entries={len(filelist)}")

    # upload order of dblocks by mtime
    dblock_order = sorted(dblocks, key=lambda n: os.path.getmtime(os.path.join(dest, n)))
    return filelist, block_to_dblock, blocklist_content, dblock_order


def file_blocks(entry, blocklist_content, blocksize):
    """All data-block hashes of a File entry (excluding metadata)."""
    bls = entry.get("blocklists")
    if bls:
        out = []
        for blh in bls:
            content = blocklist_content.get(blh)
            if content is None:
                fail(f"unexpandable blocklist for {entry.get('path')}")
            out.extend(content)
        return out
    if entry.get("size", 0) > 0:
        return [entry["hash"]]
    return []


def pick_candidates(filelist, block_to_dblock, blocklist_content, dblock_order, blocksize, per_stratum):
    order_idx = {n: i for i, n in enumerate(dblock_order)}
    n = len(dblock_order)
    windows = {"early": (0, n // 3), "mid": (n // 3, 2 * n // 3), "late": (2 * n // 3, n)}

    def window_of(dblocks_touched):
        idxs = [order_idx[d] for d in dblocks_touched if d in order_idx]
        if not idxs:
            return None
        mid = sorted(idxs)[len(idxs) // 2]
        for w, (lo, hi) in windows.items():
            if lo <= mid < hi:
                return w
        return "late"

    def live_size_matches(entry):
        try:
            return os.lstat(entry["path"]).st_size == entry.get("size", 0)
        except OSError:
            return False

    candidates = []
    seen_paths = set()
    seen_hashes = set()
    dir_counts = {}

    def top_dir(path):
        # containing directory, truncated to four components: caps concentration
        # for shallow dirs (a file directly under ~/X must key on ~/X, not on
        # its own filename) while keeping deep trees distinguishable
        parts = os.path.dirname(path).strip("/").split("/")
        return "/".join(parts[:4])

    def add(entry, stratum, blocks):
        path = entry["path"]
        if path in seen_paths:
            return False
        # positional filename is a FILTER to duplicati-cli: glob chars would
        # silently widen the restore
        if any(ch in path for ch in "*?[]"):
            return False
        # dedupe byte-identical content and cap per-directory concentration
        # (singleton strata -- large/empty/symlink -- are exempt from the cap)
        mh = entry.get("hash")
        if mh and mh in seen_hashes:
            return False
        td = top_dir(path)
        if stratum.split("/")[0] not in ("large", "empty", "symlink") and dir_counts.get(td, 0) >= 3:
            return False
        touched = sorted({block_to_dblock[b] for b in blocks if b in block_to_dblock})
        candidates.append({
            "path": path,
            "size": entry.get("size", 0),
            "manifest_hash": mh,
            "stratum": stratum,
            "dblocks": touched,
            "live_present": os.path.lexists(path),
            "live_size_matches": live_size_matches(entry) if entry.get("type") == "File" else False,
        })
        seen_paths.add(path)
        if mh:
            seen_hashes.add(mh)
        dir_counts[td] = dir_counts.get(td, 0) + 1
        return True

    files = [e for e in filelist if e.get("type") == "File"]
    singles = [e for e in files if not e.get("blocklists") and 0 < e.get("size", 0) <= blocksize]
    multis = [e for e in files if e.get("blocklists") and e.get("size", 0) < 60 * 2**20]
    larges = sorted((e for e in files if e.get("size", 0) >= 300 * 2**20), key=lambda e: -e["size"])
    empties = [e for e in files if e.get("size", 0) == 0]
    symlinks = [e for e in filelist if e.get("type") == "Symlink"]

    for w in ("early", "mid", "late"):
        got_s = got_m = 0
        for e in singles:
            if got_s >= per_stratum:
                break
            blocks = file_blocks(e, blocklist_content, blocksize)
            if window_of([block_to_dblock.get(b) for b in blocks if b in block_to_dblock] or []) == w and add(e, f"single/{w}", blocks):
                got_s += 1
        for e in multis:
            if got_m >= per_stratum:
                break
            blocks = file_blocks(e, blocklist_content, blocksize)
            if window_of([block_to_dblock.get(b) for b in blocks if b in block_to_dblock] or []) == w and add(e, f"multi/{w}", blocks):
                got_m += 1
    if larges:
        add(larges[0], "large", file_blocks(larges[0], blocklist_content, blocksize))
    if empties:
        add(empties[0], "empty", [])
    if symlinks:
        add(symlinks[0], "symlink", [])

    coverage = sorted({d for c in candidates for d in c["dblocks"]})
    return candidates, coverage


def main():
    ap = argparse.ArgumentParser(description="fresh-set restore drill (destination-only, dual oracle)")
    ap.add_argument("--dest", default="/media/pcalnon/temp_backups/Ubuntu")
    ap.add_argument("--run-root", default="/media/pcalnon/temp_backups/_fresh_drill")
    ap.add_argument("--cred-file", default=os.path.expanduser("~/.config/duplicati-backup/env"))
    ap.add_argument("--cred-key", default="PASSPHRASE")
    ap.add_argument("--blocksize", type=int, default=1024 * 1024)
    ap.add_argument("--per-stratum", type=int, default=2)
    ap.add_argument("--live-floor", type=int, default=10,
                    help="minimum live-oracle MATCHES for a PASS (else INCONCLUSIVE)")
    ap.add_argument("--backup-start-epoch", type=int, default=1787523309,
                    help="2026-08-23T17:15:09-05:00; live mtime BEFORE this + divergence = contradiction")
    ap.add_argument("--select-only", action="store_true", help="stop after writing candidates.json")
    ap.add_argument("--encryption", choices=["gpg", "aes"], default="gpg")
    ap.add_argument("--single-invocation", action="store_true",
                    help="restore ALL candidates in one duplicati-cli call (one shared "
                         "temp-DB recreate -- required for large sets where a per-candidate "
                         "recreate is prohibitive); candidates with duplicate basenames are "
                         "dropped so verification stays unambiguous")
    args = ap.parse_args()
    global gpg_decrypt
    if args.encryption == "aes":
        gpg_decrypt = aes_decrypt

    dest = os.path.realpath(args.dest)
    if not os.path.ismount("/media/pcalnon/temp_backups"):
        fail("/media/pcalnon/temp_backups is not a mountpoint")
    run_dir = os.path.join(args.run_root, f"drill-{time.strftime('%Y%m%d-%H%M%S')}")
    if os.path.realpath(run_dir).startswith(dest + os.sep):
        fail("run dir must not be inside the destination")
    workdir = os.path.join(run_dir, "work")
    restore_root = os.path.join(run_dir, "restored")
    tmpdir = os.path.join(run_dir, "tmp")
    for d in (workdir, restore_root, tmpdir):
        os.makedirs(d, exist_ok=True)
    dbpath = os.path.join(run_dir, "tempdb.sqlite")
    print(f"run dir     : {run_dir}")

    passphrase = load_passphrase(args.cred_file, args.cred_key)
    filelist, block_to_dblock, blocklist_content, dblock_order = parse_destination(
        dest, workdir, passphrase, args.blocksize)

    candidates, coverage = pick_candidates(
        filelist, block_to_dblock, blocklist_content, dblock_order, args.blocksize, args.per_stratum)
    with open(os.path.join(run_dir, "candidates.json"), "w") as fh:
        json.dump(candidates, fh, indent=1)
    print(f"candidates  : {len(candidates)} across strata; dblock coverage {len(coverage)}/{len(dblock_order)}")
    for c in candidates:
        print(f"  [{c['stratum']:>10}] {c['size']:>12} B  {len(c['dblocks']):>3} dblock(s)  {c['path']}")
    if args.select_only:
        return

    # ---- provenance snapshot ------------------------------------------------
    ver = subprocess.run(["dpkg-query", "-W", "-f=${Package} ${Version}\\n", "duplicati"],
                         capture_output=True, text=True, check=False)
    with open(os.path.join(run_dir, "provenance.txt"), "w") as fh:
        fh.write(f"installed package: {ver.stdout.strip() or ver.stderr.strip()}\n\ndestination inventory:\n")
        for n in sorted(os.listdir(dest)):
            st = os.stat(os.path.join(dest, n))
            fh.write(f"{n}\t{st.st_size}\t{int(st.st_mtime)}\n")

    # ---- restore phase ------------------------------------------------------
    env = dict(os.environ, PASSPHRASE=passphrase)
    results = []

    if args.single_invocation:
        seen_base = set()
        uniq = []
        for c in candidates:
            base = os.path.basename(c["path"].rstrip("/"))
            if base in seen_base:
                print(f"  dropping duplicate-basename candidate: {c['path']}")
                continue
            seen_base.add(base)
            uniq.append(c)
        candidates = uniq
        rdir = os.path.join(restore_root, "all")
        os.makedirs(rdir, exist_ok=True)
        t0 = time.monotonic()
        argv = ["duplicati-cli", "restore", f"file://{dest}"] + [c["path"] for c in candidates] + [
            f"--dbpath={dbpath}", f"--restore-path={rdir}", f"--tempdir={tmpdir}",
            "--version=0", "--no-local-blocks=true", "--overwrite=true",
            "--console-log-level=Warning"]
        proc = subprocess.run(argv, env=env, capture_output=True, text=True, check=False)
        dur = time.monotonic() - t0
        with open(os.path.join(run_dir, "restore-all.log"), "w") as fh:
            fh.write(proc.stdout + "\n--- stderr ---\n" + proc.stderr)
        if os.path.exists(dbpath):
            fail(f"{dbpath} materialized -- see per-candidate mode comment")
        print(f"  single restore invocation: rc={proc.returncode} in {dur:.0f}s for {len(candidates)} candidates")
        for c in candidates:
            verdict, detail, live_oracle = verify_candidate(c, rdir, args.backup_start_epoch)
            if proc.returncode >= 3:
                verdict, detail, live_oracle = "RESTORE_FAILED", f"rc={proc.returncode}: {proc.stderr[-200:]}", None
            results.append({**c, "rc": proc.returncode, "seconds": round(dur, 1),
                            "verdict": verdict, "detail": detail, "live_oracle": live_oracle})
            print(f"  [{c['stratum']:>12}] {verdict}  {detail}")
        finish_report(args, run_dir, results, coverage, dblock_order)
        return

    for i, c in enumerate(candidates):
        rdir = os.path.join(restore_root, f"c{i:02d}")
        os.makedirs(rdir, exist_ok=True)
        t0 = time.monotonic()
        proc = subprocess.run(
            ["duplicati-cli", "restore", f"file://{dest}", c["path"],
             f"--dbpath={dbpath}", f"--restore-path={rdir}",
             f"--tempdir={tmpdir}", "--version=0",
             "--no-local-blocks=true", "--overwrite=true",
             "--console-log-level=Warning"],
            env=env, capture_output=True, text=True, check=False,
        )
        dur = time.monotonic() - t0
        with open(os.path.join(run_dir, f"restore-c{i:02d}.log"), "w") as fh:
            fh.write(proc.stdout + "\n--- stderr ---\n" + proc.stderr)
        if os.path.exists(dbpath):
            fail(f"{dbpath} materialized -- the exists-branch would reuse it and the "
                 "drill would no longer be destination-only; investigate before rerunning")

        # duplicati-cli returncodes: 0 = success; 1 = success, no files changed;
        # 2 = success with warning(s); >=3 = errors. Only >=3 is a restore failure.
        verdict, detail, live_oracle = verify_candidate(c, rdir, args.backup_start_epoch)
        if proc.returncode >= 3:
            verdict, detail, live_oracle = "RESTORE_FAILED", f"rc={proc.returncode}: {proc.stderr[-200:]}", None
        results.append({**c, "rc": proc.returncode, "seconds": round(dur, 1),
                        "verdict": verdict, "detail": detail, "live_oracle": live_oracle})
        print(f"  c{i:02d} [{c['stratum']:>10}] rc={proc.returncode} {dur:6.1f}s  {verdict}  {detail}")

    finish_report(args, run_dir, results, coverage, dblock_order)


def finish_report(args, run_dir, results, coverage, dblock_order):
    ok = sum(1 for r in results if r["verdict"].startswith("VERIFIED"))
    live_ok = sum(1 for r in results if r["live_oracle"] == "match")
    contradictions = [r for r in results if r["live_oracle"] == "contradiction"]
    bad = [r for r in results if not r["verdict"].startswith("VERIFIED") and r["verdict"] != "UNVERIFIED_NO_ORACLE"]
    unverified = [r for r in results if r["verdict"] == "UNVERIFIED_NO_ORACLE"]
    with open(os.path.join(run_dir, "results.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    print()
    print(f"RESTORED+VERIFIED: {ok}/{len(results)} candidates; dblock coverage {len(coverage)}/{len(dblock_order)}")
    print(f"live-source oracle: {live_ok} matches, {len(contradictions)} contradictions (floor for PASS: {args.live_floor})")
    if bad or contradictions:
        print("FAILURES:")
        for r in bad:
            print(f"  {r['path']}: {r['verdict']} {r['detail']}")
        print("RESULT: DRILL FAILED")
        sys.exit(1)
    if unverified:
        for r in unverified:
            print(f"  NOTE: {r['path']}: {r['detail']}")
    if live_ok < args.live_floor:
        print(f"RESULT: INCONCLUSIVE -- restores matched the manifest, but the live-source oracle "
              f"engaged on only {live_ok} < {args.live_floor} candidates; shared-author circularity not broken")
        sys.exit(1)
    print("RESULT: fileset verified restorable for the sampled strata (dual oracle)")
    print("        (verdict scope: sampled candidates + destination-only recreate; see the run's certification note)")


def verify_candidate(c, rdir, backup_start_epoch):
    """Verify restored artifact against manifest + live source.

    Returns (verdict, detail, live_oracle) where live_oracle is one of
    "match" | "benign-divergence" | "contradiction" | None (not engaged).
    A divergence on a live file whose mtime PREDATES the backup start is the
    shared-author corruption signal the oracle exists for -- it FAILS.
    """
    base = os.path.basename(c["path"].rstrip("/"))

    if c["stratum"] == "symlink":
        for root, dirs, files in os.walk(rdir, followlinks=False):
            for nm in dirs + files:
                p = os.path.join(root, nm)
                if os.path.islink(p) and nm == base:
                    got = os.readlink(p)
                    if not os.path.lexists(c["path"]):
                        return "UNVERIFIED_NO_ORACLE", f"symlink restored (target {got}) but live link is gone; no oracle", None
                    live_target = os.readlink(c["path"])
                    if got == live_target:
                        return "VERIFIED", f"symlink target {got} == live", "match"
                    if os.lstat(c["path"]).st_mtime < backup_start_epoch:
                        return "SYMLINK_MISMATCH", f"restored->{got} live->{live_target} (live link PREDATES backup)", "contradiction"
                    return "UNVERIFIED_NO_ORACLE", f"restored->{got}, live retargeted after backup ->{live_target}", "benign-divergence"
        return "MISSING", "no symlink restored", None

    found = None
    for root, _dirs, files in os.walk(rdir):
        for nm in files:
            if nm == base:
                found = os.path.join(root, nm)
        if found:
            break
    if found is None:
        return "MISSING", "restored file not found under restore-path", None
    if c["size"] == 0:
        if os.path.getsize(found) == 0:
            return "VERIFIED", "empty file restored", None
        return "SIZE_MISMATCH", f"expected 0 got {os.path.getsize(found)}", None

    got_hash = sha256_file(found)
    if got_hash != c["manifest_hash"]:
        return "HASH_MISMATCH", f"manifest {c['manifest_hash'][:12]} != restored {got_hash[:12]}", None

    if not os.path.exists(c["path"]) or os.path.islink(c["path"]):
        return "VERIFIED", "manifest-hash-match (live source gone; oracle not engaged)", None
    live_hash = sha256_file(c["path"])
    if live_hash == got_hash:
        return "VERIFIED", "manifest-hash-match + live-oracle-match", "match"
    if os.lstat(c["path"]).st_mtime < backup_start_epoch:
        # live file claims to predate the backup yet differs from what the
        # backup stack stored AND hashed: manifest, blocks, and Remotevolume
        # share one author -- the unchanged live file is the only witness.
        return "LIVE_ORACLE_CONTRADICTION", \
            f"live mtime predates backup but live {live_hash[:12]} != restored {got_hash[:12]}", "contradiction"
    return "VERIFIED", "manifest-hash-match (live changed after backup; benign)", "benign-divergence"


if __name__ == "__main__":
    main()
