# HANDOFF 2026-08-26 — the perf lane after the live re-measure: #586 / #570 / #579 closed on counts, F3 landing, parity decisions remain

Successor to
[`HANDOFF_2026-08-25_perf-lane-closeout-563-attributed-586-570-568.md`](HANDOFF_2026-08-25_perf-lane-closeout-563-attributed-586-570-568.md).
That handoff's §3 work order is **measurement-closed**: items 1 (§3.1, both live re-measures),
2 (§3.2, the F3 fork-safety audit — and the preload PR is open with its verification) and 3
(§3.3, the post-#563 worker profile) are DONE with evidence; items 4 (§3.4 parity decisions) and
5 (§3.5 owner-timed) are unchanged and owner-gated. Its §4 hazards and §5 inherited list, and the
2026-08-24 predecessor's §3/§4.8/§5/§6 behind them, are **inherited by reference** (§5 below).

"§N" means a section of this document; "pred. §N" means the 2026-08-25 predecessor. Commands run
from the juniper-ml repo root unless stated. Every number below was measured **2026-08-26 at
cascor `67d7ea35`** (= #587 + #588 + #589; the SHA T6 pinned), on a shared host, as a COUNT with
vacuity controls wherever the predecessor demanded one.

---

## 1. What is settled — do not re-measure

| finding | evidence | status |
| --- | --- | --- |
| **The #586 shutdown tax is gone.** k=4 paired `e-k-thread-probe-cap16`, arms interleaved, both at `67d7ea35`: `did not stop gracefully` = **0 in all 4 CLI legs and all 4 service legs** (was 7/7 per CLI leg at `c4bbe815`); CLI `train_other` 37±1 → **0±1 s**; CLI total logged 112±10 → **63±6 s**; service 103±14 → 83±5 s; total-logged ratio **0.76** (63/83; the service is long-lived, so it has no process wall to compare) — the CLI now spans *less*, the service does more candidate (+5 s) and output (+8 s) work. The count is the acceptance criterion: #587's shared 5 s deadline alone would have capped the *time* even if the feeder-flush fix were wrong | [#571 comment](https://github.com/pcalnon/juniper-cascor/issues/571#issuecomment-5428971649); `reports/perf-lane-post-fix-2026-08-26/g4_*` | **#571 CLOSED**; register G4 CLOSED. Cite as "**#587 with #588** removed the shutdown tax" — the run is joint (#587+#588+#589); the solo `76f4d51b` run was deliberately not spent because 0/28 is unambiguous |
| **The #570 forkserver leak is closed.** Census on the fixed build (same cap-4 cell as the pre-fix run; auditor + `_diag_hot` extended to watch `sentry_sdk`; DSN present by value): exactly one ledger (the forkserver, `FINAL modules=1094`, torch+numpy), **zero child ledgers** (was 7), every worker enters `_worker_loop` at **1,166** modules (was 1,872; bound 1,400) with `present=['torch','numpy']`, **no `sentry_sdk` in any worker** | [#570 comment](https://github.com/pcalnon/juniper-cascor/issues/570#issuecomment-5429032512); `reports/…/census_at67d7ea35_*` | **#570 CLOSED**; G6 CLOSED. The service arm was NOT censused (its `__mp_main__` is the uvicorn entry; #588 changes it only via the lazy plotter) — optional follow-up, not a gap in the closure |
| **#579 worker profile RUN.** cProfile, 32 profiles per corpus, like-for-like: `inspect` family **52.17 % → 0.88 %** of worker self time (≈98 % → ~1 % counting the `hasattr`/`isinstance`/`dict.get` storms `getmodule` drove); total self time 3,994 → 85 s. #563 reached the worker path | [#579 comment](https://github.com/pcalnon/juniper-cascor/issues/579#issuecomment-5429051993); `reports/…/worker_profile_*` | **#579 CLOSED**; G2 annotated. **Side-finding for #573:** ~30 % of what remains is logging-related — `logger.py` 18 % (`_is_valid_level_name`, `_log_at_level`, per-record `open`/`strftime`) + tensor `__format__`/`_tensor_str` ~12 % (1.8 M `__format__` calls from f-strings in log lines) |
| **F3 (#569) fork-safety audit DONE**: 34-module first-party closure, 29 import-time statements all reviewed — no open handle, thread, lock, socket, CUDA context, RNG seed, `atexit` or environ write at import. **Preload verified live**: with the entry, forkserver `FINAL modules=` **1,094 → 1,157** (≥ the 1,155 predicted), workers unchanged at 1,166, zero child ledgers | [#569 audit](https://github.com/pcalnon/juniper-cascor/issues/569#issuecomment-5428849758); [#569 PR link](https://github.com/pcalnon/juniper-cascor/issues/569#issuecomment-5429135208); scanner `util/ad-hoc/2026-08-26_fork_safety_import_surface.py`; `reports/…/census_at67d7ea35_preload_verification_*` | **MERGED as cascor#592** (`3697101e`, 2026-08-26 18:15Z; #569 closed). Worth ≲2 s/run (`pool_setup` 2±0 s at cap 16) — cleanliness, not speed |
| The service's post-fit "teardown" reads **5±1 s (was 2±1)** in the G4 table | `Training ended` → lifespan shutdown lines, service leg logs | **Not pool work**: #589 now *logs* the lifespan shutdown (`TrainingLifecycleManager shut down (0.00s)`), so the segment includes `run_suite`'s completion-poll → SIGTERM latency that the SIGTERM re-raise used to cut off. Do not chase it |
| **T6 re-baseline COMPLETE** 2026-08-26 03:58 CDT — 23/23 cells, `worst_rc=0`, `67d7ea35` held; completion announced to this session by name at 12:31 CDT; hold released, checkout freeze lifted | `~/.local/state/juniper-experiments/t6-campaign-20260826T075112Z.out` (`CAMPAIGN COMPLETE`), T6's closing handoff ml#1393 | **No T6 window to wait for any more.** The primary `Juniper/juniper-cascor` sits at `67d7ea35`, clean, **one commit behind `origin/main`** (`3697101e` = #592). Advancing it is routine again — but not while a live service runs from it (`ls -l /proc/[0-9]*/cwd 2>/dev/null \| grep -c juniper-cascor/src` > 0: the canopy-E2E cascor on :8202 was running from it at handoff, and a pull under a live forkserver changes what its children re-import) |
| Tensor-hash probe (2026-08-24 handoff §4.2 — not the 2026-08-25 §4.2, which is the `git stash` hazard) is now recorded on **both** #582 and #572 | [#572 comment](https://github.com/pcalnon/juniper-cascor/issues/572#issuecomment-5422774072) | precondition for §3.4 met; the probe itself was NOT run |
| Determinism attribution (pred. §1 rows 1–4), ad-hoc retention policy, `#566` corollary UNTESTED | pred. §1 | unchanged — do not resurrect or re-test |

### 1.1 Documents this handoff is shorthand for

pred. §1.1's table unchanged ("evidence note", "register", "residual note", "fix design", "§12 perf
lane"), plus **"the reports dir"** = juniper-ml `reports/perf-lane-post-fix-2026-08-26/` (13
artifacts: G4 analysis text + decomposition JSON + legs + provenance; census controls, forkserver
ledgers, DIAG-ENV lines, provenance ×2; worker-profile diff + inspect-share). **Five of them are
`.log` files, which `.gitignore:52` (`*.log`) excludes and `git status` is blind to — they were
committed with `git add -f`; do the same for any future `.log` evidence.**

---

## 2. Merged / filed this arc (verify — concurrent sessions merge constantly)

| item | what | state at handoff |
| --- | --- | --- |
| **cascor#592** | `fix/569-forkserver-preload-trainer` @ `08065c5` (signed, ONE commit): the preload entry, the comment fix, `src/tests/unit/test_forkserver_preload_569.py` (4 guards, incl. the importability check — CPython swallows preload `ImportError`s). junit 7/0/0 with the #568 probes; flake8/black/isort clean; `juniper-cascor-model` mirror untouched | **MERGED 2026-08-26T18:15:04Z as `3697101e`** via the native auto-merge net (`--squash --auto`, explicit subject/body) under Paul's 2026-08-26 approval ("all PRs in this session and work arc"); #569 auto-closed (completed); `origin/main` verified to carry the entry and no garbled comment; fix worktree removed, local + remote branch deleted by hand (**`delete_branch_on_merge` is OFF on cascor**), `git worktree prune` run |
| **juniper-ml PR** (this handoff's) | branch `perf/post-fix-remeasure-2026-08-26` off `19207308`: 5 `util/ad-hoc/` scripts (§6), register rows G2/G4/G5/G6, the reports dir, this handoff — ONE signed commit (amended) | opened after this validation pass; native auto-merge armed under the same approval |
| cascor#571, #570, #579 | closed with the evidence comments above | CLOSED |
| cascor#569 | retitled ("fork-safety audit DONE 2026-08-26; land after the post-#588 census (#570) reads clean"); audit + PR-link comments | CLOSED (completed) by #592's merge |
| cascor#572 | tensor-hash probe comment | OPEN (decision) |
| ml#1393 | T6's closing handoff (another session) | was OPEN at handoff time |

---

## 3. OPEN WORK — ordered

| # | item | gate |
| --- | --- | --- |
| 1 | **#592 is landed and cleaned up — nothing left** (§2 row 1). For the ml PR (item 2) and any future cascor PR: checks via `gh pr view N --repo pcalnon/<repo> --json statusCheckRollup,reviewDecision,mergeStateStatus` (`reviewThreads` is NOT a valid `--json` field on this gh build — the whole call errors); unresolved CodeQL threads, which block a merge while the rollup reads green, via `gh api graphql -f query='{repository(owner:"pcalnon",name:"<repo>"){pullRequest(number:N){reviewThreads(first:50){nodes{isResolved path}}}}}'` | — |
| 2 | **Land the ml PR** (this handoff) | CI + the approval already given |
| 3 | **§3.4 parity decisions — #582 / #572 / #530 / #578** (pred. §3.4, unchanged). The arms are each deterministic but disagree (11,310 vs 13,140 candidate epochs at cap 4; 46,970 vs 53,590 at cap 16). The first *action* is the tensor-hash probe, now specified on both issues; **nothing else should be built until it has run**. #578 (baseline-tier decision) depends on the outcome | owner picks an option per issue |
| 4 | **#573 logging redesign** — design doc first. Feed it three findings: the 2026-08-24 handoff §4.13's two (`_log_at_level`'s per-record `open()`, the unconditional `print()` — the 2026-08-25 document has no §4.13) and §1 row 3's new one (~30 % of post-#563 worker self time is logging: `logger.py` 18 % + tensor formatting ~12 %, 1.8 M `Tensor.__format__` calls) | owner-timed |
| 5 | **#550** CodeQL unused-global on juniper-cascor-model — Wave 2 adoption | owner |
| 6 | **Deferred, inherited (2026-08-24 handoff §4.8, carried through 2026-08-25 §5)**: cap-series re-measure post-F1 (now genuinely cheap — today's cap-16 k=4 paired campaign took **~11 min** end to end: 10 m 53 s from `provenance.json`'s `started_utc` to the CLI stack's `torn_down_utc`); cap-128 3-seed spread (cost-gate first, the 637 MB cap-64 log); retrospective corpus re-validation (**raise with the owner, do not absorb**); #566's "a slow cell would re-diverge" corollary (cap-64/128 N≥10 falsifier, never run); optional service-arm census (§1 row 2) | T6 is done — host is shared, not exclusive; coordinate with live peers via `ListAgents` before any multi-hour campaign |
| — | cascor#590 (CUDA-OOM classified as a 0-unit stall) is the canopy-E2E arc's, not this lane's | — |

### 3.1 How to re-run any of today's measurements (one command each, all detached-safe)

```bash
# G4 paired campaign (CLI worktree at the primary's SHA; ~11 min at cap 16 k=4) — then the analysis:
bash util/ad-hoc/2026-08-21_detach_campaign.bash <LOG> bash util/ad-hoc/2026-08-21_h2h_paired_campaign.bash <WT>/src util/experiments/suites/p4/e-k-thread-probe-cap16.yaml 4 <NEW_OUT_ROOT>
python3 util/ad-hoc/2026-08-26_g4_post_fix_analysis.py <OUT_ROOT>        # resolves service legs from legs.jsonl; counts ungraceful stops per leg; runs the decomposition
# Census + worker profile on one cap-4 cell. Needs the auditor: `git cherry-pick 67d7ea35..diag/census-at67d7ea35-0339`
# — all THREE commits (05a8272 auditor, 2eab062 sentry_sdk in both tuples, bbf03da preload entry); the tip alone is only
# the preload line and the runner refuses without cascor_diag_import_audit.py:
bash util/ad-hoc/2026-08-21_detach_campaign.bash <LOG> bash util/ad-hoc/2026-08-26_census_post588_run.bash <CWT>/src <CELL> <NEW_OUT_ROOT> 360
python3 util/ad-hoc/2026-08-26_worker_profile_inspect_share.py pre563 ~/.local/state/juniper-experiments/profile-cap4/prof-cli post <OUT_ROOT>/prof
# Watch any detached launch as a harness Monitor (emits progress; exits on the done/fail marker or pid death):
bash util/ad-hoc/2026-08-26_watch_detached_launch.bash <LOG> '<done regex>' '<fail regex>' '<progress regex>' 10
# Fork-safety screen of any entry module's first-party closure:
python3 util/ad-hoc/2026-08-26_fork_safety_import_surface.py <cascor>/src cascade_correlation.cascade_correlation
```

---

## 4. Hazards this arc created or confirmed — NEW ones only; pred. §4 and its predecessor's §3 still apply

### 4.1 `2026-08-14_r5_stack_up.bash` is not executable — invoke it with `bash`

A direct call fails with `Permission denied` → "stack bring-up failed" (the census runner's
first launch died this way; its watcher's FAIL marker caught it in 10 s). The runner now invokes
it via `bash`. Every other ad-hoc launcher the handoffs quote is invoked with `bash` for the same
reason — keep doing that.

### 4.2 The worktree-isolated command guard refuses more than loops

`for`, pipes with `${PIPESTATUS}`, `[ … ]`, `${#VAR}`, `cd … &&` — refused even over scratchpad
files. What passes: plain commands, `&&` chains, `sed -i`, `git -C <sibling>` single operations,
`python3 script args`. So every multi-step procedure this session needed became a `util/ad-hoc/`
script (five of them, §6) — which is also what the script-placement rule wants.

### 4.3 Two sessions editing `MEMORY.md` at once: a `sed` on the previous wording silently no-ops

The T6 session rewrote the same index lines twice in the minutes I was editing them; my first
substitution matched nothing and the command still exited 0. **Count the replacement** (`grep -c`
the new text afterwards) and re-read the current line before substituting.

### 4.4 A completion announcement can arrive hours late; the campaign's own terminal line is authoritative

T6 finished at 03:58 CDT; its session was not woken until 12:30 and this holder session was idle
until told to resume ~9 h later. The campaign log's `CAMPAIGN COMPLETE … worst_rc=0` line, plus
quiet tripwires, is sufficient to proceed **after telling the peer by name and giving it a tool
round to object** (it confirmed). "Not started" and "finished" are only indistinguishable when
no campaign log exists.

### 4.5 A negative on an unwatched package is vacuous

The shipped diag auditor watched neither `sentry_sdk` in `_WATCH` nor in `_worker_loop`'s
`_diag_hot`; both edits live on `diag/census-at67d7ea35-0339` and the runner's pre-flight greps
for them. Any future census that asserts "no X in workers" must first confirm X is in both tuples.

### 4.6 bandit reads free text after `# nosec B404` as test IDs

`# nosec B404 -- rationale` makes bandit warn "Test in comment: rationale is not a test name" for
every word (exit still 0, suppression still applied — the memory's comma trap is the *silent*
variant). Bare IDs on the marker; rationale on its own line above.

### 4.7 The G4 decomposition's service "teardown" now contains harness latency (§1 row 5)

Any future service-arm table must subtract or annotate the `Training ended` → lifespan-shutdown
gap (~5 s of `run_suite` polling) before comparing teardown across builds that straddle #589.

---

## 5. Inherited by reference — READ THE PREDECESSORS for these

- **pred. §4.1–4.6** (script-specific completion markers; `stash push -u` takes untracked tests;
  timestamp partitioning; the T6 protocol — now moot but its port/lockdir/cwd gate is still the
  right pre-flight; pytest summary swallowed; truncated reference sweeps) — all still true.
- **pred. §5** in full (golden reset, evidence-preservation rules, orphan reaper, cascor-model
  mirror, sequence-safety waiver, working-tree revert blindness, `GOLDEN_CAPTURE=1`, corrected
  numbers, eliminated hypotheses, py-spy ancestor rule, `--down --all-mine` scope, required-context
  names, methodology rules). **New preserve roots this arc** (the 2026-08-24 handoff §3.2 rules, inherited via
  2026-08-25 §5; no `registry.jsonl` references the three STACK dirs, but each is recorded inside
  its own out-root — `provenance.json`'s `STACK_RUN_ID` or the `stack_run_id` file):
  `g4-paired-cap16-at67d7ea35` (+ its 68 copied-out `.h5` under `cli-snapshots-from-worktree/`;
  the four service legs are **top-level run dirs** `20260826T173406Z-a1e0`, `20260826T173653Z-8ccf`,
  `20260826T173943Z-6b8d`, `20260826T174228Z-4b5d`, linked from
  `suites/e-k-thread-probe-cap16-20260826T17{3406,3653,3942,4228}Z/registry.jsonl` — note the
  third suite stamp is `3942`, the run dir's is `3943`; CLI stack `20260826T173539Z-6f17`),
  `census-at67d7ea35` (+ 20 copied-out `.h5`; stack `20260826T174914Z-48e8`),
  `census-at67d7ea35-preload` (stack `20260826T175816Z-77c3`), and T6's `t6-rebaseline-20260826T075112Z`.
- **pred. §1.1** (document shorthands) / **2026-08-24 §1.8** (terms); the option lists on **cascor#578 and #582 themselves** (pred. §3.4: "each issue lists them" — no handoff section carries them).

---

## 6. Operational notes

- **Approval**: Paul granted "merge approval for all PRs in this session and work arc"
  (2026-08-26). It covers #592 and the ml PR; it does **not** cover the Cursor-fleet PRs
  (cascor#583/#584, ml#1332–#1346) or anything another session opens.
- **Landing path** (memories are explicit): keep a PR at ONE commit (squash ships the first
  commit's diff when history is messy); arm GitHub's native net —
  `gh pr merge N --repo pcalnon/<repo> --squash --auto --subject '<subject> (#N)' --body-file <body>`
  then confirm `state=OPEN armed=true`; never report a merge on `safe_merge`'s exit code — look
  for `mergedAt`. `python3 util/wait_for_checks.py --pr N --repo <repo> --anchor required` is the
  waiter if a foreground wait is wanted (≤ 3300 s; bg tasks die at the ~3600 s lease).
- **Host**: shared, not exclusive, throughout today's runs (load1 4–25 from peer sessions; the
  canopy-E2E trio 8202/8101/8051 came up mid-campaign). Counts were unaffected; absolute seconds
  are not comparable across days. Gate any heavy launch on the pred. §3.1 pre-flight (ports
  8110–8139 / 8230–8259 / 8260–8289, lockdirs, `/proc/*/cwd` on `juniper-cascor/src`) and tell
  live peers (`ListAgents` names them) before multi-hour work.
- **Env**: `/opt/miniforge3/envs/JuniperCascor1` (py 3.13.13, torch 2.11.0+cu130); black/isort
  are NOT in it — use `/opt/miniforge3/bin/black -l 512` and `/opt/miniforge3/bin/isort --profile black -l 512`.
- **New tooling on the ml branch** (`util/ad-hoc/`, all RETAINED per policy):
  `2026-08-26_fork_safety_import_surface.py` (static fork-safety screen of an import closure),
  `2026-08-26_watch_detached_launch.bash` (Monitor-friendly watcher: done/fail regex + pid death),
  `2026-08-26_g4_post_fix_analysis.py` (ledger-resolved service legs + ungraceful-stop counts +
  decomposition), `2026-08-26_census_post588_run.bash` (two-leg census/profile runner with printed
  controls; refuses a reused OUT_ROOT, a missing DSN, or unwatched `sentry_sdk`),
  `2026-08-26_worker_profile_inspect_share.py` (share of worker self time by file, inspect family).
- Concurrent sessions at handoff: canopy e2e, defect register, p5 ports, t6 rebaseline (done),
  cascor stop fix, memory budget, duplicati. **Re-derive; do not trust this list.**

---

## 7. Worktrees and branches — state at handoff

| item | state | action |
| --- | --- | --- |
| `worktrees/juniper-cascor--fix--569-forkserver-preload-trainer--20260826-1252--67d7ea35` | **removed this session after #592 merged**; local and remote `fix/569-forkserver-preload-trainer` deleted; `git worktree prune` run | none |
| `worktrees/juniper-cascor--exp--g4-at67d7ea35--…` and `…--diag--census-at67d7ea35--…` | **removed this session** after copying their 68 + 20 `.h5` to `g4-paired-cap16-at67d7ea35/cli-snapshots-from-worktree/` and `census-at67d7ea35/cli-snapshots-from-worktree/` | none |
| cascor local branch `diag/census-at67d7ea35-0339` (`05a8272` cherry-pick of the auditor → `2eab062` sentry edits → `bbf03da` preload verification) | **local-only provenance ref** for the #570 census, the #579 profile and the #569 verification; NOT for merge | keep; never push, never delete without updating this table. Joins `diag/forkserver-import-audit` and `diag/seed-instability-at-56{2,3,5}` (pred. §7) — **the former**, `diag/forkserver-import-audit`, still tracks `origin/main` (`[origin/main: ahead 1, behind N]`): never `git pull` with it checked out. This new branch and the three seed-instability branches have no upstream |
| pred. §7's other rows (`rescue/*` worktrees with 28 `.h5`, `exp--determinism-postarc` / `fix--logger-frame-resolution` / `exp--residual-wall-gap` with 100/73/450 `.h5`) | **unchanged**, all still present | owner's call, exactly as pred. §7 states — copy `.h5` out before any removal |
| this session's ml worktree `.claude/worktrees/clever-conjuring-hanrahan` | branch `perf/post-fix-remeasure-2026-08-26` off `origin/main` `19207308` | the ml PR |
| `Juniper/juniper-cascor` primary | `67d7ea35`, clean, **one behind** `origin/main` `3697101e` (#592) | no freeze; pull it when no live service runs from it (§1 row 6) |

---

## 8. Verification commands

```bash
gh pr view 592 --repo pcalnon/juniper-cascor --json state,mergedAt,mergeCommit   # MERGED 2026-08-26T18:15:04Z, 3697101e
gh api repos/pcalnon/juniper-cascor/issues/571 --jq .state; gh api repos/pcalnon/juniper-cascor/issues/570 --jq .state; gh api repos/pcalnon/juniper-cascor/issues/579 --jq .state   # closed ×3
gh api repos/pcalnon/juniper-cascor/issues/569 --jq .title    # "…fork-safety audit DONE 2026-08-26…"
# Re-derive today's numbers from stored evidence (seconds each; NO training):
python3 util/ad-hoc/2026-08-26_g4_post_fix_analysis.py ~/.local/state/juniper-experiments/g4-paired-cap16-at67d7ea35 | grep -E 'TOTAL|train_other|mean'   # TOTAL cli=0 service=0; CLI train_other 0±1
grep -H 'FINAL modules=' ~/.local/state/juniper-experiments/census-at67d7ea35/audit-logs/*.log ~/.local/state/juniper-experiments/census-at67d7ea35-preload/audit-logs/*.log   # census-at67d7ea35/…3487362.log: 1094; census-at67d7ea35-preload/…3524806.log: 1157 (the session shell's grep is an ugrep shim that reorders output — -H labels each line)
grep -c 'DIAG-ENV' ~/.local/state/juniper-experiments/census-at67d7ea35/cli-01/logs/juniper_cascor.log   # 7 (each sys_modules=1166)
python3 util/ad-hoc/2026-08-26_worker_profile_inspect_share.py post563 ~/.local/state/juniper-experiments/census-at67d7ea35/prof | grep 'inspect family'   # 0.88 %
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor branch -vv | grep -E 'diag/census|fix/569'
# Host state before ANY heavy run (pred. §3.1 / §8 gate, unchanged):
ss -ltn | awk 'NR>1{split($4,a,":"); p=a[length(a)]+0; if ((p>=8110&&p<=8139)||(p>=8230&&p<=8259)||(p>=8260&&p<=8289)) print p}'; ls -1 /run/user/1000/juniper-experiments; ls -l /proc/[0-9]*/cwd 2>/dev/null | grep -c 'juniper-cascor/src'
```

---

## 9. Validation record

Written per `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`. Validation per
the 2026-08-23 multi-agent adversarial SOP was **partial**: round 1 launched three independent
lenses (rubric re-probe of every path/SHA/number; adversarial fact-check against raw evidence and
code; fresh-session executability), each prompted to refute, none shown another's verdict — but
**only the rubric re-probe completed** (17 findings: 10 major, 7 minor, 0 critical; dominated by
`pred. §N` references inherited verbatim from the 2026-08-25 predecessor that resolve to the wrong
document under this document's own convention, plus the `.gitignore *.log` evidence exclusion —
**all 17 applied, none rejected**; details in the ml PR body). The adversarial fact-checker and the
executability auditor were terminated by an API usage-credit error before reporting, and **round 2
was not run** for the same reason. Treat this document as validated by ONE lens, not three; re-run
the SOP (`Agent` × 3, refute-prompted, then a round 2 on the fixes) when credits allow — the
fact-checker's brief (attack the count-vs-time reasoning, the teardown artifact, the 72-module
arithmetic, the like-for-like profile comparator, T6's completion) is the highest-value one.
