#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License

Pointer-follow soak instrument -- section 6 of the shared-session-memory plan
(``notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md``).
Protocol: ``notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md``.

WHY v0.2 EXISTS -- v0.1 could not falsify the bet
--------------------------------------------------
Three independent reviews (statistical, decision-theoretic, adversarial) found
the same dominant defect: **the denominator was conditioned on the outcome.**
An occasion was recorded only if someone NOTICED a relocated fact was relevant,
but the dominant failure of a pointer architecture is *the agent never knew the
fact existed* -- and that agent cannot notice. Follows were logged at ~100%,
ignorance-misses at ~0%. At q_miss ~ 0.26 a true 0.70 printed as exactly 0.900.

Every error term in v0.1 had the same sign. Nothing in it could make the
measured rate look worse than the truth. That is a confirmation procedure with
error bars, not a falsification test.

THE TWO ARMS
------------
**seeded** (verdict-bearing). Each row is one run of a PRE-REGISTERED PROBE from
``conf/soak_probes.json`` -- a task that cannot be done correctly without a
specific relocated fact. The denominator is fixed before the session starts, so
q_miss == q_follow == 1 and the estimate is unbiased. Fifteen seeded runs are
worth more than sixty self-reported ones.

**organic** (descriptive only). Opportunistic self-report. Retained because it
is free and occasionally shows something, but it is NEVER used for a verdict and
is reported explicitly as an UPPER BOUND with a q_miss sensitivity row.

VERDICTS ARE ON THE INTERVAL, NOT THE POINT ESTIMATE
----------------------------------------------------
v0.1 compared a point estimate to 0.90. That threshold is unreachable: a Wilson
lower bound clearing 0.90 needs 35 consecutive perfect runs, and at a TRUE rate
of exactly 0.90 the old rule fired BET-HOLDS only 55% of the time -- ~55% power
against its own hypothesis. v0.2 tests the Wilson interval against a single
reachable boundary and NAMES THE VERDICT AFTER WHAT WAS PROVEN, so a 0.75-grade
interval cannot print a word that authorises the P5 fleet rollout.

Exit codes
----------
``record`` / ``probe-run`` / ``resolve``  0 written, 2 rejected
``report``                                0 always
``status``                                0 in progress or holds, 1 action due, 2 no data
``verify-probes``                         0 registry sound, 1 defective
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# #1196 -- the first commit at which AGENTS.md is in its post-P3, hazards-correct
# shape. Full SHA: a 7-char abbreviation can go ambiguous, and this predicate
# fails CLOSED, so an ambiguous marker would refuse every write.
START_MARKER = "500508b"

DEFAULT_LEDGER = Path("reports/soak/pointer_follow_soak.jsonl")
DEFAULT_PROBES = Path("conf/soak_probes.json")

# Seeded runs needed before a terminal verdict. At an observed 0.90 a Wilson
# lower bound clears 0.75 at n=33; 35 is that, rounded up. This is a PRECISION
# target -- v0.1's session count controlled nothing, because the rate was over
# occasions while the stop was over sessions.
TARGET_PROBE_RUNS = 35
MIN_DISTINCT_PROBES = 15

# One boundary, tested against the interval. 0.75 is the strongest claim
# reachable inside a soak this project will actually run: LB >= 0.80 needs ~62
# clean runs and LB >= 0.90 needs an observed 0.96+, which no honest study here
# reaches. 0.90 survives only as a descriptive line, never as a trigger.
DECISION_BOUNDARY = 0.75
Z_95 = 1.959963984540054

# Area escalation is a RATE rule, not a count rule. A fixed absolute count is an
# absorbing barrier: re-evaluated on every append it fires eventually under the
# null (measured 47% family-wise at 60 occasions, -> 100% with exposure), so the
# escalation it produces carries no information. Bonferroni over observed areas.
AREA_MIN_MISSES = 3
AREA_ALPHA = 0.05

# "source-recovered" (owner decision 2026-08-31): the agent produced the CORRECT
# answer but reached the fact from source -- the helper, its test, a grep -- rather
# than through the relocated pointer. It is recordable directly so a future scorer
# does not have to file a miss and then re-score it; the `rescore` verb exists for
# the 2026-08-22 backlog that was scored before this outcome did.
#
# It is NOT a follow and does NOT leave the denominator. See `analyse`.
OUTCOMES = ("follow", "miss", "source-recovered")
ARMS = ("seeded", "organic")
SEVERITIES = ("hazard", "operational", "reference")

# "area-systematic" is deliberately absent: it is DERIVED. Letting an author type
# it would let the escalation be declared rather than earned.
MISS_CLASSES = {
    "discoverability": "agent never knew to look -> rung 1: add an index row",
    "hazard": "the missed fact was hazard-class -> rung 2: CI gate or hook",
    "pointer-defect": "pointer wrong/stale -> fix the pointer, not the architecture",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(cwd: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=False)
    except OSError:
        return 127, ""
    return p.returncode, p.stdout.strip()


def repo_root(start: Path) -> Path:
    """Resolve the real repo root.

    v0.1 trusted ``Path.cwd()``, so a session that had cd'd into a subdirectory
    silently created a brand-new ledger there -- never merged, never read, never
    committed, and reported success.
    """
    rc, out = _run(start, "git", "rev-parse", "--show-toplevel")
    return Path(out) if rc == 0 and out else start


def wilson(k: int, n: int, z: float = Z_95) -> tuple[float, float] | tuple[None, None]:
    """Wilson score interval.

    Not Wald: at k/n near 1 Wald produces impossible bounds (27/30 -> upper
    1.007) and its coverage collapses, so 20/20 would read as certainty.
    """
    if n <= 0:
        return (None, None)
    p = k / n
    zz = z * z
    denom = 1 + zz / n
    centre = (p + zz / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + zz / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Bin(n, p)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(math.comb(n, i) * (p**i) * ((1 - p) ** (n - i)) for i in range(k, n + 1))


def at_or_after_marker(root: Path) -> bool | None:
    """True if HEAD descends from the marker. None if undecidable."""
    rc, _ = _run(root, "git", "rev-parse", "--verify", f"{START_MARKER}^{{commit}}")
    if rc != 0:
        return None
    rc, _ = _run(root, "git", "merge-base", "--is-ancestor", START_MARKER, "HEAD")
    return rc == 0


def load_probes(path: Path) -> dict:
    if not path.exists():
        return {"probes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_rows(ledger: Path) -> tuple[list[dict], int]:
    """Read the ledger. Returns (rows, bad_line_count).

    Dedup is on ``obs_id`` (uuid4). v0.1 keyed on ``(session, seq)`` with ``seq``
    computed at record time -- so two worktrees recording concurrently both
    computed seq=1 and the loader DELETED one, with the survivor decided by merge
    order. Subagents inherit the parent's CLAUDE_CODE_SESSION_ID, which makes
    that collision routine rather than exotic.
    """
    if not ledger.exists():
        return [], 0
    rows: list[dict] = []
    seen: set[str] = set()
    bad = 0
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if not isinstance(row, dict) or not row.get("obs_id"):
            bad += 1
            continue
        if row["obs_id"] in seen:
            continue
        seen.add(row["obs_id"])
        rows.append(row)
    return rows, bad


def norm_area(a: str | None) -> str | None:
    return a.strip().lower() if a and a.strip() else None


def analyse(rows: list[dict], bad_lines: int = 0) -> dict:
    """Reduce the ledger. The seeded arm decides; the organic arm describes."""
    resolved = {r.get("resolves") for r in rows if r.get("kind") == "resolve"}

    # An observation against a probe later found DEFECTIVE is not data. It must
    # leave the denominator -- but by an auditable append, never by deleting the
    # line, or the ledger stops being a record of what was actually run. The
    # 2026-08-21 pilot needed this: 9 of 15 probes turned out to test facts that
    # had never been relocated, so their runs measured nothing.
    invalidated = {r.get("invalidates") for r in rows if r.get("kind") == "invalidate"}

    # Re-scoring (owner decision 2026-08-31). A run where the agent produced the
    # CORRECT answer but reached it from source rather than through the relocated
    # pointer is not the same event as failing to obtain the fact, and scoring
    # both as "miss" conflated them. Like resolve and invalidate this is an
    # APPEND -- the original observation stays in the file, so the record shows
    # what was scored as well as what it was re-scored to.
    #
    # It deliberately does NOT remove the run from the follow-rate denominator.
    # Doing so was considered and rejected: 9 of the 11 architectural misses are
    # source-recovered, so dropping them would move the rate from 24/35 (68.6%,
    # spanning the boundary) to 24/26 (92.3%, clearing it) and convert
    # INCONCLUSIVE into a pass by redefinition. The pointer either did the work
    # or it did not; recovering the fact another way does not make it a follow.
    rescored = {
        r.get("rescores"): r.get("to_outcome")
        for r in rows
        if r.get("kind") == "rescore" and r.get("rescores") and r.get("to_outcome")
    }
    obs = [r for r in rows
           if r.get("kind") not in ("resolve", "invalidate", "rescore")
           and r.get("obs_id") not in invalidated]

    # in_scope must be EXPLICITLY true. v0.1 used `is not False`, so a missing
    # key, None, 0 or "no" all counted as in-scope -- fail-open on exactly the
    # hand-written retrospective rows the organic arm depends on.
    in_scope = [r for r in obs if r.get("in_scope") is True]
    out_of_scope = len(obs) - len(in_scope)

    seeded = [r for r in in_scope if r.get("arm") == "seeded"]
    organic = [r for r in in_scope if r.get("arm") == "organic"]

    def eff(r: dict) -> str | None:
        """The outcome after re-scoring. Never read `outcome` directly below."""
        return rescored.get(r.get("obs_id"), r.get("outcome"))

    def rate_of(rs: list[dict]) -> dict:
        # pointer-defect is excluded from the ARCHITECTURAL rate (the agent did
        # try to follow; the target was broken) but is counted and thresholded
        # separately, so a pile of broken pointers cannot read as success.
        arch = [r for r in rs if r.get("miss_class") != "pointer-defect"]
        f = [r for r in arch if eff(r) == "follow"]
        m = [r for r in arch if eff(r) == "miss"]
        sr = [r for r in arch if eff(r) == "source-recovered"]
        pd = [r for r in rs if r.get("miss_class") == "pointer-defect"]
        # source-recovered stays IN the denominator -- see the note on `rescored`.
        n = len(f) + len(m) + len(sr)
        lo, hi = wilson(len(f), n)
        return {
            "runs": len(rs),
            "follows": len(f),
            "misses": len(m),
            "pointer_defects": len(pd),
            "denom": n,
            "rate": (len(f) / n) if n else None,
            "ci_low": lo,
            "ci_high": hi,
            # source_recovered: the agent got the fact, but NOT via the pointer.
            # retention answers a different question from `rate`: `rate` asks
            # whether the pointer did the work, retention asks whether relocation
            # LOST the fact. Reporting only one of them is how a safe relocation
            # reads as a failure, or an unproven pointer reads as a success.
            "source_recovered": len(sr),
            "retention": ((len(f) + len(sr)) / n) if n else None,
            "retention_ci": wilson(len(f) + len(sr), n),
            # An unclassifiable row is neither follow nor miss nor defect. v0.1
            # let those inflate the occasion count while contributing nothing.
            "unclassified": len(rs) - len(f) - len(m) - len(sr) - len(pd),
            "_follows": f,
            "_misses": m,
            "_source_recovered": sr,
        }

    s = rate_of(seeded)
    o = rate_of(organic)

    # N counts only sessions that contributed a RATE-BEARING row. v0.1 counted
    # every in-scope session, so 19 pointer-defect sessions plus one follow
    # reached "N=20" on a denominator of 1.
    # Source-recovered rows are RATE-BEARING -- they sit in the denominator -- so
    # their sessions count here too. Omitting them dropped N from 35 to 26 the
    # moment the backlog was re-scored, understating the study's own size on a
    # change that was supposed to reclassify rows, not lose them.
    sessions = {
        r.get("session")
        for r in (s["_follows"] + s["_misses"] + s["_source_recovered"])
        if r.get("session")
    }
    probes_run = {r.get("probe_id") for r in seeded if r.get("probe_id")}

    # Severity strata. Severity comes from the probe registry, never from a
    # judgement at scoring time, so the hazard stratum cannot be defined post hoc.
    haz = [r for r in seeded if r.get("severity") == "hazard"]
    # Reads the EFFECTIVE outcome. A hazard run re-scored to source-recovered is
    # no longer an escalation: the agent obtained the fact and handled the hazard
    # correctly, which is what rung 2 exists to guarantee. It did not reach the
    # fact through the pointer, and that shortfall is carried by the follow rate,
    # not by a standing hazard alarm.
    haz_misses = [r for r in haz if eff(r) == "miss" and r.get("miss_class") != "pointer-defect"]
    haz_open = [r for r in haz_misses if r.get("obs_id") not in resolved]

    # Area escalation: rate rule with Bonferroni over observed areas.
    by_area_miss: dict[str, int] = defaultdict(int)
    by_area_n: dict[str, int] = defaultdict(int)
    for r in seeded + organic:
        a = norm_area(r.get("area"))
        if not a:
            continue
        by_area_n[a] += 1
        # Effective outcome here too, or an area would look systematically bad on
        # runs that were re-scored out of the miss column everywhere else -- the
        # rung-3 alarm would then fire on a rate no other view still reports.
        if eff(r) == "miss" and r.get("miss_class") != "pointer-defect":
            by_area_miss[a] += 1
    pooled = s["rate"]
    pooled_miss = (1 - pooled) if pooled is not None else None
    n_areas = max(1, len(by_area_n))
    systematic = []
    if pooled_miss is not None and pooled_miss > 0:
        for a, k in sorted(by_area_miss.items()):
            if k < AREA_MIN_MISSES:
                continue
            if binom_sf(k, by_area_n[a], pooled_miss) <= AREA_ALPHA / n_areas:
                systematic.append(a)

    # Escalations are reported ALONGSIDE the verdict, never instead of it. In
    # v0.1 an if/elif chain let a single hazard miss mask an 11% follow rate,
    # and -- the ledger being append-only with no discharge -- pinned the
    # verdict there permanently, so the soak went dark on its first real finding.
    escalations = []
    if haz_open:
        escalations.append({"kind": "hazard", "rung": 2, "count": len(haz_open),
                            "obs_ids": [r["obs_id"] for r in haz_open]})
    if systematic:
        escalations.append({"kind": "area-systematic", "rung": 3, "areas": systematic})
    if s["runs"] and s["pointer_defects"] / s["runs"] > 0.10:
        escalations.append({"kind": "pointer-defect", "rung": 0,
                            "count": s["pointer_defects"]})

    # Verdict. Data-integrity states outrank everything: a destroyed instrument
    # must not read as a healthy one.
    if bad_lines:
        verdict, note = "DEGRADED", f"{bad_lines} unparseable ledger line(s)"
    elif not obs:
        verdict, note = "NO-DATA", "ledger absent or empty"
    elif s["denom"] == 0:
        verdict, note = "NO-SEEDED-DATA", "no seeded runs; the organic arm cannot decide"
    elif s["runs"] < TARGET_PROBE_RUNS or len(probes_run) < MIN_DISTINCT_PROBES:
        verdict, note = "IN-PROGRESS", (
            f"{s['runs']}/{TARGET_PROBE_RUNS} runs, "
            f"{len(probes_run)}/{MIN_DISTINCT_PROBES} distinct probes")
    elif not haz:
        # A hazard stratum with zero observations cannot vacuously pass.
        verdict, note = "INCONCLUSIVE", "hazard stratum is empty; run hazard probes"
    elif s["ci_low"] is not None and s["ci_low"] >= DECISION_BOUNDARY:
        verdict, note = f"HOLDS-AT-{DECISION_BOUNDARY}", "lower bound clears the boundary"
    elif s["ci_high"] is not None and s["ci_high"] < DECISION_BOUNDARY:
        verdict, note = "BET-FAILING", "upper bound is below the boundary"
    else:
        verdict, note = "INCONCLUSIVE", "the interval spans the boundary"

    return {
        "verdict": verdict,
        "note": note,
        "escalations": escalations,
        "seeded": {k: v for k, v in s.items() if not k.startswith("_")},
        "organic": {k: v for k, v in o.items() if not k.startswith("_")},
        "sessions": len(sessions),
        "distinct_probes": len(probes_run),
        "target_runs": TARGET_PROBE_RUNS,
        "min_distinct_probes": MIN_DISTINCT_PROBES,
        "boundary": DECISION_BOUNDARY,
        "hazard_runs": len(haz),
        "hazard_misses_open": len(haz_open),
        "out_of_scope": out_of_scope,
        "bad_lines": bad_lines,
        "start_marker": START_MARKER,
    }


def sensitivity(rate: float | None) -> list[tuple[float, float]]:
    """What true rate an observed organic rate implies at various q_miss.

    observed = p / (p + (1-p)*q)  =>  p = observed*q / (1 - observed + observed*q)
    """
    if rate is None:
        return []
    out = []
    for q in (1.0, 0.5, 0.25, 0.1):
        p = rate * q / (1 - rate + rate * q)
        out.append((q, p))
    return out


def _reject(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 2


def _base_row(args: argparse.Namespace, root: Path) -> dict | int:
    session = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID") or ""
    if not session.strip() or session.strip().lower() == "unknown":
        return _reject("a real --session is required (CLAUDE_CODE_SESSION_ID was empty/unknown)")
    scope = at_or_after_marker(root)
    if scope is None and not args.force_scope:
        return _reject(
            f"cannot decide whether HEAD descends from {START_MARKER} "
            "(marker object missing -- `git fetch`?). Refusing to write: this "
            "predicate fails CLOSED because the worktrees lacking the marker are "
            "exactly the stale pre-cut ones. Override with --force-scope.")
    return {
        "obs_id": str(uuid.uuid4()),
        "kind": "observation",
        "ts": _utcnow(),
        "session": session.strip(),
        "in_scope": bool(scope),
        "worktree": root.name,
        "commit": _run(root, "git", "rev-parse", "--short=8", "HEAD")[1] or None,
        "note": args.note,
    }


def _write(ledger: Path, row: dict, dry_run: bool) -> int:
    line = json.dumps(row, sort_keys=True, ensure_ascii=False)
    if dry_run:
        print(line)
        return 0
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(f"recorded {row.get('kind')} {row.get('outcome') or ''} -> {ledger} [{row['obs_id']}]")
    if row.get("in_scope") is False:
        print(f"  warning: HEAD does not descend from {START_MARKER}; row is OUT OF SCOPE",
              file=sys.stderr)
    return 0


def cmd_probe_run(args: argparse.Namespace) -> int:
    root = args.repo_root or repo_root(Path.cwd())
    reg = load_probes(args.probes or (root / DEFAULT_PROBES))
    probe = next((p for p in reg.get("probes", []) if p["probe_id"] == args.probe_id), None)
    if probe is None:
        return _reject(f"unknown --probe-id {args.probe_id!r}; see conf/soak_probes.json")
    if args.outcome == "miss" and not args.miss_class:
        return _reject("a miss requires --class")
    if args.outcome == "follow" and args.miss_class:
        return _reject("--class is only meaningful on a miss")

    base = _base_row(args, root)
    if isinstance(base, int):
        return base
    base.update({
        "arm": "seeded",
        "probe_id": probe["probe_id"],
        "outcome": args.outcome,
        "miss_class": args.miss_class,
        # severity and area come from the FROZEN registry, never the CLI.
        "severity": probe["severity"],
        "area": norm_area(probe.get("area")),
        "fact": probe["fact"],
        "pointer": probe["pointer"],
        "scored_by": args.scored_by,
    })
    return _write(args.ledger or (root / DEFAULT_LEDGER), base, args.dry_run)


def cmd_record(args: argparse.Namespace) -> int:
    root = args.repo_root or repo_root(Path.cwd())
    if args.outcome == "miss" and not args.miss_class:
        return _reject("a miss requires --class")
    if args.outcome == "follow" and args.miss_class:
        return _reject("--class is only meaningful on a miss")
    if args.outcome == "miss" and not norm_area(args.area):
        return _reject("a miss requires --area (a miss you cannot localise is one you cannot remedy)")
    for name in ("fact", "pointer", "task"):
        if not (getattr(args, name) or "").strip():
            return _reject(f"--{name} must not be empty")

    base = _base_row(args, root)
    if isinstance(base, int):
        return base
    base.update({
        "arm": "organic",
        "outcome": args.outcome,
        "miss_class": args.miss_class,
        "severity": args.severity,
        "area": norm_area(args.area),
        "fact": args.fact.strip(),
        "pointer": args.pointer.strip(),
        "task": args.task.strip(),
    })
    return _write(args.ledger or (root / DEFAULT_LEDGER), base, args.dry_run)


def cmd_resolve(args: argparse.Namespace) -> int:
    """Discharge an escalation.

    Without this the ledger is append-only and `analyse` scans all history, so
    one long-since-fixed hazard miss pinned the verdict forever and every future
    `status` exited 1 -- which is exactly how a real signal gets ignored.
    """
    root = args.repo_root or repo_root(Path.cwd())
    ledger = args.ledger or (root / DEFAULT_LEDGER)
    rows, _ = load_rows(ledger)
    if not any(r.get("obs_id") == args.obs_id for r in rows):
        return _reject(f"no observation with obs_id {args.obs_id!r} in {ledger}")
    if not (args.ref or "").strip():
        return _reject("--ref is required: name the PR or gate that discharged this")
    row = {
        "obs_id": str(uuid.uuid4()),
        "kind": "resolve",
        "ts": _utcnow(),
        "resolves": args.obs_id,
        "ref": args.ref.strip(),
        "note": args.note,
    }
    return _write(ledger, row, args.dry_run)


def cmd_invalidate(args: argparse.Namespace) -> int:
    """Retire an observation whose PROBE was defective.

    Distinct from ``resolve``: resolve discharges an escalation that was real and
    has been fixed; invalidate says the observation should never have counted.
    Both are appends -- the original row stays in the file, so the record shows
    what was run as well as what was counted.
    """
    root = args.repo_root or repo_root(Path.cwd())
    ledger = args.ledger or (root / DEFAULT_LEDGER)
    rows, _ = load_rows(ledger)
    if not any(r.get("obs_id") == args.obs_id for r in rows):
        return _reject(f"no observation with obs_id {args.obs_id!r} in {ledger}")
    if not (args.reason or "").strip():
        return _reject("--reason is required: say why the observation is not data")
    row = {
        "obs_id": str(uuid.uuid4()),
        "kind": "invalidate",
        "ts": _utcnow(),
        "invalidates": args.obs_id,
        "reason": args.reason.strip(),
        "note": args.note,
    }
    return _write(ledger, row, args.dry_run)


RESCORE_OUTCOMES = ("source-recovered",)


def cmd_rescore(args: argparse.Namespace) -> int:
    """Re-score an observation to a different outcome (owner decision 2026-08-31).

    Distinct from both siblings: ``invalidate`` says the run should never have
    counted; ``resolve`` discharges an escalation that was real and has been
    fixed; ``rescore`` says the run happened and counts, but was filed under the
    wrong outcome.

    Only ``source-recovered`` is accepted, deliberately. An open-ended re-score
    verb is a way to move any inconvenient row to any convenient column, and the
    whole reason this exists is that 9 of 11 architectural misses were CORRECT
    answers reached from source. Widening it needs the same scrutiny this did.

    It does NOT remove the run from the follow-rate denominator -- see the
    ``rescored`` note in ``analyse``. If it did, this command would convert the
    standing INCONCLUSIVE verdict into a pass by redefinition.
    """
    root = args.repo_root or repo_root(Path.cwd())
    ledger = args.ledger or (root / DEFAULT_LEDGER)
    rows, _ = load_rows(ledger)
    target = next((r for r in rows if r.get("obs_id") == args.obs_id), None)
    if target is None:
        return _reject(f"no observation with obs_id {args.obs_id!r} in {ledger}")
    if target.get("kind") not in (None, "observation"):
        return _reject(f"obs_id {args.obs_id!r} is a {target.get('kind')!r} row, not an observation")
    if args.to not in RESCORE_OUTCOMES:
        return _reject(f"--to must be one of {RESCORE_OUTCOMES}, got {args.to!r}")
    if target.get("outcome") != "miss":
        return _reject(
            f"only a miss can be re-scored; obs_id {args.obs_id!r} is {target.get('outcome')!r}"
        )
    if any(r.get("kind") == "rescore" and r.get("rescores") == args.obs_id for r in rows):
        return _reject(f"obs_id {args.obs_id!r} has already been re-scored")
    if not (args.reason or "").strip():
        return _reject("--reason is required: say what evidence shows the fact was obtained")
    row = {
        "obs_id": str(uuid.uuid4()),
        "kind": "rescore",
        "ts": _utcnow(),
        "rescores": args.obs_id,
        "from_outcome": target.get("outcome"),
        "to_outcome": args.to,
        "reason": args.reason.strip(),
        "note": args.note,
    }
    return _write(ledger, row, args.dry_run)


def _slugs(path: Path) -> set[str]:
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(#{2,6})\s+(.*)", line)
        if m:
            s = m.group(2).strip().lower()
            s = re.sub(r"[^a-z0-9 _-]", "", s).replace(" ", "-")
            out.add(s)
    return out


def cmd_verify_probes(args: argparse.Namespace) -> int:
    """Every probe pointer must resolve, and every probe fact must actually have
    been relocated.

    The second half is the gate this instrument shipped without, and the 2026-08-21
    pilot paid for it: 9 of 15 probes tested facts that were still RESIDENT in
    ``AGENTS.md``, so they measured nothing about pointer-following at all. One of
    them (P01) tested a fact in the resident ``## Hazards`` list -- a section the
    protocol explicitly excludes from being an occasion.

    Checking that a pointer RESOLVES says nothing about whether the fact LEFT the
    source. Each probe therefore declares ``must_be_absent_from_source``: phrases
    that must not appear in ``AGENTS.md``. If one does, the fact is still always
    loaded and the probe is invalid by construction.
    """
    root = args.repo_root or repo_root(Path.cwd())
    reg = load_probes(args.probes or (root / DEFAULT_PROBES))
    probes = reg.get("probes", [])
    problems: list[str] = []
    if not probes:
        problems.append("registry is empty")

    source = root / reg.get("source_file", "AGENTS.md")
    source_text = source.read_text(encoding="utf-8").lower() if source.exists() else None
    if source_text is None:
        problems.append(f"source file {source} not found; residency cannot be checked")
    ids = [p.get("probe_id") for p in probes]
    if len(set(ids)) != len(ids):
        problems.append("duplicate probe_id")
    cache: dict[str, set[str]] = {}
    for p in probes:
        for field in ("probe_id", "severity", "area", "fact", "pointer", "task", "discriminator"):
            if not (p.get(field) or "").strip():
                problems.append(f"{p.get('probe_id')}: missing {field}")
        if p.get("severity") not in SEVERITIES:
            problems.append(f"{p.get('probe_id')}: severity {p.get('severity')!r} not in {SEVERITIES}")
        ptr = p.get("pointer") or ""
        if "#" not in ptr:
            problems.append(f"{p.get('probe_id')}: pointer has no anchor")
            continue
        rel, anchor = ptr.split("#", 1)
        target = root / rel
        if not target.exists():
            problems.append(f"{p.get('probe_id')}: {rel} does not exist")
            continue
        if rel not in cache:
            cache[rel] = _slugs(target)
        if anchor not in cache[rel]:
            problems.append(f"{p.get('probe_id')}: anchor #{anchor} not found in {rel}")

        # THE RESIDENCY GATE. A probe whose fact never left AGENTS.md tests
        # nothing: the agent already has it, so there is no pointer to follow.
        absent = p.get("must_be_absent_from_source")
        if not absent:
            problems.append(
                f"{p.get('probe_id')}: no must_be_absent_from_source -- residency "
                "unverifiable, so the probe cannot be shown to test a RELOCATED fact")
        elif source_text is not None:
            for phrase in absent:
                if phrase.lower() in source_text:
                    problems.append(
                        f"{p.get('probe_id')}: INVALID -- {phrase!r} is still resident "
                        f"in {source.name}; the fact was never relocated")
    if problems:
        print("PROBE REGISTRY DEFECTIVE:")
        for x in problems:
            print(f"  - {x}")
        return 1
    print(f"OK: {len(probes)} probes, all pointers resolve, severities valid.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    root = args.repo_root or repo_root(Path.cwd())
    ledger = args.ledger or (root / DEFAULT_LEDGER)
    rows, bad = load_rows(ledger)
    st = analyse(rows, bad)
    if args.json:
        print(json.dumps(st, indent=2, sort_keys=True))
        return 0
    s, o = st["seeded"], st["organic"]
    print("=== pointer-follow soak ===")
    print(f"  ledger         {ledger}")
    print(f"  verdict        {st['verdict']}  ({st['note']})")
    print()
    print("  -- seeded arm (verdict-bearing; denominator known by construction) --")
    print(f"     runs        {s['runs']}/{st['target_runs']}   "
          f"distinct probes {st['distinct_probes']}/{st['min_distinct_probes']}   "
          f"sessions {st['sessions']}")
    print(f"     follows     {s['follows']}   misses {s['misses']}   "
          f"src-recovered {s['source_recovered']}   "
          f"ptr-defects {s['pointer_defects']}   unclassified {s['unclassified']}")
    if s["rate"] is not None:
        print(f"     rate        {s['rate']:.1%}   95% CI "
              f"[{s['ci_low']:.3f}, {s['ci_high']:.3f}]   boundary {st['boundary']}")
    # Printed next to the rate, never instead of it. They answer different
    # questions -- rate: did the POINTER do the work; retention: did relocation
    # LOSE the fact -- and showing only the flattering one is how a safe
    # relocation reads as a failure, or an unproven pointer reads as a success.
    if s.get("retention") is not None and s["source_recovered"]:
        rlo, rhi = s["retention_ci"]
        print(f"     retention   {s['retention']:.1%}   95% CI [{rlo:.3f}, {rhi:.3f}]"
              f"   (follow OR source-recovered; NOT a pointer-follow rate)")
    print(f"     hazard      {st['hazard_runs']} runs, {st['hazard_misses_open']} open misses")
    print()
    print("  -- organic arm (DESCRIPTIVE ONLY -- an UPPER BOUND, never a verdict) --")
    print(f"     runs        {o['runs']}   follows {o['follows']}   misses {o['misses']}")
    if o["rate"] is not None:
        print(f"     observed    {o['rate']:.1%}  <-- biased UP; misses are under-logged")
        for q, p in sensitivity(o["rate"]):
            print(f"       if misses logged at {q:>4.0%} of follows -> true rate ~ {p:.1%}")
    if st["escalations"]:
        print()
        print("  -- escalations (independent of the verdict) --")
        for e in st["escalations"]:
            print(f"     rung {e['rung']}: {e['kind']} {e.get('areas') or e.get('count')}")
    if st["out_of_scope"] or st["bad_lines"]:
        print()
        print(f"  out-of-scope rows {st['out_of_scope']}   unparseable lines {st['bad_lines']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = args.repo_root or repo_root(Path.cwd())
    ledger = args.ledger or (root / DEFAULT_LEDGER)
    rows, bad = load_rows(ledger)
    st = analyse(rows, bad)
    if args.json:
        print(json.dumps(st, indent=2, sort_keys=True))
    else:
        s = st["seeded"]
        ci = (f"[{s['ci_low']:.3f}, {s['ci_high']:.3f}]" if s["ci_low"] is not None else "n/a")
        print(f"{st['verdict']}  seeded={s['runs']}/{st['target_runs']} "
              f"rate={'n/a' if s['rate'] is None else format(s['rate'], '.1%')} "
              f"ci={ci} escalations={len(st['escalations'])}  ({st['note']})")
        # The VERDICT-driven next action prints FIRST. Escalations used to print
        # above it, so `status` led with "rung 2" and read as though rung 2 were
        # the next step -- when rung 2 is neither taken nor closed, and rung 1 is
        # what the verdict actually calls for. Ascending order, and the two are
        # visually separated, so neither can be mistaken for the other's outcome.
        if st["verdict"] == "BET-FAILING":
            print("  -> the relocation bet is failing; revisit owner decision 7. "
                  "NEVER re-inline.")
        elif st["verdict"] == "INCONCLUSIVE":
            print("  -> rung 1: add index rows for the missed facts, then keep soaking. "
                  "This is the cheap no-regret action when the data cannot decide.")

        if st["escalations"]:
            print("")
            print("  escalations are OPEN and INDEPENDENT of the verdict -- a verdict that "
                  "improves does not close them:")
        for e in st["escalations"]:
            if e["kind"] == "hazard":
                print("  -> rung 2: promote the missed hazard to a CI gate or hook. NEVER re-inline.")
                for oid in e.get("obs_ids", []):
                    print(f"       open: {oid}")
                # `resolve` was previously suggested here as a bare command. It appends a
                # discharge to an APPEND-ONLY ledger and there is no un-resolve, so an
                # escalation cleared to make this command exit 0 cannot be recovered --
                # and the exit code is precisely the thing that tempts you to clear it.
                print("       DISCHARGE ONLY after a real gate or hook has LANDED:")
                print("         python3 util/soak_ledger.py resolve --obs-id <id> --ref <PR that landed it>")
                print("       IRREVERSIBLE: this appends to an append-only ledger; there is no un-resolve.")
                print("       Do NOT run it to make `status` exit 0 -- exiting 1 here is the design.")
                print("       If the miss was a CORRECT answer scored conservatively, that is an "
                      "owner decision about SCORING, not a discharge.")
            elif e["kind"] == "area-systematic":
                print(f"  -> rung 3: path-scoped rule for {e['areas']}. "
                      "Caveat (plan 7.6): a path-scoped rule is LOST AT COMPACTION.")
            else:
                print("  -> fix the broken pointers; these are repo defects, not "
                      "architecture failures.")
    if st["verdict"] in ("NO-DATA", "DEGRADED", "NO-SEEDED-DATA"):
        return 2
    return 1 if (st["escalations"] or st["verdict"] == "BET-FAILING") else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Pointer-follow soak ledger.")
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--probes", type=Path, default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("probe-run", help="record one run of a pre-registered probe (SEEDED)")
    pr.add_argument("--probe-id", required=True)
    pr.add_argument("--outcome", required=True, choices=OUTCOMES)
    pr.add_argument("--class", dest="miss_class", default=None, choices=sorted(MISS_CLASSES))
    pr.add_argument("--session", default=None)
    pr.add_argument("--scored-by", default=None, help="who scored this run")
    pr.add_argument("--note", default=None)
    pr.add_argument("--force-scope", action="store_true")
    pr.add_argument("--dry-run", action="store_true")
    pr.set_defaults(func=cmd_probe_run)

    rec = sub.add_parser("record", help="opportunistic observation (ORGANIC -- descriptive only)")
    rec.add_argument("--outcome", required=True, choices=OUTCOMES)
    rec.add_argument("--fact", required=True)
    rec.add_argument("--pointer", required=True)
    rec.add_argument("--task", required=True)
    rec.add_argument("--area", default=None)
    rec.add_argument("--severity", default="reference", choices=SEVERITIES)
    rec.add_argument("--class", dest="miss_class", default=None, choices=sorted(MISS_CLASSES))
    rec.add_argument("--session", default=None)
    rec.add_argument("--note", default=None)
    rec.add_argument("--force-scope", action="store_true")
    rec.add_argument("--dry-run", action="store_true")
    rec.set_defaults(func=cmd_record)

    rs = sub.add_parser("resolve", help="discharge an escalation")
    rs.add_argument("--obs-id", required=True)
    rs.add_argument("--ref", required=True, help="PR or gate that discharged it")
    rs.add_argument("--note", default=None)
    rs.add_argument("--dry-run", action="store_true")
    rs.set_defaults(func=cmd_resolve)

    inv = sub.add_parser("invalidate", help="retire an observation whose probe was defective")
    inv.add_argument("--obs-id", required=True)
    inv.add_argument("--reason", required=True)
    inv.add_argument("--note", default=None)
    inv.add_argument("--dry-run", action="store_true")
    inv.set_defaults(func=cmd_invalidate)

    rsc = sub.add_parser("rescore",
                         help="re-file a miss under a different outcome (source-recovered)")
    rsc.add_argument("--obs-id", required=True)
    rsc.add_argument("--to", required=True, choices=list(RESCORE_OUTCOMES))
    rsc.add_argument("--reason", required=True)
    rsc.add_argument("--note", default=None)
    rsc.add_argument("--dry-run", action="store_true")
    rsc.set_defaults(func=cmd_rescore)

    vp = sub.add_parser("verify-probes",
                        help="check pointers resolve AND facts actually left the source")
    vp.set_defaults(func=cmd_verify_probes)

    rp = sub.add_parser("report", help="render both arms")
    rp.add_argument("--json", action="store_true")
    rp.set_defaults(func=cmd_report)

    st = sub.add_parser("status", help="verdict + escalations")
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_status)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
