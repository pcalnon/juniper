# HANDOFF 2026-08-24 — Duplicati: GPG-adjacent failure unpinned; scheduled lane shipped, timer held

**Continue restoring a working, verified backup posture after the 2026-07-13 archive damage.**
The old archive lost its five 2026-07 restore points; the fresh set stood up to replace it has
now failed twice without producing a *verified* restore point. That is the arc.

Predecessor: [`HANDOFF_2026-08-23_duplicati-fresh-set-and-purge.md`](HANDOFF_2026-08-23_duplicati-fresh-set-and-purge.md).
Its §3 items **4** (linger) and **5** (alerting) are **closed and verified**.

Notes of record — read before acting on the old archive:
[`…DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](../../notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md) ·
[`…DUPLICATI-FRESH-BACKUP-SET-PLAN.md`](../../notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md) ·
⛔ [`…DUPLICATI-DB-RESTORE-RUNBOOK.md`](../../notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md)
— **WITHDRAWN, DO NOT EXECUTE.** It is a complete, plausible, step-numbered runbook whose
premise is false: it restores the archived 2026-07-12 DB, which *already contains the wedge*.
It is retained as a specimen. Anyone grepping `notes/` for a Duplicati procedure will find it.

Open PR: **ml#1292** (5 commits, not merged).

> **Length deviation, declared.** The procedure asks for ~500 words; this is ~2,600. The
> procedure has no deviation clause, so this is a violation on the books, made deliberately:
> four independent validators found **45 defects** in the ~1,900-word draft of this document,
> and the majority were *omissions* that would have cost the next thread more than the reading
> time. §3 and §5 exist so a wrong conclusion is not re-derived from scratch.

---

## 0. The decision already made for you

The user's explicit direction:

> **Investigate the GPG failure properly first** — reproduce under controlled concurrency and
> pin the actual mechanism *before changing anything*.

Three alternatives were offered and **not** chosen: retry with reduced concurrency, switch to
the built-in AES module, drill the existing restore point first. Do not silently substitute one.

---

## 1. What is broken — and what is NOT yet established

The fresh backup failed twice on 2026-08-23.

| run | started | ended | how |
|---|---|---|---|
| 1 — manual, PID 779263 | 17:15:09 | SIGTERM 22:47:44 | **hung** at ~65%, fully idle from ~21:22:20 |
| 2 — systemd, PID 1552486 | 22:51:26 | 23:48:24 | **failed rc=100** |

Run 2's exception:

```
System.Security.Cryptography.CryptographicException:
  Failure while invoking GnuPG, program won't flush output
   at Duplicati.Library.Encryption.GPGStreamWrapper.Dispose(Boolean disposing)
```

### 1a. Three corrections to the obvious reading — all found by adversarial review

**(i) It was ONE failure event, not "every dblock failed."** The log contains exactly **one**
`Error in handler` (line 511). It terminated 3 in-flight uploads; two logged `Cancelled` —
collateral, not independent GPG failures. The five following `UnobservedTaskException` blocks
are near-identical and are consistent with .NET's finalizer resurfacing the *same* exception
through orphaned continuations. **At most one dblock ever hit the GPG error**; ~300 more were
never attempted because the whole backend queue runner crashed instead of retrying one volume.

> This matters for how you investigate. A bisection search for a concurrency threshold
> presupposes a reproducible, monotonic-in-load failure. The evidence is at least equally
> consistent with a **rare, possibly non-deterministic single event whose blast radius is
> disproportionate** — a fault-isolation defect, not a performance one. A bisection built on
> the wrong premise may never converge, or may report a falsely "safe" concurrency.

**(ii) The two runs are not a matched pair.** `util/systemd/duplicati-backup.service` sets
`Nice=10`, `IOSchedulingClass=best-effort`, `IOSchedulingPriority=7`. That applies to **run 2
only**; run 1 ran at default priority. A load-sensitive pipe-drain mechanism would plausibly
behave *differently* across that difference. The ~4h-to-hang vs ~57min-to-crash asymmetry is
unexplained and this is a live candidate explanation.

**(iii) Run 1's match to the GPG wrapper rests on kernel wait-channel names only.**
`wait_for_partner` and `anon_pipe_read` are generic states for *any* pipe IPC in a
multithreaded .NET/CoCoL runtime — not a code-path fingerprint. **Treat "one fault, two
presentations" as a working hypothesis, not a premise.** The title of this document says
"GPG-adjacent … unpinned" for that reason.

### 1b. Hypotheses tested — with the exact limits of each test

| hypothesis | status | evidence, and what it does NOT cover |
|---|---|---|
| gpg too slow, exceeds the wrapper's wait | **NOT refuted — test was out of regime** | `duplicati_gpg_throughput.bash 500` → 500 MiB in 1.24 s (403 MiB/s). But that is one *solo, foreground, idle* invocation. The failure says "won't flush output" — a reader-drain symptom — and appeared only with volumes in flight. **The bound itself was never established**: `strings` on `Duplicati.Library.Encryption.dll` (2.3.0.4) shows `WaitForExit`/`GPGFlushError` but no timeout constant, so "4x margin" is margin over an unknown. |
| memory pressure / OOM | **weakly refuted** | PSI memory 0.00 — but sampled *after* the incident. PSI avg10/60/300 decay within minutes; a spike during run 1's window would be gone. Re-sample **during** a reproduction. |
| disk hang | **weakly refuted** | same timing caveat; `df`/`ls`/`stat` were instant post-hoc, no D-state threads |
| strict overcommit blocking fork of a 27 GB process | **refuted** | `vm.overcommit_memory=0` (heuristic) |
| fd / process limits | **refuted** | `ulimit -n` 524288, `ulimit -u` 377368 |
| gpg-agent wedged | **refuted** | `gpg-connect-agent 'GETINFO version' /bye` → `D 2.4.8 / OK` |
| tmpfs staging caused it | **not established** | tmpfs was 19% full. A **real defect**, fixed (§2) — but not the diagnosis. Do not conflate. |

**Positive evidence for concurrency** (stronger than the process-of-elimination framing the
draft used): the log line `Terminating 3 active uploads` shows multiple encryption/upload tasks
genuinely in flight at the moment of failure. The runner sets **none** of
`--concurrency-max-threads`, `--asynchronous-upload-limit`, `--concurrency-block-hashers`, so
concurrency is Duplicati's default on a **16-CPU** machine. Heap peaked at **27.3 GB**
(`Mem peak: 27.3G`), itself anomalous and worth attention independently.

### 1c. Suggested approach

Re-run with `--log-file-log-level=Verbose` so individual PUT attempts and retry counts are
visible — "exhausted" was inferred from a stack frame, not observed. Vary concurrency
explicitly. Sample PSI *during* the run. A stack dump would settle (iii) fastest, but
**`yama.ptrace_scope` blocks `eu-stack`** — needs `sudo`. `gdb` and `eu-stack` are installed;
`dotnet-dump` / `dotnet-stack` are **not**.

---

## 2. What shipped and is verified

**PR ml#1292**, branch `feat/duplicati-scheduled-backup-lane`, 5 commits on `18760ad`.

```
util/duplicati_scheduled_backup.bash        runner, 6 guards
util/duplicati_backup_failure.bash          OnFailure reporter
util/install_duplicati_timer.bash           installer (copies, never symlinks)
util/systemd/*.{service,timer}              unit definitions
util/ad-hoc/duplicati_progress_watch.bash   stall / recovery / exit watcher
util/ad-hoc/duplicati_gpg_throughput.bash   the gpg probe (read its regime caveat)
```

- **`Linger=yes`** — the mechanical cause of the 42-day silent outage.
- **Alerting proven on a REAL failure** at 23:48:24, not a synthetic one.
- **Credentials relocated** to `~/.config/duplicati-backup/env` (0600), holding `PASSPHRASE`
  and `PASSPHRASE_OLD`. **This file is now authoritative.** The original still exists at
  `…/worktrees/curious-plotting-hummingbird/.env` — a second live copy. Reconcile or delete it
  deliberately; two copies of a live secret is the §0 divergence shape.
- **`--tempdir` fix** — Duplicati was staging 500 MB volumes in `/tmp` (**tmpfs, RAM**): 8.4 GB
  resident with swap at 17/20 GB. Now `/media/pcalnon/temp_backups/_duplicati_tmp` (ext4, a
  **sibling** of the destination, never a child). Guard 3b refuses tmpfs/ramfs. Reclaimed 7.26 GB.
- **Three CRITICAL guard defects found by validation and fixed** (commit `736eb8d`):
  guard 5 was name-anchored and missed `/usr/bin/duplicati-cli` *and* server-in-process runs —
  it now checks whether **any live process holds the dbpath open**; the skip paths reported
  success and froze `last-run.status` — they now stamp `SKIPPED` with a current timestamp and
  **escalate to a hard failure after `STALE_DAYS` (3) with no success**; the ≥12-char
  passphrase floor from `duplicati_first_backup.bash` had been dropped and is restored.

### 2a. Known gaps in the lane, deliberately not fixed

- The exclusion list is **hardcoded** in the runner; `duplicati_first_backup.bash` reads it live
  from the server DB's `Filter` table. A UI-side change will not propagate — silent drift that
  surfaces only at restore time.
- **No free-space floor** (`duplicati_first_backup.bash:44-48` refuses under 250 GB). Not urgent:
  sdc4 is 6% used, 1.7 TB free. Fails loudly if hit.
- Guard 3 confirms only that *some* `duplicati-*` file exists, not that the archive is the
  expected one.
- Guard 1 cannot detect a **wrong** passphrase — nothing can, since Duplicati will encrypt a
  fresh set under any value. This is why §4 item 2 matters.

---

## 3. Traps this session actually fell into

- **A short sample gives a confidently wrong rate.** A 110-second window read 3.6 GiB/h during a
  small-file patch; the hour-scale rate was **18.7 GiB/h**. Use `duplicati_progress_watch.bash`.
- **`read_bytes`/`write_bytes` count block-device I/O ONLY** — blind to tmpfs. Use **`rchar`/`wchar`**.
- **`ps %cpu` is a lifetime average.** Use `top -b -n 2` or two `/proc/<pid>/stat` samples.
- **PSI decays.** Sample during, not after.
- **Editing a bash script while it runs corrupts it.** `duplicati_first_backup.bash` was modified
  at 19:07:19, two hours into its 17:15 run — almost certainly a `git checkout` in that worktree
  — producing `line 116: unexpected EOF`. Both copies pass `bash -n`. Here it cost only the final
  `rc:` echo; the same mechanism silently skips any completion logic.
- **`pgrep -f <pattern>` self-matches.** Use `ps -eo args | grep '^[d]up…'` — and note even that
  is name-anchored (see §2's guard-5 fix).
- **This session's shell refuses compound commands** (`for`, `&&` chains, `git -C`). Write a
  script under `util/ad-hoc/` instead of fighting it.
- **An unmounted destination reads as "everything is missing", not as an error.** The tooling
  refuses below a floor — **any new check you write must too.**
- **`/tmp` is tmpfs**: every scratch log dies on reboot. Backup progress is re-derivable from the
  destination; **purge and drill logs are not.** Write them somewhere durable.

---

## 4. Open work, priority order

**Items 2 and 3 do NOT depend on item 1** — different job, database, destination and passphrase.
Run them in parallel if useful; the only real coupling is I/O contention.

1. **Investigate the GPG failure** (§0, §1c).

2. **Drill the fresh set — and do NOT trust the dlist until you do.**
   The set holds **1 dlist / 104 dblock / 104 dindex, 51 GiB**. ⚠ **The dlist was written by
   run 2 at 22:51:50 — 24 seconds after run 2 started — while the last real data volume landed
   at 20:47:12, over two hours earlier.** It is a *synthetic* manifest produced by a different
   run's reconciliation pass, describing a fileset whose author never certified it complete.
   Duplicati normally writes the dlist **last**, precisely so its presence guarantees
   completeness. **Calling this "a restore point" is the verdict the drill is supposed to
   establish** — and this arc exists because Duplicati once reported success while restoring
   July files as **0 bytes**. Check specifically whether the dlist references any block hash
   absent from the 104 dblocks.

   ⚠ **Both drill scripts default to the OLD archive. Pass every flag explicitly:**
   - `duplicati_drill_run.py:188` — `--dest` defaults to `file:///mnt/Backups/Ubuntu`
   - `duplicati_drill_select.py:86-87` — `--good-fileset` defaults `2025-11-12`,
     `--bad-fileset` `2026-07-11` (both old-archive dates). Against the fresh DB, pass
     `--good-fileset 2026-08-23`; otherwise the *good* group under-delivers too and a real
     misconfiguration reads as expected.
   - The predecessor's §3 item 1 command block is now **stale** — it says
     `--passphrase-file .env`, relative to a worktree that is no longer the working directory.
     Use `~/.config/duplicati-backup/env`.
   - `duplicati_drill_run.py:131,137` hard-codes `--no-local-blocks=true` and
     `--no-backend-verification=true`. **Both are mandatory.** `--no-local-blocks` defaults to
     *false*, and most drill files still exist locally — without it the drill passes without
     ever reading the archive, a false pass indistinguishable from proof. Any **manual** restore
     needs them set by hand.

3. **Predecessor §4 — the intact-arm re-run with `--time`.** Still unproven. Measured then:
   surviving-index 5 = **2025-11-12 (id 341)**, all-rows index 5 = **2026-07-06 (id 580)**, a
   *damaged* fileset; all four sampled files shared identical BlocksetIDs, so byte-identical
   output was guaranteed either way. Contends for I/O with the Recreate. `drill.sqlite` carries
   a **6.86 GB uncheckpointed WAL** from the timed-out purge dry run.

4. **Purge decision.** `list-broken-files` timed out at 90 min; `purge-broken-files --dry-run` at
   the 8 h cap. **A timeout is not a result.** `util/ad-hoc/duplicati_offline_broken_files.py`
   computed the equivalent census in ~10 minutes and is the only method that produced one.
   `util/ad-hoc/duplicati_purge_dryrun.bash <dbpath> <dest-url> <timeout-seconds>` is guarded and
   structurally cannot perform a real purge.

5. **Migration to `/mnt/Backups/Ubuntu`** — highest-stakes item, still no procedure.
   sda1 has **1.1 TB free**, so space alone does not gate it — but **space is not the gate.**
   sda1 hosts the damaged archive and **the Recreate is still writing to it** (58+ hours
   elapsed). Standing up a new ~155 GiB set there now means heavy I/O contention with a
   multi-day job against a DB known to disagree with its archive. Settle the Recreate first.
   ⚠ **`--blocksize` is IRREVERSIBLE** — "cannot be changed after remote files are created."
   The plan note records that an earlier revision recommending 500 KB was **wrong**. Current
   values live in `util/ad-hoc/duplicati_build_fresh_job.py` (the source of truth) and are
   mirrored in the runner: `--blocksize=1MB --dblock-size=500MB --skip-files-larger-than=2GB
   --no-auto-compact=true --allow-missing-source=true`. **Verify the effective value at job
   creation rather than assuming inheritance.**

6. **Enable the timer** — `systemctl --user enable --now duplicati-backup.timer` (next elapse
   02:30, `Persistent=true`). The plan's acceptance criteria are stricter than "one drill":
   a second drill from a **different** restore point after at least one incremental; survives a
   logout **and a reboot** (`Linger=yes` and `Persistent=true` are both **untested across a
   boot**); and the destination migrated to `/mnt/Backups/Ubuntu` with a full backup plus drill
   passing *there*. The failure-notification criterion **is** satisfied.

7. **Recreate disposition** — user chose **defer**. ⚠ **13 queued tasks (IDs 6–18) sit behind it**
   (task 5), and Duplicati exposes **no dequeue verb** — `task/{id}/stop` and `/abort` return 200
   and leave the task queued. **The hazard materialises if the Recreate ever COMPLETES**: it
   would rebuild a DB consistent with the destination, let pre-flight pass, and release 13
   backups against the damaged archive. Open question from the runbook, still unanswered: *why
   did Recreate take the `dblock` path when 2,682 `dindex` files are present?* A future Recreate
   will do the same.

8. Remove the root `duplicati.service` on :8200; delete `_drill_scratch` (~35 GB) and the
   **4.0 GB** stranded in `_duplicati_tmp` once the investigation no longer needs it.

### Loose ends

- ⚠ **Auto-compact is ON and retention is active on the OLD job (id 2).** An interrupted compact
  is what destroyed the July restore points. Neither `--no-auto-compact` nor any override is
  present in its settings. The **fresh** job sets `--no-auto-compact=true` deliberately.
- **Back up the server DB.** It is ~180 KB and holds job config, schedule, filters and the
  `enc-v1:` encrypted passphrase/TargetURL — cheap and disproportionately valuable. Duplicati
  must be **stopped** for a consistent copy, or use the SQLite backup API: a `cp` of a live
  WAL-mode DB can capture a torn state. Note `~/.config/Duplicati/` is an explicit exclusion in
  the fresh job, so the server DB is **not** in any backup — now structurally, not accidentally.
- **The release-train GPG private key is in no backup.**
  `…/Juniper/.gnupg/juniper-release-train.2026-07-21.private-key.pem` is mode `----------`
  (0000), so Duplicati logs permission-denied and skips it. Deliberate or accident — the user's
  call. **Permissions were not changed.**
- `duplicati_first_backup.bash:116` prints `exclusions : 44`; there are 43 (`CMD` has 12 leading
  elements, the line subtracts 11).
- **`duplicati_api.py` is broken two ways**, not merely 401: its hardcoded default `PW_FILE` is
  `.env`, which no longer exists here, so it dies with `FileNotFoundError`; and `login()` sits
  outside `call()`'s `try/except HTTPError`, so a 401 surfaces as an unhandled traceback rather
  than a status line.
- `duplicati_server_db_diff.py` keys rows by `ID` where present and **by ordinal position
  otherwise**. `Option` has no `ID`, so a reordering rewrite produces spurious diffs there —
  compare `Option` keyed by `(BackupID, Name)`. Relevant if you re-verify the §6 Schedule claim.
- Stale job description on id 2 ("Development and Documents folders"; the source is `$HOME`
  entire). The My Passport is on a **USB 2.0** controller while four faster ones sit idle —
  roughly 5–10× available. `util/ad-hoc/average_iso_size.bash` has a 10× undercount for files
  ≥10 GB (`tr -d "G."`) and fails on sub-1 GB files. Retention policy still deferred.

---

## 5. Standing prohibitions — all binding

- **NEVER run `Repair`** on the old job (id 2). It can re-upload volumes reconstructed from the
  database and delete remote volumes it does not recognise. It is the UI's default suggestion.
- **NEVER `kill -9` Duplicati.** TERM, then wait. **Diagnostic while waiting: a shrinking `-wal`
  beside a growing `.sqlite` means it is working** — that is how you tell "safely finishing" from
  "actually hung" without escalating. The old job's WAL was measured at 8.26 GB and takes many
  minutes. (TERM worked cleanly on run 1: the destination's 208 volumes and 54.55 GB were
  byte-identical afterwards.)
- **Verify the mount before ANY destination operation.** `/mnt/Backups` is *not* a mountpoint;
  `/mnt/Backups/Ubuntu` is. Unmounted, the path resolves to an empty dir on `/` **and any
  destination operation is catastrophic.**
- **`pgrep -x duplicati` is safe**; bare `pgrep duplicati` also matches the **root** daemon
  (`comm=duplicati-serve`, `Restart=always`). Never signal that pid.
- **Name the passphrase key explicitly.** Both secrets are 32 chars; neither length nor position
  distinguishes them. `PASSPHRASE` = fresh set, `PASSPHRASE_OLD` = old archive. **To confirm
  which one actually ran, compare the `sha256[:16]` prefix the runners log** — a character count
  cannot. Rotating a passphrase does **not** re-encrypt existing volumes, so `PASSPHRASE_OLD`
  must be retained indefinitely.
- **Run `duplicati_secret_check.py` whenever a long job holds a secret**, and after any edit to a
  credential file while one is running. **Exit 0 = match, 1 = DIFFER, 2 = undetermined.** On
  DIFFER, act immediately: capture from `/proc/<pid>/environ` **before the process exits**. A
  file-vs-process divergence is invisible to any check that only reads the file — this is what
  nearly cost ~40 GB on 2026-08-23.
- **Do not `git worktree remove` `curious-plotting-hummingbird`** without checking: it holds the
  original `.env` and was the failed run's `cwd`.

---

## 6. Identifiers and damage facts

| what | value |
|---|---|
| new job | `Ubuntu-fresh`, id **3** |
| new destination | `/media/pcalnon/temp_backups/Ubuntu` (sdc4 — **same physical disk as `/home`**) |
| new dbpath | `/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite` |
| staging dir | `/media/pcalnon/temp_backups/_duplicati_tmp` (ext4) |
| credentials (authoritative) | `~/.config/duplicati-backup/env` (0600) |
| runner state | `~/.local/state/duplicati/` — `last-run.status`, `failures.log`, `backup-*.log` |
| failed run's log | `~/.local/state/duplicati/backup-20260823-225125.log` |
| old job | `Ubuntu`, id **2**, dbpath `…/SJTCQIIZSJ.sqlite` — **mid-Recreate, do not use** |
| old destination | `/mnt/Backups/Ubuntu` (sda1) |
| **archived pre-deletion DB** | `/home/pcalnon/.config/Duplicati/backup SJTCQIIZSJ 20260712033545.sqlite` — 13 GB, **filename contains spaces**, **NEVER write**. Open it read-only via SQLite's URI parameter: `sqlite3.connect('file:/…?mode=ro&immutable=1', uri=True)`. ⚠ `immutable=1` is a **SQLite open flag, not a filesystem attribute** — `lsattr` shows `--------------e-------` (extent), **not** `i`. Nothing on disk protects this file: it is mode 0600 and freely deletable. It is the only pre-deletion state that exists. Do not sweep it up in any cleanup. |
| disposable drill DB | `/media/pcalnon/temp_backups/_drill_scratch/drill.sqlite` |
| Recreate pid | 2525453 (still running at handoff, 58+ h; **re-check**) |

**Damage facts** — needed before any operation on `/mnt/Backups/Ubuntu`:
the five **2026-07** restore points are broken; the five older ones — **2024-03-04, 2024-06-03,
2025-08-31, 2025-10-06, 2025-11-12** — are intact and must survive anything you do. Cause: an
interrupted compact on 2026-07-13 deleted **1,208** dblock/dindex pairs and wrote zero
replacements. Surviving volumes verified intact: **5,366/5,366 sizes exact, 30/30 sampled hashes
exact** (`util/ad-hoc/duplicati_verify_volumes.py`) — no need to re-verify.

⚠ **The `Schedule` table in `Duplicati-server.sqlite` is EMPTY** (rowcount 0, verified against a
fresh copy). Neither job is scheduled inside Duplicati; the predecessor's "schedule closed and
verified" does not hold. The systemd timer is the replacement.

---

## 7. Verify your starting state

Run these one at a time and read each result — they are deliberately not `&&`-chained, so a
"STOP" line does **not** halt the rest.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/memoized-singing-cloud
git log --oneline -3 && git status -sb          # expect clean, == origin
gh pr view 1292 --json state,mergeable

mountpoint -q /mnt/Backups/Ubuntu         || echo "OLD ARCHIVE NOT MOUNTED - STOP HERE"
mountpoint -q /media/pcalnon/temp_backups || echo "NEW DEST NOT MOUNTED - STOP HERE"

ps -eo args | grep '^[d]uplicati-cli backup'          # expect nothing
systemctl --user is-active duplicati-backup.service   # expect: failed
systemctl --user is-enabled duplicati-backup.timer    # expect: disabled  <- keep it so
pgrep -x duplicati                                    # Recreate; expect 2525453 or none

ls -1 /media/pcalnon/temp_backups/Ubuntu | wc -l      # expect 209
cat ~/.local/state/duplicati/last-run.status          # expect result=FAILED rc=100
#   ^ CHECK THE `when=` FIELD AGAINST TODAY. A stale timestamp is itself the finding.

# only meaningful once the OLD archive is confirmed mounted, above:
bash util/ad-hoc/duplicati_verify_passphrase.bash /mnt/Backups/Ubuntu \
    ~/.config/duplicati-backup/env PASSPHRASE_OLD     # expect: valid ZIP stream
```

**Git**: branch `feat/duplicati-scheduled-backup-lane`, HEAD `736eb8d` plus this handoff's own
commit. Nothing staged, nothing uncommitted once this document is committed — **commit it with
the branch**. PR **#1292** open, not merged; 16 checks were green before the last two commits and
CI re-triggers on each push — **confirm green before requesting a merge**. Merges require the
user's explicit per-PR approval.

---

## 8. Standing operating procedure

All generated content — notes, code, configs — must be validated by multiple **independent**
custom agents, including adversarial review, targeting hallucinations and untested assumptions.
Launch them concurrently in one message, give each a **different lens**, and prompt for
**refutation**, not confirmation. Treat agent output as evidence, not verdict — verify their
claims too.

That process earned its place again here. Four validators found **45 defects** in this
document's draft, including three CRITICAL guard bugs in code written the same day: a
concurrency guard that could not see the two Duplicati processes actually running on the
machine, and skip paths that reported success to systemd while freezing the status file —
which would have reproduced *this arc's founding failure*, a backup that silently stops,
inside the lane built to prevent it.

**The recurring failure shape: a correct mechanism paired with a wrong consequence.** This
session added several — a lifetime-average CPU reading, a block-I/O counter blind to tmpfs, a
110-second sample extrapolated to a 20-hour ETA, an idle benchmark used to close a
load-dependent hypothesis, and a synthetic manifest called a restore point before the drill
that would prove it. Every premise true; every conclusion wrong. **Prefer running the thing
over reasoning about it** — and check that what you ran is in the same regime as what failed.
