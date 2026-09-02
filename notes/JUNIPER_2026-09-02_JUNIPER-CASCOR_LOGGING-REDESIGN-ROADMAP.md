# Logging redesign — development roadmap

**Project**: Juniper
**Sub-Project**: juniper-cascor (`src/log_config/`), with ecosystem touchpoints
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-09-02
**Status**: ROADMAP — phases, steps, dependencies, concurrency and guardrails for [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573)
**Evidence base**: [`JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md) (below: **RECON**)
**Measured at**: cascor `70edfc4`

> **Path convention.** Scripts live in two repos. Every path below is prefixed:
> `juniper-ml/util/…` or `juniper-cascor/…`. An unprefixed `util/` path is a defect — three
> guardrails in the first draft cited juniper-ml scripts as if they were in cascor.
>
> **Anchoring.** Line numbers are at `70edfc4`; anchor on the quoted text, not the number.

---

## 1. Scope

### In scope

| # | from | what |
| --- | --- | --- |
| 1 | #573 scope 1 | A console sink that can be turned off independently of the file sink. **Owner decision 4 stands: the stream stays stdout** (provisional). This item is about *disableability*, not relocation |
| 2 | #573 scope 2 | Richer sinks — a sink abstraction, formatted and optionally colourised console output, explicit rotation with a single owner |
| 3 | #573 scope 3 | Per-logger levels, from config file **and** environment variable |
| 4 | #573 scope 4 | Structured export — JSON as a second sink; the ELK shipper itself stays deferred |
| 5 | RECON N-3 / N-3a / N-3b | **The level system**: the guard predicate and the emit filter read disjoint state; `is_valid_level` returns `True` for everything; one contradicting level table |
| 6 | design F-1 residue | `frame`/`tsp` eager evaluation (revised-order item 3, 1.0 % pre-#598) |
| 7 | design F-2 | Per-record `open()` |
| 8 | design F-4a | Per-record closure construction — **seven** closures per record, not two (RECON §4 F-4a) |
| 9 | RECON N-1 | The 1.89× write amplification under the juniper-ml launchers |
| 10 | RECON N-4 | A compatibility guardrail for the record envelope **and** for anchored message text, sited where it can fire |
| 11 | RECON N-6 / N-7 / N-8 | Dead code (`cascade_correlation/backups/`), the unused `profiling/logging_utils.py`, and the session-scoped fixture that stubs the emit path |

### Out of scope (named so it is a decision, not an omission)

- **The ELK/Kibana shipper** — §11.
- **Converging Path B into Path A.** The roadmap makes the three paths legible and separable; it does
  not merge them.
- **`juniper-canopy`'s custom logger**, **`juniper-service-core`'s** unread `JUNIPER_SERVICE_LOG_LEVEL` — §12.
- **A full 879-site f-string sweep.** Option B, refused.

### The claims this roadmap will not let itself make

1. That it recovers #563's 9× or #598's 49 %. Both are banked.
2. That any number in the revised priority order still describes the build — **except** that
   `_filter_by_level` is measured post-fix at **1.20 s / 2.8 %** (#598's PR body), which is already
   enough to question whether further logger-internal work earns its risk.
3. That a format change is safe because cascor's CI is green. It would be (RECON N-4).
4. **That "the existing test suite is green" verifies anything about emission.** `conftest.py:870-927`
   stubs `Logger._log_at_level` to a no-op for the whole session (RECON N-8).

---

## 2. Phase overview, dependencies and concurrency

| phase | title | gates on | blocks | size | live stack? |
| --- | --- | --- | --- | --- | --- |
| **P0** | Re-baseline, harness and policy | — | P2, P3, P5, P6 | **M–L** | yes (P0.1, P0.3) |
| **P1** | Level-system correctness | — | P4, P6 | **L** | no |
| **P2** | Logger internals | P0.4 | P3 | S–M | no |
| **P3** | Sink architecture | P0.4, P2, **P5.1** | P5.2 | L | yes (P3-G3) |
| **P4** | Per-logger levels | P1, **P3.4** | — | M–L | yes (P4.4) |
| **P5** | Structured output and observability convergence | P0 (P5.1: none) | P7 | M | yes (P5.4) |
| **P6** | Call-site policy and dead-code removal | P0.4, P1, P2 | — | M | no |
| **P7** | Export / ELK | P5 | — | deferred | — |

### Dependency graph

```text
   P0 ────┬──────────────────────────────► P6
  (measure│ harness, policy)                (call sites)
          │                                      ▲
          ├───► P2 ───► P3 ───► P5.2 ───► P7     │
          │  (internals) (sinks) (JSON)  (ELK)   │
          │              ▲                       │
          │   P5.1 ──────┘  (decides P3.3)       │
          │                                      │
   P1 ────┴───► P4        P1 ───────────────────┘
 (levels)    (per-logger; P4.4 also needs P3.4)
```

### 2.1 What can run concurrently

| may run in parallel | condition |
| --- | --- |
| **P0 ∥ P1** | P0 measures, P1 edits — but see trap 2 for P1's internal serialisation |
| **P0.1 ∥ P0.3** | **only under distinct `JUNIPER_CASCOR_LOG_DIR` and distinct run dirs.** Otherwise they destroy each other's evidence — see trap 1 |
| **P5.1 ∥ everything except P3.1 and P3.3** | it gates both. It can *start* on day one; P3 cannot start until it closes |
| **P4.1–P4.3 ∥ P3** | P4.4 is **not** — it needs P3.4 |
| **P6.2 → P6.3** | **not** parallel — see trap 3 |

### 2.2 What looks parallel and is not — five traps

1. **Two cascor processes sharing a checkout destroy each other's logs.** Stated in-source at
   `juniper-cascor/src/cascor_constants/constants.py:422-427`: *"cascor's parent logger writes ONLY
   to this file… Two cascor processes sharing a checkout therefore interleave and rotate away each
   other's evidence. Not hypothetical: that is how the F-P1-3 arm A/B logs were lost when a
   long-lived service rotated the shared file mid-arc."* **Every live-stack step in this roadmap must
   set a distinct `JUNIPER_CASCOR_LOG_DIR`.**
2. **The byte-gate covers four directories, not one file.**
   `juniper-cascor-model/tests/test_drift.py:27`: `_EXTRACTED_DIRS = ("candidate_unit", "utils",
   "log_config", "cascor_constants")`, with `_NORMALIZED_DIVERGENCE` now **empty**. P1.1, P1.2 and
   P4.3 all edit files inside it. **Serialise all work in those four trees.** The single exception is
   `log_config/logger/logger.py`, on `_INTENTIONAL_DIVERGENCE` — it must **not** be mirrored, and a
   reverse guard fails if it becomes identical (RECON N-5).
3. **P6.3's lint rule fails on P6.2's intermediate commits.** G-6 mandates one PR per file, so P6.2 is
   a multi-PR sequence; a rule banning bare numeric levels lands red until the last one merges. Ship
   P6.3 after P6.2, or behind `--advisory`.
4. **P3.4 without P3.3 is a regression.** A persistent handle converts Path A from open-by-name —
   which *survives* Path C's rotation — into a held descriptor, which follows the renamed inode and
   appends to `.1` forever while the live file, the one ~17 juniper-ml consumers glob first, stays
   near-empty. Nothing errors. **P3.3 (rotation owner) runs BEFORE P3.4 (persistent handle).**
5. **The mirror gate is one-directional.** `test_drift.py:78` walks the **package** tree
   (`(self.package_root / d).rglob("*.py")`), so a file that exists only in `src/` is never compared.
   P3.1 adds `src/log_config/sinks.py`; drift stays green while the package ships a logging tree
   missing the module. And because `logger.py` is allowlisted, the package's logger will not even
   `ImportError` — it silently keeps the old behaviour. **Adding a module to `log_config/` requires
   adding it to the package tree in the same PR.**

### 2.3 Critical path and the free work

Critical path: `P0.4 → P2 → P3 → P5.2`.

**Free on day one**: P5.1 (an adjudication, no code) and P0.5 (a code read). **P1 is not free** — its
real content is a level-state reconciliation that did not exist in the first draft, and its edits are
serialised behind trap 2. Do not schedule P1 as the cheap early win; schedule P0.4 and P5.1.

---

## 3. Phase 0 — Re-baseline, harness and policy

**Purpose.** Recover the measurement footing, build the guardrail every later phase depends on, and
settle two policies that are cheap now and expensive later.

**Explicitly a gate.** #598's headline was taken on a pre-merge branch build twelve minutes before
merge, and no corpus postdates it.

| step | tasks | depends on | live stack? |
| --- | --- | --- | --- |
| **P0.1** Post-merge worker profile corpus | (a) run the 32-profile cap-4 cell on merged `main` with `JUNIPER_CASCOR_WORKER_PROFILE`; (b) archive under `juniper-ml/reports/`; (c) **record the cell identity** — suite path, `max_hidden_units`, dataset seed, experiment seed, base config, arm | — | **yes** |
| **P0.2** Decompose the remainder | (a) re-run `juniper-ml/util/ad-hoc/2026-08-29_format_caller_attribution.py`; (b) attribute `logger.py`, `_io.open`, `strftime`, `print`; (c) report the **emitted** share and the **discard count** — see the acceptance caveat | P0.1 | no |
| **P0.3** Volume census | (a) bytes per record for **Path A** vs **{Path B ∪ Path C}** — B and C are byte-identical on disk (RECON §3), so a per-path split needs instrumentation or must be reported as a union; (b) the 1.89× duplication factor re-measured; (c) per-run totals at cap 4 and cap 16, **extrapolated** to cap 64 rather than run there; (d) how many Path-B/C records are lost to a descriptor held across Path C's rename | — | **yes** |
| **P0.4** Envelope + marker harness *(the guardrail every later phase uses)* | see §3.1 | — | once, to capture |
| **P0.5** Characterise the stubbed emit path | `conftest.py:870-927` replaces `Logger._log_at_level` with a no-op, autouse, session scope. State **per phase** which acceptance criteria that invalidates, and whether it is also the §7.1 swallowed-pytest mechanism | — | no |
| **P0.6** Settle the mirror policy | Decide now whether `juniper-cascor-model`'s logger copy is backported (as `test_drift.py`'s docstring promises for Wave 2) or frozen. Every P1/P4 edit to a byte-gated tree carries a mirror **and a package-release** obligation to `juniper-cascor-worker`; deciding this in P5 is five phases too late | — | no |
| **P0.7** Restore the written record | Comment on #573 with #598, the measurement, this roadmap and the deferral | P0.2, P0.3 | no |

### 3.1 P0.4 — the harness, in detail

Split out because the first draft made it a Phase-2 deliverable whose *stated location* made it
unenforceable.

- (a) **Two reference captures, not one** — the file sink and the redirected-stdout sink. They differ:
  the console formatter omits the function name (`constants_logging.py:157`), and `print()` into a
  redirected fd is block-buffered while the file path opens and closes per record. A single envelope
  definition matches both and distinguishes neither.
- (b) **An envelope checker**: `+` sentinel, bracket prefix, `(TIMESTAMP)` **including its precision**,
  `[LEVEL]`, message.
- (c) **A named-marker inventory** — the half of G-3 that matters most. RECON N-4 rates anchored
  **message text** BREAKING for ~17 juniper-ml scripts, and an envelope check passes a message-text
  change. Enumerate every marker string those scripts anchor on and assert each is still emitted.
- (d) **The enforcement mechanism.** A test sited in juniper-ml cannot fail a cascor PR — separate
  repos, no status-check propagation — so a juniper-ml-side comparison detects breakage only after
  the fact. (It is *feasible*: `juniper-ml/.github/workflows/docs-full-check.yml:107-110` already
  shallow-clones every ecosystem repo, so option (ii)'s harness exists.) **Choose one**:
  (i) a **cascor-side** test asserting the formatter strings in `constants_logging.py:152-158`,
  `conf/logging_config.yaml:47` and `api/observability.py:119` against a checked-in golden — mechanical,
  runs in cascor CI, catches the change at its source, and covers **all three copies of the prefix**;
  or (ii) a scheduled juniper-ml job that runs a cell and diffs. **Recommend (i)**, with (ii) as a soak.
- (e) **CI wiring, in the same PR.** juniper-ml's CI test list is hand-maintained;
  `tests/test_ci_test_wiring_drift.py` fails any `tests/test_*.py` not invoked by `ci.yml`'s
  regression step, and `AGENTS.md` carries a parallel hand-maintained list.

**Acceptance.** A named logging share with its emitted/discarded split *as far as the instrument
allows* — see the caveat — plus a bytes/record figure, a mirror policy, and a harness that fails a
deliberately-broken record in cascor CI.

> **Acceptance caveat, inherited and load-bearing.** GATED §3 states that f-string *construction* cost
> for discarded records is inline in each calling function's self time and is **not separately
> attributable** from this corpus; a true bound needs a build with the log calls removed, and raising
> the level does **not** measure it because arguments evaluate at the call site regardless. So P0.2
> can report the *emitted* share and the discard *count*, and **must not** promise the construction
> cost of discarded records. The disabled-logging A/B was already considered and **rejected** for the
> same reason — do not reach for it.

### SWOT

| | |
| --- | --- |
| **Strengths** | Mostly cheap. The profiling instrument exists and has been used twice. P0.4 is the guardrail the whole repo currently lacks, and P0.5/P0.6 are code reads that prevent two classes of late surprise |
| **Weaknesses** | Produces no user-visible improvement, so it is the phase most likely to be skipped. cProfile distorts absolute timings (#567: "profiling destroyed the difference" on a 9.2 ms gap) — it is a *composition* instrument, not a *speed* one |
| **Opportunities** | May retire whole phases. `_filter_by_level` is already at 2.8 %; if the rest of logging is comparable, P2 is not worth its risk and the roadmap shortens honestly |
| **Threats** | A **vacuous pass** — a corpus that cannot show a difference. A 32-profile run that silently collects 3 reads as a clean result. And P0.5 may find that a phase's stated coverage does not exist |
| **Risks** | The cell drifts from the pre-#598 cell. **This may be unrecoverable**: `logfix-verify/` holds only `prof/` — no config, no suite yaml, no manifest — and `grep -rln 'logfix'` across juniper-ml returns nothing. If the pre-#598 cell cannot be reconstructed from #598's PR body, say so and compare a known cell against an unknown one, explicitly |

### Guardrails

- **P0-G1 — instrument adequacy.** State, before running, what result would falsify the expectation.
- **P0-G2 — assert the CELL, not the count.** 32 profiles = `max_hidden_units × pool_size`; cap 8 ×
  pool 4 also yields 32 on entirely different work. Record the suite path, caps, seeds, base config
  and arm alongside the corpus. A count is not an identity.
- **P0-G3 — distinct `JUNIPER_CASCOR_LOG_DIR` per concurrent run** (trap 1), and protect long cells
  from `juniper-ml/util/reap_pytest_orphans.bash`, which treats reparenting to `systemd --user` as
  the orphan predicate while the experiment stack launches under `nohup`.
- **P0-G4 — cite the corpus path AND its mtime** in every number. The #598-vs-merge confusion happened
  because a path was quoted without its timestamp.

---

## 4. Phase 1 — Level-system correctness

**Purpose.** RECON N-3: `isEnabledFor` and `_filter_by_level` read **disjoint class state**, and
`set_level()` — which `candidate_unit.py:188` and `:297` call on construction — writes only the
guard's copy. Every later phase that touches levels inherits this.

**Sized L, not M.** The first draft scoped P1 to the numeric *table* and missed the *state* split
entirely; a table fix leaves the defect intact.

| step | tasks | depends on |
| --- | --- | --- |
| **P1.1** Reconcile the two configured-level states *(the actual content of this phase)* | (a) make `set_level` the single writer of one resolved level; (b) make `isEnabledFor` and `_filter_by_level` two **readers of that same value**; (c) fix `is_valid_level`'s `level == level` typo (`logger.py:341`); (d) a test that `set_level(X)` moves **both** paths. Detail below the table | — |
| **P1.2** One numeric table | (a) `cascor_constants/constants.py:534-541` is **canonical** and is **imported** by `logger.py:92-93` — **keep it**; (b) re-derive `logger.py:233-242`, which hardcodes a duplicate that *agrees*; (c) reconcile or delete `profiling/logging_utils.py:250-251` (`TRACE=5, VERBOSE=15`), the **only** table that contradicts; (d) export symbolic constants without colliding with the `_level_trace = "TRACE"` string attributes already on the class (`logger.py:196-206`) | — |
| **P1.3** Correct the guard integers | The **8** `isEnabledFor` call sites in `candidate_unit.py` (`:596,597,764,765,766,833,834,1046`) — not the 15 `if _log_*:` *use* sites they feed. `cascade_correlation.py`'s 7 hoists already pass `logging.DEBUG`/`logging.INFO` and are **out of scope**. Mirror `candidate_unit.py` | P1.1, P1.2 |
| **P1.4** Disposition `profiling/logging_utils.py` | Adopt (reconcile levels, wire to a real call site) or delete. Imported only by its own test (RECON N-7). **Do not leave a third definition.** If deleting, see P6-G3's symbol-loss trailer requirement | P1.2 |
| **P1.5** Per-level exercise test | Run the converted modules once per level — TRACE, VERBOSE, DEBUG, INFO — asserting no exception and that each level emits exactly the records it should. **Depends on P1.1**: until one level value drives both paths, there is no supported runtime mechanism to set the emission level, and this test cannot be written as specified | **P1.1** |

**P1.1 in detail.** Today `isEnabledFor` reads `_log_level` (`logger.py:448`, `:1042`) while
`_filter_by_level`'s threshold comes from `_level_logger_config` / `_level_logger_name` (`:516`) —
the latter assigned once in the class body (`:164`) and **never written again anywhere in the repo**.
`set_level` writes only the first (`:438-442`). Separately, `is_valid_level` returns
`cls._is_valid_level_name(level) or cls._is_valid_level_number(level == level)`; `level == level` is
`True`, `isinstance(True, int)` is `True`, and `True in _level_numbers.values()` is `True` because
`True == 1` and TRACE is 1 — so it returns `True` for `None` and `"BANANA"` alike.

**Acceptance.** `set_level(X)` moves both the guard and the emit filter; `is_valid_level("BANANA")` is
`False`; one numeric table; symbolic guards at 8 sites; P1.5 green at four levels.

### SWOT

| | |
| --- | --- |
| **Strengths** | Fixes a defect that silently defeats the guard idiom the whole call-site strategy rests on. P1.5 is the test that would have caught it, and it generalises into P6's G-2 |
| **Weaknesses** | Entirely invisible in output (see Threats), so it will read as churn to anyone who has not run the probe. The commit message must carry the evidence |
| **Opportunities** | Makes P4 possible at all, and turns the guard idiom from a hazard into a recommendation |
| **Threats** | **The first draft claimed a user-visible behaviour change here. There is none.** Both `if _log_trace:` blocks (`candidate_unit.py:604`, `:767`) contain only `.trace()` calls, so a mis-firing guard costs work and emits nothing. The real threat is the opposite: because nothing observable changes, a regression in P1.1 is **undetectable by inspection of the logs** |
| **Risks** | Trap 2 — P1.1/P1.2 touch `log_config/` and `cascor_constants/`, P1.3 touches `candidate_unit/`; all four trees are byte-gated except `logger.py`, which must not be mirrored |

### Guardrails

- **P1-G1 — the mirror is asymmetric, and it covers four trees.** `candidate_unit/`, `utils/`,
  `log_config/` and `cascor_constants/` are byte-gated; `log_config/logger/logger.py` is allowlisted
  and **must not** be mirrored. Both directions are enforced; neither is intuitive.
- **P1-G2 — pre-commit reformats one side of a byte-gated pair.** Black covers `src/` only. Re-sync
  the mirror *after* the final pre-commit run. (This is the surviving, fully-correct half of the
  analysis's G-5.)
- **P1-G3 — enumerate before converting.** Produce the full list of numeric level literals and convert
  from the list.
- **P1-G4 — verify the fix by probe, not by log inspection.** `juniper-ml/util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py`
  prints both paths side by side; extend it into the regression test. Log output cannot show this fix
  working, because a correct guard and a broken guard produce the same log.

---

## 5. Phase 2 — Logger internals

**Purpose.** The remaining revised-order item 3, plus the per-record closures. Contained inside
`logger.py`; no call-site changes; no format change.

**Sized honestly, and droppable.** `_filter_by_level` — the one large logger-internal item — is
already at 2.8 % post-#598. P0.2 decides whether the rest is worth its risk. Because P0.4 now owns the
harness, **dropping P2 does not drop P3's guardrail**.

| step | tasks | depends on |
| --- | --- | --- |
| **P2.1** Move `frame`/`tsp` inside `_log_at_level` | (a) drop the eager `cls._frm()` / `cls._tsp()` arguments from all eight methods; (b) capture inside, after the filter; **(c) preserve `_frame_info`'s one-hop contract** — pass `cls._frm().f_back` from `_log_at_level` rather than making `_frame_info` walk two hops; (d) assert `_log_at_level` has no callers outside the eight methods | P0.4 |
| **P2.2** Hoist the formatter closures | **Six** closures per *emitted* record plus **one per call**, against the two the design names: `_logging_message` ×2 (`logger.py:521,522`), a `_frame_info` and a `_date` closure inside **each** of `_console_dict` (`:302,303`) and `_file_dict` (`:320,321`), and `_get_log_level`'s lambda (`:391`, built at `:516`) — the last **before the filter**, so it is the most frequent of the seven. The two named in F-4a are the two *cheapest* | P0.4 |
| **P2.3** Widen the invalidation set to match | The `:459` closure captures `formatter_string` and `dict_method` by value and is hoistable; but the dict builders read `cls._date_format`, `cls._field_names_*`, `cls._frame_file/_line/_func` and `cls._frame_unknown` **at call time**. Hoisting far enough to matter widens invalidation to all of them | P2.2 |

**Why P2.1(c) matters.** `test_logger_frame_resolution.py` calls `_frame_info` **directly** (`:71`,
`:90`, `:104`, `:109`) and compares it against `getouterframes(frame)[1]`. Making `_frame_info` walk
two hops breaks all four assertions — and §5's SWOT names that suite as the step's *only* detector,
because no consumer parses the `file:func:line` field (RECON N-4). Rewriting the test to accommodate
the change would leave the step with no detector at all.

**P2.4 (per-record level-check lambda) is deliberately absent** — it is the same edit as P4.2's
"resolve once at configuration time", on the same two functions. Doing it twice is a three-way
conflict with P3.1. **It belongs to P4.2.**

**Acceptance.** P0.4 green; `test_logger_frame_resolution.py` green **unmodified**; a re-measured delta
against P0.1's corpus, reported even if nil.

### SWOT

| | |
| --- | --- |
| **Strengths** | Zero call-site risk. Independently revertable, one item per PR |
| **Weaknesses** | The measured value is small and may not survive P0.2. This is the phase most at risk of being effort spent for a number that rounds to zero. Also: P2.2's hoist is *delivered anyway* by P3.1, which replaces `logger.py:521-526` wholesale — so on the critical path it is work discarded one phase later unless it is landed specifically to isolate its measurement |
| **Opportunities** | If P0.2 says logging is now small, this phase's honest outcome is **cancellation**, and the roadmap is better for saying so |
| **Threats** | **P2.1 changes the reported caller.** Frame resolution is how every record gets `file:func:line`; getting the depth wrong mislabels every record — and **no consumer parses that field** (RECON N-4), so nothing downstream fails. The test suite is the only detector, and P0.5 must confirm it is not stubbed |
| **Risks** | P2.2/P2.3 cache state that must be invalidated on reconfiguration — the same shape as #598's level cache, which needed `_invalidate_level_cache` to avoid silently discarding custom-level records |

### Guardrails

- **P2-G1 — no phase-2 item lands without P0.4 green**, via the cascor-side mechanism chosen in
  P0.4(d). A juniper-ml-sited test cannot fail a cascor PR.
- **P2-G2 — every cache gets an invalidator, and a test that the invalidator fires**, covering the
  full captured set from P2.3.
- **P2-G3 — measure the delta and report it honestly**, including nil.
- **P2-G4 — do not fold P2 into P3**, and do not fold either into a hot-path bugfix. #573 was
  deliberately kept out of #563 so neither justified the other; #598 then took two redesign items
  inside a perf fix and recorded nothing on #573. That is the failure this guardrail prevents.

---

## 6. Phase 3 — Sink architecture

**Purpose.** #573 scopes 1 and 2, design F-2 and F-3, RECON N-1 and N-9. The phase that carries the
volume win and most of the design risk.

**Note the reordering**: rotation is settled **before** the persistent handle (trap 4).

| step | tasks | depends on |
| --- | --- | --- |
| **P3.1** Sink abstraction | (a) a minimal sink protocol; (b) a registry on `Logger` — **first fix the shadowed binding** at `logger.py:136`/`:155` (see below); (c) route `_log_at_level`'s tail through it, **each sink with its own byte contract**; (d) add the new module to the package tree in the same PR (trap 5) | P0.4, P2, **P5.1** |
| **P3.2** Independently disableable console sink | (a) an **explicit switch** (env + config) defaulted per §13 decision 2. Do **not** condition on "stdout is redirected" — the only runtime signal is `isatty()`, false for a redirect *and* a pipe *and* systemd, i.e. false always for the service; (b) TTY-gated colourisation, console sink only, **never** the file sink | P3.1 |
| **P3.3** Rotation with a single owner *(before P3.4)* | (a) **give the file one owner.** Path C's `RotatingFileHandler` (`api/observability.py:110-115`, 10 MB / 5 backups) rotates the same file Path A appends to per record and Path B holds open. Either the sink owns rotation for all three paths, or the paths get distinct files; (b) document rotation as a property of the file sink; (c) confirm the `.N` glob ~17 juniper-ml consumers use still holds | P0.3, P3.1, P5.1 |
| **P3.4** Persistent file handle | (a) hold one handle for the process lifetime; (b) flush per record (owner decision 2); (c) **open in append mode (`O_APPEND`)**; (d) **open lazily, relative to forkserver start** (RECON N-2); (e) preserve create-on-demand and the `FileNotFoundError` retry (F-2b); (f) survive P3.3's rollover. Constraints (b), (c), (d) and (f) explained below | **P3.3** |

**P3.1(b) — the shadowed binding.** `logger.py:136` sets `_file_name = "file"` (the destination name);
`:155` overwrites it with `"filename"` (the format field). `Logger._file_name` is therefore
`"filename"`, the destination name `"file"` is unreachable, and `_console_name` (`:135`) still holds
`"console"`. A registry keyed on `(cls._console_name, cls._file_name)` registers a sink called
`"filename"`. Fix the shadowing first.

**P3.4's constraints, in detail.**

- **(b) flush per record** is owner decision 2, and its reason travels with it: *"a complete log for a
  crashed run outweighs the throughput; a truncated log is how several analyses in this arc went
  wrong."* It is the obvious thing to trade away once an I/O cost is measured — do not, without
  re-taking the decision.
- **(c) `O_APPEND`** makes each write seek-to-end atomically, and is the only thing that makes
  concurrent appenders survivable at all. A handle written by two processes without it corrupts.
- **(d) laziness is load-bearing.** `cascade_correlation` is in the forkserver preload list, so the
  forkserver process imports the logging tree; a handle opened at import or forkserver time is
  inherited by every child with a **shared file offset**.
- **(f) the rollover.** A held descriptor follows the renamed inode, so this needs a
  stat-the-path-and-reopen check or `copytruncate` semantics — see trap 4.

**Acceptance.** P0.4 green on both captures; console sink demonstrably off with the file sink
unaffected and **every consumer of the redirected-stdout file re-pointed**; a fork-safety re-screen
green; per-run bytes down by the factor P0.3 measured.

### SWOT

| | |
| --- | --- |
| **Strengths** | Delivers the visible half of #573. P3.2 alone is a measurable volume win on the harness corpus, where the evidence is produced |
| **Weaknesses** | The largest phase, with the most surface, in a class the codebase itself describes as *"TODO: Need to clean-up this steaming pile"* (`logger.py:613`) |
| **Opportunities** | Once a sink protocol exists, P5.2's JSON sink is an implementation of it rather than a second write path. The abstraction pays for itself in P5 or it was not worth building |
| **Threats** | **The forkserver-inherited handle** (N-2) and **the rename-stranded descriptor** (N-9, trap 4) — two independent ways for P3.4 to lose records with no error. Secondary: **atomicity has a size limit** — `PIPE_BUF` is the threshold below which a concurrent append is atomic; cascor records embed formatted tensors and can exceed it |
| **Risks** | P3.2 changes behaviour for anyone reading stdout. The runner convention of redirecting stdout wholesale and reading the log file must keep working — verify, do not assume |

### Guardrails

- **P3-G1 — re-run `juniper-ml/util/ad-hoc/2026-08-26_fork_safety_import_surface.py`.** #569's audit
  certified the preload closure creates "no import-time resource a forked child would share"; a
  persistent handle would invalidate that certification. Landing gate.
- **P3-G2 — CPython swallows a forkserver preload `ImportError`.** Verify with the module census.
- **P3-G3 — test for torn records at a known threshold.** Run a concurrent-append cell at cap ≥ 16
  under a **distinct log dir** (trap 1) with records deliberately above and below `PIPE_BUF`, and scan
  for interleaved or truncated records. "Above the platform guarantee" is not a number anyone can
  test against; `PIPE_BUF` is.
- **P3-G4 — the fallbacks stay on the table.** Per-PID files (changes the artifact layout ~17 scripts
  depend on) and a parent writer thread (cleanest, most machinery, itself a fork-safety hazard).
  Owner decision 3 is explicitly provisional, **and its premise — `fork` — is refuted**; it has never
  been re-issued against the forkserver model. P3.4 is where it is confirmed or replaced.
- **P3-G5 — colour never reaches the file sink.**
- **P3-G6 — no reduction in what is logged, checked on the RIGHT stream.** A file-sink record count is
  invariant under P3.2 by construction, so counting it proves nothing. P3.2 removes records from the
  **redirected-stdout** file, which has real consumers —
  `juniper-ml/util/ad-hoc/2026-08-10_ea_aggregate_clean.py:44` (`LOG_CANDIDATES = ("logs/juniper-cascor.log", …)`),
  `juniper-ml/util/ad-hoc/e2e_cascor_leg_supervise.bash:96`, `juniper-ml/util/ad-hoc/e2e_cascor_leg_restart.bash:50`. Enumerate and
  re-point every one.
- **P3-G7 — the `+` sentinel is load-bearing, and the timestamp is load-bearing for a different set.**
  Two scripts split worker from parent lines on `line.startswith("+")` alone
  (`juniper-ml/util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash:309`,
  `juniper-ml/util/ad-hoc/2026-08-26_t6_stop_evidence_scan.py:103`); removing or relocating the
  sentinel **silently nulls their orphaned-worker signal**. Separately, 3 of the 6 timestamp parsers
  have no optional `,millis` group and would silently skip every line if Path A gained sub-second
  precision — but they are a **disjoint set** from the two sentinel consumers, which both carry
  `(?:,(\d{3}))?` and tolerate it. Guard the two surfaces separately; do not conflate them.

---

## 7. Phase 4 — Per-logger levels

**Purpose.** #573 scope 3. Precedence, most specific first: per-logger env var → global env var →
per-logger config entry → global config → default.

| step | tasks | depends on |
| --- | --- | --- |
| **P4.1** Establish what "per-logger" can mean | Decide between **per-instance loggers** and **named sub-loggers on the class** before writing code. The two binding styles and the API-break consequence are set out below | P1.1 |
| **P4.2** Resolution and precedence | Implement the chain; resolve names to integers **once** at configuration time and store the integer. **This subsumes the per-record `_get_log_level_check` lambda** (`logger.py:394`, called at `:516`) — it is not a separate Phase-2 item | P4.1 |
| **P4.3** Env surface | `JUNIPER_CASCOR_LOG_LEVEL` is canonical; `CASCOR_LOG_LEVEL` is deprecated with a `DeprecationWarning` and a split-config stderr warning (CFG-05, `constants.py:638-658`). Extend that convention; do not invent a second. Byte-gated tree — trap 2 | P4.2 |
| **P4.4** Fork propagation | Configuration set in the parent must survive into forkserver children. #573 raises this, citing `JUNIPER_CASCOR_WORKER_PROFILE` as precedent | P4.2, **P3.4** |

**P4.1 in detail.** Two binding styles already coexist: `candidate_unit.py:188`/`:297` and
`cascade_correlation.py:3188` bind the **class**; `cascade_correlation.py:667` binds an **instance**
(`self.log_config.get_logger()`). Both resolve to the same class-wide state anyway, because
`isEnabledFor` is a `@classmethod` (`logger.py:1026`) and every level knob — `_log_level`,
`_level_logger_name`, `_level_logger_config`, `_level_number_cache` — is a class attribute.
**Per-instance levels therefore require making `isEnabledFor` an instance method, which breaks every
`Logger.trace(...)` classmethod call site.** That is the decision, and it sets the phase's size.

**Acceptance.** A per-logger level set by env and by config, demonstrated **in a forkserver child**.

### SWOT

| | |
| --- | --- |
| **Strengths** | Addresses owner-raised scope. Retires the remaining per-record level resolution as a side effect |
| **Weaknesses** | **P4.1 may find the phase is L, not M.** If per-logger means per-instance, it is an API break across ~1,200 Path-A call sites; if it means named sub-loggers on the class, it is tractable. That is a scoping decision, not an implementation detail |
| **Opportunities** | A per-logger level is what makes the ~872 live Path-A suppressed-by-default sites cheap to turn on selectively — the operator need behind the whole f-string argument |
| **Threats** | Precedence chains are where silent misconfiguration lives. A per-logger var that loses when it should win produces *no error* — just the wrong records |
| **Risks** | P4.4 is the classic failure: configuration applied in the parent after the forkserver started is invisible to children |

### Guardrails

- **P4-G1 — a precedence truth table, tested**, including the "both set, different values" case CFG-05
  already handles for the global pair.
- **P4-G2 — demonstrate in a child**, under a distinct log dir (trap 1).
- **P4-G3 — do not add a third env-var convention.**
- **P4-G4 — an unknown level name must fail loudly at configuration time.** **Prerequisite: P1.1(c).**
  This is unimplementable while `is_valid_level` returns `True` for every input.

---

## 8. Phase 5 — Structured output and observability convergence

**Purpose.** #573 scope 4's prerequisite, and the reconciliation of the fork that already exists.

**Reframed.** D-4 and owner decision 6 say "no second implementation local to cascor". One is
**already there and deliberate**: `api/observability.py:75-119` forks `configure_logging` with its
rationale in-source at `:81-83`. The decision is not "avoid a fork" but "reconcile the one we have."

| step | tasks | depends on |
| --- | --- | --- |
| **P5.1** Adjudicate the fork *(free on day one; **blocks P3.3**)* | (a) upstream cascor's needs into `juniper_observability.configure_logging`; (b) keep the fork, documented, re-using only `JuniperJsonFormatter`; (c) narrow the fork to the delta. **Recommend (c).** Two consequences below | — |
| **P5.2** JSON as a Path-A sink | Implement `JuniperJsonFormatter` as a P3.1 sink. Stable field names; the human-readable sink stays byte-stable alongside it | P3.1, P5.1 |
| **P5.3** Screen the import surface | Adding `juniper-observability` to the **worker** import path changes the worker module count. #570 closed at 1,166 modules/worker; do not silently undo it | P5.2 |

**Two consequences of P5.1 that make it block P3.3.**

1. **Option (a) deletes the only rotator.** `juniper-observability` has no file sink and no rotation
   (RECON §3), so upstreaming cascor's `configure_logging` removes the `RotatingFileHandler` at
   `api/observability.py:111`. `juniper_cascor.log` would stop rotating and the `.N` glob that P3.3(c)
   is told to confirm would stop existing.
2. **Any option changes handler-set state at `Logger.__init__` time.** `logger.py:768` decides whether
   to apply the YAML's `root:` section — and therefore whether Path B attaches a *second* handler to
   the same file — by testing whether `logging.getLogger().handlers` is already non-empty. P5.1 moves
   that condition.

**Acceptance.** One documented JSON implementation; the human-readable envelope unchanged; worker
module count within its bound; `src/tests/unit/test_api_observability.py:85-120` updated deliberately.

### SWOT

| | |
| --- | --- |
| **Strengths** | The dependency and the formatter already exist — convergence, not construction |
| **Weaknesses** | Option (a) moves `juniper-observability`'s minimum pin for every consumer: a release-train item, not a cascor PR |
| **Opportunities** | canopy, data and recurrence all call the shared function unmodified; what cascor needs is plausibly what they will need next |
| **Threats** | `juniper_observability.configure_logging` **removes all existing root handlers** (`logging.py:72-73`); cascor's fork does the same. Ordering between them, and between either and `Logger.__init__`'s root-clobber guard (`logger.py:768-770`, incident-dated 2026-07-10), is unguarded in one direction |
| **Risks** | P5.3's module-count regression is silent — nothing fails, the worker is just fatter, and #570's closure quietly stops being true |

### Guardrails

- **P5-G1 — module census, not absence of errors.**
- **P5-G2 — the plain sink stays byte-stable while JSON is added.** JSON is a *second* sink. This is
  the design §6 recommendation, adopted verbatim.
- **P5-G3 — a shared-package pin bump is a release-train item**, not a cascor PR.
- **P5-G4 — name the affected suite.** `src/tests/unit/test_api_observability.py:89`, `:97` and `:114`
  assert `len(root.handlers) == 2` (StreamHandler + RotatingFileHandler). All three options change
  that; say which assertions move under each.

---

## 9. Phase 6 — Call-site policy and dead-code removal

**Purpose.** Demoted to last by measurement. It survives because of dead code and because a migration
without a rule is undone by the next author.

| step | tasks | depends on |
| --- | --- | --- |
| **P6.1** Delete `src/cascade_correlation/backups/` | 472 sites in five files nothing imports (RECON N-6). Two tests reference the directory only to **exclude** it (`test_blas_thread_policy.py:118`, `test_phase_2e_topology_correlation_phase.py:191`) — dead clauses to remove in the same PR. **Also decide `src/backups/check.py`** (~68 sites) — it is **untracked**, so it is invisible to `git grep` and survives a tracked-tree deletion | — |
| **P6.2** Guard idiom, symbolically | Convert to `Logger.TRACE` / `Logger.VERBOSE`. **One PR per file** (G-6) | P1, P2 |
| **P6.3** A rule that holds | A lint rule banning bare numeric levels in `isEnabledFor`, and optionally f-strings in `trace`/`verbose`/`debug` within the hot modules. **Lands after P6.2's last PR, or behind `--advisory`** (trap 3) | P6.2 |
| **P6.4** `%`-args where trivial | Only where the conversion is mechanical. **Not a sweep** | P6.2 |

**Acceptance.** `backups/` gone; zero bare numeric levels; the lint rule failing on a deliberately bad
call; P0.4's marker inventory still green.

### SWOT

| | |
| --- | --- |
| **Strengths** | P6.1 is subtraction at zero behavioural risk. P6.3 is the only item in the roadmap that prevents recurrence |
| **Weaknesses** | P6.2 and P6.4 have the worst value-to-risk ratio here. They are **hygiene**, and should be argued that way |
| **Opportunities** | P6.1 makes every later grep honest. Concentration in the two hot files is 46 % of live code, or **56 %** of live Path-A code — the migration analysis's claim was *understated*, not overstated |
| **Threats** | The three `%`-conversion hazards are unchanged and are listed in full below the table |
| **Risks** | Scope creep from P6.4 into a full sweep — refused as Option B |

**The `%`-conversion hazards, carried forward verbatim in substance.**

1. **A literal `%` becomes a format spec.** `logger.info(f"progress {pct}%")` → `"progress %s%"`
   raises `ValueError: incomplete format` at emit time — **inside logging, in a forked worker, at a
   level that is off in testing and on in production.** Existing `%` must be escaped to `%%`.
2. **Format specs do not survive, and precision is a parsing surface.** `f"{x:.4f}"` must become
   `"%.4f"`; a conversion that drops the spec **silently changes log output**, and several
   `juniper-ml/util/ad-hoc/` scripts parse numeric fields out of log text — so a precision change is a
   **downstream parsing change, not a cosmetic one.**
3. **A lone tuple argument splats.** `if args: message = message % args` (`logger.py:520`) passes
   whatever it is given, so a single tuple-valued argument mis-formats. P6.4's "no literal `%`, no
   format spec" filter does **not** exclude this class.

### Guardrails

- **P6-G1 — exercise every CONVERTED SITE at its own level.** This is G-2, and it is **not** discharged
  by P1.5: the logger's own suite does not execute `cascade_correlation.py`'s or `candidate_unit.py`'s
  call sites, so it cannot detect a broken `%`-string at a converted site. One run per level **over the
  converted modules**, asserting no exception and no `ValueError: … format …`.
- **P6-G2 — one PR per file** (G-6). `cascade_correlation.py` (508 sites) and `candidate_unit.py` (172)
  are separately reviewable; together they are not.
- **P6-G3 — deletion needs a symbol-loss waiver, and P6.1 is NOT free.**
  `juniper-cascor/.github/workflows/main-verify.yml:186` runs `juniper-symbol-loss-check --scope
  'src/**/*.py'` and **always runs** on the default branch; the per-PR screen is advisory and will only
  warn. Deleting five modules is a large AST symbol loss. Commit with an enumerated
  `Allow-Symbol-Loss:` trailer **as the final paragraph of one commit**, and verify with
  `git log -1 --format='%(trailers:key=Allow-Symbol-Loss)'`. The same applies to P1.4's delete option.
- **P6-G4 — re-measure, and say which population.** The pre-migration `Tensor.__format__` anchor is
  **1,813,318** for that callee alone; **3,626,636** is the matched-callee set including the delegation
  edge. Quoting the wrong one makes the guardrail unfalsifiable.
- **P6-G5 — "hot" is behavioural, not file-based.** The design's definition: *anything inside candidate
  training, the per-epoch output loop, or a per-record path.* The file-based proxy is exactly what N-6
  showed to be unreliable.

---

## 10. Cross-cutting: rollback and release

Neither had a home in the first draft.

- **Rollback.** P1.3, P3.2, P3.4 and P5.1 all change a shared on-disk artifact consumed by ~17 external
  scripts. A revert after a corpus has been generated leaves a **mixed corpus with no marker**. Each
  needs a named revert trigger **and a way to tell, from a log file alone, which behaviour produced
  it** — a version token in the first record is the cheapest form.
- **Release.** `juniper-cascor-model` publishes independently (`publish-cascor-model.yml`, Release-
  triggered) and `juniper-cascor-worker` depends on it. Every edit to a byte-gated tree therefore
  carries a mirror re-extraction **and a package release** before the worker sees it. P0.6 settles the
  policy; each phase that touches those trees states its release obligation.
- **Ownership.** Every step marked "live stack? yes" needs an owner and a slot: P0.1, P0.3, P3-G3,
  P4-G2, P5.3. They contend for the GPU, they carry the reaper hazard, and per trap 1 they destroy
  each other's evidence if they share a log dir.

---

## 11. Phase 7 — Export / ELK (deferred)

Gated on P5. Retained so the deferral is a recorded decision.

A network sink on the per-record path in a forkserver child is where an unbounded queue or a blocking
socket costs more than everything this roadmap recovers. Ship structured output; let a sidecar ship it
onward.

**Latent conflict to resolve before P7** (migration analysis §4 Option D): lazy message callables and
a deferred/queued writer are mutually unsafe — closures capture by reference, so a message evaluated
after the fact can render a **different value** than at the call site. If P7 introduces a queue,
Option D is off the table, and vice versa. **They must not be adopted independently.**

Option D carries two further constraints if it is ever revisited: a lambda that raises must not take
down a training run, so it needs its own try/except — **a new swallow-path to get right**; and it
allocates a closure per call **even when suppressed**, a new per-call cost at ~872 live Path-A suppressed sites.

---

## 12. Adjacent, out of this arc, worth an issue each

1. **canopy's `LoggingConfig` env overrides are dead.** `src/logger/logger.py:536` gates on a top-level
   `logging:` key its dictConfig-shaped YAML does not have, so `CASCOR_CONSOLE_LOG_LEVEL` and
   `CASCOR_FILE_LOG_LEVEL` never apply and every logger falls back to hardcoded defaults. Verified.
2. **`juniper-service-core` declares `JUNIPER_SERVICE_LOG_LEVEL` and nothing reads it**
   (`settings.py:31,36`) — 150 emit sites, zero configuration.
3. **canopy still accepts `CASCOR_*` env names** for a non-cascor service — a CFG-05-shaped migration.

---

## 13. Open decisions for the owner

| # | decision | why it cannot be defaulted |
| --- | --- | --- |
| 1 | **Does P2 run at all?** | `_filter_by_level` is already at 2.8 %; P0.2 sizes the rest. Pre-authorising "drop P2 if the logging share is below X %" would let P0 close cleanly |
| 2 | **P3.2's default** — console sink on or off? | Off is the volume win; on preserves every current stdout consumer. Recommend **on by default, off in the harness profile**. Note this is a *policy* switch, not a runtime detection |
| 3 | **P5.1** — upstream, keep, or narrow the `configure_logging` fork? | (a) moves a fleet-wide pin **and deletes the only rotator**; (c) recommended, leaves a documented divergence |
| 4 | **P0.6 / mirror** — is `juniper-cascor-model`'s logger backported in Wave 2, or frozen? | `test_drift.py`'s docstring promises Wave 2. Until decided, every logger change has an undefined obligation to a second tree **and to a published package** |
| 5 | **P4.1** — per-instance loggers, or named sub-loggers on the class? | Per-instance means de-classmethod-ing `isEnabledFor` and breaking ~1,200 call sites. This decides whether P4 is M or L |
| 6 | **Owner decision 5 is still open and still yours.** The call-site migration scope was deferred pending the analysis; the analysis was delivered and its recommendation overturned by measurement. **This roadmap schedules P6 but does not take the decision** | The design reserved it explicitly. It must not become planned work by default |
| 7 | **§7.1's swallowed-pytest investigation** | Still unexplained, and P0.5 has surfaced a candidate mechanism (`conftest.py`'s session-scoped `_log_at_level` no-op). The design's protocol stands: reproduce the disappearance, then distinguish pytest capture, a `capsys`/`-s` interaction, the logger's `print`, and stream buffering — **and only then** propose a fix. **Explicitly not a blocker** on the rest |

---

## 14. Consensus record

Sizing per [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) §3:
**high criticality** × **high uncertainty** (overturns standing conclusions; universal quantifiers; a
convenient finding) → Lane A ≥ 2 distinct entry points, Lane B ≥ 2 opposing briefs, ≥ 2 iterations.

**Lane A** — two agents, distinct entry points (the code tree; git/GitHub/disk history). Recorded in
RECON §8.

**Lane B round 1** — three agents, three lenses: factual over-generalisation, amputation,
executability. Each briefed that a finding of soundness is worth nothing. It changed this document
structurally, not cosmetically:

| what round 1 found | what changed here |
| --- | --- |
| The level system has **two disjoint configured-level states**; `set_level()` is a no-op for emission — found by *running* the logger, and reached independently by two reviewers | P1 rewritten around it and resized M → **L**; P1.5 re-declared as depending on it; P1-G4 changed to verify by probe because the log cannot show this fix working |
| `is_valid_level` returns `True` for every input (`level == level`) | new P1.1(c); P4-G4 declared unimplementable without it |
| P1's deletion target was **wrong** — `constants.py` is canonical and *imported* by `logger.py` | P1.2 rewritten; "three contradictory tables" corrected to two-agree-one-contradicts |
| `conftest.py:870-927` stubs `_log_at_level` for the whole session | new **P0.5**; "the suite is green" struck as an acceptance criterion in §1 and P2 |
| The envelope harness was sited where it **cannot fail a cascor PR**, and its CI wiring was missing | moved into **P0.4** with an enforcement mechanism, two captures, a marker inventory, and the hand-maintained CI-list obligation |
| G-2 was declared "implemented by P1.4" — a test that cannot exercise converted call sites | false discharge removed; P6-G1 restored to its real scope |
| **`O_APPEND`** — the one constraint that makes concurrent appending safe — had been dropped | restored as P3.4(c); `PIPE_BUF` restored to P3-G3 |
| P3.3-before-P3.4 was backwards; a persistent handle **acquires** the rename defect | phases reordered; trap 4 added |
| P5.1 declared parallel to P3, but it **decides** P3.3's contract and would delete the only rotator | P5.1 now blocks P3.3; noted in §2 and §13 |
| P2.4 and P4.2 were the same edit in two phases | P2.4 deleted, folded into P4.2 |
| The byte-gate covers **four** trees; the mirror gate is **one-directional** | traps 2 and 5 |
| P6.1 called "free" — the always-on symbol-loss screen fires on it | P6-G3 with the `Allow-Symbol-Loss:` trailer requirement; "free" struck |
| Seven per-record closures, not two | P2.2/P2.3 rewritten |
| `test_logger_frame_resolution.py` is what P2.1 **breaks**, not what protects it | P2.1(c) specifies the one-hop-preserving implementation |
| Owner decisions 4 and 5 had been dropped or converted to planned work | decision 4 restated in §1 scope item 1; decision 5 restored as §13 item 6 |
| Conversion hazards 2 and 3 (precision-as-parsing-change; tuple splat) dropped | restored to P6 Threats |
| Cross-repo script paths unprefixed | path convention added at the head |

**Lane B round 2 — briefed on the corrections, not on the roadmap.** It found **24 defects**, which
is the procedure's premise vindicated: the fix pass is where new errors enter. What it changed here:

| what round 2 found in round 1's fixes | resolution |
| --- | --- |
| **Round 1's own P3 reorder was not propagated.** Trap 4 still read *"P3.4 runs BEFORE P3.3"* — after renumbering, that instructs the exact ordering the reorder was made to prevent | trap 4 inverted; P3.3's title no longer points at a non-existent "P3.3b"; the §2 phase table, graph and concurrency table renumbered (P4.4 needs **P3.4**; P5.1 decides **P3.3**) |
| **§2.1 still listed "P5.1 ∥ everything"** after the correction that made P5.1 a blocker of P3.1 and P3.3 | qualified: it may *start* on day one, but P3 cannot start until it closes |
| **P0.4(d)'s stated ground was false** — "juniper-ml CI has no cascor checkout". `docs-full-check.yml:107-110` shallow-clones every ecosystem repo | the conclusion survives on the correct ground (separate repos, no status-check propagation); option (ii)'s harness is noted as already existing |
| The seventh closure was filed as per-**emitted**-record. `_get_log_level`'s lambda is built **before the filter**, so it is paid on the 91 % discarded and is the most frequent of the seven | P2.2 restated as six-per-emitted plus one-per-call |
| The restored "absence of milliseconds" hazard in P3-G7 is **false** — both sentinel scripts carry an optional `,millis` group | P3-G7 rewritten: the `+` sentinel and the timestamp are **disjoint** surfaces with disjoint consumers |
| P3.4 promised "all five constraints explained below"; four are, and (e) is explained nowhere | corrected to name the four |
| Two `util/` paths remained unprefixed — which the document's own head rule calls a defect | prefixed |
| §14 cited "RECON §9"; RECON has no §9 | corrected to §8, and RECON's References renumbered |

**Termination.** Round 2's remaining findings were anchor and pointer slips changing no number,
disposition or action — the procedure's stopping condition. Round 3 is not warranted.

## 15. References

- [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) — the issue and owner scope
- [cascor#598](https://github.com/pcalnon/juniper-cascor/pull/598) — the shipped remediation
- [cascor#563](https://github.com/pcalnon/juniper-cascor/pull/563), [#569](https://github.com/pcalnon/juniper-cascor/issues/569), [#570](https://github.com/pcalnon/juniper-cascor/issues/570), [#579](https://github.com/pcalnon/juniper-cascor/issues/579)
- [`…LOGGING-CURRENT-STATE-RECONCILIATION.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md) — the evidence base
- [`…LOGGING-REDESIGN-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md) and [`…LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md`](JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md) — the documents reconciled
- [`…GATED-MEASUREMENTS-RESULTS.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md) §3 — the measurement that inverted the priority order
- `juniper-ml/util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py` — the level-state probe
