# CLI Experimentation — direct CLI vs service, head-to-head smoke

**Run**: `20260815T001158Z-79fb` (data 8110 / cascor 8230) · 2026-08-14 19:13–19:18 CDT
**Code**: juniper-cascor `main` @ `3857d1e` (post-#514, post-#517, post-#522) · juniper-ml `main` @ `a39be0b`
**Verdict**: **no service-tier penalty and no direct-CLI compute penalty.** On identical data at an
identical budget the two paths agree to **0.00–1.00 pp** on validation accuracy and finish within the
same 35–46 s band.

---

## 1. Why this could not be run before

R-5 §5 named F-P1-3 as the only thing standing between the analysis and a head-to-head. Closing
F-P1-3 (juniper-cascor#517) was necessary but not sufficient — two further blockers had to go:

| blocker | why it broke the comparison | cleared by |
| --- | --- | --- |
| The CLI hung after training under an interactive backend | no completed direct-CLI run existed to compare | cascor#517 (`--no-plots` + backend guard) |
| The CLI ignored the configured output-epoch budget | the two arms could not be put on the same budget — L-1 | cascor#522 |
| `n_rotations` defaulted differently per path (CLI 1, service 3.0) | the two arms were not on the same *dataset* | equalised here, explicitly |

The `n_rotations` split is the one that silently invalidated the historical numbers. The direct CLI's
`_SPIRAL_PROBLEM_NUM_ROTATIONS = 1`, while the whole E-A / E-I service surface was measured at 3.0.
ml#1093 measured that knob alone moving val **0.595 → 1.000** at cap 8. Arm C's `0.960 / 0.970` was
therefore an *easy-spiral* number and was never comparable to the service's 0.595-class figures — the
apparent "CLI beats service" gap was mostly a dataset difference wearing a path difference's clothes.

---

## 2. Design — one config file per arm pair

Both arms of each pair are driven from **the same YAML file**. There is no second document to drift.

`util/ad-hoc/2026-08-14_h2h_smoke_nrot1.yaml` and `..._nrot3.yaml` differ in exactly **4 of 35
keys**: `dataset.params.n_rotations` (the variable under test) plus three labels
(`experiment.name`, `experiment.description`, `dataset.tags`). Every budget key is identical.

| choice | reason |
| --- | --- |
| `n_rotations` set **explicitly** in both arms | the only dataset knob that differs by default; leaving it implicit is what made prior numbers incomparable |
| `algorithm` / `radius` **omitted** | the CLI's `_W11_DATASET_KEY_MAP` carries neither, so it *cannot* send them; omitting means **neither** arm sends them, making equality structural rather than an assumption about juniper-data's default |
| `max_iterations: 32` named anyway | the CLI reports it service-tier-only and ignores it; it is there so the **service**'s growth is cap-bound like the CLI's (`derive_epochs_cap` uses `min(max_iterations, max_hidden_units)`) |
| `outputs.max_wall_seconds: 900` explicit | the driver budget is what actually ends a run; unset silently inherits `spiral-baseline`'s 3600 (the E-I budget trap) |
| `plots: []` | the CLI renders no plot *files* at all, so leaving the service plotting would add client-side work to one side of a wall-clock comparison |
| CLI arms run from a **dedicated worktree** | the parent log is `<checkout>/logs/juniper_cascor.log`; a shared checkout gets rotated out from under the run (how the 2026-08-14 arm evidence was lost) |

---

## 3. Equalisation, proven rather than asserted

**Same data.** juniper-data dataset IDs are content-addressed. After all four runs the service held
exactly **two** datasets:

```
["spiral-1.0.0-7a976ad47ea86fe7","spiral-1.0.0-7c3b48e57fc26a07"]
```

which are precisely the two IDs the service arms recorded. The CLI arms created none — they resolved
to the same content addresses. And the CLI genuinely went to the service rather than falling back
in-process (the F-P4-1 trap):

```
[spiral_problem.py: generate_n_spiral_dataset:548] SpiralProblem: generate_n_spiral_dataset: Using JuniperData service at http://127.0.0.1:8110
```

**Same budget.** From the CLI's own parent log, both arms:

```
CascadeCorrelationNetwork: fit: Starting main training loop with max_epochs: 100, max_iterations: 1000000, early stopping: True
```

`max_epochs: 100` is the YAML's configured value. **Pre-#522 this line read `10000`** — the module
constant — and the initial output pass ran the full 10000 epochs. The highest output-layer epoch
reached in these runs is exactly **100**, matching the per-round passes. This run is therefore also
an end-to-end field verification of the L-1 fix.

`max_iterations: 1000000` is the CLI's network default; with a 2-unit cap and the service's 32, the
**cap binds on both paths**, and both stopped for the same reason.

---

## 4. Results

Cap 2 · pool 4 · `output_epochs` 100 · `candidate_epochs` 50 · patience 50 · lr 0.05 · seed 20260729.

| arm | n_rot | dataset_id | train | **val** | units | reason | wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| service | 1.0 | `…7c3b48e5` | 0.9625 | **0.9700** | 2 | early_stopped | 46.30 s total / 45.31 s drive |
| **CLI** | 1.0 | `…7c3b48e5` | 0.9637 | **0.9700** | 2 | early_stopped | **36 s** |
| service | 3.0 | `…7a976ad4` | 0.6113 | **0.6450** | 2 | early_stopped | 35.46 s total / 35.15 s drive |
| **CLI** | 3.0 | `…7a976ad4` | 0.6212 | **0.6550** | 2 | early_stopped | **35 s** |

**Delta (CLI − service)** — easy: train **+0.12 pp**, val **0.00 pp**. Hard: train **+0.99 pp**, val
**+1.00 pp**.

Service ROC-AUC: easy **0.9958**, hard **0.6078**.

**Internal consistency check.** Both arms show the same dataset-difficulty effect, easy → hard:
service **−32.5 pp**, CLI **−31.5 pp**. The two paths respond to the dataset identically, which is
what makes the near-zero path delta credible rather than a coincidence of one cell.

---

## 5. What this settles

**F-P1-3b is now positively refuted, not merely withdrawn.** It claimed structural direct-CLI compute
overhead (a "~25×" figure was later attributed to it that it never stated). Measured on identical
data at an identical budget, the CLI is **not slower at all** — 36 s vs 46 s and 35 s vs 35 s. The
withdrawal in the F-P1-3 note rested on "no gap was ever measured"; this run measures it and finds
none.

> **Scale qualifier added 2026-08-17.** "Not slower at all" is true *at this cap* and does not
> generalise. The [wide-budget head-to-head](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md)
> measures **1.99 ± 0.21×** at caps 64/128, entirely in the candidate phase — a term that compounds
> per growth iteration and is therefore near-absent at a 2-unit cap. F-P1-3b's specific claim
> (structural, ~25×) stays refuted; "there is no wall-clock difference between the paths" was never
> a safe reading of these two cells and is now known to be wrong at wide budgets.
>
> **Magnitude superseded 2026-08-20.** The `1.99×` was measured pre-#531/#533, when `main.py`
> capped BLAS threads to 2 on the CLI path and the service path was uncapped — worth 1.30× of a
> 1.52× candidate-phase penalty at cap 16. The *direction and the compounding* stand; the *number*
> does not, and the gap on post-#533 `main` is unmeasured. Quote the qualifier, not the ratio.

**There is no service-tier limitation.** This is now the third independent line of evidence, after
ml#1093 (service aces the easy spiral at a small budget) and E-I (service aces the hard spiral given
capacity). The remaining question F-5 raised — is the service tier itself handicapped — is answered
**no** on all three.

**The historical CLI-vs-service gap was dataset, not path.** Arm C's easy-spiral 0.960/0.970 sits
within ~0.1 pp of this run's service easy arm. The service's 0.595-class figures were the *hard*
spiral. Same code, same budget, different data.

---

## 6. Honest limits

- **Smoke scale, one cell per arm, one seed.** A 2-unit cap on a spiral is a deliberately small
  probe. It establishes the absence of a *gross* path gap; it does not bound a small one, and it says
  nothing about behaviour at the 64–128-unit budgets where E-I found the interesting capacity curve.
- **The wall-clock columns are not a like-for-like benchmark.** The service figure is the driver's
  poll-based drive loop (plus dataset create / collect for the total); the CLI figure is whole-process
  wall including interpreter start and dataset fetch. They share no denominator. The defensible claim
  is the band, not a ratio.
- **The `n_rotations` 3.0 arm is floored by design.** At a 2-unit cap both arms sit near chance; that
  arm is a control showing the easy arm's separation is real, not a measurement of the hard spiral.
- **Host state.** The isolated E2E stack's cascor (`:8202`) was up throughout but `STOPPED` / `IDLE`
  (`is_training: false`), so it held GPU memory without competing for compute — these are idle-GPU
  wall times. GPU 981 MiB before → 995 MiB after.

---

## 7. Reproduction

```bash
util/ad-hoc/2026-08-14_r5_stack_up.bash                      # prints RUN_ID / DATA_URL

# service arm (per n_rotations); needs ports.json copied into the arm dir
python util/experiments/run_experiment.py \
    --config util/ad-hoc/2026-08-14_h2h_smoke_nrot1.yaml \
    --run-dir <RUN_DIR>/h2h/svc-nrot1

# direct-CLI arm, SAME config file, from a DEDICATED cascor worktree
util/ad-hoc/2026-08-14_fp13_verify_fix.bash <DEDICATED_SRC> \
    util/ad-hoc/2026-08-14_h2h_smoke_nrot1.yaml \
    <RUN_DIR>/h2h/cli-nrot1 <DATA_URL> 600 -- --no-plots

# the equalisation check that matters
curl -s "<DATA_URL>/v1/datasets?limit=50"                    # expect ONE id per config, shared by both arms

util/experiment_stack.bash --down <RUN_ID>
```

Evidence preserved under
`~/.local/state/juniper-experiments/20260815T001158Z-79fb/h2h/` — both configs, both service
manifests + artifacts, and both CLI parent-log slices (~1.1 MB each, carrying the budget line, the
`Using JuniperData service` line, and the accuracy figures).

Teardown attested: experiment ranges 8110-8139 / 8230-8259 / 8260-8289 all **0 listeners**, **0**
stale lockdirs, **0** reapable orphans, `artifacts/` preserved.

---

## 8. Disposition

| item | status |
| --- | --- |
| Head-to-head (R-5 §5 / F-P1-3 §6 follow-up) | **CLOSED at smoke scale** — no path gap |
| F-P1-3b | **REFUTED** (§5) — was withdrawn for lack of evidence; now measured and absent |
| F-5 "genuine service-tier limitation" | **FALSE**, third independent confirmation |
| L-1 fix (cascor#522) | **field-verified** (§3) — `max_epochs: 100`, initial pass caps at 100 |
| Wide-budget head-to-head (64–128 units) | **CLOSED** by [the wide-budget evidence note](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-WIDE-BUDGET-HEAD-TO-HEAD-EVIDENCE.md) (2026-08-16/17, 6 paired replicates at caps 64 and 128). **Accuracy: this run's finding holds** — +0.75 ± 0.52 pp, no gap worth acting on. **Wall clock: it does not.** §6's refusal to quote a ratio was right for a different reason than it gave: with a shared denominator the direct CLI takes **1.99 ± 0.21×**, wholly in the candidate phase. That term compounds per growth iteration, so a 2-unit cap has almost none of it — which is why the 36/46 s and 35/35 s figures here show no sign of it |
