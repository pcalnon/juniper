# HANDOFF 2026-08-19 — snapshot arc closed; R3 resume is next

Successor to
[`HANDOFF_2026-08-15_q6-resolved-and-owner-decision-register.md`](HANDOFF_2026-08-15_q6-resolved-and-owner-decision-register.md).

**Nothing from this arc is in flight.** Fourteen PRs merged (9 juniper-ml, 3 juniper-cascor,
2 juniper-deploy) plus one direct-to-main cascor commit. This document is the only deliverable
left, and the session that wrote it is landing it.

Citations are `file:NNN` for a **line** and `§N` only for a real **section heading**. Line
numbers are against **juniper-cascor `1d330f9`** (§7). Re-derive before editing: two of this
document's own citations were 11 lines stale on the first pass and landed in *different
functions*, and no single offset recovered the set.

> **This document was validated by three independent agents and FAILED the first pass.** The
> findings are folded in below. Two are worth knowing as warnings in their own right, and both
> are called out where they apply: the reuse design in §2.1 as originally drafted **would have
> silently stopped training**, and the "`load_network` has no production callers" claim that
> appeared in earlier documents is **false**.

---

## 1. Shipped this arc — do NOT redo

| PR | repo | what |
|---|---|---|
| ml#1129 | juniper-ml | Q-6 closure propagated into **10** stale register sites |
| ml#1136 | juniper-ml | **F-P1-2 closed — premise refuted**; P1.6 + P3 criteria 6/8 evidenced |
| ml#1137 | juniper-ml | snapshot-lifecycle design + §12 perf-lane phase gating + census script |
| ml#1138 | juniper-ml | Grafana port configurability proven; corrected D-1 remedy |
| ml#1144 → ml#1164 | juniper-ml | D-A demotion, then its **retraction** (§4) |
| ml#1150 / ml#1172 | juniper-ml | ecosystem port registry; S-5 answer recorded |
| ml#1181 | juniper-ml | cross-repo reference sweep preserved in `util/ad-hoc/` |
| deploy#183 / #186 | juniper-deploy | `PROMETHEUS_HOST_PORT`; monitoring tier honours `BIND_HOST` |
| cascor **`5f15a45`** | juniper-cascor | **optimizer restore fixed** — faithful class, state, lr. *(Landed on main via merge `cb8a30e`; `git show cb8a30e` shows the WRONG diff — use `5f15a45`.)* |
| cascor#534 | juniper-cascor | logger creates its dir on demand; `.gitignore` stops ignoring the snapshots package |
| cascor#536 | juniper-cascor | model constants re-extracted; **drift gate made to actually fire** |
| cascor#537 | juniper-cascor | service snapshot destination moved **out of the importable package** |

---

## 2. Open work — in the owner's stated priority order

> **The owner's order overrides the design's own sequencing.** The design
> (`SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md` §8) and the prioritisation note put **D-B** in
> Tier 1 ahead of everything and list no R3 item at all. The owner's 2026-08-19 instruction is
> R3 → S-1/S-2 → D-B, and **that governs**. Do not "correct" back to the design's order.

### 2.1 FIRST — R3 resume follow-on

**The owner's requirement, verbatim (2026-08-18):** *"restore a snapshotted network, observe
replay to gain insight into its training, edit the network based on that insight, and then
resume training … an iterative, experimental approach … one of the key purposes of the Juniper
project."*

Steps 1-3 work after `5f15a45`. **Step 4 throws the state away.** (Paths below are relative to
the cascor repo root — `api/…` means `src/api/…`.)

- `resume_from_snapshot` (`api/lifecycle/manager.py:4671`) calls `_load_snapshot_to_network`
  at `:4702`, sets `_resume_point_epoch` at `:4723`, `mark_resume_ready()` at `:4724`. Nothing
  in `:4702-4739` touches the optimizer, so the faithful one survives that far.
- The training pass then runs `train_output_layer`, whose `cascade_correlation.py:2063` is an
  **unconditional** `self.output_optimizer = self._create_optimizer(output_layer.parameters())`.
  The restored optimizer is replaced before its first step. Note there are **three** call sites
  — `:1891` (initial pass in `fit`), `:4594` and `:4823` (per-round grow passes) — so a
  reuse-when-valid change lands on all three, not just the one the §5 grep anchors.

**Two facts about the owner's workflow that reframe the whole item:**

- **`resume_from_snapshot` re-reads the snapshot from disk.** `_load_snapshot_to_network`
  (`manager.py:4504`) globs `<snapshots_dir>/<id>.h5` and replaces the network (`:4515-4523`).
  So step 4 discards **all in-memory edits, not just the optimizer**, unless the operator
  re-snapshots after editing. The owner's loop is therefore
  restore → replay → edit → **re-snapshot** → resume — which is exactly what cascor#225's
  round-trip test does. Confirm the intended loop before designing.
- **`/restore` and `/resume` land in different FSM states.** `load_snapshot` →
  `INVESTIGATING`; `resume_from_snapshot` → `mark_resume_ready()` → `RESUME_READY`. The edit
  endpoints (`add_hidden_unit_manual` `:4185`, `remove_hidden_unit_manual` `:4303`) hard-require
  `is_investigating()`, so they are **unreachable from the state `/resume` produces**. Editing
  happens in the restore state, before resuming.

The recreation is correct but **over-broad**. Its comment (`:2049-2053`) justifies it by the
parameter space changing *when a hidden unit is added* — true on growth, false for a resume
that has not grown.

#### ⚠ The obvious fix is a trap — read this before designing

The natural shape ("reuse when the optimizer is still valid: same class, `param_groups` shapes
match the rebuilt `nn.Linear`") **is broken, and fails silently.**

`_load_optimizer_state_from_hdf5_helper` builds a **local** `nn.Linear`
(`snapshots/snapshot_serializer.py:1049`) and binds the restored optimizer to *its* parameters
(`:1135`). `train_output_layer` builds a **different** local layer (`cascade_correlation.py:2054`).
The shapes are identical by construction, so a shape check **passes** — then `loss.backward()`
(`:2096`) populates `.grad` on the new layer's Parameters while `optimizer.step()` (`:2098`)
iterates the *old* ones, whose `.grad` is `None`. A **no-op**. `:2110-2112` copies the
unchanged weights back. Loss is still logged, callbacks still fire: **the output layer silently
stops training.**

Two shapes that actually work:

- **(a) preferred** — build via `_create_optimizer` as today, then
  `new_opt.load_state_dict(old_opt.state_dict())`, guarded by class equality. Torch's optimizer
  `state_dict` is **positionally indexed**, so it re-binds to the new Parameters correctly.
- **(b)** persist the `nn.Linear` on the network and reuse the layer object too — needs
  serializer support and is the larger change.

#### Everything else a correct implementation must handle

- **`_zero_optimizer_state_for` (`manager.py:4127`) is inert today and becomes the hazard under
  reuse.** It looks up `optimizer.state.get(parameter)` by tensor identity, passed
  `self.network.output_weights` (`:4091`) / `hidden_units[i][field]` (`:4080`) — never a
  Parameter the optimizer holds. Harmless while the optimizer is rebuilt anyway; under reuse it
  means a **weight edit is stepped with pre-edit Adam moments**. This is the guard that makes
  `PATCH /v1/network/weights` safe, and it does not currently work.
- **`PATCH /v1/training/params` can change `learning_rate` and `optimizer_type`** (`manager.py:3579`,
  and `:53-57` writes `network.config.optimizer_config.optimizer_type`). Reuse must compare the
  restored optimizer against `self.config.optimizer_config.optimizer_type` — comparing it to
  *itself* always passes — and must make an explicit decision about lr.
- **`output_optimizer` does not exist on a fresh network.** It is assigned only at
  `cascade_correlation.py:2063` and never in `__init__` (`test_p1_fixes.py:190` asserts
  `not hasattr(...) or is None`). Use `getattr(self, "output_optimizer", None)`; a bare access
  raises `AttributeError` on the first `fit`. That same guard subsumes the `None` written by a
  degraded restore (`snapshot_serializer.py:1044`) and by `add_hidden_unit_manual`
  (`manager.py:4259-4260`) / `remove_hidden_unit_manual` (`:4344-4345`) — so no separate
  topology-change flag is needed.
- **Premise worth confirming cheaply:** the restored optimizer does survive from
  `resume_from_snapshot` to `train_output_layer` — `start_training` only recreates a network
  when `self.network is None` (`manager.py:4185`), and `create_network` refuses while
  INVESTIGATING (`:1512-1513`) though not while RESUME_READY.

#### The gate this will actually meet

`src/tests/integration/test_golden_trajectory.py` pins per-epoch losses/accuracies to
checked-in goldens at rtol=1e-3 plus the exact growth sequence, run by
`.github/workflows/golden-regression.yml`. It is **skipped unless `--golden`**
(`src/tests/conftest.py:208`, `:243-247`), so a green local `pytest tests/unit/` proves nothing
about it:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CASCOR_NUM_PROCESSES=1 \
  python -m pytest -m golden --golden --slow --integration src/tests/integration/test_golden_trajectory.py
```

**A correct fix is golden-neutral, and here is why** — so a diff means *bug*, not *expected*:
in the growth loop `train_output_layer` is only called right after a unit is installed
(`:4594` after `add_units_as_layer`, `:4823` via `_retrain_output_layer`), so the parameter
space always grew and a correct check always recreates. The only unchanged-space call is the
initial pass in `fit` (`:1891`), which on a cold start has no optimizer at all.

**Tests that would make it credible:** resume from a snapshot and assert the optimizer's `step`
**continues** rather than restarting; **and** a second test asserting growth **still** forces a
rebuild. Without the second, the first proves nothing. The natural homes are
`src/tests/unit/test_p1_fixes.py:96-106` and
`src/tests/unit/test_snapshot_serializer_coverage_final.py` (`:99-100` Adam, `:128` SGD,
`:158` lr, `:173-184` save→load state) — the two files `5f15a45` touched.

### 2.2 SECOND — S-1 / S-2

Both are in the design's **§9** open-questions table.

- **S-1 — should snapshots move out of the repo checkout entirely?** cascor#537 moved the
  service destination out of the importable *package* to `<repo>/snapshots`, deliberately
  staying inside the checkout because S-1 is unanswered. `juniper-canopy` already uses a
  repo-root `snapshots/` (`juniper-canopy/scripts/juniper-canopy.service:54`), so the current
  layout matches an existing convention. Going outside the checkout (e.g.
  `~/.local/state/juniper-cascor/snapshots`, mirroring the experiment `RUN_DIR` convention)
  would make the fix structural, at the cost of changing default paths for both tiers.
- **S-2 — is the March–April 2026 cohort of retained research value?** 27,005 files (exact),
  96.9% of the frozen census denominator. The **retention decision** is not answerable until
  the design's **§6.2 (Phase 2) index** exists and can characterise what those files are — that
  ordering is the point of the design. **But running the census is not blocked**:
  `util/ad-hoc/2026-08-16_snapshot_archive_census.py` (`--census` / `--sample`) is read-only,
  has no delete path, and is the cheapest progress available.

### 2.3 THIRD — D-B (owner asked to DISCUSS before implementing)

**Do not implement this. The owner asked for a discussion first.** Scoped here only so the
discussion has facts, and deliberately kept thin — an earlier draft of this section read like a
work order while containing a false premise.

A **corrupt** snapshot is reported as **`404 Not Found`**, fusing *pick another snapshot* with
*investigate data loss*, across `restore` / `retrain` / `resume` / `replay`
(`api/routes/snapshots.py` raise sites `:252`, `:303`, `:350`, `:407`; plus three occurrences
of the reason string in `manager.py` at `:4584`, `:4628`, `:4704`).

> **CORRECTION — a claim in the earlier documents is FALSE.** ml#1144, ml#1164, the design doc
> (§4.2) and the prioritisation note all state that *"`load_network` has no production callers"*
> and that *"a fix applied only to `load_network` would change nothing."* **Both are wrong, and
> inverted.** `load_network` (`snapshot_serializer.py:877`) is the live loader:
> `_load_snapshot_to_network` (`manager.py:4504`) calls it at **`:4523`**, and
> `cascade_correlation.py:5130` calls it too. It is where absent and corrupt collapse to `None`,
> and therefore the only place that can separate them — paired with error-mapping in
> `_load_snapshot_to_network`, which currently flattens every failure to `return False`
> (`:4524-4526`). The false claim came from a grep truncated by `head -12`; see §4 item 4.

Also note `verify_saved_network`'s `'Invalid format'` (`snapshot_serializer.py:268`) is
misleading — it fires from the `_validate_format` gate before any payload inspection.

---

## 3. Live state — probed 2026-08-19/20; re-probe rather than trusting

- **juniper-cascor** `origin/main` `1d330f9`; primary checkout current and clean; **zero open PRs**.
- **juniper-ml** `origin/main` **`0288cef`** (#1184). Note `c3cf395` is the *authoring
  worktree's HEAD*, not `origin/main` — an earlier draft conflated them, which made §5's own
  `HEAD..origin/main` command non-empty. ml#1184 merged 2026-08-19T23:59Z; zero open PRs.
- **juniper-deploy** #183/#186 merged. **The local deploy checkout was three commits behind
  `origin/main`** and still showed the pre-#186 literal — a live instance of §4 item 5.
- Snapshot archive: `juniper-cascor/src/cascor_snapshots/` **27,885** `.h5` live today. The
  design's census froze at **27,869** (`SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md:50`), which is
  the denominator for the 96.9% and the 88/89 sample. The service dir `src/snapshots/` holds
  **no `.h5`** — 7 tracked source files, plus a gitignored `snapshot_history.jsonl` runtime
  artifact still on disk (`.gitignore:76`).
- `CI — juniper-cascor-model` is green on main again (cascor#536, run 2026-08-19T21:23Z). It
  had been **red on main since 2026-07-20**; last green before that was 2026-07-03.

---

## 4. Method lessons this arc paid for — read before starting §2.1

Three retractions (items 1-3) plus two process lessons (items 4-5). Each retraction was a
**correct mechanism paired with a wrong consequence** — the mechanism checked out, the "so
what" did not.

1. **One file is not a cohort.** The snapshot census first generalised from the single oldest
   file — an Oct-2025 husk — and would have declared 97% of the archive dead, making an
   aggressive sweep look justified. A stratified sample showed **88/89 valid**.
2. **"I checked the consumers" is not "I checked all the consumers."** D-A was demoted to
   "inert" after tracing `output_optimizer` to the training loop — but the trace never read
   `load_snapshot`'s own docstring (`manager.py:4558-4571`, phrase at `:4563`), which says a
   restored network **"cannot start training directly"**. Independent friendly and adversarial
   reviews both refuted the demotion; the defect was in fact destroying optimizer state on
   every load→save cycle.
3. **Grep the behaviour, not the token.** "The model package has neither override" came from
   grepping the *variable name* `_PROJECT_LOG_DIR_OVERRIDE`. The model honoured
   `JUNIPER_CASCOR_LOG_DIR` via a differently-named bare `or`. Only W-6 was genuinely absent.
4. **Never truncate a sweep — it cost this arc twice.** The first reference sweep piped through
   `head -50` and hid a cross-repo reference in juniper-canopy. The *same mistake*, `head -12`,
   produced the false "`load_network` has no production callers" claim in §2.3 — which then
   propagated into two merged PRs, the design doc and the prioritisation note before a
   validator caught it. Use
   `util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash`, which prints full per-group counts
   for exactly this reason, **before any move or rename**. It turned a confident two-constant
   list into eight load-bearing references, including a systemd `ReadWritePaths` entry whose
   omission silently EPERMs every save.
5. **Read from the right tree.** A post-merge check reported changes missing because it read a
   checkout three merges behind. Verify with `git show origin/main:<path>`, not the working tree.

**And the meta-lesson:** this document failed its own validation pass. Handoffs inherit errors
across generations — validate with independent agents before landing one.

---

## 5. Verification commands

```bash
JUNIPER=/home/pcalnon/Development/python/Juniper      # absolute: ../juniper-cascor fails from a worktree
conda activate JuniperCascor1                          # REQUIRED — unsuffixed JuniperCascor has broken torch

git -C "$JUNIPER/juniper-ml" fetch --prune
git -C "$JUNIPER/juniper-ml" log --oneline HEAD..origin/main    # empty before committing
gh pr list --state open                                          # dup-guard; goes stale in minutes

# R3: the unconditional recreate that discards the restored optimizer
grep -n "self.output_optimizer = self._create_optimizer" \
  "$JUNIPER/juniper-cascor/src/cascade_correlation/cascade_correlation.py"      # ONE hit, ~:2063

# R3 trap: the restored optimizer is bound to a THROWAWAY layer
sed -n '1049p;1135p' "$JUNIPER/juniper-cascor/src/snapshots/snapshot_serializer.py"

# D-B: the fused 404 — four route sites + three manager sites
grep -c "not found or failed to load" \
  "$JUNIPER/juniper-cascor/src/api/routes/snapshots.py" \
  "$JUNIPER/juniper-cascor/src/api/lifecycle/manager.py"                        # expect 4 and 3

# D-B: load_network DOES have production callers (the corrected claim)
grep -rn "\bload_network\b" "$JUNIPER/juniper-cascor/src" --include=*.py | grep -v "/tests/"

# The optimizer-restore contract (the suites 5f15a45 actually touched)
( cd "$JUNIPER/juniper-cascor/src" && python -m pytest \
    tests/unit/test_p1_fixes.py tests/unit/test_snapshot_serializer_coverage_final.py -q --slow; echo "exit=$?" )

# Before ANY move/rename, enumerate references properly
"$JUNIPER/juniper-ml/util/ad-hoc/2026-08-19_ecosystem_reference_sweep.bash" 'PATTERN'
```

**Gotchas that cost real time:** `gh pr checks` has **no `--json`** in this build (gh 2.46.0) —
parse the tab-separated output, column 2 is the bucket. `ss -tlnpH 'sport = :A' 'sport = :B'`
is malformed and returns **empty with exit 0**; one port per call. cascor's `tests/unit` runs
can omit the `=== N passed ===` summary — key on the **exit code**.

---

## 6. Required reading, and where it is stale

- **`notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`** —
  the design of record. Read **§9's S-5 ANSWERED block** (what §2.1 condenses) and **§4.1's
  RETRACTION**. ⚠ **§5's R3 row and §6.3's D-A row are STALE** — they still carry the retracted
  "requirement in question / D-A is inert / do not add a state-survives test" position, and a
  top-down reader hits it twice before reaching the current one. §4.2's `load_network` claim is
  **false** (§2.3 above).
- **`notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`** —
  companion prioritisation note; carries the same false `load_network` claim.
- **`notes/JUNIPER_2026-05-01_JUNIPER-ECOSYSTEM_PHASE-6E-SPRINT-B-DESIGN.md` §2.1/§2.3** — the
  restore/retrain/resume verb contract that `load_snapshot` (`manager.py:4556`) and
  `resume_from_snapshot` (`:4703`) cite as spec.
- **`util/ad-hoc/2026-08-16_snapshot_archive_census.py`** — the census S-2 needs.

---

## 7. Git state and procedure

- **juniper-ml** `origin/main` **`0288cef`**; this document is on
  `docs/handoff-snapshot-arc-closeout`. **Re-probe these before relying on them** — this block
  reads as authoritative and was wrong on the first pass.
- **juniper-cascor** `origin/main` `1d330f9`; item 1 is a **cascor** change.
- **Worktrees are the standing default** for task work — centralized in `Juniper/worktrees/`,
  per the parent `CLAUDE.md` and each repo's `notes/` setup/cleanup procedures.
- **cascor's `ci.yml` no longer has the `feature/**` / `fix/**` push globs** (removed
  2026-08-13), so a pushed branch with **no PR shows zero checks** — that is expected, not a
  broken pipeline. Open the PR.
- **`required_signatures` is live fleet-wide**: a headless local commit cannot land. Sign, or
  use `juniper-ml/util/open_signed_pr.py`.
- **Merge queues are unavailable to Juniper** — they require org/enterprise ownership and every
  repo is user-owned. Settled by policy validation 2026-08-18; **do not re-raise it**. The
  working technique is a merge-when-green watcher that re-issues
  `gh api -X PUT repos/OWNER/REPO/pulls/N/update-branch` on `BEHIND` and merges on `CLEAN`;
  budget generously — one cascor CI cycle plus a branch update exceeds 30 minutes.
