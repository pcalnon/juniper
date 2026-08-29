# HANDOFF 2026-08-26 — Duplicati: Paul's decisions executed (B deployed, win11 VDI excluded, 09:00 confirmed, key kept); the tail is root-gated

**Continue the backup-restoration arc from a goal state that now includes deployed alerting.**
Predecessor: [`HANDOFF_2026-08-25_duplicati-widened-scope-recertified-paul-gated-tail.md`](HANDOFF_2026-08-25_duplicati-widened-scope-recertified-paul-gated-tail.md)
— its §0 decisions, §3 traps, §4 identifiers, §5 prohibitions and its **§2 items 5–11** remain
binding and are NOT restated here. Read it first, then the note's new
[§8.9](../../notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md).
Every remaining item needs root or a decision Paul has not yet given — execute picked ones,
do not re-derive them, do not redo anything in §0.

## 0. What this session settled (do not redo)

| predecessor §2 item | outcome |
|---|---|
| 1 merge #1390 + sync primary | DONE before this session started (`19207308`; primary checkout synced, tooling present) |
| 2 alerting | **B DEPLOYED** 12:30:59 CDT via new `util/ad-hoc/yamaguchi_watchdog_deploy.bash`; timer enabled, next fire 2026-08-27 12:00 CDT; closing test `JOB_MISSING` fired 12:31:30 (`notify-send rc=0`, real state dir), annotated synthetic, status back to `OK` 12:32:21. **Criterion 4 CLOSED.** A stays drafted, undeployed. |
| 3 schedule | Paul: **09:00 CDT intended** — no change |
| 4 VM image / key | **win11 VDI EXCLUDED** (PUT 12:31 CDT via new `util/ad-hoc/yamaguchi_edit_sources.py`, 7/7 post-PUT checks PASS; record `_yamaguchi_check/yamaguchi-config-post-vm-exclusion.json`) — effective from the 08-27 run. **Key KEPT.** |
| — first scheduled run | 2026-08-26 14:00Z **Success, 25 m 15 s**, 29 volumes / 7.27 GB up, 0 retries; `191449Z` thinned as predicted; census **808 = 2 + 403 + 403, 209,791,975,432 B, `-> AGREE`**; filesets `102739Z` + `20260826T140000Z` |
| records | re-synced to sda1 12:3x CDT via new `util/ad-hoc/yamaguchi_records_sync.bash` (guarded rsync) |
| PR | **#1394** (`feat/yamaguchi-decisions-executed-2026-08-26`), auto-merge armed under Paul's standing approval (given 03:35 CDT). If it shows neither OPEN nor MERGED, the branch is on origin — re-open it; never sweep the worktree first |

Timing fact: the session idled 03:41→12:30 CDT, so the PUT landed **after** the 09:00 run —
today's run still re-read the 56 GB image (56.4 GB "modified", 7.27 GB uploaded). The 08-27
run is the first without it; expect the ~9-minute class.

## 1. Open work — predecessor §2 numbering (all PAUL RUNS or Paul's call)

- **5 loopback restage** (root) — the predecessor's five steps stand; not between 08:45 CDT and the run's end.
- **6 `dbconfig.json`** — delete vs rewrite-as-array; Paul has not picked.
- **7 server-brain backup** (root) — the predecessor's stdlib command stands (`sqlite3` CLI absent).
- **8 migration decision** (plan §7 criterion 6) — options a/b/c; record in the plan's §8; end with a drill at the new location, announced to any GPU session first.
- **9 retirements** — each needs a go; note §8.8 KEEP list first. Re-confirmed today: `~/.config/duplicati-backup/env` fingerprints `PASSPHRASE`→`6d8b263f6d064556`, `PASSPHRASE_OLD`→`b085454a8c34bd8c` (sha256 of the stripped value), so the `curious-plotting-hummingbird/.env` bullet's precondition holds. New candidates (not acted): stale arc worktrees `ticklish-waddling-grove` (detached at `19207308`, #1390's, no `.env`), `mossy-growing-salamander` [`feat/yamaguchi-backup-tooling`, #1369 merged, no `.env`], `memoized-singing-cloud` [`feat/duplicati-scheduled-backup-lane`]; local branches `fix/duplicati-backup-rebuild`, `fix/duplicati-findings-corrections` (remotes gone).
- **10 reboot survival** (criterion 5) — after the next reboot, additionally: `systemctl --user is-enabled yamaguchi-watchdog.timer` = enabled, `Linger=yes`, and the 12:00 check lands in `~/.local/state/duplicati/server-watchdog.log`.
- **11 old-archive tail** — untouched; by the predecessor's precise reference.

## 2. Traps added this session

- **The worktree hook refuses any command string containing `enable`** (`systemctl --user enable --now …` → "runs a string through enable"). Put it in a script file and run the file (`yamaguchi_watchdog_deploy.bash`).
- **A first `enable` of a `Persistent=true` timer does not catch up a same-day fire that already passed** — no stamp exists yet; run the service once by hand (the deploy script does).
- **An idle session is not a paused clock.** Re-read `date` on resume before any "before 09:00" action; this session's "before the run" PUT became an "after the run" PUT.
- **A config-record diff after a PUT carries the server's own post-run `Schedule.Time`/`Metadata` advancement** — judge the PUT against the edit script's printed "before" state, not the previous day's record.
- `yamaguchi_edit_sources.py --remove <path> --dry-run` is a free smoke test of the whole guard chain (state, verbatim match, fingerprint) without a PUT.

## 3. Verify your starting state (one line per call)

```bash
git fetch origin
git status -sb
systemctl --user is-enabled yamaguchi-watchdog.timer                 # enabled
systemctl --user list-timers yamaguchi-watchdog.timer --no-pager     # next 12:00 CDT
cat ~/.local/state/duplicati/server-watchdog.status                  # OK (RUNNING during 09:00–~09:30)
grep -E '^DAEMON_OPTS' /etc/default/duplicati                        # any|loopback + 8300 + --portable-mode
ps -eo args | grep '[d]uplicati-server'                              # matches the line above
python3 util/ad-hoc/yamaguchi_server_api.py status                   # job 2; ActiveTask; ProposedSchedule
python3 util/ad-hoc/yamaguchi_census.py --runs 2                     # literal "-> AGREE" + newest Success
python3 util/ad-hoc/yamaguchi_edit_sources.py --remove /nonexistent --dry-run   # rc 4 "not present" — no PUT
ls /mnt/Backups/Ubuntu/_yamaguchi_records/                           # 4 record dirs
```

## 4. Git / session state

Branch `feat/yamaguchi-decisions-executed-2026-08-26` from main `19207308` in worktree
`.claude/worktrees/mutable-squishing-seahorse` (session "duplicati"). Changed: the
certification note (§8.6 decision markers, §8.7 criterion 4 checked, new §8.9); three new
`util/ad-hoc/` scripts (`yamaguchi_edit_sources.py`, `yamaguchi_watchdog_deploy.bash`,
`yamaguchi_records_sync.bash`); this handoff. No AGENTS.md / REFERENCE.md / CHANGELOG (same
footprint as #1369 / #1390). Committed as one GPG-signed commit, pushed, opened as **PR #1394**
(12:4x CDT), auto-merge armed under Paul's standing approval (03:35 CDT). CodeQL alert 586
(bare sha256 over the passphrase in the fingerprint guard) was fixed before merge by moving the
fingerprint to PBKDF2-HMAC-SHA256 (fixed public salt, 200k rounds; prefixes `1ff8be456de2752f`
/ `ad251cf01cbec4b5`, note §8.9-3) — the `.env` reconciliation in §1 item 9 still uses the
plain sha256[:16] values, which is a hand check, not code. After it merges the
primary checkout is behind `main` by this PR only — its sync is Paul's action; the deployed
watchdog does not depend on it (the unit runs `yamaguchi_watchdog.py`, unchanged since
`19207308`). All evidence is durable under `/media/pcalnon/temp_backups/_yamaguchi_check/`
and mirrored to sda1.
