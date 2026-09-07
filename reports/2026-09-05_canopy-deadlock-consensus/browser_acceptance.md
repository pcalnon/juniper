# Browser acceptance — the selection traversal, observed

**Date**: 2026-09-05
**Subject**: juniper-canopy `main` @ `aa61156` (i.e. after canopy#592 and #593)
**Acceptance step for**: `JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`
§10 OQ-N5 — *"Re-run this falsifier as an acceptance step for PR 3 — the traversal in §4.1 is so
far established only by executing handlers, never in a DOM."*

**Result: the traversal completes. `(recurrence, equities_seq)` is reachable in a live browser.**

---

## 1. Stack

Isolated trio + recurrence, on a port set colliding with nothing:

| service | port | note |
|---|---|---|
| juniper-data | 8105 | installed with `[api,equities]`, so `yfinance` is present |
| juniper-cascor | 8206 | |
| **juniper-recurrence** | **8215** | `--with-recurrence`; canopy given `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` |
| juniper-canopy | 8055 | service mode, `JUNIPER_CANOPY_DEMO_MODE=0` |

Brought up with `util/isolated_stack.bash --up --with-recurrence` and `JUNIPER_E2E_RUN_DIR=/tmp/juniper-e2e-catch22`.

**Two other stacks were live throughout and were not touched**: the operator's on-host stack
(canopy 8050, cascor 8201) and a concurrent session's isolated stack (8051 / 8101 / 8202 / 8211).
The default isolated ports were **already occupied**, which is why a distinct set was chosen rather
than the documented default. Verified after teardown: 8055/8105/8206/8215 free, the other six still
listening.

Because the recurrence service is genuinely wired here, `backend == "recurrence"` after the swap —
so this run exercises the **honest** branch of canopy#592's predicate, not the X1 branch.

## 2. Method

Per `reference_canopy_browser_driving_force_click`: canopy never reaches DOM stability
(`document.title` sat at `"Updating..."` throughout, confirmed), so every default click path times
out. All clicks were `page.locator(sel).click({force: true})` — trusted CDP input.

**One obstacle not in the prior record**: a first-run **"Welcome to Juniper Canopy"** modal covers
the sidebar. `force: true` skips the hit-test, so the first ✕ click silently landed on the modal's
`<ol>` instead and appeared to do nothing. Diagnosed with `document.elementFromPoint` on the ✕'s own
centre, which returned `OL` inside `.modal-body`. Dismissed via `#welcome-modal-close`, after which
`elementFromPoint` resolved inside `.dash-dropdown-clear`.

**Carry this forward: a `force: true` click that "does nothing" is not evidence the control is
inert — hit-test the target's centre first.** This is the same shape as the 09-02 finding that the
environmental blocker (X7) was itself a defect.

## 3. Observations

### 3.1 The ✕ exists in the rendered DOM

```html
<a class="dash-dropdown-clear" title="Clear selection" aria-label="Clear selection">
```

Under `clearable=False` this element is not rendered at all. Its presence is the shipped fix,
observed rather than inferred. It also carries `aria-label`, so unlike the greyed dataset *option*
(Y7: no `aria-disabled`) this affordance is exposed to assistive technology.

### 3.2 The traversal

| step | gesture | model | dataset | Start | Apply |
|---|---|---|---|---|---|
| mount | — | Active: CasCor (Cascade-Correlation) | `Spirals` | enabled | enabled |
| 1 | click ✕ | Active: CasCor | **`""`** (`⊥`) | **DISABLED** | **DISABLED** |
| 2 | open model table | — | `⊥` | — | — |
| 3 | click `Select` on Recurrence | **Active: Recurrence (LMU)** | `⊥` → snapping | disabled | disabled |
| 4 | gate settles | Active: Recurrence (LMU) | **`Equities (sequence)`** | **enabled** | **enabled** |

At step 2 the model table reported:

```
CasCor (Cascade-Correlation) | feedforward    | live | ✓ compatible | Selected (enabled)
Recurrence (LMU)             | ts established | live | ✓ compatible | Select   (ENABLED)
```

On 2026-09-02 the same click was proven inert — the button was `disabled` and clicking the greyed
dataset option changed nothing. **That is the deadlock, and it is gone.**

### 3.3 Both new gates fire in the real UI

Step 1 is the X5 / N9 evidence: at `⊥`, `start-button.disabled === true` and
`apply-dataset-button.disabled === true`, recovering to `false` at step 4 once the selection is
complete again. The ✕ itself also disappears at `⊥` (nothing left to clear) and returns at step 4.

## 4. A measurement error worth recording

The step-3 probe read `datasetValue: ""` at 4000 ms and was written up in-session as "the dataset
did not snap". It had. A later read returned `"Equities (sequence)"`; the gate callback simply had
not completed inside the poll window, on a page whose callbacks are continuously in flight.

**The instrument was too fast, and a null reading was briefly mistaken for a null result.** Same
class as `reference_vacuous_pass_check_class`: the probe was correct and its enumeration of "settled"
was not. Any future timing-sensitive assertion on this UI should poll for the expected value with a
deadline rather than sample once after a fixed sleep.

## 5. Still open, and now observed rather than inferred

- **Y9 is real and visible.** At `⊥` the model table renders `✓ compatible` for **both** models — a
  positive falsehood, not merely a missing reason. Scheduled for §4.3 in PR B.
- Nothing here exercises the `⊥`-**model** state (§4.11 has not shipped) or the empty
  compatible∩available set (§4.7), since `equities_seq` was available in this stack — all 16
  generators reported `available: true` with the `equities` extra installed.
- No training run was started, so this says nothing about whether the LMU can actually train on
  `equities_seq` end-to-end (§12.4's unvalidated-capability caveat stands).
