# HANDOFF 2026-08-23 — Duplicati: fresh set running, purge pending, one claim unproven

Predecessor: [`HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md`](HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md).
Both of its blocking items (§1 `Backup.DBPath`, §2 schedule) are **closed and verified**.

Merged this arc: **ml#1263**, **ml#1268**, **ml#1269**.

> **Length deviation, declared.** The procedure asks for ~500 words; this is ~1,800. The
> predecessor ran ~1,700 for the same reason: this arc concerns a live backup system with real
> data loss, where the expensive failures come from *not knowing* a prohibition or an
> identifier. §5a and §1a exist because an adversarial review found the first draft had dropped
> the never-Repair / never-`kill -9` rules and omitted the new job's dbpath — i.e. the words
> were previously being spent on the wrong things, not merely on too many things.
Findings of record: [`notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](../../notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md) ·
Plan: [`…_DUPLICATI-FRESH-BACKUP-SET-PLAN.md`](../../notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md)

---

## 0. 🔴 READ FIRST — the fresh set's passphrase is NOT in `.env`

The `Ubuntu-fresh` backup launched 17:15 and read `PASSPHRASE` into its process environment. `.env`
was then edited at **17:45** and `PASSPHRASE` was overwritten with a *different* value (the old UI
password). From that moment the secret encrypting the fresh set existed **only inside PID 779263**.

Proven against a real volume from the fresh set:

```
captured value        DECRYPTS THE FRESH SET
.env PASSPHRASE       does not decrypt (Bad session key)
.env PASSPHRASE_OLD   does not decrypt (Bad session key)
```

**The value is captured** at `~/duplicati-Ubuntu-fresh-passphrase-RECOVERED.env` (mode 0600, outside
the repo, key `PASSPHRASE_UBUNTU_FRESH`, `sha256[:16]=6d8b263f6d064556`).

**Before anything else:**

1. Record that value in a password manager. It protects the only current copy of everything since
   2025-11-12.
2. Reconcile `.env`. If the 17:45 edit was accidental, restore `PASSPHRASE` to the captured value.
   If a different passphrase was genuinely intended for the fresh set, the running backup must be
   killed and restarted against an **emptied** destination — the runner refuses to append to a
   non-empty one precisely to prevent a half-set under two secrets.
3. Until reconciled, pass `--passphrase-key`/`DUPLICATI_PW_KEY` explicitly everywhere, and read the
   fresh set with the RECOVERED file, not `.env`.

⚠ **A file-vs-process divergence is invisible to any check that only reads the file.** The value was
verified correct at ~17:30 and drifted afterwards; nothing in the tooling would have noticed. When a
long job holds a secret, compare `/proc/<pid>/environ` against the file — all six runners now log a
`sha256[:16]` prefix so this comparison is one step.

---

## 1. Settled — do not re-litigate (but read §4 before trusting the *intact* half)

**The old archive has real data loss.** All five 2026-07 restore points are broken; the five older
ones (2024-03-04, 2024-06-03, 2025-08-31, 2025-10-06, 2025-11-12) are intact. Cause: an **interrupted
compact** on 2026-07-13 deleted 1,208 dblock/dindex pairs and wrote **zero replacements**, destroying
blocks the July filesets still referenced. The findings note reconciles this **three
independent ways** (Duplicati's own Repair error naming 1,208 volumes; a direct filesystem
check finding 1,208/1,208 absent; archived-DB arithmetic), and a restore drill then returned
July files as **0 bytes while Duplicati reported success**.

Surviving volumes are intact: **5,366/5,366 sizes exact, 30/30 sampled hashes exact**.

---

## 1a. Identifiers a fresh session needs

| what | value |
|---|---|
| **new** job | `Ubuntu-fresh`, id **3** |
| **new** destination | `/media/pcalnon/temp_backups/Ubuntu` (sdc4) |
| **new** dbpath | `/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite` |
| **new** passphrase key | `PASSPHRASE` in `.env` |
| **old** job | `Ubuntu`, id **2** |
| **old** destination | `/mnt/Backups/Ubuntu` (sda1) |
| **old** dbpath | `/home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite` — **mid-Recreate, do not use** |
| **old** passphrase key | `PASSPHRASE_OLD` in `.env` |
| archived pre-deletion DB | `/home/pcalnon/.config/Duplicati/backup SJTCQIIZSJ 20260712033545.sqlite` (13 GB, read `immutable=1`, never write) |
| disposable migrated copy | `/media/pcalnon/temp_backups/_drill_scratch/drill.sqlite` (17 GB, schema-19) |

All work runs from
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/curious-plotting-hummingbird`.

---

## 2. Process state — RE-CHECK, do not trust these lines

| process | status when this was written (2026-08-23 ~18:15) | how to re-check |
|---|---|---|
| **fresh backup** | **RUNNING** ~1h in, ~32 GB of ~155 GiB written | `ps -eo args \| grep '[d]uplicati-cli backup'` |
| **purge dry run** | **DEAD — timed out** at 14:56, `rc: 124`, no result | `tail -4 <log>`; see §3.3 |
| **Recreate** | RUNNING, task 5, ~47 days left, 13 backups queued behind it | `pgrep -x duplicati` |

⚠ **`pgrep -f '<pattern>'` matches its own command line.** Checking for a dead process this way
returns a false "running" because the `pgrep` invocation itself contains the pattern. This produced a
wrong status line in the first draft of this very document. Use `ps -eo args | grep '[d]up...'` (the
bracket trick) or `pgrep -x`.

⚠ `/tmp` is **tmpfs** — every scratch log dies on reboot. Progress is re-derivable from the
destination (`du -sh /media/pcalnon/temp_backups/Ubuntu`); the purge/drill logs are not.

## 3. Remaining work, in priority order

1. **Finish + verify the fresh backup**, then run a restore drill against the NEW set. This is the
   acceptance criterion the old archive never had — it accumulated 10+ restore points and **none was
   ever restored**, which is why six weeks of damage went undetected.

   ```bash
   mountpoint -q /media/pcalnon/temp_backups || { echo "NOT MOUNTED - STOP"; exit 1; }
   python3 util/ad-hoc/duplicati_drill_select.py \
       --db /home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite \
       --dest /media/pcalnon/temp_backups/Ubuntu \
       --count 5 --out /tmp/drill_new.json
   python3 util/ad-hoc/duplicati_drill_run.py \
       --candidates /tmp/drill_new.json \
       --dbpath /home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite \
       --dest file:///media/pcalnon/temp_backups/Ubuntu \
       --passphrase-file .env --passphrase-key PASSPHRASE \
       --out-dir /media/pcalnon/temp_backups/_drill_new
   ```

   The selector expects a *damaged* and an *intact* fileset; with a single healthy version it will
   report UNDER-DELIVERED for the damaged group. **That is the correct answer for a healthy set** —
   read it as "nothing damaged to sample", not as a failure. Judge the good group on
   `RESTORED_OK` with SHA-256 match.
2. **Re-run the old archive's intact-arm drill with `--time`.** See §4 — currently unproven.
3. **Decide the purge on a different basis — Duplicati's own analysis does not finish here.**
   Two attempts both died on timeout with no result: `list-broken-files` at 90 min, and
   `purge-broken-files --dry-run` at the full 8 h cap (`rc: 124`, log ends at "Listing remote
   folder"). Meanwhile `util/ad-hoc/duplicati_offline_broken_files.py` computed the equivalent
   census in ~10 minutes. Either re-run the dry run with a much larger cap on an idle machine
   (it contends with the Recreate for disk `sdc`), or accept the offline census as the basis and
   treat the dry run as confirmation-if-obtainable rather than a gate. **A timeout is not a
   result** — do not read `rc: 124` as "nothing to purge". Wrapper:
   `util/ad-hoc/duplicati_purge_dryrun.bash <dbpath> <dest-url> <timeout-seconds>` (guarded;
   structurally cannot perform a real purge).
   ⚠ **Verify the mount before this and every other destination operation** (§5a).
4. **`loginctl enable-linger pcalnon`** + a `systemd --user` unit. `Linger=no` +
   `app-gnome-duplicati-*.scope` is the mechanical cause of the 42-day silent outage.
5. **Alerting.** `additional-report-url` is empty. A backup that silently stops is indistinguishable
   from one that works. Highest-value structural fix after linger.
6. **Migrate back to `/mnt/Backups/Ubuntu`** (sda1, SATA) — the *specified* home for this tier.
   `temp_backups` is `sdc4`, the **same physical disk as `/home` (sdc3)**; accepted as temporary.
   This is the **highest-stakes remaining item** — a mishandled destination operation is what caused
   this entire arc — and it has no procedure yet. Sketch, to be designed properly first:
   verify both mounts; free space on sda1 (needs the purge decision in item 3 first); either move the
   volumes and repoint `TargetURL`, or start a second fresh set on sda1 and retire this one once its
   own restore drill passes. **Do not improvise this against a live archive.**
7. Remove the root `duplicati.service` on :8200 (privileged, `yamaguchi` job never completed).
8. Delete `/media/pcalnon/temp_backups/_drill_scratch/` (~35 GB) once the purge work is done.

---

## 4. The one claim that is NOT proven

**"2025-11-12 restores" is not demonstrated.** The drill's intact arm computed `--version` by indexing
the **10 surviving** filesets, but the archived DB holds all **21** and the DB resolves `--version`.
Measured: surviving-index 5 = 2025-11-12 (id 341), all-rows index 5 = **2026-07-06 (id 580)**, a
*damaged* fileset. And all four sampled files share **identical BlocksetIDs** between the two, so
byte-identical output was guaranteed either way — the 4/5 SHA-256 matches prove those blocksets are
recoverable, not that the indexing was right.

Both scripts now select by **`--time=<timestamp>`**. Re-running the intact arm settles it.
The claim currently rests on the offline census + volume-integrity scan: strong, but not a restore.

---

## 5. Credentials — the sharpest trap in this arc

`.env` holds **exactly two** `KEY=VALUE` entries, both **32 chars**. Neither length nor position
distinguishes them.

| key | opens | verified how |
|---|---|---|
| `PASSPHRASE` | the **new** set (`Ubuntu-fresh`) | matches the running backup's logged `sha256[:16]` |
| `PASSPHRASE_OLD` | the **old** archive at `/mnt/Backups/Ubuntu` | decrypts a real volume to a valid ZIP stream |

**The web-UI password is NOT in `.env`.** It was there earlier and was replaced when the keys were
corrected. Consequence: **`python3 util/ad-hoc/duplicati_api.py GET ...` currently returns HTTP 401**,
because its candidate list falls through to `PASSPHRASE_OLD`, which is now an archive passphrase.
To use the API, add a `DUPLICATI_UI_PASSWORD=` entry to `.env` or set `DUPLICATI_PW_KEY` to whichever
key holds it. Everything else in this handoff works without the API.

**Always pass the key name explicitly.** A wrong pick fails in one of two silent ways — it encrypts a
backup under a secret nobody recorded as belonging to it, or it reports a healthy archive as
undecryptable. Both happened today. Confirm which secret ran via the `sha256[:16]` prefix the runners
log; a character count cannot tell two 32-char secrets apart.

⚠ **Rotating the archive passphrase would NOT re-encrypt existing volumes.** Every volume stays
encrypted under the passphrase that wrote it, so `PASSPHRASE_OLD` must be retained for as long as the
old archive's five intact restore points matter.

---

## 5a. Standing prohibitions — carried forward, still binding

- **NEVER run `Repair`** on the old job. With a database that disagrees with the archive it can
  re-upload volumes reconstructed *from the database* and delete remote volumes it does not
  recognise. It is the UI's default suggestion, which is what makes it the likeliest mistake.
- **NEVER `kill -9` Duplicati.** The Recreate's WAL was measured at **8.26 GB**; shutdown
  checkpointing takes many minutes. Use TERM, then wait — a shrinking `-wal` beside a growing
  `.sqlite` means it is working.
- **Verify the mount before ANY destination operation.** `/mnt/Backups` is *not* a mountpoint;
  `/mnt/Backups/Ubuntu` is. Unmounted, the path resolves to an empty dir on `/` and any destination
  operation is catastrophic.
- **`pgrep -x duplicati` is safe** — it matches only the user instance. Bare `pgrep duplicati`
  also matches the **root** daemon (`comm=duplicati-serve`, `Restart=always`). Never signal that pid.
- An **unmounted destination reads as "everything is missing"**, not as an error. The tooling now
  refuses below a floor, but any new check must too.

## 6. Verify your starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/curious-plotting-hummingbird
git log --oneline -3 && git status -sb

mountpoint -q /mnt/Backups/Ubuntu         || echo "OLD ARCHIVE NOT MOUNTED - STOP"
mountpoint -q /media/pcalnon/temp_backups || echo "NEW DEST NOT MOUNTED - STOP"

ps -eo args | grep '[d]uplicati-cli backup'          # fresh backup still running?
du -sh /media/pcalnon/temp_backups/Ubuntu            # progress; ~155 GiB when complete

# old archive still openable with the OLD key (expect: valid ZIP stream)
bash util/ad-hoc/duplicati_verify_passphrase.bash /mnt/Backups/Ubuntu .env PASSPHRASE_OLD
```

**Git**: branch `fix/duplicati-findings-corrections`, **1 commit ahead** of `origin/main`
(`c212b34`, the fresh-set tooling). Working tree carries **one untracked file — this handoff** —
which should be committed with it.

⚠ **The branch's upstream is stale**: it tracks `origin/fix/agents-sequence-safety-required`, which
was **deleted after #1269 merged** (`git status -sb` shows `[gone]`). A bare `git push` will not do
what you want. Push explicitly:
`git push -u origin HEAD:fix/<new-branch-name>`. This session has merge approval for the arc.

⚠ `duplicati_api.py` returns **401** until a UI-password key is added to `.env` — see §5.

## 7. Standing operating procedure

**All generated content — notes, code, configs — must be validated by multiple INDEPENDENT custom
agents, including adversarial review, targeting hallucinations and untested assumptions.** Launch
them concurrently in one message, give each a **different lens** (re-probe every asserted fact /
attack the conclusion while granting premises / hunt silent-wrong-answer bugs), and prompt for
**refutation**, not confirmation. Treat agent output as evidence, not verdict: two agents disagreed
on the `--version` question in §4 and the measurement decided it.

That process earned its place here. It found, in my own work: a tool that returned **exit 0 "all
clear" on an unmounted destination**; a purge wrapper whose database guard was bypassable four ways;
a timed-out restore scored as "as predicted"; and a `--blocksize` recommendation *below* the vendor
default.

**The recurring failure shape, stated plainly: a correct mechanism paired with a wrong consequence.**
It occurred **nine** times across this arc — every premise individually true, every conclusion wrong.
Prefer running the thing over reasoning about it: guessing Duplicati's passphrase hash produced four
wrong answers, and one `gpg --decrypt` settled it in seconds.
