# Fresh backup set — design and open decisions

**Project**: Juniper (workstation backup infrastructure)
**Author**: Paul Calnon
**Date**: 2026-08-23
**Status**: Design; destination decision NOT yet made
**Companion**: [`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md)

---

## 1. Why this is the top priority

Every 2026-07 restore point in the existing archive is damaged. The most recent restorable state is
**2025-11-12**. Everything changed on the workstation since then exists in exactly one place — the
live disk. A single disk failure loses nine months of work.

Repairing the existing archive does not address this. Deleted volumes cannot be resurrected, and the
in-flight Recreate — 49 days at its measured rate — produces only an accurate description of a
damaged archive.

**Getting a current second copy outranks every other item in this arc.**

---

## 2. The blocking constraint: there is not enough room

| quantity | value |
|---|---:|
| source size (last good measurement, 2026-07-09) | **1.29 TiB** / 1,160,303 files |
| destination free space | **1.1 TB** |
| destination total | 3.6 TB (2.4 TB used by the existing archive) |
| `/home` free | 1.5 TB (not a valid destination — same physical disk as the source) |

A fresh full backup does not fit alongside the existing archive, and the existing archive cannot
simply be discarded: its five intact restore points (2024-03-04, 2024-06-03, 2025-08-31, 2025-10-06,
2025-11-12) are currently the only recovery path that exists.

**The source figure needs re-measuring** — it is cached from 2026-07-09 and this tree changes daily.
That measurement is a prerequisite to choosing among the options below.

---

## 3. Destination options

### Option A — new physical storage (recommended)

Add a disk and target the fresh set at it. Leaves the existing archive fully intact and read-only for
restores. No trade-off against existing recovery capability.

- **Cost**: hardware.
- **Risk**: none to existing data.
- **Also fixes**: both copies currently live in the same machine; a separate disk is a prerequisite
  for any off-machine posture later.

### Option B — reclaim space by purging the damaged restore points

The five 2026-07 restore points are unrestorable. Purging them (`purge-broken-files`) would free the
volumes uniquely referenced by them.

- **Unknown**: how much this actually frees. Blocks are shared across filesets, so volumes referenced
  by the surviving 2024/2025 points are untouched. The recoverable amount must be **measured before
  this is chosen** — it may be far less than the ~200 GB shortfall.
- **Risk**: `purge-broken-files` deletes from the database *and* remote storage. Always `--dry-run`
  first, and abort if it proposes touching any of the five intact restore points.
- **Note**: this is worth doing eventually regardless — the damaged points consume space and offer
  nothing — but it is a poor way to fund the fresh set, because it spends the safety margin of the
  only archive that currently exists.

### Option C — remote / off-machine destination

Addresses the single-machine exposure at the same time. Slowest to first-copy over a home uplink for
1.29 TiB; consider seeding locally first.

---

## 4. Settings for the fresh job

Carried from the failure analysis — each line encodes a specific defect observed in the existing job.

| setting | value | why |
|---|---|---|
| `--no-auto-compact` | `true` (initially) | An interrupted compact is what destroyed the existing archive. Do not enable until the set is proven. |
| retention policy | **none** (initially) | Retention is what marked the intermediate filesets expendable. Add it only once restores are proven and space is understood. |
| `--skip-files-larger-than` | **revisit** | Currently 50 MB. See §5. |
| `dblock-size` | `1GB` → consider smaller | 1 GB volumes make Recreate cost ~23 min *per volume*. A smaller volume size trades storage overhead for dramatically cheaper recovery. This is the single biggest lever on "how long until I can restore". |
| `--allow-missing-source` | `true` | Keep; harmless and avoids spurious failures. |
| encryption | gpg, **same passphrase or a newly recorded one** | Whichever is chosen, record it somewhere recoverable that is not inside the backup. |

---

## 5. The 50 MB skip must become an explicit decision

`--skip-files-larger-than=50MB` currently excludes, among other things, **all three archived job
databases** (2.26 / 11.51 / 13.17 GB) — recovery files too large to be included in the recovery. It
also excluded roughly 121 GB across ~74 files as measured on 2026-08-22 (needs recount).

The useful axis is **regenerable vs irreplaceable**, not file size. A 4 GB `.venv` tarball is
regenerable; a 4 GB dataset or database is not. Recommended replacement: keep a size guard for
obviously-regenerable trees via path exclusions, and remove the blanket size cap, or raise it far
enough that nothing irreplaceable is silently dropped.

---

## 6. Structural fixes to land with the fresh set

These are the reasons the last failure went unnoticed for 42 days; a fresh set without them will fail
the same way.

1. **`loginctl enable-linger pcalnon`** plus a `systemd --user` unit, or a dedicated system user. The
   current job runs in a GNOME session (`app-gnome-duplicati-*.scope`) with `Linger=no`, so it dies
   at logout.
2. **Remove or repurpose the root `duplicati.service`** on port 8200. It runs privileged, its
   `yamaguchi` job has never completed a backup, and it is `Restart=always`.
3. **Alerting on failure.** `additional-report-url` is empty. A backup that silently stops is
   indistinguishable from one that works. This is the single highest-value item in this list.
4. **Back up the server database.** It is ~470 KB and holds config, schedule, filters and encrypted
   credentials. Duplicati only snapshots it automatically before schema migrations on version
   upgrade. A cron copy is cheap and disproportionately valuable.
5. **Correct the job description** — it says "Development and Documents folders"; the source is
   `%HOME%` entire with 37 exclusions.

---

## 7. Acceptance criteria

The fresh set is not "done" until:

- [ ] A full backup has completed successfully.
- [ ] A **restore drill** has recovered a real file to a scratch path and its checksum matches the
      original. The existing archive accumulated 10+ restore points and *none was ever restored* —
      which is why its damage went undetected for six weeks.
- [ ] A second restore drill from a *different* restore point succeeds after at least one incremental
      run.
- [ ] A failure notification has been observed firing (test it deliberately).
- [ ] The job survives a logout/login cycle and a reboot.

---

## 8. Open decisions

| # | decision | blocked on |
|---|---|---|
| 1 | Destination — A, B or C | owner; §2 re-measurement |
| 2 | Whether to purge the five damaged restore points | measurement of what it frees |
| 3 | `dblock-size` for the new set | owner's tolerance for recovery time vs storage overhead |
| 4 | Replacement for the 50 MB skip | inventory of what it currently excludes |
| 5 | Same passphrase or new | owner |
