#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/soak_next_probe.py``. ``util/`` is outside every pre-commit
Python hook's scope, so this suite is the only check on it.

What it pins, and why it matters more than it looks
---------------------------------------------------
The soak protocol's second requirement is that a probe reaches an UNPRIMED
session: it must never see the fact, the pointer or the discriminator before
answering (ledger §7; priming is what invalidated option A in §11 D2). A primed
run cannot be un-primed afterwards, and nothing downstream can detect it -- the
run just looks like a follow.

So the load-bearing property is a NEGATIVE one: stdout must carry the task and
NOTHING else. That is not visible by reading the output (a leak looks like extra
helpful context), which is exactly the kind of property that needs a test rather
than a careful author.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_next_probe.py"
PROBES = REPO_ROOT / "conf" / "soak_probes.json"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def probes() -> list[dict]:
    return json.loads(PROBES.read_text(encoding="utf-8"))["probes"]


class StdoutCarriesOnlyTheTask(unittest.TestCase):
    """The unprimed guarantee. A leak here silently contaminates every run."""

    def test_default_stdout_is_exactly_one_probe_task(self) -> None:
        out = run().stdout.strip()
        self.assertTrue(out)
        tasks = {p["task"].strip() for p in probes()}
        self.assertIn(out, tasks)

    def test_stdout_never_contains_a_fact_pointer_or_discriminator(self) -> None:
        out = run().stdout
        for p in probes():
            for field in ("fact", "pointer", "evidence", "discriminator"):
                val = p.get(field)
                if isinstance(val, str) and val.strip():
                    self.assertNotIn(val.strip(), out, f"{field} of {p['probe_id']} leaked to stdout")

    def test_stdout_never_names_the_soak_or_the_probe_id(self) -> None:
        out = run().stdout.lower()
        for word in ("soak", "probe", "pointer-follow", "ledger", "rung"):
            self.assertNotIn(word, out, f"{word!r} leaked to stdout and primes the session")
        for p in probes():
            self.assertNotIn(p["probe_id"].lower(), out)

    def test_metadata_goes_to_stderr_so_a_redirect_stays_clean(self) -> None:
        r = run()
        self.assertIn("Paste ONLY the stdout", r.stderr)
        self.assertNotIn("Paste ONLY the stdout", r.stdout)


class RevealIsOptIn(unittest.TestCase):
    def test_reveal_shows_the_fact_and_the_discriminator(self) -> None:
        pid = probes()[0]["probe_id"]
        out = run("--reveal", "--probe-id", pid).stdout
        self.assertIn(probes()[0]["fact"], out)
        self.assertIn("discriminator", out)

    def test_reveal_does_not_print_a_pasteable_bare_task(self) -> None:
        # --reveal is for scoring. It must not double as a dispatch path, or an
        # operator could paste scoring output into a session and prime it.
        pid = probes()[0]["probe_id"]
        out = run("--reveal", "--probe-id", pid).stdout
        self.assertIn("probe_id", out)

    def test_status_prints_no_task_text(self) -> None:
        out = run("--status").stdout
        for p in probes():
            self.assertNotIn(p["task"].strip(), out)


class ProbeSelection(unittest.TestCase):
    def test_unknown_probe_id_is_rejected_not_silently_defaulted(self) -> None:
        r = run("--probe-id", "P99-does-not-exist")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout.strip(), "")

    def test_named_probe_is_honoured(self) -> None:
        p = probes()[3]
        self.assertEqual(run("--probe-id", p["probe_id"]).stdout.strip(), p["task"].strip())

    def test_status_lists_every_registered_probe(self) -> None:
        out = run("--status").stdout
        for p in probes():
            self.assertIn(p["probe_id"], out)


if __name__ == "__main__":
    unittest.main()
