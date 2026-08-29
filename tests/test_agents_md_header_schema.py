"""Lint test: ``AGENTS.md`` header schema.

Catches drift where ``AGENTS.md``'s canonical header bullet block
is missing fields, has fields in the wrong relative order, or has
empty values. This is the *schema* test; the version-equality
check (``**Version**:`` matches ``pyproject.toml``) lives in
``test_agents_md_version_drift.py``.

Canonical schema (required fields, in this relative order):

    **Project**: <descriptive name>
    **Repository**: <github-org>/<repo-name>
    **Author**: <name>
    **License**: <license string>
    **Version**: <X.Y.Z>
    **Last Updated**: <YYYY-MM-DD>

Additional fields (e.g. ``**Python**:``) may appear and may be
interleaved freely; the lint only enforces that the six required
fields are *all present* and *in canonical relative order*.

The ``Last Updated`` field is auto-bumped on every PR push by the
``.github/workflows/agents-md-touch-up.yml`` workflow; this test
only validates *format* (ISO 8601 date), not currency.

The test is intentionally portable: it auto-locates the repo root
by walking up from this file looking for an ``AGENTS.md`` sibling
to ``.github/``, so the same module drops into any Juniper repo's
``tests/`` or ``util/`` directory without per-repo edits.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import ClassVar


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "AGENTS.md").is_file() and (parent / ".github").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (AGENTS.md + .github/) from {here}")


_REPO = _repo_root()
_AGENTS_MD = _REPO / "AGENTS.md"

# Required fields, in canonical relative order. Extra fields are
# permitted anywhere and are not validated.
_REQUIRED_FIELDS: tuple[str, ...] = (
    "Project",
    "Repository",
    "Author",
    "License",
    "Version",
    "Last Updated",
)

# Matches a bold-field-then-colon bullet anywhere in the header:
#   **Field Name**: value
_BULLET_RE = re.compile(r"^\*\*(?P<field>[^*]+)\*\*:\s*(?P<value>.+?)\s*$", re.MULTILINE)

# ISO 8601 calendar date format YYYY-MM-DD.
_ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


def _extract_header_bullets(text: str) -> list[tuple[str, str]]:
    """Extract the ordered list of (field, value) pairs from the
    AGENTS.md header. The header is everything before the first
    ``---`` horizontal rule or ``## `` H2 section, whichever comes
    first.
    """
    lines = text.splitlines()
    header_end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "---" or line.startswith("## "):
            header_end = i
            break
    header = "\n".join(lines[:header_end])
    return [(m.group("field"), m.group("value")) for m in _BULLET_RE.finditer(header)]


class AgentsMdHeaderSchemaTest(unittest.TestCase):
    """Pin AGENTS.md header to the canonical schema."""

    bullets: ClassVar[list[tuple[str, str]]]

    @classmethod
    def setUpClass(cls) -> None:
        text = _AGENTS_MD.read_text(encoding="utf-8")
        cls.bullets = _extract_header_bullets(text)

    def test_all_required_fields_present(self) -> None:
        present = {field for field, _ in self.bullets}
        missing = [f for f in _REQUIRED_FIELDS if f not in present]
        self.assertEqual(
            missing,
            [],
            (f"AGENTS.md header is missing required field(s): {missing}. " f"Schema requires (in order): {list(_REQUIRED_FIELDS)}"),
        )

    def test_required_fields_appear_in_canonical_order(self) -> None:
        """Filtering out extras, the required fields must appear in
        the canonical relative order. Extras (e.g. ``**Python**:``)
        may be interleaved freely."""
        present_required = [field for field, _ in self.bullets if field in _REQUIRED_FIELDS]
        self.assertEqual(
            present_required,
            list(_REQUIRED_FIELDS),
            (f"AGENTS.md required fields are not in canonical relative " f"order. Got: {present_required}. " f"Expected: {list(_REQUIRED_FIELDS)}."),
        )

    def test_required_field_values_non_empty(self) -> None:
        for field, value in self.bullets:
            if field in _REQUIRED_FIELDS:
                with self.subTest(field=field):
                    self.assertTrue(
                        value.strip(),
                        f"AGENTS.md `**{field}**:` has an empty value.",
                    )

    def test_last_updated_is_iso_date(self) -> None:
        last_updated = next((v for f, v in self.bullets if f == "Last Updated"), None)
        if last_updated is None:
            self.skipTest("`**Last Updated**:` is absent (covered by earlier test)")
        self.assertRegex(
            last_updated,
            _ISO_DATE_PATTERN,
            (f"AGENTS.md `**Last Updated**: {last_updated!r}` is not in " f"`YYYY-MM-DD` format."),
        )


if __name__ == "__main__":
    unittest.main()
