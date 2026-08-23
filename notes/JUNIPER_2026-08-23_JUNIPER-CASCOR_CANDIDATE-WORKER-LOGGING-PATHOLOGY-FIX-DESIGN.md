# Design — the candidate-worker logging pathology, and the CLI-vs-service wall gap it causes

**Project**: juniper-cascor (design authored in juniper-ml) · **Author**: Paul Calnon
**Created**: 2026-08-23
**Evidence**: [`JUNIPER_2026-08-21_…RESIDUAL-WALL-GAP-EVIDENCE.md`](JUNIPER_2026-08-21_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-RESIDUAL-WALL-GAP-EVIDENCE.md) ·
[`JUNIPER_2026-08-20_…SEED-REPRODUCIBILITY-EVIDENCE.md`](JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-SEED-REPRODUCIBILITY-EVIDENCE.md)
**Baseline SHA**: cascor `362b88b1475eb40f4f8aa0a28caa9755ec812722`

---

## 1. What this is

The investigation into a 1.9× direct-CLI wall-clock penalty found something larger on the way:
**roughly 78% of candidate-worker CPU is spent resolving the caller of each log record**, on *both*
entry points, in the hottest loop in the system. The CLI-vs-service gap turns out to be a
*consequence* of that cost rather than a separate defect — the CLI's module table is 1.33× larger,
and the resolution is O(len(`sys.modules`)).

So the headline is not "make the CLI as fast as the service". It is:

> **Stop the trainer spending four fifths of its compute deciding where a log line came from.**
> The CLI-vs-service gap closes as a side effect.

This document designs that fix, plus the two smaller defects the same investigation exposed. It is
deliberately **not** a logging redesign — that is a separate, larger question (§8).

## 2. The defect, precisely

`log_config/logger/logger.py:230-235`:

```python
@classmethod
def _frame_info(cls, frame=None):
    return lambda name: getattr(getouterframes(frame)[1], name)
```

Three compounding problems in one line:

1. **`getouterframes(frame)` walks the ENTIRE stack** and builds a `FrameInfo` for every frame —
   then `[1]` discards all but one. `FrameInfo` construction calls `getframeinfo` →
   `findsource` → `getsourcefile` → **`inspect.getmodule`**.
2. **`getmodule` is O(len(sys.modules)) on a cache miss** — `inspect.py:1023` runs
   `for modname, module in sys.modules.copy().items()`, copying the whole module dict *per call*.
   When the scan resolves nothing for that filename, `modulesbyfile` is never populated for it, so
   the next call rescans, forever.
3. **The returned closure re-walks the stack on every field access.** `_console_dict` reads two
   fields (`:246-247`) and `_file_dict` three (`:264-266`) — so each log record pays the full walk
   **2–3 times**.

Cost, measured at a realistic stack depth (12) and module count (1,333):

| implementation | per resolution |
| --- | ---: |
| current — `getouterframes(frame)[1]` | **20,711 µs** |
| proposed — `frame.f_back` attributes | **1.0 µs** |
| **speedup** | **≈ 20,700×** |

It scales with stack depth **and** `sys.modules` size, which is exactly why it is worse on the CLI.

### 2.1 Corroboration from three independent instruments

| instrument | finding |
| --- | --- |
| cProfile (deterministic, per-worker) | `inspect` ≈ ⅔ of worker CPU; **1.46 × 10⁹** `hasattr` calls across 32 candidate trainings |
| py-spy `--native` (sampling) | `inspect` frames ≈ **78%** of worker self time; `getmodule` alone ≈ 33% |
| microbenchmark (above) | 20,711× per-call difference |

## 3. Fix inventory and sequencing

| # | fix | what it buys | risk |
| --- | --- | --- | --- |
| **F1** | Logger frame resolution | ~78% of worker CPU, **both** paths; closes most of the CLI gap | low |
| **F2** | CLI import hygiene | the remaining 1.33× module-table ratio | low–medium |
| **F3** | Forkserver preload set | ~12.8 s per pool creation; worker memory | medium (fork safety) |
| F4 | Candidate seed derivation | cross-arm comparability | **done, verified** |

**Sequence F1 → F2 → F3.** F1 is the largest, benefits every consumer, and is the most surgical.
F2 and F1 overlap on the *gap* but not on absolute performance: F1 makes each resolution cheap, F2
makes the thing being scanned smaller. F1 alone reduces F2's value; F2 alone leaves the 78% intact.

## 4. F1 — logger frame resolution

### 4.1 The change

`getouterframes(frame)[0]` is `frame` itself and `[1]` is `frame.f_back`, so the target is exactly
`frame.f_back`. Every field the logger reads has an O(1) raw equivalent:

| `FrameInfo` field (configured name) | raw frame attribute |
| --- | --- |
| `filename` | `frame.f_code.co_filename` |
| `lineno` | `frame.f_lineno` |
| `function` | `frame.f_code.co_name` |

```python
@classmethod
def _frame_info(cls, frame=None):
    """Resolve the caller's file/line/function without walking or importing anything.

    `getouterframes(frame)[1]` is just `frame.f_back`, but it built a FrameInfo for EVERY frame
    on the stack to get there -- and each of those calls inspect.getmodule, which copies and
    scans sys.modules. Measured at 20.7 ms per resolution against 1.0 us for the direct read,
    and it was paid 2-3 times per log record.
    """
    target = frame.f_back if frame is not None else None
    if target is None:
        # Previously an IndexError from getouterframes(...)[1] on a depth-1 stack. A log call
        # must never raise, so degrade to placeholders instead.
        return lambda name: cls._frame_unknown
    code = target.f_code
    fields = {
        cls._frame_file: code.co_filename,
        cls._frame_line: target.f_lineno,
        cls._frame_func: code.co_name,
    }
    return lambda name: fields.get(name, cls._frame_unknown)
```

Resolved **once** per record rather than per field, which removes the 2–3× multiplier as well.

### 4.2 Why this is behaviour-preserving

`FrameInfo.filename` comes from `getsourcefile(frame) or getfile(frame)`; `getfile(frame)` *is*
`frame.f_code.co_filename`, and `getsourcefile` returns that same string for any real `.py` file.
The logger then takes `os.path.basename(...)` of it, so the rendered value is identical for every
frame originating in a source file. `lineno` and `function` map to `f_lineno` / `co_name` exactly.

The one behavioural change is deliberate and an improvement: a depth-1 stack currently raises
`IndexError` inside a logging call; it now renders a placeholder.

### 4.3 Verification

- **Unit**: assert `_frame_info` returns the same `(filename, lineno, function)` as the current
  implementation for a synthetic nested call — the equivalence claim, pinned.
- **Unit**: a depth-1 frame renders placeholders rather than raising.
- **Regression guard**: a test that fails if `getouterframes` (or `inspect.stack`) reappears in
  `logger.py`. This is the guard that stops the pathology returning silently — it is a one-line
  source scan and it is the cheapest durable protection available.
- **End-to-end**: the paired campaign (§6).

## 5. F2 — CLI import hygiene

`import main` pulls **1,867** modules including **`fastapi`** and **`pydantic`**; `import api.app`
pulls **1,416**. The direct CLI never serves HTTP and never validates a request model.

Because resolution cost is O(len(`sys.modules`)), that surplus is paid on every log record in every
candidate worker — it is the entire measured 1.327× worker-table ratio, and therefore the entire
residual gap once F1 is in.

**Design**: find the import edge that pulls the web/validation stack into `main.py` (a shared
settings or constants module is the likely culprit) and break it — defer to a function-local import,
or split the shared module so the CLI path does not transit the API layer.

**Not yet traced.** The edge itself has not been identified; that is the first task of F2 and it is
cheap (`python -X importtime`, or `sys.modules` diffing against a bisected import).

**Verification**: assert `len(sys.modules)` after `import main` is below a threshold, and that
`fastapi` / `uvicorn` are absent — a guard that also documents the intent.

## 6. F3 — forkserver preload set

Currently `["os", "uuid", "torch", "numpy", "random", "logging", "datetime"]`.

| entry | + modules | import | verdict |
| --- | ---: | ---: | --- |
| `torch` | 886 | 2.938 s | keep — the reason the mechanism exists |
| `numpy` | 109 | 0.153 s | keep |
| `logging` | 10 | 0.013 s | harmless |
| `random`, `uuid`, `datetime` | 9 | 0.008 s | harmless |
| `os` | **0** | 0.000 s | already imported — pure noise |
| **missing: `cascade_correlation`** | **242** | **1.822 s** | **paid per worker, after the fork** |

Every worker must import `cascade_correlation` to unpickle its target. Not preloading it costs
**~12.8 s of duplicated CPU per pool creation** (7 workers × 1.82 s) plus 242 × 7 modules of memory
that copy-on-write would otherwise share from one forkserver copy.

**Precondition, not a recommendation.** Preloading runs a module's import-time side effects *in the
forkserver*, and every worker inherits them across a fork. Logger handles, file descriptors, or any
resource opened at import become shared rather than per-worker — the classic fork-safety hazard,
and the reason a preload list is not simply "add everything". **That audit is not done**, and F3
must not land before it is.

Also in scope for F3, because it actively misleads: the commented-out
`self._mp_ctx = mp.get_context("forkserver")` at `cascade_correlation.py:1061-1062` above a garbled
note reading *"…did not corrUse 'fork' context for better compatibility with BaseManager on Linux"*.
The code uses forkserver; the comment says otherwise.

### 6.1 An open question F3 should answer

Workers were measured at **1,871** (CLI) and **1,410** (service) modules — within a handful of their
respective launchers, and far above a clean forkserver table (1,091 preload, 1,333 with the
trainer). **The forkserver is not currently delivering the isolation its use implies**, and the
route by which the launcher's import graph reaches the workers has not been traced. If that route
is closed, F2 may become unnecessary — the workers would stop inheriting the entry point's imports
at all.

## 7. Verification plan (end-to-end)

The instruments already exist and are the ones that produced the baseline, so before/after is
like-for-like:

| step | tool | expected after F1 |
| --- | --- | --- |
| paired campaign, cap 16, k=4 | `2026-08-21_h2h_paired_campaign.bash` | candidate-phase ratio **1.706 → ~1.0**; absolute wall on **both** arms down sharply |
| per-epoch ratio | `2026-08-21_h2h_paired_ratio.py` | rate ratio **1.415 → ~1.0** |
| worker profile | `2026-08-23_pyspy_conda_shim.bash` + `_native_profile_diff.py` | `inspect` frames fall from ~78% of self time to negligible |
| determinism unchanged | `2026-08-20_determinism_nrun.py` | service still **0/190**; CLI rate **not made worse** |

That last row is the one most easily forgotten: F1 changes what is computed per log record, not the
arithmetic, so the divergence rate must be **unchanged**. If it moves, something else happened.

All arms at a single recorded cascor SHA; the campaign driver refuses otherwise.

## 8. Explicitly out of scope — the logging redesign

The owner has separately raised a broader logging question: a clean stream to stdout/stderr, richer
sinks (formatted and colourised file output), **per-logger** levels settable via config file and
environment variable, and possibly streaming into an ELK/Kibana-style backend.

That is a genuine and larger piece of work, and it is **not** this design. The distinction matters:
F1 is a bug fix to a hot path that any redesign would have to make anyway, and it should not wait
behind an architecture discussion. Conversely the redesign should not be justified by F1's
performance number, because F1 already captures it.

Recorded here so the two are not conflated; the redesign warrants its own analysis document.

## 8a. F1 — IMPLEMENTED AND VERIFIED (cascor `a520c07`, branch `fix/logger-frame-resolution`)

### Correctness

- **Equivalence pinned** against the previous implementation at stack depths 0 / 1 / 5 / 12, both
  resolvers applied to the *same* frame.
- **Console and file output compared byte-for-byte** before and after — `+[<string>: 3] (…) [INFO] …`
  and `+[<string>: <module>:3] (…) [INFO] …` render identically.
- **86 tests pass** (`test_logger_coverage.py` 80 + `test_logger_frame_resolution.py` 6).
- **The regression guard was verified to FAIL** by temporarily re-introducing `getouterframes`. An
  untested guard is a vacuous check, and this arc has already shipped one of those.

### Effect, cap 4, one run per arm

| | service before | service after | CLI before | CLI after |
| --- | ---: | ---: | ---: | ---: |
| candidate phase | 187.8 s | **16.0 s** | 276.1 s | **15.0 s** |
| candidate epochs | 11,360 | 11,360 | 10,734 | 11,900 |
| s / candidate epoch | 0.01652 | **0.00141** | 0.02571 | **0.00126** |
| **speedup (per epoch)** | | **11.7×** | | **20.4×** |

The CLI run did **more** candidate work than its baseline (11,900 vs 10,734) and still finished in
15 s against 276 s, so this is not a truncated run.

### The gap closed, and closed for the predicted reason

**CLI / service per-epoch rate ratio: 1.555 → 0.894.**

The prediction in §1 was that the gap is a *consequence* of the logging cost, so removing the cost
should remove the gap without any CLI-specific change. It did. And the asymmetry in the benefit is
the mechanism's own signature: the CLI gained **20.4×** where the service gained **11.7×**, because
`getmodule` was scanning the CLI's 1,871-module table against the service's 1,410. The arm with
more to lose lost more.

> n=1 per arm. The **magnitude** (11–20×) is far outside any plausible noise, but the **ratio**
> (0.894 vs 1.0) is a single pair and should not be quoted as "the CLI is now faster" — the honest
> reading is that the gap is gone. A k=4 paired cap-16 campaign is the publishable number, and it
> is now affordable in minutes rather than hours because the runs got ~15× shorter.

### What this does to F2 and F3

- **F2 (CLI import hygiene)** is no longer a performance fix. Its 1.33× module-table ratio only
  mattered because every log record scanned that table; nothing does now. It remains worth doing
  for import time, memory, and hygiene — the direct CLI should not be dragging FastAPI and pydantic
  into a training loop — but it drops out of the critical path.
- **F3 (forkserver preload)** is unaffected: the ~12.8 s per pool creation is import cost, not
  logging cost.

## 9. Risks

| risk | mitigation |
| --- | --- |
| Rendered log fields change subtly (e.g. absolute vs source path) | equivalence unit test against the current implementation before removal |
| F3 shares a fork-unsafe resource via preload | audit precondition; F3 blocked until done |
| F2 breaks an import someone relies on | guard test asserts absence of `fastapi`/`uvicorn`, not presence of a module list |
| The pathology returns silently in a later refactor | source-scan regression guard (§4.3) |
