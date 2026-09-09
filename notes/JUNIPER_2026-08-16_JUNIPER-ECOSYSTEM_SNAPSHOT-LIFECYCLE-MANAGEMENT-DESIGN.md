# Snapshot Lifecycle Management — design of record (F-P1-4)

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-23

**Status**: **COMPLETE.** Phases 6.1 (identity), 6.2 (index) and 6.3 (fixes) have shipped;
**Phase 6.4 (retention) was ratified by the owner on 2026-08-23 as a no-deletion policy**
(§6.4.3). No files were deleted, moved, or modified in producing this document, and under the
ratified policy none ever will be — every number below still comes from a read-only census.

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

| #      | Use case                    | What it demands of the system                                                                               |
|--------|-----------------------------|-------------------------------------------------------------------------------------------------------------|
| **R1** | **Replay**                  | A stored model loads and reproduces its recorded behaviour.                                                 |
| **R2** | **Further experimentation** | A stored model can be *found* by what it is (dataset, params, run), then branched from.                     |
| **R3** | **Training pauses**         | Training resumes from a snapshot **with optimizer state intact** — otherwise it is a restart, not a resume. |
| **R4** | **System crashes**          | An unattended run leaves a recoverable, identifiable point.                                                 |

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

| `juniper_version` | files  |  | filename year-month | files      |
|-------------------|--------|--|---------------------|------------|
| 0.3.2             | 27,095 |  | 2025-10             | 47         |
| 0.4.0             | 520    |  | 2026-02             | 84         |
| 0.5.0             | 181    |  | 2026-03             | **13,498** |
| 0.6.0             | 64     |  | 2026-04             | **13,507** |
| 0.9.0             | 3      |  | 2026-05             | 501        |
|                   |        |  | 2026-06             | 5          |
|                   |        |  | 2026-07             | 160        |
|                   |        |  | 2026-08             | 67         |

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

| tier       | directory               | resolution                                                                         | naming                                           |
|------------|-------------------------|------------------------------------------------------------------------------------|--------------------------------------------------|
| direct CLI | `src/cascor_snapshots/` | `constants_hdf5.py:46-57`, `JUNIPER_CASCOR_SNAPSHOTS_DIR` at **import** time (W-6) | `cascor_snapshot_<YYYYMMDD>_<HHMMSS>_<uuid4>.h5` |
| service    | `src/snapshots/`        | `manager.py:4403` `_get_snapshots_dir`, same env var at **call** time (W-6)        | `snapshot_<ISO8601>Z.h5`                         |

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

> **Correction (2026-08-17) — the impact paragraph above is WRONG, and D-A is NOT Tier 1.** The
> defect mechanism is real and reproduces exactly as described. **Its consequence does not.** Before
> implementing the fix, the consumer side was traced, and it does not support the claim:
>
> - **`output_optimizer` has exactly ONE production consumer**: `cascade_correlation.py:2063`,
>   `self.output_optimizer = self._create_optimizer(output_layer.parameters())`. That line **assigns**
>   it. There is **no production read** of a previously-restored optimizer anywhere in the tree — every
>   other reference is in `tests/`.
> - The recreation is **deliberate and documented** at `cascade_correlation.py:2050-2053`: *"In Cascade
>   Correlation, the output layer's parameter space changes each time a hidden unit is added
>   (input_size grows), so the previous nn.Linear and optimizer state are **invalid**. Rebuilding from
>   the current output_weights ensures the optimizer tracks the correct parameter tensors."* `:2062`
>   calls it "Create or **recreate** … (see INTENTIONAL note above)".
> - The deserializer additionally builds its optimizer over a **throwaway** `torch.nn.Linear`, and
>   **`load_state_dict` is called nowhere in the snapshot module** — the saved `state_dict` is parsed
>   and only logged. So even with the type error fixed, no optimizer state would be restored.
>
> **Therefore:** a restored optimizer is never read, and is overwritten on the next
> `train_output_layer` call. Fixing the type error changes **nothing observable in training** — it
> removes a WARNING. That makes D-A **log hygiene with a latent trap**, not a correctness defect, and
> it is **not** "the most important thing this census found".
>
> **R3 is not deliverable by a serializer fix at all.** In Cascade Correlation the output parameter
> space changes on every unit insertion, so prior Adam moments are invalid *by construction*. If
> resume-with-optimizer-state is genuinely wanted it is a **training-loop design question** — and the
> code's own comment argues it is not meaningful. **R3 should be re-examined as a requirement**, not
> scheduled as a bug fix. Raised as **S-5** (§9).
>
> **The fix still has value, at low priority, and must be done carefully:** the asymmetry is that
> `learning_rate` is *written* with `write_str_attr` (`:449`, stringifying via `np.bytes_`) but *read*
> with a raw `opt_group.attrs.get` (`:1037`) instead of the `read_str_attr` counterpart used for
> `optimizer_type` one line above. Coercing on read fixes every existing and future snapshot with no
> format change. **But fixing it silences the only signal that this path is inert** — so the fix must
> land together with a comment (and ideally a test) recording *why* optimizer restore does nothing,
> or the next investigator will "restore" it believing it matters.
>
> **Method note.** This is the second time in this arc that a correct mechanism produced a wrong
> consequence: the first was generalising from one snapshot file (§2.1). **Tracing the consumer is
> part of establishing impact** — "this code is wrong" and "this wrongness matters" are separate
> claims requiring separate evidence.

> **RETRACTION (2026-08-17, later same day) — the correction immediately above is ITSELF wrong.
> D-A is a DATA-DESTRUCTION defect and is the top item.** Independent friendly and adversarial
> reviews were run over the "inert" conclusion; both refuted it, on evidence neither the original
> analysis nor the correction had. What follows supersedes both.
>
> **1. The "one production consumer" premise is false.** `output_optimizer` has three to four
> production sites. The decisive one is `api/lifecycle/manager.py:4127`, `_zero_optimizer_state_for`,
> which **reads** it — called from `PATCH /v1/network/weights` (`:4080`, `:4091`), FSM-gated to
> `Investigating`. That is a manual weight-edit endpoint, not the training loop. `manager.py:4259`
> and `:4344` also null it after topology surgery.
>
> **2. The restore path never trains, and says so in its own docstring.** `manager.py:4551-4554`:
> *"The FSM transitions to `INVESTIGATING` so the user can edit meta-params, replace the dataset, and
> re-snapshot, **but cannot start training directly.** To enter a training state, the user must
> invoke `restore_for_retrain` … or `resume_from_snapshot`."* Restore / retrain / resume are
> deliberately distinct verbs. The recreation at `cascade_correlation.py:2063` happens on the
> **training** verbs — so on the restore path **nothing overwrites the restored optimizer**. The
> "inert" argument assumed a verb the user did not invoke.
>
> **3. A load → save cycle SILENTLY DESTROYS optimizer state.** The save guard at `:430` is
> `if hasattr(...) and network.output_optimizer is not None:`. Load sets it to `None` (`:1028`).
> So re-saving a loaded network writes **no optimizer group at all**, and unlike the load side the
> save side emits **no warning whatsoever**. The documented "restore → edit → re-snapshot" workflow
> therefore strips momentum and step counters permanently. Reproduced end-to-end. **This is data
> loss, not log hygiene, and it alone defeats the inert conclusion.**
>
> **4. The largest fidelity loss is optimizer IDENTITY, not momentum.** `optimizer_type` is **not**
> persisted in the snapshot's `config` group — `OptimizerConfig` falls through `_config_to_dict`'s
> skip-complex-types branch (`:1673`), and `_load_config_to_network` does not restore it. The
> corrupted optimizer group is the **only** record of which optimizer was used. So after restoring
> one of the **97 real SGD snapshots**, `GET` training params returns a fabricated **`"Adam"`**
> (`_read_optimizer_type`, `manager.py:42-48`, feeding `get_training_params` at `:3555`) — a
> metaparameter the API reports confidently and wrongly.
>
> **Scale:** of 27,878 snapshots, **~27,500 carry an optimizer group and 100% of those store
> `learning_rate` as `np.bytes_`.** This fires on essentially the whole corpus.
>
> **THE FIX IS DANGEROUS IF DONE NAIVELY — both reviews flagged the same trap independently.**
> Decoding the attribute and calling `load_state_dict` on the parsed JSON **does not raise**. It is
> accepted, but `state` is keyed by the strings `'0'` / `'1'`, which match no `Parameter`, so
> training silently restarts from a fresh optimizer while every observer reports "restored" — and
> **both existing test suites pass in either state**. A type mismatch is worse: SGD state into Adam
> raises immediately; Adam state into SGD raises **deferred, mid-training**, at `.step()`.
>
> **Contract the fix must meet.** After `load_network`, `output_optimizer` is a live optimizer **of
> the class recorded at save time**, whose `state_dict()` is structurally equal to the persisted one
> (same `param_groups` hyperparameters modulo tuple/list, same per-param state keys, buffers
> elementwise equal), built over parameters shaped as the output layer was at save time. A snapshot
> with no optimizer restores `None`. A restore that cannot honour the contract **warns and degrades
> to `None`** — it must not raise, or the ~97 SGD loads that succeed today would start failing.
>
> This is a **state-fidelity** contract, not a promise of trajectory reproduction: `train_output_layer`
> genuinely does rebuild the optimizer on growth, so older claims of "resume training exactly where it
> left off" (`notes/history/P1_FIXES_COMPLETE.md:219-222`) remain over-claims and must not be repeated.
>
> **Why it survived:** `tests/unit/test_p1_fixes.py:96` asserts `hasattr(loaded_network,
> "output_optimizer")` — **true when the value is `None`** — then prints
> `"✅ PASS: Optimizer saved and restored successfully"`. Feasibility is **proven**: real Adam and SGD
> snapshots were reconstructed from disk, and the float32 JSON round-trip is exactly lossless.
>
> **Method note, third occurrence.** The first error generalised from one file; the second traced
> consumers but stopped at the training path and never read the restore path's own docstring.
> **"I checked the consumers" is not the same as "I checked all the consumers."**
>
> **SHIPPED 2026-08-18 — juniper-cascor `main` `cb8a30e` (fix commit `5f15a45`, +228/-19).**
> All five cascor main workflows green (Post-Merge Main Verification, Golden Regression,
> Conformance, CodeQL, CI/CD Pipeline). What landed:
>
> - `_coerce_optimizer_lr` — accepts bytes / str / numpy scalar / float, so the historical string
>   form and a plain numeric attribute both round-trip.
> - `_rehydrate_optimizer_state` — int keys and real tensors, closing the inert-restore trap.
> - `optimizer_type` honoured via `getattr(torch.optim, ...)`; an unresolvable name still falls back
>   to Adam but **skips** state loading (Adam and SGD carry different buffers).
> - `lr` preferred from `param_groups[0]["lr"]` over the attribute; the save side now records the
>   optimizer's actual lr.
> - Restore failure **warns and degrades** — it does not raise, so the ~97 SGD loads that succeeded
>   before still succeed.
> - The save guard now warns instead of silently dropping an optimizer group.
>
> **Verification.** All three new tests **fail on unpatched code and pass with the fix**; full
> `tests/unit/` exit 0; pre-commit clean; and against the real corpus a 0.3.2-era **Adam** snapshot
> restores with `step` preserved and `Parameter`-keyed state, a real **SGD** snapshot restores *as
> SGD* with `momentum_buffer` intact, and the optimizer group survives a load → save → load cycle.
>
> **The weak assertion that hid this for years is fixed**: `test_p1_fixes.py` asserted only
> `hasattr(loaded_network, "output_optimizer")` — true when the value is `None` — then printed a
> success banner. It now asserts `is not None`, same class, and non-string state keys.
>
> **Extra evidence for §3.1 found while landing it:** `.gitignore` carries **nine** overlapping rules
> blanket-ignoring `src/snapshots/`, so editing the tracked Python modules in that directory requires
> `git add -f`. That is the artifact/source coupling §3.1 proposes to remove, showing up as day-to-day
> friction on top of the cascor#501 deletion risk.

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

> **Update (2026-08-17) — D-B is CONFIRMED reachable in production, is worse than stated, and is now
> the top item.** The same consumer-tracing that demoted D-A (§4.1) strengthened this one. The
> conflation is not merely possible for a hypothetical caller; it is **implemented and user-facing**:
>
> - `POST /v1/snapshots/{id}/restore` (`api/routes/snapshots.py:213`) calls
>   `lifecycle.load_snapshot(...)` and does
>   `if not result["loaded"]: raise HTTPException(status_code=404, detail=f"Snapshot '{snapshot_id}' not found or failed to load")`.
> - The manager agrees, verbatim: `manager.py:4573` returns
>   `reason="snapshot not found or failed to load"`.
>
> So **a corrupt snapshot is reported to the API client as `404 Not Found`** — the two conditions are
> fused in the status code *and* in the message text. An operator recovering from a crash (**R4**)
> cannot tell "this snapshot never existed" from "this snapshot is damaged", which are opposite
> situations: one means pick another snapshot, the other means investigate data loss.
>
> The same routes carry the other stated requirements — `resume_snapshot` (`:317`, **R3**),
> `start_replay_endpoint` (`:379`, **R1**), `retrain_from_snapshot` (`:266`) — so the fused failure
> mode sits under every snapshot-consuming operation, not just restore.
>
> **Corrected priority: D-B is Tier 1, ahead of D-A.** It is a real, reachable, user-visible defect,
> whereas D-A is inert (§4.1). A minimal fix distinguishes *absent* (→ 404) from *corrupt/unreadable*
> (→ 422 or 500 with the verifier's reason), leaving the `None`-returning form for back-compat.
>
> ~~Note `load_network` itself has **no production callers** — the live path is
> `lifecycle._load_snapshot_to_network`. Any fix must be applied where the service actually loads,
> not only to `load_network`, or it will change nothing. *(That is the same trap D-A fell into.)*~~
>
> ⛔ **RETRACTED — this paragraph is FALSE. Do not act on it.** `load_network` is the live loader
> and is the only place that can separate *absent* from *corrupt*. See the correction immediately
> below.

> **CORRECTION (2026-08-19) — the "no production callers" claim above is FALSE, and inverted.**
> Caught by an independent validator while checking the successor handoff. `load_network`
> (`snapshot_serializer.py:877`) **is** the live loader:
>
> - `_load_snapshot_to_network` (`manager.py:4561`) — the function this document names as "the
>   live path" — **calls it** at `manager.py:4580`: `network = serializer.load_network(matches[0])`.
> - `cascade_correlation.py:5130` calls it too, inside the public `load_from_hdf5`.
> - References are not confined to one test file either — ~16 files under `src/` reference it.
>
> So the guidance "a fix applied only to `load_network` would change nothing" is exactly
> backwards: `load_network` is where absent and corrupt both collapse to `None` (a missing-file
> return, a `_validate_format` failure, and a catch-all), and therefore **the only place that can
> separate them**. A fix belongs there, paired with error-mapping in `_load_snapshot_to_network`,
> which currently flattens every failure to `return False` (`:4575` absent / `:4583` corrupt), and
> in the four route raise sites.
>
> ⚠ **Line numbers in this block were re-derived against juniper-cascor `4bec1be`** (2026-08-20).
> juniper-cascor#539 shifted `manager.py` by ~66 lines, so the pre-#539 citations that appear
> elsewhere in this document (`:4504`, `:4523`, `:4573`) are stale by that amount.
>
> **D-B now has its own design of record**, which supersedes this section for implementation
> purposes: [`JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md`](JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md)
> (juniper-ml#1193). It carries the full taxonomy, the four wire-contract options, the blast radius,
> and the `start_replay`-returns-`bool` asymmetry that decides the size of the change.
>
> **How the error happened, because it is the more useful lesson:** the original check was a
> `grep` piped through `head -12`. The test file's matches filled the window and the two
> production callers were cut off. That is the *same* truncation mistake that hid a cross-repo
> reference earlier in this arc — the reason
> `util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash` prints full per-group counts. **Never
> truncate a reference sweep.**

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

| Req                        | Status                             | Blocking gap                                                                                                                                                                                                  |
|----------------------------|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| R1 replay                  | **Largely met**                    | 88/89 sampled verify; cross-version loads work back to 0.3.2. Caveat: D-B hides the failures that do occur.                                                                                                   |
| R2 further experimentation | **Not met**                        | D-C: no provenance, no index, no query path.                                                                                                                                                                  |
| R3 training pauses         | **MET (2026-08-20)**               | ⚠ The former "requirement itself in question" entry was based on the retracted D-A-is-inert position and is **withdrawn** — see **S-5 ANSWERED** (§9). Restore is faithful (cascor `5f15a45`); resume now *continues* the restored optimizer rather than discarding it (cascor#539). Golden-neutral. |
| R4 crash recovery          | **Partially met**                  | Snapshots exist and load, but D-B makes "corrupt" indistinguishable from "absent", and the CLI tier has no audit trail.                                                                                       |

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
| --- | --- | --- |
| **D-A** | ✅ **SHIPPED.** Restore made faithful in cascor `5f15a45`; resume follow-on (R3) in cascor#539. ⚠ The 2026-08-17 re-scope that stood here is **retracted in full** — it called D-A inert, ranked it lowest, and said "**Do not** add a state-survives save→load test". All three were wrong: that test is precisely what now guards the fix (`test_snapshot_serializer_coverage_final.py::TestOutputOptimizerStateReuse`, `test_p1_fixes.py::test_2b_optimizer_state_survives_resume`). Not gated on S-5 — S-5 was ANSWERED yes (§9). | juniper-cascor |
| **D-B** | Give `load_network` a raising variant (or a typed result) so *absent*, *corrupt*, and *loaded* are distinguishable; keep the `None` form for back-compat callers. Fix `'Invalid format'` to name the missing group. | juniper-cascor |
| **3.1** | Move the service snapshot root out of the importable package (`src/snapshots/` → a data dir), so no cleanup can ever again delete modules (cascor#501). | juniper-cascor |

D-A is the highest-value item in this document and is independently shippable — it needs none of
Phase 1 or 2.

### 6.4 Phase 4 — Retention policy (only after 1–3)

> **RATIFIED 2026-08-23.** The proposal below was put to the owner as three questions; all three
> are answered, and the answers resolve this phase to a **no-deletion policy**. The proposal text
> is retained verbatim because the ratified outcome is only legible against what was proposed.

#### 6.4.1 The proposal, as written

- **Never auto-delete.** Tooling proposes; a human ratifies; every action is logged to the index.
- Classify by provenance: *named/pinned* (referenced by an evidence note, a suite registry, or an
  explicit keep-mark) → **keep indefinitely**; *run-attributed intermediates* → age out by policy;
  *unattributable legacy* → **quarantine, never delete** (move to a cold archive, reversibly).
- Key on the internal `created` attribute, **never `mtime`** (§2.2).
- Deletion tooling must refuse to operate on a directory containing `.py` files (§3.1), refuse
  outside a configured snapshot root, and be `--dry-run` by default with `--yes` required —
  the `generated_prompt_index.py` / `list_runs.py` safety contract this repo already uses.

#### 6.4.2 The three ratification questions and their answers

| # | question | answer |
|---|---|---|
| 1 | Do cohort B's 273 truncated writes get deleted, quarantined, or kept? | **Quarantine, never delete.** |
| 2 | Does behavioural attribution count as §6.4 "named"? | **No — inference is not a keep-mark.** |
| 3 | Is a `util/juniper-backup.bash` archive a sufficient safeguard before removal? | **Not until a restore drill passes.** *(2026-08-26: pipeline half PASSES; key half still owner-gated — see below.)* |

**On (1).** Cohort B is the archive's only established, irrecoverable loss — and it is
**13.0 MB of a 1.7 GB archive, 0.75%**. There is no space argument for an irreversible action at
that scale, and the files are the only physical evidence of the non-atomic-write defect that
cascor#561 closed. They are kept as evidence, not as models.

**On (2).** §6.4's *named/pinned* definition names three mechanisms — an evidence note, a suite
registry, an explicit keep-mark. Behavioural attribution is none of them: it is statistical
inference from how a network behaves, and `util/snapshot_attribute.py`'s own output says it is
evidence rather than provenance. Anyone who wants a specific snapshot kept writes an explicit
keep-mark, which is precisely the mechanism §6.4 already provides.

**On (3).** `util/juniper-backup.bash` streams `tar` into `gpg` with two independent recipients
and carries no `--exclude`, so `cascor-snapshots/` genuinely would be captured. It is **unrelated
to the Duplicati path** whose broken restore points ml#1263 documented — that finding does not
transfer to it. But the script's own line 173 states it cannot prove the tar inside is intact,
and **no restore drill has ever been run**. An unverified backup is the exact failure class
ml#1263 already caught once: archives that exist and do not restore.

**Drill status, updated 2026-08-26.** The drill has two independent failure classes, and only
one of them is testable without the owner present:

| # | class | question | status |
|---|---|---|---|
| 1 | **PIPELINE** | Does `tar -cjf - \| gpg -e` round-trip a tree byte-for-byte, and do the script's two unattended checks actually fire? | **PASSES** (re-drilled 2026-08-28 against the corrected bzip2 pipeline) |
| 2 | **KEY** | Can the owner's YubiKey-backed private key decrypt a *real* archive? | **CLOSED 2026-08-28** |

Class 1 was drilled by [`util/ad-hoc/2026-08-26_backup_restore_drill.bash`](../util/ad-hoc/2026-08-26_backup_restore_drill.bash),
which reproduces this script's pipeline verbatim against a synthetic tree — text, incompressible
binary, an `.h5`-shaped file, unicode and spaced filenames, a symlink, and a mode-755 file — using
**throwaway** recipients in an isolated `$GNUPGHOME`, so the real keyring and the YubiKey are never
touched. It restores, then compares SHA-256 of every file plus every type/mode/symlink target. All
7 files and the full type/mode/link manifest matched. It also carries a **negative control**: a byte
flipped mid-ciphertext must make the restore fail, and it does — so an all-pass result is not
vacuous. The drill found one real defect, in its own recipient-count check, before passing:
`gpg --with-colons --list-keys` emits an `fpr` record for the primary key *and* each subkey, so a
naive `/^fpr:/` grep double-counts recipients.

**Class 2 is CLOSED as of 2026-08-28.** All 15 archives of the `snapshot-2026-02-27` backup set were
decrypted with the documented recipe (`gpg -d | tar -xjf -`) and diffed against the tree they were
built from: every one restored, matched source, and was byte-identical across both devices. The
decrypting subkeys are card-resident — `gpg --list-secret-keys --with-colons` reports YubiKey serials
`D2760001240102010006092583970000` and `D2760001240100000006249551140000` on the encryption subkeys,
with the primary secrets held offline (`#`) — so this exercised the real hardware path, not an
on-disk copy. Re-runnable: [`util/ad-hoc/2026-08-28_verify_feb_backup_set.bash`](../util/ad-hoc/2026-08-28_verify_feb_backup_set.bash).

The paragraph below is retained as the record of what was owed before that.

Class 2 cannot be closed unattended: `ENCRYPT_KEYS` names two YubiKey-backed recipients, so
decrypting a real archive requires the hardware. **What is owed is now specific** — take one real
`.tbz2.gpg`, decrypt it with a YubiKey, untar it, and confirm the tree lands — rather than the
open-ended "no drill has ever been run".

**Both preconditions recorded earlier on 2026-08-26 are now CLEARED** (they were true when first
written, hours before the multi-device revision was fixed; superseded rather than deleted so the
change is legible):

| precondition, as first recorded | status now |
|---|---|
| "No archive exists to drill" — no project `.tbz2.gpg` on this host | **cleared.** `juniper-backup.bash` now produces one on demand; several were written and verified during its repair. |
| "The destination is not mounted" — `/media/pcalnon/DFF3-2782/` does not exist | **cleared.** Both `EBC5-F0A3` (`/dev/sdf1`) and `DFF3-2782` (`/dev/sdg1`) are mounted, each with a `Juniper-8.0.0.python/` directory. |

**Class 2 no longer requires a full-tree backup, which is the useful part.** `--source` accepts any
directory, so a *seconds-long* archive of a small tree is a real `.tbz2.gpg` encrypted to the same two
YubiKey recipients as a 141 GB one — identical for the purpose of proving the key decrypts:

```bash
util/juniper-backup.bash --source <any small dir> --dest <scratch dir>   # seconds, real archive
gpg --decrypt <that>.tbz2.gpg | tar -tjf -                               # YubiKey; lists the tree
```

If that lists the tree, class 2 is closed and question 3 is fully answered.

**Capacity is no longer tight — corrected 2026-08-28.** This paragraph previously recorded the run as
"genuinely tight" at **141.2 GB** against ~135 GiB free on `EBC5-F0A3`. That figure was an artifact of
a defect, not a property of the tree: the script's `--exclude` flags were malformed and *inert for
`tar`*, so it archived every directory the exclude list named — most importantly `juniper-data/data`,
96 GB of regenerable dataset artifacts. With the exclude list actually applying (juniper-ml#1439), the
measured footprint is:

| | archived | unexcluded |
|---|---|---|
| whole project, 10 repos | **2.8 GB** | 113 GB |
| `juniper-data` alone | **34 MB** | 97 GB |

A **41x** reduction, and it fits both `EBC5-F0A3` (~135 GiB free) and `DFF3-2782` (~67 GiB) with room
to spare. Re-measure with [`util/ad-hoc/2026-08-28_backup_footprint.bash`](../util/ad-hoc/2026-08-28_backup_footprint.bash),
which uses the script's own exclude list and measurement path.

**The 2026-02-27 snapshot has been re-archived — 2026-08-28.** The 111 GB *plaintext*
`juniper-8.0.0_python_2026-02-27.tgz` was extracted once (applying the same repo-top-level exclude
policy, 111 GB -> 5.2 GB, zero errors) and re-backed through the fixed script as the labelled set
`snapshot-2026-02-27`: **15 archives, 186 MB, on both devices, all verified by restore**.

The legacy trees were deliberately **excluded**. On 2026-02-27 they sat at the parent's top level as
`JuniperCascor/ JuniperData/ JuniperLegacy/` (no `JuniperBackup/` yet) and were later consolidated
into `juniper-legacy/`. Diffed with that mapping applied — a prefix-keyed diff wrongly reports them
absent — the current tree reproduces **all** of it: **0 files exist only in the archive**, and once
logs / `__pycache__` / `.venv` churn is set aside the only difference is 514 bytes of
`.git/FETCH_HEAD`. 58,382 of 58,383 files match by size; 25/25 content hashes match. The current
`juniper-legacy` is a strict superset (16.0 GB vs 4.2 GB, +7,370 files).

Loose parent-level files (`AGENTS.md`, the `CLAUDE.md` symlink, the workspace file, a screenshot)
were staged into `_juniper-parent-files/` because the script archives directories, never loose files.

Once the owner is satisfied with the set, the 111 GB plaintext tarball can be deleted; it is the
single largest consumer of `EBC5-F0A3` and the exposure this script's encryption exists to prevent.

The script still warns at both thresholds rather than only below 50%. The pre-existing *unencrypted*
`juniper-8.0.0_python_2026-02-27.tgz` (111 GB) on `EBC5-F0A3` remains an owner decision — it is both a
plaintext copy of the whole project on removable media and most of that drive's used space.

#### 6.4.3 The ratified policy

Applying (1) and (2) to the cohort table leaves **no file in the archive with a deletion path**:

| cohort | n | bytes | §6.4 class | disposition |
|---|---:|---:|---|---|
| B — truncated writes | 273 | 13.0 MB | *(evidence, by q1)* | **quarantine, never delete** |
| zero-node, loadable | 15,927 | 666 MB | recoverable | **keep** — 380/380 sampled trained on demand |
| behaviour-attributed | 129 | — | unattributable legacy (by q2) | **quarantine, never delete** |
| loadable, hidden units, unattributed | 11,579 | 1.1 GB | unattributable legacy | **quarantine, never delete** |

**The middle category is empty, and this is the load-bearing finding.** *Run-attributed
intermediates* — the only class the proposal gave an ageing-out path — presupposed **identity**
attribution: a `RUN_ID` stamped at write time by Phase 6.1. The archive holds exactly **one**
identity-attributed file (`e-i-cap-ceiling`), and that one is a named experiment, so it is
*named/pinned* anyway. The other **129 are behaviour-attributed**, which q2 rules is not the same
thing. Phase 6.1 provenance began stamping only recently, so **no pre-6.1 file can ever enter the
ageing-out class** — the category is not merely empty today, it is unreachable for the entire
legacy archive.

Consequences:

- **No deletion tooling is to be built.** The four existing tools each carry an AST test
  enforcing that they have no delete path; that property is now the policy, not a precaution.
- The §7 gate for this phase — *"dry-run must propose zero deletions of anything
  provenance-linked"* — is satisfied vacuously and permanently: it proposes zero deletions of
  anything at all.
- **Question 3 is moot for this phase** (nothing is deleted, so nothing needs safeguarding), but
  the restore drill it names is **owed to the backup arc** regardless, and becomes a hard
  precondition if this policy is ever revisited.
- Should quarantine be implemented as a physical move, it inherits the full safety contract
  above: `--dry-run` by default, `--yes` required, refusal on any directory containing `.py`
  files, refusal outside the configured snapshot root, and every action logged to the index.

### 6.5 Explicit non-goals

- **No sweep, of any size, at any phase of this design.** The 1.74 GiB is not a problem worth risk.
- No rewriting or migrating existing snapshot files.
- No change to the on-disk HDF5 *format version* (Phase 1 is additive attributes only).

---

## 7. Validation plan

Per standard Juniper practice, each phase ships with its own gate:

| phase         | validation                                                                                                                                                                                                                                           |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 6.1 identity  | Unit: provenance attrs round-trip save→load. Drift: a snapshot written by the launcher carries the run's `RUN_ID` (asserted in `tests/test_experiment_stack_script.py`'s live arm).                                                                  |
| 6.2 index     | Behavioural tests over a synthetic snapshot tree (hermetic, mirroring `test_list_runs.py`): classification, `--json` shape, and that destructive flags do nothing without `--yes`. Plus a real read-only scan of the 27,869-file archive as a smoke. |
| 6.3 fixes     | **D-A: a regression test that fails on today's code** — assert `output_optimizer is not None` and its state matches after save→load. D-B: assert distinct outcomes for absent / corrupt / valid.                                                     |
| 6.4 retention | Dry-run over the real archive must propose **zero** deletions of anything provenance-linked; a planted unattributable fixture must be proposed for *quarantine*, not deletion. **SATISFIED PERMANENTLY (2026-08-23):** the ratified policy proposes zero deletions of anything at all (§6.4.3), and the four shipped tools each carry an AST test enforcing that they have no delete path. |

The census is reproducible and preserved as
[`util/ad-hoc/2026-08-16_snapshot_archive_census.py`](../util/ad-hoc/2026-08-16_snapshot_archive_census.py)
(`--census` for §2's structural figures, `--sample` for §2.1's stratified verification; seed-fixed,
read-only, and deliberately carrying **no delete path**). It reproduces every number in §2 and §2.1
exactly. It lives in `util/ad-hoc/` rather than a scratch dir per the repo's script-placement rule —
the rule exists because scripts of exactly this kind were lost once before.

---

## 8. Sequencing and dependencies

```bash
6.3 D-A (optimizer)  ── independent, highest value ──> ship first
6.3 D-B (load API)   ── independent
6.3 3.1 (move dir)   ── independent; closes the cascor#501 class
6.1 identity ───────> 6.2 index ───────> 6.4 retention proposal
```

Phase 6.3's three items are unblocked today. Phases 6.1→6.2→6.4 are strictly ordered: **retention
last, and only once the archive can say what each file is.**

**Outcome (2026-08-23).** That ordering did its job. By the time retention was reachable, the
index and the classifier could say what each file is — and what they said (§6.4.3) is that
nothing in the archive qualifies for deletion under any of the proposal's own categories. The
sequencing constraint was not merely procedural: had retention run first, the ageing-out class
would have looked populated, because behavioural attribution superficially resembles the
run-attribution the class was written for.

Relative priority against the program's other open work is set in the companion prioritisation
note, not here.

---

## 9. Open questions for the owner

| #       | Question                                                         | Why it needs a decision                                                                                                                                                           |
|---------|------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **S-1** | Should snapshots move out of repo checkout entirely              | Would make §3.1 structural rather than a fix, and stop checkout accrual permanently. Larger blast radius: changes default paths for both tiers.                                   |
|         | (e.g. under `~/.local/state/juniper-snapshots/`,                 |                                                                                                                                                                                   |
|         | mirroring the experiment `RUN_DIR` convention)?                  |                                                                                                                                                                                   |
| **S-2** | Is the March–April 2026 cohort (27,005 files, 96.9%) of retained | Decides whether Phase 6.4 needs a real policy or whether that cohort can be quarantined wholesale once identified.                                                                |
|         | research value, or is it a known bulk artifact of one campaign?  |   **CLOSED 2026-08-23.** §6.2 characterised it (identity is unrecoverable for the pre-2026-07-30 files); §6.4.3 then quarantines it wholesale, never deletes. The question no longer gates anything. |
| **S-3** | Should the service tier's `snapshot_history.jsonl` audit log     | Two mechanisms or one.                                                                                                                                                            |
|         | be extended to the CLI tier, or replaced by the §6.2 index?      |                                                                                                                                                                                   |
| **S-4** | Retention horizon and cold-archive location, once §6.2 exists.   | The only genuinely policy-shaped question, deliberately deferred to last. **Horizon ANSWERED 2026-08-23: there is none — nothing is deleted (§6.4.3).** Cold-archive *location* remains open, and any physical move is gated on the restore drill of §6.4.2 q3. |
| **S-5** | **Is R3 ("training pauses" with optimizer state)                 | Raised by the 2026-08-17 correction to §4.1. Cascor deliberately **recreates** the output optimizer on every `train_output_layer` call                                            |
|         | a real requirement for Cascade Correlation at all?**             |   because a hidden-unit insertion changes the output parameter space, making prior optimizer moments invalid *by construction* (`cascade_correlation.py:2050-2053`).              |
|         |                                                                  |   So R3-as-written cannot be satisfied by any serializer change, and may not be meaningful. If what is actually wanted is "resume training from a snapshot and continue growing", |
|         |                                                                  |   that is already what `/resume` does — and it needs no optimizer state. **Answering this decides whether any optimizer work is scheduled at all.**                               |

> **S-5 ANSWERED (2026-08-18) — R3 IS a real requirement, and it is NOT yet delivered.**
>
> The owner's answer: *"ideally, my preference would be to resume training on a restored network. The
> workflow would be something like: restore a snapshotted network, observe replay to gain insight
> into its training, edit the network based on that insight, and then resume training … this
> functionality would allow an iterative, experimental approach to network training that gets at one
> of the key purposes of the Juniper project."*
>
> So **restore → replay → edit → resume** is a first-class workflow, not a hypothetical, and R3 stands
> as written. The earlier suggestion that R3 might be dropped is withdrawn.
>
> **What the cascor#523-era fix does and does not buy.** The shipped fix (cascor `cb8a30e`) makes the
> restored optimizer *faithful* — correct class, `Parameter`-keyed state, real buffers, true `lr`.
> That satisfies **R1 (replay)**, **R2 (further experimentation)** and **R4 (crash recovery)**, and it
> is what makes the first three steps of the owner's workflow trustworthy.
>
> **It does not yet satisfy R3**, because the fourth step throws the state away:
>
> - `resume_from_snapshot` (`manager.py:4660`) calls `_load_snapshot_to_network` — so the faithful
>   optimizer *is* loaded — then computes `_resume_point_epoch` and `mark_resume_ready()`. It does not
>   touch the optimizer again.
> - But the subsequent training pass runs `train_output_layer`, whose `:2063` is an **unconditional**
>   `self.output_optimizer = self._create_optimizer(output_layer.parameters())`. The restored
>   optimizer is replaced before its first step.
>
> **The recreation is right, but over-broad.** Its own comment (`:2049-2053`) justifies it precisely:
> *"the output layer's parameter space changes each time a hidden unit is added … so the previous
> nn.Linear and optimizer state are invalid."* That is true **when a unit was added**. It is not true
> for a resume that has not (yet) grown the network — exactly the owner's case, where the operator
> edits weights or metaparameters and continues. The code applies the always-invalid rule to a
> sometimes-invalid situation.
>
> ~~**Proposed shape (not yet implemented, and deliberately not bundled with the restore fix):** reuse
> the existing `output_optimizer` when it is still valid for the current parameter space — same
> optimizer class, and `param_groups` shapes matching the rebuilt `nn.Linear` — and recreate only when
> that check fails.~~
>
> ⛔ **THE PROPOSED SHAPE ABOVE IS A TRAP — RETRACTED (2026-08-20). Do not implement it.** Reusing the
> optimizer **object** passes that exact check by construction and then silently stops training. The
> snapshot loader binds the restored optimizer to a *throwaway* `nn.Linear` it builds itself
> (`snapshot_serializer.py:1119`, bound at `:1135`), which is not the layer `train_output_layer`
> creates. Shapes match, so the check passes — then `loss.backward()` fills `.grad` on the new
> layer's parameters while `optimizer.step()` iterates the old ones, whose `.grad` is `None`. The
> unchanged weights are copied back, loss is still logged, callbacks still fire. Measured against a
> deliberate implementation of this shape: **output weights byte-identical after 2 epochs.**
>
> ✅ **SHIPPED SHAPE (cascor#539):** keep building the optimizer with `_create_optimizer`, then
> transfer the prior state with `new_opt.load_state_dict(old_opt.state_dict())` — torch's optimizer
> `state_dict` is **positionally indexed**, so it re-binds to the freshly created parameters.
> Guarded by class equality and a parameter-shape check.
>
> Two constraints the original sketch missed:
>
> - `load_state_dict` replaces `param_groups` wholesale, so it silently reverts a live
>   `PATCH /v1/training/params` learning rate to the snapshot's. Capture the fresh optimizer's
>   hyperparameters and re-apply them after: **current config wins for hyperparameters, snapshot
>   wins for state.**
> - `_zero_optimizer_state_for` (the `PATCH /v1/network/weights` guard) was **inert** — it looked up
>   state by the network-level tensor, never the `nn.Linear` `Parameter` the optimizer keys by. Under
>   reuse that would step an edited weight with pre-edit moments, so it had to be fixed in the same
>   change.
>
> **Evidence contract met:** a test that resumes and asserts `step` *continues*, a negative control
> that growth still forces a rebuild, and a test that the layer's weights actually **move** — the
> last being the only one that catches the trap. Golden trajectory unchanged, locally and in CI.

---

## 10. Relationship to F-P1-4 as previously recorded

The P1 smoke note's F-P1-4 row says *"the smoke left **4** snapshot `.h5` files … Files left in
place for the owner"*, with the remedy *"**W-6** … redirects these into `RUN_DIR/snapshots/`"*.

Both halves need updating and are updated in that note: the count is **27,869**, and W-6 redirects
only when its env var is exported, so the direct-CLI path still accrues into the checkout. The
finding's disposition changes from *"keep or delete"* to *this design*.
