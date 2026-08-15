# CLI Experimentation — F-P1-3: the direct CLI was never compute-bound

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-ml / juniper-cascor
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-14

**F-P1-3** — the cascor direct CLI (`src/main.py`) has never been run to completion anywhere
in this arc — is a **blocking `plt.show()` after training finishes**, not a budget or
performance problem. Root-caused, reproduced under control, and fixed in **cascor#517**.

The headline number: on the arm that
[R-5](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R5-SERVICE-VS-CLI-EVIDENCE.md)
had to kill after ~15 minutes, **training finishes in 39 seconds**. Everything after that was
spent parked in a GUI event loop waiting for windows nobody would close.

This **overturns finding F-P1-3b** ("structural CLI-path compute overhead", P1 note §5). The
direct CLI is not slow. It just never exits.

---

## 1. The controlled experiment

Three arms. Same host, same per-run juniper-data instance (`:8110`), same smoke YAML
(`util/ad-hoc/2026-08-14_r5_arm_c_direct_cli_smoke.yaml` — `max_hidden_units: 2`,
`candidate_pool_size: 4`, `candidate_epochs: 50`). One variable moves at a time.

| arm | checkout | matplotlib backend | flags | outcome |
| --- | --- | --- | --- | --- |
| **A** treatment | cascor `main` `1d04989` | `Agg` (forced via `MPLBACKEND`) | — | **exit 0, 39 s** |
| **B** control | cascor `main` `1d04989` | `tkagg` (inherited, `DISPLAY=:0`) | — | **hung past a 240 s bound** |
| **C** fix | cascor#517 branch | `tkagg` (inherited) | `--no-plots` | **exit 0, 38–40 s** |

The arms agree on everything except termination:

- `fit: Training completed.` lands at **+39 s** in all three.
- All three reach the 2-unit cap, train accuracy **0.960**, test **0.970**, unit correlations
  0.321 / 0.326.
- A and C then reach `main.py: Completed solving SpiralProblem instance` and exit 0.
- B's log **stops dead** after the two `Started plotting process PID: …` lines. Across the
  full 241 s there are **zero** occurrences of `Completed solving SpiralProblem instance`.

Arm A is the first completed direct-CLI run on record in this program. Arm B is the same
binary, the same seconds of training, and no exit.

> **On arm B's exit code.** `timeout` returned **125**, not the 124/137 a TERM/KILL implies.
> That is a `timeout --kill-after` reporting artifact and is *not* evidence of completion — the
> substantive signals are `wall_seconds=241` (the bound) and the absent completion line. The
> control script's verdict now keys on reaching the bound rather than on `rc`, because `rc`
> alone was misleading enough to nearly invert the reading.

---

## 2. The mechanism

`solve_n_spiral_problem` ends like this
(`juniper-cascor/src/spiral_problem/spiral_problem.py:1325-1327`, pre-fix):

```python
if self.plot:
    plt.show()
    self.plotter.join()
```

Both calls block under an interactive backend:

- **`plt.show()`** hands the process to the GUI event loop until every figure window is
  closed. In an automated run there is no one to close them.
- **`self.plotter.join()`** waits on the dataset-plot child spawned at
  `spiral_problem.py:1298` (pre-fix; `:1325` after cascor#517) — a **non-daemon** `spawn` process, which is itself parked in its
  own `plt.show()` (`juniper-cascor/src/cascor_plotter/cascor_plotter.py:125`; the same
  pattern at lines 194 and 246). So even if the parent's `show()` returned, the join would
  not.

The decision-boundary and training-history plotters (`cascade_correlation.py:5755-5793`) are
`daemon=True`, so they are not the ones holding the run open — the dataset plotter is.

### 2.1 Why it could not be turned off

- Plotting defaults to **on**: `_SPIRAL_PROBLEM_GENERATE_PLOTS_DEFAULT = True`
  (`juniper-cascor/src/cascor_constants/constants_problem/constants_problem.py:868`), passed
  straight through at `juniper-cascor/src/main.py:438` and `:501`.
- The **W-11 key maps carry no plot knob**. `_W11_DATASET_KEY_MAP` (7 keys) and
  `_W11_TRAINING_KEY_MAP` (8 keys) at `juniper-cascor/src/main.py:229-250` cover dataset
  geometry and training budget only. `_resolve_cli_overrides` reads *only* `dataset.params`
  and `training.params`.
- Consequently `outputs.plots: []` in an experiment YAML is **not consumed by the direct CLI
  at all** — it is a driver-side (`run_experiment.py`) concept. The smoke YAML sets it, which
  makes the config *look* like it disabled plotting. It never did.
- Before cascor#517 there was no `--no-plots` flag either. There was no way, from any
  supported surface, to stop the CLI from opening windows.

### 2.2 Why the host matters

`DISPLAY=:0` is set on this workstation, so matplotlib resolves to **`tkagg`** — interactive.
A truly headless machine resolves to `Agg`, where `plt.show()` is a no-op and the CLI would
have exited normally. That is why this presented as an intractable property of the CLI rather
than an obvious hang: it depends on the launching environment, not on the config.

### 2.3 Why the service path never showed it

The service tier never calls `solve_n_spiral_problem` and never constructs a plotter — it
drives `CascadeCorrelationNetwork` directly and returns over HTTP. Every E-A, E-I and R-5
service run terminated correctly at its cap. The defect is confined to the direct-CLI entry
point, which is exactly the path with no automated coverage.

---

## 3. What this overturns

The [P1 smoke evidence](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md)
§5 recorded **F-P1-3b**:

> with every documented bound verifiably applied, the direct-CLI training path exceeds a 590 s
> smoke bound on this host, where the **service** path completes the identical shape […] in
> **24 s**. The gap is structural CLI-path compute overhead

Both halves of that inference were sound given what was visible, and both are wrong:

- **"exceeds a 590 s bound"** — it exceeded the bound; it was not *training* for 590 s. That
  campaign's five attempts progressively tightened budgets (pool 156→12, epochs, log level)
  and every one still timed out, which reasonably reads as compute-bound. All five were
  blocked in the same place, and no budget knob could ever have moved it.
- **"structural CLI-path compute overhead"** — there is no measured CLI-vs-service compute gap
  here at all. The service completes the shape in 24 s; the CLI trains its arm in 39 s. Those
  are the same order, on a different arm, with candidate patience changed by cascor#514 in
  between. There may or may not be a real per-path difference; **this arc never measured one.**

The methodological point, and it is the same one
[R-5 §5.1](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R5-SERVICE-VS-CLI-EVIDENCE.md)
flagged: a timeout is not a measurement. Five timeouts are not five measurements. Nothing in
the F-P1-3b campaign observed the CLI *finish*, so nothing in it constrained how long the CLI
takes to finish.

---

## 4. The fix (cascor#517)

Two halves, covering different conditions:

1. **`--no-plots`** skips the figures entirely, threaded through every entrypoint — plain,
   `--profile`, `--profile-memory`. A profiling run is automated by definition and is
   precisely the path that must not park in an event loop. **This is the operative fix on any
   host with `DISPLAY` set**, which includes this one.
2. **The blocking pair now sits behind `_backend_is_interactive()`.** A genuinely headless run
   no longer depends on `plt.show()` *happening* to be a no-op under Agg, nor `join()` on the
   child's behaviour; and the silent discard of display-only figures is logged instead of
   invisible.

The `plot_*` helpers only ever `show()` — they never `savefig` — so skipping them loses no
artifact. That is worth stating plainly: **the direct CLI has never produced a plot file.**
Its figures are screen-only, which is why disabling them costs the experimentation program
nothing.

Regression coverage: `src/tests/unit/test_fp13_direct_cli_termination.py` pins the flag
plumbing (including that no entrypoint calls a bare `main()`), `_backend_is_interactive()`
across both backend classes plus the pre-3.9-matplotlib fallback, and an anti-regression check
that neither blocking call can drift back outside the guard.

---

## 5. Latent findings, filed not fixed

Found while tracing the budget path; all inert today, none bundled into the hang fix.

| # | finding | status |
| --- | --- | --- |
| L-1 | `spiral_problem.py:1338` (`:1311` pre-cascor#517) calls `fit(max_epochs=_SPIRAL_PROBLEM_OUTPUT_EPOCHS)` — the module **constant**, not `self.output_epochs`, which is where the W-11 `output_epochs` / `max_epochs` override actually lands. | Inert |
| L-2 | `fit()` never forwards `max_epochs` to `grow_network`: it is logged at `cascade_correlation.py:1910` and then unused (`:1912`). So L-1 is inert *because* the argument is dead — the effective output-epoch budget arrives via the config object, which does carry the override. | Inert |
| L-3 | `epochs_max` is assigned at `cascade_correlation.py:714` and never read anywhere in that module. Its constant is `_PROJECT_MODEL_EPOCHS_MAX = 100_000_000_000` (`constants_model.py:206`) — a 1e11 sentinel that looks like an unbounded budget but governs nothing. | Dead |
| L-4 | `training.params.early_stopping` is reported by W-11 as service-tier-only and ignored, so the direct CLI always uses `fit()`'s `early_stopping=True` default. Harmless while every config wants it true; silently wrong the first time one does not. | Inert |

L-1 and L-3 are the dangerous shape: two plausible-looking budget knobs that a future
investigator will reach for and that do nothing. Recommend fixing L-1/L-2 together (pass
`self.output_epochs`, and either forward `max_epochs` or drop the parameter) and deleting L-3
outright.

> **Superseded — read [§9](#9-5-correction--l-1-is-live-and-l-3-must-not-be-deleted-2026-08-14-post-merge) before acting on this table.**
> This section was written from a static read. L-1 is **live**, not inert (fixed in cascor#522);
> L-2's "the argument is dead" is wrong; and deleting L-3 would **break the build** — it is the
> C2b/Q1 snapshot-compat attribute, not dead code.

---

## 6. What this unblocks

R-5 §5 named F-P1-3 as *"the only thing standing between this analysis and a direct
head-to-head"*. That blocker is gone: with cascor#517, the direct CLI runs to completion at a
controlled budget in well under a minute on smoke-scale arms.

The head-to-head itself is **not** performed here and should not be assembled from this note's
numbers. Arm C ran on the cascor#517 branch, i.e. **post-#514**, and
[R-5 §5.1](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R5-SERVICE-VS-CLI-EVIDENCE.md)
established that spiral figures are not comparable across #514 — candidates now get the
configured patience 100 rather than a hardcoded 50. A real comparison needs both arms on the
same side of #514, which is a fresh campaign, not a re-read of this one.

---

## 7. Reproduction

```bash
# 1. per-run data service (prints RUN_ID / DATA_URL)
util/ad-hoc/2026-08-14_r5_stack_up.bash

# 2. control — unfixed checkout, inherited backend: hangs at the bound
util/ad-hoc/2026-08-14_fp13_control_tkagg.bash \
    util/ad-hoc/2026-08-14_r5_arm_c_direct_cli_smoke.yaml <OUT_DIR> <DATA_URL> 240

# 3. fix — cascor#517 checkout, inherited backend, plots off: exits 0 in ~40 s
util/ad-hoc/2026-08-14_fp13_verify_fix.bash \
    <CASCOR_SRC> util/ad-hoc/2026-08-14_r5_arm_c_direct_cli_smoke.yaml \
    <OUT_DIR> <DATA_URL> 240 -- --no-plots

# 4. the discriminating check — the completion line the control never reaches
grep -c 'Completed solving SpiralProblem instance' <CASCOR_CHECKOUT>/logs/juniper_cascor.log

# 5. teardown
util/experiment_stack.bash --down <RUN_ID>
```

Two traps worth carrying forward:

- **The parent's log is not on stdout.** `main.py`'s own logger writes to
  `<checkout>/logs/juniper_cascor.log`; stdout carries only the candidate workers' lines. A
  run tailed on stdout looks like it died mid-candidate-training when it in fact finished and
  hung later. Read the file log.
- **A fresh worktree has no `logs/`**, and the path derives from the checkout root
  (`constants.py:416`, `_PROJECT_DIR = _PROJECT_SOURCE_DIR.parent`), so logger init raises
  `FileNotFoundError` before anything runs. `mkdir logs` first — both ad-hoc runners now do.

---

## 8. Disposition

| item | status |
| --- | --- |
| **F-P1-3** — direct CLI cannot be run to completion at a controlled budget | **CLOSED** — root-caused (§2), fixed in cascor#517, verified (§1 arm C) |
| **F-P1-3b** — "structural CLI-path compute overhead" | **WITHDRAWN** (§3) — no compute gap was ever measured; the 590 s was a block, not a workload |
| P1.2 full-completion row (P1 smoke) | **Re-runnable** — arm A/C are completed direct-CLI runs; the P1 row can close once #517 merges |
| R-5 §5 "no completed direct-CLI run" | **Resolved**; the head-to-head itself is now **CLOSED at smoke scale** — [head-to-head smoke evidence](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md): no path gap, and F-P1-3b positively **refuted** |
| L-1 … L-4 | **Superseded by §9** — L-1 was live (fixed, cascor#522); L-2 re-scoped; L-3's "delete" recommendation withdrawn; L-4 still filed |

Artifacts live under the run dir
`~/.local/state/juniper-experiments/20260814T200636Z-dcf8/artifacts/results/` —
`fp13-agg/` (arm A), `fp13-control/` (arm B), `fp13-fix-noplots-2/` and `fp13-fix-postisort/`
(arm C, the latter re-run after isort touched the imports).

### 8.1 Evidence-preservation correction (added after validation)

**The per-arm figures above are NOT re-derivable from those run dirs.** Independent validation of
this note's handoff caught three compounding causes, all since fixed:

1. The runners captured **stdout only**, and the parent's logger writes to
   `<checkout>/logs/juniper_cascor.log`. All four arm logs contain **zero** occurrences of
   `Training completed` / `Started plotting process PID` / `Completed solving` — so the preserved
   dirs cannot tell arm B apart from arms A/C on the completion marker at all.
2. Those runs used the **shared** cascor checkout, whose log the live `:8202` service rotates every
   few minutes. The 15:06-15:14 window has rotated away.
3. Arm B's own verdict line was **overwritten**: a `>` redirect gives forked children a shared
   non-append offset, so an orphan flushing after the kill wrote over what the shell had appended.

Both ad-hoc runners now use `>>` and slice the run's own portion of the parent log into
`OUT_DIR/parent_juniper_cascor.log`. A **preserved** arm-C run (2026-08-14 17:50, dedicated
worktree) lives at
`~/.local/state/juniper-experiments/20260814T224846Z-0565/artifacts/results/fp13-armC-preserved/`:
`Completed solving` ×1, `Training completed` ×1, `Started plotting` ×**0** (proving `--no-plots`
end to end), 2-unit cap, train **0.95625**.

Two corrections to §1 that follow: train **0.960** / test **0.970** are **arm A's** figures, not
all three arms'; and the wall times are contention-dependent — arm C measured 38-40 s on an idle
GPU and **95 s** alongside a live training run. The qualitative result (pre-fix hangs, fixed
terminates) is unaffected, and arms A and B remain directly-observed but transcript-only.

**Do not** grep the shared `juniper-cascor/logs/juniper_cascor.log` for the completion marker: the
live service rotates it, so a `0` means "rotated", not "never completed" — which inverts the
finding this note establishes.

---

## 9. §5 correction — L-1 is live, and L-3 must not be deleted (2026-08-14, post-merge)

§5 filed L-1…L-4 as "all inert today" from a **static** read of the budget path. Re-derived
against the preserved arm C log, two of the four rows were wrong — one in each direction. The
§5 table above is left as written; this section supersedes it.

| # | §5 said | actually | disposition |
| --- | --- | --- | --- |
| L-1 | Inert | **Live on the direct CLI** — the configured budget is discarded for the initial output pass | **FIXED** (cascor#522) |
| L-2 | "the argument is dead" | **Wrong** — `max_epochs` is consumed; it is only `grow_network` that never receives it | Re-scoped + documented in code |
| L-3 | Dead; "delete outright" | **Not dead** — it is the C2b/Q1 snapshot-compat attribute | **Recommendation WITHDRAWN** |
| L-4 | Inert | unchanged | Still filed |

### 9.1 L-1 is live

`fit` resolves `max_epochs = (max_epochs, self.output_epochs)[max_epochs is None]`
(`cascade_correlation.py:1882`) and spends the result on the **initial** output-layer pass
(`:1891`). A non-`None` argument therefore *wins over* the config. `solve_n_spiral_problem`
passed the module constant, so the W-11 override never reached that pass — while every
per-round pass inside `grow_network` reads `self.output_epochs` directly and did honour it.

The preserved arm C log proves it in that run's own evidence. YAML: `training.params.max_epochs: 100`.

| pass | budget source | epochs reached |
| --- | --- | --- |
| initial (`fit` → `train_output_layer`) | `_SPIRAL_PROBLEM_OUTPUT_EPOCHS` | **10000** |
| per-round #1 (`grow_network`) | `self.output_epochs` | 100 |
| per-round #2 (`grow_network`) | `self.output_epochs` | 100 |

`Starting main training loop with max_epochs: 10000` where the YAML asked for 100. The initial
pass ran **17:49:18 → 17:49:36 — ~18 s of a ~40 s run** — with the loss flat at `0.203637` from
roughly epoch 150 on. Same function, same run, two different budgets.

This is a **measured mechanism, not a resurrection of F-P1-3b.** F-P1-3b claimed a structural
compute ratio inferred from runs that never finished; this is one identified call site, measured
from a completed run's own log. It says nothing about a CLI-vs-service ratio, and §6's rule stands.

Two repo-internal specifications were already explicit about the intended semantics, which is why
this counts as a defect rather than a preference:

- `main.py:246` — `_W11_TRAINING_KEY_MAP` maps the YAML's `max_epochs` onto `output_epochs`
  precisely so it can bound this pass: *"C2b semantics: TrainingParams.max_epochs is the initial
  output-training pass budget"*.
- `manager.py:1614-1637` — `derive_epochs_cap` models the run as
  `output_epochs + effective_iterations * (candidate_epochs + output_epochs)`, i.e. "one initial
  output-training pass" costing `output_epochs`.

Fixed in **cascor#522**: `spiral_problem.py:1348` now passes `self.output_epochs`. Pinned by
`src/tests/unit/test_l1_spiral_output_epochs_budget.py`, verified to fail against the pre-fix
source. `solve_n_spiral_problem` has no non-test caller outside the direct CLI, so the service
path is untouched.

### 9.2 L-2 was mis-scoped

`max_epochs` is **not** dead: `:1891` consumes it. What is true is narrower — it is not forwarded
to `grow_network`, whose per-round passes read `self.output_epochs`. The asymmetry is real and now
carries a comment at the resolution site rather than being silently surprising.

It is also not purely a CLI concern: `max_epochs` is in the service's
`TrainingLifecycleManager._FIT_KWARGS`, so an explicit PATCH can still split the initial pass from
the per-round passes. Whether an explicit `max_epochs` *should* re-budget the per-round passes is
an open semantic question. It was deliberately not settled inside a fix PR — forwarding it would
change service behaviour and is golden-suite-visible.

### 9.3 L-3 must not be deleted

§5's "deleting L-3 outright" would **break the build**. `epochs_max` is not dead code that nobody
noticed; C2b/Q1 already retired it as an *input* while deliberately keeping the attribute:

- `snapshot_serializer.py:354` writes `config_group.attrs["epochs_max"]`, and
  `test_snapshot_serializer.py::test_epochs_max_roundtrip` asserts `loaded.epochs_max == 777`.
- `test_c2b_epochs_cap_and_surfaces.py:136` asserts
  `getattr(lifecycle.network, "epochs_max", None) is not None  # legacy attribute still exists (snapshot compat)`.

`cascade_correlation.py:714` **is** that snapshot-compat attribute, and "the engine never reads it"
is already the documented intended state (`manager.py:1618-1625`), not a latent defect. The 1e11
sentinel reads alarmingly, but nothing consults it — which is the point of the C2b design, since
the reported cap is now derived from the granular limits instead.

**Method note.** Both errors came from reading the budget path statically and stopping at the
first plausible conclusion — L-1 looked inert because a nearby argument looked dead, and L-3
looked dead because its assignment has no reader in that one module. Both dissolved on contact
with the run's own log and a repo-wide grep. The same lesson as F-P1-3b, one level down: a
static read is not a measurement either.
