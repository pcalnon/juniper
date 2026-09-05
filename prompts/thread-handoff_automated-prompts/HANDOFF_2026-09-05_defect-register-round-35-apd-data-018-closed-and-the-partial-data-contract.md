# HANDOFF 2026-09-05 — round 35: `APD-DATA-018` closed, a look-ahead leak found by a derived field, and a partial-data contract with more left than it first appeared

> **The filename says "the partial-data contract" and the first draft's title said "two-thirds
> built". Validation falsified that.** The filename is kept because it is the archived identifier;
> the estimate it implies is not to be trusted. §0.2 has the real remaining set.

The standing mandate is unchanged: keep closing entries in the ecosystem defect register
(`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, ml#1092), one small reviewable PR
per entry or per group, plus a juniper-ml PR recording it.

Successor to
`HANDOFF_2026-09-03_defect-register-round-33-close-protocol-made-resident-and-the-actionable-set-reached-empty.md`
— cite this one by its full name. **Validate this document with independent agents before trusting
it** (memory `feedback_validate_handoff_prompts_independently`); its own validation status is §7.
All dates UTC.

**A bare "§N" means a section OF this document.** Every reference to a section of any other file
names that file.

**Register moved 78 → 79 fixed, 18 → 17 open.** `APD-DATA-018` closed. The work then continued past
the register into an owner-specified partial-data contract. **The first draft of this document called
that contract "two-thirds delivered" and said canopy was all that remained. Adversarial validation
falsified both.** See §0.2 for the five gaps, four of them in juniper-cascor.

---

## 0. Remaining work

1. **Successor, first — validate this document (§7). One round has run; its findings are applied
   below and a SECOND is owed.** Round 1 falsified this document's central claim, so do not assume
   the corrections are themselves right.
2. **CANOPY IS NOT THE ONLY THING LEFT. That claim was FALSE and is withdrawn.** Adversarial
   validation found five substantive gaps, four of them in juniper-cascor, and one of them makes
   canopy a *contract* task rather than the UI task this document originally called it. Ordered by
   what blocks what:

   **(a) `progress, metrics and results` are NOT annotated — only the dataset is.** The owner's
   clause is explicit and is unmet on *both* the CLI and canopy paths. juniper-data does its half
   (`DatasetMeta.truncation` / `.data_quality`, persisted). juniper-cascor **logs the shortfall and
   discards it**: `_log_dataset_shortfall` emits `self.logger.warning(...)` and returns. Nothing
   reaches a manager field, `get_status()`, the WS stream, metrics or results. **Canopy therefore
   has nothing to read**, which is why (a) blocks the canopy work. The nearest precedent,
   `_validation_warning`, is itself written and never read outside tests — so cascor currently has
   *no* working mechanism for annotating a run.

   **(b) The flag is inert on `main.py`'s own run path.** Its only consumer is
   `Settings().allow_truncated_datasets` inside `TrainingLifecycleManager._reload_dataset`, which
   runs in the **service** process. `main.py` → `SpiralProblem` → `SpiralDataProvider` fetches the
   `spiral` generator (not truncatable) and never constructs a lifecycle manager. The flag parses,
   its tests pass, and it does nothing where it is advertised — the
   `reference_instrument_answers_an_adjacent_question` class.

   **(c) Auto-start neither opts in nor fails the run.** `_auto_start_training` never forwards
   `allow_truncation`, so an opted-in deployment with `auto_dataset=equities` still gets a 422 — and
   `except Exception: logger.exception(...)` swallows it in a background task. The service stays up
   and healthy with no training and no failure. *"The run itself fails"* is met on the staged path
   (RuntimeError → 409 → non-zero driver exit) and **unmet here**.

   **(d) Canopy's option 3 is unreachable when the service flag is on.** The forced
   `{**jd_params, "allow_truncation": True}` is last in the merge, so it overrides a caller-supplied
   `allow_truncation: False`. "Send neither" silently becomes "accept".

   **(e) Docs**: zero mentions of `--allow-truncated-datasets` / `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS`
   anywhere in juniper-ml's `docs/`.

3. **THEN juniper-canopy's three-way prompt.** The owner's spec
   (2026-09-05, quoted verbatim in §3) requires canopy to present a meaningful error and require an
   affirmative choice of one of three:
   - **accept** broken rows and continue → `allow_truncation=true`, `incomplete_rows="accept"`
   - **drop** broken rows and continue → `allow_truncation=true`, `incomplete_rows="drop"`
   - **fail** the data load completely → send neither; juniper-data answers 422
   Options 1 and 2 must annotate progress, metrics and results. Option 3 must show a meaningful
   error, **cancel the load, deselect the selected dataset, and let the user pick another**.
   Both parameters exist and are live at the juniper-data boundary, but **this is NOT a
   UI-only task**: it is blocked on (a) above, because canopy has no annotated progress/metrics to
   render, and on (d), because option 3 cannot be expressed while the service flag is on.
4. **AN AMBIGUITY THE OWNER HAS NOT YET RESOLVED — do not guess a second time.** The spec numbers
   three options, then says *"option 2 should provide a meaningful error message, cancel the data
   load, deselect the selected dataset"*. Option 2 is *drop and continue*, which cannot also cancel
   and deselect. I read it as **option 3** and built the data layer that way (accept and drop both
   annotate and continue; only fail cancels). **This was flagged to the owner and not answered.**
   Confirm before building the canopy flow on it.
5. **Carried, and each is an owner decision, not a task**: the 3 tickers rescuable only by
   `CommonStockSharesIssued` (issued ≠ outstanding — `market_cap` would quietly mean something else
   for them); whether `STZ` — the one genuinely unrescuable name — justifies anything beyond today's
   refusal; and whether `fundamentals_fill="zero"` should stop being the default now that it is
   known to fabricate an impossible value.
6. **Unfiled**: `_PROJECT_API_TRUNCATABLE_GENERATORS` in juniper-cascor duplicates knowledge that
   lives in juniper-data. Its drift cost is a hard failure with a clear message, not silent bad
   data, which is why it was accepted — but it is a fork-drift row waiting to be filed.

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
cross-check **79 / 79 / 79, AGREE**.

---

## 2. What this session did

| PR | Result |
|---|---|
| data#321 | `arc_agi` incident record — three error classes, four sites |
| ml#1604 | register: close protocol made **resident**, park taxonomy defined |
| ml#1606 | round-33 handoff + the citation rule ml#1604 itself broke |
| data#326 | `csv_import` **byte** cap, 422-until-opt-in, permanent annotation |
| ml#1647 | register: `APD-DATA-018` owner decision + csv_import half |
| data#348 / ml#1669 | equities sizing measurement + the analysis document |
| data#354 / ml#1714 | equities **symbol** cap (14); `APD-DATA-018` **CLOSED**, 79/17 |
| data#362 / ml#1738 | six free fields; **look-ahead leak**; empty-concept fallback bug |
| data#366 | shares **rescue ladder** (37 → 1) + the fail/accept/drop contract |
| **cascor#621** | `--allow-truncated-datasets`, and the run fails when unset. **NOT MERGED at the time of writing — it was OPEN and RED.** The constants edit was not mirrored into `juniper-cascor-model/`, failing `test_extracted_modules_match_cascor_src` on three runners (the documented verbatim-extraction drift class). Mirrored, and a false precedence claim corrected, in a follow-up commit; **confirm its state before trusting this row.** Every other row here was verified merged and an ancestor of the right `main`. |

---

## 3. The four findings worth carrying

**1. The unit belongs to the cost, not to the register.** One row, two halves, two different units,
both right. `csv_import` bounds **bytes** (its input is a file). `equities` bounds **symbols**,
because measurement showed its cost is per *request*: **163× the payload costs 1.16× the time**. One
symbol over 26 years is 210 KB / ~2 s; the Russell 3000 over *one day* is 92 KB / **1.7–3.2 h**. A
byte cap there is **anti-correlated** with cost — it would admit the expensive request and reject
the cheap one. Never transfer a cap's unit between generators without re-measuring what the cost
tracks.

**2. A derived field audits the field it derives from.** `days_since_report` was added as a *free*
column. Its first live run returned **−19 days** — impossible, and the symptom of a **look-ahead
leak in `total_shares`/`market_cap` that had been shipping for months**: the SEC series was aligned
on the *period end* and forward-filled, so a quarter ending 2021-03-27 but not filed until
2021-04-29 reached every trade date in those five weeks. A wrong share count looks like a share
count; a negative age looks like nothing. **Deriving a quantity with a known-impossible range out of
one with no obvious range turns a silent error into a loud one**, and costs nothing when the source
is already downloaded.

**3. Truthiness is not a "has data" test.** `if payload.get("units")` accepted SEC's
`{"units": {"shares": {}}}` — a **truthy empty container** — and broke out of the fallback loop, so
12 tickers with perfectly good data under the second tag got `market_cap = 0.0`. Count the elements;
never test the container.

**4. `companyconcept` and `companyfacts` disagree for the same CIK, taxonomy and tag.** For `KO`:
636 bytes / **0 facts** versus **71 facts** / 4.30 B shares. Both endpoints omit *dimensional*
facts, and multi-class filers tag shares per share class. **The 37 "missing" tickers were never
missing data — it was the wrong endpoint.** 37 → 1 (`STZ` alone). `companyfacts` costs ~1.15 s and
~5 MB against ~0.20 s and ~600 B, so it is a **fallback rung**, not the primary path: paying it per
symbol would cut the 14-symbol cap to ~9.

---

## 4. The contract as it now stands

**juniper-data** (`core/limits.py` owns all of it):

| Gate | `incomplete_rows` | Outcome |
|---|---|---|
| unset *(default)* | — | **422**, naming affected symbols, row count, both remedies |
| set | `accept` | rows kept and filled, `DatasetMeta.data_quality` annotated |
| set | `drop` | symbols excluded, **still annotated with what went** |

`allow_truncation` is the gate (request param · `JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION` · `.env`).
Truncation says *how much is missing*; `data_quality` says *what is wrong with what is present* —
`degraded` (recovered from a weaker source) is deliberately **not merged** with `unrescued`.

**juniper-cascor**: `--allow-truncated-datasets` → exports the env var *before* the first
`Settings()` (the idiom `--config` already uses, so the flag beats env and YAML). Unset ⇒ the 422
becomes a run failure whose message names all three surfaces; set ⇒ the shortfall is re-logged at
WARNING on that run, because an operator reading a training log never opens the artifact.

---

## 5. Traps

### 5.1 The sandbox refuses shell STRUCTURE, and got stricter
`for … done`, `${PIPESTATUS}`, heredocs inside `&&` lists — all refused. **New this session**: a
standalone heredoc is *also* refused when its body contains an apostrophe in prose or a `$(…)`; and
`awk` programs are refused outright. Fall back to the Edit tool. **cwd does not persist.**

### 5.2 `safe_merge` — prefer it, but read the last line
It won repeatedly here where `--auto` + manual `update-branch` lost. **Exit 0 is never proof**: look
for `MERGED #N at <sha>`, then confirm `git merge-base --is-ancestor <sha> origin/main`. On an
exit-0 timeout, check `autoMergeRequest` — **armed ⇒ wait, do not retry**; `net disarmed` ⇒ nothing
will land it.

### 5.3 juniper-data cannot run one test file alone
A pre-existing circular import (`csv_import/__init__` → `generator` → `api.settings` → `app` →
`routes.generators` → back). Pass `-p juniper_data.api.app` to force the order. Confirmed on `main`,
not introduced here.

### 5.4 Environments
juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python`; juniper-cascor →
`.../JuniperCascor1/bin/python`. The system `python3` lacks pandas/hypothesis and will mislead you.
`pytest -q` on top of addopts `-q` **suppresses the summary line**.

### 5.5 Sequence Safety fires on extract-method and on renames
Waive with `Allow-Symbol-Loss:` trailers, enumerated with reasons, and **pass an explicit
`--body-file` at squash so they survive** — verified twice (`grep -c` = 2 on the merge commit).

---

## 6. Git status

Written from harness worktree `cozy-wibbling-nebula`. Branches cut from `origin/main`.
`juniper-data` restored to `main` at `0 0` and clean. **`juniper-cascor` is NOT on `main`** — it sits
on `feat/allow-truncated-datasets-cli-flag`, because that branch had not merged (§2). Restore it once
cascor#621 lands. Concurrent
sessions were active throughout — one landed the three-partition `X_val` contract on top of this
session's equities work mid-session, without conflict.

---

## 7. Validation of this document

**NOT YET VALIDATED.** Attack in this order:

1. **§3's four findings** — each is a claim about live external APIs. Re-derive the KO
   `companyconcept`-vs-`companyfacts` disagreement and the −19-day leak yourself; both are
   reproducible in one command.
2. **§0.2's claim that canopy is the ONLY unfinished deliverable.** Re-read the owner's spec against
   what shipped. If any clause of the CLI half is unmet, that is the highest-cost miss here.
3. **§0.3's ambiguity** — confirm the option-numbering reading was flagged and not silently decided.
4. **§2's PR table** — verify each merge SHA is an ancestor of the right `main`.
5. **§1's expected values** — re-derive all three independently.

---

## 8. Session-close checklist

- [x] `APD-DATA-018` closed; register at 79/17, cross-check AGREE
- [x] juniper-data contract shipped (data#366)
- [ ] **juniper-cascor CLI half — NOT shipped.** cascor#621 was OPEN and RED when first reported as
      shipped; the drift failure is fixed but the merge is unconfirmed. Verify before relying on it.
- [x] Handoff document generated (this file)
- [x] PR opened for this document — **ml#1757**
- [x] Consensus validation round 1 — falsified §0.2's central claim; findings applied above
- [ ] **Consensus validation round 2** — owed, because round 1's corrections are themselves unvalidated
- [ ] **The four juniper-cascor gaps** (§0.2 a–e); (a) blocks canopy
- [ ] **juniper-canopy three-way prompt** — blocked on §0.2(a), §0.2(d), and the §0.4 ambiguity
