# Duplicati database restore — operational runbook

**Project**: Juniper — backup & restore systematization
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-22

**Status**: RUNBOOK — prepared, **not executed**. Nothing in this document has been run. It exists so
the decision can be made with the steps in front of you rather than improvised against live backup
infrastructure.

**Context**: the `Ubuntu` Duplicati job wedged on 2026-07-13 and a database **Recreate** was started
2026-08-21 ~18:20 to clear it. After 21 hours the Recreate had read ~4 % of the archive, was
downloading `dblock` volumes rather than the `dindex` volumes it should need, and its database had
grown **21 MB in twelve hours**. Every rate estimate lands in weeks. This runbook is the alternative.

---

## 0. The one thing that must stay true

**Nothing in this runbook modifies the backup archive.** Every step operates on the *local database*,
which is a rebuildable index of `/mnt/Backups/Ubuntu` — not the backup itself.

Verified before writing: destination holds **10 restore points, 2.4 TB, unchanged** throughout the
incident and the 21-hour Recreate.

The single exception is §4's `purge-broken-files`, which **does** delete from remote storage. It is
quarantined in its own section, gated behind a `--dry-run`, and is not part of the restore.

---

## 1. Why the Jul 12 backup is the right recovery point

Duplicati keeps automatic pre-upgrade copies of both databases. The relevant one:

| file | size | taken |
|---|---|---|
| `backup SJTCQIIZSJ 20260712033545.sqlite` | **13.17 GB** | 2026-07-12 15:35 |
| `backup Duplicati-server 20260712030517.sqlite` | 180 KB | 2026-07-12 15:03 |

Place it on the incident timeline:

| when | event |
|---|---|
| 2026-07-09 14:23 | **last successful backup** |
| 2026-07-11 | newest `dlist` on the destination (restore point #21) |
| **2026-07-12 15:35** | **← this database backup** |
| 2026-07-12 16:31 | `BackendQuotaNear` — 4 KiB free |
| 2026-07-13 07:36 | strict-mode wedge; job dead from here |

It postdates the last good backup and **predates every failure by roughly an hour**. That is the
database as it was when things were still healthy.

⚠ **Caveat worth knowing before you start.** These copies are made *before a schema migration*, and
2.3.0.4 was released 2026-07-09 — three days earlier. So this file is most likely in the **pre-2.3.0.4
schema**, and Duplicati will migrate it on first load. That is a supported path and it is what the
backup exists for, but it means the first startup after the restore may be slow and will itself
write a fresh `backup …` copy. Do not interrupt it.

---

## 2. Restore procedure

Times are indicative. Steps 1–4 are reversible; §6 is the rollback.

### Step 1 — stop the Recreate and the instance that owns it

The Recreate is a foreground operation inside the running Duplicati. Cancel it in the UI first
(**Home → `Ubuntu` → the running task → Cancel/Abort**), and wait for the process to settle before
stopping anything, so SQLite closes its WAL cleanly.

```bash
pgrep -x duplicati                      # expect one pid (the :8300 user instance)
# after the UI reports the task cancelled:
kill "$(pgrep -x duplicati | head -1)"  # TERM, not KILL -- let it checkpoint
sleep 10
pgrep -x duplicati || echo "stopped"
```

**Do not `kill -9`.** An abrupt kill mid-WAL leaves the half-built database in a state that makes the
next startup try to recover it, which is exactly what you are trying to walk away from.

### Step 2 — preserve, do not delete

```bash
cd /home/pcalnon/.config/Duplicati
mv SJTCQIIZSJ.sqlite      SJTCQIIZSJ.sqlite.recreate-abandoned-20260822
mv SJTCQIIZSJ.sqlite-wal  SJTCQIIZSJ.sqlite-wal.recreate-abandoned-20260822  2>/dev/null
mv SJTCQIIZSJ.sqlite-shm  SJTCQIIZSJ.sqlite-shm.recreate-abandoned-20260822  2>/dev/null
```

Renamed, not removed. ~20 GB, and it is the only artefact of 21 hours of work. Delete it once a backup
has succeeded, not before.

### Step 3 — put the Jul 12 database in place

**Copy, never move.** The archived backup is the fallback; if the copy is interrupted you still want
the original intact.

```bash
cp -v "backup SJTCQIIZSJ 20260712033545.sqlite" SJTCQIIZSJ.sqlite
ls -la SJTCQIIZSJ.sqlite          # expect ~13.17 GB
```

Confirm it is a readable SQLite database before starting Duplicati:

```bash
python3 -c "
import sqlite3
c = sqlite3.connect('file:SJTCQIIZSJ.sqlite?mode=ro', uri=True)
print('tables:', len(list(c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"))))
print('remote volumes:', list(c.execute('SELECT COUNT(*) FROM RemoteVolume'))[0][0])
print('by state:', list(c.execute('SELECT State, COUNT(*) FROM RemoteVolume GROUP BY State')))"
```

**What you are looking for**: a `RemoteVolume` count in the thousands (the destination holds 2,674
`dblock` + 2,682 `dindex` + 10 `dlist` = 5,366 files), and — the point of the whole exercise — whether
anything is still in `Uploading` state. If the Jul 12 snapshot predates the wedge, it should not be.

### Step 4 — start Duplicati and let it migrate

Start it the way it normally starts (tray icon / your usual launcher, listening on **:8300**). First
startup will migrate the schema and may take a while. Watch for it settling:

```bash
ls -la /home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite*   # WAL activity = migrating
pgrep -x duplicati
```

### Step 5 — verify before trusting

In the UI: **Home → `Ubuntu`** should show **21 versions**, source ~1.29 TiB, last backup 2026-07-09.
If the version count is right, the database matches the archive.

Then, and only then, run a backup. Expect it to be long — six weeks of delta.

---

## 3. `list-broken-files` — how to actually reach it

This was the unclear part, and the answer is that **you do not need to assemble a CLI invocation at
all**.

### Route A — the UI's built-in Commandline (recommended)

Duplicati ships a commandline runner in the web UI that **pre-fills the target URL, passphrase,
encryption module and `--dbpath` from the job's own configuration**:

```
http://127.0.0.1:8300/ngclient/backup/2/commandline
```

(`2` is the `Ubuntu` job id, as seen in the other job URLs — `…/ngclient/backup/2/general`.)

Pick the command from the dropdown, change nothing else, run. This is strongly preferred because the
GPG passphrase and `TargetURL` are stored `enc-v1:`-encrypted in the server database — with this route
you never have to extract or retype them.

### Route B — the CLI, if you need it outside the UI

```bash
export PASSPHRASE='<the backup passphrase>'      # NEVER pass --passphrase on the command line
duplicati-cli list-broken-files "file:///mnt/Backups/Ubuntu" \
    --dbpath=/home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite \
    --encryption-module=gpg
```

Duplicati explicitly documents the environment-variable route: *"You can provide the encryption
passphrase … from the commandline, but this will make them visible to other users on the system that
can list processes. You can instead use the environment variables: `PASSPHRASE` …"*.
`--parameters-file` is the third option if you would rather it not be in the environment either.

**`--dbpath` matters.** Without it the CLI builds its own database from scratch — which is the 21-day
operation you are escaping.

### What the output means

`list-broken-files` is **read-only**. It reports file *versions* that cannot be restored because the
remote volumes holding their blocks are missing. Expected outcomes here:

- **Nothing broken** — the stale `Uploading` record was the only problem; it is gone with the restored
  database. Proceed to a normal backup.
- **Some versions broken** — they will be from the 07-12/13 failed runs, not from the 21 good restore
  points. §4 then applies.

---

## 4. `purge-broken-files` — destructive, read this first

> *"Removes all files from the database **and remote storage** that are no longer restoreable. Use this
> operation with caution."*

This is the only step in this document that touches the archive. Always dry-run:

```bash
duplicati-cli purge-broken-files "file:///mnt/Backups/Ubuntu" \
    --dbpath=/home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite \
    --encryption-module=gpg --dry-run
```

Read the list. Only if it contains solely versions from the failed 07-12/13 window should it be
applied without `--dry-run`. If it proposes removing anything from the 21 established restore points,
**stop** — that means the restored database disagrees with the archive, and the right move is to go
back to §6 rather than to delete backup data.

---

## 5. If the restored database does not match the archive

Symptoms: wrong version count in the UI, or `list-broken-files` implicating good restore points.

Options, in increasing cost:

1. Try the **2025-08-31 copy** (`backup SJTCQIIZSJ 20250831055322.sqlite`, 11.51 GB). Older, but
   Duplicati can carry a database forward from an older state.
2. Re-run **Recreate**, accepting the multi-week cost — but first investigate *why* it took the
   `dblock` path when 2,682 `dindex` files exist, because that is the actual defect and it will
   recur.
3. **Start a new backup set** to a new destination folder, keeping the existing archive read-only for
   restores. Costs a full initial backup; guarantees a clean state.

---

## 6. Rollback

Nothing above is one-way. To return to exactly the pre-restore state:

```bash
kill "$(pgrep -x duplicati | head -1)"; sleep 10
cd /home/pcalnon/.config/Duplicati
mv SJTCQIIZSJ.sqlite SJTCQIIZSJ.sqlite.jul12-attempt
mv SJTCQIIZSJ.sqlite.recreate-abandoned-20260822 SJTCQIIZSJ.sqlite
mv SJTCQIIZSJ.sqlite-wal.recreate-abandoned-20260822 SJTCQIIZSJ.sqlite-wal  2>/dev/null
mv SJTCQIIZSJ.sqlite-shm.recreate-abandoned-20260822 SJTCQIIZSJ.sqlite-shm  2>/dev/null
```

The abandoned Recreate cannot be *resumed* — restoring it returns you to a half-built database, not to
a running rebuild. Its value is forensic.

---

## 7. Two things this incident surfaced

### 7.1 Automating the database backups — yes, and here is the actual gap

**Correction to an earlier claim of mine: Duplicati did *not* make `Duplicati-server_2026-08-21.sqlite`
automatically. The owner made it by hand.** I described it as automatic behaviour; that was wrong.

What Duplicati *does* do automatically is narrower, and the file naming shows it. The auto-generated
copies come in **server + job pairs** taken minutes apart:

| pair | server DB | job DB |
|---|---|---|
| 2023-06-13 | *(pruned)* | `backup SJTCQIIZSJ 20230613095835.sqlite` |
| 2025-08-31 | `…20250831052019` | `…20250831055322` |
| 2026-07-12 | `…20260712030517` | `…20260712033545` |

Three pairs in three years — these are **pre-schema-migration** snapshots taken on version upgrade,
not scheduled protection. The manual copy uses a different naming convention entirely
(`Duplicati-server_2026-08-21.sqlite`) and has no job-DB partner, which is how you can tell them apart.

**So the gap is real**: between upgrades — a year or more — there is no database protection at all,
and this incident is precisely the case where a recent copy is worth having. The Jul 12 pair being
usable here is **luck**: a version upgrade happened to land a day before the failure.

Recommended shape (design decision, not done):

- A periodic copy of **both** databases, weekly or before any risky operation.
- ⚠ Cost is not trivial: the job DB is **13–17 GB**. Weekly retention of four copies is ~70 GB.
- The server DB is **180 KB** and holds the job configuration, schedule, filters and the `enc-v1:`
  encrypted passphrase/TargetURL. **It is cheap and disproportionately valuable — back it up often
  regardless of what is decided for the job DB.**
- Duplicati must be **stopped** for a consistent copy, or the copy taken via SQLite backup API rather
  than `cp`. A `cp` of a live WAL-mode database can capture a torn state.

### 7.2 The 50 MB file-size limit — it excludes the recovery aids

`--skip-files-larger-than = 50MB` on the `Ubuntu` job means **none of the archived job databases is
backed up** — they are 2.26 / 11.51 / 13.17 GB. Recovery files too large to be included in the
recovery. Same shape as the outage itself: a safety mechanism that silently does not apply.

It also excludes **117.16 GB of `Juniper/`** across 69 files (juniper-data 102.52, juniper-legacy
10.62, juniper-cascor 2.82, juniper-canopy 0.72, juniper-ml 0.48) — roughly 93 % of that tree by
volume.

Reconsideration is warranted, and the answer is probably **not** a single global threshold:

| candidate | note |
|---|---|
| Raise or remove the limit | Simplest. Adds ~117 GB to the set; destination has 1.1 TB free. Backup windows get much longer. |
| Keep the limit, add targeted includes | Exempt the Duplicati databases and anything else genuinely irreplaceable. More precise, more configuration. |
| Keep the limit, exclude deliberately | If `juniper-data` really is regenerable, excluding it is defensible — but it should be an **explicit recorded decision**, not an inherited setting. |

The distinction that matters is **regenerable vs irreplaceable**, not file size. A 50 MB threshold is a
proxy for "probably a build artefact" that happens to be wrong for both of this system's most
irreplaceable categories: model snapshots and database backups.

---

## 8. Open questions

- **Why did Recreate take the `dblock` path** when 2,682 `dindex` files are present? Unanswered, and
  it is the real defect — a future Recreate will do the same.
- **Is the Jul 12 database pre- or post-2.3.0.4 migration?** Inferred pre- from the release date
  (2026-07-09) and the pairing convention; not confirmed.
- **Should the root `duplicati-server` on :8200 be removed?** Its `yamaguchi` job has never completed
  a backup and it runs privileged.
- **Should the job move to a dedicated system user?** The owner wants this. Note the job currently
  runs in a *user-session* instance that dies with the session — plausibly why a 42-day outage went
  unnoticed.

---

## 9. Related

- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-21_backup-systematization-design-arc.md`
  — the arc this belongs to (juniper-ml#1216, #1241).
- `util/juniper-backup.bash` — the external-media leg (juniper-ml#1221, #1223).
- `notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-STORAGE-CONVENTION-DESIGN.md` §2 — the C-1…C-6
  constraints this backup posture has to satisfy.
