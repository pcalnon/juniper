# HANDOFF 2026-08-29 — canopy E2E: F-039 is one store id holding TWO values at once

Continue the juniper-canopy E2E validation arc. **Headline: F-CANOPY-037's fix is merged and verified at
the mechanism level and the topology rows are still BLOCKED anyway. F-CANOPY-039's cause is now evidenced
from both sides — a server-side probe sees the topology store's client copy holding the correct 7,059 B
for 11 consecutive ticks while, over the same window, the rebuild renders empty through a fast path that
can only fire on an EMPTY store. Ledger 43 / 25 fixed / 1 accepted / 17 open (2 P0/P1 · 2 P1 · 13 P2).
Matrix 298/298 verdicted, 0 unfilled, 42 BLOCKED (all owned below).** Predecessor:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-26_canopy-e2e-phase2-p1-fix-wave.md`
— read its "Key context" once; several procedures below survive only there and are carried forward here.

## Documents (the successor needs all five)

| role | path |
|---|---|
| **the ledger** (findings, authority for dispositions) | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` |
| **the matrix** (rows; the ledger for verdicts) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` |
| the plan (§6.4 Phase 3, §6.5 Phase 4 closeout, §13 acceptance) | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` |
| the WS-migration plan (JR-CAN-PERF-004; owed an update — item 9) | `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md` |
| callback-starvation design (12-slot pool, Stage 1–3) | `notes/JUNIPER_2026-08-23_JUNIPER-CANOPY_CALLBACK-STARVATION-REMEDIATION-DESIGN.md` |

## Verify your starting state

```bash
cd <worktree of juniper-ml>          # fetch first; heads move hourly
python3 util/ad-hoc/e2e_finding_triage.py    # 43 / 25 fixed / 1 accepted / 17 open (2 P0/P1)
python3 util/ad-hoc/e2e_unfilled_rows.py     # 298 verdicted / 0 UNFILLED
bash util/isolated_stack.bash --status       # FOUR legs, printed data:8101, cascor:8202,
                                             # recurrence:8211, canopy:8051. The THIRD (8211) is
                                             # the DEPLOY container, not this stack — never touch it.
```

Heads at handoff: ml `origin/main` `065045cf`; arc branch `docs/canopy-f039-probes` — **re-derive its
head, do not trust a SHA written here**: this document lives on that branch and was amended into its own
commit more than once;
juniper-canopy `27af847`; juniper-cascor `b4c1087` (= cascor#596, another session's deps bump — this arc
has not touched cascor since #594). **Re-derive every line anchor** — several in the ledger have drifted.

**Work from the ml#1444 branch, not a fresh `main` worktree.** Nine `e2e_f03[79]_*` tools exist. The two
`e2e_f037_*` are already on `main`; the seven `e2e_f039_*` — including
`e2e_f039_topoprobe_instrument.py`, which items 2 and 3 both need — plus the F-039 evidence are on
`docs/canopy-f039-probes` only, until ml#1444 merges. **None of these scripts has an execute bit; invoke
them as `python3 util/ad-hoc/<name>.py`.**

## The one thing to read first

**One store id is holding two different values at the same instant.**

A server-side probe inside the store's WRITER — the only instrument in this arc that was neither
unreliable nor ambiguous — logs what Dash actually delivers as `State`. Over one continuous 71 s window,
no restart:

```
4 samples   19:43:17 -> 19:43:33   eq=False  cur_len=75     new_len=7059
11 samples  19:43:39 -> 19:44:28   eq=True   cur_len=7059   new_len=7059
```

The client's copy of `network-visualizer-topology-store` is empty for ~22 s, then **CONVERGES** and holds
the correct 7,059 bytes for 11 consecutive ticks. **Over that same window the rebuild renders empty** —
and it can only do that through its own fast path (`network_visualizer.py:474`, `if not topology_data or
topology_data.get("input_units", 0) == 0`), which requires an EMPTY store. The writer's view and the
reader's view of one store id disagree, simultaneously. **That is the duplicate-instance signature,
evidenced from both sides** rather than inferred from absence, and it makes the runtime duplicate-**store**
probe (item 3) the leading hypothesis rather than one option among six.

> **Do not repeat the mistake that produced the earlier version of this section.** It read the HEAD of the
> probe log, saw `cur_len=75`, and wrote "permanently the 75-byte empty default … never advances, not
> once" into the ledger, the matrix, this handoff and canopy#537's test docstring. The same file's last 11
> lines said otherwise. All four are corrected; `report` now prints the distinct `cur_len` values so that
> generalisation cannot recur silently. (#537 is still OPEN, so that fourth correction has not reached any
> default branch yet.)

Evidence: `reports/e2e/20260828T132533Z/f039_evidence/topoprobe_store_comparison.log` (35 lines;
force-added because `.gitignore:52` is `*.log`). Re-runnable, and targetable at either store, via
`python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py {apply,report,revert} --target {topology,metrics}`.

### The metrics store is a SEPARATE question, and its deduction is weaker than it looks

F-CANOPY-038's census — 32 writes, 31 byte-identical, **zero** `no_update` — was described in an earlier
draft as something that "can only happen if the client's `metrics-panel-metrics-store` never advances".
**That is false in source.** Zero `no_update` is consistent with at least four things, and the census
separates none of them:

1. the client's copy genuinely never advancing;
2. a **deterministic** round-trip asymmetry — the ledger's hypothesis (i). A constant result is what a
   deterministic transform *predicts* (NaN→null on `_normalize_metric`'s nullable `val_loss` / `f1` /
   `precision` / `recall` / `roc_auc`), so "it would have to corrupt all 32 identically" is not the
   parsimony argument it reads as;
3. **mis-attribution to a second writer** — the ledger's still-open hypothesis (iii). The store has TWO
   writers: the guarded poll `update_metrics_store` (`dashboard_manager.py:3877-3899`) and
   `append_ws_metrics_store` (`:3910-3919`, `allow_duplicate=True`), whose handler
   `_append_ws_metrics_store_handler` (`:6664-6685`) ends `return merged[-window_size:] …` with **no
   identity guard at all**. Every write it contributes is `no_update`-free by construction and says
   nothing about the client's copy;
4. the guarded handler's own empty-copy branches (`:6740`, `:6795`) — `return dash.no_update if
   current_metrics else []` **writes `[]` rather than returning `no_update` whenever the client copy is
   falsy** — so "zero `no_update`" is partly predicted by the hypothesis's own premise and cannot also be
   its evidence.

F-CANOPY-035's corroboration is weak for a separate reason: its "globally empty (`len 0`) on both tabs"
came from `e2e_p1wave_redrive.py --step storeprobe`, the **client-side store read this arc has ruled
inadmissible** (see Traps), and the entry attributed it to F-004 congestion / instrument artefact — it was
not filed "for want of an explanation". Item 2's server-side probe is the only admissible test.

**Net: F-035 / F-038 / F-039 may be one defect or three. Work them as one investigation only until item 2
separates them.**

## Remaining work, in priority order

1. **ml#1444 — get Paul's explicit approval, then merge it first.** It is the only durable record of this
   session's root cause and every `e2e_f039_*` tool lives on its branch. **Current state: OPEN, `BEHIND`,
   checks re-running on the head pushed at handoff** — not "green", as an earlier draft said. See
   "Merging" for the required update-branch-then-wait sequence. **This handoff grants no merge approval.**
2. **Separate-or-unify the two stores. Three commands, no source edit needed.** `--target metrics` works
   as-is because `_update_metrics_store_handler` (`dashboard_manager.py:6687`) already has
   `current_metrics` as a parameter. (`--target topology` needs a preparatory `State` and the tool refuses
   it with instructions — expected, not a bug: `_update_topology_store_handler` at `:6797` takes only
   `(n, active_tab)`.)
   ```
   python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py apply  --checkout <canopy> --target metrics
   #   restart ONLY the canopy leg (the fixture lives in the CASCOR process — see "Stack"),
   #   open Training Metrics ~90 s, then:
   python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py report --log <log>      --target metrics
   python3 util/ad-hoc/e2e_f039_topoprobe_instrument.py revert --checkout <canopy>
   ```
   **The revert is not optional** — `apply` edits the PRIMARY canopy checkout that the live leg, peer
   `p5 memory` and the F-6 stale-checkout guard all depend on, and `open_signed_pr.py` sends whole files,
   so an un-reverted probe ships into the next canopy PR. Tell the peer before you apply.

   **Read `cur_type`, `cur_len`, `canon_eq` and the per-key `differs` lines together — not `cur_len`
   alone.** The store ships `data=[]`, so its empty default is `cur_len=2`, while a `State` Dash never
   resolves gives `cur_len=0`; those are different defects with different fixes and both look "small and
   constant". And **large + CONSTANT with `canon_eq=False` is hypothesis (i)**, the round-trip asymmetry —
   the case an earlier draft's decision rule had no bucket for at all. Whatever you find, **discriminate
   by writer** (§ above, alternative 3) before treating a unification as more than a hypothesis.
3. **The duplicate-STORE probe — the leading hypothesis, and the only open variant.** Write
   `util/ad-hoc/e2e_f039_duplicate_store_probe.py`. Observable: the number of runtime instances of
   `network-visualizer-topology-store` after the A1-iii-b1 tab rebuild; `>1` confirms.
   **Do not re-run the duplicate-ELEMENT check** — it is answered: `n_elements_with_graph_id = 1`,
   attached (F-039's ruled-out table, 2026-08-28, `e2e_f039_dom_apply_probe.py`), and the static check was
   464 ids / 464 distinct. The ledger's "Named next probes (1)" is stale text sitting above the
   measurement that superseded it; an earlier draft of this handoff restored it as if it were open.
   The **store** variant survives precisely because a `dcc.Store` renders **no DOM**, so it is invisible to
   both the element count and `e2e_f027_dup_ids.py`. F-CANOPY-027's investigation named the trap: *"if a
   store is declared twice, Dash writes one instance and the consumers read the other."* Test at
   **runtime**, via `paths.strs`.
   Gates **16 BLOCKED matrix rows** — M-TOPOLOGY-01..06 and -09..18 (**-07 is PASS, -08 is FAIL**, so the
   matrix note's "01..18" is imprecise). The ledger also folds W4-01..17 and W1-12..14 into a "36"; those
   ids appear **only inside blocker notes** and are enumerated in no document, so treat 16 as the
   verifiable figure and re-derive the walkthrough steps from the plan before quoting 36.
   Items 2 and 3 are independent: either order, or both at once.
4. **canopy#537 — prepare a recommendation for Paul; the decision is his.** The rebuild's tick
   short-circuit named `fast-update-interval`, the trigger F-CANOPY-027 replaced with `tabpoll-topology`;
   dead code since. Real dead-guard fix; **does NOT fix F-039** (census 0 of 2 on a leg built from it).

   **Its CI history is genuinely ambiguous and an earlier draft got it wrong in both directions.**
   `UI Sub-suite (Playwright)` failed on **both attempts** at head `5598974`; I called that a flake, the
   re-run refuted me, and I wrote "do not call it a flake". Then the same suite **passed** at head
   `f212f72` — a **docstring-only** change to the test file, behaviourally identical. Two failures then a
   pass on an equivalent tree is evidence *for* intermittency after all. At handoff the current head
   `cf68bcc3` is OPEN / `BLOCKED` (behind) with 12 SUCCESS and no failures, checks still running.
   **Read the current run before deciding anything.**

   Two traps if it goes red again:
   - *"`network_visualizer.py` does not touch the metrics store"* is **not** exoneration. F-CANOPY-027's
     root cause is dash-renderer's **shared 12-slot pool**: callbacks in different files starve each
     other, and #537 changes that pool's occupancy. The failing test's docstring opens *"The
     starvation-protection pin."*
   - *"passes locally under CI's exact invocation"* — it was not exact. CI runs
     `JUNIPER_CANOPY_DEMO_MODE=1 … -m "ui and not slow" src/tests/ui --maxfail=3` over the **whole
     directory, 34 tests co-resident**; one 5-test file is not that, and the co-resident load is the
     entire hypothesis.

   Correcting an OPEN PR needs `python3 util/ad-hoc/2026-08-26_commit_files_to_pr_branch.py --repo …
   --branch … --message … --add LOCAL:REPOPATH` (`open_signed_pr.py`'s dup-guard refuses an existing
   branch; a plain push is refused under `required_signatures`).
5. **The P2 wave's owed live re-drives** (the wave merged; the rows were never re-scored).
   **Run-free rows, do these first:** C2.9-05, M-PARAMETERS-04/-05/-06, M-METRICS-03, M-WORKERS-02,
   C2.1-01/02, the Network Editor patch rows.
   **For M-PARAMETERS-04/-05/-06, re-drive the SYMPTOM, not the rows** — they already PASS on their stated
   expectations, and F-028's fix (canopy#533) was authored against a re-diagnosed writer whose *"precise
   repro was not reproduced from source"*. Pin a key, reload, pin a second, assert the first survives.
   **Run-requiring rows, batch them LAST and together on ONE fresh run:** F-036 (needs the Candidate
   Metrics tab open during a run) and F-026 (needs a MID-RUN sample — `phase_started_at` is cleared on
   completion, so a post-run probe reads `None` and proves nothing).
   **⚠ A new run ends the `2/10/2/89` fixture that items 2 and 3 are both specified against. Finish 2 and
   3 first.**
6. **The two open P1s, currently unowned**: **F-CANOPY-035** (may be subsumed — see item 2) and
   **F-CASCOR-001**, whose upstream tracker `juniper-cascor#590` is still OPEN.
7. **F-CANOPY-033** — deferred; reproduces at ~15/s but has no source-level root cause.
   **F-CASCOR-002** — still needs filing upstream (no cascor issue exists for it).
   **F-CANOPY-037 shipped a recorded cosmetic regression**: new-unit detection is a *last-pair* check
   (`metrics_data[-2]` vs `[-1]`) and, after the Input→State demotion, no longer fresh by construction.
   **M-TOPOLOGY-16 (cascade-add glow) is therefore flaky BY DESIGN** — it sits inside item 3's 16 rows;
   score it accordingly rather than filing a new defect. Named fix: adopt
   `metrics_panel._hidden_unit_addition_markers`' whole-window scan (`metrics_panel.py:1999-2003`) with
   dedupe so a dismissed pulse cannot re-arm.
8. **Owner decision 4 (live 3-D, "both arms")** — a demo arm on `/api/dataset/generate` (demo-gated **by
   design**) and a live arm on `/api/stage_dataset`. The sequence control set **M-DATASET-17..26 is 10
   already-BLOCKED rows** gated on this (`dataset-plotter-seq-controls` ships `display:none`, revealed
   only for a sequence dataset). **They are gated on the owner's scoping decision as well as on the
   technical precondition — surface it, do not drive around it.** Once decided, loading one sequence
   dataset satisfies the precondition for all ten.
9. **JR-CAN-PERF-004 plan update.** Its §7 item 3 and its Phase 2 blocker (`:189`) still pose the F-036
   server-vs-clientside choice as open; the owner chose server-side and canopy#536 shipped it. Record that
   Phase 2 is no longer gated on it. **Its "must not run concurrently with F-036" constraint (`:189`)
   still binds anything touching the candidate-metrics feeder.**
10. **13 BLOCKED rows are owned by no other item**: M-METRICS-11..16 and -18 and -27 (8 — the replay
    transport), M-CANDIDATES-10/-11, M-EVOLUTION-07, M-BOUNDARIES-07, M-DATASET-03. Most need the same
    V2-snapshot-with-history precondition as W5-21/-23 and should ride with them.
    **Ownership adds up:** 16 (item 3) + 10 (item 8) + 13 (here) + 3 (C2.10-03, M-SNAPSHOTS-20/-21;
    item 11) = **42**, the matrix's full BLOCKED set.
11. Also owed: F-CANOPY-010's cancel-close W5-step-6 re-confirm; C2.10-03; M-SNAPSHOTS-20/-21; W5-21/-23
    on a V2 snapshot with non-empty history; plan **§6.5 Phase 4 closeout** (§11 drift table, the D-3
    replay-tick-base-1000 ms source fix) and **§13 acceptance**.
    Plan **§6.4 Phase 3** (the automated `ui_live` suite) is **BLOCKED, not merely owed**: its entry
    condition is "Phase 2 P0/P1 closed", and both F-037's rows and F-039 are open. Not startable until
    items 2 and 3 land.
    *(Dropped from an earlier draft as already closed on 2026-08-26, run `20260826T215010Z`: the `f031`
    driver step, and M-DATASET-14 — which is PASS at 17.5 s, at/just past the ≤16 s F-004 bound.)*

## Merging (constraint carried forward — do not merge without it)

Rulesets canopy `14249530` / ml `13805432` are `strict_required_status_checks_policy: true` with Admin
bypass `always`, so a `BEHIND` PR merges as `result=bypass` with checks never re-run on the new head. Six
canopy + one ml merge already recorded that. **Sequence: `update-branch` → wait for green on the NEW head
→ merge**, via `python3 util/safe_merge.py --pr N --repo R --owner pcalnon --execute` (exit 0 ≠ merged;
look for the `MERGED` line). `wait_for_checks.py` can return immediately after an update-branch if it
still sees the old head's completed rollup — re-check the head SHA. **Merges need the owner's explicit
per-PR approval and approval does not carry across sessions; this handoff grants none.** The same applies
to *closing* a PR and to removing any worktree.

## Traps this session paid for

- **Read the WHOLE instrument output before you generalise from it.** The most expensive error of the arc:
  the probe log's first four lines say `cur_len=75`, and "permanently empty, never advances, not once"
  went from there into four documents — while the same file's last eleven lines said `cur_len=7059`.
  Nothing about the instrument was wrong; the reading stopped early, and every downstream document quoted
  the *conclusion* instead of re-deriving it. The tell is **the quantifier** — never / always / every /
  not once, asserted from a sample nobody read to the end. What caught it was mechanical, not clever:
  make the instrument re-runnable, then replay it over its own archive.
- **A discriminating test can return a strong CONFIRMING signal for a hypothesis that is wrong.**
  Disabling `tabpoll-topology` at runtime made the graph paint immediately — traces 0 → 181, sig 2 →
  31152, *byte-identical* to the signature F-037 recorded for the two sessions that did paint. That looked
  decisive. Two fixes derived from it each failed a live census (0 of 2, 0 of 1) and one was reverted.
  Item 2 is another confirm-or-refute probe with a stated confirm criterion; check `cur_type` and
  `canon_eq`, not just the headline number.
- **A zero is not a result until you know the instrument could have produced a non-zero.** Five instances:
  a `logger.debug` grep with DEBUG **off**; the driver's `_store()` reading `None` while that store's
  writer provably fired 12x/60 s (**this is why F-035's `len 0` is not admissible evidence**); an itempath
  walk that failed on all 40 samples and returned a clean-looking "0"; a hazard scanner that found 0
  hazards in a file containing 4; and the `*.log` gitignore rule that made a "harvested" evidence file
  untracked while `git status` read clean.
- **`dcc.Graph(id=X)` renders a WRAPPER.** The plotly instance is on an inner `.js-plotly-plot`; reading
  `_fullLayout` off the id-bearing element reports "plotly never initialised" for a healthy graph.
  Resolve it as `e2e_f027_redrive.fig_info` does.
- **Substring-matching an id in redux actions is not "an action about that component"** — `SET_PATHS`
  fires ~45x/min with a 534 KB payload naming every id in the app.
- **When a CLIENT-side value is in question, instrument the SERVER's view of it.**
- **Three guards this session named an identifier that had moved** (F-039's short-circuit, F-038's Stage 2
  lever, F-018's dropped keys). Treat a rename or relocation as a hazard in its own right.
- **`git status --porcelain` is blind to ignored files** — and `git worktree remove` deletes them.

## Stack and cleanup owed

The isolated trio **is UP** (verified at handoff, 17 h 22 m): data `:8101` pid 1379438, cascor `:8202` pid
1379625, canopy `:8051` pid 1379952 — the last two running **out of the PRIMARY checkouts**, so ordinary
work in juniper-canopy or juniper-cascor can disturb the fixture, and the completed 10-unit network
(`2/10/2/89`) lives in pid 1379625's memory: **restart cascor and items 2/3/5 lose their fixture.**
Restarting the canopy leg alone is safe, and is what item 2 needs. The A/B leg on `:8052` is down. Do not
run `util/reap_pytest_orphans.bash` while the trio is up.

`bash util/isolated_stack.bash --down` **is documented** — `usage()` says it stops the optional recurrence
leg, and the `.h5` deletion is `announce`d on every invocation (`:472`) with a 14-line rationale at
`:476-489`. (An earlier draft called both "undisclosed"; they are not.) **The actual hazard is narrower:**
it calls `stop_port "${RECURRENCE_PORT}"` — default **8211** — and, unlike `--up` (`:314-316`), with **no
pre-check**, so on this host it will kill the deploy stack's process. It also `rm -f`s
`${CANOPY_SRC_DIR}/snapshots/snapshot_*.h5` from the **primary** canopy checkout.

At teardown, as one pass:
1. Harvest `/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--ab-premerge-9f6fac9/logs/system.log`
   (5,050 B — the pre-merge A/B leg's log, the evidence that #531–#536 did not cause F-039).
   **`git add -f` it** — `reports/e2e/**/*.log` is gitignored, which already silently defeated one harvest.
2. Sweep, **by full path, never by glob** (a canopy-wide glob also takes three **non-arc July worktrees** —
   `relay-supervisor-liveness-and-state-truth`, `sec-f22-two-flag-bind-attestation`,
   `ungate-metrics-topology-polls`; all three **are** merged into `origin/main`, at 113 / 134 / 113
   commits behind, but they are **not this arc's to remove**):
   `juniper-canopy--fix--{f012-output-weights-2d--20260827-2245--9f6fac97, f026-naive-phase-stamp-compat--20260827-2225--9f6fac97, f036-server-side-pool-history--20260828-0825--6b55399d, f037-topology-rebuild-starvation--20260827-2105--9f6fac97, p2-wave-batch-a--20260827-2135--9f6fac97, p2-wave-batch-b--20260827-2200--9f6fac97}`
   plus `juniper-canopy--ab-premerge-9f6fac9` (detached HEAD, so a PR-keyed gate refuses it).
   **Keep `fix--f039-stale-shortcircuit--20260828-1914--27af8472` while #537 is open.**
   **Remove nothing until Paul has explicitly said the arc is cleaned up AND `gh pr view` reads MERGED for
   each branch.** Run `git status --porcelain --ignored` in EVERY tree first — including this ml session
   worktree — and cross-check the deletion list with an independent sub-agent.
   The peer's gated sweeper is **not in this repo**: it is at
   `<juniper-ml>/.claude/worktrees/mighty-greeting-mochi/util/ad-hoc/2026-08-28_p5_worktree_cleanup.py`
   (another session's worktree). Ask `p5 memory` to run it, or use `util/ad-hoc/worktree_sweep_survey.bash`.
3. **Ping peer `p5 memory`** (`uds:/run/user/1000/cc-socks/3727200.sock`) once both primaries are free —
   it has the canopy/cascor AGENTS.md cuts queued behind them, and has said explicitly that it is not
   hurrying the fixture.

## Peer coordination in flight

`p5 memory` is cutting canopy's AGENTS.md as **two sequential single-destination PRs**: doc-about-doc →
`docs/DOCUMENTATION_OVERVIEW.md`, the rest → a new `docs/AGENTS_REFERENCE.md`, with `docs/REFERENCE.md`
keeping its index role. A **hazards-promotion PR lands first** (canopy AGENTS.md has no `## Hazards`
section); they will send bullet 1 for review before it lands. Figures of record, theirs not mine:
`docs/REFERENCE.md` is 9,672 chars of which **54.1% is inline content, not link tables**; the
doc-about-doc mass is **27,687 chars = the sum of seven discrete non-contiguous sections** (not a span —
measuring it as a range double-counts). cascor = Tier A, nine sections; cascor-worker#164 and deploy#197
are already MERGED. **Correction already sent:** my "already cost a P0/P1" rationale for promoting the
Dash `no_update`-chaining trap (`dashboard_manager.py:3869`, labelled CRITICAL, silent, **absent from
AGENTS.md**) was **unsourced** — the ledger records the nearest tested sibling as *"Plausible, and wrong …
Reverted"*, and F-027's real cause was the 12-slot pool. It is promoted on the CRITICAL-label +
silent-failure + absent-from-AGENTS.md basis only.

**That bullet is worth reading before item 2, because it now carries the duplicate-writer predicate**
this session derived (ml#1450, §6a). Its shape: an idling `no_update` producer must not be an `Input`
to an interval-driven callback **that shares its tick** — and the remedy branches, which is what
decides whether a store has asymmetric writers at all:

| the callback needs the signal to… | remedy | second writer? |
|---|---|---|
| **read** it | pass as `State` (`ws-liveness-store` does) | no |
| **drive** an update | `State` cannot serve it — State does not trigger — so a separate `allow_duplicate` callback does (`ws-metrics-buffer` is routed this way, and is **not** in the poll's signature at all) | **yes, necessarily** |

So on the must-drive branch the second writer *is* the fix, not a side effect of it. Ask "read or
drive?" of any idling signal and you know whether its store has the asymmetry before opening a file.
**Grep the store id, not the callback** — an `allow_duplicate=True` Output is invisible to anyone
reading the handler they happened to open.

## Environment

Every `e2e_f0*` driver needs `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python`
(the conda activate hooks that strip the rust_mudgeon libtorch do **not** run on direct binary
invocation). Run the triage scripts from the ml repo root (they use repo-relative defaults). The env this
repo's `CLAUDE.md` names as `JuniperCanopy` does not exist — use **`JuniperCanopy1`** /
**`JuniperCascor1`** (`JuniperData` does exist and is unaffected; the `*-DEPRECATED` variants are not
usable). `gh` auth and a working GPG signing key are required for items 1 and 4.

## Git state at handoff

juniper-ml: on `docs/canopy-f039-probes` → **PR ml#1444 OPEN, `BEHIND`, checks re-running**.
Everything this session produced is committed and pushed there as a **single** commit — deliberately
collapsed, because a later commit corrected an earlier one on the same branch and GitHub's squash-merge
ships only the first commit's diff. juniper-canopy: `fix/f039-stale-shortcircuit` at `cf68bcc3` →
**PR canopy#537 OPEN, `BLOCKED` (behind), 12 SUCCESS / no failures / checks running**. All other arc
branches merged. juniper-cascor: untouched by this arc since #594.

**Two fixes were built on a refuted supersession hypothesis, tested live, and reverted** — #537's
short-circuit (kept, on its own merits) and a no-op-write suppression on the topology store (**discarded;
it exists nowhere and would need rewriting if wanted**). Neither is in the primary checkouts. The lesson
they carry is in Traps, not here.
