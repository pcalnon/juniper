# juniper-cascor-client v0.7.0 — Release Notes (archived)

> **Backfilled 2026-09-05**, verbatim from the GitHub Release
> [`v0.7.0`](https://github.com/pcalnon/juniper-cascor-client/releases/tag/v0.7.0) (published
> 2026-07-18T00:11:59Z; the body's own header dates the notes 2026-07-16). Unlike the `v0.6.0` entry —
> which was reconstructed from `CHANGELOG.md` plus the tag date during the Phase 0.3 backfill and says
> so — this Release carried a full authored body, so nothing had to be re-derived.
>
> **Why it was missing.** The central-archive convention
> ([`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.3)
> asks that releases cut from other repos be archived here, not only in their own repo. 0.7.0 was
> archived in `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.7.0.md` but never copied across —
> the same drift Phase 0.3 existed to correct, recurring two weeks after it. Found while archiving
> `v0.8.0`, which left this directory reading 0.6.0 → 0.8.0 for this package.

---

# Juniper Cascor Client v0.7.0 Release Notes

**Release Date:** 2026-07-16
**Version:** 0.7.0
**Release Type:** MINOR

---

## Overview

This release ships **CL1** of the canopy training-runtime defects plan: WebSocket heartbeat handling (the root fix for the 40-second control-WS kill behind the 2026-07-10 incident) and a first-class **liveness surface** for consumers. Both stream classes now answer the cascor server's application-level heartbeat pings automatically, the control stream reads its socket from the moment it connects, and consumers get honest connection-health primitives (`is_connected`, `is_alive`, `last_frame_at`, `pongs_sent`) that detect the half-open sockets the historical `_ws is not None` idiom could not. `FakeCascorTrainingStream` carries full parity.

> **Status:** STABLE — Backward-compatible additive release.

---

## Release Summary

- **Release type:** MINOR
- **Primary focus:** CL1 — heartbeat auto-pong + liveness surface + diagnosable unrecognized-frame warnings
- **Breaking changes:** No (pure-additive surfaces; `auto_pong=False` restores legacy ping-yield behaviour)
- **Priority summary:** Root-fixes the idle control-WS kill at 40 s (2026-07-10 incident class); makes canopy's manual-pong relay workaround redundant; provides the seam canopy's supervisor hardening (N2/CL2) swaps onto

---

## Added

- **WebSocket heartbeat handling (CL1).** The cascor server (C3 contract; heartbeat since cascor#133) pings `{"type":"ping","ts":<float>}` every 30 s on `/ws/training` and `/ws/control` and closes after a 10 s pong window. Both stream classes now answer automatically with `{"type":"pong"}` (`auto_pong: bool = True` constructor kwarg on `CascorTrainingStream` / `CascorControlStream`), and `CascorControlStream.connect()` starts the background recv loop eagerly so pings are answered from the moment the connection exists. New constants `WS_MSG_TYPE_PING` / `WS_MSG_TYPE_PONG`.
- **Liveness surface for consumers.** Both stream classes (and `FakeCascorTrainingStream`) expose `is_connected` (real `websockets` protocol state — detects processed closes), `is_alive(window_sec=90)` (connected AND inbound traffic within the window — detects half-open sockets), `last_frame_at`, and `pongs_sent`. A successful `connect()` counts as first liveness evidence.

## Changed

- **`ping` is a recognized transport frame** — consumed before envelope validation; no more per-30s `unrecognized_ws_frame` warning spam (~2,400 lines in the 2026-07-10 session).
- **Unrecognized-frame warnings carry the frame type in the message text** (`type=<type> endpoint=<endpoint>`), not just in the `extra` dict; stable prefix preserved for log-grep continuity; Prometheus counter unchanged.
- **`FakeCascorTrainingStream` parity:** `auto_pong` kwarg, injected pings consumed/counted (or yielded under `auto_pong=False`), full liveness surface.
- `__init__.__version__` corrected to match `[project].version`.

## Compatibility

- **New client / old server:** pongs answered as the server always expected — strictly better.
- **Old client / new server (cascor C3):** unchanged failure mode for idle control connections, now with an observable close (valid code + reason) instead of a silent half-open.
- Canopy's relay keeps `/ws/training` alive via its own pong workaround, which this release makes redundant (the relay simply never sees pings anymore). Downstream follow-up (CL2): canopy floor bump to `>=0.7.0`, adapter `_ws`-seam swap onto the liveness surface, manual-pong retirement.

---

## References

- Plan of record: juniper-ml `notes/JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md` (§4 I-1/I-4, §7 CL1)
- PR: juniper-cascor-client#92 · Server-side companion: juniper-cascor#401 (C3)
- Incident: 2026-07-10 frozen-dashboard session (control WS died 18:17:03; 12+ h half-open)

