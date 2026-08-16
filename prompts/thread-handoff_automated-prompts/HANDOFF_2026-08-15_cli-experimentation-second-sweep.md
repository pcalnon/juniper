# HANDOFF 2026-08-15 — CLI experimentation: a second sweep, and the §12 perf lane nobody owns

Successor to [`HANDOFF_2026-08-14_f-p1-3-root-caused-and-fixed.md`](HANDOFF_2026-08-14_f-p1-3-root-caused-and-fixed.md).

**Nothing here is in flight.** No experiment driver is running, the experiment port ranges are
clear, and `juniper-cascor` has zero open PRs and zero open issues.

**What this is.** A second sweep of the plan and the P0–P4 notes, carrying the items the other
2026-08-15 handoffs do not. It is *not* a claim that the plan is now fully covered — it is one more
pass, and §9 records what it deliberately leaves out. The single largest finding is that **the §12
performance lane has never been run and no document owns it**.

## Read this first — five handoffs were archived 2026-08-15

| document                                                                        | owns                                                                                                                                                                    |
|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `HANDOFF_2026-08-15_api-primer-defect-register-outstanding-work.md` (ml#1121)   | the **defect register** — 91 open defects                                                                                                                               |
| `HANDOFF_2026-08-15_wide-budget-head-to-head-campaign.md` (ml#1122)             | the wide-budget head-to-head **campaign** (64–128 units)                                                                                                                |
| `HANDOFF_2026-08-15_canopy-e2e-phase1-segment-12.md` (ml#1123)                  | the canopy E2E matrix — a different arc entirely                                                                                                                        |
| `HANDOFF_2026-08-15_q6-resolved-and-owner-decision-register.md` (ml#1124)       | **Q-6's closure**, its five stale register sites, `run_suite`'s parallel refusal, and the owner-decision table (F-P1-2, Q-8, Q-10, W-12/Q-7, PF **thresholds**, F-P1-4) |
| `HANDOFF_2026-08-15_ruleset-bypass-and-branch-protection-register.md` (ml#1125) | branch protection — a different arc                                                                                                                                     |
| **this one**                                                                    | §2–§8 below                                                                                                                                                             |

None supersedes another. **ml#1124 is the register of record for this arc** — where its scope and
this document's touch, ml#1124 wins. If your task is named in a row above, go there instead.

---

## 2. The §12 performance lane — the largest unowned block in the plan

ml#1124 §2.3 names the lane and owns nothing in it; ml#1122 does not mention it at all — it carries
no reference to the perf suites, any `PF-` scenario, or plan §12. Nobody has run it.

**It has never been executed.** Six suites ship under `util/experiments/suites/perf/` — `pf1`
(cascor spiral repeats), `pf2` (dataset scaling), `pf3` (pool scaling), `pf5` (recurrence
`d`-scaling), `pf6` (`n_steps` scaling), `pf7` (readout rungs). Zero perf runs exist:
`ls ~/.local/state/juniper-experiments/suites/ | grep -c pf` → **0**, against 36 suite dirs.

Two scenarios have no driver suite **by design**, and both need a decision, not a suite:

- **PF-4** — cascor micro-benchmarks, run through the existing perf suite against
  `src/tests/performance/baselines/baseline_20260526.json`, not the driver.
- **PF-8** — two-run concurrency cost. Needs two simultaneous runs. `run_suite`'s cascor-parallel
  refusal (**ml#1124 §2.2 owns it**, gated on a cascor version floor that cannot be written until
  #523 ships in a release) blocks the *suite* path only — `suites/perf/README.md:18` names the
  alternative: *"Wave 7.5 parallel mode / manual two-terminal per the P3 isolation precedent"*.

**G-17 is the lane's other half** (plan `:202`, sub-items at `:913`): recurrence has no
`performance` pytest marker, and its bench writes offline JSON only, so **recurrence timings
cannot reach Grafana at all**. The plan splits it in two — add the marker, and let the *driver*
publish bench-equivalent timings through the service path (`/v1/train` already records
`_train_last_duration_seconds`) rather than touching the offline harness.

**Do not conflate the lane with its thresholds.** §12.3/§12.4 threshold ratification is Paul's and
is ml#1124's row; *running the scenarios* is engineering and is unowned. The plan is explicit that
§12 is *"a design start, not a final design"* (plan `:897`) and that run-level baselines stay
report-only until variance is characterised on this shared workstation.

---

## 3. Live defects in juniper-ml's experiment tooling

### 3.1 `run_suite` has no `execution:` key for the wall-clock budget — the ml#1069 class

`util/experiments/run_suite.py:330` builds the driver command:

```python
drv_argv = [python_bin, str(driver), "--config", str(cell_yaml), "--run-dir", str(run_dir)]
if stall_seconds is not None:
    drv_argv += ["--stall-seconds", str(stall_seconds)]
```

`--max-wall-seconds` is never passed (`grep max_wall` → no match), and `EXECUTION_KEYS` (`:64`)
has no wall-clock member. `per_run_timeout_seconds` (`:411`) is only the **subprocess** timeout —
it records `timed_out` from the outside, where the driver would write an honest `timed_out`
manifest.

**State the gap narrowly — a suite *can* already set the budget.** `materialise_cell` applies
arbitrary dotted `matrix` / `include` overrides with no allow-list, and the repo's own widest suite
does exactly that: `util/experiments/suites/p4/e-i-cascor-cap-ceiling.yaml:71` sets
`outputs.max_wall_seconds: [14400]`, and its header (`:25-35`) documents the whole mechanism. The
real defect is **ergonomic and silent**: an *un-overridden* cell inherits `base_config`'s value
(`spiral-baseline`'s 3600 s) with no signal, exactly as `stall_seconds` did before ml#1069 added it
to `EXECUTION_KEYS` and forwarded `--stall-seconds` — same file, one field over. The E-I note
records the consequence: two of its three cells would have been truncated by the inherited default.

ml#1122 handles this for its own campaign by requiring an explicit per-run value; that is a
convention, not a gate. Fix shape: add `max_wall_seconds` to `EXECUTION_KEYS`, forward
`--max-wall-seconds` (`run_experiment.py:1748` already defines it, CLI > YAML > 3600), and pin it
in `tests/test_run_suite.py` beside the stall field.

### 3.2 Q-1 was answered "yes" and never implemented

Plan `:524` reserves the file in the §6.4 RUN_DIR layout —
`experiment.resolved.yaml           # PROPOSED: fully-materialised defaults (Q-1)` — and the
Q-table (`:1140`) answers *"Yes — dumped from the live `Settings` object, not hand-reconstructed."*

Nothing writes it. `experiment.resolved` appears in exactly two places repo-wide, **both in the
plan**. No `experiment.resolved.yaml` exists on disk. Live run dirs carry only
`config/experiment.yaml` (7 of 177 have an empty `config/`).
`materialise_cell` does write a resolved per-cell `cells/<id>/experiment.yaml`, which is adjacent
but is neither named nor placed as Q-1 specifies, and exists only for suite runs.

**This is a gap, not an owner call** — the decision was made. Every campaign so far has
reconstructed effective parameters by hand from the manifest, which is the error class the file
was designed to remove.

### 3.3 The orphan reaper classifies **live** experiment stacks as `WOULD REAP`

The sharpest safety item here. From the R-5 note (`:300-312`), during that campaign
`util/reap_pytest_orphans.bash --dry-run` classified as `WOULD REAP`:

- that campaign's **own live** experiment-stack cascor, and
- a **concurrent session's live** experiment cascor, mid-training, its pool holding 7 × 116 MiB of GPU.

Both healthy and wanted. `experiment_stack.bash` launches services under `nohup` inside a subshell,
so they reparent to `systemd --user` — precisely the reaper's orphan predicate. The long-lived
isolated E2E stack is correctly `KEEP` (its supervising parent is alive), so the hazard is specific
to nohup-launched per-run stacks — which is every experiment stack.

ml#1122 carries this as a *warning to the operator* (the bullet at `:325-327`). No document owns
fixing it. A reaper
run without `--dry-run` during any campaign kills it. Fix shape: exclude pids holding a port in the
experiment ranges, or match against the run root's pidfiles.

### 3.4 `start_fresh: true` does not stop an in-flight training session

R-5 note `:232`: the first attempt hit the 120 s stall abort, **the service kept training**, and
the naive re-run failed with `HTTP 409: Training already in progress`. `start_fresh: true` does not
preempt a live session. The workaround was an ad-hoc poller that attaches instead of restarting.
Unowned; it will bite every re-run after a driver-side abort.

### 3.5 Widen the R-6 presence gate to trigger on cap as well as pool

`tests/test_experiment_suite_yamls.py` requires `execution.stall_seconds` when a cascor suite
sweeps `candidate_pool_size >= 16`. ml#1122 (`~:305`) shows that is not sufficient — a wide-**cap**
suite at pool 8 passes the gate and ships, then loses its 128-unit cells to a false `stalled` hours
in. Two further edges it names: the gate reads only `matrix` / `include`, so a pool inherited from
`base_config` is invisible to it; and what is always gated is key *spelling*, not presence.
ml#1122 explicitly disowns the fix — *"a genuinely useful follow-up — it is **not** part of this
deliverable"* — so it is orphaned. The gate lives in `tests/test_experiment_suite_yamls.py`
(`LARGE_POOL_THRESHOLD = 16` against `training.params.candidate_pool_size`), a different file from
§3.1's.

---

## 4. W-items that landed partially

Both were counted implemented by earlier sweeps. Each shipped one half.

### 4.1 W-4 — the install hint the operator is sent to does not exist (and G-16 is its other half)

`util/experiments/run_experiment.py:611` refuses an unavailable generator with
*"missing optional dependency; see GET /v1/generators for the install hint"*. That endpoint carries
no hint: `GeneratorInfo` (`juniper-data/juniper_data/core/models.py:111-121`) has exactly `name`,
`version`, `description`, `available`, `params_schema` (aliased `schema`), and
`routes/generators.py:213-219` constructs it with exactly those five. The actionable `pip install`
text reaches a client only on the `POST /v1/datasets` 501 path, and only indirectly: the real
string lives in the generator's `ImportError` (`generators/mnist/generator.py:76` —
`"Install with: pip install datasets"`) and surfaces through the `{e}` interpolation in that
route's `detail=` at `routes/datasets.py:167`. The preflight never reaches it.

**G-16 is the same wound from the other side** (plan `:201`): `mnist` is unavailable on this host
because HF `datasets` is absent, so a cascor mnist experiment 501s. Fixing W-4's message makes G-16
self-explaining. Fix either half: add the hint to `GeneratorInfo`, or point the message at the 501
path. W-4's docs half is genuinely done.

### 4.2 W-9 — the hand-kept mirror W-9 existed to retire is still the gate

`juniper-data-client/tests/test_generator_parity.py:32` still defines `EXPECTED_SERVER_GENERATORS`
as a hand-maintained `frozenset` of **16** names. The live cross-check meant to make it
self-maintaining, `test_pinned_mirror_matches_live_registry`, guards on `if live is None:` (`:152`)
and calls `pytest.skip` (`:153`) when `juniper_data` is unimportable — and **no juniper-data-client
CI lane installs juniper-data**. The four `pip install -e ".[test]"` sites in
`.github/workflows/ci.yml` are `unit-tests` (`:228`), `integration-tests` (`:321`),
`dependency-docs` (`:431`) and `security` (`:543`); `[test]` is
pytest/pytest-cov/pytest-timeout/responses/juniper-observability. So the cross-check never runs in
CI and the frozenset is exactly as stale-able as before W-9.

Fix shape: install juniper-data in one lane, or make the skip a hard failure there.

---

## 5. cascor code follow-ups from the F-P1-3 arc

### 5.1 L-2 — an open semantic question, not a bug

`fit` (def `cascade_correlation.py:1803`) consumes `max_epochs` at `:1891`
(`train_loss = self.train_output_layer(x_train, y_train, max_epochs)`) but never forwards it to
`grow_network` (`:4466`), whose per-round passes read `self.output_epochs`. Whether an explicit
`max_epochs` **should** re-budget the per-round passes is unsettled.

It was deliberately kept out of cascor#522 — that PR **added the scope note itself**: *"whether an
explicit `max_epochs` should also re-budget the per-round passes is an open semantic question, not
settled here"*. The constraint is that `max_epochs` is in the service's
`TrainingLifecycleManager._FIT_KWARGS` (`src/api/lifecycle/manager.py:2067`, alongside `epochs`,
`max_iterations`, `early_stopping`), so forwarding it **changes service behaviour and is
golden-suite-visible**. Decide the semantics before touching code.

### 5.2 L-4 — wider than the one key it was filed under

L-4 was filed as `training.params.early_stopping` being service-tier-only. The shape is larger:
`_W11_TRAINING_KEY_MAP` (`src/main.py:238-250`) admits **eight** keys — `learning_rate`,
`correlation_threshold`, `max_hidden_units`, `patience`, `candidate_epochs`,
`candidate_pool_size`, `output_epochs`, `max_epochs` — and every other experiment-YAML training key
is logged and dropped at `:429`:

> `W-11: experiment-YAML keys with no direct-CLI counterpart (service-tier only), IGNORED here: …`

`early_stopping` appears nowhere in `src/main.py`, and `fit()` defaults it to `True` (`:1812`), so
the direct CLI always early-stops. The shipped configs already set dropped keys —
`spiral-baseline.yaml` drops `candidate_learning_rate`, `candidate_patience`,
`convergence_threshold`, `early_stopping`, `max_iterations`. **A direct-CLI run is therefore not
configured the way its YAML reads**, and that warning line is the only signal.

**The coupling that matters**: the R-3 cap-reading rule — a cap-bound cell reports `early_stopped`,
disambiguated by `units == max_hidden_units` — holds *only* under `early_stopping: true`. The first
config that sets it false changes how every outcome column is read, silently, on the direct CLI only.

ml#1122 works the same mechanism four times as a campaign design rule (`:56-65`, `:265`, `:270`,
`:279`) and states the cap-reading rule at `:331`. What is new here is `early_stopping`
specifically, the `:429` warning as the sole signal, and that coupling.

---

## 6. Evidence gap — the published E-C surface is stale

**R-4 was disposed; only its re-run half was skipped.** Say it that way — two merged documents
record the register as closed, and the owner decision is explicit in
`HANDOFF_2026-08-13_p4-followups-r6-shipped-r1-designed.md:11` (*"give E-C's spiral rows an
E-A-class budget — do not reduce E-C to a moon-only study"*) and in ml#1075's commit message
(`ff4e2ca`, *"R-4 (owner-decided) … Rebased on spiral-baseline"*). Do not re-litigate that call.

What is stale is the evidence. The suite edit landed **2026-08-13 00:43**; the newest E-C run under
`~/.local/state/juniper-experiments/suites/` is `e-c-cascor-noise-robustness-20260811T095213Z` —
**two days earlier**, and all six E-C runs are 08-09/08-11. So the published E-C noise surface is
still the cap-bound one whose curve is flat *because the unit cap binds* (F-6,
`…P4-SPIRAL-RESURFACE-EVIDENCE.md:117`), not because noise does not matter. No note records the
re-run.

**Note the conflict when you act**: ml#1122 `:6-8` and `…p4-arc-complete.md:13` both state the
R-1..R-6 register is closed. On the register they are right; on the *evidence* they read as more
settled than it is. Re-run E-C under the current suite and publish, or record that the surface is
knowingly stale.

**Related, and also unowned**: cascor#514 changed candidate patience, and R-5 §5.1 established
spiral figures are not comparable across it. ml#1122 handles that inside its own campaign design.
Nobody owns re-baselining the **published** E-A / E-I grids, both of which predate #514.

---

## 7. Traceability threads

- **Q-12 / Wave 7.6 — proposed, not ratified.** The block exists:
  `notes/JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md`, status
  *"PROPOSAL — IDs become official only at the next snapshot refresh"*. Wave 7.6's verb is
  "Propose" (plan `:1115`), so **the wave item is done**; ratification remains. There are zero
  `JR-REC-` IDs in the requirements index or `id_assignments.yaml` — do not read that as the
  proposal being missing. And do not look for a `REC.md` under `notes/requirements/by-area/`: those
  15 files are **area** codes (API…WS) while `REC` is an **owner** code, so one would never exist.
  Plan `:1171` lists the minimum coverage: §5.5 config, G-5 plotting, W-5/W-7, G-4 dashboard, G-17.
- **F-7 — provenance re-pin, dangling.** `…P0-PREFLIGHT-EVIDENCE.md:145`: *"re-pin provenance when
  Wave 3 touches the recurrence repo."* Wave 3 shipped; `plan:64` still records `f23f3ba` / app
  `0.2.0`. Trivial, and stale provenance is exactly what F-7 was filed about.
- **The plan still calls itself a draft.** `plan:1213`: *"Status: **Proposed (draft for owner
  review)**. Ratification requires owner decisions on Q-1 through Q-12"* — after the whole program
  has executed against it. Q-1…Q-5, Q-9 and Q-11 are settled; the trailer should say so.

---

## 8. Already closed — do not re-open

- **G-18** (recurrence service-mode leaves no model artifact) is **mitigated by design**: the
  driver's `outputs.save_model: true` re-runs `juniper-recurrence train --out` as a
  manifest-recorded extra step (plan `:380`).
- **Q-9 / Wave 7.4** is **complete but barely attested** — every alert in
  `juniper-deploy/prometheus/alert_rules.yml` carries `environment!="host-experiment"` (80
  occurrences across all 29 alerts). No `notes/` document records the closure — only the bulk
  Waves 0–7 line in `HANDOFF_2026-08-09_cli-experimentation-program-wrapup.md:7` — and the P3
  rollup (`:57`) still lists Q-9 under *Remaining*, so each sweep rediscovers it.

## 9. What this sweep does NOT cover

Stated so the next one does not assume the plan is now fully swept:

- Anything inside ml#1121 / ml#1122 / ml#1124's scope (see the table above).
- The residual clauses buried inside register rows marked closed — R-1's second clause, R-2's
  tooling-generalization clause, R-6's "retire the ad-hoc shim". Each may or may not be live; none
  was re-derived here.
- The plan's §12.2 sub-items beyond G-17.

---

## 10. Live state, probed 2026-08-15 — re-probe, do not copy forward

**ml#1124 §4 and §5 own the live-state and traps narrative**, including the `JuniperCascor1`
site-packages shadow (a 2026-07-01 copy of `cascor_constants.constants` that defeats imports rooted
outside `src/`) and the `gh pr checks --json` / pytest-exit-4 traps. Read it. Three probes are new
or worth restating:

- **No perf suite has ever run** — `ls ~/.local/state/juniper-experiments/suites/ | grep -c pf` → `0`.
- **The deploy container serves cascor 0.8.0** (`git_sha d8ae2f9`, built 2026-08-09) while disk and
  `JuniperCascor1` are both 0.9.0. A 6-day-old image, not a drift bug — but do not read container
  output as current code.
- **`:8201/v1/health` answers 200 unauthenticated**; `/v1/training/status`, `/v1/metrics` and
  `/v1/network` return 401 `Missing API key`. A 401 there is not a health failure.

Standing facts, re-probed:

- **The isolated E2E trio is DOWN** — nothing on `:8051` / `:8101` / `:8202`. Earlier handoffs'
  "do not touch the live isolated stack" no longer applies to those ports.
- **The `juniper-deploy` Docker stack is up (6 days)**: canopy `127.0.0.1:8050`, cascor
  `8201→8200`, recurrence `8211→8210`, juniper-data **container-internal `8100` only, unreachable
  from the host**, Grafana `3001→3000`, Prometheus `9090`, Alertmanager, two workers, redis. Eight
  report `(healthy)`; grafana and prometheus define no healthcheck. **canopy's healthcheck flaps**
  (ml#1122 `:416`) — it currently reads healthy; do not treat a single reading as stable.
  **Do not tear the stack down.**
- **A native Grafana v13.0.1 binds `*:3000`** — that listener is F-P1-2's subject and an open owner
  decision (ml#1124 §3). Deploy's Grafana is the separate loopback `:3001` instance (v12.4.0,
  `juniper-deploy/docker-compose.yml:931`).
- Experiment ranges `8110-8139` / `8230-8259` / `8260-8289` clear; `/run/user/1000/juniper-experiments`
  empty; no `run_suite.py` / `run_experiment.py` process. GPU **680 MiB used of 8192**, desktop
  processes only — `--query-compute-apps` returns rows when idle, so a non-empty list is not
  contention.
- **`ss -tlnpH 'sport = :A' 'sport = :B'` returns EMPTY with exit 0** — one port per call, or you
  will manufacture a false "the stack is down".

## 11. Verification commands

Every `file:NNN` in §2–§8 was probed on 2026-08-15 against juniper-ml `b2f9f4e` and juniper-cascor
`3857d1e`. **Re-confirm any anchor before acting on it; if a path, symbol or flag does not resolve,
stop and report rather than substitute a nearby one.** The commands below re-verify only a subset.

Run from the `juniper-ml` repo root.

```bash
git fetch --prune && git log --oneline HEAD..origin/main   # empty before committing
gh pr list --repo pcalnon/juniper-ml --state open          # dup-guard; turns over in minutes
gh issue list --repo pcalnon/juniper-cascor --state open   # expect zero

# §2 — the perf lane has never run
ls util/experiments/suites/perf/
ls ~/.local/state/juniper-experiments/suites/ | grep -c pf          # expect 0

# §3.1 — no execution: key for the driver budget; the e-i suite overrides it in the matrix
grep -n "max_wall\|max-wall" util/experiments/run_suite.py           # expect NO match
sed -n '64p;330p' util/experiments/run_suite.py
grep -n "max_wall_seconds" util/experiments/suites/p4/e-i-cascor-cap-ceiling.yaml

# §3.2 — Q-1's file is still unwritten
grep -rn "experiment.resolved" util/ notes/ | grep -v "^notes/JUNIPER_2026-07-29"  # expect none

# §4.2 — the parity cross-check cannot run in CI
sed -n '32p;152,153p' ../juniper-data-client/tests/test_generator_parity.py

# §6 — E-C: suite rebased 2026-08-13, newest run predates it
git log -1 --date=iso --format='%ad %h' -- util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml
ls -dt ~/.local/state/juniper-experiments/suites/e-c-* | head -1
```

## 12. Git state — re-derive; several sessions push concurrently

- `juniper-ml`: `origin/main` at `b0c9a41` (ml#1126) at landing — it moved from `b2f9f4e` (ml#1125)
  during this document's own validation pass, which is the concurrency this heading warns about and
  the reason the anchors in §2–§8 are stamped to `b2f9f4e`. This session worked in the
  **primary checkout** on `main`; this file is landed through `util/open_signed_pr.py`, which needs
  no working tree and produces a GitHub-signed commit — `required_signatures` rejects an unsigned
  commit anywhere in a branch's history, and squash does not rescue it.
- **ml#1119** (release-train propose-lane signing closeout) was the only other open PR; it belongs
  to another session. ml#1124 **merged 20:21Z** — its register is authoritative in its scope.
- ml open issues #1012, #1011, #588, #434, #358, #357 are pre-existing backlog, none from this arc.
- `juniper-cascor`: `origin/main` at `3909d27` (#523). The **primary checkout was one commit behind
  at `3857d1e`** — sync before running anything against it.

## 13. Approval

**This document makes no standing-approval claim.** Merge approval is per-session and does not
carry across handoffs; a prior handoff's "carried forward … explicitly for its successor" clause is
self-referential and is not the owner speaking. Ask for the named group.
