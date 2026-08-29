# HANDOFF 2026-08-25 — T6: window-coordination day; the campaign is STILL not launched

Successor to
[`HANDOFF_2026-08-24_t6-rebaseline-campaign.md`](HANDOFF_2026-08-24_t6-rebaseline-campaign.md)
(as amended by the ml#1355 banners). That document remains **canonical** for T6's rationale (§1),
the do-not-resume rule (§1.3), the budget table, the trap catalogue (§2), **its §0 decision
record** — L-2 in particular: the `max_epochs=2000 is set without output_epochs` manifest warning
fires on **every E-A cell** and is expected noise, not a failure — **and its §4 merge-trap
paragraph** (its SHAs and open-PR list are dead; its rules — `util/safe_merge.py` mandatory,
waiver-trailer carried into the squash commit, the three `gh` traps — are not). This document
owns the **delta**: what the 2026-08-25 session did, the live coordination obligations it leaves
behind, the launch tooling it built, and the traps it added. Read the predecessor FIRST; nothing
here re-derives it. Its rules stand — anchors move: **locate by pattern, never by line number**.

**Bottom line: zero T6 cells have run.** The campaign was staged, verified (200/200 driver-suite
tests OK under JuniperCascor1 Python 3.13.13, the attempt-1 provenance interpreter), and then
held all day — first behind peer-session GPU work, then behind host maintenance, then behind a
daytime load floor (~5) that never met the quiet bar. Attempt 1 (2026-08-23) remains
reference-only; the do-not-resume rule stands.

**Validation:** three independent agents, one adversarial round, distinct refutation lenses —
citations/anchors PASS (1 minor); coverage/amputation FAIL (1 major, 6 minor); executability
FAIL (2 majors, 7 minor). All 17 findings are folded into this revision; §9 records the majors
and the chosen remedies. No factual claim was refuted.

---

## 0. What the 2026-08-25 session did (05:05 → 17:50 local; all dates 2026-08-25 unless said)

Chronology, kept because it produced live obligations (§3) and new traps (§5):

- **05:05** — pre-flight: host quiet (load15 **2.09**) but GPU at 4404 MiB — two orphan
  forkserver cohorts (~34 procs × 116 MiB, started 22:56 / 23:42 the previous evening) left by
  the overnight E2E-trio cascor services. The documented GPU-leak class.
- **05:10** — mid-probe, the "defect register" session brought up an experiment stack
  (`~/.local/state/juniper-experiments/20260825T101004Z-1ccb`, cascor `:8230` / data `:8110`)
  plus a `forkserver-audit-c4bbe815` state dir.
- **~05:14 and ~06:20** — ran `util/reap_pytest_orphans.bash` FOR REAL, two passes: 30 + 4
  orphans reaped, ~3.9 GiB GPU freed. The audit stack was pidfile-PROTECTED and untouched. The
  reaper's candidate predicate is **Python-only** (grep `Collect candidate PIDs` in the script),
  which matters two bullets down.
- **05:13:35** — the overnight duplicati backup (`backup-20260824-222158`, started 22:21 the
  night before) **died rc=143 (SIGTERM)** while still counting files (~678k / 187.7 GiB).
  Sender unattributed — the reaper is exonerated by its Python-only predicate; candidates were
  the audit session's prep window, a runtime limit, or one of 3 logged-in users. Since
  superseded: ml#1369 certified the first complete verified restore point later that day.
  Backup triage belongs to that arc, not T6.
- **05:16–05:17** — the audit stack tore down (graceful; `teardown.json`) and the freed window
  was **sniped in ~40 seconds**: the "cli vs service" session launched `g4-paired-cap16`
  (perf-lane G4 overhead decomposition, K=4 service-vs-CLI pairs, pinned `c4bbe815`) and the
  canopy-E2E session brought the isolated trio (`8051/8101/8202`) up with chrome-headless work.
  Load hit 19.7.
- **05:20–05:45** — negotiated GPU handover with both sessions (§3): g4 completed ~05:31 (4/4
  pairs, and **dropped its optional cap-4 pair round in T6's favor**); canopy-E2E tore the trio
  down at a clean boundary. **Both committed to hold CPU/GPU-heavy work "until T6 announces
  completion."**
- **06:07** — a ClamTk `clamscan` started (~84–89% CPU, ran ≥2 h); the root duplicati server
  began re-running the failed backup (84% CPU + an aescrypt helper at 44%).
- **07:46** — the v2 drain watch **false-fired on a 2-minute load1 lull** (load1 3.83 while
  clamscan and the backup both ran at 80%+; load15 was 8.31). Caught by the layered pre-flight
  BEFORE the launcher ran. v3 (load15 + hot-process gates) armed 07:47.
- **07:47 → 17:48** — v3 never fired: the daytime load floor is **~5** (desktop + session
  fleet). The only genuinely quiet period observed all day was ~05:00–05:10.

## 1. Remaining work — unchanged in substance from predecessor §1.4

1. **Claim a genuinely quiet window.** Empirically that is the **post-backup early morning**
   (~05:10–07:45): the server-scheduled nightly duplicati lane historically occupies
   ~22:20 → ~05:10, so "overnight" does NOT fire; 2026-08-25's only true-quiet period was
   05:00–05:10 (§4).
2. **Re-derive the cascor gap AT LAUNCH** and record the pin (predecessor §2.3; §4 below holds
   today's answer, which will be stale when you read it).
3. **Launch all three suites detached via the campaign driver** (§2 runbook). If the driver
   aborts exit-3 mid-campaign, apply §2's recovery rule — do not improvise.
4. **Publish the grids**: the E-C table is **replaced, not merely un-bannered** (the
   `KNOWINGLY STALE` banner's own text says the outstanding work "replaces this table"); the
   banner's closing paragraph extends the currency caveat to the published **E-A and E-I**
   grids — resolve that too when the new grids are placed (all three land in the same evidence
   doc); update F-P4-6 from INCOMPLETE to the real result and correct its "~4 minutes" (E-I
   kill time) to **5 m 07 s** (independently corroborated from `teardown.json` mtimes: 307 s).
   Anchors: grep `F-P4-6\|KNOWINGLY STALE` in
   `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md`.
5. **Attribution scope note stands** — the grids are comparable to each other; no "#514 cost
   N%" claim without the control arm F-P4-6 defines.
6. **Release the peer holds** (§3) the moment the grids are captured — this step is NEW and
   as binding as the publish.

## 2. Launch tooling — built today; the session-scratchpad originals are DEAD

Three scripts, all `util/ad-hoc/` (the driver predates today; the other two were graduated from
session scratchpad into the repo by this handoff's PR because scratchpads are reaped with their
session — the exact `/tmp/` loss class the script-placement rule exists for):

| script | role |
|---|---|
| `2026-08-23_t6_rebaseline_campaign.bash` | the driver: timestamped campaign dir, `campaign.jsonl` SHA ledger, abort-on-SHA-move (exit 3), abort-on-dirty-cascor (exit 2), suite order E-A → E-I → E-C |
| `2026-08-25_t6_watch_host_drained.bash` | sustained-drain watch: ports one-per-`ss`-call, load1 < 4 **and** load15 < 4.5, no clamscan/clamdscan/duplicati/aescrypt process > 20% CPU, GPU < 1200 MiB, 2 × 60 s streak; prints ONE line and exits |
| `2026-08-25_t6_launch.bash` | atomic claim: re-checks the gates (slightly looser: load1 < 6 / load15 < 5), activates JuniperCascor1, verifies interpreter 3.13.13, launches the driver **detached** (`setsid nohup`, fresh `~/.local/state/juniper-experiments/t6-campaign-<UTC>.out`), prints `LAUNCHED pid=… out=… ml_dir=…` |

**Runbook:**

1. Arm a Monitor task wrapping the watch script (`bash util/ad-hoc/2026-08-25_t6_watch_host_drained.bash`).
2. On fire: run predecessor §2.1 pre-flight + `bash util/reap_pytest_orphans.bash --dry-run` +
   re-derive the cascor gap (§4) + check the experiment **port-lock root** for stragglers
   (`ls "${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments"`) — the watch probes only each range's
   MINIMUM port (8230/8110/…), so a stack allocated at 8111/8231+ is invisible to it.
3. **Launch from a checkout that will outlive the campaign.** The detached driver resolves every
   suite path through the launching checkout (`ML_DIR`, echoed in the `LAUNCHED` line) for the
   full 8–12 h. A session worktree is acceptable ONLY if it will not be removed or handed off
   before `CAMPAIGN COMPLETE`; the primary checkout (once this handoff's PR is merged) is the
   safer host. Then: `bash util/ad-hoc/2026-08-25_t6_launch.bash` — any gate failure aborts with
   a printed reason and NOTHING launches.
4. Verify liftoff: the `.out` prints `campaign dir :` and `cascor pinned:`; that dir's
   `campaign.jsonl` has the `start` event; the E-A suite log begins filling; a `:823x` listener
   appears; **and the `.out` contains no `ABORT` line** — the driver emits the first three
   indicators BEFORE its dirty-cascor gate, so an instant exit-2 abort satisfies them and is
   ledger-silent; only the `.out` shows it.
5. Arm a campaign Monitor: `tail -F <campaign-dir>/campaign.jsonl` (only ~8 lines over the whole
   run) **plus a liveness probe of the LAUNCHED pid** — a kill -9 writes no terminal event, and
   silence must not read as "still running".
6. Announce the launch to the holding sessions (§3), then announce completion when done.
7. **Exit-3 recovery rule (cascor SHA moved mid-campaign):** the campaign restarts from suite 1
   at a freshly derived pin. Suites completed at the old pin demote to **reference data exactly
   like attempt 1 — do not splice them** (predecessor §1.3's one-SHA logic applies unchanged to
   this case). Do not restore the checkout to the old pin to "continue" — shared checkout,
   editable install (predecessor §2.3).

**GPU gate is 1200 MiB, not the predecessor's "~1 GiB", deliberately**: ~950 MiB of
display-memory is this host's idle floor with ZERO compute apps; the bar's intent is "no compute
residue", and 1042 MiB of pure display memory blocked a launch this morning until re-derived.

**Do not run any leg through a harness background task** (predecessor §2.2 stands; the
`setsid nohup` in the launcher is the mechanism).

## 3. Live obligations to peer sessions — DO NOT DROP

Session names/refs are from 2026-08-25 morning and **will be stale**. At launch time,
re-establish with whoever now owns each arc: via `ListAgents` **where the harness provides it**
(interactive sessions typically do; subagent contexts do not), else by asking Paul which
sessions now hold each arc. Cross-session messages can be **held for the recipient user's
approval** — never build a step that requires delivery; pair every message with an independent
tripwire. **Terminal fallback: if no mechanism reaches a holder, the release/announcement
obligation discharges by stating it plainly to Paul — by telling the owner, never by silence.**

1. **"cli vs service"** (was `[ea2159]`): completed and verified g4's teardown, dropped its
   optional cap-4 round for T6, and **holds all CPU/GPU-heavy suites until T6 announces
   completion**. Owed: that announcement (or a succession notice if T6 is reassigned).
2. **"canopy e2e phase 2"** (successor session, ref `f73927` as of 2026-08-25 evening): the
   original holder (`[780adb]`) tore down the trio + chrome-headless at a clean boundary and
   retired; its successor confirmed unprompted that **the hold transferred and stands** —
   nothing of theirs touches the GPU or brings the isolated stack up until T6's completion
   announcement, which should be addressed to that successor by name. **Their F-CANOPY-005
   live verification queues behind the hold** — leaving it dangling blocks their arc. (Refs go
   stale; if that name no longer resolves at announcement time, apply this section's terminal
   fallback.)
3. **"defect register"** (was `[3bdaa9]`): T6's message to them was **held for user approval and
   never confirmably delivered** (the 12 h idle-notice expired unanswered). If their
   forkserver-audit numbers look confused about pre-existing orphans: the two overnight cohorts
   (~34 procs, ~3.9 GiB GPU) were reaped at ~05:14, minutes after their audit began.
4. **Checkout-freeze ask — NEW and UNMET.** The holds above cover CPU/GPU-heavy *work* only;
   nothing binds any session to leave the shared cascor primary checkout un-advanced during the
   campaign — and that is exactly the driver's exit-3 trigger (cascor advanced twice within
   ~2 h of this document's 17:48 probe). At launch, ask the live peers to freeze
   `/home/pcalnon/Development/python/Juniper/juniper-cascor` (no pull, no commit, no dirty tree)
   until the completion announcement. This is a session-level courtesy ask like the GPU holds;
   if any session needs the checkout mid-window, escalate the ordering to Paul rather than
   launching into a known abort.

## 4. Live state — probed 17:48 2026-08-25 (deltas to 18:01 noted). RE-PROBE EVERYTHING.

- **No campaign, no experiment stacks, no Juniper processes** (reaper dry-run clean). Listeners:
  deploy stack `8050/8201/8211` (do not touch), duplicati server `:8300`, long-standing unknown
  `0.0.0.0:8181` (outside all experiment ranges). GPU 946 MiB = display floor.
- **Host load ~5.0 flat** (daytime floor: desktop + ~7 busy Claude sessions) — and the 06:07
  duplicati re-run was **still >40% CPU at 18:01**, i.e. the hot-process gate, not only the load
  bar, was blocking. With the nightly backup lane occupying ~22:20 → ~05:10, expect the watch to
  fire in the **post-backup early morning (~05:10–07:45)**, not overnight. Two ways to run
  sooner, **both owner calls**: quiet the desktop, or bless an unattended overnight cron of the
  launcher (its gates encode the pre-flight, but the cascor-gap READING step — §1.2 — would then
  need to be done in the evening and the pin pre-decided; do not skip it silently).
- **juniper-ml**: `origin/main` `0c974f04` and moving fast. This session's worktree
  (`twinkly-nibbling-piglet`, branch `worktree-twinkly-nibbling-piglet`) was cut at `7f3cb19`;
  the handoff PR carries this document + the two new scripts. Landed-since context: ml#1369
  (backup CERTIFIED — first complete verified restore point), ml#1361 (canopy E2E P0-sweep
  handoff), **ml#1356 (owner decision 2026-08-25: ALL `util/ad-hoc` scripts RETAINED, headers
  rewritten, retirement now exceptional). ml#1356 closes the predecessor's LAST open §0.2
  residual — the `2026-08-16_h2h_wide_nrot3.yaml` durability question — by policy. With it, all
  six §0.2 residuals are closed: #2/#4/#5/#6 via ml#1316, #3 via cascor#580, #1 via ml#1356.**
- **juniper-cascor**: checkout `fa649d0` — one commit (#585, CI-ratchet port, non-runtime) atop
  `c4bbe81`, which is itself the #581 deps bump and the exact pin the morning's g4 +
  forkserver-audit runs used (`c4bbe815…`). Gap to `origin/main` at 17:48 was ONE commit —
  **`76f4d51` / #587 "fix(pool): workers no longer hang at exit on advisory-queue flush"**, the
  same-day fix for **cascor#586** (g4's finding: direct-CLI at cap 16, 7/7 candidate workers
  fail the graceful stop, ~35 s/run serial teardown tax inside `fit()`; **service arm 0/7**) —
  and by 17:56 it was already TWO: **`d2d1069` / #588 "fix(cli): stop forkserver children
  re-running main.py's body; lazy-import the plotter"**, which touches the very forkserver class
  §0 documents. Both are runtime-flavored. The pull-vs-pin reasoning recorded this morning
  (pull = cheap comparability insurance; pin defensible on #586's 0/7 service evidence) was
  built on a #587-only gap and is **void if the gap at launch differs — re-argue from the actual
  subjects; more commits will have accumulated.** Respect predecessor §2.3's caveats (shared
  checkout, editable install, worktree-pinning REJECTED).
- **juniper-data**: **still unreleased past `fec68b4`** — newest release remains v0.11.0
  (2026-07-29), so `install_hint` is invisible to every consumer. Predecessor §0.1 residuals
  1–3 all stand (G-16 live-refusal half, driver preflight-hint consumption — the driver still
  emits the "see `GET /v1/generators`" pointer and never reads `install_hint` — and the release).
- **Publish-time interpretation guardrail**: cascor#582 (open) — the service promotes the
  dataset's `X_test/y_test` to in-loop validation; the direct CLI trains with no validation
  data at all. T6's grids are all-service and internally consistent, but the publish must not
  imply CLI-vs-service comparability; that is R-5 / cascor#578 territory.

## 5. New traps (additive to predecessor §2; each cost real time today)

1. **A load1 lull fires a naive watch.** v2 gated on load1 alone and fired at 3.83 while
   clamscan ran at 84% and a backup encrypted at 44% (load15 8.31). Gate on load15 AND
   top-process composition — attempt-1's "judge the 15-minute number" lesson, in new clothing.
2. **A freed window is claimed in under a minute.** The 05:16 snipe went teardown → peer launch
   in ~40 s. Secure peer agreements BEFORE the window opens; claim atomically (the launcher
   re-checks every gate in the same second it launches).
3. **Monitors and scratchpad tooling die with their session.** The watch/launcher originals
   lived in the session scratchpad and died with it; only the `util/ad-hoc/` copies are durable.
   Re-arm Monitors fresh each session; never assume a predecessor's watch still stands.
4. **The worktree-isolation hook refuses compound Bash.** Multi-statement one-liners (loops,
   chained `$()`) are rejected as "too complex to verify" — two validators reproduced it
   independently. Put the logic in a script file and invoke `bash <path>`; run doc command
   stanzas one call at a time.
5. **Cross-session messages can be held for the recipient user's approval.** One of three
   morning messages was held and never confirmably delivered. Pair every message with an
   independent tripwire (port watch, idle-notice); treat delivery as best-effort.
6. **Ambient SIGTERMs happen on this host** (3 logged-in users + an active fleet). A long-lived
   process dying rc=143 needs attribution before blame: this morning's backup death was NOT the
   orphan reaper — its candidate predicate matches Python processes only (grep
   `Collect candidate PIDs` in `util/reap_pytest_orphans.bash`).
7. **`ss` multi-port filters lie** (predecessor §3) — re-confirmed; the scripts encode
   one-port-per-call. And the port gates check only each range's minimum port — a survivor
   stack on 8111/8231+ passes them; the §2.2 port-lock-root check is the countermeasure.
8. **The detached campaign pins the launching checkout for its whole life.** `ML_DIR` resolves
   through the invoking script's location; if the launching worktree is removed mid-campaign,
   the NEXT suite's `python3 <deleted-path>` fails rc=2 as an ordinary `suite_end` and the
   campaign ends `CAMPAIGN COMPLETE worst_rc=1` with E-I/E-C silently unrun. Launch from a
   checkout that outlives the run; never clean the launching worktree before `CAMPAIGN
   COMPLETE` (§2.3).

## 6. What this document does NOT cover

Everything in predecessor §6 (recurrence wall-ordering rows, requirements cross-view
inconsistency, T2's permanent residual, T7's JR-REC coverage tail, R-1's second clause, plan
§12.2 items, PF-4/PF-8, F-7). Additionally: the backup arc (certified; ml#1369 owns it), the P5
fleet rollout, the defect-register round-24 ledger, and open cascor issues #572/#573/#578/#579/
#582 (other owners; #582 matters here only as §4's publish guardrail).

## 7. Approval

**No standing-approval claim.** The re-baseline is owner-approved (2026-08-23, "full post-#514
re-baseline"), as is the deferral until the host is quiet. The 2026-08-25 peer-hold agreements
are session commitments, not owner policy. Ask before: spending GPU hours beyond the three named
suites; lowering the quiet bar or running unattended overnight; pulling the shared cascor
checkout if any live peer session objects at launch time; acting on any predecessor §0.1
residual.

## 8. Verification commands

Run from a fresh worktree of juniper-ml, **one stanza per Bash call** — the worktree-isolation
hook refuses loops and long compound lines (trap #4), and shell state does not persist between
calls, so paths are inline and absolute. If an anchor does not resolve, **stop and report;
never substitute a nearby one**.

```bash
git fetch --prune && git log --oneline HEAD..origin/main | head   # ml main moves hourly

gh pr list --repo pcalnon/juniper-ml --state open | head          # dup-guard

git -C /home/pcalnon/Development/python/Juniper/juniper-cascor rev-parse --short HEAD

git -C /home/pcalnon/Development/python/Juniper/juniper-cascor log --oneline HEAD..origin/main
# ^ re-derive the gap; READ EVERY SUBJECT

git -C /home/pcalnon/Development/python/Juniper/juniper-cascor status --porcelain
# ^ driver aborts (exit 2) on dirty

gh release list --repo pcalnon/juniper-data --limit 3
# ^ §4: unreleased while nothing newer than v0.11.0

ls util/ad-hoc/2026-08-23_t6_rebaseline_campaign.bash util/ad-hoc/2026-08-25_t6_watch_host_drained.bash util/ad-hoc/2026-08-25_t6_launch.bash

bash util/reap_pytest_orphans.bash --dry-run | tail -2

ss -tlnH 'sport = :8230' | wc -l
# ^ ONE port per call; run again for 8110, 8202, 8101, 8051 — never as a loop

ls "${XDG_RUNTIME_DIR:-/tmp}/juniper-experiments" 2>/dev/null
# ^ port-lock stragglers (see §2.2)

python3 -m unittest tests.test_experiment_suite_yamls tests.test_run_suite tests.test_run_experiment
# ^ 200 tests; OK twice on 2026-08-25 under JuniperCascor1 3.13.13 (morning + validation round)

ls ~/.local/state/juniper-experiments/t6-rebaseline-20260823T200328Z/
# ^ attempt 1, reference only (do not --resume)
```

**Git state at handoff:** this document + the two launch scripts are the only changes, committed
on branch `worktree-twinkly-nibbling-piglet` (worktree of the same name, cut at `7f3cb19`,
behind a fast-moving `origin/main` — expected) and open as **ml#1371** against `main`. Merge
awaits Paul's per-PR approval (headless-merge policy); until it merges, the two scripts exist
ONLY on this branch, so a successor in a fresh worktree must either start from this branch or
wait for the merge (§2's durability claim is contingent on it). Nothing else is staged or dirty;
no campaign process, monitor, or scratchpad artifact of the authoring session survives it.

## 9. Validation record

Three general-purpose agents, launched in parallel, each prompted to REFUTE (per the
multi-agent adversarial SOP), read-only, with independent repo/host probing:

- **Citations/anchors lens — PASS** (1 minor: §4 had placed the #581 deps bump *on top of*
  `c4bbe81` when it IS `c4bbe81`; fixed). Independently corroborated the 5 m 07 s E-I kill
  figure (307 s from `teardown.json` mtimes) and re-verified all §0.2 closure mappings on disk.
- **Coverage/amputation lens — FAIL, 1 major + 6 minor.** The major: mid-campaign exit-3 had no
  prevention agreement and no recovery procedure in either document — remedied by §3.4
  (checkout-freeze ask) and §2.7 (recovery rule). Minors folded: preamble canonical-list
  extended (L-2 noise, merge-trap rules); publish step now says replace-the-table + resolve the
  E-A/E-I currency caveat; §4 gained the duplicati-re-run status and the post-backup-morning
  window; §3 gained the terminal discharge-by-telling-the-owner fallback.
- **Executability lens — FAIL, 2 majors + 7 minor.** The majors: the detached campaign pins the
  launching checkout for 8–12 h (remedied: §2.3 launch-host rule, §5 trap 8, launcher now echoes
  `ml_dir=`); and §3's re-establishment step depended on a tool absent from some harness
  contexts (remedied: "where the harness provides it" + owner fallback). Minors folded: exit-2
  liftoff caveat (§2.4), #588/two-commit gap and void-if-different note (§4), aescrypt added to
  both scripts' hot-process regex, stderr silenced on probe commands in the watch loop, §8
  rewritten one-stanza-per-call with inline paths, port-lock-root check added (§2.2, §8).
  Chosen remedy notes: the driver's emit-before-dirty-gate ordering was left UNCHANGED (it is
  tracked, battle-tested code; the doc-side caveat covers it) — reordering it is available to a
  successor as a separate reviewed change.

Verdict after fold: no unresolved finding. The three reports live in the authoring session's
transcript; the folded items are individually visible above.
