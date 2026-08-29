# HANDOFF 2026-08-27 — juniper-backup.bash per-repo rewrite: review + the arc's remaining tail

> **Continue the backup / snapshot-lifecycle arc.** `util/juniper-backup.bash` was rewritten to
> produce one encrypted tarball **per application repo** with per-repo exclude lists, and shipped as
> **ml#1427 (MERGED `99df9bf0`, 2026-08-28)** — which is now `origin/main`. The owner reported two
> symptoms: the backup is very slow, and archives are enormously larger than their sources
> (`juniper-data` ~33 MB excluding `data/` → **>75 GB** on the drive).
>
> **Both symptoms have one root cause, and it SURVIVED the merge.** §N = a section of THIS document.
> Predecessor:
> `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-26_cascor-stop-fix-verified-and-attribution-tail.md`.

**FIRST ACTION: fix B1 (§2.1) on a NEW branch off `main`. ml#1427 is already merged — there is no PR
to repair.** The exclude handling was restructured before merge (the string-splitting defect this
review originally found is gone) but the replacement **still does not exclude anything**, by a
different mechanism. Verified against `origin/main` on 2026-08-28.

### Status of every finding against merged `main` (`99df9bf0`, 479 lines)

| # | finding | status on main |
|---|---|---|
| **B1** | excludes never reach tar | **STILL BROKEN — new mechanism** (§2.1). Proven: 3,000,918 B vs 177 B, `data/` present. |
| **B2** | `.tgz` name, bzip2 content | **STILL PRESENT** — `TAR_EXT="tgz"` `:111`, `tar -cjf` `:423`. Restore path broken. |
| **B3** | per-repo failures forgotten | **STILL PRESENT** — `SUCCEEDED=1`/`FAILED_LABELS=()` at `:431-432`, inside the loop opened at `:407`. |
| **B4** | bzip2 3.8× slower, no smaller | **STILL PRESENT** |
| **B5** | `INCLUDE_CASCOR_SNAPSHOTS` inverted | **STILL INVERTED**, and now set `FALSE` (`:75`) → snapshots **are included**. |
| **B6** | unanchored excludes hit nested dirs | **LATENT** — cannot bite until B1 is fixed, then it will. |
| §2.8 | `project_stats.bash` shellcheck | **FIXED** — 0 findings; this is what unblocked the merge. |
| §2.8 | `project_stats.bash` inert `du --exclude` | **STILL PRESENT** — `:122`. |

`util/juniper-backup.bash` is now shellcheck-clean, so **lint will not find any of B1–B6.** They are
all semantic.

Dup-guard first: `gh pr list --repo pcalnon/juniper-ml --state open`, and check sibling worktrees —
two sessions off one handoff have duplicated PRs before.

---

## 1. State at handoff

- juniper-ml `origin/main`: **`99df9bf0`** (ml#1427). The preceding arc landed at `421e34b5` with all
  three post-merge workflows green, verified directly rather than via a watcher (§5 trap 1):
  **#1411** (snapshot_counter census), **#1413** (restore drill, pipeline half), **#1422** (backup
  multi-device repair), **#1424** (attribution displacement guard) — all 2026-08-26.
- **The per-repo rewrite MERGED as ml#1427** (`99df9bf0`, 2026-08-28; 479
  lines, vs the 390-line #1422 version it replaced). It is now `origin/main`. The uncommitted copy
  in the primary checkout is the PRE-merge 527-line draft and is now STALE — discard it rather than
  working from it (`git checkout -- util/juniper-backup.bash` in the primary checkout).
- Owner is handling the class-2 restore drill (YubiKey decrypt). **§4 changes what that costs.**
- 25 open CodeQL alerts repo-wide, none in any file touched by the 08-26 arc.

---

## 2. REVIEW — `util/juniper-backup.bash` as merged on `main`

**All line anchors are against the merged 479-line file at `99df9bf0`** — re-based after the merge,
so they are directly usable. Severity order, not file order. Re-verify before quoting: `main` moves
several times an hour.

### 2.1 ⚠ B1 — CRITICAL, live on `main`, and the single root cause of BOTH reported symptoms

**The defect changed shape during the merge but was not fixed.** It is now a *quoting-inside-a-string*
bug rather than a *word-splitting* one, with the same effect: **tar excludes nothing, and does not
error.**

**There are TWO independent causes. Fixing either one alone leaves the excludes broken** — this is
the single most important thing in this document.

**Cause 1 — literal quotes and a trailing space.** `build_exclude_dirs_arg()` (`:193-200`):

```bash
exclude_dirs_arg+=("$(printf -- '--exclude="%s" ' "${exclude_dir}")")
```

Shell quoting has already happened by the time `printf` runs, so those `"` are *data*. The element
is literally `--exclude="data" `, and tar reads the pattern as `"data" ` — quote, d, a, t, a, quote,
space — matching nothing.

**Cause 2 — absolute paths.** `validate_exclude_dirs()` (`:174-188`) stores
`realpath`-canonicalised **absolute** paths:

```bash
current_exclude_path="$(realpath "${current_exclude_dir}")"
exclude_dirs_array+=("${current_exclude_path}")
```

Confirmed live: it returns e.g. `/home/pcalnon/…/juniper-data/data`. But tar matches `--exclude`
against **archive member names**, which under `-C "${SOURCE_PARENT}"` with leaf `juniper-data` are
*relative* (`juniper-data/data/…`). An absolute pattern can never match one.

Both measured (`/tmp/…/scratchpad/{merged_exclude_test,abs_exclude_test}.sh`, re-author under
`util/ad-hoc/`):

| form | archive | `data/` entries |
|---|---|---|
| merged: `--exclude="data" ` (cause 1) | **3,000,918 B** | **2 — not excluded** |
| absolute: `--exclude=/abs/path/data` (cause 2) | **2,000,631 B** | **2 — not excluded** |
| `--exclude=repo/data` (relative) | **171 B** | 0 |
| `--exclude=data` (basename) | **171 B** | 0 |

**Minor, latent — not the bug.** `realpath` without `-m` fails if an *intermediate* component is
missing, and under `set -euo pipefail` that assignment would abort the script. It does not bite
today: only the final component (`.amp`, `.trunk`, …) is ever absent, which plain `realpath`
tolerates, and `[[ -d ]]` then filters it. Verified against `juniper-data`: 9 of 16 resolved, exit 0.
Worth `-m` or a guard if the repo list ever contains a path whose parent may not exist.

**~17,000× inflation, silently.** Against the real tree: `juniper-data` is **97 GB**, of which
`data/` is **96 GB**. `du` reports ~33 MB because the *size* path resolves its excludes separately;
tar archives all 97 GB → bzip2 → the **>75 GB** on the drive. Symptom 2 fully explained; symptom 1
largely so (archiving 97 GB, not ~1 GB) with B4 compounding it.

**Fix — both causes at once.** Keep `validate_exclude_dirs`'s *existence* check but store the name
relative to the archive root, not an absolute path, and build the flag without `printf`:

```bash
# validate_exclude_dirs: keep the -d test, store what tar will actually see
[[ -d "${application_dir}/${exclude_dir}" ]] && exclude_dirs_array+=( "${exclude_dir}" )

# build_exclude_dirs_arg: no printf, no embedded quotes, no trailing space
for exclude_dir in "${EXCLUDE_DIRS_VALIDATED[@]}"; do
    exclude_dirs_arg+=( "--exclude=${SOURCE_LEAF}/${exclude_dir}" )   # anchored: also fixes B6
done
```

Anchoring on `${SOURCE_LEAF}/` (e.g. `juniper-data/data`) matches the member names tar actually
writes and, unlike a bare basename, does **not** also delete `src/**/data/` — so it closes B6 in the
same change. Verified above: `--exclude=repo/data` gives 171 B and 0 `data/` entries.

**Why this keeps recurring — read before touching it.** This is the *second* independent way this
one line has silently disabled every exclude, and both times the code looked plausible and lint was
happy. The pre-merge version used `printf … | tr '\n' ' '` and quoted command substitution; the
merged version uses `printf` with embedded quotes. **The failure mode is invisible in the source and
invisible to shellcheck — the file is now shellcheck-clean.** So do not accept a fix on inspection:

```bash
# The only acceptable proof. Must print a small number and 0 entries.
bash util/juniper-backup.bash --dry-run --source <a repo with an excluded dir> 2>&1 | grep 'tar args:'
printf '%s\n' "${EXCLUDE_DIRS_ARG[@]}" | cat -A     # each line exactly --exclude=NAME$, no quotes, no trailing space
```

Better: add a regression test that runs `build_exclude_dirs_arg` and asserts each element matches
`^--exclude=[^"'\'' ]+$`. Nothing else in the repo will catch the third variant.

### 2.2 ⚠ B2 — CRITICAL: the `.tgz` name is a lie, and it breaks restore

`TAR_EXT="tgz"` (`:111`) but the build is `tar -cjf -` (`:423`) — **bzip2**. Measured:

```
file(1):                bzip2 compressed data, block size = 900k
tar -xzf mislabelled.tgz -> FAILS      <-- the documented restore path
tar -xjf mislabelled.tgz -> OK
```

Every archive this version writes is undecompressable by the documented recipe
(`gpg -d | tar -xzf -`) used in the lifecycle design §6.4.2 and in the merged drill. For a backup
script this is the most serious class: the artifact exists and does not restore. Fix by choosing
one — `-czf` + `.tgz` (recommended, see B4) or `-cjf` + `.tbz2`.

### 2.3 ⚠ B3 — HIGH: per-repo failures are silently forgotten; report can say COMPLETE while a repo failed

`SUCCEEDED=1`, `FAILED_LABELS=()` and `APPLICATION_REPOS_ARGS=()` are **inside** the per-repo loop
(`:431-432`, loop opens `:407`). They reset every iteration, so the final report (`:469`, `:477`) shows
only the **last** repo's device count and `${GPG_FILE}` names only the **last** archive. If repo 3 of
10 fails to copy to device 2, that failure is erased by repo 4 and the script prints
`COMPLETE: every configured device holds a verified archive.`

This is the third occurrence of the script's recurring class (report success, produce nothing) — see
its own header notes on `${ENCRPYTED}` and the stale-`GPG_PATH` loop. **Fix:** accumulate across
repos (`TOTAL_EXPECTED`, `TOTAL_WRITTEN`, `FAILED_LABELS` declared before the loop) and report a
per-repo table.

### 2.4 B4 — HIGH: bzip2 is strictly worse here (second slowness cause, independent of B1)

Measured on 120 MB of mixed compressible/incompressible content:

```
gzip  (-czf):   2.3 s   60,068,372 B
bzip2 (-cjf):   8.9 s   60,265,155 B
-> 3.8x slower for 100.3% the size
```

On this corpus (mostly `.h5`/`.npz`/binary) bzip2 buys nothing and costs ~4×. Use `-czf`. If ratio
matters more than time, `zstd --long -T0` beats both, but that is a bigger change.

### 2.5 B5 — MEDIUM: `INCLUDE_CASCOR_SNAPSHOTS` does the opposite of its name

`TRUE="0"` / `FALSE="1"` (`:62-63`), and `:75`/`:81-82`:

```bash
INCLUDE_CASCOR_SNAPSHOTS="${TRUE}"
if [[ "${INCLUDE_CASCOR_SNAPSHOTS:-${FALSE}}" == "${TRUE}" ]]; then
    EXCLUDE_DIRS=( "${EXCLUDE_DIRS[@]}" "cascor-snapshots" )
fi
```

Setting **INCLUDE** to TRUE **ADDS `cascor-snapshots` to the exclude list**. As written, snapshots are
currently being dropped. Rename to `EXCLUDE_CASCOR_SNAPSHOTS`, or invert the test. Decide
deliberately: `cascor-snapshots` is ~1.7 GB / 28k files and is the corpus the whole snapshot arc
depends on.

### 2.6 B6 — MEDIUM: unanchored excludes silently drop nested directories

The guard tests only the top level (`[[ -d "${application_dir}/${EXCLUDE_DIR}" ]]`, `:187`) but emits
an **unanchored** `--exclude=<name>` (`:190`), which tar matches at **any depth**. With
`EXCLUDE_DIRS` containing `data`, `build`, `dist`, `logs`, `resources`, any `src/**/data/` or
`src/**/build/` in any repo is dropped from the backup. Silent, and it is *source* loss, not cache
loss. Fix: `--exclude=./<name>` (with `-C` semantics) or add `--anchored`.

### 2.7 Lower severity

- **B7** `APPLICATION_REPOS_ARGS=()` at `:472` inside the loop — harmless today only because bash
  expands the `for` list once; a latent trap if that block is ever moved.
- **B8** `juniper-legacy` exists on disk but is absent from `APPLICATION_REPOS` (`:87`). Intentional?
  If not, it is an unbacked-up tree.
- **B9** Top-level `echo`s at `:88` and `:121` run before argument parsing, so they pollute `--help`
  and `--dry-run`.
- **B10** `--exclude-caches-all` and `--exclude-caches-under` together (`:120`) are redundant.
- **B11** With an empty exclude list, `validate_exclude_dirs` emits a lone space → a one-element
  array containing `" "` → tar receives an empty-ish argument. Guard the empty case.
- **B12** Header docs still describe the single-archive design ("replicate it to every attached
  external drive", exit-code table, `--dest`), not per-repo archives. Update, or the next reader
  inherits a false model.

### 2.8 ⚠ `util/project_stats.bash` — shipped in #1427; lint fixed, semantics not

Not part of the backup path, but it landed on `main` in the same PR. Its shellcheck failures (SC2010,
SC2044, eight × SC2046) — which were what blocked the merge — **were fixed**; the file is now clean.

**Its silent-no-op survived, exactly like B1.** `:122` on `main`:

```bash
REPO_SIZE="$(du -s --exclude="juniper-data/data/*" "${REPO_PATH}" | awk …)"
```

The quoting was tidied; the *pattern* was not.

`du --exclude` matches a **glob against each entry's name**, not a path prefix, so a pattern
containing `/` matches nothing. Measured on a synthetic tree:

| form | reported |
|---|---|
| no exclude | 2936 KB |
| `--exclude="juniper-data/data/*"` (as written) | **2936 KB — inert** |
| `--exclude="data"` | 4 KB |

So `project_stats.bash` reports `juniper-data` at its full ~97 GB while appearing to exclude the data
tree — a stats tool that silently overstates the largest repo by ~100×. Fix with a basename pattern
(`--exclude=data`), or `--exclude=./data` if only the top-level one is meant.

**This is the pattern worth carrying out of this arc.** Across #1427, lint was satisfied on every
file and **not one of the three exclusion mechanisms actually excludes anything**: the backup
script's `--exclude="data" `, this script's `juniper-data/data/*`, and (latent) the unanchored
matching of B6. A clean shellcheck run says the shell is well-formed, never that a flag does what
its name suggests. **Every exclusion in this PR needs an empirical before/after size check, not a
reading.**

### 2.9 Keep — these are right

`gpg --compress-algo=none -z 0` (`:423`) correctly avoids double-compression. `verify_archive`'s
recipient-count check, the mount-root check, the build-once-then-copy structure, per-repo
`IN_PROGRESS` cleanup that preserves already-verified archives, and the shared `UUID_VALUE` /
`DATE_STAMP` grouping one backup set across repos — all from #1422, all still correct.

---

## 3. Suggested order

ml#1427 is **merged**; this is a fresh branch off `main`. One PR carrying B1–B6 is fine — they are
one subsystem — but B1 alone is worth shipping first if you want the symptoms gone today.

1. **B1** (§2.1) — the only fix that addresses both reported symptoms. **Prove it empirically**
   (§2.1 gives the commands); do not accept it on inspection, because this line has now silently
   failed twice while looking correct and passing lint.
2. **B2 + B4** (§2.2, §2.4) — one decision: `-czf` with `.tgz`. Repairs the broken restore path and
   the 3.8× slowdown together.
3. **B3** (§2.3) — cross-repo accounting, or a partial backup keeps printing COMPLETE.
4. **§2.8** — `project_stats.bash:122`'s inert `du --exclude` (its lint is already fixed).
5. **B5, B6** (§2.5, §2.6) — both silently change *what ends up in the backup*. Decide deliberately;
   B5 currently **includes** ~1.7 GB of `cascor-snapshots` while reading `FALSE`.
6. Re-run the drill (§4) once B2/B4 are settled, then correct the lifecycle design §6.4.2.

**Add a regression test.** `tests/` has no coverage of this script, and every defect here is
semantic and lint-invisible. A test that calls `build_exclude_dirs_arg` and asserts each element
matches `^--exclude=[^"'\'' ]+$` would have caught both B1 variants; wire it into `ci.yml`'s
hand-maintained module list ([[reference_juniper_ml_ci_test_list_is_hand_maintained]]) or it will
not run.

**Merging.** Land via `util/open_signed_pr.py` (`required_signatures` is live), then
`python util/safe_merge.py --pr <N> --execute --merge-method squash`. **Never `--admin`** — this is
executable code, and admin-bypass is the class that reddened main in ml#932/#924. Expect BEHIND
races; see §5 trap 2.

---

## 4. ⚠ The merged restore drill no longer matches the script

`util/ad-hoc/2026-08-26_backup_restore_drill.bash` (merged in #1413) proved the pipeline
byte-for-byte — but it hardcodes `tar -czf - | gpg -e`. The script now does
`tar -cjf - | gpg --compress-algo=none -z 0 -e`. **The drill no longer tests the real pipeline**, and
its "PIPELINE VERIFIED" claim in the lifecycle design §6.4.2 is stale.

After fixing B2/B4, update the drill to mirror the final flags and re-run it, then correct
`notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md` §6.4.2.

**This also gates the owner's class-2 drill:** decrypting a current archive with
`gpg -d | tar -xzf -` fails (B2). Give the owner the corrected one-liner, or fix B2 first.

---

## 5. Traps

1. **A green watcher is not a green build.** A watcher selecting `.conclusion // .status` reports
   success while runs are in progress: `gh` returns `conclusion` as `""` during a run, and jq's `//`
   falls back only on `null`/`false`. Both guards missed and control fell through to GREEN. **Key
   running-ness off `.status`; when two guards can both miss, the fall-through must be failure.**
2. **Native auto-merge does NOT update a BEHIND branch.** #1424 sat green + armed + `BEHIND` across
   three polls. `safe_merge` refuses after 3 BEHIND cycles (exit 1, net disarmed). Remedy:
   `gh api repos/pcalnon/juniper-ml/pulls/<N>/update-branch -X PUT`, never a force-push. See
   `[[reference_safe_merge_exits_zero_without_merging]]`.
3. **Sandbox refusals in a worktree-isolated session:** heredocs, `for` loops, `${PIPESTATUS}`, and
   `git -C <sibling>` are refused; `$(…)`, `&&`/`;` chains and `sed`/`grep` on sibling paths work.
   Put multi-step logic in a `util/ad-hoc` script and run `bash <file>`.
4. **`pre-commit` skips `util/ad-hoc/` for Black/flake8/mypy/bandit — but CodeQL scans it.** Run
   `flake8` + `pyflakes` by hand on anything added there.
5. Do not re-open the settled items in the predecessor's §3.3 (`/dev/shm` sweeper, persist-history,
   moon/spiral/xor/gaussian verdicts).

---

## 6. Verification commands

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper

git -C "$JUNIPER/juniper-ml" rev-parse --short origin/main      # 99df9bf0 or later
gh pr view 1427 --repo pcalnon/juniper-ml --json state,mergedAt # MERGED 2026-08-28
git -C "$JUNIPER/juniper-ml" show origin/main:util/juniper-backup.bash | wc -l   # 479 = the merged version

# B1 — the live defect. This is the line:
git -C "$JUNIPER/juniper-ml" show origin/main:util/juniper-backup.bash | sed -n '193,200p'
#   exclude_dirs_arg+=("$(printf -- '--exclude="%s" ' "${exclude_dir}")")   <- literal quotes + trailing space

# Lint will NOT find it — confirm that for yourself before trusting a green run:
shellcheck --severity=warning "$JUNIPER/juniper-ml/util/juniper-backup.bash"   # 0 findings
shellcheck --severity=warning "$JUNIPER/juniper-ml/util/project_stats.bash"    # 0 findings

# SS2.8: the stats script's exclude is inert
du -s --exclude="juniper-data/data/*" "$JUNIPER/juniper-data" | cut -f1   # ~97 GB — pattern does nothing
du -s --exclude="data"                "$JUNIPER/juniper-data" | cut -f1   # ~1 GB  — basename works

# Sizes that make the 75 GB obvious
du -sh "$JUNIPER/juniper-data" "$JUNIPER/juniper-data/data"     # 97G / 96G

# B2
grep -n 'TAR_EXT=\|tar -cjf\|tar -czf' "$JUNIPER/juniper-ml/util/juniper-backup.bash"

# Drives (both were mounted 2026-08-26)
findmnt -rno TARGET,SOURCE | grep media
df -Ph /media/pcalnon/EBC5-F0A3 /media/pcalnon/DFF3-2782        # 135G / 67G avail
```

Re-probe every count before quoting it: the archive grew 27,908 → 28,040 in days, and `main` moves
several times an hour.

---

## 7. Also still owed (owner)

- **Class-2 restore drill** — YubiKey-decrypt one real archive. Cheap now (`--source <small dir>`
  gives a real archive in seconds) **but blocked by B2** until the format/extension mismatch is fixed.
- **Capacity** — full tree is 141.2 GB; `EBC5-F0A3` ~135 GiB free, `DFF3-2782` ~67 GiB. Fixing B1
  removes ~96 GB (juniper-data/data) and makes per-repo archives comfortably fit.
- **A pre-existing UNENCRYPTED 111 GB `juniper-8.0.0_python_2026-02-27.tgz`** sits on `EBC5-F0A3` —
  a plaintext copy of the whole project on removable media, and most of that drive's used space.
  Owner decision: it is both the exposure this script's asymmetric encryption exists to prevent and
  the capacity problem.
