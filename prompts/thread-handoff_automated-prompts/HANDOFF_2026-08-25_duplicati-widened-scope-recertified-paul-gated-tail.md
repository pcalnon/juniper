# HANDOFF 2026-08-25/26 — Duplicati: widened scope RE-CERTIFIED on the full ladder; the tail is Paul-gated

**Continue the backup-restoration arc from its re-baselined goal state.** The predecessor
left task 8 (the scope-widening backup) running and an acceptance tail. This session
settled it: task 8 succeeded; the widened fileset passed the full ladder (coverage, HMAC
of every volume, drill 2); the config of record and census were regenerated; the
certification records are mirrored off the source spindle; the alerting candidates are
written and proven. **Every remaining item needs Paul's decision or root** — execute the
picked ones, do not re-derive them, and do not redo anything listed as DONE.

Glossary for a cold reader: *Yamaguchi* = the production backup job (id 2 on the system
`duplicati-server`, port 8300, AES) named after this host; *dlist* = one per run, the
fileset manifest; *dblock* = a 500 MB data volume; *dindex* = the index of one dblock;
*the ladder* = coverage (every hash the dlist needs is declared by a dindex) → HMAC
(every volume decrypts) → drill (files restored destination-only and hash-matched
against the live source); *portable-mode trap* = a server restart without
`--portable-mode` wakes against a different data root and job 2 simply vanishes.

Predecessor: [`HANDOFF_2026-08-25_duplicati-yamaguchi-certified-open-tail.md`](HANDOFF_2026-08-25_duplicati-yamaguchi-certified-open-tail.md)
— **its §0 decisions, §3 traps and §5 prohibitions remain binding** (two restated in §0
below). Its §2 items: **1 DONE**, **2 Paul** (loopback → item 5), **3 DONE** (#1369 merged
22:20Z), **4 DONE** (drill 2), **5 candidates proven → item 2**, **6 → item 9**, **7 → item
6**, **8 ANSWERED** (09:00 CDT; intent → item 3), **9 → item 8**, **10 records mirrored; DB
copy → item 7; key question → item 4**, **11 carried by precise reference** (its item 11 →
the 2026-08-24 handoff §4 items 3–5, 7 and §6 damage facts, all still binding). Its ⏳ rows
are all superseded by §1.

Note of record for everything below: [`…DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md` **§8**](../../notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md)
(what changed, task 8, census, ladder, tooling, Paul's decisions with exact edits, criteria
status, retirement inventory **with the KEEP list**). Read it before acting. ⛔ The
DB-restore runbook stays WITHDRAWN.

> Length deviation, declared: ~2,800 words by `wc -w` (commands and tables included)
> against the ~500 asked. Four adversarial
> validators (accuracy, omission/amputation, executability, cold-start) found ~45 defects in
> the draft — among them an unqualified `Ubuntu/` in a deletion list that also names the
> old-archive mountpoint, a GET→PUT path that would have submitted a passphrase mask, and
> three code defects. The extra words are those corrections and the exact commands.

---

## 0. Decisions — do not relitigate

- **Drills select the NEWEST dlist** (never `dlists[0]`), derive the oracle cutoff from it,
  and refuse (rc 2) if the newest dlist changes across the restore. `--version=0` stays the
  pin; the guard is what makes it safe on a live set. The driver's defaults are now the
  live set (Yamaguchi / `_yamaguchi_drill` / aes); the old gpg set needs explicit flags.
- **Alerting recommendation is B** (external watchdog on a user timer): the only design
  that catches never-ran / job-vanished / server-down / stuck. A (`--run-script-after`)
  complements, cannot replace. Neither is deployed; Paul picks.
- **Restated from the predecessor's §0, still binding**: retention
  `1W:1D,1M:1W,1Y:1M,3Y:2M` runs WITH `--no-auto-compact=true` — the pairing is
  load-bearing (an interrupted compact destroyed the July archive); never enable
  auto-compact, and a manual compact is a separately-decided future operation, not a
  space-reclaim shortcut for item 9. The system `duplicati.service` on :8300 IS production
  — never remove it (the 08-24 "remove the :8200 service" is superseded). Both passphrases
  stay retained indefinitely; select by NAME (`PASSPHRASE` = Yamaguchi/fresh,
  `PASSPHRASE_OLD` = old archive).
- **PUT rule**: `GET /api/v1/backup/<id>` returns `passphrase` as a 15-character MASK. Any
  GET/modify/PUT must replace that setting with the real value from
  `~/.config/duplicati-backup/env` — exactly as `yamaguchi_switch_aes.py` does — then GET
  again and confirm `encryption-module=aes`, 3 sources, 44 filters. Never "simplify" it.
- Nothing was deleted, restarted, re-scheduled, or PUT to the live job. The one desktop
  notification Paul may have seen (18:41 CDT 08-25, "JOB_MISSING backup=999") was the
  deliberate watchdog proof.

## 1. State of the world (live-probed 02:27–02:52 CDT 2026-08-26; ⏳ = re-probe before use)

| fact | value |
|---|---|
| Task 8 (widened scope) | **Success** 19:14:49Z→20:56:20Z 08-25 (1 h 41 m): 726,190 files / 326.5 GB examined; 195 added = 125.4 GB (both VDIs + two ISOs); 401 volumes / 104.5 GB up; 0 retries/warnings/errors; retention thinned the 18:13Z fileset; `CompactResults` empty |
| ⏳ Destination | **780 = 2 dlist + 389 dblock + 389 dindex; 202,586,201,260 B** — agrees exactly with server metadata. Filesets `20260825T102739Z` (original full) + `20260825T191449Z` (widened). **The `…191449Z` dlist will be retention-thinned by the 2026-08-26 14:00Z run** (same-day as the full; `1W:1D` keeps the earliest per interval + the newest) — expect `102739Z` + `20260826T140000Z` afterwards; thinning, not loss (only the dlist goes; volumes stay under `--no-auto-compact`) |
| Ladder for `…191449Z` — COMPLETE | coverage **1,241,950/1,241,950** (389/389; surplus 1,625 = older/thinned filesets' blocks) · HMAC **780/780 valid, 0 failures** (1,159 s, 02:29–02:48 CDT 08-26, unit `yamaguchi-validate2`) · drill 2 **17/17 VERIFIED** (241/389 dblocks; 13 live matches / 0 contradictions; incl. the 63.9 GB static win10 VDI and a symlink+sibling pair; 63.92 GiB in 40 m 44 s; restore done 19:19, verdict 19:31 CDT 08-25). **Do not re-run any rung.** |
| Config of record | `_yamaguchi_check/yamaguchi-config-post-widening.json` (10 settings — `--skip-files-larger-than` GONE; 44 filters; 3 sources). `yamaguchi-config-final.json` = the original certified config, history |
| ⏳ Schedule | `Time=2026-08-25T14:00:00Z, Repeat=1D` → **daily 09:00 CDT**; next 2026-08-26T14:00Z. Set by Paul's 14:14 UI save; intent unconfirmed. **Duration is now unknown** (a live-modified 56 GB VDI is re-read daily), not the pre-widening ~9 min |
| Server / file | pid 1327450 since 02:46 08-25, `any` + 8300 + `--portable-mode`; file matches; **restart trap CLOSED**; loopback pending (comment line 12 lacks portable-mode — never activate it verbatim). `sudo -n` needs a password — root steps are Paul's |
| Job DB (root) | `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite` + `Duplicati-server.sqlite` there — NOT the same-named orphaned `~/.config/Duplicati/Duplicati-server.sqlite` |
| VM finding | `win11_vm_clean_2026-07-15` runs under VBoxHeadless; its VDI (56 GB) is modified continuously → crash-consistent copy, re-read and re-uploaded daily. win10 VDI (64 GB) static |
| Release-train key | **IN the backup** (`…/.gnupg/juniper-release-train.2026-07-21.private-key.pem`, 1,675 B) |
| Records off-spindle | `/mnt/Backups/Ubuntu/_yamaguchi_records/` (sda1) **re-synced 02:52 CDT 08-26** — includes drill 2's `results.json`/`restore-all.log`, the validate log, `watchdog-proof-20260825.log`, both config records (redacted) |
| dbconfig.json | hand-written single object mapping Yamaguchi → `DQRVQNDIFX.sqlite`; the CLI expects an array, so a `--dbpath`-less op fails to parse rather than opening the wrong DB — misleading, not dangerous. Always `--dbpath` |
| PRs | #1369 MERGED. **This session's PR: #1390 OPEN** (`feat/yamaguchi-widened-scope-recert`, opened 02:58 CDT 08-26) — awaiting Paul's explicit merge approval; if it shows neither OPEN nor MERGED, see the §7 fallback |
| Peer session | "t6 rebaseline" (GPU campaign, `…/dazzling-swimming-stroustrup`). **Told** at 02:52 CDT that the drill and the validate pass are done and that the 09:00 run's duration is unknown. Reply route: copy the `from=` of any message it sends (`uds:/run/user/1000/cc-socks/3685337.sock` worked from this session); `ListAgents` shows it if alive. Its launch gate trips on any duplicati-family/aescrypt process >20 % CPU — **announce before starting any drill or validate**; if it is gone there is nothing to tell |
| Alerting candidates | B `yamaguchi_watchdog.py` proven (forced `UNREACHABLE`/`JOB_MISSING`/`STALE` → rc 1 with durable records; normal → `OK`; desktop notification rc 0); re-proven after hardening at 02:50. A drafted. Neither deployed |

## 2. Open work — priority order (PAUL RUNS = needs root or is his call)

1. **Merge this session's PR** (Paul's explicit approval). Then sync the primary checkout:
   `cd /home/pcalnon/Development/python/Juniper/juniper-ml && git pull --ff-only origin main && test -f util/ad-hoc/yamaguchi_watchdog.py`.
2. **Pick the alerting architecture and deploy it** (§8.6-4). **B only after item 1** (the
   unit's `ExecStart` is the primary-checkout path; deployed earlier, every 12:00 fire exits
   2 silently): copy `util/systemd/yamaguchi-watchdog.{service,timer}` to
   `~/.config/systemd/user/`; `systemctl --user daemon-reload`; `systemctl --user enable --now yamaguchi-watchdog.timer`;
   `systemctl --user start yamaguchi-watchdog.service`; read
   `~/.local/state/duplicati/server-watchdog.status` (expect `OK`). Closing test for
   criterion 4: run the deployed script once with `--backup-id 999` (real state dir, real
   desktop notification; annotate the `server-failures.log` line as synthetic). Re-check
   `loginctl show-user pcalnon -p Linger` = yes after any reboot. **A** (PAUL RUNS):
   `sudo install -D -o root -g root -m 0755 util/ad-hoc/yamaguchi_run_script_after.bash /usr/local/lib/duplicati/yamaguchi_run_script_after.bash`,
   then add `--run-script-after=<that path>` to backup 2 via GET/modify/PUT (§0 PUT rule),
   prove on a throwaway job with an unreachable destination — never by breaking the live job.
3. **Confirm the schedule** — 09:00 CDT intended? If 13:00: PUT `Schedule.Time` = the next
   day's `18:00:00Z` (§0 PUT rule; `ActiveTask: null` first).
4. **Decide the VM-image and key questions** (§8.6-1/2, exact edits there): exclude the
   running VM's VDI / shut it down before 09:00 / accept; keep or exclude the release-train
   key (excluded = in NO backup → needs its own off-spindle copy).
5. **Loopback restage** (PAUL RUNS, not between 08:45 CDT and the run's end): (1)
   `python3 util/ad-hoc/yamaguchi_server_api.py status` → `ActiveTask: null` AND
   `SchedulerQueueIds: []`; (2) `sudo sed -i 's/--webservice-interface=any/--webservice-interface=loopback/' /etc/default/duplicati`
   (touches only the active line 11) and `grep -E '^DAEMON_OPTS' /etc/default/duplicati`
   must show `loopback … 8300 … --portable-mode`; (3) re-run (1); (4)
   `sudo systemctl restart duplicati.service` (unit has `Restart=always` and no
   `TimeoutStopSec` — a restart mid-task ends in SIGKILL, the §5 class); (5) `status` must
   still list job 2 + a `ProposedSchedule`; if not, check `ps -eo args | grep '[d]uplicati-server'`
   for `--portable-mode` and stop.
6. **dbconfig.json** (Paul's user config): delete `~/.config/Duplicati/dbconfig.json`
   (Duplicati rewrites its own) or rewrite it as an array with `"Path": "/media/pcalnon/temp_backups/Ubuntu"`.
7. **Server-brain backup** (PAUL RUNS; `sqlite3` CLI is NOT installed): `mountpoint -q /mnt/Backups/Ubuntu || exit 1`, then
   `sudo python3 -c "import sqlite3; s=sqlite3.connect('file:/usr/lib/duplicati/data/Duplicati-server.sqlite?mode=ro', uri=True); d=sqlite3.connect('/mnt/Backups/Ubuntu/_yamaguchi_records/Duplicati-server.PORTABLE-8300.sqlite'); s.backup(d); d.close(); s.close()"`,
   verify `sudo python3 -c "import sqlite3; print(sqlite3.connect('/mnt/Backups/Ubuntu/_yamaguchi_records/Duplicati-server.PORTABLE-8300.sqlite').execute('select count(*) from Backup').fetchone())"` → `(1,)`,
   then `sudo chown pcalnon: …PORTABLE-8300.sqlite && chmod 0600 …` (it carries the
   encrypted passphrase blob). Optional: same for `BMXWPAOGLP.sqlite`. Records re-sync any time:
   `mountpoint -q /mnt/Backups/Ubuntu && rsync -a --exclude='restored/' --exclude='tmp/' --exclude='work/' --exclude='*.sqlite*' --exclude='dlist-query-*/' /media/pcalnon/temp_backups/_yamaguchi_check /media/pcalnon/temp_backups/_fresh_dlist_check /media/pcalnon/temp_backups/_yamaguchi_drill /media/pcalnon/temp_backups/_fresh_drill /mnt/Backups/Ubuntu/_yamaguchi_records/`.
8. **Migration decision** (plan §7 criterion 6 — do NOT report the arc closed without it):
   facts and the five-step move procedure in §8.6-8. Options: (a) move the set to a
   subfolder on sda1, (b) second copy on the My Passport after a USB-3 replug — **(b) alone
   is a re-scope** (plan §3 rejected sdb1 on measurement) needing re-measurement and a plan
   amendment, (c) both. Record the decision in the plan's §8; end with a drill at the new
   location, announced to the peer first.
9. **Retirements** (§8.8 — read its **KEEP list first**; each needs an explicit go):
   `_drill_scratch/` 35 GB **only after item 11's purge decision is executed or abandoned**
   (the old archive's only local DB) · `_duplicati_tmp/` stale `dup-*` CONTENTS 4.0 GB
   (never the directory, never mid-run) · `_yamaguchi_drill/*/restored/` ~70 GB (keep
   logs/results) · `_gpg_repro/` 2.3 GB · `_fresh_drill/` restored copies ·
   **`/media/pcalnon/temp_backups/Ubuntu/`** 51 GB (old gpg fresh set — **NOT
   `/mnt/Backups/Ubuntu`, the old-archive mountpoint; nothing is ever deleted there**) +
   `~/.config/Duplicati/DQRVQNDIFX.sqlite*` · `updates.disabled-2026-08-25/` after a soak
   Paul calls comfortable · user lane `~/.config/systemd/user/duplicati-backup.{service,timer}`,
   `duplicati-backup-failure.service`, `~/.local/bin/duplicati-{scheduled-backup,backup-failure}.bash`,
   repo `util/systemd/duplicati-backup.*` (retire the lane's files in
   `~/.local/state/duplicati/` by name — the watchdog shares that directory) ·
   `…/.claude/worktrees/curious-plotting-hummingbird/.env` (6 lines, only the two
   passphrases; `rm` is safe after checking `~/.config/duplicati-backup/env` holds
   `6d8b263f…`/`b085454a…` by sha256[:16]).
10. **Reboot / login survival** (criterion 5): after the next reboot —
    `systemctl is-active duplicati.service`, `status` shows job 2 + `ProposedSchedule`,
    the next run appears in `log 2`, `loginctl show-user pcalnon -p Linger` = yes.
11. **Old-archive tail** — untouched; by precise reference: predecessor §2 item 11 → the
    2026-08-24 handoff §4 items 3–5, 7 (intact-arm re-run with `--time`; purge decision —
    only `duplicati_offline_broken_files.py` ever produced a census, timeouts are not
    results, any real purge must pass `--no-auto-compact=true` explicitly; the Recreate
    dblock-path question; the upstream issue package) and its §6 damage facts.

## 3. Traps added this session

- **`ps -o pcpu` is a LIFETIME average** (the idle server read 45 % for 15 h after two long
  runs); `top -b -n2 -d2 -p <pid>` second frame reads live. A peer's gate was blocked on it.
- **Never `ps`-grep the duplicati family while a validate or drill runs**: `duplicati-aescrypt`
  carries the passphrase on argv. `ps -eo args | grep '[d]uplicati-server'` is the safe form.
- **Two `Ubuntu/` exist**: `/media/pcalnon/temp_backups/Ubuntu/` (old fresh set, deletable
  on Paul's go) and `/mnt/Backups/Ubuntu` (old-archive mountpoint, never). Always qualify.
- **"job 2" is a collision** (predecessor §3): the live Yamaguchi job is id 2 on the system
  server; the old archive job is also id 2 in the orphaned profile DB. Every prohibition
  about "the old job" means the profile world.
- **The Bash tool's cwd persists across calls**; use absolute paths. **The worktree-isolation
  hook refuses anything beyond one simple pipeline** (loops, `${PIPESTATUS}`, `$(…)` chains)
  — put logic in `util/ad-hoc/*.bash` and run the file.
- **`1W:1D` keeps the EARLIEST fileset per 1-day interval + the newest**; only the dlist is
  removed; volumes stay until an explicit compact.
- **`sqlite3` CLI and `/usr/local/lib/duplicati/` do not exist** on this host (§2 items 7, 2A).
- **The server ignores `pagesize` on `/backup/<id>/log`** (always 5 entries); tools cut
  client-side. `yamaguchi_census.py --runs N` now honours N.
- `_yamaguchi_drill/drill-20260825-183412/` is drill 2's `--select-only` preview (no
  `results.json`) — not a failed drill.
- Drill 2 staged >20 GB in its tempdir at peak; keep `--run-root` on the scratch fs.

## 4. Identifiers (delta — the predecessor's §4 still holds, except that its "tooling only on
#1369's branch" is now "new tooling only on this PR's branch until merged")

| what | value |
|---|---|
| widened fileset / dlist | `duplicati-20260825T191449Z.dlist.zip.aes` (epoch 1787685289) — thinned after 2026-08-26 14:00Z |
| drill 2 | run dir `_yamaguchi_drill/drill-20260825-183711/`; unit log `_yamaguchi_drill/drill2-run.log`; argv `python3 -u util/ad-hoc/duplicati_drill_fresh.py --encryption aes --single-invocation --dest /media/pcalnon/temp_backups/Yamaguchi --run-root /media/pcalnon/temp_backups/_yamaguchi_drill` under `systemd-run --user` |
| records of this session | `_yamaguchi_check/{census,crosscheck,dlist-query,yamaguchi-config}-post-widening.*`, `decrypt_validate_all-post-widening.log`, `watchdog-proof-20260825.log` |
| new tooling (this PR) | `util/ad-hoc/{duplicati_dlist_query,yamaguchi_config_record,yamaguchi_census,yamaguchi_watchdog}.py`, `yamaguchi_run_script_after.bash`, `yamaguchi_drill_watch.bash`, `util/systemd/yamaguchi-watchdog.{service,timer}`; revised `duplicati_drill_fresh.py`, `duplicati_dlist_crosscheck.py` |
| watchdog state (when deployed) | `~/.local/state/duplicati/server-watchdog.{status,log}`, `server-failures.log` |
| UI credential | `DUPLICATI_WEB_CREDENTIAL` in the PRIMARY checkout's `.env` (untracked), read by absolute path — the tools work from any cwd, fail opaquely on a fresh clone |

## 5. Standing prohibitions

Unchanged from the predecessor's §5 — NEVER Repair the old-archive job; NEVER `kill -9`
Duplicati; verify mounts first (`/mnt/Backups` itself is NOT a mountpoint — every write
under it is guarded by `mountpoint -q /mnt/Backups/Ubuntu`); never restore "latest" against
the old fresh DB; `duplicati_secret_check.py` around long secret-holding jobs; no restart
mid-task; the runbook stays withdrawn. Added: never delete `_duplicati_tmp/` itself; never
prove alerting by breaking the live job; never PUT a job body whose `passphrase` is the mask.

## 6. Verify your starting state (one line at a time; from this branch's worktree until the PR merges, from main after)

```bash
git fetch origin && git status -sb                                    # clean once committed (§7)
git log origin/main --oneline -1 -- util/ad-hoc/yamaguchi_watchdog.py  # empty ⇒ NOT merged yet — do not read an empty PR list as "merged"
grep -E '^DAEMON_OPTS' /etc/default/duplicati                         # any|loopback + 8300 + --portable-mode
systemctl is-active duplicati.service                                 # active
ps -eo args | grep '[d]uplicati-server'                               # must match the line above (catches a re-opened trap after a restart)
systemctl --user is-enabled duplicati-backup.timer                    # disabled (rc 1) — keep so until retired
mountpoint /media/pcalnon/temp_backups && mountpoint /mnt/Backups/Ubuntu
python3 util/ad-hoc/yamaguchi_server_api.py status                    # job 2; ActiveTask; ProposedSchedule
python3 util/ad-hoc/yamaguchi_server_api.py log 2                     # newest-first; every ParsedResult Success (one historical Fatal 10:13Z 08-25 = the pre-AES gpg attempt)
python3 util/ad-hoc/yamaguchi_census.py --runs 3                      # the invariant is the literal "-> AGREE" + newest Success — NOT 780 (after 09:00 08-26 expect 3 dlists then thinning)
python3 util/ad-hoc/yamaguchi_watchdog.py --no-notify --state-dir /tmp/wd   # OK (or OK RUNNING during the 09:00 run); on ALERT: touch nothing, read `log 2`, tell Paul
ls /mnt/Backups/Ubuntu/_yamaguchi_records/                            # 4 record dirs
```

## 7. Git / session state

Branch `feat/yamaguchi-widened-scope-recert` (from main `45c2f4fc`) in worktree
`.claude/worktrees/ticklish-waddling-grove`; commits GPG-signed locally as
`Paul Calnon <paul.calnon@gmail.com>`. Changed: the certification note (§8 addendum +
three pointer edits), two revised drill tools, six new files under `util/ad-hoc/` and two
under `util/systemd/`, this handoff. No AGENTS.md / REFERENCE.md / CHANGELOG (same
footprint as #1369). Committed as `6b4801ba` (+ this PR-number touch-up), pushed, and
opened as **PR #1390** at 02:58 CDT 08-26. Fallback if the PR is somehow neither OPEN nor
MERGED: the branch is on origin; re-open it from any checkout — never sweep the worktree
first. All evidence is durable under `/media/pcalnon/temp_backups/` and mirrored to sda1
(02:52 CDT 08-26).

The recurring failure shape held again this session: a lifetime CPU average read as live
load; a stale 08:29 record read as the live schedule; a "pre-commit passed" on files git
did not yet know about; a retention rule stated as calendar days when the deletions show
intervals. Re-probe volatile state at the moment of use; every ⏳ row above expired when
you read it.
