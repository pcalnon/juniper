# HANDOFF 2026-09-04 — soak per-probe characterisation

**UNVERIFIED.** Written under context pressure at the owner's instruction; nothing
below was re-checked before writing. Verify every number and state claim before
acting. Commands to do that are in *Verify first*.

## Immediate task

Finish **per-probe characterisation** of the pointer-follow soak. Drive the
ambiguous probes toward n≈8–10 to resolve which stratum each belongs to.

The pooled verdict is **BET-FAILING** (terminal), so
`util/soak_run_probe.py` **refuses to run** — pass `--force`. This is expected and
sanctioned: §8.3 of the design conversation flagged that guard as keyed on a
pooled verdict the owner's purpose demoted, and the per-probe question is
untouched by it.

```bash
python3 util/soak_run_probe.py --probe-id <ID> --timeout 780 --force
```

Then score by hand against the frozen discriminator
(`python3 util/soak_next_probe.py --reveal --probe-id <ID>`), and record with
`python3 util/soak_ledger.py probe-run --probe-id <ID> --outcome
follow|source-recovered|miss --session <id> --scored-by <who> --note '...'`.

## BLOCKER — do this first

**PR ml#1644 is OPEN with failing CI**: `Regression Tests (Python 3.13)` and
`(3.14)` FAILURE, mergeState BEHIND. Cause **not diagnosed**. It carries the
retrieval-channel fix, 3 new tests, 3 observations and §10 of the design doc.
Likely candidates (guesses, unverified): the 3 appended tests in
`tests/test_soak_run_probe.py`, or a black/format issue, or an unrelated main
breakage. Reproduce with `python3 -m unittest tests/test_soak_run_probe.py`.

Do not run more probes onto that branch until it is green and merged, or the
ledger diff will keep growing on a red PR.

## Per-probe state (approximate — re-derive)

| Probe | f/n |
|---|---|
| P21 | 1/4 |
| P15 | 0/4 |
| P19 | 0/4 |
| P14 | 0/3 |
| P23 | 1/3 |

The other 10 probes are follow-dominant and not the priority.

## Key findings this session (all in §§8–10 of the design doc)

- **Pooled 60.5%, CI [0.456, 0.736] — BET-FAILING.** But **retention 95.3%**:
  relocation does not lose facts; pointer-following is not what prevents the loss.
  Agents reach the fact from **source**.
- **Strata are real** (permutation test, p=0.0017) but **per-probe membership is
  not established** — every probe's CI spans 50%. P23 flipped 0/2 → 1/3, which is
  why membership needed testing at all.
- **Nothing predicts stratum membership.** `severity` splits; `area` splits
  (`ports` holds both P19 and P24); "has a nearby test" is refuted by P21/P02.
  This is the deeper blocker for decision support.
- **The retrieval channel was over-reporting follows** — it searched the answer
  text, so reciting the pointer path scored as following it. Fixed to tool inputs
  only. Only P15 was affected; P23/P06 re-audited as genuine.
- **A third channel exists with no category: index-recovery.** P19's session used
  the rung-1 `MEMORY.md` row directly ("The memory note about port checks
  fail-opening is relevant here") with no tool call. 1 of 4 rung-1 probes, and the
  detector only catches explicit mentions — **a floor, not an estimate.** If rung 1
  works by making facts resident, it will never appear as a follow.

## Open owner decisions (do not decide these)

1. Whether **index-recovery** becomes a scored outcome (registry + ledger change).
2. Whether **BET-FAILING** feeds back into relocation policy — "safe, but not for
   the reason assumed".
3. Whether the stopping rule should be re-keyed off the pooled verdict.
4. P06's discriminator **under-specifies** (enumerates acceptable answers; a
   session found a safe third). Registry-author item.

## Documents

**Referenced / to read first**
- `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` — §§8–10 are this session's work
- `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` — protocol of record; §7 scoring, §15.3 prediction, §17/§19/§20 instrument limits
- `notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md` — what may/may not be automated

**Changed this session**
- `reports/soak/pointer_follow_soak.jsonl` — 7 observations
- `util/soak_run_probe.py` — parser type guard; `retrieval_channel` tool-inputs-only; verdict stopping rule; `resolve_claude()`
- `tests/test_soak_run_probe.py` — 3 channel regression tests
- `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` — §§8–10

## Verify first

```bash
git fetch origin && git status --short --branch
gh pr view 1644 --repo pcalnon/juniper-ml --json state,mergeStateStatus
python3 -m unittest tests/test_soak_run_probe.py
python3 util/soak_ledger.py verify-probes
python3 util/soak_ledger.py report
python3 util/soak_next_probe.py --status
```

## Git state

Worktree `.claude/worktrees/nifty-tinkering-wave`, branch
`feat/soak-bet-failing-and-channel-fix`, pushed, PR **ml#1644 OPEN and RED**.
Earlier work this session merged: ml#1616, #1602, #1581, #1576, #1566.

Merge policy: owner approval granted for PRs in this session/arc; still use
`util/wait_for_checks.py --pr N`, arm `--auto` only after green, and drive
`update-branch` when BEHIND.
