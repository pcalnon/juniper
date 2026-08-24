# HANDOFF 2026-08-23 — Canopy E2E: Phase 2 defect triage, and everything left on the arc

Continue the juniper-canopy E2E validation arc — **Phase 1 is COMPLETE; you are in Phase 2 (defect triage &
fix PRs)**, plan §6.3. Successor to
[`HANDOFF_2026-08-20_canopy-e2e-phase1-segment-16.md`](HANDOFF_2026-08-20_canopy-e2e-phase1-segment-16.md),
which covered the last 32 matrix rows. This one covers the **whole remaining arc**, not one segment.

**Read order ≠ page order.** Execute: **(1)** Verify starting state → **(2)** *What Phase 2 actually requires*
(the exit gate is 16 findings, not 28) → **(3)** Standing up the stack → **(4)** The F-CANOPY-027 dossier
(read before touching it — eighteen mechanisms are already refuted) → **(5)** Recording verdicts →
**(6)** Landing. *Traps* is reference, not a step.

## Documents

| what                                                                       | path                                                                        |
|----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| matrix (the ledger)                                                        | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| evidence note (findings ledger + per-segment record)                       | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`        |
| plan (§6.3 Phase 2, §6.4 Phase 3, §6.5 Phase 4, merge policy `:689`)       | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`   |

## Verify your starting state first

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline -3 origin/main    # expect b402bfa or later
git status --porcelain                                  # expect clean
gh pr list --repo pcalnon/juniper-ml     --state open --limit 10
gh pr list --repo pcalnon/juniper-canopy --state open --limit 10
python3 util/ad-hoc/e2e_unfilled_rows.py                # expect 298 verdicted / 0 UNFILLED
python3 util/ad-hoc/e2e_finding_triage.py --open-only   # expect 37 findings / 9 fixed / 28 open
```

Sibling checkouts (paths are ecosystem-root-relative; both must be clean and current):

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-canopy log --oneline -1   # expect 041eb69 or later
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor  log --oneline -1
```

## Where the arc stands

**Phase 1 row coverage is CLOSED at 298 of 298.** Every row carries a terminal verdict. That is *coverage*,
not health — the distribution is **226 PASS · 48 BLOCKED · 21 FAIL · 3 other** (`INCONCLUSIVE`,
`DIVERGENCE D-1 CONFIRMED`, `PASS + doc nuance`). **69 rows are FAIL or BLOCKED**, and almost all of them
trace to a small number of open findings rather than to independent problems.

**Findings: 37 total, 9 fixed, 28 open.** Run `e2e_finding_triage.py` rather than trusting any list —
including this one.

## What Phase 2 actually requires

Plan §6.3's exit is *"every P0 and P1 closed or explicitly deferred with owner sign-off; no matrix row left
FAIL without a linked issue."* That is **16 findings**, not 28 — the 9 open P2s, 2 LEDGER entries and 1
untriaged do **not** gate the phase:

| pri       |  n | ids                                                                                                |
|-----------|---:|----------------------------------------------------------------------------------------------------|
| P0        |  3 | F-CANOPY-002, F-CANOPY-005, F-CANOPY-006                                                           |
| P0/P1     |  3 | F-CANOPY-004, F-CANOPY-008, **F-CANOPY-027**                                                       |
| P1        | 10 | F-CANOPY-003, -007, -009, -010, -011, -014, -025, -031, F-CASCOR-001, F-ML-001                     |
| *(P2)*    |  9 | F-CANOPY-001, -012, -015, -018, -026, -028, -032, -033, F-CASCOR-002 — **not** a Phase 2 gate      |
| *(other)* |  3 | F-E2E-004, F-E2E-005 (LEDGER); **F-CANOPY-013 has no priority tag — triage it first, it is cheap** |

Each fix PR must carry, per §6.3: **(a)** the fix, **(b)** a regression test that fails on the parent commit,
**(c)** a matrix-row reference. After merge, re-drive the affected rows on a fresh stack and re-score.

> **The regression test must be shown to FAIL on the parent commit.** This is not ceremony — F-CANOPY-029's
> whole reason for shipping was two green tests that asserted against a shape production never had. When that
> was fixed, the hardened tests were re-run against a temporarily-reverted fix and did reproduce the
> production error. Do that every time; a hardened test that passes both ways buys nothing.

## Ordering: fix by leverage, not by number

Measured, not guessed:

1. **F-CANOPY-027** (P0/P1) — the single highest-leverage item. It alone accounts for the Candidate Metrics,
   Decision Boundary and Dataset View panels: ~a dozen FAIL/BLOCKED rows, **and** it invalidates five rows
   (`M-CANDIDATES-01/-02/-03/-04/-06`) that currently carry `PASS` recorded against the panel's *mount
   defaults* — `-02`/`-03`'s stated expectations literally name the defaults `"Idle"` and `"0"`. Those five
   must be re-driven once it is fixed. **Read the dossier below before starting.**
2. **F-CANOPY-031** (P1) — the snapshots panel never renders against the migrated 27,903-entry corpus; a
   direct consequence of the S-1 storage move and likely far more tractable than -027.
3. **F-CANOPY-002 / -006** (P0) — both are root-caused already in the ledger, with the mechanism named.
4. **F-CANOPY-025** (P1) — blocks workflow W7 entirely from the UI.
5. The rest of P1, then decide with the owner whether the 9 P2s are fixed or deferred (§6.3 allows explicit
   deferral with sign-off; **that is the owner's call, not yours**).

The reference for how a fix lands end-to-end is **F-CANOPY-029**: `juniper-canopy#504` (`041eb69`) for the
fix + test hardening, then `juniper-ml#1248` (`8d6e1f3`) for the record and the five re-scored rows.

## The F-CANOPY-027 dossier — read this before touching it

The ledger entry is the authority; it now carries three appended investigation blocks. Summary of state:

**What it is.** A panel's data store is written repeatedly with genuinely changing data and *nothing*
downstream of it ever runs, so three panels sit at mount defaults through an entire live run. Reproduced
cleanly: backend advanced `candidate_epoch` **1 → 101** at a steady `pool_size 40` while the panel held a
single DOM state for 180 s.

**The broken layer is identified.** An A/B injection settled it. Using each component's own Dash-supplied
`setProps({data: …})`, with a redux control confirming the prop really changed:

| store                                                 | prop written? | consumers        |
|-------------------------------------------------------|---------------|------------------|
| `metrics-panel-training-state-store` (working)        | yes, verified | **all 3 FIRED**  |
| `candidate-metrics-panel-training-state-store` (dead) | yes, verified | **all 3 SILENT** |

So Dash's client does not treat the dead store as an **observable callback Input at runtime**, even though
its five consumers are in the served `/dashboard/_dash-dependencies` with the exact input id, `paths`
resolves to the correct `Store`, and the prop is writable. The unapplied server response and the
never-firing consumers are **two faces of one defect**.

**Eighteen mechanisms are already refuted — do not re-run them.** They are enumerated as bullets in the ledger entry, plus a seven-item prose "Ruled out" list from the original write-up that partly overlaps.
Highlights that cost the most time: mount order (falsified by its own prediction — the working chain survived
an unmount/remount round-trip); duplicate ids (both earlier checks were blind to `dcc.Store`, which renders
no DOM); "the callback hangs" (they complete in 0.6–2.6 s); "the value never changes" (27 of 29 payloads
differ); and "the prop is written then reverted inside the sampling gap" (replaced 400 ms polling with a
`store.subscribe` observer — across **5974** state changes the dead prop held exactly one value, `{}`).

**The one property still standing.** The working panel is the **default/first** tab (its store path carries
no tab index after the tabs container); every dead panel sits at an indexed position — candidate
`children/1`, boundary `children/4`, dataset `children/5`. All four are children of `visualization-tabs`,
which the model-class callback rebuilds. Note this is **narrower than** the already-refuted mount-order
hypothesis: "mounts later" is insufficient; *"is never the initially-active pane"* is what survives.

**Fastest iteration loop.** `util/ad-hoc/e2e_f027_setprops_probe.py` is a ~1-minute yes/no test of whether
the wiring is restored — use it instead of a full driving pass:

```bash
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_f027_setprops_probe.py --tab 'Candidate Metrics'
# control (must show all three FIRED):
LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/e2e_f027_setprops_probe.py --tab 'Training Metrics' --store metrics-panel-training-state-store --consumers metrics-panel-progress-detail,metrics-panel-current-lr,metrics-panel-phase-duration
```

## Rows that need re-driving regardless of any fix

- **`M-CANDIDATES-01/-02/-03/-04/-06`** — currently `PASS` against mount defaults (see above). Treat as
  unproven.
- **`M-DATASET-14`** — `BLOCKED` on an *instrument* limit, not a defect: the `dark-mode-toggle` click never
  fired, so no theme transition occurred. Needs a verified theme flip before the recolour arm can be judged.
- **`M-DATASET-17..26`** (10 rows) — the sequence/3-D control set. `BLOCKED` structurally, not by timing: a
  sequence dataset cannot be loaded in the LIVE lane at all. `POST /api/dataset/generate` is demo-gated (400)
  and both sequence-capable registry entries (`equities`, `equities_seq`) report `available:false` from
  `GET /api/dataset/generators`. Reaching them needs the **DEMO lane** or a 3-D model posture — an owner
  scoping decision, not a driving problem.
- **`M-SNAPSHOTS-19/-20/-21`** — -19 unblocks if F-CANOPY-031 is fixed; -20/-21 need a real dataset-swap
  event, reachable only via `POST /v1/training/dataset/swap` (F-CANOPY-025 kills the UI entry point).

## Beyond Phase 2

- **Phase 3** (plan §6.4) — the automated UI suite, 4 PRs in juniper-canopy: harness (`ui_live` marker +
  `src/tests/ui_live/` + `make test-ui-live`), per-tab smoke, workflow suites, fragile-area regressions.
  **Entry condition is Phase 2 P0/P1 closed**, so the suite encodes correct behaviour rather than bugs. Do
  not start it early.
- **Phase 4** (plan §6.5) — evidence report is already largely written (the evidence note *is* it); remaining
  is the docs-truth-up PR(s) per §11 and a closeout note against §13's acceptance criteria.

## Standing up the stack

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper JUNIPER_E2E_RECURRENCE_PORT=8212 util/isolated_stack.bash --up    # data 8101 · cascor 8202 · canopy 8051
# teardown uses the SAME overrides. No corpus backup, no restore.
```

**No snapshot backup ceremony.** The root moved to `<Juniper>/juniper-cascor/cascor-snapshots/`
(`isolated_stack.bash:122`) under the S-1 ruling, and teardown no longer sweeps it — the script carries an
explicit `-- DO NOT ADD A SWEEP OF ${CASCOR_SNAPSHOT_ROOT} HERE --` guard at `:476`. The root holds **27,903+
`.h5` / 1.8 GB**; copying it is actively harmful, and `ls *.h5 | wc -l` overflows the shell arg limit and
reports **0** — count with `find <root> -maxdepth 1 -name '*.h5' | wc -l`.

Two live hazards remain: `--down` stops the recurrence port **unconditionally** and defaults to **8211, the
port the live juniper-deploy container holds** (`:83`, stop at `:467`) — always pass
`JUNIPER_E2E_RECURRENCE_PORT=8212`; and `PROJECT_DIR` derives from the script's own location (`:62`), so a
worktree resolves siblings to non-existent paths unless `JUNIPER_E2E_PROJECT_DIR` is set.

Gate every live check on canopy `/v1/health` reporting `demo_mode:false` **and**
`juniper_data_available:true` — HTTP 200 alone is not the gate. Record leg pids at bring-up; a count on this
shared GPU box is not a measurement. **Never run `util/reap_pytest_orphans.bash` while the stack is up**
(F-ML-001).

Special postures, when needed: `C2.5-07` needs `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` exported
*before* `--up`; the DEMO lane needs a **hand-launched** canopy (the launcher hard-codes
`JUNIPER_CANOPY_DEMO_MODE=0` at `:379`) and that launch **must clear `LD_LIBRARY_PATH`**, because the demo
backend imports torch where the service backend does not.

## Recording verdicts

New bring-up ⇒ new run id `<UTC yyyymmddThhmmssZ>`; create `reports/e2e/<RUN_ID>/statuses.tsv` with header
`row_id<TAB>status<TAB>notes<TAB>screenshots`; update `reports/e2e/CURRENT_RUN_ID` (currently
`20260822T014138Z` — a human pointer only, no tool reads it). **Screenshots are local evidence — never commit
them**; `open_signed_pr.py` base64s raw bytes and bypasses the LFS clean filter.

For Phase 2 re-scores use **`util/ad-hoc/e2e_matrix_rescore.py`**, not `e2e_matrix_fill.py --overwrite` —
the latter rewrites every cell any source covers and would clobber hand-authored cells
(`INCONCLUSIVE`, `DIVERGENCE D-1 CONFIRMED …`). The rescore tool touches only named rows and refuses any edit
that changes a line's cell count. Verify every matrix edit with
`git diff -U0 <matrix> | grep -E '^[-+]\|'` — equal in/out counts, zero cell-count mismatches.

Only plan §9 vocabulary reaches a status cell: `PASS` / `FAIL` / `BLOCKED` / `N-A` / `DEAD-CONFIRMED`,
optionally with a rider that *narrows* the verdict. `pending …` is not a verdict. §6.3 asks re-validated rows
to read `PASS (re-validated @ <sha>)`.

## Traps that have already cost this arc time

**Instrument discipline — this is where the arc has lost the most time.**

- **Substring matching on component ids has misled me four times.**
  `candidate-metrics-panel-training-state-store` **contains** `metrics-panel-training-state-store`; a
  multi-output callback stores every output under one combined key, which made a correct 182-entry registry
  look like it was missing 253. Use exact `==` on ids, and count entries rather than trusting a derived index.
- **Never `includes()` against a sliced response.** The largest real Dash response measured is **675,891
  chars**; a 3 000-char slice reported zero hits for outputs that were present.
- **Never let a capture buffer evict.** A 250-entry ring under-reported fills 4×.
- **Subscribe, don't sample.** A 400 ms poll cannot prove "never changed" when `SET_PATHS` fires ~2/s;
  `store.subscribe` sees every dispatch.
- **Scope Radix option scrapes by the trigger's `aria-controls`** — a bare `[role=option]` sweep catches
  other open menus.
- **Use a panel's own ids.** A `table tbody tr` count once read the Network Info table and reported 63
  snapshot rows that did not exist.
- **A fixed control can still look dead.** The repaired F-CANOPY-029 modal takes **~39 s** to appear under
  F-CANOPY-004 congestion; a 3 s settle reported the working fix as still broken. Poll for the transition.

**Driving.** Verify a click by its EFFECT, not the tool's return — Playwright's post-click ack times out
while the click lands, and real keystrokes do **not** land at all (`elementHandle.type()` times out *and*
leaves the value untouched). Numeric inputs take the native value-setter idiom. `dbc.Checkbox` needs
`_valueTracker.setValue(String(!target))` + native `checked` setter + a **`click`** event (React drives
checkbox onChange off click, not change). `<button>`, `[role=tab]`, `[role=option]` and `dcc.RadioItems` take
a plain raw `.click()`; `dbc.Switch` is inert to it.

**Reading.** Settle times run 3–17 s and up; closed modals are legitimately **ABSENT**; panels are hidden,
not unmounted — assert visibility via `getComputedStyle` + `getBoundingClientRect`, and remember `dcc.Store`
/ `dcc.Interval` render **no DOM at all**, so a zero node count for a store proves nothing. Poll for a
*change* when the target already holds text. `/api/set_params`, `/api/stage_dataset` and the snapshot routes
are POSTed **server-side** — zero browser requests is expected. Clientside callbacks emit no
`_dash-update-component` traffic.

**Judgement.** A first-pass anomaly here is more often the instrument than a defect: this arc has caught
**four** wrong findings before filing (most recently `dataset-plotter-split-selector`, which I called
"definitively" broken one step before driving all three of its values cleanly). Reproduce a second way, and
read the handler, before writing it down. A negative-arm pass is not evidence a gate works — that trap hid
F-CANOPY-025 for five segments and taints five §3.2 rows today.

## Landing work

One PR per defect or tight cluster. Deliverables for a Phase 2 fix: the canopy fix PR (fix + failing-on-parent
regression test), then a juniper-ml companion PR carrying the evidence-note update, the re-drive
`reports/e2e/<RUN_ID>/statuses.tsv`, the `CURRENT_RUN_ID` bump, and the re-scored matrix cells.

1. Branch from a freshly fetched `origin/main`; `gh pr list` immediately before pushing.
2. Commit signed with `util/open_signed_pr.py` (`--repo` / `--branch` / `--add local:repopath` / `--message`
   / `--title` / `--body-file`) — `main` enforces `required_signatures`. It uploads **whole files**, so two
   PRs touching one file must merge sequentially with the second rebased. Its dup-guard refuses a second PR
   on a branch that already has one open, so a correction needs a **new branch** and the old PR closed.
   `--body-file` bypasses the template: include the `## Requirements` section yourself.
3. **Scan new Python for unused imports before pushing.** CodeQL blocks the merge via an unresolved review
   thread while the checks rollup still reads green — this cost a full PR cycle in this series.
4. Wait with `util/wait_for_checks.py --pr <N> --anchor required`; never hand-roll a poll loop. Then check
   `gh pr view <N> --json mergeStateStatus` — `BLOCKED` with green checks means an unresolved CodeQL thread.
5. Merge with the REST squash endpoint:
   `gh api -X PUT repos/<owner>/<repo>/pulls/<N>/merge -f merge_method=squash`. Headless merge is
   pre-authorized for this arc by the plan (`:689`) — green CI including `ui-tests`, and no release/publish
   or deploy-gate machinery. **A canopy code fix is still `PR-C*` in the plan's own sequence, so it is
   covered.**
6. After merging: `gh run list --workflow=main-verify.yml -c "$(gh pr view <N> --json mergeCommit -q .mergeCommit.oid)"`
   — **`-c` matches only FULL 40-char SHAs**. juniper-canopy does **not** auto-delete merged branches; delete
   them via `gh api -X DELETE repos/pcalnon/juniper-canopy/git/refs/heads/<branch>`.

**Before emitting the next handoff, validate it independently.** This arc's handoffs inherit errors across
generations — one was rewritten only after three validators failed its first draft. Re-run
`e2e_unfilled_rows.py` and `e2e_finding_triage.py` and diff their output against whatever tables you write.

## Tooling you already have

31 arc scripts under `util/ad-hoc/e2e_*.py`. The ones you will actually reach for:

| tool                          | use                                                                                |
|-------------------------------|------------------------------------------------------------------------------------|
| `e2e_finding_triage.py`       | open/fixed + P0/P1/P2 counts straight from the ledger (`--open-only`)              |
| `e2e_unfilled_rows.py`        | ledger-derived row coverage — authoritative; `e2e_row_coverage.py` is an estimator |
| `e2e_matrix_rescore.py`       | re-score **named** rows after a fix, cell-count safe                               |
| `e2e_matrix_fill.py`          | fill from run records (dry-run default; **do not** use `--overwrite` for rescores) |
| `e2e_append_statuses.py`      | dup-guarded TSV verdict append                                                     |
| `e2e_f027_setprops_probe.py`  | ~1-min yes/no wiring test — the F-CANOPY-027 iteration loop                        |
| `e2e_f027_*` (17 more)        | the full F-CANOPY-027 forensic kit — registry, layout, paths, dispatch, redux      |
| `e2e_seg16_dataset_driver.py` | §3.6 + singleton driver (`--step start,toolbar,selector,…`)                        |
| `isolated_stack.bash`         | `--up` / `--down` / `--status` / `--dry-run`, **always with both env overrides**   |

Drive under `LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python` — the only env with playwright.
Try the browser MCP first (`mcp__playwright__*`); it has been present in roughly half the segments and absent
in the rest, including the last three.

## Git state at handoff

Cut from `b402bfa` on `origin/main`; juniper-canopy at `041eb69`. **No open PR in either repo.** Working tree
clean; the isolated stack is **DOWN** and all isolated ports are free. **`origin/main` moves several times a
day — always branch from a freshly fetched `origin/main`, never from the SHA above, and re-derive every line
anchor in this document before relying on it** (the 2026-08-21 pass alone had to move four).

Matrix at **298 of 298** (226 PASS · 48 BLOCKED · 21 FAIL · 3 other). Verdict records:
`reports/e2e/20260809T223851Z/rowlog.md` plus `statuses.tsv` under `20260810T002233Z`, `20260811T010700Z`,
`20260816T124231Z`, `20260817T093715Z`, `20260817T101500Z`, `20260820T080544Z`, `20260821T212306Z`,
`20260822T014138Z`.
