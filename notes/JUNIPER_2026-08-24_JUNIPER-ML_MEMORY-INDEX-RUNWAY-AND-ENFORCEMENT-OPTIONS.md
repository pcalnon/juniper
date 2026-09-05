# `MEMORY.md` runway is ~7 days, not ~32 — and the decision that unblocks it

**Project**: juniper-ml
**Author**: Paul Calnon
**Date**: 2026-08-24
**Status**: Analysis — prepares owner decision #4 (the forward-only cap) and its enforcement surface
**Relates to**: [`JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md) §P0
**Operator surface**: [`docs/REFERENCE.md` § MEMORY.md Index Check](../docs/REFERENCE.md#memorymd-index-check)

---

## 1. The headline

`MEMORY.md` truncates **silently, newest-first**, at 200 lines / 25,000 bytes. The plan's P0
log projected **~32 days** of runway after the 2026-08-19 eviction. Measured today, it is
**~7**.

| | 2026-08-19 (post-eviction) | 2026-08-24 (measured) | Δ | rate |
|---|---:|---:|---:|---:|
| rows | 123 | **137** | +14 | 2.80/day |
| bytes | 16,933 | **20,256** | +3,323 | 665/day |

| Constraint | Headroom | Runway |
|---|---:|---:|
| rows (200) | 63 | 22.5 days |
| **bytes (25,000)** | **4,744** | **7.1 days** ← binding |

## 2. Why the projection was optimistic — two independent errors

**It tracked the wrong cap.** The P0 log's "days to silent truncation" is a **row** projection
("@1.06/day"). The cap that actually arrives first is the **byte** cap. Rows have 22 days of
room; bytes have 7. Every figure in that row of the log is answering a question that was not
the binding one.

**It assumed a rate 2.6x too low.** 1.06 rows/day was assumed; the observed rate since
eviction is **2.80 rows/day**.

Those compound. The result is a projection off by more than 4x, in the optimistic direction,
for a mechanism whose failure mode is **silent**.

## 3. The driver is row LENGTH, not row COUNT

| | bytes/row |
|---|---:|
| corpus mean (all 137 rows) | 144.7 |
| **rows added since eviction** | **237** |

New rows run **1.64x** the corpus mean. That is why the byte cap binds while the row cap
doesn't, and it is precisely what owner decision #4 — a forward-only cap on **new** entries —
was designed to stop. It has not shipped, and the interval since eviction is a clean
measurement of what its absence costs: **665 bytes/day**.

Eviction addressed the *stock*. The flow was never governed, so the stock refilled at 2.6x
the assumed rate.

## 4. "120 bytes" is underspecified, and one reading is unimplementable

Decision #4 is recorded as *120 bytes on NEW entries only*. Measured against the real corpus:

| Part of a row | mean | median | max |
|---|---:|---:|---:|
| link — `- [Title](file.md)` | 90 | 91 | 115 |
| hook — everything after | 55 | 45 | 285 |

- **Whole-line 120 B is not writable.** The link alone averages 90 B and reaches 115 B. A
  120-byte line budget leaves 5–30 B for the hook, and the memory-file naming convention
  (`reference_…`, `project_…`, `feedback_…` slugs) makes the link part incompressible.
- **Hook-only 120 B is generous and correct.** The median hook is 45 B, and only **6 of 137**
  rows exceed 120. It binds exactly the outliers (285, and the five other long hooks) without
  touching normal rows.

**Recommendation: the cap applies to the HOOK, not the line.** Same intent, and it is the only
reading that can actually be satisfied.

## 5. The blocked decision: enforcement surface

The plan's blocker is real — `MEMORY.md` lives at `~/.claude/projects/…/memory/`, **outside
every repo**, so no CI job can reach it. It also has **no git history**, which is why §1's
5-day window had to be reconstructed from the plan's own log rather than measured directly.

| Option | Catches a violation | Cost | Fails how |
|---|---|---|---|
| **A. `util/` linter**, run on demand | only when someone runs it | ~1 file + tests; no new surface | silently — nobody runs it |
| **B. local hook** (`SessionStart`/`Stop`) | every session, automatically | settings.json wiring; per-machine, not shared | silently on a machine that never installed it |
| **C. documented discipline** | never — advisory only | a paragraph | always |

Options A and B are not exclusive: the linter is the mechanism, the hook is the trigger. **A
alone is worth shipping now** (7 days of runway), with B as a follow-up once the linter has
proven its false-positive rate. C is not an option on its own — the file has been under
"documented discipline" the whole time and grew at 2.6x the assumed rate.

**Recommended: A now, B next, and treat C as documentation of A rather than a substitute.**

§6 sharpens why this is not optional: **no stock-side action buys more than ~37 days**, from
an empty file. Governing the flow is the only lever that moves the date at all.

## 6. There is no stock-side fix — the arithmetic forbids it

An earlier revision of this section recommended two "do them anyway" actions. **Both were
checked against the measured rate before being acted on, and neither survives it.** The
correction matters more than the original advice, because it changes what the enforcement
decision *is*: not an improvement, the only lever.

| Stock-side action | Recovers | Buys |
|---|---:|---:|
| trim all six over-120 hooks to 120 B | 461 B | **0.7 days** |
| re-run eviction back to the post-P0 16,933 B | 3,323 B | 12.1 days total |
| **empty the file completely** | 20,256 B | **37.6 days** |

**At 665 bytes/day, the entire 25,000-byte cap is 37.6 days.** That is the ceiling on any
possible eviction, trim, or rewrite — starting from nothing. Every stock-side action is a
rounding error against the flow.

Trimming the six hooks is also a **bad trade on its own terms**. Those hooks are long because
they carry operational hazards: one records *"DO NOT `--resume` attempt 1 … a resume splits
the grid"*, another that a secret read at launch *"diverges silently and is INVISIBLE to any
file-only check"*. Spending that recall to buy **0.7 days** is the wrong direction — and
"demote the detail" only helps if someone reads the topic file, which is the very behaviour
the pointer-follow soak measured at 68.6%.

**So: eviction remains useful for keeping the index legible, and should still be re-run when
it is worth doing — but it must not be mistaken for runway.** Only governing the flow moves
the date, and until it is governed the date is never more than ~37 days out however hard the
file is cleaned.

**Hard rule, unchanged: detail may be demoted; STATUS may not.** A row that records whether
something is open, shipped, or refuted keeps its status even when its detail moves.

If a stopgap is wanted before the decision lands, the honest one is **stop adding rows**, not
**shorten existing ones** — the measured cost is 237 bytes per *new* row.

## 7. Caveat on the measurement

The 2026-08-19 datapoint is taken from the plan's P0 execution log, not from version control —
`MEMORY.md` has no history, so the growth curve between the two points is unknown. The
endpoints are solid; the 2.80 rows/day is an average over 5 days and could be lumpy. It would
have to be wrong by more than 3x to restore the ~32-day projection.

That the file cannot be measured historically is itself an argument for option A: a linter
that records what it saw is the only way this repo ever gets a growth series.
