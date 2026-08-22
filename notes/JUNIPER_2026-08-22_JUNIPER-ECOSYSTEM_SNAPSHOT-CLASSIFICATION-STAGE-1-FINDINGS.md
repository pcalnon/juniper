# Snapshot Classification — stage 1 findings, and the root cause of "fails to load"

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-22

**Status**: FINDINGS — measured, not proposed. Ships the classifier
(`juniper-ml/util/snapshot_classify.py`) and reports what a full-archive load pass says.
No snapshot was modified and none was deleted. Line numbers are against juniper-cascor
`7e06dc6` and drift constantly in `snapshot_serializer.py` / `cascade_correlation.py` —
**re-derive before editing**.

Successor to the 2026-08-22 handoff
[`HANDOFF_2026-08-22_snapshot-classification-and-metadata-reconstruction.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-22_snapshot-classification-and-metadata-reconstruction.md),
whose §3 item 1 (classifier) is what this closes.

---

## 1. Headline

**526 of 27,908 snapshots (1.88%) fail to load**, against a §6.2 index that reports all
27,908 as `readable`. All 526 decompose into exactly **four** root causes with nothing
left over (§3), and **253 of them are recoverable today**.

In order of how much each changes the plan:

1. **The handoff's §3.1 shortcut is wrong.** Category 1 (*fails to load*) is **not**
   derivable from the §6.2 index. `readable` there means only *h5py opened the file*,
   and it is `true` for all 27,908. Classification needs a real load pass through
   cascor's own `load_network_result`. That pass costs 14 minutes — this is a cheap
   correction, not an expensive one.

2. **The largest class is not damage — it is a REBUILD FAULT** (A, 239 files), and the
   snapshots are fully recoverable: 5/5 specimens recovered a self-consistent, inferring
   network. §4.

3. **A second class IS real, irrecoverable data loss** (B, 273 files), and one root cause
   explains it *and* every other structurally-partial file in the archive: **snapshot
   writes are not atomic**. §5.

4. **A third class is a time bomb** (C, 14 files): the loader cannot tolerate config
   schema drift, so **every future removal of a config field retroactively bricks
   whichever slice of the archive still carries it**. The only one of the three that is
   still accruing. §6.

Findings 2–4 are what §3.4 of the handoff asked for — "root cause determination of the
formatting or data issues affecting the *fails to load* snapshots".

> ⚠ **Two findings here contradict a plausible first reading of the same evidence.**
>
> * **A contradicts the loader's own error message.** The gate says *"output_size
>   disagrees: the snapshot's arch group says 3, the network built from its config is
>   2"*, which reads as "this file is inconsistent with itself". It is not: three of the
>   four places recording `output_size` agree on 3, the tensors are self-consistent at 3,
>   and the fourth is the one the loader trusts.
> * **C is not the bug it looks like.** All 14 also carry a malformed
>   `activation_function_name` (`'Tanh()'`). That is a real oddity and it is *not* the
>   cause — 126 files carry it and 112 load fine. Only running the loader and reading the
>   exception separated correlation from causation.
>
> Neither was caught by reading. Do not re-derive them from intuition.

---

## 2. What shipped — the classifier

`juniper-ml/util/snapshot_classify.py`, read-only, with
`juniper-ml/tests/test_snapshot_classify.py` (33 tests).

**Staged, because the five categories differ in cost by five orders of magnitude:**

| stage | cost (measured) | settles |
|---|---|---|
| `index` | ~1 s over 27,908 | categories 4 and 5; narrows the rest |
| `load` | **35 files/s → ~14 min** for the archive | category 1, authoritatively |
| `train` | **not implemented** (handoff item 3) | categories 2 vs 3 |

**Two axes, not one.** The owner's five categories (§2.4 of the handoff) are not a
partition, and the order they are listed in is not a first-match-wins precedence — read
that way, **category 5 is unreachable**, because every attributed snapshot with hidden
units is caught by category 4 first and every attributed one without them by 2 or 3. So
the tool emits:

- `category` — *does this snapshot's metadata need reconstructing?* Attribution decides
  it; `fails_to_load` overrides, because a broken file needs a root cause whatever
  metadata it carries.
- `health` — *what can the artifact actually do?* `fails_to_load` / `zero_node` /
  `has_hidden`.

This is a **resolved ambiguity, not a reading of the source text**, and it is the one
design decision in this work that is the owner's to overturn. `CATEGORY_PRECEDENCE` in
the module is the single place that encodes it. Health questions must be asked with
`--health`, never `--category`.

**`iterations_lower_bound`, never an epoch count.** Per §2.1, hidden-unit count is a
lower bound on completed cascor iterations. The tool reports it and never reads
`meta.current_epoch`, which is inert (§7.1).

**No `--prune`, AST-enforced**, mirroring `snapshot_index.py`. Retention is §6.4 and is
gated on this tool's output; acting on a verdict inside the tool that forms it would
prejudge the decision.

---

## 3. The population

Full load pass over all 27,908 files, `snapshot_classify.py --stage load --write`.

Full load pass over all 27,908 files, `snapshot_classify.py --stage load --write`:
**846.6 s (14.1 min), 30.3 ms/file**, sidecar written.

| category | files | note |
|---|---:|---|
| `loads_hidden_nodes` (4) | 11,513 | loads, carries hidden units |
| `undetermined` | 15,868 | loads with zero hidden units — **categories 2 vs 3 need the train stage** |
| `fails_to_load` (1) | **526** | 1.88% of the archive |
| `fully_attributed` (5) | 1 | the single D-C snapshot |
| `fails_to_train` (2) / `formerly_broken` (3) | 0 / 0 | not yet decidable — the train stage is unimplemented |

**526 fail to load, against an index that reports all 27,908 as `readable`.** That is
1.75× the forensics design's ~300 extrapolation, because D-E's gates now enforce.

Every one of the 526 decomposes into exactly **four** root causes, with nothing left over:

| # | signature | files | root cause | recoverable? |
|---|---|---:|---|---|
| A | `output_size disagrees: …arch group says N, …built from its config is N` | **239** | stale `config_json` after a live resize (§4) | **yes — measured** |
| B | `Missing required group: random` | **265** | truncated write, stopped inside `hidden_units` (§5) | **no — hidden units lost** |
| B | `Invalid format: None` | **6** | truncated write, stopped before root attrs (§5) | no — file is empty |
| B | `Missing required group: params` | **2** | truncated write, stopped after `config` (§5) | no |
| C | `snapshot could not be deserialized into a network` | **14** | config schema drift (§6) | **yes — trivially** |
|  | | **526** | | |

Health axis (independent of attribution): `has_hidden` 11,513, `zero_node` 15,869,
`fails_to_load` 526.

**Archive-wide iteration lower bound: 78,798 completed cascor iterations**, max 260 in a
single network, over 11,973 snapshots carrying at least one hidden unit.

---

## 4. Root cause A — the arch-mismatch class is a rebuild fault, not damage

### 4.1 What the file actually contains

A snapshot records `output_size` in **four** places, from **two** different sources:

| where | written from | specimen value |
|---|---|---|
| `arch.attrs["output_size"]` | `network.output_size` (live) | **3** |
| `config.attrs["output_size"]` | `network.output_size` (live) | **3** |
| `params/output_layer/weights`, `…/bias` | the live tensors | **(4, 3)**, **(3,)** |
| `config/config_json` | `network.config.output_size` (**the config object**) | **2** |

`_save_configuration` (`snapshot_serializer.py:324`) writes the JSON from
`network.config` and the attrs from `network.<attr>`. `_save_architecture` (`:380`) also
reads the live network. So three independent records agree at 3, the tensors are
mutually consistent at 3, and `config_json` alone says 2.

`_create_network_from_file` (`:1613`) prefers `config_json` whenever it is present, so
the network is rebuilt at width 2 and the width-3 tensors are then loaded into it. D-E's
arch gate correctly notices and refuses. **The gate is right; its input is wrong.**

### 4.2 Why the config object goes stale

`_resize_network_for_dataset` (`cascade_correlation.py:897`) — the live dataset swap
shipped in cascor#252 — does:

```python
self.input_size = input_size_new
self.output_size = output_size_new
self.active_output_dim = output_size_new
```

and never touches `self.config`. **`config.output_size` is never assigned anywhere in the
cascor source tree** (verified by grep: reads at `cascade_correlation.py:678`, `:740`,
`:741`; zero writes). Once a network is resized, its config object is permanently stale,
and every snapshot taken afterwards carries the contradiction.

### 4.3 They are recoverable — measured

`util/ad-hoc/2026-08-22_arch_mismatch_recoverability_probe.py`, 5 specimens, loaded with
`allow_invalid=True`:

```
   config_json.output_size=2   arch.output_size=3
   strict load        : snapshot_arch_mismatch
   permissive load    : OK   weights=(4, 3) bias=(3,) hidden=2
   tensors self-consistent at width 3: True
   inference          : OK  out=(4, 3) all-finite=True

RESULT: 5/5 recovered a self-consistent, inferring network
```

In every case `weights.shape == (input_size + len(hidden_units), 3)` and
`bias.shape == (3,)`. These are healthy models.

### 4.4 What this implies

- **Do not classify this cohort as broken, and do not consider it for deletion.** It is
  category 4 wearing category 1's clothes.
- **D-E made a real regression visible, not a new one.** Before cascor#551/#553 these
  loaded with an ERROR line and a `Successfully loaded network` after it — the network
  silently had the wrong `output_size` attribute while its tensors were right. Fail-closed
  is the correct behaviour; the cohort simply moved from *silently wrong* to *loudly
  refused*.
- **Two candidate fixes, and they are not alternatives:**
  - *Writer (root)*: keep `network.config` in sync on resize, or stop writing
    `config_json` from a source that can diverge from the tensors.
  - *Loader (recovery)*: prefer `arch` over `config_json` for structural dimensions when
    they disagree. **Only this one unblocks the existing archive**, because the affected
    files are already written.

---

## 5. Root cause B — snapshot writes are not atomic

### 5.1 The write is in-place

`save_network` (`snapshot_serializer.py:160`) does `h5py.File(filepath, "w")` — it opens
the **destination path** directly. There is no temp-file-then-rename anywhere in the
serializer. So a save that is interrupted *or that raises* leaves a partial `.h5` at the
final path, named exactly like a good snapshot and indistinguishable from one without
opening it.

Post-C1 the exception is correctly propagated as `SnapshotSaveError` rather than
swallowed into `False` — but **the corpse is still left behind**.

### 5.2 Every partial file in the archive is a prefix of the write sequence

`_save_network_objects_helper` (`:256`) writes in a fixed order:

```
root attrs → meta → config → arch → params → hidden_units → random → mp
```

Group sets observed in the index map onto that order exactly, with no exceptions:

| groups present | count | interrupted after |
|---|---:|---|
| *(none, no attrs, 800 B)* | 6 | before root attrs completed |
| `config, meta` | 2 | during `config`, before `arch` |
| `arch, config, hidden_units, meta, params` | 265 | **during `hidden_units`** — `random`/`mp` never reached |
| `arch, config, meta, mp, params, random` | 15,926 | complete (no hidden units → no group; `_save_hidden_units:485` returns early) |
| `arch, config, hidden_units, meta, mp, params, random` | 11,704 | complete |
| `arch, config, hidden_units, history, meta, mp, params, random` | 4 | complete + training history |
| `arch, config, meta, mp, params, provenance, random` | 1 | complete + D-C provenance |

**273 files (6 + 2 + 265) are truncated writes.** That is a single root cause, not three.

### 5.3 The 265 are real data loss

`_save_hidden_units` (`:482`) writes `num_units` **before** the unit loop:

```python
hidden_group = hdf5_file.create_group("hidden_units")
hidden_group.attrs["num_units"] = len(network.hidden_units)
for i, unit in enumerate(network.hidden_units):
    ...
```

so the declared count survives an interruption while the units themselves do not. Across
all 265, three independent records agree on the true unit count and the serialized groups
fall short:

| `arch.num_hidden_units` | `hidden_units.num_units` | unit groups written | implied by output-weight rows | files |
|---:|---:|---:|---:|---:|
| 10 | 10 | **1** | 10 | 174 |
| 5 | 5 | **1** | 5 | 48 |
| 50 | 50 | **1** | 50 | 22 |
| 20 | 20 | **1** | 20 | 19 |
| 260 | 260 | **185** | 260 | 1 |
| 147 | 147 | **38** | 147 | 1 |

The output layer is sized for the full unit count in every row
(`weights.shape[0] - input_size` matches), so the units genuinely existed. Their weight
vectors are simply not in the file. **This is irrecoverable** — unlike §4, nothing in the
snapshot can reconstruct them.

Cohort: all `juniper_version` **0.3.2**, created **2026-03-31 → 2026-04-06** — the same
window as the handoff's §4.4 volume event. The varying stop point (1, but also 185 and
38) argues for an external interruption (kill / OOM / disk) rather than a deterministic
bug at unit index 1; the *structural* conclusion does not depend on which it was.

### 5.4 What this implies

- **Fix is one change**: write to a sibling temp file and `os.replace` on success, so a
  failed save leaves no artifact. This is a live defect — it will keep producing partial
  files.
- **The 265 are the strongest retention-deletion candidates in the archive** (§6.4): they
  are unloadable, unrecoverable, and their loss is already established. That is the
  owner's call, not this document's.
- **`allow_invalid=True` does not reach them.** `load_network` returns at the format gate
  (`:986`) before `_create_network_from_file`, and `allow_invalid` is only consulted at
  `_check_integrity` afterwards. So the D-E forensic hatch covers §4's cohort but **not**
  §5's — worth knowing before the forensics-tooling design
  ([`…SNAPSHOT-FORENSICS-TOOLING-DESIGN.md`](JUNIPER_2026-08-21_JUNIPER-CASCOR_SNAPSHOT-FORENSICS-TOOLING-DESIGN.md))
  is implemented against it.

---

## 6. Root cause C — the loader has no tolerance for config schema drift

14 files fail with the generic `snapshot could not be deserialized into a network`. They
are **structurally complete** — all six groups present — and the real reason is only
visible in the log:

```
Could not create network from file: CascadeCorrelationConfig.__init__()
got an unexpected keyword argument 'optimizer_config'
```

`_create_network_from_file` (`snapshot_serializer.py:1613`) rebuilds the config with
`CascadeCorrelationConfig(**config_dict)` after popping a **hard-coded denylist** of five
runtime-only keys (`activation_functions_dict`, `log_config`, `logger`,
`candidates_per_layer`, `layer_selection_strategy`). `optimizer_config` is not on it: it
was a real config field in cascor 0.3.2 (these files are 2025-10-18 → 2025-10-21) and has
since been removed from the dataclass, which now accepts 56 kwargs.

So the load fails on strict keyword matching. **The snapshot is fine; the loader cannot
express "this file predates a field I dropped".**

> ⚠ A tempting wrong reading, checked and discarded: all 14 also carry
> `activation_function_name = 'Tanh()'` — parenthesised, unlike the archive's usual
> `'Tanh'` — which looks like an obvious stringification bug. It is not the cause. **126
> files carry the parenthesised name and 112 of them load fine.** The correlation is real
> and the causation is not; only running the loader and reading the exception separated
> them.

**Why this one matters most for the future.** A and B are historical: A stopped when the
resize path stopped being exercised, B when the writes stopped being interrupted. C is a
**time bomb** — every future removal of a config field retroactively bricks whichever slice
of the archive still carries it, silently, with a message that names nothing. The denylist
must be extended by hand for each removal, and nothing prompts anyone to do so.

Fix: filter `config_dict` to the dataclass's actual fields (an allowlist derived from
`inspect.signature`) and log the dropped keys, instead of popping a fixed five.

---

## 7. Smaller findings

### 7.1 `meta.current_epoch` is inert — reconfirmed at full-archive scale

`current_epoch == 0` for **all 27,908**; `snapshot_counter == 0`; `best_value_loss ==
inf`. Confirmed here independently of the handoff. `arch.num_hidden_units` reaches 260,
and the archive's summed lower bound is **78,798 completed cascor iterations**. Reading
the epoch counter as progress says "nothing here was ever trained" — the false reading
that would have justified deleting 27,005 real models.

### 7.2 `Invalid format: None` names nothing

`_validate_format_detail:1847` renders `f"Invalid format: {format_name}"`, and
`format_name` is `None` when the `format` attribute is **absent** rather than wrong. D-B's
stated goal was to make the format rejection name the specific failure; this arm conflates
*missing attribute* with *invalid value*, which is exactly the distinction an operator
root-causing a partial write needs. One-line fix.

### 7.3 cascor logs every load to stdout, and `logging.disable` does not hold

Two INFO lines per `load_network`, on **stdout** — ~119k lines over a full pass, into the
same stream as `--json`. `logging.disable(logging.CRITICAL)` suppresses the first few
files and then **silently stops working**, because each load constructs a network whose
`Logger.__init__` re-runs `dictConfig` and resets the global disable. `redirect_stdout`
also fails, because a `StreamHandler` built earlier holds the original stream object. The
classifier muffles **file descriptor 1** for the duration of the load loop, which nothing
in the logging layer can escape. Worth fixing in cascor: a library should not log INFO to
stdout on every load.

### 7.4 `tests/test_snapshot_index.py` silently skips 7 tests under direct execution

`DatasetJoinTest` is defined **after** the `if __name__ == "__main__": unittest.main()`
guard, so `python tests/test_snapshot_index.py` runs 20 tests and
`python -m unittest tests/test_snapshot_index.py` runs 27. CLAUDE.md documents the
`-m unittest` form, so CI is unaffected — but a green 20-test run reads as a full pass.
Vacuous-pass class; fix is to move the guard to the end of the file.

---

## 8. What this does and does not settle

**Settled:**

- Handoff item 1 (classifier) — shipped, and the §3.1 shortcut it was specified against
  is corrected.
- The root cause of **all 526** "fails to load" snapshots (§3.4's ask), with nothing
  unaccounted for.
- That A's 239 and C's 14 must not be deleted — they are recoverable — and that B's 265
  are the only files in the archive with established, irrecoverable loss.
- The full-archive iteration lower bound: **78,798** completed cascor iterations.

**Not settled, and deliberately not started:**

- **Item 2, the inference pass.** The owner's design (score every 2-in/2-out cascor
  dataset, pick the largest above-chance margin) is sound and unblocked by this work, but
  needs the dataset roster enumerated first.
- **Item 3, the training probe.** The expensive step. `--stage train` refuses rather than
  reporting categories 2 and 3 as zero, and refuses again unless
  `JUNIPER_CASCOR_SNAPSHOTS_DIR` points somewhere other than the real archive — because
  `train_output_layer` calls `create_snapshot()` unconditionally and would grow the corpus
  under study.
- **Items 4–6** (backfill, retention, the inert-metadata writer fix).

**Owner decisions this work newly requires:**

1. Ratify or overturn the two-axis reading of §2.4 (§2).
2. Whether the §4 loader-side recovery ships — it is the only thing that makes A's 239
   files (0.86% of the archive) loadable again, and it is the only fix that reaches
   snapshots already written.
3. Whether §5's established data loss changes B's 265 files' retention standing (§6.4).
4. **Priority of the §6 fix.** A and B are historical; C is the only root cause still
   accruing, and it does so silently at every config-schema change. It is also the
   cheapest of the three to fix.

---

## 9. Reproduction

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper
conda activate JuniperCascor1        # REQUIRED — unsuffixed JuniperCascor has broken torch

# index stage — ~1s, no cascor needed
python "$JUNIPER/juniper-ml/util/snapshot_classify.py" --stats

# load stage — ~14 min over 27,908 files; --write persists the sidecar
python "$JUNIPER/juniper-ml/util/snapshot_classify.py" --stage load --sample 300 --stats
python "$JUNIPER/juniper-ml/util/snapshot_classify.py" --stage load --write --stats

# the §4 recoverability probe
python "$JUNIPER/juniper-ml/util/ad-hoc/2026-08-22_arch_mismatch_recoverability_probe.py"

# regression suite
python -m unittest -v "$JUNIPER/juniper-ml/tests/test_snapshot_classify.py"
```

Sidecar: `<snapshot root>/snapshots_classification.jsonl`, one row per snapshot,
**replace-not-append** (a deeper stage revises a verdict; two rows for one path would make
the newest answer a matter of file order). Gitignored by `/cascor-snapshots/*`.

---

## 10. Provenance

- Classifier + suite: this change.
- Index it reads: `util/snapshot_index.py` (§6.2, juniper-ml#1238 / #1244).
- Taxonomy it speaks: `snapshots/snapshot_load_status.py` (D-B, juniper-cascor#542).
- Gates that produce §4's refusals: D-E (juniper-cascor#551, #553).
- Cohort it classifies: [`…S2-COHORT-CHARACTERISATION`](JUNIPER_2026-08-22_JUNIPER-CASCOR_S2-COHORT-CHARACTERISATION.md) (juniper-ml#1247).
- Parent design: [`…SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md) §6.
