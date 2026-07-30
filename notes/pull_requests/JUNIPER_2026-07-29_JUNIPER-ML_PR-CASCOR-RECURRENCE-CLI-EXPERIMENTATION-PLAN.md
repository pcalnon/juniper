# PR #867 — cascor+recurrence CLI test/validation/experimentation plan of record

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Pull Request**: [#867](https://github.com/pcalnon/juniper-ml/pull/867)
**Branch**: `docs/cascor-recurrence-cli-experimentation-plan` → `main`
**Author**: Paul Calnon
**Date**: 2026-07-29

---

## Summary

- Adds the plan of record `notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (1212 lines): a phased program for testing, validation, and experimentation of **juniper-cascor + juniper-recurrence launched from the command line as on-host services** (no containers, no juniper-canopy).
  It covers: a YAML experiment-config layer (YAML preferred, constants-files fallback, precedence CLI > YAML > env > `.env` > constants), PROPOSED `util/experiment_stack.bash` + `util/experiments/run_experiment.py` launch/drive tooling with per-run `RUN_DIR` isolation, a Grafana bridge for host runs (launcher-owned `socat` relay + Prometheus `file_sd` targets with run-scoped scrape-side labels, R1.1-compliant),
  end-of-run plots (datasets, decision boundaries, training performance, inference results, values/statistics), a 15-hazard concurrency-safety design, full dataset matrices with enablement work items W-1…W-12, and design-beginnings for performance testing/benchmarking (§12) and multi-run experiment automation (§13).
- Drafted and hardened by a multi-agent workflow: 5 read-only recon agents grounded the draft in the live repos; a planner agent wrote it; **three independent adversarial validator agents** then re-probed it with no access to the drafting sources — ~330 citations (327 confirmed, 0 refuted, 0 hallucinated artifacts), 61 mechanical-design claims (1 blocker + 4 majors found in the drafted design),
  and a requirements-coverage/consistency audit (5 majors + 11 minors). All 29 findings were folded in; the validation record is §2.4 of the plan.
- Two-commit history preserves the review surface: `5b64361` is the pre-validation draft; `4fbe230` is the validator correction fold (the diff between them IS the validation outcome, including the §7 redesign after the blocker: a `host-gateway`-addressed scrape can never reach a loopback-bound service, so the bridge became a launcher-owned relay).

## Requirements

- Partially closes JR-CAS-TEST-006 — performance testing infrastructure with reproducible baselines (plan §12 reuses the existing 5-phase perf suite + baselines; CI integration explicitly deferred).
- Partially closes JR-CAS-OBS-004 — define performance targets for latency/throughput (§12.3 scenario list + §7 Grafana surface provide the measurement harness; targets themselves stay an owner decision, Q-8).
- References JR-CAS-TEST-018 — E2E pipeline spun up for real (cascor → juniper-data → artifact → training) as an operator-invoked program, not automated tests.
- References JR-CAS-OBS-002 (shipped) — §12.1 consumes the shipped `juniper_cascor_training_step_duration_seconds` buckets.
- References JR-CAS-PERF-004, JR-CAS-PERF-005 — in-repo profiling used instead of py-spy; continuous profiling noted as a possible later phase.
- References JR-CAS-TEST-019, JR-CAS-OBS-005 — WS-load testing out of scope; the CLI harness is its natural future host.
- References JR-CAS-TRAIN-010 — cited as the config-knob precedent for the §5.4 YAML layer.
- No `JR-REC-*` IDs exist (recurrence postdates the 2026-05-12 snapshot); the plan proposes minting a `rec` block (§16, wave item 7.6).

## Test plan

- markdownlint-cli 0.42.0 with the repo `.markdownlint.yaml` — PASS (0 findings) on the plan document.
- `juniper-check-doc-links` (CI-equivalent invocation: same excludes, `--cross-repo skip`, 547 files) — PASS, all links valid.
- Adversarial citation verification: ~330 claims re-probed against the live repos — 0 refuted, 0 hallucinated artifacts (3 line-number drifts corrected).
- Mechanical/design verification: 61 claims — 1 blocker + 9 majors + 16 minors, all folded in (plan §2.4 record).
- Requirements-coverage audit: owner requirements R1–R10 graded COVERED after corrections.
- Docs-only change — no code, no CI-workflow, no config edits.

## Process notes (for future archaeology)

- Recon agents covered: cascor internals, recurrence internals, juniper-data generator catalog, observability/Grafana path, juniper-ml tooling/conventions. Their digests were session artifacts; the plan's `repo/path:line` citations are the durable ground truth.
- The three validators ran with deliberately disjoint lenses (citations / mechanics / coverage-consistency) and no shared inputs beyond the document itself; the blocker was caught by the mechanics lens, the labeling-honesty sweep (PROPOSED vs existing) came back clean on both sides.
- Notable validator catches beyond the blocker: the stock `YamlConfigSettingsSource` would silently no-op for nested experiment YAML under `extra="ignore"`; cascor's `server.py` parses no CLI flags so YAML could have out-ranked the launcher's port allocation; `candidate_correlation` is absent from `/v1/metrics/history` rows; the recurrence HTTP metric family is `juniper_recurrence_http_*`, not covered by the existing p50/p95/p99 recording rules.
