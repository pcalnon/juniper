# CLI Experimentation — R-2: E-H cascor re-run evidence

**Project**: Juniper — CLI test/validation/experimentation program
**Sub-Project**: juniper-ml / juniper-cascor
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.1
**Last Updated**: 2026-08-13

Register item **R-2** from the P4 §7 follow-ups: re-run the E-H **cascor** leg on a GPU
proven clean, to establish whether the original result was contaminated by the cascor#509
leak. Also the first live campaign under both #509 fixes, so it doubles as their field test.

Scope, as the register requires: **only `p4/e-h-real-data.yaml`**. Of the remaining P4
suites it is the sole `app: cascor` entry — E-D/E-E/E-F/E-G and `e-h-recurrence-real-data.yaml`
are `app: recurrence`, emit no `juniper-cascor.log`, and cascor#509 cannot implicate them.
They were not re-run.

---

## 1. Result — the original E-H cascor evidence stands

Suite `e-h-real-data-20260813T131815Z`, 2/2 cells `succeeded`, both screened `oom == 0`.

| cell | dataset                       | units | train  | val        | wall  | completion        |
|------|-------------------------------|-------|--------|------------|-------|-------------------|
| c000 | spiral control (smoke budget) | 2     | 0.575  | 0.35       | 119 s | `early_stopped`   |
| c001 | equities AAPL 2015–2022       | **0** | 0.5326 | **0.5284** | 32 s  | `below_threshold` |

Against the original, quoted directly from
[`JUNIPER_2026-08-09_…-P4-STUDIES-EVIDENCE.md` §E-H](JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md):

> | equities AAPL 2015–2022 | 0.5284 | 0.5318 (up-day base rate) | 0 | 52 |

**val 0.5284 and 0 hidden units, in both runs.** The clean re-run reproduces the original
exactly. The original E-H cascor result was **not** contaminated, and the
efficient-market-ceiling finding — next-day-direction accuracy ≈ the up-day base rate, no
exploitable signal — holds unchanged.

(Method note, per the §6 retraction discipline: the prior figures above are quoted from the
original document, not inferred from a later re-run.)

### 1.1 The 0-unit result is now provably algorithmic

c001 recruits 0 hidden units and stops at `below_threshold` with best candidate correlation
`0`. Before cascor#511 that shape was ambiguous — an exhausted GPU produced a visually
identical `succeeded` / 0-unit / low-accuracy record. It no longer can: an
all-candidates-errored round raises `CandidateTrainingError` and terminates the run
**Failed**. A `below_threshold` result surviving to `succeeded` is therefore now a positive
statement that every candidate trained and none beat the threshold — which is the honest
finding about real equities.

---

## 2. Live validation of the two cascor#509 fixes

The campaign ran with the primary `juniper-cascor` checkout at `main` carrying both fixes
(#511 honest outcomes, #512 pool lifecycle).

**#512 — pool released at end of run.** GPU free memory across the campaign:

| point | free |
| --- | --- |
| before (after reaping 1 pre-existing orphan) | 4921 MiB |
| mid-campaign, cell 0 training | 4731 MiB |
| after cell 0 teardown | 5079 MiB |
| after both cells | 5077 MiB |

Free memory **returned above its starting value** rather than dropping. The pre-fix
signature was a loss of roughly **285 MiB per cell** with the children surviving teardown.
A post-campaign orphan sweep found **0 reapable processes** — the 18 kept all belong to an
unrelated long-lived service (§3).

**#511 — no false success.** Not exercised as a failure this run (nothing OOMed), but c001
demonstrates the discriminator working in the other direction: `success_count > 0` with zero
candidates above threshold correctly stays a benign `below_threshold`, not an escalation.

---

## 3. Conditions

A separate long-lived **isolated E2E stack** was up throughout (cascor `:8202` at 22 h
uptime, juniper-data `:8101`, canopy `:8051`), holding ~2 GiB of GPU across 18 forkserver
children. It was left untouched: `util/reap_pytest_orphans.bash` correctly classified all 18
as live-parent KEEP and reaped only the one true orphan.

The experiment stack allocated from its own ranges (data `8110`, cascor `8230`), so there was
no port contention. Two cascor processes did share the `juniper-cascor` checkout, which the
one-cascor-per-checkout guidance (H-7, pending Q-6) discourages; the shared resource is the
checkout's own file log, while run dirs, snapshots (`JUNIPER_CASCOR_SNAPSHOTS_DIR`), ports
and sampled metrics are all per-run, so the recorded results are unaffected. The smoke-budget
cells were small enough not to pressure the card.

> **Update (2026-08-16) — "pending Q-6" is stale.** Q-6 is **resolved and shipped**:
> `JUNIPER_CASCOR_LOG_DIR` (cascor#523), exported per run by `util/experiment_stack.bash` (ml#1120).
> This paragraph's verdict is unchanged — these results came from per-run manifests and artifacts, not
> the shared file log. Note the sharper framing Q-6 settled: that log is the *only* place cascor's
> parent logger writes, so a co-tenant process **rotates** such evidence away rather than interleaving
> it. Plan §15.2 Q-6.

---

## 4. Register status

R-2 is closed: **the original E-H cascor evidence is confirmed, not superseded.**

Remaining from the P4 §7 register: re-running **E-A** under R-3 (ml#1077) to obtain a
non-degenerate cap surface — which is also the precondition **R-5** needs, since the
service-vs-CLI comparison is meaningless until the unit budget is equalised
(see the R-5 premise check in ml#1075). That campaign is materially heavier than E-H
(12 cells, up to 32 units, ~4–6 GPU-hours) and should be scheduled when the card is not
shared with a live stack.
