# HANDOFF 2026-08-14 — E-A campaign running under R-3; register otherwise closed

**NOTE:  Start here!!**
**This session is recovering from a previous, interrupted session. The work outlined in this prompt is in an unknown state.**
**The first step of this session should be to determine the current state and status of the Juniper Project and this prompt's work.**

---

Continue the **CLI experimentation program**. Successor to
[`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md`](HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md).
The P4 §7 register (R-1..R-6) is **closed and merged**. One campaign is **in flight**.

## Do not redo — all merged

| PR | Item |
| --- | --- |
| cascor#511 | R-1a honest outcomes — infra failure no longer reported as `no_candidate` |
| cascor#512 | R-1b forkserver lifecycle — RC-4 pool released at end of run |
| ml#1074 | R-6 `execution.stall_seconds` (prior session) |
| ml#1075 | R-2 prereq aggregator + R-4 E-C rebudget + R-5 premise check |
| ml#1077 | R-3 `max_iterations: [32]` so the unit cap binds in E-A |
| ml#1078 | R-2 E-H re-run evidence |

ml main `cfd5ded`; cascor main carries both #509 halves. No open PRs in either repo.

## CAMPAIGN COMPLETE — superseded by the evidence note

The E-A re-run **finished 2026-08-14T04:55Z**: 12/12 `succeeded`, all `oom == 0`, 176.6 min.
Results, the R-3 verdict, the #512-at-scale verdict and the R-5 consequence are written up in
[`notes/JUNIPER_2026-08-14_…-R3-EA-RERUN-EVIDENCE.md`](../../notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R3-EA-RERUN-EVIDENCE.md).
Headlines: units now track the cap (4/8/16/32), the previously bit-identical c006≡c009 and
c007≡c010 pairs are resolved, best val rose **0.670 → 0.735**, and GPU free went **6840 →
6891 MiB net across twelve un-reaped cells**. The section below is retained as the original
in-flight record.

## (original in-flight record)

**E-A re-run under R-3.** Started 2026-08-14T01:58Z, 12 cells, ~4–6 h expected.

- Suite dir: `~/.local/state/juniper-experiments/suites/e-a-cascor-budget-sweep-20260814T015826Z`
- Launched as ONE `run_suite.py` invocation, **deliberately no per-cell reaping** — that
  reaping was the workaround for the leak #512 fixed, so 12 consecutive cells is the
  at-scale test. It used to exhaust the card after 4–5.
- GPU trace sampling every 30 s to
  `scratchpad/ea_gpu_trace.csv`. **A flat trace is the #512 proof; a descending staircase
  means the fix does not hold at scale.** Pre-campaign baseline: **6840 MiB free / 946 used**
  at 01:58:04Z.

### On completion

1. `python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12` — every cell must be
   `oom == 0`; the script screens that.
2. Confirm the R-3 fix landed in the data: **c006 ≠ c009 and c007 ≠ c010** (they were
   bit-identical before, both iteration-bound at 12 units). Expect units to track the cap
   (4→4, 8→8, 16→16, 32→32) with `early_stopped`, not `max_iterations`.
3. Read the GPU trace; state plainly whether #512 held across 12 cells.
4. Evidence note + PR, modelled on
   `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R2-EH-RERUN-EVIDENCE.md`.
5. This also unblocks **R-5** — the service-vs-CLI comparison is meaningless until the unit
   budget is equalised, which this campaign does.

If the run died mid-way: `run_suite.py --resume <SUITE_ID>` skips cells already terminal in
`registry.jsonl`. Check for stale lockdirs under `/run/user/1000/juniper-experiments` and
leftover listeners in 8110–8139 / 8230–8259 before resuming.

## Interpreting the results (earned the hard way)

- The cap binds via `early_stop = early_stopping and (... or max_units_reached ...)` — it
  holds **only** because baseline sets `early_stopping: true`. A cap-bound cell reports
  `early_stopped`, the *same* reason as patience-exhausted and accuracy-target cells.
  **Disambiguate with the units column**: `units == max_hidden_units` means the cap bound.
- A `below_threshold` / 0-unit result is now *provably algorithmic*. Pre-#511 an exhausted
  GPU produced a visually identical `succeeded` record; it now raises and ends **Failed**.
- `cell_id` hashes the override set, so R-3 changed every id. Aggregation is fine (keys on
  `cell_id[:4]`) but old `--only <full-id>` refs will not resolve.

## Environment facts that bitenothingscor1/bin/python`) —
  matplotlib for plots. `JUNIPER_EXP_HEALTH_TIMEOUT=180`.
- A **live isolated E2E stack** is up: cascor `:8202`, data `:8101`, canopy `:8051`, all
  healthy and idle. It currently holds **zero** GPU (it released its forkserver children).
  **Do not touch it.** `reap_pytest_orphans.bash` correctly KEEPs its live-parent children —
  always `--dry-run` the reaper and identify the live parent before reaping.
- Two cascor processes share the checkout, which H-7 / Q-6 discourages; tolerable because
  only the checkout file log is shared (run dirs, snapshots, ports, sampled metrics are
  per-run).
- This session type is **worktree-isolated**: inline shell loops, redirects and compound
  commands are refused. Put loops in a script under the scratchpad and invoke it plainly.
  `git -C <other-repo>` works; `git -C <juniper-ml>` does not.
- Unsigned commits (touch-up bot, `--no-gpg-sign` merge resolutions) make a PR show
  `mergeStateStatus=BLOCKED` under `required_signatures` → merge with
  `gh pr merge N --squash --admin`. Always gate on `behind_by == 0` + green first.
- `JuniperCascor1` has a stale installed `juniper-cascor` 0.6.0 vs pyproject 0.8.0, so
  `test_version_matches_pyproject` fails locally on pristine main. Pre-existing, CI-invisible.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main    # must be empty before committing
tail -5 <the run_suite background output log>               # per-cell progress
python3 util/ad-hoc/2026-08-10_ea_aggregate_clean.py --expect 12
tail -5 /tmp/claude-1000/.../scratchpad/ea_gpu_trace.csv    # GPU trace
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
```

## Git state

- `juniper-ml`: session worktree `.claude/worktrees/stateful-wondering-moth` on branch
  `worktree-stateful-wondering-moth` at `cfd5ded` (= origin/main), tree clean apart from this
  handoff. **Re-derive the SHA — concurrent sessions push to main.**
- `juniper-cascor`: primary checkout at main with #511 + #512; both R-1 worktrees removed and
  pruned.
- No experiment listeners, no stale lockdirs at launch time.
