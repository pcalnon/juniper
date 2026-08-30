# HANDOFF 2026-08-30 — Duplicati Yamaguchi: a cleartext passphrase, two stale harnesses, the reboot

Continue the Duplicati Yamaguchi backup arc. Predecessor:
[`HANDOFF_2026-08-29_duplicati-reboot-and-root-tail.md`](HANDOFF_2026-08-29_duplicati-reboot-and-root-tail.md).
Its traps remain binding and are **not** restated — but the "not restated" chain is now **ten**
handoffs deep, so read at minimum note **§2** (the restart trap), **§8.14**, and **§8.15–§8.19** of
[`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`](../../notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md).

> **Read §0 and §1 first.** Three of the predecessor's five items are now DONE. But a validation
> pass on 2026-08-30 found a premise repeated **three** times in the note is false, and a tooling
> defect that detonates on the exact next planned action. Do not treat this arc as closed.

## §0 — The backup passphrase is stored in CLEARTEXT, and three note sections say otherwise

Verified 2026-08-30 against the live server-DB snapshot. The value in the DB and the value in
`~/.config/duplicati-backup/env` have **identical SHA-256** — byte-identical to a known plaintext,
so this is cleartext, not ciphertext:

```text
[Option] BackupID=2  Name=passphrase  length=32   <- same SHA-256 as the env file's PASSPHRASE
PASSPHRASE_OLD: 0 hits across all 16 tables / 1998 cells (correctly absent — not a Duplicati setting)
```

`duplicati-server` announces it on every start, and has all along (verbatim):

```text
No database encryption key was found. The database will be stored unencrypted. Supply an
encryption key via the environment variable SETTINGS_ENCRYPTION_KEY or disable database
encryption with the option --disable-db-encryption
```

**Three statements in the note were wrong** — all three are **corrected as of §8.20**, each with an
inline `CORRECTED 2026-08-30` marker. Referenced by section, not line number, because this session's
own edits shifted every line number below §8.6:

| Section | Said | Now |
|---|---|---|
| §8.6 item 7 | "…and **encrypted passphrase** live only in `Duplicati-server.sqlite`" | corrected; recipe retargeted |
| §8.18.2 | "…job definition, filters, schedule **and the encrypted passphrase**" | corrected inline |
| §8.19.3 | "the passphrase inside this DB **is encrypted**" | corrected; the circularity conclusion survives, the premise did not |

The §8.6 one is notable: the 08-29 session **quoted that subsection** for its copy-recipe finding and
read past the false word inside it. Quoting a section is not reading it.

**Scope it honestly — the snapshot is NOT a new leak.** An earlier handoff in this chain overstated
a finding of exactly this shape and contradicted itself two items later; a first draft of *this*
document did it again and was caught in validation. The accurate position:

- The snapshot grants the `pcalnon` user **nothing new** — `~/.config/duplicati-backup/env` is
  already `-rw------- pcalnon` cleartext.
- The archive **already contained** a cleartext copy, via the stray `.env` of §8.18.2.
- Inside the archive it is ciphertext-within-ciphertext, under the very key it holds.

**What the finding actually changes is the handling class of the DB, plus one latent hazard:**

> §8.6-7's recipe copies `Duplicati-server.sqlite` into `/mnt/Backups/Ubuntu/_yamaguchi_records/`,
> which is mode **0775** — group- and other-readable. Its sibling `_yamaguchi_keys/` is correctly
> **0700**.
>
> **This is latent, not live.** `namei -mo` shows the parent `/mnt/Backups/Ubuntu` is **0770**, so
> "other" cannot traverse to it today, and `pcalnon` is the only human account (`uid>=1000` yields
> `pcalnon` and the `libvirt-qemu` service account; group `pcalnon` has no extra members). Do **not**
> write that it "publishes the key to any local account" — that is false, and it was the exact
> error validation caught. The hazard is that a cleartext key would sit in a permissive directory
> protected only by one ancestor's mode: a later `chmod` on `/mnt/Backups/Ubuntu`, or a second
> account, converts it into a real leak with no further warning.

**Owner decision taken 2026-08-30: accept as-is and document it.** Rejected: `SETTINGS_ENCRYPTION_KEY`
(adds a *third* key needing escrow, and losing it makes the server DB unreadable — worse recovery
story), and excluding the snapshot from the backup (defeats its purpose; the archive already holds a
cleartext copy anyway).

**Both actions are DONE in §8.20**: all three sections corrected, and §8.6-7's recipe retargeted from
`_yamaguchi_records/` to `_yamaguchi_keys/`. Nothing is outstanding here — it is recorded so a fresh
session does not "rediscover" it as new, and so the *reasoning* survives if someone later proposes
encrypting the DB.

## §1 — Both #1319 restore-integrity harnesses break the moment you reboot

Not previously recorded **anywhere** — not in the note's 1874 lines, not in any of the ten handoffs.
Found by adversarial completeness audit, then confirmed in source:

| File | Line | Gate |
|---|---|---|
| `util/ad-hoc/duplicati_dlist_crosscheck.py` | 113 | `if not os.path.ismount("/media/pcalnon/temp_backups"): fail(...)` |
| `util/ad-hoc/duplicati_decrypt_validate_all.bash` | 26 | `mountpoint -q /media/pcalnon/temp_backups \|\| fail` |

**Both gates are hardcoded and fire regardless of the destination actually being checked** —
`--dest` (py) and `$1` (bash) do not influence them. Their defaults also still point at the
pre-migration `/media/pcalnon/temp_backups/Ubuntu`.

**Why this collides with the next planned action:** criterion 5 is a reboot, and sdc4 is not in
fstab, so it will not remount. At that point both harnesses — the two scripts
`tests/test_duplicati_restore_integrity.py` exists to pin — refuse to run against **any**
destination, including the live sda1 Yamaguchi backup they exist to validate, with a `FATAL: not
mounted` that has nothing to do with the destination.

This is the **same defect class** the note found and fixed in five other tools (§8.13.2, §8.14.2:
"a hardcoded path in a checker does not fail loudly when it drifts; it produces a confident,
well-formatted, wrong answer"). It survived because the hunt used
`grep -rn 'temp_backups/Yamaguchi' util/ad-hoc/` — and these two files contain
`temp_backups/**Ubuntu**`, so that grep structurally could not find them. **Re-run that sweep with a
pattern matching the mount, not the job name.**

## Where the predecessor's five items now stand

| # | Item | State on 2026-08-30 |
|---|---|---|
| 1 | Key escrow | **HALF DONE** — sda1 copy verified; **offline copy still owed** |
| 2 | Server-brain DB | **DEPLOYED**, capture not yet confirmed (see below) |
| 3 | Loopback hardening | **DONE** — verified bound to `127.0.0.1` |
| 4 | Reboot (criterion 5) | **NOT DONE** — uptime 13 d |
| 5 | Two residuals | `_drill_scratch` sync **CLOSED** (§8.19.6); user-lane removal PR still open |

**Item 3 landed and the §2 trap did not fire.** `/etc/default/duplicati` active line is now
`DAEMON_OPTS="--webservice-port=8300 --portable-mode"`; the commented trap line (which omits
`--portable-mode`) is untouched; rollback file `duplicati.bak-20260830-010814` exists; journal says
*"listening on localhost, port 8300"*; `ss` shows only `127.0.0.1:8300` and `[::1]:8300`; the census
still finds job 2 and reconciles `-> AGREE`.

**Item 2 is deployed, but "deployed" is not "protected".** `yamaguchi-server-db-snapshot.timer` is
`enabled`, next elapse 08:45 CDT (**13:45Z**), and the first snapshot is on disk — 160 KB,
`integrity_check` = ok, 16 tables, 0600 in a 0700 dir. It is inside Source `/home/pcalnon/` and
matched by no filter, **so the 14:00Z run should capture it — but that run has not happened yet.**
The guarantee this control exists to provide is one scheduled run away from being confirmed. Verify
it after the next run rather than assuming; do not mark §8.19.8 item 2 closed until then.

## Corrections to the inherited chain

1. **`ProgramState=Paused` is not an incident.** The server restarted 01:08:45 CDT (item 3) and
   `startup-delay=30m` pauses it for the following half hour (`paused-until = 0`, i.e. no manual
   pause). There was **no reboot**: `journalctl --list-boots` shows a single boot ID spanning
   08-16 → 08-30, and sdc4 is still mounted.
2. **"`PASSPHRASE` survives only as root-only material in a single unbacked-up DB"** (predecessor §0)
   is now false three ways: an sda1 escrow copy exists, the DB copy is `pcalnon`-readable, and the
   value was never root-*only* — the `env` file always had it in cleartext.
3. **The census baseline is 823 files / 212,009,670,891 B**, not 818 (recorded in §8.19.7). Still
   `-> AGREE`. `LastRun=2026-08-29T14:00:00Z`; next `2026-08-30T14:00:00Z`.

## Remaining work, in severity order

1. **§1 — de-drift the two #1319 harnesses** so their mount gate follows the destination instead of
   a hardcoded scratch path, and re-run the stale-path sweep with a mount-shaped pattern. Do this
   **before** the reboot, or the first post-reboot validation attempt fails confusingly.
   **This is the only genuinely unstarted engineering task left in the arc.**
2. **The offline escrow copy — still owed, and the last single point of failure.**
   `~/.cache/yamaguchi-key-escrow-sheet.txt` (0600, present, unprinted) holds both passphrases.
   `.cache/` is **filter 36**, so it is excluded from the archive by construction — do not
   "helpfully" relocate it somewhere backed up. Print → store off-machine → `shred -u`. **Until
   then `PASSPHRASE_OLD` has no copy outside physical disk `sdc` + sda1**, and it is the only key
   to the ten dlists that are the sole record of the purged 2.3 TiB archive.
3. **Criterion 5 (reboot).** `util/ad-hoc/yamaguchi_reboot_verify.bash pre|post` is written, and
   both lanes were executed on the live system — **that PASS is about the script, not the criterion;
   nothing has rebooted.** Traps it already encodes, do not re-derive them: `systemctl --user
   is-enabled` and `loginctl … Linger` **cannot fail because of a reboot** (they read a symlink and
   a persisted file), and "`LAST` is after boot" is a **false negative on a healthy reboot** (the
   watchdog is `OnCalendar=12:00 Persistent=true`). The real evidence is that `systemctl --user`
   **connects at all**. After a reboot sdc4 will be absent, which also makes
   `yamaguchi_retire_tier3.py` refuse at gate 0 (`not a mountpoint`, exit 3) and the durability
   check print `ABSENT` rather than `NOT DURABLE` — neither is a fault.
4. **Confirm the server-DB snapshot is actually captured** in a *completed* backup after the next
   14:00Z run — deployment is confirmed, capture is not. Only then close §8.19.8 item 2.
5. **§8.8's `.env` sha256 reconciliation** — still unreconciled, still the precondition for sweeping
   `…/juniper-ml/.claude/worktrees/curious-plotting-hummingbird/`. Its `.env` is **git-ignored**, so
   `git worktree remove` deletes it **silently**. Risk is now lower — with the sda1 escrow in place
   it is no longer the only recoverable copy of `PASSPHRASE_OLD` — but it is still a cleartext key
   inside a backup Source.
6. **Cloud reporting** (§8.18.4) — owner-**deferred, not rejected**. `remote-control-enabled = True`
   and `additional-report-url` embeds a long-lived bearer JWT (`iss=api.duplicati.com`,
   `exp=2028-08-24`). A credential, not merely a URL.
7. **The disabled `duplicati-backup.*` user lane** (§8.11.3) — removal PR still unopened. The lane
   fails safe. **Do not "repair" its paths** — that re-arms a CLI lane that is 0-for-3.
8. **Two §7 items orphaned since the note's first snapshot** (2026-08-25), never re-asked in 19
   addenda: the root `duplicati.service` **on 8200 was repurposed to 8300 rather than removed**
   (note line 193), and the **schema-19 profile server DB** (jobs `Ubuntu`/`Ubuntu-fresh`) is
   orphaned from any running server, openable by 2.3.0.4+ if ever needed (lines 194-195). Both are
   informational, neither is a live hazard — but nothing in the record closes them.

> **Not in this arc**, and deliberately not carried here: the `util/juniper-backup.bash` per-repo
> tarball lane (handoff `HANDOFF_2026-08-27_…`) is a different mechanism this note never covers.
> Its class-2 restore drill **is closed** (ml#1442, merged) — an audit pass in this session
> initially reported it as still owed; that was wrong.

## Key context a fresh session will otherwise get wrong

- **The ten retained dlists cannot RESTORE.** They record what existed across ten restore points
  2024-03-04 → 2026-07-11. Keep all ten: the Llama-2 / CodeLlama weights appear only in earlier
  filesets. **The directory is `Llama2`, no hyphen** — searching `Llama-2` returns 0 in *every*
  dlist, including the two holding the weights. Control query: `rust_mudgeon/adamo/Cargo` → exactly
  3 entries.
- **sdc3 (`/home`) and sdc4 (`/media/pcalnon/temp_backups`) are the same physical disk `sdc`.**
  `st_dev` distinguishes them, so any "is this really a second copy" check that stops at filesystem
  identity passes wrongly. `yamaguchi_key_escrow.py` resolves the parent block device via
  `/sys/class/block` for this reason and refuses an sdc4 destination.
- **`OnCalendar` defaults to LOCAL time.** The backup is fixed at 14:00**Z**, so the snapshot timer
  is pinned `13:45:00 UTC`. Under CDT both forms resolve identically — the bug would appear only at
  the DST change. Do not "simplify" the suffix away.
- **`old_archive_purge.py` and `yamaguchi_retire_tier3.py` are safe to re-run** (content-idempotent,
  though not inert). **The three live-config editors are the opposite**:
  `yamaguchi_edit_setting/sources/target.py` are `--dry-run`-**opt-in** — omitting the flag sends
  the live `PUT`. `yamaguchi_edit_sources.py` is **remove-only**; there is no `--add`.
- **`safe_merge.py` exits 0 without merging** — look for the literal `MERGED` line. A
  `REFUSED: is MERGED, not OPEN` is *success* (an auto-merge net landed it); verify content on `main`.
- **A note citing a handoff by filename requires that file to be committed.**
  `tests/test_thread_handoff_archive.py` globs the filesystem, so it **passes locally and fails in
  CI** while the file is untracked. Commit the handoff and any note citing it in the same PR. (That
  test scans only `notes/*.md`; handoff-to-handoff citations inside `prompts/` are not covered.)
- **`gh pr checks` exits 8 while any check is pending** (confirmed in gh 2.46.0 source) — a `set -e`
  script stops there; that is not a failure.

## Verify starting state

Run from a worktree of `juniper-ml` on current `main`. `yamaguchi_server_api.py` hardcodes its
credential file to the **primary** checkout's `.env`, so the API-backed commands need that file.

```bash
git fetch origin && git status -sb
python3 util/ad-hoc/yamaguchi_census.py --runs 1        # expect "-> AGREE"
df -h /mnt/Backups/Ubuntu /media/pcalnon/temp_backups   # sda1 199G/6%; sdc4 197G/12%
ss -ltn | grep 8300                                     # 127.0.0.1 and [::1] ONLY, not *:8300
grep -n DAEMON_OPTS /etc/default/duplicati              # active line must keep --portable-mode
systemctl list-timers yamaguchi-server-db-snapshot.timer --no-pager
ls -la ~/.local/state/duplicati-server-db/              # snapshot present, 0600
ls -la ~/.cache/yamaguchi-key-escrow-sheet.txt          # PRESENT = offline escrow still owed
ls -la /mnt/Backups/Ubuntu/_yamaguchi_keys/             # env 0600 in a 0700 dir
sha256sum ~/.config/duplicati-backup/env /mnt/Backups/Ubuntu/_yamaguchi_keys/env   # must match
cat ~/.local/state/duplicati/server-watchdog.status     # check the TIMESTAMP, not the word OK
grep -n 'ismount\|mountpoint -q' util/ad-hoc/duplicati_dlist_crosscheck.py util/ad-hoc/duplicati_decrypt_validate_all.bash   # §1: still hardcoded?
```

Expected: live set `823 files / 212,009,670,891 B`; next run `2026-08-30T14:00:00Z`. `ProgramState`
is `Running` unless the server restarted within the last 30 min (`startup-delay=30m`).

## Git / session state

Branch `docs/handoff-duplicati-arc-remaining-work`, based on `69829e01`. The predecessor's work
merged as **#1473** (`00c90942`); #1463 merged earlier as `a9a95614`. No open PRs in this arc.
Derive the head with `git rev-parse --short HEAD` rather than trusting this document. The primary
checkout **is** synced — that was the precondition for item 2's deploy — but re-check it before
deploying anything else whose unit `ExecStart` names it.

*Length ~2,400 words against the procedure's ~500 guidance. Deliberate — §0 and §1 are corrections
of the record, and the reboot false-negatives are not safely compressible — and recorded here rather
than left as a silent breach. This document was adversarially validated by three agents on separate
lenses (fact-check, completeness/amputation, reproducibility); §1 and the §0 over-statement were
both found by that pass and would otherwise have shipped.*
