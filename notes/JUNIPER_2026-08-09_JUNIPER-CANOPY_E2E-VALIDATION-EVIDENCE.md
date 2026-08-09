# Juniper Canopy — E2E Front-End Validation: Evidence Record

**Project**: juniper-canopy end-to-end front-end validation (execution arc)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Fable 5), session "canopy functionality testing"
**Started**: 2026-08-09
**Status**: PHASE 0 COMPLETE — PHASE 1 PENDING
**Plan of record**: [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`](JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md) (merged juniper-ml#1036, approved by owner 2026-08-09)
**Execution script**: [`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`](JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md)

This file accumulates the arc's execution evidence phase by phase (plan §9). Matrix row statuses live in the matrix's own `status` column at Phase-1 close; this file holds transcripts, findings, and the PR ledger.

---

## Phase 0 — Prerequisites & stack fixes (2026-08-09) — COMPLETE

### Exit criteria (plan §6.1)

| Criterion | Result |
|---|---|
| `--up` reaches the honest gate (`demo_mode == false`, `juniper_data_available == true`) | **PASS** (rehearsal 4, ~08:40Z) |
| `--down` releases all ports | **PASS** (8051/8101/8202/8211 all free post-teardown) |
| Env preflight | **PASS** (see below) |
| PR-M1 | **MERGED** — juniper-ml#1037 |
| PR-M2 (§4.5 default, owner-ratified) | juniper-ml#1042 (auto-merge armed at time of writing) |

### Env preflight (plan §6.1 step 3)

- Ports 8050/8051/8101/8202/8211: no listeners at preflight.
- `python3.14`: present at `/usr/bin/python3.14` — **stock GIL build** (`Py_GIL_DISABLED = 0`; no `python3.14t` exists) → drove fix (2) below.
- `juniper-cascor-client` in JuniperCanopy1: `0.7.0` — meets the `>=0.7.0` floor (T-3/T-4 preflight).
- `juniper-recurrence` console script: present in JuniperCascor1 (no dedicated recurrence env; experiment_stack parity).
- Canopy `make check-env` equivalent (`juniper-env-drift-check --repo-root juniper-canopy --check-lock`): **RESULT: OK** (5 lock pins OK).

### Bring-up rehearsal ledger

| # | Command | Result | Cause / action |
|---|---|---|---|
| 1 | `--up --with-recurrence` (defaults) | FAIL (data leg) | Session-worktree gotcha: `PROJECT_DIR` derives two-up from the script → resolved to `.claude/worktrees/`; `pip install -e .../worktrees/juniper-data[api]` invalid. Action: use `JUNIPER_E2E_PROJECT_DIR` (documented override); partial-failure teardown behaved correctly. |
| 2 | + `JUNIPER_E2E_PROJECT_DIR=<ecosystem root>` | FAIL (data leg, 60s gate burn) | `PYTHON_GIL=0` fatal on the now-stock host python3.14: `Fatal Python error: config_read_gil: Disabling the GIL is not supported by this build`. Action: fix (2). |
| 3 | + GIL-probe fix | FAIL (cascor leg) | **cascor main broken at HEAD** — see Finding F-E2E-001. Action: restore PR cascor#501; rehearsal re-pointed via symlink e2e-root at the restore worktree. |
| 4 | + restored cascor | **PASS — exit 0** | data healthy 2s → cascor 2s → recurrence 2s → canopy 6s. |

**Honest gate (rehearsal 4)** — `GET http://127.0.0.1:8051/v1/health`: `status: "ok"`, **`demo_mode: false`**, **`juniper_data_available: true`**, `version: 0.4.0`; `GET /v1/health/ready`: `overall: ready`, `juniper_data: healthy`, `juniper_cascor: healthy`; recurrence `GET :8211/v1/health/ready`: HTTP 200. Teardown: all four services stopped by port; `ss` re-check empty. Full transcripts: session scratchpad `rehearsal_up{,2,3,4}.log` (summarized here; scratchpad is transient by design).

### Findings (Phase 0)

**F-E2E-001 — cascor main broken by direct-push over-deletion (CRITICAL, HEALED).**
cascor commit `4081f5b` ("removing old snapshots", 2026-08-09 03:16 CDT, direct push) deleted the stale `src/snapshots/snapshot_*.h5` artifacts **and five live source modules** (`snapshot_cli.py`, `snapshot_common.py`, `snapshot_errors.py`, `snapshot_serializer.py`, `snapshot_utils.py`; 2,635 lines). `api/routes/snapshots.py:11` and `cascade_correlation.py` still import them → `create_app` import-dies; cascor Post-Merge Main Verification and Golden Regression (WS-6 Gate) went RED on main. Landing as a direct push bypassed the per-PR sequence-safety `juniper-symbol-loss-check` screen (which exists for precisely this class). **Heal**: cascor#501 restored the five modules byte-for-byte from `4081f5b^` (`.h5` deletions honored), merged 2026-08-09T08:47:50Z; primary cascor checkout fast-forwarded.

**F-E2E-002 — isolated_stack teardown glob reproduced the same over-deletion class (FIXED in #1042).**
`do_down`'s `snapshots/snapshot_*` glob matched the **source modules** (`src/snapshots/` is a Python package), reproduced live against a fresh cascor worktree. Root-cause rhyme for F-E2E-001's sweep pattern. Glob tightened to `snapshot_*.h5` + a `snapshot_cli.py` survival guard in tests.

**F-E2E-003 — host python3.14 regressed to a stock GIL build (FIXED for isolated_stack in #1042; experiment_stack follow-up PR in flight).**
`PYTHON_GIL=0` is fatal on stock CPython (`config_read_gil`). isolated_stack's data leg now probes `sysconfig Py_GIL_DISABLED` and passes the toggle conditionally. `util/experiment_stack.bash` carries the same latent class (3 sites) — follow-up PR delegated.

**F-E2E-004 — `juniper_plant_all.bash` flat `JUNIPER_CANOPY_PORT` is probe-only (LEDGER; operator path).**
The plant script's `JUNIPER_CANOPY_PORT` (default 8050) moves only its health-probe URL/origin derivation and is never exported into canopy's process — an operator override probes a port canopy never binds. Latent T-1 variant; works at defaults by coincidence. Triage in Phase 2/4.

**F-E2E-005 — `tests/test_experiment_stack_script.py` pre-existing `assertIn(..., env_text)` sites render ambient secrets on failure (LEDGER; test hygiene).**
Found by the #1044 executor while mutation-testing: the live-up stubs capture `env | grep -E '^(...|JUNIPER_)'` into `env_text`, and an assertion failure renders the whole blob — including live `JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI` tokens — the exact class `tests/redacted_env.py` exists to prevent. #1044's new assertions compare filtered line lists; the pre-existing sites remain. Follow-up: sweep that file (and siblings) for the shape. Severity: leaks only on local failure output, but real.

**F-E2E-003 scope precision (from the #1044 executor)**: the JuniperData *conda* env python (3.14.2) is still free-threaded (`Py_GIL_DISABLED=1`); only the *system* `/usr/bin/python3.14` (3.14.0) is stock. isolated_stack builds its venv from the system interpreter (live break, fixed in #1042); experiment_stack launches from the conda env (latent, hardened in #1044).

### PR ledger (Phase 0)

| PR | Repo | Content | State |
|---|---|---|---|
| #1036 | juniper-ml | Planning docs (plan + matrix + dual audits) | MERGED (owner) |
| #1037 | juniper-ml | PR-M1: canopy leg nested `JUNIPER_CANOPY_SERVER__PORT`/`__HOST` + checklist §3.3 + 3 test-site inversion + negative guards | MERGED |
| cascor#501 | juniper-cascor | Restore 5 snapshot modules (F-E2E-001 heal) | MERGED |
| #1042 | juniper-ml | PR-M2: `--with-recurrence` leg (8211, occupancy pre-check, canopy URL hand-off) + GIL probe + teardown glob `.h5`-only | auto-merge armed |
| #1044 | juniper-ml | experiment_stack GIL probe (F-E2E-003 tail; latent hardening — conda-env python still free-threaded) | MERGED |

### Notes for Phase 1

- Bring-up: `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper util/isolated_stack.bash --up --with-recurrence` (post-#1042 script; cascor primary is healed so no symlink root needed).
- Gate every live check on the §4.3 body assertions, never HTTP 200.
- Evidence: matrix row statuses + screenshots per plan §9 (`<row-id>__<step>.png`).
