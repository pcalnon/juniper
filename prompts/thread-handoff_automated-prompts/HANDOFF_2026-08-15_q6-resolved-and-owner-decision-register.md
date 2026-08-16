# HANDOFF 2026-08-15 — Q-6 resolved and shipped; the register that is left

Successor to
[`HANDOFF_2026-08-14_f-p1-3-root-caused-and-fixed.md`](HANDOFF_2026-08-14_f-p1-3-root-caused-and-fixed.md).

**No code PR from this arc is in flight** — all three merged. This document itself is the one
unlanded deliverable; see §7.

Source documents are named in full on first use. Citations are written `file:NNN` for a **line**
and `§N` only for a real **section heading** — the plan document is 1213 lines and has no §1147.

## Read this first: THREE handoffs are live today, and they do not overlap

| document                                                                                                                                           | owns                                                                                                            |
|----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| [`HANDOFF_2026-08-15_wide-budget-head-to-head-campaign.md`](HANDOFF_2026-08-15_wide-budget-head-to-head-campaign.md) (ml#1122)                     | the wide-budget head-to-head **campaign** (64–128 units) — GPU work, a new suite, a new evidence note           |
| [`HANDOFF_2026-08-15_api-primer-defect-register-outstanding-work.md`](HANDOFF_2026-08-15_api-primer-defect-register-outstanding-work.md) (ml#1121) | the **defect register** — 91 open defects, the throttle port, consolidation                                     |
| **this one**                                                                                                                                       | what is left of the CLI-experimentation *plan*: two engineering items, and the owner-decision / parked register |

All three were written by different sessions on the same day and are **siblings** — none supersedes
another. ml#1122 was authored after this session's Q-6 work landed and cites ml#1120 / cascor#523
accurately. **If you are here to run the campaign, go to ml#1122 instead.**

---

## 1. Shipped this session — do NOT redo

All merged, all merge-commit diffs verified with `git show --stat` (squash has silently shipped only
a first commit before), all post-merge gates green.

| PR         | Squash               | Item                                                                                                |
|------------|----------------------|-----------------------------------------------------------------------------------------------------|
| ml#1118    | `1b5cbf35` (+62/−0)  | F-P1-3b refutation propagated into three stale forward-looking registers                            |
| cascor#523 | `3909d275` (+215/−5) | **Q-6** — `JUNIPER_CASCOR_LOG_DIR` override, service + direct CLI                                   |
| ml#1120    | `181f76d8` (+62/−7)  | **Q-6** launcher half — per-run export at all 3 `cascor_up` sites                                   |
| —          | —                    | juniper-cascor issue **#521** closed (stale release-train HALT; v0.9.0 had already shipped to PyPI) |

Post-merge: ml `main-verify` success on `1b5cbf35` and `181f76d8`; cascor `3909d275` green on all
five workflows (Post-Merge Main Verification, Golden Regression, Conformance, CodeQL, CI/CD
Pipeline). The four *work* worktrees and their branches were removed and pruned.

### 1.1 What Q-6 settled

`JUNIPER_CASCOR_LOG_DIR` overrides the checkout-shared `logs/juniper_cascor.log`. Unset, blank or
whitespace-only keeps `<repo>/logs` **byte-identically** (`.strip()` folds them to falsy and the
`else` branch is the untouched prior expression), so nothing changed for existing deployments.

| tier       | site                                                | read          |
|------------|-----------------------------------------------------|---------------|
| direct CLI | `constants._PROJECT_LOG_DIR_DEFAULT` (module level) | import time   |
| service    | `api/observability.py::_resolve_log_dir`            | **call** time |
| service    | `api/service_launcher.py::_resolve_log_dir`         | **call** time |

The call-time read is load-bearing and has no W-6 equivalent: in both helpers the `os.environ.get`
precedes the `try: from cascor_constants.constants import …`, and the `except ImportError` arm
returns a hardcoded `Path(__file__).resolve().parent.parent.parent / "logs"` that never consults the
constants. An import-time-only override would therefore be silently dropped exactly there.

**The reframing matters more than the code.** H-7 filed the shared log as *accepted residual risk*
conditional on the one-cascor-per-checkout rule, treating Q-6 as a **concurrency** question. It is
not. cascor's parent logger writes **only** to that file — stdout carries just candidate-worker
lines — so the markers that decide a run's verdict exist nowhere else
(`Training completed` at `src/cascade_correlation/cascade_correlation.py:1936`, `Completed solving`
at `src/main.py:512`, both `logger.info`). A second cascor process does not interleave the log, it
**rotates the evidence away**. One other process is enough, so the one-instance rule never protected
an individual run from a long-lived service sharing its checkout. That is how the F-P1-3 arm A/B
logs were lost.

---

## 2. Engineering work left (two items)

### 2.1 Propagate Q-6's closure into the registers that still call it open

**Do this first — it is small, and leaving it is the exact defect ml#1118 existed to fix.** Five
sites still record Q-6 as unresolved, and a successor reading any of them will re-open settled work:

| site                             | stale text                                                                                                                         |
|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| plan:728 (H-7 row)               | "lifting it (Wave 5.3) **requires resolving** `OPEN QUESTION Q-6`"                                                                 |
| plan:1093 (Wave 5.3 row)         | "**Explicitly depends on resolving Q-6** … Until Q-6 is resolved, 5.3 is scoped to concurrent runs in **distinct checkouts** only" |
| plan:1145 (Q-table)              | "**Defer** for single-instance-per-checkout use"                                                                                   |
| P4 studies note:189, :194-195    | "W-12/Q-7, F-P1-2, PF threshold ratification **and Q-6 are unchanged and still open**" … "Recommend resolving Q-6 **yes**"         |
| **P2 matrix note:84** (also :65) | "Of this paragraph's other items, **F-P1-2 and Q-6 remain genuinely open owner calls.**"                                           |

- plan = `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`
- P4 studies note = `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md`
- P2 matrix note = `notes/JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P2-DATASET-MATRIX-EVIDENCE.md`

**The P2 site is the sharpest lesson here: ml#1118 *created* it.** That PR's own update block —
committed at 03:43, about 90 minutes before cascor#523 at 05:10 — added line 84 asserting Q-6 was
still an open owner call, and its
supersede block at :67-84 names only three stale F-P1-3b references, so it does not cover its own
new claim. Line :65's "launcher multi-run + Q-6 log-dir class" is likewise untouched. A register-repair
PR can plant the next stale register entry; **re-grep the finding ID after writing the fix, not just
before.**

Use dated `> **Update (…)**` blockquote markers appended below the original text — the house idiom,
and what ml#1118 did. Do not rewrite history. Note that Wave 5.3's dependency is only *partly*
discharged: the override exists, but see 2.2.

### 2.2 Lift `run_suite`'s cascor-parallel refusal, behind a cascor version floor

`util/experiments/run_suite.py:112` is the refusal's condition (comment `:113-123`, `raise` at
`:124`). **Line 111 is a different, unrelated `max_parallel >= 1` bounds check** — do not anchor
there.

This was **deliberately not lifted** in ml#1120, and the reason is the task: the override exists,
but `run_suite` cannot verify the **installed** cascor honours it. Against a pre-#523 cascor the
export is silently ignored and parallel cells race the shared log exactly as before, **with no
signal** — a silent return of the evidence-destruction bug.

1. Assert a `juniper-cascor` version floor at suite load. **#523 is unreleased**: `v0.9.0` was cut
   at `1f2d9d9`, two commits *before* it, and pyproject is still `0.9.0` on `main`. So there is no
   released version carrying Q-6 yet — the floor cannot be written until the next cascor release.
   **Do not guess `>=0.9.1`.**
2. Only then relax the `app: cascor` + `parallel > 1` refusal.
3. Keep the failure loud when the floor is unmet.

The comment and message at that site already state the *current* reason, so they will not mislead
you. `tests/test_run_suite.py:152` pins the `Q-6` ID in the message — keep it greppable.

Not urgent: sequential cascor suites work, and every campaign to date has used them.

### 2.3 Also open, and not an owner decision

The **§12 performance lane** (plan §12, heading at plan:895) remains open engineering. ml#1118's
refresh of the P4 note records it explicitly: *"The perf lane remains open on the PF suites and the
E-B ranking; it no longer has an F-P1-3b premise."* The PF suites and the E-B difficulty ranking are
its standing inputs. This is distinct from **PF threshold ratification** (§3), which is Paul's — do
not merge the two.

---

## 3. Owner decisions and parked items

None is blocked on engineering. Do not "make progress" by guessing Paul's answer.

Sources in this table: **P3 rollup** = `notes/JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md`; **P1 smoke note** = `notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md`; plan as above.

| item                          | nature                                                                                                                                                                             | source                            |
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| **F-P1-2**                    | Owner decision — a native Grafana v13.0.1 owns `:3000` (apt, systemd `active`+`enabled` since 2026-07-15, non-default creds, **binds `*:3000`**). Options package already written. | P3 rollup §3                      |
| **Q-8**                       | Owner call — where run-level performance baselines live. Also gates the `JR-CAS-OBS-004` targets (plan:1160).                                                                      | plan:1147                         |
| **Q-10**                      | Owner call — dedicated `JuniperRecurrence` conda env vs riding `JuniperCascor1`. Hygiene, explicitly *not* a blocker.                                                              | plan:1149                         |
| **W-12 / Q-7**                | Parked — `csv_import` corpus. The plan's Q-7 row says "Defer until a corpus is defined". It has blocked nothing.                                                                   | plan:1095 (W-12), plan:1146 (Q-7) |
| **PF threshold ratification** | The *thresholds* are Paul's. The lane itself is §2.3 above.                                                                                                                        | plan §12                          |
| **F-P1-4**                    | Owner's to keep or delete — snapshot `.h5` debris.                                                                                                                                 | P1 smoke note:37 (§2 Findings)    |

**On F-P1-4, correct a claim you may find elsewhere: W-6 did NOT stop new debris.**
`juniper-cascor/src/cascor_snapshots/` holds **27,867** `.h5` files, **65 of them from 2026-08**
(newest 2026-08-14). W-6 only redirects when `JUNIPER_CASCOR_SNAPSHOTS_DIR` is exported — direct-CLI
runs, which this arc used heavily, still write to the checkout. The P1 note's original "4 files" is
long superseded.

**F-P1-1 is CLOSED — do not re-open it.** The P1 smoke note's `:22` names it alongside F-P1-2 as
blocking the render arm, which reads as open — but `:22` is the P1.6 row of **§1 Results** and
records the state as of 2026-08-07; it predates the clearance. It was cleared on 2026-08-09:
[`HANDOFF_2026-08-09_cli-experimentation-program-wrapup.md`](HANDOFF_2026-08-09_cli-experimentation-program-wrapup.md):10
— "Images rebuilt + provenance-verified (**F-P1-1 cleared**)". (P3 rollup:57 only records the
rebuild as "authorized and **in progress**" as of 2026-08-08 — it is not the clearance record, and
an earlier draft of this handoff wrongly paraphrased it as "done".) The P1 note's own §4 Disposition
at `:47` / `:49` and the 2026-08-15 P4 update block both name **F-P1-2 alone**.

**P1.6 interactive render is the only non-PASS arm of P1 smoke**, and its live blocker is F-P1-2
alone. P3 criteria 6 and 8 carry the same caveat.

---

## 4. Live state, probed 2026-08-15 — re-probe, do NOT copy forward

The predecessor handoff was wrong here because it inherited state verbatim. Two of its facts had
already changed by today, so assume these have too.

**Listeners** (one `ss` call per port):

| port                              | bind                        | what                                                    |
|-----------------------------------|-----------------------------|---------------------------------------------------------|
| `:3000`                           | **`*:3000`**                | native Grafana v13.0.1 — F-P1-2's subject, and it is UP |
| `:8050`                           | `127.0.0.1`                 | operator canopy                                         |
| `:8200`                           | `127.0.0.1` **and `[::1]`** | operator cascor (container)                             |
| `:8201`                           | `127.0.0.1`                 | operator cascor (host)                                  |
| `:8211`                           | `127.0.0.1`                 | deploy-stack recurrence                                 |
| `:9090`                           | `127.0.0.1`                 | Prometheus                                              |
| `:8051` `:8100` `:8101` `:8202`   | —                           | **no listeners** — the isolated E2E stack is DOWN       |
| 8110-8139 / 8230-8259 / 8260-8289 | —                           | **no listeners** — experiment ranges clear              |

The predecessor described the E2E stack as actively training at 7/10 units; that run has ended.

**GPU**: ~900 MiB used of 8192. `nvidia-smi --query-compute-apps` returns ~6 rows, all desktop
(steam/slack/gnome, 5-66 MiB) — **no training compute**. It does not return empty; do not read a
non-empty list as contention.

### 4.1 `JuniperCascor1` + a stale checkout: NEITHER tier honours Q-6 today — version equality is not a drift check

This is the trap worth carrying forward. `importlib.metadata.version('juniper-cascor')` reports
**0.9.0**, pyproject says **0.9.0**, so `test_version_matches_pyproject` passes and the env looks
clean. It is not:

```bash
$ /opt/miniforge3/envs/JuniperCascor1/bin/python -c "import cascor_constants.constants as c; print(c.__file__); print(hasattr(c,'_PROJECT_LOG_DIR_OVERRIDE'))"
/opt/miniforge3/envs/JuniperCascor1/lib/python3.13/site-packages/cascor_constants/constants.py
False
```

A **physical July-1 copy in site-packages shadows the editable-install finder**. It has no
`_PROJECT_LOG_DIR_OVERRIDE`, and resolves the log dir to
`/opt/miniforge3/envs/JuniperCascor1/lib/python3.13/logs` — a site-packages path, *not* the
checkout-shared log. So a direct-CLI run resolving through that shadowed module ignores
`JUNIPER_CASCOR_LOG_DIR` entirely and writes somewhere neither tier intends.

**Scope this precisely, and mind the second condition.** The shadow defeats only the **import-time
constants** tier: both service helpers read the env *before* the constants import, so a **service**
still honours the override — **but only when launched from a checkout carrying #523**, because those
helpers live in the checkout, not site-packages. At `3857d1e` (where the primary cascor checkout sat
when this was written, §7) `_resolve_log_dir` has no `os.environ.get` at all and goes straight to the
constants import. So on this host as configured, *neither* path honours Q-6 until the checkout is
synced. `experiment_stack.bash`'s `cascor_up` launches from `CASCOR_SRC_DIR`, so **syncing the checkout
fixes both paths** for normal invocations: CWD precedes site-packages on `sys.path`, so an import
rooted in `src/` (which is where the direct CLI and the §6 pytest both run) resolves to the checkout
and the shadow never wins. Verified — from `src/` the probe returns the checkout copy; from the repo
root it returns the site-packages copy. The shadow therefore bites only imports rooted **outside**
`src/`, which is how §4.1's probe above was run. Removing it is worthwhile hygiene, not a
precondition.

This is the `ml#1109` STALE-metadata class. **Check module content, not the version number.** Repair
is a `pip install -e <checkout> --no-deps --force-reinstall` after removing the shadowing copy — but
confirm the shadow is gone afterwards with the probe above, and note a *running* service keeps
serving old code until restarted.

---

## 5. Traps this session paid for

- **`gh pr checks` has NO `--json` flag in this build** (gh 2.46.0) — it exits `unknown flag`. A
  waiter using `--json … || echo '[]'` reports "still pending" *forever* and never fires; it burned
  a 20-minute monitor here. Parse the tab-separated output (`awk -F'\t'`, col 2 = bucket).
- **`ss -tlnpH 'sport = :A' 'sport = :B'` is malformed and returns EMPTY with exit 0** — a silent
  false negative that has already produced a wrong "the stack is down" claim. One port per call.
- **pytest exit `4` is a USAGE error** (`file or directory not found`), not a test failure. Separately,
  juniper-cascor's `tests/unit/api` runs **omit the `=== N passed ===` summary line even for a single
  file** — so key pass/fail on the **exit code**, never on the presence of a summary. (The
  observability tests are in `test_access_log_survival.py`; there is no `test_observability.py`.)
- **`cascor_up.index("nohup")` matches the wrong thing** — the `announce` dry-run string ends
  `# nohup -> ${LOG_DIR}/…` at `util/experiment_stack.bash:618`, preceding the real launch at `:646`.
  Anchor on `nohup "${uvicorn_bin}"`.
- **`cascor_up` states its launch env three times** (announce `:618` / `record_launch_env` `:631` /
  live `nohup` `:643`). Updating only the live one is the standing failure mode and is invisible to a
  whole-function grep — `tests/test_experiment_stack_script.py:435` pins the **count**, not presence.
- **`git show --stat` is necessary but NOT sufficient.** ml `8c1d03b` — "docs(handoff): finalize …
  and document findings" — shows `1 file changed, 1041 insertions(+)`, which *corroborates* its own
  message. Only a content diff reveals the truth: of those 1041 added lines, 888 are non-blank, and
  the document's six sections appear **ten times over** — `grep -c '^## Verification commands'` on
  that blob returns `10`. The file went 117 → 1158 lines (≈117 × 10) and `27c6fb3` later cut it back
  to 123. An earlier draft of this handoff claimed "1041 blank lines" and a later one "a duplicated
  second copy"; both were wrong, and independent validators caught each in turn. Read the content,
  count it, and do not restate a diff summary as if it were an inspection.
- **Approval does not carry across sessions.** A handoff saying "standing approvals carried forward
  … explicitly for its successor" is exactly the blanket grant that
  `feedback_headless_merge_approval_policy` classifies as **per-session and non-carrying**, and it is
  self-referential (a prior session wrote it, not Paul). **Do not merge on it.** Ask; Paul grants a
  named group readily. Background task notifications are never approval either.

---

## 6. Verification commands

Run from the `juniper-ml` repo root. The cascor block is a **subshell** on purpose — a bare
`cd ../juniper-cascor/src` persists and silently runs every later command in the wrong repo.

```bash
git fetch --prune && git log --oneline HEAD..origin/main    # empty before committing
gh pr list --state open                                     # dup-guard; goes stale in minutes

grep -c JUNIPER_CASCOR_LOG_DIR util/experiment_stack.bash    # expect 3 (all cascor_up sites)

# Q-6 end to end. The cascor checkout may be BEHIND origin/main — #523 ships this test, so an
# exit 4 here means "checkout is stale", NOT "Q-6 regressed". Sync first.
( cd ../juniper-cascor && git fetch -q origin && git pull --ff-only origin main \
  && cd src && python -m pytest tests/unit/api/test_q6_log_dir_override.py -q; echo "exit=$?" )

# Does the resolved cascor code actually carry Q-6? Version equality does NOT answer this (§4.1).
# Run from src/ — that is where the CLI and pytest import from, and CWD beats site-packages.
( cd ../juniper-cascor/src && /opt/miniforge3/envs/JuniperCascor1/bin/python -c \
  "import cascor_constants.constants as c; print(c.__file__); print(hasattr(c,'_PROJECT_LOG_DIR_OVERRIDE'))" )
# Same probe from the repo root instead resolves to the site-packages shadow and prints False even
# when fully repaired — that is the §4.1 trap, not a failure.

# Live state — one port per call; the multi-arg form returns EMPTY.
ss -tlnpH 'sport = :8202'; ss -tlnpH 'sport = :8201'
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader   # desktop rows are normal
python util/experiments/list_runs.py                        # NOT executable — needs the interpreter
```

---

## 7. Git state — re-derive; concurrent sessions push constantly

- `juniper-ml`: `origin/main` at `b5670c8` (ml#1122) when written.
- **This document is authored on branch `docs/handoff-q6-closeout`** in
  `worktrees/juniper-ml--docs--handoff-q6-closeout--20260815-1351--b5670c85`. If it is still
  unlanded, land it via PR, then remove the worktree and branch per the V2 cleanup procedure.
- **Open PRs ml#1119** (release-train propose-lane signing closeout) and **ml#1123**
  (`docs/canopy-e2e-seg12-handoff`) belong to **other sessions** — leave both. Re-run
  `gh pr list --state open`; this set turns over in minutes.
- ml open issues #1012, #1011, #588, #434, #358, #357 are pre-existing owner-decision / backlog
  items; **none is from this arc**.
- `juniper-cascor`: `origin/main` at `3909d27` (#523), **zero open PRs, zero open issues**. The
  primary checkout was one commit behind at `3857d1e` — check before running anything against it.
- 14 session worktrees under `.claude/worktrees/`; none belong to this arc.
