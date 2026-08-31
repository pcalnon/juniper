# Where does cascor put a test partition?

**Project**: Juniper
**Sub-Project**: juniper-cascor
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-31
**Status**: FINDING — answers the blocking question in
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md) §9 S-1
**Read at**: cascor `origin/main` `da262a76`; `manager.py` verified byte-identical to the working tree read

---

## 1. The question and the answer

The partition design's §5 assigns `test` one job: *"the final reported score — touched **exactly once**,
after training completes."* Three plan versions and ten review agents assumed cascor could be pointed
at such a partition. It cannot.

**Answer: nowhere — and the architecture has no place for one, for a reason deeper than a missing
slot. cascor has no end-of-training evaluation step at all.**

## 2. Evidence

### 2.1 Four tensor slots exist. None is a test slot.

Enumerating every `self._{train,val,test,eval,holdout}_*` attribute on
`src/api/lifecycle/manager.py` returns exactly:

```
self._train_x   self._train_y   self._val_x   self._val_y
```

plus `self._eval_metrics_average`, `self._eval_metrics_enabled` (config flags) and the `_eval_split`
method. `grep -c '_test_x'` → **0**.

### 2.2 One slot, three writers, two real ingress points

| line | writer | source |
| --- | --- | --- |
| `:2195` | `self._val_x = X_val` | inline request (`InlineDataset.val_x`) |
| `:3533` | `self._val_x = new_val_x` | `arrays["X_test"]` at `:3451` — the juniper-data artifact |
| `:3293` | `self._val_x = pre.val_x` | **not an ingress** — `_PreSwapSnapshot` rollback (`:2939`, restored by `_rollback_pre_swap_state` at `:3270`); it mirrors whatever slots exist |

### 2.3 The single slot feeds BOTH training and reporting

- **Training**: `:2324` `self._executor.submit(self._run_training, self._train_x, self._train_y, self._val_x, self._val_y, …)` → `:2942` `fit(val_x=self._val_x, …)`
- **Reporting**: `_eval_split()` (`:1902-1909`) returns `self._val_x, self._val_y` → `_compute_eval_scalar_metrics` (`:1923`) → the metrics payload (`:2690-2691`, which labels the split `"validation"`)

This is the leak, structurally: **selection and reporting are the same tensor object**, not merely
the same rows.

### 2.4 The decisive finding — evaluation is LIVE, not final

`_compute_eval_scalar_metrics` (`:1911`) runs a forward pass on `_eval_split()`'s return. Its only
caller (`:1948`) is gated on:

```python
approx_len = len(self.network.history.get("train_loss", []))
if approx_len <= self._last_emitted_history_len:
    return None
return self._compute_eval_scalar_metrics()
```

— i.e. **it recomputes whenever a new training-history row appears**, during training, and serves the
result from the live metrics endpoint. Its own docstring confirms the intent: *"Called OUTSIDE
`_metrics_lock` so the forward pass does not extend that critical section (which `get_metrics` also
takes)."*

`grep` for a post-training finalisation hook (`_on_training_complete`, `_finalize`, …) returns only a
WebSocket broadcast at `:1424`. **There is no compute-final-metrics step.**

So the design's *"touched exactly once, after training completes"* has **no existing mechanism to
attach to**. Adding a `_test_x` slot would give the tensor a home and still leave nothing that
evaluates it once at the end.

### 2.5 The inline path drops an unknown field silently

`InlineDataset` (`src/api/models/training.py:19`) declares **no** `model_config`; `TrainingParams`
declares `model_config = ConfigDict(extra="forbid")` at `:62`. So a `test_x` sent to the inline
endpoint today is **accepted and discarded**, with no error.

## 3. What a fix requires — minimum, and the same for both candidate designs

1. A third tensor pair `_test_x`/`_test_y` on the manager.
2. Both ingress points extended (`:2195` inline, `:3533` artifact), plus `_PreSwapSnapshot` so a
   rollback does not silently drop it.
3. **A new end-of-training evaluation step** — this does not exist and is the substance of the work.
4. `_eval_split()` split in two: the in-loop signal versus the reported score. Today one method
   serves both callers.
5. `:2691`'s `"validation"` label corrected, so the payload stops calling a selected-on number a
   held-out one.
6. `InlineDataset` gains the third pair **and** `extra="forbid"`, or the new field is droppable in
   silence.

## 4. What this changes about the design choice

**It does not discriminate between the two candidates — and that is the useful part.**

The Lane B case for the cascor-local fix rested on it being ~36 lines needing no contract change, no
release and no re-baseline. That remains true of *those* costs. But items 1–6 above are required
**identically** by both paths: the local fix must also add a test slot, also split `_eval_split`, and
also invent the end-of-training evaluation. Its advantage was never in this area, and this work is
not avoided by choosing it.

Consequences for the comparison:

- **The local fix is more expensive than billed.** "Halve `X_test` and report the other half"
  understated it: there is no mechanism that reports a half *once*.
- **The ecosystem change's incremental cost falls**, relatively — the shared prerequisite is now
  visible on both sides of the ledger rather than only one.
- **This work is a genuine prerequisite either way**, so it can be scheduled and landed *before* the
  design choice is finally settled, without prejudging it.

That last point is the actionable one: items 1–6 are a coherent, self-contained, cascor-only change
that both designs need, that closes nothing prematurely, and that would make the reported metric
honest even before any contract work begins.

## 5. What this evidence cannot support

- **That items 1–6 are sufficient.** They are the minimum this trace establishes as *necessary*. I
  did not attempt a design for the end-of-training step, nor determine where it should be triggered
  (training-thread completion, the lifecycle state machine, or the `training_complete` broadcast at
  `:1424`).
- **Runtime behaviour.** No code was executed and no test was run. Every claim is read from source
  at `da262a76`.
- **The CLI arm.** This traces the *service* tier only. `spiral_problem.py`'s CLI path has its own
  ingress and is out of scope here (design decision 5, plan Chunk 6).
- **Whether any consumer depends on `:2691`'s `"validation"` label.** Correcting it may be a
  breaking change to a payload someone parses; I did not sweep for readers.
- **Snapshot/restore interaction.** `_PreSwapSnapshot` is named above because it writes `_val_x`, but
  I did not audit the wider snapshot format for whether a third pair must be persisted.
