#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Complementary leftover of ``tests/test_soak_next_probe.py`` and of ml#1699 /
ml#1700.

The unprimed-stdout suite runs against the LIVE ledger and never calls
``post_intervention()``. The consensus reducer suite pins the *ad-hoc* §15.4
split; the Wilson-power suite pins the interval at an observed rate. Neither
can see the production picker that decides which probe spends the next billed
session.

``notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md``
§4.6 / §4.10: ``analyse()`` has no date filter; ``--status`` reports
post-intervention counts; 4 of 8 post runs landed on probes rung 1 never
touched; on-cutoff is POST; bare ``P19`` does not resolve.

Hermetic: synthetic rows only. Never launches ``claude``. Never reads the live
corpus except the frozen probe registry for the prefix-reject CLI arm.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "util" / "soak_next_probe.py"
SCRIPT = MODULE_PATH

_spec = importlib.util.spec_from_file_location("soak_next_probe", MODULE_PATH)
assert _spec and _spec.loader
snp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(snp)

P15 = "P15-worktree-converge-not-remove"
P19 = "P19-port-check-fail-opens"
P21 = "P21-pidfile-key-prefix-guard"
P02 = "P02-assert-release-tag-ref"
P06 = "P06-expect-removals-scope"


def obs(probe_id: str, ts: str, **kw) -> dict:
    row = {
        "obs_id": f"o-{probe_id}-{ts}",
        "kind": "observation",
        "ts": ts,
        "arm": "seeded",
        "probe_id": probe_id,
        "outcome": "follow",
    }
    row.update(kw)
    return row


def _probes(*ids: str) -> list[dict]:
    return [{"probe_id": pid, "task": f"task-{pid}"} for pid in ids]


class PostInterventionSplit(unittest.TestCase):
    """Ledger §15.4: pre-intervention rows are a different corpus."""

    def test_pre_intervention_rows_are_excluded(self) -> None:
        rows = [
            obs(P15, "2026-08-30T23:59:59Z"),
            obs(P15, "2026-08-30"),
            obs(P19, "2026-09-01T00:00:00Z"),
        ]
        kept = snp.post_intervention(rows)
        self.assertEqual([r["probe_id"] for r in kept], [P19])

    def test_on_cutoff_date_is_post(self) -> None:
        # Consensus §4.6 / the ad-hoc reducer: ts >= 2026-08-31 is POST.
        # `>` would drop the cutoff-day rows and re-dispatch already-covered probes.
        rows = [
            obs(P15, "2026-08-31"),
            obs(P19, "2026-08-31T00:00:00Z"),
            obs(P21, "2026-08-31T23:59:59Z"),
        ]
        kept = snp.post_intervention(rows)
        self.assertEqual([r["probe_id"] for r in kept], [P15, P19, P21])

    def test_empty_or_missing_ts_is_excluded(self) -> None:
        missing = obs(P21, "placeholder")
        missing["ts"] = None
        rows = [
            obs(P15, ""),
            obs(P19, "2026-09-01T00:00:00Z"),
            missing,
        ]
        kept = snp.post_intervention(rows)
        self.assertEqual([r["probe_id"] for r in kept], [P19])

    def test_organic_arm_is_excluded_even_when_post(self) -> None:
        rows = [
            obs(P15, "2026-09-01T00:00:00Z", arm="organic"),
            obs(P19, "2026-09-01T00:00:00Z"),
        ]
        kept = snp.post_intervention(rows)
        self.assertEqual([r["probe_id"] for r in kept], [P19])

    def test_mutation_kinds_are_not_counted_as_runs(self) -> None:
        # invalidate / rescore / resolve carry their own obs_id. Counting them
        # as coverage inflates --status the same way keying mutations on obs_id
        # silently no-ops the consensus reducer (ml#1699).
        target = obs(P19, "2026-09-01T00:00:00Z")
        rows = [
            target,
            {"obs_id": "inv-1", "kind": "invalidate", "invalidates": target["obs_id"], "ts": "2026-09-02T00:00:00Z", "arm": "seeded", "probe_id": P15},
            {"obs_id": "rs-1", "kind": "rescore", "rescores": target["obs_id"], "ts": "2026-09-02T00:00:00Z", "arm": "seeded", "probe_id": P15, "to_outcome": "source-recovered"},
            {"obs_id": "rv-1", "kind": "resolve", "resolves": target["obs_id"], "ts": "2026-09-02T00:00:00Z", "arm": "seeded", "probe_id": P21},
        ]
        kept = snp.post_intervention(rows)
        self.assertEqual([r["probe_id"] for r in kept], [P19])

    def test_legacy_kind_none_still_counts_when_seeded_and_post(self) -> None:
        row = obs(P19, "2026-09-01T00:00:00Z")
        row["kind"] = None
        kept = snp.post_intervention([row])
        self.assertEqual([r["probe_id"] for r in kept], [P19])


class PickNextIgnoresPreInterventionPile(unittest.TestCase):
    """The contamination the consensus named: 4 of 8 post runs were on probes
    rung 1 never touched, because the pooled count looked like coverage."""

    def test_pre_intervention_pile_does_not_prevent_picking_an_untouched_probe(self) -> None:
        # P15 has a deep PRE history and zero POST runs. P02 has one POST run.
        # The next billed session must go to P15.
        pre = [obs(P15, f"2026-08-2{i:01d}T00:00:00Z") for i in range(10)]
        post = [obs(P02, "2026-09-01T00:00:00Z")]
        runs = Counter(r.get("probe_id") for r in snp.post_intervention(pre + post))
        self.assertEqual(runs[P15], 0)
        self.assertEqual(runs[P02], 1)
        chosen = snp.pick_next(_probes(P02, P15), runs)
        self.assertEqual(chosen["probe_id"], P15)

    def test_least_post_coverage_wins(self) -> None:
        rows = [
            obs(P02, "2026-09-01T00:00:00Z"),
            obs(P02, "2026-09-02T00:00:00Z"),
            obs(P06, "2026-09-01T00:00:00Z"),
        ]
        runs = Counter(r.get("probe_id") for r in snp.post_intervention(rows))
        chosen = snp.pick_next(_probes(P02, P06), runs)
        self.assertEqual(chosen["probe_id"], P06)

    def test_registry_order_breaks_a_tie(self) -> None:
        chosen = snp.pick_next(_probes(P02, P06, P15), Counter())
        self.assertEqual(chosen["probe_id"], P02)

    def test_pooling_pre_and_post_would_pick_the_wrong_probe(self) -> None:
        # Negative control: if someone drops the date filter, the pre pile on
        # P15 makes it look covered and the picker sends the session at P02.
        pre = [obs(P15, f"2026-08-2{i:01d}T00:00:00Z") for i in range(10)]
        post = [obs(P02, "2026-09-01T00:00:00Z")]
        pooled = Counter(r.get("probe_id") for r in (pre + post) if r.get("arm") == "seeded")
        self.assertEqual(snp.pick_next(_probes(P02, P15), pooled)["probe_id"], P02)
        split = Counter(r.get("probe_id") for r in snp.post_intervention(pre + post))
        self.assertEqual(snp.pick_next(_probes(P02, P15), split)["probe_id"], P15)


class StatusCountsArePostIntervention(unittest.TestCase):
    """``--status`` is the operator surface §4.10 called a different quantity
    in a confusable format. A pre-intervention pile must not appear in the count."""

    def test_status_total_ignores_pre_intervention_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            rows = [
                obs(P15, "2026-08-20T00:00:00Z"),
                obs(P15, "2026-08-21T00:00:00Z"),
                obs(P19, "2026-09-01T00:00:00Z"),
            ]
            ledger.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            buf = io.StringIO()
            err = io.StringIO()
            with mock.patch.object(snp, "LEDGER", ledger), mock.patch.object(sys, "argv", [str(SCRIPT), "--status"]):
                with redirect_stdout(buf), redirect_stderr(err):
                    rc = snp.main()
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("total post-intervention seeded runs: 1", out)
            # P15's two pre rows must print as 0, not 2.
            self.assertRegex(out, rf"\n\s+0\s+{P15}\n")
            self.assertRegex(out, rf"\n\s+1\s+{P19}\n")


class BarePrefixProbeIdIsRejected(unittest.TestCase):
    """Consensus §4.10: ``--probe-id P19`` is not a probe. Prefix match would
    silently dispatch P19-port-check-fail-opens (or fail later at record time)."""

    def test_bare_p19_is_rejected_not_prefix_matched(self) -> None:
        r = subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--probe-id", "P19"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout.strip(), "")
        self.assertIn("no such probe: P19", r.stderr)
        self.assertNotIn("P19-port-check-fail-opens", r.stdout)


if __name__ == "__main__":
    unittest.main()
