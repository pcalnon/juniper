# Lane A / Agent A3 — Ship status from the git and PR record

- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane A
- **Subject design**: `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (juniper-ml), §7 phasing table
- **Date**: 2026-09-05
- **Entry point**: commit and PR history only; every verdict then confirmed against the diff that would have implemented it
- **Mode**: READ-ONLY. No edits, branches, commits, PRs, merges, or service start/stop.

## 0. Reference points

| ref | SHA | date | note |
|-----|-----|------|------|
| canopy baseline (last `main` commit before 2026-09-02) | `30e15b7` | 2026-09-01T12:19:41-05:00 | `fix(F-CANOPY-041)` (#558) |
| canopy HEAD at audit time | `fc62175` | 2026-09-05T20:39:42Z | `chore(deps)` (#591) |
| juniper-data HEAD | `005a82b` | 2026-09-05T17:06:10-05:00 | (#378) |
| juniper-recurrence HEAD | `9c86ac9` | 2026-09-06T00:34:16Z | (#150) |

**Baseline validated against the design's own citations.** The design cites
`dashboard_manager.py:1334` (`clearable=False`), `:5260-5293` (`open_restart_confirm_modal`),
`:7187` (`_update_button_appearance_handler`), `:2702-2706` (the snap), `:2845`
(`_apply_dataset_handler`), `:2681` (`_resolve_oneshot_start_body_handler`), and
`model_registry.py:{200,209,264,276,408}`. Every one of those resolves correctly in `30e15b7`
and in no later tree, so `30e15b7` is the tree the design was written against. That makes
`30e15b7 → fc62175` the exact drift window the task asks about.

---

## T1 — Ship status per planned PR

### Summary table

| §7 item | contents | verdict |
|---------|----------|---------|
| **PR 1** | §4.4 X1 model-state truth + G5 | **NOT SHIPPED** |
| **PR 2** | §4.10 dataset-axis hydration, both axes + G7 | **NOT SHIPPED** |
| **PR 3** | §4.1 ✕ + §4.11 + §4.2/§4.8 guards + §4.3 + §4.7 + §4.12 + G1a–G1d, G3, G6, G8, G9 | **NOT SHIPPED** |
| **PR 4** | §4.5 restart modal + §4.6 alias + §4.9 staging + G2, G4 | **NOT SHIPPED** |
| **PR 5** | §12 generator expansion + G10, G11 | **NOT SHIPPED** |
| **∥** | juniper-data packaging: `equities` extra into `requirements.lock` | **NOT SHIPPED** |

**Zero of the six items has shipped, in whole or in part.** No commit on any ref of
`pcalnon/juniper-canopy` or `pcalnon/juniper-data` implements any part of them.

### Repo-level negatives (the strongest single result)

`git diff --stat 30e15b7 fc62175 -- src/` on juniper-canopy lists 46 changed files.
**`src/model_registry.py` is not among them.** The file that §5's "enabling change" targets —
the five resolvers lacking an injectable parameter, without which G1c/G1d cannot be written —
has not been touched at all:

```
$ git log --all --since=2026-08-25 -- src/model_registry.py
(empty)
```

At `fc62175`, `src/model_registry.py:200,209,264,276,408` still read
`dataset_type_options()`, `dataset_default_params(value)`, `get_model_spec(key)`,
`get_dataset_spec(value)`, `gated_dataset_options(model_key)` — no `*, dataset_types=` or
`models=` parameter on any of the five. Identical to the design's citation.

`DATASET_TYPES` at `src/model_registry.py:132` still seeds **6** `DatasetTypeSpec` entries
(`spirals`, `xor`, `mnist`, `circles`, `moons`, `equities_seq`). §12 wants 16 minus a named
exclusion list. PR 5: **NOT SHIPPED**.

### Per-PR evidence

**PR 1 — §4.4 X1 model-state truth. NOT SHIPPED.**
`_select_model_handler` (`src/frontend/dashboard_manager.py:2876-2898` at both refs) is
byte-identical between `30e15b7` and `fc62175` (sha1 of the extracted block `850dc6c05b` at
both). It still mirrors only `nn_model` and `execution`; it does not read `swapped` or
`backend`. `_model_summary_text` (`:2932-2939`) likewise identical (`650d44aa05`).
Pickaxe across **all refs**: `git log --all -S 'swapped is False'` → empty.
The response field it would read is already pinned by
`src/tests/regression/test_d8_d11_phase4_truth_up.py:81` (`assert body["swapped"] is False`),
and that file is byte-identical baseline→HEAD.

**PR 2 — §4.10 hydration. NOT SHIPPED.**
`GET /api/train/status` (`src/main.py:3708-3718` at HEAD) still returns
`{"backend": ..., "execution": ..., **status}` with **no dataset field**. There is no
dataset-hydration callback in `dashboard_manager.py`. Pickaxe all refs:
`git log --all -S 'staged_dataset'` → empty. (The route body *did* change — see T3 — but only
in how it is executed, not in what it reports.)

**PR 3 — the reachability fix proper. NOT SHIPPED, on every one of its parts.**
- §4.1: `src/frontend/dashboard_manager.py:1334` still reads `clearable=False` at both refs.
  `git log --all -S 'clearable=True'` over the whole canopy history → **empty**. No commit
  has ever introduced `clearable=True` in this repo.
- §4.7 and §4.11: `_gate_dataset_options_handler` (`:2687-2707`, sha1 `13a6667b90` at both refs)
  still contains verbatim `if not model_key: return dash.no_update, dash.no_update` and
  `if current_value in enabled or not enabled: return options, dash.no_update`.
- §4.3: the inverted docstring the design says to fix first is still there —
  `dashboard_manager.py:2695` reads *"snap to the first enabled option (dataset-primary
  conflict policy, D5)"* for a model-primary snap.
- §4.3 toast: `git log --all -S 'dbc.Toast'` → empty; `-S 'aria-describedby'` → empty.
- §4.2: `_apply_dataset_handler` (`:2831-2875`, sha1 `758d93e748`) identical.
- §4.8: `_update_button_appearance_handler(self, button_states=None, model_key=None)` —
  signature unchanged (block sha1 `1f7687ef29` at both refs; it moved `:7187` → `:7250` purely
  by upstream line drift). It still takes no dataset argument, so `(cascor, ⊥)` would still
  send a bare start POST. The design calls this a *prerequisite* of §4.1, not an enhancement.
- §4.12 / G9: `src/demo_mode.py:549-554` still falls back to `_generate_spiral_dataset_local`
  under a bare `self.logger.warning(...)` — no visible degraded-mode banner. `demo_mode.py`
  *was* changed on 2026-09-05 (`8a43a33`, #589, decision-11 `X_full` re-point) but not at this
  locus.

**PR 4 — restart modal, alias, staging. NOT SHIPPED.**
- §4.5: the `open_restart_confirm_modal` callback registration (baseline 5250-5295, head
  5263-5308) is byte-identical. Its `Output` list still has no `Output("restart-ds-type",
  "options")` and its `State` list no `model-selection-store`. `git log --all -S
  'restart-ds-type", "options"'` → empty. The inner
  `_open_restart_confirm_modal_handler` (baseline `:5460-5502`, head `:5473-5515`) is identical.
- §4.6: `_resolve_oneshot_start_body_handler` (`:2668-2686`, sha1 `c68559ccc3`) still passes
  `dataset_generator` straight through. `generator_name_for_type` is imported at
  `dashboard_manager.py:49` and used at `:2769` and `:2846` — the two sibling handlers — and
  **not** in this one, exactly as the design describes.
- §4.9: `grep -n "def stage_dataset" src/backend/recurrence_backend.py` → no match.
  `src/main.py:4192` still calls `backend.stage_dataset` unguarded. `recurrence_backend.py` has
  zero commits since 2026-09-02 on any ref; `ok=True` still returned at `:156` (N6's target).
  juniper-recurrence itself has no `stage_dataset` anywhere.

**PR 5 — §12 generator expansion. NOT SHIPPED.** See the `DATASET_TYPES` count above.

**∥ — juniper-data packaging. NOT SHIPPED.**
`juniper-data/requirements.lock` header, at HEAD `005a82b`:

```
#    uv pip compile pyproject.toml --extra api --extra observability --extra mnist -o requirements.lock
```

The `equities` extra is not compiled in. `grep -i yfinance requirements.lock` → no match
(`yfinance>=0.2.40` exists only in `pyproject.toml:51`, inside the `equities` extra).
`git log --all -S 'yfinance' -- requirements.lock` → **empty**: no commit has ever put it there.
The lock's only commits since 2026-09-01 are `cc15640` / `569f983` (#368, the 0.13.0 release),
which did not add the extra. juniper-data's only open PR is #369 (`feature/drop-full-family`,
decision 11) — unrelated.

### In-flight work: one empty worktree, and it is the only sign of intent

`/home/pcalnon/Development/python/Juniper/worktrees/` contains, created after HEAD:

```
juniper-canopy--feature--selection-x1-model-truth--20260905-2124--fc621752
```

That is PR 1's name. It is **empty**:

- `git status --porcelain --untracked-files=all` → no output
- `git diff main --stat` → no output
- `git log --oneline main..HEAD` → no output (HEAD == `fc62175`)
- `git ls-remote --heads origin feature/selection-x1-model-truth` → no output

A worktree was checked out for PR 1 and no work has been done in it. This is evidence of
intent, not of shipping.

No other canopy worktree in that directory touches the selection surface. Canopy's own
checkout is clean; the four stashes are all from pre-2026-08 branches.

### Open / closed PR sweep

- `gh pr list --state open` on juniper-canopy: **0 open PRs.**
- 8 PRs closed-unmerged since 2026-09-01 (#568, #569, #571, #574, #576, #577, #579, #580) —
  all Cursor-fleet docs/test PRs for X7 and F-CANOPY-042/046/047; #569, #577 and #580 were
  harvested into #585/#587. None touches the selection surface.
- `gh pr list --state all --search 'reachability OR clearable OR deadlock OR catch-22'`
  returns only fuzzy dependabot/security matches; no PR in canopy's history proposes this fix.

---

## T2 — What consumed 2026-09-02 → 2026-09-05

**24 canopy PRs merged** with `mergedAt` in `[2026-09-02T00:00Z, 2026-09-05T23:59Z]`.

| class | count | PRs |
|-------|-------|-----|
| **(a) deadlock plan** | **0** | — |
| **(b) X7 arc** | **8** | #566, #567, #578, #581, #582, #585, #587, #590 |
| **(c) F-CANOPY-0xx E2E defect fixes** | **8** | #561, #562, #564, #565, #570, #572, #573, #575 |
| **(d) other** | **8** | #560, #563, #583, #584, #586, #588, #589, #591 |

Detail:

| PR | mergedAt | class | subject |
|----|----------|-------|---------|
| 560 | 2026-09-02T11:05:22Z | d | main-verify catch-up base from SCREENED |
| 561 | 2026-09-02T19:22:15Z | c | F-CANOPY-041b heatmap zero height |
| 562 | 2026-09-03T00:43:34Z | c | F-CANOPY-040 residual + F-CANOPY-043 |
| 563 | 2026-09-03T04:20:02Z | d | memory-budget ceiling 51,329 → 48,581 |
| 564 | 2026-09-03T05:03:09Z | c | F-CANOPY-044 / F-CANOPY-045 node click |
| 565 | 2026-09-03T19:59:43Z | c | F-CANOPY-047 CSP `blob:` img-src |
| 566 | 2026-09-04T07:50:48Z | b | X7 slice 1b — cascor client budget |
| 570 | 2026-09-04T18:10:03Z | c | F-CANOPY-042 depth-filter label |
| 573 | 2026-09-04T18:39:30Z | c | F-CANOPY-046 clear-selection control |
| 567 | 2026-09-04T21:54:49Z | b | X7 slice 1a — off-loop discipline |
| 578 | 2026-09-05T06:33:05Z | b | X7 slice 1c — timer poll + status cache |
| 583 | 2026-09-05T09:50:18Z | d | fleet operator-docs consolidation |
| 581 | 2026-09-05T10:10:21Z | b | X7 slice 1d — admission control |
| 575 | 2026-09-05T11:52:10Z | c | F-CANOPY-046 rebuild-contract tests |
| 584 | 2026-09-05T12:33:03Z | d | widen cascor-client cap |
| 588 | 2026-09-05T13:24:21Z | d | retire pending tense in docs |
| 572 | 2026-09-05T13:40:01Z | c | F-CANOPY-042 bounds-sync tests |
| 585 | 2026-09-05T16:30:04Z | b | X7 1a gate suites harvested from #569/#577 |
| 587 | 2026-09-05T16:47:00Z | b | X7 1c status-cache guards harvested from #580 |
| 590 | 2026-09-05T17:03:46Z | b | X7 1c changelog: 18 guards, not 16 |
| 582 | 2026-09-05T18:59:28Z | b | X7 PR 2 — stop presenting simulated data as real |
| 586 | 2026-09-05T19:33:57Z | d | val-split gate (partial-data contract) |
| 589 | 2026-09-05T19:55:26Z | d | decision 11 — artifact guard off `X_full` |
| 591 | 2026-09-05T20:39:42Z | d | pin cascor-client floor 0.8.0 |

**One near-miss worth naming.** #582 (`7a70f35`) is titled *"stop presenting simulated data as
real"* and could be mistaken for §4.12 / G9. It is not: its body cites the **X7** design of
record (`notes/JUNIPER_2026-09-03_JUNIPER-CANOPY_X7-EVENT-LOOP-BLOCKING-REMEDIATION-DESIGN.md`
§7/§8) and its diff touches `connection_indicator.py`, the `"WS: Demo"` badge, and snapshot
size fabrication. It does not touch `demo_mode.py` at all. §4.12's locus
(`demo_mode.py:549-554`) is untouched.

The three days were spent on the X7 arc (which the deadlock design's own OQ-N5 discovered and
spun out) and on the F-CANOPY E2E defect queue, in roughly equal thirds, with the last third
on infra, docs and the unrelated partial-data / decision-11 contract work.

---

## T3 — Collateral drift on the handlers the design plans to modify

**Instrument.** `dashboard_manager.py` has only **two** commits on any ref since
2026-09-02: `9fbf4b8` (#562) and `644967b` (#578). Their hunk headers land at pre-image lines
3989-4024 / 6898-6966 and 6434 respectively — none inside a target handler. Rather than rely on
hunk headers, I extracted each named function's full text from `30e15b7` and from `fc62175` and
compared sha1s.

### Result: 0 of 9 frontend handlers changed

| handler | baseline lines | HEAD lines | block sha1 (both) | changed? |
|---------|---------------|------------|-------------------|----------|
| `_gate_dataset_options_handler` | 2687-2707 | 2687-2707 | `13a6667b90` | **no** |
| `_select_model_handler` | 2876-2898 | 2876-2898 | `850dc6c05b` | **no** |
| `_model_summary_text` | 2932-2939 | 2932-2939 | `650d44aa05` | **no** |
| `_apply_dataset_handler` | 2831-2875 | 2831-2875 | `758d93e748` | **no** |
| `_resolve_oneshot_start_body_handler` | 2668-2686 | 2668-2686 | `c68559ccc3` | **no** |
| `_update_button_appearance_handler` | 7187-7225 | 7250-7288 | `1f7687ef29` | **no** (moved +63) |
| `open_restart_confirm_modal` (+ decorator) | 5250-5295 | 5263-5308 | identical | **no** (moved +13) |
| `_build_model_selection_table` | 3000-3080 | 3000-3080 | `0881c81e49` | **no** |
| `_fetch_generators` | 2713-2736 | 2713-2736 | `fd8e19cc8b` | **no** |

Also verified identical: `_open_restart_confirm_modal_handler`, `_dataset_model_hint_handler`,
`_restage_dataset` (the §4.2 idiom the design says to copy), and all six `clearable=` sites.

### Result: 1 of 2 backend routes changed — plus one adjacent site

| route | verdict | SHAs |
|-------|---------|------|
| `POST /api/model/select` (`src/main.py`, base 3731-3748, head 3921-3938) | **UNCHANGED** — byte-identical | — |
| `GET /api/train/status` (base 3523-3532, head 3708-3718) | **CHANGED, twice** | `94220f0`, `c2c3cb7` |
| `POST /api/stage_dataset` (base 3985-4007, head 4182-4204) — adjacent, §4.2/§4.9's locus | **CHANGED** | `c2c3cb7` |

`GET /api/train/status`:

```python
-    return {"backend": backend.backend_type, "execution": backend.execution, **backend.get_status()}
+    status = await offload(backend.get_status)
+    return {"backend": backend.backend_type, "execution": backend.execution, **status}
```

- `94220f0` (#567, X7 slice 1a, 2026-09-04): sync `backend.get_status()` →
  `await asyncio.to_thread(backend.get_status)`. Attributed by
  `git log --all -S '**backend.get_status()}' -- src/main.py`.
- `c2c3cb7` (#581, X7 slice 1d, 2026-09-05): `asyncio.to_thread` → `offload` (the
  admission-control wrapper). Attributed by `git log --all -S 'offload(backend.get_status'`.

`POST /api/stage_dataset`: `c2c3cb7` changed `await asyncio.to_thread(backend.stage_dataset,
**params)` → `await offload(backend.stage_dataset, **params)`. The
`body.model_dump(exclude_none=True)` on the line above (now `src/main.py:4191`, the mechanism
§4.2 names for the vacuous 200) is unchanged, and the call is still unguarded against a backend
with no `stage_dataset` (§4.9).

### What this means for the design

**The design's plan still applies to the code it will be applied to, essentially unmodified.**
Every frontend line number it cites is either exact or off by a constant, uniform shift
(+63 below `:6900`, +13 below `:5250`), and every mechanism it describes is present verbatim.

Two adjustments the design does not currently account for, both from X7:

1. **§4.10's hydration lands inside an offloaded call.** Adding a staged-dataset field to
   `GET /api/train/status` now means adding it to what `offload(backend.get_status)` returns
   (or to `_backend_status_extras()`, added by `644967b`/#578 at `src/main.py`), not to a
   synchronous dict literal. That also puts the new field behind X7 slice 1d's admission
   control and slice 1c's status cache, which is a caching/staleness question §4.10 does not
   discuss.
2. **§4.9's guard now goes on an `offload()` call.** Same shape, different callee.

Neither is a re-plan; both are one-line retargetings.

---

## T4 — Test-surface drift

**The affected-site population has not moved at all.**

Census of references to the nine handler names under `src/tests/*.py`, at both refs
(`git grep -c` with nine `-e` patterns):

| file | baseline `30e15b7` | HEAD `fc62175` |
|------|-------------------|----------------|
| `src/tests/integration/test_button_state.py` | 1 | 1 |
| `src/tests/regression/test_model_picker.py` | 20 | 20 |
| `src/tests/regression/test_model_table.py` | 17 | 17 |
| `src/tests/regression/test_oneshot_start_body.py` | 9 | 9 |
| `src/tests/unit/frontend/test_dashboard_helpers_coverage.py` | 2 | 2 |
| `src/tests/unit/frontend/test_dashboard_manager.py` | 4 | 4 |
| `src/tests/unit/frontend/test_dashboard_manager_95.py` | 2 | 2 |
| `src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner2.py` | 4 | 4 |
| `src/tests/unit/frontend/test_dashboard_manager_handlers.py` | 6 | 6 |
| `src/tests/unit/frontend/test_n7_dataset_panel.py` | 16 | 16 |
| `src/tests/unit/frontend/test_restart_orchestration_handlers.py` | 6 | 6 |
| `src/tests/unit/test_dashboard_manager.py` | 2 | 2 |
| **total** | **89 across 12 files** | **89 across 12 files** |

`git diff --stat 30e15b7 fc62175` over those 12 files plus `test_d8_d11_phase4_truth_up.py`
and `test_model_registry.py` → **empty**. All fourteen are byte-identical.

**The X7 guard suites do not touch this surface.** The five suites added by the named PRs are
`test_x7_gate_soundness.py` + `test_x7_sites_outside_main_gate.py` (#585, from #569/#577),
`test_x7_status_cache_guards.py` (#587, from #580), `test_f042_depth_slider_bounds.py` (#572)
and `test_f046_selection_rebuild_contract.py` (#575). None references any of the nine handlers.
`test_f046_selection_rebuild_contract.py` is about **topology node** selection
(F-CANOPY-046), not model/dataset selection — a name collision, not a scope overlap.

**One test file on the selection lane did change**, and it is X7 collateral the design does not
know about: `src/tests/regression/test_model_select.py` (+2/-1), from `94220f0` (#567) making
`main._seed_training_state` async:

```python
-        main._seed_training_state(_FakeBackend(backend_type=backend_type))
+        asyncio.run(main._seed_training_state(_FakeBackend(backend_type=backend_type)))
```

That is a 13th selection-adjacent file, not one of the design's 12 sites, and it is already
repaired.

**On the design's own count.** §6 says "12 sites across 2 files (4 forced assertion inversions,
3 rendered vacuous, 1 premise destroyed, 4 callback-arity breaks)". Measured against
`fc62175` — and identically against `30e15b7`, so this is **not drift** —

- the §4.8 arity change alone breaks **12 call sites across 6 files**:
  `test_model_table.py:306,311`; `test_button_state.py:263`;
  `test_dashboard_manager_95.py:429,446`; `test_dashboard_manager.py:697,711`;
  `test_dashboard_helpers_coverage.py:813,835`;
  `test_dashboard_manager_handlers.py:766,782,789` — against the design's "4";
- the §4.11 "premise destroyed" assertion
  (`_gate_dataset_options_handler("", ...) == (no_update, no_update)`) appears **twice**, at
  `test_model_picker.py:105` and `test_n7_dataset_panel.py:155` — against the design's "1".

So the affected-site count has **not changed since 2026-09-02**, but it appears to have been
understated in the design *when written*. I flag this as a lead for Lane B/C; it is outside
my entry point to adjudicate, and it is not collateral drift.

---

## T5 — Prior-art check in juniper-ml

**Documents only. No code.**

Commits touching either selection document, on any ref (`git log --all -- 'notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-*'`):

| SHA | date | subject |
|-----|------|---------|
| `4d60c939` / `2083fc5f` | 2026-09-02T07:42 / 07:20 -05:00 | design(canopy): the catch-22 is a reachability defect (#1571) |
| `22c658d9` / `d050c8a9` | 2026-09-02T16:13 -05:00 / 21:30Z | refactor(docs): table formatting in canopy selection notes (#1574) |
| `e924ef87` / `04556de9` | 2026-09-02T17:05 / 17:14 -05:00 | design(canopy): adopt the six answers + iteration-2 scope (#1575) |
| `72711850` / `81439f38` / `bbed0562` | 2026-09-02T19:37 / 20:38 / 20:45 -05:00 | measure(canopy): OQ-N5 closed — both gates hold in a live DOM (#1588) |

**The last of these is `bbed0562`, 2026-09-02T20:45:44-05:00. Nothing after 2026-09-02 touches
either document.**

Content search for the arc across the ml tree
(`grep -rln "SELECTION-REACHABILITY-DESIGN" notes/ prompts/ reports/`):

- `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` (the evaluation, 09-02)
- `reports/2026-09-02_canopy-selection-deadlock/{round2_citations,round2_corrections,oqn5_browser_falsifier}.md` (09-02)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-04_x7-slice-1a-off-loop-discipline.md`

The last is the only post-2026-09-02 artifact, committed by `fd6ac4bd` (2026-09-04T10:48:02Z,
#1631). Its lines 163-164 read:

> **The original catch-22** — `(recurrence, equities_seq)` compatible but unreachable. Design:
> `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`; **PRs 1–3 unstarted.**

That is a first-party, dated, in-repo corroboration of this lane's independent finding.

Commit-message search across all ml refs since 2026-09-02 for `clearable`, `catch-22`,
`I-cover`, `OQ-N` → **empty**. Matches for `deadlock` → **empty**. Matches for `reachab` and
`selection` are all X7 design revisions, F-CANOPY-035/037/042/046 E2E docs, and unrelated
soak/handoff work. The only code produced in the neighbourhood is
`util/ad-hoc/2026-09-04_x7_offload_census{,_v2}.py` (`fd6ac4bd`), which measures X7's off-loop
sites — not this arc.

---

## Instrument-adequacy note

**Could a shipped change have been missed — e.g. landed under an unrelated commit message?**
This is the failure mode the reporting rules ask about, and it is the one my primary instrument
(commit messages) is weakest against. Five independent guards, none of which reads a commit
message:

1. **Content pickaxe across all refs, not just `main`.** `git log --all -S <string>` for
   `clearable=True`, `I-cover`, `restart-ds-type", "options"`, `swapped is False`,
   `staged_dataset`, `dbc.Toast`, `aria-describedby` — **all seven empty**, over the entire
   canopy history including unmerged branches. A pickaxe finds the change no matter what the
   commit was called.
2. **Whole-function sha1 comparison, not hunk inspection.** The nine handlers were extracted by
   name from both blobs and hashed. This is immune to line drift (which is real here: +63 and
   +13) and to a change hidden inside an unrelated commit's diff.
3. **Whole-`src/` diffstat.** All 46 changed files were enumerated;
   `src/model_registry.py` and `src/backend/recurrence_backend.py` are absent from it, so no
   change to them can exist regardless of how it was labelled.
4. **Unmerged and off-`main` surfaces.** `gh pr list --state open` (0), all 8 closed-unmerged
   PRs since 09-01 (inspected: all Cursor docs/tests), `git branch -a` (133 lines, local +
   remote), the centralized worktree directory (23 canopy entries, every one inspected by name;
   the single selection-named one opened and proved empty), canopy's own working tree (clean)
   and its four stashes (all pre-2026-08).
5. **Cross-repo.** juniper-data's lockfile checked by content *and* by
   `git log --all -S 'yfinance' -- requirements.lock` (empty over all history);
   juniper-recurrence has one commit since 09-02 and no `stage_dataset` anywhere.

**Residual risk.** Two narrow gaps remain. (a) Work living only in a local branch inside a
worktree I identified by directory name — I opened every canopy worktree whose name suggested
this surface, but I did not `git log` all 23 canopy worktrees individually; guard 1 partly
covers this, since `--all` sees any ref in the shared object store, and a worktree branch is
such a ref. (b) Work existing only as uncommitted edits in a worktree I did not `status` — the
same limitation. Both would be work that is by definition not shipped, so neither can change a
verdict from NOT SHIPPED to SHIPPED; at most they could change "no artifact" to "in progress",
as the empty `feature/selection-x1-model-truth` worktree already does.

**Direction of error.** Every guard here can only turn NOT SHIPPED into SHIPPED, never the
reverse. None did.

---

## Bottom line

The prior session's memory assertion — *"the fix is NOT yet implemented"* — **holds unchanged
three days later**, and is independently corroborated by an in-repo dated artifact
(`HANDOFF_2026-09-04_x7-slice-1a-off-loop-discipline.md:164`, "PRs 1–3 unstarted").

Zero of nine planned frontend handlers changed. One of two planned backend routes changed, and
only in *how* it executes (`sync` → `to_thread` → `offload`), not in what it reports. The test
surface is byte-identical. The design's line numbers are still valid modulo two constant
shifts. Nothing about the intervening three days invalidates the plan; it simply was not
started.
