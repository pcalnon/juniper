# HANDOFF 2026-08-21 — backup & restore systematization (greenfield design arc)

**This is a NEW arc.** No branch, no PR, no partial work. It was split out of the snapshot
storage-convention arc (juniper-cascor#548, juniper-deploy#189, juniper-ml#1211 — all merged) because
that arc's central constraint turned out to rest on a backup process nobody had written down.

**The deliverable is a DESIGN**, per the owner's standing direction for this class of work: *"a
planned, systems based solution … designed, validated, and documented iaw standard juniper operating
procedures"* — never an ad-hoc sweep or a one-off script.

> ## 🔴 READ FIRST — there is a live outage, and it is not a design problem
>
> **Duplicati's last successful backup finished 2026-07-09. It has been dead for 42 days.**
>
> | | |
> |---|---|
> | `Metadata.LastBackupDate` | **`20260709T142349Z`** (finished `155302Z`, ran 1h29m) |
> | `Metadata.LastErrorDate` | `20260713T123608Z` |
> | `LastErrorMessage` | *"remote volume `duplicati-bb634e17…dblock.zip.gpg` is in uploading state, partially uploaded, and **strict mode is on**"* |
> | Quota | **16.3 GB free of 3.94 TB — 0.41 %** |
> | Schedule | daily; last ran **2026-07-13 07:03**, next due 07-14 — **never ran** |
>
> The failure chain is recorded on the host: quota exhaustion (2026-07-12) → a wedged
> partially-uploaded volume → a server-startup crash (`ReWriteAllFieldsIfEncryptionChanged`, the
> 2026-07-12 crashlog). The strict-mode error is **sticky** — it re-fails every run until the partial
> volume is manually repaired. **This needs an operator, not a designer, and it should not wait for
> the design.**
>
> Everything created since 2026-07-09 — including every snapshot written during the storage-convention
> arc — has never been in a Duplicati backup.

---

## 0. How to run this arc

- **Target repo**: `juniper-ml` (the design lands in its `notes/`).
- **Worktree**: mandatory per both `CLAUDE.md` files — centralized under
  `/home/pcalnon/Development/python/Juniper/worktrees/` with the standard naming.
- **Branch**: suggest `docs/backup-systematization-design`.
- **Landing**: **via PR.** Direct pushes to `main` are blocked fleet-wide (`required_signatures`);
  use `juniper-ml/util/open_signed_pr.py` if you cannot sign locally.
- **Document name**: `notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-ECOSYSTEM_<DESCRIPTION-PHRASE>.md` per the
  naming convention.

---

## 1. Why this arc exists

The snapshot storage convention put ~27,900 model snapshots **inside the repo checkout** rather than
under `~/.local/state`, on owner constraints **C-1** (snapshots are project assets captured by the
whole-tree offline backup) and **C-3** (one root shared across stack origins). The design states it
plainly: *"C-1 and C-3 together are what make the in-checkout location correct rather than merely
acceptable."*

C-1 was recorded as **unverified** because no whole-tree backup script or manifest existed in the
tree. This arc closes that — and the verification found the constraint is not currently met.

---

## 2. What actually exists — verified 2026-08-21

Two mechanisms, **neither of which covers the system**.

| leg | scope | destination | state |
|---|---|---|---|
| `tar -czf` (owner-described) | `Juniper/` tree only | temporarily-attached external drive | **no artifact ever found** — see O-0 |
| Duplicati job `SJTCQIIZSJ` ("Ubuntu") | `%HOME%` | `/mnt/Backups/Ubuntu` on `/dev/sda1` | **dead 42 days** (banner) |

### 2.1 The structural finding — C-2 is violated by construction

**`tar` covers `Juniper/` only. Duplicati covers `$HOME` only.** Therefore:

- **Nothing covers `/var/lib/docker`** — 16 juniper Docker volumes exist, including
  `…_juniper-cascor-snapshots`, which holds **container-written snapshots**. C-1 material, zero copies.
- **Nothing covers `/opt/miniforge3/envs`** — **47 GB**, 11 environments.
- **The `tar` leg misses every credential the system needs to boot** — SSH keys, GPG, `gh` auth, the
  SOPS age key all live under `$HOME` outside `Juniper/`.

So **C-2 ("copy + extract → full functionality") cannot hold today** even if both legs were healthy.
That is the arc's real headline, and it is independent of the outage.

### 2.2 Even when healthy, Duplicati drops most of the tree

- **`--skip-files-larger-than = 50MB`** — measured: **69 files, 117.16 GB** of `Juniper/` silently
  skipped (juniper-data 102.52, juniper-legacy 10.62, juniper-cascor 2.82, juniper-canopy 0.72,
  juniper-ml 0.48). Roughly **93 % of the tree by volume**.
- **37 exclude filters**, four inside the tree: `Juniper/logs/`, `Juniper/resources/` (live, 45 MB),
  `Juniper/data/` and `Juniper/jupyter/backups/.ipynb_checkpoints/` (both stale paths, masked by
  `--allow-missing-source=true`).
- **The job skips its own recovery databases.** `~/.config/Duplicati/` is **42 GB**; all four job DBs
  (17.3 / 13.2 / 11.5 / 2.3 GB) exceed the 50 MB cap. Only the 192 KB server DB is captured.
- **Snapshots themselves would survive both screens** (largest snapshot file ≈ 2.3 MB). The mechanism
  is sound; the state is broken.

### 2.3 Two key single-points-of-failure, not one

- **GPG passphrase** — the archive is `encryption-module=gpg`; the passphrase and `TargetURL` exist
  only as `enc-v1:`-wrapped blobs in a 192 KB DB beside `machineid.txt`. Losing it costs the entire
  archive. A legacy note says passphrases are "in LP".
- **SOPS age key** — `~/.config/sops/age/keys.txt` (189 B, `0600`), outside the `tar` scope.
  **An escrow script already exists**: `juniper-deploy/util/sops-backup-key.sh`. Whether it has ever
  been run is unknown (O-2).

### 2.4 ⛔ RETRACTED — a claim an earlier draft of this handoff made

> ~~"Plain `tar` does not consult `.gitignore`, and Duplicati covers `/home/pcalnon/`, so the snapshot
> archive **is** captured today and C-1 is satisfied in substance. The real gap is not coverage."~~

**Wrong, and dangerously so — it instructed the successor not to check the thing that is broken.**
Both halves fail: Duplicati has been dead since 2026-07-09, and GNU tar 1.35 *does* offer
`--exclude-vcs-ignores` / `--exclude-vcs`, so whether the tar leg captures gitignored snapshots
depends on an invocation nobody has read (**O-0**). `/cascor-snapshots/*` **is** gitignored
(`juniper-cascor/.gitignore:74`), so the original alarm is only refuted once that command line is seen.

**Never ship a prohibition on checking.** Verify, then conclude.

### 2.5 Also false in that draft

> ~~"No backup script, config, schedule, or manifest exists anywhere in the Juniper tree."~~

**Three exist:**

1. `juniper-deploy/util/sops-backup-key.sh` — 3,545 B, age-key escrow with a documented restore path.
2. `juniper-legacy/JuniperLegacy/notes/backups_config.bash` — the Duplicati install/config manifest.
3. `juniper-legacy/JuniperLegacy/util/backup_conda_dotfiles.bash` — 7,287 B, a real backup script.
   *(Irony worth designing around: it writes into `Juniper/resources/`, a Duplicati-excluded path.)*

A schedule and config also exist — in `Duplicati-server.sqlite`, not in the tree.

**How that claim survived:** the sweep was run and its output not read — `sops-backup-key.sh` appears
in it 21 times. The other two are invisible because `juniper-legacy` is absent from the sweep
script's `REPOS` array. See §7.

---

## 3. Inventory — what the design must account for

Verified present 2026-08-21. **`tar`** = inside `Juniper/`; **`Dup`** = inside `$HOME` (nominal only —
that leg is dead).

| # | Path | Size | tar | Dup | Why it matters |
|---|---|---|---|---|---|
| 1 | `juniper-legacy/` | **18 GB** | ✅ | ✅ | **No `.git` at all.** 18 GB with zero replication — the largest thing git does not cover. |
| 2 | `~/.local/state/juniper-experiments/` | **26 GB**, 245 runs | ❌ | ✅ | The CLI-experimentation evidence corpus. Not regenerable — seeded runs do not reproduce (cascor#532). ~19.6 GB exceeds the 50 MB cap. |
| 3 | `/var/lib/docker/volumes/` | **16 juniper volumes** | ❌ | ❌ | Includes `…_juniper-cascor-snapshots`. **Outside both legs.** |
| 4 | `/opt/miniforge3/envs/` | **47 GB**, 11 envs | ❌ | ❌ | **Outside both legs.** Regenerable in principle — confirm the recipes are in git. |
| 5 | `~/.config/sops/age/keys.txt` | 189 B | ❌ | ✅ | SPOF #2. Escrow script exists, never confirmed run. |
| 6 | `~/.config/Duplicati/` | **42 GB** | ❌ | ⚠️ | Skips its own job DBs (§2.2). Holds SPOF #1. |
| 7 | `~/.ssh/` | 13 private keys | ❌ | ✅ | Per-repo GitHub deploy keys. Loss = no push access to any repo. |
| 8 | `~/.gnupg/`, `~/.config/gh/`, `~/.kaggle/` | — | ❌ | ✅ | GPG is Duplicati's encryption module; `.kaggle` gates the dataset regeneration that "juniper-data is regenerable" depends on. |
| 9 | `~/.claude/` | **558 MB** | ❌ | ✅ | 163 memory files — the program's institutional memory. Nothing reconstructs it. |
| 10 | `~/.local/state/juniper-ruleset-snapshots/` | 34 JSON | ❌ | ✅ | The only local record of branch-protection config across 9 repos. **GitHub-side state (issues, PRs, releases, Actions secrets) has no local copy at all.** |
| 11 | `Juniper/worktrees/` + `.git/refs/stash` | 791 MB, 15 worktrees; cascor 4 stashes, canopy 4 | ✅ | ✅ | In-flight work. Stashes are never pushed. |
| 12 | `Juniper/backups/`, `util/`, `notes/`, `prompts/`, `resources/` | 83 MB + 45 MB | ✅ | ⚠️ | Parent-level dirs the sweep never searches; `resources/` is Duplicati-excluded. |
| 13 | `juniper-cascor/cascor-snapshots/` | 1.8 GB, ~27,897 | ✅ | ✅ | **Gitignored** — so working tree, tar, and (dead) Duplicati are the *only* three copies. The arc's premise. |

**Tiering is likely the highest-value output of this arc.** Git already replicates all tracked source
to GitHub; the backup's real job is the *untracked* set. Naming that boundary explicitly is worth more
than any tooling choice.

---

## 4. Constraints inherited from the snapshot ruling

From the storage-convention design §2 — all six, quoted rather than summarised, because an earlier
draft dropped two and misattributed a third:

- **C-1** captured by the whole-tree offline backup. **C-2** restore = copy + extract → full
  functionality. **C-3** shared artifacts across stack origins, supporting cross-researcher
  collaboration. **C-4** excluded from the repos. **C-5** protected from deletion. **C-6** never on
  PyPI; transfer strictly out-of-band and user-driven.

C-3 interacts with C-6: a backup that silently syncs artifacts to another host would violate the
out-of-band rule. And **restore preserves contents but not necessarily uid/gid** — a root-extracted
restore leaves a root-owned snapshot root that silently EPERMs every container save (design §7).

---

## 5. Grounding

- `notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-STORAGE-CONVENTION-DESIGN.md` — §2 constraints,
  §6 item 6 (this gap), §7 operator notes. ⚠ Its §9 cites juniper-cascor**#545**, which was **closed**
  and superseded by **#548**; don't chase it.
- `notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-ROOT-LOCATION-DECISION-BRIEF.md`
- `notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md` — age key at
  `~/.config/sops/age/keys.txt`, also a GitHub secret `SOPS_AGE_KEY`.
- `juniper-deploy/util/sops-backup-key.sh`, and the two `juniper-legacy` scripts in §2.5.
- `~/.config/Duplicati/Duplicati-server.sqlite` — schedule, 37 filters, 58 options. **Open read-only**
  (`file:…?mode=ro`); do not touch the 17 GB job DB.

---

## 6. Open questions for the owner

- **O-0 — what is the exact `tar` command line?** No script, alias, cron entry, systemd unit, or
  `.tar*` artifact was found anywhere on `/home` or `/mnt`; the external drive is not attached.
  **Whether the tar leg has ever produced an artifact is unknown**, and it decides whether gitignored
  snapshots are captured. Highest-value question in this document.
- **O-1** — is `juniper-data`'s ~102 GB genuinely regenerable, or is any of it unique?
- **O-2** — has `sops-backup-key.sh` ever been run, and where is its output?
- **O-3** — is the Duplicati GPG passphrase recorded anywhere off this host?
- **O-4** — was the ~1 TB freed from `/mnt/Backups` since 2026-07-12 a deliberate cleanup, or loss?
- **O-5** — is offsite in scope, or is on-site redundancy the accepted posture? Note `/dev/sda1` is an
  **internal, non-removable** disk — it shares a failure domain with `/home`.
- **O-6** — has a restore *ever* been performed from either leg?

---

## 7. Verification

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper

# Duplicati state — READ-ONLY, and do not open the 17 GB job DB
python3 -c "
import sqlite3; c=sqlite3.connect('file:$HOME/.config/Duplicati/Duplicati-server.sqlite?mode=ro',uri=True)
print([r for r in c.execute('SELECT Name,Value FROM Metadata')])
print([r for r in c.execute('SELECT Name,Value FROM Option') if 'larger' in r[0] or 'encryption' in r[0]])"

# What the 50MB cap drops
find "$JUNIPER" -type f -size +50M -printf '%s\n' | awk '{s+=$1} END {printf "%d files, %.2f GB\n", NR, s/1e9}'

# Backup tooling in the tree -- FILENAME-scoped, whole tree.
# Do NOT use the ecosystem_reference_sweep for this: its REPOS array omits juniper-legacy and it
# never searches the parent-level Juniper/{util,notes,backups,prompts} dirs. That blind spot is
# exactly how "no backup script exists" got into an earlier draft.
find "$JUNIPER" -maxdepth 6 \( -iname '*backup*' -o -iname '*restore*' \) \( -name '*.sh' -o -name '*.bash' \) -not -path '*/.git/*'

# Out-of-scope stores
docker volume ls --format '{{.Name}}' | grep -i juniper | wc -l
du -sh /opt/miniforge3/envs ~/.local/state/juniper-experiments ~/.config/Duplicati
```

`du -h` reports **GiB**; figures above are converted to decimal GB where labelled. Counts move — the
snapshot archive grew by one file during validation.

---

## 8. Git state

- **juniper-cascor** `origin/main` **`362b88b`** (#551, D-E integrity gates) — moved twice during the
  authoring of this document.
- **juniper-ml** / **juniper-deploy** current as of 2026-08-21.
- Snapshot-arc PRs, all MERGED: cascor#548, cascor#549, deploy#189, ml#1211, ml#1197.
  cascor#545 and #546 were **closed** and superseded by #548.
- Worktrees created for the snapshot arc were removed 2026-08-21; **36 linked worktrees persist
  overall** across the three repos — they are live uncommitted-work exposure the design must cover.

**Re-probe all of this.** Two predecessor handoffs in this family were wrong about `origin/main` on
their first pass.

---

## 9. Method notes

- **Validate with multiple independent agents before landing** — standing owner policy, and not
  ceremony: this document's first draft asserted the opposite of the truth in its most emphatic
  paragraph, and two validators caught it.
- **A correct mechanism paired with a wrong consequence** is this program's recurring failure shape.
  "`tar` ignores `.gitignore`" and "Duplicati's source is `%HOME%`" are both true; "therefore coverage
  is fine" was false. State what you *ran* separately from what you *reasoned*.
- **Running a sweep is not reading it.** The false claim in §2.5 sat 21 times in the sweep's own output.
- **Linting is not validation.** For a document, the only check that matters is re-probing every
  asserted fact against the real system.
