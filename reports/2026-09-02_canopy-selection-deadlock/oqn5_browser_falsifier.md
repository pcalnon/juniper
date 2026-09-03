# OQ-N5 — the browser falsifier, executed

**Date**: 2026-09-02
**Instrument**: isolated juniper-data 8103 / juniper-cascor 8204 / juniper-canopy 8053, brought up by
`util/isolated_stack.bash --up` with `JUNIPER_E2E_*` port + run-dir overrides
(`JUNIPER_E2E_RUN_DIR=/tmp/juniper-e2e-oqn5`, `JUNIPER_E2E_DATA_EXTRAS=api,equities`).
Driver: Playwright MCP, real CDP-dispatched (trusted) input.
**Not touched**: the operator's stack (8050 / 8201) and a concurrent session's isolated stack
(8051 / 8101 / 8202 / 8211). Verified clear before and after.

---

## 1. Result — both gates HOLD

| falsifier | control | trusted click delivered | state after | verdict |
| --- | --- | --- | --- | --- |
| **A** | dataset option `Equities (sequence) — needs a 3-D model` | yes (`clickErr: null`) | dropdown still `Spirals`; menu did not close | **GATE HELD** |
| **B** | model row `Recurrence (LMU)` Select button | yes (`clickErr: null`) | summary still `Active: CasCor (Cascade-Correlation)`; dataset still `Spirals` | **GATE HELD** |

This closes the last open evidence gap in
`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` §9. The deadlock is confirmed
end-to-end in a live DOM, not only by executing handlers.

The live page reproduced the operator's screenshots exactly: dataset `Spirals`, summary
`Active: CasCor (Cascade-Correlation)`, hint `rank-2 (tabular) models only`, and a six-option menu
ending in `Equities (sequence) — needs a 3-D model`.

## 2. The two gates have DIFFERENT accessibility postures

Measured on the rendered elements:

| | dataset option (Equities) | model Select (Recurrence) |
| --- | --- | --- |
| native `disabled` | — (not a form control) | **`true`** |
| `aria-disabled` | **`null`** | `null` (native `disabled` conveys it) |
| `pointer-events` | `auto` | `none` |
| `cursor` | **`not-allowed`** | — |
| colour | `rgba(0, 21, 89, 0.6)` (dimmed) | — |
| class vs enabled peers | **identical** | — |
| `title` | — | `needs 3-D data` |

**The dataset gate is enforced in JavaScript, not by native semantics, and is invisible to assistive
technology.** Its only machine-readable signal is `cursor: not-allowed`, which no screen reader
announces. The model gate, by contrast, is a real disabled `<button>` and is correctly exposed.

This confirms and sharpens Y7 empirically: the reason text in the option **label** is the only
accessible channel on the dataset side — exactly what D2 of
`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` mandated, and (as P1
predicted) it survives by accident rather than by design.

## 3. New defect — canopy blocks when its backend is unreachable

Found while quiescing the page. **Reproduced and causally confirmed:**

| cascor (8204) | canopy `/v1/health` (8053) |
| --- | --- |
| up | **200** in 8 ms |
| stopped (SIGTERM) | **no response** (curl `--max-time 8` → exit 28) |
| restarted | **200** in 6 ms — *canopy was never restarted* |

Mechanism, from `logs/juniper-canopy.log`:

1. Dash callbacks fetch **canopy's own REST API** — `Failed to fetch metrics from API: ReadTimeout:
   HTTPConnectionPool(host='127.0.0.1', port=8053): Read timed out. (read timeout=2)`. Canopy calls
   itself over HTTP (`_fetch_generators` and siblings use `self._api_url(...)`).
2. Those handlers call cascor synchronously **with urllib3 retries** — `Retry(total=2 … 1 … 0)` per
   call, across `/v1/metrics/history`, `/v1/training/params`, `/v1/history/dataset_swaps`.
3. With cascor refusing connections, each call burns its retry budget before failing.
4. Because the caller *is* canopy, its own workers block on those retrying outbound calls, so the
   server cannot answer new requests — **including `/v1/health`**. Observed 66 threads.

It is a **liveness** failure, not a crash: canopy recovers on its own once the backend returns.

**Consequence for the arc**: this is very likely why E2E journey W8 was blocked `N-A`
(`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:1756`) and why this falsifier
appeared impossible for most of the session. An *environmental* blocker masked a *UI* blocker —
and the environmental blocker turns out to be a canopy defect, not an environment problem.

## 4. Correction to the record

`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` §9 states that canopy "accepts
TCP on 8050 but never responds". That was true when measured three times (curl, a browser
navigation, and Lane A1's probe) but it is **transient, not standing**: both the operator's canopy
(8050) and the isolated one answered `/v1/health` and `/dashboard/` in under 10 ms afterwards. §3
gives the mechanism, and predicts the condition recurs whenever cascor is unreachable.

## 5. Driver note (reusable)

**canopy never reaches DOM stability**, because its polling intervals keep a callback in flight
almost continuously (`document.title` sits at `"Updating..."`). Consequently:

- chrome-devtools MCP `click` → *"element did not become interactive within the configured timeout"*;
- Playwright `locator.click()` → *"waiting for element to be visible, enabled and stable"* → timeout;
- untrusted synthetic `MouseEvent` / `PointerEvent` / keyboard dispatch → **ignored**: the widgets are
  **Radix** (`data-state`, `aria-controls="radix-…"`), which does not act on untrusted events, and
  canopy's re-render discards programmatic focus (`document.activeElement` came back empty).

**What works: `locator.click({force: true})`** — trusted CDP input, scrolls and clicks atomically,
skips the stability wait. Coordinate clicking (`page.mouse.click`) is *not* a reliable substitute:
the coordinates go stale between the scroll and the click as the page re-renders.

## 6. Incidental confirmation of the §12 scope, from the live services

`GET /v1/generators` on the isolated juniper-data (installed `[api,equities]`) served **16**
generators, **15 available** (only `mnist`, whose extra was not installed). Canopy's dataset menu in
the same stack rendered exactly **6** options. That is the
`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` §12 gap, observed live rather
than inferred from the registry — and `equities_seq` was **available**, so the compatibility gate
was the only thing blocking it during falsifier A.
