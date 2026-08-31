# CLI-experimentation arc — tail re-probe (2026-08-29)

**Subject**: every item in the "remaining tail — UNOWNED" section of
[`HANDOFF_2026-08-29_cli-experimentation-tail-and-requirements-corpus.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-29_cli-experimentation-tail-and-requirements-corpus.md) §3,
re-probed against the tree at `origin/main` = `d1f949e9`.

**Why**: the handoff itself warns that its own T7 line numbers went stale between drafts
("a first pass of this handoff had four of the five crossed, so re-check rather than trusting
them"). That warning generalises. A tail that is copied forward at every hop accumulates items
that were closed elsewhere by other owners, and nothing in the chain re-checks them — the
handoff records what the *previous* session believed, and belief is not a probe.

**Result**: of 16 tail buckets, **6 are already shipped**, **2 carry a label error**, **7 are
genuinely open**, and **1 was already recorded as needing no action**. One new finding sizes a
previously-unscoped item at 172 instances.
*(Counts as of 2026-08-29 and are now wrong. **Read §0.1 first**, then §0; both override this
line and the §1 table.)*

**Method**: every claim below is a `file:line`, a merge commit, or a command and its output.
Nothing is carried over on the strength of the handoff saying it.

---

## 0.1 UPDATE 2026-08-31 — four more closed; this supersedes §0 as well

| bucket | §0 said | now |
|---|---|---|
| **3 — T2** | "OPEN, undefined" | **CLOSED, and it was never undefined** — see below |
| **2 — `install_hint`** | blocked on a juniper-data release | **UNBLOCKED** — juniper-data **0.12.0** published to PyPI 2026-08-31 |
| **9 — Q-6's unfollowed half** | needs a *released* cascor carrying #523 | **CLOSED** — cascor **0.10.0** published; the floor landed in **ml#1521** |
| **1 — G-16** | needs HF `datasets` + a live mnist-capable juniper-data | **premise now FALSE** — see below |
| **15 — title artifacts** | 172, unowned | **81 repaired** (ml#1511); **91 remain**, all needing an editorial decision |

**T2 was closed on 2026-08-21 and this document said otherwise for two days.** It shipped in
**ml#1231** (`c8ecbba6`, "Q-1 — write `experiment.resolved.yaml`, scoped to what is verifiable"),
covered by `tests/test_run_experiment.py:1980-2037`; plan `:571` now reads **`SHIPPED (Q-1)`**.

**And the tail's name for it was wrong**, which is why §1 recorded it as "undefined". T2 is
`experiment.resolved.yaml`; "the read-only settings surface" was only **option (1)** of two
unblocking routes the 2026-08-18 handoff listed. What shipped is a **third** route: record only
what is verifiable, each half tagged by source — `driver_resolved` (true by construction) plus
`service_training_params` (the service's own echo, cascor only) — with an explicit `NOT COVERED`
statement so the file cannot be read as a complete config, and failures *recorded* so "could not
read it" never looks like "it was empty".

> **The method error was this document's.** §1 searched for the tail's *phrase* ("read-only
> settings"), correctly found nothing in `notes/`, and concluded "OPEN, undefined". The search was
> right; the inference was not. T2's definition lived in
> `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-18_cli-experimentation-unowned-tasks.md` §2,
> which that phrase never matches. **When a tail entry cannot be found, trace it to the handoff
> that first defined it before calling it undefined.**

**G-16's premise is now false, and its two halves have diverged.** HF `datasets` 5.0.1 is installed
in the `JuniperData` env, so `mnist` reports `available=True` and a cascor mnist experiment can run —
that half is done. The *live-refusal* half is now **untestable in that environment**, because no
generator there is unavailable any more: fixing availability removed the thing the refusal path
needed to demonstrate itself. Exercising it now requires deliberately withholding an optional
dependency, which is a test-fixture question rather than a host-provisioning one.

**Running total: four tail entries were found already-done** — launcher fast-fail (ml#1061), the
G-4 / W-5 / W-7 group, §12.2 item 1, and T2. Six items by individual count. The tail's failure
mode is systematic, not incidental.

**Still open after 2026-08-31**: G-17's marker half, R-1's second clause, PF-4/PF-8 + PF threshold
ratification, the 91 remaining title artifacts, plan §97, F-P4-7, E-C's untested 0.10/0.20 rows at
cap 128, W-12/Q-7, F-P1-2, and G-16's refusal half under the caveat above.

---

## 0. UPDATE 2026-08-30 — five buckets closed; read this before §1

This document went stale in exactly the direction it was written to prevent: it lists work as
open that has since been done. §1's table and §4's prose are preserved as the 2026-08-29
record — **this section overrides them where they disagree.**

| bucket | was | now |
|---|---|---|
| **4d — G-5** recurrence plotting | OPEN (rated High) | **CLOSED** — juniper-recurrence#139 |
| **6b — §12.2 item 3** cross-app surface | OPEN | **CLOSED** — juniper-deploy#198 + ml#1489 |
| **12 — the two ml#1412 callers** | OPEN | **CLOSED** — ml#1488 (T6 driver + import probe); the h2h caller was closed independently by ml#1477 |
| **4e — G-17** | HALF OPEN | **still half open** — the marker is genuinely absent; note `--strict-markers` is set, so it needs a `markers = [...]` section, not merely a usage |
| **15 — corpus title artifacts** | measured, unowned | **still open** — 172 entries, 163 of them already visited by a repair pass that left the title broken. The extraction rule is an owner decision |

**Two corrections to this document's own claims.**

1. **§2.4 overstated G-17's second sub-item.** It reads as though recurrence timings *reach*
   Grafana. The panels are correctly wired and the metric names are right — but there are
   currently **zero** recurrence series under `environment="host-experiment"`, so that row has
   never been observed populated. The plumbing is complete (`util/experiment_stack.bash:900`
   puts recurrence in `SCRAPE_TARGETS`); what is missing is a recurrence run launched with
   `--grafana-bridge`. Read §2.4 as "the wiring shipped", not "data flows".
2. **A defect was found and fixed in a repo this document did not examine.** juniper-recurrence's
   app CI lane was **red on `main`** and invisibly so: service-core 0.6.0 narrowed `EXEMPT_PATHS`
   (dropping `/docs` and `/openapi.json`), and recurrence's `test_app_smoke.py` asserted the old,
   defective contract. It stayed hidden because that lane is **path-filtered** — `main`'s newest
   *green* app run was for an OLDER sha than `main` itself. Fixed in juniper-recurrence#141
   (assert the real contract both ways; floor raised to `>=0.6.0` so a security behaviour stops
   being resolution-dependent). Fanned out to juniper-cascor#599 and juniper-canopy#539, which
   carried the same *coupling* though — unlike recurrence — no live exposure, because both
   un-mount docs whenever auth is on. juniper-data was already correct (APD-DATA-024).

**Method note worth keeping**: "is `main` green?" is not answered by the newest run's conclusion.
It is answered by **which sha that run was for**. A path-filtered lane that never ran and a lane
that passed are indistinguishable in `gh run list` output.

**Still open after 2026-08-30**: G-16 (needs HF `datasets` + a live mnist-capable juniper-data),
`install_hint` (needs a juniper-data release), T2 (declined; needs a scope written before it can
be revived), G-17's marker half, R-1's second clause, Q-6's unfollowed half (needs a *released*
cascor carrying #523 plus a floor asserted at suite load), PF-4/PF-8 + PF threshold ratification,
the 172 title artifacts, plan §97, F-P4-7, and E-C's untested 0.10/0.20 rows at cap 128.

---

## 1. Verdict table

| # | Tail item | Verdict | Evidence |
|---|---|---|---|
| 1 | G-16 live-refusal half | **PREMISE FALSE 08-31** (§0.1) | mnist now available; refusal half untestable there |
| 2 | `install_hint` inert | **UNBLOCKED 08-31** (§0.1) | juniper-data 0.12.0 on PyPI |
| 3 | T2 (`experiment.resolved.yaml`) | **CLOSED 08-31** (§0.1) | shipped ml#1231 on 08-21; §1's name for it was wrong |
| 4a | G-4 recurrence Grafana dashboard | **SHIPPED** | juniper-deploy#166 |
| 4b | W-5 `ar_p` in bench registry | **SHIPPED** | juniper-recurrence#100 |
| 4c | W-7 `--results-dir` | **SHIPPED** | juniper-recurrence#102 |
| 4d | G-5 recurrence plotting | **CLOSED 08-30** (§0) | was: zero `matplotlib`/`pyplot` — recurrence#139 |
| 4e | G-17 `performance` marker | **HALF OPEN** | marker absent; metrics half shipped |
| 4f | "Wave 7.6" as the container | **LABEL ERROR** | Wave 7.6 is the `JR-REC-*` block, and it shipped |
| 5 | R-1 second clause | **OPEN** | adjacent guard exists but predates the finding |
| 6a | §12.2 item 1 — run durations | **SUBSTANTIALLY MET** | recommendation (c) is on the dashboard |
| 6b | §12.2 item 3 — cross-app surface | **CLOSED 08-30** (§0) | was: no comparison row — deploy#198 + ml#1489 |
| 7 | PF-4 / PF-8 decision | **OPEN, with an unblocked entry point** | perf-lane note Tier 4 |
| 8 | PF threshold / W-12+Q-7 / F-P1-2 | **OPEN** | evidence doc §6, unchanged |
| 9 | Q-6 unfollowed half | **CLOSED 08-31** (§0.1) | cascor 0.10.0 published; floor in ml#1521 |
| 10 | Launcher fast-fail | **SHIPPED** | ml#1061, 2026-08-10 |
| 11 | F-7 provenance re-pin | **NO ACTION** (as recorded) | disposition already settled |
| 12 | Two ml#1412 callers | **CLOSED 08-30** (§0) | ml#1488; h2h closed separately by ml#1477 |
| 13 | F-P4-7 learner question | **OPEN** | no entry point |
| 14 | E-C noise 0.10/0.20 at cap 128 | **OPEN, minor** | as stated |
| 15 | Requirements title artifacts | **81 REPAIRED 08-30** (ml#1511); 91 open | new scan, §5 |
| 16 | Requirements plan §97 | **OPEN, confirmed** | `:97` still says "thin indexes" |

---

## 2. Six items are already shipped

### 2.1 Launcher fast-fail — shipped 2026-08-10, listed as "never carried"

The tail says the health gate "cannot distinguish 'slow boot' from 'crashed at import'" and that
the follow-up was "never carried". It was carried, in **ml#1061** (`3f82d774`, 2026-08-10) — 19
days before the handoff that lists it as outstanding.

`wait_for_health` (`util/experiment_stack.bash:378-405`) takes a `pgrep -f` liveness pattern as
its 4th argument and ends the wait after **two consecutive** misses, naming the log to read. All
three legs pass one: data `:622`, cascor `:688`, recurrence `:722`. The design is careful in the
two ways that matter — two misses rather than one, because the launch subshell returns before its
child finishes `exec`ing; and a host without `pgrep` degrades to timeout-only rather than
manufacturing a false death (`:380-383`).

One detail in the tail is also wrong in the same breath: the default is **90 s**, not 180
(`:144`). The 180 belongs to `2026-08-21_h2h_paired_campaign.bash:54`, which overrides it.

### 2.2 G-4, W-5, W-7 — three of the five "Wave 7.6" items

| item | claim in the tail | reality |
|---|---|---|
| **G-4** | "no recurrence Grafana dashboard" | `juniper-deploy/grafana/provisioning/dashboards/juniper-recurrence.json` — 13,784 bytes, 20 titled panels, landed **juniper-deploy#166** (`6116da7`, "JuniperRecurrence dashboard + recurrence latency recording rules (Wave 1.3)") |
| **W-5** | "register `ar_p` in the bench registry" | `bench/datasets.py:139` factory, `:287` in `DATASETS`, and the module docstring `:15` names "plan W-5". Landed **juniper-recurrence#100** (`eb54c01`) |
| **W-7** | "`--results-dir` for `bench.run_benchmark`" | `bench/run_benchmark.py:339-345`, default `_RESULTS` unchanged exactly as the plan specified, `:331` comment cites "W-7 (CLI experimentation plan §11 / H-6)". Landed **juniper-recurrence#102** (`4c8c3cb`) |

The recurrence working tree is clean, so these are committed, not local state.

### 2.3 §12.2 item 1 — the plan's own recommendation is met

Plan `:989` frames it as "Run-level durations are not a metric" and recommends "**(c) first, (a)
always, (b) only if a gap survives**", where (c) is "rate panels derived from the existing
`juniper_cascor_training_epochs_total` counter".

(c) is on the dashboard:

```promql
sum by (run_id, phase) (rate(juniper_cascor_training_epochs_total{environment="host-experiment", ...}[$interval]))
```

plus a `training_step_duration_seconds` p50/p95 pair. (a) — driver-computed into `stats.json` —
is the status quo and always was. So the recommendation is discharged; (b), the proposed cascor
run-duration Summary/Gauge, was explicitly conditional and no gap has been demonstrated.

**Nuance worth keeping**: the item's *headline* ("total run wall-clock is not a metric") is still
literally true. What is closed is the plan's recommended response to it, not the underlying
observation. Anyone reopening this should reopen (b) on its merits, not on the headline.

### 2.4 G-17's second sub-item

§12.2 item 2 has two halves. The second — "let the **driver** publish bench-equivalent timings
via the service path … so recurrence timings reach Grafana without touching the offline harness"
— is shipped: the experiments dashboard queries
`juniper_recurrence_train_last_duration_seconds` and
`juniper_recurrence_crossval_last_duration_seconds`, both scoped `environment="host-experiment"`.

The first half — a `performance` pytest marker in the recurrence app — is **absent**: no
`pytest.ini`, `setup.cfg` or `tox.ini` in the repo, no `markers` key in `pyproject.toml`, and no
`pytest.mark.performance` anywhere. G-17 is half done, and the remaining half is the cheap half.

---

## 3. Two label errors

### 3.1 "T7's Wave 7.6 minimum" names the wrong wave

Plan `:1223-1228` is the wave table. **Wave 7.6 is "Propose the `JR-REC-*` ID block (§16)"** —
juniper-ml, size S — and it **shipped**: 11 distinct `JR-REC-*` ids live in the corpus
(`JR-REC-API-001`, `JR-REC-DATA-001`, `JR-REC-DEP-001`, `JR-REC-OBS-001`, `JR-REC-TEST-001`, …),
and the v5 refresh records them as official.

The five items the handoff files under that label — G-4, G-5, G-17, W-5, W-7 (+ "the
experiment-config layer") — are **G-** ids from the gap table (`:216`, `:217`, `:240`) and **W-**
ids from the work table (`:945`, `:947`). Different tables, different numbering, no relation to
Wave 7.6. The individual line numbers are all correct; only the container is wrong.

Consequence: anyone who "closes Wave 7.6" closes something already done, and anyone who checks
Wave 7.6 to see whether the five are done gets a misleading answer.

The sixth item, "the experiment-config layer", is likely **cascor#486** ("Wave 3.1 — experiment
YAML config layer, service:-block projection, YAML > env", merged 2026-08-08) — Wave 3.1, not
7.6. Flagged rather than asserted: the handoff gives no line reference for it, so which artifact
it means is a genuine ambiguity for the owner to settle.

### 3.2 PF-4 / PF-8 are gated, but the note never names them

The tail says PF-4/PF-8 are "gated behind the perf-lane phasing note". The note —
[`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md) —
contains **zero `PF-` mentions**. The gating is real but sits one level up: §1 "§12 status:
development is GATED", and Tier 4 orders the whole lane `F-P1 Design → F-P2 Planning → F-P3
Verification (owner ratifies thresholds) → F-P4 Documentation → development`.

**This turns an "awaiting a decision" item into an actionable one.** The note's closing paragraph
of Tier 4 says:

> **One dependency worth pulling forward.** F-P1 must specify the Q-8 baseline directory. That is
> cheap and unblocks nothing else — so it can be drafted opportunistically alongside Tier 2
> without starting the lane proper.

So the entry point is **F-P1 Design, specifying the Q-8 baseline directory** — explicitly
sanctioned as pull-forward work, no owner ratification needed to start, and no GPU. The tail's
framing ("need a decision, not a suite") obscured that.

---

## 4. The genuinely open items, with what each actually needs

- **G-16 live-refusal half** — still blocked the same way. HF `datasets` imports fail in both
  `JuniperCascor1` and `JuniperData`. Verifying it needs either `pip install datasets` in a
  candidate env or a live juniper-data with mnist available; ports are data `8110-8139`, cascor
  `8230-8259` (`util/experiment_stack.bash:122-127`).

- **`install_hint`** — confirmed exactly as described. `git grep install_hint v0.11.0` returns
  nothing; on `origin/main` it appears in 5 files (`api/routes/generators.py`, `core/models.py`,
  and three generators). Newest release by date is `v0.11.0` (2026-07-29) while GitHub still
  marks **v0.10.0** as `Latest` — so "latest release" resolved programmatically gets the wrong
  one, as the handoff warns. **Unblocked by a juniper-data release, nothing else.**

- **T2 read-only settings surface** — the phrase "read-only settings" appears **nowhere** in
  `notes/`, and `gh search` finds no PR or issue for it. The handoff's own conclusion is right
  and now stronger: there is nothing to revive, only something to write. Note the near-miss:
  cascor#486 is a settings *config layer*, not a read-only surface — do not mistake one for the
  other.

- **G-5 recurrence plotting** — zero `matplotlib`/`pyplot` across the repo, confirmed. Plan
  `:217` rates it **High**; it is the highest-rated genuinely-open item in the tail.

- **G-17 first half** — add a `performance` marker to the recurrence pytest config. Small.

- **R-1 second clause** — "do not report `succeeded` when zero candidates were installable
  because of allocation failures". A closely-related guard **does** exist:
  `BUG-CC-18 / ROBUST-01` in `cascade_correlation.py:2536` and `:2545-2549` raises
  `CandidateTrainingError` when both training paths fail and when results come back empty,
  explicitly refusing to "install zero-correlation dummy candidates".

  **This does not discharge R-1.** That guard landed in **cascor#138 on 2026-04-24**, nearly four
  months *before* R-1 was raised on 2026-08-12 — so R-1 was written with it already in place. It
  covers both-paths-failed and empty-results; a per-candidate allocation failure that still
  returns a (zero-correlation) result is the uncovered shape. R-1's first clause, cascor#509, is
  **CLOSED** (2026-08-14); only the second clause survives.

  Beware the name collision the handoff flags: the plan's own `R-1` at `:1236` is an unrelated
  Prometheus-scrape risk. The live clause is at
  `JUNIPER_2026-08-12_…P4-SPIRAL-RESURFACE-EVIDENCE.md:183`, owner column **cascor**.

- **§12.2 item 3, cross-app comparison surface** — genuinely absent. The experiments dashboard
  has a "Cascor Training" row and a separate "Recurrence" row with **disjoint metric families**
  (`juniper_cascor_training_*` vs `juniper_recurrence_*_last_duration_seconds`); there is no row
  comparing the two across `run_id`s, which is what the item asks for. Plan `:991` calls it "a
  small dashboard addition once §7 lands" — §7 has landed, so it is now unblocked.

- **PF threshold ratification (§12), W-12/Q-7 (parked), F-P1-2 (Grafana render)** — evidence doc
  §6 still lists all three, and its own 2026-08-16 update confirms them "unchanged and still
  open" while retiring Q-6 and F-P4-1 from that list. No handoff in the chain has carried them;
  that remains true.

- **Q-6's unfollowed half** — correctly stated. `util/experiments/run_suite.py:112` still refuses
  `app: cascor` with `max_parallel > 1`, and the comment at `:117-123` is explicit that lifting it
  "needs a cascor version floor asserted at suite load, which is a separate change — do not relax
  it merely because the override exists upstream". Note this is a *different* Q-6 residual from
  the log-dir override, which cascor#523 closed; the evidence doc's own 08-16 update warns against
  conflating them.

- **The two ml#1412 callers** — all three claims confirmed:
  - `util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash` — the comment block still states the
    refuted rationale verbatim ("Pinning the checkout instead was considered and rejected …
    would mix a pinned cwd with primary-checkout imports and produce a baseline nobody could
    describe"), and `:39` hard-codes `CASCOR_DIR="${PROJECT_DIR}/juniper-cascor"`.
  - `util/ad-hoc/2026-08-21_h2h_paired_campaign.bash:67` derives `SVC_SHA` from
    `${JUNIPER_EXP_PROJECT_DIR}/juniper-cascor` and refuses on mismatch — with the ecosystem root
    as its `:53` default. **A default-value trap, not a broken script**, exactly as recorded: under
    the shadow-dir configuration that path *is* the pin and the check passes. Reproduce before
    "fixing".
  - `util/ad-hoc/2026-08-26_cascor_import_provenance.py` — its `Related:` line still cites
    `experiment_stack.bash:95 (CASCOR_SRC_DIR, hard-wired to the primary checkout)`, which
    `:112`'s `JUNIPER_EXP_CASCOR_SRC_DIR` override falsified. Its "Why this exists" prose reads as
    an open question that the probe has since answered.

- **F-P4-7's learner question** and **E-C's untested 0.10/0.20 rows at cap 128** — unchanged, no
  entry point, correctly stated.

- **Requirements plan §97** — confirmed verbatim at `:97`: "The `by-repo/` and `by-status/` files
  are thin indexes that link into `by-area/` — not duplicates." ml#1462 made them a generated
  projection carrying full bodies. Still nobody's.

---

## 5. New finding — the corpus title-artifact class is 172 entries, and repair is implicated

The tail files "Detail *selection*" as one entry (`JR-ML-OBS-003`) with "Scope unknown — no scan
exists for it". That scan now exists:
[`util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py`](../util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py).

```text
entries scanned            : 1814
title artifacts            : 172
    unbalanced-bold     : 118
    truncated           : 84
    field-label         : 8
    blockquote          : 5
  visited by a repair pass : 163  (repair did not fix the title)
  never repaired           : 9
```

**The headline is the second-to-last line.** 163 of the 172 carry a
`brief repaired from cited content` marker — a repair pass visited them and left the title an
artifact. Sampling shows why: the repair replaced a section-heading title with a fragment cut out
of the *middle* of a bolded run, so the opening `**` was left behind:

| id | marker records the OLD title as | the title it produced |
|---|---|---|
| `JR-ML-API-005` | `'4.3 CR-024: Chunked Encoding Body Limit'` | `Effort**: 0.5 day \| **Repo**: juniper-cascor \| **Status**: FIXED.` |
| `JR-ML-API-037` | `'Overview'` | `**API Surface**: 42+ REST methods + 2 WebSocket stream classes.` |
| `JR-ML-API-029` | `'4.1 Root Cause'` | `Output weights transposition bug**: ALREADY FIXED (merged). …` |

For `JR-ML-API-005` the repair made the entry **worse**: the discarded title named the subject
(chunked-encoding body limit); the replacement is an effort-estimate cell.

Three things follow.

1. **`--check-views` structurally cannot see this.** It compares the three view families, and
   since ml#1462 by-repo/by-status are *generated from* by-area — so a defect in the canonical
   entry is copied identically into every view and the diff is empty. This is the tail's own
   trap ("a cross-view check finds families DISAGREEING; it can never find a defect all three
   SHARE") measured at scale.

2. **The scale is ~9.5% of the corpus**, not one entry. `JR-ML-OBS-003` is a Detail-selection
   defect specifically, which is a *different* class from these 172 title defects and is not
   counted above — it survives as its own item.

3. **A repair pass is not self-validating.** 354 `v3 brief repaired` markers exist; 163 of the
   entries carrying one still have a broken title. Before any further repair is authorised it
   should be paired with this scan as an acceptance gate (`--check` exits 1 while artifacts
   remain), or the next pass will bank the same result.

`JR-ML-OBS-004`'s title is a worked example of the shape, sitting immediately below the entry the
tail already names:

```text
### JR-ML-OBS-004 — Status**: **PARTIAL (2026-04-10)** — typed contract done; WebSocket consumption still open. See….
```

**ml#1467's five repairs are not implicated** — they are marked `2026-08-29 brief repaired`
(DATA 2, ARCH 1, TRAIN 1, OBS 1 = 5, matching the record), and none of the five trips the scan.
The 163 are the older v3 tranche.

---

## 6. What this document does not cover

- Anything outside handoff §3. The backup arc, P5 rollout, defect register, canopy E2E arc and
  service-core round-29 work all have other owners and are out of scope by the handoff's own §6.
- **Whether the 172 titles should be repaired, and by what rule.** This sizes the problem and
  supplies the detector; choosing the extraction rule is a design decision, and the evidence
  above is that choosing it badly is the failure mode.
- Cascor #572 / #573 / #578. #582 remains in scope only as F-P4-7's interpretation guardrail.
- The E-C and F-P4-7 results themselves — unchanged, and re-verified green via §5 of the handoff
  before this probe began.

---

## 7. Environment note

`git -C <sibling-repo>` **works in this session**, unlike the predecessor's, whose shell gate
refused it (handoff §2). That is what made the deploy / recurrence / cascor / data provenance
checks above possible from a juniper-ml worktree. Do not assume either way — test it once at
session start, because several verdicts here are unreachable without it.
