# Equities ingest: sizing, download cost, and field availability

**Project**: Juniper
**Sub-Project**: juniper-data
**Author**: Paul Calnon
**Version**: 1.0.0
**License**: MIT License
**Last Updated**: 2026-09-04

Written to settle the **`equities` half of `APD-DATA-018`**, the row left OPEN when the
`csv_import` half shipped in [juniper-data#326](https://github.com/pcalnon/juniper-data/pull/326).
The csv_import half took a **byte** cap. The question here is whether the same unit transfers, and
what a record would contain if the field set were extended.

Every number below is measured on 2026-09-04 by
`juniper-data/util/ad-hoc/2026-09-04_measure_equities_payloads.py` and projected by
`juniper-data/util/ad-hoc/2026-09-04_equities_sizing_matrix.py`, or is a cited published index
count. Where a figure is derived rather than measured, it says so.

---

## 1. The headline: bytes are the wrong unit here, and not by a little

**A byte cap on `equities` would be anti-correlated with the cost it is meant to bound.**

| Request | Wire bytes | Wall time |
|---|---:|---:|
| 1 symbol × 26 years (`since 2000`) | **210 KB** | **~2 s** |
| Russell 3000 × **1 day** | **92 KB** | **1.7–3.2 h** |

The **smaller** request takes **three to five thousand times longer**. Any threshold that admits
the first rejects the second, and vice versa — so a byte cap does not merely bound a different
axis, it bounds the *wrong direction* on the axis that matters.

(The wall-time range is the two independent per-symbol measurements reconciled in the paragraph
below; the conclusion holds at either end.)

The reason is that the ingest cost is **per request**, not per byte. Measured against the Yahoo
chart API with one symbol, varying only the horizon:

| Horizon | Wire (gzip) | Uncompressed | Seconds |
|---|---:|---:|---:|
| 1 month | 1,322 B | 3,663 B | 0.50 |
| 1 year | 8,398 B | 28,541 B | 0.34 |
| 5 years | 36,762 B | 139,113 B | 0.42 |
| since 2000 | 215,505 B | 724,740 B | 0.58 |

**163× the payload costs 1.16× the time.** There is no per-byte term worth modelling in the range
that matters. The unit cost is:

- **Yahoo chart**: ~0.34–0.58 s per request direct; **~1.85 s** through `yfinance`, which adds
  cookie/crumb negotiation and DataFrame construction.
- **SEC EDGAR XBRL** (`companyconcept`): **~0.20 s**, ~10.5 KB per call, **1–2 calls per symbol**
  (`dei:EntityCommonStockSharesOutstanding` first, falling through to
  `us-gaap:CommonStockSharesOutstanding`). SEC's own 10 req/s ceiling is enforced in
  `generator.py` as `_SEC_MIN_INTERVAL = 0.12`.

**Per-symbol total: ~2.1 s measured here; ~4.0 s measured on 2026-09-02** for §1.6 of
[`JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md`](JUNIPER_2026-09-01_JUNIPER-DATA_ASYNC-JOB-PATTERN-DECISION-ANALYSIS.md).
The two disagree by ~2×; the gap is most likely conditioning work and network variance, and it does
not change any conclusion below, because every universe is one to two orders of magnitude over
budget either way. **Where a single figure is needed, the conservative 4.0 s is used.**

Bytes per trading day per symbol, for completeness: **~32 B gzipped wire**, ~108 B uncompressed,
~44 B in the NPZ (10 `float32` feature columns + a `float32` label), 56 B in the pandas frame.

---

## 2. Universe × horizon

Constituent counts are current published figures. **Every one of these indexes holds fewer names
than its title claims** — a detail that matters if a cap is ever expressed as "an index's worth".

| Universe | Symbols | 1 day | 1 month | 1 quarter | 1 year | since 2000 |
|---|---:|---:|---:|---:|---:|---:|
| Dow 30 | 30 | 963 B | 19.7 KB | 59.2 KB | 237.0 KB | 6.2 MB |
| Nasdaq-100 | 101 | 3.2 KB | 66.5 KB | 199.5 KB | 797.9 KB | 20.7 MB |
| **S&P 500** *(the default)* | **503** | 15.8 KB | 331.1 KB | 993.4 KB | 3.9 MB | 103.3 MB |
| S&P MidCap 400 | 400 | 12.5 KB | 263.3 KB | 790.0 KB | 3.1 MB | 82.1 MB |
| S&P SmallCap 600 | 600 | 18.8 KB | 395.0 KB | 1.2 MB | 4.6 MB | 123.2 MB |
| S&P Composite 1500 | 1,503 | 47.1 KB | 989.4 KB | 2.9 MB | 11.6 MB | 308.6 MB |
| Russell 1000 | 1,004 | 31.5 KB | 660.9 KB | 1.9 MB | 7.7 MB | 206.2 MB |
| Russell 2000 | 1,958 | 61.4 KB | 1.3 MB | 3.8 MB | 15.1 MB | 402.1 MB |
| Russell 3000 | 2,923 | 91.6 KB | 1.9 MB | 5.6 MB | 22.5 MB | 600.2 MB |
| Wilshire 5000 | 3,414 | 107.0 KB | 2.2 MB | 6.6 MB | 26.3 MB | 701.1 MB |

**Wall time does not appear in that table because it does not vary along it.** It depends only on
the symbol count:

| Universe | Symbols | Serial wall time (any horizon) | SEC throttle floor alone |
|---|---:|---:|---:|
| Dow 30 | 30 | 2.0 min | 5.0 s |
| Nasdaq-100 | 101 | 6.7 min | 17.0 s |
| **S&P 500** | **503** | **33.5 min** | 1.4 min |
| S&P Composite 1500 | 1,503 | 1.7 h | 4.2 min |
| Russell 2000 | 1,958 | 2.2 h | 5.5 min |
| Russell 3000 | 2,923 | 3.2 h | 8.2 min |
| Wilshire 5000 | 3,414 | 3.8 h | 9.6 min |

*(at the conservative 4.0 s/symbol; halve for the 2.1 s figure.)*

**The default configuration is 67× over the 30 s budget.** `EQUITIES_DEFAULT_MAX_SYMBOLS = None`
means all 503 bundled S&P 500 constituents.

**A parallelism note, not a recommendation.** The SEC throttle floor for the whole Russell 3000 is
only **8.2 minutes** — nearly all the remaining time is serial Yahoo latency, and `generator.py`
passes `threads=False` explicitly. Yahoo is the parallelisable part; SEC is already near its own
ceiling. That changes the shape of any future work but not today's decision: even perfectly
parallel, no full index fits in a 30 s request.

**What fits in the budget**: 30 s ÷ 4.0 s = **7.5 symbols**; at the optimistic 2.1 s, 14.1. The
analysis document's independently-derived crossover was "~7 symbols". Three estimates agree on
single digits to low teens.

---

## 3. Field availability

Assessed against the sources the generator actually uses. **Legend**: ✅ available now at no extra
request · ➕ available, needs a change · 💰 needs a new/paid source · ❌ not available.

### 3.1 Free — already retrieved, or one flag away

| Field | Status | Source | Note |
|---|---|---|---|
| ticker | ✅ | request / constituents CSV | |
| company name | ✅ | `sp500_constituents.csv`, SEC `company_tickers.json` | bundled file covers **S&P 500 only**; other universes need a constituent source |
| date (Y-M-D) | ✅ | chart index | |
| day of week | ✅ | derived from date | free |
| price open / high / low / close | ✅ | chart | already `EQUITIES_FEATURE_COLUMNS` |
| adjusted close | ➕ | chart (`Adj Close`) | **already returned and currently discarded** |
| day's volume, total | ✅ | chart | already a feature |
| **stock splits** | ➕ | chart, `actions=True` | **same request, zero marginal cost.** Verified: AAPL 7:1 2014-06-09, 4:1 2020-08-31. `generator.py` does not currently pass `actions=True` |
| dividends | ➕ | chart, `actions=True` | arrives with splits, free |
| 52-week high / low **value** | ✅ | derived, rolling 252 sessions | already features |
| 52-week high / low **date** | ➕ | same rolling window (`argmax`/`argmin`) | **free** — the window is already computed, only the value is kept |
| total shares | ✅ | SEC `dei`/`us-gaap` | already a feature; see the KO caveat in §3.4 |
| market cap | ✅ | derived (shares × close) | already a feature |
| **reporting date** | ➕ | SEC XBRL `filed` per fact | **already inside the payload the generator downloads** and discards |

### 3.2 Cheap — one extra SEC call per symbol

| Field | Status | Source | Cost |
|---|---|---|---|
| **P/E ratio** | ➕ | `us-gaap:EarningsPerShareBasic` / `…Diluted`, ÷ into close | +1 SEC call/symbol (~48.7 KB, ~0.2 s; 338 facts for AAPL). Requires choosing basic vs diluted and assembling TTM from quarterly facts — the concept returns quarters, not a trailing sum |

### 3.3 Needs a new source

| Field | Status | Where it lives |
|---|---|---|
| calendar / holiday list | ➕ | NYSE/Nasdaq calendars (`pandas_market_calendars`), or inferred from gaps in the series — inference conflates holidays with halts and single-name no-trade days, so it is not equivalent |
| trading pause / halt | 💰 | Nasdaq Trading Halts feed, NYSE notices, LULD bands. **Not present in any daily bar** |
| CEO salary | ➕/💰 | **DEF 14A Inline XBRL** (`ecd:` taxonomy). Machine-readable **only for fiscal years ending on/after 2022-12-16**, and **not for Smaller Reporting Companies**. It is *filing-level* inline XBRL, so it is **not reachable via `companyconcept`/`frames`** — it needs filing retrieval and parsing. Pre-2023, it is unstructured proxy prose |

### 3.4 Not available from any current source

| Field | Why |
|---|---|
| **day's volume at open / high / low / close** (4 fields) | **A daily bar carries one aggregate volume.** Volume attributed to a price point requires decomposing tick/trade data (NYSE TAQ, Polygon, Databento). Closing-auction volume is separately published by exchanges but is not in the daily bar, and is not the same quantity as "volume at close" |
| **available shares (float)** | `dei:EntityPublicFloat` exists but is a **USD market value, annual, cover-page** — not a share count (AAPL: 19 facts, last `val` 3.25e12 USD for FY2025). Yahoo's `floatShares` would carry it, but see the `.info` gate below |
| **CEO tenure** | Not tagged anywhere. Derivable only by parsing 8-K Item 5.02 appointment events, or from a third-party dataset |

### 3.5 A live constraint on anything Yahoo-sourced

**`yfinance.Ticker.info` returns HTTP 401 as of 2026-09-04** — `Invalid Crumb`, then
*"User is unable to access this feature"*. Yahoo's `quoteSummary` endpoint is gated. Every field
that would come from `.info` — `trailingPE`, `floatShares`, `fiftyTwoWeekHighDate`,
`companyOfficers`, `marketCap` — is therefore **unreachable through that path today**.

The `chart` endpoint that `yf.download()` uses is unaffected and works normally. The generator's
existing design already avoids `.info`, which is why this does not currently break anything — but
it does close off the easy route to several fields above, and it is a reason to prefer SEC XBRL
(a stable, documented, rate-limited public API) wherever both could serve.

### 3.6 Other fields worth having, all free

All derivable from data already downloaded, at zero additional request cost: **turnover**
(volume × close), **gap** (open − prior close), **true range / ATR**, **relative volume** (volume ÷
its own moving average), **shares-outstanding delta** (a buyback/dilution signal, from the SEC
series already fetched), **days since last filing** (from `filed`), **sector** and **CIK** (both in
the bundled constituents file, currently loaded but not featurised), and **index-membership flag**.

---

## 4. Recommendation

**Bound `equities` by symbol count, not bytes**, and carry over the rest of the `csv_import`
contract unchanged.

1. **Unit: symbols.** It is the only quantity the cost tracks. `EQUITIES_DEFAULT_MAX_SYMBOLS`
   already exists and already means exactly this — the change is a *value*, from `None` to finite,
   plus honesty about what happens at the boundary.
2. **Value: a single-digit-to-low-teens default.** 7.5 symbols fit the 30 s budget at the
   conservative rate, 14.1 at the optimistic one, and the earlier independent estimate was ~7.
   **10 is the round number inside that range**; it is the owner's call whether to sit at the
   optimistic or conservative end.
3. **Same contract as `csv_import`**, because the failure mode is identical:
   `generators/equities/generator.py:264` is `ordered = ordered[: params.max_symbols]` — a bare
   slice that **truncates silently**, records nothing, and returns a dataset indistinguishable from
   a complete one. Under the 2026-09-04 ruling that is the thing to fix: **refuse with 422 unless
   the caller opts in, then truncate and annotate permanently.** `DatasetMeta.truncation` and
   `InputTooLargeError` already exist and are generator-agnostic; the descriptor needs one new
   `reason` value (`universe_exceeded_symbol_cap`) and `symbols_requested` / `symbols_imported`
   beside the existing byte fields.
4. **A byte cap may still be worth keeping as a second, independent guard** — not as *the* bound,
   but because it is the only thing that would catch a pathological single-symbol payload. If
   added, it should be generous (tens of MB) and expressed as a backstop, so it never becomes the
   binding constraint in normal use.

### What this does not settle

- **Which end of the range** the default sits at (7 vs 14) — a product call about how many symbols
  a default request should return, not a measurement.
- **Whether whole-index requests should be supported at all**, and if so by what mechanism. The
  async-job pattern was considered and rejected on 2026-09-04; Yahoo-side parallelism is the
  remaining lever and would need its own design (it is the majority of the wall time, and SEC is
  already near its published ceiling).
- **Whether any of the §3.1 free fields should actually be added.** They cost nothing to fetch, but
  each one widens `EQUITIES_FEATURE_COLUMNS`, which is a dataset-shape change for every existing
  consumer.
- **The KO gap**: `KO` returns 636 bytes and **zero facts** on `dei:EntityCommonStockSharesOutstanding`
  and 404 on the `us-gaap` fallback, so it gets no shares data at all and its `total_shares` /
  `market_cap` features fill per `EQUITIES_DEFAULT_FUNDAMENTALS_FILL` (default `"zero"`). How many
  of the 503 constituents share that gap was not surveyed here, and a silent zero in a feature
  column is the same class of problem as a silent truncation.

---

## 5. Sources

Measured: `juniper-data/util/ad-hoc/2026-09-04_measure_equities_payloads.py`,
`juniper-data/util/ad-hoc/2026-09-04_equities_sizing_matrix.py`.

Published index counts: [Russell 3000](https://en.wikipedia.org/wiki/Russell_3000_Index) (2,923),
[Russell 1000](https://en.wikipedia.org/wiki/Russell_1000_Index) (1,004),
[Russell 2000](https://en.wikipedia.org/wiki/Russell_2000_Index) (1,958),
[Wilshire 5000](https://en.wikipedia.org/wiki/Wilshire_5000) (3,414 as of 2025-12-31).
S&P 500 = 503, the row count of the bundled `sp500_constituents.csv`.

Regulatory: [SEC Pay Versus Performance final rule](https://www.sec.gov/files/rules/final/2022/34-95607.pdf)
and [SEC small-business compliance guide](https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/pay-versus-performance)
for Item 402(v) Inline XBRL tagging and its effective date.
