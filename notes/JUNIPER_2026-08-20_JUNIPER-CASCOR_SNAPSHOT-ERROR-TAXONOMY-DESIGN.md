# Snapshot Error Taxonomy — separating *corrupt* from *absent* (D-B)

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-20

**Status**: DESIGN — **not implemented**. Nothing in juniper-cascor was modified in producing this
document. The owner asked (2026-08-19) that D-B be *discussed before implementing*; this is that
discussion, written down so the decision has facts rather than recollection.

**Line numbers are against juniper-cascor `4bec1be`** (`origin/main`, 2026-08-20 — the tip after
juniper-cascor#539 merged). #539 shifted `api/lifecycle/manager.py` by ~66 lines, so every citation
below was re-derived after that merge. Re-derive again before editing.

---

## 1. The defect, in one sentence

A **corrupt** snapshot and an **absent** snapshot are reported identically — `404 Not Found`,
`"Snapshot '<id>' not found or failed to load"` — so the operator cannot tell *"pick a different
snapshot"* from *"you have lost data, go investigate."*

The four affected verbs and their raise sites (`src/api/routes/snapshots.py`):

| Verb | Route raise site | Lifecycle entry point |
|---|---|---|
| restore | `:252` | `load_snapshot` (`manager.py:4614`) |
| retrain | `:303` | `restore_for_retrain` (`manager.py:4655`) |
| resume  | `:350` | `resume_from_snapshot` (`manager.py:4728`) |
| replay  | `:407` | `start_replay` (`manager.py:4798`) |

All four raise the identical `HTTPException(status_code=404, ...)`. The reason string also appears
three times in the manager — `:4641` (restore), `:4685` (retrain), `:4761` (resume). `start_replay`
has none, for a reason that matters to the design (§6).

---

## 2. A correction that has to lead

> **Earlier documents state that `load_network` has no production callers, and that a fix applied
> only to `load_network` would change nothing. Both claims are false, and inverted.**

The claim appears in juniper-ml#1144, juniper-ml#1164, the snapshot-lifecycle design of record
(§4.2), and the perf-lane prioritisation note. It originated in a `grep` truncated by `head -12`.

Re-derived here, untruncated, against `4bec1be`:

```
$ grep -rn "\bload_network\b" juniper-cascor/src --include=*.py | grep -v "/tests/"
src/cascade_correlation/cascade_correlation.py:5130:  network = serializer.load_network(filepath=..., restore_multiprocessing=...)
src/api/lifecycle/manager.py:4580:                     network = serializer.load_network(matches[0])
src/snapshots/snapshot_serializer.py:877:             def load_network(self, ...)
```

`load_network` is **the live loader** on both tiers. `_load_snapshot_to_network`
(`manager.py:4561`) calls it at `:4580`, and that is the sole path behind all four verbs.

This inverts the design consequence: `load_network` is not an irrelevant backwater to be skipped,
it is **the only place in the system that still knows why the load failed**. Any fix must start
there.

---

## 3. Where the information is destroyed

The cause is knowable at the bottom of the stack and is discarded three times on the way up.

### Collapse 1 — `load_network` returns `None` for five distinct causes

`snapshots/snapshot_serializer.py:877`:

| Line | Cause | True classification |
|---|---|---|
| `:892` | `os.path.exists` is false | **ABSENT** |
| `:895` | `_validate_format` rejected the file | **CORRUPT** (bad/incompatible format, or a failed structural check) |
| `:898` | `_create_network_from_file` returned falsy | **CORRUPT** (config group unusable) |
| `:918` | `except Exception` — truncated file, h5py read error, … | **CORRUPT** (or an I/O fault) |
| `:913` | `_validate_shapes` failed | **neither** — this only *warns* and still returns the network |

That last row is worth noticing on its own: a snapshot whose tensors disagree in shape loads
"successfully" and is installed on the live lifecycle.

### Collapse 2 — `_load_snapshot_to_network` flattens everything to `bool`

`manager.py:4561`:

```python
matches = [f for f in snapshots_dir.glob("*.h5") if f.stem == snapshot_id]
if not matches:
    return False          # :4575  -- ABSENT, detected here, never reaching load_network
network = serializer.load_network(matches[0])
if network is None:
    return False          # :4583  -- CORRUPT (or anything else load_network hit)
...
return True               # :4599
```

Two structurally different outcomes, one `False`. Note that ABSENT is detected **twice** —
here at `:4573`, and again inside `load_network` at `:892` — which is why the fix cannot live
in `load_network` alone.

### Collapse 3 — the routes read only `loaded`

`_snapshot_result` (`manager.py:4601`) already carries a `reason` field, and its own docstring
records that the routes ignore it:

> *"Internal contract: the snapshot routes build their own HTTP payload via
> `_build_unified_payload` and consume only `loaded` for error-mapping."*

**This is the most useful fact in the document.** The transport for a distinguishing reason
already exists and is already populated — `resume_from_snapshot` passes
`reason=f"rejected: lifecycle is {...}"` on the FSM path — it is simply discarded at the route
boundary. Three of the four verbs need no new plumbing at all, only a classification at the
bottom and a mapping at the top.

---

## 4. A related, smaller wart

`verify_saved_network` (`snapshot_serializer.py:255`) returns
`{"valid": False, "error": "Invalid format"}` at `:268` from the `_validate_format` gate —
**before any payload inspection**. `_validate_format` (`:1626`) checks far more than the format
string: required groups, hidden-unit consistency, parameter dataset shapes. So a snapshot that
fails any of those is reported to the operator as "Invalid format", which points at the wrong
thing. This is the same class of defect as D-B and would be natural to fix in the same change,
but it is a separate surface (the verify/CLI path, not the four verbs).

---

## 5. Design options for the wire contract

The classification is the real work; the status code is a judgement call. Four candidates:

| Option | For | Against |
|---|---|---|
| **A. 422 for corrupt, 404 stays absent** | Well-formed request, unprocessable entity — exactly the semantics. No collision with existing codes on these routes. | A new code for clients to learn. |
| **B. 500 for corrupt** | It genuinely is a server-side data-integrity failure. | 5xx implies "retry might help"; a corrupt file is deterministic. Also pollutes error-rate alerting with a user-triggerable condition. |
| **C. 409 for corrupt** | Already used on these four routes. | Those routes **already** use 409 for FSM conflicts (`:246`, `:297`, `:346`, `:402`). Re-using it would fuse a *different* pair — trading one ambiguity for another. |
| **D. Keep 404, distinguish in the body only** | Zero breaking change. | A 404 for a file that exists is a lie; and any client that branches on status alone still cannot tell. |

**Recommendation: Option A**, with a machine-readable discriminator in the body rather than only
in prose — e.g. `reason: "snapshot_corrupt"` vs `"snapshot_absent"` — so clients can branch
without string-matching a human sentence.

---

## 6. The replay asymmetry — the one real structural obstacle

Three verbs return `Dict[str, Any]` through `_snapshot_result`. **`start_replay` returns a bare
`bool`** (`manager.py:4798`, `-> bool`, returning `False` at `:4821` and `:4825`), and its route
consumes it as `if not success:` (`routes/snapshots.py:407`).

So `start_replay` has no channel for a reason at all. Any implementation must either:

1. **Converge `start_replay` onto `_snapshot_result`** — consistent with the WS-6 B2b return
   convergence the `_snapshot_result` docstring names as its direction of travel, but it is a
   signature change with its own callers and tests; or
2. **Leave replay fused** and fix the other three — cheaper, but leaves the taxonomy
   inconsistent across four sibling verbs, which is its own trap for the next reader.

This choice, not the status code, is what decides the size of the change. **It is the main thing
worth an owner decision.**

---

## 7. Blast radius

Small, and better than expected.

- **No in-repo client special-cases these 404s.** `juniper-cascor-client` does not wrap the four
  verbs at all. `juniper-canopy`'s `POST /api/v1/snapshots/{id}/restore` (`main.py:2293`) is a
  *local demo implementation* over `_demo_snapshots`, not a proxy to cascor.
- **Canopy does flatten a cascor 404 elsewhere** — `main.py:4042` deliberately maps any backend
  failure on the `dataset_swaps` proxy, "including cascor 404 for a missing snapshot", to a 502 so
  the timeline degrades gracefully. That is a *different* endpoint, not one of the four verbs, but
  it shows the taxonomy is flattened more than once in the stack and that canopy's error handling
  should get its own pass before anyone claims the distinction reaches the UI.
- **cascor's own tests pin the current contract** and would need updating —
  `tests/unit/api/test_snapshot_route_coverage.py` asserts `404` at `:99`, `:106`, `:191`, `:258`,
  `:265`, `:339`, `:471`, `:796`, and asserts the literal string `"not found or failed to load"` at
  `:259`, `:266`, `:340`, `:472`.

---

## 8. Test plan

A fix here is only credible if the tests distinguish the two causes, which today's do not:

1. **Absent** — request a snapshot id with no file. Expect `404` and `reason: snapshot_absent`.
2. **Corrupt / bad format** — write an `.h5` whose `format` attr is wrong, so `_validate_format`
   rejects it at `:1647`. Expect the corrupt status and `reason: snapshot_corrupt`. This is the
   arm that fails against today's code.
3. **Corrupt / truncated** — a file that raises inside the `try`, exercising `:918` rather than
   `:895`, proving the classification is not keyed to one specific failure.
4. **Negative control** — a valid snapshot still loads and returns 200 on all four verbs. Without
   this, a change that classifies *everything* as corrupt would pass 1–3.
5. **Per-verb coverage** — all four verbs, because the fusion is duplicated four times and a fix
   applied to three is the likeliest way this ships half-done.

The corpus for arm 2/3 already exists: the census found **6 EMPTY files** and one Oct-2025 husk
that fails verification (`202510` bucket, writer version `None`) among 27,885 — real corrupt
specimens rather than synthetic ones. Fixtures should still be synthetic for hermeticity, but the
husk is available to validate that the classification matches reality.

---

## 9. Non-goals

- **Not** a repair or recovery path for corrupt snapshots. This change makes the failure *legible*;
  it does not attempt to salvage anything.
- **Not** a retention or deletion policy. That remains gated on the §6.2 index (S-2).
- **Not** a change to `_validate_shapes`' warn-and-continue behaviour (§3, collapse 1, last row).
  That is a real defect in its own right — a shape-broken network is installed on the live
  lifecycle — but it is a *different* failure mode from D-B and deserves its own decision rather
  than being smuggled in here.

---

## 10. Open questions for the owner

1. **§6 — converge `start_replay` onto `_snapshot_result`, or leave replay fused?** This decides
   whether the change is small-and-inconsistent or larger-and-uniform. *(Recommend: converge —
   four sibling verbs disagreeing on their error contract is exactly the kind of thing that gets
   half-fixed twice.)*
2. **§5 — is `422` acceptable for corrupt?** *(Recommend: yes, with a machine-readable `reason`.)*
3. **§4 — fold in the `verify_saved_network` "Invalid format" wart, or keep it separate?**
   *(Recommend: same PR — same class, adjacent code, and it is two lines.)*
4. **§9 — should `_validate_shapes`' warn-and-continue become its own tracked defect?**
   *(Recommend: yes, as a separate item; silently installing a shape-broken network on the live
   lifecycle is arguably worse than the fused 404.)*

---

## 11. Provenance

- Supersedes the `load_network` claim in the snapshot-lifecycle design of record §4.2 and in the
  perf-lane prioritisation note. Both still carry the false version (§2); correcting them is a
  separate documentation change, not folded in here.
- Companion to [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md)
  (§9's open-questions table, where D-B is recorded).
- The R3 resume follow-on that preceded this item shipped as juniper-cascor#539 (`4bec1be`).
