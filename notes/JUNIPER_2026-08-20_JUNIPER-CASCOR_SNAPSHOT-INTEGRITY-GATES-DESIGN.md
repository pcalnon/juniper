# Snapshot Integrity Gates — six checks, zero enforcement (D-E)

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-20

**Status**: DESIGN — **not implemented**. Nothing in juniper-cascor was modified. Every number
below is measured, by `util/ad-hoc/2026-08-20_shape_broken_network_probe.py` (read-only; it writes
only into a temp dir it creates and never touches the archive).

**Line numbers are against juniper-cascor `4bec1be`.** Tracked as **D-E**, the fourth defect in the
snapshot family after D-A (fixed), D-B (designed), D-C (open).

---

## 1. The defect

`load_network` runs **six** integrity checks. It honours **none** of them: each one logs and
execution continues, and the loaded network is then installed on the live lifecycle by
`_load_snapshot_to_network` (`manager.py:4590`) and reported to the operator as a successful
restore.

| # | Gate | Site | On failure |
|---|---|---|---|
| 1 | `input_size` vs saved arch | `snapshot_serializer.py:930` | `WARNING`, continue |
| 2 | `output_size` vs saved arch | `:934` | `WARNING`, continue |
| 3 | `output_weights` checksum | `:1024` | **`ERROR`**, continue |
| 4 | `output_bias` checksum | `:1030` | **`ERROR`**, continue |
| 5 | `_validate_shapes` | `:913`–`:914` | `WARNING`, continue |
| 6 | — | `:915` | logs **`Successfully loaded network`** |

Gates 3 and 4 are the sharpest: a **checksum mismatch is positive evidence of data corruption**,
it is logged at `ERROR`, and the loader proceeds anyway. Gate 6 then contradicts gates 1–5 in the
same log stream.

`_validate_shapes` (`:1592`) is not a redundant sanity check either. It validates exactly the
invariants the training loop assumes: `output_weights` against the `nn.Linear` that
`train_output_layer` builds, and hidden-unit weight length against the elementwise broadcast in
`_compute_hidden_outputs` (`cascade_correlation.py:1968`).

---

## 2. What a shape-broken network actually does — measured

The question that decides whether this is a UX defect or a correctness defect: does a bad shape
*raise*, or does it *broadcast*? **Both, depending on the violation** — and the silent branch is
reachable.

| Case | `load_network` | `_validate_shapes` | `forward(x)` | `train_output_layer` |
|---|---|---|---|---|
| A — `output_weights` loses a row | returns a network | detects (False) | `RuntimeError` | `RuntimeError` |
| B — `output_bias` wrong length | returns a network | detects (False) | `RuntimeError` | `RuntimeError` |
| C — hidden weights too short | returns a network | detects (False) | `RuntimeError` | `RuntimeError` |
| **D — hidden weights length 1** | returns a network | detects (False) | **returns a finite (8, 2) tensor** | **returns loss 1.032** |

Case D is the one that matters. A length-1 weight vector is *broadcast-compatible* with the
`(batch, col)` slice it multiplies, so the arithmetic succeeds and the network computes a
different answer — **max abs delta 0.2474 against the intact network** — with no error anywhere.
It then trains, reports a plausible loss, emits metrics, and can be re-snapshotted, propagating
the corruption into new files.

**So D-E is strictly worse than D-B.** D-B misreports *why* a load failed; D-E lets a load that
the system knows is broken succeed and produce wrong numbers silently.

---

## 3. A fifth class, found in the real archive

The four synthetic cases above were constructed. Sampling the actual archive turned up a class
none of them modelled.

`cascor_snapshot_20260330_222615_88cc3a7e-….h5`:

```
input_size=2  output_size=2  hidden=1
output_weights (3, 3)   expected (3, 2)
output_bias    (3,)     expected (2,)
hidden[0] weights (2,)  expected (2,)      <- fine
_validate_shapes: False
forward(x): returned tensor shape=(4, 3) (finite)
```

The params are **mutually consistent at width 3**; what they disagree with is the network's
declared `output_size=2`. So the forward pass works perfectly and silently returns a **3-column**
output for a network that advertises 2.

**Root cause:** `_create_network_from_file` builds the network from the `config` group, then
`_load_parameters` installs tensors from the `params` group, and `_load_architecture` (`:919`)
only *warns* when the two disagree (`:930`, `:934`) — it never reconciles or rejects. Config and
params are allowed to describe different networks.

Anything downstream that trusts `output_size` — the `active_output_dim` slicing in
`train_output_layer`, canopy's rendering, a conformance check — is reading a contract the tensors
do not honour.

---

## 4. Blast radius of rejecting at load

Measured over a seed-fixed random sample of the live archive (n=1500 of 27,888, seed 20260820),
loading each through the production loader and re-running `_validate_shapes`:

| Result | Count | Rate | Extrapolated |
|---|---|---|---|
| shape valid | 1484 | 98.9% | — |
| **shape INVALID** | **9** | **0.60%** of those that load | **~170 files** |
| **load returned `None`** | **7** | **0.47%** of those sampled | **~130 files** |
| load raised | 0 | — | — |

**0.60% of snapshots that load today would be newly refused** by a strict reject-at-load change —
on the order of ~170 files. Small, but not zero, and the affected files are currently *loadable*,
so a hard rejection is a real behaviour change for research use. (An earlier n=250 pass estimated
0.40% off a single hit; n=1500 is the figure to quote.)

**The `load_returned_none` row is a finding in its own right, and it belongs to D-B.** Roughly 130
archive files fail the full load outright. Neither existing measurement covers this:

- the 2026-08-16 census classified files structurally ("has model groups"), without calling
  `load_network`;
- `verify_saved_network` gates on `_validate_format`, **not** `_validate_shapes` and not the full
  load path — so "88/89 valid" was never a statement about either shape integrity or loadability.

Every one of those ~130 files produces today's fused `404 "not found or failed to load"` — so D-B
is not a hypothetical operator inconvenience; it already misreports a real, measurable population
of the archive.

---

## 5. Options

| Option | For | Against |
|---|---|---|
| **A. Reject at load, no escape hatch** | Fail-closed; impossible to train on a known-broken network. | Makes ~110 currently-loadable archive files unloadable, including for forensics — exactly what the "never an aggressive sweep" instruction is about. |
| **B. Reject by default + explicit opt-in override** | Fail-closed on the service path; a researcher can still load a known-broken snapshot deliberately, for inspection. | One more parameter on the load API. |
| **C. Promote the logs to `ERROR` only** | Zero behaviour change. | The system *already* logs `ERROR` for checksum failures and proceeds. More logging does not stop case D from training on garbage. |
| **D. Attempt repair** | Could rescue the §3 class by adopting the params' width. | Guessing which of two disagreeing sources is authoritative. Out of scope until provenance (D-C) exists. |

**Recommendation: B.** Reject by default; add an explicit opt-in (e.g.
`load_network(..., allow_invalid=False)`) for forensic loads, and classify the rejection as
**CORRUPT** in D-B's taxonomy so the operator gets `422` and a real reason rather than a `404`.
D-B and D-E share the same error channel, which is why D-B should land first.

Gates 1–4 need the same decision, not just gate 5. A checksum mismatch in particular should be
fail-closed — it is unambiguous evidence of corruption.

---

## 6. Test plan

1. **Each violation class rejects** — A, B, C, D from §2, plus the §3 config/params disagreement.
   The synthetic corruptions are cheap: save a valid network, replace one HDF5 dataset, load.
2. **Case D specifically** — the broadcast case is the only one that fails silently today, so it
   is the arm that proves the fix does anything. Assert rejection, *not* just that it raises later.
3. **Checksum mismatch rejects** — flip a byte in a tensor, leave the checksum, assert refusal.
4. **The opt-in override still loads** — a forensic load of a known-broken snapshot succeeds and
   is clearly labelled.
5. **Negative control** — a valid snapshot still loads on all four verbs. Without it, a change
   that rejected everything would pass 1–4.
6. **The real offender** — `cascor_snapshot_20260330_222615_88cc3a7e-….h5` is a genuine specimen.
   Fixtures should stay synthetic for hermeticity, but this file is available to confirm the
   classification matches reality.

---

## 7. Non-goals

- **Not** a repair path (option D). Deciding which of config/params is authoritative needs
  provenance (D-C).
- **Not** a retention or deletion decision. The ~110 shape-invalid files are *evidence* here, not
  sweep candidates; nothing in this design deletes anything.
- **Not** a change to `_validate_shapes`' checks themselves — they are correct and already detect
  every case above. The defect is purely that nothing acts on the answer.

---

## 8. Open questions

1. **Gates 1–4 as well as 5?** Recommend yes, with checksum failures fail-closed — a mismatch is
   unambiguous corruption. This widens the change beyond shapes.
2. **What should the opt-in be called, and where does it surface?** A serializer parameter is
   easy; whether it should also be reachable from the API (a forensic `?allow_invalid=true`) or
   stay CLI/library-only is an operator-surface decision.
3. **Should the §3 config/params disagreement be its own classification?** It is distinguishable
   from "tensors are the wrong shape" and might deserve a distinct reason string.
4. **Sequencing against D-B.** D-B should land first so D-E has a `422` + reason channel to report
   through — otherwise a rejected load regresses to the fused `404` this arc is trying to remove.

---

## 9. Provenance

- Evidence: `util/ad-hoc/2026-08-20_shape_broken_network_probe.py` (default mode = the four
  synthetic classes; `--archive-sample N` = blast radius; `--inspect PATH` = classify one file).
- Companion to [`JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md`](JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-ERROR-TAXONOMY-DESIGN.md)
  (D-B, juniper-ml#1193), whose §9 flagged this as deserving its own decision.
- Parent: [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md).
