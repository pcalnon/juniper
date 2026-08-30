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
   passphrase live only in `/usr/lib/duplicati/data/Duplicati-server.sqlite`
   (job DB `BMXWPAOGLP.sqlite`, both root-owned, outside every backup). Copy via the
   SQLite backup API — a live `cp` of a WAL-mode DB can tear. The `sqlite3` CLI is
   **not installed** on this host; the stdlib does it:
   `sudo python3 -c "import sqlite3; s=sqlite3.connect('/usr/lib/duplicati/data/Duplicati-server.sqlite'); d=sqlite3.connect('/mnt/Backups/Ubuntu/_yamaguchi_keys/Duplicati-server.sqlite'); s.backup(d); d.close()"`.
   The redacted config record plus `~/.config/duplicati-backup/env` is a
   re-creatable definition.

   > **CORRECTED 2026-08-30 (§8.20).** This item said "**encrypted** passphrase". It is
   > **cleartext** — `Option` row `BackupID=2, Name=passphrase`, byte-identical to the
   > `env` file's `PASSPHRASE`. The destination above was also changed from
   > `_yamaguchi_records/` (mode **0775**) to `_yamaguchi_keys/` (mode **0700**): the
   > original target would have placed a cleartext key in a group/other-readable
   > directory, protected only by the parent's 0770. Treat this DB as key material.
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
      the portable data root; the restart trap is closed). **Updated 2026-08-26 (§8.10.2):
      this criterion now has a named, mechanically-identified failure candidate** — the
      destination filesystem sdc4 has NO boot-time mount configuration (not in `/etc/fstab`;
      systemd only observed the mount), so a root-run 09:00 job could fire against a bare
      path on `/`. Probe: `bash util/ad-hoc/yamaguchi_destination_durability_check.bash`.
      **That mechanism is RETIRED for the destination as of §8.13** — the migration moved it
      to fstab-managed sda1. Two residuals keep the criterion open: `--tempdir` is still on
      the non-durable sdc4 (§8.13.3), and the criterion has still never been exercised by an
      actual reboot (also re-check `Linger=yes` and the watchdog timer then).
- [x] Migration to a physically separate drive — **CLOSED 2026-08-26 (§8.13)**. Paul chose
      §8.11.2 option (a); the set was copied to sda1, the copy decrypt-validated 811/811 with
      0 failures, the job repointed (PUT 200, 8/8 post-checks), a proof run succeeded there in
      9 m 31 s, the census reads **813 / 210,486,704,937 B → AGREE**, and a drill at the new
      location verified **17/17 candidates, 16 live-oracle matches, 0 contradictions**.
      Yamaguchi is now on sda1 — a different physical disk from `/home`, and the only
      fstab-managed backup-class filesystem on this host.

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

> **Superseded in part by §8.10–§8.11 (2026-08-26 afternoon).** `dbconfig.json`, the
> migration decision and the retirements are now written up decision-ready in **§8.11**;
> reboot survival gained a named failure candidate in **§8.10.2**. Loopback restage,
> server-brain backup and the old-archive tail are unchanged and still root-gated.

### 8.10 Addendum (2026-08-26 afternoon) — the VDI exclusion is live-proven; the destination mount is not boot-durable

Written from a live re-probe at 15:52–16:01 CDT, after ml#1394 merged (`63dcbe1e`, 14:38
CDT) and the primary checkout was synced. Everything §8.9 deployed is still healthy:
watchdog timer `enabled` with next fire **2026-08-27 12:00 CDT**, status `OK` on a live
probe (`--max-age-hours 26`), the synthetic `JOB_MISSING` line still annotated, the server
still `any` + 8300 + `--portable-mode` with `/etc/default/duplicati` matching the process,
and `yamaguchi_edit_sources.py --remove /nonexistent --dry-run` still refusing at **rc 4**
without a PUT.

#### 8.10.1 An unscheduled run measured the exclusion — it works

§8.9 could only *predict* the effect of the win11 exclusion, because the PUT landed after
the 09:00 run. An **unscheduled run at `2026-08-26T18:12:06Z` (13:12 CDT)** — manual, not
the timer: it did not advance `Schedule.LastRun`, which still reads `2026-08-26T14:00:00Z`
— is the first run with the new source list, and measures it directly:

| metric | 14:00Z (VDI in scope) | 18:12Z (VDI excluded) | delta |
|---|---|---|---|
| `SizeOfExaminedFiles` | 337,235,161,326 B | 283,881,683,008 B | **−53,353,478,318 B** |
| `SizeOfModifiedFiles` | 56,386,479,073 B | 854,717,426 B | **−55,531,761,647 B** |
| `BytesUploaded` | 7,265,366,585 B | 557,858,839 B | **−92.3 %** |
| `FilesUploaded` | 29 | 3 | −26 |
| `ExaminedFiles` | 753,435 | 755,363 | +1,928 (churn) |
| Duration | 25 m 15 s | **16 m 18 s** | −8 m 57 s |

The daily 56 GB re-read of a continuously-modified image is gone, and the live config now
carries **2 sources** (`/home/pcalnon/` + the static win10 VDI), 44 filters, 10 settings,
`encryption-module=aes`, `--no-auto-compact=true`, retention unchanged.

**§8.9's "expect the pre-widening ~9-minute class from 08-27" was wrong, and this run is
the correction.** 16 m 18 s is the measured figure, and the residual is not upload: with
only 3 files uploaded, the run is dominated by *scanning* 755,363 files / 283.9 GB and by
the ~586 MB post-backup verification download (`BytesDownloaded=586,649,767`, `TestResults:
Success on 3 file(s)`). Two caveats in opposite directions: this run ran 4 h behind the
scheduled one and still absorbed 4,749 added files / 2.59 GB of churn, so a steady-state
09:00 run should be somewhat cheaper — but it will not approach 9 minutes, because the
~9-minute class predated the scope widening and its 755 k-file scan. **Treat ~12–16 min as
the new steady-state class** and re-measure on 08-27.

Retention behaved: `DeleteResults.DeletedSets=[]`, `CompactResults=False`. **Three dlists
is correct, not drift** — `1W:1D` keeps the earliest fileset per 1-day interval plus the
newest, so `20260825T102739Z` (08-25's earliest), `20260826T140000Z` (08-26's earliest) and
`20260826T181206Z` (newest) all survive. The 08-27 run should thin `181206Z`.

Census at 15:52 CDT: **811 = 3 dlist + 404 dblock + 404 dindex; 210,349,834,271 B (195.904
GiB) — `-> AGREE`** against server `TargetFilesCount`/`TargetFilesSize`. Evidence:
`_yamaguchi_check/vdi-exclusion-proof-20260826.log`.

#### 8.10.2 The destination filesystem has no boot-time mount configuration

Found while gathering facts for the migration decision (§8.6-8), and it changes that
decision's shape. **`/etc/fstab` has exactly four entries** — `/`, swap, `/home`, and
`/mnt/Backups/Ubuntu` (sda1). **`/media/pcalnon/temp_backups` (sdc4), which is where
Yamaguchi lives, is not one of them.** systemd's own view is the proof:

| mount | `FragmentPath` | `SourcePath` | meaning |
|---|---|---|---|
| `/mnt/Backups/Ubuntu` (sda1) | `/run/systemd/generator/mnt-Backups-Ubuntu.mount` | `/etc/fstab` | generated from fstab — **mounts at boot** |
| `/media/pcalnon/temp_backups` (sdc4) | *(empty)* | `/proc/self/mountinfo` | systemd merely **observed** an existing mount and synthesised a passive unit — **nothing remounts it at boot** |

The mount options are `rw,relatime` with no `nosuid,nodev`, which is the signature of a
plain root `mount`, not a udisks automount (compare the My Passport, which carries
`rw,nosuid,nodev,relatime`). Host uptime is **10 d 9 h (since 2026-08-16 06:14:39)** — the
mount has simply persisted since it was made by hand.

Why this matters: `duplicati.service` is a **system** unit running as root with
`Restart=always`, started at boot, independent of any desktop login. If it fires the 09:00
job while sdc4 is not mounted, `file:///media/pcalnon/temp_backups/Yamaguchi` is a bare
path on the root filesystem, not the destination — an **empty destination against a
populated job DB** (`BMXWPAOGLP.sqlite`), which is the shape that reads as "every remote
volume is missing". The root filesystem is `/dev/nvme0n1p5`, 716 G with **264 G free** —
enough to absorb most of a 196 GiB re-upload and fill `/` in the process, so the failure
mode is not a clean early error.

This is untested: criterion 5 has never been exercised, and the last reboot predates the
entire Yamaguchi job. **Criterion 5 is therefore not merely "unexercised" — it has a named,
specific, mechanically-identified failure candidate**, recorded in §8.7.

The check is now a re-runnable probe:
`bash util/ad-hoc/yamaguchi_destination_durability_check.bash` (read-only, always exits 0
so it composes inside `&&` chains during an incident; prints `DURABLE` / `NOT DURABLE` /
`ABSENT` per mountpoint). Evidence:
`_yamaguchi_check/destination-durability-20260826.log`.

Candidate remedies, none applied (each is root or Paul's call, and the migration decision
may moot the choice of filesystem):

- **(i) fstab entry for sdc4** — smallest change; makes the *current* destination durable
  but leaves Yamaguchi on the same physical disk as `/home`, so it does not touch criterion 6.
- **(ii) migrate to sda1** (§8.11.2 option a) — resolves criterion 6 *and* criterion 5's
  mount risk in one move, because sda1 is already the only fstab-managed backup-class
  filesystem.
- **(iii) a `--run-script-before` mount guard on the job** — defence in depth, and the only
  remedy that also covers a destination that is *unmounted mid-life*; needs root deployment
  under `/usr/local/lib/duplicati/` exactly as option A in §8.6-4, plus a Paul-gated PUT.

(i) and (ii) are alternatives; (iii) complements either. Doing nothing is a standing
reboot-shaped risk.

---

### 8.11 Decision packets (2026-08-26) — the three items Paul asked to be worked up

Analysis only. **Nothing in this section has been executed**; each ends in a question.

#### 8.11.1 `dbconfig.json` (§8.6-5) — recommendation: DELETE

Re-read live at 15:5x CDT; 308 B, `pcalnon:pcalnon`, mtime 2026-08-25 03:13. Confirmed
contents and four independent defects:

```json
{"Type":"file","Server":"localhost","Path":"/media/pcalnon/temp_backups/Yamaguchi",
 "Prefix":"duplicati","Username":"pcalnon","Port":8300,
 "Databasepath":"/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite",
 "ParameterFile":"/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite"}
```

1. **A BOM** (`EF BB BF`, verified with `od -c`) precedes the `{`.
2. **A single object, not an array** — per `CLIDatabaseLocator.cs` at the installed tag the
   CLI expects an array, so it fails to parse rather than opening the wrong DB (§8.6-5).
3. **The mapping is wrong**: it points the *Yamaguchi* destination at `DQRVQNDIFX.sqlite`,
   which is the **old gpg fresh set's** job DB. Yamaguchi's real DB is the root-owned
   `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`.
4. **`ParameterFile` names a 334 MB SQLite file.** A ParameterFile is a text file of CLI
   options; had this ever matched, the CLI would try to parse a binary database as one.
   (`Username: "pcalnon"` is a fifth defect in practice — the CLI computes null for a plain
   `file://` URL, so an array-shaped version would never match either.)

**Recommend deleting rather than rewriting**, for a reason that is new since §8.6-5 was
written: the rewrite variant maps the file to `/media/pcalnon/temp_backups/Ubuntu` and
`DQRVQNDIFX.sqlite` — **both of which are on the §8.11.3 retirement list**. Rewriting
therefore hand-authors a fresh mapping to a set Paul is being asked to delete in the same
session; it is self-obsoleting. Deletion also matches the standing rule ("always pass
`--dbpath` regardless"), removes the BOM/array/ParameterFile defects at once rather than
preserving a hand-written artifact of the class that caused the confusion, and costs
nothing — Duplicati writes its own if it ever wants one.

Exact action if approved: `rm ~/.config/Duplicati/dbconfig.json` (no root; user config).
It is the only `dbconfig.json` on the host in that profile, and nothing in `util/`
references it.

#### 8.11.2 Migration, plan §7 criterion 6 (§8.6-8) — facts re-measured; Paul picks

Every §8.6-8 fact was re-probed. Two changed, and §8.10.2 adds a decisive new one.

| fact | §8.6-8 (08-25) | re-probed 2026-08-26 16:00 CDT |
|---|---|---|
| Yamaguchi on sdc4, same physical disk as `/home` (sdc3) | yes | **confirmed** — `lsblk` shows sdc3 + sdc4 on sdc |
| sdc4 free | — | 1.9 T total, 359 G used, **1.4 T avail** |
| sda1 (`/mnt/Backups/Ubuntu`) free | 1.1 TB | **1.1 T avail** (3.6 T, 69 % used) — unchanged |
| My Passport sdb1 free | 2 TB, 1.5 TB free | **2.0 T, 369 G used, 1.6 T avail** — *changed* |
| My Passport bus | USB-2, bus 3 port 1.4, 480 Mb/s | **still USB-2** — sdb resolves to `usb3/3-1/3-1.4`, bus 003 root hub is 480 M. **Not replugged.** Buses 2/4/6 at 10 Gb/s and bus 8 at 5 Gb/s remain idle |
| **sda1 boot-durable, sdc4 not** | *not known* | **NEW — §8.10.2.** sda1 is fstab-generated; sdc4 has no boot-time mount configuration at all |

Three **new** facts against option (b), all found today:

- **sdb1's root is not writable by `pcalnon`** — owned `dnsmasq:pcalnon`, mode `drwxr-xr-x`
  (group has r-x only). A 512 MB `dd` probe returned `Permission denied`. Option (b) needs
  a root-created, `chown`ed subdirectory before it is even possible. (The `dnsmasq` owner is
  a uid collision from another system — cosmetic, but it is why the group bit is the whole
  story.)
- **sdb1 is not a spare disk.** It holds `Archive/`, `Downloads/`, `Movies/`, `Music/`,
  `TV Shows/` — live media, 369 G of it.
- **sdb1 is a udisks automount at a UUID path**
  (`/media/pcalnon/dee46823-4119-4914-ac15-08194ee27d81`, `rw,nosuid,nodev,relatime`), so it
  inherits the §8.10.2 problem in a *worse* form than sdc4: it is removable, and the path is
  a bare UUID.

Throughput arithmetic for (b), unchanged in conclusion: at 480 Mb/s the bus caps real
throughput near 40 MB/s, so a 196 GiB seed costs roughly 1.5 h and the bus, not the disk,
is the limit. After a replug to a 10 Gb/s bus the 5400-rpm WD40NMZW itself becomes the
limit at roughly 110–130 MB/s, so about 28 min. **The decision-relevant measurement can
only be taken after Paul physically replugs**; nothing in software can pre-empt it.

**The options, restated with today's facts:**

- **(a) Move the set to a subdirectory of sda1.** Different physical disk from `/home`
  (satisfies criterion 6), 1.1 T free against a 196 GiB set, invisible to the old job's
  non-recursive root listing, and — the new argument — **it is the only backup-class
  filesystem on this host that mounts at boot**, so it closes §8.10.2's reboot risk in the
  same move. Cost: the five-step procedure in §8.6-8, ending in a drill at the new
  location. Caveat unchanged: sda1 also hosts the damaged old archive, so one disk failure
  takes both.
- **(b) Second copy on the My Passport.** Still a **re-scope**, not a choice — plan §3
  rejected sdb1 on measurement (§8 decision 1) — and now carries three fresh objections
  (not user-writable, live media disk, removable UUID automount) on top of the USB-2
  measurement. Needs a replug, a re-measurement, a root-created directory, *and* a plan
  amendment.
- **(c) Both.** (a) for criterion 6 and §8.10.2; (b) afterwards as a genuine second copy on
  removable media, with its own drill. Highest cost, and the only option that produces two
  independent copies.

**Recommendation, stated as a recommendation and not a decision: (a) now, (c) as the
target.** (a) is the only option that closes two open criteria at once, needs no hardware
change, and uses a filesystem already proven and already mounted at boot. (b) should not
be attempted before the replug, because its measurement is what plan §3 rejected it on.

#### 8.11.3 Retirements (§8.8) — re-measured, tiered, nothing deleted

All sizes re-measured live at 15:5x–16:00 CDT (`du -sh`). §8.8's KEEP list was read first
and is unchanged; `_yamaguchi_check/` (76 K) and `_fresh_dlist_check/` (32 K) are on it and
appear nowhere below.

**Tier 1 — no dependency on any open decision; deletable on a plain go.**

| path | size | note |
|---|---|---|
| `_yamaguchi_drill/drill-20260825-183711/restored/` | 64 G | drill 2's restored copies; `results.json`, `restore-all.log`, `provenance.txt`, `candidates.json`, `drill-meta.json` all stay |
| `_yamaguchi_drill/drill-20260825-075730/restored/` | 4.5 G | same shape; 3 symlink-retest logs stay |
| `_yamaguchi_drill/drill-20260825-075352/tmp/` | **1.1 G** | **not in §8.8's inventory** — a stale *tempdir*, not a `restored/` (that drill's `restored/` is 8 K). A "delete `restored/`, keep the rest" sweep would have missed it |
| `_fresh_drill/drill-20260824-142353/restored/` | 1.3 G | 15 `restore-c*.log` + `results.json` stay |
| `_duplicati_tmp/` **contents only** | 4.0 G | 8 × ~524 MB `dup-*` dated 2026-08-23 23:48 + 8 small stragglers (4 from 08-24 22:22), all `pcalnon`-owned |
| `_gpg_repro/` (whole) | 2.3 G | `macro-20260824-043743` 1.8 G + `micro` 521 M |
| **Tier 1 total** | **≈ 77.2 G** | |

⚠️ `_duplicati_tmp/` **is the live job's `--tempdir`** (confirmed in the job's settings) and
its directory mtime is `2026-08-26 13:28` — exactly the 18:12Z run's end (18:28:24Z). The
directory is in active use; only the stale contents go, and only with `ActiveTask: null`.
Never the directory, never during a run.

**Tier 2 — a go with a consequence to weigh.**

| path | size | consequence |
|---|---|---|
| `/media/pcalnon/temp_backups/Ubuntu/` | 51 G | the old **gpg fresh set** (209 volumes) — the only certified gpg-era set. Drill 2 passed on Yamaguchi (§8.4-3), so it is superseded, not needed. **Never `/mnt/Backups/Ubuntu`** |
| `~/.config/Duplicati/DQRVQNDIFX.sqlite` + `-wal` + `-shm` | 334 M + 19 M + 64 K | that set's job DB. Delete **with** the set, never before |
| `~/.config/Duplicati/updates.disabled-2026-08-25/` | 250 M | the "two installs" root cause's remains; §8.8 says only after a soak Paul calls comfortable |
| **Tier 2 total** | **≈ 51.6 G** | |

**Tier 3 — BLOCKED, do not sweep.**

| path | size | blocker |
|---|---|---|
| `_drill_scratch/` | 35 G | holds `drill.sqlite` + a 6.86 GB WAL — **the old archive's only local database** and the state of the purge dry-run. Blocked until §7's old-archive purge decision is executed or formally abandoned; deleting it makes that work a multi-day Recreate |

Also untouched and unproposed: the user-lane systemd/`~/.local/bin` files and the repo's
`util/systemd/duplicati-backup.*` (a code change, better as its own PR), and
`…/worktrees/curious-plotting-hummingbird/.env` (its precondition was re-confirmed
2026-08-26: `~/.config/duplicati-backup/env` fingerprints `PASSPHRASE` → `6d8b263f6d064556`
and `PASSPHRASE_OLD` → `b085454a8c34bd8c` by sha256[:16] — the hand-reconciliation values
of §8.9-3, not the PBKDF2 ones).

**Honest framing of the payoff.** Tier 1 + Tier 2 is ≈ 128.8 G, but sdc4 currently sits at
**21 % used with 1.4 T free** — there is no capacity pressure, and none of this is needed to
make room for anything, including a migration to sda1. The case for sweeping is hygiene and
the removal of confusable artifacts (three restored trees, a superseded backup set and its
DB), not space. That argues for doing Tier 1 whenever convenient, and for treating Tier 2 —
particularly the 51 G old fresh set — as a decision about *when Paul is comfortable losing a
fallback*, not about disk usage.

---

### 8.12 Addendum (2026-08-26 late afternoon) — Paul's §8.11 decisions executed

Decisions taken 2026-08-26 ~16:05 CDT against the §8.11 packets:

| §8.11 packet | decision |
|---|---|
| §8.10.2 mount risk | **Fold into the migration** — no standalone fstab entry for sdc4; migrating to sda1 resolves it |
| §8.11.2 migration | **(a) move the set to sda1 now** |
| §8.11.3 retirements | **Tier 1 AND Tier 2 approved in full** (Tier 3 `_drill_scratch/` remains blocked) |
| §8.11.1 `dbconfig.json` | *not answered in that round; see §8.12.4* |

#### 8.12.1 Sequencing — Tier 2 deliberately deferred, and why

The approvals were executed in an order that is **not** the order they were
given. Tier 2's `/media/pcalnon/temp_backups/Ubuntu/` is the old gpg fresh set —
the last certified non-Yamaguchi fallback on this host. §8.6-8 step 5 already
requires keeping the sdc4 Yamaguchi copy until a drill passes at the new
location; deleting the *other* fallback during the same window would leave the
migration with no net at all. So:

- **Phase A (done, 16:13 CDT)** — Tier 1 in full, plus `updates.disabled-2026-08-25`
  (250 M), which has no fallback role.
- **Phase B (in progress)** — the migration, steps 2→4, keeping the sdc4 copy.
- **Phase C (after the drill passes)** — Tier 2's old gpg fresh set +
  `DQRVQNDIFX.sqlite*`, and only then the sdc4 Yamaguchi copy.

This is a sequencing judgement, not a change to Paul's decision: everything
approved still goes, and nothing extra does.

#### 8.12.2 Phase A executed — 77 GB reclaimed

`util/ad-hoc/yamaguchi_retire_tier1.bash` (new; dry-run by default, `--execute`
to apply). It takes **no path argument** and expands no wildcard beyond the
tempdir contents, so it cannot be aimed elsewhere; every target is re-checked at
runtime against a `FORBIDDEN` list (`/mnt/Backups/Ubuntu`, `temp_backups/Ubuntu`,
`_drill_scratch`, `_yamaguchi_check`, `_fresh_dlist_check`, `Yamaguchi`, the live
tempdir) rather than the literal list being trusted. It refuses unless
`ActiveTask` is null and `SchedulerQueueIds` empty.

Deleted: `drill-20260825-183711/restored/` (64 G), `drill-20260825-075730/restored/`
(4.5 G), `drill-20260825-075352/tmp/` (1.1 G), `_fresh_drill/drill-20260824-142353/restored/`
(1.3 G), `_gpg_repro/` (2.3 G), `updates.disabled-2026-08-25/` (250 M), and the 16
stale `dup-*` files in the live tempdir (4.0 G, all dated 2026-08-23/24).

**sdc4: 359 G used / 1.4 T free (21 %) → 282 G used / 1.5 T free (16 %).**

Verified intact afterwards: every drill's `results.json`, `restore-all.log`,
`provenance.txt`, `candidates.json`, `drill-meta.json` and the symlink-retest
logs; `_yamaguchi_check/` (88 K); `_fresh_dlist_check/` (32 K); `_drill_scratch/`
(35 G, Tier 3); `Ubuntu/` (51 G, Tier 2, deferred); `Yamaguchi/` (196 G); and the
live tempdir **directory** itself, `drwxrwxr-x pcalnon pcalnon`, emptied to 4.0 K.

#### 8.12.3 A measured correction to §8.6-8's copy procedure: drop `--checksum`

§8.6-8 step 2 prescribes `rsync -a --checksum`. Run verbatim, the copy did
nothing visible for two minutes; `/proc/<pid>/io` explained why — the sender had
**read 21,822,431,232 B and written 0**. With `--checksum`, rsync pre-computes
checksums across the whole source before transferring.

On an **empty** destination that decides nothing: every file is missing and must
be sent regardless. The flag was costing a full extra read of a 196 GiB set —
about 20 minutes at the observed ~179 MB/s — to answer a question with only one
possible answer. The copy was stopped (destination still had **0 entries**,
`write_bytes: 0`, so nothing was lost) and relaunched without it; bytes began
flowing immediately at ~175 MB/s.

`util/ad-hoc/yamaguchi_migrate_copy.bash` now decides the flag from the target:
`--checksum` **when the target already holds volumes** (a re-run reconciling a
possibly-corrupt earlier copy — exactly what it is for), omitted when the target
is empty. Integrity is not weakened, because it was never rsync's job here:
`duplicati_decrypt_validate_all.bash` performs full AES/HMAC verification of every
volume on the copy, which is strictly stronger than an rsync checksum.

**The general lesson**: a verification flag that cannot change the outcome is not
free caution — it is cost with no information. Ask what a guard would *decide*
before paying for it.

#### 8.12.4 `dbconfig.json` — the recommendation is now stronger, not weaker

§8.11.1 recommended deleting rather than rewriting, because the rewrite target
(`/media/pcalnon/temp_backups/Ubuntu` + `DQRVQNDIFX.sqlite`) was itself on the
retirement list. **Paul then approved Tier 2 in full**, so that mapping is now
certain to be dangling. The only other coherent rewrite — pointing at the new
sda1 destination — is also useless: the matching job DB is the root-owned
`/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`, which a user-run CLI cannot open, and
`dbconfig.json` is a user-profile locator. Deletion remains the recommendation and
is now the only option that leaves nothing false behind.

#### 8.12.5 Tooling added for Phase B

- `util/ad-hoc/yamaguchi_migrate_copy.bash` — stages the copy. **Copy only**: it
  never touches the job definition, never repoints `TargetURL`, never deletes the
  source. Guards: both filesystems mounted, `ActiveTask` null and queue empty,
  free space ≥ source + 5 %; verifies by file count and byte total; prints the
  decrypt-validate command as the next step rather than claiming integrity itself.
- `util/ad-hoc/yamaguchi_edit_target.py` — migration step 3. Carries the §8.6-4
  passphrase rule verbatim from `yamaguchi_edit_sources.py` (PBKDF2 fingerprint
  guard, mask substitution, value never printed) and adds destination guards: the
  new target must exist, be on a mounted filesystem, hold **at least as many
  volumes as the current one and the same byte total** (rc 4 — the copy must be
  complete before the job is allowed to follow it), and have an `/etc/fstab` entry
  (**rc 7**, overridable only with `--allow-non-durable`), so the tool structurally
  refuses to move the job onto another non-boot-durable mount. Post-PUT it re-GETs
  and requires `TargetURL` to be the new value while sources, filters, settings
  count, `encryption-module`, passphrase masking and the schedule are unchanged.

---

### 8.13 Addendum (2026-08-26 evening) — the migration to sda1, executed

Plan §7 criterion 6, open since the arc began, executed 16:14–18:0x CDT under
Paul's §8.11.2 option (a). The set now lives on a **different physical disk from
`/home`** and — the argument that decided it, §8.10.2 — on the **only
fstab-managed backup-class filesystem on this host**, so the same move also
retires criterion 5's named failure candidate.

#### 8.13.1 What was done, in order, with the numbers

| step | result |
|---|---|
| **2a copy** | `rsync -a` (no `--checksum`, §8.12.3) sdc4 → sda1, 16:17:47→16:54:45 CDT, **36 m 58 s ≈ 95 MB/s**. Verified by count and bytes on both sides: **811 files / 210,349,834,271 B**, identical. Log `_yamaguchi_check/migrate-copy-20260826-161747.log` |
| **2b integrity** | `duplicati_decrypt_validate_all.bash` on the **copy**: **811 / 811 volumes decrypt-valid, 0 failures**, full HMAC, 2,926 s (16:55:18→17:44:04). Record `_yamaguchi_check/decrypt_validate_all-migrated-20260826.log` |
| **3 repoint** | `yamaguchi_edit_target.py` — every guard passed (mounted; **fstab-managed**; census 811/811 and bytes equal both sides; passphrase fingerprint `1ff8be456de2752f`). **PUT 200, 8/8 post-checks PASS**: TargetURL is the new value; sources (2), filters (44), settings (10), `encryption-module=aes`, passphrase re-masked, `Schedule.Time`/`Repeat` and `ProposedSchedule` all unchanged. Record `_yamaguchi_check/yamaguchi-config-post-migration.json` |
| **3b `dbconfig.json`** | deleted per §8.12.4, after archiving the 308-byte original to `_yamaguchi_check/dbconfig.json.retired-20260826` |
| **4a proof run** | manual run, task 11: **Success**, 22:45:12→22:54:43Z, **9 m 31 s**; 770,697 files / 285.2 GB examined; 16,302 added (1.04 GB), 732 modified, 968 deleted; **199 MB / 3 files uploaded**, 0 retries / warnings / errors; **`TestResults: Success on 3 file(s)`** — the post-backup sample was fetched and verified *from sda1*. Retention thinned `181206Z` (`DeletedSets: [2026-08-26T13:12:06-05:00]`) |
| **4b census** | **813 = 3 dlist + 405 dblock + 405 dindex; 210,486,704,937 B — `-> AGREE`** against the server. Record `_yamaguchi_check/census-post-migration-20260826.txt` |
| **4c drill** | see §8.13.4 |

The 9 m 31 s run is worth noting against §8.10.1: with the win11 VDI excluded
*and* a normal churn load, the daily cost is now **under 10 minutes** — the
"~12–16 min" estimate in §8.10.1 was measured on a run carrying four hours of
accumulated churn, and the steady-state figure is better than that. Writes to
sda1 (an SMR WD40EZAZ) did not degrade the run; the 500 MB dblocks are
sequential, which is the SMR-friendly case.

#### 8.13.2 Two stale hardcoded paths, found the hard way

The migration invalidated two tools at once, both by the same mechanism — a path
frozen at authoring time — and both failing **quietly**, which is why they are
recorded here rather than just fixed.

1. **`yamaguchi_watch.bash`** held `API=` pointing into the sibling worktree
   `.claude/worktrees/mossy-growing-salamander` (a §8.8 retirement candidate, so
   retiring it would have broken the watcher silently at the moment it is most
   wanted — mid-run) and `DEST=` pointing at the pre-migration destination, so
   every "dest files" count it printed would have described the wrong directory
   while looking entirely plausible. Both are now derived / parameterised.

2. **`yamaguchi_census.py`** — the more serious of the two, because it *is* the
   arc's primary invariant. Its `--dest` default and its `os.path.ismount` guard
   were both hardcoded to sdc4. Immediately after the repoint it censused the
   **old** directory while printing the **new** `TargetURL` one line below, then
   compared those mismatched witnesses and printed **`-> DIVERGE`** — with both
   witnesses in fact perfectly consistent at 813 / 210,486,704,937 B. Anyone
   chasing that DIVERGE would have been hunting a defect that did not exist, in
   the one tool whose entire job is to be trusted about exactly this. And Phase C
   retires the old directory: the next census after that would have found **zero
   files** and printed a maximally alarming DIVERGE against a healthy backup.
   `--dest` now defaults to the job's own `TargetURL`, and the mount guard walks
   up from the resolved destination to its containing mountpoint instead of
   naming a filesystem.

**The pattern worth carrying forward**: a tool that *reports on* a resource must
locate that resource the same way the system does — by asking the authority
(here, the job's `TargetURL`) — not by remembering where it used to be. A
hardcoded path in a checker does not fail loudly when it drifts; it produces a
confident, well-formatted, wrong answer. Both instances here printed a clean
report. One of them printed a false alarm; the other would have.

#### 8.13.3 Residual: the tempdir is still on the non-durable filesystem

The destination is now boot-durable. **`--tempdir` is not**: it still reads
`/media/pcalnon/temp_backups/_duplicati_tmp`, on sdc4, the filesystem §8.10.2
showed has no `/etc/fstab` entry. Severity is far lower than the destination case
— these are transient files, not the backup — but it is the same class, and after
a reboot without sdc4 mounted the job would write temp volumes to a bare path on
`/` (264 G free). With `--asynchronous-upload-limit=1` and 500 MB dblocks the
working set is small, so this is a tidiness and root-filesystem-pressure issue
rather than a data-loss one. Options, none applied — Paul's call, it is a live-job
setting:

- **(i)** leave it (fast scratch on a separate spindle from the destination, which
  is the performance-preferred arrangement);
- **(ii)** move it to `/mnt/Backups/Ubuntu/_duplicati_tmp` (fully durable, but puts
  temp write I/O on the same SMR spindle as the destination);
- **(iii)** move it under `/home` (fstab-managed, and a different partition from
  the destination — durable *and* off the destination spindle, but on the same
  physical disk as sdc4).

**(iii)** is the one that satisfies both constraints; it is recommended but not
applied.

#### 8.13.4 Drill at the new location, and what remains

**Drill at the new destination — PASSED.** `duplicati_drill_fresh.py --dest
/mnt/Backups/Ubuntu/Yamaguchi --single-invocation --encryption aes`, run dir
`_yamaguchi_drill/drill-20260826-175815/`, unit `yamaguchi-drill-migrated`,
17:58:15→18:59:01 CDT (**60 m 46 s wall, 27 m 46 s CPU, 12.6 G peak RSS**).

- drilled dlist `duplicati-20260826T224512Z.dlist.zip.aes` — the **newest** of 3,
  per the §0 decision (never `dlists[0]`), oracle cutoff epoch 1787784312
- **17 / 17 candidates RESTORED+VERIFIED**, every stratum: single/multi ×
  early/mid/late, `large` (4.70 GB / 21 dblocks), **`vmimage` (63.86 GB / 201
  dblocks — the win10 VDI, half the set's dblocks)**, `empty`, `symlink-target`,
  `symlink`
- **dblock coverage 245 / 405**
- **live-source oracle: 16 matches, 0 contradictions** (floor for PASS: 10)
- `RESULT: fileset verified restorable for the sampled strata (dual oracle)`

**Plan §7 criterion 6 is CLOSED**, and criterion 5's §8.10.2 failure candidate is
retired by the same move — the destination is now on the only fstab-managed
backup-class filesystem on the host. Criterion 5 itself remains open until an
actual reboot exercises it (§8.7).

#### 8.13.5 Phase C — Tier 2 group 1 executed; group 2 deliberately NOT

`util/ad-hoc/yamaguchi_retire_tier2.bash`, all five gates re-probed live and
passing: TargetURL is the new destination · 813 volumes there · newest run
`Success` · **a drill at that destination with all 17 candidates verified** · no
task active.

Executed (`--execute`, group 1): `/media/pcalnon/temp_backups/Ubuntu` (51 G, the
old gpg fresh set) and `~/.config/Duplicati/DQRVQNDIFX.sqlite{,-wal,-shm}`
(353 M). **sdc4: 346 G used / 20 % → 295 G used / 17 %.** Verified untouched
afterwards: the old archive on sda1 (5,366 `.gpg` volumes at its root),
`_drill_scratch/` (35 G, Tier 3), `_yamaguchi_check/`, and the sdc4 Yamaguchi
copy.

**Group 2 — the 196 G sdc4 Yamaguchi copy — was NOT executed, and the
recommendation is to keep it.** §8.6-8 step 5 says to keep it *until* the drill
passes, which is a floor, not an instruction to delete afterwards. Now that the
drill has passed, that copy is no longer scaffolding: it is a **second,
independently decrypt-validated, complete copy of the live set on a different
physical disk** — which is materially what §8.11.2 option (c) was asking for.
Deleting it would reduce redundancy to buy 196 G on a filesystem that currently
has **1.5 T free**. There is no space pressure to spend it on. Paul's call;
`--execute-old-destination` is the flag if he wants it gone.

Note that the two copies now diverge by design: sdc4 is frozen at the
pre-migration state (811 volumes, fileset `…181206Z` still present), while sda1
is live (813 volumes, `…181206Z` thinned by the proof run). The sdc4 copy is a
point-in-time snapshot, not a mirror, and will not track further runs.

#### 8.13.6 A gate of mine that was vacuous, found before it was trusted

`yamaguchi_retire_tier2.bash`'s gate 4 originally accepted the drill if **any**
candidate carried `verdict: VERIFIED`:

```bash
if grep -qE '"verdict"[[:space:]]*:[[:space:]]*"(PASS|VERIFIED)"' "$rj"; then DRILL_OK=1; fi
```

`results.json` is a JSON **list** of per-candidate objects, so a drill of 1 pass
and 16 failures would have satisfied that grep — and authorised deleting the last
fallback on the strength of a failed drill. Caught while inspecting the real
`results.json` to confirm the gate would fire, i.e. before it was ever relied on.
The check is now **total**: parsed in python, requiring a non-empty list in which
every entry is `VERIFIED`/`PASS`, and printing `all N candidates verified`.

This is the same failure class as §8.13.2 in a different costume — a check that
returns a confident answer without actually checking the thing. There it was a
path frozen at authoring time; here it was an existential test standing in for a
universal one. Both produce clean, plausible output while being wrong.

#### 8.13.7 What remains

- **Criterion 5** — still open; needs an actual reboot. The §8.10.2 mechanism is
  retired for the destination, but `--tempdir` remains on the non-durable sdc4
  (§8.13.3), and `loginctl show-user pcalnon -p Linger` plus the watchdog timer
  need re-checking after the reboot.
- **`--tempdir` residual** (§8.13.3) — Paul's call; recommendation (iii), `/home`.
- **Group 2** (§8.13.5) — Paul's call; recommendation: keep.
- **Today's drill `restored/` tree** (~64 G under
  `_yamaguchi_drill/drill-20260826-175815/restored/`) — the same Tier-1 class Paul
  already approved, but created after that approval. Freeable on a go; the run
  dir's `results.json` / `drill-meta.json` / `provenance.txt` must stay.
- Unchanged and still root-gated: loopback restage (§8.6-6), server-brain backup
  (§8.6-7), the old-archive tail.

---

### 8.14 Addendum (2026-08-28) — the first scheduled run from sda1; three more stale-path tools; `--tempdir` moved

Written from a live session the morning after §8.13. Two of its open items are now closed by
Paul's decisions, and the §8.13.2 defect class turned out to have three more instances that
the previous session's grep instruction was pointing at but did not follow through.

#### 8.14.1 The 2026-08-27 run — criterion 6 now has *scheduled-path* proof

§8.13 closed criterion 6 on a **proof run** that was started by hand. The 08-27 run is the
first one the **timer** drove at the new destination, and it is the stronger evidence:

| | 08-26 proof run (manual) | **08-27 scheduled run** |
|---|---|---|
| Started by | hand | the schedule — `Schedule.LastRun` advanced to `2026-08-27T14:00:00Z` |
| Result | Success, 9 m 31 s | **Success, 9 m 03 s** |
| Uploaded | 198,609,655 B / 3 files | 167,073,415 B / 3 files |
| Verification | `TestResults: Success on 3 file(s)` | `TestResults: Success on 3 file(s)`, 0 warnings, 0 errors |
| Retention | thinned `20260826T131206` | thinned `20260826T174512`, `DeletedSets` = 1 |
| Census | 813 / 210,486,704,937 B AGREE | **815 / 210,590,946,931 B — `-> AGREE`** |

The manual run advanced nothing and so proved only that the destination *worked*; this one
proves the **scheduled path** works from sda1 unattended, and it supersedes §8.10.1's "treat
~12–16 min as the new steady-state class" outright.

**A correction to §8.13's "under 10 minutes", made by the very next run.** The 08-28 scheduled
run — the first to use the new tempdir (§8.14.4) — took **10 m 27 s**, so "under 10 minutes" is
not a floor that every run clears. It is not a regression either, and the two runs together say
something more useful than either alone:

| | 08-27 | 08-28 |
|---|---|---|
| Added files | 429 | **18,151** (42×) |
| Modified / deleted | 422 / 78 | 992 / 2,447 |
| Uploaded | 167 MB | 310 MB |
| Duration | 9 m 03 s | **10 m 27 s** |

**42× the added-file churn cost about 1.5 minutes.** The run is dominated by the ~786 k-file scan
and the ~587 MB post-backup verification download, not by the work the churn creates, which is why
the duration is so insensitive to it. The honest class is therefore **~9–10.5 min, scan-bound**,
and a run drifting well outside that band is a signal worth reading rather than noise.

Retention did not thin on 08-28 (`DeletedSets=[]`) and the destination now carries **4 dlists**.
That is correct, not drift: `1W:1D` keeps the earliest fileset per 1-day interval plus the newest,
and 08-25/08-26/08-27/08-28 are four distinct days inside the 1-week window.

The watchdog independently corroborates it: the `yamaguchi-watchdog.timer` fired **on its own
schedule** for the first time at `2026-08-27T12:00:04-0500` and logged
`OK backup=2 newest run 2026-08-27T14:00:00.1584685Z ParsedResult=Success age=3.0h`. §8.9
closed criterion 4 on a hand-run of the unit; this is the timer proving itself.

Cross-witness from a second, independent tool (`duplicati_dlist_query.py` against the newest
dlist, `20260827T140000Z`): `IsFullBackup=True`, 771,048 File entries / 285,427,701,894 B —
**exactly** the server's `SourceFilesCount` / `SourceFilesSize` — and exactly one `.vdi` entry
(the static win10 image), so the win11 exclusion of §8.9 is still holding three runs later.

#### 8.14.2 Three more tools carried the pre-migration path — and one of them is the drill

§8.13.2 fixed `yamaguchi_census.py` and `yamaguchi_watch.bash`, and ended with the right
instruction: *"Grep `util/ad-hoc/` for `temp_backups/Yamaguchi` before trusting any other
tool."* Doing that turns up **three more**, none of which §8.13 fixed:

| tool | stale thing | why it matters |
|---|---|---|
| `duplicati_drill_fresh.py` | `--dest` default | **The restore drill.** The arc's highest-value check. |
| `duplicati_dlist_query.py` | `--dest` default + hardcoded `ismount()` guard | Answers "what is in the backup?" about the wrong set. |
| `yamaguchi_build_job.py` | `TargetURL`, `--tempdir`, record dir | Re-running it creates a **second** job at the retired path. |

Three others match the grep and are **correct**: `yamaguchi_migrate_copy.bash`'s `SRC`,
`yamaguchi_retire_tier2.bash`'s `OLD_DEST`, and `patch_census_derive_dest.py`'s search string
all legitimately name the old location.

The drill is the serious one, and its own comment convicts it. The line directly above the
stale default read:

> `# A bare run against the wrong destination would print a true-looking PASS for the wrong set.`

That was written as a caution about the *other* arguments. After the migration it described
the default itself. And the failure is not loud: the old directory still exists as the frozen
811-volume pre-migration copy, so a bare drill does not error — it drills a real, decryptable,
internally consistent set and PASSes. Worse, that set's newest dlist is `20260826T181206Z`, a
fileset the live set has since **retained away**: a bare drill would have certified as
restorable a restore point the live backup no longer offers.

**The remedy differs from §8.13.2's on purpose.** `yamaguchi_census.py` was fixed by *deriving*
the destination from the job's `TargetURL`, which is right there because census must talk to the
server anyway to reconcile against it. The drill and `dlist_query` are **destination-only**
tools — the drill's requirement 1 is explicit about it — so making them ask the Duplicati server
where to look would couple a disaster-recovery instrument to the service a disaster may have
removed. For those two the remedy is **`--dest` with no default at all**: explicitness cannot
rot, and it costs one argument. `yamaguchi_build_job.py` keeps defaults (it is a builder, not a
checker) but they now name the current destination, and it **refuses by default if a job of
that name already exists** — the duplicate-job hazard was the real one there.

#### 8.14.3 `ismount()` is not a durability check — measured, not theorised

Fixing the drill's hardcoded `ismount("/media/pcalnon/temp_backups")` meant deriving the mount
guard instead. The obvious derivation — walk up to the containing mountpoint, refuse `/` — is
what §8.13.2 used for census, and it is **not sufficient for a tool that writes**.

Testing the new guard with a run root under `/tmp`, the drill **started**: `/tmp` is a genuine
mountpoint, so the guard passed. `/tmp` on this host is **tmpfs, 47 G, RAM-backed**. The drill
began restoring into RAM and **1.5 GB was resident** before the run was killed; a full drill
restores tens of GB, and the machine has 92 G total with 41 G already in use. The run was
killed, its orphaned `duplicati-cli` child killed separately (it does **not** die with its
parent), and both scratch trees removed. The live destination is read-only to a drill and was
never at risk, and the five real drill run dirs are intact.

Three things follow, and all three are now code:

1. A `VOLATILE_FSTYPES` refusal (`tmpfs`, `ramfs`, `devtmpfs`, `squashfs`, `overlay`) on the
   drill's `--run-root`, read from `/proc/mounts`. **"Is a mountpoint" and "is somewhere it is
   safe to write 64 GB" are different questions**, and `os.path.ismount()` only answers the first.
2. A free-space warning below 100 GiB on the run root.
3. The dest and run-root guards are now *separate*. The old single hardcoded guard covered the
   run root only by coincidence — the run-root default happened to live on the filesystem it
   named. Deriving the dest guard alone would have silently **dropped** run-root protection.

This is less a new class than the oldest one in this job rediscovered: `--tempdir` exists on the
Yamaguchi job at all because "the server's default `/tmp` is tmpfs — the run-1 trap". The hazard
was known and documented in `yamaguchi_build_job.py` in August, and the drill — written later,
by the same hand, for the same set — did not carry the lesson across.

#### 8.14.4 `--tempdir` moved to `/home/pcalnon/.cache/duplicati-tmp` (§8.13.3 closed)

Paul's decision: move it off sdc4, to `/home`. Executed 2026-08-28 13:2xZ.

The chosen path is **`/home/pcalnon/.cache/duplicati-tmp`**, not a new `/home` top-level dir,
because it satisfies one more constraint than `/home/duplicati-tmp` does:

- `/home` is **ext4 and fstab-managed** — durable across a reboot, which is the whole point.
- It is **not** the destination spindle: the destination is sda1, `/home` is sdc3.
- It is inside the backup source `/home/pcalnon/` — but **filter 36 already excludes
  `/home/pcalnon/.cache/`**, so the job cannot scan the temp volumes it is writing. No new
  filter, and therefore no second live-config edit, was needed.
- It needs **no root**: `/home` itself is `root:root`, so a top-level dir there would have.

One honest limitation, recorded because the decision's stated rationale was "off the destination
spindle": **`/home` (sdc3) and `/media/pcalnon/temp_backups` (sdc4) are partitions of the same
physical disk** (`sdc`, WD 8 TB). The move buys fstab durability and gets off the deprecated
filesystem, but it does not change which spindle the temp writes land on — they were on `sdc`
before and they are on `sdc` now. The only truly spindle-independent option is `/` on the NVMe
(`nvme0n1p5`, 264 G free). Left as-is: `/home` is what was chosen, it meets the durability
requirement that motivated the change, and it keeps temp churn off the consolidating sda1
destination, which matches the stated mid-term goal.

The edit needed a third editor — `yamaguchi_edit_target.py` does the destination and
`yamaguchi_edit_sources.py` the source list, but nothing edited `Settings`. New
**`util/ad-hoc/yamaguchi_edit_setting.py`** does, generically, with the same passphrase-safe
GET/modify/PUT and the same refusal discipline; the path-specific guards (`--path-value`) are
the three failures above turned into checks. Verified against the live job before the PUT:

- `--value /tmp` → **rc 4**, "not durable storage".
- `--value /home/pcalnon/Development` → **rc 4**, "inside backup source … and no exclude filter covers it".
- `--value /home/pcalnon/.cache/duplicati-tmp` → both guards pass, naming filter 36 as the cover.

`PUT 200`, then **9/9 post-checks PASS**: `--tempdir` is the new value; `TargetURL`, sources,
filter count (44), settings count (10), `encryption-module=aes`, passphrase re-masked,
`Schedule.Time`/`Repeat` and `ProposedSchedule` all unchanged. Record:
`_yamaguchi_check/yamaguchi-config-post-tempdir-move-20260828.json`.

**Proven in flight, not merely configured.** The 08-28 14:00Z run was sampled while it was
executing: **10 `dup-*` temp files in `/home/pcalnon/.cache/duplicati-tmp` and 0 in the old
`_duplicati_tmp/` on sdc4**. The run completed Success (10 m 27 s, census **818 /
210,901,216,426 B AGREE**, `TestResults: Success on 3 file(s)`, 0 errors, 0 retries) and Duplicati
cleaned the new tempdir out behind itself. The old sdc4 `_duplicati_tmp/` is now provably unused
and can be removed at any time.

Note for any future settings edit: Duplicati setting names begin with `--`, so argparse needs
the `=` form — `--name=--tempdir`, not `--name --tempdir`.

#### 8.14.5 A refused run must not leave a trace — `build_job` did

Adding the duplicate-job guard to `yamaguchi_build_job.py` surfaced an ordering defect in it.
The script wrote its redacted config **record** before contacting the server, so the very first
`--dry-run` — which then correctly refused — had *already* overwritten
`_fresh_dlist_check/yamaguchi-config-imported.json`, the provenance record of the original
2026-08-25 import, with a config carrying today's defaults.

Recovered intact from the sda1 records mirror (`_yamaguchi_records/_fresh_dlist_check/`,
6541 B, Aug 25 04:01, still naming `file:///media/pcalnon/temp_backups/Yamaguchi`) — which is
the first time in this arc the records mirror has been *used* rather than merely maintained,
and is the argument for keeping it.

Both halves are now fixed: the record write happens **after** every guard and after the
`--dry-run` return, and it **never clobbers** an existing record (a second import writes a
UTC-stamped filename instead). The general rule: *a tool that refuses should leave the world
exactly as it found it* — and a dry run most of all.

#### 8.14.6 What remains

- **Criterion 5 (reboot)** — still the only unexercised criterion, and it is now *cleaner*: with
  `--tempdir` on `/home`, every path the job depends on is fstab-managed. After the next reboot
  check `duplicati.service` active, job 2 + `ProposedSchedule` present,
  `yamaguchi_destination_durability_check.bash`, `loginctl show-user pcalnon -p Linger` = yes,
  and `systemctl --user is-enabled yamaguchi-watchdog.timer`.
- **Group 2, the 196 GB sdc4 copy** — Paul's decision: **KEEP**. Post-drill it is a second,
  independently decrypt-validated copy on a different physical disk, and sdc4 has 1.5 T free.
  It is frozen at 811 volumes and tracks no further runs, so it ages as a restore point;
  `yamaguchi_retire_tier2.bash --execute --execute-old-destination` removes it when wanted.
- **Old sdc4 `_duplicati_tmp/`** — now provably unused (the 08-28 run wrote only to the new
  tempdir); removable whenever wanted.
- **The drill `restored/` tree** (~64 G) and the old-archive tail — unchanged from §8.13.7.
- **Consolidation onto sda1** is the stated mid-term direction; sda1 is at 74 % / 909 G free
  with the old `.gpg` archive still on it, so the old-archive purge is the decision that
  actually gates it.

### 8.15 Addendum (2026-08-28 evening) — the old-archive purge, made decidable

§8.14.6 ended by naming the old-archive purge as "the decision that actually gates" consolidation
onto sda1, and left it there. This section closes the analysis gap: what the archive *is*, whether
it can still be read, and — the only question that matters — whether any of it is the **last copy**
of something. Two new read-only tools do the work, so the finding is re-derivable rather than
asserted.

#### 8.15.1 What is actually on sda1

`/mnt/Backups/Ubuntu` (sda1, 3.6 T, 74 % used, 908 G free) holds three things at its root: the live
`Yamaguchi/` destination (196 GiB, §8.13), the `_yamaguchi_records/` mirror, and the **old gpg
archive** — 5,366 loose `.gpg` volumes:

| | count | note |
|---|---|---|
| `.dlist` | 10 | the restore points |
| `.dblock` | 2,674 | |
| `.dindex` | 2,682 | 8 more than dblock — see §8.15.5 |
| total | **5,366 files / 2,551,196,522,664 B (2,376 GiB)** | |

Ten restore points spanning **2024-03-04 → 2026-07-11**. The set went cold on 2026-07-11, six weeks
before the live set's oldest surviving fileset (2026-08-25), so the two do not overlap in time at
all: the archive is the *only* record of any state before 2026-08-25.

**Purging it frees 2,376 GiB and takes sda1 from 74 % to roughly 8 %** (~3.2 T free). That is the
whole of what consolidation is waiting on; the 196 GB sdc4 copy Paul chose to keep is not on sda1
and is irrelevant to it.

#### 8.15.2 The expired-YubiKey red herring

`gpg --list-secret-keys --with-colons` shows the RSA-4096 key whose UID reads
`…yamaguchi_gpg2-yubikey…` with validity `e` — **expired 2021-01-09** — and its subkeys resident on
YubiKey serial `D2760001240102010006092583970000`, a *different* card from the current 3a/3c. Read
alone, that says the archive may need a card that no longer exists, and makes the purge look
either urgent or already-moot.

It is not what encrypted these volumes. `gpg --list-packets` on any volume reports:

```
gpg: AES256.CFB encrypted data
gpg: encrypted with 1 passphrase
:symkey enc packet: version 4, cipher 9, aead 0, s2k 3, hash 10
```

`:symkey enc packet` — **symmetric passphrase encryption**. Duplicati's GPG module used a
passphrase, not a recipient key. No key, no card, and no expiry is involved in reading these
volumes. *Trap: on a GPG-encrypted archive, check the packet type before reasoning about keys —
the key listing and the archive can be entirely unrelated, and here the alarming one was.*

#### 8.15.3 The archive is decryptable — proven, not assumed

`util/ad-hoc/old_archive_decrypt_probe.py` decrypts real volumes with `PASSPHRASE_OLD` (from
`~/.config/duplicati-backup/env`, which retains both the current and the old passphrase) and
requires the plaintext to begin with a **Zip magic number** — Duplicati volumes are Zip inside the
GPG envelope, and a passphrase that "succeeds" while emitting garbage is exactly what a bare
exit-code check would wave through.

Result: **4/4 volumes, Zip-verified**, including the newest dlist (94,517,602 bytes of Zip). The
archive is live, readable data — so the purge is a genuine retention decision, not the disposal of
something already lost.

#### 8.15.4 What the purge would actually destroy

`util/ad-hoc/old_archive_coverage_diff.py` decrypts **all ten** old filesets — not just the newest,
because a file deleted in 2025 is absent from the newest fileset and destroyed by the purge just
the same, so a newest-to-newest comparison understates the loss — unions their paths, and diffs
against the live set's newest fileset:

| | files | bytes |
|---|---|---|
| old union (10 filesets) | 3,832,238 | 2.4 TiB |
| live newest | 786,752 | 266.8 GiB |
| **only in old** | **3,263,118** | **2.2 TiB** |
| also in live | 569,120 | 14.9 % of old paths |

The "all ten filesets" choice is not theoretical caution — it is worth a factor of two, and the
tool will show it. Re-run with `--newest-only` and the same archive reports **1.1 TiB across
596,783 orphans, 48.8 % covered**; the union reports **2.2 TiB across 3,263,118 orphans, 14.9 %
covered**. A newest-to-newest comparison would have understated what the purge destroys by half,
and would have made the archive look twice as redundant as it is.

14.9 % coverage looks alarming until the 2.2 TiB is grouped. Every large group is either a
**deliberate exclusion in the live job's own 44 filters** or **content deleted from disk that is
re-obtainable externally**:

| only-in-old group | size | why it is not a loss |
|---|---|---|
| `.local/share/Steam/steamapps` | 883.5 GiB | live filter 37; Steam re-downloads |
| `Development/Llama2/{llama,codellama}` | ~530 GiB | **gone from disk**; published Meta weights, re-obtainable |
| `anaconda3/envs` | 202.6 GiB | **gone from disk** (replaced by miniforge3); reinstallable |
| `StarfieldData` | 122.2 GiB | live filter 39 |
| `Development/python/Juniper/juniper-data` | 96.0 GiB | live filter 42 — the COCO / ImageNet zips; re-downloadable |
| `VirtualBox/win10_vm_2023-04-29.vdi` | 57.7 GiB | **old path**; the VM moved to `VirtualMachines/`, where the live job backs it up as an explicit Source |
| `rust_mudgeon/{juniper,reference,adamo}` | ~40.7 GiB | live filters 1–9 — `target/` and `libs/` build output, regenerable |
| `Downloads` | 24.8 GiB | live filter 29 |
| `.config/Duplicati/*.sqlite` | 23.0 GiB | live filter 41 — the *old job's own database*; self-referential |
| `.cache` | 15.0 GiB | live filter 36 |

The remaining groups are historical versions of files inside directories the live job **does**
cover. That was verified rather than inferred from the absence of a filter — matching the live
newest fileset directly:

| path | entries in the LIVE set |
|---|---|
| `/home/pcalnon/.gnupg/` | 99 |
| `/home/pcalnon/Documents/` | 9,390 |
| `/home/pcalnon/.claude/` | 6,145 |
| `/home/pcalnon/.mozilla/` | 42,310 |
| `/home/pcalnon/Development/rust/rust_mudgeon/` | 4,417 |

`rust_mudgeon` deserves the explicit note: it is a **live 46 GB project on disk**, and its source
is fully covered — only the nine `target/` and `libs/` paths are excluded, which is why its
orphaned bytes are build artifacts rather than code.

**Verdict: nothing in the old archive is the last copy of irreplaceable data.** The two groups
whose only copy it holds — the Llama-2 / CodeLlama weights and the `anaconda3` environments — are
both re-obtainable from upstream. The archive's entire residual value is **point-in-time history
for 2024-03-04 → 2026-07-11** on paths the live set already covers in their current form.

#### 8.15.5 The dblock/dindex asymmetry, and the trap under it

2,674 dblock vs 2,682 dindex is an 8-file gap, and the obvious move — set-diff the GUIDs in the
filenames — is **wrong**. A dindex is named with its *own* random GUID (`duplicati-i<guid>`),
not the GUID of the dblock it indexes (`duplicati-b<guid>`); the association lives inside the
encrypted index. The two name sets are drawn from independent identifier spaces, so a filename
diff would have reported ~2,674 "missing" volumes on either side and meant nothing.

Attributing the 8 requires decrypting all 2,682 indexes and reading which dblock each names. That
was not done: the gap is consistent with ordinary orphaned indexes from compaction or an
interrupted run, and it does not change the decision — 8 indexes cannot make 2.2 TiB of
deliberately-excluded and externally-re-obtainable content into a loss. *Trap: two counts differing
by a small number invites a set-diff; check first that both sets are drawn from the same
identifier space.*

#### 8.15.6 The decision, for Paul

The technical blocker is gone: the archive is readable, and purging it loses no irreplaceable
data. What is left is a retention preference, and it is genuinely a preference:

- **(a) Purge it.** Frees 2,376 GiB, sda1 74 % → ~8 %, consolidation unblocked immediately, and
  Tier 3 (`_drill_scratch/`, 35 GB) unblocks with it. Costs every restore point before
  2026-08-25 — including the ~530 GiB of Llama-2 weights, which are re-obtainable but not
  *conveniently* so (Meta license request, then a large download).
- **(b) Purge selectively.** Delete the volumes and keep nothing but the 10 dlists (~978 MB
  total) as a *record* of what existed when — the file lists stay queryable forever, the bytes
  go. This does not preserve restorability of anything; it preserves the manifest. Cheap, and
  it makes any future "was X ever on this machine" question answerable.
- **(c) Extract first, then purge.** Restore just `Development/Llama2` (~530 GiB) to a holding
  location, then purge. Only worth it if re-downloading the weights is considered painful; it
  spends 530 GiB of the 2,376 GiB being reclaimed.
- **(d) Keep it.** Consolidation stays blocked. Note the archive is *cold* — nothing has written
  to it since 2026-07-11 and nothing will, so it will not improve with age.

**Recommendation: (b).** It captures essentially all of (a)'s space at a ~978 MB cost, and the
one thing a purge genuinely destroys that cannot be reconstructed — the *knowledge* of what was
on the machine between 2024 and 2026 — is exactly what the dlists preserve. If the Llama-2
weights matter, (c) layers onto it.

Nothing has been deleted. Every number above is re-derivable:

```bash
python3 util/ad-hoc/old_archive_decrypt_probe.py --try-current
python3 util/ad-hoc/old_archive_coverage_diff.py --depth 6 \
    --dump-orphans /home/pcalnon/.cache/old_archive_orphans.tsv
```

The second takes ~10 minutes (ten dlist decrypts); `--dump-orphans` writes every orphan as
`size<TAB>path` so that later questions are a `grep`, not another decrypt pass.

### 8.16 Addendum (2026-08-28 evening) — option (b) executed; the purge is done

Paul picked **option (b)** from §8.15.6: delete the archive's data volumes, keep its ten dlists as
a permanently queryable record. Executed by `util/ad-hoc/old_archive_purge.py`, which is dry-run by
default and re-proves every claim §8.15 made rather than trusting the note — this deletes 2.3 TiB
and cannot be undone.

#### 8.16.1 The caveat that had to be closed first

§8.15 was written knowing the dlists *decrypt*, but it had **not** been tested that a dlist stays
readable once its dblock volumes are gone. The entire value of option (b) rests on that, so
asserting it would have been the same error this arc keeps finding: a check that passes because it
never really ran.

It was proven on a copy first, and then made **gate 5** of the purge tool so it can never be
skipped: one dlist, alone in a directory with **zero dindex and zero dblock**, was queried and
yielded its full **1,360,811-entry** listing. A dlist is self-contained. (What it cannot do is
restore — the file data is gone. It answers *what existed, how big, and when*.)

That probe also produced a correction worth keeping. A first match for
`/Development/Llama2/llama/llama-2-70b/` against the newest dlist returned **0 entries**, which
reads as "the record is broken". It is not: the Llama-2 weights were deleted from disk *before* the
final 2026-07-11 fileset, so they appear only in **earlier** ones (223 orphan paths, confirmed
against the dumped orphan list). Verified by matching a path that *is* in the newest fileset —
`rust_mudgeon/adamo/Cargo` → 3 entries with sizes and timestamps. **This is why option (b) keeps
all ten dlists and not just the newest**, and why a zero-result match must be checked against a
known-present control before it is believed.

#### 8.16.2 Gates, all eight passed

| gate | assertion |
|---|---|
| 0 | archive root on `/dev/sda1`, **fstab-managed** |
| 1 | `ActiveTask=null`, scheduler queue empty |
| 2 | live `TargetURL` is the `Yamaguchi/` **subdirectory** — what makes a non-recursive root delete safe |
| 3 | live set reconciles: filesystem **818 files / 210,901,216,426 B** = server `TargetFilesCount`/`Size` |
| 4 | all **10** dlists decrypt **and are Zip** |
| 5 | isolated dlist (0 dblock, 0 dindex) yields **1,360,811 entries** |
| 6 | deletion set is exactly **5,356** root-level volumes (2,674 dblock + 2,682 dindex); **0 dlists**, 0 paths under `Yamaguchi/` or `_yamaguchi_records/`, asserted explicitly rather than inferred from the glob |
| 7 | the 10 dlists mirrored to `/media/pcalnon/temp_backups/_old_archive_dlists` on **`/dev/sdc4`** — a different physical disk — and **sha256-verified** before anything was deleted |

Gate 2 deserves the note: the live destination being a *subdirectory* of the archive mountpoint
(§8.13) is the only reason a root-level delete is safe at all. If the live job ever pointed at the
root itself, the tool refuses.

#### 8.16.3 Result

```
deleted 5356/5356 volumes, freed 2.3 TiB
kept 10 dlists + README.md
```

| | before | after |
|---|---|---|
| sda1 used | 2.6 T (**74 %**) | 198 G (**6 %**) |
| sda1 free | 908 G | **3.3 T** |
| archive root | 5,366 `.gpg` files | 10 dlists (933 MiB) + `README.md` |

Verified after the fact, not assumed:

- **Live set unaffected** — census `818 files / 210,901,216,426 B -> AGREE`.
- **The record works with the volumes actually gone** — querying
  `--dest /mnt/Backups/Ubuntu` now reports `10 dlist / 0 dindex / 0 dblock` and still returns the
  full 1,360,811-entry fileset and answers path queries.
- `_yamaguchi_records/`, `lost+found/` and `temp/` untouched (they are directories; the deletion
  set was root-level *files* only).
- The sdc4 mirror holds all ten, 934 MB.

A `README.md` was written at the archive root recording what was removed, what is kept, that the
dlists cannot restore, that all ten must be kept, the exact query command, and where the second
copy lives — so the next reader does not have to find this note first.

#### 8.16.4 What this unblocks, and what is left

**Consolidation onto sda1 is unblocked** — 3.3 T free, the stated mid-term goal. Tier 3
(`_drill_scratch/`, 35 GB) is no longer gated. The 196 GB sdc4 `Yamaguchi/` copy is unaffected and
remains KEEP per Paul's §8.14 decision.

Still open, unchanged: **criterion 5 (reboot)** — now the last unexercised criterion in the whole
arc; the old sdc4 `_duplicati_tmp/` (empty, removable); the drill `restored/` tree (~64 G); and the
root-owned items (loopback restage, server-brain DB backup).

### 8.17 Addendum (2026-08-29) — Tier 3 retired; consolidation verified; only root/reboot work remains

With the purge done (§8.16), the two items it was gating were executed and the sda1 consolidation
claim was checked rather than assumed. After this section **every remaining item in the arc is
root-owned or reboot-gated**, which is why the successor handoff exists.

#### 8.17.1 Consolidation: the records mirror was already current

The 2026-08-28 handoff stated the sda1 records mirror "has NOT been re-synced since (run
`yamaguchi_records_sync.bash`)". Running it produced **no output at all** — rsync
`--itemize-changes` transferred nothing. Silence from a sync is exactly the shape of a vacuous pass,
so it was checked directly instead of believed: **73 evidence files on each side, identical path
lists, and the newest drill's `results.json` byte-identical (`cmp`)**. The mirror was already
current; the handoff's claim was stale. Recorded because the next reader will otherwise re-run it
expecting work.

This is what "consolidation onto sda1" actually amounts to for evidence: sdc4 is **not
fstab-managed**, so anything whose only copy is there is on a mount that does not come back after a
reboot. The durable copy is the sda1 mirror, and it is current.

#### 8.17.2 Tier 3, and why the purge had to come first

`_drill_scratch/` was never generic scratch: it is **35 GB of temporary SQLite databases built by
the 2026-08-23 drill to index the very volumes §8.16 deleted** (13.2 GB + 17.3 GB + a 6.9 GB WAL +
shm). While the archive existed those DBs were a plausible shortcut for re-drilling it; with the
volumes gone they index nothing. That is the real reason Tier 3 was gated on the purge decision, and
`yamaguchi_retire_tier3.py` **enforces** it as gate 3 (refuses while any `.dblock`/`.dindex` remains
at the archive root) rather than trusting the ordering.

Executed 2026-08-29, seven gates green:

| deleted | size |
|---|---|
| `_drill_scratch/*.sqlite*` (4 files) | 34.8 GiB |
| `_yamaguchi_drill/drill-20260826-175815/restored/` | 63.9 GiB |
| `_duplicati_tmp/` (empty since §8.14) | — |
| **total** | **98.7 GiB** |

**sdc4: 296 G used (17 %) → 197 G (12 %), 1.6 T free.** The live set was re-checked afterwards:
`818 files / 210,901,216,426 B -> AGREE`.

#### 8.17.3 What was preserved, and the silent loss that was nearly shipped

`_drill_scratch/restored/` held **nine restored sample files** (`good/` and `damaged/`) from the
old-archive drill — 264 KB, and now the **only surviving artifact of a drill whose archive no longer
exists**. The standing `yamaguchi_records_sync.bash` syncs `_yamaguchi_check`, `_fresh_dlist_check`,
`_yamaguchi_drill` and `_fresh_drill` — **not `_drill_scratch`** — so a `rm -rf` of the directory
would have destroyed them without any tool noticing. Gate 5 copies them to
`_yamaguchi_records/_drill_scratch/restored/` on sda1 and verifies the count before the deletion
proceeds. *A retirement tool must check what the standing sync does **not** cover; "the records are
mirrored" is a claim about four named directories, not about the disk.*

Gate 4 required all five drill evidence files (`results.json`, `drill-meta.json`, `provenance.txt`,
`candidates.json`, `restore-all.log`) to exist on **both** spindles and be **byte-identical** before
`restored/` was touched — because `yamaguchi_retire_tier2.bash` reads that same `results.json` as
*its* gate 4, so deleting it would have silently disarmed a different tool. Confirmed still armed
afterwards: tier 2 re-run reports `gate 4 PASS` on the same path.

#### 8.17.4 Two stale items corrected

- **§7's "loopback interface is already staged in `/etc/default/duplicati` pending restart" is no
  longer true.** The file now reads `DAEMON_OPTS="--webservice-interface=any --webservice-port=8300
  --portable-mode"` — Paul restored that at 14:14 on 2026-08-25 to close the restart trap (§2), which
  overwrote the staged loopback. Loopback hardening is therefore an **open decision requiring a root
  edit plus a restart**, not a change waiting to take effect.
- **The superseded user-lane service fails safe.** `duplicati-backup.timer` is `disabled`, but the
  unit files remain and could be started by hand. Its runner defaults to
  `DEST_PATH=/media/pcalnon/temp_backups/Ubuntu` (retired in Tier 2 group 1) and
  `TEMP_DIR=/media/pcalnon/temp_backups/_duplicati_tmp` (deleted above); both are now absent, and the
  runner's own guard `[[ -d "${DEST_PATH}" ]] || fail` refuses before writing anything. No action
  needed — recorded so nobody "fixes" the paths and re-arms a lane that is 0-for-3.

#### 8.17.5 The arc's remaining surface

| item | why it is not done |
|---|---|
| **Criterion 5 (reboot)** | deferred by Paul 2026-08-29; the last unexercised acceptance criterion |
| **Loopback hardening** | root edit of `/etc/default/duplicati` + restart |
| **Server-brain DB backup** | the job DB lives at `/usr/lib/duplicati/data/` — root-only, and **outside every backup Source** (`/home/pcalnon/` + one VDI), so it is in no backup at all |

> **Superseded by [§8.18](#818-addendum-2026-08-29--the-key-to-the-backup-is-excluded-from-the-backup).**
> The sentence below was true of the *retirement* work and false of the arc. A validation pass on
> this section's successor handoff found that the backup's own passphrase is excluded from the
> backup and shares a physical disk with the sources — an item that outranks all three rows above.
> Read §8.18 before treating this table as the remaining surface.

Every retirement tier is executed, both destinations reconcile, the watchdog is armed, and the
record of the purged archive is on two spindles. Successor handoff:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-29_duplicati-reboot-and-root-tail.md`.

### 8.18 Addendum (2026-08-29) — the key to the backup is excluded from the backup

Found by the multi-agent validation pass on the §8.17 successor handoff, not by the arc's own
checks. It outranks every item §8.17.5 listed, and **§8.17.5's "Nothing else is outstanding" is
superseded by this section.** It is recorded here, in the note, because a finding that lives only in
a session handoff does not survive the handoff.

#### 8.18.1 The finding

| what | path | device |
|---|---|---|
| backup **Sources** (2) | `/home/pcalnon/` and `…/VirtualMachines/VirtualBox/win10_vm_2023-04-29/win10_vm_2023-04-29.vdi` | **sdc3** |
| **the passphrase file** | `/home/pcalnon/.config/duplicati-backup/env` (388 B, 0600) | **sdc3** |
| frozen second copy (196 GB) + `_old_archive_dlists/` mirror + drill evidence | `/media/pcalnon/temp_backups/` | **sdc4 — the same physical disk, `sdc`** |
| destination (210 GB of AES ciphertext) | `/mnt/Backups/Ubuntu/Yamaguchi` | sda1 |

`env` holds `PASSPHRASE` — the AES key for the entire destination — and `PASSPHRASE_OLD`, the only
key to the ten retained dlists that are now the sole record of the purged 2.3 TiB archive (§8.16).
**Live filter 43 (`Include: false`) excludes `/home/pcalnon/.config/duplicati-backup/`**, so the key
is not in the backup that it unlocks.

Consequence: **losing the physical disk `sdc` — the failure this backup exists to survive — takes
the sources, the frozen second copy, the dlist mirror and the key in one event.** The arc has
certified restores, run drills, censused volumes, deployed a watchdog and executed a purge without
ever asking where the key lives.

**Stated precisely, because the obvious phrasing overstates it.** It is *not* true that "nothing
surviving can open the ciphertext" — §8.18.2 describes a route that does, and an earlier draft of
this section contradicted itself two paragraphs apart. The defensible claim is:

- **`PASSPHRASE` survives an `sdc` loss only as root-only material inside an unbacked-up database**
  (`Duplicati-server.sqlite` on `/`). That is a single, unreplicated, unmonitored copy — not an
  escrow.
- **`PASSPHRASE_OLD` has no surviving out-of-band copy at all.** Its job no longer exists in the
  server, so the DB does not carry it; it is recoverable only *through* `PASSPHRASE`, by restoring
  the stray `.env` from the backup (§8.18.2).
- Therefore a single additional failure — that DB lost or unreadable — makes both keys
  unrecoverable and the 210 GB destination permanently opaque.

**Trap:** §8.8 wants the stray `.env` swept as secrets sprawl. Doing so **removes the only in-backup
copy of `PASSPHRASE_OLD`**. Escrow first, sweep second.

Re-derive with `python3 util/ad-hoc/yamaguchi_config_record.py --out <file>` (44 filters, 2 sources;
filter 43 is the exclusion). `yamaguchi_server_api.py export` currently fails `400`; the
`GET /api/v1/serversettings` endpoint returns **200** through the tool's own login path.

#### 8.18.2 Two partial mitigations that exist by accident, and neither is sufficient

- **`Duplicati-server.sqlite`** (`/usr/lib/duplicati/data/`, root-only, on `/` = nvme0n1p5) holds the
  job definition, filters, schedule **and the passphrase — in CLEARTEXT, corrected 2026-08-30, see
  §8.20; this bullet originally said "encrypted"**. It is on a different physical
  disk from `sdc`, so it is the one artifact that survives an `sdc` loss carrying key material — but
  it is root-only, in no backup, and **Recreate does not restore it** (Recreate rebuilds only
  `BMXWPAOGLP.sqlite`, the per-job index). §8.6-7's recipe copies it to
  `/mnt/Backups/Ubuntu/_yamaguchi_records/`, which is on sda1 and **is not a backup Source** — so
  running that recipe verbatim leaves "the brain is in no backup" exactly as true as before.
- **The stray `…/juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env`** (114 B, Aug 23,
  §8.8, never reconciled) carries `export PASSPHRASE=` and `export PASSPHRASE_OLD=` in cleartext,
  sits inside Source `/home/pcalnon/`, and is matched by no filter — so the backup does contain a
  copy of both passphrases, encrypted under `PASSPHRASE`. That makes `PASSPHRASE_OLD` recoverable
  from the backup and `PASSPHRASE` **not**: it is the one secret its own copy cannot rescue. The file
  is git-ignored, so `git worktree remove` deletes it **silently** — do not sweep that worktree
  before §8.8's reconciliation.

#### 8.18.3 What has to happen (owner decision)

Agree an escrow for `PASSPHRASE` that is **off `sdc` and outside the ciphertext** — an offline or
printed copy, and/or a copy on sda1 — and decide whether `Duplicati-server.sqlite` gets an automated
root-owned copy into a non-excluded path (a one-shot decays: the DB advances every run). A headless
session cannot do either: `/usr/lib/duplicati/data/` is `drwx------ root root` and `sudo -n true`
fails with `interactive authentication is required`.

Do **not** "fix" this by moving the key inside a Source — that puts the key inside the archive it
unlocks, which is the same circularity in a new place.

#### 8.18.4 A related exposure, same validation pass

`remote-control-enabled = True` with `additional-report-url = https://ingress.duplicati.com/backupreports/…`
— backup reports are being sent to Duplicati's cloud service. Separately, the server DB already
stores `server-listen-interface = loopback`; the command line in `/etc/default/duplicati` is what
overrides it, so the loopback hardening of §7 may be a *deletion* of `--webservice-interface=any`
rather than an addition. **The commented-out line in that file omits `--portable-mode`**, so
activating it by swapping comment markers reproduces the §2 restart trap — edit the active line in
place.

### 8.19 Addendum (2026-08-29 afternoon) — the four owner decisions, and the half of them a headless session could execute

§8.18 ended by naming an owner decision. It was taken the same day. This section records the
decisions, what was executed and verified against them, and what is still gated on root.

#### 8.19.1 The decisions

| § | Question | Decision |
|---|---|---|
| 8.18.3 | Where does the `PASSPHRASE` escrow live? | **Both** — an offline/printed copy *and* a copy on sda1 |
| 8.18.2 | How is `Duplicati-server.sqlite` protected? | **Automated root-owned copy** into a non-excluded path |
| 8.18.4 | How far to narrow the web service? | **Narrow bind only** — leave cloud reporting alone for now |
| 7 (crit. 5) | Reboot? | **Prepare it; the owner reboots on his own schedule** |

#### 8.19.2 Escrow — the sda1 half is DONE, the offline half is not

`util/ad-hoc/yamaguchi_key_escrow.py --execute` wrote
`/mnt/Backups/Ubuntu/_yamaguchi_keys/env` (388 B, mode 0600, in a 0700 directory), sha256
`96ab727c…a74a`, **verified byte-identical to the source** by an independent `sha256sum` of both
files. A `README.md` beside it states the accepted limitation in place.

The tool's value is not the copy — `cp` could do that — it is three gates that encode the failure
being defended, each **demonstrated to fire** rather than merely present:

| Gate | Refuses | Why it is not decoration |
|---|---|---|
| inside a Source | `--dest-dir /home/pcalnon/…` | escrowing into a Source puts the key inside the archive it unlocks |
| same filesystem | any dest whose `st_dev` matches the source's | a copy on the same filesystem is not an escrow |
| **same physical disk** | `--dest-dir /media/pcalnon/temp_backups/…` | **`st_dev` separates sdc3 from sda1 but NOT sdc3 from sdc4** — the "second copy" that is not a second disk is exactly the trap §8.18 names, and only a `/sys/class/block` parent-device lookup catches it |

Gate ordering is itself load-bearing and was corrected during the session. With the
same-filesystem check first, every `/home/pcalnon/...` destination was swallowed by the vaguer
"same filesystem" message and the specific "inside a Source" error was **unreachable**. The
string test now runs first.

The printable sheet lands at `~/.cache/yamaguchi-key-escrow-sheet.txt` (mode 0600). `.cache/` is
**filter 36**, so the plaintext sheet is excluded from the job by construction — writing it
anywhere else under `/home/pcalnon/` would have put both passphrases into the archive in the clear.

> **The escrow is HALF DONE.** The offline copy requires a human at a printer. Until the sheet is
> printed, stored away from the machine, and `shred -u`'d, the only escrow is the sda1 copy — which
> sits beside the ciphertext it unlocks and does not survive losing sda1. **`PASSPHRASE_OLD` still
> has no copy outside `sdc` + sda1.**

#### 8.19.3 Server DB — tooling built, deployment gated on root

`util/ad-hoc/yamaguchi_server_db_snapshot.py` + `util/systemd/yamaguchi-server-db-snapshot.{service,timer}`
+ `util/ad-hoc/yamaguchi_server_db_deploy.bash`.

Destination `/home/pcalnon/.local/state/duplicati-server-db/` was **verified against all 44
filters** — the job has **zero include filters and 44 excludes**, so everything under
`/home/pcalnon/` is captured except those 44 paths; the nearest neighbours are filter 36
(`.cache/`) and filter 37 (`.local/share/Steam/`), neither of which covers `.local/state/`.

Three things worth keeping:

- **`sqlite3.backup()`, not `cp`.** The server is running and writing. A byte copy of a live SQLite
  file can land mid-transaction and restore as a corrupt DB **that still opens**. The snapshot is
  then proved with `PRAGMA integrity_check` *before* it replaces the previous good one.
- **The timer is pinned to UTC, and that is not cosmetic.** `OnCalendar` defaults to *local* time
  while the backup schedule is fixed at 14:00**Z**. A local `08:45` sits 15 min *before* the backup
  under CDT and 45 min *after* it under CST — so at the next DST change the snapshot would silently
  start missing its own backup by a day, with no error anywhere. `13:45:00 UTC` holds year-round.
  Both forms resolve identically *today*, which is precisely why the bug would be invisible now.
- **This is not key escrow and must not be mistaken for it.** The archive the DB is copied into is
  encrypted with the very key one would be trying to recover. It is a circle. §8.19.2 is the control
  that breaks it; this one restores the *job definition and index*.

  > **CORRECTED 2026-08-30 (§8.20).** This bullet originally opened "The passphrase inside this DB
  > is encrypted, and…". **It is cleartext.** The circularity conclusion still holds — it rests on
  > the *archive* being encrypted, not the DB — but the premise was false, and it was written by the
  > session that built the snapshot. Treat the snapshot as key material.

A defect was found in this tool by running it: as an unprivileged user it reported
`source DB missing`, because `/usr/lib/duplicati/data` is `drwx------ root root` and
`os.path.isfile()` on a perfectly present DB returns `False`. That is a **fail-into-plausible**
read — it would send an operator hunting for a deleted file instead of prefixing `sudo`. It now
distinguishes `PermissionError` from `FileNotFoundError` and says so.

#### 8.19.4 Narrow bind — tooling built, execution gated on root

`util/ad-hoc/yamaguchi_narrow_bind.bash`. Two premises were verified rather than assumed:

- **The edit will take effect.** `duplicati.service` is `EnvironmentFile=-/etc/default/duplicati`
  with `ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS`, and the live process cmdline is
  `--webservice-interface=any --webservice-port=8300 --portable-mode` — exactly the active line.
- **Deleting the flag is sufficient.** `GET /api/v1/serversettings` returns
  `server-listen-interface = loopback` **already stored in the DB**. The command line is what
  overrides it, so the fix is a *deletion*, not an addition.

**The §2 restart trap now has a stated mechanism.** Both databases live in
`/usr/lib/duplicati/data/` — the *portable* location. Drop `--portable-mode` and the server looks
in root's profile instead, finds no job, and comes up **empty**: no Yamaguchi backup, no schedule,
no history. It presents as total loss and is merely a wrong data directory. That is why the
commented line in `/etc/default/duplicati` — which omits `--portable-mode` — must never be
activated by swapping comment markers. The script edits the **active line in place**, asserts
`--portable-mode` survived and the interface flag is gone, and **rolls back from a timestamped
backup** if either assertion fails. The `sed` was proved on a copy of the real file: the active
line is rewritten, the commented trap line is untouched.

Restart is opt-in (`--restart`) and refuses unless `ActiveTask` is null.

#### 8.19.5 Reboot — script written and validated end-to-end

`util/ad-hoc/yamaguchi_reboot_verify.bash pre|post`. Both lanes were **executed** on the live
(un-rebooted) system, so every code path has run; `post` returned `PASS` and its forced watchdog run
refreshed `server-watchdog.status` from `12:00:54` to `15:42:46`.

> That `PASS` validates **the script**, not criterion 5. Nothing has rebooted.

The file carries the two traps that make the naive version of this check worthless:

- `systemctl --user is-enabled` and `loginctl … Linger` **cannot fail because of a reboot** — they
  read a symlink and a persisted file respectively. They test configuration, not survival. The real
  evidence is that `systemctl --user` **connects at all**.
- "`LAST` is after the boot time" is a **false negative on a healthy reboot**: the watchdog timer is
  `OnCalendar=*-*-* 12:00:00 Persistent=true`, so it catches up only if a 12:00 point was crossed
  while down. Reboot at any other hour and `LAST` legitimately stays pre-boot for ~23 h. Hence the
  explicit `systemctl --user start` — `Type=oneshot`, safe on demand.

#### 8.19.6 Residual closed: `_drill_scratch/` is now maintained, not a one-shot

`yamaguchi_records_sync.bash` synced four named directories and excluded `restored/`, so the nine
preserved drill samples that Tier 3 gate 5 placed on sda1 were unmaintained. `_drill_scratch` now
has its own rsync invocation; both sides hold 9 files and a re-run is a no-op.

It is a **separate invocation on purpose**. rsync matches each rule against the path relative to
*each* transfer root, so any `--include=/restored/***` broad enough to rescue
`_drill_scratch/restored` would equally un-exclude `_yamaguchi_drill/*/restored` — re-arming the
copy the exclusion exists to prevent. A second call cannot make that mistake. A 50 MB guard turns a
future large `_drill_scratch` into a loud refusal instead of a silent bulk copy.

Measured while doing it: **the `restored/` exclusion is now vestigial** — Tier 3 deleted the 63.9 GB
it was written to block, and it currently guards ~16 KB across three drill dirs. **It stays**: it is
a standing guard against the next drill recreating a large tree, not a statement about today's sizes.

#### 8.19.7 Expectation drift a fresh session will otherwise misread

The predecessor handoff expects `818 files / 210,901,216,426 B`. The census now reports
**823 files / 212,009,670,891 B** and still reconciles `-> AGREE`. This is the 2026-08-29T14:00Z run
completing (`FilesUploaded=5`; 818 + 5 = 823), not drift. Next run `2026-08-30T14:00:00Z`.

#### 8.19.8 Still open

1. **The offline escrow copy** (§8.19.2) — needs a human at a printer. Highest remaining consequence.
2. **`sudo bash util/ad-hoc/yamaguchi_server_db_deploy.bash`** — after the primary checkout is synced
   to a `main` containing the script, or every timer fire exits non-zero.
3. **`sudo bash util/ad-hoc/yamaguchi_narrow_bind.bash --restart`**.
4. **Criterion 5** — owner reboots, then `yamaguchi_reboot_verify.bash pre` / `post`.
5. **§8.8's `.env` sha256 reconciliation**, still unreconciled — and still the precondition for
   sweeping `curious-plotting-hummingbird`. Note that §8.19.2 changes its risk: with the sda1 escrow
   in place, sweeping it no longer destroys the only recoverable copy of `PASSPHRASE_OLD`. It is now
   an ordinary secrets-sprawl item.
6. **Cloud reporting** (§8.18.4) — owner-deferred, not rejected. `remote-control-enabled = True` and
   `additional-report-url` embeds a **long-lived bearer JWT** (issuer `api.duplicati.com`, expiring
   2028) — it is a credential, not merely a URL, and should be treated as one if that file is shared.
7. **The disabled `duplicati-backup.*` user lane** (§8.11.3) — removal PR still unopened. The lane
   fails safe; not urgent. Do **not** "repair" its paths.

### 8.20 Addendum (2026-08-30) — the passphrase is cleartext, and two harnesses that break on reboot

Three of §8.19.1's four owner decisions were executed by the owner overnight (items 2 and 3 in full;
item 1's sda1 half on 08-29). A validation pass the next morning found two things the arc had been
carrying wrongly. Handoff:
[`HANDOFF_2026-08-30_duplicati-cleartext-passphrase-and-escrow-tail.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-30_duplicati-cleartext-passphrase-and-escrow-tail.md).

#### 8.20.1 Executed by the owner, verified here

| Item | Evidence |
|---|---|
| **Narrow bind (§8.19.4)** | `/etc/default/duplicati` active line is `DAEMON_OPTS="--webservice-port=8300 --portable-mode"`; rollback file `duplicati.bak-20260830-010814`; journal *"listening on localhost, port 8300"*; `ss` shows only `127.0.0.1:8300` + `[::1]:8300` |
| **Server-DB snapshot (§8.19.3)** | `yamaguchi-server-db-snapshot.timer` `enabled`, next elapse 13:45Z; snapshot on disk 160 KB, `integrity_check` = ok, 16 tables, 0600 in 0700 |

**The §2 restart trap did not fire.** `--portable-mode` survived, the commented trap line is
untouched, and the census still finds job 2 and reconciles `-> AGREE`.

**`ProgramState=Paused` after that restart is not an incident** — `startup-delay=30m`, with
`paused-until = 0` (no manual pause). There was **no reboot**: `journalctl --list-boots` shows one
boot ID spanning 08-16 → 08-30.

**Item 2 is deployed, not yet proven.** The snapshot is inside Source `/home/pcalnon/` and matched by
no filter, so the next 14:00Z run *should* capture it — but that run had not happened when this was
written. Do not mark §8.19.8 item 2 closed until a completed run shows it.

#### 8.20.2 The passphrase is stored in CLEARTEXT — three sections corrected

The value in `Duplicati-server.sqlite` (`Option`, `BackupID=2`, `Name=passphrase`) has the **same
SHA-256** as `PASSPHRASE` in `~/.config/duplicati-backup/env`. Byte-identical to a known plaintext,
so it is not ciphertext. `PASSPHRASE_OLD` is absent from all 16 tables — correct, it is not a
Duplicati setting. `duplicati-server` has announced this on every start all along: *"No database
encryption key was found. The database will be stored unencrypted."*

Corrected in place: **§8.6 item 7** (line 389), **§8.18.2**, **§8.19.3**. The first is the one the
08-29 session quoted for the copy-recipe and read past — a reminder that quoting a section is not
reading it.

**Scoped honestly: the snapshot is not a new leak.** `pcalnon` already reads the passphrase in
cleartext from the `env` file, and the archive already held a cleartext copy via the stray `.env` of
§8.18.2. What changed is the **handling class** of the DB, plus one latent hazard: §8.6-7's recipe
targeted `_yamaguchi_records/` (mode **0775**) rather than `_yamaguchi_keys/` (**0700**). That is
**latent, not live** — the parent `/mnt/Backups/Ubuntu` is 0770 so "other" cannot traverse, and
`pcalnon` is the only human account. A first draft of the handoff called it a live leak "readable by
any local account"; that was false and was caught in validation, which is worth recording because
the predecessor chain had *already* flagged overstatement of exactly this shape.

**Owner decision (2026-08-30): accept as-is and document.** `SETTINGS_ENCRYPTION_KEY` was rejected —
it adds a third key needing escrow and makes the DB unreadable if lost. Excluding the snapshot from
the backup was rejected — it defeats the purpose and the archive holds a cleartext copy regardless.
The recipe target was changed to `_yamaguchi_keys/`.

#### 8.20.3 Both #1319 restore-integrity harnesses refuse to run once sdc4 is unmounted

Never previously recorded anywhere in this note or the ten handoffs.

| File | Line | Gate |
|---|---|---|
| `util/ad-hoc/duplicati_dlist_crosscheck.py` | 113 | `if not os.path.ismount("/media/pcalnon/temp_backups"): fail(...)` |
| `util/ad-hoc/duplicati_decrypt_validate_all.bash` | 26 | `mountpoint -q /media/pcalnon/temp_backups \|\| fail` |

Both gates are **hardcoded and fire regardless of the destination under test** — `--dest` (py) and
`$1` (bash) do not influence them — and both still default to the pre-migration
`/media/pcalnon/temp_backups/Ubuntu`.

This matters because **criterion 5 is a reboot and sdc4 is not in fstab**. After it, the two scripts
that `tests/test_duplicati_restore_integrity.py` exists to pin will refuse against *any* destination,
including the live sda1 backup they validate, with a `FATAL: not mounted` unrelated to the
destination.

It is the **same defect class** §8.13.2 / §8.14.2 already found and fixed in five other tools. It
survived because the sweep used `grep -rn 'temp_backups/Yamaguchi' util/ad-hoc/`, and these two files
contain `temp_backups/`**`Ubuntu`** — the grep structurally could not match them. **Re-run that sweep
against the mount path, not the job name.**

#### 8.20.4 Two §7 items orphaned since the note's first snapshot

Neither is a live hazard, but 19 addenda and ten handoffs have passed without either being closed or
re-asked, so they are recorded here to stop them dissolving:

- the root `duplicati.service` **on 8200 was repurposed to 8300 rather than removed** (line 193);
- the **schema-19 profile server DB** (jobs `Ubuntu` / `Ubuntu-fresh`) is orphaned from any running
  server, openable by 2.3.0.4+ if ever needed (lines 194-195).

*(Guard against a false third: §7's "release-train key in the backup" item **is** closed — §8.9
item 4, "KEEP. No change". A literal-string sweep flags it as orphaned; it is not.)*

#### 8.20.5 Still open

1. **De-drift the two harnesses in §8.20.3** — before the reboot, not after.
2. **The offline escrow copy** (§8.19.2) — still owed. `~/.cache/yamaguchi-key-escrow-sheet.txt` is
   present and unprinted; `.cache/` is filter 36 so it is out of the archive by construction. Until
   it is printed and stored off-machine, `PASSPHRASE_OLD` has no copy outside `sdc` + sda1.
3. **Criterion 5 (reboot)** — `util/ad-hoc/yamaguchi_reboot_verify.bash pre|post` is written and both
   lanes have been executed on the live system; that PASS validates the script, not the criterion.
4. **Confirm item 2's capture** in a completed backup (§8.20.1).
5. §8.8's `.env` reconciliation; 6. cloud reporting (owner-deferred); 7. the disabled user-lane
   removal PR; 8. the two §8.20.4 items.
