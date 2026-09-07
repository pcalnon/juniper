# HANDOFF 2026-09-07 — Duplicati Yamaguchi arc: what is left, and what will hurt you

Continue the Duplicati Yamaguchi backup arc. State below was re-verified live on 2026-09-07,
then **adversarially validated by three independent agents** (fact-check, completeness,
usability). Their findings are folded in; §6 records what they caught, because the errors
are instructive.

Document of record: `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`
(2,533 lines, newest section §8.25). Every bare `§8.x` below refers to that file. The
acceptance criteria live in a *different* file:
`notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md` §7.

**Distrust order — re-derive before acting.** Rots within a day: `LastRun`, the census
file/byte counts (they *grow*; only `AGREE`/`DIVERGE` carries signal), sda1 usage, open-PR
counts, any SHA. Rots on one owner action: sdc4's existence and mount state, the escrow
sheet's presence. Rots on any merge: "main-verify green on all 9". Stable: the sdc geometry,
the §8.x record.

---

## §0 — Verified 2026-09-07, and what is CLOSED

| Fact | Value |
|---|---|
| Backup | `LastRun=2026-09-07T14:00:00Z`, `ProgramState=Running`, census **848 files / 215,353,308,976 B → AGREE** |
| sda1 | 398 G / 12 % |
| **sdc4** | **EXISTS (1.8 T ext4, start 3813408768) but UNMOUNTED** — retired from service, **not destroyed** |
| Frozen set | `/mnt/Backups/Ubuntu/_yamaguchi_frozen_20260826/` (811 files) + sibling `_yamaguchi_frozen_20260826.README.md` |
| dlist 2nd copy | `~/.local/state/yamaguchi-old-archive-dlists/` — 10 files, 934 MB |
| Escrow sheet | `~/.cache/yamaguchi-key-escrow-sheet.txt` present ⇒ **print still owed** |
| `main-verify` | green on all 9 repos; tier-1 resolver present in all 9 |

**Closed, with the residual each closure left behind** — a section being closed does *not*
close what that section itself recorded as open:

| Closed | Residual that survives it |
|---|---|
| §8.21 harness de-drift + zero-volume vacuous pass | §8.21.5 residuals 2 & 3 (§1 item 8) |
| §8.22 the 42.6 h paused-server outage | §8.22.5's "the reboot gains a precondition" |
| §8.23 the reboot **hazard** (see §1 item 2 for its limits) | §8.23.3's *proactive* `paused-until` sample |
| §8.24 escrow interim + sdc4 scoping | §8.24.3 item 4's "re-verify after each move" rule |
| §8.25 three-lane consensus clearing sdc4 | §8.25.6 — **`sda` drive health never verified** |
| SCREENED-not-GREEN fan-out (ml#1291 → 8 repos) | drift-guard tests absent in 7 (§1 item 4) |

---

## §1 — Outstanding work, severity order

### 1. Criterion 5 — logout/login + reboot survival. NEVER EXERCISED.

**The arc's last unexercised acceptance criterion**
(`notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md` §7; the only
unchecked box in §8.7 of the certification note). `journalctl --list-boots` shows **one boot
ID, 2026-08-16 → 2026-09-07, uptime 22 days**. sdc4's unmount was manual, not a reboot.

Do not confuse this with §8.23's refuted *hazard* — that closed a risk, not the criterion.

- **`util/ad-hoc/yamaguchi_reboot_verify.bash pre` MUST run before the reboot**; `post` after.
- Post-reboot checklist (§8.19 / §8.20 lineage): `duplicati.service` active; job 2 and
  `ProposedSchedule` present; `util/ad-hoc/yamaguchi_destination_durability_check.bash`;
  `loginctl show-user pcalnon -p Linger` = yes; `systemctl --user is-enabled
  yamaguchi-watchdog.timer`.
- **Two false-negative traps.** `systemctl --user is-enabled` and `Linger` **cannot fail
  because of a reboot** — they read a symlink and a persisted file. The real evidence is that
  `systemctl --user` **connects at all**. And "`LAST` is after boot" is a false negative on a
  healthy reboot (`OnCalendar=12:00 Persistent=true`).
- Post-reboot, sdc4 is absent, so `util/ad-hoc/yamaguchi_retire_tier3.py` refuses at gate 0
  (`not a mountpoint`, exit 3), the durability check prints `ABSENT` not `NOT DURABLE`, and
  `util/ad-hoc/yamaguchi_records_sync.bash` refuses (§1 item 5). **None is a fault.**
- Owner decision: **prepare it; the owner reboots on his own schedule.**
- Combine with §8.23.3's proactive sample: **read `paused-until` during the restart's
  30-minute `startup-delay` window** — that is the baseline nobody has captured (§1 item 7).

### 2. sdc4 reclaim — cleared by CONTENT, two things still owed, and the reclaim is dangerous

**Cleared by content** (§8.25.2): all 908 files hashed full-SHA-256 both sides. But
§8.25.2's actual verdict is *"the literal claim is FALSE; the operational claim holds"* —
five paths and 17 directories exist only on sdc4. Four are telemetry JSONs (~2.3 KB); the
fifth is a zero-byte `Untitled7-checkpoint.ipynb` that **scores as "matched" only because
sda1 contains other empty files**. No sda1 file is named `Untitled7*`; no `c00` directory
exists. It is not preserved. That is the vacuous-pass class *inside* the data-loss check.

**Still owed before destruction:**

- **`sda` drive health has NEVER been checked** (§8.25.6) — no lane had passwordless sudo for
  SMART or `dumpe2fs`. Destruction makes irreplaceable manifests depend on sda alone. Read
  SMART first.
- §8.24.3 item 4's standing rule: **re-verify sda1's copies after each move, never trust a
  copy tool's exit code.** `/mnt/Backups/Ubuntu/README.md` was corrected 2026-09-02 — verify
  that, do not assume it.

**The fallback ends when the FILES go, not the partition.**
`util/ad-hoc/yamaguchi_retire_tier2.bash --execute-old-destination` deletes the ~196 G sdc4
copy; its own header calls it *"the single most dangerous delete in the arc."* Do not run it,
`util/ad-hoc/yamaguchi_retire_tier1.bash`, or `util/ad-hoc/yamaguchi_retire_tier3.py` unless
the owner names the lane.

**Grow sdc2, NOT `/home`** — geometry verified from `/sys/block/sdc/*/start` (§8.25.3):
sdc2 ends at 3,813,408,768 = sdc4's start; sdc4 ends at 7,782,432,768 = sdc3's start.
Extending sdc2 moves no data; extending `/home` relocates 3.65 TiB backwards.

> **The sdc2 grow is NOT routine.** `sdc2` is **NTFS** (`Microsoft basic data`, label
> `WindowsPrograms`) on a **GPT** disk whose `sdc1` is Microsoft Reserved — this is a Windows
> install. Toolchain is `ntfsresize`/ntfs-3g, **not `resize2fs`**, and NTFS left dirty by
> Windows fast-startup or hibernation must be cleaned from Windows first. The partition-table
> edit is on `/dev/sdc`, which also carries **live, mounted `/home`** (sdc3, 2.0 T used). Do
> it from a rescue/live boot, not a running desktop. Capture `sfdisk -d /dev/sdc > sdc.table`
> first. Order: partition, then filesystem. Nothing forces this on any schedule.

### 3. Print the escrow sheet (owner action, blocked on a printer)

`~/.cache/yamaguchi-key-escrow-sheet.txt` (0600, 1993 B). A synced password-manager copy
exists and the owner accepted it as an interim (§8.24.1) — this is a **trust-model**
improvement, not a single-point-of-failure fix: paper fails independently of an account, a
provider, and a reachable device.

`.cache/` is excluded from the archive by the job's filter list — do **not** relocate it
somewhere backed up. The sheet is **regenerable** by `util/ad-hoc/yamaguchi_key_escrow.py`
from `/home/pcalnon/.config/duplicati-backup/env`, so `shred -u` is recoverable while that
file lives. A third key copy exists at `/mnt/Backups/Ubuntu/_yamaguchi_keys/env` (388 B,
0600, in a 0700 dir).

### 4. Drift-guard tests missing in seven repos

Confirmed absent 2026-09-07: **cascor, cascor-client, cascor-worker, data, data-client,
deploy, recurrence**. The tier-1 signal in `.github/workflows/main-verify.yml` is the exact
step name `Assert screens reached a verdict`; renaming it fails nothing and silently drops the
resolver to the legacy tier.

**Reference is juniper-ml, not canopy.** `tests/test_main_verify_catchup_base.py` in
juniper-ml is 16 tests (an 11-test resolver rehearsal against a stubbed `gh`, plus a 5-test
drift class), wired at `ci.yml:451` and `main-verify.yml:443`. canopy's
`src/tests/regression/test_main_verify_catchup_base.py` is a 6-test drift-only subset whose
one unique test is the screened-tier-over-legacy ordering assertion. **Port the union.**

**Per-repo blockers — path selection is NOT the main one:**

| Repo | Blocker (verify each yourself) |
|---|---|
| cascor-client, data-client | **no PyYAML in `pyproject.toml`** — `import yaml` is a collection error, i.e. red CI, until added to the test extra |
| deploy | PyYAML also **absent from `pyproject.toml`** (an agent claimed otherwise — check the dev/test requirements path before trusting either reading) |
| cascor-worker | PyYAML present |
| cascor, data | CI filters `-m "unit and not slow"` with `--strict-markers` and no auto-marking conftest — an unmarked file is **deselected**; cascor has no `src/tests/regression/` at all |
| recurrence | app lane is path-filter gated on `^juniper-recurrence/`, so a PR touching only `.github/workflows/main-verify.yml` **skips the test job** — vacuous against its own threat model |

**The reference test raises `SkipTest`, not a failure, when misplaced — a bad port is
silently green.** Prove it ran by reading the CI log for the test name, never by a green
rollup.

### 5. `util/ad-hoc/yamaguchi_records_sync.bash` is already dead (not previously recorded)

Its `SRC_ROOT` is hardcoded to the now-unmounted sdc4 and it refuses on a `mountpoint` guard,
so the evidence mirror at `/mnt/Backups/Ubuntu/_yamaguchi_records/` is **frozen at
2026-08-30** (82 files, none newer). §8.21.3 classified this tool "sdc4 **is** the subject —
correct as written"; the retirement invalidated that classification and the sweep was never
re-run against it.

Consequence: §8.21.4's live sda1 crosscheck — which the note itself calls *"new certification
evidence in its own right"* — and all of §8.25.1's frozen-set certification exist **only as
prose in the note**, not in the durable evidence base, and no tool can now put them there.

### 6. `ProgramState` + scheduler-queue check does not exist

§8.22.3. `util/ad-hoc/yamaguchi_watchdog.py` never inspects `ProgramState`, and anchors
freshness on the newest log entry of **any** `MainOperation` — a Compact refreshes the
backup-freshness clock. Discriminator (§8.22.2): **`Paused` + a non-empty `SchedulerQueueIds`
is always a fault, whatever the uptime.**

- `SchedulerQueueIds` is **not** printed by `util/ad-hoc/yamaguchi_census.py`.
  `util/ad-hoc/yamaguchi_server_api.py status` prints it.
- **This script is DEPLOYED.** `~/.config/systemd/user/yamaguchi-watchdog.timer` is enabled;
  its `ExecStart` names the **PRIMARY checkout**
  (`/home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_watchdog.py`).
  Merging a PR changes nothing until the primary is pulled; editing the primary directly puts
  unreviewed code into the only backup-alerting lane on the next fire. Redeploy via
  `util/ad-hoc/yamaguchi_watchdog_deploy.bash` (units `util/systemd/yamaguchi-watchdog.{service,timer}`).
- The arc spans **two systemd scopes**: the watchdog is `--user`;
  `yamaguchi-server-db-snapshot.timer` is system.

### 7. The 2026-08-30 stuck pause — root cause still unknown

§8.23.2 eliminated two candidates by direct test: `startup-delay` resume works, and there were
zero suspend/sleep events. A **third is untested**: *first start after a `DAEMON_OPTS` change
behaves differently.* `journalctl -u duplicati` across 08-30 01:08 → 08-31 14:32 holds only
the start lines. A single unexplained event, not a reproducible fault.

`paused-until` read `'0'` while stuck and `''` while running; the in-window pause was never
sampled. **If it recurs, read `paused-until` BEFORE resuming** — and capture the baseline
proactively during the item-1 reboot.

### 8. Recorded so they stop dissolving

- **Deployed-vs-repo divergence.** `diff ~/.local/bin/duplicati-scheduled-backup.bash
  util/duplicati_scheduled_backup.bash` is 32 lines and is **not** about stale paths: the
  *repo* copy carries a 2026-08-29 DB-holder-detection fix the deployed copy lacks — without
  it *"a live holder went undetected and the corruption guard passed."* The deployed lane
  ships a silently-failing corruption guard. Timer `disabled`, last run FAILED 2026-08-25.
  **Do not "repair" its paths** (re-arms a lane 0-for-3); the open work is the §8.11.3
  removal PR, still unopened — it deletes `util/systemd/duplicati-backup.*` and the
  `~/.local/bin` copy.
- **No §8.26 exists.** The 2026-09-02 dlist relocation, the `/mnt/Backups/Ubuntu/README.md`
  correction, and the sdc4 unmount are recorded **only** on disk and in this handoff —
  violating the arc's own rule that a finding living only in a handoff does not survive it.
  *(This PR adds §8.26; if you are reading this later, verify it landed.)*
- **§8.21.5 residuals 2 & 3**: `util/ad-hoc/duplicati_dlist_crosscheck.py` rebinds the
  module-global `gpg_decrypt` under `--encryption aes` (an in-process caller cannot stub the
  decrypt seam — why the hermetic tests exercise gpg); and its same-filesystem workdir is a
  WARNING while `util/ad-hoc/duplicati_dlist_query.py` refuses.
- **`util/ad-hoc/yamaguchi_server_db_snapshot.py:20`** still says *"the encrypted
  passphrase"* — an uncorrected survivor of the falsehood three note sections were corrected
  for on 2026-08-30. The passphrase is **cleartext** in that DB.
- **`util/ad-hoc/duplicati_first_backup.bash`** carries the hardcoded-gate defect §8.21 fixed
  elsewhere: `DESTDIR` is `$3` but `MOUNT` is hardcoded, and both the `mountpoint` gate (L40)
  and `df --output=avail "$MOUNT"` (L44) measure the literal — L49 prints `$DESTDIR` beside a
  free-space figure from a different disk. No test pin.
- **canopy `src/tests/test_memory_budget_check.py`** is top-level, referenced by no workflow,
  outside canopy's pytest selection — it appears never to run.
- **§8.8's `.env` reconciliation.** `.claude/worktrees/curious-plotting-hummingbird/.env`
  (114 B, Aug 23) is git-ignored, so `git worktree remove` deletes it **silently**. The
  fingerprints are `PASSPHRASE → 6d8b263f6d064556`, `PASSPHRASE_OLD → b085454a8c34bd8c`
  (sha256[:16] — the **hand-reconciliation** values of §8.9-3, **not** the PBKDF2 pair
  `1ff8be45…`/`ad251cf0…`; picking the wrong scheme yields a confident mismatch).
- **Cloud reporting** — owner-**deferred, not rejected**. §8.19.8 item 6 records a bearer JWT
  with issuer `api.duplicati.com` expiring **2028** (no exact date is in the record —
  do not invent one). §8.18.4 has the `remote-control-enabled` / report-URL facts.
- **Two §8.20.4 orphans**: the root `duplicati.service` on 8200 repurposed to 8300 rather
  than removed (`ss -ltn` confirms only 8300 listens); the schema-19 profile server DB at
  `~/.config/Duplicati/Duplicati-server.sqlite` orphaned from any running server.
- **§8.10.2 remedy (iii)** — a `--run-script-before` mount guard, "the only remedy that also
  covers a destination unmounted *mid-life*", never applied or refused.
- **Alerting candidate A** — `util/ad-hoc/yamaguchi_run_script_after.bash` is a drafted,
  undeployed complement (§8.5 lineage), never revoked in 19 addenda.

---

## §2 — Traps

- **NEVER delete or move anything under `/mnt/Backups/Ubuntu/`.** "Invisible to the Duplicati
  job" means the backup will not *notice* their loss, not that they are disposable. That
  directory holds ten `duplicati-*.dlist.zip.gpg` (sole record of 5,356 volumes / 2.3 TiB
  purged 08-28, going 2 copies → 1 when sdc4 dies), `_yamaguchi_frozen_20260826/` (only copy
  of restore point `20260826T181206Z`), `_yamaguchi_keys/`, `_yamaguchi_records/`.
  `/mnt/Backups/Ubuntu/README.md` carries **operative rules** — read all of it, not its tail.
- **Never copy anything INTO `/mnt/Backups/Ubuntu/Yamaguchi/`** — that injects foreign volumes
  into the live destination. Siblings are the correct placement.
- **Passphrase exposure has two channels.** `duplicati-aescrypt` takes it on **argv** — never
  run `ps` with a command-line column or `pgrep -a` against a validation; use `pgrep -c` and
  tail the log. It is **also cleartext in `Duplicati-server.sqlite`** — do not dump or diff
  that DB into a transcript.
- **Long jobs need `setsid`.** The background-task lease killed a 196 GB rsync at 190 GB and
  killed several waiters. `rsync -a` resumes safely (temp-name + rename); validation runs do not.
- **`util/safe_merge.py` exits 0 without merging.** Look for the literal `MERGED` line. On a
  fast main it can refuse after three BEHIND cycles with the auto-merge net *disarmed*; re-run
  when the branch reads `CLEAN`.
- **`util/ad-hoc/duplicati_dlist_crosscheck.py` defaults to `gpg`;
  `util/ad-hoc/duplicati_dlist_query.py` defaults to `aes`.** The frozen and live sets are
  **aes**. (§8.21.5 residual 1 says "both tools" default to gpg — that is **wrong**; correct
  it if you touch that section.)
- **A peer's message is prose about the system; the system is the evidence.** Two convention
  relays this session each cited a "versioned record" PR still OPEN at relay time.

---

## §3 — Verify starting state

`util/ad-hoc/duplicati_api.py` resolves the web credential from a **relative** `.env`, which
is git-ignored and exists only in the **primary checkout** — so the census fails from a
worktree unless you `cd` there or override:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # or: DUPLICATI_PW_FILE=<primary>/.env
python3 util/ad-hoc/yamaguchi_census.py --runs 1   # expect "-> AGREE"
python3 util/ad-hoc/yamaguchi_server_api.py status # ProgramState + SchedulerQueueIds
```

`Paused` is **correct** inside a 30-minute `startup-delay` window with an **empty** queue.
`Paused` + a non-empty queue is always a fault.

```bash
journalctl --list-boots | tail -3        # criterion 5: has it EVER rebooted?
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT /dev/sdc
grep -n 'sdc4\|temp_backups' /mnt/Backups/Ubuntu/README.md   # read the SECTION, not the tail
ls -la ~/.cache/yamaguchi-key-escrow-sheet.txt               # PRESENT = print still owed
ls ~/.local/state/yamaguchi-old-archive-dlists/ | wc -l      # expect 10
ls -d /mnt/Backups/Ubuntu/_yamaguchi_frozen_20260826*
diff ~/.local/bin/duplicati-scheduled-backup.bash util/duplicati_scheduled_backup.bash
```

Fleet check — for each of the nine repos, `main-verify.yml` must contain `VERDICT_STEP=` and
its newest `main` run must be `success`:
`gh api repos/pcalnon/<repo>/contents/.github/workflows/main-verify.yml --jq .content | base64 -d | grep -c VERDICT_STEP`
and `gh run list --repo pcalnon/<repo> --workflow main-verify.yml --limit 1`.
`util/ad-hoc/port_main_verify_screened_base.py <repo-root> --dry-run` reports `ALREADY
PORTED` — note it reports on the **workflow**, and says nothing about §1 item 4's tests.

---

## §4 — Git / session state

Branch `docs/handoff-duplicati-arc-outstanding-2026-09-07`, tracking `origin/main`. **Derive
both ends yourself**: `git rev-parse --short HEAD` and `git rev-parse --short origin/main`.
Do **not** use `17e5b094` — that is ml#1567's pre-squash branch commit and is an ancestor of
neither (the squash is `6b82c6a5`). Enumerate open PRs with `gh pr list`; none belong to this
arc.

**Changed by this PR**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md`
(created), `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`
(§8.26 added), `util/ad-hoc/port_main_verify_screened_base.py` (nosec fix).

ml#1567 shipped `# nosec B404 - <prose>`, which bandit parses as test IDs (**eight** warnings,
not the five its commit message claimed). The fix was made but never staged — edited after
`git add` — so that commit message claims a fix that did not ship. It is corrected in this PR.
Severity is low: bandit is scoped `^(scripts|tests)/.*\.py$` **and** skips B404, so `util/`
draws no CI signal at all.

---

## §5 — Out of scope

The `util/juniper-backup.bash` per-repo tarball lane is a **different mechanism** this arc
never covers; its class-2 restore drill is closed (ml#1442). An audit pass once reported it as
still owed — that was wrong. Do not re-derive it into this arc.

---

## §6 — What the validation caught (read before trusting any future handoff)

Three agents reviewed the first draft. They found **one amputation, nine factual errors, and
four dangerous omissions** — worth recording because each is a repeatable failure shape:

1. **Amputation**: criterion 5 was missing entirely. `§8.23 the reboot hazard (refuted)` sat
   in the CLOSED list, and a fresh reader would conclude the reboot was done. **Closing a
   hazard is not closing the criterion it threatened.**
2. **Residual leakage**: every "closed" section carried its own still-open residuals out with
   it. §0 now lists them explicitly.
3. **A number quoted from my own earlier prose, not re-measured** — "five bandit warnings" was
   copied from ml#1567's commit message; it is eight.
4. **An inherited error**: "both tools default to gpg" came from §8.21.5, which is itself
   wrong. Copying a note's claim is not verifying it.
5. **A vacuous verify command**: `tail -3 README.md` cannot see the sdc4 claim it purported to
   check (that text is ~line 37) — it passes either way.
6. **A self-inflicted regression**: restoring a file from a scratchpad snapshot silently
   reverted a pre-commit auto-fix (a `with` block → bare `open()`).
7. **Over-precision**: `exp=2028-08-24` appears nowhere in `notes/`; the record says only
   "2028".
