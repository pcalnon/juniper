# HANDOFF 2026-08-25 (evening) — the cascor stop-during-training defect is DIAGNOSED and FIXED; two PRs await approval; the tail remains

> **Continue the juniper-cascor / juniper-ml snapshot-lifecycle arc.** The predecessor handoff
> (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-25_snapshot-arc-closeout-and-cascor-shutdown-defect.md`,
> "the predecessor" below) carried one partly-diagnosed defect (its §2) and a tail (its §3). The
> defect is now fully diagnosed, fixed, and **verified on an ISOLATED stack, pre-merge, for a stop
> landing in the output-layer phase** — the mid-candidate-round path is covered only by a unit test
> with mocked hooks and has never run live; production verification is §3.2. **Its §3 tail is
> untouched and carries forward verbatim** (§3 here points at it rather than restating it).

**FIRST ACTION: get the two PRs landed — only on Paul's explicit approval** (headless-merge policy;
do not arm auto-merge on your own initiative):

| PR | what | state at handoff |
|---|---|---|
| **cascor#589** (`fix/shutdown-joins-training-before-sigterm-exit`, base `d2d1069`) | the fix: `TrainingLifecycleManager.shutdown()` joins training (3 s bound) and releases the pool + shared memory explicitly; lifespan awaits it via `asyncio.to_thread` | OPEN; **all CI checks green, `mergeStateStatus` CLEAN, `mergeable` MERGEABLE, zero review threads** (2026-08-25 19:25 CDT; re-probe with `gh pr checks 589 --repo pcalnon/juniper-cascor` — main moves) |
| **ml `docs/shm-leak-mechanism-corrected-sigterm-reraise`** (the PR that carries this handoff — opened together with it, so its number is only knowable from `gh pr list`) | §6.5 correction to the characterisation note + the probe, the repro script, three evidence reports, and this handoff | OPEN once this file is visible on GitHub; if you are reading it from a worktree and `gh pr list --repo pcalnon/juniper-ml` shows no such branch, the PR was never opened and these seven files exist nowhere else — open it (§6) |

Merge mechanics are the predecessor's §5 (auto-merge preconditions, never `update-branch` the moment
a PR goes BEHIND, compare `.base.sha`, waiters get killed). Both `--auto` preconditions were
re-checked this session (2026-08-25 ~19:00 CDT) and hold on BOTH repos: `allow_auto_merge` = true,
and the main ruleset (`juniper-cascor-rules` 15081045 / `juniper-ml-rules` 13805432) has
`strict_required_status_checks_policy` = true. Re-verify if more than a day has passed. Land order: the cascor PR body links to `juniper-ml/util/ad-hoc/…` files that exist only
once the ml PR merges — land ml first, or accept dangling references. ⚠ The cascor PR was authored from
`main @ d2d1069` as **whole files**. Cursor draft **cascor#584** overlaps it only in
`src/api/lifecycle/manager.py`, at hunks far from `shutdown()` (`_create_network_locked` ~:1513,
`start_training` ~:2130, `reset` ~:2442; #589 touches the constant at ~:41 and `shutdown()` at
~:5021+; the test files do not overlap — #584 edits `test_lifecycle_manager.py`,
`…coverage_ext.py`, `test_network_route_coverage.py`, `test_training_route_coverage.py`; #589 edits
`test_lifecycle_manager_coverage.py` (class `TestShutdown`), `test_app_startup_tasks.py`,
`test_api_app.py`).
GitHub's 3-way merge handles that; the real check after #584 lands is
`gh pr view 589 --repo pcalnon/juniper-cascor --json mergeable`. What you must NOT do is amend
#589 with a whole-file `manager.py` taken from a tree that lacks #584 — that silently reverts it.

"§N" means a section of THIS document.

---

## 1. What this session established — the predecessor's §2.3 question is answered

The predecessor asked *"why did the existing interrupt not fire?"* and offered three candidates.
**All three were wrong. The process was already dead.**

- uvicorn's `Server.capture_signals` (0.29+, "cooperative signal handling", March 2024; host
  envs run **0.40.0 / 0.46.0 / 0.49.0** for JuniperData / JuniperCascor1 / JuniperCanopy1 and
  every lockfile pins **0.52.4** for the Docker images — all newer than 0.29) restores the
  original signal handlers when `serve()` returns and then `signal.raise_signal()`s every captured
  signal. Python leaves SIGTERM at `SIG_DFL`, so the kernel terminates the process **within
  milliseconds of the lifespan's shutdown stanza returning — no `atexit`, no interpreter
  finalisation, no thread joins**. (The SIGTERM→death latency is ~0.2 s, almost all of it
  uvicorn's own shutdown tick *before* the stanza; the probe's thread was last seen ~1 ms before
  the stanza's mark, never after.) SIGINT is the only stop probed that unwinds normally (Python's
  handler raises `KeyboardInterrupt`); no other signal was tested.
- Every fleet stop tool sends SIGTERM (`juniper_chop_all.bash`, `experiment_stack.bash`,
  `isolated_stack.bash`, `docker stop`); `python src/server.py` → `uvicorn.run()` behaves the same
  as the `--factory` CLI. So cascor's three `atexit` registrations (`_cleanup_shared_memory`,
  `_release_candidate_worker_pool`, `service_launcher._cleanup_at_exit`) and multiprocessing's own
  finalizers were **dead code on every stop the fleet performs**, and `shutdown()` — which set
  `_stop_event` and returned in microseconds — was the last Python that ran.
- The 08-24 23:47 log proves it without a repro (split by a rotation at that instant: the epoch
  lines end `juniper-cascor/logs/juniper_cascor.log.1`, the shutdown stanza is lines 1–9 of
  `juniper_cascor.log`): the training thread wrote ~165 lines/s (≈1,650 epochs/s; an interrupt
  opportunity every ~15 ms) and wrote **nothing** after `JuniperCascor API shutting down` — not
  the `Epoch 7970` line due ~6 ms later, not `Training ended` (engine lines carry no
  milliseconds, so ordering inside ±10 ms of `.084` is not provable from timestamps; the
  per-second count — 15 lines in second `:00` at ~6 ms each — is consistent with death at
  ~`.09`). Nothing hung for 15 s. The predecessor's "SIGKILL after 15 s" was a deduction
  from the residue; the residue is equally explained by a SIGTERM death, and the log timing
  excludes the hang.
- The cooperative interrupt (`_handle_event` → `_check_for_interrupt` → `TrainingInterrupted`)
  is sound; it simply never got the milliseconds it needed. **No engine change was required**, and
  the characterisation note's §6.4 item 2 (= the predecessor's §2.4 step 2: a stop check in
  `train_output_layer`) is unnecessary. The predecessor's §2.3 candidates 1–2 were refuted by
  code, so nobody re-derives them: (1) `_run_training` drives
  `self.model.fit(…, on_event=self._handle_event)` — the sink is wired; (2) the `_stop_event` at
  `manager.py` ~:896 belongs to `_ReplaySession` (class at ~:837), the manager's is ~:1130 —
  same object as `_check_for_interrupt` reads.
- Qualifications on the claims above: "`python src/server.py` behaves the same" is by reading
  the source (`uvicorn.run` → `Server.run` → the same `serve()` inside `capture_signals`), not
  measured; `docker stop` is default semantics — cascor's Dockerfile has no `STOPSIGNAL` and the
  deploy compose's `stop_grace_period` was **not** checked (Docker's default is 10 s); the engine
  logs of both repro runs carry no device line, so "real training" means the full engine path
  including the forkserver candidate pool, with CUDA available in the env — not a verified GPU
  placement.

Measured, both directions, on an isolated stack (`util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash`;
own port 8209, own snapshot root and log dir, in-process spiral data, real training through the
full engine path including the forkserver candidate pool, one SIGTERM once the first hidden unit
is installed):

| | unpatched `d2d1069` | with the fix |
|---|---|---|
| SIGTERM → death | 0.277 s, wait status 143 | 1.542 s, status 143 (uvicorn's re-raise is unchanged by design) |
| training unwound | no — last log line is an epoch | `stop_requested` → `Training ended` → `TrainingLifecycleManager shut down (1.27s)` |
| descendants orphaned alive (tracker, forkserver, 15 workers) | **17** | **0** |
| `/dev/shm` residue after a reaper-equivalent SIGKILL of the orphans | **1 `juniper_train_*` + 9 `sem.mp-*`** — the ledger's signature exactly | **0 + 0** |

**Why it matters beyond 371 KB:** each orphaned forkserver child keeps its CUDA context (~116 MiB,
per `_release_candidate_worker_pool`'s docstring) and they accumulate until `CandidateUnit.__init__`
fails with CUDA OOM and runs report plausible results computed from nothing; and the same
abandon-mid-run trigger produced cohort B (273 truncated snapshots) until cascor#561 made the write
atomic — #561 closed the archive path, not the trigger.

Evidence: `reports/stop-during-training-2026-08-25/` (probe JSONL + both repro `report.json`),
`util/ad-hoc/uvicorn_sigterm_atexit_probe.py` (the minimal FastAPI probe: SIGTERM → status 143 and
`atexit` never ran, with or without joining the thread; SIGINT → exit 0 and `atexit` ran). Both
repro runs' `/dev/shm` entries were removed afterwards; **the host ledger is unchanged at 10
segments / 90 semaphores** (baseline 10 events, 08-17 → 08-24).

---

## 2. The fix, precisely (juniper-cascor PR)

`src/api/lifecycle/manager.py`:

- new module constant `_SHUTDOWN_TRAINING_JOIN_TIMEOUT_SECONDS = 3.0` (after the imports; not in
  `cascor_constants`, which would have required the model-core mirror);
- `shutdown()`: set `_stop_event` **and** `_pause_event`; `future.result(timeout=3.0)` on
  `_training_future` (the `swap_dataset_live` pattern; `TimeoutError` → WARNING, other exceptions
  → DEBUG); then `_release_network_resources()`; then the pre-existing liveness / replay /
  executor teardown with **`wait=False` kept** (`Executor.shutdown(wait=True)` has no timeout);
  the final log line keeps the `TrainingLifecycleManager shut down` prefix deliberately (substring
  greps in checklists and stack watchers still match) and now carries the elapsed time, or is a
  WARNING variant if the thread was abandoned;
- new `_release_network_resources()`: `network._release_candidate_worker_pool()` +
  `network._cleanup_shared_memory()`, idempotent, each failure logged and swallowed.

`src/api/app.py`: `await asyncio.to_thread(lifecycle.shutdown)`; stanza order unchanged
(coordinator → WS → lifecycle — stopping the coordinator first is what unblocks a training thread
waiting on a distributed round).

Tests: `TestShutdown` gains four tests (join-before-return; bounded + still-releases when the fit
ignores the stop, constant patched to 0.2 s; releases when idle; a failing hook does not mask the
next). `test_app_startup_tasks.py` gains a source guard for the `to_thread` line;
`test_api_app.py` gains a behavioural test (no running loop visible inside `shutdown()`).
**Fail-first was proven**: the four fail against the original body on the specific assertions
(`shutdown() returned with the training future still running`; hooks called 0 times).

Budget: common case ~1.3 s (measured). Pathological: 3 s join + `_WORKER_SHUTDOWN_GRACE_SECONDS`
(5 s) + a 1 s shared terminate-join + **0.5 s per worker that outlives its SIGKILL join**
(`_terminate_workers` is sequential there; none survive in practice, but "at most 1.5 s" is not
a strict bound — 15 stuck workers would be 8.5 s) ≈ 9.5 s realistically, **plus** the
pre-existing `stop_liveness_heartbeat` join (≤ 2 s) and `_replay_session.stop()` — so it can still
brush the 10 s grace of `experiment_stack.bash` / `docker stop`; chop_all's 15 s is safe. **No `SIGTERM_TIMEOUT`
change is needed** for the common case; if the ledger shows candidate-round stops (§3.2), consider
it then.

---

## 3. Remaining work, highest value first

1. **Land the two PRs** (FIRST ACTION above).
2. **Post-merge production verification — the ledger is the only instrument.** The fix is live on
   this host only once the primary checkout `/home/pcalnon/Development/python/Juniper/juniper-cascor`
   is pulled to a `main` that contains the merge (the experiment / isolated stacks run uvicorn from
   its `src/`) — **and the T6 campaign aborts (exit 3) the instant that HEAD moves, so the pull must
   wait for its COMPLETION announcement.** Until then every mid-training stop on the host still
   leaks; the T6 driver's own inter-cell stops are pre-fix. After the pull, take a fresh
   baseline (`ls -1 /dev/shm | grep -c '^juniper_train_'` / `grep -c '^sem.mp-'` — 10 / 90 at
   handoff, but `/dev/shm` is tmpfs: a reboot resets it and other sessions' pre-fix stops add
   pairs) and watch for **one new pair, not an absolute count**. A new pair after that is one of
   three things — a mid-candidate-round timeout (the cascor
   log carries `shut down with the training thread still running`), a genuine hard kill (SIGKILL /
   OOM / `KILL_WORKERS=1`; no such line), or a stack still running a pre-fix checkout. **Read the
   log before blaming the fix.** If it is the timeout class, decide whether the candidate-result
   wait loop needs its own interrupt check (engine code inside `train_candidates`'s result
   collection; does not touch the trajectory, but the golden gate is mandatory).
3. **Fleet audit: `atexit` reliance in the other uvicorn services — largely already answered.**
   juniper-data, juniper-canopy and juniper-recurrence have the same uvicorn property, but a
   read-only grep this session (`atexit.register|weakref.finalize|util.Finalize`, non-test, whole
   repo — juniper-data's package is `juniper_data/`, it has no `src/`) found **zero** hits in all
   three; only cascor registers anything. What remains is narrower and low priority: confirm nothing
   *load-bearing* in those services happens only at interpreter exit via a dependency (logging
   flush, `tempfile.TemporaryDirectory` finalizers, prometheus multiprocess dirs). One notes/ audit
   paragraph, not a PR, unless a hit turns up.
4. **Optional belt-and-braces for the Docker entry point**: in `juniper-cascor/src/server.py`,
   install a SIGTERM handler that raises `SystemExit(143)` *before* `uvicorn.run()` so the re-raise
   unwinds the interpreter normally (exit status preserved, `atexit` runs). ⚠ **Never inside
   `create_app()`** — uvicorn installs its handler before the factory runs and yours would replace
   it and break graceful stop. Deliberately excluded from the fix PR.
5. **The predecessor's §3 tail — untouched, carry forward as written there**: (1) the displacement
   guard (6 of 108 displaced: spiral 4 AND xor 2; frame on "best raw score ≠ winner", not on
   floor ≥ 1.000) — ⚠ **ml#1340 (open cursor draft) edits exactly this surface**
   (`util/snapshot_attribute.py`, `tests/test_snapshot_attribute.py`, `docs/REFERENCE.md`, the
   null-model doc, the regenerate script) and whole-file sends cannot see it:
   `gh pr view 1340 --repo pcalnon/juniper-ml --json state,files` before authoring; (2) `846587fb`
   (xor 0.79 at 1u; circles 1.000 at 2/3/4u); (3) persist training history via
   `include_training_state` (NOT `save_history`) — read the four snapshots that already carry a
   `history` group first; (4) the restore drill that the **retention ratification** (lifecycle
   DESIGN doc `JUNIPER_2026-08-16_…SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md` §6.4.2 q3 / §6.4.3)
   created — never run; gates S-4, S-1, S-3; (5) `snapshot_counter` is LIVE, `snapshot_classify.py`
   ~:60 still denies it; (6) a guarded `/dev/shm` sweeper — **lower value still**: with the fix in,
   the ledger is a regression detector, and sweeping erases the only production verification of
   §3.2; (7) moon is undecidable; (8) read the ledger as telemetry (now §3.2). Its §4 findings
   (seeded datasets, Floor B circularity, capacity confound, two inert fields, spiral withdrawn /
   xor thin margin) all still hold. **Its §5 (merge), §6 (traps: both lint invocations, BLOCKED =
   review thread, the hand-maintained CI test list, message strings as contracts, `tail -1`, the bg
   lease, stale pidfiles), §7 (verification commands + expected sidecar counts 27,962 / 27,689 /
   108 + 8; `--root`, never `JUNIPER_CASCOR_SNAPSHOTS_DIR`, for the sidecar chain) and §8
   (`regenerate_sidecar_chain.bash` with its REPO default hard-coded to the merry-puzzling-quasar
   worktree and mandatory `--backup DIR`) apply unchanged to every one of these items.** Nothing in
   this session touched the sidecars, so those counts stand — but re-probe before quoting (other
   sessions train).

---

## 4. Traps this session paid for

1. **A stop landing mid-candidate-round cannot be interrupted before the round ends.** The parent
   training thread waits on worker results; the interrupt rides only `epoch_end` / `phase_change`.
   The join then times out (3 s), the explicit release does the work, and the training thread is
   abandoned — bounded and logged **in the unit test only; untested live**. The untried part is the
   concurrent `_shutdown_worker_pool()` from the shutdown thread while the training thread is inside
   `train_candidates` (the training thread then fails its round on dead workers and lands in
   `_run_training`'s `except Exception` → Failed — harmless for a dying process, but never
   observed). It is the one path that can still leave residue if the process dies inside the 6.5 s
   pool escalation. See §3.2.
2. **A Python SIGTERM handler installed inside the app factory breaks graceful stop** (see §3.4).
3. **The sandbox's "too complex" refusal is heuristic, not a fixed grammar.** Seen refusing:
   `for` loops, `$(…)` substitutions, `cd` inside a compound, `env VAR=… python -m/-c`, multi-stage
   pipelines, and any `git -C` into a sibling checkout — while accepting other `&&` chains and
   pipes of similar shape. Don't predict it; when refused, split into plain commands (or a
   scratch script). Read sibling repos with `sed`/`grep`; make sibling-repo changes on a **scratch copy**
   and ship with `util/open_signed_pr.py`. The two rsyncs actually used (the exclusions matter — a
   bare `rsync -a juniper-cascor/ scratch/` copies the protected `cascor-snapshots/` asset store,
   `src/cascor_snapshots/` (766 .h5) and 100 MB of `logs/` into `/tmp`):
   `rsync -a --exclude cascor_snapshots --exclude __pycache__ --exclude .pytest_cache --exclude '*.h5' juniper-cascor/src/ <scratch>/cascor/src/`
   then
   `rsync -a --exclude src --exclude .git --exclude cascor-snapshots --exclude logs --exclude dist --exclude '*.log' --exclude .mypy_cache --exclude .pytest_cache --exclude .ruff_cache --exclude .benchmarks --exclude __pycache__ --exclude juniper_cascor.egg-info juniper-cascor/ <scratch>/cascor/`
   (root files `Dockerfile`, `conf/`, `pyproject.toml`, …; `test_dockerfile_bind_guard.py` fails
   without them). Run pytest from `<scratch>/cascor/src`. Imports resolve from the copy when it is
   the cwd / `--app-dir` (verified: `api`, `cascade_correlation`, `cascor_constants` all from the
   copy).
4. **`POST /v1/training/start` accepts `{"dataset":{"generator":"spiral","params":{…}}}` in-process**
   — no juniper-data leg is needed for a cascor-only repro (params: `n_points_per_spiral`,
   `n_rotations`, `noise`, `radius`, `seed`). Other generators 422 on that route.
5. **Redirect BOTH env vars for any probe that trains**: `JUNIPER_CASCOR_SNAPSHOTS_DIR` (or the
   probe grows the archive) **and** `JUNIPER_CASCOR_LOG_DIR` (or it rotates the shared checkout's
   `logs/juniper_cascor.log`, which is how the 08-24 evidence nearly rotated away).
6. **The T6 re-baseline tripwire**: a cascor listener on **8230–8259** means the GPU campaign is
   live; do not start cascor/GPU work while it is present (the range is from the T6 owner's
   cross-session message of 2026-08-25; its handoff ml#1371 documents 8230 as the campaign's
   *minimum* port and the 8259 upper bound appears only in that message and in the repro script's
   guard — widen the guard if the campaign's allocation grows; the repro script refuses to run
   over it). The campaign also aborts if the shared cascor primary
   checkout's HEAD moves — never pull/commit there. **This session promised the T6 owner
   (`t6 rebaseline [144e1d]`) no cascor/GPU work between its LAUNCH and COMPLETION announcements;
   launch was expected ~21:00 CDT 08-25 or 05:10–07:45 CDT 08-26. The successor inherits that
   promise.**
7. **Remove your own repro residue — only when the report says it is safe.** The script's
   `shm_leaked_after_reap.txt` is a before/after diff of `/dev/shm` restricted to the two cascor
   prefixes; it is attributable to your run only because the script refuses to start while any
   host python process has a cwd inside a juniper-cascor tree (service, forkserver, worker, stack
   driver — Docker's `/dev/shm` is namespaced and not a concern) and re-checks at the end:
   `report.json` → `leak_lists_safe_to_remove` must be `true`. If it is `false`, a peer cascor
   appeared during the window and the list may name ITS pending block — do not `rm`. The script
   never removes anything itself. (This guard was added after the cold-successor review; the two
   archived runs predate it but were verified peer-free by hand — no host cascor process existed
   and the deploy stack is containerised.)
8. **`open_signed_pr.py --dry-run` prints the base sha it will pin** — ml `main` moved from
   `45c2f4fc` to `1ac6e767` during this session; re-run the staleness guard
   (`git diff --stat origin/main -- <path>`) immediately before the real call.

---

## 5. Verification commands

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper
WT="$JUNIPER/juniper-ml/.claude/worktrees/buzzing-beaming-raccoon"   # or your own
PY=/opt/miniforge3/envs/JuniperCascor1/bin/python

gh pr list --repo pcalnon/juniper-ml --state open        # dup-guard
gh pr list --repo pcalnon/juniper-cascor --state open    # #584 collision check

# the ledger — must not grow across stops once the fix is deployed
ls -1 /dev/shm | grep -c '^juniper_train_'   # 10 at handoff
ls -1 /dev/shm | grep -c '^sem.mp-'          # 90 at handoff

# uvicorn behaviour (3 s, no GPU, ports 18991-18993)
$PY "$WT/util/ad-hoc/uvicorn_sigterm_atexit_probe.py"

# the live repro / fix verifier (GPU, ~1 min; refuses over a T6 listener on 8230-8259)
#   <cascor-src>  = a scratch copy's src/ (patched or not), NEVER the shared checkout
bash "$WT/util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash" <cascor-src> <run-dir> 8209
#   it refuses (exit 6) while any host python process sits in a juniper-cascor cwd, and (exit 5) over a T6 listener
#   then, ONLY if <run-dir>/report.json has "leak_lists_safe_to_remove": true (§4 trap 7):
sed 's|^|/dev/shm/|' <run-dir>/shm_leaked_after_reap.txt | xargs -r rm -f
```

Rebuilding the patched tree (the scratch copy is session-scoped and reaped — §6): do the two
rsyncs of §4 trap 3 into `<scratch>/cascor/`, then apply #589 on top:
`gh pr diff 589 --repo pcalnon/juniper-cascor > /tmp/589.diff && patch -p1 -d <scratch>/cascor < /tmp/589.diff`
(or fetch the five files at the PR head with `gh api repos/pcalnon/juniper-cascor/contents/<path>?ref=<head-sha>`).
Confirm with `grep -c _release_network_resources <scratch>/cascor/src/api/lifecycle/manager.py` (≥ 1)
and the same grep on the primary checkout (0 until the merge is pulled).

Cascor gates as run this session against the patched scratch copy (from its `src/`):
`$PY -m pytest tests/unit -q --slow` → **4,895 passed, 0 failed/skipped** (exit 0; the count is a
dot-count of the progress lines — `pyproject.toml`'s addopts already carries `-q`, so the extra
`-q` suppressed pytest's summary line; drop the flag or pass `-o addopts=""` to get it; the first
attempt stopped on the scratch-tree artifact of §4.3) and
`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CASCOR_NUM_PROCESSES=1 $PY -m pytest -m golden --golden --slow --integration tests/integration/test_golden_trajectory.py`
→ **1 passed**. Lint per the cascor hooks: black 25.1.0, isort, flake8 (src and tests args, bugbear),
ruff `--select ASYNC` — clean on the five files.

---

## 6. Git state

- juniper-ml `origin/main`: `1291e839` at handoff (moved three times this session — `45c2f4fc` →
  `1ac6e767` → `1291e839`; re-probe).
  juniper-cascor `origin/main`: `d2d1069763` (the fix PR's base; local primary checkout == it).
- Work was done in `juniper-ml/.claude/worktrees/buzzing-beaming-raccoon`, branch
  `worktree-buzzing-beaming-raccoon`, on top of `45c2f4fc`. Local, uncommitted, **ALL SEVEN carried
  by the ml PR** (verify with `gh pr view <N> --repo pcalnon/juniper-ml --json files`): the §6.5
  doc edit, `util/ad-hoc/uvicorn_sigterm_atexit_probe.py`,
  `util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash`, the three files under
  `reports/stop-during-training-2026-08-25/`, and this handoff. If any is missing from the PR it
  exists nowhere else — the standing cleanup procedure removes this worktree.
- **The scratch trees are ephemeral** (`/tmp/claude-1000/…/scratchpad/{cascor,cascor-unfixed,repro}`:
  the patched tree, the fail-first variant, and both repro runs' FULL cascor logs and descendant
  censuses — only the two `report.json` files and the probe JSONL were archived; `/tmp` is reaped).
  The durable copy of the fix is the PR branch: `gh pr diff 589 --repo pcalnon/juniper-cascor`, or
  `git fetch origin fix/shutdown-joins-training-before-sigterm-exit` in a cascor worktree. Amend
  with `util/ad-hoc/2026-08-22_amend_signed_pr.py` from a re-derived tree, never from a stale copy.
- PR numbers: **cascor#589** (signed commit `5bb4a2f2`, opened 2026-08-25 ~19:35 CDT); **ml — the PR
  that carries this handoff** (its number is not knowable from inside itself; `gh pr list` shows it).
- `required_signatures` is live fleet-wide: everything lands through `util/open_signed_pr.py`
  (whole files — re-check the staleness guard first) or `util/ad-hoc/2026-08-22_amend_signed_pr.py`.
- A memory note was written: `reference_uvicorn_sigterm_reraise_skips_atexit`.

---

## 7. Validation record

Reviewed by three independent agents, each prompted to **refute** (the project's multi-agent
adversarial SOP), against the draft as first written:

| lens | found | incorporated |
|---|---|---|
| **amputation** (a fork with the session's full context) | **2 blockers, 9 major, 8 minor.** The handoff file itself was missing from the ml PR's file list (it would have existed nowhere once the worktree was cleaned); PR numbers were placeholders; "verified live" overstated what an isolated, output-phase-only repro showed; the fix cannot reach the host until the primary checkout is pulled, which the T6 agreement forbids mid-campaign; a new ledger pair was attributed to one cause when three are possible; the rsync recipe as abbreviated would have copied the protected snapshot archive into `/tmp`; the scratch trees are ephemeral and were the only copy of the full repro logs; the predecessor's §5–§8 and the ml#1340 collision had been dropped; the budget claim omitted the liveness join. | all 19 |
| **cold successor** (fresh agent, executed §5 read-only) | **1 blocker, 1 major, 8 minor.** The blocker was real and in the *script*, not the prose: `shm_created_by_run.txt` was a raw before/after diff of all of `/dev/shm`, so a peer cascor's entries could be mis-attributed and then `rm`'d by the residue step — fixed with a cwd-keyed peer-cascor guard (refuse at start, re-check at end, `leak_lists_safe_to_remove` in the report) plus prefix filtering. The major: the patched tree had no stated durable location or rebuild recipe (now §5/§6). Minors: two "§6.4" mis-citations, the #584 overlap overstated (only `manager.py`, hunks far apart, no test-file overlap), the fleet audit is empty as scoped (zero `atexit` hits in data/canopy/recurrence), absolute ledger counts vs "one new pair", the 08-24 evidence file not named. It verified every number in §1's table, the git state, uvicorn 0.46.0, `allow_auto_merge` on both repos, and reproduced the sandbox trap (§4.3) verbatim. | all 10 |
| **factual re-probe** (fresh agent, re-derived every number from the sources; 94 tool calls) | **3 wrong, 11 softer.** Wrong: "~0.2 s *after the stanza returns*" (the 0.2 s is SIGTERM→death; death follows the stanza within ms — the same error sat in #589's docstring and the memory note, both corrected); "the predecessor's §6.4 item 2" (it is the characterisation note's §6.4 / the predecessor's §2.4); "the fleet runs 0.46.0" (0.40 / 0.46 / 0.49 across host envs, 0.52.4 in every lockfile). Softer: the "+1.5 s" escalation is 1 s + 0.5 s *per stuck worker*, not a bound; "real GPU training" is unverifiable from the logs; the 8259 tripwire bound comes only from the T6 owner's message; trap 3's trigger list was wrong in detail; the fail-first run was not archived (now `reports/…/fail_first_unfixed_shutdown_tests.log`); the unit count is a dot-count from a `-qq` run. It independently re-ran the probe and the fail-first tests, confirmed every repro number byte-for-byte against the run dirs, and confirmed the fix diff matches §2 exactly. | all 14 |

Three lessons this round: (1) the only BLOCKER that could have damaged something was in a
*script*, and only the lens that executed the document found it — prose review would not have;
(2) the amputations were all in the operational envelope around a technically sound core, which
is exactly where a successor gets hurt; (3) the three lenses overlapped on almost nothing — and
the one factual error that had already propagated into shipped code (the docstring's "a few
hundred milliseconds after this method returns") was caught only by the lens that re-measured
instead of re-reading.
