# F-P4-1 Root Cause — the cascor SERVICE path did not train spiral

**Project**: Juniper — CLI Test/Validation/Experimentation Program (P4 follow-up)
**Author**: Paul Calnon
**Date**: 2026-08-10
**Status**: ROOT-CAUSED — fixes: juniper-cascor#504 (fallback fidelity), this repo's staged-spiral driver PR, cascor#505 (candidate-param plumbing, filed)
**Finding**: F-P4-1, raised in [`JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md`](JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md) §4

---

## 1. Symptom (as raised)

At every budget tested — smoke and the full `max_epochs 2000 × max_iterations 12` baseline — a service-mode spiral run completed in 30–50 s with `train_accuracy ≈ 0.505` (chance), 0–1 hidden units, and `metrics_final` at epoch ≈ 2. All 12 E-A cells, the E-B/E-C spiral rows, and retroactively P1.1's certified reference run carry the identical signature. The direct CLI trained spiral hard for minutes on the same machine, and the service path trained staged easy tasks (xor/moon/gaussian) normally. The suspect named at raise time was training-termination semantics around `POST /v1/training/start`.

## 2. Root cause — three stacked defects, none of them the suspected termination semantics

### 2.1 The driver's spiral-only inline path handed cascor a different dataset than configured

`util/experiments/run_experiment.py` staged every generator through `POST /v1/training/dataset` **except spiral**, which passed the juniper-data DatasetSource inline on `POST /v1/training/start`. Cascor's route does not fetch that source: for `generator: "spiral"` it materializes its **in-process fallback** (`api/routes/training.py::_generate_spiral_data`) and silently ignores the `source`/`url`. The run therefore never trained on the juniper-data dataset the config described (1000 points, radius 10, noise 0.05, seeded).

### 2.2 The fallback spiral was parameter-deaf and scale-degenerate

`_generate_spiral_data` read only the legacy `n_per_spiral` key — the driver's `n_points_per_spiral: 500` missed, giving 2×100 = 200 points (the `eval_metrics.n_samples: 200` in every affected `metrics_final.json`) — and ignored `n_rotations`, `noise`, and `seed`. Decisively, it emitted a **unit-radius** spiral (coordinates normalized by 1/(4π)), while both other spiral sources in the ecosystem — cascor's own `spiral_problem` (`_SPIRAL_PROBLEM_DEFAULT_RADIUS = 10.0`) and juniper-data's `spirals` generator (`SPIRAL_DEFAULT_RADIUS = 10.0`) — use radius 10.

### 2.3 Why unit radius kills the cascade: linear-regime candidates against an x-orthogonal residual

Candidate units initialize with `randn × 0.1` weights (`candidate_unit.py:244`, `_SPIRAL_PROBLEM_RANDOM_VALUE_SCALE = 0.1`). On |x| ≤ 1 inputs the tanh pre-activation is ~0.1, so every candidate starts (and stays) in tanh's **linear regime**. After the output layer converges, least-squares orthogonality makes the residual ⟂ every linear function of the inputs — so a near-linear candidate's correlation with the residual is pinned at the output layer's convergence leftover, ≈ 2.7e-4 (observed to three digits in both the live E-A runs and the in-process repro, across different seeds). Gradient ascent improves it by only ~6e-7/epoch; the candidate-level early stop (patience 50, min-improvement 1e-3 — see §2.4) fires unimproved at epoch 50; `grow_network` then breaks `below_threshold` (best 2.7e-4 < adaptive threshold ≈ residual·0.01 ≈ 5e-3) at iteration 1 with `_completion_reason = "below_threshold"` — the "terminates at epoch ≈2" signature. No termination-semantics bug exists: the loop did exactly what a zero-correlation pool asks of it.

Why the contrasts held: xor/moon/gaussian (staged, from juniper-data at healthy scales) have residual structure recoverable in the near-linear regime, so candidates clear the adaptive threshold and recruit; the direct CLI's `spiral_problem` generates at radius 10, where candidates leave the linear regime immediately.

### 2.4 Secondary defect: API candidate params never reach the pool

`candidate_patience: 100` / `candidate_convergence_threshold` are applied to the network by `_apply_params_unlocked` but never threaded into the worker `CandidateUnit(...)` construction — the pool always runs the module defaults (50 / 0.001). Filed as **cascor#505** (not the F-P4-1 blocker; at radius 10 candidates escape well inside 50 epochs).

## 3. Reproduction (decisive experiment)

`juniper-cascor` `util/ad-hoc/f_p4_1_spiral_service_repro.py` (committed in cascor#504) replays the exact service path in-process — route-fallback data, `create_simple_config(2,2)` network, the E-A TrainingParams applied the `_apply_params_unlocked` way, `fit(max_epochs=2000, max_iterations=12, early_stopping=True)`:

| arm | data | result |
|---|---|---|
| A | route fallback, scale ×1 (as shipped) | best corr 0.0007 → `below_threshold` @ iter 1, **0 units**, acc 0.505, 18 s |
| A ×4π | identical but coordinates ×12.566 | corr 0.05–0.39/iter, **12 units**, acc **0.995**, `max_iterations`, 1074 s |

Identical code and params — only the data scale differs. (A CUDA OOM from the candidate seeding path appeared in early runs on the memory-full workstation GPU; it reproduces identically with `CUDA_VISIBLE_DEVICES=` and is environmental noise, not the cause.)

## 4. Fix set

1. **juniper-ml (this repo)** — the driver stages spiral through `POST /v1/training/dataset` like every other generator (`STAGEABLE_GENERATOR_ALIASES` already carried `"spiral" → "spirals"`; cascor's staged Literal accepts it; juniper-data's `SpiralParams` accepts the config's param names verbatim). Experiments now train on the **configured** dataset — radius 10, n=1000, noise, seeded — and the G-6 input-width assert covers spiral.
2. **juniper-cascor#504** — `_generate_spiral_data` honors `n_points_per_spiral`/`n_rotations`/`noise`/`radius`/`seed` (legacy `n_per_spiral` kept) and defaults to radius 10, for the API callers that still hit the fallback.
3. **juniper-cascor#505 (filed)** — thread `candidate_patience`/`candidate_convergence_threshold` into the candidate-pool task payload and construction.

## 5. Program consequences

- E-A's budget surface and the E-B/E-C spiral rows remain **F-P4-1 measurements**; re-running them against the fixed stack is an owner-scheduled follow-up (a real spiral cell now trains for minutes, not 30–50 s — the E-A grid becomes hours of compute).
- P1.1's reference-run metrics tables describe the degenerate fallback dataset, not spiral learning; mechanics validated there (exit codes, artifacts, parity) are unaffected.
- E-B's difficulty ranking gains its spiral slot only after a re-run; expect spiral ≫ checkerboard at the smoke budget.
- The one-screen acceptance smoke for the fix: a spiral-baseline run at reduced budget must show `hidden_units > 0` and `train_accuracy` well above 0.505, with staging visible in the manifest (`g6_shape_check` populated).
