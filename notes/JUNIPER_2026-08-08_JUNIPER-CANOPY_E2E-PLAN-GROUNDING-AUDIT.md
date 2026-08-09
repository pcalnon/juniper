# Juniper Canopy — E2E Plan & Matrix Grounding Audit

**Project**: Juniper — juniper-canopy end-to-end front-end validation arc
**Document Type**: Grounding / anti-hallucination audit (findings report)
**Status**: **COMPLETE**
**Date**: 2026-08-08
**Auditor**: independent grounding auditor (Claude Code, read-only; no document under audit was modified)

**Documents audited**

1. `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` (703 lines) — "the PLAN"
2. `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` (1015 lines) — "the MATRIX"

**Ground truth re-probed** (read-only, at the commits below)

| Repo | Path | HEAD |
|---|---|---|
| juniper-canopy | `/home/pcalnon/Development/python/Juniper/juniper-canopy` | `e8309ec` (Merge PR #477, release/juniper-canopy-v0.6.0), tree clean |
| juniper-ml (worktree) | `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/joyful-popping-castle` | `eca38af` |
| juniper-recurrence | `/home/pcalnon/Development/python/Juniper/juniper-recurrence` | — (settings only) |
| juniper-cascor | `/home/pcalnon/Development/python/Juniper/juniper-cascor` | — (one symbol cross-check) |

**Method.** Every concrete claim class was re-probed independently of the documents' own prose:

- **Mechanical line verification.** A checker (`check.py`) was fed 444 `(file, line, expected-substring)`
  triples extracted from the documents' component-id, route, handler, symbol and constant citations; it
  reports EXACT (needle on the cited line), DRIFT (nearest real occurrence within ±3), or WRONG (beyond ±3).
- **Range verification.** 224 callback/region range citations (`:NNNN-NNNN`) were dumped at their first and
  last line and eyeballed against the claim.
- **Route verification.** All `@app.<verb>` decorators in `src/main.py` were enumerated with `grep -n` and
  diffed against the MATRIX §1.6 inventory.
- **Negative verification.** The "no callback anywhere" / "not a registered route" / "no `hoverData`" /
  "appears nowhere" claims were re-grepped repo-wide, including for `include_router` / `add_api_route` /
  `app.mount` before ruling on D-0.
- **Value verification.** Interval milliseconds, HTTP status codes, colour hex, defaults, and every count
  claim (tabs, tooltips, fields, tests, writers) were read out of the source or computed.

Tolerance per the audit brief: within ±3 lines of truth = VERIFIED-DRIFT; beyond = WRONG.

---

## 1. Executive verdict

### **GO-WITH-FIXES** — documentation reliability is high; six defects to correct, one of them blocking.

These are the **best-grounded planning documents I have audited in this repository**. The MATRIX's
per-control citation layer is essentially perfect: **251/251** per-tab component-id citations landed on the
exact line, **45/45** route citations in §1.6 landed on the exact line, and **118/119** global-chrome id
citations landed exactly. Every one of the ten load-bearing claims (a)–(j) named in the audit brief is
**VERIFIED** (§5). No invented file, no invented route, no phantom callback region was found.

The defects are of two kinds: (i) **five arithmetic / stale-fact errors**, four of them in the PLAN, and
(ii) **one blocking cross-document contradiction** — the two documents use *incompatible W-numbering* for
the workflow scripts, so the PLAN's execution order (§6.2) and suite mapping (§8.4) reference workflows
that mean something different in the MATRIX. That must be fixed before execution or Phase 1 will run the
wrong scripts in the wrong order.

### Counts

Denominator = concrete claims **mechanically re-probed** by this audit (not every sentence in the
documents). Shared citations that appear in both documents are attributed to the MATRIX (which states them
with line numbers) and counted once.

| Document | Claims checked | VERIFIED | VERIFIED-DRIFT | WRONG | UNVERIFIABLE |
|---|---:|---:|---:|---:|---:|
| **MATRIX** | 713 | 706 | 5 | **2** | 0 |
| **PLAN** | 176 | 168 | 4 | **4** | 0 |
| **Cross-document** | 1 | 0 | 0 | **1** (blocking) | 0 |
| **Totals** | **890** | **874** | **9** | **7** | **0** |

MATRIX breakdown: 45 route→line (§1.6) · 370 component-id→line (§2, §3, §5.1) · 71 handler/symbol/URL→line ·
210 callback-region ranges · 17 in-depth behavioural/value claims.
PLAN breakdown: ~120 `file:line` claims (§2–§5, §7, §8, §11, §15) · ~30 cross-repo claims (isolated-stack,
checklist, recurrence, Skills, live conda env) · ~26 behavioural/value/count claims.

Zero UNVERIFIABLE **claims**; three forward-looking *design assumptions* that cannot be statically resolved
are listed in §4 so they are not mistaken for verified facts.

---

## 2. WRONG findings, ordered by severity

### F-1 — BLOCKING-DECISION: the two documents number the workflows incompatibly

- **Documents / sections**: PLAN §3.3, §6.2, §8.4, §13 A-3 ⇄ MATRIX §4, §6.1, §6.4
- **Claim**: the PLAN treats `W-1 … W-12` as the shared workflow identifiers and tells the executor
  "Per-control detail lives in the **companion matrix document**" (PLAN:135), then prescribes the Phase-1
  execution order "W-1 → W-2 → W-3/W-4 → W-5 → **W-10** → **W-8/W-9** → W-6 → W-7 → W-11 → W-12"
  (PLAN:301) and the suite mapping "W-3/W-4 control loop, W-5 params, W-6 cold migration, W-7 hot
  migration, **W-8/W-9 snapshots+replay**, **W-11 model swap**" (PLAN:537).
- **Truth**: the MATRIX defines a **different, 13-entry** numbering. Only W6 and W7 coincide.

  | # | PLAN §3.3 (`W-n`) | MATRIX §4 (`Wn`) | Same? |
  |---|---|---|---|
  | 1 | First visit → welcome modal | Cold-start cascor training, end to end | ✗ |
  | 2 | Tab tour (all 15) | Pause/Resume/Stop/Reset control matrix | ✗ |
  | 3 | Start → Pause → Resume → Stop | Parameter apply round-trip | ✗ |
  | 4 | Reset → Start | Topology exploration | ✗ |
  | 5 | Parameter apply round-trip | Snapshot lifecycle | ✗ |
  | 6 | Cold dataset migration | Dataset COLD migration | **✓** |
  | 7 | Hot dataset migration | Dataset HOT migration | **✓** |
  | 8 | Snapshot create → restore → editor unlock | Model switch cascor ⇄ recurrence | ✗ |
  | 9 | Snapshot replay | DEMO-lane dataset generate/upload/URL | ✗ |
  | 10 | Topology render + interactions | Metrics layout save/load/delete | ✗ |
  | 11 | Model swap cascor ↔ recurrence | In-metrics replay controls | ✗ |
  | 12 | Dataset View import | Evolution + Boundaries during a live run | ✗ |
  | 13 | *(does not exist)* | Ancillary tabs + chrome smoke | ✗ |

- **Evidence**:
  - PLAN:128-135 (the `W-1 … W-12` roster, ending "Per-control detail lives in the **companion matrix document**").
  - PLAN:301 (`Order: W-1 → W-2 → W-3/W-4 → W-5 → W-10 → W-8/W-9 → W-6 → W-7 → W-11 → W-12`).
  - PLAN:537 (§8.4 Workflows row), PLAN:646 (A-3 "W-1 … W-12 each end `PASS`").
  - MATRIX:629 (`### W1 — Cold-start cascor training, end to end`), :654 (W2), :669 (W3), :687 (W4),
    :709 (W5), :745 (W6), :770 (W7), :792 (W8), :812 (W9), :831 (W10), :845 (W11), :861 (W12), :876 (W13).
  - MATRIX:999-1000 (§6.4 lane table enumerating `W1 … W13`).
- **Consequence**: an executor reading PLAN §6.2 and opening the MATRIX would, at "W-10", run *Metrics
  layout save/load/delete* instead of *Topology render + interactions*; at "W-8/W-9" it would run *Model
  switch* + *DEMO dataset* instead of *snapshots + replay*. The Phase-1 evidence protocol, the
  acceptance criterion A-3, and the Phase-3 suite mapping all inherit the error.
- **Recommended fix**: adopt the MATRIX numbering (`W1 … W13`) as canonical — it is the executable
  artifact — and rewrite PLAN §3.3, §6.2, §8.4 and §13 A-3 against it. See §7 C-1.
- **Severity**: **BLOCKING-DECISION**

---

### F-2 — ROW-LEVEL: PLAN T-19 asserts "exactly two `active_tab` writers"; there are three

- **Document / section**: PLAN §5, trap **T-19** (PLAN:266)
- **Claim**: "A model swap does **not** reset `active_tab`; `_visible_tabs` deliberately keeps exactly two
  `active_tab` writers. | `dashboard_manager.py:2254-2268`"
- **Truth**: the first half is correct; the "exactly two" half is **a stale docstring quoted as fact**.
  There are **three** writers of `visualization-tabs.active_tab`.
- **Evidence** (repo-wide grep for the property):

  ```
  $ grep -rn 'visualization-tabs' src/ --include="*.py" | grep -v /tests/
  src/frontend/components/hdf5_snapshots_panel.py:1230:  Output("visualization-tabs", "active_tab", allow_duplicate=True),
  src/frontend/dashboard_manager.py:3278:                    Output("visualization-tabs", "active_tab", allow_duplicate=True),
  src/frontend/dashboard_manager.py:3300:                    Output("visualization-tabs", "active_tab", allow_duplicate=True),
  ```

  The "exactly two" text lives only in the docstring at `src/frontend/dashboard_manager.py:2259-2261`:
  `"...the dashboard keeps exactly / two ``visualization-tabs.active_tab`` writers (Store-restore + tutorial trigger) to / avoid a mount-time restore race..."`.
- **Note**: the MATRIX gets this **right** and files it as `DIVERGENCE D-1` (MATRIX:147, :917, :928). The
  PLAN repeats the stale docstring without the correction, so the two documents disagree (also listed in §6).
- **Recommended fix**: rewrite T-19 to state three writers and cite the three lines; keep the
  orphaned-active-tab probe rationale unchanged.
- **Severity**: **ROW-LEVEL**

---

### F-3 — ROW-LEVEL: PLAN §8.1 says all 21 UI tests carry `@pytest.mark.ui`; one does not

- **Document / section**: PLAN §8.1 (PLAN:494-495)
- **Claim**: "The current suite is 11 files / 21 test functions under `src/tests/ui/`, all `@pytest.mark.ui`"
- **Truth**: **11 files ✓** and **21 test functions ✓** — both exact — but only **20** carry
  `@pytest.mark.ui`. `src/tests/ui/test_sidebar_width.py:52` `test_every_known_tab_has_a_label_mapping`
  is marked `@pytest.mark.regression`.
- **Evidence**:

  ```
  $ grep -n "^def test_\|@pytest.mark" src/tests/ui/test_sidebar_width.py
  51:@pytest.mark.regression
  52:def test_every_known_tab_has_a_label_mapping() -> None:
  60:@pytest.mark.ui
  61:@pytest.mark.parametrize("tab", _ALL_TABS)
  62:def test_sidebar_width_matches_ui_standards(dashboard_page, tab: str) -> None:
  ```

  Per-file `@pytest.mark.ui` counts sum to 20 against 21 test functions.
- **Consequence for this arc**: that test is currently reachable **only** through `make test-ui`
  (`Makefile:23-24`, no `-m` filter). CI's ui-tests job filters `-m "ui and not slow"`
  (`.github/workflows/ci.yml:402`) so it never runs there, and `--ignore=src/tests/ui`
  (`pyproject.toml:352`) keeps it out of the default run. PLAN §8.2 item 3 proposes changing CI's selector
  to `-m "ui and not slow and not ui_live"`, which **preserves** the hole rather than closing it.
- **Recommended fix**: correct the sentence to "21 test functions, 20 of them `@pytest.mark.ui`", and add
  a one-line Phase-3 item to either mark `test_every_known_tab_has_a_label_mapping` `ui` or move it out of
  `src/tests/ui/`.
- **Severity**: **ROW-LEVEL**

---

### F-4 — ROW-LEVEL: MATRIX §2.9 says Apply POSTs "all 27 fields"; the dashboard sends 28

- **Document / section**: MATRIX §2.9, `apply-params-button` row (MATRIX:275)
- **Claim**: "Blur-commit (`:2985-3005`) → clamp to `CascorPatchBounds` → `POST /api/set_params` with all
  27 fields"
- **Truth**: the Apply callback carries **28** `State`s. `src/frontend/dashboard_manager.py:4508-4540`:
  13 NN inputs (`:4508-4520`) + **11** CN inputs (`:4522-4532` — the inline comment says "Candidate Nodes
  (10)" but there are 11 lines) + `nn-output-epochs-input` (`:4534`) + `nn-optimizer-type-dropdown`
  (`:4536`) + `nn-activation-function-dropdown` (`:4538`) + `nn-init-output-weights-dropdown` (`:4540`).
- **Corroborating in-repo evidence**: `src/tests/ui/test_param_roundtrip_visible.py:34-36` —
  `"# Build a payload that satisfies SetParamsRequest's required-field / # contract — the dashboard sends
  all 28 fields on Apply, so we / # mirror that shape rather than rely on an \"all-optional\" surface."`
- **Not wrong elsewhere**: MATRIX W3 step 3 (MATRIX:675) says "the full 27-field body … pinned by
  `test_param_roundtrip_visible.py:37-65`". That is **correct in its own context** — the *test* payload is
  exactly 27 keys (`:38-64`), because it omits `nn_init_output_weights`. Only the §2.9 row, which
  describes what the *dashboard* sends, is wrong.
- **Recommended fix**: §2.9 → "with all 28 fields"; optionally add "(the shipped test payload mirrors 27 of
  them — it omits `nn_init_output_weights`)".
- **Severity**: **ROW-LEVEL**

---

### F-5 — COSMETIC: PLAN §8.4 says §7 names "twelve" tests; it names eighteen

- **Document / section**: PLAN §8.4, Fragile-area regressions row (PLAN:538)
- **Claim**: "`live/test_fragile_*.py` | the twelve tests named in §7 | live"
- **Truth**: PLAN §7 names **18** `ui_live` tests: §7.1 → 2 (PLAN:363-364), §7.2 → 4 (PLAN:385-386),
  §7.3 → 3 (PLAN:409-410), §7.4 → 4 (PLAN:439-441, excluding the demo-lane `test_replay_ops_501_in_demo`),
  §7.5 → 5 (PLAN:484-486). 2+4+3+4+5 = 18. (Two further *conditional* non-browser unit pins are named at
  PLAN:364-366 and PLAN:411 and are not `ui_live`.)
- **Note**: acceptance criterion A-4 (PLAN:647) says "≥12 new `ui_live` tests", which 18 satisfies — so the
  arithmetic error is confined to §8.4 and does not weaken the acceptance bar.
- **Recommended fix**: §8.4 → "the eighteen tests named in §7"; optionally raise A-4's floor to ≥18.
- **Severity**: **COSMETIC**

---

### F-6 — COSMETIC: MATRIX §2.9 claims 24 tooltips; there are 23

- **Document / section**: MATRIX §2.9, tooltips row (MATRIX:287)
- **Claim**: "24 `dbc.Tooltip`s built at `:1819` from `CONTROL_TOOLTIPS` (`…/tooltips.py:7-34`) — 23
  parameter inputs + `apply-params-button`."
- **Truth**: `CONTROL_TOOLTIPS` has **23** entries = **22** parameter inputs + `apply-params-button`, and
  they are rendered 1:1.
- **Evidence**:

  ```
  $ python3 -c "... exec_module(tooltips) ..."
  CONTROL_TOOLTIPS len = 23
  param inputs = 22
  ```

  `src/frontend/dashboard_manager.py:1819`:
  `*[dbc.Tooltip(text, target=target_id, placement="top") for target_id, text in CONTROL_TOOLTIPS.items()],`
  — one Tooltip per key, no additions. The cited range `tooltips.py:7-34` is **exact** (dict opens :7,
  closes :34).
- **Recommended fix**: "23 `dbc.Tooltip`s … — 22 parameter inputs + `apply-params-button`".
- **Severity**: **COSMETIC**

---

### F-7 — COSMETIC: PLAN §7.3 names a symbol that does not exist (`_status_bar_display_fields`)

- **Document / section**: PLAN §7.3, Planned regression tests (PLAN:411)
- **Claim**: "plus a pure-unit pin on `_status_bar_display_fields` mapping if Phase 2 touches it."
- **Truth**: `_status_bar_display_fields` **appears nowhere** in the canopy repository.

  ```
  $ grep -rn "_status_bar_display_fields" src/ --include="*.py" | head -3
  EXIT=0        # zero matches
  ```

  The real status-bar symbols are `_counter_displays` (`dashboard_manager.py:5996`),
  `_classify_response_failure` (`:5872`), `_status_bar_error_tuple` (`:5915`) and
  `_build_unified_status_bar_content` (called at `:5962`).
- **Mitigating**: the sentence is forward-looking ("if Phase 2 touches it"), and MATRIX §2.3 cites the
  correct `_counter_displays` (`:5996-6070`). Still, it names a non-existent identifier as if it existed.
- **Recommended fix**: replace with `_counter_displays`.
- **Severity**: **COSMETIC**

---

### Minor symbol-naming nits (below the WRONG bar; listed for completeness, no correction required)

| # | Location | Stated | Actual |
|---|---|---|---|
| n-1 | MATRIX §2.7 (:244) | callback `gated_dataset_options` | function is `gate_dataset_options` (`dashboard_manager.py:2432`); handler `_gate_dataset_options_handler`. The cited range `:2424-2433` is exact. |
| n-2 | MATRIX §3.2 (:349) | "tab-gated `_fetch_training_state` (`:233-247`)" | `_fetch_training_state` is at `candidate_metrics_panel.py:409`; `:233-247` is the callback *registration* (inner function `fetch_training_state` at `:243`, `active_tab` Input at `:239`, call at `:246`). Region is right, symbol line is elsewhere. |

---

## 3. VERIFIED-DRIFT list

All nine are within the ±3 tolerance and none changes a claim's substance.

| # | Doc / § | Claim | Cited | Actual | Δ |
|---|---|---|---|---|---|
| D-a | MATRIX §2.2 (:146) | `layout-state-store` … `storage_type="local"`, `:1724` | `:1724` | `dcc.Store(` opens `:1724`; `id="layout-state-store"` `:1725`; `storage_type="local"` `:1726` | +1 |
| D-b | MATRIX §2.9 (:277) | "while set, `fast`/`slow` update intervals are disabled (`:3224`)" | `:3224` | the two `Output(... "disabled")` lines are `:3221`/`:3222`; `:3224` is the callback's `Input("apply-in-flight","data")` — same clientside callback (`:3213-3226`) | −2/−3 |
| D-c | MATRIX §3.1 (:339) | `SCALAR_SERIES`, `:93-98` | `:93` | `SCALAR_SERIES` declared `metrics_panel.py:92`; the four F1/Precision/Recall/ROC-AUC entries are `:93-96`, close `:97` | −1 |
| D-d | MATRIX §3.7 (:481) | `_render_workers_table` `:257` | `:257` | `@staticmethod` `:257`, `def _render_workers_table` `:258` | +1 |
| D-e | MATRIX §3.2 (:349) | `_fetch_training_state` (`:233-247`) | `:233` | see n-2 above | — |
| D-f | PLAN §7.4 (:431) | Network Editor "gate `:401`" | `:401` | `def _is_investigating` `network_editor_panel.py:400`; `:401` is its docstring line | −1 |
| D-g | PLAN §2.2 / T-13 | sidebar visibility `dashboard_manager.py:2286-2308` | `:2286` | `:2286` = `def _setup_sidebar_visibility_callback`; the `@self.app.callback` is `:2289` (MATRIX cites `:2289-2308`). Both correct at different layers. | +3 |
| D-h | MATRIX §2.2 (:150) | `TAB_SIDEBAR_WIDTH` table `ui_standards.py:39-58` | `:39-58` | declared `:37`; 15 entries `:39-55`; closes `:56` | −2/+2 |
| D-i | MATRIX §2.4 (:171) | badge "registered at `dashboard_manager.py:3533-3537`" | `:3533` | `self.app.clientside_callback(` `:3532`; JS arg `:3533`; two Inputs `:3536`/`:3537`; close `:3538` (PLAN cites `:3532-3538`) | −1 |

---

## 4. Could-not-verify

**Zero UNVERIFIABLE claims.** Every concrete factual assertion re-probed in this audit resolved to
VERIFIED, VERIFIED-DRIFT, or WRONG. The following are **forward-looking design assumptions**, not claims of
present fact; they are listed so they are not later mistaken for verified findings.

| # | Item | Why it cannot be settled statically | Suggested disposition |
|---|---|---|---|
| U-1 | PLAN §4.2's runtime consequence chain — that canopy actually binds 8050, fails the 8051 health gate, and `do_up` tears the trio down | Every *code* link is verified (§5a), but the stack was **not** brought up during this audit; runtime confirmation requires `util/isolated_stack.bash --up` | Confirm in Phase-0 step 4's bring-up rehearsal; do not treat as executed |
| U-2 | PLAN §4.5 **fallback** option: point `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` at canopy's own port "so the routing predicate is satisfied without a real fit" | The predicate half **is** verified — `_selection_targets_recurrence` only tests `bool(settings.recurrence_service_url)` (`main.py:3510`), so any non-empty URL satisfies it. Whether the resulting `RecurrenceServiceAdapter` pointed at canopy yields *usable* UI behaviour (rather than 404 storms) is runtime-only | Rehearse before adopting the fallback, or prefer the `--with-recurrence` default |
| U-3 | The DEAD-EXPECTED contract's runtime half — "clicking MUST do nothing: no network request, no DOM change, **no console error**" | The static half is fully verified (no callback exists for any of the four pattern ids; no `hoverData` Input anywhere) — see §5e/§5f. The console-error half is observable only in a live browser | Keep as a Phase-1 observation, which is what MATRIX §7 already specifies |
| U-4 | PLAN §4.5's choice of host port **8211** for the optional recurrence leg | Not a factual error, but note the in-code comment `juniper-recurrence/juniper_recurrence/settings.py:152`: `port: int = 8210  # container port; deploy maps host 8211 -> ctr 8210`. 8211 is precisely the port a running juniper-deploy stack publishes, so an on-host `--with-recurrence` leg on 8211 can collide with a live compose stack | Add a pre-`--up` 8211 occupancy check to PR-M2, mirroring PLAN §12's 8050/8051 mitigation |

---

## 5. Load-bearing-claim verdicts

### (a) `isolated_stack.bash:252` exports `JUNIPER_CANOPY_PORT`, which canopy never reads → canopy binds 8050 — **VERIFIED (every link)**

| Link | Evidence | Verdict |
|---|---|---|
| Export exists at the cited line | `util/isolated_stack.bash:252`: `JUNIPER_CANOPY_PORT="${CANOPY_PORT}" \` | EXACT |
| Canopy never reads it | `grep -rn "JUNIPER_CANOPY_PORT" .` over the whole canopy repo → **zero matches** | EXACT |
| It is silently dropped | `src/settings.py:189` `env_prefix="JUNIPER_CANOPY_"`, `:193` `extra="ignore"`, `:194` `env_nested_delimiter="__"` (PLAN cites `:188-195`) | EXACT |
| The real field is nested, default 8050 | `src/settings.py:118` `class ServerSettings`, `:122` `port: int = 8050`, `:198` `server: ServerSettings = ServerSettings()` (PLAN cites `:118-122`) | EXACT |
| Entry point reads `settings.server.port` | `src/main.py:4247` `host = settings.server.host`, `:4248` `port = settings.server.port`, `:4258` `uvicorn.run(app, host=host, port=port, ...)` | EXACT |
| `_api_base_url` derives from the same field | `src/frontend/dashboard_manager.py:440` **and** `:443`, both `self._api_base_url = f"http://127.0.0.1:{self._settings.server.port}"` | EXACT (both lines) |
| Health gate is on `CANOPY_PORT` | `util/isolated_stack.bash:259` `wait_for_health "juniper-canopy" "http://127.0.0.1:${CANOPY_PORT}/v1/health" \|\| return 1` | EXACT |
| Failure tears the trio down | `util/isolated_stack.bash:294` `canopy_up \|\| failed=1`; `:296-302` teardown branch | EXACT |
| The checklist repeats the bug | `notes/JUNIPER_2026-07-21_…ISOLATED-STACK-E2E-CHECKLIST.md:106`: `JUNIPER_CANOPY_PORT=8051 \` | EXACT |
| The tests pin the bug | `tests/test_isolated_stack_script.py:348` (comment) / `:349` `assertIn("JUNIPER_CANOPY_PORT=9051", out)`; `:609` `assertIn("JUNIPER_CANOPY_PORT=65051", env_text)` | EXACT |

**Strengthening evidence neither document cites** — canopy's **own** UI conftest already uses the nested
form, which independently proves the PLAN's Phase-0 fix is the right one:

```
src/tests/ui/conftest.py:40:        "JUNIPER_CANOPY_SERVER__HOST": "127.0.0.1",
src/tests/ui/conftest.py:41:        "JUNIPER_CANOPY_SERVER__PORT": str(port),
```

**Gap in PR-M1's stated scope**: PR-M1 (PLAN:278-282) names `tests/test_isolated_stack_script.py:348-349`
and `:609`. There is a **third** occurrence at `tests/test_isolated_stack_script.py:425` —
`printf 'JUNIPER_CANOPY_PORT=%s\n' "${{JUNIPER_CANOPY_PORT-}}"` inside the launch-stub heredoc — which must
change in the same PR or `:609` will assert against a variable the stub no longer prints. See §7 C-8.

### (b) `GET /api/network/topology` is not a registered route while `network_editor_panel.py:517` fetches it — **VERIFIED**

- Full route enumeration of `src/main.py` (`grep -n '^@app\.\(get\|post\|put\|delete\|patch\|websocket\)'`)
  yields **70 routes**; `/api/network/topology` is **not** among them. The near neighbours are
  `/api/network/stats` `:1322`, `/api/topology` `:1373`, `/api/topology/raw` `:1388` — exactly as the
  MATRIX states.
- **Ruled out before concluding** (as the brief requires): there is **no** `include_router`, no
  `add_api_route`, no `APIRouter` anywhere in `src/` outside tests. The only two mounts are
  `src/main.py:468` `app.mount("/metrics", MetricsAuthMiddleware(...))` and `:495`
  `app.mount("/dashboard", WSGIMiddleware(dashboard_manager.app.server))` — neither can serve
  `/api/network/topology`.
- The fetch is exact: `src/frontend/components/network_editor_panel.py:517`
  `f"{self._api_base_url}/api/network/topology",` inside a bare `except: topology = None` (`:523-524`).
- The consequence is exact: `:538-540` `def render_topology(topology): if not topology: return
  html.Em("No topology loaded.", …), []`.
- The repo's own test admits the 404: `src/tests/unit/test_main_import_and_lifespan.py:304-305`
  `response = app_client.get("/api/network/topology")` / `assert response.status_code in (200, 404, 500)`.
- The MATRIX's "stale comment" sub-claim is also exact: `dashboard_manager.py:3714`
  `# PERF-CN-01: prevent_initial_call=False — must hit /api/network/topology`, while the handler it
  guards actually calls `/api/topology` at `dashboard_manager.py:6439`.

### (c) Silent demo-fallback at `main.py:322-337` and the `/v1/health` payload fields — **VERIFIED**

- `src/main.py:322` `# Probe JuniperCascor at startup (service mode only) — fallback to demo on failure.`
  → `:330` `system_logger.warning("JuniperCascor unreachable at %s — falling back to demo mode", cascor_url)`
  → `:331` `await backend.shutdown()` → `:334` `backend = create_backend(demo_mode=True)` → `:336`
  `backend_initialized = True`. The PLAN's `:322-337` covers the block exactly (`:337` is blank).
- `@app.get("/v1/health")` `:1047`; return dict `:1059-1075`; `"status": "ok"` `:1061`;
  **`"demo_mode": backend.backend_type == "demo"` `:1068`**; **`"juniper_data_available": juniper_data_available` `:1069`**;
  `"git_sha": provenance_git_sha()` `:1073`; `"build_date": provenance_build_date()` `:1074`.
  Every line cited by PLAN §4.3 / §8.5 and MATRIX §0 is exact.
- The PLAN's honest-gate design is therefore correct: HTTP 200 + `status == "ok"` survives the fallback;
  only `demo_mode == false` distinguishes it.

### (d) Recurrence `status="live"`, `model_is_trainable` keyed off status only, silent no-op swap — **VERIFIED (all four sub-claims)**

- `src/model_registry.py:188` `status="live",  # A1-iv-5: flipped coming_soon → live …` (recurrence);
  `:175` `status="live"` (cascor). MATRIX §2.5's `model_registry.py:175,188` is exact.
- `src/model_registry.py:232` `def model_is_trainable(...)`; `:246` `return spec.status == "live"`;
  `:247` unknown key → `return True`. PLAN's `:232-247` is exact. **No consultation of
  `recurrence_service_url` anywhere in that function.**
- Silent no-op swap: `src/main.py:3498` `def _selection_targets_recurrence(...)` → `:3510`
  `return spec is not None and spec.provider == RECURRENCE_PROVIDER and bool(settings.recurrence_service_url)`.
  With the URL unset this is `False`, and `_swap_backend`'s guard `:3544`
  `if _selection_targets_recurrence(nn_model) == (backend.backend_type == "recurrence"):` matches, so
  `:3547` `return _model_state_response(nn_model, swapped=False)` — **no error, no re-create**.
- The "silent" characterisation is confirmed at the UI layer: `_select_model_handler`
  (`dashboard_manager.py:2696-2717`) reads **only** `nn_model`, `execution` and the summary from the
  response (`:2713`) — it never inspects `swapped` or `backend` — and `_model_summary_text` (`:2751-2758`)
  renders `Active: Recurrence (LMU)` with no lifecycle note because `status == "live"`.
- Start therefore stays enabled: `dashboard_manager.py:6749-6752`
  `start_disabled, start_text = get_button_props(...)` / `# D8 Train-gate: …` /
  `if not model_is_trainable(model_key): start_disabled = True` — never taken for recurrence.
- The docstring the PLAN's D-8 flags is exact: `src/backend/__init__.py:116-118` —
  `"…The A1 selection UI / (A1-iv) gates an unconfigured recurrence model out of the picker, so the
  unset-URL path / is a safety net rather than the normal flow."` — while `:125-127` is the code that
  actually just logs and returns `None`.

**Verdict**: PLAN §4.5, T-16 and F-CANDIDATE (§7.5) are fully substantiated, including the phrase "the user
is shown a successful selection of a model that is not actually active".

### (e) The DEAD-EXPECTED controls have no callback anywhere — **VERIFIED**

| Pattern id | Definition | Repo-wide occurrences |
|---|---|---|
| `{"type": f"{self.component_id}-swap-restore-pre-btn", "index": i}` | `hdf5_snapshots_panel.py:709` | **1** (the definition) |
| `{"type": f"{self.component_id}-swap-restore-post-btn", "index": i}` | `hdf5_snapshots_panel.py:720` | **1** |
| `{"type": f"{self.component_id}-history-pool-header", "index": epoch}` | `candidate_metrics_panel.py:679` | **1** |
| `{"type": f"{self.component_id}-history-pool-collapse", "index": epoch}` | `candidate_metrics_panel.py:694` (`is_open=False` `:695`) | **1** |

```
$ grep -rn "swap-restore-pre-btn\|swap-restore-post-btn" src/ | grep -v egg-info
src/frontend/components/hdf5_snapshots_panel.py:709: ...
src/frontend/components/hdf5_snapshots_panel.py:720: ...
$ grep -rn "history-pool" src/ | grep -v egg-info
src/frontend/components/candidate_metrics_panel.py:679: ...
src/frontend/components/candidate_metrics_panel.py:694: ...
```

The ids are built by f-string from `component_id`, whose defaults are
`hdf5_snapshots_panel.py:68` `component_id: str = "hdf5-snapshots-panel"` and
`candidate_metrics_panel.py:71` `component_id: str = "candidate-metrics-panel"`, so the MATRIX's expanded
dict shapes are correct. The `cursor: pointer` styling the MATRIX flags as misleading is exact at
`candidate_metrics_panel.py:678`. All four lines are exactly as cited in PLAN T-12 and MATRIX §3.2/§3.9/§5.1.

### (f) No `hoverData` Input on `network-visualizer-graph` (or anywhere) — **VERIFIED**

```
$ grep -rn "hoverData" src/ | grep -v egg-info
                       # zero matches, repo-wide
```

The only graph event Inputs are `relayoutData` (`network_visualizer.py:294`), `clickData` (`:552`) and
`selectedData` (`:553`) — each verified at the exact cited line. PLAN §7.2's "verified by grep" and MATRIX
§3.3/§5.1 are both correct.

### (g) The `dbc.Input(type=number)` wall, the `set_params` doctrine, and `/api/set_params` outside the gated set — **VERIFIED**

- **The wall, as two strict xfails**: `src/tests/ui/test_apply_button_flow.py:62` `@pytest.mark.xfail(`,
  `:63` `strict=True,`, `:64-72` the reason ("Playwright fills DOM but Dash dbc.Input(type=number) never
  sees the React onChange — apply callback receives State value=null…"). And
  `src/tests/ui/test_l3_native_setter_poc.py:46` `@pytest.mark.xfail(`, `:47` `strict=True,`, `:48` reason
  ("…Apply pushes the default, not the set value… XPASS here = Dash fixed it."). Both exactly as cited
  (PLAN T-7 `:62-71` / `:46-48`; MATRIX §1.3 `:64` / `:48`). The PLAN's "an XPASS is a *canary*" reading is
  literally the in-code wording.
- **The doctrine**: `src/tests/ui/test_param_roundtrip_visible.py` — `:31` test def, `:37-65` the 27-key
  payload, `:66` `requests.post(f"{canopy_url}/api/set_params", json=base_payload, timeout=10)`,
  `:70-77` the `/api/state` poll, `:82-92` reload + `wait_for_function` DOM assertion. Every citation
  (PLAN §8.3 `:37-92` and T-7 `:66-92`; MATRIX §1.3 `:31-92`, W3 `:37-65` / `:70-77` / `:82-92`) is exact.
- **`/api/set_params` is outside the browser-control-auth gated set**: `src/main.py:3640`
  `@app.post("/api/set_params")` — **no `dependencies=`**. The seven gated routes are exactly
  `:3246`, `:3278`, `:3299`, `:3320`, `:3341`, `:3362`, `:3426`, each carrying
  `dependencies=[Depends(require_browser_control_auth)]` — all seven line numbers in PLAN T-9 and MATRIX
  §1.6 are exact.
- **Keyless posture**: `src/security.py:314` `async def require_browser_control_auth(request)`; `:352-354`
  `# 2. Auth globally disabled -> open access (dev/demo).` / `if not auth.enabled: return`; `enabled` is
  `len(self._api_keys) > 0` (`:53-54`, property `:56-59`), fed by `get_api_key_auth()` reading
  `get_secret("CANOPY_API_KEY")` (`:261-268`). The isolated stack sets no key
  (`util/isolated_stack.bash:251-255` contains no `CANOPY_API_KEY`), so the PLAN's "the live browser lane
  is unblocked" is correct.
- **Rate-limiter exemption (T-8)**: `src/settings.py:317` `rate_limit_enabled: bool = False`;
  `src/frontend/internal_api.py:63-79` `internal_api_headers()` whose docstring states
  "Always includes the per-process internal-request token (``INTERNAL_REQUEST_HEADER``) so canopy's own
  rate limiter exempts these self-calls (#2a)" and whose body is
  `headers = {INTERNAL_REQUEST_HEADER: INTERNAL_REQUEST_TOKEN}` (`:75`). Exact.

### (h) Three `active_tab` writers — **VERIFIED (MATRIX correct; PLAN wrong — see F-2)**

`Output("visualization-tabs", "active_tab", …)` occurs exactly three times:
`dashboard_manager.py:3278` (tutorial context-menu clientside, `:3271-3281`),
`dashboard_manager.py:3300` (layout-state restore clientside, `:3287-3304`),
`hdf5_snapshots_panel.py:1230` (snapshot `replay` op, inside `:1225-1296`, tab hand-off at `:1270-1286`).
Every line cited by MATRIX §2.2 / A-3 / D-1 is exact.

### (i) conftest demo-mode hard-pins — **VERIFIED**

- Root: `conftest.py:12` `# Set demo mode for all tests`, `:13`
  `os.environ["JUNIPER_CANOPY_DEMO_MODE"] = "1"` — PLAN's `conftest.py:12-13` exact.
- Suite: `src/tests/conftest.py:22` `# CRITICAL: Set demo mode BEFORE any imports of main.py`, `:23`
  `os.environ["JUNIPER_CANOPY_DEMO_MODE"] = "1"`, `:25`
  `os.environ["JUNIPER_DATA_URL"] = "http://localhost:8100"`, `:27`
  `os.environ["JUNIPER_CANOPY_RATE_LIMIT_ENABLED"] = "false"` — PLAN's `src/tests/conftest.py:22-27` exact,
  including the "also pins `JUNIPER_DATA_URL` and disables rate limiting" rider.
- Both are **unconditional assignments**, which is precisely what PLAN §8.2 item 1's escape hatch targets.
- Related, all exact: `pyproject.toml:339-353` addopts with `--ignore=src/tests/ui` at `:352` (T-20 cites
  `:346-352`); the `ui` marker at `pyproject.toml:368`; `Makefile:23-24` `test-ui:` /
  `$(PYTEST) src/tests/ui --override-ini=addopts=`; `Makefile:31-32` `check-env:` /
  `juniper-env-drift-check --repo-root . --check-lock`.
- `src/tests/ui/conftest.py`: `canopy_url` fixture `:33-34`, `subprocess.Popen([sys.executable, str(_SRC / "main.py")], …)` `:46-47`,
  `/v1/health/ready` gate `:60`, `yield base` `:71`; `dashboard_page` `:81-82`, localStorage pre-seed `:96`,
  `page.wait_for_function(` `:110`; file is 126 lines (PLAN's `:81-126` exact).

### (j) CI `ui-tests` job and quality gate — **VERIFIED**

- Job block `.github/workflows/ci.yml:353` `ui-tests:` … `:415` `retention-days: 30` — PLAN's `:353-415` exact.
- Budget commitment `:350-351` `#   Budget commitment: must add ≤5 min to overall CI wall-clock. Runs in`
  / `#   parallel with unit-tests …` — exact.
- Selector `:402` `-m "ui and not slow"` — exact.
- Demo pin `:395` `JUNIPER_CANOPY_DEMO_MODE: "1"` (corroborates "CI is a demo lane").
- Artifact `:409-415` — exact.
- Quality gate `:928-932`:
  `# UI tests: failure = error, skipped = OK (only runs on PRs and main/develop)` /
  `if [[ "${{ needs.ui-tests.result }}" == "failure" ]]; then` / `echo "::error::UI sub-suite (Playwright) failed"` /
  `exit 1` / `fi` — **exact**, and the PLAN's "failure = error" reading is the in-file comment verbatim.

---

## 6. Cross-document contradictions

| # | Fact | PLAN says | MATRIX says | Adjudication |
|---|---|---|---|---|
| **X-1** | Workflow numbering | `W-1 … W-12`, with W-8/W-9 = snapshots, W-10 = topology, W-11 = model swap, W-12 = dataset import (PLAN:128-135) | `W1 … W13`, with W5 = snapshots, W4 = topology, W8 = model switch, W9 = demo dataset, W10 = metrics layouts, W11 = in-metrics replay, W12 = evolution/boundaries, W13 = chrome (MATRIX:629-892) | **BLOCKING** — see F-1. Only W6/W7 coincide. Adopt the MATRIX numbering. |
| **X-2** | `active_tab` writer count | "exactly two" stated as fact (T-19, PLAN:266) | "three … the docstring still claims 'exactly two' — **DIVERGENCE D-1**, doc-only" (MATRIX:147, :917, :928) | **MATRIX correct.** Three writers verified (§5h). See F-2. |
| **X-3** | Field count on Apply | not stated | "all 27 fields" (§2.9, MATRIX:275) vs "the full 27-field body … pinned by `test_param_roundtrip_visible.py:37-65`" (W3, MATRIX:675) | Internal to the MATRIX: 28 States on the dashboard vs 27 keys in the test payload. See F-4. |
| **X-4** | Fragile-area test count | "twelve tests named in §7" (§8.4) vs "≥12 new `ui_live` tests" (A-4) vs the 18 actually named in §7 | not stated | Internal to the PLAN. See F-5. |

**Benign variances (not contradictions, no action needed).** Both documents are correct at different
granularities in these cases, and an executor is not misled:

- Sidebar-visibility callback: PLAN `:2286-2308` (the method `_setup_sidebar_visibility_callback`) vs
  MATRIX `:2289-2308` (the `@self.app.callback` inside it).
- WS-badge registration: PLAN `:3532-3538` (whole `clientside_callback(...)`) vs MATRIX `:3533-3537`
  (the JS arg through the two Inputs).
- Status bar: PLAN cites the handler `_update_unified_status_bar_handler` (`:5939-5969`); MATRIX cites the
  callback `update_unified_status_bar` (`:3087-3104`) plus `_counter_displays` (`:5996-6070`). Different
  layers of the same path; all three are exact.
- `/api/dataset/import-url` demo gate: PLAN T-11 `:1572` (the message string) vs MATRIX `:1570-1574`
  (the whole guard). Both land inside the same `if`.
- Topology handler: PLAN §7.1 `:6427-6464` (whole handler) vs MATRIX §3.3 `:6427-6436` (the tab gate).

---

## 7. Recommended corrections (mechanically applicable)

Ordered by severity. Nothing here was applied by this audit.

| ID | File | Location | Change |
|---|---|---|---|
| **C-1** | PLAN | §3.3 (:128-135), §6.2 (:301), §8.4 (:537), §13 A-3 (:646) | **Blocking.** Renumber every `W-n` reference to the MATRIX's `W1 … W13`. Suggested mapping: PLAN W-1/W-2 → fold into MATRIX **W13** (chrome smoke: welcome modal, 15-tab walk); W-3/W-4 → **W1**+**W2**; W-5 → **W3**; W-6 → **W6**; W-7 → **W7**; W-8/W-9 → **W5**; W-10 → **W4**; W-11 → **W8**; W-12 → **W9**. Then restate §6.2's order as, e.g., `W13 → W1 → W2 → W3 → W4 → W5 → W6 → W7 → W8 → W9 → W10 → W11 → W12`, and A-3 as "W1 … W13". Add a one-line note in §3.3: "Workflow ids are the companion matrix's; this list is a summary, not a second numbering." |
| **C-2** | PLAN | §5, T-19 (:266) | Replace "…`_visible_tabs` deliberately keeps exactly two `active_tab` writers" with "…there are **three** `active_tab` writers (`dashboard_manager.py:3278` tutorial trigger, `:3300` layout-state restore, `hdf5_snapshots_panel.py:1230` snapshot replay); the 'exactly two' text at `dashboard_manager.py:2259-2261` is a stale docstring — matrix DIVERGENCE D-1." |
| **C-3** | PLAN | §8.1 (:494-495) | Replace "21 test functions under `src/tests/ui/`, all `@pytest.mark.ui`" with "21 test functions under `src/tests/ui/`, **20** of them `@pytest.mark.ui` (`test_sidebar_width.py:52` `test_every_known_tab_has_a_label_mapping` is `@pytest.mark.regression`, so it runs only under `make test-ui` — neither CI's `-m "ui and not slow"` nor the default run reaches it)." |
| **C-4** | MATRIX | §2.9, `apply-params-button` row (:275) | "with all 27 fields" → "with all **28** fields (`dashboard_manager.py:4508-4540`)". |
| **C-5** | PLAN | §8.4, Fragile-area row (:538) | "the twelve tests named in §7" → "the **eighteen** tests named in §7". Optionally raise A-4 (:647) from "≥12" to "≥18". |
| **C-6** | MATRIX | §2.9, tooltips row (:287) | "24 `dbc.Tooltip`s … — 23 parameter inputs + `apply-params-button`" → "**23** `dbc.Tooltip`s … — **22** parameter inputs + `apply-params-button`". |
| **C-7** | PLAN | §7.3, Planned regression tests (:411) | "`_status_bar_display_fields`" → "`_counter_displays` (`dashboard_manager.py:5996-6070`)". |
| **C-8** | PLAN | §6.1 step 1 (:278-282) and §10 PR-M1 row (:581) | Add the third occurrence to PR-M1's scope: `tests/test_isolated_stack_script.py:425` (`printf 'JUNIPER_CANOPY_PORT=%s\n' "${{JUNIPER_CANOPY_PORT-}}"` in the launch-stub heredoc) must move to the nested name in the same PR, or the `:609` assertion asserts against a variable the stub no longer prints. |
| **C-9** | PLAN | §4.2 / §4.3 (optional, strengthening) | Cite `src/tests/ui/conftest.py:40-41` (`JUNIPER_CANOPY_SERVER__HOST` / `JUNIPER_CANOPY_SERVER__PORT`) as in-repo precedent that the nested form is correct — it makes the Phase-0 fix uncontestable. |
| **C-10** | PLAN | §4.5 default option (:231-235) | Add an 8211 occupancy pre-check to PR-M2's scope. `juniper-recurrence/juniper_recurrence/settings.py:152` documents 8211 as the **deploy host-mapped** port, so a running compose stack can already hold it. |
| **C-11** | MATRIX | §2.7 (:244) | "`gated_dataset_options`" → "`gate_dataset_options`" (cosmetic; the cited range `:2424-2433` is already exact). |
| **C-12** | MATRIX | §3.2 (:349) | Optionally split the citation: registration `:233-247`, handler `_fetch_training_state` `:409`. |
| **C-13** | Both | drift table §3 | Optional ±1–3 line nudges: MATRIX `:1724`→`:1725`, `:3224`→`:3221-3222`, `:93-98`→`:92-97`, `:257`→`:258`, `:3533-3537`→`:3532-3538`, `:39-58`→`:37-56`; PLAN `:401`→`:400`. None changes a claim's substance; safe to leave. |

---

## Appendix A — What was verified clean (headline pass rates)

| Claim class | Checked | Exact | Notes |
|---|---:|---:|---|
| MATRIX §1.6 route → `main.py` line | 45 | **45** | Diffed against the full `@app.<verb>` enumeration; zero drift, zero invented route |
| MATRIX §3 per-tab component-id → line | 251 | **251** | 15 panels; `component_id` prefixes independently confirmed for all 15 |
| MATRIX §2 + §5.1 chrome component-id → line | 119 | 118 | 1 drift (+1) |
| Handler / helper / URL symbol → line | 74 | 71 | 3 drift; 0 invented symbols in the MATRIX |
| Callback-region ranges (both docs) | 224 | 224 land on real callback/def/comment boundaries | 0 phantom regions |
| Tab roster: 15 tabs, ids, order, per-tab def lines | 15×2 | **all** | `_all_visualization_tabs` `:2164`, entries `:2176-2252`; every `:2177-2181` … `:2247-2251` exact |
| `_CASCADE_ONLY_TAB_IDS` = 5 ids at `:387` | 1 | exact | `{"candidates","topology","evolution","boundaries","workers"}` |
| `TAB_SIDEBAR_CONFIG` = 12 keys (no evolution/replay/network-editor) | 1 | exact | Computed: 12 keys at `:285,301,317,333,349,366,367,368,369,370,371,372` |
| `SIDEBAR_SECTION_IDS` = 14 ids `:267-282` | 1 | exact | |
| `TAB_SIDEBAR_WIDTH` lists all 15; wide=3/narrow=2/grid=12 | 4 | exact | `ui_standards.py:27,31,32,37-56`; `notes/UI_STANDARDS.md:27-31` enumerates all 15 |
| Interval values (1000/500/2000/5000/10000 ms) | 6 | **all** | incl. D-3's `base_interval = 1000` at `metrics_panel.py:1034` |
| WS-badge 7 states, texts, hex colours | 7 | **all** | `connection_indicator.py:36,80-83,86-89,91-92,94-98,99-100` |
| Doc-drift rows D-1…D-8 + T-14/T-15 | 12 | **all** | incl. the *negative* T-15 checks (USER_MANUAL has no "C++"/"JuniperPython"/Redis-Cassandra-"Planned") |
| File sizes quoted in PLAN §3.2 | 4 | **all** | metrics 2288 / visualizer 1770 / plotter 1355 / snapshots 1410 |
| Live-environment claim (§4.3) | 1 | exact | `/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/juniper_cascor_client-0.7.0.dist-info` present; floor `pyproject.toml:162` |
| juniper-ml Skills frontmatter (§6.2) | 6 | **all** | `service-smoke` and `ui-test-author` both `model: opus`, `effort: max`, `mcp__playwright`, teardown |
| isolated-stack + checklist claims | 12 | **all** | ports `:60-62`, conda `:66-67`, origin `:77`, cascor allowlist `:229`, checklist `:106` / `§4:121-133` / `§6` |
| juniper-recurrence settings (§4.2/§15) | 2 | exact | `:128` flat `env_prefix="JUNIPER_RECURRENCE_"`; `:152` `port: int = 8210` |

**Zero fabricated artifacts.** Every file path, route, component id, callback, marker, workflow job,
document and environment named across both documents exists. The only non-existent identifier found in
either document is `_status_bar_display_fields` (F-7), which appears once, in a forward-looking sentence.

---

*End of audit. Status: COMPLETE. No audited document was modified; this report is the sole artifact written.*
