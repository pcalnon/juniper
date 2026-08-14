"""Extract the API primer's code examples from the document and run their tests.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-13
Status: ad-hoc -- investigation (documentation verification)
Retire when: the primer's examples are moved into a real test suite, or the primer is retired.
Related: notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md

The primer claims its examples are "fully functional". Documentation code rots faster than
anything else in a repository precisely because nothing executes it, so this script closes the
loop: it extracts the fenced blocks *from the document itself* -- not from a parallel copy that
can silently drift -- writes them to a scratch directory, and runs pytest over them.

Extraction convention: a fenced block is exported when the line immediately preceding the
opening fence is an HTML comment of the form::

    <!-- example-file: idempotent_jobs.py -->
    ```python
    ...
    ```

The comment is invisible in rendered markdown, so the document reads normally while remaining
machine-extractable. Blocks without the marker (illustrative snippets) are ignored.

Usage::

    python util/ad-hoc/2026-08-13_run_primer_examples.py [--doc PATH] [--python PYTHON] [--keep]
    python util/ad-hoc/2026-08-13_run_primer_examples.py --list

Exit codes: 0 all tests passed / 1 tests failed / 2 misuse or extraction failure.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_DOC = Path("notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")

# Third-party packages the examples import. Kept here rather than in a requirements file so the
# script stays self-describing; versions are floors, and the primer pins the exact versions it
# was verified against in its own Appendix D.
REQUIREMENTS = ["fastapi>=0.115", "httpx>=0.28", "pydantic>=2.9", "pytest>=8.0", "pytest-asyncio>=0.24"]

_MARKER_RE = re.compile(r"^<!--\s*example-file:\s*(?P<name>[A-Za-z0-9_.\-/]+)\s*-->\s*$")


class ExtractionError(RuntimeError):
    """Raised when the document's example blocks are malformed."""


def extract(doc_text: str) -> dict[str, str]:
    """Return ``{filename: source}`` for every marked fenced block in the document."""
    files: dict[str, str] = {}
    lines = doc_text.splitlines()
    i = 0
    in_fence = False
    fence = "```"
    while i < len(lines):
        stripped = lines[i].strip()

        # Markers inside a fenced block are documentation *about* the convention, not uses of
        # it -- Appendix D shows the marker syntax in a code block. Scanning without tracking
        # fence state turns that illustration into a duplicate-marker error.
        if in_fence:
            if stripped.startswith(fence):
                in_fence = False
            i += 1
            continue

        match = _MARKER_RE.match(stripped)
        if not match:
            if stripped.startswith("```"):
                in_fence = True
                fence = stripped[:3]
            i += 1
            continue

        name = match.group("name")
        # The marker must be immediately followed by an opening fence; anything else means the
        # document was edited in a way that silently orphans the marker.
        if i + 1 >= len(lines) or not lines[i + 1].lstrip().startswith("```"):
            raise ExtractionError(f"marker for {name!r} on line {i + 1} is not followed by a code fence")

        fence = lines[i + 1].strip()[:3]
        body: list[str] = []
        j = i + 2
        while j < len(lines) and lines[j].strip() != fence:
            body.append(lines[j])
            j += 1
        if j >= len(lines):
            raise ExtractionError(f"unterminated code fence for {name!r} starting at line {i + 2}")

        if name in files:
            raise ExtractionError(f"duplicate example-file marker: {name!r}")
        files[name] = "\n".join(body).rstrip() + "\n"
        i = j + 1

    if not files:
        raise ExtractionError("no example-file markers found -- has the extraction convention changed?")
    return files


def build_env(workdir: Path, python: str) -> Path:
    """Create a virtualenv in ``workdir`` and install the example requirements."""
    venv = workdir / ".venv"
    subprocess.run([python, "-m", "venv", str(venv)], check=True, capture_output=True)
    py = venv / "bin" / "python"
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"], check=True, capture_output=True)
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", *REQUIREMENTS], check=True, capture_output=True)
    return py


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract and run the API primer's code examples.")
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC, help="Path to the primer markdown.")
    parser.add_argument("--python", default=sys.executable, help="Interpreter used to build the scratch venv.")
    parser.add_argument("--venv", type=Path, help="Reuse an existing venv instead of building one.")
    parser.add_argument("--keep", action="store_true", help="Keep the scratch directory and print its path.")
    parser.add_argument("--list", action="store_true", help="List extracted example files and exit.")
    args = parser.parse_args(argv)

    if not args.doc.is_file():
        print(f"ERROR: document not found: {args.doc}", file=sys.stderr)
        return 2

    try:
        files = extract(args.doc.read_text(encoding="utf-8"))
    except ExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for name, src in sorted(files.items()):
            print(f"{name:32s} {len(src.splitlines()):5d} lines")
        return 0

    workdir = Path(tempfile.mkdtemp(prefix="juniper-api-primer-examples-"))
    try:
        for name, src in files.items():
            target = workdir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(src, encoding="utf-8")
        print(f"Extracted {len(files)} file(s) to {workdir}")

        if args.venv:
            py = args.venv / "bin" / "python"
            if not py.is_file():
                print(f"ERROR: no interpreter at {py}", file=sys.stderr)
                return 2
        else:
            print("Building scratch virtualenv (this takes a moment)...")
            py = build_env(workdir, args.python)

        proc = subprocess.run([str(py), "-m", "pytest", "-q", str(workdir)], cwd=workdir)
        if proc.returncode == 0:
            print("\nAll primer examples passed.")
        else:
            print(f"\nExamples FAILED (pytest exit {proc.returncode}).", file=sys.stderr)
        return 0 if proc.returncode == 0 else 1
    finally:
        if args.keep:
            print(f"Kept scratch directory: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
