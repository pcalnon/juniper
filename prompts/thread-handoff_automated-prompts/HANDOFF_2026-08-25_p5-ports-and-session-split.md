# HANDOFF — P5 ports (cascor-client, recurrence), the two-session split, and what is left

**Date**: 2026-08-25 (evening)
**Origin session**: memory governance (`fluttering-bubbling-newell`)
**Predecessor**: [`HANDOFF_2026-08-25_memory-governance-and-p5-fleet-rollout.md`](HANDOFF_2026-08-25_memory-governance-and-p5-fleet-rollout.md)

Every figure below was re-probed in this session, not inherited. **Nothing was merged by this
session and nothing is promoted** — merges are the owner's per-PR call.

---

## Handoff prompt (copy this into the new thread)

Continue the **shared-session-memory** arc in `juniper-ml`, P5 fleet rollout. Authorities:
plan §P5 in [`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`](../../notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md)
(its `NOT STARTED` banner is fixed by **ml#1376, pending merge** — until then the banner lies);
tracker **ml#1326** (retitled IN PROGRESS; its comments are the live per-repo ledger); the
predecessor handoff for mechanism facts and owner decisions, none of which changed.

**Run the dup-guard BEFORE any work** (see *Key context*): two sessions ran this handoff at once
today and duplicated each other for 20 minutes.

### State, verified 2026-08-25 ~19:15 local

| Repo | PR | State | Ceiling |
|---|---|---|---:|
| canopy | canopy#516 | MERGED | 95,133 |
| cascor | cascor#585 | MERGED; `main` green post-merge | 71,098 |
| cascor-client | **cascor-client#139** | OPEN, all 21 checks green, `Memory Budget` pass | 34,695 |
| recurrence | **recurrence#131** | OPEN, green; **standalone `.github/workflows/memory-budget.yml`** (no `ci.yml` there) | 11,578 |
| data-client, data, cascor-worker, deploy | the **peer session's** — worktrees `worktrees/juniper-<repo>--feat--memory-budget-gate--20260825-1852--…` | in flight; PRs expected | — |
| juniper-ml docs | **ml#1376** (peer) supersedes my closed #1375 | OPEN, green | — |
| juniper-ml helper | **ml#1379** (peer) supersedes my closed #1378 | OPEN; `Verify AGENTS.md Last Updated` was RED at last look | — |

All ports are ADVISORY, standalone, absent from every Quality Gate `needs:`, ceilings seeded by
`--ratchet` in the target with zero slack. slacker has no `AGENTS.md` — six governable repos remained
this morning, not seven.

### Remaining work

1. **Owner merge decisions**: #139, #131, ml#1376, ml#1379, and the peer's four once open. Verify a
   merge with `gh pr view N --repo … --json state,mergedAt` plus a marker grep on `origin/main` — a
   native auto-merge prints no `MERGED` line. Never merge to clear a queue.
2. **After ml#1379 merges**, confirm it carries what my closed #1378 had — the peer committed (19:20)
   to folding these into #1379 as one amended commit, each with a hermetic test:
   `git show origin/main:util/ad-hoc/2026-08-25_p5_port_memory_budget.py | grep -c "B404\|header-version\|pytest-marker"`.
   If 0, cherry-pick from `origin/chore/p5-toolkit-seed-and-render` @ `cb8a4b73` (`adapt-test
   --sub-project / --header-version <v>|none / --pytest-marker unit` + `# nosec B404` on the import;
   `insert-job` refusing a second job; repo name from the origin URL).
3. **If ml#1376 does not land**, my closed #1375 (branch `docs/p5-status-rates-and-hazards` @
   `903c208a`) holds the same fixes — reopen it; do not re-author.
4. **Promotion — NOT yet.** Four preconditions, in order: merged to that repo's `main`; `--advisory`
   REMOVED; the three negative controls passed against the NON-advisory invocation; slack ≥ the largest
   measured single commit, declared with `Allow-Ceiling-Raise: AGENTS.md`. Then
   `python3 util/ad-hoc/2026-08-20_require_context_safely.py --repo juniper-<x> --context 'Memory Budget'`
   (dry-run) then `--apply`. Observed-only is its DEFAULT — the flag that exists is
   `--allow-unobserved`; there is no `--require-observed`. Its roster omits recurrence: pass `--repo`.
5. **Worktree cleanup only after the PR is MERGED**, and only after
   `util/ad-hoc/2026-08-20_worktree_liveness_probe.py`: mine are
   `worktrees/juniper-cascor-client--feat--memory-budget-gate--20260825-1826--f5a90304` and
   `worktrees/juniper-recurrence--feat--memory-budget-gate--20260825-1848--d9688520`; the predecessor's
   canopy/cascor ones are merged and still present. **Never touch the peer's `…--1852--…` ones.**
6. Owner decisions are unchanged from the predecessor (soak's null-experiment question; worktree
   convergence LEAVE IT; Skills deferred; the MEMORY.md cap is decided). Do not re-propose.

### Key context

- **Per-repo traps, each a test or hook in a DIFFERENT file, none caught by pre-commit** — verified by
  doing: the client repos' tests-scoped bandit (relaxed) skips B101/B104/B108/B110/B311 but **not
  B603/B607/B404** — cascor-client's pre-commit failed on `import subprocess` until `# nosec B404`
  (cascor's config skips B404, so #585 never hit it); **data** runs `-m "unit and not slow"` from
  `juniper_data/tests/unit` (depth 3; needs `pytestmark = pytest.mark.unit` or it is silently
  deselected; ruff-format rewrites); **data-client** pins every `Version:` header under `tests/` to the
  package version; **recurrence** has no `ci.yml`, `util/`, top-level `tests/` or `docs/REFERENCE.md`
  — its workflow runs the ported suite itself and `pre-commit run --all-files` is its CI lane;
  **deploy** has no Python linters, `yamllint --strict`, env var `PYTHON_VERSION`.
- **Full-suite hazard confirmed twice**: cascor-client 458 passed in a fresh `.[test]` venv;
  recurrence's `--all-files` pre-commit (17 hooks) passed.
- **The harness refuses compound commands in a worktree-isolated session** — loops, `cd`+chains,
  heredocs writing into sibling repos, `${PIPESTATUS}` — with one unchanging message. One plain command
  per call; multi-step logic belongs in a tracked `util/ad-hoc` script. Sibling worktrees, local
  GPG-signed commits (YubiKey present) and `gh pr create` all worked.
- **Same-handoff collision**: both sessions retitled #1326, fixed the same banner and extended the same
  helper within minutes. Dup-guard = `gh pr list --state all` on ml AND each target, `git -C <repo>
  branch --list feat/memory-budget-gate`, `ls worktrees/ | grep <repo>--feat`, the tracker's newest
  comments. **Tell subagents to STOP on a pre-existing worktree** — one of mine overwrote
  `tests/test_memory_budget_check.py` in the peer's deploy worktree at 18:56:38 before being killed;
  the peer was warned by `SendMessage` (delivered), found a one-line difference, and restored its own
  artifact. The peer also confirmed data-client and cascor-worker both failed their pre-commit on
  B404 until annotated — the trap is real on every client-shaped repo.
- **Sequence Safety**: extracting `growth_stats` out of `measure_growth` reads as `WEAKENED`
  (53→31 lines). Waiver `Allow-Symbol-Loss: func:measure_growth` in the FIRST commit; a force-push does
  not fire `synchronize`.
- Measured order (30 d to 2026-08-25, `--ref origin/main`): cascor 730/day > cascor-client 196 >
  recurrence 137 > data-client 135 > data 109 > canopy 81 > worker 66 = deploy 66. Zero shrinking
  commits anywhere; the recurring **+1,982 is one fleet-wide sweep** (base-branch-guard docs,
  2026-08-21) and is worker's and deploy's entire growth — the shape zero slack cannot absorb.
- `--advisory` prints and exits 0: no ledger, no counter. It does not measure the burn; `measure-growth`
  does. Expect it to report on every AGENTS.md-growing PR; that is noise, not data.
- MEMORY.md: 121 lines / 19,511 bytes after this session's three writes (P5 state, the collision
  lesson, the harness-refusal reference).

---

## Verification commands

```bash
git fetch origin
gh pr list --repo pcalnon/juniper-ml --state all --limit 40 --json number,state,mergedAt --jq '.[]|select(.number as $n|[1375,1376,1378,1379]|index($n))|"#\(.number) \(.state) \(.mergedAt // "-")"'
gh pr view 139 --repo pcalnon/juniper-cascor-client --json state,mergedAt,mergeStateStatus
gh pr view 131 --repo pcalnon/juniper-recurrence --json state,mergedAt,mergeStateStatus
gh pr list --repo pcalnon/juniper-data-client --state all --limit 10 --json number,title,state   # repeat for juniper-data, juniper-cascor-worker, juniper-deploy — ONE command each
git -C /home/pcalnon/Development/python/Juniper/juniper-recurrence show origin/main:.github/workflows/memory-budget.yml | grep -c "Memory Budget"   # 1 once #131 merges
python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth /home/pcalnon/Development/python/Juniper/juniper-cascor --days 30 --ref origin/main   # --ref exists only after #1376/#1379 or #1375's branch
python3 util/soak_ledger.py report      # INCONCLUSIVE 35/35 68.6% 5 open misses; `status` exits 1 by design
python3 util/memory_budget_check.py     # OK 36,960 / 38,000
```

## Git status at handoff

- Worktree `fluttering-bubbling-newell`, branch **`docs/handoff-2026-08-25-p5-ports-split`** from
  `origin/main` at `1291e839`; this file is its only change, pushed with its archive PR.
- Closed-PR branches kept on origin (closing never deletes): `docs/p5-status-rates-and-hazards`
  (`903c208a`), `chore/p5-toolkit-seed-and-render` (`cb8a4b73`).
- Sibling worktrees of this session: cascor-client (#139), recurrence (#131) — open PRs, do not remove.
- The juniper-ml primary checkout was in sync with `origin/main` at session start; re-check.

## Corrections to the predecessor

- **`--require-observed` is not a flag** on `require_context_safely.py`; observed-only is the default and
  `--allow-unobserved` is the override (the peer's ml#1376 annotates the 08-25 handoff accordingly).
- "Seven repos remain" → **six governable**; slacker has no `AGENTS.md`. Rates are now measured for all
  eight governed repos (table above); the predecessor had none for the six.
- `--ratchet` seeds only an EXISTING `ceiling_chars` entry (`chars < ceiling`), so a fresh repo needs a
  placeholder ceiling first — the plan's step b says "run `--ratchet`" without that step.
