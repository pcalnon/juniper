# HANDOFF 2026-08-26 — T6 re-baseline COMPLETE; the CLI-experimentation arc's residual tail

Successor to
[`HANDOFF_2026-08-25_t6-rebaseline-window-held-not-launched.md`](HANDOFF_2026-08-25_t6-rebaseline-window-held-not-launched.md)
(and, through it, the 2026-08-24 document that remains canonical for T6's rationale and trap
catalogue). **T6 is closed.** This document records what shipped, the two things the campaign
found that are *not* closed, the peer-hold ledger (all released), and the arc's remaining
unowned tail so a successor does not re-derive it. Anchors move — locate by pattern.

**Nothing is in flight.** No campaign, no experiment stack, no monitor of this session survives it.
Post-campaign attest at 12:30 CDT: experiment ports clear, zero port locks, GPU 722 MiB, reaper
clean, zero `/dev/shm` residue from the campaign window.

---

## 0. What closed

| item | evidence |
|---|---|
| **T6 re-baseline — 23/23 cells at ONE cascor sha `67d7ea3`**, `worst_rc=0`, 66 min (E-A 1,588 s · E-I 1,781 s · E-C 623 s) | ledger `~/.local/state/juniper-experiments/t6-rebaseline-20260826T075112Z/campaign.jsonl`; suite dirs `e-a-cascor-budget-sweep-20260826T075112Z`, `e-i-cascor-cap-ceiling-20260826T081740Z`, `e-c-cascor-noise-robustness-20260826T084722Z` |
| **Published**: E-C table REPLACED (KNOWINGLY STALE lifted), new "E-A / E-I re-baselined" block, F-P4-6 RESOLVED with the second-attempt record and the `5 m 07 s` correction | `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md` §3–§4 (grep `RE-BASELINED 2026-08-26`, `Second attempt (2026-08-26)`) |
| Currency banners into the two pre-#514 grids | `notes/JUNIPER_2026-08-14_…R3-EA-RERUN-EVIDENCE.md`, `…E-I-CAP-CEILING-EVIDENCE.md` (grep `RE-BASELINED 2026-08-26`) |
| Launch-tooling gate fix (live CPU, not `ps` lifetime average) + orphan sentinel + campaign monitor | **ml#1389** (merged); `util/ad-hoc/2026-08-25_t6_{watch_host_drained,launch,orphan_sentinel,campaign_monitor}.bash` |
| Grid renderer used for the publish | `util/ad-hoc/2026-08-26_t6_render_grids.py` (this PR) |
| cascor#589 (shutdown joins training before uvicorn's SIGTERM re-raise) verified under load | 23 inter-cell stops: 0 leaked `/dev/shm` pairs, 0 `training thread still running` warnings, sentinel reaped 0 |

**Headline results** (details and caveats in the evidence doc — do not quote these without them):
surface cap-bound everywhere as under R-3; control cell E-A c010 ≡ E-I c000 reproduces exactly
(32 units, 0.8825 / 0.8400); accuracy at equal capacity up vs the pre-#514 grid (cap 32 / pool 8
0.735 → 0.840, `wide-pool-long` 0.665 → 0.920, E-I cap 64 → 1.000, cap 128 → 1.000 — the
`n_rotations 3.0` ceiling now reached at 64 units); walls 4–12× shorter, scaling with pool size
(cascor#563). **None of that is attributed to a single commit** — the interval is #514 … #589 and no
control arm exists. E-C's moon curve: 1.0 / 1.0 / 1.0 / 0.975.

## 1. Two findings the campaign left OPEN

1. **E-C's spiral rows are `max_iterations`-bound at 12 units** (the inherited `spiral-baseline`
   cap), so their flat ≈0.63–0.66 curve is a capacity artifact — the same reading F-6 gave for the
   old 2-unit smoke cap, one cap up. A spiral noise-robustness curve needs those four cells at an
   E-I-class `max_iterations` (≥ 64). **Owner decision**; the closed R-4 disposition is not
   reopened by noting it.
2. **`run_experiment.py` tears a `timed_out` / `stalled` cell down with a plain SIGTERM** —
   `preempt_training` (`POST /v1/training/stop` + wait) is only used for a 409 on start. Harmless
   now that cascor#589 joins training in the service's own shutdown, but a graceful stop before
   teardown would also give the collect step a settled final state. Unfiled; small; tested driver.

## 2. Peer-hold ledger — ALL RELEASED 12:30–12:35 CDT

Holds and the cascor checkout freeze were in force from the 02:51 LAUNCH announcement. Released
by name to: `performance lane [1522ce]` (successor of "cli vs service"; now running its G4
re-measure pinned at `67d7ea3`), `canopy e2e [adc3cc]` (successor of "canopy e2e phase 2"; now
bringing the isolated trio up for F-CANOPY-005), `defect register [d2a423]`, `cascor stop fix
[bfdbd9]` (apparent successor of "snapshot"), `duplicati [a20f2d]` (courtesy). The first three
predecessor names had already gone stale — **re-resolve names with `ListAgents` before every
announcement**. Nothing is owed to any peer.

## 3. Traps added by this session (additive to the 2026-24/25 catalogues)

- **`ps %CPU` is a lifetime average.** An idle `duplicati-server` read 45% (live 0.0%) and would
  have held the drain gate shut ~35 h; that, not real load, blocked all of 2026-08-25 after 14:14.
  Both gate scripts now sample `top -b -n 2 -d 1 -w 512`'s second frame (`-w 512` because the
  default width truncates `duplicati-serve` to `duplica+`, which the regex misses). Memory:
  `reference_ps_pcpu_lifetime_average.md`.
- **A monitor that fires while the session is not awake is indistinguishable from one that never
  fired.** The drain watch fired 19:33 and the session was re-invoked 02:30; the campaign completed
  03:58 and was acted on at 12:30. Peers were released 8.5 h late. The ledger's terminal line is
  the authoritative completion signal (the performance-lane session correctly resumed on it);
  peers should be told to read it, and a `PushNotification` at launch/completion is the owner's
  wake-up, not the session's.
- **Looping the full orphan reaper beside a campaign is unsafe**: a freshly launched cell service
  is reparented to `systemd --user` before its health gate writes the protecting pidfile. The
  sentinel's predicate is `multiprocessing.(forkserver|spawn|resource_tracker)` only.
- **The launch host is pinned for the campaign's life.** Launched from worktree
  `dazzling-swimming-stroustrup` at `main` `c36bc886`, synced *before* liftoff and frozen after;
  the primary was avoided because other sessions pull it.

## 4. The arc's remaining tail (unchanged, unowned — carried from the 2026-08-24/25 documents)

T3 residuals (§0.1 there): G-16 live-refusal half unverified; driver still emits the
"see `GET /v1/generators`" pointer instead of consuming `install_hint`; **juniper-data is still
unreleased past `fec68b4`** (newest release v0.11.0), so no consumer sees the field. The five
recurrence wall-ordering rows; the requirements cross-view inconsistency; T2's declined
read-only settings surface; T7's JR-REC coverage items (G-5, W-5/W-7, G-4, G-17); R-1's second
clause; plan §12.2 items 1 and 3; PF-4 / PF-8. None was touched here.

## 5. Git state at handoff

Worktree `juniper-ml/.claude/worktrees/dazzling-swimming-stroustrup`, branch
`worktree-dazzling-swimming-stroustrup`, at `main` `c36bc886` plus the uncommitted publish
(three `notes/` files, the renderer, this document) — carried to `main` by the closing PR via
`util/open_signed_pr.py`. ml#1389 merged 07:39Z under the owner's merge approval for this session's
arc PRs (granted 2026-08-26 ~02:35 CDT; **session-scoped** — a successor re-asks).

## 6. Verification (one stanza per Bash call — the worktree hook refuses compound lines)

```bash
python3 - <<'PY'
import json;S='/home/pcalnon/.local/state/juniper-experiments/t6-rebaseline-20260826T075112Z/campaign.jsonl'
print([json.loads(l)['event'] for l in open(S)])
PY

python3 util/ad-hoc/2026-08-26_t6_render_grids.py /home/pcalnon/.local/state/juniper-experiments/suites/e-a-cascor-budget-sweep-20260826T075112Z

grep -n "RE-BASELINED 2026-08-26\|Second attempt (2026-08-26)\|Status: RESOLVED" notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md

git -C /home/pcalnon/Development/python/Juniper/juniper-cascor log --oneline -1
```
