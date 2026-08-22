# HANDOFF 2026-08-22 — snapshot classification and metadata reconstruction

Successor to
[`HANDOFF_2026-08-19_snapshot-arc-closeout-and-r3-resume.md`](HANDOFF_2026-08-19_snapshot-arc-closeout-and-r3-resume.md).

**Nothing from this arc is in flight.** Eleven PRs merged (6 juniper-ml, 5 juniper-cascor); every
one is on `main` and green. The snapshot lifecycle design's §6.1–§6.3 are closed and §6.4 is
unblocked. What remains is the **owner's classification scheme** (§2), which is new design work,
not cleanup.

Citations are `file:NNN`. Line numbers drift constantly in `manager.py` / `snapshot_serializer.py`
— **re-derive before editing**; two merges this arc shifted `manager.py` by ~66 lines each.

> ⚠ **Three findings in this document contradict a plausible first reading of the same data.**
> Each is marked. They were all caught by checking a case whose answer was known in advance; none
> was caught by review. Do not re-derive them from intuition.

---

## 1. Shipped this arc — do NOT redo

| PR | repo | what |
|---|---|---|
| cascor#539 | juniper-cascor | **R3** — resume continues the restored optimizer (golden-neutral) |
| ml#1193 | juniper-ml | D-B design-of-record |
| ml#1195 | juniper-ml | retracted the false `load_network` claim **in place** |
| ml#1199 | juniper-ml | D-E design + shape probe |
| cascor#542 | juniper-cascor | **D-B** — corrupt snapshot is 422, not 404 |
| cascor#551 | juniper-cascor | **D-E** — enforce the load-time integrity gates |
| cascor#553 | juniper-cascor | D-E gap — the **two hidden-unit checksum gates** (six→eight) |
| cascor#554 + ml#1230 | both | **D-C** — provenance capability + launcher wiring |
| ml#1218 | juniper-ml | probe fix (D-E had broken its own evidence tool) |
| ml#1238 + ml#1244 | juniper-ml | **§6.2 index + query**, and the `dataset_id` join |
| cascor#558 | juniper-cascor | test suite no longer leaks snapshots into the archive |
| ml#1247 | juniper-ml | **S-2 cohort characterisation** (findings, no policy) |

---

## 2. The owner's classification scheme — THE remaining design work

Recorded 2026-08-22, and it supersedes the framing in ml#1247 §3. Reproduce faithfully; the
reasoning matters as much as the categories.

### 2.1 Iterations, not epochs

> *"Number of iterations is the important measure of training duration. Number of epochs — both
> for output training and for candidate pool training — is essentially meaningless."*

- Output training's **principal metric is accuracy**, not epoch count: whether a round ran its
  full budget or stopped early is not significant.
- Candidate-pool training's **product is the best candidate meeting the correlation threshold**.
  Epochs spent are effectively irrelevant.

**Therefore: hidden-node count is a LOWER BOUND on completed cascor iterations.** Each installed
hidden node required one successfully completed iteration. Some unknown number of iterations may
have run without finding a candidate that cleared the threshold, so the true count is ≥ the node
count.

This is why ml#1247 is framed on `arch.num_hidden_units` — and it is now the *right* framing for
a second reason, not just because the epoch counters are broken (§4.1).

### 2.2 Inference is sufficient for accuracy

A snapshot that loads can, by definition, perform inference. So **every loadable snapshot yields
two recoverable attributes**: a lower bound on iterations, and a network accuracy value.

### 2.3 Zero hidden nodes as a prima facie signal

Zero hidden nodes is a *prima facie* indication the network could not perform normal cascor
operations. **The owner flags this as a deliberate overgeneralisation** — useful if we accept that
the interesting networks are those that operated well enough to grow.

To go deeper: **load the no-hidden-node snapshots and initiate standard training.** At that point
current training performance becomes the only truly interesting attribute, and its behaviour fills
in the missing metadata. A snapshot that then fails to train belongs to a different subset —
dysfunctional networks.

### 2.4 Draft categories

1. **fails to load**
2. **fails to train**
3. **formerly broken** — reloads without hidden nodes, but *is* able to train
4. **loads hidden nodes**
5. **fully attributed** — snapshots generated going forward with full metadata

### 2.5 The intended sequence

> initial classification → network inference → training operations → use the resulting data to
> fill out missing snapshot metadata.

---

## 3. Remaining work, in dependency order

1. **Classifier (read-only) over the §6.2 index** — categories 1, 4, 5 are already derivable
   without opening a file: `readable`, `arch.num_hidden_units > 0`, `provenance != null`.
2. **Inference pass** — load each loadable snapshot, run inference, record accuracy. Needs a
   dataset; the cohort is uniformly 2-in/2-out synthetic (§4.3), so a generated spiral/moons set
   is the plausible stand-in. **Whether accuracy against a *substitute* dataset is meaningful is
   an open question for the owner** — the original dataset identity is unrecoverable (§4.2).
3. **Training probe for the zero-node subset** — separates *formerly broken* (trains) from *fails
   to train* (dysfunctional). This is the expensive step: ~11,751 networks.
4. **Backfill** — write the recovered attributes somewhere. **Do not write into the snapshots**
   without an explicit decision: they are read-only project assets and the index is the natural
   home.
5. **§6.4 retention** — the owner's call, now informed.
6. **Inert-metadata defect (§4.1)** → defect-register entry + a cascor writer fix. Not started.

---

## 4. Findings that constrain the work

### 4.1 ⚠ `meta.current_epoch` / `snapshot_counter` / `best_value_loss` are INERT

`current_epoch` is `0` across **all 27,908** snapshots — including all 174 snapshots of a network
that grew **0 → 260 hidden units**. `snapshot_counter` is `0`; `best_value_loss` is `inf`.

**The false reading this produced:** *"every snapshot is at epoch 0, so nothing was trained here"*
— which would have justified deleting 27,005 real models. It only came apart on checking a network
known to have grown. Three fields that look like training-progress metadata are dead.

Independently confirmed by the owner's §2.1 reasoning: even if they worked, epochs would be the
wrong measure. **Use `arch.num_hidden_units`.**

### 4.2 ⚠ Identity is UNRECOVERABLE for the Mar–Apr cohort

**Zero surviving experiment run dirs before 2026-07-30** (267 exist; earliest `20260730T…`; the
cohort is March–April). ml#1244's `run_id → manifest → dataset_id` join needs both halves and the
cohort has neither. Do not propose retroactive attribution — it was checked and it is gone.

### 4.3 The cohort, measured (ml#1247)

27,005 snapshots (96.8% of archive), 1.7 GiB, 16,462 networks, all readable, cascor 0.3.2/0.4.0.

| | networks | snapshots | bytes |
|---|---|---|---|
| grew ≥1 hidden unit | 4,711 | 15,057 | 1.17 GiB |
| never grew | 11,751 | 11,948 | 499 MiB |

Never-grew are **not untrained** — 200/200 sampled had non-zero `output_weights`. Architecture is
uniformly (2 in, 2 out) with 0–3 hidden: the synthetic-generator family, not equities.

### 4.4 ⚠ The four-day cluster is a VOLUME event, not a failure event

Per the owner's instruction, cascor PRs merged in the 3–5 days before 2026-03-31 were reviewed.
The window is dense with directly relevant work:

| PR | date | title |
|---|---|---|
| #43–#57 | 03-29/30 | metrics emission, candidate-progress streaming, TrainingMonitor refactors |
| #58 | 04-02 | resolve resource tracker KeyErrors |
| #60, #61 | 04-03 | **critical training failure** / resource leak from OPT-5 SharedMemory |
| #64 | 04-04 | **rename epoch → iteration in `grow_network` for correct CasCor semantics** |
| #66 | 04-04 | resolve training stalling, add growth iteration semantics |

**The tempting conclusion — "the OPT-5 training failure caused the never-grow cluster" — is not
supported.** Both categories spike together and collapse together:

| day | never-grew | grew |
|---|---|---|
| 03-31 | 1,263 | 1,548 |
| 04-01 | 2,059 | 3,738 |
| 04-02 | 751 | 1,103 |
| 04-03 | 1,962 | 1,417 |
| **04-04** | **71** | **87** |

The never-grew *fraction* during the cluster (~44%) matches the cohort-wide rate. So it is the
heaviest experimentation period in the archive — a debugging campaign against exactly those
training failures — that ended abruptly on 04-04 when #64/#66 landed. Note #64 renamed epoch →
iteration for correct CasCor semantics, which is the same distinction §2.1 draws.

---

## 5. Traps this arc paid for — read before starting

1. **`util/open_signed_pr.py` sends WHOLE FILES.** It silently reverts any concurrent change to
   those paths. Re-check **immediately before pushing**, not at sync time:
   `git log --oneline HEAD..origin/main -- <paths you will --add>` (want empty). Cost this arc one
   clobber of `docs/REFERENCE.md`.
2. **A docs-screen deletion count larger than your edit means CLOBBER, not "add a waiver".** The
   screen suggests `Allow-Docs-Rewrite:`; adding it cements someone else's deleted work. Rebase.
3. **Run the sequence-safety screens locally before pushing**, every time
   (`juniper-symbol-loss-check`, `juniper-docs-additions-check` vs `origin/main`). Skipping one
   PR in a turn is how the clobber reached CI. **Extract-method refactors trip the symbol screen
   as `WEAKENED`** and need `Allow-Symbol-Loss: method:<Class>.<name>` **in the first commit**.
4. **`safe_merge.py` false negatives.** Exit 3 twice on PRs that HAD merged (deleted head ref;
   base-branch race). Always check `gh pr view <n> --json state` before retrying. ml#1242 has
   since fixed the net-won case.
5. **`tests/` has weaker lint than `util/`** in juniper-ml — flake8 is relaxed there, so an unused
   import passes locally and **CodeQL blocks the merge via an unresolved review thread while every
   required check is green**.
6. **`ls dir/*.h5 | wc -l` returns 0 at ~28k files** (ARG_MAX; `ls` fails silently). Use `find`.
7. **`train_output_layer` calls `create_snapshot()` unconditionally.** cascor#558 stopped the test
   suite leaking into the shared archive, but any ad-hoc script with the provenance env set still
   writes there. Set `JUNIPER_CASCOR_SNAPSHOTS_DIR` for probes.
8. **`util/snapshot_index.py` is READ-ONLY by construction**, enforced by an AST test. Retention
   is §6.4; do not add a `--prune` while implementing the classifier.

---

## 6. Verification commands

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper
conda activate JuniperCascor1                 # REQUIRED — unsuffixed JuniperCascor has broken torch

git -C "$JUNIPER/juniper-ml" fetch --prune && git -C "$JUNIPER/juniper-ml" log --oneline -1 origin/main
gh pr list --repo pcalnon/juniper-ml --state open      # dup-guard; goes stale in minutes

# the §6.2 index (append-only; ~3m27s cold, ~1s to query)
python "$JUNIPER/juniper-ml/util/snapshot_index.py" --scan
python "$JUNIPER/juniper-ml/util/snapshot_index.py" --stats
python "$JUNIPER/juniper-ml/util/snapshot_index.py" --experiment E --cell-id C --resolve-datasets

# the S-2 characterisation (reads the index, not the snapshots)
python "$JUNIPER/juniper-ml/util/ad-hoc/2026-08-22_s2_cohort_characterisation.py"

# cascor gates that must stay green for any snapshot-path change
cd "$JUNIPER/juniper-cascor/src"
python -m pytest tests/unit -q --slow
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CASCOR_NUM_PROCESSES=1 \
  python -m pytest -m golden --golden --slow --integration tests/integration/test_golden_trajectory.py
```

**Archive:** `$JUNIPER/juniper-cascor/cascor-snapshots/` — 27,908 `.h5`, 1.7 GiB, plus
`snapshots_index.jsonl` (gitignored). The root moved there in cascor#548; `src/cascor_snapshots`
no longer exists.

---

## 7. Git state and procedure

- **juniper-ml** — this arc's last merge was **`be644c3`** (ml#1247), but main had already advanced
  to `c88a23d` before this handoff was written. **Re-probe; do not trust this SHA.** Parallel
  sessions merge to juniper-ml continuously — main moved roughly a dozen times during this arc,
  which is also what makes trap §5.1 live rather than theoretical.
- **juniper-cascor** `origin/main` **`7e06dc6`** (cascor#558) at handoff — quieter, but re-probe.
- Zero open PRs in either repo at handoff (verified, and stale within minutes).
- No worktrees from this arc remain; all were removed, branches deleted, `git worktree prune` run.
- **Worktrees are the standing default** for task work, centralized in `Juniper/worktrees/`.
- **`required_signatures` is live fleet-wide** — a headless local commit cannot land. Use
  `juniper-ml/util/open_signed_pr.py`; to amend a PR already in flight it refuses (by design), so
  use `createCommitOnBranch` with `expectedHeadOid` pinned, and only re-cut the PR when a waiver
  trailer must ride the first commit.
- **Merge queues are unavailable to Juniper** (user-owned repos) — settled policy, do not
  re-raise. Use `util/safe_merge.py`.
