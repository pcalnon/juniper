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
      RESULT is the tree GitHub would actually land -- the merge CI never sees
      because ``strict_required_status_checks_policy`` is ``false``;
  (c) on that RESULT runs the repo-pinned fast gates on the touched files
      (``pre-commit run black isort flake8 mypy check-ast --files <changed>``)
      PLUS two screens CI cannot see: an AST symbol-loss screen (a symbol present
      on ``origin/main`` but absent in the merged result -- the #755/#729/#738
      "flake8+mypy still pass" damage class) and, for docs, a diff-vs-main
      additions-only screen (any removed content line on an addition PR is a
      suspected #801/#803 silent section deletion);
  (d) emits a per-PR JSON verdict + the TRUE changed-file delta computed from the
      merge RESULT (``git diff --name-only origin/main <result>``), NOT the stale
      ``gh pr list --json files`` list (#729 showed 12 files vs 2 truly changed);
  (e) ``--batch`` builds the same-file cluster map (files -> PRs, from the true
      deltas) and a suggested merge order (restore/heal PRs first, then ascending
      same-file-cluster membership so the least-colliding PRs land first).

Script verdicts: MERGE-CLEAN | NEEDS-UPDATE-BRANCH | DAMAGED-FIX-FIRST | CONFLICT.
The DUP-CLOSE recommendation is an agent-layer, two-key, owner-confirmed
adjudication (see ``.claude/agents/fleet-supervisor.md``); the script never
adjudicates duplicates and never closes, pushes, or merges anything.

Exit codes: 0 always-report (even when verdicts are DAMAGED/CONFLICT -- this is a
report); 2 on usage / precondition error (bad args, unresolved ref, no ``gh``,
``--repo-root`` not a git repo).

Any git commit this script makes (only the throwaway local merge commit) uses
``-c commit.gpgsign=false`` so the owner's YubiKey/ed448 signing config never
blocks an unattended run.

CLI: ``python util/fleet_triage/predict_merge.py --pr <N> | --batch [--json] [--repo-root P]``
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 -- git/gh/pre-commit orchestration, fixed argv lists, no shell
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

# The repo-pinned fast-gate hooks run on the merged RESULT's touched .py files
# (.pre-commit-config.yaml: black 26.3.1, isort, flake8, mypy v1.13.0, check-ast :83).
PRECOMMIT_HOOKS = ("black", "isort", "flake8", "mypy", "check-ast")

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
# AST symbol screen -- delegate to the permanent sequence-safety checker
# --------------------------------------------------------------------------- #
#
# util/sequence_safety/symbol_loss_check.py (landed in ml#873) is the permanent home for
# the symbol-loss screen; predict_merge shells out to its CLI on the merged RESULT so a
# per-PR triage screen is byte-identical to the push:main "main-verify" gate -- the same
# LOST/WEAKENED/DUPLICATED classification, RELOCATED downgrade, and Allow-Symbol-Loss
# commit-trailer waivers. (This replaces the ad-hoc flood-census seed
# util/ad-hoc/2026-07-28_flood_census_symbol_screen.py, whose pure extractors were borrowed
# before the permanent module existed; the seed stays put as a program artifact.)

_SYMBOL_LOSS_CHECK = Path(__file__).resolve().parent.parent / "sequence_safety" / "symbol_loss_check.py"


def _ast_symbol_screen(clone: Path, base_ref: str, result_ref: str, changed: list) -> dict:
    """Screen the merged RESULT for a silently deleted / gutted / duplicated symbol vs ``base_ref``.

    Delegates to ``util/sequence_safety/symbol_loss_check.py`` -- the SAME CLI the post-merge
    ``main-verify`` gate runs -- against the scratch clone, so a per-PR verdict matches the
    push:main net exactly (its in-scope filter, RELOCATED downgrade, and ``Allow-Symbol-Loss``
    commit-trailer waivers all apply). ``status`` is ``fail`` iff the checker reports an unwaived
    FAIL (exit 1); a missing / broken checker degrades to ``skip`` rather than crashing the
    report. ``lost`` keeps the ``{file, symbol, kind}`` shape the JSON report + human render read.
    """
    if not any(p.endswith((".py", ".bash")) for p in changed):
        return {"status": "pass", "lost": []}  # nothing screenable in the delta -> skip the subprocess
    if not _SYMBOL_LOSS_CHECK.exists():
        return {"status": "skip", "lost": [], "detail": "symbol-loss checker unavailable"}
    cp = _run([sys.executable, str(_SYMBOL_LOSS_CHECK), "--repo-root", str(clone), "--base", base_ref, "--head", result_ref, "--json"])
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
# docs additions-only screen
# --------------------------------------------------------------------------- #

def _removed_content_lines(diff_text: str) -> int:
    """Count removed CONTENT lines in a unified diff (a ``-`` line that is not the ``---`` header)."""
    count = 0
    for line in diff_text.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            count += 1
    return count


def _docs_additions_only_screen(clone: Path, base_ref: str, result_ref: str, changed: list) -> dict:
    """Flag any changed ``.md`` whose merge result removes content (suspected section deletion)."""
    deletions: list = []
    for path in changed:
        if not path.endswith(".md"):
            continue
        cp = _git(clone, "diff", "--no-color", base_ref, result_ref, "--", path)
        removed = _removed_content_lines(cp.stdout)
        if removed > 0:
            deletions.append({"file": path, "removed_lines": removed})
    return {"status": "fail" if deletions else "pass", "deletions": deletions}


# --------------------------------------------------------------------------- #
# fast-gate battery (pre-commit) -- injectable for hermetic tests
# --------------------------------------------------------------------------- #

def _default_gate_runner(clone: Path, hook: str, files: list) -> tuple:
    """Run one pre-commit hook on the merged result's touched files; ('pass'|'fail', detail)."""
    cp = _run(["pre-commit", "run", hook, "--files", *files], cwd=clone)
    if cp.returncode == 0:
        return ("pass", "")
    return ("fail", (cp.stdout + cp.stderr).strip()[-800:])


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


def _is_heal(v: dict) -> bool:
    """A restore/heal PR (land these first): title or branch names restore/heal/repair/fix-first."""
    hay = f"{v.get('title', '')} {v.get('branch', '')}".lower()
    return any(tok in hay for tok in ("restore", "heal", "repair", "fix-first"))


def suggest_order(verdicts: list, clusters: dict) -> list:
    """Restore/heal PRs first, then ascending same-file-cluster membership (least-colliding first)."""
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
    }


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
    lines.append("Suggested merge order (restore/heal first, then least-colliding): " + str(report["merge_order"]))
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
