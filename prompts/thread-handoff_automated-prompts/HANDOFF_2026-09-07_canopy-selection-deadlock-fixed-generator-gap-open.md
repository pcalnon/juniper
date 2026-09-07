# Thread Handoff — Canopy selection deadlock FIXED; the pair still cannot be TRAINED

- **Date**: 2026-09-07
- **Arc**: juniper-canopy model/dataset selection catch-22 (the "Recurrence cannot be selected" defect)
- **Session**: `catch-22`
- **Design of record**: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md) — **§12 is 57 lines; this handoff does not replace it**
- **Evaluation of record**: [`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md) — §6.1 (X1–X7), §6.4 (Y1–Y9)
- **Consensus validation**: [`notes/JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md`](../../notes/JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md) — **read §4, §5, §7 AND §8.2**
- **Browser evidence**: `reports/2026-09-05_canopy-deadlock-consensus/browser_acceptance.md` (on `main`)
  and `…/browser_acceptance_prb.md` (**lands with `ml#1809`; if that PR is still open, read it there**)

---

## Goal statement

Continue the juniper-canopy selection-reachability arc. `(recurrence, equities_seq)` is now
**selectable** — merged and observed in a browser. It is **not trainable**: staging that pair fails
on both branches, and Start is not gated on whether the selected model is the one that will actually
run. Close those, then the generator gap (§12), which the owner ruled equally critical.

**Completed — seven canopy PRs, all merged:** `#592` X1 model-state *label*; `#593` **the fix**
(`clearable=True`, the `⊥` cut vertex, Start gated on both axes, guards on all three `⊥`-commit
paths, restart-modal regate, G1a/G1b/G2/G6); `#594` §4.11 model clear + N11 + Y9 + G8; `#595` §4.7
empty-set + §4.3 notice channels + G3 + G1d; `#596` §4.12 demo degradation + G9; `#598` five resolver
injection points + G1c; `#599` §4.6 alias (X3) + §4.9 staging *guard* (X6) + G4 + the X8 tripwire.
Plus `ml#1803`/`#1804` (merged) and `ml#1809` (**open when written — confirm it merged**).

**Remaining work. The order matters: items 1–2 block §12.4, so §12 cannot complete before them.**

1. **N5 — Start is not gated on backend agreement. A "Recurrence" run executes on cascor.**
   `settings.py:261` defaults `recurrence_service_url=None`; `_selection_targets_recurrence`
   (`main.py:3859-3871`) then returns False for `recurrence`; `_swap_backend` short-circuits to
   `swapped=False` with **HTTP 200** and records the selection. The Start gate
   (`dashboard_manager.py:7545-7552`) reads only `model_is_trainable` (registry lifecycle, hardcoded
   `"live"`) plus both-axes-set — **never `swapped`, never provider agreement**. `#592` changed the
   *label*; nothing blocks the run. This is decision **N5** and the entire rationale for §7's
   "truth-telling precedes reach", and it is in no PR. **The bring-up recipe below masks it** because
   `--with-recurrence` sets the URL; a bare local canopy reproduces it.
2. **Staging the pair fails on both branches** (X6's real fix; `#599` only made the failure legible).
   cascor's `Literal` (`juniper-cascor/src/api/models/training.py:235`) has `equities` but **no
   `equities_seq`** → 502. The other branch needs `RecurrenceBackend.stage_dataset`, which needs a
   staging endpoint on juniper-recurrence first. **Both are cross-repo and neither is filed.**
3. **§12, iteration 2 — the generator gap.** The owner's stated primary goal. **Read §12 in full**;
   its prerequisites are summarised below but not reproduced.
4. **§4.10 dataset-axis hydration + G7** — a real unshipped deliverable, not a dead PR. The shipped
   code names it: `dashboard_manager.py:3110` says *"Seeding that value honestly is model/dataset
   hydration, which the design sequences separately (§4.10)."* Consensus §7 hands over the
   implementation: the `pending_dataset` channel already exists (`service_backend.py:308`,
   `demo_backend.py:131` — refutation R2), and `_init_params_from_backend_handler` is the natural
   host. G7 has **no test**. N10 says the ordering is non-negotiable: hydration lands *before*
   `⊥`-at-mount.
5. **`⊥`-at-mount (OQ-N2)** — owner-ACCEPTED, still undeliverable. See "Do not re-litigate".
6. **X10 / X11** — backend identity is health-blind (`RecurrenceBackend.initialize()` returns `True`
   unconditionally, so `main.py`'s 502 is unreachable); first paint always reads "Active: CasCor"
   because `_initial_model_summary` passes no `backend`.
7. **Y1 is live *because* this arc made recurrence reachable.** `main.py:4262` calls
   `backend.get_experimental_functions` **unguarded**, and `RecurrenceBackend` lacks it — so
   `GET /api/admin/experimental_functions` 500s on every page mount under recurrence. Y2 (snapshot
   save/restore writes cascor meta and zero LMU state, reporting success at both ends) is also live.
8. **∥ packaging** — `equities` **and any other extra a new seed needs** into
   `juniper-data/requirements.lock` (currently `--extra api --extra observability --extra mnist`).
   `arc-agi` is also unlocked, so that "easy" rank-2 seed is permanently `available=false` in the
   container.
9. **§4.3 residue**: its own step 1 was skipped — `dashboard_manager.py:2741` still labels the
   model-driven snap *"(dataset-primary conflict policy, D5)"*, which §4.3 said to correct *before*
   writing UI copy from it. And `aria-describedby` (Y7) never shipped: zero occurrences in `src/`.
10. **Record that OQ-6 is answered.** §4.11 said both-axes-clearable would make it answerable;
    `dashboard_manager.py:2754` now asserts the dataset-primary policy in a docstring. A deferred
    design decision has been settled without being written down.

---

## §12 prerequisites — do not seed without these

Summary only; **§12.3 and §12.4 are the authority**.

- **Y5 first.** The generators proxy sends no `X-API-Key` while `/v1/generators` is not auth-exempt,
  so canopy falls back to a schema-less list and every new seed renders "No adjustable parameters".
- **`csv_import` is excluded, not seeded** (§12.3.4) — it is an import path and canopy already has
  `dataset_import.py`. It belongs on **G10**'s named exclusion list.
- **`arc_agi`'s rank is unverified** (§12.3.5) and its extra is unlocked. It is not a free seed.
- **`mackey_glass` accepts a `seed` and ignores it.** Verified upstream:
  `juniper_data/generators/mackey_glass/params.py:37` — the seed is consumed only inside
  `if init_noise_std > 0`, which defaults to `0.0`. Seeding it into a benchmarking UI unflagged
  ships irreproducible runs.
- **Every seed needs bounded `default_params`** or the one-shot path blows cascor's 300 s timeout.
  **G11 as designed fails on the incumbents**: executed, `spirals/xor/mnist/circles/moons` all have
  `default_params={}` and only `equities_seq` is bounded. G11 needs a stated exemption or a
  narrower predicate.
- **G10 and G11 do not exist.** Neither is in canopy.
- **The seedable delta is ≤ 9, not 10** (consensus §4.2) — `csv_import` is excluded.
- **§12.4 requires generate → stage → train → render per seed.** Blocked by item 2 for every rank-3
  seed: none of `multi_sine`, `mackey_glass`, `ar_p`, `irregular_sine`, `delay_product` is in
  cascor's `Literal` either.

---

## Key context

### X8 will silently zero the LMU if you seed from upstream naively

canopy labels `equities_seq` `task_type="regression"` (`src/model_registry.py:141`); juniper-data
labels it `"classification"` (`juniper_data/api/routes/generators.py:117`). `compatible()` tests
`task_type in supported_task_types` and recurrence declares `frozenset({"regression"})`.

**Aligning canopy to upstream gives `compatible_models(equities_seq) == []` — the LMU becomes
unselectable.** The generator is genuinely dual-target and the LMU reads the regression target, so
both labels are locally correct; neither vocabulary has a word for "both". Inert today only because
`GeneratorInfo` omits `task_type` from the wire.
`src/tests/regression/test_dataset_generator_contract.py` pins it and **computes** the consequence.
Settle it before any §12 seed sources `task_type` upstream.

### Two independent cut vertices

The dataset ✕ and the model clear each independently break the deadlock — clearing the model ungates
the list, from which `equities_seq` can be picked directly. Measured; G2 asserted otherwise and
failed. **Consequence: neither affordance can be regression-tested by its own absence. Only the pair
can.**

### Do not re-litigate

- **`swapped is False` is the wrong "is this model active" predicate** — also False on the healthy
  re-select path. Use provider agreement. `backend_type` is exactly
  `{"service","demo","recurrence"}` — **no `"cascor"`**.
- **`⊥`-at-mount cannot be built as specified.** `params-init-interval` (`:1902`,
  `max_intervals=1`) is an `Input` of `gate_dataset_options` (`:2654`), which owns
  `Output("nn-dataset-type-dropdown","value")` — so a `⊥` mount is snapped to `spirals` one second
  after load. §4.1 calls that snap correct; §4.10 requires the opposite. **No phase ever edited the
  seed line** — `value=DEFAULT_DATASET_TYPE`, `dashboard_manager.py:1350` at `de253e9` (the design
  and the consensus doc both cite `:1333`, which was correct at the pre-arc `fc62175` and has since
  drifted). The design's §7 **row 2** — "§4.10 hydration + G7", never built, *not* a merged PR
  number — was the only thing that would have delivered it. Resolve the contradiction, land §4.10
  hydration first (N10), and note the field now sits behind X7's `offload()` status cache — a
  staleness question no document has answered. **The two-writer problem is prospective, not
  present**: `Output("nn-dataset-type-dropdown","value")` has exactly one writer today
  (`dashboard_manager.py:2649`); §4.10's hydration would add the second, on the same interval. **A clear inside the first ~1 s is also snapped
  back**, which a browser falsifier must wait out.
- **§4.3's repair notice is not interactively reachable** — the model table enables a Select only
  when the model is compatible with the current dataset, precisely when no snap is needed.
- **The alias fix is asymmetric on purpose.** One-shot body → juniper-data (`spiral`); staging
  payload → cascor, whose `Literal` takes canopy's **plural** dialect (`spirals`). Counter-guard:
  `test_the_STAGING_payload_must_NOT_be_translated`.

### Not established (consensus §8.2 — carry this forward)

**No training run was ever started.** Nothing in this arc says the LMU can train on `equities_seq`
end-to-end; B3 graded the "5× larger" framing **OVERSTATED** for exactly that reason. And **two
fail-open layers** mean a *down* juniper-data reports `equities_seq` **available**, with the failure
surfacing later as a 501 — so an empty-set state cannot be produced by stopping the service.

### Environment and traps

- **`conda run -n JuniperCanopy1 python -m pytest …`.** `JuniperCanopy` is DEPRECATED; the env's
  python invoked directly bypasses activate hooks → ~101 spurious torch ImportErrors.
- **A checkout is not a deployment.** The isolated stack serves canopy from the **shared**
  `juniper-canopy/src` (`isolated_stack.bash:66`), not your worktree. That checkout is **behind
  `origin/main`** at time of writing (`f8fb4a2` vs `de253e9`), so a stack brought up today serves
  code three commits old — this nearly produced a false browser result in this arc. Pull it first
  **and** grep the served source for your symbol. Note another session's stack may also be serving
  from it, so pulling changes code under a running service: check `ss -ltn` before you do.
- **A fixed sleep is not a synchronisation primitive.** Three probes this arc reported the *opposite*
  of the truth. Poll with a deadline. Clicks need `locator.click({force: true})`; a first-run
  "Welcome to Juniper Canopy" modal covers the sidebar and `force` skips the hit-test, so hit-test
  with `document.elementFromPoint` before concluding a control is inert.
- **A force-push does not fire `synchronize`.** Push a real commit (`update-branch` no-ops when the
  base has not moved).
- **`Allow-Symbol-Loss:` takes a list of bare symbols, never prose.** `--help`'s epilog documents
  the trailer itself; what it does *not* document is the kind-prefix vocabulary — `func:<name>` and
  `method:<Class>.<name>`. The value splits on `[,\s]+` (`symbol_loss_check.py:429`), so commas or
  whitespace both work and commas are the documented form. A justification sentence tokenises into
  words, matches nothing, and still FAILS.
- **The checker is NOT installed in `JuniperCanopy1`** (exit 127) — it resolves from `JuniperCascor1`.
  Run it by path before pushing:
  `/opt/miniforge3/envs/JuniperCascor1/bin/juniper-symbol-loss-check --base origin/main --head HEAD --scope 'src/**/*.py'`.
- **Three `test_demo_mode_gauge.py` failures are PRE-EXISTING and unrelated to this arc.** The
  mechanism is **not** juniper-data being down, which is what an earlier draft of this handoff
  claimed: all three fail `assert response.status_code == 200` on `GET /metrics` with **403
  Forbidden** — `juniper_observability.middleware.metrics_auth` refusing an unparseable client IP
  (`'testclient'`). juniper-data *is* also unreachable and *is* logged, but on a fallback path that
  then succeeds. Symptom holds, mechanism does not — reproduce before attributing.
- **`MEMORY.md` compaction is owed but is not a 140-line target.** The governor is a **25,000
  character** cap (currently ~20,850, 83%); the "140 lines" figure some tooling reports is the
  pre-eviction count from `JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` §4a, whose
  2026-08-19 eviction took it to 123. 7–8 sessions write the file concurrently, so a bulk rewrite
  clobbers peers.

---

## Verification commands

```bash
# 1. Both repos current
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git fetch origin && git log origin/main --oneline -3
cd /home/pcalnon/Development/python/Juniper/juniper-ml     && git fetch origin && git log origin/main --oneline -3

# 2. The arc's guardrails — 51 + 9 + 18 = 78 passing at de253e9 (measured, not estimated)
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda run -n JuniperCanopy1 python -m pytest \
  tests/regression/test_selection_reachability_guardrails.py \
  tests/regression/test_demo_mode_local_fallback.py \
  tests/regression/test_dataset_generator_contract.py -q

# 3. The deadlock is gone — must snap to equities_seq
conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from frontend.dashboard_manager import DashboardManager
o,v,n = DashboardManager({})._gate_dataset_options_handler('recurrence','spirals',generators=[])
print('snap ->', v)"

# 4. Item 1 is still open — must print False (Start NOT disabled for an inactive model)
conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from frontend.dashboard_manager import DashboardManager
st={'start':{'disabled':False,'loading':False,'timestamp':0}}
print('start_disabled =', DashboardManager({})._update_button_appearance_handler(
    button_states=st, model_key='recurrence', dataset_value='equities_seq')[0])"

# 5. X8 still inert (must print 'regression')
conda run -n JuniperCanopy1 python -c "
import sys; sys.path.insert(0,'.')
from model_registry import get_dataset_spec; print(get_dataset_spec('equities_seq').task_type)"
```

**Isolated stack** — never disturb the operator's 8050/8201; check ports first, a concurrent session
holds the documented defaults 8051/8101/8202/8211. Set `JUNIPER_E2E_PROJECT_DIR` explicitly: the
script derives it from `BASH_SOURCE` (`util/isolated_stack.bash:62`), so running from a worktree
resolves to a path that does not exist.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_E2E_DATA_PORT=8105 JUNIPER_E2E_CASCOR_PORT=8206 JUNIPER_E2E_CANOPY_PORT=8055 \
JUNIPER_E2E_RECURRENCE_PORT=8215 JUNIPER_E2E_RUN_DIR=/tmp/juniper-e2e-<yours> \
JUNIPER_E2E_DATA_EXTRAS=api,equities \
bash util/isolated_stack.bash --up --with-recurrence   # ...and --down after
# Omit the equities extra to reproduce the empty-set state.
# --with-recurrence SETS recurrence_service_url and therefore MASKS remaining item 1.
```

---

## Git status at handoff

- **juniper-canopy**: `origin/main` at `de253e9` (`#599`). Shared checkout clean. Remove the worktree
  `worktrees/juniper-canopy--feature--selection-staging-and-alias--20260907-0840--f56f46c2` now that
  `#599` has merged. `…--drop-full-family--…` and `…--val-split-gate--…` belong to **another
  session** — leave them.
- **juniper-ml**: this session worked from `.claude/worktrees/happy-yawning-boot` on
  `docs/canopy-prb-browser-acceptance` (`ml#1809`, open at time of writing).
- **Nothing uncommitted once this handoff is committed** — it is the only untracked file at time
  of writing. Every other change is in a merged or open PR.
- **The canopy shared checkout is at `f8fb4a2`, behind `origin/main` (`de253e9`).** Pull it before
  bringing up a stack (see the trap above).
- **Merge approval** was granted by the owner for all PRs in this arc; it does **not** extend to a
  new arc, and it never extended to deploys or PyPI gates.
