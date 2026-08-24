# Snapshot dataset-attribution — null-model findings

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-24

**Status**: FINDINGS — measured, reproducible, and not yet applied to the shipped tool. No
snapshot was written, moved, or deleted; the probes redirect
`JUNIPER_CASCOR_SNAPSHOTS_DIR` so they cannot grow the archive they measure.

Closes the open item *"a capacity-matched null for attribution"* carried by the
2026-08-23 handoff (§3 item 2). The headline is that the stated concern is real but
**small**, and that a different, larger defect sits next to it.

---

## 1. The question

`util/snapshot_attribute.py` decides which dataset a snapshot was trained on by scoring it
against each candidate and requiring the score to clear a **floor** by a margin. The floor is
built by `build_null`, which scores freshly-constructed networks — and a freshly-constructed
cascade network has **zero hidden units**.

The concern on record: that floor is capacity-correct only for zero-node networks and is *too
lenient for grown ones*, because a bigger network partitions the input plane more finely and
permutation-corrected argmax accuracy could rise with capacity for reasons unrelated to having
learned anything.

**First measurement, and it sharpens the concern:** of the 129 attributed snapshots,
**0 have zero hidden units.** They run 1..103, median 58 for xor. The shipped floor is
capacity-correct for *none* of them.

The floors actually used, recovered exactly as `score - lift` from the sidecar:

| dataset | zero-unit floor in force |
|---|---:|
| spiral | 0.572 |
| circles | 0.690 |
| xor | 0.720 |
| moon | 0.890 |

---

## 2. Three nulls, ordered by strictness

Each replays the **unmodified** `adjudicate` over the **stored** scores, so the floor is the
only thing that changes. Same margin (0.05), same gap (0.05).

| null | what it holds fixed | what it destroys | builds |
|---|---|---|---|
| **N1 capacity-matched** | architecture, init scale | all weight information | 120 random nets per architecture |
| **N2 weight-permutation** | architecture, **weight multiset** | only the *arrangement* | 120 permutations per snapshot |
| **N3 cross-dataset empirical** | nothing simulated | — | snapshots attributed **elsewhere** |

N1 answers *"what does an untrained network of this size score?"* N2 removes N1's remaining
assumption — that the null's weights are at *initialisation* scale, when trained weights grow
and larger weights sharpen a sigmoid's boundary. N3 answers the question the archive actually
poses: **what does a network that WAS trained, just not on this dataset, score here?** N3 needs
no simulation, because the sidecar already stores every snapshot's score against every
shape-compatible dataset.

### 2.1 Results

| dataset | shipped | N1 capacity | N2 permutation | N3 cross-dataset |
|---|---:|---:|---:|---:|
| **xor** | 94 | 94 | 93 | **93** |
| **circles** | 10 | 10 | 7 | **9** |
| **spiral** | 20 | 19 | 9 | **4** |
| **moon** | 5 | 3 | 4 | **0** |
| **total** | **129** | **126** | **113** | **106** |

---

## 3. Findings

### 3.1 ⚠ The capacity confound is real but nearly inert — and points the *other* way

N1 kills **3 of 129**. Inspecting the lifts shows why, and it contradicts the hypothesis: at
high capacity the capacity-matched floor is frequently **lower** than the zero-unit floor, so
lift goes *up* (xor at 103 units: +0.265 → +0.275; circles at 14 units: +0.310 → +0.330).

The mechanism: on these 2-D problems a zero-unit network is a linear model, and a good linear
split already scores well after permutation correction. Bolting on 100 cascade units with
*random* weights injects noise features into the output layer, and a random readout over 102
mostly-uninformative columns produces a more arbitrary split — driving the score **toward
chance**, not away from it.

So "a large network scores high by accident" is **not** what inflates these attributions. A
high score at high capacity is *harder* to reach by chance, not easier. The concern as stated
does not survive measurement, and a capacity-matched random null is not the fix.

### 3.2 The real defect: the null asks the wrong question

The shipped floor asks *"did this network learn **anything**?"* Attribution needs
*"did it learn **this** rather than something else?"* Those differ whenever a network trained on
A scores well on B — which is common here, because these six generators are not orthogonal.

The clearest single instance, straight from the sidecar. A snapshot **attributed to spiral**,
7 hidden units, scores:

```
gaussian     0.890      <- its best score
moon         0.835
spiral       0.624      <- what it was attributed to
checkerboard 0.560
xor          0.550
circles      0.510
```

It is attributed to spiral while scoring *worse on spiral than on three other datasets*. It
wins only because spiral's floor (0.572) is the lowest one available. That is floor arithmetic,
not evidence.

### 3.3 xor is solid — by complete separation, not by margin

Under N3 the xor reference class (35 networks trained on something else) has **median 0.540,
max 0.775**. The xor cohort (94) has **min 0.810, median 0.955, max 0.990**.

**Zero cohort members fall at or below the floor.** The distributions do not overlap at all —
the weakest xor snapshot beats the strongest differently-trained network. The one loss (18
units, 0.810 vs floor 0.775, lift 0.035) is simply the tail clearing by less than the margin.

Corroborated independently by capacity, which no floor choice affects: xor scores **rise** with
capacity, 0.921 at ≤10 units → 0.966 at ≥50, plateauing at 0.985. **That is a learning curve,
and a scoring artifact does not produce one.**

### 3.4 ⚠ spiral does not survive, and its "survivors" are not credible either

spiral degrades monotonically as the null tightens: **20 → 19 → 9 → 4**. The collapse is
**not** outlier-driven — excluding the contested network of §3.5 leaves it at exactly 4/20.

Three independent lines all say the same thing:

1. **Capacity is flat, and falling.** 0.642 at ≤10 units → 0.625 at ≥50 (**−0.017**). The four
   networks with real capacity (93, 97, 97, 101 units) post the cohort's *lowest* scores,
   0.624–0.629. The opposite of §3.3's xor curve.
2. **The tool contradicts itself.** `--min-hidden`'s own help text records that **"8 units still
   scored 0.510 on spiral"** — chance. Yet 11 of the 20 spiral attributions sit at ≤10 units,
   and 16 at ≤19.
3. **The four survivors are inside that same dead zone** — 8, 10, 12 and 13 hidden units,
   clearing the margin by 0.012–0.038. By the tool's own measurement they cannot have learned
   spiral.

**No credible spiral attribution remains.**

### 3.5 ⚠ moon is UNDECIDABLE — and it is the same question as the instability item

moon's N3 floor is set by **exactly one** snapshot: `5af596ef`, attributed to *circles*, 3
hidden units, scoring a perfect **1.000** on moon. With it, moon's floor is 1.000 and all 5
attributions die. Without it the floor is **0.875**, and the remaining 3 clear it by
0.070–0.110 and all survive.

That single snapshot is **already flagged as attribution-unstable** by §3 item 4 of the
handoff. Excluding its UUID removes three snapshots from one training run, captured 46 seconds
apart:

| file time | hidden units | attributed to |
|---|---:|---|
| 09:37:07 | 1 | moon |
| 09:37:20 | 2 | moon |
| 09:37:53 | 3 | **circles** |

So two of moon's five attributions *are* that unstable network, and the network that sets the
floor that would kill the other three *is also* that unstable network. **The null-model question
and the attribution-instability question are the same question for moon.** It cannot be settled
from the null alone, and it is reported as undecidable rather than resolved in either direction.

### 3.6 A circularity to keep in view

N3's reference class is built **from attributions**, so a wrong attribution contaminates it.
This is bounded, not fatal — xor's floor is set by *circles*-attributed 2–3 unit networks
(0.725–0.775), and xor's separation is total (§3.3) — but it means N3 should not be read as an
oracle. Capacity-banding the reference class (±20 units) shrinks it to as few as ~4 networks
for high-capacity targets and costs xor 17 survivors; that number is small-sample noise in the
floor, not evidence against xor, and is recorded here so it is not mistaken for a result.

---

## 4. What the defensible attribution set now is

| dataset | shipped | defensible | basis |
|---|---:|---:|---|
| xor | 94 | **93** | complete distributional separation + a monotone learning curve |
| circles | 10 | **8–9** | clears every null; loses only its weakest 1–3 members |
| spiral | 20 | **0** | collapses under every strictening; survivors are below the learnability threshold |
| moon | 5 | **undecidable** | 0 or 3 depending on one snapshot that is itself unstable |
| **total** | **129** | **~101–102** | |

`gaussian` remains structurally unattributable (untrained floor 1.000), unchanged.

---

## 5. Recommendation — two floors, not a replacement

Do **not** swap the untrained null for the cross-dataset one. They answer different questions
and a snapshot should have to clear **both**:

- **Floor A (keep, as shipped)** — the untrained null. *Did it learn anything at all?*
- **Floor B (add)** — the cross-dataset empirical null. *Did it learn THIS rather than
  something else?*

Floor B costs nothing to compute: it is a second pass over scores the tool already produces.
Adding it is what withdraws spiral and quarantines moon while leaving xor and circles standing.

Not done here, deliberately — this is a findings document, and the tool change wants its own
change with its own regression tests (asserting the SPECIFIC verdict, and verified to fail
against the current code first).

### 5.1 Also worth correcting when that change is made

`adjudicate._floor`'s docstring cites *"327 snapshots attributed to checkerboard"* as the
measured cost of a p95 floor. **checkerboard has 0 attributions in the current sidecar**, and
the passage contradicts itself on whether those scores sat between p95 and max or above max.
The direction it argues (max, not p95) is right and is retained throughout this document; the
cited figures should not be quoted.

---

## 6. Reproducing

```bash
conda activate JuniperCascor1          # REQUIRED -- unsuffixed JuniperCascor has broken torch
cd /home/pcalnon/Development/python/Juniper/juniper-ml

# The archive-side facts (no cascor import, no HDF5 opens)
python3 util/ad-hoc/2026-08-24_attribution_arch_profile.py             # capacity profile
python3 util/ad-hoc/2026-08-24_attribution_arch_profile.py --floors    # floors in force
python3 util/ad-hoc/2026-08-24_attribution_arch_profile.py --curve xor # the learning curve
python3 util/ad-hoc/2026-08-24_attribution_arch_profile.py --curve spiral

# N3 -- free, and the strictest
python3 util/ad-hoc/2026-08-24_crossdataset_null.py
python3 util/ad-hoc/2026-08-24_crossdataset_null.py --exclude 5af596ef   # the sensitivity of 3.5

# N1 and N2 -- minutes each; both redirect JUNIPER_CASCOR_SNAPSHOTS_DIR before importing cascor
python util/ad-hoc/2026-08-24_capacity_matched_null.py  --null-size 120
python util/ad-hoc/2026-08-24_weight_permutation_null.py --null-size 120
```

`--null-size 8 --limit-arch 3` (N1) or `--null-size 8 --limit 3` (N2) give a fast smoke.
Expected totals at `--null-size 120`: **N1 126/129, N2 113/129, N3 106/129**.
