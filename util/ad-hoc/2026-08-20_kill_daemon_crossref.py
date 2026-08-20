#!/usr/bin/env python3
"""Cross-reference background-task kill timestamps against `~/.claude/daemon.log`.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc investigation tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-20
Status:      ad-hoc -- investigation (one-off, may be re-run after a client upgrade)
Retire when: the kill mechanism is identified, or the mechanism class is excluded and
             `notes/JUNIPER_2026-08-19_JUNIPER-ECOSYSTEM_SAFE-MERGE-KILL-FORENSICS.md`
             section 3.3 is closed.
Related:     forensics doc section 3.3 ("the cheap decisive test -- not run"),
             HANDOFF_2026-08-19 section 2.1.

What this does
--------------
Two INDEPENDENT extractions, then a mechanical join:

  (1) The kill population, from `~/.claude/projects/**/*.jsonl`:
        * launches      -- records carrying `toolUseResult.backgroundTaskId`
        * terminals     -- `<task-notification>` blobs carrying `<task-id>`/`<status>`
        * TaskStop      -- assistant `tool_use` records named `TaskStop`
      Signature A = a TaskStop call names the task.  Signature B = killed with none.

  (2) The daemon event population, from `daemon.log`:
        `[<iso>] [<subsystem>] <message>`

Then, for every signature-B kill, the nearest daemon event in time -- reported with a
signed delta, no threshold applied at extraction time.

Deliberate methodology notes (this test has failed independent reproduction once)
---------------------------------------------------------------------------------
* EVERY row is emitted with file + line provenance so a third party can re-check it.
* Unparseable lines are COUNTED, never silently dropped.
* A kill has TWO timestamps: the `queue-operation`/`enqueue` (earlier, closer to the
  event) and the delivered `user` notification. Both are emitted; the enqueue is the
  join anchor when present. The published 455 ms figure used the delivery.
* The null model is computed over the span daemon.log actually covers, and the
  multi-day gaps are reported, because a null result inside a gap is uninformative
  rather than exculpatory.
* No expected signature is assumed anywhere. The join reports nearest-neighbour
  distances and lets the distribution speak.

Usage
-----
    python3 util/ad-hoc/2026-08-20_kill_daemon_crossref.py
    python3 util/ad-hoc/2026-08-20_kill_daemon_crossref.py --window 2.0
    python3 util/ad-hoc/2026-08-20_kill_daemon_crossref.py --dump-dir <dir>
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
DAEMON_LOG_DEFAULT = Path.home() / ".claude" / "daemon.log"

DAEMON_RE = re.compile(r"^\[([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+Z)\]\s+\[([a-z]+)\]\s+(.*)$")
TASKID_RE = re.compile(r"<task-id>([^<]+)</task-id>")
STATUS_RE = re.compile(r"<status>([^<]+)</status>")
SUMMARY_RE = re.compile(r"<summary>([^<]*)</summary>")


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def iso(dt):
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


# --------------------------------------------------------------------------
# (1) kill population
# --------------------------------------------------------------------------
def scan_transcripts(root: Path):
    launches, terminals, taskstops = {}, {}, {}
    stats = {"files": 0, "lines": 0, "unparseable": 0}

    for path in sorted(root.rglob("*.jsonl")):
        stats["files"] += 1
        try:
            fh = path.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for lineno, line in enumerate(fh, 1):
                stats["lines"] += 1
                if not line.strip():
                    continue
                # cheap prefilter -- the corpus is large
                interesting = (
                    "backgroundTaskId" in line
                    or "<task-notification>" in line
                    or "TaskStop" in line
                )
                if not interesting:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    stats["unparseable"] += 1
                    continue
                prov = f"{path.name}:{lineno}"
                ts = parse_ts(rec.get("timestamp"))

                tur = rec.get("toolUseResult")
                if isinstance(tur, dict) and tur.get("backgroundTaskId"):
                    tid = tur["backgroundTaskId"]
                    prev = launches.get(tid)
                    if prev is None or (ts and prev["ts"] and ts < prev["ts"]):
                        launches[tid] = {
                            "task_id": tid,
                            "ts": ts,
                            "session": rec.get("sessionId") or rec.get("session_id"),
                            "slug": rec.get("slug", ""),
                            "cwd": rec.get("cwd", ""),
                            "version": rec.get("version", ""),
                            "prov": prov,
                        }

                blob = None
                kind = None
                if rec.get("type") == "queue-operation":
                    c = rec.get("content")
                    if isinstance(c, str) and "<task-notification>" in c:
                        blob, kind = c, "enqueue"
                elif rec.get("type") == "user":
                    c = (rec.get("message") or {}).get("content")
                    if isinstance(c, str) and "<task-notification>" in c:
                        blob, kind = c, "delivery"
                if blob:
                    m, s = TASKID_RE.search(blob), STATUS_RE.search(blob)
                    if m and s:
                        tid = m.group(1)
                        sm = SUMMARY_RE.search(blob)
                        e = terminals.setdefault(
                            tid,
                            {
                                "task_id": tid,
                                "status": s.group(1),
                                "summary": sm.group(1) if sm else "",
                                "enqueue_ts": None,
                                "delivery_ts": None,
                                "session": rec.get("sessionId") or rec.get("session_id"),
                                "prov": prov,
                            },
                        )
                        key = "enqueue_ts" if kind == "enqueue" else "delivery_ts"
                        if e[key] is None or (ts and ts < e[key]):
                            e[key] = ts
                        e["status"] = s.group(1)

                if rec.get("type") == "assistant":
                    content = (rec.get("message") or {}).get("content") or []
                    if isinstance(content, list):
                        for blk in content:
                            if (
                                isinstance(blk, dict)
                                and blk.get("type") == "tool_use"
                                and blk.get("name") == "TaskStop"
                            ):
                                inp = blk.get("input") or {}
                                for v in inp.values():
                                    if isinstance(v, str):
                                        taskstops.setdefault(v, []).append(
                                            {"ts": ts, "prov": prov}
                                        )
    return launches, terminals, taskstops, stats


# --------------------------------------------------------------------------
# (2) daemon events
# --------------------------------------------------------------------------
def scan_daemon(path: Path):
    events, bad = [], 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            m = DAEMON_RE.match(line)
            if not m:
                bad += 1
                continue
            ts = parse_ts(m.group(1))
            if ts is None:
                bad += 1
                continue
            events.append(
                {
                    "ts": ts,
                    "subsystem": m.group(2),
                    "message": m.group(3),
                    "prov": f"{path.name}:{lineno}",
                }
            )
    events.sort(key=lambda e: e["ts"])
    return events, bad


def find_gaps(events, threshold_s=3600.0):
    gaps = []
    for a, b in zip(events, events[1:]):
        d = (b["ts"] - a["ts"]).total_seconds()
        if d >= threshold_s:
            gaps.append((a["ts"], b["ts"], d))
    return gaps


# NOTE on "silent" (this replaced an earlier, WRONG `in_daemon_gap` flag).
# The first version asked "does this kill fall inside a >=1h interval between two
# consecutive daemon events?" -- which is true even for a kill 0.4 s after an event,
# because that event is the interval's left endpoint. It therefore labelled the one
# real coincidence (the incident, delta -0.426 s) as "in a gap". The question that
# was actually meant is "was the log silent AROUND this kill", which is answered by
# the nearest-neighbour distance directly.
SILENT_S = 600.0


def pair_workers(events):
    """Pair each `bg spawned|claimed-spare <id> (<kind>)` with its `bg settled <id>`."""
    born, pairs = {}, []
    birth_re = re.compile(r"bg (?:spawned|claimed-spare) ([0-9a-f]+) \((\w+)\)")
    settle_re = re.compile(r"bg settled ([0-9a-f]+) \((\w+)\)")
    for e in events:
        m = birth_re.match(e["message"])
        if m:
            born[m.group(1)] = (e["ts"], m.group(2))
            continue
        m = settle_re.match(e["message"])
        if m and m.group(1) in born:
            b, kind = born.pop(m.group(1))
            pairs.append(
                {
                    "worker": m.group(1),
                    "kind": kind,
                    "spawned": b,
                    "settled": e["ts"],
                    "lifetime_s": (e["ts"] - b).total_seconds(),
                    "outcome": m.group(2),
                }
            )
    return pairs


def binom_tail(n, k, p):
    from math import comb

    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--window", type=float, default=2.0, help="coincidence window in seconds (each side)"
    )
    ap.add_argument("--daemon-log", default=str(DAEMON_LOG_DEFAULT))
    ap.add_argument("--projects", default=str(PROJECTS))
    ap.add_argument("--dump-dir", default="")
    args = ap.parse_args()

    dlog = Path(args.daemon_log)
    if not dlog.exists():
        print(f"FATAL: daemon log not found: {dlog}", file=sys.stderr)
        return 2

    events, bad = scan_daemon(dlog)
    print(f"daemon.log            : {dlog}")
    print(f"  events parsed       : {len(events)}  (unparseable: {bad})")
    if not events:
        return 2
    print(f"  span                : {iso(events[0]['ts'])} .. {iso(events[-1]['ts'])}")
    gaps = find_gaps(events)
    print(f"  gaps >= 1h          : {len(gaps)}")
    for a, b, d in sorted(gaps, key=lambda g: -g[2])[:6]:
        print(f"      {iso(a)} .. {iso(b)}  ({d / 3600:.1f} h)")

    launches, terminals, taskstops, stats = scan_transcripts(Path(args.projects))
    print()
    print(
        f"transcripts           : {stats['files']} files, {stats['lines']} lines, "
        f"{stats['unparseable']} unparseable"
    )
    print(f"  launches            : {len(launches)}")
    print(f"  terminal notifs     : {len(terminals)}")
    by_status = {}
    for t in terminals.values():
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
    print(f"  by status           : {dict(sorted(by_status.items()))}")
    print(f"  TaskStop'd task ids : {len(taskstops)}")

    killed = {k: v for k, v in terminals.items() if v["status"] == "killed"}
    sigA = {k: v for k, v in killed.items() if k in taskstops}
    sigB = {k: v for k, v in killed.items() if k not in taskstops}
    print(
        f"  killed              : {len(killed)}  (sig A/TaskStop: {len(sigA)}, "
        f"sig B/unexplained: {len(sigB)})"
    )

    ev_ts = [e["ts"] for e in events]

    far = datetime.max.replace(tzinfo=timezone.utc)
    rows = []
    for tid, k in sorted(
        sigB.items(), key=lambda kv: (kv[1]["enqueue_ts"] or kv[1]["delivery_ts"] or far)
    ):
        anchor = k["enqueue_ts"] or k["delivery_ts"]
        if anchor is None:
            continue
        i = bisect.bisect_left(ev_ts, anchor)
        best = None
        for j in (i - 1, i):
            if 0 <= j < len(events):
                d = (events[j]["ts"] - anchor).total_seconds()
                if best is None or abs(d) < abs(best[0]):
                    best = (d, events[j])
        L = launches.get(tid)
        elapsed = ""
        if L and L["ts"] and anchor:
            elapsed = f"{(anchor - L['ts']).total_seconds():.1f}"
        silent = best is None or abs(best[0]) > SILENT_S
        rows.append(
            {
                "task_id": tid,
                "enqueue_ts": iso(k["enqueue_ts"]),
                "delivery_ts": iso(k["delivery_ts"]),
                "elapsed_s": elapsed,
                "session": (k["session"] or "")[:8],
                "slug": (L or {}).get("slug", ""),
                "summary": k["summary"][:70],
                "nearest_delta_s": f"{best[0]:.3f}" if best else "",
                "nearest_event": (best[1]["message"][:60] if best else ""),
                "nearest_subsystem": (best[1]["subsystem"] if best else ""),
                "nearest_prov": (best[1]["prov"] if best else ""),
                "log_silent": "YES" if silent else "no",
                "kill_prov": k["prov"],
            }
        )

    print()
    print("=" * 118)
    print(
        "SIGNATURE-B KILLS vs NEAREST daemon.log EVENT   (delta = event - kill; "
        "negative = event precedes kill)"
    )
    print("=" * 118)
    print(
        f"{'task_id':<11} {'kill (enqueue)':<25} {'elap':>9} {'quiet':<6} "
        f"{'delta_s':>12}  nearest event"
    )
    print("-" * 118)
    for r in rows:
        print(
            f"{r['task_id']:<11} {r['enqueue_ts'] or r['delivery_ts']:<25} "
            f"{r['elapsed_s']:>9} {r['log_silent']:<6} {r['nearest_delta_s']:>12}  "
            f"[{r['nearest_subsystem']}] {r['nearest_event']}"
        )

    # ---- worker lifetimes -------------------------------------------------
    pairs = pair_workers(events)
    print()
    print("=" * 118)
    print("WORKER LIFETIMES  (daemon.log `bg spawned|claimed-spare` -> `bg settled`)")
    print("=" * 118)
    print(f"{'worker':<10} {'kind':<7} {'lifetime_s':>12}  outcome")
    print("-" * 50)
    for w in sorted(pairs, key=lambda r: r["lifetime_s"]):
        print(
            f"{w['worker']:<10} {w['kind']:<7} {w['lifetime_s']:>12.3f}  {w['outcome']}"
        )
    expired = [w["lifetime_s"] for w in pairs if w["kind"] == "spare" and w["outcome"] == "done"]
    if expired:
        print()
        print(
            f"  spare workers reaching natural expiry: n={len(expired)}  "
            f"min={min(expired):.3f}s  max={max(expired):.3f}s"
        )
        print("  ^ this is the ~3600 s lease. Compare against the elapsed-at-kill column above.")

    # ---- elapsed-at-kill ceiling -----------------------------------------
    el = sorted(float(r["elapsed_s"]) for r in rows if r["elapsed_s"])
    band = [x for x in el if 3550.0 <= x <= 3650.0]
    print()
    print("=" * 118)
    print("ELAPSED-AT-KILL CEILING")
    print("=" * 118)
    print(f"  sig-B kills with resolvable elapsed : {len(el)}")
    print(f"  elapsed values                      : {[round(x, 1) for x in el]}")
    print(f"  in the 3600 s band [3550,3650]      : {len(band)}  {[round(x, 3) for x in band]}")
    print("  A task cannot outlive the worker hosting it. Tasks launched onto a FRESH spare")
    print("  die at ~3600 s; tasks adopted onto an AGED spare die at whatever runway is left,")
    print("  which is why elapsed-at-kill carries no duration signal on its own.")

    # ---- null model -------------------------------------------------------
    w = args.window
    span_start, span_end = events[0]["ts"], events[-1]["ts"]
    ivs = []
    for e in events:
        lo = (e["ts"] - span_start).total_seconds() - w
        hi = (e["ts"] - span_start).total_seconds() + w
        if ivs and lo <= ivs[-1][1]:
            ivs[-1] = (ivs[-1][0], max(ivs[-1][1], hi))
        else:
            ivs.append((lo, hi))
    covered = sum(hi - lo for lo, hi in ivs)
    total = (span_end - span_start).total_seconds()
    p = covered / total if total else 0.0

    inw = [r for r in rows if r["nearest_delta_s"] and abs(float(r["nearest_delta_s"])) <= w]
    n = len(rows)
    k_hits = len(inw)

    print()
    print("=" * 118)
    print("NULL MODEL")
    print("=" * 118)
    print(f"  window (each side)  : +/- {w} s")
    print(f"  daemon span         : {total / 3600:.1f} h")
    print(f"  covered by windows  : {covered:.1f} s  ->  p = {p:.6f}")
    print(f"  sig-B kills tested  : {n}")
    print(f"  kills within window : {k_hits}")
    if n:
        print(f"  P(X >= {k_hits}) under uniform null : {binom_tail(n, k_hits, p):.4g}")
    print()
    print("  CAVEAT 1: the uniform null is ANTI-CONSERVATIVE. Kills and daemon events both")
    print("            concentrate in active working hours, so the true p is larger than")
    print("            the figure above. Treat it as an upper bound on significance.")
    print("  CAVEAT 2: kills marked quiet=YES sit in a stretch where the log was silent for")
    print("            more than 10 min either side; for those a miss is uninformative, not")
    print("            exculpatory. The daemon was DOWN for several multi-day stretches while")
    print("            background tasks kept running and kept dying.")
    quiet = sum(1 for r in rows if r["log_silent"] == "YES")
    print(f"  kills in a quiet stretch : {quiet} of {n}  (informative sample: {n - quiet})")

    if args.dump_dir:
        d = Path(args.dump_dir)
        d.mkdir(parents=True, exist_ok=True)
        if rows:
            with (d / "sigb_kills_vs_daemon.csv").open("w", newline="") as fh:
                wri = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                wri.writeheader()
                wri.writerows(rows)
        with (d / "daemon_events.csv").open("w", newline="") as fh:
            wri = csv.DictWriter(fh, fieldnames=["ts", "subsystem", "message", "prov"])
            wri.writeheader()
            for e in events:
                wri.writerow(
                    {
                        "ts": iso(e["ts"]),
                        "subsystem": e["subsystem"],
                        "message": e["message"],
                        "prov": e["prov"],
                    }
                )
        with (d / "all_terminals.csv").open("w", newline="") as fh:
            wri = csv.DictWriter(
                fh,
                fieldnames=["task_id", "status", "enqueue_ts", "delivery_ts", "taskstop", "prov"],
            )
            wri.writeheader()
            for tid, t in sorted(terminals.items()):
                wri.writerow(
                    {
                        "task_id": tid,
                        "status": t["status"],
                        "enqueue_ts": iso(t["enqueue_ts"]),
                        "delivery_ts": iso(t["delivery_ts"]),
                        "taskstop": "yes" if tid in taskstops else "no",
                        "prov": t["prov"],
                    }
                )
        print(f"\n  dumped CSVs to      : {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
