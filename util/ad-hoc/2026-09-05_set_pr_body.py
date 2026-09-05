#!/usr/bin/env python3
"""Set a PR's title/body via the REST API, because `gh pr edit` is broken here.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc automation
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- automation
Retire when: the installed `gh` is upgraded past the 2.46.0 `pr edit` breakage.

WHY

`gh` 2.46.0 fails EVERY `gh pr edit` invocation -- not just `--body-file` -- with
a GraphQL error about deprecated Projects (classic):

    GraphQL: Projects (classic) is being deprecated ... (repository.pullRequest.projectCards)

The edit never applies. The REST endpoint `PATCH /repos/{owner}/{repo}/pulls/{n}`
is unaffected because it does not touch the projects field at all.

Usage
-----
    python3 util/ad-hoc/2026-09-05_set_pr_body.py --pr 1754 --body-file body.md
    python3 util/ad-hoc/2026-09-05_set_pr_body.py --pr 1754 --title "new title"
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocation, no shell
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="pcalnon/juniper-ml")
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--body-file", type=Path)
    ap.add_argument("--title")
    args = ap.parse_args()

    payload: dict[str, str] = {}
    if args.body_file:
        payload["body"] = args.body_file.read_text()
    if args.title:
        payload["title"] = args.title
    if not payload:
        print("nothing to set: pass --body-file and/or --title", file=sys.stderr)
        return 2

    proc = subprocess.run(
        ["gh", "api", "-X", "PATCH", f"repos/{args.repo}/pulls/{args.pr}", "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr[:600], file=sys.stderr)
        return 1
    print("updated:", json.loads(proc.stdout)["html_url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
