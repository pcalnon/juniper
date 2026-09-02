# HANDOFF 2026-09-02 — canopy E2E: F-039 closed; two of my own fixes were wrong; M-TOPOLOGY half cleared

Continue the juniper-canopy E2E validation arc.

**Read this first.** F-CANOPY-039 is root-caused and FIXED (0/11 → 11/11). That unblocked
M-TOPOLOGY-01..18. But **two fixes this session shipped defects**: canopy#558 replaced an HTTP 500 with a
silent blank canvas (F-041b, fix open as **canopy#561**), and canopy#557 revived a dead 5 s poll that now
feeds the rebuild unsuppressed (**F-CANOPY-043**). Three reviewers over two rounds found ~24 defects in
this document; the corrected claims are what you are reading, and **a third round is owed** (§Validation).

## Authorities and documents (Juniper/AGENTS.md § Cross-Project Conventions)

| role | path (juniper-ml) |
|---|---|
| **ledger** — authority for findings | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` |
| **matrix** — authority for rows | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| consensus procedure | `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` |
| plan (Phase 3/4 gates) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` |

**Tiebreak, and you will need it:** where the matrix and `/tmp/juniper-e2e/seg17_results.json` disagree,
**the JSON is the newer measurement** — re-score the matrix from it, never the reverse.

## Verify your starting state (run from the juniper-ml worktree root)

```bash
git fetch origin && git rev-parse origin/main   # written at 9188535a; assume it moved
python3 util/ad-hoc/e2e_finding_triage.py       # 49 / 27 fixed / 1 accepted / 21 open (1 P0/P1, 5 P1)
python3 util/ad-hoc/e2e_unfilled_rows.py        # 298 verdicted / 0 UNFILLED
gh pr view 561 --repo pcalnon/juniper-canopy --json state   # F-041b fix
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy worktree list | tail -n +2 | wc -l  # 11
```

## Row state: the topo step is UNSTABLE — 5 to 7 PASS depending on the run. The matrix's 9 PASS is STALE, and so is any single run.

**Do not trust a single `--step topo` run, including the matrix's.** Two consecutive runs on an unchanged
stack gave 7 PASS and then **5 PASS**, and the differences are not independent — they **cascade**.

Newest run (`/tmp/juniper-e2e/seg17_results.json`), 5 PASS / 4 FAIL:

| row | evidence | reading |
|---|---|---|
| M-TOPOLOGY-02 | `on_hash == off_hash == 26d0f961`, `back = de463bff` | M-01's layout reset still landing during M-02's reads |
| M-TOPOLOGY-03 | `types=[] n_yaxes=0 plot_area=0` | the weight matrix rendered **nothing** |
| M-TOPOLOGY-04 | `counts 0/0/0/—` vs server `2/40/2/944` | **inherited M-03's empty graph** |
| M-TOPOLOGY-05 | `types=[]` | same empty graph |

**M-03 leaves the graph empty and nothing recovers it**, so -04 and -05 are reading wreckage rather than
failing on their own contracts. And M-03's failure mode VARIES between runs — 41 zero-height traces in
one, zero traces in the next. That variance is **F-CANOPY-040's documented residual**: `-display-mode`
rides as `State`, not `Input`, so switching to Weight Matrix does not trigger the fetch; the store fills
only on the next 5 s tick, and the driver sometimes reads before it. M-03's `wait_for` is still the bare
`any(type == "heatmap")`, so when the store is late the wait burns its full 45 s budget and the step
proceeds against a broken view.

**Consequences for how you work these rows:**
- **Fix the cascade before scoring anything downstream of M-03.** Options: make the raw-topology poll
  trigger on `-display-mode` (an `Input`, not `State`) so the switch fetches immediately; and/or have
  M-03 restore the node-graph view before returning, so a failure there cannot poison -04 and -05.
- **M-02 is a separate, unresolved defect and it is mine.** I added `settle_figure` and it did **not**
  fix it: `settle_figure` settled on a figure that was stable only because the next request had not
  started — **"stable is not ready", one level up.** Done = `on/off/back` are three distinct `fig_hash`es.
- **Re-score the matrix only from a run where -03 renders**, i.e. after canopy#561 lands AND the cascade
  is fixed. Scoring from any run before that records other rows' failures against the wrong finding.

## Do first

1. **Land canopy#561** (F-041b). Verify with
   `python -m pytest src/tests/unit/frontend/test_f037_topology_rebuild_decoupling.py -k every_row_has_real_height -v`
   in the canopy checkout. **Merge only on Paul's explicit approval**, via `python3 util/safe_merge.py`
   (exit 0 ≠ merged — look for the MERGED line). Until it lands the Weight Matrix view is blank on any
   cascade ≥25 units.
2. **Fix M-TOPOLOGY-02's settle** (above). Done = `on/off/back` are three distinct `fig_hash` values.

## Completed this session

- **F-CANOPY-039 FIXED** (canopy#549) — `getUniqueIdentifier` (`dash_renderer.dev.js:1715`) hashes a
  callback's inputs+outputs+state, **not its trigger**, so `:3026` drops the **in-flight** invocation when
  the same identity is re-requested. Fix = tick **Input → State**. *Two caveats reviewers raised and I
  accept: that dedup is Dash's normal design (present in every app) — what was canopy-specific is a 5 s
  poll on a 1.5-31 s callback plus canopy#537's `no_update` short-circuit; and `.dev.js` is the DEV
  bundle, `.min.js` is served outside `debug=True` (same source, so the mechanism holds).*
- **F-CANOPY-040 FIXED** (canopy#557) — the raw-topology poll gated on the 2D/3D toggle. **But see
  F-CANOPY-043**: that fix revived the poll, and it has no identity suppression.
- **F-CANOPY-041 → NOT FIXED**; **F-041b** registered; canopy#561 open.
- **F-CANOPY-042** (P2) — depth label never updates on a slider move. **Fix material already exists:**
  `network_visualizer.py:507` computes a correct server-side `depth_label` and never uses it.
- **F-CANOPY-043** (P2) — see above.
- **M-TOPOLOGY-16 detector FIXED** (canopy#555); **M-TOPOLOGY-01/-06 driver defects fixed** (ml#1556).
- **`juniper-cascor#602`** filed 2026-08-30 *within this multi-day session* (which began 08-30). Two
  reviewers read it as the predecessor's work because the 08-30 handoff — also written by this session —
  already lists it. Noted so you are not surprised by the same inference.

## Remaining work

1. **Nine M-TOPOLOGY rows BLOCKED: 09, 10, 11, 12, 13, 14, 15, 16, 18** — derived from the matrix. None
   has a scorer. The driver's docstring **has been corrected** (it previously advertised `toposel` /
   `w1grow`, which are not in `STEPS`) and now lists exactly what each step scores and which rows have
   none — trust it. **Sizing, which I previously understated:** rows 10-15 drive
   `network-visualizer-graph` by click / box-select / zoom-pan / camera / hover, and
   `util/ad-hoc/e2e_seg17_topology_driver.py` has **no plotly-event idiom at all** (only `set_radio`,
   `set_checklist`, `set_dropdown`, `set_slider`). That is the bulk of the work. M-14 also needs a
   Playwright download intercept; M-15 is a DEAD-EXPECTED negative assertion; M-16 is MANUAL/VIS.
   Register each step in the `STEPS` dict. **Done = each of the nine has a scorer that fails on a known
   bad state**, not merely that it runs.
2. **M-TOPOLOGY-16 needs a fixture with headroom.** The live network is **40/40, saturated**, and M-16
   requires a *unit being added*. **Raise it in place** —
   `PATCH http://127.0.0.1:8202/v1/training/params {"max_hidden_units": 45}` then
   `POST /v1/training/start` **without** `start_fresh`. **Do NOT `POST /v1/network`**: it destroys the
   40-unit fixture that M-03's re-score and the whole 09-01 baseline (2/40/2/944, 1891 traces) depend on.
   Instrument: `util/ad-hoc/e2e_m16_glow_instrument.py` (`apply --checkout <canopy> / report --log /
   revert`) — patch the checkout the **live 8051 leg** runs from, currently the primary.
3. **F-CANOPY-037 is the only finding with the literal `P0/P1` label; FIVE P1s are now open**
   (F-035, F-041, F-041b, F-CASCOR-001, F-CASCOR-002). The plan's Phase 3 entry gate ("Phase 2 P0/P1
   closed", §6.4 of the E2E frontend validation plan) needs all of them. **Do not close F-037** — nine of
   its eighteen rows are still BLOCKED. *(An earlier draft said its blast radius also covers W4-01..17 and
   W1-12..14 "tracked in the plan document". That is false — those ids appear nowhere in the plan; I
   copied the claim from the matrix without opening the file. They exist only in the matrix and ledger.)*
4. **F-CANOPY-035 / -038** concern `metrics-panel-metrics-store`. The ledger has **already adjudicated**
   the apparent contradiction: GLOWPROBE (`metrics_len` 4 and 23) overrules the older "never advances"
   inference. Open only: whether F-035's 79-sample empty reading is scope-limited to that run.
5. **F-039 residual.** The rebuild's three per-tick triggers are `tabpoll-topology` (now State),
   `-topology-store` (identity-suppressed by canopy#542) and **`-raw-topology-store` (NOT suppressed —
   F-CANOPY-043)**. Measured paints are 7.1-31.1 s against a 5 s tick, so the 11/11 growth result shows
   growth on that fixture was slower than the paint, **not** that the starvation class is closed.
6. **F-CASCOR-001** (`juniper-cascor#590`) OPEN upstream.

## Traps

- **`sig` is a byte LENGTH** — use `fig_hash`. **A stable figure is not a READY one** (`settle_figure`
  reports `painted`) — and it can settle on a figure whose next request has not started (M-02, above).
  **A present trace is not a VISIBLE one** — check `plot_area`.
- **Re-reading a widget proves the DOM moved, NOT that Dash received the value.** The depth slider is
  `updatemode="mouseup"`; synthetic idioms run first turn the later drag into a no-op gesture.
- **A wait predicate already true on entry never waits.**
- **Unit tests of a correct handler cannot see a caller that never supplies the value** (F-040 survived
  five passing tests). **And a tautological assert certifies anything** (F-041b survived three checks).
- **`start_fresh: true` discards `max_hidden_units`**; `POST /v1/network` fills unspecified params from the
  REQUEST schema (`correlation_threshold` 0.1, `patience` 5), not the service config (0.01, 50).
- **Symbol deletions need an `Allow-Symbol-Loss:` trailer** — canopy#549 omitted one and turned `main` red.
  *(canopy#560 has since landed the SCREENED-ratchet fix, so canopy's main-verify no longer
  self-perpetuates — an earlier draft said it was still missing.)*
- **`Scheduled Tests` has been red on canopy `main` since 2026-07-21 (~43 days)** — pre-existing.

## Git state and environment

juniper-ml on `worktree-hazy-toasting-abelson`. juniper-canopy / juniper-cascor primaries clean on `main`.
**canopy has ELEVEN non-primary worktrees**: six merged-arc (#549 `f039-tabpoll-input-to-state`, #542
`f039-topology-noop-suppression`, #557 `f040-raw-topology-gate`, #558 `f041-heatmap-spacing`, #555
`m16-cascade-add-glow`, #545 `docs--handoff-word-count`), `f041b-zero-height` (#561, open),
`main-verify-screened-base` (#560, merged), and three July trees that are not this arc's.

**Harvest before removing** — `--harvest DIR` **does exist**:
`python3 util/ad-hoc/2026-08-28_p5_worktree_cleanup.py --pattern 'juniper-canopy--fix--*' --harvest <dest> --execute`
(gates on merged + unoccupied + clean, copies ignored payload out first). *(An earlier draft said no such
flag exists — that is true only of `util/worktree_cleanup.bash`.)* The two F-039 trees hold ~1.2 MB of
census logs.

**All run evidence is in `/tmp/juniper-e2e/`** and `/tmp` is reaped. Copy to
`reports/e2e-canopy-2026-09-02/` **excluding `.venv-data/`**, and **leave the `*.pid` files in place** —
they are one of the orphan reaper's two protection keys.

Stack: data 8101 / cascor 8202 / canopy 8051, plus **8211 = the juniper-deploy stack, not ours**. Bring-up
`util/isolated_stack.bash --up`; the canopy leg is relaunched separately via
`util/ad-hoc/e2e_f039_relaunch_canopy.bash`. **Prefer teardown by pid.** `--down` unconditionally stops
whatever listens on `JUNIPER_E2E_RECURRENCE_PORT` (default 8211) — **F-ML-002, open**. (An earlier draft
called `--down` "safe: zero `.h5` at risk verified"; **no artifact records that verification**.)

Drivers need `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python`. `gh` **2.46.0**:
`gh pr edit` is broken for every flag — use `gh api -X PATCH …/pulls/N -F body=@file`.

## Validation record (consensus procedure §7) — and its own shortfall

- **Instrument**: 3 reviewers × 2 rounds, each able to return "no defects"; none did. ~24 accepted defects.
- **Entry points**: (1) ledger+matrix, deriving the row list mechanically; (2) git/`gh` + live source under
  an opposing brief; (3) the document alone, role-playing a fresh session. Round 2 was told round 1's
  fixes were not above suspicion.
- **Iterations**: 2. Round 1 → ~14 corrections **plus one CRITICAL that changed code** (F-041 not fixed →
  canopy#561). Round 2 → 10 more, of which **two were introduced by round 1's corrections** (the
  `--harvest` denial; the "canopy lacks the SCREENED fix" note) — the documented failure mode of this
  procedure, reproduced exactly.
- **Unresolved dissent**: two reviewers hold that `cascor#602` was the predecessor session's work; I hold
  it was filed within this multi-day session. Recorded unresolved rather than settled by assertion.
- **This review was UNDER-SIZED and the shortfall is not cured.** §3 puts this in the top-right cell
  (a fix hangs on it, it overturns a document of record, single-session sample, many universal
  quantifiers): **3+ Lane A with distinct entry points, 2+ Lane B, ≥2 iterations.** Round 1 ran ≤2 Lane A
  and no true **measurement re-creation** — nobody re-ran `_create_weight_heatmap` in Lane A; the CRITICAL
  came from Lane B. **A third round is owed**, and the convergence argument is weakened by round 1's
  "found by all three" worktree count having itself been wrong (nine, actually eleven).
- **What this evidence cannot support**: that the nine BLOCKED rows are drivable — no scorer exists and
  none has been run. That F-039's starvation class is closed (item 5). That M-02's failure is understood.
  That canopy#561 is correct beyond its unit tests — it has not been driven live.
- **And this document was stale before it was archived.** It first said "9 PASS" (the matrix), was
  corrected to "7 PASS" from a run, and the NEXT run of the same step on an unchanged stack returned
  **5 PASS** with the extra failures **cascading from M-03**. Every row count in this arc is a
  measurement with a timestamp, not a property of the system. **Re-run before you trust one — including
  the one above.**
