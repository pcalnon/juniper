# Requirements cross-view inconsistency — measured

**Project**: juniper-ml (ecosystem-wide requirements corpus)
**Author**: Paul Calnon
**Date**: 2026-08-26
**Status**: measurement complete; one owner decision open

---

## 1. What was recorded, and what it bought

The v5-1 row of the requirements plan's §11 tracker records, as a finding that forced a design:

> the three view families disagree with each other on the shipped corpus (52 entries by-area vs
> by-repo, 149 by-area vs by-status, by-area carrying a spurious trailing period), so regenerating
> any family from another propagates a defect. The script is therefore **append-only** and
> re-emits entry bodies **verbatim**.

That conclusion is load-bearing. It is why [`util/requirements_consolidate.py`](../util/requirements_consolidate.py) never regenerates a view family from another, and why `--check-roundtrip` asserts only `render(parse(x)) == x`.

The counts were a dated snapshot taken before the v5 `rec` block landed, and **nothing in the repo re-measures them**: `--check-roundtrip` covers the 15 `by-area` files and never reads `by-repo` or `by-status` at all. The disagreement was recorded once, never re-measured, and is ungated.

## 2. Method

[`util/ad-hoc/2026-08-26_requirements_cross_view_diff.py`](../util/ad-hoc/2026-08-26_requirements_cross_view_diff.py) parses all three families from the shipped corpus and compares, per `JR-` id: the heading title, the four metadata fields (`Status` / `Priority` / `Category` / `Owner`), and the full entry body (heading to next heading).

```bash
python3 util/ad-hoc/2026-08-26_requirements_cross_view_diff.py --show 6
```

## 3. Result

The recorded counts reproduce **exactly** — 52 and 149. What they are is not what the wording implies.

| comparison | ids only in one side | metadata field mismatches | title mismatches | body mismatches |
| --- | --- | --- | --- | --- |
| `by-area` vs `by-repo` | **0** | **0** | 52 | 52 |
| `by-area` vs `by-status` | **0** | **0** | 149 | 149 |

All three families carry the same **1,814** entries.

- **Zero id divergence.** Every id present in one family is present in all three.
- **Zero metadata divergence.** `Status`, `Priority`, `Category` and `Owner` agree on all 1,814 entries in all three families.
- The 52 / 149 are **title-and-body diffs on the same ids**, and under normalization (strip trailing `.` / `:`, ignore blank-line and indentation differences) they collapse to **four entries**:

| entry | families | the actual difference |
| --- | --- | --- |
| `JR-ML-DATA-010` | area vs repo, area vs status | one line is `# test_websocket_topology_push.py …` in one family, `test_websocket_topology_push.py …` in the other — a lost `#` |
| `JR-ML-DATA-041` | area vs repo, area vs status | a trailing `---` section rule captured in one family and not the other |
| `JR-ML-ARCH-014` | area vs status | title is ` ```bash ```. ` vs ` ```bash``` ` |
| `JR-ML-OBS-003` | area vs status | `… (high-volume / low-latency …` vs `… , high-volume / low-latency …` |

Every one of the four is punctuation, whitespace, or a markdown artifact. **None is divergent requirement content.** The "spurious trailing period" recorded as a third, separate item is not separate — it is the mechanism of essentially the whole count: `by-repo` has 52 more period-terminated titles than `by-area` (1,803 vs 1,751), which is the 52 exactly.

## 4. What this changes

The recorded conclusion — *"regenerating any family from another propagates a defect"* — is **too strong**. It is true of four cosmetic artifacts, not of 201 divergent entries. The corpus is far more consistent than the note implies: three byte-different renderings of one identical dataset.

Two consequences worth noting, neither of which this document acts on:

1. **The append-only constraint on `requirements_consolidate.py` is more conservative than the evidence requires.** It was chosen against a believed content divergence that does not exist. Relaxing it is not urgent — append-only is a fine property — but the *stated reason* for it is now known to be wrong, and a future maintainer reading that row would over-estimate the risk of touching the views.

2. **The shipped architecture does not match the design.** The plan (§97) describes `by-repo` and `by-status` as *"thin indexes that link into `by-area` — not duplicates … avoids the maintenance trap of three copies of every requirement going stale independently."* What shipped is three copies of every entry body. Three copies is precisely what exists, and the 201 cosmetic diffs are them having drifted — mildly, so far. The design's own stated failure mode is live; it just has not yet cost anything.

## 5. Owner decision

Not taken here, because it rewrites the corpus of record (1,814 entries × 3 families, 31 files):

- **(a) Leave it.** The divergence is cosmetic and harmless today. Record the corrected characterization and move on.
- **(b) Normalize.** One pass stripping trailing `.` / `:` from titles and reconciling the four artifacts, after which the three families agree byte-for-byte modulo layout, and a cross-view gate can be added to `--check-roundtrip` so they cannot drift again.
- **(c) Re-architect to the documented design.** `by-area` stays canonical; `by-repo` / `by-status` become generated thin indexes. Removes the three-copies trap permanently and makes (b) unnecessary, but is the largest change and touches how the corpus is read.

**Recommendation: (b).** It is mechanical, it is verifiable by re-running the tool, and the gate it enables is what stops this from being re-discovered a third time. (c) is the right end state but should be its own decision, not a side effect of a cleanup.

## 6. Reproduction

```bash
python3 util/requirements_consolidate.py --check-roundtrip
python3 util/ad-hoc/2026-08-26_requirements_cross_view_diff.py --show 6
python3 util/ad-hoc/2026-08-26_requirements_cross_view_diff.py --json
```

The first reports `1814 entries, 15 area files, 0 mismatching` — `by-area` only, which is why it never saw any of this.
