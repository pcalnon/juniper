# Requirements cross-view inconsistency — measured

**Project**: juniper-ml (ecosystem-wide requirements corpus)
**Author**: Paul Calnon
**Date**: 2026-08-26
**Status**: measurement complete (2026-08-26); decision taken and shipped 2026-08-29 — see §5

**Operator surface:** [`docs/REFERENCE.md` § Requirements Snapshot Consolidation](../docs/REFERENCE.md#requirements-snapshot-consolidation) — `--check-roundtrip` is by-area only; `--check-views` owns the derived projection decided in §5.

---

## 1. What was recorded, and what it bought

The v5-1 row of the requirements plan's §11 tracker records, as a finding that forced a design:

> the three view families disagree with each other on the shipped corpus (52 entries by-area vs
> by-repo, 149 by-area vs by-status, by-area carrying a spurious trailing period), so regenerating
> any family from another propagates a defect. The script is therefore **append-only** and
> re-emits entry bodies **verbatim**.

That conclusion is load-bearing. It is why [`util/requirements_consolidate.py`](../util/requirements_consolidate.py) never regenerates a view family from another, and why `--check-roundtrip` asserts only `render(parse(x)) == x`.

The counts were a dated snapshot taken before the v5 `rec` block landed, and **nothing in the repo re-measured them**: `--check-roundtrip` covers the 15 `by-area` files and never reads `by-repo` or `by-status` at all. The disagreement was recorded once, never re-measured, and ungated — which is how it survived. (Since §5, `--check-views` closes that hole.)

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

| entry | families | the actual difference | disposition |
| --- | --- | --- | --- |
| `JR-ML-DATA-010` | area vs repo, area vs status | one line is `# test_websocket_topology_push.py …` in one family, `test_websocket_topology_push.py …` in the other — a lost `#` | **repaired 2026-08-29** |
| `JR-ML-DATA-041` | area vs repo, area vs status | a trailing `---` section rule captured in one family and not the other | **repaired 2026-08-29** |
| `JR-ML-ARCH-014` | area vs status | title is ` ```bash ```. ` vs ` ```bash``` ` | **repaired 2026-08-29** |
| `JR-ML-OBS-003` | area vs status | `… (high-volume / low-latency …` vs `… , high-volume / low-latency …` | **repaired 2026-08-29** |

Every one of the four is punctuation, whitespace, or a markdown artifact. **None is divergent requirement content.** The "spurious trailing period" recorded as a third, separate item is not separate — it is the mechanism of essentially the whole count: `by-repo` has 52 more period-terminated titles than `by-area` (1,803 vs 1,751), which is the 52 exactly.

### 3.1 The four repaired (2026-08-29)

Repaired by [`util/ad-hoc/2026-08-29_requirements_artifact_repair.py`](../util/ad-hoc/2026-08-29_requirements_artifact_repair.py), which asserts every target matches exactly once and writes nothing otherwise. Three of the four "titles" were not requirement statements at all — a bare code fence, a bare filename, a truncated blockquote fragment — so each new brief is derived from that entry's **own cited source range**, read rather than invented, with the previous text preserved in `Notes` under the corpus's existing `[… brief repaired …; was: '…']` idiom.

| entry | was | now |
| --- | --- | --- |
| `JR-ML-ARCH-014` | ` ```bash ```. ` | Improved `juniper_plant_all.bash` / `juniper_chop_all.bash`: health polling, port and conda-env validation, /proc-based PID checks, graceful SIGTERM→SIGKILL |
| `JR-ML-DATA-010` | `"""cascade_add WebSocket message must trigger topology broadcast."""` | Phase 3 integration test: a `cascade_add` WebSocket message must trigger a topology broadcast |
| `JR-ML-DATA-041` | `` `juniper_cascor_client/client.py` `` | juniper-cascor-client (Phase 4): add `get_dataset_data()` to `juniper_cascor_client/client.py` |
| `JR-ML-OBS-003` | `>   per the canopy requirements (high-volume / low-latency …` | P5-RC-05 (frontend WebSocket consumption) is STILL OPEN, not deferred — high-volume / low-latency metrics and the bidirectional `set_params` control channel depend on it |

Two **structural** artifacts were repaired alongside them:

- `JR-ML-DATA-041` carried a stray `---` at the end of its body — the only entry in 1,814 that did, not the last entry in its file, and no `by-area` file ends with a rule. A horizontal rule sitting between two entries, now removed.
- `JR-ML-ARCH-014`'s Detail was `# 1. wait_for_health() …`, a comment lifted out of a ```` ```bash ```` fence which, outside that fence, renders as an **H1 inside an H3 entry**. Wrapped in backticks rather than having the `#` deleted: that keeps the source text exact while removing the spurious heading. (`JR-ML-DATA-010`'s equivalent line needed nothing — `by-area` had already dropped its `#`, and that Detail reads correctly as prose. Deleting `ARCH-014`'s would instead have turned the line into an ordered-list item, so the treatments differ because the content does.)

### 3.2 A fifth, found by scanning rather than by the cross-view diff

`JR-ML-TRAIN-054` carried **both** defects — a docstring-shaped brief (`"""Demo backend must produce hidden-to-hidden cascade connections."""`) and a `# Setup: create network with 2+ hidden units` Detail rendering as an H1. It never appeared in the cross-view diff because it is an **intra-entry** defect: all three families agreed with each other, and agreed on being wrong. It was found by grepping the corpus for `^# ` after the four were repaired, and is now `Phase 2 test: the demo backend must produce hidden-to-hidden cascade connections`.

That is the general lesson: the cross-view check finds families disagreeing, never a defect all three share. After this pass the corpus carries **0** stray H1 lines, **0** bodies ending in a rule, and **0** briefs that are bare code fences.

**Not repaired: Detail *selection*.** `JR-ML-OBS-003`'s Detail quotes the first-pass revision line that its own source then supersedes. Choosing better Detail is re-extraction — a different job with a different evidence bar — and this pass only fixed what was enumerable.

## 4. What this changes

The recorded conclusion — *"regenerating any family from another propagates a defect"* — is **too strong**. It is true of four cosmetic artifacts, not of 201 divergent entries. The corpus is far more consistent than the note implies: three byte-different renderings of one identical dataset.

Two consequences follow. Both are acted on in §5; they are stated here as they read at measurement time:

1. **The append-only constraint on `requirements_consolidate.py` is more conservative than the evidence requires.** It was chosen against a believed content divergence that does not exist. Relaxing it is not urgent — append-only is a fine property — but the *stated reason* for it is now known to be wrong, and a future maintainer reading that row would over-estimate the risk of touching the views.

2. **The shipped architecture does not match the design.** The plan (§97) describes `by-repo` and `by-status` as *"thin indexes that link into `by-area` — not duplicates … avoids the maintenance trap of three copies of every requirement going stale independently."* What shipped is three copies of every entry body. Three copies is precisely what exists, and the 201 cosmetic diffs are them having drifted — mildly, so far. The design's own stated failure mode is live; it just has not yet cost anything.

## 5. Owner decision — TAKEN 2026-08-29: option (c), keeping full bodies

The options as framed:

- **(a) Leave it.** The divergence is cosmetic and harmless today. Record the corrected characterization and move on.
- **(b) Reconcile.** Make `by-repo` / `by-status` match `by-area` for the divergent entries, then gate it. Note this is *not* "strip trailing periods everywhere" — that would rewrite ~1,800 titles and would have to rule on whether a title legitimately ending in a period should keep it. Scoping to the divergent entries sidesteps that question entirely.
- **(c) Make them derived.** `by-area` stays canonical; `by-repo` / `by-status` become a projection of it, regenerated and gated. Subsumes (b) — they agree by construction and cannot drift again.

**Decided: (c), with full entry bodies retained** rather than the plan's literal "thin indexes". The plan's §97 rationale was the maintenance trap of three independently-maintained copies, and *derivation* removes that trap; making the files link-only would additionally remove content readers use, which was never the point. So the reading experience is unchanged and the drift mechanism is gone.

**Shipped:**

- `render_derived()` / `check_views()` / `regenerate_views()` in [`util/requirements_consolidate.py`](../util/requirements_consolidate.py), plus `--check-views` and `--regenerate-views` CLI modes.
- `write_all` no longer writes the derived families — `FAMILIES_WRITTEN_BY_WRITE_ALL` is `by-area` alone, so exactly one writer owns each file. Two independent writers is what produced the drift.
- The reconciliation itself: 8 files, all differences whitespace or trailing punctuation, entry counts unchanged, per-file preambles preserved.
- `DerivedViewTest` in [`tests/test_requirements_consolidate.py`](../tests/test_requirements_consolidate.py) — already wired into `ci.yml`.

**Why (c) became available at all:** it was ruled out in v5-1 on the belief that regenerating one family from another "propagates a defect". §3 above measures that as false — the families differ by zero ids and zero metadata fields. The measurement is what unlocked the decision.

**One consequence, recorded deliberately.** The projection adopts `by-area` verbatim, *including* the four entries where by-area's own text is arguably the worse of the two (e.g. `JR-ML-OBS-003` keeps by-area's `(high-volume … the.` over by-status's `, high-volume … the`). Canonical has to mean something; correcting content *in* the canonical family is a separate, deliberate act, not a side effect of making the views consistent. **That act was then taken, 2026-08-29 — see §3.1** — which is why `JR-ML-OBS-003` now reads as a requirement rather than as the fragment quoted here.

## 6. Reproduction

```bash
python3 util/requirements_consolidate.py --check-roundtrip
python3 util/requirements_consolidate.py --check-views
python3 util/ad-hoc/2026-08-26_requirements_cross_view_diff.py --show 6
python3 util/ad-hoc/2026-08-26_requirements_cross_view_diff.py --json
```

The first reports `1814 entries, 15 area files, 0 mismatching` — `by-area` only, which is why it never saw any of this.
