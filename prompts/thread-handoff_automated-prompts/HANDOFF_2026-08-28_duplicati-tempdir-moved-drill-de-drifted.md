# HANDOFF 2026-08-28 — Duplicati: the scheduled path is proven, `--tempdir` moved, the drill de-drifted; the tail is the old-archive purge

Continue the backup arc. Predecessor:
[`HANDOFF_2026-08-26_duplicati-migrated-to-sda1-criterion-6-closed.md`](HANDOFF_2026-08-26_duplicati-migrated-to-sda1-criterion-6-closed.md)
— its §2 traps and inherited prohibitions remain binding and are NOT restated. Read it, then
the note's new [§8.14](../../notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md).

> ⚠️ Two things the predecessor said are now **wrong**: `--tempdir` is no longer on sdc4, and
> "under 10 minutes" is not a floor. Both corrected below.

## 0. Settled this session — do not redo

| item | outcome |
|---|---|
| **#1425** | **MERGED** `6be74167` 04:25Z, via auto-merge Paul armed 08-27 00:15Z |
| **#1433** | **OPEN, CI GREEN 17/17.** The §8.14 work. Needs Paul's explicit merge word — a handoff cannot carry it |
| **`--tempdir`** (§8.13.3) | **CLOSED.** Moved sdc4 → `/home/pcalnon/.cache/duplicati-tmp`. `PUT 200`, 9/9 post-checks. **Proven in flight**: 08-28 run wrote 10 `dup-*` there, 0 in the old dir |
| **196 GB sdc4 copy** | Paul: **KEEP**. Frozen at 811 volumes, second decrypt-validated copy on another disk |
| Criterion 6 | now has **scheduled-path** proof, not just the hand-started proof run |
| Criterion 4 | watchdog timer fired **unattended** for the first time 08-27 12:00:04 CDT, `OK` |
| Three stale-path tools | fixed: `duplicati_drill_fresh.py`, `duplicati_dlist_query.py`, `yamaguchi_build_job.py` |
| New tool | `util/ad-hoc/yamaguchi_edit_setting.py` — third live-config editor (target / sources / **settings**) |

**Two scheduled runs from sda1**, both Success, both `TestResults: Success on 3 file(s)`, 0 errors:

| | 08-27 | 08-28 |
|---|---|---|
| Duration | 9 m 03 s | **10 m 27 s** |
| Added files | 429 | **18,151** (42×) |
| Census | 815 / 210,590,946,931 B AGREE | **818 / 210,901,216,426 B AGREE** |

**The real class is ~9–10.5 min, scan-bound** (786 k files + a ~587 MB verification download);
42× the churn cost ~1.5 min. 4 dlists is correct, not drift — `1W:1D` keeps one per day and
08-25…08-28 are four days inside the window.

## 1. Open — all root or Paul's call

1. **Old-archive purge — this is now the gating decision.** Paul's stated mid-term goal is
   consolidating backups onto sda1. sda1 is at **74 % / 909 G free** with the old `.gpg` archive
   still at its root. That purge, not the sdc4 copy, is what gates consolidation. It also
   unblocks Tier 3 (`_drill_scratch/`, 35 GB).
2. **Criterion 5 (reboot)** — the last unexercised criterion, and now *cleaner*: with `--tempdir`
   on `/home`, every path the job depends on is fstab-managed. After the next reboot check
   `duplicati.service` active, job 2 + `ProposedSchedule`, `yamaguchi_destination_durability_check.bash`,
   `loginctl show-user pcalnon -p Linger` = yes, `systemctl --user is-enabled yamaguchi-watchdog.timer`.
3. **Old sdc4 `_duplicati_tmp/`** — now *provably* unused; removable whenever.
4. **Drill `restored/` tree** (~64 G) — unchanged; keep `results.json` / `drill-meta.json` / `provenance.txt`.
5. Loopback restage, server-brain backup — root, unchanged by the predecessor's precise reference.

## 2. Traps added

- **`os.path.ismount()` is not a durability check.** Deriving the drill's mount guard the way
  #1425 did for census, a `--run-root` under `/tmp` **passed** and the drill began restoring into
  **tmpfs**; 1.5 GB was RAM-resident before the kill. tmpfs/ramfs/devtmpfs/squashfs/overlay all
  satisfy `ismount()`. Now refused from `/proc/mounts`.
- **The drill's orphaned `duplicati-cli` child does not die with its parent.** `pkill -f <driver>`
  leaves it running — kill it separately.
- **When you replace one guard covering two things, count the things.** The old single hardcoded
  guard covered the run-root only by coincidence; deriving the dest guard alone silently dropped it.
- **A hazard comment does not protect the line beneath it.** The drill's stale `--dest` default sat
  directly under a comment warning about exactly that failure.
- **A refused run must leave no trace.** `build_job` wrote its provenance record *before* its
  guards, so the first dry run — which then correctly refused — overwrote the 2026-08-25 import
  record. Recovered from the sda1 `_yamaguchi_records/` mirror: **the first time in this arc that
  mirror was used rather than merely maintained.**
- **Duplicati setting names start with `--`**, so argparse needs `--name=--tempdir`, not `--name --tempdir`.
- **`/home` (sdc3) and `/media/pcalnon/temp_backups` (sdc4) are the same physical disk** (`sdc`).
  The tempdir move buys fstab durability, not spindle separation; only `/` (NVMe) would.

## 3. Verify starting state (one per call)

```bash
git fetch origin && git status -sb
python3 util/ad-hoc/yamaguchi_census.py --runs 2          # target=/mnt/Backups/Ubuntu/Yamaguchi, literal "-> AGREE"
bash util/ad-hoc/yamaguchi_destination_durability_check.bash   # sda1 DURABLE; sdc4 NOT DURABLE
python3 util/ad-hoc/yamaguchi_server_api.py status        # job 2; ActiveTask null; --tempdir under ~/.cache
cat ~/.local/state/duplicati/server-watchdog.status       # OK
bash util/ad-hoc/yamaguchi_retire_tier2.bash              # 5 gates PASS, dry run
grep -rn 'temp_backups/Yamaguchi' util/ad-hoc/            # ONLY migrate_copy SRC, retire_tier2 OLD_DEST, patch_census anchor
```

The drill and `dlist_query` now **require** `--dest` — a bare run is refused by design, not broken.

## 4. Git / session state

Branch `fix/yamaguchi-stale-path-tools-and-tempdir` from main `99df9bf0`, in worktree
`.claude/worktrees/calm-scribbling-origami`, session "duplicati closeout". Two GPG-signed
commits: `13cfb236` (the three tools + `yamaguchi_edit_setting.py` + §8.14) and `105875c4` (the
08-28 run, the in-flight tempdir proof, and the timing correction). Pushed; **PR #1433 open, CI
green, unmerged.** Main has since moved to `80cefb44` (#1434, #1435) — neither touches these
files. Evidence: `_yamaguchi_check/yamaguchi-config-post-tempdir-move-20260828.json`; the
records mirror on sda1 has NOT been re-synced since (run `yamaguchi_records_sync.bash`). Memory
updated: `project_duplicati_gpg_flush_mechanism_2026-08-24`,
`reference_vacuous_pass_check_class` (instance 15 + class-13 recurrence), both MEMORY.md lines.
