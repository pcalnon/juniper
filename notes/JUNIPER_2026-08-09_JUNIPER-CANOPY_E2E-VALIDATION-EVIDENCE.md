# Juniper Canopy — E2E Front-End Validation: Evidence Record

**Project**: juniper-canopy end-to-end front-end validation (execution arc)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Fable 5), session "canopy functionality testing"
**Started**: 2026-08-09
**Status**: PHASE 1 IN PROGRESS (LIVE lane, run `20260809T223851Z`)
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
| #1042 | juniper-ml | PR-M2: `--with-recurrence` leg (8211, occupancy pre-check, canopy URL hand-off) + GIL probe + teardown glob `.h5`-only | MERGED |
| #1044 | juniper-ml | experiment_stack GIL probe (F-E2E-003 tail; latent hardening — conda-env python still free-threaded) | MERGED |

### Notes for Phase 1

- Bring-up: `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper util/isolated_stack.bash --up --with-recurrence` (post-#1042 script; cascor primary is healed so no symlink root needed).
- Gate every live check on the §4.3 body assertions, never HTTP 200.
- Evidence: matrix row statuses + screenshots per plan §9 (`<row-id>__<step>.png`).

---

## Phase 1 — Live click-by-click validation (started 2026-08-09) — IN PROGRESS

**Run-id**: `20260809T223851Z` — screenshots `reports/e2e/20260809T223851Z/<row-id>__<step>.png` (working tree of the results branch; landing decision at Phase 4)
**Working branch**: `arc/canopy-e2e-phase1-results` (matrix `status` column filled in place there; this file accumulates findings + transcripts)

### Environment header (plan §8.5)

- **Lane**: LIVE. Stack: `util/isolated_stack.bash --up --with-recurrence` @ c9bd54e (post-F-E2E-006 fix), `JUNIPER_E2E_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`, **`JUNIPER_E2E_RECURRENCE_PORT=8212`**.
- **Ports**: data 8101 / cascor 8202 / recurrence **8212** / canopy 8051. The §4.5 default 8211 was legitimately occupied by the operator's juniper-deploy stack (`juniper-recurrence` container publishes host 8211→ctr 8210, up + healthy) — the PR-M2 occupancy pre-check exists for exactly this; the documented `JUNIPER_E2E_RECURRENCE_PORT` override keeps W8 end-to-end honest without touching the deploy stack. Canopy's `RECURRENCE_SERVICE_URL` follows the override (wired from `${RECURRENCE_PORT}` in `canopy_up`).
- **Honest gate (§4.3)**: `status: ok`, `demo_mode: false`, `juniper_data_available: true` — passed at bring-up and re-passed after the F-E2E-006 bounce. Upstreams: data `ok`, cascor `ok`, recurrence `/v1/health/ready` → `ready`.
- **Preflights**: `juniper_cascor_client-0.7.0` in JuniperCanopy1 (floor `>=0.7.0`); `juniper-env-drift-check --repo-root juniper-canopy --check-lock` under the **JuniperCanopy1 interpreter** → `RESULT: OK` (5/5 floors, 5/5 lock pins). Caveat for future runs: the same check from a JuniperCascor1-active shell reports that interpreter's `juniper-cascor-client 0.5.0` as BELOW_FLOOR — an active-interpreter artifact, not a canopy-env fact.
- **Auth posture (T-9)**: no `CANOPY_API_KEY` configured → browser-control auth on `/api/train/*` disabled; CSRF still minted and carried on the WS handshake. **Rate limiter (T-8)**: default off. **Transport (T-21)**: `enable_ws_control_buttons` defaults True → training buttons are WS-primary on `/ws/control`.
- **Browser**: Playwright MCP Chromium, viewport 1600×900.

### Findings (Phase 1)

**F-E2E-006 — canopy's browser-WS origin allowlist defaults to port-8050 origins only; an isolated canopy 403-loops its own dashboard sockets (FIXED in ml#1049).**
First browser contact: `/ws/training` + `/ws/control` handshakes rejected 403 in a reconnect loop; canopy log `ws_security: WebSocket origin rejected: http://127.0.0.1:8051 not in allowlist`. Root cause: `websocket.allowed_origins` defaults admit only `{http,https}×{localhost,127.0.0.1}:8050` (canopy `src/settings.py:142-147`) and `canopy_up` exported no override — the deploy stack works only because its canopy sits exactly on 8050. Invisible to Phase 0 (HTTP-only gates). Fix (ml#1049): `canopy_up` exports `JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS` derived from the real canopy port (`127.0.0.1` + `localhost`); 5 test pins (SCRIPT_TEXT, both dry-run arms, live env stub, TestCanopyUp); checklist §3.3 updated. Verified live post-bounce: both sockets `open`, console 0 errors. **Canopy-side note for Phase 2 triage**: the default allowlist does not track `server.port`, and no canopy doc names the env var for non-8050 deployments — candidate docs/config finding, severity P2.

### PR ledger (Phase 1)

| PR | Repo | Content | State |
|---|---|---|---|
| #1049 | juniper-ml | F-E2E-006: canopy leg browser-WS allowlist export + 5 test pins + checklist §3.3 | MERGED (--admin per landing protocol; green-but-BEHIND) |
