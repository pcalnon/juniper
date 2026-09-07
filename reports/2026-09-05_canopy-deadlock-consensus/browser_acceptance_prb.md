# Browser acceptance — PR B (both axes clear, empty-set recovery, notices)

**Date**: 2026-09-07
**Subject**: juniper-canopy `main` @ `f8fb4a2` (after canopy#594, #595, #596)
**Follows**: `browser_acceptance.md` (PR A — the dataset ✕ traversal, 2026-09-05)

**Result: three of the four new behaviours observed. The fourth is not interactively reachable,
and that is itself a finding.**

---

## 1. Two stacks, because availability is a bring-up parameter

Both runs used an isolated trio plus the recurrence service on 8105 / 8206 / 8215 / 8055 — a port
set chosen off the documented default because a concurrent session's stack holds those. The
operator's stack and that session's stack were verified untouched after each teardown (6 ports
still listening).

| run | `JUNIPER_E2E_DATA_EXTRAS` | `equities_seq` | exercises |
|---|---|---|---|
| **A** | `api,equities` | available | the model-clear cut vertex, ungating, Y9 |
| **B** | `api` | **unavailable** | the empty compatible ∩ available set (§4.7) |

Run B is the **deployed container's real configuration** — `yfinance` is absent from juniper-data's
lockfile, so the LMU genuinely has zero available datasets there (§9). The empty-set state was
tested in the condition that actually produces it, not a synthetic one.

**A trap caught before it produced a false result**: the first bring-up served canopy from the main
checkout, which was still at `aa61156` — *pre*-PR B. The stack was healthy and the dashboard
loaded, so nothing looked wrong. Caught by grepping the served source for `model-selection-clear`
(count: 0) before driving anything. **A checkout is not a deployment**; verify the code under test
is the code being served.

## 2. Run A — the model clear is a second, independent cut vertex

At the mount state `(cascor, spirals)` the model modal renders the new control, labelled
**"Clear model — show all datasets"**, and the table reads:

```
CasCor (Cascade-Correlation) | feedforward    | live | ✓ compatible   | Selected (enabled)
Recurrence (LMU)             | ts established | live | needs 3-D data | Select   (DISABLED)
```

Clicking **Clear model**:

| observed | |
|---|---|
| sidebar summary | `No model selected — all datasets shown; choose one to train` |
| dataset | **kept** at `Spirals` — §5.6's dataset-primary policy |
| dataset options | all six offered, **`Equities (sequence)` enabled**; MNIST greyed with its availability reason |
| Start | **disabled** |
| modal | closed |

Then, without ever touching the dataset ✕:

```text
(⊥model, Spirals) --pick Equities (sequence) from the ungated list--> (⊥model, equities_seq)
                  --Select Recurrence (now ENABLED)--> (Recurrence (LMU), Equities (sequence))
                                                        Start ENABLED, Apply ENABLED
```

At `equities_seq` the table correctly inverts: `CasCor — needs 2-D data (DISABLED)`,
`Recurrence — ✓ compatible (enabled)`.

**This is the second cut vertex, observed.** G2 was rewritten during PR B because it asserted the
dataset ✕ was the only exit; this run is that rewrite confirmed in a DOM.

`/api/stream_health` reported `mode: "recurrence"` afterwards, so the **backend really swapped** —
the sidebar's "Active:" is honest here, not merely a label (canopy#592's predicate on its true
branch).

## 3. Run B — the empty compatible ∩ available set

With the `equities` extra absent, `/api/dataset/generators` reports
`equities_seq: {available: false, install_hint: 'The "equities" extra is required…'}`.

Clearing the dataset to `⊥` and selecting Recurrence (enabled at `⊥`) produces:

> **No dataset is available for Recurrence (LMU).** Every dataset compatible with this model is
> unavailable in this deployment — usually a missing optional data extra in juniper-data. Install
> it, or choose a different model.

| property | observed |
|---|---|
| container | `role="status"`, `aria-live="polite"` |
| rendering | `.alert.alert-warning`, **no `duration`** — persistent, per N12 |
| dataset | held at `⊥` (not parked on a disabled option, which is what shipped before) |
| Start / Apply | **both disabled** |

That is §4.7 + N8 + N12's persistent channel, end to end, in the configuration §9 describes.

## 4. The repair notice is not interactively reachable — a finding, not a gap in testing

The transient notice (D5's, §4.3) fires when the gate **moves** the dataset: the current value is
not in the enabled set and the enabled set is non-empty. Attempting to trigger it through the model
table failed, and the reason is structural:

> **The model table enables a model's Select only when that model is compatible with the current
> dataset — in which case no snap is needed.** When a snap *would* be needed, the Select is
> disabled, so the transition cannot be made from there.

So the snap is a **safety net for the non-interactive paths**, not an ordinary interaction: the
mount-time gate pass (`params-init-interval`), and an availability change under a live session. Its
rendering is covered at handler level (`TestDatasetRepairNotice`, four cases including that it
auto-dismisses and that it clears when the gate changes nothing), but it was **not observed in a
DOM** and this document does not claim otherwise.

Worth recording for whoever revisits §4.3: the notice's value is highest exactly where it is hardest
to trigger by hand — a dataset silently swapped at mount, or out from under a running session.

## 5. Not observed

- **G9's demo badge.** The isolated stack runs canopy in service mode
  (`JUNIPER_CANOPY_DEMO_MODE=0`), so the demo branch never renders. The wire field was confirmed
  live (`/api/stream_health` → `dataset_source: None` for a non-demo backend, which is the
  "not this field's business" case); the badge branch itself is pinned by source inspection, on the
  same reasoning as the F-CANOPY-042 bounds-sync suite.
- **No training run was started**, so nothing here says whether the LMU can actually train on
  `equities_seq`. §12.4's unvalidated-capability caveat stands.
- **G1c's three-component registry** is synthetic by construction and has no DOM at all.

## 6. Method note — the same instrument error, three times

Three separate probes in this session read a value **before the callback settled** and briefly
reported the opposite of the truth: the dataset "did not snap" (PR A), Start "was not disabled" at
a cleared model, and the model modal "did not open". Each was a single sample after a fixed
`waitForTimeout`.

Canopy's callbacks are continuously in flight (`document.title` sits at `"Updating..."`), so a
fixed sleep is not a synchronisation primitive here. **Poll for the expected value with a deadline**
— every assertion in runs A and B that mattered was taken from a polling loop, and the two that
were not are the two that were initially wrong.
