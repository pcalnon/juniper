# HANDOFF 2026-08-30 — canopy E2E: the F-039 suppression is MERGED, and the census that would validate it is vacuous unless it drives growth

Continue the juniper-canopy E2E validation arc. **Headline: F-CANOPY-039's trigger mechanism is now
fully explained from source, the suppression fix is merged, and the remaining step — the census — has a
predicted failure mode recorded BEFORE it runs. An idle census will certify this fix green whether or not
the defect survives. Do not run one.**

## Documents

| role | path |
|---|---|
| **the ledger** (authority for dispositions) | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` |
| **the matrix** (rows) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| the review procedure | `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` |
| the plan (§6.4 Phase 3, §6.5 Phase 4, §13 acceptance) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` |
| WS-migration plan (JR-CAN-PERF-004; still owed an update) | `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md` |
| predecessor handoff | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-30_canopy-e2e-f039-response-not-applied.md` |

## Verify your starting state

```bash
python3 util/ad-hoc/e2e_finding_triage.py    # 44 / 25 fixed / 1 accepted / 18 open (2 P0/P1, 3 P1, 13 P2)
python3 util/ad-hoc/e2e_unfilled_rows.py     # 298 verdicted / 0 UNFILLED
ss -ltnp | grep -E ':8101|:8202|:8051|:8211' # expect ONLY 8211 (the deploy container)
```

Merged this session: **canopy#542** (`1b6f4c5`), **ml#1503** (`4965dca7`), **ml#1509** (`d202db3c`).
Filed: **juniper-cascor#602**. Re-derive every line anchor — `main` moves hourly.

## The one thing to read first

**The rebuild gets THREE triggers per poll cycle, and the third one had never been identified.**

```
update_topology_store (dashboard_manager.py)      identical 7,059 B payload every 5 s
   |-> update_network_graph                        [trigger 2: topology-store.data]
   \-> clientside slider-sync (network_visualizer.py:706-738)
          \-> depth-slider.value := unchanged, STILL FIRES
                 \-> update_network_graph          [trigger 3: depth-slider.value]
tabpoll-topology.n_intervals                       [trigger 1]
```

The slider's clientside bounds-sync takes the topology store as its **only** Input and re-emits `value`
unconditionally. So the store's own write manufactures a second consumer trigger.

**Consequence: canopy#537's guard (`network_visualizer.py:447`) requires `len(ctx.triggered) == 1`, which
on a poll cycle is always 3. It is structurally dead — not statistically unlucky.** That retires the
"underpowered census" argument in both directions and explains both prior results:

| trial | measured | why |
|---|---|---|
| #537 alone | 0 of 2 | guard cannot fire; no N would have shown otherwise |
| suppression alone | 0 of 6 | leaves a bare tick, but #537 didn't exist in that build |
| **the pair (now merged)** | **never censused** | suppression leaves a bare tick, #537's guard catches it |

## THE CENSUS IS VACUOUS UNLESS IT DRIVES CASCADE GROWTH — read before running one

**Predicted before the fact, deliberately.** The pair works by stopping the rebuild from *running* on
no-op cycles. At idle it will paint regardless of whether the apply failure survives. And a server-side
`dash.no_update` **does not save a renderer slot** — the round trip already happened — so on a cycle where
the topology genuinely changes, the next bare tick may still retire the in-flight rebuild.

The likely true outcome is therefore **correct at idle, still broken during cascade growth**, which is the
only time the panel matters. An idle census certifies that as FIXED.

`util/ad-hoc/e2e_f037_render_census.py` now defends against this itself:

- `provenance` records HEAD sha / branch / dirty for canopy, cascor and ml — and records the source the
  **stack** ran from (`--canopy-src` / `$CANOPY_SRC_DIR`, else primary), because a fix under test normally
  lives in a worktree while the primary sits on main. No census in this arc ever recorded its build.
- `topology_growth` derives from per-session server truth and **says so, in the artifact and on stdout**,
  when `hidden_units` never moved. A static-topology census is now self-labelling.

So: bring the stack up, **start a training run**, then census at N>=11 with `--canopy-src` pointed at
whatever build you are testing.

## Corrections to the predecessor handoff

- **"Instrument dash-renderer's apply of the 8-output response — never been run" is WRONG.** It has been
  run (`util/ad-hoc/e2e_f039_renderer_apply.py`) and its result is in the ledger: 7 responses, 5,556
  actions, 126 naming the graph, **none carrying the figure**, lifecycle complete with exact itempaths.
  Following that item buys a measurement the ledger already holds.
- **F-CASCOR-002 was P2 in its header and P1 in its own UPGRADE section.** Synchronised to P1 (a
  synchronisation, not a new judgement) and filed as juniper-cascor#602. Triage counts moved accordingly.

## Remaining work

1. **The census** (above). This is the only thing standing between F-CANOPY-039 and a disposition.
2. **M-TOPOLOGY-16 is probably BLOCKED, not owed.** The predecessor named
   `metrics_panel._hidden_unit_addition_markers` as the fix — but that function **already does** a correct
   whole-window scan; it is the model, not the bug. The real last-pair check is
   **`network_visualizer.py:505-509`** (`metrics_data[-2]` vs `[-1]`). *However*, that detection reads
   `metrics-panel-metrics-store` as State, and the ledger records that store's client copy as never
   advancing (`[]` on 79 samples). If that holds, the glow cannot fire whichever scan is used, and a
   whole-window fix would be **correct but unobservable** — inviting the wrong conclusion that the scan
   failed. **Re-measure the metrics store's client copy once** before either fixing or reclassifying.
   That store has TWO writers (`dashboard_manager.py:3878` guarded poll, `:3910` unguarded
   `allow_duplicate` WS append), so a WS-populated copy is possible and source alone cannot settle it.
3. **Two open P1s** plus F-CANOPY-035 (blocked on the metrics-store defect, so M-CANDIDATES-07 is BLOCKED
   not owed) and **F-CASCOR-001** (`juniper-cascor#590`, still OPEN).
4. **42 BLOCKED matrix rows**, unchanged: 16 topology (gated on F-039), 10 dataset (owner decision 4 —
   *surface it, do not drive around it*), 13 needing the V2-snapshot-with-history precondition, 3 others.
5. **P2 wave re-drives** — run-free rows first. For M-PARAMETERS-04/-05/-06 **re-drive the SYMPTOM, not
   the rows**. F-026 and F-036 both need a fresh run — batch them last, together.
6. **JR-CAN-PERF-004 plan update** — §7 item 3 and the Phase 2 blocker (`:189`) still pose the F-036
   server-vs-clientside choice as open; canopy#536 settled it server-side.
7. Plan **§6.4 Phase 3 is BLOCKED** (entry condition "Phase 2 P0/P1 closed"). **§6.5 Phase 4 closeout**
   and **§13 acceptance** remain.

## Traps this session paid for — all new, none in the previous handoff

- **`git merge-base --is-ancestor` is ALWAYS false for a squash-merged branch**, because squashing
  discards the original SHA. It will tell you merged work is unmerged. Verify **content** on main
  instead — `git show origin/main:<path> | grep <symbol>`.
- **A merged branch is auto-deleted, which makes `--force-with-lease` fail with "stale info"** against a
  branch that no longer exists. `git fetch --prune` first, then push fresh.
- **`safe_merge.py` refreshes the base and MOVES THE HEAD.** Never push to a branch while its merge is
  armed. Its `MERGED` line names the pre-merge head, not the squash commit.
- **canopy tests pin source TEXT of function signatures.** `test_phase_b_bridge.py:535` asserted
  `"def update_topology_store(n, ws_topology, active_tab):"` verbatim and broke on an unrelated parameter
  addition. **Grep `tests/` for `def <name>(` before changing any callback signature.** It is repinned on
  its actual subject now (absence of `ws_status` + leading Input order).
- **A targeted local pytest run will NOT catch arity breaks.** canopy CI runs
  `-m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/`;
  five inner-callback call sites broke where a 283-test targeted subset was green. Run CI's selection.
- **CodeQL `py/empty-except` fires on a bare `except: pass` even with a docstring explaining it.** The
  comment must be *in the clause body*. Fix the cause; a `noqa` would have hidden it and still blocked
  the merge.
- Everything in the predecessor's "Standing constraints" still binds — `isolated_stack.bash --down`
  (F-ML-002), the sweep destroying ignored `logs/`, `gh pr view` = MERGED as the removal gate, green
  rollup != mergeable, and reading the WHOLE instrument output.

## Git state

juniper-ml on `worktree-hazy-toasting-abelson`, clean, synced to `origin/main` at `d202db3c`. **No open
PRs in any repo from this session.** juniper-canopy and juniper-cascor primaries clean, on `main`,
up to date. Peer session `p5 memory` (`uds:/run/user/1000/cc-socks/3727200.sock`) confirmed it has
**nothing open in canopy or cascor** — both were formally reclaimed this session.

Worktree `worktrees/juniper-canopy--fix--f039-topology-noop-suppression--20260830-1200--f7e0213e` is
**merged and removable** — harvest any ignored `logs/` before removing it. Three July canopy worktrees
remain and are **not** this arc's to remove.

## Environment

Drivers need `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python` (the conda
activate hooks do not run on direct binary invocation). `JuniperCanopy` does not exist — use
**`JuniperCanopy1`** / **`JuniperCascor1`**. `gh` is **2.46.0**: `gh pr edit` is broken for **every** flag
(use `gh api -X PATCH …/pulls/N -F body=@file`), and `gh pr checks --json` does not exist. No
`util/ad-hoc/` script carries an execute bit — invoke via `python3`.
