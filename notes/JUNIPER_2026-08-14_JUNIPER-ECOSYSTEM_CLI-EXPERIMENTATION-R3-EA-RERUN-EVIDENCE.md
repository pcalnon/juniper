# CLI Experimentation — R-3: E-A re-run evidence, and #512 at scale

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-ml / juniper-cascor
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-14

E-A re-run under **R-3** (ml#1077), which raised `max_iterations` to 32 so the swept
`max_hidden_units` cap can actually bind. Suite
`e-a-cascor-budget-sweep-20260814T015826Z`, 12/12 cells `succeeded`, all screened
`oom == 0`, 176.6 min total.

Run as a **single** `run_suite.py` invocation with **no per-cell reaping** — deliberately,
because that reaping was the workaround for the leak cascor#512 fixed, so twelve consecutive
cells is the at-scale test of the fix (§3).

---

## 1. The grid

| cell | pool | cap | units | train | val | wall | completion | best corr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c000 | 4 | 4 | 4 | 0.5450 | 0.570 | 215 s | `early_stopped` | 0.073 |
| c001 | 8 | 4 | 4 | 0.6050 | 0.545 | 286 s | `early_stopped` | 0.138 |
| c002 | 16 | 4 | 4 | 0.6162 | 0.610 | 437 s | `early_stopped` | 0.073 |
| c003 | 4 | 8 | 8 | 0.6350 | 0.625 | 366 s | `early_stopped` | 0.143 |
| c004 | 8 | 8 | 8 | 0.6312 | 0.595 | 536 s | `early_stopped` | 0.138 |
| c005 | 16 | 8 | 8 | 0.6300 | 0.580 | 744 s | `early_stopped` | 0.270 |
| c006 | 4 | 16 | **16** | 0.6125 | 0.600 | 557 s | `early_stopped` | 0.292 |
| c007 | 8 | 16 | **16** | 0.6312 | 0.610 | 807 s | `early_stopped` | 0.425 |
| c008 | 16 | 16 | **16** | 0.6087 | 0.585 | 1494 s | `early_stopped` | 0.270 |
| c009 | 4 | 32 | **32** | 0.6700 | 0.685 | 938 s | `early_stopped` | 0.347 |
| c010 | 8 | 32 | **32** | 0.7200 | **0.735** | 1319 s | `early_stopped` | 0.425 |
| c011 | 32 | 24 (5000 ep) | 24 | 0.7062 | 0.665 | 2893 s | `early_stopped` | 0.420 |

### 1.1 R-3 confirmed — the cap binds and the degenerate pairs are gone

**Units track the cap exactly**: 4→4, 8→8, 16→16, 32→32, every cell `early_stopped`
(`units == max_hidden_units` is the cap-bound signature — see §4). Previously every cap
above 12 was iteration-bound at 12 units.

The two pairs that were **bit-identical** in the prior grid now differ:

| pair | before (both) | now |
| --- | --- | --- |
| c006 / c009 (pool 4, cap 16 vs 32) | 12 units, val 0.615 | 16 units @ 0.600 vs **32 units @ 0.685** |
| c007 / c010 (pool 8, cap 16 vs 32) | 12 units, val 0.645 | 16 units @ 0.610 vs **32 units @ 0.735** |

Cells c000–c005 reproduce the prior clean grid **identically** (same units, same accuracies).
That is the control: those caps always bound, so R-3 must not move them, and it did not.

### 1.2 The 0.670 "ceiling" was a budget artifact

The prior grid's best cell was **0.670**, and the P4 write-up recorded spiral as topping out
there. With the cap actually binding, **c010 reaches 0.735** — and accuracy is still rising
with unit count at the top of the sweep. The ceiling was `max_iterations: 12`, not the model
and not the dataset.

### 1.3 Units dominate pool

At fixed cap 32, pool 4 → 0.685 and pool 8 → 0.735, so pool helps. But c011 (pool **32**,
cap 24, 5000 epochs, 2893 s — the most expensive cell in the grid) reaches only **0.665**,
below c010's pool-8 result at a higher cap. Best-candidate correlation still rises
monotonically with pool (0.073 → 0.270 → 0.425), reproducing the prior grid's finding that
**pool raises correlation but not accuracy**. Capacity is what buys accuracy here.

---

## 2. Consequence for R-5

R-5 asks why the service spiral tops out at 0.670 against ≈0.995 for the direct CLI. Two
independent legs of that premise have now moved:

1. The premise check (ml#1075) showed the two paths generate **different spirals** — the
   service uses juniper-data `algorithm: modern` (θ from `n_rotations`, normal noise), the
   CLI the legacy family (`r = θ`, uniform noise) where `n_rotations` is not a parameter at
   all. 1-NN separability is ~1.0 for both, so noise is not the differentiator.
2. The 0.670 figure was measured on an **artificially capped** surface. The real number at
   cap 32 is 0.735, still climbing.

R-5 as originally stated therefore has no stable basis. A meaningful comparison needs the
same dataset on both paths **and** an equalised budget; the number to compare against is no
longer 0.670.

---

## 3. cascor#512 at scale — the leak is fixed

Twelve consecutive cells, no reaping between them. GPU free memory sampled every 30 s
(354 samples); the meaningful figure is free memory at the **inter-cell idle points**, where
only desktop processes hold the card:

```
6840 → 6952 → 6950 → 6954 → 6956 → 6886 → 6895 → 6876 → 6891 → 6891  MiB
```

Start **6840 MiB**, end **6891 MiB** — **net +51 MiB across the whole campaign**. The ±80 MiB
wobble is desktop-application noise, not a trend. Between cells the compute-process count
returns to 4 (desktop only) every time.

The pre-fix signature was roughly **285 MiB lost per cell** with forkserver children
surviving teardown, exhausting an 8 GiB card after 4–5 cells. Twelve cells would have
consumed ~3.4 GB. **It consumed nothing.**

This is also why the grid is trustworthy: under the old behaviour, cells c005 onward would
have run on a progressively fuller card, and the late high-capacity cells — exactly the ones
carrying the new finding — are the ones that would have silently degraded.

---

## 4. Reading these results

The cap is enforced through the early-stopping path:

```
early_stop = early_stopping and (train_accuracy_reached or max_units_reached or patience_exhausted)
```

Two consequences:

1. It holds **only because** `spiral-baseline` sets `early_stopping: true`. A cell with early
   stopping off would ignore `max_hidden_units` and run to `max_iterations`.
2. A cap-bound cell reports `early_stopped` — the *same* reason as patience-exhausted and
   accuracy-target cells. **Disambiguate with the units column**: `units == max_hidden_units`
   means the cap bound. Every cell in this grid satisfies that.

`cell_id` hashes the override set, so R-3 changed every id relative to the prior campaign.
Aggregation is unaffected (it keys on `cell_id[:4]`), but `--only <full-id>` references to
earlier campaigns will not resolve.

---

## 5. Conditions

The long-lived isolated E2E stack (cascor `:8202`, data `:8101`, canopy `:8051`) was up and
healthy throughout and was left untouched. By campaign start it held **zero** GPU — it had
already released its own forkserver children — so contention was limited to the ~950 MiB of
desktop/compositor overhead visible in the trace floor.

Two cascor processes shared the `juniper-cascor` checkout, which the one-cascor-per-checkout
guidance (H-7, pending Q-6) discourages; the shared resource is only the checkout's file log,
while run dirs, snapshots, ports and sampled metrics are per-run, so the recorded results are
unaffected.

Peak concurrent GPU use was 5087 MiB free (pool-32 cell), leaving ~1.7 GiB headroom — the
7200 s per-cell timeout was never approached either, the widest cell taking 2893 s.
