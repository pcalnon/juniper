# HANDOFF 2026-08-25 — the perf lane's open surface, after attribution, the shutdown tax, and the `__main__` re-import

Successor to
[`HANDOFF_2026-08-24_determinism-zero-and-perf-lane-open-surface.md`](HANDOFF_2026-08-24_determinism-zero-and-perf-lane-open-surface.md).
That handoff's §4 work order is **analysis-closed through item 9** (§4.1, §4.11, §4.2 leads,
§4.12, §4.3, §4.5, §4.6-gate, §4.7) — except item 2 (§4.10, the post-#563 worker profile), which
was **ticketed as cascor#579, not run** — and item 10 (§4.4) has its instrument and first
measurement. As GitHub work, item 7 (cascor#570) stays OPEN until §3.1's census lands; item 9
(cascor#568) is CLOSED by #588. Its §3
hazards and §4.8 deferred list are **inherited by reference** (§5 below) — do not treat them as
retired because they are not restated at length.

Throughout, "§N" means a section of **this** document; "pred. §N" means the predecessor. Commands
run from the juniper-ml repo root unless stated.

---

## 1. What is settled — do not re-measure

| finding | evidence | status |
| --- | --- | --- |
| **CLI determinism closure is attributed to cascor#563**, bracketed to ONE commit (#562 diverges 0.847/0.932; #563 and #565 read 0/190, N=20 each) | [evidence note](../../notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-POST-ARC-DETERMINISM-EVIDENCE.md) §3; cascor#532 closing comment | **CLOSED** (cascor#532) |
| Mechanism: a **time-coupled parent-side consumer of the global `random` stream** — at #562 the round-1+ seed lists are shifted windows of one sequence, shift ↔ round-0 wait-loop polls r = 0.931; #563's speedup pins the count | evidence note §3.5 | measured; the exact consumer is deliberately untraced (dead regime, decoupled surface) |
| **#566 is the structural guarantee**, not the closer — it removes the candidate-seed reader of the global stream. The corollary "a slow cell on a pre-#566 build would re-diverge" is **inferred** from three time points (69 s/0.768 · 85 s/0.932 · 4 s/0.000) plus a code reading — **no slow cell was ever run at #563–#565 or post-#566** | evidence note §0 item 4, §3.5 | mechanism measured; the counterfactual is **untested** — falsifier is the cap-64/128 N≥10 check in pred. §4.8. Cite as "#566 removes the reader", never "#566 closed the gap" |
| Thread-context mitigation (`util/ad-hoc/2026-08-20_cascor_thread_context_diag.patch`) | evidence note §3.6 | **DROPPED**, never merged; artifact of record stays on `main` |
| Forkserver **route traced** (cascor#570): the forkserver is clean (1,093 modules); every CHILD re-imports the launcher's `__main__` via CPython spawn-preparation, re-running `main.py`'s body — incl. the module-scope **Sentry init in every worker** | [#570 comment](https://github.com/pcalnon/juniper-cascor/issues/570#issuecomment-5408936691); branch `diag/forkserver-import-audit` | measured; "start the forkserver earlier" is **dead** |
| **G4 instrument shipped**; cap-16 overhead is ONE defect, not diffuse startup | `util/ad-hoc/2026-08-25_g4_overhead_decomposition.py`; [#571 comment](https://github.com/pcalnon/juniper-cascor/issues/571#issuecomment-5409644938) | first measurement in; re-measure owed (§3.1) |
| **cascor#586** — 7/7 CLI workers failed the graceful stop at cap 16, ~35 s/run serial teardown inside `fit()` (0/7 at cap 4, 0/7 service; the instrument reads it as `train_other` 37±1 s = 7 × 5 s joins + ~2 s of real post-round work). Cause: workers hang at interpreter exit on the advisory-queue **feeder flush**; fix = `cancel_join_thread` on progress/instrumentation queues + parent-side drain + a **shared** join deadline | cascor#587 **MERGED** (`76f4d51b`) | **FIXED** in code; live re-measure owed (§3.1) |
| The 1.817 span ratio does **not** reproduce on the current build: nrun-anchored **1.32** (≈ all #586), whole-process **1.09** — the service now spends MORE in candidate and output than the CLI | #571 comment | pre-F1 series remains historical (pred. §1.5) |
| Work term post-#566: cli/svc **0.861** at cap 4, **0.876** at cap 16 (was 1.230 at cap 16 pre-#566); both arms work-deterministic (epochs sd 0) | evidence note §5; #571 comment | reconciled — the "1.308" was the candidate-*phase* ratio, never a work value |
| Ad-hoc scripts are **RETAINED** (owner decision 2026-08-25): no retirement deadlines; `Retire when:` lines read `RETAINED (…) Previously: <condition>` | ml#1356 MERGED (`e91e2dae`); `util/ad-hoc/README.md` Lifecycle | policy — never delete an ad-hoc script as routine cleanup |

### 1.1 Documents this handoff is shorthand for

| shorthand | path (juniper-ml `notes/` unless stated) |
| --- | --- |
| "evidence note" | `JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-POST-ARC-DETERMINISM-EVIDENCE.md` |
| "register" (G1–G6) | `JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md` §2 — **G1/G1a CLOSED, G1b SHIPPED, G2 annotated, G4 measured, G6 = cascor#570** |
| "residual note" | `JUNIPER_2026-08-21_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-RESIDUAL-WALL-GAP-EVIDENCE.md` |
| "fix design" | `JUNIPER_2026-08-23_JUNIPER-CASCOR_CANDIDATE-WORKER-LOGGING-PATHOLOGY-FIX-DESIGN.md` |
| "the §12 perf lane" | `JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` §12 |

Terms (arm, cap-N, trace vs correlation fingerprint, `span = work × rate`): pred. §1.8, unchanged.

---

## 2. Merged / filed this arc (verify — concurrent sessions merge constantly)

| item | what | state |
| --- | --- | --- |
| **ml#1349** (`a6f478df`) | evidence note + register overhaul + G4 instrument + `2026-08-24_seedvar_{analysis.py,probe_driver.bash}` | MERGED |
| **ml#1356** (`e91e2dae`) | ad-hoc retention policy — 101 files: 99 script-header rewrites + `util/ad-hoc/README.md` + `2026-08-25_retire_line_sweep.py` | MERGED |
| **cascor#587** (`76f4d51b`) | the #586 fix: `_release_advisory_queues`, `_drain_progress_queue`, shared-deadline `_terminate_workers`, 6 tests (5 proven guards) | MERGED — closes #586 |
| **cascor#588** | the #568 fix: `main.py` gated on `__name__ != "__mp_main__"` (SpiralProblem import, `load_dotenv`, Sentry block); lazy `CascadeCorrelationPlotter` at the constructor; `src/tests/unit/test_import_hygiene_568.py` (2 subprocess guards proven failing pre-fix + 1 declared non-guard). Measured `__mp_main__` exec 1,867 → **1,142** modules; `import cascade_correlation` 1,334 → **1,155**; no heavy packages, **no Sentry in workers**. **First CI run went RED** (F821: a fourth plotter use site, the static `plot_dataset` delegate, missed by a truncated grep — see §4.6) and was corrected in `54c23b0` | **MERGED** (`d2d10697`, second CI run GREEN 23/23) — #568 CLOSED; #569 unblocked |
| cascor#532 | closed with the full attribution comment | CLOSED |
| cascor#578 / #579 / #582 / #586 | filed (baseline-tier decision; post-#563 worker profile; test→val promotion parity; shutdown tax) | #586 CLOSED by #587; rest OPEN |

```bash
gh pr view 588 --repo pcalnon/juniper-cascor --json state,mergedAt        # MERGED 2026-08-25T22:56Z
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor log --oneline -3 origin/main   # d2d10697 = #588, 76f4d51b = #587
```

---

## 3. OPEN WORK — ordered

**Work it in this sequence.** Item 1 is the arc's outstanding *verification*; without it #587 and
#588 are merged code-level fixes with predicted, not measured, effect — the same unattributed class
this arc just spent a day discharging for #532. **Host-independent work while waiting for the T6
window:** the #569 fork-safety audit (§3.2, code reading) and the two auditor edits §3.1 step 2
requires — but **create the census worktree from `origin/main`, never from the primary's `HEAD`**
(the primary is two commits behind; a census cut from it measures the PRE-fix build and nothing in
the ledgers would say so — a round-2 validator caught this in an earlier draft).

| # | item | gate |
| --- | --- | --- |
| 1 | **§3.1 re-measure both merged fixes live** (G4 decomposition at cap 16 for #587; worker census for #588) | **T6 window** (§4.4) |
| 2 | **§3.2 cascor#569 — F3 preload, now unblocked** | after §3.1's census reads clean; the fork-safety audit (code reading) can start now |
| 3 | **§3.3 cascor#579 — the post-#563 worker profile** (never run; "#563 caused the 9×" is still a correlation) | T6 window — **share item 1's cell**, it is one cap-4 run |
| 4 | **§3.4 cross-arm parity: #582 / #572 / #530 / #578** — decisions, not measurements | owner decides #578 and #582's option |
| 5 | **§3.5 the tracked-but-untouched items**: #573 (logging redesign, owner-timed), #550 (CodeQL/model-core Wave 2) | owner |
| — | pred. §4.8 deferred list: cap series re-measure, cap-128 3-seed spread (cost-gate first), retrospective corpus re-validation — **inherited; its #530/#572 bullets are absorbed into §3.4; raise the last one with the owner, do not absorb** | T6 window / owner |

### 3.1 Re-measure both merged fixes (first, and it needs the host)

**Pre-conditions, in order — the campaign REFUSES otherwise.** The service arm always runs from
the **primary checkout** `Juniper/juniper-cascor` (`util/experiment_stack.bash`, anchor text
`CASCOR_SRC_DIR="${PROJECT_DIR}/juniper-cascor/src"`), and the paired campaign's pre-flight
compares that checkout's HEAD with the CLI worktree's and exits 2 on mismatch (anchor text
`paired: REFUSING -- arms are at different cascor commits`). Because the launch is
`setsid nohup … &`, that refusal lands only in the launch log — a watcher armed on the completion
marker never fires (§4.1). At handoff the primary is at `fa649d0b`, **two behind** `origin/main`
(`d2d10697`). So:

```bash
# 0. T6 window open? (§4.4) — then:
# The launchers `cd` into juniper-cascor/src and exec `uvicorn api.app:create_app` / `python main.py`
# — the path is NEVER in argv, so an argv grep is blind to an idle stack. Gate on cwd instead:
ls -l /proc/[0-9]*/cwd 2>/dev/null | grep -c 'juniper-cascor/src'      # must print 0 (a Docker-stack `python src/main.py` at /app does not match)
bash util/experiment_stack.bash --status                                 # no runs
ls -1 /run/user/1000/juniper-experiments                                 # empty
ss -ltn | awk 'NR>1{split($4,a,":"); p=a[length(a)]+0; if ((p>=8110&&p<=8139)||(p>=8230&&p<=8259)||(p>=8260&&p<=8289)||p==8202||p==8101||p==8051) print p}'   # empty (incl. the canopy-E2E trio)
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor rev-parse --abbrev-ref HEAD   # main
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor status --porcelain   # must be empty
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor pull --ff-only origin main
SHA=$(git -C /home/pcalnon/Development/python/Juniper/juniper-cascor rev-parse --short=8 HEAD)   # expect d2d10697 or later
# 1. CLI worktree at the SAME commit (the #588 fix worktree is gone; create fresh, detached) — capture WT now:
WT=/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--exp--g4-post587--$(date +%Y%m%d-%H%M)--${SHA}
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor worktree add "$WT" --detach HEAD
```

**Step 1 — G4 decomposition (verifies #587).** Launch is `setsid nohup`, never a harness
background task (pred. §3.3); the completion marker is **`paired: done ->`** (§4.1):

```bash
setsid nohup bash util/ad-hoc/2026-08-21_h2h_paired_campaign.bash "${WT}/src" \
  util/experiments/suites/p4/e-k-thread-probe-cap16.yaml 4 \
  ~/.local/state/juniper-experiments/g4-paired-cap16-post587 \
  > ~/.local/state/juniper-experiments/g4-paired-cap16-post587.launch.log 2>&1 &
# ~15-25 min. A NEW OUT_ROOT every time (pred. §3.2: reuse truncates provenance and appends logs).
# Service legs are NOT in OUT_ROOT. Resolve them from THIS campaign's own ledger, never by suite-dir
# name (the 20260825T* legs listed in §5 belong to the PREVIOUS campaign and would silently pair
# old service legs with new CLI legs):
#   suite_dir per leg  <- ~/.local/state/juniper-experiments/g4-paired-cap16-post587/legs.jsonl
#   run_dir per leg    <- <suite_dir>/registry.jsonl  (four)
python3 util/ad-hoc/2026-08-25_g4_overhead_decomposition.py \
  --dir-arm cli ~/.local/state/juniper-experiments/g4-paired-cap16-post587 \
  --run-arm service <run_dir 1> <run_dir 2> <run_dir 3> <run_dir 4>
for d in ~/.local/state/juniper-experiments/g4-paired-cap16-post587/cli-*; do grep -c 'did not stop gra' "$d/logs/juniper_cascor.log"; done
```

**Acceptance — read the ungraceful-stop COUNT, not the time.** #587 shipped two independent
changes: (a) the feeder-flush fix (`cancel_join_thread` + drain) — the hypothesised mechanism — and
(b) a **shared** 5 s grace + 1 s kill deadline replacing seven serial `join(5.0)`s. **(b) alone caps
teardown at ≈ 5 + 1 + 7×0.5 ≈ 10 s even if (a) is wrong**, so `train_other` can never "stay high"
on a #587 build and a time-only reading would call a still-broken pool "fixed". The discriminator
is the count:

| reading | meaning |
| --- | --- |
| `train_other` ≤ 3 s **and** `did not stop gracefully` = **0** in all four CLI legs | mechanism (a) confirmed |
| `train_other` > 3 s **and/or** any ungraceful stop | **(a) was wrong or incomplete; (b) is masking it** — the count decides, not the seconds. py-spy the stuck worker in ancestor mode (`util/ad-hoc/2026-08-23_pyspy_conda_shim.bash`; `ptrace_scope=1`; no `--nonblocking` with `--native`) and reopen #586 with the stack |

On a pass, post the table to **#571 and close it**: G4's question ("what is the fixed overhead?")
is answered — one defect, now fixed — and its residue (the cross-arm candidate/output difference)
is #582/#578's, not an overhead hunt. Then update the register's G4/G5/G6 rows (they still read
"#568 OPEN / import edge not traced" and "After #586") and retitle **#569** (its title still says
BLOCKED).

The whole-process ratio will then read **≈ 0.75** (77/103), NOT "near 1.0" — the CLI's remaining
span is *smaller* than the service's, because the service does more candidate and output work (§1
row 6). **Attribution caveat:** a run at `d2d10697` measures **#587 + #588 jointly** — #588 also
removed a per-worker `sentry_sdk.init` whose `atexit` flush (no `shutdown_timeout` configured,
`main.py`, anchor text `sentry_sdk.init(`) is an *independent* exit-hang candidate. To attribute
#587 **alone**, run at exactly `76f4d51b` (primary AND CLI worktree both checked out there); the
joint run is the one that matters operationally, the solo run is what you cite as "#587's effect".

**Step 2 — worker census (verifies #588), same window, one cap-4 cell.** The auditor is on the
local branch `diag/forkserver-import-audit` (one commit: `src/cascor_diag_import_audit.py` + a
preload-list/`_worker_loop` patch; `git -C /home/pcalnon/Development/python/Juniper/juniper-cascor show diag/forkserver-import-audit --stat`).

**How the ledgers actually work — read before interpreting anything.** The auditor's module body
runs ONCE, in the forkserver; forked children inherit the `__import__` hook without re-executing
the module and exit via `os._exit` (no `atexit`). So exactly **one** ledger carries `auditor
ARMED` and `FINAL modules=` (the forkserver), and a child ledger exists **only if that child
triggered a first-import of a watched package**. On the pre-#588 build there were 7 child ledgers
(one per worker, matplotlib/pydantic/fastapi/httpx chains); **on the fixed build the expected
count of child ledgers is ZERO** — which is why "no `sentry_sdk` in any child ledger" is a hollow
zero by itself. The worker-side evidence is the census line each worker logs into the trainer log
(`_worker_loop: DIAG-ENV: … sys_modules=N present=[…]`) — and as shipped, neither its `_diag_hot`
tuple nor the auditor's `_WATCH` tuple contains `sentry_sdk`, so both must be edited first.

On a **throwaway** worktree/branch, cut from **`origin/main`** (never the primary's `HEAD`, never
a PR branch); all commands from the juniper-ml root, using `git -C` so the shell never changes
directory:

```bash
CWT=/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--diag--census-post588--$(date +%Y%m%d-%H%M)--${SHA}
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor fetch -q origin
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor worktree add "$CWT" -b diag/census-post588-$(date +%H%M) origin/main   # fresh suffix; never -B (it would reset an earlier attempt's commit)
git -C "$CWT" cherry-pick diag/forkserver-import-audit        # applies cleanly on d2d10697 (hunks sit between #587/#588's)
#   edit $CWT/src/cascor_diag_import_audit.py:        add "sentry_sdk" to the _WATCH tuple
#   edit $CWT/src/cascade_correlation/cascade_correlation.py, the _worker_loop DIAG-ENV line: add "sentry_sdk" to the _diag_hot tuple
git -C "$CWT" commit -qam "diag: census post-#588 (NOT for merge)"
git -C "$CWT" rev-parse --short=8 HEAD                        # RECORD THIS in the #570 post — the evidence carries no SHA otherwise
[ -n "${JUNIPER_CASCOR_SENTRY_DSN:-$SENTRY_SDK_DSN}" ] || echo "NO DSN — the Sentry negative would be meaningless"   # by VALUE; the login shell sets only the legacy SENTRY_SDK_DSN, which main.py accepts with a DeprecationWarning (that warning is control 1)
mkdir -p ~/.local/state/juniper-experiments/census-post588/audit-logs   # _write() swallows errors: a missing dir = zero ledgers = a hollow zero
bash util/ad-hoc/2026-08-14_r5_stack_up.bash                            # prints RUN_ID= and DATA_URL=; export both
CELL=~/.local/state/juniper-experiments/suites/e-l-determinism-cap4-20260824T003754Z/cells/c000-7749f335/experiment.yaml
JUNIPER_DIAG_IMPORT_LOG=~/.local/state/juniper-experiments/census-post588/audit-logs \
  bash util/ad-hoc/2026-08-17_h2h_thread_probe.bash "$CWT/src" "$CELL" \
  ~/.local/state/juniper-experiments/census-post588/cli-01 "$DATA_URL" 360 default
```

**Controls, in order (check a zero for vacuity — every one must hold before the result means
anything):**

1. `grep -c 'SENTRY_SDK_DSN is deprecated' ~/.local/state/juniper-experiments/census-post588/cli-01/direct_cli.log` ≥ 1 —
   the parent resolved a DSN (the legacy-name `DeprecationWarning` proves it; the pre-#588 stored
   run has exactly one such line).
2. Exactly **one** ledger in `audit-logs/` with `auditor ARMED` and `FINAL modules=` — the
   forkserver ran the hook. (Label quirk: the forkserver's lines read `role=parent(main.py)` and
   any child's read `role=forkserver` — the `_role()` heuristic is inverted; do not grep for
   `child-of-`.) The comparator for "what child ledgers look like" is the pre-fix run
   `forkserver-audit-c4bbe815/audit-logs/` (7 child ledgers × 7 `FIRST-IMPORT` lines).
3. **7–8** `_worker_loop: DIAG-ENV` lines in `cli-01/logs/juniper_cascor.log`, each with
   `sentry_sdk` visibly absent from a `present=` list that the edited `_diag_hot` *would* have
   shown (confirm your edit landed: `grep -c '"sentry_sdk"' "$CWT/src/cascade_correlation/cascade_correlation.py"` ≥ 1).

**Result:** every `DIAG-ENV` line reads `sys_modules` **< 1,400** (pre-fix 1,872; the #588 test's
own bound) and `present=['torch', 'numpy']`; **zero** child ledgers in `audit-logs/` (any child
ledger names the chain that re-entered — that IS the failure branch: post its `FIRST-IMPORT` line
to #570 and do not close). If `sys_modules` ≥ 1,400 or `present` lists anything beyond torch/numpy,
#588's gate misfired for that path — same action. Post the SHA + the three controls + the result to
#570 and #571; **close #570 only if all hold.** Tear down with `bash util/experiment_stack.bash
--down "$RUN_ID"`.

**Step 3 — #579's profile shares this cell** (§3.3): re-run the same probe into a **new**
`cli-02` output dir (re-using `cli-01` appends to its `logs/juniper_cascor.log` and doubles every
count — pred. §3.2's reuse class) with
`JUNIPER_CASCOR_WORKER_PROFILE=~/.local/state/juniper-experiments/census-post588/prof` set.

### 3.2 cascor#569 — F3 preload (unblocked by #588)

Only after §3.1's census confirms `import cascade_correlation` is matplotlib-free in a worker.
Then add `"cascade_correlation.cascade_correlation"` to `set_forkserver_preload` (the list in
`_init_multiprocessing`, `cascade_correlation.py`; anchor on the text `set_forkserver_preload`, not
a line number) and re-run the census. **Read both branches:** the forkserver's own `FINAL modules=` should rise
from ~1,093 to **≥ 1,155** (1,155 is the fresh-interpreter trainer count; the union with the
forkserver's own table may read higher — measure, do not assume) — **if it stays at ~1,093 the preload silently did nothing**: CPython's
forkserver swallows a preload `ImportError` (`multiprocessing/forkserver.py`, `except ImportError:`
in `main`), so a mistyped module string is a no-op with no error. Do not expect a visible
`pool_setup` win — it is 2±0 s at 1-second resolution, the instrument's own floor. **Fork-safety audit is still required before merge**, and it is a code-reading task: what
module-level state does importing `cascade_correlation.cascade_correlation` create that a forked
child would share? Known at `d2d10697`: no module-level `Logger` instance (cascor's `Logger` opens
its file per record, `logger.py`, no persistent handle); module globals `_task_queue = None` /
`_result_queue = None` (created lazily, in the manager server only); the two `atexit.register`
calls are inside `_init_multiprocessing` (instance-level, only run when a network is constructed);
transitively `parallelism/task_distributor.py` takes a stdlib `logging.getLogger`. The audit must
also cover `candidate_unit`, `cascor_constants`, `log_config` and `utils` (all imported at module
level). **Size the benefit honestly:** `pool_setup` is 2±0 s at cap 16 with seven workers importing
concurrently, so the preload saves ≲ 2 s per run (~2%) — worth doing for cleanliness, not for
speed. The commented-out `mp.get_context("forkserver")` + garbled note above the context creation
(pred. §4.6) should be cleaned in the same PR.

### 3.3 cascor#579 — the post-#563 worker profile

Instrument exists (`JUNIPER_CASCOR_WORKER_PROFILE=<dir>`, cascor#567). The **pre-#563 comparator
corpus** is `~/.local/state/juniper-experiments/profile-cap4/prof-cli/` (32 `.prof`, the residual
note §4.3b/§4.3c corpus; `profile-cap4` is on pred. §3.2's preserve list). Run one cap-4 CLI cell with the env var set (§3.1 step 3
shares the census cell), then
`python3 util/ad-hoc/2026-08-23_h2h_worker_profile_diff.py pre563 ~/.local/state/juniper-experiments/profile-cap4/prof-cli post563 <new prof dir>`
(`<BASE_LABEL> <BASE_DIR> <OTHER_LABEL> <OTHER_DIR> [--top N]`). Like-for-like baseline: the cProfile corpus read **≈ two thirds** of worker self time under
`inspect` (residual note §4.3c); the ≈78% figure is py-spy's (§4.3d) and is NOT what the diff
script compares against. **cProfile for attribution only, never timing** (pred. §1.6).
**Expected:** `inspect.getmodule` / `getsourcefile` frames **< 5%** of worker self time. **If they
still dominate, #563's f_back change did not reach the worker path** (the logger is re-created per
process) — that would reopen the 9× attribution, not close it. Post to #579 either way.

### 3.4 Cross-arm parity — decisions

The two arms are each deterministic but disagree (11,310 vs 13,140 candidate epochs at cap 4;
46,970 vs 53,590 at cap 16). Two causes are located: **#582** (service promotes `X_test`→val
in-loop at `api/lifecycle/manager.py`, anchor text `new_val_x = torch.tensor(arrays["X_test"]`; CLI
trains with `(no val data)`) and **#572/#530** (construction-time global-stream offsets; service seed
pinned to 42). **#578** is the baseline-tier decision that depends on them. None needs a run; all
need the owner to pick an option (each issue lists them). Do not build tooling here first.

### 3.5 Tracked, untouched, owner-timed

**#573** logging redesign (design doc first; carry `_log_at_level`'s per-record `open()` and the
unconditional `print()` into it — those two findings are recorded in **pred. §4.13**, NOT in the
fix design's §8, which only scopes the redesign out of F1). **#550** CodeQL unused-global on
juniper-cascor-model (Wave 2 adoption is the structural fix).

---

## 4. Hazards this arc created or confirmed — NEW ones only; pred. §3.1–3.7 all still apply

### 4.1 A campaign's completion marker is script-specific

`2026-08-21_h2h_paired_campaign.bash` ends with **`paired: done ->`**; the determinism campaign
ends with `campaign: done`. A watcher grepping the wrong marker times out silently while the
campaign has long finished (happened this arc — the monitor hit its 60-min cap; the campaign had
completed in 15). Grep the script's own final `echo` before arming a watcher.

### 4.2 `git stash push -u` takes untracked TEST files with it

Proving a guard by reversion with `stash push -u` removed the new (untracked) test file, so the
targeted pytest run reported **"no tests ran"**. That run exits **5** (empty collection) or **4**
(missing path) — non-zero, so the exit code DOES catch it; what hides it is the swallowed summary
(§4.5) if you read only the last lines. The genuinely pass-looking variant is a **whole-suite** run:
it exits 0 while the new guard silently never collects. So: trust the exit code **and** assert a
non-zero collected count (`--junitxml`, `tests=` attribute) whenever the point of the run is a
specific new test. Mechanically: copy the source files aside, `git checkout origin/main -- <src
files>`, keep the tests in place, restore by copy. If you must stash on this host: unique tag,
capture the SHA, `stash apply <sha>`, drop by re-found ref — the stash stack is shared across
sessions; never bare `stash pop`.

### 4.3 Timestamp partitioning miscounts same-second round boundaries

A cascor round's output tail lands in the **same second** as the next round's `train_candidates`
start; a decomposition that partitions by timestamp zeroes whole rounds (read 5 s where truth was
12). Use **log stream order** (the `_g4_overhead_decomposition.py` state machine) for any
1-second-resolution instrument. Also: the initial output pass runs **before** the
`fit: Starting main training loop` record — that marker is not the training start.

### 4.4 The T6 host-window protocol is live

Another session ("T6 re-baseline E-A/E-I/E-C"; its cross-session socket was
`uds:/run/user/1000/cc-socks/1606678.sock` at handoff time — the `ListAgents`/`SendMessage` tools
may not be loaded in a fresh session, and a socket file's existence proves nothing) holds
the next exclusive GPU window (~7–9.5 GPU-hours). **This session committed: no CPU/GPU-heavy suites
until it announces completion.** Its drain watch requires experiment ports + the canopy-E2E trio
(8202/8101/8051) clear, load1 < 4, GPU < 1 GiB. Honour that; if Paul arbitrates differently, his
call wins. **There is no observable "announcement" artifact**, and **"not started" and "finished" have the
identical host signature** (no ports, no lockdirs, nothing new under `suites/`) — so a quiet host is
*necessary* for §3.1 but never *sufficient*. What opens the window is an explicit go from Paul or
from the T6 session; the host checks (§8's port/lockdir/load lines, `nvidia-smi`, new `suites/`
dirs) only tell you whether a campaign is *currently* running. T6 had **not** started at
handoff time (no ports, no lockdirs, nothing new under `suites/`) — and note its own drain
condition (`load1 < 4`) may be unmet for hours by unrelated host load (a `duplicati-server` job
and a VM were holding load1 at 13–18 on 2026-08-25). **Bounded wait:** if T6 has neither started
nor announced within ~4 hours of a session starting, ask Paul which of T6 and §3.1 goes first
rather than idling; his call wins either way.

### 4.5 `pytest` under cascor's logger swallows the summary

Trust the exit code, or write `--junitxml=<file>` and read `tests/failures/errors` from it — the
summary line is frequently absent from captured output (pred. §6, carried into #573).

### 4.6 A truncated reference sweep ships a broken build

`grep -n CascadeCorrelationPlotter … | head -8` truncated a **10-line** result; the hidden tail
held the static `plot_dataset` delegate — the **fourth real use site** — which became an
`F821 undefined name` that only CI caught (#588's first run). Third recurrence of this class in the
arc's history. **Count first (`grep -c`),
then list untruncated** — `head` on a reference sweep is never acceptable. Same discipline for
`sed -n` windows when deciding an edit anchor is unique.

---

## 5. Inherited by reference — READ THE PREDECESSOR for these

- **pred. §3.1** golden reset (#566) — every pre-2026-08-23 baseline incomparable.
- **pred. §3.2** evidence-preservation rules for `~/.local/state/juniper-experiments/` (46 GB+;
  service arms live in top-level run dirs via `suites/*/registry.jsonl`; never sweep by name).
  **New roots this arc, preserve:** `seedvar-n20-at565`, `seedvar-n20-at563`, `seedvar-n20-at562`
  (1.1–1.2 GB each — the attribution bracket), `g4-paired-cap16-20260825` (988 MB) + its four
  `suites/e-k-thread-probe-cap16-20260825T*` service legs, `forkserver-audit-c4bbe815` (57 MB) —
  **and the arc's stack run dirs** (~100 KB each; **no registry references them**, so pred. §3.2's
  resolve-from-registry rule does not protect them): `20260824T095117Z-304c` (the seedvar
  bracket's stack — named in `seedvar-n20-at565/provenance.json` and evidence note §7),
  `20260825T101852Z-eebb` (the G4 campaign's — named in `g4-paired-cap16-20260825/provenance.json`),
  and **`20260825T101004Z-1ccb` (the #570 census stack — named NOWHERE else; this line is its only
  link)**.
- **pred. §3.3** the orphan reaper kills live campaigns (`util/reap_pytest_orphans.bash` —
  protection keys P1/P2). Also: never two determinism campaigns at once (shared `pkill -f` by cell).
- **pred. §3.4** `juniper-cascor-model` byte-identical extraction — mirror `src/` edits to
  `candidate_unit` / `utils` / `log_config` / `cascor_constants`. **#587 and #588 touched neither
  tree** (verified: `cascade_correlation.py`, `main.py`, tests only).
- **pred. §3.5–3.7** sequence-safety waiver in ONE commit; anchor on required contexts; server-side
  update-branch.
- **pred. §4.1** two hazards that outlive the attribution: the campaign's same-SHA guard reads
  `rev-parse HEAD` and **cannot see a working-tree revert**; and **`GOLDEN_CAPTURE=1` rewrites
  `src/tests/fixtures/golden/*` AND `two_spiral_seed42.npz` in place, no prompt, no backup** —
  every golden failure message invites it; legitimate only inside a PR that means to move the
  baseline.
- **pred. §1.4 / §1.4a** corrected numbers (do not resurrect: "OMP=2 costs 1.30×", "~1.17×
  residual", "#533 removed 1.30×") and build-specific numbers (do not discard: 0.768 pre-arc;
  1.308 / 1.230 / 1.162 — now reconciled in evidence note §5).
- **pred. §1.6** the eliminated-hypotheses table (thread context, pool packing, cProfile-for-timing,
  BLAS thread count, arrival-order tie-break) — each was tested and killed; re-proposing one is
  cheap and re-testing it is not. Sources: four rows cite the residual note, two the
  **reproducibility note**
  `notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md`.
- **pred. §4.2**'s tensor-hash probe (hash the training tensors on both paths before the first
  candidate round) is the cheapest discriminator for #582/#572. **#582 carries it as a comment
  (2026-08-25T22:59Z); #572 still does not** — add it there before doing §3.4.
- **pred. §4.8** deferred list: cap-series re-measure, cap-128 3-seed spread (cost-gate first),
  retrospective corpus re-validation (**owner decides**); its #530/#572 bullets now live in §3.4.
- **pred. §6** operational notes (env, `JUNIPER_EXP_HEALTH_TIMEOUT=180`, py-spy ancestor rule,
  the 637 MB cap-64 log, `--down --all-mine` scope) and **pred. §6.2**, the per-category tooling
  list — in the predecessor's own words, *"'now cheap' claims are only true if you know which
  script to run"*.
- **pred. §4.5**'s symbol anchors for the forkserver architecture
  (`_PROJECT_MODEL_CANDIDATE_TRAINING_CONTEXT = "forkserver"` in `constants_model.py`; the pool
  creates workers with `self._mp_ctx.Process`) — the starting points for §3.2's fork-safety audit.
- **pred. §2**'s required-status-context names (`Symbol & Docs Screen`, `Golden / Snapshot
  Regression`, `model-core Conformance`) — they differ from the workflow names, so grepping a
  check-runs list for the workflow name finds nothing.
- **pred. §5** methodology rules 1–10; this arc added: *check a zero for vacuity* proved decisive
  again (§4.2's "no tests ran").
- **pred. §6.1** worktree table — see §7 for what changed.

---

## 6. Operational notes

- Env: `/opt/miniforge3/envs/JuniperCascor1` (torch 2.11.0+cu130, py 3.13.13). `columnar` absent
  there → `test_utils_optional_deps.py::TestColumnarImportGuard` fails locally, passes in CI.
- `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` is load-bearing from a
  worktree; the campaign scripts default it.
- Stacks: always `util/experiment_stack.bash --down <RUN_ID>` from your own `provenance.json`;
  **`--down --all-mine` tears down EVERY run** (pred. §6). Check `--status`, `ps`, the three port
  ranges and `/run/user/1000/juniper-experiments` before launching anything.
- **Concurrent sessions**: during this session's validation rounds three other ml handoff PRs
  (#1361, #1363, #1364) merged and `origin/main` moved three times; the Cursor fleet had
  cascor#583/#584 open; the T6 session was waiting on the host. **Re-derive, do not trust this
  list.**
  `gh pr list` dup-guard before opening anything.
- **Landing path**: `python3 util/wait_for_checks.py --pr N --repo <repo> --anchor required`; merges
  only on Paul's explicit approval (`util/safe_merge.py --pr N --repo <repo> --merge-method squash
  --execute` when approved).

---

## 7. Worktrees and branches — state at handoff

| item | state | action |
| --- | --- | --- |
| `worktrees/juniper-cascor--fix--568-cli-import-hygiene--20260825-0730--fa649d0b` | branch `fix/568-cli-import-hygiene` — **#588 MERGED** (`d2d10697`) | **removed by this session after the merge** (ran only pytest; snapshot check read 0). Local branch deleted. **`delete_branch_on_merge` is OFF on juniper-cascor** — merged remote branches persist until deleted by hand (#587's `fix/586-worker-shutdown-hang` still exists on origin; #588's was deleted by the owner) |
| cascor local branches `diag/seed-instability-at-56{2,3,5}`, `diag/forkserver-import-audit` | **local-only provenance refs** for the evidence note §3.2 and #570 (each = base + one "NOT for merge" diag commit); their worktrees are already removed | **keep**; never push, never delete without updating the evidence note's provenance table. **`diag/forkserver-import-audit` tracks `origin/main`** (`git branch -vv` → `[origin/main: ahead 1, behind N]`) — never `git pull` while it is checked out, it would merge main into a provenance ref; the owner may `git branch --unset-upstream diag/forkserver-import-audit` |
| `worktrees/juniper-cascor--fix--candidate-seed-derivation--20260823--362b88b1` (`rescue/candidate-seed-derivation-wip`) and `…--diag--seeds-and-balance--20260821-2115--362b88b1` (`rescue/seeds-and-balance-diag-wip`) | pred. §6.1 rows; **still present, 28 `.h5` between them**; their `util/ad-hoc/*.patch` twins verified on `main` | **Redundancy is uneven** (verified by content diff): `seeds-and-balance` ≡ its `.patch` ≡ the `diag/seed-instability-at-56x` commit content; but `candidate-seed-derivation-wip` (81 lines: network-owned seed RNG + `DIAG:` seed log + worker-profile dispatcher + `DIAG-ENV` census) ≡ **its `.patch` ONLY** — no `diag/*` branch carries it, its substance shipped as #566/#567, and the patch no longer applies to `origin/main` in either direction. Provenance only. **Owner's call to remove**: copy the 28 `.h5` out first (`worktree remove` deletes them), then `git branch -D` (both unmerged, unpushed) |
| pred. §6.1's `exp--determinism-postarc` (detached `234c203`), `fix--logger-frame-resolution` (`be346be`), `exp--residual-wall-gap` (detached `362b88b`) | **ALL THREE STILL PRESENT** — `git -C /home/pcalnon/Development/python/Juniper/juniper-cascor worktree list`; `.h5` counts **100 / 73 / 450**. (An earlier draft of this table said "no longer listed" — that was a `../juniper-cascor` path resolving nowhere from the session worktree; a validator caught it.) `determinism-n20-postarc/provenance.json:cascor_src` still points at the postarc tree | pred. §6.1's dispositions stand unchanged: **postarc — keep, do not move its HEAD** (it is the §1.1 provenance link); the other two — removable **only after** the snapshot check, ~620 un-indexed models between them; **owner's call** |
| this session's ml worktree `.claude/worktrees/adaptive-soaring-codd` | branch `docs/handoff-2026-08-25-perf-lane-closeout` off `origin/main` `84f52793`; only this file (untracked until committed) | the handoff PR |
| `Juniper/juniper-cascor` primary checkout | at `fa649d0b`, **two behind** `origin/main` (`d2d10697` = #588, `76f4d51b` = #587), clean | **§3.1 step 0 requires syncing it** (the service arm runs from here) — only when its tree is clean and `ps` shows nothing running from `juniper-cascor/src` |

---

## 8. Verification commands

```bash
git fetch --prune && git log --oneline HEAD..origin/main            # expect commits; sessions merge often
gh pr view 588 --repo pcalnon/juniper-cascor --json state,mergeStateStatus,mergedAt
gh issue list --repo pcalnon/juniper-cascor --state open --limit 20  # 532/568/586 CLOSED; 569 570 571 572 573 578 579 582 530 550 OPEN
gh issue view 532 --repo pcalnon/juniper-cascor --json state         # CLOSED
gh issue view 586 --repo pcalnon/juniper-cascor --json state         # CLOSED
# gh issue view without --json fails on this gh build (projectCards GraphQL); PR bodies via REST:
#   gh api -X PATCH repos/pcalnon/<repo>/pulls/<n> -F body=@body.md

# Re-derive this arc's numbers from stored logs (seconds each; NO training):
python3 util/ad-hoc/2026-08-24_seedvar_analysis.py ~/.local/state/juniper-experiments/seedvar-n20-at562/at562   # expect 177/190 = 0.932
python3 util/ad-hoc/2026-08-20_determinism_nrun.py --dir-arm at563 ~/.local/state/juniper-experiments/seedvar-n20-at563/at563  # expect 0/190
python3 util/ad-hoc/2026-08-25_g4_overhead_decomposition.py --dir-arm cli ~/.local/state/juniper-experiments/g4-paired-cap16-20260825  # expect train_other 37±1

# Host state before ANY heavy run (T6 protocol, §4.4):
ss -ltn | awk 'NR>1{split($4,a,":"); p=a[length(a)]+0; if ((p>=8110&&p<=8139)||(p>=8230&&p<=8259)||(p>=8260&&p<=8289)) print p}'
ls -1 /run/user/1000/juniper-experiments; cut -d' ' -f1 /proc/loadavg; nvidia-smi --query-gpu=memory.used --format=csv,noheader
[ -n "${SENTRY_SDK_DSN:-}${JUNIPER_CASCOR_SENTRY_DSN:-}" ] && echo DSN-OK || echo NO-DSN   # by VALUE, not name — an empty var passes a name grep
util/reap_pytest_orphans.bash --dry-run                              # --dry-run only prints WOULD REAP. NEVER non-dry while T6 (or any campaign) is alive: its nohup'd services sit on the orphan predicate and rely on P1/P2 alone
```

---

## 9. Validation record

Written per `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` and validated per
the 2026-08-23 multi-agent adversarial SOP: three independent lenses in round 1 (the repo's
`prompt-validator` rubric + re-probe; an adversarial fact-checker; a fresh-session executability
auditor), each prompted to refute, none shown another's verdict; a second round on the corrected
draft. The findings, which were verified against primary sources before being applied, and which
were rejected, are in the handoff PR body.
