# Third-partition rollout — scope, sequencing, dependencies, risk

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (juniper-data → juniper-data-client → juniper-cascor / canopy / recurrence / ml)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-09-04
**Status**: PLAN v3 — **round 3 returned NOT RESOLVED on all four targets; four of its seven findings
have since moved.** §9 is still the live record and is **not** folded into §§2–7, which remain
v3-as-reviewed rather than v3-as-corrected. **Still do not implement from this document.**
The partitioning question is CLOSED on the design of record (decisions 9 REVERSED / 10 COLLAPSED /
11 / 12). Operator surface: [`docs/REFERENCE.md` § Train / Val / Test Partition Contract](../docs/REFERENCE.md#train--val--test-partition-contract).

| finding | state |
| --- | --- |
| S-1 cascor has no test slot | **PARTLY CLOSED** — cascor#614 built the machinery, cascor#616 populates it from the **inline** path. The **artifact** ingress still needs the ecosystem change (Chunk 4). |
| S-2 D-1's premise is false | **CLOSED** — D-1 re-posed and **ruled** 2026-08-31, with D-2 and a normalisation sub-ruling. See §3's banner and design §9.2. |
| S-3 `NPZ_SPLITS` owned by no chunk | **CONFIRMED** from source 2026-09-01. Still unhomed. Decision 11 makes drop-`"full"` + add-`"val"` one coherent edit (design §9.5.4 item 4). |
| S-4 §6a rejects sequence val artifacts | OPEN. |
| S-5 three of four ml homes wrong | OPEN. |
| S-6 store-root count vacuous | **RESOLVED** 2026-09-01 — full census; **R-4 downgraded to theoretical**, R-3 re-homed to LocalFS. |
| S-7 stale env justifying dead code | **FILED** as juniper-canopy#559. |

**A new requirement has since opened and gates the sizing work: prefix stability** (design §9.3).
**P-1a is measured BLOCKED** (design §9.3.1) — partly semantic, not merely expensive — so **P-1b is
recommended and awaits a ruling.** Code has moved in cascor only (#614, #616); no producer or
contract change has shipped.
**Design of record**: [`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md)
**Reviewed under**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) — record in §8

---

## 1. Revision history — what each version got wrong

Kept in full. A reader needs to know which claims from earlier versions to discard, and the pattern
is itself evidence about how this plan should be read.

**v1 → v2** (round 1, three adversarial lenses, all returned *do not ship*): the founding measurement
was backwards (five exact-key gates **do** run per-PR in juniper-data's unit lane); R-4 removed
(canopy boots); R-1 downgraded; R-6 named the wrong dependency edge; `SPIRAL_DATASET_TYPE` does not
exist; the "7 of 9 repos" headline was padded; and **two of five owner decisions had been dropped
entirely** (CLI early stopping, re-baseline).

**v2 → v3** (round 2, two lenses). Nine of eleven v2 corrections verified clean. The damage was in
the prose written *around* them:

| # | v2 claim | corrected in v3 |
| --- | --- | --- |
| E-1 | Chunk 2: *"fix the tabular early return at `contract.py:70-71` so the split loop is reachable for 2-D"* | **Dangerous and doubly wrong.** The loop calls `_validate_sequence_split`, which raises at `contract.py:89-90` when neither `t_<split>` nor `dt_<split>` is present. Tabular artifacts have neither, so this would raise on **every** tabular artifact. And the rationale was false: `validate_npz_contract` has **no fleet consumer** — `NPZ_SPLITS` is referenced twice, both inside `contract.py` itself. **Both round-2 lenses found this independently.** |
| E-2 | Chunk 4's *"consumer exact-set gate"* | **Unsatisfiable shape.** `equities` already emits `y_reg_*`, `ticker_code_*`, `date_*`, `ticker_vocab`; sequence artifacts carry `t_*`/`dt_*`/`observed_mask_*`; and §6 deliberately defers the sequence tier, guaranteeing a long 6-vs-8-key interval. See §6a for the corrected shape |
| E-3 | Chunk 3→4 interval *"Recoverable but inert"* | **Not inert.** cascor keeps early-stopping on `X_test` (`manager.py:1902-1909`) while a real `X_val` sits unread. §5's invariant stays violated **and the artifact now advertises compliance** — the defect is camouflaged, not absent |
| E-4 | C-6: *"`ml` … touch it only in tests"* | **Over-corrected.** juniper-ml is a runtime consumer: `util/experiments/run_experiment.py:149`, `util/experiments/plots_cascor.py:68,98`, `util/snapshot_attribute.py:318`, `prompts/agent_templates/data/ecosystem.yaml:32` |
| E-5 | D-2: *"four cross-field ratio validators must invert"* | **Two** exist (`spiral/params.py:136`, `equities/params.py:123`). Eight tabular generators declare `train_ratio`/`test_ratio` as independent fields and need a validator **created**. Understated, not overstated |
| E-6 | R-5 rated HIGH, gating D-1 before Chunk 3 | **Fires in the deferred tier.** Every `assert_array_equal(X_full, concat([X_train, X_test]))` site is a *sequence* test. Chunk 3 (tabular) trips **zero** of them |
| E-7 | Chunk 3: *"`ALTER TABLE … ADD COLUMN n_val INTEGER`"* | **Drops `IF NOT EXISTS`.** All five precedents carry it and `SCHEMA_SQL` runs on every init — the second boot errors |
| E-8 | Chunk 2: *"update 3 fake assertions + 12 headers"* | **Under-scoped.** The fake **producers** (`testing/generators.py:101-105`, five functions) must emit `val`, or canopy's fakes test the old contract forever |
| E-9 | §5: *"Client before producer, confirmed by re-running Kahn's"* | **Wrong evidence.** There is **no edge** between them in `registry.yaml`; the index gap is a lexicographic tie-break artifact. The ordering rests on floor-resolvability (§5), not on the DAG |
| E-10 | §8: *"the two store roots"* | **Three** (C-11 said so; §8 contradicted the correction it certified) |
| E-11 | Chunk 6: *"the CLI gains `x_val` and early stopping"* | **Mis-sized.** The model already has it — `cascade_correlation.py:185` declares `x_val: np.ndarray`, exercised at `golden_support.py:199`. The work is **CLI plumbing only** |
| E-12 | Chunk 9 / R-9 cite `test_run_experiment.py:703` | **Two** rejection tests — `test_recurrence_bad_dataset_split_rejected` and `test_recurrence_bad_predict_split_rejected` — backed by two guards (`run_experiment.py:519`, `:557`) |
| E-13 | §2's *"~11 partition-of-unity"* and *"22 fixed-N"* counts | **Withdrawn.** Round 2 could not reconstruct either under any consistent definition. Unsourced counts removed rather than defended |

## 2. The detection surface

| tier | detection | fails how |
| --- | --- | --- |
| **juniper-data** | 5 exact-key gates in the **per-PR unit lane** (`tests/unit/test_{spiral,moon,gaussian,circles,checkerboard}_generator.py`, each `@pytest.mark.unit`) | **Loudly, on commit one** — but they are edited *inside* Chunk 3, so they stop detecting once that chunk lands |
| **juniper-data-client** | 3 exact-set assertions over the **fakes** (`tests/test_fake_client.py:43`, `test_fake_client_batch.py:39`, `test_npzfile_resource_lifecycle.py:95`) | Loudly — but only about the fakes |
| **cascor** | subset check (`data_provider.py:193-196`); every subsequent loop iterates `required_keys` | **Silently** — an `X_val` gets no shape validation at all |
| **canopy** | per-key presence + dtype + ndim ladder (`demo_mode.py:821-837`), `X_full` only | Silently |
| **recurrence** | `validate_npz_contract` (`data.py:77`); ingestion is **split-name-generic** (`sequence_data_from_arrays` reads `X_{split}` for any string) | Silently — and it can already read a `val` split today |
| **juniper-ml** | **exclusionary allow-list** — `RECURRENCE_SPLITS` (`run_experiment.py:149`), with two tests asserting `"validation"` is **rejected** | **Rejects outright** |

**The served artifact's own contract gate cannot currently fail anything.** `test_e2e_npz_keys_contract`
is `@pytest.mark.slow`, and the only lane running `slow` is schedule/dispatch-gated with
`|| echo "No slow tests found"` — the exit code is swallowed.

## 3. Decisions required before any code · **round-3 target**

> **RULED 2026-08-31 — both D-1 and D-2 are settled. Read the design of record, not this section.**
> The rulings live in [`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.2](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md)
> as decisions 6–8, together with a sub-ruling on normalisation fit scope that this section never
> asked for and that is load-bearing.
>
> - **D-1 → `X_full` is ASSEMBLED, not split.** The three subsets are generated first, each shuffled
>   and normalised, and `X_full` is their concatenation. This inverts today's flow and is *stronger*
>   than option (a) below: it makes the identity true by construction in the array-equality form,
>   not merely by length.
> - **Normalisation → fit on `train` only**, applied unchanged to `val` and `test`. Therefore
>   **`X_full` is deliberately not uniformly normalised**.
> - **D-2 → dataset-level row counts.** Ratios mean rows of the realised dataset, identically for
>   every generator regardless of its native size knob.
>
> **D-1's stated premise below is FALSE and is retained only as revision history** — see S-2 in §9.
> The clauses it cites are *length* identities, which shuffling cannot violate, and
> `test_e2e_workflow.py:299-301` asserts one and passes. The question was re-posed before it was put
> to the owner.
>
> **One new requirement is OPEN and gates the sizing work: prefix stability** (design §9.3). D-1's
> rationale is cross-snapshot dataset comparison under a shared seed; D-2 makes adding the third
> partition an ask for N+M rows instead of N; and V-1 *measured* that all six cascor-relevant
> generators return different rows in that case. So the ruling's own goal is unreachable until
> either generation is made prefix-stable or each partition draws from its own seed substream.

### D-1 — what does `X_full` mean under three partitions?

**Partly an existing divergence, not purely a new decision.** For tabular generators `X_full` is the
**unshuffled pre-split** array (`spiral/generator.py:60` returns `"X_full": X`) while train/test come
from `shuffle_and_split` — so `X_full == concat(X_train, X_test)` is *already false by content*
today, and the two normative clauses (`USER_MANUAL.md:367`, `JUNIPER_DATA_API.md:1001`) are already
violated by every shuffled tabular generator.

**Options the owner must choose between** (v2 posed the question with none):
(a) `full = train + val + test`; (b) `full = train + test`, val excluded; (c) retire `X_full`.

**Propagates to**: `DatasetMeta.n_samples` (`core/meta.py:61` computes `n_train + n_test`),
`test_e2e_workflow.py:317`, `n_samples INTEGER NOT NULL` in Postgres, and four normative documents
including the ecosystem `AGENTS.md`.

**Blast radius is in the DEFERRED tier** (E-6), so D-1 gates the sequence chunk, not Chunk 3.

### D-2 — how is additive sizing implemented?

Owner decision 2 mandates honouring the requested training count and **generating** extra points.
`split_data` raises when `train_ratio + test_ratio > 1.0` (`core/split.py:64-65`), so a
train-at-100 % model violates that function's own invariant — making `split.py` "three-way" **is**
the carve-up the design rejected.

Honouring it means changing per-generator **size** parameters, which are heterogeneous:
`n_points_per_spiral`, `n_points_per_quadrant` (xor), `n_samples_per_class` (gaussian),
`n_samples` (moon / circles / checkerboard), `n_samples: int | None` (mnist). **What "40 % of train"
means for a per-spiral knob is exactly the ruling required**, and v2 restated the heterogeneity as a
hazard without resolving it. Two cross-field validators exist; eight generators need one created.

**D-2 determines R-1's rating** (§7) and v2 did not say so: R-1 is self-mitigating only if the
ratios land as *request params*, and D-2's additive model changes *size* params instead.

## 4. Scope — every design decision homed

§6.1 rules → Chunk 4 · §6.1 marking obligations → **Chunk 9** (`validation_warnings` is a
**juniper-ml** manifest field: `run_experiment.py:256,1576,1927`; cascor has only a comment) +
Chunk 8 (dashboard) · §6.2 legacy compensation → Chunk 5 · §6.3 sizing → D-2, Chunk 3 · §6.4 gated
choice → Chunk 8 + Chunk 4 (headless) · §5 invariant → §6a · decision 1 → Chunks 3, 5 · decision 2 →
D-2, Chunk 3 · decision 3 → Chunks 4, 8 · decision 4 → Chunk 7 · decision 5 → Chunk 6 · V-3 →
Chunk 6 · §10 naming → Chunks 2, 3; casing in Chunk 4 · §7 snapshot provenance → Chunk 7.

**juniper-ml is a runtime consumer** (E-4) and its sites are homed: `run_experiment.py` allow-list →
Chunk 9; `plots_cascor.py:68,98` and `snapshot_attribute.py:318` → Chunk 7 (they read the corpus
the re-baseline touches); `ecosystem.yaml:32` → Chunk 3 (the contract declaration moves with the
contract).

**Out of scope, evidenced**: cascor-worker, cascor-client (zero references); `core/artifacts.py`
(key-blind passthrough); the crossval tier (D-CV-4). **Canopy's demo path is conditionally out of
scope** — unaffected only if D-1 leaves `X_full` semantics unchanged.

## 5. Dependencies and ordering

**Client before producer** — but *not* because the DAG says so (E-9). `registry.yaml` has **no edge**
between them. The real constraint is floor-resolvability: a consumer floor bump is unresolvable
until the new client is on PyPI, and Lockfile Freshness is a required gate in canopy, cascor and
data.

**Ceilings**: `juniper-data-client>=0.4.2,<0.5.0` — recurrence's **core runtime** dep. A 0.5.0 minor
is excluded; the release train *will* open that PR, but only for a MINOR bump (`propose.py:930`).
Note E-1: whether Chunk 2 warrants a minor at all is now open, since `NPZ_SPLITS` is fleet-inert.

**`DatasetMeta` fields must be defaulted** — required-with-no-default (`models.py:38-39`) loaded via
`DatasetMeta(**meta_dict)` (`local_fs.py:248`), against 19 `.meta.json` across three store roots.

## 6. Chunks

| # | chunk | if the NEXT never ships |
| --- | --- | --- |
| **1** | **Hygiene, unconditional.** Pin `NPZ_SPLITS`; pin `DatasetMeta`'s field set **including defaultedness** (a name-only pin misses R-3, the failure it exists to prevent); **delete** the orphaned golden fixtures (only *delete* is unconditional — *wire* depends on D-1, the fixtures lack `X_full` entirely, and `generate_golden_datasets.py:31`'s default cascor path does not exist). **Not** the slow-marker change — see Chunk 3 | Nothing. Owed regardless |
| **2** | **data-client**: fake **producers** emit `val` (E-8); 3 assertions; 12 headers. **No `contract.py` change** (E-1) — if a tabular validation branch is wanted it is new code, specified separately | Two-partition artifacts still validate |
| **3** | **data (tabular)**: D-2's sizing; 9 tabular generator dicts; `DatasetMeta.n_val` defaulted; `meta.py:61`; params schemas (2 validators inverted, 8 created); **six** Postgres sites with `ADD COLUMN IF NOT EXISTS` (E-7); `ecosystem.yaml:32`; generator `VERSION` bumps **first, not last**; and promote the served-artifact gate here, where its two sizing-dependent siblings are being edited anyway | Producer emits 8 keys; **the interval is camouflaged, not inert** (E-3) |
| **4** | **cascor**: consume `X_val`; §6.1 rules 1–3; **refuse** rather than return `(None, None)` when no eval split exists (deleting `_eval_split`'s fallback silently drops f1/precision/recall/roc_auc); widen `SpiralDatasetTuple`; pairing guard; the §6a gate; casing aligned **onto `X_val`** (lowercase breaks `juniper-model-core`'s conformance interface) | **This is the fix.** Without it #582 stays open |
| **5** | **data**: §6.2 generate-shortfall / re-partition, and the non-synthesisable exclusion class | Chunk 8's option 0 has no backend |
| **6** | **cascor CLI plumbing only** (E-11) — the model already accepts `x_val`; V-3 measures the effect | Tier parity not achieved |
| **7** | **Re-baseline** (decision 4) + §7 snapshot partition provenance + `plots_cascor.py`, `snapshot_attribute.py` | Pre/post results silently comparable when they are not |
| **8** | **canopy**: §6.4 four-option UI + dashboard-lifetime warning | Interactive users refused with no choice |
| **9** | **juniper-ml**: `RECURRENCE_SPLITS` + **both** rejection tests (E-12); `validation_warnings` manifest field | The harness cannot address the new partition |
| **3b** | **data (sequence)**: `_sequence.py`, `equities_seq`. **Gated by D-1** — this is where R-5 actually fires | Split contract persists |

### 6a. The consumer gate — corrected shape

Not exact-set (E-2). The gate must assert **presence and shape of the partitions the artifact
declares**, tolerating extra keys:

- `X_val` present ⟹ 2-D, same feature count as `X_train`, paired with `y_val` of matching rows.
- `X_val` absent ⟹ §6.1 rule 2's gated path, **not** a failure.
- Extra keys (`y_reg_*`, `t_*`, `ticker_vocab`, …) ⟹ ignored.

This also gives §5's invariant its first testable form: assert that the tensor bound to the
training loop's early-stopping signal is **not** the one reported as the final metric. v2 homed that
invariant to "Chunk 4 gate" and then described no gate.

## 7. Risks

| id | risk | rating | note |
| --- | --- | --- | --- |
| R-1 | Stale cached artifacts | **MEDIUM** | Self-mitigating **only if** ratios are request params — which **D-2 likely makes false** (§3). Chunk 3's `VERSION` bump is the unconditional mitigation; all 19 cached artifacts are at `1.0.0` across 5 generators |
| R-2 | Consumers accept silently | **HIGH** | §2. Addressed by §6a |
| R-3 | `DatasetMeta` bricks the store | **HIGH** | Default the field |
| R-4 | `ADD COLUMN NOT NULL` on a populated table; **and a missing `IF NOT EXISTS` breaks the second boot** | **HIGH** | E-7 |
| R-5 | `full == train + test` breakage | **MEDIUM** (was HIGH) | Fires in Chunk 3b, not Chunk 3 (E-6). Gated by D-1 |
| R-6 | Silent exclusion at `client<0.5.0` | **LOW** (was MEDIUM) | recurrence's reader is split-name-generic and can already read a `val` split at 0.4.x; only its t/dt validation is skipped |
| R-7 | cascor silently ignores a real `X_val` | **HIGH** (was MEDIUM) | E-3 — during Chunks 3→4 the artifact advertises compliance while the defect persists |
| R-8 | Split tabular/sequence contract | **MEDIUM** | Persists until 3b **and** §6a land |
| R-9 | ml harness rejects `"validation"` | **MEDIUM** | Two tests, two guards (E-12) |
| R-10 | Deployed stack skips release ceremony | **LOW** | — |

## 8. Consensus record (procedure §7)

- **Instrument**: 3 Lane A (distinct entry points, forbidden the design docs) → v1 → 3 Lane B
  (refute / opposing brief / omission-and-framing) → v2 → 2 round-2 lenses (what-the-rewrite-broke /
  fresh-engineer executability) → v3. **Could it have produced a different answer?** Repeatedly:
  round 1 overturned v1's founding measurement; round 2 caught a v2 prescription that would break
  every tabular artifact.
- **Sample size**: 8 agents, ~600 tool calls, 9 repos. Round 3 targeted, not yet run.
- **Iterations**: 2 complete. **Round 2 did not terminate** under §4 — it changed numbers, ratings
  and actions — so round 3 is owed on §3 (D-1/D-2), §6 Chunk 2, §6a, and §4's ml scope.
- **Independent convergence**: A1+A3 on the `NPZ_SPLITS` skip, subset blindness, Postgres
  `NOT NULL`, and the model tier's pre-existing `X_val`. B1+B2+B3 all returned *do not ship* on
  different grounds. **Both round-2 lenses independently flagged E-1** — the strongest signal in
  the record.
- **Reconciler re-derivation** (§5.2): every correction in §1 was personally re-derived before
  application — the five unit-lane gates, `_validate_sequence_split`'s raise, `validate_npz_contract`
  having no fleet consumer, the `|| echo` swallow, `cascade_correlation.py:185`, both rejection
  tests, `split_data:64-65`, the nullable migration precedents, and the **three** store roots.
- **Corrections that failed re-derivation, recorded rather than adopted**: B3 argued R-5's
  assertions would *hold* under additive sizing — they are hardcoded two-term and fail under either
  model. Its premise was right, its conclusion wrong.
- **Errors in my own certification, both from round 2**: v2's §8 said "two store roots" while its own
  C-11 said three; and v2 stated C-2's mechanism as a `;` marker on canopy's pyproject line, which
  has none — the skip happens because `[project.optional-dependencies]` renders as `; extra == …`
  in the *installed metadata*. Right conclusion, wrong stated mechanism, in a section claiming
  re-derivation.

### What this evidence cannot support

- **That v3 is correct.** v2 read as sound and contained a prescription that would have broken every
  tabular artifact in the ecosystem.
- **Runtime pass/fail.** No test body was executed at any point.
- **D-1 and D-2.** Owner rulings with no artifact to appeal to.
- **Whether `PostgresDatasetStore` is live.** Circumstantially dormant — its DDL declares
  `n_classes`/`class_distribution` `NOT NULL` while `DatasetMeta` allows both `None`, so the table
  is already incompatible with regression artifacts. If dormant, R-3 and R-4 are theoretical.
- **Effort or duration.** Not estimated. Chunking is by dependency and blast radius only.
- **That the ecosystem change is the right call.** One Lane B lens argued the defect has a ~36-line
  cascor-local fix needing no contract change, no release, and no re-baseline, and that the design's
  rejection of that option was argued against RNG-dependence a deterministic split does not have.
  **That case is not refuted here.** The owner elected to proceed with it on the record.

---

## 9. Round-3 findings — KNOWN-OPEN, not yet folded in

Round 3 (two lenses: four targeted items / what-the-second-rewrite-broke) returned **not resolved on
all four targets**. These are recorded verbatim rather than corrected in place, because correcting
them in place is exactly what produced the v2 and v3 defects. §§2–7 above are **v3-as-reviewed**.

### S-1 — STRUCTURAL, and upstream of both candidate designs

**cascor has no test-tensor slot.** `grep -c '_test_x' src/api/lifecycle/manager.py` → **0**.

`_eval_split()` (`manager.py:1902-1909`) returns `self._val_x, self._val_y` — the same tensors that
reach training (`_run_training` at `:2324`, `fit(val_x=…)` at `:2942`), sourced from
`arrays["X_test"]` at `:3451-3452`. So **repointing `_val_x` at a real `X_val` renames the leak
rather than removing it**: the reported `f1`/`precision`/`recall`/`roc_auc` still come from the rows
that drove early stopping, and `:2691` still labels the split `"validation"`.

Neither the ecosystem plan nor the cascor-local alternative can deliver the design's §5 row
(*"`test` | the final reported score | **exactly once**"*) without adding a third tensor pair.
**This question must be answered before either design can be specified.**

### S-2 — D-1's premise is false (my error, introduced in v3)

§3 claims `full == train + test` is "already false by content" for shuffled tabular generators. The
two normative clauses read `len(X_train) + len(X_test) == len(X_full)` — **length** identities, which
shuffling cannot violate — and `test_e2e_workflow.py:299-301` asserts it, passing today.

What is actually true: the **array-equality** form fails for shuffled tabular generators (order, not
content), and the length clause is *violable via request params* — all ten generators accept
`train_ratio + test_ratio < 1.0`, since the two cross-field validators reject only `> 1.0`. The
sequence tier honours concatenation exactly.

A **fourth D-1 option** is live and unstated: ratify the current superset semantics (`X_full` is the
raw pre-split array, not required to equal any concatenation). Option (a) would *newly constrain*
nine currently-unconstrained generators.

### S-3 — v3 cut the legitimate half of E-1

`validate_npz_contract` **does** have a fleet consumer — `juniper-recurrence/.../data.py:77` calls it
as a "full-contract gate", and §2 above says so, contradicting §1's E-1. E-1 conflated the *function*
with the *constant*.

Consequence: extending `NPZ_SPLITS` with `"val"` — the only thing that makes a sequence artifact's
`t_val`/`dt_val`/mask rules validated — is now owned by **no chunk**, while Chunk 1 *pins* the
3-tuple, freezing the gap. After Chunk 3b, recurrence would read a `val` split that
`validate_npz_contract` never validates. Restore it and Chunk 2 earns its minor; leave it out and
Chunk 2 is three cosmetic edits.

#### S-3 CONFIRMED 2026-09-01 — re-derived from source

Both halves check out, and the distinction S-3 draws is exactly the one E-1 lost.

- **The CONSTANT is contract-internal.** `NPZ_SPLITS: Tuple[str, ...] = ("train", "test", "full")` is
  declared at `juniper_data_client/constants.py:421` and referenced in exactly two places, both
  inside `contract.py` — the import at `:39` and `for split in NPZ_SPLITS:` at `:75`. E-1's claim was
  true *of the constant*.
- **The FUNCTION has a fleet consumer.** `juniper-recurrence/juniper_recurrence/data.py:18` does
  `from juniper_data_client import JuniperDataClient, validate_npz_contract` — a module-level import
  on the app's data-fetch path, its own docstring calling it the *"full-contract validator"*.
  `juniper-recurrence-model/juniper_recurrence_model/data.py` applies a deliberate strict subset.
  E-1's claim was **false of the function**, and §2's detection table said so all along.

Path note: the checkout root `juniper-recurrence/` contains a package directory of the same name, so
the doubled `juniper-recurrence/juniper-recurrence/juniper_recurrence/data.py` is correct from the
ecosystem root. There is **no `src/`** in that repo — a `src/`-bearing path does not resolve.

The consequence stands exactly as stated above.

### S-4 — §6a rejects every sequence val artifact

§6a specifies "`X_val` present ⟹ **2-D**". Sequence `X_*` is 3-D `(W, L, F)`. It needs the ndim
dispatch `contract.py:67-73` already has. Its "extras ignored" clause also blesses an equities
artifact missing `y_reg_val`, after which `resolve_target_key` silently falls back from the
regression target to the direction one-hot.

### S-5 — three of four juniper-ml homes are wrong

`plots_cascor.py` — wrong lines (`:69`/`:73`, not `:68`/`:98`) and wrong chunk (it reads the run's
NPZ, so Chunk 3/4). `snapshot_attribute.py:318` reads **live generator output**, so it is a D-1 site.
`ecosystem.yaml:32` is **documentation-only** — nothing reads `npz_contract:` — and homing an
ml-repo file in a juniper-data chunk makes that chunk cross-repo. Still unhomed:
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:218`, the existing bias-measurement instruments
(`suites/p4/e-o-val-split-bias-cap4.yaml`, `util/ad-hoc/2026-08-29_val_split_bias_collect.py`), and
`docs/REFERENCE.md:1679`.

### S-6 — the store-root count was VACUOUS, and R-3 is under-sized

E-10's "19 across three roots" is `18 + 1` — exactly what a host filesystem sweep can see.
`/var/lib/docker/volumes` is root-only, so the **live** volume enumerated as *empty* rather than
erroring, and the total still read plausible.

Measured via `docker exec`: **4** `juniper-data-datasets` volumes; `juniper-data` `Up 2 weeks
(healthy)`; **5** `.meta.json` in the live volume, of which **≥2 exist nowhere on the host**. At
least four reachable roots, 29 files across the enumerable ones, no upper bound until three stale
worktree-named volumes are read as root.

**R-3's blast radius therefore includes a store this plan did not know existed** — two weeks stale
relative to every working tree, read through `DatasetMeta(**meta_dict)` (`local_fs.py:248`).

#### S-6 RESOLVED 2026-09-01 — full census taken, and R-4 is DEAD CODE

S-6 said *"no upper bound until three stale worktree-named volumes are read as root."* They do not
need root: `docker run --rm -v <volume>:/x alpine ls /x` reads any named volume without touching
`/var/lib/docker/volumes`. Census taken that way.

| root | `.meta.json` | distinct contribution |
| --- | --- | --- |
| `juniper-deploy_juniper-data-datasets` (**live**; `juniper-data` Up healthy) | **10** | 10 |
| `juniper-deploy--fix--canopy-demo-ws-origin-allowlist--…` | 1 | **0** |
| `juniper-deploy--fix--cascor-demo-juniper-data-api-key--…` | 1 | **0** |
| `juniper-deploy--fix--demo-seed-x-api-key--…` | 1 | **0** |
| host `juniper-data/data/datasets/` | **18** | 16 |

**5 reachable roots, 26 distinct artifacts** — against §8's "19 across three roots" and S-6's own
"≥4 roots, 29 files".

- **The three stale volumes are redundant, not unbounded.** Each holds exactly one file; all three
  hold the *same* file (`spiral-1.0.0-ff889b96de118f5c.meta.json`); and it is already in the live
  volume. They contribute **zero** distinct artifacts. S-6's "no upper bound" was over-cautious.
- **The live volume and the host directory are near-disjoint.** 8 of the live 10 exist nowhere in the
  host directory; 16 of the host 18 exist nowhere in the live volume; only 2 are shared. Neither root
  enumerates the other — which is precisely why a host sweep produced a plausible-but-wrong total.
- **The live count is volatile**: 5 on 2026-08-31, 10 on 2026-09-01. Treat any figure here as a
  sample, not a constant.

**R-4 is THEORETICAL — `PostgresDatasetStore` has no production construction site.** `api/app.py:42`
unconditionally builds `LocalFSDatasetStore(storage_path)`; no env var, setting or branch selects
Postgres. `get_postgres_store()` exists, but every call to it and every `PostgresDatasetStore(...)`
construction is **in tests** (`tests/unit/test_storage.py:660`;
`tests/unit/test_postgres_store.py:86,95,113,122`). R-4's `ADD COLUMN` / `IF NOT EXISTS` /
`NOT NULL` failure modes cannot fire in the served path. §8's *"circumstantially dormant"* is
confirmed as **structurally dormant**. **Downgrade R-4 from HIGH.**

**R-3 stays HIGH — but it is a LocalFS risk, not a Postgres one.** The live mechanism is
`DatasetMeta(**meta_dict)` at `storage/local_fs.py:249` (**S-6 and §5 say `:248` — off by one**),
against `n_train: int` / `n_test: int` declared **required with no default** at
`core/models.py:38-39`. An `n_val: int` added without a default fails **all 26** existing artifacts
on load. The stated mitigation — default the field — is correct, and is the whole of it.

### S-7 — side-finding: a stale local env is justifying dead code

`juniper-canopy/src/demo_mode.py:1845` justifies a hand-rolled rank probe on the grounds that
`validate_npz_contract` is *"absent from the pinned / published juniper-data-client (0.4.x)"*. The
live canopy container runs **0.4.2** and the module is **present**; only the local `JuniperCanopy1`
env (0.4.1) lacks it — and that env is behind the container *within the same pin range*. The comment
is false in production. Unrelated to this arc; worth its own ticket.

#### S-7 FILED 2026-09-01 — juniper-canopy#559

Re-verified before filing, against the container rather than the host:
`docker exec juniper-canopy` reports `juniper-data-client` **0.4.2** with `validate_npz_contract`
**present**; `/opt/miniforge3/envs/JuniperCanopy1` reports **0.4.1**, **absent**. canopy pins
`juniper-data-client>=0.4.1,<0.5.0` (`pyproject.toml:148`), so the comment is defensible about the
**floor** and wrong about the **range** — the function landed inside `0.4.x`.

The ticket records one thing this arc did **not** check: whether `validate_npz_contract` is a
behavioural drop-in for the current probe. The probe dispatches on `ndim == 3` only, while the shared
function validates a full contract, so swapping them could turn a permissive path strict. That needs
checking before the swap, and the ticket says so.

### The failure mode this document keeps exhibiting

Across three rounds the *conclusions* mostly survived and the *evidence* did not: E-3 cited the
reporting split for a training-binding claim; E-1 cited the function for a claim true of the
constant; D-1 cited content for a clause about length; the store count used a filesystem sweep for a
store that lives in a volume. Each time the artifact checked was *adjacent* to the one that could
falsify the claim. Every instance was caught by re-derivation, none by re-reading — which is the
procedure's §5.2 earning its cost.
