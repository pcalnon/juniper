# Resident-Hazard Gap Triage — fleet-wide

**Project**: Juniper
**Sub-Project**: juniper-ecosystem
**Author**: Paul Calnon
**License**: MIT License
**Last Updated**: 2026-08-31

---

## 1. What this is

The P5 cut gave all nine governed repos a resident `## Hazards` block. Every one of those blocks
was built with [`util/ad-hoc/2026-08-28_hazard_triage.py`](../util/ad-hoc/2026-08-28_hazard_triage.py),
which reads `AGENTS.md` and ranks what is **already there**. It cannot, even in principle, surface a
directive that was never in the file.

The complementary question — *what is hazard-shaped in the SOURCE and resident nowhere?* — belongs to
[`2026-08-28_resident_gap_scan.py`](../util/ad-hoc/2026-08-28_resident_gap_scan.py), which until
2026-08-31 had only ever been run against juniper-canopy. This document is the first fleet-wide pass.

It is a **triage**, not a decision record for everything it lists: it classifies, cites evidence, and
names what was promoted, what was rejected, and what is blocked on budget.

## 2. Method, and the tool the pass needed

`resident_gap_scan.py` ranks its output by **identifier count**, a proxy for distinctiveness rather
than for danger. Run fleet-wide it returned ~630 raw candidates whose top entries were mostly long
docstrings that happened to name many symbols.

[`2026-08-31_resident_gap_triage.py`](../util/ad-hoc/2026-08-31_resident_gap_triage.py) joins the two
existing tools: the gap scan's *finding*, `hazard_triage`'s four *severity* signals
(prohibition / silent-failure / irreversible / hazard-noun). Output is ranked by score, then by
whether a silence marker is present, then by identifier count.

### 2.1 The positive control, and the design it rejected

The first build scored a **2-sentence sliding window**, on the reasoning that a 3,000-character
`Args:` docstring would otherwise accumulate a prohibition from one paragraph and a silence marker
from an unrelated one, and score as though a single directive carried both. That reasoning is sound
and the design was still wrong.

The control that caught it: cascor's `cascade_correlation.py:1927` — the `max_epochs` /
`output_epochs` split, owner-settled as finding L-2, silent in both directions, and promoted to
cascor's Hazards block by [juniper-cascor#609](https://github.com/pcalnon/juniper-cascor/pull/609).
Scored against cascor's **pre-#609** `AGENTS.md` it must rank at the top.

| Scoring | Result |
|---|---|
| 2-sentence window | score **2**, below threshold, winning window was the BUG-CC-09 tail |
| whole block | score **3**, **rank 1 of 110** |

"Do not *fix* this by forwarding `max_epochs`" and "the residual footgun is real" sit four paragraphs
apart. No small window can pair them. The window build would have missed **the one hazard already
known to be real** — the vacuous-pass class, in a hazard-finder.

So the score is the **block** score, exactly as `hazard_triage` computes it, because that tool is
deliberately *"tuned for RECALL, not precision: a missed hazard costs far more than a false
positive."* The sentence window survives only to choose the snippet printed for the reviewer. False
aggregation across a long docstring is handled by a human reading the printed line — **not** by a
threshold that silently drops real directives.

The control ships as `--self-check` and exits non-zero if the known hazard is missed:

```bash
git -C juniper-cascor show e1b4988c:AGENTS.md > /tmp/pre609.md
python3 util/ad-hoc/2026-08-31_resident_gap_triage.py \
    ../juniper-cascor --self-check --agents /tmp/pre609.md
# SELF-CHECK PASS: cascade_correlation.py:1927 score=3 rank=1 of 110
```

### 2.2 A scan artifact fixed en route

The same pass found `resident_gap_scan.py` filtering only `.git` while globbing `*/**/*.py`. juniper-ml
keeps session worktrees *inside* the repo, so it walked ~60 full copies: **23,120 files, 15,285
"candidates"**, the top three being the same `run_experiment.py` once per worktree. Scoped correctly:
467 files, 311. Fixed in [juniper-ml#1519](https://github.com/pcalnon/juniper-ml/pull/1519)
(`SKIP_DIRS`). Filed as instance 19 of the vacuous-pass class — the inverse shape: not a false PASS
but **one true result multiplied into a false magnitude**, which is worse, because a big number is
trusted for being big.

## 3. Score distribution

285 blocks carried at least one severity signal. 4 is the maximum.

| Repo | s=1 | s=2 | s=3 | s=4 | scored | headroom |
|---|---:|---:|---:|---:|---:|---:|
| juniper-cascor | 84 | 21 | 5 | 0 | 110 | 5,050 |
| juniper-canopy | 65 | 25 | 0 | 0 | 90 | 2,414 |
| juniper-data | 16 | 17 | 0 | 0 | 33 | 1,233 |
| juniper-recurrence | 15 | 5 | 0 | 1 | 21 | 6,741 |
| juniper-cascor-client | 12 | 3 | 3 | 1 | 19 | 1,815 |
| juniper-data-client | 4 | 2 | 1 | 0 | 7 | **486** |
| juniper-cascor-worker | 2 | 1 | 0 | 0 | 3 | **783** |
| juniper-deploy | 1 | 1 | 0 | 0 | 2 | 1,233 |

Two caveats a reader will otherwise trip on:

- **juniper-data's 33 includes 16 duplicates.** That repo ships a dual tree (`juniper_data/` and
  `src/`), so every hit appears twice. Its real count is ~17.
- **canopy scored 90 here against 63 on 2026-08-28, and the rise is correct.** The cut moved ten
  sections *out* of its `AGENTS.md`, so source identifiers that used to have a resident counterpart
  no longer do. **Expect this in every repo that took a cut** — it is plan §1's accepted tradeoff
  surfacing as a number, not a regression.

## 4. Promoted

| Repo | Source | PR | Why it clears the bar |
|---|---|---|---|
| cascor | `cascade_correlation.py:1927` | [#609](https://github.com/pcalnon/juniper-cascor/pull/609) | `max_epochs`/`output_epochs` split; was resident in **juniper-ml's** block while the code lives here |
| cascor | `snapshots/snapshot_serializer.py:290` | [#613](https://github.com/pcalnon/juniper-cascor/pull/613) | a `getattr(..., 0)` default made 27,908 snapshots read as epoch 0 and **nearly justified deleting 27,005 real models** |

Both were verified at source before landing — for #609 that meant following the `output_epochs`
default through four aliases to `_PROJECT_MODEL_OUTPUT_EPOCHS = 10000`
(`cascor_constants/constants_model.py:300`) rather than transcribing juniper-ml's wording.

The residency test that matters is not severity alone but **whether reading the code recovers the
fact**. `snapshot_serializer.py`'s `hasattr` guard looks like defensive over-engineering to anyone
who does not know what the defaults cost; a future tidy-up removing it would read as a
simplification.

## 5. Recommended, but BLOCKED on budget — owner decision required

These four clear the bar on evidence. They are **not** landed, because each target repo's remaining
headroom is at or below the **1,982-char fleet fan-out floor** — the size of the single sweep
(`docs(agents): document the PR base-branch guard`, 2026-08-21) that landed in every repo's
`AGENTS.md` at once, and the exact shape a thin ceiling cannot absorb.

| Repo | Source | Hazard | Headroom | Est. cost | After |
|---|---|---|---|---:|---:|
| cascor-client | `constants.py:49` | APD-CCLIENT-001: urllib3 replays **inside the adapter, where the caller never learns**; no idempotency key anywhere (APD-ECO-001). A retried POST `save_snapshot` writes a duplicate row; a retried DELETE destroys a network another actor recreated. The training POSTs are only *accidentally* safe via cascor's FSM 409 — **any new mutating endpoint inherits the raw behaviour** | 1,815 | ~600 | 1,215 |
| canopy | `components/metrics_panel.py:68` | Python trace names MUST match the JS `findTraceIndex` lookups; a mismatch **silently mis-appends WS points to the wrong trace** | 2,414 | ~450 | 1,964 |
| canopy | `dashboard_manager.py:4166` | F-CANOPY-018/028: a wholesale pin-store replace asserts "not pinned" for every key whose checkbox is not in the DOM, **silently discarding pins made before a reload** | (as above) | ~550 | 1,414 |
| data | `generators/_sequence.py:17` | Windowing one entity at a time, split by **target time not row index**, is what makes Frankenstein-sequence and train-reaches-past-test-cut leakage structurally impossible. A future vectorized rewrite can **silently reintroduce both** | 1,233 | ~500 | 733 |

The Hazards preamble already states the policy — *"Adding a new hazard here is legitimate — ratchet
space out of a reference section in the same PR rather than waiving the budget gate."* Landing these
therefore means a relocation PR per repo, not a one-line append. That is a real piece of work and a
design decision about which reference section goes, so it is recorded here rather than taken
unilaterally.

The data one is the most consequential of the four for a research platform: it protects **train/test
leakage**, and leakage does not announce itself — it inflates every downstream result.

## 6. Rejected, with reasons

Recording rejections matters as much as promotions: an un-recorded rejection gets re-litigated by the
next pass.

| Repo | Source | Score | Why not |
|---|---|---:|---|
| recurrence | `bench/plots.py:267` | **4** | Highest score in the fleet and a **false positive**. A matplotlib axis decision — clip `r2` to an interpretable band, name the worst offender so clipping never hides a result. Scores on "destroys the shared axis", "hides", "worse", "never". Presentational; nothing is destroyed |
| cascor-client | `constants.py:178` | 3 | Real incident (2026-07-10: control WS silently killed after 40s, half-open for 12h+) but the text is a **contract description**, not a directive, and the safe behaviour is already the default (`auto_pong=True`). The directive worth having is narrower — *do not set `auto_pong=False` without handling pings yourself* |
| cascor-client | `ws_client.py:342` | 3 | ERR-14 "do not silently swallow disconnects" is an implementation rule for this module, enforced by the code itself; nothing downstream breaks silently if a reader is unaware |
| cascor | `snapshot_serializer.py:1490` | 3 | "Degrade to V1 rather than fail the whole load" is a deliberate design choice, already implemented and logged at WARNING |
| cascor | `control_stream.py:317` | 3 | C3 liveness tolerance is correct-by-construction and pinned; a reader who never learns it cannot break it |
| data-client | `client.py:304` | 3 | Request-id propagation no-ops without `juniper-observability`; documented **graceful degradation**, and the server generates a fresh id |

The `bench/plots.py` case is the clearest argument for keeping this tool recall-tuned and
human-reviewed: **the top-scoring row in the entire fleet was noise**, and no threshold change would
have separated it from the genuine ones without also dropping cascor's `max_epochs`.

## 7. The residual

**274 rows at score 1–2** are not triaged individually. Reading the sample, they are dominated by:

- the word `WARNING` as a **log level** rather than a caution (the tool demotes the `hazard-noun`
  signal for these when the window is in a logging context — 14 demotions fleet-wide, recorded in the
  `demoted` field, never silently dropped);
- docstring `Args:` / `Returns:` blocks whose parameter prose trips `prohibition`;
- correct-by-construction notes, where the code enforces what the comment describes.

Re-run rather than transcribing:

```bash
python3 util/ad-hoc/2026-08-31_resident_gap_triage.py \
    ../juniper-cascor ../juniper-canopy ../juniper-data ../juniper-recurrence \
    ../juniper-cascor-client ../juniper-data-client ../juniper-cascor-worker ../juniper-deploy \
    --min-score 3 --json /tmp/fleet_triage.json
```

## 8. What this pass establishes

1. **A Hazards block built from `hazard_triage` alone is structurally incomplete.** Both cascor
   promotions were invisible to it, because neither directive was ever in `AGENTS.md`. Every repo's
   block was built that way, so every repo's block has this gap shape.
2. **Cutting widens the gap.** Relocation moves facts out of the resident file, so the resident-gap
   count rises after a cut by construction. The gap scan should be re-run **after** each cut, not
   only before.
3. **Headroom, not size, is what now blocks hazard work.** Four evidenced hazards are un-landed
   because their repos have less slack than one fleet-wide sweep. The budget was designed to stop
   accretion; it also throttles the one category of growth the plan explicitly calls legitimate.

Related: [`SHARED-SESSION-MEMORY-PLAN`](JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md) §P5,
[`P5-CUT-CANOPY-CASCOR-PREP`](JUNIPER_2026-08-28_JUNIPER-ECOSYSTEM_P5-CUT-CANOPY-CASCOR-PREP.md) §7.1
(the exclusion rule), tracker [juniper-ml#1326](https://github.com/pcalnon/juniper-ml/issues/1326).
