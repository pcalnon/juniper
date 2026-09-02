# juniper-data — the async job pattern (`APD-DATA-018`): decision analysis

**Project**: Juniper
**Sub-Project**: juniper-data
**Author**: Paul Calnon
**Status**: Analysis — no decision taken; measurements added 2026-09-02 (§1.6), recommendation revised (§4)
**Last Updated**: 2026-09-02

Supports the open defect-register row `APD-DATA-018` ("No async job pattern — generation runs
inside the request"), primer anchor 3853. Written because the row's one-line summary understates
both the problem and the remedies, and because the primer frames it as a **judgement call** rather
than a defect with a known fix.

Everything in §1 was verified in source or measured on 2026-09-01. Claims that are inferred rather
than measured are marked **[inferred]**.

---

## 1. Ground truth

### 1.1 What the code actually does

Generation runs inside the POST. `create_dataset` resolves the params class, computes a
content-addressed id, checks the store, and on a miss calls the generator on a worker thread:

- `juniper_data/api/routes/datasets.py:175` — `arrays = await asyncio.to_thread(generator_class.generate, params)`
- There is **no** `202`, no job resource, and no background-task machinery anywhere:
  `grep -rn 'BackgroundTasks|asyncio.create_task' juniper_data/ --include=*.py` (excluding tests) →
  **0 hits**.

`asyncio.to_thread` keeps the event loop responsive — it does **not** decouple the work from the
request. The client holds the socket for the whole generation.

### 1.2 The generator population splits in two, and this is the crux

The row reads as though generation is uniformly slow. It is not. Of the **16** generators
(`juniper_data/generators/*/` — `_sequence.py` and `_synthetic.py` are shared helper modules, not
generators), two classes behave completely differently:

**Class A — bounded local compute (12).** `spiral`, `xor`, `moon`, `circles`, `gaussian`,
`checkerboard`, `ar_p`, `mackey_glass`, `irregular_sine`, `multi_sine`, `delay_product`,
`equities_seq`. Two properties matter:

- **Measured**: `spiral` at `n_points_per_spiral=1000` generates in **0.008 s**.
- **Bounded by validation**, so the worst case is capped at the request boundary rather than by
  hope: `spiral` rejects `n_points_per_spiral > 10000`
  (`generators/spiral/params.py`, `le=10000`), `delay_product` caps `n_components` at 16,
  `equities_seq` caps a window at 512, and the ratio fields are all `le=1`.

For this class the synchronous posture is not merely acceptable, it is *correct*: a job resource
would add a round trip and a polling loop to work that finishes in milliseconds.

**Class B — external data fetch (3).** `mnist`, `equities`, `arc_agi`. These are unbounded by
anything juniper-data controls:

- `equities` (`generators/equities/generator.py`) fetches Yahoo Finance via `yfinance` **and** SEC
  EDGAR (`_SEC_CONCEPT_URL`, `_SEC_TICKERS_URL`), with a **30 s timeout on a single request**
  (`:104`) and retry backoff that sleeps between attempts (`:100`, `:114`). Its `le=2520` bound is
  on trading days, not on network time.
- `mnist` (`generators/mnist/generator.py:1-25`) loads from the **Hugging Face Hub** via
  `datasets.load_dataset` — a first-run download, cached thereafter.
- `arc_agi` handles `requests.exceptions.ConnectionError` / `HTTPError` with a fallback dataset
  (`generators/arc_agi/generator.py:101-103`), so it too is a network call.

**One SEC fetch can consume a client's entire budget on its own.** That is the finding.

**Class C — unbounded local I/O (1).** `csv_import` is neither: it reads a file from
`settings.import_dir` under a traversal guard (`generators/csv_import/generator.py:83-86`,
`:107-129`). No network, so no 30 s-per-fetch tail — but no size bound either, so a large import is
slow for a different reason. **It is called out separately on purpose:** a remedy aimed at network
latency (warming, retries, longer budgets) does nothing for it, and a size cap would do nothing for
Class B. Folding the two together is the mistake this split exists to prevent.

### 1.3 The client budget is 30 s and cannot be raised per call

- `juniper-data-client` default timeout is **30 s** (`juniper_data_client/client.py:178`, `:188`).
- `create_dataset` (`client.py:498-510`) takes `persist`, `name`, `description`, `created_by`,
  `parent_dataset_id`, `tags`, `ttl_seconds` — and **no `timeout`**. A caller cannot widen the
  budget for a slow generation without constructing a whole separate client. That gap is its own
  open row, `APD-ECO-003`.
- The live production caller does not override it either: cascor builds
  `JuniperDataClient(base_url=data_url, api_key=api_key)` with no timeout
  (`juniper-cascor/src/api/app.py:500`, and again at `lifecycle/manager.py:3694`).

So the effective contract today is: **generation must finish in 30 s or the caller gives up**, and
the caller has no supported way to ask for more.

### 1.4 The mitigating fact: the POST is content-addressed and idempotent

`dataset_id = generate_dataset_id(generator, version, params)` (`routes/datasets.py:139-143`) is
derived from the request, and an existing id short-circuits to a cache hit (`:145-146`). The cache
outcome is already exported to operators as `POST_CACHE_HIT` / `POST_CACHE_MISS`.

**Consequence, and it is load-bearing for the options below:** a client that times out and retries
*converges* — provided the server finished the work. The timeout is not data loss; it is a lost
*answer*. This is why "do nothing" is a genuinely defensible position and not merely inertia.

### 1.5 Risk calibration: latent by default, live by configuration

cascor's auto-start defaults to **spiral** (`juniper-cascor/src/api/settings.py:89`,
`_JUNIPER_CASCOR_API_AUTO_DATASET_DEFAULT = _JUNIPER_CASCOR_API_AUTO_DATASET_SPIRAL`) — Class A,
8 ms. So the shipped default path is nowhere near the timeout.

The exposure appears when an operator points `auto_dataset` at a Class B generator, or when any
caller requests one through the training API. **[inferred]** — I did not find a deployment that
does this today; I also did not find anything preventing it, and nothing warns the operator.

This matters for how the row should be graded. It is not "the service is broken"; it is "a
supported configuration has no working path", which is the same shape the register has repeatedly
recorded as *one config change away* (`APD-DATA-007`, `APD-SVCCORE-007`).

### 1.6 Measured, 2026-09-02 — the precondition is met, but not uniformly

Step 1 of §4 below, run with
`util/ad-hoc/2026-09-02_measure_class_b_generators.py`. Both external services were healthy at
measurement time (`huggingface.co` 200 in 0.84 s, `sec.gov` 200 in 1.40 s), so the slow numbers are
work, not a hung socket.

| Generator | Cold | Warm | vs the 30 s budget |
|---|---|---|---|
| `equities`, **3 symbols** | **12.03 s** | **0.27 s** | within — but see the default below |
| `equities`, **default (503 symbols)** | **~2017 s ≈ 34 min** *(extrapolated)* | — | **~67×over** |
| `arc_agi`, default | **> 600 s** *(timed out; network healthy)* | — | **> 20×over** |
| `mnist`, default | **26.98 s** *(true cold, 38 MB downloaded)* | **20.54 s** | under — with **no headroom** |

Three findings, and they do not point the same way:

1. **`equities` at its default configuration cannot work, and the cause is a default rather than an
   architecture.** `EQUITIES_DEFAULT_MAX_SYMBOLS = None`
   (`generators/equities/defaults.py:38`) means *all* 503 bundled S&P constituents
   (`sp500_constituents.csv`). At the measured **4.01 s per symbol** that is ~34 minutes. Even the
   arithmetic floor from SEC throttling alone — 503 × `_SEC_MIN_INTERVAL` 0.12 s = **60.4 s**
   (`generators/equities/generator.py:73`) — is twice the budget before a single byte moves.
   **The crossover is ~7 symbols**: 30 s ÷ 4.01 s. A request for eight symbols cannot finish
   inside the client's default timeout.
2. **Caching helps `equities` enormously and `mnist` barely.** equities warm is **44× faster**
   (12.03 → 0.27 s) because its cost is fetching. mnist warm is **1.3×** faster (26.98 → 20.54 s)
   because its cost is *decoding* 70 000 images, which no fetch cache avoids. Any remedy built
   around warming must not be assumed to generalise across Class B.
3. **`mnist` is the dangerous middle case.** It fits the budget — at 68 % of it warm, 90 % cold.
   That is not headroom, it is a coin flip against network variance, and it will read as an
   intermittent failure rather than a capacity limit.

**A caveat that matters for reading row 1 of the table.** The ~2017 s figure is *arithmetic*
(4.01 s × 503), not observed: measuring the default would mean ~1000 SEC requests for a number that
extrapolates from three, which the SEC fair-access policy the generator already honours
(`_SEC_UA`, `generators/equities/generator.py:70`) does not invite. The 60.4 s throttle floor,
by contrast, is exact — it follows from a constant.

**What this does not change:** juniper-data's own content-addressed artifact cache (§1.4) still
short-circuits every *repeat* POST for the same params, for all generators. These numbers are the
cost of the **first** call for a given parameter set.

---

## 2. The decisions actually on the table

The row bundles four separable questions. Conflating them is what makes it look like one large
architecture project.

| # | Decision | Why it is separable |
|---|---|---|
| **D1** | Is the sync-only posture a defect **for the whole surface**, or only for Class B? | Class A is measurably fine. A remedy scoped to Class B is a fraction of the work. |
| **D2** | If we act, what **shape**: a job resource, a wider budget, out-of-band warming, or client-side convergence? | These differ by an order of magnitude in cost and in blast radius. |
| **D3** | If a job resource: where does **job state** live? | In-process dies with the worker; Redis/Postgres already exist as store backends. |
| **D4** | How do **three clients** adopt whatever ships? | juniper-data-client is published; cascor and canopy consume it. Any 202 is a wire contract. |

D1 governs. If Class B is the only real exposure, options 1/2/5 below become viable and the full
job resource stops being the obvious answer.

---

## 3. Options

### Option 0 — Do nothing; document the constraint

Record in the OpenAPI description and the generator docs that generation is synchronous, that
Class B generators perform external fetches, and that the caller's timeout governs.

- **Strengths.** Zero risk, zero wire change, zero client migration. Honest: the primer says a
  synchronous API is correct until work outlives a sensible timeout, and for 12 of 16 generators it
  demonstrably does not. Idempotency (§1.4) means the failure mode is a lost answer, not lost data.
- **Weaknesses.** Leaves a supported configuration with no working path. The operator learns the
  limit by hitting it, in production, with a 30 s stall and an opaque client-side timeout.
- **Risks.** The row stays open indefinitely and the next reader re-derives this analysis — the
  "unexamined, not deferred" failure the §4.1 lesson block of the defect register
  (`JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`) already records three times.
- **Guardrails if chosen.** Write the constraint where a caller meets it, not only in notes; add
  the Class A/Class B split to the generator table; re-file the row as documentation-closed rather
  than leaving it open with no stated reason.

### Option 1 — Widen and expose the budget (fix `APD-ECO-003` first)

Add a per-call `timeout` to `juniper-data-client.create_dataset`, and make the service return a
clean, typed error when it gives up rather than letting the socket die.

- **Strengths.** Small, additive, no wire-contract change. Directly removes the "cannot ask for
  more" half of the problem, which is the half that has no workaround today. Also closes a second
  open row.
- **Weaknesses.** Does not bound the work — it moves the ceiling, it does not remove it. A caller
  who sets `timeout=600` now holds a connection for ten minutes, consuming a worker slot.
- **Risks.** Encourages very long synchronous requests, which interact badly with proxies,
  load-balancer idle timeouts, and rolling restarts. A long POST is *not* safe to retry blindly
  even when idempotent, because the retry re-triggers generation if the first attempt has not yet
  written the artifact.
- **Guardrails.** Cap the accepted timeout server-side; emit `Retry-After` on the give-up path;
  document that a timed-out POST may still be in flight and that the correct recovery is a `GET`
  on the deterministic id, **not** an immediate re-POST.

### Option 2 — Warm Class B out of band

Prime the cache for external-fetch generators outside the request path: a scheduled refresh, a
CLI/admin endpoint, or a startup warm for the configured `auto_dataset`.

- **Strengths.** Exploits §1.4 exactly: once the artifact exists, every future POST is a cache hit
  and finishes in milliseconds. No wire change; clients need no migration at all. Turns a latency
  problem into an operational one, which is where it is easier to reason about.
- **Weaknesses.** Only helps *anticipated* parameter combinations. The id is content-addressed over
  params, so a warm for one `equities` window does nothing for a different window.
- **Risks.** Silent staleness — a warmed artifact is a snapshot of an external source; nothing
  currently expresses "this data is from Tuesday". Cache growth is unbounded without retention
  policy.
- **Guardrails.** Warm only an explicit allowlist of (generator, params) pairs; record the fetch
  time in metadata; pair with TTL, which the API already supports (`ttl_seconds`).

### Option 3 — Full async job resource (`202` + `/jobs/{id}`)

POST returns `202 Accepted` with a `Location` pointing at a job resource; the client polls until
the job reports a terminal state and yields the `dataset_id`.

- **Strengths.** The textbook answer, and the one RFC 9205 / the primer point at. Decouples work
  from connection lifetime entirely; survives client disconnects, proxy timeouts and rolling
  restarts. Gives progress reporting and cancellation a natural home. Scales to generators slower
  than anything present today.
- **Weaknesses.** The largest option by a wide margin, and **it is a wire contract**: three clients
  and every hand-rolled caller must learn a two-step flow. It also introduces state that must be
  stored, expired, and made consistent across workers — juniper-data has **none** of that
  machinery today (§1.1).
- **Risks.**
  - **Split-brain across workers.** With more than one uvicorn worker, in-process job state is
    invisible to the process that receives the poll. This is the failure that makes naive job
    patterns worse than the synchronous one they replaced.
  - **Orphaned jobs.** A worker that dies mid-generation leaves a job `running` forever unless
    there is a lease/heartbeat.
  - **Two ways to do the same thing.** If POST keeps its synchronous behaviour for Class A and
    gains a 202 for Class B, the API now has a mode switch that clients must branch on — exactly
    the "clients pay interest on a server-side decision" shape `APD-CCLIENT-008` was.
  - **Retention.** Job records outlive their datasets unless expired; nothing does that today.
- **Guardrails.**
  - Put job state in a **shared** backend from day one. Redis and Postgres already exist as store
    backends, so this is not new infrastructure — but the in-memory store must then be explicitly
    unsupported for multi-worker deployment, and that must fail loudly at boot, not silently.
  - Give jobs a lease/heartbeat so a dead worker's job transitions to `failed` rather than hanging.
  - Make the job id **derived from the content-addressed dataset id**, so a duplicate submission
    joins the existing job instead of starting a second identical fetch.
  - Declare the whole status set in `responses={...}` — noting that juniper-data currently declares
    none anywhere (`APD-DATA-022`, parked), so a 202 would be invisible in the generated OpenAPI
    and every generated client blind to it.
  - Ship the client helper (`wait_for_dataset`) in the same release as the server change, or the
    contract exists with no ergonomic way to consume it.

### Option 4 — Hybrid: synchronous by default, `202` only when it is needed

Keep the current behaviour, and return `202` only when the request is predicted to be slow — by
generator class, by an explicit `prefer: respond-async` request header, or by both.

- **Strengths.** Pays the cost only where the benefit exists. Class A keeps its one-round-trip
  simplicity; Class B gets a path that cannot time out. An explicit opt-in header (RFC 7240
  `Prefer`) makes the mode a *caller* decision rather than a server heuristic, which keeps the
  contract predictable.
- **Weaknesses.** Two response shapes for one endpoint — the client must handle both. If the
  trigger is a server-side heuristic rather than an explicit header, the client cannot predict
  which it will get, and that is genuinely worse than either pure option.
- **Risks.** Heuristic drift: a generator reclassified from A to B silently changes the response
  shape for existing callers. This is the failure mode to design against.
- **Guardrails.** Make the switch **explicit and caller-driven** (`Prefer: respond-async`), never a
  server-side guess. Pin the classification in a test so moving a generator between classes is a
  deliberate, reviewed act. Everything in Option 3's guardrails still applies to the async half.

### Option 5 — Client-side convergence on the idempotent id

Change nothing server-side. Give the client a helper that POSTs, and on timeout polls
`GET /{dataset_id}` (the id being derivable client-side from generator+params) until the artifact
appears or a deadline passes.

- **Strengths.** No wire change, no server state, no migration for anyone who does not opt in.
  Exploits §1.4 fully. Cheapest option that actually removes the stall for a caller who cares.
- **Weaknesses.** Requires the client to compute the same content-addressed id the server computes
  — **duplicating a hashing rule across a repo boundary**, which is precisely the drift class this
  ecosystem has been burned by (`APD-DATA-011`'s cursor encoding, the env-lookup re-derivation the
  primer records). Unless the id is returned or derivable from a published helper, this is fragile.
- **Risks.** The first POST may still be running when the poll starts, so the client cannot
  distinguish "in progress" from "failed" — it polls a 404 either way. No progress, no failure
  reason, no cancellation.
- **Guardrails.** Publish the id derivation from the *server's* package (or return it in an early
  response) rather than reimplementing it client-side. Bound the poll. Treat this as a stopgap that
  makes Option 3 easier later, not as a substitute for it.

### Option 6 — Bound the default fan-out (added 2026-09-02, after measurement)

Give `max_symbols` a finite default instead of `None`, so the out-of-the-box `equities` request
stops meaning "503 sequential SEC lookups". Callers who want the full index opt in explicitly.

This option did not exist in the 2026-09-01 draft. It is here because the measurement in §1.6
located the cost in a **default value**, not in the request/response shape.

- **Strengths.** By far the cheapest thing that moves the headline number: one constant, no wire
  change, no client migration, no new state. Takes the default from ~34 min to a few seconds at,
  say, 8 symbols — under the crossover computed in §1.6. It also converts an unbounded default into
  a bounded one, which is the same discipline Class A already enforces through `le=` validation and
  which the primer treats as the baseline expectation.
- **Weaknesses.** Changes behaviour for anyone relying on the current default, silently returning a
  smaller dataset unless the cap is loud. Does nothing for `arc_agi` (> 600 s with no fan-out to
  cap) or `mnist` (cost is decoding, not breadth).
- **Risks.** A silent truncation is worse than a slow request: a caller who asked for "the S&P 500"
  and receives eight symbols has bad data rather than a late answer. This is the failure to design
  against.
- **Guardrails.** Never truncate silently — either reject a request whose fan-out exceeds the cap
  with a message naming `max_symbols`, or return the count in metadata where it cannot be missed.
  Record the chosen bound against the measured per-symbol cost so the number has a stated basis.
  Pair with §1.4 idempotency: a capped request is still content-addressed, so the smaller dataset
  gets its own id and cannot be confused with the full one.

---

## 4. Recommendation

**Revised 2026-09-02, after the measurement in §1.6.** Step 1 below is now done, and it moved the
answer. The original draft recommended deferring the job resource on the grounds that the
precondition was unproven; it is now proven for two of the three Class B generators, and the
cheap options no longer cover the whole problem.

**What the numbers changed:**

- **Option 1 (widen the budget) is no longer sufficient on its own.** It was drafted as half the
  remedy. But no sane timeout makes a **34-minute** `equities` request or a **> 600 s** `arc_agi`
  request into a synchronous call — you cannot hold a socket, a worker slot and a proxy connection
  that long. Widening the budget remains worth doing for the `mnist`-shaped middle (20–27 s against
  a 30 s limit is the case where 60 s genuinely fixes it), and it still closes `APD-ECO-003`, but
  it is no longer a candidate remedy for the tail.
- **Option 2 (warming) is stronger than drafted for `equities` and weaker for `mnist`** — 44× versus
  1.3×. It cannot be described as a Class B remedy; it is an *equities* remedy that happens to
  generalise to fetch-dominated generators.
- **Option 6 (bound the default fan-out) did not exist before measuring** and is now the single
  highest value-per-unit-effort change, because §1.6 located the headline cost in a default value
  rather than in the request shape.

**Revised sequence:**

1. **Option 6 first.** Give `max_symbols` a finite default, loudly. One constant; takes the default
   `equities` request from ~34 minutes to seconds; no wire change. Do it with the anti-silent-
   truncation guardrail, which is the whole risk.
2. **Option 1 + Option 2.** A per-call timeout (closing `APD-ECO-003`) plus warming for the
   configured fetch-dominated generators. Together these cover `mnist`'s missing headroom and
   `equities`' repeat cost.
3. **Then Option 4** — and this is where the recommendation has genuinely shifted. With `arc_agi`
   over 600 s and no fan-out to bound, there is a residue that steps 1–2 cannot reach. The
   `Prefer: respond-async` hybrid is now the expected destination for that residue rather than a
   contingency, and it should be planned for rather than deferred indefinitely.

**Option 3 as a first move is still the one I would argue against** — its failure modes
(split-brain across workers, orphaned jobs, two ways to do the same thing) are unchanged and each
remains worse than the stall it replaces. But the case for *eventually* needing the async path is
now measured rather than speculative, and `arc_agi` is the generator that makes it.

**What would falsify this recommendation:** if `arc_agi`'s > 600 s turns out to be a one-off
download rather than a per-call cost — it timed out before completing even once, so its *warm*
number is still unknown. That single missing measurement is the difference between "the async path
is required" and "three cheap changes were enough". It should be taken before step 3 is committed.

---

## 5. Guardrails that apply whatever is chosen

- **Do not let a timed-out POST be retried blindly.** Idempotency protects the *data*, not the
  *work*: a retry while the first attempt is still generating starts a second identical external
  fetch. Any documented recovery must be "GET the id", not "POST again".
- **Declare the status set.** juniper-data declares no `responses={...}` anywhere
  (`APD-DATA-022`, parked, owner-routed), so today a new code would not appear in the OpenAPI at
  all. Any option that adds a status code needs that row unblocked, or it ships invisible to every
  generated client.
- **Anything stateful must be shared-backend from the first commit,** with the single-worker-only
  configuration failing loudly at boot rather than degrading silently under a second worker.
- **Keep the Class A path one round trip.** Whatever ships must not make an 8 ms generation cost a
  poll loop.
- **Do not duplicate the id derivation across the repo boundary.** If clients need the
  content-addressed id, publish the derivation; do not reimplement it.

---

## 6. What this analysis does not settle

- Whether any deployment today actually configures a Class B generator for `auto_dataset`
  (**[inferred]** absent, not verified).
- ~~Actual cold/warm timings for `mnist`, `equities`, `arc_agi`~~ — **measured 2026-09-02, §1.6**.
  Two gaps remain: `arc_agi`'s **warm** cost (it timed out before completing a first run, so only
  its cold bound is known — and §4 names this as the measurement that would falsify the revised
  recommendation), and `csv_import`, which needs an import directory and a fixture file to time.
- Whether canopy's demo-mode path (`juniper-canopy/src/demo_mode.py:918`) shares the 30 s exposure;
  it constructs its own client and was not traced here.
- `APD-DATA-019` (pagination) is a separate row with a separate remedy; the two are sometimes
  discussed together as "juniper-data performance" and should not be bundled.
