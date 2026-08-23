# Duplicati archive — damage findings and recovery posture

**Project**: Juniper (workstation backup infrastructure)
**Author**: Paul Calnon
**Date**: 2026-08-23
**Status**: Findings established; remediation not yet designed
**Predecessor**: [`HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md)

---

## 1. Headline

The `Ubuntu` Duplicati archive at `/mnt/Backups/Ubuntu` has **real data loss**, not merely a
database that disagrees with the destination.

**The most recent restorable state is 2025-11-12.** Every 2026-07 restore point is damaged.
Anything changed on the workstation since 2025-11-12 exists in exactly one place — the live disk.

This retires the open question in the predecessor handoff §5 ("was the Jul-13 deletion retention, or
damage?"). It was damage.


> **Volume integrity has since been verified** (`util/ad-hoc/duplicati_verify_volumes.py`,
> 2026-08-23): all **5,366** present volumes match the size recorded in the archived database
> exactly (0 mismatches), and a random sample of **30** volumes totalling 12.39 GiB match their
> recorded SHA-256 exactly (0 bad). So the surviving volumes are *intact*, not merely *present* —
> which was a real gap in the original analysis, since it decided survival by filename alone.
>
> **What is proven.** Both halves are now demonstrated end-to-end by the restore drill in §4a, not
> merely inferred from the database. Files sampled from the 2026-07 restore points restore as
> **0 bytes**; files sampled from 2025-11-12 restore with **byte-exact length and matching SHA-256**,
> with local-block reuse disabled so the data provably came from the archive rather than from copies
> still on disk. An earlier revision of this document called "restorable" an inference rather than a
> fact — correctly, at the time it was written. The drill closed that gap.

---

## 2. What actually happened

The destination was **99.6 % full** on 2026-07-09 (`FreeQuotaSpace` = 16.3 GB of 3.94 TB, cached in
the server database at the last successful backup). Under that pressure a retention sweep expired the
intermediate filesets, and a compact began reclaiming their volumes.

**The compact was interrupted.** Volume `duplicati-bb634e177b1b04ebe96615b2c694cd6c8.dblock.zip.gpg`
is recorded in the `Uploading` state and is absent from the destination.

A correct compact **repacks still-referenced blocks into new volumes before deleting the originals**.
That did not happen here:

| evidence | value |
|---|---|
| newest file anywhere in the destination | 2026-07-11 09:58:38 (a `dindex`) |
| destination directory mtime | 2026-07-13 17:26 |
| `temp/` subdirectory mtime | 2026-07-13 17:09 |
| replacement volumes written on 2026-07-13 | **zero** |

A directory mtime later than every file inside it, with no new files, is the signature of **deletion
only**. So on 2026-07-13 roughly 1,208 volume pairs were removed and nothing was written to replace
the live blocks they held.

Because Duplicati backups are incremental and deduplicated, the 2026-07 filesets referenced blocks
that were *physically stored* in volumes first written during 2025-12 … 2026-06. Expiring those
intermediate filesets made their volumes look reclaimable; deleting them destroyed blocks the July
filesets still depended on. That is precisely why the **old restore points survive intact and the
recent ones do not** — the 2024/2025 filesets reference old volumes that were never touched.

---

## 3. Reconciliation (three independent methods agree)

| quantity | as of archived Jul-12 DB | on disk today | delta |
|---|---:|---:|---:|
| dblock volumes (`Verified` + `Uploaded`) | 3,882 | 2,674 | **1,208** |
| dindex volumes (`Verified` + `Uploaded`) | 3,890 | 2,682 | **1,208** |
| dlist volumes (`Verified`) | 20 | 10 | 10 |

1. **Duplicati's own Repair error** (server `ErrorLog`, 2026-08-21 18:02:48) names **1,208 distinct
   missing dblock volumes**. The message is complete, not truncated.
2. **Direct filesystem cross-check**: all 1,208 named volumes are genuinely absent — 1,208/1,208,
   zero false positives.
3. **Archived-database arithmetic**: 1,223 `Blocks`-type volumes are missing overall, of which
   `Verified` (1,206) + `Uploaded` (2) = **1,208**. The remaining 15 (`Temporary` 3, `Uploading` 2,
   `Deleting` 8, `Deleted` 2) are states Repair does not count, because the database already knows
   they were never committed.

The dblock/dindex deletion is **pair-symmetric** (1,208 each), which is what orderly reclamation
looks like. That symmetry is real but does not imply the survivors are intact — see §7.

---

## 4. Damage by restore point

Computed offline by `util/ad-hoc/duplicati_offline_broken_files.py` against the archived 2026-07-12
job database. See §6 for why that database is a valid basis and §7 for the correctness controls.

| restore point | entries | damaged | verdict |
|---|---:|---:|---|
| 2024-03-04 05:03 | 2,746,726 | 0 | **intact** |
| 2024-06-03 06:03 | 3,153,606 | 0 | **intact** |
| 2025-08-31 17:22 | 2,901,748 | 0 | **intact** |
| 2025-10-06 07:03 | 891,851 | 0 | **intact** |
| 2025-11-12 06:03 | 923,285 | 0 | **intact** |
| 2026-07-06 07:03 | 1,368,424 | 484,699 | **BROKEN** |
| 2026-07-07 07:03 | 1,352,970 | 463,858 | **BROKEN** |
| 2026-07-08 07:03 | 1,355,732 | 464,603 | **BROKEN** |
| 2026-07-09 09:23 | 1,354,804 | 462,530 | **BROKEN** |
| 2026-07-11 07:03 | 1,360,811 | 463,303 | **BROKEN** |

Block-level totals: 28,461,735 blocks, of which 2,807,729 had their primary copy in a missing volume.
**Exactly one** was rescued by a surviving duplicate — so 2,807,728 blocks (9.9 %) are genuinely
unrecoverable. 993,226 blocksets and 598,690 metadatasets are affected. The blocklist-indirection
path contributed **+0** additional blocksets.

> **Caveat on the denominator**: "entries" counts `FilesetEntry` rows, which include directories and
> symlinks, so the true damaged *fraction of ordinary files* is higher than `damaged / entries`
> suggests. The damaged counts themselves are exact: `FilesetEntry` has a composite primary key
> `(FilesetID, FileID)` and `FileLookup.ID` is the rowid, so the join matches at most one row per
> entry — no fan-out, no double counting.
>
> One precision point, corrected after adversarial review: a directory or symlink cannot be flagged
> through the **content** path, because its `FileLookup.BlocksetID` is a sentinel
> (`FOLDER_BLOCKSET_ID` / `SYMLINK_BLOCKSET_ID`) that can never match a real lost blockset. But
> directories and symlinks **do** carry ordinary metadata blocksets, so the `MetadataID` arm of the
> query can legitimately flag one when its metadata block is lost. That is arguably correct — the
> metadata really is unrecoverable — but it means the damaged counts are not composed purely of
> ordinary files. An earlier phrasing here said such entries "can never be counted damaged", which
> was too absolute.

### Which filesets were deleted

The 2026-07-12 archived database held 21 filesets; 10 survive and 11 were deleted on 2026-07-13:

```
2025-12-17  2026-01-21  2026-02-25  2026-04-01  2026-05-06  2026-06-10
2026-06-17  2026-06-24  2026-07-02  2026-07-05  2026-07-12
```

This is the mechanism in §2 made explicit. The deleted set is precisely the **intermediate** cadence
— monthly through 2026-05, then weekly through 2026-07 — spanning exactly the window whose volumes
physically held the blocks the surviving July restore points reference. The five intact restore
points all predate that window, which is why they are untouched.

(The 2026-07-12 entry is a special case: as of the snapshot its dlist was still in `Uploading` state,
so it was never a committed restore point.)

---

## 4a. Restore drill — the analysis is now PROVEN, not inferred

Run 2026-08-23 (`util/ad-hoc/duplicati_drill_select.py` + `duplicati_drill_run.py`). Five files were
sampled at random from a damaged restore point and five from an intact one, **predictions recorded
before any restore was attempted**, and each result judged by SHA-256 + byte length against
`Blockset.FullHash` — never by exit code, because Duplicati emits files and reports success even when
they are empty.

| group | restore point | result |
|---|---|---|
| DAMAGED | 2026-07-11 | **5/5 as predicted** — every file restored as **0 bytes** against expected sizes of 11 KB–2 MB |
| INTACT | 2025-11-12 | **5/5 confirmed** — 4 restored automatically with length **and** SHA-256 matching; the 5th recovered by direct block extraction, hash-verified |

**The damage is demonstrated, not inferred.** Files from the July restore points come back as empty
husks while Duplicati reports them restored — which is precisely why the drill verifies content.

Two methodology points that decide whether such a drill means anything at all:

* **`--no-local-blocks=true` is mandatory.** It defaults to *false*, so Duplicati rebuilds files from
  blocks found on the **local disk**. Most drill files still exist locally, so without this the drill
  passes without ever reading the archive — a false pass indistinguishable from proof.
* **`--no-backend-verification=true` is required here**, because Duplicati otherwise aborts the whole
  restore at pre-flight over the missing volumes, producing zero files. That is an operation-level
  abort, not file-level evidence, and scoring it as damage is a false positive. **Restoring anything
  from this archive in its current state — including from the intact restore points — requires this
  flag or a completed `purge-broken-files`.** That is a real recovery obstacle.

**The one file that did not auto-restore was NOT data loss**, and the investigation is worth
recording because the obvious reading was wrong. `sortingNetworks_vs2019.vcxproj` failed to restore
from the *intact* fileset. Its single 5,043-byte block lives in
`duplicati-b82d9ca67e6234b52bdc1ad9c1d0dcb4f.dblock.zip.gpg`, which is present, `Verified`,
size-exact and hash-exact. The restore log carried a ZIP warning
(*"Number of entries expected in End Of Central Directory..."*), which suggested a second damage
class: a volume bit-identical to what was uploaded but internally malformed. **That hypothesis was
tested and refuted** — `zipfile.testzip()` and `unzip -t` both report the volume completely clean
(11,770 entries, no errors), and extracting the block directly yields 5,043 bytes hashing to exactly
the expected value. The data is intact; Duplicati's restore path dropped the file. A true premise
(there was a ZIP warning) very nearly produced a false conclusion (a second damage class, and a
claim that the damage figure was an under-estimate).

---

## 5. Surviving restore points

The ten dlist files on the destination:

| restore point | verdict |
|---|---|
| 2024-03-04 | intact |
| 2024-06-03 | intact |
| 2025-08-31 | intact |
| 2025-10-06 | intact |
| 2025-11-12 | intact |
| 2026-07-06 | damaged |
| 2026-07-07 | damaged |
| 2026-07-08 | damaged |
| 2026-07-09 | damaged |
| 2026-07-11 | damaged |

Note the **2026-07-11** restore point exists on disk although the server database's
`LastBackupDate` records 2026-07-09 — a backup completed its fileset on 07-11 and the run was never
recorded as successful. The UI's "21 versions" is a cached `BackupListCount` from 2026-07-09 and is
not evidence of anything; ground truth is the ten dlist files.

The surviving set is **not** explained by the retention ladder `1W:1D,1M:1W,6M:1M,20Y:1Y`. The
`1M:1W` and `6M:1M` tiers have zero survivors despite backups demonstrably running through
2025-12 … 2026-06 (volumes exist with those mtimes), and 2024 retains two entries where `20Y:1Y`
permits one. An earlier reading in this arc that the survivors "match the ladder exactly" was wrong
and is retracted.

---

## 6. Why the archived Jul-12 database is a valid basis

The live job database is mid-Recreate and unusable, and the real `list-broken-files` needs the GPG
passphrase. The archived `backup SJTCQIIZSJ 20260712033545.sqlite` predates the 2026-07-13 deletion,
so it still holds the complete block → blockset → file → fileset mapping.

Its validity rests on one precondition: **no replacement volumes were written after the snapshot.**
If a compact had repacked blocks into new volumes, `Block.VolumeID` would be stale and the analysis
worthless. §2 establishes deletion-only, and the tool re-checks the precondition at runtime and
refuses to run if it no longer holds.

This database must **not** be restored as the live job database — that question was settled in the
predecessor handoff §4 (schema 13 vs 19, mid-Compact, disagrees with the archive by ~1.2 TB). Reading
it is a different operation entirely, and is done `immutable=1`.

---

## 7. Correctness controls applied

The recurring failure shape in this arc is *a correct mechanism paired with a wrong consequence*.
Three specific controls were applied because of it:

- **`DuplicateBlock` is honoured.** Duplicati records additional copies of a block in
  `DuplicateBlock` (7,007,336 rows here). A block whose primary `Block.VolumeID` is missing may still
  be readable from a surviving volume. Ignoring this over-reports damage. The first run of the
  analysis did ignore it and produced an **upper bound**; the figures in §4 are from the corrected
  run, which counts a block as lost only when *every* copy is gone. The correction moved the result
  by **one block and one file** — the upper bound turned out to be effectively tight. That outcome
  does not retroactively justify skipping the check: 7 million duplicate rows could equally have
  overturned the finding, and which of those two worlds we were in was not knowable without running
  it.
- **All three failure paths are walked** — a file is damaged if a content block, a metadata block,
  *or* a blocklist block (the indirection large files use) is unavailable. Losing only the blocklist
  makes a file unreadable even when every data block survives.
- **The "expected" reading was tested, not assumed.** Disk-full pressure and pair-symmetric deletion
  both genuinely point toward benign housekeeping. Both are true. Neither implies the survivors are
  intact, and they are not.

---

## 8. Configuration state (verified 2026-08-22 → 23)

Two defects from the predecessor handoff are now closed:

- **§1 `Backup.DBPath`** — was pointing at the 479 KB *server* database; now correctly
  `/home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite`. Corrected in the UI by the owner without a
  restart (pid unchanged).
- **§2 schedule** — the `Schedule` table now holds **0 rows** and `ProposedSchedule` is empty, so no
  further runs are enqueued.

Verified side-effect-free: a keyed `(BackupID, Name)` comparison of the server database before and
after shows the *only* changes are `DBPath`, `Schedule` 1 → 0 rows, and two same-length `enc-v1`
re-encryptions (`passphrase`, `TargetURL`). Sources (1 rule) and Filters (37 rules) are byte-identical.

**The stored GPG passphrase is intact.** The web API masks it as `***************` on GET, and the
schedule change was applied via a GET → modify → PUT cycle, so this needed proof rather than
assumption. Five semantically-empty options encrypt to exactly 407 characters, establishing the
baseline; `passphrase` is 471 = 407 + 2 AES blocks → plaintext 33–48 bytes. A 15-character mask pads
to a single block and would be 407. The value was preserved; only the IV was refreshed.

### Still open

- **13 queued tasks (IDs 6–18)** remain behind the active Recreate (task 5). Duplicati's API exposes
  no dequeue verb — `task/{id}/stop` and `task/{id}/abort` both return 200 but leave a queued task at
  `Status: "Waiting"`; they act only on *running* tasks. The queue is in-memory and dies with the
  process. It is a **deferred** hazard, not an imminent one: while volumes are missing and
  `bb634e17…` sits in `Uploading`, every backup aborts during pre-flight `RemoteListAnalysis` before
  reaching retention or compact. The risk materialises only if the Recreate ever completes, which
  would rebuild a database consistent with the destination and let pre-flight pass.
- **Auto-compact is on and retention is active.** Neither `--no-auto-compact` nor any override is
  present in the job's seven settings. Per the predecessor handoff §8.4, the first backup after
  recovery should run with auto-compact disabled and retention removed.

---

## 9. Structural findings

- **The backup runs in a GUI session.** `app-gnome-duplicati-2525453.scope`, "Application launched by
  gnome-shell", and `loginctl show-user pcalnon` reports **`Linger=no`**. The process therefore dies
  at logout and nothing restarts it. This is the mechanical root cause of the 42-day silent outage
  recorded on 2026-08-21. The fix is `loginctl enable-linger pcalnon` plus a proper `systemd --user`
  unit, or a dedicated system user.
- **A second, privileged Duplicati exists.** `duplicati.service` runs `/usr/bin/duplicati-server` as
  root on port 8200, `Restart=always`, enabled, up 6 days. It is `Nice=19` /
  `IOSchedulingClass=idle`, so it is not competing for I/O. Its `yamaguchi` job has never completed a
  backup. Candidate for removal rather than migration.
- **`/tmp` is tmpfs (RAM-backed).** The Recreate stages ~1 GB volumes there, two at a time. Combined
  with the process's ~7.2 GB RSS and **swap at 100 % (20/20 GB)**, an OOM kill is a live tail risk —
  and an OOM kill is functionally `kill -9`, which the predecessor handoff §3 prohibits because the
  WAL is 8.26 GB.
- **The job description is stale.** It reads "Backup of the Development and Documents folders" but
  the source is `%HOME%` entire, with 37 exclusions.
- **`.config/Duplicati/` is not excluded**, so the databases would be backed up were it not for
  `--skip-files-larger-than=50MB`. All three archived job databases (2.26 / 11.51 / 13.17 GB) are
  therefore excluded — recovery files too large to be included in the recovery.

---

## 10. Recreate status

Task 5, started **2026-08-21 19:27:16** (the server database mtime corroborates; the predecessor
handoff's "~18:20" was an estimate). Measured rate: one ~1 GB volume per ~23 minutes, consistent with
the predecessor's ~27 min/volume figure. At that rate the remaining ~2,648 volumes are ≈ **49 days**.

It is genuinely making progress — it holds a downloaded volume open in `/tmp` and the job database
grows steadily. But it is rebuilding a database that will accurately describe an archive whose recent
restore points are broken. **It cannot resurrect deleted volumes.** Completing it does not recover
2026-07 data.

---

## 11. Recommended priorities

1. **Get a current second copy.** Everything since 2025-11-12 is single-copy on the live disk. This
   outranks any repair of the existing set.
2. **Prove the finding end-to-end** with a restore drill: one small file from a good restore point
   (2025-11-12) and one from a damaged one (2026-07-11). Nothing here is proven until a restore has
   actually been performed — none ever has.
3. **Keep the current archive read-only** for restores from the five intact points.
4. **Do not run `Repair`** (predecessor handoff §3). `purge-broken-files` is the destructive
   counterpart to `list-broken-files`; always `--dry-run` first.
5. **Fix the structural defects** in §9 — lingering, the root daemon, the 50 MB skip, database
   backups — as a separate piece of work.

---

## 12. Tooling produced

| script | purpose |
|---|---|
| `util/ad-hoc/duplicati_offline_broken_files.py` | offline `list-broken-files` from an archived job DB + destination listing; no credential, no passphrase, read-only |
| `util/ad-hoc/duplicati_server_db_diff.py` | row-level diff of two `Duplicati-server.sqlite` files |
| `util/ad-hoc/duplicati_api.py` | authenticated client for the local web API, re-authenticating on token expiry |

**Known limitation**: `duplicati_server_db_diff.py` keys rows by `ID` where present and by ordinal
position otherwise. The `Option` table has no `ID` column, so a rewrite that reorders rows produces
spurious positional diffs there. Compare `Option` keyed by `(BackupID, Name)` instead.
