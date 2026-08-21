# HANDOFF 2026-08-19 — safe_merge defects and kill forensics

Successor to
[`HANDOFF_2026-08-15_ruleset-bypass-and-branch-protection-register.md`](HANDOFF_2026-08-15_ruleset-bypass-and-branch-protection-register.md).
That register's two owner decisions (ml#1011, ml#1012) are now **closed**; this document takes over the
register role for what remains.

**Validated by two independent agents** before archiving — one re-derived every checkable claim against
live state (34/36 confirmed, 0 refuted), one audited for omissions. Corrections from both are folded
in; the errors they caught are noted where they matter.

Continue the branch-protection / merge-tooling arc in **juniper-ml**. The owner decisions are closed.
What remains is **documented, unfixed defects** plus one **time-critical experiment**. Except where an
issue number is given, **nothing below is tracked anywhere else** — this handoff is the record.

---

## 1. Completed — do not redo

- **Three owner decisions closed.** ml#1011 (`Sequence Safety` required on all 9), ml#1012 (bypass
  actors), ml#1128 (merge queue — **not possible**, requires org ownership).
- **`Sequence Safety` required on all 9**, and renamed to drop `(Advisory)` on the 8 siblings.
- **Direct pushes to `main` BLOCKED on all 9** via a second, no-bypass ruleset
  (`juniper-no-direct-push`). Binds the owner too — everything goes through a PR.
- **`allow_auto_merge` enabled on all 9** — a safety fix: where false, `--auto` silently merged instead
  of arming.
- **`util/safe_merge.py`** built (R4) and hardened (ml#1183); `util/wait_for_checks.py` pre-existed.
- Merged: ml#1134, #1166, #1168, #1169, #1170, #1171, #1173, #1183, #1184, **#1189**.

> **Caveat on "required".** `RepositoryRole 5` (owner) holds `always` bypass on all 9, so a required
> check does **not** constrain the owner's own merges. ml#1011 was never the fix for that failure mode.
> `safe_merge` is discipline, not enforcement, for the same reason.
>
> **ml#1011 landed 2026-08-18, ahead of its own ~2026-08-21 A5.2 soak gate.** Whether the four-check
> checklist was run is recorded nowhere. `HELD-PLANNING-ITEMS-REGISTER.md` §2 and `MEMORY.md` both
> still say "#1011 gated on ~08-21" — **both are stale**.

---

## 2. Remaining work — in dependency order

### 2.1 FIRST — run the kill-mechanism cross-reference (time-critical, evidence is decaying)

Cross-reference the 19 background-task kill timestamps against `~/.claude/daemon.log`'s
`supervisor` / `bg adopt` / `orphan-spare reap` / `bg settled` lines.
Source: `notes/JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SAFE-MERGE-KILL-FORENSICS.md` §3.3 (on `main`).

**A validator already ran it for the one published timestamp and got a hit.** Preserved verbatim here
because `daemon.log` **rotates** and this line exists nowhere else:

```text
[2026-08-19T02:50:28.549Z] [bg] bg settled e7e92976 (done)
```

That is **455 ms before** the incident kill (`02:50:29.004Z`) and the **only** daemon.log event in a
3 h 09 m window (~4×10⁻⁵ under a uniform null). Caveats, honestly: `e7e92976` is the **spare** worker,
not the incident session's; `settled … (done)` reads as a normal terminal transition; and the interval
from its spawn is **3600.977 s — an almost exact 1-hour spare-lifetime expiry**. A strong lead, not an
identification.

> **This also corrects the forensics doc.** §3.2 says daemon.log "records supervisor lifecycle only …
> so its silence is uninformative by construction." **Wrong** — it demonstrably records per-worker
> `[bg]` transitions (`bg spawned`, `bg settled`, `bg adopt`, `orphan-spare reap`), so its content
> around a kill window *is* informative. Fix that line when you touch the doc.

**Why first, and why it is not "minutes":** the forensics doc §8 says the evidence is perishable —
task outputs under `/tmp/claude-1000/**/tasks/*.output` are reaped, and files vanished mid-investigation.
Only **1 of 19** absolute timestamps is published; the other 18 must be re-derived from
`~/.claude/projects/**/*.jsonl` by a method that **already failed independent reproduction once**
(§8 flags the population figures as unverified). daemon.log is sparse — 31 KB, one line in the
incident hour, multi-day gaps at 08-11→08-13 and 08-16→08-18. **A null result may mean the log is too
sparse, not that the mechanism class is excluded.**

### 2.2 Fix D1–D4 in `util/safe_merge.py` — **D3 must land with or before D1**

Documented in the forensics doc §4. No issue filed.

| # | Defect | Evidence |
| --- | --- | --- |
| **D1** | Auto-merge net **not armed on the `BEHIND→UNKNOWN` path** — the longest, most kill-exposed wait, and the shape of the incident | `arm_auto_merge` gated on `state == "BLOCKED"` (`:437`); `BEHIND` branch `continue`s at `:419`; `grep -i unknown` over the file returns **zero** hits |
| **D2** | `UNKNOWN` also mis-fires the merge gate → spurious `Refused` | `:470` `if final not in ("CLEAN","UNSTABLE","HAS_HOOKS")` → `raise Refused` `:482` |
| **D3** | Net **never disarmed**, so a refusal can still become a merge | no disarm call anywhere; `armed` is a per-cycle local (`:436`); refusal paths `:445 :447 :462 :513`. Docstring `:102` still claims *"A refusal is never silent and never degrades to a merge"* — **false**. Observed live on ml#1185 |
| **D4** | Armed net drops `--match-head-commit`, trading away head-pinning silently | `:313` vs the local path `:496-497` |

> **Ordering is load-bearing.** Widening the arming condition (D1) strictly **increases** the number of
> refusals that leave a live server-side auto-merge (D3). Ship D3 with or before D1, never D1 alone.
>
> **Interim mitigation, unmentioned until now:** `--no-auto-fallback` (`:539`, `docs/REFERENCE.md:1257`)
> restores the strict semantic — nothing merges unless that run merges it. **Use it while D3 is open**,
> and after any refusal check `gh pr view N --json autoMergeRequest`, because a refusal may have left a
> live net that merges later without approval.

### 2.3 Re-size `DEFAULT_TIMEOUT`

`900 s` (`:124`) was sized from juniper-ml's CI median 251 s. juniper-cascor runs **~2.1× longer in
wall-clock** (561 s observed; 2.1× is a **duration** ratio, not the 1.47× context-count ratio). 900 s is
still ~1.6× cascor's observed clean re-test, so this is mis-sized, **not catastrophic**.
**Re-measure — do not reuse 251 s:** ml went 15→16 required contexts on 08-20, and that median predates
both `Sequence Safety` (08-18) and `Memory Budget` (08-20).

### 2.4 Close issue ml#1161 — verified stale

Tracks the `76e4513b` content loss, **healed by ml#1165** (merged 08-18T08:16:03Z). main-verify is green
×6. Verify, then close.

### 2.5 Owner decision — bypass actors (open)

**The roster is five rows on every repo**, not two:

| Actor                       | Mode           | Disposition                                                                                                                                                 |
|-----------------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DeployKey` (null)          | `always`       | **IDENTIFY-FIRST, unresolved** — the widest entitlement in the roster (push / force-push / **delete** `main` past all checks). Tracked in no other handoff. |
| `RepositoryRole 5` (owner)  | `always`       | **KEEP** — load-bearing (§1 caveat)                                                                                                                         |
| `29110` dependabot          | `always`       | **candidate for removal**                                                                                                                                   |
| `1143301` Copilot SWE Agent | `always`       | **candidate for removal**                                                                                                                                   |
| `4362741` release-train App | `pull_request` | **DO NOT TOUCH** — see below                                                                                                                                |

The decision covers **only `29110` and `1143301`**. Both work solely via PRs on their own branches, and
the rulesets target `~DEFAULT_BRANCH` only — the same structural argument that retired cursor / claude /
Amp / Copilot-code-review.

> **"Never exercised a bypass" is an INFERENCE, not a finding.** A 300-suite sample across ml/cascor/data
> shows only `pcalnon`, but no full 9-repo census was run. Run one before the owner decides.
>
> **`4362741` is a trap.** Its recorded justification was the `code_quality` deadlock, which is now
> refuted — so it *looks* removable by exactly the argument above. But the bypass-actor research still
> marks it **KEEP** ("re-breaks the hands-free archive-PR auto-merge"), and the code-quality audit says:
> *test it (arm an archive PR with the row temporarily absent) or leave it.* **Void justification ≠
> demonstrated redundancy.**

### 2.6 Documentation residue

- **R6 is not finished — 4 lines still carry refuted claims.** `RELEASE-TRAIN-OPERATOR-RUNBOOK.md:963`
  and **`:1023`**, `REQUIRED-STATUS-CHECK-CONTEXT-LISTS.md:561`, `MERGE-QUEUE-ENABLEMENT-RUNBOOK.md:294`.
  **`:1023` is the dangerous one** — §8 known-limitation 5 says `code_quality` "blocks all non-bypass
  merges" and that removal is "deferred until the code-signing work is configured". Code-signing *was*
  configured 2026-08-07, so that stanza actively instructs the next reader to perform the removal the
  do-not-relitigate list forbids.
- **CQ-9 is not in the org-migration plan.** It appears in four notes docs but **not** in
  `MERGE-QUEUE-ENABLEMENT-RUNBOOK.md` §8.3 — the one document that *is* the migration plan.
- **`allow_auto_merge` has no notes document.** Its only record is the tool docstring,
  `docs/REFERENCE.md:1256-1257`, and this handoff. Either write one or declare REFERENCE.md the record.
- `docs/REFERENCE.md:1258` still lists exit codes 0/1/2/3; **exit 4 = INTERRUPTED** is missing.

### 2.7 Carried forward, unowned

**ml#434** — "Sweep recent stacked-PR merges for the squash-into-stacked-branch footgun". Merge-tooling,
open, was carried by the predecessor handoff. Other open issues (ml#1176 lockfile retention, ml#588
env-drift consolidation) belong to other arcs.

---

## 3. Concurrency — READ BEFORE ANY RULESET WRITE

**Another session is writing the same rulesets right now.** The memory arc promoted `Memory Budget` to a
required context on juniper-ml (**15 → 16**) with `integration_id: null`, using a **third** tool,
`util/ad-hoc/2026-08-20_add_required_context.py` (PR **ml#1191**, open).

That is the exact operation that made `main` unmergeable on five repos this session. Therefore:

- **Re-read the live ruleset immediately before any PUT.** Three tools now edit it.
- **Ruleset edits are owner-gated — do not apply unilaterally.**
- `integration_id: null` means "any integration", which is permissive and *not* the failure mode that
  bit this session (a wrong *specific* id). It is not itself a defect.

Merging is via `python util/safe_merge.py --pr N [--repo R] --execute`. Direct pushes to `main` are
blocked, so **there is no fallback path**. Merge only on the owner's explicit per-PR approval. The
tools live **only in juniper-ml** — from a sibling repo, run them from a juniper-ml checkout with
`--repo <sibling>`.

---

## 4. Rollback paths for the live infrastructure changes

| Change | Rollback |
| --- | --- |
| `juniper-no-direct-push` (9 repos) | `python util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --remove --execute` |
| `Sequence Safety` required (8 siblings) | re-PUT `~/.local/state/juniper-ruleset-snapshots/*-pre-sequence-safety.json` (8 files, dated 08-18 03:17 — they predate the rename, so they revert that too) |
| The `(Advisory)` rename | reverse the phases, or revert the 8 workflow commits and re-run phases 1/3 with the names swapped |
| `allow_auto_merge` (9 repos) | **NOT a blanket `--disable`.** It was `true` on **juniper-ml only** beforehand, so a fleet `--disable --execute` **over-reverts ml**. Use eight `--repo <sibling> --disable --execute` calls. |

---

## 5. Do NOT relitigate

- **Merge queues are unavailable** — require org ownership; these repos are User-owned (ml#1128).
- **`code_quality` is INERT** — 779/785 and 399/399 pass, 0 fail. The real July blocker was the
  **`update` rule**, removed 08-10. **Do not remove or "fix" `code_quality`** — the audit says *"Do not
  drop the rule."*
- **CQ-9, stated correctly:** `code_quality` is already configured at `severity: errors` on all 9. It is
  inert only because GitHub Code Quality is unavailable on User accounts — **the same constraint that
  blocks merge queues**. An org migration would make the already-configured rule **start evaluating**,
  with unknown-magnitude blast radius. The audit's recommendation is to **enable on one repo first and
  watch**, *not* to drop the rule and *not* to do all nine at once.
- **A required status check is `(context, integration_id)`, not a string.** Hardcoding `15368` made
  `main` unmergeable on 5 repos (their `Bandit` is `57789`). Preserve existing ids on any PUT; the
  **ruleset history API** is the recovery path. Related: a ruleset PUT is **full-replacement**, and
  `code_quality` is emitted by REST while absent from the documented REST enum *and* GraphQL's
  `RepositoryRuleType` — so any editor rebuilding `rules` from a schema-derived allowlist **silently
  drops it**.
- **Renaming a required check is 3-phase** (unrequire → rename+merge → require) — the rename PR blocks
  itself otherwise.
- **A ruleset edit is not a PR event.** A PR left `CLEAN` with auto-merge armed needs **re-arming**
  (`--disable-auto` then `--auto`). Never `--admin`.
- **`git push --dry-run` does NOT evaluate rulesets**; **`update-branch` is 202/async**. Both are silent
  false-negatives.
- **`required_review_thread_resolution: true`** (with `required_approving_review_count: 0`) on all 9: a
  fully-green PR can be `BLOCKED` by one unresolved `github-advanced-security` thread, invisible to both
  `gh pr checks` and `wait_for_checks.py`. **This is the most likely mis-diagnosis path for D2.**
- **The rebase tax is ACCEPTED** — `strict=true` stays on all 9.
- **A prior "resolved" claim about the kill issue was spurious** and is withdrawn. There is no fix to
  find.
- **Do not prime an investigator with the signature you expect.** Doing so produced a confidently wrong
  attribution this session (forensics §5). Supply the question and the evidence sources only.

---

## 6. Verify starting state

```bash
python util/ad-hoc/2026-08-10_ruleset_context_audit.py            # expect BLOCKING=0 on all 9
python util/ad-hoc/2026-08-19_enable_allow_auto_merge.py --status # expect true on all 9
python util/ad-hoc/2026-08-18_no_direct_push_ruleset.py --status  # expect PRESENT, bypass=0, all 9
gh pr list --repo pcalnon/juniper-ml --state open
gh run list --repo pcalnon/juniper-ml --workflow main-verify.yml --limit 3   # expect success
python3 -m unittest tests/test_safe_merge.py                      # expect 41 OK
```

> **Expected confusing output:** on juniper-cascor the audit prints `~ Sequence Safety [2/8]` under
> *"PATH-GATED: do NOT require"* even though it **is** required there (`required=22 matched=22
> BLOCKING=0`). Do not "fix" it.
>
> **Harness pin:** the forensics doc's §2/§3 findings are properties of **Claude Code 2.1.236**.
> daemon.log records an upgrade self-restart at `2026-08-19T20:22:28Z` (2.1.235→2.1.236). Re-probe
> after any client upgrade rather than trusting them.

---

## 7. Git state

Branch `docs/safe-merge-kill-forensics` merged as ml#1189 (`68ceb6b3`); worktree
`.claude/worktrees/piped-drifting-dragon`. `main` moves continuously — **re-probe before acting**, and
`gh pr list` dup-guard first: concurrent sessions own the memory arc (ml#1190 merged, **ml#1191 open**)
and others.
