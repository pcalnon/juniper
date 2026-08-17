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

| phase | deliverable | done when |
|---|---|---|
| **P1 — Design** | A design-of-record note: what is measured, on which tier, against which baseline, at what budget, and what a regression *means*. Must resolve the §12.3 scenario matrix from draft to fixed, and specify the Q-8 baseline directory (name, layout, retention, who writes it). | A `notes/` design doc exists and is reviewed. |
| **P2 — Planning** | Work items with repo, size, and dependencies — the §14-style wave table this program uses everywhere else. | Items are enumerated and sequenced. |
| **P3 — Verification** | The thresholds ratified (owner), and the measurement contract demonstrated end-to-end on a real run before anything is gated on it. | PF thresholds ratified; a dry measurement pass reproduces. |
| **P4 — Documentation** | Operator surface in `docs/REFERENCE.md` + the cheatsheet; the baseline directory documented as a first-class artifact location. | Docs merged. |

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

| id | work | state | owner-blocked? |
|---|---|---|---|
| **A** | **D-A optimizer restore defect** — optimizer state silently dropped on every snapshot load, current version included | Ready; unblocked | no |
| **B** | **5.3 lift `run_suite` cascor-parallel refusal** (`run_suite.py:112`) | Ready except for an **external** gate: no released cascor carries #523 | no |
| **C** | **W-12 `csv_import` corpus**, both cascor and recurrence | Un-parked by Q-7; **scope widened** beyond the original question | no |
| **D** | **Q-10 dedicated `JuniperRecurrence` conda env** | Ready; provisioning + docs | no |
| **E** | **F-P1-4 snapshot lifecycle** — phases 6.1 identity → 6.2 index → 6.4 retention | Designed ([design](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)); 6.3 fixes ready | S-1/S-2 open |
| **F** | **§12 perf lane** P1→P4 then development | **Gated** (this note) | PF thresholds (P3) |
| **G** | **Wide-budget head-to-head campaign** (ml#1122) | **In progress**, concurrent session, GPU-bound | no |
| **H** | **Defect register outstanding work** (ml#1121) — 91 open defects | In progress, separate arc | no |

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
> |---|---|
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
> **Implementation trap for whoever picks this up:** `load_network` has **no production callers**.
> The live path is `lifecycle._load_snapshot_to_network`. A fix applied only to `load_network` would
> change nothing — which is precisely the error that made D-A look important.

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

| item | note |
|---|---|
| **PF threshold ratification** | Lands inside F-P3. The lane cannot finish its verification phase without it. |
| **S-1 / S-2** (snapshot design §9) | S-1 (move snapshots out of the checkout entirely) would make the fix structural. S-2 (is the March–April cohort of retained value?) is **deliberately not actionable** until E-6.2 can characterise it. |
| **S-3 / S-4** | Audit-log unification and the retention horizon — both correctly deferred to last. |

**Closed this round:** F-P1-2 (premise refuted), Q-6, Q-7, Q-8, Q-10.
