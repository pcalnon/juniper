#!/usr/bin/env python3
"""Fail if any Juniper ruleset is scoped `~ALL` instead of `~DEFAULT_BRANCH`.

Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

WHY THIS EXISTS
---------------
On 2026-08-23 the `dependabot[bot]` (29110) and `Copilot SWE Agent` (1143301) bypass rows
were removed from all 9 repos. That removal is safe **only while every ruleset stays
`~DEFAULT_BRANCH`-scoped**, and the dependency is not obvious from anything in the repo:

* Under `~DEFAULT_BRANCH`, the `creation` rule is evaluated only when creating the default
  branch -- which no bot ever does -- so the rows were inert and removing them changed
  nothing.
* Under `~ALL`, `creation` is evaluated on **every** branch, including `dependabot/*`. The
  rows were genuinely load-bearing there: that is exactly what the 24 `creation: fail`
  bypass events between 2026-07-20 and 2026-08-10 were.

So re-scoping any ruleset back to `~ALL` silently re-arms a dependency on rows that no
longer exist. The symptom is dependency PRs stopping fleet-wide, with nothing pointing at
the cause. Determination + evidence:
``notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md``.

WHAT THIS DOES **NOT** CHECK
----------------------------
**Bypass-row presence.** ``bypass_actors`` is redacted for unauthenticated callers, and
this guard is deliberately token-free so it can run on any PR without a secret. It reports
scope only, and says so. For the row half use the authenticated
``util/ad-hoc/2026-08-23_bypass_removal_verify.py``, which checks both.

That split is intentional and must not be quietly "improved": a token-free tool that
appears to verify rows would report a redacted field as an empty one -- reporting the
removal as verified while checking nothing.

TOKEN
-----
None required: all 9 repos are public and `GET /repos/{o}/{r}/rulesets[/{id}]` answers 200
unauthenticated. ``GITHUB_TOKEN``/``GH_TOKEN`` is used when present purely for the higher
rate limit (60/hr unauthenticated is per-IP and shared on hosted runners).

EXIT CODES
----------
0  every ruleset narrowly scoped
1  at least one `~ALL` ruleset -- the guard firing
2  a probe failed after retries -- **could not verify**, which is not the same as clean

Both non-zero codes are failures on purpose (fail-closed). Transient flakiness is absorbed
by retries rather than by treating an unverified result as a pass.

Usage::

    python3 util/ruleset_scope_guard.py                  # this repo only (per-PR)
    python3 util/ruleset_scope_guard.py --fleet          # all 9 (weekly)
    python3 util/ruleset_scope_guard.py --repo juniper-data --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

OWNER = "pcalnon"
SELF_REPO = "juniper-ml"

FLEET = [
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
]

# The scope that makes the removed bypass rows inert. Anything broader re-arms them.
FORBIDDEN_SCOPE = "~ALL"

_API = "https://api.github.com"
_RETRIES = 3
_BACKOFF = 2.0


class ProbeError(RuntimeError):
    """A request failed after retries. NEVER convert this into an empty result."""


def _get(path: str, *, retries: int = _RETRIES, sleeper=time.sleep):
    """GET a JSON path, retrying transient failures. Raises ProbeError; never returns None.

    Returning ``None``/``[]`` on failure is the mistake this codebase keeps re-learning --
    a failed probe that reads as "nothing found" reports a broken check as a clean one.
    """
    req = urllib.request.Request(f"{_API}{path}")  # nosec B310 - fixed https host
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    last = ""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as exc:
            last = f"{type(exc).__name__}: {exc}"
            if attempt < retries - 1:
                sleeper(_BACKOFF * (attempt + 1))
    raise ProbeError(f"GET {path} failed after {retries} attempts -- {last}")


def scope_of(ruleset: dict) -> list[str]:
    return ((ruleset or {}).get("conditions") or {}).get("ref_name", {}).get("include", [])


def audit_repo(repo: str, *, getter=None) -> list[dict]:
    """Return one row per ruleset. Propagates ProbeError rather than degrading.

    ``getter`` resolves at CALL time, not definition time -- a ``getter=_get`` default would
    bind the original function object and make the module attribute unpatchable, so the
    hermetic tests would silently hit the network instead of their fake.
    """
    getter = getter or _get
    rows = []
    for summary in getter(f"/repos/{OWNER}/{repo}/rulesets"):
        detail = getter(f"/repos/{OWNER}/{repo}/rulesets/{summary['id']}")
        scope = scope_of(detail)
        rows.append(
            {
                "repo": repo,
                "id": summary["id"],
                "name": detail.get("name") or summary.get("name"),
                "scope": scope,
                "violation": FORBIDDEN_SCOPE in scope,
            }
        )
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--fleet", action="store_true", help=f"audit all {len(FLEET)} repos")
    group.add_argument("--repo", help="audit a single named repo (default: this repo)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    repos = FLEET if args.fleet else [args.repo or SELF_REPO]

    rows: list[dict] = []
    failures: list[str] = []
    for repo in repos:
        try:
            rows.extend(audit_repo(repo))
        except ProbeError as exc:
            failures.append(str(exc))

    if args.as_json:
        print(json.dumps({"rows": rows, "probe_failures": failures}, indent=2))
    else:
        print("=" * 78)
        print("RULESET SCOPE GUARD -- scope only; bypass rows are NOT checked (see module doc)")
        print("=" * 78)
        for r in rows:
            flag = "  <-- VIOLATION" if r["violation"] else ""
            print(f"{r['repo']:24s} [{r['id']}] {r['name']:30s} {','.join(r['scope']) or '(none)'}{flag}")
        print("-" * 78)
        print(f"rulesets checked: {len(rows)}   violations: {sum(r['violation'] for r in rows)}   probe failures: {len(failures)}")

    for f in failures:
        print(f"PROBE FAILURE: {f}", file=sys.stderr)

    if failures:
        print(
            "\nCOULD NOT VERIFY -- this is not the same as clean. Re-run; if it persists, "
            "check api.github.com availability before assuming the rulesets are fine.",
            file=sys.stderr,
        )
        return 2

    violations = [r for r in rows if r["violation"]]
    if violations:
        print(
            f"\nFAIL: {len(violations)} ruleset(s) scoped {FORBIDDEN_SCOPE}.\n"
            f"  {FORBIDDEN_SCOPE} evaluates `creation` on EVERY branch, which re-arms the need for the\n"
            "  dependabot (29110) / Copilot (1143301) bypass rows removed 2026-08-23. Left as-is,\n"
            "  dependency PRs stop fleet-wide with nothing naming the cause.\n"
            "  Re-scope to ~DEFAULT_BRANCH, or restore those rows deliberately and update\n"
            "  notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md.",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v['repo']} [{v['id']}] {v['name']}", file=sys.stderr)
        return 1

    if not rows:
        # No rulesets at all is not a pass -- it means the repo is unprotected, or the
        # probe silently returned an empty list.
        print("\nFAIL: no rulesets found at all. Unprotected, or a degraded probe.", file=sys.stderr)
        return 2

    print(f"\nOK: {len(rows)} ruleset(s), none scoped {FORBIDDEN_SCOPE}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
