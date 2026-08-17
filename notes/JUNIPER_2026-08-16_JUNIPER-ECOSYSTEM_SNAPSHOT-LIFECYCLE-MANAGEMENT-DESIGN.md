# Snapshot Lifecycle Management — design of record (F-P1-4)

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-16

**Status**: DESIGN — not implemented. No files were deleted, moved, or modified in producing
this document; every number below comes from a read-only census.

Supersedes the disposal framing of **F-P1-4** ("snapshot `.h5` debris — owner's to keep or
delete"). Per the owner (2026-08-16), snapshots get *"a planned, systems based solution … designed,
validated, and documented iaw standard juniper operating procedures"*, and **"ad-hoc, overly
aggressive, or one-off cleanup sweeps should not be performed."**

**The census vindicates that instruction, and inverts the finding.** The archive is not debris:
**27,863 of 27,869 snapshots are structurally valid and load through cascor's own deserializer**.
A sweep sized to "reclaim 1.8 GB" would have destroyed ~27.8k replayable models to recover less
disk than a single container image.

The real problems are not disk. They are **three silent-failure defects** (§4) and **the absence of
provenance** (§5) — and they bite precisely the four use cases the owner named.

---

## 1. Design requirements (owner-stated)

Snapshotting exists to allow historical models and training runs to be loaded for:

| # | Use case | What it demands of the system |
|---|---|---|
| **R1** | **Replay** | A stored model loads and reproduces its recorded behaviour. |
| **R2** | **Further experimentation** | A stored model can be *found* by what it is (dataset, params, run), then branched from. |
| **R3** | **Training pauses** | Training resumes from a snapshot **with optimizer state intact** — otherwise it is a restart, not a resume. |
| **R4** | **System crashes** | An unattended run leaves a recoverable, identifiable point. |

R1 and R4 are largely met today. **R3 is broken** (§4.1). **R2 is unreachable** (§5) — nothing
records which run or dataset a snapshot came from.

---

## 2. Measured current state

Read-only census of `juniper-cascor/src/cascor_snapshots/`, 2026-08-16, using `h5py` for structure
and cascor's own `CascadeHDF5Serializer.verify_saved_network` for validity.

```text
total files            27,869        total bytes   1.74 GiB
structurally loadable  27,863        empty stubs        6
format                 juniper.cascor v2  (100% of loadable)
```

Stamped writer version, and filename-date cohorts:

| `juniper_version` | files | | filename year-month | files |
|---|---|---|---|---|
| 0.3.2 | 27,095 | | 2025-10 | 47 |
| 0.4.0 | 520 | | 2026-02 | 84 |
| 0.5.0 | 181 | | 2026-03 | **13,498** |
| 0.6.0 | 64 | | 2026-04 | **13,507** |
| 0.9.0 | 3 | | 2026-05 | 501 |
| | | | 2026-06 | 5 |
| | | | 2026-07 | 160 |
| | | | 2026-08 | 67 |

**96.9% of the archive was written in March–April 2026** (27,005 files, ~1.65 GiB) by cascor 0.3.2.

### 2.1 Validity is measured, not assumed

A **stratified sample of 89 files**, up to 12 per filename year-month, seed-fixed, run through
`verify_saved_network`:

```text
valid: 88     invalid: 1  (a degenerate empty file — one of the 6 stubs)
```

Every cohort verifies, **including the 0.3.2 files six minor versions behind current**. Group shape
is `arch|config|meta|mp|params|random`, with `hidden_units` additionally present when the network
grew any (its absence in a 0-unit network is correct, not damage).

> **Method note, recorded because it nearly produced a false headline.** The first probe used the
> *single oldest* file as the 0.3.2 representative. That file is an Oct-2025 husk holding only
> `config` + `meta`, it fails verification, and `load_network` returns `None` for it. Generalising
> from it would have declared 97% of the archive dead and made an aggressive sweep look justified —
> the exact outcome the owner's instruction guards against. **One file is not a cohort.** The
> stratified sample is the load-bearing evidence; the husk is a real but rare artifact (6 of 27,869).

### 2.2 `mtime` is not creation time

Filenames embed dates from **2025-10** onward, but no file has an `mtime` earlier than **2026-02** —
a copy or restore reset them all. The authoritative creation timestamp is the **`created` root
attribute** (ISO-8601, written by the serializer), corroborated by the filename.

**Consequence, binding on any future policy: retention must never key on `mtime`.** A naive
`find -mtime +N` would misjudge the age of the entire archive.

---

## 3. Where snapshots live today

| tier | directory | resolution | naming |
|---|---|---|---|
| direct CLI | `src/cascor_snapshots/` | `constants_hdf5.py:46-57`, `JUNIPER_CASCOR_SNAPSHOTS_DIR` at **import** time (W-6) | `cascor_snapshot_<YYYYMMDD>_<HHMMSS>_<uuid4>.h5` |
| service | `src/snapshots/` | `manager.py:4403` `_get_snapshots_dir`, same env var at **call** time (W-6) | `snapshot_<ISO8601>Z.h5` |

Two directories, **two incompatible naming schemes**, and one audit log —
`src/snapshots/snapshot_history.jsonl` (14 entries: `restore` / `replay` actions with
`snapshot_id`, path, mode) — which covers **only the service tier**. The 27,869 CLI snapshots have
no audit trail at all.

### 3.1 The service snapshot directory is a Python package

`src/snapshots/` contains `.h5` artifacts **interleaved with the serializer's own source**:
`snapshot_serializer.py`, `snapshot_cli.py`, `snapshot_common.py`, `snapshot_errors.py`,
`snapshot_utils.py`, `__init__.py`, `README.md`.

This is not hypothetical risk. On **2026-08-09** a concurrent session's `.h5` cleanup in this tree
**swept 5 snapshot modules**, breaking every cascor boot with `ModuleNotFoundError` until healed as
**cascor#501**. Mixing mutable artifacts into an importable package is the direct cause, and it is
the single strongest argument for the owner's "no ad-hoc sweeps" rule: *in this directory a glob is
a code-deletion tool.*

### 3.2 W-6 is a per-run redirect, not a policy

`JUNIPER_CASCOR_SNAPSHOTS_DIR` redirects **only when exported**. `experiment_stack.bash` exports it,
so launcher-run experiments write to `RUN_DIR/snapshots/` — but any direct `python src/main.py`
invocation still writes into the checkout. **Accrual is live**: the archive grew by 2 files during
this census, from a concurrent session's direct-CLI campaign.

---

## 4. Defects found (all silent; all block a stated requirement)

### 4.1 D-A — optimizer state is discarded on every load (blocks R3)

`snapshot_serializer.py:1022-1027`:

```python
if "optimizer" in output_group:
    opt_group = output_group["optimizer"]
    try:
        self._load_optimizer_state_from_hdf5_helper(opt_group, network)
    except Exception as e:
        self.logger.warning(f"CascadeHDF5Serializer: Could not restore optimizer: {e}")
        network.output_optimizer = None
```

Measured on one snapshot per stamped version — **0.3.2, 0.4.0, 0.5.0, 0.6.0 and current 0.9.0 all
raise**:

```text
Could not restore optimizer: '<=' not supported between instances of 'float' and 'numpy.bytes_'
```

A `float` is being compared against a `numpy.bytes_` — an HDF5 string attribute read back without
decoding. The handler catches it, logs at **WARNING**, sets `output_optimizer = None`, and the load
reports success.

**Impact.** "Resume a paused training run" (**R3**) silently degrades to "reinitialise the optimizer
and continue", on the current version. The caller is told the load succeeded. This is a correctness
defect, not a cleanliness one, and it is **the most important thing this census found.**

### 4.2 D-B — `load_network` returns `None` instead of raising

`load_network` (`:861`) has four `return None` paths — missing file, `_validate_format` failure,
and others — plus a catch-all returning `None` via `_log_exception_stacktrace`. **No failure
raises.**

A caller cannot distinguish *"no snapshot"* from *"corrupt snapshot"* from *"loaded"*. The Oct-2025
husk demonstrates it: `verify_saved_network` reports `{'valid': False, 'error': 'Invalid format'}`
while `load_network` yields a bare `None`. Any recovery path (**R4**) built on the return value alone
will mistake corruption for absence.

Note also that `'Invalid format'` is a **misleading message**: the file's `format` *is*
`juniper.cascor` v2. What is missing is the model payload (`arch` / `params`). The verifier should
say which required group is absent.

### 4.3 D-C — snapshots carry no run provenance (blocks R2)

`meta` records `network_uuid`, `created`, `python_version`, `torch_version`, `serializer_version`,
`juniper_version`, and `arch`/`config` hold the model shape and hyperparameters. **Nothing records
the run.** There is no `run_id`, no `experiment`, no `dataset_id`, no config hash.

So "load the model from the E-I cap-128 cell and branch from it" (**R2**) cannot be answered from
the archive at all — not by filename (timestamp + uuid4), not by content. With 27,869 files the
practical answer today is *"you can't find it"*.

This is also why a retention policy **cannot responsibly be written yet**: with no provenance there
is no principled way to say which snapshots are keepable history and which are disposable
intermediates. **Identity must precede retention.** Any policy authored before §6.1 lands would be
guessing, and guessing at deletion is exactly the failure mode being avoided.

---

## 5. Gap analysis

| Req | Status | Blocking gap |
|---|---|---|
| R1 replay | **Largely met** | 88/89 sampled verify; cross-version loads work back to 0.3.2. Caveat: D-B hides the failures that do occur. |
| R2 further experimentation | **Not met** | D-C: no provenance, no index, no query path. |
| R3 training pauses | **Broken** | D-A: optimizer silently dropped on every load. |
| R4 crash recovery | **Partially met** | Snapshots exist and load, but D-B makes "corrupt" indistinguishable from "absent", and the CLI tier has no audit trail. |

---

## 6. Proposed design

Ordered so that each phase is independently useful and **no phase deletes anything until the phase
that can identify what it is deleting has landed**.

### 6.1 Phase 1 — Identity (prerequisite for everything else)

**Stamp provenance into the snapshot at write time.** Extend `_save_metadata`
(`snapshot_serializer.py:225`) to record, when available from the environment/manager:
`run_id`, `experiment`, `dataset_id`, `config_hash`, `git_sha`, and `tier` (`cli` | `service`).

Sources already exist: the launcher exports `RUN_ID`/experiment per run, the driver holds the
content-addressed `dataset_id`, and build-provenance already ships `git_sha` for the metrics
`build_info`. Additive HDF5 attributes — older readers ignore unknown attrs, so this is
back-compatible in both directions.

**Unify naming** on `cascor_snapshot_<ISO8601Z>_<run_id|norun>_<uuid8>.h5` for both tiers, keeping
the existing patterns readable by the index (§6.2). Do **not** rename existing files.

### 6.2 Phase 2 — Index and query (delivers R2)

A `snapshots_index.jsonl` per snapshot root, append-only, one record per snapshot: path, `created`,
tier, the §6.1 provenance, `arch` summary, verification verdict, size. Built by a **read-only
scanner** that can be re-run over the legacy archive (the metadata that exists is enough for a
useful partial record — `created`, `network_uuid`, arch, config).

Ship a query CLI in `juniper-ml/util/` alongside `list_runs.py`, which already models the
conventions: read-only by default, `--json`, and destructive actions gated behind explicit `--yes`
and never available under `--dry-run`.

This is what makes the archive an asset rather than a heap, and it is worth doing **even if no file
is ever deleted.**

### 6.3 Phase 3 — Correctness fixes (deliver R3, harden R4)

| id | fix | repo |
|---|---|---|
| **D-A** | Decode HDF5 string attrs before comparison in `_load_optimizer_state_from_hdf5_helper`; add a round-trip test asserting optimizer state **survives** save→load. Downgrade-to-`None` must become a loud, explicit outcome, never a silent WARNING on the success path. | juniper-cascor |
| **D-B** | Give `load_network` a raising variant (or a typed result) so *absent*, *corrupt*, and *loaded* are distinguishable; keep the `None` form for back-compat callers. Fix `'Invalid format'` to name the missing group. | juniper-cascor |
| **3.1** | Move the service snapshot root out of the importable package (`src/snapshots/` → a data dir), so no cleanup can ever again delete modules (cascor#501). | juniper-cascor |

D-A is the highest-value item in this document and is independently shippable — it needs none of
Phase 1 or 2.

### 6.4 Phase 4 — Retention policy (only after 1–3)

Written **as a proposal for owner ratification**, not applied. Expected shape:

- **Never auto-delete.** Tooling proposes; a human ratifies; every action is logged to the index.
- Classify by provenance: *named/pinned* (referenced by an evidence note, a suite registry, or an
  explicit keep-mark) → **keep indefinitely**; *run-attributed intermediates* → age out by policy;
  *unattributable legacy* → **quarantine, never delete** (move to a cold archive, reversibly).
- Key on the internal `created` attribute, **never `mtime`** (§2.2).
- Deletion tooling must refuse to operate on a directory containing `.py` files (§3.1), refuse
  outside a configured snapshot root, and be `--dry-run` by default with `--yes` required —
  the `generated_prompt_index.py` / `list_runs.py` safety contract this repo already uses.

### 6.5 Explicit non-goals

- **No sweep, of any size, at any phase of this design.** The 1.74 GiB is not a problem worth risk.
- No rewriting or migrating existing snapshot files.
- No change to the on-disk HDF5 *format version* (Phase 1 is additive attributes only).

---

## 7. Validation plan

Per standard Juniper practice, each phase ships with its own gate:

| phase | validation |
|---|---|
| 6.1 identity | Unit: provenance attrs round-trip save→load. Drift: a snapshot written by the launcher carries the run's `RUN_ID` (asserted in `tests/test_experiment_stack_script.py`'s live arm). |
| 6.2 index | Behavioural tests over a synthetic snapshot tree (hermetic, mirroring `test_list_runs.py`): classification, `--json` shape, and that destructive flags do nothing without `--yes`. Plus a real read-only scan of the 27,869-file archive as a smoke. |
| 6.3 fixes | **D-A: a regression test that fails on today's code** — assert `output_optimizer is not None` and its state matches after save→load. D-B: assert distinct outcomes for absent / corrupt / valid. |
| 6.4 retention | Dry-run over the real archive must propose **zero** deletions of anything provenance-linked; a planted unattributable fixture must be proposed for *quarantine*, not deletion. |

The census is reproducible and preserved as
[`util/ad-hoc/2026-08-16_snapshot_archive_census.py`](../util/ad-hoc/2026-08-16_snapshot_archive_census.py)
(`--census` for §2's structural figures, `--sample` for §2.1's stratified verification; seed-fixed,
read-only, and deliberately carrying **no delete path**). It reproduces every number in §2 and §2.1
exactly. It lives in `util/ad-hoc/` rather than a scratch dir per the repo's script-placement rule —
the rule exists because scripts of exactly this kind were lost once before.

---

## 8. Sequencing and dependencies

```text
6.3 D-A (optimizer)  ── independent, highest value ──> ship first
6.3 D-B (load API)   ── independent
6.3 3.1 (move dir)   ── independent; closes the cascor#501 class
6.1 identity ───────> 6.2 index ───────> 6.4 retention proposal
```

Phase 6.3's three items are unblocked today. Phases 6.1→6.2→6.4 are strictly ordered: **retention
last, and only once the archive can say what each file is.**

Relative priority against the program's other open work is set in the companion prioritisation
note, not here.

---

## 9. Open questions for the owner

| # | Question | Why it needs a decision |
|---|---|---|
| **S-1** | Should snapshots move out of the repo checkout entirely (e.g. under `~/.local/state/juniper-snapshots/`, mirroring the experiment `RUN_DIR` convention)? | Would make §3.1 structural rather than a fix, and stop checkout accrual permanently. Larger blast radius: changes default paths for both tiers. |
| **S-2** | Is the March–April 2026 cohort (27,005 files, 96.9%) of retained research value, or is it a known bulk artifact of one campaign? | Decides whether Phase 6.4 needs a real policy or whether that cohort can be quarantined wholesale once identified. **Not actionable until §6.2 can characterise it.** |
| **S-3** | Should the service tier's `snapshot_history.jsonl` audit log be extended to the CLI tier, or replaced by the §6.2 index? | Two mechanisms or one. |
| **S-4** | Retention horizon and cold-archive location, once §6.2 exists. | The only genuinely policy-shaped question, deliberately deferred to last. |

---

## 10. Relationship to F-P1-4 as previously recorded

The P1 smoke note's F-P1-4 row says *"the smoke left **4** snapshot `.h5` files … Files left in
place for the owner"*, with the remedy *"**W-6** … redirects these into `RUN_DIR/snapshots/`"*.

Both halves need updating and are updated in that note: the count is **27,869**, and W-6 redirects
only when its env var is exported, so the direct-CLI path still accrues into the checkout. The
finding's disposition changes from *"keep or delete"* to *this design*.
