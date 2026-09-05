#!/usr/bin/env python3
"""predict_merge.py -- deterministic predicted-merge triage for third-party PRs.

Project: juniper-ml
Sub-Project: custom-agent suite / Cursor-fleet PR-flood remediation
Application: fleet triage (Stage-0 supervisor, script layer)
Author: Paul Calnon
License: MIT License

WHAT IT DOES (P3 §1A -- the deterministic SCRIPT layer, no agent):

For a PR branch (``--pr N``) or every open PR (``--batch``) it, per PR:

  (a) creates a throwaway DETACHED ``git clone`` under the system tempdir --
      never a ``git worktree`` of the primary repo, never the invoking checkout,
      never a push (the merge stays local and is discarded);
  (b) merges ``origin/main`` into the branch tip (``git merge --no-ff``) so the
      RESULT is the tree GitHub would actually land -- previewed here WITHOUT
      paying for it. ``strict_required_status_checks_policy`` is ``true`` on all
      nine repos, and ``allow_update_branch`` is ``false``, so a PR that has gone
      ``BEHIND`` cannot merge and GitHub will not sync it for you: every sync is a
      manual ``update-branch`` that creates a fresh head and restarts the FULL
      required-check battery (~10 min on juniper-ml). CI does eventually run on a
      main-merged tree -- after that cycle. This gives the verdict before it;
  (c) on that RESULT runs the repo-pinned fast gates on the touched files
      (``pre-commit run black isort flake8 mypy check-ast --files <changed>``)
      PLUS two screens CI cannot see, BOTH delegating to the juniper-ci-tools console
      scripts (``juniper-symbol-loss-check`` / ``juniper-docs-additions-check``, PyPI
      package >=0.8.0) on the merged RESULT so a per-PR verdict is byte-identical to the
      post-merge ``main-verify`` gate: an AST symbol-loss screen
      (a symbol present on ``origin/main`` but absent in the merged result -- the
      #755/#729/#738 "flake8+mypy still pass" damage class) and a docs
      deletion-magnitude screen (a deleted Markdown heading, or a run of >= N
      consecutive deleted lines with no adjacent addition, is a suspected #801/#803
      silent section deletion; a small in-place swap is WARN, and the same
      ``Allow-Docs-Rewrite`` commit-trailer waiver is honored so intentional rewrites
      are not DAMAGED);
  (d) emits a per-PR JSON verdict + the TRUE changed-file delta computed from the
      merge RESULT (``git diff --name-only origin/main <result>``), NOT the stale
      ``gh pr list --json files`` list (#729 showed 12 files vs 2 truly changed);
  (e) ``--batch`` builds the same-file cluster map (files -> PRs, from the true
      deltas) and a suggested merge order (heal PRs first -- a fix|heal|hotfix head
      branch or a fix(/fix:/heal title -- then ascending same-file-cluster membership
      so the least-colliding PRs land first).

Script verdicts: MERGE-CLEAN | NEEDS-UPDATE-BRANCH | DAMAGED-FIX-FIRST | CONFLICT.
The DUP-CLOSE recommendation is an agent-layer, two-key, owner-confirmed
adjudication (see ``.claude/agents/fleet-supervisor.md``); the script never
adjudicates duplicates and never closes, pushes, or merges anything.

Exit codes: 0 always-report (even when verdicts are DAMAGED/CONFLICT -- this is a
report); 2 on usage / precondition error (bad args, unresolved ref, no ``gh``,
``--repo-root`` not a git repo).

Requires: ``gh`` on PATH (PR discovery), and -- for the two compositional-loss screens --
the ``juniper-ci-tools`` package (>=0.8.0) installed so ``juniper-symbol-loss-check`` /
``juniper-docs-additions-check`` are on PATH (``pip install 'juniper-ci-tools>=0.8.0,<0.9.0'``).
If a console script is absent, that screen degrades to ``skip`` (never crashes the report);
the fast-gate battery + verdict logic still run.

Any git commit this script makes (only the throwaway local merge commit) uses
``-c commit.gpgsign=false`` so the owner's YubiKey/ed448 signing config never
blocks an unattended run.

CLI: ``python util/fleet_triage/predict_merge.py --pr <N> | --batch [--json] [--repo-root P]``
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 -- git/gh/pre-commit orchestration, fixed argv lists, no shell
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

# The repo-pinned fast-gate hooks run on the merged RESULT's touched .py files
# (.pre-commit-config.yaml: black 26.3.1, isort, flake8, mypy v1.13.0, check-ast :83).
# The fast-gate battery. Superset across the nine ecosystem repos: juniper-ml and most
# siblings use black/isort/flake8, juniper-data uses ruff/ruff-format, juniper-canopy has
# BOTH. A hook absent from the target repo is reported `skip` by the runner, never `fail`
# (see `_default_gate_runner`), so running the union here costs one no-op invocation per
# missing hook and removes the juniper-ml-only blind spot: before 2026-09-05 `ruff` was
# never run on ANY repo, so a juniper-data PR could be reported MERGE-CLEAN while CI
# failed it on the lint the repo actually uses.
PRECOMMIT_HOOKS = ("black", "isort", "flake8", "ruff", "ruff-format", "mypy", "check-ast")

# pre-commit's message when the target repo does not define a requested hook.
MISSING_HOOK_RE = re.compile(r"No hook with id", re.IGNORECASE)

# The four verdicts the deterministic SCRIPT emits. DUP-CLOSE is deliberately
# NOT here: it is an agent-layer, owner-confirmed adjudication, never a script call.
SCRIPT_VERDICTS = ("MERGE-CLEAN", "NEEDS-UPDATE-BRANCH", "DAMAGED-FIX-FIRST", "CONFLICT")

# Headless git identity for the throwaway merge commit. gpgsign/tag.gpgsign are
# forced off so the owner's signing config can never block an unattended run.
_MERGE_IDENT = (
    "-c", "user.name=fleet-triage",
    "-c", "user.email=fleet-triage@juniper.invalid",
    "-c", "commit.gpgsign=false",
    "-c", "tag.gpgsign=false",
)

GateRunner = Callable[[Path, str, list], tuple]


class PredictMergeError(RuntimeError):
    """A precondition / operational failure that prevents producing a report (exit 2)."""


# --------------------------------------------------------------------------- #
# subprocess helpers
# --------------------------------------------------------------------------- #

def _run(cmd: list, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603 -- fixed argv, no shell, trusted tool names
        [str(c) for c in cmd],
        cwd=(str(cwd) if cwd else None),
        capture_output=True,
        text=True,
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return _run(["git", "-C", str(repo), *args])


def _rev(repo: Path, ref: str) -> Optional[str]:
    cp = _git(repo, "rev-parse", "--verify", "-q", ref)
    out = cp.stdout.strip()
    return out if cp.returncode == 0 and out else None


def _blob(repo: Path, ref: str, path: str) -> Optional[str]:
    """Source text of ``<ref>:<path>`` in ``repo``, or None if the path is absent there."""
    cp = _git(repo, "show", f"{ref}:{path}")
    return cp.stdout if cp.returncode == 0 else None


def _names(repo: Path, *diff_args: str) -> list:
    cp = _git(repo, "diff", "--name-only", *diff_args)
    return [ln for ln in cp.stdout.splitlines() if ln.strip()]


# --------------------------------------------------------------------------- #
# AST symbol screen -- delegate to the juniper-ci-tools console script
# --------------------------------------------------------------------------- #
#
# The symbol-loss screen ships as the PyPI package juniper-ci-tools (>=0.8.0); its console
# script juniper-symbol-loss-check is the SAME one the per-PR ``sequence-safety`` job and the
# push:main ``main-verify`` gate run, so a per-PR triage screen is byte-identical to those
# gates -- the same LOST/WEAKENED/DUPLICATED classification, RELOCATED downgrade, and
# Allow-Symbol-Loss commit-trailer waivers. predict_merge invokes it with NO --scope, so the
# package's built-in default (ml's historical in_scope() predicate) applies verbatim, exactly
# as the deleted in-repo util/sequence_safety/ copy did (rollout W3). REQUIRES juniper-ci-tools
# installed (see the module docstring); a missing console script degrades to ``skip`` rather
# than crashing the report.

_SYMBOL_LOSS_CHECK = "juniper-symbol-loss-check"  # console script from juniper-ci-tools>=0.8.0 (on PATH once installed)


def _ast_symbol_screen(clone: Path, base_ref: str, result_ref: str, changed: list) -> dict:
    """Screen the merged RESULT for a silently deleted / gutted / duplicated symbol vs ``base_ref``.

    Delegates to the ``juniper-symbol-loss-check`` console script (juniper-ci-tools>=0.8.0) --
    the SAME CLI the post-merge ``main-verify`` gate runs -- against the scratch clone, so a
    per-PR verdict matches the push:main net exactly (its in-scope filter, RELOCATED downgrade,
    and ``Allow-Symbol-Loss`` commit-trailer waivers all apply). ``status`` is ``fail`` iff the
    checker reports an unwaived FAIL (exit 1); a missing checker (juniper-ci-tools not installed)
    or a broken one degrades to ``skip`` rather than crashing the report. ``lost`` keeps the
    ``{file, symbol, kind}`` shape the JSON report + human render read.
    """
    if not any(p.endswith((".py", ".bash")) for p in changed):
        return {"status": "pass", "lost": []}  # nothing screenable in the delta -> skip the subprocess
    if shutil.which(_SYMBOL_LOSS_CHECK) is None:
        return {"status": "skip", "lost": [], "detail": f"{_SYMBOL_LOSS_CHECK} unavailable -- pip install 'juniper-ci-tools>=0.8.0,<0.9.0'"}
    cp = _run([_SYMBOL_LOSS_CHECK, "--repo-root", str(clone), "--base", base_ref, "--head", result_ref, "--json"])
    if cp.returncode == 2 or not cp.stdout.strip():
        return {"status": "skip", "lost": [], "detail": (cp.stderr.strip() or "symbol-loss screen error")[-300:]}
    try:
        report = json.loads(cp.stdout)
    except json.JSONDecodeError:
        return {"status": "skip", "lost": [], "detail": "symbol-loss screen returned non-JSON"}
    lost = [
        {"file": f["path"], "symbol": f["symbol"], "kind": str(f.get("verdict", "lost")).lower()}
        for f in report.get("findings", [])
        if f.get("severity") == "FAIL"
    ]
    return {"status": "fail" if cp.returncode == 1 else "pass", "lost": lost}


# --------------------------------------------------------------------------- #
# docs deletion-magnitude screen -- delegate to the juniper-ci-tools console script
# --------------------------------------------------------------------------- #
#
# The docs deletion-magnitude screen ships as the PyPI package juniper-ci-tools (>=0.8.0);
# its console script juniper-docs-additions-check runs on the merged RESULT -- the SAME
# subprocess pattern _ast_symbol_screen uses -- so a per-PR docs verdict is byte-identical to
# the push:main "main-verify" gate: the module's magnitude thresholds (a deleted Markdown
# heading, or a run of >= N consecutive deleted lines with no adjacent addition, FAILs; a
# small in-place swap is WARN) and its ``Allow-Docs-Rewrite`` commit-trailer waiver. This
# REPLACES the earlier inline any-removed-line rule, which painted every honest docs
# replacement DAMAGED (the August-storm false-positive class: 26 hand-adjudicated DAMAGED
# verdicts across the two storm triages -- 14 cascor + 12 ml) even though main-verify would
# have passed the same diff.

_DOCS_ADDITIONS_CHECK = "juniper-docs-additions-check"  # console script from juniper-ci-tools>=0.8.0 (on PATH once installed)


def _docs_additions_only_screen(clone: Path, base_ref: str, result_ref: str, changed: list) -> dict:
    """Screen changed ``.md`` files for a net section deletion in the merged RESULT vs ``base_ref``.

    Delegates to the ``juniper-docs-additions-check`` console script (juniper-ci-tools>=0.8.0)
    -- the SAME CLI the post-merge ``main-verify`` gate runs -- so a per-PR docs verdict uses
    the module's magnitude thresholds (a deleted Markdown heading, or a run of >= N consecutive
    deleted lines with no adjacent addition, FAILs; a small in-place swap is WARN) and its
    ``Allow-Docs-Rewrite`` commit-trailer waiver, instead of the old inline any-removed-line
    rule that DAMAGED every honest docs replacement. Every changed ``.md`` is passed via
    ``--files`` so the fleet screen keeps its broader "any changed .md" scope (the module's
    default scope is docs/ + notes/ + AGENTS.md). ``status`` mirrors the module's exit:
    ``fail`` iff it reports an unwaived FAIL (exit 1); a missing checker (juniper-ci-tools not
    installed) or a broken / non-JSON one degrades to ``skip`` rather than crashing the report
    (parity with ``_ast_symbol_screen``). The ``deletions`` / ``waived`` slots keep the
    ``{file, removed_lines, ...}`` shape the JSON report + human render read.
    """
    md_files = [p for p in changed if p.endswith(".md")]
    if not md_files:
        return {"status": "pass", "deletions": [], "waived": []}  # nothing screenable -> skip the subprocess
    if shutil.which(_DOCS_ADDITIONS_CHECK) is None:
        return {"status": "skip", "deletions": [], "waived": [], "detail": f"{_DOCS_ADDITIONS_CHECK} unavailable -- pip install 'juniper-ci-tools>=0.8.0,<0.9.0'"}
    cp = _run([_DOCS_ADDITIONS_CHECK, "--repo-root", str(clone), "--base", base_ref, "--head", result_ref, "--files", *md_files, "--json"])
    if cp.returncode == 2 or not cp.stdout.strip():
        return {"status": "skip", "deletions": [], "waived": [], "detail": (cp.stderr.strip() or "docs-deletion screen error")[-300:]}
    try:
        report = json.loads(cp.stdout)
    except json.JSONDecodeError:
        return {"status": "skip", "deletions": [], "waived": [], "detail": "docs-deletion screen returned non-JSON"}
    deletions: list = []
    waived: list = []
    for f in report.get("findings", []):
        item = {"file": f["path"], "reason": f.get("reason"), "removed_lines": (f.get("detail") or {}).get("deleted")}
        if f.get("severity") == "FAIL":
            deletions.append(item)
        elif f.get("severity") == "WAIVED":
            waived.append({**item, "waived_by": "Allow-Docs-Rewrite trailer"})
    return {"status": "fail" if cp.returncode == 1 else "pass", "deletions": deletions, "waived": waived}


# --------------------------------------------------------------------------- #
# fast-gate battery (pre-commit) -- injectable for hermetic tests
# --------------------------------------------------------------------------- #

def _default_gate_runner(clone: Path, hook: str, files: list) -> tuple:
    """Run one pre-commit hook on the merged result's touched files; ('pass'|'fail'|'skip', detail).

    A hook the TARGET REPO does not define is ``skip``, never ``fail``. juniper-data
    lints with ``ruff`` / ``ruff-format`` and defines no ``black`` / ``isort`` / ``flake8``
    hook at all, so pre-commit answers ``No hook with id `black` in stage `pre-commit```
    and exits non-zero. Scoring that as a gate FAILURE made every juniper-data PR
    ``DAMAGED-FIX-FIRST`` for a property of the instrument rather than of the PR
    (observed 2026-09-05: 6 of 30 juniper-data PRs, all false positives).
    """
    cp = _run(["pre-commit", "run", hook, "--files", *files], cwd=clone)
    if cp.returncode == 0:
        return ("pass", "")
    blob = (cp.stdout + cp.stderr).strip()
    if MISSING_HOOK_RE.search(blob):
        return ("skip", f"hook `{hook}` is not configured in this repo")
    return ("fail", blob[-800:])


def _run_gate_battery(clone: Path, changed_existing: list, *, run_gates: bool, gate_runner: Optional[GateRunner]) -> dict:
    """Per-hook pass/fail/skip on the merged result. ``gate_runner`` (if given) is always used."""
    gates: dict = {}
    py_files = [f for f in changed_existing if f.endswith(".py")]
    use_default = gate_runner is None
    env_skip = bool(os.environ.get("JUNIPER_FLEET_SKIP_PRECOMMIT"))
    skip_all = use_default and (not run_gates or env_skip)
    runner = gate_runner or _default_gate_runner
    for hook in PRECOMMIT_HOOKS:
        if skip_all:
            gates[hook] = {"status": "skip", "detail": "gates disabled (run_gates/env)"}
            continue
        if not py_files:
            gates[hook] = {"status": "skip", "detail": "no .py files in delta"}
            continue
        status, detail = runner(clone, hook, py_files)
        gates[hook] = {"status": status, "detail": detail}
    return gates


# --------------------------------------------------------------------------- #
# detached scratch clone (NEVER a worktree; NEVER mutates the source)
# --------------------------------------------------------------------------- #

def _scratch_clone(repo_root: Path, base_sha: str, branch_sha: str, scratch_parent: Path) -> tuple:
    """Detached ``git clone`` under the system tempdir with ``base``/``branch`` pinned by SHA.

    ``git clone --shared`` references the source's WHOLE object store via an alternate (every
    object reachable from any of the source's refs -- including remote-tracking ``origin/*`` and,
    for a linked-worktree source, the shared common object store -- is visible), so both commit
    SHAs are already present; a plain ``update-ref`` then binds them to stable
    ``refs/fleet/{base,branch}``. ``--shared`` (not ``--local``) is cross-device-safe -- the
    scratch lives under the system tempdir, typically a different filesystem from the repo, where
    ``--local`` hardlinks fail with "Invalid cross-device link". No refspec disambiguation, no
    network. The merge writes new objects only into the SCRATCH's own object dir; the source repo
    is READ only -- never written, never a worktree, never pruned during the seconds-long run.
    """
    scratch = Path(tempfile.mkdtemp(prefix="fleet-triage-", dir=str(scratch_parent)))
    clone = scratch / "clone"
    cp = _run(["git", "clone", "--no-checkout", "--quiet", "--shared", str(repo_root), str(clone)])
    if cp.returncode != 0:
        shutil.rmtree(scratch, ignore_errors=True)
        raise PredictMergeError(f"git clone of {repo_root} failed: {cp.stderr.strip()}")
    for ref_name, sha in (("refs/fleet/base", base_sha), ("refs/fleet/branch", branch_sha)):
        upd = _git(clone, "update-ref", ref_name, sha)
        if upd.returncode != 0:
            shutil.rmtree(scratch, ignore_errors=True)
            raise PredictMergeError(f"could not pin {ref_name} -> {sha[:12]} in scratch clone: {upd.stderr.strip()}")
    return scratch, clone


# --------------------------------------------------------------------------- #
# per-PR predicted-merge simulation (the unit under test; no gh, no network)
# --------------------------------------------------------------------------- #

def simulate_merge(
    repo_root,
    branch_ref: str,
    *,
    pr=None,
    base_ref: str = "origin/main",
    scratch_parent=None,
    gate_runner: Optional[GateRunner] = None,
    run_gates: bool = True,
    keep_scratch: bool = False,
) -> dict:
    """Simulate merging ``base_ref`` into ``branch_ref`` in a detached clone; return the verdict dict.

    Pure of ``gh``/network: callers resolve the branch ref (real: ``origin/<headRefName>``);
    tests pass a fixture branch name directly. The invoking ``repo_root`` is only READ.
    """
    repo_root = Path(repo_root).resolve()
    base_sha = _rev(repo_root, base_ref)
    if base_sha is None:
        raise PredictMergeError(f"base ref {base_ref!r} does not resolve in {repo_root}")
    branch_sha = _rev(repo_root, branch_ref)
    if branch_sha is None:
        raise PredictMergeError(f"branch ref {branch_ref!r} does not resolve in {repo_root}")
    scratch_parent = Path(scratch_parent) if scratch_parent else Path(tempfile.gettempdir())

    scratch = None
    try:
        scratch, clone = _scratch_clone(repo_root, base_sha, branch_sha, scratch_parent)

        # branch behind main iff main tip is NOT an ancestor of the branch tip
        anc = _git(clone, "merge-base", "--is-ancestor", "refs/fleet/base", "refs/fleet/branch")
        behind = anc.returncode != 0

        # check out the branch tip, then merge main into it -> the predicted RESULT
        co = _git(clone, "checkout", "--quiet", "-B", "fleet-sim", "refs/fleet/branch")
        if co.returncode != 0:
            raise PredictMergeError(f"checkout of branch tip failed: {co.stderr.strip()}")
        merge = _git(clone, *_MERGE_IDENT, "merge", "--no-ff", "--no-edit", "refs/fleet/base")
        conflict = merge.returncode != 0

        if conflict:
            conflicted = _names(clone, "--diff-filter=U")
            _git(clone, "merge", "--abort")
            mb = _git(clone, "merge-base", "refs/fleet/base", "refs/fleet/branch").stdout.strip()
            true_delta = _names(clone, mb, "refs/fleet/branch") if mb else []
            gates = {
                "merge": "conflict",
                **{h: {"status": "skip", "detail": "merge conflict"} for h in PRECOMMIT_HOOKS},
                "ast_symbol_screen": {"status": "skip", "lost": [], "detail": "merge conflict"},
                "docs_additions_only": {"status": "skip", "deletions": [], "detail": "merge conflict"},
            }
            return _verdict_dict(
                pr, branch_ref, base_ref, base_sha, branch_sha,
                mergeable=False, behind=behind, verdict="CONFLICT",
                gates=gates, true_delta=true_delta, conflicted=conflicted,
            )

        # clean merge: HEAD (fleet-sim) is the predicted result
        true_delta = _names(clone, "refs/fleet/base", "HEAD")
        changed_existing = [p for p in true_delta if _blob(clone, "HEAD", p) is not None]

        ast_screen = _ast_symbol_screen(clone, "refs/fleet/base", "HEAD", true_delta)
        docs_screen = _docs_additions_only_screen(clone, "refs/fleet/base", "HEAD", true_delta)
        hook_gates = _run_gate_battery(clone, changed_existing, run_gates=run_gates, gate_runner=gate_runner)

        gate_fail = any(g["status"] == "fail" for g in hook_gates.values())
        damaged = gate_fail or ast_screen["status"] == "fail" or docs_screen["status"] == "fail"
        if damaged:
            verdict = "DAMAGED-FIX-FIRST"
        elif behind:
            verdict = "NEEDS-UPDATE-BRANCH"
        else:
            verdict = "MERGE-CLEAN"

        gates = {
            "merge": "clean",
            **hook_gates,
            "ast_symbol_screen": ast_screen,
            "docs_additions_only": docs_screen,
        }
        return _verdict_dict(
            pr, branch_ref, base_ref, base_sha, branch_sha,
            mergeable=True, behind=behind, verdict=verdict,
            gates=gates, true_delta=true_delta, conflicted=[],
        )
    finally:
        if scratch is not None and not keep_scratch:
            shutil.rmtree(scratch, ignore_errors=True)


def _verdict_dict(pr, branch_ref, base_ref, base_sha, branch_sha, *, mergeable, behind, verdict, gates, true_delta, conflicted) -> dict:
    return {
        "pr": pr if pr is not None else branch_ref,
        "branch": branch_ref,
        "base_ref": base_ref,
        "base_sha": base_sha,
        "branch_sha": branch_sha,
        "mergeable": mergeable,
        "behind_main": behind,
        "verdict": verdict,
        "gates": gates,
        "true_delta": sorted(true_delta),
        "conflicted_files": sorted(conflicted),
    }


# --------------------------------------------------------------------------- #
# batch: cluster map + suggested merge order (pure functions over verdicts)
# --------------------------------------------------------------------------- #

def _pr_key(value) -> tuple:
    """Sort key that orders int PR numbers before/among string branch refs deterministically."""
    if isinstance(value, bool):  # bool is an int subclass; keep it out of the int lane
        return (1, str(value))
    if isinstance(value, int):
        return (0, value)
    return (1, str(value))


def build_clusters(verdicts: list) -> dict:
    """file -> sorted list of PRs that truly change it (from the predicted-merge deltas)."""
    clusters: dict = {}
    for v in verdicts:
        for path in v.get("true_delta", []):
            clusters.setdefault(path, []).append(v["pr"])
    return {path: sorted(prs, key=_pr_key) for path, prs in sorted(clusters.items())}


# Heal-first ordering (land restore/repair PRs before ordinary feature work). Tightened
# after a wave-1 mis-sort: an ordinary "test(...) + heal tokens" title matched the bare
# substring "heal" and was promoted to the front. Heal-first now fires ONLY on a
# fix|heal|hotfix HEAD-branch prefix or a fix(/fix:/heal TITLE prefix -- never an arbitrary
# substring anywhere in the title/branch.
_HEAL_BRANCH_RE = re.compile(r"^(?:fix|heal|hotfix)/", re.IGNORECASE)
_HEAL_TITLE_RE = re.compile(r"^\s*(?:fix\(|fix:|heal\b)", re.IGNORECASE)


def _is_heal(v: dict) -> bool:
    """A restore/heal PR to land first: the HEAD branch matches ``^(fix|heal|hotfix)/`` OR
    the title starts with ``fix(`` / ``fix:`` / ``heal``. Tightened from the old
    bare-substring match (``restore`` / ``heal`` / ``repair`` / ``fix-first`` anywhere in the
    title or branch), which mis-sorted an ordinary ``test(...) + heal tokens`` PR to the
    front of the wave-1 triage order. ``v['branch']`` is the origin-qualified ref
    (``origin/<headRefName>``); the leading ``origin/`` is stripped so the HEAD branch name
    is matched, and a bare fixture branch (no remote prefix) is matched as-is."""
    branch = str(v.get("branch", ""))
    head = branch.split("/", 1)[1] if branch.startswith("origin/") else branch
    title = str(v.get("title", ""))
    return bool(_HEAL_BRANCH_RE.match(head) or _HEAL_TITLE_RE.match(title))


def suggest_order(verdicts: list, clusters: dict) -> list:
    """Heal PRs first (``_is_heal``: fix|heal|hotfix branch or fix(/fix:/heal title), then
    ascending same-file-cluster membership (least-colliding first)."""
    def contention(v: dict) -> int:
        return max((len(clusters.get(path, [])) for path in v.get("true_delta", [])), default=0)

    ordered = sorted(verdicts, key=lambda v: (0 if _is_heal(v) else 1, contention(v), _pr_key(v["pr"])))
    return [v["pr"] for v in ordered]


# --------------------------------------------------------------------------- #
# gh layer (thin resolvers on top of the pure core)
# --------------------------------------------------------------------------- #

def _gh_json(repo_root: Path, *args: str):
    cp = _run(["gh", *args], cwd=repo_root)
    if cp.returncode != 0:
        raise PredictMergeError(f"`gh {' '.join(args)}` failed: {cp.stderr.strip() or cp.stdout.strip()}")
    try:
        return json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise PredictMergeError(f"`gh {' '.join(args)}` returned non-JSON: {exc}") from exc


def triage_pr(repo_root, pr: int, *, base_ref: str = "origin/main", **kw) -> dict:
    """Resolve PR ``pr``'s branch via ``gh`` and simulate its predicted merge."""
    repo_root = Path(repo_root).resolve()
    info = _gh_json(repo_root, "pr", "view", str(pr), "--json", "number,title,headRefName,mergeable,mergeStateStatus")
    branch_ref = f"origin/{info['headRefName']}"
    verdict = simulate_merge(repo_root, branch_ref, pr=info.get("number", pr), base_ref=base_ref, **kw)
    verdict["title"] = info.get("title", "")
    verdict["gh_mergeable"] = info.get("mergeable")
    verdict["gh_merge_state"] = info.get("mergeStateStatus")
    return verdict


def triage_batch(repo_root, *, base_ref: str = "origin/main", **kw) -> dict:
    """Simulate every open PR, then build the cluster map + suggested merge order."""
    repo_root = Path(repo_root).resolve()
    prs = _gh_json(
        repo_root, "pr", "list", "--state", "open",
        "--json", "number,title,headRefName,mergeable,mergeStateStatus", "--limit", "200",
    )
    verdicts: list = []
    for info in prs:
        branch_ref = f"origin/{info['headRefName']}"
        try:
            v = simulate_merge(repo_root, branch_ref, pr=info.get("number"), base_ref=base_ref, **kw)
        except PredictMergeError as exc:
            v = {
                "pr": info.get("number"),
                "branch": branch_ref,
                "verdict": "ERROR",
                "error": str(exc),
                "true_delta": [],
                "gates": {},
            }
        v["title"] = info.get("title", "")
        v["gh_mergeable"] = info.get("mergeable")
        v["gh_merge_state"] = info.get("mergeStateStatus")
        verdicts.append(v)
    clusters = build_clusters(verdicts)
    order = suggest_order(verdicts, clusters)
    return {
        "base_ref": base_ref,
        "base_sha": _rev(repo_root, base_ref),
        "open_pr_count": len(verdicts),
        "prs": verdicts,
        "clusters": clusters,
        "merge_order": order,
        "screen_coverage": screen_coverage(verdicts),
    }


def screen_coverage(verdicts: list) -> dict:
    """Per-gate pass/fail/SKIP counts + the PRs no compositional screen could evaluate.

    Both loss screens hard-code ``{"status": "skip"}`` when the merge does not apply, so on
    a CONFLICT PR they answer nothing. Reading a batch report without this section invites
    the vacuous claim "0 docs deletions across all N" when the true statement is "0 across
    the N-minus-skipped that were actually screened" -- a CORRECT predicate over an
    INCOMPLETE site enumeration. On 2026-09-05 that was 43 of 99 juniper-ml PRs (43%),
    and the unscreened set is exactly the CONFLICT set -- i.e. the PRs whose damage would
    live in the conflict resolution, which is where the 2026-07-26 flood's damage came from.

    ``unscreened`` is therefore the population a reviewer must read by hand; it is NOT a
    clean bill of health for them.
    """
    gates = ("ast_symbol_screen", "docs_additions_only") + PRECOMMIT_HOOKS
    coverage: dict = {}
    for gate in gates:
        tally = {"pass": 0, "fail": 0, "skip": 0, "absent": 0}
        for v in verdicts:
            entry = (v.get("gates") or {}).get(gate)
            status = entry.get("status") if isinstance(entry, dict) else entry
            tally[status if status in tally else "absent"] += 1
        evaluated = tally["pass"] + tally["fail"]
        coverage[gate] = {
            **tally,
            "evaluated": evaluated,
            # The honest denominator. A rate over `len(verdicts)` is the vacuous one.
            "screened_fraction": round(evaluated / len(verdicts), 3) if verdicts else 0.0,
        }
    unscreened = sorted(
        v.get("pr")
        for v in verdicts
        if ((v.get("gates") or {}).get("ast_symbol_screen") or {}).get("status") == "skip"
        or ((v.get("gates") or {}).get("docs_additions_only") or {}).get("status") == "skip"
    )
    return {"per_gate": coverage, "unscreened": unscreened, "unscreened_count": len(unscreened)}


# --------------------------------------------------------------------------- #
# CLI + human-readable rendering
# --------------------------------------------------------------------------- #

def _resolve_repo_root(arg: Optional[str]) -> Path:
    root = Path(arg).resolve() if arg else Path.cwd()
    cp = _run(["git", "-C", str(root), "rev-parse", "--show-toplevel"])
    if cp.returncode != 0:
        raise PredictMergeError(f"--repo-root {root} is not inside a git repository")
    return Path(cp.stdout.strip())


def _render_single(v: dict) -> str:
    lines = [f"PR {v['pr']}  [{v['verdict']}]  mergeable={v['mergeable']}  behind_main={v.get('behind_main')}"]
    if v.get("title"):
        lines.append(f"  title: {v['title']}")
    lines.append(f"  branch: {v.get('branch')}  base: {v.get('base_ref')}")
    g = v.get("gates", {})
    if g:
        hook_bits = " ".join(f"{h}={g[h]['status']}" for h in PRECOMMIT_HOOKS if h in g)
        lines.append(f"  merge={g.get('merge')}  {hook_bits}")
        ast = g.get("ast_symbol_screen", {})
        if ast.get("lost"):
            lines.append(f"  LOST symbols ({len(ast['lost'])}): " + ", ".join(f"{x['file']}:{x['symbol']}" for x in ast["lost"][:8]))
        docs = g.get("docs_additions_only", {})
        if docs.get("deletions"):
            lines.append("  DOCS removals: " + ", ".join(f"{d['file']}(-{d['removed_lines']})" for d in docs["deletions"][:8]))
    if v.get("conflicted_files"):
        lines.append("  CONFLICTED: " + ", ".join(v["conflicted_files"][:8]))
    lines.append(f"  true_delta ({len(v.get('true_delta', []))}): " + ", ".join(v.get("true_delta", [])[:12]))
    return "\n".join(lines)


def _render_batch(report: dict) -> str:
    lines = [f"Open PRs: {report['open_pr_count']}  base={report.get('base_ref')} ({(report.get('base_sha') or '?')[:12]})", ""]
    for v in report["prs"]:
        lines.append(_render_single(v))
        lines.append("")
    contested = {f: prs for f, prs in report["clusters"].items() if len(prs) > 1}
    lines.append(f"Same-file clusters (contested, {len(contested)}):")
    for f, prs in sorted(contested.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines.append(f"  {f}: {prs}")
    lines.append("")
    cov = report.get("screen_coverage") or {}
    if cov:
        n = report["open_pr_count"]
        lines.append(f"Screen coverage (a `skip` is NOT a pass -- it is a PR nothing examined):")
        for gate, t in (cov.get("per_gate") or {}).items():
            lines.append(f"  {gate}: pass={t['pass']} fail={t['fail']} skip={t['skip']} -> evaluated {t['evaluated']}/{n}")
        unscreened = cov.get("unscreened") or []
        if unscreened:
            lines.append(f"  UNSCREENED by at least one loss screen ({len(unscreened)}/{n}): {unscreened}")
            lines.append("  ^ these must be read by hand; no compositional-loss claim covers them.")
        lines.append("")
    lines.append("Suggested merge order (heal first, then least-colliding): " + str(report["merge_order"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="predict_merge.py",
        description="Deterministic predicted-merge triage for third-party fleet PRs (Stage-0 supervisor script layer).",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pr", type=int, metavar="N", help="triage a single open PR by number")
    mode.add_argument("--batch", action="store_true", help="triage every open PR + emit cluster map & merge order")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a human report")
    parser.add_argument("--repo-root", default=None, help="target repo (default: cwd's git toplevel)")
    args = parser.parse_args(argv)

    try:
        repo_root = _resolve_repo_root(args.repo_root)
        if args.pr is not None:
            verdict = triage_pr(repo_root, args.pr)
            print(json.dumps(verdict, indent=2) if args.json else _render_single(verdict))
        else:
            report = triage_batch(repo_root)
            print(json.dumps(report, indent=2) if args.json else _render_batch(report))
    except PredictMergeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
