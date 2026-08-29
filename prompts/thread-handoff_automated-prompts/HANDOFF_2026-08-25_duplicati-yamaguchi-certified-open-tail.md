# HANDOFF 2026-08-25 — Duplicati: Yamaguchi CERTIFIED; scope widened mid-handoff; close the acceptance tail

**Continue the backup-restoration arc from its goal state.** The arc that began with the
2026-07-13 archive damage now has **a complete, certified restore point** — the
Yamaguchi set — plus successful same-day incrementals, and (as this handoff was being
validated) a **scope-widening top-up backup launched by Paul** was in flight. What
remains: settle and re-record the widened scope, the acceptance tail (second drill,
reboot survival, alerting, **migration off the source's own spindle**), retirements,
and the old-archive questions.

Predecessor: [`HANDOFF_2026-08-24_duplicati-gpg-failure-and-scheduled-lane.md`](HANDOFF_2026-08-24_duplicati-gpg-failure-and-scheduled-lane.md)
— its §4 items 1–2 closed (investigation + fresh-set certification notes); item 6
superseded as an action **but two of its embedded acceptance criteria are still open
and carried here (§2 items 5, 9)**; items 3–5 and 7 carried in §2 item 11; item 8's
first half (":8200 service removal") is **SUPERSEDED — that unit, now on 8300, IS the
production backup server; never remove it** — only its scratch-deletion half carries
forward. The predecessor's "Loose ends" are individually dispositioned in §2 items
6–10.

Notes of record (read before acting in the corresponding area):
[`…DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`](../../notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md) ·
[`…DUPLICATI-FRESH-SET-CERTIFICATION.md`](../../notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-SET-CERTIFICATION.md) ·
[`…DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`](../../notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md) ·
plan of record [`…DUPLICATI-FRESH-BACKUP-SET-PLAN.md` §7](../../notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md) ·
⛔ [`…DUPLICATI-DB-RESTORE-RUNBOOK.md`](../../notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md)
— still **WITHDRAWN, DO NOT EXECUTE** (retained specimen; its premise is false).

> **Length deviation, declared.** The procedure asks ~500 words; this is ~2,900. Four
> adversarial validators (accuracy, omission/amputation, executability — which ran the
> §6 block live — and cold-start-successor simulation) reviewed the draft and found
> ~30 defects, including one CRITICAL amputation, three claims already stale at the
> draft's own timestamp, and a live operation the draft missed. All material findings
> are incorporated; the length buys the successor those corrections.

---

## 0. Decisions already made — do not relitigate

- **Architecture**: backups run on the **system duplicati-server** (dpkg 2.3.0.4,
  port 8300, `--portable-mode`, root, unit `duplicati.service`). This unit is
  production; the predecessor's "remove the :8200 service" is superseded. The
  user-lane CLI runner/timer is superseded (final record 0-for-3, three distinct
  failure modes) — retirement candidate, not revival candidate.
- **Encryption**: Yamaguchi uses the built-in **AES module** (2026-08-25) — gpg
  reproduced GPGFlushError under root even with mitigations in a calm-memory window;
  AES makes the class structurally impossible. Old sets stay gpg; **both passphrases
  retained indefinitely** (`PASSPHRASE` fresh/Yamaguchi, `PASSPHRASE_OLD` old
  archive; select by NAME — both are 32 chars).
- **Retention `1W:1D,1M:1W,1Y:1M,3Y:2M` runs WITH `--no-auto-compact=true`** — the
  pairing is load-bearing (an interrupted compact destroyed the July archive).
  Retention-thinned filesets get their fully-unreferenced VOLUMES deleted at later
  runs — that is deletion, not compaction, and is expected (verified: every run's
  `CompactResults: false`). Do not enable auto-compact; a manual compact is a
  separately-decided future operation.
- **Scope widening (Paul, 2026-08-25 14:14, via UI)**: two VM images added as
  explicit Sources (`win10_vm_2023-04-29.vdi`, `win11_vm_clean_2026-07-15.vdi`),
  `*.iso`/`*.vdi` filters removed, and **`--skip-files-larger-than` removed
  entirely** (required to admit the VDIs; note the cap's absence is now global —
  any future giant file in `/home` is in scope). The `VirtualMachines/` folder
  exclude remains; only the named images enter. New total scope ≈ 210 GB.
- **Merges**: only on Paul's explicit per-PR/group approval; `util/safe_merge.py`;
  verify PR *state*, never exit codes.
- **SOP**: all generated content gets multi-custom-agent adversarial validation —
  different lenses, prompted to REFUTE, hunting omissions as hard as errors.

## 1. State of the world (live-probed at final revision, ~15:1x 2026-08-25; volatile rows marked ⏳)

| fact | value |
|---|---|
| Yamaguchi full (task 5) | **Success** — 726,130 files / 201.1 GB examined+added, 375 volumes / 98.1 GB, 2 h 12 m, wrote own dlist, `IsFullBackup: True` (zero retries per server stats — transcript-attested) |
| Certification (of the ORIGINAL scope) | coverage **1,122,583/1,122,583, zero surplus**; **375/375 HMAC-valid**; drill **14/15 outright**, 13 live-oracle matches, 0 contradictions; symlink restored+live-matched under engine preconditions |
| Incrementals (tasks 6, 7) | both **Success**; task 6's same-day fileset retention-thinned (its volumes deleted at next run; `CompactResults: false` throughout — configured-safe) |
| ⏳ Task 8 | **Backup, RUNNING at handoff** (started 14:14:49, manual, the widened ~210 GB scope; was ~90/210 GB at 15:00). Destination census is UNSTABLE until it settles — settled post-task-7 state was 380 files / 2 dlists; mid-task counts (467/475/520…) are transients. **Do not use any fixed count.** |
| `/etc/default/duplicati` | active line (mtime 14:14): `--webservice-interface=any --webservice-port=8300 --portable-mode` — **the restart trap is CLOSED** (portable-mode restored by Paul). Residue: the loopback variant survives only as a COMMENT that **lacks portable-mode** — activating that comment verbatim would re-open the trap (§2 item 2) |
| PRs | #1319 / #1348 / #1350 / **#1370** MERGED; **#1369 OPEN** (certification note + tooling; awaiting Paul) |
| ⚠ dbconfig.json | `~/.config/Duplicati/dbconfig.json` now maps **the Yamaguchi destination → `DQRVQNDIFX.sqlite`** — the OLD fresh set's job DB. A `--dbpath`-less CLI op against the Yamaguchi destination would open the WRONG database. Always pass `--dbpath` explicitly, or fix the mapping (Paul-gated; §2 item 7) |
| ⚠ Same-spindle exposure | `/home` = **sdc3**, `/media/pcalnon/temp_backups` (Yamaguchi + all certification evidence + config records) = **sdc4** — the certified backup lives on the source's own physical disk. Plan §7 criterion 6 (physically separate drive) is OPEN (§2 item 9) |
| Old fresh set `Ubuntu/` | intact, 209 files, gpg, certified **partial** (~55% of then-scope); job DB `DQRVQNDIFX.sqlite` (350 MB) |
| Old archive `/mnt/Backups/Ubuntu` | unchanged (5,366 volumes; 5 intact pre-2026 restore points); Recreate dead; in the orphaned profile DB, old job 'Ubuntu' has **auto-compact ON** (job 3 'Ubuntu-fresh' has it off) — bites only if that world is revived |
| Old profile server DB | `~/.config/Duplicati/Duplicati-server.sqlite` schema **19**, orphaned; schema-11 copies preserved beside it; holds old job DEFINITIONS |
| Autoupdater shadow | neutralized: `~/.config/Duplicati/updates.disabled-2026-08-25/` (2.0.7.1, 2.0.8.1, `current`) — the "two installs" root cause |

## 2. Open work, priority order

1. **Settle task 8, then re-baseline.** Wait for it to finish (`…yamaguchi_server_api.py
   progress` / `task 8`); confirm `ParsedResult: Success` (`log 2` verb). Then:
   re-census the destination; **re-export the config of record** (task 8 ran under a
   config newer than `yamaguchi-config-final.json` — regenerate it, marked
   post-scope-widening); update the certification note's §3 or append a scope-change
   addendum. The existing certification covers the ORIGINAL scope; the widened scope
   (VM images) is certified by the item-4 drill.
2. **Re-stage loopback correctly (Paul, then a service restart applies it).** Edit
   only `any`→`loopback` in the ACTIVE line, i.e.
   `DAEMON_OPTS="--webservice-interface=loopback --webservice-port=8300 --portable-mode"`.
   The stale loopback COMMENT lacks portable-mode — never activate it verbatim. Until
   the restart, the UI listens on `*:8300` (accepted temporary state — **do not
   restart just to close it while a backup runs**).
3. **Merge PR #1369** (Paul). The branch now also carries the API client's `log`/`task`
   verbs (needed by items 1 and 8) and this handoff.
4. **Second drill — certifies the widened scope.** Run AFTER task 8 settles, outside
   the daily schedule window:
   `python3 util/ad-hoc/duplicati_drill_fresh.py --encryption aes --single-invocation
   --dest /media/pcalnon/temp_backups/Yamaguchi --run-root /media/pcalnon/temp_backups/_yamaguchi_drill
   --backup-start-epoch <RECOMPUTED>`
   **Time-decaying parameters — re-derive at drill time, never copy:** version 0 =
   whichever fileset the NEWEST surviving dlist names (retention thins same-day
   duplicates); `--backup-start-epoch` is the live-oracle mtime cutoff = that dlist's
   filename timestamp (`date -d '<YYYY-MM-DDTHH:MM:SS±TZ>' +%s`). Two driver edits
   first, landing on a **new branch off main after #1369 merges** (never pushed onto
   the awaiting PR): relax `parse_destination`'s exactly-1-dlist assertion
   (`duplicati_drill_fresh.py:124-125`) to **parse the NEWEST dlist** (`dlists[-1]`
   — the list is sorted; `dlists[0]` would silently drill the original full), and
   include a VM-image candidate in the strata (the >4 GB class now includes ~50 GB
   VDIs — cap the large-stratum size or expect a long drill). Expected quirks:
   symlink candidates need parent-folder preconditions (cert note §5.4); duplicati-cli
   rc 1/2 are SUCCESS variants.
5. **Server-run failure alerting** (plan §7 criterion 4 — REGRESSED by the server
   pivot: server-run jobs currently fail silently). Recommended: job-level
   `--run-script-after` invoking the notification path of `util/duplicati_backup_failure.bash`
   (the REPO copy — it survives lane retirement; the deployed `~/.local/bin` copy may
   be swept by item 6). Architecture choice is Paul's; present options, implement the
   picked one, prove it on a forced failure (the lane's alert was only trusted after
   a real firing).
6. **Retirements (each needs Paul's explicit go):**
   - User lane: units + timer (disabled) in `~/.config/systemd/user`, deployed
     scripts in `~/.local/bin`, repo `util/systemd/duplicati-backup.*`. Keep the repo
     `util/duplicati_backup_failure.bash` if item 5 reuses it.
   - **`…/.claude/worktrees/curious-plotting-hummingbird/.env` still holds LIVE
     copies of both passphrases** (predecessor protected it for a now-closed
     investigation). Reconcile/delete DELIBERATELY — authoritative file is
     `~/.config/duplicati-backup/env`; an unannotated worktree sweep hitting it is
     the silent-divergence shape.
   - Old fresh set `Ubuntu/` (~55 GB) + `DQRVQNDIFX.sqlite`: keep until item 4
     passes; it is the only certified gpg-era set (partial).
   - Scratch (all under `/media/pcalnon/temp_backups/`): `_gpg_repro/` 2.3 GB ·
     `_fresh_drill/` 1.2 GB (**keep its logs** — fresh-set certification evidence) ·
     `_yamaguchi_drill/` ~5.5 GB restored copies (**keep logs/results**) ·
     `_drill_scratch/` ~35 GB (old-archive era; `drill.sqlite` carries a 6.86 GB
     WAL) · `_fresh_dlist_check/`+`_yamaguchi_check/` (small, **keep** — evidence) ·
     `_duplicati_tmp/`: **this is Yamaguchi's LIVE `--tempdir`** — delete stale
     `dup-*` CONTENTS only (eight ~524 MB pcalnon-owned files from Aug 23 + small
     stragglers; no root needed), never the directory, never while a backup runs.
   - `updates.disabled-2026-08-25/` after a comfortable soak.
7. **dbconfig.json fix (Paul-gated, one entry):** correct or remove the
   Yamaguchi→`DQRVQNDIFX.sqlite` mapping (§1 row) so a bare CLI op cannot open the
   wrong DB. Until then: always `--dbpath`.
8. **Verify the schedule question.** Server `ProposedSchedule` says next fire
   `2026-08-26T14:00:00Z` (=09:00 CDT) though the configured `Time` is 18:00Z
   (13:00 CDT) — determine which fires (the `log 2` verb shows run BeginTimes);
   if wrong, fix via GET/modify/PUT of backup 2 (the `yamaguchi_switch_aes.py`
   pattern), Paul-gated since it edits the live job.
9. **Migration — plan §7 criterion 6, still OPEN (do NOT report the arc closed
   without it).** "The tier is specified to live on a physically separate on-host
   drive … it is not done until it does." Yamaguchi shares sdc with the source
   (§1). Whether the finished state is destination-migration to `/mnt/Backups/…`
   or a second-copy design is **Paul's re-scope decision — currently recorded
   nowhere**; obtain and record it. Relevant facts: sda1 hosts the damaged old
   archive (5 intact restore points must survive anything done there); the My
   Passport drive sits on a **USB 2.0 controller** with faster controllers idle
   (~5–10× available — a replug changes migration feasibility); `--blocksize`
   is IRREVERSIBLE per set.
10. **Back up the server's own brain (small, high value):** the Yamaguchi job
    definition/schedule/filters/encrypted passphrase live ONLY in the root-owned
    portable server DB (`/usr/lib/duplicati/data/`, outside every backup), and the
    config-of-record JSONs sit on the same sdc spindle. Copy the server DB (server
    stopped, or via SQLite backup API — a live `cp` of a WAL-mode DB can tear) +
    the `_yamaguchi_check/` records to sda1 or off-disk. Also ask Paul: the
    root-run backup now includes previously-skipped 0000-mode files — notably the
    release-train GPG private key (`…/Juniper/.gnupg/juniper-release-train.…pem`)
    — **is that inclusion wanted?** (It is currently that key's only backup, on the
    same spindle as the original.)
11. **Old-archive tail** (predecessor §4 items 3–5 + 7 detail; its §6 damage facts
    remain binding): the intact-arm re-run with `--time`; the purge decision (only
    `util/ad-hoc/duplicati_offline_broken_files.py` ever produced a census; timeouts
    are not results; **any real purge/delete there must pass `--no-auto-compact=true`
    explicitly** — the CLI default would compact the last 5 intact restore points);
    the unanswered "why did Recreate take the dblock path with 2,682 dindexes
    present" (a future Recreate will repeat it); and the upstream Duplicati issue
    (investigation §9 candidate 4 — the evidence package for the 5 s Join, vacuous
    retry, and queue-kill defects is filing-ready and still relevant while gpg sets
    remain restorable).

## 3. Traps (predecessor §3 still applies; this session added)

- **"job 2" is a COLLISION**: the live Yamaguchi job is id 2 on the system server;
  the OLD archive job is also id 2 in the orphaned profile DB. Every §5 prohibition
  about "the old job" means the profile world, never the live server.
- **`last-run.status` (user lane) is written only at run END** — a hung run displays
  the PREVIOUS result. This misread triggered the server pivot. Status files are not
  live state; check the process.
- **A oneshot service reads `activating` its whole runtime**, never `active`.
- **`pgrep -f <pattern>` self-matches your own compound command**; `duplicati-server`'s
  comm truncates to `duplicati-serve`. Use `pgrep -x`/`ps -C` with care.
- **The background-worker lease kills `run_in_background` tasks (minutes-scale
  here).** Long work runs as `systemd-run --user` transient units; a killed WATCHER
  is not a failed JOB — re-arm and re-check.
- **Python block-buffers redirected output** — a killed run leaves a 0-byte log; use
  `python3 -u`.
- **duplicati-cli rc 1 = success/no-changes, rc 2 = success-with-warnings**; only
  ≥3 is failure.
- **Partial restores (new engine)**: no parent-dir creation for metadata-only
  entries; out-of-tree relative symlinks skipped by containment policy. Full-tree
  restores unaffected.
- **`duplicati-server-util` lacks abort/delete/log verbs** — use
  `util/ad-hoc/yamaguchi_server_api.py` (proven verbs: status, progress, run, abort,
  delete, import, **log, task**; `export` 400s on this server — use `GET
  /api/v1/backup/<id>`). Credential `DUPLICATI_WEB_CREDENTIAL` read in-process from
  `/home/pcalnon/Development/python/Juniper/juniper-ml/.env` by ABSOLUTE path — works
  from any cwd; `.env` is untracked and lives only in the primary checkout.
- **SharpAESCrypt takes the password on argv** (accepted single-user-host deviation);
  rc 3 = HMAC mismatch, rc 4 = wrong password.
- **The worktree isolation hook refuses compound inline commands** — put multi-step
  logic in a script file and run that.

## 4. Identifiers

| what | value |
|---|---|
| Yamaguchi job | id **2** on the system server, `http://127.0.0.1:8300` (UI on `*:8300` until item-2 restart) |
| destination | `/media/pcalnon/temp_backups/Yamaguchi/` (`.zip.aes`) — on **sdc4**, same disk as `/home` (sdc3) |
| server unit / opts | `duplicati.service` (system); `/etc/default/duplicati` active line = `any` + `8300` + `portable-mode` (post-14:14) |
| server data root | `/usr/lib/duplicati/data/` (root-owned, `drwx------`) — portable mode |
| UI credential | `DUPLICATI_WEB_CREDENTIAL` in `/home/pcalnon/Development/python/Juniper/juniper-ml/.env` (untracked; primary checkout only) |
| backup passphrases | `~/.config/duplicati-backup/env`: `PASSPHRASE` (sha256[:16]=**6d8b263f6d064556**) = fresh/Yamaguchi; `PASSPHRASE_OLD` (**b085454a8c34bd8c**) = old archive |
| config of record | `_yamaguchi_check/yamaguchi-config-final.json` — **STALE since 14:14** (pre-widening); regenerate per §2 item 1. The two `_fresh_dlist_check/yamaguchi-config-*.json` are pre-AES history |
| certification evidence | `_yamaguchi_check/{crosscheck.log, decrypt_validate_all.log, drill-full-run.log}`; drill run dir `_yamaguchi_drill/drill-20260825-075730/` (results.json, restore-all.log, `symlink-retest*.log` — numbered retest/retest3/retest4, no retest2; retest-4 verdict in that unit's journal) |
| tooling | `util/ad-hoc/yamaguchi_*.{py,bash}`, `duplicati_dlist_crosscheck.py`, `duplicati_decrypt_validate_all.bash`, `duplicati_drill_fresh.py` — **only on PR #1369's branch until merge** |
| old fresh set | `Ubuntu/` 209 files gpg; job DB `~/.config/Duplicati/DQRVQNDIFX.sqlite` (also wrongly mapped in dbconfig.json — §2 item 7) |
| old archive | `/mnt/Backups/Ubuntu` (sda1); archived pre-deletion DB `backup SJTCQIIZSJ 20260712033545.sqlite` (13 GB, spaces in name) — open read-only via SQLite URI `immutable=1` (**an SQLite open flag; nothing on disk protects the file**) — do not sweep |

## 5. Standing prohibitions — all still binding

- **NEVER run `Repair`** against the old-archive job (profile world).
- **NEVER `kill -9` Duplicati.** TERM, then wait; a shrinking `-wal` beside a growing
  `.sqlite` means it is finishing.
- **Verify mounts before ANY destination operation** — `/mnt/Backups` is NOT a
  mountpoint; `/mnt/Backups/Ubuntu` and `/media/pcalnon/temp_backups` are.
- **Never restore "latest" against the OLD fresh job DB** (crashed-fileset landmine).
- **Run `util/ad-hoc/duplicati_secret_check.py`** whenever a long job holds a secret
  and after any credential-file edit while one runs (0 match / 1 DIFFER / 2
  undetermined; on DIFFER capture `/proc/<pid>/environ` before exit).
- Do not execute the withdrawn DB-restore runbook (⛔ above). Do not restart
  `duplicati.service` while a backup task is running, for any reason short of §5's
  TERM discipline being required.

## 6. Verify your starting state

**Until #1369 merges, run this from a worktree/checkout of
`feat/yamaguchi-backup-tooling`** (the tooling and this document exist only there;
after merge, any up-to-date main checkout works). Do not `git -C` into other
checkouts from a worktree-isolated session. Run one line at a time.

```bash
git fetch origin && git status -sb                        # clean, tracking the branch
gh pr view 1369 --json state --jq .state                  # OPEN until Paul merges

grep -E '^DAEMON_OPTS' /etc/default/duplicati             # any + 8300 + portable-mode (post-14:14; loopback pending item 2)
systemctl is-active duplicati.service                     # active
ps -eo args | grep '[d]uplicati-server'                   # matches the DAEMON_OPTS above
systemctl --user is-enabled duplicati-backup.timer        # disabled (rc 1 is normal)  <- keep so until retired

mountpoint /media/pcalnon/temp_backups && mountpoint /mnt/Backups/Ubuntu
ls -1 /media/pcalnon/temp_backups/Ubuntu | wc -l          # 209, unchanged
# Yamaguchi census: NO fixed number is valid -- re-census and reconcile against
# the server's own run log (deletes are retention thinning; CompactResults must stay false):
ls /media/pcalnon/temp_backups/Yamaguchi | grep -c dlist
python3 util/ad-hoc/yamaguchi_server_api.py status        # job 2 present; note ActiveTask
python3 util/ad-hoc/yamaguchi_server_api.py log 2         # newest-first; every ParsedResult should be Success (one historical Fatal = the pre-AES gpg attempt)
```

## 7. Git / session state

Branch `feat/yamaguchi-backup-tooling` (PR **#1369**, OPEN): HEAD `4e5d739d` plus one
final commit from the authoring session containing this handoff AND the API client's
new `log`/`task` verbs (§2 items 1/8 depend on them — both committed together;
verify with `git log -1 --stat`). #1319/#1348/#1350/#1370 are MERGED. Merges require
Paul's explicit approval. All certification evidence is durable under
`/media/pcalnon/temp_backups/` (survives reboot; nothing load-bearing in `/tmp`).

The recurring failure shape, which this document itself demonstrated in draft —
three §1 claims were stale at the draft's own timestamp, and a live task was missed
— is **a correct mechanism paired with a wrong consequence**: a status file read as
live state, a snapshot stamped "verified" without a final re-probe, a success banner
from a tool that never checked its mode. Prefer running the thing over reasoning
about it; re-probe volatile state at the moment of use; and treat every ⏳ row above
as expired the moment you read it.
