#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

Pin ``util/ad-hoc/2026-08-19_p3_relocate_section.py``'s section extraction against fenced code.

Failure class this pins
-----------------------
``heading_level`` cannot tell a markdown heading from a shell comment -- both are ``# text`` at
column 0. Until 2026-08-28 ``extract`` was fence-blind, so the FIRST ``# comment`` inside a code
block ended the section: level 1 is ``<= 2``, so a ``##`` section stopped there.

Measured against juniper-canopy's ``AGENTS.md`` (136 such lines) before the fix: 8 of 11 candidate
sections truncated -- ``## Quick Start Commands`` extracted **62 of 10,009 chars**, ``## Code Style
Guidelines`` 314 of 4,580, ``## Archive Procedures`` 185 of 3,720.

**And it would not have raised.** The relocation would succeed, the unmoved remainder would sit
orphaned under a "Moved to ..." pointer, and G3 (``util/relocation_check.py``) would still PASS --
every line it *did* remove does appear in the destination; G3 has no way to notice the lines it did
not remove. That is the whole gate chain reporting success over mangled content, so this file is the
only thing standing between a fence-blind regression and a silent bad cut.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-19_p3_relocate_section.py"


def _load():
    spec = importlib.util.spec_from_file_location("p3_relocate_section", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FenceMaskTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_plain_fence_marks_interior_only(self):
        lines = ["a\n", "```bash\n", "# not a heading\n", "```\n", "b\n"]
        self.assertEqual(self.mod.fence_mask(lines), [False, False, True, False, False])

    def test_four_backtick_fence_swallows_inner_three(self):
        """The canopy case: a ````-fence wrapping ```-examples must not flip parity."""
        lines = ["````markdown\n", "```bash\n", "# inner\n", "```\n", "````\n", "after\n"]
        mask = self.mod.fence_mask(lines)
        self.assertTrue(all(mask[1:4]), f"inner fence content not masked: {mask}")
        self.assertFalse(mask[5], "content after the outer fence is still masked")

    def test_closing_fence_needs_no_info_string(self):
        """```bash cannot CLOSE a ```-block; it is content inside it."""
        lines = ["```\n", "```bash\n", "x\n", "```\n", "out\n"]
        mask = self.mod.fence_mask(lines)
        self.assertTrue(mask[1], "an info-string fence wrongly closed the block")
        self.assertFalse(mask[4], "block failed to close on the bare fence")

    def test_unclosed_fence_runs_to_eof(self):
        lines = ["```\n", "a\n", "b\n"]
        self.assertEqual(self.mod.fence_mask(lines), [False, True, True])


class ExtractTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_shell_comment_in_fence_does_not_end_the_section(self):
        """The exact canopy failure: `# Run all tests` scored level 1 and ended a `##` section."""
        lines = [
            "## Quick Start\n",
            "\n",
            "```bash\n",
            "# Run all tests\n",
            "pytest\n",
            "# Run with coverage\n",
            "pytest --cov\n",
            "```\n",
            "\n",
            "trailing prose that belongs to the section\n",
            "\n",
            "## Next Section\n",
            "other\n",
        ]
        start, end = self.mod.extract(lines, "## Quick Start")
        self.assertEqual(start, 0)
        self.assertEqual(end, 11, "extraction stopped early -- fenced `#` treated as a heading")
        body = "".join(lines[start:end])
        self.assertIn("trailing prose", body)
        self.assertIn("pytest --cov", body)

    def test_real_heading_still_ends_the_section(self):
        lines = ["## A\n", "body\n", "## B\n", "other\n"]
        self.assertEqual(self.mod.extract(lines, "## A"), (0, 2))

    def test_shallower_real_heading_ends_the_section(self):
        lines = ["## A\n", "body\n", "# Top\n", "other\n"]
        self.assertEqual(self.mod.extract(lines, "## A"), (0, 2))

    def test_deeper_heading_does_not_end_the_section(self):
        lines = ["## A\n", "### sub\n", "body\n", "## B\n"]
        self.assertEqual(self.mod.extract(lines, "## A"), (0, 3))

    def test_section_runs_to_eof_when_last(self):
        lines = ["## A\n", "body\n", "more\n"]
        self.assertEqual(self.mod.extract(lines, "## A"), (0, 3))

    def test_heading_inside_a_fence_is_not_a_match(self):
        """A `## X` shown as a markdown EXAMPLE must not be mistaken for the real section."""
        lines = [
            "## Docs\n",
            "```markdown\n",
            "## Target\n",
            "```\n",
            "## Target\n",
            "real body\n",
        ]
        start, end = self.mod.extract(lines, "## Target")
        self.assertEqual(start, 4, "matched the fenced example instead of the real heading")
        self.assertEqual(end, 6)

    def test_ambiguous_heading_refuses(self):
        lines = ["## A\n", "x\n", "## A\n", "y\n"]
        with self.assertRaises(SystemExit):
            self.mod.extract(lines, "## A")

    def test_missing_heading_refuses(self):
        with self.assertRaises(SystemExit):
            self.mod.extract(["## A\n"], "## Nope")


if __name__ == "__main__":
    unittest.main(verbosity=2)
