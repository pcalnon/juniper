#!/usr/bin/env python3
"""Open the D6 ceiling-bump follow-on PRs for a released upstream, via the GitHub API only.

Project:     Juniper
Sub-Project: juniper-ml
Application: release-train D6 follow-on opener
Author:      Paul Calnon
License:     MIT License
Status:      ad-hoc (single-use for the juniper-service-core 0.6.0 release, 2026-08-29)

WHY THIS EXISTS
---------------
``util/release_train/propose.py --execute --cross-repo`` opens these follow-ons itself, but it does
so by **branching, editing and pushing the sibling's local checkout**. That is unsafe here:
``juniper-cascor``'s primary checkout is frozen -- a live ``uvicorn`` on :8202 imports from its
``src/`` -- so switching its working tree mid-release could disturb a running service. propose.py was
therefore run WITHOUT ``--cross-repo``, which skipped the three follow-ons with an explicit reason.

This opener touches **no local checkout at all**. Every read and write goes through the GitHub API,
so the file content edited is always the branch tip's own content rather than a possibly-stale
working copy -- which also sidesteps the whole-file-clobber class (a PR built from a behind-main copy
reverting concurrent changes).

Per plan S13/D6 each follow-on is a **separate standard-gated PR** in the consumer's own repo, never
folded into the upstream proposal.

Usage:
    python3 util/ad-hoc/2026-08-29_open_ceiling_bump_prs.py --dry-run
    python3 util/ad-hoc/2026-08-29_open_ceiling_bump_prs.py --execute
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

UPSTREAM = "juniper-service-core"
OLD_SPEC = "juniper-service-core>=0.5.0,<0.6.0"
NEW_SPEC = "juniper-service-core>=0.5.0,<0.7.0"
NEW_CEILING = "0.7.0"
UPSTREAM_VERSION = "0.6.0"
BRANCH = f"deps/{UPSTREAM}-ceiling-{NEW_CEILING}"

# (repo, path-to-pyproject-within-repo)
CONSUMERS = [
    ("juniper-cascor", "pyproject.toml"),
    ("juniper-data", "pyproject.toml"),
    ("juniper-recurrence", "juniper-recurrence/pyproject.toml"),  # monorepo: sub-package, not repo root
]

BODY = f"""## Summary

Raises this repo's `{UPSTREAM}` ceiling so it can receive **v{UPSTREAM_VERSION}**.

`{UPSTREAM}` v{UPSTREAM_VERSION} is a pre-1.0 **MINOR** bump (juniper-ml#1458). Under the fleet's
`>=floor,<next-minor` pinning policy (release-train plan S6) each `0.x` is a compatibility boundary,
so the new version **escapes** this repo's current `<0.6.0` ceiling and would never be installed here.

```
- "{OLD_SPEC}",
+ "{NEW_SPEC}",
```

**This PR raises ONLY the ceiling.** The floor and every other specifier are preserved byte-for-byte.

## Why it matters here

v{UPSTREAM_VERSION} carries the `Security` entry that removes `/docs`, `/openapi.json` and `/redoc`
from `EXEMPT_PATHS`, so the OpenAPI document is no longer served to unauthenticated callers
(juniper-ml#1434). Without this ceiling bump that fix cannot reach this repo.

## How this consumer was found

The release-train registry's `depends_on` for `{UPSTREAM}` named only two of its four consumers, so
the D6 propagation analysis originally generated a follow-on for `juniper-recurrence` alone —
`juniper-cascor` and `juniper-data` would have been silently stranded below the release. Fixed in
juniper-ml#1452, which also added the converse guard: the existing check verified that each
*declared* edge pointed at a known package, and so could not see a *missing* edge.

Opened per plan S13/D6 as a **separate standard-gated PR**, never folded into the upstream proposal.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016iu2WciSqYJ1ZoHLMMBt5N
"""


def gh(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def default_branch(repo: str) -> str:
    return gh("api", f"repos/pcalnon/{repo}", "--jq", ".default_branch")


def head_sha(repo: str, branch: str) -> str:
    return gh("api", f"repos/pcalnon/{repo}/git/ref/heads/{branch}", "--jq", ".object.sha")


def get_file(repo: str, path: str, ref: str) -> tuple[str, str]:
    """Return (decoded_text, blob_sha) read from the API -- never from a local checkout."""
    raw = gh("api", f"repos/pcalnon/{repo}/contents/{path}?ref={ref}")
    data = json.loads(raw)
    return base64.b64decode(data["content"]).decode("utf-8"), data["sha"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="actually create branches and open PRs")
    ap.add_argument("--dry-run", action="store_true", help="report only (default)")
    args = ap.parse_args()
    execute = args.execute and not args.dry_run

    print(f"D6 ceiling-bump follow-ons for {UPSTREAM} v{UPSTREAM_VERSION}")
    print(f"branch: {BRANCH}")
    print(f"mode:   {'EXECUTE' if execute else 'DRY-RUN (nothing is written)'}\n")

    failures = 0
    for repo, path in CONSUMERS:
        base = default_branch(repo)
        sha = head_sha(repo, base)
        text, blob_sha = get_file(repo, path, base)

        occurrences = text.count(OLD_SPEC)
        print(f"{repo}/{path}  (base={base} @ {sha[:8]})")
        if occurrences != 1:
            print(f"  SKIP: expected exactly 1 occurrence of the old spec, found {occurrences}")
            failures += 1
            continue
        if NEW_SPEC in text:
            print("  SKIP: ceiling already raised")
            continue

        new_text = text.replace(OLD_SPEC, NEW_SPEC)
        # Belt-and-braces: the edit must change exactly one line and nothing else.
        changed = [(a, b) for a, b in zip(text.splitlines(), new_text.splitlines()) if a != b]
        if len(changed) != 1:
            print(f"  SKIP: edit touched {len(changed)} lines, expected 1")
            failures += 1
            continue
        print(f"  edit: {changed[0][0].strip()}  ->  {changed[0][1].strip()}")

        if not execute:
            print("  (dry-run: no branch, no PR)\n")
            continue

        gh("api", f"repos/pcalnon/{repo}/git/refs", "-X", "POST", "-f", f"ref=refs/heads/{BRANCH}", "-f", f"sha={sha}")
        gh(
            "api",
            f"repos/pcalnon/{repo}/contents/{path}",
            "-X",
            "PUT",
            "-f",
            f"message=chore(deps): raise the {UPSTREAM} ceiling to <{NEW_CEILING}\n\nPre-1.0 MINOR upstream bump (juniper-ml#1458) escapes this repo's <0.6.0\nceiling under plan S6. Ceiling only; floor and every other specifier preserved.\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
            "-f",
            f"content={base64.b64encode(new_text.encode('utf-8')).decode('ascii')}",
            "-f",
            f"sha={blob_sha}",
            "-f",
            f"branch={BRANCH}",
        )
        url = gh(
            "pr",
            "create",
            "--repo",
            f"pcalnon/{repo}",
            "--base",
            base,
            "--head",
            BRANCH,
            "--title",
            f"chore(deps): raise the {UPSTREAM} ceiling to <{NEW_CEILING}",
            "--body",
            BODY,
        )
        print(f"  opened: {url}\n")

    print(f"done. {failures} consumer(s) needed attention.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
