# HANDOFF 2026-08-14 — F-P1-3 root-caused and fixed; the direct CLI runs

Continue the **CLI experimentation program**. Successor to
[`HANDOFF_2026-08-14_e-i-cap-ceiling-and-f-p1-3-successor.md`](HANDOFF_2026-08-14_e-i-cap-ceiling-and-f-p1-3-successor.md),
which named F-P1-3 as the successor to the closed spiral arc. **F-P1-3 is now closed.** Nothing of
this arc is unmerged.

## Do not redo — all merged

| PR         | Merge                | Item                                                                                                                                |
|------------|----------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| cascor#517 | `ed3da59d` (+182/-8) | Fix — `--no-plots` through every entrypoint + `_backend_is_interactive()` guard + `test_fp13_direct_cli_termination.py` (15 passed) |
| ml#1102    | `736181e7` (+396)    | Root-cause evidence note + the two ad-hoc arms                                                                                      |

Both content-verified after merge; both rule-suites `pass`, not `bypass`; ml main-verify and
cascor Golden/Conformance/CodeQL/Sequence-Safety green on the merge SHAs.

## What was settled

**F-P1-3 is a blocking `plt.show()` AFTER training, not a budget or performance problem.**
`solve_n_spiral_problem` ended with `plt.show()` then `self.plotter.join()`: the first parks the
process in the GUI event loop, the second waits on a **non-daemon** plot child parked in its own
`plt.show()`. Pre-fix positions `spiral_problem.py:1325-1327`; post-fix the guarded pair is at
`:1363-1365` and the helper at `:122`.

| arm | code       | backend                          | flags        | outcome                                              |
|-----|------------|----------------------------------|--------------|------------------------------------------------------|
| A   | pre-fix    | `Agg` forced                     | —            | exit 0, 39 s                                         |
| B   | pre-fix    | `tkagg` inherited (`DISPLAY=:0`) | —            | **hung past a 240 s bound**                          |
| C   | cascor#517 | `tkagg` inherited                | `--no-plots` | exit 0 (38-40 s idle; **95 s** under GPU contention) |

Arm A was the first completed direct-CLI run on record. **Finding F-P1-3b ("structural CLI-path
compute overhead") is WITHDRAWN**: nothing in that five-attempt campaign observed the CLI *finish*,
so it measured no compute gap. All five blocked in the same place and no budget knob could have
moved any of them. **A timeout is not a measurement.** (Do not quote a ratio for F-P1-3b — it never
states one; 590 s was a *bound*, not a completion.)

Why it survived two "plumbing verified" waves: it depends on the launching environment, not the
config — a genuinely headless host resolves to `Agg`, where `plt.show()` is a no-op. And the W-11
key maps carry **no plot knob**, so `outputs.plots: []` is never read by the direct CLI. The
`plot_*` helpers only `show()`, never `savefig`, so the CLI has never written a plot file and
disabling them costs nothing.

## Evidence status — read before quoting any number

**The arm A/B parent-log evidence is GONE and the per-arm figures are not re-derivable from the
2026-08-14 run dirs.** Two independent causes, both now fixed:

- The runners captured stdout only, and the parent's logger writes to
  `<checkout>/logs/juniper_cascor.log`. The four `20260814T200636Z-dcf8` arm logs contain **zero**
  occurrences of `Training completed` / `Started plotting process PID` / `Completed solving`.
- Those runs used the *shared* cascor checkout, whose log the live `:8202` service rotates every
  few minutes. The 15:06-15:14 window has rotated away entirely.
- Arm B's own verdict line was additionally **overwritten** — a `>` redirect hands forked children
  a shared non-append offset, so an orphan flushing after the kill wrote over it. Both runners now
  use `>>` and slice the parent log into `OUT_DIR/parent_juniper_cascor.log`.

**Preserved replacement**: arm C re-run 2026-08-14 17:50 from a dedicated worktree —
`~/.local/state/juniper-experiments/20260814T224846Z-0565/artifacts/results/fp13-armC-preserved/`
has `Completed solving` ×1, `Training completed` ×1, `Started plotting` ×**0** (proving
`--no-plots` end to end), 2-unit cap, train **0.95625**. Arms A and B were directly observed but
are transcript-only; treat 0.960/0.970 as arm A's figures, not "all three".

## Open work

1. **Direct-CLI vs service head-to-head** — unblocked for the first time, but **do not assemble it
   from this arc's numbers**: arm C is post-cascor#514, and R-5 §5.1 established spiral figures are
   not comparable across #514 (candidates now get the configured patience 100, not the module
   constant `_PROJECT_MODEL_CANDIDATE_PATIENCE = 50`). Needs both arms on one side of #514.
2. **Close the P1.2 full-completion row** — the P1 note's §5 addendum leaves it open *against
   F-P1-3b* (not "pending W-11", which W-11 already satisfied), and this arc withdraws F-P1-3b.
   Close it on "a completed direct-CLI run now exists" — **do not import arm A/C numbers into a
   comparison against P1.1's pre-#514 24 s service run**; that is the item-1 trap.
3. **L-1..L-4** (§5 of the merged note, filed not fixed). **L-1 and L-3 are the dangerous pair** —
   two plausible-looking budget knobs that do nothing: `fit(max_epochs=…)` gets the module constant
   and is never forwarded to `grow_network` (`cascade_correlation.py:1910` logs it, `:1912` omits
   it), and `epochs_max` is assigned at `:714` from a `1e11` sentinel and never read by the engine.
   Recommend fixing L-1/L-2 together and deleting L-3. Post-fix, L-1's site is
   `spiral_problem.py:1338`.
4. **Unchanged by this arc**: F-P1-2 (native Grafana v13 squats `:3000`), Q-6/Q-7 + W-12, Q-8,
   Q-10, PF threshold ratification, F-P1-4 snapshot debris.

## Environment facts that bite

- **The live isolated E2E stack is ACTIVELY TRAINING, not idle** — cascor `:8202` was at 7/10
  hidden units, phase CANDIDATE, since 17:11 local. It holds GPU **and** it is what rotates the
  shared `juniper-cascor/logs/juniper_cascor.log`. **Do not touch it**, budget for the contention
  (arm C: 39 s idle → 95 s alongside it), and **run experiments from a dedicated worktree** so your
  log is your own. Always `--dry-run` `reap_pytest_orphans.bash` and identify the live parent first.
- **The parent's log is not on stdout** — stdout carries only candidate workers. A run tailed on
  stdout looks like it died mid-candidate-training when it actually finished and hung later.
- **A fresh worktree has no `logs/`**; the path derives from the checkout root
  (`constants.py:416`), so logger init raises `FileNotFoundError` before anything runs. `mkdir logs`.
- **`timeout --kill-after` returned 125**, not 124/137 — key a hang verdict on *elapsed >= bound*,
  never on `rc`. Both runners now do.
- **Force-push may not fire `synchronize`** — observed on ml PRs 2026-08-14 (see the CI-trigger-traps
  memory), not independently reproduced here. If a head SHA has no runs, use
  `gh api -X PUT /repos/O/R/pulls/N/update-branch`, which is confirmed to work.
- `JuniperCascor1` has installed `juniper-cascor` **0.6.0** vs pyproject **0.9.0** (bumped by
  cascor#518), so `test_version_matches_pyproject` fails locally on pristine `main`. Pre-existing,
  CI-invisible.
- This session type is **worktree-isolated**: inline loops, redirects and compound commands are
  refused. `git -C <other-repo>` works; `git -C <juniper-ml>` does not.

## Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main    # empty before committing
gh pr list --state open                                     # dup-guard — goes stale in minutes

# reproduce F-P1-3 (run from a DEDICATED cascor worktree, or your log will rotate away)
util/ad-hoc/2026-08-14_r5_stack_up.bash                     # prints RUN_ID / DATA_URL
util/ad-hoc/2026-08-14_fp13_verify_fix.bash <DEDICATED_SRC> \
    util/ad-hoc/2026-08-14_r5_arm_c_direct_cli_smoke.yaml \
    <OUT_DIR> <DATA_URL> 240 -- --no-plots                  # expect exit 0
grep -c 'Completed solving SpiralProblem instance' <OUT_DIR>/parent_juniper_cascor.log   # expect 1
util/experiment_stack.bash --down <RUN_ID>
```

Do **not** grep the shared `juniper-cascor/logs/juniper_cascor.log` for that marker — the live
service rotates it, so a `0` means "rotated", not "never completed", which inverts the finding.

## Git state

- `juniper-ml`: session worktree `.claude/worktrees/modular-shimmying-pizza`, branch
  `worktree-modular-shimmying-pizza`. **Re-derive the SHA — concurrent sessions push constantly.**
- `juniper-cascor`: primary checkout on `main` at the #517 merge. Fix worktree, local branch **and
  remote branch** all deleted (cascor does *not* auto-delete merged remote branches; ml does).
  Zero open cascor issues.
- Open elsewhere at writing, not this arc: ml#1106, cascor#519, cascor#520 (ml#1105 has merged;
  ml#1099 is a closed *issue*). Snapshot — re-run the dup-guard.

## Standing approvals carried forward

The owner granted, for this arc and explicitly for its successor: **merge approval for PRs created
during the arc** once green (verify `behind_by == 0` and green *at tip*, then confirm the merge
commit's diff — squash has dropped later commits before); **custom-agent validation of the
handoff**; and archiving, PR'ing and merging the handoff itself under the same approval.
