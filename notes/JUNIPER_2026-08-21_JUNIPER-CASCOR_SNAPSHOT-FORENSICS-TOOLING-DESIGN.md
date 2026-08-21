# Snapshot Forensics Tooling — the missing half of the D-E escape hatch

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-cascor / juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-21

**Status**: DESIGN — **not implemented**. This document records a *need* and its requirements; it
changes no code. Line numbers are against juniper-cascor `ddd32300` (`origin/main`, 2026-08-21).

---

## 1. Why this exists

The D-E decision (2026-08-21) is that all six of `load_network`'s integrity gates become
fail-closed, with the forensic escape hatch as a **serializer parameter only** — library and CLI,
deliberately not reachable from the API, because an operator investigating data loss is at a shell
rather than driving HTTP.

That decision is only sound if there *is* tooling at that shell. Today there is not. The hatch
would ship as a Python keyword argument with no ergonomic way to reach it, which is a hatch in name
only.

This is the companion requirement to
[`JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-INTEGRITY-GATES-DESIGN.md`](JUNIPER_2026-08-20_JUNIPER-CASCOR_SNAPSHOT-INTEGRITY-GATES-DESIGN.md)
(D-E, juniper-ml#1199) — not a nice-to-have discovered alongside it.

---

## 2. The population that needs it

Measured over a seed-fixed sample of the live archive (n=1500 of **27,896**, seed 20260820), each
file loaded through the production loader:

| Result | Rate | Extrapolated |
|---|---|---|
| shape INVALID | 0.60% of those that load | **~170 files** |
| `load_network` returned `None` | 0.47% of those sampled | **~130 files** |

**Roughly 300 files that nothing in the system can currently characterise.** Once D-E enforces,
they become exactly the set an operator can only open deliberately — and there is no supported way
to do so.

Neither existing measurement covers them:

- the 2026-08-16 census classified files *structurally* ("has model groups") without ever calling
  `load_network`;
- `verify_saved_network` gates on the format check alone (§3).

So the familiar **"88/89 valid" figure says nothing about either group** and must not be cited for
loadability or shape integrity.

---

## 3. What is blind today — the concrete gap

`verify_saved_network` (`snapshots/snapshot_serializer.py:259`) returns on the format gate at
`:275` and **never calls `_validate_shapes`**. Every verification surface in cascor routes through
it:

| Surface | Call site | Sees format? | Sees shapes / arch? |
|---|---|---|---|
| `snapshot_cli.py verify` | `snapshot_cli.py:153` | yes | **no** |
| `snapshot_cli.py list` | `snapshot_cli.py:70` | yes | **no** |
| `snapshot_utils` sweep | `snapshot_utils.py:101` | yes | **no** |
| `snapshot_utils` compare | `snapshot_utils.py:126`, `:127` | yes | **no** |
| `snapshot_utils` info | `snapshot_utils.py:264` | yes | **no** |

Meanwhile `_validate_shapes` runs on the *load* path (`:967`) and only warns (`:973`) before the
loader logs "Successfully loaded network".

**The result: cascor has six verification call sites and not one of them can see the two failure
classes D-E is about.** An operator asking "is this snapshot healthy?" today gets an answer that
is silent on the exact defects that matter.

---

## 4. What the tooling must do

Each requirement below traces to something this arc actually hit, not to a hypothetical.

1. **Classify a single file** into the taxonomy the code now speaks — `SNAPSHOT_ABSENT` /
   `SNAPSHOT_CORRUPT` (`snapshots/snapshot_load_status.py:24`, `:31`) plus the D-E additions
   (shape-invalid, and the arch-mismatch reason chosen in D-E Q3). Reporting the *same* codes the
   API returns is the point: an operator handed a `422 SNAPSHOT_CORRUPT` should be able to ask the
   tool the same question and get the same word back.

2. **Diff `config` against `params`.** The real archive case
   (`cascor_snapshot_20260330_222615_88cc3a7e-….h5`) has `output_weights (3, 3)` and
   `output_bias (3,)` that are mutually consistent *at width 3* while the network declares
   `output_size=2`. Diagnosing that requires seeing both sides at once — a single-sided dump makes
   it look fine.

3. **Dump structure without constructing a network.** Groups, attrs, tensor shapes, writer
   version, and the internal `created` attribute — for files that cannot be loaded at all, which
   is the ~130.

4. **Sweep and bucket across the archive**, reporting populations rather than one file at a time.
   This is what would finally characterise the ~300, and it is the input the retention question
   (S-2) is still waiting on.

5. **Read-only, with no delete path.** Non-negotiable under the standing instruction that
   snapshots get a designed solution and **never** an ad-hoc or aggressive sweep. See §6 for why
   this is more than a formality here.

---

## 5. Where it should live

`juniper-ml/util/ad-hoc/2026-08-20_shape_broken_network_probe.py` is the seed. It already carries
`--inspect PATH`, `--archive-sample N`, and the four synthetic corruption classes, and it produced
every number in §2.

It is the wrong long-term home on two counts: it is explicitly marked ad-hoc with a *"Retire when:
the warn-and-continue behaviour is decided and fixed"* clause (that condition is now being met),
and it lives in **juniper-ml** while the artifacts it inspects belong to **juniper-cascor**.

Two candidate destinations:

- **A new `snapshot_cli.py` subcommand** (e.g. `diagnose`). The module already exists with
  `save` / `load` / `list` / `verify` / `compare` / `cleanup`, so this is the surface an operator
  would already reach for, and it sits next to the `verify` command whose blindness (§3) is the
  gap. Preferred.
- **A permanent `util/` script in cascor**, if the CLI's argument surface is judged already
  crowded.

Either way the promotion should carry the probe's synthetic-corruption cases across as tests: they
are the only reproducible specimens of each failure class.

---

## 6. Hazards the tool must encode

Three traps this arc paid for, which belong in the tool's own docstring rather than being
rediscovered:

- **Shell globbing silently fails on this archive.** `ls cascor-snapshots/*.h5 | wc -l` returned
  **0** — not an error — because the glob exceeded `ARG_MAX`, which briefly read as the entire
  27,896-file archive having vanished during the S-1 move. Sweeps must use `find` or
  `pathlib.glob`, never shell expansion.
- **`mtime` is not creation time here.** A copy reset them all, so files named `2025-10` carry
  2026 mtimes and a `find -mtime` filter would misjudge the whole archive. The authoritative stamp
  is the internal `created` root attribute.
- **The existing CLI already has a count-based delete path.** `snapshot_cli.py cleanup --keep N`
  reaches `snapshot_utils.py:332`'s `os.remove(filepath)` and knows nothing about validity or
  provenance — run against the archive root with the default `--keep 10` it would destroy ~27,886
  files. A diagnosis tool must never grow a delete path, and should arguably be the thing that
  makes `cleanup` look as dangerous as it is.

---

## 7. Non-goals

- **Not** a repair or salvage path. Deciding which of two disagreeing sources is authoritative
  needs provenance (D-C), which does not exist yet.
- **Not** a retention or deletion policy. This tool produces the evidence S-2 is blocked on; it
  does not act on it, and it deletes nothing.
- **Not** an API surface. D-E Q2 settled that the forensic path stays library/CLI; adding an HTTP
  route here would reverse that decision by the back door.

---

## 8. Open questions

1. **`snapshot_cli.py diagnose` subcommand, or a standalone `util/` script?** (§5 — leaning
   subcommand, since it belongs beside the `verify` whose blindness motivates it.)
2. **Should `verify` itself be widened rather than adding a sibling command?** Making `verify`
   see shapes and arch would fix five call sites at once (§3) — but it changes what an existing
   command reports, which is a compatibility question for anything parsing it.
3. **Does the sweep mode belong in CI**, as a scheduled report on the archive's health, or stay
   operator-invoked? A scheduled run would catch a regression in snapshot *writing*, which nothing
   currently would.

---

## 9. Provenance

- Motivated by the D-E Q2 decision (2026-08-21): fail-closed gates with a library/CLI-only
  forensic opt-in.
- Evidence and seed implementation:
  `util/ad-hoc/2026-08-20_shape_broken_network_probe.py` (juniper-ml#1199).
- Taxonomy it must speak: `snapshots/snapshot_load_status.py`, shipped with D-B
  (juniper-cascor#542).
- Parent design:
  [`JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md).
