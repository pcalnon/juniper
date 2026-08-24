# Attribution instability — the five multi-dataset networks

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-24

**Status**: FINDINGS — measured and reproducible. Strictly read-only: the probes open snapshots
with `h5py.File(..., "r")` and never import cascor, so they cannot trigger the unconditional
`create_snapshot()` in `train_output_layer`.

Closes §3 item 4 of the 2026-08-23 handoff: *five networks attribute to more than one dataset
at different growth stages — either retrained on a second dataset (no other record) or
attribution is unstable there.*

**Both explanations are right, for different networks.** Three are scoring artifacts and the
two-floor rule (ml#1306) removes them. One is a real multi-dataset training run. One is
marginal. And the "no other record" clause turns out to be structural, not incidental.

---

## 1. The discriminator

The two explanations leave different signatures:

| | score vector | wall clock |
|---|---|---|
| **retrained** | changes materially — one dataset's score climbs while another's falls | usually a gap; a second run has to be started |
| **unstable** | essentially constant; only the *winner* moves, on floor arithmetic | snapshots seconds apart, one continuous run |

So the tests are the **spread** of each dataset's score along the trajectory, whether peaks are
**ordered and followed by decay** (catastrophic forgetting as training moves on), and the
**inter-snapshot gaps**.

---

## 2. ⚠ The training record does not exist — and this is structural

cascor *does* record dataset swaps: P2-2 persists them under
`history/dataset_swaps/event_{i}` with `before_cfg`, `after_cfg` and `arch_changes`
(`snapshot_serializer.py`, the block documented at ~line 801). That would settle the question
outright.

It is not there. Not for these five, and not for the archive:

> **0 of 500 randomly sampled snapshots carry a `history` group at all** — across every month
> present, 2025-10 through 2026-07. Observed top-level groups are
> `arch, config, [hidden_units,] meta, mp, params, random`. No `history`, no `data`, no
> `provenance`.

`dataset_swaps` lives *inside* `history`, so the container is missing, not just the contents.
**The absence of swap events is therefore not evidence that no swap happened** — it is evidence
that swaps could not have been recorded either way. This is the same shape as the S-2 identity
finding: the question is unanswerable from the archive, and the honest response is to say so
rather than to read absence as a negative.

Everything below is therefore **behavioural inference**, and is labelled as such.

---

## 3. Per-network findings

| network | snaps | span | inter-snap | v1 verdicts | v2 (shipped) | conclusion |
|---|---:|---|---|---|---|---|
| `17de4973` | 173 | 179 s | 1 s | moon 1, spiral 2, indet 170 | **all 173 indeterminate** | **artifact — resolved** |
| `1e9e15a8` | 59 | 58 s | 1 s | moon 1, spiral 2, indet 56 | **all 59 indeterminate** | **artifact — resolved** |
| `5af596ef` | 5 | 137 s | ~35 s | moon 2, circles 1, ambig 1, indet 1 | circles 1, ambig 1, indet 3 | **artifact — resolved** |
| `846587fb` | 5 | 202 s | 55 s | xor 1, circles 3, indet 1 | xor 1, circles 3, indet 1 | **marginal — unresolved** |
| `2537e0f0` | 20 | 11.4 h | 9.4 h gap | xor 2, moon 1, circles 4, ambig 1, indet 12 | xor 2, circles 5, indet 13 | **real multi-dataset run** |

### 3.1 `17de4973` and `1e9e15a8` — artifacts, and near-identical twins

173 snapshots in **179 seconds**, and 59 in **58 seconds** — one snapshot per second, one
continuous growth run each, no gap anywhere. Of 173, **170 were already indeterminate**; the
"instability" was 3 dissenting snapshots (1 moon, 2 spiral) inside a trajectory that otherwise
says *cannot tell*.

**Under the two-floor rule every snapshot in both networks becomes indeterminate.** The
multi-dataset attribution is gone, and with it the puzzle.

They are also near-identical twins — the same attributions at the same capacities (moon at 76
units, spiral at 97), the same scores to three decimals, an hour apart on 2026-04-06. Whatever
produced one produced the other, which is itself evidence for a deterministic scoring artifact
rather than two independent training histories.

### 3.2 `5af596ef` — artifact, and already met in the null-model work

The contested snapshot of
[`…ATTRIBUTION-NULL-MODEL-FINDINGS.md` §3.5–3.6](JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md).
Five snapshots over 137 s, growth 0→4 units:

```
hid  v1                  v2                  circles  gaussian    moon     xor
  0  indeterminate       indeterminate         0.530     0.810   0.885   0.540
  1  attributed:moon     indeterminate         0.680     0.970   0.985   0.530
  2  attributed:moon     indeterminate         0.670     0.980   0.985   0.535
  3  attributed:circles  ambiguous             0.880     1.000   1.000   0.725
  4  ambiguous           attributed:circles    0.840     1.000   1.000   0.740
```

Both moon attributions are withdrawn (moon's floor is 1.000; 0.985 does not clear it), and the
3-unit snapshot becomes ambiguous exactly as the null-model work predicted. **It no longer
attributes to two datasets.**

### 3.3 ⚠ `2537e0f0` — a real multi-dataset run, on three independent grounds

The one network where "retrained" is the better reading:

1. **A 9.4-hour wall-clock gap** mid-trajectory (median inter-snapshot gap: 309 s; max: 33,685 s).
2. **It resumes at the same capacity it stopped at** — session 1 ends at 10 hidden units, session
   2 begins at 10. The network was loaded and continued, not started afresh.
3. **Three sustained, ordered phases with decay** in session 2:

```
time      hid  v2                   circles  gaussian    moon  spiral     xor
05:10:39   10  attributed:xor         0.620     0.730   0.750   0.526   0.980
05:15:33   11  attributed:xor         0.590     0.680   0.720   0.526   0.990
05:19:06   11  indeterminate          0.710     0.570   0.975   0.598   0.660
05:24:11   12  attributed:circles     0.830     0.550   0.985   0.598   0.660
05:28:20   12  attributed:circles     1.000     0.730   0.685   0.557   0.540
05:43:58   14  attributed:circles     1.000     0.940   0.685   0.536   0.550
```

xor holds ≥0.98 across **two** snapshots five minutes apart, then falls to 0.660 and finally
0.540 (**decay 0.440**). moon then holds ≥0.975 across **two** snapshots, then falls to 0.685
(**decay 0.300**). circles rises 0.590 → 1.000 and stays there for four snapshots.

Each dataset peaks in its own window and gives up the lead as the next takes over — while the
network keeps growing (10→14 units) throughout. That is sequential training with catastrophic
forgetting. **Noise does not produce ordered peak-and-decay**, and a single-dataset run does not
produce it either.

**Attribution is not misbehaving here — it is correctly tracking a network whose training set
changed.** Per §2 this cannot be confirmed from the files, so it is stated as the reading the
behaviour supports, not as established provenance.

### 3.4 `846587fb` — marginal, and the honest answer is "not settled"

Five snapshots over 202 s, 55 s apart, monotonic growth 0→4 units. No gap, so no retrain.

```
hid  v2                   circles  gaussian    moon     xor
  0  indeterminate          0.600     0.790   0.580   0.585
  1  attributed:xor         0.700     0.510   0.570   0.855
  2  attributed:circles     1.000     0.500   0.645   0.530
  3  attributed:circles     1.000     0.500   0.620   0.505
  4  attributed:circles     1.000     0.500   0.675   0.510
```

circles reaches 1.000 at 2 units and holds — that part is solid. The xor attribution rests on a
**single snapshot at ONE hidden unit** (0.855, clearing the 0.775 floor by 0.080), which decays
to 0.510 immediately after.

Contrast §3.3: `2537e0f0`'s xor phase is *sustained* across two snapshots at ≥0.98. A
one-snapshot spike at one hidden unit is much better explained by a nearly-linear boundary that
happens to align with xor, then being destroyed as the network fits circles. But it does clear
the bar, and one snapshot is not enough to call it either way. **Recorded as unresolved.**

---

## 4. ⚠ A defect found along the way: an unattributable dataset can DISPLACE attribution

`5af596ef` at 4 units scores **1.000 on gaussian and 1.000 on moon** — both structurally
unattributable (cross-dataset floor 1.000) — and is attributed to **circles at 0.840**.

The known behaviour was that gaussian "can never be an ANSWER". The failure mode is the
neighbouring one: because an unattributable dataset can never win, **the attribution falls
through to a lower-scoring runner-up instead of to a refusal**. A network that scores a perfect
1.000 on moon should not be recorded as circles on 0.840.

Measured archive-wide over the 104 two-floor survivors:

| displacement | count |
|---|---:|
| spiral attributed while **moon** scored higher | 4 |
| spiral attributed while **gaussian** scored higher | 1 |
| **xor (93) and circles (7)** | **0** |

Two things follow. First, the credible attributions are untouched — no xor or circles survivor
is beaten by an unattributable dataset. Second, **all four surviving spiral attributions score
higher on moon than on spiral**, which is a fifth independent line against that cohort, on top
of the four in the null-model findings (flat-to-falling capacity curve, the tool's own
"8 units still scored 0.510 on spiral", survivors inside that dead zone, monotone collapse
across three nulls).

**Suggested guard, not implemented here**: when a snapshot's best raw score belongs to a dataset
whose floor is ≥1.000, the honest verdict is `indeterminate` — "it behaves most like something I
cannot test for" — rather than attribution to the runner-up. That is a behaviour change to
`adjudicate` and wants its own change, its own regression test, and a decision about whether it
should also apply when the unattributable dataset merely ties.

---

## 5. Outcome

| | before | after |
|---|---|---|
| networks attributing to >1 dataset | 5 | **1** (`846587fb`, marginal) + `2537e0f0` where it is correct |
| explained as scoring artifact | — | **3** (`17de4973`, `1e9e15a8`, `5af596ef`) |
| explained as real multi-dataset training | — | **1** (`2537e0f0`) |
| unresolved | — | **1** (`846587fb`) |

The two-floor rule of ml#1306 did most of this work without being aimed at it: three of the five
dissolve because the attributions that disagreed were never above a properly-constructed floor.

**Open, and not closeable from the archive**: whether `2537e0f0` and `846587fb` were literally
retrained. `history` is never persisted (§2), so the record does not exist. Any future run that
wants this answerable needs `save_history=True` on the snapshot path — worth deciding
deliberately, because it is the difference between a future archive that can explain itself and
another one that cannot.

---

## 6. Reproducing

```bash
conda activate JuniperCascor1       # REQUIRED — unsuffixed JuniperCascor has broken torch
cd /home/pcalnon/Development/python/Juniper/juniper-ml

# Trajectories, spreads, ordered peak-and-decay, and v1-vs-v2 verdicts per snapshot
python3 util/ad-hoc/2026-08-24_attribution_instability.py                # all five
python3 util/ad-hoc/2026-08-24_attribution_instability.py --uuid 2537e0f0 --all-rows

# Ground truth attempt: dataset-swap events, provenance and data groups (needs h5py)
python util/ad-hoc/2026-08-24_probe_dataset_swaps.py

# The calibration that makes the above a non-finding rather than a negative finding
python util/ad-hoc/2026-08-24_history_group_census.py --sample 500
```

Expected: the swap probe reports **no** events *and* no `history` group; the census reports
`has a history group: {False: 500}`. Read together, those two say "unanswerable", not "no".
