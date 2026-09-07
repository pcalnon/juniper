# PF scenario suites (plan §12.3 — Wave 7.3)

Operator surface (PF-1 matched epoch pair, matrix-axis repeats, scrapeability, PF-3 stall/wall, PF-4/PF-8 not driver suites): [`docs/REFERENCE.md` § PF Scenario Suites](../../../../docs/REFERENCE.md#pf-scenario-suites).

Runnable instruments for the performance-scenario matrix. **Thresholds are deliberately absent**: §12 fixes the reuse decisions and the measurement contract only — the scenario matrix and its thresholds still need a ratification pass of their own. Run any file with:

```bash
python util/experiments/run_suite.py --suite util/experiments/suites/perf/<file>.yaml --dry-run   # inspect first
```

| ID | File | Instrument surface |
| --- | --- | --- |
| PF-1 | `pf1-cascor-spiral-repeats.yaml` | step-duration p50/p95 + wall-clock variance over 5 identical cells |
| PF-2 | `pf2-cascor-dataset-scaling.yaml` | wall-clock vs samples; RSS via the experiments dashboard Performance row |
| PF-3 | `pf3-cascor-pool-scaling.yaml` | speedup curve; oversubscription onset via the Process CPU Rate panel |
| PF-4 | — not a driver suite | cascor's in-repo perf suite vs `baseline_20260526.json` (`juniper-cascor` `tests/performance/`) |
| PF-5 | `pf5-recurrence-d-scaling.yaml` | fit time vs `d`; r² vs fit time |
| PF-6 | `pf6-recurrence-nsteps-scaling.yaml` | fit time vs window count |
| PF-7 | `pf7-recurrence-readout-rungs.yaml` | fit time + r² per readout rung |
| PF-8 | — not a sequential suite | two **simultaneous** runs with pinned equal thread budgets (Wave 7.5 parallel mode / manual two-terminal per the P3 isolation precedent) |
