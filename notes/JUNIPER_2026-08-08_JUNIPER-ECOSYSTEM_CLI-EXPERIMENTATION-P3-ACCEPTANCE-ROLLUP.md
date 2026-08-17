# CLI Experimentation — P3 Acceptance-Criteria Roll-Up

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Sub-Project**: CLI test / validation / experimentation program (plan §10.4, Wave 6.3)
**Author**: Paul Calnon
**Date**: 2026-08-08
**Status**: EVALUATED — 9/9 criteria evidenced; one sub-arm (Grafana dashboard render) pending the F-P1-2 owner decision
**Plan of record**: [JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md](JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md) §10.4
**Prior evidence**: [P0](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md) · [P1](JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P1-SMOKE-EVIDENCE.md) · [P2](JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P2-DATASET-MATRIX-EVIDENCE.md)

---

## 1. Verdict table (§10.4 criteria)

| # | Class | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Correctness (cascor) | **PASS** | Spiral P1.1 reference run (exit 0, COMPLETED 24 s). Separability (P2 run dirs, `metrics_final.json` val accuracy vs majority class): **xor 0.945 vs 0.500**, **circles 1.000 vs 0.500** — both clear margins, as the criterion requires. Bonus rows: moon 0.995, gaussian 0.989 vs 0.333. Honest observation: checkerboard reached only 0.545 vs 0.501 at the P2 smoke budget (`max_hidden_units 6` / 4 iterations under-fits the 16-cell board) — a difficulty-ranking data point for E-B, not a criterion failure (the criterion names xor and circles). Hidden units ≤ `max_hidden_units` in every manifest. |
| 2 | Correctness (recurrence) | **PASS** | Offline authority: W-8 bench (recurrence#101) — ratified OQ-14 bands **overall PASS**. Service-vs-bench identical-params arm run this session (§2 below): service CV r² **0.98809046** / RMSE **0.15315912** vs the bench primary's 0.9881 / 0.1532 — the service path lands exactly inside the bands; **no service-path defect**. P1.4 already showed CLI `model.npz` r² ≈ service (0.9888). |
| 3 | Readout spectrum | **PASS** | `delay_product`: RFF beats linear — in-repo bench artifact (r² 0.789 vs −0.039, gap **+0.83**; MLP +0.87) and the P2 service-mode `p2-delay-product` row (rff readout, 5/5 plots). |
| 4 | Reproducibility | **PASS — bit-identical** | Two runs of the same YAML on the same SHAs (§2): same content-addressed `dataset_id` (`irregular_sine-1.0.0-2537aaeb…`) and **bit-identical** metrics (CV r² 0.9880904583810473, RMSE 0.15315912126906223 — equal to the last printed digit). No residual nondeterminism observed on this path; the cascor path's multiprocessing/BLAS caveat stays documented in W-8 (~1e-10 cross-env float noise on shared rows). |
| 5 | Config precedence | **PASS** | Named tests per §10.6: cascor `test_experiment_yaml_settings.py` (41 arms incl. CLI>YAML>env>.env>defaults), recurrence `tests/test_experiment_yaml_settings.py` (22 arms; no `.env` tier by design), W-11 `test_w11_cli_yaml_mapping.py` + `test_w11_train_yaml_seeding.py` (explicit-CLI-beats-YAML; YAML seeds unset flags). |
| 6 | Observability | **PASS at the Prometheus level** | P2: `up{run_id} == 1` for all three services throughout; app families carry `run_id`/`experiment` labels. The "experiments dashboard renders it" sub-arm is pending the F-P1-2 decision (§3) — the PromQL layer the dashboard reads from is proven. |
| 7 | Artifacts | **PASS** | P2: 11/11 run dirs with valid `manifest.json`, config copy, full applicable plot set, `stats.json`, `summary.md`. |
| 8 | Isolation | **PASS** | P1 live concurrent stacks (8110 vs 8111); P2 per-row run-dir isolation on one stack; Wave 5.3's `TestTwoRunConcurrency` pins `--down` scoping (run A's teardown leaves run B's pid/locks/pidfile/target intact). Distinct `dataset_id`s wherever params differ (P2 table). "Both visible in Grafana" shares the F-P1-2 shadow (§3); both visible in Prometheus. |
| 9 | Cleanliness | **PASS** | Teardown attestations: P1.7, P2 §6, and this session's parity stack — experiment port ranges empty, target files removed, locks released, `artifacts/` preserved, `JuniperProject.pid` untouched (H-10). |

> **Update (2026-08-16) — criteria 6 and 8 are now FULLY evidenced; the F-P1-2 caveats are spent.**
> Both rows above defer their Grafana sub-arm to the F-P1-2 decision (§3). **F-P1-2 is closed and its
> premise was false** — see the update on §3 below. The sub-arms were then positively evidenced
> against live run `20260817T011726Z-6d05`:
>
> - **Criterion 6** — the `Juniper Experiments` dashboard rendered all 13 panels with real data, and
>   the queries were additionally verified *through Grafana's datasource proxy* (the layer this row
>   correctly noted was unproven: "the PromQL layer the dashboard reads from is proven"). The
>   `run_id` template variable resolves; Training Loss / Accuracy / Hidden Units / Candidate
>   Correlation / Epoch Rate / Step-Duration p50+p95 all populated.
> - **Criterion 8** — both services appear in Grafana, run-scoped (`Targets Up = 2`, each row
>   carrying `run_id` + `experiment`). The row's "both visible in Prometheus" is now "both visible in
>   Grafana" as originally intended.
>
> Full evidence:
> [F-P1-2 closure](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_F-P1-2-GRAFANA-RENDER-CLOSURE-EVIDENCE.md).

## 2. New arms run for this roll-up (2026-08-08)

Stack `20260808T223507Z-2836` (data + recurrence only), config `p3-bench-parity.yaml`: `irregular_sine` with the bench primary's exact parameters — `n_steps 2000, lookback 32, jitter 0.6, noise_std 0.0, seed 0`; `d=16, ridge=0.0, linear readout`; 5-fold expanding walk-forward, embargo 2 (the `run_benchmark.py` primary-row recipe verbatim).

| Arm | Result |
| --- | --- |
| `p3-a` | exit 0, `dataset_id=irregular_sine-1.0.0-2537aaeb25a059a7`, CV r² 0.9880904583810473, RMSE 0.15315912126906223 |
| `p3-b` (identical invocation) | exit 0, same `dataset_id`, **bit-identical** CV r² and RMSE |
| Bench primary (W-8 REPORT) | LMU r² 0.9881, var-Δt RMSE 0.1532 |

Two criteria from one pair of runs: reproducibility (arms a≡b) and service-vs-bench comparability (arm a ≡ bench to report precision). Run dirs preserved under the stack's `RUN_DIR/p3-{a,b}/`; teardown attested.

## 3. F-P1-2 context package — the :3000 Grafana squatter (owner decision, parked until blocking)

Facts (probed read-only 2026-08-08):

- The listener on `:3000` is a **system-level `grafana-server.service`** — apt package `grafana 13.0.1` (Grafana OSS), systemd-**enabled**, running since **2026-07-15 07:05 CDT** (predates this program's 2026-07-29 plan). `/api/health` returns 200 with `database: ok`.
- Credentials are non-default (anonymous 401; `admin:admin` rejected — P1 probe). Whether it holds dashboards anyone built cannot be inspected without credentials; its data lives in `/var/lib/grafana` and survives a service stop.
- Consequence: the juniper-deploy compose Grafana maps host `:3000`, so the containerized dashboard surface (including the Wave-1.4 experiments dashboard) cannot bind while the native service runs. Prometheus itself is unaffected (the P2/P1.6 evidence used the targeted `juniper-prometheus` container).

Options when a dashboard render is actually needed:

1. **Rebind the deploy Grafana** to another host port (compose override, e.g. `3001:3000`) — least destructive, no sudo, reversible; costs a non-standard URL.
2. **Stop/disable the native service** (`sudo systemctl disable --now grafana-server`) — frees `:3000` for the stack; native dashboards (if any) go dormant but are not deleted.
3. **Recover the native instance's credentials** (`sudo grafana-cli admin reset-admin-password …`) and inspect whether it is actually in use before choosing 1 or 2.

Recommendation when it blocks: option 1 to unblock immediately; option 3 then 2 if the native install turns out to be incidental. No action taken now per the owner's direction.

> **Update (2026-08-16) — F-P1-2 is CLOSED, and every fact in this context package is wrong.**
> Do not act on the options above; none is needed, and none was performed.
>
> - **The `:3000` listener was never `grafana-server`.** It is the **Domotz Pro agent** snap
>   (`snap.domotzpro-agent-publicstore.domotzpro-agent-deamon.service`) — the served page is an
>   AngularJS app declaring `ng-app="agent"` and loading `domotz-angular-widgets`. On `:3000`,
>   `/api/health` and `/login` both return **404**.
> - **The `/api/health` 200 + `database: ok`** belongs to the **deploy** Grafana on `:3001`.
> - **The credential mystery is a phantom** — the 401s were Domotz refusing, not Grafana.
> - **The stated consequence was already false when written.** The deploy compose has not mapped
>   host `:3000` since **2026-05-27**: juniper-deploy `c36e52b` (#90) *"fix(grafana): default host
>   port to 3001 (avoid system-installed grafana on 3000)"*. That predates the program plan by two
>   months and this finding by ten weeks. There was never a bind conflict to resolve.
>
> The blocked arms were then evidenced directly (criteria 6/8 update above; P1.6 likewise):
> [F-P1-2 closure](JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_F-P1-2-GRAFANA-RENDER-CLOSURE-EVIDENCE.md).
>
> **Two real defects surfaced while probing, neither Juniper's** (closure note §5): `grafana-server`
> is in a hard restart loop (**12,763** restarts and climbing — it can never bind a port Domotz
> owns; owner-directed remedy is a systemd drop-in repointing it to `:3002`), and the deploy
> Grafana mounts the repo-committed `secrets.example` placeholder while its live password comes from
> `secrets/` — latent today (read-once at init), but a volume re-init would set a publicly-known
> admin password.
>
> **Method lesson.** These probes were real and read-only, but they were probes of the *wrong
> process*, interpreted against an assumption about the compose file that was never checked against
> the compose file. A port probe tells you something is listening, not what.

## 4. Program state after P3

P0 ✓ · P1 ✓ · P2 ✓ · **P3 ✓ (this document)** · Wave 4 ✓ · Wave 5 ✓ (5.5/W-12 parked on Q-7). Remaining: Wave 7 (run_suite, list_runs, PF scenarios owning F-P1-3b, Q-9 alert scoping, bounded-parallel, the Q-12 `JR-REC-*` block proposal), then P4 experimentation studies (§10.5) on the automation Wave 7 provides. Image rebuild for the deploy stack (F-P1-1 unblock) authorized and in progress this session.

> **Update (2026-08-15):** "PF scenarios **owning F-P1-3b**" is superseded — F-P1-3b is **REFUTED**
> (withdrawn in the [F-P1-3 root cause §3](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-F-P1-3-ROOT-CAUSE.md),
> then measured absent in the [head-to-head §5](JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-HEAD-TO-HEAD-SMOKE-EVIDENCE.md)).
> Wave 7 has since shipped and the PF scenarios stand on their own; they simply no longer own that
> finding. Criterion 6 and criterion 8's Grafana sub-arms (§3) remain open against **F-P1-2**, unchanged.
