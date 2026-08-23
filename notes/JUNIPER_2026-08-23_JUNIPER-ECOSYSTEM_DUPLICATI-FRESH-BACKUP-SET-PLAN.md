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

## 3. Destination — DECIDED, and explicitly temporary

### The intended architecture

This Duplicati job is **one tier of a three-tier posture**, and the tiering is by design, not
accident:

| tier | medium | cadence | role |
|---|---|---|---|
| **Duplicati `Ubuntu`** (this job) | a **physically separate on-host drive** | daily | fast, frequent, many restore points |
| full Juniper archives | external drive, **kept offline** | infrequent | air-gapped; survives host compromise/failure |
| project archives | USB drives | more frequent than the full archives | portable, per-project |

`/mnt/Backups/Ubuntu` (`/dev/sda1`, SATA) **is** the intended home for this tier and satisfies the
"physically separate on-host drive" requirement — `/home` is on `sdc`, so source and backup already
sit on different spindles.

### The temporary deviation

**`/media/pcalnon/temp_backups`** (`/dev/sdc4`, 1.9 TB, 1.8 TB free) is the destination **for now**,
because the existing archive occupies `sda1` and must stay readable while the five intact restore
points are the only recovery path. This is explicitly a short-lived arrangement: **return to
`/mnt/Backups/Ubuntu` as soon as practicable**, once the damaged restore points are purged and space
is reclaimed.

While it lasts, note that `sdc4` shares a physical disk with `/home` (`sdc3`), so it does **not**
satisfy the separate-spindle requirement. It protects against accidental deletion, per-partition
filesystem corruption and user error — not against failure of `sdc`. That is an accepted, bounded
risk for the duration, not a design position.

### Why not the USB drive — measured, not assumed

`sdb1` (WD My Passport) was considered and **rejected on measurement**:

| destination | transport | sequential read | full 181 GiB backup |
|---|---|---:|---:|
| `sdb1` My Passport | **USB 2.0** (480 Mbps link) | **39.4 MiB/s** | ~78 min |
| `sda1` intended tier | SATA | **116.6 MiB/s** | ~26 min |
| `sdc4` temp_backups | SATA | **240.6 MiB/s** | ~13 min |

~3× slower than the intended drive and ~6× slower than the interim one — a real slowdown, so the
"reevaluate if insignificant" test fails. It is also already committed to a different tier.

> **Separate actionable finding.** The My Passport is attached *through a hub on a USB 2.0
> controller* (`usb3/3-1/3-1.4`, 480 Mbps) while this host has four faster controllers idle —
> `usb2`/`usb4`/`usb6` at 10000 Mbps and `usb8` at 5000 Mbps. The 25E2 is a USB 3.0 model, so this is
> a port/hub choice rather than a device limit. Relocating it, and the project-archive USB drives, to
> a direct USB 3 port should yield roughly 5–10× — which matters for the external-archive tiers even
> though it does not change this job's destination.

## 4. Settings for the fresh job

Each line encodes a specific defect observed in the existing job, and each number is derived from the
measurements in §2/§5 rather than a rule of thumb.

| setting | recommended | why |
|---|---|---|
| `--blocksize` | **1 MB — i.e. leave it at the current default** | **Irreversible: "cannot be changed after remote files are created"** (verified in `duplicati-cli help advanced` on 2.3.0.4). The existing job runs at **100 KB**, a stale default from when it was created; 2.3.0.4's default is now **1 MB**. Recreate cost tracks *total block count* (data ÷ blocksize), which is why 100 KB produced 28.5 M blocks, a 13 GB database and a 49-day Recreate. Simply accepting today's default is a **10x** block-count reduction. At 181 GiB with ~1.2 M files (mean ≈156 KB) most files are a single block either way, so sub-file dedup loses little. **An earlier revision of this plan recommended 500 KB — that was wrong**: it is *below* the current default and would have given only a 5x reduction while carrying a justification burden the default does not. Verify the effective value when creating the job rather than assuming it inherits. |
| `--dblock-size` | **500 MB** (currently 1 GB) | Duplicati's docs: larger volumes mean *"data corruption destroys the entire volume, instead of just a few chunks"* — precisely the granularity at which 1,208 volumes were just lost. 500 MB stays inside the documented 500–2000 MiB local-destination band, halves per-volume blast radius, and makes targeted restores cheaper. **Changeable later**, unlike blocksize. |
| `--skip-files-larger-than` | **2 GB** (currently 50 MB) | With the §5 exclusions in place this drops only 8 files / 24 GiB, while *keeping* ~30 GiB of `~/.local/state/juniper-experiments/` logs that are **not reproducible** (seeded runs do not reproduce, cascor#532). Today's 50 MB cap silently discards them. |
| `--no-auto-compact` | **`true`** initially | An interrupted compact is what destroyed the existing archive. Do not enable until a restore has been proven. |
| retention policy | **none** initially, then generous | Retention is what marked the intermediate filesets expendable. Add only once restores are proven. **The restricted file set changes the arithmetic in our favour**: at ~181 GiB per full version instead of the ~1.29 TiB the old job scanned, the same 3.6 TB drive holds far more restore points, so retention can be materially more generous than `1W:1D,1M:1W,6M:1M,20Y:1Y` once the set is proven. |
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

**On ISOs specifically** — and there are **two different sets of twelve**, which is an easy trap:

| set | where | count | total | mean | in the backup's scope? |
|---|---|---:|---:|---:|---|
| measured by `util/ad-hoc/average_iso_size.bash` | `~/Downloads/` | 12 | 53.65 GiB | **4.47 GiB** | **NO — `%HOME%/Downloads/` is already exclusion #29** |
| measured by `duplicati_size_histogram.py` | rest of `$HOME` | 12 | 68.55 GiB | 5.71 GiB | **yes** |

Both counts are 12 by coincidence. The `~/Downloads` set (the source of the observed 1.7–7.9 GB
range and 4.5 GB mean) is **already excluded** and therefore does not bear on the cap at all. The set
that does is the in-scope one, and **ten of its twelve live inside `VirtualMachines/`**:

```
4 x Win11_25H2_English_x64_v2.iso   @ 7.89 GiB   = 31.56 GiB
4 x Win10_21H2_English_x64.iso      @ 5.48 GiB   = 21.92 GiB
1 x ubuntu-24.10-desktop-amd64.iso  @ 5.28 GiB
1 x ubuntu-23.04-desktop-amd64.iso  @ 4.59 GiB
```

Note that **53.5 GiB of that 63.35 GiB is duplicate copies of just two ISOs**, replicated across VM
directories. Duplicati's block-level dedup would collapse them to ~13.4 GiB if they were backed up,
so the cap's headline "68 GiB of ISOs" overstates what they would actually cost. It is still the
right call to exclude them — they are re-downloadable — but the exclusion should be justified by
*identity*, not by the raw figure.

**Conclusion unchanged**: exclude ISOs as a **consequence** of excluding `VirtualMachines/`, not as a
separate size rule. No ISO-specific filter is needed.

> **Note on the measuring script.** `average_iso_size.bash` produces a correct mean for this dataset
> (4.53 vs an exact 4.47 GiB — the gap is `du -sh` rounding to one decimal). Two latent defects are
> worth knowing before it is reused: it parses `du -sh` output with `tr -d "G."`, so a file ≥ 10 GB
> prints as e.g. `12G`, strips to `12`, and is counted as **1.2 GiB — a 10x undercount**; and a file
> under 1 GB prints as e.g. `700M`, which survives the `tr` and makes `bc` fail. Neither fires here
> because every file in `~/Downloads` happens to fall between 1.6 and 7.9 GiB.

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
- [ ] **The destination has been migrated back to `/mnt/Backups/Ubuntu`** and a full
      backup plus a restore drill have both passed there. The interim location is not the
      finished state; the tier is specified to live on a physically separate on-host
      drive, and it is not done until it does.

---

## 8. Open decisions

| # | decision | status |
|---|---|---|
| 1 | Destination | **SETTLED** — `/media/pcalnon/temp_backups` interim, return to `/mnt/Backups/Ubuntu` as soon as practicable (§3). `sdb1` rejected on measurement. |
| 2 | Purge the five damaged restore points | **UNBLOCKED** — the restore drill confirmed the 2026-07 points are unrecoverable and 2025-11-12 is intact. `list-broken-files` first, then `purge-broken-files --dry-run`. |
| 3 | `--blocksize` | Recommended **1 MB = the current default** (§4). **Irreversible once the first backup runs.** (A previous revision said 500 KB; corrected — that was below the default.) |
| 4 | `--dblock-size` | Recommended **500 MB** (§4). Changeable later. |
| 5 | Size cap + exclusions | Recommended **2 GB** plus six path exclusions (§5). Inventory done. |
| 6 | Same passphrase or new | Owner. Whichever is chosen, record it somewhere recoverable that is **not inside the backup** — today it exists only as an `enc-v1:` blob in the server database. |
| 7 | Retention policy | Deferred until restores are proven; then materially more generous than before, since ~181 GiB versions fit far more restore points on the same drive. |

---

## 9. Sequence back to the intended architecture

1. `list-broken-files` (read-only) → confirm exactly what is unrecoverable.
2. `purge-broken-files --dry-run` → verify it proposes touching **none** of the five intact restore
   points. Abort if it does.
3. Apply the purge, reclaiming the space the damaged 2026-07 points occupy on `sda1`.
4. Stand up the fresh job at `/media/pcalnon/temp_backups` with the §4/§5 settings; full backup and
   restore drill must both pass.
5. Once a current second copy exists and `sda1` has room, **migrate the destination back to
   `/mnt/Backups/Ubuntu`** and re-run the acceptance checks there.
6. Retire `/media/pcalnon/temp_backups` as a backup destination.

---

## 10. Document history

This plan was restructured twice on 2026-08-23, which is why several headings in its history no
longer exist. Recorded here so the sequence-safety docs screen's findings can be audited rather than
merely waived:

| former heading | what happened to it |
|---|---|
| `### Option A/B/C` (destination options) | Superseded once the owner clarified the **three-tier architecture**: `/mnt/Backups/Ubuntu` is the *specified* home for this tier, so the destination stopped being an open A/B/C choice. Option B's substance (purge to reclaim space) survives in §2, §8 row 2 and §9 steps 2–3, including the `--dry-run`-first warning. Option C's (off-machine) survives as the *existing* offline external-archive tier in §3's table. |
| `## 4. Settings for the fresh job` | Same heading, body replaced wholesale when every value was re-derived from measurement. |
| `## 5. The 50 MB skip must become an explicit decision` | Renamed to **§5 Replace the size cap with path exclusions** and expanded ~3x, once measurement showed the cap is the wrong instrument. |

Nothing was dropped; each former section's content is traceable to a current one.
