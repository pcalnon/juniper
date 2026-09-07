# Lane A1 — Measurement re-creation, entry point: the design document's own claims

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) §2 Lane A
- **Target document**: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) (written 2026-09-02)
- **Scope verified**: §2, §4.1–§4.12, §5 (the "status before" column + the "Enabling change" paragraph), §12.1–§12.3
- **Code under test**: `juniper-canopy` @ `main` `fc62175` (verified `git rev-parse HEAD`); `juniper-cascor` @ `995be91`; `juniper-data` @ `005a82b`
- **Date**: 2026-09-05
- **Entry point**: the design's prose. Every falsifiable sentence was traced to a declaration
  (a signature, a decorator's Input/Output/State list, a `Literal`, a registry dict, a config
  block) and, where a handler could be run, executed.
- **Constraints honoured**: read-only on all three repos; no service started, stopped or
  contacted; **zero network calls** (every probe stubs `requests` / `_fetch_generators`);
  no branch, commit or PR. The operator stack on 8050 was not touched.

**Line-number drift baseline.** Because drift detection is a stated purpose of this pass, every
citation was checked against **two** trees: HEAD, and the file as it stood at the design's date
(`dashboard_manager.py` @ `9fbf4b8`, 2026-09-02; `main.py` @ `27af847`, 2026-08-28). That
distinguishes *the design was right and X7 moved it* from *the design was already wrong*.
Both classes occur.

---

## 1. Verdict table

| id | design's claim | verdict | current evidence (file:line) |
|----|----------------|---------|------------------------------|
| **§2** | | | |
| 2.1 | shipped code enforces `I-safe` (no reachable committed pair with `compatible()` False) | CONFIRMED | BFS over shipped handlers: 0 invalid committed states (probe `p6_bfs.py`) |
| 2.2 | `I-cover` not established: the target pair is unreachable | CONFIRMED | BFS: Reach = 5, missing `('recurrence','equities_seq')` |
| 2.3 | `I-cover` is conditioned on availability; in the container the LMU has zero available datasets | CONFIRMED | BFS container scenario: compatible∩available = 5, all cascor; `yfinance` absent from `juniper-data/requirements.lock` |
| 2.4 | family F2 "created five reachable-but-invalid states while still failing to reach the target pair" | CONFIRMED (conditional — condition omitted) | reproduced exactly, but **only** with `equities_seq` unavailable: 10 reachable / **5** invalid / target unreached. With all available the same F2 gives 6 / **0** / reached. Detail: this report's §5.6 |
| 2.5 | `⊥` is a universal cut vertex joining every component | CONFIRMED | BFS with `clearable=True` as the *only* change: Reach 5 → 8, 0 invalid, target reached |
| 2.6 | `_update_button_appearance_handler` (`:7187`) takes `(self, button_states, model_key)` — no dataset argument | DRIFTED | `dashboard_manager.py:7250`; was `:7229` at the design's own date — the citation was already 42 lines off when written |
| 2.7 | `:7206` gates Start solely on `model_is_trainable` | DRIFTED | `dashboard_manager.py:7269-7270`; was `:7248` at design date |
| 2.8 | at `⊥`, `(recurrence, ⊥)` fails closed with a 409 | CONFIRMED | `backend/recurrence_backend.py:139-140` (`ok=False`, "no dataset reference") → `main.py:3614-3618` (`HTTPException(409)`) |
| 2.9 | `(cascor, ⊥)` sends the bare start POST and trains on the last-staged dataset | CONFIRMED | `main.py:3612` (`start_kwargs` only when `backend_type == "recurrence"`); Start not disabled — executed, `start_disabled=False` |
| **§4.1** | | | |
| 4.1.1 | `dashboard_manager.py:1334` is `clearable=False` on `nn-dataset-type-dropdown` | CONFIRMED (exact) | `dashboard_manager.py:1334` |
| 4.1.2 | `_build_model_selection_table(None,'cascor')` returns both Select buttons `disabled=False` | CONFIRMED (executed) | 2 buttons, `[False, False]`; predicate `disabled=not is_compatible` at `:3050`, `dataset=None` at `:3018` |
| 4.1.3 | `_dataset_model_hint_handler(None)` returns `''` | CONFIRMED (executed) | `dashboard_manager.py:2962` (`dataset_model_hint(...) or ""`) |
| 4.1.4 | `_resolve_oneshot_start_body_handler('one_shot', None)` returns `None` | CONFIRMED (executed) | `dashboard_manager.py:2679-2680` |
| 4.1.5 | pinned by `test_model_table.py:170-173`, comment "No dataset selected (e.g. cleared)" | CONFIRMED (exact) | `src/tests/regression/test_model_table.py:170-173` |
| 4.1.6 | **"All TEN Python consumers of `nn-dataset-type-dropdown.value`"** | **REFUTED (count)** | **NINE** reader sites; the tenth `.value` reference is the *writer* `Output(...,"value")` at `:2606`. Enumerated in this report's §2.1 |
| 4.1.7 | …are null-safe | CONFIRMED (executed, all 9) | none raises at `None`; three propagate `None` downstream — §5.2/§5.3 |
| 4.1.8 | there are **zero** JS consumers | CONFIRMED | no `.js/.ts/.css/.html` file in the repo references the id (6 asset JS files scanned) |
| 4.1.9 | the traversal `(cascor,spirals) → clear → (cascor,⊥) → Select Recurrence → (recurrence,⊥) → snap → (recurrence,equities_seq)` works | CONFIRMED (executed, end-to-end) | `gate('recurrence', None)` → `'equities_seq'`; BFS with clear only: target enters Reach |
| 4.1.10 | the snap behaves identically at `None` and `'spirals'`; only the `or not enabled` branch differs | CONFIRMED (executed) | both → `'equities_seq'`; with nothing enabled both → `no_update` (parks) |
| 4.1.11 | "the existing snap at `:2702-2706`" | CONFIRMED | `dashboard_manager.py:2702-2706`; the `if` itself is `:2704` |
| 4.1.12 | `gate_dataset_options` reads the dataset as `State` (`:2609`), not `Input` | CONFIRMED (exact) | `dashboard_manager.py:2609` `State(...)`; Inputs are `:2607-2608` |
| **§4.2** | | | |
| 4.2.1 | `_apply_dataset_handler:2845` would POST `nn_dataset_type: None` | CONFIRMED (exact + executed) | `dashboard_manager.py:2845`; executed payload `{'nn_dataset_type': None}` |
| 4.2.2 | `main.py:3994`'s `model_dump(exclude_none=True)` strips it | DRIFTED | now `src/main.py:4191` (+197). Substance holds; a **second** strip exists at `backend/cascor_service_adapter.py:1537` |
| 4.2.3 | …into a vacuous 200 plus a false pending-banner | CONFIRMED at handler level | handler returns `(True, None)` → banner opens. The 200 half was not exercised against a live service (no network) |
| 4.2.4 | "the correct idiom already exists at `_restage_dataset:5629-5631`" | DRIFTED (mis-cited) | idiom is at `dashboard_manager.py:5642-5644`; `:5631` is the `def`, `:5629` is the tail of `_describe_dataset`. Wrong at authoring time too |
| **§4.3** | | | |
| 4.3.1 | `:2695` labels the snap "dataset-primary" when it is model-primary | CONFIRMED (exact) | `dashboard_manager.py:2695` "…(dataset-primary conflict policy, D5)" |
| 4.3.2 | at `⊥` the table renders "✓ compatible" for every model (Y9) | CONFIRMED (executed) | both rows render `Span('✓ compatible')`; `:3033` `reason = … if dataset is not None else None`, `:3040-3041` |
| 4.3.3 | canopy has **zero** `Toast` components today | CONFIRMED | 0 occurrences of `Toast` in `src/` (non-test), 0 in `dashboard_manager.py` |
| 4.3.4 | Y7 records zero `aria-*` attributes in `dashboard_manager.py` | CONFIRMED | 0 matches for `aria-`/`aria_`/`role=`. (Aside: `src/frontend/assets/context_menus.js:95`, `tutorial_walkthrough.js:89` do carry them — the claim is correctly scoped to the Python file) |
| **§4.4** | | | |
| 4.4.1 | `_select_model_handler` mirrors only `nn_model` and `execution` (`:2893`; def `:2876`) | CONFIRMED (exact) | `dashboard_manager.py:2876`, `:2893`. It additionally reads `status` via `_model_summary_text` (`:2936`) |
| 4.4.2 | it does not read `swapped` / `backend` | CONFIRMED (source scan) | neither token appears in `_select_model_handler` or `_model_summary_text`; both **are** emitted by `main.py:3867` / `:3870` |
| 4.4.3 | `test_d8_d11_phase4_truth_up.py:64-82` pins the response shape | CONFIRMED (exact) | `src/tests/regression/test_d8_d11_phase4_truth_up.py:81` (`swapped is False`), `:82` (`backend != "recurrence"`) |
| **§4.5** | | | |
| 4.5.1 | `restart-ds-type` has no writer for `.options` **anywhere in the repo** | CONFIRMED | only 6 references repo-wide; the sole `.options` is the static layout seed `dashboard_manager.py:5435`; the only `Output` is `"value"` at `:5281` |
| 4.5.2 | `open_restart_confirm_modal` (`:5260-5293`) | DRIFTED (imprecise) | decorator `:5273-5305`, def `:5306`; `:5260-5271` is the enclosing method's docstring |
| 4.5.3 | the seeded gate is inverted for recurrence | CONFIRMED | `:5435` `options=gated_dataset_options(DEFAULT_MODEL_KEY)` — cascor's gate, `equities_seq` disabled |
| 4.5.4 | `execute_restart` forwards it | CONFIRMED | `State("restart-ds-type","value")` `:5379` → `:5395-5397` |
| **§4.6** | | | |
| 4.6.1 | `_resolve_oneshot_start_body_handler` (`:2681`) does not route through `generator_name_for_type` | CONFIRMED (exact + executed) | `:2681`; executed `oneshot('one_shot','spirals')` → `{'dataset': {'generator': 'spirals'}}` while the registry key is `spiral` |
| 4.6.2 | both sibling handlers do (`:2769`, `:2846`) | CONFIRMED (exact, both) | `:2769` `_render_dataset_params_handler`; `:2846` `_apply_dataset_handler` |
| **§4.7** | | | |
| 4.7.1 | `if current_value in enabled or not enabled: return options, dash.no_update` (`:2702-2706`) | CONFIRMED | `:2704-2705`; block `:2702-2706` |
| 4.7.2 | the `not enabled` arm parks instead of recovering | CONFIRMED (executed) | all-unavailable: returns `(options, no_update)`, all six disabled |
| **§4.8** | | | |
| 4.8.1 | `_update_button_appearance_handler` (`:7187`, gate `:7206`) must take the dataset | DRIFTED | see 2.6 / 2.7 — `:7250` / `:7269` now, `:7229` / `:7248` at design date |
| 4.8.2 | this is a callback-signature change | CONFIRMED | callback `:4471-4497` — 10 Outputs, 2 Inputs, no State; adding one changes arity |
| **§4.9** | | | |
| 4.9.1 | cascor's `Literal` (`juniper-cascor/src/api/models/training.py:235`) has no `equities_seq` → 502 | CONFIRMED (exact) | `training.py:235` — `["spirals","xor","mnist","circles","moons","equities","gaussian","checkerboard"]`; 502 path `cascor_service_adapter.py:1541-1543` → `main.py:4193-4196` |
| 4.9.2 | `RecurrenceBackend` has no `stage_dataset` | CONFIRMED | full method list `backend/recurrence_backend.py:108-306`; the `BackendProtocol` (`backend/protocol.py:232-328`) does not declare one either |
| 4.9.3 | called unguarded at `main.py:3995` → 500 | DRIFTED | now `main.py:4192`, and the call form changed `asyncio.to_thread(...)` → `await offload(...)` (X7 slice 1a, #567). Still unguarded; 500 at `main.py:4198-4202` |
| 4.9.4 | one-shot Start bypasses staging | CONFIRMED | `main.py:3612-3613` |
| **§4.10** | | | |
| 4.10.1 | "canopy has *never* hydrated the dataset from the backend. There is no dataset-hydration callback" | DRIFTED (over-broad) | true of the **type**: the dropdown's only writer is `:2606`, registry-driven. **False of the dataset config**: `init_params_from_backend` (`:4875-4921`) hydrates `nn-dataset-elements-input` `:4889`, `nn-dataset-noise-input` `:4890`, `nn-spiral-rotations-input` `:4887`, `nn-spiral-number-input` `:4888` from `/api/state` |
| 4.10.2 | **"`GET /api/train/status` carries no dataset field"** | **REFUTED (literal)** | `main.py:3708-3716` splats `backend.get_status()`, which carries `pending_dataset` — `backend/service_backend.py:308` (cascor path) and `backend/demo_backend.py:131` (demo path). It carries no *active-type* field, which is the substance |
| 4.10.3 | `nn_dataset_type` (`main.py:3971`) is a *request* model | DRIFTED | now `src/main.py:4168` (`StageDatasetRequest`, class at `:4159`) |
| 4.10.4 | X7 slice 1c added no hydration | CONFIRMED | `backend/status_cache.py` (366 lines) contains no dataset field; no new writer of `nn-dataset-type-dropdown.value` |
| **§4.11** | | | |
| 4.11.1 | `gated_dataset_options(None)` returns all six datasets enabled | CONFIRMED (executed) | 6 options, `disabled` flags `[F,F,F,F,F,F]`; `model_registry.py:416-423` |
| 4.11.2 | the handler early-returns `no_update, no_update` on a falsy `model_key` | CONFIRMED (exact + executed) | `dashboard_manager.py:2700-2701`; `gate(None,…)` and `gate('',…)` both → `(no_update, no_update)` |
| **§4.12** | | | |
| 4.12.1 | `demo_mode.py:551-554` calls juniper-data first, falls back on exception | CONFIRMED (exact) | `src/demo_mode.py:550-554` |
| 4.12.2 | its own comment names "Docker standalone, CI smoke test" | CONFIRMED (exact) | `src/demo_mode.py:548-549` |
| 4.12.3 | the fallback degrades **silently** (also G9's status-before) | DRIFTED | it logs `logger.warning` at `:553` and the local generator emits a `DeprecationWarning` at `:1061-1065`. Silent **in the UI**, not silent |
| 4.12.4 | (implied) one fallback site | REFUTED (scope) | **three**: `:551-554`, `:1821-1824`, `:2242-2245` |
| **§5 status-before** | | | |
| G1a | fails (5 of 6) | CONFIRMED (BFS) | Reach = 5, compatible∩available = 6, missing `('recurrence','equities_seq')` |
| G1b | passes | CONFIRMED (BFS) | 0 reachable committed-but-incompatible states |
| G1c | fails (2 unreachable) over a synthetic ≥3-component registry | **NO ARTIFACT** | not measurable at handler level today — `gated_dataset_options` has no injectable registry (the design's own enabling change). Registry-level arithmetic is consistent; the handler-level form could not be run |
| G1d | fails (parks) | CONFIRMED (executed) | all-unavailable → `(options, no_update)` |
| G2 | passes | CONFIRMED (BFS) | as G1b |
| G3 | fails | CONFIRMED (executed) | empty enabled set → `dash.no_update`, no recovery surface |
| G4 | **fails** (`spirals`/`moons` are not keys) | **REFUTED** | as worded ("**through `generator_name_for_type`**") the test **passes** today: all 6 seeds resolve to real registry keys. See §3.3 |
| G5 | fails | CONFIRMED | `swapped` never read (4.4.2) |
| G6 | fails | CONFIRMED (executed) | `start_disabled=False` for `cascor` and `recurrence` alike |
| G7 | fails — no hydration exists **at all** | DRIFTED | see 4.10.1 |
| G8 | fails — options freeze at the old gate | CONFIRMED (executed) | see 4.11.2 |
| G9 | fails — degrades silently | DRIFTED | see 4.12.3 |
| G10 | fails — 10 unseeded, none excluded | CONFIRMED (executed) | 10 unseeded; no exclusion list in `model_registry.py` or `dataset_schema.py` |
| G11 | fails for any new seed without them | DRIFTED (under-specified) | **5 of the 6 current seeds** have `default_params={}` — a literal G11 fails today on existing seeds, not only on new ones |
| §5-E1 | five resolvers lack an injectable parameter: `gated_dataset_options` `:408`, `get_model_spec` `:264`, `get_dataset_spec` `:276`, `dataset_type_options` `:200`, `dataset_default_params` `:209` | CONFIRMED (all five lines exact) | `src/model_registry.py` — signature census by `inspect.signature` |
| §5-E2 | "while `compatible_models`, `compatible_datasets` and `model_options` have one" | DRIFTED (incomplete) | **five** have one: those three plus `model_is_trainable` (`:232`) and `dataset_model_hint` (`:382`) |
| §5-E3 | `dataset_default_params` is on G1's path via `:2682` | CONFIRMED (exact) | `dashboard_manager.py:2682` |
| §5-E4 | `_gate_dataset_options_handler` needs its generator list injectable — it calls live HTTP and fails open under test | CONFIRMED | `_fetch_generators` `:2713-2735`; `except → generators = []` → `is_generator_available` returns True for everything |
| §5-E5 | "G1 over `model_registry` alone goes green on the deadlocked code — measured" | CONFIRMED (re-measured) | registry-level reach == the full compatible set (6/6) |
| **§12.1** | | | |
| 12.1.1 | `GENERATOR_REGISTRY` (`juniper-data/juniper_data/api/routes/generators.py:44`) registers 16 | CONFIRMED (exact + executed) | `len(GENERATOR_REGISTRY) == 16` |
| 12.1.2 | canopy `DATASET_TYPES` seeds 6 | CONFIRMED (executed) | `model_registry.py:132-150` |
| 12.1.3 | the ten unseeded split 5 rank-2 / 5 rank-3 exactly as tabulated | CONFIRMED (executed, exact set match) | rank-2 `{arc_agi, checkerboard, csv_import, equities, gaussian}`; rank-3 `{ar_p, delay_product, irregular_sine, mackey_glass, multi_sine}` |
| 12.1.4 | `irregular_sine`, `delay_product` are explicitly non-uniform Δt | CONFIRMED (executed) | the only two params classes carrying a `jitter` field (default `0.5`) |
| **§12.2** | | | |
| 12.2.1 | the graph keeps exactly **two** connected components after the expansion | CONFIRMED (executed) | 2 before (6 datasets), 2 after (16 datasets) |
| **§12.3** | | | |
| 12.3.1 | Y5: proxy sends no `X-API-Key`; `/v1/generators` not auth-exempt; fallback is a schema-less 4-entry list | CONFIRMED (all three) | `canopy src/main.py:1854` (no `headers=`); `juniper-data juniper_data/api/constants.py:72-80`; `canopy src/main.py:1866-1874` (4 entries, no `schema`, no `available`). Conditional: juniper-data auth engages only when `settings.api_keys` is set (`api/app.py:53`) |
| 12.3.2 | `equities_seq` needed `max_symbols=5` for the 300 s train timeout | CONFIRMED | `model_registry.py:148`; `backend/recurrence_service_adapter.py:101` `_DEFAULT_TRAIN_READ_TIMEOUT = 300.0` |
| 12.3.3 | `mackey_glass` accepts a `seed` and ignores it | CONFIRMED (conditional) | `mackey_glass/generator.py:64-66` — the seed is consumed only inside `if params.init_noise_std > 0`; `init_noise_std` default resolves to `DEFAULT_MACKEY_GLASS_INIT_NOISE_STD`, fallback `0.0` (`core/constants.py:71`) but **env-overridable** (`:72`, `:93`). Inert *by default*, not unconditionally |
| 12.3.4 | `csv_import` is an import path; canopy already has `dataset_import.py` | CONFIRMED | `canopy src/dataset_import.py`, `parse_csv_bytes` `:44` |
| 12.3.5 | `arc_agi`'s rank is unverified — confirm before seeding | CONFIRMED, and now measured rank-2 | no `lookback` field, no `time_unit`, `task_type="classification"` — the same test that classifies `mnist` as rank-2 |

**Counts (85 rows)** — **CONFIRMED 66** · **DRIFTED 14** · **REFUTED 4** · **NO ARTIFACT 1**.

Three DRIFTED rows are the same artifact seen twice (`2.6`/`2.7`/`4.8.1` are one handler;
`4.10.1`≡`G7`; `4.12.3`≡`G9`), and three more (`4.2.2`, `4.9.3`, `4.10.3`) are three citations of
the one +197 `main.py` shift. De-duplicated: **10 distinct drifted artifacts, 4 refutations, 1
unmeasurable.**

---

## 2. REFUTED findings

### 2.1 §4.1 — "All **TEN** Python consumers of `nn-dataset-type-dropdown.value`" → there are NINE

Repo-wide search (`grep -rn "nn-dataset-type-dropdown"`, all file types, excluding `build/`,
`node_modules/`, `.git/`) returns **13** hits in `src/frontend/dashboard_manager.py`. Classified:

| line | kind | consumer? |
|------|------|-----------|
| `:1331` | `id=` in the layout | no — the declaration |
| `:1845` | a comment | no |
| `:2576` | `State(...,"value")` → `_toggle_model_modal_handler` | **read 1** |
| `:2605` | `Output(...,"options")` | no — writer, different property |
| `:2606` | `Output(...,"value")` | no — **writer** |
| `:2609` | `State(...,"value")` → `_gate_dataset_options_handler` | **read 2** |
| `:2624` | `Input(...,"value")` → `_render_dataset_params_handler` | **read 3** |
| `:2637` | `Input(...,"value")` → `_resolve_oneshot_start_body_handler` | **read 4** |
| `:2649` | `Input(...,"value")` → `_dataset_model_hint_handler` | **read 5** |
| `:4935` | `State(...,"value")` → `_apply_dataset_handler` | **read 6** |
| `:5166` | `State(...,"value")` → `_open_live_switch_modal_handler` | **read 7** |
| `:5223` | `State(...,"value")` → `_accept_live_switch_handler` | **read 8** |
| `:5298` | `State(...,"value")` → `_open_restart_confirm_modal_handler` | **read 9** |

Nine readers. The count reaches ten only by including the `Output(..., "value")` **writer** at
`:2606` — which is not a consumer, and which is the very callback §4.1 is analysing as the thing
that *sets* the value.

The set was byte-identical at the design's own commit (`9fbf4b8`), so this is an authoring
mis-count, not X7 drift.

**Why it matters despite being off by one.** The claim is used as a safety argument ("all ten are
null-safe, so `clearable=True` is safe"). A count that silently includes the writer is a count
whose enumeration was not audited — and the audit is the safety argument. The substance survives
(verdict row 4.1.7), but the number should read **nine**.

### 2.2 §4.10 / G7 — "`GET /api/train/status` carries no dataset field" → it carries `pending_dataset`

```
src/main.py:3708  @app.get("/api/train/status", dependencies=[Depends(require_browser_control_auth)])
src/main.py:3715      status = await offload(backend.get_status)
src/main.py:3716      return {"backend": backend.backend_type, "execution": backend.execution, **status}
```

`**status` is the backend's payload. Both shipped non-recurrence backends put a dataset field in it:

```
src/backend/service_backend.py:308      "pending_dataset": raw.get("pending_dataset"),
src/backend/demo_backend.py:131         "pending_dataset": getattr(self._demo, "_pending_dataset_config", None),
```

So the route **does** carry a dataset field. What it does not carry is the *active/staged dataset
type* — `pending_dataset` is the staged-but-unapplied config and is `None` whenever nothing is
staged, which is the steady state the design cares about.

**Consequence for the design, and it is not cosmetic.** §4.10 concludes that PR 2 needs "a new
route or route field". The measurement says a dataset channel on this route **already exists** and
is already carried through from cascor (`cascor #242` per the comment at `:303-307`). Whether PR 2
is "add a field" or "widen the existing `pending_dataset` carry-through to include the applied
type" is a real design fork the sentence as written forecloses. The §6 sizing note ("§4.10
hydration (a new route or route field plus a mount callback)") inherits the error.

### 2.3 §5 G4 — "status before: **fails** (`spirals`/`moons` are not keys)" → it passes today

G4 as specified: *"canopy `DATASET_TYPES` maps onto juniper-data `GENERATOR_REGISTRY` **through
`generator_name_for_type`**"*. Executed against both live registries:

```
spirals        -> spiral         in registry? True    raw 'spirals'      in registry? False
xor            -> xor            in registry? True
mnist          -> mnist          in registry? True
circles        -> circles        in registry? True
moons          -> moon           in registry? True    raw 'moons'        in registry? False
equities_seq   -> equities_seq   in registry? True
```

All six map. The alias map that makes them map is already shipped
(`src/dataset_schema.py:97-100`, `{"spirals": "spiral", "moons": "moon"}`), and the test-plan row
*names that function in its own test statement*. The parenthetical reason — `spirals`/`moons` are
not keys — is true and is exactly what the alias exists to fix; it describes the **un-aliased**
mapping, i.e. a different test.

So the row is internally inconsistent: the stated test passes before the change, and the stated
reason belongs to a test that is not the one stated. §5's framing sentence ("Specified to **fail**
on today's code") does not hold for G4. Either the test statement should drop "through
`generator_name_for_type`", or the status-before should read *passes*.

### 2.4 §4.12 — one demo-mode fallback site → there are three

§4.12 and OQ-N2's disposition both locate the fallback at `demo_mode.py:551-554` and specify one
remedy ("a visible degraded-mode banner whenever the local generator is used"). There are three
call sites of `_generate_spiral_dataset_local`, each in its own `try/except`:

```
src/demo_mode.py:551-554     DemoMode.__init__            (the one the design names)
src/demo_mode.py:1821-1824   restart_dataset
src/demo_mode.py:2242-2245   the spiral_rotations param path (regenerate on rotation change)
```

A fix that instruments only the constructor leaves demo mode able to *become* degraded mid-session
— on a dataset restart or a rotations change — with no banner. That is the same shape as the defect
G9 exists to close, arriving through the un-instrumented door.

---

## 3. DRIFTED findings

### 3.1 §2 / §4.8 — `_update_button_appearance_handler` line numbers were wrong when written

| citation | design | at design date (`9fbf4b8`) | at HEAD (`fc62175`) |
|----------|--------|---------------------------|---------------------|
| handler def | `:7187` | `:7229` | `:7250` |
| the Start gate | `:7206` | `:7248` | `:7269` |

A constant −42 offset at authoring time, then a further +21 from X7. The **substance is exactly
right** and X7 did **not** touch this handler:

```
7250:  def _update_button_appearance_handler(self, button_states=None, model_key=None):
7269:      if not model_is_trainable(model_key):
7270:          start_disabled = True
```

Executed: `start_disabled` is `False` for `model_key="cascor"` and for `"recurrence"` with a clean
`button_states`. No dataset argument exists on the signature or on the callback
(`:4471-4497`: 10 Outputs, 2 Inputs `button-states` + `model-selection-store`, no State).

X7 slices 1a/1c/1d did **not** change this handler, so §4.8's plan does not collide with X7.

### 3.2 §4.2 / §4.9 / §4.10 — every `main.py` citation drifted by +197

`main.py` was `27af847` (2026-08-28) when the design was written; three X7 commits have landed
since (`94220f0` 1a, `644967b` 1c, `c2c3cb7` 1d) plus `7a70f35`. All three cited lines were
**exactly right then**:

| design | then | now | note |
|--------|------|-----|------|
| `main.py:3971` `nn_dataset_type` request field | `:3971` | `:4168` | class `StageDatasetRequest` now at `:4159` |
| `main.py:3994` `model_dump(exclude_none=True)` | `:3994` | `:4191` | |
| `main.py:3995` `backend.stage_dataset` unguarded | `:3995` | `:4192` | **call form changed**: `await asyncio.to_thread(...)` → `await offload(...)` (X7 slice 1a) |

The `offload()` rewrite is the only shape change and it does not affect the claim — the call is
still made without a `hasattr` guard, so a `RecurrenceBackend` still raises `AttributeError` into
`except Exception` at `:4198-4202` → **500 with an opaque `error_id`**, as §4.9 says.

### 3.3 §4.2 — the "correct idiom" citation points at the wrong lines

Design: *"The correct idiom already exists at `_restage_dataset:5629-5631`."* The idiom is:

```
dashboard_manager.py:5642      dtype = dataset_vals.get("dataset_type")
dashboard_manager.py:5643      if dtype is not None:
dashboard_manager.py:5644          payload["nn_dataset_type"] = dtype
```

`:5631` is `def _restage_dataset`; `:5629` is the last line of `_describe_dataset`. Verified
identical at the design's own commit — the citation was wrong when written. The claim's substance
holds: `_restage_dataset` does guard, and `_apply_dataset_handler` (`:2845`) does not.

### 3.4 §4.10 / G7 — "no dataset hydration **at all**" is over-broad

The dataset **type** is never hydrated — correct, and the important half. But canopy *does*
hydrate four dataset-config fields from the backend on mount:

```
dashboard_manager.py:4875-4921   init_params_from_backend  (Input: params-init-interval)
  :4887  Output("nn-spiral-rotations-input", "value")
  :4888  Output("nn-spiral-number-input",    "value")
  :4889  Output("nn-dataset-elements-input", "value")
  :4890  Output("nn-dataset-noise-input",    "value")
```

sourced from `GET /api/state`, which carries `nn_dataset_elements` (`main.py:1339`, `:1425`) and
`nn_dataset_noise` (`:1340`, `:1426`) but **no** `nn_dataset_type`. So the shape of the gap is:
*the state route exposes the dataset's parameters and not its identity, and the mount callback that
would carry the identity already exists*. That is a materially smaller job than "no hydration
exists at all", and it names where PR 2's mount callback should live (`init_params_from_backend`,
which already fires on `params-init-interval` — the same Input `gate_dataset_options` uses at
`:2608`).

### 3.5 §4.12 / G9 — "degrades silently"

`demo_mode.py:553` logs `self.logger.warning("JuniperData dataset generation failed (%s), falling
back to local generation", exc)`, and `_generate_spiral_dataset_local` raises a `DeprecationWarning`
(`:1061-1065`). The degradation is invisible **in the UI**, which is what N13 and G9 are about; it
is not invisible in the log. Worth fixing the word, because "silently" is the sort of claim a later
reader checks by grepping for a logger call and then distrusts the whole section.

### 3.6 §5 G11 — under-specified against the current seeds

G11: *"every seeded generator has bounded `default_params`"*, status-before *"fails for any new seed
without them"*. Executed over today's seeds:

```
spirals        default_params={}
xor            default_params={}
mnist          default_params={}
circles        default_params={}
moons          default_params={}
equities_seq   default_params={'max_symbols': 5, 'regression_target': 'return'}
```

Written literally the test **fails today on five existing seeds**. It presumably intends "every
seeded generator whose one-shot path is unbounded", or "every *newly* seeded generator" — but as
written it either fails on the incumbents or needs an exemption the design does not state. §12.3.2's
rationale (the 300 s `_DEFAULT_TRAIN_READ_TIMEOUT` on the one-shot path) applies only to one-shot
models, i.e. rank-3 seeds; the five 2-D seeds never take that path.

### 3.7 §5 Enabling change — the "have one" list is incomplete

Five resolvers lacking an injectable parameter: **confirmed exactly**, all five line numbers exact
(`:408`, `:264`, `:276`, `:200`, `:209`). The complement is stated as three; a full
`inspect.signature` census of `model_registry` shows **five** functions carry a keyword-only
injectable:

```
compatible_datasets(model, *, dataset_types=DATASET_TYPES)   :329
compatible_models  (dataset, *, models=MODELS)               :321
dataset_model_hint (dataset_value, *, models=MODELS)         :382   <- not listed
model_is_trainable (model_key, *, models=MODELS)             :232   <- not listed
model_options      (*, models=MODELS)                        :222
```

Harmless to the plan, but it is the same enumeration habit as §2.1: the group the author needed was
audited, the group they did not need was recalled.

### 3.8 §4.5 — `open_restart_confirm_modal` range

Design cites `:5260-5293`. The callback's decorator opens at `:5273` and closes at `:5305`, with the
def at `:5306`; `:5260-5271` is the enclosing `_setup_restart_orchestration_callbacks` docstring.
The Output list the design wants to extend is `:5274-5294`. Imprecise, not wrong in substance — the
claim that `Output("restart-ds-type","options")` must be *added* is confirmed (verdict row 4.5.1).

---

## 4. NO ARTIFACT

### 4.1 §5 G1c — "fails (2 unreachable)" over a synthetic ≥3-component registry

I could not measure this at the level the design specifies. G1 is required to live at handler
level (§5's own last line), and the handler path runs
`gated_dataset_options(model_key)` → `model_registry.DATASET_TYPES` / `MODELS` **module globals**
(`model_registry.py:416-423`). There is no injection point, which is precisely the enabling change
§5 asks for. Monkeypatching the module globals would be measuring my patch, not the shipped code,
so I did not report a number from it.

At registry level the arithmetic is consistent with "2 unreachable" for a 3-component registry
(a third component's model and its dataset are both unreachable from a mount in component 1, and
the pair count depends on how many datasets the third component holds — "2 unreachable" is right for
one dataset + one model, or for two datasets, depending on how pairs are counted). I state that as
**not re-derived**, not as agreement.

---

## 5. Additional findings the design does not state

These are not verdicts on design claims. They surfaced while executing the claims and bear on the
same PRs, so they are recorded rather than dropped.

### 5.1 `equities_seq`'s `task_type` diverges between the two registries

```
canopy   src/model_registry.py:138-149   task_type="regression",     ndim=3, temporal="irregular"
data     .../routes/generators.py         task_type="classification", time_unit="calendar_days"
```

canopy's `compatible()` (`model_registry.py:318`) tests `dataset.task_type in
model.supported_task_types`, and `recurrence.supported_task_types == frozenset({"regression"})`. The
gate works **only** because canopy keeps its own value. If the capability model is ever relocated to
the producing service — family F5, the design's stated follow-on (§1, "Out of scope, deliberately")
— `equities_seq` becomes cascor-compatible and recurrence-**in**compatible, inverting the very gate
this arc is repairing. Worth carrying into F5's scope note.

### 5.2 The Live Dataset Switch is a second, unnamed X4 site

`_accept_live_switch_handler` (`:6046`) builds its payload then strips falsy-`None` keys:

```
dashboard_manager.py:6062-6069
    payload = {"nn_dataset_type": dataset_type, ...}
    payload = {k: v for k, v in payload.items() if v is not None}
```

Executed at `dataset_type=None` it does **not** crash (so "null-safe" holds) — it POSTs
`/api/live_dataset_swap` with the four spiral fields and **no dataset type**, then renders
*"Live dataset swap complete."* §4.2 names Apply Dataset and §4.5 names the restart modal; this
third control takes `⊥` straight to a live swap. Mitigation on the record: the button ships
`disabled=True` (`dashboard_manager.py:1367`) and is gated by the `experimental-flags-store` +
`training-status-store` combination (layout comment `:1352-1360`; the gate now lives inside
`update_unified_status_bar`, `:3285-3313`), so it is not on the default path — but N9 ("a control
that cannot be honoured is disabled at the control") applies to it identically.

### 5.3 `⊥` propagates into a `clearable=False` dropdown in the restart modal

`_open_restart_confirm_modal_handler` (`:5473`) returns `dataset_vals["dataset_type"]` into
`Output("restart-ds-type","value")` (`:5281`, slot index 5). Executed at `dataset_type=None` it
returns `None` into that slot. `restart-ds-type` is `dcc.Dropdown(..., clearable=False)` at `:5435`,
so the modal opens showing no dataset and offering no way to express "unchanged"; `execute_restart`
then forwards `ds_type=None` (`:5395`). `_restage_dataset` guards it (`:5643`), so nothing is
mis-staged — but the baseline diff at `:5494` records `dataset_type: None`, which `_values_differ`
(`:5551-5560`) treats as *different from anything*. PR 3's `⊥` should either disable the field or
seed it from the baseline.

### 5.4 X3's blast radius includes the clientside transport

The un-aliased generator name from `:2681` lands in `oneshot-start-params-store` (`:2635`), which is
read as `State` by **both** Start transports — `:4398` (server-side REST) and `:4423` (Phase D
clientside JS). §4.6 frames X3 as one handler's omission; the wrong value reaches the browser path
too. Fixing it at `:2681` fixes both, which is the good news; the acceptance check should exercise
both.

### 5.5 The stage path strips `None` twice, not once

Besides `main.py:4191`, `cascor_service_adapter.py:1537` filters again:
`{... for k, v in canopy_params.items() if k in self._DATASET_PARAM_MAP and v is not None}`. Either
strip alone produces X4's vacuous 200. A guard added at only one of them does not close it; §4.2's
guard belongs at the handler (`:2845`), as the design says.

### 5.6 An independent reproduction of the evaluation's F2 table

§2's F2 sentence attributes its numbers to the evaluation document
(`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` §5.1). I re-derived them from
the shipped handlers without reading the simulation script, by replacing the model-Select predicate
with the unary `compatible_datasets(model)` form:

| scenario | guard | reachable | invalid | target reached |
|----------|-------|-----------|---------|----------------|
| all available | today (joint) | 5 | 0 | no |
| all available | F2 unary | 6 | **0** | **yes** |
| `equities_seq` unavailable | today (joint) | 5 | 0 | no |
| `equities_seq` unavailable | F2 unary | 10 | **5** | no |
| all available | this design (clear, gates hard) | 8 | 0 | yes |
| `equities_seq` unavailable | this design | 7 | 0 | no (correctly — it is unavailable) |

The `10 / 5 / unreached` row matches the evaluation's S3 exactly, and `6 / 0 / reached` matches S2.
**The design's §2 sentence states the S3 result unconditionally.** Under S2 the rejected family is
clean and *does* reach the target. The rejection stands — S3 is the container, i.e. the deployed
state — but the sentence should carry its condition, because a reader who checks it in the
all-available case will find it false and distrust §2's other four claims.

---

## 6. Instrument adequacy

Required by §2 Lane A: *could this instrument have produced a different answer?*

| claim(s) | instrument | could it have failed? |
|----------|-----------|------------------------|
| 4.1.2, 4.1.3, 4.1.4, 4.3.2 | direct invocation of the static handlers at `None`, asserting the returned Dash components | **Yes.** The same probe, run on `_build_model_selection_table("spirals","cascor")` as a control, returned `recurrence.disabled=True` — the opposite answer on adjacent input. A probe that returns `[False, False]` for one input and `[False, True]` for another is discriminating |
| 4.1.9, G1a, G1b, G2, 2.1, 2.2, 2.5 | BFS over the composed relation, transitions read off `:3050` (model gate) and the gate handler's own option list, with `clear` a toggle | **Yes.** The identical BFS returns Reach 5 with `allow_clear=False` and Reach 8 with `allow_clear=True`, and returns 0 vs 5 invalid states when the model predicate is swapped for F2's. Four distinct outcomes from one instrument across four configurations |
| 4.1.7 (null-safety of 9 consumers) | invoke each handler at `dataset=None` with `requests` monkeypatched to a capture stub | **Yes — and it did fail once.** My first shim lacked `_read_restart_param_seed`, so consumer 9 raised `AttributeError`. That was **my** defect, not the code's; I rebuilt the shim binding the real helper and re-ran before recording a verdict. An `AttributeError` from an under-built shim is not evidence about the claim, and I did not record the first result |
| 4.2.1 | executed `_apply_dataset_handler` with a fake `requests.post` capturing the body | **Yes.** The same capture, run with `dataset_type="spirals"`, returns the spiral typed fields — so the stub records what it is given rather than a constant |
| 4.11.1 | `gated_dataset_options(None)` | **Yes.** `gated_dataset_options("recurrence")` on the same call path returns 5 of 6 disabled |
| 12.1.3 (rank split) | **first instrument was inadequate and I discarded it.** I initially discriminated rank by `issubclass(params_class, SyntheticSequenceParams)` imported from a guessed module path; the import failed, `SEQ` fell to `None`, and every generator scored `seq=False` — a clean, uniform, entirely false answer that would have "refuted" the design's table. Detected because 16/16 rank-2 is not a plausible reading of a registry containing `equities_seq`. The second instrument imports the base from the path `juniper_data/tests/unit/test_registry_dispatch_completeness.py:35` uses, and cross-checks with `"lookback" in params_class.model_fields` and the registry's `time_unit` key — three signals that agree | **Yes, on the second instrument** — it separates 6 from 10 and its two independent signals agree row by row. **This is the one place a silent-null instrument nearly produced a confident wrong REFUTED** |
| 12.2.1 (component count) | union-find over `mr.compatible()` on a synthetic 16-dataset registry | **Yes — control run.** `p9_control.py`: seeded → 2; **+ one `ndim=3, task_type="classification"` dataset → 3**; + a disjoint rank-4 model and dataset → 3. The count is not pinned at 2 by construction |
| 4.11.1 (control) | `gated_dataset_options` across four keys | **Yes — control run.** `None` → `[F,F,F,F,F,F]`; `'cascor'` → `[F,F,F,F,F,T]`; `'recurrence'` → `[T,T,T,T,T,F]`; `'nonsense'` → `[F,F,F,F,F,F]`. Three distinct outputs, so the all-enabled answer for `None` is a measurement, not a default. (Note the fourth row: an *unknown* key also ungates — `model_registry.py:416-419` — so `gated_dataset_options` cannot distinguish "no model" from "stale model") |
| 2.8, 4.9.1, 4.9.2, 4.9.3, 12.3.1 | reading declarations (`Literal` members, method lists, `EXEMPT_PATHS`, a `client.get` call with no `headers=`) | **Partly.** These are absence claims read from a declaration. The `Literal` and `EXEMPT_PATHS` are closed enumerations, so absence is decisive. `RecurrenceBackend` has no `stage_dataset` is decisive for the class but **not** for a runtime-attached attribute — I did not instantiate the backend, so a `setattr` elsewhere would not have been seen. I grepped for `stage_dataset` across `src/` and found no such assignment |
| 4.10.2 | reading `**status` splat plus both `get_status` implementations | **Yes** — it produced the REFUTED. The same read of `RecurrenceBackend.get_status` (`:204-226`) shows **no** dataset field, so the instrument distinguishes the three backends rather than answering "yes" everywhere |
| 4.2.3 ("vacuous 200") | **not measured end-to-end.** No live service was contacted, per the brief. I confirmed the handler half (banner opens) and both `None`-strips by reading. The 200 itself depends on cascor's response to an empty stage body | **No** — this half of the claim is *unverified*, not confirmed. Recorded as such |
| line-number drift | `git show <commit>:<path>` into the scratchpad, then grep both trees | **Yes.** It returned "unchanged" for `dashboard_manager.py`'s `:1331-5298` block, "+197" for `main.py`, and "already wrong by −42" for `:7187` — three different answers, so it is not a rubber stamp |
| 5.6 (F2 reproduction) | union-find/BFS with the model predicate swapped, run in both availability scenarios | **Yes.** It produced 0 invalid in one scenario and 5 in the other from the same code — and the 5 matched a number I had not yet read. I read the evaluation's §5.1 table **after** running the simulation, specifically so the number could not be reconstructed from it |

**What this evidence cannot support.**

- Nothing here was observed in a browser. Every `⊥` result is a handler-level execution. The design's
  own OQ-N5 says the same ("the traversal in §4.1 is so far established only by executing handlers,
  never in a DOM") and schedules a PR-3 re-run; this pass does not discharge that.
- No claim about runtime behaviour of a live cascor, juniper-data or juniper-recurrence service was
  tested — no network calls were made. The 502 (§4.9) and the vacuous 200 (§4.2) are traced through
  code paths, not observed.
- The availability scenarios are **injected**, not read from a deployment. "The container's LMU has
  zero available datasets" is confirmed as *`yfinance` is absent from
  `juniper-data/requirements.lock`* plus *the gate behaves this way when told the generator is
  unavailable* — not as an observation of the running container.
- G1c is not re-derived at all (§4.1).
- §2's cross-document claims about the evaluation's §2.1 / §5.1 / §7 were checked only where a
  number was quoted (F2, §5.6). The rest of the evaluation was not audited.
- Sample size for every execution result is **1 run of a deterministic pure function**; none of these
  handlers carries state across calls except `_fetch_generators`' TTL cache, which was stubbed out.

---

## 7. Method appendix — instruments

Probes live in this session's scratchpad and are reproduced here so the instrument is on the record
rather than only its output. All were run with `conda run -n JuniperCanopy1 python <probe>`
(canopy / cross-repo) or `conda run -n JuniperData python <probe>` (juniper-data). The direct
interpreter path was **not** used: `~/.bashrc` exports a stale `LIBTORCH` / `LD_LIBRARY_PATH` that
shadows the env's torch and produces broad `undefined symbol` ImportErrors that look like a
regression and are not.

| probe | what it measures |
|-------|------------------|
| `p1_canopy.py` | §4.1 / §4.2 / §4.6 / §4.7 / §4.11 handler execution; `model_registry` signature census |
| `p2_nullsafe.py` | null-safety of all nine `.value` consumers; `_select_model_handler` field scan; the deadlock premise |
| `p3_data_registry.py` / `p4_rank.py` | §12.1 registry census and the rank split (p3's discriminator was inadequate; p4 replaced it) |
| `p5_rest.py` | consumer 9 with a complete shim; §12.2 component count; the `equities_seq` task_type divergence |
| `p6_bfs.py` | the composed-relation BFS behind G1a/G1b/G2/G1d and §2 |
| `p7_f2.py` / `p8_f2_container.py` | independent reproduction of the evaluation's F2 table in both availability scenarios |
| `p9_control.py` | instrument-adequacy controls for the component counter and the option gate |

Transition model used by the BFS, read off the shipped code rather than the design's prose:

- **T1 select model M′** — admitted iff `_build_model_selection_table(d, m)`'s button for M′ has
  `disabled is False` (`:3050`: `disabled = not is_compatible`); then `gate_dataset_options` fires
  (its Input is `model-selection-store`, `:2607`) and may snap `d`.
- **T2 pick dataset d′** — admitted iff d′'s option is enabled in the *current* gated list; the gate
  does **not** re-fire, because the dataset rides as `State` (`:2609`).
- **T3 clear** — not admitted today (`clearable=False`, `:1334`); toggled on to model §4.1.

The probe files live only in this session's scratchpad, so the load-bearing instrument is inlined
here rather than lost with the session (per the ecosystem's `/tmp`-is-not-a-home rule; a graduated
copy belongs in `juniper-canopy/util/ad-hoc/` if PR 3 wants to keep it):

```python
def reach(shim, start, allow_clear):
    """BFS the composed transition relation over the SHIPPED handlers. shim._fetch_generators()
    returns the injected /v1/generators list, so no network call is made."""
    seen, frontier = {start}, [start]
    while frontier:
        m, d = frontier.pop()
        # T1 -- select another model, admitted only if its table button is enabled (:3050)
        for m2, disabled in buttons(DM._build_model_selection_table(d, m)).items():
            if disabled or m2 == m:
                continue
            _opts, val = DM._gate_dataset_options_handler(shim, m2, d)   # the snap fires
            d2 = d if val is dash.no_update else val
            if (m2, d2) not in seen:
                seen.add((m2, d2)); frontier.append((m2, d2))
        # T2 -- pick a dataset from the CURRENT gated options; the gate does NOT re-fire (:2609 State)
        opts, _ = DM._gate_dataset_options_handler(shim, m, d)
        if opts is not dash.no_update:
            for o in opts:
                if o.get("disabled") or o["value"] == d:
                    continue
                if (m, o["value"]) not in seen:
                    seen.add((m, o["value"])); frontier.append((m, o["value"]))
        # T3 -- clear (clearable=True only)
        if allow_clear and d is not None and (m, None) not in seen:
            seen.add((m, None)); frontier.append((m, None))
    return seen
```

`buttons(table)` walks the returned `dbc.Table` and returns `{model_key: button.disabled}`.
`DM` is `frontend.dashboard_manager.DashboardManager`; the handlers are called unbound with a
shim `self` exposing only `_fetch_generators`.
