# HANDOFF 2026-08-22 — Duplicati recovery: fix DBPath FIRST, then decide

**Read §1 before touching anything. There is a latent corruption that fires on the next Duplicati
restart.** Everything else can wait; that cannot.

Predecessor arc: `HANDOFF_2026-08-21_backup-systematization-design-arc.md` (juniper-ml#1216, #1241).
That handoff's *design* framing still stands. This one is the operational thread.

> ## ⛔ A RUNBOOK I WROTE WAS WRONG — DO NOT EXECUTE IT
>
> `notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md` (written today,
> **never merged, never executed**) proposed restoring the 2026-07-12 archived job database. Two
> independent validators refuted it and I confirmed the key points myself. **Its premise is false.**
> §4 records exactly why, so the idea is not re-invented. Treat that file as a specimen, not a plan.

---

## 1. FIRST STEP — the job's database path points at the wrong file

**Verified 2026-08-22:**

```bash
LIVE  /home/pcalnon/.config/Duplicati/Duplicati-server.sqlite
      → Backup.DBPath = '/home/pcalnon/.config/Duplicati/Duplicati-server.sqlite'   ← WRONG
MANUAL COPY (18:19 Aug-21) Duplicati-server_2026-08-21.sqlite
      → Backup.DBPath = '/home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite'         ← CORRECT
```

The `Ubuntu` job's **local job database** setting now names the 479 KB **server** database. It changed
between 18:19 and 19:27 on 2026-08-21 — the window the owner was in the UI running Repair/Recreate.
Mechanism is almost certainly the Database page's **Placement** box
(`/ngclient/backup/2/database`, buttons `Reset` / `Save` / `Save & Repair` / `Move existing database`).

**Why it is not yet broken:** the running process holds the correct file open — verified via
`/proc/<pid>/fd`: `SJTCQIIZSJ.sqlite` + `-wal` + `-shm`. The bad value is config-only and takes effect
**on next start**.

### Fix it

UI → `http://127.0.0.1:8300/ngclient/backup/2/database` → Placement →
set to `/home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite` → **`Save`**.

- ⛔ **NOT `Save & Repair`** — Repair must never be run here (§3).
- ⛔ **NOT `Move existing database`** — that moves files.

Verify:

```bash
python3 -c "import sqlite3;c=sqlite3.connect('file:/home/pcalnon/.config/Duplicati/Duplicati-server.sqlite?mode=ro',uri=True);print(list(c.execute('SELECT ID,Name,DBPath FROM Backup')))"
```

**Do not restart Duplicati until this reads `SJTCQIIZSJ.sqlite`.**

---

## 2. SECOND — disable the schedule before any restart

**Verified:** `Schedule` → next run **2026-08-22 07:03** (already overdue; it is 15:32), `Repeat=1D`,
all days allowed. Plus `startup-delay = 30m`, `retention-policy = 1W:1D,1M:1W,6M:1M,20Y:1Y`, and
auto-compact is **on** by default (`--no-auto-compact=false`).

So a restart fires an unattended backup 30 minutes later, against a database whose state is unknown,
with **retention deletions and compaction enabled** — both of which delete from the archive.

UI → `Ubuntu` → Edit → Schedule → **"Automatically run backups" OFF** → Save. Confirm the Home row
shows no "Next scheduled run".

---

## 3. Standing prohibitions

- **NEVER run `Repair`.** With a database that disagrees with the archive, Repair re-uploads
  dlist/dindex volumes reconstructed *from the database* and can delete remote volumes it does not
  recognise. It is the UI's default suggestion, which makes it the likeliest mistake.
- **NEVER `kill -9` Duplicati.** The live WAL is **8.26 GB**; shutdown checkpointing takes many
  minutes. `kill` (TERM), then wait in a loop; a shrinking `-wal` with a growing `.sqlite` means it is
  working.
- **Verify the mount before any destination operation.** `/mnt/Backups` is **not** a mountpoint;
  `/mnt/Backups/Ubuntu` is (`/dev/sda1`, 3.6 T, 1.1 T free). If unmounted, the path resolves to an
  empty dir on `/` and any destination op is catastrophic:

  ```bash
  mountpoint -q /mnt/Backups/Ubuntu || { echo "NOT MOUNTED - STOP"; exit 1; }
  ```

- **`pgrep -x duplicati` is safe** — returns only the user instance (pid was 2525453). Root's daemon
  has `comm=duplicati-serve` (15-char truncation) and cannot match. But `pgrep duplicati` without
  `-x` matches **both**. Never signal the root pid; it is `Restart=always` and respawns.

---

## 4. Why the Jul-12 database restore is WRONG (do not retry it)

All verified directly against `backup SJTCQIIZSJ 20260712033545.sqlite` with `immutable=1`:

| finding                                   | evidence                                                                                                                                                                      |
|-------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **It already contains the wedge**         | 3 volumes in `Uploading` — including `duplicati-bb634e177b1b04ebe96615b2c694cd6c8.dblock.zip.gpg`, the exact volume the job is stuck on. Restoring it reproduces the failure. |
| **Wrong schema**                          | `Version` = **13**; live database built by 2.3.0.4 is **19**. Six migrations.                                                                                                 |
| **Disagrees with the archive by ~1.2 TB** | It expects ~1,200 dblock volumes that no longer exist.                                                                                                                        |
| **Taken mid-Compact**                     | Its last operation is a `Compact` (the one operation that deletes remote data) still in flight.                                                                               |
| Also present                              | 3 `Temporary`, 8 `Deleting` rows.                                                                                                                                             |

Older copies are **worse**, not graceful fallbacks: the 2025-08-31 database knows only ~3,100 of the
5,366 files present. Retention and compaction have run repeatedly since.

---

## 5. Ground truth about the archive

**I previously told the owner "your backup data is untouched and safe". That was wrong and is
retracted.**

- Destination: **2,674 dblock + 2,682 dindex + 10 dlist = 5,366 files**, 2.4 TB used, 1.1 TB free.
- Directory mtime **2026-07-13 17:26** while the newest file is **2026-07-11 09:58** — only a
  **deletion** bumps a directory mtime with no newer file in it.
- Server DB cached at last success: `TargetFilesCount = 7761`, `TargetFilesSize = 3.72 TB`.
  Today: 5,366 files / 2.4 TB. **~2,400 files, ~1.2 TB removed on 2026-07-13.**

⚠ **This is not necessarily data loss.** Retention (`1W:1D,1M:1W,6M:1M,20Y:1Y`) plus compaction
produces exactly this signature, and the 10 surviving restore points may be perfectly sound — the
deleted volumes may have belonged to expired filesets. **`list-broken-files` is what distinguishes
"expired, fine" from "restore points broken." Run it before drawing any conclusion.**

Note the "21 versions" shown in the UI is a **cached** `Metadata.BackupListCount` from 2026-07-09 and
is **not** evidence of anything. Ground truth is the **10** dlist files on disk.

---

## 6. How to run `list-broken-files`

### Route A — the UI's Commandline runner (preferred)

```bash
http://127.0.0.1:8300/ngclient/backup/2/commandline
```

Job id **2** is `Ubuntu`. It pre-fills target URL, passphrase, encryption module and `--dbpath` from
the job config — so you never handle the GPG passphrase, which is `enc-v1:`-encrypted and not
readable otherwise.

⚠ **The command dropdown defaults to `backup`.** Confirm it reads `list-broken-files` before running.
⚠ **Fix §1 first** — this route reads `Backup.DBPath` and would otherwise pass the wrong `--dbpath`.

### Route B — CLI

```bash
export PASSPHRASE='<backup passphrase>'     # never --passphrase on the command line (visible in ps)
duplicati-cli list-broken-files "file:///mnt/Backups/Ubuntu" \
    --dbpath=/home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite \
    --encryption-module=gpg
```

`--dbpath` is essential — without it the CLI builds a database from scratch (the multi-week
operation). Duplicati documents `PASSPHRASE` explicitly; `--parameters-file` is the alternative.

`purge-broken-files` is the destructive counterpart — it removes from the database **and remote
storage**. Always `--dry-run` first, and stop if it proposes touching any of the 10 good restore points.

---

## 7. The Recreate currently running

Started 2026-08-21 ~18:20. Still running at time of writing (~21 h).

- It consumed **all 2,682 dindex + 10 dlist on day 1**, then fell through to **dblocks** on day 2 —
  the documented fallback when the index cannot satisfy the block map. Given ~1,200 dblocks are
  missing, an incomplete index is expected. **The fallback is a symptom, not the defect.**
- Measured cost: ~27 min per dblock, 2,648 remaining ≈ **49 days**. Two independent methods agree.
- It will **not** auto-resume after a restart (no task queue in the server DB). The *schedule* is the
  restart hazard, not the Recreate.
- **It is building a database that matches the archive** — which the Jul-12 copy does not. That makes
  "let it finish, throttled" a legitimate option rather than an obvious loss, despite the duration.

---

## 8. Decision, once §1 and §2 are done

1. Run `list-broken-files` (§6). It is read-only and it decides everything.
2. **If the 10 restore points are sound** — the archive is fine; the question is only how to get a
   working database. Options: let the Recreate finish (~49 d), or `purge-broken-files` to clear the
   stuck volume, or start a fresh backup set to a new folder and keep the current archive read-only
   for restores.
3. **If restore points are broken** — that is real data loss and changes priorities entirely.
4. Whatever is chosen, the **first backup afterwards** should run with auto-compact disabled and
   retention temporarily removed, so a database that is subtly wrong cannot delete archive data.
5. **Then do a restore drill** — one small file from one restore point. 21 versions have accumulated
   and none has ever been restored. Nothing here is proven until one is.

---

## 9. Still open

- **Why is `Backup.DBPath` wrong?** Only the resulting state and its 68-minute window are known.
- **Was the Jul-13 deletion retention, or damage?** §5. `list-broken-files` answers it.
- **The root `duplicati-server` on :8200** — its `yamaguchi` job has never completed a backup, it runs
  privileged, and its config is unreadable without sudo. Candidate for **removal**, not migration.
  Owner wants Duplicati on a dedicated system user; note the real job runs in a **user-session**
  instance that dies with the session — plausibly why a 42-day outage went unnoticed.
- **The 50 MB skip** — excludes ~121 GB across 74 files (~88 % of `Juniper/` by volume, measured
  2026-08-22; recount, this tree changes daily) **and all three archived job databases** (2.26 /
  11.51 / 13.17 GB). Recovery files too large to be included in the recovery. Needs to become an
  explicit decision; the useful axis is **regenerable vs irreplaceable**, not file size.
- **Automating database backups** — Duplicati only snapshots both DBs **before schema migrations on
  version upgrade** (2023-06, 2025-08, 2026-07 — two complete server+job pairs plus one orphan). The
  owner's manual 18:19 copy was **not** automatic; an earlier claim of mine that it was is retracted.
  That copy is currently the only correct record of `DBPath`. The server DB is ~470 KB live and holds
  config, schedule, filters and encrypted credentials — cheap and disproportionately valuable.

---

## 10. Method note

**This handoff has NOT been through multi-agent validation** — written under context pressure at the
owner's instruction to prioritise completion. Every factual claim in §1, §2, §4, §5 and §7 was
verified directly by command; treat §9 as less certain.

The predecessor runbook *was* validated, and that is the only reason its false premise was caught
before execution. If time allows, validate this one before acting on §8.

**Recurring failure shape in this arc, stated plainly:** a correct mechanism paired with a wrong
consequence. It has now happened five times — the hyphen/setuptools claim, "coverage is fine",
"no backup script exists", "the job is orphaned", and "the archive is untouched". Every premise was
individually true. **Verify the conclusion separately from the premises.**
