# HANDOFF 2026-08-24 — T6: the E-A/E-I/E-C re-baseline, still owed

Successor to [`HANDOFF_2026-08-18_cli-experimentation-unowned-tasks.md`](HANDOFF_2026-08-18_cli-experimentation-unowned-tasks.md),
whose T1–T2, T4–T5 and T7 are **closed**; **T3 is closed only in part** (§0.1). This document owns
**T6** plus the residual work §0.1–§0.2 name.

**Nothing is in flight.** No experiment driver, no campaign; experiment port ranges
`8110-8139` / `8230-8259` / `8260-8289` were clear at handoff time.

**"The plan"** always means
`notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`.
Where a *different* plan is meant it is named in full — the requirements one in particular.

**Anchors move — locate by pattern, never by line number.** juniper-cascor took **19 commits** between
2026-08-21 and 2026-08-24 alone (they span #547–#575, and #568–#573 do not exist — which is
itself why you grep rather than interpolate). Every citation below carries enough surrounding
text to `grep`. If a number does not resolve, grep the quoted text; do **not** read the neighbouring
line and assume.

**Validated by five independent agents across two rounds** — round 1 on non-shared lenses
(citations / executability / coverage) returned FAIL with ~40 defects; round 2 re-checked the
corrections and found 17 more, including a budget sum off by 12 GPU-hours and two trap recipes that
did not do what their prose claimed. Both rounds are folded in. Its
first draft recommended a *resume* that would have silently produced a split baseline — see §1.3.

---

## 0. What closed, so you do not re-derive it

| item | what | PR | merge |
|---|---|---|---|
| **T1** | wall-ordering gate (hard-fail) + 4 cascor suites fixed + `_oversize_reasons` inherited fix | ml#1200 | `cd81e3c` |
| **T2** | Q-1 `experiment.resolved.yaml`, re-scoped to what is verifiable | ml#1231 | `c8ecbba` |
| **T3** | `GET /v1/generators` install hint (W-4) — **partial, see §0.1** | juniper-data#277 | `fec68b4` |
| **T4** | generator-parity cross-check actually runs in CI (W-9) | juniper-data-client#157 | `7906299` |
| **T5 / L-2** | the `max_epochs` / `output_epochs` split SETTLED as intended | cascor#555 | `c239944` |
| **T5 / L-4** | W-11 full parity — 9 keys wired, 17/25 TrainingParams mapped | cascor#556 | `15ad3d8` |
| **T7** | requirements v5 refresh; consolidator rebuilt; `JR-REC-*` official | ml#1249 | `79d02f2` |
| **T6 (partial)** | `wide-pool-long` budget 3600 → 5400; F-P4-6 recorded; campaign driver preserved | ml#1284 | `1d4a255` |

**Decisions, with the rationale that stops them being re-litigated:**

- **L-2 — the `max_epochs` / `output_epochs` split is INTENDED.** Do not "fix" the warning by
  forwarding `max_epochs` into `grow_network`. Reason: `max_epochs` is in
  `TrainingLifecycleManager._FIT_KWARGS`, so forwarding changes **service** behaviour and is
  **golden-suite-visible** — a deliberate release, not a quiet patch. ml#1159's manifest warning is
  the instrument; it fires on every E-A cell (`max_epochs=2000 is set without output_epochs`) and is
  a WARNING, not a failure. Expected noise during T6.
- **L-4 — 17 of 25 `TrainingParams` keys are mapped, and that is finished, not partial.** The eight
  unmapped keys are deliberate: `auto_snap_*` (service snapshot lifecycle) and the multi-candidate
  set have no CLI counterpart, and **`epochs_max` is pinned by a test** so nobody "completes" the map
  by adding it — it is documented DEPRECATED/never-applied server-side, so mapping it would make the
  CLI honour a knob the service ignores. `max_epochs → output_epochs` aliasing is also deliberately
  untouched (it is what gives the CLI one budget for every pass; the divergence is instrumented).
- **L-4 changed what a direct-CLI run computes, on BOTH legs of the R-3 rule.** `max_iterations` now
  bounds `grow_network`'s loop (the CLI previously ran the constant 1000000), so a CLI
  spiral-baseline run caps at `min(12, 24) = 12` rounds. **`early_stopping` is now mapped too**, which
  is the other leg: the R-3 cap-reading rule holds only under `early_stopping: true`, and the CLI now
  honours whatever the YAML says. **Prior direct-CLI results are not comparable across cascor#556.**
  This does **not** affect T6 — E-A/E-I/E-C run the SERVICE path (`POST /v1/training/start`), and
  cascor's Golden Regression + Conformance gates both passed on the L-4 merge.

### 0.1 T3 is closed only in part — three live residuals

The core shipped (`juniper-data/juniper_data/core/models.py` gained `install_hint`; the registry
helper and five tests landed). But:

1. **G-16's acceptance is half-unmet.** The predecessor required "G-16 re-checked against a live
   `mnist` refusal". What was verified live is the **listing** (`available=False` + hint) on a host
   where HF `datasets` really is absent. Both *refusal* paths — the 501 on `POST /v1/datasets` and
   the driver preflight — were exercised only under `patch(... HF_AVAILABLE, False)` in a TestClient.
2. **The driver still does not consume the hint.** `util/experiments/run_experiment.py` still emits
   "see `GET /v1/generators` for the install hint" while `preflight_generator` already holds the
   `GeneratorInfo` dict that now carries it. The plan's own W-4 row says **"Prefer the pre-flight"** —
   the preferred remedy is the unbuilt half. Acceptance was an OR, so closure stands, but this is
   real work.
3. **`install_hint` is unreleased.** juniper-data `pyproject.toml` is `0.11.0` and the `v0.11.0` tag
   predates `fec68b4`, so **no consumer sees the field — including T4's own parity lane**, which
   installs `juniper-data[api]` from PyPI. A juniper-data release is the unblock.

### 0.2 Open work this session created and did not finish

> **STATUS 2026-08-25 — five of the six bullets below are CLOSED. One is still open.**
> The bullets are left exactly as written; this banner is the current answer.
>
> | # | bullet | status |
> |---|---|---|
> | 1 | `h2h_wide_nrot3.yaml` **durability risk / relocation** | **STILL OPEN — owner decision.** Untouched deliberately. Exposure re-counted 2026-08-24: **7 suite YAMLs plus `util/ad-hoc/2026-08-16_h2h_preflight.py`**. |
> | 2 | that file's **arm-equalisation taxonomy** | **CLOSED** — ml#1316 (`2a914f7bc`). |
> | 3 | cascor **`_resolve_cli_overrides` docstring** | **CLOSED** — cascor#580 (`b3819e343`). |
> | 4 | **L-item ledger** not updated by either T5 PR | **CLOSED** — ml#1316 added **§10** to the F-P1-3 doc. |
> | 5 | **invisible INVERTED cascor suite** | **CLOSED** — ml#1316. |
> | 6 | **gate's own stale text, two places** | **CLOSED** — ml#1316, both places. |
>
> **Three corrections to the bullets themselves**, found while closing them — the bullets
> understate the problem in each case, so do not use them as the specification:
>
> 1. **Bullet 2 names three keys; it is SIX.** cascor#556 also mapped
>    `candidate_learning_rate`, `convergence_threshold` and `candidate_convergence_threshold`
>    — all three sit in the file's OMIT bucket. That bucket's *premise* is therefore void, not
>    just its labels: pre-#556 omitting a key equalised the arms, post-#556 it leaves each arm
>    on its own default, and #556's commit note records two of those defaults differing by
>    **2x and 100x**. The taxonomy is marked STALE-pending-re-derivation rather than relabelled,
>    and **no param value was changed** — seven suites inherit this file.
> 2. **Bullet 2's non-inheritance rationale is now void too.** The file says it must not inherit
>    `spiral-baseline.yaml` *because* the CLI cannot receive `candidate_patience`. It can now.
>    The `base_config` is nonetheless unchanged — re-pointing it would re-measure seven suites.
> 3. **Bullet 5's fix is not "raise the timeout".** The author's `1800` was preserved and moved
>    onto the mechanism that writes a manifest: `execution.max_wall_seconds: 1800` with
>    `per_run_timeout_seconds: 2700` as the outer backstop. Raising the timeout to clear 3600
>    would have doubled the cell cost the author never asked for.
>
> **The blindness that hid bullet 5 is also closed.** `util/ad-hoc/2026-08-20_wall_ordering_survey.py`
> gained an **AD-HOC section** (ml#1316) reporting suite-shaped YAML under `util/ad-hoc/`. The **gate
> is deliberately NOT extended** — hard-failing CI on scratch files would make `util/ad-hoc/`
> un-scratch — so defects there are reported, never enforced.
>
> **§0.1 (T3) is untouched.** All three of its residuals remain open, including the unreleased
> `install_hint`. **§1 (T6 itself) is untouched** — the re-baseline was never run; see the banner there.

- **`util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml` — durability risk, still an owner decision.**
  Predecessor §1.6 raised it 2026-08-17 ("Relocating it is a **Paul decision**"). Exposure has since
  grown from 5 shipped suites to **7** (ml#1278 added `p4/e-m-h2h-paired-cap64.yaml` and
  `p4/e-n-profile-cap4.yaml` onto the same base). A routine ad-hoc cleanup would silently re-point
  seven suites at the driver default.
- **That same file's arm-equalisation taxonomy is now factually wrong.** Its design comments assert
  `max_iterations`, `early_stopping` and `candidate_patience` are unmapped and that a
  candidate-patience comparison is "NOT AVAILABLE" until the map carries the key. cascor#556 mapped
  all three. The file has not been touched since ml#1143. **Grep it for `NOT AVAILABLE` before
  trusting any of its equalisation notes.**
- **cascor#556 re-broke the docstring cascor#555 had just fixed.** `juniper-cascor/src/main.py`'s
  `_resolve_cli_overrides` docstring still offers "service-tier-only knobs like **max_iterations** or
  **candidate_patience**" as examples of *unmapped* keys — both are now mapped, three lines above
  #555's own note explaining why a mapped example teaches the opposite of the point. Self-inflicted;
  fix it with the corrected examples (`multi_candidate`, `auto_snap_best`).
- **The L-item ledger was not updated by either T5 PR.**
  `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md` §5 still
  marks L-2 and L-4 "Inert". A successor consulting the register these items are filed in gets the
  pre-session answer.
- **A cascor suite fails the T1 ordering predicate, invisible to both the survey and the gate.**
  (It is the sixth failing row overall and the *only* cascor one — every gated cascor suite passes.)
  `util/ad-hoc/2026-08-10_spiral_correlation_threshold_diagnostic.yaml` is a real `app: cascor` suite
  with `per_run_timeout_seconds: 1800` against spiral-baseline's 3600 s budget — **INVERTED**. Both
  the survey and `_suite_files()` scan only `util/experiments/suites/`, so neither can see it. This is
  the predecessor's own §0.2 lesson ("ask where else X may legitimately live") unapplied.
- **The gate's own text is stale, in two places.** `TimeoutOrderingContractTest`'s *docstring* says
  "3 inverted, 6 equal, 14 correct"; a separate *inline comment* further down says "the reason CI
  judges 7 suites of 23". The tree is now **25** suites. Fix both — editing only "the docstring"
  leaves the second.

---

## 1. T6 — what it is, and what is actually left

> **STATUS 2026-08-25 — T6 STILL OWED. Not started; nothing below is superseded.**
> No suite was run, no GPU hour was spent, and **attempt 1 remains the only data on disk**.
> §1.3's warning stands in full: do **not** `--resume` it.
>
> **Blocked on §2.1's quiet-host criterion, which was never met.** Probed 2026-08-24 04:30:
> 15-minute load average **12.43** on 16 cores against a bar of ~4, with `duplicati` at
> **81% CPU for 2 days 12 hours**. Two things worth knowing before re-probing:
>
> - That `duplicati` is **not** the scheduled lane and no timer will clear it. Its PPID is
>   `gnome-shell` — a hand-launched desktop job, started 2026-08-21 16:25. Meanwhile
>   `duplicati-backup.service` had **failed** (exit 100, mem peak 27.3 G) and its timer is
>   `disabled`. §2.1 already says to check `ps` as well as `systemctl`; this is why.
> - Everything else in §2.1 **passed**: all three experiment port ranges clear, the reaper
>   clean (0 orphans, 0 protected), and `experiment_stack.bash --status` showing nothing live.
>   The host CPU was the only failing gate.
>
> **The §2.3 cascor gap was ZERO at probe time** — checkout HEAD == `origin/main` == `4a92082`,
> tree clean. That is the cleanest possible pin, and it decays: cascor moved 19 commits in the
> three days before. **Re-derive it per §2.3 anyway** — this line is a dated observation, not
> a standing answer.
>
> §0.2's residual list *is* largely closed — see the banner there — but that is bookkeeping
> around T6, not T6.

**Why**: cascor#514 made `candidate_patience` / `candidate_convergence_threshold` actually reach the
candidate pool, and `spiral-baseline.yaml` sets `candidate_patience: 100`. R-5 §5.1
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R5-SERVICE-VS-CLI-EVIDENCE.md`,
grep `not directly comparable`) records that every published spiral figure was measured with the pool
at patience 50, and that a re-run must **either pin the pre-#514 code or re-baseline the grid**. The
owner chose re-baseline. Separately E-C's published surface is cap-bound — grep `KNOWINGLY STALE` in
`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md`.

**Do not re-litigate R-4.** The owner decided E-C's spiral rows get an E-A-class budget rather than
reducing E-C to a moon-only study; the suite already encodes it.

### 1.1 Attempt 1 (2026-08-23) — E-A 10/12, then killed. Reference only.

```text
~/.local/state/juniper-experiments/t6-rebaseline-20260823T200328Z/                   # campaign.jsonl + logs
~/.local/state/juniper-experiments/suites/e-a-cascor-budget-sweep-20260823T200329Z/  # registry.jsonl, aggregate.csv, REPORT.md
```

cascor was pinned at `341ffa3`. E-A ran 11,221 s, completing **10 of 12** cells; E-I was killed
5 min 07 s in (F-P4-6 records "~4 minutes" — correct it to 5 m 07 s when you update that
finding); E-C never started. Two failures, different in kind:

- **c010-27f3447e** (pool 8 / cap 32) — `torn_down_early`, exit **3** (`EXIT_UNREACHABLE`), service
  `Connection refused` at 141 s. No CUDA OOM, no kernel OOM, 60 GB RAM free. **Infrastructure.**
- **c011** (pool 32 / `max_epochs` 5000) — `timed_out` at **3616.1 s** against the inherited 3600 s
  budget, where it ran **2893.1 s** pre-#514. **A real result**, already acted on: budget raised to
  5400 in ml#1284, which is why its cell id moved `850cdc66` → `63f4fcb9`.

### 1.2 The measurement you must NOT reuse

Matched-cell wall time came out **+16.9%** (6,380.7 → 7,457.3 s), nine of ten cells slower
(+6.5%…+52.8%), one *faster* (−27.8%, pool 4 / cap 32).

**Not a cascor#514 measurement, and F-P4-6 says so.** The host was picked on a load-average lull of
4.09 (the 1-minute figure, observed directly) while the 15-minute average was **19.55**, with a
`duplicati` backup >200% CPU throughout. One cell moving the other way is not what a uniform
code-induced slowdown looks like. **Do not quote +16.9% as evidence of anything.**

### 1.3 ⚠ The obvious shortcut is WRONG — do not resume attempt 1

A `--resume` of the 2026-08-23 E-A suite dir would re-run only c010 and c011 and keep ten cells
measured at `341ffa3`. **Since that pin cascor has moved 8 commits to the current checkout and 9 to
`origin/main`, two of which move exactly the quantities E-A measures:**

- **#563** `perf(logger): resolve the caller from f_back … (~9x faster training)` — the inspect frames were
  ~78% of candidate-worker CPU, `getmodule` alone ~33%. Wall time, E-A's primary metric, is not comparable across it.
- **#566** `fix(seeding): derive candidate seeds from a network-owned RNG` — its commit body is headed
  **`BASELINE RESET -- READ THIS`** and states the change is *"a deliberate numerical discontinuity"*
  on **every** path. Seed-42 goldens were regenerated. Accuracy is not comparable across it.

Splicing two post-#566 cells into a ten-cell pre-#563 grid manufactures precisely the incomparability
T6 exists to remove — inside a single suite, where no SHA guard would catch it. **Re-run all three
suites from scratch at one SHA. Treat attempt 1 as reference data only.**

### 1.4 Remaining work

1. **Wait for a genuinely quiet host** (owner instruction, 2026-08-23). Criteria and pre-flight in §2.1.
2. **Re-derive the cascor gap yourself** (§2.3) and record the SHA you pin. Do not reuse this
   document's answer — it will be stale by the time you read it.
3. **Run all three suites detached, via the campaign driver** (§2.2). It pins and re-checks the SHA
   around every suite, which a standalone `run_suite.py` invocation does **not** do.
4. **Publish the grids**: lift the `KNOWINGLY STALE` marker on the E-C table and update F-P4-6 from
   INCOMPLETE to the real result.
5. **Scope note on attribution.** Steps 1–4 deliver *grids comparable to each other*. They do **not**
   deliver an attributable "#514 cost N%" — F-P4-6 states that needs a control (a re-run on a quiet
   host **or** the same grid re-measured at the pre-#514 commit under the same conditions). That
   second arm is neither scheduled nor budgeted here. Do not let step 4 imply otherwise.

**Budget.** Estimates, with their provenance, because they are not equally solid:

| suite | estimate | basis |
|---|---|---|
| E-A | **≈ 3.5–4 h** | attempt 1 ran 11,221 s but that covers only 10 completed cells (c010 aborted at 146 s vs 1,319 s pre-#514; c011 truncated at 3,616 s under a budget now 5,400 s). A genuine 12-cell run is *more* than 3.1 h. |
| E-I | **≈ 2.4 h** | 8,648 s, measured (1,497 + 2,907 + 4,244). |
| E-C | **1–3 h, UNMEASURED** | every E-C run on disk predates the 2026-08-13 rebase onto `spiral-baseline` and totals 0.02–0.47 h at the old smoke cap. This is a guess, not a measurement. |

Total **≈ 7–9.5 GPU-hours**. Worst case against configured *ceilings* is far higher:
E-I 3 × 14,400 s = 12 h, E-C 8 × 3,600 s = 8 h, E-A 11 × 3,600 s + 1 × 5,400 s = 12.5 h →
**≈ 32.5 h**. The ceilings are what the driver enforces; the estimates are what it has historically
used. Size any host reservation against the ceiling, not the estimate.

---

## 2. Traps that each cost real GPU hours

### 2.1 "Quiet host" means the 15-minute average — and a port sweep, not just load

The previous session called the host quiet at `load average: 4.09` (1-minute) and lost a campaign to a
box whose 15-minute average was 19.55. Pre-flight, **from the worktree**:

```bash
uptime                                                   # judge the THIRD number (15-min)
ps -eo pcpu,pid,etime,comm --sort=-pcpu | head -6        # row 1 is the header, row 2 is often `ps`
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
bash util/reap_pytest_orphans.bash --dry-run             # surfaces protected/orphan stacks
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  bash util/experiment_stack.bash --status | grep -iE "UP|healthy"   # NO --dry-run: it suppresses the probe
```

Want: 15-minute average near or below ~4; **no `duplicati` / `duplicati-cli` in the top-CPU list**;
GPU under ~1 GiB; and the last two commands showing nothing live. **Load and GPU alone are not
enough** — a competing cascor on `:8202` (the isolated E2E trio) passed both gates during validation
while genuinely running. ml#1292 landed a scheduled backup lane under `systemd --user`; check
`systemctl --user list-unit-files 'duplicati*'` (a *disabled* timer appears in neither
`list-timers` nor `--all`) **and** `ps` for a long-lived `duplicati` daemon, since the daemon
predates the timer.

### 2.2 A long run CANNOT be a harness background task — this applies to EVERY step, not just the driver

Attempt 1's campaign was killed, and so was c010's cascor. Both belong to the population documented in
`notes/JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SAFE-MERGE-KILL-FORENSICS.md` §3.4. The mechanism is a
**spare `[bg]` worker's ~3600 s lease** expiring — and the lease is *inherited*, so a task landing on
an already-old worker gets only the remainder (the documented case got 229 s). It is **not** a
universal 3600 s cap: §3.4 also records long-lived `slash` workers running 8.5–23.6 h and five
completions above 3600 s, which is why attempt 1 survived 3.1 h before dying. You cannot tell which
kind of worker you landed on, so **even a single suite must be launched detached.**

Note the population figure: §3.1's "19" was **corrected upward to 33** on 2026-08-20 ("the figures
above are an undercount… treat the corrected figures as canonical"). Cite 33, not 19.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml    # or your worktree
conda activate JuniperCascor1                             # see §2.7 — the interpreter is recorded
setsid nohup bash util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash \
  > ~/.local/state/juniper-experiments/t6-campaign.out 2>&1 < /dev/null &
```

The campaign dir is timestamped at launch and printed **only** into that `.out` file
(`campaign dir : …`), so read it from there, then poll that dir's `campaign.jsonl`.

### 2.3 Re-derive the cascor gap — the driver pins the CHECKOUT, which lags `origin/main`

`util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash` records `git -C juniper-cascor rev-parse HEAD`
before and after **every** suite and aborts on change. It also **aborts with exit 2 if the cascor tree
is dirty** — a detached launch onto a dirty tree dies in seconds with the cause only in the `.out`.

It pins the **checkout HEAD**, routinely *behind* `origin/main` (attempt 1 pinned `341ffa3`, two
behind). That is fine and describable **only if you check what the gap contains**:

```bash
J=/home/pcalnon/Development/python/Juniper
git -C $J/juniper-cascor rev-parse --short HEAD                       # what gets pinned
git -C $J/juniper-cascor log --oneline HEAD..origin/main              # READ EVERY SUBJECT
git -C $J/juniper-cascor log --format='%B' HEAD..origin/main | grep -iE "baseline reset|discontinuity|seed|perf"
```

Attempt 1's gap was benign (#561 snapshot I/O, #562 resize config sync — neither reachable from suites
that train fresh at fixed dimensions). **That answer is expired**; #563 and #566 have since landed.
Decide deliberately whether to pin the checkout or `git pull` it first, and record which.

Pinning via a dedicated worktree was considered and **rejected**: juniper-cascor is installed
**editable** into `JuniperCascor1`, so a pinned cwd mixes with primary-checkout imports and yields a
baseline nobody can describe.

### 2.4 `JUNIPER_EXP_PROJECT_DIR` is mandatory from a worktree

`util/experiment_stack.bash` derives `PROJECT_DIR` from its own location
(`PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-$(dirname "${JUNIPER_ML_DIR}")}"`), which resolves to
`.../.claude/worktrees` from a worktree — so `CASCOR_SRC_DIR` points at a nonexistent directory and
**every cell fails**. Always export
`JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`. The campaign driver already does.
Same trap class bit `requirements_consolidate.py`'s `ECOSYSTEM_ROOT`.

### 2.5 A killed run leaves a stack up AND reaper-protected — in either of two roots

The run-dir `*.pid` outlives the driver, so `util/reap_pytest_orphans.bash` prints
`PROTECT  pid=… (live experiment)` (the per-process token is `PROTECT`; only the summary says
"protected") and the orphan holds GPU indefinitely. **`collect_protected_pids()` scans two roots** —
the experiment run root **and `/tmp/juniper-e2e`** — so a grep over `~/.local/state/...` alone can
come back empty. Find the owning run dir, then tear down:

```bash
J=/home/pcalnon/Development/python/Juniper
bash util/reap_pytest_orphans.bash --dry-run     # gives you the PROTECT pid
# mirror the reaper's own scan: -maxdepth 3 over BOTH roots (depth-1 launch pidfiles and
# <RUN_ID>/relays/*.pid both exist and a depth-2 glob misses them)
find ~/.local/state/juniper-experiments /tmp/juniper-e2e -maxdepth 3 -name '*.pid' \
  -exec grep -l "^<PID>$" {} +
```

**Then branch on WHICH root matched — they are different stacks with different owners:**

- Under the experiment run root → `RUN_ID` is `basename "$(dirname "<matched-path>")"`, and the tool
  is `JUNIPER_EXP_PROJECT_DIR=$J bash util/experiment_stack.bash --down <RUN_ID>`.
- Under **`/tmp/juniper-e2e`** → this is the isolated E2E trio, **not** an experiment run. There is no
  RUN_ID (`basename $(dirname …)` yields the literal `juniper-e2e`), and its owner is
  `bash util/isolated_stack.bash --down`, which stops by port and takes no argument. Per §3 that
  stack may be **another session's live work** — confirm before stopping it.

Then `bash util/reap_pytest_orphans.bash` (may need TWO passes).

A run dir with **no `manifest.json`** is the signature of a killed run — the driver writes it
unconditionally from a `finally`. The 2026-08-21 orphan found during T1 was the same class. Observed
2026-08-23 (this session's own measurement, not otherwise recorded): **7534 MiB of 8192** held by
~63 orphan forkservers, freed to 564 MiB by two reaper passes.

### 2.6 Wall-ordering is gated — keep every budget strictly BELOW its suite timeout

ml#1200 made the ordering a **hard-fail** contract
(`tests/test_experiment_suite_yamls.py::TimeoutOrderingContractTest`): a suite **fails** when
`per_run_timeout_seconds <= effective_budget`. E-A is timeout `7200` vs budget `3600..5400`. If you
raise a budget, keep it strictly below the timeout, or run_suite's subprocess kill pre-empts the
driver and **the manifest is lost entirely**. Re-check:

```bash
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  python3 util/ad-hoc/2026-08-20_wall_ordering_survey.py
```

### 2.7 Environment: the driver interpreter is whatever `python3` you have

`run_suite.py` uses `python_bin = os.environ.get("JUNIPER_SUITE_PYTHON", sys.executable)`, so **your
shell's `python3` becomes the driver** and is recorded per cell in `manifest.environment.python`.
Attempt 1 ran `3.13.13` (JuniperCascor1); `/usr/bin/python3` is `3.13.7`. Running a leg from a shell
without JuniperCascor1 active writes different provenance into the same grid. `experiment_stack.bash`
is safe either way (it hard-defaults `CASCOR_CONDA=JuniperCascor1`); only the driver drifts.

**There is no git SHA in the per-run manifest** (`manifest['git']` is `{}`; `packages` records only
version `0.9.0` + editable path, unchanged across every one of those commits). The campaign driver's
`campaign.jsonl` is the **only** SHA ledger — another reason to run through it rather than invoking
`run_suite.py` directly.

---

## 3. Live state — probed 2026-08-24, RE-PROBE, do not copy forward

- **No experiment driver, no campaign.** Experiment port ranges clear at handoff time.
- **The `juniper-deploy` Docker stack is up** (canopy `127.0.0.1:8050`, cascor `8201`, recurrence
  `8211`, Grafana `3001`, Prometheus `9090`). **Do not tear it down** — unrelated to the experiment
  ranges.
- **The isolated E2E trio (`8051` / `8101` / `8202`) came UP during this handoff's validation** and
  another session appears to be restarting it (its pid changed between two probes minutes apart). Its
  pidfile lives in `/tmp/juniper-e2e/`. Treat `:8202` as someone else's live work unless you have
  established otherwise.
- `*:3000` is **Domotz, not Grafana**; deploy's Grafana is the loopback `:3001` instance.
- `ss -tlnpH 'sport = :A' 'sport = :B'` returns EMPTY with exit 0 — **one port per call**, or you will
  manufacture a false "the stack is down".
- Host was **not** quiet at handoff time: `duplicati` daemon ~81–99% CPU.

---

## 4. Git state

- **juniper-ml**: `origin/main` at **`6f8509d`** and moving fast (it advanced 17 commits during this
  session's validation alone). The worktree
  `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sequential-puzzling-whistle`
  (branch `worktree-sequential-puzzling-whistle`) was synced to that tip; the only untracked file was
  this handoff. **`git log HEAD..origin/main` is the check — do not assume the branch tip is the
  remote tip; the first draft of this document made exactly that error.**
- **juniper-cascor**: `origin/main` **`4a92082`**, primary checkout HEAD **`fcb4192`** — they differ,
  which is normal; §2.3 says what to do about it.
- **juniper-data**: T3's core merged (`fec68b4`) but **unreleased** — see §0.1.3.
- **juniper-data-client**: T4 merged (`7906299`); its parity lane cannot see `install_hint` until
  juniper-data releases.
- Open ml PRs at handoff (none from this arc): #1305 recurrence roster blind-spot, #1304 lockfiles.
- **Merge traps** (`reference_github_pr_ci_trigger_traps`): merging a base with `--delete-branch`
  irreversibly closes a stacked child; `gh pr edit --body-file` can silently no-op behind a
  Projects-classic warning (use `gh api -X PATCH ... -F body=@file`); `until gh pr checks N | grep -qv
  pending` does **not** mean "until nothing is pending" (use `until ! ... | grep -q pending`).
- Use `util/safe_merge.py` — direct pushes to main are blocked fleet-wide. Carry any
  `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` trailer into the **squash** commit message or
  post-merge `main-verify` goes red on a waiver the PR itself had.

---

## 5. Verification commands

Run from the worktree; sibling paths are absolute because `../juniper-*` does **not** resolve from
one. Re-confirm any anchor before acting; if a path, symbol or flag does not resolve, **stop and
report rather than substitute a nearby one**.

```bash
J=/home/pcalnon/Development/python/Juniper

git fetch --prune && git log --oneline HEAD..origin/main   # empty ONLY if still synced; ml main moves hourly
gh pr list --repo pcalnon/juniper-ml --state open          # dup-guard; turns over in minutes
git -C $J/juniper-cascor rev-parse --short HEAD            # what the campaign will pin
git -C $J/juniper-cascor log --oneline HEAD..origin/main   # the gap to read (§2.3)

# attempt 1, reference only
ls ~/.local/state/juniper-experiments/t6-rebaseline-20260823T200328Z/
python3 - <<'PY'
import json
S='/home/pcalnon/.local/state/juniper-experiments/suites/e-a-cascor-budget-sweep-20260823T200329Z'
for l in open(S+'/registry.jsonl'):
    r=json.loads(l); print(r['cell_id'], r['outcome'], r.get('wall_seconds'))
PY

# the budget bump and the ordering guard
grep -n "max_wall_seconds: 5400" util/experiments/suites/p4/e-a-cascor-budget-sweep.yaml
JUNIPER_EXP_PROJECT_DIR=$J python3 util/ad-hoc/2026-08-20_wall_ordering_survey.py | grep e-a-cascor

# the record of attempt 1
grep -n "F-P4-6\|KNOWINGLY STALE" notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md

# §0.2 residuals, each should still reproduce
grep -n "NOT AVAILABLE" util/ad-hoc/2026-08-16_h2h_wide_nrot3.yaml
grep -n "service-tier-only knobs like" $J/juniper-cascor/src/main.py
grep -n "per_run_timeout_seconds" util/ad-hoc/2026-08-10_spiral_correlation_threshold_diagnostic.yaml
grep -rn "Inert" notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md | head -4
```

Relevant suites: `python3 -m unittest tests.test_experiment_suite_yamls tests.test_run_suite tests.test_run_experiment`
(200 tests, OK as of this handoff).

---

## 6. What this document does NOT cover

- **The 5 recurrence wall-ordering rows** — `recurrence-d-sweep` (600/900, inverted) and `p4/e-d`,
  `p4/e-f`, `p4/e-g`, `perf/pf5` (900/900, equal). T1 gated cascor only; the recurrence budget is the
  socket timeout on the synchronous `POST /v1/train`, a different failure mode needing its own
  analysis, and `perf/pf5` sits inside the gated perf lane. (The sixth, cascor, row is §0.2.)
- **The requirements cross-view inconsistency** — 52 entries differ between `by-area` and `by-repo`,
  149 between `by-area` and `by-status`; `by-area` carries a spurious trailing period. Predates v5;
  recorded in **`notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md` §11**
  (the *requirements* plan, not the CLI-experimentation one) for its own pass.
- **T2's permanent residual** — `experiment.resolved.yaml` carries an explicit `_meta.scope`
  "NOT COVERED" line for app-level `Settings`. Option (1), a read-only settings surface in cascor and
  recurrence, was **declined**, not deferred; reviving it is a new owner decision.
- **T7's remaining JR-REC coverage items** — the plan's Wave 7.6 minimum listed the experiment-config
  layer, **G-5** (plotting gap), **W-5/W-7** (bench `--results-dir` / `ar_p` registration), **G-4**
  (missing Grafana dashboard) and **G-17** (absent `performance` marker). The predecessor carried only G-17
  into its not-covered list; all five are still open in the plan.
- **R-1's second clause** (do not report `succeeded` when zero candidates were installable) —
  unverified and homeless since the 2026-08-15 sweep.
- **The plan's §12.2 items 1 and 3** — run-level durations are not a metric; no cross-app comparison
  surface.
- **PF-4 / PF-8** — need a decision, not a suite; gated behind the perf-lane phasing note.
- **F-7 provenance re-pin** — ml#1142 recorded the recurrence re-pin beneath the plan's
  authoring-time table; the table itself is deliberately unchanged. No further action assumed.
- Anything inside the defect-register, canopy-E2E, snapshot or determinism arcs.

---

## 7. Approval

**This document makes no standing-approval claim.** Merge approval is per-session and does not carry
across handoffs. The re-baseline itself is owner-approved (2026-08-23, "full post-#514 re-baseline"),
as is the deferral until the host is quiet — but ask before spending GPU hours on anything beyond the
three suites named here, and before acting on any §0.1 / §0.2 residual.
