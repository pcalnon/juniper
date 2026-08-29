"""Generate the API primer's worked-example sections from the verified example sources.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-13
Status: ad-hoc -- one-off (document build)
Retire when: RETAINED (owner policy 2026-08-25 — no retirement deadline). Previously: the primer is assembled and merged.
Related: notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md

The three capstone examples are developed and tested as real files, then embedded into the
document. Embedding them by hand would mean the document and the tested source could diverge
the first time either is edited, so the embedding is generated: this script reads the *actual*
files that pytest ran and wraps each in a fenced block carrying the ``example-file`` marker that
``2026-08-13_run_primer_examples.py`` extracts.

The round trip is therefore closed. Sources are tested, this script embeds the tested bytes, and
the runner extracts them back out of the document and re-tests them.

Usage::

    python util/ad-hoc/2026-08-13_gen_primer_examples.py --examples DIR --out DIR
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Per-part example sections: output fragment, heading, prose intro, and the source files to embed.
SECTIONS: list[dict[str, object]] = [
    {
        "out": "part1-example.md",
        "heading": "### I.12 Part I Worked Example — Making a Non-Idempotent POST Safe to Retry",
        "intro": """This example implements the idea at the centre of Part I: a client cannot tell a lost request from a lost response, so a `POST` that starts real work must be made replay-safe before it is safe to retry.

It is drawn directly from a live defect in this ecosystem. `juniper-cascor-client` retries `POST /v1/training/start` on transient 5xx (`juniper_cascor_client/constants.py:37`) with no idempotency key, so a dropped response can start a second training run on the same GPU. Its sibling `juniper-data-client` carries the fix and cites the specification for it (`juniper_data_client/constants.py:59-67`). This is what the corrected design looks like on both sides of the wire.

Three things are worth watching as you read it:

1. **The key is chosen by the client and reused across retries.** A server-generated key would be useless — the client needs it *before* it knows whether the first attempt survived.
2. **The stored record includes a fingerprint of the request.** Replaying a key with a different body is a client bug, and the server says so (422) rather than silently returning the wrong resource.
3. **The concurrent case is handled explicitly.** Two in-flight requests with one key is the interesting race, and the example reserves the key atomically before doing any work, so the loser gets a 409 rather than a second job.

The `_simulate_dispatch` helper deserves a note: real work always yields to the event loop, and without a yield the handler would be effectively atomic, making the 409 path unreachable in a test and misrepresenting production. The optional gate is a deliberate, documented test seam.""",
        "files": ["idempotent_jobs.py", "test_idempotent_jobs.py"],
    },
    {
        "out": "part2-example.md",
        "heading": "### II.11 Part II Worked Example — Conditional Requests and Optimistic Concurrency",
        "intro": """This example builds the HTTP semantics of Part II into one small service: content-addressed identifiers, strong `ETag`s, conditional `GET` returning 304, optimistic concurrency with `If-Match` and 412, `428 Precondition Required` for writes that omit the precondition, keyset pagination with a `Link` header, and RFC 9457 `application/problem+json` for every error.

The motivation is again a real gap. `juniper-data` already computes a SHA-256 over every artifact and stores it on the metadata record (`juniper_data/core/artifacts.py:50-63`), and its dataset identifiers are already content-addressed (`juniper_data/core/dataset_id.py:23-61`) — so its artifacts are the strongest possible candidate for `ETag` plus `Cache-Control: immutable`. It emits neither, and supports no conditional requests at all. The validator it needs is already sitting in the codebase.

The headline test is `test_lost_update_is_prevented_by_if_match`. It spells out the interleaving explicitly, because the lost-update problem is easy to nod along to and hard to actually picture:

```text
A: GET   -> tags=["baseline"], ETag=E0
B: GET   -> tags=["baseline"], ETag=E0     (B now holds a snapshot of E0)
A: PATCH If-Match: E0 -> 200, ETag=E1
B: PATCH If-Match: E0 -> 412               (B's view is stale)
*: GET   -> A's write survived
```

Without the precondition, B's write succeeds and silently erases A's change: no error, no log line, and no way for A to discover it. That silence is what makes lost updates expensive to diagnose in production.

One deliberate divergence from the real service: this example returns **200** when a content-addressed dataset already exists, reserving **201** for genuine creation. `juniper-data` returns 201 either way (`juniper_data/api/routes/datasets.py:71`), so a client cannot tell whether it created anything.""",
        "files": ["conditional_datasets.py", "test_conditional_datasets.py"],
    },
    {
        "out": "part3-example.md",
        "heading": "### III.9 Part III Worked Example — A Client Library That Does Not Lose Information",
        "intro": """This example is the corrected version of the design defects Part III identified in the three real Juniper client libraries. Each correction is a direct response to something observable in the shipped code.

| Defect in the real clients | Correction here |
|---|---|
| Exceptions carry only a formatted string — no `.status_code`, no `.response` — so callers cannot branch without parsing text | Every HTTP-derived error preserves `status_code`, the parsed problem-details `payload`, and the `request_id` as real attributes |
| One client retries `POST`, `PATCH`, and `DELETE` on transient 5xx with no idempotency key | Non-idempotent methods are retried **only** when an idempotency key is supplied |
| A single scalar timeout covers connect, read, write, and pool | Timeouts are separated, with per-call override |
| `create_network(**kwargs: Any)` types nothing and forwards blind | Public methods are keyword-only with `Literal` types for closed enums |
| Retry exhaustion collapses a typed 503 into the base exception, losing the status | The final response is mapped before raising, so the typed error survives exhaustion |
| No jitter on backoff | Full jitter, with `Retry-After` honoured when the server supplies it |

The instrumentation hook is worth studying as a small ergonomics lesson: it defaults to a **named no-op function** rather than `None`, so the call site has no branch; it fires in a `finally` so failures are observed as well as successes; and its own exceptions are swallowed with an explicit comment, because instrumentation that can break the caller is worse than no instrumentation.

The exception hierarchy is deliberately flat — one base plus typed leaves — matching the shape the real clients already use. The improvement is not the shape; it is that the objects carry their information.""",
        "files": ["wellformed_client.py", "test_wellformed_client.py"],
    },
]

FOOTER = """Run this example, and the other two, with the harness described in [Appendix D](#appendix-d--running-the-examples)."""


def render(section: dict[str, object], examples: Path) -> str:
    parts: list[str] = [str(section["heading"]), "", str(section["intro"]), ""]
    for name in section["files"]:  # type: ignore[union-attr]
        src = examples / str(name)
        if not src.is_file():
            print(f"ERROR: missing example source: {src}", file=sys.stderr)
            raise SystemExit(2)
        body = src.read_text(encoding="utf-8").rstrip("\n")
        if "```" in body:
            # A fence inside the source would terminate the block early and silently truncate
            # the embedded file -- refuse rather than emit a corrupted document.
            print(f"ERROR: {name} contains a code fence; cannot embed safely.", file=sys.stderr)
            raise SystemExit(2)
        parts += [f"<!-- example-file: {name} -->", "```python", body, "```", ""]
    parts.append(FOOTER)
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the primer's worked-example fragments.")
    parser.add_argument("--examples", required=True, type=Path, help="Directory holding the tested example sources.")
    parser.add_argument("--out", required=True, type=Path, help="Fragments directory to write into.")
    args = parser.parse_args(argv)

    if not args.examples.is_dir() or not args.out.is_dir():
        print("ERROR: --examples and --out must both be existing directories.", file=sys.stderr)
        return 2

    for section in SECTIONS:
        text = render(section, args.examples)
        dest = args.out / str(section["out"])
        dest.write_text(text, encoding="utf-8")
        print(f"Wrote {dest.name} ({len(text.splitlines())} lines, {len(section['files'])} embedded files)")  # type: ignore[arg-type]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
