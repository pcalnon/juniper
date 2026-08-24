# Snapshot dataset-attribution — null-model findings

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-24

**Status**: FINDINGS — measured, reproducible, and **applied**: the second floor of §5 now
ships in `util/snapshot_attribute.py` (schema v2, `--no-cross-dataset-floor` to opt out). No
snapshot was written, moved, or deleted; the probes redirect `JUNIPER_CASCOR_SNAPSHOTS_DIR` so
they cannot grow the archive they measure.

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

| dataset | before | N1 capacity | N2 permutation | N3 cross-dataset | **as shipped** |
|---|---:|---:|---:|---:|---:|
| **xor** | 94 | 94 | 93 | 93 | **93** |
| **circles** | 10 | 10 | 7 | 9 | **7** |
| **spiral** | 20 | 19 | 9 | 4 | **4** |
| **moon** | 5 | 3 | 4 | 0 | **0** |
| **total** | **129** | **126** | **113** | **106** | **104** |

The last two columns differ by 2, and the reason is a correction found while implementing —
see §3.6. The **as shipped** column is the authoritative one.

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

### 3.6 ⚠ A snapshot must not help set the bar it is judged against

Found while implementing, and it changes two verdicts. The N3 script above pooled every
attributed snapshot into each dataset's reference class — **including the snapshot currently
being judged**. That is not merely untidy; it is self-serving in a specific direction.

The measured case is `5af596ef` at 3 hidden units, already familiar from §3.5. Its scores:

```
gaussian 1.000   moon 1.000   circles 0.880   xor 0.725   checkerboard 0.535   spiral 0.515
```

Its own perfect 1.000 was the **highest moon score in the reference class**, so it set moon's
floor to 1.000 — which drove its *own* moon lift to exactly zero, removed moon as a runner-up,
and left circles looking cleanly separated at +0.130. A snapshot scoring a **perfect 1.000 on
moon** was thereby recorded as confidently *circles*.

Excluding a snapshot from its own bar (falling back to the reference class's runner-up) fixes
it: moon's floor drops to 0.875, its own moon lift becomes +0.125 against circles' +0.130, the
separation collapses to 0.005, and the verdict becomes **ambiguous** — the honest answer.

This is why the shipped total is 104 rather than N3's 106. Both rows recovered are cases where
a snapshot had topped a rival's floor with its own score. The shipped `build_cross_dataset_floor`
therefore keeps the runner-up alongside the maximum, and `cross_floor_excluding` applies it.

Note this arrives at §3.5's conclusion from a completely different direction: the tool now flags
`5af596ef` as ambiguous on its own, without anyone having to know it is the unstable network.

### 3.7 A circularity to keep in view

N3's reference class is built **from attributions**, so a wrong attribution contaminates it.
This is bounded, not fatal — xor's floor is set by *circles*-attributed 2–3 unit networks
(0.725–0.775), and xor's separation is total (§3.3) — but it means N3 should not be read as an
oracle. Capacity-banding the reference class (±20 units) shrinks it to as few as ~4 networks
for high-capacity targets and costs xor 17 survivors; that number is small-sample noise in the
floor, not evidence against xor, and is recorded here so it is not mistaken for a result.

---

## 4. What the defensible attribution set now is

**The tool outputs 104; this table says 100, and the gap is deliberate.** The four survivors
are spiral's, and they are rejected here on the capacity argument of §3.4 — they sit at 8–13
hidden units, which the tool's own positive control records as too small to learn spiral. That
is knowledge about the *problem*, not about the score vector, and the tool has no way to encode
it: a floor cannot know that spiral needs more capacity than moon. The four are reported rather
than silently dropped, and a `--min-hidden` run is the honest way to exclude them.

| dataset | before | defensible | basis |
|---|---:|---:|---|
| xor | 94 | **93** | complete distributional separation + a monotone learning curve |
| circles | 10 | **7** | clears every null; loses its weakest members and the two of §3.6 |
| spiral | 20 | **0** | collapses under every strictening; survivors are below the learnability threshold |
| moon | 5 | **0**, and undecidable | see below |
| **total** | **129** | **100** | |

`gaussian` remains structurally unattributable (untrained floor 1.000), unchanged.

**On moon's zero.** The shipped rule withdraws all five, but it does so on a floor set by a
single contested snapshot (§3.5). That is the *conservative* outcome, not a settled one: with
`5af596ef` removed from the reference class the other three clear a 0.875 floor comfortably.
Read moon as **withdrawn pending §3 item 4**, not as refuted. The tool is right to refuse —
refusing is what it does when the evidence will not carry a verdict.

---

## 5. Applied — two floors, not a replacement

Shipped in `util/snapshot_attribute.py`. The untrained null was **not** swapped out; a
candidate must clear **both** floors, which is the same as clearing the stricter one:

- **Floor A** — the untrained null. *Did it learn anything at all?*
- **Floor B** — the cross-dataset empirical null (`build_cross_dataset_floor`). *Did it learn
  THIS rather than something else?*

Floor B costs nothing: it is a second pass over scores the first pass already produced, which
is also why it *cannot* run until the first pass finishes — its reference class is the first
pass's own attributions.

- `--no-cross-dataset-floor` restores the single-floor behaviour, for comparison.
- `SCHEMA_VERSION` is **2**. Rows carry a `floors` object (`untrained`, and `cross_dataset`
  when it applies), and the `reason` names *which* floor bound. A v1 sidecar is still readable
  but its verdicts are not comparable with v2's: a v1 attribution only ever cleared Floor A.
- A snapshot is excluded from the bar it is judged against (§3.6).
- No delete path was added; the AST read-only guard still passes.

### 5.1 Corrected in the same change

`adjudicate`'s floor docstring and the module docstring both cited *"327 snapshots attributed
to checkerboard"* as the measured cost of a p95 floor. **checkerboard has 0 attributions in the
current sidecar**, and the passage contradicted itself on whether those scores sat between p95
and max or above max. The mechanism it argues (max, not p95) is right, is retained, and is what
the regression tests pin; the count is no longer quoted.

The module's `KNOWN LIMITATION — THE NULL IS NOT CAPACITY-MATCHED` section, which named a
capacity-matched null as "the rigorous fix", is replaced by §3.1's measurement showing that it
is not.

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
Expected totals at `--null-size 120`: **N1 126/129, N2 113/129, N3 106/129** — and **104** from
the shipped two-floor path, which differs from N3 by the self-exclusion of §3.6.

The shipped behaviour is pinned by regression tests rather than by a full re-run:

```bash
python3 -m unittest -v tests/test_snapshot_attribute.py    # 44 tests
```

`CrossDatasetFloorTest` and `CrossDatasetReferenceClassTest` are the two new classes. Each
adjudicates the same score vector twice — once with `cross_floor=None`, which *is* the
single-floor behaviour that shipped before — so removing the second floor makes the two arms
agree and the tests fail.
