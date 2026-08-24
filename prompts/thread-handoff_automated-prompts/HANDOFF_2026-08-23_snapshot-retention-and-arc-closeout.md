# HANDOFF 2026-08-23 — snapshot retention (§6.4) and arc closeout

> **Continue the juniper-cascor / juniper-ml snapshot-lifecycle arc.** Handoff items 1–4 and 6
> are closed; **item 5 (retention) is the remaining work**, and it is an owner decision, not an
> implementation task.

**FIRST ACTION: put §2.3's three questions to the owner** — item 5 is blocked on them and
nothing else in §2 can proceed without the answers. **While waiting, land §3 item 1**: a
one-line unshipped fix (`Invalid format: None` names nothing), fully specified and ready.

Throughout, **"§N" means a section of THIS document**. References to other documents are
written as "the prior handoff's §3" or given a path in the table below.

## Documents

| what | path |
|---|---|
| **§6.4 — the retention policy this handoff is about** | `notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md` § "6.4 Phase 4 — Retention policy" |
| Stage-1 findings (root causes, §7.1 counters) | `notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_SNAPSHOT-CLASSIFICATION-STAGE-1-FINDINGS.md` |
| S-2 cohort characterisation | `notes/JUNIPER_2026-08-22_JUNIPER-CASCOR_S2-COHORT-CHARACTERISATION.md` |
| Predecessor handoff (its §2.4 scheme, §3 item list, §3.2/§3.4 owner prose) | [`HANDOFF_2026-08-22_snapshot-classification-and-metadata-reconstruction.md`](HANDOFF_2026-08-22_snapshot-classification-and-metadata-reconstruction.md) |

**Root-cause taxonomy** (used as bare letters below; cohort letter == cause letter):

- **A** — stale `config_json` after a live dataset resize. 239 files. Recoverable; fixed.
- **B** — truncated write (non-atomic save died mid-write). 273 files, three signatures. **The
  only irrecoverable loss in the archive.** Fixed going forward.
- **C** — config schema drift (a field this version removed). 14 files. Recoverable; fixed.

Line numbers drift constantly in `snapshot_serializer.py` / `cascade_correlation.py` —
**re-derive before editing**. Six merges moved them during this arc.

> ⚠ **Five findings below contradict a plausible first reading of the same data.** Each is
> marked ⚠. Every one was caught by a *mechanical check* — running tests against unfixed code,
> grepping for a known marker, comparing `HEAD` to `origin/main`, a save→load→save round trip.
> None was caught by reasoning. Do not re-derive them from intuition.

---

## 1. Shipped this arc — do NOT redo

Eleven PRs, all merged: 6 juniper-cascor, 5 juniper-ml.

| PR | repo | what |
|---|---|---|
| cascor#559 | juniper-cascor | **C** — loads snapshots carrying a since-removed config field |
| cascor#560 | juniper-cascor | **A loader half** — rebuild from `arch` when the tensors corroborate it |
| cascor#561 | juniper-cascor | **B** — atomic writes (`_atomic_hdf5_write`); a failed save leaves nothing |
| cascor#562 | juniper-cascor | **A writer half** — `_sync_config_dimensions()` on resize |
| cascor#565 | juniper-cascor | training counters measured-or-absent (**write** path) |
| cascor#574 | juniper-cascor | the same for the **load** path — #565 was half a fix (§4.3) |
| ml#1254 | juniper-ml | classifier + the three root causes (`util/snapshot_classify.py`) |
| ml#1255 | juniper-ml | findings-doc update (records what shipped) |
| ml#1273 | juniper-ml | dataset attribution (`util/snapshot_attribute.py`) |
| ml#1279 | juniper-ml | backfill (`util/snapshot_backfill.py`) |
| ml#1282 | juniper-ml | §7.1 correction — `snapshot_counter` is LIVE |

**Not this arc**, though this document cites them: **ml#1259** and **ml#1265** (another
session wired unrun test suites and added the drift gate). Do not attribute them here.

**Archive: 526 → 273 unloadable.** 253 recovered. All three write-side causes are closed, so
nothing new can join the 273.

---

## 2. THE REMAINING WORK — item 5, retention (§6.4)

An **owner decision**. Do not build deletion tooling before it is ratified.

### 2.1 The cohort table (this is what the decision keys on)

| cohort | n | standing |
|---|---:|---|
| **B — truncated writes** | **273** | the ONLY established, irrecoverable loss |
| zero-node, loadable | 15,927 | **recoverable** — 380/380 sampled trained on demand |
| attributed | 129 (**15** networks) | **candidate** for §6.4 "named" — contested, see §2.3 q2 |
| loadable, hidden units, unattributed | 11,579 | unattributable legacy → §6.4 "quarantine, never delete" |
| **total** | **27,908** | |

⚠ The 129 are **21 (network, dataset) pairs across 15 distinct networks** — five networks
attribute to more than one dataset (§3 item 5). "21 networks" is wrong.

### 2.2 ⚠ The prior handoff's §2.3 premise did not survive measurement

It offered zero-hidden-nodes as a *prima facie* signal that a network "could not perform normal
cascor operations", flagged as a deliberate overgeneralisation. **It does not hold.** 380 of
15,927 were loaded and trained: **380 trained, 0 failed.** Rule of three → 95% upper bound on
the dysfunctional rate ~0.8% (≤ ~126 archive-wide, plausibly zero). Category 2 (*fails to
train*) is **empty**. They are under-trained, not broken.

### 2.3 What §6.4 needs from the owner

1. Do B's 273 get deleted, quarantined, or kept? Unloadable AND unrecoverable — the only
   cohort where deletion loses nothing not already lost.
2. **Does attribution count as §6.4 "named"?** §6.4 defines *named/pinned* as "referenced by an
   evidence note, a suite registry, or an explicit keep-mark". Attribution is **statistical
   inference from behaviour** — none of those three. Unresolved; do not assume keep.
3. Is a compressed/encrypted archive via `util/juniper-backup.bash` (note the **hyphen**; the
   prior handoff's §3 item 4 wrote `juniper_backup.bash`) a sufficient safeguard before removal?

**Any retention tooling must be `--dry-run` by default, require `--yes`, refuse to operate on a
directory containing `.py` files, and log every action to the index** (§6.4). None of the four
existing tools has a delete path; each has an AST test enforcing that.

---

## 3. Also remaining, highest value first

1. **`Invalid format: None` names nothing.** `_validate_format_detail` renders
   `f"Invalid format: {format_name}"`, and `format_name` is `None` when the attribute is
   *absent* rather than wrong — conflating *missing* with *invalid*, for the 6 emptiest files
   in the archive. **One-line fix, unshipped.** Start here while waiting on §2.3.
2. **A capacity-matched null for attribution.** `util/snapshot_attribute.py` builds its null
   from freshly-constructed (**zero-hidden-unit**) networks — correct for the zero-node
   majority, **too lenient for grown networks**. The xor cluster survives on independent
   grounds (scores rise monotonically 0.945 → 0.995 as the net grows 18 → 103 units; an
   artifact does not produce a learning curve). **spiral (+0.062) and moon (+0.085) are
   provisional.**
3. **`/dev/shm` leak** — the OPT-5 SharedMemory class (cascor#60/#61) is not fully closed;
   orphaned runs leave segments behind. ⚠ **Time-sensitive and previously misreported**: it was
   8–9 `juniper_train_*` segments totalling **~283–316 KB** (not "32 MB" — that was the whole
   tmpfs `Used` column). Re-measure with `du -ch /dev/shm/juniper_train_*`, never `df`.
4. **Attribution instability** — five networks attribute to more than one dataset at different
   growth stages: `2537e0f0` (circles 4 / xor 2 / **moon 1** — three datasets), `846587fb`
   (circles 3 / xor 1), `17de4973`, `1e9e15a8`, `5af596ef` (spiral/moon or moon/circles).
   Either retrained on a second dataset (no other record) or attribution is unstable there.
5. **Orphaned cascor run — RESOLVED, no action.** PID 1764840 is **gone**; `ps` returns
   nothing. Recorded only so the forensics are not redone: it was reparented to
   `systemd --user`, 15 children, 4.6 GB, silent 13 h, unprotected by either reaper key. ⚠ The
   three `*.pid` files under `~/.local/state/juniper-experiments/` hold 2755940 / 1309004 /
   3777156 — **all three are dead processes / stale pidfiles**, and two of the three sit at the
   directory root, not in run dirs.

---

## 4. Findings that constrain the work

### 4.1 ⚠ `snapshot_counter` is LIVE — the prior handoff's §4.1 was wrong

Over an 800-snapshot sample of the archive **as written**:

| field | archive reality | assigned in the model? |
|---|---|---|
| `current_epoch` | INERT — 0 in all 800 | **never**, still true at HEAD |
| `patience_counter` | INERT — 0 in all 800 | never *before* cascor#565; **assigned now** |
| `best_value_loss` | INERT — `inf` in all 800 | never *before* cascor#565; **assigned now** |
| **`snapshot_counter`** | **LIVE — 28 distinct values** | **yes, increments** |

The count of three was right; the **membership was wrong in both directions**. One network's
110 snapshots carry `snapshot_counter` **0 → 109** — a **per-run ordering signal**, independent
of filename timestamps, available across the whole archive. Corrected in ml#1282. Continue to
use `arch.num_hidden_units` as the *iteration lower bound*; never an epoch count.

### 4.2 ⚠ Dataset attribution: "beats chance" is NOT evidence

An **untrained** network beats chance on `gaussian` by **+0.408 mean, up to a perfect +0.500** —
the blobs are linearly separable and permutation-correction amplifies it. 11 of 12 untrained
nets "pick" gaussian. So the bar is the **untrained-network null**, and gaussian is
**structurally unattributable** (floor 1.000 — strictly, floor *plus* the 0.05 margin).

Two further corrections:

- **Raw accuracy is the wrong metric.** One-hot column order is arbitrary; a network that
  learned a set with swapped columns scores `1-p`, reading as *below* chance. Archive snapshots
  at **0.010** on gaussian are **0.990** inverted. Use `max(p, 1-p)`.
- **The floor is the null's observed MAX, not p95.** ⚠ The "327 checkerboard" anecdote in
  `snapshot_attribute.py`'s docstring is **not reproducible** — a replay of `adjudicate` over
  the recorded scores attributes **0** to checkerboard under every {p95|max}×{0|0.05}
  combination, and that docstring contradicts itself on whether the scores sat *between* p95
  and max or *above* max. The **direction is right** (p95 → max removes ~46 attributions,
  spiral 60→20, circles 13→8); the cited numbers are not. Do not quote them.

### 4.3 ⚠ A fabricated default is indistinguishable from a measurement — and the fix took TWO PRs

`_save_metadata` wrote `getattr(network, "best_value_loss", float("inf"))` for an attribute the
model never assigned, so the default was written every time. Reading the archive literally said
nothing ever trained — the reading that nearly justified deleting 27,005 real models.

**cascor#565 fixed only the write path.** `_restore_training_state_helper` kept
`.get(name, default)`, so the defect returned on **any resume**: load a snapshot that correctly
omitted `best_value_loss`, get `inf` written onto the instance, re-save, and the file claims a
measurement nobody took. Closed in **cascor#574**, which also fixed a second defect the guard
exposed — the helper's own debug log f-stringed `patience_counter` unconditionally, so an
absent counter raised `AttributeError` and a **good snapshot reported as `SNAPSHOT_CORRUPT`**.

Generalisable: **a missing key is a question you can ask; a fabricated default is an answer you
cannot check.** And a write-side guard is only half — check the read side too.

### 4.4 ⚠ "Can it train?" is about PROCESS, not outcome

Score it as *`fit()` completed AND the cascade installed a unit*. One sampled snapshot went
**0.490 → 0.460** (accuracy worse) while training cleanly — category 3, not category 2. An
outcome-based rule files healthy networks as dysfunctional.

---

## 5. Traps this arc paid for

1. **A stale local checkout clobbers your OWN work.** `util/open_signed_pr.py` sends WHOLE
   files. Scratch copies from a `juniper-cascor` checkout **3 commits behind** would have
   reverted cascor#561 and #562 — both merged earlier the same session. `git log
   HEAD..origin/main -- <paths>` was *misleading*: it listed those PRs and they read as
   "already mine". **Ask "is my copy current?"** — `git rev-parse --short HEAD` must equal
   `origin/main`, and grep the scratch file for a marker of each merged fix
   (`_atomic_hdf5_write`, `_sync_config_dimensions`); `0` means you would revert it.
   **Fast-forward the sibling checkout after every merge to it.**
2. **A `noqa` can hide a real defect.** `import ast  # noqa: F401 - …` with a plausible
   rationale survived self-review AND pre-commit; only CodeQL caught it, post-push, as an
   unresolved thread that blocks merge **while every check reads green**. `util/` is outside
   flake8's pre-commit scope (`^(scripts|tests)/.*\.py$`), which also `--extend-ignore`s F401.
   Run before every push:
   `python -m flake8 --select=F401,F811,F841 --max-line-length=512 util/<files>`.
3. **CodeQL blocked three PRs in this arc at fully-green checks.** `mergeStateStatus=BLOCKED`
   with 17/17 or 25/25 passing means an unresolved review thread — check with the
   `reviewThreads` GraphQL query, not `gh pr checks`. The thread resolves itself once the code
   changes; do not hunt for a dismiss button.
4. **cascor's training defaults are sized for real runs, not probes**: `candidate_pool_size=40`,
   `candidate_epochs=400`, `output_epochs=10000`, `max_iterations=1e6`. A naive `fit()` is
   minutes per network. For probes: `CASCOR_NUM_PROCESSES=1`, `pool=3`, `candidate_epochs=30`.
   (The `max_epochs`-vs-`output_epochs` split itself is a **settled owner decision** recorded
   in `cascade_correlation.py` — "Do not 'fix' this by forwarding `max_epochs`." It is also
   AGENTS.md's 4th resident hazard. Pin both; do not re-litigate.)
5. **`train_output_layer` calls `create_snapshot()` unconditionally.** Set
   `JUNIPER_CASCOR_SNAPSHOTS_DIR` **before any cascor import** — `constants_hdf5.py` reads it at
   module-import time — or a probe grows the archive it is measuring.
6. **A test that never runs is indistinguishable from one that passes.**
   `tests/test_ci_test_wiring_drift.py` now enforces `tests/test_*.py ⊆ ci.yml`. Adding a suite
   takes three edits: ci.yml run block, ci.yml install block, AGENTS.md.
7. **Verify a new suite FAILS against unfixed code.** Every suite this arc was checked that way
   (10/15, 6/10, 6/8, 1/3 failing pre-fix). `assert status != OK` passed against a broken design
   and would have shipped a regression — assert the SPECIFIC status.
8. **`pre-commit` on anything under `prompts/` is a VACUOUS PASS.** `.pre-commit-config.yaml`
   excludes `prompts/.*`, so every hook reports "no files to check" — including doc-link
   validation. **Handoffs are never machine-validated.** This one was reviewed by three
   independent agents instead, which found 23 defects including a live bug in cascor#565.
   **Validate the next one the same way.**

---

## 6. Verification commands

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper
conda activate JuniperCascor1                 # REQUIRED — unsuffixed JuniperCascor has broken torch

git -C "$JUNIPER/juniper-ml" fetch --prune && git -C "$JUNIPER/juniper-ml" log --oneline -1 origin/main
git -C "$JUNIPER/juniper-cascor" fetch --prune && git -C "$JUNIPER/juniper-cascor" log --oneline -1 origin/main
gh pr list --repo pcalnon/juniper-ml --state open       # dup-guard; stale within minutes
gh pr list --repo pcalnon/juniper-cascor --state open

# the four sidecars (all gitignored, all beside the archive)
python "$JUNIPER/juniper-ml/util/snapshot_index.py"     --stats
python "$JUNIPER/juniper-ml/util/snapshot_classify.py"  --from-sidecar --stats
python "$JUNIPER/juniper-ml/util/snapshot_attribute.py" --from-sidecar --stats
python "$JUNIPER/juniper-ml/util/snapshot_backfill.py"  --from-sidecar --stats
# attribution EVIDENCE (not provenance — the tool's own output says so) for the XOR-attributed net
python "$JUNIPER/juniper-ml/util/snapshot_backfill.py"  --from-sidecar \
       --explain cascor_snapshot_20260707_183654

cd "$JUNIPER/juniper-ml"
python3 -m unittest -v tests/test_snapshot_index.py tests/test_snapshot_classify.py \
                       tests/test_snapshot_attribute.py tests/test_snapshot_backfill.py

# cascor gates that must stay green for ANY snapshot-path change
cd "$JUNIPER/juniper-cascor/src"
python -m pytest tests/unit -q --slow
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CASCOR_NUM_PROCESSES=1 \
  python -m pytest -m golden --golden --slow --integration tests/integration/test_golden_trajectory.py
```

**Expected sidecar figures** — regenerate if they disagree; the archive grows when other
sessions train, so the raw `.h5` count drifts while the sidecar totals do not:

- index: `total` 27,908 · `attributed` 1 · `unattributed` 27,907
- classification `by_category`: `fails_to_load` **273** · `loads_hidden_nodes` 11,708 ·
  `undetermined` 15,926 · `fully_attributed` 1 · **`fails_to_train` 0** · **`formerly_broken` 0**
  (the two zeros are load-bearing — §2.2's claim is that category 2 is empty)
- classification `by_health`: `zero_node` **15,927** (= `undetermined` 15,926 + the 1
  `fully_attributed`; §2.1 counts on the health axis, this block on the category axis — both
  are right, they are different frames)
- attribution: **129** attributed (xor 94 / spiral 20 / circles 10 / moon 5, **gaussian 0**),
  2 ambiguous
- backfill: root causes `{"B": 273}` · identity recovered **1** · unrecoverable 27,907

**Archive:** `$JUNIPER/juniper-cascor/cascor-snapshots/` — ~27,923 `.h5` and rising, plus four
`*.jsonl` sidecars, all gitignored by `/cascor-snapshots/*`.

---

## 7. Git state and procedure

- **This file was archived by the authoring session** (unlike some siblings, it is not left
  untracked for the successor to commit). If `git log -1 -- <this file>` shows no commit, it
  was not merged — commit it before anything else.
- Work was done in the session worktree
  `juniper-ml/.claude/worktrees/parallel-percolating-lollipop`, branch
  `worktree-parallel-percolating-lollipop`, otherwise clean and synced to `origin/main`.
- **juniper-ml** `origin/main` at handoff: **`18760ad`**. **Re-probe; do not trust this SHA** —
  parallel sessions merge continuously; main moved ~12 times during this arc.
- **juniper-cascor** `origin/main` at handoff: **`e20c9d1b`** (cascor#574). Also re-probe.
- Zero PRs from this arc open in either repo.
- **Worktrees are the standing default** for task work, centralized in `Juniper/worktrees/`.
- **`required_signatures` is live fleet-wide** — a headless local commit cannot land. Use
  `juniper-ml/util/open_signed_pr.py`; it refuses an existing branch by design, so to amend a
  PR in flight use `util/ad-hoc/2026-08-22_amend_signed_pr.py` (added this arc), which pins
  `expectedHeadOid` to the **branch** head.
- **Merge queues are unavailable to Juniper** (user-owned repos) — settled policy, do not
  re-raise. Use `util/safe_merge.py`. It arms an auto-merge net pinned to the OLD head before
  refusing, then disarms; the net does **not** re-pin after an amend.
