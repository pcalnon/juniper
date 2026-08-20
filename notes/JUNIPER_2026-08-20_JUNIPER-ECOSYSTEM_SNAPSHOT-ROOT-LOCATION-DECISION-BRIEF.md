# Snapshot root location — decision brief for **S-1**

**Project**: Juniper — snapshot lifecycle management (F-P1-4)
**Sub-Project**: juniper-cascor / juniper-deploy / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-20

**Status**: DECISION BRIEF — awaiting owner ruling. Nothing here is implemented; this document
changes no code, no path, and no default. It exists to make S-1 answerable.

**Question, as posed** in
[`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)
§9:

> **S-1** — Should snapshots move out of the repo checkout entirely (e.g. under
> `~/.local/state/juniper-snapshots/`, mirroring the experiment `RUN_DIR` convention)?

**Why it is being asked now.** The design's §8 sequencing makes Phase 6.1 (identity) the next
unblocked work, and 6.1 specifies **both** a provenance stamp **and** a unified filename. Deciding
the root afterwards means re-opening 6.1. Answering S-1 first costs one ruling; answering it second
costs a rework.

**Evidence base.** Every path, line number, and count below was probed on **2026-08-20** against
juniper-cascor `4bec1be`, juniper-ml `c1589cd`, juniper-deploy `bae0334`, juniper-canopy `955e8d4`.
The reference inventory (§3) was produced with
[`util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash`](../util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash)
run **`--all`, untruncated** — the discipline that §4 item 4 of the closeout handoff was written to
enforce.

---

## 1. Executive summary

Five things were found that were not on the record when S-1 was written. Three of them change the
answer.

| # | Finding | Bearing on S-1 |
|---|---|---|
| **F-1** | **The Docker tier's snapshot volume is mounted one directory away from where either tier writes.** `juniper-cascor-snapshots` mounts at `/app/data`; the service writes `/app/snapshots`, the CLI writes `/app/src/cascor_snapshots`. Container snapshots land in the writable layer and die with the container. | The strongest argument for an **explicitly configured** root. A path that is *derived* from the source-file location cannot be mounted reliably. |
| **F-2** | **47 snapshot `.h5` files are tracked in git** — `src/cascor_snapshots/`, 1,694,936 bytes, all from the 2025-10 cohort. | Moving the *write* default does not remove them. Every clone and every worktree materialises them. A separate ruling is needed. |
| **F-3** | **The CLI-tier default is duplicated into a published PyPI package** (`juniper-cascor-model`) and byte-gated against drift. Installed as a wheel it resolves **inside site-packages**. | Doubles the change surface for any CLI-tier default change, and is a latent (not live) correctness problem in its own right. |
| **F-4** | **The canopy precedent is weaker than assumed.** `juniper-canopy/snapshots/` holds one 3.6 MB `snapshot_history.jsonl` and **zero `.h5`**. | It is a precedent for an *audit log* at the repo root, not for model-artifact storage. The handoff's "matches an existing convention" argument does not hold as stated. |
| **F-5** | **The two tiers resolve their root by different mechanisms** — service at **call** time through a single function with 5 call sites; CLI at **import** time through a 4-hop constant chain ending at 2 write sites. | Option C is cheap and safe on the service side and materially more work on the CLI side. They can be decided, and shipped, separately. |

**Recommendation: Option C, staged — service tier first, CLI tier second, existing archive not
moved.** Rationale in §6. The staging matters more than the destination: F-5 means the service half
is a contained change that also fixes F-1, while the CLI half carries the 27,886-file migration
question and the F-3 drift gate.

---

## 2. Measured current state

### 2.1 Where each tier resolves its root

| tier | resolution site | when | default | naming |
|---|---|---|---|---|
| direct CLI | `src/cascor_constants/constants_hdf5/constants_hdf5.py:46,53-57` | **import** | `<repo>/src/cascor_snapshots` | `cascor_snapshot_<YYYYMMDD>_<HHMMSS>_<uuid4>.h5` |
| service | `src/api/lifecycle/manager.py:4480-4486` (`_get_snapshots_dir`) | **call** | `<repo>/snapshots` | `snapshot_<ISO8601>Z.h5` |

Both honour `JUNIPER_CASCOR_SNAPSHOTS_DIR` (W-6), both treat a blank value as unset. The
import-time/call-time split is the load-bearing difference: the CLI tier's value is frozen before
the first `cascor_constants` import, so a launcher must export the variable *before exec*, while the
service tier picks up a change at any time.

The service tier is **single-rooted**: all five uses go through `_get_snapshots_dir()` —
`manager.py:4518, 4571, 4935, 4950, 4975` — so reads and writes move together atomically. The
lookup itself is a glob over exactly one directory (`manager.py:4571-4572`), with no search path and
no fallback.

The CLI tier reaches its write sites through a four-hop chain:

```text
constants_hdf5.py:57  _HDF5_PROJECT_SNAPSHOTS_DIR
  → constants.py:951  _CASCADE_CORRELATION_NETWORK_HDF5_PROJECT_SNAPSHOTS_DIR
  → cascade_correlation_config.py:207   (default constructor argument)
  → cascade_correlation.py:757          (instance attribute)
  → cascade_correlation.py:4933, 5012   (the two write sites)
```

### 2.2 What is actually on disk

```text
src/cascor_snapshots/          27,886  .h5     1.8 GB     ← the CLI-tier archive
  of which tracked in git          47  .h5     1.6 MiB    ← F-2, all 2025-10
<repo>/snapshots/              does not exist yet         ← created on demand by _get_snapshots_dir
src/snapshots/                      4  .h5                ← untracked, gitignored, pre-move leftovers
  (plus 7 tracked source modules — the importable package #537 protected)
juniper-canopy/snapshots/           0  .h5                ← F-4: one snapshot_history.jsonl, 3.6 MB
```

> **The 4 `.h5` in `src/snapshots/` carry today's mtime but 2026-08-11/13 filenames.** They are
> untracked and gitignored (`.gitignore:75`), and the only service-side resolution site
> (`manager.py:4485`) now points at the repo root, so they are leftovers whose timestamps were
> reset — **§2.2's "`mtime` is not creation time" trap, observed live**. Do not read them as
> evidence that a write path still targets the package directory; the grep for resolution sites
> returns exactly one, and it is the repo-root one.

---

## 3. Full reference inventory

Everything that names a snapshot root. Produced untruncated; **this is the list any move must
satisfy**, and its length is the point — the first attempt at this class of sweep in this arc
returned two constants and was wrong by six.

### 3.1 Resolution and propagation (juniper-cascor)

| # | reference | role |
|---|---|---|
| 1 | `src/cascor_constants/constants_hdf5/constants_hdf5.py:46,53-57` | CLI-tier resolution |
| 2 | `src/api/lifecycle/manager.py:4480-4486` | service-tier resolution |
| 3 | `src/cascor_constants/constants.py:141,279,951` | re-export + `__all__` |
| 4 | `src/cascade_correlation/cascade_correlation_config/cascade_correlation_config.py:57,207` | config default |
| 5 | `src/cascade_correlation/cascade_correlation.py:95,757,4933,5012` | instance attr + 2 write sites |
| 6 | `src/api/lifecycle/manager.py:4518,4571,4935,4950,4975` | the 5 service consumers |

### 3.2 The vendored duplicate — byte-gated (F-3)

| # | reference | role |
|---|---|---|
| 7 | `juniper-cascor-model/cascor_constants/constants_hdf5/constants_hdf5.py:46,53-57` | **byte-identical copy** (whole file, 89 lines both sides), published to PyPI |
| 8 | `juniper-cascor-model/cascor_constants/constants.py:141,279,951` | same re-export chain |
| 9 | `juniper-cascor-model/tests/test_drift.py` | byte-compares `cascor_constants` against `src`; `_NORMALIZED_DIVERGENCE` is **empty** as of the 2026-08-19 re-extraction |

Consequence: **any edit to `constants_hdf5.py` in `src` must be mirrored into the package in the
same commit**, or `CI — juniper-cascor-model` fails. That gate was only made to actually fire in
cascor#536 — it is now load-bearing rather than decorative.

### 3.3 Deployment surfaces

| # | reference | role |
|---|---|---|
| 10 | `juniper-cascor/scripts/juniper-cascor.service:45` | `ReadWritePaths` → CLI dir |
| 11 | `juniper-cascor/scripts/juniper-cascor.service:52` | `ReadWritePaths` → service dir (added with the #537 move) |
| 12 | `juniper-deploy/docker-compose.yml:265` | `juniper-cascor-snapshots:/app/data` (canonical cascor service) |
| 13 | `juniper-deploy/docker-compose.yml:434` | same mount, cascor-demo service |
| 14 | `juniper-deploy/docker-compose.yml:1119` | the named-volume declaration |

Under `ProtectSystem=strict` + `ProtectHome=read-only` (`juniper-cascor.service:41-42`), **a root
outside both `ReadWritePaths` entries EPERMs every save** — the exact failure the closeout handoff
flags as the one an incomplete sweep produces.

### 3.4 Launcher, tooling, tests, ignore rules

| # | reference | role |
|---|---|---|
| 15 | `juniper-ml/util/experiment_stack.bash:484,618,630,642` | exports `JUNIPER_CASCOR_SNAPSHOTS_DIR=${RUN_DIR}/snapshots` |
| 16 | `juniper-ml/tests/test_experiment_stack_script.py:416,441` | pins that export, **and its occurrence count == 3** |
| 17 | `juniper-cascor/src/tests/unit/api/test_w6_snapshots_dir_override.py:89-95` | asserts unset → `_SRC_DIR/"cascor_snapshots"` |
| 18 | `juniper-cascor/juniper-cascor-model/tests/test_constants_dir_overrides.py:52-54,68` | same assertion, package copy |
| 19 | `juniper-cascor/util/rename_snapshots.bash:24` | `DEST_DIR="src/cascor_snapshots"` |
| 20 | `juniper-ml/util/ad-hoc/2026-08-16_snapshot_archive_census.py:40,56` | census default dir |
| 21 | `juniper-cascor/.gitignore:62,63,65,66,72,74,75,76` | eight snapshot rules |
| 22 | 5 sibling repos: `juniper-canopy/.gitignore:34`, `juniper-cascor-client:52`, `juniper-cascor-worker:52`, `juniper-data:132-133`, `juniper-deploy:151-152` | `**/cascor/cascor_snapshots/*` |
| 23 | docs: `juniper-cascor/docs/api/API_REFERENCE.md:707`, `docs/source/QUICK_START.md:146`, `notes/API_REFERENCE.md:502`, `juniper-ml/docs/REFERENCE.md:1836` | operator-facing path statements |

> **Item 22 is inert, and worth knowing before anyone "fixes" it.** `**/cascor/cascor_snapshots/*`
> requires a path component named exactly `cascor`; the live path is `juniper-cascor/src/…`.
> Verified decisively: `git check-ignore --no-index src/cascor_snapshots/notmatching.h5` returns
> **not-ignored**, while a real snapshot is caught by `.gitignore:63 cascor_snapshot_*.h5`. So CLI
> snapshots are ignored **by filename pattern, not by directory** — which is also why the 47 tracked
> files of F-2 stayed tracked, and why a Phase 6.1 rename must keep the `cascor_snapshot_` prefix
> or silently un-ignore 27,886 files.

---

## 4. The three findings that change the answer

### 4.1 F-1 — Docker snapshots are not persisted today

`juniper-deploy/docker-compose.yml:265` and `:434` mount the named volume `juniper-cascor-snapshots`
at **`/app/data`**. Neither tier writes there:

- The image is built `WORKDIR /app` with `COPY --chown=juniper:juniper src/ ./src/`
  (`juniper-cascor/Dockerfile:59,66`), so `manager.py` sits at `/app/src/api/lifecycle/manager.py`.
- `_get_snapshots_dir` takes `Path(__file__).resolve().parents[3]` → **`/app`**, giving
  **`/app/snapshots`**.
- The CLI tier's `_HDF5_PROJECT_SOURCE_DIR` is `/app/src`, giving **`/app/src/cascor_snapshots`**.
- Compose **never sets** `JUNIPER_CASCOR_SNAPSHOTS_DIR` — grepped across `*.yml`, `*.env`,
  `*.example` and the Makefile in juniper-deploy: zero hits. So neither default is overridden.

**The arithmetic is corroborated, not just asserted.** The same `parents[]` reasoning predicts the
log directory at `/app/logs`, and `docker-compose.yml:266` mounts `juniper-cascor-logs:/app/logs` —
a directory that *does* line up. The method is right; the snapshot mount is the outlier.

**This predates #537**: before the move the service default was `/app/src/snapshots`, also not
`/app/data`. It is a long-standing mismatch, not a regression, and it is invisible because nothing
errors — snapshots write successfully into the container's writable layer and vanish on recreate.

**Why it bears on S-1.** A root derived from `__file__` cannot be mounted without knowing the
image's internal layout, and changes silently when the layout does. An **explicitly configured**
root — whether in-checkout or out — is mountable by name. Option C makes the correct mount
self-evident; Options A and B leave the operator deriving it from `parents[3]`.

> ⚠ **F-1 is a defect in its own right and is *not* fixed by answering S-1.** Whatever the ruling,
> juniper-deploy needs either the mount corrected or `JUNIPER_CASCOR_SNAPSHOTS_DIR` set to
> `/app/data`. Recorded here because it was found here; it should be tracked separately rather than
> folded into the S-1 change.

### 4.2 F-2 — 47 snapshots are in git history

```text
git ls-files src/cascor_snapshots/ | wc -l      →  47
git ls-tree -r -l HEAD -- src/cascor_snapshots/ →  1,694,936 bytes across 47 files
year-month distribution                          →  47 × 202510   (all of them)
```

That is **exactly** the design's §2 census row `2025-10 → 47`. The tracked cohort *is* the 2025-10
cohort — including the 800-byte husk that nearly produced the census's false headline (the first two
entries share blob `82daee09`, i.e. byte-identical duplicates).

Two consequences:

1. **It explains the mtime reset for that cohort.** Those 47 are written by `git checkout`, so their
   mtime is checkout time — §2.2's trap, with a mechanism attached for at least part of the archive.
   (The remaining ~27,800 are untracked; their reset has a different, un-investigated cause.)
2. **A default-path move does not remove them.** They will keep materialising in every clone and
   every worktree regardless of where new snapshots go. Removing them is a *separate* ruling —
   `git rm --cached` plus history, or leave them as a deliberate fixture.

### 4.3 F-3 — the CLI default ships inside a PyPI package

`juniper-cascor-model` vendors `cascor_constants` verbatim and is consumed by
`juniper-cascor-worker`. Installed as a wheel, `_HDF5_PROJECT_SOURCE_DIR` is the **package root in
site-packages**, so `_HDF5_PROJECT_SNAPSHOTS_DIR` resolves to `<site-packages>/cascor_snapshots`.

This is the same class the package already had to fix once: `test_drift.py`'s own header records
that the logger diverged deliberately *"where this package lives in site-packages and the
source-relative logs/ dir is not writable"*. The snapshot constant has the identical shape and has
**not** had the equivalent treatment.

**Stated precisely, because overclaiming is this arc's recurring failure: the exposure is latent,
not live.** `_EXTRACTED_DIRS` is `("candidate_unit", "utils", "log_config", "cascor_constants")` —
the package contains no `cascade_correlation` module, so nothing inside it consumes
`_HDF5_PROJECT_SNAPSHOTS_DIR`; the constant is exported (`constants.py:279`) but unread. It becomes
live the moment the model package grows a save path, or a consumer imports the constant. Option C is
the fix that also closes it.

---

## 5. The options

### Option A — status quo

Keep both defaults in the checkout; rely on W-6 for per-run isolation.

| | |
|---|---|
| **Change surface** | none |
| **Closes** | nothing |
| **Leaves open** | F-1, F-3, INT-P3-010 (`cascor_snapshots` vs `snapshots` confusion, tracked since the integration roadmap), the two-naming-scheme split |
| **Cost** | Phase 6.1 must pick one of the two roots anyway to unify naming, so the decision is deferred, not avoided |

Defensible only if the intent is that snapshots *are* checkout-scoped research artifacts. Worth
saying plainly: **that is a coherent position** — it makes a worktree self-contained, which suits an
experimentation platform where a checkout is a lab notebook.

### Option B — converge both tiers on `<repo>/snapshots`

Move the CLI default from `src/cascor_snapshots` to `<repo>/snapshots`, joining the service tier.

| | |
|---|---|
| **Change surface** | items 1, 3-5, 7-9, 10-11, 17-19, 21, 23 — both constants copies in lockstep (F-3 gate), the systemd unit, two test assertions |
| **Closes** | INT-P3-010; the two-root split; leaves one root to stamp in Phase 6.1 |
| **Leaves open** | F-1 (still `parents[]`-derived), F-3 (still site-packages-relative in the wheel), F-2 |
| **Migration** | 27,886 files orphaned from the default unless moved — and the design's §6.5 says *"No rewriting or migrating existing snapshot files"* |

### Option C — out of the checkout

Both tiers default to `${JUNIPER_CASCOR_STATE_HOME:-${XDG_STATE_HOME:-~/.local/state}}/juniper-cascor/snapshots`,
mirroring `JUNIPER_EXP_RUN_ROOT`.

| | |
|---|---|
| **Change surface** | Option B's, **plus** a third `ReadWritePaths` (or a `StateDirectory=`), plus the compose mount, plus operator docs |
| **Closes** | INT-P3-010, F-1 (root becomes nameable), F-3 (no longer source-relative), permanent checkout accrual |
| **Leaves open** | F-2 (needs its own ruling) |
| **Migration** | same 27,886-file question as B |

**Precedent for the destination is real but confined to tooling, not services.** `JUNIPER_EXP_RUN_ROOT`
defaults to `${HOME}/.local/state/juniper-experiments` at **10 lines across 8 files** —
`util/experiment_stack.bash:48,116`, `util/reap_pytest_orphans.bash:65,88`, five ad-hoc campaign
scripts (`2026-08-10_ea_aggregate_clean.py`, `2026-08-14_e_i_cap_ceiling_campaign.bash`,
`2026-08-14_r5_stack_up.bash`, `2026-08-16_h2h_init_control.bash`, `2026-08-16_h2h_orchestrate.bash`),
and `tests/test_experiment_stack_script.py:350`, which pins the default so it cannot drift. Separately,
`util/ad-hoc/2026-08-18_promote_sequence_safety.py:206` uses `~/.local/state/juniper-ruleset-snapshots`.
**No Juniper service uses `~/.local/state` today**; the nearest is a canopy comment contemplating it
(`juniper-canopy/src/settings.py:333`). Option C would be the first service adoption.

---

## 6. Recommendation

**Option C, staged, with the existing archive left where it is.**

1. **Service tier first.** It is a one-function change (`_get_snapshots_dir`), single-rooted across
   five call sites, call-time resolved, with `<repo>/snapshots` not yet existing on disk — so there
   is **nothing to migrate**. Ship it with the systemd `ReadWritePaths` line and the compose mount
   in the same change, which incidentally closes F-1. This is the cheapest available structural win
   and is independently verifiable.
2. **CLI tier second, as its own change.** It carries the F-3 lockstep edit, import-time semantics,
   two pinned test assertions, and the 27,886-file question. Separating it keeps the service fix
   from being held hostage to the migration debate.
3. **Do not move the existing archive.** §6.5 forbids it, and there is a better answer: Phase 6.2's
   index scanner is specified to run **read-only over the legacy archive**. Point it at both roots.
   The archive stays discoverable where it is; only new writes go to the new root. This converts the
   migration question into an index question, which is the design's own strategy.
4. **F-2 is a separate ruling** — 47 tracked files, 1.6 MiB. Cheap either way; it just needs a
   decision rather than drift.

**The staging is the substance of this recommendation.** If only one thing is taken from this brief,
take F-5: the two tiers are different enough that binding them to one change is what would make
Option C expensive. Split, the service half is small and closes a live defect.

**If the ruling is Option A**, the one thing that still needs doing is F-1 — Docker snapshot
persistence is broken independently of where the default points.

---

## 7. What this brief does *not* determine

Stated explicitly so the next reader does not mistake silence for coverage.

- **Whether the 27,886 files should ever move.** Deliberately out of scope; it is S-2/§6.4
  territory and unanswerable before the index exists.
- **Why ~27,800 untracked files have reset mtimes.** F-2 explains the 47 tracked ones. The rest is
  still "a copy did it", unverified.
- **Whether `juniper-cascor-worker` will ever save snapshots.** F-3's exposure is latent on the
  strength of `_EXTRACTED_DIRS` containing no `cascade_correlation`; if that changes, re-derive.
- **The Phase 6.1 filename**, beyond the constraint that it must keep the `cascor_snapshot_` prefix
  or defeat `.gitignore:63` (§3.4 note).

**Incidental, found in passing, not part of S-1:** `cascade_correlation.py:4933` and `:5012` read
`pl.Path(self.…snapshots_dir) or pl.Path(_CASCADE_…)` — a `Path` is always truthy, so the `or`
fallback is unreachable. Harmless today (the attribute is set at `:757`), but it is a guard that
reads as protection and provides none. The adjacent docstrings also say *"defaults to
./snapshots"*, which no code path produces.

---

## 8. Verification commands

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper
conda activate JuniperCascor1        # unsuffixed JuniperCascor has broken torch

# The two resolution sites — expect exactly one each
grep -n "_HDF5_PROJECT_SNAPSHOTS_DIR = pathlib" \
  "$JUNIPER/juniper-cascor/src/cascor_constants/constants_hdf5/constants_hdf5.py"
grep -n 'parents\[3\] / "snapshots"' "$JUNIPER/juniper-cascor/src/api/lifecycle/manager.py"

# F-1: the mount vs the write path
grep -n "juniper-cascor-snapshots:" "$JUNIPER/juniper-deploy/docker-compose.yml"      # /app/data, x2
grep -n "WORKDIR /app\|COPY --chown=juniper:juniper src/" "$JUNIPER/juniper-cascor/Dockerfile"
grep -rn "JUNIPER_CASCOR_SNAPSHOTS_DIR" "$JUNIPER/juniper-deploy"; echo "rc=$?  # 1 = never set"

# F-2: snapshots in git history
git -C "$JUNIPER/juniper-cascor" ls-files src/cascor_snapshots/ | wc -l               # 47
git -C "$JUNIPER/juniper-cascor" ls-tree -r -l HEAD -- src/cascor_snapshots/ \
  | awk '{s+=$4} END {print s" bytes / "NR" files"}'

# F-3: the byte-gated duplicate
diff "$JUNIPER/juniper-cascor/src/cascor_constants/constants_hdf5/constants_hdf5.py" \
     "$JUNIPER/juniper-cascor/juniper-cascor-model/cascor_constants/constants_hdf5/constants_hdf5.py"
grep -n "_EXTRACTED_DIRS\|_NORMALIZED_DIVERGENCE" \
  "$JUNIPER/juniper-cascor/juniper-cascor-model/tests/test_drift.py"

# §3.4 note: the sibling-repo ignore rule is inert
git -C "$JUNIPER/juniper-cascor" check-ignore -v --no-index src/cascor_snapshots/notmatching.h5
echo "rc=$?  # 1 = NOT ignored, i.e. **/cascor/cascor_snapshots/* never matches"

# Re-run the inventory before acting on it — UNTRUNCATED
"$JUNIPER/juniper-ml/util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash" --all \
  'JUNIPER_CASCOR_SNAPSHOTS_DIR' 'cascor_snapshots'
```

---

## 9. Related documents

- [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)
  — design of record; S-1 is its §9 open question, and §6.1/§6.2 are what this ruling unblocks.
- [`JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md`](JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md)
  — D-B's design of record (juniper-ml#1193). Independent of S-1; both touch `_load_snapshot_to_network`,
  so sequence them rather than interleaving.
- [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md)
  — companion prioritisation note.
- juniper-cascor#537 (service destination out of the importable package), #536 (drift gate made to
  fire), #539 (R3 resume — the item this brief follows in the owner's stated order).
