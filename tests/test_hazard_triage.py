#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

Pin ``util/ad-hoc/2026-08-28_hazard_triage.py`` -- the pre-cut HAZARD FINDER.

Failure class this pins
-----------------------
A census that can certify a vacuous or partial result as complete. The first
version of this tool scored per LINE and found ZERO candidates in juniper-ml's
own ``AGENTS.md``, which has a Hazards section with four bullets. Wrapped
prose ("Do not set it" / "silently diverges") never reaches two signals on a
single line, so the finder reported a clean file over real hazards.

That is the same class as an X7 offload census that certified 36 sites where
58 is true: the instrument that is supposed to be the test can hide the
remainder and still print success. ``util/`` is outside every pre-commit
Python hook, so this suite is the gate.

Hermetic: scores in-memory markdown. ``blob()`` / ``gh api`` are never called.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-28_hazard_triage.py"
AGENTS = REPO_ROOT / "AGENTS.md"


def _load():
    spec = importlib.util.spec_from_file_location("hazard_triage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


# The documented positive-control miss: two signals on DIFFERENT lines of one bullet.
_WRAPPED = """\
## Hazards (resident -- do not relocate)

- **`FLAG=1` is opt-in.** Default `0` in the helper documented here.
  Do not set it to "be thorough".
  That choice silently diverges the service from the CLI.

## Later

Some other section.
"""

_FENCED_FALSE_POSITIVE = """\
## Quick Start

Here is the recovery idiom:

```python
try:
    risky()
except Exception:
    # silently swallow -- HAZARD: looks like success
    pass
```

Nothing after the fence.
"""


class FenceMaskTest(unittest.TestCase):
    def test_plain_fence_marks_interior_only(self):
        lines = ["a", "```bash", "# not a heading", "```", "b"]
        self.assertEqual(mod.fence_mask(lines), [False, False, True, False, False])

    def test_four_backtick_fence_swallows_inner_three(self):
        """A ````-fence wrapping ```-examples must not flip parity (the canopy case)."""
        lines = ["````markdown", "```bash", "# inner", "```", "````", "after"]
        mask = mod.fence_mask(lines)
        self.assertTrue(all(mask[1:4]), f"inner fence content not masked: {mask}")
        self.assertFalse(mask[5], "content after the outer fence is still masked")

    def test_closing_fence_needs_no_info_string(self):
        """```bash cannot CLOSE a ```-block; it is content inside it."""
        lines = ["```", "```bash", "x", "```", "out"]
        mask = mod.fence_mask(lines)
        self.assertTrue(mask[1], "an info-string fence wrongly closed the block")
        self.assertFalse(mask[4], "block failed to close on the bare fence")


class CollectCandidatesTest(unittest.TestCase):
    def test_wrapped_prose_is_one_block_and_scores(self):
        """The exact first-version miss: two signals, two lines, one bullet."""
        found = mod.collect_candidates(_WRAPPED, min_score=2)
        self.assertTrue(found, "block scoring found no candidate in the wrapped-prose fixture")
        scores, _starts, sections, texts, hits_list = zip(*found)
        self.assertGreaterEqual(max(scores), 2)
        self.assertTrue(any("Hazards" in sec for sec in sections))
        joined = " ".join(texts)
        self.assertIn("Do not set it", joined)
        self.assertIn("silently", joined)
        self.assertIn("prohibition", hits_list[0])
        self.assertIn("silent-failure", hits_list[0])

    def test_per_line_scoring_misses_the_same_fixture(self):
        """A line-wise scorer at min_score=2 is the vacuous-pass this file exists to prevent."""
        lines = [ln for ln in _WRAPPED.splitlines() if ln.strip() and not ln.startswith("#")]
        line_hits = [mod.score(ln)[0] for ln in lines]
        self.assertTrue(all(n < 2 for n in line_hits), f"a line already scores 2; fixture is not the documented miss: {list(zip(lines, line_hits))}")
        self.assertTrue(mod.collect_candidates(_WRAPPED, min_score=2))

    def test_fenced_code_is_not_scored(self):
        """A try/except sample must not spend reviewer judgement on its own comments."""
        found = mod.collect_candidates(_FENCED_FALSE_POSITIVE, min_score=2)
        self.assertEqual(found, [], f"fenced comments leaked as candidates: {found}")

    def test_short_blocks_are_skipped(self):
        short = "- NEVER silently delete this.\n"
        self.assertLess(len(short.strip()), 40)
        self.assertGreaterEqual(mod.score(short)[0], 2)
        self.assertEqual(mod.collect_candidates(short, min_score=2), [])

    def test_min_score_threshold(self):
        # One signal only: "silently" (no prohibition / irreversible / hazard-noun).
        one = "- This paragraph is long enough to be scored and it silently does nothing else of note.\n"
        self.assertEqual(mod.score(one)[0], 1)
        self.assertEqual(mod.collect_candidates(one, min_score=2), [])
        found = mod.collect_candidates(one, min_score=1)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][4], ["silent-failure"])

    def test_has_hazards_section(self):
        self.assertTrue(mod.has_hazards_section(_WRAPPED))
        self.assertFalse(mod.has_hazards_section(_FENCED_FALSE_POSITIVE))
        self.assertTrue(mod.has_hazards_section(AGENTS.read_text(encoding="utf-8")))


class PositiveControlTest(unittest.TestCase):
    def test_agents_md_is_not_vacuous(self):
        """juniper-ml's own Hazards block must produce candidates. The first version scored 0 of 4."""
        text = AGENTS.read_text(encoding="utf-8")
        self.assertTrue(mod.has_hazards_section(text))
        found = mod.collect_candidates(text, min_score=2)
        hazard_hits = [row for row in found if "Hazards" in row[2]]
        self.assertGreaterEqual(
            len(hazard_hits),
            3,
            f"Hazards section produced {len(hazard_hits)} candidates (need >= 3); " "a regression to per-line scoring reprints the documented 0-of-4 vacuous pass",
        )
        blob = " ".join(row[3] for row in hazard_hits)
        self.assertIn("KILL_WORKERS", blob)
        self.assertIn("max_epochs", blob)
        self.assertRegex(blob, r"unmergeable|CI-skip|Never put that marker")


if __name__ == "__main__":
    unittest.main()
