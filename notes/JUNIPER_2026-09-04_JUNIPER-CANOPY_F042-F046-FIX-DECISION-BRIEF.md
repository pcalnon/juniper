# F-CANOPY-042 and F-CANOPY-046 — fix decision brief

**Project**: Juniper — juniper-canopy
**Author**: Paul Calnon
**Date**: 2026-09-04
**Status**: **DECIDED 2026-09-04** — all six decision points closed by the owner; this is now the
design-of-record for both fixes. Decisions are recorded verbatim in
[§ Decisions taken](#decisions-taken-2026-09-04) at the foot of this document; the options analysis
above is preserved unchanged so the *rejected* alternatives and their costs remain legible.

---

## Why this brief exists

Both findings were registered in
[`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`](JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md)
with **fix direction deliberately not asserted**, because both touch the callback family this arc has
repeatedly starved (F-CANOPY-037 / -039 / -043) and a casual fix adds a trigger to a 1.5–31 s rebuild.

Reading the code to write this up turned up **two things the ledger does not record**:

1. **F-CANOPY-042 is two defects, not one.** The label does not follow the slider (the registered
   finding) *and* the label's zero-semantics disagree with the filter's. The second is wrong **right
   now, at rest**, with no user action at all.
2. **F-CANOPY-046 has an independent latent cost** — the clear path writes `[]` unconditionally, so it
   triggers a full rebuild even when nothing was selected. That is worth fixing whichever option is
   chosen, and is not part of any of them.

All line numbers are `src/frontend/components/network_visualizer.py` at canopy `af39083`+ unless noted.

---

## F-CANOPY-042 — the depth-filter label

### What the user sees

Drag the depth slider to 20 on a 40-unit cascade. The filter **works**: the figure re-renders
(`de463bff` → `ab8c6d50`, 1891 → 551 traces) and the stats bar updates (`hidden` `40` → `20 of 40`,
`conn` `944` → `274`). **The label beside the slider stays `"0 of 40"`.**

### Defect A — the label is wired to the wrong thing

The label is an Output of the **clientside slider-bounds sync** (`:755-789`), whose only Input is
`-topology-store`. The slider's value rides there as **State**.

```
Outputs: -depth-slider.max, -depth-slider.value, -depth-slider-container.style, -depth-label.children
Input  : -topology-store.data
State  : -depth-slider.value
```

So the label recomputes when the **topology** changes, never when the user moves the slider. And since
canopy#542 identity-suppressed `-topology-store`, at idle it never changes at all — the label is frozen
at whatever the last topology write produced.

### Defect B — `0` means two different things (NEW, and live at rest)

| consumer | rule | at `value=0`, `n_hidden=40` |
|---|---|---|
| filter (`_apply_hierarchy_filter`, `:801`) | `depth is None or depth <= 0 or depth >= total` → **no filter**, label `"all"` | shows **all 40** |
| label (clientside, `:772`) | `(v === nHidden) ? "all" : v + " of " + nHidden` | renders **`"0 of 40"`** |

The slider ships `min=0, max=0, value=0` (`:178-188`) and the label's static default is `"all"`
(`:174`). So on a loaded 40-unit network the control reads **"0 of 40" while all 40 units are
displayed** — the label is wrong before anyone touches it.

**Fixing Defect A alone does not fix this.** Making the label follow the slider would still render
`"0 of 40"` at rest. Whatever wiring is chosen, the zero-semantics have to be settled too.

### Constraint 1 — the obvious fix is structurally unavailable

"Add `Input(-depth-slider, 'value')` to the existing clientside callback" **cannot be done**: that
callback already *Outputs* `-depth-slider.value`. Same component-property as both Input and Output is a
circular dependency and Dash rejects it at registration. Any fix must either split the label out of that
callback or source it elsewhere.

### Constraint 2 — the server already computes the right label and discards it

`_apply_hierarchy_filter` returns `(filtered_topology, depth_label)` with exactly the wanted format.
The rebuild calls it at `:507`:

```python
topology_data, depth_label = self._apply_hierarchy_filter(topology_data, depth_filter, n_hidden_total)
```

and **`depth_label` is never referenced again** (grep past `:507` finds only the docstring). The rebuild
*does* take `-depth-slider.value` as an Input (`:350`), so routing the label through it would track the
slider correctly and automatically agree with the filter — same function, one value.

The costs are real:

- the rebuild is the **starvation-prone** callback (1.5–31 s measured; F-037/-039/-043). The label
  would lag the graph by the full paint time, so the number under the user's thumb updates seconds
  after the drag;
- it has **four return paths** (two empty-figure, two full-figure). A ninth Output must be added to
  every one, and the two empty-figure paths have no meaningful label to give;
- it couples a trivial text readout to the heaviest callback in the app.

### Options

| # | Option | Tracks slider | Agrees with filter | New rebuild triggers | Notes |
|---|---|---|---|---|---|
| **A1** | Split the label into its own **clientside** callback: `Input(-depth-slider.value)` + `Input(-topology-store)`, Output label only | yes, instant | only if the rule is duplicated correctly | none | no cycle (it outputs no slider prop); label logic then exists in two places unless the old one drops it |
| **A2** | Add `-depth-label.children` as a **ninth Output of the rebuild**, using the already-computed `depth_label` | yes | **by construction** — same function | none (already an Input) | label lags 1.5–31 s; touch all 4 return paths |
| **A3** | Both: clientside for instant feedback, server value as the authority | yes, instant | yes | none | two writers to one Output → needs `allow_duplicate`; last-writer-wins flicker |
| **A4** | Leave the wiring; only fix the zero-semantics | no | partially | none | label still frozen after a drag — does not close the finding |

**Recommendation: A1**, with the zero-rule taken from the server's definition so the two agree by
inspection. A2 is more obviously correct but puts a text label behind a 31 s paint, which is the wrong
trade for a readout whose entire purpose is immediate feedback.

### Decision points

> **D1 — wiring.** A1 (own clientside callback), A2 (rebuild Output), A3 (both), or A4 (semantics only)?
>
> **D2 — what does `0` mean?** Three coherent answers:
> - **(a) `0` = "all"** — matches the filter as written; label renders `"all"` at 0. Slider then has two
>   values meaning "all" (`0` and `max`), which is redundant but harmless.
> - **(b) `min=1`** — `0` becomes unreachable; `1..N`, with `N` = all. Cleanest semantics; changes the
>   control's range and any saved value of 0 snaps to 1.
> - **(c) `0` = "none"** — make the *filter* honour it (show zero hidden units). Truthful to the label
>   but produces a deliberately empty-looking graph, and changes filter behaviour, not just a label.
>
> **D3 — scope.** Fix both defects in one PR, or land the wiring fix (A) and the semantics fix (D2)
> separately? They are independent, and B is visible at rest while A needs a drag to see.

---

## F-CANOPY-046 — clearing the selection

### What the user sees

The panel says **"(Click again or elsewhere to deselect)"** (`:719`) and, for box select,
**"(Click elsewhere to deselect)"** (`:667`). Clicking elsewhere does nothing.

### The mechanism, measured

`handle_node_selection`'s only click Input is `-graph.clickData`, and **plotly emits `plotly_click`
only when a POINT is hit**. A click on empty canvas produces no event at all, so `clickData` never
changes, the callback (`prevent_initial_call=True`) never runs, and the selection stands.

```
M-TOPOLOGY-12 click empty space: cleared=False plotly_click_events=0 -> FAIL
```

Two consecutive runs. `plotly_click_events=0` is the finding: **not** "the handler ran and failed to
clear" but "there was no event to clear on". The handler is fine.

**What does work:** clicking an already-selected node toggles it, and that path returns `[]` — clearing
the *whole* selection, including a multi-node box selection. So the feature is reachable; it is the
*"or elsewhere"* half of the app's own instruction that is not.

### Independent of the option chosen — the unconditional write

The clear path (`:98` within the callback) is:

```python
return [], [], hidden_style
```

It writes `[]` **whether or not anything was selected**. `-selected-nodes` is an `Input` of the topology
rebuild (`:352`), so every such write triggers a 1.5–31 s rebuild. Any option below that makes empty
clicks reach this callback turns each stray click on the canvas into a full repaint.

**This should return `dash.no_update` when the selection is already empty, regardless of which option is
chosen.** It is a one-line guard and it is the difference between "clearing costs a rebuild" (correct —
the highlight must be redrawn) and "*not* clearing costs a rebuild" (pure waste). Listed as D6 so it is
decided explicitly rather than smuggled in.

### Options

| # | Option | Clears on empty click | New triggers on the rebuild path | Risk |
|---|---|---|---|---|
| **B1** | **Make the text honest** — "(Click again to deselect)" in both places | no | none | zero risk; closes the *mismatch*, not the *gesture*. The promise disappears rather than being kept |
| **B2** | **Add a "Clear selection" button** | n/a — explicit control | one Input (`n_clicks`); one rebuild per clear, which is correct work | discoverable, unambiguous; adds UI |
| **B3** | **Clientside listener on the graph div**, writing a store that feeds the callback | yes | one Input; needs the D6 guard or every stray click repaints | discriminating "empty" from "on a point" is doable via `event.target.closest('.points')`, but it is a second event path racing plotly's own |
| **B4** | **Clear on `relayoutData` autorange** (double-click) | only on double-click | one Input, and it fires on every zoom/pan | conflates "reset view" with "clear selection"; likely to clear selections the user wanted to keep |
| **B5** | **Accept and document** — leave text and behaviour as-is | no | none | the app keeps telling the user to do something that does nothing |

**Recommendation: B1 + B2.** B1 stops the app promising a gesture it does not implement (and is
independently correct whatever else happens); B2 supplies a real, discoverable way to clear that does
not depend on plotly emitting an event it does not emit. B3 is the only option that literally satisfies
the original text, and it is the one most likely to reintroduce a starvation-class defect.

### Decision points

> **D4 — behaviour.** B1, B2, B3, B4, B5, or a combination? (B1 composes with any of B2/B3/B4.)
>
> **D5 — if the text changes, what should it say?** The click branch has a working alternative
> ("Click again to deselect"). The box-select branch's only working gesture is "click any selected
> node", which is awkward to phrase — candidates: *"(Click a selected node to clear)"*, or drop the
> hint from the box branch entirely if B2 lands and the button carries the affordance.
>
> **D6 — the unconditional `[]` write.** Add the `dash.no_update`-when-already-empty guard? (Recommended
> yes, independent of D4. Note it changes a currently-unconditional Output write, so any test asserting
> "clear always returns `[]`" would need updating — none exists today.)

---

## Summary of decision points

| ID | Finding | Question | Recommendation |
|---|---|---|---|
| **D1** | F-042 | Label wiring: A1 own clientside / A2 rebuild Output / A3 both / A4 none | **A1** |
| **D2** | F-042 | Meaning of `0`: (a) all / (b) `min=1` / (c) none | **(a)** — matches the filter as written |
| **D3** | F-042 | One PR or split wiring from semantics | **One PR** — same control, same test |
| **D4** | F-046 | Behaviour: B1 text / B2 button / B3 clientside / B4 relayout / B5 accept | **B1 + B2** |
| **D5** | F-046 | Replacement hint text, incl. the box-select branch | see D5 candidates |
| **D6** | F-046 | Guard the unconditional `[]` write | **Yes**, independent of D4 |

**Verification available for all of the above.** `util/ad-hoc/e2e_seg17_topology_driver.py` (juniper-ml)
scores M-TOPOLOGY-06/-07 (`--step topo`) and M-TOPOLOGY-12 (`--step topoevents`) against the live stack,
and M-TOPOLOGY-12 already reports `plotly_click_events` so a fix can be shown to work *and* shown to
work for the right reason. Note that M-TOPOLOGY-06's predicate is
`label == want OR counts["hidden"] == want` and currently passes on the counts branch — **it does not
cover the label**, which is why F-042 was invisible until the slider could be driven. Tightening that
predicate belongs with whichever option D1 selects.

---

## Decisions taken (2026-09-04)

Closed interactively by the owner against the options above.

| ID | Decision | Chosen | Rejected, and why it matters |
|---|---|---|---|
| **D1** | Label wiring | **A1** — the label gets its **own clientside callback** (`Input` on `-depth-slider.value` **and** `-topology-store.data`; Output the label only). The existing bounds-sync callback **drops** its label Output, which is what removes the cycle. | A2 would have put a text readout behind a 1.5–31 s paint; A3's two writers to one Output invite flicker; A4 does not close the finding. |
| **D2** | Meaning of `0` | **(a) `0` = "all"** — the label renders `"all"` at `0`, matching `_apply_hierarchy_filter`'s `depth <= 0` guard. **No filter behaviour changes.** | (b) `min=1` changes the control's range and makes "show zero units" unexpressible; (c) would make the *default* slider position render a near-empty graph. |
| **D3** | Packaging | **Two PRs, one per finding.** | One PR would interleave the falsification evidence for two unrelated defects and make a revert take both. |
| **D4** | Clear behaviour | **B1 + B2** — make the hint text honest **and** add a "Clear selection" button. | B3 (clientside listener) literally satisfies the old text but races plotly's own event path and is the option most likely to reintroduce a starvation defect; B4 conflates "reset view" with "clear selection"; B5 leaves the app promising a dead gesture. |
| **D5** | Hint text | Click branch keeps **`"(Click again to deselect)"`**; the box/lasso branch **drops its hint entirely** — the visible button carries the affordance. | Phrasing "click a selected node to clear" is accurate but users will not act on it; pointing both branches at the button discards a gesture that does work. |
| **D6** | No-op guard | **Yes** — return `dash.no_update` when the selection is already empty. | Leaving it makes *failing* to clear cost a full 1.5–31 s repaint, which is exactly the F-CANOPY-037/-039/-043 waste class. |

### What this means concretely

**F-CANOPY-042 (PR 1)** — `src/frontend/components/network_visualizer.py`:

1. new `app.clientside_callback` owning **only** `-depth-label.children`, triggered by
   `-depth-slider.value` and `-topology-store.data`;
2. the existing bounds-sync callback loses its label Output and returns a 3-tuple;
3. label rule: `"all"` when `v === 0 || v === nHidden`, else `v + " of " + nHidden` — the `v === 0` arm
   is D2, and is what makes the control correct **at rest**, not merely after a drag.

**F-CANOPY-046 (PR 2)** — same file:

1. click-branch hint → `"(Click again to deselect)"`; box-branch hint removed;
2. a "Clear selection" control wired as a new `Input` to `handle_node_selection`;
3. the clear path returns `dash.no_update` when `current_selection` is already empty (D6).

### Verification owed by each PR

Both are drivable against the live stack, and **each must be falsified against its own parent**, not
merely shown green — the standard this arc has been holding:

- **F-042**: `util/ad-hoc/e2e_seg17_topology_driver.py --step topo` (juniper-ml) scores M-TOPOLOGY-06
  and -07. **M-TOPOLOGY-06's predicate is `label == want OR counts["hidden"] == want` and currently
  passes on the counts branch — it does not cover the label at all.** Tightening it to require the label
  belongs with this PR, otherwise the row would go green without testing the thing that was fixed.
- **F-046**: `--step topoevents` scores M-TOPOLOGY-12 and already reports `plotly_click_events`, so the
  fix can be shown to work *and* shown to work for the right reason. The row's current FAIL carries
  `plotly_click_events=0`; after B2 the clearing path is a button, so M-TOPOLOGY-12's contract itself
  needs restating — "clicking empty space clears" is a gesture the app will no longer claim.
