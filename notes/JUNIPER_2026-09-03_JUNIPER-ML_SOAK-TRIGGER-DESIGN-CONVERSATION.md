# What should trigger a soak? — a design conversation

**Project**: Juniper
**Sub-Project**: juniper-ml
**Author**: Paul Calnon
**Status**: Blue-sky design conversation — nothing here is a decision or a commitment
**Created**: 2026-09-03
**Protocol of record**: `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`
**Related**: `notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md`,
`util/soak_run_probe.py`, `util/systemd/juniper-soak-probe.{service,timer,path}`

---

## 0. How to read this

This is deliberately a conversation, not a specification. Ideas are ranked by how
much they'd teach us per session spent, and several are recorded specifically
because they are probably wrong in an interesting way. Nothing here should be
built without the usual scrutiny; the point is to widen the option set before
narrowing it.

One framing runs through all of it:

> **A probe costs a real session. The question is not "when is it convenient to
> run one" but "when would running one change what we believe?"**

Time-based triggers score badly on that question, and they are what we shipped
first — because they were easy, not because they were informative.

---

## 1. The reframe: triggers are a sampling strategy

The soak estimates a rate. Every trigger is a rule for *when to sample*, and
sampling rules have a property the current design never states: **they determine
what the estimate is an estimate OF.**

- Sample on a **timer** → you estimate the rate *averaged over calendar time*,
  which nobody has a decision riding on.
- Sample when the **index changes** → you estimate the rate *conditional on
  recent memory churn* — closer to interesting, still not a decision variable.
- Sample when someone is **about to make a relocation decision** → you estimate
  the rate *at the moment it is load-bearing*. That is the quantity the whole
  arc exists to inform.

That last one reframes the problem entirely: **the best trigger may not be a file
event at all, but a decision event.**

---

## 2. Candidate trigger classes

### A. The memory index changed

The obvious family, and what `util/systemd/juniper-soak-probe.path` currently
watches.

| Event                                  | Informative?                                           |
|----------------------------------------|--------------------------------------------------------|
| any write to `MEMORY.md`               | weak — peers rewrite it constantly; mostly noise       |
| a row **added** for a probed fact      | strong — a direct intervention on the thing under test |
| a row **removed** for a probed fact    | strong, and currently invisible                        |
| the index **crossed a size threshold** | interesting — see below                                |
| the index actually **TRUNCATED**       | **urgent**, and nothing watches for it                 |

**The truncation trigger deserves its own line.** The index has a hard cap and
truncation is silent and drops the NEWEST rows. If it fires, resident facts
vanish without any edit event — a state change no `PathChanged` watch would
characterise correctly, because the file *did* change, just not in the way the
watcher assumes. That is simultaneously a hazard alarm and the single most
interesting moment to probe: the population under test just changed underneath
the experiment.

### B. The pointed-to document changed

`docs/REFERENCE.md` is where all 15 pointers land.

- **Anchor moved or renamed** → `verify-probes` already catches this, CI-gated.
- **Prose under a stable anchor rewritten** → *nothing catches this.* The
  role-analysis document (`notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md`)
  records it as an unowned gap: `_slugs()` checks a heading exists, never that
  the fact still lives under it. A doc edit that keeps the heading and rewrites
  the sentence silently invalidates the probe.

So: **a content-hash change under a probe's anchor** is a trigger for
*re-validation*, not for measurement. Different purpose, same watcher.

- **The fact returns to `AGENTS.md`** → the probe becomes invalid by
  construction (it no longer tests a *relocated* fact). Worth an alarm, not a
  probe.

### C. The instrument changed

Easy to forget that the subject is software with a version.

- Claude Code version bump — context assembly is the mechanism under test.
- The launcher's default model switches (this project has a standing note that it
  does, periodically).
- A new memory feature ships.

**These are the events most likely to move the rate and least likely to be
noticed**, because nothing in the repo changes when they happen. A probe run
before and after a version bump is a genuinely controlled comparison.

### D. The registry changed

A probe added, retired, or its discriminator edited. Mostly a *re-baseline*
trigger: prior runs of that probe may not be comparable.

### E. Reality supplied a miss — the highest-value class

**Someone, somewhere, failed to retrieve a relocated fact and it cost something.**

- a defect filed whose root cause is a documented-but-unretrieved fact
- a PR review comment amounting to "you should have known X"
- a session asking the owner something answerable from a relocated fact
- a postmortem citing a fact that was written down and not followed

This is ground truth from the world rather than a synthetic task, and it lands
exactly where the corpus is weakest: `notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md`
§6b established that the ledger contains **two** misses, both the same probe, so
every claim about *failure* shapes rests on one probe's behaviour. Organic misses
are the only cheap source of miss diversity.

The catch is the one the protocol already knows: the organic arm can't bear a
verdict because its **denominator is unknown** — you see the misses that hurt,
not the occasions that passed silently. See §4 for an idea that might recover it.

### F. A decision is pending that the answer serves

The reframe from §1, made concrete:

- **a relocation PR is opened** — someone proposes moving more resident content
  out; the follow rate is precisely the input to whether that is safe
- a memory-budget ceiling raise is proposed
- an `AGENTS.md` cut is planned in any fleet repo

**This is the trigger with the clearest claim to being *right*.** It samples the
rate when a human is about to act on it, and it makes the measurement's purpose
legible instead of ambient.

### G. Absence-of-event triggers

Trigger on a *gap*: "the index changed 40 times and no probe has run in two
weeks." Accumulated unmeasured drift is itself a state worth sampling. This is
the honest version of a timer — a timer with a reason.

---

## 3. Three out-of-the-box ideas

### 3.1 Paired probes — stop measuring a rate, start measuring a difference

Today the design estimates one rate across sessions and compares its interval to
a boundary. But the *intervention* is per-fact: an index row exists or it
doesn't. So run the same probe twice — once with the row present, once with it
absent — and measure the **within-fact difference**.

- Controls for task difficulty, model tier, and session-to-session variance, all
  of which currently sit in the noise term.
- Turns "is the rate above 0.75?" into "does the row change behaviour?", which is
  the question the rung-1 intervention actually asks.
- Trigger becomes: **whenever an index row is about to be added or removed**,
  probe immediately before and immediately after.

Cost: two sessions per data point instead of one. Probably worth it — the current
design needs ~35 runs to say anything, and has spent 36 to reach INCONCLUSIVE.

**Risk worth naming:** deliberately removing a row to create the control arm is
an intervention on live memory that other sessions are reading. That is not free
and might be unacceptable.

### 3.2 Retrospective scoring — probe zero sessions

The organic arm is descriptive-only because the denominator is unknown. But the
denominator is only unknown because nobody looks for it.

Every session leaves a tool log. If you can mechanically detect *"this session
worked in the subject area of probe P"* — it touched the files the fact is about,
or ran the command the fact governs — then you have an **occasion**. Whether it
also read the pointer document is already mechanically decidable (that is exactly
what `retrieval_channel()` in `util/soak_run_probe.py` computes).

Occasion + retrieval channel = an observation, at **zero marginal session cost**,
from work that was happening anyway.

This would be the single biggest change to the economics of the whole arc. It
also converts the trigger question into a *detector* question: not "when should I
spend a session" but "how do I notice one already happened".

**Why it might fail:** "worked in the subject area" is a fuzzy predicate, and a
loose one manufactures occasions that were never really occasions — inflating the
denominator and deflating the rate. It would need the same instrument-adequacy
scrutiny as everything else here, and it is exactly the shape that reads
plausible while being wrong.

### 3.3 Negative controls as a first-class trigger

Probe a fact that was **never relocated** — one still resident in `AGENTS.md`.
If the "follow" rate on those looks like the rate on relocated facts, the probe
suite is not measuring relocation; it is measuring something else (task shape,
tool habits, how the question is phrased).

Trigger: run one negative control for every N real probes, automatically.

The 2026-08-21 pilot is the argument for this: **9 of 15 probes turned out to
test facts that had never been relocated**, and that was discovered by hand.
A standing negative-control arm makes that class of error self-announcing rather
than dependent on someone thinking to check.

---

## 4. Anti-triggers — when NOT to run

Worth designing as deliberately as the triggers, because each of these turns a
spent session into a worthless or misleading row.

- **Terminal verdict reached** — implemented; the wrapper refuses on
  `BET-FAILING` / `HOLDS-AT-*` unless `--force`.
- **`verify-probes` failing** — a broken pointer means the run measures the
  pointer, not the agent. Cheap to check, currently not checked at dispatch.
- **The index is mid-edit or over cap** — sampling a transient state.
- **A probe is already in flight** — systemd handles this for the unit path only.
- **The host is busy with an experiment stack** — a probe competing with a live
  campaign is bad for both.
- **The same probe ran very recently** — the least-covered selection rule mostly
  handles this, but not against a burst trigger.

---

## 5. Ranking by information per session

Rough, and the ordering is the argument, not the numbers.

| Rank | Trigger                                             | Why                                                        |
|------|-----------------------------------------------------|------------------------------------------------------------|
| 1    | **Organic miss observed** (§2E)                     | ground truth; fixes the miss-diversity gap; near-zero cost |
| 2    | **Relocation decision pending** (§2F)               | samples the rate when it is load-bearing                   |
| 3    | **Index row added/removed for a probed fact** (§2A) | direct intervention on the thing under test                |
| 4    | **Instrument version changed** (§2C)                | most likely to move the rate; currently invisible          |
| 5    | **Index truncation** (§2A)                          | hazard + population change in one event                    |
| 6    | **Accumulated drift with no recent probe** (§2G)    | the honest timer                                           |
| 7    | any write to `MEMORY.md` (§2A)                      | mostly noise; what we shipped                              |
| 8    | pure calendar timer                                 | measures nothing in particular; a floor, not a plan        |

The two things currently wired are ranked 7 and 8.

---

## 6. Questions this conversation should put to the owner

1. **Is the soak's purpose to produce a verdict, or to inform relocation decisions?**
If the latter, §2F should probably be the primary trigger and the timer becomes a fallback.
2. **Is deliberately removing an index row acceptable?**
To create a paired control (§3.1)? It is an intervention on live shared memory.
3. **Is retrospective scoring (§3.2) worth prototyping**
Given it could make probes nearly free but risks a fuzzy denominator?
4. **Should negative controls be a standing arm?**
(§3.3) And not just a one-off audit?
5. **What is a probe worth?**
Everything above is a ranking by information per session, and none of it can be traded off properly without a rough sense of what one session costs relative to a wrong relocation decision.

## 7. What this document is not

Not a plan, not a recommendation, and not costed. Several ideas here — §3.2
especially — would need the full instrument-adequacy treatment before anyone
built them, and §3.1 has an ethical-ish question about mutating shared memory
that a design note cannot settle.

---

## 8. Question 1, answered — and it reorders the product, not just the triggers

**Owner, 2026-09-03: "the soak exists, most importantly, to inform relocation
decisions."**

§6 flagged this as the question that governs the rest. It does, and it reaches
further than the trigger ranking.

### 8.1 The pooled rate is close to useless for the stated purpose

Per-probe outcomes, after the 2026-08-31 re-score:

| Group | Probes | Runs | Follows | Rate |
|---|---|---|---|---|
| **never follow** | 4 — P14, P15, P19, P23 | 10 | 0 | **0%** |
| **follow-dominant** | 11 — the rest | 26 | 24 | **92%** |
| pooled | 15 | 36 | 24 | **66.7%** |

The distribution is **bimodal**, and the headline 66.7% describes **neither**
group. As a verdict about "relocation in general" it is a defensible summary. As
an input to *"should I relocate this section?"* it is close to meaningless: the
honest answer is either ~0% or ~92% depending on which stratum the fact lands in,
and 66.7% is never the right estimate for any actual decision.

**This is the single largest consequence of the answer.** Under a verdict
purpose, the pooled rate with its interval is the product. Under a
decision-support purpose, the pooled rate is a mixture statistic and the
*stratum* is the product.

### 8.2 The blocker is not more runs — it is that nothing predicts stratum membership

If a decision needs to know which stratum a candidate fact falls into, something
must predict membership *before* the fact is relocated. Every obvious candidate
fails against the existing data:

- **`severity`** — hazards sit in both groups (P14, P23 never follow; P02, P16,
  P20, P21, P25 are follow-dominant).
- **`area`** — `ports` splits **across both groups**: P19 never follows, P24
  always does. Same area, opposite behaviour. This is the sharpest single
  refutation available.
- **"has a nearby test or owning script"** — the ledger's own proposed
  explanation (`JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` §14).
  Refuted: P21 has a test (`tests/test_juniper_chop_all.py:662`) and follows;
  P02 has `tests/test_assert_release_tag.py` and follows 3 of 4.

So the arc has established, at real cost, that **two sharply separated strata
exist** — and has not established what puts a fact in one rather than the other.
That is the actual blocker to decision support, and no number of additional runs
at the pooled level removes it. More runs sharpen an interval nobody needs.

**The next question is therefore a characterisation question, not a sampling
one:** what distinguishes P14/P15/P19/P23 from the other eleven? Candidate
angles worth examining — none tested yet — include how *findable* the fact is by
a plausible grep of the task's own vocabulary, whether the task can be completed
correctly *without* the fact (making retrieval optional rather than necessary),
and whether the fact contradicts a plausible default the agent already holds.

### 8.3 The stopping rule now keys on the wrong signal

`util/soak_run_probe.py` refuses to run when the verdict is terminal
(`BET-FAILING` / `HOLDS-AT-*`) unless `--force`. That rule was written under the
verdict model, where a terminal verdict means the question is answered and
further spend cannot change it.

Under decision support the premise fails: **relocation decisions keep arriving,
and each one needs current evidence about its own stratum.** A pooled verdict
being terminal says nothing about whether the next candidate section is safe to
move. The guard is not harmful — it still prevents unattended runaway spend — but
it is keyed on a signal that is no longer the product. A decision-support
stopping rule would key on something like *no pending relocation decision AND
adequate recent coverage of the relevant stratum*.

Left in place for now; flagged so it is changed deliberately rather than
discovered later.

### 8.4 The trigger ranking, re-sorted under the answer

§5 ranked by information per session in the abstract. Re-sorted for decision
support, the top of the list changes character:

| Rank | Trigger | Why it moved |
|---|---|---|
| 1 | **relocation decision pending** (§2F) | was 2nd; now the *definition* of when the answer is needed |
| 2 | **organic miss** (§2E) | unchanged — still the only cheap source of miss diversity |
| 3 | **characterisation probes** (new) | deliberately probing to separate the strata, not to sharpen the pooled rate |
| 4 | index row added/removed for a probed fact (§2A) | unchanged |
| … | timer, any-write | still a floor, now explicitly *only* a floor |

Rank 3 is new and follows directly from §8.2: if membership is unpredictable, the
highest-value probes are the ones chosen to *discriminate between competing
explanations of membership* — not the least-covered probe, which is what the
dispatcher currently picks. **Least-covered selection optimises for an even
pooled estimate, which is the statistic the answer just demoted.**

### 8.5 What this does not change

- The subject is still irreducible; automating it away still deletes the
  experiment.
- Scoring is still a judgement, and the calibration set still cannot validate its
  own safety property (two misses, one probe).
- `verify-probes` still is not checked at dispatch.

---

## 9. Characterisation probes run, 2026-09-04 — §8's claim half survives

Four probes were run to test §8.1's bimodality claim, selected to resolve stratum
membership rather than to even out coverage: **P21** (the only split probe),
**P14** and **P23** (both 0/2, to confirm never-follow), and **P06** (n=1, the
weakest evidence in the follow group). Corpus: 36 → **40 runs**.

### 9.1 Results

| Probe | Before | Run outcome | After |
|---|---|---|---|
| P21 | 1 follow, 1 src-rec | **source-recovered** | 1/3 |
| P14 | 0 follow, 2 src-rec | **source-recovered** | 0/3 |
| P23 | 0 follow, 2 src-rec | **FOLLOW** | 1/3 |
| P06 | 1 follow | **follow** | 2/2 |

All four answers were **correct**. Three reached the fact from source; P23 and
P06 read `docs/REFERENCE.md`.

### 9.2 §8.1's membership assignment was over-read

**P23 moved out of the never-follow group on its third run.** Its 0/2 was
small-sample noise, not a stratum property — and it was one of the four probes
§8.1 named as never-follow. The group shrank 4 → 3, and the follow-dominant
rate fell 92% → 84%.

Worse for the original framing: **not one probe's interval excludes 50%.**

| Probe | f/n | 95% CI |
|---|---|---|
| P14, P15, P19 | 0/3 | **[0.00, 0.56]** |
| P21, P23 | 1/3 | [0.06, 0.79] |
| six probes | 2/2 | [0.34, 1.00] |
| P02 | 3/4 | [0.30, 0.95] |

No probe's interval excludes the pooled 65%. Individually, **nothing is pinned
down**, and "P14 never follows" is not a supportable claim from 0/3.

### 9.3 But the strata are real — tested, not eyeballed

The right question is not whether any single probe is extreme; it is whether the
*pattern* of variation exceeds binomial noise. Permutation test, 20,000 draws,
null = all 15 probes share the pooled rate:

```
probes=15  runs=40  follows=26  pooled p=0.650
observed heterogeneity statistic = 30.84
permutation p-value = 0.0017
```

**p = 0.0017.** The probes do not share one rate. So:

- **§8.1's core claim survives and is now supported rather than eyeballed** — the
  pooled rate is a mixture, and it is the wrong estimate for any specific
  relocation decision.
- **§8.1's membership assignment does not.** Which stratum a *given* probe
  belongs to is not established at n=2–4, and P23 is the proof.

These are not in tension. "These probes differ" and "I cannot tell you where this
one sits" are both true, and for decision support the second is the binding
constraint.

### 9.4 What this means for the next step

More runs *do* now have a purpose they lacked in §8.2 — not to sharpen the pooled
interval, but to resolve **per-probe membership**, which is what a relocation
decision needs. The cheapest informative design is to drive the ambiguous probes
to n≈8–10 rather than spreading runs evenly: P21 and P23 (both 1/3, maximally
uncertain) and the three 0/3 probes.

The predictor gap from §8.2 is unchanged and remains the deeper blocker: even
with membership resolved for these 15, nothing yet predicts the stratum of a
*new* fact, which is what a relocation decision actually faces.

### 9.5 Two instrument findings from the run

- **A parser defect ate a completed run.** `parse_events` assumed
  `ev["message"]` is always a dict; some stream-json events carry it as a bare
  string, and `.get` on it raised `AttributeError` *after* the session had been
  spent. Fixed by guarding the type. The P21 run was recovered by re-parsing its
  saved `stream.jsonl` rather than re-running — which is the argument for keeping
  the raw transcript rather than only the parsed status.
- **The retrieval channel can false-positive, and P06 is where it nearly did.**
  That probe's task involves constructing a command containing
  `--dest docs/REFERENCE.md`, so the pointer path appears in the answer whether or
  not the document was read. Checked by hand: P06 really did read it (`grep` over
  its headings, then `sed -n '1240,1330p'`). The mechanical channel was right here
  but is **not** reliable for probes whose pointer path is also a command
  argument, and that limitation was not previously recorded.

### 9.6 A discriminator that under-specifies

P06's frozen discriminator offers two acceptable paths — scope the flag to
relocation PRs, or refuse — and calls unconditional adoption the miss. The
session took a safe **third** path: adopt on every PR, but classify the vacuity
exit 2 as SKIP-never-PASS while any other exit 2 stays FAIL, verified against the
live tool and pinned by a test on the marker string. The harm the discriminator
names is explicitly prevented, so the session demonstrably held the fact.

Scored a follow, with the tension recorded rather than smoothed. It is a
**registry-author** item: a discriminator that enumerates acceptable answers
rather than stating the property will mis-score any better answer nobody thought
of.

---

## 10. The bet failed — and two findings that complicate reading it

Continuing §9.4's design (drive the ambiguous probes toward n≈8–10) produced
three more runs and a terminal verdict.

### 10.1 BET-FAILING

```
runs 43   follows 26   misses 2   src-recovered 15
rate      60.5%   95% CI [0.456, 0.736]   boundary 0.75
retention 95.3%   95% CI [0.845, 0.987]
verdict   BET-FAILING  (upper bound is below the boundary)
```

The pointer-follow rate's **upper bound is now below 0.75**. The bet the arc was
built to test has failed.

**But retention is 95.3%.** Read together, these say something sharper than
either alone:

> **Relocation does not lose facts — and pointer-following is not what prevents
> the loss.** Agents overwhelmingly still obtain a relocated fact (95.3%), but
> they get it by reading the source, not by following the pointer (60.5%, and
> that is now an upper-bounded failure rather than an open question).

For the decision the soak exists to inform, that is a *usable* answer, and not
the one the boundary was set to detect. Relocation looks safe. The mechanism
credited for its safety was the wrong one.

### 10.2 The retrieval channel was over-reporting follows — found live

P15's run reported `pointer doc referenced: True`. A hand audit found **zero tool
calls touching `docs/REFERENCE.md`**; the answer merely *named* the file ("before
the `docs/REFERENCE.md` relocation cut it to ~35k").

Cause, in `util/soak_run_probe.py`: `retrieval_channel` searched tool inputs
**plus the answer text**. So any run that recited the pointer's path scored as a
follow — and a model reciting a path without opening it is the strongest possible
example of *not* following the pointer. The channel credited the exact opposite
of what it measured.

Fixed (tool inputs only) with three regression tests; a positive control that
reintroduces the defect fails two of them. **All prior automated runs
re-audited**: P23 (2 tool calls) and P06 (7) are genuine follows and their scores
stand; P02 was correctly scored. **Only P15 was affected**, and it was caught
before recording — it is filed source-recovered.

This matters beyond one row: the channel is the part of scoring that
`notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md`
argued was *"mechanical, not a judgement"* and therefore safe to automate. It was
mechanical and it was wrong, in the direction that inflates the headline.

### 10.3 A third retrieval channel the scoring model has no category for

P19's session wrote, in its own reasoning and with **no tool call retrieving it**:

> *"The memory note about port checks fail-opening is relevant here."*

P19 is one of the four rung-1 probes. That fact was in its context because of the
`Port check fail-opens` index row added 2026-08-31. The session used the
**index**, not the pointer and not the source.

The model has two categories — follow and source-recovered — and this is neither.
Call it **index-recovery**. It matters because rung 1's whole hypothesis was that
index rows aid retrieval: if the intervention works by making the fact resident,
it will never show up as a pointer *follow*, and §15.3's prediction that rung 1
"will not move the follow rate" could be **correct and irrelevant at the same
time**.

**Do not over-read this.** It is 1 observation across the 4 rung-1 probes, and
the detector only catches sessions that say so explicitly — silent index use is
invisible. **1/4 is a floor, not an estimate.** The honest claim is that a
category is missing, not that it is common.

### 10.4 The stopping rule fired, exactly as §8.3 predicted

Attempting the fourth run hit:

```
REFUSING: soak verdict is BET-FAILING -- terminal.
```

§8.3 flagged this guard as keyed on a signal the Q1 answer had demoted. It has
now actually blocked per-probe characterisation work — which the *pooled* verdict
says nothing about. The guard behaved as designed; the design is what is wrong
for the current purpose.

`--force` exists for this, but a terminal verdict is an owner-facing event, not
something to push through silently.

### 10.5 State

| Probe | f/n after this batch |
|---|---|
| P21 | 1/4 |
| P15 | 0/4 |
| P19 | 0/4 |
| P14 | 0/3 (run not attempted — blocked) |
| P23 | 1/3 (run blocked) |

Open: whether to `--force` and continue characterisation now that the pooled
question is closed, and whether **index-recovery** should become a scored outcome
(a registry- and ledger-level change, not a scorer's call).
