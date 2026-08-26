# Duplicati Yamaguchi Backup — First Full Backup and Certification

**Project**: Juniper — Backup Infrastructure
**Author**: Paul Calnon (campaign executed by Claude Code session "backup sys work")
**Date**: 2026-08-25
**Status**: CERTIFIED — the arc's first complete, verified restore point. **Addendum §8 (2026-08-25 evening)**: the scope was widened the same afternoon (two VM images admitted, size cap removed); the widened fileset is re-certified there and §3/§7 are read as the 08:29 snapshot they were.
**Predecessors**: [`JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`](JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md) · [`JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-SET-CERTIFICATION.md`](JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-SET-CERTIFICATION.md)

---

## 1. Verdict

> **The Yamaguchi backup set is a complete, certified restore point.**
> First full backup: **Success** — 726,130 files / 201.1 GB examined and added
> (zero errors, zero skipped-as-too-large), 375 volumes / 98.1 GB uploaded with
> zero retries in 2 h 12 m, and the run **wrote its own dlist**
> (`IsFullBackup: True`) — the completeness marker no prior run in this arc
> ever produced. Certification: destination-only coverage
> **1,122,583 / 1,122,583 with zero surplus**, **375/375 volumes
> full-HMAC-valid**, and a stratified destination-only restore drill:
> **14/15 candidates verified outright** (13 live-oracle matches, 0
> contradictions, 40/187 dblocks exercised, including a 4.7 GB file spanning
> 21 volumes), with the 15th — a symlink — **proven correct and then restored
> with a live-oracle match** once the restore engine's partial-restore
> preconditions were met (§5).

Remaining plan-level criteria before the posture is fully closed (§7): a
second drill from a different fileset after an incremental, and reboot
survival of the schedule.

## 2. The topology change that made it possible

The 2026-08-25 discovery (Paul's diagnosis, mechanism pinned in-session): the
box had **two effective Duplicati installs** — the dpkg 2.3.0.4 base, and a
**stale autoupdater shadow install** (`~/.config/Duplicati/updates/` holding
2.0.7.1/2.0.8.1 with a `current` pointer) through which legacy entrypoints
resolved. The long-running profile server on 8300 (owning the old jobs) was a
2.0.8-era image; the TrayIcon crash of 02:30 was that same era's binary
refusing the profile server DB after a 2.3.0.4 run upgraded it (schema 11→19;
pre-upgrade copy preserved as `Duplicati-server.backup`). The shadow install
is now **neutralized** (renamed `updates.disabled-2026-08-25`).

Going forward, backups run on the **system service**: `/usr/bin/duplicati-server`
2.3.0.4, port 8300, `--portable-mode`, root, unit `duplicati.service` with
`Nice=19`/`IOSchedulingClass=idle`.

> ⚠ **RESTART TRAP (open at time of writing).** The persisted
> `/etc/default/duplicati` (edited 04:10) reads
> `--webservice-interface=loopback --webservice-port=8300` — loopback is good
> and already staged — but it **drops `--portable-mode`**, while the running
> server (started 02:46) still has it. On the next restart/reboot the server
> will come up against a DIFFERENT data root: job 2 and its schedule become
> invisible and backups silently stop — this arc's founding failure shape.
> **Before any restart, re-add `--portable-mode` to DAEMON_OPTS** (or
> deliberately migrate the portable server DB to the default root location).
> File is root-owned; the fix is Paul's.

The user-lane CLI runner (timer disabled
throughout) is superseded; its final record: 0-for-3 on full runs, with three
*distinct* failure modes (GPGFlushError; pre-flight `ConstraintException` on
crashed-fileset debris — cleared by deleting the crashed fileset via
Duplicati's own `delete --version=0` after a dry-run; and an idle deadlock at
the scan boundary whose thread census showed the `wait_for_partner`/
`anon_pipe_read` fingerprint **with zero gpg processes in existence** —
retro-attributing run 1's identical "pipe wait" evidence away from gpg; the
thread census is preserved in the session transcript only).

## 3. The job (id 2, "Yamaguchi") — configuration of record

> **Superseded 2026-08-25 14:14 CDT** — this section describes the configuration
> *as certified* by §5 (the `20260825T102739Z` fileset). The live job has since been
> widened; the current configuration of record is §8.1 /
> `_yamaguchi_check/yamaguchi-config-post-widening.json`.

Destination `file:///media/pcalnon/temp_backups/Yamaguchi/` (dedicated
subdirectory; an earlier auto-started run with default options into the mount
ROOT was stopped and its 78 orphan volumes deleted via the job-delete-with-
remote-files API — the certified `Ubuntu/` subdir is invisible to the
non-recursive file backend and was verified untouched). Source
`/home/pcalnon/` with the Ubuntu-fresh exclusion set parsed live from the
runner (44) plus `*.iso`/`*.vdi` — 46 filters.

Settings: **`encryption-module=aes`** (§4), `compression-module=zip`,
`--blocksize=1MB` (irreversible — pinned), `--dblock-size=500MB`,
`--skip-files-larger-than=8GB` (Paul's choice; admits the 2–8 GB band the old
2 GB cap dropped), `--no-auto-compact=true` (load-bearing beside retention:
retention marks deletions, and an interrupted compact is what destroyed the
July archive), `--allow-missing-source=true`, `--asynchronous-upload-limit=1`,
`--tempdir=/media/pcalnon/temp_backups/_duplicati_tmp` (ext4 — the server's
default `/tmp` is tmpfs, the run-1 trap), `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`
(Paul's choice), daily 13:00 schedule. Passphrase: the fresh-set key
(`PASSPHRASE`, sha256[:16]=6d8b263f…), set explicitly from the credentials
file. Config records (passphrase redacted):
`_fresh_dlist_check/yamaguchi-config-{as-created,imported}.json` (**both
predate the §4 AES switch and still read `encryption-module=gpg`** — history,
not the config of record) and `_yamaguchi_check/yamaguchi-config-final.json`
(**the configuration as certified**: aes, 11 settings, 46 filters).

## 4. Why AES (decision 2026-08-25, superseding gpg fixes 2–3 for this job)

The first properly-configured run — gpg module *with* the compression-off and
upload-limit mitigations — failed at 9 minutes with the identical
GPGFlushError, under root, in a calm-memory window (50 G available, PSI ≈ 0).
gpg had consumed the full volume (the miss is on the drain side), the
root-context difference could not be inspected without root, and a virgin-
keyring user approximation ran clean — so the class was judged unfixable-by-
configuration in this context. The built-in AES module — the investigation's
own "strongest structural fix" — eliminates the external process, the 5 s
`Join`, and every root-context gpg coupling. The AES run succeeded on the
first attempt. Old sets (Ubuntu/, the old archive) remain gpg-encrypted and
restorable; both passphrases stay retained.

## 5. Certification evidence (durable under `_yamaguchi_check/` and the drill run dir)

1. **Coverage** (`duplicati_dlist_crosscheck.py --encryption aes`): every hash
   the dlist references — 726,130 files + 110,989 non-file entries →
   **1,122,583 distinct hashes** (single-block files, metadata, 7,729
   blocklists content-hash-verified, and their expansions) — is declared by
   the dindex set across **187/187** dblocks, with **needed == available
   exactly** (zero surplus: a clean single-run set). `IsFullBackup: True`.
   Log: `_yamaguchi_check/crosscheck.log` (archived re-run; numbers identical
   to the first in-session run).
2. **Physical + ciphertext** (`duplicati_decrypt_validate_all.bash … aes`):
   **375/375 volumes decrypt with full HMAC verification** (SharpAESCrypt
   rc-3-on-mismatch semantics; 594 s for 98.1 GB / 91.3 GiB; the log's final
   banner still says "MDC" — a gpg-era hard-coded string in the tool, noted).
   The job DB lives in the root
   server's portable data and is not readable user-side; whole-content HMAC
   subsumes the size/hash-vs-DB rung of the previous ladder.
3. **Restore drill** (`duplicati_drill_fresh.py --encryption aes
   --single-invocation`): destination-only temp DB (`--version=0` — this
   destination holds exactly one dlist), `--no-local-blocks=true`, one shared
   recreate for all candidates (a per-candidate recreate is prohibitive at
   1.12 M blocks), dual job-DB-independent oracle (manifest per-file SHA-256
   + live-source re-hash gated on pre-backup mtime, backup-start epoch
   1787653659). Result: **14/15 VERIFIED** — every file stratum including
   `large` (4,702,947,166 B across 21 dblocks) and `empty` — **13 live-oracle
   matches, 0 contradictions** (floor 10). Run dir:
   `_yamaguchi_drill/drill-20260825-075730/`.
4. **The symlink finding** (the 15th candidate): partial restores in the new
   engine (2.3.0.4, `--restore-legacy=false`) do **not** create parent
   directories for metadata-only entries, and deliberately **skip links whose
   relative target points outside the restored tree** (containment policy) —
   three progressively-isolating retests pinned both rules, each retrieving
   the correct stored target string. Retest 4 (parent directory present,
   target subtree in-tree): **SYMLINK RESTORED, live-oracle match** — target
   byte-identical to the live link. Caveat recorded: **partial** restores of
   symlink-only folders need their parent folder in the filespec (or
   pre-created); full-tree restores are unaffected. Logs:
   `_yamaguchi_drill/drill-20260825-075730/symlink-retest*.log` (numbered
   retest, retest3, retest4 — there is no retest2; scripts at
   `_yamaguchi_drill/symlink_retest*.bash`, retest 4's verdict in the
   `symlink-retest4` unit journal).

## 6. Tooling (branch `feat/yamaguchi-backup-tooling`)

`yamaguchi_server_api.py` (authenticated REST client — server-util lacks
abort/delete verbs; credential read in-process from the repo `.env`,
`DUPLICATI_WEB_CREDENTIAL`), `yamaguchi_build_job.py` (job builder — parses
the exclusion list live from the runner; applies the investigation settings),
`yamaguchi_switch_aes.py`, `yamaguchi_watch.bash`, and `--encryption aes`
modes in the three certification tools. Accepted deviation, documented:
SharpAESCrypt takes the password on argv (transient `/proc` exposure on this
single-user host).

## 7. Open items

> Snapshot of 2026-08-25 08:29. Dispositions as of the evening addendum are in §8.7;
> the RESTART TRAP named below was **closed at 14:14** (`--portable-mode` restored by
> Paul; the running process matches the file).

- **Plan acceptance tail**: second drill from a different fileset after an
  incremental (the daily 13:00 schedule produces one naturally); schedule
  survival across a reboot (server service is system-enabled — verify after
  the next boot); decide the fate of the old sets.
- **Server best practices**: loopback interface is already staged in
  `/etc/default/duplicati` pending restart — but see the §2 RESTART TRAP:
  `--portable-mode` must be restored to DAEMON_OPTS first;
  service runs as root (works, reads everything — including files a user-run
  backup skipped, e.g. the 0000-mode release-train key; consider whether
  that inclusion is wanted); no failure alerting on server-run jobs (the
  lane's OnFailure covered only the CLI path; options: `send-mail-*`,
  `run-script-after`, or an API-polling watchdog).
- **Retirement candidates**: the user-lane timer/units/runner (superseded;
  keep disabled or remove), the old `Ubuntu/` fresh set (~55 GB freeable once
  Yamaguchi has a second good fileset — it remains the only gpg-era certified
  set until then), scratch dirs (`_gpg_repro` 2.3 GB, `_fresh_drill` 1.3 GB,
  `_yamaguchi_drill` ~6 GB restored copies, `_drill_scratch` ~35 GB from the
  old-archive work, `_duplicati_tmp` stragglers).
- **Old-archive items** (handoff §4 3–5, 7–8) remain: the Recreate died with
  the old profile server (disposition now moot-ish but the damaged archive
  questions stand); purge decision; migration planning; the root
  `duplicati.service` on 8200 was repurposed to 8300 rather than removed.
- The profile server DB (schema 19, jobs Ubuntu/Ubuntu-fresh) is orphaned
  from any running server; openable by 2.3.0.4+ if ever needed.

## 8. Addendum (2026-08-25 evening) — scope widening and re-certification

### 8.1 What changed (Paul, 14:14 CDT, via the UI)

Diff of the live job against `yamaguchi-config-final.json`
(`yamaguchi_config_record.py`; record: `_yamaguchi_check/yamaguchi-config-post-widening.json`,
passphrase redacted):

- **Sources** (1 → 3): `/home/pcalnon/` plus two explicit VM images —
  `VirtualMachines/VirtualBox/win10_vm_2023-04-29/win10_vm_2023-04-29.vdi`
  (63,860,375,552 B, static since 2026-07-15) and
  `VirtualMachines/VirtualBox/win11_vm_clean_2026-07-15/win11_vm_clean_2026-07-15.vdi`
  (55,966,695,424 B — **its VM was running under VBoxHeadless during the backup and
  still is**, so the stored image is crash-consistent at best; §8.6). The
  `VirtualMachines/` exclude (filter 40) remains, so only the named images enter.
- **Filters** (46 → 44): `*.iso` and `*.vdi` removed — the two Ubuntu server ISOs
  under `Development/python/Tooling/k8s/` (3.3 GB + 2.3 GB) entered with the VDIs.
- **Settings** (11 → 10): **`--skip-files-larger-than=8GB` removed entirely** (the
  VDIs required it; the cap's absence is now global). The UI re-keyed
  `--dblock-size` as `dblock-size` (same 500MB). Unchanged: `encryption-module=aes`,
  `compression-module=zip`, `--blocksize=1MB`, `--no-auto-compact=true` paired with
  `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`, `--allow-missing-source=true`,
  `--asynchronous-upload-limit=1`, `--tempdir=/media/pcalnon/temp_backups/_duplicati_tmp`.
- **Schedule**: `Time` 2026-08-25T18:00:00Z → **2026-08-25T14:00:00Z**, `Repeat=1D`,
  all days — the job now fires **daily at 09:00 CDT** (server `ProposedSchedule`
  2026-08-26T14:00:00Z), not the 13:00 CDT §3 describes. The two agree; the
  handoff's "configured 18:00Z" was the pre-widening record. Intent is Paul's to
  confirm (§8.6).
- `/etc/default/duplicati` (same edit, mtime 14:14:25): the active line is
  `--webservice-interface=any --webservice-port=8300 --portable-mode`; the running
  server (pid 1327450, started 02:46) matches it. The stale loopback COMMENT on the
  next line still lacks `--portable-mode` — never activate it verbatim.

### 8.2 Task 8 — the widened backup, settled

Manual run 2026-08-25 19:14:49Z → 20:56:20Z (1 h 41 m 32 s), **`ParsedResult: Success`**:
726,190 files / 326,505,686,811 B examined; **195 added = 125,431,093,952 B**
(both VDIs 119,827,070,976 B + the two ISOs 5,586,804,736 B + ~17 MB of ordinary
files), 250 modified (241,072,793 B), 90 deleted at source, 0 with errors, 0
too-large; **401 volumes / 104,483,971,101 B uploaded, 0 retries, 0 warnings, 0
errors**; post-run test 3/3 (dlist, dindex, dblock) OK. Retention thinned task 7's
same-day fileset (`DeletedSets: [2026-08-25T13:13:38-05:00]`, `FilesDeleted: 1`);
**`CompactResults` empty** — deletion, not compaction, as configured. Full record:
`_yamaguchi_check/census-post-widening.txt` (`yamaguchi_census.py`, newest 5 runs).

### 8.3 Destination census, settled (18:40 CDT)

**780 files = 2 dlist + 389 dblock + 389 dindex; 202,586,201,260 B (188.673 GiB)** —
the filesystem count and byte total **agree exactly** with the server's
`TargetFilesCount` / `TargetFilesSize`. Reconciliation against the previous settled
state (380 files / 2 dlists after task 7): +401 uploads − 1 retention-deleted dlist =
780 ✓. Surviving filesets: `20260825T102739Z` (the original full, §1–§5) and
`20260825T191449Z` (the widened scope). The 18:00Z and 18:13Z same-day filesets
were retention-thinned: `1W:1D` keeps the earliest fileset of each 1-day interval
measured from the last kept backup, plus always the newest (observed twice — the
middle fileset went, the 10:27Z full stayed). **By the same rule the drilled
`…191449Z` fileset will itself be thinned by the next run** (2026-08-26 14:00Z is
< 1 day after 10:27Z): the census afterwards should read `102739Z` +
`20260826T140000Z` — thinning, not loss; the drill-2 evidence names a dlist that
will no longer be on the destination while its blocks stay referenced by the
successor fileset. Retention removes only the dlist (`FilesDeleted: 1` on each
thinning run); with `--no-auto-compact=true` a thinned fileset's exclusive
dblock/dindex volumes remain until an explicit compact.

### 8.4 Re-certification ladder for the widened fileset `20260825T191449Z`

1. **Coverage** (`duplicati_dlist_crosscheck.py --encryption aes`, now checking the
   NEWEST dlist): **1,241,950 / 1,241,950** distinct needed hashes declared by the
   dindex set across **389/389** indexed dblocks; 7,783 blocklists content-hash-
   verified; 0 unexpandable; `IsFullBackup: True`; 726,190 files + 110,969 non-file
   entries. Available 1,243,575 → a surplus of 1,625 blocks, which is the older
   fileset's and the thinned filesets' exclusive blocks — expected in a multi-run
   set (§5.1's zero surplus is a single-run property). Log:
   `_yamaguchi_check/crosscheck-post-widening.log`.
2. **Physical + ciphertext** (`duplicati_decrypt_validate_all.bash … aes`, every
   volume on the destination): **780/780 decrypt with full HMAC verification, 0
   failures, 1,159 s** (2026-08-26 02:29–02:48 CDT, transient unit
   `yamaguchi-validate2`). Log: `_yamaguchi_check/decrypt_validate_all-post-widening.log`.
3. **Restore drill 2** (`duplicati_drill_fresh.py --encryption aes
   --single-invocation`, revision of this date — destination-only temp DB,
   `--no-local-blocks=true`, newest-dlist selection with a pre/post-restore guard,
   oracle cutoff derived from the dlist = epoch 1787685289): **17/17 VERIFIED** —
   every stratum: single/multi × early/mid/late, `large` (4.70 GB across 21
   dblocks), **`vmimage` — the 63.86 GB static win10 image across 201 dblocks,
   live-oracle match**, `empty`, and the symlink pair `.cargo/bin/cargo → rustup`
   (link target restored and live-matched; the 20.8 MB sibling live-matched).
   **13 live-oracle matches, 0 contradictions** (floor 10); 2 benign divergences
   (Firefox session-store files rewritten after the backup), 1 not engaged (a git
   ref log deleted since). dblock coverage **241/389**. One invocation, rc 2
   (success-with-warnings; 0 warning lines in the restore log), 2,444 s, 63.92 GiB
   restored; the newest-dlist guard held before and after (destination unchanged).
   Run dir `_yamaguchi_drill/drill-20260825-183711/` (`results.json`,
   `restore-all.log`, `drill-meta.json`, `candidates.json`, `provenance.txt`); unit
   log `_yamaguchi_drill/drill2-run.log` (`drill-20260825-183412/` beside it is the
   `--select-only` preview, no results — not a failed drill). Exact invocation, run
   as a `systemd-run --user` transient unit: `python3 -u util/ad-hoc/duplicati_drill_fresh.py
   --encryption aes --single-invocation --dest /media/pcalnon/temp_backups/Yamaguchi
   --run-root /media/pcalnon/temp_backups/_yamaguchi_drill` (the symlink+sibling
   recipe holds only in `--single-invocation` mode, where both land in one restore
   tree). This is plan §7 criterion 3 — a second drill from a *different* restore
   point after incrementals — satisfied.

### 8.5 Tooling changes landed with this addendum

- `duplicati_drill_fresh.py`: drills the NEWEST dlist (never `dlists[0]`, which after
  any incremental is the original full); re-lists the destination before and after
  each restore and refuses (rc 2) if the newest dlist changed; derives
  `--backup-start-epoch` from the drilled dlist; adds a `vmimage` stratum (smallest
  image whose live mtime predates the backup, so the live oracle engages); bounds
  `large` at `--large-max-bytes` (16 GiB) and excludes images from it; prefers a
  symlink whose live target is a sibling file in the fileset and restores the
  sibling too (`symlink-target`), which satisfies the §5.4 engine preconditions
  without pre-created directories.
- `duplicati_dlist_crosscheck.py`: newest-dlist selection (was an exactly-one assertion).
- New: `duplicati_dlist_query.py` (what is in the newest fileset, without the job DB),
  `yamaguchi_config_record.py` (redacted config of record), `yamaguchi_census.py`
  (filesystem-vs-server reconciliation + full run stats), `yamaguchi_watchdog.py` +
  `util/systemd/yamaguchi-watchdog.{service,timer}` (alerting candidate B),
  `yamaguchi_run_script_after.bash` (alerting candidate A, draft),
  `yamaguchi_drill_watch.bash` (unit watcher).

### 8.6 Findings that need Paul's decision

1. **The release-train private key is in the backup** — *decided 2026-08-26: KEEP (§8.9-4)* —
   `Development/python/Juniper/.gnupg/juniper-release-train.2026-07-21.private-key.pem`
   (1,675 B, mode 0000; root reads it). It is currently that key's only backup and
   sits on the same spindle as the original. Wanted, or exclude? Excluding = add the
   filter `-/home/pcalnon/Development/python/Juniper/.gnupg/juniper-release-train.2026-07-21.private-key.pem`
   — and then the key is in NO backup, so it needs its own off-spindle copy.
2. **A running VM's image is being backed up.** *Decided 2026-08-26: EXCLUDED, effective from
   the 08-27 run (§8.9-3).* `win11_vm_clean_2026-07-15.vdi` is
   open by VBoxHeadless (38 h uptime at 18:30); its mtime advances continuously, so
   (a) the stored copy is not a consistent snapshot, (b) every daily incremental
   re-reads the whole 56 GB image and re-uploads its changed blocks — the daily
   run's duration is therefore no longer the pre-widening ~9 min and is unknown
   until the first scheduled run lands — and (c) no `--snapshot-policy` can help on
   this filesystem. Options: exclude the running VM's image (remove its `Sources`
   entry via GET/modify/PUT), shut the VM down before 09:00, or accept
   crash-consistency. The win10 image is static and unaffected.
3. **Schedule moved to 09:00 CDT** (§8.1) — intended? *Confirmed 2026-08-26: yes, 09:00 CDT
   daily stays (§8.9-2).* If 13:00 had been, the fix would have been a
   GET/modify/PUT of backup 2 setting `Schedule.Time` to the next day's `18:00:00Z`
   (`yamaguchi_switch_aes.py` pattern, passphrase rule in item 4), with `ActiveTask: null`.
4. **Alerting** (plan §7 criterion 4 — *B DEPLOYED 2026-08-26 12:30 CDT, criterion CLOSED,
   §8.9-1*; before that, server-run jobs failed silently):
   - **B, recommended: `yamaguchi_watchdog.py` on a user timer** (`util/systemd/`,
     12:00 daily, `Persistent=true`). Asks the server from outside, so it also catches
     what a job hook structurally cannot — never ran, job definition vanished (the
     portable-mode trap presents as `JOB_MISSING`), server down, run stuck.
     **Proven 18:40–18:41 CDT**: forced `UNREACHABLE`, `JOB_MISSING`, `STALE` each
     alerted (rc 1, durable record written) and the normal check read `OK`; one
     deliberate desktop notification fired (`notify-send rc=0`); proof record archived
     at `_yamaguchi_check/watchdog-proof-20260825.log`. Deploy = **after this PR
     merges and the primary checkout is synced** (the unit's `ExecStart` names the
     primary checkout path, which lacks the script until then): copy the two units to
     `~/.config/systemd/user/`, `daemon-reload`, `enable --now` the timer. Closing
     test for criterion 4 (an `OK` firing is not "a failure notification observed"):
     run the deployed script once with `--backup-id 999` — it writes the REAL
     `~/.local/state/duplicati/server-failures.log` line and a critical desktop
     notification; annotate that line as synthetic. B depends on `Linger=yes` for
     the user (verified today) — re-check `loginctl show-user pcalnon -p Linger`
     after any reboot, since a lingerless session is the 42-day-outage mechanism.
   - **A: `--run-script-after`** (`yamaguchi_run_script_after.bash`, draft; it does
     NOT reuse `util/duplicati_backup_failure.bash` — own notify path) — fires per
     run as root; must be deployed root-owned under `/usr/local/lib/duplicati/`
     (the directory does not exist yet: `sudo install -D -o root -g root -m 0755 …`;
     a user-writable hook run by root is an escalation), then the setting added to
     the live job (Paul-gated PUT — see the passphrase-mask rule below), proven on a
     throwaway job with an unreachable destination. Complements B; cannot replace it.
   - **PUT rule**: `GET /api/v1/backup/<id>` returns `passphrase` as a 15-char mask,
     so any GET/modify/PUT must first replace that setting with the real value from
     `~/.config/duplicati-backup/env` — exactly what `yamaguchi_switch_aes.py` does
     (its `drop`/`insert` of `passphrase`) — then GET again and confirm
     `encryption-module=aes`, the expected source count (3 until §8.9-3; **2** since), 44
     filters, and watch the next run's `ParsedResult`. `yamaguchi_edit_sources.py` (§8.9-3)
     is the rule as code, with a PBKDF2-fingerprint guard on the re-inserted value. A PUT carrying the mask is refused or mangled by the server
     (it has explicit placeholder handling); never "simplify" the pattern.
   - The config records' `<redacted>` therefore replaces a placeholder, not a secret
     (the mask is identical across records and matches neither real key) — kept as
     belt-and-braces.
5. **`~/.config/Duplicati/dbconfig.json`** is a hand-written single JSON object (with
   a BOM) mapping the Yamaguchi destination to `DQRVQNDIFX.sqlite` (the OLD fresh
   set's job DB). Per `CLIDatabaseLocator.cs` at the installed tag the CLI expects a
   JSON *array* and matches on `Username` too (null for a plain `file://` URL), so a
   `--dbpath`-less operation would fail to parse the file — or, once shaped as an
   array, never match and create a fresh random DB — rather than open the wrong one.
   Misleading rather than dangerous. Fix (Paul's user config): delete the file
   (Duplicati rewrites its own) or rewrite it as an array with `"Path":
   "/media/pcalnon/temp_backups/Ubuntu"`. Always pass `--dbpath` regardless.
6. **Loopback restage**: edit only `any` → `loopback` in the ACTIVE line of
   `/etc/default/duplicati`, then restart when no task is running.
7. **Server-brain backup** (§7 item): the job definition, schedule, filters and
   encrypted passphrase live only in `/usr/lib/duplicati/data/Duplicati-server.sqlite`
   (job DB `BMXWPAOGLP.sqlite`, both root-owned, outside every backup). Copy via the
   SQLite backup API — a live `cp` of a WAL-mode DB can tear. The `sqlite3` CLI is
   **not installed** on this host; the stdlib does it:
   `sudo python3 -c "import sqlite3; s=sqlite3.connect('/usr/lib/duplicati/data/Duplicati-server.sqlite'); d=sqlite3.connect('/mnt/Backups/Ubuntu/_yamaguchi_records/Duplicati-server.sqlite'); s.backup(d); d.close()"`.
   The redacted config record plus `~/.config/duplicati-backup/env` is a
   re-creatable definition.
8. **Migration (plan §7 criterion 6, OPEN)**: Yamaguchi is on sdc4, the same
   physical disk as `/home` (sdc3). Facts for the decision: sda1 (SATA WD40EZAZ,
   `/mnt/Backups/Ubuntu`, 1.1 TB free) hosts the damaged old archive at its root — a
   Yamaguchi subdirectory there is invisible to the old job's non-recursive listing;
   the My Passport (sdb, WD40NMZW, sdb1 ext4 2 TB with 1.5 TB free, sdb2 1.6 TB
   unformatted) hangs off a USB-2 hub (bus 3, port 1.4, 480 Mb/s) while buses 2/4/6
   (10 Gb/s) and 8 (5 Gb/s) are idle — a replug changes its feasibility. Moving the
   existing set (copy the folder, repoint `TargetURL`) preserves the certified
   volumes; a fresh full to the new place costs ~2 h and keeps `--blocksize` free to
   change (it is irreversible per set). Procedure for the move variant, once decided:
   (1) `mountpoint` guard on the target; (2) copy the folder with `rsync -a --checksum`
   and re-run `duplicati_decrypt_validate_all.bash` on the copy; (3) with
   `ActiveTask: null`, GET/modify/PUT backup 2's `TargetURL` and fix `dbconfig.json`;
   (4) one backup run, then `duplicati_drill_fresh.py --dest <new>`; (5) keep the sdc4
   copy until that drill passes; announce the drill to any GPU-campaign session first.
   Option (b) alone is a **re-scope** of criterion 6 (plan §3 rejected sdb1 on
   measurement; §8 decision 1) — it needs a re-measurement after the replug and a plan
   amendment, not just a choice.

### 8.7 Plan §7 acceptance criteria — status after this addendum

- [x] A full backup has completed successfully (task 5; and the widened scope, task 8).
- [x] A restore drill has recovered real files with matching checksums (drill 1, §5.3).
- [x] A second restore drill from a *different* restore point after ≥1 incremental —
      drill 2 (§8.4-3): fileset `20260825T191449Z`, 17/17 (restore complete 19:19 CDT,
      verdict after hashing 19:31 CDT, 2026-08-25).
- [x] A failure notification observed firing — B **deployed** 2026-08-26 12:30:59 CDT (timer
      enabled, persistent); the deployed script's closing test fired `JOB_MISSING` at 12:31:30
      with the durable record and a desktop notification (`notify-send rc=0`); status back to
      `OK` at 12:32:21 (§8.9-1, proof `_yamaguchi_check/watchdog-closing-test-20260826.log`).
- [ ] Logout/login and reboot survival — not yet exercised (system unit enabled; job in
      the portable data root; the restart trap is closed).
- [ ] Migration to a physically separate drive — OPEN; Paul's re-scope decision
      (destination migration vs second copy) is recorded nowhere yet.

### 8.8 Retirement inventory (measured 18:2x CDT; nothing deleted — each needs Paul's go)

`_drill_scratch/` 35 GB (old-archive era; `drill.sqlite` + 6.86 GB WAL — **the old
archive's only local database**, the state of the purge dry-run; keep until §7's
old-archive purge decision is executed or formally abandoned, else that work needs a
multi-day Recreate) ·
`_duplicati_tmp/` 4.0 GB = 8 × ~524 MB `dup-*` from 2026-08-23 23:48 + 8 small
stragglers (4 of them from 2026-08-24 22:22), all pcalnon-owned (the user lane's; the
root server cleans its own) —
**contents only, never the directory, never during a run** · `_yamaguchi_drill/`
5.6 GB **+ 64 GB of drill-2 restored copies** (`drill-20260825-183711/restored/`;
keep logs/results) · `_gpg_repro/` 2.3 GB ·
`_fresh_drill/` 1.3 GB (keep logs) · **`/media/pcalnon/temp_backups/Ubuntu/`** 51 GB
(the old gpg fresh set, 209 volumes — **never `/mnt/Backups/Ubuntu`, which is the
mountpoint of the 5,369-volume old archive and is never deleted**) +
`~/.config/Duplicati/DQRVQNDIFX.sqlite` (+ `-wal`/`-shm`) 350 MB (the only certified
gpg-era set; drill 2 has passed — §8.4-3 — so freeable on Paul's go) ·
`~/.config/Duplicati/updates.disabled-2026-08-25/` 250 MB (only after a soak Paul
calls comfortable — it is the "two installs" root cause's remains) · user lane:
`~/.config/systemd/user/duplicati-backup.{service,timer}` +
`duplicati-backup-failure.service`, `~/.local/bin/duplicati-scheduled-backup.bash` +
`duplicati-backup-failure.bash`, repo `util/systemd/duplicati-backup.*` ·
`…/.claude/worktrees/curious-plotting-hummingbird/.env` still carries both
passphrases (2 lines; `.env` is git-ignored, so a `worktree remove` deletes it
silently) — reconcile against `~/.config/duplicati-backup/env` by sha256[:16]
(`6d8b263f…` / `b085454a…`) before deleting.

**KEEP — never in any sweep**: `_yamaguchi_check/`, `_fresh_dlist_check/`, every log /
JSON / results file under `_yamaguchi_drill/` and `_fresh_drill/`; in
`~/.config/Duplicati/`: every `*.sqlite*` — `backup SJTCQIIZSJ 20260712033545.sqlite`
(13 GB, spaces in the name, the only pre-deletion state of the old archive),
`Duplicati-server.sqlite` + its 112 MB `-wal` (the orphaned profile server's job
definitions live in that WAL — a "stray WAL" cleanup loses them), the dated
`Duplicati-server_2026-08-2*.sqlite` copies, `SJTCQIIZSJ*.sqlite*`, and
`DQRVQNDIFX.sqlite*` until Paul retires the old fresh set.

### 8.9 Addendum (2026-08-26 midday) — Paul's decisions executed; alerting B deployed; criterion 4 closed

Decisions taken by Paul 2026-08-26 ~03:36 CDT and executed 12:30–12:33 CDT. The session
was idle 03:41→12:30, so execution landed **after** the 09:00 run, not before; the
consequence is noted per item.

1. **Alerting = B, DEPLOYED.** New `util/ad-hoc/yamaguchi_watchdog_deploy.bash` (idempotent:
   asserts the primary checkout carries the script and `Linger=yes`, installs the two units
   into `~/.config/systemd/user/`, `daemon-reload`, `enable --now` the timer, one check now)
   ran at 12:30:59 CDT: timer **enabled** (`timers.target.wants/yamaguchi-watchdog.timer`),
   next fire **2026-08-27 12:00 CDT** (today's 12:00 had already passed at enable time and
   `Persistent=true` has no stamp to catch up from on a first enable — the deploy's own check
   stood in for it); first check `OK … newest run 2026-08-26T14:00:00Z ParsedResult=Success
   age=3.5h`. **Closing test 12:31:30 CDT**: `yamaguchi_watchdog.py --backup-id 999` against
   the REAL state dir → `ALERT JOB_MISSING … [notify-send rc=0]`, rc 1, the line written to
   `~/.local/state/duplicati/server-failures.log` and annotated in place as synthetic; the
   desktop notification fired; 12:32:21 the real check re-ran through the unit and the status
   file reads `OK` again. Proof record: `_yamaguchi_check/watchdog-closing-test-20260826.log`.
   **Plan §7 criterion 4 is closed** (§8.7). A (`--run-script-after`) stays a drafted,
   undeployed complement.
2. **Schedule confirmed — 09:00 CDT daily is intended.** No change.
3. **Running VM's image EXCLUDED.** New `util/ad-hoc/yamaguchi_edit_sources.py` — the §8.6-4
   PUT rule as code: refuses (rc 3) on an active or queued task, replaces the 15-char mask
   with the real `PASSPHRASE` from `~/.config/duplicati-backup/env` in place, refuses (rc 5)
   unless the value's fingerprint starts with the recorded prefix, never prints the value,
   and verifies the job after the PUT. **Fingerprint = PBKDF2-HMAC-SHA256, fixed public salt
   `juniper-yamaguchi-passphrase-fingerprint-v1`, 200,000 rounds, first 16 hex**: `PASSPHRASE`
   (Yamaguchi) → `1ff8be456de2752f`, `PASSPHRASE_OLD` (old archive) → `ad251cf01cbec4b5`. (The
   first revision used bare sha256 — CodeQL `py/weak-sensitive-data-hashing`, alert 586 on
   ml#1394 — and its sha256[:16] values `6d8b263f6d064556` / `b085454a8c34bd8c` remain valid
   only for the hand reconciliation of stray `.env` copies, §8.8.) The executed PUT ran under
   the sha256 revision; the guard's semantics are unchanged. It removed
   `/home/pcalnon/VirtualMachines/VirtualBox/win11_vm_clean_2026-07-15/win11_vm_clean_2026-07-15.vdi`
   from `Sources` at 12:31 CDT: PUT 200; re-GET verified **2 sources, 44 filters, 10
   settings, `encryption-module=aes`, passphrase masked again, `Schedule.Time`/`Repeat` and
   `ProposedSchedule` (2026-08-27T14:00Z) unchanged** (7/7). Record:
   `_yamaguchi_check/yamaguchi-config-post-vm-exclusion.json`; its diff against the
   post-widening record is exactly the win11 entry (`Sources` + `DisplayNames`) plus the
   server's own post-run `Schedule`/`Metadata` advancement. Effective from the **2026-08-27
   09:00 run**; today's run still re-read the image (below). The image's already-stored
   blocks (task 8 + today) stay on the destination while any surviving fileset references
   them and, under `--no-auto-compact=true`, until an explicit compact after that — the
   exclusion reclaims no space by itself.
4. **Release-train key — KEEP.** No change; the §8.6-1 caveat stands (same spindle as the
   original; the migration decision, §8.6-8, is what would move it off-spindle).

**Today's 09:00 run — the first scheduled run after the widening**: `Success`,
14:00:00→14:25:14Z (**25 m 15 s**); 753,435 files / 337,235,161,326 B examined (+27,245
files since task 8 — overnight session output); 31,447 added (11.58 GB), 1,202 modified
(**56,386,479,073 B — the win11 image**), 4,202 deleted; **29 volumes / 7,265,366,585 B
uploaded** (the image's changed blocks after dedup), 0 retries / warnings / errors, post-run
test 3/3. Retention thinned the drilled `191449Z` fileset exactly as §8.3 predicted
(`DeletedSets: [2026-08-25T14:14:49-05:00]`, `FilesDeleted: 1`, `CompactResults` empty).
Census 12:31 CDT: **808 = 2 dlist + 403 dblock + 403 dindex; 209,791,975,432 B (195.384
GiB) — `-> AGREE`**; filesets `20260825T102739Z` + `20260826T140000Z`. So the steady-state
daily cost with the running VM in scope was ~25 min and ~7 GB of upload; without it, expect
the pre-widening ~9-minute class from 08-27.

**Peer note**: the T6 GPU campaign completed 03:58 CDT (23/23 cells), five hours before the
run — no duplicati contention occurred.

**Records**: `_yamaguchi_records/` on sda1 re-synced 12:3x CDT via the new
`util/ad-hoc/yamaguchi_records_sync.bash` (the handoff's guarded `rsync` as a file — the
worktree hook refuses the `mountpoint -q … && rsync …` chain at the prompt).

**Still open after this addendum** — all root or Paul's call; exact steps in the 2026-08-26
handoff: loopback restage (§8.6-6), server-brain backup (§8.6-7), `dbconfig.json`
(§8.6-5), migration decision (§8.6-8), retirements (§8.8), reboot survival (criterion 5),
the old-archive tail.
