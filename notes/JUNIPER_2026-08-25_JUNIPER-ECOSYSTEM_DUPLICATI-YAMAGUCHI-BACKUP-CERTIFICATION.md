# Duplicati Yamaguchi Backup — First Full Backup and Certification

**Project**: Juniper — Backup Infrastructure
**Author**: Paul Calnon (campaign executed by Claude Code session "backup sys work")
**Date**: 2026-08-25
**Status**: CERTIFIED — the arc's first complete, verified restore point
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
