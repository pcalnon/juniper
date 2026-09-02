# What a Claude session is actually doing in the soak workflow, and what can be automated away

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**Status**: Analysis — one recommendation is an owner decision, nothing implemented
**Created**: 2026-09-02
**Subject**: `util/soak_run_probe.py`, `util/soak_next_probe.py`, `util/soak_ledger.py`
**Protocol of record**: `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`

---

## 1. Why ask the question at all

`util/soak_run_probe.py` (ml#1561) automated dispatch, execution and evidence
capture. The obvious follow-up is "how much more can go?" — and the honest answer
requires separating roles that all happen to be performed by the same kind of
actor. A Claude session appears at four distinct points in this workflow, and
they have completely different automation properties. Treating them as one thing
is how you either under-automate the mechanical parts or, much worse, automate
away the measurement itself.

## 2. The roles (four named; review found more)

| # | Role | What it does | Automatable? |
|---|---|---|---|
| 1 | **Subject** | answers the probe task | **Never** — it *is* the measurement |
| 2 | **Orchestrator** | select probe, dispatch, capture, classify channel | **Done** (ml#1561) |
| 3 | **Scorer** | judge the answer against the frozen discriminator | **Candidate** — see §4 |
| 4 | **Interpreter** | verdict semantics, escalations, scoring-model changes | **No** — owner policy |
| 5 | **Registry author** | writes probes, discriminators, `must_be_absent_from_source` | **No** — and it is the highest-leverage judgement here |
| 6 | **Analyst** | writes the document the owner acts on (this note is an instance) | **No** — and it is where self-interest bites |

Rows 5 and 6 were missing from the first version of this table, which claimed to
enumerate every point a session appears. Row 5 matters most: a badly scoped
discriminator or an incomplete `must_be_absent_from_source` list predetermines
every future run of that probe, and the 2026-08-21 pilot found **9 of 15 probes
invalid** for exactly that reason. `cmd_verify_probes` checks the list against
`AGENTS.md`; nothing checks that the list is *exhaustive*.

A related gap with no owner at all: `_slugs()` (`soak_ledger.py:625-633`) fails a
probe whose pointer ANCHOR disappears, and CI runs it — but it never re-reads the
prose under that heading. A doc edit that keeps the heading and rewrites the
sentence carrying the fact passes `verify-probes` cleanly while silently
invalidating the probe. Structural drift is gated; **semantic drift under a
stable anchor is not, by anyone.**

### 2.1 The subject is irreducible, and that is not a limitation

Role 1 cannot be automated away because automating it away deletes the
experiment. The soak measures *what a Claude session does when it needs a
relocated fact*. A cheaper actor answering the probe would measure that cheaper
actor. This is worth stating plainly because "reduce the number of sessions" is
otherwise an obviously good goal, and here it has a floor of exactly one.

### 2.2 The orchestrator is already gone

Probe selection, dispatch, transcript capture, and the **retrieval channel** —
did the run read the pointer document or reach the fact from source — are all
mechanical. The channel in particular is a file-path question, not a judgement,
which is why it was safe to automate in ml#1561 while correctness was not.

## 3. So the whole question is role 3

Sessions per probe run today: **two** — one subject, one scorer. Automating the
scorer takes that to **one**. It cannot go to zero (§2.1). That is the entire
available saving, and it is worth being precise about whether it is safe.

## 4. The scorer: one tempting design, empirically refuted

### 4.1 The tempting design

Every probe in `conf/soak_probes.json` carries `must_be_absent_from_source` — a
list of phrases, e.g. P02's `["ref_type", "--ref-name"]`. It reads like a
ready-made scoring oracle: *if the answer contains a miss phrase, score a miss.*

**It is not one, in two independent ways.**

### 4.2 It is a registry-integrity field, not a scoring field

`util/soak_ledger.py:647-691` uses `must_be_absent_from_source` to assert the
phrases are absent from **`AGENTS.md`** — proving the fact genuinely *left* the
source, so the probe tests a relocated fact rather than a resident one. It says
nothing about answers. Using it to score is a category error, and a tempting one
precisely because the field name reads as scoring-adjacent.

### 4.3 The only real automated run already breaks it

The first automated run (`P02-assert-release-tag-ref`, session `3a9e07ae`,
recorded in `reports/soak/pointer_follow_soak.jsonl`) was scored **correct**. Its
answer contains `ref_type` **twice** — at `answer.md:31` and `:66`, in the
sentence that gets the fact *right*:

> **`--ref "${{ github.ref }}"`, not `github.ref_name`** — the script takes the
> fully-formed ref and uses the `refs/tags/` prefix as its tag-vs-branch
> discriminator

A keyword scorer would have marked this **miss**. The failure mode is general and
not fixable by better keywords: **an answer that explains why the wrong thing is
wrong necessarily contains the wrong thing.** Negation, contrast and warning are
the normal shapes of a *correct* answer to a hazard probe.

Precision, since the counter-example is load-bearing: of P02's two forbidden
phrases, only `ref_type` appears (twice). `--ref-name` appears **zero** times —
the answer writes `github.ref_name`, the dot form, not the hyphenated flag. So
the disagreement is driven by one phrase, not both, and a scorer requiring *all*
forbidden phrases would have coincidentally agreed here. That coincidence is not
a defence: the mechanism (correct answers quote what they reject) is unchanged,
and it would fire on the first answer that happened to name the flag form too.

### 4.4 The discriminators, classified — and a correction

**An earlier draft of this section claimed "all fifteen are semantic; zero of
fifteen are mechanically decidable". Adversarial review classified them one at a
time and that framing is wrong.** It was written from a shape impression — every
discriminator reads *"Does the session [state / recognise / refuse / preserve]
X? [Doing Y] is the miss"* — rather than from a per-probe classification. A
universal quantifier asserted from a sampled impression is the exact escalator
the [consensus procedure](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) §3 names.

The measured classification:

| Class | Count | Probes |
|---|---|---|
| fully, robustly mechanically decidable | **0** | — |
| partially decidable (real literal or numeric signal) | **2–3** | P02, P14, (P16 — see below) |
| semantic only | **12–13** | P06, P07, P08, P15, P18–P25 |

- **P02** carries literal CLI tokens (`--ref`, `--ref-type`, `--ref-name`).
- **P14** is the strongest case: *"keep `per_run_timeout_seconds` above the wall
  budget and tighten `max_wall_seconds`"* is a **numeric comparison between two
  named keys**, which a parser can decide outright *if* the answer states both
  values. Prose without numbers ("raise it comfortably above") falls back to
  semantics.
- **P16** was offered as partially decidable on the strength of a `candidates[0]`
  code token. That token is **not in the registry** — it is an inference about
  what a wrong answer would contain. Recorded as the weakest of the three.

**What survives, and it is the operative point:** *zero of fifteen are robustly
decidable by naive keyword presence*, including all three partials. The corrected
claim is narrower than the original and still supports §5 — scoring cannot be
automated by keyword matching, though P14-shaped probes show a *typed predicate*
(compare two named numbers) is not inconceivable for a minority of the registry.

## 5. The design that could work, and how to know if it does

If role 3 is automated, it must be **a separate headless session given only the
answer and the discriminator** — not the subject (which would be marking its own
work), and not the orchestrator.

The orchestrator half needs restating: a stateless CLI that exits after one run
has no memory and no reward, and cannot "have a stake" in anything -- the
original phrasing anthropomorphised a Python script. The real concern is
**context leakage into a scoring SESSION**: if the same session both progresses
the corpus and judges the answers, the coverage state is in its context while it
judges. That concern was sound and the implementation still leaked -- see
Sec 6b finding 3.

**It must not be trusted on assertion.** There is an answer key of **36 scored
runs**. A candidate scorer can be run against them blind and its agreement
measured.

**But the key is far weaker than that count suggests, and this is decisive for
the design.** Of the 36: 24 follows, 10 source-recovered, and **2 misses -- both
the same probe** (`P15`). So the criterion that actually matters can be exercised
against two examples of one probe.

Any bar therefore has to be stated in terms the set can support:

- an **outcome-agreement** figure over 36 rows -- available now, but note that
  ">= 34/36" is numerically identical to today's retention (34/36) and so restates
  the current tally rather than expressing an independent risk appetite;
- **zero human=miss -> machine=follow** -- exercisable on n=2, one probe. A pass
  means "does not fail on P15-shaped misses", nothing broader;
- **miss-CLASS agreement**, which the original bar omitted entirely even though
  `soak_ledger.py:327` fires the rung-2 hazard escalation on `miss_class` and not
  on the outcome.

The honest conclusion is that **the calibration cannot be run meaningfully until
the corpus contains labelled misses from more than one probe** -- which the
re-soak will produce, or will not, and either way that is the prerequisite.

Below that bar, scoring stays human-directed. The asymmetry matters: a machine
that under-reports misses converts the soak into the confirmation procedure v0.2
was built to eliminate.

## 6. What must never be automated, regardless

- **The subject** (§2.1).
- **Changing the scoring model** — e.g. the 2026-08-31 source-recovered
  re-score. The ledger already forbids the adjacent move (*"Do NOT run [resolve]
  to make `status` exit 0"*), and a re-score that drops rows from the denominator
  converts INCONCLUSIVE into a pass by redefinition.
- **Discharging escalations** — a machine that discharges its own alarms is not
  an instrument.

## 6a. Adversarial review — what it changed

Reviewed under the [consensus procedure](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md):
two Lane A (independent entry points: the reaper source; the probe registry) and
two Lane B (this note; the systemd units). Every finding below was re-derived by
the author before acceptance.

**Corrections to this note:**

| Claim | Outcome |
|---|---|
| "all 15 discriminators semantic, 0 mechanically decidable" | **Overstated** — 0 fully, 2–3 partially (P02, P14), 12–13 semantic-only. Fixed in §4.4 |
| The ≥34/36 calibration bar | **Underived, and not independent of the data** — retention is currently 34/36 exactly, so the bar restates today's tally |
| "a real calibration experiment with a known ground truth" | **Overstated** — see §6b |
| four-role taxonomy is complete | **Incomplete** — see §6b |
| "the orchestrator has a stake in coverage numbers" | **Anthropomorphic** as written about a stateless script; the real concern is session context leakage, and the artifact leaked it — see §6b |

## 6b. Four findings that change the recommendation

1. **The calibration set cannot validate its own headline safety property.**
   The bar's load-bearing half is "zero disagreements of the shape human=miss,
   machine=follow". There are **exactly two** effective misses in the whole
   ledger, and **both are the same probe** (`P15-worktree-converge-not-remove`,
   obs `72d17be5`, `3eaabad5`). A pass certifies only that a scorer does not
   fail on P15-shaped misses; the other 14 probes have **zero** labelled miss
   examples. This is close to a probe that cannot produce a non-zero — the
   inadequacy the consensus procedure §2 names.

2. **Miss-CLASS agreement is not in the bar at all**, and it is the more
   consequential judgement. `soak_ledger.py:327` fires the rung-2 hazard
   escalation on `miss_class`, not on the outcome. A scorer could clear ≥34/36
   on outcomes while relabelling a hazard miss as `discoverability`, suppressing
   an escalation without ever failing the gate — the exact direction §6 says must
   never be automated.

3. **The isolation design leaked the thing it isolates against.**
   `soak_next_probe.py:113` prints a `post-interv. : N run(s)` coverage line, and
   `soak_run_probe.py` embedded `--reveal`'s stdout verbatim into
   `scoring_packet.md`. The "separate scorer with no stake in coverage" was
   therefore handed the coverage tally, beside the discriminator, in the one
   artifact built to implement the separation. **Fixed** — the packet is now
   redacted.

4. **The dispatch path had no stopping rule.** Neither `soak_next_probe.py` nor
   `soak_run_probe.py` consulted the verdict, so an enabled timer would keep
   spending sessions after the soak reached a terminal answer — spend that
   cannot change a conclusion. **Fixed** — the wrapper now refuses on
   `BET-FAILING` / `HOLDS-AT-*` unless `--force`.

Findings 3 and 4 are code defects, now closed. Findings 1 and 2 are defects in
the **proposal** and are carried into §7 and §8 rather than fixed, because they
change what the calibration would have to be.

## 7. What this analysis does not establish

- **That an automated scorer would pass the §5 bar.** Nobody has built or run
  one. The bar is proposed so the question is decidable, not answered.
- **That two sessions per run is expensive enough to be worth removing.** No cost
  measurement was taken. The saving is at most one session per probe run, against
  a corpus of 15 probes needing a handful of runs each.
- **Whether probes could be redesigned to have mechanically-checkable outcomes.**
  Considered and set aside: it would invalidate the frozen registry and make the
  36 recorded runs incomparable — a far larger cost than the scoring it saves.
- **Whether the calibration set has the power to certify what the bar claims.**
  It does not, today — see §6b finding 1. This is distinct from "nobody has run
  it yet": even a clean pass on this corpus would not support the general claim.
- **Whether retrieval propensity is model-tier-dependent.** §2.1 asserts the
  subject is irreducible because a cheaper actor "would measure that cheaper
  actor". That is an assumption, not a result. The protocol's own definition of
  the bet is a tool-call-observable fact (*did the session open the destination*),
  which `retrieval_channel()` already computes mechanically — so the possibility
  that retrieval propensity is driven by harness and task structure rather than
  model tier was never tested. If it is harness-driven, a cheaper subject could
  be valid for the primary axis, with full-tier sessions reserved for probes a
  cheap pre-screen cannot resolve. The floor of "exactly one full-tier session"
  is therefore asserted, not proven.
- **Which model answered any given probe.** The dispatch command carries no
  `--model` flag and `meta.json` does not record one. If the subject session "is
  the measurement", its identity is an uncontrolled and unlogged variable — and
  this project's own memory records that the launcher default switches
  periodically.

## 8. Recommendation

**Automate nothing further right now.** Roles 1 and 4 are closed by definition,
role 2 is done, and role 3 is a *decidable* question that has not been decided
because the calibration in §5 has not been run.

The proportionate next step is the calibration itself — build a candidate scorer,
run it blind against the 36-row answer key, report agreement. That is a
measurement, not a commitment, and it costs one afternoon rather than the
integrity of the instrument.
