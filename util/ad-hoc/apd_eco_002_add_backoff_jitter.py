#!/usr/bin/env python3
"""Add urllib3 ``backoff_jitter`` to the shared ``Retry`` policy in a Juniper client worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-26
Status: ad-hoc -- migration (the APD-ECO-002 close across the three client repos)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-ECO-002), the three client fix PRs named in its §5.1 row

``APD-ECO-002``: none of the three clients passes ``backoff_jitter`` to ``urllib3``'s ``Retry``,
so every client that trips the same transient outage retries on the *same* schedule -- a
synchronised retry storm against a service that is already failing.

urllib3 applies jitter as an ABSOLUTE additive term, not a proportional one::

    backoff_value = backoff_factor * (2 ** (consecutive_errors - 1))
    if backoff_jitter != 0.0:
        backoff_value += random.random() * backoff_jitter

so the value is chosen to match ``DEFAULT_BACKOFF_FACTOR`` (0.5 in all three repos): that spreads
callers across a 0.5 s window on the first retry, which is the 1.0 s step where a herd hurts most.

``backoff_jitter`` was added in **urllib3 2.0.0** (changelog 2.0.0, 2023-04-26, upstream #2952) and
all three clients already pin ``urllib3>=2.0.0``, so no dependency floor moves.

The edit is idempotent: re-running it on an already-patched tree makes no change and reports
``already patched``. Every insertion is anchored on an exact line, and the script refuses (raises)
rather than guessing if an anchor is missing or ambiguous.

    python3 util/ad-hoc/apd_eco_002_add_backoff_jitter.py <client-worktree> [...]
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

JITTER_VALUE = "0.5"

CONSTANT_BLOCK = """# APD-ECO-002: urllib3 applies this as an ABSOLUTE additive term --
# ``backoff_value += random.random() * backoff_jitter`` -- not a proportional
# one. Without it every client that trips the same transient outage retries on
# an identical schedule, so a service that is already failing is hit by a
# synchronised herd. Matched to DEFAULT_BACKOFF_FACTOR so the spread is a full
# window on the first retry, which is the step that carries the most callers.
DEFAULT_BACKOFF_JITTER: float = {value}
"""

RETRY_KWARG = """            # APD-ECO-002: decorrelate retry schedules across client instances.
            backoff_jitter=DEFAULT_BACKOFF_JITTER,
"""


@dataclass(frozen=True)
class Target:
    """One client package inside a worktree."""

    constants: Path
    client: Path

    @property
    def label(self) -> str:
        return self.constants.parent.name


def discover(worktree: Path) -> Target:
    """Locate the single ``juniper_*_client`` package under ``worktree``."""
    matches = sorted(worktree.glob("**/juniper_*_client/constants.py"))
    matches = [m for m in matches if "test" not in m.parts]
    if len(matches) != 1:
        raise SystemExit(f"{worktree}: expected exactly one client package, found {len(matches)}: {matches}")
    constants = matches[0]
    client = constants.parent / "client.py"
    if not client.is_file():
        raise SystemExit(f"{worktree}: no client.py beside {constants}")
    return Target(constants=constants, client=client)


def _insert_after(text: str, anchor: str, addition: str, *, what: str, path: Path) -> str:
    """Insert ``addition`` immediately after the unique line ``anchor``."""
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f"{path}: anchor for {what} appears {count} times, expected 1: {anchor!r}")
    return text.replace(anchor, anchor + addition, 1)


def patch_constants(target: Target) -> bool:
    """Declare ``DEFAULT_BACKOFF_JITTER`` and export it if the module has an ``__all__``."""
    text = original = target.constants.read_text()
    if "DEFAULT_BACKOFF_JITTER" in text:
        return False

    factor = "DEFAULT_BACKOFF_FACTOR: float = 0.5\n"
    text = _insert_after(
        text,
        factor,
        CONSTANT_BLOCK.format(value=JITTER_VALUE),
        what="the constant declaration",
        path=target.constants,
    )

    export = '    "DEFAULT_BACKOFF_FACTOR",\n'
    if export in text:
        text = _insert_after(
            text,
            export,
            '    "DEFAULT_BACKOFF_JITTER",\n',
            what="the __all__ export",
            path=target.constants,
        )

    target.constants.write_text(text)
    return text != original


def patch_client(target: Target) -> bool:
    """Import the new constant and pass it to the ``Retry`` construction."""
    text = original = target.client.read_text()
    if "DEFAULT_BACKOFF_JITTER" in text:
        return False

    text = _insert_after(
        text,
        "    DEFAULT_BACKOFF_FACTOR,\n",
        "    DEFAULT_BACKOFF_JITTER,\n",
        what="the constants import",
        path=target.client,
    )

    # Anchor inside the Retry(...) call, never on the __init__ signature default
    # (``backoff_factor: float = DEFAULT_BACKOFF_FACTOR`` carries an annotation).
    start = text.find("retry_strategy = Retry(")
    if start == -1:
        raise SystemExit(f"{target.client}: no 'retry_strategy = Retry(' call found")
    head, tail = text[:start], text[start:]

    for anchor in ("            backoff_factor=self.backoff_factor,\n", "            backoff_factor=backoff_factor,\n"):
        if tail.count(anchor) == 1:
            tail = tail.replace(anchor, anchor + RETRY_KWARG, 1)
            break
    else:
        raise SystemExit(f"{target.client}: no unique backoff_factor kwarg inside the Retry(...) call")

    text = head + tail
    target.client.write_text(text)
    return text != original


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    for raw in argv:
        worktree = Path(raw).resolve()
        if not worktree.is_dir():
            raise SystemExit(f"not a directory: {worktree}")
        target = discover(worktree)
        changed_constants = patch_constants(target)
        changed_client = patch_client(target)
        state = "patched" if (changed_constants or changed_client) else "already patched"
        print(f"{target.label:26s} {state}  ({target.constants.name}={changed_constants}, {target.client.name}={changed_client})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
