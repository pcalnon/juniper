# Tensor-hash probe — cascor#572 / #582 parity discriminator

**Run date**: 2026-08-28 · **cascor build**: `67d7ea35` + probe commit `42b7699` (local branch
`diag/tensor-hash-probe-572`, NOT for merge) · **suite**: `e-n-profile-cap4` (1 cell, `seed_policy:
fixed`, seed 42, cap 4) · **cell**: `c000-07fb425b`, `config_sha256
a4fc57469df7435be5337f1c34d011ffe2297ff27f57c9d10ed6f2facf8089fb` — byte-identical across arms
because the CLI leg was handed the exact cell the service leg materialised.

Probe: `fit()` is the single entry point both arms reach. The hash sits after validation and
**before the initial output pass**, so it observes pure construction. `raw` = tensor bytes in
order; `sorted` = row-multiset (rows sorted as byte strings), which separates a pure **ordering**
difference from different **content**.

## Result

| tensor | CLI arm | service arm | verdict |
| --- | --- | --- | --- |
| `x_train` | `(800,2) raw=341d9dd0cb9ed0ea sorted=061649c115853d5a sum=-56.125038` | **identical** | same bytes, same order |
| `y_train` | `(800,2) raw=8d92cbeba78a414e sorted=cb3326f2870073da sum=800.000000` | **identical** | same bytes, same order |
| `x_val` | `None` | `(200,2) raw=e0ecd7ffe171d447 sum=50.611530` | **#582 confirmed** |
| `y_val` | `None` | `(200,2) raw=22cd2024464128c0 sum=200.000000` | **#582 confirmed** |

`raw` matching (not merely `sorted`) is the stronger result: the arms receive the same rows **in
the same order**, so neither dataset provenance nor a data-level stream offset is in play.

## The handoff's framing was wrong on a load-bearing point

Both #572 and #582 carry this sentence: *"Both arms already differ at iteration 0 (CLI loss
0.239217 / acc 0.5787 vs service 0.240292 / 0.6088), so the difference is present at construction
or at the first output pass."* This run reproduces those exact numbers — and shows the inference
does not follow, for two independent reasons.

**1. `Iteration 0` is a POST-candidate checkpoint.** The CLI log's own ordering:

```
fit:1990                  Initial - Train Loss: 0.246147
_add_best_candidate:5096  Adding best candidate ... at iteration 0
_retrain_output_layer     Full Network Training Loss after Epoch 0, Train Loss: 0.239217
validate_training:5644    Iteration 0 (no val data) - Train Loss: 0.239217, Train Acc: 0.5787
```

`validate_training: Iteration 0` runs **after** the first candidate has been trained, selected and
installed, and after the output layer has been retrained. It is not a pre-training reading.

**2. The genuinely pre-candidate checkpoint is IDENTICAL on both arms.**

| checkpoint | CLI | service |
| --- | --- | --- |
| Initial Train Loss | 0.246147 | **0.246147** |
| Initial Train Accuracy | 0.5138 | **0.5138** |

Identical to every printed digit. Same data, same network initialisation, same initial output
pass. The arms do not diverge at construction and do not diverge at the first output pass.

## Where they actually diverge

The first divergence is inside the **first candidate round** — and it is small and structured:

| | CLI | service |
| --- | --- | --- |
| winning candidate | `candidate_index=7` | `candidate_index=7` — **same winner** |
| its correlation | `0.09112932150459425` | `0.09099080889819966` |

Same winning index out of 8 candidates, correlation differing at the **4th significant figure**
(~1.5e-3 relative). Post-retrain the arms read 0.239217 vs 0.240292.

## What this settles, and what it does NOT

**Settled — construction of the DATA is exonerated.** Dataset provenance and any data-level
ordering difference are ruled out by `raw` equality on both training tensors. Network
initialisation is ruled out by the identical initial output pass. Nothing needs to be built to
pin the dataset or re-derive its seeding.

**Settled — #582 is real and observed directly**, not inferred: `x_val is None` on the CLI while
the service carries a promoted `(200,2)` split. The two arms therefore compute different
early-stopping and patience signals, and their reported accuracies are not like-for-like (the CLI
prints `Iteration 0 (no val data)`).

**NOT settled — #572 is not exonerated by this probe.** The probe's stated dichotomy ("hashes
match ⇒ #582 is the whole story") conflates *data identity* with *RNG-stream identity*. Those are
different claims. The tensors are identical, yet the arms still differ from the first candidate
round onward, which is exactly where `_seed_random_generator`'s draw from the global stream would
first show up. A candidate-side probe (stream position + candidate initial weights at round 0) is
what would separate "different candidate init (#572)" from "float-reduction nondeterminism across
forked workers". This probe cannot, and should not be read as having done so.

**Caveat**: one pair, one cell, cap 4. The identity results (`raw` equality, identical initial
pass) are robust to that — they are exact equalities, not statistics. The correlation-difference
magnitude is a single observation and should not be treated as a characterised effect size.

## Follow-up probe, 2026-08-29 — #572 CONFIRMED, and it is not float noise

The question left open above ("different candidate init (#572)" vs "float-reduction
nondeterminism across forked workers") was settled by a second probe on the same harness: promote
`_seed_random_generator`'s existing `verbose` roll-count line to INFO with the seeder's name
(commit `3a8f8ea`, same diag branch).

`_initialize_randomness` calls `_seed_random_generator` **four** times on this host — `np.random.seed`,
`random.seed`, `torch.manual_seed`, and `torch.cuda.manual_seed` (CUDA is available). Each call does:

```python
seeder(seed)
random_sequence = random.randint(0, max_value)   # ALWAYS the global `random` module
self._roll_sequence_number(sequence=random_sequence, ..., generator=generator)
```

Candidate 0, one growth round:

| call site | CLI | service |
| --- | --- | --- |
| `np.random.seed` | **96** | **27** |
| `random.seed` | 26 | 26 |
| `torch.manual_seed` | 90 | 90 |
| `torch.cuda.manual_seed` | 99 | 99 |

Aggregate over the complete record — 8 candidates × 4 rounds × 4 sites = **128 lines per arm**,
matching the raw log count exactly (no truncation):

- **All 63 distinct `manual_seed` (seed, roll) pairs are identical across arms** (`diff` exit 0).
- `seed`-labelled pairs: 38 shared, 26 service-only, 25 CLI-only — consistent with `random.seed`
  (32 (cand, seed) combinations) always matching, plus a few coincidental collisions in the 0–100
  roll range, and `np.random.seed` otherwise differing.
- **The derived candidate seeds are identical across arms in every case** — seed derivation is not
  the problem.

Exactly the one call site whose roll is drawn *before* `random` is re-seeded diverges; every site
after the re-seed agrees. At site 1 `random.randint()` reads whatever position the **process** left
the global module in, and a long-lived uvicorn worker and a fresh `python main.py` do not share that
history. Numpy's generator is therefore rolled a different number of times for the same seed —
[cascor#572](https://github.com/pcalnon/juniper-cascor/issues/572)'s title, reproduced.

This is not service-vs-CLI specific: any two processes with different `random` histories diverge,
including the same service having handled a different number of prior requests. Cross-arm parity is
one visible symptom of a general reproducibility defect, and it is consistent with #530 (a pinned
seed does not pin numpy).

**Fix direction**: `_seed_random_generator` should draw the roll count from the `generator` it was
handed, never from a hard-coded `random.randint`, so the count is always a function of the seed just
set. That moves every numpy-drawn candidate initialisation, so it is a behaviour change and should
be sequenced with the partition/tier decision rather than landed alone.

**Probe-design note for the next reader**: labelling the sites by `seeder.__name__` collapsed two
pairs — `np.random.seed` and `random.seed` are both `seed`, and both torch seeders are
`manual_seed`. The aggregate `seed`-site counts above are muddied by that; the per-candidate ordered
reading and the unambiguous `manual_seed` result are what carry the conclusion. A future probe
should label by call-site index, not by function name.

## Reproduce

```bash
# service leg (pinned to the probe worktree via ml#1412's knob, so the primary stays free)
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_EXP_CASCOR_SRC_DIR=<probe-worktree>/src \
  python util/experiments/run_suite.py --suite util/experiments/suites/p4/e-n-profile-cap4.yaml

# CLI leg — ONLY after the service leg finishes: 2026-08-14_r5_stack_up.bash resolves
# "newest run dir carrying a ports.json", so a service leg still up re-points the CLI arm
# at the wrong data service.
bash util/ad-hoc/2026-08-14_r5_stack_up.bash            # -> DATA_URL
bash util/ad-hoc/2026-08-17_h2h_thread_probe.bash <probe-worktree>/src \
  <suite-dir>/cells/c000-07fb425b/experiment.yaml <OUT_DIR> <DATA_URL> 900 default
bash util/experiment_stack.bash --down <RUN_ID>         # by RUN_ID, never --all-mine
```

`util/ad-hoc/2026-08-21_h2h_paired_campaign.bash` was **not** usable here: its pre-flight derives
the service arm's SHA from `${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor` (the primary) and refuses
when it differs from the CLI arm's worktree. ml#1412 added `JUNIPER_EXP_CASCOR_SRC_DIR` but did
not update this caller, so a campaign pinned to a worktree still fails that equality check.
