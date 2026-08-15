# HANDOFF 2026-08-14 — API primer + defect register COMPLETE; no work in flight

**NOTE:  Start here!!**
**This session is recovering from a previous, interrupted session. The work outlined in this prompt is in an unknown state.**
**The first step of this session should be to determine the current state and status of the Juniper Project and this prompt's work.**

---

Independent of the concurrent CLI-experimentation and canopy E2E arcs; touches none of their files.
Nearest sibling by date: [`HANDOFF_2026-08-14_cli-experimentation-p4-arc-complete.md`](HANDOFF_2026-08-14_cli-experimentation-p4-arc-complete.md).

**Nothing is in flight.** Every PR of this arc is merged, the working tree is clean, and no branch
of this arc remains open.

## Shipped and merged (do not redo)

| PR | Item |
| --- | --- |
| ml#1080 | The API primer — 9,866 lines, 57 sections, 17 Controversy blocks, 62 executable example tests |
| ml#1081 | service-core: WebSocket heartbeat closes `1011`, not the reserved `1006` (RFC 6455 §7.4.1) |
| ml#1082 | service-core: `FailedAuthThrottle` — the 401 path consumed no rate-limit budget |
| ml#1092 | The defect register — 96 verified findings extracted from the primer |
| ml#1085 | *(closed unmerged — raced by ml#1084, which landed the identical waiver)* |

Four ad-hoc harnesses also landed, all `util/ad-hoc/2026-08-13_*`: the specification cache
(`fetch_api_specs.bash`, 31 RFCs), the deterministic fragment→document build
(`assemble_api_primer.py`, has `--check`), the worked-example embedder
(`gen_primer_examples.py`), and the extractor that runs the examples out of the document
(`run_primer_examples.py`).

## Verify starting state

```bash
git fetch origin && git log --oneline origin/main -1        # expect 8c4947e or later
python util/ad-hoc/2026-08-13_run_primer_examples.py        # expect "62 passed"
wc -l notes/JUNIPER_2026-08-14_*DEFECT-REGISTER.md          # expect 619
```

## The three findings that change how the register reads

1. **Severity is not reachability.** `juniper-data` publishes no host port in the reference stack
   (internal networks only, `juniper-deploy/docker-compose.yml:135-143`) and `juniper-cascor` is
   loopback-only with attestation. Most `Security` entries are **not** externally exposed. This is
   §2.1, deliberately placed above the tables rather than in an appendix.
2. **`juniper-service-core` is only partially consumed.** `.middleware` / `.security` have exactly
   one production consumer (`juniper-recurrence`, via the lazy root re-export at
   `juniper_recurrence/app.py:26-34`); `.websocket.*` and `workers/` have **none**. Nine register
   entries are therefore latent library defects, not live exposure. See the §4.2 preamble.
3. **Consolidating the forks would make a latent defect live.** The tempting fix for the fork
   divergence — adopt the shared middleware everywhere — is exactly what would activate
   `APD-SVCCORE-003`, a `getattr`-with-default settings lookup that silently skips the WebSocket
   Origin allowlist when a field is absent or misspelled. cascor's fork reads those settings as hard
   attributes, so **on that axis the fork is the stricter copy.** Harden `_setting` first.

## The theme worth more than any single entry

Twelve register findings share one shape: **a guard adopted in one copy of near-identical code and
not in its siblings.** §2.3 splits them because the groups need different fixes — five fork drift
(a drift check against `juniper-service-core` catches these), two sibling-package drift (needs a
written cross-client convention, not tooling), two same-file inconsistency (ordinary review misses).

The natural experiment that proves it: **ml#1082's fix reached `juniper-recurrence` automatically**,
because recurrence imports `SecurityMiddleware` from the shared package. `juniper-cascor` and
`juniper-data` missed it entirely, because both import their own forks. Same fix, same ecosystem,
three services; the only differentiator is library-versus-copy.

## Highest-value next steps, in order

1. **`APD-DATA-002`** — the body-limit bypass in `juniper-data`
   (`juniper_data/api/middleware.py:79-83`). A chunked request with no `Content-Length` streams past
   the 10 MiB cap. Twelve already-written, already-tested lines exist in **two** sibling repos
   (`juniper-cascor/src/api/middleware.py:100-110`). Highest consequence over lowest cost.
2. **`APD-CASCOR-002` + `APD-DATA-034`** — the blanket `ValueError` → 400 handler in **both**
   services. `PydanticSerializationError` subclasses `ValueError`, so server faults are reported as
   client errors and never reach 5xx alerting. It has already bitten once; cascor's
   `coerce_native_scalars` exists solely to dodge it, and juniper-data has no equivalent.
3. **`APD-DATA-006`** — the `record_access` lock asymmetry. A `GET` can silently undo a concurrent
   tag edit, because `record_access` rewrites the whole metadata document under a lock the
   tag-update path does not take.
4. **A drift check** comparing the forked middleware in `juniper-data` and `juniper-cascor` against
   `juniper-service-core`. Five of the twelve drift findings are copies of shared code that diverged
   silently; nothing currently notices.

## Read before triaging the register

- **§2.1** (reachability) and the **§4.2 preamble** (consumer split) — a reader who skips these will
  mis-triage roughly a third of the 96 entries.
- Entries marked **`†`** are **register-original**: verified against source but *not* asserted by the
  primer. Everything unmarked is a genuine extraction.
- **Coverage is uneven by construction.** The primer visited code where it made a good example, so
  `juniper-canopy` and `juniper-cascor-worker` are nearly absent. **Their absence is not evidence of
  health.**

## Method notes worth reusing

- **Primary sources on disk beat recall.** All 31 cited specifications were downloaded and grepped
  rather than remembered; the cache is reproducible via `fetch_api_specs.bash`. This caught several
  errors that would otherwise have shipped, including that the `RateLimit` header fields are still an
  Internet-Draft and that RFC 7396 (not the widely-miscited 7386) is JSON Merge Patch.
- **Independent validation found what self-review would not.** Across the primer and the register,
  adversarial passes produced 3 fabricated attributions, 9 wrong citations, 4 overstatements, 1 false
  positive, 1 duplicate pair and 1 omission — against 85 confirmed. Two of the corrections reversed
  claims made in earlier turns of the session.
- **A validator can be wrong too.** One reviewer's "no service imports the shared middleware" was
  false (its grep missed the lazy root re-export), and the correction agent caught it rather than
  applying the instruction. Verify a correction before applying it, exactly as you verify a finding.

## Unrelated, but live

Post-Merge Main Verification has a recurring failure class documented in memory
(`project_main_verify_red_since_2026-08-12`): the G3.1 catch-up base makes each red guarantee the
next, and the two screens take **different** waiver trailer formats. Both known occurrences are
resolved as of ml#1084 and ml#1089. The `Regression Battery` job passing while `Symbol & Docs Screen`
fails is the tell for this class.
