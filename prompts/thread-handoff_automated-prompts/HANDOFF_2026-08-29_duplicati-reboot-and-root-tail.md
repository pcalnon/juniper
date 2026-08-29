# HANDOFF 2026-08-29 — Duplicati Yamaguchi: key escrow, the server brain, then the reboot

Continue the Duplicati Yamaguchi backup arc. Predecessor:
[`HANDOFF_2026-08-28_duplicati-tempdir-moved-drill-de-drifted.md`](HANDOFF_2026-08-28_duplicati-tempdir-moved-drill-de-drifted.md).
Its traps remain binding and are **not** restated — but note that the "not restated" chain is now
nine handoffs deep, so read at minimum note **§2** (the restart trap — *not* reachable from the
§8.15–§8.17 pointer below), **§8.14**, and **§8.15–§8.17** of
[`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`](../../notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md).

> **Read §0 before anything else.** The retirement/cleanup phase of this arc is finished, but a
> validation pass on 2026-08-29 found a restorability gap that outranks every item previously
> tracked. Do not treat this arc as closed.

## §0 — FIRST: the key to the backup is excluded from the backup, and shares a disk with the sources

Not previously recorded anywhere. Verified 2026-08-29:

| what | path | device |
|---|---|---|
| backup **sources** | `/home/pcalnon/` (+ one VDI) | **sdc3** |
| **the passphrase file** | `/home/pcalnon/.config/duplicati-backup/env` (388 B, 0600) | **sdc3** |
| "second copy" (196 GB, frozen) + dlist mirror | `/media/pcalnon/temp_backups/` | **sdc4 — same physical disk `sdc`** |
| destination (210 GB ciphertext) | `/mnt/Backups/Ubuntu/Yamaguchi` | sda1 |

`env` holds `PASSPHRASE` (AES key for the whole 210 GB destination) and `PASSPHRASE_OLD` (the only
key to the ten retained dlists — the sole surviving record of the purged 2.3 TiB archive). **Live
filter 43 excludes `/home/pcalnon/.config/duplicati-backup/` from the job**, so the key is not in
the backup. Lose the physical disk `sdc` — the event this backup exists for — and the sources, the
second copy, the dlist mirror and the key all go together.

**Do not overstate it** (an earlier draft did, and contradicted itself two items later): a recovery
route *does* survive, because `Duplicati-server.sqlite` sits on `/` (nvme0n1p5) and holds the
encrypted passphrase. The accurate claim is that **`PASSPHRASE` survives only as root-only material
in a single unbacked-up DB**, and **`PASSPHRASE_OLD` has no surviving out-of-band copy at all** — it
is recoverable only *through* `PASSPHRASE`, by restoring the stray `.env` below from the backup. One
further failure of that DB makes both keys unrecoverable. Full statement in note §8.18.

**Action (needs Paul):** agree an escrow for `PASSPHRASE` that is **off `sdc` and outside the
ciphertext** — printed/offline, or on sda1, or both. Do not "fix" this by moving the file inside a
Source: that puts the key inside the archive it unlocks.

**Trap before you tidy:** §8.8 wants that stray `.env` swept as secrets sprawl, and sweeping it
**removes the only in-backup copy of `PASSPHRASE_OLD`**. Escrow first, sweep second.

**Recorded durably in note §8.18** — read that, not this section, as the authority; a finding that
lives only in a handoff dies with it. To re-derive the filter list use
`python3 util/ad-hoc/yamaguchi_config_record.py --out <file>` (44 filters, 2 Sources; filter 43 is
the exclusion). `yamaguchi_server_api.py export` fails `400`; `GET /api/v1/serversettings` returns
**200** through the tool's login path.

Related and still open from §8.8, never reconciled: `…/juniper-ml/.claude/worktrees/`
`curious-plotting-hummingbird/.env` (114 B, Aug 23) contains `export PASSPHRASE=` and
`export PASSPHRASE_OLD=` in cleartext. It is **git-ignored**, so `git worktree remove` deletes it
**silently** — do not sweep that worktree until §8.8's sha256 reconciliation is done. It is inside
Source `/home/pcalnon/` and matched by no filter, so it is simultaneously a secrets-sprawl item and
(accidentally) the only in-backup copy of `PASSPHRASE_OLD`.

## Corrections to the inherited chain

One predecessor statement is now false, one was false when written, and one note statement is stale:

1. **"PR #1433 open, unmerged"** (predecessor, now false) — merged 2026-08-28 21:27Z as `ef88fcfb`.
2. **"the records mirror on sda1 has NOT been re-synced"** — already current. The sync transferred
   nothing; verified directly (73 files each side, identical lists, newest `results.json`
   byte-identical). Do not re-run it expecting work.
3. **Note §7's "loopback is already staged in `/etc/default/duplicati` pending restart"** — stale;
   Paul overwrote it 2026-08-25 14:14 closing the restart trap. See item 3 below.

## Completed this session (2026-08-28 → 29)

| PR | state | what |
|---|---|---|
| #1445 | **MERGED** `43b07e2f` | §8.15 — purge made decidable |
| #1448 | **MERGED** `f50d04c8` | §8.16 — purge executed |
| #1463 | **OPEN, CI GREEN, `mergeStateStatus=BEHIND`** | §8.17 + §8.18 — Tier 3, the tool fixes, and this handoff |

- **Purge, option (b)**: 5,356 volumes deleted, **2.3 TiB freed**; ten dlists kept (933 MiB),
  **mirrored to sdc4** at `_old_archive_dlists/`, plus a `README.md` at the archive root
  (**sda1 only — the README is not mirrored**). sda1 **74 % → 6 %**.
- **Tier 3**: 98.7 GiB = 34.8 GiB drill temp SQLite + 63.9 GiB drill `restored/` + the empty old
  tempdir. sdc4 **17 % → 12 %**.

> **Step 0 — land #1463 before any of the numbered work below.** `python3 util/safe_merge.py --pr
> 1463 --merge-method squash --execute` (it handles `BEHIND` by syncing and re-waiting). The
> 98.7 GiB deletion has already happened on disk; §8.17 and §8.18 are its only durable record and
> they are still only on this branch. This is a prerequisite, not a work item — the numbered list
> below starts at key escrow.

**Two blockers that were live earlier are now cleared — recorded because both classes recur.**
(a) §8.17.5 cites this handoff by name and `tests/test_thread_handoff_archive.py` requires every such
citation to resolve to a file in the archive directory. While the handoff was untracked the test
**passed locally and failed in CI** on 3.12/3.13/3.14 plus Quality Gate — a local-green/CI-red
divergence, so never conclude from a green local run that a note-to-handoff reference is sound.
(b) An "Empty except" CodeQL thread on `util/ad-hoc/yamaguchi_retire_tier3.py` went
`isOutdated=true` when the code was fixed but stayed `isResolved=false`, and an unresolved thread
blocks the merge on its own; it was cleared with the GraphQL `resolveReviewThread` mutation. A green
rollup does not clear it.

The 98.7 GiB deletion has already happened on disk; its only durable record is on that unmerged
branch. Land it before starting anything else.

## Remaining work, in severity order

1. **Key escrow (§0)** — root/owner decision. Highest consequence.

2. **Server-brain DB — and it is not the DB the last handoff named.** Two different databases live
   in root-only `/usr/lib/duplicati/data/` (`drwx------ root root`), and they have opposite loss
   profiles:
   - `BMXWPAOGLP.sqlite` — the per-job **local index**. Recreate rebuilds it from the destination.
     Slow, not fatal.
   - `Duplicati-server.sqlite` — the **brain**: job definition, 2 sources, 44 filters, 10 settings,
     the schedule, and the **encrypted passphrase**. Recreate does **not** restore it. On `/`
     (nvme0n1p5), this is the **only Yamaguchi key material that survives an `sdc` failure**.

   Note §8.6-7 gives a `sqlite3.backup()` recipe, but it writes to
   `/mnt/Backups/Ubuntu/_yamaguchi_records/` — **which is on sda1 and is not a backup Source**, so
   running it verbatim leaves "the brain is in no backup" exactly as true as before. Options for
   Paul: an automated root-owned copy into a non-excluded path (a one-shot decays — the DB advances
   every run), or accept Recreate for `BMXWPAOGLP` and solve key escrow separately under §0. Note
   also that copying a live SQLite file is not consistent without `sqlite3.backup()`, and that
   `yamaguchi_edit_sources.py` is **remove-only** (`--remove` is required; there is no `--add`), so
   "just add the directory to Sources" has no tooling today.

3. **Loopback hardening (root) — the file ships the trap pre-written.** `/etc/default/duplicati` is
   world-readable and currently contains *both* of these lines:

   ```
   DAEMON_OPTS="--webservice-interface=any --webservice-port=8300 --portable-mode"
   # DAEMON_OPTS="--webservice-interface=loopback --webservice-port=8300"
   ```

   **The commented line omits `--portable-mode`.** Swapping the comment markers — the most natural
   way to make this change — reproduces the restart trap (note §2) that cost this arc a full
   session. **Edit the active line in place; never activate the commented one.** `ss -ltn` shows
   `LISTEN *:8300` so narrowing the bind is measurable, but `ufw` is active, so this is
   defence-in-depth rather than closing live exposure — it is genuinely the least urgent item here.
   Restart only with `ActiveTask: null`. Ask Paul before editing.

   Two things that change what this item actually *is*: the server DB **already stores
   `server-listen-interface = loopback`** — the command line is what overrides it, so the minimal
   fix may be *deleting* `--webservice-interface=any` rather than adding `=loopback`. And the
   interface is not the whole exposure surface: `remote-control-enabled = True` with an
   `additional-report-url` pointing at `https://ingress.duplicati.com/backupreports/…`, i.e. backup
   reports are being sent to Duplicati's cloud service. Worth putting to Paul in the same
   conversation; it is a separate decision from the bind address.

4. **Criterion 5 (reboot) — Paul deferred it 2026-08-29.** Do not reboot without his say-so.
   Risk is lower than when written: every path the job needs is fstab-managed (destination
   `/mnt/Backups/Ubuntu`, tempdir `/home/pcalnon/.cache/duplicati-tmp`, sources `/home/pcalnon/`,
   both DBs under `/`), and **sdc4 is not in fstab but the job no longer touches it**.

   **Two of the three checks the predecessor chain proposed cannot fail because of a reboot** —
   `Linger` is persisted in `/var/lib/systemd/linger/pcalnon`, and `systemctl --user is-enabled`
   reads a symlink in `timers.target.wants/`. Both already report the expected value *now*. They
   test configuration, not survival. The real question — does the **user manager** come up without
   a graphical login — needs a check that can actually fail:

   ```bash
   # BEFORE: never reboot mid-run. Next scheduled run is 14:00Z daily (09:00 CDT).
   python3 util/ad-hoc/yamaguchi_server_api.py status    # require ActiveTask: null, empty queue
   # AFTER, without logging in graphically:
   systemctl is-active duplicati.service                 # expect: active
   systemctl --user list-timers yamaguchi-watchdog.timer # must CONNECT and show NEXT populated
   systemctl --user start yamaguchi-watchdog.service     # oneshot: forces a run NOW
   cat ~/.local/state/duplicati/server-watchdog.status   # NOW the timestamp must be post-boot
   ```

   **Do not use "`LAST` is after the boot time" as the criterion** — it produces a false negative on
   a *healthy* reboot. The timer is `OnCalendar=*-*-* 12:00:00` with `Persistent=true`, so it only
   catches up if a 12:00 elapse point was crossed while down; reboot at any other hour and `LAST`
   legitimately stays pre-boot for up to ~23 h. Waiting for the 09:00 backup does not help either —
   it is three hours *before* the 12:00 watchdog. Hence the explicit `start` above: it is a
   `Type=oneshot`, safe to trigger on demand, and it refreshes both artifacts immediately. That
   `systemctl --user` connects at all is itself the evidence the user manager came up without a
   graphical login, which is the failure this criterion is really about.

   `server-watchdog.status` has **no freshness component** — it would read `OK` forever if the
   watchdog died, so check the timestamp, not the word. (The unit's `ExecStart` points at the
   **primary** checkout, not this worktree.) Also: under linger with no session,
   `notify-send` has nowhere to go, so the alert degrades to file-only — that is how an earlier
   outage went unnoticed. Then let one full scheduled run complete.

   **`startup-delay = 30m` is set on the server.** For the first half hour after boot, job 2's
   `ProposedSchedule` can read empty or shifted. Do **not** treat that as a failed reboot — wait out
   the delay before concluding anything from the schedule.

5. **Two residuals, small but unowned.**
   - `_drill_scratch/restored/` — nine drill samples mirrored to sda1 **once**, by Tier 3's gate 5.
     `yamaguchi_records_sync.bash` cannot maintain them: it syncs four named directories and
     `--exclude='restored/'`. Either extend it (source list *and* the exclusion) or accept the copy
     is a one-shot.
   - The disabled user-lane units, and `util/systemd/duplicati-backup.*` in the repo — §8.11.3
     wanted a removal PR that was never opened. Not urgent; see the fail-safe note below.

## Key context a fresh session will otherwise get wrong

- **The ten retained dlists cannot RESTORE.** They are a record — every path, size and timestamp
  across ten restore points 2024-03-04 → 2026-07-11. `/mnt/Backups/Ubuntu/README.md` says so.
- **Keep all ten.** Older filesets hold paths the newest does not; the Llama-2 / CodeLlama weights
  (223 paths — 130 under `llama/`, 93 under `codellama/`) appear only in earlier ones. A 0-hit query
  is not evidence of absence — check the control `rust_mudgeon/adamo/Cargo` → exactly 3 entries.
  **The directory is `Llama2`, with no hyphen**: match `/Development/Llama2/`. Searching `Llama-2`
  returns 0 in *every* dlist including the two that hold the weights — an earlier draft of this
  handoff prescribed exactly that and so produced the false zero it was warning about. A bare
  lowercase `llama` is also wrong: 7 unrelated hits in the newest fileset, 323 in the 2024 ones.
- **The 196 GB frozen sdc4 copy is Paul's KEEP** — but it is a second copy on a different
  *filesystem*, **not a different physical disk**: sdc3 (`/home`) and sdc4 are both `sdc`. See §0.
- **`old_archive_purge.py` and `yamaguchi_retire_tier3.py` are safe to re-run** now — repeat
  `--execute` leaves the README byte-identical and the 9 samples intact. Precisely: *content* is
  unchanged, but they are not literally inert — the purge still re-mirrors and sha256-verifies
  933 MiB and re-runs its gate-5 probe, and Tier 3 still re-copies the samples. Both were fixed
  2026-08-29 after validation found a second `--execute` would have rewritten the archive README to
  "0 volumes (0 B)" (keeping the hardcoded date, so the corruption still read as authentic), that
  Tier 3 rmtree'd the preserved samples before re-copying them, and — in the *fix* — that the swap
  could promote a stale leftover over the good copy.
  **The three live-config editors are the opposite** — `yamaguchi_edit_setting/sources/target.py`
  are `--dry-run`-*opt-in*, i.e. they write to the live job by default.
- **The disabled user lane fails safe.** `duplicati-backup.timer` is `disabled`; its runner's
  `DEST_PATH`/`TEMP_DIR` defaults point at deleted directories and its own
  `[[ -d "${DEST_PATH}" ]] || fail` refuses. (Precisely: it still does `mkdir -p "$STATE_DIR"` and
  `fail()` writes a log line first — **nothing reaches the destination**, which is the material
  point, but it is not literally "writes nothing".) **Do not "fix" those paths** — that re-arms a
  CLI lane that is 0-for-3.
- **`safe_merge.py` exits 0 without merging.** Look for the literal `MERGED` line. It refused twice
  this session: once on an unresolved CodeQL thread (green checks; the thread was `isOutdated=true`
  but `isResolved=false`, cleared via the GraphQL `resolveReviewThread` mutation), once on the red
  CI above.

## Verify starting state

**Run from the worktree `.claude/worktrees/golden-painting-kazoo`, not the primary checkout** —
`util/ad-hoc/yamaguchi_retire_tier3.py` exists only on the unmerged branch. Note that
`yamaguchi_server_api.py` hardcodes its credential file to the **primary** checkout's `.env`, so the
four API-backed commands depend on that file existing there.

The worktree isolation hook does **not** refuse plain `&&` chains (a belief carried in
`yamaguchi_records_sync.bash:9` and, until round 2 of validation, in this document). What it refuses
is **git aimed at another checkout** — a `cd <other-worktree> && git …` or `git -C <other-worktree>`
— plus a complexity heuristic on multi-statement lines. `gh pr checks` **exits 8** while any check is
pending, so a `set -e` script stops there; that is not a failure.

```bash
git fetch origin
git status -sb
gh pr view 1463 --json state,mergeStateStatus,autoMergeRequest --jq '"state=\(.state) merge=\(.mergeStateStatus) auto=\(.autoMergeRequest != null)"'
gh pr checks 1463
python3 util/ad-hoc/yamaguchi_census.py --runs 1     # expect literal "-> AGREE", 818 files
bash util/ad-hoc/yamaguchi_destination_durability_check.bash   # sda1 DURABLE; sdc4 NOT DURABLE
cat ~/.local/state/duplicati/server-watchdog.status  # check the TIMESTAMP, not just "OK"
python3 util/ad-hoc/yamaguchi_retire_tier3.py        # dry run; deletion set now 0 B
ls /mnt/Backups/Ubuntu/                              # 10 dlists, README.md, Yamaguchi/, _yamaguchi_records/, lost+found, temp/
```

Expected now: sda1 `198G / 6% / 3.3T avail`; sdc4 `197G / 12% / 1.6T avail`; live set
`818 files / 210,901,216,426 B`; next run `2026-08-29T14:00:00Z`.

**After a reboot these expectations change**, because sdc4 is not in fstab and will not be mounted:
`yamaguchi_retire_tier3.py` **refuses at gate 0** (`not a mountpoint`, exit 3) and the durability
check prints `VERDICT : ABSENT` for sdc4, *not* `NOT DURABLE`. Neither is a fault — remount sdc4
(or skip both) and re-run.

## Git / session state

Branch `feat/yamaguchi-tier3-retirement`, **one signed commit, pushed, working tree clean**; PR
#1463 open, CI green, `BEHIND`. Worktree `.claude/worktrees/golden-painting-kazoo`, session
"duplicati closeout". Read the head SHA from `git rev-parse --short HEAD` rather than from this
document: the branch was force-pushed twice during validation (an earlier `f2b96c8e` is **no longer
an ancestor**), and a handoff that names a superseded SHA invites a reset against the wrong commit.

The branch is based on **`d1738886`** (#1462), *not* on `f50d04c8` (#1448's merge commit, **ten**
commits and ~4¾ h earlier) — derive a branch point from `git log -1 --format=%P <head>`, never from
the last PR the session merged. `origin/main` has moved on, so re-fetch; `safe_merge.py` handles the
`BEHIND` sync itself.

*Length note: ~2,500 words against the procedure's "~500 words" guidance. The deviation is
deliberate — §0 and the corrections are load-bearing — and is recorded rather than left as a silent
breach.*
