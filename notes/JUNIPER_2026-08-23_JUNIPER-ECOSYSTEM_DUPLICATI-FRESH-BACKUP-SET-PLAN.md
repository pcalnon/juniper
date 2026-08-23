# Fresh backup set — design and open decisions

**Project**: Juniper (workstation backup infrastructure)
**Author**: Paul Calnon
**Date**: 2026-08-23
**Status**: Destination CHOSEN (`/media/pcalnon/temp_backups`, temporary); settings recommended from measured data
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

## 2. Space: a fresh set fits comfortably

Measured 2026-08-23 by `util/ad-hoc/duplicati_source_measure.py`, which reads the source root, the
37 exclusions and the size cap directly from the live server database so the measurement cannot drift
from the real job configuration.

| quantity | value |
|---|---:|
| **what the job would actually store** | **181.31 GiB** / 1,216,061 files |
| dropped by the `50MB` cap | 1.46 TiB / 1,443 files (**89.2 %** of eligible data) |
| pruned by the 37 path exclusions | 1.19 TiB / 4,235,032 files |
| destination free space | 1.1 TB |
| destination total | 3.6 TB (2.4 TB used by the existing archive) |
| `/home` free | 1.5 TB (not a valid destination — same physical disk as the source) |

> **Correction.** An earlier reading of this arc took the server database's cached
> `SourceFilesSize` = **1.29 TiB** as the size of a fresh backup and concluded that one would not fit
> in the 1.1 TB free. That was wrong. `SourceFilesSize` counts the **scanned** tree *before* the
> 50 MB cap is applied; what actually gets stored is 181 GiB. A fresh full set fits with well over
> a terabyte to spare, and the destination decision in §3 is therefore **not** forced by capacity.

This changes the shape of the decision. Option A (new storage) is no longer required to make a fresh
set possible — it is now purely a question of whether both copies should continue to live in the same
machine. Option B (purging the damaged restore points to reclaim space) is **no longer needed at all**
as a funding mechanism, and should be judged on its own merits.

The existing archive still cannot be discarded: its five intact restore points (2024-03-04,
2024-06-03, 2025-08-31, 2025-10-06, 2025-11-12) are currently the only recovery path that exists.

> Two measurement caveats. The three figures above sum to more than `df` reports for `/home`, because
> they are **apparent** sizes (`st_size`) and the VM disk images are sparse — apparent size exceeds
> blocks actually allocated. And the tree is live: two runs minutes apart differed by 17 files. Treat
> 181 GiB as accurate to a few hundred MiB, which is far inside the margin that matters here.

---

## 3. Destination — DECIDED

**`/media/pcalnon/temp_backups`** (owner decision, 2026-08-23). 1.9 TB filesystem, 1.8 TB free,
currently empty. Explicitly **temporary**: once normal operation is restored and unneeded files are
removed, the destination returns to `/mnt/Backups/Ubuntu`.

> ⚠ **Shared failure domain.** `/media/pcalnon/temp_backups` is `/dev/sdc4`; `/home` is `/dev/sdc3`.
> **Same physical disk** (WDC WD8002FZWX, 7.3 TB). The archive it temporarily replaces lives on
> `/dev/sda1` — a *different* disk. So this arrangement protects against accidental deletion,
> filesystem corruption of one partition and user error, but **not against failure of `sdc`**, which
> would take the source and the backup together.
>
> Alternatives on a different spindle, all large enough for the 181 GiB set, if a separate failure
> domain is wanted later: `sdb1` (1.6 TB free, mounted), `sdb2` (1.6 TB, unformatted),
> `nvme0n1p2` (651 GB free). Accepted knowingly as a temporary posture.

### Other options considered

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

- **No longer needed to fund the fresh set** — §2 shows there is no capacity shortfall. Judge this
  purely on whether reclaiming the space is worth the risk.
- **Unknown**: how much it actually frees. Blocks are shared across filesets, so volumes referenced
  by the surviving 2024/2025 points are untouched. Measure before choosing.
- **Risk**: `purge-broken-files` deletes from the database *and* remote storage. Always `--dry-run`
  first, and abort if it proposes touching any of the five intact restore points.
- **Note**: this is worth doing eventually regardless — the damaged points consume space and offer
  nothing — but it is a poor way to fund the fresh set, because it spends the safety margin of the
  only archive that currently exists.

### Option C — remote / off-machine destination

Addresses the single-machine exposure at the same time. At **181 GiB** the first copy is far more
tractable over a home uplink than the cached 1.29 TiB figure suggested — this option is materially
more attractive than it looked before the measurement.

---

## 4. Settings for the fresh job

Each line encodes a specific defect observed in the existing job, and each number is derived from the
measurements in §2/§5 rather than a rule of thumb.

| setting | recommended | why |
|---|---|---|
| `--blocksize` | **500 KB** (default 100 KB) | **Irreversible — cannot be changed after the first backup.** Recreate cost tracks *total block count* (data ÷ blocksize), which is why 100 KB across this archive's history produced 28.5 M blocks, a 13 GB database and a 49-day Recreate. At 181 GiB across ~1.2 M files (mean ≈156 KB) most files are already 1–2 blocks, so sub-file dedup gains little; 500 KB cuts block count ≈5× for minimal dedup loss. Duplicati's docs advise evaluating carefully above 1 MB, so this stays inside sanctioned territory. |
| `--dblock-size` | **500 MB** (currently 1 GB) | Duplicati's docs: larger volumes mean *"data corruption destroys the entire volume, instead of just a few chunks"* — precisely the granularity at which 1,208 volumes were just lost. 500 MB stays inside the documented 500–2000 MiB local-destination band, halves per-volume blast radius, and makes targeted restores cheaper. **Changeable later**, unlike blocksize. |
| `--skip-files-larger-than` | **2 GB** (currently 50 MB) | With the §5 exclusions in place this drops only 8 files / 24 GiB, while *keeping* ~30 GiB of `~/.local/state/juniper-experiments/` logs that are **not reproducible** (seeded runs do not reproduce, cascor#532). Today's 50 MB cap silently discards them. |
| `--no-auto-compact` | **`true`** initially | An interrupted compact is what destroyed the existing archive. Do not enable until a restore has been proven. |
| retention policy | **none** initially | Retention is what marked the intermediate filesets expendable. Add only once restores are proven and space is understood. |
| `--allow-missing-source` | `true` | Keep; harmless, avoids spurious failures. |
| encryption | gpg, passphrase **recorded outside the backup** | The passphrase exists today only as an `enc-v1:` blob in the server database. If that database is lost with the machine, the archive is unrecoverable. |

## 5. Replace the size cap with path exclusions

Measured 2026-08-23 across the whole source (`util/ad-hoc/duplicati_size_histogram.py`). The
published guidance converges on the same conclusion the data shows — exclude by **identity**, not by
threshold. Veeam's file-exclusion guidance is explicit: *"move VMs and other large files to a separate
volume, and add the whole volume to the exclude list."*

**Add these six path exclusions:**

| exclusion | reclaims | class |
|---|---:|---|
| `%HOME%/.local/share/Steam/` + `%HOME%/snap/steam/` | ~750 GiB | re-downloadable |
| `%HOME%/StarfieldData/` | ~118 GiB | re-downloadable game data |
| `%HOME%/VirtualMachines/` | ~290 GiB | VM images — **also removes 10 of the 12 ISOs** |
| `%HOME%/.config/Duplicati/` | ~63 GiB | the backup's own databases (regenerable indexes) |
| `%HOME%/Development/python/Juniper/juniper-data/data/` | ~95 GiB | re-fetchable datasets (COCO, ImageNet) |

**Effect on the cap decision** — eligible data falls from 1.64 TiB to **184.63 GiB**, and the long
tail collapses:

| cap | files above | bytes above | with the six exclusions |
|---|---:|---:|---:|
| 50 MB | 1,443 → **316** | 1.46 TiB → **100.81 GiB** | |
| 1 GB | 233 → **14** | 1.18 TiB → **32.22 GiB** | |
| 2 GB | 154 → **8** | 1.08 TiB → **24.32 GiB** | recommended |
| 4 GB | 51 → **1** | 728.98 GiB → **4.38 GiB** | |
| 8 GB | 27 → **0** | 587.82 GiB → **0 B** | |

**On ISOs specifically** (the owner's question): 12 ISOs above 50 MB, 68.55 GiB, mean **5.71 GiB** —
consistent with the observed 1.7–7.9 GB range. Ten of them live *inside* `VirtualMachines/`, so
excluding that one path removes them without needing an ISO-specific rule; only 2 (5.20 GiB) remain
elsewhere. Exclude ISOs as a **consequence** of excluding the VM tree, not as a separate size rule.

**Why the cap must stop being load-bearing.** Today it is the only thing deciding what survives, and
it decides purely on size. That is how four irreplaceable `.vdi` images (289.85 GiB of state that
exists nowhere else) and ~30 GiB of non-reproducible experiment logs came to be silently unprotected,
while 750 GiB of trivially re-downloadable game payloads were excluded for the same reason. With path
exclusions carrying the policy, the cap becomes a backstop and can sit well above anything
irreplaceable.

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
| 1 | Destination — A, B or C | owner (§2 re-measurement is **done**; capacity no longer forces the answer) |
| 2 | Whether to purge the five damaged restore points | owner — no longer needed to fund the fresh set |
| 3 | `dblock-size` for the new set | owner's tolerance for recovery time vs storage overhead |
| 4 | Replacement for the 50 MB skip | owner (inventory is **done** — see §5) |
| 5 | Same passphrase or new | owner |
