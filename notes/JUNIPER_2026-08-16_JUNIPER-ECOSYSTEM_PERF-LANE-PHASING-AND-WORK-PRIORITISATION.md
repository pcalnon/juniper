# §12 Performance Lane — phase gating, and prioritisation across open program work

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-ml / juniper-cascor / juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-16

Records the owner's 2026-08-16 direction on the **§12 performance lane** — *"open engineering …
needs design, planning, verification, and documentation before development can begin"* — and, as
directed, **prioritises each phase against the program's other outstanding and in-progress work**.

This note schedules; it does not design. The §12 design itself is the first deliverable it
schedules.

---

## 1. §12 status: development is GATED

[Plan §12](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md)
opens by saying so itself:

> **This section is a design start, not a final design.** It fixes the reuse decisions and the
> measurement contract; the scenario matrix and thresholds need a ratification pass of their own.

So §12 today is a **reuse decision** (§12.1: cascor's `tests/performance/`, its persisted
`baseline_20260526.json`, and the `--profile` / `--profile-memory` entry points) plus a **draft**
scenario list (§12.3) and a **draft** baseline/regression policy (§12.4). None of that is a
buildable specification.

**No §12 development starts until phases P1–P4 below complete.** Recording this explicitly because
the lane has twice been mistaken for ready work: it previously "owned" **F-P1-3b**, a finding that
was first withdrawn for lack of evidence and then positively **refuted**. The lane survived that —
its real inputs are the **PF suites** and the **E-B difficulty ranking** — but it has never had a
premise strong enough to build from.

### 1.1 The four gating phases

| phase                  | deliverable                                                                                                                                                                                                                                               | done when                                                  |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| **P1 — Design**        | Design-of-record note: what is measured, on which tier, against which baseline, at what budget, & what regression *means*. Must resolve §12.3 scenario matrix, draft -> fixed, & specify Q-8 baseline directory (name, layout, retention, who writes it). | A `notes/` design doc exists and is reviewed.              |
| **P2 — Planning**      | Work items with repo, size, and dependencies — the §14-style wave table this program uses everywhere else.                                                                                                                                                | Items are enumerated and sequenced.                        |
| **P3 — Verification**  | The thresholds ratified (owner), and the measurement contract demonstrated end-to-end on a real run before anything is gated on it.                                                                                                                       | PF thresholds ratified; a dry measurement pass reproduces. |
| **P4 — Documentation** | Operator surface in `docs/REFERENCE.md` + the cheatsheet; the baseline directory documented as a first-class artifact location.                                                                                                                           | Docs merged.                                               |

Only then: development.

### 1.2 Inputs that already exist

- **PF suites** — six runnable §12.3 suites, 31 cells, all driver-validated (ml#1033).
- **E-B difficulty ranking** — moon/gaussian < xor/circles < checkerboard.
- **cascor micro-layer** — `tests/performance/` + `baseline_20260526.json`, reused not rebuilt.
- **Q-8 (answered 2026-08-16)** — run-level baselines live in a **dedicated, new directory**. This
  is a P1 input, not an implementation detail: the directory's location, layout and retention
  contract are part of the design, and Q-8 also gates the `JR-CAS-OBS-004` targets.

### 1.3 Known trap for P1

The driver's `outputs.max_wall_seconds` — **not** the suite's `per_run_timeout_seconds` — is what
actually ends a run; `run_suite` never passes `--max-wall-seconds`, so an unoverridden cell silently
inherits `spiral-baseline`'s 3600 s. Any timing-based scenario authored without pinning that will
measure the budget rather than the workload. This is the same class of error that produced F-P1-3b:
**a timeout is not a measurement.**

---

## 2. Open and in-progress work inventory (2026-08-16)

| id    | work                                                                                                                 | state                                                                                                              | owner-blocked?     |
|-------|----------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|--------------------|
| **A** | **D-A optimizer restore defect** — optimizer state silently dropped on every snapshot load, current version included | Ready; unblocked                                                                                                   | no                 |
| **B** | **5.3 lift `run_suite` cascor-parallel refusal** (`run_suite.py:112`)                                                | Ready except for an **external** gate: no released cascor carries #523                                             | no                 |
| **C** | **W-12 `csv_import` corpus**, both cascor and recurrence                                                             | Un-parked by Q-7; **scope widened** beyond the original question                                                   | no                 |
| **D** | **Q-10 dedicated `JuniperRecurrence` conda env**                                                                     | Ready; provisioning + docs                                                                                         | no                 |
| **E** | **F-P1-4 snapshot lifecycle** — phases 6.1 identity → 6.2 index → 6.4 retention                                      | Designed ([design](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)); 6.3 fixes ready | S-1/S-2 open       |
| **F** | **§12 perf lane** P1→P4 then development                                                                             | **Gated** (this note)                                                                                              | PF thresholds (P3) |
| **G** | **Wide-budget head-to-head campaign** (ml#1122)                                                                      | **COMPLETE** 2026-08-17 (ml#1143) — no accuracy gap; a real CLI wall-clock penalty, all of it candidate-phase       | no                 |
| **G1**| **Seeded runs do not reproduce** ([cascor#532](https://github.com/pcalnon/juniper-cascor/issues/532))                 | **CHARACTERISED at N=20** 2026-08-20 ([evidence](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md)) — and it is **PATH-SPECIFIC**, which changes what it blocks. Service **0 / 190** pairs; direct CLI **0.768** [0.553, 0.847]. Cause identified: the two entry points run `fit()` on different threads (service on a `ThreadPoolExecutor` worker, CLI on the main thread). Moving the CLI onto a pool thread cuts it to 0.337 at no wall-clock cost — a large mitigation, not a cure; residual not yet understood | **narrowed** — blocks P3 thresholds only where they rest on **direct-CLI single-run** numbers; service-tier baselines are clear |
| **G1a**| **Residual 0.337 after the thread-context mitigation**                                                              | **OPEN — NEW.** Survives entirely in the final candidate round (no `grow_network` line), worth 0.5 pp val. Only visible on the correlation fingerprint; the iteration trace reads 0.000 | blocks a CLI-side "reproducible" claim |
| **G1b**| **Observability gap blocking further root-cause** — `_add_best_candidate` logs `{best_candidate}`, a memory address (`cascade_correlation.py:4850`) | **OPEN**, cheap. The installed unit's identity is the one fact separating a selection flip from arithmetic jitter and is unrecoverable from any shipped log; the campaign needed a patched build to get it | no |
| **G2**| **Residual CLI-vs-service wall gap** after [cascor#533](https://github.com/pcalnon/juniper-cascor/pull/533)            | **CLOSED** 2026-08-23 ([evidence](JUNIPER_2026-08-21_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-RESIDUAL-WALL-GAP-EVIDENCE.md), [fix design](JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md)). Measured k=4 paired at caps 4/16/64; decomposes into a stable **rate** term and a stochastic **work** term. Root cause of the rate term: `inspect.getmodule` scanning `sys.modules` on every log record, ~78% of candidate-worker CPU. Fixed in **cascor#563** — ~9x faster training on BOTH arms, rate ratio 1.415 -> **1.065** [0.869, 1.262], interval includes 1.0. The **work** term (1.230) is G1/G1a and untouched. NOTE: the **span** ratio did NOT improve (1.735 -> 1.817) — see G4 | no |
| **G3**| **#531's "OMP=2 cap costs 1.30x" REFUTED**                                                                            | **CLOSED** — re-measured rep-paired at k=3: **1.016x** [0.885, 1.148]; 1.30x excluded. #533 remains correct engineering (one BLAS policy, both entry points); only its *performance* justification failed. Two further single-run attributions died the same way: the "~1.17x" cap-16 residual (actually 1.706x at k=4) and the expectation that #533 would move the cap-64 headline | no |
| **G4**| **Per-run fixed overhead is now the dominant cost** (NEW, exposed by cascor#563)                                       | **OPEN — no instrument.** Before F1 the candidate phase was 98% of a cap-16 span (890 of 908 s); after, 66% (41 of 62 s). Startup, dataset fetch, output passes and teardown now set the wall and have never been examined. The existing phase split separates candidate from output only, so this needs a new instrument first | no |
| **G5**| **F2 CLI import hygiene / F3 forkserver preload**                                                                     | **OPEN.** F2: `import main` pulls fastapi+pydantic (1,867 modules vs api.app's 1,416); **demoted** by cascor#563 from perf-critical to hygiene; import edge not traced. F3: preload omits `cascade_correlation` (242 modules / 1.822 s, ~12.8 s per pool creation) — **blocked on a fork-safety audit**. Both may be subsumed by the untraced forkserver-isolation leak (evidence §4.4a §6.1) | no |
| **H** | **Defect register outstanding work** (ml#1121) — 91 open defects                                                     | In progress, separate arc                                                                                          | no                 |

---

## 3. Prioritisation

Ordering rationale, highest first. Three criteria: **correctness before capability**, **unblocked
before blocked**, and **do not contend for a resource another arc is holding**.

### Tier 1 — do now

1. **A — the D-A optimizer defect.** A correctness bug on the current version that silently breaks
   "resume a paused training run", one of the four stated snapshot requirements. It is small,
   independently shippable, needs nothing from any other item, and every day it stays open is a day
   any resume-based work is quietly wrong. **Highest value per unit effort in the whole inventory.**
2. **E-6.3 — the other two snapshot fixes.** `load_network`'s silent `None` (corruption is
   indistinguishable from absence) and moving the service snapshot root out of the importable
   package — the latter closes the cascor#501 class, where a cleanup sweep deleted five modules.
   Both independent of the rest of E.

> **Correction (2026-08-17) — Tier 1 is REORDERED; item 1 above was wrong.** Tracing the consumers
> before implementing (design
> [§4.1](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)) inverted the
> ranking:
>
> | | corrected standing |
> | --- | --- |
> | **D-A optimizer** | **Demoted to lowest of the three.** The TypeError is real, but a restored optimizer is **never read** — `cascade_correlation.py:2063` unconditionally *recreates* it, deliberately, because a hidden-unit insertion invalidates the prior parameter space (`:2050-2053`), and `load_state_dict` is called nowhere. Fixing it changes nothing observable; it is **log hygiene**, not a correctness bug. The claim that it "silently breaks resume" above is **withdrawn**. |
> | **D-B `load_network` / restore** | **Promoted to Tier 1 item 1.** Confirmed reachable and user-facing: `POST /v1/snapshots/{id}/restore` returns **404 "not found or failed to load"** for a *corrupt* snapshot (`api/routes/snapshots.py:213`, `manager.py:4573`), fusing two opposite operator situations under every snapshot operation (`/restore`, `/resume`, `/replay`, `/retrain`). |
> | **move snapshot dir out of the package** | Unchanged, Tier 1 item 2 — closes the cascor#501 class. |
>
> **Corrected Tier 1 order: (1) D-B restore/corrupt distinction, (2) move the snapshot dir,
> (3) D-A type coercion — gated on S-5.**
>
> **New owner question S-5** (design §9): is R3 ("training pauses" *with optimizer state*) a real
> requirement for Cascade Correlation? It cannot be satisfied by any serializer change, and the
> architecture argues it is not meaningful. **Answering S-5 decides whether D-A is fixed or its
> save/restore path is deleted.**
>
> ~~**Implementation trap for whoever picks this up:** `load_network` has **no production callers**.
> The live path is `lifecycle._load_snapshot_to_network`. A fix applied only to `load_network` would
> change nothing — which is precisely the error that made D-A look important.~~
>
> ⛔ **RETRACTED — this paragraph is FALSE. Do not act on it.** `load_network` is the live loader
> and is the only place that can separate *absent* from *corrupt*. See the correction immediately
> below.

> **CORRECTION (2026-08-19) — the "no production callers" claim above is FALSE, and inverted.**
> Caught by an independent validator while checking the successor handoff. `load_network`
> (`snapshot_serializer.py:877`) **is** the live loader:
>
> - `_load_snapshot_to_network` (`manager.py:4561`) — the function this document names as "the
>   live path" — **calls it** at `manager.py:4580`: `network = serializer.load_network(matches[0])`.
> - `cascade_correlation.py:5130` calls it too, inside the public `load_from_hdf5`.
> - References are not confined to one test file either — ~16 files under `src/` reference it.
>
> So the guidance "a fix applied only to `load_network` would change nothing" is exactly
> backwards: `load_network` is where absent and corrupt both collapse to `None` (a missing-file
> return, a `_validate_format` failure, and a catch-all), and therefore **the only place that can
> separate them**. A fix belongs there, paired with error-mapping in `_load_snapshot_to_network`,
> which currently flattens every failure to `return False` (`:4575` absent / `:4583` corrupt), and
> in the four route raise sites.
>
> ⚠ **Line numbers in this block were re-derived against juniper-cascor `4bec1be`** (2026-08-20).
> juniper-cascor#539 shifted `manager.py` by ~66 lines, so the pre-#539 citations elsewhere in this
> document (`:4504`, `:4523`, `:4573`) are stale by that amount.
>
> **D-B now has its own design of record:**
> [`JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md`](JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md)
> (juniper-ml#1193).
>
> **How the error happened, because it is the more useful lesson:** the original check was a
> `grep` piped through `head -12`. The test file's matches filled the window and the two
> production callers were cut off. That is the *same* truncation mistake that hid a cross-repo
> reference earlier in this arc — the reason
> `util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash` prints full per-group counts. **Never
> truncate a reference sweep.**

> **RETRACTION (2026-08-17, later same day) — the reorder above is ITSELF wrong; D-A returns to
> Tier 1 item 1.** Friendly and adversarial reviews both refuted the "inert" finding. Decisive
> evidence: (a) `output_optimizer` has 3-4 production sites, incl. `manager.py:4127` read from
> `PATCH /v1/network/weights`; (b) `load_snapshot`'s own docstring (`manager.py:4551-4554`) says a
> restored network **"cannot start training directly"** — restore/retrain/resume are distinct verbs,
> so nothing overwrites the restored optimizer on the restore path; (c) **a load → save cycle
> silently destroys optimizer state** (save guard `:430` skips when `None`, with no warning) — data
> loss, reproduced; (d) `optimizer_type` has no other home in the snapshot, so restoring an SGD
> snapshot makes `GET` training params report a fabricated `"Adam"` (97 real SGD files).
>
> **Corrected Tier 1 order: (1) D-A optimizer restore — data destruction, (2) D-B absent-vs-corrupt,
> (3) move the snapshot dir out of the package.** D-B's promotion still stands on its own evidence;
> D-A simply outranks it. Full record: design doc §4.1 retraction.
>
> **The fix must not be naive** — `load_state_dict` on the raw parsed JSON is *accepted but inert*
> (string keys match no `Parameter`), converting a loud failure into a silent one across ~27.5k
> snapshots, with both existing test suites passing either way. Restore failure must **warn and
> degrade to `None`**, never raise (~97 SGD loads succeed today and must keep succeeding).

### Tier 2 — next

3. **E-6.1 identity → E-6.2 index.** Strictly ordered, and the prerequisite for any retention
   conversation. Also the item that turns 27,869 snapshots from a heap into something queryable —
   valuable even if nothing is ever deleted.
4. **C — W-12 `csv_import`.** Owner-requested, un-parked, and now spans both corpora. **Re-estimate
   before scheduling**: the plan's `S` predates the widening to recurrence, which adds a 3-D import
   path and a second matrix row.
5. **D — the `JuniperRecurrence` env.** Small, self-contained, mostly provisioning + documentation
   (parent `CLAUDE.md` env table, `docs/REFERENCE.md`, and `experiment_stack.bash`, whose recurrence
   leg currently rides `JuniperCascor1`).

### Tier 3 — scheduled, with a live external gate

6. **B — lift the cascor-parallel refusal.** Q-6's rationale (*"parallel execution on-stack is
   becoming important"*) makes this demand-driven rather than opportunistic, so it sits above §12.
   Everything on our side is ready; the gate is external and binary — **a cascor release carrying
   #523**. Re-check `https://pypi.org/pypi/juniper-cascor/json` on every pass; PyPI latest is
   `0.9.0`, cut *before* the merge. **Do not guess a floor.** The moment a release lands, this
   moves to Tier 1.

### Tier 4 — the perf lane, in order

7. **F-P1 Design**, then **F-P2 Planning**, then **F-P3 Verification** (owner ratifies thresholds),
   then **F-P4 Documentation**, then development.

**Why §12 sits last among the engineering items** — and this is a scheduling judgement, not a
demotion: it is the only item whose *first* phase is a design pass, it is the only one with an
owner-ratification step inside it, and its most valuable input (the PF suites) is already banked and
does not decay. Meanwhile items A and E-6.3 are live correctness defects. Correctness before
capability.

**One dependency worth pulling forward.** F-P1 must specify the Q-8 baseline directory. That is
cheap and unblocks nothing else — so it can be drafted opportunistically alongside Tier 2 without
starting the lane proper.

### Not scheduled here

**G** (wide-budget campaign) and **H** (defect register) are separate arcs owned by other sessions.
They are listed only so the prioritisation is honest about contention:

- **G holds the GPU** and, per this session's observation, a `juniper-cascor` checkout. Any Tier-1/2
  item that needs a live cascor training run should expect contention and should **not** assume the
  experiment ranges are free — check `util/experiments/list_runs.py` and the port lockdirs first.
  Items A, E-6.1/6.2/6.3, C and D are all implementable without a GPU campaign.
- **H** touches many of the same repos; coordinate on the shared files rather than sequencing
  around it.

---

## 4. Dependency graph

```text
Tier 1   A  (optimizer fix) ─────────────── independent
         E-6.3 (load API, dir move) ─────── independent

Tier 2   E-6.1 identity ──> E-6.2 index ──> E-6.4 retention proposal ──> [owner ratifies]
         C  (csv_import, re-estimate first)
         D  (recurrence env)

Tier 3   B  (cascor-parallel) ──gated on── [cascor release carrying #523]   ← external

Tier 4   F-P1 design ──> F-P2 plan ──> F-P3 verify ──> F-P4 docs ──> §12 development
             ^
             └── Q-8 (answered): dedicated baseline directory is a P1 input
             └── PF thresholds (owner) land in F-P3
```

---

## 5. Owner items still open after 2026-08-16

| item                               | note                                                                                                                                                                                                    |
|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PF threshold ratification**      | Lands inside F-P3. The lane cannot finish its verification phase without it.                                                                                                                            |
| **S-1 / S-2** (snapshot design §9) | S-1 (move snapshots out of the checkout entirely) would make the fix structural. S-2 (is the March–April cohort of retained value?) is **deliberately not actionable** until E-6.2 can characterise it. |
| **S-3 / S-4**                      | Audit-log unification and the retention horizon — both correctly deferred to last.                                                                                                                      |

**Closed this round:** F-P1-2 (premise refuted), Q-6, Q-7, Q-8, Q-10.
