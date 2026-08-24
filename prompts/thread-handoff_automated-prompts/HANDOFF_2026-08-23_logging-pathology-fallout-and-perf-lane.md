# HANDOFF 2026-08-23 — after the logging pathology: three unmerged fixes, a new perf target, and a tabled redesign

Successor to
[`HANDOFF_2026-08-18_seed-reproducibility-and-residual-wall-gap.md`](HANDOFF_2026-08-18_seed-reproducibility-and-residual-wall-gap.md).

That handoff's §3 (seeded-run reproducibility) and §4 (residual wall gap) are both **CLOSED**. The
investigation ended somewhere neither section anticipated: the wall gap was a *symptom* of a logging
defect costing ~78% of candidate-worker CPU on **both** entry points. Fixing it made training **~9×
faster on both arms** and removed the per-epoch throughput penalty.

**Read that precisely.** The *rate* term closed (1.415 → 1.065, interval includes 1.0). The **span**
ratio did **not** improve (1.735 → 1.817), and the residual candidate-phase ratio (1.308) is the
*work* term — cascor#532, untouched. "The gap closed" is too strong; see §4.3.

Throughout, "§N" means a section of **this** document. Commands run from the juniper-ml repo root.

---

## 1. What is settled — do not re-measure

| finding                                                                                                                                                   | evidence                  | status                                     |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|--------------------------------------------|
| Seeded runs: **service 0/190 pairs, direct CLI 0.768** [0.553, 0.847] at N=20                                                                             | ml#1205                   | **CLOSED** — path-specific                 |
| Cause of CLI nondeterminism: the two entry points run `fit()` on **different threads**                                                                    | reproducibility note §3.9 | identified, **mitigation unmerged** (§3.2) |
| Wall gap **decomposition** `work × rate` reproduces the measured phase ratio to 0.002 at caps 4/16/64 (this is the *decomposition* residual, NOT the gap) | ml#1278                   | **CLOSED**                                 |
| Root cause of the **rate** term: `inspect.getmodule` scanning `sys.modules` per log record                                                                | ml#1278 §4.4              | **FIXED** — cascor#563                     |
| Forkserver architecture **is** in use (`cascor_constants/constants_model/constants_model.py:54`; pool at `cascade_correlation.py:3772`)                   | evidence note §4.4a       | verified                                   |

### 1.1 Numbers that were CORRECTED — do not resurrect them

Three single-run attributions failed under replication. All are corrected in place; if you find a
document still quoting the old value, it was missed.

| superseded claim                        | replicated value                                           |
|-----------------------------------------|------------------------------------------------------------|
| #531: "the `OMP=2` cap costs **1.30×**" | **1.016×** [0.885, 1.148] at k=3 — no effect               |
| "the residual is **~1.17×**" (cap 16)   | **1.706×** at k=4                                          |
| "#533 removed 1.30× of the gap"         | cap-64 1.924 ± 0.486 vs pre-#533 1.99 ± 0.21 — overlapping |

**#533 is still correct engineering** (one BLAS policy, both entry points). Only its *performance*
justification failed.

### 1.2 Every published ratio is now PRE-F1 and historical

The cap series (span 1.459 / 1.735 / 1.924 at caps 4/16/64) was measured before cascor#563. Post-F1
at cap 16, k=4: rate ratio **1.065** [0.869, 1.262] — the per-epoch penalty is no longer
demonstrable. **Do not quote the pre-F1 series as current.**

### 1.3 The documents this handoff is shorthand for

Everything below cites these by short name. Read them before acting; they carry the risk tables and
mitigations this summary strips.

| shorthand                                           | path (all in juniper-ml `notes/`)                                                                        |
|-----------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| "reproducibility note"                              | `JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md`              |
| "evidence note" / "residual note"                   | `JUNIPER_2026-08-21_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-RESIDUAL-WALL-GAP-EVIDENCE.md`                 |
| "fix design" — defines **F1/F2/F3**                 | `JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md`                     |
| "perf-lane register" — defines **G1/G1a/G1b/G2–G5** | `JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`                      |
| "the §12 perf lane"                                 | `JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` §12 |
| "the P3 rollup"                                     | `JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md`                       |

**Repos**: `main.py`, `cascade_correlation.py`, `candidate_unit.py`, `logger.py`, `constants*.py` are
**juniper-cascor** (`src/…`). `run_experiment.py`, `experiment_stack.bash`, `util/ad-hoc/*` and all
`notes/` are **juniper-ml**.

### 1.4 Eliminated at runtime — do NOT re-check

Each was a live hypothesis, tested and killed. They are cheap to re-propose and expensive to re-test.

| eliminated                                                                                                                                                   | evidence                                       |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| **Thread context is not the wall mechanism** — moving `fit()` to a pool thread changed span by 0.7% (280.8 → 282.9 s) against a service arm at 192.5 s       | residual note §4.1                             |
| **Pool packing is not it** — LPT imbalance ratio **1.012×**; both arms pack equally badly                                                                    | residual note §4.3                             |
| **The pool is created ONCE** for 16 rounds, not re-forked per iteration (7 processes, both arms)                                                             | residual note §4.3                             |
| **cProfile is the wrong instrument** — it *destroys* the effect (per-call 0.944; the 9.2 ms/epoch gap becomes 1.9 ms under profiling). Use `py-spy --native` | residual note §4.3b                            |
| **BLAS thread count is not the driver** — `threads=1` does not fix determinism; `OMP=2` costs 1.016×                                                         | reproducibility note §3.8, residual note §4.3a |

---

## 2. Merged this arc

| PR             | merged     | what                                                                       |
|----------------|------------|----------------------------------------------------------------------------|
| **ml#1205**    | 2026-08-21 | N=20 determinism instrument + evidence (§3 of the predecessor)             |
| **ml#1278**    | 2026-08-23 | Residual wall-gap campaign, root cause, tooling, corrections               |
| **cascor#563** | 2026-08-23 | **F1** — logger resolves the caller from `f_back`, ~20,700× per resolution |

F1's effect, cap 16 k=4 paired: service span **827 s → 89 s**, CLI **1434 s → 162 s** (~9× both).

**Verify before trusting this table** — it was drafted before the merges completed:
`gh pr view 563 --repo pcalnon/juniper-cascor --json state,mergedAt`.

### 2.1 Verification NOT performed — do this before relying on F1

The fix design's verification plan has four rows. Two were executed (the paired campaign and the
per-epoch ratio, both in §2 above). **Two were not:**

1. **Determinism unchanged.** F1 changes what is computed per log record, not the arithmetic, so the
   divergence rate MUST be unchanged — service 0/190, CLI not worse. **This was never run.** The fix
   design calls it "the row most easily forgotten"; it was forgotten. Run
   `util/ad-hoc/2026-08-20_determinism_campaign.bash` against post-F1 cascor before any
   reproducibility claim rests on the current build.
2. **Post-fix worker profile** — `inspect` frames should fall from ~78% of self time to negligible.
   Not run. Tooling: `util/ad-hoc/2026-08-23_pyspy_conda_shim.bash` + `_h2h_native_profile_diff.py`.

---

## 3. UNMERGED WORK — three real fixes exist only as patches

**This is the most perishable item in this handoff.** Four cascor patches live in
`util/ad-hoc/*.patch` (on juniper-ml `main`); the working state they came from has been **rescued
onto branches** — see §6 — but none is a PR.

**All four applied cleanly to cascor `main` as of 2026-08-23** (`git apply --check`). cascor#563 has
landed since, so **re-check before relying on that**.

**Landing recipe, common to all three fixes below:**

1. `git -C juniper-cascor worktree add -b fix/<name> <path> origin/main`
2. `git apply` the patch, then **hand-delete the diagnostics** (they are not separate hunks — see
   each item)
3. `pre-commit run --files <changed>` — cascor gates on Black across 3.12/3.13/3.14 and it **failed
   cascor#563 on first push**; run it locally
4. add the named guard test, and **prove the guard fails** by reverting the fix (this arc shipped a
   vacuous check once)
5. `util/safe_merge.py --pr N --repo juniper-cascor --merge-method squash --execute`

### 3.1 Candidate-seed derivation (verified, no PR)

`cascade_correlation.py` draws `candidate_seeds` from the **process-global `random` stream**, so
seeds are a function of how many times anything has drawn from it — not of the configured seed.
Measured: the CLI's round-0 seed list begins at the **service's 4th element** and stays 3 draws
offset, so the two paths train *different candidates* on identical config with `network_seed=42`.

Fix: a network-owned `random.Random(self.random_seed)`. **Verified** — both arms then log exactly
`random.Random(42)`'s draws.

- **Patch**: `util/ad-hoc/2026-08-23_cascor_seedfix_and_worker_diag.patch`
- **Rescue branch**: cascor `rescue/candidate-seed-derivation-wip` (was uncommitted on a detached
  HEAD until 2026-08-23)
- **The diagnostics are NOT a separate hunk.** Inside hunk 1, immediately after the fix, sits a
  `DIAG: candidate_seeds=…` INFO log — hand-delete it. Hunk 2 is a different thing entirely: it
  renames `train_candidate_worker` → `_train_candidate_worker_impl` and adds a
  `JUNIPER_CASCOR_WORKER_PROFILE` dispatcher.
- **Ruling on that dispatcher**: it is the **only** way to profile forked candidate workers
  (`main.py --profile` instruments the parent; the service has no equivalent), it is a no-op when
  the env var is unset, and §4.3/§4.4 both need it. **Land it as tooling in its own PR** — do not
  discard it as "diagnostics".
- **Guard test to write**: round-*k* seeds are a function of `(random_seed, k)` and are unmoved by
  intervening global `random.random()` calls. That is exactly the regression that would otherwise
  return silently.

### 3.2 Thread-context mitigation (verified, no PR)

Running `fit()` on a `ThreadPoolExecutor` worker — mirroring the service — cuts the CLI divergence
rate **0.768 → 0.337** at N=20, at **no wall-clock cost**. Patch:
`util/ad-hoc/2026-08-20_cascor_thread_context_diag.patch`.

**Do not merge as-is.** It is symptom-shaped (an executor in `main.py`), and the residual 0.337 is
not understood. Decide the shape before landing.

### 3.3 Observability: `_add_best_candidate` logs a memory address

`_add_best_candidate` interpolates a `CandidateUnit` with no `__repr__` (search the message text
`"Adding best candidate"`; it was `:4850` at `4bec1be` and moved to ~`:4864` after #555 — this
handoff's own §5 rule 5 says not to trust that number), so the installed
unit's identity — the one fact separating a selection flip from arithmetic jitter — is
unrecoverable from any shipped log. This campaign needed a patched build to get it. Patch:
`util/ad-hoc/2026-08-20_cascor_candidate_identity_diag.patch`. Tracked as perf-lane **G1b**.

> A **fourth** patch, `2026-08-21_cascor_seeds_and_balance_diag.patch`, overlaps this one (same two
> hunks plus a `candidate_seeds` log). Rescue branch: `rescue/seeds-and-balance-diag-wip`. Prefer the
> narrower `_candidate_identity_diag` patch for G1b; the other is superseded.

**G1b blocks G1a** (§4.5): without the installed unit's identity you cannot tell a selection flip
from arithmetic jitter, which is the first question the residual 0.337 asks. **Do G1b first.**

---

## 4. OPEN WORK

**Order is not arbitrary. Work it in this sequence:**

| # | item                                     | why here                                                                                             | gate                        |
|---|------------------------------------------|------------------------------------------------------------------------------------------------------|-----------------------------|
| 1 | **§2.1 determinism-unchanged check**     | F1 is merged and this was never run; everything downstream assumes the current build is reproducible | none — do it first          |
| 2 | **§3.3 → §3.1 → §3.2** (the three fixes) | perishable; §3.3 (G1b) unblocks §4.5                                                                 | none                        |
| 3 | **§4.4 forkserver isolation**            | **gates §4.1 AND §4.2** — see below                                                                  | none                        |
| 4 | **§4.2 F3 preload**                      | its ~12.8 s estimate is unsound until §4.4 resolves                                                  | **fork-safety audit**       |
| 5 | **§4.1 F2 import hygiene**               | may become unnecessary if §4.4's leak is closed                                                      | after §4.4                  |
| 6 | **§4.3 fixed overhead**                  | needs an instrument built first                                                                      | none, but no tooling exists |
| 7 | §4.5 G1a, §4.6, §4.7, §4.8               | independent                                                                                          | §4.5 needs §3.3             |
| — | **§4.9 logging redesign**                | owner-raised, its own document                                                                       | owner decides timing        |

**§4.4 gates §4.1 and §4.2, and that is not obvious from reading them in order.** §4.2's headline
"~12.8 s per pool creation" assumes workers get the forkserver's table — §4.4 measured that they do
**not**. If §4.4's leak is closed, §4.2 must be re-sized and §4.1 may be moot.

**Nothing here is issue-tracked.** No cascor issue exists for F2, F3, the fixed-overhead target, the
latent seeding defect, or the logging redesign. **Filing them is part of item 1** — otherwise this
document is the sole carrier for the entire open surface.

### 4.1 F2 — CLI import hygiene (**demoted**, still worth doing)

`import main` pulls **1,867** modules including **`fastapi` and `pydantic`**; `import api.app`
pulls 1,416. The direct CLI never serves HTTP.

**F1 removed its performance motivation** — the 1.327× table ratio only mattered because every log
record scanned it. Remaining value: import time, worker memory, and not shipping a web stack into a
trainer.

**The import edge is NOT traced.** That is F2's first task: `python -X importtime`, or bisect
`sys.modules` against a trimmed import.

### 4.2 F3 — forkserver preload set (**blocked on an audit**)

Current: `["os", "uuid", "torch", "numpy", "random", "logging", "datetime"]`.

| entry                                | +modules |      import | verdict                                   |
|--------------------------------------|---------:|------------:|-------------------------------------------|
| `torch`                              |      886 |     2.938 s | keep                                      |
| `numpy`                              |      109 |     0.153 s | keep                                      |
| `os`                                 |    **0** |     0.000 s | pure no-op                                |
| `uuid`/`random`/`logging`/`datetime` | 19 total |     0.021 s | harmless                                  |
| **missing `cascade_correlation`**    |  **242** | **1.822 s** | **~12.8 s per pool creation** (7 workers) |

**BLOCKER**: preloading runs import-time side effects *in the forkserver*, inherited by every worker
across the fork. Logger handles or descriptors opened at import become shared — classic fork-safety
hazard. **The audit is not done and F3 must not land before it is.**

Also in F3's scope: `cascade_correlation.py:1061-1062` still carries a commented-out
`mp.get_context("forkserver")` above a garbled note reading *"…did not corrUse 'fork' context for
better compatibility with BaseManager on Linux"*. The code uses forkserver; the comment says
otherwise and actively misleads.

### 4.3 NEW — per-run fixed overhead is now the dominant cost

**This target did not exist before F1 and nobody has looked at it.**

Before F1 the candidate phase was **98%** of the service's cap-16 span (890 s of 908 s). After F1 it
is **66%** (41 s of 62 s). Startup, dataset fetch, output passes and teardown were invisible under a
cost 20× larger; they now set the wall.

Consequence: the **span ratio did not improve** (1.735 → 1.817) even though training got 9× faster.
That ratio is now measuring fixed overhead, not throughput — **do not compare it to the pre-F1
number**.

**No instrument exists.** `util/ad-hoc/2026-08-16_h2h_phase_split.py` splits candidate vs output
only; it cannot decompose startup / dataset fetch / teardown. (It *was* repaired to anchor on
message text, so it works — it just does not answer this.) First task is building the decomposition,
not measuring. Tracked as perf-lane **G4**.

### 4.4 Forkserver isolation is not delivered

Workers measured at **1,871** (CLI) / **1,410** (service) modules — within a handful of their
*launchers*, far above a clean forkserver table (1,091 preload, 1,333 with the trainer). The route
by which the launcher's import graph reaches the workers is **not traced**. If it is closed, F2 may
become unnecessary.

### 4.5 G1a — residual determinism 0.337

After the §3.2 mitigation the CLI still diverges in 0.337 of pairs [0.100, 0.505]. It survives
entirely in the **final candidate round** (which has no `grow_network` line, so the iteration trace
reads 0.000) and is worth **0.5 pp** of validation accuracy. Only visible on the correlation
fingerprint.

Structure to resume from: the 20 runs split **16 / 4** — group A at val 0.6350 / 10,960 candidate
epochs, group B at val 0.6400 / 10,950 — giving 1 distinct trace outcome and 2 distinct correlation
outcomes (reproducibility note §4.4). **Blocked on §3.3 (G1b)**: without the installed candidate's
identity you cannot distinguish a selection flip from arithmetic jitter.

### 4.6 Latent seeding defect (inert today)

`CandidateUnit._initialize_randomness` seeds numpy, *then* draws its roll count from the **stdlib
`random`** stream (`candidate_unit.py:317` → `:364`) — which has not been seeded for that candidate
yet (`random.seed` is the *next* call, `:319`). numpy's stream position therefore depends on
leftover interpreter state. Inert only because nothing in candidate training draws from
`np.random`; the torch stream that seeds the weights is rolled *after* `random.seed`.

### 4.7 Perf-lane consequence — CLI and service CANNOT share a baseline

`run_experiment.py` drives training **entirely via the service REST API** and never invokes
`main.py`, so every suite and PF suite runs the service tier. But §12 contemplates
`python main.py --profile --profile-output "$RUN_DIR/profiles"` — the **direct CLI**.

Post-F1 the per-epoch penalty is gone, but the **span** ratio (1.817) is not, because fixed overhead
differs. A P3 threshold calibrated on one tier and applied to the other is still wrong. **Either the
lane measures one tier, or it keeps two baselines.** This has not reached the §12 design.

### 4.8 Deferred, do not let them die silently

- **Re-measure the cap series post-F1** — everything published is pre-F1 (§1.2). Now cheap: runs are
  ~9× shorter.
- **Timing noise floor** — deliberately not published (contention); now affordable on a quiet host.
- **3-seed spread at cap 128** — still NOT MEASURED.
- **cascor#530** — `TrainingParams` has no seed field; the service network seed is unconditionally
  42. Its body flags a follow-on: `_CANDIDATE_UNIT_RANDOM_SEED` (`constants.py:1046`) must reach the
  candidate pool too.
- **Retrospective corpus re-validation** — most E-A/E-I/P4 results are single-run and the P3 rollup
  grades Reproducibility "PASS — bit-identical". Raise with the owner; **do not absorb it**.

### 4.9 TABLED — logging redesign (owner-raised, its own analysis)

The owner has asked for an analysis of: a clean stream to stdout/stderr, richer sinks (formatted and
colourised file output), **per-logger** levels settable via config file *and* environment variable,
and possibly streaming into an ELK/Kibana-style backend.

**Deliberately not folded into F1.** F1 is a hot-path bug fix any redesign would have to make
anyway; equally the redesign must not be justified by F1's number, since F1 already banks it. This
wants its own design document.

Worth carrying in: the logger currently `open()`s the log file **per record**
(`logger.py` `_log_at_level`), and `print()`s to stdout unconditionally.

---

## 5. Methodology this arc earned — apply it

1. **No small sample supports a mechanism claim.** Three published attributions died under
   replication (§1.1), and *two of my own* predictions died the same way — the near-tie hypothesis
   and the thread-count hypothesis, the latter revived from 8 runs split 4/4.
2. **An n=6 screen can read as a clean zero.** The thread-context mitigation showed **0/15** at n=6
   and **0.337** at N=20.
3. **Carry two fingerprints.** A cap-4 run trains 32 candidates but logs 3 iterations; its final
   candidate round is invisible to the trace. Trace-only rates read 0.632 where correlations read
   0.768.
4. **Interleave arms; never run them in blocks.** A constant load cancels in a ratio; a load that
   drifts across a block boundary biases one arm irrecoverably.
5. **Anchor log parsing on message TEXT, never `file.py: func:LINE`.** `phase_split.py` silently
   parsed nothing after #539 shifted `cascade_correlation.py` by ~90 lines.
6. **Verify a guard by making it fail.** The F1 regression guard was proved by re-introducing
   `getouterframes`; an untested guard is a vacuous check, and this arc shipped one (a localiser
   comparing `uuid4()`s fired on 100% of pairs including identical ones).

---

## 6. Operational notes

- `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing from a
  worktree; `JUNIPER_EXP_HEALTH_TIMEOUT=180` (default 90 is too short for a cold start).
- **`JUNIPER_EXP_CONDA_DIR`** points the launcher at a shim conda tree — how the service was
  profiled. `ptrace_scope=1` means py-spy must be an **ancestor**; attaching to a running
  non-descendant is denied and there is no passwordless sudo.
- py-spy `--native` **cannot** be combined with `--nonblocking`.
- A cap-64 CLI leg wrote a **637 MB** trainer log; the experiment state dir holds **38 GB**. This
  constrains `k` independently of wall-clock.
- Always `util/experiment_stack.bash --down <RUN_ID>`; a live run holds one port from each of the
  three 30-slot ranges plus lockdirs.
- **Worktrees — READ BEFORE REMOVING ANY.** An earlier draft of this handoff listed all of these as
  "safe to clean up"; two held uncommitted work on **detached HEADs**, where removal destroys it and
  `git worktree prune` orphans any rescue commit. Both have since been committed to branches.

  | worktree (under `Juniper/worktrees/`)                                              | state                                                          | action                                             |
  |------------------------------------------------------------------------------------|----------------------------------------------------------------|----------------------------------------------------|
  | `juniper-cascor--fix--logger-frame-resolution--20260823-1200--acf953b3`            | branch, **merged** (cascor#563)                                | safe to remove                                     |
  | `juniper-cascor--fix--candidate-seed-derivation--20260823--362b88b1`               | branch `rescue/candidate-seed-derivation-wip` — **holds §3.1** | keep until §3.1 is a PR                            |
  | `juniper-cascor--diag--seeds-and-balance--20260821-2115--362b88b1`                 | branch `rescue/seeds-and-balance-diag-wip`                     | safe once §3.3 lands                               |
  | `juniper-cascor--exp--residual-wall-gap--20260821-0800--362b88b1`                  | detached, clean                                                | safe to remove                                     |
  | shim farms `~/.local/state/juniper-experiments/{diag-project-20260821,pyspy-shim}` | generated                                                      | regenerate from `2026-08-23_pyspy_conda_shim.bash` |

- **Do NOT sweep `~/.local/state/juniper-experiments/` on size alone.** The 43 GB is mostly this
  arc's raw evidence, and §4.8's post-F1 re-measure needs the pre-F1 runs to compare against:
  `determinism-n20`, `h2h-paired-e-k-thread-probe-cap16`, `h2h-paired-e-m-h2h-paired-cap64`,
  `h2h-thread-sweep`, `f1-paired-cap16`, `profile-cap4`, `pyspy-out`.
- To find a stack to tear down: `util/experiment_stack.bash --status` lists every run;
  `--down --all-mine` closes yours. **Concurrent sessions share these port ranges** — a non-zero
  lockdir count is not necessarily yours.

### 6.1 Tooling built this arc (all merged, on `main`)

**Determinism:** `2026-08-20_determinism_nrun.py` (rate + bootstrap CI + dual fingerprint;
`--dir-arm` / `--suite-arm`) · `_localize.py` · `_diag.py` · `_campaign.bash` · `_arm.bash` ·
`_report.bash` · `_watch.bash` / `_await.bash`.

**Wall gap:** `2026-08-21_h2h_paired_campaign.bash` (interleaved, SHA + `config_sha256` guards) ·
`_paired_ratio.py` (ratio-of-pairs + required-k) · `_h2h_pool_balance.py` (LPT critical path) ·
`_thread_sweep.bash` + `2026-08-22_h2h_sweep_ratios.py` · `2026-08-21_detach_campaign.bash`.

**Profiling:** `2026-08-23_pyspy_conda_shim.bash` · `_pyspy_cli_leg.bash` ·
`_h2h_native_profile_diff.py` · `_h2h_worker_profile_diff.py`.

**Suites:** `e-m-h2h-paired-cap64.yaml`, `e-n-profile-cap4.yaml`; `e-l-determinism-cap4.yaml`
expanded to 20 replicates.

---

## 7. Git state (re-derive; concurrent sessions push often)

- `juniper-ml` — arc branch `exp/residual-wall-gap-post533` → **ml#1278**.
- `juniper-cascor` — `fix/logger-frame-resolution` → **cascor#563**.
- Authored from session worktree `.claude/worktrees/silly-weaving-hopcroft`.
- Open issues owned by this arc: **cascor#532** (updated: title, body, and a findings comment).

## 8. Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main   # non-empty is EXPECTED here: the arc
                                                           # branch squash-merged. Re-branch off main.
gh pr list --repo pcalnon/juniper-ml --state open
gh pr list --repo pcalnon/juniper-cascor --state open
gh issue view 532 --repo pcalnon/juniper-cascor --json number,title,state,comments
# NB: bare `gh issue view 532` and `--comments` fail with a projectCards GraphQL
#     deprecation on this gh build. Use --json.

python3 -m unittest tests/test_experiment_suite_yamls.py        # 23 as of this handoff
util/reap_pytest_orphans.bash --dry-run                          # forkserver orphans outlive runs
ss -ltn | awk 'NR>1{split($4,a,":"); p=a[length(a)]+0; if ((p>=8110&&p<=8139)||(p>=8230&&p<=8259)||(p>=8260&&p<=8289)) print p}'   # all THREE ranges
ls -1 /run/user/1000/juniper-experiments   # non-zero may be a CONCURRENT session, not a leak;
                                           # confirm with: util/experiment_stack.bash --status
```
