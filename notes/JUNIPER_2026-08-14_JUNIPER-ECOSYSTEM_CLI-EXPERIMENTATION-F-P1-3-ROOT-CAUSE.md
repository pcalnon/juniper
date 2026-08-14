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
  `spiral_problem.py:1298` — a **non-daemon** `spawn` process, which is itself parked in its
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
| L-1 | `spiral_problem.py:1311` calls `fit(max_epochs=_SPIRAL_PROBLEM_OUTPUT_EPOCHS)` — the module **constant**, not `self.output_epochs`, which is where the W-11 `output_epochs` / `max_epochs` override actually lands. | Inert |
| L-2 | `fit()` never forwards `max_epochs` to `grow_network`: it is logged at `cascade_correlation.py:1910` and then unused (`:1912`). So L-1 is inert *because* the argument is dead — the effective output-epoch budget arrives via the config object, which does carry the override. | Inert |
| L-3 | `epochs_max` is assigned at `cascade_correlation.py:714` and never read anywhere in that module. Its constant is `_PROJECT_MODEL_EPOCHS_MAX = 100_000_000_000` (`constants_model.py:206`) — a 1e11 sentinel that looks like an unbounded budget but governs nothing. | Dead |
| L-4 | `training.params.early_stopping` is reported by W-11 as service-tier-only and ignored, so the direct CLI always uses `fit()`'s `early_stopping=True` default. Harmless while every config wants it true; silently wrong the first time one does not. | Inert |

L-1 and L-3 are the dangerous shape: two plausible-looking budget knobs that a future
investigator will reach for and that do nothing. Recommend fixing L-1/L-2 together (pass
`self.output_epochs`, and either forward `max_epochs` or drop the parameter) and deleting L-3
outright.

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
| R-5 §5 "no completed direct-CLI run" | **Resolved**; the head-to-head remains open and needs a #514-consistent campaign (§6) |
| L-1 … L-4 | **Filed, not fixed** (§5) |

Artifacts live under the run dir
`~/.local/state/juniper-experiments/20260814T200636Z-dcf8/artifacts/results/` —
`fp13-agg/` (arm A), `fp13-control/` (arm B), `fp13-fix-noplots-2/` and `fp13-fix-postisort/`
(arm C, the latter re-run after isort touched the imports).
