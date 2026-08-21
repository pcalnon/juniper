# HANDOFF 2026-08-21 — safe_merge defects, base-branch guard rollout, bypass identification

Successor to [`HANDOFF_2026-08-19_safe-merge-defects-and-kill-forensics.md`](HANDOFF_2026-08-19_safe-merge-defects-and-kill-forensics.md).
**That handoff is now fully discharged** except one item its owner tabled. This document
records what closed, what is still in flight, and the three things worth carrying forward.

---

## 1. Closed this session

| Item | Result |
| --- | --- |
| §2.1 kill mechanism | **IDENTIFIED.** A background task cannot outlive its `[bg]` host worker; spare workers hold a hard **~3600 s lease**. Incident matched to **0.426 s** (elapsed 229.398 s = worker's *remaining* lease 228.972 s). Supervisor-restart candidate **refuted** (1 hit in 33). |
| §2.2 D1–D4 | **ALL FIXED.** D3 (disarm on refusal) shipped with/before D1 as required. D4 closed last, on a live measurement — see §3. |
| §2.3 `DEFAULT_TIMEOUT` | **RE-MEASURED**, per-repo. 900 s sat at *canopy's median*; ~half its healthy merges would have refused. |
| §2.4 ml#1161 | **CLOSED** (healed by #1165; main-verify green ×6). |
| §2.5 bypass roster | **DeployKey IDENTIFIED** — see §3. dependabot verdict **WITHDRAWN**. |
| §2.6 doc residue | **CLEARED**, incl. the runbook stanza whose deferral condition had since been met. |
| §2.7 / ml#434 | **SWEPT + FIXED.** Guard now on **9/9** repos, required on **9/9**, documented on **9/9**, `stacked-pr` label on **9/9** (was 1/1/1/0). |
| Short kills (16–456 s) | **TABLED by owner.** Still unexplained. |

~45 PRs across 9 repos. Fleet BLOCKING contexts: **0** throughout.

---

## 2. IN FLIGHT — check this first

`util/ad-hoc/base_branch_guard/merge_all.py --set final` was merging 11 PRs serially when the
session ended. At last read: **1 merged** (deploy#192), **2 armed** (ml#1228, cascor#557 —
these self-complete server-side), **8 not yet reached**.

The merger is itself a background task and therefore subject to the ~3600 s worker lease this
session documented, so **assume it was killed mid-run**. Re-check and finish:

```bash
python3 util/ad-hoc/base_branch_guard/merge_all.py --set final    # dry-run first
python3 util/ad-hoc/base_branch_guard/merge_all.py --set final --execute
```

It is dup-guarded and re-entrant: already-merged PRs report REFUSED (`not OPEN`) and are skipped.

---

## 3. The three findings worth carrying forward

**A stacked PR is governed by NO ruleset.** Both rulesets are `~DEFAULT_BRANCH`-scoped:
`gh api repos/pcalnon/juniper-ml/rules/branches/feature%2Fx --jq length` → **0** (`main` → 9).
So it merges clean with **zero** required checks — that is the mechanism behind
recurrence#7/#8 and canopy#365. An adversarial audit concluded the opposite ("already
unmergeable"), and it was believed because its *premise* checks out while its *conclusion*
does not. One API call separated them.

**`expectedHeadOid` on auto-merge is ENABLE-TIME, not continuous** (probe ml#1225: armed with
a pin, moved the head, `autoMergeRequest` still present with unchanged `enabledAt`). Had it
been continuous, pinning would kill the net the moment GitHub syncs a `strict` branch —
silently negating D1. This is why D4 was measured rather than reasoned.

**The DeployKey bypass is this operator's own machines.** 17 write-enabled keys, all
`added_by: pcalnon`: 9 match this host's `~/.ssh/id_ed25519_gh_*`, 8 are a second machine
("Turing", `last_used` 2026-05-07). Confirmed by `ssh -T` → `Hi pcalnon/juniper-ml!` (the
deploy-key response shape). **`last_used` is NOT a recency signal** — it read 2026-08-17
immediately after a successful auth and ~30 same-day pushes.

---

## 4. Open decisions (owner)

- **DeployKey row.** Lowest-risk step, no ruleset edit: delete the 8 dormant "Turing" keys if
  that machine is retired — halves the entitlement. The row itself looks low-impact to remove
  (no-direct-push already blocks main pushes; feature-branch pushes aren't evaluated), but the
  residual `deletion` / `non_fast_forward` on `main` is **UNTESTED** and not testable safely.
- **dependabot `29110` / Copilot `1143301`.** Both **UNDETERMINED**, on the absence-from-history
  evidence the census itself called insufficient. Do not act on the census §1 text — it is
  struck; read §3c.
- **F-5 `concurrency:`** — closed as a reasoned no-change, rationale in the workflow header.
  Revisit only with a measurement that a *superseded* `cancelled` run does not gate.

---

## 5. The pattern this session should be remembered for

**Nine instances of the vacuous-pass class in one arc**, five of them a distinct variant:
*queries and assertions that returned a clean result they were structurally incapable of
producing.* `rule-suites` defaulting to `time_period=day`; `gh pr list --limit` truncating
twice; a duplicate class name silently deleting six tests; `TIMEOUT_CEILING` declared,
asserted against, never consulted; a required check whose failure arm had never once run;
and — twice — my own audit tooling (`gh_json(...) or []` reporting a failed probe as zero).

Memory updated: [[reference_vacuous_pass_check_class]] now carries all nine plus a second
diagnostic for the query variant — *"could this query have returned a non-empty answer at
all?"*

**The gates were never the weak point.** Every defect was caught by one — CodeQL, markdownlint,
the Memory Budget, the mergeability gate, mypy, two independent validators. The two real
failures were talking *past* what a gate showed: a `-3` diffstat where `-2` was expected
(a regex eating a blank line) that was noticed and rationalised, and a uniform 9-repo fan-out
run without checking whether any repo had a constraint the others didn't (juniper-ml's
`AGENTS.md` budget).

> **Carry this rule:** a clean result on the one input that should have been dirty is a
> signal, not a relief. Explain the anomaly or investigate it — do not reason past it.

---

## 6. Verify starting state

```bash
python3 util/ad-hoc/2026-08-20_base_branch_guard_scan.py     # expect 9/9 guard + required
python util/ad-hoc/2026-08-10_ruleset_context_audit.py        # expect BLOCKING=0
python3 util/ad-hoc/2026-08-21_deploykey_bypass_audit.py --local-keys
python3 -m unittest tests/test_safe_merge.py                  # expect 65 OK
python3 -m unittest tests/test_wait_for_checks.py             # expect 37 OK
python3 util/ad-hoc/base_branch_guard/test_guard_shell.py     # expect 6/6
gh pr list --repo pcalnon/juniper-ml --state open
```

**Git state:** worktree `.claude/worktrees/dapper-drifting-wigderson`, branch
`ci/guard-merge-group` (pushed, PR ml#1236). `main` moves continuously — re-probe and
`gh pr list` dup-guard before acting; concurrent sessions are active.
