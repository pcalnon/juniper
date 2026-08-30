# HANDOFF 2026-08-30 — canopy E2E: F-039 is a RESPONSE-APPLY failure; the census that shaped the arc was invalid

Continue the juniper-canopy E2E validation arc. **Headline: F-CANOPY-039's premise was overturned by
direct instrumentation — the rebuild receives a correct 7,059 B topology and computes a real figure
7 of 8 invocations, and the DOM keeps the mount-time render. The response is never applied. Separately,
the census that condemned the leading candidate fix was re-read under a formal consensus procedure and
cannot support the conclusion drawn from it.** The stack is DOWN and the 17-hour fixture is GONE —
re-establishing it is the first cost of any live work below.

## Documents

| role | path |
|---|---|
| **the ledger** (authority for dispositions) | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` |
| **the matrix** (rows) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| **the review procedure** (new; governs the work below) | `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` |
| the plan (§6.4 Phase 3, §6.5 Phase 4, §13 acceptance) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` |
| WS-migration plan (JR-CAN-PERF-004; owed an update) | `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md` |
| predecessor handoff | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-29_canopy-e2e-f039-store-write-and-p2-tail.md` |

## Verify your starting state

```bash
python3 util/ad-hoc/e2e_finding_triage.py    # 43 / 25 fixed / 1 accepted / 17 open (2 P0/P1)
python3 util/ad-hoc/e2e_unfilled_rows.py     # 298 verdicted / 0 UNFILLED
ss -ltnp | grep -E ':8101|:8202|:8051|:8211' # expect ONLY 8211 (the deploy container)
```

Nine PRs merged in the previous session (ml#1444, #1471, #1480, #1482, #1485, #1487, #1495;
canopy#537). Re-derive every line anchor and every head — `main` moves hourly.

## The one thing to read first

**F-CANOPY-039 is not "the store is empty". The rebuild's RESPONSE IS NEVER APPLIED.**

Direct instrumentation of `update_network_graph`, live, while the failure reproduced
(`traces=0`, counts `0/0/0/0`, 3/3 samples):

```
8 invocations
 1 x  td_len=75    input_units=0  takes_empty_path=True    <- mount only
 7 x  td_len=7059  input_units=2  takes_empty_path=False   <- every tick after
```

Every populated invocation's trigger list:
`['tabpoll-topology.n_intervals', 'network-visualizer-topology-store.data',
'network-visualizer-depth-slider.value']`.

The poll rewrites an **identical** 7,059 B payload every 5 s, Dash fires consumers on any write, so the
store re-triggers the rebuild continuously and it is **never a bare tick** — which is why canopy#537's
short-circuit correctly does not fire. Tools: `util/ad-hoc/e2e_f039_rebuild_instrument.py`
(apply/report/revert), `e2e_f039_render_state.py`, `e2e_f039_duplicate_store_probe.py`.

**Ruled out by measurement, do not re-run:** duplicate store instance (1 occurrence of every id on all
three tabs, with three control ids to catch a self-measuring probe); duplicate/detached graph element;
hidden pane; plotly uninitialised; `RESET_COMPONENT_STATE`.

**The metrics store is a different defect.** Its client copy never advances at all — `[]` on all 79
samples while the server offers 155,392 B. That killed F-038's hypothesis (i) and explains F-035, whose
INCONCLUSIVE disposition is superseded. Topology's copy *converges*; metrics' never does. **Do not
unify them.**

## The census re-read, and why it constrains what you may conclude

Run under the consensus procedure: 3 measurement agents (entry points: ledger / git+PR history / raw
evidence tree), 2 adversarial agents (opposing briefs), all load-bearing single-sourced claims
re-derived by the reconciler. Full record in the ledger.

- **"0 of 1" is not a census** — one session, which bypassed `e2e_f037_render_census.py` entirely. That
  tool's header says a fix **"CANNOT be validated by one session"**; `DEFAULT_SESSIONS = 11`.
- **The stated rationale is false** — canopy#537 says *"its comparison can never fire while `current` is
  always the empty default"*; the cited log is **11 `eq=True` in 15 samples**.
- **The suppression's source was never staged** — no branch, commit, stash, dangling or loose object.
  Reinstating is a rewrite, so its next measurement is not comparable to the 0-of-1.
- **The pair the mechanism predicts has never been run** — the short-circuit branch never touches
  `dashboard_manager.py`, and the primary sat at `27af847` throughout the suppression's window.
- **Two arguments that look decisive and are not.** (a) `depth-slider.max` reads 10 against a default of
  0 in all ten failing sessions, so the store write reaches the client — but its writer is
  `app.clientside_callback` (`network_visualizer.py:706`), in-browser, while the rebuild is
  `@app.callback` (`:332`) at 1.5-5 s. A fast clientside consumer landing while a slow server consumer
  does not is *what supersession predicts*. (b) "The census was underpowered" is weaker than it looks:
  P(0|no effect)≈82% at n=1 assumes a stochastic null at p=2/11, but the regime is **0 of 6 with
  identical deterministic signatures**, and the 2/11 baseline **has no artifact at all**.

**Net: supersession is NOT refuted and NOT confirmed. Do not reinstate on the strength of the census
re-read alone** — that would be subtracting a refutation rather than adding a confirmation, which this
arc has already paid for three times.

## Remaining work

1. **The owed experiment, and it is specific.** Rewrite the suppression — five edit sites:
   `dashboard_manager.py:3924` add `State("network-visualizer-topology-store","data")`, `:3959`/`:3966`
   thread it as `current=`, `:6797` extend `_update_topology_store_handler`'s signature, `:6829` add the
   guard before `return topology`. Run it **together with canopy#537's short-circuit** (the untested
   pair) at **N >= 11**, and **record the canopy commit in the census artifact** — no census in this arc
   ever has, which is why provenance had to be reconstructed from leg logs.
2. **The alternative that fits the same evidence.** A pure dash-renderer apply failure explains
   "computed correctly, never applied" without supersession. The only manipulation that discriminates
   them (disabling `tabpoll-topology`, traces 0 -> 181) is itself n=1. **Instrument dash-renderer's
   application of the 8-output response** — the ledger localised there and it has never been run.
   Prefer this to (1) if you can only do one: it is diagnostic rather than confirmatory.
3. **canopy#537 shipped and does NOT fix F-039** (census 0 of 2 on a leg built from it, with the caveats
   above). It fixed a real dead guard. **F-CANOPY-037's deferred regression stands**: new-unit detection
   is a last-pair check, so **M-TOPOLOGY-16 (cascade-add glow) is flaky by design** — named fix is
   `metrics_panel._hidden_unit_addition_markers`' whole-window scan (`metrics_panel.py:1999-2003`) with
   dedupe.
4. **Two open P1s**: F-CANOPY-035 (now explained — its fix is blocked on the metrics-store defect, so
   M-CANDIDATES-07 is BLOCKED not owed) and **F-CASCOR-001** (`juniper-cascor#590`, still OPEN).
   **F-CASCOR-002 still needs filing upstream.**
5. **42 BLOCKED matrix rows**, all owned: 16 (item 1/2 — M-TOPOLOGY-01..06, -09..18; **-07 PASS, -08
   FAIL**), 10 (M-DATASET-17..26, gated on owner decision 4 — *surface it, do not drive around it*),
   13 (M-METRICS-11..16/-18/-27, M-CANDIDATES-10/-11, M-EVOLUTION-07, M-BOUNDARIES-07, M-DATASET-03 —
   need the V2-snapshot-with-history precondition), 3 (C2.10-03, M-SNAPSHOTS-20/-21).
6. **P2 wave re-drives** — run-free rows first (C2.9-05, M-PARAMETERS-04/-05/-06, M-METRICS-03,
   M-WORKERS-02, C2.1-01/02, Network Editor patch rows). For M-PARAMETERS-04/-05/-06 **re-drive the
   SYMPTOM, not the rows** (they already PASS on their stated expectations; F-028's repro was never
   reproduced from source). F-026 (mid-run `phase_started_at`) and F-036 (Candidate Metrics tab open)
   both need a fresh run — batch them last, together.
7. **JR-CAN-PERF-004 plan update** — §7 item 3 and the Phase 2 blocker (`:189`) still pose the F-036
   server-vs-clientside choice as open; canopy#536 settled it server-side. The "must not run
   concurrently with F-036" constraint still binds.
8. Plan **§6.4 Phase 3 is BLOCKED**, not owed — entry condition is "Phase 2 P0/P1 closed". **§6.5 Phase
   4 closeout** and **§13 acceptance** remain.

## Standing constraints — these have all drawn blood

- **`isolated_stack.bash --down` stops port `${RECURRENCE_PORT}` (default 8211) unconditionally and,
  unlike `--up`, with no pre-check.** 8211 is the DEPLOY container. Stop the trio by pid instead. It
  also `rm -f`s `${CANOPY_SRC_DIR}/snapshots/snapshot_*.h5` from the primary.
- **The sweep is where evidence dies.** Every arc worktree held a 203-434 KB ignored `logs/system.log`;
  `git status --porcelain` cannot see them and `git worktree remove` deletes them. One of those logs
  turned out to carry the leg provenance a five-agent review had just declared destroyed. **Harvest
  ignored `logs/` before removing anything.**
- **`git worktree remove` needs `gh pr view` = MERGED as the gate**, not ancestry:
  `worktree_sweep_survey.bash` marks squash-merged branches ACTIVE because a squash discards the head
  SHA.
- **A green check rollup does not mean mergeable.** Unresolved CodeQL review threads blocked three PRs
  at 23 SUCCESS / 0 failures. `util/ad-hoc/watch_prs_until_terminal.bash` reports `fail=`, `threads=` and
  `mergeState=` together; it wraps `util/wait_for_checks.py` — **do not hand-roll a poll loop**, two
  attempts did and both hit documented traps.
- **`safe_merge.py` has five refusal shapes.** `REFUSED: is MERGED, not OPEN` is a SUCCESS (an
  auto-merge net landed it first) — verify the merge commit's CONTENT, since being the merger is no
  longer evidence.
- **Never force-push after a server-side `update-branch` without fetching first** — it silently reverts
  the sync. Check `git merge-base --is-ancestor origin/main HEAD`.
- **Squash-merge ships the first commit's diff.** Collapse to one commit when a later commit corrects an
  earlier one on the same branch.
- **Read the WHOLE instrument output.** The arc's most expensive error was a universal ("never
  advances") written from the first 4 lines of a 35-line log; it reached four documents.
- **Count the writers before reasoning from a write census** — an `allow_duplicate=True` Output is
  invisible to anyone reading the handler they happened to open. Grep the store id, not the callback.
- **Check the declaration, not the prose about it** — a signature settles what a comment only claims.
- `/tmp` is prohibited for script source and is reaped: 10 census artifacts survived only as orphaned
  tempfiles and are now under `reports/e2e/_recovered/`.

## Environment

Drivers need `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python` (the conda
activate hooks do not run on direct binary invocation). `JuniperCanopy` does not exist — use
**`JuniperCanopy1`** / **`JuniperCascor1`**. `gh` is **2.46.0**: `gh pr checks --json` does not exist and
exits 0 on the unknown flag. No `util/ad-hoc/` script carries an execute bit — invoke via `python3`.

## Git state

juniper-ml on `chore/arc-teardown-evidence` → **ml#1495 open, CI running**; everything else merged.
juniper-canopy and juniper-cascor primaries clean, on `main`, up to date, released to peer session
`p5 memory` (`uds:/run/user/1000/cc-socks/3727200.sock`), which has queued: a hazards-promotion PR,
then canopy AGENTS.md PR1 (doc-about-doc → `docs/DOCUMENTATION_OVERVIEW.md`) and PR2 (the rest → a new
`docs/AGENTS_REFERENCE.md`), then cascor Tier A. **Do not start work in those repos without checking
with them first.** Only the three non-arc July canopy worktrees remain; they are not this arc's to
remove.
