# HANDOFF 2026-08-18 — the unowned CLI-experimentation tasks, and the wall-budget knob with one adopter

Successor to [`HANDOFF_2026-08-15_cli-experimentation-second-sweep.md`](HANDOFF_2026-08-15_cli-experimentation-second-sweep.md) (ml#1127),
whose §3 lane is now **closed**.

**Nothing here is in flight.** No experiment driver is running, the experiment port ranges are clear,
and the 2026-08-16/17 head-to-head campaign has finished.

**"The plan"** always means
`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`.
`notes/` holds thirteen `CLI-EXPERIMENTATION*` documents, so every bare `plan :NNN` below refers to
that file and nothing else. Section references of the form "the plan's §12" likewise.

**Plan line numbers are volatile — locate by pattern.** They are pinned here to juniper-ml `76e4513`,
but that file is edited often: it moved by ~18 lines during this document's own authoring, which
invalidated a first set of anchors, and the predecessor's three plan anchors were stale for the same
reason. Every plan citation below is therefore given with enough surrounding text to `grep` for. If a
number does not resolve, grep the quoted text — do **not** read the neighbouring line and assume.

**What this owns.** **Seven items, T1–T7.** T2–T7 are the tasks the second sweep left unowned — the
predecessor counted them as *five* bullets because it grouped W-4 with W-9; split into T3 and T4 they
are six. (L-2 and L-4 remain grouped, as T5.) **T1** is the seventh: the half of the wall-budget work that shipped a mechanism and never
swept the library that needed it.

Items are numbered **T1–T7** deliberately. Do **not** re-letter them A–H: the perf-lane phasing note
(§0.3) already uses A–H for a *different* inventory, and its **G** is the head-to-head campaign.

**Validation.** Two rounds of independent agent review before landing: three validators on the first
draft (verdict **FAIL**, ~25 defects), then a re-check of the corrections, since a revision introduces
its own errors — it did, and they were caught. Findings are folded in.

Two lessons the successor should carry, because they are about *this* document:
the predecessor's `:201` / `:1115` / `:1171` plan anchors were all **wrong** and the first draft
inherited them verbatim while claiming a full re-probe; and one validator's "correction" to
`run_experiment.py:658` was itself wrong (`:657` is the guard, `:658` *is* the message). **Re-derive
what you copy, and verify what a reviewer tells you.**

---

## 0. What closed since the predecessor, so you do not re-derive it

### 0.1 Merged in juniper-ml

| PR | landed | what |
|----|--------|------|
| ml#1133 | `b7f7ec2` | the orphan reaper no longer kills a live experiment stack or campaign |
| ml#1142 | `e4f05f5` | `execution.max_wall_seconds` forwarding, R-6 gate widened to cap, pf3 fix, 4 doc true-ups |
| ml#1152 | `652724e` | driver preempts a 409 on start; reports an inert stall window |
| ml#1159 | `49cc073` | **guards the `max_epochs`/`output_epochs` trap** + the 2× root-cause tooling (creates the E-K / E-L suites) |
| ml#1160 | `9fd5b1a` | determinism analyzer refuses to compare an in-flight run |

`main-verify` green on the first three. **ml#1159 and ml#1160 are not this session's work** — they
belong to the determinism / 2×-penalty arc (`Refs juniper-cascor#532`). ml#1159 is listed because
**T5 depends on it** (it guards T5's own mechanism) and because it created the E-K / E-L suites T1
surveys; ml#1160 is listed only so you can date the arc and not mistake it for this one's work.

### 0.2 Two corrections worth not re-inheriting

- **"Two of E-I's three cells would have been truncated" is WRONG — it is one.** From
  `~/.local/state/juniper-experiments/suites/e-i-cascor-cap-ceiling-20260814T091542Z/aggregate.csv`:
  cap 32 → 1497.443 s, cap 64 → 2907.087 s, cap 128 → **4243.571 s** against a 3600 s default. Only
  128 exceeds it; 64 cleared by 692.9 s. The wrong figure originated in a memory file and reached a
  docstring before anyone opened the CSV.
- **A documented blind spot bit in the un-reasoned direction.** ml#1142's wall contract read only a
  suite's own `matrix`/`include`; the `base_config` blind spot was documented as a source of false
  *negatives* and promptly produced false *positives*. Fixed in the same PR. **When you add a "you
  must declare X" gate, ask where else X may legitimately live.** T1 shows this is only half-fixed.

### 0.3 The perf lane is GATED, not "owned elsewhere"

`notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md` owns the
plan's §12 as its inventory item **F**, Tier 4, **gated** behind F-P1→F-P4 with owner PF-threshold
ratification. Its "not scheduled here" list names the wide-budget campaign (its **G**, now finished)
and the defect register (its **H**).

Practical consequence for T1: do not start perf runs, and treat any edit under
`util/experiments/suites/perf/**` as requiring an explicit decision — **including `pf5`, which T1's
own survey flags** (§1.2).

### 0.4 Predecessor residuals — disposition

The predecessor's §9 declared three residual clauses it did not re-derive. Their status today:

| clause | status |
|--------|--------|
| R-6 "retire the ad-hoc shim" | **CLOSED.** `util/ad-hoc/2026-08-10_driver_stall_shim.py` is gone; `tests/test_experiment_suite_yamls.py:319 StallShimRetirementTest` anti-resurrects it. |
| R-2 tooling-generalization | **CLOSED.** `util/ad-hoc/2026-08-10_ea_aggregate_clean.py` now takes a suite prefix + run root ("Originally E-A-only (hence the filename); now takes the suite prefix, run root, and expected…"). |
| R-1 second clause — *do not report `succeeded` when zero candidates were installable* | **UNVERIFIED and homeless.** cascor#509 is closed but this clause was never independently confirmed. It is **not** adopted here; see §9. |

---

## 1. T1 — the wall-budget knob shipped with one adopter, and nine suites have an ordering defect

ml#1142 added `execution.max_wall_seconds` to `run_suite`'s `EXECUTION_KEYS` and forwards it as
`--max-wall-seconds`. That is the *mechanism*. The *integration* never happened.

### 1.1 Adoption is 1 of 23

23 suite files under `util/experiments/suites/`; exactly **one** declares `execution.max_wall_seconds`
— `perf/pf3-cascor-pool-scaling.yaml:24`, set by ml#1142 itself. Everything else inherits from
`base_config`, except E-I which overrides `outputs.max_wall_seconds` in its matrix (`:71`).

Inheriting a correct budget is fine. It is only wrong where the inherited number and the suite's own
timeout disagree — which is the rest of this section.

### 1.2 The ordering rule, and who breaks it

`per_run_timeout_seconds` is only run_suite's **subprocess** timeout. When it is *below* the driver's
effective wall budget, run_suite kills the driver from outside, records `timed_out` with
`exit_code: null` (`util/experiments/run_suite.py:350-353`, which returns **before** the manifest read
at `:355`), and **the driver never writes its manifest** — the honest `timed_out` record of the plan's
§13.4 is lost.

The rule is stated in-repo, correctly, by a suite author: `p4/e-j-h2h-wide-cap64.yaml:73-75` —
*"per_run_timeout_seconds (15600) is deliberately ABOVE the config's outputs.max_wall_seconds (14400):
the DRIVER must be what stops a run, because it writes an honest `timed_out` manifest where a
run_suite subprocess kill leaves none."* **The knowledge existed and was not carried forward.**

Full survey of all 23 suites, resolving each `base_config` the way `_resolve_base_config` does
(driver default 3600 where a base pins nothing):

**INVERTED — subprocess kills first (3):**

| suite | timeout | effective budget | app |
|-------|---------|------------------|-----|
| `p4/e-k-thread-probe-cap16.yaml:37` | 7200 | 14400 | cascor |
| `p4/e-l-determinism-cap4.yaml:27` | 3600 | 14400 | cascor |
| `recurrence-d-sweep.yaml:17` | **600** | **900** | recurrence |

**EQUAL — a race, whichever fires first (6):** `cascor-budget-sweep.yaml` (3600/3600),
`p4/e-c-cascor-noise-robustness.yaml:26` (3600/3600), `p4/e-d-recurrence-d-sweep.yaml` (900/900),
`p4/e-f-recurrence-irregularity.yaml` (900/900), `p4/e-g-recurrence-cv-scheme.yaml` (900/900),
`perf/pf5-recurrence-d-scaling.yaml` (900/900).

**OK: 14.** So a gate with the predicate `per_run_timeout_seconds <= effective_budget` fires on
**nine** suites. Expect that; it is not a gate bug.

Two things that survey changes:

- **Five of the nine are `app: recurrence`** (`recurrence-d-sweep`, `e-d`, `e-f`, `e-g`, `pf5`), which the existing wall gate can never see:
  `tests/test_experiment_suite_yamls.py:253` short-circuits `if doc["suite"]["app"] != "cascor"`.
  The recurrence budget is the socket timeout on the synchronous `POST /v1/train`, a different
  failure mode this document does not analyse — **do that analysis before "fixing" a recurrence row.**
- **`perf/pf5` is inside the perf lane** (§0.3). Flag it; do not unilaterally edit it.

### 1.3 It is latent — and here is the measurement, not an extrapolation

No run has been truncated. Measured on this host:

| suite | measured wall | its timeout | outcome |
|-------|---------------|-------------|---------|
| E-K (`e-k-thread-probe-cap16-20260817T211146Z`) | **981.6 s** | 7200 | `succeeded` |
| E-L (`e-l-determinism-cap4-20260818T032548Z`) | **229.0 s** | 3600 | `succeeded` |

It is a misconfiguration waiting for a slower host or a wider cell, not an active failure. Say so.

### 1.4 Where the gate goes

- ml#1142's wall contract fires only on `max_hidden_units >= 64` **and** `app == cascor`.
- ml#1152's driver check compares **stall vs wall** and cannot see `per_run_timeout_seconds` at all —
  that value lives in run_suite and is never passed to the driver (`grep per_run_timeout` in
  `run_experiment.py` → no match).
- `run_suite` knows both: it reads the timeout at `run_suite.py:426` and the budget at `:429`, and
  `expand_cells` resolves `base_config` via `_resolve_base_config` (`:190`, `:203`).
  **Correction to a claim in this document's first draft**: `materialise_cell` does *not* call it — it
  consumes the already-resolved `cell["config_path"]` (`:215`).

**Two constraints on the implementation.** The effective budget is **per-cell**, not per-suite — E-I
sets it through the matrix — so a `load_suite`-time check cannot see it; only post-`expand_cells` can.
And mirror ml#1142's decision to **decline to judge** when a base config is an uncloned sibling;
`tests/test_experiment_suite_yamls.py::_inherited_wall_budgets` is the worked precedent, including its
`unresolved` return.

**Severity is an open choice, and it is a decision, not an implementation detail.** An inverted
ordering silently destroys evidence, whereas ml#1152 chose *non-fatal* for the inert stall window
because the run itself stays valid. Do not copy that severity across without arguing it — and note
that with nine suites currently failing the predicate, a hard failure blocks CI until all nine are
resolved. Raise it with Paul.

### 1.5 The stall gate is still blind where the wall gate is not

ml#1142 added `_inherited_wall_budgets` (`tests/test_experiment_suite_yamls.py:140`) so the **wall**
contract can see a `base_config` budget. `_oversize_reasons` (`:113-122`) was left reading only
`_declared_numbers` (matrix / include), so the **stall** contract still cannot see a
`candidate_pool_size` or `max_hidden_units` inherited from a base config.

`e-l-determinism-cap4.yaml` demonstrates it: it declares only `max_hidden_units: [4]` (`:29`); its
`candidate_pool_size: 8` comes from `util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml:124` and is invisible
to the gate. Pool 8 is below the threshold so nothing trips today — but a suite inheriting pool 32
would slip through. Same file, same helper, one commit. This is §0.2's own lesson applied
asymmetrically.

### 1.6 The `util/ad-hoc/` durability risk (raised with Paul 2026-08-17; deliberately not acted on)

Five shipped suites — the three `e-j-h2h-*`, `e-k-thread-probe-cap16`, `e-l-determinism-cap4` — take
their `base_config` from `util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml`.

**State the risk accurately**: AGENTS.md's *Script placement* rule (`:904-911`) governs **scripts**
(`util/ad-hoc/<name>.{py,bash}`) and says nothing about `.yaml` configs, so it does not by itself
forbid this. The risk is practical, not policy: a routine ad-hoc cleanup would silently re-point five
suites at the driver default. Relocating it is a **Paul decision** and belongs to the determinism arc
that created those suites (§0.1), not to this one.

### 1.7 Acceptance for T1

- The 23-suite survey re-run and recorded: declared budget, inherited budget, timeout, verdict.
- The three inverted suites fixed **or** consciously waived in writing — with E-K/E-L routed to the
  determinism arc and `recurrence-d-sweep` analysed against the recurrence failure mode first.
- **A disposition for the six EQUAL-race suites too** — they are not covered by the inverted bullet.
  Deciding they are acceptable is a fine outcome; leaving them unmentioned is not, because a gate
  using `<=` fires on all nine.
- A gate on the ordering, with a negative control proving it bites, and a stated severity decision.
- `_oversize_reasons` reads inherited pool/cap (§1.5), or an explicit note saying why not.
- No edit under `util/experiments/suites/perf/**` without an explicit decision (§0.3).

---

## 2. T2 — Q-1's `experiment.resolved.yaml`: decided, unimplemented, and not implementable as literally specified

- Reserved in the §6.4 RUN_DIR layout: plan **`:571`** —
  `experiment.resolved.yaml           # PROPOSED: fully-materialised defaults (Q-1)`
- Answered in the Q-table: plan **`:1221`** — *"Yes — dumped from the live `Settings` object, not
  hand-reconstructed."*
- Restated as decided-but-unimplemented in the trailer ml#1142 added: plan **`:1345`**.
- `grep -rn "experiment.resolved" util/` → **no match**.

The decision is on record, so this is a gap rather than an owner call — **but it cannot be built as
worded.** The driver is an HTTP client; it never constructs the app's `Settings`. cascor exposes no
settings endpoint (`GET /v1/training/params` covers `TrainingParams` only) and the recurrence path has
no equivalent at all. So T2 is really **design-then-build**, blocked on one of:

1. a new read-only settings surface in cascor (and recurrence), or
2. an owner re-scoping to "re-serialise the driver's resolved config" — which is explicitly *not*
   what plan `:1229` says, and would re-admit the hand-reconstruction error class it was meant to kill.

Raise that choice before writing code. Do not silently pick (2).

**Do not mistake the adjacent artifact for this one**: `materialise_cell` writes a resolved per-cell
`cells/<id>/experiment.yaml` (`run_suite.py:231-234`), which is neither named nor placed as Q-1
specifies and exists only for suite runs.

**Acceptance**: the design choice recorded as a decision; if (1), the endpoint plus the driver write;
either way a test that the file exists and round-trips for both apps.

---

## 3. T3 — W-4: the install hint the operator is sent to does not exist

`util/experiments/run_experiment.py:658` refuses an unavailable generator with:

> `dataset.generator '<g>' is registered but unavailable on this host (missing optional dependency; see GET /v1/generators for the install hint)`

That endpoint carries no hint. `GeneratorInfo` is declared at
`juniper-data/juniper_data/core/models.py:111` with exactly five fields at **`:114-121`** — `name`,
`version`, `description`, `available`, `params_schema` (aliased `schema`) — and
`juniper_data/api/routes/generators.py:213` constructs it with exactly those five. The registry
`description` (`generators.py:166`) carries no install text either.

The actionable string exists only on the **501** path of `POST /v1/datasets`: it lives in the
generator's `ImportError` (`juniper_data/generators/mnist/generator.py:76` —
`"Install with: pip install datasets"`) and reaches a client through the `{e}` interpolation at
`juniper_data/api/routes/datasets.py:167`. The driver's preflight never gets there.

**G-16 is the same wound from the other side** — plan **`:238`** (*not* `:201`; the predecessor's
anchor was wrong and its own row independently cites the 501 mapping as `datasets.py:165-168`).
`mnist` is unavailable on this host because HF `datasets` is absent, so a cascor mnist experiment
501s. Fixing W-4's message makes G-16 self-explaining.

Fix either half: add the hint to `GeneratorInfo`, or point the driver message at the 501 path.
W-4's docs half is genuinely done.

**Acceptance**: a PR on **juniper-data** (this is cross-repo); a test asserting `GET /v1/generators`
carries actionable install text for an unavailable generator, or that the driver's message names the
501 path; G-16 re-checked against a live `mnist` refusal.

---

## 4. T4 — W-9: the cross-check that was supposed to retire the hand-kept mirror never runs in CI

`juniper-data-client/tests/test_generator_parity.py:32` still defines `EXPECTED_SERVER_GENERATORS` as
a hand-maintained `frozenset` of **16** names. The live cross-check meant to make it self-maintaining,
`test_pinned_mirror_matches_live_registry`, guards on `if live is None:` (**`:152`**) and calls
`pytest.skip` (**`:153`**) when `juniper_data` is unimportable.

**No juniper-data-client CI lane installs juniper-data.** The four `pip install -e ".[test]"` sites in
`.github/workflows/ci.yml` are at **`:228`, `:321`, `:431`, `:543`**, and `[test]`
(`pyproject.toml:35-43`) is pytest / pytest-cov / pytest-timeout / responses / juniper-observability.
So the cross-check always skips in CI and the frozenset is exactly as stale-able as before W-9.

**Trap when you verify this:** `juniper_data` *is* importable on this workstation, so the cross-check
runs and passes locally. **Local green proves nothing about the CI lane** — read the workflow.

**Acceptance**: a PR on **juniper-data-client**; the cross-check must *run*, not skip, in at least one
CI lane — assert that positively (e.g. fail when `live is None` in CI) rather than trusting a green
run that skipped.

---

## 5. T5 — L-2 and L-4: raise the decisions, do not code them

**Read ml#1159 (`49cc073`) first.** It landed *after* the predecessor was written and directly
concerns this mechanism: `load_config` now records a `validation_warnings` entry naming the 10000
fallback and carries it on the **manifest**, documented as the plan's §5.6 rule 7 and in AGENTS.md.
It was deliberately non-fatal (spiral-baseline ships the split, so erroring would break the canonical
baseline). The *decision* below is still open; the *trap* is now guarded and instrumented.

All anchors below are at juniper-cascor **`9a7e7e0`** — see §10, they moved.

### 5.1 L-2 — an open semantic question

`fit` (`src/cascade_correlation/cascade_correlation.py:1803`) consumes `max_epochs` at **`:1891`**
(`train_loss = self.train_output_layer(x_train, y_train, max_epochs)`) but never forwards it to
`grow_network` (**`:4469`**), whose per-round passes read `self.output_epochs` at **three** sites:
**`:4594`** and **`:4823`** (`train_output_layer`) and **`:4771`** (`_retrain_output_layer(...,
epochs=self.output_epochs, ...)`). A forwarding change must cover all three.

ml#1159 adds the asymmetry that makes it matter: the **service** leaves later passes at
`self.output_epochs`, which falls back to `_PROJECT_MODEL_OUTPUT_EPOCHS = 10000` when unset, while the
**direct CLI** aliases `max_epochs → output_epochs` (`src/main.py:246`), so it bounds *every* pass. A
config carrying only `max_epochs: N` therefore runs the CLI at N per pass and the service at N then
10000.

The code says it is unsettled: the scope note at **`:1874`** (added by cascor#522) states it is *"an
open semantic question, not settled here"*.

**Why it is a decision, not a patch**: `max_epochs` is in `TrainingLifecycleManager._FIT_KWARGS`
(`src/api/lifecycle/manager.py:2067`, with `epochs`, `max_iterations`, `early_stopping`), so
forwarding it **changes service behaviour and is golden-suite-visible**.

### 5.2 L-4 — wider than the one key it was filed under

`_W11_TRAINING_KEY_MAP` (`src/main.py:246`) admits exactly **eight** keys — `learning_rate`,
`correlation_threshold`, `max_hidden_units`, `patience`, `candidate_epochs`, `candidate_pool_size`,
`output_epochs`, `max_epochs` (the last as an **alias** to `output_epochs`; an explicit
`output_epochs` wins). Every other experiment-YAML training key is logged and dropped at **`:437`**:

> `W-11: experiment-YAML keys with no direct-CLI counterpart (service-tier only), IGNORED here: …`

`early_stopping` appears **nowhere** in `src/main.py` (`grep -c` → `0`), and `fit()` defaults it to
`True` (`cascade_correlation.py:1812`), so the direct CLI always early-stops. Shipped configs already
set dropped keys — `spiral-baseline.yaml` drops `candidate_learning_rate`, `candidate_patience`,
`convergence_threshold`, `early_stopping`, `max_iterations`. **A direct-CLI run is therefore not
configured the way its YAML reads.**

**The coupling that matters**: the R-3 cap-reading rule — a cap-bound cell reports `early_stopped`,
disambiguated by `units == max_hidden_units` — holds *only* under `early_stopping: true`. The first
config that sets it false changes how every outcome column is read, silently, on the direct CLI only.

**Acceptance**: both questions put to Paul as explicit choices (extend the map? make the drop fatal?
document and move on?), with ml#1159's guard as the current state. No code before an answer.

---

## 6. T6 — E-C's published evidence is knowingly stale (a compute decision)

`util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml` was rebased onto `spiral-baseline` and
given E-A-class budgets on **2026-08-13 00:43** (`ff4e2ca`, ml#1075). The newest E-C run on this host
is `e-c-cascor-noise-robustness-20260811T095213Z` — **two days earlier**. The published surface is
still the cap-bound one whose spiral curve is flat *because the unit cap binds* (F-6), not because
noise does not matter.

ml#1142 recorded that in the evidence doc (`KNOWINGLY STALE`,
`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md:108`), so the
honesty half is **done**. What remains is the re-run, which costs GPU hours and is **Paul's call**.

**Do not re-litigate R-4.** The owner decided to give E-C's spiral rows an E-A-class budget rather
than reduce E-C to a moon-only study; the suite already encodes it.

**Separate, and separately unowned — do not fold it into the E-C decision**: cascor#514 changed
candidate patience, and the R-5 evidence doc
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R5-SERVICE-VS-CLI-EVIDENCE.md`) §5.1
established that spiral figures are not comparable across it, so the
published **E-A** and **E-I** grids carry the same currency caveat. That re-baselining is engineering
with no owner, not a GPU-budget question. It is **not** adopted here; see §9.

---

## 7. T7 — Q-12: proposed, not ratified

`notes/JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md:7` carries status
*"PROPOSAL — IDs become official only at the next snapshot refresh"*. The Wave 7.6 row is plan
**`:1196`** and its verb is *Propose*, so **the wave item is done** (the plan's own trailer says so at
**`:1352`**); ratification remains.

There are **zero** `JR-REC-` IDs in `notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md`
and zero in `notes/requirements/id_assignments.yaml` — do not read that as the proposal being missing.

**Do not go looking for `notes/requirements/by-area/REC.md`.** Those 15 files are **area** codes
(`API` … `WS`); `REC` is an **owner** code, so one would never exist.

Plan **`:1293`** (*not* `:1171`) lists the minimum coverage: the experiment-config layer (§5.5), the
plotting gap (G-5), the bench `--results-dir` and `ar_p` registration (W-5/W-7), the missing Grafana
dashboard (G-4), and the absent `performance` marker (G-17).

**Blocked on**: a requirements snapshot refresh. This document does **not** know who triggers one or
on what cadence — establish that first, or T7 cannot start. If no refresh is scheduled, the honest
outcome is to say so and leave the proposal as the record.

---

## 8. Live state, probed 2026-08-18 — re-probe, do not copy forward

- **No experiment driver, no campaign, no experiment listeners.** The head-to-head campaign has
  finished; ports `8110-8139` / `8230-8259` / `8260-8289` are clear and the reaper reports
  `0 protected (live experiment)`.
- The reaper reports **2 would be reaped** — a `multiprocessing.resource_tracker` and a `forkserver`
  child, both `ppid 51427` = `systemd --user`. **Genuine orphans**; reaping them is correct. They are
  left only because nobody asked.
- **The `juniper-deploy` Docker stack is up**: canopy `127.0.0.1:8050`, cascor `8201`, recurrence
  `8211`, Grafana `3001`. **Do not tear it down.**
- A native listener holds `*:3000` — it is **Domotz, not Grafana** (F-P1-2 was a misdiagnosis, closed
  2026-08-16). Deploy's Grafana is the loopback `:3001` instance.
- The isolated E2E trio (`8051` / `8101` / `8202`) is **down**.
- `ss -tlnpH 'sport = :A' 'sport = :B'` returns EMPTY with exit 0 — one port per call, or you will
  manufacture a false "the stack is down".

---

## 9. What this document does NOT cover

Stated so the next sweep does not assume the plan is now fully swept:

- **R-1's second clause** (§0.4) — unverified, homeless.
- **E-A / E-I re-baselining** post-cascor#514 (§6) — engineering, unowned.
- **The plan's §12.2 items 1 and 3** — run-level durations are not a metric; no cross-app comparison
  surface. Neither re-derived here.
- **G-17** (recurrence has no `performance` marker; its bench writes offline JSON only) — named in
  T7's coverage list but not itself adopted.
- **PF-4 / PF-8** — the predecessor said these "need a decision, not a suite"; still true, still
  gated behind §0.3.
- **F-7 provenance re-pin** — ml#1142 recorded the recurrence re-pin beneath the plan's authoring-time
  table; the table itself is deliberately unchanged. No further action assumed.
- Anything inside the defect-register or canopy-E2E arcs.

---

## 10. Git state

**Authoring session**: worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/soft-hopping-haven`, branch
`handoff/cli-exp-unowned-tasks`, working tree clean apart from this file.

- `juniper-ml`: `origin/main` at **`76e4513`** at authoring. It moved four times during the previous
  session's work; assume it has moved again.
- `juniper-cascor`: `origin/main` at **`9a7e7e0`** (`fix(runtime): apply one BLAS thread policy at
  BOTH entry points (#531) (#533)`). The predecessor's `7fa2e66` is **one commit behind**, and #533
  shifts every §5 anchor — `src/main.py` `238 → 246` and `429 → 437`, `grow_network` `4466 → 4469`,
  the per-round passes `4591 → 4594`, `4768 → 4771` and `4820 → 4823`. **All §5 anchors above are already at
  `9a7e7e0`.** Re-probe anyway.
- **juniper-cascor has open issues** #530 (*TrainingParams has no seed field*) and #532 (*seeded runs
  do not reliably reproduce*), both from the determinism arc. The predecessor's "zero open issues" no
  longer holds.
- Open ml PRs at authoring: #1150, #1149, #1148, #1147, #1139 — none from this arc.
- **Merge traps that cost real time in the predecessor session**, recorded in
  `reference_github_pr_ci_trigger_traps`: merging a base with `--delete-branch` irreversibly closes a
  stacked child; `gh pr edit --body-file` can silently no-op behind a Projects-classic warning (use
  `gh api -X PATCH ... -F body=@file`); `until gh pr checks N | grep -qv pending` does **not** mean
  "until nothing is pending" (use `until ! ... | grep -q pending`).
- Carry any `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` trailer into the **squash** commit message,
  or post-merge `main-verify` goes red on a waiver the PR itself had.

---

## 11. Verification commands

**Run from the CANONICAL checkout `/home/pcalnon/Development/python/Juniper/juniper-ml`.** Sibling
paths are absolute below precisely because `../juniper-*` does **not** resolve from a worktree, and
AGENTS.md makes worktree isolation the standing procedure.

Re-confirm any anchor before acting on it; if a path, symbol or flag does not resolve, **stop and
report rather than substitute a nearby one**.

```bash
J=/home/pcalnon/Development/python/Juniper
PLAN=notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md

git fetch --prune && git log --oneline HEAD..origin/main    # empty before committing
gh pr list --repo pcalnon/juniper-ml --state open           # dup-guard; turns over in minutes
git -C $J/juniper-cascor rev-parse --short HEAD             # expect 9a7e7e0 or newer
git -C $J/juniper-cascor rev-parse --short origin/main

# T1 — one adopter; the ordering survey; the in-repo statement of the rule
grep -rn "max_wall_seconds" util/experiments/suites/ --include=*.yaml
grep -n "per_run_timeout_seconds" util/experiments/suites/recurrence-d-sweep.yaml
sed -n '73,76p' util/experiments/suites/p4/e-j-h2h-wide-cap64.yaml
sed -n '426,430p' util/experiments/run_suite.py        # timeout + budget, the gate seam
sed -n '113,122p' tests/test_experiment_suite_yamls.py # _oversize_reasons, still matrix-only

# T2 — decided, unimplemented
grep -rn "experiment.resolved" util/                   # expect NO match
sed -n '571p;1221p;1345p' "$PLAN"   # locate by pattern if these drift

# T3 — five fields, no hint
sed -n '111,121p' $J/juniper-data/juniper_data/core/models.py
sed -n '167p'     $J/juniper-data/juniper_data/api/routes/datasets.py
grep -n '^| \*\*G-16\*\*' "$PLAN"                     # G-16

# T4 — the cross-check cannot run in CI
sed -n '152,153p' $J/juniper-data-client/tests/test_generator_parity.py
grep -n 'pip install -e "\.\[test\]"' $J/juniper-data-client/.github/workflows/ci.yml

# T5 — at cascor 9a7e7e0
grep -n "L-2 (scope note)" $J/juniper-cascor/src/cascade_correlation/cascade_correlation.py   # 1874
grep -n "self.output_epochs" $J/juniper-cascor/src/cascade_correlation/cascade_correlation.py # 4594/4771/4823
grep -n "_W11_TRAINING_KEY_MAP = {" $J/juniper-cascor/src/main.py                             # 246
grep -c "early_stopping" $J/juniper-cascor/src/main.py                                        # expect 0

# T6 / T7
git log -1 --format='%ad %h' --date=iso -- util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml
ls -dt ~/.local/state/juniper-experiments/suites/e-c-* | head -1
grep -n '^| 7.6 |' "$PLAN"; grep -n 'Work item 7.6 (PROPOSED)' "$PLAN"
grep -c "JR-REC-" notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-INDEX.md   # expect 0
```

Relevant suites: `python3 -m unittest tests.test_experiment_suite_yamls tests.test_run_suite tests.test_run_experiment`

---

## 12. Approval

**This document makes no standing-approval claim.** Merge approval is per-session and does not carry
across handoffs. T5 and T6 are explicitly owner decisions; T2's scoping and T1's gate severity are
also decisions. Ask before coding any of them.
