# HANDOFF 2026-09-05 — round 36: the partial-data contract's last two halves shipped, a live `market_cap` corruption fixed, and round 35's corrections corrected

Successor to
`HANDOFF_2026-09-05_defect-register-round-35-apd-data-018-closed-and-the-partial-data-contract.md`
— cite this one by its full name.

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`). Its own validation status is §7. **Round 35's
central claim was falsified by validation, and its *corrections* were then partly falsified too** —
assume the same of this document. All dates UTC.

**A bare "§N" means a section OF this document.** Every reference to a section of any other file
names that file.

**Register moved 79 → 79 fixed, 17 → 17 open. This round closed no register entry, and that is
correct**: round 35's handoff directed its remaining-work list as FIRST WORK, and the register's
own §2 note records 16 of the 17 open rows as *parked*. The single unparked row is `APD-DATA-019`
(§0.3).

---

## 0. Remaining work

1. **Successor, first — validate this document (§7).** No round has run on it.
2. **`juniper-canopy`'s three-way prompt — the ONLY piece of the partial-data contract left, and it
   is now UNBLOCKED.** Both blockers named by round 35 are shipped: cascor#621 (the flag) and
   cascor#624 (`dataset_shortfall` + the non-clobbering merge). **The owner's option-numbering
   ambiguity is RESOLVED** — see §3.
   Canopy has **zero** occurrences of `allow_truncation` today. Its code is under `src/`, not
   `juniper_canopy/` (which holds only `__init__.py`); the dataset paths are `src/dataset_schema.py`,
   `src/main.py`, and the flows pinned by `src/tests/integration/test_apply_dataset_flow.py`.
3. **`APD-DATA-019` is the one unparked register row, and it needs an owner decision before code.**
   `total = len(filtered)` (`juniper-data/juniper_data/storage/base.py:537`) materialises the whole
   filtered set per page — **including on the cursor path** (`:545-548`), so `APD-DATA-011`'s keyset
   pagination did not touch it. The register's own assessment says a real fix needs a storage index
   **plus making `total` estimated, cached or absent** — the last being a **response-shape change for
   existing clients**. Do not start until the owner rules on `total`.
4. **`juniper-data#378` is OPEN, GREEN, and deliberately UNMERGED pending the owner's
   re-confirmation.** See §2 — its second half has a blast radius wider than the decision that
   authorised it.
5. **Carried from round 35, still unbuilt in cascor** (all filed in cascor#624's PR body): the
   annotation does not reach `get_metrics()` / `/v1/metrics`; `--allow-truncated-datasets` is
   **inert on `main.py`'s own run path** (its only consumer lives in the service process, and
   `main.py` reaches only `spiral`, which is not truncatable); `_auto_start_training` neither opts in
   nor surfaces its failure; **zero** docs mention the flag or its env var.
6. **Unfiled, and now with a second instance.** Round 35 noted
   `_PROJECT_API_TRUNCATABLE_GENERATORS` duplicates knowledge owned by juniper-data. Validation
   added: **two thirds of that set is unreachable** — `dataset_type`'s Literal excludes `csv_import`
   and `equities_seq`, so only `equities` can reach the line that reads the flag.

---

## 1. Verify starting state

Run each line standalone (§5.1).

```bash
git fetch origin
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
python3 util/ad-hoc/register_open_set.py
python3 util/ad-hoc/register_status_crosscheck.py
```

Expected, measured 2026-09-05: FIXED rows **79**; open-set **`96 rows | 79 fixed | 17 open`**;
cross-check **79 / 79 / 79, AGREE**. Unchanged from round 35 — see the note above on why.

---

## 2. What this session did

| PR | Result |
|---|---|
| **data#376** | **MERGED.** A same-day 8-K restatement kept the OLD share count. `sort_index()` defaults to quicksort — **not stable** — so `duplicated(keep="last")` picked arbitrarily among ties. Measured over the real 485-payload SEC cache: **54 tickers collide, 15 across 9 tickers resolved wrong** — DVA **10.43%**, ORLY 6.79%, KO 0.92%. **Live at defaults: ADSK is position 12 of `sorted(constituents)[:14]`.** Fix sorts on `(filed, end)` explicitly. |
| **data#377** | **MERGED.** Record corrections in 8 files (§4). |
| **ml#1791** | **MERGED** (`9523f7cc`). The juniper-ml half of the same corrections. |
| **cascor#621** | **MERGED** (`58a0d42`). Round 35 left it OPEN and RED. Unblocked twice — §5.2. |
| **cascor#624** | **MERGED** (`995be91`). The two contract gaps — §3. |
| **data#378** | **OPEN, GREEN, HELD.** The two owner decisions — §2.1. |

### 2.1 Why data#378 is held rather than merged

Its `CommonStockSharesIssued` rung is self-contained. Its **other** half — `fundamentals_fill`
default `"zero"` → `"nan"` — was authorised on the framing *"an unfillable fundamental reads as
missing"*. Building it surfaced a wider radius than that framing implies, and the owner was asked to
re-confirm:

* SEC XBRL reaches back only to ~2009, so this is **not** limited to unrescued tickers — **every**
  ticker has pre-filing rows. A default `start_date=2000` request now yields **~9 years of NaN** in
  `total_shares`, `market_cap` and `days_since_report` for **every** symbol.
* **`equities_seq` windows are no longer finite.** A test asserted `np.isfinite(X_train).all()`;
  that property is now false by default, and `equities_seq` feeds the **recurrence tier**. The
  assertion was rewritten to what it actually guarded (normalisation introduces no non-finite
  values), not deleted.
* **juniper-cascor has NO NaN guard on ingested dataset arrays.** Its only `torch.isfinite` covers
  weight patching, not `_artifact_to_tensors`. A NaN dataset reaches training as a NaN **loss**, not
  a named refusal.

The narrower alternative — NaN only for *unrescued* fundamentals, pre-filing rows staying `0.0` — is
a small change from the branch as it stands.

---

## 3. Owner rulings, 2026-09-05 — do not re-litigate

Round 35 flagged an ambiguity and recorded it **only in its own handoff prompt** — not in data#366's
body, not in the register, not in any note. It had therefore never reached the owner. Put to them
directly and answered:

| Question | Ruling |
|---|---|
| The spec numbers three options then says "option 2 … cancel the data load, deselect" | **Option 3 (fail) is the one that cancels and deselects.** As built. No rework. |
| The 3 tickers rescuable only by `CommonStockSharesIssued` | **Add the rung, annotated as degraded** with its own basis. Shipped in data#378. |
| Whether STZ justifies more than today's refusal | **No.** The contract already covers it. |
| Whether `fundamentals_fill="zero"` should stop being the default | **Yes → `"nan"`.** But see §2.1. |

### 3.1 The two cascor gaps, and the one that matters most

**A deployment default silently overrode the caller.** `{**jd_params, "allow_truncation": True}` put
the literal key **last** in the merge, replacing a caller's explicit `False`. Option 3 is expressed
by sending *neither* parameter — so on any deployment with the flag on, **"send neither" became
"accept" and option 3 was unreachable.** Now a default, not an override.

⚠ **The same shape exists one layer lower and is NOT fixed.** juniper-data ORs the request parameter
with its own env var, so a request still cannot opt **out** if
`JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION` is set. Neither env var is set in juniper-deploy today —
**assert that before claiming option 3 is enforceable end to end.**

**A log line is not a surface.** `_log_dataset_shortfall` logged and returned; nothing reached a
field, `get_status()`, the WS stream, metrics or results. `get_status()` now carries
`dataset_shortfall` (`None` when clean), which reaches `/v1/training/status` **and the WS training
stream together**, because the stream reads `get_status()`. **This is the field canopy renders.**

---

## 4. What validation falsified — read before quoting round 35

Four adversarial lenses ran against round 35's §3.5. Its *direction* held; several specifics did not.

| Round 35 claim | Verdict |
|---|---|
| The byte argument is inverted | **CONFIRMED** — 2.07 MB re-derived independently from the note's own table |
| …with a ~1,298 B envelope → 3.6 MB / 46 MB | **FALSIFIED** — internally inconsistent with the rows it corrects; not used |
| The inverted claim is in 2 files | **FALSIFIED — six**, incl. `juniper-data/juniper_data/core/limits.py`, the module that *owns* the cap |
| "37 → 1" is in the register's §5.1 row | **FALSIFIED** — the register contains **zero** rescue-ladder content |
| "37 → 1" → "29 → 1" | **CORRECTED to ">= 28 of 37"** — the probe covered 29; 8 were never probed |
| `keep="last"` is the bug | **Mechanism wrong** — it is `sort_index()`'s quicksort instability |
| The leak test is a tautology | **Overstated** — it catches some mutations but misses a real look-ahead in `total_shares` |
| Canopy owns the forced merge | **Wrong repo** — canopy has zero occurrences; it is cascor `manager.py` |

**Also established:** the `companyconcept` gap is an **upstream regression** (2026-06 → 2026-09), not
the published "dimensional facts are excluded" property — a June cache holds KO's *same 71 dei
facts*, KO is single-class, and all three genuine multi-class filers resolved fine. And the census
instrument **conflates throttling with absence** (403/timeout/404/empty → one verdict, no retries),
so "37" cannot be separated from *"37 minus however many were throttled"*.

**Changed by §4's corrections:** `juniper-ml/notes/JUNIPER_2026-09-04_JUNIPER-DATA_EQUITIES-INGEST-SIZING-AND-FIELD-AVAILABILITY.md`,
`juniper-ml/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`,
`juniper-data/juniper_data/core/limits.py`, `.../generators/equities/defaults.py`,
`.../generators/equities/generator.py`, `.../generators/equities/params.py`,
`.../tests/unit/test_equities_generator.py`, `juniper-data/CHANGELOG.md`,
`juniper-data/notes/releases/RELEASE_NOTES_v0.13.0.md`,
`juniper-data/util/ad-hoc/2026-09-04_equities_sizing_matrix.py`.

---

## 5. Traps

### 5.1 The sandbox refuses shell STRUCTURE, and refused more this round
Loops, `${PIPESTATUS}`, heredocs — all refused. **New:** a `cd <dir> && … && git …` chain is refused
("too complex to verify"), as is any `gh api` whose path is built inside a larger construct, and a
`sleep` followed by another command. Split into plain, separate commands. **cwd does not persist.**

### 5.2 CodeQL's unused-global block, and the fix that did NOT work
cascor#621 sat green-but-unmergeable on 4 unresolved CodeQL threads. **Adding the constants to
`constants_api/__init__.py`'s import block and `__all__` did not clear them** — verified against
`code-scanning/alerts`, which still returned 4 open. `cascor_constants` exists twice as a top-level
package, so an absolute import in `__init__.py` carries the same ambiguity. **The fix that worked is
`__all__` in the module where the name is DEFINED** (`constants_api_defaults.py`), generated by AST,
mirrored by `cp`. Alerts then read **0**. Memory `reference_codeql_unused_global_cascor` has the
detail.

### 5.3 `safe_merge` update-branches before it refuses
On the CodeQL refusal it had already run `update-branch`, so the remote had moved and the next
`git push` was rejected non-fast-forward. **Rebase onto `origin/<branch>`** after confirming your
previous head is an ancestor of it; never force-push over the merge commit it created. Also: the
SHA in `MERGED #N at <sha>` is the **head it merged**, not the resulting squash commit — verify
against `origin/main`'s tip, not that SHA.

### 5.4 juniper-ml `main` moves faster than its CI
ml#1791 was refused once: *"went BEHIND 3 times without a stable green head."* Retry when quieter.
(ml#1763 is open to re-tier `safe_merge` for exactly this.)

### 5.5 Golden snapshots need three collection gates
Adding a key to `get_status()` fails `Golden / Snapshot Regression`. `--slow` alone still **skips**.
Recapture with the lane's own invocation:
`GOLDEN_CAPTURE=1 python -m pytest -m golden --golden --slow --integration src/tests/integration`.

### 5.6 A small fixture will not reproduce a sort-stability bug
2–32-row synthetic frames all resolved *correctly*; the real KO payload needed **66** rows. Assert
the invariant, not the misordering — and prove the test fails against the old code before trusting
it. Memory `reference_unstable_sort_dedup_keeps_the_wrong_row`.

### 5.7 Environments
juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python`; juniper-cascor →
`.../JuniperCascor1/bin/python`. juniper-data cannot run one test file alone (circular import) —
pass `-p juniper_data.api.app`. `pytest -q` on top of addopts `-q` **suppresses the summary line**.

---

## 6. Git status

Written from harness worktree `compiled-inventing-sprout`, branch `docs/round-36-record-corrections`
(merged as ml#1791; the branch is behind `main` and can be discarded).

All three repos' `main` are current: juniper-ml `9523f7cc`, juniper-data `df71574` + #378 pending,
juniper-cascor `995be91`.

**Worktrees created this session and deliberately NOT removed** (cleanup needs the owner's explicit
signal, and `git worktree remove` deletes ignored files):

- `juniper-cascor--feat--allow-truncated-datasets-cli-flag--20260905-0631--77e02a86` (#621, merged)
- `juniper-cascor--feat--dataset-shortfall-operator--20260905-1600--e133bb15` (#624, merged)
- `juniper-data--fix--shares-duplicate-filed-stable-sort--20260905-1502--aae79ac2` (#376, merged)
- `juniper-data--docs--equities-record-corrections--20260905-1640--7064030d` (#377, merged)
- `juniper-data--feat--nan-fill-issued-rung--20260905-1730--bdcb98e0` (#378, **open**)

Two pre-existing stash entries in juniper-data belong to other sessions and were left untouched.

---

## 7. Validation of this document

**NOT YET VALIDATED.** Attack in this order:

1. **§2.1's blast-radius claims.** Re-derive the ~9-year NaN span and the `equities_seq` finiteness
   break yourself. If either is overstated, the hold on data#378 is wrong.
2. **§3.1's claim that juniper-data ORs the env var**, so option 3 is still not enforceable end to
   end. This is the highest-cost claim here — it says a shipped contract has a hole.
3. **§2's PR table** — verify each merge SHA is an ancestor of the right `main`, not merely resolvable.
4. **§4's table** — it says round 35 was wrong in six specific ways. Re-derive at least the "six
   files" and "the register carries none of it" claims.
5. **§1's expected values** — re-derive all three independently.

---

## 8. Session-close checklist

- [x] Round-35 §3.5 validated by four adversarial lenses; results in §4
- [x] Corrections propagated to all 10 files (ml#1791, data#377)
- [x] `sort_index` corruption found, reproduced against the real cache, fixed and mutation-pinned (data#376)
- [x] cascor#621 unblocked and merged; cascor#624 (both contract gaps) merged
- [x] Four owner decisions obtained and recorded (§3)
- [x] Memories written: `reference_unstable_sort_dedup_keeps_the_wrong_row`,
      `project_partial_data_contract_arc_2026-09-05`,
      `reference_cap_unit_must_be_measurable_ex_ante`; `reference_codeql_unused_global_cascor` extended
- [ ] **data#378 — owner re-confirmation on the NaN default (§2.1), then merge**
- [ ] **juniper-canopy three-way prompt — unblocked, and the last piece of the contract**
- [ ] `APD-DATA-019` — owner ruling on `total` before any code
- [ ] The four cascor follow-ups in §0.5
