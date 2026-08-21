#!/usr/bin/env python3
"""Identify the `DeployKey` ruleset bypass actor, and audit the keys behind it.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc audit tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-08-21
Status:      ad-hoc -- audit
Retire when: the DeployKey bypass disposition is decided and recorded.
Related:     HANDOFF_2026-08-19 section 2.5;
             notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_BYPASS-ACTOR-CENSUS.md

The open item
-------------
Every repo's primary ruleset carries `{"actor_type": "DeployKey", "actor_id": null,
"bypass_mode": "always"}` -- the WIDEST entitlement in the roster (push / force-push /
delete the default branch past every rule), and the only one never identified.
`actor_id: null` means ANY deploy key on that repo, so the entitlement is exactly as wide
as the set of deploy keys, and read-only keys cannot use it at all.

So the question "what is this actor" reduces to three checkable ones, per repo:

  1. Which deploy keys exist, and are any WRITE-enabled? (a read-only key makes the row
     inert on that repo)
  2. Do they correspond to anything on this host -- i.e. is the "unidentified third party"
     actually the operator's own workstation push identity?
  3. Has the entitlement ever been exercised, and if so WHEN relative to ruleset changes?

Trap this tool exists to avoid
------------------------------
`last_used` on a deploy key is **NOT a reliable recency signal**. Measured 2026-08-21: the
juniper-ml key reported `last_used: 2026-08-17` immediately after a successful `ssh -T`
authentication AND after roughly thirty pushes that same day. Do not conclude a key is
dormant from that field. The authoritative probe is `ssh -T` against the host alias:
GitHub answers `Hi <owner>/<repo>!` for a deploy key and `Hi <user>!` for a user key.

Usage
-----
    python3 util/ad-hoc/2026-08-21_deploykey_bypass_audit.py
    python3 util/ad-hoc/2026-08-21_deploykey_bypass_audit.py --local-keys
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - shells out to `gh` and `ssh` by design
from pathlib import Path

REPOS = [
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


class ProbeError(RuntimeError):
    """A read failed. Raised, never defaulted -- see the note in `gh_json`."""


def gh_json(path: str, *, retries: int = 3):
    """Read via `gh api`, RAISING on failure rather than returning an empty result.

    The first version of this function returned None on failure and every call site wrote
    `gh_json(...) or []`. That conflates "the API call failed" with "this repo has no
    deploy keys" -- and it bit immediately: a transient failure made juniper-canopy report
    **0 keys**, and the tool concluded its bypass row was "provably inert and removable
    with zero risk". canopy in fact has TWO write-enabled keys. A wrong, actionable,
    confident conclusion from a probe that never ran.

    That is the same class this ecosystem keeps hitting (a check whose machinery breaks and
    reports success), so it is fixed the same way `util/wait_for_checks.py` fixes it: a
    failed probe raises, and a genuinely-empty result is a distinct, trustworthy value.
    """
    last = ""
    for attempt in range(max(1, retries)):
        p = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
            ["gh", "api", path], capture_output=True, text=True, timeout=120
        )
        if p.returncode == 0:
            try:
                return json.loads(p.stdout or "null")
            except json.JSONDecodeError as exc:
                raise ProbeError(f"{path}: unparseable response") from exc
        last = (p.stderr or "").strip()[:200]
        # A 404 is a real answer for some endpoints; everything else gets retried.
        if "404" in last:
            raise ProbeError(f"{path}: 404")
    raise ProbeError(f"{path}: failed after {retries} attempts: {last}")


def local_pubkeys() -> dict:
    """Map public-key blob -> local file, for every ~/.ssh/*.pub on this host.

    Public keys only. Nothing here reads or prints private key material, and every blob
    matched against is already publicly readable from the GitHub API.
    """
    out = {}
    ssh = Path.home() / ".ssh"
    if not ssh.is_dir():
        return out
    for pub in sorted(ssh.glob("*.pub")):
        try:
            parts = pub.read_text(encoding="utf-8").split()
        except OSError:
            continue
        if len(parts) >= 2:
            out[parts[1]] = pub.name
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--local-keys", action="store_true",
                    help="match repo deploy keys against this host's ~/.ssh/*.pub")
    args = ap.parse_args()

    local = local_pubkeys() if args.local_keys else {}
    if args.local_keys:
        print(f"local public keys found: {len(local)}")
        print()

    print(f"{'repo':<24} {'bypass row?':<12} {'keys':>5} {'writable':>9}  detail")
    print("-" * 100)
    writable_total = 0
    failures = []
    for repo in REPOS:
        try:
            sets = gh_json(f"repos/{args.owner}/{repo}/rulesets")
            has_row = False
            for rs in sets:
                full = gh_json(f"repos/{args.owner}/{repo}/rulesets/{rs['id']}")
                for b in (full or {}).get("bypass_actors", []):
                    if b.get("actor_type") == "DeployKey":
                        has_row = True
            keys = gh_json(f"repos/{args.owner}/{repo}/keys")
        except ProbeError as exc:
            # Named loudly and counted, never rendered as a zero.
            print(f"{repo:<24} {'PROBE FAILED':<12} {'?':>5} {'?':>9}  {exc}")
            failures.append(repo)
            continue
        writable = [k for k in keys if not k.get("read_only")]
        writable_total += len(writable)
        detail = []
        for k in keys:
            tag = "RW" if not k.get("read_only") else "ro"
            blob = (k.get("key") or "").split()[-1] if k.get("key") else ""
            mine = local.get(blob)
            detail.append(f"{k.get('title')!r}[{tag}]" + (f"=={mine}" if mine else ""))
        print(
            f"{repo:<24} {'YES' if has_row else 'no':<12} {len(keys):>5} {len(writable):>9}  "
            f"{'; '.join(detail)[:52]}"
        )

    print()
    print("=" * 100)
    if failures:
        print(f"!! {len(failures)} repo(s) COULD NOT BE PROBED: {', '.join(failures)}")
        print("!! Their counts above are '?', not 0. Re-run before drawing any conclusion")
        print("!! about them -- a failed probe reported as 0 keys is how this tool once")
        print("!! declared juniper-canopy's bypass row inert when it has two live keys.")
        print()
    print(f"WRITE-ENABLED deploy keys across the fleet: {writable_total}"
          + (" (INCOMPLETE)" if failures else ""))
    print("A DeployKey bypass row is only as wide as the WRITE-enabled keys on that repo.")
    print("Where a repo has none, the row is inert there and removing it changes nothing.")
    if args.local_keys:
        print()
        print("`==<file>` marks a deploy key whose public half is present on THIS host --")
        print("i.e. the 'unidentified' bypass actor is this workstation's own push identity.")
        print("Confirm with: ssh -T git@<host-alias>   ->  'Hi owner/repo!' means deploy key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
