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

> **CORRECTED 2026-09-05 — this section's original argument was arithmetically inverted.** It
> claimed the expensive request was the *smaller* one in bytes, and therefore that a byte cap would
> "admit the expensive request and reject the cheap one". That is backwards, and it was derivable
> from this document's own tables on the day it was published. The **decision** — cap `equities` by
> symbol count — is unchanged and is now argued from something that does not depend on the
> correlation direction at all. The original text is replaced rather than annotated because it
> shipped into five other places (§1.1) and each needs the same replacement, not the same footnote.

**A byte cap on `equities` cannot be a measurement. It can only be a prediction.**

That is the whole argument, and it survives any correction to the numbers below.

`csv_import` bounds **bytes** because it *has* an input: the upload is in hand, and the cap is a
`stat` (then a read-enforced re-check). `equities` has **no input** — the request is a ticker list
and a date range, and its byte count does not exist until the fetches the cap is meant to prevent
have already been made. A byte cap there would have to be *estimated* from (symbols × horizon),
which makes it a noisier function of the symbol count by construction. The symbol count, by
contrast, is knowable before a single byte moves: `_resolve_symbols` counts the resolved list and
raises `InputTooLargeError` with **zero network calls** (`juniper_data/generators/equities/generator.py`).

The unit of a cap must be something the server can measure **before doing the work**. That is why
the two halves of `APD-DATA-018` took different units, and it is a stronger claim than the one this
section originally made — which rested on a correlation, and got its direction wrong.

### 1.1 What the original argument said, and why it was wrong

| Request | As published | Actually, with a per-request envelope |
|---|---:|---:|
| 1 symbol × 26 years (`since 2000`) | 210 KB | ~215–223 KB (essentially unchanged) |
| Russell 3000 × **1 day** | **92 KB** | **~2.0–3.9 MB** |

The published figure came from a **purely proportional** model —
`2,923 symbols × 32.1 B/day × 1 day = 91.6 KB` — with **no per-request intercept**, in
`util/ad-hoc/2026-09-04_equities_sizing_matrix.py`. But Russell 3000 × 1 day is **2,923 separate
HTTP requests**, each carrying its own response envelope. Fitting an intercept to *this document's
own* horizon table (the two smallest rows, 1 month and 1 year) gives **679 B fixed + 30.6 B/day**,
hence **2.07 MB** for that row — 22× the published figure. The 1-year/5-year pair gives a 1,307 B
intercept and 3.90 MB. Either way the expensive request is also the **larger** one, so bytes are
**positively** correlated with cost here, not anti-correlated.

Two consequences worth stating plainly:

- **A byte cap would not, in fact, have picked the wrong request.** The published sentence claiming
  it would is false. What disqualifies a byte cap is §1's argument — that it is unmeasurable before
  the work — not a correlation that points the other way.
- **The exact envelope is not pinned.** 679 B and 1,307 B are fits to two different pairs of the
  same four rows; an OLS fit over all four gives a *negative* intercept. Any figure quoted to
  three digits here is over-precise. What is robust is the sign and the order of magnitude.

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

**163× the payload costs 1.16× the time** — but read that as an order-of-magnitude statement, not a
measurement. It is the two **extremes** of a four-point series quoted as one ratio, and the series
is **non-monotonic**: 1 year (0.34 s) is *faster* than 1 month (0.50 s), so 1.16× is inside the
sampling noise rather than above it. A re-run reported 156× payload against **0.83×** time — which
points the same way (time is flat in payload) while showing the ratio itself is not repeatable.

What the series does support, robustly, is the qualitative claim: **there is no per-byte term worth
modelling in the range that matters** — wall time tracks the number of *requests*, not their size.
The unit cost is:

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
**~68 B in the NPZ** (16 `float32` feature columns + a `float32` label), 56 B in the pandas frame.

*(Corrected 2026-09-05: this said "~44 B … 10 `float32` feature columns". The matrix went 10 → 16
columns in juniper-data#362, published after the measurement, and §7 of this same document records
that widening — so the document contradicted itself. `NPZ_X_BYTES_PER_ROW = 10 * 4` in
`util/ad-hoc/2026-09-04_equities_sizing_matrix.py` is stale for the same reason.)*

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
- ~~**Whether any of the §3.1 free fields should actually be added.**~~ — **RESOLVED 2026-09-04: all
  six added** in [juniper-data#362](https://github.com/pcalnon/juniper-data/pull/362), matrix 10 → 16
  with existing positions preserved. See §6.
- ~~**The KO gap**~~ — **SURVEYED 2026-09-04. See §6.**

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

---

## 6. Follow-up, 2026-09-04: the free fields shipped, and the KO gap is measured

### 6.1 The six free fields are in

[juniper-data#362](https://github.com/pcalnon/juniper-data/pull/362) added `adj_close`, `dividend`,
`split_ratio`, `days_since_week52_high`, `days_since_week52_low` and `days_since_report` —
`EQUITIES_FEATURE_COLUMNS` goes 10 → 16, with the existing ten holding their positions. The three
underlying dates ship as row-aligned YYYYMMDD arrays (`week52_high_date_*`, `week52_low_date_*`,
`report_date_*`) rather than as feature columns.

Verified live against AAPL 2013–2021: **34 dividends** and both real splits (**7:1 on 2014-06-09**,
**4:1 on 2020-08-31**).

### 6.2 Adding one of them exposed a look-ahead leak that predates it

`days_since_report` came back at **−19 days** on live data. A negative filing age is impossible, and
it was the symptom of a real leak: the SEC shares series was aligned on the **period end** and
forward-filled, so a figure reached every trade date between the period it described and the filing
that disclosed it. **`total_shares` and `market_cap` have been carrying that leak all along**; the
new column merely made it visible. Over the AAPL 2013–2021 window, **325 of 2,266 rows (14.3%)**
carried a negative age.

> **CORRECTED 2026-09-05 — the worked example was false, and it shipped into five files.** This
> paragraph said "Apple's quarter ending 2021-03-27 — not filed until 2021-04-29 — reached every
> trade date in those five weeks." Verified against the real cached payload:
>
> - AAPL's dei series has **no 2021-03 point at all**.
> - The 2021-04-29 filing carries **`end=2021-04-16`** — a **13-day** gap, not five weeks.
> - `end` on this tag is an **as-of date, not a fiscal period end**. SEC's own description is
>   *"as stated on cover of related periodic report"*. AAPL's fiscal Q2 FY2021 did end 2021-03-27;
>   the dei point does not.
> - The **−19** comes from **four 2015–2016 filings** (2015-01-09, 2015-10-09, 2016-01-08,
>   2016-04-08), which tie. 2021's widest gap is **14** days, so 2021 could not have produced it.
> - The genuine outlier is a 10-K/A: `end=2009-10-16` filed 2010-01-25, **101 days**.
>
> The leak, the −19, and the 325/2,266 are **confirmed exactly**. Only the example was wrong.
> Corrected in `juniper-data/juniper_data/generators/equities/generator.py`,
> `juniper-data/juniper_data/tests/unit/test_equities_generator.py` and `juniper-data/CHANGELOG.md`
> by juniper-data#376.

Alignment is now on the filing date, and a point with no `filed` is dropped rather than approximated
by its period end. Post-fix: 0 negative ages, 0 future report dates, coverage unchanged.

**The fix was also incomplete, and its test could not see the gap.** Two facts can share one `filed`
date — an 8-K restating an old quarter is filed the same day as the current 10-Q — and the
de-duplication resolved that tie with an *unstable* sort, keeping the restated old figure on **15
collisions across 9 tickers** (DVA by 10.4%, ADSK — inside the default 14-symbol universe — by
0.26%). Meanwhile `test_shares_are_not_visible_before_they_were_filed` inspected only `report_date`,
never `total_shares`, so a look-ahead in the value itself passed it. Both fixed in juniper-data#376.

*Adding a field that is a function of an existing one is a cheap way to audit the existing one —
and the audit it produces still needs auditing.*

### 6.3 The KO gap: 37 of 503, and a bug that made it look worse

**Census** — `util/ad-hoc/2026-09-04_survey_sec_shares_coverage.py`, all 503 bundled constituents,
three concept tags each:

| Outcome | Count | Share |
|---|---:|---:|
| Shares available | **463** | 92.0% |
| **No shares under either tag** | **37** | **7.4%** |
| Rescuable by `us-gaap:CommonStockSharesIssued` | 3 | 0.6% |

**But 12 of the 463 were broken anyway, by a bug.** SEC answers `200` with
`{"units": {"shares": {}}}` for some filers, and the generator's guard was
`if payload and payload.get("units")` — **that dict is truthy**, so the loop accepted the empty
concept and never tried the `us-gaap` fallback. Twelve tickers had perfectly good data there and got
none of it: **BIIB, CDNS, EXE, GD, GEHC, HUBB, JCI, MDLZ, NXPI, OMC, PNR, PPG**. Fixed in
juniper-data#362 by counting facts instead of testing truthiness.

So the real before/after is **451 → 463 working**, not 463 either way.

**`KO` itself is not a bug.** It, along with 36 others, reports no shares concept to SEC under
either tag — including some large names: **META, SPGI, HCA, HUM, WELL, STZ, RL**. That is upstream
reality, not something juniper-data can fix.

> **CORRECTED 2026-09-05 — "upstream reality" was right, but not permanent, and "37" is not a
> measurement of absence.** Two independent problems with the census this table rests on:
>
> **1. The instrument conflates throttling with absence.** `_facts` in
> `util/ad-hoc/2026-09-04_survey_sec_shares_coverage.py` maps a 403, a timeout, a 404 and an
> empty-units body onto values the verdict cascade treats identically, and — unlike the generator's
> `_sec_get(retries=3)` — it performs **no retries**. At `_SEC_MIN_INTERVAL = 0.12` (≈8.3 req/s)
> over ~1,509 requests, a single throttle sends a ticker to "NO SHARES ANYWHERE". So **37 cannot be
> separated from "37 minus however many were throttled"**. Re-measure with an instrument that
> distinguishes the three before quoting this figure again.
>
> **2. The gap is a *regression*, not a property.** A June-2026 `companyconcept` cache on this
> machine holds KO's **same 71 dei facts** that `companyfacts` returns today — i.e. `companyconcept`
> *did* serve KO, three months earlier. Across the probed tickers, the ones rescued at the first two
> rungs are **exactly** the ones with a June cache entry (set equality, zero symmetric difference).
> Population-level: no-data went **15 → 37** between June and September against a constituents CSV
> unchanged since 2026-06-03.
>
> **3. The published mechanism is inverted.** The "multi-class filers tag shares per share class, so
> the facts carry a dimension and are excluded" story does not fit its own example: **KO is
> single-class** and its rows carry **no dimensional keys at all**. Meanwhile the three genuine
> multi-class filers (GOOG/GOOGL, NWS/NWSA, FOX/FOXA) all resolved to *undimensioned* series in
> June — the mechanism's predicted victims were never hidden. The one name the story does fit,
> **STZ**, is the one it failed to rescue.
>
> **Consequence for the rescue ladder**: if SEC restores `companyconcept`, the framing is wrong; if
> it degrades further, the `companyfacts` rung is not guaranteed either. The ladder is still the
> right shape — it is a fallback, and a fallback does not need to know why the primary failed — but
> it should not be documented as compensating for a permanent property of the endpoint.

What *was* wrong is that it was **silent**: the generator warned only when the fetch raised, never
when it returned nothing, so `fundamentals_fill="zero"` turned a missing series into
`total_shares = 0.0` and `market_cap = 0.0` — a value no listed company can have, and one nothing
downstream distinguishes from a measurement. It now logs a warning naming the ticker and the fill
policy.

### 6.4 What this leaves for the owner

- **The 3 rescuable tickers.** `us-gaap:CommonStockSharesIssued` would cover them, but *issued* is
  not *outstanding* — it includes treasury shares, so `market_cap` would silently mean something
  different for those three than for the other 500. Not added; it is a judgement call.
- **Whether a zero-filled `market_cap` should be an error rather than a warning.** 7.4% of the
  default universe is affected, and `fundamentals_fill` already offers `"nan"` and `"drop"` — the
  question is whether `"zero"` should remain the default when it fabricates an impossible value.
- **Why the 37 report nothing.** Not investigated. `META` is a plausible clue: multi-class share
  structures may report per share class rather than into the default units bucket, which would make
  this a parsing gap rather than an absence.
