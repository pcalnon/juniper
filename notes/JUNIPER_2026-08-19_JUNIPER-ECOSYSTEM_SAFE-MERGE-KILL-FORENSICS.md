# What Killed the `safe_merge` Run — forensic investigation

**Project**: Juniper (ecosystem)
**Author**: Paul Calnon
**Date**: 2026-08-19
**Harness**: Claude Code **2.1.236** — every §2/§3 finding is a property of this build. Re-probe after a
client upgrade before relying on them.
**Status**: Incident identified. **Killer mechanism UNDETERMINED and still open** — a prior
"resolved" claim was spurious and is withdrawn (§3.3). The mechanism is bounded and characterised, and
a cheap decisive test is named (§3.3) that has **not** been run.
**Scope**: **Document only.** No code, config, ruleset or repository setting was changed by this
investigation.
**Related**: [ml#1183](https://github.com/pcalnon/juniper-ml/pull/1183) (kill-resilience fixes),
[ml#1184](https://github.com/pcalnon/juniper-ml/pull/1184) (context rename),
[`…_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_BRANCH-PROTECTION-INVESTIGATION-SYNTHESIS.md)
(origin of the tool; its R4 is "gate merges on `util/wait_for_checks.py`"),
[`…_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md`](JUNIPER_2026-08-16_JUNIPER-ML_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md)
(merge queues are **unavailable** — do not re-litigate),
[`…_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md`](JUNIPER_2026-08-10_JUNIPER-ECOSYSTEM_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md)
(canonical per-repo context lists),
[`…_DIRECT-PUSH-PREVENTION.md`](JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_DIRECT-PUSH-PREVENTION.md)

---

## 0. Bottom line

The reported incident is **`safe_merge --pr 1175 --repo juniper-ml`**, background task `bi5a42rgc` in
session `fa36ee6b`, **killed 229 s in**, after it had already issued its `update-branch` and while it
was waiting on the restarted CI.

It is **one member of a population of 19 background-task kills** that share a signature and have no
identified cause. It is not special; it is the one that was noticed.

| Question | Answer |
| --- | --- |
| Which run? | `--pr 1175`, task `bi5a42rgc`, session `fa36ee6b`, killed at **229 s** |
| Killed by a timeout? | **No.** The `timeout` parameter is not consulted for background tasks (§2.1) |
| Killed by duration at all? | **No.** Same session: kills at 37/46/60/229 s **alongside** completions at 248–932 s |
| Killed by the operator? | **No `TaskStop` call exists** in that session's transcript |
| Root mechanism | **UNDETERMINED and still open** — no prior fix resolved it; an earlier "resolved" claim was spurious (§3.3). Best unexplored candidate: the `[bg]` supervisor's restart/adopt cycle (§3.2) |
| Was anything lost? | Yes — nothing server-side existed to finish the merge. That is RC-4, fixed afterwards in ml#1183, **partially** (§4) |

> **A first draft of this document identified the wrong incident** (`juniper-cascor#536`). That draft
> was refuted during validation and the reasons are recorded in §5, because the *method* failure is
> more reusable than the conclusion was.

---

## 1. The incident

Session `fa36ee6b-32e3-495c-993d-12a2a50e06ca` (worktree `swirling-kindling-octopus`), 2026-08-19:

| Time (UTC) | Event |
| --- | --- |
| 02:42:16 | "#1174 is merged and verified on main" — **run 1 succeeds** |
| 02:46:39.577 | `python util/safe_merge.py --pr 1175 --repo juniper-ml --execute` launched as background task `bi5a42rgc` — **run 2** |
| — | run 2 issues its `update-branch`; CI restarts on the new head |
| **02:50:29.004** | notification `status=killed`, **elapsed 229 s**; output file contains `[killed]` |
| 02:50:37 | session observes: "`safe_merge` was **killed**, not completed" |
| 02:51:22 | session observes: "It had completed its update-branch (which is why checks restarted), then was stopped while waiting" |

That is the reported symptom exactly: same session, same repo, **second** PR, killed mid-wait after
the sync.

### 1.1 It was not alone

The same session shows three further kills and eight completions:

| Killed | Completed |
| --- | --- |
| `--pr 1175` (229 s), `--pr 1180` (60 s), `wait_for_checks.py` (37 s), `gh pr checks --watch` (46 s) | 248, 253, 257, 259, 263, 273, 275, **932** s |

A 932 s task completed in the same session where a 37 s task was killed. **Duration does not
determine the outcome**, which forecloses the entire "it timed out" family before any probe is run.

---

## 2. Disproven hypotheses

### 2.1 The `timeout` parameter is not consulted for background-task lifetime

Two controlled probes, both `run_in_background: true`:

| Probe | `timeout` passed | Command | Observed |
| --- | --- | --- | --- |
| A | **omitted** (documented default 120000 ms) | `sleep 200` | ran **200 s**, exit 0 |
| B | **30000** (30 s) | `sleep 120` | ran **120 s** — 4× its stated timeout — exit 0 |

Supporting population scan (see §6 for the caveat): of 231 background tasks in
`~/.claude/projects/**/*.jsonl`, **45 of 204 completed tasks ran > 600 s**, nine ran > 1800 s, longest
**10,593 s (2 h 56 m)** completed normally.

> An earlier `sleep 700` probe is **not** cited as evidence here. It passed an explicit
> `timeout: 900000`, so it only ever excluded a ceiling that ignores the parameter. Probes A/B and the
> §1.1 same-session spread are what carry this.

### 2.2 Also disproven

| Hypothesis | Evidence against | Strength |
| --- | --- | --- |
| Turn end | task `btsiv1b27` survived its turn end by **8 m 15 s**, exit 0 | strong |
| Concurrency cap | most kills occurred with **zero** other background tasks in flight | strong |
| OOM | 92 GiB RAM, 75 GiB available; nothing in `dmesg`/`journalctl` | strong |
| Orphan reaper | the only live `reap_pytest_orphans.bash` runs align with no kill | strong |
| Session end | the launching session kept logging for hours afterwards | **weak — see below** |

**The "session end" disproof is weaker than it looks.** JSONL continuity is *not* process continuity: a
resumed session appends to the same file, so later log lines do not prove the process survived. Other
stop paths — a CLI process exiting, `/clear`, a harness-internal stop on worktree teardown — would also
leave signature B (§3.1) with no `TaskStop` call. Treat "session end" as **not excluded**.

---

## 3. The kill population — the finding that generalises

### 3.1 Two disjoint signatures

- **(A) `TaskStop`** — output file gets `[killed]`, a tool_result confirms it, and **no** task
  notification is delivered. 9 files match a `TaskStop` call to the second.
- **(B) Killed by something else** — file gets `[killed]` **and** a `killed` notification arrives.
  **19 tasks across 11 sessions, with no `TaskStop` call anywhere.** The incident is a member of B.

Every member of B is a long-poll/wait command — `until` loops on `gh pr checks`, `gh pr checks
--watch`, `wait_for_checks.py`, `safe_merge.py`, an experiment-stack launcher. **This is not a
`safe_merge` problem.** It affects any waiting job.

Elapsed-at-kill (18 of the 19 have a resolvable start): 16, 37, 45, 46, 48, 48, 55, 60, 67, 84, 101,
121, 127, 208, 208, 220, 229, 456 s — no bound, overlapping with survivors.

> **Caveat on "no `TaskStop` anywhere":** this establishes no *`TaskStop` tool call* was made. It does
> not establish that no stop occurred by another path (§2.2).

### 3.2 What the clustering shows — and the candidate mechanism

Four pairs died within milliseconds: two pairs at the same millisecond inside one session, and **two
pairs 11 ms and 16 ms apart across *independent* sessions**.

- **PROVEN:** per-task timers are excluded for those clustered members. Independent timers do not fire
  11 ms apart in different sessions.
- **INFERRED:** a single external event. "Sweep" over-specifies it — a supervisor restart, a crash, an
  OOM of a shared parent, a `pkill`, or a control-socket teardown all produce the same observation.
- **UNKNOWN:** whether the ~11 non-clustered members share that cause at all.

**The candidate the first pass missed.** `~/.claude/daemon.log` shows the `[bg]` subsystem is owned by
a supervisor that **shuts down and re-adopts workers on binary upgrade**:

```text
[2026-08-19T20:22:28.269Z] [supervisor] binary … changed (2.1.235 → 2.1.236) — self-restarting for upgrade
[2026-08-19T20:22:28.322Z] [supervisor] shutting down (cause=upgrade, uptime=66721s, leases=2, live_workers=1)
[2026-08-19T20:22:28.991Z] [bg] bg adopt: adopted=1 respawned=0 dead=0
[2026-08-19T20:22:28.996Z] [bg] bg orphan-spare reap: 1
[2026-08-19T20:22:44.011Z] [bg] bg: post-takeover prewarm burst — respawned 0/1 stale workers, 1 refused in 0s
```

There are ~6 such self-restarts between 08-06 and 08-19, plus two `idle 5s with no clients — exiting`
shutdowns. This is a concrete, **host-wide, event-driven, non-duration** mechanism that would take
tasks in independent sessions at the same millisecond — exactly the shape the clustering needs.

**It is a candidate, not a finding.** The restart quoted above is at 20:22Z, *after* the 02:50Z
incident, so it does not explain that kill. What it establishes is that the mechanism class exists on
this host and was never checked.

> **Correction to the first pass:** it noted the daemon log was "silent at three of four kill windows"
> and treated that as disconfirming. That reasoning is invalid — the log records **supervisor
> lifecycle only**, never per-task kills, so its silence is uninformative by construction. Absence of
> evidence was mistaken for evidence of absence in a log that structurally cannot contain it.

### 3.3 The cheap decisive test — not run

**Cross-reference all 19 kill timestamps against `daemon.log`'s `supervisor` / `bg adopt` /
`orphan-spare reap` / `post-takeover` lines.** If kills coincide with supervisor lifecycle events, the
mechanism is identified; if they systematically do not, that class is excluded. This costs minutes and
requires no reproduction.

The first pass instead proposed three expensive options — a debug log that is stale here (last write
2026-04-06), an `execsnoop`/audit trace, and a one-hour multi-session reproduction. Those remain valid
fallbacks **after** the cheap test.

> **A prior "resolved" claim is WITHDRAWN — do not go looking for it.** On 2026-08-19T23:54:36Z it was
> stated that "the safe_merge, `wait_for_checks`, `gh --watch` kill issue has been **resolved** in a
> concurrent session." The operator has since confirmed that claim was **spurious**: it rested on an
> analysis that was later disproved. There is no resolution to find, and §3 is not duplicating one.
>
> Keep the shape of the error, not just the correction: a *"resolved"* claim inherits the confidence of
> whatever analysis produced it. This investigation produced its own confidently wrong attribution (§5)
> that survived until an adversarial pass — the same failure mode, one link earlier in the chain. Grade
> a resolution claim like any other claim (§6).

---

## 4. Defects in the shipped fix (ml#1183)

ml#1183 fixed four root causes. Reading `util/safe_merge.py` at HEAD, **four defects remain** — three
of them in the RC-4 net that was the headline fix. None is fixed here; this document changes no code.

| # | Defect | Why it matters |
| --- | --- | --- |
| **D1** | **The net is not armed on the path that most needs it.** `arm_auto_merge` is gated on `state == "BLOCKED"` (`:437`), but the `BEHIND` branch `continue`s at `:419` before reaching it. On the next cycle GitHub commonly reports `UNKNOWN` while it recomputes mergeability — **`UNKNOWN` is handled nowhere in the file** — so a run can enter its longest, most kill-exposed wait (the post-sync full CI re-run) with **no net armed**. That is precisely the shape RC-4 exists for, and precisely the shape of this incident. |
| **D2** | **`UNKNOWN` also mis-fires the new merge gate.** `if final not in ("CLEAN", "UNSTABLE", "HAS_HOOKS")` raises `Refused`; an `UNKNOWN` returned mid-recomputation produces a spurious refusal. |
| **D3** | **The net is never disarmed, so a refusal can still become a merge.** Once armed, every later refusal path leaves a live server-side auto-merge. The module docstring still asserts "*A refusal is never silent and never degrades to a merge*" — **no longer true**. The SIGTERM handler prints "nothing was merged", which is misleading when a net is armed. Observed live 2026-08-20T00:23:51Z: "`safe_merge` armed GitHub auto-merge before refusing — so #1185 will merge itself once checks pass." |
| **D4** | **The armed net drops `--match-head-commit`.** The docstring calls that pinning the thing that stops the gate being "decorative — the ml#924 shape". The net carries the checks-green guarantee but **not** the head-pinning one. That trade is real and was never stated. |

**`DEFAULT_TIMEOUT = 900 s` is also mis-sized**, though less severely than the first draft claimed. It
was set from juniper-ml's CI (median 251 s / max 333 s). juniper-cascor's pipeline — 22 required
contexts vs juniper-ml's 15 — runs **2.1× longer in wall-clock** (561 s vs 265 s observed), though only
1.5× in context count. A 900 s budget is thin there.

> Two corrections to the first draft's version of this point: a wait timeout raises `Refused` → **exit
> 1**, not exit 2 (`:446-449`, `:574-576`); and the "2.1×" figure is a **duration** ratio, not the
> context-count ratio the sentence implied.

---

## 5. How the first draft got the wrong incident — a method failure worth keeping

The first draft confidently identified `juniper-cascor#536`. It was **refuted**:

- **cascor#536 was never a `safe_merge` run.** No transcript on this host contains
  `safe_merge.py --pr 536`. It was driven by a hand-rolled watcher, `merge_cascor_536.sh`, launched
  under the `Monitor` tool by session `a4708443`.
- **It was never killed.** The watcher **hard-stopped by design** at 20:58:18Z because
  `Test (Python 3.12)` failed on the synced head. The session then fixed the coverage gate, pushed a
  new commit, relaunched, and merged at 21:23:33.
- **The "decisive fingerprint" was not decisive.** The sync commit `d6b62744` is
  `author: pcalnon / committer: GitHub (web-flow)` — byte-identical whether emitted by `safe_merge`,
  by that watcher script, by `gh pr update-branch`, or by a human clicking "Update branch".
- **The uniqueness argument was tautological.** "Only one sync in a 20-hour window" is isolation in a
  ~5-point-per-day series, not identity. And a killed run on a PR that was *not* BEHIND leaves **no
  sync at all**, so the sweep could never have found the real incident by construction.

**Root cause of the error: I primed my own investigator.** The subagent prompt asserted the fingerprint
— *"So the fingerprint is: an `update-branch` merge commit, followed by a gap…"* — and told it the
signature was distinctive to `safe_merge`. The agent found what it was instructed to find, and the
result was then presented as an independent fleet sweep.

> **Rule:** when briefing an investigator, supply the **question and the evidence sources**, not the
> signature you expect it to match. A hypothesis handed to a subagent comes back as a finding.

The strongest tell was available the whole time and was missed: the first draft's own §4 listed
"a **229 s** task was killed while a **273 s** sibling in the same session completed" — those two tasks
*are* the incident (`--pr 1175`) and its successor (`--pr 1178`). **The document cited the answer as an
anonymous data point and did not recognise it.**

### 5.1 A second, unrelated kill — kept separate deliberately

Task `b9xa73jia` (`safe_merge --pr 1171 --execute`) was killed at 02:28:57Z by an explicit `TaskStop`
issued by the session that launched it — **21 minutes before** the real incident, in a different
session. Root cause: a self-collision, where `safe_merge`'s `update-branch` mutated the branch the
session was concurrently editing, its `git push` was rejected, and it killed its own job to rebase.

It is signature A, not B, and is **definitively excluded** as the reported event (the reporter said
"another session"; this was the reporting session). It is recorded because the **shared hazard** is
real: `safe_merge` mutating a branch an operator is editing.

---

## 6. Confidence

| Claim | Status |
| --- | --- |
| The incident is `--pr 1175` / task `bi5a42rgc`, killed at 229 s | **PROVEN** (session transcript + kill notification) |
| Duration does not determine kill outcome | **PROVEN** (same-session 37–229 s killed vs 248–932 s completed) |
| `timeout` parameter is ignored for background tasks | **PROVEN** (probes A/B) |
| The 231-task population figures | **UNVERIFIED** — an independent validator could not reproduce the extraction. Not refuted; the §1.1 same-session data carries §2.1 without it. |
| Per-task timers excluded for the clustered kills | **PROVEN** (11 ms cross-session co-death) |
| A single external event causes the clustered kills | **INFERRED** |
| The `[bg]` supervisor restart is that event | **CANDIDATE — untested** (§3.3) |
| Session-end is excluded | **NOT ESTABLISHED** (§2.2) |
| cascor#536 was the incident | **REFUTED** (§5) |
| D1–D4 in ml#1183 | **PROVEN by code reading**; D1's `UNKNOWN` window is **INFERRED** from observed `UNKNOWN` states, not from a captured failure |
| Incident B was a self-`TaskStop` | **PROVEN** (transcript + 12 ms file mtime) |

---

## 7. Implications (no changes made)

1. **Do not rely on a foreground wait inside a background task surviving.** ~8% die without
   explanation, at elapsed times as short as 16 s, regardless of any timeout parameter.
2. **Hold the completion condition off-process** — a server-side net, a detached `setsid` process with
   its own state file, or an idempotent re-entrant command a later poll can resume. Note **D1**: the
   current net is not armed on the `BEHIND→UNKNOWN` path, which is the most exposed one.
3. **A merge tool and its operator can race for the same branch** (§5.1).
4. **Duration-based reasoning about this harness is unsound.** The documented Bash-tool `timeout`
   bounds do not apply to background tasks. (This is unrelated to `safe_merge`'s own
   `DEFAULT_TIMEOUT`, which is a CI-wait budget — §4.)

---

## 8. Reproduction and artifacts

Evidence here is **perishable** — task output files under `/tmp/claude-1000/**/tasks/*.output` are
reaped shortly after completion, and files vanished mid-investigation. Capture promptly.

| What | Where / how |
| --- | --- |
| Incident session | `~/.claude/projects/*swirling-kindling-octopus*/fa36ee6b-32e3-495c-993d-12a2a50e06ca.jsonl` |
| Incident B session | `~/.claude/projects/*piped-drifting-dragon*/c68f7db0-3c13-4f0d-926d-5a8ea3204669.jsonl` |
| Kill signature | grep the session jsonl for the task id, then for `status` `killed`; a `TaskStop` shows as a tool_use with `task_id` |
| Background-task population | scan `~/.claude/projects/**/*.jsonl` for `run_in_background` tool_use records and their terminal notifications — **note:** an independent validator could not reproduce the pairing; treat §2.1's population figures as unverified until the extraction is republished |
| Supervisor lifecycle | `~/.claude/daemon.log` — **rotates**; the quoted lines are not preserved elsewhere |
| Ruleset state at an event | `gh api repos/pcalnon/<repo>/rulesets/<id>/history/<version>` — **anchor on the version in effect at the event**, never the current one (see below) |

> **Verification trap.** cascor's ruleset *today* requires a context named `Sequence Safety`. At the
> 2026-08-19 events the check was named `Sequence Safety (Advisory)`; the rename landed
> **23:23:31Z**, via ml#1184. A naive re-check against the current ruleset concludes the required
> context was absent and the PR never green — a false refutation. Anchor on ruleset history.
>
> Relatedly, this document's context counts (juniper-ml **15**, juniper-cascor **22**) are each **+1**
> versus `…_REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md` (14 / 21), because `Sequence Safety` became
> required on 2026-08-18. Not an error.

---

## 9. Follow-ups

| Item | State |
| --- | --- |
| Run the §3.3 timestamp cross-reference against `daemon.log` | **not done** — no issue filed |
| D1–D4 in `util/safe_merge.py` | **not fixed** — no issue filed; this investigation was document-only |
| Size `DEFAULT_TIMEOUT` per-repo, or from the slowest repo | **not done** — no issue filed |
| ~~Reconcile with the "resolved in a concurrent session" claim~~ | **closed** — the claim was spurious (§3.3); there is nothing to reconcile |

The trail ends here. Nothing above is tracked anywhere else.
