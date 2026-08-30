# Independent Agent Consensus — verification procedure for measurements and conclusions

**Project**: Juniper (ecosystem-wide working practice)
**Author**: Paul Calnon
**Status**: Adopted 2026-08-30
**Applies to**: any measurement or conclusion that will be written into a document of record,
used to close a finding, or used to justify shipping or reverting a change.

---

## 1. Why this exists

Every failure this procedure targets was found the same way: **by re-deriving something from its
source, not by re-reading a report of it.** In the 2026-08-29/30 juniper-canopy E2E session alone:

| what failed                                                                       | how it was caught                                              | how it was NOT caught                                                     |
|-----------------------------------------------------------------------------------|----------------------------------------------------------------|---------------------------------------------------------------------------|
| "the store never advances" — read from the first 4 lines of a 35-line log         | replaying the probe over its own archive                       | four documents quoted the conclusion; an adversarial fact-check missed it |
| "zero `no_update` can only happen if…" — reasoned from 1 of the store's 2 writers | a second adversarial pass, prompted to refute                  | the first review pass accepted it                                         |
| a hazard promoted because it "already cost a P0/P1"                               | re-reading the ledger before quoting it to a peer              | it had been asserted twice already                                        |
| "both signals ride as `State`"                                                    | a peer checking the callback SIGNATURE, not the prose about it | the prose had been read completely and carefully                          |
| a PR watcher declaring a suite terminal mid-run                                   | comparing its verdict against the shared waiter                | it had shipped, reviewed, one PR earlier                                  |

The common shape is **a correct local reading generalised past the evidence actually examined**.
Review of the *writing* does not catch it, because the writing is internally consistent. Only
re-derivation from the artifact catches it.

**Corollary that makes this non-optional:** accepting a peer's or an agent's correction without
re-deriving it is the same error, merely outsourced. Two corrections exchanged with a peer session on
2026-08-29 were themselves partly wrong, and both were caught only because the *receiver* re-measured.

---

## 2. The two lanes

Verification splits into two independent lanes. **Do not let one agent do both** — an agent that
produced a measurement is the worst possible reviewer of what it means.

### Lane A — Measurement re-creation (observations)

An observation is verified when an agent that did **not** produce it re-derives it from primary
artifacts and reports the same value.

Requirements:

- **Independent ENTRY POINTS, not just independent agents.** Three agents all starting from the same
  summary paragraph are one agent with three seats. Give each a genuinely different route to the same
  fact — e.g. for a census: (a) start from the ledger's claim and trace numbers to artifacts, (b) start
  from git/PR history, (c) start from the raw evidence tree. Convergence then means something.
- **Artifact over prose, always.** A claim in a commit message, PR body, or notes file is a *claim*.
  Where a declaration exists — a function signature, a config block, a log file, a schema — the
  declaration is the evidence and the prose is a claim about it.
- **Absence must be reportable.** Every prompt must make "NO ARTIFACT" / "UNTRACEABLE" an allowed and
  expected answer. Without that, an agent will reconstruct the expected number from the narrative.
- **Instrument adequacy is part of the observation.** "Could this instrument have produced a different
  answer?" is a required question, not a nicety. A zero from a probe that cannot produce a non-zero is
  not a measurement.

### Lane B — Analysis review (conclusions)

A conclusion is verified when independent agents attack it and it survives.

Requirements:

- **Prompt to REFUTE, not to check.** "Verify this analysis" yields agreement. "Find where this
  reasoning fails; a finding that it is sound is worth nothing" yields defects.
- **Steelman both directions when a decision is at stake.** For a revert/reinstate or ship/hold
  decision, run one agent arguing each side on the same evidence. Asymmetric review produces
  asymmetric confidence.
- **Different lenses, not different wording.** Vary what each reviewer is told to care about —
  correctness, omission (amputation), false authority, actionability, self-serving framing. Reviewers
  given the same lens duplicate each other.
- **Analysis review runs on the RECONCILED measurement**, not on the raw claim. Lane A first.

---

## 3. Sizing the review

Pool size and iteration count scale with **uncertainty × criticality**. Both axes, not either alone.

| | **Low criticality** (local, easily reversed) | **High criticality** (document of record, gates a ship/revert, closes a finding) |
| --- | --- | --- |
| **Low uncertainty** — directly measured, instrument known good, result reproduced | 0–1 reviewers. Self-check by re-running the instrument. | 1–2 Lane A. Confirm the instrument could have produced a different answer. |
| **Medium uncertainty** — measured once, or derived from a measurement | 1 Lane A | 2 Lane A + 1–2 Lane B adversarial |
| **High uncertainty** — inferred, small sample, instrument novel or previously wrong, or the conclusion overturns a standing one | 1–2 Lane A + 1 Lane B | **3+ Lane A (distinct entry points) + 2+ Lane B (opposing briefs), and at least 2 iterations** |

**Escalators — each one moves the cell up:**

- the conclusion would **overturn** something already written into a document of record;
- the measurement rests on a **sample size below ~5**, or on a single session;
- the instrument is **new**, or has been wrong before;
- the claim contains a **universal quantifier** (never / always / every / only / not once);
- a **fix or revert** hangs on it;
- the finding is **convenient** — it confirms what the author already believed.

**De-escalator, and only this one:** the result has been independently reproduced end-to-end by a
different instrument. Nothing else reduces required rigour — not confidence, not seniority, not how
carefully the prose was written.

---

## 4. Iteration

One round is a check; two rounds is a process. Run a second round when **any** of these holds:

- round 1 produced corrections (**the fix pass is the least trustworthy part of any document** — it is
  written fastest, under the belief that the hard thinking is done, and it is where new errors enter);
- reviewers disagreed with each other;
- the conclusion changed as a result of round 1;
- the work is in the top-right cell of §3.

**Brief round 2 explicitly on the corrections**, not on the whole artifact: "these N changes were made
in response to round 1; find what they broke." On 2026-08-29 a round-2 pass briefed exactly that way
found that the round-1 correction had *restored a question already answered and closed* — an error
created by the fix, invisible to anyone reviewing the document as a whole.

**Termination.** Stop when a round produces no finding that changes a number, a disposition, or an
action. Do not stop merely because reviewers agree — agreement among reviewers who share an entry
point is not evidence (§2 Lane A).

---

## 5. Processing the results — the reconciler's job

The orchestrating agent does not average opinions. It:

1. **Separates measurement disputes from interpretation disputes.** A disagreement about *what the
   artifact says* is settled by opening the artifact. Only interpretation disputes need judgement.
2. **Re-derives anything load-bearing that only one agent reports.** A lone finding is a lead, not a
   fact. This is the step that catches a confidently wrong agent — and agents are confidently wrong
   often enough that the ecosystem has a standing note about it (`E2E finding mechanisms are
   unreliable`: symptoms usually hold, mechanisms and fix-directions frequently do not).
3. **Records dissent that was not resolved**, rather than dropping it. "Two agents said X, one said Y,
   Y was not re-derivable" is a more useful record than a clean X.
4. **States the residual uncertainty explicitly** in whatever document the result lands in, including
   the sample size and the instrument used.

---

## 6. Failure modes of this procedure itself

Recorded so that the process is not trusted more than it earns.

- **False consensus.** N agents given the same starting document agree because they read the same
  sentence. Mitigation: §2 Lane A entry-point independence. This is the dominant failure mode.
- **Outsourced assertion.** Accepting a reviewer's correction without re-deriving it. Mitigation: §5.2.
- **Confident wrongness.** An agent reports a mechanism that does not exist. Mitigation: §5.2, plus
  preferring findings that name a file, line, or command over findings that narrate.
- **Review theatre.** Running the pool and then writing the conclusion you already had. Mitigation: a
  round that changes nothing must be recorded as such — and if no round ever changes anything, the
  prompts are asking for confirmation, not refutation.
- **Cost.** This is expensive and is meant to be. Do not apply the top-right cell to routine work; the
  matrix exists to keep rigour proportionate.

---

## 7. Minimum record

Whatever the verified result lands in must state:

- the **instrument** used, and whether it could have produced a different answer;
- the **sample size**;
- how many agents in each lane, and their **entry points**;
- how many **iterations**, and what the last one changed;
- any **unresolved dissent**;
- what the evidence **cannot** support.

The last line is the one most often omitted and most often needed.
