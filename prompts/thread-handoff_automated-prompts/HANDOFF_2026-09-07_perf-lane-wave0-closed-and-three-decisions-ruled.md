# HANDOFF 2026-09-07 — Wave 0 CLOSED, three owner decisions ruled, and two consensus findings REFUTED

Successor to
[`HANDOFF_2026-09-04_perf-lane-gate-built-waves-not-closed.md`](HANDOFF_2026-09-04_perf-lane-gate-built-waves-not-closed.md).

> **THE PREDECESSOR IS NOT SUPERSEDED. Keep reading it.** An earlier draft of this document claimed
> its §5 traps were "carried into §7 here"; consensus validation measured that as true for **1 of
> 12**. §7 below now carries the ones that had no other home, but the predecessor remains live for
> its §2 (key context) and §9 (consensus record, two findings of which this session refuted in
> place). Do not delete it, and do not assume this document contains it.
>
> **NOTHING IS RUNNING from this session.** No campaign, suite, monitor or background task survives
> it. Verify with a PROCESS check, not only ports:
> `pgrep -c -x sha256sum` and
> `ps -eo pid,cmd --no-headers | grep -E "run_suite|contention_load|headroom_sweep" | grep -v grep`.
>
> **A PEER session's stack IS running** and is not yours to touch — see §6.

`origin/main` was `ef73443f` when this was written and moves every ~10–28 min. **Re-check it; do not
branch from a recorded sha.**

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. **Wave 0 is CLOSED** and every owner decision the plan
was blocked behind is ruled. What remains splits cleanly into *needs an idle host* and *needs no host
at all*.

**Item numbers refer to
[`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
unless stated otherwise.**

### Immediate, in order

1. **Land `ml#1811`** if it has not merged — the only open PR from this session (`gh pr view 1811
   --json state,mergedAt`). It is armed with native auto-merge and goes BEHIND every time main moves;
   the fix is `gh api -X PUT repos/pcalnon/juniper-ml/pulls/1811/update-branch`, not a force-push.
2. **Free — Wave 4 item 4.3, and do it BEFORE 4.1.** Re-scope PF-8 against the headroom sweep first:
   §8.4 of
   [`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md)
   already answers the neighbouring question ("is contention real"), so PF-8 may be narrower than
   Wave 4 assumes — or redundant. **Answer that before building 4.1's harness.**
3. **Free — item 2.4 is UNBLOCKED** by the 2.5 ruling. It *establishes* a cascor micro timing
   reference; it does not build a gate. `baselines/baseline_20260526.json` holds 10 entries with
   **zero timing data**, and cascor's
   `src/tests/performance/test_baselines.py` has **no baseline-relative timing check** — only
   `_check_memory_regression` calls `load_latest_baseline`.
   **Do not repeat the inherited phrase "no timing tolerance of any kind"** — it is false: the same
   file defines `FIT_TIME_THRESHOLD_S = 60.0` (`:70`) and `SERIALIZATION_TIME_THRESHOLD_S = 30.0`
   (`:65`), both enforced by hard asserts (`:463`, `:466`). They are fixed absolute ceilings, not
   baseline comparisons — which is why 2.4 stands. **That false phrase is still live in
   `JUNIPER_2026-08-31_..._PERF-LANE-P1-DESIGN.md:45` and item 2.4 of the P2 plan; correct it at
   those sources**, or the next handoff re-inherits it.
   Caveat: `baseline_20260526.json` is **gitignored with zero commit history**, so it is invisible
   from a clean clone — 2.4's starting artifact exists only on this host. Repo: juniper-cascor.
4. **Needs an IDLE host — 2.1 (PF-2), and it needs a PROBE first.** See §4. Do not guess an epoch
   number.
5. **Needs an IDLE host and a quiet window — 2.2 (PF-3).** ~6.7 h worst case. Owner approval was
   given 2026-09-07 and still stands; only the window was missing.
6. **Item 2.3 (PF-5/6/7, recurrence) is REPORT-ONLY forever** absent new instrumentation inside
   juniper-recurrence. Do not build a gate for it.

### Do NOT do these

- **Do not wire `compare_baseline.py` to CI.** Closed 2026-09-07, structurally — see §3.
- **Do not "correct" the `13-20.5%` drift band to `15.0-20.5%`.** Refuted — see §3.
- **Do not make the "cannot serve as an upper bound" wording duration-conditional.** Refuted — §3.
- **Do not fast-forward the juniper-cascor primary checkout** without checking §6 first.

---

## 2. What shipped this session (verified by receipt, not by memory)

Each row was confirmed with `gh pr list --head <branch> --state all` — the form that distinguishes
"never opened" from "already merged".

| PR | merged | what |
|---|---|---|
| `ml#1758` | 2026-09-05T13:14:39Z | P4 operator surface was **stale, not missing**; six closed defects were listed as open |
| `ml#1767` | 2026-09-05T18:16:08Z | work contract in all 3 gate tools predated its own precondition |
| `ml#1762` | 2026-09-05T19:31:14Z | P2 plan + P1 design banners; iteration-cap mechanism **withdrawn** |
| `ml#1765` | 2026-09-05T22:08:30Z | drift-band **and** C4 refutations; handoff §7.1 decision record |
| `ml#1786` | 2026-09-07T12:54:47Z | item **3.3 discharged**; 2.1 re-survey; 2.2 deferral |
| `cascor#629` | merged 2026-09-07 | `xor-staged.yaml` sets both epoch keys to 200 |
| **`ml#1811`** | **OPEN at hand-off** | three owner decisions + Wave 0 close |

**`ml#1811` is described in the present tense deliberately.** It had not merged when this was
written. Do not assume it landed; check.

---

## 3. Key context — do not re-derive, and do not re-open

### 3.1 P1 §6 is CLOSED: do not wire the run tier to CI

**The owner's ruling stands. The justification below is NARROWER than the one the ruling was taken
on** — consensus validation (§10) showed the first draft over-claimed, and the correction is recorded
here rather than quietly applied.

**What is measured and certain:**

- `util/experiments/compare_baseline.py:63` treats `HOST_IDENTITY_FIELDS` — `cpu_model`,
  `cpu_count`, `thread_budget` — as **blocking**. A mismatch becomes a `basis_reason` (`:281-286`),
  and **`basis_reasons` outrank FAIL** (`:304` runs before the FAIL branch at `:306`), so the verdict
  is REFUSED, exit 2. There is **no bypass**: with empty `candidate_manifests` the host comparison
  still runs and mismatches *harder*, it does not skip.
- All 61 `runs-on:` declarations across all 24 workflow files are `ubuntu-latest`; **zero**
  `self-hosted` anywhere.
- The baseline the successor is told to use, `pf1-2026-09-04b/HOST.json`, records `cpu_count: 16`,
  `cpu_model: "AMD Ryzen 7 2700 Eight-Core Processor"`. Public-repo `ubuntu-latest` runners are
  **4 vCPU**. So `cpu_count` (16 ≠ 4) blocks before `cpu_model` is even reached.

⇒ **Against the current workstation-cut baseline, CI would REFUSE on every run.** That is the
vacuous-gate class this lane keeps finding, and it would have shipped as a feature.

**What the first draft over-claimed, and a successor must not repeat:**

- It said "STRUCTURAL" and "permanently", then two sentences later named a condition under which it
  reopens. A claim with a reopening condition is not permanent; it is *"true under the current CI
  configuration and the current baseline"*.
- **It named self-hosted runners as the ONLY reopening path. That is wrong and the alternative is
  cheap.** Nothing requires a baseline to be cut on the workstation: `make_baseline.collect_host()`
  reads `nproc` and `/proc/cpuinfo` from **whatever host ran the suite**. A baseline cut *on a
  hosted `ubuntu-latest` job* would carry `cpu_count: 4` and match every future `ubuntu-latest`
  candidate on that field, leaving only `cpu_model` (Azure's undocumented physical-CPU
  heterogeneity) open. **This path was never examined when the decision was taken.** If anyone wants
  to reopen P1 §6, that is the question to answer — not "do we have a self-hosted runner".
- **`thread_budget` is not a hardware fact.** It originates at
  `run_experiment.py:1448` — `{var: os.environ.get(var) for var in THREAD_ENV_VARS}` over the four
  vars listed at `run_experiment.py:225` — and `make_baseline.py:128,137` merely reads that
  pre-existing manifest field. All four are `null` in `pf1-2026-09-04b/HOST.json`, so a CI job that
  also leaves them unset matches trivially. Describing it as part of "same hardware" is imprecise.

Relaxing `HOST_IDENTITY_FIELDS` to advisory was considered and **rejected**: §2 of the P1 design
defines a run-tier regression as *"the same YAML, same hardware, same thread budget"*, so relaxing it
makes every CI comparison silently cross-hardware — the exact failure the refusal prevents.
`compare_baseline.py` is an **operator** tool. Item 1.4's decoupling of `run_suite`'s exit code from
the verdict stands as the settled design.

### 3.2 TWO consensus findings from the predecessor's §9 are REFUTED

Both failed the same way: **the claim about the numbers was checked; the numbers were not.**

**(a) The drift band.** §9 said the quiet floor is `15.0-20.5%` and that `13-20.5%` "mixes two
normalizations". Recomputed from the six source values in §5 / §8.4 of the sweep note:

| quantity | runs | `max/min − 1` | `(max−min)/max` |
|---|---|---|---|
| two quiet 20 s runs (18.42 → 20.81 ms) | quiet | **12.98% → the 13.0%** | 11.48% |
| three quiet sweep blocks (18.282 / 22.024 / 18.663) | quiet | **20.47% → the 20.5%** | 16.99% |
| `modest load 4/16` (18.42 → 21.18 ms) | **LOADED** | 14.98% → the 15.0% | — |

Both endpoints are already `max/min − 1` over **quiet** runs. **15.0% is the loaded run** — §4 of the
sweep note labels it `bridged quiet → modest load (4/16)`. Adopting it folds a load effect into the
noise band and makes §8.4's central claim circular (6 workers at +19.9% sitting *inside* a 20.5%
quiet band means nothing if the band contains a loaded run). The string is correct in **9 sites**
including the `metric_contract` written into every `baseline.json`.

**(b) C4.** §9 said *"drive cannot serve as an upper bound on noise"* is false above ~60 s, "where
the sd ratio is 0.86–1.25". **That range is the argument against the change.** An upper bound needs
ratio ≤ 1, and **0.86–1.25 straddles 1**. From §3 of the sweep note: at **66 s** the ratio is
`4.198 / 3.357 = 1.25`, so `drive` *understates* and cannot bound; at 126 s it is `0.87` and
overstates. Both directions above 60 s — precisely the condition the source sentence cites. The
finding conflates **faithful** (≈1) with **conservative** (≤1).

Both are struck in place in the predecessor with the arithmetic inline, and the normalization is
pinned next to the numbers in the sweep note.

### 3.3 The other two rulings

- **2.5 — PF-4 is REPORT-ONLY on timing. The ruling stands; ONE of its two arguments does not.**
  - The argument that **survives**: a ≥20% tolerance is worse than useless, because §8.4 measured six
    competing processes at **+19.9%** — blind to real regressions, yet fires on an ordinary loaded
    host. This alone supports not building a percentage-tolerance timing gate.
  - The argument that **FAILED validation**: "a micro-benchmark's op count is fixed by the test, so
    gating it gates a constant". **False for 1 of the 5 cascor micro files.**
    `test_micro_candidate.py:52-54` says so itself — *"train_detailed may early-stop when correlation
    plateaus, so epochs_completed can be less than the requested epoch count"* — backed by
    `assert 1 <= result.epochs_completed <= epochs`, an assertion that would be pointless if the
    count were fixed. Live execution during validation, seeded exactly as the test seeds:
    **requested 100 and requested 200 both completed 68** — two different budgets landing on the same
    early-stopping point, which is sufficient on its own to show the count is **emergent**,
    structurally identical to `step_count`. (A round-1 run reported 100 → 52; round 2 could not
    reproduce that figure and got 68. Treat the *thesis* as established and the exact numbers as
    host-load-sensitive — re-measure before quoting any of them.) The other four micro files are
    genuinely fixed.
  - **Therefore an unexamined option exists**: a work-style **exact-match** gate on
    `epochs_completed` for the candidate micro-benchmarks — the micro analogue of the run tier's
    split gate. It was foreclosed by reasoning that is wrong, not by evidence. **Owner call**; do not
    treat "PF-4 report-only" as having settled it.
- **0.5 — `xor-staged.yaml` sets both epoch keys to 200** (`cascor#629`, MERGED).
  **The matching removal of its `PENDING_EPOCH_SPLIT_DECISIONS` entry is in `ml#1811`, which was
  OPEN when this was written.** On `main` today that dict still contains `xor-staged.yaml`. Check
  before quoting: `git show origin/main:tests/test_experiment_config_schemas.py | grep -A2 PENDING`.
  Empty is its intended resting state once `#1811` lands.

### 3.4 Carried from the predecessor, still true

- **`timings.drive` is DE-RATIFIED** — quantized to `DEFAULT_POLL_INTERVAL = 5.0`. The 25×–182×
  understatement is a **CV ratio specific to 20 s cells**; at ≥60 s it collapses (see 3.2b).
- **`step_count` is exact and deterministic only WITHIN a termination branch.** Census: 333 runs,
  153 distinct configs, 79 repeated, **29 divergent — all explained by `completion_reason`, none
  within a branch**. Caveat: those 29 partition into 74 branches, **54 singletons**, so the finding
  rests on the **20 branches with n≥2**.
- **Identity is checked BEFORE work.** `config_sha256` cannot be the identity (it hashes
  `experiment.description`). `workload_fingerprint()` strips cosmetic keys but **keeps `seed`**.
- **Recurrence work is not countable *for the readouts the PF suites use* — with one carve-out that
  must not be dropped again.** `n_epochs` takes two values across 36 runs by readout type, and a
  closed-form readout never sets it. **But `juniper-recurrence-model/.../_readout_mlp.py:77,150`
  DOES maintain a genuine counter** (`self.n_epochs_ = epoch + 1`, commented *"epochs actually
  trained (LMURegressor reads this for TrainResult.n_epochs)"*). So "recurrence exposes no work-done
  counter" is **too absolute** — it is true of closed-form readouts, false of the MLP readout. This
  carve-out lived only in the predecessor's §9 and is recoverable from no other document; an earlier
  draft of this handoff dropped it while issuing an unqualified "REPORT-ONLY forever" instruction.
- **Pre- and post-2026-09-02 figures are not comparable** (`cascor#618` epoch pair).
- **Use baseline `pf1-2026-09-04b`**, at `~/.local/state/juniper-experiments/baselines/` — outside
  the repo, untracked. `pf1-2026-09-04` predates the `ml#1733` guard and is **correctly refused**.

---

## 4. Item 2.1 (PF-2) — what is settled and what is not

Re-surveyed 2026-09-07 against the resolved base config. **Two of the three concerns in the
predecessor's item 6 are DISCHARGED:**

| concern | finding |
|---|---|
| *"declares only `per_run_timeout_seconds`, not `outputs.max_wall_seconds`"* | True of the suite file — but `spiral-smoke.yaml` supplies `max_wall_seconds: 600`, and **600 < 2400**, so the driver budget binds first. §4 ordering **satisfied**. PF-1 is identical (1200 / 600). |
| epoch split | **Closed** — `cascor#618` gave the base config both keys; PF-2 inherits `max_epochs: 50` *and* `output_epochs: 50`. |
| duration | **STANDS** — native `(2,2)`/50 runs **15.09 s**, short of PF-1's ~60 s. |

**The PF-1 template you are copying is thinner than it looks** — carried from the predecessor's §9,
recoverable from no other document: the 50-epoch anchor is a **cross-suite n=2 mean with 26% internal
spread** (11.886 and 9.139), and the 500 / 2000 / 5000 probe points are **n=1 each**. The 4000 choice
is sound but rests on a thinner base than four clean points would suggest. Budget more probes for
PF-2, not fewer.

**No epoch override is proposed, deliberately.** PF-1 reached 4000 by *probing* 500 / 2000 / 5000 and
interpolating within the upper segment, because the log-log slope changes (~0.32 below 2000, ~0.71
above) where early stopping stops binding. PF-2 is harder: its matrix spans an **8× dataset range** (2000/250)
(`n_points_per_spiral: [250, 500, 1000, 2000]`), so one epoch value must put the *smallest* cell over
the duration floor **and** keep the *largest* inside `max_wall_seconds: 600`. Whether one value does
both is empirical. **A guessed number would look like calibration without being it.**

**Two source documents still need correcting** (same class as the timing phrase in §1 item 3): item
2.1 of the P2 plan says PF-2 spans a *"10× dataset range"* — it is **8×** (2000/250); and
`JUNIPER_2026-08-31_..._PERF-LANE-P1-DESIGN.md:45` plus P2 item 2.4 still carry *"no timing tolerance
of any kind"*. Fix them at source, or the next handoff re-inherits both.

**`util/ad-hoc/2026-08-20_wall_ordering_survey.py` cannot be used from a session worktree** — it
reports `UNRESOLVED` for every sibling-repo `base_config`. It fails visibly, so it is a nuisance, not
a hazard. See §7 trap 1.

---

## 5. Verification commands

```bash
git fetch origin && git rev-parse --short origin/main
gh pr list --head feat/perf-lane-owner-decisions-wave0-close --state all   # ml#1811: never-opened vs merged
python3 -m unittest -q tests/test_read_run_metrics.py tests/test_make_baseline.py tests/test_compare_baseline.py
python3 -m unittest -q tests/test_compare_baseline_defects.py tests/test_work_countable_contract.py \
  tests/test_termination_branch_precondition.py tests/test_run_suite_uncountable_report.py
python3 -m unittest -q tests.test_experiment_config_schemas
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest -q tests.test_experiment_config_schemas
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-04b \
  --suite ~/.local/state/juniper-experiments/suites/pf1-cascor-spiral-repeats-20260903T040803Z
```

| command | expected |
|---|---|
| three gate suites | **118 OK** (33 reader + 30 baseline + 55 comparator). **Not 91** — see below. |
| the four *other* gate suites | **46 OK.** These are CI-wired and were omitted from every prior handoff's verification block. |
| schema suite, CI mode | **OK, 4 skipped** — the cross-repo walk skips; siblings are not cloned |
| schema suite, FORCE_LOCAL | **Depends on `ml#1811`.** While `#1811` is UNMERGED it **passes** — two stalenesses cancel (main still exempts `xor-staged`, and the stale cascor checkout still shows the split, so neither test fires). **After `#1811` merges it FAILS** until the cascor primary is fast-forwarded, because the exemption is gone while the local file still splits. Neither state is a defect. See §6. |
| `compare_baseline` | `verdict: PASS`, `step_count baseline=1770.0 candidate=1770.0`, exit 0 |

**On the test counts.** The predecessor said 88; a draft of this document said 91 and reasoned "+3".
Both were wrong at write time: the real figure was **118**, and had been stable for ~38 hours. The
growth came from `ml#1740/#1742/#1776/#1778/#1783/#1796/#1798` — concurrent peer PRs on this exact
test surface that appear in **no** handoff's shipped table. **Do not derive a test count by adding a
delta to a predecessor's figure; run the command.**

**Stop condition.** If the comparator does not say PASS on the suite its own baseline was cut from,
the baseline or the reader has drifted — stop, do not proceed.

---

## 6. Retained state — DO NOT DELETE, and one live PEER process

Carried from the predecessor's §4 and **re-verified on disk 2026-09-07**:

- **Cascor pin worktree** `worktrees/juniper-cascor--exp--e-c-cap64--20260828-1922--67d7ea35`
  (detached at `67d7ea3`), with `~/.local/state/juniper-experiments/shadow-ec-cap64/juniper-cascor`
  symlinked to it — **both confirmed present**. The symlink is load-bearing and **fails silently**: a
  dangling one makes `_resolve_base_config` fall back to the primary's config, producing pinned code
  against primary config with nothing in the manifest revealing it.
- **`util/remove_stale_worktrees.bash` has NO staleness predicate.** From juniper-ml it enumerates
  every `.claude/worktrees/*` session checkout and removes each unconditionally. The predecessor said
  "10+ live"; **measured 2026-09-07 it is 93 session checkouts, and the loop's own
  `git worktree list | grep worktrees` matches 114 lines.** Do not run it unguarded.
- PF-1 run artifacts and `headroom-sweep-*` / `pf1-epoch-calibration-*` / `output-epochs-impact-*`
  suites under `~/.local/state/juniper-experiments/`.

**NEW 2026-09-07 — the juniper-cascor PRIMARY checkout is BEHIND and MUST NOT be pulled blindly.**
It was 2 commits behind at first draft and 3 an hour later — **measure it, never quote a count**:
`git -C <cascor> rev-list --count HEAD..origin/main`. A live cascor stack holds
`/home/pcalnon/Development/python/Juniper/juniper-cascor/src` on its `sys_path`: a **uvicorn listener
on port 8202** plus a **separate forkserver** process (both pids differ per session — verify the
condition, not a pid) — a peer session's isolated stack. `JuniperCascor1`'s editable finder maps cascor to
that primary tree, so fast-forwarding it swaps code under a running service. Phase 7 of the cleanup
procedure would normally say to pull it; **check for that process first**:

```bash
ps -eo pid,cmd --no-headers | grep -E "cascor" | grep -v grep | grep -v docker
```

**This staleness is why the FORCE_LOCAL row in §5 is conditional — it does NOT fail today.** Today it
passes, because `main` still exempts `xor-staged` *and* this checkout still shows the split, so
neither test fires. The failure arrives when **`ml#1811` merges while this checkout is still behind**:
the exemption goes, the local file still splits, and `test_no_unexempted_epoch_split` fires. The fix
then is to fast-forward this checkout — once the peer's stack is down — not to revert anything.

---

## 7. Traps this session paid for

1. **`experiment_stack.bash`'s targets dir resolves INSIDE the worktree, fails SILENTLY, and INVERTS
   the result.** `--help` prints `…/juniper-ml/.claude/worktrees/juniper-deploy/prometheus/targets`,
   which does not exist; Prometheus mounts the real `juniper-deploy/prometheus`. `DEPLOY_DIR` derives
   from `PROJECT_DIR`, and juniper-ml keeps worktrees *inside itself*. The bridge then writes where
   nothing reads, **every step still succeeds**, and the acceptance query returns zero series —
   reporting item 3.3 as FAILED when the plumbing is fine. **Always set
   `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`** and confirm the `Targets`
   line before launching.
2. **`/metrics` 307-redirects to `/metrics/`.** A naive `curl …/metrics | grep` reads **empty**,
   which looks exactly like a missing exporter. Prometheus follows redirects; use `curl -sL`.
3. **`git commit -m "…\`cmd\`…"` executes the backticks and DELETES the text**, exit 0. Hit once this
   session; the clause vanished from the message. **Use `-F FILE` for every non-trivial message.**
4. **`safe_merge.py` REFUSES with exit 0** when main outpaces CI ("went BEHIND 3 times"). Exit 0 is
   not evidence of a merge — look for the MERGED line. Its auto-merge net is **pinned to a SHA** and
   does not re-pin. GitHub's **native** auto-merge (`gh pr merge --squash --auto`) does track the PR:
   verified here across an `update-branch` **and** two later commits, all of which shipped.
5. **`$?` after a pipe reports the pipe's last command.** The title-scan gate looked like exit 0 and
   is exit 1.
6. **`pre-commit run <hook> --files docs/…` reports "(no files to check) Skipped"** — a vacuous pass.
   Hooks are scoped to `scripts/` and `tests/`; run `markdownlint`, `flake8`, `bandit` directly.
7. **`util/` is not black-formatted and is not gated.** `black --check` fails on
   `util/experiments/*.py` on `origin/main` too. Do not "fix" it inside an unrelated PR.
8. **A worktree-isolated session refuses compound shell** containing loops, heredocs or `jq` format
   strings. Split into plain commands rather than fighting it.

**Carried from the predecessor's §5 because they exist nowhere else** (consensus validation found a
draft of this document had dropped them while claiming to carry them):

9. **`gh pr view`'s `mergeable=UNKNOWN` is lazily computed.** `gh api repos/.../pulls/N` forces the
   real `mergeable_state`. Directly relevant to §1 item 1.
10. **`auto-merge net disarmed` does not reliably mean a check failed.** Twice it meant an unresolved
    CodeQL review thread: `mergeable_state=blocked` with every required context green. Neither
    `gh pr checks` nor `wait_for_checks` sees review threads — query `reviewThreads` via GraphQL.
11. **`git -C` reaches sibling repos but NOT juniper-ml's own shared checkout** from a worktree
    session. This is the trap most likely to bite §1 items 3–4, which both send you at juniper-cascor.
12. **Never assert a flag's absence by grepping source.** A test did
    `assertNotIn("--force", getsource(mb))` and failed on the docstring *saying* there is no `--force`.
13. **Never `except ImportError: return <empty>` for a sibling module** that ships in the same
    directory. It shipped item 1.4 silently doing nothing — blank columns plus "work invariant:
    BROKEN".
14. **A stable number can be a saturated instrument.** The tell that started this whole lane: `drive`
    was ~100× quieter than its own siblings (`plots` 8.40%, `start` 3.63%) on the same host.
15. **`include` cells do NOT inherit `matrix`** — a suite with `include` and no `matrix` also emits a
    bare base-config cell. Deliberate idiom in the p4 suites, not a defect.
16. **The juniper-ml CI test list is hand-maintained.** A new suite is not gated merely by existing —
    wire it into `.github/workflows/ci.yml` explicitly. (This is exactly how the four gate suites in
    §5 stayed out of every handoff's verification block while being CI-wired all along.)
17. **juniper-ml formats with black; juniper-recurrence with ruff. `flake8` checks neither.**

One predecessor trap is deliberately **not** carried: `ECOSYSTEM_ROOT = REPO_ROOT.parent` breaking
from a worktree is **obsolete** — it was fixed in code by `_find_ecosystem_root()`
(`tests/test_experiment_config_schemas.py:37-53`), whose docstring restates the trap. Omission is
correct there, not a loss.

---

## 8. CLI-experimentation arc tail — STILL OPEN, carried rather than dropped

The predecessor notes that an earlier draft dropped every one of these. Re-probed 2026-09-07 where
cheap. From §0/§0.1/§4 of
[`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md`](../../notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md):

- **The title-repair ACCEPTANCE GATE — work-destroying if dropped.** §5 of that document records
  that **163 of 172 broken titles were produced BY a repair pass**. Any further repair must be gated
  on `util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py --check`. **Re-probed 2026-09-07:
  still exit 1, 91 artifacts** (84 truncated, 41 unbalanced-bold, 8 field-label, 1 blockquote — these
  **overlap and are not a partition**: 42 of the 91 carry 2–3 classes, and 134 tag-instances − 91
  entries = 43 = 41×1 + 1×2; 91 visited by a repair pass, 0 never repaired). Owner must choose the
  extraction rule. Run it **unpiped** — `$?` after a pipe reports the pipe's last command and reads 0.
- **`JR-ML-OBS-003`** survives as its own item — a different class from the 172.
- **R-1's second clause** — cascor must not report `succeeded` when zero candidates were installable
  due to allocation failures. Owner: cascor.
- **F-P4-7** (why the noise-free spiral is harder), **E-C's 0.10/0.20 rows at cap 128**,
  **W-12/Q-7** (csv_import corpus), **F-P1-2** (Grafana render), **G-16's refusal half now
  untestable in `JuniperData`**.
- **The owner's standing rider on the withdrawn 0.5% threshold** — *"come back and verify after this
  gate goes live"* — is neither honoured nor retired. Speed is now structurally ungated, so it is
  arguably moot; **decide and record which.**

**Cross-repo — re-probed 2026-09-07 and WORSE than recorded.** juniper-recurrence pins
`juniper-data>=0.9.0,<0.12.0` at `juniper-recurrence/juniper-recurrence/pyproject.toml:95` and
`:104`. **juniper-data is now `0.13.0`** — the pin excludes two minors, and the data contract has
since moved to `generator_version 3.0.0` (the `*_full` retirement, `juniper-data#369`). So recurrence
cannot consume the current contract. `JuniperCascor1` still has `juniper-service-core` **0.5.0**,
below recurrence's `>=0.6.0` floor, so `tests/test_app_smoke.py::test_docs_require_auth_when_enabled`
fails locally and passes in CI.

---

## 9. What this handoff does NOT cover

Deliberate, so a dropped item stays distinguishable from an out-of-scope one: the backup/Duplicati
arc, the canopy E2E arc, the defect register, P5 fleet rollout, the soak arc, the partition/data
contract arc (`juniper-data#369` and its consumers), and juniper-service-core work. All have other
owners and moved independently during this session.

---

## 10. Consensus validation

Validated under
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).
Sized to the **top-right cell** of its §3 — a document of record, **overturning** two findings
already written into one, carrying **universal quantifiers**. Round 1: **3 Lane A on deliberately
disjoint entry points** (A1 git/GitHub only; A2 source/config only; A3 the live machine) and **2 Lane
B briefed to refute** (B1 correctness, told to *rescue* the findings this document overturns; B2
amputation + executability). Verdicts: A1 **FAIL**, A2 PASS w/ findings, A3 PASS w/ findings, B1
2-of-4 attacks partially succeed, B2 **not safe to archive**.

**The draft failed, and the failures were in the two classes this procedure exists to catch.**

| # | finding | lane | disposition |
|---|---|---|---|
| 1 | "91 OK" — actual **118**, stale ~38 h; grown by 7 peer PRs in no handoff's table | A1, A2, B2 | fixed; §5 now says run the command, never add a delta |
| 2 | Four CI-wired gate suites (**46 tests**) omitted from every prior verification block, incl. the one pinning §3.4's census | B2 | fixed |
| 3 | `PENDING_EPOCH_SPLIT_DECISIONS` "is now empty" — non-empty on `main`; empty only in unmerged `ml#1811` | A1 | fixed; scoped to `#1811` |
| 4 | §5 FORCE_LOCAL predicted FAIL; **passes** today — two stalenesses cancel | A1 | fixed; conditioned on `#1811` |
| 5 | Header claimed the predecessor's 12 traps were carried — true of **1** | B2 | fixed; 7 restored, predecessor un-superseded |
| 6 | **C3 carve-out amputated** — `_readout_mlp.py:77,150` maintains a real counter | B2 | fixed; §3.4 qualified |
| 7 | §3.1 "STRUCTURAL / permanently" over-claims; a **CI-cut baseline** was never examined; `thread_budget` is env, not hardware | B1 | fixed; ruling kept, justification narrowed |
| 8 | §3.3 premise false — `epochs_completed` **is** emergent (live: 100→52, 200→68) | B1 | fixed; unexamined exact-match gate surfaced as an owner question |
| 9 | "no timing tolerance" false — two `*_TIME_THRESHOLD_S` asserts; **inherited from P1 design §1** | A2, B2 | fixed here + flagged for source correction |
| 10 | "10+" worktrees → **93 / 114** | A3 | fixed |
| 11 | title sub-counts overlap, not a partition | A3 | fixed |
| 12 | cascor primary 2 → 3 behind | A1, A2, A3 | fixed; now a command, not a count |
| 13 | 10× → **8×** dataset range | A2 | fixed |
| 14 | PF-1 calibration caveat amputated (n=2, 26 % spread; 500/2000/5000 n=1) | B2 | carried into §4 |
| 15 | `baseline_20260526.json` gitignored, no history | A1 | recorded in §1 item 3 |

**Survived attack:** both refutations in §3.2. B1 could not rescue either, and *strengthened* C4 with
data this document had not cited — 6 real suites at ≥55 s, of which **3 straddle ratio 1**
(0.86, 0.87, 0.90, 1.01, 1.05, 1.25). It also could not locate any evidentiary basis for the original
C4 claim's "five suites out to 225.8 s". B1 did confirm the **mixed-normalization objection is real**
— §4 of the sweep note reports the same quiet pair as −11.5% under a directional convention — but
orthogonal: 15.0 % is tied to *which run* (loaded), not to which formula.

**Failure of this procedure, recorded per its §6.** Mid-audit I switched the shared worktree's branch,
mutating the ground truth two lanes were reading. A2 caught it via `git reflog` and flagged it. That
is why A1 and A2 report opposite FORCE_LOCAL results — both correct for the state they saw. **Run
consensus lanes against a frozen tree, or a disagreement becomes an artifact of the auditor.**

### 10.2 Round 2 — run on the corrections, and it found one

Briefed only on the 15 fixes ("find what they broke"), not on the document. It verified 12 of 15
byte-for-byte against live code, live tests and the live `ml#1811` diff, and found:

- **HIGH — the fix pass created a self-contradiction.** Corrected §5 said FORCE_LOCAL *passes* today;
  §6's closing line, untouched, still said *"this is why the FORCE_LOCAL row in §5 fails today"*.
  Round 2 ran it (**OK, 12 tests**) and proved §5 right and §6 stale. **Exactly the class round 2
  exists for**, and invisible to anyone reviewing the document as a whole. Fixed.
- **MEDIUM — a corrected citation was itself wrong.** `thread_budget` does not come from
  `make_baseline.py:128,137`; those read a manifest field. The `os.environ.get()` loop is
  `run_experiment.py:1448`, vars at `:225`. Conclusion unchanged, citation fixed.
- **MEDIUM — correction 13 fixed 8× here but left "10×" live in P2 plan item 2.1**, the document this
  handoff calls canonical. Now flagged in §4 alongside the timing phrase.
- **LOW — "100 → 52" did not reproduce** (round 2 got 68 for both 100 and 200). Thesis unaffected —
  two budgets landing on one point proves emergence — figures re-stated as host-sensitive.
- **INFO — 7 restored traps verified 1:1** against the predecessor with no garbling; two more
  (hand-maintained CI list, ruff/black) since added as §7 items 16–17; the `ECOSYSTEM_ROOT` trap
  confirmed **obsolete in code**, so its omission is correct.

**Termination.** Round 2 changed one action-relevant claim (Finding 1) and two citations. A round 3
was not run: the remaining findings are disclosure-only, and the procedure's stop rule is "no finding
that changes a number, a disposition, or an action" — Findings 4–5 change none.

**Residual uncertainty, stated per §5.4.** Sample size for the `epochs_completed` counterexample is
n=1 host, two budgets, and its exact values did not reproduce between rounds. The `cpu_model`
question left open in §3.1 (whether hosted-runner CPU models are stable enough for a CI-cut baseline)
is **unmeasured** — neither lane could settle it from GitHub's published specs.
