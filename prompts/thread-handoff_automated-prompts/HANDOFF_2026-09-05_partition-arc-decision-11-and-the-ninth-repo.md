# HANDOFF — partition arc, decision 11, and the ninth repo

**Date**: 2026-09-05 · **Session**: <https://claude.ai/code/session_01TLRJzK5ENpFF3vZjZ9wYeX>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/binary-swimming-emerson`
**Branch**: `docs/handoff-partition-decision-11-ninth-repo` (juniper-ml#1782)
**Revision**: round-2 consensus applied. §10 records what round 2 overturned — including four
errors this document itself introduced.

**Documents REFERENCED** (the ecosystem convention in
`/home/pcalnon/Development/python/Juniper/AGENTS.md` § Cross-Project Conventions requires the
filename on every citation, because more than one document is cited):

- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` — design of record
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` — rollout plan
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — §10's instrument
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` — this document's template
- `util/ad-hoc/README.md` — the ad-hoc header convention

**Documents CHANGED**: this file; header blocks in the eight
`util/ad-hoc/2026-09-05_{census_full_family,drop_full_data_client,drop_full_data_client_tests,drop_full_data_client_docs,drop_full_producer,drop_full_producer_tests,drop_full_producer_docs,fix_partition_import_placement}.py`;
and one new file, `util/ad-hoc/2026-09-05_census_full_family_v2.py` (§3.1). Nine scripts, one document.

---

## 0. PREFLIGHT — do these five things before reading further

Every one of them cost this document an error.

1. **Fetch all five repos.** juniper-data, juniper-data-client, juniper-cascor, juniper-canopy,
   juniper-recurrence. Three separate stale-checkout errors were made here, in cascor *and* canopy.
   **§4's canopy line numbers are from a local tree 3 commits behind `origin/main`; §5's cascor line
   numbers are from `origin/main` via `gh api`.** Do not mix them up.
2. **Check juniper-data#369's arm state.** It was found **ARMED** at 18:44:02Z while its own
   auto-merge commit body says, in bold, *"Do not merge this before juniper-data-client#190,
   juniper-canopy#589 and cascor's `required_keys` relaxation are in."* Two of those three are now
   in; **cascor's is not.** This session **disarmed it**. If it is armed again, disarm it again until
   §5 ships: `gh pr merge --disable-auto 369 --repo pcalnon/juniper-data`.
3. **Read #369's CI before analysing it.** `gh pr checks 369 --repo pcalnon/juniper-data`. It is
   **RED** and tells you in one line what §3.0 took a page to infer.
4. **Nothing in this document is a quotation about merge order.** Neither
   `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` nor
   `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` contains the word
   "merge" — zero hits in both. The ordering in §1 is an **inference**, sound but unsourced.
5. **Environment.** The conda envs are `JuniperCascor1` / `JuniperCanopy1` / `JuniperData` — the
   bare `JuniperCascor` / `JuniperCanopy` names are `-DEPRECATED`, contradicting
   `/home/pcalnon/Development/python/Juniper/AGENTS.md`. **juniper-recurrence has no conda env at
   all** (`juniper-recurrence/AGENTS.md:125`); install into your active env. juniper-data is **not
   running** — port 8100 is not listening — so §3.2's sites 1 and 2 cannot be exercised live without
   starting it. canopy python needs `env -u LD_LIBRARY_PATH`.

---

## 1. Goal statement

Continue the Juniper partition arc. `X_val` is shipped producer→consumer; what remains is
**decision 11** — removing the `*_full` family from the NPZ contract — and the release train behind
it. This session wrote no production code. It re-derived the state twice, under
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, and both
passes moved things.

**Completed.** `X_val` end to end (juniper-data #353/#358/#361/#367/#368,
juniper-data-client #187, juniper-cascor #620/#622/#623, juniper-ml #1744/#1750/#1751/#1752/#1761).
Decision 11 consumer-side in juniper-data-client#190 — that repo is genuinely done, and says so at
`juniper_data_client/constants.py:429-437`. **canopy#586 and #589 both MERGED** (19:33:57Z,
19:55:26Z). Chunk 6, Chunk 8 and Chunk 9 are in. **juniper-data 0.13.0 is PUBLISHED on PyPI.**

**The central finding.** The consumer census decision 11 rests on — §9.5.1 of
`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` — is incomplete.
An independent re-census found hard breaks in **five** repos, including an entire repository the
census never scanned and an API route that dies outright. §3 is the corrected census. The instrument
that produced the original, `util/ad-hoc/2026-09-05_census_full_family.py`, had three scope defects;
§3.1 measures exactly what each cost.

**Authoring order.** Write commits in this order; merge in the different order below.

0. **Repair juniper-data#369.** Three defects, §3.0. Its CI is red and names two of them.
1. **cascor's `required_keys`** (§5). This is the only unmet precondition of #369's own merge
   instruction, so it is the critical path for the whole arc.
2. **The two exposed recurrence sites** (§3.2). `POST /v1/crossval` dies permanently.
3. **The remaining juniper-data sites** (§6) and the ml sites (§7).
4. **Docs** (§8), starting with `/home/pcalnon/Development/python/Juniper/AGENTS.md:122,130` — the
   always-loaded parent agent file. **It is in no git repository** (`git rev-parse` there returns
   *"not a git repository"*), so there is no PR, no CI and no merge slot: edit in place and know the
   change is invisible to every other machine.

**Merge order** — an inference, not a citation (PREFLIGHT 4). cascor `required_keys` → recurrence →
**juniper-data#369 LAST**, keeping #369 disarmed until cascor lands. The reasoning: cascor
`src/spiral_problem/data_provider.py:209` *rejects* an artifact lacking `X_full`, so a producer that
stops emitting it before cascor is relaxed breaks every new artifact fleet-wide. §9.5.4 of
`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` supports this only
indirectly: it obliges consumers to keep *tolerating* `X_full` after producers stop, and names
`required_keys` as "the one site that would reject an artifact for its absence." It does not state a
sequence. #369's own commit body does.

**Still open.**

- **§9.5.4 of `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`** —
  four items, two now done. Table in §9.
- **Decision 12 is ADOPTED and unimplemented**: a `partition_provenance` block **inside the NPZ**
  plus one ingestion gate, ruled 2026-09-03 (§9.2 row 12 and §9.6.3 of that same design document).
  §9.6.6 records the schema as *described, not specified*; no code has moved.
- **The plan's "crossval tier out of scope" ruling is FALSIFIED** — §3.3, and it is why §3.2 site 1
  exists.
- **V-3 is an open measurement.** §4 of
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` homes it to Chunk 6;
  Chunk 6 shipped the plumbing and nobody took the measurement.
- **Chunks**: 3, 3b, 4, 6, 8, 9 shipped with PR evidence; **1 and 2 believed shipped, unevidenced
  here**. Open: **Chunk 5** (§6.2 generate-shortfall of
  `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`) and **Chunk 7**
  (re-baseline, snapshot provenance, `plots_cascor.py`, `snapshot_attribute.py`).
- **Risks**, from `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`:
  **R-2 HIGH**, remedied by §6a of that plan (presence-and-shape, not exact-set; `X_val` absent ⟹ a
  gated path, not a failure; extra keys ignored). **R-3 HIGH** (§3.4). **R-4 is theoretical** — S-6
  downgraded it. **R-9 MEDIUM.** **R-1 re-opens** (§3.0c). **S-5 OPEN**, **S-7** filed as
  juniper-canopy#559.
- **The four issues under §9.6.4 of
  `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` are CLOSED**, not
  filed-and-unstarted: juniper-data #317 (2026-09-03), #319 (2026-09-03), #314 (2026-09-04), #320
  (2026-09-04). An earlier revision of this handoff said unstarted — see §10.

**Standing constraints.** Merge approval granted for every PR in this session and arc; deploy and
PyPI gates are Paul's. Commits carry the `Co-Authored-By:` / `Claude-Session:` trailers; PR bodies
the Claude Code line and session URL. All git operations target this worktree. Never bare
`git stash`. `/tmp/` is prohibited for scripts touching repo content.

---

## 2. State

**Stable — what each PR is:**

| repo | PR | what it does |
| --- | --- | --- |
| juniper-data | #367, #368, #374, #375 | MERGED — sequence `val`; three live defects; the `extras` path |
| juniper-data | **#369** | *"stops emitting the `*_full` family"* — **OPEN, RED CI, disarmed by this session** |
| juniper-data-client | #190 | MERGED — consumer side; repo done |
| juniper-cascor | #620, #622, #623 | MERGED |
| juniper-canopy | #586 | **MERGED 19:33:57Z** — Chunk 8 / §6.4 gated choice |
| juniper-canopy | #589 | **MERGED 19:55:26Z** — §9.5.4 item 2, the artifact guard |
| juniper-ml | #1744/#1750/#1751/#1752/#1761 | MERGED — Chunk 9 |

**Volatile — re-measure, do not trust.** These moved repeatedly inside one session. Commit counts
below were correct at ~20:00Z and were already wrong twice before that.

| repo | version | tag | commits since |
| --- | --- | --- | --- |
| juniper-data | 0.13.0 | `v0.13.0` **published** | 8 |
| juniper-data-client | **0.4.2** | `v0.4.2` (`cec374f`, 2026-06-17) — **predates #187 and #190** | 96 |
| juniper-cascor | 0.10.0 | `v0.10.0` | **19** |
| juniper-canopy | 0.6.0 | `v0.6.0` (2026-07-28) | 108 |
| juniper-ml | 0.7.1 | `v0.7.1` (2026-08-09) | 648 |

---

## 3. The corrected census

Re-measured from an independent entry point — all ten repositories plus
`/home/pcalnon/Development/python/Juniper/{src,util}` — not from either design document. **Zero**
`*_full` sites in juniper-cascor-client, juniper-cascor-worker, juniper-deploy, juniper-slacker, or
the top-level `src/`/`util/`.

### 3.0 juniper-data#369 — three defects, and its CI names two

**Its head is `f843d5a9`, not the `d0b43f44` an earlier revision cited.** It has base-refreshed and
absorbed #374.

**(a) `equities_seq` — already broken at the head.**
`juniper_data/generators/equities_seq/generator.py:209` reads
`truncation["records_imported"] = int(arrays["X_full"].shape[0])`, the sole surviving `_full` in a
file whose `_assemble` no longer produces it. Reached whenever `truncation is not None` — the
APD-DATA-018 symbol cap. `juniper_data/tests/unit/test_equities_seq_symbol_cap.py:137` pins it and is
**not in the PR's 47-file diffstat**. **Repair not decided**: is `records_imported` the pre-partition
import count or the partition sum? Answer that before patching.

**(b) `arc_agi` — extras are silently DROPPED, not a KeyError.** An earlier revision predicted
`KeyError: 'X_full'` from a truncation loop. At `f843d5a9` that loop is **gone entirely**:

```python
aligned = dict(extras or {})
split = shuffle_and_split_three_way(..., extras=aligned)
return split          # <- nothing writes `aligned` back into `split`
```

so `arc_agi`'s `task_ids` is never emitted. The docstring still describes truncation "to `X_full`'s
length". **The repair is to re-add the assignment**, bounded by
`counts["n_train"] + counts["n_val"] + counts["n_test"]` — not merely to re-bound a loop that no
longer exists.

**CI confirms both**, and is the fastest route to either:

```
FAILED test_arc_agi_generator.py::...::test_generate_from_hf          - assert 'task_ids' in {...}
FAILED test_arc_agi_generator.py::...::test_generate_hf_missing_task_id - KeyError: 'task_ids'
FAILED test_arc_agi_generator.py::...::test_generate_from_local        - KeyError: 'task_ids'
FAILED test_arc_agi_generator.py::...::test_task_ids_stay_aligned_with_shuffled_full - KeyError: 'X_full'
FAILED test_csv_import_cap_enforcement.py::...                         - KeyError: 'X_full'
========== 5 failed, 251 passed, 123 deselected in 14.96s ==========
```

**That list is a floor, not a census**: the job runs `--maxfail=5` and aborted at **256 of 1543**
selected tests. `test_equities_seq_symbol_cap.py:137` never ran — it is unreached, not passing.

**(c) No `generator_version` bump — R-1 re-opens.** Zero `VERSION =` changes across the diff. R-1 was
closed because all 16 generators went to `2.0.0` for the *val* change and `generate_dataset_id` hashes
it. Removing keys is a second contract change with no bump, so cache state decides whether a consumer
sees `*_full`.

**(d) A new defect #369 introduces.** Its `csv_import` replacement is
`fit_source = X_train if X_train.shape[0] else np.vstack([a for a in (X_val, X_test) if a.shape[0]])`,
which raises `ValueError: need at least one array to concatenate` when all three are empty — a case
the old `X_full` covered.

### 3.1 The instrument, and what its defects cost

`util/ad-hoc/2026-09-05_census_full_family.py` is what was actually run. Three scope defects, now
measured rather than asserted:

| defect | what it hid |
| --- | --- |
| `REPOS` = 5 repos (`:38`) | **juniper-recurrence only** — 43 consume sites over 12 files. The other four unscanned repos genuinely have zero. |
| `--include` = `*.py`/`*.md` only | **one** site: `prompts/agent_templates/data/ecosystem.yaml:32` |
| per-repo loop, no ecosystem-root scope | **two** statements, both in `/home/pcalnon/Development/python/Juniper/AGENTS.md` |

§9.5.5 of `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` claims
eight repos; §8 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`
counts nine agents-over-repos; the instrument saw five. The failure class is a **correct predicate
over an incomplete site enumeration** — reviewing a gate's enumeration is a separate act from
reviewing its predicate, and only the second was done.

`util/ad-hoc/2026-09-05_census_full_family_v2.py` is the corrected instrument (ten repos + root; eight
file types; `git ls-files` instead of a filesystem walk, which took it from *not finishing in eight
minutes* to seconds). **It over-reports**: six juniper-deploy "sites" are
`profiles: ["full", "demo", "dev", "test"]` in `docker-compose.yml`, and a round-1 reviewer who
reported juniper-deploy as zero was right. The false-positive class is documented in the script
rather than tuned away, because narrowing the pattern would lose the split-name allow-lists it exists
to catch.

### 3.2 juniper-recurrence — the ninth repository

Real (`pcalnon/juniper-recurrence`, clean, `main` `c7dec7e`), a first-class `recurrence` extra at
`pyproject.toml:67-69`, absent from the Active Repositories table in
`/home/pcalnon/Development/python/Juniper/AGENTS.md`.

1. **`POST /v1/crossval` dies permanently.**
   `juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/crossval.py:72` passes
   `split="full"` — hardcoded, commented *"CV always derives folds from the full chronological set
   (D-CV-4)"*. The router maps the `ValueError` to an HTTP data error, so it fails **loudly**;
   `GET /v1/crossval/status` never populates.
2. **The model tier raises.**
   `juniper-recurrence/juniper-recurrence-model/juniper_recurrence_model/data.py:66-67` —
   `if f"X_{split}" not in arrays: raise ValueError(...)`. This is the mechanism site 1 trips.
3. **The benchmark harness reads only `*_full`** — `bench/datasets.py:51-52`, 24 calls across six
   factories, keys `X`, `y`, `y_reg`, `dt`, `target_dt`, six importers, live under
   `ci-recurrence-bench.yml`. **It is NOT a merge gate**: `juniper-recurrence/juniper-recurrence/pyproject.toml:95`
   and `:104` cap the bench extras at `juniper-data>=0.9.0,<0.12.0`, so 0.13.0 is already excluded and
   #369 cannot reach it. Note the cap also excludes 0.12.0, so widening it forces the `val` migration
   and the `*_full` migration at once.

Sites 1 and 2 have no such cap — they reach juniper-data through
`juniper-data-client>=0.4.2,<0.5.0` (`juniper-recurrence/juniper-recurrence/pyproject.toml:52`)
against a running service.

**Risk R-6 does not cover this**, and an earlier revision's claim that R-6 is "still wrong" was a
category error: R-6 is scoped to *silent* val-split exclusion caused by the `client<0.5.0` floor, and
its full text ends *"; only its t/dt validation is skipped."* These sites break on `X_full` removal,
loudly, for a different reason. R-6's rating stands; it simply does not reach here.

### 3.3 Decision 11 falsifies the plan's crossval scope ruling

§4 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md:160` lists
*"the crossval tier (D-CV-4)"* under **"Out of scope, evidenced"**. D-CV-4's premise is recorded in
`juniper-model-core/juniper_model_core/crossval/splits.py:5-6`: *"folds are derived client-side from
the `*_full` arrays; no `juniper-data` change is required for v1."* Decision 11 deletes `*_full`, so
the evidence for the scope ruling is void.

`juniper-model-core` is **published at 0.3.1** — a released package whose docstring asserts a dead
contract — and `juniper-recurrence-model/tests/test_crossval.py:19` imports from it. So §3.2 site 1 is
not an oversight in recurrence; it is the predictable consequence of a scope ruling decision 11
invalidated.

### 3.4 R-3's mechanism, and the census to quote

`DatasetMeta(**meta_dict)` at `juniper_data/storage/local_fs.py:249` against
`juniper_data/core/models.py:38-39` required-with-no-default. §9.5.4 item 1 of
`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` redefines
`DatasetMeta.n_samples` — exactly R-3's failure class — and #369 is the PR that would do it.
**Default the field.**

Blast radius: **39 artifacts across 7 roots**, not the 26-across-5 an earlier revision quoted. That
design document at `:830-831` supersedes the plan's S-6 census explicitly, and adds that any such
figure is valid only with its timestamp — live volume grows ~10 writes/day.

---

## 4. canopy — mostly done, and cited from a stale tree

**Every canopy line number in this section is from a local checkout 3 commits behind
`origin/main`, pre-#586/#589.** They are kept because the *substance* below survives; re-derive
before editing.

**Refuted by #589**: `_validate_npz_arrays` no longer requires `X_full` — on `origin/main` it is
`:818`, walks `_VALIDATED_PARTITIONS = ("train","val","test")` (`:815`), and requires
`X_train`/`y_train`. The four "direct subscripts with no fallback" are now
`_whole_dataset(npz_data, …)` (`:1009`, `:1010`, `:1902`, `:1903`), and `:1893-1897` falls back
`X_full` → `X_train`. **§9.5.4 item 2 is DONE**, with tests (`test_demo_mode_gate_coverage.py`,
`test_juniper_data_integration.py`).

**Survives #589** — the silent-fallback class, which is worse than any crash here:

- The `ValueError` path is still swallowed by bare `except Exception` at three sites
  (`origin/main` `:550-554`, `:1820-1824`, `:2241-2245`), substituting
  `_generate_spiral_dataset_local` (`:1045`) — deprecated, `np.random.seed(42)`, 4π, 2 classes. **The
  genuine fallback delta is `n_rotations` and `algorithm`, not "every dataset knob"**: the happy path
  already hardcodes `n_spirals` and `noise`. The real damage an earlier revision missed is that the
  fallback skips the [-1,1] normalisation and never sets `network._input_min`/`_input_max`, so the
  decision boundary renders with absent normalisation parameters.
- `_install_sequence_dataset` still falls back to `*_train` (`origin/main` `:2002`, `:2008`, `:2028`),
  making `n_windows`, `windows_X`, `windows_y`, `lookback` and `n_features` **all** train-only while
  an inline comment claims whole-dataset.
- **#589's new surface has zero test coverage**: no test references `_whole_dataset` or the
  partial-pair error at `demo_mode.py:847-849`.
- `src/tests/conftest.py:406-407,432-433` — the shared fixtures still pass (they supply
  `X_train`/`y_train`), but **both are two-way with no `X_val`/`y_val`**, already stale against the
  shipped contract. **8** canopy test files carry the family; two are `pytest.raises(match="X_full")`
  guards keyed to an error string decision 11 rewrites.

---

## 5. cascor — the critical path

The **service** is clean (`src/api/app.py:531` → `src/api/lifecycle/manager.py:3807` →
`_artifact_to_tensors` reads no `_full`). The **direct CLI** is not, and it is the last unmet
precondition in #369's own merge instruction.

**It is BOTH a key-set relaxation AND an arity change.** An earlier revision said "not a key-set
relaxation"; taken literally that ships a half-fix in which cascor rejects every post-#369 artifact.
Do all three: **relax the requirement, keep the tolerance, drop the tuple member.**

**Line numbers from `origin/main` post-#622**, read via
`gh api repos/pcalnon/juniper-cascor/contents/...`. Three documents have cited `required_keys` at
three different wrong lines (§9.5.4 of
`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` says `:193`; an
earlier revision of this file said `:195`).

`src/spiral_problem/data_provider.py`: `SpiralDatasetTuple` `:29-34` (`(x_full, y_full)` member
`:33`), annotation `:122`, docstring `:146`, `_convert_arrays_to_tensors` `:194`, **`required_keys`
`:209`**, error `:212`, shape loop `:231`, tensor build `:244-245`, return `:247`.
`src/spiral_problem/spiral_problem.py`: docstring `:572`, 4-way unpack `:1333`, assignment `:1340`,
**seven** log lines `:1336`/`:1342-1344`/`:1346-1348`, plot payload `:1371`.

**Do not believe "the plot is the only consumer of `full`."** §9.5.1 of
`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` annotates *one*
cascor row "plotting only" and lists `data_provider.py` separately — and the seven log lines above are
seven more consumers. Concatenating at the plot site is still the right shape; it is just not the
whole job.

`src/tests/unit/test_cli_partition_arity_contract.py` (merged by #622) encodes the 4-arity
deliberately — `CLI_EXPECTED_PARTITIONS = 4`, `_unpack_four`,
`test_partitions_arrive_in_train_val_test_full_order`. It exists to catch this drift, so update it
rather than work around it. Five more cascor test files follow; the integration ones are marker-gated
and invisible without `--integration`.

---

## 6. juniper-data's own remaining sites

**Six of these are already fixed inside #369** — this is a census of the PR's work, not of work
outstanding. Genuinely remaining: `equities_seq/generator.py:209` (§3.0a), the two stores, and
`test_val_emission_guards.py:127`.

- **Fixed by #369**: `csv_import/generator.py:71,89,93,102-103` (`:89` was the empty-train normaliser
  fallback — and fitting on `X_train` *is* juniper-data#314's shipped remedy, now CLOSED);
  `delay_product/generator.py:89-91` and `equities/generator.py:336` (both drop `"full"`);
  `api/routes/datasets.py:963-968` (re-pointed at `train`; `core/meta.py:109-120` was the
  already-correct sibling); six `expected_keys` assertions.
- **`storage/hf_store.py:145-146` and `storage/kaggle_store.py:242-243` still write
  `X_full`/`y_full` and carry no `X_val`/`y_val`.** `util/ad-hoc/2026-09-05_drop_full_producer.py`
  records leaving them as a decision. The consequence was not thought through: cascor *refuses* a
  val-less artifact, so every HF/Kaggle artifact is already unusable downstream. #369 edits their
  tests while leaving the producers alone.
- **`test_val_emission_guards.py:127`** is `test_full_is_the_vstack_of_the_three_partitions` — a guard
  whose entire purpose is the retired identity. Untouched by #369.
- **39** test files reference the family (not 31). **#369 leaves 10 of them untouched**, including
  `test_equities_seq_symbol_cap.py` (pins §3.0a) and `test_csv_import_cap_enforcement.py` (one of the
  five CI failures). `test_api_routes.py:136`/`:301` — `test_preview_uses_x_full_y_full_when_available`
  and `test_preview_stacks_train_test_when_no_full_arrays` — still **pass** while testing the opposite
  of their names, because #369 deleted both branches they cover. Silent coverage loss, not a red test.

### 6.1 The row-order permutation reaches further than first thought

`equities_seq/generator.py::_assemble` builds per-split arrays split-major (`:233`) and built `_full`
ticker-major (`:236-239`) — same rows, different permutation. **The same is true of tabular
`equities`**: `:304-306` concatenates whole frames per ticker into `full`, while `:307-309` build the
splits per-split. And unlike `equities_seq` (3-D, routed to `_install_sequence_dataset`), tabular
`equities` is 2-D and **does** reach canopy's `_whole_dataset`, whose legacy branch returns the
ticker-major `X_full` while a post-#369 artifact yields the split-major concatenation. **Canopy will
render two different row orders for the same logical dataset depending on artifact vintage.**

An earlier revision claimed this also moves the recurrence benchmark's numbers. **Refuted**:
`bench/datasets.py:211-213` declares `symbols: tuple[str, ...] = ("AAPL",)` and `:289` registers the
bare function, so `len(per_ticker) == 1` and the two orders are the same array. It qualifies §9.5.1's
*"nothing is lost by removing them"* in
`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`: membership is
preserved, order is not.

---

## 7. juniper-ml

- **`util/snapshot_attribute.py:318`** — `produced["X_full"]`/`["y_full"]`, **outside** the
  `try/except` at `:311-316`, so a crash rather than the "recorded gap" path.
  `tests/test_snapshot_attribute.py` has no `_full` reference. Tabular tier, and
  `juniper_data/core/split.py` built the old `X_full` as `np.vstack([X_train, X_val, X_test])`, so the
  concatenation is byte-identical.
- **`RECURRENCE_SPLITS` (`util/experiments/run_experiment.py:159`) — keep `"full"`, weakly.** It gates
  `dataset.split` (`:637-639`) and `predict.from_dataset_split` (`:675-677`), both forwarded verbatim
  to the recurrence service (`:1954`, `:1976`), which accepts any string
  (`juniper_recurrence/schemas.py:83` is a bare `split: str`). Nothing requests it today;
  `tests/test_run_experiment.py:790` pins the four-member set; E-12 of
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` documents both guards
  and both rejection tests; and S-5 in that plan, which calls three of four juniper-ml homes wrong,
  does **not** dispute this one. The back-compat argument does not carry — the lane requires a
  generator (`:632-634`) and always calls `create_dataset`, so stored artifacts are reachable only by
  **cache hit**, which is §3.0(c)'s nondeterminism. Keep it for inertia, and pair it with an explicit
  not-found error path.
- **`util/experiments/plots_cascor.py`** reads only train/test, so `dataset.png` silently omits the
  validation rows. §4 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`
  homes it to Chunk 7; S-5 in that plan re-homes it to Chunk 3/4 and corrects the lines to `:69`/`:73`.
  Doubly homed, not unhomed — pick one.
- **Stale contract declarations**: `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:244` and
  `prompts/agent_templates/data/ecosystem.yaml:32`, both still the pre-arc two-way list.
  Documentation-only: `npz_contract` is read by nothing (S-5 says so; verified by grep).
  `juniper-model-core/juniper_model_core/crossval/splits.py:6` is a third — see §3.3.
- **S-5's two unhomed instruments**, carried by no handoff in this arc:
  `util/experiments/suites/p4/e-o-val-split-bias-cap4.yaml` and
  `util/ad-hoc/2026-08-29_val_split_bias_collect.py`. Its third site, `docs/REFERENCE.md:1679`, holds
  no contract reference and that file has no `X_full` — unresolved either way.
- **16 `util/ad-hoc/` scripts** read the family. Retained provenance; they will not re-run.
- **A compound silent failure**: `_aux_phase` (`:1913-1934`, called `:1990`) records crossval HTTP
  failures and returns `None` — *"failures are recorded, never fatal"*. With §3.2 site 1, every
  recurrence experiment with `crossval.enabled` completes and writes a manifest with `crossval: null`.

---

## 8. Documentation

- **`/home/pcalnon/Development/python/Juniper/AGENTS.md:122,130`** — the always-loaded parent agent
  file, publishing the key list and the `len(...) == len(X_full)` identity. Not in any git repository
  (PREFLIGHT 5).
- **juniper-data, 13 statements** across `README.md`, `AGENTS.md`, `docs/QUICK_START.md`,
  `docs/REFERENCE.md`, `docs/USER_MANUAL.md`, `docs/DEVELOPER_CHEATSHEET.md`,
  `docs/DOCUMENTATION_OVERVIEW.md`, `docs/api/JUNIPER_DATA_API.md`,
  `docs/testing/TESTING_REFERENCE.md`. #369 covers most — diff it rather than assume.
- **juniper-data-client `docs/REFERENCE.md:639`** still documents the four-member `NPZ_SPLITS`, stale
  since #190.
- **Consumers**: `juniper-canopy/docs/demo/DEMO_MODE_REFERENCE.md:375`;
  `juniper-recurrence/README.md:48`; `juniper-recurrence-client/README.md:48` and
  `juniper_recurrence_client/client.py:514`.
- **Inverse risk**: `juniper_recurrence/main.py:53` advertises `full` in `--split` help while
  `schemas.py:83` has no `Literal`, so `{"split": "full"}` is accepted and fails at load.

---

## 9. §9.5.4 status, and the release train

Items from §9.5.4 of `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`:

| # | item | status |
| --- | --- | --- |
| 1 | `DatasetMeta.n_samples` → partition sum | **UNOWNED**; fires R-3 (§3.4) |
| 2 | canopy's validation ladder re-pointed, explicitly and tested | **DONE** — canopy#589, with tests |
| 3 | preview endpoint needs a new source (a product decision) | done inside #369 |
| 4 | `NPZ_SPLITS` | **DONE** — juniper-data-client #187 then #190 |

**Release train.** The split is already shipped: juniper-data 0.13.0 (three-way emitter) is live on
PyPI while `juniper-data-client 0.4.2` is the only client there, and 0.4.2's failure mode is
**silent** — `contract.py` (at tag `v0.4.2`, `:68`) iterates `NPZ_SPLITS` and skips absent splits, so
it ignores `X_val` rather than raising.

- **juniper-data-client is the blocker, and cutting 0.5.0 is not free.** `v0.4.2` ships
  `NPZ_SPLITS = ("train","test","full")` (`:258` at the tag) while `main` has
  `("train","val","test")` (`:437`) under the same version number. But §5 of
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` records the ceiling
  `juniper-data-client>=0.4.2,<0.5.0` as recurrence's **core runtime** dep
  (`juniper-recurrence/juniper-recurrence/pyproject.toml:52`), that the release train only auto-opens
  PRs for a **MINOR** bump (`propose.py:930`), and that a consumer floor bump is unresolvable until
  the new client is on PyPI while **Lockfile Freshness is a required gate** in canopy, cascor and
  data. Order: widen recurrence's ceiling → publish the client → bump floors → regenerate lockfiles.
- **juniper-data** owes a second release after #369 (keys removed **and** the `generator_version`
  bump §3.0c requires). **juniper-cascor** 19 commits past `v0.10.0`, breaking → 0.11.0.
  **juniper-canopy** 108 past `v0.6.0`. **juniper-recurrence** after §3.2. **juniper-ml** itself is
  648 commits past `v0.7.1`.
- **juniper-ml floors are all pre-arc**: `pyproject.toml:30`, `:47`, `:48`, `:49`, and the
  `recurrence` extra `:67-69`.

Every deploy is a cut GitHub Release with notes under `notes/releases/` — never a bare tag push.

---

## 10. Consensus validation — two rounds, and what they cost

Instrument: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
**Sample**: 6 agents over 2 rounds, ~390 tool calls, 10 repositories.
**Round 1** — 3 lanes: one Lane A re-measurement (forbidden both design documents and this archive)
and two Lane B lenses (claim refutation; omission-and-framing).
**Round 2** — 3 lenses, briefed per §4 of that procedure **explicitly on the ~18 corrections**, not on
the whole artifact: what-the-fix-pass-broke; fresh-engineer executability; coverage of §4/§6, which no
round-1 lane examined.

**Neither round terminated.** Both changed numbers, dispositions and actions.

Round 1 found the ninth repository and the `split.py` hazard, refuted two of this document's claims
(the `equities_seq` permutation is a no-op at the benchmark's single-ticker config; the bench extra is
capped so #369 cannot reach it), and caught R-4 reported HIGH against S-6's downgrade.

**Round 2's yield was larger, and four of its findings are errors this document's own fix pass
introduced** — which is exactly what §4 of that procedure predicts ("the fix pass is the least
trustworthy part of any document"):

| # | what the fix pass broke |
| --- | --- |
| 1 | Asserted three times that #369 is "deliberately NOT armed". **It was armed**, at 18:44:02Z, against its own commit body. Worse, correction #6 filed that claim in a table newly labelled *"stable, safe to rely on"* — armed-ness is the most volatile field on a PR. |
| 2 | Added the four §9.6.4 issues as "filed and unstarted" by transcribing status from the design document instead of GitHub. **All four closed 2026-09-03/04**, before this handoff was written — and §6 quoted #314's shipped remedy while calling it unstarted. |
| 3 | Attributed the merge order to §9.5.4's back-compat clause as though quoting it. That clause is about **tolerance**; neither design nor plan contains the word "merge" (0 hits in both). |
| 4 | Cured the stale-checkout class in cascor (§5, re-derived via `gh api`) and left its sibling in canopy (§4) uncured and unlabelled. |

Round 2 also: corrected §3.4's blast radius from a superseded 26/5 to **39/7**; showed §5 is a
key-set relaxation **and** an arity change, where "not a key-set relaxation" would ship a half-fix;
refuted the R-6 objection as a category error; found canopy#586/#589 **merged**; found #369's CI red
with a five-failure floor at 256/1543; found §3.0(b)'s mechanism to be a **silent drop** rather than
the predicted `KeyError`, invalidating the stated repair; and found the tabular-`equities` half of
§6.1, which reaches canopy where `equities_seq` does not.

**Reconciliation.** Every load-bearing claim from every lane was re-derived in-session before being
written here. That mattered twice: a round-1 lane reported a cascor unpack defect that #622 had fixed,
and my own corrected census instrument produced six false positives where a round-1 lane's "zero" was
right (§3.1).

**Unresolved dissent**: none outstanding — the two round-1/round-2 disagreements (bench as a gate;
the `equities_seq` permutation's reach) were both settled by opening the code.

**What this evidence cannot support**: whether any migrated juniper-data assertion is
row-order-sensitive (§6.1, ~180 assertions, unaudited); whether `hf_store`/`kaggle_store` should
partition (a product decision); the `t_*`/`dt_*` families and tabular `equities`'s `_val` siblings
(§9.5.5 bullets 2 and 3 of
`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`, only partly closed);
Chunk 1 and Chunk 2's shipped status; anything outside these ten repositories. **No tests were run in
either round** — every claim comes from source, git, the GitHub API and PyPI, not from a green run.

**Owed to a third round**: the corrections in *this* revision, unreviewed.

---

## 11. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/binary-swimming-emerson
git status --short && git log --oneline -1

# PREFLIGHT 2 and 3 — the two that decide what you may safely touch.
gh pr view 369 --repo pcalnon/juniper-data --json state,mergeStateStatus,autoMergeRequest,headRefOid
gh pr checks 369 --repo pcalnon/juniper-data

# §3.0 — read the PR HEAD, never the local checkout; main and the head differ here.
gh api repos/pcalnon/juniper-data/contents/juniper_data/core/split.py?ref=f843d5a9 \
  -q '.content' | base64 -d | sed -n '/^def partition_and_assemble/,/^    return split/p' | tail -12

# §5 — origin/main, post-#622. A local grep returns the stale :195.
gh api repos/pcalnon/juniper-cascor/contents/src/spiral_problem/data_provider.py \
  -q '.content' | base64 -d | grep -n 'required_keys\|X_full'

# §3.2 — the ninth repo
grep -n 'split="full"' /home/pcalnon/Development/python/Juniper/juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/crossval.py
grep -c '_full(out' /home/pcalnon/Development/python/Juniper/juniper-recurrence/bench/datasets.py

# §3.1 — the instrument, old and corrected
sed -n '38p' util/ad-hoc/2026-09-05_census_full_family.py
python3 util/ad-hoc/2026-09-05_census_full_family_v2.py | head -15

# §7 — ml sites
grep -n 'RECURRENCE_SPLITS' util/experiments/run_experiment.py
grep -n 'X_full' util/snapshot_attribute.py docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md prompts/agent_templates/data/ecosystem.yaml

# §4 — canopy is MERGED; re-derive its line numbers before trusting any of them.
gh pr view 589 --repo pcalnon/juniper-canopy --json state,mergedAt
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy fetch origin main
```

## 12. Git status at handoff

Branch `docs/handoff-partition-decision-11-ninth-repo`, PR **juniper-ml#1782**, auto-merge armed.

**A worked example of the trap in §13, at this document's own expense.** #1782 sat unmerged for over
an hour across five sync attempts. The diagnosis was the contended merge lane — juniper-ml `main`
took five merges in 45 minutes against a ~13-minute CI battery, and the PR genuinely did reach green
and fall `BEHIND` repeatedly, which made the story fit. It was **wrong**. The real blocker was an
unresolved CodeQL review thread on `util/ad-hoc/2026-09-05_fix_partition_import_placement.py`
("Empty except"), against a ruleset carrying `required_review_thread_resolution: true` — visible only
via `reviewThreads(isResolved: false)`, never in `gh pr checks`, which read 17/17 green throughout.
The tell was `mergeStateStatus: BLOCKED` rather than `BEHIND` once the branch was up to date;
`BLOCKED` with `mergeable: MERGEABLE` and every required context green means a *rule*, not a check.

Two lessons worth carrying: the lane contention was real but **incidental**, and a plausible
mechanism that explains the symptom is not thereby the cause; and
`util/ad-hoc/2026-09-05_auto_merge_shepherd.py` reports `NOT-ARMED` transiently from GraphQL when the
PR is in fact armed — its own docstring warns about that read, and it wants `owner/repo` where
`util/safe_merge.py` wants a bare name.

Working tree carries this document plus `util/ad-hoc/2026-09-05_census_full_family_v2.py`; the other
eight ad-hoc scripts are committed. The local branch is behind its remote by the `update-branch` merge
commits the shepherd creates — that is expected, and a `git worktree remove` here would delete the
untracked v2 script.

---

## 13. Traps

Cut from an earlier revision as "process narrative"; restored because the first entry cost this
document an hour and a wrong diagnosis (§12).

- **An unresolved CodeQL review thread blocks a merge while every check reads green.** juniper-ml's
  ruleset sets `required_review_thread_resolution: true`. `gh pr checks` cannot see it. Query
  `reviewThreads(isResolved: false)`. **`BLOCKED` + `mergeable: MERGEABLE` + all required contexts
  green = a rule, not a check.** juniper-cascor#622 was blocked four times this way.
- **Never assert `X_full` is absent.** §9.5.4 of
  `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` obliges readers to
  keep tolerating it; a test demanding absence turns "not required" into a requirement the other way.
- **The plan's §§2–7 are pre-review.**
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` says §9 is the live
  record and is not folded back. Reading its §7 risk table alone gives R-4 as HIGH when S-6
  downgraded it, and its S-6 artifact census when the design supersedes it (§3.4).
- **Status transcribed from a document is not status.** All four §9.6.4 issues read "filed, none
  started" in the design document and were closed on GitHub days earlier (§10).
- **`juniper-cascor-model/` drift guard**: edits to
  `src/{candidate_unit,utils,log_config,cascor_constants}` must be mirrored byte-for-byte;
  `test_drift.py` catches it only in CI.
- **Squash-merge ships only the first commit's diff** on a multi-commit PR → keep one commit.
  Auto-merge base-refreshes armed branches, so re-derive line numbers after every sync.
- `tests/test_env_repr_safety.py` forbids `dict(os.environ)` and its scanner reads source **text**,
  so it fires on comments too.
- Sequence-safety screens need CI's scope (`--scope 'juniper_data/**'`, `'src/**/*.py'`); a bare
  invocation reports `files_screened=0` and is vacuous. `Allow-Symbol-Loss:` must be the **last**
  paragraph.
- `util/safe_merge.py` wants a bare repo name; `util/ad-hoc/2026-09-05_auto_merge_shepherd.py` wants
  `owner/repo`. Background waiters get OOM-killed — do not run two on one PR.
- `gh` 2.46.0 breaks **all** `gh pr edit`; patch through `gh api -X PATCH .../pulls/N -F body=@file`.
- cascor's marker-gated `src/tests/integration/` skips without `--integration`.
- **This worktree-isolated session refuses** compound commands that name git with a runtime-computed
  value; issue them one at a time.
- juniper-ml's `ci.yml` test list is **hand-maintained** — a new test does not self-register.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

<https://claude.ai/code/session_01TLRJzK5ENpFF3vZjZ9wYeX>
