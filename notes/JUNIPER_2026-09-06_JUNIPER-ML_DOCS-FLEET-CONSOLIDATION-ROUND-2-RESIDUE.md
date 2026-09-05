# Docs Fleet Consolidation Round 2 — What Was Held Back

**Project**: juniper-ml
**Author**: Paul Calnon
**Date**: 2026-09-06
**Status**: Evidence record for the 35-PR docs consolidation

---

## 1. What this document is

`util/ad-hoc/2026-09-06_docs_conflict_resolve.py` merges a fleet docs PR by ITEM identity and
**writes nothing it cannot address**. Every line it refuses is printed rather than merged. This
is that printout, adjudicated.

The refusal is the point. The previous consolidation shipped two superseded security bounds
because six gates all passed prose that was well-formed and wrong; a union keyed on the line
cannot tell a new claim from a stale one, so this one declines to try and reports instead.

## 2. The numbers

Across 35 PRs contributing **2841** added lines absent from `main`:

| Verdict | Lines | Meaning |
|---|---:|---|
| LANDED | 26 | the same text is in the merged tree — refused in its own hunk, carried by a keyed sibling from another PR |
| NEAR | 66 | a line sharing its backticked identifiers and anchors is in the tree — the same claim, reworded |
| ABSENT | 173 | nothing like it is in the tree |

**173 of 2841 is 6%.** Classification is by `util/ad-hoc/2026-09-06_docs_residue_audit.py`,
which matches on backticked identifiers and link anchors — prose gets reworded, paths and
anchors do not. A line carrying neither cannot be matched and is reported ABSENT, so the count
errs toward over-reporting loss.

## 3. The four largest contributors, adjudicated

These four are half the ABSENT total, and all four are **superseded drafts**, verified against
`main` rather than assumed.

### #1736 — 33 lines — "Comparator defects still open (source-verified)"

The list names six open defects in `util/experiments/compare_baseline.py`. Five are closed on
`main`, each with a test that would fail if it reopened:

| #1736's claim | Pinned closed by |
|---|---|
| unmeasured cells are dropped, not refused | `ComparatorDefectTest.test_A1_unmeasured_cells_are_refused` |
| `outcome` is never read | `test_A2_a_failed_candidate_is_refused` |
| one unreadable `--suite` turns FAIL(1) into REFUSE(2) | `test_A3_a_real_FAIL_is_not_masked_by_an_unrelated_refusal` |
| duplicate fingerprints collapse | `test_A7_duplicate_baseline_fingerprints_are_refused` |
| scenario coverage is unchecked | `test_A6_partial_scenario_coverage_is_refused` |

Its "Settled contract" prose and determinism census table are already in `docs/REFERENCE.md`
§ Perf-Lane Work Gate, in `main`'s newer wording.

### #1701 — 22 lines — the older operator loop

Resolved by hand. `main`'s loop carries `--force`, which this branch predates. Two things the
branch had and `main` did not were taken: probe ids are full slugs (`--probe-id P19` exits 2)
and the `--class discoverability` form of a `miss`. The rest is an older copy of the same six
commands.

### #1671 — 18 lines — the pre-correction byte-cap argument

`### Why a byte cap is the wrong unit` and its worked example. juniper-ml#1791 landed
*"the byte argument was inverted, and the worked example was false"*, so `main`'s
`## Equities Symbol Cap` is the corrected text and this is what it corrected.

### #1662 — 13 lines — superseded by the hand resolution

Resolved by hand in favour of the branch, not `main`: the branch's `### C5` analysis and
behavioural-test table are on neither side of `main`. The residue is the `main`-side text that
lost, plus two stale forward references the merge corrected (`canopy#567` is merged; the
`2026-09-04_async_blocking_callgraph.py` command names a script that never landed here).

## 4. The rest, verbatim

87 lines across the remaining 31 PRs, listed so the judgement can be re-run rather than
taken on trust. Dominant shapes: table rows whose header sits on neither side of the hunk (a
row written without its header would start a separator-less table — the failure this whole
approach exists to avoid), `Tip:` paragraphs duplicating a cheatsheet row that did land, and
`Operator contract:` pointers to sections that already exist.


### #1736 docs(experiments): operator surface after the terminat

```text
    **Version**: 1.0.73
    **Date**: 2026-09-05
    After juniper-ml#1733 a branch flip REFUSES (exit 2); a same-branch one-step move still FAILS (exit 1).
    **Settled contract (juniper-ml#1733).** `step_count` is exact and deterministic for a seed-fixed config **only given the branch that ended training**. Consensus
    The question was settled by census, not by argument (`util/ad-hoc/2026-09-04_step_count_determinism_census.py`, whole corpus):
    | Fact | Count |
    |------|------:|
    | Distinct configs | 153 |
    | Configs seen more than once | 79 |
    | Still divergent within one branch | **0** |
    **What #1733 changes.** The branch becomes part of the comparison precondition, so a flip is REFUSE (different trajectory) instead of FAIL (false regression). C
    rg -n 'TRUNCATING_TERMINATIONS' util/experiments/read_run_metrics.py
    If that symbol is absent, you are on pre-#1733 code and a branch flip still FAILs. File-header comments and `baseline.json`'s `metric_contract.work` may still s
    **Do not wire `compare_baseline.py` to CI.** `ci.yml` already runs the **unittests**. That is not a run-tier gate against a blessed baseline. Remaining defects
    python util/experiments/make_baseline.py --tag pf1-2026-09-04b --suite SUITE_DIR
    python util/experiments/compare_baseline.py --baseline pf1-2026-09-04b --suite SUITE_DIR
    Whitespace-only `--accept-work-change` is exit 2. Prefer cutting a **new baseline tag** over a waiver — tags supersede by name and are cheap. #1733 verified thi
    ### Termination-branch precondition
    `TRUNCATING_TERMINATIONS = {timed_out, torn_down_early, stalled}` — these stop the **driver**, not the workload, so the histogram is cut short and the count mea
    4. Baseline branch ≠ candidate branch (the 6496 / 6095 counterexample).
    `make_baseline` refuses to bless a suite whose cells ended on different branches or on a truncating state. It will still write `completion_reason: null` if ever
    ### Writer vs comparator — the remaining asymmetry
    A PASS therefore does **not** mean "every cell succeeded and was measured." Read `manifest.outcome`, `manifest.completion_reason`, and the series file yourself
    ### Comparator defects still open (source-verified)
    1. **Unmeasured cells are dropped, not refused.** `summarise` builds `step_counts` only from numeric values. One measured cell among four empty series still rep
    2. **`outcome` is never read.** A `failed` cell with a non-truncating `completion_reason` still PASSes when the remaining counts match. (The #1715 "every cell `
    4. **One unreadable `--suite` converts FAIL(1) into REFUSE(2).** `reasons` are collected across all `--suite` args; any reason forces REFUSED. A real work miss
    5. **Duplicate fingerprints collapse.** `by_fingerprint = {s["workload_fingerprint"]: s for s in scenarios}` keeps the last row. Two baseline scenarios sharing
    6. **Scenario coverage is unchecked.** A two-scenario baseline compared to one matching candidate still PASSes. Missing scenarios are not a refusal.
    ### Work-gate troubleshooting
    > **Operator surface (2026-09-05).** Q-8 writer + split comparator are on main. `step_count` is exact **within a termination branch** ([juniper-ml#1733](https:/
    > **Do not wire the run-tier hook to CI** — remaining comparator defects are listed on the operator page.
    > Operator contract: [`docs/REFERENCE.md` § Perf-Lane Work Gate](../docs/REFERENCE.md#perf-lane-work-gate).
```

### #1701 docs(soak): operator surface after the handoff consens

```text
    Tip: pointer-follow soak — `python3 util/soak_run_probe.py --dry-run` then run; score with `--reveal` only after. Use the full slug (`P19-port-check-fail-opens`
    Protocol: [`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`](../notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md). Trigger d
    On this tree the terminal-verdict refuse in `soak_run_probe.py` runs **before** the `--dry-run` branch (`util/soak_run_probe.py` ~261–268). `BET-FAILING` / `HOL
    Automated (mechanical): probe selection, unprimed dispatch, transcript capture, the **retrieval channel**. `parse_events` walks `tool_use` blocks only (`grep -n
    ### Least-covered vs characterisation — do not run n≈8–10
    For a relocation decision the pooled rate is a **mixture**. Characterisation runs (juniper-ml#1616; design-conversation §9) showed the probes do not share one r
    As of this `origin/main` tip: `python3 util/soak_ledger.py report` prints **INCONCLUSIVE**, seeded 40/35, 26 follows / 2 misses / 12 source-recovered, rate 65.0
    Per-probe on this ledger (effective outcome after rescores; Wilson on follows/n):
    Within n=8–10, Wilson's low-side resolving threshold is `k ≤ 1` at every point in the band and loosens only at n=11. Runs 9 and 10 add trials against an unchang
    | probe | n | follow | src-recovered | miss | rate | 95% CI | excludes 50%? |
    |-------|---|--------|---------------|------|------|--------|---------------|
    | `P14-per-run-timeout-ordering` | 3 | 0 | 3 | 0 | 0% | [0.000, 0.561] | no |
    | `P15-worktree-converge-not-remove` | 3 | 0 | 1 | 2 | 0% | [0.000, 0.561] | no |
    | `P21-pidfile-key-prefix-guard` | 3 | 1 | 2 | 0 | 33% | [0.061, 0.792] | no |
    | `P23-reaper-over-protection-bias` | 3 | 1 | 2 | 0 | 33% | [0.061, 0.792] | no |
    | projected | interval | excludes 50%? |
    |-----------|----------|---------------|
    | 3/8 | [0.137, 0.694] | no |
    | 3/10 | [0.108, 0.603] | no |
    | 9/26 | [0.194, 0.538] | no |
    | 10/31 | [0.186, 0.499] | **yes** — first resolve |
    The **organic** arm is descriptive only (an upper bound). Never used for a verdict. On this tree it has **zero** runs.
```

### #1671 docs(equities): operator surface for the APD-DATA-018

```text
    Tip: default `equities` is **503 S&P names, ~34 min** — 67× over the 30 s data-client timeout. Cost is per ticker, not per byte (a 1-day Russell 3000 payload is
    `equities` / `equities_seq` generation still runs inside the request (`APD-DATA-018`). The csv_import half of that row shipped a **byte** cap ([juniper-data#326
    Bound-the-inputs decision: [`notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md`](../notes/JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-P
    Measured 2026-09-04 (`juniper-data/util/ad-hoc/2026-09-04_measure_equities_payloads.py` and `…_equities_sizing_matrix.py`). Holding the symbol fixed and varying
    The *smaller* payload takes thousands of times longer. A byte threshold that admits the first rejects the second — the **wrong direction** on the axis that matt
    Unit cost (two measurements; the ~2× gap is conditioning + network, and does not change the conclusion):
    - Yahoo chart via `yfinance`: ~1.85 s/request (direct HTTP ~0.34–0.58 s). `_download_ohlcv` calls `yf.download(..., threads=False)` — serial on purpose.
    - SEC EDGAR `companyconcept`: ~0.20 s, 1–2 calls/symbol (`dei:EntityCommonStockSharesOutstanding`, then `us-gaap:CommonStockSharesOutstanding`). Throttle: `_SEC
    - Per-symbol total: **~2.1 s** (2026-09-04) / **4.01 s** (2026-09-02, async-job analysis §1.6). Use **4.0 s** when a single figure is needed.
    **Default request is ~67× over the 30 s budget.** 503 × 4.01 s ≈ **34 min** (any horizon; async-job analysis §1.6). What fits: 30 / 4.01 ≈ **7.5** symbols (cons
    The E-H suite (`util/experiments/suites/p4/e-h-real-data.yaml` and `e-h-recurrence-real-data.yaml`) sets `symbols: [AAPL]` and does **not** set `max_symbols`, s
    # stay inside the ~30 s request budget — pick an explicit list:
        # max_symbols: 10              # silent prefix of the resolved list; no annotation
    ### Operator pitfalls (shipped)
    ### Still an owner call
    A finite `EQUITIES_DEFAULT_MAX_SYMBOLS` (single-digit to low teens) plus the csv_import loud-truncation contract (`InputTooLargeError` → 422 unless opt-in, then
    Do **not** add a tight byte cap as the binding bound — it is anti-correlated with wall time. A generous byte backstop (tens of MB) would only catch a pathologic
    Experiment `--up` redirects it to `$RUN_DIR/equities-cache`. A default (no-`symbols`) request is still ~34 min even when warm helps a *repeat*. See [Equities Sy
```

### #1662 docs(x7): operator surface for the 58-site off-loop ce

```text
    **X7 off-loop census (58):** slice 1a is an AST scan, not ruff. Shipped count is **58** (52 direct + 2 `HELPER` + 4 outside `main.py`) after canopy#567 — not th
    Read design §§3, 5.2, 6, 7 before writing canopy code. Slice **1a** (off-loop discipline) closes X7 **alone**; 1c/1d are load reduction and honesty. Splitting b
    Slice 1a **ships as juniper-canopy#567**. The count moved 40 → 39 → 37 → **52** → **58**. The first three moves each removed a false positive. The fourth added
    The 54-vs-52 delta on v2 vs the pre-#567 gate is exactly two `backend._demo` accessors (`get_network`, `get_current_state`) confirmed in-process and excluded by
    ### The last six — the gate structurally cannot see them
    These are why the count is 58, not 52. Each is fixed in canopy#567.
    The gate was therefore **extended**, not merely satisfied: it now resolves module-level sync helpers transitively (bucket `HELPER` / `_blocking_helpers`). New t
    **v2 resolves assignment provenance** inside the enclosing handler:
    | `_seed_training_state()` — from `lifespan` and `_swap_backend` | Same shape. |
    | `cascor_service_adapter.connect()` → `self._client.is_alive()` | Outside `main.py`. |
    | `_relay_loop()` → `self.extract_network_topology()` | Outside `main.py`. Measured **123 s blocked per 183 s** with no user present. |
    | `service_backend.initialize()` → `attach_to_existing()` | Outside `main.py`. On a **request** path: `_swap_backend` awaits `initialize()` for a runtime model
    | `initialize()` → `CascorStateSync(...).sync()` | Outside `main.py`; receiver is a constructor call. Same request path. |
```

### #1675 docs(e2e): operator surface for the post-#1672 topolog

```text
    Tip: `e2e_seg17_topology_driver.py` scores Topology-tab rows against isolated `:8051`. Trust `STEPS` (`--step` exit `2` on unknown). After #1672, M-06 needs **b
    Row text: [`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](../notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRI
    The registered step names are the `STEPS` dict at the bottom of the file. `--step` rejects anything else (exit `2`). The module docstring's "NOT IMPLEMENTED" li
    ## Canopy E2E topology driver (operational)
    `e2e_seg17_topology_driver.py` scores Topology-tab matrix rows against a live isolated canopy (`JUNIPER_E2E_CANOPY_URL`, default `:8051`). `--step` names must b
    Do not treat the module docstring's "NOT IMPLEMENTED" list as the registry — `topostate` and `topoexport` exist. Do not invent clicks with `gd.emit`.
    `2026-09-04_canopy_verify_instance.bash` brings up a second canopy from a worktree (default `:8052`) beside the shared isolated stack. It does not restart `:805
    Operator contract: [`docs/REFERENCE.md` § Canopy E2E Topology Driver](../../docs/REFERENCE.md#canopy-e2e-topology-driver).
```

### #1638 docs(e2e): operator surface for canopy matrix writes

```text
    `e2e_matrix_rescore.py --write` still writes found rows when some `--row` ids are missing. Do not plan from `e2e_row_coverage.py`. Do not `--overwrite` a named
    ## Canopy E2E matrix writes (operational)
    W-lane ids have no status cell (`no-matrix-row`, not an error). Operator contract: [`docs/REFERENCE.md` § Canopy E2E Matrix Writes](../../docs/REFERENCE.md#cano
    | Script | Default | Load-bearing constraint |
    |--------|---------|-------------------------|
    | `e2e_matrix_fill.py` | dry-run (`--write` to apply) | Locates `status` by header per table; splits on unescaped pipes; first `--verdicts` source wins (newest
    | `e2e_matrix_rescore.py` | dry-run | Named `--row` only. Missing ids warn **and still write** the found rows. |
```

### #1639 docs(e2e): operator surface for the canopy matrix stat

```text
    ## F-CANOPY-027 poller starvation (operational)
    The `e2e_f027_*.py` family is **retained provenance** of the canopy dashboard starvation investigation (finding **FIXED** in juniper-canopy #507 / #509 / #511).
    Operator contract: [`docs/REFERENCE.md` § F-CANOPY-027 Poller Starvation Probes](../../docs/REFERENCE.md#f-canopy-027-poller-starvation-probes).
    Do **not** add a new `dcc.Interval` / poller to "fix" a frozen panel — that re-saturates dash-renderer's hard-coded 12-slot pool. Feed an existing store instead
    Live probes (`e2e_f027_queues.py`, `e2e_f027_ready.py`, `e2e_f027_slots.py`) need a **live isolated** canopy (`JuniperCanopy1`, `DEMO_MODE=0`, empty `LD_LIBRARY
    `e2e_f027_deps_endpoint.py` is a **server-registry** check: run it from `juniper-canopy/src` so `frontend.dashboard_manager` imports. `e2e_f027_cleanroom.py` is
    These scripts are **not** CI. Sibling `e2e_f027_*.py` files in this directory are earlier refutation probes (layout, dispatch, redux, DOM) kept as the twenty-me
```

### #1687 docs(e2e): operator surface for the W6 / Dataset View

```text
    Tip: W6 (`e2e_w6_dataset_driver.py --steps`) is sidebar stage/banner/restart-modal and **stops before `#restart-confirm-button`** — that POST wipes the live net
    ## Canopy E2E dataset drivers (operational)
    `e2e_w6_dataset_driver.py` (W6 sidebar stage → banner → restart **modal**) and `e2e_seg16_dataset_driver.py` (§3.6 Dataset View panel) score the canopy dataset
    - **W6 stops before `#restart-confirm-button`.** That `POST /api/train/restart` ships `reset=True` and wipes the live network. Default `--steps 1,2,4,7` cancels
    - **§3.6 is `--step` (singular, required).** Select is inert; Load on the LIVE arm is expected 400. Scope dropdown options by `aria-controls`.
    - Both need `LD_LIBRARY_PATH=` and the `JuniperCanopy1` interpreter. Target is `JUNIPER_E2E_CANOPY_URL`, not `JUNIPER_E2E_CANOPY_PORT`.
    Operator contract: [`docs/REFERENCE.md` § Canopy E2E Dataset Drivers](../../docs/REFERENCE.md#canopy-e2e-dataset-drivers).
```

### #1731 docs(e2e): operator surface for the unfilled-rows ledg

```text
    **Version**: 1.0.72
    **Date**: 2026-09-05
    Tip: plan canopy E2E re-drives from `python3 util/ad-hoc/e2e_unfilled_rows.py`, not `e2e_row_coverage.py`. The ledger reads matrix `status` cells (`C2.` / `M-`
    ## Canopy E2E unfilled-rows ledger (operational)
    `e2e_unfilled_rows.py` is the **ledger** reader for the click-by-click matrix. It lists `C2.` / `M-` rows whose `status` cell is still a placeholder (`""`, `—`,
    `e2e_row_coverage.py` is an **estimator**: it diffs matrix row ids against `reports/e2e/*/statuses.tsv` and `rowlog.md`. It can list already-`PASS` rows as rema
    Operator contract: [`docs/REFERENCE.md` § Canopy E2E Unfilled-Rows Ledger](../../docs/REFERENCE.md#canopy-e2e-unfilled-rows-ledger).
```

### #1668 docs(partition): operator surface for the shipped NPZ

```text
    **Last Updated**: 2026-09-04
    **Status**: PLAN v3 — **round 3 returned NOT RESOLVED on all four targets; four of its seven findings
    have since moved.** §9 is still the live record and is **not** folded into §§2–7, which remain
    v3-as-reviewed rather than v3-as-corrected. **Still do not implement from this document.**
    The partitioning question is CLOSED on the design of record (decisions 9 REVERSED / 10 COLLAPSED /
    11 / 12). Operator surface: [`docs/REFERENCE.md` § Train / Val / Test Partition Contract](../docs/REFERENCE.md#train--val--test-partition-contract).
```

### #1674 docs(e2e): operator surface for the topology-tab score

```text
    Tip: `e2e_seg17_topology_driver.py` scores Topology-tab rows against isolated `:8051`. Trust the `STEPS` dict (`--step` exit `2` on unknown names) — the docstri
    ## Canopy E2E topology driver (operational)
    `e2e_seg17_topology_driver.py` scores Topology-tab matrix rows against a live isolated canopy (`JUNIPER_E2E_CANOPY_URL`, default `:8051`). `--step` names must b
    Do not treat the module docstring's "NOT IMPLEMENTED" list as the registry — `topostate` and `topoexport` exist. Do not invent clicks with `gd.emit`.
    Operator contract: [`docs/REFERENCE.md` § Canopy E2E Topology Driver](../../docs/REFERENCE.md#canopy-e2e-topology-driver).
```

### #1680 docs(experiments): operator surface for the suite driv

```text
    Tip: `run_suite.py` expands `base_config × matrix` then `--up`/`drive`/`--down` per cell. `--dry-run` writes nothing. `--resume` skips only `succeeded`. Cascor
    `util/experiment_stack.bash` + `util/experiments/run_experiment.py` are the **per-run** CLI experimentation tooling (plan Wave 2.1–2.6; this section is Wave 2.7
    Local orchestration scripts in `util/` also read the host-stack variables documented in [Host Orchestration Utilities](#host-orchestration-utilities), the E2E o
    Operator surface for the shipped suite driver (`util/experiments/run_suite.py`, Wave 7.1 / 7.5): [`docs/REFERENCE.md` § Suite driver](../docs/REFERENCE.md#suite
```

### #1652 docs(e2e): operator surface for the F-CANOPY-037 rende

```text
    Tip: F-CANOPY-037 painted in 2 of 11 sessions — one green `topodiag` is ~18% likely while still broken. `e2e_f037_render_census.py` exits 0 even at `painted==0`
    `JUNIPER_E2E_SEG17_RESULTS` is the per-session structured-verdict path the F-037 census sets for each `topodiag` child (default `$JUNIPER_E2E_RUN_DIR/seg17_resu
    `e2e_f037_render_census.py` runs N independent `topodiag` sessions (default 11, the finding's sample). A single green session is ~18% likely while the race is s
```

### #1657 docs(register): operator surface for the close-protoco

```text
    ## Defect-register close protocol (operational)
    `register_open_set.py` uses a **relative** `Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md")`. Run it from the juniper-ml repo root or it r
    Operator contract: [`docs/REFERENCE.md` § Defect Register Close Protocol](../../docs/REFERENCE.md#defect-register-close-protocol).
```

### #1678 docs(experiments): operator surface for the suite driv

```text
    Tip: `run_suite.py` expands a suite YAML into cells and runs each as up → drive → down. `--resume` skips only `succeeded`; `--only` of a subset still exits `1`
      - A suite could always reach the budget through a dotted `outputs.max_wall_seconds` override (`suites/p4/e-i-cascor-cap-ceiling.yaml:71` does exactly that), b
    Local orchestration scripts in `util/` also read the host-stack variables documented in [Host Orchestration Utilities](#host-orchestration-utilities), the E2E o
```

### #1692 docs(cascor): operator surface for the primary-checkou

```text
    ## Cascor primary freeze tell (operational)
    Exit 1 = freeze in force. Exit 0 is **no user-owned importer**, not "no importer" — root-owned `/proc/<pid>/{fd,environ,maps}` are unreadable. Sibling `juniper-
    Operator contract: [`docs/REFERENCE.md` § Cascor Primary Freeze Tell](../../docs/REFERENCE.md#cascor-primary-freeze-tell).
```

### #1696 docs(experiments): operator surface for reading Wave 2

```text
    Tip: `stats.json` is the Wave 2.6 archive, not the WORK/SPEED gate. `outcome.wall_seconds` is de-ratified `timings.total`. Cascor `p50`/`p95` are per-poll means
    `util/experiment_stack.bash` + `util/experiments/run_experiment.py` are the **per-run** CLI experimentation tooling (plan Wave 2.1–2.6; this section is Wave 2.7
    **Operator surface (Wave 2.6).** How to read `artifacts/results/stats.json` / `summary.md` — de-ratified `wall_seconds`, per-poll step-duration honesty, `scrape
```

### #1730 docs(requirements): operator surface for the v5 consol

```text
    **Version**: 1.0.71
    **Date**: 2026-09-05
    Tip: never regenerate `notes/requirements/` views from `id_assignments.yaml` — the ledger has no `detail`. Run `python3 util/requirements_consolidate.py --check
```

### #1615 docs(ruleset): operator surface for require_context_sa

```text
      - **Known limitation**: only the suite's own `matrix` / `include` are read, so a pool or cap inherited from `suite.base_config` is invisible — deliberate, bec
      The Q-2 detector watches `current_epoch`, which does not advance while the CANDIDATE pool trains, so those cells are recorded `stalled` while perfectly health
```

### #1619 docs(experiments): operator surface for perf-lane read

```text
    Tip: do **not** gate on `aggregate.csv` `wall_seconds` or `manifest.timings.drive` (poll-quantized).
    `python util/experiments/read_run_metrics.py SUITE_DIR` reads the last `metrics_series.csv` row.
```

### #1649 docs(experiments): operator surface for suite-report g

```text
    Tip: `run_suite` `aggregate.csv` / `REPORT.md` now carry both gate inputs (`step_count` WORK, mean step SPEED) beside de-ratified `wall_seconds`. `--compare-bas
      - **P2 item 1.4 (juniper-ml#1643):** `aggregate.csv` carries `step_count` and `mean_step_seconds` beside the de-ratified `wall_seconds`; `REPORT.md` has a **G
```

### #1665 docs(experiments): operator surface for the run lister

```text
    Tip: `list_runs.py` is directory-truth (ignores `run_suite` `index.jsonl`). `--prune` deletes the whole `RUN_DIR`, unlike `--down` which keeps `artifacts/`. It
    `util/experiment_stack.bash` + `util/experiments/run_experiment.py` are the **per-run** CLI experimentation tooling (plan Wave 2.1–2.6; this section is Wave 2.7
```

### #1705 docs(soak): dry-run spends no session, so the stopping

```text
    Tip: pointer-follow soak — `python3 util/soak_run_probe.py --dry-run` then run; score with `--reveal` only after. Full-slug `--probe-id` (bare `P19` exits 2). `
      - Test hooks: `JUNIPER_REAP_PROC_ROOT`, `JUNIPER_REAP_KILL_CMD` (plus the two run-root vars, redirected per-test). Operator surface: [docs/REFERENCE.md § Pyte
```

### #1621 docs(soak): operator surface for pointer-follow charac

```text
    Local orchestration scripts in `util/` also read the host-stack variables documented in [Host Orchestration Utilities](#host-orchestration-utilities), the E2E o
```

### #1628 docs(experiments): operator surface for the split comp

```text
    Identity (`workload_fingerprint`) first — a config edit is REFUSED (exit `2`), not a work FAIL (exit `1`). Speed cannot fail the gate.
```

### #1641 docs(worktree): operator surface for the in-use probe

```text
    Tip: before removing a worktree you did not just leave, run the cwd-only liveness probe **and** `python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py WT`. An
```

### #1646 docs(e2e): operator surface for finding-triage disposi

```text
    Tip: Phase 2 exit is "every P0 and P1 closed or explicitly deferred". Run `python3 util/ad-hoc/e2e_finding_triage.py` rather than a hand list. It reads only the
```

### #1651 docs(experiments): operator surface for csv_import byt

```text
    Generators: `spiral`, `xor`, `gaussian`, `circles`, `checkerboard`, `csv_import` (128 MiB cap; 422 until `allow_truncation`; **not** a cascor staging target), `
```

### #1654 docs(e2e): operator surface for the F-CANOPY-037 rende

```text
    The F-CANOPY-037 census inherits `JUNIPER_E2E_CANOPY_URL` (default `http://127.0.0.1:8051`) and writes per-session `JUNIPER_E2E_SEG17_RESULTS`. It does not take
```

### #1660 docs(soak): operator surface for pointer-follow charac

```text
    Tip: pointer-follow soak — `python3 util/soak_run_probe.py --dry-run` then run; score with `--reveal` only after. Default pick is least-covered; characterisatio
```

### #1691 docs(experiments): operator surface for recurrence wor

```text
    Tip: recurrence work is **not countable** (juniper-ml#1683). `n_epochs` is 1-or-200 by readout type; `n_windows` is input size. `read_run_metrics.py --run RUN_D
```

## 5. How to reproduce

```bash
python3 util/ad-hoc/2026-09-06_docs_pr_cluster_map.py . <pr> [<pr> ...]      # who touches what
python3 util/ad-hoc/2026-09-06_docs_merge_probe.py . <pr> [<pr> ...]         # how much merges clean
python3 util/ad-hoc/2026-09-06_docs_consolidate.py . <branch> <report> <pr>… # the run
python3 util/ad-hoc/2026-09-06_docs_residue_audit.py <report>                # this classification
```

The consolidator stops on any hunk it cannot address and names the PR to resume from; the two
that stopped this run (#1662, #1701) are the ones adjudicated in §3.
