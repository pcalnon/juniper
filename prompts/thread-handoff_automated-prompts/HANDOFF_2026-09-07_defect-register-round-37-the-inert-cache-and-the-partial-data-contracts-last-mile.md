# HANDOFF 2026-09-07 — round 37: an inert cache that no test could see, two NaN guards, and the partial-data contract's last mile

Successor to
`HANDOFF_2026-09-05_defect-register-round-36-the-partial-data-contract-closed-and-a-live-data-corruption-fixed.md`
— cite this one by its full name.

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`). Its own validation status is §7. **Round 36's
validators were wrong on two of seven verdicts, both times falsifying a true claim** — §4 — so treat
consensus here as evidence, not proof, and re-derive any number you intend to act on.

**A bare "§N" means a section OF this document.** Every reference to a section of any other file
names that file. All dates UTC.

**Register: 79 fixed / 17 open, unchanged. `APD-DATA-019` was RE-SCOPED, not closed.** Of the 17
open, 16 are parked; `-019` is the one unparked row and §0.4 says what actually remains under it.

---

## 0. Remaining work

1. **Successor, first — validate this document (§7).** No round has run on it.

2. **`juniper-canopy`'s three-way prompt — the ONLY unbuilt piece of the partial-data contract, and
   every blocker is now merged.** The owner's ruling is settled and must not be re-litigated:
   **option 3 (fail) is the one that cancels the load and deselects the dataset**; accept and drop
   both continue and annotate.
   - Canopy has **zero** occurrences of `allow_truncation`. Its code lives under `src/`, not
     `juniper_canopy/` (which holds only `__init__.py`).
   - The wire path already exists: `StageDatasetRequest.nn_dataset_params` (`src/main.py`) is a
     free-form dict forwarded verbatim to cascor's `params`. Canopy needs to *populate* it, not
     plumb it.
   - The field to render is **`dataset_shortfall`** on `GET /v1/training/status` — `null` when
     clean, otherwise `dataset_id`, `accepted_via_allow_truncated_datasets`, `truncation`,
     `data_quality`, `summary`.
   - **⚠ CORRECTED BY VALIDATION: it does NOT ride the WS stream in any useful sense.** An earlier
     draft said it did, inheriting the claim from cascor's own CHANGELOG without checking.
     `get_status()` is reached from the WS layer at **exactly one** place —
     `src/api/websocket/training_stream.py:96`, inside `_send_initial_state`, which emits a one-shot
     `{"type": "initial_status"}` **at connect**. There is no status frame in the broadcast set
     (metrics / cascade_add / event / candidate_progress / state / topology), and `create_state_message`
     reads `training_state.get_state()`, a different source. **A client already connected when
     `_reload_dataset` sets the field never sees it over WS** — which is exactly canopy's case, since
     the prompt fires at dataset-apply time. Canopy must POLL `/v1/training/status`, or cascor needs a
     new broadcast frame. Budget for that; do not assume the stream carries it.
   - UI entry points: `src/frontend/components/parameters_panel.py`, `src/dataset_schema.py`, and
     the flows pinned by `src/tests/integration/test_apply_dataset_flow.py`.

3. **⚠ OPTION 3 IS NOT ENFORCEABLE END TO END — but the cause is a DESIGN DECISION, not an
   oversight. Read this whole item before proposing a fix.**

   juniper-data **ORs** the request parameter with its own env var, at three sites on today's
   `main`: `equities/generator.py:471` and `:501`, and `csv_import/generator.py:153`. (An earlier
   draft cited `:468`/`:498`/`:148` — those were the numbers before data#369 shifted them on
   2026-09-06, so they were **already stale when written**. Re-derive rather than trusting either
   set.)

   ```python
   allow = bool(params.allow_truncation or settings.equities_allow_truncation)
   ```

   So a request **cannot opt out** once `JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION` is set. There is no
   upstream escape: the route calls `bind_deployment_defaults` (which ORs again) and the only 422
   comes from `InputTooLargeError` / `IncompleteDataError`, raised solely under `not allow_truncation`.

   **This is intentional and pinned.** `generator.py`'s own docstring says *"A client cannot opt out
   of the operator's choice"*, it is documented in `docs/REFERENCE.md` and `CHANGELOG.md`, and
   `tests/unit/test_csv_import_generator.py:726` is
   `test_request_cannot_opt_out_of_deployment_allow_truncation`. **An earlier draft of this document
   said "prefer fixing the OR" — that would invert a privilege model juniper-data deliberately
   encodes, and is withdrawn.** The real question for the owner is whether option 3 should be a
   *caller* right at all, or whether "the operator opted the deployment in" is simply the answer.

   **And cascor#624's remedy is NOT portable here.** #624 fixed a dict-merge ORDER bug with a
   presence test (`"allow_truncation" not in jd_params`). juniper-data declares
   `allow_truncation: bool = Field(default=...)` — a plain `bool`, not `bool | None`, with nothing
   reading `model_fields_set` — so **explicit `false` is indistinguishable from omitted**. Expressing
   option 3 caller-side would require a schema change, not a one-line guard.

   Neither env var is set in juniper-deploy today (zero occurrences, tracked or untracked), so the
   hole is **latent** — assert that before claiming the contract holds end to end.

4. **`APD-DATA-019`, re-scoped 2026-09-07 — what remains is the storage index, NOT `total`.**
   `total = len(filtered)` is a **negligible** share of the call (measured between 0.0000041% and
   0.000012% depending on run — the third significant figure is not supportable, the conclusion is
   beyond dispute) and has **zero in-tree consumers**; do **not** re-file it as a `total` problem
   (the row now says so explicitly).
   **But "absent" is NOT free**, contrary to an earlier draft's implication: `total` is a *required*
   field of the live `/v1/datasets/filter` schema, and `docs/api/JUNIPER_DATA_API.md:63` publishes
   *"Response fields will NOT be removed within a major version"*, with `:75` naming removal as
   breaking. Dropping it is a **MAJOR** bump regardless of who consumes it. The O(N) floor is
   `list_all_metadata()` at 96.8%, which juniper-data#381 *bounds* with the cache but does not
   remove. At the deployed **N=21** `/filter` costs ~3 ms, so this is latent. A real fix pushes
   filter/sort/limit into each store.

   **CORRECTED BY VALIDATION:** an earlier draft warned that "Postgres already pushes down
   `LIMIT/OFFSET` (`postgres_store.py:519`), so a LocalFS-shaped fix would regress it." That
   pushdown is in **`list_datasets`**, which is **not on the `/filter` path**. `filter_datasets`
   reads `_list_all_metadata_cached()` → `list_all_metadata()`, and Postgres's `list_all_metadata()`
   is `SELECT * FROM datasets ORDER BY created_at DESC` with **no LIMIT and no OFFSET**. On the very
   method this row was re-scoped onto, **Postgres pushes down nothing** — so it needs the index work
   as much as LocalFS does, not less.

5. **Four cascor follow-ups, filed in cascor#624's PR body and still unbuilt:**
   - `get_metrics()` / `/v1/metrics` carry no shortfall annotation.
   - `--allow-truncated-datasets` is **inert on `main.py`'s own run path** — its only consumer is in
     the *service* process, and `main.py` reaches only `spiral`, which is not truncatable.
   - `_auto_start_training` (`src/api/app.py`) neither forwards the opt-in nor surfaces its failure;
     `except Exception: logger.exception(...)` leaves the service up and healthy with no training.
   - **No `.md` or `.env` file** in cascor, data, canopy or ml mentions `--allow-truncated-datasets`
     or `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS` — including every `AGENTS.md`, `README.md`,
     `.env.example` and the ~30 `docs/*.md` env-var tables. (An earlier draft said "zero docs";
     cascor's `CHANGELOG.md` **does** document the knob at length under the settings-field name
     `allow_truncated_datasets`. The gap is operator-facing documentation, not the record.)

6. **Three look-ahead paths still shipping in `equities`** — found by round 36's validation, never
   actioned, all verified still present 2026-09-07:
   - **`adj_close`** (`auto_adjust=False` at `generator.py:785`; the column is built at `:625`/`:804`): Yahoo retroactively restates it for
     every future split/dividend. Understated when filed — `close` itself is split-adjusted too, so
     the leak is in `open/high/low/close`, `week52_*`, `cost_basis`, `next_close` and `y_reg`; what
     `adj_close` *uniquely* adds is a future-dividend channel (`close/adj_close` is cumulative
     dividends from that row to series end).
   - **`cost_basis`** (`:758`): a per-ticker constant written to **every** row including earlier
     ones. Inert at the default `purchase_date`, a full future-price leak at any later one — and
     `purchase_date` is a plain field reachable through the public API.
   - **`_SHARES_OUTLIER_FACTOR`** (`:79`): filters share points against a **whole-history median**,
     i.e. which points survive depends on filings made after the affected rows. 61 of 485 tickers
     lose ≥1 point (re-derived exactly); **15 or 16** would keep a different set under a causal median — the count is definition-dependent and this document never fixed the rule, so pin the definition before quoting it.

7. **A second, unfiled defect in the same shares path.** `_fetch_shares` keeps the *latest-filed*
   fact per period end (`generator.py:918-923`), so an 8-K that merely **re-states** an old figure
   rewrites that figure's publication date — the original point vanishes and earlier rows keep the
   *previous* quarter's count. Direction is **stale, not leaky**, so no look-ahead test can see it.

   **CORRECTED BY VALIDATION, twice.** An earlier draft said "rows 2013-02-27..2013-04-24 (40 trading
   days) **understated** 0.638%". The magnitude and window are exact, but:
   - **The direction is inverted — it is OVERSTATED.** Re-derived from the cached KO payload: those
     rows ship 4,485,161,506 (the 2012-10-22 figure) where 4,456,717,996 (2013-02-25) is correct,
     i.e. **+0.63822%**.
   - **40 days is one of three episodes.** KO's full exposure is **103 trading days**:
     2013-02-27..04-24 (40 d, +0.638%), 2016-02-25..04-27 (44 d, +0.450%), 2024-05-02..05-29
     (19 d, +0.104%).

8. **Unfiled fork-drift row.** `_PROJECT_API_TRUNCATABLE_GENERATORS` duplicates knowledge owned by
   juniper-data, **and two thirds of it is unreachable** — cascor's `dataset_type` Literal
   (`src/api/models/training.py:235`) excludes `csv_import` and `equities_seq`, so only `equities`
   can reach the line that reads the flag.

9. **The SEC shares cache can disagree with the endpoint indefinitely.** Its key is **CIK only** —
   `_CACHE_DIR / "shares" / f"{cik:010d}.json"` (`generator.py:866`) — with no version, no
   `generator_version`, no TTL and no mtime check (`if use_cache and cache.exists()`, `:868`).
   Contrast `:771`, where the OHLCV key *does* include its date range. Consequences, both carried
   from round 35's validation and still unactioned:
   - `EQUITIES_DEFAULT_USE_CACHE = True`, so **on a warm cache the generator never executes the
     empty-units guard and never reaches the rescue ladder** — the "451 → 463" and "≥28 of 37"
     figures describe **cold-cache** behaviour only.
   - A payload cached between 2026-06-03 and the truthy-empty fix would hold
     `{"units": {"shares": {}}}` and **permanently** short-circuit both rescue paths for that CIK.
     Latent on this machine (0 of 485 cached payloads are empty) but real.
   - This is also why the `companyconcept` gap reads as permanent when it is an **upstream
     regression**: the June-2026 cache and the September endpoint disagree, and nothing reconciles
     them.

10. **A stale comment that contradicts the evidence underneath it.** `generator.py:733` says KO and
    ABT report "no shares concept to SEC at all" — but the cache holds **71 dei points for KO**
    (CIK 21344), and §0.7's whole measurement depends on them. It is a leftover from before the
    rescue ladder; fix it when touching that file.

11. **The other 16 open register rows are PARKED and need owner unparking before any session may
    action them.** That is the register's own operating rule, not a preference — do not action one
    on your own judgement.

12. **NEW, found validating this document — `equities_seq` binds no deployment defaults, and that
    poisons its cache key.** `bind_deployment_defaults` is defined only on `EquitiesGenerator`
    (`equities/generator.py:505`); the route looks it up with
    `getattr(generator_class, "bind_deployment_defaults", None)` (`api/routes/datasets.py:146`), so
    for `equities_seq` **nothing is bound** — while `equities_seq.generate` still calls
    `EquitiesGenerator._resolve_symbols`, i.e. the same OR. Consequence: `generate_dataset_id`
    hashes the *schema* defaults (`allow_truncation=False`) instead of the effective policy, so
    **two requests under different truncation policies collide on one `dataset_id`**, and toggling
    the env var keeps serving the artifact built under the old one. `equities_seq` is registered and
    advertised in `docs/REFERENCE.md`. This is a live cache-poisoning path and a **third** OR
    consumer that §0.3 does not name.

13. **NEW — `accepted_via_allow_truncated_datasets` can be FALSE on a run that trained on partial
    data.** cascor builds it from its own `Settings().allow_truncated_datasets`
    (`manager.py:3933` → `:3725`), not from the effective outcome. If juniper-data's env var forces
    acceptance (§0.3) while cascor's flag is off, the run gets a non-null `dataset_shortfall` whose
    `accepted_via_allow_truncated_datasets` reads `false` — **the annotation denies the acceptance it
    is annotating**. This is a defect in cascor#624's own field, it is the field §0.2 tells canopy to
    render, and it should be fixed before canopy renders it: derive the flag from the producer's
    response, or drop the field rather than state something false.

---

## 1. Verify starting state

Run each line standalone (§5.1).

```bash
git fetch origin
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
python3 util/ad-hoc/register_open_set.py
python3 util/ad-hoc/register_status_crosscheck.py
```

Expected, measured 2026-09-07: FIXED rows **79**; open-set **`96 rows | 79 fixed | 17 open`**;
cross-check **79 / 79 / 79, AGREE**.

---

## 2. What this session did

| PR | Result |
|---|---|
| **data#381** | **MERGED** (`c8f09fe`). **The JD-PERF-02 metadata cache was INERT in production.** 6 of 7 stores never called `super().__init__()`, so `_list_all_metadata_cached` silently degraded to an uncached walk — including on `LocalFSDatasetStore`, the store `api/app.py` wires. **Order 100× at N=100 and N=1,000** — measured 96.6–148.3× and 77.4–163.2× across four runs, so quote the order, not four significant figures. |
| **cascor#630** | **MERGED** (`1ea2062`). `_artifact_to_tensors` refuses NaN/Inf by name, all six arrays, with the count and the producer-side remedy in the message. |
| **recurrence#151** | **MERGED** (`e5679b0`). The regression target is now finiteness-checked, as `X` and `dt` already were. |
| **ml#1813** | `APD-DATA-019` re-scoped off `total` and onto `list_all_metadata()`. |

All four merge SHAs verified as **ancestors** of their repo's `origin/main`, not merely resolvable.

Round 36's five PRs (data#376/#377, cascor#621/#624, ml#1791/#1795) all merged; **data#378 (the
`fundamentals_fill="nan"` default) was merged by the owner** at 2026-09-05T22:06 as `005a82b`.

---

## 3. Owner rulings — do not re-litigate

| Date | Question | Ruling |
|---|---|---|
| 09-05 | Option numbering in the partial-data spec | **Option 3 (fail)** cancels and deselects |
| 09-05 | The 3 tickers rescuable only via `CommonStockSharesIssued` | **Add the rung, annotated as its own degraded basis** (`issued_includes_treasury`) |
| 09-05 | Whether STZ needs more than refusal | **No** |
| 09-05 | `fundamentals_fill` default | **`"nan"`** — shipped |
| 09-07 | `APD-DATA-019` disposition | **Re-scope to the real cost**, keep open |
| 09-07 | The inert cache | **Fix it properly now** (done, data#381) |
| 09-07 | NaN follow-up | **Guard cascor AND recurrence's `y`** (done) |
| 09-07 | The NaN record | **Add the measured numbers** (done) |

---

## 4. Where consensus was wrong, and how it was caught

Round 36's adversarial validators falsified two true claims. **Both were caught by reading the
source, not by a third opinion:**

- They said the default `start_date` is **2015**, so the NaN span is empty. It is
  **`2000-01-01`** (`defaults.py:17`). Measured across the 485-payload cache: earliest first filing
  **2009-04-15**, median **2009-12-18**, **mean 43.1%** of a default window precedes the first
  filing — **as of 2026-09-07, and it drifts**, because `EQUITIES_DEFAULT_END_DATE = None` means the
  window ends at the wall clock (44.3% on 2026-01-01, 46.0% a year earlier). Always state the as-of
  date.

  **The denominator is 485 CIKs that HAVE a cached payload, not the universe.** The bundled default
  universe is **503 tickers / 500 CIKs**, and **15 members have no cached SEC payload at all** (EL,
  TSN, RL, META, XYZ, ABNB, TTD, STZ, DASH, TKO, UHS, HRL, MKC, LEN, ERIE). That *strengthens* the
  conclusion — those 15 lack shares data for 100% of the window — and moves the universe-wide mean to
  **44.85%**. An earlier draft said "0 of 485 tickers exempt", which is really "0 of the 485 we
  looked at".
- They said `days_since_report` is NaN from a separate path. `generator.py:751-752` fills it **only**
  under `fundamentals_fill == "zero"`.

They were right where it mattered most, and where the previous session was wrong: **`equities_seq`
does not feed the recurrence tier** in any harmful way — it is barred from cascor at three layers,
and the recurrence tier rejects non-finite `X` by name.

**The lesson worth carrying: divide the numbers yourself.** See memory
`reference_cap_unit_must_be_measurable_ex_ante` and `reference_drift_band_13_to_20_5_stands`.

---

## 5. Traps

### 5.1 The sandbox refuses shell STRUCTURE
Loops, `${PIPESTATUS}`, heredocs, `cd … && … && git …` chains, `gh api` with a path built inside a
larger construct, and `sleep` followed by another command — all refused. Split into plain commands.
**cwd does not persist.** Heredocs into `python3 -` DO work and were the workhorse this round.

### 5.2 A `# noqa` that satisfies ruff and not CodeQL is worse than none
data#381 was blocked twice by CodeQL on **my own test code**: `py/side-effect-in-assert` (a mutation
inside an `assert` vanishes under `python -O`, so the test passes having deleted nothing) and
`py/unused-import` on three imports kept for their subclass-registration side effect — each already
carrying `# noqa: F401`. The fix that works is `importlib.import_module(...)`: a **call**, not an
import. Same pattern as canopy#585.

### 5.3 A broken thing masks the next one — in the tests
While a store's cache is **inert**, its read-your-writes tests pass **trivially**: there is no cache
to go stale. Fixing only the store the validator named would have left three arms meaningless.
Always ask what the test can still detect once the first defect is gone.

### 5.4 The census caught its own stub
Walking `DatasetStore.__subclasses__()` found the test file's `_CountingStore`. Scope such a census
to the production package (`sub.__module__.startswith("juniper_data.storage")`) or it fails for a
reason it does not care about.

### 5.5 A skipped arm pins nothing
The recurrence `y_train` fallback arm originally `pytest.skip`ped when the fixture did not emit that
key. Make the fixture reach the branch (here: pop `y_reg_train`) instead of skipping past it.

### 5.6 Environments
juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python` (pass `-p juniper_data.api.app`, a
circular import otherwise). juniper-cascor → `.../JuniperCascor1/bin/python` — **note the trailing
`1`**; the unsuffixed names are `-DEPRECATED` on disk. **juniper-recurrence has NO conda env**:
borrow one and set `PYTHONPATH=juniper-recurrence-model`, or a stale installed copy shadows the
worktree. In that borrowed env `test_crossval.py` does not collect (stale `juniper_model_core`) and
one torch test skips — both pre-existing, reproduced on an unmodified checkout.

### 5.7 Golden snapshots need three collection gates
`GOLDEN_CAPTURE=1 pytest -m golden --golden --slow --integration src/tests/integration`. `--slow`
alone still skips.

---

## 6. Git status

Written from harness worktree `compiled-inventing-sprout`, branch `docs/rescope-apd-data-019`.

Worktrees created this round and **deliberately not removed** (cleanup needs the owner's explicit
signal, and `git worktree remove` deletes ignored files):

- `juniper-data--fix--metadata-cache-inert--20260907-0837--a1fc2876`
- `juniper-cascor--fix--reject-non-finite-artifacts--20260907-0930--60371871`
- `juniper-recurrence--fix--guard-y-non-finite--20260907-0950`

Plus five from round 36, all merged. Two pre-existing juniper-data stash entries belong to other
sessions and were left untouched.

---

## 7. Validation of this document

**TWO ADVERSARIAL ROUNDS RUN (2026-09-07). Both found real errors in it; all are corrected above and
the corrections were re-derived from source before being applied.** What they changed:

| Claim as first written | Verdict |
|---|---|
| "prefer fixing the OR" in §0.3 | **Withdrawn** — the OR is deliberate, documented in five places, and pinned by `test_request_cannot_opt_out_of_deployment_allow_truncation` |
| "it also rides the WS training stream" | **Wrong for canopy's case** — `get_status()` reaches WS only in a one-shot at connect |
| "Postgres already pushes down, so a LocalFS-shaped fix would regress it" | **Wrong method** — the pushdown is in `list_datasets`, not on the `/filter` path |
| §0.7 "understated 0.638%" | **Direction inverted** — it is OVERSTATED, and 40 days is 1 of 3 episodes totalling 103 |
| "0 of 485 tickers exempt" | **Wrong denominator** — 485 CIKs *with a payload*; the universe is 503/500 and 15 have none |
| "114.8× / 92.9×" | **Unsupportable precision** — run-to-run spread is ~2× |
| "zero non-test consumers ⇒ absent is cheap" | **Incomplete** — removal is a MAJOR bump on a published contract |
| §8 marking ml#1813 done | **It is still OPEN** |
| Three cited line numbers | **Stale on the day written** (data#369 had shifted them) |

**A third round is owed**, because §0.11–§0.13 were added *by* validation and have had none. Attack
in this order:

1. **§0.3 — that juniper-data's `or settings.*` makes option 3 unenforceable.** Highest-cost claim
   here: it says a shipped contract has a hole. Re-derive from source.
2. **§0.6's three look-ahead paths** — are they reachable at DEFAULT parameters, or only through
   non-default values? The previous round over-claimed exactly this shape.
3. **§2's PR table** — verify each merge SHA is an ancestor of the right `main`, not merely resolvable.
4. **§4's measurements** — re-derive 43.1% and the 114.8× independently. Do not accept them because
   this document is confident.
5. **§1's expected values.**

---

## 8. Session-close checklist

- [x] Both open decisions closed interactively with the owner (§3)
- [x] The inert cache fixed across all 7 stores, with a non-vacuous conformance suite (data#381)
- [x] NaN guards added at both consumer boundaries (cascor#630, recurrence#151)
- [ ] **`APD-DATA-019` re-scope — ml#1813 is still OPEN**, refused twice by `safe_merge` on
      juniper-ml main-churn ("went BEHIND 3 times without a stable green head"). The re-scoped row
      exists only on the PR head; `origin/main` still carries the old `total`-scoped wording. Merge
      it, or the next session reads the superseded text.
- [x] Handoff generated (this file)
- [ ] **juniper-canopy three-way prompt — the last piece of the contract (§0.2)**
- [ ] **The `or settings.*` hole in juniper-data (§0.3) — option 3 is not enforceable without it**
- [ ] The four cascor follow-ups (§0.5)
- [ ] The three look-ahead paths and the 8-K restatement defect (§0.6, §0.7)
- [ ] File the `_PROJECT_API_TRUNCATABLE_GENERATORS` fork-drift row (§0.8)
- [ ] The CIK-only SEC shares cache key — no version, no TTL (§0.9)
- [ ] Owner unparking, if any of the other 16 open rows are to be actioned (§0.11)
- [ ] `equities_seq` binds no deployment defaults — live cache-key collision (§0.12)
- [ ] `accepted_via_allow_truncated_datasets` can deny the acceptance it annotates (§0.13)
